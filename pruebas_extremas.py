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
        "import os, sys, tempfile" + chr(10) +
        "tmp = tempfile.mkdtemp()" + chr(10) +
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


# --- Resultado ------------------------------------------------------------

print("\n" + "=" * 70)
if FALLOS:
    print(f"{len(FALLOS)} FALLOS de {HECHAS} pruebas:\n")
    for f in FALLOS:
        print("  -", f)
    sys.exit(1)
print(f"Las {HECHAS} pruebas extremas pasan: ningun manejador lanzo excepcion.")
