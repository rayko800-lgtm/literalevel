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

import inspect
import os
import sys
import time
import pathlib
import tempfile
import traceback
import zipfile
from pathlib import Path

sys.path.insert(0, "app")
# ANTES de importar ui: sus rutas de datos se fijan al importarse. Sin esto,
# las pruebas escriben en los datos reales de quien las ejecuta, y de hecho lo
# hicieron: 24 archivos de prueba acabaron en la biblioteca del usuario.
# Y se borra al salir (`pruebas_tmp`): cada corrida dejaba 100 MB en %TEMP%.
import pruebas_tmp  # noqa: E402
os.environ["LITERALEVEL_DATOS"] = pruebas_tmp.carpeta("literalevel_pruebas_")
# Y ANTES de importar cualquier cosa que use la clave: esta suite NO PUEDE
# llamar a OpenAI, y lo hacia. La prueba "audio inexistente" llegaba a
# `voz.explicar_correccion`, que no tiene cache, y pagaba un `gpt-4o-mini` en
# CADA ejecucion, con la clave real: `config.cargar` la lee de `CLAVES.txt` y
# la mete en el entorno al importarse. Ademas tardaba segundos de red y daba un
# resultado distinto sin conexion, o sea que la suite no era reproducible.
#
# Se corta en el origen y no prueba a prueba. Sin clave, la aplicacion toma su
# camino degradado, que es precisamente el que `AGENTS.md` promete y el que
# interesa ejercitar aqui: "sin OPENAI_API_KEY la app tiene que seguir
# funcionando en todo lo que no usa red".
import config as config_mod  # noqa: E402
config_mod.cargar = lambda *a, **k: None
os.environ.pop("OPENAI_API_KEY", None)
import ficha as ficha_mod  # noqa: E402
import reader  # noqa: E402
import perfil as perfil_mod  # noqa: E402
import ui  # noqa: E402

FALLOS: list[str] = []
HECHAS = 0


def prueba(nombre: str, fn):
    """Ejecuta `fn`. Que lance es fallo, y devolver una lista con algo dentro
    tambien.

    Lo segundo hay que explicarlo. Varias pruebas de este archivo siguen el
    patron `return malas or "todo bien"`: recorren un espacio, van juntando las
    violaciones en una lista y devuelven esa lista si hay alguna. Con la regla
    de antes -"que devuelva algo es exito"- una lista llena de violaciones se
    imprimia como `ok`, seguida de las violaciones. Es decir: **cuatro pruebas
    sustantivas no podian fallar**, que es peor que no tenerlas, porque dan
    confianza sin darla.

    Lo encontro una auditoria externa. El arreglo va en cada una de esas
    cuatro, con un `assert not malas` antes de devolver: probe a ponerlo aqui,
    en el envoltorio, rechazando toda lista no vacia, y NO sirve -muchas
    pruebas legitimas devuelven una lista como resultado, no como queja, y
    saltaron veinte falsos fallos de golpe-.

    Y quedaba el OTRO patron, que lo encontro la auditoria siguiente y era
    peor: **39 pruebas devolvian un booleano que nadie aseveraba**, asi que un
    `False` se imprimia como `ok False` y la suite terminaba en verde. Con eso,
    un banco de mutaciones demostro que la suite pasaba con `_entrar`
    aceptando cualquier contrasena, con los tres topes por hora apagados, con
    la practica de voz sin puerta de pago, con `_salir` que no olvida y con
    `_dir_lector` mezclando las carpetas de dos lectores. Ahora un `False`
    explicito es un fallo: a diferencia de una lista vacia, nunca es un
    resultado legitimo.

    Tambien se itera lo que devuelva una generadora. `_medir`, `_consultar` y
    `_de_que_trata` lo son, y una lambda que las llama sin iterarlas devuelve
    el generador **sin ejecutar una sola linea del cuerpo**: la prueba "medir
    indice imposible" imprimia `ok <generator object>` y pasaba igual con un
    IndexError dentro.
    """
    global HECHAS
    HECHAS += 1
    try:
        r = fn()
        if inspect.isgenerator(r):
            r = list(r)
        assert r is not False, (
            "la prueba devolvio False: eso es un fallo, no un resultado")
        resumen = str(r)
        if len(resumen) > 90:
            resumen = resumen[:87] + "..."
        print(f"  ok    {nombre:<46} {resumen}")
    except Exception as e:
        FALLOS.append(f"{nombre}: {type(e).__name__}: {e}")
        print(f"  FALLA {nombre:<46} {type(e).__name__}: {e}")
        traceback.print_exc(limit=3)


def consulta(*args):
    """`_consultar` es generadora (dos etapas). Aqui interesa la ultima."""
    ultima = ("", "", None)
    for tramo in ui._consultar(*args):
        ultima = tramo
    return ultima


def abrir_catalogo(*args):
    """`_abrir_del_catalogo` tambien es generadora. Interesa el ultimo tramo."""
    ultima = None
    for tramo in ui._abrir_del_catalogo(*args):
        ultima = tramo
    return ultima


def titulo(t: str):
    print(f"\n--- {t} " + "-" * max(0, 60 - len(t)))


TMP = Path(pruebas_tmp.carpeta("literalevel_extremas_"))

# Lo primero de todo, antes de que ninguna prueba toque nada: montar la
# interfaz no puede cargar el modelo, ni el catalogo, ni el diccionario.
titulo("Arranque perezoso (antes de cualquier otra prueba)")
prueba("construir() no carga nada pesado",
       lambda: (len(ui.construir().blocks),
                ui._puntuador, ui._catalogo, ui._consultor))
assert (ui._puntuador, ui._catalogo, ui._consultor) == (None, None, None), \
    "construir() cargo un recurso pesado: la app tardara en abrir"

# Aqui habia un `ui.voz.registrar_fallos = lambda *a, **k: None`, puesto cuando
# la suite escribia en el `~/.literalevel/voz.db` de quien la ejecutara. Ya no
# hace falta -`LITERALEVEL_DATOS` apunta a una carpeta temporal desde la linea
# 29- y hacia daño: apagar el registro deja SIN EFECTO la unica linea que
# decide en que voz.db se apunta el fallo, asi que el mutante que le quitaba la
# `peticion` -una voz.db compartida por todos los visitantes- no lo podia cazar
# ninguna prueba. Un doble puesto por prudencia que anula lo que se quiere
# medir es la tercera forma de que una prueba no pruebe nada.


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

prueba("palabra vacia", lambda: consulta(None, None, None, "", "")[0])
prueba("solo espacios", lambda: consulta(None, None, None, "   ", "")[0])
prueba("None como palabra", lambda: consulta(None, None, None, None, "")[0])
prueba("frase de 10 palabras",
       lambda: consulta(None, None, None, "a b c d e f g h i j", "")[0])
def _sin_encabezado_gigante():
    """Una 'palabra' larguisima no puede convertirse en el encabezado.

    Lo encontro Miguel probandola desde el movil: se validaba que no fueran
    mas de cuatro *palabras*, pero no la longitud, asi que 3000 caracteres
    seguidos salian como titulo H2 y llenaban la pantalla entera.
    """
    ficha = consulta(None, None, None, "X" * 3000, "")[0]
    assert len(ficha) < 300, f"la ficha ocupa {len(ficha)} caracteres"
    assert not ficha.startswith("##"), "sigue siendo un encabezado"
    # Y aunque se llame a _ficha por otro camino, el encabezado va acotado.
    from types import SimpleNamespace as N
    r = N(palabra_superficie="Y" * 9000, lema_buscado="y", categoria=None,
          ipa_uk=None, ipa_us=None, sentido=None, etiquetas_sentido=[],
          n_sentidos_candidatos=0, similitud=None, definicion_contextual=None,
          explicacion_gramatical=None, explicacion_adaptada=None,
          ejemplo_simplificado=None, banda_lector="b", frecuencia_zipf=None,
          desde_cache=False, audio_generado=False, avisos=[],
          audio_uk=None, audio_us=None)
    assert len(ui._ficha(r)) < 300
    return "acotado en el manejador y en el renderizado"


prueba("palabra larguisima no llena la pantalla", _sin_encabezado_gigante)
prueba("una palabra de 40 caracteres sigue valiendo",
       lambda: consulta(None, None, None, "x" * 40, "")[0][:30])
prueba("mensaje de palabra larga en ingles",
       lambda: consulta(None, None, None, "x" * 100, "", "en")[0][:40])

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

prueba("id vacio", lambda: abrir_catalogo("")[-1])
prueba("id None", lambda: abrir_catalogo(None)[-1])
prueba("StoryWeaver no es de Gutenberg",
       lambda: abrir_catalogo("SWgdlgdl42")[-1][:60])
prueba("id sin digitos", lambda: abrir_catalogo("PG")[-1][:60])
prueba("id con inyeccion", lambda: abrir_catalogo("PG1;rm -rf /")[-1][:60])
prueba("opciones vacias", lambda: ui._opciones_libros([]))


class _LibroFalso:
    id, titulo, autor, nivel = "PG42", "Un libro", "Alguien", "B1"
    gancho, descargas, similitud, afinidad = "", 0, 0.0, 0.0
    url_gutenberg = "https://www.gutenberg.org/ebooks/42"


prueba("opciones con un libro de Gutenberg",
       lambda: (ui._opciones_libros([_LibroFalso()])["choices"] or None)
       and "lista una opcion")

titulo("Correccion de pronunciacion palabra a palabra")

_ev = ui.voz.evaluar_pronunciacion(
    "Our prison stood at the edge of the fortress",
    "Our prison stood at the age of the fortes")
# Marcarlo TODO en verde -`fallo = set()`- pasaba esta prueba: devolvia una
# tupla, y una tupla nunca es False. Es el paso cinco del guion del video.
def _marca_bien_y_mal():
    html = ui._palabras_html(_ev, True)
    falladas = list(_ev.palabras_falladas)
    assert falladas, "el caso de prueba no tiene ninguna palabra fallada"
    marcadas = html.count('class="ll-w')
    assert marcadas, "no marco ni una palabra"
    # Las clases son `ll-w mal` y `ll-w ok`, no `ll-w-mal`: la primera version
    # de esta asercion se invento el nombre y fallaba sobre codigo correcto.
    mal = html.count('class="ll-w mal"')
    assert mal == len(falladas), (
        f"{len(falladas)} palabras falladas y {mal} marcadas en rojo: "
        f"si sale 0, la correccion pinta todo en verde")
    assert html.count('class="ll-w ok"') == marcadas - mal
    return f"{mal} en rojo y {marcadas - mal} en verde"


prueba("marca bien y mal", _marca_bien_y_mal)
prueba("sin transcripcion no inventa marcas y dice que no oyo",
       lambda: ("No te oí" in (h := ui._palabras_html(_ev, False)) and 'class="ll-w' not in h
                and "no inventa marcas y dice «No te oí»"))
prueba("frase vacia",
       lambda: repr(ui._palabras_html(ui.voz.evaluar_pronunciacion("", ""), True)))
# Esperaba encontrar "&lt;" y llevaba tiempo devolviendo False, o sea
# informando de un fallo como exito. Y la expectativa era la equivocada:
# `normalizar_palabras` quita la puntuacion ANTES, asi que de
# "<script>alert(1)</script>" solo quedan las palabras y no hay ningun "<"
# que escapar. Lo que hay que aseverar es la propiedad de seguridad de
# verdad: que no salga HTML vivo.
prueba("html incrustado en la frase",
       lambda: "<script" not in ui._palabras_html(
           ui.voz.evaluar_pronunciacion("<script>alert(1)</script> hello",
                                        "hello"), True)
               and "ni una etiqueta viva en la salida")

# Feedback de Laura (12 sep): «don’t» con apostrofo tipografico salia como dos
# palabras falladas, «don» y «t».
prueba("el apostrofo tipografico no parte la contraccion",
       lambda: ui.voz.normalizar_palabras("You don’t warn; I won‘t call") ==
               ["you", "don't", "warn", "i", "won't", "call"]
               and "don’t sigue siendo una palabra")
prueba("contraccion tipografica dicha igual no cuenta como fallo",
       lambda: ui.voz.evaluar_pronunciacion("I don’t know", "I don't know"
                                            ).palabras_falladas == []
               and "cero falladas")

# Feedback de Laura (12 sep): la cabecera del lector decia «Tolstoy, Leo, graf».
prueba("el autor corto quita el titulo nobiliario",
       lambda: (ui._autor_corto("Tolstoy, Leo, graf, 1828-1910") == "Tolstoy, Leo"
                and ui._autor_corto("Doyle, Arthur Conan, Sir, 1859-1930") == "Doyle, Arthur Conan"
                and ui._autor_corto("Dostoyevsky, Fyodor, 1821-1881; "
                                    "Garnett, Constance, 1861-1946 [Translator]")
                    == "Dostoyevsky, Fyodor"
                and ui._autor_corto("Homer") == "Homer")
               and "sin graf ni Sir")
# Codex (auditoria 18): el primer arreglo se quedaba con las dos primeras partes
# y rompia autores reales del catalogo.
prueba("el autor corto conserva Jr., II y las comas de un parentesis",
       lambda: (ui._autor_corto("Alger, Horatio, Jr., 1832-1899") == "Alger, Horatio, Jr."
                and ui._autor_corto("Appleton, Victor, II") == "Appleton, Victor, II"
                and ui._autor_corto("Allen, George (Vicar of St. Thomas's, Islington), 1827-1878")
                    == "Allen, George (Vicar of St. Thomas's, Islington)")
               and "Jr., II y parentesis intactos")

# La prueba de punta a punta: con «fix» por «fox» la explicacion culpaba a la
# /f/. Ahora la evaluacion guarda lo que se entendio y el prompt lo lleva.
def _lo_que_se_entendio_viaja():
    ev = ui.voz.evaluar_pronunciacion("The quick brown fox jumps over the lazy dog",
                                      "The quick brown fix jumps over the lazy")
    assert ("fox", "fix") in ev.entendidas, ev.entendidas
    assert ("dog", "") in ev.entendidas, ev.entendidas
    assert ev.palabras_falladas == ["fox", "dog"], ev.palabras_falladas
    texto = ui.voz._lo_que_se_entendio(ev.entendidas)
    assert "fox → «fix»" in texto and "dog → (no se oyó)" in texto, texto
    assert ui.voz._lo_que_se_entendio([]) == "" and ui.voz._lo_que_se_entendio(None) == ""
    tramo = ui.voz.evaluar_pronunciacion("I am going to go", "I am gonna go")
    assert ("going", "gonna") in tramo.entendidas and ("to", "gonna") in tramo.entendidas, tramo.entendidas
    return "fox → fix y dog sin oir llegan al prompt"


prueba("la explicacion sabe lo que se entendio", _lo_que_se_entendio_viaja)

prueba("el relleno de los markdown no toca el html del lector",
       lambda: (":not(:has(.html-container)):has(.prose *)" in ui._CSS_GLOBAL
                and "hide-container:has(.prose *)" not in ui._CSS_GLOBAL)
               and "la regla excluye los gr.HTML")

# Codex: al vencer el plazo sin que cambiase el texto, desplazaba igual 6 s
# despues. La rama del plazo solo para; la del texto nuevo es la unica que sube.
prueba("el salto al texto no se dispara al vencer el plazo",
       lambda: (ui.re.search(r"else if \(\+\+vueltas > 40\) \{\s*parar\(\);\s*\}", ui.JS_AL_TEXTO)
                and "window.__llAlTexto()" in ui.JS_AL_TEXTO
                and "'touchstart'" in ui.JS_AL_TEXTO)
               and "plazo sin salto, cancela la anterior y cede al gesto")

titulo("Avisos legibles cuando algo falla")

prueba("el 429 de OpenAI se cuenta en cristiano",
       lambda: ui._humanizar(
           "OpenAI no disponible: RuntimeError: Error code: 429 - You "
           "exceeded your current quota", "es")[:52])
prueba("y en ingles",
       lambda: ui._humanizar("Error code: 429 exceeded your current quota", "en")[:44])
prueba("la falta de clave tambien",
       lambda: ui._humanizar("sin OPENAI_API_KEY: no hay explicacion", "es")[:40])
prueba("un corte de red tambien",
       lambda: ui._humanizar("Connection timed out", "es")[:40])
prueba("un aviso desconocido se deja tal cual",
       lambda: ui._humanizar("algo rarisimo que nadie previo", "es"))
prueba("ningun aviso conocido llega en crudo a la ficha",
       lambda: all("RuntimeError" not in ui._humanizar(a, i) and "429" not in ui._humanizar(a, i)
                   for a in ("OpenAI no disponible: RuntimeError: Error code: 429 - quota",)
                   for i in ("es", "en")))


def _sin_seccion_inexistente():
    """El aviso de baja afinidad no puede remitir a una seccion que falta."""
    from types import SimpleNamespace as N
    base = dict(palabra_superficie="x", lema_buscado="x", categoria="noun",
                ipa_uk=None, ipa_us=None, sentido="algo", etiquetas_sentido=[],
                n_sentidos_candidatos=3, similitud=0.10,
                explicacion_gramatical=None, explicacion_adaptada=None,
                ejemplo_simplificado=None, banda_lector="básico",
                frecuencia_zipf=None, desde_cache=False, audio_generado=False,
                audio_uk=None, audio_us=None, avisos=[])
    sin = ui._ficha(N(**base, definicion_contextual=None), "es")
    con = ui._ficha(N(**base, definicion_contextual="Aquí significa algo."), "es")
    assert "Aquí significa" not in sin.split("**Diccionario")[0] + \
        "".join(l for l in sin.split("\n\n") if l.startswith("[!]")), \
        "manda al lector a una seccion que no existe"
    assert any("Aquí significa" in l for l in con.split("\n\n") if l.startswith("[!]"))
    return "remite a «Aquí significa» solo cuando existe"


prueba("aviso de afinidad baja coherente", _sin_seccion_inexistente)

titulo("Freno de gasto por IP")


class _Pet:
    def __init__(self, ip=None, host=None):
        self.headers = {"x-forwarded-for": ip} if ip else {}
        self.client = type("c", (), {"host": host})() if host else None


prueba("saca la IP de x-forwarded-for",
       lambda: ui._ip(_Pet(ip="203.0.113.7, 10.0.0.1")) == "203.0.113.7"
       and "203.0.113.7")
prueba("cae al host del cliente si no hay cabecera",
       lambda: ui._ip(_Pet(host="198.51.100.9")) == "198.51.100.9"
       and "198.51.100.9")
prueba("sin peticion no revienta", lambda: ui._ip(None))
prueba("cabeceras raras no rompen", lambda: ui._ip(_Pet(ip=None, host=None)))
# Las dos que siguen devolvian un numero y una tupla, que NUNCA son False:
# imprimian `ok 4` y `ok (True, True)` y con el tope roto habrian impreso
# `ok 9` en verde. Se asevera lo que se espera.
prueba("el tope se respeta",
       lambda: (lambda n: n == 4 and f"pasan {n} de 9")(
           sum(ui._dentro_del_limite(_Pet(ip="10.1.1.1"), "p1", 4)
               for _ in range(9))))
prueba("una IP no consume la cuota de otra",
       lambda: (all(ui._dentro_del_limite(_Pet(ip="10.2.2.2"), "p2", 2)
                    for _ in range(2))
                and ui._dentro_del_limite(_Pet(ip="10.3.3.3"), "p2", 2)
                and "la segunda IP conserva su cuota"))
prueba("tope 0 significa sin limite",
       lambda: all(ui._dentro_del_limite(_Pet(ip="10.4.4.4"), "p3", 0)
                   for _ in range(200)))
# Devolvia una TUPLA `(True, False)`, que nunca es False: con los tres cubos
# contados en el mismo, una hora de consultas te dejaba sin practica de voz.
prueba("cubos distintos no se mezclan",
       lambda: (ui._dentro_del_limite(_Pet(ip="10.5.5.5"), "lexico", 1)
                and ui._dentro_del_limite(_Pet(ip="10.5.5.5"), "voz", 1)
                and not ui._dentro_del_limite(_Pet(ip="10.5.5.5"), "lexico", 1))
       and "el lexico se agota y la voz sigue")
prueba("el mensaje de limite existe en los dos idiomas",
       lambda: (len(ui._mensaje_limite("es", 60)) > 40,
                len(ui._mensaje_limite("en", 60)) > 40))
def _por_encima_del_tope_no_llega_al_consultor():
    """Agotado el tope por hora, `_consultar` devuelve el aviso y no consulta.

    La version anterior de esta prueba no probaba NADA: preguntaba por el cupo
    con `tope=0`, que significa justamente SIN LIMITE, asi que la condicion
    nunca se cumplia, la rama que hacia la consulta no se ejecutaba jamas y la
    prueba imprimia "tope generoso, no aplica" en verde. Lo encontro una
    auditoria externa leyendo la expresion condicional.

    Ahora se agota un tope de verdad -bajando la constante del modulo- y se
    comprueba lo que de verdad importa: que la segunda consulta trae el aviso
    de limite y que NO llega a construir el consultor, que es lo que costaria
    dinero. Si llegara, el doble revienta y la prueba falla.
    """
    pet = _Pet(ip="10.6.6.7")

    def no_deberia_llamarse():
        raise AssertionError("llego al consultor con el tope agotado")

    tope_antes, consultor_antes = ui.LIMITE_CONSULTAS_HORA, ui.consultor
    ui.LIMITE_CONSULTAS_HORA = 1
    ui.consultor = no_deberia_llamarse
    # El tope solo frena lo que VA A COSTAR dinero: una consulta sin clave es
    # diccionario local y no se limita. Aqui se finge que hay clave, porque lo
    # que se prueba es el freno de gasto, no el camino gratuito.
    falta_antes = config_mod.falta
    config_mod.falta = lambda: []
    try:
        # El primer uso gasta el unico permitido. Puede fallar por otras
        # razones -no hay diccionario en las pruebas- y da igual: lo que
        # interesa es que consuma el cupo.
        try:
            consulta(None, None, None, "word", "A sentence with the word.",
                     "es", pet)
        except AssertionError:
            pass          # llego al consultor, que en el primer uso es normal
        segunda = consulta(None, None, None, "word",
                           "A sentence with the word.", "es", pet)[0]
        aviso = ui._mensaje_limite("es", 60)[:30]
        assert aviso in segunda, f"esperaba el aviso de limite, dio: {segunda[:90]}"
    finally:
        ui.LIMITE_CONSULTAS_HORA, ui.consultor = tope_antes, consultor_antes
        config_mod.falta = falta_antes
    return "con el tope agotado devuelve el aviso y no consulta"


prueba("consultar por encima del tope no llama a OpenAI",
       _por_encima_del_tope_no_llega_al_consultor)

titulo("Datos de cada lector, no de todos")


class _Peticion:
    def __init__(self, h): self.session_hash = h


def _con_nube(fn):
    """Ejecuta algo como si la app estuviera desplegada."""
    antes = ui.EN_LA_NUBE
    ui.EN_LA_NUBE = True
    try:
        return fn()
    finally:
        ui.EN_LA_NUBE = antes


prueba("en local no se parte lo ya guardado",
       lambda: ui._dir_lector(_Peticion("x")) == ui.BASE_DATOS_LECTOR)
prueba("desplegada, una carpeta por sesion",
       lambda: _con_nube(lambda: ui._dir_lector(_Peticion("abc123")).name))
prueba("dos sesiones no comparten carpeta",
       lambda: _con_nube(lambda: ui._dir_lector(_Peticion("aaa"))
                         != ui._dir_lector(_Peticion("bbb"))))
def _el_session_hash_no_escapa():
    """Un `session_hash` con `../` no puede salirse de la carpeta de lectores.

    La version anterior de esta prueba NO PODIA FALLAR: comprobaba
    `base/lectores in ruta.parents`, y `Path.parents` es LEXICO, asi que
    `base/lectores/../../etc/passwd` tiene a `base/lectores` entre sus padres
    aunque resuelva fuera del disco. Quitando la sanitizacion entera la prueba
    seguia en verde. La sanitizacion real esta bien; era la prueba la que no
    valia.

    Ahora se comprueba lo que importa de las dos formas: que el nombre no
    contenga separadores ni puntos, y que la ruta RESUELTA siga dentro.
    """
    def dentro():
        base = (ui.BASE_DATOS_LECTOR / "lectores").resolve()
        malos = []
        for h in ("../../etc/passwd", "..\\..\\Windows\\System32", "a/../..",
                  "....//....//x", "/etc/passwd"):
            d = ui._dir_lector(_Peticion(h))
            if any(c in d.name for c in "/\\") or ".." in d.name:
                malos.append(f"{h!r} deja el nombre {d.name!r}")
            if base not in d.resolve().parents:
                malos.append(f"{h!r} resuelve FUERA: {d.resolve()}")
        assert not malos, malos
        return "cinco intentos de escape, ninguno sale de lectores/"
    return _con_nube(dentro)


prueba("session_hash con ../ no escapa", _el_session_hash_no_escapa)


def _dos_lectores_no_se_ven_los_datos():
    """Que `_dir_lector` separe carpetas no basta: hay que ejercitar el camino.

    Todas las pruebas de aqui arriba comprueban la FUNCION que reparte, y
    ninguna llamaba a un manejador con dos sesiones distintas para ver que lo
    guardado por uno no lo ve el otro. Por eso sobrevivian cinco mutantes que
    devolvian el Space a "una carpeta para todos": bastaba con que un manejador
    dejara de pasar la peticion -que es justamente el fallo que tuvo el
    cuestionario- y ninguna prueba se enteraba.

    Aqui se hace el recorrido de verdad: A fija su nivel, B fija otro, y cada
    uno tiene que recuperar el suyo.
    """
    def dentro():
        a, b = _Peticion("lector-aaa"), _Peticion("lector-bbb")
        # Cada uno responde el cuestionario con respuestas distintas.
        claves = ui._claves_cuestionario()
        pa = ui._desde_cuestionario(None, "Ana", a, *([0] * len(claves)))[0]
        pb = ui._desde_cuestionario(None, "Bruno", b,
                                    *([3] * len(claves)))[0]
        assert pa is not None and pb is not None, "no se creo algun perfil"
        # Y cada uno recupera el SUYO al recargar la pagina.
        va = ui._perfil_inicial(a)[0]
        vb = ui._perfil_inicial(b)[0]
        assert va is not None and vb is not None, "algun perfil no se recupero"
        assert va.nombre == "Ana", f"A recupero {va.nombre!r}"
        assert vb.nombre == "Bruno", f"B recupero {vb.nombre!r}"
        assert ui._archivo_lector("perfil.json", a) != \
            ui._archivo_lector("perfil.json", b), "misma ruta para los dos"
        return f"A={va.nombre} ({va.nivel}), B={vb.nombre} ({vb.nivel})"
    return _con_nube(dentro)


prueba("dos lectores no se ven los datos", _dos_lectores_no_se_ven_los_datos)


def _los_datos_sobreviven_a_recargar():
    """Recargar la pagina NO puede estrenar carpeta.

    Es lo que fallaba y ninguna prueba veia: Gradio estrena `session_hash` en
    cada carga, asi que el lector fijaba su nivel, leia "Guardado", pulsaba F5
    y volvia a "Todavia no has fijado tu nivel". La prueba de aislamiento
    pasaba porque usa dos hashes FIJOS: no probaba lo que hace una persona.

    Ahora la identidad la pone el navegador y vive en `localStorage`. Aqui se
    simula una recarga: misma identidad, `session_hash` distinto.
    """
    def dentro():
        ui._LECTOR_POR_SESION.clear()
        claves = ui._claves_cuestionario()

        antes = _Peticion("sesion-antes-de-F5")
        ui._registrar_lector("lector-que-recarga", antes)
        ui._desde_cuestionario(None, "Nadia", antes, *([1] * len(claves)))
        p1 = ui._perfil_inicial(antes)[0]
        assert p1 is not None and p1.nombre == "Nadia", "no guardo"

        # F5: Gradio da un session_hash NUEVO, el navegador la misma identidad.
        despues = _Peticion("sesion-despues-de-F5")
        assert despues.session_hash != antes.session_hash
        ui._registrar_lector("lector-que-recarga", despues)
        p2 = ui._perfil_inicial(despues)[0]
        assert p2 is not None, "tras recargar, el perfil se perdio"
        assert p2.nombre == "Nadia", f"recupero otro perfil: {p2.nombre}"
        assert ui._dir_lector(antes) == ui._dir_lector(despues),             "misma identidad y carpetas distintas"

        # Y otro navegador sigue sin ver nada de este.
        otro = _Peticion("sesion-de-otro")
        ui._registrar_lector("otro-lector-distinto", otro)
        assert ui._dir_lector(otro) != ui._dir_lector(antes), "se mezclan"
        return "sobrevive a recargar y sigue separado de otro navegador"
    return _con_nube(dentro)


prueba("los datos sobreviven a recargar", _los_datos_sobreviven_a_recargar)


def _sin_localStorage_no_revienta():
    """En una ventana privada `localStorage` LANZA, y el JS devuelve "".

    Si eso rompiera el registro, la pagina entera arrancaria en error. Tiene
    que caer al `session_hash` de siempre, que es lo que habia antes.
    """
    def dentro():
        ui._LECTOR_POR_SESION.clear()
        pet = _Peticion("sesion-sin-almacen")
        for vacio in ("", None):
            ui._registrar_lector(vacio, pet)
        d = ui._dir_lector(pet)
        assert d.name == "sesion-sin-almacen", d.name
        # Y una identidad con `../` no puede sacar la carpeta de su sitio.
        ui._registrar_lector("../../etc/passwd", pet)
        d = ui._dir_lector(pet)
        base = (ui.BASE_DATOS_LECTOR / "lectores").resolve()
        assert base in d.resolve().parents, f"escapo: {d.resolve()}"
        assert ".." not in d.name and "/" not in d.name, d.name
        return "sin almacen cae en la sesion, y un ../ no escapa"
    return _con_nube(dentro)


prueba("sin localStorage no revienta", _sin_localStorage_no_revienta)


def _el_arranque_averigua_quien_es_antes_de_leer():
    """`_perfil_inicial` y `_reanudar` NO pueden ir sueltos en `demo.load`.

    Varios `demo.load` corren a la vez. Si leen los datos antes de que el
    registro de identidad haya llegado, leen la carpeta equivocada -o la de
    "anonimo"- y el lector ve su estanteria vacia justo despues de guardar. El
    orden se garantiza encadenando con `.then()`, y eso es lo que se comprueba
    aqui: en el codigo, porque para verlo correr haria falta el bucle de
    eventos de Gradio.
    """
    import re
    fuente = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(
        encoding="utf-8")
    malos = []
    for quien in ("_perfil_inicial", "_reanudar"):
        if re.search(rf"demo\.load\(\s*{quien}\b", fuente):
            malos.append(f"{quien} va suelto en demo.load, sin encadenar")
        if not re.search(rf"\.then\(\s*{quien}\b", fuente):
            malos.append(f"{quien} no esta encadenado con .then()")
    i_reg = fuente.find("demo.load(_registrar_lector")
    i_perfil = fuente.find(".then(_perfil_inicial")
    if i_reg < 0:
        malos.append("el registro de identidad no se cablea en demo.load")
    elif not (0 < i_reg < i_perfil):
        malos.append("el registro no va ANTES de leer el perfil")
    assert not malos, malos
    return "el arranque registra la identidad y despues lee los datos"


prueba("el arranque averigua quien es antes de leer",
       _el_arranque_averigua_quien_es_antes_de_leer)


def _los_manejadores_que_guardan_pasan_la_peticion():
    """Un manejador cableado que toque datos del lector TIENE que anotar
    `gr.Request`; si no, Gradio no se la inyecta y escribe en `anonimo/`.

    La otra prueba de inyeccion solo mira los que YA anotan `Request`, asi que
    un mutante que le quite la anotacion al cuestionario se le escapa: deja de
    anotar, deja de recibir, y la prueba lo salta por no anotar. Aqui se mira
    al reves: se sacan los manejadores CABLEADOS a la interfaz, y si alguno usa
    datos del lector sin anotar, es un fallo.
    """
    import re
    fuente = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(
        encoding="utf-8")
    # Los nombres que se cablean a un evento de Gradio.
    # `then` incluido: al encadenar el arranque con `.then()` para que la
    # identidad del lector se registre ANTES de leer sus datos, dos manejadores
    # dejaron de contarse aqui y esta prueba paso de 29 a 28 sin que fallara
    # nada. Una prueba que vigila una lista puede perder cobertura en silencio
    # solo con que el codigo cambie de forma.
    cableados = set(re.findall(
        r"\.(?:click|change|submit|load|select|upload|stop|input|then)\(\s*"
        r"(_[a-z_]+)", fuente))
    assert cableados, "no encuentro ningun manejador cableado"
    malos = []
    for nombre in sorted(cableados):
        f = getattr(ui, nombre, None)
        if f is None or not callable(f):
            continue
        try:
            cuerpo = inspect.getsource(f)
            sig = inspect.signature(f)
        except (TypeError, OSError, ValueError):
            continue
        toca_datos = re.search(
            r"_archivo_lector\([^)]*peticion|_dir_lector\(peticion|"
            r"_ruta_sesion\(peticion|_codigo_de\(peticion", cuerpo)
        if not toca_datos:
            continue
        p = sig.parameters.get("peticion")
        if p is None or "Request" not in str(p.annotation):
            malos.append(f"{nombre}{sig}")
    assert not malos, malos
    return f"{len(cableados)} manejadores cableados; los que guardan, anotados"


prueba("los manejadores que guardan pasan la peticion",
       _los_manejadores_que_guardan_pasan_la_peticion)
prueba("session_hash vacio cae en 'anonimo'",
       lambda: _con_nube(lambda: ui._dir_lector(_Peticion("")).name))
prueba("sin peticion tampoco revienta",
       lambda: _con_nube(lambda: ui._dir_lector(None).name))
prueba("session_hash larguisimo se recorta",
       lambda: _con_nube(
           lambda: len(ui._dir_lector(_Peticion("z" * 500)).name) <= 64)
       and "recortado a 64 o menos")
prueba("session_hash raro no deja el nombre vacio",
       lambda: _con_nube(lambda: ui._dir_lector(_Peticion("///")).name))

titulo("Cuaderno de palabras")

import cuaderno  # noqa: E402

_CDB = str(TMP / "cuaderno.db")

prueba("base vacia", lambda: (cuaderno.contar(_CDB), cuaderno.ultimas(5, _CDB)))
prueba("registrar una consulta",
       lambda: cuaderno.registrar(palabra="fetters", lema="fetter",
                                  oracion="the convicts were in fetters",
                                  zipf=2.3, libro="Dead House", capitulo=5,
                                  ruta=_CDB))
# Estas dos devuelven False cuando la palabra SE RECHAZA, que es lo que se
# quiere. Devolver el booleano pelado las dejaba a merced del envoltorio: se
# imprimian como `ok False` y habrian pasado igual si el rechazo dejara de
# funcionar. Se asevera la expectativa y se devuelve algo legible.
prueba("palabra vacia se rechaza",
       lambda: not cuaderno.registrar(palabra="", lema="x", oracion="y",
                                      ruta=_CDB) and "rechazada")
prueba("oracion en blanco se rechaza",
       lambda: not cuaderno.registrar(palabra="x", lema="x", oracion="   ",
                                      ruta=_CDB) and "rechazada")
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
                                   oracion="in fetters again", zipf=2.3, ruta=_CDB)
                or len([a for a in cuaderno.para_repasar(9, _CDB)
                        if a.lema == "fetter"]) == 1)
       and "una sola entrada para fetter y fetters")
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
       lambda: consulta(None, None, None, "", "", "klingon")[0])
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
       # El tercer None es `peticion`, que en este manejador va ANTES de
       # `*valores`: ver su docstring. Los dos ultimos son respuestas vacias.
       lambda: ui._desde_cuestionario(None, "", None, None, None)[1][:70])
prueba("muestra vacia", lambda: ui._desde_muestra(None, "", "")[1][:70])
prueba("muestra que no es prosa",
       lambda: ui._desde_muestra(None, "", "- uno\n- dos\n- tres")[1][:70])
prueba("describir perfil None", lambda: ui._describir(None)[:60])

# Medir el nivel subiendo un libro entero, en vez de copiar y pegar.
prueba("nivel desde libro: sin archivo",
       lambda: ui._nivel_desde_libro(None, "", None)[1][:50])
prueba("nivel desde libro: archivo inexistente",
       lambda: ui._nivel_desde_libro(None, "", str(TMP / "nada.epub"))[1][:50])
prueba("nivel desde libro: epub corrupto",
       lambda: ui._nivel_desde_libro(None, "", escribir("x.epub", b"no soy zip"))[1][:50])
prueba("nivel desde libro: texto insuficiente",
       lambda: ui._nivel_desde_libro(None, "", escribir("mini.txt", "hola"))[1][:50])


def _muestreo_reparte():
    """La muestra no puede salir toda del principio del libro."""
    class C:
        def __init__(s, t, n): s.titulo, s.texto = t, " ".join(f"w{i}" for i in range(n))
        @property
        def palabras(s): return len(s.texto.split())

    class L:
        titulo, autor = "L", "A"
        capitulos = ([C("Foreword", 900)]
                     + [C(f"CHAPTER {i}", 900) for i in range(1, 13)])
    m = ui._muestra_de_libro(L())
    assert "Foreword" not in m
    trozos = m.split("\n\n")
    assert len(trozos) >= 4, f"solo {len(trozos)} trozos"
    return f"{len(trozos)} trozos de {len(L.capitulos) - 1} capítulos de cuerpo"


prueba("la muestra se reparte por el libro", _muestreo_reparte)
prueba("muestra de un libro sin capítulos útiles",
       lambda: repr(ui._muestra_de_libro(type("L", (), {"capitulos": []})())))


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
    # La raiz CONFIGURADA, no `~/.literalevel` a pelo: desde que la app puede
    # apuntar sus datos a un disco persistente, `RUTAS_PERMITIDAS` cuelga de
    # `LITERALEVEL_DATOS`, y esta prueba media contra otra carpeta -pasaba por
    # casualidad, porque en local las dos coinciden-.
    base = ui.BASE_DATOS_LECTOR
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



titulo("Mis libros")

import biblioteca  # noqa: E402

_BIB = str(TMP / "biblioteca.json")

prueba("estanteria vacia", lambda: biblioteca.listar(_BIB))
prueba("anotar un libro",
       lambda: biblioteca.anotar(ruta_libro=str(TMP / "l.epub"), titulo="T",
                                 autor="A", capitulos=10, capitulo=3,
                                 palabras=5000, ruta=_BIB))
# Mismo caso que las del cuaderno: False significa "rechazado", que es el
# exito. Se asevera, para que aceptar un libro sin ruta o sin titulo pase a
# ser un fallo de verdad y no un `ok False`.
prueba("sin ruta se rechaza",
       lambda: not biblioteca.anotar(ruta_libro="", titulo="T", autor="",
                                     capitulos=1, capitulo=0, palabras=1,
                                     ruta=_BIB) and "rechazado")
prueba("sin titulo se rechaza",
       lambda: not biblioteca.anotar(ruta_libro="x", titulo="", autor="",
                                     capitulos=1, capitulo=0, palabras=1,
                                     ruta=_BIB) and "rechazado")
prueba("ruta imposible no lanza",
       lambda: (biblioteca.anotar(ruta_libro="x", titulo="t", autor="", capitulos=1,
                                  capitulo=0, palabras=1, ruta="Z:/no/b.json"),
                biblioteca.listar("Z:/no/b.json")))
prueba("json corrupto no lanza",
       lambda: (pathlib.Path(_BIB).write_text("{roto", encoding="utf-8"),
                biblioteca.listar(_BIB))[1])
prueba("re-anotar no duplica",
       lambda: (biblioteca.anotar(ruta_libro="a", titulo="T", autor="", capitulos=9,
                                  capitulo=1, palabras=9, ruta=_BIB),
                biblioteca.anotar(ruta_libro="a", titulo="T", autor="", capitulos=9,
                                  capitulo=5, palabras=9, ruta=_BIB),
                [(e.ruta, e.capitulo) for e in biblioteca.listar(_BIB)])[2])
prueba("avance con un solo capitulo",
       lambda: biblioteca.Entrada("r", "t", "a", 1, 0, 10, "").avance)
prueba("avance con capitulo fuera de rango",
       lambda: biblioteca.Entrada("r", "t", "a", 5, 99, 10, "").avance)
prueba("libro que ya no existe se marca",
       # `.existe` es False, que es el acierto: el libro no esta.
       lambda: not biblioteca.Entrada("Z:/no.epub", "t", "a", 5, 1, 10,
                                      "").existe and "marcado como ausente")
prueba("seguir sin elegir",
       lambda: list(ui._seguir_leyendo(""))[-1][-1])
prueba("seguir con ruta muerta",
       lambda: list(ui._seguir_leyendo(str(TMP / "fantasma.epub")))[-1][-1][:40])
prueba("olvidar un libro",
       lambda: (biblioteca.olvidar("a", _BIB),
                [e.ruta for e in biblioteca.listar(_BIB)])[1])


titulo("Ficha del libro")

prueba("ficha de None", lambda: ui._ficha_libro(None))
prueba("ficha sin capitulos",
       lambda: ui._ficha_libro(reader.Libro("t", "a", [])))
prueba("ficha de un capitulo vacio",
       lambda: ui._ficha_libro(reader.Libro("t", "a", [reader.Capitulo("I", "")])))
prueba("ficha de texto basura",
       lambda: ui._ficha_libro(reader.Libro("t", "a",
                                            [reader.Capitulo("I", chr(0) * 500)])))
prueba("de que trata sin libro", lambda: list(ui._de_que_trata(None))[-1][:40])
prueba("de que trata con libro vacio",
       lambda: list(ui._de_que_trata(reader.Libro("t", "a", [])))[-1][:40])
prueba("sinopsis guardada de un libro inexistente",
       lambda: ui._sinopsis_guardada(reader.Libro("t", "a",
                                                  [reader.Capitulo("I", "x")])))
prueba("sin_licencia con None dentro", lambda: ficha_mod.sin_licencia(""))
prueba("reloj con cero", lambda: ficha_mod.reloj(0))
prueba("reloj con un numero enorme", lambda: ficha_mod.reloj(10 ** 7))


titulo("Indice y aislamiento de datos")

prueba("indice sin libro", lambda: ui._indice_de(None))
prueba("indice de un libro sin capitulos",
       lambda: ui._indice_de(reader.Libro("t", "a", [])))
prueba("indice con capitulo actual fuera de rango",
       lambda: ui._indice_de(reader.Libro("t", "a",
                                          [reader.Capitulo("I", "x " * 200)]), 99))
prueba("indice de un libro largo",
       lambda: len(ui._indice_de(reader.Libro("t", "a", [
           reader.Capitulo(f"C{i}", "x " * 200) for i in range(400)]))["choices"]))
prueba("grafica con un solo capitulo",
       lambda: type(ui._grafica_analisis(
           {"titulo": "t", "filas": [{"capitulo": 1, "dificultad": 1.0,
                                      "titulo": "I"}]})).__name__)
prueba("grafica con muchos capitulos",
       lambda: type(ui._grafica_analisis(
           {"titulo": "t", "filas": [{"capitulo": i, "dificultad": 1.0 + (i % 7) / 10,
                                      "titulo": f"C{i}"} for i in range(400)]})).__name__)
prueba("suavizar con lista vacia", lambda: ui._suavizar([], 5))
prueba("suavizar con ventana mayor que los datos", lambda: ui._suavizar([1.0, 2.0], 9))

# Esta es la que importa: las pruebas NO pueden escribir en los datos reales.
# Paso porque paso: la bateria abria libro.txt, vacio.txt y falso.txt y los
# anotaba en la biblioteca del usuario, que se encontro 24 archivos de prueba
# entre sus cuatro libros al abrir "Mis libros" en el movil.
prueba("los datos de las pruebas no son los del usuario",
       lambda: (str(ui.BASE_DATOS_LECTOR) != str(pathlib.Path(
           os.path.expanduser("~")) / ".literalevel")
                and "literalevel_pruebas" in str(ui.BASE_DATOS_LECTOR)))
prueba("la biblioteca real no se toca",
       lambda: not any("literalevel_pruebas" in e.ruta
                       for e in __import__("biblioteca").listar(
                           str(pathlib.Path(os.path.expanduser("~"))
                               / ".literalevel" / "biblioteca.json"))))


titulo("Escala MCER y modos de analisis")

prueba("cefr en el extremo bajo", lambda: ui._cefr(0.0))
prueba("cefr en el extremo alto", lambda: ui._cefr(2.0))
prueba("cefr por encima del maximo", lambda: ui._cefr(99.0))
prueba("cefr negativo", lambda: ui._cefr(-3.0))
prueba("cefr con texto", lambda: ui._cefr("1.2"))
prueba("nivel dicho como cifra", lambda: ui._nivel_dicho(1.2, "intermedio", "cifra"))
prueba("nivel dicho como cefr", lambda: ui._nivel_dicho(1.2, "intermedio", "cefr"))
prueba("nivel dicho con modo desconocido",
       lambda: ui._nivel_dicho(1.2, "", "loquesea"))
prueba("los seis anclajes salen de la escala 0-2",
       lambda: sorted({ui._cefr(v / 20) for v in range(41)})
       == ["A1", "A2", "B1", "B2", "C1", "C2"] and "los seis, y solo los seis")
# Los limites de la tabla que ve el usuario TIENEN que ser los del codigo. Con
# round() de Python no lo eran: redondea los empates al par, asi que 1.00 daba
# B1 y 1.80 daba C1, y la tabla decia B2 y C2.
prueba("los limites de la tabla son los del codigo",
       lambda: [(lim, ui._cefr(lim - 0.001), ui._cefr(lim)) for lim, esperado
                in ((0.20, "A2"), (0.60, "B1"), (1.00, "B2"), (1.40, "C1"),
                    (1.80, "C2"))
                if ui._cefr(lim) != esperado] or "los cinco limites cuadran")
prueba("analizar sin libro", lambda: list(ui._analizar_libro(None))[-1][0][:40])
prueba("analizar modo desconocido",
       lambda: list(ui._analizar_libro(None, "inventado"))[-1][0][:40])
prueba("analizar libro sin capitulos",
       lambda: list(ui._analizar_libro(reader.Libro("t", "a", [])))[-1][0][:40])
prueba("analizar libro sin prosa suficiente",
       lambda: list(ui._analizar_libro(
           reader.Libro("t", "a", [reader.Capitulo("I", "corto")])))[-1][0][:40])
prueba("resumen de un solo capitulo",
       lambda: ui._resumen_analisis(
           {"titulo": "t", "autor": "", "palabras": 100, "ventanas": 1,
            "filas": [{"capitulo": 1, "dificultad": 1.0, "titulo": "I",
                       "ventanas": 1}]})[:40])
prueba("resumen en modo rapido lo dice",
       lambda: "vistazo rápido" in ui._resumen_analisis(
           {"titulo": "t", "autor": "", "palabras": 100, "ventanas": 60,
            "modo": "rapido", "capitulos_medidos": 30, "capitulos_totales": 42,
            "filas": [{"capitulo": i, "dificultad": 1.0, "titulo": "I",
                       "ventanas": 2}
                      for i in range(30)]}))
prueba("resumen completo no se llama vistazo",
       lambda: "vistazo" not in ui._resumen_analisis(
           {"titulo": "t", "autor": "", "palabras": 100, "ventanas": 60,
            "modo": "completo",
            "filas": [{"capitulo": i, "dificultad": 1.0, "titulo": "I",
                       "ventanas": 2}
                      for i in range(30)]}))
prueba("rapido y completo se guardan aparte",
       lambda: ui._ruta_analisis(reader.Libro("t", "a", []), "rapido")
       != ui._ruta_analisis(reader.Libro("t", "a", []), "completo"))


titulo("Paletas de color")

import paletas as paletas_mod  # noqa: E402

# `or "las cinco"` hacia que devolver la LISTA DE LAS QUE FALLAN contara como
# exito: con `_css_paleta` devolviendo "", la pagina se queda sin paleta y
# esta prueba imprimia ok.
prueba("todas las paletas dan css",
       lambda: not [k for k in paletas_mod.PALETAS
                    if not ui._css_paleta(k).startswith("<style>")]
       and f"las {len(paletas_mod.PALETAS)}")
prueba("clave inventada vuelve a la de siempre",
       lambda: ui._css_paleta("noexiste") == ui._css_paleta(paletas_mod.POR_DEFECTO))
prueba("clave None", lambda: ui._css_paleta(None)[:7])
prueba("clave vacia", lambda: ui._css_paleta("")[:7])
prueba("clave con html dentro",
       lambda: "<script" not in ui._css_paleta("<script>alert(1)</script>"))
prueba("opciones del selector",
       lambda: len(paletas_mod.opciones()) == len(paletas_mod.PALETAS))
prueba("todas definen las mismas variables",
       lambda: len({tuple(sorted(d["vars"])) for d in paletas_mod.PALETAS.values()}) == 1)


def _contraste_suficiente():
    """WCAG AA pide 4.5:1 para texto normal. Una paleta bonita e ilegible no
    sirve: esto se anadio porque la app la va a usar gente de quince anos en
    un movil, no un disenador en un monitor calibrado."""
    def rgba(c):
        """(r, g, b, alfa). El alfa IMPORTA: los paneles son
        semitransparentes y antes se tiraba, o sea que se median
        colores que el navegador nunca pinta."""
        c = c.strip()
        if c.startswith("#"):
            c = c[1:]
            if len(c) == 3:
                c = "".join(x * 2 for x in c)
            return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (1.0,)
        n = c[c.find("(") + 1:c.find(")")].split(",")
        v = tuple(int(float(x)) for x in n[:3])
        return v + (float(n[3]) if len(n) > 3 else 1.0,)

    def sobre(color, fondo):
        """Compone `color` sobre `fondo`. Un panel rgba(255,255,255,.86)
        sobre un fondo oscuro NO es blanco, y es lo que se ve."""
        r, g, b, a = rgba(color)
        fr, fg, fb, _ = rgba(fondo)
        return (r * a + fr * (1 - a), g * a + fg * (1 - a),
                b * a + fb * (1 - a), 1.0)

    def rgb(c):
        return rgba(c)[:3]

    def lum(c):
        def f(v):
            v /= 255
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        r, g, b = rgb(c)
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    # Estos son los pares que de verdad ve el usuario. Antes solo se median los
    # dos primeros, y por eso paso desapercibido que el BOTON PRINCIPAL fallaba
    # AA en las cinco paletas: el texto del boton sobre la parte alta de su
    # degradado daba entre 2,50 y 3,91. Es el boton que dice "Estimar mi nivel"
    # o "Leer el libro entero", o sea el que mas se pulsa de la aplicacion.
    # Cada pareja lleva su umbral, porque WCAG no pide lo mismo a todo:
    # 4,5:1 al texto normal y 3:1 al texto grande (>=24 px, o >=18,7 px en
    # negrita), que es el caso del h1.
    #
    # La lista crecio dos veces, y las dos por lo mismo: se median pocas
    # parejas. Primero se descubrio que el BOTON PRINCIPAL fallaba AA en las
    # cinco paletas -entre 2,50 y 3,91-, que es el boton que dice "Estimar mi
    # nivel". Despues, que el rotulo de la pestana seleccionada usa
    # --ll-acento y daba 3,04 en menta, y que las paradas del degradado del
    # h1 bajaban hasta 1,87. Una prueba que solo mira donde ya sabes que esta
    # bien no es una prueba.
    PARES = {
        "interfaz": ("--ll-texto", "--ll-fondo", 4.5),
        "lector": ("--ll-lector-texto", "--ll-lector-fondo", 4.5),
        "boton-alto": ("--ll-boton-texto", "--ll-boton-alto", 4.5),
        "boton-hondo": ("--ll-boton-texto", "--ll-acento-hondo", 4.5),
        # El rotulo de la pestana elegida: texto normal.
        "pestana-elegida": ("--ll-acento", "--ll-fondo", 4.5),
        # Las tres paradas del degradado del titulo: texto grande.
        "titulo-1": ("--ll-titulo-1", "--ll-fondo", 3.0),
        "titulo-2": ("--ll-titulo-2", "--ll-fondo", 3.0),
        "titulo-3": ("--ll-titulo-3", "--ll-fondo", 3.0),
        # Las casillas de opcion: el cuestionario entero de "Mi nivel"
        # y el selector de colores. Se anadieron porque al forzar el
        # color del texto de la paleta sin tocar el relleno que pinta
        # Gradio, quedaron en 1,03:1 medidos en el Space.
        "casilla": ("--ll-texto", "--ll-panel", 4.5),
        "casilla-encima": ("--ll-texto", "--ll-fondo-alto", 4.5),
        # La curva por capitulos vive sobre el panel, no sobre el
        # fondo. Es un objeto grafico: WCAG le pide 3:1.
        "grafica-linea": ("--ll-acento", "--ll-panel", 3.0),
        # Las tres que siguen las encontro la auditoria del contraste DESPUES
        # de arreglar C1, y las tres son el mismo fallo en sitios que nadie
        # habia revisado. El fondo puede ser una PILA de capas: un rgba sobre
        # otro rgba no da lo mismo que sobre el fondo pelado.
        #
        # La franja de error: era el unico sitio donde el color seguia
        # saliendo del tema del navegador, 1,02:1 en las paletas claras.
        "error": ("--ll-texto", ("--ll-fondo-bajo",), 4.5),
        # El resaltado al seleccionar una palabra, que es COMO SE CONSULTA EL
        # DICCIONARIO. Estaba clavado en amarillo y daba 1,20:1 en las claras.
        "seleccion": ("--ll-lector-texto",
                      ("--ll-lector-fondo", "--ll-seleccion"), 4.5),
        # La barra de avance de "Mis libros" contra su propio canal: 1,47:1.
        # Objeto grafico, 3:1. (El borde de la cita del cuaderno es la misma
        # pareja que `grafica-linea`, asi que no se repite aqui.)
        "barra-avance": ("--ll-acento", ("--ll-panel", "--ll-borde"), 3.0),
        # El subrayado de acierto y el de fallo de la pronunciacion. Iban
        # clavados en el CSS: verde 2,21 y rojo 2,86 en las paletas claras.
        # El del fallo se mide sobre SU fondo rojizo, que es donde vive.
        "voz-bien": ("--ll-bien", ("--ll-lector-fondo",), 3.0),
        "voz-mal": ("--ll-mal", ("--ll-lector-fondo", "--ll-mal-fondo"), 3.0),
        # Y la palabra fallada tiene que leerse sobre ese fondo rojizo.
        "voz-mal-texto": ("--ll-lector-texto",
                          ("--ll-lector-fondo", "--ll-mal-fondo"), 4.5),
    }

    malas = []
    for k, d in paletas_mod.PALETAS.items():
        v = d["vars"]
        for etiqueta, (a, capas, minimo) in PARES.items():
            capas = (capas,) if isinstance(capas, str) else capas
            if a not in v or any(c not in v for c in capas):
                malas.append(f"{k}/{etiqueta}=falta variable")
                continue
            # El fondo se compone sobre --ll-fondo antes de medir, y el texto
            # sobre ese fondo ya compuesto. Medir el color declarado en vez
            # del compuesto es exactamente el error que dejo pasar la
            # opacidad del .62. Y se admite una PILA: la seleccion del lector
            # son tres capas semitransparentes, una encima de otra.
            fondo = rgba(v["--ll-fondo"])
            for c in capas:
                fondo = sobre(v[c], "rgb(%d,%d,%d)" % fondo[:3])
            texto = sobre(v[a], "rgb(%d,%d,%d)" % fondo[:3])
            la = lum("rgb(%d,%d,%d)" % texto[:3])
            lb = lum("rgb(%d,%d,%d)" % fondo[:3])
            r = (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
            if r < minimo:
                malas.append(f"{k}/{etiqueta}={r:.2f} (pide {minimo})")
    assert not malas, malas
    return (f"{len(paletas_mod.PALETAS)} paletas x {len(PARES)} pares, "
            f"todas AA")


prueba("todas las paletas son legibles", _contraste_suficiente)


def _opacidad_no_borra_el_texto():
    """El texto con `opacity` tambien tiene que pasar AA.

    Esto lo destapo Miguel probando la aplicacion: "en las pastel las letras
    son muy tenues". El color del texto estaba bien -10:1 en las tres claras-
    y todas las parejas pasaban la prueba de contraste. El culpable era el CSS:
    `opacity:.62` sobre un fondo claro compone el texto con el fondo y lo deja
    en 3,4:1, y ningun color declarado cambia, asi que la prueba anterior no
    podia verlo.

    Medido: con .74 la peor paleta clara (menta) llega justo a 4,5. El CSS usa
    .78 en adelante para tener margen.
    """
    import re

    def rgb(c):
        """Acepta `#abc`, `#aabbcc`, `rgb(...)` y `rgba(...)`.

        Antes solo entendia hex de seis y la paleta que no lo fuera se
        SALTABA en silencio (un `continue`), o sea que declarar el fondo
        como `rgb(...)` habria apagado la prueba entera sin avisar.
        """
        c = c.strip()
        if c.startswith("#"):
            c = c[1:]
            if len(c) == 3:
                c = "".join(x * 2 for x in c)
            if len(c) != 6:
                raise ValueError(f"color que no se sabe leer: {c!r}")
            return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
        if c.startswith("rgb"):
            n = c[c.find("(") + 1:c.find(")")].split(",")
            return tuple(int(float(x)) for x in n[:3])
        raise ValueError(f"color que no se sabe leer: {c!r}")

    def lum(c):
        def f(v):
            v /= 255
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        r, g, b = c
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    def ratio(a, b):
        la, lb = lum(a), lum(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    def componer(texto, fondo, alfa):
        t_, f_ = rgb(texto), rgb(fondo)
        return tuple(round(t_[i] * alfa + f_[i] * (1 - alfa)) for i in range(3))

    # El regex de antes era `opacity:(\.[0-9]+)`, y solo veia la forma `.NN`.
    # Un `opacity: 0.3` o un `opacity:0` -texto invisible- no contaban, asi
    # que la prueba pasaba por CONVENCION DE ESCRITURA y no por cobertura:
    # con el mismo color pintado, `opacity:.3` la hacia fallar y `opacity:0.3`
    # no. Ahora se aceptan las cuatro formas y el porcentaje. Y se leen los
    # DOS archivos con CSS: una opacidad anadida en `paletas.py` no se media.
    fuentes = [pathlib.Path(__file__).parent / "app" / f
               for f in ("ui.py", "paletas.py")]
    crudas = []
    for f in fuentes:
        crudas += re.findall(r"opacity\s*:\s*([0-9]*\.?[0-9]+%?)",
                             f.read_text(encoding="utf-8"))
    alfas = {float(x[:-1]) / 100 if x.endswith("%") else float(x)
             for x in crudas}
    assert alfas, "no encuentro ninguna opacidad en el CSS"

    malas = []
    for nombre, d in paletas_mod.PALETAS.items():
        v = d["vars"]
        fondo, texto = v["--ll-fondo"], v["--ll-texto"]
        for a in alfas:
            r = ratio(componer(texto, fondo, a), rgb(fondo))
            if r < 4.5:
                malas.append(f"{nombre}/opacity:{a}={r:.2f}")
    assert not malas, malas
    return (f"{len(paletas_mod.PALETAS)} paletas x {len(alfas)} opacidades, "
            f"todas AA compuestas")


prueba("la opacidad del CSS no borra el texto", _opacidad_no_borra_el_texto)

# Las cuatro pruebas que siguen nacieron de la decima auditoria y de que
# Miguel abriera la app en el movil. Necesitan estos dos modulos aqui
# arriba: `cuentas` se importa mas abajo para las pruebas del contador, y
# a estas alturas del archivo todavia no existe.
import cuentas as cuentas_mod  # noqa: E402
import scoring  # noqa: E402


def _la_paleta_manda_sobre_el_navegador():
    """El CSS de cada paleta tiene que redefinir las variables de Gradio.

    Gradio pinta el markdown con `.prose *{color:var(--body-text-color)}`, y
    esa variable la resuelve SU tema segun el modo claro/oscuro del visitante.
    Si la paleta no la redefine, el color del texto lo decide el navegador y
    no la paleta: medido en el Space con ?__theme=light, la paleta por defecto
    daba 1,1:1 -pagina negra sin texto-.

    La prueba anterior de contraste no podia verlo, porque mide --ll-texto
    sobre --ll-fondo, una pareja que el navegador nunca llega a pintar.
    """
    imprescindibles = ("--body-text-color", "--body-background-fill",
                       "--block-title-text-color", "--block-label-text-color")
    malas = []
    for nombre in paletas_mod.PALETAS:
        css = paletas_mod.css(nombre)
        for var in imprescindibles:
            if f"{var}:var(--ll-" not in css:
                malas.append(f"{nombre}: no redefine {var}")
        # Y tiene que valer tambien en modo oscuro, no solo en :root.
        if ".dark" not in css:
            malas.append(f"{nombre}: no cubre el modo oscuro")
    assert not malas, malas
    return f"{len(paletas_mod.PALETAS)} paletas redefinen el tema en los dos modos"


prueba("la paleta manda sobre el modo del navegador",
       _la_paleta_manda_sobre_el_navegador)


def _las_superficies_tambien_salen_de_la_paleta():
    """No basta con forzar el COLOR DEL TEXTO: hay que forzar el fondo.

    La primera version de la correccion redefinia --body-text-color y se
    quedaba ahi. Resultado medido en el Space con ?__theme=dark y la
    paleta menta: las casillas de opcion -el cuestionario entero de "Mi
    nivel", que es la primera pantalla- con letra de la paleta sobre el
    relleno del tema, 1,11:1. Con amanecer y papel, 1,03:1.

    Arreglar solo uno de los dos no mejora el contraste: lo mueve de
    sitio. Aqui se comprueba que van los dos.
    """
    superficies = ("--checkbox-label-background-fill",
                   "--checkbox-label-text-color",
                   "--input-background-fill",
                   "--button-secondary-background-fill",
                   "--button-secondary-text-color",
                   "--block-background-fill",
                   "--table-even-background-fill",
                   "--color-accent",
                   # La franja de error se quedo fuera del arreglo de C1 y era
                   # el unico sitio donde el color seguia saliendo del tema
                   # del navegador: 1,02:1 con las paletas claras, o sea que
                   # el aviso de que algo ha fallado era lo unico ilegible.
                   "--error-text-color",
                   "--error-background-fill")
    malas = []
    for nombre in paletas_mod.PALETAS:
        css = paletas_mod.css(nombre)
        for var in superficies:
            if f"{var}:var(--ll-" not in css:
                malas.append(f"{nombre}: no redefine {var}")
    # Y la casilla ELEGIDA: lleva el relleno del boton, asi que su letra
    # tiene que ser la del boton. La regla general de `label` le ganaba.
    for nombre in paletas_mod.PALETAS:
        if "label.selected" not in paletas_mod.css(nombre):
            malas.append(f"{nombre}: la casilla elegida se queda sin regla")
    assert not malas, malas
    return f"{len(superficies)} superficies atadas a la paleta"


prueba("las superficies tambien salen de la paleta",
       _las_superficies_tambien_salen_de_la_paleta)


def _colores_literales(fragmento: str) -> list[str]:
    """Los colores escritos a mano en un trozo de CSS o de Python.

    Vive aparte porque lo usan dos pruebas y porque su historia es una lista
    de agujeros que se fueron tapando de uno en uno:

    - primero solo miraba `#[0-9a-fA-F]{6}`, asi que el MISMO color escrito
      `#8ce` en vez de `#88ccee` pasaba sin que nadie dijera nada;
    - luego se le anadieron `rgb()` y `hsl()`;
    - y seguia sin ver los colores POR NOMBRE. Un banco de mutaciones lo
      demostro clavando `background:yellow` en el resaltado del lector: la
      prueba de colores clavados pasaba en verde, con el amarillo que un
      comentario de `ui.py` dice haber desterrado.

    `transparent` NO cuenta: es lo contrario de un color clavado y se usa a
    proposito -el lienzo de la grafica y el subrayado de la voz-. `inherit` y
    `currentColor` si cuentan cuando aparecen como color, porque son la otra
    forma de saltarse la paleta: fue el fallo de `#ll-lector` y de `#ll-voz`.
    """
    import re
    NOMBRES = (r"\b(?:yellow|red|blue|green|white|black|gray|grey|orange|pink|"
               r"purple|violet|brown|cyan|magenta|lime|navy|teal|olive|maroon|"
               r"silver|gold|beige|ivory|khaki|salmon|coral|crimson|indigo|"
               r"turquoise|aqua|fuchsia)\b")
    return (re.findall(r"#[0-9a-fA-F]{3,8}\b", fragmento)
            + re.findall(r"(?:rgba?|hsla?)\([0-9][^)]*\)", fragmento)
            + re.findall(NOMBRES, fragmento)
            + re.findall(r"currentColor|(?<=color:)\s*inherit", fragmento))


def _el_css_no_clava_los_colores_que_ya_fallaron():
    """Cuatro reglas del CSS pintaban un color fijo con la paleta que fuera.

    Las encontro una auditoria DESPUES de dar C1 por cerrado, y todas se
    escaparon por el mismo motivo: `_contraste_suficiente` mide VARIABLES de
    la paleta, asi que un color clavado en el CSS le es invisible -puede
    seguir en verde midiendo una variable que ya no se pinta-.

    Medido antes del arreglo, en las tres paletas claras: el resaltado de
    seleccion 1,20:1 (y es COMO SE CONSULTA EL DICCIONARIO), el canal de la
    barra de avance 1,47:1, el borde de la cita del cuaderno 1,23:1. Y dos
    variables declaradas en las cinco paletas eran codigo muerto porque otra
    regla posterior les ganaba: `--ll-seleccion` y `--ll-lector-texto`.
    """
    import re
    fuente = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(
        encoding="utf-8")
    css = "\n".join(re.findall(r"<style>.*?</style>", fuente, re.S))
    # Los comentarios del CSS citan los colores viejos A PROPOSITO, para que
    # se sepa que fallaba. No cuentan como color clavado.
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    reglas = {
        "#ll-lector::selection": "--ll-seleccion",
        "#ll-lector{": "--ll-lector-texto",
        "#ll-biblio .ll-b{": "--ll-borde",
        "#ll-biblio .ll-b i{": "--ll-acento",
        "#ll-cuaderno .ll-f{": "--ll-acento",
        # `#ll-voz` repetia palabra por palabra el fallo de `#ll-lector`: un
        # `border` abreviado y posterior en el DOM que reescribia entero el
        # `border-color:var(--ll-borde)`, y un `color:inherit` encima. Se
        # corrigio en uno y no en el otro.
        "#ll-voz{": "--ll-borde",
        "#ll-voz .ok{": "--ll-bien",
        "#ll-voz .mal{": "--ll-mal",
    }
    malas = []
    for selector, variable in reglas.items():
        # Cada selector puede aparecer VARIAS veces: el lector se pinta en
        # dos bloques, uno de ellos una f-string con `{_RADIO}` dentro, asi
        # que recortar hasta la primera `}` da un cuerpo a medias. Se miran
        # todas las apariciones: ninguna puede clavar un color, y al menos
        # una tiene que usar la variable de la paleta.
        cuerpos, i = [], css.find(selector)
        while i >= 0:
            cuerpos.append(css[i:css.find("}", i) + 1])
            i = css.find(selector, i + 1)
        if not cuerpos:
            malas.append(f"no encuentro la regla {selector}")
            continue
        if not any(variable in c for c in cuerpos):
            malas.append(f"{selector} ya no usa {variable}")
        for c in cuerpos:
            clavados = _colores_literales(c)
            if clavados:
                malas.append(f"{selector} vuelve a clavar {clavados}")
    assert not malas, malas
    return f"{len(reglas)} reglas atadas a la paleta, sin color clavado"


prueba("el CSS no clava los colores que ya fallaron",
       _el_css_no_clava_los_colores_que_ya_fallaron)


def _ningun_color_literal_en_el_css():
    """NINGUN color escrito a mano en el CSS de la aplicacion. Cero.

    La prueba de aqui arriba vigila ocho selectores concretos, y por eso
    sobrevivian mutantes que clavaban un color en cualquier OTRO sitio: el
    fondo de una tarjeta del cuaderno, el de la estanteria, el degradado del
    titulo, y -el peor- `button.primary{background:#2e9cc4 !important}`, o sea
    el boton que mas se pulsa de la aplicacion, con la pareja `boton-alto` de
    la prueba de contraste midiendo una variable que ya no se pintaba.

    Vigilar selectores de uno en uno es perder siempre: hay que invertir la
    regla. Los colores viven en `PALETAS[...]["vars"]` de `paletas.py` y en
    ningun otro sitio; el CSS solo los referencia con `var(--ll-...)`. Hoy
    `ui.py` cumple eso al pie de la letra -cero literales- y el generador
    `css()` tambien, asi que la invariante se puede exigir entera.
    """
    import re
    PERMITIDOS = {
        # Transparencias deliberadas: el lienzo de la grafica y la leyenda van
        # transparentes PARA que se vea el fondo de la paleta, que es lo
        # contrario de un color clavado.
        "rgba(0,0,0,0)", "transparent",
    }
    malos = []
    for rel, trozo in (("app/ui.py", None), ("app/paletas.py", "def css(")):
        t = (pathlib.Path(__file__).parent / rel).read_text(encoding="utf-8")
        if trozo:
            # Solo el GENERADOR, no las definiciones de las paletas: ahi los
            # colores literales son el contenido legitimo. Aqui el CSS vive
            # dentro de cadenas, asi que una linea que empiece por `#` si es un
            # comentario de Python.
            t = t[t.index(trozo):]
            t = re.sub(r"^\s*#.*$", " ", t, flags=re.M)
        else:
            # Solo los bloques <style>. Y OJO: aqui NO se pueden quitar
            # "comentarios de Python" por empezar la linea con `#`, porque un
            # selector de id empieza exactamente asi. Al hacerlo, este mismo
            # comprobador borraba TODAS las reglas de id -o sea casi todo el
            # CSS- y daba cero literales midiendo el vacio. Se descubrio
            # mutando: clavar un color en `#ll-cuaderno .ll-p` no lo cazaba.
            t = "\n".join(re.findall(r"<style>.*?</style>", t, re.S))
        t = re.sub(r"/\*.*?\*/", " ", t, flags=re.S)     # comentarios CSS
        for c in _colores_literales(t):
            if c.replace(" ", "") not in PERMITIDOS:
                malos.append(f"{rel}: {c}")
    # Y las dos reglas que sostienen el arreglo del critico: si desaparecen, el
    # texto vuelve al color del tema del navegador -1,1:1 medido en el Space-.
    css = paletas_mod.css("hielo")
    if ".prose" not in css:
        malos.append("paletas.py: falta la regla de .prose")
    # Y DENTRO de su regla, no en cualquier parte del CSS: `--ll-boton-texto`
    # aparece tambien en las variables del tema, asi que buscarlo en todo el
    # CSS daba por bueno un `label.selected{color:var(--ll-texto)}`, que es el
    # 1,03:1 medido en el Space. Comprobado mutando.
    regla = re.search(r"label\.selected[^{]*\{([^}]*)\}", css)
    if regla is None:
        malos.append("paletas.py: falta la regla label.selected")
    elif "--ll-boton-texto" not in regla.group(1):
        malos.append(f"paletas.py: label.selected no usa el texto del boton: "
                     f"{regla.group(1)[:60]}")
    assert not malos, malos
    return "cero colores literales en el CSS; solo var(--ll-...)"


prueba("ningun color literal en el CSS", _ningun_color_literal_en_el_css)


def _un_txt_ya_descargado_acierta_en_la_cache():
    """La cache de Gutenberg mira las DOS extensiones, no solo `.epub`.

    Cuando el epub falla se baja el `.txt`, pero la comprobacion de cache solo
    miraba el `.epub`: un libro ya descargado como texto no acertaba nunca y se
    volvia a pedir a Gutenberg -tres intentos de red- cada vez que el lector lo
    abria. Se comprueba que con el `.txt` en la carpeta no se toca la red.
    """
    import urllib.request
    ruta = pathlib.Path(ui.RUTA_LIBROS)
    ruta.mkdir(parents=True, exist_ok=True)
    txt = ruta / "pg99999.txt"
    txt.write_bytes(b"x" * 5000)
    intentos = []

    def espia(*a, **k):
        intentos.append(a[:1])
        raise OSError("espia: la red no se debe tocar")

    real = urllib.request.urlopen
    urllib.request.urlopen = espia
    try:
        devuelto = ui._descargar_gutenberg("PG99999")
    finally:
        urllib.request.urlopen = real
        txt.unlink(missing_ok=True)
    assert not intentos, f"toco la red {len(intentos)} veces teniendo el .txt"
    assert devuelto.endswith(".txt"), devuelto
    return "con el .txt en cache no se toca la red"


prueba("un txt ya descargado acierta en la cache",
       _un_txt_ya_descargado_acierta_en_la_cache)


def _todos_los_manejadores_reciben_la_peticion():
    """Declarar `peticion: gr.Request` no basta: Gradio tiene que inyectarla.

    `special_args` (en `gradio/helpers.py`) recorre la firma y **corta en el
    primer parametro que no sea posicional**, asi que un `peticion` detras de
    un `*valores` es keyword-only y no se inspecciona nunca: llega `None`
    siempre. Le paso a `_desde_cuestionario`, y `None` significa que
    `_archivo_lector` resuelve a `lectores/anonimo/`, una sola carpeta para
    TODOS los visitantes del Space. Cada lector pisaba el perfil del anterior
    y ninguno lo recuperaba al recargar.

    En local no se nota, porque fuera del Space no se reparte por sesion. O
    sea que esto solo se puede cazar aqui, comprobando la inyeccion de verdad
    contra el Gradio instalado y no contra lo que uno cree que hace.
    """
    from gradio.helpers import special_args

    malos = []
    for nombre in dir(ui):
        f = getattr(ui, nombre)
        if not callable(f) or not nombre.startswith("_"):
            continue
        try:
            sig = inspect.signature(f)
        except (TypeError, ValueError):
            continue
        p = sig.parameters.get("peticion")
        # Solo los que ANOTAN `gr.Request`, que es como Gradio decide donde
        # inyectar. Los ayudantes internos -`_dir_lector`, `_sesion_de`,
        # `_ip`...- reciben la peticion de quien les llama, no de Gradio, y
        # llevan el parametro sin anotar a proposito.
        if p is None or "Request" not in str(p.annotation):
            continue
        # Se le dan tantas entradas como parametros posicionales, y se mira si
        # `special_args` mete el centinela en el sitio de `peticion`.
        centinela = object()
        entradas = [None] * max(0, len(sig.parameters) - 1)
        nuevas, *_ = special_args(f, inputs=list(entradas), request=centinela)
        if centinela not in nuevas:
            malos.append(f"{nombre}{sig}")
    assert not malos, malos
    return f"los manejadores con `peticion` la reciben ({len(dir(ui))} nombres revisados)"


prueba("todos los manejadores reciben la peticion",
       _todos_los_manejadores_reciben_la_peticion)


def _la_grafica_no_lleva_colores_clavados():
    """Plotly no lee CSS: la grafica es una imagen con los colores dentro.

    Estaba clavada en azul hielo -letra #c8dbe6, lineas #79d0ea y
    #4bb8da- con la paleta que fuera. Sobre el panel blanco de las tres
    paletas claras la letra de los ejes daba 1,3:1. Y no hay un color que
    valga para las cinco: sobre el fondo mas oscuro hace falta luminancia
    >= 0,186 y sobre el mas claro <= 0,174.
    """
    fuente = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(
        encoding="utf-8")
    i = fuente.find("def _grafica_analisis(")
    j = fuente.find("\ndef ", i + 10)
    cuerpo = fuente[i:j]
    assert i > 0 and j > i, "no encuentro _grafica_analisis"
    import re
    # Antes esto era solo `#[0-9a-fA-F]{6}`, o sea que el MISMO color escrito
    # como `#8ce` en vez de `#88ccee` se colaba sin que la prueba dijera nada,
    # igual que cualquier `rgb()` o `hsl()`. Se buscan las cuatro formas.
    clavados = _colores_literales(cuerpo)
    # Excepcion legitima y a proposito: el fondo del lienzo y de la leyenda
    # van TRANSPARENTES para que se vea el de la paleta. Es lo contrario de
    # un color clavado; clavar aqui cualquier otra cosa si seria el fallo.
    clavados = [c for c in clavados if c.replace(" ", "") != "rgba(0,0,0,0)"]
    assert not clavados, f"colores clavados en la grafica: {clavados}"
    assert "_colores_paleta(" in cuerpo, "no consulta la paleta"
    # Y que de verdad cambien de una paleta a otra.
    a = ui._colores_paleta("hielo")["--ll-texto"]
    b = ui._colores_paleta("papel")["--ll-texto"]
    assert a != b, "las dos paletas dan la misma letra"
    # Clave inventada: la de siempre, sin reventar.
    assert ui._colores_paleta("noexiste")["--ll-texto"] == a
    assert ui._rgba("#8fd3e8", 0.5) == "rgba(143,211,232,0.5)"
    assert ui._rgba("rgba(1,2,3,.4)", 0.5) == "rgba(1,2,3,.4)"
    return "la grafica se pinta con la paleta"


prueba("la grafica no lleva colores clavados",
       _la_grafica_no_lleva_colores_clavados)


def _clave_con_acentos():
    """Una contrasena con ene tiene que funcionar, no reventar.

    `hmac.compare_digest` con `str` solo admite ASCII y lanza TypeError con
    cualquier otra cosa. Un perfil declarado con ene no podia entrar nunca, y
    el usuario veia un "Error" pelado.
    """
    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    os.environ["LITERALEVEL_CUENTAS"] = "niño:contraseña:5,ok:simple:5"
    try:
        assert cuentas_mod.verificar("niño", "contraseña") is not None
        assert cuentas_mod.verificar("niño", "mala") is None
        assert cuentas_mod.verificar("nadie", "contraseña") is None
        assert cuentas_mod.verificar("ok", "simple") is not None
        # Y un emoji tampoco puede tirar la funcion.
        assert cuentas_mod.verificar("ok", "🙂") is None
    finally:
        if viejo is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo
    return "ene, tilde y emoji sin reventar"


prueba("una contrasena con acentos no revienta", _clave_con_acentos)


def _el_modelo_vale_como_repositorio():
    """`Puntuador` tiene que aceptar un repositorio del Hub, no solo carpeta.

    Es el camino que usa el despliegue y el que ninguna prueba ejercitaba: en
    esta maquina existe ./modelo_v4, asi que todo se cargaba de disco y la
    aplicacion desplegada no podia puntuar NADA.

    No se descarga el modelo aqui -son 328 MB-: se comprueba la decision, que
    es donde estaba el fallo.
    """
    from scoring import _parece_repo_hf
    assert _parece_repo_hf("MikeMaki1763/literalevel-v4")
    assert _parece_repo_hf("owner/name")
    for ruta in ("modelo_v4", "./modelo_v4", "C:/Users/x/modelo_v4",
                 "/tmp/modelo", "a/b/c", "sin-barra", ""):
        assert not _parece_repo_hf(ruta), ruta
    # Y una carpeta que no existe tiene que seguir dando el error legible.
    try:
        scoring.Puntuador("carpeta-que-no-existe-en-ningun-sitio")
    except FileNotFoundError as e:
        assert "No encuentro el modelo" in str(e), str(e)
    except Exception as e:
        raise AssertionError(f"deberia ser FileNotFoundError, fue {type(e).__name__}")
    else:
        raise AssertionError("no lanzo nada con una carpeta inexistente")

    # Y AHORA la comprobacion que de verdad caza la regresion. Todo lo de
    # arriba mide `_parece_repo_hf` POR SEPARADO, y con el guardia roto -o
    # sea, volviendo a `if not os.path.isdir(ruta)`- sigue pasando entero:
    # se comprobo mutando esa linea. Lo unico que distingue el codigo bueno
    # del roto es construir el Puntuador CON un identificador y ver que llega
    # a cargar. No se descargan los 328 MB: se corta `from_pretrained` con un
    # centinela en cuanto lo llaman, que es justo despues del guardia.
    import transformers

    class _Llego(Exception):
        pass

    def _centinela(*a, **k):
        raise _Llego(str(a[0]) if a else "")

    guardados = (transformers.AutoTokenizer.from_pretrained,
                 transformers.AutoModelForSequenceClassification.from_pretrained)
    transformers.AutoTokenizer.from_pretrained = _centinela
    transformers.AutoModelForSequenceClassification.from_pretrained = _centinela
    try:
        scoring.Puntuador("MikeMaki1763/literalevel-v4")
    except _Llego as e:
        assert "MikeMaki1763/literalevel-v4" in str(e), str(e)
    except FileNotFoundError as e:
        raise AssertionError(
            "el guardia rechaza el repositorio del Hub, que es EXACTAMENTE "
            f"el fallo que dejo la app desplegada sin poder puntuar: {e}")
    else:
        raise AssertionError("no llego a cargar y no dijo por que")
    finally:
        (transformers.AutoTokenizer.from_pretrained,
         transformers.AutoModelForSequenceClassification.from_pretrained) = guardados

    return ("acepta repositorio -y LLEGA a cargarlo-, rechaza carpeta "
            "inexistente con mensaje")


prueba("el modelo vale como repositorio del Hub",
       _el_modelo_vale_como_repositorio)


def _la_entrada_al_perfil_esta_arriba():
    """La caja de entrar tiene que ir ANTES de las pestanas y abierta.

    Estaba en un acordeon cerrado dentro de una de ocho pestanas y no la
    encontraba nadie, empezando por el autor. Se comprueba sobre el codigo
    fuente porque construir la interfaz entera aqui costaria mas que la
    prueba: lo que importa es el ORDEN, y el orden esta escrito.
    """
    fuente = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(encoding="utf-8")
    i_entrar = fuente.find('gr.Accordion("Entrar con tu perfil"')
    i_pestanas = fuente.find("with gr.Tabs()")
    assert i_entrar > 0, "no encuentro el acordeon de entrar"
    assert i_pestanas > 0, "no encuentro las pestanas"
    assert i_entrar < i_pestanas, "la entrada al perfil va DESPUES de las pestanas"
    tramo = fuente[i_entrar:i_entrar + 120]
    assert "open=True" in tramo, "el acordeon de entrar esta cerrado"
    # Y la consulta de palabra, antes del texto del capitulo.
    i_palabra = fuente.find('gr.Accordion("Consultar una palabra"')
    i_texto = fuente.find("texto = gr.HTML(_html_lectura")
    assert 0 < i_palabra < i_texto, "la palabra va despues del texto del capitulo"
    return "entrar arriba y abierto; la palabra antes del texto"


prueba("lo que abre funciones se encuentra",
       _la_entrada_al_perfil_esta_arriba)


titulo("Bandas coherentes con la letra")

# Un texto no puede llamarse "C1" y "intermedio" en la misma linea. Antes si
# pasaba: con los cortes en 0,8 y 1,6 y un modelo que comprime sus
# predicciones, "avanzado" solo lo alcanzaba un C2 y tres de los cinco niveles
# medidos caian en "intermedio".
def _bandas_coherentes():
    malas = []
    for i in range(0, 201):
        v = i / 100
        letra, banda = ui._cefr(v), ui.scoring.public_band(v)
        esperada = {"A": "básico", "B": "intermedio", "C": "avanzado"}[letra[0]]
        if banda != esperada:
            malas.append(f"{v:.2f} -> {letra} pero {banda}")
    assert not malas, malas[:5]
    return "las 201 puntuaciones concuerdan"


prueba("la banda nunca contradice a la letra", _bandas_coherentes)
def _tres_bandas():
    b = sorted({ui.scoring.public_band(i / 100) for i in range(0, 201)})
    assert b == ["avanzado", "básico", "intermedio"], b
    return b


prueba("las tres bandas son alcanzables", _tres_bandas)
prueba("banda con un valor fuera de escala",
       lambda: (ui.scoring.public_band(-5), ui.scoring.public_band(99)))


# La letra sale por dos caminos: `ui._cefr` la calcula desde la puntuacion
# publica para la tabla, y `scoring.anchor_cefr` desde la interna para el
# contrato de `Resultado`. Tienen que coincidir SIEMPRE. No coincidian: una
# usaba floor(x + 0,5) y la otra `round`, que redondea al par, asi que en los
# empates -interno 0,5, 2,5 y 4,5- una decia A1, B1, C1 y la otra A2, B2, C2.
def _una_sola_letra():
    malas = []
    for i in range(0, 50001):
        y = i / 10000
        a, b = ui._cefr(ui.scoring.public_score(y)), ui.scoring.anchor_cefr(y)
        if a != b:
            malas.append(f"interno {y} -> interfaz {a} / contrato {b}")
    assert not malas, malas[:5]
    return "las 50.001 coinciden"


prueba("la interfaz y el contrato dan la misma letra", _una_sola_letra)
prueba("los empates suben, no se van al par",
       lambda: [ui.scoring.anchor_cefr(y) for y in (0.5, 1.5, 2.5, 3.5, 4.5)]
       == ["A2", "B1", "B2", "C1", "C2"] and "suben todos")


titulo("Codigos de acceso a lo que cuesta dinero")

# La app entera es libre; lo que va a OpenAI -explicacion en contexto y
# pronunciacion- se cierra detras de un codigo, porque el enlace es publico y
# el saldo es de Miguel.
import cuentas as cuentas_mod  # noqa: E402


def _con_codigos(fn):
    """Ejecuta `fn` con una tabla de codigos de mentira, y la retira despues."""
    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    os.environ["LITERALEVEL_CUENTAS"] = "jefe:LLAVE-A:0,invitado:LLAVE-B:2"
    try:
        return fn()
    finally:
        if viejo is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo


prueba("sin codigos configurados no se cierra nada",
       lambda: cuentas_mod.permite(pathlib.Path(TMP), None)[0] is True)
prueba("un codigo inventado no abre nada",
       lambda: _con_codigos(
           lambda: cuentas_mod.permite(pathlib.Path(TMP), "no-existe")[0]) is False)
prueba("sin codigo, con la puerta puesta, no pasa",
       lambda: _con_codigos(
           lambda: cuentas_mod.permite(pathlib.Path(TMP), None)[0]) is False)
prueba("el codigo sin tope no se agota",
       lambda: _con_codigos(
           lambda: cuentas_mod.queda(pathlib.Path(TMP),
                                     cuentas_mod.validar("jefe:LLAVE-A")) is None))
prueba("codigo vacio, None y espacios",
       lambda: _con_codigos(
           lambda: [cuentas_mod.validar(x) for x in ("", None, "   ")]))


def _cupo_se_agota():
    def dentro():
        base = pathlib.Path(pruebas_tmp.carpeta("cupo_"))
        c = cuentas_mod.validar("invitado:LLAVE-B")
        vistos = []
        for _ in range(4):
            ok = cuentas_mod.permite(base, "invitado:LLAVE-B")[0]
            vistos.append(ok)
            if ok:
                cuentas_mod.apuntar(base, c)
        return vistos
    v = _con_codigos(dentro)
    assert v == [True, True, False, False], v
    return "dos usos y se cierra"


prueba("el cupo se agota y no revive", _cupo_se_agota)


def _sin_carrera():
    """Veinte peticiones simultaneas con un cupo de dos: pasan dos.

    Antes pasaban las veinte y el contador acababa en 1. Preguntar el cupo y
    apuntarlo eran dos operaciones, y entre las dos cabia media aplicacion.
    """
    import threading
    def dentro():
        base = pathlib.Path(pruebas_tmp.carpeta("carrera_"))
        pasaron = []
        def intento():
            if cuentas_mod.consumir(base, "invitado:LLAVE-B")[0]:
                pasaron.append(1)
        hilos = [threading.Thread(target=intento) for _ in range(20)]
        for h in hilos: h.start()
        for h in hilos: h.join()
        return len(pasaron)
    n = _con_codigos(dentro)
    assert n == 2, f"pasaron {n} peticiones con un cupo de 2"
    return "20 simultaneas, cupo 2, pasan 2"


def _no_se_pierden_apuntes():
    """Dos hilos x 200 usos con cupo sin limite: el contador llega a 400."""
    import threading
    def dentro():
        base = pathlib.Path(pruebas_tmp.carpeta("apuntes_"))
        def bucle():
            for _ in range(200):
                cuentas_mod.consumir(base, "jefe:LLAVE-A")
        hs = [threading.Thread(target=bucle) for _ in range(2)]
        for h in hs: h.start()
        for h in hs: h.join()
        return cuentas_mod.gastado(base, "jefe")
    n = _con_codigos(dentro)
    # El codigo sin tope no gasta cupo, asi que no debe contarse.
    assert n == 0, f"un codigo sin tope no deberia apuntar usos, y apunto {n}"
    return "el codigo sin tope no consume contador"


prueba("veinte peticiones a la vez no burlan el cupo", _sin_carrera)
prueba("el codigo sin tope no gasta contador", _no_se_pierden_apuntes)
prueba("consumir con la puerta quitada deja pasar",
       lambda: cuentas_mod.consumir(pathlib.Path(TMP), None)[0] is True)


titulo("Las tres puertas del dinero")

# Fable senalo que NINGUNA de las 198 pruebas tocaba los manejadores que
# deciden si se gasta dinero. Estas tres los ejercitan sin red: con la puerta
# puesta y sin codigo, los tres tienen que negarse y devolver texto legible.
def _con_puerta(fn):
    """Con perfiles declarados Y con clave.

    Lo de la clave se anadio con la auditoria 16: los tres manejadores de pago
    se cortan ahora ANTES de la puerta de perfil cuando no hay
    `OPENAI_API_KEY`, porque sin clave no puede haber llamada y no hay nada que
    cobrar. Esta suite corre sin clave a proposito, asi que sin fingirla las
    pruebas de la puerta de perfil ya no llegan a la puerta: medirian el
    mensaje de «falta la clave», que es otra cosa.
    """
    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    viejo_falta = config_mod.falta
    os.environ["LITERALEVEL_CUENTAS"] = "jefe:LLAVE-A:0"
    config_mod.falta = lambda: []
    ui._CODIGO_SESION.clear()
    try:
        return fn()
    finally:
        config_mod.falta = viejo_falta
        if viejo is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo
        ui._CODIGO_SESION.clear()


def _sinopsis_pide_codigo():
    tramos = list(ui._de_que_trata(libro_ok))
    texto = str(tramos[-1])
    assert "entres con tu perfil" in texto, texto[:120]
    return "la sinopsis se niega sin codigo"


prueba("la sinopsis pide codigo", lambda: _con_puerta(_sinopsis_pide_codigo))


def _la_consulta_lexica_pide_codigo():
    """La TERCERA puerta, que no tenia prueba y es la que mas se abre.

    Una auditoria lo demostro mutando `puede, motivo_pago = _puede_pagar(...)`
    por `True, ""`: las 222 pruebas seguian en verde. Es la puerta que se cruza
    en cada palabra que consulta el lector, o sea la que mas veces decide si se
    gasta dinero.

    Se comprueba lo que de verdad importa: que al consultor se le pase
    `usar_openai=False`, y que la ficha diga por que.
    """
    visto = []

    class Consultor:
        def consultar(self, *a, **k):
            visto.append(k.get("usar_openai"))
            from lexicon import ResultadoLexico
            return ResultadoLexico(
                "hi", "hi", "hi", "hi", "INTJ", "interjection", "A greeting.",
                [], 0.8, 2, None, None, None, None, False, None, None, None,
                None, "basico", 5.0, False, [])

    antes, falta_antes = ui.consultor, config_mod.falta
    ui.consultor = lambda: Consultor()
    # Con clave: lo que se prueba es la PUERTA DE PERFIL. Sin clave no hay nada
    # que cobrar y el aviso correcto pasa a ser "no hay clave", que es otra cosa.
    config_mod.falta = lambda: []
    try:
        ficha = consulta(None, None, None, "hello", "Hello there.", "es")[0]
    finally:
        ui.consultor, config_mod.falta = antes, falta_antes
    assert visto == [False], f"se le paso usar_openai={visto}"
    assert "perfil" in ficha.lower(), f"no dice por que: {ficha[:120]}"
    return "sin perfil, la consulta va con usar_openai=False y lo dice"


prueba("la consulta lexica pide codigo",
       lambda: _con_puerta(_la_consulta_lexica_pide_codigo))


def _los_topes_por_hora_estan_puestos():
    """Los tres topes tienen que ser mayores que cero por defecto.

    La prueba que ejercita el tope de consultas SUSTITUYE la constante por 1,
    asi que el valor real del modulo no lo miraba nadie: poner
    `LIMITE_VOZ_HORA = 0` -que significa SIN LIMITE- pasaba las 222 pruebas.
    """
    topes = {"consultas": ui.LIMITE_CONSULTAS_HORA,
             "voz": ui.LIMITE_VOZ_HORA,
             "sinopsis": ui.LIMITE_SINOPSIS_HORA}
    malos = [f"{k}={v}" for k, v in topes.items() if not v or v <= 0]
    assert not malos, f"topes apagados: {malos}"
    assert ui._VENTANA == 3600.0, ui._VENTANA
    return f"consultas {topes['consultas']}, voz {topes['voz']}, sinopsis {topes['sinopsis']}, por hora"


prueba("los topes por hora estan puestos", _los_topes_por_hora_estan_puestos)


def _medir_con_el_modelo_inalcanzable():
    """Si el modelo no se puede cargar, `_medir` devuelve texto, no traceback.

    `_medir` solo atrapaba `FileNotFoundError`, que cubre la carpeta local
    ausente. Desplegada, `LITERALEVEL_MODELO` es un repositorio del Hub y
    `from_pretrained` lanza `OSError` si el Hub no responde o la descarga se
    corta en el arranque en frio: el boton "¿Como de dificil es este capitulo?"
    escupia el traceback a la interfaz. Los otros tres manejadores que cargan
    el modelo ya lo atrapaban; este se habia quedado fuera, y ninguna prueba
    medía con un modelo ausente.
    """
    def revienta():
        raise OSError("We couldn't connect to 'https://huggingface.co'")

    antes = ui.puntuador
    ui.puntuador = revienta
    try:
        # Se itera: `_medir` es generadora y sin iterarla no se ejecuta nada.
        salida = str(list(ui._medir(libro_ok, 0))[-1])
    finally:
        ui.puntuador = antes
    assert "huggingface" in salida.lower(), salida[:120]
    return "con el modelo inalcanzable devuelve aviso, no traceback"


prueba("medir con el modelo inalcanzable", _medir_con_el_modelo_inalcanzable)


def _voz_y_sinopsis_respetan_su_tope():
    """Los cubos «voz» y «sinopsis» tampoco tenian prueba.

    Los dos mutantes que apagaban su `_dentro_del_limite` sobrevivian. Se
    agota un tope de 1 de verdad y se comprueba que el segundo intento trae el
    aviso de limite, no el resultado.
    """
    antes = (ui.LIMITE_VOZ_HORA, ui.LIMITE_SINOPSIS_HORA)
    ui.LIMITE_VOZ_HORA = ui.LIMITE_SINOPSIS_HORA = 1
    pet = _Pet(ip="10.7.7.7")
    # El cubo por hora solo se gasta si la pulsacion PUEDE costar dinero, asi
    # que aqui se finge que hay clave: sin ella no hay tope que probar.
    falta_antes = config_mod.falta
    config_mod.falta = lambda: []
    try:
        ui._practicar("no_existe.wav", "hello", pet)
        segunda_voz = str(ui._practicar("no_existe.wav", "hello", pet)[1])
        list(ui._de_que_trata(libro_ok, pet))
        segunda_sin = str(list(ui._de_que_trata(libro_ok, pet))[-1])
    finally:
        ui.LIMITE_VOZ_HORA, ui.LIMITE_SINOPSIS_HORA = antes
        config_mod.falta = falta_antes
    aviso = ui._mensaje_limite("es", 60)[:28]
    assert aviso in segunda_voz, f"la voz no freno: {segunda_voz[:110]}"
    assert aviso in segunda_sin, f"la sinopsis no freno: {segunda_sin[:110]}"
    return "voz y sinopsis frenan al agotar su tope"


prueba("voz y sinopsis respetan su tope", _voz_y_sinopsis_respetan_su_tope)


def _no_se_cobra_lo_que_no_se_gasta():
    """`consumir` cobra ANTES de llamar, asi que hay que devolver si no se llamo.

    Y tiene que hacerlo en TODOS los caminos, no en uno: se reprodujeron tres
    -resumen sin cliente, consulta sin diccionario y voz sin transcripcion- que
    dejaban al lector con tres usos menos y cero llamadas a la API. `devolver`
    existia y solo se usaba en el acierto de cache.

    Se comprueba tambien el suelo en cero y que `consumir` deshaga el
    incremento que rechaza: cuatro mutantes de esa contabilidad sobrevivian.
    """
    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    os.environ["LITERALEVEL_CUENTAS"] = "invitado:LLAVE-B:3"
    base = ui.BASE_DATOS_LECTOR
    cta = cuentas_mod.validar("invitado:LLAVE-B")
    try:
        # Suelo en cero: devolver sin haber cobrado no puede dejar negativo.
        for _ in range(3):
            cuentas_mod.devolver(base, "invitado:LLAVE-B")
        assert cuentas_mod.gastado(base, "invitado") == 0, "bajo de cero"
        # Cobrar y devolver deja el contador donde estaba.
        cuentas_mod.consumir(base, "invitado:LLAVE-B")
        assert cuentas_mod.gastado(base, "invitado") == 1
        cuentas_mod.devolver(base, "invitado:LLAVE-B")
        assert cuentas_mod.gastado(base, "invitado") == 0, "no devolvio"
        # Y al rechazar por tope, el contador no sigue subiendo.
        for _ in range(3):
            cuentas_mod.consumir(base, "invitado:LLAVE-B")
        antes = cuentas_mod.gastado(base, "invitado")
        for _ in range(5):
            cuentas_mod.consumir(base, "invitado:LLAVE-B")
        assert cuentas_mod.gastado(base, "invitado") == antes == cta.tope, \
            f"el contador paso del tope: {cuentas_mod.gastado(base, 'invitado')}"
        return f"cobra, devuelve, no baja de cero y se detiene en {cta.tope}"
    finally:
        if viejo is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo


prueba("no se cobra lo que no se gasta", _no_se_cobra_lo_que_no_se_gasta)


def _la_suite_no_puede_llamar_a_openai():
    """El blindaje de la cabecera tiene que seguir puesto.

    Borrar las dos lineas que anulan `config.cargar` y vacian la clave deja la
    suite corriendo con la clave REAL de `CLAVES.txt`: medido, once llamadas de
    pago por ejecucion. Y pasaba las pruebas, porque nada comprobaba el
    blindaje. Esto lo comprueba.
    """
    assert config_mod.falta(), (
        "la suite tiene clave de OpenAI: el blindaje de la cabecera no esta "
        "puesto y estas pruebas van a gastar dinero")
    assert not os.environ.get("OPENAI_API_KEY"), "hay clave en el entorno"
    return "sin clave: la suite no puede llamar a OpenAI"


prueba("la suite no puede llamar a OpenAI", _la_suite_no_puede_llamar_a_openai)


def _los_clientes_de_openai_tienen_plazo():
    """Un cliente sin `timeout` puede tumbar el Space entero.

    El SDK de OpenAI espera 600 s por defecto y reintenta dos veces: una sola
    peticion atascada retiene su hilo casi media hora, y con la cola de Gradio
    en un solo trabajador todo lo demas se apila detras. Ocurrio: una consulta
    con perfil dejo el Space sin servir HTTP mas de media hora, mientras la API
    de Hugging Face seguia diciendo RUNNING.

    Se comprueba sobre el CODIGO, no construyendo el cliente, porque construirlo
    necesita clave y esta suite corre sin ella a proposito.
    """
    import re
    malos = []
    for rel in ("app/lexicon.py", "app/voz.py", "app/ficha.py"):
        f = pathlib.Path(__file__).parent / rel
        if not f.exists():
            continue
        for m in re.finditer(r"OpenAI\((.*?)\)", f.read_text(encoding="utf-8"),
                             re.S):
            args = m.group(1)
            if "timeout" not in args:
                malos.append(f"{rel}: OpenAI(...) sin timeout")
            if "max_retries" not in args:
                malos.append(f"{rel}: OpenAI(...) sin max_retries")
    assert not malos, malos
    return "los clientes de OpenAI llevan plazo y limite de reintentos"


prueba("los clientes de OpenAI tienen plazo",
       _los_clientes_de_openai_tienen_plazo)


# Los manejadores que cargan el v4 y comparten cola. Si se anade o se quita
# uno, esta cifra se cambia A MANO y a proposito: es la unica forma de que la
# prueba se entere de que alguien saco un manejador de la cola del modelo.
MANEJADORES_DEL_MODELO = 5


def _la_cola_admite_a_mas_de_uno():
    """Sin `demo.queue()`, Gradio atiende a UN visitante a la vez.

    Su propia documentacion lo dice de `default_concurrency_limit`: «Defaults
    to 1 if not set otherwise». Con eso, una consulta lexica esperando a OpenAI
    dejaba sin servicio a TODA la aplicacion: medido en el Space, otra sesion
    distinta pulso "Estimar mi nivel" -aritmetica pura sobre las respuestas del
    cuestionario, no toca el modelo- y se quedo 170 segundos sin respuesta. Las
    tres funciones de pago no es que fallaran: tumbaban la cola.

    Y al reves: el modelo tiene que seguir limitado. Son 2 vCPU en `cpu-basic`
    y dos puntuaciones a la vez van peor que en serie, asi que los CINCO
    manejadores que cargan el v4 comparten `concurrency_id`: medir el capitulo,
    los dos analisis del libro -completo y rapido- y las dos formas de situar
    al lector con un libro suyo.

    El umbral era `n < 4` con cinco manejadores puestos, o sea que se podia
    quitar uno sin que esto fallara. Se cuenta el numero exacto.
    """
    import re
    fuente = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(
        encoding="utf-8")
    malos = []
    m = re.search(r"demo\.queue\(([^)]*)\)", fuente)
    if m is None:
        malos.append("no se llama a demo.queue(): la cola atiende de uno en uno")
    else:
        lim = re.search(r"default_concurrency_limit\s*=\s*(\d+)", m.group(1))
        if lim is None:
            malos.append("demo.queue() sin default_concurrency_limit")
        elif int(lim.group(1)) < 2:
            malos.append(f"la cola sigue atendiendo de {lim.group(1)} en {lim.group(1)}")
    n = len(re.findall(r'concurrency_id="modelo"', fuente))
    if n != MANEJADORES_DEL_MODELO:
        malos.append(f"{n} manejadores del modelo llevan concurrency_id y "
                     f"esperaba {MANEJADORES_DEL_MODELO}")
    assert not malos, malos
    return "la cola admite 8, y el modelo va de uno en uno"


prueba("la cola admite a mas de uno", _la_cola_admite_a_mas_de_uno)


def _el_diagnostico_avisa_de_un_perfil_repetido():
    """`problemas()` y `declaradas()` no las probaba nadie.

    Son la interfaz publica que se anadio para que el secreto del Space deje
    de editarse a ciegas, y con ellas mudas el diagnostico dice "9 de 9" con
    una entrada rota. El caso caro es el usuario repetido: no desaparece el
    perfil, cambia su contrasena.
    """
    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    os.environ["LITERALEVEL_CUENTAS"] = "ana:x:0,Ana:y:5,rota:sin-tope,:vacio:1"
    try:
        avisos = cuentas_mod.problemas()
        assert cuentas_mod.declaradas() == 4, cuentas_mod.declaradas()
        assert len(cuentas_mod._tabla()) == 1, cuentas_mod._tabla()
        texto = " ".join(avisos).lower()
        for pista in ("repite", "campos", "vac"):
            assert pista in texto, f"no avisa de «{pista}»: {avisos}"
        assert "x" not in [a.split()[-1] for a in avisos], "filtro una contrasena"
        return f"{len(avisos)} avisos de 4 entradas declaradas, 1 valida"
    finally:
        if viejo is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo


prueba("el diagnostico avisa de un perfil repetido",
       _el_diagnostico_avisa_de_un_perfil_repetido)


def _el_cupo_cuadra_con_las_llamadas_de_pago():
    """Los MANEJADORES, no solo la contabilidad de `cuentas`.

    La prueba de aqui arriba ejercita `consumir`/`devolver`/`gastado` y ni
    toca `ui`. Su docstring presumia de reproducir tres caminos de manejador y
    no llamaba a ninguno: los cuatro `cuentas.devolver` de `ui.py` estaban sin
    cubrir, y borrarlos pasaba las 232 pruebas. Decorativa, en la corrección
    insignia de una auditoría entera.

    Aqui se pulsa de verdad, con un espia sobre `openai.OpenAI` que cuenta las
    llamadas de pago que HABRIA hecho cada pulsacion, y se exige la regla que
    `cuentas.py` declara: **el cupo baja si y solo si se gasta dinero**.
    """
    import openai

    llamadas = []

    class Espia:
        def __init__(self, *a, **k):
            pass

        class _Chat:
            class _C:
                @staticmethod
                def parse(**k):
                    llamadas.append("chat")
                    raise RuntimeError("espia")
            completions = _C()

        class _Audio:
            class _T:
                @staticmethod
                def create(**k):
                    llamadas.append("whisper")
                    raise RuntimeError("espia")

            class _S:
                @staticmethod
                def create(**k):
                    llamadas.append("tts")
                    raise RuntimeError("espia")
            transcriptions = _T()
            speech = _S()

        # `responses.parse` es la que usa `lexicon` para la explicacion
        # contextual, y faltaba: sin ella el espia contaba CERO llamadas en una
        # consulta que si intentaba pagar, y la prueba acusaba al codigo de
        # cobrar sin gastar. Un espia incompleto miente en la direccion que
        # parece un fallo del otro.
        class _Responses:
            @staticmethod
            def parse(**k):
                llamadas.append("responses")
                raise RuntimeError("espia")

            @staticmethod
            def create(**k):
                llamadas.append("responses")
                raise RuntimeError("espia")
        chat = _Chat()
        audio = _Audio()
        responses = _Responses()

    class _P:
        session_hash = "s-cupo"
        headers = {}
        client = type("X", (), {"host": "10.44.44.44"})()

    pet = _P()
    viejo_cli, viejo_cuentas = openai.OpenAI, os.environ.get("LITERALEVEL_CUENTAS")
    viejo_falta, viejo_clave = config_mod.falta, os.environ.get("OPENAI_API_KEY")
    openai.OpenAI = Espia
    os.environ["LITERALEVEL_CUENTAS"] = "zoe:CLAVE-Z:9"
    os.environ["OPENAI_API_KEY"] = "sk-falsa-de-prueba"
    config_mod.falta = lambda: []
    ui._CODIGO_SESION[ui._sesion_de(pet)] = "zoe:CLAVE-Z"
    gastado = lambda: cuentas_mod.gastado(ui.BASE_DATOS_LECTOR, "zoe")

    malos = []
    try:
        # `_de_que_trata` sin diccionario: revienta al construir el consultor,
        # antes de cualquier llamada. No debe cobrar.
        antes, n = gastado(), len(llamadas)
        list(ui._de_que_trata(libro_ok, pet))
        if len(llamadas) == n and gastado() != antes:
            malos.append("el resumen cobro sin una sola llamada de pago")

        # `_consultar`, con un consultor DOBLE. No vale espiar a `openai` aquí:
        # en esta suite el consultor ya se construyó sin clave, así que no
        # llamaría nunca y la prueba acusaría al código de cobrar sin gastar
        # cuando el que no es fiel es el montaje. El doble hace explícito lo
        # único que importa: si `usar_openai` llega True, hubo gasto.
        from lexicon import ResultadoLexico

        class ConsultorDoble:
            """`explicacion` y `audio` son dos caches y dos llamadas distintas.

            Antes este doble solo modelaba la explicacion, y con eso la prueba
            daba por buena la fuga de tts-1: la explicacion acertaba en cache
            -`desde_cache=True`, uso devuelto- y el audio se pedia igual,
            porque su clave se hacia con la palabra tal cual la escribio el
            libro. "Fetters", "FETTERS" y "fetters." pagaban un audio cada una
            con el cupo intacto. El doble tiene que poder decir eso.
            """

            def __init__(self, explicacion_en_cache, audio_en_cache=True):
                self.cache = explicacion_en_cache
                self.audio = audio_en_cache

            def consultar(self, *a, **k):
                # Solo hay llamada si se permite Y no acierta en cache: el
                # acierto de cache es justamente el caso en que `lexicon`
                # recibe `usar_openai=True` y no llega a pagar nada.
                pago = 0
                if k.get("usar_openai"):
                    if not self.cache:
                        llamadas.append("responses")
                        pago += 1
                    if not self.audio:
                        llamadas.append("tts")
                        pago += 1
                return ResultadoLexico(
                    "hi", "hi", "hi", "hi", "INTJ", "interjection", "A greeting.",
                    [], 0.8, 2, None, None, None, None, False, None, None, None,
                    None, "basico", 5.0, self.cache, [], pago)

        antes_c = ui.consultor
        for cache, audio, etiqueta in (
                (False, True, "sin cache: hay llamada"),
                (True, True, "todo en cache: no hay llamada"),
                # El caso de la fuga: explicacion cacheada, audio NO.
                (True, False, "explicacion en cache y audio nuevo: se paga")):
            ui.consultor = lambda c=cache, au=audio: ConsultorDoble(c, au)
            antes, n = gastado(), len(llamadas)
            consulta(None, None, None, "hello", "Hello there.", "es", pet)
            hubo, cobro = len(llamadas) > n, gastado() != antes
            if hubo != cobro:
                malos.append(f"{etiqueta}: llamada={hubo} pero cobro={cobro}")

        # Y el diccionario ausente: revienta al construir el consultor, antes
        # de cualquier llamada. Tampoco puede cobrar.
        def sin_diccionario():
            raise FileNotFoundError("No encuentro el diccionario Kaikki")

        ui.consultor = sin_diccionario
        antes, n = gastado(), len(llamadas)
        consulta(None, None, None, "hello", "Hello there.", "es", pet)
        if len(llamadas) == n and gastado() != antes:
            malos.append("sin diccionario: cobro sin una sola llamada")
        ui.consultor = antes_c

        # Y el reves, que es el que abrio un agujero: la voz sin transcripcion
        # SI gasta -gpt y tts-1-, asi que tiene que cobrar.
        antes, n = gastado(), len(llamadas)
        ui._practicar("no_existe.wav", "hello there friend", pet)
        if len(llamadas) > n and gastado() == antes:
            malos.append(f"la voz hizo {len(llamadas) - n} llamadas de pago "
                         "y NO cobro: se puede gastar sin limite")
    finally:
        openai.OpenAI = viejo_cli
        config_mod.falta = viejo_falta
        # Y el consultor. La primera seccion construye el `ConsultorLexico`
        # de verdad con `openai.OpenAI` espiado, y el espia se queda guardado
        # en `_cliente_openai`: restaurar `openai.OpenAI` no lo deshace.
        # Hoy no rompe nada porque las pruebas de despues ponen dobles, pero
        # es un espia vivo paseandose por el resto de la suite.
        ui._consultor = None
        ui._CODIGO_SESION.clear()
        for k, v in (("LITERALEVEL_CUENTAS", viejo_cuentas),
                     ("OPENAI_API_KEY", viejo_clave)):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    assert not malos, malos
    return "el cupo baja si y solo si se gasta dinero"


prueba("el cupo cuadra con las llamadas de pago",
       _el_cupo_cuadra_con_las_llamadas_de_pago)
prueba("la practica de voz pide codigo",
       lambda: _con_puerta(
           lambda: "entres con tu perfil" in str(ui._practicar("x.wav", "hello there")[1])))
prueba("entrar con una clave mala no abre nada",
       lambda: _con_puerta(lambda: "No he podido entrar" in ui._entrar("jefe", "INVENTADO")))
prueba("entrar con el perfil bueno lo dice",
       lambda: _con_puerta(lambda: "jefe" in ui._entrar("jefe", "LLAVE-A")))
prueba("un usuario que no existe no entra",
       lambda: _con_puerta(lambda: "No he podido entrar" in ui._entrar("nadie", "LLAVE-A")))
prueba("el usuario no distingue mayusculas y la clave si",
       lambda: _con_puerta(lambda: "jefe" in ui._entrar("JEFE", "LLAVE-A")
                           and "No he podido" in ui._entrar("jefe", "llave-a")))
def _salir_olvida_de_verdad():
    """No basta con que diga "Has salido": tiene que olvidar la sesion.

    La version anterior solo miraba el mensaje, asi que un `_salir` que no
    borrara nada -probado quitandole el `pop`- seguia pasando en verde. En un
    ordenador compartido eso significa que el siguiente en sentarse hereda el
    perfil y el cupo del anterior.
    """
    def dentro():
        assert "jefe" in ui._entrar("jefe", "LLAVE-A"), "no pudo entrar"
        assert ui._codigo_de(None) is not None, "no recordo el perfil"
        salida = ui._salir()
        assert "Has salido" in salida, salida
        assert ui._codigo_de(None) is None, "dijo que salio y NO olvido nada"
        return "sale, y la sesion queda sin perfil"
    return _con_puerta(dentro)


prueba("salir olvida el perfil", _salir_olvida_de_verdad)

def _apuntar_en_ruta_imposible():
    r = _con_codigos(
        lambda: cuentas_mod.apuntar(pathlib.Path("Z:/no/existe"),
                                    cuentas_mod.validar("jefe:LLAVE-A")))
    assert r is None, r
    return "no revienta y no devuelve nada"


prueba("apuntar en una ruta imposible no revienta", _apuntar_en_ruta_imposible)


titulo("Una sola dificultad por libro")

# La app y el precalculo masivo daban numeros distintos para el mismo libro:
# una hacia la media de las medias de capitulo y el otro la media de todas las
# ventanas. Con capitulos de tamano desigual no coinciden.
def _agregacion_por_ventanas():
    import random
    r = random.Random(42)
    malas = []
    for _ in range(500):
        filas, todas = [], []
        for _ in range(r.randint(1, 40)):
            n = r.randint(1, 60)
            vs = [r.uniform(0, 2) for _ in range(n)]
            todas.extend(vs)
            filas.append({"dificultad": sum(vs) / n, "ventanas": n})
        esperado = sum(todas) / len(todas)
        obtenido = ui.ficha.dificultad_global(filas)
        if abs(obtenido - esperado) > 1e-9:
            malas.append(f"{obtenido!r} != {esperado!r}")
    assert not malas, malas[:3]
    return "500 libros sinteticos, identica a la media de ventanas"


prueba("la dificultad global es la media de todas las ventanas",
       _agregacion_por_ventanas)
def _caso_de_la_auditoria():
    # Un capitulo de una ventana a 0 y otro de nueve a 2. Ponderando por
    # ventanas son 1,8; haciendo la media de las medias, 1,0. Si alguien
    # volviera a la media de medias, esta prueba TIENE que suspender, y
    # sin el assert no suspendia: devolvia 1,0 tan tranquila.
    v = ui.ficha.dificultad_global([{"dificultad": 0.0, "ventanas": 1},
                                    {"dificultad": 2.0, "ventanas": 9}])
    assert abs(v - 1.8) < 1e-9, f"esperaba 1.8 y salio {v}"
    return v


prueba("el caso que destapo la auditoria", _caso_de_la_auditoria)
prueba("un libro sin ventanas no revienta",
       lambda: ui.ficha.dificultad_global([]))


titulo("Archivos propios mal formados")
# Los escribe la app, no un usuario, asi que son bordes. Pero la cabecera de
# `ui.py` promete que NINGUN manejador levanta, y estos cuatro lo hacian. El
# de `_reanudar` es el peor: corre en `demo.load`, o sea que la pagina entera
# arrancaba con error para ese lector hasta que borrara el archivo a mano.


def _sesion_que_no_es_un_objeto():
    """`sesion.json` con JSON valido que no sea un diccionario."""
    ruta = pathlib.Path(ui._ruta_sesion(None))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    guardado = ruta.read_text(encoding="utf-8") if ruta.exists() else None
    try:
        for basura in ("[]", '"hola"', "3", "null"):
            ruta.write_text(basura, encoding="utf-8")
            list(ui._reanudar())          # generadora: hay que iterarla
        return "cuatro formas de basura y ninguna levanta"
    finally:
        if guardado is None:
            ruta.unlink(missing_ok=True)
        else:
            ruta.write_text(guardado, encoding="utf-8")


prueba("sesion.json que no es un objeto", _sesion_que_no_es_un_objeto)


def _perfil_con_nivel_no_numerico():
    """Un `perfil.json` con `nivel: "abc"` se construia sin queja y reventaba
    despues, en la aritmetica de quien lo usara."""
    ruta = pathlib.Path(ui._archivo_lector("perfil.json", None))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    guardado = ruta.read_text(encoding="utf-8") if ruta.exists() else None
    try:
        import json as _json
        import perfil as perfil_mod
        ruta.write_text(_json.dumps({"nivel": "abc", "banda": "basico",
                                     "origen": "cuestionario", "creado": "",
                                     "nombre": ""}), encoding="utf-8")
        assert perfil_mod.cargar(str(ruta)) is None, "deberia darlo por corrupto"
        ui._perfil_inicial()
        return "se da por corrupto y no revienta"
    finally:
        if guardado is None:
            ruta.unlink(missing_ok=True)
        else:
            ruta.write_text(guardado, encoding="utf-8")


prueba("perfil con nivel no numerico", _perfil_con_nivel_no_numerico)


def _analisis_y_sinopsis_mal_formados():
    """Los otros dos archivos que escribe la app y que si levantaban.

    Un `analisis/*.json` con filas sin `dificultad` daba KeyError, y una
    sinopsis que fuera `[]`, `"hola"` o llevara un numero donde se espera texto
    daba AttributeError. Es el mismo fallo de `sesion.json` y `perfil.json` en
    los dos archivos que quedaban: JSON valido, forma distinta.
    """
    import json as _json
    ruta_a = pathlib.Path(ui._ruta_analisis(libro_ok, "completo"))
    ruta_s = pathlib.Path(ui.RUTA_ANALISIS) / f"{ui._clave_libro(libro_ok)}-sinopsis.json"
    ruta_a.parent.mkdir(parents=True, exist_ok=True)
    guardados = [(r, r.read_text(encoding="utf-8") if r.exists() else None)
                 for r in (ruta_a, ruta_s)]
    basura_analisis = ['[]', '"hola"', '{"filas": 3}',
                       '{"filas": [{"capitulo": 1}]}', '{"filas": ["x"]}']
    basura_sinopsis = ['[]', '"hola"', '{"de_que_trata": 5}', 'null']
    try:
        for b in basura_analisis:
            ruta_a.write_text(b, encoding="utf-8")
            list(ui._analizar_libro(libro_ok, "completo"))
        ruta_a.unlink(missing_ok=True)
        for b in basura_sinopsis:
            ruta_s.write_text(b, encoding="utf-8")
            list(ui._de_que_trata(libro_ok))
        return (f"{len(basura_analisis)} analisis y {len(basura_sinopsis)} "
                "sinopsis mal formados, ninguno levanta")
    finally:
        for r, guardado in guardados:
            if guardado is None:
                r.unlink(missing_ok=True)
            else:
                r.write_text(guardado, encoding="utf-8")


prueba("analisis y sinopsis mal formados", _analisis_y_sinopsis_mal_formados)

prueba("mover con un indice que no es numero",
       lambda: (ui._mover(libro_ok, "abc", 1), ui._mover(libro_ok, None, 1))
       and "no revienta")
def _el_aviso_de_tope_dice_los_minutos_que_faltan():
    """Decia siempre "60 minutos", que es la ventana entera y casi nunca lo
    que falta: quien agoto el cupo hace cincuenta y ocho minutos leia que
    tenia que esperar una hora mas."""
    pet = _Pet(ip="10.9.9.9")
    assert ui._minutos_para_la_siguiente("lexico", pet) == 0, "sin gasto, 0"
    ui._dentro_del_limite(pet, "lexico", 1)
    m = ui._minutos_para_la_siguiente("lexico", pet)
    assert m == 60, f"recien gastado deberian faltar 60, no {m}"
    # Y con una marca vieja, lo que de verdad falta.
    with ui._CANDADO_GASTO:
        ui._gasto[f"lexico:{ui._ip(pet)}"] = [time.time() - 58 * 60]
    m = ui._minutos_para_la_siguiente("lexico", pet)
    assert m == 2, f"tras 58 minutos deberian faltar 2, no {m}"
    return "dice los minutos que faltan, no siempre 60"


prueba("el aviso de tope dice los minutos que faltan",
       _el_aviso_de_tope_dice_los_minutos_que_faltan)

def _la_casilla_vacia_no_ensena_un_error_de_python():
    """`gr.Number` vacio manda None, y salia "int() argument must be...".

    La version anterior pasaba `p=None`, y con eso `_recomendar` vuelve en su
    primer guardia y NUNCA llega al `int(n)`: probaba el guardia, no el
    arreglo. Hay que darle un perfil de verdad. Y `_buscar` tiene el mismo
    `int(n)` y no lo probaba nadie.
    """
    p = perfil_mod.Perfil(nivel=1.0, banda="intermedio",
                          origen="cuestionario", creado="", nombre="Ana")
    malos = []
    for etiqueta, salida in (
            ("_recomendar", str(ui._recomendar(p, None))),
            ("_buscar", str(ui._buscar(p, "aventuras", False, None)))):
        if "int()" in salida:
            malos.append(f"{etiqueta}: {salida[:90]}")
    assert not malos, malos
    return "con la casilla vacia, los dos responden sin error de Python"


prueba("cuantos libros vacio no ensena un error de Python",
       _la_casilla_vacia_no_ensena_un_error_de_python)


def _el_rango_anunciado_es_el_filtrado():
    """El rotulo tiene que decir el rango que se USO para filtrar.

    Anunciaba `rango_recomendado` -nivel-0,10 a nivel+0,15- mientras
    `por_nivel` filtraba con holgura simetrica de 0,25: con nivel 1,00 decia
    "entre 0.90 y 1.15" y listaba libros de 0,80 y 1,20. Volver al rango viejo
    pasaba las pruebas, asi que la correccion no estaba protegida.
    """
    p = perfil_mod.Perfil(nivel=1.0, banda="intermedio",
                          origen="cuestionario", creado="", nombre="Ana")
    texto = str(ui._recomendar(p, 5))
    h = ui.HOLGURA_POR_NIVEL
    lo, hi = f"{max(0.0, p.nivel - h):.2f}", f"{min(2.0, p.nivel + h):.2f}"
    assert lo in texto and hi in texto,         f"esperaba anunciar {lo}-{hi} y dijo: {texto[:130]}"
    return f"anuncia {lo}-{hi}, que es la holgura con la que filtra"


prueba("el rango anunciado es el que se filtra", _el_rango_anunciado_es_el_filtrado)


# --- El orden de los capitulos y el filtro de prosa continua --------------
#
# Dos fallos que Miguel encontro usando la aplicacion desplegada, los dos con
# *The Memoirs of Sherlock Holmes*, y los dos invisibles para las 250 pruebas
# que ya habia. Van juntos porque son el mismo lector abriendo el mismo libro.

titulo("Orden de los capitulos y filtro de prosa")

import scoring as scoring_mod  # noqa: E402

# Los nombres reales del libro con el que se reprodujo el fallo. Se conservan
# porque el sintoma se lee mejor asi: "XII. The Final Problem" es donde muere
# Holmes, y salia como capitulo 5 de 13.
CAPS_MEMORIAS = [
    "I. Silver Blaze", "II. The Cardboard Box", "III. The Yellow Face",
    "IV. The Stockbroker's Clerk", "V. The Gloria Scott",
    "VI. The Musgrave Ritual", "VII. The Reigate Squires",
    "VIII. The Crooked Man", "IX. The Resident Patient",
    "X. The Greek Interpreter", "XI. The Naval Treaty",
    "XII. The Final Problem",
]

_RELLENO = ("He said nothing for a long while, and the train ran on through "
            "the brown moor towards the west, with the rain beginning to "
            "streak the glass of the window beside us. ") * 4


def _epub(nombre, archivos, spine, con_spine=True, id_antes_de_href=False):
    """Escribe un epub minimo y devuelve su ruta.

    `archivos` es [(nombre_interno, titulo_del_capitulo)] y `spine` la lista de
    ids en orden de lectura. Con `id_antes_de_href=False` el manifiesto se
    escribe **como lo escribe Project Gutenberg**: `href` primero.
    """
    ruta = TMP / nombre
    manifiesto, cuerpos = [], []
    for i, (interno, tit) in enumerate(archivos):
        idx = f"item{i}"
        if id_antes_de_href:
            manifiesto.append(
                f'<item id="{idx}" href="{interno}" '
                f'media-type="application/xhtml+xml"/>')
        else:
            manifiesto.append(
                f'<item href="{interno}" id="{idx}" '
                f'media-type="application/xhtml+xml"/>')
        cuerpos.append((interno,
                        f"<html><body><h1>{tit}</h1><p>{_RELLENO}</p>"
                        f"</body></html>"))
    itemrefs = "".join(f'<itemref idref="{s}" linear="yes"/>' for s in spine)
    opf = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:title>The Memoirs of Sherlock Holmes</dc:title>'
        '<dc:creator>Arthur Conan Doyle</dc:creator></metadata>'
        f'<manifest>{"".join(manifiesto)}</manifest>'
        + (f"<spine>{itemrefs}</spine>" if con_spine else "<spine></spine>")
        + "</package>")
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("OEBPS/content.opf", opf)
        for interno, html in cuerpos:
            z.writestr(f"OEBPS/{interno}", html)
    return str(ruta)


def _el_orden_de_los_capitulos_es_el_del_spine():
    """El indice salia 1, 10, 11, 12, 2, 3... y reventaba el final del libro.

    En *The Memoirs of Sherlock Holmes* el desplegable ponia "XII. The Final
    Problem" -donde muere Holmes- como capitulo 5 de 13: quien pulsara
    "Siguiente" tres veces se comia el desenlace.

    La causa no era un `sorted()` cualquiera, sino que el `spine` **no se podia
    resolver**. El manifiesto se leia con

        <item\\s[^>]*id="..."[^>]*href="..."

    que exige `id` ANTES que `href`, y Gutenberg los escribe al reves. Con el
    diccionario vacio, `_leer_epub` caia al respaldo alfabetico.

    Por eso el epub de esta prueba se escribe con los atributos en el orden de
    Gutenberg **y** con nombres de archivo cuyo orden alfabetico es el
    CONTRARIO al de lectura: asi ninguna ordenacion por nombre -ni la
    alfabetica ni la natural- puede dar el resultado correcto por casualidad.
    Solo lo da respetar el spine.
    """
    n = len(CAPS_MEMORIAS)
    archivos = [(f"pg{n - i}.xhtml", t) for i, t in enumerate(CAPS_MEMORIAS)]
    ruta = _epub("memorias.epub", archivos, [f"item{i}" for i in range(n)])
    libro = reader.cargar(ruta)
    titulos = [c.titulo for c in libro.capitulos]
    assert titulos == CAPS_MEMORIAS, f"orden roto: {titulos[:6]}"
    assert titulos[-1] == "XII. The Final Problem", (
        f"el final del libro no va el ultimo, va: {titulos[-1]}")
    assert "Final Problem" not in titulos[4], (
        "el desenlace sale como capitulo 5: es el fallo original")
    return f"{n} capitulos en el orden del spine, el desenlace el ultimo"


prueba("el orden de los capitulos es el del spine",
       _el_orden_de_los_capitulos_es_el_del_spine)


def _sin_spine_los_capitulos_van_en_orden_natural():
    """El respaldo ordenaba cadenas: pg1, pg10, pg11, pg12, pg2, pg3...

    Se usa solo cuando el epub no trae un spine legible, pero cuando se usa
    tiene que contar como cuenta una persona.
    """
    n = len(CAPS_MEMORIAS)
    archivos = [(f"pg{i + 1}.xhtml", t) for i, t in enumerate(CAPS_MEMORIAS)]
    ruta = _epub("sin_spine.epub", archivos, [], con_spine=False)
    titulos = [c.titulo for c in reader.cargar(ruta).capitulos]
    assert titulos == CAPS_MEMORIAS, f"orden de texto, no natural: {titulos[:6]}"
    return f"pg9 antes que pg10 en los {n} archivos del respaldo"


prueba("sin spine, los capitulos van en orden natural",
       _sin_spine_los_capitulos_van_en_orden_natural)


# Un capitulo de novela dialogada con una lista numerada DENTRO, que es la
# forma exacta de "I. Silver Blaze": la tarjeta de la carrera, seis caballos,
# en medio de 9.577 palabras de prosa. Medido en el capitulo real: 6 lineas de
# vineta sobre 792, el 0,8 %.
CAPITULO_DIALOGADO = "\n".join([
    "I. Silver Blaze",
    "“I am afraid, Watson, that I shall have to go,” said Holmes.",
    "“To go! Where to?”",
    "“To Dartmoor; to King’s Pyland.”",
    "I was not surprised. Indeed, my only wonder was that he had not already",
    "been connected with this extraordinary case, which was the one topic of",
    "conversation through the length and breadth of England.",
    "“I should be happy to go down with you, if I am not in the way,”",
    "said I.",
    "“My dear Watson, you would confer a great favour upon me by coming.”",
    "“And what have you learned so far?” I asked him.",
    "“That the horse is gone and that the trainer is dead,” he answered.",
    "“The grass was dry and the ground was hard, and the tracks told little.”",
    "“Surely the stable-boy saw something,” I objected.",
    "“He saw a man, or he says that he saw a man. It was a dark night.”",
    "“And the knife?”",
    "“The knife is the strangest thing of all,” said Holmes.",
    "“It was a cataract knife, and a man takes no such weapon to a moor.”",
    "“Then what do you make of it?”",
    "“That the trainer took it because it was the first thing he found.”",
    "The papers of the week had printed the whole card of the coming race, and",
    "Holmes read it aloud to me while the train ran on towards the west.",
    "1. Mr. Heath Newton’s The Negro (red cap, cinnamon jacket).",
    "2. Colonel Wardlaw’s Pugilist (pink cap, blue and black jacket).",
    "3. Lord Backwater’s Desborough (yellow cap and sleeves).",
    "4. Colonel Ross’s Silver Blaze (black cap, red jacket).",
    "5. Duke of Balmoral’s Iris (yellow and black stripes).",
    "6. Lord Singleford’s Rasper (purple cap, black sleeves).",
    "“Six horses,” said I, “and one is missing on the eve of the race.”",
    "“Precisely. And the favourite of the six, which is the whole matter.”",
    "“You think that the horse is still alive, then?”",
    "“I think that a horse of that value is worth far more alive.”",
    "“And the dog did nothing in the night-time,” I remarked at last.",
    "“That was the curious incident,” said Sherlock Holmes.",
    "We sat in silence a long while, and the moor went by the window, brown",
    "and empty under a sky that promised rain before the evening came.",
    "The inspector met us at the station with a face that told the story",
    "before he opened his mouth, and we drove to the stables in a carriage.",
    "“You have formed a theory, then?” he asked, when we had gone a mile.",
    "“Several, and I shall know within the hour which of them is the true one.”",
    "“The horse was found upon the moor at daybreak,” said the inspector.",
    "“Then the matter is finished, and only the reason for it remains.”",
])


def _un_capitulo_dialogado_con_una_lista_dentro_se_puntua():
    """"¿Como de dificil es este capitulo?" sobre "I. Silver Blaze" -9.577
    palabras de Conan Doyle- contestaba "Parece una lista, un menu o una
    tabla". El fallo central del producto, muerto en el libro mas leido.

    Y la causa NO era la regla de lineas cortas, que es lo que parecia: medido
    sobre 589 capitulos de los diez epub cacheados, esa regla no rechazo NI UNO
    -Silver Blaze tiene el 8,8 % de lineas cortas, muy por debajo del 35 %-.
    Los 52 falsos rechazos los causaba `con_vineta >= 2`, un recuento
    ABSOLUTO: la tarjeta de la carrera con sus seis caballos, los separadores
    de escena `*  *  *` de Alicia, las llamadas a nota al pie de Guerra y Paz.

    La asercion tiene que ser que el capitulo PASA. Comprobar que la lista se
    detecta, o que el mensaje es legible, seguiria siendo cierto con el fallo
    dentro.
    """
    ok, motivo = scoring_mod.continuous_prose(CAPITULO_DIALOGADO)
    assert ok, f"un capitulo de novela dialogada se rechaza por '{motivo}'"
    lineas = [l.strip() for l in CAPITULO_DIALOGADO.splitlines() if l.strip()]
    vinetas = sum(bool(scoring_mod.BULLET_RE.match(l)) for l in lineas)
    assert vinetas >= 2, (
        "la prueba ha dejado de tener la lista dentro y ya no prueba nada")
    return f"pasa con {vinetas} lineas de lista en {len(lineas)}"


prueba("un capitulo dialogado con una lista dentro se puntua",
       _un_capitulo_dialogado_con_una_lista_dentro_se_puntua)


def _la_ficha_y_el_medidor_no_se_contradicen():
    """Los dos paneles de la MISMA pantalla decian cosas incompatibles.

    La ficha: "Dialogo: 40 % de las frases llevan voz - muy conversado". El
    medidor, del mismo capitulo: "Parece una lista, un menu o una tabla".
    Si `ficha` dice que un texto es conversacion, `scoring` no puede decir que
    es un menu.
    """
    libro = reader.Libro("The Memoirs of Sherlock Holmes", "Arthur Conan Doyle",
                         [reader.Capitulo("I. Silver Blaze", CAPITULO_DIALOGADO)])
    car = ficha_mod.caracteristicas(libro)
    ok, motivo = scoring_mod.continuous_prose(CAPITULO_DIALOGADO)
    assert car.dialogo >= 0.35, (
        f"la muestra ha dejado de ser dialogada ({car.dialogo:.0%})")
    assert "conversado" in car.forma_del_dialogo, car.forma_del_dialogo
    assert ok, (f"la ficha dice '{car.forma_del_dialogo}' y el medidor "
                f"lo rechaza por '{motivo}'")
    return f"ficha {car.dialogo:.0%} de dialogo y el medidor lo acepta"


prueba("la ficha y el medidor no se contradicen",
       _la_ficha_y_el_medidor_no_se_contradicen)


# Los cuatro maquetados que el filtro SI tiene que rechazar. Aflojar la regla
# de vinetas sin esto es abrirle la puerta a lo que el filtro existe para
# parar: una carta de menu de 432 palabras ya se puntuo una vez como prosa.
_MENU = "\n".join(["THE OLD MILL: DINNER MENU"] + [
    "Tomato soup with basil", "Garlic bread with cheese", "Prawn cocktail",
    "Mixed green olives", "Goat cheese salad", "Onion soup", "Smoked salmon",
    "Chicken liver pate", "Roast chicken and potatoes", "Grilled salmon",
    "Beef lasagne", "Vegetable curry with rice", "Steak and chips",
    "Mushroom risotto", "Fish and chips", "Pork chop with mash",
    "Duck with orange sauce", "Lamb shank", "Sausages and mash",
    "Cheese ravioli", "Hand cut chips", "Green side salad",
    "Steamed vegetables", "Onion rings", "Buttered rice", "Garlic potatoes",
    "Chocolate cake", "Apple pie and cream", "Vanilla ice cream",
    "Cheesecake of the day", "Fresh fruit salad", "Lemon tart",
    "Still mineral water", "Sparkling mineral water", "Orange juice",
    "Apple juice", "Black coffee", "Tea with milk", "House red wine",
    "House white wine", "Bottled beer", "Home made lemonade",
    "Service is not included in any of the prices shown above.",
    "The kitchen closes at ten in the evening from Monday to Friday.",
    "Please tell your waiter about any allergy before you order.",
    "Booking a table is recommended at the weekend and on holidays.",
])

_INDICE = "\n".join([
    "CONTENTS OF THIS VOLUME",
    "I. The Rabbit Hole", "II. The Pool of Tears", "III. A Long Tale",
    "IV. A Little Bill", "V. The Caterpillar", "VI. Pig and Pepper",
    "VII. A Mad Tea Party", "VIII. The Croquet Ground", "IX. The Mock Turtle",
    "X. The Lobster Quadrille", "XI. Who Stole the Tarts",
    "XII. The Evidence of Alice", "LIST OF THE ILLUSTRATIONS",
    "The White Rabbit", "The Pool of Tears", "The Caucus Race",
    "The Little Bill", "The Caterpillar", "The Duchess", "The Mad Hatter",
    "The Croquet Ground", "The Mock Turtle", "The Lobster",
    "The Knave of Hearts", "Alice in the court", "NOTES AND APPENDIX",
    "A note on the text", "A note on the plates", "Bibliography",
    "Index of the names", "Index of first lines", "Acknowledgements",
    "About the editor", "Other titles", "Reading group questions",
    "A short chronology", "Further reading", "A note on the type",
    "The page numbers of this edition are printed beside every entry.",
    "The illustrations are bound together after the twelfth chapter.",
    "Roman numerals are used for the chapters and arabic for the plates.",
    "The index of names was prepared by the editor of this edition.",
])

_TABLA = "\n".join(["Country   Capital   People   Area   Money"] + [
    f"{p}   {c}   {hab}   {km}   {mon}" for p, c, hab, km, mon in [
        ("France", "Paris", 68, 551, "Euro"), ("Germany", "Berlin", 83, 357, "Euro"),
        ("Spain", "Madrid", 47, 505, "Euro"), ("Italy", "Rome", 59, 301, "Euro"),
        ("Portugal", "Lisbon", 10, 92, "Euro"), ("Poland", "Warsaw", 38, 312, "Zloty"),
        ("Sweden", "Stockholm", 10, 450, "Krona"), ("Norway", "Oslo", 5, 385, "Krone"),
        ("Denmark", "Copenhagen", 5, 42, "Krone"), ("Finland", "Helsinki", 5, 338, "Euro"),
        ("Ireland", "Dublin", 5, 70, "Euro"), ("Austria", "Vienna", 9, 83, "Euro"),
        ("Belgium", "Brussels", 11, 30, "Euro"), ("Greece", "Athens", 10, 131, "Euro"),
        ("Hungary", "Budapest", 9, 93, "Forint"), ("Romania", "Bucharest", 19, 238, "Leu"),
        ("Bulgaria", "Sofia", 6, 110, "Lev"), ("Croatia", "Zagreb", 3, 56, "Euro"),
        ("Slovakia", "Bratislava", 5, 49, "Euro"), ("Slovenia", "Ljubljana", 2, 20, "Euro"),
        ("Estonia", "Tallinn", 1, 45, "Euro"), ("Latvia", "Riga", 1, 64, "Euro"),
        ("Lithuania", "Vilnius", 2, 65, "Euro"), ("Czechia", "Prague", 10, 78, "Koruna"),
        ("Netherlands", "Amsterdam", 17, 41, "Euro"), ("Iceland", "Reykjavik", 3, 10, "Krona"),
        ("Malta", "Valletta", 5, 31, "Euro"), ("Cyprus", "Nicosia", 1, 92, "Euro"),
        ("Switzerland", "Bern", 8, 41, "Franc"), ("Serbia", "Belgrade", 6, 88, "Dinar"),
        ("Albania", "Tirana", 2, 28, "Lek"), ("Ukraine", "Kyiv", 41, 603, "Hryvnia"),
        ("Moldova", "Chisinau", 2, 33, "Leu"), ("Georgia", "Tbilisi", 3, 69, "Lari"),
        ("Armenia", "Yerevan", 2, 29, "Dram"), ("Turkey", "Ankara", 85, 783, "Lira"),
        ("Belarus", "Minsk", 9, 207, "Rouble"), ("Monaco", "Monaco", 1, 2, "Euro"),
        ("Andorra", "Andorra", 1, 4, "Euro"), ("Liechtenstein", "Vaduz", 1, 1, "Franc"),
    ]] + [
    "Source: the national statistics office of each country listed above.",
    "Figures are rounded to the nearest hundred thousand inhabitants.",
    "The area of each country is given in thousands of square kilometres.",
    "The currency column shows the legal tender in use during this year.",
])

_LISTA = "\n".join([
    "Before you travel abroad, check every one of the following points.",
] + [f"- {x}" for x in [
    "Passport valid for at least six months after the date of your return",
    "Visa or travel authorisation for the country that you are visiting",
    "Travel insurance that covers medical costs and cancellation of the trip",
    "Vaccination certificates if the country you visit requires them of you",
    "A printed copy of the confirmation of every booking you have made",
    "The address and the telephone number of the hotel where you will stay",
    "Enough local currency in cash for the first day of the whole trip",
    "A charger and an adaptor that fit the sockets used in that country",
    "Any medicine that you take regularly, kept in its original box",
    "A photocopy of your passport, kept apart from the passport itself",
    "The emergency telephone number of your travel insurance company",
    "Your driving licence if you are planning to hire a car when you arrive",
    "A list of the numbers of the cards that you are carrying with you",
    "The address of the nearest consulate of your country in that city",
]] + [
    "The list above covers the documents that travellers forget most often.",
    "Keep the copies in a separate bag from the original documents.",
    "If you lose a document, contact the nearest consulate straight away.",
    "Most problems are solved in a day if you carry the copies with you.",
])


def _el_filtro_sigue_rechazando_menus_indices_y_tablas():
    """La otra direccion del arreglo, que es la que se olvida.

    Los cuatro tienen mas de 150 palabras y mas de cuatro frases a proposito:
    si no, los rechazaria la regla de "corto" y esta prueba pasaria sin llegar
    nunca a la regla de maquetado. Por eso se exige el motivo exacto.
    """
    malos = []
    for nombre, texto in (("menu", _MENU), ("indice", _INDICE),
                          ("tabla", _TABLA), ("lista con vinetas", _LISTA)):
        palabras = len(scoring_mod.words(texto))
        if palabras < scoring_mod.MIN_WORDS:
            malos.append(f"{nombre}: solo {palabras} palabras, lo tira 'corto'")
            continue
        ok, motivo = scoring_mod.continuous_prose(texto)
        if ok or motivo != "maquetado_de_lista":
            malos.append(f"{nombre}: ok={ok} motivo={motivo}")
    assert not malos, malos
    return "menu, indice, tabla y lista rechazados por maquetado"


prueba("el filtro sigue rechazando menus, indices y tablas",
       _el_filtro_sigue_rechazando_menus_indices_y_tablas)



# --- Lo que un banco de mutantes demostro que nadie protegia ---------------
#
# La auditoria 13 aplico 50 mutantes y 15 sobrevivieron. Varios deshacian
# correcciones que auditorias anteriores dieron por cerradas: cobrar sin clave,
# el cubo por hora de una IP gastado por visitantes que no pueden pagar, la
# licencia de Gutenberg sin quitar antes de decidir si un capitulo ES licencia,
# el tope sin tope negado, la ventana de una hora, el minimo de palabras para
# puntuar, el recorte de lo que viaja a OpenAI y la apertura en la portadilla.
#
# Una prueba por fila, y cada una comprobada CONTRA SU MUTANTE: se rompe la
# linea a proposito y se exige que falle esta prueba y no otra.

titulo("Mutantes que sobrevivian")


def _sin_clave_no_se_culpa_al_cupo():
    """Sin clave, el aviso tiene que hablar de la clave. Y no cobrar.

    `_consultar` mira `config.falta()` ANTES de pasar por la puerta de pago,
    justamente para no gastar un uso del cupo cuando no puede salir ninguna
    peticion. Quitar esa comprobacion -el mutante- hace que un lector con el
    cupo agotado lea "se te acabo el cupo" en un servidor que ni siquiera
    tiene clave: se le echa la culpa al cupo de algo que es del servidor.
    """
    class _P:
        session_hash = "s-sinclave"
        headers = {}
        client = type("X", (), {"host": "10.9.9.9"})()

    pet = _P()
    viejo_falta = config_mod.falta
    viejo_cuentas = os.environ.get("LITERALEVEL_CUENTAS")
    viejo_consultor = ui.consultor
    from lexicon import ResultadoLexico

    def doble():
        class C:
            @staticmethod
            def consultar(*a, **k):
                return ResultadoLexico(
                    "hi", "hi", "hi", "hi", "INTJ", "interjection", "A greeting.",
                    [], 0.8, 2, None, None, None, None, False, None, None, None,
                    None, "basico", 5.0, False,
                    ["sin OPENAI_API_KEY: no hay explicacion contextual"], 0)
        return C()

    try:
        config_mod.falta = lambda: ["OPENAI_API_KEY"]
        os.environ["LITERALEVEL_CUENTAS"] = "ana:CLAVE-N:1"
        ui._CODIGO_SESION.clear()
        ui._CODIGO_SESION[ui._sesion_de(pet)] = "ana:CLAVE-N"
        ui.consultor = doble
        # Se le agota el cupo a mano: uno de uno.
        cuentas_mod.consumir(ui.BASE_DATOS_LECTOR, "ana:CLAVE-N")
        antes = cuentas_mod.gastado(ui.BASE_DATOS_LECTOR, "ana")
        salida = ""
        for tramo in ui._consultar(None, None, None, "hello", "Hello there.",
                                   "es", pet):
            salida = str(tramo)
        despues = cuentas_mod.gastado(ui.BASE_DATOS_LECTOR, "ana")
        assert "cupo" not in salida.lower(), \
            f"culpa al cupo sin haber clave: {salida[:160]}"
        assert despues == antes, f"cobro un uso sin clave: {antes} -> {despues}"
    finally:
        config_mod.falta = viejo_falta
        ui.consultor = viejo_consultor
        ui._CODIGO_SESION.clear()
        if viejo_cuentas is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo_cuentas
    return "sin clave: ni cobra ni le echa la culpa al cupo"


prueba("el cupo no baja sin clave de OpenAI", _sin_clave_no_se_culpa_al_cupo)


def _el_cubo_por_hora_solo_cuenta_lo_que_cuesta():
    """El cubo por hora es de la IP ENTERA, y frena el gasto, no el uso.

    Un visitante sin perfil no puede pagar nada, asi que sus pulsaciones no
    pueden gastar fichas del cubo. Sin la guarda `va_a_costar`, seis clics de
    alguien que no ha entrado dejaban sin sinopsis a quien si habia entrado
    desde la misma IP -en un Space, todos comparten proxy-.
    """
    class _P:
        session_hash = "s-cubo"
        headers = {}
        client = type("X", (), {"host": "10.7.7.7"})()

    pet = _P()
    viejo_cuentas = os.environ.get("LITERALEVEL_CUENTAS")
    viejo_falta = config_mod.falta
    try:
        # Puerta cerrada: hay perfiles declarados y esta sesion no entro.
        os.environ["LITERALEVEL_CUENTAS"] = "jefe:LLAVE-A:0"
        config_mod.falta = lambda: []
        ui._CODIGO_SESION.clear()
        with ui._CANDADO_GASTO:
            ui._gasto.clear()
        for _ in range(3):
            list(ui._de_que_trata(libro_ok, pet))
            list(ui._consultar(None, None, None, "hello", "Hello there.", "es", pet))
        with ui._CANDADO_GASTO:
            usados = {k: len(v) for k, v in ui._gasto.items() if v}
        assert not usados, f"gasto fichas del cubo sin poder pagar: {usados}"
    finally:
        config_mod.falta = viejo_falta
        ui._CODIGO_SESION.clear()
        with ui._CANDADO_GASTO:
            ui._gasto.clear()
        if viejo_cuentas is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo_cuentas
    return "quien no puede pagar no gasta fichas de la IP"


prueba("el cubo por hora solo cuenta lo que cuesta dinero",
       _el_cubo_por_hora_solo_cuenta_lo_que_cuesta)


def _un_perfil_sin_tope_puede_gastar():
    """`tope = 0` es SIN LIMITE, no "cero usos".

    Lo dice `DESPLIEGUE.md` y lo usa el perfil del profesor. Las pruebas del
    `jefe:0` solo miraban `queda()` y `gastado()`, asi que invertir la
    condicion en `permite` y en `consumir` -bloquear justo al que no tiene
    limite- pasaba la suite entera.
    """
    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    try:
        os.environ["LITERALEVEL_CUENTAS"] = "jefe:LLAVE-A:0,becario:LLAVE-B:2"
        puede, motivo = cuentas_mod.permite(ui.BASE_DATOS_LECTOR, "jefe:LLAVE-A")
        assert puede, f"el perfil sin tope no puede usar OpenAI: {motivo!r}"
        for i in range(3):
            ok, motivo = cuentas_mod.consumir(ui.BASE_DATOS_LECTOR, "jefe:LLAVE-A")
            assert ok, f"consumir #{i + 1} negado a un perfil sin tope: {motivo!r}"
        assert cuentas_mod.queda(
            cuentas_mod.validar("jefe:LLAVE-A")
            and ui.BASE_DATOS_LECTOR, cuentas_mod.validar("jefe:LLAVE-A")) is None
    finally:
        if viejo is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo
    return "tope 0 = sin limite, en permite y en consumir"


prueba("un perfil sin tope puede gastar", _un_perfil_sin_tope_puede_gastar)


def _el_tope_por_hora_dura_una_hora():
    """Una marca de hace media hora SIGUE contando.

    Nadie probaba la duracion de la ventana, solo el recuento, asi que bajarla
    de 3.600 s a 1 s pasaba la suite: el tope por hora duraba un segundo y
    cualquiera podia gastar sin freno esperando entre clic y clic.
    """
    class _P:
        headers = {}
        client = type("X", (), {"host": "10.3.3.3"})()

    pet = _P()
    clave = f"prueba_ventana:{ui._ip(pet)}"
    try:
        with ui._CANDADO_GASTO:
            ui._gasto[clave] = [time.time() - 1800.0, time.time() - 60.0]
        assert not ui._dentro_del_limite(pet, "prueba_ventana", 2), \
            "dos marcas de esta hora no cuentan: la ventana no dura una hora"
        with ui._CANDADO_GASTO:
            ui._gasto[clave] = [time.time() - 7200.0]
        assert ui._dentro_del_limite(pet, "prueba_ventana", 1), \
            "una marca de hace dos horas sigue contando: la ventana no caduca"
    finally:
        with ui._CANDADO_GASTO:
            ui._gasto.pop(clave, None)
    return "la ventana son 3.600 s: cuenta lo de esta hora y olvida lo de antes"


prueba("el tope por hora dura una hora", _el_tope_por_hora_dura_una_hora)


def _un_texto_de_veinte_palabras_no_se_puntua():
    """`MIN_WORDS` es el suelo del modelo, y hay que decir POR QUE se rechaza.

    El "muy corto" de `tests_smoke` caia por `pocas_frases`, asi que bajar
    MIN_WORDS a 1 no rompia nada. Aqui el texto tiene cinco frases de sobra y
    solo puede caer por corto.
    """
    corto = ("The dog ran fast. The cat slept well. The bird sang loud. "
             "The boy laughed hard. The girl read on.")
    n = len(scoring_mod.words(corto))
    ok, motivo = scoring_mod.continuous_prose(corto)
    assert not ok and motivo == "corto", \
        f"{n} palabras y cinco frases: ok={ok} motivo={motivo}"
    return f"{n} palabras se rechazan por 'corto', no por otra regla"


prueba("un texto de veinte palabras no se puntua",
       _un_texto_de_veinte_palabras_no_se_puntua)


# La envoltura legal de Gutenberg, en VARIAS lineas, que es como viene.
# Escribirla en una sola linea hacia inutil la prueba de abajo: la primera
# linea es la cabecera corrida, y `_sin_cabecera_corrida` se la lleva, asi que
# con una sola linea se llevaba tambien la licencia entera.
_LICENCIA = (
    "The Project Gutenberg eBook of Something, by Someone." + chr(10) +
    "This eBook is for the use of anyone anywhere in the United States and " + chr(10) +
    "most other parts of the world at no cost and with almost no restrictions " + chr(10) +
    "whatsoever. You may copy it, give it away or re-use it under the terms " + chr(10) +
    "of the Project Gutenberg License included with this eBook or online at " + chr(10) +
    "www.gutenberg.org. If you are not located in the United States, you will " + chr(10) +
    "have to check the laws of the country where you are located before using " + chr(10) +
    "this eBook. This particular Project Gutenberg edition was produced by a " + chr(10) +
    "volunteer, and the full Project Gutenberg License applies to it." + chr(10) +
    "*** START OF THE PROJECT GUTENBERG EBOOK SOMETHING ***" + chr(10))


def _la_licencia_se_quita_antes_de_decidir():
    """`_es_boilerplate` mira el texto SIN la envoltura legal.

    Si la mira con ella, la formula de Gutenberg aparece en las primeras 400
    palabras de cualquier capitulo que la lleve pegada -y en un .txt la lleva
    el capitulo unico, que es el libro entero-, y el libro se descarta sin
    puntuar. Se corrigio el 9 de septiembre y no habia prueba: revertirlo
    pasaba la suite.
    """
    class Cap:
        titulo = "CHAPTER I. The Journey"
        texto = _LICENCIA + (
            "He said nothing for a long while, and the train ran on through the "
            "brown moor towards the west, with the rain beginning to streak the "
            "glass of the window beside us. ") * 30

        @property
        def palabras(self):
            return len(self.texto.split())

    c = Cap()
    assert c.palabras < 3000, f"el caso pierde sentido con {c.palabras} palabras"
    assert not ficha_mod._es_boilerplate(c), \
        "un capitulo de verdad con la licencia pegada se toma por licencia"
    # Y al reves: la licencia sola SIGUE cazandose.
    class Solo:
        titulo = "The Full Project Gutenberg License"
        texto = _LICENCIA * 6

        @property
        def palabras(self):
            return len(self.texto.split())

    assert ficha_mod._es_boilerplate(Solo()), "la licencia sola ya no se caza"
    return "la envoltura se quita antes de mirar, y la licencia sola sigue fuera"


prueba("la licencia se quita antes de decidir si es licencia",
       _la_licencia_se_quita_antes_de_decidir)


def _epub_con_cabecera_corrida(nombre="cabecera.epub"):
    """Un epub como los de la generacion vieja de Gutenberg (`pg28xxx`).

    Cada archivo empieza con un <h1> que repite "The Project Gutenberg eBook
    of X" y despues viene el encabezado de capitulo de verdad.
    """
    ruta = TMP / nombre
    cabecera = "<h1>The Project Gutenberg eBook of Something, by Someone.</h1>"
    # La portadilla de verdad tiene TITULO LIMPIO -en *Orgullo y prejuicio* es
    # "PRIDE. and PREJUDICE"- y debajo la licencia y el indice. Si el titulo
    # sale del texto legal, `_es_boilerplate` la caza por el titulo y la regla
    # de la portadilla no hace falta: la prueba pasaria sin ella.
    indice = "".join(f"<p>CHAPTER {i}. Of things that happen</p>"
                     for i in range(1, 41))
    archivos = [
        ("portadilla.xhtml", cabecera + "<h2>SOMETHING · A NOVEL</h2>"
                             f"<p>{_LICENCIA}</p><p>Contents</p>{indice}"),
        # Seis veces el relleno para pasar de 500 palabras: por debajo de eso
        # `_abrir` no lo considera cuerpo y la prueba de la portadilla mediria
        # otra cosa.
        ("cap1.xhtml", cabecera + "<h2>CHAPTER I</h2>"
                       f"<p>{_RELLENO * 6}</p>"),
        ("cap2.xhtml", cabecera + "<h2>CHAPTER II</h2>"
                       f"<p>{_RELLENO * 6}</p>"),
    ]
    manifiesto = "".join(
        f'<item href="{n}" id="it{i}" media-type="application/xhtml+xml"/>'
        for i, (n, _) in enumerate(archivos))
    itemrefs = "".join(f'<itemref idref="it{i}"/>' for i in range(len(archivos)))
    opf = ('<?xml version="1.0" encoding="utf-8"?>'
           '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">'
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
           '<dc:title>Something</dc:title><dc:creator>Someone</dc:creator>'
           '</metadata>'
           f'<manifest>{manifiesto}</manifest><spine>{itemrefs}</spine></package>')
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("OEBPS/content.opf", opf)
        for n, cuerpo in archivos:
            z.writestr(f"OEBPS/{n}", f"<html><body>{cuerpo}</body></html>")
    return str(ruta)


def _la_cabecera_corrida_no_es_el_titulo():
    """Los epub viejos repiten "The Project Gutenberg eBook of X" en cada archivo.

    Como no coincide con el titulo del libro, se colaba como titulo del
    capitulo: la *Alicia* ilustrada del catalogo salia con trece capitulos
    llamados igual. Y con ese titulo, `_es_boilerplate` los tomaba por licencia
    y la curva del "libro entero" se calculaba sobre UNO de los trece. Medido
    sobre `pg28885.epub`: 1 de 13 antes, 12 de 13 despues. En *Los hermanos
    Karamazov* eran 38 capitulos de 98.
    """
    libro = reader.cargar(_epub_con_cabecera_corrida())
    titulos = [c.titulo for c in libro.capitulos]
    colados = [t for t in titulos if "Project Gutenberg" in t]
    assert not colados, f"la cabecera corrida se colo como titulo: {colados}"
    assert "CHAPTER I" in titulos and "CHAPTER II" in titulos, titulos
    cuerpo = ficha_mod.capitulos_de_cuerpo(libro)
    assert len(cuerpo) == 2, \
        f"esperaba los dos capitulos de verdad y hay {len(cuerpo)}: {titulos}"
    return f"{len(cuerpo)} capitulos de cuerpo y ninguno titulado por la cabecera"


prueba("la cabecera corrida de Gutenberg no es el titulo del capitulo",
       _la_cabecera_corrida_no_es_el_titulo)


def _abrir_no_cae_en_la_portadilla():
    """Abrir un libro tiene que dejarte en el primer capitulo, no en los creditos.

    La integracion solo miraba que `idx` no fuera None, asi que fijarlo a 0
    -la portadilla- pasaba la suite.
    """
    libro, upd, _, resumen = ui._abrir(_epub_con_cabecera_corrida("portada.epub"))
    assert libro is not None, resumen
    idx = upd.get("value") if isinstance(upd, dict) else getattr(upd, "value", None)
    assert idx == 1, f"abrio en el capitulo {idx}, y el 0 es la portadilla"
    assert "capítulo 2" in resumen, resumen[:160]
    return "abre en el primer capitulo con cuerpo, no en la portadilla"


prueba("abrir un libro no cae en la portadilla", _abrir_no_cae_en_la_portadilla)


def _lo_que_viaja_a_openai_va_recortado():
    """El Cuadro 5 (T8) presume de este recorte y nadie lo comprobaba.

    Sin el, la oracion entera de un capitulo -o lo que pegue quien quiera-
    viaja a OpenAI: mas tokens, mas dinero y una via para inflar la peticion.
    """
    vistas = {}
    viejo_consultor = ui.consultor
    viejo_falta = config_mod.falta
    from lexicon import ResultadoLexico

    def doble():
        class C:
            @staticmethod
            def consultar(palabra, oracion, nivel, **k):
                vistas["palabra"], vistas["oracion"] = palabra, oracion
                return ResultadoLexico(
                    "hi", oracion, "hi", "hi", "INTJ", "interjection", None,
                    [], None, 0, None, None, None, None, False, None, None,
                    None, None, "basico", None, False, [], 0)
        return C()

    try:
        config_mod.falta = lambda: ["OPENAI_API_KEY"]
        ui.consultor = doble
        largo = "The rain fell on the moor and the train ran west. " * 200
        # Una palabra DE VERDAD. Con "x" * 300, `_consultar` contesta "eso son
        # 300 caracteres seguidos" y no llama al consultor: `vistas` quedaba
        # vacio y `len("") <= 400` se cumplia sola. Un mutante que quitaba el
        # recorte no rompia esta prueba.
        list(ui._consultar(None, None, None, "rain", largo, "es", None))
    finally:
        ui.consultor = viejo_consultor
        config_mod.falta = viejo_falta
    assert "oracion" in vistas, ("el consultor no se llego a llamar: la "
                                 "prueba no mide nada")
    assert len(vistas["oracion"]) == ui.LIMITE_ORACION, \
        f"la oracion viajo con {len(vistas['oracion'])} caracteres"
    # Y la palabra larga se rechaza antes de salir, que es la otra mitad.
    corte = list(ui._consultar(None, None, None, "x" * 300, largo, "es", None))
    assert "caracteres seguidos" in str(corte[-1]), str(corte[-1])[:120]
    return (f"oracion recortada a {ui.LIMITE_ORACION}; palabra de 300 "
            f"rechazada antes de salir")


prueba("lo que viaja a OpenAI va recortado", _lo_que_viaja_a_openai_va_recortado)


def _una_sesion_torcida_no_tumba_el_arranque():
    """`sesion.json` con la forma torcida, y `_reanudar` corre en `demo.load`.

    Se cerro para `[]`, `"hola"` y `3`, pero no para un objeto con la clave
    puesta y del tipo equivocado: `{"ruta": ["x"]}` llegaba a `os.path.exists`
    y lanzaba TypeError, o sea que la pagina entera arrancaba en error para ese
    lector hasta que alguien borrara el archivo a mano.
    """
    ruta = ui._ruta_sesion(None)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    guardado = ruta.read_text(encoding="utf-8") if ruta.exists() else None
    torcidas = ['{"ruta": ["x"], "idx": 0}', '{"ruta": {"a": 1}}',
                '{"ruta": 3}', '{"ruta": null}', '{"idx": 2}']
    try:
        for texto in torcidas:
            ruta.write_text(texto, encoding="utf-8")
            assert ui._leer_sesion(None) is None, f"acepto {texto}"
            list(ui._reanudar(None))          # es lo que corre en demo.load
            ui._capitulo(None, 0)
    finally:
        if guardado is None:
            ruta.unlink(missing_ok=True)
        else:
            ruta.write_text(guardado, encoding="utf-8")
    return f"{len(torcidas)} formas torcidas rechazadas sin lanzar"


prueba("un archivo de sesion con la forma torcida no tumba el arranque",
       _una_sesion_torcida_no_tumba_el_arranque)


def _un_analisis_a_medias_no_tumba_la_ficha():
    """El validador comprobaba `filas` y no lo que se lee despues.

    Un archivo con filas validas y sin `ventanas` pasaba la puerta y reventaba
    con `KeyError: 'ventanas'` dentro de `_resumen_analisis`, que es justo lo
    que ese validador existe para evitar. Y `dificultad` podia ser una cadena:
    `ficha.dificultad_global` la sumaba y salia un TypeError.
    """
    class Libro:
        titulo, autor, palabras = "Something", "Someone", 1000
        capitulos = []
        ruta = "x.epub"

    lib = Libro()
    p = ui._ruta_analisis(lib, "completo")
    p.parent.mkdir(parents=True, exist_ok=True)
    guardado = p.read_text(encoding="utf-8") if p.exists() else None
    try:
        # 1. Le falta todo menos las filas: se completa y no revienta.
        p.write_text('{"filas": [{"capitulo": 1, "dificultad": 1.0}]}',
                     encoding="utf-8")
        d = ui._analisis_guardado(lib, "completo")
        assert d is not None, "rechazo un analisis con filas validas"
        texto = ui._resumen_analisis(d)
        assert "Something" in texto, texto[:120]
        # 2. `dificultad` que no es numero: se rechaza el archivo.
        for mala in ('"abc"', "true", "null", "[]"):
            p.write_text('{"filas": [{"capitulo": 1, "dificultad": %s}], '
                         '"ventanas": 1, "palabras": 1, "titulo": "X", '
                         '"autor": "Y"}' % mala, encoding="utf-8")
            assert ui._analisis_guardado(lib, "completo") is None, \
                f"acepto dificultad = {mala}"
        # 3. Filas vacias: `min()` sobre lista vacia lanzaba ValueError.
        p.write_text('{"filas": []}', encoding="utf-8")
        assert ui._analisis_guardado(lib, "completo") is None, "acepto filas vacias"
    finally:
        if guardado is None:
            p.unlink(missing_ok=True)
        else:
            p.write_text(guardado, encoding="utf-8")
    return "se completa lo que falta y se rechaza lo que no es numero"


prueba("un analisis guardado a medias no tumba la ficha",
       _un_analisis_a_medias_no_tumba_la_ficha)


def _las_dos_pestanas_prometen_el_mismo_rango():
    """"Mi nivel" y "Sorprendeme" tienen que decir el MISMO rango.

    "Mi nivel" anunciaba `rango_recomendado` -nivel-0,10 a nivel+0,15- y
    "Sorprendeme" filtraba y anunciaba nivel±0,25. Con nivel 1,13, una decia
    "entre 1.03 y 1.28" y la de al lado "entre 0.88 y 1.38", del mismo perfil.
    Se arreglo en la segunda pestana y quedo mal la primera: el numero tiene
    que estar en UN sitio, y esta en `perfil.HOLGURA`.
    """
    p = perfil_mod.Perfil(nivel=1.13, banda="intermedio",
                          origen="cuestionario", creado="", nombre="Ana")
    h = ui.HOLGURA_POR_NIVEL
    # Y el numero, clavado. Sin esto la prueba solo dice que las dos pestanas
    # LEEN la misma variable: subirla a 0,5 -o sea, recomendar de 0,63 a 1,63
    # al que esta en 1,13- las deja de acuerdo las dos en la misma barbaridad
    # y la prueba sigue verde. 0,25 sobre 2 es medio nivel del MCER, y eso es
    # una promesa al lector, no un detalle interno.
    assert h == 0.25, (
        f"la holgura de recomendacion es {h} y no 0,25. Si de verdad cambia, "
        "cambiala aqui a mano y di por que en el commit")
    lo, hi = f"{max(0.0, p.nivel - h):.2f}", f"{min(2.0, p.nivel + h):.2f}"
    mi_nivel = perfil_mod.describir(p)
    assert lo in mi_nivel and hi in mi_nivel, \
        f"'Mi nivel' no anuncia {lo}-{hi}: {mi_nivel[:160]}"
    assert p.rango_recomendado == (round(p.nivel - h, 3), round(p.nivel + h, 3)), \
        f"rango_recomendado = {p.rango_recomendado}, y la holgura es {h}"
    return f"las dos pestanas dicen {lo}-{hi}"


prueba("las dos pestanas prometen el mismo rango",
       _las_dos_pestanas_prometen_el_mismo_rango)


def _un_perfil_con_nivel_infinito_no_se_carga():
    """`float("1e400")` es `inf` y pasa el `float()` sin queja.

    Con el, la pestana decia "Tu nivel de lectura: **inf / 2.00**" y
    "Lo mas leido entre **inf** y **2.00**". La escala publica es 0..2.
    """
    base = {"banda": "intermedio", "origen": "cuestionario", "creado": "",
            "nombre": "Ana"}
    malos = []
    for etiqueta, crudo in (("1e400", "1e400"), ("-1e400", "-1e400"),
                            ("nan", "NaN"), ("fuera de escala", "7.5"),
                            ("negativo", "-3")):
        ruta = TMP / f"perfil_{etiqueta.replace(' ', '_')}.json"
        ruta.write_text('{"nivel": %s, "banda": "intermedio", "origen": '
                        '"cuestionario", "creado": "", "nombre": "Ana"}' % crudo,
                        encoding="utf-8")
        if perfil_mod.cargar(str(ruta)) is not None:
            malos.append(etiqueta)
    ruta = TMP / "perfil_bueno.json"
    ruta.write_text('{"nivel": 1.13, "banda": "intermedio", "origen": '
                    '"cuestionario", "creado": "", "nombre": "Ana"}',
                    encoding="utf-8")
    bueno = perfil_mod.cargar(str(ruta))
    assert not malos, f"acepto niveles imposibles: {malos}"
    assert bueno is not None and abs(bueno.nivel - 1.13) < 1e-9, bueno
    assert base                      # el dict esta solo para documentar la forma
    return "inf, -inf, nan y fuera de 0..2 se rechazan; 1,13 se carga"


prueba("un perfil con nivel infinito no se carga",
       _un_perfil_con_nivel_infinito_no_se_carga)


def _las_descargas_nuevas_tienen_tope():
    """Descargar de Gutenberg no cuesta dinero, pero puede dejar sin servicio.

    Son hasta tres peticiones de 45 s a gutenberg.org, y mientras esperan
    ocupan uno de los ocho huecos de la cola: ocho ids distintos sin cache
    dejan la aplicacion sin huecos un par de minutos. Es el unico camino que
    puede tumbar el servicio sin gastar un centimo, y no tenia tope.

    Y el tope no puede cobrarle nada a quien vuelve a abrir un libro que YA
    tiene: eso no sale a la red.
    """
    class _P:
        headers = {}
        client = type("X", (), {"host": "10.6.6.6"})()

    pet = _P()
    clave = f"descargas:{ui._ip(pet)}"
    try:
        with ui._CANDADO_GASTO:
            ui._gasto[clave] = [time.time()] * ui.LIMITE_DESCARGAS_HORA
        tramos = list(ui._abrir_del_catalogo("PG9999999", pet))
        aviso = str(tramos[-1][-1])
        assert "libros nuevos en esta hora" in aviso, aviso[:160]
        # Y un libro ya cacheado no gasta ficha: se comprueba con el ayudante,
        # que es el que decide, sin bajar nada.
        ruta = ui.RUTA_LIBROS / "pg9999998.epub"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(b"x" * 3000)
        try:
            assert ui._esta_cacheado("PG9999998"), "no ve el libro ya descargado"
            assert not ui._esta_cacheado("PG9999997"), "se inventa una cache"
            assert not ui._esta_cacheado(""), "acepta un id vacio"
        finally:
            ruta.unlink(missing_ok=True)
    finally:
        with ui._CANDADO_GASTO:
            ui._gasto.pop(clave, None)
    return f"tope de {ui.LIMITE_DESCARGAS_HORA} libros nuevos por hora, y los ya bajados no cuentan"


prueba("las descargas nuevas tienen tope por hora", _las_descargas_nuevas_tienen_tope)


def _la_poda_de_sesiones_no_tira_al_que_sigue_leyendo():
    """La poda tiene que tirar las MENOS USADAS, no las que entraron primero.

    `_LECTOR_POR_SESION` se poda a la mitad al pasar de 5.000, y reasignar una
    clave que ya existe NO la mueve al final en un dict de Python: una sesion
    de las primeras que siguiera viva -recargando la pagina cada rato- se
    quedaba en la cabecera de la fila y caia en la siguiente poda, con lo que
    ese lector perdia sus datos hasta volver a cargar.
    """
    class _P:
        def __init__(self, s):
            self.session_hash = s

    viejo = dict(ui._LECTOR_POR_SESION)
    try:
        with ui._CANDADO_LECTOR:
            ui._LECTOR_POR_SESION.clear()
        # El lector veterano: entra primero de todos.
        ui._registrar_lector("veterano", _P("s-0"))
        for i in range(1, 4000):
            ui._registrar_lector(f"lector{i}", _P(f"s-{i}"))
        # Y sigue leyendo: cada carga de pagina lo vuelve a registrar.
        ui._registrar_lector("veterano", _P("s-0"))
        for i in range(4000, 5200):
            ui._registrar_lector(f"lector{i}", _P(f"s-{i}"))
        with ui._CANDADO_LECTOR:
            sigue = ui._LECTOR_POR_SESION.get("s-0")
            cuantos = len(ui._LECTOR_POR_SESION)
        assert sigue == "veterano", \
            f"la poda se llevo al lector que seguia usando la app ({cuantos} vivos)"
        assert cuantos <= 5000, f"la poda no poda: {cuantos} entradas"
        # Y lo mismo consultando, que es lo que hace `_dir_lector`.
        with ui._CANDADO_LECTOR:
            ui._LECTOR_POR_SESION.clear()
        ui._registrar_lector("consultado", _P("s-c"))
        for i in range(4999):
            ui._registrar_lector(f"otro{i}", _P(f"t-{i}"))
        # `_dir_lector` se corta antes en local -devuelve la carpeta de
        # siempre-, asi que se llama a la parte que mira el diccionario, que es
        # la que refresca. Es tambien la que usa `_dir_lector` desplegada.
        assert ui._lector_de_sesion("s-c") == "consultado"
        for i in range(4999, 5300):
            ui._registrar_lector(f"otro{i}", _P(f"t-{i}"))
        with ui._CANDADO_LECTOR:
            sigue = ui._LECTOR_POR_SESION.get("s-c")
        assert sigue == "consultado", "consultar no cuenta como uso para la poda"
    finally:
        with ui._CANDADO_LECTOR:
            ui._LECTOR_POR_SESION.clear()
            ui._LECTOR_POR_SESION.update(viejo)
    return "la poda tira las menos usadas, no las que entraron primero"


prueba("la poda de sesiones no tira al que sigue leyendo",
       _la_poda_de_sesiones_no_tira_al_que_sigue_leyendo)


def _una_sola_raiz_de_datos():
    """Todo lo que la app escribe cuelga de `LITERALEVEL_DATOS`. TODO.

    Es lo que permite montar un disco persistente en un Space sin tocar codigo,
    y `DESPLIEGUE.md` lo prometia -"no hace falta tocar codigo, solo la ruta
    base"- cuando era falso a medias: la carpeta de audio que Gradio sirve, los
    libros descargados, la cache de lexico, la de audio y `voz.db` estaban
    clavadas a `~/.literalevel`. Las dos caches son las que evitan volver a
    PAGAR a OpenAI por lo mismo, asi que perderlas en cada reinicio cuesta
    dinero de verdad.

    Esta prueba corre en un proceso aparte a proposito: las rutas se resuelven
    al importar cada modulo, y esta suite ya tiene la suya fijada.
    """
    import subprocess
    guion = (
        "import atexit, os, shutil, sys, tempfile" + chr(10) +
        "tmp = tempfile.mkdtemp(dir=os.environ.get('LITERALEVEL_TMP') or None)" + chr(10) +
        "atexit.register(shutil.rmtree, tmp, ignore_errors=True)" + chr(10) +
        "os.environ['LITERALEVEL_DATOS'] = tmp" + chr(10) +
        "sys.path.insert(0, %r)" % str(pathlib.Path(__file__).parent / "app") + chr(10) +
        "import catalogo, config, ui, lexicon, voz" + chr(10) +
        "rutas = {" + chr(10) +
        # La decima. Se quedo fuera cuando se escribio esta prueba, la prueba
        # decia 'TODO' igual, y con ella fuera la cache del catalogo seguia
        # yendo al disco efimero del Space: 56,9 s de recodificar en cada
        # arranque. Una lista escrita a mano miente en cuanto alguien anade
        # una ruta, asi que lo que hay que mirar es que no falte ninguna." + chr(10) +
        "  'catalogo.DIR_CACHE': str(catalogo.DIR_CACHE)," + chr(10) +
        "  'BASE_DATOS_LECTOR': str(ui.BASE_DATOS_LECTOR)," + chr(10) +
        "  'RUTAS_PERMITIDAS': ui.RUTAS_PERMITIDAS[0]," + chr(10) +
        "  'RUTA_LIBROS': str(ui.RUTA_LIBROS)," + chr(10) +
        "  'RUTA_ANALISIS': str(ui.RUTA_ANALISIS)," + chr(10) +
        "  'RUTA_SESION': str(ui.RUTA_SESION)," + chr(10) +
        "  'lexicon.RUTA_CACHE': str(lexicon.RUTA_CACHE)," + chr(10) +
        "  'lexicon.RUTA_AUDIO_GENERADO': str(lexicon.RUTA_AUDIO_GENERADO)," + chr(10) +
        "  'voz.RUTA_DB_POR_DEFECTO': str(voz.RUTA_DB_POR_DEFECTO)," + chr(10) +
        "  'voz.RUTA_AUDIO_GENERADO': str(voz.RUTA_AUDIO_GENERADO)," + chr(10) +
        "}" + chr(10) +
        "fuera = {k: v for k, v in rutas.items() if not v.startswith(tmp)}" + chr(10) +
        "print(len(rutas), fuera)" + chr(10))
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", guion],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=600)
    assert r.returncode == 0, r.stderr[-600:]
    cuantas, _, resto = r.stdout.strip().partition(" ")
    assert resto == "{}", f"rutas clavadas fuera de la raiz: {resto}"
    return f"las {cuantas} rutas de escritura cuelgan de LITERALEVEL_DATOS"


prueba("una sola raiz de datos, configurable", _una_sola_raiz_de_datos)


def _el_modelo_puede_reventar_de_cualquier_forma():
    """Los cuatro manejadores del modelo, contra lo que NO es ValueError ni OSError.

    La cabecera de este modulo declara que ningun manejador levanta hacia
    Gradio. Se cumplia para `ValueError` y `OSError` y para nada mas, y la
    prueba que lo cubria solo lanzaba `OSError` y solo contra `_medir`.

    Lo que lanza torch al quedarse sin memoria es `RuntimeError`
    -"DefaultCPUAllocator: not enough memory"-, y lo que lanza `safetensors`
    con una descarga del Hub cortada en un arranque en frio tampoco desciende
    de OSError. En `cpu-basic`, con dos analisis completos encolados, no es
    exotico.

    Se prueban las cuatro puertas con tres excepciones distintas, y se exige
    que vuelva texto con el aviso en vez de una traza.
    """
    class Revienta:
        def __init__(self, que):
            self.que = que

        def puntuar(self, *a, **k):
            raise self.que

        def perfil_de_texto(self, *a, **k):
            raise self.que

    libro = ui._abrir(escribir(
        "revienta.txt", "The rain fell on the moor and the train ran west. " * 120))[0]
    assert libro is not None

    viejo = ui.puntuador
    malos = []
    try:
        for que in (RuntimeError("DefaultCPUAllocator: not enough memory"),
                    MemoryError("sin memoria"),
                    KeyError("safetensors")):
            ui.puntuador = lambda q=que: Revienta(q)
            casos = {
                "_medir": lambda: list(ui._medir(libro, 0)),
                "_analizar_libro": lambda: list(ui._analizar_libro(libro, "rapido")),
                "_desde_muestra": lambda: ui._desde_muestra(
                    None, "x", "The rain fell on the moor and the train ran west. " * 40),
                "_nivel_desde_libro": lambda: ui._nivel_desde_libro(
                    None, "x", escribir("revienta2.txt",
                                        "The rain fell on the moor. " * 400)),
            }
            for nombre, fn in casos.items():
                try:
                    salida = str(fn())
                except Exception as e:
                    malos.append(f"{nombre} LEVANTA {type(e).__name__} con {type(que).__name__}")
                    continue
                if "[!]" not in salida:
                    malos.append(f"{nombre} no avisa con {type(que).__name__}: {salida[:90]}")
    finally:
        ui.puntuador = viejo
    assert not malos, malos
    return "las cuatro puertas del modelo avisan en vez de levantar"


prueba("el modelo puede reventar de cualquier forma",
       _el_modelo_puede_reventar_de_cualquier_forma)


def _la_pantalla_del_libro_no_se_contradice():
    """Un solo recuento de palabras por pantalla.

    La cabecera pintaba `libro.palabras` -crudo, con portadilla y licencia
    dentro- y tres lineas mas abajo la ficha pintaba el descontado. En
    *Metamorphosis* eran 25.077 arriba y 21.938 abajo, a la vez, en el tercer
    clic del recorrido de la demo. Dos cifras distintas de lo mismo a tres
    lineas de distancia es lo primero que alguien compara.
    """
    texto = ("CHAPTER I. The Journey\n\n"
             + "He said nothing for a long while, and the train ran on through the "
               "brown moor towards the west, with the rain beginning to streak the "
               "glass of the window beside us. " * 40)
    libro, _, _, resumen = ui._abrir(escribir("un_recuento.txt", texto))
    assert libro is not None, resumen
    c = ficha_mod.caracteristicas(libro)
    cuenta = ficha_mod.miles(c.palabras)
    assert cuenta in resumen, \
        f"la cabecera dice otra cosa que la ficha ({cuenta}): {resumen[:140]}"
    ficha_texto = ui._ficha_libro(libro)
    assert cuenta in ficha_texto, f"la ficha dice otra cosa: {ficha_texto[:140]}"

    # Y tampoco se contradicen en el SINGULAR. Con un libro de un capitulo la
    # cabecera decia "1 capítulos" y la ficha, tres lineas mas abajo,
    # "1 capítulo": la misma pantalla, dos formas de contar lo mismo.
    uno, _, _, _ = ui._abrir(escribir(
        "un_capitulo.txt",
        "The lantern swung above the quiet harbour wall and nobody moved. " * 40))
    assert uno is not None and len(uno.capitulos) == 1, (
        f"el libro de prueba no tiene un solo capitulo: {uno and len(uno.capitulos)}")
    cab_uno = ui._abrir(escribir(
        "un_capitulo_b.txt",
        "The lantern swung above the quiet harbour wall and nobody moved. " * 40))[3]
    assert "1 capítulo " in cab_uno and "1 capítulos" not in cab_uno, (
        f"la cabecera no concuerda en singular: {cab_uno[:140]}")
    assert "1 capítulos" not in ui._ficha_libro(uno), "y la ficha tampoco"
    return f"cabecera y ficha dicen las mismas {cuenta} palabras, y el singular"


prueba("la pantalla del libro no se contradice",
       _la_pantalla_del_libro_no_se_contradice)


def _la_oracion_de_contexto_no_arrastra_el_titulo():
    """Lo que se manda a desambiguar tiene que ser una frase, no un titulo pegado.

    `_oracion_de` partia el capitulo entero con `SENT_RE`, y los encabezados no
    llevan punto: se los tragaba y los pegaba delante. El contexto que se
    citaba de *Metamorphosis* empezaba "I I One morning, when Gregor Samsa
    woke...". `_frase_del_capitulo` ya lo tenia resuelto partiendo por parrafos
    primero; esta no.
    """
    texto = ("CHAPTER I\n\nDown the Rabbit-Hole\n\n"
             "Alice was beginning to get very tired of sitting by her sister on "
             "the bank, and of having nothing to do. Once or twice she had peeped "
             "into the book her sister was reading, but it had no pictures.")
    o = ui._oracion_de(texto, "Alice")
    assert o, "no devolvio ninguna oracion"
    assert not o.startswith("CHAPTER"), f"arrastra el encabezado: {o[:80]}"
    assert "Rabbit-Hole" not in o, f"arrastra el titulillo: {o[:80]}"
    assert o.startswith("Alice was beginning"), o[:80]
    # Y si NO hay mas que el encabezado, sigue devolviendo algo antes que nada.
    assert ui._oracion_de("CHAPTER XII\n\nAlice's Evidence", "Alice"), \
        "sin cuerpo tendria que devolver el respaldo"
    return "la oracion empieza donde empieza la prosa"


prueba("la oracion de contexto no arrastra el titulo",
       _la_oracion_de_contexto_no_arrastra_el_titulo)


def _ningun_aviso_llega_en_crudo_al_lector():
    """Los avisos que `lexicon` escribe para el log no valen para la pantalla.

    Salia tal cual: "acepcion provisional: margen bajo (0.004) frente a otra
    acepcion: An animal that preys on game...". Sin acentos, con el margen en
    decimales y con jerga, al lado de avisos redactados con cuidado.
    """
    crudos = [
        "acepcion provisional: margen bajo (0.004) frente a otra acepcion: An animal.",
        "sin audio en el diccionario",
        "sin OPENAI_API_KEY: no hay explicacion contextual",
        "OpenAI no disponible: AuthenticationError: 401",
        "OpenAI no disponible: APITimeoutError: timed out",
        "no se pudo generar audio: RateLimitError 429 insufficient_quota",
    ]
    malos = []
    for idioma in ("es", "en"):
        for crudo in crudos:
            humano = ui._humanizar(crudo, idioma)
            if humano == crudo:
                malos.append(f"{idioma}: sin traducir -> {crudo[:60]}")
            elif any(j in humano for j in ("acepcion", "OPENAI_API_KEY", "Error",
                                           "429", "401")):
                malos.append(f"{idioma}: sigue con jerga -> {humano[:60]}")
    assert not malos, malos
    return f"los {len(crudos)} avisos salen redactados, en los dos idiomas"


prueba("ningun aviso llega en crudo al lector",
       _ningun_aviso_llega_en_crudo_al_lector)


# --- S3: lo que trece mutantes demostraron que nadie protegia --------------
#
# De 37 mutantes de la auditoria 14, trece sobrevivieron. No son fallos: son
# agujeros en la red. Cada prueba de aqui abajo existe porque, sin ella, se
# podia deshacer una correccion sin que nada se enterase.

titulo("La red que faltaba (auditoria 14)")


def _el_marcapaginas_y_el_cuaderno_son_de_cada_lector():
    """El recorrido de verdad, con DOS visitantes, no solo la funcion que reparte.

    `_dos_lectores_no_se_ven_los_datos` recorre el perfil y nada mas, asi que
    dos mutantes sobrevivian:

      - `_ruta_sesion` devolviendo `RUTA_SESION` -un marcapaginas para todos-,
        que es literalmente "el caso mas feo" que describe la cabecera de
        `ui.py`: `demo.load` le pinta a cada visitante el capitulo del PDF
        privado del anterior.
      - `_archivo_lector("cuaderno.db", ...)` sin la peticion: un cuaderno de
        vocabulario para todos, con las palabras y las FRASES del libro de otro.

    La prueba que vigilaba esto miraba el CUERPO de los manejadores buscando
    `_archivo_lector(... peticion`, asi que el manejador que dejaba de pasarla
    ya no casaba con el patron y se saltaba: la red no cubria justo lo que
    queria cubrir.
    """
    from lexicon import ResultadoLexico

    def dentro():
        a, b = _Peticion("aisla-aaa"), _Peticion("aisla-bbb")
        libro_a = escribir("libro_de_a.txt",
                           "The rain fell on the moor and the train ran west. " * 120)

        # A abre un libro y se queda en un capitulo.
        ui._abrir(libro_a, a)
        assert ui._leer_sesion(a), "A no guardo su marcapaginas"
        assert ui._leer_sesion(b) is None, \
            "B ve el marcapaginas de A: un solo sesion.json para todos"

        # Y `_reanudar`, que es lo que corre en `demo.load`.
        recuperado_b = str(list(ui._reanudar(b)))
        assert "libro_de_a" not in recuperado_b, \
            f"demo.load le pinta a B el libro de A: {recuperado_b[:120]}"

        # A consulta una palabra; el cuaderno es suyo.
        antes = ui.consultor

        def doble():
            class C:
                @staticmethod
                def consultar(palabra, oracion, nivel, **k):
                    return ResultadoLexico(
                        palabra, oracion, palabra, palabra, "NOUN", "noun",
                        "A private word.", [], 0.9, 1, None, None, None, None,
                        False, None, None, None, None, "basico", 3.0, False, [], 0)
            return C()

        try:
            ui.consultor = doble
            list(ui._consultar(None, None, None, "zarzaparrilla",
                               "The zarzaparrilla grew by the wall.", "es", a))
        finally:
            ui.consultor = antes

        mias = str(ui._mis_palabras(a))
        suyas = str(ui._mis_palabras(b))
        assert "zarzaparrilla" in mias, f"A no ve su propia palabra: {mias[:120]}"
        assert "zarzaparrilla" not in suyas, \
            "B lee el cuaderno de A: un solo cuaderno.db para todos"
        assert ui._archivo_lector("cuaderno.db", a) != \
            ui._archivo_lector("cuaderno.db", b), "mismo cuaderno para los dos"
        assert ui._ruta_sesion(a) != ui._ruta_sesion(b), "mismo sesion.json"
        return "marcapaginas y cuaderno separados por lector"

    return _con_nube(dentro)


prueba("el marcapaginas y el cuaderno son de cada lector",
       _el_marcapaginas_y_el_cuaderno_son_de_cada_lector)


def _cada_respuesta_del_cuestionario_va_a_su_pregunta():
    """El primer clic de la demo, y nadie comprobaba que las respuestas casaran.

    Invertir la lista de claves -`_claves_cuestionario()[::-1]`- asigna cada
    respuesta a otra pregunta y sobrevivia a las 266 extremas y a
    `pruebas_perfil.py`: aquella prueba `perfil.desde_cuestionario` con
    diccionarios ya construidos, y las de `ui` solo miraban el nombre y que el
    perfil no fuera `None`.

    Aqui se pone valor en UNA sola posicion y se exige el nivel que le toca.
    """
    claves = ui._claves_cuestionario()
    frag = [c for c in claves if c in perfil_mod._CLAVES_FRAGMENTOS]
    opin = [c for c in claves if c not in perfil_mod._CLAVES_FRAGMENTOS]
    assert frag and opin, f"el cuestionario ya no tiene los dos grupos: {claves}"

    # UN solo valor no discrimina: con un dato, el promedio de las de opinion y
    # el maximo de los fragmentos devuelven los dos ese dato, asi que invertir
    # las claves daba el mismo nivel. Hacen falta dos valores en grupos
    # DISTINTOS, y entonces cambiarlos de sitio cambia el resultado.
    vector = [None] * len(claves)
    vector[claves.index(opin[0])] = 0.0
    vector[claves.index(frag[0])] = 2.0
    peso = perfil_mod.PESO_FRAGMENTOS
    esperado = round((1.0 - peso) * 0.0 + peso * 2.0, 3)
    alreves = round((1.0 - peso) * 2.0 + peso * 0.0, 3)
    assert abs(esperado - alreves) > 1e-6, \
        "con este peso los dos grupos dan lo mismo: la prueba no discriminaria"

    p = ui._desde_cuestionario(None, "Ana", None, *vector)[0]
    assert p is not None, "no salio perfil"
    assert abs(p.nivel - esperado) < 1e-6, (
        f"{opin[0]}=0,0 y {frag[0]}=2,0 tendrian que dar {esperado} y dio "
        f"{p.nivel}; {alreves} seria con las respuestas cambiadas de pregunta")
    return f"opinion 0,0 + fragmento 2,0 -> {esperado}, y no {alreves}"


prueba("cada respuesta del cuestionario va a su pregunta",
       _cada_respuesta_del_cuestionario_va_a_su_pregunta)


def _sorprendeme_filtra_de_verdad_por_nivel():
    """`por_nivel` tiene que FILTRAR, no solo anunciar.

    `_el_rango_anunciado_es_el_filtrado` mira el rotulo; que `por_nivel`
    ignorara la holgura -`d = self.df`- y devolviera cualquier libro sobrevivia
    entera. Es la pantalla que el guion ensena en el segundo paso.
    """
    try:
        cat = ui.catalogo()
    except Exception as e:
        return f"sin catalogo en esta maquina ({type(e).__name__}), no se puede medir"
    h = ui.HOLGURA_POR_NIVEL
    malos = []
    for nivel in (0.0, 0.8, 2.0):
        libros = cat.por_nivel(nivel, holgura=h, n=10)
        fuera = [(b.nivel, b.puntuacion_nivel) for b in libros
                 if abs(b.puntuacion_nivel - nivel) > h + 1e-9]
        if fuera:
            malos.append(f"nivel {nivel}: devuelve {fuera} fuera de ±{h}")
    assert not malos, malos
    return f"por_nivel respeta ±{h} en los tres extremos"


prueba("sorprendeme filtra de verdad por nivel",
       _sorprendeme_filtra_de_verdad_por_nivel)


def _un_libro_de_gutenberg_se_puede_abrir_desde_la_tabla():
    """Dos mutantes vivian aqui, y los dos dejan el boton "Leerlo ahora" muerto.

    `_opciones_libros` sin listar nada, y `_tabla_libros` marcando TODO como
    abrible -incluido StoryWeaver, que no se puede descargar-. Las pruebas que
    los cubrian devolvian `["choices"]` y no aseveraban nada.
    """
    class L:
        def __init__(self, ident, titulo):
            self.id, self.titulo, self.autor = ident, titulo, "Autor"
            self.nivel, self.gancho, self.descargas = "B1", "de que va", 10
            self.similitud = self.afinidad = 0.5

    libros = [L("PG1342", "Pride and Prejudice"), L("SW201", "Un cuento")]
    upd = ui._opciones_libros(libros)
    opciones = upd.get("choices") if isinstance(upd, dict) else getattr(upd, "choices", [])
    assert opciones, "el desplegable de 'Leerlo ahora' sale vacio"
    ids = [str(o[1] if isinstance(o, (list, tuple)) else o) for o in opciones]
    assert any("PG1342" in i for i in ids), f"no ofrece el de Gutenberg: {ids}"
    assert not any("SW201" in i for i in ids), \
        f"ofrece abrir uno de StoryWeaver, que no se puede descargar: {ids}"

    tabla = ui._tabla_libros(libros)
    assert "▸ 1 de 2" in tabla, f"el recuento de abribles no cuadra: {tabla[:160]}"
    # Con el catalogo medido todos son de Gutenberg: la cabecera no puede
    # hablar de "los demas, de StoryWeaver" en una lista que no tiene demas.
    solo_pg = ui._tabla_libros([L("PG1342", "Pride and Prejudice"), L("PG2554", "Crime")])
    assert "StoryWeaver" not in solo_pg.split("|")[0], \
        f"habla de StoryWeaver sin haber ninguno: {solo_pg[:160]}"
    assert "▸" in solo_pg.split("|")[0], f"sin la leyenda del ▸: {solo_pg[:160]}"
    # Una antologia de Gutenberg trae diecisiete autores con fechas y papel:
    # en la tabla sale el primero y «y otros», y el traductor no cuenta.
    antologia = L("PG9999", "Best Russian Short Stories")
    antologia.autor = ("Seltzer, Thomas, 1875?-1943 [Editor]; Andreyev, Leonid, "
                       "1871-1919 [Contributor]; Chekhov, Anton Pavlovich, "
                       "1860-1904 [Contributor]")
    garnett = L("PG2554", "Crime and Punishment")
    garnett.autor = ("Dostoyevsky, Fyodor, 1821-1881; Garnett, Constance, "
                     "1861-1946 [Translator]")
    tabla_larga = ui._tabla_libros([antologia, garnett])
    assert "Seltzer, Thomas y otros" in tabla_larga and "Chekhov" not in tabla_larga, \
        f"la antologia lista a todos sus autores: {tabla_larga[:300]}"
    assert "Dostoyevsky, Fyodor ·" in tabla_larga and "Garnett" not in tabla_larga, \
        f"el traductor cuenta como otro autor o sobran las fechas: {tabla_larga[:300]}"
    etiquetas = [str(o[0]) for o in ui._opciones_libros([antologia, garnett])["choices"]]
    assert all("Contributor" not in e and "1821" not in e for e in etiquetas), \
        f"el desplegable arrastra el autor entero: {etiquetas}"
    return "el de Gutenberg se ofrece y el de StoryWeaver no"


prueba("un libro de Gutenberg se puede abrir desde la tabla",
       _un_libro_de_gutenberg_se_puede_abrir_desde_la_tabla)


def _la_sinopsis_guardada_no_se_vuelve_a_pagar():
    """"Un libro se resume una vez y ya", dice el documento. Nadie lo probaba.

    Ignorar la sinopsis guardada -`datos = None`- hace que cada pulsacion de
    "¿De que trata?" pague cuatro pasajes a la API. La prueba del cupo
    comprueba que no se cobre sin llamar; no que no se llame cuando ya esta.
    """
    class Cap:
        titulo = "CHAPTER I"
        texto = "The rain fell on the moor and the train ran west. " * 40
        palabras = 400

    class Libro:
        titulo, autor, palabras = "Guardado", "Autor", 1000
        capitulos = [Cap()]
        ruta = "guardado.txt"

    lib = Libro()
    p = ui.RUTA_ANALISIS / f"{ui._clave_libro(lib)}-sinopsis.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    guardado = p.read_text(encoding="utf-8") if p.exists() else None
    try:
        p.write_text('{"de_que_trata": "Va de esto.", "temas": ["a"], '
                     '"para_quien": "para ti", "aviso": ""}', encoding="utf-8")
        assert ui._sinopsis_guardada(lib), \
            "no reconoce la sinopsis que acaba de guardarse: se pagaria otra vez"
        # Y con ella puesta, el manejador no puede llegar a pedir cliente.
        llamadas = []
        antes = ui.consultor
        try:
            ui.consultor = lambda: (_ for _ in ()).throw(
                AssertionError("pidio consultor con la sinopsis ya guardada"))
            salida = str(list(ui._de_que_trata(lib)))
        finally:
            ui.consultor = antes
        assert "Va de esto" in salida, f"no uso la guardada: {salida[:140]}"
        assert not llamadas
    finally:
        if guardado is None:
            p.unlink(missing_ok=True)
        else:
            p.write_text(guardado, encoding="utf-8")
    return "la sinopsis guardada se reutiliza y no se vuelve a pagar"


prueba("la sinopsis guardada no se vuelve a pagar",
       _la_sinopsis_guardada_no_se_vuelve_a_pagar)


def _los_tres_cubos_por_hora_son_de_verdad_distintos():
    """La prueba que habia devolvia una TUPLA `(True, False)`, que nunca es False.

    Con los tres cubos contados en el mismo, una hora de consultas lexicas te
    deja sin practica de voz.
    """
    class _P:
        headers = {}
        client = type("X", (), {"host": "10.8.8.8"})()

    pet = _P()
    claves = [f"{c}:{ui._ip(pet)}" for c in ("lexico", "voz", "sinopsis")]
    try:
        with ui._CANDADO_GASTO:
            for c in claves:
                ui._gasto.pop(c, None)
        # Se agota SOLO el de lexico.
        for _ in range(ui.LIMITE_CONSULTAS_HORA):
            assert ui._dentro_del_limite(pet, "lexico", ui.LIMITE_CONSULTAS_HORA)
        assert not ui._dentro_del_limite(pet, "lexico", ui.LIMITE_CONSULTAS_HORA), \
            "el cubo de lexico no se agota"
        assert ui._dentro_del_limite(pet, "voz", ui.LIMITE_VOZ_HORA), \
            "agotar lexico deja sin voz: los cubos estan mezclados"
        assert ui._dentro_del_limite(pet, "sinopsis", ui.LIMITE_SINOPSIS_HORA), \
            "agotar lexico deja sin sinopsis: los cubos estan mezclados"
    finally:
        with ui._CANDADO_GASTO:
            for c in claves:
                ui._gasto.pop(c, None)
    return "agotar el lexico no toca ni la voz ni la sinopsis"


prueba("los tres cubos por hora son de verdad distintos",
       _los_tres_cubos_por_hora_son_de_verdad_distintos)


def _los_archivos_que_escribe_la_app_no_la_tumban():
    """Tres formas de tumbar un manejador con archivos que la app MISMA escribe.

    No es paranoia de disco corrupto:

    - `_analizar_libro` guarda `round(sum(vs) / len(vs), 3)`, y si el modelo
      devuelve `NaN` -`np.clip(nan)` sigue siendo `nan`- se PERSISTE en el
      JSON. `json.loads` lo lee de vuelta tan contento, y revienta con
      `ValueError: cannot convert float NaN to integer` **la siguiente vez que
      se abra ese libro**. Una bomba puesta por nosotros mismos.
    - La sinopsis viene de un modelo de lenguaje: un campo que tenia que ser
      texto puede llegar como lista, y el `.strip()` de quien la pinta levanta
      `AttributeError`.
    - Y `perfil.json` convertido en carpeta: `_perfil_inicial` corre en
      `demo.load`, asi que la pagina entera arrancaba en error para ese lector.
    """
    class Cap:
        titulo = "CHAPTER I"
        texto = "The rain fell on the moor and the train ran west. " * 40
        palabras = 400

    class Libro:
        titulo, autor, palabras = "Bomba", "Autor", 1000
        capitulos = [Cap()]
        ruta = "bomba.txt"

    lib = Libro()
    malos = []

    # 1. El analisis con NaN e inf, que es lo que el propio modelo puede guardar.
    pa = ui._ruta_analisis(lib, "completo")
    pa.parent.mkdir(parents=True, exist_ok=True)
    for etiqueta, crudo in (
            ("NaN", '{"filas": [{"capitulo": 1, "dificultad": NaN, "titulo": "I"}], '
                    '"ventanas": 1, "palabras": 1, "titulo": "X", "autor": "Y"}'),
            ("inf", '{"filas": [{"capitulo": 1, "dificultad": 1.0, "titulo": "I"}], '
                    '"ventanas": 1e400, "palabras": 1, "titulo": "X", "autor": "Y"}')):
        pa.write_text(crudo, encoding="utf-8")
        d = ui._analisis_guardado(lib, "completo")
        if d is not None:
            try:
                ui._resumen_analisis(d)
            except Exception as e:
                malos.append(f"analisis con {etiqueta}: {type(e).__name__}: {e}")
        try:
            list(ui._analizar_libro(lib, "rapido"))
        except Exception as e:
            malos.append(f"_analizar_libro con {etiqueta}: {type(e).__name__}: {e}")
    pa.unlink(missing_ok=True)

    # 2. La sinopsis con una lista donde iba texto, y una cadena donde iba lista.
    ps = ui.RUTA_ANALISIS / f"{ui._clave_libro(lib)}-sinopsis.json"
    for etiqueta, crudo in (
            ("lista en de_que_trata",
             '{"de_que_trata": ["a", "b"], "temas": ["x"], "para_quien": "tu"}'),
            ("lista en para_quien",
             '{"de_que_trata": "ok", "temas": ["x"], "para_quien": ["a"]}'),
            ("cadena en temas",
             '{"de_que_trata": "ok", "temas": "una cadena", "para_quien": "tu"}')):
        ps.write_text(crudo, encoding="utf-8")
        try:
            salida = str(list(ui._de_que_trata(lib)))
        except Exception as e:
            malos.append(f"sinopsis con {etiqueta}: {type(e).__name__}: {e}")
            continue
        if etiqueta == "cadena en temas" and "u · n · a" in salida:
            malos.append("los temas se pintan letra a letra")
    ps.unlink(missing_ok=True)

    # 3. `perfil.json` que es una carpeta: lo lee `demo.load`.
    import tempfile
    carpeta = pathlib.Path(pruebas_tmp.carpeta()) / "perfil.json"
    carpeta.mkdir()
    try:
        if perfil_mod.cargar(str(carpeta)) is not None:
            malos.append("acepto una CARPETA como perfil")
    except Exception as e:
        malos.append(f"perfil.cargar con carpeta: {type(e).__name__}: {e}")

    assert not malos, malos
    return "NaN, inf, listas donde iba texto y una carpeta: ninguno tumba nada"


prueba("los archivos que escribe la app no la tumban",
       _los_archivos_que_escribe_la_app_no_la_tumban)


def _la_pantalla_del_libro_no_se_contradice_ni_en_la_curva():
    """El resumen de la curva tambien. Mi arreglo anterior se quedo a medias.

    Alinee la cabecera con la ficha y deje fuera el resumen del analisis, que
    seguia imprimiendo `libro.palabras` crudo: la misma pantalla decia 129.589
    arriba y "sobre 130.104 en total" debajo de la grafica. Y 130.104 era la
    cifra que el guion del video dice a camara.
    """
    # CON la envoltura legal de Gutenberg, a proposito: sin ella el recuento
    # crudo y el descontado son el MISMO numero, devolver uno u otro da igual
    # y el mutante sobrevive. Es el tercer patron de prueba decorativa que
    # este archivo documenta: un dato de prueba demasiado limpio prueba el
    # camino equivocado.
    texto = (_LICENCIA + "CHAPTER I. The Journey\n\n"
             + "He said nothing for a long while, and the train ran on through the "
               "brown moor towards the west, with the rain beginning to streak the "
               "glass of the window beside us. " * 40)
    libro, _, _, resumen = ui._abrir(escribir("tres_cifras.txt", texto))
    assert libro is not None, resumen
    cuenta = ficha_mod.miles(ficha_mod.caracteristicas(libro).palabras)
    crudo = ficha_mod.miles(libro.palabras)
    assert crudo != cuenta, (
        f"el caso no discrimina: crudo y descontado son los dos {crudo}")
    assert cuenta in resumen, f"la cabecera no dice {cuenta}: {resumen[:120]}"

    datos = {"titulo": libro.titulo, "autor": libro.autor,
             "palabras": ui._palabras_del_cuerpo(libro), "ventanas": 10,
             "filas": [{"capitulo": 1, "titulo": "I", "dificultad": 1.0}],
             "modo": "completo"}
    curva = ui._resumen_analisis(datos)
    assert cuenta in curva, \
        f"la curva dice otra cifra que la cabecera ({cuenta}): {curva[:160]}"
    if crudo != cuenta:
        assert crudo not in curva, f"la curva sigue con el recuento crudo {crudo}"
    return f"cabecera, ficha y curva dicen las mismas {cuenta} palabras"


prueba("la pantalla del libro no se contradice ni en la curva",
       _la_pantalla_del_libro_no_se_contradice_ni_en_la_curva)


def _las_frases_no_se_parten_en_las_abreviaturas():
    """Lo que se le ensena a una persona no puede salir a medias.

    `scoring.SENT_RE` corta en cada punto -es el partidor con el que se entreno
    el modelo y no se toca-, pero `ui` lo usaba para la frase de la practica de
    voz y para el contexto que VIAJA A OPENAI. Medido sobre cuatro libros: 13,1 %
    de las candidatas de *Orgullo y prejuicio* eran fragmentos, y la practica de
    voz ofrecia `on the afternoon of May 7, 1915.`, que es media frase.
    """
    casos = [
        ("It was 2 p.m. on the afternoon of May 7, 1915. The ship sank.",
         "It was 2 p.m. on the afternoon of May 7, 1915."),
        ("The advent of Mr. Collins was perfect. She smiled.",
         "The advent of Mr. Collins was perfect."),
        ("She saw Mrs. Bennet at the door. He left.",
         "She saw Mrs. Bennet at the door."),
        ("Dr. Watson arrived at St. Mary's at 9 a.m. today. It rained.",
         "Dr. Watson arrived at St. Mary's at 9 a.m. today."),
    ]
    malos = []
    for texto, esperada in casos:
        salen = ui._oraciones(texto)
        if not salen or salen[0] != esperada:
            malos.append(f"{texto[:40]!r} -> {salen[:2]}")
    assert not malos, malos

    # Y que el partidor del modelo NO se ha tocado: es el del entrenamiento.
    assert scoring_mod.SENT_RE.pattern == r"[^.!?]+[.!?]+|[^.!?]+$", \
        "alguien cambio SENT_RE, que es el partidor con el que se entreno el v4"

    # Una frase que empieza donde acaba otra no vale para leer en voz alta.
    assert not ui._empieza_entera("” thought Alice to herself, after such a fall")
    assert not ui._empieza_entera("on the afternoon of May 7, 1915.")
    assert ui._empieza_entera("It was 2 p.m. on the afternoon of May 7, 1915.")

    # Y el titulillo en versales no viaja pegado a la frase.
    assert ui._sin_encabezado(
        "PROLOGUE PROLOGUE It was two in the afternoon of a day in May."
    ).startswith("It was two"), "el encabezado sigue pegado"

    # Y por el BOTON, que es el camino que ve el lector. Con el partidor
    # viejo la candidata seria `She said that the advent of Mr.`: siete
    # palabras y empieza en mayuscula, asi que pasa los dos filtros y acaba
    # en la caja para leer en voz alta.
    class Cap:
        titulo = "CHAPTER I"
        # La primera frase tiene diez palabras, que cae dentro del 6-25 que
        # exige el boton. Con el partidor viejo se corta en `Mr.` y deja
        # `She said that the advent of Mr.`: siete palabras y empieza en
        # mayuscula, asi que pasa los dos filtros igual.
        texto = ("She said that the advent of Mr. Collins was perfect. "
                 "Everyone in the house agreed with her that same morning, "
                 "and nobody could have arranged it better than her own dear "
                 "sister had arranged it.")
        palabras = 40

    class Libro:
        titulo, autor = "Abreviaturas", "Autor"
        capitulos = [Cap()]
        palabras = 40

    ofrecida = ui._frase_del_capitulo(Libro(), 0)
    v = ofrecida if isinstance(ofrecida, str) else (
        ofrecida.get("value") if isinstance(ofrecida, dict) else "")
    assert v, "el boton no ofrecio ninguna frase"
    assert not str(v).rstrip().endswith(("Mr.", "Mrs.", "Dr.", "St.")), (
        f"el boton ofrece un fragmento cortado en una abreviatura: {v!r}")
    assert "Collins" in str(v), f"la frase llega partida: {v!r}"

    return f"{len(casos)} abreviaturas respetadas, SENT_RE intacto y el boton entero"


prueba("las frases no se parten en las abreviaturas",
       _las_frases_no_se_parten_en_las_abreviaturas)


def _la_ficha_no_promete_una_pronunciacion_que_no_existe():
    """Y avisa cuando la acepcion es dudosa de verdad.

    Dos fallos que se veian a la vez en la misma ficha, medidos sobre el prologo
    de *The Secret Adversary*:

    - "torpedoes", en una frase sobre un barco torpedeado, salia como "An
      electric ray of the genus Torpedo" con afinidad 0,38 y SIN aviso, porque
      el umbral estaba en 0,35. Y esa acepcion se guarda en el cuaderno.
    - El aviso decia "la pronunciacion de arriba esta generada" cuando no hay
      ninguna: sin clave no se genera audio, y el diccionario solo trae IPA para
      el 2,3 % de las palabras.
    """
    from lexicon import ResultadoLexico

    def resultado(**kw):
        base = dict(
            palabra_superficie="torpedoes", oracion="struck by two torpedoes",
            lema="torpedo", lema_buscado="torpedo", pos_spacy="NOUN",
            categoria="noun", sentido="An electric ray of the genus Torpedo.",
            etiquetas_sentido=[], similitud=0.38, n_sentidos_candidatos=15,
            ipa_uk=None, ipa_us=None, audio_uk=None, audio_us=None,
            audio_generado=False, definicion_contextual=None,
            explicacion_gramatical=None, explicacion_adaptada=None,
            ejemplo_simplificado=None, banda_lector="intermedio",
            frecuencia_zipf=2.9, desde_cache=False,
            avisos=["sin audio en el diccionario"])
        base.update(kw)
        return ResultadoLexico(**base)

    assert ui.AFINIDAD_DUDOSA >= 0.40, (
        f"el umbral de duda bajo a {ui.AFINIDAD_DUDOSA}: con 0,35, 'torpedoes' "
        f"(0,38) salia como el pez electrico sin un solo aviso")

    sin_nada = ui._ficha(resultado(), "es")
    assert "pronunciación de arriba" not in sin_nada, \
        f"promete una pronunciacion que no existe: {sin_nada[:200]}"
    assert "no hay pronunciación" in sin_nada, sin_nada[:200]
    assert "confianza" in sin_nada.lower() or "dudosa" in sin_nada.lower(), \
        f"afinidad 0,38 y ningun aviso de duda: {sin_nada[:220]}"

    # Con audio generado de verdad, el aviso de siempre sigue saliendo.
    con_audio = ui._ficha(resultado(audio_generado=True, ipa_uk="/x/"), "es")
    assert "pronunciación de arriba" in con_audio, con_audio[:200]
    return "sin audio no promete audio, y 0,38 avisa"


prueba("la ficha no promete una pronunciacion que no existe",
       _la_ficha_no_promete_una_pronunciacion_que_no_existe)


# --- S6: los veintidos mutantes que sobrevivieron a la auditoria 15 --------
#
# De 30 mutantes, 22 vivieron. Seis de ellos daban a TODOS los visitantes los
# datos de uno -la sesion de pago, la estanteria, la voz, el perfil-, y las
# pruebas que vigilaban eso miraban el CUERPO de los manejadores buscando
# `_archivo_lector(..., peticion)`: quitar el argumento en la llamada tambien
# quita el patron, asi que el manejador mutado dejaba de vigilarse solo.
#
# Lo que sigue no mira codigo: pone dos visitantes y comprueba que lo que
# escribe uno no lo lee el otro.

titulo("La red que faltaba (auditoria 15)")


class _Visitante:
    """Una peticion de Gradio con identidad de navegador y direccion propias."""

    def __init__(self, sesion, ip="10.0.0.1"):
        self.session_hash = sesion
        self.headers = {"x-forwarded-for": ip}
        self.client = type("X", (), {"host": ip})()


def _la_sesion_de_pago_es_de_cada_visitante():
    """Entrar con un perfil no puede abrirle la puerta a los demas.

    `_sesion_de` devolviendo `"local"` para todos -un mutante de una linea-
    pasaba las 276 pruebas: el que entra paga, y todo el que llegue despues
    gasta su cupo sin escribir una contrasena.

    Y la promesa de la otra direccion tambien se comprueba aqui, porque son la
    misma linea: recargar la pagina NO cierra la sesion. Gradio estrena
    `session_hash` en cada carga, asi que la identidad tiene que venir del
    navegador.
    """
    def dentro():
        antes = dict(ui._CODIGO_SESION)
        ui._CODIGO_SESION.clear()
        try:
            primera = _Visitante("s-antes-de-f5")
            recarga = _Visitante("s-despues-de-f5")
            otro = _Visitante("s-otro-visitante")
            # Las dos primeras son el MISMO navegador; la tercera, otro.
            ui._registrar_lector("navegador-de-ana", primera)
            ui._registrar_lector("navegador-de-ana", recarga)
            ui._registrar_lector("navegador-de-beto", otro)

            assert ui._sesion_de(primera) == ui._sesion_de(recarga), (
                "recargar cambia la sesion de pago: hay que volver a entrar "
                "cada F5, y eso es teclear la contrasena delante del profesor")
            assert ui._sesion_de(primera) != ui._sesion_de(otro), (
                "dos navegadores distintos comparten sesion de pago")

            dicho = ui._entrar("jefe", "LLAVE-A", primera)
            assert "jefe" in dicho, dicho
            assert ui._codigo_de(recarga) == ui._codigo_de(primera), (
                "la sesion de pago no sobrevive a recargar")
            assert ui._codigo_de(otro) is None, (
                "el perfil de pago de uno vale para todos: quien entre "
                "segundo gasta el cupo del primero sin dar contrasena")
            return "la sesion de pago aguanta un F5 y no se contagia"
        finally:
            ui._CODIGO_SESION.clear()
            ui._CODIGO_SESION.update(antes)

    return _con_codigos(lambda: _con_nube(dentro))


prueba("la sesion de pago es de cada visitante",
       _la_sesion_de_pago_es_de_cada_visitante)


def _la_estanteria_la_voz_y_el_perfil_son_de_cada_lector():
    """Los otros cinco manejadores que escriben, por el camino del lector.

    `_mis_libros`, `_abrir`, `_debiles`, `_practicar` y `_desde_muestra`
    leian y escribian sin `peticion` en cinco mutantes distintos, y ninguna
    prueba se enteraba. Aqui A hace las tres cosas y B no ve ninguna.
    """
    import voz as voz_mod

    class _Ev:
        puntuacion = 62.0
        palabras_objetivo = ["the", "zarzaparrilla"]
        palabras_falladas = ["zarzaparrilla"]
        transcripcion = "the zarzaparrilla"

    class _Sesion:
        evaluacion = _Ev()
        transcripcion_ok = True
        transcripcion = "the zarzaparrilla"
        correccion = None
        audio_correcto = None

    class _FalsoPuntuador:
        @staticmethod
        def puntuar(texto):
            return type("R", (), {"puntuacion": 1.2, "banda": "intermedio",
                                  "n_bloques": 1, "confianza": "alta"})()

    def dentro():
        a, b = _Visitante("estante-a"), _Visitante("estante-b")
        ui._registrar_lector("navegador-a", a)
        ui._registrar_lector("navegador-b", b)
        ui._CODIGO_SESION[ui._sesion_de(a)] = "jefe:LLAVE-A"
        ui._CODIGO_SESION[ui._sesion_de(b)] = "jefe:LLAVE-A"

        # 1) La estanteria. A abre un libro; B no lo tiene en la suya.
        ruta = escribir("libro_solo_de_a.txt",
                        "The lantern swung above the quiet harbour wall. " * 120)
        ui._abrir(ruta, a)
        mios = str(ui._mis_libros(a))
        suyos = str(ui._mis_libros(b))
        assert "libro_solo_de_a" in mios or "lantern" in mios.lower(), \
            f"A no ve su propio libro en la estanteria: {mios[:160]}"
        assert "libro_solo_de_a" not in suyos, \
            "B ve la estanteria de A: un solo biblioteca.json para todos"

        # 2) La voz. `voz.practicar` se dobla para no pagar ni grabar nada:
        # lo que se prueba es DONDE se apunta el fallo, no como se evalua. Y la
        # clave se finge, porque desde la auditoria 16 `_practicar` se corta
        # antes si no la hay.
        viejo_practicar = voz_mod.practicar
        viejo_falta = config_mod.falta
        try:
            config_mod.falta = lambda: []
            voz_mod.practicar = lambda *a_, **k_: _Sesion()
            dicho = ui._practicar(escribir("audio_falso.wav", b"RIFF"),
                                  "the zarzaparrilla", a)
            assert "62" in str(dicho[1]), (
                f"la practica no llego a evaluar nada: {str(dicho[1])[:200]}")
        finally:
            voz_mod.practicar = viejo_practicar
            config_mod.falta = viejo_falta
        mias = str(ui._debiles(a))
        suyas = str(ui._debiles(b))
        assert "zarzaparrilla" in mias, \
            f"A no ve la palabra que acaba de fallar: {mias[:160]}"
        assert "zarzaparrilla" not in suyas, \
            "B ve los puntos debiles de A: una sola voz.db para todos"

        # 3) El perfil por muestra.
        viejo_p = ui.puntuador
        try:
            ui.puntuador = lambda: _FalsoPuntuador()
            ui._desde_muestra(None, "Ana",
                              "The harbour was quiet and the boats were still. " * 40,
                              a)
        finally:
            ui.puntuador = viejo_p
        assert perfil_mod.cargar(ui._archivo_lector("perfil.json", a)) is not None, \
            "A no guardo su perfil"
        assert perfil_mod.cargar(ui._archivo_lector("perfil.json", b)) is None, \
            "B hereda el perfil de A: un solo perfil.json para todos"
        return "estanteria, voz y perfil separados por lector"

    return _con_codigos(lambda: _con_nube(dentro))


prueba("la estanteria, la voz y el perfil son de cada lector",
       _la_estanteria_la_voz_y_el_perfil_son_de_cada_lector)


def _el_resumen_devuelve_el_uso_cuando_no_sale_a_la_red():
    """Las tres salidas de `_de_que_trata`, y cual de ellas cobra.

    La prueba grande del cupo solo llegaba a una: para cuando corre, el
    consultor ya esta construido, asi que la rama del constructor roto y las
    de `sin_red` / `sin_pasajes` no se recorrian nunca. Tres mutantes vivos.

    La regla es la de `cuentas.py`, y es de una linea: **el cupo baja si y
    solo si la peticion sale a la red.**
    """
    def dentro():
        viejo_cons, viejo_sin = ui.consultor, ficha_mod.sinopsis
        viejo_falta = config_mod.falta
        # Cuenta PROPIA y con sitio de sobra: con la compartida, otra prueba de
        # la suite puede haberle gastado el cupo y entonces el manejador se va
        # por la puerta de "no puedes pagar" sin llegar a lo que se mide.
        viejo_cuentas = os.environ.get("LITERALEVEL_CUENTAS")
        os.environ["LITERALEVEL_CUENTAS"] = "sofia:CLAVE-S:50"
        pet = _Visitante("resumen-cupo", ip="10.55.55.55")
        ui._CODIGO_SESION[ui._sesion_de(pet)] = "sofia:CLAVE-S"
        gastado = lambda: cuentas_mod.gastado(ui.BASE_DATOS_LECTOR, "sofia")
        malos = []

        class _Cliente:
            pass

        class _Consultor:
            @staticmethod
            def _cliente():
                return _Cliente()

        try:
            config_mod.falta = lambda: []

            # a) El consultor revienta al construirse -el diccionario que
            #    falta en el Space-: no ha salido nada a la red.
            def revienta():
                raise FileNotFoundError("No encuentro el diccionario Kaikki")

            ui.consultor = revienta
            antes = gastado()
            list(ui._de_que_trata(libro_ok, pet))
            if gastado() != antes:
                malos.append("el constructor roto cobro un uso sin salir a la red")

            # b) `sinopsis` dice que no hubo red, o que el libro no daba
            #    pasajes. Tampoco se gasto nada.
            ui.consultor = lambda: _Consultor()
            for causa in ("sin_red", "sin_pasajes"):
                ficha_mod.sinopsis = lambda *a_, **k_: (None, causa)
                antes = gastado()
                list(ui._de_que_trata(libro_ok, pet))
                if gastado() != antes:
                    malos.append(f"«{causa}» cobro un uso sin salir a la red")

            # c) Y al reves, que es la mitad que hace que esto no sea
            #    regalar: si la peticion SALIO y fallo despues, se cobra.
            ficha_mod.sinopsis = lambda *a_, **k_: (None, "fallo")
            antes = gastado()
            list(ui._de_que_trata(libro_ok, pet))
            if gastado() == antes:
                malos.append("una llamada que si salio a la red no cobro nada")
        finally:
            ui.consultor, ficha_mod.sinopsis = viejo_cons, viejo_sin
            config_mod.falta = viejo_falta
            ui._CODIGO_SESION.clear()
            if viejo_cuentas is None:
                os.environ.pop("LITERALEVEL_CUENTAS", None)
            else:
                os.environ["LITERALEVEL_CUENTAS"] = viejo_cuentas
        assert not malos, malos
        return "el resumen cobra si y solo si sale a la red"

    return dentro()


prueba("el resumen devuelve el uso cuando no sale a la red",
       _el_resumen_devuelve_el_uso_cuando_no_sale_a_la_red)


def _medir_un_capitulo_no_puntua_la_licencia():
    """El boton «¿Como de dificil es este capitulo?» mide PROSA.

    Quitar el `ficha.sin_licencia` de esa linea no rompia nada: el capitulo se
    medía con los dos parrafos legales de Gutenberg dentro, que son ingles
    juridico y arrastran la dificultad hacia arriba. El lector veia C2 en un
    capitulo de novela juvenil.
    """
    visto = []

    class _Espia:
        @staticmethod
        def puntuar(texto):
            visto.append(texto)
            return type("R", (), {"puntuacion": 1.0, "banda": "intermedio",
                                  "n_bloques": 3, "confianza": "alta"})()

    class _Cap:
        titulo = "CHAPTER I"
        texto = ("*** START OF THE PROJECT GUTENBERG EBOOK PRUEBA ***\n"
                 + "The rain fell on the moor and the train ran west. " * 60
                 + "\n*** END OF THE PROJECT GUTENBERG EBOOK PRUEBA ***\n"
                 + "You may copy it, give it away or re-use it under the terms "
                   "of the Project Gutenberg License included with this eBook. "
                   "Redistribution is subject to the trademark license. " * 8)
        palabras = 700

    class _Libro:
        titulo, autor = "Prueba", "Autor"
        capitulos = [_Cap()]
        palabras = 600

    viejo = ui.puntuador
    try:
        ui.puntuador = lambda: _Espia()
        list(ui._medir(_Libro(), 0))
    finally:
        ui.puntuador = viejo

    assert visto, "el boton no llego a puntuar nada"
    medido = visto[-1]
    assert "PROJECT GUTENBERG" not in medido.upper(), (
        "se esta midiendo la licencia junto con el capitulo: "
        f"{medido[:120]!r}")
    assert "Redistribution" not in medido, (
        "el texto legal del final entra en la medicion y sube la dificultad")
    assert "rain fell" in medido, "se ha llevado por delante la prosa tambien"
    return "el capitulo se mide sin la licencia de Gutenberg"


prueba("medir un capitulo no puntua la licencia",
       _medir_un_capitulo_no_puntua_la_licencia)


def _el_recorte_va_dentro_del_sumatorio():
    """§2.1 del documento: cada ventana se recorta a 0..5 ANTES de promediar.

    Quitar ese `np.clip` no rompia ninguna prueba porque el promedio se vuelve
    a recortar al final, y parece lo mismo. No lo es: una ventana que el
    modelo puntua -10 arrastra la media hacia abajo y el recorte final ya no
    puede deshacerlo. Con tres ventanas 5, 5 y -10 la media honesta es 3,33 y
    la rota es 0,00, o sea C2 contra A1 del mismo texto.

    Se prueba con un modelo de mentira, que es lo unico que permite elegir los
    numeros que el de verdad casi nunca da -pero da-.
    """
    import contextlib
    import numpy as np
    import scoring as sc

    crudos = [5.0, 5.0, -10.0]

    class _Tensor:
        def squeeze(self, *a): return self
        def float(self): return self
        def cpu(self): return self
        def numpy(self): return np.array(crudos, dtype=float)

    class _Modelo:
        def __call__(self, **kw):
            return type("O", (), {"logits": _Tensor()})()

    stub = type("P", (), {})()
    stub._torch = type("T", (), {"no_grad": staticmethod(contextlib.nullcontext)})()
    stub.tokenizer = lambda bloques, **kw: {"input_ids": bloques}
    stub.modelo = _Modelo()
    stub.dispositivo = "cpu"

    salida = sc.Puntuador._puntuar_bloques(stub, ["a", "b", "c"])
    assert all(0.0 <= v <= 5.0 for v in salida), (
        f"una ventana sale fuera de la escala interna 0..5: {salida}")
    media = float(np.mean(salida))
    assert abs(media - 10 / 3) < 0.01, (
        f"la media de 5, 5 y -10 recortadas es 3,33 y sale {media:.2f}: el "
        "recorte no esta dentro del sumatorio")
    assert sc.public_band(sc.public_score(media)) != sc.public_band(
        sc.public_score(float(np.mean(crudos)))), \
        "recortar o no recortar por ventana daria la misma banda: el caso no separa"
    return "cada ventana se recorta antes de promediar (5, 5, -10 -> 3,33)"


prueba("el recorte va dentro del sumatorio",
       _el_recorte_va_dentro_del_sumatorio)


def _las_ventanas_son_las_del_entrenamiento():
    """250 palabras por ventana y 8 ventanas por documento, medido en bloques.

    `tests_smoke.py` lo comprobaba contra las propias constantes -"todas las
    ventanas miden `BLOCK_WORDS`"-, que es una cota autorreferente: cambiar la
    constante cambia las dos mitades de la igualdad y la prueba sigue verde.
    Cambiarlas SI importa: el modelo v4 se entreno con estas dos, y con otras
    puntua otra cosa sin avisar.
    """
    import scoring as sc
    mil = " ".join(["word"] * 1000)
    b = sc.fixed_blocks(mil)
    tam = [len(x.split()) for x in b]
    assert tam == [250] * 4, (
        f"1.000 palabras tenian que dar cuatro ventanas de 250 y dan {tam}")

    cinco_mil = " ".join(["word"] * 5000)
    n = len(sc.fixed_blocks(cinco_mil))
    assert n == 8, (
        f"5.000 palabras dan {n} ventanas y el tope del entrenamiento es 8")
    return "cuatro ventanas de 250 en 1.000 palabras, y tope de 8"


prueba("las ventanas son las del entrenamiento",
       _las_ventanas_son_las_del_entrenamiento)


def _la_portada_de_un_txt_se_llama_siempre_igual():
    """"Antes del primer capitulo" no es un titulo bonito: es un contrato.

    `ficha.capitulos_de_cuerpo` descarta la portada por ESE nombre. Cambiarlo
    en `reader` -a "Preambulo", por ejemplo- no rompia nada visible y dejaba la
    portadilla contando como capitulo: el indice del libro pasa a tener un
    capitulo de mas y la curva de dificultad mide la portada.
    """
    # Los capitulos han de pasar de 150 palabras: por debajo, `ficha` los
    # descarta por cortos y la prueba no llegaria a mirar el titulo.
    cuerpo = "The rain fell on the quiet moor and the train ran west. " * 20
    ruta = escribir("con_portada.txt",
                    "Translated by someone. " * 30 + "\n\n"
                    + "CHAPTER I\n" + cuerpo + "\n\n"
                    + "CHAPTER II\n" + cuerpo)
    libro = reader.cargar(ruta)
    titulos = [c.titulo for c in libro.capitulos]
    assert titulos[0] == "Antes del primer capítulo", (
        f"la portada de un .txt se llama {titulos[0]!r} y `ficha` descarta "
        "«Antes del primer capítulo»: ya no la descarta nadie")
    indices = [i for i, _ in ficha_mod.capitulos_de_cuerpo(libro)]
    assert 0 not in indices, (
        f"la portada cuenta como capitulo de cuerpo: {indices}")
    assert len(indices) == 2, f"deberian quedar los dos capitulos: {indices}"
    return "la portada se llama como `ficha` espera y queda fuera del cuerpo"


prueba("la portada de un txt se llama siempre igual",
       _la_portada_de_un_txt_se_llama_siempre_igual)


def _la_tarjeta_del_cuaderno_escapa_el_html():
    """La frase del libro se pinta dentro de un `<div>`, y viene del libro.

    La prueba que habia comprobaba `cuaderno.registrar` -que guarda bien- y no
    la TARJETA, que es donde se pinta. Quitarle el `_html.escape` a la frase
    dejaba que un `.txt` con `<img onerror=...>` ejecutara su script en la
    pestana "Mis palabras" de quien lo hubiera consultado.
    """
    import cuaderno as cuaderno_mod
    pet = _Visitante("cuaderno-html", ip="10.77.77.77")
    ruta = ui._archivo_lector("cuaderno.db", pet)
    cuaderno_mod.registrar(
        palabra="fetters", lema="fetter",
        oracion='He wore <img src=x onerror="alert(1)"> fetters "always".',
        categoria="noun", sentido="A chain.", libro="Prueba", capitulo=1,
        banda="intermedio", zipf=2.8, ruta=ruta)
    html = str(ui._mis_palabras(pet))
    assert "fetters" in html, f"la palabra no llego a la tarjeta: {html[:160]}"
    assert "<img" not in html, "la frase del libro se pinta sin escapar"
    assert "&lt;img" in html, "la frase no aparece escapada por ningun lado"
    assert "onerror=" not in html or "&quot;" in html, \
        "el atributo del libro entra crudo en la tarjeta"
    return "la frase del libro llega escapada a la tarjeta"


prueba("la tarjeta del cuaderno escapa el html",
       _la_tarjeta_del_cuaderno_escapa_el_html)


def _la_tabla_que_ve_el_lector_es_la_del_codigo():
    """La tabla A1-C2 de la pestana Leer es texto, y `_cefr` es codigo.

    La prueba de `_cefr` comprobaba los limites contra numeros escritos en la
    propia prueba, asi que cambiar «1.00 - 1.40» por «1.00 - 1.50» en la tabla
    no rompia nada: el lector compara su cifra con la tabla y encuentra una
    letra distinta de la que le acaba de dar la app.

    Aqui se LEE la tabla y se exige que cada tramo case con `_cefr`.
    """
    import re
    filas = re.findall(r"\|\s*([\d.]+)\s*–\s*([\d.]+)\s*\|\s*\*\*([A-C][12])\*\*",
                       ui._TABLA_CEFR)
    assert len(filas) == 6, f"la tabla ya no tiene seis tramos: {filas}"
    malos = []
    for lo, hi, letra in filas:
        lo, hi = float(lo), float(hi)
        for cifra in (lo, round(hi - 0.01, 2)):
            dicho = ui._cefr(cifra)
            if dicho != letra:
                malos.append(f"la tabla dice {letra} para {cifra:.2f} y "
                             f"la app dice {dicho}")
    assert not malos, malos
    return f"los {len(filas)} tramos de la tabla dicen lo que dice `_cefr`"


prueba("la tabla que ve el lector es la del codigo",
       _la_tabla_que_ve_el_lector_es_la_del_codigo)


def _el_tope_de_subida_es_el_que_se_declara():
    """Un epub es un zip, y sin tope cabe una bomba de descompresion.

    La prueba de `main.py` miraba que apareciera `max_file_size=`, no cuanto
    valia: ponerlo en "2000mb" la pasaba entera.
    """
    assert ui.TAMANO_MAXIMO_SUBIDA == "20mb", (
        f"el tope de subida es {ui.TAMANO_MAXIMO_SUBIDA!r}. Si cambia de "
        "verdad, cambialo aqui a mano: es la unica defensa contra un zip que "
        "se descomprime en gigas")
    fuente = (pathlib.Path(__file__).parent / "main.py").read_text(encoding="utf-8")
    assert "max_file_size=TAMANO_MAXIMO_SUBIDA" in fuente, (
        "`main.py` ya no pasa el tope a Gradio")
    return "20mb, y `main.py` lo pasa"


prueba("el tope de subida es el que se declara",
       _el_tope_de_subida_es_el_que_se_declara)


def _la_puerta_de_entrada_tiene_freno():
    """`compare_digest` no protege de un diccionario de contrasenas.

    El tiempo de respuesta no dice nada, cierto, pero nada impedia probar
    contrasenas corrientes contra `LITERALEVEL_CUENTAS` a la velocidad de la
    red: `caja_clave.submit` esta cableado y no cuesta un centimo. La ficha la
    gasta el intento FALLIDO, no el que acierta.
    """
    def dentro():
        ui._gasto.clear()
        tope = ui.LIMITE_INTENTOS_ENTRAR
        assert 0 < tope <= 30, (
            f"el freno de la puerta esta en {tope}: o no frena, o el dia de "
            "la demo un dedo torpe deja fuera a quien presenta")

        # Acertar no gasta ficha: cinco entradas buenas seguidas.
        bueno = _Visitante("freno-bueno", ip="10.90.90.1")
        for _ in range(5):
            dicho = ui._entrar("jefe", "LLAVE-A", bueno)
            assert "jefe" in dicho, dicho

        malo = _Visitante("freno-malo", ip="10.90.90.2")
        for i in range(tope):
            dicho = ui._entrar("jefe", f"INVENTADA-{i}", malo)
            assert "No he podido entrar" in dicho, (i, dicho)
        cerrado = ui._entrar("jefe", "OTRA-MAS", malo)
        assert "Demasiados intentos" in cerrado, (
            f"tras {tope} intentos fallidos se puede seguir probando: {cerrado}")
        # Y con la puerta cerrada no se comprueba nada, ni siquiera la buena:
        # si no, el freno seria un oraculo de contrasenas correctas.
        assert "Demasiados intentos" in ui._entrar("jefe", "LLAVE-A", malo), \
            "la puerta cerrada sigue comprobando contrasenas"
        # El de al lado no paga lo que hizo este: el cubo es por IP.
        otra_ip = _Visitante("freno-vecino", ip="10.90.90.3")
        assert "jefe" in ui._entrar("jefe", "LLAVE-A", otra_ip), \
            "un solo cubo para todas las IP: uno bloquea a los demas"
        return f"{tope} intentos fallidos por IP y hora; acertar no gasta ficha"

    try:
        return _con_codigos(dentro)
    finally:
        ui._gasto.clear()
        ui._CODIGO_SESION.clear()


prueba("la puerta de entrada tiene freno",
       _la_puerta_de_entrada_tiene_freno)


def _la_ip_no_se_inventa_y_el_freno_va_tambien_por_usuario():
    """Revision de api.py en 2a49bf2, hallazgo 1: la IP salia del PRIMER valor
    de x-forwarded-for, que escribe el cliente. Cambiandolo en cada intento no
    habia freno de contrasenas ni tope por hora."""
    # Los proxies añaden al final: se usa la ultima direccion publica.
    assert ui._ip(_Pet(ip="1.2.3.4, 203.0.113.9")) == "203.0.113.9"
    assert ui._ip(_Pet(ip="8.8.8.8, 203.0.113.9, 10.0.0.2")) == "203.0.113.9"
    assert ui._ip(_Pet(ip="basura, 10.0.0.2")) == "10.0.0.2"
    viejo = ui._SALTOS_PROXY
    try:
        ui._SALTOS_PROXY = "2"
        assert ui._ip(_Pet(ip="1.1.1.1, 2.2.2.2, 3.3.3.3")) == "2.2.2.2"
        ui._SALTOS_PROXY = "0"
        assert ui._ip(_Pet(ip="1.1.1.1", host="198.51.100.4")) == "198.51.100.4"
    finally:
        ui._SALTOS_PROXY = viejo

    def dentro():
        ui._gasto.clear()
        # 1) Inventarse el principio de la cabecera no da intentos nuevos.
        for i in range(ui.LIMITE_INTENTOS_ENTRAR):
            falso = _Visitante(f"spoof-{i}", ip=f"{i + 1}.9.9.9, 203.0.113.60")
            assert "No he podido entrar" in ui._entrar("jefe", f"MAL-{i}", falso), i
        otro_falso = _Visitante("spoof-ultimo", ip="77.7.7.7, 203.0.113.60")
        assert "Demasiados intentos" in ui._entrar("jefe", "MAL-X", otro_falso), \
            "cambiando x-forwarded-for se sigue probando contraseñas"

        # 2) Por usuario: muchas IP de verdad contra el MISMO usuario tambien paran.
        ui._gasto.clear()
        tope_u = ui.LIMITE_INTENTOS_USUARIO
        assert ui.LIMITE_INTENTOS_ENTRAR < tope_u <= 30, tope_u
        for i in range(tope_u):
            v = _Visitante(f"red-{i}", ip=f"198.51.100.{i + 1}")
            assert "No he podido entrar" in ui._entrar(" JEFE ", f"MAL-{i}", v), i
        nueva = _Visitante("red-nueva", ip="198.51.100.200")
        assert "Demasiados intentos" in ui._entrar("jefe", "MAL-Y", nueva), \
            "con una IP distinta por intento no hay freno para ese usuario"
        # El freno no dice si el usuario existe: otro usuario, aunque no exista,
        # recibe el mensaje normal desde una IP limpia.
        assert "No he podido entrar" in ui._entrar("nadie", "MAL-Z", nueva)
        return f"ip de la derecha; {ui.LIMITE_INTENTOS_ENTRAR} por ip y {tope_u} por usuario"

    try:
        return _con_codigos(dentro)
    finally:
        ui._gasto.clear()
        ui._CODIGO_SESION.clear()


prueba("la ip no se inventa y el freno va tambien por usuario",
       _la_ip_no_se_inventa_y_el_freno_va_tambien_por_usuario)


def _un_epub_que_se_descomprime_a_gigas_no_se_abre():
    """Revision de api.py en 2a49bf2, hallazgo 2: el tope de subida mide el zip
    comprimido y `reader` descomprimia sin mirar. Sin crear una bomba de verdad:
    se baja el tope a 64 KB y se prueba con un zip de pocos KB."""
    import zipfile
    r = ui.reader
    opf = ('<package><metadata><dc:title>Prueba</dc:title></metadata>'
           '<manifest><item id="c1" href="c1.xhtml"/></manifest>'
           '<spine><itemref idref="c1"/></spine></package>')

    def epub(ruta, cuerpo: bytes):
        with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("content.opf", opf)
            z.writestr("c1.xhtml", cuerpo)

    def no_abre(ruta, motivo):
        try:
            r.cargar(str(ruta))
        except ValueError as e:
            return str(e)
        raise AssertionError(f"se abrio {motivo}")

    viejo = r.MAX_DESCOMPRIMIDO_EPUB
    try:
        r.MAX_DESCOMPRIMIDO_EPUB = 64 * 1024
        normal = TMP / "epub_normal.epub"
        epub(normal, ("<p>" + "word " * 2000 + "</p>").encode())
        assert r.cargar(str(normal)).capitulos, "un epub normal ya no se abre"

        grande = TMP / "epub_grande.epub"
        epub(grande, b"<p>" + b"a " * 200_000 + b"</p>")
        assert grande.stat().st_size < 10_000, grande.stat().st_size
        mensaje = no_abre(grande, "un epub que declara 400 KB con tope de 64 KB")
        assert "MB" in mensaje, mensaje

        # El tamaño declarado miente (100 bytes): manda lo que de verdad sale.
        mentira = TMP / "epub_mentira.epub"
        epub(mentira, b"<p>" + b"a " * 200_000 + b"</p>")
        datos = bytearray(mentira.read_bytes())
        nombre = b"c1.xhtml"
        for firma, campo_tam, campo_nombre, inicio_nombre in ((b"PK\x03\x04", 22, 26, 30),
                                                              (b"PK\x01\x02", 24, 28, 46)):
            i = datos.find(firma)
            while i != -1:
                largo = int.from_bytes(datos[i + campo_nombre:i + campo_nombre + 2], "little")
                if bytes(datos[i + inicio_nombre:i + inicio_nombre + largo]) == nombre:
                    datos[i + campo_tam:i + campo_tam + 4] = (100).to_bytes(4, "little")
                i = datos.find(firma, i + 4)
        mentira.write_bytes(bytes(datos))
        assert ui.reader.zipfile.ZipFile(mentira).getinfo("c1.xhtml").file_size == 100
        no_abre(mentira, "un epub que miente sobre su tamaño")
    finally:
        r.MAX_DESCOMPRIMIDO_EPUB = viejo
    return "tope por lo declarado y por lo leido de verdad"


prueba("un epub que se descomprime a gigas no se abre",
       _un_epub_que_se_descomprime_a_gigas_no_se_abre)


def _la_clave_de_analisis_lleva_el_texto():
    """Revision de api.py en 2a49bf2, hallazgo 4: la clave de la curva y la
    sinopsis no llevaba el texto y la carpeta es comun. Un libro subido con el
    titulo y los recuentos de uno del catalogo escribia lo que veian todos."""
    R = ui.reader

    def libro(final, id_catalogo=None):
        l = R.Libro("pg1342.txt", "Austen", [R.Capitulo("Chapter I", "word " * 100 + final)])
        if id_catalogo:
            l.id_catalogo = id_catalogo
        return l

    alfa, omega = libro("alpha"), libro("omega")
    assert (alfa.palabras, alfa.titulo) == (omega.palabras, omega.titulo)
    assert ui._clave_libro_v3(alfa) == ui._clave_libro_v3(omega), "la prueba ya no reproduce el fallo"
    assert ui._clave_libro(alfa) != ui._clave_libro(omega), "mismo titulo y recuentos, otro texto, misma clave"
    assert ui._clave_libro(alfa) == ui._clave_libro(libro("alpha")), "el mismo texto cambia de clave"

    viejo = ui.RUTA_ANALISIS
    try:
        ui.RUTA_ANALISIS = TMP / "analisis_migracion"
        ui.RUTA_ANALISIS.mkdir(exist_ok=True)
        subido, catalogo = libro("alpha"), libro("alpha", id_catalogo="PG1342")
        v3 = ui._clave_libro_v3(catalogo)
        (ui.RUTA_ANALISIS / f"{v3}.json").write_text(ui.json.dumps(
            {"filas": [{"capitulo": 1, "dificultad": 1.1}], "ventanas": 3, "palabras": 101}),
            encoding="utf-8")
        (ui.RUTA_ANALISIS / f"{v3}-sinopsis.json").write_text(ui.json.dumps(
            {"de_que_trata": "Una novela.", "temas": ["amor"]}), encoding="utf-8")
        # Un libro subido no hereda lo guardado con la clave vieja.
        assert ui._analisis_guardado(subido) is None, "un libro subido hereda la curva vieja"
        assert ui._sinopsis_guardada(subido) is None, "un libro subido hereda la sinopsis vieja"
        # Uno del catalogo, si: no se recalcula lo ya pagado.
        assert ui._analisis_guardado(catalogo)["filas"][0]["dificultad"] == 1.1
        assert ui._sinopsis_guardada(catalogo)["de_que_trata"] == "Una novela."
        assert (ui.RUTA_ANALISIS / f"{ui._clave_libro(catalogo)}-sinopsis.json").is_file()
        assert (ui.RUTA_ANALISIS / f"{v3}-sinopsis.json").is_file(), "se movio en vez de copiarse"
    finally:
        ui.RUTA_ANALISIS = viejo
    return "clave con el texto; el catalogo hereda la v3 y lo subido no"


prueba("la clave de analisis lleva el texto",
       _la_clave_de_analisis_lleva_el_texto)


def _las_frases_no_llevan_comillas_sueltas_ni_cursiva():
    """f4, informe final (captura 18): la oracion de «waistcoat-pocket» salia
    como «” (when she thought it over afterwards…», con la comilla de cierre de
    la frase anterior y los _guiones bajos_ de la cursiva de Gutenberg, y asi se
    guardaba en «Mis palabras». Y en «Leer en voz alta», 107 de 306 candidatas
    de *Alicia* abrian una comilla que no cerraban."""
    texto = ("“Oh dear! Oh dear! I shall be late!” (when she thought it over afterwards, it "
             "occurred to her that she ought to have wondered at this, but at the time it all "
             "seemed quite natural); but when the Rabbit actually _took a watch out of its "
             "waistcoat-pocket_, and looked at it, and then hurried on, Alice started to her feet. "
             "“I wonder how many miles I’ve fallen by this time?” she said aloud. “I must be "
             "getting somewhere near the centre of the earth. Let me see: that would be four "
             "thousand miles down, I think.” She didn’t like it.")
    oraciones = ui._oraciones(texto)
    for o in oraciones:
        assert (o.count("“") + o.count("«")) == (o.count("”") + o.count("»")), o
        assert "_" not in o, o
        assert not o.startswith(("”", "»")), o
    # Un parlamento de UNA oracion conserva sus comillas: la de cierre vuelve a
    # su frase. Uno de VARIAS («“Oh dear! Oh dear! I shall be late!”») queda
    # partido y cada trozo pierde la suya, que ya no tendria pareja.
    assert "“I wonder how many miles I’ve fallen by this time?”" in oraciones, oraciones
    assert "I shall be late!" in oraciones, oraciones
    assert "didn’t" in oraciones[-1], "se toco el apostrofo"
    contexto = ui._oracion_de(texto, "waistcoat-pocket")
    assert contexto.startswith("(when she thought"), contexto
    assert "_" not in contexto and "”" not in contexto, contexto
    assert not ui._empieza_entera("(when she thought it over afterwards, it occurred to her)")
    assert ui._empieza_entera("(It was late.) She ran.")

    # Y sobre los libros de verdad, si estan descargados en esta maquina.
    import glob
    medidos = []
    for nombre in ("pg11.epub", "pg1342.epub"):
        rutas = glob.glob(os.path.expanduser(f"~/.literalevel/**/{nombre}"), recursive=True)
        if not rutas:
            continue
        lib = ui.reader.cargar(rutas[0])
        malas = total = 0
        for c in lib.capitulos:
            for parrafo in ui.re.split(r"\n\s*\n", c.texto):
                for o in ui._oraciones(" ".join(parrafo.split())):
                    total += 1
                    malas += (o.count("“") != o.count("”")) or "_" in o.replace("__", "")
        assert malas == 0, (nombre, malas, total)
        medidos.append(f"{nombre} {total} oraciones")
    return "comillas emparejadas y sin cursiva" + (f" ({'; '.join(medidos)})" if medidos else "")


prueba("las frases no llevan comillas sueltas ni cursiva",
       _las_frases_no_llevan_comillas_sueltas_ni_cursiva)


def _la_ficha_dudosa_sin_explicacion_ofrece_las_principales():
    """f4, captura 21: «on the bank» salia como «A device used to store coins or
    currency», con aviso de dudosa y sin explicacion que lo corrigiera."""
    import lexicon as lexicon_mod   # aqui arriba del archivo aun no esta importado
    base = dict(palabra_superficie="bank", oracion="sitting by her sister on the bank", lema="bank",
                lema_buscado="bank", pos_spacy="NOUN", categoria="noun",
                sentido="A device used to store coins or currency.", etiquetas_sentido=["countable"],
                similitud=0.16, n_sentidos_candidatos=28, ipa_uk=None, ipa_us=None, audio_uk=None,
                audio_us=None, audio_generado=False, explicacion_gramatical=None,
                explicacion_adaptada=None, ejemplo_simplificado=None, banda_lector="intermedio",
                frecuencia_zipf=5.0, desde_cache=False,
                avisos=["acepcion provisional: margen bajo (0.002) frente a otra acepcion: X"])
    principales = ["An institution where one can place and borrow money.",
                   "An edge of river, lake, or other watercourse.",
                   "A row or panel of items stored or grouped together.",
                   "A bench, as for rowers in a galley; also, a tier of oars."]
    sin = ui._ficha(lexicon_mod.ResultadoLexico(**base, definicion_contextual=None,
                                                acepciones_principales=principales), "es")
    assert "Puede ser:" in sin and "An edge of river" in sin, sin
    assert "store coins" not in sin, "sigue enseñando la acepcion elegida"
    assert "Poca confianza" not in sin, "el aviso de la acepcion elegida no aplica si no se enseña"
    con = ui._ficha(lexicon_mod.ResultadoLexico(**base, definicion_contextual="La orilla.",
                                                acepciones_principales=[]), "es")
    assert "Puede ser" not in con and "store coins" in con, con
    en = ui._ficha(lexicon_mod.ResultadoLexico(**base, definicion_contextual=None,
                                               acepciones_principales=principales), "en")
    assert "It may be:" in en, en
    return "puede ser: las principales; con explicacion, la de siempre"


prueba("la ficha dudosa sin explicacion ofrece las principales",
       _la_ficha_dudosa_sin_explicacion_ofrece_las_principales)


def _la_sinopsis_no_recibe_el_final_del_libro():
    """f4, informe final: la sinopsis de Alicia prometia «no destripar el final» y
    hablaba del juicio. El modelo tenia el ultimo capitulo delante: `_pasajes`
    lo mandaba. Lo que no se le da no lo puede contar."""
    import ficha as ficha_mod
    R = ui.reader
    for n in (1, 2, 3, 4, 7, 12, 40):
        caps = [R.Capitulo(f"Chapter {i + 1}", f"capitulo{i} " + "word " * 200) for i in range(n)]
        pasajes = ficha_mod._pasajes(R.Libro("Prueba", "Autor", caps))
        assert pasajes, (n, "sin pasajes")
        usados = [int(p.split()[0].removeprefix("capitulo")) for p in pasajes]
        if n > 1:
            assert n - 1 not in usados, (n, usados, "manda el ultimo capitulo")
        assert max(usados) <= (2 * n) // 3, (n, usados)
        assert len(pasajes) <= ficha_mod._PASAJES, (n, len(pasajes))
    return "principio y desarrollo, nunca el ultimo capitulo"


prueba("la sinopsis no recibe el final del libro",
       _la_sinopsis_no_recibe_el_final_del_libro)


def _la_oracion_larga_se_cita_por_su_clausula():
    """f4: la oracion de «waistcoat-pocket» en Alicia es UNA frase de 107
    palabras y se citaba entera en la ficha y en «Mis palabras»."""
    larga = ("(when she thought it over afterwards, it occurred to her that she ought to have "
             "wondered at this, but at the time it all seemed quite natural); but when the Rabbit "
             "actually took a watch out of its waistcoat-pocket , and looked at it, and then hurried "
             "on, Alice started to her feet, for it flashed across her mind that she had never before "
             "seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning "
             "with curiosity, she ran across the field after it, and fortunately was just in time to "
             "see it pop down a large rabbit-hole under the hedge.")
    assert len(larga.split()) >= 100, len(larga.split())
    frag = ui._fragmento_para_leer(larga, "waistcoat-pocket")
    assert len(frag.replace("…", "").split()) <= 30, frag
    assert "waistcoat-pocket" in frag and "…" in frag, frag
    corta = "The Rabbit took a watch out of its waistcoat-pocket."
    assert ui._fragmento_para_leer(corta, "waistcoat-pocket") == corta
    sin_palabra = ui._fragmento_para_leer(larga, "zzqxvj")
    assert len(sin_palabra.replace("…", "").split()) <= 30, sin_palabra
    # Una sola clausula de mas de 30 palabras: ventana centrada en la palabra.
    sin_comas = " ".join(["word"] * 40 + ["bank"] + ["word"] * 40)
    ventana = ui._fragmento_para_leer(sin_comas, "bank")
    assert "bank" in ventana and len(ventana.replace("…", "").split()) <= 30, ventana
    fuente = pathlib.Path(ui.__file__).read_text(encoding="utf-8")
    assert "_fragmento_para_leer(oracion, palabra)" in fuente.split("def _consultar")[1]
    assert "_fragmento_para_leer(a.oracion, a.palabra)" in fuente.split("def _mis_palabras")[1].split("def _repasar")[0]
    assert "_fragmento_para_leer(a.oracion, a.palabra)" in fuente.split("def _repasar")[1]
    assert "_fragmento_para_leer(str(f['frase'])" in fuente.split("def _mal_pronunciadas")[1]
    return f"107 palabras -> {len(frag.replace('…', '').split())} con la palabra dentro"


prueba("la oracion larga se cita por su clausula",
       _la_oracion_larga_se_cita_por_su_clausula)


def _recargar_no_borra_el_has_entrado_como():
    """La sesion de pago sobrevive a un F5, pero la caja no lo decia.

    El visitante recargaba, veia la caja vacia y sin el «Has entrado como», y
    no tenia forma de saber si seguia dentro hasta que consultaba una palabra
    -y le cobraban-. Asi que volvia a teclear la contrasena por si acaso, que
    es justo lo que no se quiere delante de una camara.
    """
    def dentro():
        ui._CODIGO_SESION.clear()
        ui._gasto.clear()
        primera = _Visitante("f5-antes", ip="10.91.91.1")
        recarga = _Visitante("f5-despues", ip="10.91.91.1")
        ui._registrar_lector("navegador-que-recarga", primera)
        ui._registrar_lector("navegador-que-recarga", recarga)

        assert ui._estado_de_entrada(recarga) == "", \
            "dice «has entrado» sin haber entrado nadie"
        assert "jefe" in ui._entrar("jefe", "LLAVE-A", primera)
        dicho = ui._estado_de_entrada(recarga)
        assert "Has entrado como" in dicho and "jefe" in dicho, (
            f"tras recargar, la caja no dice que sigue dentro: {dicho!r}")

        # Y quien no ha entrado no ve nada, aunque recargue.
        otro = _Visitante("f5-otro", ip="10.91.91.2")
        ui._registrar_lector("otro-navegador", otro)
        assert ui._estado_de_entrada(otro) == "", \
            "le dice a un visitante cualquiera que ha entrado"

        # Y lo que de verdad faltaba: que este CABLEADO. Todo lo de arriba
        # comprueba que la funcion hace su trabajo, y eso se cumple igual si
        # nadie la llama al cargar la pagina. Un mutante que quitara el
        # `.then(_estado_de_entrada, ...)` de `demo.load` pasaba esta prueba
        # entera. Lo caz`o el banco, no yo.
        demo = ui.construir()
        fns = demo.fns
        cableados = [getattr(getattr(f, "fn", None), "__name__", "")
                     for f in (fns.values() if isinstance(fns, dict) else fns)]
        assert "_estado_de_entrada" in cableados, (
            "`_estado_de_entrada` no esta cableada a ningun evento: la funcion "
            "existe y funciona, y al cargar la pagina no la llama nadie")
        return "tras recargar, la caja sigue diciendo con que perfil se entro"

    try:
        return _con_codigos(lambda: _con_nube(dentro))
    finally:
        ui._CODIGO_SESION.clear()


prueba("recargar no borra el has entrado como",
       _recargar_no_borra_el_has_entrado_como)


def _los_dos_botones_de_voz_no_se_pisan():
    """«Corrigeme» y «Mis puntos debiles» escribian en la misma caja.

    Pulsar el segundo borraba la correccion que acababa de costar una llamada
    de pago, y para volver a verla habia que pagar otra.
    """
    import re
    fuente = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(
        encoding="utf-8")
    m_pract = re.search(r"b_practicar\.click\((.*?)\)\n", fuente, re.S)
    m_deb = re.search(r"b_debiles\.click\((.*?)\)\n", fuente, re.S)
    assert m_pract and m_deb, "ya no encuentro los dos botones cableados"
    salidas_pract = set(re.findall(r"[a-z_]+", m_pract.group(1).split("[")[-1]))
    destino_deb = m_deb.group(1).split(",")[-1].strip()
    assert destino_deb, f"no leo el destino de «Mis puntos debiles»: {m_deb.group(1)!r}"
    assert destino_deb not in salidas_pract, (
        f"«Mis puntos debiles» escribe en «{destino_deb}», que es una de las "
        f"salidas de «Corrigeme» ({sorted(salidas_pract)}): pulsar uno borra "
        "lo del otro")
    return f"«Corrigeme» y «Mis puntos debiles» escriben en cajas distintas"


prueba("los dos botones de voz no se pisan",
       _los_dos_botones_de_voz_no_se_pisan)


def _construir_con_perfiles_configurados():
    """La interfaz se monta tambien con la puerta puesta, que es el Space.

    «construir() no carga nada pesado» corre SIN `LITERALEVEL_CUENTAS`, asi que
    toda la caja de entrada -que solo existe si hay perfiles- se quedaba sin
    montar en las pruebas. Encadenar `_estado_de_entrada` a `demo.load` la
    rompio, y de eso me entere por la otra prueba, la del caso sin puerta:
    desplegado habria arrancado en error y en local no.
    """
    def dentro():
        demo = ui.construir()
        n = len(demo.blocks)
        assert n > 0, "la interfaz con puerta sale vacia"
        return f"{n} bloques con la puerta puesta"

    return _con_codigos(dentro)


prueba("construir con perfiles configurados",
       _construir_con_perfiles_configurados)


def _la_casilla_de_acercar_al_nivel_hace_algo():
    """«Acercar los resultados a mi nivel» pesa 0,3; ponerlo a 0 no rompia nada.

    Ninguna prueba llamaba a `buscar` con perfil, asi que la casilla podia
    quedarse sin efecto y la pestana seguia prometiendo que lo tiene. Aqui el
    parecido se deja CLAVADO -todos los libros empatan- para que lo unico que
    pueda ordenar la lista sea el nivel.
    """
    import numpy as np
    import pandas as pd
    import catalogo as cat_mod

    df = pd.DataFrame({
        "id": ["PG1", "PG2", "PG3"], "title": ["Uno", "Dos", "Tres"],
        "author": ["A", "B", "C"], "nivel_cefr": ["A1", "B2", "C2"],
        "hook": ["de que va", "de que va", "de que va"], "downloads": [1, 1, 1]})
    cat = object.__new__(cat_mod.Catalogo)
    cat.df = df
    # `embeddings` es una propiedad perezosa que codificaria el catalogo con
    # MiniLM; se rellena su respaldo para que devuelva la matriz de mentira.
    cat._emb = np.full((3, 4), 0.5, dtype=np.float32)
    cat._fichas = ["uno a", "dos b", "tres c"]
    cat._modelo_emb = lambda: type("M", (), {"encode": staticmethod(
        lambda x, **k: np.full((1, 4), 0.5, dtype=np.float32))})()

    facil, _ = cat.buscar("algo cualquiera", nivel_lector=0.0, n=3)
    dificil, _ = cat.buscar("algo cualquiera", nivel_lector=2.0, n=3)
    assert facil and dificil, "la busqueda no devuelve nada con el montaje"
    assert facil[0].nivel == "A1", (
        f"con nivel 0,0 el primero es {facil[0].nivel}: la casilla no acerca nada")
    assert dificil[0].nivel == "C2", (
        f"con nivel 2,0 el primero es {dificil[0].nivel}")
    return "con el parecido empatado, manda el nivel: A1 primero y C2 primero"


prueba("la casilla de acercar al nivel hace algo",
       _la_casilla_de_acercar_al_nivel_hace_algo)


def _la_frase_de_voz_no_viaja_entera():
    """T8 promete 300 caracteres, y esa linea no la aseveraba nadie.

    `voz.practicar` transcribe con whisper y genera audio con tts-1: mandar un
    capitulo entero en vez de una frase es caro y ademas no se puede leer en
    voz alta.
    """
    visto = []

    class _Ev:
        puntuacion = 50.0
        palabras_objetivo = ["a"]
        palabras_falladas = []
        transcripcion = "a"

    class _Sesion:
        evaluacion = _Ev()
        transcripcion_ok = True
        transcripcion = "a"
        correccion = None
        audio_correcto = None

    import voz as voz_mod
    viejo = voz_mod.practicar
    viejo_falta = config_mod.falta
    pet = _Visitante("frase-larga", ip="10.66.66.66")
    try:
        # Con clave fingida: sin ella `_practicar` se corta antes de llamar.
        config_mod.falta = lambda: []
        def espia(ruta, frase, **k):
            visto.append(frase)
            return _Sesion()
        voz_mod.practicar = espia
        ui._practicar(escribir("audio_largo.wav", b"RIFF"), "palabra " * 900, pet)
    finally:
        voz_mod.practicar = viejo
        config_mod.falta = viejo_falta

    assert visto, "la practica no llego a llamar a `voz.practicar`"
    assert len(visto[0]) <= ui.LIMITE_FRASE_VOZ, (
        f"a whisper le viajan {len(visto[0])} caracteres y el tope es "
        f"{ui.LIMITE_FRASE_VOZ}")
    assert ui.LIMITE_FRASE_VOZ == 300, (
        f"el tope de la frase es {ui.LIMITE_FRASE_VOZ} y el documento promete 300")
    return f"a whisper le llegan {len(visto[0])} caracteres, no 6.300"


prueba("la frase de voz no viaja entera",
       _la_frase_de_voz_no_viaja_entera)


def _traer_una_frase_no_devuelve_siempre_la_misma():
    """Practicar dos veces seguidas tiene que ser practicar dos frases.

    Devolver siempre la primera candidata hacia que el boton pareciera roto
    -pulsas y no cambia nada- aunque estuviera haciendo su trabajo. La prueba
    que habia solo medía el largo de lo que devolvia.
    """
    frases = [
        "The rain fell on the moor and the train ran west that morning.",
        "She opened the window and the cold air came into the small room.",
        "He counted the coins twice before he put them back in the drawer.",
        "Nobody in the village had seen the doctor since the end of March.",
    ]

    class _Cap:
        titulo = "CHAPTER I"
        texto = " ".join(frases)
        palabras = len(texto.split())

    class _Libro:
        titulo, autor = "Rotacion", "Autor"
        capitulos = [_Cap()]
        palabras = len(_Cap.texto.split())

    libro = _Libro()
    salidas = []
    for _ in range(3):
        v = ui._frase_del_capitulo(libro, 0)
        salidas.append(v if isinstance(v, str) else str(v.get("value", "")))
    assert all(salidas), f"el boton devolvio algo vacio: {salidas}"
    assert len(set(salidas)) > 1, (
        f"tres pulsaciones y la misma frase: {salidas[0]!r}")
    return f"{len(set(salidas))} frases distintas en tres pulsaciones"


prueba("traer una frase no devuelve siempre la misma",
       _traer_una_frase_no_devuelve_siempre_la_misma)


def _el_vistazo_rapido_muestrea_de_verdad():
    """El vistazo es un vistazo: 30 capitulos y 2 ventanas de cada uno.

    Si deja de muestrear, el boton «Vistazo rápido (unos segundos)» pasa a
    medir el libro entero y tarda minutos con la etiqueta puesta. Ninguna
    prueba lo miraba porque todas evitan cargar el modelo; con un puntuador de
    mentira se puede mirar sin cargarlo.
    """
    medidos, topes = [], []

    class _Espia:
        @staticmethod
        def perfil_de_texto(texto, tope=0):
            medidos.append(texto[:20])
            topes.append(tope)
            return [1.0] * (tope or 5)

    cuerpo = "The rain fell on the moor and the train ran west. " * 20

    class _Cap:
        def __init__(self, n):
            self.titulo, self.texto = f"CHAPTER {n}", cuerpo
            self.palabras = len(cuerpo.split())

    class _Libro:
        titulo, autor = "Vistazo de mentira", "Autor"
        capitulos = [_Cap(i) for i in range(50)]
        palabras = 50 * len(cuerpo.split())

    viejo = ui.puntuador
    try:
        ui.puntuador = lambda: _Espia()
        list(ui._analizar_libro(_Libro(), "rapido"))
    finally:
        ui.puntuador = viejo

    assert medidos, "el vistazo no midio ni un capitulo"
    assert len(medidos) <= ui.RAPIDO_CAPITULOS, (
        f"el vistazo mide {len(medidos)} capitulos de 50 y el tope es "
        f"{ui.RAPIDO_CAPITULOS}: ya no es un vistazo")
    assert len(medidos) == ui.RAPIDO_CAPITULOS, (
        f"mide {len(medidos)} y deberia repartir {ui.RAPIDO_CAPITULOS}")
    assert set(topes) == {ui.RAPIDO_VENTANAS}, (
        f"las ventanas por capitulo son {set(topes)} y no {ui.RAPIDO_VENTANAS}")
    assert (ui.RAPIDO_CAPITULOS, ui.RAPIDO_VENTANAS) == (30, 2), (
        f"el vistazo son {ui.RAPIDO_CAPITULOS}x{ui.RAPIDO_VENTANAS} ventanas; "
        "la pestana anuncia 30 x 2 = 60 y el documento las cronometra")
    return f"{len(medidos)} capitulos x {ui.RAPIDO_VENTANAS} ventanas, de 50"


prueba("el vistazo rapido muestrea de verdad",
       _el_vistazo_rapido_muestrea_de_verdad)


def _la_letra_del_catalogo_se_declara_heredada():
    """La app no puede desmentirse a si misma cuatro clics despues.

    «Sorprendeme» propone diez B2 a un lector de 1,20; el lector abre uno y
    «¿Como de dificil es este capitulo?» le contesta C1. La letra sale del
    catalogo heredado de la v1 y el numero sale del modelo v4, y hasta que el
    catalogo este remedido entero eso no se arregla: lo que si se puede es
    decirlo DONDE se ve la etiqueta, y no solo en el PDF.
    """
    class _L:
        def __init__(self, ident="PG1155", titulo="The Secret Adversary"):
            self.id, self.titulo, self.autor = ident, titulo, "Christie"
            self.nivel, self.gancho, self.descargas = "B2", "detectives", 10
            self.similitud = self.afinidad = 0.6
            self.puntuacion_nivel = 1.2

    p = perfil_mod.Perfil(nivel=1.20, banda="intermedio",
                          origen="cuestionario", creado="", nombre="Ana")
    clave = "sin medir con el modelo"
    malos = []

    class _CatalogoDoble:
        @staticmethod
        def por_nivel(*a, **k):
            return [_L()]

        @staticmethod
        def buscar(*a, **k):
            return [_L()], ""

    viejo = ui.catalogo
    try:
        ui.catalogo = lambda: _CatalogoDoble()
        pantalla, _ = ui._recomendar(p, 10)
        if clave not in pantalla:
            malos.append(f"«Sorprendeme» no avisa: {pantalla[-200:]!r}")
        pantalla, _ = ui._buscar(p, "detectives victorianos", True, 10)
        if clave not in pantalla:
            malos.append(f"el buscador no avisa: {pantalla[-200:]!r}")

        # Y con aviso del catalogo, el aviso no se come la nota.
        class _ConAviso(_CatalogoDoble):
            @staticmethod
            def buscar(*a, **k):
                return [_L()], "Se descartaron 3 por parecido bajo."
        ui.catalogo = lambda: _ConAviso()
        pantalla, _ = ui._buscar(p, "detectives victorianos", True, 10)
        if clave not in pantalla or "parecido bajo" not in pantalla:
            malos.append(f"el aviso y la nota no caben juntos: {pantalla[-220:]!r}")
    finally:
        ui.catalogo = viejo
    assert not malos, malos
    return "las dos pantallas dicen que la letra es heredada"


prueba("la letra del catalogo se declara heredada",
       _la_letra_del_catalogo_se_declara_heredada)


def _lo_que_mas_se_repite_no_son_muletillas():
    """«Lo que mas se repite: tommy, tuppence, julius, don't, james, think...»

    Cuatro de diez puestos gastados en palabras que estan en todas las
    novelas. Y con el apostrofo tipografico -el que usa Gutenberg- no bastaba
    con anadir `don't` a la lista: `don’t` no casaba. Ademas, `[A-Za-z]`
    partia «Svidrigaïlov» en «svidriga» y «lov», y las dos mitades subian a la
    lista como si fueran palabras del libro.
    """
    relleno = ("Tuppence said that Svidrigaïlov thought so too. "
               "She don’t think she got down. ") * 15

    class _Cap:
        titulo = "CHAPTER I"
        texto = relleno
        palabras = len(relleno.split())

    class _Libro:
        titulo, autor = "Muletillas", "Autor"
        capitulos = [_Cap()]
        palabras = len(relleno.split())

    d = ficha_mod.caracteristicas(_Libro()).distintivas
    assert "tuppence" in d, f"el nombre del personaje no sale: {d}"
    assert "svidrigaïlov" in d, (
        f"el nombre con tilde llega partido o no llega: {d}")
    assert not any(x in d for x in ("svidriga", "lov")), (
        f"el nombre sigue partido en dos: {d}")
    muletillas = [x for x in ("don't", "don’t", "think", "got", "down",
                              "said", "too", "she") if x in d]
    assert not muletillas, (
        f"siguen subiendo muletillas a «lo que mas se repite»: {muletillas}")
    return f"salen los nombres y no las muletillas: {', '.join(d[:4])}"


prueba("lo que mas se repite no son muletillas",
       _lo_que_mas_se_repite_no_son_muletillas)


# --- La auditoria 16, la del dia antes de grabar ---------------------------
#
# Cuatro serios que nadie cubria, y tres de ellos se ven en camara.

titulo("Lo que encontro la auditoria 16")


def _abrir_un_libro_no_pinta_un_error_rojo():
    """«Value: 1 is not in the list of choices: []», en el paso estrella.

    Abrir un libro desde el buscador cambia `est_libro` y `cap` a la vez, y el
    indice tenia DOS manejadores: uno que ponia sus opciones y otro que ponia
    su valor. Si el valor llegaba primero -o con el numero de capitulo del
    libro anterior, que tiene menos capitulos- Gradio pintaba un recuadro rojo
    de Error. El libro se abria bien; lo que no puede es salir un Error rojo
    delante de una camara.

    Reproducido en el Space el 11 de septiembre de 2026, dos veces de dos.
    """
    class _Cap:
        def __init__(self, n):
            self.titulo, self.texto = f"CHAPTER {n}", "word " * 200
            self.palabras = 200

    class _Libro:
        def __init__(self, n):
            self.titulo, self.autor = f"Libro de {n}", "Autor"
            self.capitulos = [_Cap(i) for i in range(n)]
            self.palabras = 200 * n

    def opciones_y_valor(upd):
        d = upd if isinstance(upd, dict) else getattr(upd, "__dict__", {})
        return d.get("choices"), d.get("value")

    # 1. El capitulo del libro ANTERIOR no puede quedarse seleccionado en el
    #    indice del nuevo, que tiene menos capitulos.
    ops, val = opciones_y_valor(_indice := ui._indice_de(_Libro(12), 40))
    indices = [o[1] if isinstance(o, (list, tuple)) else o for o in (ops or [])]
    assert val is None or val in indices, (
        f"el indice queda seleccionado en {val} y sus opciones son {indices[:5]}…: "
        "eso es el recuadro rojo de Gradio")

    # 2. Y los casos torcidos que Gradio sabe mandar. El valor tiene que ser
    #    **None**, no «cualquiera que este dentro de rango»: con un respaldo
    #    de `0` el indice marcaria el capitulo 1 y, viniendo de `indice.select`,
    #    te mandaria al capitulo 1 de un libro que acabas de abrir por otro
    #    sitio. Un mutante con `else 0` pasaba la version anterior de esto.
    for actual in (None, -1, 99, float("nan"), [1], "hola"):
        ops, val = opciones_y_valor(ui._indice_de(_Libro(5), actual))
        assert val is None, (
            f"con actual={actual!r} el indice se queda marcado en {val!r}: "
            "si no vale, no se marca nada")
    # Un numero en texto SI vale -Gradio los manda asi- y marca su capitulo.
    _, val = opciones_y_valor(ui._indice_de(_Libro(5), "3"))
    assert val == 3, f"«3» tendria que marcar el capitulo 4, y sale {val!r}"

    # 3. Un valor bueno SI se conserva: si no, el indice no marcaria nunca
    #    donde estas y esta prueba se cumpliria sola.
    ops, val = opciones_y_valor(ui._indice_de(_Libro(12), 3))
    assert val == 3, f"un capitulo valido tiene que quedar marcado, y sale {val!r}"

    # 3b. Y los DOS mandos dicen exactamente lo mismo. Son dos vistas del
    #     mismo estado -el desplegable de arriba y el indice de abajo- y el
    #     comentario del codigo lo promete; hasta ahora no lo probaba nadie, y
    #     reconstruir las etiquetas en `_abrir` con otro formato pasaba entero.
    ruta_dos = escribir(
        "dos_mandos.txt",
        "CHAPTER I\n" + "The rain fell on the quiet moor and the train ran west. " * 20
        + "\n\nCHAPTER II\n" + "She opened the window and the cold air came in. " * 20)
    libro_dos, upd_cap, _, _ = ui._abrir(ruta_dos)
    assert libro_dos is not None, "no se pudo abrir el libro de dos capitulos"
    ops_cap, _ = opciones_y_valor(upd_cap)
    ops_ind, _ = opciones_y_valor(ui._indice_de(libro_dos, 0))
    assert ops_cap == ops_ind, (
        f"el desplegable y el indice ofrecen etiquetas distintas del mismo "
        f"libro:\n  desplegable {ops_cap}\n  indice      {ops_ind}")

    # 4. Y el descargador no puede VACIAR el desplegable mientras trabaja.
    #    Es el disparador de verdad, aislado en el Space: con un libro ya
    #    abierto -o sea siempre que se haya leido algo antes- quitarle las
    #    opciones a un componente que conserva su valor pinta el Error rojo.
    def choices_de(upd):
        d = upd if isinstance(upd, dict) else getattr(upd, "__dict__", {})
        return d.get("choices", "sin tocar")

    for entrada, etiqueta in ((None, "sin elegir libro"),
                              ("", "con el id vacio")):
        primero = next(iter(ui._abrir_del_catalogo(entrada)))
        assert choices_de(primero[1]) == "sin tocar", (
            f"{etiqueta}: el descargador vacia el desplegable de capitulos "
            f"({choices_de(primero[1])!r}), y eso borra el indice del libro "
            "que se estaba leyendo y pinta un Error rojo")
        # Y tampoco tira el LECTOR entero: pulsar sin elegir nada no puede
        # dejarte sin el libro que estabas leyendo y con el desplegable
        # lleno de sus capitulos. Mandos vivos sobre un lector vacio.
        assert primero[0] == ui.gr.skip(), (
            f"{etiqueta}: te quita el libro que estabas leyendo ({primero[0]!r})")
        assert primero[2] == ui.gr.skip(), (
            f"{etiqueta}: te borra el texto del libro que estabas leyendo")

    # 4b. Y el ULTIMO yield, el que abre el libro de verdad, tiene que traer
    #     el desplegable LLENO. Dejarlo vacio ahi abre el libro sin desplegable
    #     y sin indice —el paso estrella de la demo, con los dos mandos
    #     muertos— y las siete suites seguian en verde: ninguna pasa por
    #     `_abrir_del_catalogo`. Se dobla la descarga para no salir a la red.
    viejo_bajar = ui._descargar_gutenberg
    try:
        ui._descargar_gutenberg = lambda i: ruta_dos
        ultimo = None
        for tramo in ui._abrir_del_catalogo("PG-de-mentira"):
            ultimo = tramo
    finally:
        ui._descargar_gutenberg = viejo_bajar
    assert ultimo is not None, "el descargador no llego a devolver nada"
    assert ultimo[0] is not None and getattr(ultimo[0], "capitulos", None), (
        f"el descargador no deja el libro abierto: {ultimo[0]!r}")
    ops_fin, val_fin = opciones_y_valor(ultimo[1])
    assert ops_fin and len(ops_fin) == len(ultimo[0].capitulos), (
        f"el libro se abre con el desplegable de capitulos vacio o a medias "
        f"({ops_fin!r}): los dos mandos quedan muertos")
    idx_fin = [o[1] if isinstance(o, (list, tuple)) else o for o in ops_fin]
    assert val_fin in idx_fin, (
        f"el desplegable abre marcando {val_fin!r}, que no esta entre sus "
        f"opciones")

    # Y «Retomar donde lo dejé», que es el mismo camino y se quedo sin arreglar
    # la primera vez. Sus DOS salidas: la de "no has elegido nada" y la de
    # "abriendo". El banco enseno que probar solo la primera no vale: el
    # mutante que vacia el desplegable en la segunda sobrevivia entero.
    for entrada, etiqueta in ((None, "sin elegir"),
                              (escribir("retomar.txt", "word " * 300), "abriendo")):
        primero = next(iter(ui._seguir_leyendo(entrada)))
        assert choices_de(primero[1]) == "sin tocar", (
            f"«Retomar donde lo dejé» ({etiqueta}) vacia el desplegable de "
            "capitulos: pinta el mismo Error rojo siempre que ya hay un libro "
            "abierto")

    # 5. Y NINGUN manejador puede LEER el desplegable de capitulos como
    #    entrada cuando lo que dispara es el cambio de LIBRO. Esta es la
    #    linea del recuadro rojo de verdad, y la anterior no la cubria:
    #    abrir un libro es una generadora, cambia `est_libro` y `cap` a la vez,
    #    y el evento del libro se dispara con el valor VIEJO del desplegable.
    #    Si ese capitulo no existe en el libro nuevo -el 90 de «Karamazov» y
    #    un libro de 24 capitulos- Gradio lo rechaza en `Dropdown.preprocess`,
    #    ANTES de llamar a la funcion, asi que validar dentro no sirve.
    #    `est_libro` es un `gr.State` y su valor vive en el servidor: ese si
    #    llega al dia.
    import re as _re
    fuente2 = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(
        encoding="utf-8")
    for m in _re.finditer(r"est_libro\.change\(([^)]*)\)", fuente2):
        args = m.group(1)
        assert "cap" not in _re.findall(r"[a-z_]+", args), (
            f"`est_libro.change` vuelve a leer el desplegable de capitulos "
            f"({args.strip()}): en una generadora ese valor llega rancio y "
            "Gradio pinta el Error rojo antes de entrar en la funcion")

    # 6. Y NINGUN manejador de los dos mandos puede mandar un valor pelado.
    #    Son `cap` (el desplegable) e `indice` (el radio de abajo), y los dos
    #    tienen `choices`: meterles un valor mientras sus opciones estan vacias
    #    -lo estan un instante, porque `_abrir_del_catalogo` es generadora y su
    #    primer yield las vacia- es exactamente el recuadro rojo.
    import re
    fuente = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(
        encoding="utf-8")
    sueltos = [l.strip() for l in fuente.split("\n")
               if re.search(r"^\s*(cap|indice)\.(change|select)\(lambda", l)]
    assert not sueltos, (
        f"un manejador de los mandos del capitulo manda un valor sin sus "
        f"opciones: {sueltos}")
    # Y que sigan cableados los dos, que si no esta prueba se cumpliria sola.
    for linea in ("cap.change(_indice_de, [est_libro, cap], indice)",
                  "indice.select(_indice_de, [est_libro, indice], cap)"):
        assert linea in fuente, f"falta el cableado: {linea}"
    return "el indice manda opciones y valor juntos, y el valor es de este libro"


prueba("abrir un libro no pinta un error rojo",
       _abrir_un_libro_no_pinta_un_error_rojo)


def _la_practica_de_voz_no_cobra_sin_clave():
    """Sin clave no puede haber llamada, asi que no hay nada que cobrar.

    `_consultar` y `_de_que_trata` ya lo hacian; `_practicar` llamaba a
    `_puede_pagar` sin mirar si habia clave. Con perfiles declarados y la clave
    caducada o borrada del Space -que ya ha pasado aqui-, cada intento de
    pronunciacion descontaba un uso del cupo sin que saliera una peticion. Y es
    ademas la unica de las tres que, a proposito, no devuelve el uso.
    """
    def dentro():
        viejo_cuentas = os.environ.get("LITERALEVEL_CUENTAS")
        viejo_falta = config_mod.falta
        os.environ["LITERALEVEL_CUENTAS"] = "elena:CLAVE-E:20"
        pet = _Visitante("voz-sin-clave", ip="10.33.33.33")
        ui._CODIGO_SESION[ui._sesion_de(pet)] = "elena:CLAVE-E"
        gastado = lambda: cuentas_mod.gastado(ui.BASE_DATOS_LECTOR, "elena")
        audio = escribir("audio_sin_clave.wav", b"RIFF")
        try:
            config_mod.falta = lambda: ["OPENAI_API_KEY"]
            antes = gastado()
            _, dicho, _ = ui._practicar(audio, "the quiet harbour", pet)
            assert gastado() == antes, (
                f"sin clave, la practica cobro {gastado() - antes} uso(s) del "
                "cupo sin que pudiera salir una sola peticion")
            assert "clave" in str(dicho).lower(), (
                f"y ademas no dice por que no se puede: {str(dicho)[:160]}")

            # Con clave si cobra: si no, esta prueba estaria pidiendo que la
            # puerta de pago no cobre nunca.
            config_mod.falta = lambda: []
            antes = gastado()
            ui._practicar(audio, "the quiet harbour", pet)
            assert gastado() > antes, (
                "con clave tampoco cobra: la puerta de pago dejo de cobrar")
            return "sin clave no cobra, con clave si"
        finally:
            config_mod.falta = viejo_falta
            ui._CODIGO_SESION.clear()
            if viejo_cuentas is None:
                os.environ.pop("LITERALEVEL_CUENTAS", None)
            else:
                os.environ["LITERALEVEL_CUENTAS"] = viejo_cuentas

    return dentro()


prueba("la practica de voz no cobra sin clave",
       _la_practica_de_voz_no_cobra_sin_clave)


def _la_ficha_no_promete_un_ritmo_que_no_sabe():
    """El mismo libro y el mismo lector no pueden tener dos tiempos.

    Con perfil y sin la curva calculada, `_ficha_libro` daba por bueno el ritmo
    comodo y lo rotulaba «a tu ritmo de lectura». Calculabas la curva, reabrias
    el libro y decia «(va por encima de tu nivel)» con doce horas mas. Medido
    en vivo sobre *Crime and Punishment* con perfil 1,20: 18 h 52 antes y
    30 h 52 despues.
    """
    class _Cap:
        titulo = "CHAPTER I"
        texto = "The rain fell on the quiet moor and the train ran west. " * 400
        palabras = len(texto.split())

    class _Libro:
        titulo, autor = "Sin medir todavia", "Autor"
        capitulos = [_Cap()]
        palabras = _Cap.palabras

    p = perfil_mod.Perfil(nivel=1.20, banda="intermedio",
                          origen="cuestionario", creado="", nombre="Ana")
    viejo = ui._analisis_guardado
    try:
        # a) Sin analisis: no puede comprometerse con un ritmo.
        ui._analisis_guardado = lambda *a, **k: None
        sin = ui._ficha_libro(_Libro(), p)
        assert "a tu ritmo de lectura" not in sin, (
            f"promete «a tu ritmo» sin haber medido el libro: {sin[:200]}")
        assert sin.count(" y ") >= 1 and "entre" in sin, (
            f"tendria que dar las dos velocidades: {sin[:200]}")
        # Y EN ESE ORDEN: «entre 18 h 52 y 30 h 52», no al reves. Con solo
        # exigir «entre» y « y », un rango invertido pasaba igual.
        c = ficha_mod.caracteristicas(_Libro())
        comodo, exigente_t = ficha_mod.reloj(c.minutos(False)), ficha_mod.reloj(c.minutos(True))
        assert comodo in sin and exigente_t in sin, (
            f"el rango no trae los dos tiempos ({comodo} / {exigente_t}): {sin[:200]}")
        assert sin.index(comodo) < sin.index(exigente_t), (
            f"el rango va al reves: dice «{exigente_t}» antes que «{comodo}»")

        # b) Con analisis y el libro por encima del lector: ahi si se moja.
        ui._analisis_guardado = lambda *a, **k: {
            "filas": [{"capitulo": 1, "dificultad": 1.70, "ventanas": 10}],
            "ventanas": 10, "palabras": _Libro.palabras}
        con = ui._ficha_libro(_Libro(), p)
        assert "va por encima de tu nivel" in con, (
            f"con la curva medida en 1,70 y el lector en 1,20 tendria que "
            f"avisar: {con[:200]}")

        # c) Y con un libro por DEBAJO, el ritmo comodo, que es el otro lado.
        ui._analisis_guardado = lambda *a, **k: {
            "filas": [{"capitulo": 1, "dificultad": 0.60, "ventanas": 10}],
            "ventanas": 10, "palabras": _Libro.palabras}
        facil = ui._ficha_libro(_Libro(), p)
        assert "a tu ritmo de lectura" in facil, (
            f"un libro por debajo de su nivel tendria que ir a ritmo comodo: "
            f"{facil[:200]}")
    finally:
        ui._analisis_guardado = viejo
    return "sin medir da el rango; medido, se moja"


prueba("la ficha no promete un ritmo que no sabe",
       _la_ficha_no_promete_un_ritmo_que_no_sabe)


def _las_sugerencias_de_capitulos_salen_cuando_tocan():
    """«Este libro te queda grande, pero estos capitulos no.»

    Lo que se exige, y por que:
    a) sin perfil, sin curva, o con el libro ya a tu alcance, NO sale nada;
    b) con el libro por encima, salen los capitulos a tu alcance y ninguno de
       los que no lo estan, con indices de ESTE libro y sin seleccion puesta;
    c) un indice que no existe en el libro -un analisis viejo- no se ofrece;
    d) un analisis roto esconde, no revienta;
    e) y esta CABLEADO leyendo solo estados del servidor, con el salto por
       `_indice_de`. Sin (e) todo lo anterior pasa aunque nadie lo llame, y
       leer el desplegable es la puerta del recuadro rojo de la auditoria 17.
    """
    import gradio as gr

    class _Cap:
        def __init__(self, t):
            self.titulo = t
            self.texto = "The rain fell on the quiet moor and the train ran west. " * 400
            self.palabras = len(self.texto.split())

    caps = [_Cap(f"CHAPTER {i}") for i in range(6)]

    class _Libro:
        titulo, autor = "Por encima", "Autor"
        capitulos = caps
        palabras = sum(c.palabras for c in caps)

    p = perfil_mod.Perfil(nivel=1.00, banda="intermedio",
                          origen="cuestionario", creado="", nombre="Ana")
    # Media ponderada por ventanas: 1,436. Por encima de 1,00 + RETO.
    filas = [
        {"capitulo": 1, "indice": 1, "dificultad": 1.70, "ventanas": 10, "palabras": 4000},
        {"capitulo": 2, "indice": 2, "dificultad": 1.05, "ventanas": 10, "palabras": 4000},
        {"capitulo": 3, "indice": 3, "dificultad": 1.80, "ventanas": 30, "palabras": 4000},
        {"capitulo": 4, "indice": 4, "dificultad": 0.90, "ventanas": 10, "palabras": 4000},
        {"capitulo": 5, "indice": 99, "dificultad": 1.00, "ventanas": 10, "palabras": 4000},
    ]

    def valores(u):
        return [v for _, v in (u.get("choices") or [])]

    viejo = ui._analisis_guardado
    try:
        ui._analisis_guardado = lambda *a, **k: {"filas": filas}
        con = ui._capitulos_sugeridos(_Libro(), p)
        assert con.get("visible") is True, (
            f"el libro va por encima (1,44 contra 1,00) y no sugiere nada: {con}")
        assert 99 not in valores(con), "ofrece un capitulo que no existe en este libro"
        assert valores(con) == [2, 4], (
            f"sugiere {valores(con)}; se esperaban [2, 4], por cercania y sin "
            f"los que van por encima del margen")
        assert con.get("value") is None, "marca una sugerencia sin que nadie la elija"

        sin_perfil = ui._capitulos_sugeridos(_Libro(), None)
        assert sin_perfil.get("visible") is False and not sin_perfil.get("choices"), \
            "sugiere capitulos sin saber el nivel del lector"

        ui._analisis_guardado = lambda *a, **k: None
        assert ui._capitulos_sugeridos(_Libro(), p).get("visible") is False, \
            "sugiere capitulos sin haber medido el libro"

        ui._analisis_guardado = lambda *a, **k: {
            "filas": [dict(f, dificultad=0.90) for f in filas[:4]]}
        assert ui._capitulos_sugeridos(_Libro(), p).get("visible") is False, \
            "sugiere capitulos de un libro que ya esta entero a su alcance"

        ui._analisis_guardado = lambda *a, **k: {"filas": "basura"}
        assert ui._capitulos_sugeridos(_Libro(), p).get("visible") is False, \
            "un analisis roto tiene que esconder las sugerencias, no reventar"
    finally:
        ui._analisis_guardado = viejo

    demo = ui.construir()
    fns = demo.fns
    lista = list(fns.values() if isinstance(fns, dict) else fns)
    sug = [f for f in lista
           if getattr(getattr(f, "fn", None), "__name__", "") == "_capitulos_sugeridos"]
    assert sug, ("`_capitulos_sugeridos` no esta cableada a ningun evento: la "
                 "funcion existe y funciona, y al abrir un libro no la llama nadie")
    for f in sug:
        ajenos = [type(c).__name__ for c in f.inputs if not isinstance(c, gr.State)]
        assert not ajenos, (
            f"las sugerencias leen un componente del navegador ({ajenos}). Solo "
            f"pueden leer estados del servidor: un desplegable llega con el valor "
            f"del libro anterior y Gradio pinta el recuadro rojo")
    fuente = (pathlib.Path(__file__).parent / "app" / "ui.py").read_text(encoding="utf-8")
    assert "sugeridos.select(_indice_de, [est_libro, sugeridos], cap)" in fuente, (
        "elegir una sugerencia ya no salta por `_indice_de`, que es lo que valida "
        "el capitulo contra este libro")
    return "solo con perfil, curva y libro por encima; indices validos; cableado limpio"


prueba("las sugerencias de capitulos salen cuando tocan",
       _las_sugerencias_de_capitulos_salen_cuando_tocan)


def _el_catalogo_medido_recomienda_capitulos_sin_saltar_mal():
    """Fase 2: la curva por capitulo del catalogo, sin mandar a otro capitulo.

    a) si los capitulos del libro abierto cuadran con los del catalogo, las
       sugerencias usan esa curva y apuntan al indice de ESTE libro;
    b) si no cuadran -un EPUB que parte el libro de otra manera-, no se sugiere;
    c) `_abrir` apunta de que libro del catalogo es, por el nombre del archivo;
    d) la descarga pide el `.txt` antes que el EPUB, y un EPUB ya guardado vale
       si el `.txt` no llega;
    e) por nivel no se recomiendan indices ni libros que no son literatura, y la
       curva por capitulo se lee del parquet que va junto al CSV, en orden.
    """
    import tempfile
    import urllib.request
    import pandas as pd
    import catalogo as cat_mod

    cuerpo = "The rain fell on the quiet moor and the train ran west. " * 200

    class _Cap:
        def __init__(self, t, texto=cuerpo):
            self.titulo, self.texto = t, texto
            self.palabras = len(texto.split())

    caps = [_Cap("Title", "Project Gutenberg title page"), _Cap("CHAPTER I"),
            _Cap("CHAPTER II"), _Cap("CHAPTER III")]

    class _Libro:
        titulo, autor = "Libro medido", "Autor"
        capitulos = caps
        palabras = sum(c.palabras for c in caps)
        id_catalogo = "PG42"

    filas_cat = [
        {"id": "PG42", "capitulo": 1, "indice": 0, "titulo": "Chapter I",
         "dificultad": 1.80, "ventanas": 10, "palabras": 2400},
        {"id": "PG42", "capitulo": 2, "indice": 1, "titulo": "Chapter II",
         "dificultad": 0.90, "ventanas": 10, "palabras": 2400},
        {"id": "PG42", "capitulo": 3, "indice": 2, "titulo": "Chapter III",
         "dificultad": 1.85, "ventanas": 10, "palabras": 2400},
    ]

    class _Cat:
        medido = True

        def __init__(self, filas):
            self.filas = filas

        def capitulos_de(self, pid):
            return [dict(f) for f in self.filas] if pid == "PG42" else []

    p = perfil_mod.Perfil(nivel=0.9, banda="intermedio",
                          origen="cuestionario", creado="", nombre="Ana")

    # a) y b)
    viejo_cat, viejo_an = ui.catalogo, ui._analisis_guardado
    try:
        ui._analisis_guardado = lambda *a, **k: None
        ui.catalogo = lambda: _Cat(filas_cat)
        con = ui._capitulos_sugeridos(_Libro(), p)
        valores = [v for _, v in (con.get("choices") or [])]
        assert con.get("visible") is True, f"con los capitulos alineados no sugiere nada: {con}"
        assert valores == [2], (
            f"sugiere {valores}: tenia que ser el indice 2 de ESTE libro -el capitulo 2 "
            f"del catalogo, desplazado por la portadilla-, no el indice del catalogo")
        desalineadas = [dict(f) for f in filas_cat]
        desalineadas[1]["titulo"] = "Chapter XX"
        ui.catalogo = lambda: _Cat(desalineadas)
        assert ui._capitulos_sugeridos(_Libro(), p).get("visible") is False, \
            "sugiere con capitulos que no cuadran: mandaria al lector a otro capitulo"
    finally:
        ui.catalogo, ui._analisis_guardado = viejo_cat, viejo_an

    # c)
    carpeta = pathlib.Path(pruebas_tmp.carpeta())
    del_catalogo = carpeta / "pg4242.txt"
    del_catalogo.write_text("CHAPTER I\n\n" + cuerpo + "\n\nCHAPTER II\n\n" + cuerpo,
                            encoding="utf-8")
    subido = carpeta / "mi_libro.txt"
    subido.write_text(del_catalogo.read_text(encoding="utf-8"), encoding="utf-8")
    assert ui._abrir(str(del_catalogo))[0].id_catalogo == "PG4242", \
        "abrir pg4242.txt no apunta que es el PG4242 del catalogo"
    assert ui._abrir(str(subido))[0].id_catalogo is None, \
        "un libro subido a mano se hace pasar por uno del catalogo"

    # d)
    libros = pathlib.Path(ui.RUTA_LIBROS)
    libros.mkdir(parents=True, exist_ok=True)
    epub = libros / "pg98765.epub"
    epub.write_bytes(b"x" * 3000)
    pedidas = []

    class _Resp:
        def __init__(self, datos):
            self.datos = datos

        def read(self):
            return self.datos

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def red_con_txt(pedido, *a, **k):
        pedidas.append(getattr(pedido, "full_url", str(pedido)))
        return _Resp(b"CHAPTER I\n\n" + b"word " * 1000)

    def sin_red(*a, **k):
        raise OSError("sin red")

    real = urllib.request.urlopen
    try:
        urllib.request.urlopen = red_con_txt
        devuelto = ui._descargar_gutenberg("PG98765")
        assert pedidas and pedidas[0].endswith(".txt"), \
            f"lo primero que pide a Gutenberg no es el .txt: {pedidas[:1]}"
        assert devuelto.endswith(".txt"), \
            f"con un EPUB guardado no baja el .txt, que es el formato medido: {devuelto}"
        pathlib.Path(devuelto).unlink(missing_ok=True)
        urllib.request.urlopen = sin_red
        devuelto = ui._descargar_gutenberg("PG98765")
        assert devuelto.endswith(".epub"), f"sin red no usa el EPUB que ya tenia: {devuelto}"
    finally:
        urllib.request.urlopen = real
        epub.unlink(missing_ok=True)
        (libros / "pg98765.txt").unlink(missing_ok=True)

    # e)
    csv = carpeta / "catalogo_medido.csv"
    pd.DataFrame({
        "id": ["PG1", "PG2", "PG3"],
        "title": ["Index of the Project Gutenberg Works", "A Primer", "Chess Problems"],
        "author": ["a", "b", "c"], "hook": ["", "", ""], "huella_texto": ["", "", ""],
        "nivel_cefr": ["", "", ""], "downloads": [30, 20, 10],
        "dificultad": [0.5, 0.5, 0.5],
        "temas": ["Indexes; Fiction", "Readers (Primary)", "Chess problems"],
    }).to_csv(csv, index=False)
    pd.DataFrame({
        "id": ["PG2", "PG2"], "capitulo": [2, 1], "indice": [3, 1], "titulo": ["II", "I"],
        "dificultad": [0.5, 0.4], "min": [0.3, 0.3], "max": [0.6, 0.6],
        "ventanas": [2, 2], "palabras": [600, 600],
    }).to_parquet(carpeta / "capitulos_medidos.parquet", index=False)
    cat = cat_mod.Catalogo(csv)
    ids = [b.id for b in cat.por_nivel(0.5, holgura=0.2, n=10)]
    assert ids == ["PG2"], (
        f"por nivel recomienda {ids}: ni un indice de Gutenberg ni unos problemas de "
        f"ajedrez son lecturas")
    assert [c["capitulo"] for c in cat.capitulos_de("PG2")] == [1, 2], \
        f"la curva por capitulo no sale en orden: {cat.capitulos_de('PG2')}"
    assert cat.capitulos_de("PG9") == [], "se inventa la curva de un libro sin medir"
    return "alinea o calla, apunta el id, .txt primero, y solo recomienda lecturas"


prueba("el catalogo medido recomienda capitulos sin saltar mal",
       _el_catalogo_medido_recomienda_capitulos_sin_saltar_mal)


def _el_buscador_encuentra_un_nombre_mal_escrito():
    """El paso 2 de la demo, que no probaba nadie.

    «dostoyevski» mal escrito encuentra a Dostoyevsky por parecido ortografico
    del nombre, no por tema. Subir `_PARECIDO_NOMBRE` a 0,99 apaga ese rescate
    y la suite entera seguia en verde: el paso estrella del guion se podia
    romper sin que se enterara nadie. Y bajar `minimo_similitud` a 0 hace que
    no se descarte nunca un resultado flojo, asi que el aviso de «ningun libro
    supera el umbral» no sale jamas.
    """
    import numpy as np
    import pandas as pd
    import catalogo as cat_mod

    df = pd.DataFrame({
        "id": ["PG2554", "PG11", "PG1342"],
        "title": ["Crime and Punishment", "Alice in Wonderland",
                  "Pride and Prejudice"],
        "author": ["Dostoyevsky, Fyodor", "Carroll, Lewis", "Austen, Jane"],
        "nivel_cefr": ["C1", "B1", "C2"],
        "hook": ["de que va", "de que va", "de que va"],
        "downloads": [1, 1, 1]})
    cat = object.__new__(cat_mod.Catalogo)
    cat.df = df
    # Parecido por TEMA nulo: lo unico que puede encontrar al autor es el
    # rescate por parecido del nombre. Si no, la prueba se cumpliria sola.
    cat._emb = np.zeros((3, 4), dtype=np.float32)
    cat._fichas = None
    cat._modelo_emb = lambda: type("M", (), {"encode": staticmethod(
        lambda x, **k: np.zeros((1, 4), dtype=np.float32))})()

    libros, aviso = cat.buscar("dostoyevski", n=3)
    assert libros, (
        f"«dostoyevski» mal escrito no encuentra nada: el rescate por parecido "
        f"del nombre esta apagado. Aviso: {aviso!r}")
    assert "Dostoyevsky" in libros[0].autor, (
        f"el primero es {libros[0].titulo!r} de {libros[0].autor!r}")

    # Y el umbral: una consulta que no se parece a nada no puede devolver
    # resultados, tiene que devolver el aviso.
    vacios, aviso = cat.buscar("zzzqqq nada que ver con esto", n=3)
    assert not vacios, f"una consulta absurda devuelve {len(vacios)} libros"
    assert "umbral" in aviso.lower() or "parecido" in aviso.lower(), (
        f"y sin decir por que: {aviso!r}")
    return "«dostoyevski» encuentra a Dostoyevsky, y lo que no se parece avisa"


prueba("el buscador encuentra un nombre mal escrito",
       _el_buscador_encuentra_un_nombre_mal_escrito)


def _la_pestana_publica_no_dice_que_usuarios_hay():
    """«Estado» es publica y la leen los visitantes.

    La prueba del diagnostico comprobaba que no se filtrara la CONTRASEÑA, y
    no que faltara el NOMBRE DE USUARIO. Invertir el `con_nombre=False` de
    `problemas()` sacaba los usuarios configurados a una pestaña publica y le
    ahorraba medio trabajo a quien prueba contraseñas.
    """
    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    os.environ["LITERALEVEL_CUENTAS"] = (
        "zoraida:x:0,Zoraida:y:5,rota:sin-tope,:vacio:1")
    try:
        publico = " ".join(cuentas_mod.problemas()).lower()
        assert "zoraida" not in publico, (
            f"la pestaña publica dice que existe el usuario «zoraida»: {publico}")
        assert "x" not in [a.split()[-1] for a in cuentas_mod.problemas()], \
            "filtro una contrasena"
        # Y sigue sirviendo para arreglar el secreto: dice QUE entrada falla.
        assert "entrada" in publico and "repite" in publico, (
            f"sin el nombre ya no se sabe que arreglar: {publico}")
        # En el registro del Space, que solo lee el dueno, el nombre SI va:
        # sin el, quien edita el secreto a ciegas no sabe cual es.
        privado = " ".join(cuentas_mod._analizar(
            os.environ["LITERALEVEL_CUENTAS"], con_nombre=True)[1]).lower()
        assert "zoraida" in privado, (
            "el registro privado tambien perdio el nombre: ahora el secreto "
            "no se puede arreglar desde ningun sitio")
        return "la pestaña publica dice que entrada falla, no quien es"
    finally:
        if viejo is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo


prueba("la pestana publica no dice que usuarios hay",
       _la_pestana_publica_no_dice_que_usuarios_hay)


# --- Fonemas: AFI y audio pregrabado en la correccion de voz ---------------

titulo("Fonemas del ingles en la correccion de voz")

import fonemas as fonemas_mod  # noqa: E402
from types import SimpleNamespace  # noqa: E402


def _inventario_completo_y_sin_duplicados():
    """41 fonemas de General American: 24 consonantes, 12 vocales, 5 diptongos.

    Un simbolo repetido haria que dos fonemas compartieran mp3, y dos
    archivos iguales que uno pisara al otro al generarlos."""
    inv = fonemas_mod.INVENTARIO
    simbolos = [f.simbolo for f in inv]
    assert len(simbolos) == len(set(simbolos)), "hay simbolos repetidos"
    archivos = [f.archivo for f in inv]
    assert len(archivos) == len(set(archivos)), "dos fonemas comparten mp3"
    por_tipo = {t: sum(1 for f in inv if f.tipo == t)
                for t in ("consonante", "vocal", "diptongo")}
    assert por_tipo == {"consonante": 24, "vocal": 12, "diptongo": 5}, por_tipo
    # Los que un hispanohablante mas falla tienen que estar, con su simbolo AFI.
    for imprescindible in ("θ", "ð", "ʃ", "ʒ", "ŋ", "ɹ", "w", "v", "æ", "ʌ", "ə",
                           "ɪ", "ʊ", "ɝ", "ɚ", "tʃ", "dʒ", "oʊ", "eɪ"):
        assert imprescindible in simbolos, f"falta /{imprescindible}/"
    for f in inv:
        assert f.nombre.strip() and len(f.ejemplos) == 2, f
        # La normalizacion de un simbolo canonico tiene que ser el mismo.
        assert fonemas_mod.normalizar(f.simbolo) == f.simbolo, f.simbolo
    return f"{len(inv)} fonemas: {por_tipo}"


prueba("fonemas: inventario completo y sin duplicados",
       _inventario_completo_y_sin_duplicados)


def _cada_fonema_tiene_su_audio():
    """El mp3 de cada fonema esta en disco y la app puede servirlo.

    Si falta uno, la correccion pinta el simbolo sin reproductor y nadie se
    entera; esto lo convierte en un fallo visible."""
    faltan = [f.simbolo for f in fonemas_mod.INVENTARIO
              if fonemas_mod.audio_de(f.simbolo) is None]
    assert not faltan, (f"sin mp3: {' '.join(faltan)} "
                        "(python -X utf8 tools/generar_fonemas.py)")
    pesos = [f.ruta.stat().st_size for f in fonemas_mod.INVENTARIO]
    assert min(pesos) > 2_000, f"un mp3 de {min(pesos)} bytes no lleva voz"
    carpeta = os.path.normcase(str(fonemas_mod.DIR_AUDIO))
    assert any(carpeta.startswith(os.path.normcase(p)) for p in ui.RUTAS_PERMITIDAS), \
        "la carpeta de los fonemas no esta en allowed_paths: el <audio> daria 403"
    return f"{len(pesos)} mp3, {sum(pesos) / 1024:.0f} KB en total"


prueba("fonemas: cada uno tiene su audio en disco", _cada_fonema_tiene_su_audio)


def _normalizacion_de_simbolos():
    """Lo que devuelve un modelo o un diccionario lleva barras, acentos,
    ligaduras, marcas de longitud o la notacion de RP. Todo eso tiene que
    llevar al mismo fonema, y lo que no es un fonema, a `None`."""
    casos = {
        "/w/": "w", "w": "w", "[w]": "w", " /w/ ": "w",
        "r": "ɹ", "/r/": "ɹ", "ɹ": "ɹ",
        "ɔː": "ɔ", "ɔ": "ɔ", "iː": "i", "uː": "u", "ɑː": "ɑ", "e": "ɛ",
        "t͡ʃ": "tʃ", "ʧ": "tʃ", "d͡ʒ": "dʒ", "ˈæ": "æ", "eɪ̯": "eɪ",
        "ɜː": "ɝ", "ər": "ɚ", "əʊ": "oʊ", "g": "ɡ", "/ð/": "ð",
        # Fable (auditoria 18): el gancho rotico no es un diacritico que se
        # pueda quitar, y las mayusculas ASCII valen para todas las letras.
        "ə˞": "ɚ", "ɜ˞": "ɝ", "W": "w", "S": "s", "R": "ɹ", "ñ": None,
        # Sin equivalente en General American, o no son fonemas: sin audio
        # antes que un audio que ensena otro sonido.
        "ɒ": None, "ɪə": None, "eə": None, "ɾ": None, "ʔ": None,
        "ninguno": None, "": None, None: None, 42: None, "warn": None,
        "/wɔːrn/": None,
    }
    malos = {k: (fonemas_mod.normalizar(k), v) for k, v in casos.items()
             if fonemas_mod.normalizar(k) != v}
    assert not malos, f"normalizacion (obtenido, esperado): {malos}"
    return f"{len(casos)} variantes bien resueltas"


prueba("fonemas: normalizacion de simbolos", _normalizacion_de_simbolos)


def _detalle(palabra="warn", fonema="w", sonido="Suena como la «hu» de «huevo».",
             boca="Redondea los labios."):
    return ui.voz.DetallePalabra(palabra=palabra, fonema=fonema,
                                 sonido_que_falla=sonido,
                                 como_colocar_la_boca=boca)


def _fonema_desconocido_no_revienta():
    """Un fonema fuera del inventario se pinta como texto, sin reproductor.

    Y `DetallePalabra` lo acepta: con un `Literal` en pydantic, un simbolo
    raro seria un ValidationError y el alumno perderia la correccion entera,
    ya pagada, por un campo."""
    for raro in ("zzz", "ninguno", "", "ɒ", "<script>", None):
        if raro is None:
            d = SimpleNamespace(palabra="warn", sonido_que_falla="x",
                                como_colocar_la_boca="y")   # sin el campo
        else:
            d = _detalle(fonema=raro)
        html = ui._detalle_de_voz(d)
        assert "<audio" not in html, f"pinto reproductor para {raro!r}: {html}"
        assert "warn" in html and "Redondea" in html or raro is None, html
        assert "<script" not in html, html
    # Un detalle vacio del todo tampoco tira nada.
    assert ui._detalle_de_voz(SimpleNamespace()).startswith("- **")
    # El HTML tiene que ir en el TEXTO del modelo, que es lo que se imprime.
    # Con el `<script>` en `fonema`, lo de arriba pasaba siempre: un fonema que
    # no esta en el inventario no se pinta. Fable (auditoria 18).
    html = ui._detalle_de_voz(_detalle(sonido='<img src=x onerror=alert(1)>',
                                       boca="<script>alert(2)</script>"))
    # Las unicas <img> son las animaciones de la boca, servidas desde disco; la
    # del modelo tiene que llegar escapada.
    assert "<script" not in html and "<img src=x" not in html, html
    assert all(t.startswith(' loading="lazy" src="gradio_api/file=') for t in html.split("<img")[1:]), html
    assert "&lt;script&gt;" in html and "&lt;img" in html, html
    return "texto sin reproductor, sin excepcion y con el texto del modelo escapado"


prueba("fonemas: detalle con fonema desconocido no revienta",
       _fonema_desconocido_no_revienta)


def _audio_del_fonema_sin_clave():
    """El audio del fonema es un archivo del repositorio: sin OPENAI_API_KEY
    tiene que seguir sonando. Esta suite corre sin clave (ver la cabecera)."""
    assert not os.environ.get("OPENAI_API_KEY"), "la suite deberia correr sin clave"
    assert "OPENAI_API_KEY" in ui.config.falta()
    ruta = fonemas_mod.audio_de("/w/")
    assert ruta and os.path.isfile(ruta), f"sin clave no hay audio de /w/: {ruta}"
    html = ui._detalle_de_voz(_detalle(fonema="/w/"))
    assert "<audio" in html and "gradio_api/file=" in html, html
    assert "/w/" in html and "we, warn" in html, html
    return "suena sin clave"


prueba("fonemas: sin clave el audio del fonema sigue disponible",
       _audio_del_fonema_sin_clave)


def _ipa_ausente_no_se_inventa():
    """Si Kaikki no trae la IPA de la palabra, se dice; nunca se inventa.

    Se finge el diccionario para que la prueba no dependa de tener los 243 MB
    en la carpeta: una palabra sin fila, otra con fila pero sin IPA, y una con
    IPA britanica solamente."""
    class _Dic:
        def buscar(self, lema):
            filas = {"thought": ("/θɔːt/", None), "the": (None, None)}
            if lema not in filas:
                return []
            uk, us = filas[lema]
            return [SimpleNamespace(pos="noun", ipa_uk=uk, ipa_us=us,
                                    audio_uk=None, audio_us=None)]

    viejo = (fonemas_mod._diccionario, fonemas_mod._diccionario_fallo)
    viejo_lexicon = sys.modules.get("lexicon")
    # CMUdict fuera: esta prueba mide lo que pasa cuando NINGUN diccionario
    # trae la palabra, y CMUdict si trae «the» y «thought».
    viejo_cmu, fonemas_mod._cmu = fonemas_mod._cmu, {}
    fonemas_mod._diccionario, fonemas_mod._diccionario_fallo = _Dic(), None
    try:
        for palabra in ("zarzaparrilla", "the"):
            assert fonemas_mod.ipa_de_palabra(palabra) == (None, None), palabra
            cabeza = ui._detalle_de_voz(_detalle(palabra=palabra)).split("<br>")[0]
            assert "sin transcripción" in cabeza, cabeza
            assert "/" not in cabeza and "[" not in cabeza, \
                f"se invento una transcripcion para {palabra}: {cabeza}"
        assert fonemas_mod.ipa_de_palabra("thought") == ("/θɔːt/", "UK")
        cabeza = ui._detalle_de_voz(_detalle(palabra="thought", fonema="θ")).split("<br>")[0]
        assert "/θɔːt/ (UK)" in cabeza, cabeza
        # Y avisa de que la transcripcion es britanica y el sonido americano.
        assert "británica" in cabeza, cabeza

        # Sin diccionario en disco -recien fallado-, lo mismo: nada inventado,
        # nada roto, y no se reintenta en cada palabra.
        fonemas_mod._diccionario, fonemas_mod._diccionario_fallo = None, fonemas_mod.time.monotonic()
        assert fonemas_mod.ipa_de_palabra("warn") == (None, None)
        assert "sin transcripción" in ui._detalle_de_voz(_detalle())

        # Pero el fallo NO es para siempre: pasado el plazo se vuelve a abrir.
        # En el Space el diccionario es un volumen montado y puede llegar tarde.
        # `ipa_de_palabra` usa tambien `lexicon._mejor_fonetica`: el modulo
        # fingido lleva la real, o la llamada falla y devuelve (None, None).
        import lexicon as _lexicon_real
        sys.modules["lexicon"] = SimpleNamespace(Diccionario=lambda ruta: _Dic(),
                                                 RUTA_DICCIONARIO="finge",
                                                 _mejor_fonetica=_lexicon_real._mejor_fonetica)
        fonemas_mod._diccionario = None
        fonemas_mod._diccionario_fallo = fonemas_mod.time.monotonic() - fonemas_mod._REINTENTO_S - 1
        assert fonemas_mod.ipa_de_palabra("thought") == ("/θɔːt/", "UK"), \
            "tras el plazo no reintento abrir el diccionario"
        assert fonemas_mod._diccionario_fallo is None
    finally:
        fonemas_mod._diccionario, fonemas_mod._diccionario_fallo = viejo
        fonemas_mod._cmu = viejo_cmu
        if viejo_lexicon is not None:
            sys.modules["lexicon"] = viejo_lexicon
        else:
            sys.modules.pop("lexicon", None)
    return "sin fila o sin IPA dice 'sin transcripción', y el fallo se reintenta pasado el plazo"


prueba("fonemas: IPA de palabra ausente en Kaikki no se inventa",
       _ipa_ausente_no_se_inventa)


def _esquema_y_prompt_apuntan_al_inventario():
    """El `enum` que viaja a Structured Outputs es el inventario mas 'ninguno',
    y el prompt lista cada simbolo: si divergen, el modelo elige simbolos que
    no tienen audio."""
    from openai.lib._pydantic import to_strict_json_schema
    esquema = to_strict_json_schema(ui.voz.Correccion)
    campo = esquema["$defs"]["DetallePalabra"]["properties"]["fonema"]
    assert campo.get("enum") == [*fonemas_mod.SIMBOLOS, ui.voz.SIN_FONEMA], campo
    assert "fonema" in esquema["$defs"]["DetallePalabra"]["required"]
    for f in fonemas_mod.INVENTARIO:
        assert f"   {f.simbolo}  (" in ui.voz._PROMPT_REGLAS, f.simbolo
    # Lo que pidio la lectora: anclar a una palabra del espanol, sin vaguedades.
    assert "huevo" in ui.voz._PROMPT_REGLAS and "mas fuerte" in ui.voz._PROMPT_REGLAS
    return f"enum de {len(campo['enum'])} y prompt con los {len(fonemas_mod.SIMBOLOS)}"


prueba("fonemas: esquema y prompt apuntan al inventario",
       _esquema_y_prompt_apuntan_al_inventario)


def _la_practica_pinta_ipa_y_audio():
    """De punta a punta por `_practicar`, con `voz.practicar` doblado: la
    correccion lleva la palabra, el simbolo del fonema y su reproductor, y un
    detalle con fonema raro sale sin reproductor pero con su texto."""
    ev = ui.voz.evaluar_pronunciacion("I warn the ship", "I born the sip")
    sesion = ui.voz.SesionVoz(
        evaluacion=ev, audio_correcto=None,
        correccion=ui.voz.Correccion(resumen="Casi.", detalles=[
            _detalle(), _detalle(palabra="ship", fonema="ʃ",
                                 sonido="Como el «shhh» de pedir silencio"),
            _detalle(palabra="the", fonema="ninguno", sonido="Es el ritmo")]))
    viejo_practicar, viejo_falta = ui.voz.practicar, ui.config.falta
    viejo_dic = (fonemas_mod._diccionario, fonemas_mod._diccionario_fallo)
    audio = TMP / "fonemas_practica.wav"
    audio.write_bytes(b"RIFF")

    # Diccionario fingido, para que la prueba MIDA la IPA y no pase igual con
    # o sin Kaikki en disco (Fable, auditoria 18).
    class _Dic:
        def buscar(self, lema):
            if lema != "warn":
                return []
            return [SimpleNamespace(pos="verb", ipa_uk="/wɔːn/", ipa_us="/woɹn/",
                                    audio_uk=None, audio_us=None)]

    # CMUdict fuera: la prueba necesita una palabra sin IPA («ship»).
    viejo_cmu = fonemas_mod._cmu
    try:
        ui.config.falta = lambda: []
        ui.voz.practicar = lambda *a, **k: sesion
        fonemas_mod._diccionario, fonemas_mod._diccionario_fallo = _Dic(), None
        fonemas_mod._cmu = {}
        _, veredicto, _ = ui._practicar(str(audio), "I warn the ship")
    finally:
        ui.voz.practicar, ui.config.falta = viejo_practicar, viejo_falta
        fonemas_mod._diccionario, fonemas_mod._diccionario_fallo = viejo_dic
        fonemas_mod._cmu = viejo_cmu
    veredicto = str(veredicto)
    assert "**warn** /woɹn/ (US)" in veredicto, f"no pinto la IPA americana de warn: {veredicto[:400]}"
    assert "**ship** (sin transcripción" in veredicto, veredicto[:400]
    assert "**Cómo corregirlo:** Casi." in veredicto, veredicto[:300]
    assert veredicto.count("<audio") == 2, f"esperaba 2 reproductores: {veredicto}"
    assert "/w/" in veredicto and "/ʃ/" in veredicto, veredicto
    assert "Es el ritmo" in veredicto, "el detalle sin fonema perdio su texto"
    assert ".." not in veredicto.replace("...", ""), "vuelve el «..»"
    # Una linea de lista por palabra: tres detalles, tres «- **».
    assert veredicto.count("\n- **") + veredicto.startswith("- **") == 3, veredicto
    return "2 reproductores para 3 detalles"


prueba("fonemas: la practica pinta ipa y audio", _la_practica_pinta_ipa_y_audio)


def _practica_sin_voz_devuelve_el_uso():
    """Reinicio 26 (Central y f4): en Gradio, una grabacion en la que whisper respondio y no
    oyo nada (`sin_voz`) devuelve el uso con `cuentas.devolver_por_silencio`, con el codigo
    leido ANTES de cobrar, y lo dice; sin respuesta de whisper (red caida) no se llama."""
    ev = ui.voz.evaluar_pronunciacion("Hello there", "")
    audio = TMP / "sin_voz_gradio.wav"
    audio.write_bytes(b"RIFF")
    llamadas, orden = [], []
    viejos = (ui.voz.practicar, ui.config.falta, ui._puede_pagar, ui._codigo_de, ui.cuentas.devolver_por_silencio)

    def practicar_con(sin_voz):
        return lambda *a, **k: ui.voz.SesionVoz(evaluacion=ev, audio_correcto=None, correccion=None,
                                                transcripcion_ok=False, sin_voz=sin_voz)

    def codigo_de(pet):
        orden.append("codigo")
        return "CODIGO-COBRADO"

    def puede_pagar(pet):
        orden.append("cobro")
        return True, ""

    salidas = {}
    try:
        ui.config.falta = lambda: []
        ui._puede_pagar, ui._codigo_de = puede_pagar, codigo_de
        ui.cuentas.devolver_por_silencio = lambda base, codigo: llamadas.append((base, codigo)) or True
        for nombre, sin_voz in (("sin_voz", True), ("red_caida", False)):
            ui.voz.practicar = practicar_con(sin_voz)
            _, veredicto, _ = ui._practicar(str(audio), "Hello there")
            salidas[nombre] = str(veredicto)
    finally:
        (ui.voz.practicar, ui.config.falta, ui._puede_pagar, ui._codigo_de, ui.cuentas.devolver_por_silencio) = viejos
    assert llamadas == [(ui.BASE_DATOS_LECTOR, "CODIGO-COBRADO")], f"devoluciones: {llamadas}"
    assert orden.index("codigo") < orden.index("cobro"), f"el codigo se leyo despues de cobrar: {orden}"
    assert "No te oí" in salidas["sin_voz"] and "Este intento no cuenta" in salidas["sin_voz"], salidas["sin_voz"][:300]
    assert "No te oí" in salidas["red_caida"] and "no cuenta" not in salidas["red_caida"], salidas["red_caida"][:300]
    return "sin voz devuelve a la cuenta cobrada y lo dice; con la red caida, no"


prueba("practica sin voz devuelve el uso", _practica_sin_voz_devuelve_el_uso)


# --- La tabla del AFI (13 sep 2026) -----------------------------------------
# Miguel: un apartado con el AFI donde cada simbolo se toca y suena, con una
# ficha tecnica de articulacion en americano y britanico, sin coste.

import articulacion as articulacion_mod  # noqa: E402


def _inventarios_del_afi_completos():
    """Cada sonido de los dos acentos tiene ficha, palabra, grupo valido y un
    archivo que no pisa a otro; el americano es EXACTAMENTE el de `fonemas`."""
    grupos = dict(articulacion_mod.GRUPOS)
    assert [s.simbolo for s in articulacion_mod.INVENTARIO_GA] == list(fonemas_mod.SIMBOLOS)
    for acento, esperados in (("ga", 41), ("rp", 44)):
        inv = articulacion_mod.inventario(acento)
        assert len(inv) == esperados, (acento, len(inv))
        archivos = [s.archivo for s in inv]
        assert len(set(archivos)) == len(archivos), f"{acento}: dos sonidos con el mismo mp3"
        for s in inv:
            assert s.grupo in grupos, (acento, s.simbolo, s.grupo)
            assert s.ejemplos and s.nombre, (acento, s.simbolo)
            for campo in ("rasgos", "labios", "lengua", "boca", "cuerdas", "aire", "trampa"):
                assert getattr(s.ficha, campo).strip(), (acento, s.simbolo, campo)
    # Lo que distingue a los acentos esta: RP tiene /ɒ/ y los centralizantes; GA no.
    for simbolo in ("ɒ", "ɪə", "eə", "ʊə", "əʊ", "ɜː"):
        assert articulacion_mod.buscar(simbolo, "rp") is not None, simbolo
        assert articulacion_mod.buscar(simbolo, "ga") is None, simbolo
    assert articulacion_mod.buscar("ɹ", "ga").ficha is articulacion_mod.buscar("r", "rp").ficha
    return "41 americanos y 44 britanicos, con ficha y mp3 propios"


prueba("afi: inventarios completos y con ficha", _inventarios_del_afi_completos)


def _la_tabla_del_afi_se_pinta_bien():
    """85 simbolos que suenan, el britanico oculto al empezar, sin <script>, y
    el texto de las fichas escapado."""
    html = ui._tabla_afi_html()
    assert html.count('class="ll-afi-btn"') == 85, html.count('class="ll-afi-btn"')
    assert html.count("<details>") == 85
    assert '<div class="ll-afi-inv" data-acento="ga">' in html
    assert '<div class="ll-afi-inv" data-acento="rp" hidden>' in html
    assert "<script" not in html, "Gradio no ejecuta scripts de un gr.HTML: va en JS_AFI"
    # Cada audio lleva `?v=` si su mp3 esta en disco (cache del navegador).
    for s in articulacion_mod.INVENTARIO_GA + articulacion_mod.INVENTARIO_RP:
        if s.audio():
            assert "?v=" in ui._src_audio(s.ruta), s.simbolo
    # Escapado: una ficha con HTML no puede salir viva.
    viejo = articulacion_mod.FICHAS["p"]
    try:
        falsa = articulacion_mod.Ficha(*(["<img src=x onerror=alert(1)>"] * 7))
        articulacion_mod.INVENTARIO_GA = tuple(
            (articulacion_mod.Sonido(s.acento, s.simbolo, s.nombre, s.ejemplos, s.grupo, falsa, s.clave)
             if s.simbolo == "p" else s) for s in articulacion_mod.INVENTARIO_GA)
        html_malo = ui._tabla_afi_html()
        assert "<img src=x" not in html_malo and "&lt;img src=x" in html_malo
    finally:
        articulacion_mod.INVENTARIO_GA = tuple(
            (articulacion_mod.Sonido(s.acento, s.simbolo, s.nombre, s.ejemplos, s.grupo, viejo, s.clave)
             if s.simbolo == "p" else s) for s in articulacion_mod.INVENTARIO_GA)
    assert articulacion_mod.buscar("p").ficha is viejo
    return "85 simbolos, britanico oculto, sin script y escapado"


prueba("afi: la tabla se pinta bien", _la_tabla_del_afi_se_pinta_bien)


def _el_afi_se_oye_y_se_engancha():
    """La carpeta britanica se sirve, y el manejador de clics va en demo.load."""
    assert str(articulacion_mod.DIR_AUDIO_RP) in ui.RUTAS_PERMITIDAS
    assert str(fonemas_mod.DIR_AUDIO) in ui.RUTAS_PERMITIDAS
    fuente = pathlib.Path(ui.__file__).read_text(encoding="utf-8")
    assert "js=JS_AFI" in fuente.split("def construir")[1], "el JS de la tabla no se engancha"
    assert "audio.play()" in ui.JS_AFI and "window.__llAfi" in ui.JS_AFI
    return "carpeta servida y JS enganchado una sola vez"


prueba("afi: se sirve el audio y se engancha el js", _el_afi_se_oye_y_se_engancha)


def _la_pestana_se_llama_ipa():
    """Miguel (13 sep): «¿no seria IPA?». Es la sigla que ve en diccionarios."""
    fuente = pathlib.Path(ui.__file__).read_text(encoding="utf-8")
    assert 'gr.Tab("Sonidos IPA", id="afi")' in fuente
    assert 'gr.Tab("Sonidos AFI"' not in fuente
    return "«Sonidos IPA»"


prueba("afi: la pestana se llama sonidos ipa", _la_pestana_se_llama_ipa)


# --- Palabras que el diccionario no resuelve (13 sep 2026) -------------------
# Con «mostly» el lector no tuvo traduccion ni audio, y la acepcion elegida era
# una obsoleta. Miguel: en esas palabras, toda la ayuda de OpenAI, marcada.

import lexicon as lexicon_mod  # noqa: E402


def _acepciones_marginales_no_ganan():
    E, S = lexicon_mod.EntradaDiccionario, lexicon_mod.Sentido
    e = E("mostly", "adv", [], None, None, None, None)
    candidatos = [(e, S("To the greatest extent; most.", "adv", ["obsolete"])),
                  (e, S("Synonym of probably, likely.", "adv", ["archaic"])),
                  (e, S("For the most part; mainly.", "adv", []))]
    elegida, _, _ = lexicon_mod._elegir_sentido("The house was mostly empty.", candidatos)
    assert elegida.glosa == "For the most part; mainly.", elegida.glosa
    # Si todas son marginales, se queda con ellas (no se queda sin nada).
    solo_raras = candidatos[:1]
    assert lexicon_mod._elegir_sentido("x", solo_raras)[0].glosa.startswith("To the greatest")
    return "la obsoleta ya no gana a «for the most part»"


prueba("lexico: acepciones obsoletas o arcaicas no ganan", _acepciones_marginales_no_ganan)


def _la_definicion_por_ia_se_pide_bien():
    """El prompt de la definicion por IA dice que la palabra NO esta en el
    diccionario, pide admitir la duda y devuelve los campos del resultado."""
    capturado = {}

    class _Parseado:
        def model_dump(self):
            return {"definicion_ia": "Brillante, que destella débilmente.", "traduccion": "resplandeciente",
                    "definicion_contextual": "Describe el lago.", "explicacion_gramatical": "Adjetivo.",
                    "explicacion_adaptada": "Que brilla.", "ejemplo_simplificado": "The glimmerous water shone."}

    class _Responses:
        def parse(self, **kw):
            capturado.update(kw)
            return SimpleNamespace(output_parsed=_Parseado())

    datos = lexicon_mod._pedir_definicion_ia(
        SimpleNamespace(responses=_Responses()), palabra="glimmerous",
        oracion="The glimmerous lake shone.", categoria="adj", banda="intermedio",
        modelo="modelo-falso", idioma="es")
    assert "NO" in capturado["instructions"] and "no tienes certeza" in capturado["instructions"]
    assert "glimmerous" in capturado["input"]
    campos = set(capturado["text_format"].model_fields)
    assert {"definicion_ia", "traduccion", "definicion_contextual"} <= campos, campos
    assert datos["traduccion"] == "resplandeciente"
    # Y la explicacion normal pide traduccion y, si la eleccion es dudosa, recibe
    # las otras acepciones del diccionario y la regla de no inventar.
    capturado.clear()
    lexicon_mod._pedir_explicacion_openai(
        SimpleNamespace(responses=_Responses()), palabra="mostly", oracion="It was mostly empty.",
        glosa="To the greatest extent; most.", categoria="adv", banda="intermedio",
        modelo="modelo-falso", alternativas=["To the greatest extent; most.", "For the most part; mainly."])
    assert "For the most part; mainly." in capturado["input"]
    assert "Nunca escribas en 'acepcion_usada'" in capturado["instructions"]
    # «waistcoat» en Alicia: con las dos acepciones delante, OpenAI se quedo con
    # la del jubon, que Kaikki no marca como historica (f4, captura 10).
    assert "otra epoca" in capturado["instructions"] and "uso actual" in capturado["instructions"]
    assert {"traduccion", "acepcion_usada"} <= set(capturado["text_format"].model_fields)
    return "prompts de IA y de acepcion alternativa con sus campos"


prueba("lexico: la definicion por ia se pide bien", _la_definicion_por_ia_se_pide_bien)


def _la_ficha_marca_lo_que_es_ia():
    """Traduccion arriba, definicion por IA con su aviso, y escapado de lo que
    viene de OpenAI (la ficha es Markdown saneado; el audio es gr.HTML)."""
    base = dict(palabra_superficie="glimmerous", oracion="", lema="glimmerous", lema_buscado="glimmerous",
                pos_spacy="ADJ", categoria=None, sentido=None, etiquetas_sentido=[], similitud=None,
                n_sentidos_candidatos=0, ipa_uk=None, ipa_us=None, audio_uk=None, audio_us=None,
                audio_generado=False, definicion_contextual="Describe el lago.", explicacion_gramatical=None,
                explicacion_adaptada=None, ejemplo_simplificado=None, banda_lector="intermedio",
                frecuencia_zipf=None, desde_cache=False,
                avisos=["'glimmerous' no esta en el diccionario Kaikki"], llamadas_de_pago=1)
    r = lexicon_mod.ResultadoLexico(**base, traduccion="resplandeciente",
                                    definicion_ia="Que destella débilmente.", generado_por_ia=True)
    ficha = ui._ficha(r, "es")
    assert "**Traducción · IA:** resplandeciente" in ficha, ficha
    assert "Definición (generada por IA)" in ficha and "inteligencia artificial" in ficha, ficha
    assert "no esta en el diccionario" not in ficha, "aviso repetido con la marca de IA"
    # Sin IA ni diccionario: el mensaje de siempre, sin fallar.
    sin = lexicon_mod.ResultadoLexico(**{**base, "definicion_contextual": None, "llamadas_de_pago": 0})
    assert "No hay entrada de diccionario" in ui._ficha(sin, "es")
    # Voz del navegador: solo sin audio, y con la palabra escapada.
    malo = lexicon_mod.ResultadoLexico(**{**base, "palabra_superficie": '"><img src=x onerror=alert(1)>'})
    html = ui._reproductores(malo)
    assert "ll-voz-navegador" in html and "<img" not in html, html
    con_audio = lexicon_mod.ResultadoLexico(**{**base, "audio_us": "https://upload.wikimedia.org/x.ogg"})
    assert "ll-voz-navegador" not in ui._reproductores(con_audio)
    fuente = pathlib.Path(ui.__file__).read_text(encoding="utf-8")
    assert "js=JS_VOZ_NAVEGADOR" in fuente.split("def construir")[1]
    return "traduccion, marca de IA, voz del navegador escapada"


prueba("lexico: la ficha marca lo que es ia", _la_ficha_marca_lo_que_es_ia)


# --- Segunda tanda de Miguel en el front (13 sep 2026) -----------------------

def _la_frase_del_libro_no_es_un_indice():
    """«Una frase de mi libro» devolvia «VIRGIL 67 V. INVOCATION TO THE LYRE 68 VI.»."""
    indices = ["VIRGIL 67 V. INVOCATION TO THE LYRE 68 VI.",
               "VOICE FROM THE PALACE 102 XXI. THE RETURN 108 XXIII.",
               "Chapter I 3 Chapter II 17 Chapter III 29 and so",
               "CONTENTS", "The End"]
    buenas = ["Such a record lays bare what lies inmostly at the heart of a people.",
              "It was 2 p.m. on the afternoon of May 7, 1915, and the ship was sinking.",
              "I went to the market with my sister and we bought bread."]
    malas = [f for f in indices if not ui._parece_indice(f)]
    falsas = [f for f in buenas if ui._parece_indice(f)]
    assert not malas and not falsas, {"indices que pasan": malas, "frases que se tiran": falsas}
    return "indices fuera, frases de verdad dentro"


prueba("voz: la frase del libro no es un indice", _la_frase_del_libro_no_es_un_indice)


def _las_mal_pronunciadas_se_guardan_con_su_frase():
    """Se guardan con la frase, se listan para practicar y una base VIEJA (sin
    la columna `frase`) se migra sola."""
    import sqlite3
    ruta = str(TMP / "voz_malpron.db")
    con = sqlite3.connect(ruta)
    con.execute("CREATE TABLE palabras_debiles (palabra TEXT PRIMARY KEY, "
                "fallos INTEGER NOT NULL DEFAULT 0, ultima_vez TEXT NOT NULL)")
    con.execute("INSERT INTO palabras_debiles VALUES ('though', 2, '2026-09-01T00:00:00+00:00')")
    con.commit()
    con.close()
    ui.voz.registrar_fallos(["thought", "though"], ruta=ruta, frase="I thought so, though.")
    ui.voz.registrar_fallos(["thought"], ruta=ruta)          # sin frase: conserva la anterior
    filas = ui.voz.palabras_para_practicar(n=5, ruta=ruta)
    assert [f["palabra"] for f in filas] == ["though", "thought"], filas
    assert filas[0]["fallos"] == 3 and filas[1]["fallos"] == 2, filas
    assert all(f["frase"] == "I thought so, though." for f in filas), filas
    assert set(filas[0]) == {"palabra", "fallos", "ultima_vez", "frase"}
    assert ui.voz.palabras_para_practicar(ruta=str(TMP / "no" / "existe" / "x.db")) == []
    return "migra la base vieja y guarda la frase"


prueba("voz: las mal pronunciadas se guardan con su frase",
       _las_mal_pronunciadas_se_guardan_con_su_frase)


def _un_historial_ilegible_se_avisa_en_las_tres_vistas():
    """Una voz.db que existe y no se lee no es «no has fallado nada»: voz lanza
    HistorialIlegible y «Palabras que pronuncié mal», «Mis puntos débiles» y
    «Repasa cinco» lo dicen. Sin base, las tres siguen diciendo que no hay nada."""
    carpeta = TMP / "historial_ilegible"
    carpeta.mkdir(parents=True, exist_ok=True)
    rota = carpeta / "voz.db"
    rota.write_bytes(b"esto no es una base de datos sqlite " * 50)
    try:
        ui.voz.puntos_debiles(5, ruta=str(rota))
        raise AssertionError("una base ilegible devolvio lista")
    except ui.voz.HistorialIlegible:
        pass
    viejo = ui._archivo_lector
    try:
        ui._archivo_lector = lambda nombre, peticion=None: str(carpeta / nombre)
        mal, debiles, repaso = ui._mal_pronunciadas(), ui._debiles(), ui._repasar()
        for vista in (mal, debiles, repaso):
            assert "[!]" in vista and "historial" in vista, vista
        assert "No hay nada que repasar" not in repaso, repaso
        rota.unlink()
        assert "Todavía no hay palabras mal pronunciadas" in ui._mal_pronunciadas()
        assert "Aún no hay palabras registradas" in ui._debiles()
        assert "No hay nada que repasar" in ui._repasar()
    finally:
        ui._archivo_lector = viejo
    return "las tres vistas avisan; sin base, siguen vacias"


prueba("voz: un historial ilegible se avisa en las tres vistas",
       _un_historial_ilegible_se_avisa_en_las_tres_vistas)


def _las_palabras_funcionales_no_son_dificiles():
    """«Tus palabras difíciles» guardaba «but · 1» y «on · 1» (Miguel, 14 sep):
    las funcionales cortas y lo de menos de tres letras no se guardan, y lo que
    ya estaba guardado deja de salir al leer. «inmostly» sí es legítima."""
    import sqlite3
    ruta = str(TMP / "voz_funcionales.db")
    ui.voz.registrar_fallos(["but", "on", "a", "the", "inmostly", "war-chant", "though"], ruta=ruta,
                            frase="But on the war-chant, though.")
    con = sqlite3.connect(ruta)
    guardadas = {p for (p,) in con.execute("SELECT palabra FROM palabras_debiles")}
    # Filas de antes de la regla: siguen en la base, pero no salen en la lista.
    con.executemany("INSERT INTO palabras_debiles (palabra, fallos, ultima_vez) VALUES (?, ?, ?)",
                    [("but", 5, "2026-09-13T00:00:00+00:00"), ("on", 4, "2026-09-13T00:00:00+00:00"),
                     ("ok", 3, "2026-09-13T00:00:00+00:00")])
    con.commit()
    con.close()
    assert guardadas == {"inmostly", "war-chant", "though"}, guardadas
    practicar = [f["palabra"] for f in ui.voz.palabras_para_practicar(n=10, ruta=ruta)]
    debiles = [p for p, _n in ui.voz.puntos_debiles(10, ruta=ruta)]
    for lista in (practicar, debiles):
        assert set(lista) == {"inmostly", "war-chant", "though"}, lista
    assert len(ui.voz.puntos_debiles(2, ruta=ruta)) == 2, "el LIMIT cuenta despues de filtrar"
    return "but, on, a, the y ok fuera; inmostly, war-chant y though dentro, tambien las viejas"


prueba("voz: las palabras funcionales no son dificiles",
       _las_palabras_funcionales_no_son_dificiles)


def _un_sonido_facil_no_se_senala_como_error():
    """«for» entendido «or»: salia /f/ con «Error típico: casi ninguno; es igual
    que la f española», que se contradice. Si el unico cambio es un sonido que
    la ficha da por facil, no se señala: se dice que no se entendio la palabra."""
    voz = ui.voz
    assert voz._comparar("for", "or") == ("f", "facil"), voz._comparar("for", "or")
    assert voz.fonema_que_cambia("for", "or") is None
    assert voz._comparar("for", "far") == ("ɔ", ""), "un cambio que si falla se sigue señalando"
    assert voz.fonema_que_cambia("tragic", "magic") == "t" and voz.fonema_que_cambia("fox", "fix") == "ɑ"
    c = voz.Correccion(resumen="Casi.", detalles=[voz.DetallePalabra(
        palabra="for", fonema="f", sonido_que_falla="x", como_colocar_la_boca="y")])
    d = voz.fijar_fonemas(c, [("for", "or")]).detalles[0]
    assert d.fonema == voz.SIN_FONEMA, d
    assert "no suele" in d.sonido_que_falla and "/f/" in d.sonido_que_falla, d
    assert "Error típico" not in d.sonido_que_falla and "Repítela entera" in d.como_colocar_la_boca, d
    return "for/or sin /f/ señalada; for/far sigue en /ɔ/"


prueba("voz: un sonido facil no se señala como error",
       _un_sonido_facil_no_se_senala_como_error)


def _cada_palabra_fallada_suena_sola():
    """audios_de_palabras pide cada palabra una vez, con tope, y el detalle de la
    correccion pinta su reproductor."""
    pedidas = []
    viejo = ui.voz.generar_audio_correcto
    try:
        # «sin» se pide pero no tiene audio (sin clave ni cache): no entra.
        ui.voz.generar_audio_correcto = lambda t, *a, **k: (pedidas.append(t) or (None if t == "sin" else f"/tmp/{t}.mp3"))
        audios = ui.voz.audios_de_palabras(["warn", "warn", "sin"] + [f"p{i}" for i in range(10)])
    finally:
        ui.voz.generar_audio_correcto = viejo
    assert pedidas.count("warn") == 1, pedidas
    assert len(pedidas) == ui.voz.MAX_AUDIOS_PALABRA, pedidas
    assert "sin" not in audios and audios["warn"] == "/tmp/warn.mp3", audios
    html = ui._detalle_de_voz(_detalle(palabra="warn", fonema="w"), str(TMP / "warn.mp3"))
    assert "Escuchar la palabra" in html and "warn.mp3" in html, html
    assert "Escuchar la palabra" not in ui._detalle_de_voz(_detalle(palabra="warn", fonema="w"))
    return "una vez por palabra, con tope, y con reproductor"


prueba("voz: cada palabra fallada suena sola", _cada_palabra_fallada_suena_sola)


def _la_ipa_de_la_ia_se_marca():
    base = dict(palabra_superficie="zorble", oracion="", lema="zorble", lema_buscado="zorble",
                pos_spacy=None, categoria=None, sentido=None, etiquetas_sentido=[], similitud=None,
                n_sentidos_candidatos=0, ipa_uk="/ˈzɔːbəl/", ipa_us="/ˈzɔɹbəl/", audio_uk=None,
                audio_us=None, audio_generado=False, definicion_contextual=None,
                explicacion_gramatical=None, explicacion_adaptada=None, ejemplo_simplificado=None,
                banda_lector="intermedio", frecuencia_zipf=None, desde_cache=False, avisos=[])
    con = ui._ficha(lexicon_mod.ResultadoLexico(**base, ipa_generada_por_ia=True), "es")
    sin = ui._ficha(lexicon_mod.ResultadoLexico(**base), "es")
    assert "IPA generada por IA" in con and "IPA generada por IA" not in sin, con
    return "marcada solo cuando la escribio la IA"


prueba("lexico: la ipa de la ia se marca", _la_ipa_de_la_ia_se_marca)


# --- Auditoria de Codex sobre 5033e69 (13 sep 2026) --------------------------

def _las_alternativas_sin_marginales_y_por_afinidad():
    """Hallazgo 3: las alternativas que ve OpenAI salian de la lista SIN filtrar
    («awful» mandaba 4 marginales de 7) y cortadas por orden del volcado («set
    the table» es la novena acepcion de «set» y nunca llegaba)."""
    E, S = lexicon_mod.EntradaDiccionario, lexicon_mod.Sentido
    e = E("set", "verb", [], None, None, None, None)
    pares = [(e, S(f"Relleno {i}.", "verb", [])) for i in range(8)]
    pares.insert(3, (e, S("To sit; to be seated.", "verb", ["obsolete"])))
    pares.append((e, S("To arrange with dishes and cutlery, to set the table.", "verb", [])))
    limpias = [s.glosa for _, s in lexicon_mod._sin_marginales(pares)]
    assert "To sit; to be seated." not in limpias and len(limpias) == 9, limpias
    todas_raras = pares[3:4]
    assert lexicon_mod._sin_marginales(todas_raras) == todas_raras

    class _Embebedor:
        def encode(self, textos, normalize_embeddings=True):
            return lexicon_mod.np.array([[1.0, 0.0] if ("table" in t or t.startswith("She")) else [0.0, 1.0]
                             for t in textos])

    viejo = lexicon_mod._cargar_embebedor
    try:
        lexicon_mod._cargar_embebedor = lambda: _Embebedor()
        elegidas = lexicon_mod._mas_afines("She set the table.", limpias, n=8, obligada="Relleno 7.")
    finally:
        lexicon_mod._cargar_embebedor = viejo
    assert len(elegidas) == 8, elegidas
    mesa = next((g for g in elegidas if g.endswith("set the table.")), None)
    assert mesa and elegidas.index(mesa) < elegidas.index("Relleno 0."), elegidas
    assert elegidas[0] == "Relleno 7.", "la acepcion elegida va siempre, y delante si no cabia"

    def _roto():
        raise RuntimeError("sin modelo")

    try:
        lexicon_mod._cargar_embebedor = _roto
        sin_modelo = lexicon_mod._mas_afines("x", limpias, n=8)
    finally:
        lexicon_mod._cargar_embebedor = viejo
    assert sin_modelo == limpias[:8], "sin embeddings se degrada al orden del volcado"
    fuente = pathlib.Path(lexicon_mod.__file__).read_text(encoding="utf-8")
    assert "_sin_marginales(pares)" in fuente.split("def consultar")[1]
    return "marginales fuera, set the table dentro, elegida siempre"


prueba("lexico: alternativas sin marginales y por afinidad",
       _las_alternativas_sin_marginales_y_por_afinidad)


def _la_ficha_no_pinta_markdown_del_modelo():
    """Hallazgo 4: gr.Markdown sanea el HTML, pero un enlace o una imagen
    remota escritos por el modelo se pintaban."""
    malicioso = "Mira ![x](https://evil.example/p.png) y [clic](https://evil.example) <b>hola</b>\n# Titulo"
    r = lexicon_mod.ResultadoLexico(
        palabra_superficie="[w](https://evil.example)", oracion="", lema="w", lema_buscado="w",
        pos_spacy=None, categoria="noun", sentido="A *thing* [x](y).", etiquetas_sentido=["_raro_"],
        similitud=None, n_sentidos_candidatos=1, ipa_uk="/*a*/", ipa_us=None, audio_uk=None,
        audio_us=None, audio_generado=False, definicion_contextual=malicioso,
        explicacion_gramatical=malicioso, explicacion_adaptada=malicioso,
        ejemplo_simplificado=malicioso, banda_lector="intermedio", frecuencia_zipf=None,
        desde_cache=False, avisos=[], traduccion=malicioso)
    ficha = ui._ficha(r, "es")
    for trozo in ("](", "![", "<b>", "\n# Titulo", "*thing*", "_raro_", "/*a*/"):
        assert trozo not in ficha, (trozo, ficha)
    assert "evil.example" in ficha, "el texto se ve literal, no se borra"
    # Lo que es de OpenAI lleva «· IA»; lo del diccionario, no.
    for rotulo in ("Traducción · IA", "Aquí significa · IA", "Gramática · IA"):
        assert rotulo in ficha, (rotulo, ficha)
    assert "Diccionario · IA" not in ficha, ficha
    return "enlaces, imagenes y html literales; secciones de ia marcadas"


prueba("lexico: la ficha no pinta markdown del modelo", _la_ficha_no_pinta_markdown_del_modelo)


def _dos_lectores_a_la_vez_pagan_una_y_se_marca_ia():
    """Hallazgos 2 y 1: sin candado, dos consultas iguales a la vez (Gradio
    atiende 8) pagaban dos veces; y con `definicion_ia` en blanco la respuesta
    de la IA salia sin marcar."""
    import threading
    import time
    from unittest.mock import patch
    llamadas = []

    def _definir(_cliente, **kw):
        llamadas.append(kw["palabra"])
        time.sleep(0.3)
        return {"definicion_ia": "   ", "traduccion": "zorblar", "definicion_contextual": "Hace algo raro.",
                "explicacion_gramatical": None, "explicacion_adaptada": None,
                "ejemplo_simplificado": None, "ipa_us": None, "ipa_uk": None}

    class _Dicc:
        def buscar(self, _p):
            return []

        def cerrar(self):
            pass

    ruta = TMP / "lex_candado.db"
    ruta.unlink(missing_ok=True)
    c = lexicon_mod.ConsultorLexico.__new__(lexicon_mod.ConsultorLexico)
    c.diccionario, c.cache = _Dicc(), lexicon_mod.CacheLexico(str(ruta))
    c.modelo_openai, c._sin_clave, c._cliente_openai = "modelo-prueba", False, object()
    resultados, errores = [], []

    def _consultar():
        try:
            resultados.append(c.consultar("zorble", "They zorble at dawn.", 1.0))
        except Exception as e:  # noqa: BLE001
            errores.append(e)

    try:
        with patch.object(lexicon_mod, "_resolver_lema_y_categoria",
                          return_value=("zorble", "zorble", "verb", "VERB")), \
             patch.object(lexicon_mod, "_pedir_definicion_ia", _definir), \
             patch.object(lexicon_mod, "_generar_audio_tts", lambda *a, **k: (None, False)):
            hilos = [threading.Thread(target=_consultar) for _ in range(2)]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join(10)
    finally:
        c.cerrar()
    assert not errores, errores
    assert len(resultados) == 2 and len(llamadas) == 1, (len(resultados), llamadas)
    assert sum(r.llamadas_de_pago for r in resultados) == 1, [r.llamadas_de_pago for r in resultados]
    assert sorted(r.desde_cache for r in resultados) == [False, True]
    for r in resultados:
        assert r.generado_por_ia and r.definicion_ia == "Hace algo raro.", r
    ficha = ui._ficha(resultados[0], "es")
    assert "No hay entrada de diccionario" not in ficha and "inteligencia artificial" in ficha, ficha
    return "una sola llamada de pago y la respuesta marcada como ia"


prueba("lexico: dos lectores a la vez pagan una y se marca ia",
       _dos_lectores_a_la_vez_pagan_una_y_se_marca_ia)


# --- El fonema de la correccion, determinista (f4, 13 sep 2026) --------------
# Con la misma grabacion («magic» por «tragic») el modelo dijo /dʒ/ y luego
# /tʃ/, con un consejo de labios falso; el error real es /tr/ -> /m/.

def _la_ipa_se_trocea_en_fonemas():
    seg = ui.fonemas.segmentar
    assert seg("/ˈtɹædʒɪk/") == ["t", "ɹ", "æ", "dʒ", "ɪ", "k"], seg("/ˈtɹædʒɪk/")
    assert seg("/θɔːt/") == ["θ", "ɔ", "t"], seg("/θɔːt/")
    assert seg("/ˈmoʊstli/, /ˈmoʊsli/") == ["m", "oʊ", "s", "t", "l", "i"]
    assert seg(None) == [] and seg("") == []
    # CMUdict tapa el hueco de Kaikki, que no trae ni «tragic» ni «magic».
    for palabra in ("tragic", "magic", "Tragic"):
        ipa, variante = ui.fonemas.ipa_de_palabra(palabra)
        assert ipa and variante == "US", (palabra, ipa, variante)
    assert ui.fonemas.ipa_de_palabra("zzqxvj") == (None, None)
    return "fonemas en orden; tragic y magic con ipa americana"


prueba("voz: la ipa se trocea en fonemas", _la_ipa_se_trocea_en_fonemas)


def _el_fonema_sale_de_comparar_y_no_del_modelo():
    voz = ui.voz
    assert voz.fonema_que_cambia("tragic", "magic") == "t"
    assert voz.fonema_que_cambia("fox", "fix") == "ɑ"
    assert voz.fonema_que_cambia("tragic", "") is None
    assert voz.fonema_que_cambia("zzqxvj", "magic") is None
    assert voz.fonema_que_cambia("tragic", "tragic") is None

    def _cliente_falso():
        # El modelo, como en el Space: un fonema que no es y un consejo falso.
        def parse(**_kw):
            c = voz.Correccion(resumen="Casi.", detalles=[
                voz.DetallePalabra(palabra="tragic", fonema="dʒ", sonido_que_falla="como la ch",
                                   como_colocar_la_boca="Junta los labios y sube la lengua."),
                voz.DetallePalabra(palabra="zzqxvj", fonema="ʃ", sonido_que_falla="sh",
                                   como_colocar_la_boca="Redondea los labios.")])
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=c))])
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))

    viejo = voz._cliente
    try:
        voz._cliente = _cliente_falso
        pares = [("tragic", "magic"), ("zzqxvj", "magic")]
        una = voz.explicar_correccion(["tragic", "zzqxvj"], entendidas=pares)
        otra = voz.explicar_correccion(["tragic", "zzqxvj"], entendidas=pares)
        sin_pares = voz.explicar_correccion(["tragic"])
    finally:
        voz._cliente = viejo
    t, raro = una.detalles
    ficha_t = ui.articulacion.FICHAS["t"]
    assert t.fonema == "t" and ficha_t.lengua in t.como_colocar_la_boca, t
    assert "Junta los labios" not in t.como_colocar_la_boca and ficha_t.trampa in t.sonido_que_falla, t
    assert una.detalles[0].model_dump() == otra.detalles[0].model_dump(), "misma grabacion, mismo consejo"
    assert raro.fonema == voz.SIN_FONEMA and "Redondea" not in raro.como_colocar_la_boca, raro
    assert "diccionarios de pronunciación" in raro.sonido_que_falla, raro
    assert sin_pares.detalles[0].fonema == voz.SIN_FONEMA, sin_pares
    assert una.resumen == "Casi.", "el resumen sigue siendo del modelo"
    html = ui._detalle_de_voz(t)
    assert "/t/" in html and "(sin transcripción" not in html, html
    return "t desde la ipa, consejo de la ficha, igual en dos llamadas"


prueba("voz: el fonema sale de comparar y no del modelo",
       _el_fonema_sale_de_comparar_y_no_del_modelo)


def _los_compuestos_se_corrigen_y_suenan_por_pieza():
    """«war-chant» se evalua entero, pero el modelo lo explica en «war» y
    «chant»: no habia fonema ni audio para ninguna de las dos (Miguel, e6)."""
    voz = ui.voz
    assert voz.piezas("war-chant") == ["war", "chant"] and voz.piezas("well-known man") == ["well", "known", "man"]
    # Se entendio «war chart»: el cambio cae en «chant» (/æ/ -> /ɑ/), no en «war».
    assert voz._comparar("war-chant", "war chart", pieza="chant") == ("æ", "")
    assert voz._comparar("war-chant", "war chart", pieza="war") == (None, "igual")
    c = voz.Correccion(resumen="Casi.", detalles=[
        voz.DetallePalabra(palabra="war", fonema="w", sonido_que_falla="x", como_colocar_la_boca="y"),
        voz.DetallePalabra(palabra="chant", fonema="tʃ", sonido_que_falla="x", como_colocar_la_boca="y")])
    # «war» se dijo bien: sin detalle, porque «chant» si falla (f4).
    detalles = voz.fijar_fonemas(c, [("war-chant", "war chart")]).detalles
    assert [d.palabra for d in detalles] == ["chant"] and detalles[0].fonema == "æ", detalles
    # Si todas las piezas suenan igual, se quedan: la correccion no se vacia.
    iguales = voz.Correccion(resumen="Casi.", detalles=[
        voz.DetallePalabra(palabra="war", fonema="w", sonido_que_falla="x", como_colocar_la_boca="y"),
        voz.DetallePalabra(palabra="chant", fonema="tʃ", sonido_que_falla="x", como_colocar_la_boca="y")])
    assert len(voz.fijar_fonemas(iguales, [("war-chant", "war chant")]).detalles) == 2

    # practicar pide el audio del compuesto, de sus piezas y de lo que nombra la correccion.
    pedidas = []
    viejos = (voz.transcribir_audio, voz.explicar_correccion, voz.generar_audio_correcto)
    try:
        voz.transcribir_audio = lambda _r: "the war chart"
        voz.explicar_correccion = lambda *a, **k: voz.Correccion(resumen="Casi.", detalles=[
            voz.DetallePalabra(palabra="War", fonema="w", sonido_que_falla="x", como_colocar_la_boca="y")])
        voz.generar_audio_correcto = lambda t, *a, **k: (pedidas.append(t) or f"/tmp/{t}.mp3")
        sesion = voz.practicar(str(TMP / "nada.wav"), "The war-chant", guardar_fallos=False)
    finally:
        voz.transcribir_audio, voz.explicar_correccion, voz.generar_audio_correcto = viejos
    assert {"war-chant", "war", "chant"} <= set(sesion.audios_palabras), sesion.audios_palabras
    assert pedidas.count("war") == 1, pedidas

    # La ficha de la correccion: la pieza sin audio propio usa el del compuesto.
    sesion2 = voz.SesionVoz(evaluacion=voz.evaluar_pronunciacion("The war-chant", "the war chart"),
                            correccion=voz.Correccion(resumen="Casi.", detalles=[
                                _detalle(palabra="chant", fonema="æ")]),
                            audio_correcto=None, audios_palabras={"war-chant": str(TMP / "war_chant.mp3")})
    viejo_practicar, viejo_falta = ui.voz.practicar, ui.config.falta
    audio = TMP / "compuesto.wav"
    audio.write_bytes(b"RIFF")
    try:
        ui.config.falta = lambda: []
        ui.voz.practicar = lambda *a, **k: sesion2
        _, veredicto, _ = ui._practicar(str(audio), "The war-chant")
    finally:
        ui.voz.practicar, ui.config.falta = viejo_practicar, viejo_falta
    assert "Escuchar la palabra" in str(veredicto) and "war_chant.mp3" in str(veredicto), veredicto

    # Un solo acento: el preferido si algun diccionario lo trae; si no, el otro, dicho.
    assert ui.fonemas.ipa_de_palabra("tragic", "UK") == ("/ˈtɹædʒɪk/", "US")
    assert ui.fonemas.ipa_de_palabra("tragic") == ui.fonemas.ipa_de_palabra("tragic", "US")
    return "fonema en su pieza, audio de cada pieza y un acento"


prueba("voz: los compuestos se corrigen y suenan por pieza",
       _los_compuestos_se_corrigen_y_suenan_por_pieza)


def _la_ficha_de_un_compuesto_no_es_la_de_su_parte():
    """Miguel consulto «war-chant» y la ficha salio como «war» con /wɔɹ/: la
    entrada tiene que decir que es de la parte, y la IPA y el audio tienen que
    ser del compuesto (la IPA, de la IA y marcada)."""
    from unittest.mock import patch
    E, S = lexicon_mod.EntradaDiccionario, lexicon_mod.Sentido
    guerra = E("war", "noun", [S("Organised, large-scale, armed conflict.", "noun", [])],
               "/wɔː/", "/wɔɹ/", None, "https://upload.wikimedia.org/war.ogg")
    pedidas = []

    class _Dicc:
        def buscar(self, p):
            return [guerra] if p == "war" else []

        def cerrar(self):
            pass

    def _explicar(_cliente, **kw):
        pedidas.append(kw)
        base = {"traduccion": "canto de guerra", "acepcion_usada": "",
                "definicion_contextual": "Un canto de guerra.", "explicacion_gramatical": "Sustantivo compuesto.",
                "explicacion_adaptada": "Canción para la guerra.", "ejemplo_simplificado": "They sang a war-chant."}
        return {**base, "ipa_us": "/ˈwɔɹˌtʃænt/", "ipa_uk": "/ˈwɔːˌtʃɑːnt/"} if kw.get("compuesto_de") else base

    def _consultor():
        c = lexicon_mod.ConsultorLexico.__new__(lexicon_mod.ConsultorLexico)
        c.diccionario, c.cache = _Dicc(), lexicon_mod.CacheLexico(":memory:")
        c.modelo_openai, c._sin_clave, c._cliente_openai = "modelo-prueba", False, object()
        return c

    oracion = "The warriors raised a war-chant."
    with patch.object(lexicon_mod, "_resolver_lema_y_categoria", return_value=("war", "war", "noun", "NOUN")), \
         patch.object(lexicon_mod, "_pedir_explicacion_openai", _explicar), \
         patch.object(lexicon_mod, "_generar_audio_tts", lambda *a, **k: (None, False)):
        c = _consultor()
        try:
            r = c.consultar("war-chant", oracion, 1.0)
            normal = c.consultar("war", oracion, 1.0)
        finally:
            c.cerrar()
    assert r.compuesto == "war-chant" and r.parte_del_diccionario == "war", r
    assert pedidas[0].get("compuesto_de") == "war" and "compuesto_de" not in pedidas[1], pedidas
    assert r.ipa_us == "/ˈwɔɹˌtʃænt/" and r.ipa_generada_por_ia, r
    assert r.audio_us is None, "el audio de «war» no es el de «war-chant»"
    assert r.sentido.startswith("Organised"), "la acepcion sigue siendo de la parte"
    assert normal.compuesto is None and normal.ipa_us == "/wɔɹ/" and not normal.ipa_generada_por_ia, normal
    ficha = ui._ficha(r, "es")
    assert "una parte de «war-chant»" in ficha and "IPA generada por IA" in ficha, ficha
    assert "/wɔɹ/" not in ficha, ficha
    assert lexicon_mod._es_compuesto("well-known") and not lexicon_mod._es_compuesto("-war")
    return "entrada de la parte dicha, ipa del compuesto marcada, palabra normal igual"


prueba("lexico: la ficha de un compuesto no es la de su parte",
       _la_ficha_de_un_compuesto_no_es_la_de_su_parte)


def _la_ipa_y_el_audio_son_de_la_forma_escrita():
    """«eclipses» salia con los botones US y UK sin IPA (Miguel, 14 sep), y al
    reproducirlo aparecio algo peor: la forma flexionada heredaba la fonetica
    del lema, «went» /ɡoʊ/ con el audio de «go». Orden: Kaikki de la forma, CMU
    de la forma (americano), el lema solo si coincide, y lo que falte, OpenAI
    marcado como IA. La britanica nunca se deduce de CMU."""
    from unittest.mock import patch
    E, S = lexicon_mod.EntradaDiccionario, lexicon_mod.Sentido

    def entrada(palabra, pos, uk=None, us=None, audio=None):
        return E(palabra, pos, [S(f"Sentido de {palabra}.", pos, [])], uk, us, None, audio)

    dicc = {
        "go": [entrada("go", "verb", "/ɡəʊ/", "/ɡoʊ/", "https://upload.wikimedia.org/go.ogg")],
        "think": [entrada("think", "verb", "/θɪŋk/", "/θɪŋk/", "https://upload.wikimedia.org/think.ogg")],
        "thought": [entrada("thought", "noun", "/θɔːt/", "/θɔt/")],
        "book": [entrada("book", "noun", "/bʊk/", "/bʊk/", "https://upload.wikimedia.org/book.ogg")],
        "run": [entrada("run", "verb", "/ɹʌn/", "/ɹʌn/")],
        "eclipse": [entrada("eclipse", "verb")],
    }
    lemas = {"went": ("go", "verb"), "go": ("go", "verb"), "thought": ("think", "verb"),
             "books": ("book", "noun"), "running": ("run", "verb"), "eclipses": ("eclipse", "verb")}
    pedidas = []

    class _Dicc:
        def buscar(self, p):
            return list(dicc.get(p, []))

        def cerrar(self):
            pass

    def _explicar(_cliente, **kw):
        pedidas.append(kw)
        base = {"traduccion": "eclipsa", "acepcion_usada": "", "definicion_contextual": "Eclipsa.",
                "explicacion_gramatical": "Verbo.", "explicacion_adaptada": "Hace sombra.",
                "ejemplo_simplificado": "She eclipses them."}
        # La americana del modelo es otra a proposito: no puede pisar la de CMU.
        return {**base, "ipa_us": "/ɪˈklɪpsɪz/", "ipa_uk": "/ɪˈklɪpsɪz/"} if kw.get("pedir_ipa") else base

    def _consultor(con_clave):
        c = lexicon_mod.ConsultorLexico.__new__(lexicon_mod.ConsultorLexico)
        c.diccionario, c.cache = _Dicc(), lexicon_mod.CacheLexico(":memory:")
        c.modelo_openai, c._sin_clave, c._cliente_openai = "modelo-prueba", not con_clave, (object() if con_clave else None)
        return c

    oracion = "In his eyes she eclipses the whole of her sex."
    resolver = lambda _o, w: (lemas[w][0], lemas[w][0], lemas[w][1], lemas[w][1].upper())
    with patch.object(lexicon_mod, "_resolver_lema_y_categoria", side_effect=resolver), \
         patch.object(lexicon_mod, "_pedir_explicacion_openai", _explicar), \
         patch.object(lexicon_mod, "_generar_audio_tts", lambda *a, **k: (None, False)):
        c = _consultor(con_clave=False)
        try:
            sin = {w: c.consultar(w, oracion, 1.0, usar_openai=False) for w in lemas}
        finally:
            c.cerrar()
        c = _consultor(con_clave=True)
        try:
            con = {w: c.consultar(w, oracion, 1.0) for w in ("eclipses", "go")}
        finally:
            c.cerrar()

    # Sin clave: diccionarios solos, nada de IA.
    assert (sin["went"].ipa_us, sin["went"].ipa_uk) == ("/wɛnt/", None), sin["went"]
    assert sin["went"].audio_us is None and sin["went"].audio_uk is None, "el audio de «go» no es el de «went»"
    assert (sin["thought"].ipa_us, sin["thought"].ipa_uk) == ("/θɔt/", "/θɔːt/"), "la entrada propia de la forma"
    assert sin["thought"].audio_us is None, "el audio de «think» no es el de «thought»"
    assert (sin["books"].ipa_us, sin["books"].audio_us) == ("/bʊks/", None), sin["books"]
    assert sin["running"].ipa_us == "/ˈɹʌnɪŋ/" and sin["running"].ipa_uk is None, sin["running"]
    assert (sin["eclipses"].ipa_us, sin["eclipses"].ipa_uk) == ("/ɪkˈlɪpsɪz/", None), sin["eclipses"]
    assert (sin["go"].ipa_us, sin["go"].audio_us) == ("/ɡoʊ/", "https://upload.wikimedia.org/go.ogg"), "forma = lema, igual que antes"
    assert not any(r.ipa_generada_por_ia for r in sin.values())

    # Con clave: la britanica que falta la pone OpenAI, marcada; la americana de CMU se queda.
    e = con["eclipses"]
    assert (e.ipa_us, e.ipa_uk, e.ipa_generada_por_ia) == ("/ɪkˈlɪpsɪz/", "/ɪˈklɪpsɪz/", True), e
    assert pedidas[0].get("pedir_ipa") is True and "pedir_ipa" not in pedidas[1], pedidas
    assert not con["go"].ipa_generada_por_ia and con["go"].ipa_uk == "/ɡəʊ/", con["go"]
    assert "IPA generada por IA" in ui._ficha(e, "es")
    return "went, thought, books, running y eclipses con su forma; la britanica que falta, de la ia y marcada"


prueba("lexico: la ipa y el audio son de la forma escrita, no del lema",
       _la_ipa_y_el_audio_son_de_la_forma_escrita)


def _el_aviso_de_acepcion_dudosa_se_va_cuando_openai_la_revisa():
    """f4: «house» traia «La acepción elegida es dudosa» con dudoso=false. Con
    OpenAI revisando las alternativas, el aviso ya no aplica; sin OpenAI, si."""
    from unittest.mock import patch
    E, S = lexicon_mod.EntradaDiccionario, lexicon_mod.Sentido
    casa = E("house", "noun", [S("A structure serving as an abode.", "noun", []),
                               S("A building used for a purpose.", "noun", [])],
             None, "/haʊs/", None, "https://upload.wikimedia.org/house.ogg")
    aviso = "acepcion provisional: margen bajo (0.010) frente a otra acepcion: A building used for a purpose."

    class _Dicc:
        def buscar(self, p):
            return [casa] if p == "house" else []

        def cerrar(self):
            pass

    def _explicar(_cliente, **kw):
        assert kw.get("alternativas"), "la eleccion dudosa no mando alternativas"
        return {"traduccion": "casa", "acepcion_usada": "", "definicion_contextual": "Una casa.",
                "explicacion_gramatical": "Sustantivo.", "explicacion_adaptada": "Donde vives.",
                "ejemplo_simplificado": "The house is big."}

    c = lexicon_mod.ConsultorLexico.__new__(lexicon_mod.ConsultorLexico)
    c.diccionario, c.cache = _Dicc(), lexicon_mod.CacheLexico(":memory:")
    c.modelo_openai, c._sin_clave, c._cliente_openai = "modelo-prueba", False, object()
    with patch.object(lexicon_mod, "_resolver_lema_y_categoria", return_value=("house", "house", "noun", "NOUN")), \
         patch.object(lexicon_mod, "_elegir_sentido", lambda o, pares: (pares[0][1], 0.31, [aviso])), \
         patch.object(lexicon_mod, "_mas_afines", lambda o, g, n=8, obligada=None: list(dict.fromkeys(g))[:n]), \
         patch.object(lexicon_mod, "_pedir_explicacion_openai", _explicar):
        try:
            previa = c.consultar("house", "The house stood alone.", 1.0, usar_openai=False)
            completa = c.consultar("house", "The house stood alone.", 1.0)
        finally:
            c.cerrar()
    assert any("provisional" in a for a in previa.avisos), previa.avisos
    assert not any("provisional" in a for a in completa.avisos), completa.avisos
    return "el aviso sale en la vista previa y se va con la revision de openai"


prueba("lexico: el aviso de acepcion dudosa se va cuando openai la revisa",
       _el_aviso_de_acepcion_dudosa_se_va_cuando_openai_la_revisa)


def _las_animaciones_de_la_boca_se_sirven_como_archivo():
    """Miguel: animacion de como se mueven boca y lengua, primero por sonido y
    luego en una palabra. En la tabla, una por sonido y acento; en la
    correccion, el sonido y la palabra. Como archivos servidos, no en linea."""
    viejo = ui.DIR_SVG_ARTICULACION
    carpeta = TMP / "svg_articulacion"
    try:
        ui.DIR_SVG_ARTICULACION = carpeta
        tabla = ui._tabla_afi_html()
        n_img = tabla.count('class="ll-afi-anim"')
        esperadas = len(ui.articulacion.inventario("ga")) + len(ui.articulacion.inventario("rp"))
        assert n_img == esperadas, (n_img, esperadas)
        assert "<svg" not in tabla, "los svg no van en linea"
        archivos = sorted(carpeta.glob("*.svg"))
        assert len(archivos) == esperadas, len(archivos)
        assert all(a.read_text(encoding="utf-8").lstrip().startswith("<svg") for a in archivos)
        marcas = {a: a.stat().st_mtime_ns for a in archivos}
        ui._tabla_afi_html()
        assert all(a.stat().st_mtime_ns == marcas[a] for a in archivos), "reescribio svg iguales"

        voz = ui.voz
        html = ui._detalle_de_voz(voz.DetallePalabra(palabra="tragic", fonema="t",
                                                     sonido_que_falla="x", como_colocar_la_boca="y"))
        assert "Ver cómo se mueve la boca" in html and html.count("<img") == 2, html
        assert "palabra_" in html and "ga_0074.svg" in html, html
        sin = ui._detalle_de_voz(voz.DetallePalabra(palabra="zzqxvj", fonema="ninguno",
                                                    sonido_que_falla="x", como_colocar_la_boca="y"))
        assert "<img" not in sin, sin
        # Sin fonema que señalar («tragic» entendido como «Mahic»), la palabra si.
        solo_palabra = ui._detalle_de_voz(voz.DetallePalabra(palabra="tragic", fonema="ninguno",
                                                             sonido_que_falla="x", como_colocar_la_boca="y"))
        assert solo_palabra.count("<img") == 1 and "palabra_" in solo_palabra, solo_palabra
    finally:
        ui.DIR_SVG_ARTICULACION = viejo
    assert str(viejo) in ui.RUTAS_PERMITIDAS, "la carpeta de los svg no se sirve"
    return f"{n_img} animaciones en la tabla, sonido y palabra en la correccion"


prueba("afi: las animaciones de la boca se sirven como archivo",
       _las_animaciones_de_la_boca_se_sirven_como_archivo)


# --- Resultado ------------------------------------------------------------

print("\n" + "=" * 70)
if FALLOS:
    print(f"{len(FALLOS)} FALLOS de {HECHAS} pruebas:\n")
    for f in FALLOS:
        print("  -", f)
    sys.exit(1)
print(f"Las {HECHAS} pruebas extremas pasan: ningun manejador lanzo excepcion.")
