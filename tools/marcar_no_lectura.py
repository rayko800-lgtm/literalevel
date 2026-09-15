"""Marca los textos libres que no son lectura en inglés. No se borran del CSV: se
excluyen al buscar y al recomendar, igual que los índices y catálogos de Gutenberg.

    python -X utf8 tools/marcar_no_lectura.py

Escribe `no_lectura_externo.csv` (id, motivo) junto a `catalogo_externo.csv`.
`app/catalogo.py` lo lee al cargar y lo suma a `_excluidos`. Así no cambia la huella del
CSV grande ni el `.npy` de sus embeddings.

POR QUÉ (diagnóstico de e6, 14 sep 2026)
Una lectora B1 buscó «amor» y los primeros resultados fueron:
- «edws», cuyo texto entero es «hrrr»;
- «Love story», con el título en inglés y el cuento en coreano;
- un cuento en hindi y otro en turco;
- «bumbumyj,jc».
Sin gancho ni texto real, el vector de búsqueda de esas filas es casi solo el de sus
temas («Children's stories; StoryWeaver reading level N»), y ese vector se parece a
cualquier consulta.

LAS DOS REGLAS, MEDIDAS SOBRE LOS 15.357 TEXTOS DEL 14 SEP
- Menos de MIN_DISTINTAS palabras distintas en alfabeto latino: texto vacío, de
  relleno o en otra escritura (coreano, hindi). Son 115.
- Menos del MIN_INGLES de sus palabras en el diccionario inglés de Kaikki: turco,
  italiano, zulú... Son 48 más.
Entre 0,6 y 0,7 quedan 35 textos que no se marcan: hay francés e italiano, pero también
cuentos ingleses con muchos nombres propios. El umbral es una decisión, no una ley.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))

import ficha  # noqa: E402

CSV_EXTERNO = RAIZ / "catalogo_externo.csv"
TEXTOS = RAIZ / "corpus_abierto.parquet"
DICCIONARIO = RAIZ / "kaikki_diccionario.db"
SALIDA = RAIZ / "no_lectura_externo.csv"

MIN_DISTINTAS = 10
MIN_INGLES = 0.6
_PALABRA = re.compile(r"[A-Za-z]+(?:'[a-z]+)?")


def motivo_no_lectura(texto: str, diccionario: set[str]) -> str | None:
    """Por qué un texto servido no es lectura en inglés, o None si lo es.
    `texto` es el de corpus_abierto.parquet: la atribución final no cuenta."""
    palabras = [w.lower() for w in _PALABRA.findall(ficha.para_medir(str(texto or "")))]
    distintas = len(set(palabras))
    if distintas < MIN_DISTINTAS:
        return f"menos de {MIN_DISTINTAS} palabras distintas en alfabeto latino ({distintas})"
    inglesas = sum(1 for w in palabras if w in diccionario) / len(palabras)
    if inglesas < MIN_INGLES:
        return f"solo el {inglesas * 100:.0f} % de sus palabras está en el diccionario inglés"
    return None


def cargar_diccionario(ruta: Path = DICCIONARIO) -> set[str]:
    with sqlite3.connect(ruta) as con:
        return {p.lower() for (p,) in con.execute("SELECT palabra FROM entradas") if p and " " not in p}


def main() -> None:
    import pandas as pd
    diccionario = cargar_diccionario()
    externo = pd.read_csv(CSV_EXTERNO, dtype=str)
    textos = pd.read_parquet(TEXTOS).set_index("id")["texto"]
    filas = []
    for pid, fuente in zip(externo["id"], externo["fuente"]):
        motivo = motivo_no_lectura(textos.get(pid, ""), diccionario)
        if motivo:
            filas.append({"id": pid, "fuente": fuente, "motivo": motivo})
    tabla = pd.DataFrame(filas, columns=["id", "fuente", "motivo"]).sort_values("id")
    tabla[["id", "motivo"]].to_csv(SALIDA, index=False, lineterminator="\n")
    tipo = tabla["motivo"].str.split(" ").str[:2].str.join(" ")
    print(f"{len(tabla)} de {len(externo)} textos libres fuera de buscar y recomendar -> {SALIDA.name}")
    print("por motivo:", tipo.value_counts().to_dict())
    print("por fuente:", tabla["fuente"].value_counts().to_dict())


if __name__ == "__main__":
    main()
