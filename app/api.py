"""API HTTP de LiteraLevel para el cliente Angular (`front/`).

Separa la interfaz del motor: Angular se sirve como estaticos y habla con esto
por HTTP. **No reimplementa ninguna regla de `ui.py`: la importa.** Las puertas
de pago, los topes por hora, la carpeta de datos de cada lector, la descarga de
Gutenberg y los analisis guardados son los de `ui.py`, que llevan diecisiete
auditorias encima. Si esta API copiara esa logica, la primera correccion que se
hiciera en `ui.py` dejaria aqui un agujero abierto sin que nadie lo viera.

Lo que si es propio de la API:

- **La identidad del lector viaja en la cabecera `X-Lector`**, un id aleatorio
  que genera el navegador y guarda en `localStorage`. Hace el papel del
  `session_hash` de Gradio: `_Lector` se lo presta a las funciones de `ui` con
  la misma forma que un `gr.Request`. Sigue sin ser autenticacion, igual que en
  Gradio; lo que cuesta dinero va detras de usuario y contrasena.
- **Las respuestas son datos, no Markdown.** La escala es la publica 0..2 en
  todas: la interna 0..5 no sale de `scoring.py`.
- **Lo lento no bloquea una peticion.** La curva de un libro entero son minutos:
  se lanza como trabajo y se consulta su avance.

Nunca devuelve una traza: un error inesperado sale como 500 con una frase, y el
detalle va al registro.

Arranque local, con Gradio montado en `/` y la API en `/api`:

    python -X utf8 app/api.py

Solo la API (lo que usa el proxy de `ng serve`):

    python -X utf8 -m uvicorn app.api:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import contextlib
import functools
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import threading
import time
import traceback
import unicodedata
import uuid
from collections import OrderedDict
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Literal

APP_DIR = Path(__file__).resolve().parent
RAIZ = APP_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from fastapi import Depends, FastAPI, HTTPException, Query, Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse, Response  # noqa: E402
from starlette.concurrency import run_in_threadpool  # noqa: E402
from starlette.formparsers import MultiPartParser  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

import animacion_articulatoria  # noqa: E402
import audiolibro  # noqa: E402
import articulacion  # noqa: E402
import biblioteca  # noqa: E402
import catalogo  # noqa: E402
import config  # noqa: E402
import cuaderno  # noqa: E402
import cuentas  # noqa: E402
import eos  # noqa: E402
import ficha  # noqa: E402
import fonemas  # noqa: E402
import perfil as perfil_mod  # noqa: E402
import reader  # noqa: E402
import scoring  # noqa: E402
import ui  # noqa: E402
import voz  # noqa: E402

VERSION = "0.2.0"

app = FastAPI(
    title="LiteraLevel API",
    version=VERSION,
    description="El motor de LiteraLevel para el cliente Angular. Escala publica 0..2.",
)

# El front vive en otro origen: `ng serve` en local, un Space estatico y, desde
# el 26 sep, Vercel (`pleyade-app.vercel.app`; `pleyade.vercel.app` ya era de
# otro, y Vercel dio tambien `pleyade-phi`). Solo esos dominios exactos. Sin credenciales -la identidad va en una cabecera propia, no en
# una cookie-, asi que un origen de mas no abre la puerta a leer datos ajenos.
_ORIGENES = [o.strip() for o in os.environ.get("LITERALEVEL_ORIGENES", "").split(",")
             if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGENES,
    allow_origin_regex=(r"^(https://[a-z0-9-]+\.(static\.)?hf\.space"
                        r"|https://pleyade-(app|phi)\.vercel\.app"
                        r"|http://(localhost|127\.0\.0\.1)(:\d+)?)$"),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-Lector"],
)


@app.exception_handler(Exception)
async def _error_inesperado(request: Request, exc: Exception):
    """La regla de toda la app: nunca una traza en la cara del lector."""
    print(f"api {request.method} {request.url.path}: {type(exc).__name__}: {exc}",
          file=sys.stderr)
    traceback.print_exc(limit=4, file=sys.stderr)
    return JSONResponse(status_code=500, content={
        "detail": "Algo ha fallado en el servidor. Vuelve a intentarlo en un momento."})


@app.exception_handler(RequestValidationError)
async def _validacion_sin_eco(request: Request, exc: RequestValidationError):
    """El 422 de FastAPI devolvía en `input` lo que llegó: en /api/entrar, la
    contraseña (ronda 2 de e6, verificado en el Space el 15 sep 2026). Solo dónde,
    qué y de qué tipo; `ctx` tampoco, que puede llevar valores."""
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(e.get("loc", ())), "msg": str(e.get("msg", "")), "type": str(e.get("type", ""))}
        for e in exc.errors()]})


def _llano(texto: str | None) -> str:
    """Los mensajes de `ui` vienen en Markdown; aqui viajan como texto."""
    t = str(texto or "")
    t = t.replace("[!] ", "").replace("**", "")
    t = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", t)
    # `cuentas` dice DÓNDE está la puerta en Gradio («arriba del todo, en
    # «Entrar»»). En el cliente Angular no está ahí: el botón Entrar va junto
    # al propio mensaje y en Ajustes. Se quita la ubicación, no el aviso.
    t = re.sub(r"\s*\(arriba del todo, en «Entrar»\)", "", t)
    return t.replace("`", "").strip()


def _no(estado: int, mensaje: str) -> HTTPException:
    return HTTPException(status_code=estado, detail=_llano(mensaje))


def _finito(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# --- Identidad del lector ----------------------------------------------------

class _Lector:
    """Lo que las funciones de `ui` leen de un `gr.Request`, y nada mas.

    `session_hash` es el id del navegador ya saneado. Con el, `ui._dir_lector`
    resuelve a `lectores/<id>` en la nube y a la carpeta de siempre en local,
    exactamente como para un visitante de Gradio. `headers` y `client` son los
    que usa `ui._ip` para los topes por hora.
    """

    def __init__(self, request: Request, ident: str | None):
        self.session_hash = ident
        self.headers = request.headers
        self.client = request.client


# Un id corto seria facil de adivinar o de repetir por casualidad. `crypto.
# randomUUID` da 36 caracteres; se exigen 16 despues de sanear.
_MINIMO_ID = 16


def _ident(request: Request) -> str | None:
    crudo = request.headers.get("x-lector", "")
    limpio = ui._SESION_SEGURA.sub("", crudo)[:64]
    return limpio if len(limpio) >= _MINIMO_ID else None


def lector(request: Request) -> _Lector:
    """Para todo lo que lee o escribe datos del lector.

    **Sin id no se sigue**, y no es por formalidad: en la nube `ui._dir_lector`
    sin `session_hash` resuelve a `lectores/anonimo`, UNA carpeta para todos los
    visitantes. Ese fallo ya paso en Gradio y costo un critico.
    """
    ident = _ident(request)
    if ident is None:
        raise _no(400, "Falta la cabecera X-Lector con el identificador de este "
                       "navegador (al menos 16 caracteres).")
    return _Lector(request, ident)


def lector_opcional(request: Request) -> _Lector:
    return _Lector(request, _ident(request))


Lector = Annotated[_Lector, Depends(lector)]
LectorOpcional = Annotated[_Lector, Depends(lector_opcional)]


def _perfil_de(pet: _Lector) -> perfil_mod.Perfil | None:
    if not pet.session_hash:
        return None
    return perfil_mod.cargar(ui._archivo_lector("perfil.json", pet))


def _perfil_json(p: perfil_mod.Perfil | None) -> dict | None:
    if p is None:
        return None
    return {**asdict(p), "objetivo": p.objetivo,
            "rango_recomendado": list(p.rango_recomendado),
            "cefr": ui._cefr(p.nivel)}


# --- Libros: de un id a un `reader.Libro` ------------------------------------

_RE_CATALOGO = re.compile(r"^(?:PG\d{1,7}|(?:SWV|ASB|VOA|LRD)[0-9A-Z]{1,64})$")
_RE_SUBIDO = re.compile(r"^u[0-9a-f]{16}$")
_EXT_LIBRO = (".epub", ".pdf", ".txt")
_TOPE_SUBIDA = 20 * 1024 * 1024     # el mismo que `ui.TAMANO_MAXIMO_SUBIDA`
_MAX_SUBIDOS = 30                   # libros propios por lector
_SUBIDAS_HORA = 12                  # intentos de subida por IP y hora
# Revisión de 4e (6): medir no cuesta dinero, pero es CPU del único proceso del
# Space, y la puntuación va de una en una (`_CANDADO_MODELO`): sin freno, un
# bucle de peticiones de medir dejaba a los demás esperando detrás. Por IP y
# hora, como los topes de `ui`; 0 quita el tope.
_MEDIDAS_HORA = int(os.environ.get("LITERALEVEL_LIMITE_MEDIDAS", "40"))    # muestra, libro y capítulo
_CURVAS_HORA = int(os.environ.get("LITERALEVEL_LIMITE_CURVAS", "6"))       # curvas nuevas
# Y la curva abre un hilo por libro que espera su turno: sin tope de cola, mil
# libros distintos eran mil hilos vivos. Para todos, no por IP.
_CURVAS_VIVAS = int(os.environ.get("LITERALEVEL_CURVAS_EN_COLA", "4"))
_HOLGURA_FORMULARIO = 64 * 1024     # cabeceras multipart y campos de texto


async def _formulario(request: Request, tope: int, mensaje: str):
    """El multipart leído por trozos con tope ANTES de interpretarlo.

    Con `File(...)` en la firma, Starlette lee el cuerpo entero -y lo vuelca a
    un temporal pasado 1 MB- antes de llamar a la ruta: una subida de gigas
    llegaba al disco y solo después salía el 413 (revisión de entrega-4e sobre
    2a49bf2). Aquí se corta al pasar el tope, venga o no Content-Length."""
    if not request.headers.get("content-type", "").startswith("multipart/form-data"):
        raise _no(415, "Se esperaba un formulario con el archivo.")
    limite = tope + _HOLGURA_FORMULARIO
    largo = request.headers.get("content-length", "")
    if largo.isdigit() and int(largo) > limite:
        raise _no(413, mensaje)
    trozos, leidos = [], 0
    async for trozo in request.stream():
        leidos += len(trozo)
        if leidos > limite:
            raise _no(413, mensaje)
        trozos.append(trozo)
    cuerpo = b"".join(trozos)

    async def flujo():
        yield cuerpo

    try:
        return await MultiPartParser(request.headers, flujo(), max_files=1, max_fields=4,
                                     max_part_size=_HOLGURA_FORMULARIO).parse()
    except Exception as e:
        raise _no(422, "No entiendo ese formulario.") from e


def _normalizar_id(crudo: str) -> str:
    """El id del cliente es de fuera. Solo pasan dos formas conocidas: nunca
    una ruta, que es lo que haria de `reader.cargar` un lector de archivos
    arbitrarios del servidor."""
    s = str(crudo or "").strip()
    if _RE_SUBIDO.fullmatch(s.lower()):
        return s.lower()
    s = s.upper()
    if _RE_CATALOGO.fullmatch(s):
        return s
    raise _no(404, "No conozco ese libro.")


def _dir_subidos(pet: _Lector) -> Path:
    return ui._dir_lector(pet) / "subidos"


def _nombres_subidos(pet: _Lector) -> Path:
    """{id: nombre con que el lector subió el archivo}. En disco el libro se
    guarda con su hash, y ese era el título que se veía («d139e28e2c2f7f80.txt»)."""
    return _dir_subidos(pet) / "nombres.json"


_CANDADOS_SUBIDAS = [threading.Lock() for _ in range(64)]


def _candado_subidas(pet: _Lector) -> threading.Lock:
    """El de las subidas de este lector: contar el tope, escribir el libro y apuntar
    su nombre van juntos. Con la subida en un hilo (31325a4), dos subidas del mismo
    lector a la vez pasaban el tope y dejaban nombres.json como JSON inválido
    (ronda 2 de e6, 15 sep 2026). 64 candados repartidos por carpeta, como los de
    `ConsultorLexico`: memoria fija, y otro lector solo espera si le toca el mismo."""
    h = int(hashlib.sha256(str(_dir_subidos(pet)).encode("utf-8")).hexdigest()[:8], 16)
    return _CANDADOS_SUBIDAS[h % len(_CANDADOS_SUBIDAS)]


def _escribir_nombres(ruta: Path, nombres: dict) -> bool:
    """nombres.json a un temporal y `os.replace`: nunca queda a medio escribir. Si no
    se puede escribir, lo dice en stderr y devuelve False: el libro sigue subido, pero
    sin su nombre original (ronda 3 de e6: el error se tragaba en silencio)."""
    temporal = ruta.with_name(f".{ruta.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporal.write_text(json.dumps(nombres, ensure_ascii=False), "utf-8")
        os.replace(temporal, ruta)
        return True
    except OSError as e:
        print(f"api nombres.json: no he podido escribir {ruta}: {type(e).__name__}: {e}", file=sys.stderr)
        with contextlib.suppress(OSError):
            temporal.unlink()
        return False


def _guardar_nombre_subido(pet: _Lector, ident: str, original: str) -> None:
    limpio = " ".join("".join(c for c in original if c.isprintable()).split())[:120]
    if not limpio:
        return
    ruta = _nombres_subidos(pet)
    try:
        nombres = json.loads(ruta.read_text("utf-8"))
        if not isinstance(nombres, dict):
            nombres = {}
    except (OSError, ValueError):
        nombres = {}
    nombres[ident] = limpio
    _escribir_nombres(ruta, nombres)


def _titulo_subido(lib: reader.Libro, ident: str, pet: _Lector) -> None:
    """Pone el nombre original solo si el título que sacó `reader` es el interno:
    un epub con su propio título lo conserva."""
    try:
        nombres = json.loads(_nombres_subidos(pet).read_text("utf-8"))
    except (OSError, ValueError):
        return
    original = nombres.get(ident) if isinstance(nombres, dict) else None
    if isinstance(original, str) and original and (not lib.titulo or ident[1:] in str(lib.titulo)):
        lib.titulo_visible = original


def _ruta_libro(ident: str, pet: _Lector, descargar: bool = True) -> str | None:
    """La ruta local del libro, descargandolo si hace falta y se permite.

    Con `descargar=False` devuelve None si no esta en disco: la consulta lexica
    solo quiere el contexto, y no puede disparar una descarga de 45 s.
    """
    if ident.startswith("u"):
        carpeta = _dir_subidos(pet)
        for ext in _EXT_LIBRO:
            p = carpeta / f"{ident[1:]}{ext}"
            if p.is_file():
                return str(p)
        raise _no(404, "Ese libro subido ya no está en este navegador.")
    if not ui._abrible(ident):
        raise _no(404, "De este libro no hay texto disponible para abrirlo aquí.")
    if not ui._esta_cacheado(ident):
        if not descargar:
            return None
        # El mismo tope que el buscador de Gradio: descargar no cuesta dinero,
        # pero cada descarga ocupa un hilo hasta 45 s por intento.
        if not ui._dentro_del_limite(pet, "descargas", ui.LIMITE_DESCARGAS_HORA):
            falta = ui._cuanto_falta(ui._minutos_para_la_siguiente('descargas', pet))[3:]
            raise _no(429, f"Has abierto {ui.LIMITE_DESCARGAS_HORA} libros nuevos "
                           f"en esta hora. Espera {falta} o sigue con los que ya tienes.")
    try:
        return ui._descargar_gutenberg(ident)
    except ValueError as e:
        raise _no(404, str(e)) from e
    except ConnectionError as e:
        raise _no(502, "No he podido descargarlo de Project Gutenberg ahora "
                       "mismo. Vuelve a intentarlo en un rato.") from e
    except OSError as e:
        raise _no(500, "No he podido guardar el libro en el servidor.") from e


def _id_de_ruta(ruta: str, pet: _Lector) -> str | None:
    """El camino inverso: de lo que guarda la biblioteca a un id publico."""
    nombre = os.path.basename(str(ruta))
    m = re.fullmatch(r"(?i)pg(\d+)\.(?:txt|epub)", nombre)
    if m:
        return f"PG{m.group(1)}"
    m = re.fullmatch(r"(?i)((?:swv|asb|voa|lrd)[0-9a-z]+)\.txt", nombre)
    if m:
        return m.group(1).upper()
    m = re.fullmatch(r"([0-9a-f]{16})\.(?:epub|pdf|txt)", nombre)
    if m and Path(ruta).parent == _dir_subidos(pet):
        return f"u{m.group(1)}"
    return None


_LIBROS: OrderedDict[tuple, reader.Libro] = OrderedDict()
_CANDADO_LIBROS = threading.Lock()
_LIBROS_EN_MEMORIA = 6


def _identificar(libro: reader.Libro, ruta: str) -> None:
    """`id_catalogo`, titulo visible y autor, como hace `ui._abrir`.

    El titulo del libro NO se toca: entra en la clave de los analisis guardados
    (`ui._clave_libro`) y cambiarlo los dejaria huerfanos.
    """
    nombre = os.path.basename(ruta)
    m = re.search(r"(?i)\bpg(\d+)\.(?:txt|epub)$", nombre)
    libro.id_catalogo = f"PG{m.group(1)}" if m else None
    if not m:
        m2 = re.search(r"(?i)\b((?:swv|asb|voa|lrd)[0-9a-z]+)\.txt$", nombre)
        libro.id_catalogo = m2.group(1).upper() if m2 else None
    libro.titulo_visible = libro.titulo
    libro.dificultad_catalogo = None
    libro.nivel_catalogo = ""
    if libro.id_catalogo:
        try:
            df = ui.catalogo().df
            fila = df.loc[df["id"].astype(str) == libro.id_catalogo]
            if len(fila):
                f = fila.iloc[0]
                if re.fullmatch(r"(?i)(?:pg\d+|(?:swv|asb|voa|lrd)[0-9a-z]+)(\.\w+)?",
                                str(libro.titulo or "")):
                    libro.titulo_visible = str(f["title"]) or libro.titulo
                libro.autor = libro.autor or str(f["author"])
                libro.dificultad_catalogo = _finito(f.get("dificultad"))
                libro.nivel_catalogo = str(f.get("nivel_cefr", "") or "")
        except Exception:
            pass


def _cargar_libro(ruta: str) -> reader.Libro:
    try:
        st = os.stat(ruta)
    except OSError as e:
        raise _no(404, "El archivo del libro ya no está en el servidor.") from e
    clave = (ruta, st.st_mtime_ns, st.st_size)
    with _CANDADO_LIBROS:
        if clave in _LIBROS:
            _LIBROS.move_to_end(clave)
            return _LIBROS[clave]
    try:
        libro = reader.cargar(ruta)
    except Exception as e:
        # pypdf y zipfile lanzan cosas que no descienden de OSError.
        raise _no(422, f"No he podido abrir el archivo ({type(e).__name__}).") from e
    if not libro.capitulos:
        raise _no(422, "El archivo no tiene texto legible.")
    _identificar(libro, ruta)
    with _CANDADO_LIBROS:
        _LIBROS[clave] = libro
        while len(_LIBROS) > _LIBROS_EN_MEMORIA:
            _LIBROS.popitem(last=False)
    return libro


def _abrir(ident: str, pet: _Lector, descargar: bool = True) -> tuple[str, reader.Libro]:
    ident = _normalizar_id(ident)
    ruta = _ruta_libro(ident, pet, descargar=descargar)
    if ruta is None:
        raise _no(404, "Ese libro todavía no está abierto en el servidor.")
    lib = _cargar_libro(ruta)
    if ident.startswith("u"):
        _titulo_subido(lib, ident, pet)
    return ruta, lib


# Que parte de un capitulo es licencia, creditos o portada y no la obra.
_PREAMBULO_RE = re.compile(
    r"project gutenberg|gutenberg-tm|produced by|proofreading|distributed proofread|"
    r"transcriber'?s note|^credits?\b|this (?:e-?book|file) was produced|www\.|https?://|"
    r"^contents\.?$|^table of contents",
    re.IGNORECASE)


def _es_preambulo(parrafo: str) -> bool:
    return bool(_PREAMBULO_RE.search(parrafo.strip()))


def _sin_cursiva(texto: str) -> str:
    """«something _to do_» -> «something to do». La marca de cursiva de Gutenberg."""
    return re.sub(r"(?<![\w_])_([^_\n]+)_(?![\w_])", r"\1", texto)


def _parece_indice(texto: str) -> bool:
    """Un indice o un titulillo, no prosa: casi todo mayusculas, o sembrado de
    numeros de pagina y numerales romanos.

    En *Poems of Giosuè Carducci* (PG56711) el indice es UN parrafo largo, asi
    que pasaba el filtro de longitud, y Pronunciar proponia leer en alto «VOICE
    FROM THE PALACE 102 VOICE FROM THE HOVEL 103 ... XXIII.» (15 de 60 frases).
    Un año suelto en una frase de prosa -1 de 17 palabras- no lo dispara.

    Y cinco o más marcas «romano.» (tambien de una letra: «I.», «V.», «X.»)
    son un indice: el «Contents» de *Sherlock Holmes* (PG1661) es un parrafo de
    73 palabras con doce, de las que solo nueve tienen dos letras y quedaba justo
    por debajo del 12 %, asi que abria el libro (diagnostico de entrega-4e). Un
    «Chapter IV.» citado en prosa no llega a cinco.
    """
    palabras = re.findall(r"[^\W\d_]+|\d+", texto)
    if not palabras:
        return True
    if len(re.findall(r"\b[IVXLCDM]+\.", texto)) >= 5:
        return True
    letras = [ch for ch in texto if ch.isalpha()]
    mayusculas = sum(ch.isupper() for ch in letras) / max(1, len(letras))
    numeros = sum(1 for p in palabras if p.isdigit() and len(p) >= 2)
    romanos = sum(1 for p in palabras if re.fullmatch(r"[IVXLCDM]{2,}", p))
    return mayusculas > 0.6 or (numeros + romanos) / len(palabras) > 0.12


def _parrafos(libro: reader.Libro, n: int) -> list[str]:
    """Los parrafos que se le enseñan al lector: la obra, no su envoltura.

    El texto va sin la licencia de Gutenberg (`ficha.sin_licencia`). Y en el
    capitulo que trae la marca de inicio -la portada del archivo- se quitan
    ademas los parrafos de cabeza que no son prosa: creditos, titulo e indice.
    Miguel abrio un libro y lo primero que leyo fue «Produced by... the Online
    Distributed Proofreading Team»; y la frase que le propuso Pronunciar salio
    de ahi.
    """
    c = libro.capitulos[n]
    texto = ficha.sin_licencia(c.texto)
    parrafos = [" ".join(t.split()) for t in re.split(r"\n\s*\n", texto)]
    parrafos = [t for t in parrafos if t]
    # Solo el capitulo con la marca de inicio de Gutenberg. Con cualquier primer
    # capitulo, un cuento de parrafos cortos -StoryWeaver- perdia su principio.
    if ficha._INICIO_PG.search(c.texto):
        i = 0
        # Solo la CABEZA: desde el primer parrafo de prosa de verdad, todo se queda.
        while i < len(parrafos) and (_es_preambulo(parrafos[i]) or _parece_indice(parrafos[i])
                                     or len(parrafos[i].split()) < 40):
            i += 1
        if i < len(parrafos):
            parrafos = parrafos[i:]
    return parrafos


def _capitulo_inicial(libro: reader.Libro) -> int:
    """No abrir en la portadilla, pero tampoco saltarse el libro.

    La regla de `ui._abrir` descarta por titulo lo anterior al capitulo 1
    («Antes del primer capítulo»). Casi siempre es portada e indice, pero cuando
    `reader` no encuentra los encabezados de un .txt ahi cae CASI TODO el libro:
    en *Modern Italian Poets* (PG8171) son 74.858 de 92.389 palabras, y el
    lector abria en el «capitulo 1», que empieza a mitad de frase. Si ese tramo
    es al menos el 40 % del libro, se abre ahi (y `_parrafos` le quita la
    envoltura). En *Orgullo y prejuicio* son 4.957 de 130.000: se sigue saltando.
    """
    total = sum(c.palabras for c in libro.capitulos) or 1

    def cuerpo(c):
        if c.palabras < 500:
            return False
        if ui._RELLENO_RE.search(c.titulo):
            return c.palabras >= 0.4 * total
        return not ficha._es_boilerplate(c)
    return next((i for i, c in enumerate(libro.capitulos) if cuerpo(c)),
                next((i for i, c in enumerate(libro.capitulos) if c.palabras >= 500), 0))


def _cap(libro: reader.Libro, n: int):
    c = ui._cap(libro, n)
    if c is None:
        raise _no(404, f"Este libro tiene {len(libro.capitulos)} capítulos; "
                       f"el {n + 1} no existe.")
    return c


_TEMAS_POR_ID: dict[str, str] | None = None
_CANDADO_TEMAS = threading.Lock()


def _temas(id_libro) -> list[str]:
    """Los temas del catálogo de un libro, para la portada tipográfica del front
    (Miguel, 14 sep): los de Gutenberg («Science fiction; Short stories») y los
    de los corpus libres («Children's stories; StoryWeaver reading level 2»).
    Como mucho ocho; [] si no los hay o si el catálogo no carga (sin cachear el
    fallo: la próxima vez se intenta otra vez)."""
    global _TEMAS_POR_ID
    ident = str(id_libro or "").strip().upper()
    if not ident:
        return []
    if _TEMAS_POR_ID is None:
        with _CANDADO_TEMAS:
            if _TEMAS_POR_ID is None:
                try:
                    d = ui.catalogo().df
                except Exception:
                    return []
                if "temas" in d.columns:
                    pares = zip(d["id"].astype(str).str.strip().str.upper(), d["temas"].fillna("").astype(str))
                    _TEMAS_POR_ID = {i: t for i, t in pares if t.strip()}
                else:
                    _TEMAS_POR_ID = {}
    return [t.strip() for t in _TEMAS_POR_ID.get(ident, "").split(";") if t.strip()][:8]


# Portadas ilustradas por IA, si algún día las hay (Miguel, 14 sep): un archivo
# por libro en /data/portadas (el disco persistente del Space), con el id del
# catálogo como nombre: PG1661.webp. Sin carpeta o sin archivo, la portada es la
# tipográfica del front. LITERALEVEL_PORTADAS la cambia (pruebas, local).
_DIR_PORTADAS = Path(os.environ.get("LITERALEVEL_PORTADAS", "/data/portadas"))
_EXT_PORTADA = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg"}


def _portada_ia(id_libro) -> str | None:
    """La URL de la portada por IA de un libro, o None. Lleva `?v=` con el
    tamaño y la fecha: si se regenera con el mismo nombre, no sale la vieja."""
    ident = str(id_libro or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9_-]{1,80}", ident):
        return None
    for ext in _EXT_PORTADA:
        try:
            st = (_DIR_PORTADAS / f"{ident}{ext}").stat()
        except OSError:
            continue
        if st.st_size > 0:
            return f"/api/portadas/{ident}{ext}?v={st.st_size}-{int(st.st_mtime)}"
    return None


def _libro_tarjeta(b) -> dict:
    """Un resultado del catalogo, listo para pintarse en una tarjeta."""
    dificultad = _finito(b.dificultad)
    return {"id": b.id, "titulo": b.titulo, "autor": ui._autor_corto(b.autor),
            "nivel": b.nivel, "dificultad": dificultad,
            "gancho": " ".join(str(b.gancho or "").split()),
            "descargas": b.descargas, "similitud": b.similitud,
            "afinidad": b.afinidad, "abrible": ui._abrible(b.id),
            "url": b.url_gutenberg, "temas": _temas(b.id), "portada_ia": _portada_ia(b.id),
            # Contrato con f4 (catalogo.py de8a4a8): "" en el catalogo es sin aviso.
            "aviso_contenido": getattr(b, "aviso_contenido", "") or None,
            # Contrato con f4 (reinicio 14): la dificultad de un texto libre corto
            # es la del bloque en que se midio, no la suya; el front lo dice.
            "medido_en_bloque": getattr(b, "medida", "") == "bloque",
            # Contrato con e6 (reinicio 23): entro por el segundo top-k de la franja. El
            # front lo pone en su bloque de nivel sin margen ni SALTO. Siempre presente.
            "por_franja": bool(getattr(b, "por_franja", False))}


def _aviso_contenido(libro) -> str | None:
    """La nota de contenido del catálogo para la ficha. None en libros subidos,
    sin id de catálogo o si el catálogo no carga: la ficha no se rompe por esto."""
    ident = getattr(libro, "id_catalogo", None)
    if not ident:
        return None
    try:
        return ui.catalogo().aviso_de(ident) or None
    except Exception:
        return None


def _medido_en_bloque(libro) -> bool:
    """¿La dificultad de catálogo de este libro es la de un bloque? Solo textos
    libres cortos; False en Gutenberg, en libros subidos o si el catálogo no carga."""
    ident = getattr(libro, "id_catalogo", None)
    if not ident:
        return False
    try:
        return ui.catalogo().medida_de(ident) == "bloque"
    except Exception:
        return False


def _filas_curva(libro: reader.Libro) -> tuple[str | None, dict | None]:
    """La mejor curva que hay sin medir nada: la completa, la rapida o la del
    catalogo (esta ultima solo si sus capitulos cuadran con este archivo)."""
    guardado = ui._analisis_guardado(libro)
    if guardado:
        return "completo", guardado
    rapido = ui._analisis_guardado(libro, "rapido")
    if rapido:
        return "rapido", rapido
    filas = ui._filas_del_catalogo(libro)
    if filas:
        return "catalogo", {"filas": filas, "modo": "catalogo",
                            "ventanas": sum(int(f.get("ventanas") or 1) for f in filas),
                            "palabras": ui._palabras_del_cuerpo(libro),
                            "titulo": libro.titulo, "autor": libro.autor}
    return None, None


def _sugeridos(libro: reader.Libro, p, filas) -> list[dict]:
    """«Este libro te queda grande, pero estos capitulos no» (`ui._capitulos_sugeridos`)."""
    if p is None or not filas:
        return []
    try:
        if ficha.dificultad_global(filas) <= p.nivel + perfil_mod.RETO:
            return []
        sel = [f for f in ficha.capitulos_a_tu_nivel(filas, p.nivel, perfil_mod.RETO)
               if 0 <= int(f["indice"]) < len(libro.capitulos)]
    except Exception:
        return []
    return [{"indice": int(f["indice"]),
             "titulo": libro.capitulos[int(f["indice"])].titulo,
             "palabras": int(f.get("palabras") or 0),
             "dificultad": _finito(f.get("dificultad"))} for f in sel]


def _libro_json(ident: str, libro: reader.Libro, pet: _Lector) -> dict:
    p = _perfil_de(pet)
    try:
        c = ficha.caracteristicas(libro)
    except Exception:
        c = None
    fuente, datos = _filas_curva(libro)
    filas = datos["filas"] if datos else []
    nivel_libro = ficha.dificultad_global(filas) if filas else libro.dificultad_catalogo
    exigente = (None if (p is None or nivel_libro is None)
                else bool(nivel_libro > p.nivel + perfil_mod.RETO))
    sinopsis = ui._sinopsis_guardada(libro)
    return {
        "id": ident,
        "titulo": libro.titulo_visible,
        "aviso_contenido": _aviso_contenido(libro),
        "medido_en_bloque": _medido_en_bloque(libro),
        "temas": _temas(getattr(libro, "id_catalogo", None) or ident),
        "portada_ia": _portada_ia(getattr(libro, "id_catalogo", None) or ident),
        "autor": ui._autor_corto(libro.autor),
        "palabras": (c.palabras if c else libro.palabras),
        "inicial": _capitulo_inicial(libro),
        "dificultad": _finito(nivel_libro),
        "cefr": ui._cefr(nivel_libro) if nivel_libro is not None else None,
        "fuente_dificultad": fuente or ("catalogo" if nivel_libro is not None else None),
        "capitulos": [{"indice": i, "titulo": cap.titulo, "palabras": cap.palabras}
                      for i, cap in enumerate(libro.capitulos)],
        "ficha": None if c is None else {
            "frase_media": c.frase_media, "dialogo": c.dialogo,
            "forma_del_dialogo": c.forma_del_dialogo, "riqueza": c.riqueza,
            "distintivas": c.distintivas[:10],
            "minutos_comodo": c.minutos(False), "minutos_exigente": c.minutos(True),
            "tiempo": (ui._reloj_llano(c.minutos(exigente)) if exigente is not None
                       else ui._rango_de_tiempo(c.minutos(False), c.minutos(True))),
            "exigente": exigente,
        },
        "sugeridos": _sugeridos(libro, p, filas),
        "sinopsis": sinopsis,
    }


# --- Salud y estado ------------------------------------------------------------

@app.get("/api/salud")
def salud() -> dict:
    """Barata a proposito: la llama el front para saber si el Space desperto."""
    return {"estado": "ok", "api": VERSION,
            "cargado": {"puntuador": ui._puntuador is not None,
                        "catalogo": ui._catalogo is not None,
                        "consultor": ui._consultor is not None},
            # Reinicio 27: true solo si una busqueda con nivel no espera a cargar nada (modelo, titulos
            # e indices de nombres). `catalogo` era true 25 s antes; el guion del video espera a este.
            "buscador_listo": bool(ui._catalogo is not None and ui._catalogo.listo_para_buscar())}


@app.get("/api/estado")
def estado() -> dict:
    """Diagnostico para la demo. **Sin rutas del disco y sin nombres de usuario**:
    esta pagina es publica (la auditoria 15 ya lo cazo en la pestana de Gradio)."""
    try:
        cat = ui.catalogo()
        catalogo_info = {"disponible": True, "libros": len(cat.df),
                         "medido_con_v4": cat.medido, "resumen": cat.resumen()}
    except Exception as e:
        catalogo_info = {"disponible": False, "detalle": type(e).__name__}
    from lexicon import RUTA_DICCIONARIO
    dic = Path(RUTA_DICCIONARIO)
    ruta_modelo = str(ui.RUTA_MODELO)
    return {
        "aplicacion": "LiteraLevel", "api": VERSION,
        "modelo": {"disponible": os.path.isdir(ruta_modelo)
                   or scoring._parece_repo_hf(ruta_modelo),
                   "cargado": ui._puntuador is not None},
        "diccionario": {"disponible": dic.exists(),
                        "megas": round(dic.stat().st_size / 1e6) if dic.exists() else 0,
                        "cargado": ui._consultor is not None},
        "catalogo": catalogo_info,
        "funciones_openai": {"disponibles": not config.falta()},
        # Reinicio 26: para ver en el Space que la precarga no sube la RAM por encima de la primera busqueda.
        "proceso": _memoria_del_proceso(),
        "perfiles": {"puerta": cuentas.hay_codigos(),
                     "validos": len(cuentas._tabla()),
                     "declarados": cuentas.declaradas(),
                     "avisos": cuentas.problemas()},
    }


# --- Entrar: la puerta de lo que cuesta dinero ---------------------------------

class EntrarPeticion(BaseModel):
    usuario: str = Field(default="", max_length=80)
    clave: str = Field(default="", max_length=200)


def _entrada_json(pet: _Lector, mensaje: str = "") -> dict:
    abierta = not cuentas.hay_codigos()
    codigo = ui._codigo_de(pet)
    cuenta = cuentas.validar(codigo) if codigo else None
    return {"puerta": not abierta, "dentro": abierta or cuenta is not None,
            "nombre": cuenta.nombre if cuenta else None,
            "restantes": (cuentas.queda(ui.BASE_DATOS_LECTOR, cuenta)
                          if cuenta else None),
            "openai": not config.falta(), "mensaje": _llano(mensaje)}


@app.get("/api/entrada")
def entrada(pet: Lector) -> dict:
    return _entrada_json(pet)


@app.post("/api/entrar")
def entrar(datos: EntrarPeticion, pet: Lector) -> dict:
    # `ui._entrar` trae el freno de intentos fallidos, la comparacion en tiempo
    # constante y el mensaje que no dice si fallo el usuario o la clave.
    mensaje = ui._entrar(datos.usuario, datos.clave, pet)
    return _entrada_json(pet, mensaje)


@app.post("/api/salir")
def salir(pet: Lector) -> dict:
    return _entrada_json(pet, ui._salir(pet))


# --- Punto 1: nivel ------------------------------------------------------------

Nivel = Annotated[float, Field(ge=0.0, le=2.0)]


class CuestionarioPeticion(BaseModel):
    nombre: str = Field(default="", max_length=80)
    respuestas: dict[str, float | list[float] | None]
    guardar: bool = True


class MuestraPeticion(BaseModel):
    nombre: str = Field(default="", max_length=80)
    texto: str = Field(min_length=1, max_length=25_000)


class NivelLibroPeticion(BaseModel):
    nombre: str = Field(default="", max_length=80)
    libro_id: str = Field(min_length=1, max_length=80)


@app.get("/api/cuestionario")
def cuestionario() -> dict:
    preguntas = [
        {"clave": clave, "pregunta": pregunta, "multiple": multiple,
         "opciones": [{"etiqueta": e, "valor": v} for e, v in opciones]}
        for clave, pregunta, opciones, multiple in perfil_mod.PREGUNTAS]
    fragmentos = [
        {**{k: v for k, v in f.items() if k != "opciones"},
         "multiple": False,
         "opciones": [{"etiqueta": e, "valor": v} for e, v in f["opciones"]]}
        for f in perfil_mod.FRAGMENTOS]
    return {"preguntas": preguntas, "fragmentos": fragmentos,
            "peso_fragmentos": perfil_mod.PESO_FRAGMENTOS}


@app.get("/api/perfil")
def perfil(pet: Lector) -> dict:
    return {"perfil": _perfil_json(_perfil_de(pet))}


def _validar_respuestas(respuestas: dict) -> dict:
    """Solo claves del cuestionario y valores de la escala. Viene de fuera."""
    validas = set(ui._claves_cuestionario())
    fuera = {}
    for k, v in respuestas.items():
        if k not in validas:
            raise _no(422, f"No hay ninguna pregunta que se llame «{k}».")
        if v is None:
            continue
        valores = v if isinstance(v, list) else [v]
        if not all(_finito(x) is not None and 0.0 <= float(x) <= 2.0 for x in valores):
            raise _no(422, "Las respuestas tienen que estar entre 0 y 2.")
        fuera[k] = v
    return fuera


@app.post("/api/perfil/cuestionario")
def perfil_cuestionario(datos: CuestionarioPeticion, pet: LectorOpcional) -> dict:
    """Vale con UNA respuesta: `perfil.desde_cuestionario` ya lo admite, y es lo
    que permite que el formulario enseñe una estimacion desde la primera
    pregunta (`enganche.md` §3.3). Con `guardar=false` solo estima."""
    respuestas = _validar_respuestas(datos.respuestas)
    try:
        p = perfil_mod.desde_cuestionario(respuestas, nombre=datos.nombre.strip())
    except ValueError as e:
        raise _no(422, str(e)) from e
    if datos.guardar:
        if not pet.session_hash:
            raise _no(400, "Para guardar el nivel hace falta la cabecera X-Lector.")
        try:
            p.guardar(ui._archivo_lector("perfil.json", pet))
        except OSError as e:
            raise _no(500, "No he podido guardar tu nivel.") from e
    return _perfil_json(p)


_CANDADO_MODELO = threading.Lock()


def _puntuar(texto: str):
    """Una puntuacion a la vez: dos forwards de torch simultaneos duplican la
    memoria del pico, y el Space tiene un solo proceso para todos."""
    with _CANDADO_MODELO:
        return ui.puntuador().puntuar(texto)


def _frenar(pet: _Lector, cubo: str, tope: int) -> None:
    """Gasta una ficha del cubo por IP y hora, o 429 con los minutos que faltan.
    Va DESPUÉS de lo que se rechaza sin coste (texto que no es prosa, capítulo
    que no existe), para que un error no gaste ficha."""
    if not ui._dentro_del_limite(pet, cubo, tope):
        raise _no(429, _mensaje_tope_medir(cubo, ui._minutos_para_la_siguiente(cubo, pet)))


_QUE_SE_MIDE = {"medidas": "medidas de nivel y de capítulos", "curvas": "curvas de libros"}


def _mensaje_tope_medir(cubo: str, minutos: int) -> str:
    """El aviso de `ui._mensaje_limite` dice que medir un capítulo no cuesta
    nada y sigue funcionando: con estos topes ya no es verdad (f4 y Central,
    reinicio 11). Aquí se dice qué se ha acabado y que leer y buscar siguen."""
    cuando = ui._cuanto_falta(minutos)
    return (f"Has llegado al límite de {_QUE_SE_MIDE.get(cubo, 'mediciones')} de esta hora. "
            f"Vuelve a intentarlo {cuando}. Leer y buscar siguen funcionando.")


@app.post("/api/perfil/muestra")
def perfil_muestra(datos: MuestraPeticion, pet: Lector) -> dict:
    texto = datos.texto.strip()
    # El filtro ANTES de cargar el modelo, como en `ui._desde_muestra`.
    ok, motivo = scoring.continuous_prose(texto)
    if not ok:
        raise _no(422, scoring._MOTIVOS.get(motivo, motivo))
    _frenar(pet, "medidas", _MEDIDAS_HORA)  # tope de la muestra
    try:
        r = _puntuar(texto)
    except ValueError as e:
        raise _no(422, str(e)) from e
    except Exception as e:
        raise _no(503, f"No he podido cargar el modelo ({type(e).__name__}).") from e
    p = perfil_mod.Perfil(nivel=r.puntuacion, banda=r.banda, origen="muestra",
                          creado=perfil_mod._ahora(), nombre=datos.nombre.strip())
    try:
        p.guardar(ui._archivo_lector("perfil.json", pet))
    except OSError as e:
        raise _no(500, "No he podido guardar tu nivel.") from e
    return _perfil_json(p)


@app.post("/api/perfil/libro")
def perfil_libro(datos: NivelLibroPeticion, pet: Lector) -> dict:
    """Situa al lector con un libro que dice leer comodo (`ui._nivel_desde_libro`)."""
    _, libro = _abrir(datos.libro_id, pet)
    muestra = ui._muestra_de_libro(libro)
    if len(muestra.split()) < 150:
        raise _no(422, "Ese libro tiene muy poco texto corrido para medirlo.")
    _frenar(pet, "medidas", _MEDIDAS_HORA)  # tope del nivel con un libro
    try:
        r = _puntuar(muestra)
    except ValueError as e:
        raise _no(422, str(e)) from e
    except Exception as e:
        raise _no(503, f"No he podido cargar el modelo ({type(e).__name__}).") from e
    p = perfil_mod.Perfil(nivel=r.puntuacion, banda=r.banda, origen="muestra",
                          creado=perfil_mod._ahora(), nombre=datos.nombre.strip())
    try:
        p.guardar(ui._archivo_lector("perfil.json", pet))
    except OSError as e:
        # Como en /api/perfil/muestra; sin esto era el 500 genérico (auditoría de Codex, 7).
        raise _no(500, "No he podido guardar tu nivel.") from e
    return {**_perfil_json(p),
            "partes": min(ui.PARTES_MUESTRA, len(ui._cuerpo_para_muestra(libro)))}


# --- Punto 2: encontrar ---------------------------------------------------------

class BusquedaPeticion(BaseModel):
    consulta: str = Field(min_length=1, max_length=300)
    nivel: Nivel | None = None
    ajustar: bool = True
    n: int = Field(default=10, ge=1, le=30)


@app.post("/api/buscar")
def buscar(datos: BusquedaPeticion, pet: LectorOpcional) -> dict:
    nivel = None
    if datos.ajustar:
        p = _perfil_de(pet)
        nivel = datos.nivel if datos.nivel is not None else (p.nivel if p else None)
    try:
        libros, aviso = ui.catalogo().buscar(datos.consulta, nivel_lector=nivel, n=datos.n, franja=True)
    except Exception as e:
        raise _no(503, f"El buscador no está disponible ahora mismo ({type(e).__name__}).") from e
    # Contrato con e6 (reinicio 23): los bordes (lo, hi] de la franja con que se marca
    # `por_franja`, en milesimas, para que el front reparta con los mismos; null sin nivel.
    return {"resultados": [_libro_tarjeta(b) for b in libros], "aviso": aviso,
            "ajustado": nivel is not None, "nivel": nivel,
            "franja": list(catalogo.franja_de(nivel)) if nivel is not None else None,
            "nota": _llano(ui._nota_nivel())}


@app.get("/api/recomendar")
def recomendar(pet: Lector, n: int = 10) -> dict:
    """«Sorprendeme»: lo mas leido cerca de tu nivel, pandas puro (0,01 s)."""
    n = max(1, min(int(n), 30))
    p = _perfil_de(pet)
    if p is None:
        return {"resultados": [], "necesita_perfil": True, "rango": None, "rescate": False}
    rescate = False
    # Con mensaje propio: si el catálogo no carga, esto caía en el 500 genérico
    # (auditoría de Codex, 7), como ya hace /api/buscar.
    try:
        cat = ui.catalogo()
        libros = cat.por_nivel(p.nivel, holgura=ui.HOLGURA_POR_NIVEL, n=n)
        # Nunca un callejon: si nada de tu nivel se abre, lo mas facil que si.
        if libros and not any(ui._abrible(b.id) for b in libros):
            faciles = [b for b in cat.por_nivel(p.nivel, holgura=3.0, n=200) if ui._abrible(b.id)]
            if faciles:
                faciles.sort(key=lambda b: scoring.ANCHORS.index(b.nivel)
                             if b.nivel in scoring.ANCHORS else 9)
                libros, rescate = faciles[:n], True
    except Exception as e:
        raise _no(503, f"El catálogo no está disponible ahora mismo ({type(e).__name__}).") from e
    lo = max(0.0, p.nivel - ui.HOLGURA_POR_NIVEL)
    hi = min(2.0, p.nivel + ui.HOLGURA_POR_NIVEL)
    return {"resultados": [_libro_tarjeta(b) for b in libros], "necesita_perfil": False,
            "rango": [round(lo, 2), round(hi, 2)], "rescate": rescate,
            "nota": _llano(ui._nota_nivel())}


# --- Punto 3: leer ---------------------------------------------------------------

@app.get("/api/libros/{libro_id}")
def libro(libro_id: str, pet: Lector) -> dict:
    """Abre el libro (descarga si hace falta) y da su indice y su ficha."""
    ident = _normalizar_id(libro_id)
    _, lib = _abrir(ident, pet)
    return _libro_json(ident, lib, pet)


@app.post("/api/libros")
async def subir_libro(pet: Lector, request: Request) -> dict:
    """Sube un `.epub`, `.pdf` o `.txt` propio. Solo lo ve este lector."""
    # Antes de leer nada: el cubo cuenta intentos, no solo subidas buenas.
    if not ui._dentro_del_limite(pet, "subidas", _SUBIDAS_HORA):
        raise _no(429, ui._mensaje_limite("es", ui._minutos_para_la_siguiente("subidas", pet),
                                          "subidas"))
    formulario = await _formulario(request, _TOPE_SUBIDA, "El archivo pasa de 20 MB.")
    try:
        archivo = formulario.get("archivo")
        if archivo is None or isinstance(archivo, str):
            raise _no(422, "No me ha llegado ningún archivo.")
        nombre = str(archivo.filename or "").lower()
        original = os.path.splitext(os.path.basename(str(archivo.filename or "")))[0]
        ext = os.path.splitext(nombre)[1]
        if ext not in _EXT_LIBRO:
            raise _no(415, "Sube un .epub, un .pdf o un .txt.")
        h = hashlib.sha256()
        trozos, total = [], 0
        while True:
            trozo = await archivo.read(1 << 20)
            if not trozo:
                break
            total += len(trozo)
            # Este tope es el del archivo tal cual llega. Lo que ocupa
            # descomprimido (un epub es un zip) lo vigila reader.py al abrirlo.
            if total > _TOPE_SUBIDA:
                raise _no(413, "El archivo pasa de 20 MB.")
            h.update(trozo)
            trozos.append(trozo)
    finally:
        await formulario.close()
    return await run_in_threadpool(_guardar_subido, pet, original, ext, h, trozos, total)


def _guardar_subido(pet: _Lector, original: str, ext: str, h, trozos: list[bytes], total: int) -> dict:
    """Lo que sigue a leer la subida, EN UN HILO: escribir hasta 20 MB y abrir el
    PDF o el epub. La ruta es `async` para leer el formulario por trozos, y en una
    ruta `async` lo síncrono corre en el bucle de eventos: mientras tanto el proceso
    entero -la API y el Gradio montado en él- no atendía a nadie (auditoría
    cruzada de 4e, 14 sep 2026)."""
    if not total:
        raise _no(422, "El archivo está vacío.")
    ident = "u" + h.hexdigest()[:16]
    carpeta = _dir_subidos(pet)
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise _no(500, "No he podido guardar el libro en el servidor.") from e
    destino = carpeta / f"{ident[1:]}{ext}"
    with _candado_subidas(pet):
        nuevo = not destino.exists()
        if nuevo and sum(1 for p in carpeta.iterdir() if p.suffix in _EXT_LIBRO) >= _MAX_SUBIDOS:
            raise _no(429, f"Ya tienes {_MAX_SUBIDOS} libros subidos. Borra alguno con la papelera de «Mis libros» para subir otro.")
        if nuevo:
            # Disco lleno o sin permiso: con mensaje propio, no el 500 genérico
            # (auditoría de Codex, 7).
            try:
                destino.write_bytes(b"".join(trozos))
            except OSError as e:
                destino.unlink(missing_ok=True)
                raise _no(500, "No he podido guardar el libro en el servidor.") from e
    # Abrir el libro, fuera del candado: pueden ser segundos (un PDF), y los candados van
    # por franjas, así que un lector ajeno de la misma franja esperaba (ronda 3 de e6).
    try:
        lib = _cargar_libro(str(destino))
    except HTTPException:
        if nuevo:
            with _candado_subidas(pet):
                destino.unlink(missing_ok=True)
        raise
    with _candado_subidas(pet):
        _guardar_nombre_subido(pet, ident, original)
    _titulo_subido(lib, ident, pet)
    return _libro_json(ident, lib, pet)


@app.get("/api/libros/{libro_id}/capitulos/{n}")
def capitulo(libro_id: str, n: int, pet: Lector) -> dict:
    ident = _normalizar_id(libro_id)
    _, lib = _abrir(ident, pet)
    c = _cap(lib, n)
    return {"libro_id": ident, "indice": n, "total": len(lib.capitulos),
            "titulo": c.titulo, "palabras": c.palabras,
            "parrafos": _parrafos(lib, n)}


class ProgresoPeticion(BaseModel):
    capitulo: int = Field(ge=0)


@app.put("/api/libros/{libro_id}/progreso")
def progreso(libro_id: str, datos: ProgresoPeticion, pet: Lector) -> dict:
    """El marcapaginas y la estanteria: los mismos archivos que usa Gradio."""
    ident = _normalizar_id(libro_id)
    ruta, lib = _abrir(ident, pet, descargar=False)
    _cap(lib, datos.capitulo)
    ui._guardar_sesion(ruta, lib.titulo, datos.capitulo, pet)
    biblioteca.anotar(ruta_libro=ruta, titulo=lib.titulo_visible, autor=lib.autor,
                      capitulos=len(lib.capitulos), capitulo=datos.capitulo,
                      palabras=lib.palabras,
                      ruta=ui._archivo_lector("biblioteca.json", pet))
    return {"ok": True, "capitulo": datos.capitulo}


@app.post("/api/libros/{libro_id}/capitulos/{n}/medir")
def medir_capitulo(libro_id: str, n: int, pet: Lector) -> dict:
    ident = _normalizar_id(libro_id)
    _, lib = _abrir(ident, pet, descargar=False)
    c = _cap(lib, n)
    _frenar(pet, "medidas", _MEDIDAS_HORA)  # tope de medir un capítulo
    try:
        r = _puntuar(ficha.para_medir(c.texto))
    except ValueError as e:
        raise _no(422, str(e)) from e
    except Exception as e:
        raise _no(503, f"No he podido cargar el modelo ({type(e).__name__}).") from e
    return {"puntuacion": r.puntuacion, "banda": r.banda, "cefr": ui._cefr(r.puntuacion),
            "bloques": r.n_bloques, "confianza": r.confianza}


@app.get("/api/libros/{libro_id}/capitulos/{n}/frase")
def frase_del_capitulo(libro_id: str, n: int, pet: Lector) -> dict:
    """Una frase para leer en voz alta; distinta en cada llamada."""
    ident = _normalizar_id(libro_id)
    _, lib = _abrir(ident, pet, descargar=False)
    _cap(lib, n)
    # La seleccion de `ui._frase_del_capitulo` (parrafos de 30+ palabras, frases
    # de 6 a 25 que empiezan donde empieza una frase, sin titulillo delante),
    # pero sobre los parrafos LIMPIOS: el original leia el capitulo crudo y
    # proponia «Credits: Produced by ellinora, Bryan Ness...» para leer en alto.
    candidatas = []
    for parrafo in _parrafos(lib, n):
        if len(parrafo.split()) < 30 or _es_preambulo(parrafo) or _parece_indice(parrafo):
            continue
        for f in ui._oraciones(ui._sin_encabezado(parrafo)):
            # A nivel de frase manda el criterio de `ui` (entrega-4e, 3a3d546):
            # el propio mira parrafos enteros y no ve «VIRGIL 67 V. INVOCATION».
            if (6 <= len(f.split()) <= 25 and ui._empieza_entera(f) and not _es_preambulo(f)
                    and not ui._parece_indice(f)):
                # Gutenberg marca la cursiva con `_guiones bajos_`: para leer en
                # alto sobran («something _to do_» salio asi en el Space).
                candidatas.append(_sin_cursiva(f))
    if not candidatas:
        return {"frase": None}
    clave = (getattr(lib, "titulo", ""), int(n))
    ronda = ui._RONDA_FRASE.get(clave, -1) + 1
    ui._RONDA_FRASE[clave] = ronda
    return {"frase": candidatas[ronda % len(candidatas)]}


# --- La curva: trabajo en segundo plano ----------------------------------------

_TRABAJOS: OrderedDict[str, dict] = OrderedDict()
_CANDADO_TRABAJOS = threading.Lock()
_UNA_CURVA_A_LA_VEZ = threading.Semaphore(1)


def _resumen_curva(fuente: str | None, datos: dict | None) -> dict:
    if not datos or not datos.get("filas"):
        return {"fuente": None, "filas": []}
    filas = datos["filas"]
    medias = [float(f["dificultad"]) for f in filas]
    global_ = ficha.dificultad_global(filas)
    mitad = len(medias) // 2 or 1
    principio = sum(medias[:mitad]) / mitad
    final = sum(medias[mitad:]) / max(1, len(medias) - mitad)
    forma = ("se_complica" if final - principio > 0.12 else
             "se_suelta" if principio - final > 0.12 else "pareja")
    facil = min(filas, key=lambda f: f["dificultad"])
    dificil = max(filas, key=lambda f: f["dificultad"])
    if len(filas) == 1:
        # Un cuento de un solo capitulo no tiene forma ni capitulo mas facil o mas dificil: con una fila,
        # `final` era sum([]) / 1 = 0 y salia «se va soltando», y facil y dificil eran la misma (e6, reinicio 27).
        forma = facil = dificil = None
    return {
        "fuente": fuente, "global": round(global_, 3), "cefr": ui._cefr(global_),
        "banda": scoring.public_band(global_), "forma": forma,
        "ventanas": datos.get("ventanas", 0), "palabras": datos.get("palabras", 0),
        "capitulos_medidos": datos.get("capitulos_medidos", len(filas)),
        "capitulos_totales": datos.get("capitulos_totales", len(filas)),
        "facil": facil, "dificil": dificil,
        "filas": [{"capitulo": f.get("capitulo"), "indice": f.get("indice"),
                   "titulo": f.get("titulo", ""), "dificultad": f["dificultad"],
                   "ventanas": f.get("ventanas"), "palabras": f.get("palabras")}
                  for f in filas]}


def _medir_libro(trabajo: dict, libro: reader.Libro, modo: str) -> None:
    """El bucle de `ui._analizar_libro`, sin grafica, y guardando en el MISMO
    archivo: una curva medida aqui la ve Gradio y al reves."""
    try:
        trabajo["estado"] = "en_cola"
        with _UNA_CURVA_A_LA_VEZ:
            trabajo["estado"] = "en_curso"
            rapido = modo == "rapido"
            cuerpo = ui._capitulos_de_cuerpo(libro)
            if not cuerpo:
                raise ValueError("Este libro no tiene capítulos con prosa suficiente.")
            if rapido and len(cuerpo) > ui.RAPIDO_CAPITULOS:
                import numpy as np
                idx = np.linspace(0, len(cuerpo) - 1, ui.RAPIDO_CAPITULOS)
                cuerpo = [cuerpo[i] for i in sorted(set(idx.round().astype(int).tolist()))]
            trabajo["total"] = len(cuerpo)
            p = ui.puntuador()
            filas, ventanas = [], 0
            for k, (i, c) in enumerate(cuerpo, 1):
                with _CANDADO_MODELO:
                    vs = p.perfil_de_texto(ficha.para_medir(c.texto),
                                           tope=ui.RAPIDO_VENTANAS if rapido else 0)
                if vs:
                    ventanas += len(vs)
                    filas.append({"capitulo": k, "titulo": c.titulo[:40], "indice": i,
                                  "dificultad": round(sum(vs) / len(vs), 3),
                                  "min": round(min(vs), 3), "max": round(max(vs), 3),
                                  "ventanas": len(vs), "palabras": c.palabras})
                trabajo["hechos"] = k
                trabajo["filas"] = list(filas)
            if not filas:
                raise ValueError("No he podido medir ningún capítulo de este libro.")
            datos = {"titulo": libro.titulo, "autor": libro.autor,
                     "palabras": ui._palabras_del_cuerpo(libro), "ventanas": ventanas,
                     "filas": filas, "modo": modo, "capitulos_medidos": len(cuerpo),
                     "capitulos_totales": len(ui._capitulos_de_cuerpo(libro))}
            ui._guardar_analisis(libro, datos, modo)
            trabajo["curva"] = _resumen_curva("completo" if not rapido else "rapido", datos)
            trabajo["estado"] = "hecho"
    except Exception as e:
        print(f"api curva: {type(e).__name__}: {e}", file=sys.stderr)
        trabajo["estado"] = "error"
        trabajo["error"] = (str(e) if isinstance(e, ValueError)
                            else f"La medición se ha interrumpido ({type(e).__name__}).")
    finally:
        trabajo["terminado"] = time.time()


@app.get("/api/libros/{libro_id}/curva")
def curva(libro_id: str, pet: Lector) -> dict:
    ident = _normalizar_id(libro_id)
    _, lib = _abrir(ident, pet, descargar=False)
    fuente, datos = _filas_curva(lib)
    clave = ui._clave_libro(lib)
    with _CANDADO_TRABAJOS:
        vivo = next((t["id"] for t in _TRABAJOS.values()
                     if t["clave"] == clave and t["estado"] in ("en_cola", "en_curso")), None)
    return {**_resumen_curva(fuente, datos), "trabajo": vivo}


class CurvaPeticion(BaseModel):
    modo: Literal["rapido", "completo"] = "rapido"


@app.post("/api/libros/{libro_id}/curva")
def medir_curva(libro_id: str, datos: CurvaPeticion, pet: Lector) -> dict:
    ident = _normalizar_id(libro_id)
    _, lib = _abrir(ident, pet, descargar=False)
    # Lo ya medido no se vuelve a medir: el completo vale tambien como rapido.
    if ui._analisis_guardado(lib) or (datos.modo == "rapido"
                                      and ui._analisis_guardado(lib, "rapido")):
        return {"trabajo": None, "ya_medido": True}
    clave = ui._clave_libro(lib)
    with _CANDADO_TRABAJOS:
        for t in _TRABAJOS.values():
            if t["clave"] == clave and t["modo"] == datos.modo and \
                    t["estado"] in ("en_cola", "en_curso"):
                return {"trabajo": t["id"], "ya_medido": False}
        # La cola, antes que la ficha por hora: si no cabe, no se gasta.
        vivas = sum(1 for t in _TRABAJOS.values() if t["estado"] in ("en_cola", "en_curso"))
        if _CURVAS_VIVAS > 0 and vivas >= _CURVAS_VIVAS:
            raise _no(503, f"Ahora mismo se están midiendo {vivas} libros. "
                           "Vuelve a pedir la curva en unos minutos.")
        _frenar(pet, "curvas", _CURVAS_HORA)
        trabajo = {"id": uuid.uuid4().hex, "clave": clave, "modo": datos.modo,
                   "libro_id": ident, "estado": "en_cola", "hechos": 0, "total": 0,
                   "filas": [], "error": None, "creado": time.time(), "terminado": None}
        _TRABAJOS[trabajo["id"]] = trabajo
        while len(_TRABAJOS) > 100:
            _TRABAJOS.popitem(last=False)
    threading.Thread(target=_medir_libro, args=(trabajo, lib, datos.modo),
                     daemon=True).start()
    return {"trabajo": trabajo["id"], "ya_medido": False}


@app.get("/api/trabajos/{trabajo_id}")
def trabajo(trabajo_id: str) -> dict:
    with _CANDADO_TRABAJOS:
        t = _TRABAJOS.get(str(trabajo_id))
        if t is None:
            raise _no(404, "No conozco ese trabajo; puede que el servidor se haya reiniciado.")
        return {k: v for k, v in t.items() if k != "clave"}


# --- Lo que cuesta dinero: sinopsis ---------------------------------------------

def _va_a_costar(pet: _Lector) -> bool:
    return (not config.falta()
            and cuentas.permite(ui.BASE_DATOS_LECTOR, ui._codigo_de(pet))[0])


def _cobrar(pet: _Lector) -> tuple[bool, str, str | None]:
    """Cobra un uso y devuelve también el código COBRADO.

    Es lo mismo que `ui._puede_pagar` (`cuentas.consumir` con el código de la
    sesión), pero con el código leído una sola vez y devuelto: cada devolución
    volvía a preguntar `ui._codigo_de(pet)`, y con /api/salir o un cambio de
    cuenta desde otra pestaña a mitad de consulta el uso no se devolvía o se
    devolvía a otra cuenta (auditoría de Codex, 2)."""
    codigo = ui._codigo_de(pet)
    puede, motivo = cuentas.consumir(ui.BASE_DATOS_LECTOR, codigo)
    return puede, motivo, codigo


def _devolver(codigo: str | None) -> None:
    """Devuelve a la cuenta que se cobró, no a la que haya ahora en la sesión."""
    cuentas.devolver(ui.BASE_DATOS_LECTOR, codigo)


# --- Escuchar un libro: se prepara únicamente el fragmento elegido ------------

def _fragmento_audio(libro_id: str, n: int, parte: int, pet: _Lector) -> dict:
    ident = _normalizar_id(libro_id)
    _, lib = _abrir(ident, pet)
    c = _cap(lib, n)
    partes = audiolibro.fragmentos("\n\n".join(_parrafos(lib, n)))
    if not partes or parte >= len(partes):
        raise _no(404, "No hay texto en ese fragmento. Elige otro capítulo.")
    texto = partes[parte]
    clave = audiolibro.clave(texto)
    base = Path(ui._dir_lector(pet))
    listo = audiolibro.guardado(base, clave)
    return {"libro_id": ident, "capitulo": n, "titulo": c.titulo,
            "parte": parte, "total": len(partes), "texto": texto,
            "clave": clave, "guardado": listo,
            "tope_caracteres": audiolibro.TOPE_CARACTERES,
            **(audiolibro.leer_marcas(base, clave) if listo else
               {"palabras": [], "aproximado": False})}


@app.get("/api/libros/{libro_id}/capitulos/{n}/escuchar")
def fragmento_audio(libro_id: str, n: int, pet: Lector,
                    parte: int = Query(default=0, ge=0)) -> dict:
    return _fragmento_audio(libro_id, n, parte, pet)


@app.post("/api/libros/{libro_id}/capitulos/{n}/escuchar")
def generar_fragmento_audio(libro_id: str, n: int, pet: Lector,
                            parte: int = Query(default=0, ge=0)) -> dict:
    datos = _fragmento_audio(libro_id, n, parte, pet)
    base = Path(ui._dir_lector(pet))
    clave = datos["clave"]
    with voz._candado_audio("audiolibro|" + str(audiolibro.ruta(base, clave))):
        if not audiolibro.guardado(base, clave):
            if config.falta():
                raise _no(503, "La voz no está disponible ahora. Puedes escuchar los fragmentos guardados.")
            codigo = ui._codigo_de(pet)
            permitido, motivo = cuentas.permite(ui.BASE_DATOS_LECTOR, codigo)
            if not permitido:
                raise _no(403, motivo)
            cuenta_hora = "audiolibro:" + hashlib.sha256(codigo.encode()).hexdigest() if codigo else None
            if not ui._dentro_del_limite(pet, "audiolibro", ui.LIMITE_VOZ_HORA, clave=cuenta_hora):
                raise _no(429, "Has llegado al límite de audio de esta hora. Sigue con los fragmentos guardados.")
            permitido, motivo = cuentas.consumir(ui.BASE_DATOS_LECTOR, codigo)
            if not permitido:
                raise _no(403, motivo)
            try:
                audiolibro.generar(base, datos["texto"])
            except Exception:
                if not audiolibro.guardado(base, clave):
                    _devolver(codigo)
                    raise _no(502, "No he podido preparar el audio. Tu uso se ha devuelto; prueba en un momento.")
                # Si las marcas fallaron, conservar el audio ya pagado.
        return {**datos, "guardado": True, **audiolibro.leer_marcas(base, clave)}


@app.get("/api/audiolibro/{clave}.mp3")
def audio_libro_guardado(clave: str, pet: Lector):
    if not re.fullmatch(r"[0-9a-f]{64}", clave):
        raise _no(404, "No existe ese audio.")
    base = Path(ui._dir_lector(pet))
    if not audiolibro.guardado(base, clave):
        raise _no(404, "No existe ese audio en tu espacio.")
    return FileResponse(audiolibro.ruta(base, clave), media_type="audio/mpeg",
                        headers={"Cache-Control": "private, no-store"})


# Un candado por libro para la sinopsis, no uno global: otra sinopsis de otro
# libro no espera, y la segunda petición del mismo libro lee lo que dejó la primera.
_CANDADOS_SINOPSIS: dict[str, threading.Lock] = {}
_REGISTRO_SINOPSIS = threading.Lock()


def _candado_sinopsis(lib: reader.Libro) -> threading.Lock:
    clave = ui._clave_libro(lib)
    with _REGISTRO_SINOPSIS:
        return _CANDADOS_SINOPSIS.setdefault(clave, threading.Lock())


@app.post("/api/libros/{libro_id}/sinopsis")
def sinopsis(libro_id: str, pet: Lector) -> dict:
    """«¿De que trata?», con las mismas guardas que `ui._de_que_trata`.

    Con un candado por libro: dos peticiones a la vez del mismo libro sin
    sinopsis guardada cobraban y generaban las dos (auditoría de Codex, 1).
    Dentro se vuelve a mirar la caché ANTES de cobrar."""
    ident = _normalizar_id(libro_id)
    _, lib = _abrir(ident, pet, descargar=False)
    datos = ui._sinopsis_guardada(lib)
    if datos is not None:
        return {"sinopsis": datos}
    with _candado_sinopsis(lib):
        datos = ui._sinopsis_guardada(lib)
        if datos is not None:
            return {"sinopsis": datos}
        if _va_a_costar(pet) and not ui._dentro_del_limite(pet, "sinopsis",
                                                          ui.LIMITE_SINOPSIS_HORA):
            raise _no(429, ui._mensaje_limite("es", ui._minutos_para_la_siguiente("sinopsis", pet),
                                              "sinopsis"))
        if config.falta():
            raise _no(503, "Para el resumen hace falta la clave de OpenAI. La ficha "
                           "contada no la necesita.")
        puede, motivo, cobrado = _cobrar(pet)
        if not puede:
            raise _no(403, motivo)
        try:
            cliente = ui.consultor()._cliente()
        except Exception as e:
            _devolver(cobrado)
            raise _no(503, f"No he podido preparar el resumen ({type(e).__name__}).") from e
        if cliente is None:
            _devolver(cobrado)
            raise _no(503, "Para el resumen hace falta la clave de OpenAI.")
        datos, causa = ficha.sinopsis(lib, cliente)
        if datos is None:
            if causa in ("sin_red", "sin_pasajes"):
                _devolver(cobrado)
            raise _no(502, "No he podido preparar el resumen ahora mismo."
                      + ("" if causa in ("sin_red", "sin_pasajes")
                         else " Este intento sí ha consumido uno de tus usos."))
        try:
            ui.RUTA_ANALISIS.mkdir(parents=True, exist_ok=True)
            (ui.RUTA_ANALISIS / f"{ui._clave_libro(lib)}-sinopsis.json").write_text(
                json.dumps(datos, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return {"sinopsis": ui._sinopsis_guardada(lib) or datos}


# --- Punto 4: la palabra, en dos etapas -----------------------------------------

class PalabraPeticion(BaseModel):
    palabra: str = Field(min_length=1, max_length=200)
    libro_id: str | None = Field(default=None, max_length=80)
    capitulo: int | None = Field(default=None, ge=0)
    oracion: str | None = Field(default=None, max_length=2000)
    idioma: Literal["es", "en"] = "es"
    etapa: Literal["diccionario", "completa"] = "completa"


_DIR_AUDIO = config.dir_datos() / "audio"
_CANDADO_LEXICO = threading.Lock()


def _candado_etapa(etapa: str):
    """El candado de cada etapa de /api/palabra.

    La completa lo retenía durante la llamada a OpenAI (unos 15 s), y la vista
    previa del diccionario de cualquier lector, la de «40 ms», esperaba detrás:
    medido 3,41 s con un doble de 4 s (auditoría cruzada de 4e, 14 sep 2026). La
    completa ya no lo necesita: `ConsultorLexico` tiene candados por clave
    alrededor de lo que se paga y relee la caché dentro, el diccionario es SQLite
    de solo lectura con `check_same_thread=False`, Gradio lo llama con 8 eventos a
    la vez, y el cobro es atómico en `cuentas`."""
    return _CANDADO_LEXICO if etapa == "diccionario" else contextlib.nullcontext()


def _url_audio(ruta) -> str | None:
    """Wiktionary se sirve desde su dominio; lo generado, por `/api/audio`."""
    if not ruta:
        return None
    s = str(ruta)
    if s.startswith("http://") or s.startswith("https://"):
        return s
    try:
        p = Path(s).resolve()
        if p.is_file() and p.parent == _DIR_AUDIO.resolve():
            return f"/api/audio/{p.name}"
    except OSError:
        pass
    return None


def _avisos_palabra(r, idioma: str, quitar_sin_clave: bool, final: bool = True) -> list[str]:
    """Los avisos de `lexicon`, traducidos y sin repetir.

    **Siempre en español**, aunque la explicacion se pida en ingles: los avisos
    son de la interfaz, que esta en español. Miguel vio en la misma ficha
    «Esta palabra no está en el diccionario», «'inmostly' no esta en el
    diccionario Kaikki» y «The dictionary has no audio for this word». El
    segundo sobra -la ficha ya dice lo mismo- y el tercero salia en ingles
    porque se traducia con el idioma de la explicacion.
    """
    # La acepción provisional la dice `dudoso` con su nota en la ficha: el aviso
    # crudo repetía lo mismo, y cuando `dudoso` salía falso, lo contradecía.
    avisos = [a for a in r.avisos if "no esta en el diccionario" not in a and not _es_provisional(a)]
    if quitar_sin_clave:
        avisos = [a for a in avisos if "OPENAI_API_KEY" not in a]
    if not r.audio_generado:
        avisos = [a for a in avisos if "sin audio en el diccionario" not in a]
        # Solo cuando ya no va a llegar nada: en la vista previa, el audio de
        # tts-1 todavia puede llegar con la etapa completa, y la ficha decia
        # «no hay pronunciacion» un momento antes de enseñarla.
        if final and not (r.ipa_uk or r.ipa_us or r.audio_uk or r.audio_us):
            avisos.append("De esta palabra no hay pronunciación: ni el diccionario la trae "
                          "ni se pudo generar.")
    return [_llano(a) for a in dict.fromkeys(ui._humanizar(a, "es") for a in avisos)]


def _es_provisional(aviso: str) -> bool:
    return "margen bajo" in aviso or "provisional" in aviso


def _es_dudoso(r, etapa: str, explicable: bool) -> bool:
    """¿Se avisa de que la acepción puede no ser la de la frase?

    Sí si lexicon la marcó provisional (margen bajo entre las dos primeras) o si
    la afinidad es baja habiendo varias. Antes, la marca de lexicon ponía
    `dudoso` en falso «para no repetir el aviso», y la ficha de «house» decía a
    la vez que era dudosa y que no. En la vista previa, si va a llegar la
    explicación, no: OpenAI revisa la acepción con las alternativas."""
    if etapa == "diccionario" and explicable:
        return False
    provisional = any(_es_provisional(a) for a in r.avisos)
    baja = (r.similitud is not None and r.n_sentidos_candidatos > 1
            and r.similitud < ui.AFINIDAD_DUDOSA)
    return bool(provisional or baja)


@app.post("/api/palabra")
def palabra(datos: PalabraPeticion, pet: Lector) -> dict:
    """Consulta lexica. El front pide primero `etapa=diccionario` (40 ms, nunca
    cuesta) y despues `etapa=completa` (la explicacion de OpenAI, ~15 s), para
    que el lector vea la definicion al instante en vez de una rueda girando.

    La etapa completa lleva exactamente las guardas de `ui._consultar`: tope por
    hora solo si va a costar, cobro atomico con `_puede_pagar`, devolucion si
    no salio ninguna llamada de pago, y cuaderno solo si el diccionario acerto.
    """
    idioma = datos.idioma
    palabra_ = datos.palabra.strip()
    if len(palabra_.split()) > 4:
        raise _no(422, "Consulta una palabra (o un phrasal verb corto), no una frase.")
    if len(palabra_) > ui.LIMITE_PALABRA:
        raise _no(422, f"Ninguna palabra inglesa pasa de {ui.LIMITE_PALABRA} letras. "
                       "Selecciona una palabra del texto.")

    lib, idx = None, None
    oracion = (datos.oracion or "").strip()[:ui.LIMITE_ORACION]
    origen = "escrita"
    if datos.libro_id:
        try:
            _, lib = _abrir(datos.libro_id, pet, descargar=False)
        except HTTPException:
            lib = None
        if lib is not None and datos.capitulo is not None and ui._cap(lib, datos.capitulo):
            idx = datos.capitulo
    if not oracion and lib is not None and idx is not None:
        oracion = ui._oracion_de(lib.capitulos[idx].texto, palabra_)
        origen = "capitulo"
    if not oracion:
        oracion, origen = palabra_, "sin_contexto"

    explicable = _va_a_costar(pet)
    motivo_sin_explicacion = ""
    if config.falta():
        motivo_sin_explicacion = "Sin clave de OpenAI: no hay explicación de contexto."
    elif not explicable:
        motivo_sin_explicacion = _llano(cuentas.permite(ui.BASE_DATOS_LECTOR,
                                                        ui._codigo_de(pet))[1])

    if datos.etapa == "diccionario":
        with _candado_etapa("diccionario"):
            try:
                r = ui.consultor().consultar(palabra_, oracion, _nivel(pet), idioma=idioma,
                                             usar_openai=False)
            except Exception as e:
                raise _no(503, f"El diccionario no está disponible ({type(e).__name__}).") from e
        # La vista previa NUNCA apunta en el cuaderno: lo hace la etapa completa,
        # que el cliente pide siempre (sin clave o sin perfil es igual de local
        # y tarda lo mismo). Una sola regla y una sola entrada por consulta.
        registrar = False
        avisos = _avisos_palabra(r, idioma, quitar_sin_clave=True, final=not explicable)
    else:
        if explicable and not ui._dentro_del_limite(pet, "lexico", ui.LIMITE_CONSULTAS_HORA):
            raise _no(429, ui._mensaje_limite(idioma,
                                              ui._minutos_para_la_siguiente("lexico", pet),
                                              "lexico"))
        with _candado_etapa("completa"):
            puede, motivo, cobrado = False, "", None
            try:
                if not config.falta():
                    puede, motivo, cobrado = _cobrar(pet)
                r = ui.consultor().consultar(palabra_, oracion, _nivel(pet), idioma=idioma,
                                             usar_openai=puede)
            except Exception as e:
                # Solo se devuelve lo cobrado: sin clave, sin perfil o si el propio
                # cobro falla no hubo uso, y devolverlo regalaba uno (revisión de 4e).
                if puede:
                    _devolver(cobrado)
                raise _no(503, f"El diccionario no está disponible ({type(e).__name__}).") from e
        if not puede and motivo:
            r.avisos = [a for a in r.avisos if "OPENAI_API_KEY" not in a] + [motivo]
        elif puede and getattr(r, "llamadas_de_pago", 0) == 0:
            _devolver(cobrado)
        registrar = bool(r.sentido)
        avisos = _avisos_palabra(r, idioma, quitar_sin_clave=False)

    if registrar:
        cuaderno.registrar(
            palabra=r.palabra_superficie, lema=r.lema_buscado or r.lema, oracion=oracion,
            categoria=r.categoria, sentido=r.sentido,
            # Libro y capítulo solo si la frase salió del capítulo: una palabra
            # escrita a mano («war-chant») se guardaba como de «Alice…, cap. 2»
            # con la frase «war-chant» (f4, prueba final).
            libro=(getattr(lib, "titulo_visible", None) if lib is not None and origen == "capitulo" else None),
            capitulo=(idx + 1 if idx is not None and origen == "capitulo" else None),
            banda=r.banda_lector, zipf=r.frecuencia_zipf,
            ruta=ui._archivo_lector("cuaderno.db", pet))

    dudoso = _es_dudoso(r, datos.etapa, explicable)
    zipf = r.frecuencia_zipf
    rareza = (None if zipf is None else "muy_comun" if zipf >= 5 else
              "frecuente" if zipf >= 4 else "poco_frecuente" if zipf >= 3 else "rara")
    return {
        "etapa": datos.etapa, "palabra": r.palabra_superficie[:ui.LIMITE_PALABRA],
        "lema": r.lema_buscado or r.lema, "categoria": r.categoria,
        "ipa_uk": r.ipa_uk, "ipa_us": r.ipa_us,
        "ipa_generada_por_ia": bool(getattr(r, "ipa_generada_por_ia", False)),
        # «war-chant» no está y la entrada es de «war» (lexicon 5fa2cea): el
        # sentido es de la parte y la IPA y el audio, del compuesto entero.
        "compuesto": getattr(r, "compuesto", None),
        "parte_del_diccionario": getattr(r, "parte_del_diccionario", None),
        # Contrato con 4e: llena solo si la acepción es dudosa y no hubo
        # explicación de OpenAI («bank» en «on the bank», f4 captura 21).
        "acepciones_principales": list(getattr(r, "acepciones_principales", None) or []),
        "audio_uk": _url_audio(r.audio_uk), "audio_us": _url_audio(r.audio_us),
        "audio_generado": r.audio_generado,
        "sentido": r.sentido, "etiquetas": r.etiquetas_sentido,
        "similitud": r.similitud, "sentidos_candidatos": r.n_sentidos_candidatos,
        "dudoso": dudoso,
        "definicion_contextual": r.definicion_contextual,
        "explicacion_gramatical": r.explicacion_gramatical,
        "explicacion_adaptada": r.explicacion_adaptada,
        "ejemplo": r.ejemplo_simplificado, "banda": r.banda_lector,
        # Campos que `lexicon` gana el 13 sep 2026 (entrega-4e). Con `getattr` y
        # su valor por defecto, para que esto funcione antes y despues de su
        # commit. La definicion por IA es la MISMA llamada de pago que la
        # explicacion: ya la cuenta `llamadas_de_pago`.
        "traduccion": getattr(r, "traduccion", None),
        "definicion_ia": getattr(r, "definicion_ia", None),
        "generado_por_ia": bool(getattr(r, "generado_por_ia", False)),
        "acepcion_elegida_por_ia": bool(getattr(r, "acepcion_elegida_por_ia", False)),
        "zipf": zipf, "rareza": rareza, "desde_cache": r.desde_cache,
        "oracion": _sin_cursiva(oracion), "origen_oracion": origen,
        "cita": _cita(_sin_cursiva(oracion), r.palabra_superficie),
        "explicacion_pendiente": datos.etapa == "diccionario" and explicable,
        "motivo_sin_explicacion": motivo_sin_explicacion or None,
        "avisos": avisos,
    }


def _nivel(pet: _Lector) -> float:
    p = _perfil_de(pet)
    return p.nivel if p is not None else ui.NIVEL_POR_DEFECTO


@app.get("/api/portadas/{nombre}")
def portada_ia(nombre: str):
    """Una portada por IA de /data/portadas. Solo «ID.ext» del catálogo, nada
    de rutas; nosniff y una semana de caché (la URL cambia si cambia el archivo)."""
    m = re.fullmatch(r"([A-Z0-9_-]{1,80})(\.webp|\.png|\.jpg)", nombre)
    if not m:
        raise _no(404, "No existe esa portada.")
    p = _DIR_PORTADAS / nombre
    if not p.is_file() or p.stat().st_size == 0:
        raise _no(404, "No existe esa portada.")
    return FileResponse(p, media_type=_EXT_PORTADA[m.group(2)],
                        headers={"Cache-Control": "public, max-age=604800",
                                 "X-Content-Type-Options": "nosniff"})


@app.get("/api/audio/{nombre}")
def audio(nombre: str):
    if not re.fullmatch(r"[\w.-]{1,160}\.(?:mp3|wav|ogg)", nombre) or ".." in nombre:
        raise _no(404, "No existe ese audio.")
    p = _DIR_AUDIO / nombre
    if not p.is_file():
        raise _no(404, "No existe ese audio.")
    # nosniff, como los SVG: el nombre lo elige el cliente (revisión de 4e, 7).
    return FileResponse(p, media_type="audio/mpeg",
                        headers={"Cache-Control": "public, max-age=604800",
                                 "X-Content-Type-Options": "nosniff"})


def _url_audio_fonema(ruta: Path, prefijo: str) -> str | None:
    """La URL del mp3 de un sonido, o None si no esta en disco o esta vacio.

    Lleva `?v=<tamaño>-<fecha>` porque los mp3 se REGENERAN con el mismo nombre
    (13 sep 2026: formato sostenido, rapido y palabra) y la respuesta se guarda
    30 dias en el navegador: sin la version, quien ya los hubiera oido seguiria
    oyendo los viejos. Es la misma huella que usa la pestaña de Gradio.
    """
    try:
        if not ruta.is_file():
            return None
        st = ruta.stat()
    except OSError:
        return None
    if st.st_size <= 0:
        return None
    return f"{prefijo}{ruta.name}?v={st.st_size}-{int(st.st_mtime)}"


@app.get("/api/fonemas")
def inventario_fonemas(acento: Literal["ga", "rp"] = "ga") -> dict:
    """La tabla del AFI: cada sonido con su audio y su ficha de articulacion.

    Dos acentos (`articulacion.inventario`): General American, 41 sonidos con los
    mp3 de `fonemas`, y britanico (RP), 44 con los suyos. `fonemas` es la lista
    plana de siempre -con `tipo` vocal, diptongo o consonante-, para no romper a
    quien ya la leia; `grupos` es el orden de la tabla por modo de articulacion.
    """
    prefijo = "/api/fonemas/" if acento == "ga" else "/api/fonemas/rp/"
    lista = [
        {"simbolo": s.simbolo, "nombre": s.nombre, "ejemplos": list(s.ejemplos),
         "grupo": s.grupo,
         "tipo": s.grupo if s.grupo in ("vocal", "diptongo") else "consonante",
         "audio": _url_audio_fonema(s.ruta, prefijo),
         "ficha": asdict(s.ficha)}
        for s in articulacion.inventario(acento)]
    grupos = [{"clave": clave, "titulo": titulo,
               "sonidos": [x for x in lista if x["grupo"] == clave]}
              for clave, titulo in articulacion.GRUPOS]
    return {"acento": acento, "acentos": articulacion.ACENTOS, "fonemas": lista,
            "grupos": [g for g in grupos if g["sonidos"]]}


def _servir_fonema(carpeta: Path, archivo: str):
    # Nombre sacado de los puntos de codigo del simbolo: nunca una ruta.
    if not re.fullmatch(r"[0-9a-f_]{4,64}\.mp3", archivo):
        raise _no(404, "No existe ese sonido.")
    p = carpeta / archivo
    if not p.is_file():
        raise _no(404, "No existe ese sonido.")
    return FileResponse(p, media_type="audio/mpeg",
                        headers={"Cache-Control": "public, max-age=2592000"})


@app.get("/api/fonemas/rp/{archivo}")
def audio_fonema_rp(archivo: str):
    return _servir_fonema(articulacion.DIR_AUDIO_RP, archivo)


@app.get("/api/fonemas/{archivo}")
def audio_fonema(archivo: str):
    return _servir_fonema(fonemas.DIR_AUDIO, archivo)


# --- El corte de la boca (animacion_articulatoria, entrega-4e) --------------------

_CABECERAS_SVG = {
    # El corte depende del código anatómico actual. Una copia pública fresca
    # durante 30 días hacía que el móvil siguiera pintando una geometría vieja
    # en la URL normal aunque «Despacio» (otro ?dur=) ya recibiera la nueva.
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    # Se sirve desde el dominio del Space y la IPA de la palabra la manda el
    # cliente: aunque alguien abra el SVG suelto, no puede ejecutar ni pedir nada.
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
}


@functools.lru_cache(maxsize=1024)
def _svg_corte(clase: str, texto: str, acento: str, quieto: bool,
               dur: float | None = None, repetir: bool = True) -> str | None:
    """Generarlo cuesta milisegundos (85 sonidos en 0,11 s): en memoria basta,
    sin escribir en disco lo que llega en la URL."""
    if clase == "palabra":
        return animacion_articulatoria.svg_palabra(texto, acento, dur=dur, repetir=repetir)
    if quieto:
        return animacion_articulatoria.svg_articulacion_quieto(texto, acento)
    return animacion_articulatoria.svg_articulacion(texto, acento, dur=dur, repetir=repetir)


def _pasada(dur: float | None, una: bool, quieto: bool = False) -> tuple[float | None, bool]:
    """«Escuchar y ver»: `dur` (segundos del audio) y `una=1` (una sola pasada,
    sin bucle), contrato de entrega-4e. Redondeado a 0,1 s y fuera de 0,3..30
    se ignora, para que la caché no guarde una copia por cada milisegundo. El
    quieto no se mueve: ni lo uno ni lo otro."""
    if quieto:
        return None, True
    # 30 y no 10 desde «Más lento» (4e, da5c96d): un mp3 de 8 s a 0,25× pasa de 30.
    if dur is not None and not (math.isfinite(dur) and 0.3 <= dur <= 30):
        dur = None
    return (round(dur, 1) if dur is not None else None), not una


# Con paréntesis, ligadura y guion: Kaikki escribe «/ˈhæp(ə)n/».
_SIGNOS_IPA = set("ˈˌːˑ./[]()‿- ")


def _es_ipa(texto: str) -> bool:
    """Letras minúsculas (las de la IPA son casi todas no ASCII), diacríticos
    combinados (el ͡ de t͡ʃ) y los signos de la transcripción. Nada más: el
    módulo pinta escapado lo que no reconoce, y sin esto `?ipa=` cualquier texto
    salía dibujado en un SVG del dominio del Space (entrega-4e)."""
    for ch in texto:
        if ch in _SIGNOS_IPA or unicodedata.category(ch).startswith("M"):
            continue
        if not ch.isalpha() or ch.isupper():
            return False
    return True


@functools.lru_cache(maxsize=4)
def _simbolos(acento: str) -> frozenset[str]:
    return frozenset(s.simbolo for s in articulacion.inventario(acento))


@app.get("/api/articulacion/palabra.svg")
def corte_de_palabra(ipa: str = Query(..., min_length=1, max_length=60),
                     acento: Literal["ga", "rp"] = "ga", dur: float | None = None, una: bool = False):
    """La boca diciendo la palabra entera, a partir de su IPA. Siempre animada:
    con «reducir movimiento» el front pide el sonido que falla, quieto.

    60 caracteres, el tope de la IPA que escribe la IA en lexicon: el módulo
    genera una regla CSS y un <text> por fonema y no tiene tope propio."""
    ipa = ipa.strip()
    if not ipa or not _es_ipa(ipa):
        raise _no(422, "Eso no es una transcripción IPA.")
    svg = _svg_corte("palabra", ipa, acento, False, *_pasada(dur, una))
    if not svg:
        raise _no(404, "No sé dibujar esa palabra.")
    return Response(svg, media_type="image/svg+xml", headers=_CABECERAS_SVG)


_TOPE_PALABRAS_LECTURA = 400


@app.get("/api/lectura/ipa")
def ipa_de_lectura(texto: str = Query(..., min_length=1, max_length=2000),
                   acento: Literal["US", "UK"] = "US",
                   audio: str | None = Query(default=None, max_length=160)) -> dict:
    """La IPA de cada palabra de una frase o párrafo, de los diccionarios
    locales (Kaikki y CMUdict; nunca del modelo): la boca 3D la lee al compás
    del audio de referencia (Miguel, 24 sep). Sin coste: no llama a OpenAI.
    Una palabra que no está en ningún diccionario sale con `ipa` null y el
    front la articula con una aproximación por letras.

    Con `audio` (el nombre de un mp3 generado, el de `/api/audio/{nombre}`),
    cada palabra que whisper ya marcó en ese audio trae `inicio` y `fin` en
    segundos: la boca articula cada palabra en su sitio en vez de repartirlas
    por el tramo (Miguel, 25 sep: «alinea el TTS»; medido en GRID: 0,31 → 0,42
    de Pearson con las mismas reglas). Solo lee el `.tiempos.json` que la
    corrección ya guardó al lado del mp3: si no está, no se pide (no cuesta)."""
    palabras = voz.normalizar_palabras(texto)[:_TOPE_PALABRAS_LECTURA]
    marcas: dict[int, tuple[float, float]] = {}
    if audio and re.fullmatch(r"[\w.-]{1,160}\.mp3", audio) and ".." not in audio:
        lado = _DIR_AUDIO / (audio + ".tiempos.json")
        try:
            if lado.is_file():
                marcas = voz._tiempos_por_indice(palabras, json.loads(lado.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            marcas = {}
    vistas: dict[str, str | None] = {}
    salida = []
    for palabra in palabras:
        if palabra not in vistas:
            # «well-known» no está entera: se junta la de cada pieza.
            piezas = [fonemas.ipa_de_palabra(p, acento)[0] for p in palabra.split("-") if p]
            vistas[palabra] = (" ".join(p.split(",")[0].strip().strip("/[]") for p in piezas)
                               if piezas and all(piezas) else None)
        dato = {"palabra": palabra, "ipa": vistas[palabra]}
        if len(salida) in marcas:
            dato["inicio"], dato["fin"] = (round(x, 3) for x in marcas[len(salida)])
        salida.append(dato)
    return {"acento": acento, "palabras": salida}


MINUTOS_LECTURA_VIVO = 3
LIMITE_GPT_LIVE_HORA = int(os.environ.get("LITERALEVEL_LIMITE_GPT_LIVE", "2"))
SEGUNDOS_GPT_LIVE = 180


def _cerrar_gpt_live_por_tope(sesion_id: str) -> None:
    """Corte de respaldo del servidor, aunque el navegador omita su temporizador."""
    import urllib.error
    import urllib.parse
    import urllib.request
    clave = config.obtener("OPENAI_API_KEY")
    if not clave:
        print("gpt-live: no se pudo aplicar el tope (sin clave)", file=sys.stderr)
        return
    url = "https://api.openai.com/v1/live/sessions/" + urllib.parse.quote(sesion_id, safe="") + "/hangup"
    peticion = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + clave}, method="POST")
    try:
        with urllib.request.urlopen(peticion, timeout=10):
            pass
    except urllib.error.HTTPError as e:
        # La sesión puede haber terminado normalmente antes del corte.
        if e.code not in (404, 409):
            print(f"gpt-live: fallo del corte ({e.code})", file=sys.stderr)
    except Exception as e:
        print(f"gpt-live: fallo del corte ({type(e).__name__})", file=sys.stderr)


def _programar_cierre_gpt_live(sesion_id: str) -> None:
    corte = threading.Timer(SEGUNDOS_GPT_LIVE, _cerrar_gpt_live_por_tope, args=(sesion_id,))
    corte.daemon = True
    corte.start()

# Configuración de inicio de GPT-Live entregada por Miguel. El JSON se envía
# tal cual: añadir campos aquí cambiaría los valores por defecto del servidor.
_GPT_LIVE_SESSION = json.loads((APP_DIR / "gpt_live_session.json").read_text(encoding="utf-8"))


class OfertaLive(BaseModel):
    sdp: str = Field(min_length=1, max_length=65536)


@app.post("/api/gpt-live/sesion")
def crear_sesion_gpt_live(oferta: OfertaLive, pet: Lector) -> dict:
    """Intercambia el SDP en el servidor; la clave del proyecto no sale al front."""
    clave = config.obtener("OPENAI_API_KEY")
    if not clave:
        raise _no(503, "La conversación en vivo necesita la clave de OpenAI.")
    puede, motivo, codigo = _cobrar(pet)
    if not puede:
        raise _no(403, motivo)
    clave_limite = "gpt-live:" + hashlib.sha256(codigo.encode()).hexdigest() if codigo else None
    if not ui._dentro_del_limite(pet, "gpt-live", LIMITE_GPT_LIVE_HORA, clave=clave_limite):
        _devolver(codigo)
        raise _no(429, ui._mensaje_limite(
            "es", ui._minutos_para_la_siguiente("gpt-live", pet, clave=clave_limite), "voz"))
    import urllib.error
    import urllib.request
    cuerpo = {"session": _GPT_LIVE_SESSION,
              "transport": {"type": "webrtc", "sdp": oferta.sdp}}
    peticion = urllib.request.Request(
        "https://api.openai.com/v1/live/sessions",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Authorization": "Bearer " + clave,
                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(peticion, timeout=25) as r:
            datos = json.loads(r.read())
        sesion_id = datos["session"]["id"]
        respuesta_sdp = datos["transport"]["sdp"]
        if not isinstance(sesion_id, str) or not sesion_id or not isinstance(respuesta_sdp, str) or not respuesta_sdp:
            raise ValueError("Respuesta Live incompleta")
    except Exception as e:
        _devolver(codigo)
        detalle = type(e).__name__
        if isinstance(e, urllib.error.HTTPError):
            detalle += f" HTTP {e.code}"
            try:
                error = json.loads(e.read(2048)).get("error", {})
                codigo_proveedor = error.get("code") if isinstance(error, dict) else None
                if isinstance(codigo_proveedor, str) and re.fullmatch(r"[a-zA-Z0-9_.-]{1,80}", codigo_proveedor):
                    detalle += f" {codigo_proveedor}"
            except (ValueError, OSError):
                pass
        print(f"gpt-live: no se abrió la sesión ({detalle})", file=sys.stderr)
        raise _no(502, "OpenAI no ha abierto la conversación en vivo. Prueba en un momento.") from e
    _programar_cierre_gpt_live(sesion_id)
    return {"session": {"id": sesion_id}, "transport": {"sdp": respuesta_sdp}}


@app.post("/api/lectura/vivo")
def lectura_en_vivo(pet: Lector) -> dict:
    """D5 (25 sep, Miguel): lectura guiada en vivo. Devuelve una clave EFÍMERA
    de OpenAI para una sesión de solo transcripción (`gpt-live-transcribe`) a
    la que el navegador se conecta por WebRTC; la clave de la cuenta nunca sale
    del servidor. Cada sesión cuesta un uso de la cuenta, como «Corrígeme», y
    el front la corta a los `MINUTOS_LECTURA_VIVO` minutos: el modelo cobra por
    minuto de audio. El uso se devuelve si OpenAI no da la clave."""
    if config.falta():
        raise _no(503, "La lectura en vivo necesita la clave de OpenAI.")
    if not ui._dentro_del_limite(pet, "voz", ui.LIMITE_VOZ_HORA):
        raise _no(429, ui._mensaje_limite("es", ui._minutos_para_la_siguiente("voz", pet), "voz"))
    puede, motivo, codigo = _cobrar(pet)
    if not puede:
        raise _no(403, motivo)
    sesion = {"session": {"type": "transcription", "audio": {"input": {
        "format": {"type": "audio/pcm", "rate": 24000},
        "transcription": {"model": "gpt-live-transcribe", "language": "en", "delay": "low",
                          "prompt": "A learner of English reading a book aloud."},
        "noise_reduction": {"type": "near_field"},
        "turn_detection": None}}}}
    import urllib.request
    peticion = urllib.request.Request(
        "https://api.openai.com/v1/realtime/client_secrets", data=json.dumps(sesion).encode(),
        headers={"Authorization": "Bearer " + os.environ.get("OPENAI_API_KEY", ""),
                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(peticion, timeout=20) as r:
            datos = json.loads(r.read())
        valor = datos.get("value")
        if not isinstance(valor, str) or not valor:
            raise ValueError("sin clave efímera")
    except Exception as e:
        _devolver(codigo)
        print(f"lectura vivo: sin clave efímera ({type(e).__name__})", file=sys.stderr)
        raise _no(502, "OpenAI no ha abierto la sesión de lectura en vivo. Prueba en un momento.") from e
    return {"clave": valor, "expira": datos.get("expires_at"), "minutos": MINUTOS_LECTURA_VIVO,
            "restantes": _entrada_json(pet)["restantes"]}


@app.get("/api/articulacion/{acento}/{archivo}")
def corte_de_sonido(acento: Literal["ga", "rp"], archivo: str, quieto: bool = False,
                    dur: float | None = None, una: bool = False):
    """Un sonido: /api/articulacion/ga/θ.svg (ciclo de 2,8 s), ?quieto=1, o
    ?dur=1.4&una=1 (una pasada del largo del audio de «Escuchar y ver»)."""
    simbolo = archivo[:-4] if archivo.endswith(".svg") else ""
    # FastAPI ya decodificó la URL: «iː» llega entero. Solo el inventario del
    # acento, antes de construir nada.
    if simbolo not in _simbolos(acento):
        raise _no(404, "No existe ese sonido.")
    svg = _svg_corte("sonido", simbolo, acento, quieto, *_pasada(dur, una, quieto))
    if not svg:
        raise _no(404, "No existe ese sonido.")
    return Response(svg, media_type="image/svg+xml", headers=_CABECERAS_SVG)


# --- Eos: la cara que habla, para los audios nuevos (28 sep, Miguel) ---------------
# Los 85 sonidos del AFI van pregrabados en el front (front/public/eos/). Aquí solo
# la frase que el lector acaba de leer: se encola y la genera un PC con Eos
# (tools/eos_pronunciar/trabajador.py). Contrato y estados en `app/eos.py`.


class EosPeticion(BaseModel):
    audio: str = Field(min_length=5, max_length=170)
    texto: str = Field(default="", max_length=600)


def _nombre_audio_de(audio: str) -> str:
    """Acepta «/api/audio/x.mp3» o «x.mp3»; solo mp3 que existan en la caché de audio."""
    nombre = audio.rsplit("/", 1)[-1]
    if not eos.nombre_audio_valido(nombre) or not (_DIR_AUDIO / nombre).is_file():
        raise _no(404, "No existe ese audio.")
    return nombre


@app.post("/api/eos/pedir")
def eos_pedir(pet: Lector, peticion: EosPeticion) -> dict:
    """Encola el vídeo de Eos leyendo un mp3 generado (audio_correcto). Sin coste."""
    return eos.pedir(_nombre_audio_de(peticion.audio), peticion.texto)


@app.get("/api/eos/estado/{clave}")
def eos_estado(clave: str) -> dict:
    return eos.estado(clave)


@app.get("/api/eos/video/{archivo}")
def eos_video(archivo: str):
    if not re.fullmatch(r"[0-9a-f]{24}\.mp4", archivo):
        raise _no(404, "No existe ese vídeo.")
    p = eos.ruta_video(archivo[:-4])
    if not p.is_file() or p.stat().st_size == 0:
        raise _no(404, "No existe ese vídeo.")
    # FileResponse de Starlette contesta a Range (el móvil lo pide para el <video>).
    return FileResponse(p, media_type="video/mp4",
                        headers={"Cache-Control": "public, max-age=2592000",
                                 "X-Content-Type-Options": "nosniff"})


def _trabajador(request: Request) -> None:
    if not eos.token_valido(request.headers.get("X-Eos-Token")):
        raise _no(403, "Este acceso es solo para el trabajador de Eos.")


@app.get("/api/eos/cola")
def eos_cola(request: Request) -> dict:
    _trabajador(request)
    return {"trabajos": [{**t, "audio_url": f"/api/audio/{t['audio']}"} for t in eos.cola()
                         if eos.nombre_audio_valido(t.get("audio"))]}


@app.post("/api/eos/entregar/{clave}")
async def eos_entregar(clave: str, request: Request) -> dict:
    _trabajador(request)
    if not eos.clave_valida(clave):
        raise _no(404, "No existe ese trabajo.")
    contenido = bytearray()
    async for trozo in request.stream():
        contenido += trozo
        if len(contenido) > eos.TOPE_MP4:
            raise _no(413, "El vídeo es demasiado grande.")
    if not eos.entregar(clave, bytes(contenido)):
        raise _no(422, "Eso no es un mp4.")
    return {"estado": "listo", "clave": clave, "video": f"/api/eos/video/{clave}.mp4"}


class EosFallo(BaseModel):
    motivo: str = Field(default="", max_length=300)


@app.post("/api/eos/fallo/{clave}")
def eos_fallo(clave: str, request: Request, cuerpo: EosFallo) -> dict:
    _trabajador(request)
    if not eos.fallo(clave, cuerpo.motivo):
        raise _no(404, "No existe ese trabajo.")
    return {"estado": "fallo", "clave": clave}


# --- Punto 5: pronunciacion ------------------------------------------------------

_EXT_AUDIO = {".webm", ".ogg", ".oga", ".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga"}
_TOPE_AUDIO = 10 * 1024 * 1024


def _fonema_json(simbolo, acento: str = "US") -> dict | None:
    """El sonido que falla, en el acento de la corrección.

    `voz` da el símbolo del inventario americano. Con acento UK se busca el RP
    con esa clave (entrega-4e: 39 de 41 uno a uno; ɹ→r, oʊ→əʊ, i→iː…). /ɝ/ y
    /ɚ/ no tienen equivalente en RP, que no pronuncia la r: se quedan en
    americano, con `acento` «ga» para que el front pida su corte en «ga»."""
    f = fonemas.buscar(simbolo)
    if f is None:
        return None
    datos = {"simbolo": f.simbolo, "nombre": f.nombre, "ejemplos": list(f.ejemplos),
             "audio": _url_audio_fonema(f.ruta, "/api/fonemas/"), "acento": "ga"}
    if acento == "UK":
        rp = next((s for s in articulacion.INVENTARIO_RP if s.clave == f.simbolo), None)
        if rp is not None:
            datos.update(simbolo=rp.simbolo, nombre=rp.nombre, ejemplos=list(rp.ejemplos),
                         audio=_url_audio_fonema(rp.ruta, "/api/fonemas/rp/"), acento="rp")
    return datos


def _audio_de_detalle(normal: list[str], audios: dict[str, str]) -> str | None:
    """El mp3 de la palabra de un detalle de la corrección.

    `voz` guarda el audio con la clave de la palabra fallada tal cual se
    normalizó, y conserva los guiones: «war-chant» es UNA palabra. Pero la
    corrección de GPT la parte en «war» y «chant», y ninguna casaba (Miguel, 13
    sep: «no me dejas escuchar la palabra sola»). Sin audio propio, vale el del
    compuesto que la contiene."""
    if not normal:
        return None
    propio = audios.get(normal[0])
    if propio:
        return propio
    for clave, ruta in audios.items():
        if normal[0] in clave.split("-"):
            return ruta
    return None


@app.post("/api/voz")
async def practicar(pet: Lector, request: Request) -> dict:
    """La corrección de pronunciacion, con las guardas de `ui._practicar`.

    Campos del formulario: `frase` (hasta 2000), `audio` (archivo) y `acento`
    (US | UK). Se leen con `_formulario`, con tope antes de interpretarlo."""
    formulario = await _formulario(request, _TOPE_AUDIO, "La grabación es demasiado larga.")
    try:
        frase = formulario.get("frase")
        acento = formulario.get("acento") or "US"
        audio = formulario.get("audio")
        if not isinstance(frase, str) or len(frase) > 2000:
            raise _no(422, "Escribe la frase que vas a leer en voz alta.")
        if acento not in ("US", "UK"):
            raise _no(422, "El acento es US o UK.")
        if audio is None or isinstance(audio, str):
            raise _no(422, "No me ha llegado audio. Graba la frase otra vez.")
        ext = os.path.splitext(str(audio.filename or "").lower())[1] or ".webm"
        contenido = await audio.read(_TOPE_AUDIO + 1)
    finally:
        await formulario.close()
    return await run_in_threadpool(_corregir_voz, pet, frase, acento, ext, contenido)


def _corregir_voz(pet: _Lector, frase: str, acento: str, ext: str, contenido: bytes) -> dict:
    """Lo que sigue a leer la grabación, EN UN HILO: whisper, gpt y tts-1 tardan
    segundos, y en el bucle de eventos congelaban el proceso entero. Medido con un
    doble de `voz.practicar` de 4 s: /api/salud tardó 3,41 s (auditoría cruzada de
    4e, 14 sep 2026)."""
    frase = frase.strip()[:ui.LIMITE_FRASE_VOZ]
    if not frase:
        raise _no(422, "Escribe la frase que vas a leer en voz alta.")
    if ext not in _EXT_AUDIO:
        ext = ".webm"
    if len(contenido) > _TOPE_AUDIO:
        raise _no(413, "La grabación es demasiado larga.")
    if len(contenido) < 800:
        raise _no(422, "No me ha llegado audio. Graba la frase otra vez.")
    fd, tmp = None, None
    try:
        # Preparar el archivo es local: si falla, no debe consumir cuota.
        try:
            fd, tmp = tempfile.mkstemp(suffix=ext, prefix="ll_voz_")
            archivo = os.fdopen(fd, "wb")
            fd = None  # El descriptor ya pertenece al objeto archivo.
            with archivo as f:
                f.write(contenido)
        except OSError as e:
            raise _no(500, "No he podido preparar la grabación en el servidor.") from e
        if _va_a_costar(pet) and not ui._dentro_del_limite(pet, "voz", ui.LIMITE_VOZ_HORA):
            raise _no(429, ui._mensaje_limite("es", ui._minutos_para_la_siguiente("voz", pet),
                                              "voz"))
        if config.falta():
            raise _no(503, "Para corregir la pronunciación hace falta la clave de OpenAI. "
                           "Lo demás de la aplicación no la necesita.")
        # El codigo se lee UNA vez y va al cobro y a la devolucion por silencio: si la sesion cambia de
        # cuenta a mitad, se cobra y se devuelve a la misma (reinicio 27, con e6: `ui._puede_pagar`
        # cobra al codigo que se le pasa sin releer la sesion).
        codigo = ui._codigo_de(pet)
        puede, motivo = ui._puede_pagar(pet, codigo)
        if not puede:
            raise _no(403, motivo)
        devuelto = False
        try:
            # Desde aqui puede haber gasto aunque falle la transcripcion.
            # El nivel del lector fija la velocidad objetivo del ritmo (4e, 9f5f909).
            perfil = _perfil_de(pet)
            s = voz.practicar(tmp, frase, guardar_fallos=False,
                              nivel=perfil.nivel if perfil is not None else None, origen="api")
            # Whisper respondio y no oyo nada: el uso se devuelve, con el tope diario de cuentas
            # (Central, reinicio 26). Con la red o la clave caidas, `sin_voz` es False y no.
            if getattr(s, "sin_voz", False) and cuentas.devolver_por_silencio(ui.BASE_DATOS_LECTOR, codigo):
                devuelto = True
            if s.evaluacion.palabras_falladas and s.transcripcion_ok:
                voz.registrar_fallos(s.evaluacion.palabras_falladas,
                                     ruta=ui._archivo_lector("voz.db", pet), frase=frase)
            # Solo guarda si se midió, y no lanza (4e, b41ff5e).
            if getattr(s, "ritmo", None) is not None:
                voz.registrar_ritmo(s.ritmo, frase, ruta=ui._archivo_lector("voz.db", pet))
        except Exception as e:
            raise _no(502, f"No he podido corregir la grabación ({type(e).__name__}).") from e
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    ev = s.evaluacion
    falladas = set(ev.palabras_falladas)
    detalles = []
    # El mp3 de cada palabra fallada, sola (`voz` lo genera dentro del mismo uso
    # de pago y lo cachea por contenido). `getattr`: sesiones sin ese campo.
    audios = getattr(s, "audios_palabras", None) or {}
    if s.correccion:
        for d in s.correccion.detalles:
            cruda = str(getattr(d, "palabra", "") or "").strip()
            # El mismo acento para toda la corrección, el que el lector eligió
            # en Pronunciar: «war» salía US y «chant» UK en la misma lista.
            ipa, variante = fonemas.ipa_de_palabra(cruda, acento=acento)
            normal = voz.normalizar_palabras(cruda)
            detalles.append({
                "palabra": cruda, "ipa": ipa, "variante": variante,
                "audio": _url_audio(_audio_de_detalle(normal, audios)),
                "fonema": _fonema_json(getattr(d, "fonema", None), acento),
                "sonido_que_falla": str(getattr(d, "sonido_que_falla", "") or "").strip(),
                "como_colocar_la_boca": str(getattr(d, "como_colocar_la_boca", "") or "").strip(),
            })
    return {
        "puntuacion": round(float(ev.puntuacion)),
        "transcripcion_ok": s.transcripcion_ok, "transcripcion": ev.transcripcion,
        "palabras": [{"palabra": w, "bien": w not in falladas} for w in ev.palabras_objetivo],
        "entendidas": [list(par) for par in getattr(ev, "entendidas", [])],
        "resumen": s.correccion.resumen if s.correccion else None,
        "detalles": detalles, "audio_correcto": _url_audio(s.audio_correcto),
        "restantes": _entrada_json(pet)["restantes"],
        "uso_devuelto": devuelto,
        "ritmo": _ritmo_json(getattr(s, "ritmo", None)),
    }


def _ritmo_json(ritmo: dict | None) -> dict | None:
    """El ritmo de `voz` tal cual (4e: 9f5f909 y 55d546c), salvo el mp3 de la
    frase dicha con naturalidad, que llega como ruta local y sale como URL,
    igual que `audio_correcto`. Índices sobre `palabras`."""
    if not isinstance(ritmo, dict):
        return None
    ritmo = dict(ritmo)
    natural = ritmo.get("natural")
    if isinstance(natural, dict):
        ritmo["natural"] = {**natural, "audio_natural": _url_audio(natural.get("audio_natural"))}
    return ritmo


def _historial_voz(leer) -> tuple[list, str | None]:
    """(filas, aviso). Sin base de voz, filas vacías y sin aviso. Con la base
    existente pero ilegible, `voz` lanza HistorialIlegible (4e, d765ee0) con un
    mensaje en español: vacío a secas decía «no has fallado nada». Con un voz.py
    anterior no hay esa clase y `except ()` no atrapa nada."""
    try:
        return leer(), None
    except getattr(voz, "HistorialIlegible", ()) as e:
        return [], str(e)


@app.get("/api/voz/debiles")
def debiles(pet: Lector) -> dict:
    filas, aviso = _historial_voz(lambda: voz.puntos_debiles(n=15, ruta=ui._archivo_lector("voz.db", pet)))
    return {"palabras": [{"palabra": w, "fallos": n} for w, n in filas], "aviso": aviso}


@app.get("/api/voz/falladas")
def falladas(pet: Lector, n: int = Query(15, ge=1, le=50)) -> dict:
    """Las palabras que peor pronuncia este lector, con la frase donde falló.
    Sin red y gratis: lee su `voz.db`."""
    filas, aviso = _historial_voz(
        lambda: voz.palabras_para_practicar(n=n, ruta=ui._archivo_lector("voz.db", pet)))
    return {"palabras": [{"palabra": f["palabra"], "fallos": f["fallos"],
                          "ultima_vez": f.get("ultima_vez"), "frase": f.get("frase")}
                         for f in filas], "aviso": aviso}


@app.get("/api/voz/ritmo")
def ritmo_de_una_frase(pet: Lector, frase: str = Query(..., min_length=1, max_length=300)) -> dict:
    """Cómo ha ido cambiando el ritmo de este lector con esa frase (4e, b41ff5e),
    del intento más antiguo al más reciente. Sin red y gratis: lee su voz.db;
    si no se puede leer, aviso en vez de una lista vacía que lo esconda."""
    filas, aviso = _historial_voz(
        lambda: voz.evolucion_ritmo(frase.strip(), n=10, ruta=ui._archivo_lector("voz.db", pet)))
    return {"intentos": list(filas), "aviso": aviso}


# --- Lo tuyo: cuaderno, repaso, biblioteca e inicio -----------------------------

def _cita(oracion: str | None, palabra: str | None) -> str:
    """Lo que se ENSEÑA de una oración larga: la cláusula donde está la palabra
    (`ui._fragmento_para_leer`, 4e, 1a4b998). La oración entera sigue en
    «oracion»: es el contexto de OpenAI y lo que guarda el cuaderno. Sin esa
    función (un ui.py anterior) o si falla, la oración entera."""
    oracion = oracion or ""
    fragmentar = getattr(ui, "_fragmento_para_leer", None)
    if fragmentar is None or not oracion:
        return oracion
    try:
        return fragmentar(oracion, palabra or "") or oracion
    except Exception:
        return oracion


def _anotacion_json(a) -> dict:
    return {"palabra": a.palabra, "lema": a.lema, "categoria": a.categoria,
            "sentido": a.sentido, "oracion": a.oracion, "cita": _cita(a.oracion, a.palabra),
            "libro": a.libro, "capitulo": a.capitulo, "rareza": a.rareza or None, "creado": a.creado}


@app.get("/api/cuaderno")
def mis_palabras(pet: Lector, n: int = 50) -> dict:
    db = ui._archivo_lector("cuaderno.db", pet)
    total, lemas, libros = cuaderno.contar(db)
    return {"consultas": total, "palabras": lemas, "libros": libros,
            "entradas": [_anotacion_json(a)
                         for a in cuaderno.ultimas(max(1, min(int(n), 200)), db)]}


@app.get("/api/repaso")
def repaso(pet: Lector) -> dict:
    """Sin nota y sin racha: un recordatorio, no un examen (`enganche.md` §5).

    Cada tarjeta lleva su `consulta_id` (D3.2): es lo que el front manda de
    vuelta al evaluar, para que el servidor sepa EXACTAMENTE qué consulta
    respondió, sin fiarse de nada más que mande el cliente.
    """
    anotaciones = cuaderno.para_repasar(5, ui._archivo_lector("cuaderno.db", pet))
    # Con el historial de voz ilegible, el cuaderno se enseña igual y la parte
    # de voz va vacía con su aviso.
    filas, aviso = _historial_voz(lambda: voz.puntos_debiles(n=5, ruta=ui._archivo_lector("voz.db", pet)))
    return {"palabras": [{**_anotacion_json(a), "consulta_id": a.id} for a in anotaciones],
            "voz": [{"palabra": w, "fallos": n} for w, n in filas], "aviso_voz": aviso}


class RepasoEvaluacion(BaseModel):
    consulta_id: int
    evaluacion: Literal["no", "dude", "si"]


@app.post("/api/repaso")
def evaluar_repaso(datos: RepasoEvaluacion, pet: Lector) -> dict:
    """Guarda una evaluación de repaso (D3.2): No/Dudé/Sí sobre una tarjeta
    concreta, identificada por `consulta_id` — nunca por lo que el front
    diga que era la palabra/frase, que se recalcula aquí desde el propio
    cuaderno de este lector (`cuaderno.registrar_repaso`).

    A diferencia de `cuaderno.registrar()` (que se calla y sigue si no
    puede escribir), aquí SÍ se informa del fallo: el front no debe fingir
    que guardó algo que no se guardó.
    """
    db = ui._archivo_lector("cuaderno.db", pet)
    if cuaderno.por_id(datos.consulta_id, db) is None:
        raise _no(404, "Esa palabra no está en tu cuaderno.")
    if not cuaderno.registrar_repaso(consulta_id=datos.consulta_id, evaluacion=datos.evaluacion, ruta=db):
        raise _no(500, "No se pudo guardar tu repaso. Vuelve a intentarlo.")
    return {"ok": True}


@app.get("/api/progreso")
def progreso(pet: Lector, tz: str | None = None) -> dict:
    """Agregados para «Mi progreso» (D3.3): nunca anotaciones completas, solo
    lo mínimo para dibujar dos gráficas pequeñas.

    `tz` es la zona IANA real del navegador
    (`Intl.DateTimeFormat().resolvedOptions().timeZone`), nunca la zona del
    servidor; si falta o no es una zona válida, `cuaderno.por_dia` degrada a
    UTC sola, sin lanzar.
    """
    db = ui._archivo_lector("cuaderno.db", pet)
    dias = cuaderno.por_dia(tz, 14, db)
    evaluaciones = cuaderno.ultimos_repasos(20, db)
    conteo = {"si": 0, "dude": 0, "no": 0}
    for e in evaluaciones:
        if e in conteo:
            conteo[e] += 1
    return {
        "palabras_por_dia": [{"fecha": f, "consultas": c} for f, c in dias],
        "repasos": {**conteo, "total": len(evaluaciones)},
    }


def _estanteria(pet: _Lector) -> list[dict]:
    db = ui._archivo_lector("cuaderno.db", pet)
    por_libro: dict[str, int] = {}
    for a in cuaderno.ultimas(500, db):
        if a.libro:
            por_libro[a.libro] = por_libro.get(a.libro, 0) + 1
    fuera = []
    for e in biblioteca.listar(ui._archivo_lector("biblioteca.json", pet)):
        ident = _id_de_ruta(e.ruta, pet) if e.existe else None
        if ident is None:
            continue
        fuera.append({"id": ident, "titulo": e.titulo, "autor": ui._autor_corto(e.autor),
                      "capitulo": e.capitulo, "capitulos": e.capitulos,
                      "avance": round(e.avance, 3), "palabras": e.palabras,
                      "visto": e.visto, "consultadas": por_libro.get(e.titulo, 0)})
    return fuera


@app.get("/api/biblioteca")
def mis_libros(pet: Lector) -> dict:
    return {"libros": _estanteria(pet)}


@app.delete("/api/biblioteca/{libro_id}")
def olvidar_libro(libro_id: str, pet: Lector) -> dict:
    ident = _normalizar_id(libro_id)
    ruta = next((e.ruta for e in biblioteca.listar(ui._archivo_lector("biblioteca.json", pet))
                 if _id_de_ruta(e.ruta, pet) == ident), None)
    if ruta:
        biblioteca.olvidar(ruta, ui._archivo_lector("biblioteca.json", pet))
    return {"ok": True}


@app.delete("/api/libros/{libro_id}")
def borrar_subido(libro_id: str, pet: Lector) -> dict:
    """Borra de verdad un libro subido: archivo, nombre guardado, entrada de
    «Mis libros» y caché de memoria.

    Quitarlo solo de la biblioteca (DELETE /api/biblioteca) dejaba el archivo
    ocupando uno de los 30 huecos y el 429 no se iba nunca (auditoría de Codex,
    4). Solo libros subidos, y solo en la carpeta de este lector."""
    ident = _normalizar_id(libro_id)
    if not ident.startswith("u"):
        raise _no(400, "Solo se pueden borrar los libros que hayas subido tú.")
    carpeta = _dir_subidos(pet)
    borrados = 0
    # Todo bajo el candado de subidas: con el archivo borrado fuera, una subida a la vez
    # podía contarlo todavía o apuntar su nombre después del borrado (ronda 3 de e6).
    with _candado_subidas(pet):
        for ext in _EXT_LIBRO:
            p = carpeta / f"{ident[1:]}{ext}"
            if not p.is_file():
                continue
            with _CANDADO_LIBROS:
                for clave in [k for k in _LIBROS if k[0] == str(p)]:
                    del _LIBROS[clave]
            biblioteca.olvidar(str(p), ui._archivo_lector("biblioteca.json", pet))
            p.unlink(missing_ok=True)
            borrados += 1
        if not borrados:
            raise _no(404, "Ese libro ya no está en el servidor.")
        try:
            ruta = _nombres_subidos(pet)
            nombres = json.loads(ruta.read_text("utf-8"))
            if isinstance(nombres, dict) and nombres.pop(ident, None) is not None:
                _escribir_nombres(ruta, nombres)
        except (OSError, ValueError):
            pass
    return {"ok": True}


@app.get("/api/inicio")
def inicio(pet: Lector) -> dict:
    """Todo lo de la portada en UNA llamada: en el movil cada viaje cuesta.

    «Seguir leyendo» primero (`retencion_movil.md`, recomendacion 1): retomar
    donde lo dejaste es la mecanica de retencion mas honesta que hay.
    """
    estanteria = _estanteria(pet)
    seguir = None
    if estanteria:
        e = estanteria[0]
        seguir = dict(e)
        try:
            _, lib = _abrir(e["id"], pet, descargar=False)
            if 0 <= e["capitulo"] < len(lib.capitulos):
                c = lib.capitulos[e["capitulo"]]
                seguir["titulo_capitulo"] = c.titulo
                # Los párrafos LIMPIOS del lector (`_parrafos`: sin la licencia de
                # Gutenberg ni la portadilla), no el texto crudo: con el progreso
                # en el capítulo 0, «Donde lo dejaste» enseñaba la licencia (b9).
                parrafos = [p for p in _parrafos(lib, e["capitulo"])
                            if len(p.split()) >= 25 and not _es_preambulo(p) and not _parece_indice(p)]
                if parrafos:
                    frases = ui._oraciones(ui._sin_encabezado(parrafos[0]))
                    seguir["extracto"] = " ".join(frases[:2])[:280] if frases else None
        except HTTPException:
            pass
    total, lemas, libros = cuaderno.contar(ui._archivo_lector("cuaderno.db", pet))
    return {"perfil": _perfil_json(_perfil_de(pet)), "seguir": seguir,
            "libros": len(estanteria),
            "cuaderno": {"consultas": total, "palabras": lemas, "libros": libros},
            "entrada": _entrada_json(pet)}


# --- Montaje junto a Gradio -------------------------------------------------------

def _precarga_activada() -> bool:
    """En el Space (SPACE_ID) o si se pide (LITERALEVEL_PRECARGA=1). LITERALEVEL_PRECARGA=0 la apaga
    aunque haya SPACE_ID: pruebas_api simula el Space con SPACE_ID y llama a para_gradio(), y sin
    esto lanzaba una precarga real con el catalogo y el modelo en mitad de la suite."""
    marca = os.environ.get("LITERALEVEL_PRECARGA", "")
    if marca == "0":
        return False
    return bool(os.environ.get("SPACE_ID") or marca == "1")


def _precargar() -> None:
    """Lo que tardaba la primera busqueda con nivel en el Space: 18,6 s (reinicio 25). Medido en
    local: catalogo +287 MB en 2,4 s, modelo MiniLM +652 MB en 18,7 s, .npy de titulos +76 MB y la
    primera busqueda, con los indices de nombres, +163 MB en 3,9 s; la segunda, 0,4 s. Es la misma
    memoria que ocupa la primera busqueda de cualquiera; aqui se ocupa al arrancar. Una peticion que
    llegue a mitad espera a la misma instancia en el candado de `ui.catalogo()`. Si algo falla, se
    dice y la carga perezosa de siempre sigue."""
    t0 = time.time()
    try:
        cat = ui.catalogo()
        cat.embeddings
        t1 = time.time()
        cat.buscar("historias de fantasmas", nivel_lector=0.8, n=1, franja=True)
        titulos = "si" if cat.emb_titulos() is not None else "no"
        print(f"api precarga: catalogo {t1 - t0:.1f} s; modelo, titulos ({titulos}) y primera busqueda "
              f"{time.time() - t1:.1f} s", file=sys.stderr)
    except Exception as e:
        print(f"api precarga: no ha podido ({type(e).__name__}: {e}); se cargara con la primera busqueda",
              file=sys.stderr)


def precargar_en_segundo_plano() -> threading.Thread | None:
    """Arranca `_precargar` en un hilo de fondo si toca; no retrasa el arranque ni /api/salud."""
    if not _precarga_activada():
        return None
    hilo = threading.Thread(target=_precargar, name="precarga-buscador", daemon=True)
    hilo.start()
    return hilo


def _memoria_del_proceso() -> dict:
    """La memoria del proceso en MB, de /proc/self/status (Linux, el Space): la de ahora y el pico.
    None donde no hay /proc. Sin rutas ni nada del lector: /api/estado es publica."""
    fuera = {"memoria_mb": None, "pico_mb": None}
    try:
        for linea in Path("/proc/self/status").read_text().splitlines():
            clave, _, valor = linea.partition(":")
            if clave in ("VmRSS", "VmHWM"):
                fuera["memoria_mb" if clave == "VmRSS" else "pico_mb"] = round(int(valor.split()[0]) / 1024)
    except (OSError, ValueError, IndexError):
        pass
    return fuera


def para_gradio() -> dict:
    """Lo que se pasa a `demo.launch(ssr_mode=False, app_kwargs=api.para_gradio())`.

    **Así es como se monta en un Space de Gradio, y no con `con_gradio`.** El
    primer intento (13 de septiembre de 2026) arrancó un uvicorn propio con
    `con_gradio` y el Space dio 502/503: allí Hugging Face arranca Gradio con
    SSR, que pone un proxy de Node en el puerto público y Python detrás. Y ese
    proxy solo pasa a Python una lista fija de prefijos
    (`templates/node/build/proxy_routes.js`: `/gradio_api`, `/config`,
    `/login`...). `/api` no está en la lista, así que aunque las rutas existan,
    con SSR cada `/api/*` devuelve la página de Gradio con un 200.

    Con `ssr_mode=False`, Python atiende el puerto directamente, que es como
    corre la app en local desde siempre. Las rutas van en el CONSTRUCTOR de la
    app FastAPI que crea el propio Gradio (`App(**app_kwargs)`), así que se
    registran antes que las suyas y ganan. El CORS lo pone el middleware de
    Gradio, que acepta cualquier origen fuera de localhost y devuelve las
    cabeceras pedidas, `X-Lector` incluida.
    """
    rutas = [r for r in app.router.routes if str(getattr(r, "path", "")).startswith("/api/")]
    # El Space solo pasa por aqui al arrancar (app.py): es donde se lanza la precarga (reinicio 26).
    precargar_en_segundo_plano()
    return {"routes": rutas, "exception_handlers": {Exception: _error_inesperado,
                                                    RequestValidationError: _validacion_sin_eco}}


def con_gradio(demo=None):
    """La API en `/api` y Gradio en `/`, en un solo proceso, con uvicorn propio.

    **Solo para local.** En un Space de Gradio no vale: ver `para_gradio`.
    Las rutas de la API se registran antes que el montaje de `/`, asi que ganan.
    """
    import gradio as gr
    demo = demo if demo is not None else ui.construir()
    return gr.mount_gradio_app(app, demo, path="/", allowed_paths=ui.RUTAS_PERMITIDAS,
                               max_file_size=ui.TAMANO_MAXIMO_SUBIDA, theme=ui.TEMA)


if __name__ == "__main__":
    import uvicorn
    nube = bool(os.environ.get("SPACE_ID") or os.environ.get("PORT"))
    uvicorn.run(con_gradio(), host="0.0.0.0" if nube else "127.0.0.1",
                port=int(os.environ.get("PORT", 7860)))
