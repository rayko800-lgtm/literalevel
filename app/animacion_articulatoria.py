"""Animaciones de articulacion: corte sagital de la cabeza en SVG animado.

Para cada sonido del ingles de la tabla del AFI (`articulacion.FICHAS`), una
vista lateral -nariz, labios, dientes, alveolo, paladar, velo, faringe,
lengua, mandibula y cuerdas vocales- que pasa de la posicion de reposo a la del
sonido y vuelve. Tambien encadena los sonidos de una palabra a partir de su
transcripcion (`svg_palabra`).

Biblioteca estandar y sin red. Los SVG se animan con CSS `@keyframes` dentro de
su `<style>`, sin JavaScript, asi que valen en `<img src="data:...">`, en
`innerHTML` y en un `gr.HTML`. Solo se animan `transform` y opacidades de piezas
separadas: nunca se interpola un trazado `d`.

API PUBLICA
- `PARAMETROS`: `Articulacion` por clave de `articulacion.FICHAS` (todas).
- `PARAMETROS_RP`: lo que el britanico articula distinto, por simbolo RP.
- `parametros(simbolo, acento="ga") -> Articulacion | None`
- `svg_articulacion(simbolo, acento="ga") -> str | None`: animado.
- `svg_articulacion_quieto(simbolo, acento="ga") -> str | None`: en la posicion.
- `trocear(ipa, acento="ga") -> list[Segmento]`: la transcripcion en fonemas.
- `svg_palabra(ipa, acento="ga") -> str | None`: la palabra entera, animada.

COLORES. Nada de fondo: los trazos usan `var(--ll-trazo, #6b7683)`, un gris que
se lee en fondo claro y oscuro; quien lo inserte en linea puede poner
`--ll-trazo: currentColor`. El aire y el resaltado usan
`var(--ll-acento, #2f9cc0)`; la lengua, `var(--ll-lengua, #d9727f)`.

LO QUE SE SIMPLIFICA. Es un corte por la linea media: lo lateral (el aire de
/l/ por los lados, los bordes de la lengua contra las muelas) va en la leyenda.
Las posiciones son de manual, no medidas de un hablante.
"""
from __future__ import annotations

import hashlib
import math
import unicodedata
from dataclasses import dataclass, replace
from xml.sax.saxutils import escape

import articulacion
import fonemas

# ---------------------------------------------------------------------------
# Parametros articulatorios
# ---------------------------------------------------------------------------

MOVIMIENTOS = ("oclusiva", "fricativa", "africada", "nasal", "aproximante", "vocal", "diptongo")
LABIOS = ("neutros", "cerrados", "redondeados", "muy_redondeados", "estirados", "labiodental")
PUNTAS = ("reposo", "interdental", "dental", "alveolar", "postalveolar", "retrofleja")


@dataclass(frozen=True)
class Articulacion:
    """Un objetivo articulatorio. `None` en un campo = libre: lo pone el contexto.

    - `movimiento`: oclusiva (cierre y explosion), fricativa (constriccion
      sostenida), africada (cierre que se suelta en fricativa), nasal (cierre
      sostenido con el velo bajado), aproximante, vocal o diptongo.
    - `mandibula`: apertura, 0 (dientes juntos) a 1 (muy abierta).
    - `labios`: uno de `LABIOS`.
    - `punta`: uno de `PUNTAS`; `punta_toca` dice si llega a tocar.
    - `cuerpo`: (altura, adelantamiento) de 0 a 1.
    - `dorso_velo`: el dorso cierra contra el velo (/k ɡ ŋ/).
    - `dorso_alto`: elevacion extra del dorso sin tocar (l oscura, /w/).
    - `raiz`: retraccion de la raiz hacia la faringe, 0 a 1.
    - `velo_abierto`: el velo baja y abre la nariz (nasales).
    - `lugar`: donde se marcan la explosion y el ruido.
    - `hacia`: segundo objetivo (diptongo; africada, la fase fricativa).
    """
    movimiento: str
    mandibula: float | None = None
    labios: str | None = None
    punta: str | None = None
    cuerpo: tuple[float, float] | None = None
    punta_toca: bool = False
    dorso_velo: bool = False
    dorso_alto: float = 0.0
    raiz: float = 0.0
    velo_abierto: bool = False
    sonora: bool = True
    lugar: str = ""
    larga: bool = False
    leyenda: str = ""
    hacia: "Articulacion | None" = None


A = Articulacion
REPOSO = A("vocal", mandibula=0.2, labios="neutros", punta="reposo", cuerpo=(0.45, 0.5))


def _vocal(alt, ade, mand, labios="neutros", leyenda="", larga=False, raiz=0.0, **kw):
    return A("vocal", mand, labios, "reposo", (alt, ade), raiz=raiz, larga=larga, leyenda=leyenda, **kw)


def _dip(a: Articulacion, b: Articulacion, leyenda: str) -> Articulacion:
    return replace(a, movimiento="diptongo", hacia=b, leyenda=leyenda)


_I = _vocal(1.0, 1.0, 0.12, "estirados", larga=True,
            leyenda="lengua alta y adelante, labios estirados; larga y tensa")
_IH = _vocal(0.78, 0.8, 0.26, "neutros",
             leyenda="más baja, más atrás y más relajada que /i/; corta")
_E = _vocal(0.58, 0.85, 0.42, "neutros", leyenda="lengua a media altura y adelante; corta")
_A_ABIERTA = _vocal(0.08, 0.55, 0.92, "neutros")
_O_MEDIA = _vocal(0.4, 0.08, 0.55, "redondeados")
_UH = _vocal(0.78, 0.22, 0.26, "redondeados",
             leyenda="más baja y relajada que /u/; labios algo redondeados; corta")
_U = _vocal(1.0, 0.05, 0.12, "muy_redondeados", larga=True, raiz=0.2,
            leyenda="lengua alta y atrás, labios muy redondeados; larga y tensa")
_SCHWA = _vocal(0.5, 0.5, 0.34, "neutros", leyenda="todo relajado, lengua en el centro; muy corta")

PARAMETROS: dict[str, Articulacion] = {
    # --- Oclusivas: cierre, presion y explosion ---
    "p": A("oclusiva", 0.08, "cerrados", None, None, sonora=False, lugar="bilabial",
           leyenda="labios cerrados que se abren de golpe, con soplo"),
    "b": A("oclusiva", 0.08, "cerrados", None, None, lugar="bilabial",
           leyenda="labios cerrados del todo que se separan, sin soplo"),
    "t": A("oclusiva", 0.18, None, "alveolar", (0.6, 0.65), punta_toca=True, sonora=False, lugar="alveolar",
           leyenda="punta en el alvéolo, no en los dientes; explosión con soplo"),
    "d": A("oclusiva", 0.18, None, "alveolar", (0.6, 0.65), punta_toca=True, lugar="alveolar",
           leyenda="punta en el alvéolo, no en los dientes; toca y baja rápido"),
    "k": A("oclusiva", 0.25, None, None, (0.45, 0.3), dorso_velo=True, sonora=False, lugar="velar",
           leyenda="el dorso cierra contra el velo; explosión con soplo"),
    "ɡ": A("oclusiva", 0.25, None, None, (0.45, 0.3), dorso_velo=True, lugar="velar",
           leyenda="el dorso cierra contra el velo y se suelta, sin soplo"),
    # --- Fricativas: constriccion sostenida ---
    "f": A("fricativa", 0.14, "labiodental", None, None, sonora=False, lugar="labiodental",
           leyenda="labio inferior contra dientes superiores"),
    "v": A("fricativa", 0.14, "labiodental", None, None, lugar="labiodental",
           leyenda="labio inferior contra dientes superiores; los labios no se juntan"),
    "θ": A("fricativa", 0.36, None, "interdental", (0.5, 0.75), sonora=False, lugar="interdental",
           leyenda="punta entre los dientes; el aire pasa por encima"),
    "ð": A("fricativa", 0.36, None, "interdental", (0.5, 0.75), lugar="interdental",
           leyenda="punta entre los dientes, sin golpe; el aire pasa por encima"),
    "s": A("fricativa", 0.1, "estirados", "alveolar", (0.62, 0.65), sonora=False, lugar="alveolar",
           leyenda="punta cerca del alvéolo sin tocarlo; aire afilado"),
    "z": A("fricativa", 0.1, "estirados", "alveolar", (0.62, 0.65), lugar="alveolar",
           leyenda="punta cerca del alvéolo sin tocarlo; zumbido de abeja"),
    "ʃ": A("fricativa", 0.12, "redondeados", "postalveolar", (0.72, 0.6), sonora=False, lugar="postalveolar",
           leyenda="labios redondeados; lengua tras el alvéolo, sin tocar"),
    "ʒ": A("fricativa", 0.12, "redondeados", "postalveolar", (0.72, 0.6), lugar="postalveolar",
           leyenda="labios redondeados; lengua tras el alvéolo, sin tocar"),
    "h": A("fricativa", None, None, None, None, sonora=False, lugar="glotal",
           leyenda="la boca ya está en la vocal; el aire roza en la garganta"),
    # --- Africadas: cierre que se suelta despacio en fricativa ---
    "tʃ": A("africada", 0.12, "redondeados", "postalveolar", (0.7, 0.62), punta_toca=True, sonora=False,
            lugar="postalveolar",
            hacia=A("fricativa", 0.12, "redondeados", "postalveolar", (0.72, 0.6), sonora=False,
                    lugar="postalveolar"),
            leyenda="cierre tras el alvéolo que se suelta en «sh»"),
    "dʒ": A("africada", 0.12, "redondeados", "postalveolar", (0.7, 0.62), punta_toca=True,
            lugar="postalveolar",
            hacia=A("fricativa", 0.12, "redondeados", "postalveolar", (0.72, 0.6), lugar="postalveolar"),
            leyenda="cierre tras el alvéolo que se suelta con zumbido"),
    # --- Nasales: cierre en la boca, velo bajado ---
    "m": A("nasal", 0.08, "cerrados", None, None, velo_abierto=True, lugar="bilabial",
           leyenda="labios cerrados; el velo baja y el aire sale por la nariz"),
    "n": A("nasal", 0.18, None, "alveolar", (0.6, 0.65), punta_toca=True, velo_abierto=True, lugar="alveolar",
           leyenda="punta en el alvéolo; el velo baja y el aire sale por la nariz"),
    "ŋ": A("nasal", 0.25, None, None, (0.45, 0.3), dorso_velo=True, velo_abierto=True, lugar="velar",
           leyenda="dorso contra el velo bajado; aire por la nariz, sin soltar g"),
    # --- Aproximantes: se acercan sin rozar ---
    "l": A("aproximante", 0.22, None, "alveolar", (0.5, 0.55), punta_toca=True, dorso_alto=0.6, raiz=0.35,
           lugar="alveolar",
           leyenda="punta en el alvéolo, aire por los lados; dorso alzado atrás (l oscura)"),
    "ɹ": A("aproximante", 0.22, "redondeados", "retrofleja", (0.55, 0.35), raiz=0.8,
           lugar="postalveolar",
           leyenda="punta curvada hacia atrás, sin tocar el paladar; no vibra ni golpea"),
    "w": A("aproximante", 0.12, "muy_redondeados", "reposo", (0.88, 0.08), dorso_alto=0.4,
           leyenda="labios muy redondeados; dorso hacia el velo, sin tocar"),
    "j": A("aproximante", 0.12, "estirados", "reposo", (1.0, 0.92),
           leyenda="dorso muy cerca del paladar duro, sin tocar, como una i rápida"),
    # --- Vocales de General American ---
    "i": _I,
    "ɪ": _IH,
    "ɛ": _E,
    "æ": _vocal(0.15, 0.85, 1.0, "estirados", larga=True,
                leyenda="boca muy abierta y lengua baja adelante: entre a y e"),
    "ɑ": _vocal(0.05, 0.05, 0.92, "neutros", larga=True, raiz=0.8,
                leyenda="boca muy abierta, lengua baja y atrás; larga"),
    "ɔ": _vocal(0.3, 0.05, 0.68, "redondeados", larga=True, raiz=0.6,
                leyenda="lengua atrás y baja, labios redondeados, boca abierta"),
    "ʊ": _UH,
    "u": _U,
    "ʌ": _vocal(0.35, 0.45, 0.58, "neutros", leyenda="lengua en el centro, media baja y relajada; corta"),
    "ə": _SCHWA,
    "ɝ": A("vocal", 0.28, "redondeados", "retrofleja", (0.58, 0.35), raiz=0.8, dorso_alto=0.2, larga=True,
           leyenda="lengua recogida con color de r durante toda la vocal, sin tocar"),
    "ɚ": A("vocal", 0.3, "neutros", "retrofleja", (0.52, 0.4), raiz=0.6, dorso_alto=0.1,
           leyenda="como /ɝ/ pero breve, átona y sin fuerza"),
    # --- Diptongos de General American: se deslizan de un objetivo a otro ---
    "eɪ": _dip(replace(_E, mandibula=0.4, cuerpo=(0.62, 0.85)), _IH, "de e media hacia i: la lengua sube"),
    "aɪ": _dip(_A_ABIERTA, _IH, "de a abierta hacia i: la boca se cierra y la lengua sube"),
    "ɔɪ": _dip(_O_MEDIA, replace(_IH, labios="estirados"), "de o redondeada hacia i: la lengua va adelante"),
    "oʊ": _dip(_vocal(0.6, 0.12, 0.38, "redondeados"), replace(_UH, labios="muy_redondeados"),
               "de o redondeada hacia u: los labios se cierran"),
    "aʊ": _dip(_A_ABIERTA, replace(_UH, labios="muy_redondeados"),
               "de a abierta hacia u: la boca se cierra y los labios se redondean"),
    # --- Solo del britanico (RP) ---
    "ɒ": _vocal(0.02, 0.02, 1.0, "redondeados", raiz=0.8,
                leyenda="boca muy abierta, lengua baja atrás, labios algo redondeados; corta"),
    "ɜː": _vocal(0.46, 0.5, 0.36, "neutros", larga=True,
                 leyenda="lengua relajada en el centro, sin r: la punta no sube; larga"),
    "ɪə": _dip(_IH, _SCHWA, "de i relajada hacia el centro, sin r"),
    "eə": _dip(replace(_E, cuerpo=(0.6, 0.85)), _SCHWA, "de e hacia el centro, sin r"),
    "ʊə": _dip(_UH, _SCHWA, "de u relajada hacia el centro, sin r"),
}

# Lo que RP articula distinto de la clave de su ficha (por simbolo RP). Los
# sonidos propios de RP (ɒ, ɜː, ɪə, eə, ʊə) ya tienen clave propia arriba.
PARAMETROS_RP: dict[str, Articulacion] = {
    "əʊ": _dip(_SCHWA, _UH, "empieza en el centro sin redondear y se cierra hacia u"),
    "ɔː": _vocal(0.55, 0.05, 0.45, "muy_redondeados", larga=True, raiz=0.4,
                 leyenda="lengua atrás, más cerrada que la americana, labios muy redondeados; larga"),
    "æ": _vocal(0.1, 0.8, 1.0, "neutros", leyenda="boca muy abierta, lengua baja adelante, cerca de a; corta"),
    "e": _vocal(0.66, 0.85, 0.34, "neutros", leyenda="lengua media alta y adelante, algo más cerrada; corta"),
    "ʌ": _vocal(0.28, 0.55, 0.68, "neutros", leyenda="lengua baja en el centro, cerca de a; corta"),
    "l": replace(PARAMETROS["l"], dorso_alto=0.0, raiz=0.0,
                 leyenda="punta en el alvéolo, aire por los lados; clara antes de vocal"),
}


def parametros(simbolo: str, acento: str = "ga") -> Articulacion | None:
    """Los parametros de ese simbolo en ese acento, o `None`."""
    # `articulacion.buscar` cae al americano con un acento desconocido: aqui no.
    if acento not in articulacion.ACENTOS:
        return None
    try:
        sonido = articulacion.buscar(simbolo, acento)
    except Exception:
        return None
    if sonido is None:
        return None
    if sonido.acento == "rp" and sonido.simbolo in PARAMETROS_RP:
        return PARAMETROS_RP[sonido.simbolo]
    return PARAMETROS.get(sonido.clave or sonido.simbolo)


# ---------------------------------------------------------------------------
# Geometria (unidades del viewBox; la cara mira a la izquierda)
# ---------------------------------------------------------------------------

_PIVOTE_MAND = (200.0, 40.0)
_PIVOTE_VELO = (168.0, 76.0)
_VELO_CERRADO, _VELO_ABIERTO = -24.0, 12.0
_PALADAR = (((64, 97), (70, 99), (74, 97), (78, 92)),
            ((78, 92), (84, 82), (104, 72), (130, 71)),
            ((130, 71), (150, 71), (162, 73), (170, 77)))
# La lengua es una cadena de articulaciones (circulos) unidas por trapecios:
# punta, lamina, frente, centro, dorso, raiz alta y raiz baja. Cada circulo solo
# se traslada; cada trapecio va dentro de su circulo y gira y se estira hasta el
# siguiente. La union se ve como una sola lengua con el contorno continuo.
_JUNTAS = ((74.0, 124.0), (86.0, 116.0), (104.0, 106.0), (130.0, 100.0),
           (157.0, 106.0), (176.0, 134.0), (182.0, 166.0))
_RADIOS = (4.5, 8.0, 13.0, 17.0, 18.0, 16.0, 12.0)
_NUCLEO = (134.0, 124.0, 44.0, 20.0)      # relleno bajo el contorno: cx, cy, rx, ry
_INCISIVO_SUP = (57.0, 120.0)
_INCISIVO_INF = (64.5, 113.0)             # con los dientes juntos
_LABIO_INF_ARRIBA = (47.0, 110.5)
_LABIO_INF_INTERIOR = (54.0, 111.5)


def _bezier(seg, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = seg
    u = 1 - t
    return (u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3,
            u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3)


_PUNTOS_PALADAR = [_bezier(s, i / 40) for s in _PALADAR for i in range(41)]


def _rotar(p, ang, centro):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    dx, dy = p[0] - centro[0], p[1] - centro[1]
    return (centro[0] + c * dx - s * dy, centro[1] + s * dx + c * dy)


def _velo_superficie(abierto: bool):
    """Puntos de la cara inferior del velo, en coordenadas absolutas."""
    ang = _VELO_ABIERTO if abierto else _VELO_CERRADO
    px, py = _PIVOTE_VELO
    return [_rotar((px + x, py + y), ang, _PIVOTE_VELO) for x, y in ((2, 5), (8, 8), (14, 12), (20, 18), (25, 26))]


def _techo(x: float, velo_abierto: bool) -> float:
    """Altura (y) del techo de la boca en x: paladar y, detras, el velo."""
    puntos = _PUNTOS_PALADAR + _velo_superficie(velo_abierto)
    cercano = min(puntos, key=lambda p: abs(p[0] - x))
    return cercano[1] if abs(cercano[0] - x) < 6 else 999.0


def _paladar_en(x: float) -> tuple[float, float]:
    return min(_PUNTOS_PALADAR, key=lambda p: abs(p[0] - x))


def _mand_transform(o: float):
    return (16.0 * o, -5.0 * o)          # (bajada, grados)


def _aplicar_mand(p, o):
    ty, ang = _mand_transform(o)
    x, y = _rotar(p, ang, _PIVOTE_MAND)
    return (x, y + ty)


def _local_mand(q, o):
    ty, ang = _mand_transform(o)
    return _rotar((q[0], q[1] - ty), -ang, _PIVOTE_MAND)


# ---------------------------------------------------------------------------
# De parametros a pose numerica
# ---------------------------------------------------------------------------

def _resolver(art: Articulacion, vecino: Articulacion = REPOSO) -> Articulacion:
    """Rellena los campos libres con los del vecino (o con el reposo)."""
    return replace(
        art,
        mandibula=art.mandibula if art.mandibula is not None else (vecino.mandibula if vecino.mandibula is not None else REPOSO.mandibula),
        labios=art.labios or vecino.labios or REPOSO.labios,
        punta=art.punta or (vecino.punta if vecino.movimiento in ("vocal", "diptongo") else None) or REPOSO.punta,
        cuerpo=art.cuerpo or vecino.cuerpo or REPOSO.cuerpo,
        raiz=art.raiz if (art.cuerpo or art.raiz) else vecino.raiz,
        dorso_alto=art.dorso_alto if (art.cuerpo or art.dorso_alto) else vecino.dorso_alto,
    )


def _pose(art: Articulacion) -> dict[str, tuple[float, ...]]:
    """Pose numerica de un objetivo ya resuelto (sin campos libres)."""
    o = art.mandibula
    ty, ang = _mand_transform(o)
    pose: dict[str, tuple[float, ...]] = {"mand": (ty, ang)}

    # Labios: el superior se traslada; el inferior va dentro de la mandibula.
    sup = {"neutros": (0, 0), "cerrados": (0, 1.5), "redondeados": (-5, 1.5), "muy_redondeados": (-8, 2.5),
           "estirados": (2.5, -1), "labiodental": (-1, -2.5)}[art.labios]
    pose["ls"] = sup
    if art.labios == "cerrados":
        destino = (_LABIO_INF_ARRIBA[0] - 1 + sup[0], 110.5 + sup[1])
        lx, ly = _local_mand(destino, o)
        pose["li"] = (lx - _LABIO_INF_ARRIBA[0], ly - _LABIO_INF_ARRIBA[1])
    elif art.labios == "labiodental":
        lx, ly = _local_mand((_INCISIVO_SUP[0] - 1, _INCISIVO_SUP[1] + 0.5), o)
        pose["li"] = (lx - _LABIO_INF_INTERIOR[0], ly - _LABIO_INF_INTERIOR[1])
    else:
        pose["li"] = {"neutros": (0, 0), "redondeados": (-5, -2.5), "muy_redondeados": (-8, -4.5),
                      "estirados": (2.5, 1)}[art.labios]

    # Lengua: el cuerpo (altura, adelantamiento) mueve frente, centro y dorso.
    alt, ade = art.cuerpo
    bx = (0.5 - ade) * 26
    by = (0.45 - alt) * (38 if alt < 0.45 else 26)
    J = [list(p) for p in _JUNTAS]
    R = _RADIOS
    for i, peso in ((2, 0.9), (3, 1.0), (4, 0.9)):
        J[i][0] += bx * peso
        J[i][1] += by * peso
    J[4][0] += art.dorso_alto * 4
    J[4][1] -= art.dorso_alto * 9
    J[5][0] += bx * 0.5 + art.raiz * 9
    J[5][1] += by * 0.3
    J[6][0] += art.raiz * 6
    techo = _PUNTOS_PALADAR + _velo_superficie(art.velo_abierto)

    def separar(i: int, holgura: float) -> None:
        """Baja la junta i hasta dejar `holgura` entre su borde y el techo."""
        for _ in range(60):
            d = min(math.hypot(J[i][0] - x, J[i][1] - y) for x, y in techo) - R[i]
            if d >= holgura:
                return
            J[i][1] += max(0.3, holgura - d)

    if art.dorso_velo:
        # El dorso cierra contra la cara inferior del velo (alzado o bajado).
        sup = _velo_superficie(art.velo_abierto)
        (x1, y1), (x3, y3) = sup[1], sup[4]
        vx, vy = (sup[2][0] + sup[3][0]) / 2, (sup[2][1] + sup[3][1]) / 2
        nx, ny = y3 - y1, -(x3 - x1)
        largo = math.hypot(nx, ny) or 1.0
        nx, ny = nx / largo, ny / largo
        if ny < 0:
            nx, ny = -nx, -ny
        J[4] = [vx + nx * (R[4] - 1.5), vy + ny * (R[4] - 1.5)]
    else:
        separar(4, 3.5)
    separar(3, 3.5)
    separar(2, 3.5)

    # Punta y lamina.
    toca = art.punta_toca
    lamina = None
    if art.punta == "reposo":
        J[0] = list(_aplicar_mand(_JUNTAS[0], o))
    elif art.punta == "interdental":
        inf = _aplicar_mand(_INCISIVO_INF, o)
        yi = (_INCISIVO_SUP[1] + inf[1]) / 2
        J[0], lamina = [53.0, yi], [67.0, yi + 1.5]
    elif art.punta == "dental":
        J[0] = [67.0, 105.0]
    elif art.punta == "alveolar":
        # En la cresta alveolar, detras del cuello de los incisivos: no en los dientes.
        px, py = _paladar_en(77)
        J[0] = [px + 1.5, py + R[0] + (-1.0 if toca else 4.0)]
    elif art.punta == "postalveolar":
        px, py = _paladar_en(84)
        qx, qy = _paladar_en(96)
        J[0] = [px, py + R[0] + (-1.0 if toca else 4.5)]
        lamina = [qx, qy + R[1] + (-0.5 if toca else 3.5)]
    else:  # retrofleja / recogida: la punta alzada y curvada hacia atras, sin tocar
        px, py = _paladar_en(92)
        J[0] = [px, py + R[0] + 7.0]
        lamina = [px - 5.0, py + R[0] + 21.0]
    if lamina is None:
        J[1] = [(J[0][0] + J[2][0]) / 2, (J[0][1] + J[2][1]) / 2 + 2]
        separar(1, 2.5)
    else:
        J[1] = lamina

    for i in range(7):
        pose[f"j{i}"] = (J[i][0], J[i][1])
    for i in range(6):
        dx, dy = J[i + 1][0] - J[i][0], J[i + 1][1] - J[i][1]
        pose[f"s{i}"] = (math.degrees(math.atan2(dy, dx)), max(0.5, math.hypot(dx, dy)))
    pose["nu"] = (bx * 0.8, by * 0.8)
    pose["ve"] = (_VELO_ABIERTO if art.velo_abierto else _VELO_CERRADO,)
    return pose


def _mezclar(a: dict, b: dict, t: float) -> dict:
    return {k: tuple(x + (y - x) * t for x, y in zip(a[k], b[k])) for k in a}


def _n(v: float) -> str:
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _transform(parte: str, v: tuple[float, ...]) -> str:
    if parte == "mand":
        px, py = _PIVOTE_MAND
        return f"translate({_n(px)}px,{_n(py + v[0])}px) rotate({_n(v[1])}deg) translate(-{_n(px)}px,-{_n(py)}px)"
    if parte[0] == "s":
        return f"rotate({_n(v[0])}deg) scale({_n(v[1])},1)"
    if parte == "ve":
        return f"translate({_n(_PIVOTE_VELO[0])}px,{_n(_PIVOTE_VELO[1])}px) rotate({_n(v[0])}deg)"
    return f"translate({_n(v[0])}px,{_n(v[1])}px)"


_PARTES = ("mand", "li", "ls", "ve", "nu") + tuple(f"j{i}" for i in range(7)) + tuple(f"s{i}" for i in range(6))

# ---------------------------------------------------------------------------
# Lineas de tiempo
# ---------------------------------------------------------------------------

_LUGARES = {
    "bilabial": (38.0, 110.0), "labiodental": (52.0, 118.0), "interdental": (50.0, 117.0),
    "alveolar": (77.0, 96.0), "postalveolar": (84.0, 90.0), "velar": _velo_superficie(False)[3],
    "glotal": (201.0, 200.0),
}
# El ruido de las fricativas se marca justo delante de la constriccion, donde sale.
_RUIDO = {**_LUGARES, "alveolar": (64.0, 104.0), "postalveolar": (68.0, 100.0),
          "interdental": (45.0, 113.0), "labiodental": (48.0, 121.0), "glotal": (201.0, 190.0)}


@dataclass
class _Linea:
    total: float
    poses: list          # [(t, pose)]
    vib: list            # [(t0, t1)]
    boca: list
    nariz: list
    ruido: dict          # lugar -> [(t0, t1)]
    golpe: dict          # lugar -> [t]


def _nueva_linea(total):
    return _Linea(total, [], [], [], [], {}, {})


def _objetivos(art: Articulacion, vecino: Articulacion):
    a = _resolver(art, vecino)
    b = _resolver(art.hacia, a if art.movimiento == "africada" else vecino) if art.hacia else None
    if b is not None and art.movimiento == "diptongo":
        b = _resolver(art.hacia, REPOSO)
    return a, b


def _linea_sonido(art: Articulacion) -> _Linea:
    """Reposo -> sonido -> reposo, en un ciclo de 2,8 s."""
    L = _nueva_linea(2.8)
    a, b = _objetivos(art, REPOSO)
    R, PA = _pose(REPOSO), _pose(a)
    PB = _pose(b) if b else None
    m = art.movimiento
    if m == "oclusiva":
        suelta = _mezclar(PA, R, 0.5)
        L.poses = [(0, R), (0.42, R), (0.95, PA), (1.5, PA), (1.6, suelta), (2.25, R), (2.8, R)]
        L.golpe[art.lugar] = [1.54]
        L.boca = [(1.54, 1.54 + (0.55 if not art.sonora else 0.25))]
        voz = (0.5, 2.1)
    elif m == "africada":
        L.poses = [(0, R), (0.4, R), (0.9, PA), (1.3, PA), (1.7, PB), (1.95, PB), (2.45, R), (2.8, R)]
        L.golpe[art.lugar] = [1.33]
        L.ruido[b.lugar or art.lugar] = [(1.4, 1.95)]
        L.boca = [(1.36, 1.95)]
        voz = (0.5, 2.25)
    elif m == "diptongo":
        L.poses = [(0, R), (0.35, R), (0.8, PA), (1.05, PA), (1.7, PB), (1.95, PB), (2.45, R), (2.8, R)]
        L.boca = [(0.85, 1.95)]
        voz = (0.45, 2.2)
    elif m == "vocal":
        t = (0.45, 0.95, 1.95, 2.45) if art.larga else (0.6, 1.05, 1.6, 2.15)
        L.poses = [(0, R), (t[0], R), (t[1], PA), (t[2], PA), (t[3], R), (2.8, R)]
        L.boca = [(t[1] - 0.1, t[2])]
        voz = (t[0] + 0.1, t[2] + 0.2)
    else:  # fricativa, nasal, aproximante
        t = (0.5, 1.0, 1.7, 2.3) if m == "aproximante" else (0.42, 0.95, 1.9, 2.45)
        L.poses = [(0, R), (t[0], R), (t[1], PA), (t[2], PA), (t[3], R), (2.8, R)]
        tramo = (t[1] + 0.05, t[2])
        if m == "nasal":
            L.nariz = [tramo]
        else:
            L.boca = [tramo]
        if m == "fricativa":
            L.ruido[art.lugar] = [tramo]
        voz = (t[0] + 0.08, t[2] + 0.25)
    if art.sonora:
        L.vib = [voz]
    return L


# ---------------------------------------------------------------------------
# Palabras
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Segmento:
    simbolo: str          # como se muestra (simbolo del inventario del acento)
    articulacion: Articulacion
    acento_silaba: int    # 0 sin acento, 1 primario (ˈ), 2 secundario (ˌ)
    desde: int            # posicion en el texto mostrado
    hasta: int


_MARCAS_PRIMARIO = "ˈ'"
_MARCAS_SECUNDARIO = "ˌ"
_NO_SIGNIFICA = set("/[]()«»“”\"`.‿ -") | set("̯̩͜͡ʰ̠̟̥̪̚ːˑ")
_GA_A_RP = {"ɝ": "ɜː", "ɚ": "ə"}


def _reconocer(sub: str, acento: str, directo: bool):
    """(simbolo mostrado, Articulacion) o None."""
    if acento == "rp":
        if directo:
            son = articulacion.buscar(sub, "rp")
        else:
            clave = fonemas.normalizar(sub)
            if not clave:
                return None
            clave = _GA_A_RP.get(clave, clave)
            son = next((s for s in articulacion.INVENTARIO_RP if s.clave == clave or s.simbolo == clave), None)
        if son is None:
            return None
        return son.simbolo, parametros(son.simbolo, "rp")
    if not directo:
        return None
    clave = fonemas.normalizar(sub)
    if not clave or clave not in PARAMETROS:
        return None
    return clave, PARAMETROS[clave]


def trocear(ipa: str, acento: str = "ga") -> tuple[str, list[Segmento]]:
    """El texto a mostrar y sus segmentos. Ignora lo que no reconoce."""
    if not isinstance(ipa, str):
        return "", []
    texto = unicodedata.normalize("NFC", ipa.strip()).strip("/[] ")
    # Caracteres significativos con su posicion en `texto`. La marca de
    # longitud se deja pasar: forma parte de «iː» en RP.
    sig: list[tuple[str, int]] = []
    marcas: dict[int, int] = {}
    for i, c in enumerate(texto):
        if c in _MARCAS_PRIMARIO or c in _MARCAS_SECUNDARIO:
            marcas[len(sig)] = 1 if c in _MARCAS_PRIMARIO else 2
        elif c == "ː" or (c not in _NO_SIGNIFICA and not unicodedata.combining(c)):
            sig.append((c, i))
    cadena = "".join(c for c, _ in sig)
    segmentos: list[Segmento] = []
    k, pendiente = 0, 0
    while k < len(cadena):
        if k in marcas:
            pendiente = marcas[k]
        hallado = None
        for directo in (True, False):
            for n in (4, 3, 2, 1):
                sub = cadena[k:k + n]
                if len(sub) < n or sub.startswith("ː"):
                    continue
                r = _reconocer(sub, acento, directo)
                if r and r[1] is not None:
                    hallado = (n, r)
                    break
            if hallado:
                break
        if not hallado:
            k += 1
            continue
        n, (simbolo, art) = hallado
        desde, hasta = sig[k][1], sig[k + n - 1][1] + 1
        while hasta < len(texto) and unicodedata.combining(texto[hasta]):
            hasta += 1
        segmentos.append(Segmento(simbolo, art, pendiente, desde, hasta))
        if art.movimiento in ("vocal", "diptongo"):
            pendiente = 0
        k += n
    return texto, segmentos


_DURACION = {"vocal": 0.34, "diptongo": 0.46, "oclusiva": 0.2, "africada": 0.28,
             "fricativa": 0.22, "nasal": 0.2, "aproximante": 0.18}
_LENTO = 1.6


def _linea_palabra(segs: list[Segmento]) -> tuple[_Linea, list[tuple[float, float]], int]:
    arts = [s.articulacion for s in segs]
    vocales = [i for i, a in enumerate(arts) if a.movimiento in ("vocal", "diptongo")]

    def vecino(i):
        sig = next((j for j in vocales if j > i), None)
        if sig is not None:
            return _resolver(arts[sig], REPOSO)
        ant = next((j for j in reversed(vocales) if j < i), None)
        if ant is not None:
            a = arts[ant]
            return _resolver(a.hacia, REPOSO) if a.hacia else _resolver(a, REPOSO)
        return REPOSO

    durs = []
    for s in segs:
        d = _DURACION[s.articulacion.movimiento] * (1.25 if s.articulacion.larga else 1.0)
        d *= {1: 1.4, 2: 1.15}.get(s.acento_silaba, 1.0)
        durs.append(d * _LENTO)
    inicio = 0.45
    total = inicio + sum(durs) + 1.0
    L = _nueva_linea(total)
    R = _pose(REPOSO)
    L.poses.append((0, R))
    L.poses.append((inicio - 0.05, R))
    tramos = []
    t = inicio
    for i, (s, d) in enumerate(zip(segs, durs)):
        art = s.articulacion
        a, b = _objetivos(art, vecino(i))
        PA = _pose(a)
        m = art.movimiento
        tramos.append((t, t + d))
        if m == "oclusiva":
            L.poses += [(t + 0.45 * d, PA), (t + 0.8 * d, PA)]
            L.golpe.setdefault(art.lugar, []).append(t + 0.84 * d)
            L.boca.append((t + 0.84 * d, t + d + (0.12 if not art.sonora else 0)))
        elif m == "africada":
            PB = _pose(b)
            L.poses += [(t + 0.3 * d, PA), (t + 0.5 * d, PA), (t + 0.8 * d, PB), (t + 0.95 * d, PB)]
            L.golpe.setdefault(art.lugar, []).append(t + 0.53 * d)
            L.ruido.setdefault(b.lugar or art.lugar, []).append((t + 0.56 * d, t + d))
            L.boca.append((t + 0.53 * d, t + d))
        elif m == "diptongo":
            PB = _pose(b)
            L.poses += [(t + 0.2 * d, PA), (t + 0.35 * d, PA), (t + 0.85 * d, PB)]
            L.boca.append((t + 0.2 * d, t + d))
        else:
            L.poses += [(t + 0.38 * d, PA), (t + 0.72 * d, PA)]
            tramo = (t + 0.3 * d, t + d)
            if m == "nasal":
                L.nariz.append(tramo)
            else:
                L.boca.append(tramo)
            if m == "fricativa":
                L.ruido.setdefault(art.lugar, []).append(tramo)
        if art.sonora:
            L.vib.append((t, t + d))
        t += d
    L.poses += [(t + 0.45, R), (total, R)]
    # La posicion quieta: la vocal acentuada, o la primera vocal, o el primero.
    fija = next((i for i in vocales if segs[i].acento_silaba == 1), vocales[0] if vocales else 0)
    return L, tramos, fija


# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------

_TRAZO = "var(--ll-trazo,#6b7683)"
_ACENTO = "var(--ll-acento,#2f9cc0)"
_LENGUA = "var(--ll-lengua,#d9727f)"
_VIBRA = "#e39b3a"
_FUENTE = "'Segoe UI','Charis SIL','Doulos SIL','DejaVu Sans',Arial,sans-serif"

_ANATOMIA = (
    # perfil de la frente y la nariz
    '<path d="M64,0C62,22 50,40 30,62C20,70 24,80 36,80L47,82C50,84 51,86 50,88"/>'
    # fosa nasal: suelo y techo, que sigue en la pared de la faringe
    '<path d="M52,78C80,72 140,66 172,68"/>'
    '<path d="M46,62C70,44 140,40 182,48C200,54 208,66 208,82L211,216"/>'
    # alveolo y paladar duro
    '<path d="M64,97C70,99 74,97 78,92C84,82 104,72 130,71C150,71 162,73 170,77"/>'
    # cuello y laringe
    '<path d="M150,194L147,216M189,184L192,216"/>'
)


def _prefijo(*partes: str) -> str:
    return "ll" + hashlib.sha1("|".join(partes).encode("utf-8")).hexdigest()[:7]


def _kf(nombre: str, puntos: list[tuple[float, str]], total: float, prop: str) -> str:
    por_valor: dict[str, list[str]] = {}
    ultimo = -1.0
    for t, v in sorted(puntos, key=lambda p: p[0]):
        pct = max(0.0, min(100.0, t / total * 100))
        if pct <= ultimo:
            pct = min(100.0, ultimo + 0.1)
        ultimo = pct
        por_valor.setdefault(v, []).append(_n(pct) + "%")
    cuerpo = "".join(f"{','.join(p)}{{{prop}:{v}}}" for v, p in por_valor.items())
    return f"@keyframes {nombre}{{{cuerpo}}}"


def _opacidad(tramos: list[tuple[float, float]], total: float, borde: float = 0.05) -> list[tuple[float, str]]:
    tramos = sorted(tramos)
    unidos: list[list[float]] = []
    for a, b in tramos:
        if unidos and a <= unidos[-1][1] + 2 * borde + 0.01:
            unidos[-1][1] = max(unidos[-1][1], b)
        else:
            unidos.append([a, b])
    puntos = [(0.0, "0"), (total, "0")]
    for a, b in unidos:
        a0, b1 = max(0.0, a - borde), min(total, b + borde)
        puntos += [(a0, "0"), (max(a0 + 0.001, a), "1"), (min(b, b1 - 0.001), "1"), (b1, "0")]
    # Quita duplicados de 0/total si un tramo los toca.
    limpio: dict[float, str] = {}
    for t, v in puntos:
        limpio[round(t, 3)] = v if round(t, 3) not in limpio or v == "1" else limpio[round(t, 3)]
    return sorted(limpio.items())


def _golpes(instantes: list[float], total: float) -> list[tuple[float, str]]:
    puntos = [(0.0, "0"), (total, "0")]
    for t in instantes:
        puntos += [(t - 0.04, "0"), (t, "1"), (t + 0.16, "0")]
    return sorted(puntos)


def _svg(prefijo: str, titulo: str, desc: str, linea: _Linea | None, fija: dict,
         marcas_fijas: dict, leyenda: list[str], simbolo_grande: str,
         extra_estilo: str = "", extra_cuerpo: str = "", fantasma: dict | None = None,
         alto_texto: int = 0) -> str:
    P = prefijo
    alto = 222 + alto_texto
    css = [f".{P} .{P}-p{{transform-box:view-box;transform-origin:0 0}}"]
    # Piezas articulatorias.
    for parte in _PARTES:
        clase = f"{P}-{parte}"
        estatico = _transform(parte, fija[parte])
        regla = f".{P} .{clase}{{transform:{estatico}"
        if linea:
            regla += f";animation:{clase} {linea.total:.2f}s ease-in-out infinite"
            css.append(_kf(clase, [(t, _transform(parte, p[parte])) for t, p in linea.poses], linea.total, "transform"))
        css.append(regla + "}")

    def marca(clase, opac_fija, puntos):
        regla = f".{P} .{clase}{{opacity:{opac_fija}"
        if linea and puntos is not None:
            regla += f";animation:{clase} {linea.total:.2f}s linear infinite"
            css.append(_kf(clase, puntos, linea.total, "opacity"))
        css.append(regla + "}")

    marca(f"{P}-vi", marcas_fijas.get("vi", 0), _opacidad(linea.vib, linea.total) if linea else None)
    marca(f"{P}-ab", marcas_fijas.get("ab", 0), _opacidad(linea.boca, linea.total) if linea else None)
    marca(f"{P}-an", marcas_fijas.get("an", 0), _opacidad(linea.nariz, linea.total) if linea else None)
    lugares_ruido = sorted(set(linea.ruido) if linea else set(k for k in marcas_fijas.get("ruido", ())))
    lugares_golpe = sorted(set(linea.golpe) if linea else set())
    for i, lugar in enumerate(lugares_ruido):
        marca(f"{P}-r{i}", 1 if lugar in marcas_fijas.get("ruido", ()) else 0,
              _opacidad(linea.ruido[lugar], linea.total) if linea else None)
    for i, lugar in enumerate(lugares_golpe):
        marca(f"{P}-g{i}", 0, _golpes(linea.golpe[lugar], linea.total))
    if linea:
        css.append(f"@keyframes {P}-w{{from{{transform:translateX(-1.2px)}}to{{transform:translateX(1.2px)}}}}")
        css.append(f".{P} .{P}-w{{animation:{P}-w .09s linear infinite alternate}}")
        css.append(f"@media (prefers-reduced-motion:reduce){{.{P} *{{animation:none!important}}}}")
    else:
        css.append(f"@media (prefers-reduced-motion:reduce){{.{P} *{{animation:none!important}}}}")
    css.append(extra_estilo)

    p = f'class="{P}-p {P}-'
    partes = []
    # Anatomia fija.
    partes.append(f'<g fill="none" stroke="{_TRAZO}" stroke-width="1.6" stroke-linecap="round" '
                  f'stroke-linejoin="round">{_ANATOMIA}</g>')
    # Pliegues vocales.
    partes.append(f'<path d="M192,197L200,200 192,203ZM210,197L202,200 210,203Z" fill="{_TRAZO}"/>')
    # Lengua: raiz, cuerpo, dorso y punta (misma tinta: se ven como una sola).
    ncx, ncy, nrx, nry = _NUCLEO
    lengua = [f'<ellipse {p}nu" cx="{_n(ncx)}" cy="{_n(ncy)}" rx="{_n(nrx)}" ry="{_n(nry)}"/>']
    for i in range(7):
        tramo = ""
        if i < 6:
            r0, r1 = _RADIOS[i], _RADIOS[i + 1]
            tramo = f'<path {p}s{i}" d="M0,-{_n(r0)}L1,-{_n(r1)} 1,{_n(r1)} 0,{_n(r0)}Z"/>'
        lengua.append(f'<g {p}j{i}"><circle r="{_n(_RADIOS[i])}"/>{tramo}</g>')
    partes.append(f'<g fill="{_LENGUA}">{"".join(lengua)}</g>')
    if fantasma:
        puntos = " ".join(f"{_n(fantasma[f'j{i}'][0])},{_n(fantasma[f'j{i}'][1] - _RADIOS[i])}" for i in range(1, 6))
        partes.append(f'<path d="M{puntos}" fill="none" stroke="{_LENGUA}" stroke-width="1.6" '
                      f'stroke-dasharray="3 3" stroke-linecap="round"/>')
    # Velo, encima de la lengua para que se vea el cierre del dorso.
    partes.append(f'<path {p}ve" d="M0,-4C16,-2 28,8 32,22C34,30 28,32 24,26C16,16 8,8 -2,4Z" '
                  f'fill="{_TRAZO}" fill-opacity=".3" stroke="{_TRAZO}" stroke-width="1.4"/>')
    # Mandibula: base de la lengua, incisivo inferior, labio inferior y menton.
    partes.append(
        f'<g {p}mand">'
        f'<ellipse cx="124" cy="146" rx="48" ry="20" fill="{_LENGUA}"/>'
        f'<path d="M63,113C60,119 59,128 60,138L69,138C69,128 68,120 66,113Z" fill="#f4f1ea" '
        f'stroke="{_TRAZO}" stroke-width="1.2"/>'
        f'<path d="M40,130C43,140 50,146 48,156C46,168 56,176 76,176C104,176 128,178 150,194" fill="none" '
        f'stroke="{_TRAZO}" stroke-width="1.6" stroke-linecap="round"/>'
        f'<path {p}li" d="M58,114C49,110 39,113 38,121C38,130 46,134 58,132C60,126 60,120 58,114Z" '
        f'fill="#c77b7b" fill-opacity=".6" stroke="{_TRAZO}" stroke-width="1.4"/></g>')
    # Incisivo superior y labio superior.
    partes.append(
        f'<path d="M60,96C58,104 56,114 57,120C60,121 62,118 64,112C66,106 68,100 70,96Z" fill="#f4f1ea" '
        f'stroke="{_TRAZO}" stroke-width="1.2"/>'
        f'<path {p}ls" d="M50,87C42,92 36,99 39,105C41,110 49,111 57,109C59,102 58,94 55,89Z" '
        f'fill="#c77b7b" fill-opacity=".6" stroke="{_TRAZO}" stroke-width="1.4"/>')
    # Marcas: aire por la boca y por la nariz, ruido, explosion y vibracion.
    partes.append(
        f'<path class="{P}-ab" d="M28,111l-6,5 6,5M19,111l-6,5 6,5M10,111l-6,5 6,5" fill="none" '
        f'stroke="{_ACENTO}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')
    partes.append(
        f'<path class="{P}-an" d="M42,84C36,90 30,95 22,102M22,95V102H29M36,85C32,92 26,98 16,106" fill="none" '
        f'stroke="{_ACENTO}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'stroke-dasharray="4 3"/>')
    for i, lugar in enumerate(lugares_ruido):
        x, y = _RUIDO.get(lugar, _RUIDO["alveolar"])
        partes.append(f'<path class="{P}-r{i}" transform="translate({_n(x)},{_n(y)})" '
                      f'd="M-7,-3c2-3 4-3 6,0s4,3 6,0M-7,3c2-3 4-3 6,0s4,3 6,0" fill="none" stroke="{_ACENTO}" '
                      f'stroke-width="1.5" stroke-linecap="round"/>')
    for i, lugar in enumerate(lugares_golpe):
        x, y = _LUGARES.get(lugar, _LUGARES["alveolar"])
        partes.append(f'<path class="{P}-g{i}" transform="translate({_n(x)},{_n(y)})" '
                      f'd="M0,-9L2.5,-2.5 9,0 2.5,2.5 0,9 -2.5,2.5 -9,0 -2.5,-2.5Z" fill="#f2b134" '
                      f'stroke="#c9861a" stroke-width=".8"/>')
    partes.append(
        f'<g class="{P}-vi"><path class="{P}-w" d="M184,188l-5,3 5,3 -5,3 5,3 -5,3 5,3M219,188l5,3 -5,3 5,3 -5,3 5,3 -5,3" '
        f'fill="none" stroke="{_VIBRA}" stroke-width="1.6" stroke-linejoin="round"/></g>')
    partes.append(extra_cuerpo)
    # Textos.
    if simbolo_grande:
        partes.append(f'<text x="234" y="30" text-anchor="end" font-size="24" font-weight="700" '
                      f'fill="{_TRAZO}">{escape(simbolo_grande)}</text>')
    for i, renglon in enumerate(leyenda):
        partes.append(f'<text x="4" y="{226 + i * 12}" font-size="9.6" fill="{_TRAZO}">{escape(renglon)}</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 {alto}" role="img" '
            f'aria-labelledby="{P}-t {P}-d" class="{P}" font-family="{_FUENTE}">'
            f'<title id="{P}-t">{escape(titulo)}</title><desc id="{P}-d">{escape(desc)}</desc>'
            f'<style>{"".join(css)}</style>{"".join(partes)}</svg>')


def _partir(texto: str, ancho: int = 46) -> list[str]:
    renglones, actual = [], ""
    for palabra in texto.split():
        if actual and len(actual) + 1 + len(palabra) > ancho:
            renglones.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    if actual:
        renglones.append(actual)
    return renglones


def _cuerdas(art: Articulacion) -> str:
    return "con vibración" if art.sonora else "sin vibración"


def _construir(simbolo: str, acento: str, animado: bool) -> str | None:
    if not isinstance(simbolo, str) or not isinstance(acento, str):
        return None
    art = parametros(simbolo, acento)
    sonido = articulacion.buscar(simbolo, acento)
    if art is None or sonido is None:
        return None
    a, b = _objetivos(art, REPOSO)
    fija = _pose(a)
    marcas = {"vi": 1 if art.sonora else 0}
    m = art.movimiento
    if m in ("fricativa", "vocal", "diptongo", "aproximante"):
        marcas["ab"] = 1
    if m == "nasal":
        marcas["an"] = 1
    if m == "fricativa":
        marcas["ruido"] = (art.lugar,)
    linea = _linea_sonido(art) if animado else None
    fantasma = _pose(b) if (b is not None and m == "diptongo") else None
    texto = f"/{sonido.simbolo}/ {art.leyenda} · {_cuerdas(art)}"
    leyenda = _partir(texto)
    nombre_acento = articulacion.ACENTOS.get(acento, acento)
    f = sonido.ficha
    titulo = f"Articulación de /{sonido.simbolo}/ ({nombre_acento})"
    desc = (f"Corte lateral de la cabeza{' animado' if animado else ''}: {f.rasgos}. {art.leyenda}. "
            f"Labios: {f.labios}. Lengua: {f.lengua}. Cuerdas vocales: {_cuerdas(art)}.")
    if animado:
        desc += " La animación va del reposo a la posición del sonido y vuelve."
    if fantasma:
        desc += " La línea discontinua marca adónde llega la lengua al final del deslizamiento."
    P = _prefijo(acento, sonido.simbolo, "a" if animado else "q")
    return _svg(P, titulo, desc, linea, fija, marcas, leyenda, f"/{sonido.simbolo}/",
                fantasma=fantasma, alto_texto=12 * len(leyenda) + 2)


def svg_articulacion(simbolo: str, acento: str = "ga") -> str | None:
    """SVG animado (reposo -> sonido -> reposo) o `None` si el simbolo no esta en ese acento."""
    try:
        return _construir(simbolo, acento, True)
    except Exception:
        return None


def svg_articulacion_quieto(simbolo: str, acento: str = "ga") -> str | None:
    """La misma figura, sin animacion, en la posicion del sonido."""
    try:
        return _construir(simbolo, acento, False)
    except Exception:
        return None


def svg_palabra(ipa: str, acento: str = "ga") -> str | None:
    """Un SVG que recorre las posiciones de los fonemas de una transcripcion.

    Acepta «/ˈmoʊstli/» o «[ˈwɔːtə]». Trocea con prioridad a lo mas largo
    (diptongos y africadas antes que sus letras), ignora lo que no reconoce
    (ɾ, ʔ, diacriticos) y devuelve `None` si no queda ningun fonema. Vocales
    mas largas que consonantes; la silaba acentuada (ˈ) dura un 40 % mas y la
    secundaria (ˌ) un 15 %. Debajo, la transcripcion con el fonema en curso
    resaltado y su leyenda.
    """
    try:
        return _construir_palabra(ipa, acento)
    except Exception:
        return None


def _construir_palabra(ipa: str, acento: str) -> str | None:
    if acento not in articulacion.ACENTOS:
        return None
    texto, segs = trocear(ipa, acento)
    if not segs:
        return None
    linea, tramos, fija_i = _linea_palabra(segs)
    arts = [s.articulacion for s in segs]
    seg_fijo = segs[fija_i]
    a, _ = _objetivos(seg_fijo.articulacion, REPOSO)
    fija = _pose(a)
    marcas = {"vi": 1 if seg_fijo.articulacion.sonora else 0,
              "ab": 1 if seg_fijo.articulacion.movimiento != "nasal" else 0,
              "an": 1 if seg_fijo.articulacion.movimiento == "nasal" else 0}
    P = _prefijo(acento, "palabra", texto)
    total = linea.total

    # Transcripcion: una capa base y otra de resaltado por fonema (fill-opacity
    # temporizada por segmentos: no depende de medir el texto).
    trozos, pos = [], 0
    for i, s in enumerate(segs):
        if s.desde > pos:
            trozos.append((texto[pos:s.desde], None))
        trozos.append((texto[s.desde:s.hasta], i))
        pos = s.hasta
    if pos < len(texto):
        trozos.append((texto[pos:], None))
    y_ipa = 238
    oculto = 'fill-opacity="0" stroke-opacity="0"'
    base ="".join(f"<tspan>{escape(t)}</tspan>" for t, _ in trozos)
    resaltado = "".join(
        f'<tspan class="{P}-k{i}">{escape(t)}</tspan>' if i is not None else f'<tspan {oculto}>{escape(t)}</tspan>'
        for t, i in trozos)
    css, cuerpo = [], []
    # Sin negrita: cambiaria el ancho de las letras y la capa de resaltado no
    # coincidiria con la base. El grosor lo da un trazo del mismo color.
    cuerpo.append(f'<text x="120" y="{y_ipa}" text-anchor="middle" font-size="18" fill="{_TRAZO}">/{base}/</text>')
    cuerpo.append(f'<text x="120" y="{y_ipa}" text-anchor="middle" font-size="18" fill="{_ACENTO}" '
                  f'stroke="{_ACENTO}" stroke-width=".8"><tspan {oculto}>/</tspan>{resaltado}<tspan {oculto}>/</tspan></text>')
    for i, (s, (t0, t1)) in enumerate(zip(segs, tramos)):
        visible = 1 if i == fija_i else 0
        puntos = [(0.0, "0"), (total, "0"), (max(0.0, t0 - 0.02), "0"), (t0 + 0.02, "1"),
                  (t1 - 0.02, "1"), (t1 + 0.02, "0")]
        css.append(_kf(f"{P}-k{i}", [(t, f"{v};stroke-opacity:{v}") for t, v in puntos], total, "fill-opacity"))
        css.append(f".{P} .{P}-k{i}{{fill-opacity:{visible};stroke-opacity:{visible};"
                   f"animation:{P}-k{i} {total:.2f}s linear infinite}}")
        renglones = _partir(f"/{s.simbolo}/ {s.articulacion.leyenda} · {_cuerdas(s.articulacion)}", 50)[:2]
        cuerpo.append(f'<text class="{P}-k{i}" font-size="9" fill="{_TRAZO}">' + "".join(
            f'<tspan x="4" y="{254 + j * 11}">{escape(r)}</tspan>' for j, r in enumerate(renglones)) + "</text>")

    titulo = f"Articulación de /{texto}/ ({articulacion.ACENTOS[acento]})"
    desc = ("Corte lateral de la cabeza animado que recorre los sonidos de la palabra: "
            + "; ".join(f"/{s.simbolo}/ {s.articulacion.leyenda}" for s in segs) + ".")
    return _svg(P, titulo, desc, linea, fija, marcas, [], "", extra_estilo="".join(css),
                extra_cuerpo="".join(cuerpo), alto_texto=52)
