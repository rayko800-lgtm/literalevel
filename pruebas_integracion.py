"""El recorrido completo del lector, de principio a fin, encadenado.

`pruebas_extremas.py` comprueba que nada revienta con entradas absurdas.
`tests_smoke.py`, `pruebas_lexicon.py` y `pruebas_desambiguacion.py` comprueban
cada modulo por su cuenta. Falta lo de en medio: que **la cadena aguante**.

Abrir un libro -> medirlo -> consultar una palabra -> que esa palabra aparezca
en el cuaderno -> cerrar y volver al mismo capitulo. Cada eslabon usa la salida
del anterior, que es justo donde se rompen las cosas cuando dos agentes tocan
modulos distintos del mismo repositorio.

No usa red ni gasta OpenAI: la consulta lexica se fuerza a la rama sin clave.
No toca los datos reales de nadie: cuaderno, marcapaginas y perfil se
redirigen a un directorio temporal.

Uso:  python -X utf8 pruebas_integracion.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "app")
import cuaderno  # noqa: E402
import ui  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="literalevel_integracion_"))
FALLOS: list[str] = []
PASOS = 0


def paso(nombre: str, condicion, detalle: str = ""):
    global PASOS
    PASOS += 1
    ok = bool(condicion)
    print(f"  {'ok   ' if ok else 'FALLA'} {nombre:<52} {detalle}")
    if not ok:
        FALLOS.append(f"{nombre} — {detalle}")


# --- Aislamiento: nada de esto puede tocar los datos reales ---------------

_CUADERNO = str(TMP / "cuaderno.db")
_registrar, _ultimas, _repasar, _contar = (
    cuaderno.registrar, cuaderno.ultimas, cuaderno.para_repasar, cuaderno.contar)
cuaderno.registrar = lambda **k: _registrar(**{**k, "ruta": _CUADERNO})
cuaderno.ultimas = lambda n=20, ruta=None: _ultimas(n, _CUADERNO)
cuaderno.para_repasar = lambda n=5, ruta=None: _repasar(n, _CUADERNO)
cuaderno.contar = lambda ruta=None: _contar(_CUADERNO)
ui.RUTA_SESION = TMP / "sesion.json"


def _libro_de_prueba() -> tuple[str, str]:
    """Un epub real si lo hay; si no, un txt generado. Devuelve (ruta, que es)."""
    for candidato in (ui.RUTA_LIBROS / "pg11.epub",
                      Path.home() / "Downloads" / "dokumen.pub_notes-from-a-dead-house.epub"):
        if candidato.exists():
            return str(candidato), f"epub real ({candidato.name})"
    parrafo = (
        "The prison stood at the edge of the fortress, right by the rampart. "
        "You could look at the world through the chinks in the fence, and the "
        "sentries paced up and down the wall by day and by night. Beyond the "
        "gates was the bright free world, and the prisoners thought of it as "
        "something impossible, almost a fairy tale. "
    )
    ruta = TMP / "libro.txt"
    ruta.write_text("CHAPTER I\n\n" + (parrafo * 14) + "\n\n" + (parrafo * 14),
                    encoding="utf-8")
    return str(ruta), "txt generado (no habia epub a mano)"


print("=" * 74)
ruta_libro, que_es = _libro_de_prueba()
print(f"libro de prueba: {que_es}")
print("=" * 74)

# --- 1. Abrir el libro ----------------------------------------------------

print("\n1) Abrir el libro")
libro, desplegable, html, resumen = ui._abrir(ruta_libro)
paso("se abre y tiene capitulos", libro is not None and libro.capitulos,
     f"{len(libro.capitulos) if libro else 0} capitulos")
if libro is None:
    print("\nSin libro no hay recorrido que probar.")
    sys.exit(1)

idx = desplegable["value"]
paso("no abre en la portadilla", idx is not None,
     f"empieza en el capitulo {idx + 1}")
paso("el capitulo inicial tiene cuerpo", libro.capitulos[idx].palabras >= 300,
     f"{libro.capitulos[idx].palabras} palabras")
paso("el lector devuelve prosa, no un volcado", html.count("<p>") >= 3,
     f"{html.count('<p>')} parrafos")
paso("deja marcapaginas al abrir", ui.RUTA_SESION.exists())

# --- 2. Navegar ------------------------------------------------------------

print("\n2) Navegar entre capitulos")
siguiente = ui._mover(libro, idx, 1)["value"]
paso("avanza un capitulo", siguiente == min(idx + 1, len(libro.capitulos) - 1),
     f"{idx + 1} -> {siguiente + 1}")
html2, cabecera = ui._capitulo(libro, siguiente)
paso("el capitulo nuevo se pinta", html2.count("<p>") >= 1 and cabecera != "")
paso("el marcapaginas sigue al lector",
     ui._leer_sesion() and ui._leer_sesion()["capitulo"] == siguiente,
     f"guardado: capitulo {ui._leer_sesion()['capitulo'] + 1}")

# --- 3. Medir la dificultad con el modelo v4 -------------------------------

print("\n3) Medir la dificultad (modelo v4)")
# `_medir` es generadora: avisa de la espera y luego da el resultado.
tramos_medir = list(ui._medir(libro, siguiente))
paso("avisa antes de cargar el modelo", len(tramos_medir) >= 2,
     tramos_medir[0][:52] if tramos_medir else "")
veredicto = tramos_medir[-1]
paso("devuelve una puntuacion, no un aviso", "/ 2.00" in veredicto,
     veredicto.split("·")[0].strip()[:46])
paso("dice cuantos bloques uso", "bloques" in veredicto)

# --- 4. Consultar una palabra del texto ------------------------------------

print("\n4) Consultar una palabra del capitulo")
texto_cap = libro.capitulos[siguiente].texto
# La palabra se saca del propio capitulo: una lista fija solo funciona con el
# libro para el que se escribio, y aqui el libro depende de lo que haya a mano.
import re as _re  # noqa: E402
_candidatas = _re.findall(r"\b[a-z]{6,12}\b", texto_cap.lower())
palabra = next((w for w in _candidatas
                if len(ui._oracion_de(texto_cap, w).split()) >= 6), None)
paso("encuentra una palabra con su oracion en el capitulo", palabra is not None,
     f"palabra: {palabra}")

if palabra:
    ui.consultor()._sin_clave = True          # sin red ni gasto
    # _consultar es generadora: se consume y se mira el resultado final.
    ficha = reproductores = ""
    audio = None
    for ficha, reproductores, audio in ui._consultar(None, libro, siguiente,
                                                     palabra, ""):
        pass
    paso("la ficha se construye", ficha.startswith("##"), ficha.split("\n")[0][:46])
    paso("trae fonetica o dice que no la hay",
         "Pronunciación" in ficha or "diccionario" in ficha.lower())
    paso("cita la oracion del libro", "\n> " in ficha)
    paso("degrada con elegancia sin clave", "[!]" in ficha,
         "avisa de lo que falta en vez de fallar")

# --- 5. La palabra llega al cuaderno ---------------------------------------

print("\n5) El cuaderno recoge lo consultado")
total, lemas, libros_distintos = cuaderno.contar()
paso("queda registrada", total >= 1, f"{total} consultas, {lemas} lemas")
ultimas = cuaderno.ultimas(5)
paso("guarda la frase del libro, no solo la palabra",
     ultimas and len(ultimas[0].oracion.split()) > 3,
     f'"{ultimas[0].oracion[:44]}..."' if ultimas else "")
paso("guarda de que libro y capitulo salio",
     ultimas and ultimas[0].libro and ultimas[0].capitulo == siguiente + 1,
     f"{ultimas[0].libro}, cap. {ultimas[0].capitulo}" if ultimas else "")
vista = ui._mis_palabras()
paso("la pestana muestra la palabra", palabra and palabra in vista)
paso("'Repasa 5' devuelve algo util", len(ui._repasar()) > 20)

# --- 6. Cerrar y volver ----------------------------------------------------

print("\n6) Cerrar la app y volver")
libro_r, desplegable_r, html_r, aviso_r, pestana = ui._reanudar()
paso("recupera el libro", libro_r is not None and
     libro_r.titulo == libro.titulo, libro_r.titulo if libro_r else "")
paso("vuelve al capitulo exacto", desplegable_r["value"] == siguiente,
     f"capitulo {siguiente + 1}")
paso("lo dice en cristiano", "seguías en el capítulo" in aviso_r,
     aviso_r[:52])
paso("abre directamente en la pestana de lectura",
     getattr(pestana, "selected", None) == "leer")

# --- 7. La frase para practicar sale del capitulo abierto ------------------

print("\n7) Enlace con la practica de voz")
frase = ui._frase_del_capitulo(libro, siguiente)
paso("trae una frase del capitulo", 6 <= len(frase.split()) <= 25,
     f'"{frase[:46]}..."')
paso("no arrastra el encabezado del capitulo",
     not frase.startswith(libro.titulo), "empieza en prosa, no en el titulo")

# --- Resultado -------------------------------------------------------------

print("\n" + "=" * 74)
if FALLOS:
    print(f"{len(FALLOS)} FALLOS de {PASOS} pasos:\n")
    for f in FALLOS:
        print("  -", f)
    sys.exit(1)
print(f"Los {PASOS} pasos del recorrido encadenan bien.")
