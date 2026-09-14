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
import difflib, hashlib, json, os, re, sqlite3, tempfile, threading
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
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
# Un candado por CLAVE exacta de audio (la ruta del mp3 de la cache): se crea
# al pedirlo y se borra cuando nadie lo usa, asi que la memoria no crece.
# Antes (71e4b52, Codex) eran 64 franjas fijas, y dos palabras DISTINTAS que
# caian en la misma franja se esperaban durante toda la llamada de red al TTS,
# hasta 90 s. Con la clave exacta solo espera quien pide el MISMO audio, que
# es lo que se quiere: se encuentra el mp3 ya publicado y no se paga dos veces.
_CANDADOS_AUDIO = {}          # clave -> [candado, usuarios]
_CANDADO_TABLA_AUDIO = threading.Lock()

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
    # Pares (lo que debia decir, lo que se entendio en su lugar); "" si no se
    # oyo nada. Sin esto la explicacion adivinaba el sonido: con «fix» por
    # «fox» culpaba a la /f/, que estaba bien, y no a la vocal.
    entendidas: list[tuple[str, str]] = field(default_factory=list)


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
    entendidas: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            falladas.extend(palabras_obj[i1:i2])
            objetivo, dicho = palabras_obj[i1:i2], palabras_dic[j1:j2]
            if len(objetivo) == len(dicho):
                entendidas.extend(zip(objetivo, dicho))
            else:
                # Tramos de distinta longitud («going to» por «gonna»): cada
                # palabra se empareja con el tramo entero que se oyo.
                entendidas.extend((w, " ".join(dicho)) for w in objetivo)

    puntuacion = round(sm.ratio() * 100, 1) if palabras_obj else 0.0
    return Evaluacion(puntuacion=puntuacion, palabras_objetivo=palabras_obj,
                      palabras_dichas=palabras_dic, palabras_falladas=falladas,
                      transcripcion=transcripcion, entendidas=entendidas)


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


def _lo_que_se_entendio(entendidas) -> str:
    """El parrafo del prompt con lo que se oyo en lugar de cada palabra."""
    pares = [(o, d) for o, d in (entendidas or []) if o]
    if not pares:
        return ""
    lineas = "; ".join(f"{o} → «{d}»" if d else f"{o} → (no se oyó)" for o, d in pares)
    return ("Lo que la transcripción automática entendió en su lugar: " + lineas + ". "
            "Elige el `fonema` comparando lo que debía decir con lo que se entendió: el "
            "sonido que falla es el que cambia entre las dos (en «fox» → «fix» es la vocal, "
            "no la /f/). La transcripción puede equivocarse; si no hay diferencia clara, "
            "elige el sonido más difícil de la palabra para un hispanohablante.\n\n")


def explicar_correccion(palabras_falladas: list[str], idioma: str = "ingles",
                        entendidas: list[tuple[str, str]] | None = None) -> Correccion | None:
    """Pide a OpenAI una explicacion breve en español de como corregir cada
    palabra fallada: que sonido falla y como colocar la boca.

    `idioma` es vestigial: el prompt y el inventario de fonemas son de ingles
    americano, y cualquier otro valor le daria al modelo una contradiccion.
    Se conserva solo para no romper a quien ya lo pasa. (Fable, auditoria 18.)

    `entendidas` son los pares (debia decir, se entendio) de `Evaluacion`. Es
    opcional para no romper a quien llame con la lista sola, pero sin ellos el
    modelo tiene que adivinar que sonido fallo.

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
                    f"{', '.join(palabras_falladas)}.\n\n"
                    f"{_lo_que_se_entendio(entendidas)}{_PROMPT_REGLAS}"},
            ],
            response_format=Correccion,
        )
        correccion = resp.choices[0].message.parsed
    except Exception:
        return None
    return fijar_fonemas(correccion, entendidas)


# --- El fonema y el consejo, deterministas -----------------------------
#
# Con la MISMA grabacion («magic» en lugar de «tragic») el modelo eligio /dʒ/ y
# en la llamada siguiente /tʃ/, con consejos de boca distintos -uno decia
# «junta los labios», que para /dʒ/ es falso-, cuando el error real es
# /tr/ -> /m/ (f4, en el Space, 13 sep 2026). Asi que el fonema ya no lo
# decide el modelo: sale de comparar la IPA de lo que se debia decir con la de
# lo que se entendio, y el consejo sale de `articulacion.FICHAS`, que esta
# revisado. Del modelo solo queda el resumen. Si no hay con que comparar, no
# se señala ningun sonido y se dice por que.

_SIN_COMPARACION = {
    "no_oida": ("No se oyó esta palabra en tu grabación, así que no hay un sonido concreto que señalar",
                "Escúchala sola y repítela despacio, sílaba por sílaba."),
    "sin_ipa": ("Esta palabra, o lo que se entendió, no está en los diccionarios de pronunciación, "
                "así que no te señalo un sonido concreto para no inventártelo",
                "Escúchala sola y repítela despacio, sílaba por sílaba."),
    "igual": ("Lo que se entendió suena igual que la palabra: puede que la transcripción "
              "automática se equivocara",
              "Repítela un poco más despacio, marcando cada sonido."),
    "sin_datos": ("No sé qué se entendió en su lugar, así que no te señalo un sonido concreto",
                  "Escúchala sola y repítela despacio, sílaba por sílaba."),
}


def _clave_palabra(palabra) -> str:
    return (str(palabra or "").strip().replace("’", "'")
            .strip(".,;:!?¿¡\"()[]«»…“”‘").lower())


def piezas(texto: str) -> list[str]:
    """Las palabras de `texto` con los compuestos partidos por el guion:
    «war-chant» -> ['war', 'chant']. Ni el diccionario ni CMUdict traen casi
    ningun compuesto, pero si sus piezas."""
    return [p for trozo in str(texto or "").split() for p in trozo.split("-") if _clave_palabra(p)]


def _segmentos_por_pieza(texto: str) -> list[list[str]]:
    """Los fonemas de cada pieza, en orden; vacio si alguna no tiene IPA."""
    salida = []
    for pieza in piezas(texto):
        ipa, _ = fonemas.ipa_de_palabra(_clave_palabra(pieza))
        if not ipa:
            return []
        salida.append(fonemas.segmentar(ipa))
    return salida


def _es_sonido_facil(simbolo: str) -> bool:
    """La ficha del sonido dice que casi no le falla a quien habla español."""
    import articulacion
    sonido = articulacion.buscar(simbolo, "ga")
    return sonido is not None and str(sonido.ficha.trampa).strip().lower().startswith("casi ningun")


def _comparar(esperada: str, entendida: str | None,
              pieza: str | None = None) -> tuple[str | None, str]:
    """(simbolo del primer fonema esperado que cambia, motivo si no lo hay).

    `pieza`: la correccion del modelo parte los compuestos («war-chant» en
    «war» y «chant»), pero lo entendido esta emparejado con el compuesto
    entero. Se compara el compuesto y solo cuentan los cambios que caen
    dentro de los fonemas de esa pieza.
    """
    import difflib
    if entendida is None:
        return None, "sin_datos"
    if not _clave_palabra(entendida):
        return None, "no_oida"
    por_pieza, oido = _segmentos_por_pieza(esperada), _segmentos_por_pieza(entendida)
    if not por_pieza or not oido:
        return None, "sin_ipa"
    a = [s for p in por_pieza for s in p]
    b = [s for p in oido for s in p]
    desde, hasta = 0, len(a)
    if pieza is not None:
        claves = [_clave_palabra(p) for p in piezas(esperada)]
        if pieza not in claves:
            return None, "sin_datos"
        i = claves.index(pieza)
        desde = sum(len(p) for p in por_pieza[:i])
        hasta = desde + len(por_pieza[i])
    facil = None
    for op, i1, i2, _j1, _j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        # Un sonido de mas en lo entendido (insert) no es un sonido esperado
        # que falle: se sigue buscando.
        if op == "equal" or i1 == i2:
            continue
        for k in range(max(i1, desde), min(i2, hasta)):
            if not fonemas.buscar(a[k]):
                continue
            # Un sonido que la ficha da por facil (/f/, /n/, /tʃ/...) no se
            # señala si hay otro cambio: con «for» entendido «or» salia /f/ con
            # «Error típico: casi ninguno», que se contradice (Miguel, 14 sep).
            if _es_sonido_facil(a[k]):
                facil = facil or a[k]
                continue
            return a[k], ""
    if facil:
        return facil, "facil"
    return None, "igual"


def fonema_que_cambia(esperada: str, entendida: str | None) -> str | None:
    """El primer fonema de `esperada` que no esta en `entendida`, comparando sus
    IPA de diccionario: «tragic» / «magic» -> «t». `None` si falta una IPA, no
    se oyo nada o suenan igual. Determinista y sin red."""
    simbolo, motivo = _comparar(esperada, entendida)
    return simbolo if not motivo else None


def _consejo_de_ficha(simbolo: str) -> tuple[str, str] | None:
    """(sonido_que_falla, como_colocar_la_boca) desde `articulacion.FICHAS`."""
    import articulacion
    sonido = articulacion.buscar(simbolo, "ga")
    if sonido is None:
        return None
    f = sonido.ficha
    return (f"/{sonido.simbolo}/, {sonido.nombre}, como en «{', '.join(sonido.ejemplos)}». "
            f"Error típico: {f.trampa}",
            f"Labios: {f.labios}. Lengua: {f.lengua}. Aire: {f.aire}.")


def fijar_fonemas(correccion: Correccion | None,
                  entendidas: list[tuple[str, str]] | None) -> Correccion | None:
    """Sustituye en cada detalle el fonema y los dos consejos del modelo por los
    deterministas (ver arriba). Devuelve la misma `Correccion`, cambiada."""
    if correccion is None:
        return None
    oidas = ({_clave_palabra(o): (d or "") for o, d in entendidas if o}
             if entendidas is not None else None)
    resultados = []
    for d in correccion.detalles:
        clave = _clave_palabra(d.palabra)
        padre = None
        if oidas is None:
            simbolo, motivo = None, "sin_datos"
        elif clave in oidas:
            simbolo, motivo = _comparar(clave, oidas[clave])
        else:
            # El modelo partio un compuesto: «war» y «chant» de «war-chant».
            padre = next((k for k in oidas if "-" in k and clave in piezas(k)), None)
            simbolo, motivo = (_comparar(padre, oidas[padre], pieza=clave) if padre
                               else (None, "sin_datos"))
        resultados.append((d, simbolo, motivo, padre))

    # La pieza de un compuesto que se dijo bien no lleva detalle si otra pieza
    # del mismo compuesto si falla: con «war dance» por «war-chant», «war» salia
    # con «suena igual… repitela mas despacio» (f4, en el Space). Si todas suenan
    # igual se quedan, para no dejar la correccion sin nada.
    con_fallo = {padre for _d, _s, motivo, padre in resultados if padre and motivo != "igual"}
    quedan = []
    for d, simbolo, motivo, padre in resultados:
        if padre and motivo == "igual" and padre in con_fallo:
            continue
        quedan.append(d)
        consejo = _consejo_de_ficha(simbolo) if simbolo and motivo != "facil" else None
        if consejo:
            d.fonema = simbolo
            d.sonido_que_falla, d.como_colocar_la_boca = consejo
        elif motivo == "facil":
            # No se señala como fallo: la ficha dice que ese sonido casi no falla.
            d.fonema = SIN_FONEMA
            d.sonido_que_falla = (f"No se entendió la palabra, pero el sonido /{simbolo}/ no suele "
                                  "fallarle a quien habla español, así que no te lo señalo como error")
            d.como_colocar_la_boca = "Repítela entera, un poco más despacio y marcando cada sonido."
        else:
            d.fonema = SIN_FONEMA
            d.sonido_que_falla, d.como_colocar_la_boca = _SIN_COMPARACION[motivo or "igual"]
    correccion.detalles = quedan
    return correccion


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

@contextmanager
def _candado_audio(clave: str):
    """Exclusion mutua por clave exacta de audio. Ver `_CANDADOS_AUDIO`."""
    with _CANDADO_TABLA_AUDIO:
        entrada = _CANDADOS_AUDIO.setdefault(clave, [threading.Lock(), 0])
        entrada[1] += 1
    try:
        with entrada[0]:
            yield
    finally:
        with _CANDADO_TABLA_AUDIO:
            entrada[1] -= 1
            if entrada[1] == 0 and _CANDADOS_AUDIO.get(clave) is entrada:
                del _CANDADOS_AUDIO[clave]


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
    reutilizable = _ruta_audio_cache(texto, voz) if ruta_salida is None else None
    candado = _candado_audio(str(reutilizable)) if reutilizable is not None else nullcontext()
    try:
        with candado:
            # Releer DENTRO: otro lector puede haber publicado mientras esperabamos.
            # La cache sigue disponible sin construir cliente ni tener clave.
            if reutilizable is not None:
                if reutilizable.is_file() and reutilizable.stat().st_size > 0:
                    return str(reutilizable)
                reutilizable.parent.mkdir(parents=True, exist_ok=True)
                ruta_salida = reutilizable
            cliente = _cliente()
            if cliente is None:
                return None
            respuesta = cliente.audio.speech.create(model=MODELO_VOZ, voice=voz,
                                                    input=_texto_para_tts(texto),
                                                    response_format="mp3")
            destino = Path(ruta_salida)
            _escribir_audio_atomico(respuesta, destino)
            return str(destino)
    except Exception:
        return None


# --- Registro de puntos debiles (SQLite, sin red) ----------------------

class HistorialIlegible(RuntimeError):
    """El historial de pronunciacion existe pero no se puede leer (corrupto, o
    bloqueado mas tiempo del que espera SQLite).

    Se lanza en vez de devolver una lista vacia: vacia quiere decir «no has
    fallado ninguna palabra», y en ese caso no es verdad. Si la base no existe,
    si es una lista vacia: ese lector todavia no ha practicado.
    """


def _conectar(ruta: str = RUTA_DB_POR_DEFECTO) -> sqlite3.Connection:
    """Conexion a la base de puntos debiles, con el esquema al dia.

    `BEGIN IMMEDIATE` (71e4b52, Codex) serializa la migracion entre hilos y
    procesos, pero se abria en CADA conexion, tambien para leer: dos lecturas a
    la vez se esperaban y, pasados los 5 s de SQLite, «Mis palabras» salia
    vacia. Ahora el esquema se mira sin transaccion y solo si falta la tabla o
    la columna `frase` se abre la transaccion, se vuelve a mirar DENTRO -otro
    hilo puede haber migrado mientras tanto- y se migra. Si algo falla, la
    conexion se cierra (y lo que no se confirmo se deshace).
    """
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    con = sqlite3.connect(ruta)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(palabras_debiles)")}
        if "frase" not in columnas:
            con.execute("BEGIN IMMEDIATE")
            con.execute("""
                CREATE TABLE IF NOT EXISTS palabras_debiles (
                    palabra    TEXT PRIMARY KEY,
                    fallos     INTEGER NOT NULL DEFAULT 0,
                    ultima_vez TEXT NOT NULL
                )
            """)
            # Las bases viejas no guardaban la frase en que se fallo.
            columnas = {fila[1] for fila in con.execute("PRAGMA table_info(palabras_debiles)")}
            if "frase" not in columnas:
                con.execute("ALTER TABLE palabras_debiles ADD COLUMN frase TEXT")
            con.commit()
    except BaseException:
        con.close()
        raise
    return con


# Palabras que no se guardan como «difíciles» ni salen en la lista (Miguel, 14
# sep: «Tus palabras difíciles» guardaba «but · 1» y «on · 1»). Las funcionales
# cortas y muy frecuentes casi siempre fallan porque whisper las traga o las
# junta con la de al lado, no por como se dijeron; y con menos de tres letras no
# hay nada que practicar. Los sonidos que traen (la /ð/ de «the») se practican
# en palabras de contenido («though», «brother»), que si se guardan.
_PALABRAS_FUNCIONALES = frozenset("""
a an the and but or nor so if as than that this then they them their there
of on in at by for to from with into up out off
i you he she it we me him her us my your his its our
am is are was were be been do does did has had have will can not no yes
""".split())


def _cuenta_como_dificil(palabra) -> bool:
    """Si una palabra fallada se guarda en el historial de pronunciacion."""
    p = str(palabra or "").strip().lower().replace("’", "'")
    return len(p.replace("'", "")) >= 3 and p not in _PALABRAS_FUNCIONALES


def registrar_fallos(palabras: list[str], ruta: str = RUTA_DB_POR_DEFECTO,
                     frase: str | None = None) -> None:
    """Suma un fallo a cada palabra (ya normalizada) de la lista y, si se da,
    guarda la frase en la que se fallo (la ultima).

    Nunca lanza excepcion hacia la interfaz: un fallo de disco al guardar el
    historial no debe tumbar la sesion de practica.
    """
    palabras = [p for p in (palabras or []) if _cuenta_como_dificil(p)]
    if not palabras:
        return
    frase = (str(frase).strip()[:400] or None) if frase else None
    try:
        ahora = _ahora()
        con = _conectar(ruta)
        try:
            with con:
                for p in palabras:
                    con.execute("""
                        INSERT INTO palabras_debiles (palabra, fallos, ultima_vez, frase)
                        VALUES (?, 1, ?, ?)
                        ON CONFLICT(palabra) DO UPDATE SET
                            fallos = fallos + 1,
                            ultima_vez = excluded.ultima_vez,
                            frase = COALESCE(excluded.frase, palabras_debiles.frase)
                    """, (p, ahora, frase))
        finally:
            con.close()
    except Exception:
        pass


# La misma regla al leer, para lo que se guardo antes de tenerla: las filas se
# quedan en la base y solo dejan de salir en la lista.
_PARAMETROS_FILTRO = tuple(sorted(_PALABRAS_FUNCIONALES))
_FILTRO_DIFICILES = ("WHERE length(replace(palabra, '''', '')) >= 3 AND palabra NOT IN ("
                     + ",".join("?" * len(_PARAMETROS_FILTRO)) + ") ")


def palabras_para_practicar(n: int = 15, ruta: str = RUTA_DB_POR_DEFECTO) -> list[dict]:
    """Las palabras que peor se han pronunciado, con la frase donde se fallaron.

    Cada elemento: {"palabra", "fallos", "ultima_vez", "frase"} (`frase` puede
    ser None en fallos registrados antes de guardarla). Orden: mas fallos
    primero y, a igualdad, la mas reciente. Lista vacia si este lector no tiene
    historial. Si lo tiene y no se puede leer, `HistorialIlegible`: antes era
    tambien una lista vacia, que decia «no has fallado nada». La base es la del
    lector: pasale su `ruta`.
    """
    if not os.path.exists(ruta):
        return []
    try:
        con = _conectar(ruta)
        try:
            cur = con.execute(
                "SELECT palabra, fallos, ultima_vez, frase FROM palabras_debiles "
                + _FILTRO_DIFICILES +
                "ORDER BY fallos DESC, ultima_vez DESC LIMIT ?",
                (*_PARAMETROS_FILTRO, max(0, int(n))))
            return [{"palabra": p, "fallos": f, "ultima_vez": u, "frase": fr}
                    for p, f, u, fr in cur.fetchall()]
        finally:
            con.close()
    except Exception as e:
        raise HistorialIlegible(
            "No he podido leer tu historial de pronunciación ahora mismo "
            f"({type(e).__name__}). Vuelve a intentarlo en un momento.") from e


def puntos_debiles(n: int = 10, ruta: str = RUTA_DB_POR_DEFECTO) -> list[tuple[str, int]]:
    """Las `n` palabras que mas fallos acumulan, de mas a menos fallos.

    Devuelve pares (palabra, fallos). Lista vacia si no hay historial; si lo
    hay y no se puede leer, `HistorialIlegible` (ver `palabras_para_practicar`).
    """
    if not os.path.exists(ruta):
        return []
    try:
        con = _conectar(ruta)
        try:
            cur = con.execute(
                "SELECT palabra, fallos FROM palabras_debiles "
                + _FILTRO_DIFICILES +
                "ORDER BY fallos DESC, ultima_vez DESC LIMIT ?", (*_PARAMETROS_FILTRO, n))
            return cur.fetchall()
        finally:
            con.close()
    except Exception as e:
        raise HistorialIlegible(
            "No he podido leer tu historial de pronunciación ahora mismo "
            f"({type(e).__name__}). Vuelve a intentarlo en un momento.") from e


# --- Ciclo completo -----------------------------------------------------

# --- Ritmo: pausas y velocidad medidas (lectura natural, parte 1) -------
# Miguel (14 sep): «cuando leo suena muy cortado, muy robótico; que me diga dónde
# acelerar». Las marcas de tiempo por palabra de whisper-1 (verbose_json, que se
# factura igual que la transcripcion normal: por segundos de audio) dicen donde se
# paro el lector y a que velocidad fue cada tramo. Se comparan con las de la frase
# bien leida: el mp3 de referencia, transcrito UNA vez y guardado a su lado. Sin
# marcas del lector no se marca nada: serian adivinadas.

UMBRAL_PAUSA_S = 0.25   # un hueco mayor entre dos palabras parte el tramo
PAUSA_DE_MAS_S = 0.35   # uno mayor que la referencia no tiene, se señala
# Velocidad objetivo, en fraccion de la referencia, por nivel del lector (escala
# publica 0-2; Central, 14 sep): la referencia es un TTS rapido y algo
# artificial, y a un lector basico no se le pide ir tan deprisa.
FACTOR_OBJETIVO = ((0.7, 0.8), (1.4, 0.9), (float("inf"), 1.0))
FACTOR_SIN_NIVEL = 0.9  # sin perfil, el de intermedio


def factor_objetivo(nivel) -> float:
    """Fraccion de la velocidad de referencia que se pide a este nivel."""
    try:
        n = float(nivel)
    except (TypeError, ValueError):
        return FACTOR_SIN_NIVEL
    if n != n:
        return FACTOR_SIN_NIVEL
    return next(f for tope, f in FACTOR_OBJETIVO if n < tope)


def _campo(obj, nombre, defecto=None):
    """El SDK devuelve objetos; una cache o una prueba, diccionarios."""
    if isinstance(obj, dict):
        return obj.get(nombre, defecto)
    return getattr(obj, nombre, defecto)


def transcribir_con_tiempos(ruta_audio: str | os.PathLike) -> dict | None:
    """{"texto", "duracion", "palabras": [{"palabra", "inicio", "fin"}]} con
    whisper-1 y marcas por palabra, o `None` sin clave o si falla. Nunca lanza."""
    cliente = _cliente()
    if cliente is None:
        return None
    try:
        with open(ruta_audio, "rb") as f:
            r = cliente.audio.transcriptions.create(
                model=MODELO_TRANSCRIPCION, file=f, response_format="verbose_json",
                timestamp_granularities=["word"])
        palabras = []
        for w in _campo(r, "words") or []:
            try:
                palabras.append({"palabra": str(_campo(w, "word", "") or ""),
                                 "inicio": float(_campo(w, "start")), "fin": float(_campo(w, "end"))})
            except (TypeError, ValueError):
                continue
        duracion = _campo(r, "duration")
        return {"texto": str(_campo(r, "text", "") or ""),
                "duracion": float(duracion) if duracion is not None else None,
                "palabras": palabras}
    except Exception:
        return None


def _tiempos_de_referencia(ruta_mp3) -> dict | None:
    """Las marcas del mp3 de la frase bien leida, transcrito una sola vez y
    guardado al lado (`<mp3>.tiempos.json`): la misma frase no se vuelve a pagar."""
    if not ruta_mp3:
        return None
    lado = Path(str(ruta_mp3) + ".tiempos.json")
    try:
        if lado.is_file():
            datos = json.loads(lado.read_text(encoding="utf-8"))
            if isinstance(datos, dict) and isinstance(datos.get("palabras"), list):
                return datos
    except (OSError, ValueError):
        pass
    datos = transcribir_con_tiempos(ruta_mp3)
    if datos and datos["palabras"]:
        try:
            descriptor, temporal = tempfile.mkstemp(dir=str(lado.parent), prefix=f".{lado.name}.", suffix=".tmp")
            with os.fdopen(descriptor, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False)
            os.replace(temporal, lado)
        except OSError:
            pass
    return datos


def _tiempos_por_indice(objetivo: list[str], tiempos: dict | None) -> dict[int, tuple[float, float]]:
    """{indice en `objetivo`: (inicio, fin)} de las palabras que whisper oyo iguales."""
    if not tiempos:
        return {}
    oidas, marcas = [], []
    for w in tiempos.get("palabras") or []:
        try:
            marca = (float(w["inicio"]), float(w["fin"]))
        except (KeyError, TypeError, ValueError):
            continue
        for trozo in normalizar_palabras(w.get("palabra", "")):
            oidas.append(trozo)
            marcas.append(marca)
    por_indice = {}
    for tag, i1, i2, j1, _j2 in difflib.SequenceMatcher(None, objetivo, oidas, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                por_indice[i1 + k] = marcas[j1 + k]
    return por_indice


def medir_ritmo(evaluacion: Evaluacion, tiempos_lector: dict | None,
                tiempos_referencia: dict | None, nivel=None) -> dict:
    """Pausas y velocidad por tramo del intento, frente a la frase bien leida.

    Indices: posiciones en `evaluacion.palabras_objetivo`; `hasta` es inclusivo.
    `medido` es False sin marcas del lector, y entonces no se marca nada. Un
    tramo sin marcas de referencia lleva `objetivo` None y nunca `acelerar`.
    `natural` lo rellena la parte 2 (analisis de OpenAI)."""
    objetivo = evaluacion.palabras_objetivo
    lector = _tiempos_por_indice(objetivo, tiempos_lector)
    ref = _tiempos_por_indice(objetivo, tiempos_referencia)
    ritmo = {"medido": bool(lector), "duracion_s": None, "palabras": [], "pausas": [],
             "tramos": [], "natural": None}
    if not lector:
        return ritmo
    if tiempos_lector.get("duracion") is not None:
        ritmo["duracion_s"] = round(float(tiempos_lector["duracion"]), 2)
    ritmo["palabras"] = [{"palabra": objetivo[i], "inicio": round(a, 2), "fin": round(b, 2)}
                         for i, (a, b) in sorted(lector.items())]
    indices = sorted(lector)
    tramos, actual = [], [indices[0]]
    for i, j in zip(indices, indices[1:]):
        hueco = lector[j][0] - lector[i][1]
        if j == i + 1 and hueco > UMBRAL_PAUSA_S:
            en_referencia = i in ref and j in ref and ref[j][0] - ref[i][1] > UMBRAL_PAUSA_S
            ritmo["pausas"].append({"despues_de": i, "segundos": round(hueco, 2),
                                    "en_referencia": en_referencia,
                                    "de_mas": hueco > PAUSA_DE_MAS_S and not en_referencia})
        if j != i + 1 or hueco > UMBRAL_PAUSA_S:
            # Pausa, o una palabra sin marca en medio (whisper oyo otra): el tramo acaba.
            tramos.append(actual)
            actual = [j]
        else:
            actual.append(j)
    tramos.append(actual)
    factor = factor_objetivo(nivel)
    for tramo in tramos:
        if len(tramo) < 2:
            continue
        duracion = lector[tramo[-1]][1] - lector[tramo[0]][0]
        if duracion <= 0:
            continue
        velocidad = len(tramo) / duracion
        referencia = objetivo_pps = None
        if all(k in ref for k in tramo):
            duracion_ref = ref[tramo[-1]][1] - ref[tramo[0]][0]
            if duracion_ref > 0:
                referencia = len(tramo) / duracion_ref
                objetivo_pps = referencia * factor
        ritmo["tramos"].append({
            "desde": tramo[0], "hasta": tramo[-1], "palabras_por_segundo": round(velocidad, 2),
            "referencia": round(referencia, 2) if referencia else None,
            "objetivo": round(objetivo_pps, 2) if objetivo_pps else None,
            "acelerar": bool(objetivo_pps and velocidad < objetivo_pps)})
    return ritmo


# --- Lectura natural: enfasis, enlaces y reducciones (parte 2) ----------
# Lo que la medicion no puede saber: que palabras llevan el acento de la frase,
# cuales se enlazan («an apple» -> /ə.ˈnæpəl/) y que formas debiles y fusiones
# tiene el habla rapida («don't you» -> «doncha»). Una llamada por FRASE a
# gpt-4o-mini con salida estructurada, guardada en disco: la misma frase no se
# vuelve a pagar, para ningun lector, y lo guardado se sirve aunque no haya clave.
# Regla de veracidad, como en el diccionario: el modelo no toca las palabras;
# contesta con posiciones de la lista numerada y lo que no casa se descarta.

# v2: reducciones solo de la lista, enlaces comprobados con la IPA y version
# natural reconstruida. Lo guardado en v1 pudo traer una reduccion inventada.
VERSION_ANALISIS_NATURAL = "v2"
TIPOS_ENLACE = frozenset({"consonante_vocal", "vocal_vocal", "r_de_enlace"})
MAX_PALABRAS_REDUCCION = 4
# Reducciones que se aceptan, por las palabras exactas que reducen. Lo que el
# modelo proponga fuera de esta lista se descarta: en la primera frase real
# («Don't you want to come with us?») propuso «to come» -> «gonna», que no existe
# (gonna es «going to»), junto a doncha y wanna, que si. Lista corta y conocida.
REDUCCIONES_CONOCIDAS = {
    ("going", "to"): {"gonna"}, ("want", "to"): {"wanna"}, ("got", "to"): {"gotta"},
    ("have", "to"): {"hafta"}, ("has", "to"): {"hasta"}, ("ought", "to"): {"oughta"},
    ("kind", "of"): {"kinda"}, ("sort", "of"): {"sorta"}, ("out", "of"): {"outta"},
    ("lot", "of"): {"lotta"}, ("cup", "of"): {"cuppa"},
    ("let", "me"): {"lemme"}, ("give", "me"): {"gimme"}, ("don't", "know"): {"dunno"},
    ("don't", "you"): {"doncha", "dontcha"}, ("won't", "you"): {"woncha", "wontcha"},
    ("did", "you"): {"didja", "dija"}, ("would", "you"): {"wouldja", "wudja"},
    ("could", "you"): {"couldja", "cudja"}, ("got", "you"): {"gotcha"}, ("bet", "you"): {"betcha"},
    ("what", "are", "you"): {"whatcha", "whaddaya"}, ("what", "do", "you"): {"whaddaya", "whatcha"},
    ("i", "am"): {"i'm"}, ("i", "would"): {"i'd"}, ("i", "had"): {"i'd"}, ("i", "will"): {"i'll"},
    ("i", "have"): {"i've"}, ("you", "are"): {"you're"}, ("we", "are"): {"we're"},
    ("they", "are"): {"they're"}, ("it", "is"): {"it's"}, ("that", "is"): {"that's"},
    ("do", "not"): {"don't"}, ("does", "not"): {"doesn't"}, ("did", "not"): {"didn't"},
    ("can", "not"): {"can't"}, ("will", "not"): {"won't"}, ("is", "not"): {"isn't"},
    ("are", "not"): {"aren't"},
    ("and",): {"'n'", "'n", "n"}, ("them",): {"'em", "em"}, ("you",): {"ya"},
    ("because",): {"'cause", "cause", "cuz"},
}


class EnfasisPalabra(BaseModel):
    indice: int = Field(description="Posicion de la palabra en la lista numerada.")
    ipa: str = Field(description="IPA americana de la palabra, entre barras, con ˈ delante de la silaba tonica.")


class EnlacePalabras(BaseModel):
    de: int = Field(description="Posicion de la primera palabra.")
    a: int = Field(description="Posicion de la palabra siguiente (de + 1).")
    tipo: str = Field(description="consonante_vocal, vocal_vocal o r_de_enlace.")
    ipa: str = Field(description="IPA americana de las dos palabras unidas, entre barras.")


class ReduccionHabla(BaseModel):
    desde: int = Field(description="Posicion de la primera palabra de la reduccion.")
    hasta: int = Field(description="Posicion de la ultima palabra (igual a desde si es una sola).")
    forma: str = Field(description="Como suena escrito de forma coloquial: doncha, wanna, gonna.")
    ipa: str = Field(description="IPA americana de la forma rapida, entre barras.")


class TramoRapido(BaseModel):
    desde: int
    hasta: int


class AnalisisNatural(BaseModel):
    enfasis: list[EnfasisPalabra]
    enlaces: list[EnlacePalabras]
    reducciones: list[ReduccionHabla]
    tramos_rapidos: list[TramoRapido]
    version_natural: str = Field(description="La frase escrita como suena rapido, solo para una voz sintetica.")


_PROMPT_NATURAL = (
    "Eres profesor de pronunciacion de ingles americano (General American) para "
    "hispanohablantes. Recibes una frase y sus palabras numeradas. Devuelve como se "
    "dice con naturalidad, a velocidad normal de conversacion:\n"
    "- enfasis: las palabras que llevan el acento de la frase (normalmente las de "
    "contenido que aportan la informacion), pocas, con su IPA americana entre barras y "
    "ˈ delante de la silaba tonica.\n"
    "- enlaces: pares de palabras SEGUIDAS (a = de + 1) que se pronuncian unidas: "
    "consonante_vocal («an apple» /ə.ˈnæpəl/), vocal_vocal con una /j/ o /w/ de "
    "transicion («go on» /ɡoʊ.wɑn/) o r_de_enlace. Con la IPA de la union.\n"
    "- reducciones: formas debiles o fusiones del habla rapida que de verdad se dan en "
    "esta frase (don't you -> doncha /ˈdoʊntʃə/, want to -> wanna, going to -> gonna, "
    "and -> /ən/). desde y hasta son las posiciones de la primera y la ultima palabra.\n"
    "- tramos_rapidos: grupos de palabras que se dicen de un tiron, sin pausa.\n"
    "- version_natural: la frase reescrita como suena rapido, solo para una voz sintetica "
    "(«I wanna go»). Si no hay reducciones, la frase tal cual.\n"
    "Reglas: no cambies, anadas ni quites palabras; usa SOLO las posiciones de la lista; "
    "no inventes fenomenos que no se dan en esta frase; si no hay nada de un tipo, lista vacia."
)


def _bordes_sonoros(palabra: str) -> tuple[str | None, str | None]:
    """(tipo del primer sonido, tipo del ultimo) de la IPA de diccionario de la
    palabra: consonante, vocal o diptongo; (None, None) si no hay IPA."""
    try:
        ipa, _ = fonemas.ipa_de_palabra(palabra)
    except Exception:
        return None, None
    tipos = [getattr(fonemas.buscar(s), "tipo", None) for s in (fonemas.segmentar(ipa) if ipa else [])]
    tipos = [x for x in tipos if x]
    return (tipos[0], tipos[-1]) if tipos else (None, None)


def _enlace_real(tipo: str, primera: str, segunda: str) -> bool:
    """Si el tipo de enlace que dice el modelo se da con los sonidos de verdad.
    «don't you» no es consonante+vocal («you» empieza por /j/) y «to come» no
    se enlaza: los dos salieron asi en la primera frase real."""
    _, fin_primera = _bordes_sonoros(primera)
    inicio_segunda, _ = _bordes_sonoros(segunda)
    vocales = ("vocal", "diptongo")
    if tipo == "consonante_vocal":
        return fin_primera == "consonante" and inicio_segunda in vocales
    if tipo == "vocal_vocal":
        return fin_primera in vocales and inicio_segunda in vocales
    if tipo == "r_de_enlace":
        return str(primera).lower().rstrip("'").endswith(("r", "re")) and inicio_segunda in vocales
    return False


def _ipa_corta(texto) -> str | None:
    """IPA del modelo entre barras, o None si viene vacia o desmedida."""
    t = str(texto or "").strip()
    if not t or len(t) > 40:
        return None
    return t if t.startswith("/") and t.endswith("/") and len(t) > 2 else f"/{t.strip('/[] ')}/"


def _validar_natural(bruto, palabras: list[str], frase: str) -> dict:
    """Lo que devuelve el modelo, quedandose solo con lo que casa con la frase:
    posiciones de verdad, enlaces que se dan con esos sonidos, reducciones de la
    lista y una version natural que diga exactamente eso."""
    datos = bruto.model_dump() if hasattr(bruto, "model_dump") else dict(bruto or {})
    palabras = [str(w).lower() for w in palabras]
    n_palabras = len(palabras)

    def indice(valor):
        try:
            i = int(valor)
        except (TypeError, ValueError):
            return None
        return i if 0 <= i < n_palabras else None

    enfasis, vistos = [], set()
    for e in datos.get("enfasis") or []:
        i = indice(_campo(e, "indice"))
        if i is not None and i not in vistos:
            vistos.add(i)
            enfasis.append({"indice": i, "ipa": _ipa_corta(_campo(e, "ipa"))})
    enlaces = []
    for e in datos.get("enlaces") or []:
        de, a, tipo = indice(_campo(e, "de")), indice(_campo(e, "a")), str(_campo(e, "tipo", "") or "")
        if (de is not None and a == de + 1 and tipo in TIPOS_ENLACE
                and _enlace_real(tipo, palabras[de], palabras[a])):
            enlaces.append({"de": de, "a": a, "tipo": tipo, "ipa": _ipa_corta(_campo(e, "ipa"))})
    reducciones = []
    for r in datos.get("reducciones") or []:
        desde, hasta = indice(_campo(r, "desde")), indice(_campo(r, "hasta"))
        forma, ipa = str(_campo(r, "forma", "") or "").strip(), _ipa_corta(_campo(r, "ipa"))
        if not (desde is not None and hasta is not None and desde <= hasta < desde + MAX_PALABRAS_REDUCCION
                and forma and len(forma) <= 30 and ipa):
            continue
        conocidas = REDUCCIONES_CONOCIDAS.get(tuple(palabras[desde:hasta + 1]), set())
        solapa = any(desde <= r_["hasta"] and r_["desde"] <= hasta for r_ in reducciones)
        if forma.lower() in conocidas and not solapa:
            reducciones.append({"desde": desde, "hasta": hasta, "forma": forma, "ipa": ipa,
                                "generado_por_ia": True})
    tramos = []
    for tr in datos.get("tramos_rapidos") or []:
        desde, hasta = indice(_campo(tr, "desde")), indice(_campo(tr, "hasta"))
        if desde is not None and hasta is not None and desde < hasta:
            tramos.append({"desde": desde, "hasta": hasta})
    frase = str(frase or "").strip()
    # La version natural tiene que decir exactamente la frase con las reducciones
    # validadas; si dice otra cosa (una reduccion descartada, una palabra de mas),
    # se reconstruye. Sin reducciones, la frase tal cual.
    esperadas = list(palabras)
    for r_ in sorted(reducciones, key=lambda x: x["desde"], reverse=True):
        esperadas[r_["desde"]:r_["hasta"] + 1] = normalizar_palabras(r_["forma"])
    version = str(datos.get("version_natural") or "").strip()
    if not reducciones:
        version = frase
    elif not version or len(version) > 2 * len(frase) + 20 or normalizar_palabras(version) != esperadas:
        texto = " ".join(esperadas)
        final = frase[-1] if frase and frase[-1] in ".?!" else ""
        version = texto[:1].upper() + texto[1:] + final
    return _pulir_natural({"enfasis": enfasis, "enlaces": enlaces, "reducciones": reducciones,
                           "tramos_rapidos": tramos, "version_natural": version}, palabras)


def _ipa_enlace(primera: str, segunda: str) -> str | None:
    """La IPA de dos palabras enlazadas, sacada del DICCIONARIO de cada una y
    unida con ‿. La del modelo no valia: en la bateria del 14 sep daba «/ə/» para
    «little of» o «/sɔrts.ə/» para «sorts of»."""
    partes = []
    for palabra in (primera, segunda):
        try:
            ipa, _ = fonemas.ipa_de_palabra(palabra)
        except Exception:
            ipa = None
        if not ipa:
            return None
        partes.append(str(ipa).strip().strip("/[]"))
    return "/" + "‿".join(partes) + "/"


def _pulir_natural(datos: dict, palabras: list[str]) -> dict:
    """Lo que pasa siempre, tambien a lo que ya estaba guardado: el enfasis nunca
    cae en una palabra funcional («of», «the»), y la IPA de cada enlace sale del
    diccionario. Asi la cache vieja se corrige al leerla, sin volver a pagar."""
    palabras = [str(w).lower() for w in palabras]
    n = len(palabras)
    datos = dict(datos)
    datos["enfasis"] = [e for e in datos.get("enfasis") or []
                        if isinstance(e.get("indice"), int) and 0 <= e["indice"] < n
                        and palabras[e["indice"]] not in _PALABRAS_FUNCIONALES]
    enlaces = []
    for e in datos.get("enlaces") or []:
        de, a = e.get("de"), e.get("a")
        if isinstance(de, int) and isinstance(a, int) and 0 <= de and a == de + 1 < n:
            enlaces.append({**e, "ipa": _ipa_enlace(palabras[de], palabras[a])})
    datos["enlaces"] = enlaces
    return datos


def _ruta_analisis_natural(frase: str) -> Path:
    clave = hashlib.sha256(
        f"{VERSION_ANALISIS_NATURAL}|{MODELO_EXPLICACION}|{frase}".encode("utf-8")).hexdigest()
    return Path(RUTA_AUDIO_GENERADO).parent / "analisis_natural" / f"{clave}.json"


def analizar_natural(frase: str, palabras_objetivo: list[str] | None = None) -> dict | None:
    """Enfasis, enlaces, reducciones, tramos rapidos y version natural de la frase,
    ya validados contra sus palabras. De la cache si esta; si no, una llamada.
    `None` si no hay nada guardado y no hay clave, o si la llamada falla."""
    frase = str(frase or "").strip()
    palabras = list(palabras_objetivo) if palabras_objetivo is not None else normalizar_palabras(frase)
    if not frase or not palabras:
        return None
    ruta = _ruta_analisis_natural(frase)
    try:
        if ruta.is_file():
            guardado = json.loads(ruta.read_text(encoding="utf-8"))
            if isinstance(guardado, dict) and isinstance(guardado.get("enlaces"), list):
                return _pulir_natural(guardado, palabras)
    except (OSError, ValueError):
        pass
    cliente = _cliente()
    if cliente is None:
        return None
    numeradas = " ".join(f"{i}:{p}" for i, p in enumerate(palabras))
    try:
        resp = cliente.chat.completions.parse(
            model=MODELO_EXPLICACION,
            messages=[{"role": "system", "content": _PROMPT_NATURAL},
                      {"role": "user", "content": f"Frase: {frase}\nPalabras numeradas: {numeradas}"}],
            response_format=AnalisisNatural)
        bruto = resp.choices[0].message.parsed
    except Exception:
        return None
    if bruto is None:
        return None
    datos = _validar_natural(bruto, palabras, frase)
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporal = tempfile.mkstemp(dir=str(ruta.parent), prefix=f".{ruta.name}.", suffix=".tmp")
        with os.fdopen(descriptor, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
        os.replace(temporal, ruta)
    except OSError:
        pass
    return datos


# --- Historial del ritmo (lectura natural, parte 3) --------------------
# Por frase, lo medido en cada intento: palabras por segundo, pausas de mas y
# tramos a acelerar, para enseñar si mejora. Nada de audio ni del analisis del
# modelo, que se regenera desde su cache. Misma base que las palabras dificiles
# (la del lector); la tabla se crea la primera vez, con la migracion serializada.

def _conectar_ritmo(ruta: str = RUTA_DB_POR_DEFECTO) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    con = sqlite3.connect(ruta)
    try:
        existe = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ritmo_intentos'").fetchone()
        if not existe:
            con.execute("BEGIN IMMEDIATE")
            con.execute("""
                CREATE TABLE IF NOT EXISTS ritmo_intentos (
                    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                    frase                TEXT NOT NULL,
                    fecha                TEXT NOT NULL,
                    palabras_por_segundo REAL,
                    pausas_de_mas        INTEGER NOT NULL DEFAULT 0,
                    tramos_a_acelerar    INTEGER NOT NULL DEFAULT 0
                )
            """)
            con.execute("CREATE INDEX IF NOT EXISTS ritmo_intentos_frase ON ritmo_intentos (frase, fecha)")
            con.commit()
    except BaseException:
        con.close()
        raise
    return con


def _resumen_ritmo(ritmo: dict) -> tuple[float | None, int, int]:
    """(palabras por segundo de todo el intento, pausas de mas, tramos a acelerar)."""
    palabras = ritmo.get("palabras") or []
    velocidad = None
    if len(palabras) >= 2:
        duracion = float(palabras[-1]["fin"]) - float(palabras[0]["inicio"])
        if duracion > 0:
            velocidad = round(len(palabras) / duracion, 2)
    pausas = sum(1 for x in ritmo.get("pausas") or [] if x.get("de_mas"))
    tramos = sum(1 for x in ritmo.get("tramos") or [] if x.get("acelerar"))
    return velocidad, pausas, tramos


def registrar_ritmo(ritmo: dict | None, frase: str, ruta: str = RUTA_DB_POR_DEFECTO) -> None:
    """Guarda lo medido en un intento. Sin medicion (sin clave, sin marcas) no se
    guarda nada: seria un intento vacio. Nunca lanza, como `registrar_fallos`."""
    frase = str(frase or "").strip()[:400]
    if not ritmo or not ritmo.get("medido") or not frase:
        return
    try:
        velocidad, pausas, tramos = _resumen_ritmo(ritmo)
        con = _conectar_ritmo(ruta)
        try:
            with con:
                con.execute("INSERT INTO ritmo_intentos (frase, fecha, palabras_por_segundo, pausas_de_mas, "
                            "tramos_a_acelerar) VALUES (?, ?, ?, ?, ?)",
                            (frase, _ahora(), velocidad, pausas, tramos))
        finally:
            con.close()
    except Exception:
        pass


def evolucion_ritmo(frase: str, n: int = 10, ruta: str = RUTA_DB_POR_DEFECTO) -> list[dict]:
    """Los ultimos `n` intentos medidos de esa frase, del mas antiguo al mas
    reciente: [{"fecha", "palabras_por_segundo", "pausas_de_mas", "tramos_a_acelerar"}].
    Lista vacia sin historial; si lo hay y no se puede leer, `HistorialIlegible`."""
    frase = str(frase or "").strip()[:400]
    if not frase or not os.path.exists(ruta):
        return []
    try:
        con = _conectar_ritmo(ruta)
        try:
            filas = con.execute(
                "SELECT fecha, palabras_por_segundo, pausas_de_mas, tramos_a_acelerar FROM ritmo_intentos "
                "WHERE frase = ? ORDER BY fecha DESC, id DESC LIMIT ?", (frase, max(0, int(n)))).fetchall()
        finally:
            con.close()
    except Exception as e:
        raise HistorialIlegible(
            "No he podido leer tu historial de pronunciación ahora mismo "
            f"({type(e).__name__}). Vuelve a intentarlo en un momento.") from e
    return [{"fecha": f, "palabras_por_segundo": v, "pausas_de_mas": p, "tramos_a_acelerar": tr}
            for f, v, p, tr in reversed(filas)]


@dataclass
class SesionVoz:
    evaluacion: Evaluacion
    correccion: Correccion | None = None
    audio_correcto: str | None = None
    transcripcion_ok: bool = True   # False si no se pudo transcribir (sin red/clave)
    # Audio de CADA palabra fallada, sola: {palabra normalizada: ruta del mp3}.
    # Miguel (13 sep): «me dices el error en la vocal, pero no como se escucha
    # la palabra sola; tengo que escuchar todo el texto». Solo las que tienen
    # audio; sin clave y sin cache, vacio.
    audios_palabras: dict[str, str] = field(default_factory=dict)
    # Pausas y velocidad del intento (ver `medir_ritmo`); None si no se midio.
    ritmo: dict | None = None


# 8 y no 6: un compuesto fallado pide tres (el compuesto y sus dos piezas).
MAX_AUDIOS_PALABRA = 8


def audios_de_palabras(palabras: list[str]) -> dict[str, str]:
    """El mp3 de cada palabra (hasta MAX_AUDIOS_PALABRA, sin repetir), pedido a
    la vez. Reutiliza la cache por contenido de `generar_audio_correcto`: una
    palabra ya generada no se vuelve a pagar y se sirve aunque no haya clave."""
    unicas = list(dict.fromkeys(p for p in palabras if p))[:MAX_AUDIOS_PALABRA]
    if not unicas:
        return {}
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(4, len(unicas))) as grupo:
        rutas = list(grupo.map(generar_audio_correcto, unicas))
    return {p: r for p, r in zip(unicas, rutas) if r}


def practicar(ruta_audio: str | os.PathLike, frase_objetivo: str,
             guardar_fallos: bool = True, nivel: float | None = None) -> SesionVoz:
    """Ciclo completo de practica: transcribe el audio del usuario, evalua
    contra la frase objetivo, explica como corregir lo que fallo, genera un
    audio de referencia y registra las palabras debiles.

    Si no hay OPENAI_API_KEY (o falla la red), la transcripcion es `None` y
    la evaluacion se hace contra una cadena vacia (todo cuenta como fallado);
    `transcripcion_ok` queda en `False` para que la interfaz pueda avisar sin
    que la funcion lance ninguna excepcion.
    """
    # Con marcas por palabra para medir el ritmo; es la misma llamada de siempre
    # con otro formato. Si no llegan, la transcripcion de antes: sin clave no
    # sale ninguna llamada y, si fallo el formato con marcas, sale una sola.
    tiempos = transcribir_con_tiempos(ruta_audio)
    transcripcion = tiempos["texto"] if tiempos is not None else None
    if tiempos is None:
        transcripcion = transcribir_audio(ruta_audio)
    evaluacion = evaluar_pronunciacion(frase_objetivo, transcripcion or "")

    if guardar_fallos and evaluacion.palabras_falladas:
        registrar_fallos(evaluacion.palabras_falladas, frase=frase_objetivo)

    correccion = None
    if evaluacion.palabras_falladas:
        correccion = explicar_correccion(evaluacion.palabras_falladas,
                                         entendidas=evaluacion.entendidas)

    # El audio de referencia se genera SIEMPRE, no solo cuando algo falla.
    # Antes iba dentro del `if`: quien pronunciaba bien se encontraba el
    # rotulo "Cómo debería sonar" con el reproductor vacio, que es justo
    # cuando uno quiere oirlo para confirmar que lo hizo bien. Y repetir una
    # frase ya generada no cuesta nada: `generar_audio_correcto` cachea por
    # contenido.
    audio_correcto = generar_audio_correcto(frase_objetivo)
    # Y cada palabra fallada, sola. Solo si hubo transcripcion: sin ella todas
    # cuentan como falladas y serian audios de pago para nada.
    # Tambien las piezas de cada compuesto y las palabras que nombra la
    # correccion: «war-chant» se evalua entero, pero el modelo lo explica en
    # «war» y «chant», y Miguel no pudo oir ninguna de las dos (e6, 13 sep).
    # Cada pieza se paga una vez: la cache es por contenido.
    audios = {}
    if transcripcion is not None:
        pedidas = []
        for palabra in evaluacion.palabras_falladas:
            pedidas.append(palabra)
            if "-" in palabra:
                pedidas.extend(_clave_palabra(p) for p in piezas(palabra))
        if correccion is not None:
            pedidas.extend(_clave_palabra(d.palabra) for d in correccion.detalles)
        audios = audios_de_palabras(pedidas)

    ritmo = medir_ritmo(evaluacion, tiempos,
                        _tiempos_de_referencia(audio_correcto) if tiempos else None, nivel)
    # Enfasis, enlaces y reducciones de la frase (una llamada por frase, cacheada)
    # y la frase dicha con naturalidad. Si la version natural es la misma frase,
    # su audio es el de referencia: no se genera otro.
    natural = analizar_natural(frase_objetivo, evaluacion.palabras_objetivo)
    if natural is not None:
        natural = dict(natural)
        texto_natural = natural.get("version_natural") or frase_objetivo
        natural["audio_natural"] = (audio_correcto if texto_natural.strip() == frase_objetivo.strip()
                                    else generar_audio_correcto(texto_natural))
        ritmo["natural"] = natural
    # Como los fallos: con guardar_fallos, practicar guarda el intento; la API y
    # Gradio lo llaman con False y guardan ellos, en la base de su lector.
    if guardar_fallos:
        registrar_ritmo(ritmo, frase_objetivo)
    return SesionVoz(evaluacion=evaluacion, correccion=correccion,
                     audio_correcto=audio_correcto, transcripcion_ok=transcripcion is not None,
                     audios_palabras=audios, ritmo=ritmo)
