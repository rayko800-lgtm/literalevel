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


# --- Dientes, encias y hueso, igual que arcoDental/tuboArco en escena.ts -----
# Coordenadas de escena con la boca cerrada: x delante/atras, `alto` arriba,
# `lat` lateral. En Blender el vertice es (x, y=lat, z=alto); los arcos son
# simetricos, asi que el signo del lateral no importa. Medidas de entrega-4e.

MEDIO_ANCHO = 1.35
DIENTES_U = [-0.92, -0.76, -0.6, -0.44, -0.28, -0.1, 0.1, 0.28, 0.44, 0.6, 0.76, 0.92]


EXPO_ARCO = 2.6                 # la arcada de cara.py: frente plano, lados abiertos


def arco(u, retroceso=2.3):
    return -2.6 + retroceso * abs(u) ** EXPO_ARCO, MEDIO_ANCHO * u


def tangente_arco(u, retroceso=2.3):
    return retroceso * EXPO_ARCO * abs(u) ** (EXPO_ARCO - 1) * (1 if u >= 0 else -1)


def pen_tubo(x, alto, lat, y0, r, retroceso=2.3):
    """Cuanto entra el punto en un tubo que sigue el arco (positivo = dentro)."""
    mejor = 9.0
    for k in range(-30, 31):
        cx, cz = arco(k / 30, retroceso)
        mejor = min(mejor, math.hypot(x - cx, alto - y0, lat - cz))
    return r - mejor


def pen_diente(x, alto, lat, u, y_centro):
    """Cuanto entra el punto en la caja de un diente (positivo = dentro)."""
    cx, cz = arco(u)
    # Cajas por tipo de corona (cara.py): incisivo, canino, premolar, molar.
    w, d = (0.34, 0.24) if abs(u) < 0.3 else (0.34, 0.3) if abs(u) < 0.5 else (0.38, 0.36) if abs(u) < 0.85 else (0.46, 0.42)
    h = 0.5
    ang = -math.atan2(tangente_arco(u), MEDIO_ANCHO)
    dx, dz = x - cx, lat - cz
    lx = dx * math.cos(ang) + dz * math.sin(ang)
    lz = -dx * math.sin(ang) + dz * math.cos(ang)
    return min(d / 2 - abs(lx), h / 2 - abs(alto - y_centro), w / 2 - abs(lz))


def pen_superior(x, alto, lat):
    """Arco superior: encia (tubo y 0,98 r 0,2) y dientes (centro y 0,7)."""
    if alto < 0.3 or (abs(lat) < 0.5 and x > -2.2):        # lejos del arco: no hay nada que medir
        return -9.0
    p = pen_tubo(x, alto, lat, 0.98, 0.2)
    for u in DIENTES_U:
        p = max(p, pen_diente(x, alto, lat, u, 0.7))
    return p


def pen_inferior(x, alto, lat):
    """Mandibula: encia (y -0,2 r 0,2), hueso (y -0,62 r 0,28, retroceso 2,6) y dientes (centro y 0,1)."""
    if alto > 0.5 or (abs(lat) < 0.5 and alto > -0.25 and x > -2.2):
        return -9.0
    p = max(pen_tubo(x, alto, lat, -0.2, 0.2), pen_tubo(x, alto, lat, -0.62, 0.28, 2.6))
    for u in DIENTES_U:
        p = max(p, pen_diente(x, alto, lat, u, 0.1))
    return p


def empujar_fuera(x, lat, alto, muestras=(0.0,)):
    """Saca el vertice de dientes y encias: hacia la linea media si es el arco
    (lo que roza son los bordes laterales) y hacia arriba si es el hueso.
    `muestras` son desplazamientos en x que otra shape key puede sumar."""
    for _ in range(30):
        if max(pen_superior(x + d, alto, lat) for d in muestras) > -HOLGURA and abs(lat) > 0.02:
            lat -= math.copysign(0.02, lat)
        elif max(pen_inferior(x + d, alto, lat) for d in muestras) > -HOLGURA:
            if abs(lat) > 0.45:
                lat -= math.copysign(0.02, lat)
            else:
                alto += 0.02
        else:
            break
    return lat, alto


# --- Forma base --------------------------------------------------------------

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=72, ring_count=36, radius=1.0)
ob = bpy.context.active_object
ob.name = "lengua"
ob.data.name = "lengua"
bpy.ops.object.shade_smooth()

LARGO, ANCHO, ALTO = 2.2, 1.0, 0.42   # semiejes
CENTRO = (0.2, 0.0, -0.45)            # la punta queda en x=-2.0, la raiz en 2.4
PUNTA_N = 3.2


def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rampa(x, a, b):
    return suave((x - a) / (b - a))


def campana(x, c, w):
    return math.exp(-((x - c) / w) ** 2)


for v in ob.data.vertices:
    ux, uy, uz = v.co.x, v.co.y, v.co.z          # en la esfera unidad
    if ux < 0:
        # D4.4b v4: punta roma (superelipse, N=3,2) en vez del apice de un
        # elipsoide. A 0,2 del apice la seccion conserva ~el 90 % del grosor de
        # la lamina: la punta se redondea, no se afila (lamina y punta 11-14 mm).
        rho = math.sqrt(max(0.0, 1 - ux * ux))
        ux = -(1 - rho ** PUNTA_N) ** (1 / PUNTA_N)
    x, y, z = ux * LARGO, uy * ANCHO, uz * ALTO
    # Piloto D4.4b: punta redondeada con espesor, no una lamina.
    # Se conserva la topologia; el ensanchamiento acaba en el predorso.
    f = 0.76 + 0.24 * rampa(x, -2.2, -0.3)
    y *= f
    z *= 0.92 + 0.08 * rampa(x, -2.2, -0.9)
    # Seccion con bordes: arriba plano y las esquinas marcadas, abajo mas redondo.
    lateral = abs(uy)
    if z > 0:
        z *= 0.55 + 0.45 * (1 - lateral ** 2.2)        # la cara de arriba, plana y de bordes redondeados
        z += 0.03 * campana(lateral, 0.78, 0.16) * rampa(x, -1.8, -0.8)   # el borde lateral, suave
        z -= 0.05 * campana(y, 0.0, 0.16) * rampa(x, -1.6, -0.6) * (1 - rampa(x, 1.2, 2.2))  # surco
    # La raiz baja hacia el suelo de la boca y engorda: no queda flotando.
    z *= 1 + 0.35 * rampa(x, 0.3, 2.1)
    z -= 0.55 * rampa(x, 0.35, 2.4)
    y *= 1 + 0.28 * rampa(x, 0.3, 2.0)
    v.co = (x + CENTRO[0], y + CENTRO[1], z + CENTRO[2])

# La forma base tampoco roza dientes ni encias.
for v in ob.data.vertices:
    x, y, z = v.co
    y, z = empujar_fuera(x, y, z)
    v.co = (x, y, z)

base = [tuple(v.co) for v in ob.data.vertices]

# --- Shape keys: una por parametro, recortadas contra el techo --------------

ob.shape_key_add(name="Basis", from_mix=False)
CLAVES = {}


def clave(nombre, delta, velo_abierto=False, toca=False, margen_x=(0.0, 0.0), libre=False):
    """`delta(x, y, z) -> (dx, dy, dz)` sobre la forma base; el resultado no
    entra en el techo (salvo la holgura de un toque, si `toca`). `margen_x`
    recorta tambien contra el techo desplazado, porque otra shape key
    (cuerpo_delante, cuerpo_atras) puede mover la lengua en x a la vez.

    `libre` (D4.4b v4): sin recorte por vertice. El recorte se hace con la
    boca CERRADA, pero /θ ð/ se dicen con la mandibula abierta (0,36): contra
    ese techo y esos incisivos la punta quedaba aplastada y arrugada. Una
    clave libre tiene que caber por su propia forma; la comprobacion por pose
    de abajo (con el giro real de la mandibula) es la que la valida."""
    k = ob.shape_key_add(name=nombre, from_mix=False)
    deltas = []
    muestras = [margen_x[0] + (margen_x[1] - margen_x[0]) * j / 4 for j in range(5)]
    for i, (x, y, z) in enumerate(base):
        dx, dy, dz = delta(x, y, z)
        nx, nz = x + dx, z + dz
        if libre:
            # Los dientes de abajo giran con la lengua: en coordenadas locales
            # valen. Solo se aparta de lado (los bordes de la lamina sobre los
            # premolares); nunca hacia arriba, que es lo que aplastaba la punta.
            ny = y + dy
            for _ in range(30):
                if pen_inferior(nx, nz, ny) > -HOLGURA and abs(ny) > 0.45:
                    ny -= math.copysign(0.02, ny)
                else:
                    break
            k.data[i].co = (nx, ny, nz)
            deltas.append((dx, ny - y, dz))
            continue
        tope = min(techo(nx + d, velo_abierto) for d in muestras) - (-TOLERANCIA_TOQUE if toca else HOLGURA)
        if nz > tope:
            nz = tope
        ny = y + dy
        # Tambien la punta interdental: pasa entre los incisivos por encima de
        # los de abajo y por debajo de los de arriba, asi que el empuje no la
        # toca; lo que rozaba eran los bordes de la lamina contra los
        # premolares de abajo en /θ ð/ (medido por entrega-4e).
        ny, nz = empujar_fuera(nx, ny, nz, muestras)
        k.data[i].co = (nx, ny, nz)
        deltas.append((nx - x, ny - y, nz - z))
    CLAVES[nombre] = deltas
    return k


punta_w = lambda x: 1 - rampa(x, -2.0, -0.6)
cuerpo_w = lambda x: campana(x, 0.1, 1.3)
dorso_w = lambda x: campana(x, 1.45, 1.05)
raiz_w = lambda x: rampa(x, 0.8, 2.4)
arriba = lambda z: 0.6 + 0.4 * (z > CENTRO[2])    # la cara de arriba sube mas que la de abajo

clave("mandibula", lambda x, y, z: (0.0, 0.0, -0.55 * (0.35 + 0.65 * raiz_w(x))), margen_x=(-0.7, 0.6))
clave("punta_arriba", lambda x, y, z: (0.1 * punta_w(x), 0.16 * y * punta_w(x) - 0.16 * y * (1 - punta_w(x)), 1.15 * punta_w(x) ** 1.3 + 0.65 * min(0, z - CENTRO[2]) * punta_w(x)), toca=True, margen_x=(-0.3, 0.1))
# Retrofleja: la punta se alza y se recoge un poco; la lamina sube con ella
# para que la punta no se doble sobre el cuerpo (comprobado abajo).
clave("punta_atras", lambda x, y, z: (0.4 * punta_w(x) ** 1.5, 0.0, 0.95 * punta_w(x) + 0.3 * campana(x, -0.9, 0.5)))
# Compensa lateralmente el alargamiento: el volumen de /theta/ queda cerca
# del reposo, conservando la nueva punta gruesa y el frente x=-3,03.
def interdental(x, y, z):
    """/θ ð/ (D4.4b v4): toda la lengua avanza (la raiz algo menos) y la
    parte anterior sube por cizalla vertical, que conserva el volumen y el
    grosor. La lamina se ensancha un poco. Sin recorte por vertice (`libre`):
    la punta queda entre los incisivos con la mandibula de la pose abierta."""
    avance = 0.85 * (1 - 0.25 * rampa(x, -1.0, 2.4))
    alza = INTERDENTAL_ALZA * (1 - rampa(x, -1.9, 0.8))
    # Hidrostato: el avance estira el cuerpo (~5 % de largo); la seccion del
    # cuerpo se adelgaza en la misma medida. La punta conserva su grosor.
    fino = rampa(x, -1.4, 0.4)
    return (-avance, -0.035 * y * fino, alza - 0.035 * (z - CENTRO[2]) * fino)


INTERDENTAL_ALZA = 1.25
clave("punta_interdental", interdental, libre=True)
clave("cuerpo_alto", lambda x, y, z: (0.0, 0.0, 1.35 * cuerpo_w(x) * arriba(z)), margen_x=(-0.8, 0.7))
clave("cuerpo_bajo", lambda x, y, z: (0.0, 0.0, -0.7 * cuerpo_w(x)), margen_x=(-0.7, 0.6))
clave("cuerpo_delante", lambda x, y, z: (-0.8 * campana(x, 0.0, 2.0), 0.0, 0.0))
clave("cuerpo_atras", lambda x, y, z: (0.7 * campana(x, 0.3, 2.0), 0.0, 0.0))
# La cara inferior acompaña al dorso: el antiguo salto 0,6/1,0 estiraba
# solo el techo de la lengua y estrangulaba el puente hacia la raiz.
def elevar_dorso(x, y, z):
    # Cupula ancha, con descenso continuo: la campana anterior y el recorte
    # escalonado contra el velo abierto dejaban un pico seguido de un gancho.
    # La base no cambia. El mismo desplazamiento sube ambas caras de la masa.
    ascenso = rampa(x, -0.8, 1.0)
    descenso = 1 - rampa(x, 1.75, 2.55)
    # El predorso debe dejar espacio a cuerpo_alto cuando ambos se suman.
    alza = 2.05 * ascenso * descenso - 0.60 * campana(x, 0.8, 0.55)
    # Limitar el desplazamiento de TODA la seccion, no recortar sus vertices
    # superiores por separado: eso aplastaba el grosor y producia una aleta.
    u = (x - CENTRO[0]) / LARGO
    cima = (ALTO * math.sqrt(max(0.0, 1 - u * u))
            * (0.92 + 0.08 * rampa(x - CENTRO[0], -2.2, -0.9))
            * (1 + 0.35 * rampa(x - CENTRO[0], 0.3, 2.1))
            - 0.55 * rampa(x - CENTRO[0], 0.35, 2.4) + CENTRO[2] + 0.03)
    limite = min(techo(x + d, True) for d in [-0.1, -0.005, 0.09, 0.185, 0.28]) + TOLERANCIA_TOQUE
    alza = min(alza, limite - cima)
    alza += 0.10 * rampa(x, 1.0, 1.25) * (1 - rampa(x, 1.65, 1.9))
    # El extremo queda enterrado en el suelo: no acaba en una punta flotante.
    # La cara inferior se prolonga hacia delante al bajar: espesor horizontal
    # de la raiz, que en una esfera simplemente estirada se vuelve una aleta.
    base_raiz = rampa(x, 0.9, 2.2) * rampa(-z, 0.45, 1.15)
    # El suelo se queda bajo la cúpula: levantar toda la sección creaba
    # un tubo arqueado. La cara inferior conserva masa hasta la raíz.
    inferior = rampa(-z, 0.5, 0.95)
    # Hidrostato (D4.4b v4): la cara de abajo sube casi tanto como la de
    # arriba (el suelo de la boca acompaña al dorso) y la parte anterior se
    # recoge y baja: la masa que sube al velo sale de la lamina, no se crea.
    recoge = 1 - rampa(x, -1.7, 0.3)
    return (-0.55 * base_raiz + 0.5 * recoge, -0.08 * y * recoge,
            alza * (1 - 0.12 * inferior) - 0.32 * recoge - 0.65 * rampa(x, 1.85, 2.4))

clave("dorso_velo", elevar_dorso, velo_abierto=True, toca=True, margen_x=(-0.1, 0.28))
clave("raiz_atras", lambda x, y, z: (0.5 * raiz_w(x), -0.06 * y * raiz_w(x), -0.08 * raiz_w(x)))

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

CARAS = [list(pg.vertices) for pg in ob.data.polygons]


def volumen(puntos):
    """Volumen de la malla cerrada (teorema de la divergencia, caras en abanico)."""
    v = 0.0
    for cara in CARAS:
        a = puntos[cara[0]]
        for i in range(1, len(cara) - 1):
            b, c = puntos[cara[i]], puntos[cara[i + 1]]
            v += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                  + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return abs(v)


def grosor_en(puntos, x0, ancho=0.2, lateral=0.15):
    """Grosor vertical de la linea media en la franja [x0, x0 + ancho]."""
    zs = [p[2] for p in puntos if x0 <= p[0] <= x0 + ancho and abs(p[1]) < lateral]
    return max(zs) - min(zs) if len(zs) >= 2 else 0.0


VOLUMEN_BASE = volumen(base)
# Hidrostato (D4.4b v4): ninguna pose cambia el volumen mas de un 10 %, y la
# punta (a 0,2 del apice) nunca es mas fina que el 75 % de la lamina (a 0,75).
TOL_VOLUMEN, PUNTA_MIN_RELATIVA = 0.10, 0.75
volumenes, grosores = {}, {}

informe = []
peor = 0.0
peor_pliegue = 0.0
peor_roce = -9.0        # cuanto entra la lengua en dientes, encias o hueso (negativo = holgura)
interdentales = []
ES_PUNTA = [punta_w(x) > 0.6 for x, _, _ in base]
ES_CUERPO = [punta_w(x) < 0.15 for x, _, _ in base]
for nombre, p in poses.items():
    inf = morfos_de(p)
    toca = p["punta_toca"] or p["dorso_velo"]
    permitido = TOLERANCIA_TOQUE if toca else 0.0
    entra = 0.0
    pos, pos_local = [], []
    angulo = min(1.0, max(0.0, p["mandibula"])) * 0.42
    coseno, seno = math.cos(angulo), math.sin(angulo)
    roce_sup = roce_inf = -9.0
    for i, (x, y, z) in enumerate(base):
        nx = x + sum(w * CLAVES[m][i][0] for w, m in zip(inf, MORFOS))
        ny = y + sum(w * CLAVES[m][i][1] for w, m in zip(inf, MORFOS))
        nz = z + sum(w * CLAVES[m][i][2] for w, m in zip(inf, MORFOS))
        # Los dientes de abajo giran con la lengua: se miden en coordenadas locales.
        r_inf = pen_inferior(nx, nz, ny)
        if os.environ.get("DEBUG_POSE") == nombre and r_inf > 0.0:
            print("DEBUG_ROCE_INF", nombre, [round(c, 3) for c in (nx, ny, nz)], round(r_inf, 3))
        roce_inf = max(roce_inf, r_inf)
        # EscenaBoca monta el GLB dentro de la mandibula: comparar el techo
        # contra coordenadas locales ocultaba el error de la punta interdental.
        pos_local.append((nx, ny, nz))
        nx, nz = (2.6 + (nx - 2.6) * coseno - (nz - 0.9) * seno,
                  0.9 + (nx - 2.6) * seno + (nz - 0.9) * coseno)
        pos.append((nx, ny, nz))
        entra = max(entra, nz - techo(nx, p["velo_abierto"]))
        # Los de arriba estan fijos: se miden con la lengua ya girada.
        r_sup = pen_superior(nx, nz, ny)
        if os.environ.get("DEBUG_POSE") == nombre and r_sup > 0.0:
            print("DEBUG_ROCE_SUP", nombre, [round(c, 3) for c in (nx, ny, nz)], round(r_sup, 3))
        roce_sup = max(roce_sup, r_sup)
    # La lengua no se dobla sobre si misma: ningun vertice de la punta queda
    # por debajo de la cara de arriba del cuerpo en su misma vertical. Se mide
    # en coordenadas LOCALES (antes del giro de la mandibula): el giro es
    # rigido para toda la lengua y, con la punta gruesa y la boca muy abierta
    # (/æ/), las columnas giradas mezclaban el vientre de la punta con el
    # dorso y daban un pliegue falso de 0,7.
    cuerpo = [(px, py, pz) for (px, py, pz), c in zip(pos_local, ES_CUERPO) if c]
    pliegue = 0.0
    for (px, py, pz), es_punta in zip(pos_local, ES_PUNTA):
        if not es_punta:
            continue
        techo_cuerpo = max((cz for cx, cy, cz in cuerpo if abs(cx - px) < 0.1 and abs(cy - py) < 0.12), default=-9.0)
        if os.environ.get("DEBUG_POSE") == nombre and techo_cuerpo - pz > 0.3:
            print("DEBUG_PLIEGUE", nombre, "punta", [round(c, 3) for c in (px, py, pz)],
                  "cuerpo", [[round(c, 3) for c in v] for v in cuerpo if abs(v[0] - px) < 0.1 and abs(v[1] - py) < 0.12][:2])
        pliegue = max(pliegue, techo_cuerpo - pz)
    exceso = entra - permitido
    if p["punta"] == "interdental":
        frente = min(v[0] for v in pos)
        punta = [v for v in pos if v[0] < frente + 0.10]
        y_min, y_max = min(v[2] for v in punta), max(v[2] for v in punta)
        assert frente < -2.72 and y_min > -0.41 and y_max < 0.45, (nombre, frente, y_min, y_max)
        interdentales.append((nombre, round(frente, 4), round(y_min, 4), round(y_max, 4)))
    # En /θ ð/ la lengua DESCANSA sobre los incisivos de abajo (es la postura):
    # se tolera el mismo toque que contra el paladar cuando la punta toca.
    roce = max(roce_sup, roce_inf) - (TOLERANCIA_TOQUE if p["punta"] == "interdental" else 0.0)
    informe.append((nombre, round(entra, 3), round(exceso, 3), round(pliegue, 3), round(roce, 3)))
    volumenes[nombre] = round(volumen(pos) / VOLUMEN_BASE - 1, 4)
    frente_x = min(v[0] for v in pos_local)
    grosores[nombre] = (round(grosor_en(pos_local, frente_x + 0.2), 3), round(grosor_en(pos_local, frente_x + 0.75), 3))
    peor = max(peor, exceso)
    peor_roce = max(peor_roce, roce)
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
# El mismo archivo va a front/public/boca3d/, que es el que carga la app: los
# dos tienen que ser identicos (lo comprueba boca3d.modelos.spec.ts).
PUBLICO = os.path.join(RAIZ, "front", "public", "boca3d", "lengua.glb")
if os.path.isdir(os.path.dirname(PUBLICO)) and os.path.abspath(SALIDA) != os.path.abspath(PUBLICO):
    import shutil
    shutil.copyfile(SALIDA, PUBLICO)

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
    "peor_roce_dientes": round(peor_roce, 3),
    "interdentales (nombre, x, ymin, ymax)": interdentales,
    "peores (nombre, entra, exceso, pliegue, roce)": sorted(informe, key=lambda r: -max(r[2], r[3], r[4]))[:6],
    "volumen_base": round(VOLUMEN_BASE, 4),
    "volumen (pose: relativo a la base)": {k: volumenes[k] for k in ["reposo", "θ", "ð", "s", "t", "k", "ŋ", "p", "m", "f", "n"] if k in volumenes},
    "peor_volumen": max(volumenes.items(), key=lambda kv: abs(kv[1])),
    "grosor (pose: punta, lamina)": {k: grosores[k] for k in ["reposo", "θ", "ð", "s", "t", "k", "ŋ", "p", "f", "n"] if k in grosores},
}, ensure_ascii=False))
fuera_volumen = {k: v for k, v in volumenes.items() if abs(v) > TOL_VOLUMEN}
punta_fina = {k: g for k, g in grosores.items() if g[1] > 0 and g[0] < PUNTA_MIN_RELATIVA * g[1]}
print("HIDROSTATO", json.dumps({"fuera_de_volumen": fuera_volumen, "punta_mas_fina_que_lamina": punta_fina}, ensure_ascii=False))
if os.environ.get("EXIGIR_HIDROSTATO") == "1" and (fuera_volumen or punta_fina):
    print("HIDROSTATO: volumen fuera de ±10 % o punta mas fina que la lamina", file=sys.stderr)
    sys.exit(1)
if peor > 0.005 or peor_pliegue > 0.005 or peor_roce > 0.005:
    print("COLISION: alguna pose entra en el techo, en los dientes, o la punta se dobla sobre el cuerpo", file=sys.stderr)
    sys.exit(1)
