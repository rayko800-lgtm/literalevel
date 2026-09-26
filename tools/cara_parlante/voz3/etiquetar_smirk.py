"""Etiquetas mejores para la cara: SMIRK (FLAME) por fotograma, en la misma rejilla `t` que el
.npz de medidas de MediaPipe (medir_expresion.py), para poder comparar y entrenar con ambas.

Por vídeo: ffmpeg decodifica a la frecuencia del .npz (25 fps) y a --ancho píxeles → MediaPipe
FaceLandmarker (modo vídeo, la cara más grande) da los 478 puntos → recorte cuadrado ×1,4 como
el demo de SMIRK, con el centro y el lado suavizados (media exponencial) para que el recorte no
tiemble → lotes de 224×224 al codificador SMIRK en la GPU → <salida>/<nombre>.npz con
  t [T], ok [T] (1 si hubo cara), expresion [T,50], mandibula [T,3], parpados [T,2],
  pose [T,3] grados (guiñada, cabeceo, alabeo), pose_ejeangulo [T,3], cam [T,3], forma [300] (media).
Reanudable (salta lo hecho; escribe a .tmp y renombra) y repartible: --parte 2/4 hace 1 de cada 4.
Progreso en el log: una línea por vídeo al empezar, cada 10 % y al acabar (fps reales).

Uso: python etiquetar_smirk.py --medidas DIR_NPZ --videos DIR_MP4 --salida DIR
        --checkpoint SMIRK_em1.pt --landmarker face_landmarker.task [--dispositivo cuda]
        [--ancho 640] [--lote 64] [--parte 1/1] [--max_seg 0] [--lista a.npz,b.npz]
Necesita: timm, mediapipe, opencv, imageio-ffmpeg. NO necesita el modelo FLAME del MPI.
"""
import argparse
import glob
import os
import subprocess
import sys
import time

import cv2
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smirk_codificador as S  # noqa: E402


def fps_de(t):
    d = np.diff(t)
    return float(1 / np.median(d)) if len(d) else 25.0


class Lector:
    """Fotogramas BGR con ffmpeg a `fps` y `ancho` fijos (como LectorFfmpeg de medir_expresion.py)."""

    def __init__(self, video, fps, ancho, ffmpeg):
        cap = cv2.VideoCapture(video)
        w, h = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or ancho, cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or ancho
        cap.release()
        self.w = int(min(ancho, w)) // 2 * 2
        self.h = int(round(h * self.w / w / 2)) * 2
        self.p = subprocess.Popen([ffmpeg, '-loglevel', 'error', '-i', video, '-vf', f'fps={fps},scale={self.w}:{self.h}',
                                   '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
        self.n = self.w * self.h * 3

    def __iter__(self):
        while True:
            b = self.p.stdout.read(self.n)
            if len(b) < self.n:
                break
            yield np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
        self.cerrar()

    def cerrar(self):
        if self.p.poll() is None:
            self.p.terminate()
        self.p.stdout.close(); self.p.wait()


def landmarker(ruta):
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
    opts = vision.FaceLandmarkerOptions(base_options=mp_python.BaseOptions(model_asset_path=ruta),
                                        running_mode=vision.RunningMode.VIDEO, num_faces=2,
                                        min_face_detection_confidence=0.3, min_tracking_confidence=0.3)
    return mp, vision.FaceLandmarker.create_from_options(opts)


def puntos(mp, lmk, img_bgr, ms):
    r = lmk.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)), ms)
    if not r.face_landmarks:
        return None
    h, w = img_bgr.shape[:2]
    caras = [np.array([[p.x * w, p.y * h] for p in c], np.float32) for c in r.face_landmarks]
    return max(caras, key=lambda c: np.ptp(c[:, 0]))


def etiquetar(video, t, red, mp, lmk, a, ffmpeg, nombre):
    fps = fps_de(t)
    T = len(t)
    exp, mand, parp, pose, cam = (np.zeros((T, n), np.float32) for n in (50, 3, 2, 3, 3))
    ok = np.zeros(T, np.uint8)
    formas = []
    lote, idx = [], []
    centro = lado = None
    dev = next(red.parameters()).device
    t0 = time.time(); ult = -1
    tope = int(a.max_seg * fps) if a.max_seg else T
    print(f'{nombre}: {T} fotogramas a {fps:.1f} fps', flush=True)

    def vaciar():
        if not lote:
            return
        x = torch.from_numpy(np.stack(lote)).to(dev).permute(0, 3, 1, 2).float() / 255
        with torch.no_grad(), torch.autocast(dev.type, enabled=dev.type == 'cuda'):
            o = red(x)
        ii = np.array(idx)
        exp[ii] = o['expresion'].float().cpu().numpy(); mand[ii] = o['mandibula'].float().cpu().numpy()
        parp[ii] = o['parpados'].float().cpu().numpy(); pose[ii] = o['pose'].float().cpu().numpy()
        cam[ii] = o['cam'].float().cpu().numpy(); formas.append(o['forma'].float().cpu().numpy().mean(0))
        ok[ii] = 1
        lote.clear(); idx.clear()

    lector = Lector(video, fps, a.ancho, ffmpeg)
    for k, img in enumerate(lector):
        if k >= min(T, tope):
            lector.cerrar()
            break
        pts = None if (a.cada > 1 and k % a.cada and centro is not None) else puntos(mp, lmk, img, int(k * 1000 / fps))
        if pts is not None:
            c, l = S.caja(pts)
            centro, lado = (c, l) if centro is None else (0.4 * centro + 0.6 * c, 0.4 * lado + 0.6 * l)
        elif centro is None or (a.cada <= 1):
            centro = None
            continue
        lote.append(S.recortar(img, centro, lado)); idx.append(k)
        if len(lote) >= a.lote:
            vaciar()
        dec = (10 * k) // max(1, min(T, tope))
        if dec != ult and k:
            ult = dec
            print(f'  {nombre} {k}/{T} ({10 * dec} %) {k / (time.time() - t0):.0f} fps', flush=True)
    vaciar()
    forma = np.mean(formas, 0) if formas else np.zeros(300, np.float32)
    print(f'  {nombre} listo: cara en {ok.mean():.0%} de los fotogramas, {T / (time.time() - t0):.0f} fps', flush=True)
    return dict(t=t, ok=ok, expresion=exp, mandibula=mand, parpados=parp, pose=S.grados(pose), pose_ejeangulo=pose,
                cam=cam, forma=forma.astype(np.float32))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--videos', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--landmarker', required=True, help='face_landmarker.task de MediaPipe')
    ap.add_argument('--dispositivo', default='cuda' if torch.cuda.is_available() else 'cpu')
    ap.add_argument('--ancho', type=int, default=640)
    ap.add_argument('--lote', type=int, default=64)
    ap.add_argument('--cada', type=int, default=1, help='MediaPipe cada N fotogramas (el recorte se mantiene entre medias)')
    ap.add_argument('--parte', default='1/1', help='i/n: este proceso hace los vídeos i-1 módulo n')
    ap.add_argument('--max_seg', type=float, default=0, help='solo los primeros segundos (pruebas)')
    ap.add_argument('--lista', default='', help='solo estos nombres (separados por coma)')
    a = ap.parse_args()
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg = 'ffmpeg'
    os.makedirs(a.salida, exist_ok=True)
    i_parte, n_parte = (int(x) for x in a.parte.split('/'))
    solo = set(a.lista.split(',')) if a.lista else None
    videos = {os.path.splitext(os.path.basename(v))[0]: v for ext in ('mp4', 'mkv', 'webm')
              for v in glob.glob(os.path.join(a.videos, '**', '*.' + ext), recursive=True)}
    red = S.cargar(a.checkpoint, a.dispositivo)
    todos = sorted(glob.glob(os.path.join(a.medidas, '**', '*.npz'), recursive=True))
    hechos = saltados = 0
    for j, npz in enumerate(todos):
        nombre = os.path.splitext(os.path.basename(npz))[0]
        if j % n_parte != i_parte - 1 or (solo and nombre not in solo):
            continue
        dest = os.path.join(a.salida, nombre + '.npz')
        if os.path.exists(dest):
            saltados += 1
            continue
        if nombre not in videos:
            print('sin vídeo', nombre, flush=True)
            continue
        t = np.load(npz)['t']
        print(f'[{j + 1}/{len(todos)}]', end=' ', flush=True)
        try:
            # MediaPipe en modo vídeo exige tiempos crecientes: un landmarker nuevo por vídeo
            mp, lmk = landmarker(a.landmarker)
            d = etiquetar(videos[nombre], t, red, mp, lmk, a, ffmpeg, nombre)
        except Exception as e:
            print('ERROR', nombre, repr(e), flush=True)
            continue
        np.savez_compressed(dest + '.tmp.npz', **d)
        os.replace(dest + '.tmp.npz', dest)
        hechos += 1
    print(f'listo: {hechos} etiquetados, {saltados} ya estaban', flush=True)


if __name__ == '__main__':
    main()
