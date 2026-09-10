"""Interfaz de LiteraLevel en Gradio: une los seis puntos en una sola app.

Cada pestana corresponde a un punto de la especificacion:

  1. Mi nivel      -> perfil.desde_cuestionario / desde_muestra
  2. Buscar        -> catalogo.buscar / por_nivel
  3. Leer          -> reader.cargar + scoring.Puntuador + lexicon.ConsultorLexico
  5. Pronunciacion -> voz.practicar / puntos_debiles
  6. Estado        -> diagnostico para la demo (claves, modelo, datos)

El punto 4 (diccionario, IPA y audio) vive dentro de la pestana de lectura, no
en una aparte: la especificacion pide consultar la palabra *mientras se lee*,
asi que la oracion de contexto se saca sola del capitulo abierto.

Arranque perezoso deliberado. Los tres recursos pesados -el modelo v4 (328 MB),
los embeddings del catalogo y el diccionario Kaikki (243 MB) con spaCy y
MiniLM- se cargan la primera vez que se usan, no al abrir la app. Asi la
interfaz aparece en el acto y una demo del buscador no paga el precio del
modelo de puntuacion.

Ningun manejador levanta excepciones hacia Gradio: lo que falla se devuelve
como texto legible en la propia interfaz.

Uso:  python -X utf8 app/ui.py
"""
from __future__ import annotations

import html as _html
import json
import math
import os
import re
import sys
import threading
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
# Los modulos se importan planos entre si ("import config"), asi que app/ tiene
# que estar en sys.path aunque a ui.py se le llame desde la raiz del proyecto.
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import gradio as gr

import biblioteca
import config
import cuaderno
import cuentas
import ficha as ficha
import paletas as paletas_mod
import perfil as perfil_mod
import reader
import scoring
import voz
from catalogo import Catalogo
from lexicon import ConsultorLexico

RUTA_MODELO = os.environ.get("LITERALEVEL_MODELO", str(RAIZ / "modelo_v4"))
NIVEL_POR_DEFECTO = 1.0   # se usa en la consulta lexica si aun no hay perfil

# Topes de entrada, aplicados en el servidor. Existen por dinero, no por
# estetica: la oracion y la frase acaban en llamadas de pago a OpenAI, y sin
# tope un visitante puede pegar cien mil caracteres y repetir.
LIMITE_ORACION = 400
LIMITE_FRASE_VOZ = 300
# La palabra tambien necesita tope, y no solo por dinero. Se validaba que no
# fueran mas de cuatro *palabras*, pero no su longitud: una sola "palabra" de
# miles de caracteres pasaba el filtro y salia como encabezado de la ficha,
# llenando la pantalla entera de letras. Ninguna palabra inglesa llega a 40;
# la mas larga de un diccionario normal ronda las 30.
LIMITE_PALABRA = 40
TAMANO_MAXIMO_SUBIDA = "20mb"   # un epub es un zip: sin tope, cabe una bomba

# Gradio solo sirve archivos del directorio de trabajo o del temporal del
# sistema. `lexicon.py` y `voz.py` guardan los audios de tts-1 en
# ~/.literalevel/audio, asi que sin declararla aqui la pronunciacion generada
# muere con InvalidPathError y no llega nunca al navegador.
#
# **Solo la subcarpeta de audio, nunca `~/.literalevel` entera.** Todo lo que
# cae bajo un allowed_path se sirve por GET /gradio_api/file=<ruta>, sin
# autenticacion cuando el Space es publico. Apuntar al directorio padre
# regalaba `cuaderno.db`, `voz.db`, `perfil.json` y `sesion.json` a cualquiera
# que escribiera la ruta, y los nombres estan en este mismo repositorio.
RUTAS_PERMITIDAS = [os.path.join(os.path.expanduser("~"), ".literalevel", "audio")]

# --- Datos personales: uno por lector, no uno para todos ------------------
# En local hay un solo lector y todo vive en ~/.literalevel. En un despliegue
# el proceso es UNO para todos los visitantes, asi que un unico cuaderno.db,
# perfil.json o sesion.json significa que quien entra ve el libro que subio
# otro y las palabras que consulto otro. El marcapaginas es el caso mas feo:
# `demo.load` se ejecuta en cada carga de pagina y pintaria el capitulo del
# PDF privado del visitante anterior.

# Configurable por entorno para que las PRUEBAS no escriban en los datos
# reales de quien ejecuta la app. No es teoria: la bateria de pruebas extremas
# abre libro.txt, vacio.txt, falso.txt... y los iba anotando en la biblioteca
# de verdad. Miguel abrio "Mis libros" en el movil y se encontro 24 archivos de
# prueba entre sus cuatro libros. Las pruebas ahora apuntan a un temporal.
BASE_DATOS_LECTOR = Path(os.environ.get(
    "LITERALEVEL_DATOS", Path(os.path.expanduser("~")) / ".literalevel"))
EN_LA_NUBE = bool(os.environ.get("SPACE_ID") or os.environ.get("PORT"))
_SESION_SEGURA = re.compile(r"[^A-Za-z0-9_-]")


def _dir_lector(peticion=None) -> Path:
    """Carpeta de datos de ESTE lector.

    En local, la de siempre, para no partir en dos lo que ya haya guardado.
    Desplegada, una por sesion de navegador. No es autenticacion -quien
    recupere su `session_hash` vuelve a sus datos- pero impide lo que de
    verdad importa: que un visitante tropiece con lo de otro sin buscarlo.
    """
    if not EN_LA_NUBE:
        return BASE_DATOS_LECTOR
    h = getattr(peticion, "session_hash", None) if peticion is not None else None
    limpio = _SESION_SEGURA.sub("", str(h))[:64] if h else ""
    return BASE_DATOS_LECTOR / "lectores" / (limpio or "anonimo")


# --- Freno de gasto: cuantas veces por hora puede costar dinero -----------
# Cada consulta lexica puede llamar a gpt-5 y generar audio con tts-1, y cada
# practica de voz usa whisper-1, gpt-5 y tts-1. Todo eso lo paga la clave del
# dueño. Recortar las entradas abarata el peor caso; esto lo *frena*.
#
# Los limites son por IP y por hora, generosos para leer de verdad -treinta
# palabras consultadas en una hora es mucha lectura- y estrechos para un bot.
# Las acciones que no cuestan dinero (leer, buscar, medir un capitulo) no se
# limitan: son locales.

LIMITE_CONSULTAS_HORA = int(os.environ.get("LITERALEVEL_LIMITE_CONSULTAS", "30"))
LIMITE_VOZ_HORA = int(os.environ.get("LITERALEVEL_LIMITE_VOZ", "10"))
# La sinopsis son cuatro pasajes de 900 palabras a la API por pulsacion, y
# nunca acierta en cache si el archivo cambia una palabra. Es la mas cara por
# uso de las tres, asi que su tope es el mas bajo.
LIMITE_SINOPSIS_HORA = int(os.environ.get("LITERALEVEL_LIMITE_SINOPSIS", "6"))
_VENTANA = 3600.0

_gasto: dict[str, list[float]] = {}
_CANDADO_GASTO = threading.Lock()


def _ip(peticion) -> str:
    """La IP del visitante. Detras de un proxy viene en x-forwarded-for."""
    if peticion is None:
        return "local"
    cabeceras = getattr(peticion, "headers", None) or {}
    try:
        reenviada = cabeceras.get("x-forwarded-for")
    except AttributeError:
        reenviada = None
    if reenviada:
        return str(reenviada).split(",")[0].strip()[:64]
    cliente = getattr(peticion, "client", None)
    return str(getattr(cliente, "host", None) or "desconocida")[:64]


def _minutos_para_la_siguiente(cubo: str, peticion) -> int:
    """Cuanto falta para que se libere una ficha de este cubo, en minutos.

    El aviso de tope decia siempre "60 minutos", que es la ventana entera y
    casi nunca lo que falta: quien agoto el cupo hace cincuenta y ocho minutos
    leia que tenia que esperar una hora mas. Se calcula con la marca mas
    antigua que sigue viva.
    """
    clave = f"{cubo}:{_ip(peticion)}"
    ahora = time.time()
    with _CANDADO_GASTO:
        marcas = [t for t in _gasto.get(clave, []) if ahora - t < _VENTANA]
    if not marcas:
        return 0
    faltan = _VENTANA - (ahora - min(marcas))
    return max(1, int(faltan // 60) + (1 if faltan % 60 else 0))


def _dentro_del_limite(peticion, cubo: str, tope: int) -> bool:
    """Consume una ficha del cubo. False si ya no quedan en esta hora."""
    if tope <= 0:
        return True                        # 0 o negativo = sin limite
    clave = f"{cubo}:{_ip(peticion)}"
    ahora = time.time()
    with _CANDADO_GASTO:
        marcas = [t for t in _gasto.get(clave, []) if ahora - t < _VENTANA]
        if len(marcas) >= tope:
            _gasto[clave] = marcas
            return False
        marcas.append(ahora)
        _gasto[clave] = marcas
        # Limpieza barata: sin esto el diccionario crece con cada IP nueva.
        if len(_gasto) > 5000:
            for k in [k for k, v in _gasto.items()
                      if not any(ahora - t < _VENTANA for t in v)]:
                del _gasto[k]
    return True


# --- Perfiles de acceso a lo que cuesta dinero ----------------------------
# El perfil con el que se entra se guarda por sesion de navegador, en memoria,
# y no viaja en los componentes de la interfaz: asi no acaba en un `gr.State`
# que se serializa al navegador ni se cuela en una traza de error. Se pierde
# al reiniciar el proceso, y esta bien que sea asi: se vuelve a entrar y ya.
_CODIGO_SESION: dict[str, str] = {}
_CANDADO_CODIGO = threading.Lock()


def _sesion_de(peticion) -> str:
    h = getattr(peticion, "session_hash", None) if peticion is not None else None
    return str(h or "local")


def _codigo_de(peticion) -> str | None:
    with _CANDADO_CODIGO:
        return _CODIGO_SESION.get(_sesion_de(peticion))


def _puede_pagar(peticion) -> tuple[bool, str]:
    """Comprueba el cupo Y lo consume, en una sola operacion.

    Antes esto solo preguntaba, y quien llamaba apuntaba el uso despues con
    `_apuntar_uso`. Entre las dos cosas cabia una condicion de carrera, y esta
    reproducida: con un codigo de tope 2 y veinte peticiones simultaneas
    pasaban las veinte. `cuentas.consumir` hace las dos bajo el mismo candado.
    """
    return cuentas.consumir(BASE_DATOS_LECTOR, _codigo_de(peticion))


def _entrar(usuario: str, clave: str, peticion: gr.Request = None) -> str:
    """Comprueba usuario y contrasena, y los recuerda para esta sesion.

    Antes esto pedia un codigo suelto y vivia en un acordeon cerrado dentro de
    la pestana de Pronunciacion. Nadie lo encontraba, empezando por el autor.
    """
    if not cuentas.hay_codigos():
        return ("No hace falta entrar: esta copia no tiene perfiles "
                "configurados y todo está disponible.")
    # Este manejador lo toca TODO visitante, y era el unico que no cumplia la
    # regla del modulo: una ene en la contrasena hacia que `compare_digest`
    # lanzase TypeError y la interfaz ensenaba un "Error" pelado. La causa ya
    # esta arreglada en `cuentas.verificar`, pero la puerta de entrada no puede
    # depender de que nada mas vuelva a fallar nunca: si el disco del cupo se
    # queda sin sitio o el secreto llega mal formado, el visitante tiene que
    # leer una frase, no un traceback.
    try:
        c = cuentas.verificar(usuario, clave)
        if c is None:
            with _CANDADO_CODIGO:
                _CODIGO_SESION.pop(_sesion_de(peticion), None)
            return ("**No he podido entrar.** Revisa el usuario y la contraseña; "
                    "se distinguen mayúsculas en la contraseña, no en el usuario.")
        with _CANDADO_CODIGO:
            _CODIGO_SESION[_sesion_de(peticion)] = f"{usuario.strip()}:{clave.strip()}"
        resto = cuentas.queda(BASE_DATOS_LECTOR, c)
    except Exception as e:
        # El detalle va al registro del Space y NO a la pantalla: aqui, a
        # diferencia de los demas manejadores, el mensaje de error lo lee quien
        # esta probando contrasenas, y no tiene por que aprender si el fallo
        # fue del usuario, de la clave o de la base de datos del cupo.
        print(f"_entrar: {type(e).__name__}: {e}", file=sys.stderr)
        return ("**No he podido entrar.** Ha fallado algo al comprobar el "
                "perfil; vuelve a intentarlo.")
    if resto is None:
        return (f"Has entrado como **{c.nombre}**. Sin límite de usos: ya "
                "tienes la explicación en contexto, «¿de qué trata?» y la "
                "corrección de pronunciación.")
    return (f"Has entrado como **{c.nombre}**. Te quedan **{resto}** usos de "
            "la explicación en contexto, «¿de qué trata?» y la pronunciación.")


def _salir(peticion: gr.Request = None) -> str:
    """Olvida el perfil de esta sesion. Util en un ordenador compartido."""
    with _CANDADO_CODIGO:
        _CODIGO_SESION.pop(_sesion_de(peticion), None)
    return "Has salido. Lo gratuito sigue funcionando."


def _mensaje_limite(idioma: str, minutos: int) -> str:
    if idioma == "en":
        return (f"You have reached this hour's limit of paid lookups. "
                f"Try again in about {minutos} minutes. Reading, searching and "
                f"measuring a chapter keep working: they cost nothing.")
    return (f"Has llegado al límite de consultas de esta hora. Vuelve a "
            f"intentarlo en unos {minutos} minutos. Leer, buscar y medir un "
            f"capítulo siguen funcionando: no cuestan nada.")


def _archivo_lector(nombre: str, peticion=None) -> str:
    d = _dir_lector(peticion)
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return str(d / nombre)


# --- Aspecto: hielo sobre espacio ----------------------------------------
# Azul de iceberg -claro arriba, profundo abajo- sobre negro espacial con
# estrellas. Los tonos frios y oscuros son deliberados: se lee de noche y el
# texto tiene que ser lo unico que brille.

HIELO = gr.themes.Color(
    name="hielo",
    c50="#eef9fd", c100="#d3f0fa", c200="#a8e2f4", c300="#79d0ea",
    c400="#4bb8da", c500="#2e9cc4", c600="#237ea6", c700="#1d6285",
    c800="#1b4d68", c900="#173d53", c950="#0e2534",
)
NOCHE = gr.themes.Color(
    name="noche",
    c50="#eef1f7", c100="#d6dcea", c200="#aeb8d0", c300="#8090b3",
    c400="#5a6b92", c500="#3f4f72", c600="#2e3b58", c700="#222c44",
    c800="#171e30", c900="#0e1320", c950="#05070d",
)
TEMA = gr.themes.Base(primary_hue=HIELO, secondary_hue=HIELO, neutral_hue=NOCHE)


def _estrellas(n: int = 90) -> str:
    """Campo de estrellas en CSS puro, sin imagenes ni peticiones de red.

    Semilla fija: el cielo tiene que ser el mismo en cada arranque, si no
    parpadea de una recarga a otra y distrae.
    """
    import random
    r = random.Random(20260906)
    capas = []
    for _ in range(n):
        x, y = r.uniform(0, 100), r.uniform(0, 100)
        tam = r.choice([1, 1, 1, 1.4, 1.8])
        op = r.uniform(0.25, 0.95)
        capas.append(f"radial-gradient({tam}px {tam}px at {x:.1f}% {y:.1f}%,"
                     f"rgba(226,242,252,{op:.2f}) 50%,transparent 51%)")
    return ",".join(capas)


# Estructura, no color. Todos los colores salen de las variables que pone
# `paletas.py`, asi que una paleta nueva no puede romper la maquetacion.
#
# Y hay una correccion que NO es de gusto y va para todas las paletas: la
# primera lectora real de la app, de quince anos, dijo que la pagina se siente
# antigua, "todo muy recto, muy marcado". Tenia razon. Esquinas de 14 px,
# bordes finos y sombras suaves en vez de aristas y contraste duro.
_RADIO = "14px"

# Las estrellas se calculan una vez y se le pasan a la paleta que las quiera.
_ESTRELLAS_CSS = _estrellas()


def _css_paleta(clave: str) -> str:
    """El `<style>` de la paleta elegida. Nunca lanza: si la clave no existe
    -un valor viejo guardado en el navegador, por ejemplo- vuelve a la de
    siempre en vez de dejar la pagina sin colores."""
    try:
        return paletas_mod.css(str(clave), _ESTRELLAS_CSS)
    except Exception:
        return paletas_mod.css(paletas_mod.POR_DEFECTO, _ESTRELLAS_CSS)

_CSS_GLOBAL = f"""<style>
/* El bloque que transporta esta hoja de estilo no debe ocupar sitio; un
   <style> sigue aplicandose aunque su contenedor este oculto. */
#ll-css,#ll-paleta-css{{display:none}}
/* El indice de un libro puede tener 366 capitulos. Sin altura maxima empuja
   toda la pagina y hay que recorrerla entera para volver al texto. */
#ll-indice .wrap{{max-height:46vh;overflow-y:auto}}
h1{{
  background:linear-gradient(96deg,var(--ll-titulo-1) 0%,
    var(--ll-titulo-2) 40%,var(--ll-titulo-3) 100%);
  -webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;color:transparent;
  letter-spacing:-.015em;
  filter:drop-shadow(0 0 26px var(--ll-sombra-titulo))}}
/* Paneles translucidos, no cajas opacas. */
.block,.form,.panel,.gr-box{{
  background-color:var(--ll-panel) !important;
  border-color:var(--ll-borde) !important;
  border-radius:{_RADIO} !important;
  backdrop-filter:blur(7px)}}
/* Nada de aristas: botones, cajas de texto, desplegables y pestanas. */
button,.gr-button,input,textarea,select,
.wrap-inner,.secondary-wrap,.gr-input,.gr-text-input{{
  border-radius:{_RADIO} !important}}
button,.gr-button{{
  transition:transform .08s ease,box-shadow .18s ease,filter .18s ease}}
button:hover,.gr-button:hover{{filter:brightness(1.06)}}
button:active,.gr-button:active{{transform:translateY(1px)}}
button.primary,.primary button{{
  background:linear-gradient(180deg,var(--ll-boton-alto),
    var(--ll-acento-hondo)) !important;
  border-color:var(--ll-borde) !important;
  color:var(--ll-boton-texto) !important;
  box-shadow:0 2px 14px var(--ll-sombra-titulo)}}
.tab-nav button.selected{{
  color:var(--ll-acento) !important;
  border-bottom-color:var(--ll-acento) !important}}
/* Las opciones de una lista, como fichas que se pueden tocar. En un movil un
   circulito de radio es un blanco de 12 px; la ficha entera es de 44. */
label:has(input[type="radio"]),label:has(input[type="checkbox"]){{
  border-radius:{_RADIO} !important;padding:.55rem .7rem}}
#ll-lector{{
  background:var(--ll-lector-fondo);border-color:var(--ll-borde);
  border-radius:{_RADIO};color:var(--ll-lector-texto)}}
#ll-lector::selection,#ll-lector p::selection{{
  background:var(--ll-seleccion)}}
#ll-voz{{
  background:var(--ll-lector-fondo);border-color:var(--ll-borde);
  border-radius:{_RADIO}}}
footer{{opacity:.78}}
/* El reproductor trae un boton de descarga que aqui no pinta nada: el
   audio es para oirlo en el momento, no para llevarselo. */
#ll-audio-ref a[download],#ll-audio-palabra a[download],
#ll-audio-ref a[href^="blob:"],#ll-audio-palabra a[href^="blob:"]{{
  display:none !important}}
</style>"""


# --- Recursos pesados: uno por proceso, cargado al primer uso -------------

_puntuador = None
_catalogo = None
_consultor = None

# Sin candado, dos peticiones que llegan a la vez construyen DOS modelos y
# duplican la memoria: el Puntuador son 278 MB de RSS y el catalogo 285 MB.
# La comprobacion "if es None" no es atomica frente a la carga que viene
# detras, que dura segundos.
_CANDADO = threading.Lock()


def puntuador() -> scoring.Puntuador:
    global _puntuador
    if _puntuador is None:
        with _CANDADO:
            if _puntuador is None:      # otro hilo pudo cargarlo mientras se esperaba
                _puntuador = scoring.Puntuador(RUTA_MODELO)
    return _puntuador


def catalogo() -> Catalogo:
    global _catalogo
    if _catalogo is None:
        with _CANDADO:
            if _catalogo is None:
                _catalogo = Catalogo()
    return _catalogo


def consultor() -> ConsultorLexico:
    global _consultor
    if _consultor is None:
        with _CANDADO:
            if _consultor is None:
                _consultor = ConsultorLexico()
    return _consultor


def _aviso(e) -> str:
    """Un fallo contado en cristiano, nunca un traceback en la cara."""
    return f"[!] {e}"


# --- Punto 1: nivel del lector -------------------------------------------

def _describir(p) -> str:
    if p is None:
        return ("Todavía no has fijado tu nivel. Responde el cuestionario "
                "o pega un texto que leas cómodo.")
    return perfil_mod.describir(p)


def _claves_cuestionario() -> list[str]:
    """Las claves, en el mismo orden en que se pintan los controles.

    Primero las preguntas de opinion y despues los fragmentos de lectura.
    `perfil.desde_cuestionario` los distingue por la clave: promedia las
    opiniones y se queda con el techo mas dificil de los fragmentos.
    """
    return ([p[0] for p in perfil_mod.PREGUNTAS]
            + [f["clave"] for f in getattr(perfil_mod, "FRAGMENTOS", [])])


def _desde_cuestionario(p_actual, nombre, peticion: gr.Request, *valores):
    """Estima el nivel con las respuestas del cuestionario y lo guarda.

    OJO CON EL ORDEN DE LA FIRMA. `peticion` va ANTES de `*valores`, y no al
    final como en los demas manejadores. Gradio solo inyecta el `Request` en
    parametros posicionales: su `special_args` recorre la firma y **corta en el
    primer parametro que no lo sea** (`gradio/helpers.py`). Con `*valores`
    delante, `peticion` era keyword-only, no se inspeccionaba nunca y llegaba
    `None` siempre.

    Y `None` aqui no era inofensivo: desplegada, `_archivo_lector(..., None)`
    resuelve a `lectores/anonimo/`, UNA carpeta para todos los visitantes. Cada
    "Estimar mi nivel" pisaba el perfil del anterior -con su nombre dentro-, y
    al recargar la pagina `_perfil_inicial`, que si recibe el Request, buscaba
    en la carpeta de la sesion y no encontraba nada: el lector volvia a
    "Todavia no has fijado tu nivel" despues de leer "Guardado". En local no se
    nota, y por eso nadie lo habia visto.

    Poner `peticion` en la tercera posicion SI funciona, aunque parezca que
    desplazaria las respuestas: `special_args` inserta el Request en el indice
    de su parametro, asi que las entradas quedan alineadas. Comprobado
    ejecutando `special_args` con las dos firmas.
    """
    claves = _claves_cuestionario()
    respuestas = {k: v for k, v in zip(claves, valores) if v is not None}
    try:
        p = perfil_mod.desde_cuestionario(respuestas, nombre=nombre or "")
        p.guardar(_archivo_lector("perfil.json", peticion))
    except (ValueError, OSError) as e:
        # Se conserva el perfil anterior: un fallo al estimar no debe borrarlo.
        return p_actual, _aviso(e), _aviso(e)
    return p, _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas.", _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas."


def _muestra_de_libro(libro, palabras: int = 2400) -> str:
    """Un extracto representativo del libro, para medir su dificultad.

    No vale con coger el principio: los primeros capitulos suelen ser
    portadilla, prologo o dedicatoria, y ademas muchos libros empiezan facil.
    Se toman trozos repartidos por toda la obra, saltandose el paratexto, para
    que la medida se parezca a lo que el lector va a encontrarse de verdad.
    """
    cuerpo = [c for c in libro.capitulos
              if c.palabras >= 300 and not _RELLENO_RE.search(c.titulo)]
    if not cuerpo:
        cuerpo = [c for c in libro.capitulos if c.palabras >= 100] or libro.capitulos
    cuantos = min(8, len(cuerpo))
    if cuantos == 0:
        return ""
    # Repartidos por el libro, no los ocho primeros.
    paso = max(1, len(cuerpo) // cuantos)
    elegidos = cuerpo[::paso][:cuantos]
    por_capitulo = max(260, palabras // cuantos)
    trozos = []
    for c in elegidos:
        ws = c.texto.split()
        # Desde un poco despues del principio: los titulillos viven ahi.
        inicio = min(40, max(0, len(ws) - por_capitulo))
        trozos.append(" ".join(ws[inicio:inicio + por_capitulo]))
    return "\n\n".join(trozos)


def _nivel_desde_libro(p_actual, nombre, archivo, peticion: gr.Request = None):
    """Situa al lector midiendo un libro entero que dice leer comodo.

    Pedirle que copie y pegue doscientas palabras es trabajo suyo que puede
    hacer la maquina: si ya tiene el libro, que lo suba.
    """
    if not archivo:
        pide = "Sube un `.epub`, `.pdf` o `.txt` que ya hayas leído."
        return p_actual, pide, pide
    try:
        libro = reader.cargar(archivo)
    except Exception as e:
        roto = _aviso(f"No pude abrir el archivo ({type(e).__name__}): {e}")
        return p_actual, roto, roto
    muestra = _muestra_de_libro(libro)
    if len(muestra.split()) < 150:
        corto = _aviso("Ese archivo tiene muy poco texto corrido para medirlo. "
                       "Prueba con un libro completo, o pega un fragmento a mano.")
        return p_actual, corto, corto
    try:
        p = perfil_mod.desde_muestra(muestra, puntuador(), nombre=nombre or "")
        p.guardar(_archivo_lector("perfil.json", peticion))
    except (ValueError, FileNotFoundError, OSError) as e:
        return p_actual, _aviso(e), _aviso(e)
    texto = (f"Medido con **{libro.titulo}**"
             + (f" — {libro.autor}" if libro.autor else "")
             + f", tomando muestras de {min(8, len(libro.capitulos))} partes "
               f"del libro.\n\n" + _describir(p)
             + "\n\nGuardado. Ya puedo recomendarte lecturas.")
    return p, texto, texto


def _desde_muestra(p_actual, nombre, texto, peticion: gr.Request = None):
    if not (texto or "").strip():
        pide = "Pega un fragmento que leas sin dificultad."
        return p_actual, pide, pide
    try:
        p = perfil_mod.desde_muestra(texto, puntuador(), nombre=nombre or "")
        p.guardar(_archivo_lector("perfil.json", peticion))
    except (ValueError, FileNotFoundError, OSError) as e:
        return p_actual, _aviso(e), _aviso(e)
    return p, _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas.", _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas."


# --- Punto 2: buscador del catalogo --------------------------------------

def _tabla_libros(libros, aviso: str = "") -> str:
    if not libros:
        return _aviso(aviso or "Sin resultados.")
    # Tres columnas, no cinco: a 390 px una tabla de cinco se aplasta hasta
    # dejar una palabra por linea. El autor y el nivel caben debajo del titulo.
    abribles = sum(str(b.id).upper().startswith("PG") for b in libros)
    cabecera = []
    if abribles:
        cabecera.append(f"**▸ {abribles} de {len(libros)}** se abren aquí "
                        f"mismo, con el botón de debajo de la tabla. Los "
                        f"demás son de StoryWeaver y no hay de dónde "
                        f"descargarlos.")
    else:
        cabecera.append("Ninguno de estos se puede abrir aquí: son de "
                        "StoryWeaver. Prueba a describirlo de otra manera "
                        "para que salgan clásicos de Project Gutenberg.")
    # La leyenda va ARRIBA: si va debajo, en un movil el simbolo ▸ queda a una
    # pantalla de distancia de lo que lo explica.
    filas = cabecera + ["", "| | Libro | De qué va |", "|---|---|---|"]
    for b in libros:
        aqui = str(b.id).upper().startswith("PG")
        # Sin enlace: tocar el titulo en un movil sacaba de la app a
        # gutenberg.org, cuando lo que se quiere es abrirlo AQUI.
        enlace = b.titulo
        gancho = (b.gancho or "").replace("\n", " ").replace("|", "/")
        if len(gancho) > 70:
            gancho = gancho[:67] + "..."
        ficha = f"**{enlace}**<br><small>{b.autor} · {b.nivel}</small>"
        filas.append(f"| {'▸' if aqui else ''} | {ficha} | {gancho} |")
    if aviso:
        filas += ["", f"_{aviso}_"]
    return "\n".join(filas)


def _opciones_libros(libros):
    """Los resultados, listos para abrirse en el lector con un clic.

    Los de StoryWeaver se listan igual pero marcados: no estan en Gutenberg y
    no hay de donde bajarlos. Mas vale decirlo en la etiqueta que dejar que el
    usuario lo descubra al pulsar.
    """
    # **Solo los que se pueden abrir.** Antes se listaban todos, marcando los
    # de StoryWeaver como "no descargable", y como son 1.049 de los 1.197 del
    # catalogo, el desplegable se llenaba de opciones inservibles: habia que
    # rebuscar entre ellas el unico libro que si se abria. Un desplegable
    # donde casi nada funciona es peor que uno corto donde todo funciona.
    opciones = [(f"{b.titulo} — {b.autor} ({b.nivel})", b.id)
                for b in libros if str(b.id).upper().startswith("PG")]
    return gr.update(choices=opciones,
                     value=opciones[0][1] if opciones else None)


def _buscar(p, consulta, ajustar, n):
    try:
        cat = catalogo()
    except (FileNotFoundError, OSError) as e:
        return _aviso(e), gr.update(choices=[], value=None)
    nivel = p.nivel if (ajustar and p is not None) else None
    # Vaciar la casilla "¿Cuántos te propongo?" hace que `gr.Number` mande
    # None, y el `int(None)` de dentro del try le ensenaba al lector un
    # "int() argument must be a string... not 'NoneType'". No es un aviso: es
    # un error de Python en la cara de quien solo borro un numero.
    n = int(n or 10)
    try:
        libros, aviso = cat.buscar(consulta, nivel_lector=nivel, n=n)
    except Exception as e:                      # red o modelo de embeddings
        return _aviso(e), gr.update(choices=[], value=None)
    cabecera = ""
    if ajustar and p is None:
        cabecera = "_Sin perfil todavía: busco solo por parecido._\n\n"
    return cabecera + _tabla_libros(libros, aviso), _opciones_libros(libros)


RUTA_LIBROS = Path(os.path.expanduser("~")) / ".literalevel" / "libros"


def _descargar_gutenberg(id_libro: str) -> str:
    """Baja un libro de Project Gutenberg y devuelve la ruta local.

    Se cachea en disco: el mismo libro no se vuelve a bajar nunca. Existe
    porque sin esto el bucle de la app estaba roto -el buscador encontraba el
    libro y despedia al lector a gutenberg.org a descargarlo y volver a
    subirlo, justo en el momento de mas ganas de leer.
    """
    import urllib.request

    texto_id = str(id_libro).strip()
    num = "".join(c for c in texto_id if c.isdigit())
    if not texto_id.upper().startswith("PG") or not num:
        raise ValueError(
            "Este libro no viene de Project Gutenberg (es de StoryWeaver / "
            "Global Digital Library), así que no puedo descargarlo. Consíguelo "
            "y súbelo con el selector de archivo.")

    RUTA_LIBROS.mkdir(parents=True, exist_ok=True)
    destino = RUTA_LIBROS / f"pg{num}.epub"
    if destino.exists() and destino.stat().st_size > 2000:
        return str(destino)

    fuentes = [
        (f"https://www.gutenberg.org/ebooks/{num}.epub.noimages", ".epub"),
        (f"https://www.gutenberg.org/cache/epub/{num}/pg{num}.txt", ".txt"),
        (f"https://www.gutenberg.org/ebooks/{num}.txt.utf-8", ".txt"),
    ]
    ultimo = None
    for url, ext in fuentes:
        try:
            pedido = urllib.request.Request(
                url, headers={"User-Agent": "LiteraLevel/1.0 (proyecto educativo)"})
            with urllib.request.urlopen(pedido, timeout=45) as r:
                datos = r.read()
            if len(datos) < 2000:
                raise ValueError("el archivo llegó vacío")
            final = destino.with_suffix(ext)
            final.write_bytes(datos)
            return str(final)
        except Exception as e:
            ultimo = e
    raise ConnectionError(f"No pude descargarlo de Gutenberg: {ultimo}")


def _abrir_del_catalogo(id_libro, peticion: gr.Request = None):
    """Abre en el lector un libro elegido en el buscador, sin salir de la app.

    Es generadora y su primer valor va a un aviso de la pestana del BUSCADOR,
    no de la de lectura. Descargar de Gutenberg puede tardar, y antes el
    usuario pulsaba el boton y no veia nada: ni espera, ni error, porque todas
    las salidas estaban en una pestana a la que no se saltaba si algo fallaba.
    """
    vacio = gr.update(choices=[], value=None)
    quieto = (None, vacio, _html_lectura(""), gr.update(), gr.Tabs())
    if not id_libro:
        yield quieto[:3] + ("Elige un libro de la lista.", gr.Tabs(),
                            "Elige un libro de la lista.")
        return
    yield quieto[:3] + (gr.update(), gr.Tabs(),
                        "Descargando de Project Gutenberg… la primera vez "
                        "puede tardar; después queda guardado.")
    try:
        ruta = _descargar_gutenberg(id_libro)
    # OSError incluido: `RUTA_LIBROS.mkdir(...)` de la cache queda fuera del
    # `try` interno, asi que un problema de disco -carpeta ocupada por un
    # archivo, permisos, disco lleno- salia hacia Gradio. Era el unico error de
    # disco que un manejador dejaba escapar.
    except (ValueError, ConnectionError, OSError) as e:
        yield quieto[:3] + (gr.update(), gr.Tabs(), _aviso(e))
        return
    libro, upd, html, resumen = _abrir(ruta, peticion)
    if libro is None:
        yield None, vacio, _html_lectura(""), resumen, gr.Tabs(), _aviso(resumen)
        return
    yield libro, upd, html, resumen, gr.Tabs(selected="leer"), ""


# La holgura con la que "Sorprendeme" busca por nivel. Esta aqui y se pasa
# EXPLICITA para que el rotulo y el filtro no puedan volver a separarse: el
# rotulo anunciaba `rango_recomendado` -nivel-0,10 a nivel+0,15- mientras
# `por_nivel` filtraba con una holgura simetrica de 0,25. Con un lector en 1,00
# la app decia "Lo mas leido entre 0.90 y 1.15" y listaba B1 (0,80) y B2
# (1,20): ni uno de los dos dentro del rango que acababa de anunciar.
HOLGURA_POR_NIVEL = 0.25


def _recomendar(p, n):
    vacio = gr.update(choices=[], value=None)
    if p is None:
        return "Primero fija tu nivel en la pestaña **Mi nivel**.", vacio
    # `gr.Number` vacio llega como None, y el `int(None)` de dentro del try
    # devolvia al lector un "int() argument must be... not 'NoneType'".
    n = int(n or 10)
    try:
        libros = catalogo().por_nivel(p.nivel, holgura=HOLGURA_POR_NIVEL,
                                      n=n)
    except Exception as e:
        return _aviso(e), vacio

    # NUNCA dejar al principiante en un callejon. Del catalogo heredado solo
    # 148 de 1.197 libros se pueden abrir aqui -los de Project Gutenberg-, y
    # estan repartidos asi:
    #
    #     A1  0 de 723      B1  10 de 69      C1  25 de 53
    #     A2  2 de 185      B2  12 de 52      C2  99 de 115
    #
    # O sea que un lector A1 recibia diez titulos y un desplegable VACIO: los
    # 723 libros de su nivel son de StoryWeaver y no hay de donde bajarlos. El
    # camino de quien mas ayuda necesita terminaba en nada. La causa no es un
    # error de programacion, es que Project Gutenberg apenas tiene material
    # elemental, y el catalogo lo rellenaba con libros que no puede servir.
    #
    # Mientras la remedicion del catalogo no termine, esto al menos ofrece lo
    # mas facil que SI se puede abrir, y lo dice en vez de disimularlo.
    rescate = ""
    if libros and not any(str(b.id).upper().startswith("PG") for b in libros):
        try:
            faciles = [b for b in catalogo().por_nivel(p.nivel, holgura=3.0, n=200)
                       if str(b.id).upper().startswith("PG")]
        except Exception:
            faciles = []
        if faciles:
            faciles.sort(key=lambda b: scoring.ANCHORS.index(b.nivel)
                         if b.nivel in scoring.ANCHORS else 9)
            libros = faciles[:int(n)]
            rescate = ("Ninguno de los libros de tu nivel se puede abrir aquí: "
                       "son de StoryWeaver y no hay de dónde descargarlos. "
                       "**Estos son los más fáciles que sí puedes leer ahora "
                       "mismo**, aunque queden por encima de tu nivel. Ve "
                       "despacio y usa el doble clic sobre las palabras.\n\n")

    # El rango que se ANUNCIA tiene que ser el que se uso para filtrar. Antes
    # aqui se leia `p.rango_recomendado`, que es otra cosa -el rango de reto
    # del lector- y no lo que `por_nivel` acababa de aplicar.
    lo = max(0.0, p.nivel - HOLGURA_POR_NIVEL)
    hi = min(2.0, p.nivel + HOLGURA_POR_NIVEL)
    # Los niveles del catalogo son seis valores discretos, asi que un lector
    # que salga del cuestionario en 0.62 puede no tener NINGUN libro dentro de
    # la holgura. Decirlo y decir que hacer, en vez del generico "Sin
    # resultados" que dejaba en un callejon.
    si_no_hay = (f"No hay libros etiquetados entre {lo:.2f} y {hi:.2f}. Prueba "
                 f"a describir lo que te apetece leer en el buscador de "
                 f"arriba: ahí sí se ajusta a tu nivel sin exigir una "
                 f"coincidencia exacta.")
    if rescate:
        return rescate + _tabla_libros(libros, si_no_hay), _opciones_libros(libros)
    return (f"Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:\n\n"
            + _tabla_libros(libros, si_no_hay), _opciones_libros(libros))


# --- Punto 3: lector, y punto 4 dentro de el ------------------------------

# Tres decisiones de este bloque no son de gusto, y conviene dejarlas dichas
# porque las tres estaban al reves y las tres las sufrio una lectora real.
#
# 1. SIN `max-height` ni `overflow-y`. Antes el lector era una caja con su
#    propio desplazamiento dentro de una pagina que tambien se desplaza. En el
#    movil eso es una loteria: el dedo unas veces mueve el texto y otras la
#    pagina, segun donde caiga, y no hay forma de saberlo de antemano. Es el
#    candidato numero uno a lo que Esmeralda, 15 anos, describio como "esta
#    bien dificil de usar en celular". El texto ahora fluye con la pagina.
#
# 2. `max-width: 66ch` en los parrafos. Sin tope, el lector ocupaba el ancho
#    entero del bloque: en un portatil de 1440 px con Georgia a 19 px son del
#    orden de 130 caracteres por linea. Al ojo le cuesta encontrar el principio
#    del renglon siguiente cuando el salto es tan largo.
#
# 3. SIN `text-align: justify`. El criterio 1.4.8 de las WCAG lo desaconseja
#    explicitamente -"Text is not justified"- porque los rios de espacio en
#    blanco despistan la vista. En una columna estrecha de movil el problema
#    empeora, no mejora. Quitado el justificado, `hyphens` deja de hacer falta;
#    y ademas Gradio sirve la pagina con lang="en", asi que partia las palabras
#    con reglas inglesas.
_CSS_LECTOR = """<style>
#ll-lector{padding:1.4rem 1.8rem;
  /* El gris clavado de antes -rgba(128,128,128,.28)- le ganaba al
     `border-color:var(--ll-borde)` que pone el bloque de la paleta, porque
     este `border` abreviado va despues y lo reescribe entero. */
  border:1px solid var(--ll-borde);border-radius:10px;
  font-family:Georgia,"Iowan Old Style","Times New Roman",serif;
  font-size:var(--ll-lectura, 19px);line-height:1.75;
  /* Era `color:inherit`, que gana al `--ll-lector-texto` de mas arriba y
     dejaba esa variable muerta en las cinco paletas. Heredaba `--ll-texto`,
     asi que se leia; pero la paleta declara un color propio para el cuerpo
     del libro y era el que no se usaba nunca. */
  color:var(--ll-lector-texto);
  text-align:left}
#ll-lector p{margin:0 0 1.05em;max-width:66ch}
#ll-lector p:first-child{margin-top:0}
/* El amarillo estaba CLAVADO aqui, y este bloque va despues del de arriba
   con la misma especificidad, asi que ganaba el amarillo y `--ll-seleccion`
   era codigo muerto en las cinco paletas. Sobre las tres claras el resaltado
   quedaba en 1,20-1,22:1, o sea invisible: y seleccionar una palabra es COMO
   SE CONSULTA EL DICCIONARIO, el gesto central de la aplicacion. */
#ll-lector::selection,#ll-lector p::selection{
  background:var(--ll-seleccion);color:var(--ll-lector-texto)}
#ll-lector .ll-vacio{font-style:italic;opacity:.78;text-align:left}
@media (max-width:640px){
  #ll-lector{padding:1.1rem 1.15rem;font-size:var(--ll-lectura, 18px)}
  #ll-lector p{max-width:none}
}
</style>"""


def _html_lectura(texto: str) -> str:
    """El capitulo como prosa legible, no como volcado en un textarea."""
    if not texto:
        return _CSS_LECTOR + ('<div id="ll-lector"><span class="ll-vacio">'
                              'Abre un libro y elige un capitulo.</span></div>')
    parrafos = [" ".join(t.split()) for t in re.split(r"\n\s*\n", texto)]
    cuerpo = "".join(f"<p>{_html.escape(t)}</p>" for t in parrafos if t)
    return _CSS_LECTOR + f'<div id="ll-lector">{cuerpo}</div>'


# Doble clic (o arrastrar) sobre una palabra del lector la copia a la caja de
# consulta. Se engancha a document una sola vez y sobrevive a que Gradio
# vuelva a dibujar el capitulo.
JS_SELECCION = r"""
() => {
  if (window.__llSel) return;
  window.__llSel = true;

  // Antes esto solo escuchaba 'mouseup', y por eso en el movil no pasaba
  // nada: al seleccionar una palabra con el dedo, iOS **no** emite mouseup.
  // Lo unico que llega de forma fiable en tactil es 'selectionchange', que
  // ademas se dispara muchas veces mientras se arrastra, asi que hay que
  // esperar a que la seleccion se estabilice.
  var espera = null;

  function enElLector(nodo) {
    if (!nodo) return false;
    var el = nodo.nodeType === 1 ? nodo : nodo.parentElement;
    return !!(el && el.closest && el.closest('#ll-lector'));
  }

  function capturar() {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    var txt = (sel.toString() || '').trim();
    // Una palabra o un phrasal verb corto. Si es mas, se esta subrayando
    // para leer, no para consultar.
    if (!txt || txt.split(/\s+/).length > 4 || txt.length > 40) return;
    if (!enElLector(sel.anchorNode)) return;
    var caja = document.querySelector('#ll-palabra textarea, #ll-palabra input');
    if (!caja || caja.value === txt) return;
    // Svelte no se entera si se asigna .value a secas: hay que usar el setter
    // nativo del prototipo y despues emitir 'input'.
    var proto = caja.tagName === 'TEXTAREA' ? HTMLTextAreaElement : HTMLInputElement;
    var setter = Object.getOwnPropertyDescriptor(proto.prototype, 'value').set;
    setter.call(caja, txt);
    caja.dispatchEvent(new Event('input', { bubbles: true }));
    // En un movil la caja queda fuera de pantalla, encima del lector: sin
    // esto el usuario selecciona una palabra y no ve que haya pasado nada.
    try { caja.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
    catch (e) { caja.scrollIntoView(); }
  }

  function programar(ms) {
    clearTimeout(espera);
    espera = setTimeout(capturar, ms);
  }

  // Tactil: la seleccion tarda en asentarse y las manijas de iOS siguen
  // moviendola un rato.
  document.addEventListener('selectionchange', function () { programar(400); });
  document.addEventListener('touchend', function () { programar(400); });
  // Raton: llega enseguida y no hace falta esperar.
  document.addEventListener('mouseup', function () { programar(10); });
}
"""


def _mover(libro, idx, paso):
    """Capitulo anterior / siguiente, sin salirse del libro."""
    if libro is None or idx is None:
        return gr.update()
    # `int(idx)` pelado lanzaba ValueError con cualquier indice que no fuera un
    # numero. `_capitulo` y `_medir` ya pasaban por `_cap`, que lo valida; este
    # se habia quedado fuera.
    try:
        actual = int(idx)
    except (TypeError, ValueError):
        return gr.update()
    return gr.update(value=max(0, min(len(libro.capitulos) - 1, actual + paso)))


# Titulos que en un epub casi siempre son paratexto y no la obra en si.
# `RELLENO_RE` y el filtro de capitulos viven en `ficha.py`: el precalculo
# masivo en Colab necesita el MISMO filtro que la app.
_RELLENO_RE = ficha.RELLENO_RE


# Se conserva por compatibilidad con lo ya guardado en local y con las
# pruebas; el marcapaginas real se resuelve por lector con `_ruta_sesion`.
RUTA_SESION = BASE_DATOS_LECTOR / "sesion.json"


def _ruta_sesion(peticion=None) -> Path:
    if not EN_LA_NUBE:
        return RUTA_SESION
    return Path(_archivo_lector("sesion.json", peticion))


def _guardar_sesion(ruta_libro: str, titulo: str, capitulo: int,
                    peticion=None) -> None:
    """Deja constancia de por donde ibas. Nunca estorba si falla."""
    destino = _ruta_sesion(peticion)
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(
            {"ruta": str(ruta_libro), "titulo": titulo, "capitulo": int(capitulo)},
            ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass          # no poder guardar el marcapaginas no puede romper la lectura


def _leer_sesion(peticion=None) -> dict | None:
    try:
        d = json.loads(_ruta_sesion(peticion).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # `isinstance` y no solo `d.get`: un `sesion.json` que sea JSON VALIDO pero
    # no un objeto -`[]`, `"hola"`, `3`- pasaba el `except` y reventaba en el
    # `.get` con un AttributeError. Y esto lo llama `_reanudar`, que corre en
    # `demo.load`, o sea que la pagina entera arrancaba con error para ese
    # lector hasta que alguien borrara el archivo a mano.
    if not isinstance(d, dict):
        return None
    return d if d.get("ruta") and os.path.exists(d["ruta"]) else None


def _perfil_inicial(peticion: gr.Request = None):
    """El perfil de ESTE lector, al abrir la app.

    No puede resolverse al construir la interfaz: eso ocurre una vez por
    proceso, y desplegada la app hay un proceso para todos los visitantes.
    Quien entrara segundo se encontraria con el nombre y el nivel del primero.
    """
    p = perfil_mod.cargar(_archivo_lector("perfil.json", peticion))
    return p, _describir(p)


def _reanudar(peticion: gr.Request = None):
    """Al abrir la app, vuelve al libro y al capitulo donde lo dejaste.

    Es la mecanica de retencion mas barata que hay: no premia ni castiga, solo
    evita que quien vuelve tenga que reconstruir donde estaba. Si el archivo
    ya no existe, no se dice nada y se empieza limpio.

    Desplegada, el marcapaginas es el de ESTA sesion de navegador. Si no lo
    fuera, cada visitante abriria la app en el libro del anterior.
    """
    vacio = (None, gr.update(choices=[], value=None), _html_lectura(""), "",
             gr.Tabs())
    s = _leer_sesion(peticion)
    if not s:
        return vacio
    libro, upd, html, resumen = _abrir(s["ruta"], peticion)
    if libro is None:
        return vacio
    idx = s.get("capitulo", 0)
    if not (isinstance(idx, int) and 0 <= idx < len(libro.capitulos)):
        idx = upd["value"]
    c = libro.capitulos[idx]
    aviso = (f"**{libro.titulo}** — seguías en el capítulo {idx + 1} de "
             f"{len(libro.capitulos)}: _{c.titulo}_.")
    return (libro, gr.update(choices=upd["choices"], value=idx),
            _html_lectura(c.texto), aviso, gr.Tabs(selected="leer"))


def _limpiar_consulta():
    """Lo que hay que borrar al abrir un libro nuevo.

    Miguel abrio The Brothers Karamazov y se encontro abajo la ficha de
    "strip", una palabra que habia consultado en el libro ANTERIOR. Parecia
    que la app le habia devuelto al vocabulario. Un libro nuevo empieza sin
    restos del anterior.
    """
    return ("", gr.update(value=""), gr.update(value=""), "",
            gr.update(value=None, visible=False))


def _abrir(archivo, peticion: gr.Request = None):
    vacio = gr.update(choices=[], value=None)
    if not archivo:
        return None, vacio, _html_lectura(""), "Sube un `.epub`, `.pdf` o `.txt`."
    try:
        libro = reader.cargar(archivo)
    except Exception as e:
        # A proposito se atrapa todo: pypdf lanza PdfStreamError y zipfile
        # BadZipFile, que no descienden de OSError. Un archivo corrupto no
        # puede tumbar la interfaz, y el nombre de la excepcion ya orienta.
        return None, vacio, _html_lectura(""), _aviso(
            f"No pude abrir el archivo ({type(e).__name__}): {e}")
    if not libro.capitulos:
        return None, vacio, _html_lectura(""), _aviso(
            "El archivo no tiene texto legible.")
    # El recuento va en la etiqueta porque muchos epub traen los titulos
    # repetidos ("I", "II"...) en dos partes y ademas portadillas sueltas:
    # sin las palabras no hay forma de distinguir el capitulo del relleno.
    opciones = []
    for i, c in enumerate(libro.capitulos):
        t = c.titulo if len(c.titulo) <= 46 else c.titulo[:43] + "..."
        opciones.append((f"{i + 1}. {t} · {c.palabras:,} pal.", i))

    # No abrir en la portadilla. Solo el recuento de palabras no basta: el
    # apendice de "Notes from a Dead House" trae 2,143 y aparece el segundo,
    # por delante del capitulo I. Asi que ademas se descarta por titulo.
    def _cuerpo(c):
        return c.palabras >= 500 and not _RELLENO_RE.search(c.titulo)

    inicial = next((i for i, c in enumerate(libro.capitulos) if _cuerpo(c)),
                   next((i for i, c in enumerate(libro.capitulos)
                         if c.palabras >= 500), 0))

    resumen = (f"**{libro.titulo}** — {libro.autor or 'autor desconocido'} · "
               f"{len(libro.capitulos)} capítulos · {libro.palabras:,} palabras")
    if inicial:
        resumen += (f"\n\n_Empiezo en el capítulo {inicial + 1}: "
                    f"los anteriores son portadilla._")
    _guardar_sesion(archivo, libro.titulo, inicial, peticion)
    biblioteca.anotar(ruta_libro=archivo, titulo=libro.titulo,
                      autor=libro.autor, capitulos=len(libro.capitulos),
                      capitulo=inicial, palabras=libro.palabras,
                      ruta=_archivo_lector("biblioteca.json", peticion))
    return (libro, gr.update(choices=opciones, value=inicial),
            _html_lectura(libro.capitulos[inicial].texto), resumen)


def _indice_de(libro, actual=None):
    """Las opciones del indice. Mismas etiquetas que el desplegable de arriba.

    El recuento de palabras va en la etiqueta por la misma razon que alli: hay
    epub que repiten los titulos ("I", "II") y traen portadillas sueltas, y sin
    las palabras no hay forma de saber cual es el capitulo de verdad.
    """
    if libro is None or not libro.capitulos:
        return gr.update(choices=[], value=None)
    opciones = []
    for i, c in enumerate(libro.capitulos):
        t = c.titulo if len(c.titulo) <= 46 else c.titulo[:43] + "..."
        opciones.append((f"{i + 1}. {t} · {c.palabras:,} pal.", i))
    return gr.update(choices=opciones, value=actual)


def _cap(libro, idx):
    """El capitulo `idx`, o None si el indice no sirve.

    El desplegable de Gradio puede devolver un indice viejo justo despues de
    cambiar de libro, o `None`, o incluso una cadena. Antes eso reventaba con
    IndexError contra la interfaz.
    """
    if libro is None or idx is None or not libro.capitulos:
        return None
    try:
        i = int(idx)
    except (TypeError, ValueError):
        return None
    return libro.capitulos[i] if 0 <= i < len(libro.capitulos) else None


def _capitulo(libro, idx, peticion: gr.Request = None):
    c = _cap(libro, idx)
    if c is None:
        return _html_lectura(""), ""
    # Mueve el marcapaginas. Se conserva la ruta ya guardada y solo se cambia
    # el capitulo, y solo si el marcador es de este mismo libro.
    s = _leer_sesion(peticion)
    if s and s.get("titulo") == libro.titulo:
        _guardar_sesion(s["ruta"], libro.titulo, int(idx), peticion)
        biblioteca.anotar(ruta_libro=s["ruta"], titulo=libro.titulo,
                          autor=libro.autor, capitulos=len(libro.capitulos),
                          capitulo=int(idx), palabras=libro.palabras,
                          ruta=_archivo_lector("biblioteca.json", peticion))
    return (_html_lectura(c.texto),
            f"**{c.titulo}** · {c.palabras:,} palabras · "
            f"capítulo {int(idx) + 1} de {len(libro.capitulos)}")


def _medir(libro, idx, como="cifra"):
    """Mide el capitulo con el modelo v4, avisando de la espera.

    La primera vez construye el `Puntuador`, que son 328 MB. Sin este primer
    `yield` la pantalla se queda quieta cerca de un minuto y parece colgada.
    """
    c = _cap(libro, idx)
    if c is None:
        yield "Abre un libro y elige un capítulo."
        return
    if _puntuador is None:
        yield ("Midiendo… la primera vez carga el modelo v4 (328 MB) y puede "
               "tardar cerca de un minuto. Después es inmediato.")
    else:
        yield "Midiendo el capítulo…"
    try:
        r = puntuador().puntuar(ficha.sin_licencia(c.texto))
    # OSError y no solo FileNotFoundError. La segunda solo cubre la carpeta
    # local que no existe; desplegada, `LITERALEVEL_MODELO` es un repositorio
    # del Hub y `from_pretrained` lanza OSError si el Hub no responde, si el
    # repositorio se renombra o si la descarga se corta en el arranque en frio.
    # Los otros tres manejadores que cargan el modelo ya atrapaban OSError;
    # este -el boton "¿Como de dificil es este capitulo?"- se habia quedado
    # fuera. `FileNotFoundError` desciende de `OSError`, asi que el mensaje de
    # la carpeta ausente sigue saliendo igual.
    except (ValueError, OSError) as e:
        yield _aviso(e)
        return
    yield (_nivel_dicho(r.puntuacion, r.banda, como)
           + f" · {r.n_bloques} bloques · confianza {r.confianza}")


# --- Las dos formas de decir el mismo numero ------------------------------
# La escala de LiteraLevel es 0..2 y es la que el modelo produce. El MCER
# (A1..C2) es el ancla con la que se entreno, no un certificado: por eso va
# siempre acompanado de la cifra y del aviso, nunca solo.

def _cefr(publico: float) -> str:
    """Ancla MCER mas cercana a una puntuacion de la escala publica 0..2.

    Redondea los empates HACIA ARRIBA, y no con `round()`, que en Python
    redondea al par: `round(2.5)` da 2 y `round(4.5)` da 4. Con esa regla un
    1.00 clavado salia B1 y un 1.80 salia C1, justo los limites que aparecen
    escritos en la tabla de la interfaz. Un usuario que comparase su cifra con
    la tabla habria encontrado dos respuestas distintas para el mismo numero.

    `scoring.anchor_cefr` se queda como esta: es del modelo y no se toca. Aqui
    hay una sola regla para todo lo que ve el lector, y es esta.
    """
    try:
        interno = float(publico) * 2.5
    except (TypeError, ValueError):
        return scoring.ANCHORS[0]
    i = int(math.floor(min(5.0, max(0.0, interno)) + 0.5))
    return scoring.ANCHORS[min(i, len(scoring.ANCHORS) - 1)]


def _nivel_dicho(publico: float, banda: str = "", como: str = "cifra") -> str:
    """El nivel escrito como lo quiera leer el usuario, con lo otro al lado.

    Nunca se da una de las dos solo. Quien elige MCER sigue viendo la cifra
    -que es lo que mide el modelo- y quien elige la cifra sigue viendo el
    ancla, que es lo que le suena de su escuela de idiomas.
    """
    b = f" ({banda})" if banda else ""
    if como == "cefr":
        return f"**{_cefr(publico)}** · {publico:.2f} / 2.00{b}"
    return f"**{publico:.2f} / 2.00**{b} · orientativo **{_cefr(publico)}**"


_TABLA_CEFR = """#### De 0–2 a A1–C2

| LiteraLevel | MCER | Qué suele significar |
|---|---|---|
| 0.00 – 0.20 | **A1** | frases muy cortas, vocabulario de andar por casa |
| 0.20 – 0.60 | **A2** | narración sencilla, poca subordinación |
| 0.60 – 1.00 | **B1** | novela juvenil, prosa clara |
| 1.00 – 1.40 | **B2** | novela adulta corriente |
| 1.40 – 1.80 | **C1** | prosa literaria densa, vocabulario amplio |
| 1.80 – 2.00 | **C2** | clásicos exigentes, sintaxis larga |

**LiteraLevel no certifica ningún nivel del MCER**, y esta columna no equivale
a un examen. El modelo se entrenó con textos anclados a esas etiquetas y
aprendió a colocar un texto nuevo en esa recta: lo que devuelve es una
posición en una escala continua, y la letra es la etiqueta más cercana. Sirve
para elegir qué leer, no para acreditar nada ante nadie."""


RUTA_ANALISIS = BASE_DATOS_LECTOR / "analisis"


def _clave_libro(libro) -> str:
    """Identifica un libro por su contenido, no por el nombre del archivo."""
    import hashlib
    # La version entra en la clave: al empezar a recortar la licencia de
    # Gutenberg antes de puntuar, los analisis ya guardados dejaron de ser
    # comparables con los nuevos. Sin esto seguirian sirviendose los viejos.
    h = hashlib.sha256(
        f"v3-sin-portadilla\x1f{libro.titulo}\x1f{libro.palabras}".encode("utf-8"))
    for c in libro.capitulos[:40]:
        h.update(f"{c.titulo}\x1f{c.palabras}".encode("utf-8"))
    return h.hexdigest()[:20]


def _ruta_analisis(libro, modo="completo"):
    """El completo se guarda sin sufijo: es el bueno y el que se busca primero."""
    sufijo = "" if modo == "completo" else f"-{modo}"
    return RUTA_ANALISIS / f"{_clave_libro(libro)}{sufijo}.json"


def _analisis_guardado(libro, modo="completo"):
    """El analisis guardado de este libro, o None si no vale.

    Se comprueba la FORMA, no solo que el JSON parsee. Es el mismo fallo que ya
    se corrigio en `sesion.json` y en `perfil.json`: un archivo valido pero con
    otra estructura -una lista, o filas sin la clave `dificultad`- pasaba el
    `except` y reventaba mas adelante con un KeyError hacia la interfaz. Los
    escribe la app, no un usuario, pero un archivo a medias de un reinicio en
    mitad de la escritura tiene exactamente esta pinta.
    """
    try:
        d = json.loads(_ruta_analisis(libro, modo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    filas = d.get("filas")
    if not isinstance(filas, list):
        return None
    for f in filas:
        if (not isinstance(f, dict) or "capitulo" not in f
                or "dificultad" not in f):
            return None
    return d


def _guardar_analisis(libro, datos, modo="completo") -> None:
    try:
        RUTA_ANALISIS.mkdir(parents=True, exist_ok=True)
        _ruta_analisis(libro, modo).write_text(
            json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass          # el analisis es util, no imprescindible


# Cuantos capitulos mira el vistazo rapido, y cuantas ventanas de cada uno.
#
# El numero no es redondo por gusto: en esta CPU el modelo hace 4,4 ventanas
# por segundo (medido, no estimado), asi que 30 x 2 = 60 ventanas son unos 14
# segundos. Con 40 capitulos se iba a 23 s, que ya no es un vistazo. Si algun
# dia el modelo corre en GPU, esto puede subir sin tocar nada mas.
RAPIDO_CAPITULOS = 30
RAPIDO_VENTANAS = 2


def _capitulos_de_cuerpo(libro):
    return ficha.capitulos_de_cuerpo(libro)


def _analizar_libro(libro, modo="completo", como="cifra", paleta=None,
                    peticion: gr.Request = None):
    """Perfil de dificultad del libro, capitulo a capitulo.

    Dos velocidades, porque son dos preguntas distintas:

    - **completo**: cada capitulo, ventana a ventana, sin muestrear. Es la
      respuesta a "¿de verdad lo lee todo?" y con un libro de 500.000 palabras
      son minutos. Se guarda en disco: se paga una vez por libro.
    - **rapido**: hasta `RAPIDO_CAPITULOS` capitulos repartidos por la obra y
      `RAPIDO_VENTANAS` de cada uno. Da la forma de la curva en segundos. Es
      un vistazo, y se dice que lo es. (Aqui decia "hasta 40 capitulos y 2
      ventanas", que era el valor de antes de bajarlo a 30: el comentario de
      las constantes explica por que se bajo y este docstring se quedo con la
      cifra vieja. Mejor no repetir el numero y nombrar la constante.)

    Va dibujando la grafica MIENTRAS mide, no al final. Es la diferencia entre
    esperar mirando una barra de progreso y ver aparecer la curva: el trabajo
    tarda lo mismo pero deja de parecer que la aplicacion se ha colgado.
    """
    if libro is None or not libro.capitulos:
        yield "Abre un libro primero, en esta misma pestaña.", None
        return

    rapido = (modo == "rapido")
    # El analisis completo vale tambien como rapido -es estrictamente mejor-,
    # asi que si ya esta hecho no se vuelve a medir peor a proposito.
    datos = _analisis_guardado(libro) or (_analisis_guardado(libro, "rapido")
                                          if rapido else None)
    if datos is None:
        cuerpo = _capitulos_de_cuerpo(libro)
        if not cuerpo:
            yield ("Este libro no tiene capítulos con prosa suficiente para "
                   "analizarlos."), None
            return
        if rapido and len(cuerpo) > RAPIDO_CAPITULOS:
            import numpy as np
            idx = np.linspace(0, len(cuerpo) - 1, RAPIDO_CAPITULOS)
            cuerpo = [cuerpo[i] for i in sorted(set(idx.round().astype(int).tolist()))]
        try:
            p = puntuador()
        except (FileNotFoundError, OSError) as e:
            yield _aviso(e), None
            return

        filas, ventanas = [], 0
        total = len(cuerpo)
        # Cada cuanto se repinta. Redibujar 366 veces cuesta mas que medir.
        cada = 1 if total <= 30 else max(2, total // 30)
        for n, (i, c) in enumerate(cuerpo, 1):
            vs = p.perfil_de_texto(ficha.sin_licencia(c.texto),
                                   tope=RAPIDO_VENTANAS if rapido else 0)
            if vs:
                ventanas += len(vs)
                filas.append({"capitulo": n, "titulo": c.titulo[:40],
                              "indice": i, "dificultad": round(sum(vs) / len(vs), 3),
                              "min": round(min(vs), 3), "max": round(max(vs), 3),
                              "ventanas": len(vs), "palabras": c.palabras})
            if filas and (n % cada == 0 or n == total):
                parcial = {"titulo": libro.titulo, "autor": libro.autor,
                           "palabras": libro.palabras, "ventanas": ventanas,
                           "filas": filas, "modo": modo}
                yield (f"Midiendo con el modelo v4: capítulo **{n} de {total}** · "
                       f"{ventanas:,} ventanas leídas."
                       + ("" if rapido else
                          "\n\nEsto se calcula una sola vez y queda guardado."),
                       _grafica_analisis(parcial, paleta))

        if not filas:
            yield "No pude medir ningún capítulo de este libro.", None
            return
        datos = {"titulo": libro.titulo, "autor": libro.autor,
                 "palabras": libro.palabras, "ventanas": ventanas,
                 "filas": filas, "modo": modo,
                 "capitulos_medidos": total,
                 "capitulos_totales": len(_capitulos_de_cuerpo(libro))}
        _guardar_analisis(libro, datos, modo)

    yield _resumen_analisis(datos, como), _grafica_analisis(datos, paleta)


def _ficha_libro(libro, p=None) -> str:
    """Como es de leer este libro. Se calcula contando, asi que es instantaneo.

    Sale solo al abrir el libro y no cuesta nada: no hay red, no hay modelo, no
    hay nada que pueda fallar salvo que el libro este vacio. Lo que si depende
    del lector es el tiempo estimado, porque leer por encima de tu nivel no es
    la misma velocidad que leer por debajo.
    """
    if libro is None or not libro.capitulos:
        return ""
    try:
        c = ficha.caracteristicas(libro)
    except Exception:
        return ""          # una ficha es un adorno; jamas puede tapar el libro
    if not c.palabras:
        return ""
    # Sin nivel del lector no se puede decir si el libro le queda cuesta
    # arriba, asi que se dan las dos velocidades en vez de elegir una al azar.
    if p is None:
        tiempo = (f"entre {ficha.reloj(c.minutos(False))} y "
                  f"{ficha.reloj(c.minutos(True))} de lectura")
    else:
        guardado = _analisis_guardado(libro)
        nivel_libro = (ficha.dificultad_global(guardado["filas"])
                       if guardado else None)
        exigente = nivel_libro is not None and nivel_libro > p.nivel + 0.15
        tiempo = ficha.reloj(c.minutos(exigente))
        tiempo += (" (va por encima de tu nivel)" if exigente
                   else " a tu ritmo de lectura")
    lineas = [
        "#### Cómo es de leer",
        f"- **{c.palabras:,} palabras** en {c.capitulos} "
        f"{'capítulo' if c.capitulos == 1 else 'capítulos'} · {tiempo}",
        f"- Frases de **{c.frase_media:.0f} palabras** de media",
        f"- Diálogo: **{c.dialogo * 100:.0f}%** de las frases llevan voz — "
        f"{c.forma_del_dialogo}",
        f"- Variedad de vocabulario: **{c.riqueza * 100:.1f}** palabras "
        f"distintas por cada 100",
    ]
    if c.distintivas:
        lineas.append("- Lo que más se repite: "
                      + ", ".join(f"`{w}`" for w in c.distintivas[:10]))
    lineas.append("\n_Todo esto está contado sobre el texto del archivo, "
                  "no lo dice ningún modelo._")
    return "\n".join(lineas)


def _sinopsis_guardada(libro):
    """La sinopsis guardada, o None si el archivo no tiene la forma esperada.

    Mismo caso que `_analisis_guardado`: un JSON valido que fuera una lista o
    una cadena pasaba el `except` y reventaba en el `.get`, y un campo numerico
    reventaba en el `.strip()`. Se normaliza a texto lo que se vaya a tratar
    como texto.
    """
    try:
        ruta = RUTA_ANALISIS / f"{_clave_libro(libro)}-sinopsis.json"
        d = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    return {k: (v if isinstance(v, list) else str(v))
            for k, v in d.items() if v is not None}


def _de_que_trata(libro, peticion: gr.Request = None):
    """Resumen en espanol de que va el libro. Es lo unico de la ficha que sale
    a la red, asi que va detras de un boton y se guarda: un libro se resume una
    vez y ya. Generadora, porque tarda unos segundos.

    **Esta es la TERCERA cosa que cuesta dinero**, y durante un tiempo fue la
    unica que estaba abierta. No recibia `gr.Request`, no pasaba por el codigo
    de acceso, no tenia tope por hora y no apuntaba el uso: en una direccion
    publica, cualquiera podia subir un .txt, pulsar el boton, cambiar una
    palabra del archivo -la cache va por titulo, palabras y titulos de
    capitulo- y repetir. Cada pulsacion son cuatro pasajes de 900 palabras a la
    API. Lo encontro una auditoria del codigo, no del documento.
    """
    if libro is None or not libro.capitulos:
        yield "Abre un libro primero."
        return
    datos = _sinopsis_guardada(libro)
    if datos is None:
        if not _dentro_del_limite(peticion, "sinopsis", LIMITE_SINOPSIS_HORA):
            yield _aviso(_mensaje_limite(
                "es", _minutos_para_la_siguiente("sinopsis", peticion)))
            return
        puede, motivo_pago = _puede_pagar(peticion)
        if not puede:
            yield motivo_pago
            return
        # `consultor()` construye el ConsultorLexico ENTERO, que abre el
        # diccionario Kaikki y lanza `FileNotFoundError` si el `.db` no esta.
        # El resumen no necesita el diccionario -ni spaCy, ni MiniLM-: solo
        # quiere un cliente de OpenAI. Sin este `try`, en el Space con el
        # dataset mal montado la pestana Leer funcionaba, la ficha contada
        # funcionaba, y este boton devolvia un "Error" pelado. En `_consultar`
        # la misma construccion si estaba protegida.
        try:
            cliente = consultor()._cliente()
        except Exception as e:
            yield _aviso(f"No pude preparar el resumen ({type(e).__name__}). "
                         "El resto de la ficha no lo necesita y sigue arriba.")
            return
        if cliente is None:
            yield ("Para el resumen hace falta la clave de OpenAI. Todo lo "
                   "demás de la ficha —lo que está contado sobre el texto— "
                   "ya lo tienes arriba y no necesita clave.")
            return
        yield "Leyendo pasajes del principio, del medio y del final…"
        datos = ficha.sinopsis(libro, cliente)
        if datos is None:
            yield ("No pude preparar el resumen ahora mismo. Vuelve a "
                   "intentarlo; el resto de la ficha no depende de esto.")
            return
        try:
            RUTA_ANALISIS.mkdir(parents=True, exist_ok=True)
            (RUTA_ANALISIS / f"{_clave_libro(libro)}-sinopsis.json").write_text(
                json.dumps(datos, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    partes = ["#### De qué trata", datos.get("de_que_trata", "").strip()]
    temas = [t for t in (datos.get("temas") or []) if str(t).strip()]
    if temas:
        partes.append("**Temas:** " + " · ".join(str(t) for t in temas))
    if datos.get("para_quien", "").strip():
        partes.append(f"**Para quién:** {datos['para_quien'].strip()}")
    if datos.get("aviso", "").strip():
        partes.append(f"**Antes de empezar:** {datos['aviso'].strip()}")
    partes.append("\n_Resumen escrito por un modelo de lenguaje a partir de "
                  "pasajes del propio archivo. Las cifras de arriba no: esas "
                  "están contadas._")
    yield "\n\n".join(partes)


def _suavizar(valores, ventana: int) -> list[float]:
    """Media movil centrada. Sin numpy ni pandas: son cuatro lineas y asi la
    grafica no depende de nada que pueda no estar en el despliegue."""
    if ventana < 2 or len(valores) < ventana:
        return list(valores)
    salida, mitad = [], ventana // 2
    for i in range(len(valores)):
        a, b = max(0, i - mitad), min(len(valores), i + mitad + 1)
        salida.append(sum(valores[a:b]) / (b - a))
    return salida


def _colores_paleta(clave):
    """Los colores de una paleta, para lo que NO es CSS.

    Plotly no sabe leer variables CSS: dibuja una imagen con los
    colores que se le den y ahi se acaba. Por eso la grafica estaba
    clavada en azul hielo aunque la paleta fuera "papel", y sobre el
    panel blanco de las paletas claras la letra de los ejes -#c8dbe6-
    daba 1,3:1. No hay un color que valga para las cinco paletas: para
    pasar AA sobre el fondo mas oscuro hace falta luminancia >= 0,186 y
    sobre el mas claro <= 0,174. Las dos condiciones no se cumplen a la
    vez, asi que el color TIENE que venir de la paleta.
    """
    d = paletas_mod.PALETAS.get(clave) or paletas_mod.PALETAS[
        paletas_mod.POR_DEFECTO]
    return d["vars"]


def _rgba(color: str, alfa: float) -> str:
    """`#rrggbb` -> `rgba(r,g,b,alfa)`. Si ya viene en rgb/rgba se
    devuelve tal cual: las paletas mezclan los dos formatos."""
    c = color.strip()
    if not c.startswith("#"):
        return c
    c = c[1:]
    if len(c) == 3:
        c = "".join(x * 2 for x in c)
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alfa})"


def _grafica_analisis(datos, paleta: str = None):
    """Curva de dificultad del libro, continua y con zoom.

    Era un diagrama de barras y con War and Peace -366 capitulos- se convertia
    en un bloque azul macizo del que no se leia nada. Con una linea se ve la
    forma, y con la barra de herramientas de Plotly se puede ampliar un tramo
    concreto, que es lo que uno quiere cuando hay cientos de capitulos.

    Van dos trazos a proposito: el fino y translucido es el dato real, capitulo
    a capitulo; el grueso es la media movil. Con 366 puntos el dato crudo es
    ruido y la tendencia -"empieza duro y se suelta"- solo se ve suavizada. Con
    pocos capitulos la media movil se desactiva sola y queda la linea real.
    """
    import plotly.graph_objects as go

    filas = datos["filas"]
    x = [f["capitulo"] for f in filas]
    y = [f["dificultad"] for f in filas]
    titulos = [f.get("titulo", "") for f in filas]

    # La ventana crece con el libro: 366 capitulos piden mas suavizado que 13.
    ventana = 1 if len(y) < 12 else max(3, round(len(y) / 25))
    nivel_general = _suavizar(y, ventana)

    # Los colores salen de la paleta elegida, no de una constante. Ver
    # `_colores_paleta`: con la paleta clavada, la grafica era ilegible
    # en papel, menta y amanecer.
    v = _colores_paleta(paleta or paletas_mod.POR_DEFECTO)
    c_texto, c_acento = v["--ll-texto"], v["--ll-acento"]
    c_borde, c_fondo = v["--ll-borde"], v["--ll-fondo"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", name="capítulo a capítulo",
        line=dict(color=c_acento, width=1), opacity=0.35,
        customdata=titulos,
        hovertemplate="Capítulo %{x}<br>%{customdata}<br>"
                      "<b>%{y:.2f}</b> / 2.00<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=x, y=nivel_general, mode="lines", name="nivel general",
        line=dict(color=c_acento, width=2.5, shape="spline", smoothing=0.6),
        fill="tozeroy",
        # El degradado es lo que pidio Miguel: el azul hielo se desvanece hacia
        # abajo en vez de cortar en un bloque plano.
        # El degradado se apaga del todo abajo. La escala publica llega a 2.00
        # y casi ningun libro baja de 1.4, asi que rellenar desde cero con
        # color solido devolvia el mismo bloque macizo que tenian las barras.
        # Asi el color acompana a la linea y el resto respira.
        fillgradient=dict(type="vertical", colorscale=[
            (0.00, _rgba(c_acento, 0.00)), (0.62, _rgba(c_acento, 0.04)),
            (0.86, _rgba(c_acento, 0.16)), (1.00, _rgba(c_acento, 0.38))]),
        hoverinfo="skip"))

    fig.update_layout(
        margin=dict(l=48, r=16, t=16, b=40), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c_texto, size=12),
        hovermode="x unified", dragmode="zoom",
        # La etiqueta flotante la pintaba Plotly con sus colores por
        # defecto: sobre una paleta clara salia letra clara en caja clara.
        hoverlabel=dict(bgcolor=c_fondo, bordercolor=c_borde,
                        font=dict(color=c_texto)),
        showlegend=len(y) >= 12,
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(title_text="Capítulo", gridcolor=c_borde,
                     zeroline=False, showspikes=True, spikethickness=1,
                     spikecolor=_rgba(c_acento, 0.5), spikemode="across")
    fig.update_yaxes(title_text="Dificultad", range=[0, 2.05],
                     gridcolor=c_borde, zeroline=False,
                     dtick=0.5)
    return fig


def _repintar_grafica(libro, clave):
    """Vuelve a dibujar la curva con la paleta nueva, si hay curva.

    Cambiar de paleta cambia el CSS al momento, pero la grafica es una
    imagen ya pintada: se quedaba con los colores de la paleta anterior
    hasta que volvieras a medir el libro.
    """
    if libro is None:
        return gr.update()
    datos = _analisis_guardado(libro) or _analisis_guardado(libro, "rapido")
    if not datos or not datos.get("filas"):
        return gr.update()
    return _grafica_analisis(datos, clave)


def _resumen_analisis(datos, como="cifra") -> str:
    filas = datos["filas"]
    medias = [f["dificultad"] for f in filas]
    # Ponderada por ventanas, no media de medias: ver `ficha.dificultad_global`.
    global_ = ficha.dificultad_global(filas)
    facil = min(filas, key=lambda f: f["dificultad"])
    dificil = max(filas, key=lambda f: f["dificultad"])
    mitad = len(medias) // 2 or 1
    principio = sum(medias[:mitad]) / mitad
    final = sum(medias[mitad:]) / max(1, len(medias) - mitad)
    if final - principio > 0.12:
        forma = "**se va complicando**: la segunda mitad es más dura que la primera"
    elif principio - final > 0.12:
        forma = "**se va soltando**: cuesta más al principio que al final"
    else:
        forma = "mantiene un nivel **parejo de principio a fin**"
    # Como se midio, dicho sin adornos. El vistazo rapido NO puede presumir de
    # recorrer el libro entero: son dos cosas distintas y hay que distinguirlas
    # o la cifra rapida acabaria citandose como si fuera la completa.
    if datos.get("modo") == "rapido":
        medidos = datos.get("capitulos_medidos", len(filas))
        totales = datos.get("capitulos_totales", medidos)
        detalle = (f"**vistazo rápido**: {datos['ventanas']:,} ventanas de 250 "
                   f"palabras tomadas de {medidos} capítulos"
                   + (f" repartidos entre los {totales} del libro"
                      if totales > medidos else "")
                   + ". Da la forma de la curva, no el número definitivo; "
                     "para eso está *Analizar el libro entero*.")
    else:
        detalle = (f"medido leyendo **{datos['ventanas']:,} ventanas** de 250 "
                   f"palabras sobre {datos['palabras']:,} en total. Aquí no se "
                   f"muestrea: el modelo recorre cada capítulo entero.")
    return (
        f"### {datos['titulo']}" + (f" — {datos['autor']}" if datos["autor"] else "")
        + f"\n\n{_nivel_dicho(global_, scoring.public_band(global_), como)} "
          f"de media, {detalle}\n\n"
        + f"El libro {forma}.\n\n"
        + f"- Lo más llevadero: **capítulo {facil['capitulo']}** "
          f"({facil['titulo']}) con {facil['dificultad']:.2f}\n"
        + f"- Lo más exigente: **capítulo {dificil['capitulo']}** "
          f"({dificil['titulo']}) con {dificil['dificultad']:.2f}\n"
        + f"- Recorrido de dificultad entre capítulos: "
          f"{min(medias):.2f} a {max(medias):.2f}")


def _oracion_de(texto: str, palabra: str) -> str:
    """Primera oracion con cuerpo del capitulo que contiene la palabra.

    Se prefiere una oracion de verdad a un encabezado. Los titulos ("CHAPTER
    X.", "The Dead House") tambien casan con el patron, y devolver uno como
    contexto deja a la desambiguacion sin nada a lo que agarrarse: la palabra
    llegaria practicamente desnuda. Si no hay mas que el encabezado, se
    devuelve, que es mejor que nada.
    """
    if not texto or not palabra:
        return ""
    patron = re.compile(rf"\b{re.escape(palabra.strip())}\b", re.IGNORECASE)
    respaldo = ""
    for frase in scoring.SENT_RE.findall(texto):
        if not patron.search(frase):
            continue
        limpia = " ".join(frase.split())
        if len(limpia.split()) >= 6:
            return limpia
        respaldo = respaldo or limpia
    return respaldo


# Rotulos de la ficha en las dos lenguas. Si el lector pide la explicacion en
# ingles, dejarle las etiquetas en espanol queda a medio hacer.
_ROTULOS = {
    "es": {
        "pron": "Pronunciación", "dicc": "Diccionario", "aqui": "Aquí significa",
        "gram": "Gramática", "nivel": "Para tu nivel", "ej": "Ejemplo",
        "elegido": "Elegido entre {n} acepciones{sim}.",
        "afinidad": ", afinidad {v:.2f}",
        "sin_entrada": "No hay entrada de diccionario para esta palabra.",
        "dudoso": ("Poca confianza en la acepción elegida (afinidad {v:.2f} "
                   "sobre 1.00). Fíjate más en «Aquí significa» que en la "
                   "definición de diccionario."),
        "dudoso_solo": ("Poca confianza en la acepción elegida (afinidad "
                        "{v:.2f} sobre 1.00) y esta vez no hay explicación de "
                        "contexto. Puede no ser el sentido que tiene en tu "
                        "frase: léela entera antes de fiarte."),
        "cache": "desde caché", "tts": "audio generado con tts-1",
        "rareza": ("muy común", "frecuente", "poco frecuente", "rara"),
    },
    "en": {
        "pron": "Pronunciation", "dicc": "Dictionary", "aqui": "Here it means",
        "gram": "Grammar", "nivel": "For your level", "ej": "Example",
        "elegido": "Chosen from {n} senses{sim}.",
        "afinidad": ", affinity {v:.2f}",
        "sin_entrada": "No dictionary entry for this word.",
        "dudoso": ("Low confidence in the sense picked (affinity {v:.2f} of "
                   "1.00). Trust “Here it means” more than the dictionary "
                   "gloss."),
        "dudoso_solo": ("Low confidence in the sense picked (affinity {v:.2f} "
                        "of 1.00), and there is no contextual explanation this "
                        "time. It may not be the sense your sentence uses: "
                        "read the whole sentence before trusting it."),
        "cache": "from cache", "tts": "audio generated with tts-1",
        "rareza": ("very common", "common", "uncommon", "rare"),
    },
}

# Por debajo de esto la eleccion de acepcion es practicamente un sorteo: se
# avisa en vez de presentarla como si fuera segura.
AFINIDAD_DUDOSA = 0.35


# Traduccion de los avisos tecnicos a algo que un lector pueda entender. Los
# avisos vienen de `lexicon.py` con el texto de la excepcion pegado, que es
# util en un log y horrible en pantalla: nadie quiere leer
# "RuntimeError: Error code: 429 - You exceeded your current quota"
# mientras lee una novela.
_AVISOS_HUMANOS = (
    (("429", "quota", "insufficient_quota", "billing"), {
        "es": "Se ha agotado el presupuesto mensual de explicaciones. El "
              "diccionario, la fonética y el audio siguen funcionando.",
        "en": "The monthly budget for explanations has run out. The "
              "dictionary, phonetics and audio still work."}),
    (("sin OPENAI_API_KEY", "api key", "authentication", "401"), {
        "es": "Sin clave de OpenAI: no hay explicación de contexto. El resto "
              "de la ficha no la necesita.",
        "en": "No OpenAI key: no contextual explanation. The rest of the "
              "card does not need it."}),
    (("sin audio en el diccionario",), {
        "es": "El diccionario no trae audio de esta palabra, así que la "
              "pronunciación de arriba está generada.",
        "en": "The dictionary has no audio for this word, so the "
              "pronunciation above is generated."}),
    (("sin sentido elegido",), {
        "es": "No se pudo elegir una acepción para esta palabra.",
        "en": "No sense could be picked for this word."}),
    (("timeout", "timed out", "connection", "network", "getaddrinfo"), {
        "es": "No hay conexión con OpenAI ahora mismo. El diccionario y la "
              "fonética son locales y siguen aquí.",
        "en": "No connection to OpenAI right now. The dictionary and "
              "phonetics are local and still here."}),
)


def _humanizar(aviso: str, idioma: str) -> str:
    bajo = aviso.lower()
    for pistas, textos in _AVISOS_HUMANOS:
        if any(p.lower() in bajo for p in pistas):
            return textos.get(idioma, textos["es"])
    return aviso


def _ficha(r, idioma: str = "es") -> str:
    """La consulta lexica en markdown, diciendo de donde sale cada cosa."""
    t = _ROTULOS.get(idioma, _ROTULOS["es"])
    # Cinturon y tirantes: `_consultar` ya rechaza lo larguisimo, pero esta
    # funcion se llama tambien desde otros sitios y un encabezado es lo unico
    # de la ficha que puede llenar una pantalla de movil sin que nada lo pare.
    cab = f"## {str(r.palabra_superficie)[:LIMITE_PALABRA]}"
    if r.lema_buscado and r.lema_buscado.lower() != r.palabra_superficie.lower():
        cab += f"  ·  _{r.lema_buscado}_"
    if r.categoria:
        cab += f"  ·  {r.categoria}"
    L = [cab]

    fon = []
    if r.ipa_uk:
        fon.append(f"UK {r.ipa_uk}")
    if r.ipa_us:
        fon.append(f"US {r.ipa_us}")
    if fon:
        L.append(f"**{t['pron']}:** " + "  ·  ".join(fon))

    if r.sentido:
        L.append(f"**{t['dicc']}** (Wiktionary): {r.sentido}")
        if r.etiquetas_sentido:
            L.append(f"_{', '.join(r.etiquetas_sentido)}_")
        if r.n_sentidos_candidatos > 1:
            sim = (t["afinidad"].format(v=r.similitud)
                   if r.similitud is not None else "")
            L.append("_" + t["elegido"].format(n=r.n_sentidos_candidatos, sim=sim) + "_")
        # `lexicon` ya avisa por su cuenta cuando el margen entre acepciones es
        # estrecho. Si lo ha hecho, no se repite el mismo aviso con otras
        # palabras: dos advertencias seguidas diciendo lo mismo se ignoran.
        ya_avisado = any("margen bajo" in a or "provisional" in a for a in r.avisos)
        if (not ya_avisado and r.similitud is not None
                and r.n_sentidos_candidatos > 1 and r.similitud < AFINIDAD_DUDOSA):
            # Si OpenAI no contesto no hay "Aquí significa" a la que remitir:
            # mandar al lector a una seccion que no existe es peor que callar.
            clave = "dudoso" if r.definicion_contextual else "dudoso_solo"
            L.append("[!] " + t[clave].format(v=r.similitud))
    else:
        L.append(f"_{t['sin_entrada']}_")

    if r.definicion_contextual:
        L.append(f"**{t['aqui']}:** {r.definicion_contextual}")
    if r.explicacion_gramatical:
        L.append(f"**{t['gram']}:** {r.explicacion_gramatical}")
    if r.explicacion_adaptada:
        L.append(f"**{t['nivel']} ({r.banda_lector}):** {r.explicacion_adaptada}")
    if r.ejemplo_simplificado:
        L.append(f"**{t['ej']}:** _{r.ejemplo_simplificado}_")

    pie = []
    if r.frecuencia_zipf is not None:
        muy, frec, poco, rara = t["rareza"]
        rareza = (muy if r.frecuencia_zipf >= 5 else
                  frec if r.frecuencia_zipf >= 4 else
                  poco if r.frecuencia_zipf >= 3 else rara)
        pie.append(f"{rareza} (zipf {r.frecuencia_zipf:.1f})")
    if r.desde_cache:
        pie.append(t["cache"])
    if r.audio_generado:
        pie.append(t["tts"])
    if pie:
        L.append("_" + " · ".join(pie) + "_")
    for a in r.avisos:
        L.append(f"[!] {_humanizar(a, idioma)}")
    return "\n\n".join(L)


def _reproductores(r) -> str:
    """Audio remoto de Wiktionary. Los locales van al componente gr.Audio."""
    trozos = []
    for etiqueta, url in (("UK", r.audio_uk), ("US", r.audio_us)):
        if url and str(url).startswith("http"):
            # La URL viene del volcado de Wiktionary. Hoy las 7.484 son de
            # upload.wikimedia.org y ninguna lleva comillas, pero un dato que
            # no controlamos no entra sin escapar en un atributo HTML.
            seguro = _html.escape(str(url), quote=True)
            trozos.append(
                f'<p style="margin:.2rem 0"><b>{etiqueta}</b><br>'
                f'<audio controls preload="none" src="{seguro}"></audio></p>')
    return "".join(trozos)


def _local(url):
    """Ruta reproducible por gr.Audio, o None si el audio es remoto."""
    if url and not str(url).startswith("http") and os.path.exists(str(url)):
        return str(url)
    return None


def _consultar(p, libro, idx, palabra, oracion_manual, idioma="es",
               peticion: gr.Request = None):
    """Consulta lexica en dos etapas, porque la espera es casi toda de red.

    Medido: todo el trabajo local -spaCy, el SQLite de 1,48 M entradas, la
    desambiguacion con MiniLM, la IPA- son **40 ms** con los modelos ya
    calientes. Los 30 segundos largos que se notan son la llamada a OpenAI.
    Antes la pantalla se quedaba en blanco todo ese rato y parecia colgada.

    Es una funcion generadora: el primer `yield` dice que se esta buscando, y
    el segundo trae el resultado. No cambia ni un numero, solo deja de mentir
    sobre lo que esta pasando.
    """
    palabra = (palabra or "").strip()
    if not palabra:
        yield "Escribe la palabra que quieres consultar.", "", gr.update(visible=False)
        return
    if len(palabra.split()) > 4:
        yield ("Consulta una palabra (o un phrasal verb corto), no una frase.",
               "", gr.update(visible=False))
        return
    if len(palabra) > LIMITE_PALABRA:
        yield ({"es": f"Eso son {len(palabra)} caracteres seguidos: ninguna "
                      f"palabra inglesa pasa de {LIMITE_PALABRA}. Selecciona "
                      f"una palabra del texto y vuelve a intentarlo.",
                "en": f"That is {len(palabra)} characters in a row: no English "
                      f"word goes past {LIMITE_PALABRA}. Pick a word from the "
                      f"text and try again."}[idioma if idioma == "en" else "es"],
               "", gr.update(visible=False))
        return

    esperando = ("es" if idioma != "en" else "en")
    yield ({"es": f"### {palabra}\n\nBuscando en el diccionario y preparando "
                  f"la explicación de contexto…",
            "en": f"### {palabra}\n\nLooking it up and preparing the "
                  f"contextual explanation…"}[esperando], "", None)

    # La oracion viaja entera al modelo y ademas entra en la clave de cache,
    # asi que un texto largo distinto en cada intento es una llamada de pago
    # nueva cada vez. El recorte va en el servidor: el limite del navegador es
    # una sugerencia, no una defensa.
    oracion = (oracion_manual or "").strip()[:LIMITE_ORACION]
    origen = "de la oración que escribiste"
    if not oracion and libro is not None and idx is not None:
        cap_actual = _cap(libro, idx)
        oracion = _oracion_de(cap_actual.texto, palabra) if cap_actual else ""
        origen = "localizada en el capítulo"
    if not oracion:
        oracion = palabra
        origen = "sin contexto: la desambiguación será peor"

    # El tope por hora es un freno de GASTO, no de uso. La cabecera de este
    # modulo lo dice: "las acciones que no cuestan dinero no se limitan". Y una
    # consulta sin perfil -o en una copia sin clave- es diccionario, IPA y
    # audio de Wiktionary: todo local y gratis. Aplicarle el tope cortaba la
    # consulta 31 de un aula entera detras de la misma NAT sin que ninguna
    # pudiera costar un centimo, y encima el aviso les decia que "leer, buscar
    # y medir siguen funcionando: no cuestan nada", como si esta si costara.
    #
    # `permite` PREGUNTA sin consumir. Quien decide de forma atomica sigue
    # siendo `_puede_pagar` mas abajo, asi que esto no reabre la condicion de
    # carrera que se cerro alli. Y se exige tambien que HAYA clave: sin ella no
    # se llama a OpenAI por mucho perfil que tenga el visitante.
    va_a_costar = (not config.falta()
                   and cuentas.permite(BASE_DATOS_LECTOR,
                                       _codigo_de(peticion))[0])
    if va_a_costar and not _dentro_del_limite(peticion, "lexico",
                                              LIMITE_CONSULTAS_HORA):
        yield (_aviso(_mensaje_limite(
            idioma, _minutos_para_la_siguiente("lexico", peticion))),
            "", gr.update(visible=False))
        return

    nivel = p.nivel if p is not None else NIVEL_POR_DEFECTO
    try:
        # `_puede_pagar` consume el uso si lo concede, en una sola operacion:
        # no hay que apuntarlo despues.
        puede, motivo_pago = _puede_pagar(peticion)
        r = consultor().consultar(palabra, oracion, nivel, idioma=idioma,
                                  usar_openai=puede)
    except (FileNotFoundError, OSError) as e:
        yield _aviso(e), "", gr.update(visible=False)
        return
    # Si la puerta de pago dijo que no, hay que decir POR QUE. Antes
    # `motivo_pago` se tiraba: `lexicon` seguia su camino de "sin clave" y el
    # visitante leia "Sin clave de OpenAI: no hay explicacion de contexto" en
    # un servidor que SI tiene clave. Lo que pasaba era que no habia entrado
    # con su perfil, o que habia agotado su cupo, y no se le decia ninguna de
    # las dos cosas. Los otros dos manejadores de pago si lo mostraban.
    if not puede and motivo_pago:
        r.avisos = ([a for a in r.avisos if "OPENAI_API_KEY" not in a]
                    + [motivo_pago])
    # Y el cupo: `_puede_pagar` cobra ANTES de saber si se va a llamar a
    # OpenAI. Si la respuesta sale de la cache de `lexicon.db` no se gasta un
    # centimo, pero el contador bajaba igual, asi que `tope` no era "llamadas
    # de pago permitidas" como declara `cuentas.py`, sino pulsaciones. Se
    # devuelve el uso. Cobrar primero y devolver despues, y no al reves, para
    # no reabrir la condicion de carrera que `consumir` cerro.
    elif puede and getattr(r, "desde_cache", False):
        cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))
    # Al cuaderno **solo si el diccionario encontro algo**. Sin este filtro
    # acababan dentro las pruebas y los errores de dedo, y la pestana "Mis
    # palabras" se llenaba de cadenas sin sentido. Una palabra que el
    # diccionario no reconoce no es vocabulario aprendido.
    if r.sentido:
        cuaderno.registrar(
            palabra=r.palabra_superficie, lema=r.lema_buscado or r.lema,
            oracion=oracion, categoria=r.categoria, sentido=r.sentido,
            libro=(libro.titulo if libro is not None else None),
            capitulo=(int(idx) + 1 if _cap(libro, idx) is not None else None),
            banda=r.banda_lector, zipf=r.frecuencia_zipf,
            ruta=_archivo_lector("cuaderno.db", peticion))

    if oracion == palabra:
        # Ni capitulo abierto ni oracion escrita. Antes el pie decia
        # "Contexto: sin contexto: la desambiguacion sera peor", que se
        # contradice solo, y encima citaba la palabra suelta como si fuera
        # una frase del libro. Mejor decir la verdad y no fingir contexto.
        cola = ("\n\n_No había ningún capítulo abierto ni escribiste una "
                "oración, así que busqué la palabra suelta: el sentido "
                "elegido puede no ser el que te interesa._"
                if idioma != "en" else
                "\n\n_No chapter was open and you did not type a sentence, so "
                "I looked the word up on its own: the sense picked may not be "
                "the one you need._")
    else:
        contexto = "Contexto" if idioma == "es" else "Context"
        cola = f"\n\n> {oracion}\n\n_{contexto}: {origen}._"
    ficha = _ficha(r, idioma) + cola
    local = _local(r.audio_us) or _local(r.audio_uk)
    yield ficha, _reproductores(r), gr.update(value=local, visible=bool(local))


# Por que capitulo va cada lector, para no repetir siempre la misma frase.
_RONDA_FRASE: dict[tuple, int] = {}


def _frase_del_capitulo(libro, idx):
    """Manda la primera oracion de largo razonable a la practica de voz.

    Devuelve `gr.update()` -es decir, no toca nada- cuando no hay frase que
    traer. Antes devolvia cadena vacia, asi que quien habia escrito su frase
    a mano y pulsaba el boton por curiosidad **se quedaba sin ella**, sin un
    solo mensaje que lo explicara.
    """
    if libro is None or idx is None:
        return gr.update()
    c = _cap(libro, idx)
    if c is None:
        return gr.update()
    # Por parrafos, no por el capitulo entero: los encabezados ("I", "The Dead
    # House") no llevan punto, asi que la primera "oracion" del texto crudo se
    # los traga enteros y sale una frase absurda para leer en voz alta.
    candidatas = []
    for parrafo in re.split(r"\n\s*\n", c.texto):
        limpio = " ".join(parrafo.split())
        if len(limpio.split()) < 30:      # titulillo o linea suelta
            continue
        for frase in scoring.SENT_RE.findall(limpio):
            f = " ".join(frase.split())
            if 6 <= len(f.split()) <= 25:
                candidatas.append(f)
    if not candidatas:
        return gr.update()
    # Una distinta en cada pulsacion. Antes devolvia siempre la primera del
    # capitulo, asi que practicar dos veces seguidas era practicar lo mismo:
    # el boton parecia roto aunque estuviera haciendo su trabajo.
    clave = (getattr(libro, "titulo", ""), int(idx))
    n = _RONDA_FRASE.get(clave, -1) + 1
    _RONDA_FRASE[clave] = n
    return candidatas[n % len(candidatas)]


# --- Punto 5: pronunciacion ----------------------------------------------

_CSS_VOZ = """<style>
/* Este bloque llega DESPUES de `#ll-css` en el DOM y con la misma
   especificidad, asi que su `border` abreviado reescribia entero el
   `border-color:var(--ll-borde)` de alli, y el `color:inherit` tapaba
   `--ll-lector-texto`. Era, palabra por palabra, el mismo fallo que se
   corrigio en `#ll-lector` y que aqui se quedo sin corregir. */
#ll-voz{padding:1.1rem 1.3rem;border:1px solid var(--ll-borde);
  border-radius:10px;font-family:Georgia,"Times New Roman",serif;
  font-size:21px;line-height:2.1;color:var(--ll-lector-texto)}
#ll-voz .ll-w{padding:.12em .34em;border-radius:5px;margin:0 .06em;
  border-bottom:3px solid transparent}
/* Verde de acierto y rojo de fallo. Salen de la paleta y no del CSS porque
   NO hay un par de colores que valga para las cinco: medidos contra el fondo
   del lector, el verde clavado daba 2,21-2,30 en las tres paletas claras y el
   rojo 2,86-2,95 sobre su propio fondo, los dos por debajo del 3:1 que WCAG
   pide a un objeto grafico. Y oscurecerlos para las claras los hunde en las
   oscuras: el rojo a x0,8 sube a 4,04 en amanecer y cae a 2,45 en
   medianoche. El significado no cambia -verde es bien y rojo es mal en las
   cinco-, solo el tono. */
#ll-voz .ok{border-bottom-color:var(--ll-bien)}
#ll-voz .mal{background:var(--ll-mal-fondo);border-bottom-color:var(--ll-mal);
  font-weight:600}
#ll-voz .leyenda{display:block;margin-top:1rem;font-family:system-ui,sans-serif;
  font-size:13px;opacity:.78;line-height:1.5}
#ll-voz .oido{display:block;margin-top:.5rem;font-family:system-ui,sans-serif;
  font-size:14px;opacity:.85;font-style:italic}
</style>"""


def _palabras_html(ev, transcripcion_ok: bool) -> str:
    """La frase objetivo palabra a palabra: cual sono bien y cual no.

    Es lo que de verdad quiere ver quien practica. El numero global dice poco;
    saber que fallaste en 'fortress' y no en 'the' es lo accionable.
    """
    if not ev.palabras_objetivo:
        return ""
    if not transcripcion_ok:
        return (_CSS_VOZ + '<div id="ll-voz"><span class="leyenda">'
                'No se pudo transcribir tu audio, así que no puedo marcarte '
                'las palabras.</span></div>')
    fallo = set(ev.palabras_falladas)
    trozos = [
        f'<span class="ll-w {"mal" if w in fallo else "ok"}">{_html.escape(w)}</span>'
        for w in ev.palabras_objetivo
    ]
    bien = len(ev.palabras_objetivo) - len(fallo)
    oido = _html.escape(ev.transcripcion or "(no se entendió nada)")
    return (_CSS_VOZ + '<div id="ll-voz">' + " ".join(trozos)
            + f'<span class="oido">Se te entendió: “{oido}”</span>'
            + f'<span class="leyenda">Subrayado verde: bien pronunciada '
              f'({bien} de {len(ev.palabras_objetivo)}). Fondo rojo: no se '
              f'entendió como esa palabra ({len(fallo)}).</span></div>')


def _practicar(ruta_audio, frase, peticion: gr.Request = None):
    # Cada practica genera un audio de referencia de pago y nunca acierta en
    # cache (el nombre lleva marca de tiempo), asi que el tope va aqui.
    frase = (frase or "").strip()[:LIMITE_FRASE_VOZ]
    if not frase:
        return "", "Escribe la frase que vas a leer en voz alta.", gr.update(visible=False)
    if not ruta_audio:
        return "", "Graba tu voz con el micrófono (o sube un audio).", gr.update(visible=False)
    if not _dentro_del_limite(peticion, "voz", LIMITE_VOZ_HORA):
        return ("", _aviso(_mensaje_limite(
            "es", _minutos_para_la_siguiente("voz", peticion))),
            gr.update(visible=False))
    # Esta es la funcion mas cara de la aplicacion: transcribe con whisper y
    # genera un audio de referencia, y ninguna de las dos cosas acierta en
    # cache. Por eso es la que se cierra detras del codigo.
    puede, motivo_pago = _puede_pagar(peticion)
    if not puede:
        return "", motivo_pago, gr.update(visible=False)
    try:
        # Los fallos se registran aparte, en la base de ESTE lector: las
        # palabras que a uno se le atragantan no son asunto de los demas.
        s = voz.practicar(ruta_audio, frase, guardar_fallos=False)
        if s.evaluacion.palabras_falladas and s.transcripcion_ok:
            voz.registrar_fallos(s.evaluacion.palabras_falladas,
                                 ruta=_archivo_lector("voz.db", peticion))
    except Exception as e:
        return "", _aviso(e), gr.update(visible=False)

    ev = s.evaluacion
    L = [f"## {ev.puntuacion:.0f} / 100"]
    if not s.transcripcion_ok:
        L.append("[!] No se pudo transcribir (sin `OPENAI_API_KEY` o sin red). "
                 "La puntuación de arriba no es válida.")
    elif not ev.palabras_falladas:
        L.append("Ni una palabra fallada. Sube el listón con una frase más larga.")

    if s.correccion:
        L.append(f"**Cómo corregirlo:** {s.correccion.resumen}")
        for d in s.correccion.detalles:
            L.append(f"- **{d.palabra}** — {d.sonido_que_falla}. "
                     f"{d.como_colocar_la_boca}")
    # El reproductor nace oculto, asi que devolver la ruta pelada asignaria el
    # valor y lo dejaria invisible: se generaba el audio, se pagaba y no se
    # veia nunca. Hay que encenderlo explicitamente.
    return (_palabras_html(ev, s.transcripcion_ok), "\n\n".join(L),
            gr.update(value=s.audio_correcto, visible=bool(s.audio_correcto)))


def _debiles(peticion: gr.Request = None):
    try:
        filas = voz.puntos_debiles(n=15, ruta=_archivo_lector("voz.db", peticion))
    except Exception as e:
        return _aviso(e)
    if not filas:
        return "Aún no hay palabras registradas. Practica una frase primero."
    return ("Tus palabras más falladas:\n\n"
            + "\n".join(f"{i + 1}. **{w}** — {n} vez{'es' if n > 1 else ''}"
                        for i, (w, n) in enumerate(filas)))


# --- Cuaderno: lo unico que sobrevive a cerrar la app ---------------------

_CSS_CUADERNO = """<style>
#ll-cuaderno{display:flex;flex-direction:column;gap:.7rem}
/* El fondo sale de la paleta, no clavado. Estaba en rgba(8,16,28,.55),
   que es un azul casi negro: en las paletas claras dejaba el texto entre
   2,5 y 3,9:1 en los dos modos. */
#ll-cuaderno .ll-c{padding:.75rem .9rem;border:1px solid var(--ll-borde);
  border-radius:9px;background:var(--ll-panel);color:var(--ll-texto)}
/* Sin esto, una palabra larguisima o una URL desbordan la pantalla del movil
   y la pestana entera se convierte en un muro ilegible. */
#ll-cuaderno .ll-c *{overflow-wrap:anywhere;word-break:break-word}
#ll-cuaderno .ll-p{font-weight:700;font-size:1.05rem}
#ll-cuaderno .ll-d{opacity:.78;font-size:.82rem;font-weight:400}
#ll-cuaderno .ll-f{margin:.4rem 0 .3rem;padding-left:.7rem;
  /* Azul hielo clavado: 1,23:1 sobre las paletas claras. Mismo fallo que
     las tarjetas, en el borde que sobrevivio al arreglo. */
  border-left:3px solid var(--ll-acento);
  font-family:Georgia,serif;line-height:1.5}
#ll-cuaderno .ll-s{font-size:.9rem;opacity:.85}
</style>"""


def _recortar(t, n: int) -> str:
    """Texto de una linea y acotado: nada puede desbordar una pantalla."""
    t = " ".join(str(t or "").split())
    return t if len(t) <= n else t[:n - 1] + "…"


def _mis_palabras(peticion: gr.Request = None):
    db = _archivo_lector("cuaderno.db", peticion)
    total, lemas, libros = cuaderno.contar(db)
    if not total:
        return ("<p>Todavía no has consultado ninguna palabra. Abre un libro "
                "en <b>Leer</b>, selecciona una que no conozcas —doble clic "
                "con el ratón, o mantenla pulsada en el móvil— y aparecerá "
                "aquí con la frase en la que la encontraste.</p>")
    tarjetas = []
    for a in cuaderno.ultimas(20, db):
        donde = f" · {_recortar(a.libro, 40)}" if a.libro else ""
        if a.libro and a.capitulo:
            donde += f", cap. {a.capitulo}"
        rareza = f" · {a.rareza}" if a.rareza else ""
        partes = [f'<div class="ll-p">{_html.escape(_recortar(a.palabra, 40))}'
                  f'<span class="ll-d">{_html.escape(rareza + donde)}</span></div>',
                  f'<div class="ll-f">{_html.escape(_recortar(a.oracion, 220))}</div>']
        if a.sentido:
            partes.append(f'<div class="ll-s">'
                          f'{_html.escape(_recortar(a.sentido, 160))}</div>')
        tarjetas.append('<div class="ll-c">' + "".join(partes) + "</div>")
    cabecera = (f"<p><b>{lemas}</b> palabras distintas, en <b>{total}</b> "
                f"consultas sobre <b>{libros}</b> "
                f"libro{'s' if libros != 1 else ''}.</p>")
    return (_CSS_CUADERNO + cabecera
            + '<div id="ll-cuaderno">' + "".join(tarjetas) + "</div>")


def _repasar(peticion: gr.Request = None):
    """Cinco palabras para repasar: las mas raras que has mirado, mas las
    que fallaste al leerlas en voz alta. Sin nota y sin racha: es un
    recordatorio, no un examen."""
    anotaciones = cuaderno.para_repasar(5, _archivo_lector("cuaderno.db", peticion))
    try:
        debiles = voz.puntos_debiles(n=5, ruta=_archivo_lector("voz.db", peticion))
    except Exception:
        debiles = []
    if not anotaciones and not debiles:
        return ("<p>No hay nada que repasar todavía. Consulta alguna palabra "
                "mientras lees, o practica una frase en voz alta.</p>")
    trozos = [_CSS_CUADERNO]
    if anotaciones:
        trozos.append("<p><b>Del cuaderno</b> — ¿las recuerdas?</p>"
                      '<div id="ll-cuaderno">')
        for a in anotaciones:
            sentido = (f'<details><summary class="ll-s">Ver el sentido</summary>'
                       f'<div class="ll-s">'
                       f'{_html.escape(_recortar(a.sentido, 160))}</div></details>'
                       if a.sentido else "")
            trozos.append(
                f'<div class="ll-c"><div class="ll-p">'
                f'{_html.escape(_recortar(a.palabra, 40))}</div>'
                f'<div class="ll-f">{_html.escape(_recortar(a.oracion, 220))}'
                f'</div>{sentido}</div>')
        trozos.append("</div>")
    if debiles:
        lista = ", ".join(f"<b>{_html.escape(_recortar(w, 30))}</b> ({n})"
                          for w, n in debiles)
        trozos.append(f"<p><b>De la práctica en voz alta</b><br>{lista}</p>")
    return "".join(trozos)


# --- Mis libros: lo que se esta leyendo y por donde se va ----------------

_CSS_BIBLIO = """<style>
#ll-biblio{display:flex;flex-direction:column;gap:.7rem}
#ll-biblio .ll-l{padding:.8rem .95rem;border:1px solid var(--ll-borde);
  border-radius:9px;background:var(--ll-panel);color:var(--ll-texto)}
#ll-biblio .ll-l *{overflow-wrap:anywhere}
#ll-biblio .ll-t{font-weight:700;font-size:1.05rem}
#ll-biblio .ll-a{opacity:.78;font-size:.85rem}
/* El canal y el relleno de la barra de avance iban clavados en azul hielo
   -rgba(143,211,232,.16) y #3aa9cf->#8fd3e8-, asi que la barra contra su
   propio canal daba 1,47-1,53:1 en las tres paletas claras. Es el mismo
   color clavado que las tarjetas de S3, en el sitio que no se reviso. */
#ll-biblio .ll-b{height:7px;border-radius:4px;margin:.5rem 0 .35rem;
  background:var(--ll-borde);overflow:hidden}
#ll-biblio .ll-b i{display:block;height:100%;
  background:linear-gradient(90deg,var(--ll-acento-hondo),var(--ll-acento))}
#ll-biblio .ll-n{font-size:.85rem;opacity:.8}
#ll-biblio .ll-x{font-size:.82rem;opacity:.78;font-style:italic}
</style>"""


def _mis_libros(peticion: gr.Request = None):
    """La estanteria: que se esta leyendo, por donde y cuanto se ha consultado."""
    todos = biblioteca.listar(_archivo_lector("biblioteca.json", peticion))
    # Los libros cuyo archivo ya no esta no se pintan. No se borran -si el
    # archivo vuelve, el marcapaginas sigue ahi-, pero ensucian: la estanteria
    # es para volver a leer, y a un archivo que no existe no se vuelve.
    libros = [e for e in todos if e.existe]
    ausentes = len(todos) - len(libros)
    if not libros:
        return ("<p>Todavía no has abierto ningún libro. Búscalo en "
                "<b>Buscar lectura</b> o sube el tuyo en <b>Leer</b>, y "
                "aparecerá aquí con el punto donde lo dejaste.</p>",
                gr.update(choices=[], value=None))

    db = _archivo_lector("cuaderno.db", peticion)
    por_libro = {}
    for a in cuaderno.ultimas(500, db):
        if a.libro:
            por_libro[a.libro] = por_libro.get(a.libro, 0) + 1

    tarjetas, opciones = [], []
    for e in libros:
        pct = int(round(e.avance * 100))
        consultadas = por_libro.get(e.titulo, 0)
        nota = (f"Capítulo {e.capitulo + 1} de {e.capitulos} · {pct}% · "
                f"{e.palabras:,} palabras")
        if consultadas:
            nota += f" · {consultadas} palabra{'s' if consultadas != 1 else ''} consultada{'s' if consultadas != 1 else ''}"
        tarjetas.append(
            f'<div class="ll-l"><div class="ll-t">'
            f'{_html.escape(_recortar(e.titulo, 60))}</div>'
            f'<div class="ll-a">{_html.escape(_recortar(e.autor or "autor desconocido", 50))}</div>'
            f'<div class="ll-b"><i style="width:{pct}%"></i></div>'
            f'<div class="ll-n">{_html.escape(nota)}</div></div>')
        opciones.append((f"{e.titulo} — cap. {e.capitulo + 1} de {e.capitulos}",
                         e.ruta))
    pie = ("" if not ausentes else
           f'<p class="ll-x">{ausentes} libro{"s" if ausentes != 1 else ""} '
           f'que abriste ya no está{"n" if ausentes != 1 else ""} en el disco. '
           f'Si vuelves a abrirlo{"s" if ausentes != 1 else ""}, aparecerá'
           f'{"n" if ausentes != 1 else ""} otra vez por donde ibas.</p>')
    return (_CSS_BIBLIO + '<div id="ll-biblio">' + "".join(tarjetas) + "</div>" + pie,
            gr.update(choices=opciones, value=opciones[0][1] if opciones else None))


def _seguir_leyendo(ruta_libro, peticion: gr.Request = None):
    """Reabre un libro de la estanteria por el capitulo donde se quedo."""
    vacio = gr.update(choices=[], value=None)
    if not ruta_libro:
        yield (None, vacio, _html_lectura(""), gr.update(), gr.Tabs(),
               "Elige uno de tus libros.")
        return
    yield (None, vacio, _html_lectura(""), gr.update(), gr.Tabs(),
           "Abriendo…")
    # El capitulo guardado se lee ANTES de abrir: `_abrir` vuelve a anotar el
    # libro en la biblioteca con su capitulo inicial, asi que leerlo despues
    # devolvia siempre el principio y "retomar" no retomaba nada.
    guardado = next((e for e in biblioteca.listar(
        _archivo_lector("biblioteca.json", peticion)) if e.ruta == str(ruta_libro)), None)
    libro, upd, html, resumen = _abrir(ruta_libro, peticion)
    if libro is None:
        yield None, vacio, _html_lectura(""), resumen, gr.Tabs(), resumen
        return
    idx = upd["value"]
    if guardado and 0 <= guardado.capitulo < len(libro.capitulos):
        idx = guardado.capitulo
        # Y se devuelve el marcapaginas al capitulo de verdad.
        _guardar_sesion(ruta_libro, libro.titulo, idx, peticion)
        biblioteca.anotar(ruta_libro=str(ruta_libro), titulo=libro.titulo,
                          autor=libro.autor, capitulos=len(libro.capitulos),
                          capitulo=idx, palabras=libro.palabras,
                          ruta=_archivo_lector("biblioteca.json", peticion))
    c = libro.capitulos[idx]
    yield (libro, gr.update(choices=upd["choices"], value=idx),
           _html_lectura(c.texto),
           f"**{libro.titulo}** — retomas en el capítulo {idx + 1} de "
           f"{len(libro.capitulos)}: _{c.titulo}_.",
           gr.Tabs(selected="leer"), "")


# --- Punto 6: diagnostico para la demo -----------------------------------

def _diagnostico():
    L = ["### Claves", "```", config.estado(), "```"]
    if config.falta():
        L.append("Sin `OPENAI_API_KEY` la app sigue funcionando: diccionario, "
                 "IPA, audio de Wiktionary, buscador y puntuación no usan red. "
                 "Lo que se apaga es la explicación contextual y la voz.")

    L.append("### Recursos")
    # Vale una carpeta local Y vale un repositorio del Hub, igual que en
    # `scoring.Puntuador`. Se corrigio alli y no aqui, asi que la pestana
    # Estado decia "FALTA" del mismo modelo que la app acababa de usar
    # para puntuar. Un diagnostico que miente es peor que no tenerlo.
    from scoring import _parece_repo_hf
    if os.path.isdir(RUTA_MODELO):
        donde = "carpeta local"
    elif _parece_repo_hf(str(RUTA_MODELO)):
        donde = "repositorio de Hugging Face"
    else:
        donde = None
    L.append(f"- Modelo v4: {donde or 'FALTA'} — `{RUTA_MODELO}`")
    from lexicon import RUTA_DICCIONARIO
    dic = Path(RUTA_DICCIONARIO)
    tam = f"{dic.stat().st_size / 1e6:.0f} MB" if dic.exists() else "FALTA"
    L.append(f"- Diccionario Kaikki: {tam}")
    # `LITERALEVEL_CUENTAS` se edita a ciegas en el panel del Space, y hasta
    # ahora una entrada mal escrita se descartaba sin que nadie lo supiera.
    # Aqui se ve el recuento; los motivos los da `cuentas.problemas()` y no
    # incluyen ninguna contrasena.
    validos, declarados = len(cuentas._tabla()), cuentas.declaradas()
    if declarados:
        L.append(f"- Perfiles: {validos} válidos de {declarados} declarados")
        for a in cuentas.problemas():
            L.append(f"  - ⚠️ {a}")
    else:
        L.append("- Perfiles: ninguno declarado, así que no hay puerta y todo "
                 "está abierto")
    try:
        L.append(f"- Catálogo: {catalogo().resumen()}")
    except Exception as e:
        L.append(f"- Catálogo: {e}")

    L.append("### Cargado en memoria")
    L.append(f"- Puntuador: {'sí' if _puntuador else 'no (se carga al usarlo)'}")
    L.append(f"- Catálogo: {'sí' if _catalogo else 'no'}")
    L.append(f"- Consultor léxico: {'sí' if _consultor else 'no'}")
    return "\n".join(L)


# --- Montaje --------------------------------------------------------------

def construir() -> gr.Blocks:
    with gr.Blocks(title="LiteraLevel") as demo:
        gr.HTML(_CSS_GLOBAL, elem_id="ll-css")
        # La paleta va en su PROPIO <style>, aparte del estructural: cambiarla
        # solo reescribe una docena de variables y no vuelve a mandar toda la
        # hoja de estilo ni puede descolocar nada.
        paleta_css = gr.HTML(_css_paleta(paletas_mod.POR_DEFECTO),
                             elem_id="ll-paleta-css")
        gr.Markdown(
            "# LiteraLevel\nLee en inglés al nivel que te toca.\n\n"
            "**1)** Fija tu nivel · **2)** busca algo que te apetezca leer · "
            "**3)** léelo aquí y consulta las palabras que se te atraganten. "
            "Las pestañas están en ese orden.")
        # Vacio a proposito: lo rellena _perfil_inicial en demo.load, que
        # si sabe de que lector se trata. Construir la interfaz ocurre una
        # vez por proceso, no una vez por visitante.
        # --- Entrar con tu perfil -------------------------------------
        # Arriba del todo y ABIERTO, no en un acordeon dentro de una pestana.
        # Tres de las funciones cuestan dinero porque llaman a un servicio
        # externo; el resto es libre. Solo aparece si esta copia tiene
        # perfiles configurados: en el ordenador de casa no hay a quien
        # limitar, y una caja pidiendo una llave que no existe solo confunde.
        if cuentas.hay_codigos():
            with gr.Accordion("Entrar con tu perfil", open=True):
                gr.Markdown(
                    "Con tu **usuario y contraseña** se activan las tres cosas "
                    "que llaman a un servicio externo: **explicar una palabra "
                    "en su frase**, **«¿de qué trata?»** y la **corrección de "
                    "pronunciación**.\n\n"
                    "Todo lo demás —medir un texto, buscar, leer el libro "
                    "entero, la curva por capítulos, el diccionario y la "
                    "fonética— **funciona sin entrar**.")
                with gr.Row():
                    caja_usuario = gr.Textbox(
                        label="Usuario", placeholder="tu usuario",
                        scale=2, autofocus=False)
                    caja_clave = gr.Textbox(
                        label="Contraseña", type="password",
                        placeholder="tu contraseña", scale=2)
                    b_entrar = gr.Button("Entrar", variant="primary", scale=1)
                    b_salir = gr.Button("Salir", scale=1)
                estado_codigo = gr.Markdown()
                b_entrar.click(_entrar, [caja_usuario, caja_clave], estado_codigo)
                caja_clave.submit(_entrar, [caja_usuario, caja_clave], estado_codigo)
                b_salir.click(_salir, None, estado_codigo)

        est_perfil = gr.State(None)
        est_libro = gr.State(None)
        # La paleta elegida. Va en un State porque el selector se construye
        # mucho mas abajo -en la pestana "Colores"- y la grafica, que la
        # necesita, se cablea antes: un State se declara aqui y se rellena
        # alli.
        est_paleta = gr.State(paletas_mod.POR_DEFECTO)

        with gr.Tabs() as pestanas:
            with gr.Tab("Mi nivel", id="nivel"):
                perfil_md = gr.Markdown(_describir(None))
                nombre = gr.Textbox(label="Tu nombre (opcional)")
                with gr.Accordion("Cuéntame cómo lees", open=True):
                    # `PREGUNTAS` trae un cuarto elemento que dice si admite
                    # varias respuestas. "Que sueles leer" es de esas: quien
                    # lee literatura clasica tambien lee menus, y marcar una
                    # sola le obliga a mentir.
                    radios = []
                    for _, pregunta, opciones, multiple in perfil_mod.PREGUNTAS:
                        elecciones = [(t, v) for t, v in opciones]
                        radios.append(
                            gr.CheckboxGroup(choices=elecciones, label=pregunta,
                                             info="Puedes marcar varias")
                            if multiple else
                            gr.Radio(choices=elecciones, label=pregunta))

                with gr.Accordion("Y ahora lee esto, con sinceridad", open=True):
                    gr.Markdown("Tres fragmentos de verdad, de menos a más "
                                "difícil. Pesan más que lo anterior: delante "
                                "de un texto real uno se juzga mejor que "
                                "describiéndose.")
                    for f in getattr(perfil_mod, "FRAGMENTOS", []):
                        # Con la tipografia del lector, para que se lea como
                        # un libro y no como un formulario.
                        gr.HTML(_html_lectura(f["texto"]))
                        gr.Markdown(f"_{f['obra']} — {f['autor']}_")
                        radios.append(gr.Radio(
                            choices=[(t, v) for t, v in f["opciones"]],
                            label=f["pregunta"]))

                b_cuest = gr.Button("Estimar mi nivel", variant="primary")
                # El resultado, tambien AQUI ABAJO. Arriba del todo se queda
                # fuera de pantalla en un movil y no te enteras de que ha
                # terminado; es la misma salida pintada dos veces.
                perfil_md_abajo = gr.Markdown()
                # Sale solo cuando ya hay nivel. Sin esto habia que subir toda
                # la pantalla a mano para llegar a las pestanas, justo despues
                # de un formulario largo: el peor momento para pedir scroll.
                b_ir_buscar = gr.Button("Ver libros para mi nivel  →",
                                        variant="primary", visible=False)
                with gr.Accordion("O mídelo con un libro que ya hayas leído",
                                  open=False):
                    gr.Markdown("Si ya leíste un libro en inglés y te resultó "
                                "cómodo, súbelo: se miden ocho partes "
                                "repartidas por toda la obra, no solo el "
                                "principio.")
                    libro_nivel = gr.File(label="Tu libro (.epub, .pdf, .txt)",
                                          file_types=[".epub", ".pdf", ".txt"],
                                          type="filepath")
                    b_libro = gr.Button("Medir con este libro", variant="primary")

                with gr.Accordion("O pega un fragmento a mano", open=False):
                    muestra = gr.Textbox(lines=8, label="Pega aquí unas 200 palabras "
                                                       "en inglés que leas sin esfuerzo")
                    b_muestra = gr.Button("Medir con este texto")
                    gr.Markdown("_La primera vez tarda: carga el modelo v4 (328 MB)._")

                salidas_nivel = [est_perfil, perfil_md, perfil_md_abajo]
                b_cuest.click(_desde_cuestionario, [est_perfil, nombre] + radios,
                              salidas_nivel)
                b_libro.click(_nivel_desde_libro, [est_perfil, nombre, libro_nivel],
                              salidas_nivel)
                b_muestra.click(_desde_muestra, [est_perfil, nombre, muestra],
                                salidas_nivel)
                est_perfil.change(lambda p: gr.update(visible=p is not None),
                                  est_perfil, b_ir_buscar)

            with gr.Tab("Buscar lectura", id="buscar"):
                with gr.Row():
                    consulta = gr.Textbox(label="¿De qué te apetece leer?", scale=4,
                                          placeholder="una novela de detectives victoriana")
                    n_res = gr.Number(value=10, label="¿Cuántos te propongo?",
                                      precision=0, minimum=1, maximum=50,
                                      scale=1,
                                      info="Cuántos libros quieres en la lista")
                ajustar = gr.Checkbox(value=True,
                                      label="Solo libros que pueda leer",
                                      info="Deja fuera lo que te quede muy "
                                           "grande o muy pequeño para tu nivel")
                # El aviso va ENCIMA del boton que provoca la espera. Debajo
                # de los resultados, en un movil, queda fuera de pantalla y se
                # lee cuando ya no sirve.
                gr.Markdown("_La primera búsqueda del día indexa los 1.197 "
                            "libros del catálogo: puede tardar cerca de un "
                            "minuto. Las siguientes son instantáneas._")
                with gr.Row():
                    b_buscar = gr.Button("Buscar", variant="primary")
                    b_recom = gr.Button("Sorpréndeme con algo de mi nivel")
                resultados = gr.Markdown()
                # Los mensajes de "Leerlo ahora" tienen que caer AQUI, en la
                # pestana donde esta el boton. Antes iban a `libro_md`, que
                # vive en la pestana de lectura: el usuario pulsaba y no veia
                # absolutamente nada, ni el error ni la espera.
                estado_abrir = gr.Markdown()
                # Lista visible, no desplegable: en un movil un dropdown
                # largo cuesta de manejar y es facil quedarse en el primero
                # sin darse cuenta de que se puede cambiar.
                elegido = gr.Radio(label="Elige cuál abrir", choices=[])
                b_abrir = gr.Button("Leerlo ahora", variant="primary")

                entradas_busq = [est_perfil, consulta, ajustar, n_res]
                b_buscar.click(_buscar, entradas_busq, [resultados, elegido])
                consulta.submit(_buscar, entradas_busq, [resultados, elegido])
                b_recom.click(_recomendar, [est_perfil, n_res], [resultados, elegido])
                # El boton vive en la pestana del cuestionario pero solo se
                # puede cablear aqui, que es donde ya existen sus salidas.
                # Salta de pestana Y trae la recomendacion hecha: llegar a un
                # buscador vacio despues de contestar seria empezar de cero.
                b_ir_buscar.click(lambda: gr.Tabs(selected="buscar"), None, pestanas
                                  ).then(_recomendar, [est_perfil, n_res],
                                         [resultados, elegido])

            with gr.Tab("Leer", id="leer"):
                with gr.Row():
                    archivo = gr.File(label="Tu libro (.epub, .pdf, .txt)",
                                      file_types=[".epub", ".pdf", ".txt"],
                                      type="filepath", scale=2)
                    libro_md = gr.Markdown()
                # Cuatro controles en una fila no caben en un movil: a 390 px
                # "Medir dificultad" se queda con unos 80 px. Se parte.
                with gr.Row():
                    b_prev = gr.Button("‹ Anterior", scale=1)
                    cap = gr.Dropdown(label="Capítulo", choices=[], scale=4)
                    b_next = gr.Button("Siguiente ›", scale=1)
                cap_md = gr.Markdown()
                # La ficha aparece sola al abrir: esta contada, es instantanea
                # y no cuesta nada. Lo de abajo son los dos botones que si
                # tardan -uno lee el libro entero con el modelo, el otro pide
                # el resumen a OpenAI- y por eso hay que pedirlos.
                with gr.Accordion("Ficha del libro", open=True):
                    ficha_md = gr.Markdown()
                    b_trata = gr.Button("¿De qué trata? (resumen)")
                    sinopsis_md = gr.Markdown()
                escala = gr.Radio(
                    choices=[("Escala LiteraLevel (0 – 2)", "cifra"),
                             ("Nivel orientativo (A1 – C2)", "cefr")],
                    value="cifra", label="Cómo quieres ver el nivel",
                    info="Salgan como salgan, se enseñan los dos: el número es "
                         "lo que mide el modelo y la letra es la etiqueta más "
                         "cercana.")
                with gr.Accordion("¿Qué significa cada nivel?", open=False):
                    gr.Markdown(_TABLA_CEFR)
                b_medir = gr.Button("¿Cómo de difícil es este capítulo?")
                # Dos botones y no uno con un desplegable: son dos decisiones
                # distintas -"echame un vistazo" y "leelo entero"- y cada una
                # dice en su etiqueta lo que cuesta.
                with gr.Row():
                    b_rapido = gr.Button("Vistazo rápido (unos segundos)")
                    b_analizar = gr.Button("Leer el libro entero (tarda más)",
                                           variant="primary")
                # El numero SALE de las constantes. Decia "unas 80" cuando
                # el producto real es 30 x 2 = 60, porque la cifra se escribio
                # a mano y luego se bajaron los capitulos de 40 a 30.
                gr.Markdown(f"_El vistazo toma unas "
                            f"{RAPIDO_CAPITULOS * RAPIDO_VENTANAS} ventanas "
                            "repartidas por "
                            "toda la obra y tarda segundos. El análisis "
                            "completo lee **todas** las ventanas del libro: en "
                            "uno largo son minutos, y queda guardado para "
                            "siempre. La curva se dibuja mientras avanza._")
                # Su propio hueco: antes la medicion pisaba la posicion del
                # capitulo y cambiar de capitulo borraba la medicion.
                medicion_md = gr.Markdown()
                analisis_md = gr.Markdown()
                # gr.Plot y no gr.BarPlot: con 366 capitulos las barras se
                # fundian en un bloque macizo. Plotly trae zoom y desplazamiento.
                grafica = gr.Plot(label="Dificultad capítulo a capítulo",
                                  show_label=True)
                # --- La palabra, ENCIMA del texto -----------------------
                # Estaba al final de la pestana, debajo del capitulo entero y
                # del indice: el lector hacia doble clic en una palabra y tenia
                # que bajar todo el capitulo para leer que significaba. En un
                # capitulo de Guerra y Paz eso son varias pantallas. Aqui la
                # caja y el resultado quedan a un palmo de donde se lee.
                with gr.Accordion("Consultar una palabra", open=True):
                    gr.Markdown(
                        "**Selecciona una palabra del texto de abajo** y se "
                        "copia aquí sola: doble clic con el ratón, o mantenla "
                        "pulsada si estás en el móvil. La oración de contexto "
                        "se busca en el capítulo abierto.")
                    with gr.Row():
                        palabra = gr.Textbox(label="Palabra", scale=3,
                                             elem_id="ll-palabra")
                        b_palabra = gr.Button("Consultar", variant="primary",
                                              scale=1)
                    ficha = gr.Markdown()
                    audio_web = gr.HTML()
                    audio_local = gr.Audio(label="Pronunciación generada",
                                           type="filepath",
                                           elem_id="ll-audio-palabra",
                                           visible=False)
                    with gr.Accordion("¿Y la oración? La busco yo sola",
                                      open=False):
                        gr.Markdown("No hace falta que copies nada: cuando "
                                    "seleccionas la palabra, busco la frase del "
                                    "capítulo donde aparece y la uso como "
                                    "contexto. Esta caja solo sirve para forzar "
                                    "otra distinta.")
                        oracion = gr.Textbox(label="Oración (opcional)")
                    idioma = gr.Radio(
                        choices=[("Explícamelo en español", "es"),
                                 ("Explain it in English", "en")],
                        value="es", label="Idioma de la explicación",
                        info="El diccionario, la IPA y el audio no cambian: "
                             "siempre vienen de Wiktionary. Esto solo afecta a "
                             "la explicación de contexto y gramática.")

                texto = gr.HTML(_html_lectura(""))

                # Los mandos, OTRA VEZ, debajo del texto. Cuando terminas un
                # capitulo estas al final de la pagina, y los de arriba quedan
                # a una pantalla entera de scroll hacia atras.
                with gr.Row():
                    b_prev2 = gr.Button("‹ Capítulo anterior")
                    b_next2 = gr.Button("Capítulo siguiente ›")
                with gr.Accordion("Índice del libro", open=False):
                    # Lista y no desplegable: en el movil se recorre con el
                    # dedo. Va dentro de un acordeon y con altura limitada
                    # porque hay libros de 366 capitulos.
                    indice = gr.Radio(label="Ir a un capítulo", choices=[],
                                      elem_id="ll-indice")

                archivo.change(_abrir, archivo, [est_libro, cap, texto, libro_md])
                archivo.change(_limpiar_consulta, None,
                               [ficha, palabra, oracion, audio_web, audio_local])
                cap.change(_capitulo, [est_libro, cap], [texto, cap_md])
                b_prev.click(lambda l, i: _mover(l, i, -1), [est_libro, cap], cap)
                b_next.click(lambda l, i: _mover(l, i, 1), [est_libro, cap], cap)
                b_medir.click(_medir, [est_libro, cap, escala], medicion_md)
                b_analizar.click(_analizar_libro,
                                 [est_libro, gr.State("completo"), escala,
                                  est_paleta],
                                 [analisis_md, grafica])
                b_rapido.click(_analizar_libro,
                               [est_libro, gr.State("rapido"), escala,
                                est_paleta],
                               [analisis_md, grafica])
                # Va colgado del State y no de `archivo`, para que la ficha
                # salga tambien cuando el libro llega del buscador y no de una
                # subida. Lo unico que los dos caminos comparten es este State.
                est_libro.change(_ficha_libro, [est_libro, est_perfil], ficha_md)
                est_libro.change(lambda: "", None, sinopsis_md)
                b_trata.click(_de_que_trata, est_libro, sinopsis_md)

                # Los mandos de abajo mueven el MISMO desplegable de arriba,
                # asi que no hay dos estados que puedan discrepar.
                b_prev2.click(lambda l, i: _mover(l, i, -1), [est_libro, cap], cap)
                b_next2.click(lambda l, i: _mover(l, i, 1), [est_libro, cap], cap)
                est_libro.change(_indice_de, [est_libro, cap], indice)
                # `.select` y no `.change`: solo dispara cuando lo toca una
                # persona. Con `.change` se hacia un bucle, porque justo abajo
                # se actualiza el indice cada vez que cambia el capitulo.
                indice.select(lambda v: v, indice, cap)
                cap.change(lambda v: gr.update(value=v), cap, indice)
                entradas_lex = [est_perfil, est_libro, cap, palabra, oracion, idioma]
                b_palabra.click(_consultar, entradas_lex,
                                [ficha, audio_web, audio_local])
                palabra.submit(_consultar, entradas_lex,
                               [ficha, audio_web, audio_local])

            with gr.Tab("Pronunciación", id="voz"):
                # La entrada al perfil ya NO vive aqui: esta arriba del todo,
                # antes de las pestanas. Estaba en un acordeon cerrado dentro
                # de esta pestana y no la encontraba nadie.

                frase = gr.Textbox(label="Frase que vas a leer en voz alta",
                                   placeholder="It is a truth universally acknowledged...")
                b_traer = gr.Button("Traer una frase del capítulo que estoy leyendo")
                mi_audio = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                    label="Léela en voz alta")
                with gr.Row():
                    b_practicar = gr.Button("Corrígeme", variant="primary")
                    b_debiles = gr.Button("Mis puntos débiles")
                palabras_html = gr.HTML()
                veredicto = gr.Markdown()
                audio_ref = gr.Audio(label="Cómo debería sonar", type="filepath",
                                 elem_id="ll-audio-ref", visible=False)

                b_traer.click(_frase_del_capitulo, [est_libro, cap], frase)
                b_practicar.click(_practicar, [mi_audio, frase],
                                  [palabras_html, veredicto, audio_ref])
                b_debiles.click(_debiles, None, veredicto)

            with gr.Tab("Mis libros", id="biblioteca"):
                gr.Markdown("Los libros que has abierto, por dónde vas en cada "
                            "uno y cuántas palabras consultaste en ellos. Se "
                            "guardan solos mientras lees.")
                b_biblio = gr.Button("Ver mis libros", variant="primary")
                biblio_html = gr.HTML()
                seguir = gr.Radio(label="Seguir leyendo", choices=[])
                b_seguir = gr.Button("Retomar donde lo dejé")
                estado_seguir = gr.Markdown()

                b_biblio.click(_mis_libros, None, [biblio_html, seguir])

            with gr.Tab("Mis palabras", id="cuaderno"):
                gr.Markdown("Se llena solo mientras lees. Cada palabra con la "
                            "frase en la que la encontraste, que es lo que "
                            "de verdad la fija.")
                with gr.Row():
                    b_cuaderno = gr.Button("Ver mis palabras", variant="primary")
                    b_repasar = gr.Button("Repasa 5")
                # gr.HTML y no gr.Markdown: hace falta el CSS que parte las
                # palabras largas, o una sola desborda la pantalla del movil.
                cuaderno_md = gr.HTML()

                b_cuaderno.click(_mis_palabras, None, cuaderno_md)
                b_repasar.click(_repasar, None, cuaderno_md)

            with gr.Tab("Colores", id="colores"):
                gr.Markdown(
                    "## Ponlo como te guste\n"
                    "Se cambia al momento y no se pierde nada de lo que "
                    "estés leyendo.")
                paleta = gr.Radio(choices=paletas_mod.opciones(),
                                  value=paletas_mod.POR_DEFECTO,
                                  label="Paleta de colores")
                paleta.change(_css_paleta, paleta, paleta_css)
                # Y la paleta tiene que llegar tambien a lo que NO es CSS: la
                # grafica es una imagen de Plotly con los colores dentro. Si ya
                # hay una curva pintada se repinta; si no, se deja como esta
                # -devolver None la borraria-.
                paleta.change(lambda c: c, paleta, est_paleta)
                paleta.change(_repintar_grafica, [est_libro, paleta], grafica)

            with gr.Tab("Estado", id="estado"):
                diag = gr.Markdown()
                gr.Button("Comprobar").click(_diagnostico, None, diag)
                demo.load(_diagnostico, None, diag)

        # Cierra el bucle buscar -> leer. Va aqui abajo y no en la pestana del
        # buscador porque necesita componentes de la pestana de lectura, que
        # se declaran despues.
        b_abrir.click(_abrir_del_catalogo, elegido,
                      [est_libro, cap, texto, libro_md, pestanas, estado_abrir])
        b_abrir.click(_limpiar_consulta, None,
                      [ficha, palabra, oracion, audio_web, audio_local])

        # Al abrir: primero de quien son los datos, luego donde se quedo.
        demo.load(_perfil_inicial, None, [est_perfil, perfil_md])
        demo.load(_reanudar, None,
                  [est_libro, cap, texto, libro_md, pestanas])

        b_seguir.click(_seguir_leyendo, seguir,
                       [est_libro, cap, texto, libro_md, pestanas, estado_seguir])
        b_seguir.click(_limpiar_consulta, None,
                       [ficha, palabra, oracion, audio_web, audio_local])

        # Engancha el doble clic del lector a la caja de consulta.
        demo.load(None, None, None, js=JS_SELECCION)

    return demo


if __name__ == "__main__":
    construir().launch(theme=TEMA, inbrowser=True,
                       allowed_paths=RUTAS_PERMITIDAS,
                       max_file_size=TAMANO_MAXIMO_SUBIDA)
