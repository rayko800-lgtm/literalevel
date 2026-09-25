"""USC-TIMIT EMA → el mismo formato de conjunto que `datos_fonemas.py`.

Cada .mat (formato mview) trae 5 frases seguidas: AUDIO y seis sensores
(UL, LL, JAW, TD, TB, TT) en 3D a 100 Hz, ya en coordenadas de cabeza:
x hacia delante, y hacia arriba, z lateral (comprobado: UL por delante de TD
y por encima de LL). El .trans del mismo nombre da los fonemas (ARPAbet en
minúsculas) con tiempos. Se corta por frase (columna 6 del .trans).

Controles (z por hablante):
  mandibula      −y de JAW          (más alto = más abierta)
  apertura_lab   y UL − y LL
  protrusion     x media de UL y LL
  tt_alt, tt_ade   punta   (y, x)
  tb_alt, tb_ade   lámina
  td_alt, td_ade   dorso

Uso: python datos_ema_usc.py --raiz .../USC-TIMIT/EMA/Data --salida DIR
"""
import argparse
import glob
import os
import re

import numpy as np
import scipy.io as sio

from datos_fonemas import leer_textgrid

CONTROLES = ['mandibula', 'apertura_lab', 'protrusion', 'tt_alt', 'tt_ade', 'tb_alt', 'tb_ade', 'td_alt', 'td_ade']


def senales(ruta):
    m = sio.loadmat(ruta, squeeze_me=True, struct_as_record=False)
    clave = [k for k in m if not k.startswith('__')][0]
    d = {e.NAME: e for e in np.atleast_1d(m[clave])}
    fs = float(d['UL'].SRATE)
    s = {k: np.asarray(d[k].SIGNAL, float) for k in ('UL', 'LL', 'JAW', 'TD', 'TB', 'TT')}
    y = np.stack([-s['JAW'][:, 1], s['UL'][:, 1] - s['LL'][:, 1], (s['UL'][:, 0] + s['LL'][:, 0]) / 2,
                  s['TT'][:, 1], s['TT'][:, 0], s['TB'][:, 1], s['TB'][:, 0], s['TD'][:, 1], s['TD'][:, 0]], 1)
    return np.arange(len(y)) / fs, y


def diezmar(t, y, n):
    """Media de cada `n` muestras (100 Hz → 50 Hz con n=2)."""
    m = len(y) // n * n
    return t[:m:n], np.nanmean(y[:m].reshape(-1, n, y.shape[1]), 1)


def rellenar(y):
    """Huecos de un sensor (NaN): interpolación lineal por columna."""
    for k in range(y.shape[1]):
        mk = np.isnan(y[:, k])
        if mk.any() and (~mk).sum() > 1:
            y[mk, k] = np.interp(np.flatnonzero(mk), np.flatnonzero(~mk), y[~mk, k])
    return y


def frases(trans):
    """[(nombre_frase, [(fonema, ini, fin)])] cortando por el número de frase."""
    por = {}
    for linea in open(trans, encoding='utf8', errors='replace'):
        c = linea.rstrip('\n').split(',')
        if len(c) < 6 or not c[5].strip():
            continue
        por.setdefault(c[5].strip(), []).append((c[2], float(c[0]), float(c[1])))
    return list(por.items())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raiz', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--aceptar_mri', action='store_true')
    ap.add_argument('--textgrid', help='carpeta de TextGrid de MFA para --textgrid_hablante')
    ap.add_argument('--textgrid_hablante', default='m3')
    ap.add_argument('--diezmo', type=int, default=2, help='100 Hz / diezmo')
    ap.add_argument('--margen', type=float, default=0.3, help='s de silencio a cada lado de la frase')
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    for hablante in sorted(os.listdir(a.raiz)):
        nombres, ts, ys, fons = [], [], [], []
        for mat in sorted(glob.glob(os.path.join(a.raiz, hablante, 'mat', '*.mat'))):
            base = os.path.splitext(os.path.basename(mat))[0]
            trans = os.path.join(a.raiz, hablante, 'trans', base + '.trans')
            tg = os.path.join(a.textgrid, base + '.TextGrid') if a.textgrid else ''
            if tg and os.path.exists(tg) and hablante.lower() == a.textgrid_hablante:
                # Alineado con MFA sobre el audio del propio .mat: el archivo
                # entero (5 frases) es una sola secuencia.
                t, y = diezmar(*senales(mat), a.diezmo)
                fon = [(re.sub(r'\d', '', f).lower() or 'sil', x0, x1) for f, x0, x1 in leer_textgrid(tg) if x1 > x0]
                if np.isnan(y).mean() > 0.1:
                    continue
                nombres.append(base); ts.append(t.astype(np.float32)); ys.append(rellenar(y)); fons.append(fon)
                continue
            if not os.path.exists(trans):
                # M3 trae las transcripciones con nombre `usctimit_mri_*`: se
                # aceptan solo si `--aceptar_mri` (ver comprobación en el informe).
                alt = os.path.join(a.raiz, hablante, 'trans', base.replace('_ema_', '_mri_') + '.trans')
                if not (a.aceptar_mri and os.path.exists(alt)):
                    continue
                trans = alt
            t, y = diezmar(*senales(mat), a.diezmo)
            for n, segs in frases(trans):
                i0, i1 = segs[0][1] - a.margen, segs[-1][2] + a.margen
                sel = (t >= i0) & (t < i1)
                yy = y[sel]
                if len(yy) < 20 or np.isnan(yy).mean() > 0.1:
                    continue
                yy = rellenar(yy)
                tt = t[sel] - i0
                fon = [('sil', 0.0, a.margen)] + [(f, x0 - i0, x1 - i0) for f, x0, x1 in segs] + \
                      [('sil', segs[-1][2] - i0, i1 - i0)]
                nombres.append(f'{base}_{n}'); ts.append(tt.astype(np.float32)); ys.append(yy); fons.append(fon)
        if not ys:
            continue
        todo = np.concatenate(ys)
        mu, sd = todo.mean(0), todo.std(0) + 1e-6
        # Arrays de objetos, como en datos_fonemas.py (solo los leen nuestros guiones).
        np.savez_compressed(os.path.join(a.salida, hablante.lower() + '.npz'),
                            nombres=np.array(nombres), t=np.array(ts, dtype=object),
                            y=np.array([((y - mu) / sd).astype(np.float32) for y in ys], dtype=object),
                            fon=np.array(fons, dtype=object), mu=mu, sd=sd,
                            controles=np.array(['ema:' + c for c in CONTROLES]))
        print(hablante, len(ys), 'frases,', len(todo), 'muestras', round(len(todo) * a.diezmo / 100 / 60, 1), 'min')


if __name__ == '__main__':
    main()
