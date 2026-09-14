"""Una lengua modelada en Blender (sin ventana) con shape keys por parametro,
exportada a glTF binario para el visor 3D de la boca.

Superficie organica suave, punta afinada, surco central, bordes laterales
marcados y la raiz bajando al suelo de la boca. Las shape keys son una por
parametro de `animacion_articulatoria.PARAMETROS`, y el visor las mezcla
(`morphTargetInfluences`) desde el mismo JSON de poses.

Comprobacion geometrica limitada: el guion carga poses.ejemplo.json,
calcula las influencias de cada pose con la MISMA regla que escena.ts
(`morfosDe`), mezcla las shape keys y mide cuanto entra la lengua en el techo
(perfil aproximado del paladar y velo del visor). Cada shape key se
recorta contra el techo y despues se reparte cada pose: si alguna entra mas
que la tolerancia, se dice y el guion termina con error. Se muestrean vertices
en 53 poses estaticas, no todas las intersecciones de triangulos/transiciones.

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
import sys

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
SALIDA = os.environ.get("SALIDA_GLB", os.path.join(AQUI, "..", "boca3d_demo", "lengua.glb"))
POSES = os.path.join(RAIZ, "front", "src", "app", "compartido", "boca3d", "poses.ejemplo.json")

# --- El techo de la boca, igual que en escena.ts -----------------------------

PALADAR = [(-2.55, 0.5), (-2.3, 0.75), (-2.05, 0.92), (-1.7, 1.15), (-1.2, 1.35), (-0.6, 1.48),
           (0.0, 1.52), (0.6, 1.5), (1.2, 1.42), (1.7, 1.32), (2.05, 1.22)]
GROSOR_PALADAR = 0.26
PIVOTE_VELO, LARGO_VELO = (2.05, 1.22), 1.2
VELO_CERRADO, VELO_ABIERTO = -0.44, -1.22
SUELO_Y = -1.1                                  # cara de arriba del suelo de la boca
FARINGE_X = 3.0                                 # cara delantera de la pared
HOLGURA = 0.06                                  # separacion minima con el techo
TOLERANCIA_TOQUE = 0.08                         # lo que puede entrar cuando toca (punta_toca, dorso_velo)


def paladar_en(x):
    if x <= PALADAR[0][0]:
        return 9.0
    for (x0, y0), (x1, y1) in zip(PALADAR, PALADAR[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return PALADAR[-1][1]


def velo_en(angulo, f):
    c, s = math.cos(angulo), math.sin(angulo)
    px, py = PIVOTE_VELO[0] + c * LARGO_VELO * f, PIVOTE_VELO[1] + s * LARGO_VELO * f
    nx, ny = s, -c
    if ny > 0:
        nx, ny = -nx, -ny
    return px, py, nx, ny


def techo(x, velo_abierto):
    """Cara inferior del techo sobre x: paladar, y detras, el velo."""
    if x <= PIVOTE_VELO[0]:
        return paladar_en(x) - GROSOR_PALADAR / 2
    ang = VELO_ABIERTO if velo_abierto else VELO_CERRADO
    mejor = 9.0
    for i in range(11):
        px, py, nx, ny = velo_en(ang, i / 10)
        if abs(px - x) < 0.25:
            mejor = min(mejor, py + ny * GROSOR_PALADAR / 2)
    return mejor


# --- Forma base --------------------------------------------------------------

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=72, ring_count=36, radius=1.0)
ob = bpy.context.active_object
ob.name = "lengua"
ob.data.name = "lengua"
bpy.ops.object.shade_smooth()

LARGO, ANCHO, ALTO = 2.2, 1.0, 0.42   # semiejes
CENTRO = (0.2, 0.0, -0.45)            # la punta queda en x=-2.0, la raiz en 2.4


def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rampa(x, a, b):
    return suave((x - a) / (b - a))


def campana(x, c, w):
    return math.exp(-((x - c) / w) ** 2)


for v in ob.data.vertices:
    ux, uy, uz = v.co.x, v.co.y, v.co.z          # en la esfera unidad
    x, y, z = ux * LARGO, uy * ANCHO, uz * ALTO
    # Afinar hacia la punta (mas estrecha y mas plana).
    f = 0.42 + 0.58 * rampa(x, -2.2, -0.3)
    y *= f
    z *= 0.55 + 0.45 * rampa(x, -2.2, -0.9)
    # Seccion con bordes: arriba plano y las esquinas marcadas, abajo mas redondo.
    lateral = abs(uy)
    if z > 0:
        z *= 0.55 + 0.45 * (1 - lateral ** 3)          # la cara de arriba, casi plana
        z += 0.06 * campana(lateral, 0.82, 0.12) * rampa(x, -1.8, -0.8)   # el borde lateral
        z -= 0.05 * campana(y, 0.0, 0.16) * rampa(x, -1.6, -0.6) * (1 - rampa(x, 1.2, 2.2))  # surco
    # La raiz baja hacia el suelo de la boca y engorda: no queda flotando.
    z -= 0.7 * rampa(x, 1.0, 2.4)
    y *= 1 + 0.15 * rampa(x, 0.6, 2.0)
    v.co = (x + CENTRO[0], y + CENTRO[1], z + CENTRO[2])

base = [tuple(v.co) for v in ob.data.vertices]

# --- Shape keys: una por parametro, recortadas contra el techo --------------

ob.shape_key_add(name="Basis", from_mix=False)
CLAVES = {}


def clave(nombre, delta, velo_abierto=False, toca=False, margen_x=(0.0, 0.0)):
    """`delta(x, y, z) -> (dx, dy, dz)` sobre la forma base; el resultado no
    entra en el techo (salvo la holgura de un toque, si `toca`). `margen_x`
    recorta tambien contra el techo desplazado, porque otra shape key
    (cuerpo_delante, cuerpo_atras) puede mover la lengua en x a la vez."""
    k = ob.shape_key_add(name=nombre, from_mix=False)
    deltas = []
    muestras = [margen_x[0] + (margen_x[1] - margen_x[0]) * j / 4 for j in range(5)]
    for i, (x, y, z) in enumerate(base):
        dx, dy, dz = delta(x, y, z)
        nx, nz = x + dx, z + dz
        tope = min(techo(nx + d, velo_abierto) for d in muestras) - (-TOLERANCIA_TOQUE if toca else HOLGURA)
        if nz > tope:
            nz = tope
        k.data[i].co = (nx, y + dy, nz)
        deltas.append((nx - x, dy, nz - z))
    CLAVES[nombre] = deltas
    return k


punta_w = lambda x: 1 - rampa(x, -2.0, -0.6)
cuerpo_w = lambda x: campana(x, 0.1, 1.3)
dorso_w = lambda x: campana(x, 1.45, 0.75)
raiz_w = lambda x: rampa(x, 0.8, 2.4)
arriba = lambda z: 0.6 + 0.4 * (z > CENTRO[2])    # la cara de arriba sube mas que la de abajo

clave("mandibula", lambda x, y, z: (0.0, 0.0, -0.55 * (0.35 + 0.65 * raiz_w(x))))
clave("punta_arriba", lambda x, y, z: (0.1 * punta_w(x), 0.0, 1.15 * punta_w(x) ** 1.3), toca=True, margen_x=(-0.3, 0.1))
# Retrofleja: la punta se alza y se recoge un poco; la lamina sube con ella
# para que la punta no se doble sobre el cuerpo (comprobado abajo).
clave("punta_atras", lambda x, y, z: (0.4 * punta_w(x) ** 1.5, 0.0, 0.95 * punta_w(x) + 0.3 * campana(x, -0.9, 0.5)))
clave("punta_interdental", lambda x, y, z: (-0.95 * punta_w(x), 0.0, 1.25 * punta_w(x)))
clave("cuerpo_alto", lambda x, y, z: (0.0, 0.0, 1.35 * cuerpo_w(x) * arriba(z)), margen_x=(-0.8, 0.7))
clave("cuerpo_bajo", lambda x, y, z: (0.0, 0.0, -0.7 * cuerpo_w(x)))
clave("cuerpo_delante", lambda x, y, z: (-0.8 * campana(x, 0.0, 2.0), 0.0, 0.0))
clave("cuerpo_atras", lambda x, y, z: (0.7 * campana(x, 0.3, 2.0), 0.0, 0.0))
clave("dorso_velo", lambda x, y, z: (0.15 * dorso_w(x), 0.0, 1.6 * dorso_w(x) * arriba(z)), velo_abierto=True, toca=True, margen_x=(-0.1, 0.4))
clave("raiz_atras", lambda x, y, z: (0.5 * raiz_w(x), 0.0, -0.1 * raiz_w(x)))

MORFOS = ["mandibula", "punta_arriba", "punta_atras", "punta_interdental", "cuerpo_alto", "cuerpo_bajo",
          "cuerpo_delante", "cuerpo_atras", "dorso_velo", "raiz_atras"]


def morfos_de(p):
    """La misma regla que `morfosDe` en escena.ts."""
    alt, ade = p["cuerpo"]
    toca = p["punta_toca"]
    punta = p["punta"]
    return [
        0.3 * min(1.0, max(0.0, p["mandibula"])),
        (1.0 if toca else 0.75) if punta in ("alveolar", "postalveolar") else 0.45 if punta == "dental" else 0.0,
        1.0 if punta == "retrofleja" else 0.0,
        1.0 if punta == "interdental" else 0.0,
        max(0.0, (alt - 0.45) / 0.55),
        max(0.0, (0.45 - alt) / 0.45),
        max(0.0, (ade - 0.5) / 0.5),
        max(0.0, (0.5 - ade) / 0.5),
        1.0 if p["dorso_velo"] else min(1.0, p["dorso_alto"]),
        min(1.0, max(0.0, p["raiz"])),
    ]


# --- Comprobacion contra las poses del catalogo ------------------------------

with open(POSES, encoding="utf-8") as f:
    catalogo = json.load(f)
poses = dict(catalogo["sonidos"])
poses.update({f"rp:{k}": v for k, v in catalogo["rp"].items()})
poses["reposo"] = catalogo["reposo"]

informe = []
peor = 0.0
peor_pliegue = 0.0
interdentales = []
ES_PUNTA = [punta_w(x) > 0.6 for x, _, _ in base]
ES_CUERPO = [punta_w(x) < 0.15 for x, _, _ in base]
for nombre, p in poses.items():
    inf = morfos_de(p)
    toca = p["punta_toca"] or p["dorso_velo"]
    permitido = TOLERANCIA_TOQUE if toca else 0.0
    entra = 0.0
    pos = []
    angulo = min(1.0, max(0.0, p["mandibula"])) * 0.42
    coseno, seno = math.cos(angulo), math.sin(angulo)
    for i, (x, y, z) in enumerate(base):
        nx = x + sum(w * CLAVES[m][i][0] for w, m in zip(inf, MORFOS))
        nz = z + sum(w * CLAVES[m][i][2] for w, m in zip(inf, MORFOS))
        # EscenaBoca monta el GLB dentro de la mandibula: comparar el techo
        # contra coordenadas locales ocultaba el error de la punta interdental.
        nx, nz = (2.6 + (nx - 2.6) * coseno - (nz - 0.9) * seno,
                  0.9 + (nx - 2.6) * seno + (nz - 0.9) * coseno)
        pos.append((nx, y, nz))
        entra = max(entra, nz - techo(nx, p["velo_abierto"]))
    # La lengua no se dobla sobre si misma: ningun vertice de la punta queda
    # por debajo de la cara de arriba del cuerpo en su misma vertical.
    cuerpo = [(px, py, pz) for (px, py, pz), c in zip(pos, ES_CUERPO) if c]
    pliegue = 0.0
    for (px, py, pz), es_punta in zip(pos, ES_PUNTA):
        if not es_punta:
            continue
        techo_cuerpo = max((cz for cx, cy, cz in cuerpo if abs(cx - px) < 0.1 and abs(cy - py) < 0.12), default=-9.0)
        pliegue = max(pliegue, techo_cuerpo - pz)
    exceso = entra - permitido
    if p["punta"] == "interdental":
        frente = min(v[0] for v in pos)
        punta = [v for v in pos if v[0] < frente + 0.10]
        y_min, y_max = min(v[2] for v in punta), max(v[2] for v in punta)
        assert frente < -2.72 and y_min > -0.41 and y_max < 0.45, (nombre, frente, y_min, y_max)
        interdentales.append((nombre, round(frente, 4), round(y_min, 4), round(y_max, 4)))
    informe.append((nombre, round(entra, 3), round(exceso, 3), round(pliegue, 3)))
    peor = max(peor, exceso)
    peor_pliegue = max(peor_pliegue, pliegue)
informe.sort(key=lambda r: -max(r[2], r[3]))

# --- Material y exportacion --------------------------------------------------

mat = bpy.data.materials.new("lengua")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.80, 0.36, 0.42, 1.0)
bsdf.inputs["Roughness"].default_value = 0.45
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
    "poses_comprobadas": len(poses), "peor_exceso": round(peor, 3), "peor_pliegue": round(peor_pliegue, 3),
    "interdentales (nombre, x, ymin, ymax)": interdentales,
    "peores (nombre, entra, exceso, pliegue)": informe[:6],
}, ensure_ascii=False))
if peor > 0.005 or peor_pliegue > 0.005:
    print("COLISION: alguna pose entra en el techo o la punta se dobla sobre el cuerpo", file=sys.stderr)
    sys.exit(1)
