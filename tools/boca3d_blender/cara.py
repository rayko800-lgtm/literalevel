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
ESMALTE = material("esmalte", (0.95, 0.92, 0.83), 0.3)
HUESO = material("hueso", (0.83, 0.76, 0.67))


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


def puntos_labio(superior, fruncir=0.0, estirar=0.0):
    """Los vertices de un labio: arco cerrado, comisuras afinadas y borde
    humedo plano para el sellado. `fruncir` (0..1) junta las comisuras, saca
    el centro hacia delante y engorda; `estirar` (0..1) separa las comisuras,
    afina y retrae un poco. Son las dos shape keys que el visor mezcla desde
    `labios` de la pose (redondeados, muy_redondeados, estirados).

    Base 2.3 de ancho y radio 0.3, igual al contrato de geometriaLabio.
    La cara de contacto conserva y=+/-0.3 en el centro: /p b m/ sellan.
    """
    vertices = []
    n, lados = 64, 20
    ancho = 1.15 * (1 - 0.5 * fruncir + 0.25 * estirar)         # media distancia entre comisuras
    grosor = 0.3 * (1 + 0.2 * fruncir - 0.2 * estirar)
    for i in range(n + 1):
        t = -1 + 2 * i / n
        fin = max(0.025, (1 - t * t) ** 0.55)
        arco = 0.615 * t * t
        # Dos lobulos superiores y una depresion central: arco de Cupido.
        cupido = 0.055 * (math.exp(-((abs(t) - 0.28) / 0.16) ** 2)
                           - 0.5 * math.exp(-(t / 0.12) ** 2)) if superior else 0
        # Fruncir saca el centro hacia delante (mas que las comisuras) y
        # estirar lo retrae.
        adelante = -0.5 * fruncir * (1 - 0.5 * t * t) + 0.12 * estirar
        for j in range(lados):
            a = 2 * math.pi * j / lados
            c, s = math.cos(a), math.sin(a)
            contacto = (s < 0) if superior else (s > 0)
            alto = 0.3 if contacto else (0.24 if superior else 0.31)
            alto *= grosor / 0.3
            # El borde humedo es ancho y plano, no una seccion circular que
            # deja una rendija aparente al ver /p/ ligeramente desde arriba.
            perfil_y = math.copysign(abs(s) ** 0.28, s) if contacto else s
            y = alto * perfil_y * (fin ** 0.16 if contacto else fin) + (cupido * max(0, s) if superior else 0)
            x = arco + grosor * c * fin + adelante
            vertices.append((x, y, ancho * t))
    return vertices


def labio(nombre, superior):
    """El labio con sus dos shape keys (fruncir, estirar)."""
    caras = []
    n, lados = 64, 20
    for i in range(n):
        for j in range(lados):
            a = i * lados + j
            b = i * lados + (j + 1) % lados
            caras.append((a, b, b + lados, a + lados))
    caras.append(tuple(reversed(range(lados))))
    caras.append(tuple(n * lados + j for j in range(lados)))
    ob = malla(nombre, puntos_labio(superior), caras, LABIOS)
    ob.shape_key_add(name="Basis", from_mix=False)
    for clave, kw in (("fruncir", {"fruncir": 1.0}), ("estirar", {"estirar": 1.0})):
        k = ob.shape_key_add(name=clave, from_mix=False)
        for i, (x, y, z) in enumerate(puntos_labio(superior, **kw)):
            k.data[i].co = (x, -z, y)          # la misma conversion de ejes que malla()
    return ob


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
# La nariz: el dorso es una banda con volumen (no una cinta) y a los lados
# van las aletas y la punta como elipsoides, para que en tres cuartos tenga
# cuerpo y no parezca una cuchilla.
perfil("nariz", [(-2.5, 3.2), (-2.9, 2.65), (-3.55, 2.05), (-3.6, 1.82),
                 (-3.3, 1.65), (-2.97, 1.7), (-2.8, 1.2), (-2.85, 0.88)],
       0.22, [0.3, 0.38, 0.5, 0.55, 0.5, 0.36, 0.28, 0.42], PIEL)


def elipsoide(nombre, centro, escala, mat):
    """Un elipsoide liso en coordenadas del visor (x, arriba, lateral)."""
    x, arriba, lateral = centro
    ex, earriba, elateral = escala
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0,
                                         location=(x, -lateral, arriba))
    ob = bpy.context.object
    ob.name = nombre
    ob.scale = (ex, elateral, earriba)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


elipsoide("aleta_izq", (-3.12, 1.78, 0.46), (0.42, 0.32, 0.3), PIEL)
elipsoide("aleta_der", (-3.12, 1.78, -0.46), (0.42, 0.32, 0.3), PIEL)
elipsoide("punta_nariz", (-3.5, 1.95, 0.0), (0.36, 0.34, 0.48), PIEL)
perfil("techo_nasal", [(-2.55, 3.15), (-1.4, 2.85), (0.4, 2.8), (1.8, 2.6), (2.8, 2.1)], 0.11, 0.9, MUCOSA)
perfil("faringe", [(2.8, 2.1), (3.05, 1.55), (3.16, 0.6), (3.08, -0.55),
                   (2.95, -1.65), (2.8, -2.5), (2.75, -3.1)], 0.15, 1.0, MUCOSA)
perfil("garganta", [(1.9, -1.9), (2.0, -2.4), (2.08, -3.1)], 0.11, 0.85, MUCOSA)

# Las superficies respetan las coordenadas del visor, incluidos los bordes
# incisivos que usa la prueba de la lengua interdental.
perfil("paladar_modelado", [(-2.55, 0.5), (-2.3, 0.75), (-2.05, 0.92),
       (-1.7, 1.15), (-1.2, 1.35), (-0.6, 1.48), (0, 1.52),
       (0.6, 1.5), (1.2, 1.42), (1.7, 1.32), (2.05, 1.22)],
       0.13, 1.35, MUCOSA)


def arco_encia(nombre, y, radio, retroceso, mat):
    vertices, caras = [], []
    pasos, lados = 96, 20
    for i in range(pasos + 1):
        u = -1 + 2 * i / pasos
        x, z = -2.6 + retroceso * u*u, 1.35*u
        nx, nz = 1.35, -2*retroceso*u
        norma = math.hypot(nx, nz)
        for j in range(lados):
            a = math.tau*j/lados
            # Seccion eliptica: encia con volumen, sin tubo circular grueso.
            vertices.append((x + radio*math.cos(a)*nx/norma,
                             y + radio*0.8*math.sin(a), z + radio*math.cos(a)*nz/norma))
    for i in range(pasos):
        for j in range(lados):
            a, b = i*lados+j, i*lados+(j+1)%lados
            caras.append((a, b, b+lados, a+lados))
    caras += [tuple(reversed(range(lados))), tuple(pasos*lados+j for j in range(lados))]
    return malla(nombre, vertices, caras, mat)


arco_encia("encia_superior", 0.98, 0.22, 2.3, MUCOSA)
arco_encia("encia_inferior", -0.2, 0.22, 2.3, MUCOSA)
arco_encia("mandibula_modelada", -0.62, 0.28, 2.6, HUESO)


def diente(nombre, u, superior):
    incisivo = abs(u) < 0.3
    profundidad, ancho = (0.24, 0.34) if incisivo else (0.36, 0.40)
    y = 0.7 if superior else 0.1
    x, z = -2.6 + 2.3*u*u, 1.35*u
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x, -z, y))
    ob = bpy.context.object
    ob.name = nombre
    ob.scale = (profundidad/2, ancho/2, 0.25)
    ob.rotation_euler.z = -math.atan2(4.6*u, 1.35)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bisel = ob.modifiers.new("corona_redondeada", "BEVEL")
    bisel.width = 0.045 if incisivo else 0.075
    bisel.segments = 5
    bpy.ops.object.modifier_apply(modifier=bisel.name)
    for v in ob.data.vertices:
        # Corona algo mas estrecha junto a la encia; el borde no es una caja.
        cuello = max(0, (v.co.z if superior else -v.co.z) / 0.25)
        v.co.x *= 1 - 0.16*cuello
        v.co.y *= 1 - 0.1*cuello
    ob.data.materials.append(ESMALTE)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.use_auto_smooth = True
    normal = ob.modifiers.new("normales_corona", "WEIGHTED_NORMAL")
    bpy.ops.object.modifier_apply(modifier=normal.name)


for i, u in enumerate([-0.92, -0.76, -0.6, -0.44, -0.28, -0.1, 0.1, 0.28, 0.44, 0.6, 0.76, 0.92]):
    diente("diente_sup_%02d" % i, u, True)
    diente("diente_inf_%02d" % i, u, False)

# Velo en su sistema local: el mismo pivote y rotacion que la animacion 2D.
perfil("velo_modelado", [(0.03, 0), (0.35, 0), (0.7, -0.015), (1.12, -0.03)],
       0.13, [0.94, 0.93, 0.76, 0.25], MUCOSA)
perfil("uvula", [(0.95, -0.04), (1.06, -0.2), (1.1, -0.39)],
       0.075, [0.12, 0.11, 0.035], MUCOSA)

# Suelo muscular continuo y menton: coordenadas de reposo, ancladas a mandibula.
vertices, caras = [], []
pasos, lados = 64, 32
for i in range(pasos + 1):
    t = i / pasos
    x = -2.2 + 4.7*t
    ancho = 0.12 + 0.98*math.sin(math.pi*t)**0.48
    altura = 0.1 + 0.32*math.sin(math.pi*t)**0.6
    centro = -1.6 + 0.18*t
    for j in range(lados):
        a = math.tau*j/lados
        vertices.append((x, centro + altura*math.cos(a), ancho*math.sin(a)))
for i in range(pasos):
    for j in range(lados):
        a, b = i*lados+j, i*lados+(j+1)%lados
        caras.append((a, b, b+lados, a+lados))
caras += [tuple(reversed(range(lados))), tuple(pasos*lados+j for j in range(lados))]
malla("suelo_boca", vertices, caras, MUCOSA)
perfil("menton", [(-2.9, -0.55), (-2.94, -0.95), (-2.64, -1.45),
       (-1.92, -1.98), (-0.8, -2.14), (0.8, -2.06), (2.0, -2.15)],
       0.12, [0.6, 0.7, 0.82, 0.98, 1.04, 0.97, 0.72], PIEL)

for ob in bpy.context.scene.objects:
    assert all(math.isfinite(c) for v in ob.data.vertices for c in v.co)
    assert all(p.area > 1e-10 for p in ob.data.polygons), ob.name

bpy.ops.export_scene.gltf(filepath=os.path.abspath(SALIDA), export_format="GLB", export_yup=True,
                          export_materials="EXPORT", export_morph=True, export_morph_normal=True)
# El mismo archivo va a front/public/boca3d/, que es el que carga la app: los
# dos tienen que ser identicos (lo comprueba boca3d.modelos.spec.ts).
PUBLICO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "front", "public", "boca3d", "cara.glb"))
if os.path.isdir(os.path.dirname(PUBLICO)) and os.path.abspath(SALIDA) != PUBLICO:
    import shutil
    shutil.copyfile(SALIDA, PUBLICO)
proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "build", "boca3d_modelos", "cara.blend"))
os.makedirs(os.path.dirname(proyecto), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=proyecto)
print("CARA_OK", json.dumps({"bytes": os.path.getsize(SALIDA), "piezas": {
    ob.name: len(ob.data.vertices) for ob in bpy.context.scene.objects}}))
