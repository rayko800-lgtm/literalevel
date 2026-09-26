"""Rasgos de voz para el modelo voz→cara: wav2vec2-base (preentrenado, Apache-2.0) sobre el
audio de cada vídeo medido, en la misma rejilla de 25 fps que su .npz de medidas.

Por vídeo: audio a 16 kHz mono (ffmpeg) → wav2vec2-base → media de las capas ocultas 6-9
(las que mejor codifican fonemas y prosodia) → 50 Hz a 25 Hz promediando pares → float16.
Guarda <salida>/<nombre>.npz con `voz` [T, 768] y `t` [T]. Reanudable; trozos de 20 s para
no agotar la memoria con vídeos largos (discursos de Obama).

Uso:  python extraer.py --medidas DIR_NPZ --videos DIR_MP4 --salida DIR [--dispositivo cuda]
Empareja <nombre>.npz con <nombre>.mp4 (busca recursivamente en --videos).
"""
import argparse
import glob
import os
import subprocess

import numpy as np
import torch


def audio(mp4, ffmpeg):
    r = subprocess.run([ffmpeg, '-loglevel', 'error', '-i', mp4, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--videos', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--dispositivo', default='cuda' if torch.cuda.is_available() else 'cpu')
    a = ap.parse_args()
    from transformers import Wav2Vec2Model
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg = 'ffmpeg'
    os.makedirs(a.salida, exist_ok=True)
    red = Wav2Vec2Model.from_pretrained('facebook/wav2vec2-base').to(a.dispositivo).eval()
    videos = {os.path.splitext(os.path.basename(v))[0]: v
              for v in glob.glob(os.path.join(a.videos, '**', '*.mp4'), recursive=True)}
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
        trozos = []
        with torch.no_grad():
            for i in range(0, len(x), 16000 * 20):
                seg = torch.tensor(x[i:i + 16000 * 20])[None].to(a.dispositivo)
                if seg.shape[1] < 400:
                    break
                h = red(seg, output_hidden_states=True).hidden_states
                trozos.append(torch.stack(h[6:10]).mean(0)[0].cpu().numpy())    # [T50, 768]
        f50 = np.concatenate(trozos)
        f25 = f50[: len(f50) // 2 * 2].reshape(-1, 2, 768).mean(1)                # 25 Hz
        g = np.arange(len(f25)) / 25.0
        idx = np.clip(np.searchsorted(g, t), 0, len(f25) - 1)                     # a la rejilla del .npz
        np.savez_compressed(dest, voz=f25[idx].astype(np.float16), t=t)
        hechos += 1
        if hechos % 20 == 0:
            print(hechos, nombre, flush=True)
    print('listo', hechos)


if __name__ == '__main__':
    main()
