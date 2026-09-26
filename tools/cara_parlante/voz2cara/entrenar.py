"""Modelo voz→cara: de los rasgos wav2vec2 (extraer.py) a los 52 blendshapes ARKit y la pose
de la cabeza, en la rejilla de fotogramas de cada vídeo (≈25-30 fps). Transformer pequeño no causal sobre ventanas de 10 s.

Objetivo por clip: blendshapes menos su media en el clip (así no aprende la cara en reposo de
cada hablante, sí su movimiento), escalados por la sd global; pose en grados menos su media.
Pérdida: MSE en fotogramas con cara + 0,5·MSE de la velocidad (movimiento suave).
Validación por vídeo: la carpeta val de 1KH y 1 de cada 8 vídeos de Obama y Miralles.

Uso: python entrenar.py --voz DIR_RASGOS --medidas DIR_NPZ --salida DIR [--epocas 30] [--dispositivo cuda]
Deja modelo.pt, normalizacion.json e informe.json (r de Pearson por grupo y por blendshape).
"""
import argparse
import glob
import json
import os
import zlib

import numpy as np
import torch
import torch.nn as nn

GRUPOS = {
    'boca': ['jawOpen', 'mouthClose', 'mouthFunnel', 'mouthPucker', 'mouthPressLeft', 'mouthPressRight',
             'mouthRollLower', 'mouthRollUpper', 'mouthLowerDownLeft', 'mouthLowerDownRight',
             'mouthUpperUpLeft', 'mouthUpperUpRight', 'mouthStretchLeft', 'mouthStretchRight'],
    'sonrisa': ['mouthSmileLeft', 'mouthSmileRight', 'cheekSquintLeft', 'cheekSquintRight'],
    'ojos': ['eyeBlinkLeft', 'eyeBlinkRight', 'eyeSquintLeft', 'eyeSquintRight', 'eyeWideLeft', 'eyeWideRight'],
    'cejas': ['browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 'browDownLeft', 'browDownRight'],
}


def pares(dir_voz, dir_med):
    med = {os.path.splitext(os.path.basename(f))[0]: f
           for f in glob.glob(os.path.join(dir_med, '**', '*.npz'), recursive=True)}
    for v in sorted(glob.glob(os.path.join(dir_voz, '**', '*.npz'), recursive=True)):
        n = os.path.splitext(os.path.basename(v))[0]
        if n in med:
            yield n, v, med[n]


def cargar(fv, fm):
    v, m = np.load(fv), np.load(fm)
    x = v['voz'].astype(np.float32)
    ok = m['ok'].astype(bool)
    if ok.mean() < 0.6 or len(x) < 75:
        return None
    bs = m['bs'].astype(np.float32)
    pose = np.nan_to_num(m['pose'].astype(np.float32))
    y = np.concatenate([bs, pose], 1)
    y = y - y[ok].mean(0)
    y[~ok] = 0
    return x, y, ok, list(m['bs_nombres']), float(m['t'][-1] - m['t'][0])


class Red(nn.Module):
    def __init__(self, ent=768, sal=55, d=256, capas=4, cabezas=4):
        super().__init__()
        self.entrada = nn.Sequential(nn.LayerNorm(ent), nn.Linear(ent, d))
        self.conv = nn.Conv1d(d, d, 5, padding=2, groups=d)                    # posición relativa local
        capa = nn.TransformerEncoderLayer(d, cabezas, 4 * d, dropout=0.1, batch_first=True, norm_first=True)
        self.cuerpo = nn.TransformerEncoder(capa, capas)
        self.salida = nn.Linear(d, sal)

    def forward(self, x):
        h = self.entrada(x)
        h = h + self.conv(h.transpose(1, 2)).transpose(1, 2)
        return self.salida(self.cuerpo(h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voz', required=True)
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--epocas', type=int, default=30)
    ap.add_argument('--dispositivo', default='cuda' if torch.cuda.is_available() else 'cpu')
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    todos = list(pares(a.voz, a.medidas))
    # 1KH val solo tiene 3 clips: se reserva además 1 de cada 8 vídeos de YouTube de 1KH
    # (por vídeo de origen, no por trozo, para que ningún hablante esté en los dos lados)
    externo = lambda fm: any(k in fm for k in ('obama', 'casa_blanca', 'miralles'))
    es_val = lambda i, n, fm: (os.sep + 'val' + os.sep in fm.replace('/', os.sep)) or \
        (externo(fm) and i % 8 == 0) or \
        (not externo(fm) and zlib.crc32(n.rsplit('_', 1)[0].encode()) % 8 == 0)
    ent, val, nombres, horas = [], [], None, 0.0
    for i, (n, fv, fm) in enumerate(todos):
        r = cargar(fv, fm)
        if r is None:
            continue
        nombres = r[3]
        if es_val(i, n, fm):
            val.append(r[:3])
        else:
            ent.append(r[:3]); horas += r[4] / 3600
    Y = np.concatenate([y[ok] for _, y, ok in ent])
    sd = Y.std(0) + 1e-3
    print(f'entrenamiento {len(ent)} clips ({horas:.1f} h), validación {len(val)} clips', flush=True)

    L = 250
    def ventanas(datos):
        X, Yv, M = [], [], []
        for x, y, ok in datos:
            for i in range(0, max(1, len(x) - L + 1), L // 2):
                xs, ys, ms = x[i:i + L], y[i:i + L] / sd, ok[i:i + L]
                if len(xs) < L:
                    pad = L - len(xs)
                    xs, ys, ms = np.pad(xs, ((0, pad), (0, 0))), np.pad(ys, ((0, pad), (0, 0))), np.pad(ms, (0, pad))
                X.append(xs); Yv.append(ys); M.append(ms)
        return torch.tensor(np.array(X)), torch.tensor(np.array(Yv), dtype=torch.float32), torch.tensor(np.array(M))
    Xe, Ye, Me = ventanas(ent)
    dev = a.dispositivo
    red = Red(sal=Ye.shape[2]).to(dev)
    opt = torch.optim.AdamW(red.parameters(), 3e-4, weight_decay=0.01)
    pasos = a.epocas * ((len(Xe) + 31) // 32)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, 1e-3, total_steps=pasos)
    for ep in range(a.epocas):
        red.train(); perm = torch.randperm(len(Xe)); tot = 0
        for i in range(0, len(perm), 32):
            b = perm[i:i + 32]
            x, y, m = Xe[b].to(dev), Ye[b].to(dev), Me[b].to(dev).unsqueeze(-1).float()
            x = x + 0.05 * torch.randn_like(x)
            p = red(x)
            l1 = ((p - y) ** 2 * m).sum() / (m.sum() * y.shape[2])
            dv = (p[:, 1:] - p[:, :-1]) - (y[:, 1:] - y[:, :-1])
            l2 = (dv ** 2 * m[:, 1:] * m[:, :-1]).sum() / (m.sum() * y.shape[2])
            loss = l1 + 0.5 * l2
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(red.parameters(), 1.0); opt.step(); sched.step()
            tot += loss.item() * len(b)
        print(f'época {ep + 1}: {tot / len(perm):.4f}', flush=True)

    red.eval(); P, T = [], []
    with torch.no_grad():
        for x, y, ok in val:
            p = red(torch.tensor(x)[None].to(dev))[0].cpu().numpy() * sd
            P.append(p[ok]); T.append(y[ok])
    P, T = np.concatenate(P), np.concatenate(T)
    col = nombres + ['cabeza_guinada', 'cabeza_cabeceo', 'cabeza_alabeo']
    r = {c: float(np.corrcoef(P[:, k], T[:, k])[0, 1]) if T[:, k].std() > 1e-6 else None for k, c in enumerate(col)}
    grupos = {g: round(float(np.nanmean([r[c] for c in cs if r.get(c) is not None])), 3) for g, cs in GRUPOS.items()}
    grupos['cabeza'] = round(float(np.mean([r[c] for c in col[-3:]])), 3)
    print('r por grupo:', grupos, flush=True)
    torch.save(red.state_dict(), os.path.join(a.salida, 'modelo.pt'))
    json.dump({'columnas': col, 'sd': sd.tolist()}, open(os.path.join(a.salida, 'normalizacion.json'), 'w'))
    json.dump({'clips_entrenamiento': len(ent), 'horas_entrenamiento': round(horas, 2), 'clips_validacion': len(val),
               'r_grupos': grupos, 'r': {k: (round(v, 3) if v is not None else None) for k, v in r.items()}},
              open(os.path.join(a.salida, 'informe.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
