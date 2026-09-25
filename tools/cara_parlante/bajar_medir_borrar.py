"""Baja un vídeo, lo mide y lo borra: solo quedan las medidas.

Para oradores cuyos vídeos tienen derechos de autor (p. ej. el canal de
Fernando Miralles): uso académico, visto bueno del profesor de Miguel. No
se guarda ni se reparte el vídeo; solo el .npz con blendshapes, pose y
prosodia (medir_expresion.py) y una línea de créditos.

Se baja a 360p: MediaPipe no necesita más y mide unas dos veces más rápido.

Uso:
  python bajar_medir_borrar.py --lista canal.tsv --salida DIR --modelo face_landmarker.task
                               [--min-s 180 --max-s 1500 --max 40]
  (canal.tsv: id<TAB>duración_s<TAB>título, de `yt-dlp --flat-playlist --print`)
"""
import argparse
import csv
import os
import subprocess
import sys
import tempfile

import imageio_ffmpeg

AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lista', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--modelo', required=True)
    ap.add_argument('--min-s', type=float, default=180)
    ap.add_argument('--max-s', type=float, default=1500)
    ap.add_argument('--max', type=int, default=0)
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)

    filas = []
    for linea in open(a.lista, encoding='utf8', errors='replace'):
        p = linea.rstrip('\n').split('\t')
        if len(p) >= 3 and p[1] not in ('NA', '') and a.min_s <= float(p[1]) <= a.max_s:
            filas.append(p)
    filas = filas[: a.max or None]
    cred_ruta = os.path.join(a.salida, 'creditos.csv')
    nuevo = not os.path.exists(cred_ruta)
    cred = csv.writer(open(cred_ruta, 'a', newline='', encoding='utf8'))
    if nuevo:
        cred.writerow(['id', 'duracion_s', 'titulo', 'url'])

    for vid, dur, tit in filas:
        npz = os.path.join(a.salida, vid + '.npz')
        if os.path.exists(npz):
            continue
        with tempfile.TemporaryDirectory(dir=os.path.dirname(a.salida)) as tmp:
            mp4 = os.path.join(tmp, vid + '.mp4')
            r = subprocess.run([sys.executable, '-m', 'yt_dlp', '--js-runtimes', 'node',
                                '--ffmpeg-location', imageio_ffmpeg.get_ffmpeg_exe(),
                                '-f', 'bv*[height<=360][ext=mp4]+ba[ext=m4a]/b[height<=360]',
                                '--merge-output-format', 'mp4', '-o', mp4,
                                f'https://www.youtube.com/watch?v={vid}'],
                               capture_output=True, text=True, encoding='utf8', errors='replace')
            if r.returncode != 0 or not os.path.exists(mp4):
                print(f'{vid}: no se pudo bajar ({r.stderr.strip().splitlines()[-1:]})', flush=True)
                continue
            subprocess.run([sys.executable, os.path.join(AQUI, 'medir_expresion.py'), '--modelo', a.modelo,
                            '--salida', a.salida, mp4], capture_output=True)
            # el vídeo se borra al salir del directorio temporal
        if os.path.exists(npz):
            cred.writerow([vid, dur, tit, f'https://www.youtube.com/watch?v={vid}'])
            print(f'{vid}: medido ({float(dur) / 60:.0f} min) y borrado', flush=True)
        else:
            print(f'{vid}: falló la medición', flush=True)


if __name__ == '__main__':
    main()
