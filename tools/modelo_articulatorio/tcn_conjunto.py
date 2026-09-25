"""TCN conjunta: un solo codificador de fonemas y una cabeza por tipo de dato
(vídeo: labios, mandíbula y mejillas; EMA: mandíbula, labios y lengua).
Ningún conjunto tiene todo a la vez, así que cada frase solo entrena la
cabeza de lo que mide. Es la versión barata de la opción 4 del informe: el
«espacio común» es el codificador, sin alinear latentes.

Evalúa en los hablantes de prueba de cada conjunto con las mismas métricas
que `base_dominancia.py`.

Uso:
  python tcn_conjunto.py --grupo video DIR_grid --grupo video DIR_lombard --grupo ema DIR_ema
     --prueba s31 s32 s33 s34 f5 --salida resultados.json [--epocas 30]
"""
import argparse
import glob
import json
import os

import numpy as np
import torch
from torch import nn

from base_dominancia import cargar, metricas
from tcn import TCN, cargar_con_acento, entrada, lote

FPS = {'video': 25.0, 'ema': 50.0}


class Conjunta(nn.Module):
    def __init__(self, n_fon, salidas, canales=64):
        super().__init__()
        self.tronco = TCN(n_fon, canales, canales=canales)
        self.cabezas = nn.ModuleDict({g: nn.Conv1d(canales, k, 1) for g, k in salidas.items()})

    def forward(self, ids, extra, grupo):
        h = self.tronco(ids, extra).transpose(1, 2)
        return self.cabezas[grupo](torch.relu(h)).transpose(1, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--grupo', nargs=2, action='append', metavar=('TIPO', 'DIR'), required=True)
    ap.add_argument('--prueba', nargs='+', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--epocas', type=int, default=30)
    ap.add_argument('--solo', help='entrenar solo con este tipo (para medir si compartir ayuda)')
    a = ap.parse_args()
    torch.manual_seed(0); np.random.seed(0)
    datos, controles = {}, {}
    for tipo, carpeta in a.grupo:
        for ruta in sorted(glob.glob(os.path.join(carpeta, '*.npz'))):
            h = os.path.splitext(os.path.basename(ruta))[0]
            datos[(tipo, h)] = cargar_con_acento(ruta)
            controles.setdefault(tipo, cargar(ruta)[1])
    fonemas = ['<pad>'] + sorted({s[0] for fr in datos.values() for f in fr for s in f[2]})
    idx = {p: i for i, p in enumerate(fonemas)}
    m = Conjunta(len(idx), {g: len(c) for g, c in controles.items()})
    train = [(tipo, (*entrada(f, idx), torch.from_numpy(f[1]))) for (tipo, h), fr in datos.items()
             if h not in a.prueba and (not a.solo or tipo == a.solo) for f in fr]
    print('frases de entrenamiento:', {g: sum(1 for t, _ in train if t == g) for g in controles}, flush=True)
    opt = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.epocas)
    por_tipo = {g: [d for t, d in train if t == g] for g in controles}
    for ep in range(a.epocas):
        m.train()
        ordenes = {g: np.random.permutation(len(v)) for g, v in por_tipo.items() if v}
        pasos = max(len(v) for v in ordenes.values()) // 32
        for i in range(pasos):
            opt.zero_grad()
            perdida = 0
            for g, orden in ordenes.items():
                j = orden[(i * 32) % len(orden):(i * 32) % len(orden) + 32]
                ids, ex, y, mk = lote([por_tipo[g][k] for k in j])
                perdida = perdida + (((m(ids, ex, g) - y) ** 2) * mk).sum() / (mk.sum() * y.shape[2])
            perdida.backward()
            opt.step()
        sched.step()
        print(f'época {ep + 1}/{a.epocas} pérdida {float(perdida):.3f}', flush=True)
    m.eval()
    res = {'controles': controles, 'parametros': sum(p.numel() for p in m.parameters()), 'hablantes': {}}
    for (tipo, h), fr in datos.items():
        if h not in a.prueba:
            continue
        filas = []
        for f in fr:
            ids, ex = entrada(f, idx)
            with torch.no_grad():
                filas.append(metricas(m(ids[None], ex[None], tipo)[0].numpy(), f[1], FPS[tipo]))
        res['hablantes'][h] = {'tipo': tipo, 'n_frases': len(filas),
                               'rmse': np.mean([x[0] for x in filas], 0).round(3).tolist(),
                               'pearson': np.mean([x[1] for x in filas], 0).round(3).tolist(),
                               'desfase_ms': np.mean([x[2] for x in filas], 0).round(1).tolist()}
        print(h, tipo, round(float(np.mean(res['hablantes'][h]['pearson'])), 3), flush=True)
    torch.save({'estado': m.state_dict(), 'fonemas': fonemas, 'controles': {g: [str(c) for c in v] for g, v in controles.items()}},
               os.path.splitext(a.salida)[0] + '.pt')
    json.dump(res, open(a.salida, 'w', encoding='utf8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
