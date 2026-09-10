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
os.environ["LITERALEVEL_DATOS"] = tempfile.mkdtemp(prefix="literalevel_pruebas_")
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
import config  # noqa: E402
config.cargar = lambda *a, **k: None
os.environ.pop("OPENAI_API_KEY", None)
import ficha as ficha_mod  # noqa: E402
import reader  # noqa: E402
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
       lambda: ui._ip(_Pet(ip="203.0.113.7, 10.0.0.1")))
prueba("cae al host del cliente si no hay cabecera",
       lambda: ui._ip(_Pet(host="198.51.100.9")))
prueba("sin peticion no revienta", lambda: ui._ip(None))
prueba("cabeceras raras no rompen", lambda: ui._ip(_Pet(ip=None, host=None)))
prueba("el tope se respeta",
       lambda: sum(ui._dentro_del_limite(_Pet(ip="10.1.1.1"), "p1", 4)
                   for _ in range(9)))
prueba("una IP no consume la cuota de otra",
       lambda: (all(ui._dentro_del_limite(_Pet(ip="10.2.2.2"), "p2", 2)
                    for _ in range(2)),
                ui._dentro_del_limite(_Pet(ip="10.3.3.3"), "p2", 2)))
prueba("tope 0 significa sin limite",
       lambda: all(ui._dentro_del_limite(_Pet(ip="10.4.4.4"), "p3", 0)
                   for _ in range(200)))
prueba("cubos distintos no se mezclan",
       lambda: (ui._dentro_del_limite(_Pet(ip="10.5.5.5"), "lexico", 1),
                ui._dentro_del_limite(_Pet(ip="10.5.5.5"), "voz", 1)))
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
prueba("session_hash con ../ no escapa",
       lambda: _con_nube(lambda: (
           ui.BASE_DATOS_LECTOR / "lectores") in ui._dir_lector(
               _Peticion("../../etc/passwd")).parents))
prueba("session_hash vacio cae en 'anonimo'",
       lambda: _con_nube(lambda: ui._dir_lector(_Peticion("")).name))
prueba("sin peticion tampoco revienta",
       lambda: _con_nube(lambda: ui._dir_lector(None).name))
prueba("session_hash larguisimo se recorta",
       lambda: _con_nube(lambda: len(ui._dir_lector(_Peticion("z" * 500)).name)))
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
       lambda: sorted({ui._cefr(v / 20) for v in range(41)}))
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

prueba("todas las paletas dan css",
       lambda: [k for k in paletas_mod.PALETAS if not ui._css_paleta(k).startswith("<style>")]
       or "las cinco")
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
       lambda: [ui.scoring.anchor_cefr(y) for y in (0.5, 1.5, 2.5, 3.5, 4.5)])


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
        base = pathlib.Path(tempfile.mkdtemp(prefix="cupo_"))
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
        base = pathlib.Path(tempfile.mkdtemp(prefix="carrera_"))
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
        base = pathlib.Path(tempfile.mkdtemp(prefix="apuntes_"))
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
    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    os.environ["LITERALEVEL_CUENTAS"] = "jefe:LLAVE-A:0"
    ui._CODIGO_SESION.clear()
    try:
        return fn()
    finally:
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

prueba("cuantos libros vacio no ensena un error de Python",
       # `gr.Number` vacio manda None. Antes salia "int() argument must be...".
       lambda: "int()" not in str(ui._recomendar(None, None))
               and "sin error de Python")

# --- Resultado ------------------------------------------------------------

print("\n" + "=" * 70)
if FALLOS:
    print(f"{len(FALLOS)} FALLOS de {HECHAS} pruebas:\n")
    for f in FALLOS:
        print("  -", f)
    sys.exit(1)
print(f"Las {HECHAS} pruebas extremas pasan: ningun manejador lanzo excepcion.")
