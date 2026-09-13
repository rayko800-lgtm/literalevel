"""Tutor de pronunciacion por voz para LiteraLevel.

Ciclo completo: el usuario lee en voz alta una frase objetivo, se transcribe
con Whisper, se compara palabra a palabra con `difflib` para saber
exactamente que fallo, un modelo de OpenAI explica en español como corregir
esos sonidos, y `tts-1` genera un audio de referencia con la pronunciacion
correcta. Las palabras que fallan se registran en SQLite para poder proponer
practica dirigida mas adelante.

Degradacion elegante: la parte de `difflib` (transcribir_audio -> comparar)
no necesita red y funciona siempre que se le de una transcripcion. Sin
OPENAI_API_KEY, `transcribir_audio`, `explicar_correccion` y
`generar_audio_correcto` devuelven `None` en vez de lanzar una excepcion, asi
que la interfaz solo tiene que comprobar si el resultado es `None`.
"""
from __future__ import annotations
import difflib, hashlib, os, re, sqlite3, tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

import config
import fonemas

# Bajo la raiz configurable de `config`, por lo mismo que en `lexicon`: el
# disco de un Space se borra al reiniciar.
RUTA_DB_POR_DEFECTO = str(config.dir_datos() / "voz.db")
RUTA_AUDIO_GENERADO = config.dir_datos() / "audio"

# Modelos: gpt-4o-mini basta y abarata la explicacion breve; whisper-1 y
# tts-1 son los unicos disponibles para voz.
MODELO_TRANSCRIPCION = "whisper-1"
MODELO_EXPLICACION = "gpt-4o-mini"
MODELO_VOZ = "tts-1"
VOZ_POR_DEFECTO = "alloy"
# Invalida los mp3 creados antes de que la escritura fuera atomica. Un clip
# corto pero decodificable no se puede separar con certeza de uno correcto;
# versionar la huella hace que todos se regeneren una vez y evita conservar
# para siempre un archivo que ya llego recortado.
VERSION_AUDIO_TTS = "v2-pausa-atomico"

_PUNTUACION_RE = re.compile(r"[^\w\s'-]", re.UNICODE)
_GUION_SOLO_RE = re.compile(r"(^[-']+|[-']+$)")
_APOSTROFOS_RE = re.compile("[‘’ʼ´`]")


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cliente():
    """Crea el cliente de OpenAI solo si hay clave. `None` si falta."""
    clave = config.obtener("OPENAI_API_KEY")
    if not clave:
        return None
    from openai import OpenAI
    # Con plazo, por lo mismo que en `lexicon.py`: sin el, el SDK espera 600 s
    # y reintenta dos veces, y un hilo atascado se lleva por delante la cola
    # entera de Gradio. La voz son whisper + gpt + tts encadenados, asi que se
    # le da mas margen que a la consulta lexica.
    return OpenAI(api_key=clave, timeout=90.0, max_retries=1)


# --- Normalizacion y comparacion (sin red, siempre disponible) --------

def normalizar_palabras(texto: str) -> list[str]:
    """Minusculas, sin puntuacion, dividido en palabras.

    Conserva apostrofes y guiones internos (don't, well-known) para no rom-
    per contracciones, pero quita comas, puntos y demas signos: una coma de
    mas no debe contar como un fallo de pronunciacion.
    """
    # Los libros escriben el apostrofo tipografico (’). Sin unificarlo, la
    # regex de abajo lo trataba como puntuacion y «don’t» salia como «don» y
    # «t»: dos palabras falladas que el lector no habia dicho mal.
    limpio = _PUNTUACION_RE.sub(" ", _APOSTROFOS_RE.sub("'", str(texto).lower()))
    return [_GUION_SOLO_RE.sub("", p) for p in limpio.split() if _GUION_SOLO_RE.sub("", p)]


@dataclass
class Evaluacion:
    puntuacion: float                  # 0..100
    palabras_objetivo: list[str]
    palabras_dichas: list[str]
    palabras_falladas: list[str]       # subconjunto de palabras_objetivo
    transcripcion: str                 # lo que de verdad se comparo (puede ser "")


def evaluar_pronunciacion(frase_objetivo: str, transcripcion: str) -> Evaluacion:
    """Compara la frase objetivo con lo transcrito y dice que palabras fallaron.

    Usa `difflib.SequenceMatcher` para alinear ambas listas de palabras. Los
    tramos "replace" y "delete" del lado del objetivo son palabras que el
    usuario no dijo bien (las cambio o se las salto); un tramo "insert" son
    palabras de mas que dijo y que no cuentan como fallo de una palabra
    objetivo concreta.
    """
    palabras_obj = normalizar_palabras(frase_objetivo)
    palabras_dic = normalizar_palabras(transcripcion)

    sm = difflib.SequenceMatcher(None, palabras_obj, palabras_dic, autojunk=False)
    falladas: list[str] = []
    for tag, i1, i2, _j1, _j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            falladas.extend(palabras_obj[i1:i2])

    puntuacion = round(sm.ratio() * 100, 1) if palabras_obj else 0.0
    return Evaluacion(puntuacion=puntuacion, palabras_objetivo=palabras_obj,
                      palabras_dichas=palabras_dic, palabras_falladas=falladas,
                      transcripcion=transcripcion)


# --- Transcripcion (necesita red) --------------------------------------

def transcribir_audio(ruta_audio: str | os.PathLike) -> str | None:
    """Transcribe un audio con whisper-1. `None` si no hay clave o falla la
    llamada: nunca lanza excepcion hacia la interfaz."""
    cliente = _cliente()
    if cliente is None:
        return None
    try:
        with open(ruta_audio, "rb") as f:
            r = cliente.audio.transcriptions.create(model=MODELO_TRANSCRIPCION, file=f)
        return r.text
    except Exception:
        return None


# --- Correccion explicada (Structured Outputs, necesita red) ----------

# Lo que el modelo pone en `fonema` cuando el fallo no es de un sonido concreto.
# No es un simbolo del inventario, asi que `fonemas.buscar` da `None` y la
# interfaz no pinta reproductor.
SIN_FONEMA = "ninguno"


class DetallePalabra(BaseModel):
    palabra: str = Field(description="La palabra en ingles que el alumno pronuncio mal.")
    # El fonema va restringido al inventario de `fonemas` EN EL ESQUEMA (el
    # `enum` que viaja a Structured Outputs), para que cada explicacion apunte
    # a un audio pregrabado que existe. En pydantic se deja como `str` a
    # proposito: con un `Literal`, un valor fuera de la lista -una cache
    # vieja, un cambio de modelo, un inventario que crezca- seria un
    # ValidationError, `explicar_correccion` devolveria `None` y el alumno
    # perderia TODA la correccion por un simbolo. Asi llega el texto y la
    # interfaz, que normaliza con `fonemas.buscar`, pinta sin reproductor.
    fonema: str = Field(
        description="Simbolo AFI del fonema que falla, tal cual aparece en la lista "
                    "(General American). 'ninguno' si el fallo no es de un sonido concreto "
                    "(acento de la palabra, ritmo) o no esta en la lista.",
        json_schema_extra={"enum": [*fonemas.SIMBOLOS, SIN_FONEMA]})
    sonido_que_falla: str = Field(
        description="Que sonido falla, anclado a una palabra del español que lo tenga o "
                    "se le acerque; si no existe en español, en que se diferencia del "
                    "sonido español mas parecido.")
    como_colocar_la_boca: str = Field(
        description="Instruccion concreta de que hacer con lengua, labios, dientes o "
                    "garganta, que un chico de 15 años pueda seguir sin saber fonetica.")


class Correccion(BaseModel):
    resumen: str = Field(description="Resumen breve en español, una o dos frases, animando al alumno.")
    detalles: list[DetallePalabra]


# El prompt de la correccion. Se reescribio por lo que dijo una lectora real:
# «el sonido W que es diferente a la letra B en español, no entiendo eso».
# Comparar con una LETRA no ensena nada; lo que funciona es anclar el sonido a
# una PALABRA del español que ya sabe decir («la hu de huevo») y, si no existe,
# decir en que se diferencia del parecido. Y fuera las vaguedades («mas
# fuerte», «mas suave») que no dicen que mover.
#
# La lista de fonemas va entera con su ancla: asi el modelo escribe el simbolo
# tal cual esta en el esquema (el `enum` de `DetallePalabra.fonema`) y usa las
# mismas comparaciones que ve el alumno junto al audio.
_PROMPT_SISTEMA = (
    "Eres un profesor de pronunciacion de ingles americano (General American) para "
    "hispanohablantes, sobre todo de Latinoamerica, que tienen unos 15 años. Respondes "
    "siempre en español, breve, concreto y con palabras de todos los dias.")

_PROMPT_REGLAS = (
    "Para cada palabra rellena los campos asi:\n"
    "1. `fonema`: el sonido que mas probablemente fallo, escrito EXACTAMENTE como en esta "
    f"lista, o '{SIN_FONEMA}' si el fallo no es de un sonido concreto:\n"
    + "\n".join(f"   {f.simbolo}  ({', '.join(f.ejemplos)}): {f.nombre}"
                for f in fonemas.INVENTARIO)
    + "\n2. `sonido_que_falla`: ancla el sonido a una PALABRA del español que lo tenga o se "
    "le acerque, por ejemplo: «/w/ suena como la \"hu\" de \"huevo\"». Si no existe en "
    "español (como /θ/ fuera de España, /ʃ/, /æ/, /ʌ/ o /ɚ/), dilo y explica en que se "
    "diferencia del sonido español mas parecido. Nunca compares con una letra suelta.\n"
    "3. `como_colocar_la_boca`: di que hacer con labios, lengua, dientes o garganta usando "
    "verbos concretos (junta, separa, redondea, apoya la punta de la lengua en..., deja "
    "salir el aire...). Prohibido «mas fuerte», «mas suave», «mas abierto» o «mas claro» "
    "sin decir que mover y como.\n"
    "4. Sin tecnicismos (fricativa, alveolar, bilabial, sonora, aspirada...) salvo que "
    "expliques en la misma frase que significan con palabras normales.\n"
    "Una o dos frases por campo.")


def explicar_correccion(palabras_falladas: list[str], idioma: str = "ingles") -> Correccion | None:
    """Pide a OpenAI una explicacion breve en español de como corregir cada
    palabra fallada: que sonido falla y como colocar la boca.

    `None` si no hay clave, no hay palabras que explicar, o falla la llamada.
    """
    if not palabras_falladas:
        return None
    cliente = _cliente()
    if cliente is None:
        return None
    try:
        resp = cliente.chat.completions.parse(
            model=MODELO_EXPLICACION,
            messages=[
                {"role": "system", "content": _PROMPT_SISTEMA},
                {"role": "user", "content":
                    f"El alumno ha pronunciado mal estas palabras en {idioma}: "
                    f"{', '.join(palabras_falladas)}.\n\n{_PROMPT_REGLAS}"},
            ],
            response_format=Correccion,
        )
        return resp.choices[0].message.parsed
    except Exception:
        return None


# --- Respuesta hablada (TTS, necesita red) -----------------------------

def _texto_para_tts(texto: str) -> str:
    """Anade una pausa final a entradas breves sin cambiar lo pronunciado."""
    limpio = texto.strip()
    if limpio and limpio[-1] not in ".,;:!?":
        limpio += ","
    return limpio


def _ruta_audio_cache(texto: str, voz: str) -> Path:
    legible = re.sub(r"[^a-z0-9]+", "_", texto.lower())[:40].strip("_") or "frase"
    clave = hashlib.sha256("\x1f".join(
        (VERSION_AUDIO_TTS, MODELO_VOZ, voz, texto)).encode("utf-8")).hexdigest()[:24]
    return RUTA_AUDIO_GENERADO / f"{legible}_{clave}.mp3"


def _escribir_audio_atomico(respuesta, ruta: Path) -> None:
    """Escribe junto al destino y lo publica con un unico `os.replace`."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    descriptor, nombre_temporal = tempfile.mkstemp(
        dir=str(ruta.parent), prefix=f".{ruta.name}.", suffix=".tmp")
    os.close(descriptor)
    temporal = Path(nombre_temporal)
    try:
        respuesta.write_to_file(str(temporal))
        if temporal.stat().st_size == 0:
            raise OSError("OpenAI devolvio un audio vacio")
        with temporal.open("ab") as archivo:
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    finally:
        temporal.unlink(missing_ok=True)

def generar_audio_correcto(texto: str, ruta_salida: str | os.PathLike | None = None,
                           voz: str = VOZ_POR_DEFECTO) -> str | None:
    """Genera un audio con tts-1 de la pronunciacion correcta de `texto`.

    Devuelve la ruta del mp3, o `None` si hay que generarlo y no se puede
    (sin clave, sin red o error). **Si la frase ya se genero antes, se
    devuelve el archivo aunque no haya clave**: negar un audio que ya esta en
    disco no protege nada y contradice la degradacion elegante del proyecto.

    **El nombre sale del contenido, no de la hora.** Antes llevaba
    `int(datetime.now().timestamp())`, asi que dos peticiones identicas
    generaban dos archivos distintos: la misma frase se pagaba a `tts-1`
    tantas veces como se pulsara el boton, y el disco crecia sin techo. Con la
    huella del texto, el modelo y la voz, repetir una frase es gratis y
    ademas instantaneo.
    """
    # La cache se mira ANTES de pedir el cliente: si la frase ya se genero,
    # se devuelve aunque no haya clave ni red.
    reutilizable = None
    if ruta_salida is None:
        reutilizable = _ruta_audio_cache(texto, voz)
        if reutilizable.is_file() and reutilizable.stat().st_size > 0:
            return str(reutilizable)
        try:
            reutilizable.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None
        ruta_salida = reutilizable

    cliente = _cliente()
    if cliente is None:
        return None
    try:
        respuesta = cliente.audio.speech.create(model=MODELO_VOZ, voice=voz,
                                                input=_texto_para_tts(texto),
                                                response_format="mp3")
        destino = Path(ruta_salida)
        _escribir_audio_atomico(respuesta, destino)
        return str(destino)
    except Exception:
        return None


# --- Registro de puntos debiles (SQLite, sin red) ----------------------

def _conectar(ruta: str = RUTA_DB_POR_DEFECTO) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    con = sqlite3.connect(ruta)
    con.execute("""
        CREATE TABLE IF NOT EXISTS palabras_debiles (
            palabra    TEXT PRIMARY KEY,
            fallos     INTEGER NOT NULL DEFAULT 0,
            ultima_vez TEXT NOT NULL
        )
    """)
    return con


def registrar_fallos(palabras: list[str], ruta: str = RUTA_DB_POR_DEFECTO) -> None:
    """Suma un fallo a cada palabra (ya normalizada) de la lista.

    Nunca lanza excepcion hacia la interfaz: un fallo de disco al guardar el
    historial no debe tumbar la sesion de practica.
    """
    if not palabras:
        return
    try:
        ahora = _ahora()
        con = _conectar(ruta)
        try:
            with con:
                for p in palabras:
                    con.execute("""
                        INSERT INTO palabras_debiles (palabra, fallos, ultima_vez)
                        VALUES (?, 1, ?)
                        ON CONFLICT(palabra) DO UPDATE SET
                            fallos = fallos + 1,
                            ultima_vez = excluded.ultima_vez
                    """, (p, ahora))
        finally:
            con.close()
    except Exception:
        pass


def puntos_debiles(n: int = 10, ruta: str = RUTA_DB_POR_DEFECTO) -> list[tuple[str, int]]:
    """Las `n` palabras que mas fallos acumulan, de mas a menos fallos.

    Devuelve pares (palabra, fallos). Lista vacia si no hay historial o si
    algo falla al leer la base de datos.
    """
    try:
        con = _conectar(ruta)
        try:
            cur = con.execute(
                "SELECT palabra, fallos FROM palabras_debiles "
                "ORDER BY fallos DESC, ultima_vez DESC LIMIT ?", (n,))
            return cur.fetchall()
        finally:
            con.close()
    except Exception:
        return []


# --- Ciclo completo -----------------------------------------------------

@dataclass
class SesionVoz:
    evaluacion: Evaluacion
    correccion: Correccion | None = None
    audio_correcto: str | None = None
    transcripcion_ok: bool = True   # False si no se pudo transcribir (sin red/clave)


def practicar(ruta_audio: str | os.PathLike, frase_objetivo: str,
             guardar_fallos: bool = True) -> SesionVoz:
    """Ciclo completo de practica: transcribe el audio del usuario, evalua
    contra la frase objetivo, explica como corregir lo que fallo, genera un
    audio de referencia y registra las palabras debiles.

    Si no hay OPENAI_API_KEY (o falla la red), la transcripcion es `None` y
    la evaluacion se hace contra una cadena vacia (todo cuenta como fallado);
    `transcripcion_ok` queda en `False` para que la interfaz pueda avisar sin
    que la funcion lance ninguna excepcion.
    """
    transcripcion = transcribir_audio(ruta_audio)
    evaluacion = evaluar_pronunciacion(frase_objetivo, transcripcion or "")

    if guardar_fallos and evaluacion.palabras_falladas:
        registrar_fallos(evaluacion.palabras_falladas)

    correccion = None
    if evaluacion.palabras_falladas:
        correccion = explicar_correccion(evaluacion.palabras_falladas)

    # El audio de referencia se genera SIEMPRE, no solo cuando algo falla.
    # Antes iba dentro del `if`: quien pronunciaba bien se encontraba el
    # rotulo "Cómo debería sonar" con el reproductor vacio, que es justo
    # cuando uno quiere oirlo para confirmar que lo hizo bien. Y repetir una
    # frase ya generada no cuesta nada: `generar_audio_correcto` cachea por
    # contenido.
    audio_correcto = generar_audio_correcto(frase_objetivo)

    return SesionVoz(evaluacion=evaluacion, correccion=correccion,
                     audio_correcto=audio_correcto, transcripcion_ok=transcripcion is not None)
