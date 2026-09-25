"""Base de referencia: pose por fonema + dominancia de Cohen-Massaro, y las dos
varas con que se compara (escalón por fonema y el calendario de claves de
`animacion.ts`). Evaluación dejando un hablante fuera.

Modelo, por control k:
  D_s(t) = α[p,k] · exp(-θa[p,k] · (c_s - t))   si t < c_s   (anticipación)
         = α[p,k] · exp(-θc[p,k] · (t - c_s))   si t ≥ c_s   (arrastre)
  y(t)   = Σ_s D_s(t) T[p,k] / Σ_s D_s(t)
con p el fonema del segmento s y c_s su centro.

Uso: python base_dominancia.py --datos DIR_hablantes --salida resultados.json
"""
import argparse
import glob
import json
import os
import re

import numpy as np
import torch

SILENCIO = {'', 'sil', 'sp', 'spn', '<eps>'}


def fonema(f):
    f = re.sub(r'\d', '', f).lower()
    return 'sil' if f in SILENCIO else f


def cargar(ruta):
    # Archivos propios de `datos_fonemas.py` (arrays de objetos): ver allí.
    d = np.load(ruta, allow_pickle=True)
    frases = []
    for t, y, fon in zip(d['t'], d['y'], d['fon']):
        segs = [(fonema(f), float(a), float(b)) for f, a, b in fon]
        frases.append((np.asarray(t, np.float32), np.asarray(y, np.float32), segs))
    return frases, list(d['controles'])


class Dominancia(torch.nn.Module):
    def __init__(self, n_fon, n_ctl):
        super().__init__()
        self.T = torch.nn.Parameter(torch.zeros(n_fon, n_ctl))
        self.la = torch.nn.Parameter(torch.zeros(n_fon, n_ctl))
        self.lta = torch.nn.Parameter(torch.full((n_fon, n_ctl), np.log(12.0)))
        self.ltc = torch.nn.Parameter(torch.full((n_fon, n_ctl), np.log(12.0)))

    def forward(self, t, ids, c):
        # t [F], ids [S], c [S] → [F, K]
        dt = c[None, :] - t[:, None]                          # >0: el segmento aún no llega
        th = torch.where(dt[..., None] > 0, self.lta.exp()[ids][None], self.ltc.exp()[ids][None])
        logd = self.la[ids][None] - th * dt.abs()[..., None]  # [F, S, K]
        w = torch.softmax(logd, dim=1)
        return (w * self.T[ids][None]).sum(1)


def tensores(frase, idx):
    t, y, segs = frase
    ids = torch.tensor([idx[p] for p, _, _ in segs])
    c = torch.tensor([(a + b) / 2 for _, a, b in segs], dtype=torch.float32)
    return torch.from_numpy(t), torch.from_numpy(y), ids, c


def entrenar(frases, idx, n_ctl, pasos=400):
    m = Dominancia(len(idx), n_ctl)
    # Arranque: T = media del control en los fotogramas de cada fonema.
    suma, n = np.zeros((len(idx), n_ctl)), np.zeros((len(idx), 1))
    for t, y, segs in frases:
        for p, a, b in segs:
            sel = (t >= a) & (t < b)
            suma[idx[p]] += y[sel].sum(0); n[idx[p]] += sel.sum()
    with torch.no_grad():
        m.T.copy_(torch.from_numpy(suma / np.maximum(n, 1)).float())
    opt = torch.optim.Adam(m.parameters(), lr=0.03)
    datos = [tensores(f, idx) for f in frases]
    for paso in range(pasos):
        opt.zero_grad()
        perm = np.random.permutation(len(datos))[:128]
        perdida = sum(((m(t, ids, c) - y) ** 2).mean() for t, y, ids, c in (datos[i] for i in perm)) / len(perm)
        perdida.backward()
        opt.step()
    return m, suma / np.maximum(n, 1)


def escalon(frase, idx, medias):
    t, _, segs = frase
    y = np.zeros((len(t), medias.shape[1]), np.float32)
    for p, a, b in segs:
        y[(t >= a) & (t < b)] = medias[idx[p]]
    return y


def suavizar(u):
    return np.where(u < 0.5, 2 * u * u, 1 - (-2 * u + 2) ** 2 / 2)


# Consonantes oclusivas en ARPAbet: su clave va a 0,45/0,80 del tramo (`lineaPalabra`).
OCLUSIVAS = {'p', 'b', 't', 'd', 'k', 'g'}


def reglas(frase, idx, medias):
    """El calendario de `lineaPalabra`: cada sonido sostiene su pose entre dos
    claves (0,38–0,72 del tramo; oclusivas 0,45–0,80) y entre claves se pasa
    con la misma curva `suavizar`. Mismas poses objetivo que el escalón (la
    media medida), para comparar solo la dinámica."""
    t, _, segs = frase
    kt, kv = [], []
    for p, a, b in segs:
        d = b - a
        f0, f1 = (0.45, 0.8) if p in OCLUSIVAS else (0.38, 0.72)
        for f in (f0, f1):
            kt.append(a + f * d); kv.append(medias[idx[p]])
    kt, kv = np.array(kt), np.array(kv)
    y = np.zeros((len(t), kv.shape[1]), np.float32)
    for i, x in enumerate(t):
        j = np.searchsorted(kt, x)
        if j == 0:
            y[i] = kv[0]
        elif j >= len(kt):
            y[i] = kv[-1]
        else:
            u = (x - kt[j - 1]) / max(1e-6, kt[j] - kt[j - 1])
            y[i] = kv[j - 1] + (kv[j] - kv[j - 1]) * suavizar(u)
    return y


def metricas(pred, real, fps=25.0, max_lag=5):
    rmse = np.sqrt(((pred - real) ** 2).mean(0))
    r, lag = [], []
    for k in range(real.shape[1]):
        a, b = pred[:, k] - pred[:, k].mean(), real[:, k] - real[:, k].mean()
        den = np.sqrt((a * a).sum() * (b * b).sum()) or 1.0
        r.append((a * b).sum() / den)
        cc = [np.dot(np.roll(a, s), b) for s in range(-max_lag, max_lag + 1)]
        lag.append((np.argmax(cc) - max_lag) * 1000 / fps)   # >0: la predicción va tarde
    return rmse, np.array(r), np.array(lag)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--datos', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--pasos', type=int, default=400)
    a = ap.parse_args()
    torch.manual_seed(0); np.random.seed(0)
    hablantes = {os.path.splitext(os.path.basename(p))[0]: cargar(p) for p in sorted(glob.glob(os.path.join(a.datos, '*.npz')))}
    controles = next(iter(hablantes.values()))[1]
    fonemas = sorted({p for fr, _ in hablantes.values() for _, _, segs in fr for p, _, _ in segs})
    idx = {p: i for i, p in enumerate(fonemas)}
    res = {'controles': controles, 'pliegues': {}}
    for prueba in hablantes:
        train = [f for h, (fr, _) in hablantes.items() if h != prueba for f in fr]
        m, medias = entrenar(train, idx, len(controles), a.pasos)
        filas = {'dominancia': [], 'escalon': [], 'reglas': []}
        for fr in hablantes[prueba][0]:
            t, y, ids, c = tensores(fr, idx)
            with torch.no_grad():
                p_dom = m(t, ids, c).numpy()
            for nombre, pred in (('dominancia', p_dom), ('escalon', escalon(fr, idx, medias)), ('reglas', reglas(fr, idx, medias))):
                filas[nombre].append(metricas(pred, fr[1]))
        res['pliegues'][prueba] = {
            n: {'rmse': np.mean([x[0] for x in v], 0).round(3).tolist(),
                'pearson': np.mean([x[1] for x in v], 0).round(3).tolist(),
                'desfase_ms': np.mean([x[2] for x in v], 0).round(1).tolist()}
            for n, v in filas.items()}
        res['pliegues'][prueba]['n_frases'] = len(hablantes[prueba][0])
        print(prueba, {n: round(float(np.mean(r['pearson'])), 3) for n, r in res['pliegues'][prueba].items() if n != 'n_frases'}, flush=True)
        torch.save({'estado': m.state_dict(), 'fonemas': fonemas, 'controles': controles},
                   os.path.join(os.path.dirname(a.salida), f'dominancia_sin_{prueba}.pt'))
    json.dump(res, open(a.salida, 'w', encoding='utf8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
