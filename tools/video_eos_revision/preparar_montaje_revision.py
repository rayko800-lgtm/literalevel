"""Une audio y curvas por escena y crea tiempos/subtítulos para el render 720p."""
from __future__ import annotations
import difflib
import json
import math
import re
import unicodedata
import wave
from pathlib import Path

HERE=Path(__file__).resolve().parent
FPS=60
RATE=24000
INITIAL=0.45
SCENES=json.loads((HERE/'guion_revision.json').read_text(encoding='utf-8-sig'))['escenas']
MOUTH={'jawOpen','mouthPucker','mouthFunnel','mouthRollLower','mouthPressLeft','mouthPressRight',
       'mouthClose','mouthLowerDownLeft','mouthLowerDownRight','mouthUpperUpLeft','mouthUpperUpRight'}

def norm(s):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s.lower()).encode('ascii','ignore').decode())

def tokens_for(words, script):
    target=script.split()
    if len(words)==len(target):
        return target
    a,b=[norm(x) for x in target],[norm(x[0]) for x in words]
    out=['']*len(words)
    prefix=[]
    for kind,i,j,k,l in difflib.SequenceMatcher(None,a,b).get_opcodes():
        if kind=='equal':
            for m in range(j-i):out[k+m]=target[i+m]
        elif kind=='replace':
            for m,word in enumerate(target[i:j]):
                if l>k:out[k+min(l-k-1,math.floor(m*(l-k)/max(1,j-i)))]+=(' ' if out[k+min(l-k-1,math.floor(m*(l-k)/max(1,j-i)))] else '')+word
                elif k>0:out[k-1]+=' '+word
        elif kind=='delete':
            if k>0:out[k-1]+=' '+' '.join(target[i:j])
            else:prefix+=target[i:j]
    if prefix and out:out[0]=' '.join(prefix)+' '+out[0]
    return out

def ass_time(t):
    c=round(t*100)
    return f'{c//360000}:{(c//6000)%60:02d}:{(c//100)%60:02d}.{c%100:02d}'

def subtitle_events(scene, data, offset):
    ws=data['palabras']; display=tokens_for(ws,scene['texto'])
    events=[]; group=[]
    def flush():
        if not group:return
        start=offset+ws[group[0]][1]
        end=offset+ws[group[-1]][2]+.12
        text=re.sub(r'\s+',' ',' '.join(display[i] for i in group)).strip()
        if len(text)>0:
            events.append(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Sutil,,0,0,0,,{text}')
        group.clear()
    for i,(word,start,end) in enumerate(ws):
        if group and ((end-ws[group[0]][1]>3.1) or (sum(len(display[j])+1 for j in group)+len(display[i])>47)
                      or (start-ws[group[-1]][2]>.38)):
            flush()
        group.append(i)
        if display[i].endswith(('.','?','!','…')):flush()
    flush()
    return events

def main():
    data=[]; all_keys=set(); all_tongue=set()
    for scene in SCENES:
        d=json.loads((HERE/('curvas_'+scene['id'])/'curvas.json').read_text(encoding='utf-8'))
        with wave.open(str(HERE/(scene['id']+'.wav')),'rb') as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,RATE):raise RuntimeError('WAV incompatible')
            pcm=w.readframes(w.getnframes())
        if scene['id']=='problema':
            # La voz ya contiene un pequeño respiro tras "inglés". Lo ampliamos
            # en una zona de baja energía para que la pregunta inicial respire.
            at, extra = 1.34, 0.38
            cut_audio=round(at*RATE)*2
            pcm=pcm[:cut_audio]+bytes(round(extra*RATE)*2)+pcm[cut_audio:]
            cut_curve=round(at*FPS)
            padding=round(extra*FPS)
            for key,values in d['curvas'].items():
                hold=0.0 if key in MOUTH else values[cut_curve-1]
                d['curvas'][key]=values[:cut_curve]+[hold]*padding+values[cut_curve:]
            for key,values in d['lengua'].items():
                d['lengua'][key]=values[:cut_curve]+[values[cut_curve-1]]*padding+values[cut_curve:]
            d['cabeza']=d['cabeza'][:cut_curve]+[d['cabeza'][cut_curve-1]]*padding+d['cabeza'][cut_curve:]
            for track in ('palabras','fonemas'):
                for item in d[track]:
                    if item[1]>=at:item[1]+=extra
                    if item[2]>=at:item[2]+=extra
        data.append((scene,d,pcm))
        all_keys.update(d['curvas']);all_tongue.update(d['lengua'])
    curves={k:[] for k in all_keys}; tongue={k:[] for k in all_tongue}; head=[]; words=[]; phonemes=[]
    pcm_all=bytearray(); timeline=[]; sub=[]
    first=data[0][1]
    start_pad=round(INITIAL*FPS)
    for k in curves:curves[k].extend([0.0 if k in MOUTH else first['curvas'].get(k,[0.0])[0]]*start_pad)
    for k in tongue:tongue[k].extend([first['lengua'].get(k,[0.0])[0]]*start_pad)
    head.extend([first['cabeza'][0]]*start_pad)
    pcm_all.extend(bytes(round(start_pad/FPS*RATE)*2))
    current=start_pad
    for scene,d,pcm in data:
        offset=current/FPS
        n=max(len(d['cabeza']),math.ceil(len(pcm)/2/RATE*FPS))
        for k in curves:
            vals=d['curvas'].get(k,[0.0]*len(d['cabeza']))
            curves[k].extend(vals+[vals[-1]]*(n-len(vals)))
        for k in tongue:
            vals=d['lengua'].get(k,[0.0]*len(d['cabeza']))
            tongue[k].extend(vals+[vals[-1]]*(n-len(vals)))
        head.extend(d['cabeza']+[d['cabeza'][-1]]*(n-len(d['cabeza'])))
        words.extend([[w,round(a+offset,3),round(b+offset,3)] for w,a,b in d['palabras']])
        phonemes.extend([[f,round(a+offset,3),round(b+offset,3)] for f,a,b in d['fonemas']])
        needed=round(n/FPS*RATE)*2
        pcm_all.extend(pcm[:needed]);pcm_all.extend(bytes(max(0,needed-len(pcm))))
        current+=n
        pause_n=round(scene.get('pausa_despues',0)*FPS)
        for k in curves:
            last=curves[k][-1]
            if k in MOUTH:
                curves[k].extend([last*max(0,1-(i+1)/min(9,pause_n)) if i<9 else 0.0
                                  for i in range(pause_n)])
            else:curves[k].extend([last]*pause_n)
        for k in tongue:tongue[k].extend([tongue[k][-1]]*pause_n)
        head.extend([head[-1]]*pause_n)
        pcm_all.extend(bytes(round(pause_n/FPS*RATE)*2))
        current+=pause_n
        timeline.append({'id':scene['id'],'start':round(offset,3),'end':round(current/FPS,3),
                         'pantallas':scene['pantallas'],'texto':scene['texto']})
        sub+=subtitle_events(scene,d,offset)
    total=current/FPS
    out={'fps':FPS,'duracion':total,'texto':' '.join(s['texto'] for s in SCENES),
         'voz':'Willow','palabras':words,'fonemas':phonemes,'lengua':tongue,'curvas':curves,'cabeza':head}
    (HERE/'timeline.json').write_text(json.dumps({'inicio_s':INITIAL,'duracion_s':total,'escenas':timeline},ensure_ascii=False,indent=2),encoding='utf-8')
    audio_path=HERE/'audio_revision.wav'
    with wave.open(str(audio_path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(pcm_all)
    import sys
    sys.path.insert(0,'D:/literalevel_video/comercial_completo_20260928')
    from ajustar_boca_audio import adjust
    out,metrics=adjust(out,audio_path)
    (HERE/'visor').mkdir(exist_ok=True)
    (HERE/'visor'/'curvas.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
    ass='''[Script Info]
Title: Pléyade demo revisada Willow
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sutil,Segoe UI,27,&H08F8F8F8,&H08F8F8F8,&H50081020,&HFF081020,0,0,0,0,100,100,0,0,1,1.8,0.8,3,60,72,37,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    (HERE/'subtitulos_revision.ass').write_text(ass+'\n'.join(sub)+'\n',encoding='utf-8')
    print('DURATION',round(total,2),'SCENES',len(timeline),'WORDS',len(words),'SUBS',len(sub),'CURVE_FRAMES',len(head),'MOUTH',metrics,flush=True)

if __name__=='__main__':main()
