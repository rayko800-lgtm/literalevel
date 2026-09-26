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


GESTOS = os.path.join(RAIZ, 'investigacion', 'cara_parlante', 'gestos', 'modelo_gestos.json')


def gestos(f0, db, fps_in):
    """El modelo aprendido (entrenar_gestos.py): prosodia → cejas, sonrisa, ojos y cabeza en z.
    Devuelve {salida: curva} al ritmo de fps_in."""
    M = json.load(open(GESTOS))
    W = {k: np.array(v) for k, v in M['pesos'].items()}
    n = len(f0); g = np.arange(0, n / fps_in, 1 / M['fps'])
    t = np.arange(n) / fps_in
    f0g, dbg = np.interp(g, t, f0), np.interp(g, t, db)
    voz = f0g > 0
    st = np.where(voz, 12 * np.log2(np.maximum(f0g, 1) / np.median(f0g[voz])), 0)
    dbn = (dbg - np.median(dbg[voz])) / (dbg[voz].std() + 1e-6)
    pausa = np.zeros(len(g), bool); i = 0
    while i < len(g):
        if not voz[i]:
            j = i
            while j < len(g) and not voz[j]:
                j += 1
            if j - i >= 0.2 * M['fps']:
                pausa[i:j] = True
            i = j
        else:
            i += 1
    dist = np.full(len(g), 1e9); ult = -1e9
    for i in range(len(g)):
        ult = i if pausa[i] else ult; dist[i] = i - ult
    ult = 1e9
    for i in range(len(g) - 1, -1, -1):
        ult = i if pausa[i] else ult; dist[i] = min(dist[i], ult - i)
    x = np.stack([st / 6, voz.astype(float), dbn / 2, np.gradient(st) / 2, np.gradient(dbn),
                  np.minimum(1, dist / M['fps']), pausa.astype(float)], 0)       # [E, T]

    def conv(x, w, b, dil):
        k = w.shape[2]; pad = dil * (k - 1) // 2
        xp = np.pad(x, ((0, 0), (pad, pad)))
        return sum(np.einsum('oi,it->ot', w[:, :, j], xp[:, j * dil: j * dil + x.shape[1]]) for j in range(k)) + b[:, None]

    gelu = lambda v: 0.5 * v * (1 + np.tanh(0.7978845608 * (v + 0.044715 * v ** 3)))
    h = x
    for capa, dil in zip((0, 2, 4, 6), M['dilataciones']):
        h = gelu(conv(h, W[f'cuerpo.{capa}.weight'], W[f'cuerpo.{capa}.bias'], dil))
    y = conv(h, W['cabeza.weight'], W['cabeza.bias'], 1)            # [S, T]
    return {s: np.interp(t, g, y[k]) for k, s in enumerate(M['salidas'])}


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
    cur['cheekSquintLeft'] = cur['cheekSquintRight'] = 0.2 * son   # más, y los pómulos se ven hinchados
    cur['eyeSquintLeft'] = cur['eyeSquintRight'] = 0.15 * son

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
    # volumen en dB por fotograma (RMS de ventanas de 40 ms)
    import wave
    with wave.open(wav) as w:
        sr = w.getframerate(); pcm = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    hop = int(sr / FPS); win = int(0.04 * sr)
    db = np.array([10 * np.log10(np.mean(pcm[k * hop:k * hop + win] ** 2) + 1e-9) if k * hop + win <= len(pcm) else -90.0
                   for k in range(n)])   # tras el final del audio: silencio

    # gestos: el modelo aprendido de caras reales (1KH + Miralles) decide cejas, sonrisa y cabeza.
    # Sus predicciones salen encogidas (regresión a la media); se reescalan a su sd de validación
    # y se multiplican por EXPRESIVIDAD para que el gesto se vea sin exagerar.
    EXPRESIVIDAD = 0.8
    inf = json.load(open(os.path.join(os.path.dirname(GESTOS), 'informe.json')))['sd_prediccion_z']
    z = {k: EXPRESIVIDAD * v / inf[k] for k, v in gestos(f0, db, FPS).items()}
    cur['browInnerUp'] = np.clip(0.06 + 0.11 * z['cejas_int'], 0, 0.6)
    cur['browOuterUpLeft'] = cur['browOuterUpRight'] = np.clip(0.04 + 0.09 * z['cejas_ext'], 0, 0.5)
    cur['browDownLeft'] = cur['browDownRight'] = np.clip(-0.06 * z['cejas_int'], 0, 0.3)
    extra = np.clip(0.07 * z['sonrisa'], -0.08, 0.2)
    for k in ('mouthSmileLeft', 'mouthSmileRight'):
        cur[k] = np.clip(cur[k] + extra, 0, 0.65)
    for k in ('eyeSquintLeft', 'eyeSquintRight'):
        cur[k] = np.clip(cur[k] + 0.03 * z['entrecerrar'], 0, 0.35)

    # cabeza: la del modelo (grados de 1KH) más un poco de ruido OU para que no se repita
    cab = vida['cabeza']
    guin = 0.6 * cab['guinada']['sd_grados'] * z['guinada'] + ou(n, 1.2, 1.5, rng)
    cabe = 0.8 * cab['cabeceo']['sd_grados'] * z['cabeceo'] + ou(n, 0.8, 1.2, rng)
    alab = 0.6 * cab['alabeo']['sd_grados'] * z['alabeo'] + ou(n, 1.0, 1.6, rng) + 2.0
    picos = []
    # suavizado (gaussiana de 0,12 s): el modelo va a 25 fps y el ruido OU da tirones a 60 fps
    def suave(v, sd=0.12):
        k = np.exp(-0.5 * (np.arange(-3 * sd * FPS, 3 * sd * FPS + 1) / (sd * FPS)) ** 2); k /= k.sum()
        return np.convolve(np.pad(v, len(k) // 2, mode='edge'), k, mode='valid')[:len(v)]
    guin, cabe, alab = suave(guin), suave(cabe), suave(alab)
    for k in ('browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 'browDownLeft', 'browDownRight',
              'mouthSmileLeft', 'mouthSmileRight', 'eyeSquintLeft', 'eyeSquintRight'):
        cur[k] = np.clip(suave(cur[k], 0.08), 0, 1)
    cabeza = np.stack([guin, cabe, alab], 1)

    json.dump({'fps': FPS, 'duracion': dur, 'texto': a.texto, 'voz': a.voz,
               'palabras': [[w, round(x, 3), round(y, 3)] for w, x, y in palabras],
               'curvas': {k: [round(float(v), 3) for v in arr] for k, arr in cur.items()},
               'cabeza': [[round(float(v), 2) for v in fila] for fila in cabeza]},
              open(os.path.join(a.salida, 'curvas.json'), 'w'))
    print(f'{len(palabras)} palabras, {len(fons)} fonemas, {dur:.1f} s, gestos del modelo, {len(pausas)} pausas')


if __name__ == '__main__':
    main()
