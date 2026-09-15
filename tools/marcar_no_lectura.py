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
La causa no era la que decía aquí («el vector es casi solo el de sus temas»). La
auditoría cruzada de e6 recalculó la huella del `.npy` externo (c0de66f8d3dfff21):
en los 15.357 textos libres `hook` y `huella_texto` estaban vacíos y los temas no se
indexan, así que el vector salía solo de «título. autor.». Un título como «edws» o
«Love story» no dice nada del texto que hay debajo, y nada lo contrarrestaba. Marcar
estos textos sigue haciendo falta aunque el vector lleve el texto: un cuento en coreano
o «hrrr» no es lectura en inglés para nadie.

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


# Anuncios subidos a StoryWeaver como si fueran cuentos (ronda 2 de 4e, 15 sep
# 2026): con el gancho visible salían en la tarjeta. Uno lleva un enlace con una
# llamada a visitarlo, o es poco más que el enlace.
_URL = re.compile(r"https?://\S+|\bwww\.[a-z0-9-]+\.[a-z]{2,}\S*", re.I)
_LLAMADA = re.compile(r"(?i)click (below|here)|to know (more|about)|buy this|watch the videos?|"
                      r"visit (our|us|the website)|for more (info|information|details)")
MAX_PALABRAS_ENLACE = 30
# Los que no llevan llamada, o ni siquiera enlace, pero son publicidad: revisados
# a mano el 15 sep 2026 sobre los textos libres con enlace o tono comercial. Un
# artículo SEO con el enlace dentro (SWV687758), agencias, cursos y un casino.
ANUNCIOS_REVISADOS = {
    "SWV687758", "SWV580747", "SWV625403", "SWV625495", "SWV628150", "SWV639823",
    "SWV643473", "SWV663506", "SWV676868", "SWV700851", "SWV700942",
}


# Solo en StoryWeaver, donde cualquiera sube un libro: Let's Read, African Storybook y
# VOA son colecciones editadas, y un enlace ahí es de la editorial («www.bilumbooks.com»
# en los libros de Bilum Books). Y un enlace institucional (.org, .int, .gov, .edu) no
# cuenta: la OMS o UNICEF citados en un cuento sobre el asma o sobre los derechos. La
# primera pasada del 15 sep 2026, sin estas dos condiciones, marcó 41 textos y 29 eran
# buenos (24 de Bilum Books).
_INSTITUCIONAL = re.compile(r"(?i)\.(org|int|gov|edu)(\.[a-z]{2})?$|\.(ac|edu|gov)\.[a-z]{2}$")


def _enlace_comercial(cuerpo: str) -> bool:
    for url in _URL.findall(cuerpo):
        host = re.sub(r"(?i)^(https?://)?(www\.)?", "", url).split("/")[0].split("?")[0]
        if not _INSTITUCIONAL.search(host.lower().rstrip(".,;:)!»\"'")):
            return True
    return False


def motivo_no_lectura(texto: str, diccionario: set[str], pid: str = "",
                      fuente: str = "storyweaver") -> str | None:
    """Por qué un texto servido no es lectura en inglés, o None si lo es.
    `texto` es el de corpus_abierto.parquet: la atribución final no cuenta."""
    if str(pid or "").strip().upper() in ANUNCIOS_REVISADOS:
        return "anuncio (revisado a mano)"
    cuerpo = ficha.para_medir(str(texto or ""))
    if fuente == "storyweaver" and _enlace_comercial(cuerpo) and (_LLAMADA.search(cuerpo) or len(_URL.sub(" ", cuerpo).split()) <= MAX_PALABRAS_ENLACE):
        return "anuncio o enlace comercial"
    palabras = [w.lower() for w in _PALABRA.findall(cuerpo)]
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
        motivo = motivo_no_lectura(textos.get(pid, ""), diccionario, pid, fuente)
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
