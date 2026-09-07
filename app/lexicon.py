"""Consulta lexica de LiteraLevel: diccionario, IPA/audio y explicacion contextual.

Fuente del diccionario: volcado de Kaikki/Wiktionary en SQLite local
(`kaikki_diccionario.db`, 1.48M filas, sin limites de API). Oxford Dictionaries
se descarto por dar 403 en las claves disponibles.

Pipeline por consulta, portado y ampliado desde el prototipo en Streamlit:
  1. spaCy (`en_core_web_sm`) da el lema y la categoria gramatical de la
     palabra dentro de SU oracion. Si el token ancla es un verbo con
     particula (phrasal verb: "set off", "give up"...) se intenta primero
     la entrada compuesta en el diccionario, y si no existe se cae al lema
     simple.
  2. El mapa POS_SPACY_A_CATEGORIA filtra las entradas del diccionario por
     categoria. Si el filtro deja la lista vacia (p.ej. "notwithstanding",
     que spaCy etiqueta ADP y no esta en el mapa), se usan todos los
     sentidos disponibles.
  3. Si quedan varios sentidos candidatos, se elige el mas afin al contexto
     por similitud coseno entre la oracion y cada glosa, con
     SentenceTransformer("all-MiniLM-L6-v2").
  4. OpenAI (Structured Outputs + Pydantic) SOLO aporta lo contextual y
     gramatical: nunca redefine la palabra, se le pasa la glosa elegida y se
     le prohibe explicitamente inventar otra.
  5. Se devuelven tambien IPA UK/US y audio UK/US de la base. Si la base no
     trae audio para esa palabra, se genera con `tts-1` (OpenAI) y se guarda
     en disco, marcando `audio_generado=True`.
  6. Cache en disco obligatoria en SQLite (~/.literalevel/lexicon.db): antes
     de cualquier llamada a OpenAI (texto o audio) se consulta la cache.
  7. Degradacion elegante: sin OPENAI_API_KEY o sin red, `consultar()` NUNCA
     lanza excepcion; devuelve lo que si consiguio (diccionario + IPA +
     audio) y describe en `avisos` que falto.

Nota de diseno: las explicaciones (`definicion_contextual`,
`explicacion_gramatical`, `explicacion_adaptada`) se piden en espanol, porque
LiteraLevel esta pensado para lectores hispanohablantes que leen literatura en
ingles; el `ejemplo_simplificado` se pide en ingles porque es material de
lectura, no un andamiaje en la lengua materna.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from config import obtener
from scoring import public_band

# --- Rutas y constantes -------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
# Configurable por entorno: al desplegar, el .db de 233 MB se monta como
# volumen de solo lectura fuera del repositorio.
RUTA_DICCIONARIO = Path(os.environ.get("LITERALEVEL_DICCIONARIO",
                                       RAIZ / "kaikki_diccionario.db"))
RUTA_CACHE = Path(os.path.expanduser("~")) / ".literalevel" / "lexicon.db"
RUTA_AUDIO_GENERADO = Path(os.path.expanduser("~")) / ".literalevel" / "audio"

MODELO_EMBEDDINGS = "all-MiniLM-L6-v2"
MODELO_OPENAI_POR_DEFECTO = "gpt-5"
MODELO_TTS = "tts-1"
VOZ_TTS = "alloy"

# Mapa POS de spaCy -> categoria de Kaikki. Si el POS de spaCy no esta aqui
# (preposiciones, conjunciones, determinantes...) no se filtra por categoria.
POS_SPACY_A_CATEGORIA = {
    "VERB": "verb", "AUX": "verb",
    "NOUN": "noun", "PROPN": "noun",
    "ADJ": "adj", "ADV": "adv",
}


# --- Modelos de datos -----------------------------------------------------
@dataclass
class Sentido:
    """Un sentido (acepcion) de una entrada del diccionario."""
    glosa: str
    pos: str
    etiquetas: list[str] = field(default_factory=list)


@dataclass
class EntradaDiccionario:
    """Una fila de `entradas` (una palabra en una categoria gramatical)."""
    palabra: str
    pos: str
    sentidos: list[Sentido]
    ipa_uk: str | None
    ipa_us: str | None
    audio_uk: str | None
    audio_us: str | None


@dataclass
class ResultadoLexico:
    """Lo que devuelve una consulta lexica completa."""
    palabra_superficie: str        # la palabra tal como aparece en el texto
    oracion: str                   # la oracion de contexto usada
    lema: str                      # lema simple (spaCy)
    lema_buscado: str               # lema o frase realmente usada en la BD
    pos_spacy: str | None
    categoria: str | None          # categoria Kaikki tras el mapeo
    sentido: str | None            # glosa elegida (o None si no se encontro)
    etiquetas_sentido: list[str]
    similitud: float | None        # similitud coseno del sentido elegido
    n_sentidos_candidatos: int
    ipa_uk: str | None
    ipa_us: str | None
    audio_uk: str | None
    audio_us: str | None
    audio_generado: bool           # True si el audio vino de tts-1, no de la BD
    definicion_contextual: str | None
    explicacion_gramatical: str | None
    explicacion_adaptada: str | None
    ejemplo_simplificado: str | None
    banda_lector: str              # básico | intermedio | avanzado
    frecuencia_zipf: float | None  # rareza de la palabra (wordfreq); util para
                                    # decidir si vale la pena mostrar la ficha
    desde_cache: bool
    avisos: list[str]

    @property
    def completo(self) -> bool:
        """True si no falto nada (ni diccionario ni contexto de OpenAI)."""
        return not self.avisos


# --- spaCy y embeddings: carga perezosa y unica por proceso ---------------
_nlp = None
_embebedor = None


def _spacy_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def _cargar_embebedor():
    global _embebedor
    if _embebedor is None:
        from sentence_transformers import SentenceTransformer
        _embebedor = SentenceTransformer(MODELO_EMBEDDINGS)
    return _embebedor


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _frecuencia_zipf(lema: str) -> float | None:
    """Rareza de la palabra en escala Zipf (wordfreq). None si no se puede
    calcular: no es critico para la consulta, es informacion adicional."""
    try:
        from wordfreq import zipf_frequency
        return round(float(zipf_frequency(lema, "en")), 2)
    except Exception:
        return None


# --- Resolucion de lema y categoria a partir del contexto ------------------
def _resolver_lema_y_categoria(
    oracion: str, palabra_superficie: str,
) -> tuple[str, str, str | None, str | None]:
    """A partir de la oracion, ubica el token ancla de `palabra_superficie` y
    devuelve (lema_a_buscar, lema_simple, categoria_kaikki, pos_spacy).

    `lema_a_buscar` puede ser una frase ("set off") si el token ancla es un
    verbo con particula (dependencia "prt"); en ese caso se intenta primero
    esa frase completa en el diccionario y solo se cae al lema simple si no
    existe (ver `Diccionario.buscar` desde el llamador).
    """
    nlp = _spacy_nlp()
    doc = nlp(oracion)
    primera = palabra_superficie.split()[0].lower()
    ancla = next((t for t in doc if t.text.lower() == primera), None)
    if ancla is None:
        # La palabra no aparece literalmente en la oracion dada: se analiza
        # sola, sin contexto real (mejor que nada, pero sin desambiguacion).
        doc_suelto = nlp(palabra_superficie)
        ancla = doc_suelto[0] if len(doc_suelto) else None
    if ancla is None:
        lema = palabra_superficie.lower().strip()
        return lema, lema, None, None

    lema = ancla.lemma_.lower()
    categoria = POS_SPACY_A_CATEGORIA.get(ancla.pos_)
    particulas = [c.text.lower() for c in ancla.children if c.dep_ == "prt"]
    lema_frasal = f"{lema} {particulas[0]}" if particulas else None
    return (lema_frasal or lema), lema, categoria, ancla.pos_


def _elegir_sentido(
    oracion: str, candidatos: list[tuple[EntradaDiccionario, Sentido]],
) -> tuple[Sentido | None, float | None, list[str]]:
    """Elige el sentido mas afin al contexto por similitud coseno.

    Devuelve (sentido_elegido, similitud, avisos). Si solo hay un candidato
    no hace falta el modelo de embeddings. Si el modelo de embeddings no se
    puede cargar (p.ej. sin red la primera vez), se degrada eligiendo el
    primer candidato y lo dice en avisos, sin lanzar excepcion.
    """
    if not candidatos:
        return None, None, []
    if len(candidatos) == 1:
        return candidatos[0][1], None, []
    try:
        modelo = _cargar_embebedor()
        glosas = [s.glosa for _, s in candidatos]
        vectores = modelo.encode([oracion, *glosas], normalize_embeddings=True)
        v_contexto, v_glosas = vectores[0], vectores[1:]
        similitudes = v_glosas @ v_contexto
        idx = int(np.argmax(similitudes))
        return candidatos[idx][1], float(similitudes[idx]), []
    except Exception as e:
        aviso = f"sin modelo de embeddings ({type(e).__name__}): se tomo el primer sentido"
        return candidatos[0][1], None, [aviso]


def _mejor_fonetica(
    entradas: list[EntradaDiccionario], categoria: str | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    """IPA/audio de la mejor entrada disponible: se prioriza la categoria
    gramatical detectada, pero si esa entrada no trae fonetica se completa
    con cualquier otra entrada de la misma palabra."""
    ordenadas = entradas
    if categoria:
        ordenadas = (
            [e for e in entradas if e.pos == categoria]
            + [e for e in entradas if e.pos != categoria]
        )
    ipa_uk = ipa_us = audio_uk = audio_us = None
    for e in ordenadas:
        ipa_uk = ipa_uk or e.ipa_uk
        ipa_us = ipa_us or e.ipa_us
        audio_uk = audio_uk or e.audio_uk
        audio_us = audio_us or e.audio_us
    return ipa_uk, ipa_us, audio_uk, audio_us


# --- Diccionario (Kaikki/Wiktionary en SQLite) -----------------------------
class Diccionario:
    """Envoltorio de solo lectura sobre `kaikki_diccionario.db`."""

    def __init__(self, ruta: str | os.PathLike = RUTA_DICCIONARIO):
        ruta = str(ruta)
        if not os.path.exists(ruta):
            raise FileNotFoundError(
                f"No encuentro el diccionario Kaikki en {ruta}.\n"
                "Debe existir kaikki_diccionario.db en la raiz del proyecto "
                "(volcado de Kaikki/Wiktionary, tabla 'entradas')."
            )
        # mode=ro: la BD puede seguir siendo escrita por el proceso que la
        # genero; abrirla de solo lectura evita bloqueos.
        self._con = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True, check_same_thread=False)
        self._con.row_factory = sqlite3.Row

    def buscar(self, lema: str) -> list[EntradaDiccionario]:
        """Todas las entradas (una por categoria gramatical) para ese lema."""
        filas = self._con.execute(
            "SELECT * FROM entradas WHERE palabra = ?", (lema.lower(),)
        ).fetchall()
        entradas = []
        for f in filas:
            try:
                sentidos_json = json.loads(f["sentidos"]) if f["sentidos"] else []
            except json.JSONDecodeError:
                sentidos_json = []
            sentidos = [
                Sentido(glosa=s["glosa"], pos=f["pos"], etiquetas=s.get("tags", []))
                for s in sentidos_json if s.get("glosa")
            ]
            entradas.append(EntradaDiccionario(
                palabra=f["palabra"], pos=f["pos"], sentidos=sentidos,
                ipa_uk=f["ipa_uk"] or None, ipa_us=f["ipa_us"] or None,
                audio_uk=f["audio_uk"] or None, audio_us=f["audio_us"] or None,
            ))
        return entradas

    def cerrar(self) -> None:
        self._con.close()


# --- Cache en disco (obligatoria antes de llamar a OpenAI) -----------------
class CacheLexico:
    """Cache SQLite de respuestas de OpenAI (texto y audio generado).

    Requisito explicito del usuario: nunca se llama a OpenAI sin antes
    consultar esta cache, para no repetir gasto por la misma palabra en el
    mismo contexto y nivel.
    """

    def __init__(self, ruta: str | os.PathLike = RUTA_CACHE):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(self.ruta), check_same_thread=False)
        self._con.execute(
            "CREATE TABLE IF NOT EXISTS respuestas ("
            " clave TEXT PRIMARY KEY, respuesta TEXT NOT NULL,"
            " modelo TEXT NOT NULL, creado TEXT NOT NULL)"
        )
        self._con.execute(
            "CREATE TABLE IF NOT EXISTS audios ("
            " clave TEXT PRIMARY KEY, ruta TEXT NOT NULL, creado TEXT NOT NULL)"
        )
        self._con.commit()

    @staticmethod
    def _clave(*partes: str) -> str:
        return hashlib.sha256("\x1f".join(partes).encode("utf-8")).hexdigest()

    def obtener_respuesta(self, *partes: str) -> dict | None:
        clave = self._clave(*partes)
        fila = self._con.execute(
            "SELECT respuesta FROM respuestas WHERE clave = ?", (clave,)
        ).fetchone()
        return json.loads(fila[0]) if fila else None

    def guardar_respuesta(self, respuesta: dict, modelo: str, *partes: str) -> None:
        clave = self._clave(*partes)
        self._con.execute(
            "INSERT OR REPLACE INTO respuestas (clave, respuesta, modelo, creado) "
            "VALUES (?, ?, ?, ?)",
            (clave, json.dumps(respuesta, ensure_ascii=False), modelo, _ahora()),
        )
        self._con.commit()

    def obtener_audio(self, *partes: str) -> str | None:
        clave = self._clave(*partes)
        fila = self._con.execute(
            "SELECT ruta FROM audios WHERE clave = ?", (clave,)
        ).fetchone()
        if fila and os.path.exists(fila[0]):
            return fila[0]
        return None

    def guardar_audio(self, ruta: str, *partes: str) -> None:
        clave = self._clave(*partes)
        self._con.execute(
            "INSERT OR REPLACE INTO audios (clave, ruta, creado) VALUES (?, ?, ?)",
            (clave, ruta, _ahora()),
        )
        self._con.commit()

    def cerrar(self) -> None:
        self._con.close()


# --- OpenAI: solo lo contextual/gramatical, nunca la definicion ------------
def _modelo_respuesta_contextual():
    """Construye el modelo Pydantic de Structured Outputs de forma perezosa,
    para no exigir `pydantic` a quien solo use diccionario + IPA."""
    from pydantic import BaseModel

    class RespuestaContextual(BaseModel):
        definicion_contextual: str
        explicacion_gramatical: str
        explicacion_adaptada: str
        ejemplo_simplificado: str

    return RespuestaContextual


IDIOMAS = ("es", "en")


def _pedir_explicacion_openai(
    cliente, *, palabra: str, oracion: str, glosa: str,
    categoria: str | None, banda: str, modelo: str, idioma: str = "es",
) -> dict:
    """Pide a OpenAI lo contextual/gramatical. Prohibe explicitamente
    inventar la definicion: debe usar la glosa que se le pasa, tal cual.

    `idioma` decide en que lengua se explica: 'es' para lectores que aun
    necesitan el andamiaje en su lengua materna, 'en' para quien ya lee
    comodo y prefiere no salir del ingles mientras lee.
    """
    RespuestaContextual = _modelo_respuesta_contextual()
    if idioma == "en":
        lengua = (
            "Answer in ENGLISH in every field. The reader is a Spanish "
            "speaker who reads English literature and prefers to stay in "
            "English while reading, so keep the explanations in plain, clear "
            "English suited to their level.\n\n"
        )
    else:
        lengua = (
            "Responde en espanol en todos los campos EXCEPTO "
            "'ejemplo_simplificado', que debe ser una frase en ingles (es "
            "material de lectura, no un andamiaje en la lengua materna).\n\n"
        )
    instrucciones = (
        "Eres el asistente lexico de LiteraLevel, una app para lectores "
        "hispanohablantes que leen literatura en ingles. Recibes una palabra "
        "o expresion, la oracion original en ingles donde aparece, y la "
        "definicion de diccionario YA elegida para ese sentido exacto.\n\n"
        "REGLA INQUEBRANTABLE: no inventes ni cambies la definicion de "
        "diccionario que se te da. Usala tal cual como base factual; tu "
        "trabajo es contextualizarla y explicarla, nunca redefinirla.\n\n"
        f"El lector tiene un nivel '{banda}' (escala LiteraLevel 0-2, "
        "básico/intermedio/avanzado). Adapta el vocabulario y la longitud de "
        "tus explicaciones a ese nivel: mas sencillas y breves para "
        "'básico', mas ricas y precisas para 'avanzado'.\n\n"
        + lengua +
        "Campos a devolver:\n"
        "- definicion_contextual: como funciona ESTA palabra en ESTA oracion "
        "concreta, apoyandote en la definicion de diccionario dada.\n"
        "- explicacion_gramatical: forma o funcion gramatical en esta "
        "oracion (tiempo verbal, si es phrasal verb, si el sustantivo es "
        "contable, etc.).\n"
        "- explicacion_adaptada: la definicion de diccionario reformulada "
        "con palabras acordes al nivel del lector.\n"
        "- ejemplo_simplificado: una frase nueva en ingles, breve y sencilla, "
        "que use la palabra con el mismo sentido que en la oracion original."
    )
    entrada = (
        f"Palabra o expresion: {palabra}\n"
        f"Categoria gramatical detectada: {categoria or 'no determinada'}\n"
        f"Oracion original: {oracion}\n"
        f"Definicion de diccionario (usar tal cual, no inventar otra): {glosa}"
    )
    respuesta = cliente.responses.parse(
        model=modelo, instructions=instrucciones, input=entrada,
        text_format=RespuestaContextual,
    )
    return respuesta.output_parsed.model_dump()


def _generar_audio_tts(cliente, palabra: str, destino_dir: Path) -> str:
    """Genera audio de respaldo con tts-1 cuando la BD no trae ninguno.
    Devuelve la ruta del mp3 (se cachea tambien como archivo, ademas de la
    entrada en CacheLexico que evita repetir la llamada)."""
    destino_dir.mkdir(parents=True, exist_ok=True)
    nombre = hashlib.sha256(palabra.encode("utf-8")).hexdigest() + ".mp3"
    ruta = destino_dir / nombre
    if not ruta.exists():
        respuesta = cliente.audio.speech.create(model=MODELO_TTS, voice=VOZ_TTS, input=palabra)
        respuesta.write_to_file(str(ruta))
    return str(ruta)


# --- Punto de entrada -------------------------------------------------
class ConsultorLexico:
    """Carga diccionario y cache una sola vez; `consultar()` resuelve una
    palabra dentro de una oracion, para un lector de un nivel dado.

    Uso:
        consultor = ConsultorLexico()
        r = consultor.consultar("brook", "A small brook ran through the valley.", nivel=0.9)
    """

    def __init__(
        self,
        ruta_diccionario: str | os.PathLike = RUTA_DICCIONARIO,
        ruta_cache: str | os.PathLike = RUTA_CACHE,
        modelo_openai: str = MODELO_OPENAI_POR_DEFECTO,
    ):
        self.diccionario = Diccionario(ruta_diccionario)
        self.cache = CacheLexico(ruta_cache)
        self.modelo_openai = modelo_openai
        self._cliente_openai = None
        self._sin_clave = False   # evita reintentar obtener() en cada llamada

    def _cliente(self):
        """Cliente OpenAI perezoso; None si falta la clave (degradacion)."""
        if self._cliente_openai is not None:
            return self._cliente_openai
        if self._sin_clave:
            return None
        clave = obtener("OPENAI_API_KEY")
        if not clave:
            self._sin_clave = True
            return None
        from openai import OpenAI
        self._cliente_openai = OpenAI(api_key=clave)
        return self._cliente_openai

    def consultar(self, palabra_superficie: str, oracion: str, nivel: float,
                  idioma: str = "es") -> ResultadoLexico:
        """Resuelve `palabra_superficie` dentro de `oracion` para un lector
        de nivel `nivel` (escala publica 0..2). Nunca lanza excepcion por
        falta de red o de OPENAI_API_KEY: lo que falte queda en `avisos`.

        `idioma` ('es' o 'en') es la lengua de las explicaciones. El
        diccionario, la IPA y el audio no dependen de el: solo cambia lo que
        aporta OpenAI. Quien ya lee comodo suele preferir 'en' para no salir
        del ingles mientras lee.
        """
        idioma = idioma if idioma in IDIOMAS else "es"
        avisos: list[str] = []
        banda = public_band(nivel)

        lema_buscado, lema_simple, categoria, pos_spacy = _resolver_lema_y_categoria(
            oracion, palabra_superficie)

        entradas = self.diccionario.buscar(lema_buscado)
        if not entradas and lema_buscado != lema_simple:
            entradas = self.diccionario.buscar(lema_simple)
            lema_buscado = lema_simple
        if not entradas:
            avisos.append(f"'{lema_buscado}' no esta en el diccionario Kaikki")

        candidatas = entradas
        if categoria:
            filtradas = [e for e in entradas if e.pos == categoria]
            candidatas = filtradas or entradas

        pares = [(e, s) for e in candidatas for s in e.sentidos]
        sentido, similitud, avisos_sentido = _elegir_sentido(oracion, pares)
        avisos.extend(avisos_sentido)
        if entradas and sentido is None:
            avisos.append("la entrada no trae sentidos con glosa utilizable")

        ipa_uk, ipa_us, audio_uk, audio_us = _mejor_fonetica(entradas, categoria)
        audio_generado = False
        if not audio_uk and not audio_us:
            avisos.append("sin audio en el diccionario")
            cliente = self._cliente()
            if cliente is None:
                avisos.append("sin OPENAI_API_KEY: no se genero audio de respaldo")
            else:
                ruta_cacheada = self.cache.obtener_audio("audio", lema_buscado)
                try:
                    if ruta_cacheada:
                        ruta = ruta_cacheada
                    else:
                        ruta = _generar_audio_tts(cliente, lema_buscado, RUTA_AUDIO_GENERADO)
                        self.cache.guardar_audio(ruta, "audio", lema_buscado)
                    audio_uk = audio_us = ruta
                    audio_generado = True
                except Exception as e:
                    avisos.append(f"no se pudo generar audio: {type(e).__name__}")

        definicion_contextual = explicacion_gramatical = None
        explicacion_adaptada = ejemplo_simplificado = None
        desde_cache = False
        if sentido is not None:
            cliente = self._cliente()
            if cliente is None:
                avisos.append("sin OPENAI_API_KEY: no hay explicacion contextual")
            else:
                # El idioma va en la clave: si no, la version en espanol y la
                # inglesa se pisarian en la cache y saldria la que llego antes.
                partes_clave = (
                    "contextual", lema_buscado, categoria or "", sentido.glosa,
                    oracion, banda, self.modelo_openai, idioma,
                )
                extra = self.cache.obtener_respuesta(*partes_clave)
                if extra is not None:
                    desde_cache = True
                else:
                    try:
                        extra = _pedir_explicacion_openai(
                            cliente, palabra=palabra_superficie, oracion=oracion,
                            glosa=sentido.glosa, categoria=categoria, banda=banda,
                            modelo=self.modelo_openai, idioma=idioma,
                        )
                        self.cache.guardar_respuesta(extra, self.modelo_openai, *partes_clave)
                    except Exception as e:
                        avisos.append(f"OpenAI no disponible: {type(e).__name__}: {e}")
                        extra = None
                if extra:
                    definicion_contextual = extra["definicion_contextual"]
                    explicacion_gramatical = extra["explicacion_gramatical"]
                    explicacion_adaptada = extra["explicacion_adaptada"]
                    ejemplo_simplificado = extra["ejemplo_simplificado"]
        elif entradas:
            avisos.append("sin sentido elegido: no se pidio explicacion contextual")

        return ResultadoLexico(
            palabra_superficie=palabra_superficie, oracion=oracion,
            lema=lema_simple, lema_buscado=lema_buscado,
            pos_spacy=pos_spacy, categoria=categoria,
            sentido=sentido.glosa if sentido else None,
            etiquetas_sentido=sentido.etiquetas if sentido else [],
            similitud=round(similitud, 4) if similitud is not None else None,
            n_sentidos_candidatos=len(pares),
            ipa_uk=ipa_uk, ipa_us=ipa_us, audio_uk=audio_uk, audio_us=audio_us,
            audio_generado=audio_generado,
            definicion_contextual=definicion_contextual,
            explicacion_gramatical=explicacion_gramatical,
            explicacion_adaptada=explicacion_adaptada,
            ejemplo_simplificado=ejemplo_simplificado,
            banda_lector=banda,
            frecuencia_zipf=_frecuencia_zipf(lema_simple),
            desde_cache=desde_cache, avisos=avisos,
        )

    def cerrar(self) -> None:
        self.diccionario.cerrar()
        self.cache.cerrar()


if __name__ == "__main__":
    import sys

    consultor = ConsultorLexico()
    palabra = sys.argv[1] if len(sys.argv) > 1 else "brook"
    oracion = sys.argv[2] if len(sys.argv) > 2 else "A small brook ran through the valley."
    nivel = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    r = consultor.consultar(palabra, oracion, nivel)
    for campo, valor in r.__dict__.items():
        print(f"{campo:<24} {valor}")
    consultor.cerrar()
