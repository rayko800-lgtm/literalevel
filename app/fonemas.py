"""Fonemas del ingles: el inventario cerrado, su audio pregrabado y la IPA.

Sirve a la practica de pronunciacion. Cuando `voz.explicar_correccion` dice que
en «warn» falla la /w/, la interfaz pinta el simbolo, un reproductor con ese
sonido y la transcripcion de la palabra entera, para que el alumno se vaya
familiarizando con el AFI sin salir de la correccion.

REFERENCIA: GENERAL AMERICAN

El acento de referencia es el General American, y los simbolos son los de la
convencion de Wiktionary para ese acento. No es una eleccion estetica: la
transcripcion de la palabra que se pinta al lado sale del volcado de
Kaikki/Wiktionary (ver `ipa_de_palabra`), y ensenar /r/ en el fonema junto a
/woɹn/ en la palabra seria ensenar dos simbolos para el mismo sonido en la
misma linea. Por eso la r es `ɹ`, la vocal de «see» es `i` sin marca de
longitud y la de «bed» es `ɛ`.

Dos excepciones, y las dos a proposito: las africadas se escriben `tʃ` y `dʒ`
sin la ligadura (Wiktionary pone `t͡ʃ`), porque es como aparecen en casi todos
los diccionarios de aprendizaje y la ligadura se pierde en muchas fuentes.

Los diccionarios para estudiantes (Cambridge, Oxford) y el acento britanico
RP escriben algunos de estos sonidos de otra forma. Todas esas variantes se
aceptan en `normalizar` y llevan al mismo fonema:

    iː -> i     uː -> u     ɑː -> ɑ     ɔː -> ɔ     e -> ɛ     r -> ɹ
    ɜː, ɜːr, ɜr -> ɝ        ər -> ɚ     əʊ (RP) -> oʊ     t͡ʃ -> tʃ

Lo que NO tiene equivalente en General American se queda fuera y
`normalizar` devuelve `None`, en vez de mandar al alumno a un sonido que no
es: los diptongos centralizantes de RP (`ɪə`, `eə`, `ʊə`, que en GA son
vocal + ɹ), la `ɒ` de «hot» en RP (en GA es `ɑ`, pero forzar esa
equivalencia al normalizar escondería una diferencia real de acento: se deja
fuera tambien) y los alofonos como la vibrante simple `ɾ` de «butter» o la
oclusion glotal `ʔ`, que no son fonemas.

EL AUDIO

Cada fonema tiene un mp3 en `app/audio_fonemas/`, generado UNA vez con
`tools/generar_fonemas.py` y versionado en el repositorio: el sonido aislado
tres veces, una pausa y sus dos palabras de ejemplo. Esta en disco, asi que se
oye sin gastar credito y sin `OPENAI_API_KEY`: este modulo no importa el SDK
de OpenAI ni sale a la red. Como se pidio cada audio, y que oyo en el un
reconocedor de fonemas, esta en `tools/fonemas_generados.json`.
"""
from __future__ import annotations

import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path

DIR_AUDIO = Path(__file__).resolve().parent / "audio_fonemas"


@dataclass(frozen=True)
class Fonema:
    simbolo: str          # AFI, convencion de Wiktionary para General American
    nombre: str           # en espanol, para quien no sabe fonetica
    ejemplos: tuple[str, ...]
    tipo: str             # consonante | vocal | diptongo

    @property
    def archivo(self) -> str:
        """Nombre del mp3. Sale de los puntos de codigo del simbolo, no del
        simbolo: `ʃ.mp3` o `ɝ.mp3` son nombres validos en NTFS, pero no en
        todas las herramientas por las que pasa un despliegue, y `θ` y `ð` no
        se distinguen a simple vista en un listado."""
        return "_".join(f"{ord(c):04x}" for c in self.simbolo) + ".mp3"

    @property
    def ruta(self) -> Path:
        return DIR_AUDIO / self.archivo


def _f(simbolo, nombre, ejemplos, tipo):
    return Fonema(simbolo, nombre, tuple(ejemplos), tipo)


# El orden es el de las tablas de fonetica: primero consonantes por modo de
# articulacion, luego vocales, luego diptongos.
INVENTARIO: tuple[Fonema, ...] = (
    # --- Consonantes (24) ---
    _f("p", "p con un soplo de aire, como al apagar una vela", ["pen", "top"], "consonante"),
    _f("b", "b de «bota»", ["bed", "cab"], "consonante"),
    _f("t", "t con soplo de aire; la lengua toca detrás de los dientes, no en ellos", ["ten", "cat"], "consonante"),
    _f("d", "d de «dedo», con la lengua detrás de los dientes", ["dog", "bed"], "consonante"),
    _f("k", "c de «casa», con soplo de aire", ["cat", "back"], "consonante"),
    _f("ɡ", "g de «gato»", ["go", "bag"], "consonante"),
    _f("f", "f de «foco»", ["fish", "leaf"], "consonante"),
    _f("v", "no existe en español: dientes de arriba sobre el labio de abajo, con zumbido", ["van", "love"], "consonante"),
    _f("θ", "la z de «zapato» como la dicen en España: lengua entre los dientes, solo aire", ["think", "bath"], "consonante"),
    _f("ð", "parecida a la d suave de «cada»: lengua entre los dientes, con zumbido", ["this", "mother"], "consonante"),
    _f("s", "s de «sol»", ["see", "bus"], "consonante"),
    _f("z", "s con zumbido, como una abeja", ["zoo", "rose"], "consonante"),
    _f("ʃ", "el «shhh» de cuando pides silencio", ["she", "fish"], "consonante"),
    _f("ʒ", "la «y» de «yo» como la dicen en Argentina", ["measure", "vision"], "consonante"),
    _f("h", "una j muy suave, solo aire, como al empañar un vidrio", ["hat", "ahead"], "consonante"),
    _f("tʃ", "ch de «chile»", ["chair", "watch"], "consonante"),
    _f("dʒ", "como la «ch» pero con zumbido, parecida a la «y» de «yo» dicha con fuerza", ["jam", "age"], "consonante"),
    _f("m", "m de «mamá»", ["man", "time"], "consonante"),
    _f("n", "n de «nube»", ["no", "ten"], "consonante"),
    _f("ŋ", "la n de «tengo» o «banco», sin llegar a decir la g", ["sing", "long"], "consonante"),
    _f("l", "l de «lado»; al final de palabra, con la lengua más atrás", ["leg", "feel"], "consonante"),
    _f("ɹ", "no se parece a la r española: la lengua no toca nada y no vibra (en otros diccionarios, r)", ["red", "car"], "consonante"),
    _f("w", "la «hu» de «huevo»", ["we", "warn"], "consonante"),
    _f("j", "la «y» de «yate», o la «i» de «hielo»", ["yes", "you"], "consonante"),
    # --- Vocales (12) ---
    _f("i", "i de «sí», más larga (en otros diccionarios, iː)", ["see", "tea"], "vocal"),
    _f("ɪ", "no existe en español: entre la i y la e, corta y relajada", ["sit", "it"], "vocal"),
    _f("ɛ", "e de «perro» (en otros diccionarios, e)", ["bed", "red"], "vocal"),
    _f("æ", "no existe en español: entre la a y la e, con la boca muy abierta", ["cat", "trap"], "vocal"),
    _f("ɑ", "a de «papá», larga y con la boca bien abierta (en otros diccionarios, ɑː)", ["father", "hot"], "vocal"),
    _f("ɔ", "una o muy abierta, casi a (en otros diccionarios, ɔː)", ["law", "caught"], "vocal"),
    _f("ʊ", "no existe en español: entre la u y la o, corta y relajada", ["book", "put"], "vocal"),
    _f("u", "u de «tú», más larga (en otros diccionarios, uː)", ["food", "blue"], "vocal"),
    _f("ʌ", "una a corta y relajada, como el «ah» de sorpresa", ["cup", "strut"], "vocal"),
    _f("ə", "la vocal débil del inglés, como el «eh» de quien duda", ["about", "sofa"], "vocal"),
    _f("ɝ", "vocal con r: la lengua recogida hacia atrás, sin vibrar (en otros diccionarios, ɜː)", ["bird", "her"], "vocal"),
    _f("ɚ", "la misma vocal con r, pero débil y sin acento (en otros diccionarios, ər)", ["butter", "letter"], "vocal"),
    # --- Diptongos (5) ---
    _f("eɪ", "ei de «rey»", ["say", "day"], "diptongo"),
    _f("aɪ", "ai de «hay»", ["my", "price"], "diptongo"),
    _f("ɔɪ", "oy de «hoy»", ["boy", "choice"], "diptongo"),
    _f("oʊ", "una o que se cierra hacia u (en inglés británico, əʊ)", ["go", "no"], "diptongo"),
    _f("aʊ", "au de «jaula»", ["now", "how"], "diptongo"),
)

SIMBOLOS: tuple[str, ...] = tuple(f.simbolo for f in INVENTARIO)
_POR_SIMBOLO = {f.simbolo: f for f in INVENTARIO}

# Variantes que llegan de fuera -de los diccionarios de aprendizaje, de RP o
# del propio modelo- y a que fonema del inventario corresponden. Se aplican
# DESPUES de quitar barras, acentos y diacriticos (ver `normalizar`).
_ALIAS = {
    "r": "ɹ", "ɻ": "ɹ", "ʁ": "ɹ",
    "g": "ɡ",                       # la g del teclado frente a la del AFI
    "iː": "i", "uː": "u", "ɑː": "ɑ", "ɔː": "ɔ",
    "e": "ɛ", "ɛː": "ɛ",
    "ɜː": "ɝ", "ɜːr": "ɝ", "ɜr": "ɝ", "ɝː": "ɝ", "ɜ˞": "ɝ", "ɜ": "ɝ",
    "ər": "ɚ", "ə˞": "ɚ", "ɚː": "ɚ",
    "əʊ": "oʊ", "oː": "oʊ", "o": "oʊ", "ou": "oʊ",
    "ei": "eɪ", "ai": "aɪ", "oi": "ɔɪ", "ɔi": "ɔɪ", "au": "aʊ", "ɑʊ": "aʊ", "ɑɪ": "aɪ",
    "ʧ": "tʃ", "ʤ": "dʒ", "tš": "tʃ",
    "ɫ": "l",                       # la l oscura es la misma /l/
    "y": "j",                       # la y de «yes» que escribe quien no usa AFI
    "ʍ": "w",
}

# Diacriticos que no cambian el fonema: ligadura (t͡ʃ), no silabica (eɪ̯),
# silabica (n̩), aspiracion y los de posicion. Se quitan antes de comparar.
_DIACRITICOS = {"͡", "͜", "̯", "̩", "ʰ", "̚",
                "̠", "̟", "̥", "̪", "̃", "˞"}
_ENVOLTURA = "/[]ˈˌ.‿ ()'\"«»“”`"


def normalizar(simbolo: object) -> str | None:
    """El simbolo del inventario al que corresponde `simbolo`, o `None`.

    Acepta lo que devuelve un modelo o un diccionario: con o sin barras
    (`/w/`, `[w]`, `w`), con acento (`ˈæ`), con ligadura (`t͡ʃ`), con marca de
    longitud (`ɔː`) o en la notacion de RP y de los diccionarios de
    aprendizaje (`r`, `e`, `ɜː`, `əʊ`). Nunca lanza: lo que no sea un fonema
    del inventario -una palabra, una cadena vacia, `None`, un alofono- da
    `None`, y la interfaz pinta el texto sin reproductor.
    """
    if not isinstance(simbolo, str):
        return None
    texto = unicodedata.normalize("NFD", simbolo.strip())
    texto = "".join(c for c in texto
                    if c not in _DIACRITICOS and c not in _ENVOLTURA)
    # NFC de vuelta: `ɡ` y los simbolos AFI no se descomponen, pero una `é`
    # tecleada si, y hay que recomponerla para no confundirla con `e`.
    texto = unicodedata.normalize("NFC", texto)
    if not texto or len(texto) > 4:
        return None
    if texto in _POR_SIMBOLO:
        return texto
    return _ALIAS.get(texto) or _ALIAS.get(texto.lower())


def buscar(simbolo: object) -> Fonema | None:
    """El `Fonema` correspondiente, o `None` si no esta en el inventario."""
    canonico = normalizar(simbolo)
    return _POR_SIMBOLO.get(canonico) if canonico else None


def audio_de(simbolo: object) -> str | None:
    """Ruta del mp3 pregrabado de ese fonema, o `None`.

    `None` si el simbolo no esta en el inventario o si su audio no esta en
    disco (por ejemplo, en una copia donde aun no se ha corrido el
    generador). No necesita clave ni red: el archivo es parte del repositorio.
    """
    fonema = buscar(simbolo)
    if fonema is None:
        return None
    ruta = fonema.ruta
    try:
        if ruta.is_file() and ruta.stat().st_size > 0:
            return str(ruta)
    except OSError:
        pass
    return None


# --- IPA de la palabra entera: del diccionario local, nunca del modelo ------

_diccionario = None
_diccionario_fallo = False
_cerrojo = threading.Lock()


def _abrir_diccionario():
    """El SQLite de Kaikki, abierto una sola vez y solo cuando se pide.

    Se usa `lexicon.Diccionario` a secas, y no un `ConsultorLexico`: la IPA
    esta en la misma fila que la glosa y basta una SELECT, sin spaCy ni
    MiniLM, que son los que pesan y que `ui` sigue cargando al primer uso de
    la consulta lexica. Abrir el SQLite en `mode=ro` tarda milisegundos.

    Si el diccionario no esta (una copia sin datos), se recuerda el fallo
    para no reintentar el `open` en cada palabra.
    """
    global _diccionario, _diccionario_fallo
    if _diccionario is not None or _diccionario_fallo:
        return _diccionario
    with _cerrojo:
        if _diccionario is None and not _diccionario_fallo:
            try:
                import lexicon
                _diccionario = lexicon.Diccionario(lexicon.RUTA_DICCIONARIO)
            except Exception:
                _diccionario_fallo = True
    return _diccionario


def ipa_de_palabra(palabra: object) -> tuple[str | None, str | None]:
    """(transcripcion, variante) de la palabra segun Kaikki/Wiktionary.

    La variante es "US" si el volcado trae la de General American -la
    referencia de este modulo- y "UK" si solo trae la britanica. Si la
    palabra no esta, o esta sin IPA, devuelve `(None, None)`: **la
    transcripcion no se le pide nunca al modelo**, que la inventaria con toda
    seguridad y sin avisar. El volcado tiene IPA para unas 40.000 de sus
    1,48 M entradas, asi que el hueco es frecuente y la interfaz tiene que
    decirlo.

    Tampoco se lematiza («jumps» no esta, «jump» si): hacerlo pediria spaCy,
    que es uno de los recursos pesados, para una linea de ayuda. Nunca lanza.
    """
    if not isinstance(palabra, str) or not palabra.strip():
        return None, None
    try:
        dic = _abrir_diccionario()
        if dic is None:
            return None, None
        import lexicon
        with _cerrojo:
            entradas = dic.buscar(palabra.strip().strip("'’"))
        _uk, us, _a, _b = lexicon._mejor_fonetica(entradas, None)
        if us:
            return us, "US"
        if _uk:
            return _uk, "UK"
    except Exception:
        pass
    return None, None
