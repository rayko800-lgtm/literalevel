"""Una lengua modelada en Blender (sin ventana) con shape keys por parametro,
exportada a glTF binario para el visor 3D de la boca.

Muestra para que Miguel vea la diferencia de aspecto frente al tubo de seis
nudos: superficie organica suave, punta afinada, surco central. Las shape keys
son una por parametro de `animacion_articulatoria.PARAMETROS`, y el visor las
mezcla (`morphTargetInfluences`) desde el mismo JSON de poses.

Coordenadas del visor: -x delante (punta), +x atras (raiz), +y arriba, z lateral.
En Blender se modela con Z arriba e Y lateral; el exportador (export_yup) lo
convierte. Las unidades son las de escena.ts (la cavidad mide unos 6).

    "C:\\Program Files\\Blender Foundation\\Blender 2.93\\blender.exe" -b --python tools/boca3d_blender/lengua.py
    (SALIDA_GLB para cambiar la ruta; por defecto tools/boca3d_demo/lengua.glb)
"""
import json
import math
import os
import struct

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.environ.get("SALIDA_GLB", os.path.join(AQUI, "..", "boca3d_demo", "lengua.glb"))

# --- Forma base: un elipsoide afinado hacia la punta, con surco central ------

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0)
ob = bpy.context.active_object
ob.name = "lengua"
ob.data.name = "lengua"
bpy.ops.object.shade_smooth()

LARGO, ANCHO, ALTO = 2.2, 1.0, 0.45   # semiejes
CENTRO = (0.2, 0.0, -0.4)             # la punta queda en x=-2.0, la raiz en 2.4


def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rampa(x, a, b):
    return suave((x - a) / (b - a))


def campana(x, c, w):
    return math.exp(-((x - c) / w) ** 2)


for v in ob.data.vertices:
    x, y, z = v.co.x * LARGO, v.co.y * ANCHO, v.co.z * ALTO
    # Afinar hacia la punta (mas estrecha y mas plana) y engordar un poco atras.
    f = 0.45 + 0.55 * rampa(x, -2.2, -0.4)
    y *= f
    z *= 0.6 + 0.4 * rampa(x, -2.2, -0.9)
    # La cara de arriba algo mas plana que la de abajo, y un surco central.
    if z > 0:
        z *= 0.85
        z -= 0.05 * campana(y, 0.0, 0.18) * rampa(x, -1.6, -0.6) * (1 - rampa(x, 1.2, 2.2))
    # La raiz baja hacia el suelo de la boca y engorda: no queda flotando.
    z -= 0.7 * rampa(x, 1.0, 2.4)
    y *= 1 + 0.15 * rampa(x, 0.6, 2.0)
    v.co = (x + CENTRO[0], y + CENTRO[1], z + CENTRO[2])

base = [tuple(v.co) for v in ob.data.vertices]

# --- Shape keys: una por parametro ------------------------------------------

ob.shape_key_add(name="Basis", from_mix=False)


def clave(nombre, delta):
    """`delta(x, y, z) -> (dx, dy, dz)` sobre la forma base."""
    k = ob.shape_key_add(name=nombre, from_mix=False)
    for i, (x, y, z) in enumerate(base):
        dx, dy, dz = delta(x, y, z)
        k.data[i].co = (x + dx, y + dy, z + dz)
    return k


# Peso de la punta (1 en la punta, 0 desde x=-0.6 hacia atras) y del cuerpo.
punta_w = lambda x: 1 - rampa(x, -2.0, -0.6)
cuerpo_w = lambda x: campana(x, 0.1, 1.3)
dorso_w = lambda x: campana(x, 1.5, 0.75)
raiz_w = lambda x: rampa(x, 0.8, 2.4)

clave("mandibula", lambda x, y, z: (0.0, 0.0, -0.55 * (0.35 + 0.65 * raiz_w(x))))
clave("punta_arriba", lambda x, y, z: (0.15 * punta_w(x), 0.0, 1.25 * punta_w(x) ** 1.3))
clave("punta_atras", lambda x, y, z: (0.9 * punta_w(x) ** 1.2, 0.0, 1.05 * punta_w(x)))
clave("punta_interdental", lambda x, y, z: (-0.7 * punta_w(x), 0.0, 0.55 * punta_w(x)))
clave("cuerpo_alto", lambda x, y, z: (0.0, 0.0, 1.3 * cuerpo_w(x) * (0.6 + 0.4 * (z > CENTRO[2]))))
clave("cuerpo_bajo", lambda x, y, z: (0.0, 0.0, -0.75 * cuerpo_w(x)))
clave("cuerpo_delante", lambda x, y, z: (-0.85 * campana(x, 0.0, 2.0), 0.0, 0.0))
clave("cuerpo_atras", lambda x, y, z: (0.75 * campana(x, 0.3, 2.0), 0.0, 0.0))
clave("dorso_velo", lambda x, y, z: (0.15 * dorso_w(x), 0.0, 1.55 * dorso_w(x) * (0.55 + 0.45 * (z > CENTRO[2]))))
clave("raiz_atras", lambda x, y, z: (0.55 * raiz_w(x), 0.0, -0.1 * raiz_w(x)))

# --- Material y exportacion --------------------------------------------------

mat = bpy.data.materials.new("lengua")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.80, 0.36, 0.42, 1.0)
bsdf.inputs["Roughness"].default_value = 0.45
bsdf.inputs["Subsurface"].default_value = 0.15
bsdf.inputs["Subsurface Color"].default_value = (0.9, 0.3, 0.3, 1.0)
ob.data.materials.append(mat)

bpy.ops.export_scene.gltf(
    filepath=os.path.abspath(SALIDA), export_format="GLB", export_morph=True, export_morph_normal=True,
    export_apply=False, export_yup=True, export_materials="EXPORT",
)

with open(SALIDA, "rb") as f:
    _, _, length = struct.unpack("<III", f.read(12))
    clen, _ = struct.unpack("<II", f.read(8))
    doc = json.loads(f.read(clen).decode("utf-8"))
malla = doc["meshes"][0]
print("LENGUA_OK", json.dumps({
    "blender": bpy.app.version_string, "bytes": length, "vertices": len(ob.data.vertices),
    "morph_targets": [len(p.get("targets", [])) for p in malla["primitives"]],
    "targetNames": malla.get("extras", {}).get("targetNames"),
}))
