"""Aplana el tercio anterior de la lengua en el gesto interdental (/θ ð/).

Blender -b --python-exit-code 1 --python este.py -- fuente.glb carpeta_nueva

La punta interdental medía 0,64 u y no cabía entre los incisivos con la
mandíbula del 2D (0,36 → hueco 0,54 u). En la referencia de Miguel la lengua
asoma plana entre los dientes con la boca casi cerrada. Se escala el grosor
(vertical) del tercio anterior hacia su línea media SÓLO en la clave
punta_interdental (0,78: volumen −8,8 %, dentro del ±10 %). Ensanchar (ANCHO
1,1) metía los bordes en los incisivos: se deja en 1,0; punta y lámina se escalan igual para no
afilar la punta (criterio punta ≥ 0,75 lámina de medir_lengua.mjs).
No usa fotos ni vídeo.
"""
import bpy
import json
import os
import sys
import numpy as np


def main():
    source, output = sys.argv[sys.argv.index('--') + 1:]
    output = os.path.abspath(output)
    os.makedirs(output, exist_ok=True)
    grosor = float(os.environ.get('GROSOR_PUNTA', '.78'))
    ancho = float(os.environ.get('ANCHO_PUNTA', '1.0'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(source), merge_vertices=True)
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data.shape_keys)
    keys = ob.data.shape_keys.key_blocks
    base = np.array([tuple(p.co) for p in keys[0].data])
    clave = keys['punta_interdental']
    gesto = np.array([tuple(p.co) for p in clave.data])
    # Peso: pleno en el tercio anterior (x < -1.1), se extingue hacia x = -0.5.
    t = np.clip((gesto[:, 0] + 1.1) / .6, 0, 1)
    peso = 1 - t * t * (3 - 2 * t)
    # Línea media del grosor por franjas de x, en la pose interdental.
    centro = np.zeros(len(gesto))
    franjas = np.round(gesto[:, 0] / .05).astype(int)
    for f in np.unique(franjas):
        sel = franjas == f
        centro[sel] = (gesto[sel, 2].min() + gesto[sel, 2].max()) / 2
    # Tras importar el glTF: x delante/detrás, y lateral, z vertical.
    nuevo = gesto.copy()
    nuevo[:, 2] = centro + (gesto[:, 2] - centro) * (1 - peso * (1 - grosor))
    nuevo[:, 1] = gesto[:, 1] * (1 + peso * (ancho - 1))
    for j, p in enumerate(clave.data):
        p.co = nuevo[j]
    for polygon in ob.data.polygons:
        polygon.use_smooth = True
    bpy.ops.export_scene.gltf(filepath=os.path.join(output, 'lengua.glb'), export_format='GLB',
                             export_yup=True, export_morph=True, export_morph_normal=False,
                             export_extras=True, export_materials='EXPORT')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output, 'lengua.blend'))
    informe = {'fuente': os.path.abspath(source), 'grosor': grosor, 'ancho': ancho,
               'vertices_afectados': int((peso > 0).sum()),
               'max_delta': float(np.linalg.norm(nuevo - gesto, axis=1).max())}
    with open(os.path.join(output, 'aplanado.json'), 'w', encoding='utf8') as f:
        json.dump(informe, f, ensure_ascii=False, indent=2)
    print('APLANADO', json.dumps(informe))


if __name__ == '__main__':
    main()
