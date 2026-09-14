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


def puntos_labio(superior, fruncir=0.0, estirar=0.0, comisura=0.0):
    """Los vertices de un labio: arco cerrado, comisuras afinadas y borde
    humedo plano para el sellado. `fruncir` (0..1) junta las comisuras, saca
    el centro hacia delante y engorda; `estirar` (0..1) separa las comisuras,
    afina y retrae un poco. Son las dos shape keys que el visor mezcla desde
    `labios` de la pose (redondeados, muy_redondeados, estirados).

    `comisura` sube (+) o baja (-) los extremos del labio esa distancia, con
    el centro quieto: es la shape key con la que el visor junta las comisuras
    de los dos labios cuando la mandibula baja (el labio de abajo va con ella
    y, sin esto, los labios se separaban del todo en las esquinas). Estirar
    sube un poco las comisuras (sonrisa) y fruncir las baja.

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
        peso = min(1.0, max(0.0, (abs(t) - 0.25) / 0.75))
        peso = peso * peso * (3 - 2 * peso)
        subida = (comisura + 0.08 * estirar - 0.04 * fruncir) * peso
        for j in range(lados):
            a = 2 * math.pi * j / lados
            c, s = math.cos(a), math.sin(a)
            contacto = (s < 0) if superior else (s > 0)
            alto = 0.3 if contacto else (0.24 if superior else 0.31)
            alto *= grosor / 0.3
            # El borde humedo es ancho y plano, no una seccion circular que
            # deja una rendija aparente al ver /p/ ligeramente desde arriba.
            perfil_y = math.copysign(abs(s) ** 0.28, s) if contacto else s
            y = alto * perfil_y * (fin ** 0.16 if contacto else fin) + (cupido * max(0, s) if superior else 0) + subida
            x = arco + grosor * c * fin + adelante
            vertices.append((x, y, ancho * t))
    return vertices


def labio(nombre, superior):
    """El labio con sus dos shape keys (fruncir, estirar) y colores por
    vertice: bermellon en la parte que se ve y piel hacia atras, donde el
    labio entra en la cara, con un borde entre los dos (el visor pinta el
    material con vertexColors sobre base blanca)."""
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
    colores = ob.data.vertex_colors.new(name="bermellon")
    rojo, piel = (0.80, 0.36, 0.40), (0.92, 0.72, 0.62)
    for poligono in ob.data.polygons:
        for indice_bucle in poligono.loop_indices:
            v = ob.data.loops[indice_bucle].vertex_index
            j = v % lados
            a = 2 * math.pi * j / lados
            c = -math.cos(a)                      # +1 delante (-x: lo que se ve), -1 hacia la cara
            f = min(1.0, max(0.0, (c + 0.15) / 0.5))   # de piel (c < -0.15) a rojo (c > 0.35)
            f = f * f * (3 - 2 * f)
            colores.data[indice_bucle].color = (piel[0] + (rojo[0] - piel[0]) * f,
                                                piel[1] + (rojo[1] - piel[1]) * f,
                                                piel[2] + (rojo[2] - piel[2]) * f, 1.0)
    ob.shape_key_add(name="Basis", from_mix=False)
    comisura = ("comisura_abajo", {"comisura": -1.0}) if superior else ("comisura_arriba", {"comisura": 1.0})
    for clave, kw in (("fruncir", {"fruncir": 1.0}), ("estirar", {"estirar": 1.0}), comisura):
        k = ob.shape_key_add(name=clave, from_mix=False)
        for i, (x, y, z) in enumerate(puntos_labio(superior, **kw)):
            k.data[i].co = (x, -z, y)          # la misma conversion de ejes que malla()
    return ob


def perfil(nombre, puntos, grosor, ancho, mat, lejos=1.0):
    """Banda curva de seccion eliptica: conserva abierto el corte sagital.
    `lejos` escala la mitad de la banda del lado contrario a la camara (z<0):
    el menton, que va sobre el borde de la piel lejana, no debe asomar por ella."""
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
            lateral = anchos[i]*math.sin(a)
            vertices.append((x - dy/largo*grosor*math.cos(a),
                             y + dx/largo*grosor*math.cos(a), lateral * (lejos if lateral < 0 else 1.0)))
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
def orientar(vertices, caras, hacia):
    """Da la vuelta a las caras cuya normal no apunta hacia `hacia(centro_de_cara)`."""
    salida = []
    for cara in caras:
        a, b, c = (vertices[i] for i in cara[:3])
        n = ((b[1]-a[1])*(c[2]-a[2]) - (b[2]-a[2])*(c[1]-a[1]),
             (b[2]-a[2])*(c[0]-a[0]) - (b[0]-a[0])*(c[2]-a[2]),
             (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]))
        cx = sum(vertices[i][0] for i in cara) / len(cara)
        cy = sum(vertices[i][1] for i in cara) / len(cara)
        cz = sum(vertices[i][2] for i in cara) / len(cara)
        d = hacia((cx, cy, cz))
        salida.append(cara if n[0]*d[0] + n[1]*d[1] + n[2]*d[2] >= 0 else tuple(reversed(cara)))
    return salida



def nariz(nombre):
    """El caballete de la nariz baja del puente a la punta y vuelve por
    debajo a la base; a cada punto le sale una seccion en medio arco que cae
    hasta la mejilla (la linea del perfil de la cara detras de la nariz),
    asi que de frente y de tres cuartos la nariz es un volumen, no una cinta."""
    espina = [(-2.5, 3.22), (-2.72, 2.95), (-2.9, 2.65), (-3.2, 2.35), (-3.55, 2.05), (-3.62, 1.82),
              (-3.42, 1.66), (-3.15, 1.64), (-2.97, 1.7), (-2.85, 1.35), (-2.82, 1.05), (-2.85, 0.9)]
    anchos = [0.22, 0.26, 0.3, 0.36, 0.44, 0.5, 0.5, 0.48, 0.44, 0.38, 0.34, 0.36]
    # La mejilla detras de cada punto: el borde del perfil de la cara (x = -2,6
    # abajo, retrocediendo hacia el puente), un poco por dentro de la piel.
    mejilla = [(-2.35, y) if y > 2.4 else (-2.45, y) for _, y in espina]
    vertices, caras = [], []
    lados = 12
    for (px, py), (mx, my), w in zip(espina, mejilla, anchos):
        for j in range(lados + 1):
            a = -math.pi / 2 + math.pi * j / lados
            s, c = math.sin(a), math.cos(a)
            vertices.append((px + (mx - px) * (1 - c), py + (my - py) * (1 - c), w * s))
    n = lados + 1
    for i in range(len(espina) - 1):
        for j in range(lados):
            caras.append((i*n + j, i*n + j + 1, (i+1)*n + j + 1, (i+1)*n + j))
    return malla(nombre, vertices, orientar(vertices, caras, lambda c: (-1.0, 0.2, c[2])), PIEL)


nariz("nariz")


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


# Sin aletas ni punta aparte: el cono ya lleva el volumen, y de frente las
# bolas quedaban raras (Central, 14 sep). `elipsoide` queda para otros usos.
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


def arco_encia(nombre, y, radio, retroceso, mat, fuera=None, alto=0.8, adelanto=0.0):
    """Tubo que sigue la arcada. La seccion es eliptica y, con `fuera`, mas
    gruesa hacia los labios que hacia la lengua (la normal del arco apunta
    hacia dentro): asi la encia envuelve el cuello de los dientes sin
    acercarse mas a la lengua, que es lo que mide lengua.py. `adelanto`
    desplaza el arco hacia los labios."""
    vertices, caras = [], []
    pasos, lados = 96, 20
    for i in range(pasos + 1):
        u = -1 + 2 * i / pasos
        x, z = -2.6 + retroceso * u*u - adelanto, 1.35*u
        nx, nz = 1.35, -2*retroceso*u
        norma = math.hypot(nx, nz)
        for j in range(lados):
            a = math.tau*j/lados
            r = radio if (fuera is None or math.cos(a) >= 0) else fuera
            vertices.append((x + r*math.cos(a)*nx/norma,
                             y + radio*alto*math.sin(a), z + r*math.cos(a)*nz/norma))
    for i in range(pasos):
        for j in range(lados):
            a, b = i*lados+j, i*lados+(j+1)%lados
            caras.append((a, b, b+lados, a+lados))
    caras += [tuple(reversed(range(lados))), tuple(pasos*lados+j for j in range(lados))]
    return malla(nombre, vertices, caras, mat)


arco_encia("encia_superior", 0.98, 0.22, 2.3, MUCOSA, fuera=0.34)
arco_encia("encia_inferior", -0.2, 0.22, 2.3, MUCOSA, fuera=0.34)
# El borde gingival: un cordon fino por delante de los cuellos, que hace la
# arcada continua (los dientes salen de la encia, no flotan sobre ella).
arco_encia("encia_borde_sup", 0.8, 0.075, 2.3, MUCOSA, alto=1.0, adelanto=0.2)
arco_encia("encia_borde_inf", -0.02, 0.075, 2.3, MUCOSA, alto=1.0, adelanto=0.2)
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
    bisel.width = 0.09 if incisivo else 0.13
    bisel.segments = 6
    bpy.ops.object.modifier_apply(modifier=bisel.name)
    for v in ob.data.vertices:
        # Corona algo mas estrecha junto a la encia; el borde no es una caja.
        cuello = max(0, (v.co.z if superior else -v.co.z) / 0.25)
        borde = max(0, (-v.co.z if superior else v.co.z) / 0.25)
        v.co.x *= 1 - 0.16*cuello
        v.co.y *= 1 - 0.1*cuello
        if incisivo:
            v.co.x *= 1 - 0.4*borde          # el incisivo se afila hacia el borde cortante
        else:
            v.co.x *= 1 - 0.08*borde         # la corona del molar se cierra un poco arriba
            v.co.y *= 1 - 0.08*borde
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
# El menton: la banda va sobre el borde del perfil de la media cabeza y
# redondea ese borde; estrecha, para no asomar por la piel lejana, que se
# encoge al alejarse del corte.
perfil("menton", [(-2.9, -0.55), (-2.94, -0.95), (-2.64, -1.45),
       (-1.92, -1.98), (-0.8, -2.14), (0.8, -2.06), (2.0, -2.15)],
       0.12, [0.3, 0.36, 0.42, 0.46, 0.48, 0.46, 0.4], PIEL, lejos=0.3)

# --- La media cabeza --------------------------------------------------------
# Lo que cierra la cara de perfil sin cajas: una piel lejana (del lado
# contrario a la camara) que sale del perfil exterior del corte sagital y se
# encoge hacia un centro al alejarse del plano, como media cabeza; las caras
# del corte (tejido cortado, mate) en tres trozos (craneo, maxilar, mandibula)
# que dejan como hueco las cavidades (boca, faringe, nariz); una pared
# interior al fondo de las cavidades; y la misma piel del lado de la camara,
# que el visor pinta translucida. Craneo, maxilar y pared son fijos; el corte
# de la mandibula gira con ella, y la piel se deforma en el visor por pesos.
import mathutils.geometry

CORTE = material("corte", (0.93, 0.74, 0.68), 0.85)
PARED = material("pared", (0.70, 0.42, 0.44), 0.55)
C_CABEZA = (0.6, 0.3)                 # hacia donde se encoge el perfil
W_CABEZA = 3.0                        # media anchura de la cabeza
EXP_CABEZA = 0.5                      # <1: lados mas planos, menos huevo


def muestrear(puntos, paso=0.18):
    """Puntos cada `paso` unidades sobre la polilinea (los vertices originales se conservan)."""
    salida = []
    for (x0, y0), (x1, y1) in zip(puntos, puntos[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / paso))
        for k in range(n):
            f = k / n
            salida.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))
    salida.append(puntos[-1])
    return salida


def piel(nombre, perfil, lado, cerrado, anillos=14, encoger=1.0, tapa=False, excluir=None, hasta_anillo=None):
    """La piel: el perfil (lista de (x, y) en el corte) alejandose del plano
    hacia `lado` (+1 camara, -1 lejos) y encogiendose hacia C_CABEZA.
    `excluir` = (i0, i1) deja sin caras los tramos entre esos indices del
    perfil en los primeros `hasta_anillo` anillos (el hueco que ocupa la
    mandibula, que solo se mueve cerca del corte)."""
    vertices, caras = [], []
    n = len(perfil)
    anillos_total = 14                # los anillos de la cabeza entera: una pieza parcial usa los mismos
    for k in range(anillos + 1):
        th = (math.pi / 2) * (min(k, anillos_total) / anillos_total) * 0.995   # el ultimo anillo, casi en el fondo: la tapa es pequeña y no hace pliegue
        f = math.cos(th) ** EXP_CABEZA * encoger
        z = lado * W_CABEZA * math.sin(th)
        for x, y in perfil:
            vertices.append((C_CABEZA[0] + (x - C_CABEZA[0]) * f, C_CABEZA[1] + (y - C_CABEZA[1]) * f, z))
    tramos = n if cerrado else n - 1
    for k in range(anillos):
        for i in range(tramos):
            j = (i + 1) % n
            if excluir and excluir[0] <= i and j <= excluir[1] and (hasta_anillo is None or k < hasta_anillo):
                continue
            caras.append((k*n + i, k*n + j, (k+1)*n + j, (k+1)*n + i))
    if tapa:
        centro = len(vertices)
        vertices.append((C_CABEZA[0], C_CABEZA[1], lado * W_CABEZA * encoger))
        for i in range(tramos):
            caras.append((anillos*n + i, anillos*n + (i + 1) % n, centro))
    fuera = lambda c: (c[0] - C_CABEZA[0], c[1] - C_CABEZA[1], c[2])
    return malla(nombre, vertices, orientar(vertices, caras, fuera), PIEL)


def placa(nombre, poligono, z, mat, escala=1.0):
    """Una cara plana en el corte (z), mirando a la camara (+z)."""
    puntos = [(C_CABEZA[0] + (x - C_CABEZA[0]) * escala, C_CABEZA[1] + (y - C_CABEZA[1]) * escala, z) for x, y in poligono]
    triangulos = mathutils.geometry.tessellate_polygon([[(x, y, 0.0) for x, y, _ in puntos]])
    caras = orientar(puntos, [tuple(tri) for tri in triangulos], lambda c: (0, 0, 1))
    return malla(nombre, puntos, caras, mat)


# El perfil exterior, en el sentido de las agujas del reloj visto desde la
# camara: corte de arriba, nuca, corte del cuello, garganta, menton (la banda
# «menton» va justo en este borde), detras de los labios y al lado de la nariz.
PERFIL = [(-2.45, 3.25), (3.55, 3.25), (3.55, -2.55), (2.04, -2.55), (2.0, -2.15), (0.8, -2.06), (-0.8, -2.14),
          (-1.92, -1.98), (-2.64, -1.45), (-2.94, -0.95), (-2.9, -0.55), (-2.62, -0.42), (-2.62, 0.9),
          (-2.62, 1.6), (-2.5, 2.4), (-2.45, 3.25)]
perfil = muestrear(PERFIL)
# El craneo es el perfil entero cerrado (con su tapa al fondo) menos el
# tramo de la mandibula.
# La piel es una sola pieza por lado: el visor la deforma (escena.ts,
# `pielQueSigueLaMandibula`) para que el menton y la barbilla acompañen a la
# mandibula sin costuras; una pieza partida dejaba un escalon al abrir.
piel("cabeza_lejana", perfil[:-1], -1, cerrado=True, tapa=True)
piel("cabeza_cercana", perfil[:-1], +1, cerrado=True, tapa=True)

# Las caras del corte: tejido entre la piel y las cavidades.
CORTE_CRANEO = [(-2.45, 3.25), (3.55, 3.25), (3.55, -2.55), (2.78, -2.55), (2.8, -2.5), (2.95, -1.65), (3.08, -0.55),
                (3.16, 0.6), (3.05, 1.55), (2.8, 2.1), (1.8, 2.6), (0.4, 2.8), (-1.4, 2.85), (-2.45, 3.1)]
CORTE_MAXILAR = [(-2.62, 0.45), (-2.62, 1.72), (2.35, 1.72), (2.35, 1.05), (2.05, 1.22), (1.7, 1.32), (1.2, 1.42),
                 (0.6, 1.5), (0.0, 1.52), (-0.6, 1.48), (-1.2, 1.35), (-1.7, 1.15), (-2.05, 0.92), (-2.3, 0.75), (-2.55, 0.5)]
CORTE_MANDIBULA = [(-2.55, -0.05), (-2.62, -0.42), (-2.9, -0.55), (-2.94, -0.95), (-2.64, -1.45), (-1.92, -1.98),
                   (-0.8, -2.14), (0.8, -2.06), (2.0, -2.15), (2.04, -2.5), (2.1, -2.3), (2.2, -1.9), (2.4, -1.5),
                   (2.5, -1.42), (1.32, -1.47), (0.15, -1.51), (-1.02, -1.56), (-2.2, -1.6), (-2.45, -1.3),
                   (-2.5, -0.8), (-2.55, -0.35)]
placa("corte_craneo", CORTE_CRANEO, -0.01, CORTE)
placa("corte_maxilar", CORTE_MAXILAR, -0.01, CORTE)
placa("corte_mandibula", CORTE_MANDIBULA, -0.01, CORTE)
# La pared del fondo de las cavidades (la mejilla por dentro), algo encogida
# para quedar dentro de la piel a esa profundidad.
placa("pared_lejana", PERFIL[:-1], -1.4, PARED, escala=0.9)

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
