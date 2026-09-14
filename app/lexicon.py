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
     por similitud coseno con SentenceTransformer("all-MiniLM-L6-v2").
     En verbos se compara categoria + etiquetas + glosa; en las demas
     categorias, la glosa. Un margen pequeno entre acepciones distintas
     se comunica en avisos. La afinidad publica sigue siendo el coseno
     oracion/glosa original, para conservar el umbral usado por la UI.
  4. OpenAI (Structured Outputs + Pydantic) SOLO aporta lo contextual y
     gramatical: nunca redefine la palabra, se le pasa la glosa elegida y se
     le prohibe explicitamente inventar otra.
  5. Se devuelven tambien IPA UK/US y audio UK/US de la base. Si la base no
     trae audio para esa palabra, se genera con `tts-1` (OpenAI) y se guarda
     en disco, marcando `audio_generado=True`.
  6. Cache en disco obligatoria en SQLite (~/.literalevel/lexicon.db): antes
     de cualquier llamada a OpenAI (texto o audio) se consulta la cache.
     `ResultadoLexico.llamadas_de_pago` cuenta las que SALIERON Y VOLVIERON
     con algo, no las que se pensaban hacer: es lo que `ui` mira para decidir
     si devuelve el uso del cupo, y un timeout o un 401 no cuestan un
     centimo. El audio tiene ademas una segunda cache, la de ARCHIVO
     (`_generar_audio_tts` devuelve `(ruta, se_pago)`): el mp3 puede estar ya
     en disco aunque esta cache no lo sepa, y entonces tampoco se paga.
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
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import config
from config import obtener
from scoring import public_band

# --- Rutas y constantes -------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
# Configurable por entorno: al desplegar, el .db de 233 MB se monta como
# volumen de solo lectura fuera del repositorio.
RUTA_DICCIONARIO = Path(os.environ.get("LITERALEVEL_DICCIONARIO",
                                       RAIZ / "kaikki_diccionario.db"))
# Bajo la raiz configurable de `config`: en un Space el disco del contenedor
# es efimero, y estas dos son las caches que EVITAN VOLVER A PAGAR. Perder
# `lexicon.db` significa pagar otra vez la explicacion de cada palabra ya
# consultada, y perder el audio significa otro tts-1 por palabra.
RUTA_CACHE = config.dir_datos() / "lexicon.db"
RUTA_AUDIO_GENERADO = config.dir_datos() / "audio"

MODELO_EMBEDDINGS = "all-MiniLM-L6-v2"
MODELO_OPENAI_POR_DEFECTO = "gpt-5"

# Esfuerzo de razonamiento de la explicacion contextual. Medido sobre tres
# palabras reales (fetters, brook, peeped), llamadas de verdad:
#
#   por defecto (medio)  67,7 s por consulta   2048 tokens de razonamiento
#   low                  14,9 s               256-576
#   minimal               7,4 s                   0
#
# Se elige "low": es 4,5 veces mas rapido y la gramatica sigue siendo
# correcta. **"minimal" no vale**, aunque sea el doble de rapido: con el,
# "had peeped" se explico como "pasado simple" cuando es pasado perfecto.
# El analisis gramatical es justo lo que se evalua, y equivocarlo por siete
# segundos es mal negocio. Los cuatro campos son cortos y la definicion ya
# viene dada: no hace falta razonamiento medio para redactarlos.
ESFUERZO_RAZONAMIENTO = "low"
MODELO_TTS = "tts-1"
VOZ_TTS = "alloy"
# Cambiar esta version invalida tanto la fila SQLite como el nombre del mp3.
# Los audios anteriores se generaban con el lema simple ("pick" en vez de
# "pick on") y tts-1 recortaba a veces el ultimo fonema de entradas muy
# breves. No se pueden distinguir con fiabilidad de un mp3 corto correcto,
# asi que todos los anteriores se consideran obsoletos una sola vez.
VERSION_AUDIO_TTS = "v2-superficie-pausa-atomico"

# Heuristica conservadora, no una probabilidad calibrada de acierto.
# Se aplica al ranking interno, no a ResultadoLexico.similitud.
_MARGEN_SENTIDO_DUDOSO = 0.05

# Etiquetas de Kaikki que apartan una acepcion si hay otra sin ellas (ver
# `_elegir_sentido`).
_ETIQUETAS_MARGINALES = {"obsolete", "archaic", "dated", "rare", "historical",
                         "nonstandard", "obsolete-form"}
# Registro que no se ofrece a OpenAI como acepcion alternativa si la elegida no
# lo tiene (ver `consultar`).
_ETIQUETAS_REGISTRO = {"slang", "vulgar", "derogatory", "offensive"}

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
    desde_cache: bool              # la EXPLICACION vino de la cache
    avisos: list[str]
    # Cuantas peticiones de pago salieron de verdad a OpenAI en esta consulta:
    # la explicacion y el audio se piden por separado y con claves de cache
    # distintas, asi que `desde_cache` no valia para saber si se gasto o no.
    # `ui` descuenta el cupo antes de consultar y lo devuelve si esto es 0.
    llamadas_de_pago: int = 0
    # Traduccion al espanol de la palabra EN ESA ORACION (OpenAI).
    traduccion: str | None = None
    # Definicion escrita por OpenAI cuando el diccionario no trae la palabra o
    # no trae ninguna acepcion utilizable. `generado_por_ia` lo marca para que
    # la interfaz lo diga: no es una definicion de diccionario.
    definicion_ia: str | None = None
    generado_por_ia: bool = False
    # True si OpenAI cambio la acepcion por OTRA DEL DICCIONARIO que encaja
    # mejor con la oracion (solo cuando la eleccion por embeddings era dudosa).
    acepcion_elegida_por_ia: bool = False
    # True si ipa_us o ipa_uk los escribio OpenAI (el diccionario no los traia).
    ipa_generada_por_ia: bool = False
    # Compuesto que el diccionario no trae entero («war-chant»). La entrada, la
    # acepcion y la categoria son de `parte_del_diccionario` («war»), no del todo;
    # `ipa_us`/`ipa_uk` y el audio SI son del compuesto entero: la IPA la escribe
    # OpenAI (marcada con `ipa_generada_por_ia`) y el audio, tts-1. Miguel (13 sep
    # 2026): la ficha salia como «war» con /wɔɹ/, «lo que hacen los diccionarios
    # tradicionales, y no lo quiero».
    compuesto: str | None = None
    parte_del_diccionario: str | None = None
    # La acepcion principal de cada entrada (etimologia) de Kaikki en la
    # categoria, cuando la eleccion es dudosa y NO hay explicacion de OpenAI
    # que la corrija. «bank» en «sitting by her sister on the bank» (Alicia)
    # elegia la hucha o el tribunal por 0,002, y la orilla quedaba la 12.ª de
    # 28: ningun ranking local medido la subia sin romper otras palabras (f4,
    # informe final, captura 21). En vez de una acepcion equivocada, las
    # principales. Vacia si la eleccion no es dudosa, si hubo explicacion o si
    # queda menos de dos. Orden: el del diccionario.
    acepciones_principales: list[str] = field(default_factory=list)

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


def _ruta_local(nombre: str) -> str:
    """La carpeta ya descargada del modelo, o su nombre si no esta.

    `SentenceTransformer("nombre/modelo")` resuelve ese nombre contra el Hub
    en CADA carga, y eso cuesta segundos aunque el modelo lleve meses en
    disco. Pasarle la ruta local se los ahorra: medido, 2,9 s -> 0,22 s en
    MiniLM-L6 y 5,8 s -> 2,7 s en el multilingue del catalogo.

    Si no esta cacheado -maquina nueva, primer arranque de un despliegue- se
    devuelve el nombre y se descarga como siempre. Nunca falla por esto.
    """
    completo = nombre if "/" in nombre else f"sentence-transformers/{nombre}"
    try:
        from huggingface_hub import snapshot_download
        return snapshot_download(completo, local_files_only=True)
    except Exception:
        return nombre


def _cargar_embebedor():
    global _embebedor
    if _embebedor is None:
        from sentence_transformers import SentenceTransformer
        _embebedor = SentenceTransformer(_ruta_local(MODELO_EMBEDDINGS))
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


def _sin_marginales(candidatos):
    """Los candidatos sin las acepciones marginales (obsolete, archaic...), o
    todos si no queda ninguno. Una sola regla para elegir la acepcion Y para
    las alternativas que ve OpenAI: antes las alternativas salian de la lista
    sin filtrar y la acepcion descartada volvia por la puerta de atras
    (Codex, auditoria de 5033e69: «awful» mandaba 4 marginales de 7)."""
    normales = [(e, s) for e, s in candidatos
                if not {t.lower() for t in s.etiquetas} & _ETIQUETAS_MARGINALES]
    return normales or candidatos


def _mas_afines(oracion: str, glosas: list[str], n: int = 8,
                obligada: str | None = None) -> list[str]:
    """Las `n` glosas mas cercanas a la oracion, con `obligada` siempre dentro.

    Antes eran las `n` primeras del volcado: «set» tiene 49 acepciones
    verbales y «To arrange with dishes and cutlery, to set the table» es la
    novena, asi que con la oracion «She set the table» nunca llegaba a OpenAI
    (Codex). Sin modelo de embeddings, se degrada al orden del volcado.
    """
    unicas = list(dict.fromkeys(g for g in glosas if g))
    if len(unicas) > n:
        try:
            modelo = _cargar_embebedor()
            vectores = modelo.encode([oracion or "", *unicas], normalize_embeddings=True)
            afinidad = vectores[1:] @ vectores[0]
            unicas = [unicas[i] for i in np.argsort(-afinidad, kind="stable")]
        except Exception:
            pass
    elegidas = unicas[:n]
    if obligada and obligada not in elegidas:
        elegidas = [obligada] + elegidas[:max(0, n - 1)]
    return elegidas


def _elegir_sentido(
    oracion: str, candidatos: list[tuple[EntradaDiccionario, Sentido]],
) -> tuple[Sentido | None, float | None, list[str]]:
    """Elige una acepcion y senala cuando la evidencia no la separa bien.

    Las glosas verbales se enriquecen con categoria y etiquetas de Kaikki:
    aportan transitividad y registro a definiciones cortas. No se anade el
    lema (comun a todos los candidatos), ni se inventan ejemplos: el volcado
    local no los conserva. En otras categorias se mantiene la glosa sola;
    extender el enriquecimiento a adjetivos empeoraba casos como "free".

    El ranking enriquecido es interno. La similitud devuelta conserva el
    coseno entre la oracion y la glosa ORIGINAL de la acepcion elegida.
    Al medir el margen se ignoran glosas repetidas, aunque procedan de
    categorias distintas (p.ej. "notwithstanding" como prep/postp).

    Devuelve (sentido_elegido, similitud, avisos). Si solo hay un candidato
    no hace falta el modelo de embeddings. Si el modelo de embeddings no se
    puede cargar (p.ej. sin red la primera vez), se degrada eligiendo el
    primer candidato y lo dice en avisos, sin lanzar excepcion.
    """
    if not candidatos:
        return None, None, []
    # Las acepciones marcadas como obsoletas, arcaicas o raras no compiten si
    # hay otras. Con «mostly» ganaba «To the greatest extent; most» (obsolete)
    # frente a «for the most part»: Miguel lo vio en la app el 13 sep 2026. Si
    # TODAS son marginales, se queda con ellas.
    candidatos = _sin_marginales(candidatos)
    if len(candidatos) == 1:
        return candidatos[0][1], None, []
    try:
        modelo = _cargar_embebedor()
        glosas = [s.glosa for _, s in candidatos]
        textos = []
        for _, s in candidatos:
            if s.pos == "verb":
                etiquetas = f" ({', '.join(s.etiquetas)})" if s.etiquetas else ""
                textos.append(f"{s.pos}{etiquetas}: {s.glosa}")
            else:
                textos.append(s.glosa)
        # Un solo lote; reutilizar textos identicos evita codificar dos veces
        # glosas no enriquecidas o duplicadas dentro del diccionario.
        unicos = list(dict.fromkeys([oracion, *textos, *glosas]))
        vectores = modelo.encode(unicos, normalize_embeddings=True)
        por_texto = dict(zip(unicos, vectores))
        v_contexto = por_texto[oracion]
        similitudes = np.array([por_texto[t] @ v_contexto for t in textos])
        idx = int(np.argmax(similitudes))
        elegida = candidatos[idx][1]
        glosa_elegida = " ".join(elegida.glosa.casefold().split())
        rivales = [i for i, g in enumerate(glosas)
                   if " ".join(g.casefold().split()) != glosa_elegida]
        avisos = []
        if rivales:
            segundo = max(rivales, key=lambda i: similitudes[i])
            margen = float(similitudes[idx] - similitudes[segundo])
            if margen < _MARGEN_SENTIDO_DUDOSO:
                avisos.append(
                    f"acepcion provisional: margen bajo ({margen:.3f}) "
                    f"frente a otra acepcion: {glosas[segundo]}"
                )
        similitud = float(por_texto[elegida.glosa] @ v_contexto)
        return elegida, similitud, avisos
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


# --- OpenAI -------------------------------------------------------------------
# REGLA (cambiada por Miguel el 13 sep 2026): OpenAI no redefine una palabra que
# el diccionario trae; la contextualiza y, si la acepcion elegida era dudosa,
# puede escoger OTRA acepcion DEL DICCIONARIO. Solo cuando el diccionario no
# trae la palabra -o ninguna acepcion utilizable- la define OpenAI, y el
# resultado va marcado como generado por IA. «Mostly» no le dio al lector ni
# traduccion ni audio, y era justo el caso en que queria toda la ayuda.
def _modelo_respuesta_contextual(compuesto: bool = False):
    """Construye el modelo Pydantic de Structured Outputs de forma perezosa,
    para no exigir `pydantic` a quien solo use diccionario + IPA.

    Con `compuesto`, pide ademas la IPA del compuesto ENTERO: el diccionario
    solo trae una de sus partes («war» de «war-chant») y su IPA no es la de
    la palabra que se esta leyendo."""
    from pydantic import BaseModel

    class RespuestaContextual(BaseModel):
        traduccion: str
        acepcion_usada: str
        definicion_contextual: str
        explicacion_gramatical: str
        explicacion_adaptada: str
        ejemplo_simplificado: str

    if not compuesto:
        return RespuestaContextual

    class RespuestaContextualCompuesto(RespuestaContextual):
        ipa_us: str
        ipa_uk: str

    return RespuestaContextualCompuesto


def _modelo_respuesta_ia():
    from pydantic import BaseModel

    class RespuestaSinDiccionario(BaseModel):
        definicion_ia: str
        traduccion: str
        ipa_us: str
        ipa_uk: str
        definicion_contextual: str
        explicacion_gramatical: str
        explicacion_adaptada: str
        ejemplo_simplificado: str

    return RespuestaSinDiccionario


def _es_compuesto(texto: str) -> bool:
    """«war-chant», «well-known»: dos o mas piezas de letras unidas por guion."""
    piezas = str(texto or "").split("-")
    return len(piezas) >= 2 and all(p and p.replace("'", "").isalpha() for p in piezas)


def _ipa_de_modelo(texto) -> str | None:
    """La IPA que devuelve OpenAI, entre barras, o None si viene vacia o
    desmedida."""
    texto = str(texto or "").strip()
    if not texto or len(texto) > 60:
        return None
    return texto if texto.startswith(("/", "[")) else f"/{texto.strip('/')}/"


def _lengua(idioma: str) -> str:
    if idioma == "en":
        return ("Answer in ENGLISH in every field except 'traduccion', which is the "
                "Spanish translation. The reader is a Spanish speaker who reads English "
                "literature and prefers to stay in English while reading, so keep the "
                "explanations in plain, clear English suited to their level.\n\n")
    return ("Responde en espanol en todos los campos EXCEPTO "
            "'ejemplo_simplificado', que debe ser una frase en ingles (es "
            "material de lectura, no un andamiaje en la lengua materna).\n\n")


def _pedir_definicion_ia(
    cliente, *, palabra: str, oracion: str, categoria: str | None, banda: str,
    modelo: str, idioma: str = "es",
) -> dict:
    """La palabra NO esta en el diccionario local (o no trae ninguna acepcion
    utilizable): OpenAI la define en su oracion. Lo que devuelve se marca como
    generado por IA en `ResultadoLexico`."""
    Respuesta = _modelo_respuesta_ia()
    instrucciones = (
        "Eres el asistente lexico de LiteraLevel, una app para lectores "
        "hispanohablantes que leen literatura en ingles. La palabra que recibes NO "
        "esta en el diccionario local de la app, asi que la defines tu. Puede ser "
        "rara, arcaica, dialectal, literaria, un nombre propio, una forma flexionada "
        "poco comun o una errata del texto: si es alguna de esas cosas, dilo al "
        "principio de 'definicion_ia'. Si no tienes certeza del significado, dilo "
        "claramente en vez de inventar.\n\n"
        f"El lector tiene un nivel '{banda}' (escala LiteraLevel 0-2, "
        "básico/intermedio/avanzado). Adapta el vocabulario y la longitud.\n\n"
        + _lengua(idioma) +
        "Campos a devolver:\n"
        "- definicion_ia: definicion breve, de estilo diccionario, del sentido que "
        "tiene en esta oracion.\n"
        "- traduccion: la traduccion al espanol mas natural en esta oracion (de una "
        "a cuatro palabras).\n"
        "- ipa_us: transcripcion fonemica en AFI (IPA) del ingles americano (General "
        "American), entre barras, con la marca de acento primario ˈ y, si la hay, la "
        "secundaria ˌ delante de la silaba: por ejemplo /ˈmoʊstli/. Usa ɹ para la r.\n"
        "- ipa_uk: lo mismo en britanico (RP), por ejemplo /ˈməʊstli/. Si la palabra no "
        "es inglesa o no puedes transcribirla con seguridad, deja los dos vacios.\n"
        "- definicion_contextual: como funciona en esta oracion concreta.\n"
        "- explicacion_gramatical: forma y funcion gramatical en esta oracion.\n"
        "- explicacion_adaptada: la definicion reformulada para el nivel del lector.\n"
        "- ejemplo_simplificado: una frase nueva en ingles, breve y sencilla, con el "
        "mismo sentido."
    )
    entrada = (
        f"Palabra o expresion: {palabra}\n"
        f"Categoria gramatical detectada: {categoria or 'no determinada'}\n"
        f"Oracion original: {oracion or '(sin oracion)'}"
    )
    respuesta = cliente.responses.parse(
        model=modelo, instructions=instrucciones, input=entrada,
        text_format=Respuesta, reasoning={"effort": ESFUERZO_RAZONAMIENTO},
    )
    return respuesta.output_parsed.model_dump()


IDIOMAS = ("es", "en")


def _pedir_explicacion_openai(
    cliente, *, palabra: str, oracion: str, glosa: str,
    categoria: str | None, banda: str, modelo: str, idioma: str = "es",
    alternativas: list[str] | None = None,
    compuesto_de: str | None = None,
) -> dict:
    """Pide a OpenAI lo contextual/gramatical. Prohibe explicitamente
    inventar la definicion: debe usar la glosa que se le pasa, tal cual, o,
    si la eleccion era dudosa, OTRA de las `alternativas` del diccionario.

    `idioma` decide en que lengua se explica: 'es' para lectores que aun
    necesitan el andamiaje en su lengua materna, 'en' para quien ya lee
    comodo y prefiere no salir del ingles mientras lee.

    `compuesto_de`: `palabra` es un compuesto que el diccionario no trae entero
    («war-chant») y la glosa es solo de esa parte («war»). Se explica el
    compuesto sin presentar la glosa como suya, y se pide su IPA entera.
    """
    RespuestaContextual = _modelo_respuesta_contextual(compuesto=bool(compuesto_de))
    lengua = _lengua(idioma)
    regla_compuesto = (
        f"La palabra del texto es el compuesto «{palabra}», que el diccionario no trae "
        f"entero: la definicion de diccionario que recibes es SOLO de su parte "
        f"«{compuesto_de}». No la presentes como la definicion del compuesto. En "
        "'definicion_contextual' y 'explicacion_adaptada' explica que significa el "
        "compuesto entero en esta oracion, apoyandote en esa parte; la 'traduccion' es "
        "la del compuesto entero.\n\n") if compuesto_de else ""
    campos_compuesto = (
        "\n- ipa_us: transcripcion fonemica en AFI (IPA) del compuesto ENTERO en ingles "
        "americano (General American), entre barras, con la marca de acento primario ˈ "
        "y la secundaria ˌ delante de la silaba: por ejemplo /ˈwɔɹˌtʃænt/. Usa ɹ para la r.\n"
        "- ipa_uk: lo mismo en britanico (RP). Si no puedes transcribirlo con seguridad, "
        "deja los dos vacios.") if compuesto_de else ""
    otras = [a for a in (alternativas or []) if a and a != glosa]
    regla_alternativas = (
        "La eleccion de la acepcion fue DUDOSA. Si la definicion dada no encaja con "
        "la oracion y alguna de las OTRAS ACEPCIONES DEL DICCIONARIO de la lista si, "
        "usa esa como base y copia su texto EXACTO en 'acepcion_usada'. Si la dada "
        "encaja, deja 'acepcion_usada' vacio. Nunca escribas en 'acepcion_usada' algo "
        "que no este en la lista.\n"
        # «waistcoat» en Alice: OpenAI recibio las dos acepciones y se quedo con
        # «An ornamental garment worn under a doublet» (f4, informe final,
        # captura 10). Kaikki no la marca como historica, asi que el filtro de
        # marginales no puede apartarla.
        "Si la definicion dada describe una prenda, un oficio, una costumbre o un "
        "objeto de otra epoca (por ejemplo, algo que se llevaba bajo un jubon) y la "
        "oracion no esta situada en esa epoca, y en la lista hay una acepcion de uso "
        "actual que encaja, elige la de uso actual.\n\n") if otras else (
        "Deja 'acepcion_usada' vacio.\n\n")
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
        + regla_compuesto + regla_alternativas + lengua +
        "Campos a devolver:\n"
        "- traduccion: la traduccion al espanol mas natural de la palabra en esta "
        "oracion (de una a cuatro palabras), coherente con la definicion.\n"
        "- acepcion_usada: ver arriba.\n"
        "- definicion_contextual: como funciona ESTA palabra en ESTA oracion "
        "concreta, apoyandote en la definicion de diccionario dada.\n"
        "- explicacion_gramatical: forma o funcion gramatical en esta "
        "oracion (tiempo verbal, si es phrasal verb, si el sustantivo es "
        "contable, etc.).\n"
        "- explicacion_adaptada: la definicion de diccionario reformulada "
        "con palabras acordes al nivel del lector.\n"
        "- ejemplo_simplificado: una frase nueva en ingles, breve y sencilla, "
        "que use la palabra con el mismo sentido que en la oracion original."
        + campos_compuesto
    )
    entrada = (
        f"Palabra o expresion: {palabra}\n"
        + (f"Parte del compuesto que trae el diccionario: {compuesto_de}\n" if compuesto_de else "")
        + f"Categoria gramatical detectada: {categoria or 'no determinada'}\n"
        f"Oracion original: {oracion}\n"
        f"Definicion de diccionario (usar tal cual, no inventar otra): {glosa}"
        + ("\nOtras acepciones del diccionario:\n" + "\n".join(f"- {a}" for a in otras)
           if otras else "")
    )
    respuesta = cliente.responses.parse(
        model=modelo, instructions=instrucciones, input=entrada,
        text_format=RespuestaContextual,
        reasoning={"effort": ESFUERZO_RAZONAMIENTO},
    )
    return respuesta.output_parsed.model_dump()


def _texto_para_tts(texto: str) -> str:
    """Conserva la expresion entera y da a tts-1 un final que pueda cerrar.

    En entradas aisladas tts-1 puede terminar justo tras el ultimo fonema.
    Una coma final fuerza una pausa breve sin anadir otra palabra al audio.
    """
    limpio = texto.strip()
    if limpio and limpio[-1] not in ".,;:!?":
        limpio += ","
    return limpio


def _escribir_audio_atomico(respuesta, ruta: Path) -> None:
    """Publica el mp3 solo despues de que `write_to_file` haya terminado."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    descriptor, nombre_temporal = tempfile.mkstemp(
        dir=str(ruta.parent), prefix=f".{ruta.name}.", suffix=".tmp")
    os.close(descriptor)
    temporal = Path(nombre_temporal)
    try:
        respuesta.write_to_file(str(temporal))
        if temporal.stat().st_size == 0:
            raise OSError("OpenAI devolvio un audio vacio")
        # write_to_file ya cerro su descriptor. Este fsync adicional garantiza
        # que tampoco queda contenido pendiente antes del os.replace atomico.
        with temporal.open("ab") as archivo:
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    finally:
        temporal.unlink(missing_ok=True)


def _generar_audio_tts(cliente, palabra: str, destino_dir: Path) -> tuple[str, bool]:
    """Genera audio de respaldo con tts-1 cuando la BD no trae ninguno.

    Devuelve `(ruta_del_mp3, se_pago)`. El mp3 se cachea tambien como ARCHIVO,
    aparte de la entrada en `CacheLexico`, asi que puede estar ya en disco
    aunque esta cache no lo sepa -otro lector lo pidio, o la base se borro-. En
    ese caso no hay llamada y no hay nada que cobrar: devolver solo la ruta
    hacia creer a quien llama que se habia pagado un tts-1.
    """
    texto_tts = _texto_para_tts(palabra)
    huella = "\x1f".join((VERSION_AUDIO_TTS, MODELO_TTS, VOZ_TTS, texto_tts))
    nombre = hashlib.sha256(huella.encode("utf-8")).hexdigest() + ".mp3"
    ruta = destino_dir / nombre
    if ruta.exists():
        return str(ruta), False
    respuesta = cliente.audio.speech.create(
        model=MODELO_TTS, voice=VOZ_TTS, input=texto_tts, response_format="mp3")
    _escribir_audio_atomico(respuesta, ruta)
    return str(ruta), True


# --- Punto de entrada -------------------------------------------------
class ConsultorLexico:
    """Carga diccionario y cache una sola vez; `consultar()` resuelve una
    palabra dentro de una oracion, para un lector de un nivel dado.

    Uso:
        consultor = ConsultorLexico()
        r = consultor.consultar("brook", "A small brook ran through the valley.", nivel=0.9)
    """

    # De la CLASE y no de la instancia: dos consultores sobre la misma cache
    # tambien se esperan, y quien construye con __new__ (las pruebas) los tiene.
    _CANDADOS = [threading.Lock() for _ in range(64)]

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
        # CON PLAZO, y no es un detalle. El SDK trae 600 s por defecto y dos
        # reintentos: una sola peticion atascada retiene su hilo casi media
        # hora, y con la cola de Gradio en un solo trabajador todo lo demas se
        # apila detras. Paso de verdad en el Space -una consulta con perfil lo
        # dejo sin servir HTTP mas de media hora, con la API de Hugging Face
        # diciendo RUNNING todo el rato-.
        #
        # 60 s es holgado: la explicacion contextual esta medida en 14,9 s con
        # `reasoning.effort="low"`. Un reintento, no dos. Peor caso 2 minutos
        # en vez de 30.
        self._cliente_openai = OpenAI(api_key=clave, timeout=60.0,
                                      max_retries=1)
        return self._cliente_openai

    def consultar(self, palabra_superficie: str, oracion: str, nivel: float,
                  idioma: str = "es", usar_openai: bool = True) -> ResultadoLexico:
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

        # Compuestos con guion («war-chant»): spaCy los parte y el lema sale de
        # una pieza («war»). Si el diccionario trae el compuesto entero, se usa
        # entero; si no, la entrada es de la pieza y la ficha lo tiene que decir:
        # la IPA y el audio de «war» no son los de «war-chant» (Miguel, 13 sep).
        compuesto = parte_del_diccionario = None
        superficie = palabra_superficie.strip().strip(".,;:!?¿¡\"'()[]«»…“”‘’").lower()
        if _es_compuesto(superficie) and lema_buscado != superficie:
            if self.diccionario.buscar(superficie):
                lema_buscado = lema_simple = superficie
            else:
                compuesto = superficie

        entradas = self.diccionario.buscar(lema_buscado)
        if not entradas and lema_buscado != lema_simple:
            entradas = self.diccionario.buscar(lema_simple)
            lema_buscado = lema_simple
        if not entradas:
            avisos.append(f"'{lema_buscado}' no esta en el diccionario Kaikki")
        elif compuesto:
            parte_del_diccionario = lema_buscado

        candidatas = entradas
        if categoria:
            filtradas = [e for e in entradas if e.pos == categoria]
            candidatas = filtradas or entradas

        pares = [(e, s) for e in candidatas for s in e.sentidos]
        sentido, similitud, avisos_sentido = _elegir_sentido(oracion, pares)
        avisos.extend(avisos_sentido)
        if entradas and sentido is None:
            avisos.append("la entrada no trae sentidos con glosa utilizable")
        # Si los embeddings no separaron bien dos acepciones, OpenAI recibe las
        # del diccionario y puede quedarse con otra de ELLAS (nunca inventarla).
        dudoso = any("acepcion provisional" in a for a in avisos_sentido)
        # Sin las de argot o vulgares, salvo que la elegida ya lo sea: en
        # «she had peeped into the book» OpenAI cambio «To look forth from
        # concealment» por «To take a look at; check out» (slang). Esto es una
        # app de literatura: el registro estandar va primero.
        registro_elegido = ({t.lower() for t in sentido.etiquetas} & _ETIQUETAS_REGISTRO
                            if sentido is not None else set())
        alternativas = (_mas_afines(
            oracion,
            [s.glosa for _, s in _sin_marginales(pares)
             if registro_elegido or not ({t.lower() for t in s.etiquetas} & _ETIQUETAS_REGISTRO)],
            n=8, obligada=sentido.glosa if sentido is not None else None,
        ) if dudoso else None)
        # Sin acepcion utilizable -la palabra no esta, o no trae glosas-, la
        # define OpenAI y se marca como generado por IA.
        modo_ia = sentido is None

        # Las dos llamadas de red -el audio de respaldo y la explicacion- se
        # lanzan A LA VEZ, no una detras de otra. Solo 7.003 de las 1.487.639
        # entradas del diccionario traen audio (un 0,5 %), asi que casi
        # cualquier palabra nueva necesita las dos, y en serie eso eran unos
        # tres segundos regalados. Las escrituras a SQLite se quedan en el
        # hilo principal: la cache es un fichero, no un servicio.
        ipa_uk, ipa_us, audio_uk, audio_us = _mejor_fonetica(entradas, categoria)
        if parte_del_diccionario:
            ipa_uk = ipa_us = audio_uk = audio_us = None
        audio_generado = False
        # `usar_openai=False` reutiliza el camino de "no hay clave", que ya
        # estaba escrito y probado: el diccionario, la IPA, la desambiguacion y
        # el audio de Wiktionary siguen funcionando, y lo que dependeria de la
        # API queda anotado en `avisos`. Sirve para que la aplicacion desplegada
        # en una direccion publica pueda ofrecer la consulta a todo el mundo sin
        # que un visitante gaste el saldo de otro. No hay una segunda rama que
        # mantener: es la misma.
        cliente = self._cliente() if usar_openai else None

        # Que falta y que ya estaba guardado.
        falta_audio = not audio_uk and not audio_us
        ruta_audio_cacheada = None
        # NORMALIZADO, y no la superficie tal cual. La clave del audio se hacia
        # con la palabra como la escribio el libro, asi que "Fetters", "FETTERS"
        # y "fetters." eran tres entradas distintas de la cache -tres audios
        # pagados- mientras la explicacion, que se guarda por LEMA, acertaba en
        # la primera. Y ahi `ui` veia `desde_cache=True` y devolvia el uso: cada
        # variante era un tts-1 gratis. tts-1 pronuncia igual las tres.
        texto_audio = (palabra_superficie.strip().strip(".,;:!?¿¡\"'()[]«»…").lower()
                       or lema_buscado)
        partes_cache_audio = (
            "audio", VERSION_AUDIO_TTS, MODELO_TTS, VOZ_TTS, texto_audio,
        )
        if falta_audio:
            avisos.append("sin audio en el diccionario")
            if cliente is None:
                avisos.append("sin OPENAI_API_KEY: no se genero audio de respaldo")
            else:
                ruta_audio_cacheada = self.cache.obtener_audio(*partes_cache_audio)

        definicion_contextual = explicacion_gramatical = None
        explicacion_adaptada = ejemplo_simplificado = None
        desde_cache = False
        partes_clave = None
        extra = None
        if sentido is not None:
            if cliente is None:
                avisos.append("sin OPENAI_API_KEY: no hay explicacion contextual")
            else:
                # El idioma va en la clave: si no, la version en espanol y la
                # inglesa se pisarian en la cache y saldria la que llego antes.
                # v2: la respuesta trae ademas `traduccion` y `acepcion_usada`.
                # Las de v1 no las tienen y se volverian a mostrar sin traduccion.
                partes_clave = (
                    "contextual-v2", lema_buscado, categoria or "", sentido.glosa,
                    oracion, banda, self.modelo_openai, idioma,
                    "alt" if alternativas else "",
                ) + (("compuesto",) if parte_del_diccionario else ())
                extra = self.cache.obtener_respuesta(*partes_clave)
                if extra is not None:
                    desde_cache = True
        elif cliente is None:
            avisos.append("sin OPENAI_API_KEY: no hay definicion por IA")
        else:
            # v2: la respuesta trae ademas la IPA generada.
            partes_clave = (
                "definicion-ia-v2", lema_buscado, categoria or "", oracion, banda,
                self.modelo_openai, idioma,
            )
            extra = self.cache.obtener_respuesta(*partes_clave)
            if extra is not None:
                desde_cache = True

        # Una sola consulta de pago por clave a la vez (Codex, auditoria de
        # 5033e69). La API ya serializaba con su _CANDADO_LEXICO, pero Gradio
        # atiende hasta 8 eventos a la vez: dos lectores con la misma palabra en
        # la misma frase pagaban dos veces. Candados por franjas segun el hash de
        # la clave, sin diccionario que crezca; dos claves distintas en la misma
        # franja solo se esperan. Dentro se RELEE la cache: el que espero se
        # encuentra lo que pago el primero y no vuelve a pagar.
        candado = None
        if (partes_clave is not None and extra is None) or (
                falta_audio and cliente is not None and not ruta_audio_cacheada):
            candado = self._CANDADOS[hash((partes_clave, texto_audio)) % len(self._CANDADOS)]
            candado.acquire()
            if partes_clave is not None and extra is None:
                extra = self.cache.obtener_respuesta(*partes_clave)
                desde_cache = extra is not None
            if falta_audio and cliente is not None and not ruta_audio_cacheada:
                ruta_audio_cacheada = self.cache.obtener_audio(*partes_cache_audio)
        try:
            pedir_audio = falta_audio and cliente is not None and not ruta_audio_cacheada
            pedir_explicacion = partes_clave is not None and extra is None
            ruta_audio_nueva = None
            audio_pagado = False
            if pedir_audio or pedir_explicacion:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=2) as grupo:
                    f_audio = grupo.submit(
                        _generar_audio_tts, cliente, texto_audio, RUTA_AUDIO_GENERADO
                    ) if pedir_audio else None
                    if not pedir_explicacion:
                        f_expl = None
                    elif modo_ia:
                        f_expl = grupo.submit(
                            _pedir_definicion_ia, cliente,
                            palabra=palabra_superficie, oracion=oracion,
                            categoria=categoria, banda=banda,
                            modelo=self.modelo_openai, idioma=idioma)
                    else:
                        # `alternativas` solo si las hay: un doble de la funcion
                        # sin ese parametro sigue valiendo en el caso normal.
                        extra_kw = {"alternativas": alternativas} if alternativas else {}
                        if parte_del_diccionario:
                            extra_kw["compuesto_de"] = parte_del_diccionario
                        f_expl = grupo.submit(
                            _pedir_explicacion_openai, cliente,
                            palabra=palabra_superficie, oracion=oracion,
                            glosa=sentido.glosa, categoria=categoria,
                            banda=banda, modelo=self.modelo_openai, idioma=idioma,
                            **extra_kw)

                    if f_audio is not None:
                        try:
                            ruta_audio_nueva, audio_pagado = f_audio.result()
                        except Exception as e:
                            avisos.append(f"no se pudo generar audio: {type(e).__name__}")
                    if f_expl is not None:
                        try:
                            extra = f_expl.result()
                        except Exception as e:
                            avisos.append(f"OpenAI no disponible: {type(e).__name__}: {e}")
                            extra = None

            # Lo que se ha pagado DE VERDAD, contado DESPUES de pedirlo. Antes se
            # contaba la intencion -"voy a pedir dos"- y `ui` cobraba el cupo
            # aunque la llamada muriera en un timeout o en un 401, que no cuestan
            # un centimo. `ficha.sinopsis` ya devolvia el uso cuando no habia red:
            # eran dos criterios distintos para lo mismo y gana el de `ficha`.
            #
            # Queda un caso que desde aqui no se distingue: que OpenAI cobre la
            # peticion y reviente al escribir el archivo. Eso cuenta como no
            # cobrada. Es el lado en el que conviene equivocarse: el cupo existe
            # para que nadie se coma la cuenta del mes, y un fallo del servidor no
            # es del visitante.
            llamadas_de_pago = (int(audio_pagado)
                                + int(pedir_explicacion and extra is not None))

            # Ya fuera de los hilos: guardar en la cache y componer el resultado.
            if ruta_audio_nueva:
                self.cache.guardar_audio(ruta_audio_nueva, *partes_cache_audio)
            ruta_audio = ruta_audio_nueva or ruta_audio_cacheada
            if ruta_audio:
                audio_uk = audio_us = ruta_audio
                audio_generado = True
            if extra and pedir_explicacion:
                self.cache.guardar_respuesta(extra, self.modelo_openai, *partes_clave)
        finally:
            if candado is not None:
                candado.release()
        traduccion = definicion_ia = None
        generado_por_ia = acepcion_elegida_por_ia = ipa_generada_por_ia = False
        if extra:
            definicion_contextual = extra.get("definicion_contextual")
            explicacion_gramatical = extra.get("explicacion_gramatical")
            explicacion_adaptada = extra.get("explicacion_adaptada")
            ejemplo_simplificado = extra.get("ejemplo_simplificado")
            traduccion = (extra.get("traduccion") or "").strip() or None
            if modo_ia:
                # Todo lo de esta respuesta lo escribio OpenAI: la marca va con
                # la respuesta, no con que `definicion_ia` traiga texto. Con una
                # definicion de solo espacios, la ficha decia «No hay entrada» y
                # enseñaba explicaciones de IA sin marcar (Codex). Si llega vacia
                # se usa la contextual, que tambien es suya.
                definicion_ia = ((extra.get("definicion_ia") or "").strip()
                                 or (extra.get("definicion_contextual") or "").strip() or None)
                generado_por_ia = True
                # La IPA de la IA solo rellena lo que el diccionario no trae, y
                # se marca. Miguel: «si ya lo esta generando OpenAI, que tambien
                # de la transcripcion en IPA con la correcta acentuacion».
                ia_us = _ipa_de_modelo(extra.get("ipa_us"))
                ia_uk = _ipa_de_modelo(extra.get("ipa_uk"))
                if not ipa_us and ia_us:
                    ipa_us, ipa_generada_por_ia = ia_us, True
                if not ipa_uk and ia_uk:
                    ipa_uk, ipa_generada_por_ia = ia_uk, True
            else:
                def _norm(t):
                    return " ".join(str(t or "").casefold().split())
                usada = _norm(extra.get("acepcion_usada"))
                # Solo se acepta una acepcion de la lista que se ofrecio: una
                # respuesta vieja de la cache no puede colar otra (p. ej. slang).
                permitidas = {_norm(a) for a in (alternativas or [])}
                if usada and usada in permitidas and usada != _norm(sentido.glosa):
                    otra = next((s for _, s in pares if _norm(s.glosa) == usada), None)
                    if otra is not None:
                        sentido, similitud, acepcion_elegida_por_ia = otra, None, True
                # OpenAI ya reviso la eleccion con las otras acepciones delante,
                # la conservara o la cambiara: el aviso de «acepcion dudosa» ya
                # no aplica. f4 lo vio en «house», con dudoso=false al lado.
                # Solo si la respuesta trae `acepcion_usada`, que es la prueba de
                # que contesto a las alternativas (una respuesta vieja, sin el
                # campo, no reviso nada). Sin OpenAI (etapa diccionario) se queda.
                if alternativas and "acepcion_usada" in extra:
                    avisos = [a for a in avisos if "acepcion provisional" not in a]

        acepciones_principales: list[str] = []
        if dudoso and not (extra and str(extra.get("definicion_contextual") or "").strip()):
            for e in candidatas:
                limpios = _sin_marginales([(e, s) for s in e.sentidos if s.glosa])
                glosa = limpios[0][1].glosa if limpios else None
                if glosa and glosa not in acepciones_principales:
                    acepciones_principales.append(glosa)
            if len(acepciones_principales) < 2:
                acepciones_principales = []

        if parte_del_diccionario and extra:
            ipa_us = _ipa_de_modelo(extra.get("ipa_us"))
            ipa_uk = _ipa_de_modelo(extra.get("ipa_uk"))
            ipa_generada_por_ia = bool(ipa_us or ipa_uk)

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
            llamadas_de_pago=llamadas_de_pago,
            traduccion=traduccion, definicion_ia=definicion_ia,
            generado_por_ia=generado_por_ia,
            acepcion_elegida_por_ia=acepcion_elegida_por_ia,
            ipa_generada_por_ia=ipa_generada_por_ia,
            compuesto=compuesto, parte_del_diccionario=parte_del_diccionario,
            acepciones_principales=acepciones_principales,
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
