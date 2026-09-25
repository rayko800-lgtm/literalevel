"""La vida de la cara medida por eventos, no fotograma a fotograma.

La regresión fotograma a fotograma (cuaderno de Colab, 25 sep) no aprendió
nada: r ≈ 0 entre prosodia y gestos. Aquí se mide lo que las reglas
necesitan, con promedios alineados a eventos y comparados con instantes al
azar del mismo clip (línea base):

  parpadeo   frecuencia, duración, intervalo entre parpadeos, y cuánto más
             probable es en una pausa que hablando;
  cejas      subida media alrededor de los picos de tono (el 10 % más alto
             de cada clip), con el desfase del máximo;
  cabeza     cabeceo medio alrededor del comienzo de cada pausa (fin de
             frase) y amplitud de la deriva mientras se habla;
  sonrisa    nivel en pausa frente a hablando.

Uso: python analizar_eventos.py --medidas D:/literalevel_cara/medidas --salida eventos.json
"""
import argparse
import glob
import json
import os

import numpy as np

VENTANA = 0.6  # s a cada lado del evento


def pausas(db, voz, fps, min_s=0.3):
    """Comienzos de pausa: tramos sin voz y con poca energía de al menos min_s."""
    silencio = (voz == 0) & (db < np.percentile(db, 30))
    n = int(min_s * fps)
    ini = []
    i = 0
    while i < len(silencio):
        if silencio[i]:
            j = i
            while j < len(silencio) and silencio[j]:
                j += 1
            if j - i >= n and i > 0:
                ini.append(i)
            i = j
        else:
            i += 1
    return np.array(ini, int), silencio


EJE = np.round(np.arange(-VENTANA, VENTANA + 1e-9, 0.04), 2)   # rejilla común de 25 fps


def promedio_alineado(x, eventos, fps):
    """Media de x alrededor de los eventos, en la rejilla EJE (los clips tienen fps distintos)."""
    off = np.round(EJE * fps).astype(int)
    trozos = [x[e + off] for e in eventos if e + off[0] >= 0 and e + off[-1] < len(x)]
    return np.mean(trozos, 0) if trozos else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--medidas', required=True)
    ap.add_argument('--salida', required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(0)

    res = dict(clips=0, segundos=0.0, parpadeos=0, ibi=[], dur_parp=[], parp_pausa=0.0,
               seg_pausa=0.0, parp_voz=0.0, seg_voz=0.0)
    cejas_ev, cejas_az, cab_ev, cab_az = [], [], [], []
    deriva, sonr_p, sonr_v = [], [], []
    for ruta in sorted(glob.glob(os.path.join(a.medidas, '*', '*.npz'))):
        d = np.load(ruta)
        if d['ok'].mean() < 0.9 or len(d['t']) < 100:
            continue
        fps = float(d['fps'])
        w = int(VENTANA * fps)
        n = list(d['bs_nombres'])
        bs, pose, f0, db = d['bs'], d['pose'], d['f0'], d['db']
        voz = (f0 > 0).astype(int)
        T = len(bs) / fps
        res['clips'] += 1
        res['segundos'] += T

        # parpadeo: umbral relativo al clip (gafas y ojos entornados cambian la base)
        b = (bs[:, n.index('eyeBlinkLeft')] + bs[:, n.index('eyeBlinkRight')]) / 2
        umbral = max(0.35, np.median(b) + 0.25)
        on = (b > umbral).astype(int)
        sube = np.flatnonzero(np.diff(on) == 1) + 1
        baja = np.flatnonzero(np.diff(on) == -1) + 1
        ini_p, silencio = pausas(db, voz, fps)
        for s in sube:
            fin = baja[baja > s]
            if len(fin):
                res['dur_parp'].append((fin[0] - s) / fps * 1000)
            if silencio[s]:
                res['parp_pausa'] += 1
            else:
                res['parp_voz'] += 1
        res['parpadeos'] += len(sube)
        res['ibi'] += list(np.diff(sube) / fps)
        res['seg_pausa'] += silencio.sum() / fps
        res['seg_voz'] += (~silencio).sum() / fps

        # cejas alrededor de los picos de tono
        cejas = (bs[:, n.index('browInnerUp')] + bs[:, n.index('browOuterUpLeft')]
                 + bs[:, n.index('browOuterUpRight')]) / 3
        cejas = cejas - np.median(cejas)
        if voz.sum() > 20:
            lf0 = np.where(voz > 0, np.log(np.maximum(f0, 1)), np.nan)
            corte = np.nanpercentile(lf0, 90)
            picos = [i for i in range(1, len(lf0) - 1)
                     if lf0[i] >= corte and lf0[i] >= np.nan_to_num(lf0[i - 1], nan=-9)
                     and lf0[i] >= np.nan_to_num(lf0[i + 1], nan=-9)]
            m = promedio_alineado(cejas, picos, fps)
            if m is not None:
                cejas_ev.append(m)
                cejas_az.append(promedio_alineado(cejas, rng.integers(w, len(cejas) - w, 30), fps))

        # cabeceo alrededor del comienzo de pausa (positivo = arriba)
        cab = pose[:, 1] - np.median(pose[:, 1])
        m = promedio_alineado(cab, ini_p, fps)
        if m is not None:
            cab_ev.append(m)
            cab_az.append(promedio_alineado(cab, rng.integers(w, len(cab) - w, 30), fps))
        if (~silencio).sum() > fps:
            deriva.append(np.std(pose[~silencio], 0))

        sonrisa = (bs[:, n.index('mouthSmileLeft')] + bs[:, n.index('mouthSmileRight')]) / 2
        if silencio.sum() > fps and (~silencio).sum() > fps:
            sonr_p.append(sonrisa[silencio].mean())
            sonr_v.append(sonrisa[~silencio].mean())

    ibi = np.array(res['ibi'])
    eje = EJE.tolist()

    def curva(ev, az):
        if not ev:
            return None
        e, z = np.mean(ev, 0), np.mean(az, 0)
        k = int(np.argmax(np.abs(e - z)))
        return dict(evento=e.round(4).tolist(), azar=z.round(4).tolist(), eje_s=eje,
                    max_dif=float((e - z)[k]), desfase_s=eje[k] if k < len(eje) else None,
                    n_clips=len(ev))

    salida = dict(
        clips=res['clips'], horas=round(res['segundos'] / 3600, 2),
        parpadeo=dict(
            por_min=round(res['parpadeos'] / res['segundos'] * 60, 1),
            por_min_pausa=round(res['parp_pausa'] / max(res['seg_pausa'], 1) * 60, 1),
            por_min_hablando=round(res['parp_voz'] / max(res['seg_voz'], 1) * 60, 1),
            dur_ms_mediana=round(float(np.median(res['dur_parp'])), 0),
            dur_ms_p10_p90=[round(float(np.percentile(res['dur_parp'], q)), 0) for q in (10, 90)],
            ibi_s_mediana=round(float(np.median(ibi)), 2),
            ibi_s_p10_p90=[round(float(np.percentile(ibi, q)), 2) for q in (10, 90)],
            ibi_gamma_k=round(float(np.mean(ibi) ** 2 / np.var(ibi)), 2)),
        cejas_en_picos_de_tono=curva(cejas_ev, cejas_az),
        cabeceo_al_empezar_pausa=curva(cab_ev, cab_az),
        cabeza_sd_grados_hablando=dict(zip(['guinada', 'cabeceo', 'alabeo'],
                                           np.median(deriva, 0).round(2).tolist())),
        sonrisa=dict(pausa=round(float(np.mean(sonr_p)), 3), hablando=round(float(np.mean(sonr_v)), 3)),
    )
    with open(a.salida, 'w', encoding='utf8') as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    resumen = {k: v for k, v in salida.items() if k not in ('cejas_en_picos_de_tono', 'cabeceo_al_empezar_pausa')}
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    for k in ('cejas_en_picos_de_tono', 'cabeceo_al_empezar_pausa'):
        c = salida[k]
        if c:
            print(k, f"max_dif={c['max_dif']:+.4f} desfase={c['desfase_s']} s n={c['n_clips']}")


if __name__ == '__main__':
    main()
