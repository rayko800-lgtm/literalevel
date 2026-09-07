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

# Contrato para la interfaz: (clave, pregunta, opciones, multiple). Solo la
# pregunta de tipos de lectura admite varias respuestas; las demas describen
# un unico grado, frecuencia o logro y por tanto siguen siendo exclusivas.
assert all(len(pregunta) == 4 for pregunta in perfil.PREGUNTAS)
marcas_multiples = {clave: multiple
                    for clave, _, _, multiple in perfil.PREGUNTAS}
assert marcas_multiples == {
    "frecuencia": False,
    "lecturas": True,
    "diccionario": False,
    "series": False,
    "libro_completo": False,
    "comprension": False,
}

# Esta prueba evita que al editar una cita se salga silenciosamente del largo
# que permite leerla como parte de un cuestionario breve.
for fragmento in perfil.FRAGMENTOS:
    palabras = re.findall(r"[A-Za-z]+(?:[’'-][A-Za-z]+)*", fragmento["texto"])
    assert 40 <= len(palabras) <= 70, (fragmento["clave"], len(palabras))
    assert len(fragmento["opciones"]) == 5
    valores = [valor for _, valor in fragmento["opciones"]]
    assert all(mayor > menor for mayor, menor in zip(valores, valores[1:]))
    assert 0.0 <= valores[-1] < valores[0] <= 2.0

extremos_fragmentos = {
    fragmento["clave"]: (fragmento["opciones"][0][1],
                         fragmento["opciones"][-1][1])
    for fragmento in perfil.FRAGMENTOS
}
assert extremos_fragmentos == {
    "fragmento_facil": (0.8, 0.0),
    "fragmento_medio": (1.2, 0.0),
    "fragmento_dificil": (2.0, 0.0),
}

faciles = {
    clave: _respuesta_extrema(opciones, 0)
    for clave, _, opciones, _ in perfil.PREGUNTAS
}
dificiles = {
    clave: _respuesta_extrema(opciones, -1)
    for clave, _, opciones, _ in perfil.PREGUNTAS
}
for fragmento in perfil.FRAGMENTOS:
    # En las preguntas de opinion la primera opcion es la mas facil; en los
    # fragmentos la comprension mayor aparece primero.
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

# Una seleccion multiple vacia equivale a no haber respondido. Con una opcion
# conserva su valor y con varias toma la mas alta, no la media.
try:
    perfil.desde_cuestionario({"lecturas": []})
except ValueError as exc:
    assert "al menos una pregunta" in str(exc)
else:
    raise AssertionError("Una seleccion multiple vacia no debe puntuar")

assert perfil.desde_cuestionario({"lecturas": [], "frecuencia": 0.8}).nivel == 0.8
assert perfil.desde_cuestionario({"lecturas": [1.4]}).nivel == 1.4
assert perfil.desde_cuestionario({"lecturas": [0.4, 1.4, 1.0]}).nivel == 1.4

# La normalizacion de listas no altera el peso superior de los fragmentos.
mixto = perfil.desde_cuestionario({
    "lecturas": [0.4, 1.4],
    "fragmento_medio": 1.2,
})
assert mixto.nivel == 1.27, mixto.nivel

print(f"TODO OK: extremo fácil={nivel_facil:.3f}, extremo difícil={nivel_dificil:.3f}")
