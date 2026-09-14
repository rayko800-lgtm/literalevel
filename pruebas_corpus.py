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
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, "app")
os.environ["LITERALEVEL_DATOS"] = tempfile.mkdtemp(prefix="literalevel_corpus_")
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
    return Path(tempfile.mkdtemp(prefix="corpus_"))


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


print()
if FALLOS:
    print(f"{len(FALLOS)} fallo(s) de {HECHAS} pruebas de corpus:")
    for n in FALLOS:
        print(f"- {n}")
    sys.exit(1)
print(f"Todas las pruebas de corpus pasan ({HECHAS}).")
