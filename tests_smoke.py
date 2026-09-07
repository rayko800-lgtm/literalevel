"""Pruebas de humo: la logica de bloques y escala no necesita el modelo."""
import os
import tempfile
from pathlib import Path
import sys, importlib.util, re
import numpy as np

sys.path.insert(0, "app")

def cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    # dataclass() resuelve anotaciones via sys.modules, asi que hay que
    # registrar el modulo ANTES de ejecutarlo.
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod

# scoring importa transformers solo dentro de Puntuador, asi que se puede
# cargar el modulo entero aunque torch aun se este instalando.
sc = cargar("scoring", "app/scoring.py")
rd = cargar("reader", "app/reader.py")

# Sin rutas clavadas a una maquina concreta: si no hay libro a mano, se genera
# uno. Estas pruebas tienen que correr en el ordenador del profesor tambien.
_LIBRO = os.environ.get("LITERALEVEL_LIBRO_PRUEBA") or next(
    (str(c) for c in (
        Path.home() / ".literalevel" / "libros" / "pg11.epub",
        Path.home() / "Downloads" / "dokumen.pub_notes-from-a-dead-house.epub",
    ) if c.exists()), None)
if _LIBRO is None:
    _LIBRO = str(Path(tempfile.mkdtemp()) / "libro.txt")
    _p = ("The prison stood at the edge of the fortress, right by the rampart. "
          "You could look at the world through the chinks in the fence, and "
          "the sentries paced up and down the wall by day and by night. ")
    Path(_LIBRO).write_text("CHAPTER I\n\n" + _p * 14, encoding="utf-8")
libro = rd.cargar(_LIBRO)
cap = max(libro.capitulos, key=lambda c: c.palabras)
print(f"libro    : {libro.titulo} — {libro.autor}")
print(f"capitulo : {cap.titulo[:45]} ({cap.palabras:,} palabras)")

ok, motivo = sc.continuous_prose(cap.texto)
print(f"prosa    : {ok} ({motivo})")

b = sc.fixed_blocks(cap.texto)
print(f"bloques  : {len(b)} (tope {sc.MAX_BLOCKS_PER_DOC}) — palabras: {[len(x.split()) for x in b]}")
assert len(b) <= sc.MAX_BLOCKS_PER_DOC, "excede el tope de bloques"
assert all(len(x.split()) == sc.BLOCK_WORDS for x in b), "bloque de tamano incorrecto"

print("\nescala interna -> publica:")
for y in (0, 1, 2, 3, 4, 5):
    p = sc.public_score(y)
    print(f"  {y}  ({sc.ANCHORS[y]})  ->  {p:.2f}  {sc.public_band(p):<11} ancla {sc.anchor_cefr(y)}")

print("\nrechazos esperados:")
for nombre, txt in [
    ("lista",       "- uno\n- dos\n- tres\n- cuatro\n- cinco\n- seis\n" * 40),
    ("muy corto",   "This is short. Only a few words here. Nothing more. Done."),
]:
    ok2, m2 = sc.continuous_prose(txt)
    print(f"  {nombre:<10} -> rechazado={not ok2} ({m2})")
    assert not ok2, f"{nombre} deberia rechazarse"

print("\nTODO OK")
