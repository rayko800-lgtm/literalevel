"""Gafas redondas finas de metal oro rosa, para la cabeza de la cara parlante.

Coordenadas de la cabeza de MetaHuman en cm (x lado, y adelante, z arriba), las mismas
de los puntos de referencia de la cara. Uso (Blender 2.93+, sin interfaz):
  blender -b -P gafas.py -- D:/literalevel_cara/gafas
Deja gafas.glb, gafas.blend y una vista previa gafas.png en la carpeta de salida.
"""
import math
import os
import sys

import bpy

SALIDA = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '.'
os.makedirs(SALIDA, exist_ok=True)

# Medidas en cm (redondas y finas)
OJO_X, OJO_Z, FRENTE_Y = 3.25, 168.3, 12.4   # centro de cada aro
R_ARO, R_ALAMBRE = 2.35, 0.07
SIEN_X, OREJA_Y, OREJA_Z = 7.4, 0.5, 167.2

bpy.ops.wm.read_factory_settings(use_empty=True)
esc = bpy.context.scene


def material(nombre, color, metal, rugosidad, alfa=1.0):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rugosidad
    if alfa < 1:
        b.inputs['Alpha'].default_value = alfa
        m.blend_method = 'BLEND'
    return m


ORO_ROSA = material('oro_rosa', (0.80, 0.52, 0.42), 1.0, 0.28)
CRISTAL = material('cristal', (0.95, 0.95, 0.97), 0.0, 0.05, alfa=0.12)


def tubo(puntos, nombre, radio=R_ALAMBRE, cerrado=False):
    """Alambre redondo que pasa por los puntos (curva con bisel)."""
    cu = bpy.data.curves.new(nombre, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radio
    cu.bevel_resolution = 3
    sp = cu.splines.new('POLY')
    sp.points.add(len(puntos) - 1)
    for p, (x, y, z) in zip(sp.points, puntos):
        p.co = (x, y, z, 1)
    sp.use_cyclic_u = cerrado
    ob = bpy.data.objects.new(nombre, cu)
    esc.collection.objects.link(ob)
    ob.data.materials.append(ORO_ROSA)
    return ob


def aro(cx):
    n = 64
    return [(cx + R_ARO * math.cos(2 * math.pi * i / n), FRENTE_Y, OJO_Z + R_ARO * math.sin(2 * math.pi * i / n))
            for i in range(n)]


piezas = []
for lado in (-1, 1):
    cx = lado * OJO_X
    piezas.append(tubo(aro(cx), f'aro_{lado}', cerrado=True))
    # cristal: disco fino dentro del aro
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=R_ARO - 0.02, depth=0.08,
                                        location=(cx, FRENTE_Y, OJO_Z), rotation=(math.pi / 2, 0, 0))
    c = bpy.context.object
    c.name = f'cristal_{lado}'
    c.data.materials.append(CRISTAL)
    piezas.append(c)
    # patilla: del borde exterior del aro hacia atrás, bajando a la oreja
    x0 = cx + lado * R_ARO
    patilla = [(x0, FRENTE_Y, OJO_Z + 0.4), (x0 + lado * 0.5, FRENTE_Y - 0.8, OJO_Z + 0.5),
               (lado * SIEN_X, FRENTE_Y - 3.0, OJO_Z + 0.4), (lado * (SIEN_X + 0.1), OREJA_Y + 2.0, OREJA_Z + 0.3),
               (lado * (SIEN_X + 0.1), OREJA_Y, OREJA_Z), (lado * (SIEN_X - 0.1), OREJA_Y - 1.2, OREJA_Z - 1.4)]
    piezas.append(tubo(patilla, f'patilla_{lado}'))
    # plaqueta de la nariz
    xp = lado * (OJO_X - R_ARO + 0.5)
    piezas.append(tubo([(lado * (OJO_X - R_ARO + 0.15), FRENTE_Y, OJO_Z - 0.9),
                        (xp, FRENTE_Y - 0.5, OJO_Z - 1.3)], f'soporte_{lado}', radio=0.04))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=(xp, FRENTE_Y - 0.55, OJO_Z - 1.35))
    pl = bpy.context.object
    pl.scale = (0.45, 0.25, 1.0)
    pl.name = f'plaqueta_{lado}'
    pl.data.materials.append(CRISTAL)
    piezas.append(pl)

# puente curvo entre los aros
xa = OJO_X - R_ARO
puente = [(-xa + 0.05, FRENTE_Y, OJO_Z + 0.55)]
for i in range(1, 8):
    t = i / 8
    x = -xa + 2 * xa * t
    puente.append((x, FRENTE_Y + 0.05, OJO_Z + 0.55 + 0.35 * math.sin(math.pi * t)))
puente.append((xa - 0.05, FRENTE_Y, OJO_Z + 0.55))
piezas.append(tubo(puente, 'puente'))

# todo a malla y en un solo objeto
for ob in piezas:
    ob.select_set(True)
bpy.context.view_layer.objects.active = piezas[0]
bpy.ops.object.convert(target='MESH')
bpy.ops.object.join()
gafas = bpy.context.object
gafas.name = 'gafas'
bpy.ops.object.shade_smooth()

# glTF usa metros y Y arriba: escala 0,01 y el exportador convierte los ejes
gafas.scale = (0.01, 0.01, 0.01)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SALIDA, 'gafas.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(SALIDA, 'gafas.glb'), export_format='GLB', use_selection=True)

# vista previa
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
esc.collection.objects.link(cam)
cam.location = (0.0, 0.45, 1.70)
cam.rotation_euler = (math.radians(92), 0, math.radians(180))
cam.data.lens = 60
esc.camera = cam
luz = bpy.data.objects.new('luz', bpy.data.lights.new('luz', 'AREA'))
luz.data.energy = 60
luz.data.size = 0.5
luz.location = (0.3, 0.6, 1.9)
esc.collection.objects.link(luz)
esc.world = bpy.data.worlds.new('mundo')
esc.world.use_nodes = True
esc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.8, 0.8, 0.82, 1)
esc.render.engine = 'BLENDER_EEVEE'
esc.render.resolution_x, esc.render.resolution_y = 900, 450
esc.render.filepath = os.path.join(SALIDA, 'gafas.png')
bpy.ops.render.render(write_still=True)
print('GAFAS_OK', os.path.getsize(os.path.join(SALIDA, 'gafas.glb')))
