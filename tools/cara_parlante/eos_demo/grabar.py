"""Graba un vídeo de Eos hablando desde el visor (modo ?grabar=<clip>), fotograma a fotograma,
y le pone la voz con ffmpeg. Usa el Chrome instalado (Playwright, channel='chrome').

Uso: python grabar.py --clip hola [--url http://127.0.0.1:8765] [--fps 30] [--ancho 1080 --alto 1080]
Deja <demo>/<clip>/eos_<clip>.mp4.
"""
import argparse
import os
import shutil
import subprocess

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

DEMO = 'D:/literalevel_cara/eos_demo'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clip', required=True)
    ap.add_argument('--url', default='http://127.0.0.1:8765')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--ancho', type=int, default=1080)
    ap.add_argument('--alto', type=int, default=1080)
    ap.add_argument('--vista', default='', help='boca: de cerca (labios, dientes y lengua)')
    a = ap.parse_args()
    tmp = os.path.join(DEMO, a.clip, 'fotogramas')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    with sync_playwright() as p:
        nav = p.chromium.launch(channel='chrome', headless=True,
                                args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
        pag = nav.new_page(viewport={'width': a.ancho, 'height': a.alto})
        pag.goto(f'{a.url}/index.html?grabar={a.clip}' + (f'&vista={a.vista}' if a.vista else ''))
        pag.wait_for_function('window.listo === true', timeout=300000)
        dur = pag.evaluate('window.duracion')
        n = int(dur * a.fps)
        for i in range(n):
            pag.evaluate(f'window.pintar({i / a.fps})')
            pag.screenshot(path=os.path.join(tmp, f'{i:05d}.png'))
            if i % 60 == 0:
                print(f'{i}/{n}', flush=True)
        nav.close()
    salida = os.path.join(DEMO, a.clip, f'eos_{a.clip}' + (f'_{a.vista}' if a.vista else '') + '.mp4')
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-framerate', str(a.fps),
                    '-i', os.path.join(tmp, '%05d.png'), '-i', os.path.join(DEMO, a.clip, 'voz.mp3'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-shortest', salida], check=True)
    shutil.rmtree(tmp)
    print('listo', salida, os.path.getsize(salida))


if __name__ == '__main__':
    main()
