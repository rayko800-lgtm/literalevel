"""Expresión y prosodia de cada fotograma de un clip de cara hablando.

Por cada vídeo escribe un .npz con
  t        segundos de cada fotograma
  bs       las 52 blendshapes ARKit de MediaPipe (nombres en `bs_nombres`)
  pose     giro de la cabeza en grados: guiñada, cabeceo, alabeo
  ok       1 si se encontró cara
  f0       tono en Hz (0 si no hay voz), llevado a los fotogramas
  db       energía RMS en dB, llevada a los fotogramas

Es la parte de `modelo_articulatorio/medir_video.py` que sirve para la vida
de la cara (parpadeo, cejas, cabeza), más la pose y la prosodia. Si hay
varias caras se queda con la más grande. Reanudable.

Uso:
  python medir_expresion.py --modelo face_landmarker.task --salida DIR clip1.mp4 [...]
"""
import argparse
import os
import subprocess
import tempfile

import cv2
import imageio_ffmpeg
import librosa
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision


def pose_de_matriz(m):
    """Ángulos (guiñada, cabeceo, alabeo) en grados de la matriz 4x4 de MediaPipe."""
    r = np.asarray(m)[:3, :3]
    cabeceo = np.degrees(np.arctan2(r[2, 1], r[2, 2]))
    guinada = np.degrees(np.arcsin(-np.clip(r[2, 0], -1, 1)))
    alabeo = np.degrees(np.arctan2(r[1, 0], r[0, 0]))
    return guinada, cabeceo, alabeo


def tiene_video(ruta):
    """Algunos tramos bajan solo con audio; cv2 se cuelga con ellos (visto el 25 sep)."""
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-i', ruta],
                       capture_output=True, text=True, errors='replace')
    return 'Video:' in r.stderr


def prosodia(video, t):
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, 'a.wav')
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-loglevel', 'error', '-y', '-i', video,
                        '-ac', '1', '-ar', '16000', wav], check=True)
        y, sr = librosa.load(wav, sr=16000)
    salto = 160  # 10 ms
    # pyin por trozos de 60 s: sobre un discurso de una hora entero pide decenas de GB
    # (matrices de probabilidad por fotograma × tono) y el sistema mata el proceso.
    trozo = 60 * sr
    f0s, vozs = [], []
    for ini in range(0, len(y), trozo):
        seg = y[ini:ini + trozo]
        if len(seg) < 2048:
            n = int(np.ceil(len(seg) / salto))
            f0s.append(np.full(n, np.nan)); vozs.append(np.zeros(n, bool))
            continue
        f, v, _ = librosa.pyin(seg, fmin=65, fmax=400, sr=sr, frame_length=1024, hop_length=salto)
        n = int(np.ceil(len(seg) / salto))          # fotogramas propios del trozo, sin el de cierre
        f0s.append(f[:n]); vozs.append(v[:n])
    f0, voz = np.concatenate(f0s), np.concatenate(vozs)
    f0 = np.where(voz, f0, 0.0)
    rms = librosa.feature.rms(y=y, frame_length=400, hop_length=salto)[0]
    db = 20 * np.log10(rms + 1e-5)
    ta = np.arange(len(f0)) * salto / sr
    tr = np.arange(len(db)) * salto / sr
    # f0 al fotograma: el valor más cercano (no interpolar entre voz y silencio)
    idx = np.clip(np.searchsorted(ta, t), 0, len(f0) - 1)
    return f0[idx], np.interp(t, tr, db)


class LectorFfmpeg:
    """Fotogramas ya reducidos a `ancho` px y a `fps_max`: ffmpeg decodifica y escala
    con varios hilos, y MediaPipe recibe imágenes pequeñas. Con vídeo HD es 2-3 veces
    más rápido que leer con cv2 a tamaño completo. Devuelve BGR, como cv2."""

    def __init__(self, video, ancho, fps_max=25):
        cap = cv2.VideoCapture(video)
        w, h = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        cap.release()
        self.w = int(min(ancho, w)) // 2 * 2
        self.h = int(round(h * self.w / w / 2)) * 2
        self.fps = min(fps, fps_max)
        self.p = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), '-loglevel', 'error', '-i', video,
                                   '-vf', f'fps={self.fps},scale={self.w}:{self.h}', '-f', 'rawvideo',
                                   '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
        self.n = self.w * self.h * 3

    def get(self, prop):
        return self.fps

    def read(self):
        b = self.p.stdout.read(self.n)
        if len(b) < self.n:
            return False, None
        return True, np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)

    def release(self):
        self.p.stdout.close()
        self.p.wait()


def medir(video, lmk, salida, ancho=0):
    cap = LectorFfmpeg(video, ancho) if ancho else cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    t, bs, pose, ok = [], [], [], []
    nombres = None
    i = 0
    while True:
        bien, img = cap.read()
        if not bien:
            break
        ts = int(i * 1000 / fps)
        r = lmk.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                          data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)), ts)
        t.append(i / fps)
        if r.face_blendshapes:
            # la cara más grande: la de mayor anchura de la malla
            k = int(np.argmax([np.ptp([p.x for p in c]) for c in r.face_landmarks]))
            cats = r.face_blendshapes[k]
            nombres = nombres or [c.category_name for c in cats]
            bs.append([c.score for c in cats])
            pose.append(pose_de_matriz(r.facial_transformation_matrixes[k]))
            ok.append(1)
        else:
            bs.append([0.0] * 52)
            pose.append((0.0, 0.0, 0.0))
            ok.append(0)
        i += 1
    cap.release()
    t = np.array(t)
    f0, db = prosodia(video, t)
    np.savez_compressed(salida, t=t, bs=np.array(bs, np.float32), pose=np.array(pose, np.float32),
                        ok=np.array(ok, np.uint8), f0=f0.astype(np.float32), db=db.astype(np.float32),
                        bs_nombres=np.array(nombres or []), fps=fps)
    return len(t), float(np.mean(ok)) if ok else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--ancho', type=int, default=0,
                    help='reducir el vídeo a este ancho (p. ej. 640) antes de medir; 0 = tamaño original')
    ap.add_argument('videos', nargs='+')
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    for v in a.videos:
        destino = os.path.join(a.salida, os.path.splitext(os.path.basename(v))[0] + '.npz')
        if os.path.exists(destino):
            continue
        if not tiene_video(v):
            print(f'{os.path.basename(v)}: sin imagen, se salta')
            continue
        opts = vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=a.modelo),
            running_mode=vision.RunningMode.VIDEO, num_faces=2,
            output_face_blendshapes=True, output_facial_transformation_matrixes=True)
        with vision.FaceLandmarker.create_from_options(opts) as lmk:
            n, frac = medir(v, lmk, destino, a.ancho)
        print(f'{os.path.basename(v)}: {n} fotogramas, cara en {frac:.0%}')


if __name__ == '__main__':
    main()
