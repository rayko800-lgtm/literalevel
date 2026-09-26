"""Lo que comparten los guiones de v3: dónde están los datos, cómo se emparejan y qué columnas hay.

- Etiquetas SMIRK (etiquetar_smirk.py): rasgos() apila expresión (50), mandíbula (3), párpados (2)
  y pose en grados (3) → [T, 58] en el orden de ENTRADAS_SMIRK.
- Medidas MediaPipe (medir_expresion.py): 52 blendshapes + pose (3) → [T, 55]; COLUMNAS_ARKIT.
- GRUPOS: qué columnas forman boca, sonrisa, ojos, cejas y cabeza (los mismos que la red de fusión).
- pares_*(): emparejan archivos por nombre (<nombre>.npz en cada carpeta, recursivo).
"""
import glob
import os

import numpy as np

GRUPOS = {
    'boca': ['jawOpen', 'mouthClose', 'mouthFunnel', 'mouthPucker', 'mouthPressLeft', 'mouthPressRight',
             'mouthRollLower', 'mouthRollUpper', 'mouthLowerDownLeft', 'mouthLowerDownRight',
             'mouthUpperUpLeft', 'mouthUpperUpRight', 'mouthStretchLeft', 'mouthStretchRight'],
    'sonrisa': ['mouthSmileLeft', 'mouthSmileRight', 'cheekSquintLeft', 'cheekSquintRight'],
    'ojos': ['eyeBlinkLeft', 'eyeBlinkRight', 'eyeSquintLeft', 'eyeSquintRight', 'eyeWideLeft', 'eyeWideRight'],
    'cejas': ['browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 'browDownLeft', 'browDownRight'],
    'cabeza': ['cabeza_guinada', 'cabeza_cabeceo', 'cabeza_alabeo'],
}
# lo que mueve la parte generativa (no verbal); la boca es lo de GRUPOS['boca']
NO_VERBAL = GRUPOS['sonrisa'] + GRUPOS['ojos'] + GRUPOS['cejas'] + GRUPOS['cabeza']
ENTRADAS_SMIRK = [f'exp{i:02d}' for i in range(50)] + ['mand_abrir', 'mand_lado', 'mand_giro', 'parpado_izq', 'parpado_der',
                                                        'pose_guinada', 'pose_cabeceo', 'pose_alabeo']


def mapa_archivos(d, ext='npz'):
    return {os.path.splitext(os.path.basename(f))[0]: f for f in glob.glob(os.path.join(d, '**', '*.' + ext), recursive=True)}


def rasgos(s):
    """[T, 58] float32 a partir de un npz de etiquetar_smirk.py (o de un dict con las mismas claves)."""
    return np.concatenate([s['expresion'], s['mandibula'], s['parpados'], s['pose']], 1).astype(np.float32)


def objetivo_mediapipe(m):
    """[T, 55]: 52 blendshapes + 3 ángulos, y sus nombres (COLUMNAS_ARKIT)."""
    y = np.concatenate([m['bs'].astype(np.float32), np.nan_to_num(m['pose'].astype(np.float32))], 1)
    return y, list(m['bs_nombres']) + GRUPOS['cabeza']


def pares_smirk(dir_smirk, dir_medidas):
    s, m = mapa_archivos(dir_smirk), mapa_archivos(dir_medidas)
    return [(n, s[n], m[n]) for n in sorted(m) if n in s]


def cargar_par(fs, fm, min_ok=0.5):
    """X [T,58], Y [T,55], ok (cara en los dos), columnas; None si el clip es malo."""
    s, m = np.load(fs), np.load(fm)
    k = min(len(s['t']), len(m['t']))
    ok = s['ok'][:k].astype(bool) & m['ok'][:k].astype(bool)
    if ok.mean() < min_ok or ok.sum() < 50:
        return None
    y, cols = objetivo_mediapipe(m)
    return rasgos(s)[:k], y[:k], ok, cols


def apilar(pares, min_ok=0.5):
    """Todos los fotogramas válidos de los pares: X, Y, id de clip por fotograma, columnas, nombres."""
    Xs, Ys, ids, cols, nombres = [], [], [], None, []
    for n, fs, fm in pares:
        r = cargar_par(fs, fm, min_ok)
        if r is None:
            continue
        x, y, ok, cols = r
        Xs.append(x[ok]); Ys.append(y[ok]); ids.append(np.full(ok.sum(), len(nombres))); nombres.append(n)
    return np.concatenate(Xs), np.concatenate(Ys), np.concatenate(ids), cols, nombres
