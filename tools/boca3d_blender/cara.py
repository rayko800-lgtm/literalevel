"""Labios y perfil seccionado propios, sin texturas ni modelos de terceros.

Blender 2.93: blender -b --python tools/boca3d_blender/cara.py
Exporta cara.glb junto a la demo. Es una ilustracion didactica, no un modelo
anatomico validado. Las posiciones articulatorias siguen en escena.ts.
"""
import json
import math
import os

import bpy

SALIDA = os.environ.get("SALIDA_CARA_GLB", os.path.join(
    os.path.dirname(__file__), "..", "boca3d_demo", "cara.glb"))
bpy.ops.wm.read_factory_settings(use_empty=True)


def material(nombre, color, rugosidad=0.6):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rugosidad
    return m


PIEL = material("piel", (0.84, 0.57, 0.50))
MUCOSA = material("mucosa", (0.68, 0.34, 0.37))
LABIOS = material("labios", (0.72, 0.32, 0.36), 0.42)


def malla(nombre, vertices, caras, mat):
    # El visor tiene Y arriba; Blender exporta Z arriba a Y arriba.
    datos = bpy.data.meshes.new(nombre)
    datos.from_pydata([(x, -z, y) for x, y, z in vertices], [], caras)
    datos.update()
    ob = bpy.data.objects.new(nombre, datos)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for p in datos.polygons:
        p.use_smooth = True
    return ob


def labio(nombre, superior):
    """Arco cerrado, comisuras afinadas y borde humedo plano para el sellado.

    Base 2.3 de ancho y radio 0.3, igual al contrato de geometriaLabio.
    La cara de contacto conserva y=+/-0.3 en el centro: /p b m/ sellan.
    """
    vertices, caras = [], []
    n, lados = 64, 20
    for i in range(n + 1):
        t = -1 + 2 * i / n
        fin = max(0.025, (1 - t * t) ** 0.55)
        arco = 0.615 * t * t
        # Dos lobulos superiores y una depresion central: arco de Cupido.
        cupido = 0.055 * (math.exp(-((abs(t) - 0.28) / 0.16) ** 2)
                           - 0.5 * math.exp(-(t / 0.12) ** 2)) if superior else 0
        for j in range(lados):
            a = 2 * math.pi * j / lados
            c, s = math.cos(a), math.sin(a)
            contacto = (s < 0) if superior else (s > 0)
            alto = 0.3 if contacto else (0.24 if superior else 0.31)
            # El borde humedo es ancho y plano, no una seccion circular que
            # deja una rendija aparente al ver /p/ ligeramente desde arriba.
            perfil_y = math.copysign(abs(s) ** 0.28, s) if contacto else s
            y = alto * perfil_y * (fin ** 0.16 if contacto else fin) + (cupido * max(0, s) if superior else 0)
            x = arco + 0.3 * c * fin
            vertices.append((x, y, 1.15 * t))
    for i in range(n):
        for j in range(lados):
            a = i * lados + j
            b = i * lados + (j + 1) % lados
            caras.append((a, b, b + lados, a + lados))
    caras.append(tuple(reversed(range(lados))))
    caras.append(tuple(n * lados + j for j in range(lados)))
    return malla(nombre, vertices, caras, LABIOS)


def perfil(nombre, puntos, grosor, ancho, mat):
    """Banda curva de seccion eliptica: conserva abierto el corte sagital."""
    vertices, caras = [], []
    lados = 16
    # Catmull-Rom con extremos repetidos, para unir nariz y garganta sin cajas.
    muestras, anchos = [], []
    for i in range(len(puntos) - 1):
        p0, p1, p2, p3 = (puntos[max(0, i - 1)], puntos[i], puntos[i + 1], puntos[min(len(puntos) - 1, i + 2)])
        for k in range(8):
            t = k / 8
            muestras.append(tuple(0.5 * ((2*b) + (-a+c)*t + (2*a-5*b+4*c-d)*t*t + (-a+3*b-3*c+d)*t*t*t)
                                   for a, b, c, d in zip(p0, p1, p2, p3)))
            anchos.append(ancho[i] * (1-t) + ancho[i+1] * t if isinstance(ancho, list) else ancho)
    muestras.append(puntos[-1])
    anchos.append(ancho[-1] if isinstance(ancho, list) else ancho)
    for i, (x, y) in enumerate(muestras):
        antes, despues = muestras[max(0, i-1)], muestras[min(len(muestras)-1, i+1)]
        dx, dy = despues[0]-antes[0], despues[1]-antes[1]
        largo = math.hypot(dx, dy)
        for j in range(lados):
            a = j / lados * math.tau
            vertices.append((x - dy/largo*grosor*math.cos(a),
                             y + dx/largo*grosor*math.cos(a), anchos[i]*math.sin(a)))
    for i in range(len(muestras)-1):
        for j in range(lados):
            a, b = i*lados+j, i*lados+(j+1)%lados
            caras.append((a, b, b+lados, a+lados))
    caras.append(tuple(reversed(range(lados))))
    caras.append(tuple((len(muestras)-1)*lados+j for j in range(lados)))
    return malla(nombre, vertices, caras, mat)


labio("labio_superior", True)
labio("labio_inferior", False)
perfil("nariz", [(-2.5, 3.2), (-2.9, 2.65), (-3.55, 2.05), (-3.6, 1.82),
                 (-3.3, 1.65), (-2.97, 1.7), (-2.8, 1.2), (-2.85, 0.88)],
       0.12, [0.28, 0.33, 0.55, 0.62, 0.54, 0.32, 0.25, 0.42], PIEL)
perfil("techo_nasal", [(-2.55, 3.15), (-1.4, 2.85), (0.4, 2.8), (1.8, 2.6), (2.8, 2.1)], 0.11, 0.9, MUCOSA)
perfil("faringe", [(2.8, 2.1), (3.05, 1.55), (3.16, 0.6), (3.08, -0.55),
                   (2.95, -1.65), (2.8, -2.5), (2.75, -3.1)], 0.15, 1.0, MUCOSA)
perfil("garganta", [(1.9, -1.9), (2.0, -2.4), (2.08, -3.1)], 0.11, 0.85, MUCOSA)

# Suelo en coordenadas de reposo: el visor lo ancla al grupo mandibular.
bpy.ops.mesh.primitive_cube_add(size=2, location=(0.15, 0, -1.55))
suelo = bpy.context.object
suelo.name = "suelo_boca"
suelo.scale = (2.35, 1.08, 0.45)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bisel = suelo.modifiers.new("bordes_suaves", "BEVEL")
bisel.width = 0.28
bisel.segments = 6
bpy.ops.object.modifier_apply(modifier=bisel.name)
suelo.data.materials.append(PIEL)
for p in suelo.data.polygons:
    p.use_smooth = True
suelo.data.use_auto_smooth = True
normal = suelo.modifiers.new("normales", "WEIGHTED_NORMAL")
bpy.ops.object.modifier_apply(modifier=normal.name)

for ob in bpy.context.scene.objects:
    assert all(math.isfinite(c) for v in ob.data.vertices for c in v.co)
    assert all(p.area > 1e-10 for p in ob.data.polygons), ob.name

bpy.ops.export_scene.gltf(filepath=os.path.abspath(SALIDA), export_format="GLB", export_yup=True,
                          export_materials="EXPORT")
print("CARA_OK", json.dumps({"bytes": os.path.getsize(SALIDA), "piezas": {
    ob.name: len(ob.data.vertices) for ob in bpy.context.scene.objects}}))
