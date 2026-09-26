"""Piloto de fiabilidad de las etiquetas: ¿cuánto coinciden SMIRK y MediaPipe sobre los mismos
fotogramas, blendshape a blendshape?

Con los clips que tienen las dos etiquetas se ajusta un mapa ridge FLAME→cada blendshape ARKit
(mapa_arkit.ajustar) en una mitad de los clips (reparto estable por vídeo) y se mide r en la
otra mitad; después al revés, y se promedian. Se informa r bruto y r sin la media de cada clip
(lo que ve el entrenamiento), por blendshape y por grupo (boca, sonrisa, ojos, cejas, cabeza).

Lectura: si dos estimadores independientes coinciden con r = ρ sobre la misma cara, un modelo
perfecto entrenado con uno de ellos no puede pasar de ≈ √ρ frente al otro; y una r alta en la
boca dice que SMIRK ve lo que MediaPipe ve, con menos ruido (SMIRK es 3D y se ajusta a la cara
entera). Un r bajo en una columna concreta señala un blendshape que uno de los dos mide mal.

Uso: python fiabilidad.py --smirk DIR --medidas DIR --salida informe_fiabilidad.json [--alpha 10]
Imprime la tabla y deja el JSON (r por columna en cada variante, grupos, clips y fotogramas).
"""
import argparse
import json
import os
import sys

import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # la consola de Windows es cp1252
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datos_v3 as D          # noqa: E402
import mapa_arkit as M        # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--smirk', required=True)
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--alpha', type=float, default=10.0)
    a = ap.parse_args()
    pares = D.pares_smirk(a.smirk, a.medidas)
    if len(pares) < 2:
        sys.exit(f'hacen falta al menos 2 clips con las dos etiquetas (hay {len(pares)})')
    X, Y, clip, cols, nombres = D.apilar(pares)
    mit = np.array([M.mitad(n) for n in nombres])
    if len(set(mit)) < 2:                       # pocos clips: reparto alterno para que haya dos mitades
        mit = np.arange(len(nombres)) % 2
    m = mit[clip]
    bruto, sin_media, n_test = [], [], []
    for h in (0, 1):
        tr, te = m != h, m == h
        mp = M.ajustar(X[tr], Y[tr], a.alpha)
        P = M.aplicar(mp, X[te])
        bruto.append(M.correlaciones(P, Y[te], cols))
        sin_media.append(M.correlaciones(P, Y[te], cols, clip[te]))
        n_test.append(int(te.sum()))

    def media(rs):
        return {c: (round(float(np.mean([r[c] for r in rs if r[c] is not None])), 3) if any(r[c] is not None for r in rs) else None)
                for c in cols}
    rb, rs = media(bruto), media(sin_media)
    gb, gs = M.por_grupo(rb), M.por_grupo(rs)
    print(f'{len(nombres)} clips, {len(X)} fotogramas; mitades de {n_test} fotogramas')
    print(f'{"columna":22s} {"r bruto":>8s} {"r sin media":>12s}')
    for c in cols:
        print(f'{c:22s} {str(rb[c]):>8s} {str(rs[c]):>12s}')
    print('por grupo (bruto):    ', gb)
    print('por grupo (sin media):', gs)
    print('techo orientativo del modelo (raiz de r sin media):', {g: (round(float(np.sqrt(max(v, 0))), 2) if v is not None else None) for g, v in gs.items()})
    json.dump({'clips': len(nombres), 'fotogramas': int(len(X)), 'nombres': nombres, 'alpha': a.alpha,
               'r_bruto': rb, 'r_sin_media': rs, 'grupos_bruto': gb, 'grupos_sin_media': gs},
              open(a.salida, 'w'), indent=1)


if __name__ == '__main__':
    main()
