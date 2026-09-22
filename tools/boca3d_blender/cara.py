"""Perfil seccionado y labios sobre la cabeza CC0 de MakeHuman.

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
# La cabeza de MakeHuman (CC0, ver recortar_makehuman.py): si esta el OBJ, la
# piel, la nariz y el menton salen de ella; si no, del loft y las bandas de antes.
CABEZA_MH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "makehuman_cabeza.obj")
CON_MH = os.path.exists(CABEZA_MH)


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


if not CON_MH:
    nariz("nariz")


def elipsoide(nombre, centro, escala, mat, segmentos=32):
    """Un elipsoide liso en coordenadas del visor (x, arriba, lateral)."""
    x, arriba, lateral = centro
    ex, earriba, elateral = escala
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segmentos, ring_count=max(6, segmentos // 2), radius=1.0,
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


# La arcada dental: frente plano de incisivos y lados que se abren, como la
# de Bonwill, en vez de una parabola: x = -2,6 + retroceso * |u|^EXPO_ARCO.
# La MISMA curva y la misma tangente viven en lengua.py, medir_roces.py y
# escena.ts (arco / arcoDental): cambiarla aqui es cambiarla en los cuatro.
EXPO_ARCO = 2.6


def arco(u, retroceso=2.3):
    """(x, lateral) del punto u (-1..1) de la arcada."""
    return -2.6 + retroceso * abs(u) ** EXPO_ARCO, 1.35 * u


def tangente_arco(u, retroceso=2.3):
    """dx/du: hacia donde mira un diente en u (giro alrededor del eje vertical)."""
    return retroceso * EXPO_ARCO * abs(u) ** (EXPO_ARCO - 1) * (1 if u >= 0 else -1)


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
        x, z = arco(u, retroceso)
        x -= adelanto
        nx, nz = 1.35, -tangente_arco(u, retroceso)
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
    """Una corona por tipo: incisivos en pala (finos, afilados al borde),
    caninos en punta, premolares con dos cuspides (surco a lo largo de la
    arcada) y molares con cuatro (surcos en cruz). Cubo subdividido, bisel
    solo en las aristas vivas y desplazamientos de vertices."""
    tipo = 'incisivo' if abs(u) < 0.3 else 'canino' if abs(u) < 0.5 else 'premolar' if abs(u) < 0.85 else 'molar'
    profundidad, ancho = {'incisivo': (0.24, 0.34), 'canino': (0.3, 0.34), 'premolar': (0.36, 0.38), 'molar': (0.42, 0.46)}[tipo]
    y = 0.7 if superior else 0.1
    x, z = arco(u)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x, -z, y))
    ob = bpy.context.object
    ob.name = nombre
    ob.scale = (profundidad/2, ancho/2, 0.25)
    ob.rotation_euler.z = -math.atan2(tangente_arco(u), 1.35)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bisel = ob.modifiers.new("corona_redondeada", "BEVEL")
    bisel.width = 0.07 if tipo == 'incisivo' else 0.1
    bisel.segments = 4
    bpy.ops.object.modifier_apply(modifier=bisel.name)
    # Una subdivision despues del bisel (antes, el bisel dejaba caras de area
    # cero entre cortes mas finos que su anchura): da vertices a la cara
    # oclusal para los surcos.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=1)
    bpy.ops.object.mode_set(mode='OBJECT')
    arriba = -1 if superior else 1               # hacia el borde cortante / la cara oclusal
    for v in ob.data.vertices:
        cuello = max(0.0, -arriba * v.co.z / 0.25)   # 1 junto a la encia
        borde = max(0.0, arriba * v.co.z / 0.25)     # 1 en el borde
        v.co.x *= 1 - 0.14*cuello
        v.co.y *= 1 - 0.08*cuello
        if tipo == 'incisivo':
            v.co.x *= 1 - 0.5*borde**1.5             # pala: se afila hacia el borde cortante
            v.co.y *= 1 + 0.06*borde                  # y se ensancha un poco
        elif tipo == 'canino':
            v.co.x *= 1 - 0.55*borde**2               # punta
            v.co.y *= 1 - 0.5*borde**2
        else:
            v.co.x *= 1 - 0.08*borde
            v.co.y *= 1 - 0.08*borde
            if borde > 0.85:                          # la cara oclusal: surcos entre cuspides
                hondo = 0.045 * math.exp(-(v.co.y / 0.07) ** 2)           # surco mesio-distal... a lo ancho
                surco = 0.05 * math.exp(-(v.co.x / 0.06) ** 2)            # surco a lo largo de la arcada (2 cuspides)
                v.co.z -= arriba * (surco + (hondo if tipo == 'molar' else 0.0))
    ob.data.materials.append(ESMALTE)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.use_auto_smooth = True
    ob.data.auto_smooth_angle = math.radians(50)
    normal = ob.modifiers.new("normales_corona", "WEIGHTED_NORMAL")
    bpy.ops.object.modifier_apply(modifier=normal.name)


DIENTES_U = [-0.92, -0.76, -0.6, -0.44, -0.28, -0.1, 0.1, 0.28, 0.44, 0.6, 0.76, 0.92]
for i, u in enumerate(DIENTES_U):
    diente("diente_sup_%02d" % i, u, True)
    diente("diente_inf_%02d" % i, u, False)

# Papilas de la encia: un bulto pequeño entre cada dos dientes, en la linea
# de la encia y algo hacia fuera; el borde gingival pasa por detras.
for i, (u0, u1) in enumerate(zip(DIENTES_U, DIENTES_U[1:])):
    u = (u0 + u1) / 2
    x, z = arco(u)
    tx, tz = tangente_arco(u), 1.35
    norma = math.hypot(tx, tz)
    nx, nz = -tz / norma, tx / norma          # la normal hacia fuera (hacia los labios)
    if nx > 0:
        nx, nz = -nx, -nz
    for superior in (True, False):
        y = 0.8 if superior else -0.02
        elipsoide("papila_%s_%02d" % ('sup' if superior else 'inf', i),
                  (x + nx * 0.16, y, z + nz * 0.16), (0.075, 0.1, 0.09), MUCOSA, segmentos=12)

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
if not CON_MH:
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
BISEL = 0.14                          # radio del borde redondeado del corte sagital


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
    # El borde del corte sagital va redondeado (un cuarto de circulo de radio
    # BISEL desde el plano hacia dentro), no cortado a cuchillo: los primeros
    # anillos giran desde el plano; luego siguen los de la media cabeza.
    anillos_bisel = 4
    escalas = []
    for b in range(anillos_bisel):
        fi = (math.pi / 2) * b / anillos_bisel
        escalas.append((1 - BISEL * (1 - math.cos(fi)) / 3.0, -BISEL * math.sin(fi)))
    for k in range(anillos + 1):
        th = (math.pi / 2) * (min(k, anillos_total) / anillos_total) * 0.995   # el ultimo anillo, casi en el fondo: la tapa es pequeña y no hace pliegue
        escalas.append((math.cos(th) ** EXP_CABEZA, -W_CABEZA * math.sin(th)))
    for f0, z0 in escalas:
        f = f0 * encoger
        z = lado * -z0
        for x, y in perfil:
            vertices.append((C_CABEZA[0] + (x - C_CABEZA[0]) * f, C_CABEZA[1] + (y - C_CABEZA[1]) * f, z))
    anillos += anillos_bisel
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


def placa(nombre, poligono, z, mat, escala=1.0, centro=None, ngon=False):
    """Una cara plana en el corte (z), mirando a la camara (+z). Los puntos
    repetidos y los triangulos sin area (perfiles muestreados) se descartan."""
    limpio = []
    for x, y in poligono:
        if not limpio or math.hypot(x - limpio[-1][0], y - limpio[-1][1]) > 1e-4:
            limpio.append((x, y))
    if len(limpio) > 2 and math.hypot(limpio[0][0] - limpio[-1][0], limpio[0][1] - limpio[-1][1]) <= 1e-4:
        limpio.pop()
    cx, cy = centro if centro else C_CABEZA
    puntos = [(cx + (x - cx) * escala, cy + (y - cy) * escala, z) for x, y in limpio]
    if ngon:
        return malla(nombre, puntos, [tuple(range(len(puntos)))], mat)
    triangulos = mathutils.geometry.tessellate_polygon([[(x, y, 0.0) for x, y, _ in puntos]])
    def area(tri):
        (ax, ay, _), (bx, by, _), (cx, cy, _) = (puntos[i] for i in tri)
        return abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) / 2
    caras = orientar(puntos, [tuple(tri) for tri in triangulos if area(tri) > 1e-8], lambda c: (0, 0, 1))
    return malla(nombre, puntos, caras, mat)


# Las cavidades del corte sagital (las mismas con las dos cabezas): el techo
# de la boca (paladar y nasofaringe), el suelo y la garganta.
PALADAR_CORTE = [(2.35, 1.72), (2.35, 1.05), (2.05, 1.22), (1.7, 1.32), (1.2, 1.42),
                 (0.6, 1.5), (0.0, 1.52), (-0.6, 1.48), (-1.2, 1.35), (-1.7, 1.15), (-2.05, 0.92), (-2.3, 0.75), (-2.55, 0.5)]
FARINGE_CORTE = [(2.78, -2.55), (2.8, -2.5), (2.95, -1.65), (3.08, -0.55), (3.16, 0.6), (3.05, 1.55), (2.8, 2.1),
                 (1.8, 2.6), (0.4, 2.8), (-1.4, 2.85)]
SUELO_CORTE = [(2.04, -2.5), (2.1, -2.3), (2.2, -1.9), (2.4, -1.5), (2.5, -1.42), (1.32, -1.47), (0.15, -1.51),
               (-1.02, -1.56), (-2.2, -1.6), (-2.45, -1.3), (-2.5, -0.8), (-2.55, -0.35), (-2.55, -0.05)]


def cabeza_loft():
    """La media cabeza lofteada desde el perfil del corte (sin MakeHuman)."""
    # El perfil exterior, en el sentido de las agujas del reloj visto desde la
    # camara: corte de arriba, nuca, corte del cuello, garganta, menton (la banda
    # «menton» va justo en este borde), detras de los labios y al lado de la nariz.
    PERFIL = [(-2.45, 3.25), (3.55, 3.25), (3.55, -2.55), (2.04, -2.55), (2.0, -2.15), (0.8, -2.06), (-0.8, -2.14),
              (-1.92, -1.98), (-2.64, -1.45), (-2.94, -0.95), (-2.9, -0.55), (-2.62, -0.42), (-2.62, 0.9),
              (-2.62, 1.6), (-2.5, 2.4), (-2.45, 3.25)]
    perfil = muestrear(PERFIL)
    # La piel es una sola pieza por lado: el visor la deforma (escena.ts,
    # `pielQueSigueLaMandibula`) para que el menton y la barbilla acompañen a la
    # mandibula sin costuras; una pieza partida dejaba un escalon al abrir.
    piel("cabeza_lejana", perfil[:-1], -1, cerrado=True, tapa=True)
    piel("cabeza_cercana", perfil[:-1], +1, cerrado=True, tapa=True)
    # Las caras del corte: tejido entre la piel y las cavidades.
    placa("corte_craneo", [(-2.45, 3.25), (3.55, 3.25), (3.55, -2.55)] + FARINGE_CORTE + [(-2.45, 3.1)], -0.01, CORTE, escala=0.992)
    placa("corte_maxilar", [(-2.62, 0.45), (-2.62, 1.72)] + PALADAR_CORTE, -0.01, CORTE, escala=0.992)
    placa("corte_mandibula", [(-2.55, -0.05), (-2.62, -0.42), (-2.9, -0.55), (-2.94, -0.95), (-2.64, -1.45), (-1.92, -1.98),
                              (-0.8, -2.14), (0.8, -2.06), (2.0, -2.15)] + SUELO_CORTE[:-1], -0.01, CORTE, escala=0.992)
    # La pared del fondo de las cavidades (la mejilla por dentro), algo encogida
    # para quedar dentro de la piel a esa profundidad.
    placa("pared_lejana", PERFIL[:-1], -1.4, PARED, escala=0.9)


# --- La cabeza de MakeHuman ----------------------------------------------------
# Escala y encaje: la linea de los labios de MakeHuman (y 6,63 dm) va a la de
# nuestros labios (y 0,15) y el frente de los labios (z 1,60) al de nuestros
# tubos (x -3,25); 4,4 unidades por decimetro deja la boca con el mismo ancho
# que la arcada. La cara mira a -x, como todo el visor.
ESCALA_MH, MH_BOCA_Y, MH_LABIO_Z = 4.4, 6.63, 1.60
Y_CORTE_ARRIBA, Y_CORTE_ABAJO = 4.0, -2.55


def a_visor(x, y, z):
    return (-(z - MH_LABIO_Z) * ESCALA_MH - 3.25, (y - MH_BOCA_Y) * ESCALA_MH + 0.15, x * ESCALA_MH)


def leer_obj_mh():
    vertices, caras, ojos = [], [], {}
    with open(CABEZA_MH, encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("v "):
                vertices.append(a_visor(*map(float, linea.split()[1:4])))
            elif linea.startswith("f "):
                caras.append([int(p.split("/")[0]) - 1 for p in linea.split()[1:]])
            elif linea.startswith("# joint-"):
                partes = linea[2:].split()
                ojos[partes[0]] = a_visor(*map(float, partes[1:4]))
    return vertices, caras, ojos


def sin_boca_interior(vertices, caras):
    """Quita el saco interior mediante rayos sobre las caras originales;
    conserva la piel exterior y sus anillos labiales conectados."""
    from mathutils.bvhtree import BVHTree
    arbol = BVHTree.FromPolygons(vertices, caras)
    def interior(c):
        centro = tuple(sum(vertices[i][k] for i in c)/len(c) for k in range(3))
        x, y, z = centro
        if not (abs(z) < 2.7 and -1.4 < y < 1.6 and x < 1.4):
            return False
        # Muestreo sobre la cara exacta, sin celdas ni vértices de otra altura.
        for i in c:
            q = tuple(0.9*vertices[i][k]+0.1*centro[k] for k in range(3))
            hit, _, _, _ = arbol.ray_cast((-10, q[1], q[2]), (1, 0, 0))
            if hit is None or q[0] - hit.x < 0.18:
                return False
        return True
    conservadas = [c for c in caras if not interior(c)]
    # El saco puede dejar islotes ocultos: conservar la superficie conectada
    # de la cabeza, sin triángulos sueltos en el interior del corte.
    por_vertice = {}
    for j, c in enumerate(conservadas):
        for i in c:
            por_vertice.setdefault(i, []).append(j)
    pendientes = set(range(len(conservadas)))
    componentes = []
    while pendientes:
        cola = [pendientes.pop()]
        grupo = []
        while cola:
            j = cola.pop()
            grupo.append(j)
            for i in conservadas[j]:
                for k in por_vertice[i]:
                    if k in pendientes:
                        pendientes.remove(k)
                        cola.append(k)
        componentes.append(grupo)
    mayor = max(componentes, key=len)
    return [conservadas[j] for j in sorted(mayor)]


def malla_mh(nombre, vertices, caras, mat):
    """Una malla en coordenadas del visor (como `malla`), con las caras que
    usa `caras` y los vertices renumerados."""
    usados = sorted({i for c in caras for i in c})
    indice = {v: k for k, v in enumerate(usados)}
    ob = malla(nombre, [vertices[i] for i in usados], [tuple(indice[i] for i in c) for c in caras], mat)
    return ob


def recortar(ob, y, arriba, plano=(0, 0, 1)):
    """Corta la malla por un plano con un corte limpio (bisect) y quita lo
    que queda del lado positivo de la normal (`arriba`) o del negativo. Por
    defecto el plano es horizontal a la altura y del visor (en Blender el
    visor (x, y, z) es (x, -z, y): z_blender = y)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    co = (0, 0, y) if plano == (0, 0, 1) else (0, y, 0)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=plano,
                           clear_outer=arriba, clear_inner=not arriba)
    # El corte deja astillas sin area donde una cara ya tocaba el plano.
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def labios_en_piel(ob):
    """Shape keys de los labios sobre la piel de MakeHuman, en coordenadas del
    visor (Blender guarda (x, -lateral, altura)): `fruncir` (/u/, /o/),
    `estirar` (/i/) y `labio_atras` (/f v/). Esculpido procedimental con tres
    zonas: los labios (peso al centro de la boca), el orbicular (un anillo
    alrededor de la boca que arrastra comisuras y surco nasolabial) y la
    mejilla con el pomulo (que se hunde al fruncir y sube y sale al
    estirar). El visor las mezcla desde el largo de los labios de la pose,
    como hacia con los tubos."""
    ob.shape_key_add(name="Basis", from_mix=False)
    base = [(v.co.x, v.co.z, -v.co.y) for v in ob.data.vertices]      # (x, altura, lateral) del visor

    def suave(t):
        t = max(0.0, min(1.0, t))
        return t * t * (3 - 2 * t)

    def peso_boca(x, y, z, rx=1.1, ry=0.95, rz=1.7):
        """1 en el centro de la boca, 0 a un radio (elipsoide) de distancia."""
        d = math.sqrt(((x + 3.1) / rx) ** 2 + ((y - 0.15) / ry) ** 2 + (z / rz) ** 2)
        return suave(1 - d)

    def anillo(x, y, z, r0=1.05, ancho=0.65):
        """El orbicular de los labios: un anillo alrededor de la boca (en el
        plano de la cara) a distancia r0 del centro, solo en la piel de delante."""
        d = math.sqrt(((y - 0.15) / 1.0) ** 2 + (z / 1.35) ** 2)
        return suave(1 - abs(d - r0) / ancho) * suave((x + 1.0) / -1.2)

    def mejilla(x, y, z):
        """La mejilla y el pomulo: a los lados de la nariz, sobre la boca."""
        d = math.sqrt(((x + 1.9) / 1.0) ** 2 + ((y - 0.7) / 1.0) ** 2 + ((abs(z) - 2.0) / 0.9) ** 2)
        return suave(1 - d)

    def clave(nombre, delta):
        k = ob.shape_key_add(name=nombre, from_mix=False)
        for i, (x, y, z) in enumerate(base):
            dx, dy, dz = delta(x, y, z)
            k.data[i].co = (x + dx, -(z + dz), y + dy)

    abre = lambda y: (1.0 if y > 0.15 else -1.0) * max(0.0, 1 - abs(y - 0.15) / 0.5)
    lado = lambda z: (1.0 if z > 0 else -1.0)

    def fruncir(x, y, z):
        # Los labios salen hacia delante y se separan un poco en el centro (la
        # «o»); el orbicular tira de toda la piel de alrededor hacia el eje de
        # la boca (comisuras y surco nasolabial hacia dentro y hacia delante);
        # las mejillas se hunden un poco hacia la boca.
        b = peso_boca(x, y, z)
        a = anillo(x, y, z)
        m = mejilla(x, y, z)
        return (-0.75 * b - 0.3 * a + 0.1 * m,
                0.13 * abre(y) * peso_boca(x, y, z, 0.8, 0.6, 0.9) - 0.3 * (y - 0.15) * a,
                -0.5 * z * b - 0.35 * z * a - 0.16 * lado(z) * m)

    def estirar(x, y, z):
        # Las comisuras se separan y suben, los labios se pegan a los dientes,
        # el orbicular se abre y las mejillas suben y salen (los pomulos de /i/).
        b = peso_boca(x, y, z)
        a = anillo(x, y, z)
        m = mejilla(x, y, z)
        return (0.2 * b + 0.05 * a - 0.2 * m,
                0.1 * b * min(1.0, abs(z) / 1.2) + 0.06 * a + 0.14 * m,
                0.45 * z * b + 0.18 * z * a + 0.06 * lado(z) * m)

    clave("fruncir", fruncir)
    clave("estirar", estirar)
    abajo = lambda y: max(0.0, min(1.0, (0.15 - y) / 0.08))
    clave("labio_atras", lambda x, y, z: (0.32 * peso_boca(x, y, z, 0.9, 0.6, 1.4) * abajo(y),
                                          0.14 * peso_boca(x, y, z, 0.9, 0.6, 1.4) * abajo(y), 0.0))

    def peso_labial(x, y, z):
        # Banda completa, incluidas comisuras: no una campana solo central.
        frente = -3.15 + 0.5 * z * z
        return suave((frente + 0.48 - x) / 0.18) * (1 - suave((abs(z) - 0.95) / 0.30)) * (1 - suave((abs(y - 0.15) - 0.20) / 0.50))

    def linea_labial(z):
        # Contornos del bermellon de la base CC0, muestreados en el piloto.
        lateral = min(1.0, abs(z) / 1.05)
        superior = 0.149 + 0.055 * math.sin(math.pi * lateral)
        inferior = 0.054 + 0.065 * lateral
        return superior, inferior, (superior + inferior) / 2

    def peso_mandibula(x, y, z):
        # Misma transformacion de pielQueSigueLaMandibula en escena.ts.
        bajo = suave((0.45 - y) / 1.35)
        frente = suave((-1.6 - x) / 0.8) * (1 - suave((abs(z) - 0.85) / 0.5))
        bajo += (suave((0.2 - y) / 0.1) - bajo) * frente
        return bajo * suave((2.3 - x) / 0.9)

    def cierre(x, y, z):
        w = peso_labial(x, y, z)
        superior, inferior, contacto = linea_labial(z)
        borde = superior if y >= contacto else inferior
        objetivo = contacto + 0.88 * (y - borde) + (-0.025 if y >= contacto else 0.025)
        # El morfo se suma DESPUES del giro ponderado de la piel. Compensa
        # ese giro para mantener el sello en toda la linea, no solo al centro.
        a = 0.08 * 0.42 * peso_mandibula(x, y, z)
        mandibula_y = 0.9 + (x - 2.6) * math.sin(a) + (y - 0.9) * math.cos(a)
        # Llevar el borde al frente del bermellon: cerrar solo en altura
        # hundia la sutura entre dos crestas y duplicaba el surco oscuro.
        sutura = math.exp(-((y - borde) / 0.14) ** 2)
        frente_contacto = -3.36 + 0.5 * z * z
        dx = (-0.045 + min(0.0, frente_contacto - x) * sutura) * w
        return (dx, (objetivo - mandibula_y) * w, 0.0)

    clave("cierre_labios", cierre)
    # Compresion separada del contacto: /m/ mantiene el sello con menos
    # presion que /p b/. El visor interpola ambos con los tiempos congelados.
    def compresion(x, y, z):
        superior, inferior, contacto = linea_labial(z)
        borde = superior if y >= contacto else inferior
        w = peso_labial(x, y, z)
        return (-0.025 * w, -0.08 * (y - borde) * w, 0.0)

    clave("compresion_labios", compresion)


def pared_por_corte(ob, nombre, z):
    """La pared del fondo a la profundidad z del visor: la seccion EXACTA de
    la piel en ese plano, rellena con bmesh (triangle_fill sobre las aristas
    del corte). Un contorno muestreado y teselado dejaba huecos."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # Lateral del visor z = -y de Blender: el plano y = -z.
    # Se quita el lado de la camara: las aristas del corte quedan como borde
    # (con las dos mitades, triangle_fill no rellenaba nada).
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0.0, -z, 0.0),
                           plane_no=(0.0, 1.0, 0.0), clear_outer=False, clear_inner=True)
    aristas = [e for e in bm.edges if e.is_boundary and all(abs(v.co.y + z) < 1e-4 for v in e.verts)]
    relleno = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=aristas)
    nuevas = {g for g in relleno["geom"] if isinstance(g, bmesh.types.BMFace)}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in nuevas], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    datos = bpy.data.meshes.new(nombre)
    bm.to_mesh(datos)
    bm.free()
    datos.update()
    pieza = bpy.data.objects.new(nombre, datos)
    bpy.context.collection.objects.link(pieza)
    datos.materials.append(PARED)
    return pieza


def centroide(poligono):
    return (sum(x for x, _ in poligono) / len(poligono), sum(y for _, y in poligono) / len(poligono))


def contorno_a_profundidad(ob, z):
    """El contorno de la piel en el plano lateral z del visor (Blender
    y = -z): se corta una copia con bisect y se ordenan los vertices del
    plano en dos ramas (cara y nuca) por altura, como el perfil sagital."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, -z, 0), plane_no=(0, 1, 0),
                           clear_outer=False, clear_inner=False)
    puntos = [(v.co.x, v.co.z) for v in bm.verts if abs(v.co.y + z) < 1e-3]
    bm.free()
    if len(puntos) < 8:
        return None
    ys = [y for _, y in puntos]
    y0, y1 = min(ys) + 0.05, max(ys) - 0.05
    def rama(elegir, de_cara):
        # Solo los puntos de esa rama (cara: x < 1,5; nuca: el resto): la nuca
        # de MakeHuman es de malla gruesa y en las alturas sin puntos de nuca el
        # maximo era un punto de la cuenca del ojo, y la pared salia rota.
        por_y = {}
        for x, y in puntos:
            if (x < 1.5) != de_cara:
                continue
            k = round(y, 1)
            por_y[k] = elegir(por_y.get(k, x), x)
        return sorted(por_y.items())
    cara_, nuca_ = rama(min, True), rama(max, False)
    if not cara_ or not nuca_:
        return None
    def en(ramita, y):
        if y <= ramita[0][0]:
            return ramita[0][1]
        for (ya, xa), (yb, xb) in zip(ramita, ramita[1:]):
            if y <= yb:
                return xa + (xb - xa) * (y - ya) / (yb - ya) if yb > ya else xb
        return ramita[-1][1]
    pasos = 40
    alturas = [y0 + (y1 - y0) * k / pasos for k in range(pasos + 1)]
    def suavizada(ramita):
        xs = [en(ramita, y) for y in alturas]
        # Media movil de cinco: la cuenca del ojo y las mallas gruesas dejaban
        # dientes de sierra en el contorno, que se veian por la cavidad nasal.
        return [sum(xs[max(0, k - 2):k + 3]) / len(xs[max(0, k - 2):k + 3]) for k in range(len(xs))]
    cara_x, nuca_x = suavizada(cara_), suavizada(nuca_)
    # Las dos ramas no se cruzan (en la cuenca del ojo o en los extremos
    # podian hacerlo y el poligono se autocortaba: la teselacion dejaba
    # huecos que se veian por la cavidad nasal como cuñas oscuras).
    nuca_x = [max(n, c + 0.15) for c, n in zip(cara_x, nuca_x)]
    return [(x, y) for x, y in zip(cara_x, alturas)] + [(x, y) for x, y in reversed(list(zip(nuca_x, alturas)))]


def acabado_piel(ob, ojos):
    """Bermellón integrado y párpados relajados sobre la topología CC0."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    def perioral(v):
        return abs(v.co.y) < 1.45 and -0.55 < v.co.z < 0.68 and v.co.x < -2.35
    aristas = [e for e in bm.edges if all(perioral(v) for v in e.verts)]
    bmesh.ops.subdivide_edges(bm, edges=aristas, cuts=1, use_grid_fill=True, smooth=0.35)
    bm.to_mesh(ob.data)
    bm.free()
    for v in ob.data.vertices:
        x, y, z = v.co.x, v.co.z, -v.co.y
        for ox, oy, oz in ojos.values():
            d = ((z - oz) / 0.95) ** 2 + ((y - oy) / 0.82) ** 2
            if x < ox and d < 1:
                v.co.z -= 0.20 * (y - oy) * (1 - d) ** 2
    colores = ob.data.vertex_colors.new(name="piel_bermellon")
    for bucle in ob.data.loops:
        v = ob.data.vertices[bucle.vertex_index].co
        x, y, z = v.x, v.z, -v.y
        ancho = max(0, 1 - (z / 1.2) ** 2)
        centro = 0.12 + 0.035 * math.sin(math.pi * min(1, abs(z)))
        alto = 0.24 * ancho ** 0.6 + 0.025
        f = max(0, min(1, (alto - abs(y - centro)) / 0.065))
        f *= max(0, min(1, (-2.7 + 0.45 * z*z - x) / 0.25))
        # Colores lineales; variación suave, sin maquillaje ni ruido pintado.
        piel, labio = (0.78, 0.57, 0.46), (0.57, 0.25, 0.24)
        colores.data[bucle.index].color = tuple(a + (b-a)*f for a,b in zip(piel,labio)) + (1,)
    ob.data.update()
    # Normales comunes en el plano medio: las dos mitades no se solapan.
    normales = []
    for v in ob.data.vertices:
        n = v.normal.copy()
        if abs(v.co.y) < 1e-5:
            n.y = 0
            n.normalize()
        normales.append(tuple(n))
    ob.data.use_auto_smooth = True
    ob.data.normals_split_custom_set_from_vertices(normales)


def cabeza_makehuman():
    vertices, caras, ojos = leer_obj_mh()
    # Conservar los anillos originales: el filtro por celdas arrancaba también
    # piel exterior de nariz, comisuras y mentón y dejaba bordes dentados.
    caras = sin_boca_interior(vertices, caras)
    # La mitad lejana se corta por el plano sagital con bisect (quedarse solo
    # con las caras enteras dejaba una franja sin piel por el centro de la
    # cara, donde las caras cruzan el plano). Lateral del visor = -y en Blender.
    ob = malla_mh("cabeza_lejana", vertices, caras, PIEL)
    # Mitades complementarias sin solapamiento. El detalle frontal no dibuja
    # planos de corte; no hace falta taparlos duplicando piel sobre el centro.
    recortar(ob, 0, arriba=True, plano=(0, -1, 0))
    recortar(ob, Y_CORTE_ARRIBA, arriba=True)
    recortar(ob, Y_CORTE_ABAJO, arriba=False)
    acabado_piel(ob, ojos)
    ob["labios_en_piel"] = 1                  # el visor esconde sus tubos de labios
    labios_en_piel(ob)
    # Segunda mitad del original, con el mismo acabado y deformaciones.
    espejo = malla_mh("cabeza_cercana", vertices, caras, PIEL)
    recortar(espejo, 0, arriba=False, plano=(0, -1, 0))
    recortar(espejo, Y_CORTE_ARRIBA, arriba=True)
    recortar(espejo, Y_CORTE_ABAJO, arriba=False)
    acabado_piel(espejo, ojos)
    labios_en_piel(espejo)
    # El perfil del corte: por cada altura, el punto mas adelantado (la cara) y
    # el mas atrasado (la nuca) de los vertices que quedan en el plano.
    seam = [(v.co.x, v.co.z) for v in ob.data.vertices if abs(v.co.y) < 1e-3]
    # Dos ramas: la cara (x < 1,5) y la nuca; cada una, ordenada por altura e
    # interpolada en alturas regulares (la nuca del cuello tiene pocos vertices).
    def rama(puntos, elegir):
        por_y = {}
        for x, y in puntos:
            k = round(y, 2)
            por_y[k] = elegir(por_y.get(k, x), x)
        return sorted(por_y.items())
    cara_ = rama([(x, y) for x, y in seam if x < 1.5], min)
    nuca_ = rama([(x, y) for x, y in seam if x >= 1.5], max)
    def en(ramita, y):
        if y <= ramita[0][0]:
            return ramita[0][1]
        for (y0, x0), (y1, x1) in zip(ramita, ramita[1:]):
            if y <= y1:
                return x0 + (x1 - x0) * (y - y0) / (y1 - y0) if y1 > y0 else x1
        return ramita[-1][1]
    pasos = 66
    frente, nuca = [], []
    for k in range(pasos + 1):
        y = Y_CORTE_ABAJO + (Y_CORTE_ARRIBA - Y_CORTE_ABAJO) * k / pasos
        frente.append((en(cara_, y), y))
        nuca.append((en(nuca_, y), y))
    def frente_entre(y0, y1):
        """Puntos del frente con y0 <= y <= y1, de abajo arriba."""
        return [(x, y) for x, y in frente if y0 - 1e-6 <= y <= y1 + 1e-6]
    def x_frente(y):
        i = min(range(len(frente)), key=lambda k: abs(frente[k][1] - y))
        return frente[i][0]
    Y_BOCA, Y_NARIZ, Y_PUENTE = 0.15, 1.55, 3.35
    # Craneo y nuca: de la frente arriba, por la nuca abajo hasta el cuello, y
    # por dentro la pared de la faringe y el techo nasal hasta el puente.
    # Un solo lazo sin cruces: nuca de arriba abajo -> faringe de abajo arriba
    # -> techo nasal -> la frente subiendo del puente al corte de arriba.
    craneo = list(reversed(nuca)) + FARINGE_CORTE + [(-2.5, 3.0), (x_frente(Y_PUENTE), Y_PUENTE)] + frente_entre(Y_PUENTE, Y_CORTE_ARRIBA)
    # La nariz: su perfil entre la base y el puente, cerrada por detras.
    nariz_corte = [(x_frente(Y_NARIZ), Y_NARIZ)] + frente_entre(Y_NARIZ, Y_PUENTE) + [(-2.5, 3.0), (-2.5, 1.72), (-2.55, 1.6)]
    # Maxilar: del labio superior (linea de la boca) a la base de la nariz por
    # delante; el paladar y la nasofaringe por dentro.
    # D4.4b v4: la seccion de cada labio va aparte, del color del labio y con
    # las MISMAS shape keys que la piel (los campos de `labios_en_piel` se
    # evaluan sobre sus vertices): en el corte sagital cada labio es un
    # volumen que se mueve con la boca, no la lamina roja de la piel vista de
    # canto sobre hueso. El de arriba llega hasta la base del filtrum; el de
    # abajo, hasta el surco mentolabial; por dentro, hasta el hueso alveolar.
    Y_LABIO_SUP, Y_LABIO_INF = Y_BOCA + 0.7, -0.35
    labio_sup = [(-2.62, Y_BOCA), (x_frente(Y_BOCA), Y_BOCA)] + frente_entre(Y_BOCA, Y_LABIO_SUP) + [(-2.62, Y_LABIO_SUP)]
    labio_inf = [(-2.55, Y_LABIO_INF), (x_frente(Y_LABIO_INF), Y_LABIO_INF)] + frente_entre(Y_LABIO_INF, Y_BOCA) + [(-2.55, -0.05)]
    maxilar = ([(-2.62, Y_LABIO_SUP), (x_frente(Y_LABIO_SUP), Y_LABIO_SUP)] + frente_entre(Y_LABIO_SUP, Y_NARIZ)
               + [(-2.55, 1.6), (-2.5, 1.72)] + PALADAR_CORTE + [(-2.6, 0.45)])
    # Mandibula: del labio inferior al cuello por delante, el corte del cuello,
    # la garganta y el suelo de la boca por dentro.
    mandibula = list(reversed(frente_entre(Y_CORTE_ABAJO, Y_LABIO_INF))) + [(2.04, Y_CORTE_ABAJO)] + SUELO_CORTE[:-1]
    placa("corte_craneo", craneo, -0.01, CORTE)
    placa("corte_nariz", nariz_corte, -0.01, CORTE)
    placa("corte_maxilar", maxilar, -0.01, CORTE)
    placa("corte_mandibula", mandibula, -0.01, CORTE)
    for nombre, poligono in (("corte_labio_sup", labio_sup), ("corte_labio_inf", labio_inf)):
        labios_en_piel(placa(nombre, poligono, -0.01, LABIOS))
    # Las paredes del fondo de las cavidades, a tres profundidades (de tres
    # cuartos, a traves de la mitad translucida, se veia el reves oscuro de
    # la piel y la cabeza parecia hueca). Cada una con el contorno REAL de la
    # piel a esa profundidad, encogido un poco: con el perfil sagital encogido
    # asomaban por la sien y el angulo de la mandibula como dientes de sierra.
    for nombre, z in (("pared_lejana", -1.3), ("pared_lejana_2", -2.1), ("pared_lejana_3", -2.8)):
        contorno = contorno_a_profundidad(ob, z)
        if contorno:
            # Un solo poligono (n-gon): la teselacion de Blender al exportar
            # aguanta los contornos concavos; tessellate_polygon dejaba huecos.
            placa(nombre, contorno, z, PARED, escala=0.90, centro=centroide(contorno), ngon=True)
    # El ojo del lado lejano: globo blanco e iris oscuro; el hueco de la cuenca
    # de MakeHuman queda cubierto.
    x, y, z = ojos["joint-r-eye"] if ojos["joint-r-eye"][2] < 0 else ojos["joint-l-eye"]
    elipsoide("ojo_lejano", (x, y, z), (0.62, 0.62, 0.62), ESMALTE, segmentos=20)
    elipsoide("iris_lejano", (x - 0.42, y, z), (0.22, 0.27, 0.27), HUESO, segmentos=16)
    elipsoide("ojo_cercano", (x, y, -z), (0.62, 0.62, 0.62), ESMALTE, segmentos=20)
    elipsoide("iris_cercano", (x - 0.42, y, -z), (0.22, 0.27, 0.27), HUESO, segmentos=16)
    print("MH_OK", {"vertices_lejana": len(ob.data.vertices), "caras_quitadas": len(caras), "frente": frente[::11], "nuca": nuca[::11]})


if CON_MH:
    cabeza_makehuman()
else:
    cabeza_loft()


def comprobar_labios_dientes():
    """Intersecciones de triangulos: labios deformados frente a las coronas.

    Muestrea la transicion reposo-cierre a cinco fracciones, y las dos
    compresiones del piloto. No sustituye la revision visual del sello.
    """
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector

    def suave(t):
        t = min(1.0, max(0.0, t))
        return t * t * (3 - 2 * t)

    def rotar(v, angulo):
        x, lat, y = v
        c, s = math.cos(angulo), math.sin(angulo)
        return Vector((2.6 + (x - 2.6) * c - (y - 0.9) * s, lat,
                       0.9 + (x - 2.6) * s + (y - 0.9) * c))

    comprobaciones, max_heredadas = 0, 0
    for cierre in [0, 0.25, 0.5, 0.75, 1]:
        angulo = (0.2 - 0.12 * cierre) * 0.42
        dientes = []
        for diente in bpy.context.scene.objects:
            if not diente.name.startswith('diente_'):
                continue
            puntos = [diente.matrix_world @ v.co for v in diente.data.vertices]
            if diente.name.startswith('diente_inf_'):
                puntos = [rotar(v, angulo) for v in puntos]
            dientes.append(BVHTree.FromPolygons(puntos, [list(p.vertices) for p in diente.data.polygons]))
        for presion in [1.0, 0.35]:
            for nombre in ['cabeza_lejana', 'cabeza_cercana']:
                ob = bpy.data.objects[nombre]
                claves = ob.data.shape_keys.key_blocks
                base = claves['Basis'].data
                puntos, puntos_antes, activos = [], [], set()
                for i, p in enumerate(base):
                    x, lat, y = p.co
                    bajo = suave((0.45-y)/1.35)
                    frente = suave((-1.6-x)/0.8) * (1-suave((abs(lat)-0.85)/0.5))
                    peso = (bajo + (suave((0.2-y)/0.1)-bajo)*frente) * suave((2.3-x)/0.9)
                    v = rotar(p.co, angulo*peso)
                    puntos_antes.append(v + 0.08*cierre*(claves['fruncir'].data[i].co-p.co))
                    for clave, valor in [('cierre_labios', cierre), ('compresion_labios', presion*cierre), ('fruncir', 0.08*cierre*(1-cierre))]:
                        delta = claves[clave].data[i].co - p.co
                        v += valor * delta
                        if clave == 'cierre_labios' and delta.length > 0.002:
                            activos.add(i)
                    puntos.append(v)
                caras = [list(p.vertices) for p in ob.data.polygons if any(i in activos for i in p.vertices)]
                piel = BVHTree.FromPolygons(puntos, caras)
                antes = BVHTree.FromPolygons(puntos_antes, caras)
                nuevos = 0
                heredadas = 0
                for d in dientes:
                    anteriores = set(antes.overlap(d))
                    actuales = set(piel.overlap(d))
                    if actuales - anteriores:
                        print('ROCE_NUEVO', cierre, nombre, [[tuple(round(c, 4) for c in base[i].co) for i in caras[a]] for a, b in actuales - anteriores])
                    nuevos += len(actuales - anteriores)
                    heredadas += len(actuales & anteriores)
                assert nuevos == 0, ('labios-dientes-nuevos', cierre, presion, nombre, nuevos)
                max_heredadas = max(max_heredadas, heredadas)
                comprobaciones += 1
    print('LABIOS_DIENTES_OK', {'comprobaciones': comprobaciones, 'intersecciones_nuevas': 0,
                              'max_pares_heredados_en_borde_de_banda': max_heredadas})


if CON_MH:
    comprobar_labios_dientes()

for ob in bpy.context.scene.objects:
    assert all(math.isfinite(c) for v in ob.data.vertices for c in v.co)
    assert all(p.area > 1e-10 for p in ob.data.polygons), ob.name

bpy.ops.export_scene.gltf(filepath=os.path.abspath(SALIDA), export_format="GLB", export_yup=True,
                          export_materials="EXPORT", export_morph=True, export_morph_normal=False, export_extras=True)
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
