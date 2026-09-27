"""La lengua de Eos: las poses de la boca didáctica (boca3d, poses.ejemplo.json, las mismas de
Blender en Pronunciar) por fonema, encadenadas con coarticulación suave.

Por cada fonema ARPAbet (con sus tiempos, los de generar.fonemas) se toma la pose del sonido IPA
y se sacan canales numéricos de la lengua:
  altura, adelante           cuerpo de la lengua (0..1, como en boca3d)
  velo, alto, raiz           dorso contra el velo (k g ŋ), dorso alto, raíz retraída
  alveolar, interdental,     dónde está la punta (pesos 0..1; la suma ≤ 1; «dental» cuenta como
  postalveolar, retrofleja   alveolar a medio camino hacia interdental)
Cada canal, en cada instante, es la media de los fonemas cercanos con pesos
  w = dominancia · exp(−|t − centro| / τ),  τ = 60 ms,
donde la dominancia es 1 si el sonido fija esa parte y 0,15 si la deja libre («libres» de la pose:
en /p/ la punta y el cuerpo van a donde vaya la vocal vecina). Antes, después y en las pausas
largas, la pose de reposo. El visor (index.html) convierte estos canales en giros de los huesos
FACIAL_C_Tongue1-4 de Eos (constantes del laboratorio lengua_lab.html).
"""
import json
import os

import numpy as np

POSES = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'front', 'src', 'app',
                                     'compartido', 'boca3d', 'poses.ejemplo.json'))
ARPA_IPA = {'aa': 'ɑ', 'ae': 'æ', 'ah': 'ʌ', 'ao': 'ɔ', 'aw': 'aʊ', 'ay': 'aɪ', 'b': 'b', 'ch': 'tʃ', 'd': 'd',
            'dh': 'ð', 'eh': 'ɛ', 'er': 'ɝ', 'ey': 'eɪ', 'f': 'f', 'g': 'ɡ', 'hh': 'h', 'ih': 'ɪ', 'iy': 'i',
            'jh': 'dʒ', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'ng': 'ŋ', 'ow': 'oʊ', 'oy': 'ɔɪ', 'p': 'p',
            'r': 'ɹ', 's': 's', 'sh': 'ʃ', 't': 't', 'th': 'θ', 'uh': 'ʊ', 'uw': 'u', 'v': 'v', 'w': 'w',
            'y': 'j', 'z': 'z', 'zh': 'ʒ'}
CANALES = ['altura', 'adelante', 'velo', 'alto', 'raiz', 'alveolar', 'interdental', 'postalveolar', 'retrofleja']
PARTE = {'altura': 'cuerpo', 'adelante': 'cuerpo', 'velo': 'cuerpo', 'alto': 'cuerpo', 'raiz': 'cuerpo',
         'alveolar': 'punta', 'interdental': 'punta', 'postalveolar': 'punta', 'retrofleja': 'punta'}
TAU = 0.06


def canales(pose):
    punta = pose.get('punta', 'reposo')
    return {'altura': pose['cuerpo'][0], 'adelante': pose['cuerpo'][1],
            'velo': 1.0 if pose.get('dorso_velo') else 0.0, 'alto': float(pose.get('dorso_alto', 0.0)),
            'raiz': float(pose.get('raiz', 0.0)),
            'alveolar': 1.0 if punta == 'alveolar' else (0.6 if punta == 'dental' else 0.0),
            'interdental': 1.0 if punta == 'interdental' else (0.4 if punta == 'dental' else 0.0),
            'postalveolar': 1.0 if punta == 'postalveolar' else 0.0,
            'retrofleja': 1.0 if punta == 'retrofleja' else 0.0}


def curvas_lengua(fons, n, fps, poses=POSES):
    """{canal: [n]} a `fps` para los fonemas (arpabet, t0, t1)."""
    P = json.load(open(poses, encoding='utf-8'))
    reposo = canales(P['reposo'])
    segs = []                                   # (centro, canales, libres)
    t_prev = None
    for f, a, b in fons:
        if t_prev is None or a - t_prev > 0.35:     # arranque o pausa larga: reposo en medio
            segs.append(((a - 0.3) if t_prev is None else (t_prev + a) / 2, reposo, set()))
        pose = P['sonidos'].get(ARPA_IPA.get(f, 'ʌ'), P['sonidos']['ʌ'])
        segs.append(((a + b) / 2, canales(pose), set(pose.get('libres', []))))
        t_prev = b
    segs.append(((t_prev or 0) + 0.3, reposo, set()))
    c = np.array([s[0] for s in segs])
    t = np.arange(n) / fps
    dist = np.exp(-np.abs(t[:, None] - c[None, :]) / TAU)          # [n, S]
    out = {}
    for k in CANALES:
        dom = np.array([0.15 if PARTE[k] in s[2] else 1.0 for s in segs])
        v = np.array([s[1][k] for s in segs])
        w = dist * dom[None, :]
        out[k] = (w @ v) / (w.sum(1) + 1e-9)
    return out
