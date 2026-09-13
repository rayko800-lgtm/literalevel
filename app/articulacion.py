"""La tabla del AFI de LiteraLevel: cada sonido del ingles con su articulacion.

Sirve a la pestaña «Sonidos IPA» (International Phonetic Alphabet; en español,
Alfabeto Fonético Internacional o AFI). Para cada sonido, en General American y en
britanico (RP), dice como se produce con el detalle de un manual de fonetica
-rasgos, labios, lengua, apertura de la boca, cuerdas vocales, salida del
aire-, que cambia de un acento a otro y la trampa tipica de un hispanohablante.

Son DATOS: este modulo no importa gradio ni sale a la red, y el audio de cada
sonido es un mp3 pregrabado. Pulsar un simbolo no cuesta nada ni necesita clave.

DOS INVENTARIOS
- General American: el de `fonemas.INVENTARIO` (41 sonidos), con sus mismos
  simbolos y sus mismos mp3 en `app/audio_fonemas/`. No se duplica: se le anade
  la ficha.
- RP (britanico): 44 sonidos, con la notacion de los diccionarios britanicos
  (`iː`, `e`, `ɜː`, `əʊ`, `r`) y los que General American no tiene: `ɒ` de
  «hot» y los diptongos centralizantes `ɪə`, `eə`, `ʊə`. Sus mp3 van aparte, en
  `app/audio_fonemas_rp/`, grabados con acento britanico.

Las fichas se escribieron a partir de la descripcion articulatoria estandar
(punto y modo de articulacion, altura y posicion de la lengua, redondeamiento).
Las notas de acento describen el habla de referencia de cada variedad, no a
todos sus hablantes: dentro de cada pais hay mucha variacion.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fonemas

DIR_AUDIO_RP = Path(__file__).resolve().parent / "audio_fonemas_rp"

ACENTOS = {"ga": "Americano (General American)", "rp": "Británico (RP)"}

# Orden de la tabla y titulo de cada grupo.
GRUPOS = [
    ("oclusiva", "Oclusivas"), ("fricativa", "Fricativas"), ("africada", "Africadas"),
    ("nasal", "Nasales"), ("aproximante", "Aproximantes"),
    ("vocal", "Vocales"), ("diptongo", "Diptongos"),
]


@dataclass(frozen=True)
class Ficha:
    rasgos: str      # la descripcion de manual: «oclusiva bilabial sorda»
    labios: str
    lengua: str
    boca: str        # apertura de la mandibula
    cuerdas: str     # vibran o no
    aire: str        # por donde y como sale
    trampa: str      # el error tipico de un hispanohablante
    ga: str = ""     # lo propio del americano
    rp: str = ""     # lo propio del britanico


@dataclass(frozen=True)
class Sonido:
    acento: str      # "ga" | "rp"
    simbolo: str
    nombre: str
    ejemplos: tuple[str, ...]
    grupo: str       # clave de GRUPOS
    ficha: Ficha
    clave: str = ""  # simbolo de FICHAS del que sale la ficha (RP «r» -> «ɹ», «iː» -> «i»)

    @property
    def archivo(self) -> str:
        return "_".join(f"{ord(c):04x}" for c in self.simbolo) + ".mp3"

    @property
    def ruta(self) -> Path:
        return (fonemas.DIR_AUDIO if self.acento == "ga" else DIR_AUDIO_RP) / self.archivo

    def audio(self) -> str | None:
        """Ruta del mp3 si esta en disco y no esta vacio; si no, `None`."""
        try:
            if self.ruta.is_file() and self.ruta.stat().st_size > 0:
                return str(self.ruta)
        except OSError:
            pass
        return None


_NO_VIBRAN = "no vibran: sonido sordo, solo aire (pon la mano en la garganta y no notarás nada)"
_VIBRAN = "vibran durante todo el sonido (con la mano en la garganta se nota el zumbido)"
_NEUTROS = "neutros, sin redondear ni estirar"
_RELAJADA = "relajada, en el suelo de la boca"

F = Ficha
FICHAS: dict[str, Ficha] = {
    # --- Oclusivas ---
    "p": F("oclusiva bilabial sorda",
           "se cierran por completo y se separan de golpe", "en reposo; no interviene",
           "se abre con la vocal que sigue", _NO_VIBRAN,
           "se retiene detrás de los labios y sale en una pequeña explosión. Al principio de "
           "una sílaba acentuada lleva aspiración [pʰ]: un soplo que apagaría una vela",
           "decirla sin soplo, como la p española, hace que «pin» suene a «bin»"),
    "b": F("oclusiva bilabial sonora",
           "se cierran por completo y se separan", "en reposo; no interviene",
           "se abre con la vocal que sigue", _VIBRAN,
           "sale al separar los labios, sin soplo",
           "entre vocales el español relaja la b y los labios no llegan a tocarse; en inglés "
           "se cierran del todo siempre"),
    "t": F("oclusiva alveolar sorda", _NEUTROS,
           "la punta toca el alvéolo, la encía dura justo detrás de los dientes de arriba; "
           "los lados de la lengua sellan contra las muelas",
           "entreabierta", _NO_VIBRAN,
           "se retiene y sale en explosión; aspirada [tʰ] al principio de sílaba acentuada",
           "apoyar la lengua en los dientes, como la t española, y decirla sin soplo",
           ga="entre dos vocales, sin acento en la segunda, se convierte en un toque rápido "
              "[ɾ] muy parecido a la r de «pero»: «water» [ˈwɑɾɚ], «butter» [ˈbʌɾɚ]",
           rp="se mantiene como t clara en «water»; en el habla británica coloquial se oye a "
              "veces como un corte de la garganta [ʔ] («wa'er»), pero no en la pronunciación de "
              "referencia"),
    "d": F("oclusiva alveolar sonora", _NEUTROS,
           "la punta toca el alvéolo, detrás de los dientes de arriba, no los dientes",
           "entreabierta", _VIBRAN, "sale al soltar la lengua, sin soplo",
           "la d española va en los dientes y entre vocales se suaviza hasta sonar como /ð/: "
           "«ladder» acaba pareciendo «lather»",
           ga="entre vocales también se vuelve el toque rápido [ɾ]: «ladder» y «latter» suenan casi igual",
           rp="se mantiene como d clara"),
    "k": F("oclusiva velar sorda", _NEUTROS,
           "la parte de atrás (el dorso) sube y toca el velo, el paladar blando del fondo de la boca",
           "entreabierta", _NO_VIBRAN,
           "se retiene detrás del cierre y sale en explosión; aspirada [kʰ] al principio de sílaba acentuada",
           "decirla sin soplo: «coat» suena a «goat»"),
    "ɡ": F("oclusiva velar sonora", _NEUTROS,
           "el dorso toca el velo, igual que en /k/", "entreabierta", _VIBRAN,
           "sale al soltar el dorso, sin soplo",
           "entre vocales el español la relaja y el dorso no llega a tocar; en inglés el cierre es completo"),
    # --- Fricativas ---
    "f": F("fricativa labiodental sorda",
           "el labio de abajo toca suavemente el borde de los dientes de arriba",
           "en reposo; no interviene", "casi cerrada", _NO_VIBRAN,
           "sale continuo por la rendija entre labio y dientes, con un soplido que se puede alargar",
           "casi ninguno; es igual que la f española"),
    "v": F("fricativa labiodental sonora",
           "el labio de abajo toca el borde de los dientes de arriba; los labios nunca se juntan",
           "en reposo; no interviene", "casi cerrada", _VIBRAN,
           "sale continuo por la rendija, con zumbido",
           "en español b y v suenan igual, con los labios juntos: «very» sale «berry»"),
    "θ": F("fricativa dental sorda", _NEUTROS,
           "la punta se asoma entre los dientes o se apoya detrás de los de arriba, sin cerrar el paso",
           "entreabierta", _NO_VIBRAN,
           "sale continuo por encima de la lengua; se puede alargar como un soplido",
           "cambiarla por t, f o s: «think» sale «tink», «fink» o «sink»"),
    "ð": F("fricativa dental sonora", _NEUTROS,
           "la punta entre los dientes o detrás de los de arriba, igual que en /θ/",
           "entreabierta", _VIBRAN,
           "sale continuo por encima de la lengua, con zumbido",
           "decir una d fuerte: «they» sale «day»"),
    "s": F("fricativa alveolar sorda", _NEUTROS,
           "la punta cerca del alvéolo sin tocarlo, con un surco en el centro por donde pasa el aire",
           "dientes casi juntos", _NO_VIBRAN, "sale continuo y afilado por el surco",
           "ante consonante al principio de palabra el español mete una e: «school» sale «eschool»"),
    "z": F("fricativa alveolar sonora", _NEUTROS,
           "la punta cerca del alvéolo, igual que en /s/", "dientes casi juntos", _VIBRAN,
           "sale continuo por el surco, con zumbido de abeja",
           "el español no tiene s sonora: «zoo» y «rose» salen con s y el zumbido desaparece"),
    "ʃ": F("fricativa postalveolar sorda",
           "redondeados y adelantados, como para dar un beso",
           "un poco más atrás que en /s/, detrás del alvéolo, con el cuerpo de la lengua abombado",
           "dientes casi juntos", _NO_VIBRAN,
           "sale continuo, más grave y ancho que en /s/: el «shhh» de pedir silencio",
           "decir ch (/tʃ/) o s: «ship» sale «chip» o «sip»"),
    "ʒ": F("fricativa postalveolar sonora",
           "redondeados y adelantados", "igual que en /ʃ/", "dientes casi juntos", _VIBRAN,
           "sale continuo con zumbido; nunca empieza palabra en inglés",
           "decir /dʒ/ o /ʃ/: «measure» sale «mejer» o «mesher»"),
    "h": F("fricativa glotal sorda",
           "ya en la posición de la vocal que sigue",
           "ya en la posición de la vocal que sigue; no toca nada",
           "la de la vocal que sigue", _NO_VIBRAN,
           "roza suavemente al pasar por la garganta, como al empañar un vidrio",
           "hacerla como la j española, raspando en el velo: «house» sale áspera; o no decirla"),
    # --- Africadas ---
    "tʃ": F("africada postalveolar sorda", "algo redondeados y adelantados",
            "la punta y la parte delantera cierran contra el alvéolo y se sueltan despacio hacia la posición de /ʃ/",
            "casi cerrada", _NO_VIBRAN,
            "se retiene y sale en una explosión que se alarga en «sh»",
            "casi ninguno; se parece a la ch de «chico»; cuidado con no cambiarla por /ʃ/"),
    "dʒ": F("africada postalveolar sonora", "algo redondeados y adelantados",
            "cierra contra el alvéolo y se suelta hacia la posición de /ʒ/, igual que en /tʃ/",
            "casi cerrada", _VIBRAN,
            "se retiene y sale en explosión con zumbido",
            "cambiarla por la y española o por ch: «jam» sale «yam» o «cham»"),
    # --- Nasales ---
    "m": F("nasal bilabial sonora", "cerrados por completo", "en reposo",
           "cerrada", _VIBRAN,
           "sale por la nariz: el velo baja y abre el paso nasal",
           "al final de palabra el español tiende a cambiarla por n: «time» casi «tine»"),
    "n": F("nasal alveolar sonora", _NEUTROS,
           "la punta en el alvéolo, sellando la salida por la boca", "entreabierta", _VIBRAN,
           "sale por la nariz", "casi ninguno; es igual que la n española"),
    "ŋ": F("nasal velar sonora", _NEUTROS,
           "el dorso sube y cierra contra el velo, como en /k/ y /ɡ/; la punta no toca nada",
           "entreabierta", _VIBRAN,
           "sale por la nariz; el sonido termina ahí, sin soltar una g",
           "añadir una g («sing» sale «sing-g») o cambiarla por n («sing» sale «sin»). Nunca empieza palabra"),
    # --- Aproximantes ---
    "l": F("aproximante lateral alveolar sonora", _NEUTROS,
           "la punta toca el alvéolo y el aire sale por los dos lados de la lengua",
           "entreabierta", _VIBRAN, "sale por los lados, sin fricción",
           "usar siempre la l clara del español, sobre todo al final de palabra",
           ga="casi siempre «oscura» [ɫ]: además de la punta, el dorso se levanta hacia atrás, "
              "y suena más grave, también en «leg»",
           rp="clara antes de vocal («leg») y oscura [ɫ] al final o antes de consonante («feel», «milk»)"),
    "ɹ": F("aproximante postalveolar sonora", "ligeramente redondeados",
           "la punta se curva hacia atrás o el cuerpo se recoge, sin tocar el paladar; los lados rozan las muelas",
           "entreabierta", _VIBRAN, "sale sin fricción ni golpe: la lengua nunca toca",
           "hacerla vibrar o dar un toque, como en «pero» o «perro»",
           ga="se pronuncia siempre, también al final de sílaba: «car» [kɑɹ], «bird» [bɝd]",
           rp="solo suena antes de vocal («red», «very»); en «car» no se pronuncia y la vocal se alarga [kɑː]"),
    "w": F("aproximante labiovelar sonora",
           "muy redondeados y adelantados, y se abren hacia la vocal siguiente",
           "el dorso se eleva hacia el velo", "casi cerrada al empezar", _VIBRAN,
           "sale sin fricción mientras los labios se abren",
           "meter una g delante («gwater») o pronunciarla como b: «wood» sale «good» o «bood»"),
    "j": F("aproximante palatal sonora", "estirados",
           "el dorso sube hacia el paladar duro sin tocarlo, como en una i muy rápida",
           "casi cerrada", _VIBRAN, "sale sin fricción",
           "convertirla en la «y/ll» fuerte de «yo» en muchas zonas: «yes» sale «dʒes»"),
    # --- Vocales de General American ---
    "i": F("vocal cerrada anterior tensa", "estirados, como en una sonrisa",
           "alta y adelantada, con los lados tocando las muelas de arriba", "casi cerrada", _VIBRAN,
           "sale por la boca; es larga",
           "no distinguirla de /ɪ/: «sheep» y «ship» suenan igual",
           rp="se escribe /iː/, con la marca de vocal larga"),
    "ɪ": F("vocal casi cerrada anterior laxa", "relajados",
           "algo más baja y más atrás que en /i/, y sin tensión", "entreabierta", _VIBRAN,
           "sale por la boca; es corta",
           "decir una i española, tensa: «ship» suena a «sheep», «bit» a «beat»"),
    "ɛ": F("vocal media abierta anterior", _NEUTROS,
           "a media altura y adelantada", "medio abierta", _VIBRAN, "sale por la boca; corta",
           "casi ninguna: es muy parecida a la e de «perro»",
           rp="se escribe /e/ y es algo más cerrada"),
    "æ": F("vocal casi abierta anterior", "ligeramente estirados",
           "baja y adelantada; la punta detrás de los dientes de abajo", "muy abierta", _VIBRAN,
           "sale por la boca",
           "decir la a española: «bad» suena a «bud» o «bod». Abre como para decir a y piensa en e",
           ga="larga y a veces con un deslizamiento hacia [ɛə] («man» [mɛən])",
           rp="más corta y abierta, cerca de [a]"),
    "ɑ": F("vocal abierta posterior no redondeada", "sin redondear, relajados",
           "baja y retrasada", "muy abierta, como para el médico", _VIBRAN, "sale por la boca; larga",
           "decirla corta y central como la a española",
           ga="es la vocal de «father» y también de «hot», «stop», «lot»",
           rp="se escribe /ɑː/ y es la de «father», «car», «bath»; «hot» usa otra vocal, /ɒ/"),
    "ɔ": F("vocal media abierta posterior redondeada", "redondeados",
           "retrasada, a media altura baja", "abierta", _VIBRAN, "sale por la boca",
           "decir una o española cerrada",
           ga="muchos hablantes la funden con /ɑ/: «caught» y «cot» suenan igual",
           rp="se escribe /ɔː/, es más cerrada y larga, con labios más redondeados: «law», «door», «thought»"),
    "ʊ": F("vocal casi cerrada posterior laxa", "algo redondeados, sin empujar",
           "alta y retrasada pero relajada, más baja que en /u/", "entreabierta", _VIBRAN,
           "sale por la boca; corta",
           "decir la u española, tensa y larga: «full» suena a «fool», «look» a «Luke»"),
    "u": F("vocal cerrada posterior tensa", "muy redondeados y adelantados",
           "alta y retrasada, tensa", "casi cerrada", _VIBRAN, "sale por la boca; larga",
           "no distinguirla de /ʊ/",
           ga="tras t, d, n, s suele adelantarse hacia [ʉ]: «new» [nu]",
           rp="se escribe /uː/; tras t, d, n se oye a menudo [j] delante: «new» [njuː]"),
    "ʌ": F("vocal media abierta central no redondeada", _NEUTROS,
           "en el centro de la boca, a media altura baja, relajada", "medio abierta", _VIBRAN,
           "sale por la boca; corta",
           "decir una a o una o españolas: «cup» sale «cap» o «cop»",
           rp="más abierta y adelantada, cerca de [ɐ]"),
    "ə": F("vocal media central (schwa)", "relajados", "en el centro, en reposo: todo suelto",
           "entreabierta", _VIBRAN,
           "sale por la boca; muy corta. Solo aparece en sílabas sin acento",
           "leer la vocal escrita: «about» con a clara, «banana» con tres aes españolas"),
    "ɝ": F("vocal media central rotacizada (acentuada)", "ligeramente redondeados",
           "recogida o con la punta curvada como en /ɹ/ durante toda la vocal", "entreabierta", _VIBRAN,
           "sale por la boca, con color de r de principio a fin",
           "decir «er» con e española y una r que vibra: «bird» sale «berd»",
           ga="es una sola vocal con r incorporada: «bird», «her», «word»",
           rp="no lleva r: /ɜː/, una vocal central larga con la lengua relajada"),
    "ɚ": F("vocal media central rotacizada (átona)", "relajados",
           "recogida como en /ɹ/, pero breve y sin fuerza", "entreabierta", _VIBRAN,
           "sale por la boca; corta, con color de r",
           "pronunciarla como «er» fuerte en «butter» o «teacher»",
           ga="es la terminación de «butter», «teacher», «color»",
           rp="no lleva r: se dice /ə/, una schwa normal"),
    # --- Diptongos de General American ---
    "eɪ": F("diptongo cerrante anterior: de [e] a [ɪ]", "de neutros a algo estirados",
            "empieza a media altura y sube hacia /ɪ/", "se cierra durante el sonido", _VIBRAN,
            "sale por la boca, deslizándose",
            "decir una e española sola, sin deslizar: «late» suena a «let»"),
    "aɪ": F("diptongo cerrante: de [a] a [ɪ]", "de neutros a algo estirados",
            "empieza baja y central, y sube hacia delante", "de muy abierta a casi cerrada", _VIBRAN,
            "sale por la boca, deslizándose", "casi ninguna: parecido a «hay»"),
    "ɔɪ": F("diptongo cerrante: de [ɔ] a [ɪ]", "de redondeados a relajados",
            "empieza atrás y media, y sube hacia delante", "de abierta a casi cerrada", _VIBRAN,
            "sale por la boca, deslizándose", "casi ninguna: parecido a «hoy»"),
    "oʊ": F("diptongo cerrante posterior: de [o] a [ʊ]", "redondeados y cada vez más cerrados",
            "empieza atrás a media altura y sube", "se cierra durante el sonido", _VIBRAN,
            "sale por la boca, deslizándose",
            "decir una o española sola: «coat» suena a «caught»",
            ga="empieza en una o redondeada: «go» [ɡoʊ]",
            rp="se escribe /əʊ/ y empieza en el centro, sin redondear: «go» [ɡəʊ]"),
    "aʊ": F("diptongo cerrante: de [a] a [ʊ]", "de abiertos a redondeados",
            "empieza baja y sube hacia atrás", "de muy abierta a casi cerrada", _VIBRAN,
            "sale por la boca, deslizándose", "casi ninguna: parecido a «causa»"),
    # --- Solo del britanico (RP) ---
    "ɒ": F("vocal abierta posterior redondeada", "ligeramente redondeados",
           "baja y retrasada", "muy abierta", _VIBRAN, "sale por la boca; corta",
           "decir la a española o una o cerrada",
           ga="no existe: «hot», «stop», «lot» usan /ɑ/",
           rp="es la vocal de «hot», «stop», «lot», «dog»"),
    "ɜː": F("vocal media central larga, sin r", "relajados",
            "en el centro, a media altura; la punta no se levanta", "entreabierta", _VIBRAN,
            "sale por la boca; larga",
            "añadir una r o decir e: «bird» sale «berd»",
            ga="en su lugar se dice /ɝ/, con r", rp="es la vocal de «bird», «her», «word»"),
    "ɪə": F("diptongo centralizante: de [ɪ] a [ə]", "relajados",
            "empieza alta y adelantada, y cae hacia el centro", "se abre un poco", _VIBRAN,
            "sale por la boca, deslizándose", "decir «ía» con dos vocales plenas",
            ga="no existe: «near» es /nɪɹ/, con r", rp="es la vocal de «near», «here», «ear»"),
    "eə": F("diptongo centralizante: de [e] a [ə]", "relajados",
            "empieza a media altura delante y va hacia el centro", "medio abierta", _VIBRAN,
            "sale por la boca; hoy muchos británicos la dicen como una e larga [ɛː]",
            "decir «ea» con dos vocales plenas",
            ga="no existe: «square» es /skwɛɹ/, con r", rp="es la vocal de «square», «hair», «where»"),
    "ʊə": F("diptongo centralizante: de [ʊ] a [ə]", "de algo redondeados a relajados",
            "empieza alta y atrás, y va hacia el centro", "se abre un poco", _VIBRAN,
            "sale por la boca; muchos británicos jóvenes dicen /ɔː/ en su lugar",
            "decir «úa» con dos vocales plenas",
            ga="no existe: «tour» es /tʊɹ/, con r", rp="es la vocal de «tour», «pure», «cure»"),
}

# Grupo de cada sonido para ordenar la tabla.
_GRUPO = {
    **dict.fromkeys(["p", "b", "t", "d", "k", "ɡ"], "oclusiva"),
    **dict.fromkeys(["f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ", "h"], "fricativa"),
    **dict.fromkeys(["tʃ", "dʒ"], "africada"),
    **dict.fromkeys(["m", "n", "ŋ"], "nasal"),
    **dict.fromkeys(["l", "ɹ", "w", "j"], "aproximante"),
}


def _grupo(simbolo: str, tipo: str) -> str:
    return _GRUPO.get(simbolo, "diptongo" if tipo == "diptongo" else "vocal")


# --- General American: el inventario de `fonemas`, con su ficha -------------

INVENTARIO_GA: tuple[Sonido, ...] = tuple(
    Sonido("ga", f.simbolo, f.nombre, f.ejemplos, _grupo(f.simbolo, f.tipo), FICHAS[f.simbolo], f.simbolo)
    for f in fonemas.INVENTARIO)

# --- RP: notacion britanica, ficha compartida cuando el sonido es el mismo ---
# (simbolo RP, ficha de la que sale, nombre, ejemplos, grupo)
_RP = [
    ("p", "p", None, None), ("b", "b", None, None), ("t", "t", None, None), ("d", "d", None, None),
    ("k", "k", None, None), ("ɡ", "ɡ", None, None),
    ("f", "f", None, None), ("v", "v", None, None), ("θ", "θ", None, None), ("ð", "ð", None, None),
    ("s", "s", None, None), ("z", "z", None, None), ("ʃ", "ʃ", None, None), ("ʒ", "ʒ", None, None),
    ("h", "h", None, None), ("tʃ", "tʃ", None, None), ("dʒ", "dʒ", None, None),
    ("m", "m", None, None), ("n", "n", None, None), ("ŋ", "ŋ", None, None),
    ("l", "l", None, ("leg", "feel")),
    ("r", "ɹ", "la r inglesa: la lengua no toca nada y no vibra; solo suena antes de vocal", ("red", "very")),
    ("w", "w", None, None), ("j", "j", None, None),
    ("iː", "i", "i de «sí», larga y con los labios estirados", ("see", "tea")),
    ("ɪ", "ɪ", None, None),
    ("e", "ɛ", "e de «perro», un poco más cerrada", ("bed", "red")),
    ("æ", "æ", "entre la a y la e, corta y con la boca muy abierta", ("cat", "trap")),
    ("ʌ", "ʌ", "una a corta y relajada", ("cup", "love")),
    ("ɑː", "ɑ", "a larga con la boca bien abierta y la lengua atrás", ("father", "car")),
    ("ɒ", "ɒ", "no existe en español: una o muy abierta y corta", ("hot", "dog")),
    ("ɔː", "ɔ", "o larga con los labios bien redondeados", ("law", "door")),
    ("ʊ", "ʊ", None, None),
    ("uː", "u", "u de «tú», larga y con los labios adelantados", ("food", "blue")),
    ("ɜː", "ɜː", "vocal central larga, sin r: la lengua relajada en medio", ("bird", "her")),
    ("ə", "ə", None, None),
    ("eɪ", "eɪ", None, None), ("aɪ", "aɪ", None, None), ("ɔɪ", "ɔɪ", None, None),
    ("əʊ", "oʊ", "empieza en una schwa central y se cierra hacia u", ("go", "no")),
    ("aʊ", "aʊ", None, None),
    ("ɪə", "ɪə", "de i relajada hacia la schwa, sin r", ("near", "here")),
    ("eə", "eə", "de e hacia la schwa, sin r; hoy casi una e larga", ("square", "hair")),
    ("ʊə", "ʊə", "de u relajada hacia la schwa, sin r", ("tour", "pure")),
]


def _rp() -> tuple[Sonido, ...]:
    por_simbolo = {f.simbolo: f for f in fonemas.INVENTARIO}
    salida = []
    for simbolo, clave, nombre, ejemplos in _RP:
        base = por_simbolo.get(clave)
        tipo = base.tipo if base else ("diptongo" if len(simbolo.replace("ː", "")) > 1 else "vocal")
        salida.append(Sonido(
            "rp", simbolo,
            nombre or (base.nombre if base else simbolo),
            tuple(ejemplos) if ejemplos else (base.ejemplos if base else ()),
            _grupo(clave, tipo), FICHAS[clave], clave))
    return tuple(salida)


INVENTARIO_RP: tuple[Sonido, ...] = _rp()


def inventario(acento: str) -> tuple[Sonido, ...]:
    """Los sonidos de un acento ("ga" o "rp"), en el orden de la tabla."""
    lista = INVENTARIO_RP if acento == "rp" else INVENTARIO_GA
    orden = {g: i for i, (g, _) in enumerate(GRUPOS)}
    return tuple(sorted(lista, key=lambda s: orden[s.grupo]))


def buscar(simbolo: str, acento: str = "ga") -> Sonido | None:
    """El sonido de ese simbolo en ese acento, o `None`."""
    return next((s for s in inventario(acento) if s.simbolo == simbolo), None)
