"""Lo que comparten los guiones de v3: dónde están los datos, cómo se emparejan y qué columnas hay.

- Etiquetas SMIRK (etiquetar_smirk.py): rasgos() apila expresión (50), mandíbula (3), párpados (2)
  y pose en grados (3) → [T, 58] en el orden de ENTRADAS_SMIRK.
- Medidas MediaPipe (medir_expresion.py): 52 blendshapes + pose (3) → [T, 55]; COLUMNAS_ARKIT.
- GRUPOS: qué columnas forman boca, sonrisa, ojos, cejas y cabeza (los mismos que la red de fusión).
- pares_*(): emparejan archivos por nombre (<nombre>.npz en cada carpeta, recursivo).
"""
import glob
import os

import numpy as np

GRUPOS = {
    'boca': ['jawOpen', 'mouthClose', 'mouthFunnel', 'mouthPucker', 'mouthPressLeft', 'mouthPressRight',
             'mouthRollLower', 'mouthRollUpper', 'mouthLowerDownLeft', 'mouthLowerDownRight',
             'mouthUpperUpLeft', 'mouthUpperUpRight', 'mouthStretchLeft', 'mouthStretchRight'],
    'sonrisa': ['mouthSmileLeft', 'mouthSmileRight', 'cheekSquintLeft', 'cheekSquintRight'],
    'ojos': ['eyeBlinkLeft', 'eyeBlinkRight', 'eyeSquintLeft', 'eyeSquintRight', 'eyeWideLeft', 'eyeWideRight'],
    'cejas': ['browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 'browDownLeft', 'browDownRight'],
    'cabeza': ['cabeza_guinada', 'cabeza_cabeceo', 'cabeza_alabeo'],
}
# lo que mueve la parte generativa (no verbal); la boca es lo de GRUPOS['boca']
NO_VERBAL = GRUPOS['sonrisa'] + GRUPOS['ojos'] + GRUPOS['cejas'] + GRUPOS['cabeza']
ENTRADAS_SMIRK = [f'exp{i:02d}' for i in range(50)] + ['mand_abrir', 'mand_lado', 'mand_giro', 'parpado_izq', 'parpado_der',
                                                        'pose_guinada', 'pose_cabeceo', 'pose_alabeo']


def mapa_archivos(d, ext='npz'):
    return {os.path.splitext(os.path.basename(f))[0]: f for f in glob.glob(os.path.join(d, '**', '*.' + ext), recursive=True)}


def rasgos(s):
    """[T, 58] float32 a partir de un npz de etiquetar_smirk.py (o de un dict con las mismas claves)."""
    return np.concatenate([s['expresion'], s['mandibula'], s['parpados'], s['pose']], 1).astype(np.float32)


def objetivo_mediapipe(m):
    """[T, 55]: 52 blendshapes + 3 ángulos, y sus nombres (COLUMNAS_ARKIT)."""
    y = np.concatenate([m['bs'].astype(np.float32), np.nan_to_num(m['pose'].astype(np.float32))], 1)
    return y, list(m['bs_nombres']) + GRUPOS['cabeza']


def columnas_mediapipe(dir_medidas):
    """Nombres de las 55 columnas de las medidas MediaPipe (52 blendshapes + cabeza)."""
    m = np.load(next(iter(mapa_archivos(dir_medidas).values())))
    return list(m['bs_nombres']) + GRUPOS['cabeza']


def pares_smirk(dir_smirk, dir_medidas):
    s, m = mapa_archivos(dir_smirk), mapa_archivos(dir_medidas)
    return [(n, s[n], m[n]) for n in sorted(m) if n in s]


def cargar_par(fs, fm, min_ok=0.5):
    """X [T,58], Y [T,55], ok (cara en los dos), columnas; None si el clip es malo."""
    s, m = np.load(fs), np.load(fm)
    k = min(len(s['t']), len(m['t']))
    ok = s['ok'][:k].astype(bool) & m['ok'][:k].astype(bool)
    if ok.mean() < min_ok or ok.sum() < 50:
        return None
    y, cols = objetivo_mediapipe(m)
    return rasgos(s)[:k], y[:k], ok, cols


def apilar(pares, min_ok=0.5):
    """Todos los fotogramas válidos de los pares: X, Y, id de clip por fotograma, columnas, nombres."""
    Xs, Ys, ids, cols, nombres = [], [], [], None, []
    for n, fs, fm in pares:
        r = cargar_par(fs, fm, min_ok)
        if r is None:
            continue
        x, y, ok, cols = r
        Xs.append(x[ok]); Ys.append(y[ok]); ids.append(np.full(ok.sum(), len(nombres))); nombres.append(n)
    return np.concatenate(Xs), np.concatenate(Ys), np.concatenate(ids), cols, nombres


# ---------------------------------------------------------------- datos de entrenamiento v3
L = 250            # ventana (fotogramas a 25 fps = 10 s)
PASO = 125         # solape de media ventana
N_FON = 35         # 34 fonemas del modelo articulatorio + silencio (índice 34)


def es_val(indice, nombre, ruta):
    """Mismo reparto que la red de fusión: la carpeta val, 1 de cada 8 vídeos de YouTube (por
    hash del vídeo, con sus trozos) y 1 de cada 8 de Obama/Casa Blanca (por índice)."""
    import zlib
    r = ruta.replace('/', os.sep)
    if os.sep + 'val' + os.sep in r:
        return True
    if any(k in r for k in ('obama', 'casa_blanca', 'miralles')):
        return indice % 8 == 0
    return zlib.crc32(nombre.rsplit('_', 1)[0].encode()) % 8 == 0


def pares_entrenamiento(dir_voz, dir_art, dir_smirk):
    """(nombre, voz.npz, art.npz, smirk.npz) de los clips que tienen las tres cosas."""
    v, a, s = mapa_archivos(dir_voz), mapa_archivos(dir_art), mapa_archivos(dir_smirk)
    return [(n, v[n], a[n], s[n]) for n in sorted(s) if n in v and n in a]


def cargar_clip(fv, fa, fs, mapa, capas_usar=None, min_ok=0.6):
    """Un clip para entrenar: voz [T,K,1024] f16, art [T,13] f16, fon [T] i64, objetivo [T,55] f32
    (ARKit vía el mapa SMIRK→ARKit, menos la media del clip), ok [T] bool, duración (s). None si es malo.
    Si `fs` es un npz de medidas MediaPipe (tiene 'bs'), el objetivo son sus blendshapes y el mapa no se usa."""
    s, v, a = np.load(fs), np.load(fv), np.load(fa)
    ok = s['ok'].astype(bool)
    k = min(len(ok), len(v['t']), len(a['t']))
    ok = ok[:k]
    if ok.mean() < min_ok or k < 75:
        return None
    if 'bs' in s.files:                 # etiquetas MediaPipe directas (plan B, sin SMIRK ni mapa)
        y = objetivo_mediapipe(s)[0][:k]
    else:
        import mapa_arkit
        y = mapa_arkit.aplicar(mapa, rasgos(s)[:k])
    y = y - y[ok].mean(0)
    y[~ok] = 0
    voz = v['voz'][:k]
    if capas_usar is not None:
        disponibles = list(v['capas'])
        voz = voz[:, [disponibles.index(c) for c in capas_usar]]
    fon = a['fon'][:k].astype(np.int64)
    fon[fon < 0] = N_FON - 1
    return dict(voz=voz.astype(np.float16), art=a['art'][:k].astype(np.float16), fon=fon, y=y.astype(np.float32), ok=ok,
                dur=float(s['t'][k - 1] - s['t'][0]))


class Conjunto:
    """Los datos de entrenamiento apilados en ventanas de L fotogramas, listos para indexar.

    La voz (la parte gorda: ~36 GB con 7 capas en 28 h) va a un memmap en `dir_cache` (disco local
    en Colab; el sistema lo mantiene en la caché de RAM si cabe) y, si se pide y cabe, a la GPU.
    Lo demás (articulación, fonema, objetivo, máscara) va a la RAM como tensores.
    Los clips de validación se guardan enteros en `val` (lista de dicts de cargar_clip)."""

    def __init__(self, pares, mapa, dir_cache, capas_usar=None, max_horas=0.0, log=print):
        import torch
        os.makedirs(dir_cache, exist_ok=True)
        elegidos, self.val, horas = [], [], 0.0
        for i, (n, fv, fa, fs) in enumerate(pares):
            if es_val(i, n, fs):
                c = cargar_clip(fv, fa, fs, mapa, capas_usar)
                if c is not None:
                    c['nombre'] = n
                    self.val.append(c)
            else:
                elegidos.append((n, fv, fa, fs))
        if not self.val and len(elegidos) > 1:            # pruebas con muy pocos clips: el último hace de validación
            n, fv, fa, fs = elegidos.pop()
            c = cargar_clip(fv, fa, fs, mapa, capas_usar)
            if c is not None:
                c['nombre'] = n; self.val.append(c)
        # tamaño total para el memmap: solo hace falta la longitud de cada clip
        largos = []
        for n, fv, fa, fs in elegidos:
            s = np.load(fs)
            largos.append(min(len(s['t']), len(np.load(fv)['t'])))
        total = sum(max(lg, L) for lg in largos)
        k0 = np.load(elegidos[0][1])['voz'].shape[1] if capas_usar is None else len(capas_usar)
        ruta = os.path.join(dir_cache, f'voz_{total}_{k0}.npy')
        nuevo = not os.path.exists(ruta + '.ok')          # la marca .ok se escribe al acabar de llenarlo
        self.voz = np.lib.format.open_memmap(ruta, mode='w+' if nuevo else 'r', dtype=np.float16, shape=(total, k0, 1024))
        Xa = np.zeros((total, 13), np.float16); Xf = np.full(total, N_FON - 1, np.int64)
        Ys, Ms, inicios, pos = [], [], [], 0
        for (n, fv, fa, fs), lg in zip(elegidos, largos):
            c = cargar_clip(fv, fa, fs, mapa, capas_usar)
            if c is None:
                continue
            k = len(c['ok'])
            if nuevo:
                self.voz[pos:pos + k] = c['voz']
            Xa[pos:pos + k], Xf[pos:pos + k] = c['art'], c['fon']
            pad = max(0, L - k)
            Ys.append(np.pad(c['y'], ((0, pad), (0, 0)))); Ms.append(np.pad(c['ok'], (0, pad)))
            inicios += [pos + j for j in range(0, max(k, L) - L + 1, PASO)]
            pos += max(k, L); horas += c['dur'] / 3600
            if max_horas and horas >= max_horas:
                break
        if nuevo:
            self.voz.flush()
            open(ruta + '.ok', 'w').write(str(pos))
        self.n = pos
        self.y = np.concatenate(Ys)[:pos]; self.m = np.concatenate(Ms)[:pos]
        self.sd = self.y[self.m].std(0) + 1e-3
        self.art, self.fon, self.inicios, self.horas = Xa[:pos], Xf[:pos], np.array(inicios), horas
        log(f'entrenamiento: {len(inicios)} ventanas, {horas:.1f} h, {len(self.val)} clips de validación; voz en {ruta}')

    def a_torch(self, dispositivo, voz_en_gpu=False):
        """Tensores para indexar por lotes. La voz se queda en el memmap salvo que se pida (y quepa) en la GPU."""
        import torch
        self.art_t = torch.from_numpy(self.art.astype(np.float16))
        self.fon_t = torch.from_numpy(self.fon)
        self.y_t = torch.from_numpy((self.y / self.sd).astype(np.float32))
        self.m_t = torch.from_numpy(self.m)
        self.voz_t = None
        if voz_en_gpu:
            try:
                self.voz_t = torch.from_numpy(np.ascontiguousarray(self.voz)).to(dispositivo)
            except (RuntimeError, MemoryError):
                self.voz_t = None
        return self

    def lote(self, idx, dispositivo):
        """idx: tensor [B] de inicios de ventana → voz [B,L,K,1024] f32, art, fon, y, m en `dispositivo`."""
        import torch
        ii = idx[:, None] + torch.arange(L)
        if self.voz_t is not None:
            voz = self.voz_t[ii.to(self.voz_t.device)].float()
        else:
            voz = torch.from_numpy(np.stack([self.voz[i:i + L] for i in idx.tolist()])).to(dispositivo).float()
        return (voz, self.art_t[ii].to(dispositivo).float(), self.fon_t[ii].to(dispositivo),
                self.y_t[ii].to(dispositivo), self.m_t[ii].to(dispositivo).unsqueeze(-1).float())
