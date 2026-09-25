"""Baja los tramos de cara hablando de TalkingHead-1KH, con audio.

TalkingHead-1KH (NVIDIA, repo MIT) lista vídeos de YouTube publicados con
licencia CC BY 3.0 y, por vídeo, los tramos donde hay una cabeza hablando
(«tubes»: trozo de 1 min, fotograma inicial y final, caja de la cara). Su
guion original baja solo la imagen; aquí bajamos imagen y audio, porque la
expresión se aprende de la prosodia.

Por cada vídeo:
  1. lee los metadatos (sin bajar nada) y comprueba que la licencia de
     YouTube sigue siendo Creative Commons; si no, lo salta y lo anota;
  2. baja solo los tramos de las tubes (--download-sections), a 720p o menos;
  3. apunta título, canal, licencia y tramo en creditos.csv (atribución CC BY).

Reanudable: si el clip ya existe, se salta.

Uso:
  python bajar_1kh.py --tubes data_list/val_video_tubes.txt --salida D:/literalevel_cara/1kh/val [--max 3]
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time

import imageio_ffmpeg


def leer_tubes(ruta):
    """{video_id: [(ini_s_en_fotogramas_relativos, ...)]} agrupado por vídeo."""
    tubes = {}
    with open(ruta) as f:
        for linea in f:
            partes = [p.strip() for p in linea.split(',')]
            if len(partes) < 9:
                continue
            vid, trozo = partes[0].rsplit('_', 1)
            h, w, f0, f1, x0, y0, x1, y1 = map(int, partes[1:9])
            tubes.setdefault(vid, []).append(
                dict(trozo=int(trozo), h=h, w=w, f0=f0, f1=f1, caja=(x0, y0, x1, y1)))
    return tubes


def ytdlp(*args):
    cmd = [sys.executable, '-m', 'yt_dlp', '--js-runtimes', 'node',
           '--ffmpeg-location', imageio_ffmpeg.get_ffmpeg_exe(), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf8', errors='replace')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tubes', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--max', type=int, default=0, help='máximo de vídeos (piloto)')
    ap.add_argument('--desde', type=int, default=0, help='primer vídeo de la lista')
    ap.add_argument('--tubes-por-video', type=int, default=0,
                    help='máximo de tramos por vídeo (más hablantes, menos de cada uno)')
    ap.add_argument('--min-s', type=float, default=8.0,
                    help='tramos más cortos no se bajan (el cuaderno usa ventanas de 10 s)')
    a = ap.parse_args()

    os.makedirs(a.salida, exist_ok=True)
    tubes = leer_tubes(a.tubes)
    ids = list(tubes)[a.desde:][: a.max or None]
    ruta_cred = os.path.join(a.salida, 'creditos.csv')
    nuevo = not os.path.exists(ruta_cred)
    cred = open(ruta_cred, 'a', newline='', encoding='utf8')
    esc = csv.writer(cred)
    if nuevo:
        esc.writerow(['clip', 'video_id', 'titulo', 'canal', 'licencia', 'ini_s', 'fin_s', 'caja', 'url'])

    for vid in ids:
        time.sleep(2)  # no apretar a YouTube
        url = f'https://www.youtube.com/watch?v={vid}'
        r = ytdlp('--skip-download', '--dump-json', '--no-playlist', url)
        if r.returncode != 0:
            print(f'{vid}: sin metadatos ({r.stderr.strip().splitlines()[-1:]})')
            continue
        info = json.loads(r.stdout)
        lic = info.get('license') or ''
        if 'Creative Commons' not in lic:
            print(f'{vid}: licencia «{lic}», se salta')
            continue
        fps = info.get('fps') or 25
        tramos = []
        largos = [t for t in tubes[vid] if (t['f1'] - t['f0']) / fps >= a.min_s]
        for k, t in enumerate(largos[: a.tubes_por_video or None]):
            ini = t['trozo'] * 60 + t['f0'] / fps
            fin = t['trozo'] * 60 + t['f1'] / fps
            tramos.append((f'{vid}_{k:02d}', ini, fin, t))
        # Una sola llamada por vídeo con todos sus tramos: los metadatos se
        # piden una vez (era lo lento: ~20 s por llamada).
        faltan = [x for x in tramos if not os.path.exists(os.path.join(a.salida, x[0] + '.mp4'))]
        if faltan:
            secciones = []
            for _, ini, fin, _ in faltan:
                secciones += ['--download-sections', f'*{ini:.2f}-{fin:.2f}']
            r = ytdlp('-f', 'bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]',
                      '--merge-output-format', 'mp4', '--no-playlist', *secciones,
                      '--force-keyframes-at-cuts',
                      '-o', os.path.join(a.salida, '_tmp', f'{vid}_%(section_start)s.%(ext)s'), url)
            tmp = os.path.join(a.salida, '_tmp')
            for clip, ini, _, _ in faltan:
                cand = [f for f in os.listdir(tmp) if f.startswith(vid + '_') and f.endswith('.mp4')
                        and abs(float(f[len(vid) + 1:-4]) - ini) < 0.05] if os.path.isdir(tmp) else []
                if cand:
                    os.replace(os.path.join(tmp, cand[0]), os.path.join(a.salida, clip + '.mp4'))
            if r.returncode != 0:
                print(f'{vid}: yt-dlp avisó ({r.stderr.strip().splitlines()[-1:]})')
        for clip, ini, fin, t in tramos:
            if not os.path.exists(os.path.join(a.salida, clip + '.mp4')):
                print(f'{clip}: falló')
                continue
            esc.writerow([clip, vid, info.get('title'), info.get('channel'), lic,
                          f'{ini:.2f}', f'{fin:.2f}',
                          '{} {} {} {} @{}x{}'.format(*t['caja'], t['w'], t['h']), url])
            cred.flush()
            print(f'{clip}: {fin - ini:.1f} s')
    cred.close()


if __name__ == '__main__':
    main()
