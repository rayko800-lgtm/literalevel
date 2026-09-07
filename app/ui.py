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

BASE_DATOS_LECTOR = Path(os.path.expanduser("~")) / ".literalevel"
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


_CSS_GLOBAL = f"""<style>
:root{{--ll-hielo:#8fd3e8;--ll-hielo-hondo:#1d6285;--ll-noche:#05070d}}
/* El bloque que transporta esta hoja de estilo no debe ocupar sitio; un
   <style> sigue aplicandose aunque su contenedor este oculto. */
#ll-css{{display:none}}
body,gradio-app,.gradio-container{{
  background-color:#05070d !important;
  background-image:{_estrellas()},
    radial-gradient(120% 62% at 50% 118%,rgba(60,150,190,.30) 0%,
      rgba(24,74,104,.16) 42%,transparent 72%),
    linear-gradient(180deg,#05070d 0%,#070c17 55%,#0a1522 100%) !important;
  background-attachment:fixed !important;
  background-repeat:no-repeat !important}}
h1{{
  background:linear-gradient(96deg,#eaf8ff 0%,#a8e2f4 40%,#4bb8da 100%);
  -webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;color:transparent;
  letter-spacing:-.015em;
  filter:drop-shadow(0 0 26px rgba(120,205,235,.35))}}
/* Los paneles, hielo translucido sobre el cielo, no cajas opacas. */
.block,.form,.panel,.gr-box{{
  background-color:rgba(12,22,38,.72) !important;
  border-color:rgba(143,211,232,.16) !important;
  backdrop-filter:blur(7px)}}
button.primary,.primary button{{
  background:linear-gradient(180deg,#3aa9cf,var(--ll-hielo-hondo)) !important;
  border-color:rgba(143,211,232,.45) !important;color:#f2fbff !important}}
.tab-nav button.selected{{
  color:var(--ll-hielo) !important;border-bottom-color:var(--ll-hielo) !important}}
#ll-lector{{background:rgba(8,16,28,.62);border-color:rgba(143,211,232,.20)}}
#ll-lector::selection,#ll-lector p::selection{{
  background:rgba(143,211,232,.38);color:#f4fcff}}
#ll-voz{{background:rgba(8,16,28,.62);border-color:rgba(143,211,232,.20)}}
footer{{opacity:.45}}
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


def _desde_cuestionario(p_actual, nombre, *valores, peticion: gr.Request = None):
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
    try:
        libros, aviso = cat.buscar(consulta, nivel_lector=nivel, n=int(n))
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
    except (ValueError, ConnectionError) as e:
        yield quieto[:3] + (gr.update(), gr.Tabs(), _aviso(e))
        return
    libro, upd, html, resumen = _abrir(ruta, peticion)
    if libro is None:
        yield None, vacio, _html_lectura(""), resumen, gr.Tabs(), _aviso(resumen)
        return
    yield libro, upd, html, resumen, gr.Tabs(selected="leer"), ""


def _recomendar(p, n):
    vacio = gr.update(choices=[], value=None)
    if p is None:
        return "Primero fija tu nivel en la pestaña **Mi nivel**.", vacio
    try:
        libros = catalogo().por_nivel(p.nivel, n=int(n))
    except Exception as e:
        return _aviso(e), vacio
    lo, hi = p.rango_recomendado
    # Los niveles del catalogo son seis valores discretos, asi que un lector
    # que salga del cuestionario en 0.62 puede no tener NINGUN libro dentro de
    # la holgura. Decirlo y decir que hacer, en vez del generico "Sin
    # resultados" que dejaba en un callejon.
    si_no_hay = (f"No hay libros etiquetados entre {lo:.2f} y {hi:.2f}. Prueba "
                 f"a describir lo que te apetece leer en el buscador de "
                 f"arriba: ahí sí se ajusta a tu nivel sin exigir una "
                 f"coincidencia exacta.")
    return (f"Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:\n\n"
            + _tabla_libros(libros, si_no_hay), _opciones_libros(libros))


# --- Punto 3: lector, y punto 4 dentro de el ------------------------------

_CSS_LECTOR = """<style>
#ll-lector{max-height:62vh;overflow-y:auto;padding:1.4rem 1.8rem;
  border:1px solid rgba(128,128,128,.28);border-radius:10px;
  font-family:Georgia,"Iowan Old Style","Times New Roman",serif;
  font-size:19px;line-height:1.75;color:inherit;text-align:justify;
  hyphens:auto;-webkit-hyphens:auto}
#ll-lector p{margin:0 0 1.05em}
#ll-lector p:first-child{margin-top:0}
#ll-lector::selection,#ll-lector p::selection{background:rgba(255,205,0,.45)}
#ll-lector .ll-vacio{font-style:italic;opacity:.7;text-align:left}
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
    // En un movil la caja queda fuera de pantalla, debajo del lector: sin
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
    return gr.update(value=max(0, min(len(libro.capitulos) - 1, int(idx) + paso)))


# Titulos que en un epub casi siempre son paratexto y no la obra en si.
_RELLENO_RE = re.compile(
    r"^\s*(also translated|a note about|about the (author|translator)|"
    r"appendix|foreword|preface|introduction|contents|index|notes?\s*$|"
    r"acknowledg|copyright|dedication|title page|borzoi|colophon|"
    r"further reading|bibliograph|glossar)", re.IGNORECASE)


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


def _medir(libro, idx):
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
        r = puntuador().puntuar(c.texto)
    except (ValueError, FileNotFoundError) as e:
        yield _aviso(e)
        return
    yield (f"**{r.puntuacion:.2f} / 2.00** ({r.banda}) · orientativo "
           f"**{r.nivel_orientativo}** · {r.n_bloques} bloques · "
           f"confianza {r.confianza}")


RUTA_ANALISIS = BASE_DATOS_LECTOR / "analisis"


def _clave_libro(libro) -> str:
    """Identifica un libro por su contenido, no por el nombre del archivo."""
    import hashlib
    h = hashlib.sha256(f"{libro.titulo}\x1f{libro.palabras}".encode("utf-8"))
    for c in libro.capitulos[:40]:
        h.update(f"{c.titulo}\x1f{c.palabras}".encode("utf-8"))
    return h.hexdigest()[:20]


def _analisis_guardado(libro):
    try:
        ruta = RUTA_ANALISIS / f"{_clave_libro(libro)}.json"
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _guardar_analisis(libro, datos) -> None:
    try:
        RUTA_ANALISIS.mkdir(parents=True, exist_ok=True)
        (RUTA_ANALISIS / f"{_clave_libro(libro)}.json").write_text(
            json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass          # el analisis es util, no imprescindible


def _analizar_libro(libro, peticion: gr.Request = None):
    """Perfil de dificultad del libro ENTERO, capitulo a capitulo.

    Aqui no se muestrea: cada capitulo se recorre ventana a ventana con el
    modelo v4. Es la respuesta a "¿de verdad lo lee todo?" -si, para esto lo
    lee todo- y es lo que permite ver que un libro empieza duro y se ablanda,
    o al reves. Tarda, asi que se guarda en disco y solo se calcula una vez
    por libro.

    Es generadora: va diciendo por donde va, porque en un libro largo esto
    son minutos y una pantalla quieta parece una pantalla rota.
    """
    if libro is None or not libro.capitulos:
        yield "Abre un libro primero, en esta misma pestaña.", None
        return

    datos = _analisis_guardado(libro)
    if datos is None:
        cuerpo = [(i, c) for i, c in enumerate(libro.capitulos)
                  if c.palabras >= 150 and not _RELLENO_RE.search(c.titulo)]
        if not cuerpo:
            yield ("Este libro no tiene capítulos con prosa suficiente para "
                   "analizarlos."), None
            return
        try:
            p = puntuador()
        except (FileNotFoundError, OSError) as e:
            yield _aviso(e), None
            return
        filas, ventanas = [], 0
        for n, (i, c) in enumerate(cuerpo, 1):
            yield (f"Leyendo el libro entero con el modelo v4: capítulo "
                   f"**{n} de {len(cuerpo)}**… Esto se calcula una sola vez y "
                   f"luego queda guardado."), None
            vs = p.perfil_de_texto(c.texto)
            if not vs:
                continue
            ventanas += len(vs)
            filas.append({"capitulo": n, "titulo": c.titulo[:40],
                          "indice": i, "dificultad": round(sum(vs) / len(vs), 3),
                          "min": round(min(vs), 3), "max": round(max(vs), 3),
                          "ventanas": len(vs), "palabras": c.palabras})
        if not filas:
            yield "No pude medir ningún capítulo de este libro.", None
            return
        datos = {"titulo": libro.titulo, "autor": libro.autor,
                 "palabras": libro.palabras, "ventanas": ventanas, "filas": filas}
        _guardar_analisis(libro, datos)

    yield _resumen_analisis(datos), _grafica_analisis(datos)


def _grafica_analisis(datos):
    import pandas as pd
    return pd.DataFrame([{"Capítulo": f["capitulo"], "Dificultad": f["dificultad"]}
                         for f in datos["filas"]])


def _resumen_analisis(datos) -> str:
    filas = datos["filas"]
    medias = [f["dificultad"] for f in filas]
    global_ = sum(medias) / len(medias)
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
    return (
        f"### {datos['titulo']}" + (f" — {datos['autor']}" if datos["autor"] else "")
        + f"\n\n**{global_:.2f} / 2.00** de media ({scoring.public_band(global_)}), "
          f"medido leyendo **{datos['ventanas']} ventanas** de 250 palabras "
          f"sobre {datos['palabras']:,} en total. Aquí no se muestrea: el "
          f"modelo recorre cada capítulo entero.\n\n"
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

    if not _dentro_del_limite(peticion, "lexico", LIMITE_CONSULTAS_HORA):
        yield _aviso(_mensaje_limite(idioma, 60)), "", gr.update(visible=False)
        return

    nivel = p.nivel if p is not None else NIVEL_POR_DEFECTO
    try:
        r = consultor().consultar(palabra, oracion, nivel, idioma=idioma)
    except (FileNotFoundError, OSError) as e:
        yield _aviso(e), "", gr.update(visible=False)
        return
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
#ll-voz{padding:1.1rem 1.3rem;border:1px solid rgba(128,128,128,.28);
  border-radius:10px;font-family:Georgia,"Times New Roman",serif;
  font-size:21px;line-height:2.1;color:inherit}
#ll-voz .ll-w{padding:.12em .34em;border-radius:5px;margin:0 .06em;
  border-bottom:3px solid transparent}
#ll-voz .ok{border-bottom-color:#3fbf8f}
#ll-voz .mal{background:rgba(224,72,92,.22);border-bottom-color:#e0485c;
  font-weight:600}
#ll-voz .leyenda{display:block;margin-top:1rem;font-family:system-ui,sans-serif;
  font-size:13px;opacity:.75;line-height:1.5}
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
        return "", _aviso(_mensaje_limite("es", 60)), gr.update(visible=False)
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
#ll-cuaderno .ll-c{padding:.75rem .9rem;border:1px solid rgba(143,211,232,.20);
  border-radius:9px;background:rgba(8,16,28,.55)}
/* Sin esto, una palabra larguisima o una URL desbordan la pantalla del movil
   y la pestana entera se convierte en un muro ilegible. */
#ll-cuaderno .ll-c *{overflow-wrap:anywhere;word-break:break-word}
#ll-cuaderno .ll-p{font-weight:700;font-size:1.05rem}
#ll-cuaderno .ll-d{opacity:.62;font-size:.82rem;font-weight:400}
#ll-cuaderno .ll-f{margin:.4rem 0 .3rem;padding-left:.7rem;
  border-left:3px solid rgba(143,211,232,.45);
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
#ll-biblio .ll-l{padding:.8rem .95rem;border:1px solid rgba(143,211,232,.20);
  border-radius:9px;background:rgba(8,16,28,.55)}
#ll-biblio .ll-l *{overflow-wrap:anywhere}
#ll-biblio .ll-t{font-weight:700;font-size:1.05rem}
#ll-biblio .ll-a{opacity:.65;font-size:.85rem}
#ll-biblio .ll-b{height:7px;border-radius:4px;margin:.5rem 0 .35rem;
  background:rgba(143,211,232,.16);overflow:hidden}
#ll-biblio .ll-b i{display:block;height:100%;
  background:linear-gradient(90deg,#3aa9cf,#8fd3e8)}
#ll-biblio .ll-n{font-size:.85rem;opacity:.8}
#ll-biblio .ll-x{font-size:.82rem;opacity:.6;font-style:italic}
</style>"""


def _mis_libros(peticion: gr.Request = None):
    """La estanteria: que se esta leyendo, por donde y cuanto se ha consultado."""
    libros = biblioteca.listar(_archivo_lector("biblioteca.json", peticion))
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
        perdido = ("" if e.existe else
                   '<div class="ll-x">El archivo ya no está en su sitio: '
                   'vuelve a abrirlo para seguir.</div>')
        tarjetas.append(
            f'<div class="ll-l"><div class="ll-t">'
            f'{_html.escape(_recortar(e.titulo, 60))}</div>'
            f'<div class="ll-a">{_html.escape(_recortar(e.autor or "autor desconocido", 50))}</div>'
            f'<div class="ll-b"><i style="width:{pct}%"></i></div>'
            f'<div class="ll-n">{_html.escape(nota)}</div>{perdido}</div>')
        if e.existe:
            opciones.append((f"{e.titulo} — cap. {e.capitulo + 1} de {e.capitulos}",
                             e.ruta))
    return (_CSS_BIBLIO + '<div id="ll-biblio">' + "".join(tarjetas) + "</div>",
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
    modelo_ok = os.path.isdir(RUTA_MODELO)
    L.append(f"- Modelo v4: {'encontrado' if modelo_ok else 'FALTA'} — `{RUTA_MODELO}`")
    from lexicon import RUTA_DICCIONARIO
    dic = Path(RUTA_DICCIONARIO)
    tam = f"{dic.stat().st_size / 1e6:.0f} MB" if dic.exists() else "FALTA"
    L.append(f"- Diccionario Kaikki: {tam}")
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
        gr.Markdown(
            "# LiteraLevel\nLee en inglés al nivel que te toca.\n\n"
            "**1)** Fija tu nivel · **2)** busca algo que te apetezca leer · "
            "**3)** léelo aquí y consulta las palabras que se te atraganten. "
            "Las pestañas están en ese orden.")
        # Vacio a proposito: lo rellena _perfil_inicial en demo.load, que
        # si sabe de que lector se trata. Construir la interfaz ocurre una
        # vez por proceso, no una vez por visitante.
        est_perfil = gr.State(None)
        est_libro = gr.State(None)

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

            with gr.Tab("Buscar lectura", id="buscar"):
                with gr.Row():
                    consulta = gr.Textbox(label="¿Qué te apetece leer?", scale=4,
                                          placeholder="una novela de detectives victoriana")
                    n_res = gr.Number(value=10, label="Resultados", precision=0,
                                      minimum=1, maximum=50, scale=1)
                ajustar = gr.Checkbox(value=True, label="Ajustar a mi nivel")
                # El aviso va ENCIMA del boton que provoca la espera. Debajo
                # de los resultados, en un movil, queda fuera de pantalla y se
                # lee cuando ya no sirve.
                gr.Markdown("_La primera búsqueda del día indexa los 1.197 "
                            "libros del catálogo: puede tardar cerca de un "
                            "minuto. Las siguientes son instantáneas._")
                with gr.Row():
                    b_buscar = gr.Button("Buscar", variant="primary")
                    b_recom = gr.Button("Recomiéndame por nivel")
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
                b_medir = gr.Button("Medir la dificultad de este capítulo")
                b_analizar = gr.Button("Analizar el libro entero")
                # Su propio hueco: antes la medicion pisaba la posicion del
                # capitulo y cambiar de capitulo borraba la medicion.
                medicion_md = gr.Markdown()
                analisis_md = gr.Markdown()
                grafica = gr.BarPlot(x="Capítulo", y="Dificultad", height=260,
                                     y_lim=[0, 2], title="Dificultad capítulo a capítulo")
                texto = gr.HTML(_html_lectura(""))

                gr.Markdown("### Consultar una palabra\n"
                            "**Selecciona una palabra del texto** y se copia aquí "
                            "sola: doble clic con el ratón, o mantenla pulsada "
                            "si estás en el móvil. La oración de contexto se "
                            "busca en el capítulo abierto.")
                with gr.Row():
                    palabra = gr.Textbox(label="Palabra", scale=3,
                                         elem_id="ll-palabra")
                    b_palabra = gr.Button("Consultar", variant="primary", scale=1)
                with gr.Accordion("¿Y la oración? La busco yo sola", open=False):
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
                    info="El diccionario, la IPA y el audio no cambian: siempre "
                         "vienen de Wiktionary. Esto solo afecta a la explicación "
                         "de contexto y gramática.")
                ficha = gr.Markdown()
                audio_web = gr.HTML()
                audio_local = gr.Audio(label="Pronunciación generada",
                                   type="filepath", elem_id="ll-audio-palabra",
                                   visible=False)

                archivo.change(_abrir, archivo, [est_libro, cap, texto, libro_md])
                archivo.change(_limpiar_consulta, None,
                               [ficha, palabra, oracion, audio_web, audio_local])
                cap.change(_capitulo, [est_libro, cap], [texto, cap_md])
                b_prev.click(lambda l, i: _mover(l, i, -1), [est_libro, cap], cap)
                b_next.click(lambda l, i: _mover(l, i, 1), [est_libro, cap], cap)
                b_medir.click(_medir, [est_libro, cap], medicion_md)
                b_analizar.click(_analizar_libro, est_libro,
                                 [analisis_md, grafica])
                entradas_lex = [est_perfil, est_libro, cap, palabra, oracion, idioma]
                b_palabra.click(_consultar, entradas_lex,
                                [ficha, audio_web, audio_local])
                palabra.submit(_consultar, entradas_lex,
                               [ficha, audio_web, audio_local])

            with gr.Tab("Pronunciación", id="voz"):
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
