"""Modelo de gestos de Eos: de la prosodia (tono y volumen) a cejas, sonrisa, ojos y cabeza.

Aprende de caras reales medidas con MediaPipe (TalkingHead-1KH y Miralles; Obama cuando
esté en local): cuándo se levantan las cejas, cuándo se sonríe, cuándo se asiente.
Una red convolucional pequeña y no causal (ve ±1,3 s de voz), entrenada en CPU.

Entradas por fotograma (25 fps): semitonos respecto a la mediana del hablante, sonoro/no,
dB normalizados, sus derivadas y la distancia a la pausa más cercana.
Salidas (z por clip, así no aprende la cara de cada hablante sino su movimiento):
cejas (interior, exterior), sonrisa, entrecerrar ojos, parpadeo y cabeza (cabeceo, guiñada, alabeo).

Uso: python entrenar_gestos.py --datos D:/literalevel_cara/medidas --salida investigacion/cara_parlante/gestos
Deja modelo_gestos.json (pesos para numpy) e informe.json (r por salida en validación frente a no moverse).
"""
import argparse
import glob
import json
import os

import numpy as np
import torch
import torch.nn as nn

FPS = 25
SALIDAS = ['cejas_int', 'cejas_ext', 'sonrisa', 'entrecerrar', 'parpadeo', 'cabeceo', 'guinada', 'alabeo']


def cargar(npz):
    d = np.load(npz)
    n = list(d['bs_nombres'])
    t = d['t']
    if len(t) < 3 * FPS:
        return None
    g = np.arange(t[0], t[-1], 1 / FPS)
    ok = np.interp(g, t, d['ok'].astype(float)) > 0.5
    if ok.mean() < 0.6:
        return None

    def bs(*nombres):
        return np.mean([np.interp(g, t, d['bs'][:, n.index(x)]) for x in nombres], 0)

    y = np.stack([bs('browInnerUp'), bs('browOuterUpLeft', 'browOuterUpRight'),
                  bs('mouthSmileLeft', 'mouthSmileRight'), bs('eyeSquintLeft', 'eyeSquintRight'),
                  bs('eyeBlinkLeft', 'eyeBlinkRight')] +
                 [np.interp(g, t, d['pose'][:, k]) for k in range(3)], 1)
    f0 = np.interp(g, t, np.nan_to_num(d['f0']))
    db = np.interp(g, t, np.nan_to_num(d['db'], nan=-60))
    voz = f0 > 0
    if voz.mean() < 0.2:
        return None
    st = np.where(voz, 12 * np.log2(np.maximum(f0, 1) / np.median(f0[voz])), 0)
    dbn = (db - np.median(db[voz])) / (db[voz].std() + 1e-6)
    # distancia (s) a la pausa más cercana (tramo sin voz de más de 0,2 s), recortada a 1 s
    sil = ~voz
    pausa = np.zeros(len(g), bool)
    i = 0
    while i < len(g):
        if sil[i]:
            j = i
            while j < len(g) and sil[j]:
                j += 1
            if j - i >= 0.2 * FPS:
                pausa[i:j] = True
            i = j
        else:
            i += 1
    dist = np.full(len(g), 1e9)
    ult = -1e9
    for i in range(len(g)):                      # distancia a la pausa anterior y a la siguiente
        if pausa[i]:
            ult = i
        dist[i] = i - ult
    ult = 1e9
    for i in range(len(g) - 1, -1, -1):
        if pausa[i]:
            ult = i
        dist[i] = min(dist[i], ult - i)
    dist = np.minimum(1, dist / FPS)
    x = np.stack([st / 6, voz.astype(float), dbn / 2, np.gradient(st) / 2, np.gradient(dbn), dist, pausa.astype(float)], 1)
    y = (y - y[ok].mean(0)) / (y[ok].std(0) + 1e-6)          # z por clip
    y[~ok] = 0
    return x.astype(np.float32), y.astype(np.float32), ok


class Red(nn.Module):
    def __init__(self, ent=7, sal=len(SALIDAS), h=48):
        super().__init__()
        capas, c = [], ent
        for dil in (1, 2, 4, 8):
            capas += [nn.Conv1d(c, h, 3, padding=dil, dilation=dil), nn.GELU()]
            c = h
        self.cuerpo = nn.Sequential(*capas)
        self.cabeza = nn.Conv1d(h, sal, 1)

    def forward(self, x):          # x [B, T, E]
        return self.cabeza(self.cuerpo(x.transpose(1, 2))).transpose(1, 2)


def trozos(datos, largo=250):
    X, Y, M = [], [], []
    for x, y, ok in datos:
        for i in range(0, len(x) - largo + 1, largo // 2):
            X.append(x[i:i + largo]); Y.append(y[i:i + largo]); M.append(ok[i:i + largo])
    return torch.tensor(np.array(X)), torch.tensor(np.array(Y)), torch.tensor(np.array(M))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--datos', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--epocas', type=int, default=25)
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    arch = sorted(glob.glob(os.path.join(a.datos, '**', '*.npz'), recursive=True))
    # validación: la carpeta val de 1KH y 1 de cada 8 vídeos de Miralles (por vídeo, no por trozo)
    val = [f for i, f in enumerate(arch) if os.sep + 'val' + os.sep in f or ('miralles' in f and i % 8 == 0)]
    ent = [f for f in arch if f not in val]
    cd = lambda fs: [r for r in (cargar(f) for f in fs) if r is not None]
    de, dv = cd(ent), cd(val)
    horas = sum(len(x) for x, _, _ in de) / FPS / 3600
    print(f'entrenamiento: {len(de)} clips, {horas:.1f} h · validación: {len(dv)} clips')
    Xe, Ye, Me = trozos(de)
    torch.manual_seed(0)
    red = Red()
    opt = torch.optim.AdamW(red.parameters(), 2e-3, weight_decay=1e-3)
    for ep in range(a.epocas):
        perm = torch.randperm(len(Xe))
        tot = 0
        for i in range(0, len(perm), 64):
            b = perm[i:i + 64]
            p = red(Xe[b])
            m = Me[b].unsqueeze(-1).float()
            loss = ((p - Ye[b]) ** 2 * m).sum() / (m.sum() * len(SALIDAS))
            opt.zero_grad(); loss.backward(); opt.step()
            tot += loss.item() * len(b)
        print(f'época {ep + 1}: {tot / len(perm):.4f}')

    # validación: r de Pearson por salida sobre fotogramas válidos, clip entero
    red.eval()
    P, Y = [], []
    with torch.no_grad():
        for x, y, ok in dv:
            p = red(torch.tensor(x)[None])[0].numpy()
            P.append(p[ok]); Y.append(y[ok])
    P, Y = np.concatenate(P), np.concatenate(Y)
    r = {s: round(float(np.corrcoef(P[:, k], Y[:, k])[0, 1]), 3) for k, s in enumerate(SALIDAS)}
    esc = {s: round(float(P[:, k].std()), 3) for k, s in enumerate(SALIDAS)}
    print('r en validación:', r)
    pesos = {k: v.detach().numpy().round(5).tolist() for k, v in red.state_dict().items()}
    json.dump({'fps': FPS, 'salidas': SALIDAS, 'entradas': ['st/6', 'voz', 'db/2', 'dst', 'ddb', 'dist_pausa', 'pausa'],
               'dilataciones': [1, 2, 4, 8], 'pesos': pesos}, open(os.path.join(a.salida, 'modelo_gestos.json'), 'w'))
    json.dump({'clips_entrenamiento': len(de), 'horas_entrenamiento': round(horas, 2), 'clips_validacion': len(dv),
               'r_validacion': r, 'sd_prediccion_z': esc,
               'nota': 'z por clip; r>0 = acierta la dirección del gesto frente a no moverse (r=0)'},
              open(os.path.join(a.salida, 'informe.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
