"""Prepara un hablante de GRID para Montreal Forced Aligner: por cada vídeo,
un .wav de 16 kHz (el audio del propio .mpg, sincronizado con el vídeo) y un
.lab con las palabras de la alineación oficial (sin `sil`/`sp`).

Uso: python corpus_mfa_grid.py --videos DIR_sN --align DIR_align_sN --salida DIR --ffmpeg RUTA
"""
import argparse
import glob
import os
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--videos', required=True)
    ap.add_argument('--align', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--ffmpeg', required=True)
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    n = 0
    for v in sorted(glob.glob(os.path.join(a.videos, '*.mpg'))):
        nombre = os.path.splitext(os.path.basename(v))[0]
        al = os.path.join(a.align, nombre + '.align')
        wav = os.path.join(a.salida, nombre + '.wav')
        if not os.path.exists(al):
            continue
        palabras = [l.split()[2] for l in open(al) if len(l.split()) == 3 and l.split()[2] not in ('sil', 'sp')]
        open(os.path.join(a.salida, nombre + '.lab'), 'w').write(' '.join(palabras) + '\n')
        if not os.path.exists(wav):
            subprocess.run([a.ffmpeg, '-v', 'error', '-y', '-i', v, '-ac', '1', '-ar', '16000', wav], check=True)
        n += 1
    print(a.salida, n, 'frases')


if __name__ == '__main__':
    main()
