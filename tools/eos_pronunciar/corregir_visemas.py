"""Corrige los visemas de Eos en `curvas.json` antes de grabar: /p b m/ cierran los labios y la lengua no se va de lado ni fuera.

    python -X utf8 tools/eos_pronunciar/corregir_visemas.py                 # todos los clips de D:/literalevel_eos_pronunciar/visor/clips
    python -X utf8 tools/eos_pronunciar/corregir_visemas.py --solo ga_006d  # uno (la /m/ del General American)
    python -X utf8 tools/eos_pronunciar/corregir_visemas.py --informe       # solo mide, no escribe

Lo pidió Miguel el 4 oct 2026 tras grabar la demo: «en la M no cierra los labios, en la P no
se ve la explosión; la lengua se mueve hacia los lados e incluso sobrepasa los dientes».
Medido en `front/public/eos/ga/006d.mp4` (/m/) y `ga/0070.mp4` (/p/): en los 2,4 s de los
tres sonidos sostenidos los labios no llegan a tocarse en ningún fotograma. La boca de Eos
es Audio2Face-3D (52 ARKit a `fps`) y la «garantía» de cierre que `generar.py` le pone
encima es la de Blender, 0,06 de cierre (informe del 26 sep, §3): no basta para que el
visor junte los labios.

Este guion no toca `generar.py` (vive en otra rama) ni el visor: actúa sobre el
`curvas.json` que `generar_clips.py` deja en cada clip, y `grabar_clips.py --rehacer`
graba el resultado. Es idempotente: la primera vez guarda `curvas.sin_corregir.json` y
siempre parte de esa copia.

Qué hace, por fotograma:
- Cierre bilabial. Con la línea de fonemas del clip (`guion.fonemas`, que `generar_clips.py`
  guarda: ARPAbet, inicio, fin y si es el sonido aislado), en cada /m/ el cierre dura todo el
  tramo; en /p b/ el cierre precede a la explosión (en el sonido aislado, el tramo sonoro ES
  la explosión: se cierra 180 ms antes; dentro de una palabra, el fono cubre cierre y
  explosión: se suelta 35 ms antes de su fin). Con rampas suaves de 50/40 ms: `jawOpen` baja
  a 0,02, `mouthClose` y `mouthPress*` suben, y lo que separa los labios (`mouthLowerDown*`,
  `mouthUpperUp*`, `mouthFunnel`, `mouthPucker`, `mouthRoll*`, `mouthShrug*`,
  `mouthStretch*`, `jawForward/Left/Right`) se apaga casi del todo.
- Explosión de /p b/ (4 oct, tarde: Miguel seguía sin ver la explosión en la P). En el
  momento del soplo los labios se separan de golpe y la boca se abre un poco (`jawOpen`,
  `mouthLowerDown*`, `mouthUpperUp*` suben en 30 ms y vuelven en 200 ms a lo que diga
  Audio2Face; `mouthClose`/`mouthPress*` caen), y en los 100 ms anteriores los carrillos se
  hinchan un poco con la presión (`cheekPuff`). En /p/ más que en /b/; en /m/ no hay.
- Lengua. Cualquier curva de lengua con «left»/«right» en el nombre se pone a cero (en
  inglés ningún sonido la mueve de lado) y las de «out» se acotan a 0,10, salvo en /θ ð/
  (ARPAbet th/dh), donde se permite hasta 0,55 (la punta sí asoma entre los dientes).
  Si las curvas de lengua no vienen en el json (la lengua de Eos la mueve el visor con las
  poses de Blender), se dice en el informe y no se inventa nada.

Sin fonemas (un `curvas.json` de otra procedencia) solo se corrige la lengua. Si el json
trae `palabras` con tiempos ([texto, inicio, fin], el formato que `generar.py` recibe de
whisper), los fonemas se derivan con los diccionarios del motor (`app/fonemas.py`) y, si
no están, con las letras p/b/m/th de cada palabra: peor que g2p, pero suficiente para
cerrar la boca donde toca.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
TRABAJO = Path(os.environ.get("LITERALEVEL_EOS_TRABAJO", "D:/literalevel_eos_pronunciar"))
CLIPS = TRABAJO / "visor" / "clips"
COPIA = "curvas.sin_corregir.json"

BILABIALES = {"p", "b", "m"}
NASALES = {"m"}
INTERDENTALES = {"th", "dh"}

# Cuánto se cierra y qué se apaga durante el cierre (fracción que sobrevive).
JAW_CERRADO = 0.02
MOUTH_CLOSE_MIN = 0.70
MOUTH_PRESS_MIN = 0.35
APAGAR = 0.12
SUBEN = {"mouthClose": MOUTH_CLOSE_MIN, "mouthPressLeft": MOUTH_PRESS_MIN, "mouthPressRight": MOUTH_PRESS_MIN}
SE_APAGAN = ("mouthLowerDownLeft", "mouthLowerDownRight", "mouthUpperUpLeft", "mouthUpperUpRight",
             "mouthFunnel", "mouthPucker", "mouthRollLower", "mouthRollUpper", "mouthShrugLower",
             "mouthShrugUpper", "mouthStretchLeft", "mouthStretchRight", "jawForward", "jawLeft", "jawRight")
RAMPA_ENTRADA_S = 0.05
RAMPA_SALIDA_S = 0.04
# /p b/ aislados: el tramo sonoro es la explosión; el cierre va delante.
CIERRE_ANTES_EXPLOSION_S = 0.18
TRAS_EXPLOSION_S = 0.015
# /p b/ dentro de una palabra: el fono cubre cierre + explosión.
ANTES_FONO_S = 0.06
SUELTA_ANTES_DEL_FIN_S = 0.035
# Explosión de /p b/: subida, meseta y vuelta; lo que sube como mínimo; carrillos antes del soplo.
EXPLOSION_SUBIDA_S = 0.03
EXPLOSION_MESETA_S = 0.06
EXPLOSION_BAJADA_S = 0.20
EXPLOSION = {"p": {"jawOpen": 0.22, "mouthLowerDownLeft": 0.30, "mouthLowerDownRight": 0.30,
                   "mouthUpperUpLeft": 0.12, "mouthUpperUpRight": 0.12},
             "b": {"jawOpen": 0.16, "mouthLowerDownLeft": 0.22, "mouthLowerDownRight": 0.22,
                   "mouthUpperUpLeft": 0.08, "mouthUpperUpRight": 0.08}}
EXPLOSION_APAGA = ("mouthClose", "mouthPressLeft", "mouthPressRight")
CARRILLOS = {"p": 0.25, "b": 0.12}
CARRILLOS_ANTES_S = 0.12
LENGUA_FUERA_MAX = 0.10
LENGUA_FUERA_INTERDENTAL = 0.55
MARGEN_INTERDENTAL_S = 0.04


def _arpabet(simbolo: str) -> str:
    return re.sub(r"\d", "", str(simbolo or "")).strip().lower()


# Un fono sin otro detrás en este margen es un sonido suelto (las tres repeticiones de cada clip).
HUECO_AISLADO_S = 0.05


def normalizar_fonemas(fonemas) -> list[dict]:
    """Admite [(arpa, t0, t1)], [[arpa, t0, t1]] y [{'arpabet', 't0', 't1', 'aislado'}].

    Si la línea no dice si el fono es un sonido suelto (los `curvas.json` de `generar_clips.py`
    traen solo arpabet y tiempos: el 4 oct por la mañana las tres /p/ sueltas de cada clip se
    trataron como /p/ dentro de palabra y los labios se abrían 130 ms después del soplo), se
    deduce: es suelto si ningún otro fono empieza en los 50 ms siguientes a su fin."""
    salida = []
    for f in fonemas or []:
        if isinstance(f, dict):
            arpa, t0, t1 = f.get("arpabet", ""), f.get("t0"), f.get("t1")
            aislado = None if f.get("aislado") is None else bool(f.get("aislado"))
        else:
            arpa, t0, t1 = f[0], f[1], f[2]
            aislado = bool(f[3]) if len(f) > 3 else None
        try:
            t0, t1 = float(t0), float(t1)
        except (TypeError, ValueError):
            continue
        if t1 <= t0:
            continue
        salida.append({"arpabet": _arpabet(arpa), "t0": t0, "t1": t1, "aislado": aislado})
    salida.sort(key=lambda f: f["t0"])
    for i, f in enumerate(salida):
        if f["aislado"] is None:
            siguiente = salida[i + 1]["t0"] if i + 1 < len(salida) else None
            f["aislado"] = siguiente is None or siguiente - f["t1"] > HUECO_AISLADO_S
    return salida


_IPA_BILABIAL = {"p": "p", "b": "b", "m": "m"}
_IPA_INTERDENTAL = {"θ": "th", "ð": "dh"}
_IPA_IGNORAR = set("ˈˌːˑ./[] ()‿.")


def _simbolos_ipa(ipa: str) -> list[str]:
    """Los sonidos de una IPA de los diccionarios, sin marcas de acento ni de largo."""
    s = [c for c in ipa if c not in _IPA_IGNORAR]
    # tʃ y dʒ cuentan como uno; el resto, letra a letra (basta para repartir tiempos).
    simbolos: list[str] = []
    i = 0
    while i < len(s):
        if i + 1 < len(s) and s[i] + s[i + 1] in ("tʃ", "dʒ"):
            simbolos.append(s[i] + s[i + 1])
            i += 2
        else:
            simbolos.append(s[i])
            i += 1
    return simbolos


def _fonemas_de_palabra_por_letras(texto: str) -> list[str]:
    letras = re.sub(r"[^a-z]", "", texto.lower())
    fonos = []
    i = 0
    while i < len(letras):
        if letras.startswith("th", i):
            fonos.append("th")
            i += 2
        elif letras.startswith("ph", i):
            fonos.append("f")
            i += 2
        else:
            c = letras[i]
            # «mb» final (lamb, comb): la b no suena.
            if c == "b" and i == len(letras) - 1 and i > 0 and letras[i - 1] == "m":
                fonos.append("")
            else:
                fonos.append(c if c in "pbm" else "x")
            i += 1
    return [f for f in fonos if f != ""] or ["x"]


def fonemas_de_palabras(palabras, acento: str = "ga") -> list[dict]:
    """[texto, t0, t1] → fonemas con tiempos repartidos a partes iguales dentro de la palabra.

    Con los diccionarios del motor (`app/fonemas.py`, Kaikki + CMUdict) si se pueden
    importar; si no, por las letras. Solo importa dónde caen /p b m/ y /θ ð/."""
    # `app/` entra en la ruta solo mientras se consulta: `fonemas.py` importa `lexicon`
    # al primer uso, y `generar_clips.py` necesita `app/` fuera para que `generar.py`
    # no confunda su `articulacion` con el del motor.
    ruta_app = str(RAIZ / "app")
    quitar = ruta_app not in sys.path
    if quitar:
        sys.path.insert(0, ruta_app)
    try:
        import fonemas as _fonemas  # noqa: E402

        ipa_de = _fonemas.ipa_de_palabra
    except Exception:  # noqa: BLE001  (sin motor: letras)
        ipa_de = None
    try:
        return _fonemas_de_palabras(palabras, acento, ipa_de)
    finally:
        if quitar and ruta_app in sys.path:
            sys.path.remove(ruta_app)


def _fonemas_de_palabras(palabras, acento: str, ipa_de) -> list[dict]:
    salida = []
    for p in palabras or []:
        try:
            texto, t0, t1 = str(p[0]), float(p[1]), float(p[2])
        except (TypeError, ValueError, IndexError):
            continue
        if t1 <= t0 or not texto.strip():
            continue
        fonos: list[str] = []
        if ipa_de is not None:
            try:
                # `app/fonemas.py` habla de US/UK; el guion de los clips, de ga/rp.
                ipa, _ = ipa_de(texto, acento="UK" if str(acento).lower() in ("rp", "uk") else "US")
            except Exception:  # noqa: BLE001
                ipa = None
            if ipa:
                fonos = [_IPA_BILABIAL.get(c, _IPA_INTERDENTAL.get(c, "x")) for c in _simbolos_ipa(ipa)]
        if not fonos:
            fonos = _fonemas_de_palabra_por_letras(texto)
        paso = (t1 - t0) / len(fonos)
        for i, f in enumerate(fonos):
            salida.append({"arpabet": f, "t0": t0 + i * paso, "t1": t0 + (i + 1) * paso, "aislado": False})
    return salida


def fonemas_del_json(datos: dict) -> tuple[list[dict], str]:
    """La línea de fonemas del clip y de dónde salió."""
    guion = datos.get("guion") or {}
    for origen, lista in (("guion.fonemas", guion.get("fonemas")), ("fonemas", datos.get("fonemas"))):
        f = normalizar_fonemas(lista)
        if f:
            return f, origen
    palabras = guion.get("palabras") or datos.get("palabras")
    if palabras:
        acento = guion.get("acento") or datos.get("acento") or "ga"
        f = fonemas_de_palabras(palabras, acento)
        if f:
            return f, "palabras"
    return [], "ninguno"


def _suavizar(x: np.ndarray) -> np.ndarray:
    return x * x * (3 - 2 * x)


def peso_cierre(n: int, fps: float, fonemas: list[dict]) -> np.ndarray:
    """0..1 por fotograma: cuánto están cerrados los labios por un /p b m/."""
    t = np.arange(n) / fps
    w = np.zeros(n)
    for f in fonemas:
        a = f["arpabet"]
        if a not in BILABIALES:
            continue
        if a in NASALES:
            ini, fin = f["t0"], f["t1"]
        elif f["aislado"]:
            ini, fin = f["t0"] - CIERRE_ANTES_EXPLOSION_S, f["t0"] + TRAS_EXPLOSION_S
        else:
            ini, fin = f["t0"] - ANTES_FONO_S, max(f["t0"] + 0.03, f["t1"] - SUELTA_ANTES_DEL_FIN_S)
        subida = np.clip((t - (ini - RAMPA_ENTRADA_S)) / RAMPA_ENTRADA_S, 0, 1)
        bajada = np.clip((fin + RAMPA_SALIDA_S - t) / RAMPA_SALIDA_S, 0, 1)
        w = np.maximum(w, _suavizar(subida) * _suavizar(bajada))
    return w


def _soltado(f: dict) -> float:
    """Instante del soplo de un /p b/: donde termina su cierre (ver `peso_cierre`)."""
    if f["aislado"]:
        return f["t0"] + TRAS_EXPLOSION_S
    return max(f["t0"] + 0.03, f["t1"] - SUELTA_ANTES_DEL_FIN_S)


def pesos_explosion(n: int, fps: float, fonemas: list[dict]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Por sonido (p, b): envolventes 0..1 por fotograma del soplo y de los carrillos previos."""
    t = np.arange(n) / fps
    soplo = {a: np.zeros(n) for a in EXPLOSION}
    carrillos = {a: np.zeros(n) for a in EXPLOSION}
    for f in fonemas:
        a = f["arpabet"]
        if a not in EXPLOSION:
            continue
        tb = _soltado(f)
        subida = np.clip((t - tb) / EXPLOSION_SUBIDA_S, 0, 1)
        bajada = np.clip((tb + EXPLOSION_SUBIDA_S + EXPLOSION_MESETA_S + EXPLOSION_BAJADA_S - t) / EXPLOSION_BAJADA_S, 0, 1)
        soplo[a] = np.maximum(soplo[a], _suavizar(subida) * _suavizar(bajada))
        hinchan = np.clip((t - (tb - CARRILLOS_ANTES_S)) / (CARRILLOS_ANTES_S - 0.03), 0, 1)
        sueltan = np.clip((tb + EXPLOSION_SUBIDA_S - t) / EXPLOSION_SUBIDA_S, 0, 1)
        carrillos[a] = np.maximum(carrillos[a], _suavizar(hinchan) * _suavizar(sueltan))
    return soplo, carrillos


def peso_interdental(n: int, fps: float, fonemas: list[dict]) -> np.ndarray:
    t = np.arange(n) / fps
    w = np.zeros(n, dtype=bool)
    for f in fonemas:
        if f["arpabet"] in INTERDENTALES:
            w |= (t >= f["t0"] - MARGEN_INTERDENTAL_S) & (t <= f["t1"] + MARGEN_INTERDENTAL_S)
    return w


def _es_lengua(clave: str) -> bool:
    return "tongue" in clave.lower() or clave.lower().startswith("lengua")


def corregir(datos: dict, fonemas: list[dict] | None = None) -> tuple[dict, dict]:
    """Devuelve (json corregido, informe). No modifica `datos`."""
    curvas = {k: np.asarray(v, dtype=float) for k, v in (datos.get("curvas") or {}).items()
              if isinstance(v, (list, tuple))}
    fps = float(datos.get("fps") or 0)
    if not curvas or fps <= 0:
        raise ValueError("curvas.json sin `fps` o sin `curvas`")
    n = len(next(iter(curvas.values())))
    if fonemas is None:
        fonemas, origen = fonemas_del_json(datos)
    else:
        origen = "parametro"
    informe: dict = {"fps": fps, "fotogramas": n, "fonemas": origen, "cierres": 0, "lengua": {}}

    w = peso_cierre(n, fps, fonemas) if fonemas else np.zeros(n)
    informe["cierres"] = int(np.sum((w[1:] > 0.5) & (w[:-1] <= 0.5)) + (1 if n and w[0] > 0.5 else 0))
    if "jawOpen" in curvas:
        dentro = w > 0.5
        informe["jawOpen_en_cierre_antes"] = round(float(curvas["jawOpen"][dentro].mean()), 3) if dentro.any() else None
    if informe["cierres"]:
        if "jawOpen" in curvas:
            curvas["jawOpen"] = curvas["jawOpen"] * (1 - w) + JAW_CERRADO * w
        for clave, minimo in SUBEN.items():
            if clave in curvas:
                curvas[clave] = curvas[clave] * (1 - w) + np.maximum(curvas[clave], minimo) * w
        for clave in SE_APAGAN:
            if clave in curvas:
                curvas[clave] = curvas[clave] * (1 - (1 - APAGAR) * w)
        if "jawOpen" in curvas and dentro.any():
            informe["jawOpen_en_cierre_despues"] = round(float(curvas["jawOpen"][dentro].mean()), 3)
    soplo, carrillos = pesos_explosion(n, fps, fonemas) if fonemas else ({}, {})
    informe["explosiones"] = 0
    for a, e in soplo.items():
        if not (e > 0.5).any():
            continue
        informe["explosiones"] += int(np.sum((e[1:] > 0.5) & (e[:-1] <= 0.5)) + (1 if e[0] > 0.5 else 0))
        for clave, minimo in EXPLOSION[a].items():
            if clave in curvas:
                curvas[clave] = np.maximum(curvas[clave], minimo * e)
        for clave in EXPLOSION_APAGA:
            if clave in curvas:
                curvas[clave] = curvas[clave] * (1 - e)
        if "cheekPuff" in curvas:
            curvas["cheekPuff"] = np.maximum(curvas["cheekPuff"], CARRILLOS[a] * carrillos[a])

    lengua = [k for k in curvas if _es_lengua(k)]
    informe["lengua"]["curvas"] = lengua
    if lengua:
        inter = peso_interdental(n, fps, fonemas) if fonemas else np.zeros(n, dtype=bool)
        laterales, fuera = [], []
        for k in lengua:
            bajo = k.lower()
            if "left" in bajo or "right" in bajo or "lado" in bajo:
                if np.abs(curvas[k]).max() > 0:
                    laterales.append(k)
                curvas[k] = np.zeros(n)
            elif "out" in bajo or "fuera" in bajo:
                tope = np.where(inter, LENGUA_FUERA_INTERDENTAL, LENGUA_FUERA_MAX)
                if (curvas[k] > tope).any():
                    fuera.append(k)
                curvas[k] = np.minimum(curvas[k], tope)
        informe["lengua"]["laterales_anuladas"] = laterales
        informe["lengua"]["fuera_acotadas"] = fuera
    else:
        informe["lengua"]["nota"] = ("sin curvas de lengua en el json: la lengua la pone el visor "
                                     "(poses de Blender); corregirla ahí")

    salida = dict(datos)
    salida["curvas"] = {**(datos.get("curvas") or {}), **{k: np.round(v, 5).tolist() for k, v in curvas.items()}}
    salida["visemas_corregidos"] = {"version": 2, "cierres": informe["cierres"], "explosiones": informe["explosiones"], "fonemas": origen,
                                    "lengua_lateral_a_cero": bool(lengua), "lengua_fuera_max": LENGUA_FUERA_MAX}
    return salida, informe


def corregir_archivo(ruta: Path, solo_informe: bool = False) -> dict:
    """Corrige `curvas.json` en su sitio a partir de la copia sin corregir (idempotente)."""
    ruta = Path(ruta)
    copia = ruta.with_name(COPIA)
    if not copia.exists():
        if solo_informe:
            origen = ruta
        else:
            copia.write_bytes(ruta.read_bytes())
            origen = copia
    else:
        origen = copia
    datos = json.loads(origen.read_text(encoding="utf-8"))
    salida, informe = corregir(datos)
    if not solo_informe:
        ruta.write_text(json.dumps(salida, ensure_ascii=False), encoding="utf-8")
    informe["clip"] = ruta.parent.name
    return informe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", default=str(CLIPS), help="carpeta con un subdirectorio por clip")
    ap.add_argument("--solo", default="", help="nombre del clip, p. ej. ga_006d")
    ap.add_argument("--informe", action="store_true", help="medir sin escribir")
    a = ap.parse_args()
    carpeta = Path(a.clips)
    rutas = sorted(p / "curvas.json" for p in carpeta.iterdir() if (p / "curvas.json").exists()) if carpeta.is_dir() else []
    if a.solo:
        rutas = [r for r in rutas if r.parent.name == a.solo]
    if not rutas:
        raise SystemExit(f"No hay curvas.json en {carpeta}")
    for r in rutas:
        inf = corregir_archivo(r, solo_informe=a.informe)
        lengua = inf["lengua"]
        if lengua.get("curvas"):
            resumen_lengua = (f"{len(lengua['curvas'])} curvas, laterales {len(lengua.get('laterales_anuladas', []))}, "
                              f"fuera {len(lengua.get('fuera_acotadas', []))}")
        else:
            resumen_lengua = "sin curvas (la pone el visor)"
        print(f"{inf['clip']}: fonemas={inf['fonemas']} cierres={inf['cierres']} explosiones={inf.get('explosiones', 0)} "
              f"jawOpen en cierre {inf.get('jawOpen_en_cierre_antes')}→{inf.get('jawOpen_en_cierre_despues')} "
              f"lengua={resumen_lengua}", flush=True)
    print(f"{len(rutas)} clips {'medidos' if a.informe else 'corregidos'}. Después: grabar_clips.py --rehacer")


if __name__ == "__main__":
    main()
