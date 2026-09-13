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

import hashlib
import math
import os
import re
import sys
import tempfile
import threading
import time
import traceback
import uuid
from collections import OrderedDict
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Literal

APP_DIR = Path(__file__).resolve().parent
RAIZ = APP_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

import articulacion  # noqa: E402
import biblioteca  # noqa: E402
import config  # noqa: E402
import cuaderno  # noqa: E402
import cuentas  # noqa: E402
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

# El front vive en otro origen: `ng serve` en local y un Space estatico en
# produccion. Sin credenciales -la identidad va en una cabecera propia, no en
# una cookie-, asi que un origen de mas no abre la puerta a leer datos ajenos.
_ORIGENES = [o.strip() for o in os.environ.get("LITERALEVEL_ORIGENES", "").split(",")
             if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGENES,
    allow_origin_regex=(r"^(https://[a-z0-9-]+\.(static\.)?hf\.space"
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
            raise _no(429, f"Has abierto {ui.LIMITE_DESCARGAS_HORA} libros nuevos "
                           f"en esta hora. Espera "
                           f"{ui._minutos_para_la_siguiente('descargas', pet)} "
                           "minutos o sigue con los que ya tienes.")
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
    return ruta, _cargar_libro(ruta)


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
    """
    palabras = re.findall(r"[^\W\d_]+|\d+", texto)
    if not palabras:
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


def _libro_tarjeta(b) -> dict:
    """Un resultado del catalogo, listo para pintarse en una tarjeta."""
    dificultad = _finito(b.dificultad)
    return {"id": b.id, "titulo": b.titulo, "autor": ui._autor_corto(b.autor),
            "nivel": b.nivel, "dificultad": dificultad,
            "gancho": " ".join(str(b.gancho or "").split()),
            "descargas": b.descargas, "similitud": b.similitud,
            "afinidad": b.afinidad, "abrible": ui._abrible(b.id),
            "url": b.url_gutenberg}


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
            "tiempo": (ficha.reloj(c.minutos(exigente)) if exigente is not None
                       else f"entre {ficha.reloj(c.minutos(False))} y "
                            f"{ficha.reloj(c.minutos(True))}"),
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
                        "consultor": ui._consultor is not None}}


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


@app.post("/api/perfil/muestra")
def perfil_muestra(datos: MuestraPeticion, pet: Lector) -> dict:
    texto = datos.texto.strip()
    # El filtro ANTES de cargar el modelo, como en `ui._desde_muestra`.
    ok, motivo = scoring.continuous_prose(texto)
    if not ok:
        raise _no(422, scoring._MOTIVOS.get(motivo, motivo))
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
    try:
        r = _puntuar(muestra)
    except ValueError as e:
        raise _no(422, str(e)) from e
    except Exception as e:
        raise _no(503, f"No he podido cargar el modelo ({type(e).__name__}).") from e
    p = perfil_mod.Perfil(nivel=r.puntuacion, banda=r.banda, origen="muestra",
                          creado=perfil_mod._ahora(), nombre=datos.nombre.strip())
    p.guardar(ui._archivo_lector("perfil.json", pet))
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
        libros, aviso = ui.catalogo().buscar(datos.consulta, nivel_lector=nivel, n=datos.n)
    except Exception as e:
        raise _no(503, f"El buscador no está disponible ahora mismo ({type(e).__name__}).") from e
    return {"resultados": [_libro_tarjeta(b) for b in libros], "aviso": aviso,
            "ajustado": nivel is not None, "nivel": nivel, "nota": _llano(ui._nota_nivel())}


@app.get("/api/recomendar")
def recomendar(pet: Lector, n: int = 10) -> dict:
    """«Sorprendeme»: lo mas leido cerca de tu nivel, pandas puro (0,01 s)."""
    n = max(1, min(int(n), 30))
    p = _perfil_de(pet)
    if p is None:
        return {"resultados": [], "necesita_perfil": True, "rango": None, "rescate": False}
    cat = ui.catalogo()
    libros = cat.por_nivel(p.nivel, holgura=ui.HOLGURA_POR_NIVEL, n=n)
    rescate = False
    # Nunca un callejon: si nada de tu nivel se abre, lo mas facil que si.
    if libros and not any(ui._abrible(b.id) for b in libros):
        faciles = [b for b in cat.por_nivel(p.nivel, holgura=3.0, n=200) if ui._abrible(b.id)]
        if faciles:
            faciles.sort(key=lambda b: scoring.ANCHORS.index(b.nivel)
                         if b.nivel in scoring.ANCHORS else 9)
            libros, rescate = faciles[:n], True
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
async def subir_libro(pet: Lector, archivo: UploadFile = File(...)) -> dict:
    """Sube un `.epub`, `.pdf` o `.txt` propio. Solo lo ve este lector."""
    nombre = str(archivo.filename or "").lower()
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
        # Un epub es un zip: sin tope cabe una bomba de descompresion.
        if total > _TOPE_SUBIDA:
            raise _no(413, "El archivo pasa de 20 MB.")
        h.update(trozo)
        trozos.append(trozo)
    if not total:
        raise _no(422, "El archivo está vacío.")
    ident = "u" + h.hexdigest()[:16]
    carpeta = _dir_subidos(pet)
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"{ident[1:]}{ext}"
    if not destino.exists():
        destino.write_bytes(b"".join(trozos))
    try:
        lib = _cargar_libro(str(destino))
    except HTTPException:
        destino.unlink(missing_ok=True)
        raise
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
    try:
        r = _puntuar(ficha.sin_licencia(c.texto))
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
                    vs = p.perfil_de_texto(ficha.sin_licencia(c.texto),
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


@app.post("/api/libros/{libro_id}/sinopsis")
def sinopsis(libro_id: str, pet: Lector) -> dict:
    """«¿De que trata?», con las mismas guardas que `ui._de_que_trata`."""
    ident = _normalizar_id(libro_id)
    _, lib = _abrir(ident, pet, descargar=False)
    datos = ui._sinopsis_guardada(lib)
    if datos is not None:
        return {"sinopsis": datos}
    if _va_a_costar(pet) and not ui._dentro_del_limite(pet, "sinopsis",
                                                      ui.LIMITE_SINOPSIS_HORA):
        raise _no(429, ui._mensaje_limite("es", ui._minutos_para_la_siguiente("sinopsis", pet)))
    if config.falta():
        raise _no(503, "Para el resumen hace falta la clave de OpenAI. La ficha "
                       "contada no la necesita.")
    puede, motivo = ui._puede_pagar(pet)
    if not puede:
        raise _no(403, motivo)
    try:
        cliente = ui.consultor()._cliente()
    except Exception as e:
        cuentas.devolver(ui.BASE_DATOS_LECTOR, ui._codigo_de(pet))
        raise _no(503, f"No he podido preparar el resumen ({type(e).__name__}).") from e
    if cliente is None:
        cuentas.devolver(ui.BASE_DATOS_LECTOR, ui._codigo_de(pet))
        raise _no(503, "Para el resumen hace falta la clave de OpenAI.")
    datos, causa = ficha.sinopsis(lib, cliente)
    if datos is None:
        if causa in ("sin_red", "sin_pasajes"):
            cuentas.devolver(ui.BASE_DATOS_LECTOR, ui._codigo_de(pet))
        raise _no(502, "No he podido preparar el resumen ahora mismo."
                  + ("" if causa in ("sin_red", "sin_pasajes")
                     else " Este intento sí ha consumido uno de tus usos."))
    try:
        ui.RUTA_ANALISIS.mkdir(parents=True, exist_ok=True)
        import json
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
    avisos = [a for a in r.avisos if "no esta en el diccionario" not in a]
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
        with _CANDADO_LEXICO:
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
                                              ui._minutos_para_la_siguiente("lexico", pet)))
        with _CANDADO_LEXICO:
            try:
                if config.falta():
                    puede, motivo = False, ""
                else:
                    puede, motivo = ui._puede_pagar(pet)
                r = ui.consultor().consultar(palabra_, oracion, _nivel(pet), idioma=idioma,
                                             usar_openai=puede)
            except Exception as e:
                cuentas.devolver(ui.BASE_DATOS_LECTOR, ui._codigo_de(pet))
                raise _no(503, f"El diccionario no está disponible ({type(e).__name__}).") from e
        if not puede and motivo:
            r.avisos = [a for a in r.avisos if "OPENAI_API_KEY" not in a] + [motivo]
        elif puede and getattr(r, "llamadas_de_pago", 0) == 0:
            cuentas.devolver(ui.BASE_DATOS_LECTOR, ui._codigo_de(pet))
        registrar = bool(r.sentido)
        avisos = _avisos_palabra(r, idioma, quitar_sin_clave=False)

    if registrar:
        cuaderno.registrar(
            palabra=r.palabra_superficie, lema=r.lema_buscado or r.lema, oracion=oracion,
            categoria=r.categoria, sentido=r.sentido,
            libro=(getattr(lib, "titulo_visible", None) if lib is not None else None),
            capitulo=(idx + 1 if idx is not None else None),
            banda=r.banda_lector, zipf=r.frecuencia_zipf,
            ruta=ui._archivo_lector("cuaderno.db", pet))

    ya_avisado = any("margen bajo" in a or "provisional" in a for a in r.avisos)
    dudoso = bool(not ya_avisado and r.similitud is not None
                  and r.n_sentidos_candidatos > 1 and r.similitud < ui.AFINIDAD_DUDOSA)
    zipf = r.frecuencia_zipf
    rareza = (None if zipf is None else "muy_comun" if zipf >= 5 else
              "frecuente" if zipf >= 4 else "poco_frecuente" if zipf >= 3 else "rara")
    return {
        "etapa": datos.etapa, "palabra": r.palabra_superficie[:ui.LIMITE_PALABRA],
        "lema": r.lema_buscado or r.lema, "categoria": r.categoria,
        "ipa_uk": r.ipa_uk, "ipa_us": r.ipa_us,
        "ipa_generada_por_ia": bool(getattr(r, "ipa_generada_por_ia", False)),
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
        "explicacion_pendiente": datos.etapa == "diccionario" and explicable,
        "motivo_sin_explicacion": motivo_sin_explicacion or None,
        "avisos": avisos,
    }


def _nivel(pet: _Lector) -> float:
    p = _perfil_de(pet)
    return p.nivel if p is not None else ui.NIVEL_POR_DEFECTO


@app.get("/api/audio/{nombre}")
def audio(nombre: str):
    if not re.fullmatch(r"[\w.-]{1,160}\.(?:mp3|wav|ogg)", nombre) or ".." in nombre:
        raise _no(404, "No existe ese audio.")
    p = _DIR_AUDIO / nombre
    if not p.is_file():
        raise _no(404, "No existe ese audio.")
    return FileResponse(p, media_type="audio/mpeg",
                        headers={"Cache-Control": "public, max-age=604800"})


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


# --- Punto 5: pronunciacion ------------------------------------------------------

_EXT_AUDIO = {".webm", ".ogg", ".oga", ".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga"}
_TOPE_AUDIO = 10 * 1024 * 1024


def _fonema_json(simbolo) -> dict | None:
    f = fonemas.buscar(simbolo)
    if f is None:
        return None
    return {"simbolo": f.simbolo, "nombre": f.nombre, "ejemplos": list(f.ejemplos),
            "audio": _url_audio_fonema(f.ruta, "/api/fonemas/")}


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
async def practicar(pet: Lector, frase: str = Form(..., max_length=2000),
                    audio: UploadFile = File(...)) -> dict:
    """La corrección de pronunciacion, con las guardas de `ui._practicar`."""
    frase = frase.strip()[:ui.LIMITE_FRASE_VOZ]
    if not frase:
        raise _no(422, "Escribe la frase que vas a leer en voz alta.")
    ext = os.path.splitext(str(audio.filename or "").lower())[1] or ".webm"
    if ext not in _EXT_AUDIO:
        ext = ".webm"
    contenido = await audio.read(_TOPE_AUDIO + 1)
    if len(contenido) > _TOPE_AUDIO:
        raise _no(413, "La grabación es demasiado larga.")
    if len(contenido) < 800:
        raise _no(422, "No me ha llegado audio. Graba la frase otra vez.")
    if _va_a_costar(pet) and not ui._dentro_del_limite(pet, "voz", ui.LIMITE_VOZ_HORA):
        raise _no(429, ui._mensaje_limite("es", ui._minutos_para_la_siguiente("voz", pet)))
    if config.falta():
        raise _no(503, "Para corregir la pronunciación hace falta la clave de OpenAI. "
                       "Lo demás de la aplicación no la necesita.")
    puede, motivo = ui._puede_pagar(pet)
    if not puede:
        raise _no(403, motivo)
    fd, tmp = tempfile.mkstemp(suffix=ext, prefix="ll_voz_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(contenido)
        # Sin devolucion del uso en ningun caso, como en `ui._practicar`: la
        # sesion puede haber pagado gpt y tts-1 aunque falle la transcripcion.
        s = voz.practicar(tmp, frase, guardar_fallos=False)
        if s.evaluacion.palabras_falladas and s.transcripcion_ok:
            voz.registrar_fallos(s.evaluacion.palabras_falladas,
                                 ruta=ui._archivo_lector("voz.db", pet), frase=frase)
    except Exception as e:
        raise _no(502, f"No he podido corregir la grabación ({type(e).__name__}).") from e
    finally:
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
            ipa, variante = fonemas.ipa_de_palabra(cruda)
            normal = voz.normalizar_palabras(cruda)
            detalles.append({
                "palabra": cruda, "ipa": ipa, "variante": variante,
                "audio": _url_audio(_audio_de_detalle(normal, audios)),
                "fonema": _fonema_json(getattr(d, "fonema", None)),
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
    }


@app.get("/api/voz/debiles")
def debiles(pet: Lector) -> dict:
    filas = voz.puntos_debiles(n=15, ruta=ui._archivo_lector("voz.db", pet))
    return {"palabras": [{"palabra": w, "fallos": n} for w, n in filas]}


@app.get("/api/voz/falladas")
def falladas(pet: Lector, n: int = Query(15, ge=1, le=50)) -> dict:
    """Las palabras que peor pronuncia este lector, con la frase donde falló.
    Sin red y gratis: lee su `voz.db`."""
    filas = voz.palabras_para_practicar(n=n, ruta=ui._archivo_lector("voz.db", pet))
    return {"palabras": [{"palabra": f["palabra"], "fallos": f["fallos"],
                          "ultima_vez": f.get("ultima_vez"), "frase": f.get("frase")}
                         for f in filas]}


# --- Lo tuyo: cuaderno, repaso, biblioteca e inicio -----------------------------

def _anotacion_json(a) -> dict:
    return {"palabra": a.palabra, "lema": a.lema, "categoria": a.categoria,
            "sentido": a.sentido, "oracion": a.oracion, "libro": a.libro,
            "capitulo": a.capitulo, "rareza": a.rareza or None, "creado": a.creado}


@app.get("/api/cuaderno")
def mis_palabras(pet: Lector, n: int = 50) -> dict:
    db = ui._archivo_lector("cuaderno.db", pet)
    total, lemas, libros = cuaderno.contar(db)
    return {"consultas": total, "palabras": lemas, "libros": libros,
            "entradas": [_anotacion_json(a)
                         for a in cuaderno.ultimas(max(1, min(int(n), 200)), db)]}


@app.get("/api/repaso")
def repaso(pet: Lector) -> dict:
    """Sin nota y sin racha: un recordatorio, no un examen (`enganche.md` §5)."""
    anotaciones = cuaderno.para_repasar(5, ui._archivo_lector("cuaderno.db", pet))
    return {"palabras": [_anotacion_json(a) for a in anotaciones],
            "voz": [{"palabra": w, "fallos": n} for w, n in
                    voz.puntos_debiles(n=5, ruta=ui._archivo_lector("voz.db", pet))]}


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
                parrafos = [" ".join(t.split()) for t in re.split(r"\n\s*\n", c.texto)
                            if len(t.split()) >= 25]
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
    return {"routes": rutas, "exception_handlers": {Exception: _error_inesperado}}


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
