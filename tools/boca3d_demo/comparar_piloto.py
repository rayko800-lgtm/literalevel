"""Monta capturas originales lado a lado, sin retocar los renders.

Uso: python tools/boca3d_demo/comparar_piloto.py build/d4_4b_piloto
Las capturas completas conservan 390x844; aquí se usa el recorte del visor.
"""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

raiz = Path(sys.argv[1])
fuente = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 21)
pequena = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
casos = [('p', '/p/ - cierre bilabial'), ('theta', '/θ/ - punta'), ('k', '/k/ - raíz'),
         ('b', '/b/ - control'), ('m', '/m/ - control'), ('t', '/t/ - control'), ('eng', '/ŋ/ - control')]
w, h = Image.open(raiz / 'capturas_antes/p_visor.png').size
salida = Image.new('RGB', (2*w+60, 92+len(casos)*(h+44)), '#f4f6fb')
d = ImageDraw.Draw(salida)
d.text((20, 12), 'D4.4b · PILOTO · pendiente de revisión de Miguel', font=fuente, fill='#18223a')
d.text((20, 45), 'ANTES', font=fuente, fill='#18223a')
d.text((w+40, 45), 'DESPUÉS', font=fuente, fill='#18223a')
for i,(nombre,etiqueta) in enumerate(casos):
    y = 82+i*(h+44)
    d.text((20,y),etiqueta,font=fuente,fill='#18223a')
    for j,estado in enumerate(['antes','despues']):
        salida.paste(Image.open(raiz / f'capturas_{estado}/{nombre}_visor.png'), (20+j*(w+20),y+30))
salida.save(raiz/'comparativa.png')

fases = ['reposo','contacto','liberacion','final']
salida = Image.new('RGB',(4*w+100,84+6*(h+45)),'#f4f6fb')
d = ImageDraw.Draw(salida)
d.text((20,12),'Cierre y liberación · vista frontal de diagnóstico',font=fuente,fill='#18223a')
for j,fase in enumerate(fases):
    d.text((20+j*(w+20),48),f'{fase} · {[0.42,1.2,1.6,2.25][j]} s',font=pequena,fill='#18223a')
for i,(s,estado) in enumerate([(s,e) for s in ['p','b','m'] for e in ['antes','despues']]):
    y=78+i*(h+45)
    d.text((20,y),f'/{s}/ · {"ANTES" if estado=="antes" else "DESPUÉS"}',font=fuente,fill='#18223a')
    for j,fase in enumerate(fases):
        salida.paste(Image.open(raiz/f'capturas_{estado}/{s}_{fase}.png'),(20+j*(w+20),y+30))
salida.save(raiz/'fases_bilabiales.png')
print('COMPARATIVAS_OK: comparativa.png y fases_bilabiales.png')
