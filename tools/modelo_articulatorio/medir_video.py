"""Medidas de labios, mandíbula y mejillas en cada fotograma de un vídeo.

Un paso, un archivo: por cada vídeo escribe un .npz con
  t        segundos de cada fotograma
  geo      medidas geométricas (ver GEO), en unidades de distancia interocular
  bs       las 52 blendshapes de MediaPipe (nombres en `bs_nombres`)
  ok       1 si se encontró cara en ese fotograma

Reanudable: si el .npz ya existe, se salta el vídeo.

Uso:
  python medir_video.py --modelo face_landmarker.task --salida DIR video1 [video2 ...]
  python medir_video.py --modelo ... --salida DIR --lista videos.txt
"""
import argparse
import os
import sys

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# Índices de la malla de 478 puntos de MediaPipe.
LABIO_SUP_EXT, LABIO_INF_EXT = 0, 17
LABIO_SUP_INT, LABIO_INF_INT = 13, 14
COMISURA_I, COMISURA_D = 61, 291
SUBNASAL, MENTON = 2, 152
OJO_EXT_I, OJO_EXT_D = 33, 263
POMULO_I, POMULO_D = 50, 280      # mejillas, bajo el ojo

GEO = [
    'apertura_int',   # hueco entre labios (interior)
    'apertura_ext',   # borde exterior de labio a labio
    'ancho',          # comisura a comisura
    'mandibula',      # subnasal a mentón
    'comisura_y',     # altura media de las comisuras respecto al centro del labio sup.
    'protrusion',     # z del centro de los labios respecto a las comisuras (negativo = hacia la cámara)
    'mejilla_y',      # altura media de los pómulos respecto a los ojos
]


def medir(lm):
    p = np.array([[q.x, q.y, q.z] for q in lm])
    io = np.linalg.norm(p[OJO_EXT_I, :2] - p[OJO_EXT_D, :2]) or 1.0
    d = lambda a, b: np.linalg.norm(p[a, :2] - p[b, :2]) / io
    com = (p[COMISURA_I] + p[COMISURA_D]) / 2
    ojos = (p[OJO_EXT_I] + p[OJO_EXT_D]) / 2
    centro_labios = (p[LABIO_SUP_EXT] + p[LABIO_INF_EXT]) / 2
    return [
        d(LABIO_SUP_INT, LABIO_INF_INT),
        d(LABIO_SUP_EXT, LABIO_INF_EXT),
        d(COMISURA_I, COMISURA_D),
        d(SUBNASAL, MENTON),
        (com[1] - p[LABIO_SUP_EXT, 1]) / io,
        (centro_labios[2] - com[2]) / io,
        ((p[POMULO_I, 1] + p[POMULO_D, 1]) / 2 - ojos[1]) / io,
    ]


def procesar(ruta, lmk, salida, reloj):
    """`reloj` es una lista [ms]: el modo VIDEO exige marcas crecientes entre vídeos."""
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    destino = os.path.join(salida, nombre + '.npz')
    if os.path.exists(destino):
        return 'ya'
    cap = cv2.VideoCapture(ruta)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    ts, geo, bs, ok = [], [], [], []
    nombres = None
    i = 0
    while True:
        bien, im = cap.read()
        if not bien:
            break
        t_ms = reloj[0] + int(round(i * 1000 / fps))
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        r = lmk.detect_for_video(img, t_ms)
        ts.append(i / fps)
        if r.face_landmarks:
            geo.append(medir(r.face_landmarks[0]))
            cats = r.face_blendshapes[0]
            if nombres is None:
                nombres = [c.category_name for c in cats]
            bs.append([c.score for c in cats])
            ok.append(1)
        else:
            geo.append([np.nan] * len(GEO))
            bs.append([np.nan] * 52)
            ok.append(0)
        i += 1
    cap.release()
    reloj[0] += int(round(i * 1000 / fps)) + 1000
    if not ts:
        return 'vacío'
    tmp = destino + '.tmp.npz'
    np.savez_compressed(tmp, t=np.array(ts), geo=np.array(geo, dtype=np.float32),
                        bs=np.array(bs, dtype=np.float32), ok=np.array(ok, dtype=np.int8),
                        geo_nombres=np.array(GEO), bs_nombres=np.array(nombres or []), fps=fps)
    os.replace(tmp, destino)
    return f'{len(ts)} fot, cara en {sum(ok)}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--lista')
    ap.add_argument('videos', nargs='*')
    a = ap.parse_args()
    videos = list(a.videos)
    if a.lista:
        videos += [l.strip() for l in open(a.lista, encoding='utf8') if l.strip()]
    os.makedirs(a.salida, exist_ok=True)
    opts = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=a.modelo),
        running_mode=vision.RunningMode.VIDEO, num_faces=1,
        output_face_blendshapes=True)
    reloj = [0]
    with vision.FaceLandmarker.create_from_options(opts) as lmk:
        for k, v in enumerate(videos):
            print(f'[{k + 1}/{len(videos)}] {os.path.basename(v)}: {procesar(v, lmk, a.salida, reloj)}', flush=True)


if __name__ == '__main__':
    sys.exit(main())
