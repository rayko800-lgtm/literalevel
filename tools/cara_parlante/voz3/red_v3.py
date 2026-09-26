"""Las redes de v3 y lo que comparten sus dos entrenamientos (boca y no verbal).

- SumaCapas: suma ponderada aprendida de las K capas guardadas de HuBERT/WavLM (softmax sobre K
  pesos, cada capa normalizada antes), como en SUPERB; después una proyección a d.
- Tronco: la parte común de las dos redes: voz + articulación de Blender + fonema embebido →
  conv local → transformer pre-norm (GELU).
- Boca: regresión; salida = base lineal desde los controles de Blender + corrección del tronco
  (igual que la red de fusión: la anatomía la pone Blender, la red añade coarticulación y vida).
- NoVerbal: flow matching (rectified flow) 1D con transformer, condicionado por la voz, «habla»
  y un vector de estilo (sd de cada canal en el clip); muestreo Euler con semilla y guía sin
  clasificador. Es lo que hace que cejas, ojos, sonrisa lenta y cabeza salgan vivos y variados
  en vez de promediados (DiffPoseTalk, ARTalk).
- Estado: guardar/cargar checkpoint completo (red, EMA, optimizador, planificador, época, RNG)
  para reanudar si Colab se cae; progreso.json por época; EMA de pesos.
"""
import json
import math
import os
import random

import numpy as np
import torch
import torch.nn as nn


class SumaCapas(nn.Module):
    def __init__(self, k, d, drop=0.1):
        super().__init__()
        self.norma = nn.LayerNorm(1024)
        self.pesos = nn.Parameter(torch.zeros(k))
        self.sal = nn.Sequential(nn.Dropout(drop), nn.Linear(1024, d))

    def forward(self, voz):                       # [B, T, K, 1024]
        w = torch.softmax(self.pesos, 0)
        return self.sal((self.norma(voz) * w[None, None, :, None]).sum(2))

    def pesos_capas(self):
        return torch.softmax(self.pesos.detach(), 0).cpu().numpy().round(3).tolist()


class Tronco(nn.Module):
    def __init__(self, k, d=384, capas=6, cabezas=None, drop=0.2, n_art=13, n_fon=35):
        super().__init__()
        cabezas = cabezas or max(1, d // 64)
        self.voz = SumaCapas(k, d)
        self.art = nn.Linear(n_art, d)
        self.fon = nn.Embedding(n_fon, d)
        self.conv = nn.Conv1d(d, d, 5, padding=2, groups=d)
        capa = nn.TransformerEncoderLayer(d, cabezas, 4 * d, dropout=drop, batch_first=True, norm_first=True, activation='gelu')
        self.cuerpo = nn.TransformerEncoder(capa, capas, enable_nested_tensor=False)
        self.norma = nn.LayerNorm(d)

    def entrada(self, voz, art, fon):
        h = self.voz(voz) + self.art(art) + self.fon(fon)
        return h + self.conv(h.transpose(1, 2)).transpose(1, 2)

    def forward(self, voz, art, fon, extra=None):
        h = self.entrada(voz, art, fon)
        if extra is not None:
            h = h + extra
        return self.norma(self.cuerpo(h))


class Boca(nn.Module):
    """Voz + Blender + fonema → columnas de la boca (ARKit vía mapa SMIRK) y mandíbula."""

    def __init__(self, k, sal, d=384, capas=6, cabezas=None, drop=0.2, n_art=13):
        super().__init__()
        self.tronco = Tronco(k, d, capas, cabezas, drop, n_art)
        self.salida = nn.Linear(d, sal)
        self.base = nn.Linear(n_art, sal)

    def forward(self, voz, art, fon):
        return self.base(art) + self.salida(self.tronco(voz, art, fon))


def tiempo_sinusoidal(t, d):
    """t en [0,1] [B] → [B, d]"""
    f = torch.exp(-math.log(10000) * torch.arange(0, d, 2, device=t.device) / d)
    ang = t[:, None] * 1000 * f[None]
    return torch.cat([ang.sin(), ang.cos()], 1)


class NoVerbal(nn.Module):
    """Campo de velocidad v(x_t, t | voz, habla, estilo) para flow matching sobre [B, L, C]."""

    def __init__(self, k, c, d=256, capas=4, cabezas=None, drop=0.1, n_art=13, n_estilo=0):
        super().__init__()
        self.c, self.d, self.n_estilo = c, d, n_estilo
        self.tronco = Tronco(k, d, capas, cabezas, drop, n_art)
        self.x = nn.Linear(c, d)
        self.t = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, d))
        self.estilo = nn.Linear(n_estilo, d) if n_estilo else None
        self.salida = nn.Linear(d, c)
        nn.init.zeros_(self.salida.weight); nn.init.zeros_(self.salida.bias)

    def forward(self, xt, t, voz, art, fon, estilo=None, sin_voz=None):
        """sin_voz: máscara [B] bool: esas muestras van sin condición de voz (para la guía)."""
        if sin_voz is not None:
            voz = voz * (~sin_voz)[:, None, None, None].float()
        extra = self.x(xt) + self.t(tiempo_sinusoidal(t, self.d))[:, None]
        if self.estilo is not None and estilo is not None:
            extra = extra + self.estilo(estilo)[:, None]
        return self.salida(self.tronco(voz, art, fon, extra))

    @torch.no_grad()
    def muestrear(self, voz, art, fon, estilo=None, pasos=32, guia=1.5, generador=None, ventana=500, solape=50):
        """Euler desde ruido N(0,1) hasta la muestra; guía sin clasificador sobre la voz. Las secuencias
        más largas que `ventana` se muestrean por trozos con fundido lineal de `solape` fotogramas."""
        B, T = voz.shape[:2]
        if T > ventana:
            out = torch.zeros(B, T, self.c, device=voz.device); peso = torch.zeros(1, T, 1, device=voz.device)
            for i in range(0, max(1, T - solape), ventana - solape):
                j = min(T, i + ventana)
                x = self.muestrear(voz[:, i:j], art[:, i:j], fon[:, i:j], estilo, pasos, guia, generador, ventana, solape)
                w = torch.ones(1, j - i, 1, device=voz.device)
                if i > 0:
                    w[:, :solape] = torch.linspace(0, 1, solape, device=voz.device)[None, :, None]
                if j < T:
                    w[:, -solape:] = torch.linspace(1, 0, solape, device=voz.device)[None, :, None]
                out[:, i:j] += x * w; peso[:, i:j] += w
                if j == T:
                    break
            return out / peso.clamp(min=1e-6)
        x = torch.randn(B, T, self.c, generator=generador, device=voz.device)
        for i in range(pasos):
            t = torch.full((B,), i / pasos, device=voz.device)
            v = self(x, t, voz, art, fon, estilo)
            if guia != 1.0:
                v0 = self(x, t, voz, art, fon, estilo, sin_voz=torch.ones(B, dtype=torch.bool, device=voz.device))
                v = v0 + guia * (v - v0)
            x = x + v / pasos
        return x


# ---------------------------------------------------------------- entrenamiento común
def semillas(s):
    torch.manual_seed(s); np.random.seed(s); random.seed(s)


def ema_actualizar(ema, red, paso):
    dec = min(0.999, (1 + paso) / (10 + paso))
    with torch.no_grad():
        for pe, pr in zip(ema.parameters(), red.parameters()):
            pe.mul_(dec).add_(pr.detach(), alpha=1 - dec)


def planificador(opt, pasos_epoca, epocas, calentamiento=5):
    calent, total = calentamiento * pasos_epoca, epocas * pasos_epoca
    f = lambda s: min(1.0, (s + 1) / calent) * 0.5 * (1 + math.cos(math.pi * min(1.0, s / total)))
    return torch.optim.lr_scheduler.LambdaLR(opt, f)


def guardar_estado(ruta, red, ema, opt, sched, escala, **resto):
    torch.save({'red': red.state_dict(), 'ema': ema.state_dict(), 'opt': opt.state_dict(), 'sched': sched.state_dict(),
                'escala': escala.state_dict(), 'rng': torch.get_rng_state(), 'np_rng': np.random.get_state(), **resto},
               ruta + '.tmp')
    os.replace(ruta + '.tmp', ruta)


def cargar_estado(ruta, red, ema, opt, sched, escala, dispositivo):
    """Devuelve el dict con lo demás (época, mejor, ...) o None si no hay checkpoint."""
    if not os.path.exists(ruta):
        return None
    e = torch.load(ruta, map_location=dispositivo, weights_only=False)
    red.load_state_dict(e['red']); ema.load_state_dict(e['ema']); opt.load_state_dict(e['opt'])
    sched.load_state_dict(e['sched']); escala.load_state_dict(e['escala'])
    torch.set_rng_state(e['rng'].cpu()); np.random.set_state(e['np_rng'])
    return {k: v for k, v in e.items() if k not in ('red', 'ema', 'opt', 'sched', 'escala', 'rng', 'np_rng')}


def anotar(salida, linea):
    """Una línea JSON por época en progreso.json (añadiendo) y por pantalla."""
    with open(os.path.join(salida, 'progreso.json'), 'a') as f:
        f.write(json.dumps(linea) + '\n')
    print(json.dumps(linea), flush=True)


def correlaciones(P, T, columnas):
    return {c: (round(float(np.corrcoef(P[:, k], T[:, k])[0, 1]), 3) if T[:, k].std() > 1e-6 and P[:, k].std() > 1e-6 else None)
            for k, c in enumerate(columnas)}


def media_grupos(r, grupos, columnas):
    out = {}
    for g, cs in grupos.items():
        v = [r[c] for c in cs if c in columnas and r.get(c) is not None]
        out[g] = round(float(np.mean(v)), 3) if v else None
    return out


def aumentar_voz(voz, L, dev, ruido=0.05, mascaras=2, p_apagar=0.2):
    """Ruido, máscaras de tiempo y, a veces, la voz entera apagada (obliga a usar la articulación)."""
    B = voz.shape[0]
    voz = voz + ruido * torch.randn_like(voz)
    tt = torch.arange(L, device=dev)[None]
    for _ in range(mascaras):
        ini = torch.randint(0, L, (B, 1), device=dev); lg = torch.randint(0, L // 10, (B, 1), device=dev)
        voz = voz * ~((tt >= ini) & (tt < ini + lg))[..., None, None]
    return voz * (torch.rand(B, 1, 1, 1, device=dev) > p_apagar)
