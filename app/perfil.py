"""Perfil de nivel del usuario (paso 1 del recorrido).

En vez de pedir al usuario que declare un nivel CEFR que probablemente no
conoce con precision, LiteraLevel lo situa con su propio modelo: el usuario
aporta un texto en ingles que lee comodo y ese texto se puntua con la misma
escala 0..2 que usa el resto de la app. La regla es la misma para todo el
sistema, asi que el nivel del lector y la dificultad de un libro son
directamente comparables.

Se ofrece un cuestionario como alternativa para quien no tenga un texto a mano.
"""
from __future__ import annotations
import json, math, os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from scoring import public_band, ANCHORS

RUTA_PERFIL_POR_DEFECTO = os.path.join(
    os.path.expanduser("~"), ".literalevel", "perfil.json")

# Margen que se suma al nivel comodo para proponer lecturas que estiren un
# poco al lector sin frustrarlo (i+1 de Krashen, en la escala publica 0..2).
RETO = 0.15

# Holgura alrededor del nivel del lector para recomendar: LA UNICA. La usan
# `rango_recomendado` -que es lo que se le dice al lector- y
# `catalogo.por_nivel` a traves de `ui.HOLGURA_POR_NIVEL`. Vive aqui, y no en
# `ui`, porque `perfil.describir` la anuncia antes de que `ui` filtre nada:
# tenerla en dos sitios ya nos costo dos pestanas prometiendo rangos distintos
# para el mismo perfil. Los niveles del catalogo son seis valores discretos y
# 0,25 es lo que garantiza que casi cualquier nivel tenga vecinos.
HOLGURA = 0.25


@dataclass
class Perfil:
    nivel: float                # escala publica 0..2
    banda: str
    origen: str                 # "muestra" | "cuestionario"
    creado: str
    nombre: str = ""

    @property
    def objetivo(self) -> float:
        """Dificultad de reto: algo por encima de lo comodo (i+1 de Krashen).

        OJO: **ya no es el techo del rango que se recomienda.** Lo fue, y de
        ahi salio que "Mi nivel" prometiera un rango asimetrico -nivel-0,10 a
        nivel+0,15- mientras "Sorprendeme" filtraba con nivel±`HOLGURA`. El
        rango vive en `rango_recomendado` y sale de `HOLGURA`, que es una sola.
        Esto se queda porque nombra una idea del documento -leer un escalon por
        encima- y puede hacer falta para decirla en la interfaz.
        """
        return round(min(self.nivel + RETO, 2.0), 3)

    @property
    def rango_recomendado(self) -> tuple[float, float]:
        """El rango que se ANUNCIA al lector, que es el que se FILTRA.

        Era asimetrico -nivel-0,10 a nivel+0,15- y la pestana "Mi nivel" lo
        anunciaba mientras "Sorprendeme" filtraba y anunciaba nivel±0,25:
        con nivel 1,13, una pestana prometia "entre 1.03 y 1.28" y la
        siguiente "entre 0.88 y 1.38" para el mismo perfil. Un solo numero,
        aqui, y `ui.HOLGURA_POR_NIVEL` lo lee de aqui.
        """
        return (round(max(self.nivel - HOLGURA, 0.0), 3),
                round(min(self.nivel + HOLGURA, 2.0), 3))

    def guardar(self, ruta: str = RUTA_PERFIL_POR_DEFECTO) -> str:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
        return ruta


def cargar(ruta: str = RUTA_PERFIL_POR_DEFECTO) -> Perfil | None:
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            p = Perfil(**json.load(f))
    except (json.JSONDecodeError, TypeError, ValueError, OSError):
        # `OSError` incluido: si `perfil.json` acaba siendo una CARPETA -o sin
        # permisos- `open` lanza PermissionError/IsADirectoryError, y esto lo
        # llama `_perfil_inicial`, que corre en `demo.load`: la pagina entera
        # arrancaba en error para ese lector.
        return None   # perfil corrupto o de una version vieja: se rehace
    # Y el TIPO, que no lo comprobaba nadie: `Perfil(**{"nivel": "abc"})` se
    # construye sin queja y revienta luego, en la aritmetica de quien lo use
    # -`_describir` hacia `nivel - 0.10` y salia un TypeError hacia la
    # interfaz-. Un perfil con el nivel no numerico es un perfil corrupto, y
    # aqui es donde se decide eso.
    try:
        p.nivel = float(p.nivel)
    except (TypeError, ValueError):
        return None
    # Y FINITO, y dentro de la escala. `float("1e400")` es `inf` y `float("nan")`
    # es `nan`: los dos pasan el `float()` de arriba sin queja, y con ellos la
    # pestana decia "Tu nivel de lectura: **inf / 2.00**" y "Lo mas leido entre
    # **inf** y **2.00**". La escala publica es 0..2 y todo lo que se salga de
    # ahi es un perfil corrupto.
    if not math.isfinite(p.nivel) or not 0.0 <= p.nivel <= 2.0:
        return None
    return p


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def desde_muestra(texto: str, puntuador, nombre: str = "") -> Perfil:
    """Situa al lector puntuando un texto que declara leer comodo.

    `puntuador` es un scoring.Puntuador ya cargado. Propaga ValueError con un
    mensaje legible si el texto no es prosa continua suficiente.
    """
    r = puntuador.puntuar(texto)
    return Perfil(nivel=r.puntuacion, banda=r.banda, origen="muestra",
                  creado=_ahora(), nombre=nombre)


# --- Cuestionario alternativo -----------------------------------------
# Las preguntas describen conductas que el lector puede recordar sin conocer
# terminologia gramatical. Cada entrada tiene la forma
# (clave, pregunta, opciones, multiple): la ultima marca permite a la interfaz
# distinguir las respuestas exclusivas de las que admiten varias opciones.
# Los valores siguen los anclajes publicos CEFR (A1=0.0, A2=0.4, B1=0.8,
# B2=1.2, C1=1.6, C2=2.0); los puntos intermedios reconocen que un habito
# aislado solo da una aproximacion del nivel.
# Solo `lecturas` es multiple: sus categorias pueden coexistir y su maximo
# refleja el techo de exposicion. Las demas opciones son grados ordenados de
# una misma frecuencia, ayuda o logro, por lo que elegir varias seria ambiguo.
PREGUNTAS = [
    ("frecuencia", "¿Con qué frecuencia lees algo en inglés?", [
        ("Nunca o casi nunca", 0.0),
        ("Menos de una vez al mes", 0.4),
        ("Varias veces al mes", 0.8),
        ("Varias veces por semana", 1.2),
        ("Casi todos los días", 1.6),
    ], False),
    ("lecturas", "¿Qué sueles leer en inglés y entender sin traducirlo entero?", [
        ("Todavía casi nada", 0.0),
        ("Mensajes, menús o instrucciones breves", 0.4),
        ("Noticias y artículos sobre temas conocidos", 1.0),
        ("Novelas actuales", 1.4),
        ("Literatura clásica o textos especializados", 2.0),
    ], True),
    ("diccionario", "Cuando lees una página en inglés, ¿cuánto usas el diccionario?", [
        ("En casi cada oración", 0.0),
        ("Varias veces por párrafo", 0.4),
        ("Unas pocas veces por página", 0.8),
        ("Solo de vez en cuando", 1.4),
        ("Casi nunca", 2.0),
    ], False),
    ("series", "¿Cómo ves series o películas en inglés?", [
        ("Todavía no logro seguirlas", 0.0),
        ("Con subtítulos en español", 0.4),
        ("Con subtítulos en inglés", 0.8),
        ("Sin subtítulos, si me basta la idea general", 1.4),
        ("Sin subtítulos y entiendo también los detalles", 2.0),
    ], False),
    ("libro_completo", "¿Has terminado un libro entero en inglés?", [
        ("No lo he intentado", 0.0),
        ("Empecé uno, pero no pude terminarlo", 0.4),
        ("Sí, uno adaptado o de lectura fácil", 0.8),
        ("Sí, una novela actual", 1.4),
        ("Sí, una obra clásica o especializada", 2.0),
    ], False),
    ("comprension", "Después de leer una página en inglés, ¿qué puedes contar de ella?", [
        ("Me cuesta explicar de qué trataba", 0.0),
        ("La idea general", 0.6),
        ("Los hechos o argumentos principales", 1.0),
        ("También los detalles y las relaciones entre ideas", 1.4),
        ("También lo implícito, el tono o el humor", 2.0),
    ], False),
]


# Los fragmentos son citas literales y autocontenidas de las ediciones de
# Project Gutenberg indicadas en `fuente`. Sus niveles son orientativos: no
# pretenden certificar CEFR, sino enfrentar al lector con dificultad creciente.
# El primer escalon se ancla en el nivel del pasaje. Releer resta poco; captar
# la idea con huecos situa algo por debajo; necesitar diccionario rebaja mas
# porque ya no hay comprension autonoma. Perder el hilo vale 0 porque no aporta
# evidencia de haber alcanzado el nivel del pasaje. La distancia aumenta en los
# textos dificiles: comprender a medias un C1/C2 si demuestra nivel intermedio.
_EXPERIENCIAS_FRAGMENTO = (
    "Lo entiendo con naturalidad, sin necesidad de releer",
    "Lo entiendo, aunque necesito releer alguna frase",
    "Capto bien la idea; solo se me escapan palabras sueltas",
    "Entiendo algunas partes, pero necesitaría el diccionario para seguirlo",
    "Me pierdo y no logro reconstruir la idea general",
)


def _opciones_fragmento(valores: tuple[float, ...]) -> list[tuple[str, float]]:
    return list(zip(_EXPERIENCIAS_FRAGMENTO, valores))


FRAGMENTOS = [
    {
        "clave": "fragmento_facil",
        "texto": (
            "Alice was beginning to get very tired of sitting by her sister "
            "on the bank, and of having nothing to do: once or twice she had "
            "peeped into the book her sister was reading, but it had no "
            "pictures or conversations in it, “and what is the use of a "
            "book,” thought Alice “without pictures or conversations?”"
        ),
        "obra": "Alice’s Adventures in Wonderland",
        "autor": "Lewis Carroll",
        "nivel_cefr": "A2/B1",
        "fuente": "https://www.gutenberg.org/ebooks/11",
        "pregunta": "Lee el fragmento y dime cuánto entiendes. Sé sincero:",
        "opciones": _opciones_fragmento((0.8, 0.6, 0.4, 0.2, 0.0)),
    },
    {
        "clave": "fragmento_medio",
        "texto": (
            "I could not help laughing at the ease with which he explained "
            "his process of deduction. “When I hear you give your reasons,” "
            "I remarked, “the thing always appears to me to be so ridiculously "
            "simple that I could easily do it myself, though at each successive "
            "instance of your reasoning I am baffled until you explain your "
            "process.”"
        ),
        "obra": "The Adventures of Sherlock Holmes",
        "autor": "Arthur Conan Doyle",
        "nivel_cefr": "B2",
        "fuente": "https://www.gutenberg.org/ebooks/1661",
        "pregunta": "Lee el fragmento y dime cuánto entiendes. Sé sincero:",
        "opciones": _opciones_fragmento((1.2, 1.0, 0.8, 0.4, 0.0)),
    },
    {
        "clave": "fragmento_dificil",
        "texto": (
            "It was already one in the morning; the rain pattered dismally "
            "against the panes, and my candle was nearly burnt out, when, by "
            "the glimmer of the half-extinguished light, I saw the dull yellow "
            "eye of the creature open; it breathed hard, and a convulsive "
            "motion agitated its limbs."
        ),
        "obra": "Frankenstein; or, the Modern Prometheus",
        "autor": "Mary Wollstonecraft Shelley",
        "nivel_cefr": "C1/C2",
        "fuente": "https://www.gutenberg.org/ebooks/84",
        "pregunta": "Lee el fragmento y dime cuánto entiendes. Sé sincero:",
        "opciones": _opciones_fragmento((2.0, 1.8, 1.6, 1.0, 0.0)),
    },
]


# Frente a un texto real la autoevaluacion tiene una referencia comun y suele
# ser mas fiable que describir habitos. El peso se aplica solo si hay respuestas
# de ambos bloques; contestar parcialmente cualquiera de ellos sigue sirviendo.
PESO_FRAGMENTOS = 0.65
_CLAVES_FRAGMENTOS = frozenset(f["clave"] for f in FRAGMENTOS)


def _valor_respuesta(valor: float | list[float] | None) -> float | None:
    """Normaliza una respuesta; en seleccion multiple conserva el techo."""
    if isinstance(valor, list):
        elegidos = [float(elemento) for elemento in valor
                    if elemento is not None]
        return max(elegidos) if elegidos else None
    return float(valor) if valor is not None else None


def desde_cuestionario(
        respuestas: dict[str, float | list[float] | None],
        nombre: str = "") -> Perfil:
    """Estima el nivel con valores escalares o listas de opciones elegidas."""
    normalizadas = ((k, _valor_respuesta(v)) for k, v in respuestas.items())
    valores = [(k, v) for k, v in normalizadas if v is not None]
    opinion = [v for k, v in valores if k not in _CLAVES_FRAGMENTOS]
    fragmentos = [v for k, v in valores if k in _CLAVES_FRAGMENTOS]
    if not opinion and not fragmentos:
        raise ValueError("Responde al menos una pregunta para estimar tu nivel.")

    nivel_opinion = sum(opinion) / len(opinion) if opinion else None
    # Los pasajes forman una escalera: interesa el techo mas dificil que el
    # lector declara comprender, no promediarlo con los escalones mas faciles.
    nivel_fragmentos = max(fragmentos) if fragmentos else None
    if nivel_opinion is None:
        nivel = nivel_fragmentos
    elif nivel_fragmentos is None:
        nivel = nivel_opinion
    else:
        nivel = ((1.0 - PESO_FRAGMENTOS) * nivel_opinion
                 + PESO_FRAGMENTOS * nivel_fragmentos)
    nivel = round(min(max(nivel, 0.0), 2.0), 3)
    return Perfil(nivel=nivel, banda=public_band(nivel), origen="cuestionario",
                  creado=_ahora(), nombre=nombre)


def describir(p: Perfil) -> str:
    """Resumen legible para mostrar en la interfaz."""
    lo, hi = p.rango_recomendado
    via = "un texto que nos diste" if p.origen == "muestra" else "el cuestionario"
    return (f"Tu nivel de lectura: **{p.nivel:.2f} / 2.00** ({p.banda}), "
            f"estimado con {via}.\n\n"
            f"Te buscaremos lecturas entre **{lo:.2f} y {hi:.2f}**: "
            f"cómodas pero con algo de reto.")
