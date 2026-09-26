"""Alineación forzada palabra a palabra: dónde suena de verdad cada palabra del texto en el audio.

Las marcas de palabra de edge-tts no casan con el mp3 (relleno variable al principio) y la
correlación mandíbula-energía fallaba (el 26 sep dejó las palabras ~0,2 s tarde: la boca se
abría después del «Hi»). Aquí se usa un reconocedor de letras (wav2vec2-base-960h, CTC) y se
fuerza el camino de Viterbi por el texto conocido: cada letra cae en su trozo de audio.

alinear(texto_palabras, wav) -> [(palabra, t0, t1)] en segundos.
"""
import re

import numpy as np

_modelo = None


def _cargar():
    global _modelo
    if _modelo is None:
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
        nombre = 'facebook/wav2vec2-base-960h'
        _modelo = (Wav2Vec2Processor.from_pretrained(nombre), Wav2Vec2ForCTC.from_pretrained(nombre).eval())
    return _modelo


def alinear(palabras, x16):
    """palabras: lista de str; x16: audio mono float a 16 kHz."""
    import torch
    proc, red = _cargar()
    with torch.no_grad():
        logp = torch.log_softmax(red(torch.tensor(x16, dtype=torch.float32)[None]).logits[0], -1).numpy()
    voc = proc.tokenizer.get_vocab()
    blank, sep = voc['<pad>'], voc['|']
    limpias = [re.sub(r"[^A-Z']", '', w.upper()) for w in palabras]
    fichas, dueno = [], []            # fichas del camino (letras y separadores) y a qué palabra pertenecen
    for k, w in enumerate(limpias):
        for ch in w:
            if ch in voc:
                fichas.append(voc[ch]); dueno.append(k)
        if k < len(limpias) - 1:
            fichas.append(sep); dueno.append(-1)
    T, S = logp.shape[0], 2 * len(fichas) + 1      # CTC con blancos intercalados
    ext = [blank if s % 2 == 0 else fichas[s // 2] for s in range(S)]
    NEG = -1e9
    D = np.full((T, S), NEG); P = np.zeros((T, S), np.int8)
    D[0, 0] = logp[0, ext[0]]; D[0, 1] = logp[0, ext[1]]
    for t in range(1, T):
        for s in range(S):
            opciones = [D[t - 1, s], D[t - 1, s - 1] if s > 0 else NEG,
                        D[t - 1, s - 2] if s > 1 and ext[s] != blank and ext[s] != ext[s - 2] else NEG]
            b = int(np.argmax(opciones)); D[t, s] = opciones[b] + logp[t, ext[s]]; P[t, s] = b
    s = S - 1 if D[-1, S - 1] >= D[-1, S - 2] else S - 2
    estado = np.zeros(T, int)
    for t in range(T - 1, -1, -1):
        estado[t] = s; s -= int(P[t, s])
    dt = len(x16) / 16000 / T                      # ~20 ms por paso
    ini, fin = {}, {}
    for t, s in enumerate(estado):
        if s % 2 == 1 and dueno[s // 2] >= 0:
            k = dueno[s // 2]; ini.setdefault(k, t); fin[k] = t
    out = []
    for k, w in enumerate(palabras):
        if k in ini:
            out.append((w, round(ini[k] * dt, 3), round((fin[k] + 1) * dt, 3)))
    return out
