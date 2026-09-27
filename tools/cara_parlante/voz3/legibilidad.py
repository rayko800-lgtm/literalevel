"""¿Qué etiquetas «leen» mejor los labios: MediaPipe o SMIRK?

La fiabilidad SMIRK↔MediaPipe (fiabilidad.py) solo dice cuánto coinciden, no cuál acierta.
Aquí se mide cuánta información articulatoria lleva cada etiquetador: un clasificador lineal
intenta adivinar, a partir de la cara de cada fotograma (±2 fotogramas), qué clase de sonido
suena según la transcripción (Whisper + g2p, preparar_art.py):
  bilabial (p b m), labiodental (f v), redondeada (uw ow w uh), abierta (aa ae ah ao aw ay),
  estirada (iy ih ey), otra consonante.
Validación cruzada por clip (ningún hablante en los dos lados); rasgos normalizados por clip.
Más exactitud equilibrada = etiquetas que ven mejor la boca = mejor maestro para la red.

Uso: python legibilidad.py --smirk DIR --art DIR --medidas DIR [--salida informe.json]
"""
import argparse
import glob
import json
import os

import numpy as np

CLASES = {'bilabial': ['p', 'b', 'm'], 'labiodental': ['f', 'v'], 'redondeada': ['uw', 'ow', 'w', 'uh'],
          'abierta': ['aa', 'ae', 'ah', 'ao', 'aw', 'ay'], 'estirada': ['iy', 'ih', 'ey']}
BOCA = ['jaw', 'mouth', 'cheek']        # blendshapes de MediaPipe que miran la boca


def contexto(X, k=2):
    return np.concatenate([np.roll(X, s, 0) for s in range(-k, k + 1)], 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--smirk', required=True)
    ap.add_argument('--art', required=True)
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--modelo_art', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..',
                                                          'front', 'src', 'app', 'compartido', 'boca3d',
                                                          'modelo_articulatorio.json'))
    ap.add_argument('--salida', default='')
    a = ap.parse_args()
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score, recall_score
    fonemas = json.load(open(a.modelo_art))['fonemas']
    clase_de = {}
    for i, f in enumerate(fonemas):
        clase_de[i] = next((k for k, v in CLASES.items() if f in v), None if f == 'sil' else 'otra')
    nombres_c = list(CLASES) + ['otra']
    med = {os.path.splitext(os.path.basename(f))[0]: f for f in glob.glob(os.path.join(a.medidas, '**', '*.npz'), recursive=True)}
    datos = {'mediapipe': [], 'smirk': [], 'ambos': []}
    Y, G = [], []
    for g, fs in enumerate(sorted(glob.glob(os.path.join(a.smirk, '*.npz')))):
        n = os.path.splitext(os.path.basename(fs))[0]
        fa = os.path.join(a.art, n + '.npz')
        if n not in med or not os.path.exists(fa):
            continue
        s, m, ar = np.load(fs), np.load(med[n]), np.load(fa)
        k = min(len(s['t']), len(m['t']), len(ar['fon']))
        ok = s['ok'][:k].astype(bool) & m['ok'][:k].astype(bool)
        bn = list(m['bs_nombres'])
        mp = m['bs'][:k][:, [i for i, c in enumerate(bn) if c.startswith(tuple(BOCA))]]
        sm = np.concatenate([s['expresion'][:k], s['mandibula'][:k]], 1)
        y = np.array([clase_de.get(int(f)) if f >= 0 else None for f in ar['fon'][:k]], object)
        sel = ok & (y != None)  # noqa: E711
        if sel.sum() < 20:
            continue
        def z(X):
            X = X.astype(np.float32); mu, sd = X[ok].mean(0), X[ok].std(0) + 1e-6
            return contexto((X - mu) / sd)[sel]
        zm, zs = z(mp), z(sm)
        datos['mediapipe'].append(zm); datos['smirk'].append(zs); datos['ambos'].append(np.concatenate([zm, zs], 1))
        Y.append(np.array([nombres_c.index(c) for c in y[sel]])); G.append(np.full(sel.sum(), g))
    Y, G = np.concatenate(Y), np.concatenate(G)
    grupos = np.unique(G)
    print(f'{len(grupos)} clips, {len(Y)} fotogramas;', {c: int((Y == i).sum()) for i, c in enumerate(nombres_c)})
    informe = {'clips': int(len(grupos)), 'fotogramas': int(len(Y))}
    for nombre, Xs in datos.items():
        X = np.concatenate(Xs)
        P = np.zeros(len(Y), int)
        for pl in range(4):                                  # 4 pliegues por clip
            prueba = np.isin(G, grupos[pl::4])
            clf = LogisticRegression(max_iter=2000, C=0.1, class_weight='balanced')
            clf.fit(X[~prueba], Y[~prueba]); P[prueba] = clf.predict(X[prueba])
        ba = balanced_accuracy_score(Y, P)
        rec = recall_score(Y, P, average=None, labels=range(len(nombres_c)))
        informe[nombre] = {'exactitud_equilibrada': round(float(ba), 3),
                           'acierto_por_clase': {c: round(float(r), 3) for c, r in zip(nombres_c, rec)}}
        print(nombre, informe[nombre])
    print('azar:', round(1 / len(nombres_c), 3))
    if a.salida:
        json.dump(informe, open(a.salida, 'w'), indent=1)


if __name__ == '__main__':
    main()
