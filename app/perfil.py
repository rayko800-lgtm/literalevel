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
import json, os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from scoring import public_band, ANCHORS

RUTA_PERFIL_POR_DEFECTO = os.path.join(
    os.path.expanduser("~"), ".literalevel", "perfil.json")

# Margen que se suma al nivel comodo para proponer lecturas que estiren un
# poco al lector sin frustrarlo (i+1 de Krashen, en la escala publica 0..2).
RETO = 0.15


@dataclass
class Perfil:
    nivel: float                # escala publica 0..2
    banda: str
    origen: str                 # "muestra" | "cuestionario"
    creado: str
    nombre: str = ""

    @property
    def objetivo(self) -> float:
        """Dificultad recomendada: algo por encima de lo comodo."""
        return round(min(self.nivel + RETO, 2.0), 3)

    @property
    def rango_recomendado(self) -> tuple[float, float]:
        return (round(max(self.nivel - 0.10, 0.0), 3), self.objetivo)

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
            return Perfil(**json.load(f))
    except (json.JSONDecodeError, TypeError):
        return None   # perfil corrupto o de una version vieja: se rehace


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
# Cada respuesta aporta un valor en la escala publica 0..2. El resultado es
# la media, deliberadamente grosera: es un punto de partida, no una medicion.
PREGUNTAS = [
    ("habitos", "¿Con qué lees en inglés sin traductor?", [
        ("Casi nada todavía", 0.25),
        ("Textos cortos y sencillos", 0.60),
        ("Artículos y noticias", 1.00),
        ("Novelas contemporáneas", 1.40),
        ("Ensayo, literatura clásica o técnica", 1.80),
    ]),
    ("vocabulario", "Cuando lees una página, ¿cuántas palabras no conoces?", [
        ("Muchísimas, pierdo el hilo", 0.25),
        ("Unas 10 o más", 0.60),
        ("Entre 3 y 8", 1.05),
        ("Una o dos", 1.50),
        ("Casi ninguna", 1.85),
    ]),
    ("sintaxis", "¿Y las frases largas con varias subordinadas?", [
        ("Me pierdo casi siempre", 0.30),
        ("Necesito releerlas", 0.75),
        ("Las sigo con algo de esfuerzo", 1.15),
        ("No me suponen problema", 1.70),
    ]),
]


def desde_cuestionario(respuestas: dict[str, float], nombre: str = "") -> Perfil:
    """`respuestas` mapea clave de pregunta -> valor de la opcion elegida."""
    valores = [v for v in respuestas.values() if v is not None]
    if not valores:
        raise ValueError("Responde al menos una pregunta para estimar tu nivel.")
    nivel = round(sum(valores) / len(valores), 3)
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
