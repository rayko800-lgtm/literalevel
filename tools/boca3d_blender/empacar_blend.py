"""Copia un proyecto con sus texturas incorporadas; no modifica el original.

blender -b --python empacar_blend.py -- entrada.blend salida.blend
"""
from pathlib import Path
import sys
import bpy

entrada, salida = (Path(p).resolve() for p in sys.argv[sys.argv.index('--') + 1:])
if entrada == salida:
    raise ValueError('La entrega debe ser una copia distinta del original')
bpy.ops.wm.open_mainfile(filepath=str(entrada))
bpy.ops.file.pack_all()
pendientes = [i.name for i in bpy.data.images
              if i.source == 'FILE' and i.filepath and not i.packed_file]
if pendientes:
    raise RuntimeError('Texturas sin incorporar: ' + ', '.join(pendientes))
salida.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(salida))
print('PROYECTO_AUTOCONTENIDO', salida.name)
