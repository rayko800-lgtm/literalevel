"""Alineación sin conexión de las palabras de ejemplo que Miguel grabó al
final de cada audio de sonido (`app/audio_fonemas*/`, `palabras_audio.json`).

Dos pasos, un guion:
  preparar  → por cada audio y acento, corta el último tramo con sonido (el
              mismo `tramosSonoros` de `boca3d/audio.ts`, portado tal cual:
              RMS en ventanas de 20 ms sobre el 6 % del pico, huecos < 0,2 s
              unidos, tramos < 60 ms fuera) con 0,15 s de margen, y deja un
              .wav y un .lab con la palabra para MFA.
  recoger   → lee los TextGrid de MFA y escribe un JSON con los fonemas
              (ARPAbet) y sus tiempos en segundos desde el inicio del archivo
              original, que es lo que necesitaría `alCompasDeTramos`.

Uso:
  python alinear_palabras_grabadas.py preparar --raiz . --salida DIR --ffmpeg RUTA
  (mfa align DIR english_us_arpa english_us_arpa DIR_TG)
  python alinear_palabras_grabadas.py recoger --salida DIR --textgrid DIR_TG --json tiempos.json
"""
import argparse
import json
import os
import subprocess
import wave

import numpy as np

from datos_fonemas import leer_textgrid

CARPETA = {'ga': 'app/audio_fonemas', 'rp': 'app/audio_fonemas_rp'}
MARGEN = 0.15


def tramos_sonoros(x, fs):
    paso = max(1, round(fs * 0.02))
    rms = np.array([np.sqrt(np.mean(x[i:i + paso] ** 2)) for i in range(0, len(x), paso)])
    umbral = max(0.01, 0.06 * rms.max())
    tramos = []
    for j, r in enumerate(rms):
        if r < umbral:
            continue
        t0, t1 = j * paso / fs, min(len(x), (j + 1) * paso) / fs
        if tramos and t0 - tramos[-1][1] < 0.2:
            tramos[-1][1] = t1
        else:
            tramos.append([t0, t1])
    return [t for t in tramos if t[1] - t[0] >= 0.06]


def leer_audio(ruta, ffmpeg, fs=16000):
    crudo = subprocess.run([ffmpeg, '-v', 'error', '-i', ruta, '-ac', '1', '-ar', str(fs), '-f', 's16le', '-'],
                           check=True, capture_output=True).stdout
    return np.frombuffer(crudo, np.int16).astype(np.float32) / 32768, fs


def preparar(a):
    datos = json.load(open(os.path.join(a.raiz, 'front/src/app/compartido/boca3d/palabras_audio.json'), encoding='utf8'))
    os.makedirs(a.salida, exist_ok=True)
    cortes = {}
    for archivo, por_acento in datos.items():
        for acento, dato in por_acento.items():
            ruta = os.path.join(a.raiz, CARPETA[acento], archivo)
            if not dato or not dato.get('palabra') or not os.path.exists(ruta):
                continue
            x, fs = leer_audio(ruta, a.ffmpeg)
            tr = tramos_sonoros(x, fs)
            if not tr:
                continue
            i0 = max(0.0, tr[-1][0] - MARGEN)
            i1 = min(len(x) / fs, tr[-1][1] + MARGEN)
            nombre = f'{acento}_{os.path.splitext(archivo)[0]}'
            seg = (x[int(i0 * fs):int(i1 * fs)] * 32767).astype(np.int16)
            with wave.open(os.path.join(a.salida, nombre + '.wav'), 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(fs); w.writeframes(seg.tobytes())
            open(os.path.join(a.salida, nombre + '.lab'), 'w', encoding='utf8').write(dato['palabra'].lower() + '\n')
            cortes[nombre] = {'archivo': archivo, 'acento': acento, 'palabra': dato['palabra'], 'desde': round(i0, 3),
                              'tramos': len(tr)}
    json.dump(cortes, open(os.path.join(a.salida, 'cortes.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print(len(cortes), 'palabras preparadas')


def recoger(a):
    cortes = json.load(open(os.path.join(a.salida, 'cortes.json'), encoding='utf8'))
    res, faltan = {}, []
    for nombre, c in cortes.items():
        tg = os.path.join(a.textgrid, nombre + '.TextGrid')
        if not os.path.exists(tg):
            faltan.append(nombre)
            continue
        fon = [[f, round(c['desde'] + x0, 3), round(c['desde'] + x1, 3)]
               for f, x0, x1 in leer_textgrid(tg) if f and x1 > x0]
        res.setdefault(c['archivo'], {})[c['acento']] = {'palabra': c['palabra'], 'fonemas': fon}
    json.dump({'origen': 'MFA 3.4.2 english_us_arpa sobre el último tramo sonoro (alinear_palabras_grabadas.py)',
               'audios': res}, open(a.json, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print(sum(len(v) for v in res.values()), 'alineadas;', len(faltan), 'sin alinear:', ' '.join(faltan))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paso', choices=['preparar', 'recoger'])
    ap.add_argument('--raiz', default='.')
    ap.add_argument('--salida', required=True)
    ap.add_argument('--ffmpeg')
    ap.add_argument('--textgrid')
    ap.add_argument('--json')
    a = ap.parse_args()
    preparar(a) if a.paso == 'preparar' else recoger(a)


if __name__ == '__main__':
    main()
