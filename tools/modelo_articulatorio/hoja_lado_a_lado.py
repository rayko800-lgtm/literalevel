"""Hoja de vídeo lado a lado para que Miguel juzgue a ojo: a la izquierda la
cara real (hablante de prueba, nunca visto en el entrenamiento); a la derecha
tres controles en el tiempo —real, dominancia, TCN y el calendario de reglas—
con un cursor que avanza con el vídeo y los fonemas debajo.

Un paso, un archivo: escribe un .mp4 con N frases seguidas.

Uso: python hoja_lado_a_lado.py --conjunto s33.npz --videos DIR_s33 --modelos DIR
       --prueba s33 --frases 8 --salida hoja_s33.mp4 [--lento 2]
"""
import argparse
import os

import cv2
import numpy as np
import torch

from base_dominancia import Dominancia, cargar, reglas, tensores
from pruebas_duras import medias_de
from tcn import TCN, cargar_con_acento, entrada

MOSTRAR = [('geo:apertura_int', 'apertura'), ('geo:ancho', 'ancho'), ('geo:mandibula', 'mandibula')]
COLOR = {'real': (255, 255, 255), 'dominancia': (90, 220, 90), 'tcn': (40, 160, 255), 'reglas': (80, 80, 255)}


def panel(series, t, cursor, segs, w=640, h=480):
    img = np.full((h, w, 3), 24, np.uint8)
    alto = (h - 60) // len(MOSTRAR)
    x = lambda s: int(40 + (w - 60) * s / max(t[-1], 1e-3))
    for i, (_, nombre) in enumerate(MOSTRAR):
        y0 = 10 + i * alto
        cv2.putText(img, nombre, (44, y0 + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        vals = np.concatenate([s[:, i] for s in series.values()])
        lo, hi = np.percentile(vals, 1), np.percentile(vals, 99)
        yy = lambda v: int(y0 + alto - 8 - (alto - 16) * (v - lo) / max(hi - lo, 1e-3))
        for m, s in series.items():
            pts = np.array([[x(tt), yy(v)] for tt, v in zip(t, s[:, i])], np.int32)
            cv2.polylines(img, [pts], False, COLOR[m], 2 if m == 'real' else 1, cv2.LINE_AA)
    for p, a, b in segs:
        if p != 'sil':
            cv2.putText(img, p, (x((a + b) / 2) - 8, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 120), 1, cv2.LINE_AA)
            cv2.line(img, (x(a), h - 50), (x(a), h - 22), (90, 90, 90), 1)
    cv2.line(img, (x(cursor), 0), (x(cursor), h - 50), (0, 220, 255), 1)
    for j, (m, c) in enumerate(COLOR.items()):
        cv2.putText(img, m, (44 + j * 140, h - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 1, cv2.LINE_AA)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--conjunto', required=True)
    ap.add_argument('--otros', nargs='+', required=True, help='conjuntos de entrenamiento (para las medias de las reglas)')
    ap.add_argument('--videos', required=True)
    ap.add_argument('--dominancia', required=True)
    ap.add_argument('--tcn', required=True)
    ap.add_argument('--frases', type=int, default=8)
    ap.add_argument('--lento', type=int, default=2, help='cada fotograma se repite n veces')
    ap.add_argument('--salida', required=True)
    a = ap.parse_args()
    frases, controles = cargar(a.conjunto)
    frases_ac = cargar_con_acento(a.conjunto)
    nombres = list(np.load(a.conjunto, allow_pickle=True)['nombres'])   # archivo propio
    k = [controles.index(c) for c, _ in MOSTRAR]
    dom = torch.load(a.dominancia, weights_only=True)
    idx = {p: i for i, p in enumerate(dom['fonemas'])}
    md = Dominancia(len(idx), len(controles)); md.load_state_dict(dom['estado']); md.eval()
    tc = torch.load(a.tcn, weights_only=True)
    idx_t = {p: i for i, p in enumerate(tc['fonemas'])}
    mt = TCN(len(idx_t), len(controles)); mt.load_state_dict(tc['estado']); mt.eval()
    medias = medias_de([f for r in a.otros for f in cargar(r)[0]], idx, len(controles))
    rng = np.random.default_rng(0)
    elegidas = rng.choice(len(frases), size=min(a.frases, len(frases)), replace=False)
    out = None
    for j in elegidas:
        fr = frases[j]
        t, y, segs = fr
        _, _, ids, c = tensores(fr, idx)
        with torch.no_grad():
            series = {'real': y[:, k], 'dominancia': md(torch.from_numpy(t), ids, c).numpy()[:, k],
                      'tcn': mt(*(x[None] for x in entrada(frases_ac[j], idx_t)))[0].numpy()[:, k],
                      'reglas': reglas(fr, idx, medias)[:, k]}
        cap = cv2.VideoCapture(os.path.join(a.videos, str(nombres[j]) + '.mpg'))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        if out is None:
            out = cv2.VideoWriter(a.salida, cv2.VideoWriter_fourcc(*'mp4v'), fps, (1280, 480))
        i = 0
        while True:
            ok, im = cap.read()
            if not ok:
                break
            izq = cv2.resize(im, (640, 480))
            cv2.putText(izq, f'{nombres[j]}  (GRID, CC BY 4.0)', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            cuadro = np.hstack([izq, panel(series, t, i / fps, segs)])
            for _ in range(a.lento):
                out.write(cuadro)
            i += 1
        cap.release()
    out.release()
    print(a.salida)


if __name__ == '__main__':
    main()
