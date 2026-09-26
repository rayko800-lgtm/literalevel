"""Mapa lineal SMIRK (FLAME) → los 52 blendshapes ARKit de MediaPipe + 3 ángulos de cabeza.

Eos (MetaHuman) solo entiende los 52 morphs ARKit; SMIRK da expresión FLAME (50), mandíbula (3),
párpados (2) y pose (3). Opciones consideradas:
  a) invertir la matriz ARKit→FLAME de mediapipe-blendshapes-to-flame (PeizhiYan): está ajustada
     con caras sintéticas, 52→50 no es invertible sin regularizar y no cubre mandíbula ni párpados;
  b) pasar por la malla FLAME y medir los blendshapes con MediaPipe sobre un render: exige el
     modelo FLAME del MPI (registro) y renderizar millones de fotogramas;
  c) ridge SMIRK→MediaPipe ajustado con los pares reales (mismo fotograma etiquetado por los dos),
     millones de fotogramas de Obama y 1KH. Es lo que se hace aquí: sin registro, calibrado
     en las mismas unidades MediaPipe que ya usa generar.py (ganancias y escala_boca_1kh.json),
     y el ruido de MediaPipe se promedia en el ajuste (el mapa es de 58 parámetros a 55 salidas).
La limitación: el mapa hereda el sesgo medio de MediaPipe (no su temblor). Para la boca
pedagógica eso se corrige en generar.py con la garantía de Blender (p/b/m, u/o/w).

Uso:  python mapa_arkit.py --smirk DIR --medidas DIR --salida mapa_arkit.json [--alpha 10]
Deja el JSON con media/sd de entrada, W [58,55], b [55], columnas y r de validación cruzada (2 mitades).
Desde otros guiones: mapa = cargar(json); Y = aplicar(mapa, X)  (X [T,58] de rasgos()).
"""
import argparse
import json
import os
import sys
import zlib

import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datos_v3 as D  # noqa: E402


def ajustar(X, Y, alpha=10.0):
    """Ridge con X estandarizada. Devuelve el mapa como dict serializable."""
    mx, sx = X.mean(0), X.std(0) + 1e-6
    Z = (X - mx) / sx
    my = Y.mean(0)
    A = Z.T @ Z + alpha * np.eye(Z.shape[1])
    W = np.linalg.solve(A, Z.T @ (Y - my))                    # [58, 55]
    return {'media_x': mx.tolist(), 'sd_x': sx.tolist(), 'W': W.tolist(), 'b': my.tolist(), 'alpha': alpha}


def aplicar(mapa, X):
    Z = (np.asarray(X, np.float32) - np.array(mapa['media_x'], np.float32)) / np.array(mapa['sd_x'], np.float32)
    return Z @ np.array(mapa['W'], np.float32) + np.array(mapa['b'], np.float32)


def cargar(ruta):
    return json.load(open(ruta))


def correlaciones(P, Y, columnas, clip=None):
    """r por columna. Si `clip` (id por fotograma) se da, se quita la media de cada clip antes
    (es lo que ve el entrenamiento: diferencias sobre la media del clip)."""
    if clip is not None:
        P, Y = P.copy(), Y.copy()
        for c in np.unique(clip):
            s = clip == c
            P[s] -= P[s].mean(0); Y[s] -= Y[s].mean(0)
    r = {}
    for k, c in enumerate(columnas):
        r[c] = round(float(np.corrcoef(P[:, k], Y[:, k])[0, 1]), 3) if Y[:, k].std() > 1e-6 and P[:, k].std() > 1e-6 else None
    return r


def por_grupo(r):
    return {g: round(float(np.nanmean([r[c] for c in cs if r.get(c) is not None])), 3) if any(r.get(c) is not None for c in cs) else None
            for g, cs in D.GRUPOS.items()}


def mitad(nombre):
    """Reparto estable en dos mitades por vídeo (los trozos _00, _01 del mismo vídeo van juntos)."""
    return zlib.crc32(nombre.rsplit('_', 1)[0].encode()) % 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--smirk', required=True)
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--alpha', type=float, default=10.0)
    ap.add_argument('--max_clips', type=int, default=0)
    a = ap.parse_args()
    pares = D.pares_smirk(a.smirk, a.medidas)
    if a.max_clips:
        pares = pares[:a.max_clips]
    X, Y, clip, cols, nombres = D.apilar(pares)
    print(f'{len(nombres)} clips, {len(X)} fotogramas con cara en los dos etiquetadores', flush=True)
    m = np.array([mitad(n) for n in nombres])[clip]
    rs = []
    for h in (0, 1):
        tr, te = m != h, m == h
        if tr.sum() < 100 or te.sum() < 100:
            continue
        mp = ajustar(X[tr], Y[tr], a.alpha)
        rs.append(correlaciones(aplicar(mp, X[te]), Y[te], cols, clip[te]))
    r_cv = {c: (round(float(np.mean([r[c] for r in rs if r[c] is not None])), 3) if rs and any(r[c] is not None for r in rs) else None)
            for c in cols}
    mapa = ajustar(X, Y, a.alpha)
    mapa.update(columnas_entrada=D.ENTRADAS_SMIRK, columnas=cols, clips=len(nombres), fotogramas=int(len(X)),
                r_cv=r_cv, r_cv_grupos=por_grupo(r_cv))
    json.dump(mapa, open(a.salida, 'w'), indent=1)
    print('r validación cruzada por grupo (sin media del clip):', mapa['r_cv_grupos'], flush=True)


if __name__ == '__main__':
    main()
