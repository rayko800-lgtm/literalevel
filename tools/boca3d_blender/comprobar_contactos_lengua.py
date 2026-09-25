"""Compara dos lenguas con las envolventes conservadoras del generador.

Blender -b --python-exit-code 1 --python este.py -- antes.glb despues.glb salida.json
No certifica la anatomía ni intersecciones entre todos los triángulos.
"""
import bpy
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lengua_realista import metrics, poses, samples


def read(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(path), merge_vertices=True)
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data.shape_keys)
    keys = ob.data.shape_keys.key_blocks
    return np.array([[tuple(p.co) for p in k.data] for k in keys]), [k.name for k in keys]


before_path, after_path, output = sys.argv[sys.argv.index('--') + 1:]
before, names = read(before_path)
after, new_names = read(after_path)
assert names == new_names
catalog = samples(poses())
old, new = metrics(before, catalog), metrics(after, catalog)
regressions = []
for symbol, pose in catalog.items():
    for field, tolerance in [('techo', .08 if pose['punta_toca'] or pose['dorso_velo'] else 0),
                             ('diente_sup', .08 if pose['punta'] == 'interdental' else 0),
                             ('diente_inf', .08 if pose['punta'] == 'interdental' else 0)]:
        if new[symbol][field] > max(tolerance, old[symbol][field]) + .002:
            regressions.append([symbol, field, old[symbol][field], new[symbol][field]])
report = {'estados': len(catalog), 'antes': old, 'despues': new, 'regresiones': regressions}
with open(output, 'w', encoding='utf8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print('CONTACTOS', json.dumps({'estados': len(catalog), 'regresiones': regressions}))
assert not regressions
