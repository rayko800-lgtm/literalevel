"""Las paletas de color de LiteraLevel, y por que hay mas de una.

El tema original -hielo azul sobre negro espacial- es el que quiso Miguel y
sigue siendo el que sale por defecto. Pero la primera lectora real de la app
fue su prima Esmeralda, quince anos, y dijo dos cosas que no se pueden
ignorar: que los colores "me dan mucha hueva" y que la pagina se siente
antigua, "todo muy recto, muy marcado".

Las dos criticas tienen arreglo y son distintas:

- El color es gusto, y el gusto no se discute: se ofrece. De ahi las paletas.
- Lo "recto y marcado" no es gusto, es diseno: esquinas vivas, bordes duros y
  contraste alto. Eso se corrige para TODAS las paletas, no solo para las
  suaves, porque tambien mejora la de Miguel.

Cada paleta es un puñado de variables CSS. La estructura -que es un panel,
que es un boton, donde va cada cosa- no cambia nunca: solo cambian los
colores. Asi una paleta nueva son diez lineas y no puede romper la interfaz.
"""
from __future__ import annotations

# `estrellas` dice si el fondo lleva el campo de estrellas. En las paletas
# claras no pinta nada: se verian como suciedad sobre el papel.
PALETAS: dict[str, dict] = {
    "hielo": {
        "nombre": "Hielo sobre el espacio",
        "pista": "la de siempre: azul de iceberg sobre negro",
        "estrellas": True,
        "vars": {
            "--ll-fondo": "#05070d",
            "--ll-fondo-alto": "#070c17",
            "--ll-fondo-bajo": "#0a1522",
            "--ll-panel": "rgba(12,22,38,.72)",
            "--ll-borde": "rgba(143,211,232,.16)",
            "--ll-acento": "#8fd3e8",
            "--ll-acento-hondo": "#1d6285",
            "--ll-acento-claro": "#a8e2f4",
            "--ll-texto": "#dfeaf3",
            "--ll-lector-fondo": "rgba(8,16,28,.62)",
            "--ll-lector-texto": "#e8f1f8",
            "--ll-seleccion": "rgba(143,211,232,.38)",
            "--ll-halo": "rgba(60,150,190,.30)",
            "--ll-titulo-1": "#eaf8ff",
            "--ll-titulo-2": "#a8e2f4",
            "--ll-titulo-3": "#4bb8da",
            "--ll-sombra-titulo": "rgba(120,205,235,.35)",
            "--ll-boton-alto": "#257c99",
            "--ll-boton-texto": "#f2fbff",
        },
    },
    "amanecer": {
        "nombre": "Amanecer",
        "pista": "crema y naranja suave, en claro",
        "estrellas": False,
        "vars": {
            "--ll-fondo": "#fdf6ef",
            "--ll-fondo-alto": "#fbeee2",
            "--ll-fondo-bajo": "#f7e6d6",
            "--ll-panel": "rgba(255,252,248,.86)",
            "--ll-borde": "rgba(198,124,74,.20)",
            "--ll-acento": "#aa5b2d",
            "--ll-acento-hondo": "#a4522a",
            "--ll-acento-claro": "#e79a5f",
            "--ll-texto": "#4a3a30",
            "--ll-lector-fondo": "rgba(255,253,250,.92)",
            "--ll-lector-texto": "#3b2f27",
            "--ll-seleccion": "rgba(231,154,95,.42)",
            "--ll-halo": "rgba(231,154,95,.22)",
            "--ll-titulo-1": "#b0532a",
            "--ll-titulo-2": "#ca7840",
            "--ll-titulo-3": "#bd7e4e",
            "--ll-sombra-titulo": "rgba(231,154,95,.28)",
            "--ll-boton-alto": "#ae5a1e",
            "--ll-boton-texto": "#fffaf5",
        },
    },
    "menta": {
        "nombre": "Menta",
        "pista": "verde y lila pastel, muy suave",
        "estrellas": False,
        "vars": {
            "--ll-fondo": "#f4faf6",
            "--ll-fondo-alto": "#edf6f1",
            "--ll-fondo-bajo": "#e6f2ec",
            "--ll-panel": "rgba(255,255,255,.86)",
            "--ll-borde": "rgba(90,150,125,.20)",
            "--ll-acento": "#3e7c64",
            "--ll-acento-hondo": "#3a7a61",
            "--ll-acento-claro": "#82c7a9",
            "--ll-texto": "#33463e",
            "--ll-lector-fondo": "rgba(255,255,255,.93)",
            "--ll-lector-texto": "#2b3a34",
            "--ll-seleccion": "rgba(130,199,169,.45)",
            "--ll-halo": "rgba(130,199,169,.22)",
            "--ll-titulo-1": "#3a7a61",
            "--ll-titulo-2": "#559b80",
            "--ll-titulo-3": "#6e93a6",
            "--ll-sombra-titulo": "rgba(130,199,169,.26)",
            "--ll-boton-alto": "#3e7f66",
            "--ll-boton-texto": "#ffffff",
        },
    },
    "papel": {
        "nombre": "Papel",
        "pista": "como un libro de bolsillo, para leer horas",
        "estrellas": False,
        "vars": {
            "--ll-fondo": "#f6f1e6",
            "--ll-fondo-alto": "#f2ece0",
            "--ll-fondo-bajo": "#ede6d8",
            "--ll-panel": "rgba(252,249,242,.90)",
            "--ll-borde": "rgba(120,104,80,.22)",
            "--ll-acento": "#846843",
            "--ll-acento-hondo": "#6b5333",
            "--ll-acento-claro": "#b39468",
            "--ll-texto": "#40382c",
            "--ll-lector-fondo": "rgba(253,250,244,.95)",
            "--ll-lector-texto": "#332d24",
            "--ll-seleccion": "rgba(212,178,120,.48)",
            "--ll-halo": "rgba(179,148,104,.18)",
            "--ll-titulo-1": "#6b5333",
            "--ll-titulo-2": "#8a6d46",
            "--ll-titulo-3": "#a0845d",
            "--ll-sombra-titulo": "rgba(179,148,104,.22)",
            "--ll-boton-alto": "#8a6f44",
            "--ll-boton-texto": "#fffdf8",
        },
    },
    "medianoche": {
        "nombre": "Medianoche",
        "pista": "oscura pero sin azul, descansada",
        "estrellas": False,
        "vars": {
            "--ll-fondo": "#16151a",
            "--ll-fondo-alto": "#1b1a20",
            "--ll-fondo-bajo": "#201e26",
            "--ll-panel": "rgba(38,36,45,.80)",
            "--ll-borde": "rgba(200,180,220,.16)",
            "--ll-acento": "#c9b6e4",
            "--ll-acento-hondo": "#6d5a8c",
            "--ll-acento-claro": "#dcccf0",
            "--ll-texto": "#e4dfea",
            "--ll-lector-fondo": "rgba(30,28,36,.72)",
            "--ll-lector-texto": "#ece7f2",
            "--ll-seleccion": "rgba(201,182,228,.36)",
            "--ll-halo": "rgba(140,115,175,.24)",
            "--ll-titulo-1": "#f0e9f8",
            "--ll-titulo-2": "#c9b6e4",
            "--ll-titulo-3": "#9b83c0",
            "--ll-sombra-titulo": "rgba(180,155,215,.30)",
            "--ll-boton-alto": "#7e63a8",
            "--ll-boton-texto": "#fbf8ff",
        },
    },
}

POR_DEFECTO = "hielo"


def opciones() -> list[tuple[str, str]]:
    """Para el selector: (lo que se lee, la clave)."""
    return [(f"{d['nombre']} — {d['pista']}", k) for k, d in PALETAS.items()]


def css(clave: str, estrellas_css: str = "") -> str:
    """El `<style>` de una paleta. Devuelve el de por defecto si no la conoce."""
    d = PALETAS.get(clave) or PALETAS[POR_DEFECTO]
    variables = ";".join(f"{k}:{v}" for k, v in d["vars"].items())
    # El campo de estrellas solo en las paletas que lo piden. En una clara se
    # veria como puntos de suciedad sobre el papel.
    fondo = (f"{estrellas_css}," if d["estrellas"] and estrellas_css else "")
    return (
        "<style>"
        f":root{{{variables}}}"
        "body,gradio-app,.gradio-container{"
        "background-color:var(--ll-fondo) !important;"
        f"background-image:{fondo}"
        "radial-gradient(120% 62% at 50% 118%,var(--ll-halo) 0%,transparent 72%),"
        "linear-gradient(180deg,var(--ll-fondo) 0%,var(--ll-fondo-alto) 55%,"
        "var(--ll-fondo-bajo) 100%) !important;"
        "background-attachment:fixed !important;"
        "background-repeat:no-repeat !important;"
        "color:var(--ll-texto) !important}"
        # --- La paleta tiene que ganarle al modo del navegador -----------
        # Esto NO es un adorno. Gradio pinta el texto de Markdown con
        # `.prose *{color:var(--body-text-color)}`, y esa variable la resuelve
        # SU tema segun el modo claro/oscuro del visitante, no segun la paleta
        # elegida aqui. Poner `color` en el contenedor no basta: la regla de
        # `.prose` es mas especifica y gana.
        #
        # Medido en el Space con ?__theme=light y la paleta por defecto:
        # texto rgb(23,30,48) sobre panel oscuro, 1,1:1. La pagina se veia
        # negra y sin texto. En modo oscuro, las tres paletas claras daban
        # 1,3:1 en todo el cuerpo. O sea que NINGUNA paleta se leia en los dos
        # modos, y las pruebas no podian verlo porque miden --ll-texto sobre
        # --ll-fondo, una pareja que el navegador nunca llega a pintar.
        #
        # Se redefinen las variables del tema, en `:root` y en `.dark`, para
        # que la paleta sea la que decide en los dos modos.
        ":root,.dark,gradio-app,.gradio-container{"
        "--body-text-color:var(--ll-texto) !important;"
        "--body-text-color-subdued:var(--ll-texto) !important;"
        "--block-title-text-color:var(--ll-texto) !important;"
        "--block-label-text-color:var(--ll-texto) !important;"
        "--block-info-text-color:var(--ll-texto) !important;"
        "--body-background-fill:var(--ll-fondo) !important;"
        "--background-fill-primary:var(--ll-fondo) !important;"
        "--border-color-primary:var(--ll-borde) !important;"
        "--link-text-color:var(--ll-acento) !important;"
        "--link-text-color-active:var(--ll-acento) !important;"
        "--link-text-color-hover:var(--ll-acento) !important;"
        "--link-text-color-visited:var(--ll-acento) !important}"
        ".prose,.prose *,.markdown-text,.markdown-text *{"
        "color:var(--ll-texto) !important}"
        "label,.label-wrap,.svelte-1gfkn6j{color:var(--ll-texto) !important}"
        "</style>")
