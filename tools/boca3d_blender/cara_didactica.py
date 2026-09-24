"""Piloto de labios y coronas, derivado del GLB v8. No reemplaza los assets de la app.

Blender 2.93 -b --python tools/boca3d_blender/cara_didactica.py
SALIDA_DIDACTICA permite elegir la carpeta. Conserva la atribución CC BY 3.0
de Lee Perry-Smith. Colores ilustrativos; no se pretende una anatomía clínica.
"""
import bpy
import json
import math
import os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.environ.get('SALIDA_DIDACTICA', os.path.join(ROOT, 'build', 'boca_didactica'))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'tools', 'boca3d_demo', 'cara.glb'))

def smooth(t):
    t = max(0., min(1., t))
    return t*t*(3-2*t)

import sys
sys.path.insert(0, os.path.dirname(__file__))
from perioral_didactico import construir
construir()
from interior_didactico import construir as construir_interior
construir_interior()

from dientes_realistas import construir as construir_dientes
construir_dientes()

for ob in bpy.context.scene.objects:
    if ob.type=='MESH':
        assert all(math.isfinite(c) for v in ob.data.vertices for c in v.co),ob.name

path=os.path.join(OUT,'cara.glb')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_yup=True,
                         export_materials='EXPORT', export_morph=True, export_morph_normal=False,
                         export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'cara.blend'))
print('PILOTO_DIDACTICO',json.dumps({'bytes':os.path.getsize(path),'salida':path}))
