"""Rasgos de voz v3: HuBERT-large (o WavLM-large) congelado, varias capas guardadas para que la
red aprenda una suma ponderada de capas (como en SUPERB), en la rejilla `t` del .npz de medidas.

Elección: por defecto facebook/hubert-large-ll60k (Apache-2.0; es el codificador de FaceDiffuser,
CodeTalker, DiffPoseTalk, Learn2Talk y SelfTalk, que lo prefieren a wav2vec2 para la sincronía
labial). microsoft/wavlm-large (--codificador wavlm-large) puntúa un poco mejor en fonemas en
SUPERB y es más robusto al ruido, pero su licencia (repositorio UniSpeech) no es Apache: vale
para este uso académico, no como opción por defecto. Los dos: 24 capas, 1024 dims, 50 Hz.

Disco: 28 h de audio × 24 capas a 50 Hz serían ~250 GB. Se guardan solo --capas (7 por defecto:
6,9,12,15,18,21,24), a 25 Hz (media de pares) y en float16 → ~1,3 GB/h, ~36 GB en total, que
caben en Drive (250 GB libres) y en la RAM del A100 High-RAM (o en un memmap, ver datos_v3.py).
<salida>/<nombre>.npz (sin comprimir: float16 no comprime y tarda) con `voz` [T, K, 1024] y `t`.

Trozos de 30 s con 1 s de solape (se descarta el borde) para que el transformer tenga contexto.
Reanudable y repartible (--parte i/n).

Uso: python extraer_v3.py --medidas DIR_NPZ --audio DIR (mp4/m4a/wav/flac) --salida DIR
        [--codificador hubert-large|wavlm-large] [--capas 6,9,12,15,18,21,24] [--dispositivo cuda]
"""
import argparse
import glob
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'voz2cara'))
from extraer import audio   # noqa: E402  (ffmpeg → float32 16 kHz mono)

MODELOS = {'hubert-large': 'facebook/hubert-large-ll60k', 'wavlm-large': 'microsoft/wavlm-large'}
CAPAS = '6,9,12,15,18,21,24'
SR = 16000


def cargar_codificador(nombre, dispositivo):
    from transformers import AutoModel
    red = AutoModel.from_pretrained(MODELOS.get(nombre, nombre)).to(dispositivo).eval()
    if dispositivo.startswith('cuda'):
        red = red.half()
    return red


def rasgos_50hz(red, x, capas, dispositivo, trozo=30.0, margen=1.0):
    """[T50, K, 1024] float16 de todo el audio x (float32 16 kHz), por trozos con solape."""
    n = len(x)
    L, Mg = int(trozo * SR), int(margen * SR)
    salidas = []
    ini = 0
    with torch.no_grad():
        while ini < n:
            a, b = max(0, ini - Mg), min(n, ini + L + Mg)
            seg = torch.from_numpy(x[a:b])[None].to(dispositivo)
            if dispositivo.startswith('cuda'):
                seg = seg.half()
            if seg.shape[1] < 800:
                break
            h = red(seg, output_hidden_states=True).hidden_states          # 25 tensores [1, T, 1024]
            hs = torch.stack([h[c][0] for c in capas], 1)                    # [T, K, 1024]
            # 50 Hz: 320 muestras por paso; se recorta el margen añadido
            i0 = (ini - a) // 320
            i1 = i0 + (min(n, ini + L) - ini) // 320
            salidas.append(hs[i0:i1].to(torch.float16).cpu())
            ini += L
    return torch.cat(salidas).numpy() if salidas else np.zeros((0, len(capas), 1024), np.float16)


def a_rejilla(f50, t):
    """50 Hz → 25 Hz (media de pares) → fila más cercana a cada instante de la rejilla t."""
    f25 = f50[: len(f50) // 2 * 2].reshape(-1, 2, *f50.shape[1:]).astype(np.float32).mean(1)
    g = np.arange(len(f25)) / 25.0
    idx = np.clip(np.searchsorted(g, t), 0, len(f25) - 1)
    return f25[idx].astype(np.float16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--audio', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--codificador', default='hubert-large')
    ap.add_argument('--capas', default=CAPAS)
    ap.add_argument('--dispositivo', default='cuda' if torch.cuda.is_available() else 'cpu')
    ap.add_argument('--parte', default='1/1')
    ap.add_argument('--max_seg', type=float, default=0, help='solo los primeros segundos (pruebas)')
    a = ap.parse_args()
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg = 'ffmpeg'
    capas = [int(c) for c in a.capas.split(',')]
    i_parte, n_parte = (int(x) for x in a.parte.split('/'))
    os.makedirs(a.salida, exist_ok=True)
    red = cargar_codificador(a.codificador, a.dispositivo)
    audios = {os.path.splitext(os.path.basename(v))[0]: v for ext in ('mp4', 'm4a', 'wav', 'flac', 'mp3')
              for v in glob.glob(os.path.join(a.audio, '**', '*.' + ext), recursive=True)}
    todos = sorted(glob.glob(os.path.join(a.medidas, '**', '*.npz'), recursive=True))
    hechos, t0 = 0, time.time()
    for j, npz in enumerate(todos):
        nombre = os.path.splitext(os.path.basename(npz))[0]
        dest = os.path.join(a.salida, nombre + '.npz')
        if j % n_parte != i_parte - 1 or os.path.exists(dest) or nombre not in audios:
            continue
        t = np.load(npz)['t']
        try:
            x = audio(audios[nombre], ffmpeg)
        except Exception as e:
            print('sin audio', nombre, e, flush=True)
            continue
        if a.max_seg:
            x = x[: int(a.max_seg * SR)]
        f50 = rasgos_50hz(red, x, capas, a.dispositivo)
        if len(f50) < 4:
            print('audio vacío', nombre, flush=True)
            continue
        np.savez(dest + '.tmp.npz', voz=a_rejilla(f50, t), t=t, capas=np.array(capas), codificador=a.codificador)
        os.replace(dest + '.tmp.npz', dest)
        hechos += 1
        if hechos % 10 == 0 or j + 1 == len(todos):
            print(f'[{j + 1}/{len(todos)}] {hechos} hechos, {len(t) / 25 / 3600:.2f} h este, {(time.time() - t0) / hechos:.0f} s/clip', flush=True)
    print('listo', hechos, flush=True)


if __name__ == '__main__':
    main()
