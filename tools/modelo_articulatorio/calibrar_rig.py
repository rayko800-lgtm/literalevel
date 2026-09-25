"""Paso de las medidas humanas a los controles del rig.

El rig es media cabeza en corte sagital (azimut limitado a −34°): no hay
vista frontal que medir con MediaPipe, así que la calibración no puede ser
«renderizar y medir». Se calibra con las **poses de referencia comunes**: los
46 sonidos que Miguel ajustó a mano (`poses.ejemplo.json` + ajustes 3D)
contra la media medida de esos mismos fonemas en GRID. Por control, una recta
medida_z → valor del rig por mínimos cuadrados sobre los fonemas donde el
campo no es «libre». La escala la ponen las poses hechas a mano; la dinámica
y la coarticulación, el modelo.

Deja `calibracion.json` con, por control: pendiente, ordenada, r de Pearson
entre fonemas y la tabla de fonemas (media humana, valor del rig, residuo).

Uso: python calibrar_rig.py --conjuntos DIR --poses DIR_boca3d --salida calibracion.json
"""
import argparse
import glob
import json
import os
import re

import numpy as np

# IPA del rig (GA) → ARPAbet de MFA.
IPA_ARPA = {
    'p': 'p', 'b': 'b', 't': 't', 'd': 'd', 'k': 'k', 'ɡ': 'g', 'f': 'f', 'v': 'v', 'θ': 'th', 'ð': 'dh',
    's': 's', 'z': 'z', 'ʃ': 'sh', 'ʒ': 'zh', 'h': 'hh', 'tʃ': 'ch', 'dʒ': 'jh', 'm': 'm', 'n': 'n', 'ŋ': 'ng',
    'l': 'l', 'ɹ': 'r', 'w': 'w', 'j': 'y', 'i': 'iy', 'ɪ': 'ih', 'ɛ': 'eh', 'æ': 'ae', 'ɑ': 'aa', 'ɔ': 'ao',
    'ʊ': 'uh', 'u': 'uw', 'ʌ': 'ah', 'ə': 'ah', 'ɝ': 'er', 'eɪ': 'ey', 'aɪ': 'ay', 'ɔɪ': 'oy', 'oʊ': 'ow', 'aʊ': 'aw',
}
# Largo del labio por forma (`LABIOS` de escena.ts): 1,05 fruncido … 2,9 estirado.
LARGO = {'neutros': 2.3, 'cerrados': 2.2, 'redondeados': 1.5, 'muy_redondeados': 1.05, 'estirados': 2.9, 'labiodental': 2.3}


def cierre_labial(p):
    # `cierreLabial` × min(1, mandíbula / REFERENCIA_CIERRE) de escena.ts.
    if p['labios'] == 'cerrados':
        c = 1.0
    elif p['labios'] != 'neutros':
        c = 0.0
    else:
        c = min(1.0, max(0.0, (0.55 - p['mandibula']) / 0.3))
    return c * min(1.0, max(0.0, p['mandibula']) / 0.2)


# Control humano (nombre en el conjunto) → (control del rig, campo libre que lo invalida, función).
PARES = {
    'geo:mandibula': ('mandibula', 'mandibula', lambda p: p['mandibula']),
    'bs:jawOpen': ('mandibula', 'mandibula', lambda p: p['mandibula']),
    'geo:ancho': ('largo_labio', 'labios', lambda p: LARGO[p['labios']]),
    'bs:mouthPucker': ('largo_labio', 'labios', lambda p: LARGO[p['labios']]),
    'geo:apertura_int': ('cierre_labios', 'labios', cierre_labial),
    'bs:mouthClose': ('cierre_labios', 'labios', cierre_labial),
}


def poses_rig(carpeta):
    base = json.load(open(os.path.join(carpeta, 'poses.ejemplo.json'), encoding='utf8'))
    ajustes = json.load(open(os.path.join(carpeta, 'poses.ajustes3d.json'), encoding='utf8'))
    sonidos = dict(base['sonidos'])
    for s, extra in ajustes.get('sonidos', {}).items():
        if s in sonidos:
            sonidos[s] = {**sonidos[s], **extra}
    return sonidos


def medias_humanas(carpeta):
    suma, n, controles = {}, {}, None
    for ruta in sorted(glob.glob(os.path.join(carpeta, '*.npz'))):
        d = np.load(ruta, allow_pickle=True)   # archivos propios de datos_fonemas.py
        controles = [str(c) for c in d['controles']]
        for t, y, fon in zip(d['t'], d['y'], d['fon']):
            for f, a, b in fon:
                p = re.sub(r'\d', '', f).lower()
                sel = (t >= a) & (t < b)
                if sel.any():
                    suma[p] = suma.get(p, 0) + y[sel].sum(0); n[p] = n.get(p, 0) + sel.sum()
    return {p: suma[p] / n[p] for p in suma}, {p: int(n[p]) for p in n}, controles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--conjuntos', required=True)
    ap.add_argument('--poses', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--min_fotogramas', type=int, default=200)
    a = ap.parse_args()
    rig = poses_rig(a.poses)
    medias, cuenta, controles = medias_humanas(a.conjuntos)
    res = {}
    for ctl, (ctl_rig, campo, f) in PARES.items():
        k = controles.index(ctl)
        filas = []
        for ipa, arpa in IPA_ARPA.items():
            p = rig.get(ipa)
            if p is None or arpa not in medias or cuenta[arpa] < a.min_fotogramas or campo in (p.get('libres') or []):
                continue
            filas.append((ipa, arpa, float(medias[arpa][k]), float(f(p))))
        x = np.array([r[2] for r in filas]); y = np.array([r[3] for r in filas])
        m, c = np.polyfit(x, y, 1)
        r = float(np.corrcoef(x, y)[0, 1])
        res[ctl] = {'control_rig': ctl_rig, 'pendiente': round(float(m), 4), 'ordenada': round(float(c), 4),
                    'r_entre_fonemas': round(r, 3), 'n_fonemas': len(filas),
                    'fonemas': [{'ipa': i, 'arpa': ar, 'humano_z': round(h, 3), 'rig': round(v, 3),
                                 'residuo': round(v - (m * h + c), 3)} for i, ar, h, v in filas]}
        peores = sorted(res[ctl]['fonemas'], key=lambda q: -abs(q['residuo']))[:4]
        print(f"{ctl:18s} → {ctl_rig:14s} r={r:+.2f} n={len(filas):2d}  más lejos: " +
              ', '.join(f"/{q['ipa']}/ {q['residuo']:+.2f}" for q in peores))
    json.dump(res, open(a.salida, 'w', encoding='utf8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
