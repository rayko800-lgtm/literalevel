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
import difflib, hashlib, os, re, sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from pydantic import BaseModel, Field

import config

RUTA_DB_POR_DEFECTO = os.path.join(os.path.expanduser("~"), ".literalevel", "voz.db")

# Modelos: gpt-4o-mini basta y abarata la explicacion breve; whisper-1 y
# tts-1 son los unicos disponibles para voz.
MODELO_TRANSCRIPCION = "whisper-1"
MODELO_EXPLICACION = "gpt-4o-mini"
MODELO_VOZ = "tts-1"
VOZ_POR_DEFECTO = "alloy"

_PUNTUACION_RE = re.compile(r"[^\w\s'-]", re.UNICODE)
_GUION_SOLO_RE = re.compile(r"(^[-']+|[-']+$)")


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cliente():
    """Crea el cliente de OpenAI solo si hay clave. `None` si falta."""
    clave = config.obtener("OPENAI_API_KEY")
    if not clave:
        return None
    from openai import OpenAI
    return OpenAI(api_key=clave)


# --- Normalizacion y comparacion (sin red, siempre disponible) --------

def normalizar_palabras(texto: str) -> list[str]:
    """Minusculas, sin puntuacion, dividido en palabras.

    Conserva apostrofes y guiones internos (don't, well-known) para no rom-
    per contracciones, pero quita comas, puntos y demas signos: una coma de
    mas no debe contar como un fallo de pronunciacion.
    """
    limpio = _PUNTUACION_RE.sub(" ", str(texto).lower())
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

class DetallePalabra(BaseModel):
    palabra: str = Field(description="La palabra en ingles que el alumno pronuncio mal.")
    sonido_que_falla: str = Field(
        description="Que sonido o fonema falla tipicamente, descrito de forma sencilla "
                    "(por ejemplo comparandolo con un sonido del español).")
    como_colocar_la_boca: str = Field(
        description="Instruccion breve y practica de como colocar lengua, labios o "
                    "dientes para producir el sonido correcto.")


class Correccion(BaseModel):
    resumen: str = Field(description="Resumen breve en español, una o dos frases, animando al alumno.")
    detalles: list[DetallePalabra]


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
                {"role": "system", "content":
                    "Eres un profesor de pronunciacion de ingles para hispanohablantes. "
                    "Responde siempre en español, de forma breve, concreta y practica."},
                {"role": "user", "content":
                    f"El alumno ha pronunciado mal estas palabras en {idioma}: "
                    f"{', '.join(palabras_falladas)}. Para cada una explica que sonido falla "
                    "tipicamente y como colocar la boca (lengua, labios, dientes) para "
                    "corregirlo. Se breve: una o dos frases por palabra."},
            ],
            response_format=Correccion,
        )
        return resp.choices[0].message.parsed
    except Exception:
        return None


# --- Respuesta hablada (TTS, necesita red) -----------------------------

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
        carpeta = os.path.join(os.path.expanduser("~"), ".literalevel", "audio")
        legible = re.sub(r"[^a-z0-9]+", "_", texto.lower())[:40].strip("_") or "frase"
        clave = hashlib.sha256(
            "\x1f".join((MODELO_VOZ, voz, texto)).encode("utf-8")).hexdigest()[:24]
        reutilizable = os.path.join(carpeta, f"{legible}_{clave}.mp3")
        if os.path.exists(reutilizable) and os.path.getsize(reutilizable) > 0:
            return reutilizable
        try:
            os.makedirs(carpeta, exist_ok=True)
        except OSError:
            return None
        ruta_salida = reutilizable

    cliente = _cliente()
    if cliente is None:
        return None
    try:
        respuesta = cliente.audio.speech.create(model=MODELO_VOZ, voice=voz, input=texto,
                                                response_format="mp3")
        respuesta.write_to_file(ruta_salida)
        return str(ruta_salida)
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
