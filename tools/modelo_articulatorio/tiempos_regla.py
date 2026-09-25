"""¿Cuánto se pierde si el modelo recibe los tiempos de fonema que la app
puede calcular (duraciones de regla `DURACION_S` repartidas en el tramo de
voz) en vez de los de MFA? Mismos modelos, mismos hablantes de prueba; solo
cambian los tiempos de entrada. La salida real sigue siendo la misma.

Uso: python tiempos_regla.py --datos DIR --prueba ls50 ... --dominancia X.pt --tcn Y.pt --fps 24 --salida r.json
"""
import argparse
import json
import os

import numpy as np
import torch

from base_dominancia import Dominancia, cargar, metricas, tensores
from tcn import TCN, cargar_con_acento, entrada

# `DURACION_S` de poses.ts por tipo de sonido, con los fonemas en ARPAbet.
CLASE = {**{p: 0.34 for p in 'aa ae ah ao eh er ih iy uh uw'.split()},
         **{p: 0.46 for p in 'aw ay ey ow oy'.split()},
         **{p: 0.2 for p in 'p b t d k g'.split()}, **{p: 0.28 for p in 'ch jh'.split()},
         **{p: 0.22 for p in 'f v th dh s z sh zh hh'.split()}, **{p: 0.2 for p in 'm n ng'.split()},
         **{p: 0.18 for p in 'l r w y'.split()}}


def a_regla(segs, clase=None):
    """Los fonemas entre el primer y el último no-silencio, repartidos por
    `CLASE` en ese mismo tramo (las pausas internas desaparecen, como cuando
    el audio del TTS no trae un hueco medible)."""
    voz = [i for i, s in enumerate(segs) if s[0] != 'sil']
    if not voz:
        return segs
    i0, i1 = voz[0], voz[-1]
    a, b = segs[i0][1], segs[i1][2]
    medio = [s for s in segs[i0:i1 + 1] if s[0] != 'sil']
    clase = clase or CLASE
    pesos = np.array([clase.get(s[0], 0.2) for s in medio])
    cortes = a + (b - a) * np.concatenate([[0], np.cumsum(pesos) / pesos.sum()])
    nuevos = [(s[0], float(cortes[k]), float(cortes[k + 1]), *s[3:]) for k, s in enumerate(medio)]
    return list(segs[:i0]) + nuevos + list(segs[i1 + 1:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--datos', required=True)
    ap.add_argument('--prueba', nargs='+', required=True)
    ap.add_argument('--dominancia', required=True)
    ap.add_argument('--tcn', required=True)
    ap.add_argument('--fps', type=float, default=25.0)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--aprender_de', nargs='*', default=[],
                    help='hablantes de entrenamiento: duración media por fonema en vez de `DURACION_S`')
    a = ap.parse_args()
    aprendida = None
    if a.aprender_de:
        dur = {}
        for h in a.aprender_de:
            for _, _, segs in cargar(os.path.join(a.datos, h + '.npz'))[0]:
                for p, x0, x1 in segs:
                    dur.setdefault(p, []).append(x1 - x0)
        aprendida = {p: float(np.mean(v)) for p, v in dur.items()}
    dom = torch.load(a.dominancia, weights_only=True)
    idx = {p: i for i, p in enumerate(dom['fonemas'])}
    tc = torch.load(a.tcn, weights_only=True)
    idx_t = {p: i for i, p in enumerate(tc['fonemas'])}
    K = len(dom['controles'])
    md = Dominancia(len(idx), K); md.load_state_dict(dom['estado']); md.eval()
    mt = TCN(len(idx_t), K); mt.load_state_dict(tc['estado']); mt.eval()
    filas = {(m, t): [] for m in ('dominancia', 'tcn') for t in ('mfa', 'regla', 'aprendida')}
    for h in a.prueba:
        ruta = os.path.join(a.datos, h + '.npz')
        for fr, fr_ac in zip(cargar(ruta)[0], cargar_con_acento(ruta)):
            t, y, segs = fr
            tipos = [('mfa', segs, fr_ac[2]), ('regla', a_regla(segs), a_regla(fr_ac[2]))]
            if aprendida:
                tipos.append(('aprendida', a_regla(segs, aprendida), a_regla(fr_ac[2], aprendida)))
            for tipo, s, s_ac in tipos:
                _, _, ids, c = tensores((t, y, s), idx)
                with torch.no_grad():
                    filas[('dominancia', tipo)].append(metricas(md(torch.from_numpy(t), ids, c).numpy(), y, a.fps))
                    filas[('tcn', tipo)].append(metricas(mt(*(x[None] for x in entrada((t, y, s_ac), idx_t)))[0].numpy(), y, a.fps))
    res = {f'{m}_{t}': {'pearson_medio': round(float(np.mean([x[1] for x in v])), 3),
                        'rmse_medio': round(float(np.mean([x[0] for x in v])), 3)} for (m, t), v in filas.items() if v}
    print(json.dumps(res, ensure_ascii=False))
    json.dump(res, open(a.salida, 'w', encoding='utf8'), indent=1)


if __name__ == '__main__':
    main()
