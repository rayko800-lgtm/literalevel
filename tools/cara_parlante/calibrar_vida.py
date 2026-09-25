"""Calibra las reglas de la vida de la cara con datos reales y las valida.

No es una red: son reglas con aleatoriedad controlada cuyos parámetros se
ajustan en los vídeos de entrenamiento y se comprueban en vídeos que no se
usaron (reparto por vídeo, 80/20):

  parpadeo  proceso de renovación con intervalos gamma (k, θ) y un factor
            de más probabilidad en pausa. Validación: distancia KS entre
            los intervalos simulados y los reales de validación, frente a
            la regla escrita a mano (uniforme 3–6 s).
  cejas     en cada pico de tono, una subida gaussiana de amplitud A,
            adelanto L y anchura σ. Validación: correlación entre la curva
            predicha y el promedio real alrededor de los picos.
  cabeza    deriva de Ornstein-Uhlenbeck por eje (desviación y tiempo de
            correlación) más un gesto antes de cada pausa (amplitud,
            adelanto, anchura). Validación: desviación y tiempo de
            correlación de validación, y la curva alrededor de las pausas.

Salida: un JSON con los parámetros que usará el front (vida_cara.json).

Uso: python calibrar_vida.py --medidas D:/literalevel_cara/medidas --salida vida_cara.json
"""
import argparse
import glob
import json
import os

import numpy as np
from scipy import optimize, stats

from analizar_eventos import EJE, pausas, promedio_alineado

FUSION_S = 0.25   # dos cierres a menos de esto son un parpadeo (ruido del detector)


def parpadeos(bs, n, fps):
    b = (bs[:, n.index('eyeBlinkLeft')] + bs[:, n.index('eyeBlinkRight')]) / 2
    on = (b > max(0.35, np.median(b) + 0.25)).astype(int)
    sube = list(np.flatnonzero(np.diff(on) == 1) + 1)
    fusion = []
    for s in sube:
        if fusion and (s - fusion[-1]) / fps < FUSION_S:
            continue
        fusion.append(s)
    return np.array(fusion, int)


def picos_tono(f0):
    voz = f0 > 0
    if voz.sum() < 20:
        return []
    lf0 = np.where(voz, np.log(np.maximum(f0, 1)), -9.0)
    corte = np.percentile(lf0[voz], 90)
    return [i for i in range(1, len(lf0) - 1)
            if lf0[i] >= corte and lf0[i] >= lf0[i - 1] and lf0[i] >= lf0[i + 1]]


def cargar(rutas):
    clips = []
    for r in rutas:
        d = np.load(r)
        if d['ok'].mean() < 0.9 or len(d['t']) < 100:
            continue
        fps = float(d['fps'])
        n = list(d['bs_nombres'])
        bs, pose, f0, db = d['bs'], d['pose'], d['f0'], d['db']
        voz = (f0 > 0).astype(int)
        ini_p, silencio = pausas(db, voz, fps)
        cejas = (bs[:, n.index('browInnerUp')] + bs[:, n.index('browOuterUpLeft')]
                 + bs[:, n.index('browOuterUpRight')]) / 3
        clips.append(dict(fps=fps, T=len(bs) / fps, parp=parpadeos(bs, n, fps), silencio=silencio,
                          ini_p=ini_p, picos=picos_tono(f0), cejas=cejas - np.median(cejas),
                          pose=pose - np.median(pose, 0), video=os.path.basename(r).rsplit('_', 1)[0]))
    return clips


def intervalos(clips):
    return np.concatenate([np.diff(c['parp']) / c['fps'] for c in clips if len(c['parp']) > 1])


def curva_media(clips, clave, serie, eje_col=None):
    ev, az = [], []
    rng = np.random.default_rng(1)
    for c in clips:
        x = c[serie] if eje_col is None else c[serie][:, eje_col]
        m = promedio_alineado(x, c[clave], c['fps'])
        if m is not None:
            ev.append(m)
            w = int(abs(EJE[0]) * c['fps']) + 1
            az.append(promedio_alineado(x, rng.integers(w, len(x) - w, 30), c['fps']))
    return np.mean(ev, 0) - np.mean(az, 0), len(ev)


def gauss(t, A, L, s):
    return A * np.exp(-0.5 * ((t - L) / s) ** 2)


def ajustar_gauss(curva):
    k = int(np.argmax(np.abs(curva)))
    p0 = [curva[k], EJE[k], 0.15]
    p, _ = optimize.curve_fit(gauss, EJE, curva, p0=p0, bounds=([-np.inf, -0.6, 0.04], [np.inf, 0.6, 0.6]))
    return p


def ou(clips, eje):
    """Desviación típica y tiempo de correlación (1/e de la autocorrelación)."""
    sds, taus = [], []
    for c in clips:
        x = c['pose'][:, eje]
        x = x - x.mean()
        if x.std() < 1e-6 or len(x) < 3 * c['fps']:
            continue
        ac = np.correlate(x, x, 'full')[len(x) - 1:] / (x.var() * len(x))
        bajo = np.flatnonzero(ac < np.exp(-1))
        sds.append(x.std())
        taus.append((bajo[0] if len(bajo) else len(x)) / c['fps'])
    return float(np.median(sds)), float(np.median(taus))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--salida', required=True)
    a = ap.parse_args()

    rutas = sorted(glob.glob(os.path.join(a.medidas, '*', '*.npz')))
    videos = sorted({os.path.basename(r).rsplit('_', 1)[0] for r in rutas})
    rng = np.random.default_rng(0)
    rng.shuffle(videos)
    val = set(videos[: len(videos) // 5])
    tr = cargar([r for r in rutas if os.path.basename(r).rsplit('_', 1)[0] not in val])
    va = cargar([r for r in rutas if os.path.basename(r).rsplit('_', 1)[0] in val])
    print(f'{len(tr)} clips de entrenamiento, {len(va)} de validación ({len(val)} vídeos)')

    # --- parpadeo
    ibi_tr, ibi_va = intervalos(tr), intervalos(va)
    k, _, theta = stats.gamma.fit(ibi_tr, floc=0)
    sim = stats.gamma.rvs(k, scale=theta, size=5000, random_state=2)
    regla_vieja = np.random.default_rng(3).uniform(3, 6, 5000)
    tasa = lambda cl, en: sum(np.sum(c['silencio'][c['parp']] == en) for c in cl) / \
        max(sum(np.sum(c['silencio'] == en) / c['fps'] for c in cl), 1)
    factor_pausa = tasa(tr, True) / max(tasa(tr, False), 1e-9)
    parpadeo = dict(
        gamma_k=round(k, 3), gamma_theta_s=round(theta, 3),
        media_s=round(k * theta, 2), por_min=round(60 / (k * theta), 1),
        factor_pausa=round(factor_pausa, 2), fusion_s=FUSION_S,
        validacion=dict(ks_modelo=round(stats.ks_2samp(sim, ibi_va).statistic, 3),
                        ks_regla_3_6s=round(stats.ks_2samp(regla_vieja, ibi_va).statistic, 3),
                        por_min_real_validacion=round(60 / ibi_va.mean(), 1)))

    # --- cejas en picos de tono
    c_tr, n_tr = curva_media(tr, 'picos', 'cejas')
    c_va, n_va = curva_media(va, 'picos', 'cejas')
    A, L, s = ajustar_gauss(c_tr)
    pred = gauss(EJE, A, L, s)
    cejas = dict(amplitud=round(A, 4), adelanto_s=round(-L, 3), anchura_s=round(s, 3),
                 validacion=dict(r_curva=round(float(np.corrcoef(pred, c_va)[0, 1]), 3),
                                 amplitud_real=round(float(c_va[np.argmax(np.abs(c_va))]), 4),
                                 n_clips=n_va))

    # --- cabeza: deriva y gesto antes de pausa
    cabeza = {}
    for i, nom in enumerate(['guinada', 'cabeceo', 'alabeo']):
        sd_tr, tau_tr = ou(tr, i)
        sd_va, tau_va = ou(va, i)
        cabeza[nom] = dict(sd_grados=round(sd_tr, 2), tau_s=round(tau_tr, 2),
                           validacion=dict(sd_grados=round(sd_va, 2), tau_s=round(tau_va, 2)))
    g_tr, _ = curva_media(tr, 'ini_p', 'pose', 1)
    g_va, n_gva = curva_media(va, 'ini_p', 'pose', 1)
    A, L, s = ajustar_gauss(g_tr)
    cabeza['gesto_pausa'] = dict(eje='cabeceo', amplitud_grados=round(A, 2), adelanto_s=round(-L, 3),
                                 anchura_s=round(s, 3),
                                 validacion=dict(r_curva=round(float(np.corrcoef(gauss(EJE, A, L, s), g_va)[0, 1]), 3),
                                                 amplitud_real=round(float(g_va[np.argmax(np.abs(g_va))]), 2),
                                                 n_clips=n_gva))

    out = dict(fuente='TalkingHead-1KH (YouTube, CC BY 3.0), medido con MediaPipe',
               clips_entrenamiento=len(tr), clips_validacion=len(va),
               parpadeo=parpadeo, cejas_en_picos_de_tono=cejas, cabeza=cabeza)
    with open(a.salida, 'w', encoding='utf8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
