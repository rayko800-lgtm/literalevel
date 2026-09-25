"""Las pruebas duras del encargo sobre el hablante de prueba de cada pliegue:

- cierre /p b m/: el mínimo de la apertura interior dentro del segmento
  (±40 ms), predicho contra real, en unidades z del hablante;
- redondeo anticipado /uw w/: cuántos ms antes del inicio acústico baja el
  ancho de la boca a medio camino de su mínimo, predicho contra real.

Lee los modelos que dejan `base_dominancia.py` y `tcn.py` en la misma carpeta.

Uso: python pruebas_duras.py --datos DIR --modelos DIR --salida pruebas.json
"""
import argparse
import glob
import json
import os

import numpy as np
import torch

from base_dominancia import Dominancia, cargar, escalon, reglas, tensores
from tcn import TCN, cargar_con_acento, entrada

REDONDEADAS = {'uw', 'w'}
BILABIALES = {'p', 'b', 'm'}


def medias_de(frases, idx, K):
    suma, n = np.zeros((len(idx), K)), np.zeros((len(idx), 1))
    for t, y, segs in frases:
        for p, a, b in segs:
            sel = (t >= a) & (t < b)
            suma[idx[p]] += y[sel].sum(0); n[idx[p]] += sel.sum()
    return suma / np.maximum(n, 1)


def adelanto(t, y, a, b):
    """ms entre el cruce a medio camino (antes → mínimo del segmento) y el inicio `a`."""
    antes = y[np.argmin(np.abs(t - (a - 0.3)))]
    dentro = (t >= a) & (t < b)
    if not dentro.any():
        return None
    minimo = y[dentro].min()
    if antes - minimo < 0.3:              # no hay gesto que medir
        return None
    mitad = (antes + minimo) / 2
    ventana = np.where((t >= a - 0.3) & (t < b))[0]
    for i in ventana:
        if y[i] <= mitad:
            return (a - t[i]) * 1000
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--datos', required=True)
    ap.add_argument('--modelos', required=True)
    ap.add_argument('--salida', required=True)
    a = ap.parse_args()
    rutas = sorted(glob.glob(os.path.join(a.datos, '*.npz')))
    habl = {os.path.splitext(os.path.basename(r))[0]: r for r in rutas}
    datos = {h: cargar(r)[0] for h, r in habl.items()}
    datos_ac = {h: cargar_con_acento(r) for h, r in habl.items()}
    controles = cargar(rutas[0])[1]
    k_ap = [c.endswith('apertura_int') for c in controles].index(True)
    k_an = [c.endswith(':ancho') for c in controles].index(True)
    res = {}
    for prueba in habl:
        dom = torch.load(os.path.join(a.modelos, f'dominancia_sin_{prueba}.pt'), weights_only=True)
        idx = {p: i for i, p in enumerate(dom['fonemas'])}
        md = Dominancia(len(idx), len(controles)); md.load_state_dict(dom['estado']); md.eval()
        tc = torch.load(os.path.join(a.modelos, f'tcn_sin_{prueba}.pt'), weights_only=True)
        idx_t = {p: i for i, p in enumerate(tc['fonemas'])}
        mt = TCN(len(idx_t), len(controles)); mt.load_state_dict(tc['estado']); mt.eval()
        medias = medias_de([f for h, fr in datos.items() if h != prueba for f in fr], idx, len(controles))
        cierre = {m: [] for m in ('real', 'dominancia', 'tcn', 'reglas')}
        adel = {m: [] for m in cierre}
        for fr, fr_ac in zip(datos[prueba], datos_ac[prueba]):
            t, y, segs = fr
            _, _, ids, c = tensores(fr, idx)
            with torch.no_grad():
                preds = {'real': y, 'dominancia': md(torch.from_numpy(t), ids, c).numpy(),
                         'tcn': mt(*(x[None] for x in entrada(fr_ac, idx_t)))[0].numpy(),
                         'reglas': reglas(fr, idx, medias)}
            for i, (p, s0, s1) in enumerate(segs):
                if p in BILABIALES:
                    sel = (t >= s0 - 0.04) & (t < s1 + 0.04)
                    if sel.any():
                        for m, v in preds.items():
                            cierre[m].append(v[sel, k_ap].min())
                if p in REDONDEADAS and i > 0 and segs[i - 1][0] not in REDONDEADAS | {'sil'}:
                    r = adelanto(t, y[:, k_an], s0, s1)
                    if r is None:
                        continue
                    for m, v in preds.items():
                        x = adelanto(t, v[:, k_an], s0, s1)
                        adel[m].append(np.nan if x is None else x)
        real_c = np.array(cierre['real'])
        res[prueba] = {
            'cierre_pbm': {m: {'error_medio_z': round(float(np.mean(np.array(v) - real_c)), 3),
                               'dentro_0.3z': round(float(np.mean(np.abs(np.array(v) - real_c) <= 0.3)), 3)}
                           for m, v in cierre.items() if m != 'real'},
            'n_pbm': len(real_c),
            'redondeo_adelanto_ms': {m: {'mediana': round(float(np.nanmedian(v)), 1),
                                         'sin_gesto': round(float(np.mean(np.isnan(v))), 3)}
                                     for m, v in adel.items()},
            'n_redondeo': len(adel['real']),
        }
        print(prueba, json.dumps(res[prueba], ensure_ascii=False), flush=True)
    json.dump(res, open(a.salida, 'w', encoding='utf8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
