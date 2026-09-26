"""Entrada articulatoria de los vídeos de entrenamiento: qué dicen y cuándo (Whisper con
marcas de palabra), y lo que haría con eso el modelo articulatorio de Blender, fotograma a
fotograma en la rejilla de su .npz de medidas.

Por vídeo: audio 16 kHz → faster-whisper (palabras con tiempo) → articulacion.entrada()
→ <salida>/<nombre>.npz con `art` [T, 13] float16, `fon` [T] int16 y `t`; y las palabras en
<salida>/<nombre>.json. Reanudable.

Uso: python preparar_art.py --medidas DIR_NPZ --videos DIR (mp4, m4a, wav o flac) --salida DIR
         [--whisper large-v3] [--dispositivo cuda] [--modelo_art ruta/modelo_articulatorio.json]
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from articulacion import MODELO, entrada   # noqa: E402
from extraer import audio                  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--videos', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--whisper', default='large-v3')
    ap.add_argument('--dispositivo', default='cuda')
    ap.add_argument('--modelo_art', default=MODELO)
    a = ap.parse_args()
    from faster_whisper import BatchedInferencePipeline, WhisperModel
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg = 'ffmpeg'
    os.makedirs(a.salida, exist_ok=True)
    tipo = 'float16' if a.dispositivo == 'cuda' else 'int8'
    asr = BatchedInferencePipeline(WhisperModel(a.whisper, device=a.dispositivo, compute_type=tipo))
    videos = {os.path.splitext(os.path.basename(v))[0]: v for ext in ('mp4', 'm4a', 'wav', 'flac')
              for v in glob.glob(os.path.join(a.videos, '**', '*.' + ext), recursive=True)}
    hechos = 0
    for npz in sorted(glob.glob(os.path.join(a.medidas, '**', '*.npz'), recursive=True)):
        nombre = os.path.splitext(os.path.basename(npz))[0]
        dest = os.path.join(a.salida, nombre + '.npz')
        if os.path.exists(dest) or nombre not in videos:
            continue
        t = np.load(npz)['t']
        try:
            x = audio(videos[nombre], ffmpeg)
        except Exception as e:
            print('sin audio', nombre, e)
            continue
        segs, _ = asr.transcribe(x, language='en', word_timestamps=True, batch_size=16)
        palabras = [(w.word.strip(), float(w.start), float(w.end)) for s in segs for w in (s.words or [])
                    if w.word.strip()]
        art, fon = entrada(palabras, t, a.modelo_art)
        np.savez_compressed(dest, art=art.astype(np.float16), fon=fon, t=t)
        json.dump(palabras, open(os.path.join(a.salida, nombre + '.json'), 'w'))
        hechos += 1
        if hechos % 20 == 0:
            print(hechos, nombre, len(palabras), 'palabras', flush=True)
    print('listo', hechos)


if __name__ == '__main__':
    main()
