"""Pruebas de los corpus libres en el catalogo y en el lector.

Cubren el camino nuevo de la noche del 12 de septiembre de 2026: los textos de
StoryWeaver, African Storybook, VOA y Let's Read que entran al catalogo
(`tools/catalogar_corpus.py`) y se abren en la aplicacion sin descargar nada.

Van en archivo propio y no en `pruebas_extremas.py` porque otra sesion estaba
editando esa suite a la vez; el formato de salida es el mismo que entiende
`tools/banco_mutantes.py` ("FALLA <nombre>" y el titular final).

Uso:  python -X utf8 pruebas_corpus.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import traceback
from pathlib import Path

# Carpetas temporales que se borran al salir, bajo LITERALEVEL_TMP si está definida
# (el helper común de 4e, 42de4cb). Sin borrarlas, cada corrida dejaba unos 100 MB en
# %TEMP% -la caché de embeddings del catálogo cae aquí- y con el banco se juntaron
# miles de carpetas: C: se quedó a 0 GB el 15 sep 2026.
import pruebas_tmp

sys.path.insert(0, "app")
os.environ["LITERALEVEL_DATOS"] = pruebas_tmp.carpeta("literalevel_corpus_")
import config as config_mod  # noqa: E402
config_mod.cargar = lambda *a, **k: None
os.environ.pop("OPENAI_API_KEY", None)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import catalogo as cm  # noqa: E402
import ui  # noqa: E402

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


class _Codificador:
    """Sustituye al MiniLM: vectores deterministas sin cargar ningun modelo."""
    def __init__(self):
        self.llamadas = []

    def encode(self, textos, **kw):
        self.llamadas.append(len(textos))
        return np.array([[float(len(t) % 97), float(i), 1.0] for i, t in enumerate(textos)],
                        dtype=np.float32)


def _montar(carpeta: Path, con_externo=True):
    """Un catalogo medido de 3 libros de Gutenberg y, al lado, 2 externos."""
    pd.DataFrame({
        "id": ["PG1", "PG2", "PG3"], "title": ["Uno", "Dos", "Tres"],
        "author": ["a", "b", "c"], "hook": ["", "", ""], "huella_texto": ["", "", ""],
        "nivel_cefr": ["", "", ""], "downloads": [30, 20, 10], "dificultad": [1.5, 1.6, 1.7],
        "palabras": [9000, 9000, 9000], "ventanas": [36, 36, 36], "capitulos": [3, 3, 3],
        "temas": ["Fiction", "Fiction", "Fiction"],
    }).to_csv(carpeta / "catalogo_medido.csv", index=False)
    if con_externo:
        pd.DataFrame({
            "id": ["SWV369", "ASB0141", "PG2"], "title": ["The Red Raincoat", "Chicken", "Duplicado"],
            "author": ["Kiran Kasturia", "", "x"], "hook": ["", "", ""], "huella_texto": ["", "", ""],
            "nivel_cefr": ["A2", "A2", "C1"], "downloads": [0, 0, 0], "dificultad": [0.36, 0.5, 1.6],
            "palabras": [437, 268, 1], "ventanas": [2, 2, 1], "capitulos": [1, 1, 1],
            "temas": ["Children's stories; StoryWeaver reading level 1",
                      "Children's stories; African Storybook reading level 1", "x"],
            "fuente": ["storyweaver", "african_storybook", "storyweaver"],
            "licencia": ["CC BY 4.0", "CC-BY", "CC BY 4.0"],
            "atribucion": ["«The Red Raincoat» CC BY 4.0", "«Chicken» CC BY", "x"],
            "url": ["https://storyweaver.org.in/x", "https://www.africanstorybook.org/", ""],
            "nivel_editor": ["1", "1", "1"], "medida": ["texto", "texto", "texto"],
        }).to_csv(carpeta / "catalogo_externo.csv", index=False)
        pd.DataFrame({
            "id": ["SWV369", "ASB0141"], "title": ["The Red Raincoat", "Chicken"],
            "author": ["Kiran Kasturia", ""], "licencia": ["CC BY 4.0", "CC-BY"],
            "atribucion": ["«The Red Raincoat» CC BY 4.0", "«Chicken» CC BY"],
            "url": ["https://storyweaver.org.in/x", ""],
            "texto": ["On Sunday, Manu's parents got him a red raincoat. " * 40
                      + "\n\n«The Red Raincoat» CC BY 4.0",
                      "Chicken and Millipede were friends. " * 40 + "\n\n«Chicken» CC BY"],
        }).to_parquet(carpeta / "corpus_abierto.parquet", index=False)
    return cm.Catalogo(carpeta / "catalogo_medido.csv")


def _nuevo():
    return Path(pruebas_tmp.carpeta("corpus_"))


# --- 1. El catalogo -----------------------------------------------------------
print("\nCatalogo con corpus externos")


def _externos_al_final_sin_duplicar():
    cat = _montar(_nuevo())
    ids = cat.df["id"].astype(str).tolist()
    assert ids[:3] == ["PG1", "PG2", "PG3"], f"los de Gutenberg no van primero: {ids}"
    assert ids[3:] == ["SWV369", "ASB0141"], f"externos mal anadidos: {ids}"
    assert ids.count("PG2") == 1, "un id del externo que ya estaba en el medido se duplico"
    assert cat._n_propio == 3
    return f"{len(ids)} filas, {cat._n_propio} propias"


prueba("los externos van al final y no duplican ids", _externos_al_final_sin_duplicar)


def _sin_externo_arranca_igual():
    cat = _montar(_nuevo(), con_externo=False)
    assert len(cat.df) == 3 and cat.ruta_externo is None
    assert not cat.es_abrible("SWV369")
    assert cat.texto_abierto("SWV369") is None
    return "sin archivos externos, 3 filas y nada abrible fuera de Gutenberg"


prueba("sin catalogo externo todo sigue como antes", _sin_externo_arranca_igual)


def _embeddings_alineados_y_separados():
    carpeta = _nuevo()
    cache = carpeta / "cache"
    viejo = cm.DIR_CACHE
    cm.DIR_CACHE = cache
    try:
        cat = _montar(carpeta)
        cod = _Codificador()
        cat._modelo_emb = lambda: cod
        emb = cat.embeddings
        assert emb.shape[0] == len(cat.df), f"{emb.shape[0]} vectores para {len(cat.df)} filas"
        assert cod.llamadas == [3, 2], f"no codifica por separado propio y externo: {cod.llamadas}"
        propios = sorted(p.name for p in cache.glob("catalogo_emb_*.npy") if "_ext_" not in p.name)
        externos = sorted(p.name for p in cache.glob("catalogo_emb_ext_*.npy"))
        assert propios and externos, f"falta un archivo de embeddings: {propios} {externos}"
        # Un catalogo nuevo con el MISMO medido y otro externo: recodifica
        # solo el externo y NO borra los embeddings de Gutenberg.
        pd.read_csv(carpeta / "catalogo_externo.csv").head(1).to_csv(
            carpeta / "catalogo_externo.csv", index=False)
        cat2 = cm.Catalogo(carpeta / "catalogo_medido.csv")
        cod2 = _Codificador()
        cat2._modelo_emb = lambda: cod2
        emb2 = cat2.embeddings
        assert cod2.llamadas == [1], f"recodifico Gutenberg al cambiar el externo: {cod2.llamadas}"
        assert emb2.shape[0] == len(cat2.df)
        siguen = [p.name for p in cache.glob("catalogo_emb_*.npy") if "_ext_" not in p.name]
        assert siguen == propios, f"guardar el externo borro los de Gutenberg: {siguen}"
        # Y al reves: cambiar el catalogo de Gutenberg lo recodifica, y su
        # limpieza de versiones viejas no puede llevarse los del externo.
        ext_antes = sorted(p.name for p in cache.glob("catalogo_emb_ext_*.npy"))
        medido = pd.read_csv(carpeta / "catalogo_medido.csv")
        medido.loc[0, "title"] = "Uno, segunda edicion"
        medido.to_csv(carpeta / "catalogo_medido.csv", index=False)
        cat3 = cm.Catalogo(carpeta / "catalogo_medido.csv")
        cod3 = _Codificador()
        cat3._modelo_emb = lambda: cod3
        cat3.embeddings
        assert cod3.llamadas == [3], f"cambiar Gutenberg no recodifico solo Gutenberg: {cod3.llamadas}"
        ext_despues = sorted(p.name for p in cache.glob("catalogo_emb_ext_*.npy"))
        assert ext_despues == ext_antes, f"recalcular Gutenberg borro los del externo: {ext_antes} -> {ext_despues}"
    finally:
        cm.DIR_CACHE = viejo
    return "propio y externo en archivos distintos; cambiar el externo no toca Gutenberg"


prueba("embeddings alineados, y el externo no borra los de Gutenberg", _embeddings_alineados_y_separados)


def _cache_externa_por_filas_efectivas():
    """El caso de la auditoria de Codex: el MISMO externo [X1, X2, X3] con dos
    principales distintos deja filas distintas de la MISMA longitud. La cache
    no puede darle a X1 el vector de X2."""
    carpeta = _nuevo()
    viejo = cm.DIR_CACHE
    cm.DIR_CACHE = carpeta / "cache"
    try:
        def principal(id_repetido):
            pd.DataFrame({
                "id": ["PG1", id_repetido], "title": ["Uno", "Repetido"], "author": ["a", "b"],
                "hook": ["", ""], "huella_texto": ["", ""], "nivel_cefr": ["", ""],
                "downloads": [1, 1], "dificultad": [1.5, 1.5], "temas": ["Fiction", "Fiction"],
            }).to_csv(carpeta / "catalogo_medido.csv", index=False)

        pd.DataFrame({
            "id": ["X1", "X2", "X3"],
            "title": ["Uno corto", "Dos con un titulo bastante mas largo", "Tres medio largo"],
            "author": ["", "", ""], "hook": ["", "", ""], "huella_texto": ["", "", ""],
            "nivel_cefr": ["A2", "A2", "A2"], "downloads": [0, 0, 0], "dificultad": [0.4, 0.4, 0.4],
            "temas": ["Children's stories"] * 3, "licencia": ["CC BY 4.0"] * 3,
        }).to_csv(carpeta / "catalogo_externo.csv", index=False)

        principal("X1")
        cat1 = cm.Catalogo(carpeta / "catalogo_medido.csv")
        cat1._modelo_emb = lambda: _Codificador()
        cat1.embeddings
        principal("X2")
        cat2 = cm.Catalogo(carpeta / "catalogo_medido.csv")
        cod = _Codificador()
        cat2._modelo_emb = lambda: cod
        emb = cat2.embeddings
        ids = cat2.df["id"].astype(str).tolist()
        assert ids[2:] == ["X1", "X3"], ids
        esperado = _Codificador().encode(cat2._texto_indexable()[2:])
        assert np.allclose(emb[2:], esperado), (
            f"el externo reutilizo vectores de otras filas: {emb[2:, 0]} vs {esperado[:, 0]}")
    finally:
        cm.DIR_CACHE = viejo
    return "otro principal con la misma longitud de externo recodifica, no reutiliza"


prueba("la cache del externo depende de sus filas efectivas", _cache_externa_por_filas_efectivas)


def _abribles():
    cat = _montar(_nuevo())
    assert cat.es_abrible("PG1342") and cat.es_abrible("swv369")
    assert not cat.es_abrible("SWgdlgdl42"), "un StoryWeaver heredado sin texto sale abrible"
    assert not cat.es_abrible("PG"), "un id sin numero sale abrible"
    t = cat.texto_abierto("SWV369")
    assert t and t["licencia"] == "CC BY 4.0" and "CC BY 4.0" in t["texto"][-60:], t
    return "Gutenberg y corpus libres si; heredado sin texto e id vacio no"


prueba("que se puede abrir y que no", _abribles)


def _indices_enlazados_fuera_de_nivel():
    """Prueba final del 13 sep 2026: el indice enlazado de Andrew Lang, con temas
    literarios, salia recomendado a un B1. Un libro real con indice al final no."""
    carpeta = _nuevo()
    pd.DataFrame({
        "id": ["PG30580", "PG46752", "PG57485", "PG11"],
        "title": ["The Fairy Books of Andrew Lang A Project Gutenberg Linked Index to All Stories in the 12 Volumes",
                  "History of the Jews, Vol. 6 (of 6) Containing a Memoir of the Author and an Index to the Complete Work",
                  "Index for Works of Andrew Barton 'Banjo' Paterson Hyperlinks to all Chapters of all Individual Ebooks",
                  "Alice's Adventures in Wonderland"],
        "author": ["Lang", "Graetz", "Paterson", "Carroll"], "hook": ["", "", "", ""],
        "huella_texto": ["", "", "", ""], "nivel_cefr": ["", "", "", ""],
        "downloads": [900, 800, 700, 600], "dificultad": [0.60, 0.62, 0.61, 0.63],
        "palabras": [6189, 183791, 184, 26426], "ventanas": [24, 700, 1, 100], "capitulos": [1, 1, 1, 12],
        "temas": ["Fairy tales; Folklore", "Jews -- History; Fiction", "Poetry", "Fantasy fiction"],
    }).to_csv(carpeta / "catalogo_medido.csv", index=False)
    cat = cm.Catalogo(carpeta / "catalogo_medido.csv")
    excl = dict(zip(cat.df["id"].astype(str), cat._excluidos))
    assert excl["PG30580"], "el indice enlazado de Andrew Lang no se excluye"
    assert excl["PG57485"], "un «Index for Works of … Hyperlinks to all Chapters» no se excluye"
    assert not excl["PG46752"], "un libro real con «an Index to the Complete Work» se excluye"
    assert not excl["PG11"], "Alice se excluye"
    ids = [l.id for l in cat.por_nivel(0.61, holgura=0.25, n=10)]
    assert "PG30580" not in ids and "PG57485" not in ids, f"se recomiendan indices: {ids}"
    assert "PG46752" in ids and "PG11" in ids, f"faltan libros de verdad: {ids}"
    return f"por nivel: {ids}"


prueba("los indices enlazados de Gutenberg no se recomiendan por nivel", _indices_enlazados_fuera_de_nivel)


def _catalogo_de_nivel(carpeta: Path, n: int = 8):
    """n libros literarios en la misma franja, del mas al menos descargado."""
    ids = [f"PG{100 + i}" for i in range(n)]
    pd.DataFrame({
        "id": ids, "title": [f"Libro {i}" for i in range(n)], "author": ["a"] * n,
        "hook": [""] * n, "huella_texto": [""] * n, "nivel_cefr": [""] * n,
        "downloads": [1000 - i for i in range(n)], "dificultad": [0.7] * n,
        "palabras": [9000] * n, "ventanas": [36] * n, "capitulos": [1] * n,
        "temas": ["Fiction"] * n,
    }).to_csv(carpeta / "catalogo_medido.csv", index=False)
    return ids


def _aviso_no_encabeza_ni_desaparece():
    """Regla del proyecto: no se filtra por contenido, se avisa. Un titulo con
    aviso sigue saliendo, pero no en los primeros puestos por nivel."""
    carpeta = _nuevo()
    ids = _catalogo_de_nivel(carpeta)
    pd.DataFrame({"id": [ids[0], "PG999999"], "motivo": ["prueba", "no esta"],
                  "nota_es": ["Obra con estereotipos de su época.", "x"]}).to_csv(
        carpeta / "avisos_contenido.csv", index=False)
    cat = cm.Catalogo(carpeta / "catalogo_medido.csv")
    libros = cat.por_nivel(0.7, holgura=0.25, n=8)
    orden = [l.id for l in libros]
    assert ids[0] in orden, f"el titulo con aviso desaparecio: {orden}"
    pos = orden.index(ids[0])
    assert pos >= cm.PRIMEROS_SIN_AVISO, f"el titulo con aviso sigue en el puesto {pos + 1}: {orden}"
    assert orden[:cm.PRIMEROS_SIN_AVISO] == ids[1:1 + cm.PRIMEROS_SIN_AVISO], f"el resto cambio de orden: {orden}"
    con = next(l for l in libros if l.id == ids[0])
    assert con.aviso_contenido.startswith("Obra con estereotipos"), con
    assert all(not l.aviso_contenido for l in libros if l.id != ids[0])
    assert cat.aviso_de(ids[0].lower()) and cat.aviso_de(ids[1]) is None
    # Sin archivo de avisos, el orden es el de siempre.
    carpeta2 = _nuevo()
    _catalogo_de_nivel(carpeta2)
    sin = [l.id for l in cm.Catalogo(carpeta2 / "catalogo_medido.csv").por_nivel(0.7, holgura=0.25, n=8)]
    assert sin == ids, f"sin avisos el orden cambia: {sin}"
    return f"con aviso en el puesto {pos + 1} de {len(orden)}"


prueba("un titulo con aviso de contenido no encabeza pero sigue saliendo", _aviso_no_encabeza_ni_desaparece)


def _libres_intercalados_por_nivel():
    """Decision de Miguel, 14 sep 2026: los cuentos libres no tienen descargas de
    Gutenberg y por popularidad no salian nunca arriba. Si hay libres en la
    franja, ocupan los puestos 2, 5, 8...; el resto sigue por descargas."""
    carpeta = _nuevo()
    pg = [f"PG{100 + i}" for i in range(12)]
    sw = [f"SWV{i}" for i in range(1, 7)]
    pd.DataFrame({
        "id": pg + ["PG900", "PG901"], "title": [f"Libro {i}" for i in range(14)], "author": ["a"] * 14,
        "hook": [""] * 14, "huella_texto": [""] * 14, "nivel_cefr": [""] * 14,
        "downloads": [1000 - i for i in range(12)] + [500, 400], "dificultad": [0.4] * 12 + [1.6, 1.6],
        "palabras": [9000] * 14, "ventanas": [36] * 14, "capitulos": [1] * 14, "temas": ["Fiction"] * 14,
    }).to_csv(carpeta / "catalogo_medido.csv", index=False)
    externos = sw + ["SWV9"]                      # SWV9 sin texto: no se abre, no es libre
    pd.DataFrame({
        "id": externos, "title": [f"Cuento {x}" for x in externos], "author": [""] * 7,
        "hook": [""] * 7, "huella_texto": [""] * 7, "nivel_cefr": ["A2"] * 7, "downloads": [0] * 7,
        "dificultad": [0.4] * 7, "palabras": [400] * 7, "ventanas": [2] * 7, "capitulos": [1] * 7,
        "temas": ["Children's stories; StoryWeaver reading level 1"] * 7, "fuente": ["storyweaver"] * 7,
        "licencia": ["CC BY 4.0"] * 7, "atribucion": ["x"] * 7, "url": [""] * 7,
        "nivel_editor": ["1"] * 7, "medida": ["texto"] * 7,
    }).to_csv(carpeta / "catalogo_externo.csv", index=False)
    pd.DataFrame({"id": sw, "title": sw, "author": [""] * 6, "licencia": ["CC BY 4.0"] * 6,
                  "atribucion": ["x"] * 6, "url": [""] * 6,
                  "texto": ["Manu got a red raincoat. " * 40] * 6}).to_parquet(
        carpeta / "corpus_abierto.parquet", index=False)
    pd.DataFrame({"id": ["SWV1"], "motivo": ["prueba"], "nota_es": ["Cuento con aviso."]}).to_csv(
        carpeta / "avisos_contenido.csv", index=False)
    cat = cm.Catalogo(carpeta / "catalogo_medido.csv")

    orden = [l.id for l in cat.por_nivel(0.4, holgura=0.25, n=9)]
    # Puestos 2, 5 y 8 para los libres. SWV1 lleva aviso: no entra en los 5
    # primeros, asi que el 2 y el 5 son SWV2 y SWV3, y SWV1 espera al 8.
    esperado = ["PG100", "SWV2", "PG101", "PG102", "SWV3", "PG103", "PG104", "SWV1", "PG105"]
    assert orden == esperado, f"intercalado mal: {orden}"

    todos = [l.id for l in cat.por_nivel(0.4, holgura=0.25, n=30)]
    assert sorted(todos) == sorted(pg + externos), f"se pierde o se repite alguno: {todos}"
    assert "SWV9" not in todos[:len(sw) * 3], f"un cuento sin texto ocupa un hueco de libre: {todos}"
    assert [x for x in todos if x.startswith("PG")] == pg, f"los de Gutenberg cambian de orden: {todos}"

    sin_libres = [l.id for l in cat.por_nivel(1.6, holgura=0.1, n=10)]
    assert sin_libres == ["PG900", "PG901"], f"sin libres en la franja el orden cambia: {sin_libres}"
    return f"por nivel: {orden}"


prueba("los textos libres se intercalan en los primeros puestos por nivel", _libres_intercalados_por_nivel)


def _libres_en_sorprendeme_del_catalogo_real():
    """Lo que ve un lector A2 o B1 en «Sorprendeme» con el catalogo de verdad:
    un tercio de las 30 tarjetas son libres, y al menos 3 en las 9 primeras."""
    raiz = Path(__file__).resolve().parent
    necesarios = [raiz / "catalogo_medido.csv", raiz / "catalogo_externo.csv", raiz / cm.NOMBRE_TEXTOS_ABIERTOS]
    if not all(p.exists() for p in necesarios):
        return "sin el catalogo real en esta carpeta, no se puede medir"
    cat = cm.Catalogo(raiz / "catalogo_medido.csv")
    cifras = []
    for nombre, nivel in (("A2", 0.4), ("B1", 0.8)):
        libros = cat.por_nivel(nivel, holgura=ui.HOLGURA_POR_NIVEL, n=30)
        libres = [i for i, b in enumerate(libros) if not b.id.upper().startswith("PG") and cat.es_abrible(b.id)]
        arriba = sum(1 for i in libres if i < 9)
        assert len(libros) == 30, f"{nombre}: {len(libros)} tarjetas"
        assert len(libres) >= 10, f"{nombre}: {len(libres)} libres entre 30"
        assert arriba >= 3, f"{nombre}: {arriba} libres entre las 9 primeras"
        assert not any(b.aviso_contenido for b in libros[:cm.PRIMEROS_SIN_AVISO]), f"{nombre}: aviso arriba"
        cifras.append(f"{nombre} {len(libres)} de 30, {arriba} en las 9 primeras")
    return "; ".join(cifras)


prueba("sorprendeme ofrece textos libres a A2 y B1 con el catalogo real", _libres_en_sorprendeme_del_catalogo_real)


def _libres_por_cercania_y_solos_antes():
    """Prueba como persona del 14 sep 2026: los libres empataban a 0 descargas y
    salian por id, y A2 y B1 veian los mismos tres cuentos del borde. Primero el
    mas cercano al nivel; a igual distancia, el medido solo antes que el de bloque.
    Y la marca de bloque llega a `Libro` y a `medida_de`."""
    carpeta = _nuevo()
    pg = [f"PG{100 + i}" for i in range(9)]
    pd.DataFrame({
        "id": pg, "title": [f"Libro {i}" for i in range(9)], "author": ["a"] * 9,
        "hook": [""] * 9, "huella_texto": [""] * 9, "nivel_cefr": [""] * 9,
        "downloads": [1000 - i for i in range(9)], "dificultad": [0.5] * 9,
        "palabras": [9000] * 9, "ventanas": [36] * 9, "capitulos": [1] * 9, "temas": ["Fiction"] * 9,
    }).to_csv(carpeta / "catalogo_medido.csv", index=False)
    # Por id irian SWV1, SWV2, SWV3, SWV4. Por cercania a 0,5: SWV4 (0,50),
    # luego SWV2 y SWV3 a 0,10 (SWV3 medido solo antes que SWV2 de bloque), y SWV1.
    sw = ["SWV1", "SWV2", "SWV3", "SWV4"]
    pd.DataFrame({
        "id": sw, "title": sw, "author": [""] * 4, "hook": [""] * 4, "huella_texto": [""] * 4,
        "nivel_cefr": ["A2"] * 4, "downloads": [0] * 4, "dificultad": [0.26, 0.60, 0.40, 0.50],
        "palabras": [400] * 4, "ventanas": [2] * 4, "capitulos": [1] * 4,
        "temas": ["Children's stories; StoryWeaver reading level 1"] * 4, "fuente": ["storyweaver"] * 4,
        "licencia": ["CC BY 4.0"] * 4, "atribucion": ["x"] * 4, "url": [""] * 4,
        "nivel_editor": ["1"] * 4, "medida": ["texto", "bloque", "texto", "texto"],
    }).to_csv(carpeta / "catalogo_externo.csv", index=False)
    pd.DataFrame({"id": sw, "title": sw, "author": [""] * 4, "licencia": ["CC BY 4.0"] * 4,
                  "atribucion": ["x"] * 4, "url": [""] * 4,
                  "texto": ["Manu got a red raincoat. " * 40] * 4}).to_parquet(
        carpeta / "corpus_abierto.parquet", index=False)
    cat = cm.Catalogo(carpeta / "catalogo_medido.csv")
    libros = cat.por_nivel(0.5, holgura=0.25, n=12)
    orden = [l.id for l in libros]
    esperado = ["PG100", "SWV4", "PG101", "PG102", "SWV3", "PG103", "PG104", "SWV2", "PG105",
                "PG106", "SWV1", "PG107"]
    assert orden == esperado, f"libres mal ordenados: {orden}"
    marca = {l.id: l.medido_en_bloque for l in libros}
    assert marca["SWV2"] and not marca["SWV3"] and not marca["PG100"], marca
    assert cat.medida_de("swv2") == "bloque" and cat.medida_de("SWV3") == "texto", "medida_de"
    assert cat.medida_de("PG100") == "" and cat.medida_de("NO") == "", "medida_de en Gutenberg"
    return f"por nivel: {orden[:9]}"


prueba("los libres van por cercania al nivel y los medidos solos antes que los de bloque",
       _libres_por_cercania_y_solos_antes)


def _atribucion_fuera_al_medir():
    """La atribucion de un texto libre se ensena, pero no se puntua: «Doggie is
    Happy» daba 0,349 con ella y 0,007 sin ella (catalogo: 0,007)."""
    import ficha
    cuerpo = "Parul saw that the doggie had not eaten.\n\nShe asked the doggie again."
    atribuciones = [
        "«Doggie is Happy» de Anitha Selvanathan, publicado en StoryWeaver (StoryWeaver Community) "
        "con licencia CC BY 4.0: https://storyweaver.org.in/en/stories/229485-doggie-is-happy",
        "«Chicken», African Storybook Project, licencia CC BY (texto de global-asp/asp-source): "
        "https://www.africanstorybook.org/",
        "«A Tale» de X, ilustrado por Y, Let's Read (The Asia Foundation), licencia CC BY 4.0: https://x",
        "«News», VOA Learning English, dominio publico. Credito: voanews.com / Voice of America. https://x",
    ]
    for a in atribuciones:
        texto = cuerpo + "\n\n" + a
        assert ficha.para_medir(texto) == cuerpo, f"no quita: {a[:40]}"
        assert ficha.sin_licencia(texto) == texto, "sin_licencia no debe quitarla: el lector la ensena"
        # Un texto sin cuerpo: el servido es "\n\n" + atribucion (SWV137935).
        assert ficha.para_medir("\n\n" + a) == "", f"sin cuerpo, la atribucion se queda como texto: {a[:40]}"
    # Lo que no es la atribucion final se queda.
    cita = cuerpo + "\n\n«Run!» she said, and StoryWeaver was never mentioned again in the tale."
    assert ficha.para_medir(cita + "\n\nThe end.") == cita + "\n\nThe end.", "se come un parrafo que no es el ultimo"
    gut = "CHAPTER I\n\n«Yes», said Holmes, turning to the window."
    assert ficha.para_medir(gut) == gut, "toca un parrafo con comillas sin biblioteca"
    raiz = Path(__file__).resolve().parent
    if not ((raiz / cm.NOMBRE_TEXTOS_ABIERTOS).exists() and (raiz / "modelo_v4").is_dir()):
        return "sin el parquet o el modelo aqui: solo las formas"
    import scoring
    t = pd.read_parquet(raiz / cm.NOMBRE_TEXTOS_ABIERTOS).set_index("id").loc["SWV229485", "texto"]
    p = scoring.Puntuador(str(raiz / "modelo_v4"))
    con = p.puntuar(ficha.sin_licencia(t)).puntuacion
    sin = p.puntuar(ficha.para_medir(t)).puntuacion
    assert sin < 0.1 < con, f"Doggie is Happy: con atribucion {con:.3f}, para_medir {sin:.3f}"
    return f"Doggie is Happy: {con:.3f} con la atribucion, {sin:.3f} sin ella"


prueba("la atribucion de un texto libre no se mide con el cuento", _atribucion_fuera_al_medir)


def _texto_servido_limpio_sin_tocar_lo_medido():
    """Punto 4 de la prueba como persona (14 sep 2026): sin U+FEFF, sin parrafos
    repetidos seguidos ni paginas duplicadas en un parrafo; el estribillo y la
    repeticion no consecutiva se quedan; y lo que se mide no cambia."""
    spec = importlib.util.spec_from_file_location("catalogar_corpus", "tools/catalogar_corpus.py")
    cc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cc)
    pagina = "Today is Monday. It is Anie's first online class today. Mother said waking her up now."
    assert cc.limpiar_para_servir("﻿Hola.\n\nAdios.") == "Hola.\n\nAdios.", "U+FEFF"
    assert cc.limpiar_para_servir(f"{pagina}\n\n{pagina}\n\nFin.") == f"{pagina}\n\nFin.", "parrafo repetido seguido"
    assert cc.limpiar_para_servir(f"{pagina} {pagina}") == pagina, "pagina duplicada dentro del parrafo"
    # Doce palabras o mas por mitad, pero UNA frase: es del cuento, se queda.
    medio = "Run, run, as fast as you can, you cannot catch me, I am the Gingerbread Man!"
    estribillo = f"{medio} {medio}"
    assert cc.limpiar_para_servir(estribillo) == estribillo, "se come un estribillo de una frase"
    lejos = f"{pagina}\n\nOtra cosa.\n\n{pagina}"
    assert cc.limpiar_para_servir(lejos) == lejos, "se come una repeticion no consecutiva"
    df = pd.DataFrame({"id": ["SWV1"], "title": ["t"], "author": ["a"], "licencia": ["CC BY 4.0"],
                       "atribucion": ["«t», StoryWeaver"], "url": [""], "texto": [f"﻿{pagina}\n\n{pagina}"]})
    servido = cc.textos_para_servir(df)
    assert servido.loc[0, "texto"] == f"{pagina}\n\n«t», StoryWeaver", servido.loc[0, "texto"]
    assert df.loc[0, "texto"] == f"﻿{pagina}\n\n{pagina}", "textos_para_servir cambio el texto que se mide"
    return "U+FEFF, parrafo y pagina dobles fuera; estribillo y repeticion lejana dentro"


prueba("el texto servido sale limpio sin tocar el que se mide", _texto_servido_limpio_sin_tocar_lo_medido)


def _textos_que_no_son_lectura_fuera():
    """Diagnostico de e6 (14 sep 2026): buscando «amor» con perfil B1 salian
    primero «edws» (texto: «hrrr»), cuentos en coreano o turco y «bumbumyj,jc».
    Se marcan y se excluyen al buscar y recomendar, sin borrarlos del CSV."""
    spec = importlib.util.spec_from_file_location("marcar_no_lectura", "tools/marcar_no_lectura.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    dic = {"the", "girl", "went", "to", "school", "and", "her", "mother", "made", "lunch", "she",
           "was", "happy", "after", "they", "home", "for", "dinner", "played", "with", "friends"}
    ingles = ("The girl went to school and her mother made lunch. She was happy. After school "
              "they went home for dinner and she played with her friends.")
    atribucion = "\n\n«The Girl» de X, publicado en StoryWeaver (X) con licencia CC BY 4.0: https://x"
    assert mod.motivo_no_lectura(ingles + atribucion, dic) is None, "marca un cuento ingles"
    assert "distintas" in (mod.motivo_no_lectura("hrrr" + atribucion, dic) or ""), "no marca «hrrr»"
    coreano = "한 남자아이와 여자아이가 비행기가 고장나서 정글에 불시착을 했어요. 그런데 호랑이가 나타나서"
    assert "distintas" in (mod.motivo_no_lectura(coreano, dic) or ""), "no marca un cuento en coreano"
    turco = ("Anne Ben Hasta Elif konusmayi ve okumayi seven oldukca hareketli bir cocuktu Elif hasta "
             "oldugundan dolayi birkac gun okula gidememisti the girl")
    assert "diccionario" in (mod.motivo_no_lectura(turco, dic) or ""), "no marca un cuento en turco"

    carpeta = _nuevo()
    _montar(carpeta)
    pd.DataFrame({"id": ["ASB0141"], "motivo": ["prueba"]}).to_csv(carpeta / "no_lectura_externo.csv", index=False)
    cat = cm.Catalogo(carpeta / "catalogo_medido.csv")
    excl = dict(zip(cat.df["id"].astype(str), cat._excluidos))
    assert excl["ASB0141"] and not excl["SWV369"], f"exclusion mal aplicada: {excl}"
    ids = [l.id for l in cat.por_nivel(0.45, holgura=0.2, n=10)]
    assert "ASB0141" not in ids and "SWV369" in ids, f"por nivel: {ids}"
    assert "ASB0141" in set(cat.df["id"].astype(str)), "se borro del catalogo en vez de excluirse"
    return "hrrr, coreano y turco marcados; el cuento ingles no; ASB0141 fuera de por nivel y dentro del CSV"


prueba("los textos que no son lectura en ingles no salen al buscar ni al recomendar",
       _textos_que_no_son_lectura_fuera)


def _busqueda_relevancia_antes_que_nivel():
    """Diagnostico de e6 (14 sep 2026): con «Ordenar por mi nivel» el nivel pesaba
    mas que el tema, y «A Midsummer Night's Dream» buscado por titulo solo salia
    sin el ajuste. El titulo gana siempre; el nivel ordena dentro de lo relevante."""
    # El titulo exacto con un parecido por tema realista: en el catalogo real,
    # «A Midsummer Night's Dream» da 0,77, el mejor de todos. Con 0,20 frente a 0,85
    # es un nombre que no tiene que ver con lo pedido, y desde el 15 sep ese no
    # rescata (MARGEN_SEMANTICO_NOMBRE; lo prueba _nombre_parecido_sin_tema_no_rescata).
    s = [0.70, 0.85, 0.84, 0.70]          # parecido por tema de cada fila con la consulta
    emb = np.array([[x, (1 - x * x) ** 0.5] for x in s], dtype=np.float32)
    df = pd.DataFrame({
        "id": ["PG1", "PG2", "PG3", "PG4"],
        "title": ["A Midsummer Night's Dream", "Relevante lejos", "Relevante cerca", "Irrelevante a mi nivel"],
        "author": ["Shakespeare, William", "Uno, Autor", "Dos, Autor", "Tres, Autor"],
        "nivel_cefr": ["C1", "C1", "B2", "B1"], "hook": [""] * 4, "downloads": [1] * 4,
        "dificultad": [1.7, 1.7, 1.6, 0.95]})
    cat = object.__new__(cm.Catalogo)
    cat.df = df
    cat._emb = emb
    cat._fichas = None
    cat._modelo_emb = lambda: type("M", (), {"encode": staticmethod(
        lambda x, **k: np.array([[1.0, 0.0]], dtype=np.float32))})()
    con = [l.id for l in cat.buscar("A Midsummer Night's Dream", nivel_lector=0.95, n=4)[0]]
    assert con[0] == "PG1", f"el titulo exacto no gana con el ajuste de nivel: {con}"
    assert con == ["PG1", "PG3", "PG2", "PG4"], f"el nivel adelanta lo irrelevante o no ordena lo relevante: {con}"
    sin = [l.id for l in cat.buscar("A Midsummer Night's Dream", n=4)[0]]
    assert sin == ["PG1", "PG2", "PG3", "PG4"], f"sin ajuste cambia el orden por parecido: {sin}"
    return f"con nivel {con}; sin nivel {sin}"


prueba("al buscar, el titulo gana y el nivel solo ordena lo relevante", _busqueda_relevancia_antes_que_nivel)


def _buscar_llena_n_con_excluidos_delante():
    """Auditoria cruzada de e6 (M1): `buscar` solo miraba `orden[:n * 3]`. Con mas
    de 2n excluidos en esos puestos devolvia menos de n habiendo validos debajo."""
    s = [0.95, 0.94, 0.93, 0.92, 0.91, 0.90, 0.60, 0.59]
    emb = np.array([[x, (1 - x * x) ** 0.5] for x in s], dtype=np.float32)
    df = pd.DataFrame({
        "id": [f"SWV{i}" for i in range(8)], "title": [f"Cuento {i}" for i in range(8)],
        "author": [""] * 8, "nivel_cefr": ["A2"] * 8, "hook": [""] * 8, "downloads": [0] * 8,
        "dificultad": [0.5] * 8})
    cat = object.__new__(cm.Catalogo)
    cat.df = df
    cat._emb = emb
    cat._fichas = None
    cat._excl = np.array([True] * 6 + [False] * 2)      # los seis mas parecidos no son lectura
    cat._modelo_emb = lambda: type("M", (), {"encode": staticmethod(
        lambda x, **k: np.array([[1.0, 0.0]], dtype=np.float32))})()
    ids = [l.id for l in cat.buscar("zzqx", n=2)[0]]
    assert ids == ["SWV6", "SWV7"], f"con los 6 primeros excluidos y n=2: {ids}"
    return f"n=2 con seis excluidos delante: {ids}"


prueba("buscar llena n aunque los primeros esten excluidos", _buscar_llena_n_con_excluidos_delante)


def _catalogo_de_mentira(s, titulos, autores, encode=None):
    """Un Catalogo sin disco: `s` es el parecido por tema de cada fila con la consulta."""
    n = len(s)
    cat = object.__new__(cm.Catalogo)
    cat.df = pd.DataFrame({"id": [f"PG{i}" for i in range(n)], "title": titulos, "author": autores,
                           "nivel_cefr": ["B1"] * n, "hook": [""] * n, "downloads": [1] * n,
                           "dificultad": [0.8] * n})
    cat._emb = np.array([[x, (1 - x * x) ** 0.5] for x in s], dtype=np.float32)
    cat._modelo_emb = lambda: type("M", (), {"encode": staticmethod(
        encode or (lambda x, **k: np.array([[1.0, 0.0]] * len(x), dtype=np.float32)))})()
    return cat


def _nombre_parecido_sin_tema_no_rescata():
    """«amor» (15 sep 2026): el autor «Fenn, Amor» subia «Design and tradition» a
    0,85, y «Amour, Amour» o «Amory» a 0,76, por delante de los libros de amor. Un
    nombre de pila o una palabra suelta del titulo ya no rescatan, y un apellido
    parecido tampoco si ninguno de sus libros se parece a lo pedido
    (MARGEN_SEMANTICO_NOMBRE). «chejov» sigue encontrando a Chekhov."""
    cat = _catalogo_de_mentira(
        [0.62, 0.60, 0.76, 0.74, 0.20],
        ["Design and tradition", "Amour, Amour, Dear Planet!", "A Dozen Ways Of Love", "Hints for Lovers",
         "Roster of Company I"],
        ["Fenn, Amor, 1863-1933", "Clutter, Mark", "Dougall, L.", "Haultain, Arnold", "Amory, Charles Bean"])
    for nivel in (None, 0.8):
        ids = [l.id for l in cat.buscar("amor", nivel_lector=nivel, n=5)[0]]
        assert ids == ["PG2", "PG3", "PG0", "PG1", "PG4"], f"«amor» con nivel {nivel}: {ids}"
    # Dos palabras que son nombres de pila del mismo autor, sin su apellido, tampoco
    # son su nombre entero (mutante C8-autor-entero-sin-apellido, 15 sep 2026).
    pila = _catalogo_de_mentira([0.62, 0.76], ["Design and tradition", "A Dozen Ways Of Love"],
                                ["Fenn, Amor Grace, 1863-1933", "Dougall, L."])
    ids = [l.id for l in pila.buscar("amor grace", n=2)[0]]
    assert ids == ["PG1", "PG0"], f"«amor grace» rescata a «Fenn, Amor Grace» sin apellido: {ids}"
    chejov = _catalogo_de_mentira([0.60, 0.65], ["The Bet, and other stories", "Russian Tales"],
                                  ["Chekhov, Anton Pavlovich, 1860-1904", "Smith, John"])
    ids = [l.id for l in chejov.buscar("chejov", n=2)[0]]
    assert ids == ["PG0", "PG1"], f"«chejov» ya no encuentra a Chekhov: {ids}"
    return "ni el nombre de pila, ni «Amour», ni el apellido «Amory» sin tema; «chejov» si"


prueba("un nombre parecido sin tema no rescata", _nombre_parecido_sin_tema_no_rescata)


def _franja_trae_su_nivel_detras_de_los_n():
    """Reinicio 23 (e6, 4db6ea3): con A2, «Fantasmas» no traia ninguno de los 40 cuentos
    de fantasmas de A2-B1, porque el techo lo ponia «True Ghost Stories» y la ventana de
    MARGEN_RELEVANCIA no llegaba a ellos. Con `franja`, detras de los n de siempre van
    los de la franja del lector, marcados: suelo, margen sobre el mejor de la franja,
    margen sobre el techo general, bordes (lo, hi], tope K, el titulo solo de los
    externos, nunca el rescate por nombre y nada sin el .npy de titulos."""
    def cat_con(s, titulos, dif, autores=None):
        cat = _catalogo_de_mentira(s, titulos, autores or ["Smith, John"] * len(s))
        cat.df["dificultad"] = dif
        return cat

    def marcados(cat, q, nivel, n):
        return [l.id for l in cat.buscar(q, nivel_lector=nivel, n=n, franja=True)[0] if l.por_franja]

    assert cm.franja_de(0.7999999999999998) == (0.35, 1.25), cm.franja_de(0.7999999999999998)
    # ACTION PART-1 (0,586) no pasa el suelo; los dos cuentos de su nivel van detras.
    cat = cat_con([0.85, 0.72, 0.64, 0.586, 0.80],
                  ["True Ghost Stories", "The Ghost Friend", "A Night at School", "ACTION PART-1", "Ghosts of Old"],
                  [1.6, 0.5, 0.6, 0.7, 1.7])
    sin = [l.id for l in cat.buscar("ghost stories", nivel_lector=0.4, n=2)[0]]
    con = cat.buscar("ghost stories", nivel_lector=0.4, n=2, franja=True)[0]
    assert [l.id for l in con[:2]] == sin and not any(l.por_franja for l in con[:2]), [(l.id, l.por_franja) for l in con]
    assert [l.id for l in con[2:]] == ["PG1", "PG2"] and all(l.por_franja for l in con[2:]), [l.id for l in con]
    assert not marcados(cat, "ghost stories", None, 2), "sin nivel no hay franja"
    assert len(cat.buscar("ghost stories", nivel_lector=0.4, n=2)[0]) == 2, "sin `franja` no se anade nada"
    # Por debajo de SUELO_FRANJA, no, aunque los margenes lo dejen pasar.
    suelo = cat_con([0.62, 0.58], ["Uno", "Dos"], [0.4, 0.5])
    assert marcados(suelo, "espectros", 0.4, 1) == ["PG0"], marcados(suelo, "espectros", 0.4, 1)
    # A mas de MARGEN_FRANJA del mejor de la franja, no.
    margen = cat_con([0.90, 0.72, 0.66], ["Uno", "Dos", "Tres"], [0.4, 0.5, 0.6])
    assert marcados(margen, "espectros", 0.4, 1) == ["PG0"], marcados(margen, "espectros", 0.4, 1)
    # A mas de MARGEN_TECHO_FRANJA del techo general, tampoco.
    techo = cat_con([0.95, 0.66, 0.64], ["Uno", "Dos", "Tres"], [1.8, 0.5, 0.6])
    assert marcados(techo, "espectros", 0.4, 1) == [], marcados(techo, "espectros", 0.4, 1)
    # Bordes (lo, hi] en milesimas: 0,35 fuera y 1,25 y 1,2500004 dentro con B1.
    borde = cat_con([0.70, 0.69, 0.68], ["Uno", "Dos", "Tres"], [0.35, 1.25, 1.2500004])
    assert marcados(borde, "espectros", 0.8, 1) == ["PG1", "PG2"], marcados(borde, "espectros", 0.8, 1)
    # Como mucho K_FRANJA detras.
    muchos = cat_con([0.70 - 0.005 * i for i in range(16)], [f"Libro {i}" for i in range(16)], [0.4] * 16)
    con = muchos.buscar("espectros", nivel_lector=0.4, n=1, franja=True)[0]
    assert len(con) == 1 + cm.K_FRANJA, len(con)
    # El titulo solo de un externo cuenta (su fila del indice queda por debajo del suelo)...
    tit = cat_con([0.90, 0.50, 0.50], ["Uno", "Dos", "Tres"], [1.8, 0.4, 0.4])
    tit._n_propio, tit._emb_tit = 1, np.array([[0.80, 0.60], [0.30, 0.95394]], dtype=np.float32)
    assert marcados(tit, "espectros", 0.4, 1) == ["PG1"], marcados(tit, "espectros", 0.4, 1)
    # ...y sin un .npy de titulos que cuadre no se marca nada.
    sin_npy = cat_con([0.90, 0.70], ["Uno", "Dos"], [1.8, 0.4])
    sin_npy._n_propio, sin_npy._emb_tit = 1, None
    assert marcados(sin_npy, "espectros", 0.4, 1) == [], marcados(sin_npy, "espectros", 0.4, 1)
    # Con una palabra, el titulo solo va contra sus frases y no contra la palabra suelta:
    # «amor» a secas se parecia 0,8 a «HOLI» o «Kuppu» (reinicio 25, variante E).
    palabra = cat_con([0.9, 0.3, 0.3], ["Uno", "HOLI", "Dos"], [1.8, 0.4, 0.4])
    palabra._emb = np.array([[0.3, 0.9], [0.3, 0.3], [0.3, 0.3]], dtype=np.float32)
    palabra._modelo_emb = lambda: type("M", (), {"encode": staticmethod(
        lambda x, **k: np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 1.0]][:len(x)], dtype=np.float32))})()
    palabra._n_propio, palabra._emb_tit = 1, np.array([[0.95, 0.0], [0.0, 0.8]], dtype=np.float32)
    assert marcados(palabra, "espectros", 0.4, 1) == ["PG2"], marcados(palabra, "espectros", 0.4, 1)
    # El rescate por nombre no marca: «Ghost Stories for Children» casa entero, pero su
    # parecido por tema es 0,40.
    nombre = cat_con([0.80, 0.40, 0.62], ["Ghost Stories", "Ghost Stories for Children", "Uno"], [1.8, 0.4, 0.5])
    m = marcados(nombre, "ghost stories", 0.4, 1)
    assert "PG1" not in m and "PG2" in m, m
    return "detras de los n, con suelo, margenes, bordes, tope, titulo solo y sin rescate ni .npy"


prueba("la franja trae su nivel detras de los n", _franja_trae_su_nivel_detras_de_los_n)


def _titulo_con_palabras_enteras():
    """Reinicio 23: «familia» casaba con «Familiar» por parecido de letras (0,93), y los
    «Familiar Things/Faces» tapaban los cuentos de familia. En el titulo, cada palabra
    entera o con su plural; el parecido de letras queda para el autor («chejov»)."""
    fam = _catalogo_de_mentira([0.70, 0.30, 0.72], ["Mi Familia", "Familiar Faces", "My family"],
                               ["Gaete, Antonia", "Graham, Harry", "Lee, Ann"])
    ids = [l.id for l in fam.buscar("familia", n=3)[0]]
    assert ids[-1] == "PG1", f"«Familiar Faces» rescatado por «familia»: {ids}"
    drag = _catalogo_de_mentira([0.55, 0.70], ["The Dragon", "Castles"], ["Smith, John", "Lee, Ann"])
    ids = [l.id for l in drag.buscar("dragons", n=2)[0]]
    assert ids == ["PG0", "PG1"], f"«dragons» ya no encuentra «The Dragon»: {ids}"
    return "«familia» no rescata «Familiar»; «dragons» sigue encontrando «The Dragon»"


prueba("un titulo casa con palabras enteras", _titulo_con_palabras_enteras)


def _autor_entero_delante_y_parciales_fuera():
    """Prueba como persona de e6 (15 sep 2026): con «Jane Austen», Emma y Pride and
    Prejudice quedaban detras de los libros sobre ella y empatadas con Sidney Austen y
    «Calamity Jane», que solo comparten una parte del nombre."""
    cat = _catalogo_de_mentira(
        [0.74, 0.64, 0.30, 0.60, 0.62, 0.70],
        ["Jane Austen and her works", "Emma", "The Frightened Planet", "Life and Adventures of Calamity Jane",
         "Pride and Prejudice", "Detective Stories"],
        ["Tytler, Sarah, 1827-1914", "Austen, Jane, 1775-1817", "Austen, Sidney", "Calamity Jane, 1856-1903",
         "Austen, Jane, 1775-1817", "Smith, John"])
    ids = [l.id for l in cat.buscar("Jane Austen", n=6)[0]]
    assert ids == ["PG1", "PG4", "PG0", "PG5", "PG3", "PG2"], f"«Jane Austen»: {ids}"
    # Serio de la ronda 3 de 4e sobre el 21: una palabra de tema en la consulta
    # («island», «white», «fang») apagaba el apellido del autor buscado, porque el
    # vocabulario de nombres era todo el campo de autor (aquí, «Island, Peter» y
    # «White, Anne»). Solo apaga un nombre de pila de otro autor con ese apellido.
    mixtas = _catalogo_de_mentira(
        [0.70, 0.72, 0.10, 0.62, 0.66, 0.10],
        ["Treasure Island", "The Island Treasure", "Poems", "White Fang", "Fang and Claw", "Sketches"],
        ["Stevenson, Robert Louis", "Smith, John", "Island, Peter", "London, Jack", "Brown, Mary", "White, Anne"])
    ids = [l.id for l in mixtas.buscar("treasure island stevenson", n=3)[0]]
    assert ids[0] == "PG0", f"«treasure island stevenson» apaga a Stevenson: {ids}"
    ids = [l.id for l in mixtas.buscar("white fang jack london", n=3)[0]]
    assert ids[0] == "PG3", f"«white fang jack london» apaga a Jack London: {ids}"
    # Un seudónimo de una sola palabra («I Love You») no se cubre con cualquier consulta
    # que traiga «love»: con B1 abría «love poems by browning».
    seudo = _catalogo_de_mentira([0.55, 0.45, 0.58], ["Singing in the Rain", "Dramatic Romances", "Love Poems"],
                                 ["I Love You", "Browning, Robert", "Smith, Ann"])
    ids = [l.id for l in seudo.buscar("love poems by browning", n=3)[0]]
    assert ids[0] == "PG1", f"«love poems by browning» abre con un seudónimo de una palabra: {ids}"
    # Una sola palabra no es el nombre entero de nadie: «rosa» como apellido de un
    # colaborador no puede pasar por delante de los títulos con «Rosa».
    rosa = _catalogo_de_mentira(
        [0.57, 0.29, 0.70],
        ["Rosa Mundi and Other Stories", "Modern Poets and Poetry of Spain", "Roses: a Monograph of the Genus Rosa"],
        ["Dell, Ethel M.", "Kennedy, James; Martinez de la Rosa, Francisco", "Andrews, Henry"])
    ids = [l.id for l in rosa.buscar("rosa", n=3)[0]]
    assert ids == ["PG2", "PG0", "PG1"], f"«rosa»: el apellido de un colaborador pasa delante de los títulos: {ids}"
    return "sus obras primero, el libro sobre ella despues; Sidney Austen y Calamity Jane solo por tema"


prueba("con el nombre entero del autor sus obras van delante", _autor_entero_delante_y_parciales_fuera)


def _palabra_suelta_con_frases():
    """Una palabra suelta en espanol casi no se parece a su tema: se incrusta tambien
    en «historias de» y «libros sobre», y vale el mejor parecido (15 sep 2026)."""
    vistos = []

    def encode(x, **k):
        vistos.append(list(x))
        return np.array([[1.0, 0.0] if "historias" in f else [0.0, 1.0] for f in x], dtype=np.float32)

    cat = _catalogo_de_mentira([0.9, 0.5], ["Uno", "Dos"], ["A", "B"], encode)
    ids = [l.id for l in cat.buscar("amor", n=2)[0]]
    assert vistos[0] == ["amor", "historias de amor", "libros sobre amor"], vistos
    assert ids == ["PG0", "PG1"], f"la frase no cuenta: {ids}"
    cat.buscar("cuentos de amor", n=2)
    assert vistos[1] == ["cuentos de amor"], f"una consulta de varias palabras no lleva frases: {vistos[1]}"
    return "«amor» se incrusta en tres frases y gana la de «historias de»; «cuentos de amor», sola"


prueba("una palabra suelta se busca tambien dentro de frases", _palabra_suelta_con_frases)


def _sin_titulo_fuera():
    """89 filas de Gutenberg sin titulo: su vector sale de «nan. nan.» y encabezaba
    busquedas como «amor» (15 sep 2026)."""
    cat = _catalogo_de_mentira([0.9, 0.8, 0.5], [None, "nan", "Un libro"], ["", "", "X, Y"])
    ids = [l.id for l in cat.buscar("algo que buscar", n=3)[0]]
    assert ids == ["PG2"] and cat.sin_titulo == 2, (ids, getattr(cat, "sin_titulo", None))
    return "las dos filas sin titulo fuera y contadas"


prueba("las filas sin titulo no salen al buscar", _sin_titulo_fuera)


def _busquedas_reales_en_espanol():
    """Sobre el catalogo real, si esta aqui: lo que pidio Central (15 sep 2026) y
    las tres consultas de la ronda 2 de 4e, en las que una palabra espanola se
    parecia a un titulo o a un autor («sobre» a «Sombre», «historias» a
    «Historians», «luna» a «Luna: The Lost Dog»)."""
    import re
    raiz = Path(__file__).resolve().parent
    if not (raiz / "catalogo_medido.csv").exists():
        return "sin el catalogo real aqui"
    cat = cm.Catalogo(cm.CSV_MEDIDO)
    _, huella = cat._externo_indexable()
    if not ((raiz / f"catalogo_emb_ext_{huella}.npy").exists() or (cm.DIR_CACHE / f"catalogo_emb_ext_{huella}.npy").exists()):
        return f"sin catalogo_emb_ext_{huella}.npy: no recalculo 15.000 vectores en una prueba"

    def top(q, nivel=None, n=12):
        return cat.buscar(q, nivel_lector=nivel, n=n)[0]

    def lista(libros):
        return [(l.id, l.titulo[:24]) for l in libros[:5]]

    r = top("dostoyevski")
    assert sum("Dostoyevsky" in l.autor for l in r[:5]) >= 3, lista(r)
    r = top("chejov")
    assert r[0].autor.startswith("Chekhov"), lista(r)
    r = top("A Midsummer Night's Dream", 0.95)
    assert {l.id for l in r[:3]} == {"PG1514", "PG2242", "PG1113"}, lista(r)
    # Ronda 2 del front de 4e: tres libros de «Austin, Jane G.» salian arriba por
    # el nombre parecido, y un solo falso positivo por nombre («Fenn, Amor») fijaba
    # el techo de «amor» y vaciaba los bloques de la pantalla nueva.
    for nivel in (None, 0.8):
        r = top("Jane Austen", nivel)
        assert sum("Austen" in l.titulo + l.autor for l in r[:5]) >= 4, lista(r)
        assert not any("Austin" in l.autor for l in r[:5]), f"Jane G. Austin delante con nivel {nivel}: {lista(r)}"
        parciales = [l.titulo for l in r if "Austen, Sidney" in l.autor or "Calamity Jane" in l.autor]
        assert not parciales, f"coincidencias parciales del nombre con nivel {nivel}: {parciales}"
    r = top("Jane Austen")
    assert r[0].autor.startswith("Austen, Jane"), f"con el nombre entero, sus obras no van primero: {lista(r)}"
    # Serio de 4e sobre el 21: apellido con tema o título. Los mínimos son los que 4e
    # midió con la regla apagada (auditoria/ronda3_2026-09-15_reinicio21.md).
    for q, patron, minimo in (("treasure island stevenson", r"Stevenson, Robert Louis", 8),
                              ("love poems by browning", r"Browning", 7),
                              ("the secret garden frances hodgson burnett", r"Burnett, Frances Hodgson", 7),
                              ("white fang jack london", r"London, Jack", 2),
                              ("the call of the wild by jack london", r"London, Jack", 10)):
        r = top(q, n=10)
        suyos = sum(bool(re.search(patron, l.autor)) for l in r)
        assert suyos >= minimo, f"«{q}»: {suyos} de 10 del autor, 4e midió {minimo}: {lista(r)}"
    for q, patron in (("browning", r"Browning"), ("robert browning", r"Browning, Robert")):
        r = top(q)
        assert re.search(patron, r[0].autor), f"«{q}» no abre con Browning: {lista(r)}"
    r = top("amor", 0.8)
    amor = sum(bool(re.search(r"(?i)\blov(e|ed|er|ers|es|ing)\b|romance", l.titulo + " " + l.gancho)) for l in r)
    assert amor >= 6, f"«amor» con B1: {amor} de 12 sobre amor: {lista(r)}"
    assert "PG53850" not in [l.id for l in r], f"«Design and tradition» (Fenn, Amor) sigue en «amor»: {lista(r)}"
    r = top("cuentos de miedo", 0.8)
    assert not any("Brownlie" in l.autor for l in r[:3]), lista(r)
    for q, fuera, dentro in (("cuentos sobre la lluvia y los agricultores", r"(?i)centos|sombre", "SWV145049"),
                             ("historias sobre la lluvia y los agricultores", r"(?i)historians", "SWV145049"),
                             ("viaje al espacio y la luna", r"(?i)\bluna\b", "SWV554287")):
        r = top(q)
        colados = [l.titulo for l in r[:5] if re.search(fuera, l.titulo + " " + l.autor)]
        assert not colados and dentro in [l.id for l in r[:5]], f"«{q}»: {lista(r)}"
    # Reinicio 25, segundo top-k de la franja (casos de e6 y de la Central, no calibracion).
    franja = "sin el .npy de titulos: la franja no marca y no se mide"
    if cat.emb_titulos() is not None:
        fuera = cat._leer_no_lectura()

        def marcados(q, nivel):
            libros = cat.buscar(q, nivel_lector=nivel, n=24, franja=True)[0]
            sin = cat.buscar(q, nivel_lector=nivel, n=24)[0]
            assert [l.id for l in libros[:len(sin)]] == [l.id for l in sin], f"«{q}» {nivel}: cambian los n"
            m = [l for l in libros if l.por_franja]
            malos = [l.id for l in m if l.id.upper() in fuera or "Fenn, Amor" in l.autor]
            assert not malos, f"«{q}» {nivel}: marcados excluidos o Fenn {malos}"
            return m

        for nivel in (0.4, 0.8):
            robots = sum(bool(re.search(r"(?i)robot", l.titulo + " " + l.gancho)) for l in marcados("Robots", nivel))
            assert robots >= 3, f"«Robots» {nivel}: {robots} robots marcados"
        m = marcados("Terror gótico", 0.8)
        assert not any("ACTION PART" in l.titulo.upper() for l in m), [l.titulo for l in m]
        for nivel in (1.2, 1.6):
            m = marcados("familia", nivel)
            assert not any(re.search(r"(?i)\bfamiliar\b", l.titulo) for l in m), [l.titulo for l in m]
        m = marcados("rosa", 0.8)
        assert not any(re.search(r"(?i)little rabbit|sun in the beach", l.titulo) for l in m), [l.titulo for l in m]
        sin, _ = cat.buscar("ghost stories", n=24)
        con, _ = cat.buscar("ghost stories", n=24, franja=True)
        assert [l.id for l in sin] == [l.id for l in con] and not any(l.por_franja for l in con), "«ghost stories» sin perfil"
        franja = "franja: Robots, sin ACTION PART-1, sin Familiar, sin los dos de rosa, ghost stories igual"
    return (f"dostoyevski, chejov, Midsummer, Jane Austen; «amor» B1 {amor}/12; sin Brownlie ni Sombre, "
            f"Historians ni Luna; {franja}")


prueba("buscar en espanol en el catalogo real: nombres y temas", _busquedas_reales_en_espanol)


def _correccion_se_aplica_al_cargar():
    """PG2242: la tabla de correcciones cambia la dificultad del libro, su letra
    y su curva de un capitulo, sin tocar el CSV grande."""
    carpeta = _nuevo()
    ids = _catalogo_de_nivel(carpeta, n=3)
    pd.DataFrame({"id": [ids[0], ids[1]] * 1 + [ids[1]], "indice": [0, 0, 1], "capitulo": [1, 1, 2],
                  "titulo": ["Texto completo", "Uno", "Dos"], "dificultad": [0.7, 0.7, 0.7],
                  "min": [0.4, 0.5, 0.5], "max": [0.9, 0.9, 0.9], "ventanas": [36, 18, 18],
                  "palabras": [9000, 4500, 4500]}).to_parquet(carpeta / cm.NOMBRE_CAPITULOS, index=False)
    antes = (carpeta / "catalogo_medido.csv").read_bytes()
    pd.DataFrame({"id": [ids[0], ids[1], "PG5", ids[2]], "dificultad": [1.713, 1.5, 1.0, "nada"],
                  "min": [1.083, None, None, None], "max": [1.989, None, None, None],
                  "motivo": ["remedido", "varios capitulos", "no esta", "roto"]}).to_csv(
        carpeta / cm.NOMBRE_CORRECCIONES, index=False)
    cat = cm.Catalogo(carpeta / "catalogo_medido.csv")
    fila = cat.df[cat.df["id"] == ids[0]].iloc[0]
    assert abs(float(fila["dificultad"]) - 1.713) < 1e-9, fila["dificultad"]
    assert fila["nivel_cefr"] == "C1", f"la letra no sale de la cifra corregida: {fila['nivel_cefr']}"
    assert abs(float(cat.df[cat.df["id"] == ids[2]].iloc[0]["dificultad"]) - 0.7) < 1e-9, "una fila rota cambio el libro"
    curva = cat.capitulos_de(ids[0])
    assert len(curva) == 1 and curva[0]["dificultad"] == 1.713 and curva[0]["min"] == 1.083 and curva[0]["max"] == 1.989, curva
    varios = cat.capitulos_de(ids[1])
    assert [c["dificultad"] for c in varios] == [0.7, 0.7], f"se invento un reparto por capitulos: {varios}"
    assert (carpeta / "catalogo_medido.csv").read_bytes() == antes, "se escribio el CSV grande"
    (carpeta / cm.NOMBRE_CORRECCIONES).write_text("esto no es un csv\x00\x00", encoding="utf-8")
    assert len(cm.Catalogo(carpeta / "catalogo_medido.csv").df) == 3, "un archivo de correcciones roto tumba el catalogo"
    return "1,713 C1 en el libro y en su curva; varios capitulos intactos; CSV grande sin tocar"


prueba("la tabla de correcciones se aplica al cargar sin tocar el CSV", _correccion_se_aplica_al_cargar)


def _titulo_entero_gana_a_palabra_suelta():
    """Prueba final del 13 sep 2026: «Little Black Sambo» empataba a 0,85 con
    cinco titulos que solo comparten «Black». Sin perder «chejov» ni un nombre
    dentro de una frase en espanol."""
    titulos = ["Little Black Sambo Bannerman, Helen", "Queen of the Black Coast Howard, Robert E.",
               "Beyond the Black River Howard, Robert E.", "The Story of Little Black Sambo Bannerman, Helen",
               "The Cherry Orchard Chekhov, Anton", "Oliver Twist Dickens, Charles"]
    f = cm._fichas(titulos)
    lex = cm._similitud_nombres("Little Black Sambo", f)
    exactos = min(lex[0], lex[3])
    parciales = max(lex[1], lex[2])
    assert exactos > parciales, f"un titulo que solo comparte «Black» empata o gana: {lex.round(3).tolist()}"
    assert exactos * cm._PESO_NOMBRE > parciales * cm._PESO_NOMBRE + 0.01, "la ventaja no aguanta el desempate por tema"
    chejov = cm._similitud_nombres("chejov", f)[4]
    assert chejov >= cm._PARECIDO_NOMBRE, f"«chejov» ya no rescata a Chekhov: {chejov:.3f}"
    dickens = cm._similitud_nombres("libros de dickens sobre huerfanos", f)[5]
    assert dickens >= cm._PARECIDO_NOMBRE, f"un autor dentro de una frase ya no se rescata: {dickens:.3f}"
    return f"exacto {exactos:.2f} > parcial {parciales:.2f}; chejov {chejov:.2f}; dickens en frase {dickens:.2f}"


prueba("un titulo entero gana a los que solo comparten una palabra", _titulo_entero_gana_a_palabra_suelta)


class _PuntuadorFalso:
    """Sustituye al v4: rechaza como no-prosa lo que lleve «LISTA»."""
    def __init__(self):
        self.llamadas = 0

    def puntuar(self, texto):
        import types
        self.llamadas += 1
        if "LISTA" in texto:
            raise ValueError("parece una lista")
        n = len(texto.split())
        return types.SimpleNamespace(puntuacion=round(min(2.0, n / 1000), 3), n_bloques=max(1, n // 250))


def _medicion_reanudable_y_mismo_reparto():
    """14 sep 2026: medir los ~12.600 textos de StoryWeaver ya no es de un tiron.
    Mismo reparto que el catalogador (un rechazado por el filtro entra en un
    bloque), shards reanudables y clave por contenido."""
    spec = importlib.util.spec_from_file_location("medir_corpus", "tools/medir_corpus.py")
    mc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc)
    carpeta = _nuevo() / "medidas"

    def tabla(texto_a="a " * 400):
        return pd.DataFrame({
            "fuente": ["storyweaver"] * 4, "id": ["SWV1", "SWV2", "SWV3", "SWV4"],
            "nivel_editor": ["1", "1", "1", "1"],
            # SWV3 y SWV4 por debajo de MIN_WORDS (150): solo pueden medirse en bloque.
            "texto": [texto_a, "LISTA " + "b " * 299, "c " * 120, "d " * 140],
        }).assign(palabras=lambda d: d["texto"].str.split().map(len))

    p1 = _PuntuadorFalso()
    df, completo = mc.medir(tabla(), puntuador=p1, carpeta=carpeta, tope=1, salida=lambda *a: None)
    assert not completo and p1.llamadas == 1, (completo, p1.llamadas)
    lineas = sum(1 for r in carpeta.glob("medidas_*.jsonl") for _ in r.open(encoding="utf-8"))
    assert lineas == 1, f"la primera unidad no quedo en disco al cortar: {lineas}"
    with next(carpeta.glob("medidas_*.jsonl")).open("a", encoding="utf-8") as f:
        f.write('{"clave": "cortada')                        # un corte a mitad de linea
    p2 = _PuntuadorFalso()
    df, completo = mc.medir(tabla(), puntuador=p2, carpeta=carpeta, salida=lambda *a: None)
    # Unidades: SWV1 texto, SWV2 texto (rechazada), bloque [SWV2], bloque [SWV3, SWV4]
    assert completo and p2.llamadas == 3, f"no reanudo: {p2.llamadas} llamadas"
    fila = df.set_index("id")
    assert fila.loc["SWV1", "medida"] == "texto"
    assert fila.loc["SWV2", "medida"] == "" or fila.loc["SWV2", "medida"] == "bloque", fila.loc["SWV2"]
    assert fila.loc["SWV3", "medida"] == "bloque" and fila.loc["SWV4", "medida"] == "bloque"
    assert fila.loc["SWV3", "dificultad"] == fila.loc["SWV4", "dificultad"], "el bloque no reparte su medida"
    p3 = _PuntuadorFalso()
    df3, _ = mc.medir(tabla(), puntuador=p3, carpeta=carpeta, salida=lambda *a: None)
    assert p3.llamadas == 0, f"volvio a medir lo hecho: {p3.llamadas}"
    assert df3["dificultad"].fillna(-1).tolist() == df["dificultad"].fillna(-1).tolist()
    p4 = _PuntuadorFalso()
    mc.medir(tabla("otro " * 400), puntuador=p4, carpeta=carpeta, salida=lambda *a: None)
    assert p4.llamadas == 1, f"un texto cambiado no se volvio a medir: {p4.llamadas}"
    return "corta, reanuda sin repetir, bloque con el rechazado y clave por contenido"


prueba("la medicion del corpus es reanudable y reparte como el catalogador", _medicion_reanudable_y_mismo_reparto)


def _cargar_medidor():
    spec = importlib.util.spec_from_file_location("medir_corpus", "tools/medir_corpus.py")
    mc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc)
    return mc


def _cola_de_grupo_medida_o_contada():
    """Auditoria cruzada de e6 (14 sep 2026): lo que sobraba por debajo de 250
    palabras al acabar un grupo se tiraba sin medir. 16 textos salian del
    catalogo contados junto a los rechazos del filtro de prosa."""
    mc = _cargar_medidor()
    ids = ["SWV10", "SWV11", "SWV12", "SWV20", "SWV21", "SWV22", "SWV23", "SWV30"]
    niveles = ["1", "1", "1", "2", "2", "2", "2", "3"]
    palabras = [120, 140, 100, 130, 130, 80, 90, 60]
    df = pd.DataFrame({"fuente": ["storyweaver"] * 8, "id": ids, "nivel_editor": niveles,
                       "texto": [f"w{i} " * n for i, n in enumerate(palabras)], "palabras": palabras})
    p = _PuntuadorFalso()
    df, completo = mc.medir(df, puntuador=p, carpeta=_nuevo() / "medidas", salida=lambda *a: None)
    fila = df.set_index("id")
    assert completo
    # Nivel 1: bloque [10, 11] de 260 y cola [12] de 100, por debajo de MIN_WORDS: se une.
    assert fila.loc["SWV12", "medida"] == "bloque", "la cola corta del grupo se quedo sin medir"
    assert fila.loc["SWV10", "dificultad"] == fila.loc["SWV12", "dificultad"] == 0.36, fila["dificultad"].tolist()
    # Nivel 2: bloque [20, 21] de 260 y cola [22, 23] de 170: se mide sola.
    assert fila.loc["SWV20", "dificultad"] == 0.26 and fila.loc["SWV22", "dificultad"] == fila.loc["SWV23", "dificultad"] == 0.17, \
        fila["dificultad"].tolist()
    # Nivel 3: 60 palabras en todo el grupo; no se puede medir y se cuenta aparte.
    assert pd.isna(fila.loc["SWV30", "dificultad"]) and df.attrs["cola_sin_medir"] == ["SWV30"], df.attrs
    return "cola corta unida al ultimo bloque, cola de 170 sola, grupo de 60 palabras contado aparte"


prueba("la cola de cada grupo se mide o se cuenta aparte", _cola_de_grupo_medida_o_contada)


class _PuntuadorConRaro(_PuntuadorFalso):
    """Como el falso, pero un texto con «RARO» dispara la medida a 1,5, como la sinopsis
    de APOCALYPTO dentro de un bloque de cuentos de nivel 1."""
    def puntuar(self, texto):
        import types
        r = super().puntuar(texto)
        return types.SimpleNamespace(puntuacion=1.5, n_bloques=r.n_bloques) if "RARO" in texto else r


def _bloque_con_un_texto_raro():
    """Central, 15 sep 2026: un solo texto raro arrastraba la medida de todo su bloque
    (SWV991, un poema de nivel 1, salia B2). Si quitar uno mueve la medida mas de
    MARGEN_RARO, los demas se quedan con la medida sin el; el raro conserva la del
    bloque entero y se marca."""
    mc = _cargar_medidor()
    ids = ["SWV1", "SWV2", "SWV3", "SWV4", "SWV5", "SWV6", "SWV7"]
    textos = ["uno " * 70, "dos " * 70, "tres " * 70, "RARO " + "cuatro " * 69,
              "cinco " * 90, "seis " * 90, "siete " * 90]
    df = pd.DataFrame({"fuente": ["storyweaver"] * 7, "id": ids, "nivel_editor": ["1"] * 4 + ["2"] * 3,
                       "texto": textos, "palabras": [70, 70, 70, 70, 90, 90, 90]})
    df, completo = mc.medir(df, puntuador=_PuntuadorConRaro(), carpeta=_nuevo() / "medidas",
                            salida=lambda *a: None)
    fila = df.set_index("id")
    assert completo
    # Nivel 1: bloque de 280 palabras con el raro (1,5); sin el, 210 palabras (0,21).
    assert [fila.loc[i, "dificultad"] for i in ids[:3]] == [0.21] * 3, fila["dificultad"].tolist()
    assert fila.loc["SWV4", "dificultad"] == 1.5 and bool(fila.loc["SWV4", "raro_en_bloque"]), fila.loc["SWV4"].to_dict()
    # Nivel 2: sin raro; quitar uno mueve 0,09 y nadie cambia.
    assert [fila.loc[i, "dificultad"] for i in ids[4:]] == [0.27] * 3, fila["dificultad"].tolist()
    assert fila["raro_en_bloque"].sum() == 1, fila["raro_en_bloque"].tolist()
    assert [b["raro"] for b in df.attrs["bloques_con_raro"]] == ["SWV4"], df.attrs["bloques_con_raro"]
    return "el raro conserva 1,5 y queda marcado; sus tres vecinos pasan a 0,21; el bloque sin raro no cambia"


prueba("un bloque con un texto raro no arrastra a los demas", _bloque_con_un_texto_raro)


def _clave_de_medida_con_modelo():
    """Auditoria cruzada de e6: con otro modelo, lo medido no puede reutilizarse.
    Lo medido antes de meter la huella en la clave vale solo con el v4."""
    mc = _cargar_medidor()
    carpeta = _nuevo() / "medidas"
    texto = "a story " * 200

    def tabla():
        return pd.DataFrame({"fuente": ["voa"], "id": ["VOA1"], "nivel_editor": [None],
                             "texto": [texto], "palabras": [400]})

    def llamadas(modelo):
        p = _PuntuadorFalso()
        df, _ = mc.medir(tabla(), puntuador=p, carpeta=carpeta, salida=lambda *a: None, modelo=modelo)
        return p.llamadas, float(df["dificultad"].iloc[0])

    assert llamadas("modelo-A")[0] == 1 and llamadas("modelo-A")[0] == 0
    assert llamadas("modelo-B")[0] == 1, "con otro modelo reutilizo la medida"
    viejo = carpeta.parent / "legado"
    viejo.mkdir()
    (viejo / "medidas_0000.jsonl").write_text(json.dumps(
        {"clave": mc.clave("texto", ["VOA1"], texto), "tipo": "texto", "ids": ["VOA1"],
         "dificultad": 1.234, "ventanas": 2, "error": None}) + "\n", encoding="utf-8")
    carpeta = viejo
    assert llamadas("otro") == (1, 0.4), "una medida sin modelo se reutilizo con otro modelo"
    assert llamadas(mc.HUELLA_V4) == (0, 1.234), "la medida del v4 anterior a la huella no se reutilizo"
    guardadas = [json.loads(l) for r in viejo.glob("medidas_*.jsonl") for l in r.open(encoding="utf-8")]
    assert any(g.get("modelo") == mc.HUELLA_V4 and g["dificultad"] == 1.234 for g in guardadas), guardadas
    return "mismo modelo reutiliza, otro vuelve a medir; lo de antes solo con el v4, y se reescribe"


prueba("la clave de medida cambia con el modelo", _clave_de_medida_con_modelo)


def _catalogador_aqui():
    """Como `_cargar_catalogador`, que se define mas abajo y aun no existe aqui."""
    spec = importlib.util.spec_from_file_location("catalogar_corpus", "tools/catalogar_corpus.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pistas_de_busqueda_de_los_libres():
    """Auditoria cruzada de e6 (14 sep 2026): en los 15.357 libres `hook` y
    `huella_texto` iban vacios y el vector salia solo de titulo y autor. Los
    fixtures de este archivo tenian el mismo punto ciego: todos con hook ""."""
    cc = _catalogador_aqui()
    atribucion = "\n\n«Chunchun» de X, publicado en StoryWeaver (Pratham Books) con licencia CC BY 4.0: https://x"
    texto = ("Chunchun was a little girl just like you.\n\nChunchun loved making things. One day, "
             "Chunchun decided to make an umbrella! She picked a piece of paper.")
    df = pd.DataFrame({"texto": [texto + atribucion, "word " * 50, ""],
                       "temas": ["Children's stories; StoryWeaver reading level 2",
                                 "VOA Learning English; As It Is", "Children's stories; Let's Read reading level 1"]})
    cc.pistas_de_busqueda(df)
    hook, huella = df["hook"].tolist(), df["huella_texto"].tolist()
    assert hook[0] == "Chunchun was a little girl just like you. Chunchun loved making things.", hook[0]
    assert huella[0].startswith("Children's stories; StoryWeaver. One day, Chunchun decided"), huella[0]
    assert "reading level" not in huella[0] and "licencia" not in huella[0] + hook[0], (hook[0], huella[0])
    assert hook[1] == " ".join(["word"] * 30) + "…" and huella[1].startswith("VOA Learning English; As It Is. word"), hook[1]
    assert hook[2] == "", hook[2]

    # Y en el catalogo que se despliega: texto indexable mas alla del titulo.
    ruta = Path("catalogo_externo.csv")
    if not ruta.exists():
        return "gancho, huella y temas sin nivel del editor (sin catalogo_externo.csv en disco)"
    ext = pd.read_csv(ruta, usecols=["title", "hook", "huella_texto"]).fillna("")
    vacios = int((ext["hook"].str.strip() == "").sum())
    assert vacios <= len(ext) // 100, f"{vacios} de {len(ext)} textos libres sin gancho en catalogo_externo.csv"
    # Un cuento muy corto cabe entero en el gancho y su huella es solo el tema:
    # lo que cuenta es cuanto texto hay entre los dos, ademas del titulo.
    pistas = (ext["hook"] + " " + ext["huella_texto"]).str.split().map(len)
    cortos = int((pistas < 8).sum())
    assert cortos <= len(ext) // 100, f"{cortos} de {len(ext)} con menos de 8 palabras de pistas"
    return f"gancho y huella en la prueba; en el catalogo, {vacios} sin gancho y {cortos} con menos de 8 palabras de {len(ext)}"


prueba("los textos libres se buscan por su texto y sus temas, no solo por el titulo",
       _pistas_de_busqueda_de_los_libres)


def _anuncios_fuera_y_enlaces_fuera_del_gancho():
    """Ronda 2 de 4e (15 sep 2026): anuncios subidos a StoryWeaver salian en la
    tarjeta con su enlace. El anuncio va a no_lectura; el enlace no entra en el
    gancho ni en la huella de nadie."""
    spec = importlib.util.spec_from_file_location("marcar_no_lectura", "tools/marcar_no_lectura.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cuento = ("The girl went to school and her mother made lunch. She was happy. After school they went "
              "home for dinner and she played with her friends. Contact: www.alqamaracademy.org for the "
              "girl and her friends who went home after school and played.")
    dic = {w.lower().strip(".:,") for w in cuento.split()}
    atribucion = "\n\n«X» de Y, publicado en StoryWeaver (X) con licencia CC BY 4.0: https://storyweaver.org.in/x"
    anuncios = ["ABS 200 Complete Course ( Introduction to Applied Behavioral Science ) To Buy This Tutorial "
                "Click Below http://www.homeworkbag.com/ASHFORD-COURSE/ABS-200",
                "Why is My Blender Not Spinning what are the Reasons and Solutions: https://blenderproguide.com/why/"]
    for a in anuncios:
        assert "anuncio" in (mod.motivo_no_lectura(a + atribucion, dic) or ""), f"no marca: {a[:40]}"
    assert mod.motivo_no_lectura(cuento + atribucion, dic) is None, "marca un cuento que da una direccion web"
    # La primera pasada real (15 sep 2026) marco 24 libros de Bilum Books en Let's Read
    # y cuentos de StoryWeaver que citan a la OMS o a UNICEF.
    bilum = cuento + " For more information visit www.bilumbooks.com."
    assert mod.motivo_no_lectura(bilum, dic, fuente="letsread") is None, "marca un libro de una coleccion editada"
    oms = cuento + " For more information visit https://www.who.int/respiratory/asthma/definition/en/"
    assert mod.motivo_no_lectura(oms, dic) is None, "marca un cuento que cita a la OMS"
    cupon = cuento + " For more information visit https://www.ritecoupons.com/stores/x"
    assert "anuncio" in (mod.motivo_no_lectura(cupon, dic) or ""), "no marca un cupon con llamada"
    assert (mod.motivo_no_lectura(cuento, dic, "swv687758") or "").startswith("anuncio"), "no mira la lista revisada"
    assert (mod.motivo_no_lectura(cuento, dic, "SWV98807") or "").startswith("sinopsis"), "APOCALYPTO no va a no_lectura"

    cc = _catalogador_aqui()
    df = pd.DataFrame({"texto": ["Introduction Manufacturing in Australia( https://forgelabs.com.au/blogs/x ) is "
                                 "changing quickly as new technologies arrive. More text follows here today.",
                                 "Ewwwwww.... said Stella. What is that smell? She called her mother at once."],
                       "temas": ["Children's stories; StoryWeaver reading level 3"] * 2})
    cc.pistas_de_busqueda(df)
    pistas = (df["hook"] + " " + df["huella_texto"]).tolist()
    assert "http" not in pistas[0] and "( )" not in pistas[0] and "Australia is changing" in pistas[0], pistas[0]
    assert df["hook"][1].startswith("Ewwwwww...."), f"se come un texto que no es un enlace: {df['hook'][1]}"
    return "dos anuncios marcados, el cuento con direccion no; ni enlaces ni parentesis vacios en las pistas"


prueba("los anuncios no son lectura y los enlaces no salen en el gancho", _anuncios_fuera_y_enlaces_fuera_del_gancho)


def _embeddings_por_partes_reanudan():
    import numpy as np
    cc = _catalogador_aqui()
    carpeta = _nuevo() / "partes"

    class Modelo:
        lotes = 0

        def encode(self, lote, **k):
            Modelo.lotes += 1
            return np.array([[len(t), 1.0] for t in lote])

    class Cat:
        def _externo_indexable(self):
            return ["a", "bb", "ccc", "dddd", "eeeee"], "h0"

        def _modelo_emb(self):
            return Modelo()

    emb, nombre = cc.embeddings_por_partes(Cat(), carpeta=carpeta, parte=2, salida=lambda *a: None)
    assert nombre == "catalogo_emb_ext_h0.npy" and Modelo.lotes == 3, (nombre, Modelo.lotes)
    assert emb[:, 0].tolist() == [1, 2, 3, 4, 5], emb.tolist()
    (carpeta / "h0" / "parte_0001.npy").unlink()             # un corte: falta la parte del medio
    Modelo.lotes = 0
    emb2, _ = cc.embeddings_por_partes(Cat(), carpeta=carpeta, parte=2, salida=lambda *a: None)
    assert Modelo.lotes == 1 and emb2.tolist() == emb.tolist(), (Modelo.lotes, emb2.tolist())
    return "tres partes; tras perder una, solo recalcula esa y el resultado es el mismo"


prueba("los embeddings del externo se calculan por partes reanudables", _embeddings_por_partes_reanudan)


# --- 2. El lector ---------------------------------------------------------------
print("\nAbrir un libro libre en el lector")


def _con_catalogo(fn):
    carpeta = _nuevo()
    viejo_cat, vieja_ruta = ui._catalogo, ui.RUTA_LIBROS
    ui._catalogo = _montar(carpeta)
    ui.RUTA_LIBROS = carpeta / "libros"
    try:
        return fn(carpeta)
    finally:
        ui._catalogo, ui.RUTA_LIBROS = viejo_cat, vieja_ruta


def _cache_no_confunde_con_gutenberg(carpeta):
    (carpeta / "libros").mkdir(parents=True, exist_ok=True)
    (carpeta / "libros" / "pg369.txt").write_text("x" * 5000, encoding="utf-8")
    # SWV369 tiene texto propio: cacheado (no sale a la red) por eso, no por pg369.
    assert ui._esta_cacheado("SWV369") is True
    (carpeta / "libros" / "pg141.txt").write_text("x" * 5000, encoding="utf-8")
    assert ui._esta_cacheado("SWgdl141") is False, "un id externo sin texto acierta en el pg141 de Gutenberg"
    return "los digitos de un id externo no se buscan entre los libros de Gutenberg"


prueba("la cache no confunde un id externo con uno de Gutenberg",
       lambda: _con_catalogo(_cache_no_confunde_con_gutenberg))


def _abre_sin_red(carpeta):
    import urllib.request
    real = urllib.request.urlopen

    def sin_red(*a, **k):
        raise AssertionError("un libro libre no puede salir a la red")

    urllib.request.urlopen = sin_red
    try:
        ruta = ui._descargar_gutenberg("SWV369")
    finally:
        urllib.request.urlopen = real
    p = Path(ruta)
    assert p.exists() and p.name == "swv369.txt", ruta
    texto = p.read_text(encoding="utf-8")
    assert texto.startswith("On Sunday") and "CC BY 4.0" in texto[-80:], texto[-120:]
    try:
        ui._descargar_gutenberg("SWgdlgdl42")
    except ValueError as e:
        assert "no hay texto disponible" in str(e), e
    else:
        raise AssertionError("un id sin texto no avisa")
    return "texto y atribucion escritos en local, sin red; sin texto, aviso claro"


prueba("un libro libre se abre sin descargar nada", lambda: _con_catalogo(_abre_sin_red))


def _copia_vieja_se_renueva(carpeta):
    """Tercer caso de Codex: si el texto del catalogo cambia (una correccion, una
    atribucion nueva), la copia local no puede quedarse con la version vieja."""
    ruta = Path(ui._descargar_gutenberg("SWV369"))
    ruta.write_text("version vieja del cuento", encoding="utf-8")
    ruta2 = Path(ui._descargar_gutenberg("SWV369"))
    texto = ruta2.read_text(encoding="utf-8")
    assert ruta2 == ruta and texto.startswith("On Sunday"), texto[:60]
    return "la copia local se reescribe cuando no coincide con el catalogo"


prueba("una copia vieja de un libro libre se renueva", lambda: _con_catalogo(_copia_vieja_se_renueva))


def _cabecera_con_titulo(carpeta):
    ruta = ui._descargar_gutenberg("SWV369")
    salida = ui._abrir(ruta)
    libro = salida[0]
    assert libro is not None, salida
    assert getattr(libro, "id_catalogo", None) == "SWV369", getattr(libro, "id_catalogo", None)
    textos = " ".join(str(s) for s in salida if isinstance(s, str))
    assert "The Red Raincoat" in textos and "swv369.txt" not in textos, textos[:300]
    return "id del catalogo apuntado y la cabecera con el titulo, no con el archivo"


prueba("la cabecera de un libro libre lleva su titulo", lambda: _con_catalogo(_cabecera_con_titulo))


def _tabla_y_desplegable(carpeta):
    libros = ui.catalogo().por_nivel(0.4, holgura=0.3, n=10)
    ids = [b.id for b in libros]
    assert "SWV369" in ids, f"por nivel no ofrece los cuentos libres: {ids}"
    upd = ui._opciones_libros(libros)
    opciones = [str(o[1]) for o in upd["choices"]]
    assert "SWV369" in opciones, f"el desplegable no deja abrir el cuento libre: {opciones}"
    tabla = ui._tabla_libros(libros)
    assert "no hay texto disponible" not in tabla and "StoryWeaver y no hay" not in tabla, tabla[:200]
    return f"{len(opciones)} abribles en la tabla y en el desplegable"


prueba("el buscador ofrece y deja abrir los cuentos libres", lambda: _con_catalogo(_tabla_y_desplegable))


# --- 3. Catalogar ---------------------------------------------------------------
print("\nCatalogar sin colar textos con derechos")


def _cargar_catalogador():
    spec = importlib.util.spec_from_file_location("catalogar_corpus", "tools/catalogar_corpus.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _aborta_con_derechos():
    cc = _cargar_catalogador()
    carpeta = _nuevo()
    ruta = carpeta / "cuentos.jsonl"
    filas = [
        {"archivo": "0001_libre.md", "titulo": "Libre", "licencia": "CC-BY", "al_catalogo": True,
         "nivel_editor": "1", "texto": "A free story. " * 60},
        # Un descargador equivocado lo marca al catalogo, pero la licencia es NC.
        {"archivo": "0002_nc.md", "titulo": "Con derechos", "licencia": "CC-BY-NC", "al_catalogo": True,
         "nivel_editor": "1", "texto": "A restricted story. " * 60},
    ]
    ruta.write_text("\n".join(json.dumps(f) for f in filas), encoding="utf-8")
    cc.FUENTES = {"african_storybook": ruta}
    try:
        cc.cargar(None)
    except SystemExit as e:
        assert "licencia no libre" in str(e), e
        return "aborta y dice por que"
    raise AssertionError("un texto CC-BY-NC marcado por error al catalogo se colo")


prueba("el catalogador aborta si llega un texto con derechos", _aborta_con_derechos)


def _respeta_al_catalogo_falso():
    cc = _cargar_catalogador()
    carpeta = _nuevo()
    ruta = carpeta / "articulos.jsonl"
    filas = [
        {"url": "https://learningenglish.voanews.com/a/x/1.html", "titulo": "VOA", "seccion": "As It Is",
         "licencia": "dominio publico (VOA)", "al_catalogo": True, "texto": "VOA text. " * 60},
        {"url": "https://learningenglish.voanews.com/a/y/2.html", "titulo": "AP", "seccion": "As It Is",
         "licencia": "adaptado de Associated Press: con derechos", "al_catalogo": False,
         "texto": "AP text. " * 60},
    ]
    ruta.write_text("\n".join(json.dumps(f) for f in filas), encoding="utf-8")
    cc.FUENTES = {"voa": ruta}
    df = cc.cargar(None)
    assert df["id"].tolist() == ["VOA1"], df["id"].tolist()
    return "lo adaptado de AP se queda fuera"


prueba("lo interno no entra al catalogo", _respeta_al_catalogo_falso)


def _storyweaver_sin_licencia_no_entra():
    """Auditoria cruzada de e6 (M3): a StoryWeaver se le presumia «CC BY 4.0» si
    faltaba el campo, y la barrera de licencias recibia la presumida."""
    cc = _cargar_catalogador()
    ruta = _nuevo() / "libros.jsonl"
    filas = [
        {"id": 1, "titulo": "Con licencia", "licencia": "CC BY 4.0", "nivel_editor": "1",
         "url": "https://storyweaver.org.in/x/1", "texto": "A free story. " * 60},
        {"id": 2, "titulo": "Sin licencia", "nivel_editor": "1",
         "url": "https://storyweaver.org.in/x/2", "texto": "A story without a licence. " * 60},
    ]
    ruta.write_text("\n".join(json.dumps(f) for f in filas), encoding="utf-8")
    cc.FUENTES = {"storyweaver": ruta}
    try:
        df = cc.cargar(None)
    except SystemExit as e:
        raise AssertionError(f"el registro sin licencia llego hasta la barrera: {e}")
    assert df["id"].tolist() == ["SWV1"], df["id"].tolist()
    assert df["licencia"].tolist() == ["CC BY 4.0"], df["licencia"].tolist()
    return "el de StoryWeaver sin licencia se queda fuera sin abortar; el CC BY 4.0 entra"


prueba("un libro de StoryWeaver sin licencia no entra al catalogo", _storyweaver_sin_licencia_no_entra)


def _dominio_publico_con_excepcion():
    """El otro caso de Codex: una etiqueta que empieza por "dominio publico" pero
    declara material de agencia no puede colarse aunque venga al_catalogo."""
    cc = _cargar_catalogador()
    carpeta = _nuevo()
    ruta = carpeta / "articulos.jsonl"
    fila = {"url": "https://learningenglish.voanews.com/a/z/3.html", "titulo": "Mixto",
            "seccion": "As It Is", "licencia": "dominio publico salvo material adaptado de Reuters",
            "al_catalogo": True, "texto": "Mixed text. " * 60}
    ruta.write_text(json.dumps(fila), encoding="utf-8")
    cc.FUENTES = {"voa": ruta}
    try:
        cc.cargar(None)
    except SystemExit as e:
        assert "licencia no libre" in str(e), e
    else:
        raise AssertionError("una licencia 'dominio publico salvo Reuters' entro al catalogo")
    assert cc.licencia_libre("CC-BY") and cc.licencia_libre("CC BY 4.0")
    assert cc.licencia_libre("CC-BY-3.0"), "CC BY 3.0 es libre y se quedaba fuera"
    assert not cc.licencia_libre("CC-BY-NC-3.0"), "la NC 3.0 no puede colarse junto a la 3.0"
    assert cc.licencia_libre("dominio publico (VOA)")
    assert not cc.licencia_libre("dominio publico (VOA)", {"agencia": "Reuters"})
    assert not cc.licencia_libre("CC-BY-NC-4.0") and not cc.licencia_libre("")
    return "solo etiquetas exactas, y nunca con agencia"


prueba("dominio publico con excepcion no entra", _dominio_publico_con_excepcion)


def _una_obra_una_fila():
    """«The Red Raincoat» estaba en StoryWeaver y en Let's Read con el mismo texto
    y salia dos veces en el buscador. Se queda uno, el de la fuente preferida."""
    cc = _cargar_catalogador()
    carpeta = _nuevo()
    sw = carpeta / "sw.jsonl"
    lr = carpeta / "lr.jsonl"
    texto = "On Sunday, Manu's parents got him a red raincoat. " * 30
    sw.write_text(json.dumps({"id": 369, "slug": "369-the-red-raincoat", "titulo": "The Red Raincoat",
                              "autores": ["Kiran Kasturia"], "licencia": "CC BY 4.0", "al_catalogo": True,
                              "nivel_editor": "1", "url": "https://storyweaver.org.in/x", "texto": texto}),
                  encoding="utf-8")
    lr.write_text(json.dumps({"master": "92e0606f-a5a4", "titulo": "The Red Raincoat ", "autores": ["Kiran Kasturia"],
                              "licencia": "CC-BY-4.0", "al_catalogo": True, "nivel_editor": "2",
                              "url": "https://www.letsreadasia.org/book/the-red-raincoat", "texto": texto}),
                  encoding="utf-8")
    cc.FUENTES = {"letsread": lr, "storyweaver": sw}
    df = cc.cargar(None)
    assert df["id"].tolist() == ["SWV369"], f"la misma obra entra dos veces o gana la fuente equivocada: {df['id'].tolist()}"
    return "una fila por titulo y autor, con StoryWeaver por delante de Let's Read"


prueba("la misma obra en dos bibliotecas entra una sola vez", _una_obra_una_fila)


def _credenciales_sin_falsos_positivos():
    spec = importlib.util.spec_from_file_location("desplegar_app", "tools/desplegar_app.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def salta(texto):
        return any(p.search(texto) for p in mod.CREDENCIALES)

    url = "https://learningenglish.voanews.com/a/cask-of-amontillado-edgar-allan-poe/1234.html"
    assert not salta(url), "la URL de VOA de The Cask of Amontillado parece una clave"
    assert not salta("mask-of-the-red-death-edgar-allan-poe-story-part-one"), "otra URL parece clave"
    assert salta('OPENAI_API_KEY="sk-proj-' + "A1b2C3d4" * 4 + '"'), "una clave sk-proj- no salta"
    assert salta("token = hf_" + "Q" * 30), "un token hf_ no salta"
    return "las URLs con 'sk-' dentro de una palabra no bloquean; las claves si"


prueba("el detector de credenciales no confunde URLs con claves", _credenciales_sin_falsos_positivos)


def _credencial_dentro_de_un_parquet_comprimido():
    """Auditoria cruzada de e6 (D1): el parquet se escaneaba como bytes. Con gzip
    no queda nada legible, y con Snappy una cadena repetida pasa a referencia."""
    spec = importlib.util.spec_from_file_location("desplegar_app", "tools/desplegar_app.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    carpeta = _nuevo()
    clave = "sk-proj-" + "Z9y8X7w6" * 4
    textos = ["Once upon a time there was a quiet harbour. " * 40,
              "The boat drifted slowly. " * 30 + f' OPENAI_API_KEY="{clave}" ' + "The end. " * 30]
    salta = []
    for compresion in ("gzip", "snappy"):
        ruta = carpeta / f"corpus_{compresion}.parquet"
        # Sin estadisticas: pyarrow guarda sin comprimir el minimo y el maximo de
        # cada columna en el pie, y con dos filas el texto de la clave ES el
        # maximo; leido como bytes salia de ahi y la prueba no distinguia nada
        # (mutante C5-parquet-como-bytes vivo, 15 sep 2026). En el corpus real la
        # clave estaria en cualquier fila, dentro de las paginas comprimidas.
        pd.DataFrame({"id": ["A", "B"], "texto": textos}).to_parquet(
            ruta, compression=compresion, index=False, write_statistics=False)
        for contenido in (None, ruta.read_bytes()):
            try:
                mod.revisar(str(ruta), "corpus_abierto.parquet", contenido)
            except SystemExit as e:
                salta.append("credencial" in str(e))
            else:
                salta.append(False)
    assert all(salta) and len(salta) == 4, f"no salta la clave dentro del parquet: {salta}"
    limpio = carpeta / "limpio.parquet"
    pd.DataFrame({"id": ["A"], "texto": [textos[0]]}).to_parquet(limpio, compression="gzip", index=False)
    mod.revisar(str(limpio), "corpus_abierto.parquet", limpio.read_bytes())
    return "la clave salta en gzip y snappy, desde disco y desde los bytes del commit; el limpio pasa"


prueba("una credencial dentro de un parquet comprimido tambien salta",
       _credencial_dentro_de_un_parquet_comprimido)


print()
if FALLOS:
    print(f"{len(FALLOS)} fallo(s) de {HECHAS} pruebas de corpus:")
    for n in FALLOS:
        print(f"- {n}")
    sys.exit(1)
print(f"Todas las pruebas de corpus pasan ({HECHAS}).")
