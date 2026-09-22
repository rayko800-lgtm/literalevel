"""Métricas de los GLB del piloto, sin Blender ni dependencias externas.

Uso: python tools/boca3d_demo/medir_piloto.py carpeta_glb salida.json
Vértices exportados: suma de accesores POSITION distintos (incluye costuras).
"""
import json
import math
from pathlib import Path
import struct
import sys


def leer(ruta):
    contenido = ruta.read_bytes()
    largo = struct.unpack_from('<I', contenido, 12)[0]
    doc = json.loads(contenido[20:20 + largo])
    binario = contenido[28 + largo:]

    def datos(indice):
        a = doc['accessors'][indice]
        v = doc['bufferViews'][a['bufferView']]
        formato = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[a['componentType']]
        n = {'SCALAR': 1, 'VEC3': 3, 'VEC2': 2, 'VEC4': 4}[a['type']]
        tamano = struct.calcsize('<' + formato * n)
        inicio = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        return [struct.unpack_from('<' + formato * n, binario, inicio + i * v.get('byteStride', tamano)) for i in range(a['count'])]
    return doc, datos, len(contenido)


def volumen(vertices, indices):
    total = 0
    for i in range(0, len(indices), 3):
        a, b, c = [vertices[indices[i+j][0]] for j in range(3)]
        total += a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2]) + a[2]*(b[0]*c[1]-b[1]*c[0])
    return abs(total / 6)


def medir(carpeta):
    salida = {}
    for nombre in ['cara', 'lengua']:
        doc, datos, tamano = leer(Path(carpeta) / (nombre + '.glb'))
        accesores = {p['attributes']['POSITION'] for m in doc['meshes'] for p in m['primitives']}
        salida[nombre] = {'bytes': tamano, 'vertices_exportados': sum(doc['accessors'][i]['count'] for i in accesores),
                          'mallas': len(doc['meshes']), 'morfos': {m['name']: m.get('extras', {}).get('targetNames', []) for m in doc['meshes'] if m.get('extras', {}).get('targetNames')}}
        if nombre == 'lengua':
            m = doc['meshes'][0]
            p = m['primitives'][0]
            vs = datos(p['attributes']['POSITION'])
            salida[nombre]['vertices_sin_costuras'] = len(set(vs))
            salida[nombre]['volumen_base'] = volumen(vs, datos(p['indices']))
            salida[nombre]['limites_base'] = [[min(v[i] for v in vs), max(v[i] for v in vs)] for i in range(3)]
            catalogo = json.loads((Path(__file__).resolve().parents[2] / 'front/src/app/compartido/boca3d/poses.ejemplo.json').read_text(encoding='utf-8'))
            medidas = {}
            deltas = [datos(t['POSITION']) for t in p['targets']]
            for simbolo in ['p', 'θ', 'k', 'b', 'm', 't', 'ŋ']:
                pose = catalogo['sonidos'][simbolo]
                alt, ade = pose['cuerpo']
                punta = pose['punta']
                pesos = [0.3*pose['mandibula'], (1 if pose['punta_toca'] else 0.75) if punta in ['alveolar','postalveolar'] else 0.45 if punta == 'dental' else 0,
                         1 if punta == 'retrofleja' else 0, 1 if punta == 'interdental' else 0,
                         max(0,(alt-0.45)/0.55), max(0,(0.45-alt)/0.45), max(0,(ade-0.5)/0.5), max(0,(0.5-ade)/0.5),
                         1 if pose['dorso_velo'] else min(1,pose['dorso_alto']), pose['raiz']]
                mezcla = [tuple(v[j]+sum(w*d[i][j] for w,d in zip(pesos,deltas)) for j in range(3)) for i,v in enumerate(vs)]
                vol = volumen(mezcla, datos(p['indices']))
                angulo = pose['mandibula'] * 0.42
                c, s = math.cos(angulo), math.sin(angulo)
                mundo = [(2.6+(x-2.6)*c-(y-0.9)*s, 0.9+(x-2.6)*s+(y-0.9)*c,z) for x,y,z in mezcla]
                frente = min(v[0] for v in mundo)
                apice = [v for v in mundo if v[0] < frente+0.1]
                medidas[simbolo] = {'volumen':vol, 'volumen_relativo_base':vol/salida[nombre]['volumen_base'],
                                   'frente':frente,'grosor_apice':max(v[1] for v in apice)-min(v[1] for v in apice),
                                   'ancho_apice':max(v[2] for v in apice)-min(v[2] for v in apice)}
            salida[nombre]['poses_piloto_y_controles'] = medidas
    return salida


if __name__ == '__main__':
    resultado = medir(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    if '--comprobar' in sys.argv[3:]:
        for simbolo, medida in resultado['lengua']['poses_piloto_y_controles'].items():
            assert abs(medida['volumen_relativo_base'] - 1) < 0.05, (simbolo, medida)
        print('VOLUMEN_PILOTO_OK 7/7: desviacion inferior al 5 % de la base')
    print(json.dumps(resultado, ensure_ascii=True))
