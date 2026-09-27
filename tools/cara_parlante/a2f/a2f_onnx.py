"""Audio2Face-3D v3.0 (NVIDIA, modelo bajo NVIDIA Open Model License) sin el SDK de C++/TensorRT:
ONNX Runtime en CPU + numpy/scipy. Reproduce lo que hace el SDK (MIT), leído de su código:

- Ventanas de 1 s de audio a 16 kHz (`window`), la primera empieza 1 s antes del audio (relleno de
  ceros) y avanzan 0,5 s; cada inferencia da 60 fotogramas (60 fps) de los que valen los 30 centrales.
- Entradas: `identity` one-hot [Claire, James, Mark]; `emotion` [30, 10] (ceros = neutra);
  `input_latents` [2, 2, 1, 256], el estado GRU que se realimenta de `output_latents`;
  `noise` N(0, 1) [1, 3, 60, 88831] nuevo en cada inferencia (semilla fija aquí).
- `prediction` [1, 60, 88831] = desplazamientos respecto al neutro: piel 72006 (24002×3), lengua 16806,
  mandíbula 15, ojos 4.
- Piel: suavizado exponencial doble (0,006 s abajo, 0,001 s arriba, mezclados por una máscara sigmoide
  en Y) y vértices = neutro + desplazamiento. Lengua: neutro + 1,3 × desplazamiento.
- Blendshape solve (bvls): min ½ wᵀAw − bᵀw con 0 ≤ w ≤ 1, A = BᵀB + regularizaciones L1/L2/temporal/
  simetría escaladas por (tamaño de la caja / templateBBSize)², b = Bᵀ(v − neutro) + T·s·w_anterior,
  sobre los 4262 vértices frontales y las poses activas; luego multiplicadores y desfases del config.

Salida: JSON con fps, nombres ARKit (52; mouthClose incluye la apertura de mandíbula) y pesos por
fotograma, más 16 de lengua; y un CSV. Uso:
  python a2f_onnx.py --wav frase.wav --salida frase_a2f.json [--identidad Claire] [--fps 25] [--semilla 0]
Necesita en la carpeta: network.onnx, network_info.json, bs_skin_<id>.npz, bs_skin_config_<id>.json,
bs_tongue_<id>.npz, bs_tongue_config_<id>.json, model_data_<id>.npz, model_config_<id>.json
(https://huggingface.co/nvidia/Audio2Face-3D-v3.0).
"""
import argparse
import csv
import json
import os
import sys
import time

import numpy as np
import scipy.optimize
import scipy.signal
import soundfile as sf

AQUI = os.path.dirname(os.path.abspath(__file__))


def cargar_audio(ruta):
    x, sr = sf.read(ruta, dtype='float32', always_2d=True)
    x = x.mean(1)
    if sr != 16000:
        from math import gcd
        g = gcd(16000, sr)
        x = scipy.signal.resample_poly(x, 16000 // g, sr // g).astype(np.float32)
    return x


class Suavizador:
    """Interpolator del SDK: grado 2, alpha = 1 − 0,5^(dt/suavizado)."""

    def __init__(self, suavizado, dt):
        self.alpha = (1 - 0.5 ** (dt / suavizado)) if suavizado > 0 else None
        self.d = None

    def __call__(self, raw):
        if self.d is None:
            self.d = [raw.copy(), raw.copy(), raw.copy()]
        self.d[0] = raw
        for i in (1, 2):
            if self.alpha is None:
                self.d[i] = self.d[i - 1].copy()
            else:
                self.d[i] = self.d[i] + (self.d[i - 1] - self.d[i]) * self.alpha
        return self.d[2]


class SolveBlendshapes:
    def __init__(self, npz, config, mascara=None):
        d = np.load(npz)
        nombres = d['poseNames'].astype(str)
        assert nombres[0] == 'neutral'
        self.nombres = list(nombres[1:])
        neutro = d['neutral'].reshape(-1).astype(np.float64)
        deltas = np.stack([d[n].reshape(-1) for n in self.nombres], 1).astype(np.float64)   # [3V, P]
        p = json.load(open(config))['blendshape_params']
        self.activos = np.array(p['bsSolveActivePoses'], bool)
        self.mult = np.array(p['bsWeightMultipliers'], np.float64)
        self.desf = np.array(p['bsWeightOffsets'], np.float64)
        self.cancel = self._pares(p['bsSolveCancelPoses'])
        # escala de las regularizaciones: (diagonal de la caja del neutro / templateBBSize)²
        v = neutro.reshape(-1, 3)
        s = (np.linalg.norm(v.max(0) - v.min(0)) / p['templateBBSize']) ** 2
        self.s = s
        idx = np.arange(len(neutro)) if mascara is None else (3 * np.asarray(mascara)[:, None] + np.arange(3)).reshape(-1)
        self.idx = idx
        self.B = deltas[idx][:, self.activos]
        self.neutro_m = neutro[idx]
        n = self.B.shape[1]
        sim = self._pares(p['bsSolveSymmetryPoses'])
        S = np.zeros((len(sim), n))
        for k, (i, j) in enumerate(sim):
            S[k, i] = 1; S[k, j] = -1
        L1, L2, T, Sy = p['strengthL1regularization'], p['strengthL2regularization'], p['strengthTemporalSmoothing'], p['strengthSymmetry']
        self.T = T
        self.A = (self.B.T @ self.B + L1 * L1 * 0.25 * s * np.ones((n, n)) + L2 * 10 * s * np.eye(n)
                  + T * 100 * s * np.eye(n) + Sy * 10 * s * S.T @ S)
        self.L = np.linalg.cholesky(self.A)                                   # A = L Lᵀ
        self.w_prev = np.zeros(n)

    def _pares(self, arr):
        """Índices (entre las poses activas) de las parejas con el mismo id ≠ -1."""
        act = [i for i, a in enumerate(self.activos) if a]
        grupos = {}
        for k, i in enumerate(act):
            if arr[i] != -1:
                grupos.setdefault(arr[i], []).append(k)
        return [tuple(g) for g in grupos.values() if len(g) == 2]

    def _bvls(self, b, u):
        # ½ wᵀAw − bᵀw = ½‖Lᵀw − L⁻¹b‖² + const
        c = np.linalg.solve(self.L, b)
        r = scipy.optimize.lsq_linear(self.L.T, c, bounds=(np.zeros(len(b)), u), method='bvls', tol=1e-8)
        return r.x

    def __call__(self, vertices):
        b = self.B.T @ (vertices[self.idx] - self.neutro_m) + self.T * self.s * self.w_prev
        u = np.ones(len(b))
        x = self._bvls(b, u)
        if self.cancel:
            for i, j in self.cancel:
                u[j if x[i] >= x[j] else i] = 1e-10
            x = self._bvls(b, u)
        self.w_prev = x
        w = np.zeros(len(self.nombres)); w[self.activos] = x
        return w * self.mult + self.desf


def inferir(x, red, info, identidad, semilla, emocion=None, avisar=print):
    import onnxruntime as ort
    p = info['params']; a = info['audio_params']
    buf, sr = a['buffer_len'], a['samplerate']
    L, C, F = p['num_frames_left_truncate'], p['num_frames_center'], p['num_frames_left_truncate'] + p['num_frames_center'] + p['num_frames_right_truncate']
    zancada = buf * C // F                        # 8000 muestras por inferencia
    desf_obj = buf * L // F                       # 4000: primer fotograma bueno dentro de la ventana
    periodo = buf / F                             # 266,67 muestras = 1/60 s
    dim = p['skin_size'] + p['tongue_size'] + p['jaw_size'] + p['eyes_size']
    sess = ort.InferenceSession(red, providers=['CPUExecutionProvider'])
    ent = {i.name: i.shape for i in sess.get_inputs()}
    avisar('entradas ONNX:', ent, '| salidas:', [(o.name, o.shape) for o in sess.get_outputs()])
    ident = np.zeros((1, len(p['identities'])), np.float32); ident[0, p['identities'].index(identidad)] = 1
    emo = np.zeros((1, C, len(p['emotions'])), np.float32) if emocion is None else np.tile(np.asarray(emocion, np.float32), (1, C, 1))
    latentes = np.zeros((p['num_diffusion_steps'], p['num_gru_layers'], 1, p['gru_latent_dim']), np.float32)
    rng = np.random.default_rng(semilla)
    inicio = -a['padding_left']
    n = len(x)
    fotogramas, tiempos = [], []
    t0 = time.time(); k = 0
    while inicio + desf_obj < n:
        ventana = np.zeros(buf, np.float32)
        i0, i1 = max(inicio, 0), min(inicio + buf, n)
        if i1 > i0:
            ventana[i0 - inicio:i1 - inicio] = x[i0:i1]
        ruido = rng.standard_normal((1, p['num_diffusion_steps'] + 1, F, dim), dtype=np.float32)
        pred, latentes = sess.run(['prediction', 'output_latents'],
                                  {'window': ventana[None], 'identity': ident, 'emotion': emo, 'input_latents': latentes, 'noise': ruido})
        for f in range(C):
            t = inicio + desf_obj + f * periodo
            if t < 0:
                continue
            if t >= n:
                break
            fotogramas.append(pred[0, L + f].astype(np.float64)); tiempos.append(t / sr)
        inicio += zancada; k += 1
    avisar(f'{k} inferencias, {len(fotogramas)} fotogramas a {F * sr / buf:.0f} fps, {time.time() - t0:.1f} s')
    return np.array(fotogramas), np.array(tiempos)


def piel_y_lengua(pred, info, datos, cfg):
    p = info['params']; c = cfg['config']
    S, T = p['skin_size'], p['tongue_size']
    dt = info['audio_params']['buffer_len'] / (p['num_frames_left_truncate'] + p['num_frames_center'] + p['num_frames_right_truncate']) / info['audio_params']['samplerate']
    neutro = datos['neutral_skin'].reshape(-1).astype(np.float64)
    ojo, labio = datos['eye_close_pose_delta'].reshape(-1), datos['lip_open_pose_delta'].reshape(-1)
    y = neutro.reshape(-1, 3)[:, 1]
    yn = (y - y.min()) / (y.max() - y.min())
    mascara = np.repeat(1 / (1 + np.exp(-(c['face_mask_level'] - yn) / c['face_mask_softness'])), 3)
    abajo, arriba = Suavizador(c['lower_face_smoothing'], dt), Suavizador(c['upper_face_smoothing'], dt)
    blink = c.get('blink_offset', 0.0)
    piel = np.empty((len(pred), S)); lengua = np.empty((len(pred), T))
    nl = datos['neutral_tongue'].reshape(-1).astype(np.float64)
    for k, fr in enumerate(pred):
        pose = c['skin_strength'] * fr[:S] + ojo * (-c['eyelid_open_offset'] + blink * c['blink_strength']) + labio * c['lip_open_offset']
        lo, hi = abajo(pose), arriba(pose)
        piel[k] = neutro + hi * c['upper_face_strength'] * (1 - mascara) + lo * c['lower_face_strength'] * mascara
        d = fr[S:S + T] * c['tongue_strength']
        d[1::3] += c['tongue_height_offset']; d[2::3] += c['tongue_depth_offset']
        lengua[k] = nl + d
    return piel, lengua


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wav', required=True)
    ap.add_argument('--salida', required=True, help='.json (y .csv al lado)')
    ap.add_argument('--identidad', default='Claire', choices=['Claire', 'James', 'Mark'])
    ap.add_argument('--semilla', type=int, default=0)
    ap.add_argument('--fps', type=float, default=0, help='remuestrear las curvas a esta frecuencia (0 = dejar 60)')
    ap.add_argument('--carpeta', default=AQUI)
    ap.add_argument('--sin_lengua', action='store_true')
    a = ap.parse_args()
    C = a.carpeta
    info = json.load(open(os.path.join(C, 'network_info.json')))
    cfg = json.load(open(os.path.join(C, f'model_config_{a.identidad}.json')))
    datos = np.load(os.path.join(C, f'model_data_{a.identidad}.npz'))
    x = cargar_audio(a.wav)
    print(f'audio: {len(x) / 16000:.2f} s')
    pred, t = inferir(x, os.path.join(C, 'network.onnx'), info, a.identidad, a.semilla)
    piel, lengua = piel_y_lengua(pred, info, datos, cfg)
    piel_npz = np.load(os.path.join(C, f'bs_skin_{a.identidad}.npz'))
    sk = SolveBlendshapes(os.path.join(C, f'bs_skin_{a.identidad}.npz'), os.path.join(C, f'bs_skin_config_{a.identidad}.json'), piel_npz['frontalMask'])
    t0 = time.time()
    pesos = np.array([sk(v) for v in piel])
    print(f'blendshape solve piel: {time.time() - t0:.1f} s; residuo relativo medio '
          f'{np.mean([np.linalg.norm(sk.B @ w[sk.activos] - (v[sk.idx] - sk.neutro_m)) / (np.linalg.norm(v[sk.idx] - sk.neutro_m) + 1e-9) for w, v in zip(pesos, piel)]):.3f}')
    salida = {'fps': 60.0, 'tiempos': t.tolist(), 'nombres': sk.nombres, 'pesos': pesos.tolist(),
              'identidad': a.identidad, 'semilla': a.semilla, 'wav': os.path.basename(a.wav), 'modelo': 'Audio2Face-3D v3.0 (ONNX)'}
    if not a.sin_lengua:
        lg = SolveBlendshapes(os.path.join(C, f'bs_tongue_{a.identidad}.npz'), os.path.join(C, f'bs_tongue_config_{a.identidad}.json'))
        salida['lengua_nombres'] = lg.nombres; salida['lengua_pesos'] = np.array([lg(v) for v in lengua]).tolist()
    if a.fps:
        tn = np.arange(0, t[-1], 1 / a.fps)
        for k in ('pesos', 'lengua_pesos'):
            if k in salida:
                w = np.array(salida[k]); salida[k] = np.stack([np.interp(tn, t, w[:, j]) for j in range(w.shape[1])], 1).tolist()
        salida['fps'] = a.fps; salida['tiempos'] = tn.tolist()
    json.dump(salida, open(a.salida, 'w', encoding='utf-8'))
    with open(os.path.splitext(a.salida)[0] + '.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['t'] + salida['nombres'] + salida.get('lengua_nombres', []))
        for i, ti in enumerate(salida['tiempos']):
            w.writerow([f'{ti:.4f}'] + [f'{v:.4f}' for v in salida['pesos'][i]] + [f'{v:.4f}' for v in salida.get('lengua_pesos', [[]] * (i + 1))[i]])
    P = np.array(salida['pesos']); nm = salida['nombres']
    top = np.argsort(-P.max(0))[:10]
    print('máximos:', ', '.join(f'{nm[j]} {P[:, j].max():.2f}' for j in top))
    print('escrito', a.salida)


if __name__ == '__main__':
    main()
