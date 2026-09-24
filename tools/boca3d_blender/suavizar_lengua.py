"""Suaviza los escalones de las deformaciones sin añadir polígonos.

Blender -b --python-exit-code 1 --python este.py -- fuente.glb carpeta_nueva
Entrada: salida reproducible de lengua_realista.py. No usa fotos ni vídeo.
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
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(source), merge_vertices=True)
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data.shape_keys)
    keys = ob.data.shape_keys.key_blocks
    before = np.array([[tuple(p.co) for p in key.data] for key in keys])
    edges = np.array([tuple(e.vertices) for e in ob.data.edges])
    start = np.concatenate((edges[:, 0], edges[:, 1]))
    end = np.concatenate((edges[:, 1], edges[:, 0]))
    degree = np.bincount(start, minlength=len(before[0]))[:, None]

    # Alisar el tercio anterior, donde los recortes heredados generan aristas.
    # El peso se desvanece antes de la raíz para conservar su inserción.
    weight = np.clip((.8 - before[0, :, 0]) / 1.2, 0, 1)
    weight = (weight * weight * (3 - 2 * weight))[:, None]
    after = before.copy()
    steps = int(os.environ.get('PASOS_LENGUA', '15'))
    assert 1 <= steps <= 20
    for k in range(len(keys)):
        points = after[k]
        # Dos pasos opuestos reducen las oscilaciones sin el encogimiento
        # sistemático de un promedio simple. Se miden volumen y contactos.
        for _ in range(steps):
            for amount in (.45, -.46):
                total = np.zeros_like(points)
                np.add.at(total, start, points[end])
                points += amount * weight * (total / degree - points)
    # El corte sagital del visor reutiliza esta cadena de vértices. La
    # triangulación asimétrica puede apartarla unas milésimas del plano.
    midline = abs(before[0, :, 1]) < 1e-5
    after[:, midline, 1] = 0
    assert np.isfinite(after).all()
    report = {
        'fuente': os.path.abspath(source),
        'vertices': len(before[0]),
        'pasos': steps,
        'triangulos': sum(len(p.vertices) - 2 for p in ob.data.polygons),
        'claves': [k.name for k in keys],
        'max_delta': {k.name: float(np.linalg.norm(after[i] - before[i], axis=1).max())
                      for i, k in enumerate(keys)},
        'raiz_delta': float(abs(after[:, weight[:, 0] == 0] - before[:, weight[:, 0] == 0]).max()),
    }
    for i, key in enumerate(keys):
        for j, p in enumerate(key.data):
            p.co = after[i, j]
    for j, vertex in enumerate(ob.data.vertices):
        vertex.co = keys[0].data[j].co
    ob.data.update()
    for polygon in ob.data.polygons:
        polygon.use_smooth = True
    bpy.ops.export_scene.gltf(filepath=os.path.join(output, 'lengua.glb'), export_format='GLB',
                             export_yup=True, export_morph=True, export_morph_normal=False,
                             export_extras=True, export_materials='EXPORT')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output, 'lengua.blend'))
    with open(os.path.join(output, 'suavizado.json'), 'w', encoding='utf8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print('SUAVIZADO', json.dumps(report))


if __name__ == '__main__':
    main()
