"""Da más vida a la cara de una secuencia de Speech2Face: mirada a cámara con microsacadas,
más parpadeos y una sonrisa tierna (base suave y más en las pausas).

Speech2Face deja la mirada sin claves (ojos fijos al frente de la cabeza), parpadea poco
y, aun con ánimo «Happiness», sonríe muy poco. Sobre una COPIA de la secuencia
(<secuencia>_vida) se retocan los controles del rig facial:
  CTRL_L/R_eye.X/Y           mirada (0 = al frente); saltos pequeños y vuelta a la cámara
  CTRL_L/R_eye_blink         parpadeo: se añaden parpadeos hasta ~18 por minuto
  CTRL_L/R_mouth_cornerPull  sonrisa;  CTRL_L/R_eye_cheekRaise acompaña (pómulos)
Lee eos_vida.json: {"secuencia": "/Game/Eos/hola/LS_hola", "curvas": "D:/.../hola/curvas.json",
"sonrisa_base": 0.12, "sonrisa_pausa": 0.25, "parpadeos_min": 18, "semilla": 5}
Escribe eos_vida.ok con la ruta de la copia.
"""
import json
import random

import unreal

D = 'D:/literalevel_cara/ue/'
cfg = json.load(open(D + 'eos_vida.json'))
rng = random.Random(cfg.get('semilla', 5))
orig = cfg['secuencia']
# Las copias recién duplicadas no exponen todos los canales del rig facial por Python (solo
# algunos), así que se retoca la ORIGINAL, guardando antes una copia intacta (<orig>_base)
# para poder volver atrás. Un marcador evita aplicar la vida dos veces sobre la misma.
if not unreal.EditorAssetLibrary.does_asset_exist(orig + '_base'):
    unreal.EditorAssetLibrary.duplicate_asset(orig, orig + '_base')
marca = D + 'vida_' + orig.replace('/', '_') + '.hecho'
import os
if os.path.exists(marca):
    raise RuntimeError('la vida ya se aplicó a ' + orig + ' (borrar ' + marca + ' tras restaurar de _base)')
copia = orig
seq = unreal.load_asset(orig)
datos = json.load(open(cfg['curvas']))
FPS = 30
r = seq.get_playback_range()
n = r.exclusive_end - r.inclusive_start

palabras = datos['palabras']
pausas = [(a[2], b[1]) for a, b in zip(palabras, palabras[1:]) if b[1] - a[2] > 0.18]
pausas.append((palabras[-1][2], n / FPS))


def canales():
    for b in seq.get_bindings():
        for t in b.get_tracks():
            if isinstance(t, unreal.MovieSceneControlRigParameterTrack):
                for s in t.get_sections():
                    for c in s.get_all_channels():
                        yield str(c.channel_name), c


C = {nombre: c for nombre, c in canales()}
if 'CTRL_L_eye_blink' not in C:
    raise RuntimeError('el rig facial aún no está cargado; volver a ejecutar')


def valores(c):
    """Valor por fotograma (interpolación lineal entre claves; 0 sin claves)."""
    ks = sorted(((k.get_time().frame_number.value, k.get_value()) for k in c.get_keys()))
    v = [0.0] * n
    if not ks:
        return v
    j = 0
    for f in range(n):
        while j + 1 < len(ks) and ks[j + 1][0] <= f:
            j += 1
        f0, v0 = ks[j]
        if j + 1 < len(ks) and f > f0:
            f1, v1 = ks[j + 1]
            v[f] = v0 + (v1 - v0) * (f - f0) / (f1 - f0)
        else:
            v[f] = v0 if f >= f0 else ks[0][1]
    return v


def escribir(c, v):
    for k in list(c.get_keys()):
        c.remove_key(k)
    for f, x in enumerate(v):
        c.add_key(unreal.FrameNumber(f), float(x))


def pulso(t, c, ancho):
    import math
    return math.exp(-0.5 * ((t - c) / ancho) ** 2)


t = [f / FPS for f in range(n)]

# sonrisa: base tierna + más en las pausas y al final
extra = [cfg.get('sonrisa_base', 0.12) + cfg.get('sonrisa_pausa', 0.25) *
         max(pulso(x, (p0 + p1) / 2, 0.4) for p0, p1 in pausas) for x in t]
for lado in 'LR':
    for nombre, k in ((f'CTRL_{lado}_mouth_cornerPull', 1.0), (f'CTRL_{lado}_eye_cheekRaise', 0.6)):
        if nombre in C:
            v = valores(C[nombre])
            escribir(C[nombre], [min(1.0, a + k * e) for a, e in zip(v, extra)])

# parpadeos: los que ya hay más los que falten hasta ~parpadeos_min por minuto
perfil = [0.35, 0.8, 1.0, 1.0, 0.75, 0.45, 0.2, 0.05]
bl = valores(C['CTRL_L_eye_blink'])
existentes = [f for f in range(1, n - 1) if bl[f] > 0.6 and bl[f] >= bl[f - 1] and bl[f] >= bl[f + 1]]
objetivo = int(cfg.get('parpadeos_min', 18) * n / FPS / 60)
nuevos, tt = [], rng.uniform(0.6, 1.4)
while tt < n / FPS - 0.3 and len(existentes) + len(nuevos) < objetivo:
    f = int(tt * FPS)
    if all(abs(f - e) > 20 for e in existentes + nuevos):
        nuevos.append(f)
    tt += rng.uniform(2.2, 4.2)
for lado in 'LR':
    nombre = f'CTRL_{lado}_eye_blink'
    v = valores(C[nombre])
    for f in nuevos:
        for i, p in enumerate(perfil):
            if f + i < n:
                v[f + i] = max(v[f + i], p)
    escribir(C[nombre], v)

# mirada: a cámara (0), con microsacadas pequeñas y alguna mirada breve a un lado en las pausas
mx, my = [0.0] * n, [0.0] * n
f = 0
while f < n:
    dur = int(rng.uniform(0.5, 1.6) * FPS)
    ox, oy = rng.gauss(0, 0.035), rng.gauss(0, 0.025)
    for i in range(f, min(n, f + dur)):
        mx[i], my[i] = ox, oy
    f += dur
for p0, p1 in pausas[:-1]:
    if p1 - p0 > 0.3 and rng.random() < 0.6:
        lado = rng.choice((-1, 1))
        for i in range(int(p0 * FPS), min(n, int((p0 + 0.35) * FPS))):
            mx[i] = 0.18 * lado
            my[i] = -0.05
for lado in 'LR':
    for nombre, v in ((f'CTRL_{lado}_eye.X', mx), (f'CTRL_{lado}_eye.Y', my)):
        if nombre in C:
            escribir(C[nombre], v)

unreal.EditorAssetLibrary.save_loaded_asset(seq)
open(marca, 'w').write('ok')
open(D + 'eos_vida.ok', 'w').write(json.dumps({'copia': copia, 'parpadeos_existentes': len(existentes),
                                              'parpadeos_nuevos': len(nuevos)}))
