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
    finally:
        cm.DIR_CACHE = viejo
    return "propio y externo en archivos distintos; cambiar el externo no toca Gutenberg"


prueba("embeddings alineados, y el externo no borra los de Gutenberg", _embeddings_alineados_y_separados)


def _abribles():
    cat = _montar(_nuevo())
    assert cat.es_abrible("PG1342") and cat.es_abrible("swv369")
    assert not cat.es_abrible("SWgdlgdl42"), "un StoryWeaver heredado sin texto sale abrible"
    assert not cat.es_abrible("PG"), "un id sin numero sale abrible"
    t = cat.texto_abierto("SWV369")
    assert t and t["licencia"] == "CC BY 4.0" and "CC BY 4.0" in t["texto"][-60:], t
    return "Gutenberg y corpus libres si; heredado sin texto e id vacio no"


prueba("que se puede abrir y que no", _abribles)


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


print()
if FALLOS:
    print(f"{len(FALLOS)} fallo(s) de {HECHAS} pruebas de corpus:")
    for n in FALLOS:
        print(f"- {n}")
    sys.exit(1)
print(f"Todas las pruebas de corpus pasan ({HECHAS}).")
