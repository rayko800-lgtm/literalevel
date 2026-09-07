"""Pruebas de humo: la logica de bloques y escala no necesita el modelo."""
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

libro = rd.cargar(r"C:/Users/laura/Downloads/dokumen.pub_notes-from-a-dead-house.epub")
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
