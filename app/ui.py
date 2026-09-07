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


def _desde_cuestionario(p_actual, nombre, *valores, peticion: gr.Request = None):
    claves = [c for c, _, _ in perfil_mod.PREGUNTAS]
    respuestas = {k: v for k, v in zip(claves, valores) if v is not None}
    try:
        p = perfil_mod.desde_cuestionario(respuestas, nombre=nombre or "")
        p.guardar(_archivo_lector("perfil.json", peticion))
    except (ValueError, OSError) as e:
        # Se conserva el perfil anterior: un fallo al estimar no debe borrarlo.
        return p_actual, _aviso(e)
    return p, _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas."


def _desde_muestra(p_actual, nombre, texto, peticion: gr.Request = None):
    if not (texto or "").strip():
        return p_actual, "Pega un fragmento que leas sin dificultad."
    try:
        p = perfil_mod.desde_muestra(texto, puntuador(), nombre=nombre or "")
        p.guardar(_archivo_lector("perfil.json", peticion))
    except (ValueError, FileNotFoundError, OSError) as e:
        return p_actual, _aviso(e)
    return p, _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas."


# --- Punto 2: buscador del catalogo --------------------------------------

def _tabla_libros(libros, aviso: str = "") -> str:
    if not libros:
        return _aviso(aviso or "Sin resultados.")
    filas = ["| Libro | Autor | Nivel | De qué va |", "|---|---|---|---|"]
    for b in libros:
        enlace = f"[{b.titulo}]({b.url_gutenberg})" if b.url_gutenberg else b.titulo
        gancho = (b.gancho or "").replace("\n", " ").replace("|", "/")
        if len(gancho) > 110:
            gancho = gancho[:107] + "..."
        filas.append(f"| {enlace} | {b.autor} | {b.nivel} | {gancho} |")
    if aviso:
        filas.append("")
        filas.append(f"_{aviso}_")
    return "\n".join(filas)


def _opciones_libros(libros):
    """Los resultados, listos para abrirse en el lector con un clic.

    Los de StoryWeaver se listan igual pero marcados: no estan en Gutenberg y
    no hay de donde bajarlos. Mas vale decirlo en la etiqueta que dejar que el
    usuario lo descubra al pulsar.
    """
    opciones = []
    for b in libros:
        etiqueta = f"{b.titulo} — {b.autor} ({b.nivel})"
        if not str(b.id).upper().startswith("PG"):
            etiqueta += "  · no descargable"
        opciones.append((etiqueta, b.id))
    # Preseleccionar uno que se pueda abrir: dejar arriba un "no descargable"
    # es ofrecer un boton que solo sabe dar una disculpa.
    abrible = next((v for _, v in opciones if str(v).upper().startswith("PG")), None)
    inicial = abrible or (opciones[0][1] if opciones else None)
    return gr.update(choices=opciones, value=inicial)


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
    """Abre en el lector un libro elegido en el buscador, sin salir de la app."""
    vacio = gr.update(choices=[], value=None)
    if not id_libro:
        return (None, vacio, _html_lectura(""),
                "Elige un libro de los resultados.", gr.Tabs())
    try:
        ruta = _descargar_gutenberg(id_libro)
    except (ValueError, ConnectionError) as e:
        return None, vacio, _html_lectura(""), _aviso(e), gr.Tabs()
    libro, upd, html, resumen = _abrir(ruta, peticion)
    # Solo se salta a la pestana de lectura si de verdad hay algo que leer.
    destino = gr.Tabs(selected="leer") if libro is not None else gr.Tabs()
    return libro, upd, html, resumen, destino


def _recomendar(p, n):
    vacio = gr.update(choices=[], value=None)
    if p is None:
        return "Primero fija tu nivel en la pestaña **Mi nivel**.", vacio
    try:
        libros = catalogo().por_nivel(p.nivel, n=int(n))
    except Exception as e:
        return _aviso(e), vacio
    lo, hi = p.rango_recomendado
    return (f"Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:\n\n"
            + _tabla_libros(libros), _opciones_libros(libros))


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
  document.addEventListener('mouseup', () => {
    const sel = window.getSelection();
    const txt = (sel.toString() || '').trim();
    if (!txt || txt.split(/\s+/).length > 4) return;
    if (!sel.anchorNode) return;
    const nodo = sel.anchorNode.nodeType === 1 ? sel.anchorNode
                                               : sel.anchorNode.parentElement;
    if (!nodo || !nodo.closest('#ll-lector')) return;
    const caja = document.querySelector('#ll-palabra textarea, #ll-palabra input');
    if (!caja) return;
    caja.value = txt;
    caja.dispatchEvent(new Event('input', { bubbles: true }));
  });
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
    return (_html_lectura(c.texto),
            f"**{c.titulo}** · {c.palabras:,} palabras · "
            f"capítulo {int(idx) + 1} de {len(libro.capitulos)}")


def _medir(libro, idx):
    c = _cap(libro, idx)
    if c is None:
        return "Abre un libro y elige un capítulo."
    try:
        r = puntuador().puntuar(c.texto)
    except (ValueError, FileNotFoundError) as e:
        return _aviso(e)
    return (f"**{r.puntuacion:.2f} / 2.00** ({r.banda}) · orientativo "
            f"**{r.nivel_orientativo}** · {r.n_bloques} bloques · "
            f"confianza {r.confianza}")


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
        yield "Escribe la palabra que quieres consultar.", "", None
        return
    if len(palabra.split()) > 4:
        yield ("Consulta una palabra (o un phrasal verb corto), no una frase.",
               "", None)
        return
    if len(palabra) > LIMITE_PALABRA:
        yield ({"es": f"Eso son {len(palabra)} caracteres seguidos: ninguna "
                      f"palabra inglesa pasa de {LIMITE_PALABRA}. Selecciona "
                      f"una palabra del texto y vuelve a intentarlo.",
                "en": f"That is {len(palabra)} characters in a row: no English "
                      f"word goes past {LIMITE_PALABRA}. Pick a word from the "
                      f"text and try again."}[idioma if idioma == "en" else "es"],
               "", None)
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
        yield _aviso(_mensaje_limite(idioma, 60)), "", None
        return

    nivel = p.nivel if p is not None else NIVEL_POR_DEFECTO
    try:
        r = consultor().consultar(palabra, oracion, nivel, idioma=idioma)
    except (FileNotFoundError, OSError) as e:
        yield _aviso(e), "", None
        return
    # Al cuaderno, con su frase y su libro: es el unico rastro que queda de
    # una sesion de lectura. Si no se puede escribir, no pasa nada.
    cuaderno.registrar(
        palabra=r.palabra_superficie, lema=r.lema_buscado or r.lema,
        oracion=oracion, categoria=r.categoria, sentido=r.sentido,
        libro=(libro.titulo if libro is not None else None),
        capitulo=(int(idx) + 1 if _cap(libro, idx) is not None else None),
        banda=r.banda_lector, zipf=r.frecuencia_zipf,
        ruta=_archivo_lector("cuaderno.db", peticion))

    contexto = "Contexto" if idioma == "es" else "Context"
    ficha = _ficha(r, idioma) + f"\n\n> {oracion}\n\n_{contexto}: {origen}._"
    yield ficha, _reproductores(r), _local(r.audio_us) or _local(r.audio_uk)


def _frase_del_capitulo(libro, idx):
    """Manda la primera oracion de largo razonable a la practica de voz."""
    if libro is None or idx is None:
        return ""
    c = _cap(libro, idx)
    if c is None:
        return ""
    # Por parrafos, no por el capitulo entero: los encabezados ("I", "The Dead
    # House") no llevan punto, asi que la primera "oracion" del texto crudo se
    # los traga enteros y sale una frase absurda para leer en voz alta.
    for parrafo in re.split(r"\n\s*\n", c.texto):
        limpio = " ".join(parrafo.split())
        if len(limpio.split()) < 30:      # titulillo o linea suelta
            continue
        for frase in scoring.SENT_RE.findall(limpio):
            f = " ".join(frase.split())
            if 6 <= len(f.split()) <= 25:
                return f
    return ""


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
        return "", "Escribe la frase que vas a leer en voz alta.", None
    if not ruta_audio:
        return "", "Graba tu voz con el micrófono (o sube un audio).", None
    if not _dentro_del_limite(peticion, "voz", LIMITE_VOZ_HORA):
        return "", _aviso(_mensaje_limite("es", 60)), None
    try:
        # Los fallos se registran aparte, en la base de ESTE lector: las
        # palabras que a uno se le atragantan no son asunto de los demas.
        s = voz.practicar(ruta_audio, frase, guardar_fallos=False)
        if s.evaluacion.palabras_falladas and s.transcripcion_ok:
            voz.registrar_fallos(s.evaluacion.palabras_falladas,
                                 ruta=_archivo_lector("voz.db", peticion))
    except Exception as e:
        return "", _aviso(e), None

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
    return (_palabras_html(ev, s.transcripcion_ok),
            "\n\n".join(L), s.audio_correcto)


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

def _mis_palabras(peticion: gr.Request = None):
    db = _archivo_lector("cuaderno.db", peticion)
    total, lemas, libros = cuaderno.contar(db)
    if not total:
        return ("Todavía no has consultado ninguna palabra.\n\n"
                "Abre un libro en **Leer**, haz doble clic en una palabra que "
                "no conozcas y aparecerá aquí, con la frase en la que la "
                "encontraste.")
    L = [f"**{lemas}** palabras distintas, en **{total}** consultas "
         f"sobre **{libros}** libro{'s' if libros != 1 else ''}.", ""]
    for a in cuaderno.ultimas(20, db):
        donde = f" · {a.libro}" if a.libro else ""
        if a.libro and a.capitulo:
            donde += f", cap. {a.capitulo}"
        rareza = f" · {a.rareza}" if a.rareza else ""
        L.append(f"**{a.palabra}**{rareza}{donde}")
        L.append(f"> {a.oracion}")
        if a.sentido:
            L.append(f"_{a.sentido}_")
        L.append("")
    return "\n\n".join(L)


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
        return ("No hay nada que repasar todavía. Consulta alguna palabra "
                "mientras lees, o practica una frase en voz alta.")
    L = []
    if anotaciones:
        L.append("### Del cuaderno")
        for a in anotaciones:
            L.append(f"**{a.palabra}** — ¿la recuerdas?")
            L.append(f"> {a.oracion}")
            if a.sentido:
                L.append(f"<details><summary>Ver el sentido</summary>\n\n"
                         f"{a.sentido}\n\n</details>")
    if debiles:
        L.append("### De la práctica en voz alta")
        L.append(", ".join(f"**{w}** ({n})" for w, n in debiles))
    return "\n\n".join(L)


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
        gr.Markdown("# LiteraLevel\nLee en inglés al nivel que te toca.")
        # Vacio a proposito: lo rellena _perfil_inicial en demo.load, que
        # si sabe de que lector se trata. Construir la interfaz ocurre una
        # vez por proceso, no una vez por visitante.
        est_perfil = gr.State(None)
        est_libro = gr.State(None)

        with gr.Tabs() as pestanas:
            with gr.Tab("Mi nivel", id="nivel"):
                perfil_md = gr.Markdown(_describir(None))
                nombre = gr.Textbox(label="Tu nombre (opcional)")
                with gr.Accordion("Cuestionario rápido", open=True):
                    radios = [
                        gr.Radio(choices=[(t, v) for t, v in opciones], label=pregunta)
                        for _, pregunta, opciones in perfil_mod.PREGUNTAS
                    ]
                    b_cuest = gr.Button("Estimar mi nivel", variant="primary")
                with gr.Accordion("O mídelo con un texto que leas cómodo", open=False):
                    muestra = gr.Textbox(lines=8, label="Pega aquí unas 200 palabras "
                                                       "en inglés que leas sin esfuerzo")
                    b_muestra = gr.Button("Medir con este texto")
                    gr.Markdown("_La primera vez tarda: carga el modelo v4 (328 MB)._")

                b_cuest.click(_desde_cuestionario, [est_perfil, nombre] + radios,
                              [est_perfil, perfil_md])
                b_muestra.click(_desde_muestra, [est_perfil, nombre, muestra],
                                [est_perfil, perfil_md])

            with gr.Tab("Buscar lectura", id="buscar"):
                with gr.Row():
                    consulta = gr.Textbox(label="¿Qué te apetece leer?", scale=4,
                                          placeholder="una novela de detectives victoriana")
                    n_res = gr.Number(value=10, label="Resultados", precision=0,
                                      minimum=1, maximum=50, scale=1)
                ajustar = gr.Checkbox(value=True, label="Ajustar a mi nivel")
                with gr.Row():
                    b_buscar = gr.Button("Buscar", variant="primary")
                    b_recom = gr.Button("Recomiéndame por nivel")
                resultados = gr.Markdown()
                with gr.Row():
                    elegido = gr.Dropdown(label="Ábrelo aquí mismo", choices=[],
                                          scale=4)
                    b_abrir = gr.Button("Leerlo ahora", variant="primary", scale=1)
                gr.Markdown("_La primera búsqueda indexa el catálogo; luego va "
                            "sola. Los libros de Gutenberg se descargan una vez "
                            "y se quedan guardados._")

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
                with gr.Row():
                    b_prev = gr.Button("‹ Anterior", scale=1)
                    cap = gr.Dropdown(label="Capítulo", choices=[], scale=5)
                    b_next = gr.Button("Siguiente ›", scale=1)
                    b_medir = gr.Button("Medir dificultad", scale=2)
                cap_md = gr.Markdown()
                texto = gr.HTML(_html_lectura(""))

                gr.Markdown("### Consultar una palabra\n"
                            "**Haz doble clic en una palabra del texto** y se copia "
                            "aquí sola. La oración de contexto se busca en el "
                            "capítulo abierto.")
                with gr.Row():
                    palabra = gr.Textbox(label="Palabra", scale=2, elem_id="ll-palabra")
                    oracion = gr.Textbox(label="Oración (opcional, si quieres forzarla)",
                                         scale=4)
                    b_palabra = gr.Button("Consultar", variant="primary", scale=1)
                idioma = gr.Radio(
                    choices=[("Explícamelo en español", "es"),
                             ("Explain it in English", "en")],
                    value="es", label="Idioma de la explicación",
                    info="El diccionario, la IPA y el audio no cambian: siempre "
                         "vienen de Wiktionary. Esto solo afecta a la explicación "
                         "de contexto y gramática.")
                ficha = gr.Markdown()
                audio_web = gr.HTML()
                audio_local = gr.Audio(label="Pronunciación generada", type="filepath")

                archivo.change(_abrir, archivo, [est_libro, cap, texto, libro_md])
                cap.change(_capitulo, [est_libro, cap], [texto, cap_md])
                b_prev.click(lambda l, i: _mover(l, i, -1), [est_libro, cap], cap)
                b_next.click(lambda l, i: _mover(l, i, 1), [est_libro, cap], cap)
                b_medir.click(_medir, [est_libro, cap], cap_md)
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
                audio_ref = gr.Audio(label="Cómo debería sonar", type="filepath")

                b_traer.click(_frase_del_capitulo, [est_libro, cap], frase)
                b_practicar.click(_practicar, [mi_audio, frase],
                                  [palabras_html, veredicto, audio_ref])
                b_debiles.click(_debiles, None, veredicto)

            with gr.Tab("Mis palabras", id="cuaderno"):
                gr.Markdown("Se llena solo mientras lees. Cada palabra con la "
                            "frase en la que la encontraste, que es lo que "
                            "de verdad la fija.")
                with gr.Row():
                    b_cuaderno = gr.Button("Ver mis palabras", variant="primary")
                    b_repasar = gr.Button("Repasa 5")
                cuaderno_md = gr.Markdown()

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
                      [est_libro, cap, texto, libro_md, pestanas])

        # Al abrir: primero de quien son los datos, luego donde se quedo.
        demo.load(_perfil_inicial, None, [est_perfil, perfil_md])
        demo.load(_reanudar, None,
                  [est_libro, cap, texto, libro_md, pestanas])

        # Engancha el doble clic del lector a la caja de consulta.
        demo.load(None, None, None, js=JS_SELECCION)

    return demo


if __name__ == "__main__":
    construir().launch(theme=TEMA, inbrowser=True,
                       allowed_paths=RUTAS_PERMITIDAS,
                       max_file_size=TAMANO_MAXIMO_SUBIDA)
