"""Exporta el modelo de dominancia a un JSON que podría leer `animacion.ts`:
por fonema (ARPAbet) y control, objetivo T, peso α y velocidades θ de
anticipación y arrastre, más la media y la desviación con que se
normalizó cada control. No toca `front/`: escribe donde se le diga.

Uso: python exportar_modelo.py --modelo dominancia_sin_X.pt --salida modelo.json
"""
import argparse
import json
import os

import torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', required=True)
    ap.add_argument('--salida', required=True)
    a = ap.parse_args()
    d = torch.load(a.modelo, weights_only=True)
    e = d['estado']
    r = lambda x: [[round(float(v), 4) for v in fila] for fila in x]
    json.dump({
        'version': 1,
        'modelo': 'dominancia Cohen-Massaro, entrenada con GRID (CC BY 4.0)',
        'formula': 'y(t) = sum_s D_s(t) T[p_s] / sum_s D_s(t); D_s = exp(log_alfa - theta * |c_s - t|), '
                   'theta = exp(log_theta_ant) si t < c_s, si no exp(log_theta_arr); salida en z del hablante',
        'fonemas': d['fonemas'], 'controles': d['controles'],
        'T': r(e['T']), 'log_alfa': r(e['la']), 'log_theta_ant': r(e['lta']), 'log_theta_arr': r(e['ltc']),
    }, open(a.salida, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print(a.salida, os.path.getsize(a.salida), 'bytes')


if __name__ == '__main__':
    main()
