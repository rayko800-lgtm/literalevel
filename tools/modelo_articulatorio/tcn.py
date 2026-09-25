"""Opción 2: red convolucional temporal (TCN) no causal sobre la secuencia de
fonemas con sus tiempos, muestreada a los fotogramas del vídeo. No causal a
propósito: la app conoce la frase entera antes de animarla.

Entrada por fotograma: fonema (embedding), fracción recorrida del fonema,
duración del fonema (s) y si es vocal acentuada. Salida: los K controles.

Mismas métricas y mismo reparto por hablantes que `base_dominancia.py`.

Uso: python tcn.py --datos DIR --salida resultados_tcn.json [--prueba s3 ...]
"""
import argparse
import glob
import json
import os
import re

import numpy as np
import torch
from torch import nn

from base_dominancia import cargar, metricas

ACENTO = re.compile(r'1$')


def cargar_con_acento(ruta):
    # Igual que `cargar`, pero conserva el dígito de acento de ARPAbet.
    d = np.load(ruta, allow_pickle=True)   # archivo propio de datos_fonemas.py
    frases = []
    for t, y, fon in zip(d['t'], d['y'], d['fon']):
        segs = [(re.sub(r'\d', '', f).lower() or 'sil', float(a), float(b), 1.0 if ACENTO.search(f) else 0.0)
                for f, a, b in fon]
        frases.append((np.asarray(t, np.float32), np.asarray(y, np.float32), segs))
    return frases


def entrada(frase, idx):
    t, _, segs = frase
    ids = np.zeros(len(t), np.int64)
    extra = np.zeros((len(t), 3), np.float32)
    for p, a, b, ac in segs:
        sel = (t >= a) & (t < b)
        ids[sel] = idx.get(p, 0)
        extra[sel, 0] = (t[sel] - a) / max(b - a, 1e-3)
        extra[sel, 1] = b - a
        extra[sel, 2] = ac
    return torch.from_numpy(ids), torch.from_numpy(extra)


class TCN(nn.Module):
    def __init__(self, n_fon, n_ctl, canales=64, emb=32, dilataciones=(1, 2, 4, 8), k=5, drop=0.1):
        super().__init__()
        self.emb = nn.Embedding(n_fon, emb)
        self.entrada = nn.Conv1d(emb + 3, canales, 1)
        self.bloques = nn.ModuleList(
            nn.Sequential(nn.Conv1d(canales, canales, k, dilation=d, padding=d * (k - 1) // 2), nn.GELU(), nn.Dropout(drop))
            for d in dilataciones)
        self.salida = nn.Conv1d(canales, n_ctl, 1)

    def forward(self, ids, extra):
        # ids [B, T], extra [B, T, 3] → [B, T, K]
        x = torch.cat([self.emb(ids), extra], -1).transpose(1, 2)
        h = self.entrada(x)
        for b in self.bloques:
            h = h + b(h)
        return self.salida(h).transpose(1, 2)


def lote(datos):
    T = max(len(d[0]) for d in datos)
    B, K = len(datos), datos[0][2].shape[1]
    ids = torch.zeros(B, T, dtype=torch.long); ex = torch.zeros(B, T, 3)
    y = torch.zeros(B, T, K); m = torch.zeros(B, T, 1)
    for i, (a, e, yy) in enumerate(datos):
        n = len(a)
        ids[i, :n], ex[i, :n], y[i, :n], m[i, :n] = a, e, yy, 1
    return ids, ex, y, m


def entrenar(frases, idx, K, epocas=30, semilla=0):
    torch.manual_seed(semilla); np.random.seed(semilla)
    datos = [(*entrada(f, idx), torch.from_numpy(f[1])) for f in frases]
    m = TCN(len(idx), K)
    opt = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epocas)
    for ep in range(epocas):
        m.train()
        orden = np.random.permutation(len(datos))
        for i in range(0, len(datos), 32):
            ids, ex, y, mk = lote([datos[j] for j in orden[i:i + 32]])
            opt.zero_grad()
            perdida = (((m(ids, ex) - y) ** 2) * mk).sum() / (mk.sum() * y.shape[2])
            perdida.backward()
            opt.step()
        sched.step()
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--datos', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--epocas', type=int, default=30)
    ap.add_argument('--prueba', nargs='*', help='hablantes de prueba; por defecto, uno fuera cada vez')
    a = ap.parse_args()
    hablantes = {os.path.splitext(os.path.basename(p))[0]: cargar_con_acento(p) for p in sorted(glob.glob(os.path.join(a.datos, '*.npz')))}
    controles = cargar(next(iter(sorted(glob.glob(os.path.join(a.datos, '*.npz'))))))[1]
    fonemas = ['<pad>'] + sorted({s[0] for fr in hablantes.values() for f in fr for s in f[2]})
    idx = {p: i for i, p in enumerate(fonemas)}
    pliegues = [[p] for p in hablantes] if not a.prueba else [a.prueba]
    res = {'controles': controles, 'pliegues': {}}
    for prueba in pliegues:
        train = [f for h, fr in hablantes.items() if h not in prueba for f in fr]
        m = entrenar(train, idx, len(controles), a.epocas)
        m.eval()
        filas = []
        for h in prueba:
            for fr in hablantes[h]:
                ids, ex = entrada(fr, idx)
                with torch.no_grad():
                    pred = m(ids[None], ex[None])[0].numpy()
                filas.append(metricas(pred, fr[1]))
        clave = '+'.join(prueba)
        res['pliegues'][clave] = {'tcn': {
            'rmse': np.mean([x[0] for x in filas], 0).round(3).tolist(),
            'pearson': np.mean([x[1] for x in filas], 0).round(3).tolist(),
            'desfase_ms': np.mean([x[2] for x in filas], 0).round(1).tolist()}, 'n_frases': len(filas)}
        print(clave, round(float(np.mean(res['pliegues'][clave]['tcn']['pearson'])), 3), flush=True)
        n_par = sum(p.numel() for p in m.parameters())
        res['parametros'] = n_par
        torch.save({'estado': m.state_dict(), 'fonemas': fonemas, 'controles': [str(c) for c in controles]},
                   os.path.join(os.path.dirname(a.salida) or '.', f'tcn_sin_{clave}.pt'))
    json.dump(res, open(a.salida, 'w', encoding='utf8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
