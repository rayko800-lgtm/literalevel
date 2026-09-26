"""No verbal v3: cejas, ojos (parpadeo, entrecerrar, abrir), sonrisa y cabeza con un modelo
GENERATIVO condicionado por la voz: flow matching (rectified flow) 1D con transformer.

Por qué generativo: la voz no determina cejas, parpadeo ni cabeza; una regresión da la media
(cara promediada, sin vida). El campo evalúa esto con FDD, diversidad y alineación con los golpes
de voz, no con r (DiffPoseTalk, ARTalk). Aquí: x1 = las 18 columnas no verbales (ARKit vía el
mapa SMIRK, menos la media del clip, en sd), x0 = ruido; la red aprende v = x1 − x0 en x_t
condicionada por la voz (HuBERT, suma de capas), «habla» + articulación, y un vector de ESTILO
(sd de cada canal en el clip: cuánto se mueve ese hablante), que se apaga el 20 % de las veces
para poder muestrear sin él. La voz se apaga el 10 % para la guía sin clasificador.

Validación (EMA, semilla fija): pérdida de flujo; y sobre una muestra por clip (Euler 32 pasos):
r por grupo (orientativo), FDD (distancia de Fréchet, covarianza diagonal, entre la sd por clip
de cada canal real y generada), diversidad (RMS entre dos semillas, en sd) y alineación con los
golpes de voz (picos de subida de dB del .npz de medidas vs mínimos de velocidad de la cabeza;
se da también la de las caras reales como referencia). El mejor modelo es el de menor pérdida
de validación. Guarda modelo.pt, normalizacion.json (con estilos reales para muestrear),
informe.json, progreso.json y ultimo.pt (reanuda solo).

Uso: python entrenar_noverbal.py --voz DIR --art DIR --smirk DIR --medidas DIR --mapa mapa_arkit.json
        --salida DIR [--cache DIR] [--epocas 300] [--paciencia 30] [--lote 48] [--lr 3e-4]
        [--capas_usar ...] [--voz_en_gpu] [--max_horas 0] [--d 256 --capas 4] [--pasos 32] [--guia 1.5]
"""
import argparse
import copy
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datos_v3 as D      # noqa: E402
import mapa_arkit         # noqa: E402
import red_v3 as R        # noqa: E402

COLUMNAS = D.NO_VERBAL
GRUPOS = {g: D.GRUPOS[g] for g in ('sonrisa', 'ojos', 'cejas', 'cabeza')}
CABEZA = [COLUMNAS.index(c) for c in D.GRUPOS['cabeza']]


def picos(x, umbral, sep=5):
    """Índices de máximos locales de x por encima de umbral, separados al menos sep."""
    idx = [i for i in range(1, len(x) - 1) if x[i] > umbral and x[i] >= x[i - 1] and x[i] >= x[i + 1]]
    out = []
    for i in idx:
        if not out or i - out[-1] >= sep:
            out.append(i)
    return np.array(out)


def golpes_voz(db):
    """Golpes de voz: picos de la subida de energía (dB) por encima de 1 sd."""
    d = np.diff(db, prepend=db[0])
    d = np.convolve(d, np.ones(3) / 3, mode='same')
    return picos(d, d.mean() + d.std())


def alineacion(mov, golpes, sigma=3.0):
    """Beat align score (Li et al. 2021): para cada golpe de voz, exp(−d²/2σ²) con d la distancia al
    golpe cinemático más cercano (mínimo local claro de la velocidad de la cabeza)."""
    if len(golpes) == 0 or len(mov) < 3:
        return float('nan')
    vel = np.linalg.norm(np.diff(mov, axis=0), axis=1)
    cin = picos(-vel, -np.median(vel))             # mínimos de velocidad claros (por debajo de la mediana)
    if len(cin) == 0:
        return 0.0
    d = np.abs(golpes[:, None] - cin[None, :]).min(1)
    return float(np.mean(np.exp(-d ** 2 / (2 * sigma ** 2))))


def frechet_diagonal(A, B):
    """Distancia de Fréchet entre dos nubes [N, C] con gaussianas de covarianza diagonal."""
    ma, mb = A.mean(0), B.mean(0)
    va, vb = A.var(0) + 1e-6, B.var(0) + 1e-6
    return float(((ma - mb) ** 2).sum() + (va + vb - 2 * np.sqrt(va * vb)).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voz', required=True); ap.add_argument('--art', required=True); ap.add_argument('--smirk', required=True)
    ap.add_argument('--medidas', required=True, help='para los dB (golpes de voz) de los clips de validación')
    ap.add_argument('--mapa', required=True); ap.add_argument('--salida', required=True)
    ap.add_argument('--cache', default=None)
    ap.add_argument('--epocas', type=int, default=300); ap.add_argument('--paciencia', type=int, default=30)
    ap.add_argument('--lote', type=int, default=48); ap.add_argument('--lr', type=float, default=3e-4)
    ap.add_argument('--capas_usar', default=''); ap.add_argument('--voz_en_gpu', action='store_true')
    ap.add_argument('--max_horas', type=float, default=0)
    ap.add_argument('--d', type=int, default=256); ap.add_argument('--capas', type=int, default=4)
    ap.add_argument('--pasos', type=int, default=32); ap.add_argument('--guia', type=float, default=1.5)
    ap.add_argument('--dispositivo', default='cuda' if torch.cuda.is_available() else 'cpu')
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    R.semillas(0)
    dev = a.dispositivo; gpu = dev.startswith('cuda')
    mapa = mapa_arkit.cargar(a.mapa)
    sel = [mapa['columnas'].index(c) for c in COLUMNAS]
    capas_usar = [int(c) for c in a.capas_usar.split(',')] if a.capas_usar else None
    medidas = D.mapa_archivos(a.medidas)

    datos = D.Conjunto(D.pares_entrenamiento(a.voz, a.art, a.smirk), mapa, a.cache or os.path.join(a.salida, 'cache'),
                       capas_usar, a.max_horas)
    datos.y = datos.y[:, sel]; datos.sd = datos.sd[sel]
    for c in datos.val:
        c['y'] = c['y'][:, sel]
        c['db'] = np.load(medidas[c['nombre']])['db'][:len(c['ok'])] if c['nombre'] in medidas else None
    datos.a_torch(dev, a.voz_en_gpu)
    sd = datos.sd; C = len(COLUMNAS); K = datos.voz.shape[1]
    # estilo por ventana: sd de cada canal en la ventana (en sd globales), guardado por ventana
    estilos = np.zeros((len(datos.inicios), C), np.float32)
    for j, i in enumerate(datos.inicios):
        m = datos.m[i:i + D.L]
        estilos[j] = (datos.y[i:i + D.L][m] / sd).std(0) if m.sum() > 10 else 1.0
    estilos_t = torch.from_numpy(estilos)
    estilos_val = [((c['y'][c['ok']] / sd).std(0)).astype(np.float32) for c in datos.val]
    rng = np.random.default_rng(0)
    muestra_estilos = estilos[rng.choice(len(estilos), min(16, len(estilos)), replace=False)].tolist()

    red = R.NoVerbal(K, C, a.d, a.capas, n_estilo=C).to(dev)
    ema = copy.deepcopy(red).eval()
    for p in ema.parameters():
        p.requires_grad_(False)
    opt = torch.optim.AdamW(red.parameters(), a.lr, weight_decay=0.02)
    pasos_ep = (len(datos.inicios) + a.lote - 1) // a.lote
    sched = R.planificador(opt, pasos_ep, a.epocas)
    bf16 = gpu and torch.cuda.is_bf16_supported()
    tipo = torch.bfloat16 if bf16 else torch.float16
    escala = torch.amp.GradScaler(enabled=gpu and not bf16)
    estado = R.cargar_estado(os.path.join(a.salida, 'ultimo.pt'), red, ema, opt, sched, escala, dev) or {}
    ep0, mejor, mejor_ep, sin_mejora, paso = (estado.get(k, v) for k, v in
                                              (('epoca', 0), ('mejor', 1e9), ('mejor_ep', 0), ('sin_mejora', 0), ('paso', 0)))
    if estado:
        print(f'reanudando desde la época {ep0} (mejor pérdida val {mejor:.4f} en la {mejor_ep})', flush=True)
    primera = np.load(next(iter(D.mapa_archivos(a.voz).values())))
    json.dump({'columnas': COLUMNAS, 'sd': sd.tolist(), 'capas': [int(c) for c in (capas_usar or primera['capas'])],
               'codificador': str(primera['codificador']), 'arquitectura': f'NoVerbal flow d={a.d} capas={a.capas}',
               'd': a.d, 'capas_transformer': a.capas, 'pasos': a.pasos, 'guia': a.guia, 'estilos': muestra_estilos,
               'estilo_medio': estilos.mean(0).tolist()},
              open(os.path.join(a.salida, 'normalizacion.json'), 'w'))
    inicios = torch.from_numpy(datos.inicios)

    def tensores_clip(c):
        tv = torch.from_numpy(c['voz'].astype(np.float32)).to(dev)[None]
        ta = torch.from_numpy(c['art'].astype(np.float32)).to(dev)[None]
        return tv, ta, torch.from_numpy(c['fon']).to(dev)[None]

    def perdida_val(modelo):
        """Pérdida de flujo en las ventanas de validación con t y ruido fijos (semilla)."""
        g = torch.Generator(device=dev).manual_seed(1)
        tot, n = 0.0, 0
        with torch.no_grad(), torch.autocast('cuda' if gpu else 'cpu', dtype=tipo, enabled=gpu):
            for c, est in zip(datos.val, estilos_val):
                for k in range(0, len(c['ok']) - D.L + 1, D.L):
                    tv, ta, tf = (x[:, k:k + D.L] for x in tensores_clip(c))
                    x1 = torch.from_numpy(c['y'][k:k + D.L] / sd).to(dev)[None].float()
                    m = torch.from_numpy(c['ok'][k:k + D.L]).to(dev)[None, :, None].float()
                    x0 = torch.randn(x1.shape, generator=g, device=dev); t = torch.rand(1, generator=g, device=dev)
                    xt = (1 - t)[:, None, None] * x0 + t[:, None, None] * x1
                    v = modelo(xt, t, tv, ta, tf, torch.from_numpy(est).to(dev)[None]).float()
                    tot += (((v - (x1 - x0)) ** 2) * m).sum().item() / C; n += m.sum().item()
        return tot / max(n, 1)

    def muestras(modelo, semilla):
        g = torch.Generator(device=dev).manual_seed(semilla)
        out = []
        with torch.no_grad(), torch.autocast('cuda' if gpu else 'cpu', dtype=tipo, enabled=gpu):
            for c, est in zip(datos.val, estilos_val):
                tv, ta, tf = tensores_clip(c)
                x = modelo.muestrear(tv, ta, tf, torch.from_numpy(est).to(dev)[None], a.pasos, a.guia, g)
                out.append(x[0].float().cpu().numpy() * sd)
        return out

    def evaluar(modelo, ep):
        pv = perdida_val(modelo)
        S1, S2 = muestras(modelo, 1), muestras(modelo, 2)
        P = np.concatenate([s[c['ok']] for s, c in zip(S1, datos.val)])
        T = np.concatenate([c['y'][c['ok']] for c in datos.val])
        r = R.correlaciones(P, T, COLUMNAS)
        din_real = np.stack([(c['y'][c['ok']] / sd).std(0) for c in datos.val])
        din_gen = np.stack([(s[c['ok']] / sd).std(0) for s, c in zip(S1, datos.val)])
        div = float(np.mean([np.sqrt(np.mean(((s1 - s2) / sd) ** 2)) for s1, s2 in zip(S1, S2)]))
        al_gen, al_real = [], []
        for s, c in zip(S1, datos.val):
            if c['db'] is not None:
                gv = golpes_voz(c['db'])
                al_gen.append(alineacion(s[:, CABEZA], gv)); al_real.append(alineacion(c['y'][:, CABEZA], gv))
        return {'epocas_hechas': ep, 'perdida_val': round(pv, 4), 'r_grupos': R.media_grupos(r, GRUPOS, COLUMNAS), 'r': r,
                'fdd': round(frechet_diagonal(din_real, din_gen), 4), 'diversidad': round(div, 3),
                'alineacion_golpes': {'red': round(float(np.nanmean(al_gen)), 3) if al_gen else None,
                                      'real': round(float(np.nanmean(al_real)), 3) if al_real else None},
                'clips_validacion': len(datos.val), 'ventanas_entrenamiento': int(len(inicios)),
                'horas_entrenamiento': round(datos.horas, 2), 'pesos_capas': modelo.tronco.voz.pesos_capas()}

    for ep in range(ep0, a.epocas):
        t0 = time.time(); red.train(); tot = 0.0
        perm = torch.randperm(len(inicios))
        for i in range(0, len(perm), a.lote):
            ids = perm[i:i + a.lote]
            voz, art, fon, x1, m = datos.lote(inicios[ids], dev)
            B = x1.shape[0]
            voz = R.aumentar_voz(voz, D.L, dev, p_apagar=0.0)
            est = estilos_t[ids].to(dev) * (torch.rand(B, 1, device=dev) > 0.2)          # estilo apagado a veces
            sin_voz = torch.rand(B, device=dev) < 0.1                                    # para la guía sin clasificador
            x0 = torch.randn_like(x1); t = torch.rand(B, device=dev)
            xt = (1 - t)[:, None, None] * x0 + t[:, None, None] * x1
            with torch.autocast('cuda' if gpu else 'cpu', dtype=tipo, enabled=gpu):
                v = red(xt, t, voz, art, fon, est, sin_voz)
            loss = (((v.float() - (x1 - x0)) ** 2) * m).sum() / (m.sum() * C).clamp(min=1)
            opt.zero_grad(set_to_none=True)
            escala.scale(loss).backward(); escala.unscale_(opt)
            nn.utils.clip_grad_norm_(red.parameters(), 1.0)
            escala.step(opt); escala.update(); sched.step(); paso += 1
            R.ema_actualizar(ema, red, paso)
            tot += loss.item() * B
        inf = evaluar(ema, ep + 1)
        linea = {'epoca': ep + 1, 'perdida': round(tot / len(perm), 4), 'perdida_val': inf['perdida_val'], 'r': inf['r_grupos'],
                 'fdd': inf['fdd'], 'diversidad': inf['diversidad'], 'alineacion': inf['alineacion_golpes'],
                 'lr': round(sched.get_last_lr()[0], 6), 's': round(time.time() - t0, 1)}
        if inf['perdida_val'] < mejor:
            mejor, mejor_ep, sin_mejora = inf['perdida_val'], ep + 1, 0
            torch.save(ema.state_dict(), os.path.join(a.salida, 'modelo.pt'))
            linea['mejor'] = True
        else:
            sin_mejora += 1
        inf['mejor_epoca'] = mejor_ep
        json.dump(inf, open(os.path.join(a.salida, 'informe.json'), 'w'), indent=1)
        R.guardar_estado(os.path.join(a.salida, 'ultimo.pt'), red, ema, opt, sched, escala,
                         epoca=ep + 1, mejor=mejor, mejor_ep=mejor_ep, sin_mejora=sin_mejora, paso=paso)
        R.anotar(a.salida, linea)
        if sin_mejora >= a.paciencia:
            print(f'parada temprana: sin mejorar desde la época {mejor_ep}', flush=True)
            break
    print('mejor época', mejor_ep, 'pérdida val', round(mejor, 4), flush=True)
    print('FIN', flush=True)


if __name__ == '__main__':
    main()
