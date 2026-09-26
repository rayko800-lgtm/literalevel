"""Eos habla: texto → voz (edge-tts, gratis) → curvas ARKit por fotograma para la cabeza.

Boca: el modelo articulatorio de dominancia (entrenado con GRID) sobre los fonemas
ARPAbet de g2p_en, repartidos dentro de los límites de palabra que da el TTS.
Vida: parpadeo gamma, cabeza Ornstein-Uhlenbeck, cabeceo antes de las pausas y
cejas en los picos de tono, todo con las constantes de vida_cara.json (1KH).
Sonrisa: una base suave y más sonrisa en las pausas largas (Eos es risueña).

Uso:  python generar.py --texto "..." --salida DIR [--voz en-US-AvaNeural] [--semilla 7]
Deja DIR/voz.mp3 y DIR/curvas.json ({fps, duracion, curvas: {nombre: [..]}, cabeza: [[guiñada, cabeceo, alabeo]..]}).
"""
import argparse
import asyncio
import json
import os
import re

import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MODELO = os.path.join(RAIZ, 'front', 'src', 'app', 'compartido', 'boca3d', 'modelo_articulatorio.json')
VIDA = os.path.join(RAIZ, 'investigacion', 'cara_parlante', 'vida_cara.json')
ESCALA = os.path.join(RAIZ, 'investigacion', 'cara_parlante', 'escala_boca_1kh.json')
FPS = 60

# Ganancia MediaPipe → morph ARKit: MediaPipe se queda corto (una boca bien
# abierta mide ~0,15 de jawOpen). Ajustada a ojo sobre la cabeza.
GANANCIA = {'jawOpen': 3.2, 'mouthPucker': 1.8, 'mouthFunnel': 6.0, 'mouthRollLower': 3.0,
            'mouthPress': 1.6, 'mouthClose': 6.0, 'cheekSquint': 1.0}


async def _tts(texto, voz, mp3):
    import edge_tts
    com = edge_tts.Communicate(texto, voz, rate='-4%', pitch='+6Hz', boundary='WordBoundary')
    palabras = []
    with open(mp3, 'wb') as f:
        async for trozo in com.stream():
            if trozo['type'] == 'audio':
                f.write(trozo['data'])
            elif trozo['type'] == 'WordBoundary':
                t0 = trozo['offset'] / 1e7
                palabras.append((trozo['text'], t0, t0 + trozo['duration'] / 1e7))
    return palabras


def fonemas(palabras):
    """(fonema ARPAbet sin acento, t0, t1) repartidos dentro de cada palabra; las vocales pesan el doble."""
    from g2p_en import G2p
    g2p = G2p()
    out = []
    for texto, t0, t1 in palabras:
        fs = [re.sub(r'\d', '', p).lower() for p in g2p(texto) if re.match(r'[A-Z]', p)]
        if not fs:
            continue
        peso = np.array([2.0 if f[0] in 'aeiou' else 1.0 for f in fs])
        bordes = t0 + (t1 - t0) * np.concatenate([[0], np.cumsum(peso) / peso.sum()])
        out += [(f, bordes[i], bordes[i + 1]) for i, f in enumerate(fs)]
    return out


def boca(fons, n):
    """Controles del modelo (z) por fotograma con la fórmula de dominancia."""
    M = json.load(open(MODELO))
    idx = {f: i for i, f in enumerate(M['fonemas'])}
    T, la = np.array(M['T']), np.array(M['log_alfa'])
    ta, tr = np.array(M['log_theta_ant']), np.array(M['log_theta_arr'])
    segs = [(idx['sil'], fons[0][1] - 0.25)] + [(idx.get(f, idx['ah']), (a + b) / 2) for f, a, b in fons] \
        + [(idx['sil'], fons[-1][2] + 0.25)]
    ids = np.array([s[0] for s in segs]); cs = np.array([s[1] for s in segs])
    t = np.arange(n) / FPS
    dt = cs[None, :] - t[:, None]                                     # [n, S]
    y = np.zeros((n, T.shape[1]))
    for k in range(T.shape[1]):
        theta = np.where(dt > 0, np.exp(ta[ids, k]), np.exp(tr[ids, k]))
        logd = la[ids, k] - theta * np.abs(dt)
        logd -= logd.max(1, keepdims=True)
        d = np.exp(logd); d /= d.sum(1, keepdims=True)
        y[:, k] = d @ T[ids, k]
    return {c: y[:, i] for i, c in enumerate(M['controles'])}


def ou(n, sd, tau, rng):
    a = np.exp(-1 / (FPS * tau)); x = np.zeros(n)
    for i in range(1, n):
        x[i] = a * x[i - 1] + sd * np.sqrt(1 - a * a) * rng.standard_normal()
    return x


def pulso(n, centros, amp, anchura):
    t = np.arange(n) / FPS; y = np.zeros(n)
    for c in centros:
        y += amp * np.exp(-0.5 * ((t - c) / anchura) ** 2)
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--texto', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--voz', default='en-US-AvaNeural')
    ap.add_argument('--semilla', type=int, default=7)
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    mp3 = os.path.join(a.salida, 'voz.mp3')
    palabras = asyncio.run(_tts(a.texto, a.voz, mp3))
    fons = fonemas(palabras)
    dur = palabras[-1][2] + 0.8
    n = int(dur * FPS)
    rng = np.random.default_rng(a.semilla)
    esc = json.load(open(ESCALA))
    vida = json.load(open(VIDA))
    z = boca(fons, n)

    def peso(nombre, zc, g):
        e = esc[nombre]
        return np.clip(g * (e['media'] + zc * e['sd']), 0, 1)

    cur = {}
    cur['jawOpen'] = peso('jawOpen', z['bs:jawOpen'], GANANCIA['jawOpen'])
    cur['mouthPucker'] = peso('mouthPucker', z['bs:mouthPucker'], GANANCIA['mouthPucker'])
    cur['mouthFunnel'] = peso('mouthFunnel', z['bs:mouthFunnel'], GANANCIA['mouthFunnel'])
    cur['mouthRollLower'] = peso('mouthRollLower', z['bs:mouthRollLower'], GANANCIA['mouthRollLower'])
    pr = peso('mouthPressLeft', z['bs:mouthPress'], GANANCIA['mouthPress'])
    cur['mouthPressLeft'] = cur['mouthPressRight'] = pr
    cur['mouthClose'] = np.minimum(peso('mouthClose', z['bs:mouthClose'], GANANCIA['mouthClose']), cur['jawOpen'])
    # labio inferior y superior acompañan a la mandíbula (MediaPipe los mide aparte; el modelo no los tiene)
    cur['mouthLowerDownLeft'] = cur['mouthLowerDownRight'] = 0.35 * cur['jawOpen']
    cur['mouthUpperUpLeft'] = cur['mouthUpperUpRight'] = 0.12 * cur['jawOpen']

    # pausas: huecos entre palabras de más de 180 ms, más el final
    pausas = [(b[2], c[1]) for b, c in zip(palabras, palabras[1:]) if c[1] - b[2] > 0.18]
    pausas.append((palabras[-1][2], dur))
    t = np.arange(n) / FPS

    # sonrisa: base tierna + crece en las pausas y al terminar
    son = 0.16 + pulso(n, [(p0 + p1) / 2 for p0, p1 in pausas], 0.22, 0.35)
    son += 0.25 * np.clip((t - palabras[-1][2]) / 0.6, 0, 1)
    son = np.clip(son - 0.5 * cur['mouthPucker'], 0, 0.6)
    cur['mouthSmileLeft'] = cur['mouthSmileRight'] = son
    cur['cheekSquintLeft'] = cur['cheekSquintRight'] = 0.5 * son
    cur['eyeSquintLeft'] = cur['eyeSquintRight'] = 0.35 * son

    # parpadeo: intervalos gamma de 1KH, a ~20/min (la media real, 36/min, se ve nerviosa en una cara quieta)
    pb = vida['parpadeo']
    parp = np.zeros(n); tt = rng.uniform(0.4, 1.5)
    while tt < dur:
        c = int(tt * FPS)
        for i, v in enumerate([0.35, 0.8, 1.0, 1.0, 0.75, 0.45, 0.2, 0.05]):
            if c + i < n:
                parp[c + i] = max(parp[c + i], v)
        tt += max(1.2, rng.gamma(pb['gamma_k'], pb['gamma_theta_s']) * 36.2 / 20)
    cur['eyeBlinkLeft'] = cur['eyeBlinkRight'] = parp

    # cejas: suben en los picos de tono (Praat), un poco antes, suaves
    import subprocess
    import imageio_ffmpeg
    import parselmouth
    wav = mp3[:-4] + '.wav'   # edge-tts da mp3; parselmouth no lo lee
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-i', mp3, '-ac', '1', wav], check=True)
    p = parselmouth.Sound(wav).to_pitch(time_step=1 / FPS, pitch_floor=120, pitch_ceiling=500)
    f0 = np.interp(t, p.xs(), np.nan_to_num(p.selected_array['frequency']))
    voz = f0 > 0
    semit = np.where(voz, 12 * np.log2(np.maximum(f0, 1) / np.median(f0[voz])), 0)
    picos = [t[i] for i in range(2, n - 2) if voz[i] and semit[i] > 2.0 and semit[i] == semit[i - 6:i + 7].max()]
    ceja = pulso(n, [c - 0.12 for c in picos], 0.28, 0.17)
    cur['browInnerUp'] = np.clip(0.05 + ceja, 0, 0.6)
    cur['browOuterUpLeft'] = cur['browOuterUpRight'] = np.clip(0.6 * ceja, 0, 0.5)

    # cabeza: OU calibrado (más suave: la media de 1KH son presentadores moviéndose) + cabeceo antes de pausa
    cab = vida['cabeza']
    guin = ou(n, 0.45 * cab['guinada']['sd_grados'], cab['guinada']['tau_s'] * 2, rng)
    cabe = ou(n, 0.45 * cab['cabeceo']['sd_grados'], cab['cabeceo']['tau_s'] * 2, rng)
    alab = ou(n, 0.45 * cab['alabeo']['sd_grados'], cab['alabeo']['tau_s'] * 2, rng) + 2.0
    g = cab['gesto_pausa']
    cabe += pulso(n, [p0 - g['adelanto_s'] for p0, _ in pausas], 2.2, g['anchura_s'])
    cabe -= 0.9 * ceja  # al subir las cejas la cabeza sube un poco
    cabeza = np.stack([guin, cabe, alab], 1)

    json.dump({'fps': FPS, 'duracion': dur, 'texto': a.texto, 'voz': a.voz,
               'palabras': [[w, round(x, 3), round(y, 3)] for w, x, y in palabras],
               'curvas': {k: [round(float(v), 3) for v in arr] for k, arr in cur.items()},
               'cabeza': [[round(float(v), 2) for v in fila] for fila in cabeza]},
              open(os.path.join(a.salida, 'curvas.json'), 'w'))
    print(f'{len(palabras)} palabras, {len(fons)} fonemas, {dur:.1f} s, {len(picos)} picos de tono, {len(pausas)} pausas')


if __name__ == '__main__':
    main()
