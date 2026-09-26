"""Inferencia v3 para Eos: audio + palabras con tiempo → boca (regresión) y no verbal (muestra
generativa con semilla), en la misma forma que la red de fusión (generar.py --gestos fusion).

prediccion_v3(mp3, palabras, dur, dir_modelo, semilla) → (t [T] a 25 fps, P [T, columnas], columnas)
  P está en unidades MediaPipe (diferencia sobre la media del clip), como la red de fusión, para
  que generar.py le aplique las mismas ganancias, la escala de reposo y la garantía pedagógica.

dir_modelo contiene boca/ y noverbal/ (cada una con modelo.pt y normalizacion.json de sus
entrenamientos). La voz se codifica con el mismo HuBERT/WavLM y las mismas capas que en el
entrenamiento (normalizacion.json lo dice). El estilo del no verbal se elige con la semilla
entre los estilos reales guardados (o el medio con --estilo medio en generar.py).
"""
import json
import os
import sys

import numpy as np
import torch

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', 'voz2cara'))
import datos_v3 as D                     # noqa: E402
import red_v3 as R                       # noqa: E402
from articulacion import entrada         # noqa: E402
from extraer import audio                # noqa: E402
from extraer_v3 import a_rejilla, cargar_codificador, rasgos_50hz   # noqa: E402

FPS = 25


def _cargar(dir_modelo, parte):
    norm = json.load(open(os.path.join(dir_modelo, parte, 'normalizacion.json')))
    K, C = len(norm['capas']), len(norm['columnas'])
    if parte == 'boca':
        red = R.Boca(K, C, norm['d'], norm['capas_transformer'])
    else:
        red = R.NoVerbal(K, C, norm['d'], norm['capas_transformer'], n_estilo=C)
    red.load_state_dict(torch.load(os.path.join(dir_modelo, parte, 'modelo.pt'), map_location='cpu', weights_only=True))
    return red.eval(), norm


def prediccion_v3(mp3, palabras, dur, dir_modelo, semilla=7, estilo='real', dispositivo='cpu'):
    import imageio_ffmpeg
    boca, nb = _cargar(dir_modelo, 'boca')
    nover, nn_ = _cargar(dir_modelo, 'noverbal')
    if nb['codificador'] != nn_['codificador'] or nb['capas'] != nn_['capas']:
        raise RuntimeError('boca y noverbal se entrenaron con distinta voz (codificador o capas)')
    x = audio(mp3, imageio_ffmpeg.get_ffmpeg_exe())
    tt = np.arange(0, dur, 1 / FPS)
    art, fon = entrada(palabras, tt)
    fon = fon.astype(np.int64); fon[fon < 0] = D.N_FON - 1
    cod = cargar_codificador(nb['codificador'], dispositivo)
    voz = a_rejilla(rasgos_50hz(cod, x, nb['capas'], dispositivo), tt).astype(np.float32)   # [T, K, 1024]
    tv = torch.from_numpy(voz)[None]; ta = torch.from_numpy(art)[None]; tf = torch.from_numpy(fon)[None]
    with torch.no_grad():
        pb = boca(tv, ta, tf)[0].numpy() * np.array(nb['sd'])
        g = torch.Generator().manual_seed(semilla)
        if estilo == 'medio' or not nn_.get('estilos'):
            est = np.array(nn_['estilo_medio'], np.float32)
        else:
            est = np.array(nn_['estilos'][semilla % len(nn_['estilos'])], np.float32)
        pn = nover.muestrear(tv, ta, tf, torch.from_numpy(est)[None], nn_['pasos'], nn_['guia'], g)[0].numpy() * np.array(nn_['sd'])
    return tt, np.concatenate([pb, pn], 1).astype(np.float32), nb['columnas'] + nn_['columnas']
