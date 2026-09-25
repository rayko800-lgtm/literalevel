"""Proporciones del tercio inferior de la cabeza didáctica (25 sep 2026).

Miguel, con su video: «la parte entre la nariz y la barbilla es muy grande»,
«de lado la barbilla parece muy caída» y «quiero una mandíbula más prominente,
más masculina». El escaneo LPS tiene un tercio inferior largo (subnasal →
estomion : estomion → mentón ≈ 1 : 2,3, la referencia estética es 1 : 2) y una
línea submentoniana que baja en rampa hasta el cuello (papada).

Un campo de desplazamiento suave, en coordenadas del exterior de Blender
(x delante(-)/detrás(+), y lateral, z arriba), que se aplica al escaneo antes
de construir nada, y al hueso ilustrativo del corte con el mismo campo:
1. acorta el mentón (sube lo que está por debajo de z = -1,0);
2. adelanta y cuadra un poco el mentón blando (pogonion);
3. tensa la línea submentoniana hacia una recta casi horizontal que acaba en
   un ángulo cervicomentoniano marcado;
4. ensancha un poco el ángulo de la mandíbula (gonion).

Nada cambia por encima de z = -0,9: la ventana perioral, los labios, la nariz
y los ojos quedan exactamente igual. Valores de ilustración, no clínicos.
"""
import math
import os

ACORTAR = float(os.environ.get('MENTON_ACORTAR', '.20'))
PROYECTAR = float(os.environ.get('MENTON_PROYECTAR', '.16'))
TENSAR = float(os.environ.get('SUBMENTON_TENSAR', '1.0'))
GONION = float(os.environ.get('GONION_ANCHO', '.13'))


def _s(t):
    t = max(0., min(1., t))
    return t * t * (3 - 2 * t)


def acortar(x, z):
    """Subida del tercio inferior (1): la usan la piel y el hueso del corte."""
    return ACORTAR * _s((-1.0 - z) / .8) * (1 - _s((x + .6) / .9))


def _linea_submenton(x):
    # Del mentón ya subido (-2,2; -1,74) a la garganta (-0,3; -1,98).
    return -1.74 - .24 * _s((x + 2.2) / 1.9)


def desplazar(x, y, z):
    """(dx, dy, dz) del punto de la piel en reposo."""
    dz = acortar(x, z)
    zz = z + dz
    # 2. Mentón blando: adelante y algo más ancho (cuadrado).
    menton = math.exp(-((z + 1.35) / .45) ** 2) * _s((-.9 - z) / .3) * _s((-2.0 - x) / .5)
    dx = -PROYECTAR * menton * math.exp(-(y / 1.1) ** 2)
    dy = .05 * y * menton * math.exp(-(y / 1.6) ** 2)
    # 3. Línea submentoniana: lo que queda por debajo se recoge hacia la recta,
    # tanto más cuanto más cerca está (el cuello no se aplasta).
    d = _linea_submenton(x) - zz
    if d > 0:
        k = TENSAR * (1 - _s((d - .5) / .9))
        mx = _s((x + 2.3) / .3) * (1 - _s((x - .05) / .6))
        my = 1 - _s((abs(y) - 1.6) / .9)
        dz += d * k * mx * my
    # 4. Gonion: el ángulo de la mandíbula, un poco más ancho y marcado.
    gon = math.exp(-((x - .45) / .7) ** 2) * math.exp(-((z + 1.35) / .55) ** 2) * _s((abs(y) - 1.4) / .7)
    dy += GONION * gon * (1 if y >= 0 else -1)
    return dx, dy, dz
