"""Une las medidas por fotograma (`medir_video.py`) con los fonemas alineados
(MFA, TextGrid) y deja un solo archivo por hablante listo para entrenar.

Salida: <salida>/<hablante>.npz con, por frase:
  y      [T, K] controles normalizados (z por hablante)
  fon    lista de (fonema, inicio_s, fin_s)
y los nombres de los controles en `CONTROLES`.
"""
import argparse
import glob
import os
import re

import numpy as np

# Controles del piloto: medidas geométricas y blendshapes (media izq./der.).
CONTROLES = [
    ('geo', 'apertura_int'), ('geo', 'ancho'), ('geo', 'mandibula'),
    ('geo', 'protrusion'), ('geo', 'mejilla_y'),
    ('bs', 'jawOpen'), ('bs', 'mouthPucker'), ('bs', 'mouthFunnel'),
    ('bs', 'mouthRollLower'), ('bs', 'mouthPress'), ('bs', 'mouthClose'),
    ('bs', 'cheekSquint'),
]


def leer_textgrid(ruta, capa='phones'):
    """Intervalos (texto, xmin, xmax) de la capa `capa` de un TextGrid largo."""
    txt = open(ruta, encoding='utf8').read()
    bloques = re.split(r'item \[\d+\]:', txt)[1:]
    for b in bloques:
        if re.search(r'name = "%s"' % capa, b):
            return [(t, float(a), float(z)) for a, z, t in
                    re.findall(r'xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"', b)]
    return []


def controles(npz):
    d = np.load(npz)
    geo_n, bs_n = list(d['geo_nombres']), list(d['bs_nombres'])
    cols = []
    for fuente, nombre in CONTROLES:
        if fuente == 'geo':
            cols.append(d['geo'][:, geo_n.index(nombre)])
        else:
            idx = [i for i, n in enumerate(bs_n) if n == nombre or n in (nombre + 'Left', nombre + 'Right')]
            cols.append(d['bs'][:, idx].mean(axis=1) if idx else np.full(len(d['t']), np.nan))
    return d['t'], np.stack(cols, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--medidas', required=True, help='carpeta con <frase>.npz de un hablante')
    ap.add_argument('--alineacion', required=True, help='carpeta con <frase>.TextGrid del mismo hablante')
    ap.add_argument('--salida', required=True)
    ap.add_argument('--hablante', required=True)
    a = ap.parse_args()
    frases, ys = [], []
    for npz in sorted(glob.glob(os.path.join(a.medidas, '*.npz'))):
        nombre = os.path.splitext(os.path.basename(npz))[0]
        tg = os.path.join(a.alineacion, nombre + '.TextGrid')
        if not os.path.exists(tg):
            continue
        t, y = controles(npz)
        fon = [(f, i, z) for f, i, z in leer_textgrid(tg) if z > i]
        if not fon or np.isnan(y).mean() > 0.1:
            continue
        # Huecos sueltos sin cara: interpolación lineal por columna.
        for k in range(y.shape[1]):
            m = np.isnan(y[:, k])
            if m.any() and (~m).sum() > 1:
                y[m, k] = np.interp(t[m], t[~m], y[~m, k])
        frases.append((nombre, t, fon))
        ys.append(y)
    todo = np.concatenate(ys)
    mu, sd = np.nanmean(todo, 0), np.nanstd(todo, 0) + 1e-6
    os.makedirs(a.salida, exist_ok=True)
    # Listas de largo variable: arrays de objetos. Solo los lee `base_dominancia.py`
    # sobre archivos que genera este mismo guion (nunca datos de terceros).
    np.savez_compressed(
        os.path.join(a.salida, a.hablante + '.npz'),
        nombres=np.array([n for n, _, _ in frases]),
        t=np.array([t for _, t, _ in frases], dtype=object),
        y=np.array([(y - mu) / sd for y in ys], dtype=object),
        fon=np.array([f for _, _, f in frases], dtype=object),
        mu=mu, sd=sd, controles=np.array(['%s:%s' % c for c in CONTROLES]))
    print(a.hablante, len(frases), 'frases,', len(todo), 'fotogramas')


if __name__ == '__main__':
    main()
