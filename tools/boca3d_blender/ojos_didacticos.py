"""Ojos abiertos de verdad en la cabeza didáctica (25 sep 2026, Miguel: «los
ojos se ven raros»).

El escaneo LPS trae los párpados CERRADOS. Hasta ahora el visor recortaba una
almendra en la piel con el shader y ponía una esfera detrás: de frente pasaba,
pero de tres cuartos y de perfil se veía un corte de papel sin grosor, la
esfera a otra profundidad que el párpado y el ojo lejano desplazado (la cara
escaneada no es simétrica: el ojo cercano está a 1,2 de la línea media y el
lejano a 1,5).

Aquí se hace en la malla, sobre la superficie del escaneo y antes de construir
nada:
1. los párpados se ciñen a una esfera concéntrica al globo ocular (radio del
   globo + grosor del párpado), con un fundido hacia la piel de alrededor;
2. se abre la hendidura en almendra (sube un poco hacia fuera) y su borde se
   ajusta exactamente a la curva, sin dientes de sierra;
3. el borde se remata con el margen del párpado: una franja que se dobla hacia
   dentro y toca el globo, que es lo que da grosor al párpado al mirarlo de
   lado y evita ver el interior por el hueco.

El globo ocular lo pone el visor (`escena.ts`, `OJOS`) con los mismos centros y
radio que se exportan aquí en `CENTROS`, `RADIO`.

Coordenadas del escaneo (Blender): x delante(-)/detrás(+), y lateral (cercana
y < 0), z arriba. Valores de ilustración medidos sobre la malla, no clínicos.
"""
import math
from mathutils import Vector

RADIO = .50           # globo ocular: ~24 mm de diámetro
GROSOR = .07          # párpado
SEMIANCHO = .56       # media hendidura
ALTO_SUP, ALTO_INF = .22, .12
# Centro de cada globo: (x, y, z). El párpado cerrado del escaneo tiene su
# punto más adelantado en x ≈ -2,50; la córnea queda un poco por detrás.
CENTROS = {-1: Vector((-1.94, -1.20, 3.00)), 1: Vector((-1.94, 1.48, 3.00))}


def _s(t):
    t = max(0., min(1., t))
    return t * t * (3 - 2 * t)


def _almendra(lado, y, z):
    """(u, borde superior, borde inferior) de la hendidura en la vertical de y."""
    c = CENTROS[lado]
    u = (abs(y) - abs(c.y)) / SEMIANCHO          # -1 lagrimal, +1 comisura
    if abs(u) >= 1:
        return u, None, None
    centro = c.z + .035 * u
    arriba = ALTO_SUP * (1 - u * u) ** .75 * (1 - .18 * u)
    abajo = ALTO_INF * (1 - u * u) ** .9
    return u, centro + arriba, centro - abajo


def _dentro(lado, p, margen=0.):
    u, sup, inf = _almendra(lado, p.y, p.z)
    return sup is not None and inf - margen < p.z < sup + margen and p.x < CENTROS[lado].x - .2


def _al_borde(lado, y, z):
    """El punto de la curva de la almendra en el rayo del centro a (y, z)."""
    c = CENTROS[lado]
    yc, zc = math.copysign(abs(c.y), y), c.z
    dy, dz = y - yc, z - zc
    if abs(dy) + abs(dz) < 1e-9:
        return y, z
    def dentro(t):
        yy, zz = yc + dy * t, zc + dz * t
        _, sup, inf = _almendra(lado, yy, zz)
        return sup is not None and inf < zz < sup
    lo, hi = 0., 1.
    while dentro(hi) and hi < 64:
        hi *= 2
    for _ in range(40):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if dentro(m) else (lo, m)
    return yc + dy * lo, zc + dz * lo


def construir(bm, capa_uv):
    """Modifica la superficie del escaneo (bmesh) en su sitio."""
    import bmesh
    for lado, c in CENTROS.items():
        # 1. Párpados ceñidos al globo, con fundido.
        for v in bm.verts:
            p = v.co
            if p.x > c.x - .12 or (p.y > 0) != (lado > 0):
                continue
            e = math.hypot((abs(p.y) - abs(c.y)) / .85, (p.z - c.z) / .60)
            w = 1 - _s((e - .55) / .45)
            if w <= 0:
                continue
            objetivo = c + (p - c).normalized() * (RADIO + GROSOR)
            v.co = p.lerp(objetivo, w)
        # 2. Hendidura: fuera las caras dentro de la almendra.
        fuera = [f for f in bm.faces if (f.calc_center_median().y > 0) == (lado > 0)
                 and _dentro(lado, f.calc_center_median())]
        bmesh.ops.delete(bm, geom=fuera, context='FACES')
        sueltos = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=sueltos, context='VERTS')
        # El borde del hueco: toda arista suelta cerca del ojo (no solo las de
        # dentro de la almendra: en el lagrimal quedaban triángulos colgando).
        def cerca(e):
            m = (e.verts[0].co + e.verts[1].co) / 2
            return ((m.y > 0) == (lado > 0) and m.x < c.x - .2
                    and math.hypot((abs(m.y) - abs(c.y)) / .9, (m.z - c.z) / .6) < 1)
        borde = [e for e in bm.edges if e.is_boundary and cerca(e)]
        verts_borde = {v for e in borde for v in e.verts}
        # El borde, sobre la curva exacta: cada vértice se lleva a lo largo del
        # rayo que sale del centro de la almendra (en y, z) hasta cruzar la
        # curva. Así las esquinas (lagrimal, comisura) no se estiran en picos.
        for v in verts_borde:
            y, z = _al_borde(lado, v.co.y, v.co.z)
            p = Vector((v.co.x, y, z))
            v.co = c + (p - c).normalized() * (RADIO + GROSOR)
        # 3. Margen del párpado: cada arista del borde baja hasta tocar el globo.
        nuevos = {}
        for v in verts_borde:
            p = v.co
            hacia = Vector((0., math.copysign(abs(c.y), p.y) - p.y, c.z - p.z))
            hacia = hacia.normalized() * .045 if hacia.length > 1e-6 else Vector()
            q = p + hacia
            nuevos[v] = bm.verts.new(c + (q - c).normalized() * (RADIO + .006))
        for e in borde:
            a, b = e.verts
            cara_vecina = e.link_faces[0]
            # Mismo sentido que la cara vecina: la franja sigue su normal.
            orden = [a, b] if list(cara_vecina.verts).index(a) + 1 == list(cara_vecina.verts).index(b) or \
                (list(cara_vecina.verts)[-1] == a and list(cara_vecina.verts)[0] == b) else [b, a]
            try:
                f = bm.faces.new((orden[1], orden[0], nuevos[orden[0]], nuevos[orden[1]]))
            except ValueError:
                continue
            f.smooth = True
            for loop in f.loops:
                origen = loop.vert if loop.vert in verts_borde else next(k for k, n in nuevos.items() if n is loop.vert)
                uv = next((l[capa_uv].uv.copy() for l in origen.link_loops if l.face is not f), None)
                if uv is not None:
                    loop[capa_uv].uv = uv
    bm.normal_update()
