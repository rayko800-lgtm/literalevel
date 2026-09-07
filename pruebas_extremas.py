"""Pruebas extremas de la interfaz: intentan romper `app/ui.py` a proposito.

No prueban la logica de los modulos -de eso ya se encargan `tests_smoke.py`,
`pruebas_voz.py` y `pruebas_lexicon.py`- sino la capa que los une, que es donde
un usuario real mete cosas que nadie previo: archivos corruptos, indices fuera
de rango, HTML incrustado en un libro, consultas de 5000 caracteres.

La regla que se verifica es una sola y es la de `AGENTS.md`: **ningun manejador
puede lanzar una excepcion hacia Gradio**. Si algo falla, tiene que volver como
texto legible. Una excepcion aqui es un fallo de la prueba.

Uso:  python -X utf8 pruebas_extremas.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import traceback
import zipfile
from pathlib import Path

sys.path.insert(0, "app")
import ui  # noqa: E402

FALLOS: list[str] = []
HECHAS = 0


def prueba(nombre: str, fn):
    """Ejecuta `fn`. Que devuelva algo es exito; que lance, es fallo."""
    global HECHAS
    HECHAS += 1
    try:
        r = fn()
        resumen = str(r)
        if len(resumen) > 90:
            resumen = resumen[:87] + "..."
        print(f"  ok    {nombre:<46} {resumen}")
    except Exception as e:
        FALLOS.append(f"{nombre}: {type(e).__name__}: {e}")
        print(f"  FALLA {nombre:<46} {type(e).__name__}: {e}")
        traceback.print_exc(limit=3)


def titulo(t: str):
    print(f"\n--- {t} " + "-" * max(0, 60 - len(t)))


TMP = Path(tempfile.mkdtemp(prefix="literalevel_extremas_"))

# Lo primero de todo, antes de que ninguna prueba toque nada: montar la
# interfaz no puede cargar el modelo, ni el catalogo, ni el diccionario.
titulo("Arranque perezoso (antes de cualquier otra prueba)")
prueba("construir() no carga nada pesado",
       lambda: (len(ui.construir().blocks),
                ui._puntuador, ui._catalogo, ui._consultor))
assert (ui._puntuador, ui._catalogo, ui._consultor) == (None, None, None), \
    "construir() cargo un recurso pesado: la app tardara en abrir"

# `practicar()` registra en ~/.literalevel/voz.db las palabras falladas. Esto
# son pruebas, no practica real: no deben ensuciar los puntos debiles de nadie.
ui.voz.registrar_fallos = lambda *a, **k: None


def escribir(nombre: str, contenido: bytes | str) -> str:
    ruta = TMP / nombre
    modo, datos = ("wb", contenido) if isinstance(contenido, bytes) else ("w", contenido)
    with open(ruta, modo, encoding=None if "b" in modo else "utf-8") as f:
        f.write(datos)
    return str(ruta)


# --- 1. Archivos que no deberian abrirse ---------------------------------

titulo("Archivos rotos, vacios y disfrazados")

prueba("ruta inexistente", lambda: ui._abrir(str(TMP / "no_existe.epub"))[3])
prueba("None como archivo", lambda: ui._abrir(None)[3])
prueba("cadena vacia", lambda: ui._abrir("")[3])
prueba("txt vacio", lambda: ui._abrir(escribir("vacio.txt", ""))[3])
prueba("txt de una palabra", lambda: ui._abrir(escribir("corto.txt", "hola"))[3])
prueba("solo espacios", lambda: ui._abrir(escribir("blanco.txt", "   \n\n \t "))[3])
prueba("extension no soportada", lambda: ui._abrir(escribir("cosa.docx", "texto"))[3])
prueba("sin extension", lambda: ui._abrir(escribir("sinext", "texto"))[3])
prueba("binario disfrazado de txt",
       lambda: ui._abrir(escribir("falso.txt", bytes(range(256)) * 40))[3])
prueba("pdf corrupto",
       lambda: ui._abrir(escribir("roto.pdf", b"%PDF-1.4 basura no es un pdf"))[3])
prueba("epub que no es zip",
       lambda: ui._abrir(escribir("roto.epub", b"esto no es un zip"))[3])


def _epub_vacio():
    ruta = TMP / "vacio.epub"
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
    return ui._abrir(str(ruta))[3]


prueba("epub zip sin contenido", _epub_vacio)


# --- 2. Indices de capitulo imposibles ------------------------------------

titulo("Indices fuera de rango")

libro_ok, upd_ok, _, _ = ui._abrir(
    escribir("libro.txt", "The quick brown fox jumps over the lazy dog. " * 200))

prueba("capitulo None", lambda: ui._capitulo(libro_ok, None)[1])
prueba("libro None", lambda: ui._capitulo(None, 0)[1])
prueba("indice 999", lambda: ui._capitulo(libro_ok, 999)[1])
prueba("indice -5", lambda: ui._capitulo(libro_ok, -5)[1])
prueba("indice texto", lambda: ui._capitulo(libro_ok, "3")[1])
prueba("mover mas alla del final", lambda: ui._mover(libro_ok, 0, 99))
prueba("mover antes del principio", lambda: ui._mover(libro_ok, 0, -99))
prueba("mover sin libro", lambda: ui._mover(None, 0, 1))
prueba("medir indice imposible", lambda: ui._medir(libro_ok, 999))


# --- 3. El lector como superficie de ataque -------------------------------

titulo("HTML y unicode dentro del libro")


def _sin_escapar():
    h = ui._html_lectura("<script>alert('xss')</script>\n\nfin")
    assert "<script>" not in h, "el script quedo sin escapar"
    assert "&lt;script&gt;" in h
    return "escapado correctamente"


def _img_onerror():
    h = ui._html_lectura('<img src=x onerror="alert(1)">')
    assert "onerror=" not in h.replace("&quot;", '"') or "&lt;img" in h
    return "escapado"


prueba("script incrustado", _sin_escapar)
prueba("img onerror", _img_onerror)
prueba("comillas y ampersands", lambda: len(ui._html_lectura('a & b "c" <d>')))
prueba("texto vacio", lambda: ui._html_lectura("") [:40])
prueba("solo saltos de linea", lambda: ui._html_lectura("\n\n\n\n"))
prueba("emoji y CJK", lambda: len(ui._html_lectura("Hola 👋 世界 مرحبا\n\nfin")))
prueba("caracteres de control", lambda: len(ui._html_lectura("a\x00b\x07c\n\nd")))
prueba("10 mil parrafos", lambda: len(ui._html_lectura("parrafo.\n\n" * 10000)))
prueba("una linea de 2 MB", lambda: len(ui._html_lectura("palabra " * 250000)))


# --- 4. Consulta lexica: entradas absurdas --------------------------------
# Solo los caminos que devuelven antes de tocar el diccionario: cargarlo son
# 243 MB, spaCy y MiniLM, y eso ya lo cubre pruebas_lexicon.py.

titulo("Consulta lexica (validacion previa)")

prueba("palabra vacia", lambda: ui._consultar(None, None, None, "", "")[0])
prueba("solo espacios", lambda: ui._consultar(None, None, None, "   ", "")[0])
prueba("None como palabra", lambda: ui._consultar(None, None, None, None, "")[0])
prueba("frase de 10 palabras",
       lambda: ui._consultar(None, None, None, "a b c d e f g h i j", "")[0])
prueba("palabra de 5000 caracteres",
       lambda: ui._consultar(None, None, None, "x" * 5000, "")[0][:60])

prueba("oracion localizada en el capitulo",
       lambda: ui._oracion_de(libro_ok.capitulos[0].texto, "fox")[:50])
prueba("palabra que no esta en el capitulo",
       lambda: repr(ui._oracion_de(libro_ok.capitulos[0].texto, "zzzznoexiste")))
prueba("regex en la palabra buscada",
       lambda: repr(ui._oracion_de(libro_ok.capitulos[0].texto, "f.x")))
prueba("parentesis sin cerrar",
       lambda: repr(ui._oracion_de(libro_ok.capitulos[0].texto, "(((")))
prueba("oracion sin libro", lambda: repr(ui._oracion_de("", "algo")))
prueba("frase para practicar", lambda: ui._frase_del_capitulo(libro_ok, 0)[:50])
prueba("frase sin libro", lambda: repr(ui._frase_del_capitulo(None, 0)))


# --- 5. Fichas lexicas degeneradas ----------------------------------------

titulo("Renderizado de la ficha")


class _Vacio:
    """Un ResultadoLexico en el que todo salio mal."""
    palabra_superficie = lema_buscado = "x"
    categoria = sentido = None
    ipa_uk = ipa_us = audio_uk = audio_us = None
    etiquetas_sentido: list = []
    n_sentidos_candidatos = 0
    similitud = frecuencia_zipf = None
    definicion_contextual = explicacion_gramatical = None
    explicacion_adaptada = ejemplo_simplificado = None
    banda_lector = "básico"
    desde_cache = audio_generado = False
    avisos: list = []


prueba("ficha con todo a None", lambda: len(ui._ficha(_Vacio())))
prueba("reproductores sin audio", lambda: repr(ui._reproductores(_Vacio())))
prueba("audio local inexistente", lambda: ui._local("C:/no/existe.mp3"))
prueba("audio remoto no es local", lambda: ui._local("https://x.org/a.ogg"))
prueba("audio None", lambda: ui._local(None))


# --- 5 bis. Abrir del catalogo y corregir pronunciacion -------------------
# Sin red: solo los caminos que se rechazan antes de salir a internet.

titulo("Abrir un libro del catalogo")

prueba("id vacio", lambda: ui._abrir_del_catalogo("")[3])
prueba("id None", lambda: ui._abrir_del_catalogo(None)[3])
prueba("StoryWeaver no es de Gutenberg",
       lambda: ui._abrir_del_catalogo("SWgdlgdl42")[3][:60])
prueba("id sin digitos", lambda: ui._abrir_del_catalogo("PG")[3][:60])
prueba("id con inyeccion", lambda: ui._abrir_del_catalogo("PG1;rm -rf /")[3][:60])
prueba("opciones vacias", lambda: ui._opciones_libros([]))


class _LibroFalso:
    id, titulo, autor, nivel = "PG42", "Un libro", "Alguien", "B1"
    gancho, descargas, similitud, afinidad = "", 0, 0.0, 0.0
    url_gutenberg = "https://www.gutenberg.org/ebooks/42"


prueba("opciones con un libro de Gutenberg",
       lambda: ui._opciones_libros([_LibroFalso()])["choices"])

titulo("Correccion de pronunciacion palabra a palabra")

_ev = ui.voz.evaluar_pronunciacion(
    "Our prison stood at the edge of the fortress",
    "Our prison stood at the age of the fortes")
prueba("marca bien y mal",
       lambda: (_ev.palabras_falladas, ui._palabras_html(_ev, True).count('class="ll-w')))
prueba("sin transcripcion no inventa marcas",
       lambda: "no puedo marcarte" in ui._palabras_html(_ev, False))
prueba("frase vacia",
       lambda: repr(ui._palabras_html(ui.voz.evaluar_pronunciacion("", ""), True)))
prueba("html incrustado en la frase",
       lambda: "&lt;" in ui._palabras_html(
           ui.voz.evaluar_pronunciacion("<script>alert(1)</script> hello", "hello"), True))

titulo("Cuaderno de palabras")

import cuaderno  # noqa: E402

_CDB = str(TMP / "cuaderno.db")

prueba("base vacia", lambda: (cuaderno.contar(_CDB), cuaderno.ultimas(5, _CDB)))
prueba("registrar una consulta",
       lambda: cuaderno.registrar(palabra="fetters", lema="fetter",
                                  oracion="the convicts were in fetters",
                                  zipf=2.3, libro="Dead House", capitulo=5,
                                  ruta=_CDB))
prueba("palabra vacia se rechaza",
       lambda: cuaderno.registrar(palabra="", lema="x", oracion="y", ruta=_CDB))
prueba("oracion en blanco se rechaza",
       lambda: cuaderno.registrar(palabra="x", lema="x", oracion="   ", ruta=_CDB))
prueba("ruta imposible no lanza",
       lambda: (cuaderno.registrar(palabra="a", lema="a", oracion="b",
                                   ruta="Z:/no/existe/c.db"),
                cuaderno.contar("Z:/no/existe/c.db"),
                cuaderno.ultimas(3, "Z:/no/existe/c.db"),
                cuaderno.para_repasar(3, "Z:/no/existe/c.db")))
prueba("html y comillas en la frase",
       lambda: cuaderno.registrar(palabra="<b>", lema="<b>",
                                  oracion="a \"quoted\" <tag> & more", ruta=_CDB))
prueba("n negativo o cero no rompe",
       lambda: (len(cuaderno.ultimas(0, _CDB)), len(cuaderno.para_repasar(-3, _CDB))))
prueba("repasar agrupa por lema",
       lambda: (cuaderno.registrar(palabra="fetters", lema="fetter",
                                   oracion="in fetters again", zipf=2.3, ruta=_CDB),
                len([a for a in cuaderno.para_repasar(9, _CDB) if a.lema == "fetter"]))[1])
prueba("rareza sin zipf", lambda: repr(cuaderno.Anotacion(
    "x", "x", None, None, "o", None, None, None, "2026").rareza))

titulo("Reanudar la sesion")

# El marcapaginas de verdad no se toca: se apunta a uno de usar y tirar.
ui.RUTA_SESION = TMP / "sesion.json"

prueba("sin sesion guardada", lambda: repr(ui._reanudar()[3]))
prueba("json corrupto",
       lambda: (ui.RUTA_SESION.write_text("{roto", encoding="utf-8"),
                repr(ui._reanudar()[3]))[1])
prueba("apunta a un archivo borrado",
       lambda: (ui._guardar_sesion(str(TMP / "fantasma.epub"), "X", 3),
                repr(ui._reanudar()[3]))[1])
prueba("capitulo fuera de rango en el marcapaginas",
       lambda: (ui._guardar_sesion(str(TMP / "libro.txt"), "libro", 9999),
                ui._reanudar()[1]["value"])[1])
prueba("capitulo negativo",
       lambda: (ui._guardar_sesion(str(TMP / "libro.txt"), "libro", -7),
                ui._reanudar()[1]["value"])[1])
prueba("capitulo no numerico",
       lambda: (ui._guardar_sesion(str(TMP / "libro.txt"), "libro", 0),
                ui.RUTA_SESION.write_text('{"ruta":"%s","titulo":"libro",'
                                          '"capitulo":"tres"}'
                                          % str(TMP / "libro.txt").replace("\\", "/"),
                                          encoding="utf-8"),
                ui._reanudar()[1]["value"])[2])
prueba("guardar en una ruta imposible no revienta",
       lambda: (setattr(ui, "RUTA_SESION", Path("Z:/no/existe/sesion.json")),
                ui._guardar_sesion("x", "y", 0),
                setattr(ui, "RUTA_SESION", TMP / "sesion.json"), "sin excepcion")[3])

titulo("Idioma de la explicacion")

prueba("idioma invalido no revienta",
       lambda: ui._consultar(None, None, None, "", "", "klingon")[0])
prueba("idiomas admitidos", lambda: ui.ConsultorLexico.consultar.__doc__ is not None)


# --- 6. Buscador del catalogo ---------------------------------------------

titulo("Buscador (sin cargar embeddings)")

prueba("consulta vacia sin perfil", lambda: ui._buscar(None, "", False, 10)[:70])
prueba("recomendar sin perfil", lambda: ui._recomendar(None, 10)[:70])
prueba("tabla de libros vacia", lambda: ui._tabla_libros([], "nada encontrado"))
prueba("tabla sin aviso", lambda: ui._tabla_libros([]))


# --- 7. Perfil ------------------------------------------------------------

titulo("Perfil")

prueba("cuestionario sin responder",
       lambda: ui._desde_cuestionario(None, "", None, None, None)[1][:70])
prueba("muestra vacia", lambda: ui._desde_muestra(None, "", "")[1][:70])
prueba("muestra que no es prosa",
       lambda: ui._desde_muestra(None, "", "- uno\n- dos\n- tres")[1][:70])
prueba("describir perfil None", lambda: ui._describir(None)[:60])


# --- 8. Voz ---------------------------------------------------------------

titulo("Voz")

prueba("sin audio ni frase", lambda: ui._practicar(None, "")[0][:60])
prueba("frase sin audio", lambda: ui._practicar(None, "hello world")[0][:60])
prueba("audio inexistente",
       lambda: ui._practicar(str(TMP / "no_existe.wav"), "hello")[0][:60])
prueba("puntos debiles", lambda: ui._debiles()[:60])


# --- 9. La app entera se monta --------------------------------------------

titulo("Montaje")

prueba("construir() dos veces seguidas",
       lambda: (len(ui.construir().blocks), len(ui.construir().blocks)))


def _rutas_permitidas():
    """Regresion doble, y las dos direcciones importan.

    Hacia arriba: sin `allowed_paths`, los mp3 de tts-1 no llegan al navegador
    y Gradio revienta con InvalidPathError *despues* de pagar la llamada.

    Hacia abajo: todo lo que cae bajo un allowed_path se sirve por
    GET /gradio_api/file=<ruta> sin autenticacion en un Space publico. Si la
    ruta permitida fuese `~/.literalevel` entera, cualquiera se descargaria
    `cuaderno.db`, `voz.db`, `perfil.json` y `sesion.json` de los demas.
    """
    base = Path(os.path.expanduser("~")) / ".literalevel"
    audio = base / "audio"

    def cubierta(ruta):
        return any(os.path.normcase(str(ruta)).startswith(os.path.normcase(p))
                   for p in ui.RUTAS_PERMITIDAS)

    assert cubierta(audio), "el audio de tts-1 no se podra servir"
    for privado in ("cuaderno.db", "voz.db", "perfil.json", "sesion.json",
                    "lexicon.db"):
        assert not cubierta(base / privado), \
            f"{privado} queda expuesto por allowed_paths"
    fuente = Path("main.py").read_text(encoding="utf-8")
    assert "allowed_paths=RUTAS_PERMITIDAS" in fuente, \
        "main.py no pasa allowed_paths a launch()"
    assert "max_file_size=" in fuente, \
        "main.py no limita el tamano de subida: un epub es un zip"
    return "audio servible; bases de datos fuera de alcance"


prueba("allowed_paths: sirve el audio y nada mas", _rutas_permitidas)


# --- Resultado ------------------------------------------------------------

print("\n" + "=" * 70)
if FALLOS:
    print(f"{len(FALLOS)} FALLOS de {HECHAS} pruebas:\n")
    for f in FALLOS:
        print("  -", f)
    sys.exit(1)
print(f"Las {HECHAS} pruebas extremas pasan: ningun manejador lanzo excepcion.")
