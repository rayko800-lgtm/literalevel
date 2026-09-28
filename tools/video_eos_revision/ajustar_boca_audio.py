"""Cierra el articulador Blender en silencios sin sustituir sus fonemas."""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d

MOUTH = {'jawOpen','mouthPucker','mouthFunnel','mouthRollLower','mouthPressLeft',
         'mouthPressRight','mouthLowerDownLeft','mouthLowerDownRight',
         'mouthUpperUpLeft','mouthUpperUpRight'}

def adjust(data, wav_path):
    fps=data['fps']
    with wave.open(str(wav_path),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth())==(1,2)
        samples=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float64)
        rate=w.getframerate()
    n=len(data['curvas']['jawOpen'])
    energy=np.empty(n)
    for i in range(n):
        a=round(i*rate/fps);b=min(len(samples),round((i+1)*rate/fps))
        energy[i]=np.sqrt(np.mean(samples[a:b]**2)) if b>a else 0
    # Suaviza el RMS sin expandirlo a los silencios vecinos.
    present=gaussian_filter1d(energy,sigma=1.8)
    gate=np.clip((present-100)/950,0,1)
    gate=gate*gate*(3-2*gate)
    gate=np.clip(gate,0,1)
    original=np.asarray(data['curvas']['jawOpen'],dtype=float)
    mouth_open=np.clip(original*(0.03+1.12*gate),0,0.40)
    for key in MOUTH:
        if key in data['curvas']:
            vals=np.asarray(data['curvas'][key],dtype=float)
            if key=='jawOpen': vals=mouth_open
            else: vals=vals*(0.04+0.96*gate)
            data['curvas'][key]=np.round(vals,5).tolist()
    data['sincronia_audio']={'metodo':'gate_rms_blender','umbral':100,'rango':950,'ganancia_mandibula':1.12,
                              'sigma':1.8}
    def corr(a,b): return float(np.corrcoef(a,np.log1p(b))[0,1])
    metrics={'corr_antes':round(corr(original,energy),3),
             'corr_despues':round(corr(mouth_open,energy),3),
             'mandibula_silencio_antes':round(float(np.mean(original[energy<100])),3),
             'mandibula_silencio_despues':round(float(np.mean(mouth_open[energy<100])),3)}
    return data,metrics

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    src=root/'visor/curvas.json'
    data=json.loads(src.read_text(encoding='utf-8'))
    out,metrics=adjust(data,root/'audio_continuacion.wav')
    (root/'curvas_gate_piloto.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
    print(metrics)
