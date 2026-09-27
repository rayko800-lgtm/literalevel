"""Boca v3: voz (HuBERT-large, suma de capas aprendida) + articulación de Blender + fonema →
las 14 columnas ARKit de la boca (etiquetas SMIRK pasadas por el mapa a ARKit), por regresión.

Salida = base lineal desde los 13 controles de Blender + corrección del transformer, como la
red de fusión. Pérdidas: posición (MSE con máscara), velocidad (diferencias) y peso pedagógico:
en los fotogramas de p/b/m las columnas de cierre (mouthClose, mouthPress*) y jawOpen pesan
--peso_pedagogico veces más, y en u/o/w las de redondeo (mouthPucker, mouthFunnel).

Validación por época con el modelo EMA: r por columna y de la boca, pedagogía (diferencia en sd
entre p/b/m y vocales abiertas en el cierre; entre u/o/w y abiertas en el redondeo; red vs real).
Guarda en --salida: modelo.pt (mejor época, EMA), normalizacion.json, informe.json (se
reescribe cada época), progreso.json (una línea por época) y ultimo.pt (red, EMA, optimizador,
planificador, época: con él el mismo mandato REANUDA solo si Colab se cae).

Uso: python entrenar_boca.py --voz DIR --art DIR --smirk DIR --mapa mapa_arkit.json --salida DIR
        --modelo_art modelo_articulatorio.json [--cache /content/datos/cache] [--epocas 300]
        [--paciencia 30] [--lote 48] [--lr 4e-4] [--capas_usar 6,9,12,15,18,21,24] [--voz_en_gpu]
        [--max_horas 0] [--d 384 --capas 6] [--dispositivo cuda]
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

COLUMNAS = D.GRUPOS['boca']
CIERRE, REDONDEO = ['mouthClose', 'mouthPressLeft', 'mouthPressRight', 'jawOpen'], ['mouthPucker', 'mouthFunnel']
ABIERTAS = ['aa', 'ae', 'ah', 'ao']


def pedagogia(P, T, F, columnas, fonemas):
    """Diferencia media (en sd) entre los fonemas de cierre/redondeo y las vocales abiertas."""
    i = {c: k for k, c in enumerate(columnas)}
    idx = {f: k for k, f in enumerate(fonemas)}

    def m(A, conj, cols):
        sel = np.isin(F, [idx[f] for f in conj if f in idx])
        return float(A[sel][:, [i[c] for c in cols]].mean()) if sel.any() else float('nan')
    out = {}
    for nombre, conj, cols in [('cierre_pbm', ['p', 'b', 'm'], ['mouthClose', 'mouthPressLeft', 'mouthPressRight']),
                               ('redondeo_uo', ['uw', 'ow', 'w'], REDONDEO)]:
        out[nombre] = {'red': round(m(P, conj, cols) - m(P, ABIERTAS, cols), 3), 'real': round(m(T, conj, cols) - m(T, ABIERTAS, cols), 3)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voz', required=True); ap.add_argument('--art', required=True); ap.add_argument('--smirk', required=True)
    ap.add_argument('--mapa', default='', help='mapa SMIRK→ARKit; vacío = etiquetas MediaPipe directas (--smirk apunta a las medidas)'); ap.add_argument('--salida', required=True)
    ap.add_argument('--modelo_art', required=True, help='modelo_articulatorio.json (nombres de fonema)')
    ap.add_argument('--cache', default=None, help='carpeta local para el memmap de la voz (por defecto --salida/cache)')
    ap.add_argument('--epocas', type=int, default=300); ap.add_argument('--paciencia', type=int, default=30)
    ap.add_argument('--lote', type=int, default=48); ap.add_argument('--lr', type=float, default=4e-4)
    ap.add_argument('--peso_pedagogico', type=float, default=3.0)
    ap.add_argument('--capas_usar', default='', help='subconjunto de las capas guardadas (T4: 12,18,24)')
    ap.add_argument('--voz_en_gpu', action='store_true'); ap.add_argument('--max_horas', type=float, default=0)
    ap.add_argument('--d', type=int, default=384); ap.add_argument('--capas', type=int, default=6)
    ap.add_argument('--dispositivo', default='cuda' if torch.cuda.is_available() else 'cpu')
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    R.semillas(0)
    dev = a.dispositivo; gpu = dev.startswith('cuda')
    fonemas = json.load(open(a.modelo_art))['fonemas']
    mapa = mapa_arkit.cargar(a.mapa) if a.mapa else {'columnas': D.columnas_mediapipe(a.smirk)}
    sel = [mapa['columnas'].index(c) for c in COLUMNAS]
    capas_usar = [int(c) for c in a.capas_usar.split(',')] if a.capas_usar else None

    datos = D.Conjunto(D.pares_entrenamiento(a.voz, a.art, a.smirk), mapa, a.cache or os.path.join(a.salida, 'cache'),
                       capas_usar, a.max_horas)
    datos.y = datos.y[:, sel]; datos.sd = datos.sd[sel]
    for c in datos.val:
        c['y'] = c['y'][:, sel]
    datos.a_torch(dev, a.voz_en_gpu)
    sd = datos.sd
    K = datos.voz.shape[1]
    # pesos por columna y por fonema (pedagogía)
    idx_fon = {f: k for k, f in enumerate(fonemas)}
    peso_col = torch.ones(len(COLUMNAS), device=dev)
    es_cierre = torch.tensor([c in CIERRE for c in COLUMNAS], device=dev)
    es_redondeo = torch.tensor([c in REDONDEO for c in COLUMNAS], device=dev)
    fon_cierre = torch.tensor([idx_fon[f] for f in ('p', 'b', 'm') if f in idx_fon], device=dev)
    fon_redondeo = torch.tensor([idx_fon[f] for f in ('uw', 'ow', 'w') if f in idx_fon], device=dev)

    red = R.Boca(K, len(COLUMNAS), a.d, a.capas).to(dev)
    ema = copy.deepcopy(red).eval()
    for p in ema.parameters():
        p.requires_grad_(False)
    opt = torch.optim.AdamW(red.parameters(), a.lr, weight_decay=0.05)
    pasos_ep = (len(datos.inicios) + a.lote - 1) // a.lote
    sched = R.planificador(opt, pasos_ep, a.epocas)
    bf16 = gpu and torch.cuda.is_bf16_supported()
    tipo = torch.bfloat16 if bf16 else torch.float16
    escala = torch.amp.GradScaler(enabled=gpu and not bf16)
    estado = R.cargar_estado(os.path.join(a.salida, 'ultimo.pt'), red, ema, opt, sched, escala, dev) or {}
    ep0, mejor, mejor_ep, sin_mejora, paso = (estado.get(k, v) for k, v in
                                              (('epoca', 0), ('mejor', -1.0), ('mejor_ep', 0), ('sin_mejora', 0), ('paso', 0)))
    if estado:
        print(f'reanudando desde la época {ep0} (mejor {mejor:.4f} en la {mejor_ep})', flush=True)
    json.dump({'columnas': COLUMNAS, 'sd': sd.tolist(), 'capas': [int(c) for c in (capas_usar or np.load(datos_v3_primera(a.voz))['capas'])],
               'codificador': str(np.load(datos_v3_primera(a.voz))['codificador']), 'arquitectura': f'Boca d={a.d} capas={a.capas}',
               'd': a.d, 'capas_transformer': a.capas, 'fonemas': fonemas},
              open(os.path.join(a.salida, 'normalizacion.json'), 'w'))
    inicios = torch.from_numpy(datos.inicios)

    def validar(modelo):
        P, T, F = [], [], []
        with torch.no_grad(), torch.autocast('cuda' if gpu else 'cpu', dtype=tipo, enabled=gpu):
            for c in datos.val:
                trozos = []
                for k in range(0, len(c['ok']), 1000):
                    tv = torch.from_numpy(c['voz'][k:k + 1000].astype(np.float32)).to(dev)[None]
                    ta = torch.from_numpy(c['art'][k:k + 1000].astype(np.float32)).to(dev)[None]
                    tf = torch.from_numpy(c['fon'][k:k + 1000]).to(dev)[None]
                    trozos.append(modelo(tv, ta, tf)[0].float().cpu().numpy())
                p = np.concatenate(trozos) * sd
                ok = c['ok']
                P.append(p[ok]); T.append(c['y'][ok]); F.append(c['fon'][ok])
        return np.concatenate(P), np.concatenate(T), np.concatenate(F)

    def informe(P, T, F, ep):
        r = R.correlaciones(P, T, COLUMNAS)
        return {'epocas_hechas': ep, 'mejor_epoca': mejor_ep, 'ventanas_entrenamiento': int(len(inicios)),
                'horas_entrenamiento': round(datos.horas, 2), 'clips_validacion': len(datos.val),
                'r_boca': R.media_grupos(r, {'boca': COLUMNAS}, COLUMNAS)['boca'], 'r': r,
                'pedagogia': pedagogia(P / sd, T / sd, F, COLUMNAS, fonemas), 'pesos_capas': ema.tronco.voz.pesos_capas()}

    for ep in range(ep0, a.epocas):
        t0 = time.time(); red.train(); tot = 0.0
        perm = torch.randperm(len(inicios))
        for i in range(0, len(perm), a.lote):
            voz, art, fon, y, m = datos.lote(inicios[perm[i:i + a.lote]], dev)
            voz = R.aumentar_voz(voz, D.L, dev)
            with torch.autocast('cuda' if gpu else 'cpu', dtype=tipo, enabled=gpu):
                p = red(voz, art, fon)
            p = p.float()
            # peso pedagógico: cierre en p/b/m y redondeo en u/o/w
            w = peso_col[None, None, :].expand(p.shape[0], D.L, -1).clone()
            w = w + (a.peso_pedagogico - 1) * (torch.isin(fon, fon_cierre)[..., None] & es_cierre).float()
            w = w + (a.peso_pedagogico - 1) * (torch.isin(fon, fon_redondeo)[..., None] & es_redondeo).float()
            wm = w * m
            l1 = ((p - y) ** 2 * wm).sum() / wm.sum().clamp(min=1)
            dv = (p[:, 1:] - p[:, :-1]) - (y[:, 1:] - y[:, :-1])
            wv = wm[:, 1:] * m[:, :-1]
            l2 = (dv ** 2 * wv).sum() / wv.sum().clamp(min=1)
            loss = l1 + 0.5 * l2
            opt.zero_grad(set_to_none=True)
            escala.scale(loss).backward(); escala.unscale_(opt)
            nn.utils.clip_grad_norm_(red.parameters(), 1.0)
            escala.step(opt); escala.update(); sched.step(); paso += 1
            R.ema_actualizar(ema, red, paso)
            tot += loss.item() * p.shape[0]
        P, T, F = validar(ema)
        inf = informe(P, T, F, ep + 1)
        nota = inf['r_boca'] if inf['r_boca'] is not None else -1.0
        linea = {'epoca': ep + 1, 'perdida': round(tot / len(perm), 4), 'r_boca': inf['r_boca'],
                 'pedagogia': inf['pedagogia'], 'lr': round(sched.get_last_lr()[0], 6), 's': round(time.time() - t0, 1)}
        if nota > mejor:
            mejor, mejor_ep, sin_mejora = nota, ep + 1, 0
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
    print('mejor época', mejor_ep, 'r boca', round(mejor, 3), flush=True)
    print('FIN', flush=True)


def datos_v3_primera(dir_voz):
    return next(iter(D.mapa_archivos(dir_voz).values()))


if __name__ == '__main__':
    main()
