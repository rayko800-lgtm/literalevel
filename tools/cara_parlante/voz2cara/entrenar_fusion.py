"""Red de fusión de Eos: el modelo articulatorio de Blender + la voz → los 52 gestos ARKit y la cabeza.

La boca de Blender (boca3d) es precisa fonema a fonema pero seca al encadenarlos; la red
voz→cara es natural pero imprecisa. Aquí la red recibe las dos cosas por fotograma:
  - la voz (rasgos wav2vec2 de extraer.py, 768);
  - lo que haría Blender (preparar_art.py: 12 controles del modelo articulatorio + «habla»)
    y el fonema que suena (embebido).
y la salida es «Blender + corrección»: una capa lineal directa desde los controles de Blender
(la base anatómica) más lo que añade el transformer (coarticulación, sonrisa, cejas, cabeza).

Técnicas: transformer pre-norm de 6 capas (d=384) con conv local, dropout 0,2, máscaras de
tiempo sobre la voz y a veces la voz entera apagada (obliga a usar la articulación), ruido,
AdamW con calentamiento y coseno, media exponencial de pesos (EMA), float16/bfloat16 mixto,
validación cada época con parada temprana, y se guarda el mejor modelo (no el último).

Objetivo: blendshapes y pose medidos (MediaPipe) menos su media en el clip, entre la sd global.
Validación: la carpeta val de 1KH, 1 de cada 8 vídeos de YouTube de 1KH y 1 de cada 8 de Obama.

Uso: python entrenar_fusion.py --voz DIR --art DIR --medidas DIR --salida DIR
         [--epocas 500] [--paciencia 40] [--dispositivo cuda]
Deja en --salida: modelo.pt (mejor época, pesos EMA), normalizacion.json, informe.json y
progreso.json (una línea por época, para seguirlo desde Drive).
"""
import argparse
import copy
import glob
import json
import math
import os
import time
import zlib

import numpy as np
import torch
import torch.nn as nn

GRUPOS = {
    'boca': ['jawOpen', 'mouthClose', 'mouthFunnel', 'mouthPucker', 'mouthPressLeft', 'mouthPressRight',
             'mouthRollLower', 'mouthRollUpper', 'mouthLowerDownLeft', 'mouthLowerDownRight',
             'mouthUpperUpLeft', 'mouthUpperUpRight', 'mouthStretchLeft', 'mouthStretchRight'],
    'sonrisa': ['mouthSmileLeft', 'mouthSmileRight', 'cheekSquintLeft', 'cheekSquintRight'],
    'ojos': ['eyeBlinkLeft', 'eyeBlinkRight', 'eyeSquintLeft', 'eyeSquintRight', 'eyeWideLeft', 'eyeWideRight'],
    'cejas': ['browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 'browDownLeft', 'browDownRight'],
}
N_FON = 35          # 34 fonemas del modelo articulatorio + silencio
L = 250             # ventana de entrenamiento (fotogramas)


class Fusion(nn.Module):
    def __init__(self, n_art=13, sal=55, d=384, capas=6, cabezas=6, drop=0.2):
        super().__init__()
        self.voz = nn.Sequential(nn.LayerNorm(768), nn.Dropout(0.1), nn.Linear(768, d))
        self.art = nn.Linear(n_art, d)
        self.fon = nn.Embedding(N_FON, d)
        self.conv = nn.Conv1d(d, d, 5, padding=2, groups=d)
        capa = nn.TransformerEncoderLayer(d, cabezas, 4 * d, dropout=drop, batch_first=True, norm_first=True,
                                          activation='gelu')
        self.cuerpo = nn.TransformerEncoder(capa, capas, enable_nested_tensor=False)
        self.norma = nn.LayerNorm(d)
        self.salida = nn.Linear(d, sal)
        self.base = nn.Linear(n_art, sal)      # Blender directo: la anatomía que la red corrige

    def forward(self, voz, art, fon):
        h = self.voz(voz) + self.art(art) + self.fon(fon)
        h = h + self.conv(h.transpose(1, 2)).transpose(1, 2)
        return self.base(art) + self.salida(self.norma(self.cuerpo(h)))


def pares(dir_voz, dir_art, dir_med):
    def mapa(d):
        return {os.path.splitext(os.path.basename(f))[0]: f
                for f in glob.glob(os.path.join(d, '**', '*.npz'), recursive=True)}
    voz, art, med = mapa(dir_voz), mapa(dir_art), mapa(dir_med)
    return [(n, voz[n], art[n], med[n]) for n in sorted(med) if n in voz and n in art]


def cargar(fv, fa, fm):
    v, a, m = np.load(fv), np.load(fa), np.load(fm)
    ok = m['ok'].astype(bool)
    if ok.mean() < 0.6 or len(ok) < 75:
        return None
    y = np.concatenate([m['bs'].astype(np.float32), np.nan_to_num(m['pose'].astype(np.float32))], 1)
    y = y - y[ok].mean(0)
    y[~ok] = 0
    fon = a['fon'].astype(np.int64)
    fon[fon < 0] = N_FON - 1
    return (v['voz'].astype(np.float16), a['art'].astype(np.float16), fon, y, ok,
            list(m['bs_nombres']), float(m['t'][-1] - m['t'][0]))


def correlaciones(P, T, col):
    r = {c: float(np.corrcoef(P[:, k], T[:, k])[0, 1]) if T[:, k].std() > 1e-6 else None
         for k, c in enumerate(col)}
    g = {n: round(float(np.nanmean([r[c] for c in cs if r.get(c) is not None])), 3) for n, cs in GRUPOS.items()}
    g['cabeza'] = round(float(np.mean([r[c] for c in col[-3:]])), 3)
    return r, g


def pedagogia(P, T, F, col, fonemas):
    """¿Cierra los labios en p/b/m y los redondea en u/o? Diferencia media (en sd) entre esos
    fonemas y las vocales abiertas, en la predicción y en las caras reales."""
    i = {c: k for k, c in enumerate(col)}
    idx = {f: k for k, f in enumerate(fonemas)}
    def m(A, conj, cols):
        sel = np.isin(F, [idx[f] for f in conj if f in idx])
        return float(A[sel][:, [i[c] for c in cols]].mean()) if sel.any() else float('nan')
    abiertas = ['aa', 'ae', 'ah', 'ao']
    out = {}
    for nombre, conj, cols in [('cierre_pbm', ['p', 'b', 'm'], ['mouthClose', 'mouthPressLeft', 'mouthPressRight']),
                               ('redondeo_uo', ['uw', 'ow', 'w'], ['mouthPucker', 'mouthFunnel'])]:
        out[nombre] = {'red': round(m(P, conj, cols) - m(P, abiertas, cols), 3),
                       'real': round(m(T, conj, cols) - m(T, abiertas, cols), 3)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voz', required=True)
    ap.add_argument('--art', required=True)
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--modelo_art', default=None, help='modelo_articulatorio.json (para los nombres de fonema)')
    ap.add_argument('--epocas', type=int, default=500)
    ap.add_argument('--paciencia', type=int, default=40)
    ap.add_argument('--lote', type=int, default=64)
    ap.add_argument('--lr', type=float, default=5e-4)
    ap.add_argument('--dispositivo', default='cuda' if torch.cuda.is_available() else 'cpu')
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    torch.manual_seed(0); np.random.seed(0)
    dev = a.dispositivo
    fonemas = json.load(open(a.modelo_art))['fonemas'] if a.modelo_art else []

    externo = lambda f: any(k in f for k in ('obama', 'casa_blanca', 'miralles'))
    def es_val(i, n, fm):
        if os.sep + 'val' + os.sep in fm.replace('/', os.sep):
            return True
        return (i % 8 == 0) if externo(fm) else zlib.crc32(n.rsplit('_', 1)[0].encode()) % 8 == 0

    todos = pares(a.voz, a.art, a.medidas)
    elegidos = []
    for i, (n, fv, fa, fm) in enumerate(todos):
        m = np.load(fm)
        if m['ok'].mean() >= 0.6 and len(m['t']) >= 75:
            elegidos.append((es_val(i, n, fm), fv, fa, fm, len(m['t'])))
    total = sum(max(lg, L) for v, _, _, _, lg in elegidos if not v)
    Xv = np.zeros((total, 768), np.float16)
    Xa = np.zeros((total, 13), np.float16)
    Xf = np.full(total, N_FON - 1, np.int64)
    val, Ys, Ms, inicios, pos, nombres, horas = [], [], [], [], 0, None, 0.0
    for v, fv, fa, fm, _ in elegidos:
        r = cargar(fv, fa, fm)
        if r is None:
            continue
        xv, xa, xf, y, ok, nombres, dur = r
        k = min(len(xv), len(xa), len(y))
        xv, xa, xf, y, ok = xv[:k], xa[:k], xf[:k], y[:k], ok[:k]
        if v:
            val.append((xv, xa, xf, y, ok)); continue
        Xv[pos:pos + k], Xa[pos:pos + k], Xf[pos:pos + k] = xv, xa, xf
        pad = max(0, L - k)
        Ys.append(np.pad(y, ((0, pad), (0, 0)))); Ms.append(np.pad(ok, (0, pad)))
        inicios += [pos + j for j in range(0, max(k, L) - L + 1, L // 2)]
        pos += max(k, L); horas += dur / 3600
    Yn, Mn = np.concatenate(Ys), np.concatenate(Ms); del Ys, Ms
    sd = Yn[Mn].std(0) + 1e-3
    col = nombres + ['cabeza_guinada', 'cabeza_cabeceo', 'cabeza_alabeo']
    peso = torch.ones(len(col))
    for c in GRUPOS['boca']:
        if c in col:
            peso[col.index(c)] = 2.0          # la boca es lo pedagógico: pesa el doble
    print(f'entrenamiento {len(inicios)} ventanas ({horas:.1f} h), validación {len(val)} clips', flush=True)

    # todo a la GPU si cabe (A100): sin copias CPU→GPU en cada lote
    donde = dev
    try:
        Xv_t, Xa_t, Xf_t = torch.from_numpy(Xv).to(donde), torch.from_numpy(Xa).to(donde), torch.from_numpy(Xf).to(donde)
        Y_t, M_t = torch.from_numpy((Yn / sd).astype(np.float32)).to(donde), torch.from_numpy(Mn).to(donde)
    except RuntimeError:
        donde = 'cpu'
        Xv_t, Xa_t, Xf_t = torch.from_numpy(Xv), torch.from_numpy(Xa), torch.from_numpy(Xf)
        Y_t, M_t = torch.from_numpy((Yn / sd).astype(np.float32)), torch.from_numpy(Mn)
    del Xv, Xa, Xf, Yn, Mn
    inicios, rango, peso = torch.tensor(inicios, device=donde), torch.arange(L, device=donde), peso.to(dev)

    red = Fusion(sal=len(col)).to(dev)
    ema = copy.deepcopy(red).eval()
    for p in ema.parameters():
        p.requires_grad_(False)
    opt = torch.optim.AdamW(red.parameters(), a.lr, weight_decay=0.05)
    pasos_ep = (len(inicios) + a.lote - 1) // a.lote
    calent = 5 * pasos_ep
    total_pasos = a.epocas * pasos_ep
    lr_f = lambda s: min(1.0, (s + 1) / calent) * 0.5 * (1 + math.cos(math.pi * min(1.0, s / total_pasos)))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lr_f)
    gpu = dev.startswith('cuda')
    bf16 = gpu and torch.cuda.is_bf16_supported()
    tipo = torch.bfloat16 if bf16 else torch.float16
    escala = torch.amp.GradScaler(enabled=gpu and not bf16)

    def validar(modelo):
        P, T, F = [], [], []
        with torch.no_grad(), torch.autocast('cuda' if gpu else 'cpu', dtype=tipo, enabled=gpu):
            for xv, xa, xf, y, ok in val:
                trozos = []
                for k in range(0, len(xv), 1000):
                    tv = torch.from_numpy(xv[k:k + 1000]).to(dev).float()[None]
                    ta = torch.from_numpy(xa[k:k + 1000]).to(dev).float()[None]
                    tf = torch.from_numpy(xf[k:k + 1000]).to(dev)[None]
                    trozos.append(modelo(tv, ta, tf)[0].float().cpu().numpy())
                p = np.concatenate(trozos) * sd
                P.append(p[ok]); T.append(y[ok]); F.append(xf[ok])
        return np.concatenate(P), np.concatenate(T), np.concatenate(F)

    mejor, mejor_ep, sin_mejora, paso = -1.0, 0, 0, 0
    prog = open(os.path.join(a.salida, 'progreso.json'), 'w')
    for ep in range(a.epocas):
        t0 = time.time()
        red.train(); perm = torch.randperm(len(inicios), device=donde); tot = 0.0
        for i in range(0, len(perm), a.lote):
            idx = inicios[perm[i:i + a.lote]][:, None] + rango
            xv, xa, xf = Xv_t[idx].to(dev).float(), Xa_t[idx].to(dev).float(), Xf_t[idx].to(dev)
            y, m = Y_t[idx].to(dev), M_t[idx].to(dev).unsqueeze(-1).float()
            B = xv.shape[0]
            # aumentos: ruido, 2 máscaras de tiempo en la voz y, a veces, la voz entera apagada
            xv = xv + 0.05 * torch.randn_like(xv)
            for _ in range(2):
                ini = torch.randint(0, L, (B, 1), device=dev); lg = torch.randint(0, L // 10, (B, 1), device=dev)
                tt = torch.arange(L, device=dev)[None]
                xv = xv * ~((tt >= ini) & (tt < ini + lg))[..., None]
            xv = xv * (torch.rand(B, 1, 1, device=dev) > 0.2)
            with torch.autocast('cuda' if gpu else 'cpu', dtype=tipo, enabled=gpu):
                p = red(xv, xa, xf)
            p = p.float()
            w = peso[None, None, :]
            l1 = ((p - y) ** 2 * m * w).sum() / (m.sum() * w.sum())
            dv = (p[:, 1:] - p[:, :-1]) - (y[:, 1:] - y[:, :-1])
            l2 = (dv ** 2 * m[:, 1:] * m[:, :-1] * w).sum() / (m.sum() * w.sum())
            loss = l1 + 0.5 * l2
            opt.zero_grad(set_to_none=True)
            escala.scale(loss).backward(); escala.unscale_(opt)
            nn.utils.clip_grad_norm_(red.parameters(), 1.0)
            escala.step(opt); escala.update(); sched.step(); paso += 1
            with torch.no_grad():
                dec = min(0.999, (1 + paso) / (10 + paso))
                for pe, pr in zip(ema.parameters(), red.parameters()):
                    pe.mul_(dec).add_(pr.detach(), alpha=1 - dec)
            tot += loss.item() * B
        P, T, F = validar(ema)
        _, g = correlaciones(P, T, col)
        nota = float(np.mean(list(g.values())))          # media de boca, sonrisa, ojos, cejas y cabeza
        linea = {'epoca': ep + 1, 'perdida': round(tot / len(perm), 4), 'r': g, 'nota': round(nota, 4),
                 'lr': round(sched.get_last_lr()[0], 6), 's': round(time.time() - t0, 1)}
        if nota > mejor:
            mejor, mejor_ep, sin_mejora = nota, ep + 1, 0
            torch.save(ema.state_dict(), os.path.join(a.salida, 'modelo.pt'))
            linea['mejor'] = True
        else:
            sin_mejora += 1
        prog.write(json.dumps(linea) + '\n'); prog.flush()
        print(json.dumps(linea), flush=True)
        if sin_mejora >= a.paciencia:
            print(f'parada temprana: sin mejorar desde la época {mejor_ep}', flush=True)
            break

    ema.load_state_dict(torch.load(os.path.join(a.salida, 'modelo.pt'), map_location=dev, weights_only=True))
    P, T, F = validar(ema)
    r, g = correlaciones(P, T, col)
    json.dump({'columnas': col, 'sd': sd.tolist(), 'arquitectura': 'Fusion d=384 capas=6'},
              open(os.path.join(a.salida, 'normalizacion.json'), 'w'))
    informe = {'ventanas_entrenamiento': len(inicios), 'horas_entrenamiento': round(horas, 2),
               'clips_validacion': len(val), 'mejor_epoca': mejor_ep, 'epocas_hechas': ep + 1,
               'r_grupos': g, 'r': {k: (round(v, 3) if v is not None else None) for k, v in r.items()}}
    if fonemas:
        informe['pedagogia'] = pedagogia(P / sd, T / sd, F, col, fonemas)
    json.dump(informe, open(os.path.join(a.salida, 'informe.json'), 'w'), indent=1)
    print('mejor época', mejor_ep, 'r por grupo:', g, flush=True)
    print('FIN', flush=True)


if __name__ == '__main__':
    main()
