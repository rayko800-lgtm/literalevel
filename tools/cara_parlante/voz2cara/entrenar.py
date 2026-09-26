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
    x = v['voz'].astype(np.float16)                 # float16 en memoria: Obama entero cabe en ~6 GB
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
    L = 250
    # Todos los clips de entrenamiento van a un único array float16 reservado de antemano
    # (cada uno rellenado hasta L fotogramas); por ventana (L fotogramas cada L/2) solo se
    # guarda su posición de inicio. Así Obama + 1KH (~28 h, ~4,6 GB) cabe en los 12 GB de Colab:
    # nunca hay dos copias de los rasgos a la vez.
    elegidos = []
    for i, (n, fv, fm) in enumerate(todos):
        m = np.load(fm)
        largo = len(m['t'])
        if m['ok'].mean() < 0.6 or largo < 75:
            continue
        elegidos.append((es_val(i, n, fm), fv, fm, largo))
    total = sum(max(largo, L) for v, _, _, largo in elegidos if not v)
    Xn = np.zeros((total, 768), np.float16)
    val, Ys, Ms, inicios, pos, nombres, horas = [], [], [], [], 0, None, 0.0
    for v, fv, fm, largo in elegidos:
        r = cargar(fv, fm)
        if r is None:
            continue
        x, y, ok, nombres, dur = r
        if v:
            val.append((x, y, ok))
            continue
        pad = max(0, L - len(x))
        Xn[pos:pos + len(x)] = x
        y, ok = np.pad(y, ((0, pad), (0, 0))), np.pad(ok, (0, pad))
        inicios += [pos + k for k in range(0, len(y) - L + 1, L // 2)]
        Ys.append(y); Ms.append(ok); pos += len(y); horas += dur / 3600
    Yn, Mn = np.concatenate(Ys), np.concatenate(Ms); del Ys, Ms
    sd = Yn[Mn].std(0) + 1e-3
    print(f'entrenamiento {len(inicios)} ventanas ({horas:.1f} h), validación {len(val)} clips', flush=True)
    Xe, Ye, Me = torch.from_numpy(Xn), torch.from_numpy((Yn / sd).astype(np.float32)), torch.from_numpy(Mn)
    inicios, rango = torch.tensor(inicios), torch.arange(L)
    dev = a.dispositivo
    red = Red(sal=Ye.shape[1]).to(dev)
    opt = torch.optim.AdamW(red.parameters(), 3e-4, weight_decay=0.01)
    pasos = a.epocas * ((len(inicios) + 31) // 32)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, 1e-3, total_steps=pasos)
    gpu = dev.startswith('cuda')
    escala = torch.amp.GradScaler(enabled=gpu)                       # float16 mixto en la T4
    for ep in range(a.epocas):
        red.train(); perm = torch.randperm(len(inicios)); tot = 0
        for i in range(0, len(perm), 32):
            b = perm[i:i + 32]
            idx = inicios[b][:, None] + rango                                    # [B, L]
            x, y, m = Xe[idx].to(dev).float(), Ye[idx].to(dev), Me[idx].to(dev).unsqueeze(-1).float()
            x = x + 0.05 * torch.randn_like(x)
            with torch.autocast('cuda' if gpu else 'cpu', dtype=torch.float16, enabled=gpu):
                p = red(x)
            p = p.float()
            l1 = ((p - y) ** 2 * m).sum() / (m.sum() * y.shape[2])
            dv = (p[:, 1:] - p[:, :-1]) - (y[:, 1:] - y[:, :-1])
            l2 = (dv ** 2 * m[:, 1:] * m[:, :-1]).sum() / (m.sum() * y.shape[2])
            loss = l1 + 0.5 * l2
            opt.zero_grad(); escala.scale(loss).backward(); escala.unscale_(opt)
            nn.utils.clip_grad_norm_(red.parameters(), 1.0); escala.step(opt); escala.update(); sched.step()
            tot += loss.item() * len(b)
        print(f'epoca {ep + 1}: {tot / len(perm):.4f}', flush=True)
        torch.save(red.state_dict(), os.path.join(a.salida, 'modelo.pt'))     # por si la sesión se cae

    red.eval(); P, T = [], []
    with torch.no_grad():
        for x, y, ok in val:
            # por trozos de 1000 fotogramas: un discurso entero (~50 000) no cabe en la atención
            p = np.concatenate([red(torch.tensor(x[k:k + 1000])[None].to(dev).float())[0].float().cpu().numpy()
                                for k in range(0, len(x), 1000)]) * sd
            P.append(p[ok]); T.append(y[ok])
    P, T = np.concatenate(P), np.concatenate(T)
    col = nombres + ['cabeza_guinada', 'cabeza_cabeceo', 'cabeza_alabeo']
    r = {c: float(np.corrcoef(P[:, k], T[:, k])[0, 1]) if T[:, k].std() > 1e-6 else None for k, c in enumerate(col)}
    grupos = {g: round(float(np.nanmean([r[c] for c in cs if r.get(c) is not None])), 3) for g, cs in GRUPOS.items()}
    grupos['cabeza'] = round(float(np.mean([r[c] for c in col[-3:]])), 3)
    print('r por grupo:', grupos, flush=True)
    torch.save(red.state_dict(), os.path.join(a.salida, 'modelo.pt'))
    json.dump({'columnas': col, 'sd': sd.tolist()}, open(os.path.join(a.salida, 'normalizacion.json'), 'w'))
    json.dump({'ventanas_entrenamiento': len(inicios), 'horas_entrenamiento': round(horas, 2), 'clips_validacion': len(val),
               'r_grupos': grupos, 'r': {k: (round(v, 3) if v is not None else None) for k, v in r.items()}},
              open(os.path.join(a.salida, 'informe.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
