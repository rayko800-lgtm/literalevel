"""Comprobaciones del cuestionario de nivel, sin cargar recursos pesados.

Uso:  python -X utf8 pruebas_perfil.py
"""
from __future__ import annotations

import re
import sys

sys.path.insert(0, "app")
import perfil  # noqa: E402


def _respuesta_extrema(opciones, indice: int) -> float:
    return opciones[indice][1]


assert 5 <= len(perfil.PREGUNTAS) <= 7
assert 3 <= len(perfil.FRAGMENTOS) <= 4

# Esta prueba evita que al editar una cita se salga silenciosamente del largo
# que permite leerla como parte de un cuestionario breve.
for fragmento in perfil.FRAGMENTOS:
    palabras = re.findall(r"[A-Za-z]+(?:[’'-][A-Za-z]+)*", fragmento["texto"])
    assert 40 <= len(palabras) <= 70, (fragmento["clave"], len(palabras))

faciles = {
    clave: _respuesta_extrema(opciones, 0)
    for clave, _, opciones in perfil.PREGUNTAS
}
dificiles = {
    clave: _respuesta_extrema(opciones, -1)
    for clave, _, opciones in perfil.PREGUNTAS
}
for fragmento in perfil.FRAGMENTOS:
    # En las preguntas de opinion la primera opcion es la mas facil; en los
    # fragmentos el orden solicitado pone "Lo entiendo todo" primero.
    faciles[fragmento["clave"]] = _respuesta_extrema(fragmento["opciones"], -1)
    dificiles[fragmento["clave"]] = _respuesta_extrema(fragmento["opciones"], 0)

nivel_facil = perfil.desde_cuestionario(faciles).nivel
nivel_dificil = perfil.desde_cuestionario(dificiles).nivel
assert nivel_facil <= 0.1, nivel_facil
assert nivel_dificil >= 1.9, nivel_dificil

# La compatibilidad parcial incluye una clave del cuestionario anterior, que
# desde_cuestionario debe seguir tratando como una respuesta de opinion.
assert perfil.desde_cuestionario({"sintaxis": 0.75}).nivel == 0.75
assert perfil.desde_cuestionario({"fragmento_facil": 0.8}).nivel == 0.8

print(f"TODO OK: extremo fácil={nivel_facil:.3f}, extremo difícil={nivel_dificil:.3f}")
