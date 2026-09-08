"""Convierte un .py con marcas `# %%` en un .ipynb que Colab abre directo.

Existe porque el .py es lo que se puede revisar en el repositorio -se lee, se
compara entre versiones, se comenta- y el .ipynb es lo que Colab necesita. El
que manda es el .py: el notebook se regenera, no se edita a mano.

Uso:  python -X utf8 tools/a_notebook.py colab_precalculo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def celdas(texto: str) -> list[dict]:
    fuera, actual, tipo = [], [], "code"
    for linea in texto.split("\n"):
        if linea.startswith("# %%"):
            if actual:
                fuera.append((tipo, actual))
            tipo = "markdown" if "[markdown]" in linea else "code"
            actual = []
            continue
        actual.append(linea)
    if actual:
        fuera.append((tipo, actual))

    celdas_json = []
    for tipo, lineas in fuera:
        if tipo == "markdown":
            # En el .py el texto va comentado; en el notebook, no.
            lineas = [l[2:] if l.startswith("# ") else l.lstrip("#")
                      for l in lineas]
        cuerpo = "\n".join(lineas).strip("\n")
        if not cuerpo.strip():
            continue
        fuente = [l + "\n" for l in cuerpo.split("\n")]
        fuente[-1] = fuente[-1].rstrip("\n")
        c = {"cell_type": tipo, "metadata": {}, "source": fuente}
        if tipo == "code":
            c["execution_count"] = None
            c["outputs"] = []
        celdas_json.append(c)
    return celdas_json


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    origen = Path(sys.argv[1])
    destino = origen.with_suffix(".ipynb")
    nb = {
        "cells": celdas(origen.read_text(encoding="utf-8")),
        "metadata": {
            "colab": {"provenance": [], "toc_visible": True},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
            "accelerator": "GPU",
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    destino.write_text(json.dumps(nb, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    codigo = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
    print(f"{destino}  ({len(nb['cells'])} celdas, {codigo} de código)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
