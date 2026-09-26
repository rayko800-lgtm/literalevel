"""El modelo articulatorio de Blender (boca3d) como entrada de la red de fusión.

Es el mismo cálculo que mueve la boca didáctica de Pronunciar: fonemas ARPAbet (g2p_en)
repartidos dentro de cada palabra y la fórmula de dominancia de Cohen-Massaro entrenada con
GRID (modelo_articulatorio.json). Da, por fotograma, los 12 controles del modelo (en z) y el
fonema que suena. generar.py (Eos) y preparar_art.py (datos de entrenamiento) lo comparten,
para que la red vea en el entrenamiento exactamente lo mismo que verá al hablar Eos.
"""
import json
import os
import re

import numpy as np

MODELO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'front', 'src', 'app',
                                      'compartido', 'boca3d', 'modelo_articulatorio.json'))
_g2p = None


def fonemas(palabras):
    """(fonema ARPAbet sin acento, t0, t1) repartidos dentro de cada palabra; las vocales pesan el doble."""
    global _g2p
    if _g2p is None:
        from g2p_en import G2p
        _g2p = G2p()
    out = []
    for texto, t0, t1 in palabras:
        fs = [re.sub(r'\d', '', p).lower() for p in _g2p(texto) if re.match(r'[A-Z]', p)]
        if not fs:
            continue
        peso = np.array([2.0 if f[0] in 'aeiou' else 1.0 for f in fs])
        bordes = t0 + (t1 - t0) * np.concatenate([[0], np.cumsum(peso) / peso.sum()])
        out += [(f, bordes[i], bordes[i + 1]) for i, f in enumerate(fs)]
    return out


def boca(fons, t, modelo=MODELO):
    """Controles del modelo (z) en los instantes t (s) con la fórmula de dominancia."""
    M = json.load(open(modelo))
    idx = {f: i for i, f in enumerate(M['fonemas'])}
    T, la = np.array(M['T']), np.array(M['log_alfa'])
    ta, tr = np.array(M['log_theta_ant']), np.array(M['log_theta_arr'])
    segs = [(idx['sil'], fons[0][1] - 0.25)] + [(idx.get(f, idx['ah']), (a + b) / 2) for f, a, b in fons] \
        + [(idx['sil'], fons[-1][2] + 0.25)]
    ids = np.array([s[0] for s in segs]); cs = np.array([s[1] for s in segs])
    y = np.zeros((len(t), T.shape[1]))
    orden = np.argsort(cs); ids, cs = ids[orden], cs[orden]
    for i0 in range(0, len(t), 500):                   # por bloques; solo pesan los segmentos cercanos
        tb = t[i0:i0 + 500]
        a, b = np.searchsorted(cs, tb[0] - 3.0), np.searchsorted(cs, tb[-1] + 3.0)
        a, b = max(0, a - 1), min(len(cs), b + 1)
        ib, cb = ids[a:b], cs[a:b]
        dt = cb[None, :] - tb[:, None]
        for k in range(T.shape[1]):
            theta = np.where(dt > 0, np.exp(ta[ib, k]), np.exp(tr[ib, k]))
            logd = la[ib, k] - theta * np.abs(dt)
            logd -= logd.max(1, keepdims=True)
            d = np.exp(logd); d /= d.sum(1, keepdims=True)
            y[i0:i0 + 500, k] = d @ T[ib, k]
    return {c: y[:, i] for i, c in enumerate(M['controles'])}


def entrada(palabras, t, modelo=MODELO):
    """Entrada articulatoria de la red en los instantes t: [len(t), 12 controles + 1 habla]
    y el índice del fonema que suena (-1 en silencio). «habla» es 1 dentro de las palabras."""
    M = json.load(open(modelo))
    idx = {f: i for i, f in enumerate(M['fonemas'])}
    fons = fonemas(palabras)
    art = np.zeros((len(t), len(M['controles']) + 1), np.float32)
    fon = np.full(len(t), -1, np.int16)
    if not fons:
        return art, fon
    b = boca(fons, t, modelo)
    art[:, :-1] = np.stack([b[c] for c in M['controles']], 1)
    for f, a, z in fons:
        i, j = np.searchsorted(t, a), np.searchsorted(t, z)
        fon[i:j] = idx.get(f, idx['ah'])
    for _, a, z in palabras:
        art[np.searchsorted(t, a):np.searchsorted(t, z), -1] = 1
    return art, fon
