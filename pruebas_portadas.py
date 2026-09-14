"""Pruebas de la parte pura del cuaderno de portadas (tools/colab_portadas.py).

Solo ejecuta las celdas marcadas `# %% [puro]`: nada de GPU, red ni Colab. El
cuaderno es la unica fuente de las reglas; aqui se comprueba que:
- el prompt nunca lleva titulo, autor ni nombres propios, y siempre pide sin
  texto y sin caras;
- la semilla es determinista y la decada sale de las fechas del autor;
- la paleta y los contrastes WCAG son los que dicen;
- las reglas de exclusion son las MISMAS que las de app/catalogo.py.

Uso:  python -X utf8 pruebas_portadas.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, "app")
os.environ["LITERALEVEL_DATOS"] = tempfile.mkdtemp(prefix="literalevel_portadas_")

FALLOS: list[str] = []
HECHAS = 0


def prueba(nombre, fn):
    global HECHAS
    HECHAS += 1
    try:
        r = fn()
        print(f"  ok   {nombre}" + (f"  -> {r}" if r else ""))
    except Exception as e:
        FALLOS.append(nombre)
        print(f"  FALLA {nombre}  -> {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)


def _celdas_puras() -> dict:
    fuente = Path("tools/colab_portadas.py").read_text(encoding="utf-8")
    trozos = fuente.split("# %%")
    puros = [t[len(" [puro]"):] for t in trozos if t.startswith(" [puro]")]
    assert puros, "el cuaderno no tiene celdas [puro]"
    espacio: dict = {}
    exec(compile("\n".join(puros), "colab_portadas[puro]", "exec"), espacio)
    return espacio


P = _celdas_puras()
FILA = {"id": "PG11", "title": "Alice's Adventures in Wonderland",
        "author": "Carroll, Lewis, 1832-1898",
        "hook": "Alice follows the White Rabbit down a hole in Oxford and meets the Queen.",
        "temas": "Fantasy fiction; Alice (Fictitious character) -- Juvenile fiction; Wonderland (Imaginary place)"}

print("\nPortadas: parte pura")


def _prompt_sin_titulo_ni_autor():
    p = P["construir_prompt"](FILA)
    bajo = p.lower()
    for prohibida in ("alice", "wonderland", "carroll", "lewis", "rabbit hole", "oxford", "queen"):
        assert prohibida not in bajo, f"el prompt lleva «{prohibida}»: {p}"
    assert "no text" in bajo and "no faces" in bajo and "no people" in bajo, p
    assert "floating castle" in bajo, "no usa el motivo de Fantasy fiction"
    assert "1860s" in bajo, "no pone la decada del autor"
    return p[:120] + "…"


prueba("el prompt no lleva titulo, autor ni nombres, y pide sin texto ni caras", _prompt_sin_titulo_ni_autor)


def _decada_y_semilla():
    assert P["decada"]("Carroll, Lewis, 1832-1898") == "1860s"
    assert P["decada"]("Shakespeare, William, 1564-1616") == "1590s"
    assert P["decada"]("Anonymous") is None and P["decada"]("") is None
    s = P["semilla"]
    assert s("PG11") == s("pg11") and s("PG11") != s("PG12") and 0 <= s("PG11") < 2**32
    return f"PG11 -> {s('PG11')}"


prueba("la decada sale del autor y la semilla es determinista por id", _decada_y_semilla)


def _motivos():
    M = P["MOTIVOS"]
    assert len(M) == 30, f"el mapa tiene {len(M)} temas, no 30"
    assert P["motivos_de"]("Nada que ver; Tampoco") == [P["MOTIVO_POR_DEFECTO"]]
    assert P["motivos_de"]("Science fiction; Horror tales -- 20th century; England -- Fiction", maximo=2) == \
        [M["Science fiction"], M["Horror tales"]]
    for tema, motivo in M.items():
        assert not any(w in motivo.lower() for w in ("face", "portrait of", " text", "letter")) or "no face" in motivo, \
            f"el motivo de {tema} pide caras o texto: {motivo}"
    return "30 temas, orden respetado, motivo por defecto"


prueba("el mapa de 30 temas a motivos se aplica en orden", _motivos)


def _contraste_y_paleta():
    c = P["contraste"]
    assert c("#FFFFFF", "#000000") == 21.0 and c("#777777", "#777777") == 1.0
    from PIL import Image
    img = Image.new("RGB", (80, 120), (20, 40, 90))
    for x in range(30):
        for y in range(120):
            img.putpixel((x, y), (230, 180, 40))
    pal = P["paleta_de"](img)
    assert 1 <= len(pal) <= 5 and abs(sum(p["proporcion"] for p in pal) - 1) < 0.01, pal
    assert pal[0]["proporcion"] >= pal[-1]["proporcion"], "la paleta no va de mas a menos"
    col = P["colores_de_lectura"](pal)
    assert col["contraste_texto"] >= 4.5, col
    assert c("#F2F2F2", col["fondo_lector"]) >= 7.0, col
    assert col["contraste_acento"] >= 4.5, col
    return f"dominante {pal[0]['hex']}, texto {col['color_texto']}, fondo {col['fondo_lector']}, acento {col['acento']}"


prueba("paleta de 5 colores y contrastes WCAG del lector", _contraste_y_paleta)


def _json_contrato():
    pal = [{"hex": "#223344", "proporcion": 0.6}, {"hex": "#DDAA33", "proporcion": 0.4}]
    d = P["json_de_portada"](FILA, P["construir_prompt"](FILA), pal, 123.4, 12.3, 1.87)
    for clave in ("id", "modelo", "semilla", "prompt_sha", "paleta", "color_texto", "fondo_lector",
                  "acento", "archivos", "kb", "generada_por_ia", "aviso"):
        assert clave in d, f"falta {clave} en el JSON"
    assert d["id"] == "PG11" and d["generada_por_ia"] is True and d["aviso"] == "Portada generada por IA, no oficial"
    assert d["archivos"] == {"portada": "PG11.webp", "miniatura": "PG11_256.webp"}
    assert "Alice" not in str(d), "el JSON guarda el titulo o el prompt en claro"
    return "claves del contrato presentes, sin prompt en claro"


prueba("el JSON por portada cumple el contrato del front", _json_contrato)


def _mismas_reglas_que_la_app():
    import catalogo as cm
    assert P["NO_ES_LECTURA_TEMAS"] == cm._NO_ES_LECTURA_TEMAS.pattern, "temas de exclusion distintos de la app"
    assert P["NO_ES_LECTURA_TITULO"] == cm._NO_ES_LECTURA_TITULO.pattern, "titulos de exclusion distintos de la app"
    assert P["LITERARIO"] == cm._LITERARIO.pattern, "regla de literario distinta de la app"
    import pandas as pd
    df = pd.DataFrame({
        "id": ["PG1", "PG2", "PG3", "PG4"], "downloads": [10, 50, 40, 30],
        "title": ["Uno", "The Fairy Books A Project Gutenberg Linked Index", "Tres", "Cuatro"],
        "temas": ["Fiction", "Fairy tales", "Chemistry", "Love stories"], "author": [""] * 4, "hook": [""] * 4})
    sel = P["seleccionar"](df, "top_medido", n=10)
    assert sel["id"].tolist() == ["PG4", "PG1"], sel["id"].tolist()
    cur = P["seleccionar"](df, "curado", n=10, ids_curado=["PG1"])
    assert cur["id"].tolist() == ["PG1"], cur["id"].tolist()
    return "exclusion y literario identicos a app/catalogo.py"


prueba("la seleccion usa las mismas reglas que el catalogo de la app", _mismas_reglas_que_la_app)

print()
if FALLOS:
    print(f"{len(FALLOS)} fallo(s) de {HECHAS} pruebas de portadas:")
    for n in FALLOS:
        print(f"- {n}")
    sys.exit(1)
print(f"Todas las pruebas de portadas pasan ({HECHAS}).")
