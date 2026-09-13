"""Pruebas de app/animacion_articulatoria.py.

    python -X utf8 pruebas_animacion.py

Imprime `ok` o `FALLO` por comprobacion y sale con codigo 1 si algo falla.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, "app")

import animacion_articulatoria as aa  # noqa: E402
import articulacion  # noqa: E402

FALLOS: list[str] = []
LIMITE_SONIDO = 15_000
LIMITE_PALABRA = 40_000


def comprobar(nombre: str, condicion: bool, detalle: str = "") -> None:
    if condicion:
        print(f"ok     {nombre}")
    else:
        print(f"FALLO  {nombre}" + (f": {detalle}" if detalle else ""))
        FALLOS.append(nombre)


def svg_limpio(nombre: str, svg: str | None, limite: int) -> None:
    """Las comprobaciones que vale cualquier SVG del modulo."""
    comprobar(f"{nombre}: devuelve SVG", isinstance(svg, str) and svg.startswith("<svg"))
    if not isinstance(svg, str):
        return
    try:
        raiz = ET.fromstring(svg)
        xml_ok = True
    except ET.ParseError as e:
        raiz, xml_ok = None, False
        comprobar(f"{nombre}: XML valido", False, str(e))
    if xml_ok:
        comprobar(f"{nombre}: XML valido", True)
        ns = "{http://www.w3.org/2000/svg}"
        comprobar(f"{nombre}: role=img, title y desc",
                  raiz.get("role") == "img" and raiz.find(f"{ns}title") is not None
                  and raiz.find(f"{ns}desc") is not None)
        comprobar(f"{nombre}: sin <script>", not any(el.tag.endswith("script") for el in raiz.iter()))
        atributos_on = [a for el in raiz.iter() for a in el.attrib if a.lower().startswith("on")]
        comprobar(f"{nombre}: sin atributos on*=", not atributos_on, ", ".join(atributos_on))
    comprobar(f"{nombre}: sin on*= en el texto", not re.search(r"\son[a-z]+\s*=", svg))
    comprobar(f"{nombre}: prefers-reduced-motion", "prefers-reduced-motion" in svg)
    peso = len(svg.encode("utf-8"))
    comprobar(f"{nombre}: pesa menos de {limite} bytes", peso < limite, f"{peso} bytes")
    comprobar(f"{nombre}: sin d interpolado en keyframes", not re.search(r"@keyframes[^}]*\{[^}]*\bd\s*:", svg))
    comprobar(f"{nombre}: sin fondo opaco", "<rect" not in svg and "background" not in svg)


def prefijo(svg: str) -> str:
    return re.search(r'class="(ll[0-9a-f]+)"', svg).group(1)


# --- 1. Parametros para cada clave de FICHAS ---------------------------------
faltan = sorted(set(articulacion.FICHAS) - set(aa.PARAMETROS))
comprobar("parametros para cada clave de FICHAS", not faltan, ", ".join(faltan))
for clave, art in aa.PARAMETROS.items():
    bien = (art.movimiento in aa.MOVIMIENTOS
            and (art.labios is None or art.labios in aa.LABIOS)
            and (art.punta is None or art.punta in aa.PUNTAS)
            and (art.movimiento != "diptongo" or art.hacia is not None)
            and (art.movimiento != "africada" or art.hacia is not None)
            and bool(art.leyenda))
    if not bien:
        comprobar(f"parametros coherentes de /{clave}/", False)
comprobar("parametros coherentes (movimiento, labios, punta, leyenda, segundo objetivo)",
          not any(f.startswith("parametros coherentes de") for f in FALLOS))

# --- 2. Cada SVG de los dos acentos -------------------------------------------
prefijos: set[str] = set()
pesos: list[int] = []
for acento, inventario in (("ga", articulacion.INVENTARIO_GA), ("rp", articulacion.INVENTARIO_RP)):
    for sonido in inventario:
        for modo, funcion in (("animado", aa.svg_articulacion), ("quieto", aa.svg_articulacion_quieto)):
            svg = funcion(sonido.simbolo, acento)
            svg_limpio(f"{acento} /{sonido.simbolo}/ {modo}", svg, LIMITE_SONIDO)
            if isinstance(svg, str):
                pesos.append(len(svg.encode("utf-8")))
                prefijos.add(prefijo(svg))
                if modo == "animado":
                    comprobar(f"{acento} /{sonido.simbolo}/: animado con @keyframes", "@keyframes" in svg)
                else:
                    comprobar(f"{acento} /{sonido.simbolo}/: quieto sin animacion", "@keyframes" not in svg
                              and not re.search(r"animation:(?!none)", svg))
n_svg = 2 * (len(articulacion.INVENTARIO_GA) + len(articulacion.INVENTARIO_RP))
comprobar("prefijos de clase distintos entre SVG", len(prefijos) == n_svg, f"{len(prefijos)} de {n_svg}")
a, b = aa.svg_articulacion("v"), aa.svg_articulacion("b")
comprobar("prefijo de /v/ distinto del de /b/", prefijo(a) != prefijo(b))
comprobar("ninguna clase ni keyframes sin prefijo",
          all(c.startswith(prefijo(a)) for c in re.findall(r'class="([^"]+)"', a) for c in c.split())
          and all(k.startswith(prefijo(a)) for k in re.findall(r"@keyframes ([\w-]+)", a)))

# --- 3. La fonetica que confunde a un hispanohablante ------------------------
P = aa.parametros
comprobar("/v/ labiodental y /b/ bilabial",
          P("v").labios == "labiodental" and P("b").labios == "cerrados")
comprobar("/θ/ y /ð/ interdentales", P("θ").punta == P("ð").punta == "interdental")
comprobar("/t/ y /d/ con la punta tocando el alveolo",
          all(P(s).punta == "alveolar" and P(s).punta_toca for s in ("t", "d")))
comprobar("/ɹ/ sin tocar el paladar", not P("ɹ").punta_toca and P("ɹ").punta == "retrofleja")
comprobar("/ŋ/ velar y nasal", P("ŋ").dorso_velo and P("ŋ").velo_abierto)
comprobar("/ʃ/ con los labios redondeados", P("ʃ").labios in ("redondeados", "muy_redondeados"))
comprobar("/æ/ muy abierta", P("æ").mandibula >= 0.9)
comprobar("/i/ mas alta y adelantada que /ɪ/",
          P("i").cuerpo[0] > P("ɪ").cuerpo[0] and P("i").cuerpo[1] > P("ɪ").cuerpo[1])
comprobar("/u/ mas alta, mas atras y mas redondeada que /ʊ/",
          P("u").cuerpo[0] > P("ʊ").cuerpo[0] and P("u").cuerpo[1] < P("ʊ").cuerpo[1]
          and P("u").labios == "muy_redondeados")
comprobar("diptongos con dos objetivos distintos",
          all(P(s).hacia is not None and P(s).hacia.cuerpo != P(s).cuerpo
              for s in ("eɪ", "aɪ", "ɔɪ", "oʊ", "aʊ")))
comprobar("RP /əʊ/ empieza central y sin redondear",
          P("əʊ", "rp").cuerpo[1] == 0.5 and P("əʊ", "rp").labios == "neutros"
          and P("oʊ", "ga").labios == "redondeados")
comprobar("RP comparte la articulacion de la clave (/p/, /iː/)",
          P("p", "rp") is P("p") and P("iː", "rp") is P("i"))
comprobar("RP tiene sus sonidos propios", all(P(s, "rp") is not None for s in ("ɒ", "ɜː", "ɪə", "eə", "ʊə")))
comprobar("las nasales abren el velo y las demas no",
          all(p.velo_abierto == (p.movimiento == "nasal") for p in aa.PARAMETROS.values()))

# Contactos medidos sobre la geometria: la punta de /t/ en el alveolo (detras
# del cuello de los incisivos), la de /θ/ por delante de ellos.
pose_t = aa._pose(aa._resolver(P("t")))
pose_th = aa._pose(aa._resolver(P("θ")))
pose_r = aa._pose(aa._resolver(P("ɹ")))
x_t, y_t = pose_t["j0"]
dist_t = min(((x_t - x) ** 2 + (y_t - y) ** 2) ** 0.5 for x, y in aa._PUNTOS_PALADAR) - aa._RADIOS[0]
comprobar("geometria: la punta de /t/ toca el paladar", dist_t <= 0.5, f"{dist_t:.1f}")
comprobar("geometria: la punta de /t/ queda detras de los incisivos", x_t - aa._RADIOS[0] > 70, f"x={x_t:.1f}")
comprobar("geometria: la punta de /θ/ asoma delante de los incisivos", pose_th["j0"][0] < aa._INCISIVO_SUP[0])
x_r, y_r = pose_r["j0"]
dist_r = min(((x_r - x) ** 2 + (y_r - y) ** 2) ** 0.5 for x, y in aa._PUNTOS_PALADAR) - aa._RADIOS[0]
comprobar("geometria: la punta de /ɹ/ no toca el paladar", dist_r > 3, f"{dist_r:.1f}")

# --- 4. Entradas raras ---------------------------------------------------------
for raro in ("x", "", "ʔ", "tʃʃ", None, 5, "p", "ɒ"):
    for acento in ("ga", "zz"):
        try:
            r = aa.svg_articulacion(raro, acento)
            q = aa.svg_articulacion_quieto(raro, acento)
            esperado_none = not (raro == "p" and acento == "ga")
            if esperado_none:
                comprobar(f"simbolo {raro!r} en {acento!r} da None", r is None and q is None)
        except Exception as e:  # noqa: BLE001
            comprobar(f"simbolo {raro!r} en {acento!r} no revienta", False, repr(e))
comprobar("/ɒ/ no existe en GA", aa.svg_articulacion("ɒ", "ga") is None)
comprobar("/r/ no existe en GA pero si en RP",
          aa.svg_articulacion("r", "ga") is None and aa.svg_articulacion("r", "rp") is not None)

# --- 5. Palabras ---------------------------------------------------------------
def simbolos(ipa, acento="ga"):
    return [s.simbolo for s in aa.trocear(ipa, acento)[1]]


comprobar("trocear «mostly»: diptongo antes que la o", simbolos("/ˈmoʊstli/") == ["m", "oʊ", "s", "t", "l", "i"],
          str(simbolos("/ˈmoʊstli/")))
comprobar("trocear «thought» britanico", simbolos("[ˈθɔːt]", "rp") == ["θ", "ɔː", "t"], str(simbolos("[ˈθɔːt]", "rp")))
comprobar("trocear «judge»: africada antes que la d", simbolos("/dʒʌdʒ/") == ["dʒ", "ʌ", "dʒ"],
          str(simbolos("/dʒʌdʒ/")))
comprobar("trocear con ligadura t͡ʃ", simbolos("/t͡ʃɪp/") == ["tʃ", "ɪ", "p"], str(simbolos("/t͡ʃɪp/")))
comprobar("trocear ignora ɾ, ʔ y diacriticos", simbolos("/ˈwɔɾɚʔ̃/") == ["w", "ɔ", "ɚ"], str(simbolos("/ˈwɔɾɚʔ̃/")))
comprobar("trocear RP: «water» sin r", simbolos("[ˈwɔːtə]", "rp") == ["w", "ɔː", "t", "ə"])
segs = aa.trocear("/ˈmoʊstli/")[1]
comprobar("acento primario en la silaba de «mostly»", [s.acento_silaba for s in segs] == [1, 1, 0, 0, 0, 0])

mostly = aa.svg_palabra("/ˈmoʊstli/")
svg_limpio("palabra «mostly»", mostly, LIMITE_PALABRA)
svg_limpio("palabra «thought» RP", aa.svg_palabra("[ˈθɔːt]", "rp"), LIMITE_PALABRA)
svg_limpio("palabra «judge»", aa.svg_palabra("/dʒʌdʒ/"), LIMITE_PALABRA)
svg_limpio("palabra con simbolos raros", aa.svg_palabra("/ˈwɔɾɚʔ̃/"), LIMITE_PALABRA)
largo = "/ˌɪntəˈnæʃənəli/"
comprobar("palabra de 10 fonemas o mas", len(simbolos(largo)) >= 10, str(simbolos(largo)))
svg_limpio("palabra larga «internationally»", aa.svg_palabra(largo), LIMITE_PALABRA)
comprobar("una IPA vacia da None", aa.svg_palabra("") is None and aa.svg_palabra("//") is None)
comprobar("una IPA sin fonemas reconocibles da None", aa.svg_palabra("/ɾʔ/") is None)
comprobar("una IPA que no es texto da None", aa.svg_palabra(None) is None and aa.svg_palabra(42) is None)
comprobar("un acento desconocido da None", aa.svg_palabra("/kæt/", "au") is None)

# Duraciones: vocal mas larga que consonante; acentuada un 40 % mas.
linea, tramos, _ = aa._linea_palabra(aa.trocear("/ˈkætæt/")[1])
d = [b - a for a, b in tramos]
comprobar("la vocal dura mas que la consonante", d[1] > d[0] and d[3] > d[2])
comprobar("la silaba acentuada dura un 40 % mas", abs(d[1] / d[3] - 1.4) < 0.01, f"{d[1] / d[3]:.2f}")
linea, tramos, _ = aa._linea_palabra(aa.trocear("/ˌkætæt/")[1])
d = [b - a for a, b in tramos]
comprobar("la silaba con acento secundario dura un 15 % mas", abs(d[1] / d[3] - 1.15) < 0.01, f"{d[1] / d[3]:.2f}")
comprobar("la palabra resalta cada fonema", all(f"-k{i}" in mostly for i in range(6)))
comprobar("dos palabras con prefijos distintos", prefijo(mostly) != prefijo(aa.svg_palabra("/dʒʌdʒ/")))

print()
print(f"pesos de los SVG de sonido: minimo {min(pesos)}, medio {sum(pesos) // len(pesos)}, maximo {max(pesos)} bytes")
if FALLOS:
    print(f"{len(FALLOS)} FALLOS")
    sys.exit(1)
print("todo ok")
