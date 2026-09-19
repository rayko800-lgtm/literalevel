"""Pruebas de `app/api.py`: la frontera HTTP que usa el cliente Angular.

Lo que se verifica no es que los modulos calculen bien -eso ya lo prueban
`pruebas_extremas.py` y compania- sino que **la API no abre ninguna puerta que
Gradio tenia cerrada**:

- sin `X-Lector` no se toca ningun dato de lector (en la nube eso seria la
  carpeta `lectores/anonimo`, compartida por todos);
- dos lectores no ven el perfil, el cuaderno ni la estanteria del otro;
- un id de libro nunca es una ruta del disco;
- lo que cuesta dinero no sale sin perfil ni sin clave, y tampoco gasta ficha;
- ningun error sale como traza.

Sin red y sin OpenAI: la clave se corta en el origen, como en
`pruebas_extremas.py`. Los libros que se abren son del corpus libre, que trae su
texto en `corpus_abierto.parquet` y no descarga nada.

Uso:  python -X utf8 pruebas_api.py
"""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
import traceback
import uuid
from pathlib import Path

sys.path.insert(0, "app")
# Todas las carpetas temporales se borran al salir (`pruebas_tmp`).
import pruebas_tmp  # noqa: E402
os.environ["LITERALEVEL_DATOS"] = pruebas_tmp.carpeta("literalevel_api_")
# La nube: carpetas por lector. Es el caso que importa, porque en local todos
# comparten la carpeta a proposito y el aislamiento no se veria.
os.environ["SPACE_ID"] = "pruebas/literalevel"
# Simular el Space no puede lanzar la precarga real del buscador (reinicio 26): para_gradio() la arranca.
os.environ.setdefault("LITERALEVEL_PRECARGA", "0")
os.environ.pop("LITERALEVEL_CUENTAS", None)
import config as config_mod  # noqa: E402
config_mod.cargar = lambda *a, **k: None
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import api  # noqa: E402
import ui  # noqa: E402

cliente = TestClient(api.app, raise_server_exceptions=False)
FALLOS: list[str] = []
HECHAS = 0
LIBRE = "SWV369"          # The Red Raincoat, StoryWeaver: sin red


def prueba(nombre: str, fn):
    """Que lance es fallo; devolver `False` tambien (ver `pruebas_extremas.py`)."""
    global HECHAS
    HECHAS += 1
    try:
        r = fn()
        if inspect.isgenerator(r):
            r = list(r)
        assert r is not False, "la prueba devolvio False"
        resumen = str(r)
        print(f"  ok    {nombre:<52} {resumen[:70]}")
    except Exception as e:
        FALLOS.append(f"{nombre}: {type(e).__name__}: {e}")
        print(f"  FALLA {nombre:<52} {type(e).__name__}: {e}")
        traceback.print_exc(limit=3)


def nuevo_lector() -> dict:
    return {"X-Lector": str(uuid.uuid4())}


A, B = nuevo_lector(), nuevo_lector()


def _ok(r, estado=200):
    assert r.status_code == estado, f"{r.status_code}: {r.text[:300]}"
    return r.json()


# --- Identidad -----------------------------------------------------------------

def sin_lector_no_hay_datos():
    for metodo, ruta in (("get", "/api/perfil"), ("get", "/api/inicio"),
                         ("get", "/api/cuaderno"), ("get", "/api/biblioteca"),
                         ("get", f"/api/libros/{LIBRE}"), ("post", "/api/palabra")):
        r = getattr(cliente, metodo)(ruta, **({"json": {"palabra": "coat"}}
                                             if metodo == "post" else {}))
        assert r.status_code in (400, 422), (ruta, r.status_code)
    assert not (ui.BASE_DATOS_LECTOR / "lectores" / "anonimo").exists(), \
        "se creo la carpeta compartida lectores/anonimo"
    return "400 en las seis"


def lector_corto_no_vale():
    r = cliente.get("/api/perfil", headers={"X-Lector": "abc"})
    assert r.status_code == 400
    r = cliente.get("/api/perfil", headers={"X-Lector": "../../" + "x" * 20})
    # Saneado deja 20 letras: vale, pero dentro de lectores/, nunca fuera.
    assert r.status_code == 200
    assert (ui.BASE_DATOS_LECTOR / "lectores" / ("x" * 20)).is_dir()
    assert not (ui.BASE_DATOS_LECTOR.parent / ("x" * 20)).exists()
    return "corto rechazado, traversal saneado"


def perfiles_aislados():
    _ok(cliente.post("/api/perfil/cuestionario", headers=A,
                     json={"respuestas": {"fragmento_medio": 1.2}, "nombre": "Ana"}))
    pa = _ok(cliente.get("/api/perfil", headers=A))["perfil"]
    pb = _ok(cliente.get("/api/perfil", headers=B))["perfil"]
    assert pa and pa["nombre"] == "Ana" and pa["nivel"] == 1.2, pa
    assert pb is None, f"B ve el perfil de A: {pb}"
    return f"A={pa['nivel']} B=None"


# --- Nivel ---------------------------------------------------------------------

def cuestionario_forma():
    d = _ok(cliente.get("/api/cuestionario"))
    assert len(d["preguntas"]) == 6 and len(d["fragmentos"]) == 3
    assert all(o["etiqueta"] and 0 <= o["valor"] <= 2
               for p in d["preguntas"] + d["fragmentos"] for o in p["opciones"])
    return "6 preguntas + 3 fragmentos"


def una_respuesta_estima_sin_guardar():
    lector = nuevo_lector()
    d = _ok(cliente.post("/api/perfil/cuestionario", headers=lector,
                         json={"respuestas": {"frecuencia": 0.8}, "guardar": False}))
    assert d["nivel"] == 0.8 and d["cefr"] == "B1", d
    assert _ok(cliente.get("/api/perfil", headers=lector))["perfil"] is None
    return "estima y no guarda"


def respuestas_de_fuera_se_validan():
    malas = [{"inventada": 1.0}, {"frecuencia": 7}, {"frecuencia": -1},
             {"lecturas": [0.4, 9]}]
    for m in malas:
        r = cliente.post("/api/perfil/cuestionario", headers=A,
                         json={"respuestas": m, "guardar": False})
        assert r.status_code == 422, (m, r.status_code)
    r = cliente.post("/api/perfil/cuestionario", headers=A, json={"respuestas": {}})
    assert r.status_code == 422 and "detail" in r.json()
    return "422 en todas"


def muestra_que_no_es_prosa_no_carga_el_modelo():
    r = cliente.post("/api/perfil/muestra", headers=A,
                     json={"texto": "- uno\n- dos\n- tres\n- cuatro"})
    assert r.status_code == 422
    assert ui._puntuador is None, "cargo 328 MB para decir que no es prosa"
    return r.json()["detail"][:50]


# --- Libros --------------------------------------------------------------------

def id_que_es_ruta_no_pasa():
    for malo in ("..%2F..%2Fetc%2Fpasswd", "C:%5CWindows", "pg1342.txt", "PG", "u123",
                 "SWV369;rm", "%2E%2E"):
        r = cliente.get(f"/api/libros/{malo}", headers=A)
        assert r.status_code == 404, (malo, r.status_code)
    return "404 en las siete"


def abrir_libro_libre():
    d = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=A))
    assert d["id"] == LIBRE and d["capitulos"] and d["titulo"], d
    assert 0 <= d["inicial"] < len(d["capitulos"])
    c = _ok(cliente.get(f"/api/libros/{LIBRE}/capitulos/{d['inicial']}", headers=A))
    assert c["parrafos"] and all(p.strip() for p in c["parrafos"])
    r = cliente.get(f"/api/libros/{LIBRE}/capitulos/9999", headers=A)
    assert r.status_code == 404
    return f"{d['titulo']} · {len(d['capitulos'])} caps"


def progreso_y_estanteria_aislados():
    _ok(cliente.put(f"/api/libros/{LIBRE}/progreso", headers=A, json={"capitulo": 0}))
    ea = _ok(cliente.get("/api/biblioteca", headers=A))["libros"]
    eb = _ok(cliente.get("/api/biblioteca", headers=B))["libros"]
    assert [e["id"] for e in ea] == [LIBRE], ea
    assert eb == [], f"B ve la estanteria de A: {eb}"
    ini = _ok(cliente.get("/api/inicio", headers=A))
    assert ini["seguir"]["id"] == LIBRE and ini["perfil"]["nombre"] == "Ana"
    assert "ruta" not in ini["seguir"], "la ruta del disco sale hacia el cliente"
    return "A la ve, B no"


def progreso_fuera_de_rango():
    r = cliente.put(f"/api/libros/{LIBRE}/progreso", headers=A, json={"capitulo": 500})
    assert r.status_code == 404
    r = cliente.put(f"/api/libros/{LIBRE}/progreso", headers=A, json={"capitulo": -1})
    assert r.status_code == 422
    return "404 y 422"


def subir_txt_y_solo_lo_ve_quien_lo_subio():
    texto = ("It was a quiet morning in the little town. " * 60 + "\n\n") * 3
    d = _ok(cliente.post("/api/libros", headers=A,
                         files={"archivo": ("mio.txt", texto.encode(), "text/plain")}))
    ident = d["id"]
    assert ident.startswith("u") and len(ident) == 17, ident
    assert cliente.get(f"/api/libros/{ident}", headers=B).status_code == 404
    assert cliente.get(f"/api/libros/{ident}", headers=A).status_code == 200
    r = cliente.post("/api/libros", headers=A,
                     files={"archivo": ("malo.exe", b"MZ" * 900, "application/octet-stream")})
    assert r.status_code == 415
    return ident


# --- Palabra y dinero ------------------------------------------------------------

def palabra_sin_clave_no_sale_a_la_red():
    # Si llegara a construir un cliente de OpenAI, esto lo haria saltar.
    import lexicon
    original = lexicon.ConsultorLexico._cliente

    def espia(self):
        raise AssertionError("se intento construir el cliente de OpenAI")

    lexicon.ConsultorLexico._cliente = espia
    try:
        caps = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=A))
        cuerpo = {"palabra": "raincoat", "libro_id": LIBRE, "capitulo": caps["inicial"]}
        d1 = _ok(cliente.post("/api/palabra", headers=A, json={**cuerpo, "etapa": "diccionario"}))
        d2 = _ok(cliente.post("/api/palabra", headers=A, json={**cuerpo, "etapa": "completa"}))
    finally:
        lexicon.ConsultorLexico._cliente = original
    assert d1["explicacion_pendiente"] is False and d1["motivo_sin_explicacion"]
    assert d2["definicion_contextual"] is None
    assert all("OPENAI_API_KEY" not in a for a in d1["avisos"] + d2["avisos"])
    # Palabra del diccionario: la IPA no la escribio la IA, y el campo viaja.
    assert d1["ipa_generada_por_ia"] is False and d2["ipa_generada_por_ia"] is False
    # «raincoat» está entera en el diccionario: no es la parte de un compuesto.
    assert d1["compuesto"] is None and d1["parte_del_diccionario"] is None, d1
    assert isinstance(d1["acepciones_principales"], list) and isinstance(d2["acepciones_principales"], list), d1
    return f"{d1['lema']} · {d1['sentido'] and d1['sentido'][:30]}"


def palabra_larguisima_y_frase():
    r = cliente.post("/api/palabra", headers=A, json={"palabra": "a" * 80})
    assert r.status_code == 422
    r = cliente.post("/api/palabra", headers=A, json={"palabra": "one two three four five"})
    assert r.status_code == 422
    return "422 y 422"


def cuaderno_aislado():
    ca = _ok(cliente.get("/api/cuaderno", headers=A))
    cb = _ok(cliente.get("/api/cuaderno", headers=B))
    # UNA consulta en dos etapas es UNA entrada: la vista previa no apunta.
    assert ca["consultas"] == 1, f"una consulta dejo {ca['consultas']} entradas"
    assert cb["consultas"] == 0 and cb["entradas"] == [], cb
    return f"A={ca['consultas']} B=0"


def lo_de_pago_sin_clave_no_cobra_ni_gasta_ficha():
    ip = "testclient"
    antes = {k: len(v) for k, v in ui._gasto.items() if ip in k}
    r = cliente.post(f"/api/libros/{LIBRE}/sinopsis", headers=A)
    assert r.status_code == 503, r.status_code
    r = cliente.post("/api/voz", headers=A, data={"frase": "The red raincoat."},
                     files={"audio": ("voz.webm", b"\x1a" * 2000, "audio/webm")})
    assert r.status_code == 503, r.status_code
    despues = {k: len(v) for k, v in ui._gasto.items() if ip in k and "descargas" not in k}
    assert all(despues.get(k, 0) == antes.get(k, 0) for k in despues), (antes, despues)
    return "503 y sin fichas gastadas"


def con_perfiles_sin_entrar_no_paga():
    os.environ["LITERALEVEL_CUENTAS"] = "profe:una-clave-larga:3"
    os.environ["OPENAI_API_KEY"] = "sk-falsa-para-pruebas"
    try:
        e = _ok(cliente.get("/api/entrada", headers=B))
        assert e["puerta"] and not e["dentro"], e
        r = cliente.post(f"/api/libros/{LIBRE}/sinopsis", headers=B)
        assert r.status_code == 403, (r.status_code, r.text)
        # El motivo no puede mandar al lector a donde estaba la puerta en Gradio.
        assert "entres con tu perfil" in r.json()["detail"], r.text
        assert "arriba del todo" not in r.json()["detail"], r.text
        mal = _ok(cliente.post("/api/entrar", headers=B,
                               json={"usuario": "profe", "clave": "otra"}))
        assert not mal["dentro"] and mal["mensaje"]
        bien = _ok(cliente.post("/api/entrar", headers=B,
                                json={"usuario": "profe", "clave": "una-clave-larga"}))
        assert bien["dentro"] and bien["nombre"] == "profe" and bien["restantes"] == 3
        # Entrar en B no deja dentro a A.
        assert not _ok(cliente.get("/api/entrada", headers=A))["dentro"]
        fuera = _ok(cliente.post("/api/salir", headers=B))
        assert not fuera["dentro"]
    finally:
        os.environ.pop("LITERALEVEL_CUENTAS", None)
        os.environ.pop("OPENAI_API_KEY", None)
    return "403 sin entrar; la sesion es de B"


# --- Varios --------------------------------------------------------------------

def audio_y_fonemas_sin_traversal():
    for malo in ("..%2F..%2Fcuaderno.db", "cuaderno.db", "x.mp3"):
        assert cliente.get(f"/api/audio/{malo}").status_code == 404, malo
    ga = _ok(cliente.get("/api/fonemas"))
    inv = ga["fonemas"]
    assert ga["acento"] == "ga" and len(inv) == 41, (ga["acento"], len(inv))
    assert all(f["ficha"]["rasgos"] and f["tipo"] in ("vocal", "diptongo", "consonante") for f in inv)
    con_audio = next(f for f in inv if f["audio"])
    # Los mp3 se regeneran con el mismo nombre: sin version, el navegador
    # seguiria sirviendo el viejo durante 30 dias.
    assert "?v=" in con_audio["audio"], con_audio["audio"]
    r = cliente.get(con_audio["audio"])
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg"
    assert cliente.get("/api/fonemas/..%2Fapi.py").status_code == 404

    rp = _ok(cliente.get("/api/fonemas", params={"acento": "rp"}))
    simbolos = {f["simbolo"] for f in rp["fonemas"]}
    assert len(rp["fonemas"]) == 44 and {"ɒ", "ɪə", "eə", "ʊə"} <= simbolos, len(rp["fonemas"])
    assert sum(len(g["sonidos"]) for g in rp["grupos"]) == 44
    assert all(f["audio"] and f["audio"].startswith("/api/fonemas/rp/") for f in rp["fonemas"])
    diptongo = next(f for f in rp["fonemas"] if f["simbolo"] == "ɪə")   # dos puntos de codigo
    r = cliente.get(diptongo["audio"])
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg", diptongo["audio"]
    assert cliente.get("/api/fonemas", params={"acento": "xx"}).status_code == 422
    assert cliente.get("/api/fonemas/rp/..%2F..%2Fapi.py").status_code == 404
    return f"{len(inv)} americanos y {len(rp['fonemas'])} britanicos"


def estado_sin_rutas():
    d = _ok(cliente.get("/api/estado"))
    texto = str(d)
    for pista in (str(ui.RAIZ), "Users", "laura", ".literalevel"):
        assert pista not in texto, f"el estado publico lleva «{pista}»"
    return "sin rutas"


def curva_de_libro_sin_medir():
    d = _ok(cliente.get(f"/api/libros/{LIBRE}/curva", headers=A))
    assert "filas" in d and "trabajo" in d
    assert cliente.get("/api/trabajos/noexiste").status_code == 404
    return d["fuente"]


def cors_del_front():
    r = cliente.options("/api/salud", headers={
        "Origin": "https://mikemaki1763-literalevel-front.static.hf.space",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "x-lector"})
    assert r.headers.get("access-control-allow-origin"), r.headers
    r = cliente.options("/api/salud", headers={
        "Origin": "https://malicioso.example.com", "Access-Control-Request-Method": "GET"})
    assert not r.headers.get("access-control-allow-origin")
    return "static.hf.space sí, otro no"


def libro_con_licencia_abre_en_la_obra():
    """Miguel abrio un libro de Gutenberg y leyo la licencia y «Produced by...»,
    y Pronunciar le propuso leer en alto una frase de los creditos."""
    import re
    cabecera = ("The Project Gutenberg eBook of Pruebas de lectura\n\n"
                "*** START OF THE PROJECT GUTENBERG EBOOK PRUEBAS DE LECTURA ***\n\n"
                "Produced by Alguien Inventado and the Online Distributed Proofreading "
                "Team at https://www.pgdp.net\n\n"
                "PRUEBAS DE LECTURA\n\nCONTENTS.\n\nThe Garden\n\nThe River\n\n")
    parrafo = " ".join(["The old gardener walked slowly along the path beside the quiet river."] * 5)
    # Un indice de UN parrafo largo en mitad del libro, como el de PG56711: pasa
    # el filtro de longitud y no puede acabar propuesto para leer en alto.
    indice = ("VOICE FROM THE PALACE 102 VOICE FROM THE HOVEL 103 VOICE FROM THE BANQUET 105 "
              "VOICE FROM THE GARRET 106 VOICE FROM BENEATH 107 XXIII. ON MY DAUGHTER'S MARRIAGE 117 "
              "XXXII. A DREAM IN SUMMER 94 XIX. ON THE SIXTH CENTENARY OF DANTE 126 XXXV.")
    prosa = "\n\n".join([parrafo] * 10 + [indice] + [parrafo] * 10)
    pie = ("\n\n*** END OF THE PROJECT GUTENBERG EBOOK PRUEBAS DE LECTURA ***\n\n"
           + "The Full Project Gutenberg License applies to this work. " * 80)
    d = _ok(cliente.post("/api/libros", headers=A,
                         files={"archivo": ("licencia.txt", (cabecera + prosa + pie).encode(), "text/plain")}))
    c = _ok(cliente.get(f"/api/libros/{d['id']}/capitulos/{d['inicial']}", headers=A))
    texto = " ".join(c["parrafos"]).lower()
    assert c["parrafos"][0].startswith("The old gardener"), c["parrafos"][:3]
    for sucio in ("produced by", "proofreading", "project gutenberg", "start of the", "contents"):
        assert sucio not in texto, f"el capitulo sigue trayendo «{sucio}»"
    for _ in range(15):
        f = _ok(cliente.get(f"/api/libros/{d['id']}/capitulos/{d['inicial']}/frase", headers=A))["frase"]
        assert f and "produced" not in f.lower() and "gutenberg" not in f.lower(), f
        assert not re.search(r"\d", f), f"frase sacada del indice: {f}"
    return c["parrafos"][0][:40]


def extracto_de_seguir_leyendo_salta_la_licencia():
    """b9, capturas del guion: «Donde lo dejaste» con el progreso en el capítulo 0
    enseñaba como extracto el texto de la licencia de Gutenberg."""
    cabecera = ("The Project Gutenberg eBook of Pruebas de lectura\n\n"
                "*** START OF THE PROJECT GUTENBERG EBOOK PRUEBAS DE LECTURA ***\n\n"
                "Produced by Alguien Inventado and the Online Distributed Proofreading Team at "
                "https://www.pgdp.net. This eBook is for the use of anyone anywhere in the United States "
                "and most other parts of the world at no cost and with almost no restrictions whatsoever.\n\n")
    parrafo = " ".join(["The old gardener walked slowly along the path beside the quiet river."] * 5)
    texto = cabecera + "\n\n".join([parrafo] * 12)
    lector = nuevo_lector()
    dentro = ui._dentro_del_limite
    ui._dentro_del_limite = lambda pet, cubo, tope: True   # la suite ya roza el tope de subidas
    try:
        d = _ok(cliente.post("/api/libros", headers=lector,
                             files={"archivo": ("portadilla.txt", texto.encode(), "text/plain")}))
    finally:
        ui._dentro_del_limite = dentro
    _ok(cliente.put(f"/api/libros/{d['id']}/progreso", headers=lector, json={"capitulo": 0}))
    seguir = _ok(cliente.get("/api/inicio", headers=lector))["seguir"]
    assert seguir and seguir["id"] == d["id"] and seguir["capitulo"] == 0, seguir
    extracto = (seguir.get("extracto") or "").lower()
    assert extracto.startswith("the old gardener"), extracto
    for sucio in ("gutenberg", "produced by", "ebook", "proofreading"):
        assert sucio not in extracto, f"el extracto trae «{sucio}»"
    return extracto[:40]


def errores_con_mensaje_propio_y_no_el_500_generico():
    """Auditoría de Codex (7): recomendar con el catálogo caído, guardar el nivel
    medido con un libro y escribir una subida caían en «Algo ha fallado en el
    servidor». Cada uno tiene que decir qué ha pasado."""
    from pathlib import Path
    from types import SimpleNamespace as NS
    from unittest.mock import patch
    lector = nuevo_lector()
    generico = "Algo ha fallado"

    def roto():
        raise RuntimeError("catalogo roto")

    with patch.object(api, "_perfil_de", lambda pet: NS(nivel=1.0)), patch.object(ui, "catalogo", roto):
        rec = cliente.get("/api/recomendar", headers=lector)
    with patch.object(api, "_puntuar", lambda t: NS(puntuacion=1.0, banda="intermedio")), \
            patch.object(ui, "_muestra_de_libro", lambda lib: "word " * 200), \
            patch.object(api.perfil_mod.Perfil, "guardar", side_effect=OSError("disco lleno")):
        niv = cliente.post("/api/perfil/libro", headers=lector, json={"libro_id": LIBRE})
    texto = ("The tailor sewed a coat for the king by candlelight every evening. " * 50 + "\n\n") * 3
    with patch.object(ui, "_dentro_del_limite", lambda pet, cubo, tope: True), \
            patch.object(Path, "write_bytes", side_effect=OSError("disco lleno")):
        sub = cliente.post("/api/libros", headers=lector, files={"archivo": ("sastre.txt", texto.encode(), "text/plain")})
    resumen = {}
    for nombre, r, estado, frase in (("recomendar", rec, 503, "catálogo"), ("perfil/libro", niv, 500, "guardar tu nivel"),
                                     ("subida", sub, 500, "guardar el libro")):
        detalle = r.json().get("detail", "")
        assert r.status_code == estado and frase in detalle and generico not in detalle, (nombre, r.status_code, detalle)
        resumen[nombre] = r.status_code
    return resumen


def cuento_de_parrafos_cortos_no_pierde_el_principio():
    """El recorte de la portada solo va en el capitulo con la marca de Gutenberg."""
    import re
    d = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=A))
    n = d["inicial"]
    c = _ok(cliente.get(f"/api/libros/{LIBRE}/capitulos/{n}", headers=A))
    # El mismo libro por el mismo camino que la API, y su capitulo EN CRUDO.
    lib = api._cargar_libro(ui._descargar_gutenberg(LIBRE))
    crudo = [" ".join(t.split()) for t in re.split(r"\n\s*\n", lib.capitulos[n].texto)]
    crudo = [t for t in crudo if t]
    assert c["parrafos"] == crudo, (len(c["parrafos"]), len(crudo), c["parrafos"][:2], crudo[:2])
    return f"{len(crudo)} párrafos intactos"


def error_inesperado_sin_traza():
    original = api._perfil_de
    api._perfil_de = lambda pet: (_ for _ in ()).throw(RuntimeError("secreto interno"))
    try:
        r = cliente.get("/api/perfil", headers=A)
    finally:
        api._perfil_de = original
    assert r.status_code == 500 and "secreto" not in r.text and "Traceback" not in r.text
    return r.json()["detail"][:40]


def voz_audio_por_palabra_y_falladas_con_su_frase():
    """La correccion trae el mp3 de cada palabra fallada, y «Mis palabras» la
    devuelve con la frase donde se fallo, solo a ese lector."""
    from types import SimpleNamespace as NS
    import config
    import voz
    lector = nuevo_lector()
    mp3 = api._DIR_AUDIO / f"prueba_{uuid.uuid4().hex[:8]}.mp3"
    mp3.parent.mkdir(parents=True, exist_ok=True)
    mp3.write_bytes(b"ID3" + b"\x00" * 64)
    # «war-chant» se normaliza como una palabra y GPT la parte en «war»: el
    # detalle «war» tiene que llevar el audio del compuesto.
    compuesto = api._DIR_AUDIO / f"prueba_{uuid.uuid4().hex[:8]}.mp3"
    compuesto.write_bytes(b"ID3" + b"\x00" * 64)
    vistas = {}

    def practicar_doble(ruta, frase, guardar_fallos=True, nivel=None, origen=""):
        vistas["frase"] = frase
        ev = NS(puntuacion=60, transcripcion="the red rain coat", palabras_falladas=["raincoat"],
                palabras_objetivo=["the", "red", "raincoat"], entendidas=[])
        corr = NS(resumen="Casi.", detalles=[NS(palabra="Raincoat,", fonema=None,
                                                 sonido_que_falla="la ei", como_colocar_la_boca="abre"),
                                              NS(palabra="war", fonema=None,
                                                 sonido_que_falla="la w", como_colocar_la_boca="redondea"),
                                              NS(palabra="red", fonema="ɹ",
                                                 sonido_que_falla="la r", como_colocar_la_boca="atrás")])
        return NS(evaluacion=ev, transcripcion_ok=True, correccion=corr, audio_correcto=None,
                  audios_palabras={"raincoat": str(mp3), "war-chant": str(compuesto)})

    import fonemas
    acentos = []
    ipa_original = fonemas.ipa_de_palabra

    def ipa_espia(palabra, acento="US"):
        acentos.append(acento)
        return ipa_original(palabra, acento=acento)

    originales = (voz.practicar, config.falta, ui._puede_pagar, api._va_a_costar)
    voz.practicar = practicar_doble
    fonemas.ipa_de_palabra = ipa_espia
    config.falta = lambda: False
    ui._puede_pagar = lambda pet, *a, **k: (True, "")
    api._va_a_costar = lambda pet: False
    try:
        r = _ok(cliente.post("/api/voz", headers=lector, data={"frase": "The red raincoat.", "acento": "UK"},
                             files={"audio": ("voz.webm", b"\x1a" * 2000, "audio/webm")}))
        malo = cliente.post("/api/voz", headers=lector, data={"frase": "x y z.", "acento": "FR"},
                            files={"audio": ("voz.webm", b"\x1a" * 2000, "audio/webm")})
    finally:
        voz.practicar, config.falta, ui._puede_pagar, api._va_a_costar = originales
        fonemas.ipa_de_palabra = ipa_original
        mp3.unlink(missing_ok=True)
        compuesto.unlink(missing_ok=True)
    # Un solo acento, el pedido, para todas las palabras de la corrección.
    assert acentos == ["UK", "UK", "UK"], acentos
    # Y el sonido que falla, en británico: /ɹ/ americano es /r/ en RP.
    assert r["detalles"][2]["fonema"]["simbolo"] == "r" and r["detalles"][2]["fonema"]["acento"] == "rp", r["detalles"][2]
    assert malo.status_code == 422, malo.status_code
    assert vistas.get("frase") == "The red raincoat.", "no llego a corregir"
    assert r["detalles"][0]["audio"] == f"/api/audio/{mp3.name}", r["detalles"]
    assert r["detalles"][1]["audio"] == f"/api/audio/{compuesto.name}", r["detalles"]
    f = _ok(cliente.get("/api/voz/falladas", headers=lector))["palabras"]
    assert [(x["palabra"], x["fallos"], x["frase"]) for x in f] == [("raincoat", 1, "The red raincoat.")], f
    assert _ok(cliente.get("/api/voz/falladas", headers=B))["palabras"] == []
    return f"audio {r['detalles'][0]['audio'][:24]}… · falladas 1 con frase"


def voz_prepara_temporal_antes_de_cobrar():
    """Un fallo local previo a voz no cobra; denegar el pago limpia el audio."""
    from contextlib import contextmanager
    from unittest.mock import patch

    mkstemp_real, fdopen_real = tempfile.mkstemp, os.fdopen
    creados, reservas = [], []

    def reservar(pet, *a, **k):
        reservas.append(1)
        return False, "Cupo agotado."

    def sin_proveedor(*a, **k):
        raise AssertionError("no debe entrar en voz.practicar")

    with tempfile.TemporaryDirectory(prefix="ll_api_audio_prueba_") as carpeta:
        def crear(*a, **k):
            fd, ruta = mkstemp_real(*a, dir=carpeta, **k)
            creados.append(Path(ruta))
            return fd, ruta

        @contextmanager
        def escritura_rota(fd, modo):
            with fdopen_real(fd, modo):
                class ArchivoRoto:
                    def write(self, contenido):
                        raise OSError("detalle privado de disco")
                yield ArchivoRoto()

        def pedir():
            return cliente.post("/api/voz", headers=nuevo_lector(),
                                data={"frase": "The red raincoat."},
                                files={"audio": ("voz.webm", b"x" * 2000, "audio/webm")})

        with patch.object(api.config, "falta", return_value=[]), \
                patch.object(api, "_va_a_costar", return_value=False), \
                patch.object(ui, "_puede_pagar", side_effect=reservar), \
                patch.object(api.voz, "practicar", side_effect=sin_proveedor) as motor:
            with patch.object(api.tempfile, "mkstemp", side_effect=OSError("detalle privado de disco")):
                sin_temporal = pedir()
            assert sin_temporal.status_code == 500 and not reservas, sin_temporal.text
            assert "detalle privado" not in sin_temporal.text

            with patch.object(api.tempfile, "mkstemp", side_effect=crear), \
                    patch.object(api.os, "fdopen", side_effect=escritura_rota):
                sin_escritura = pedir()
            assert sin_escritura.status_code == 500 and not reservas, sin_escritura.text
            assert "detalle privado" not in sin_escritura.text
            assert creados and all(not p.exists() for p in creados), creados

            with patch.object(api.tempfile, "mkstemp", side_effect=crear):
                sin_cupo = pedir()
            assert sin_cupo.status_code == 403 and len(reservas) == 1, sin_cupo.text
            assert len(creados) == 2 and all(not p.exists() for p in creados), creados
            assert motor.call_count == 0, motor.call_count
    return "crear/escribir: 500 sin cobro; cupo: 403; temporales borrados"


def dudoso_coherente_con_el_aviso_de_lexicon():
    """«house»: lexicon marcaba la acepción provisional y `dudoso` salía falso,
    así que la ficha decía a la vez que era dudosa y que no."""
    from types import SimpleNamespace as NS
    base = dict(similitud=0.9, n_sentidos_candidatos=3, audio_generado=True,
                ipa_uk=None, ipa_us="/haʊs/", audio_uk=None, audio_us=None)
    # Con otro aviso al lado, que tiene que sobrevivir: sin él, una lista vacía
    # no distingue «filtró el provisional» de «tiró todos».
    prov = NS(avisos=["acepcion provisional: margen bajo (0.01)", "sin audio en el diccionario"], **base)
    limpio = NS(avisos=[], **base)
    baja = NS(avisos=[], **{**base, "similitud": 0.0})
    assert api._es_dudoso(prov, "completa", True) is True
    assert api._es_dudoso(prov, "diccionario", False) is True
    assert api._es_dudoso(limpio, "completa", True) is False
    assert api._es_dudoso(baja, "completa", False) is True
    # En la vista previa, con la explicación en camino, OpenAI revisa la acepción.
    assert api._es_dudoso(prov, "diccionario", True) is False
    avisos = api._avisos_palabra(prov, "es", quitar_sin_clave=True)
    # `ui._humanizar` lo reescribe como «La acepción elegida es dudosa…».
    assert len(avisos) == 1 and not any("dudosa" in a or "provisional" in a for a in avisos), avisos
    return "provisional -> dudoso; vista previa con explicación en camino -> no"


def fonema_de_la_correccion_en_britanico():
    """Con acento UK, el sonido que falla y su audio son los de RP; /ɝ/ y /ɚ/,
    sin equivalente, se quedan en americano en vez de reventar."""
    us, uk = api._fonema_json("ɹ", "US"), api._fonema_json("ɹ", "UK")
    assert (us["simbolo"], us["acento"]) == ("ɹ", "ga"), us
    assert (uk["simbolo"], uk["acento"]) == ("r", "rp"), uk
    assert uk["audio"] is None or uk["audio"].startswith("/api/fonemas/rp/"), uk
    assert api._fonema_json("oʊ", "UK")["simbolo"] == "əʊ"
    assert api._fonema_json("θ", "UK")["simbolo"] == "θ"
    for sin_rp in ("ɝ", "ɚ"):     # «bird», «butter»
        x = api._fonema_json(sin_rp, "UK")
        assert x is not None and (x["simbolo"], x["acento"]) == (sin_rp, "ga"), x
    return f"ɹ→r, oʊ→əʊ; ɝ ɚ en americano; audio rp {uk['audio'] and uk['audio'][:22]}"


def subida_grande_se_corta_antes_de_leerla_entera():
    """Revisión de 4e (3): con File(...) Starlette leía el cuerpo entero y lo
    volcaba a disco antes del 413. Ahora el multipart no llega a interpretarse."""
    from starlette import formparsers
    interpretados = []
    original = formparsers.MultiPartParser.parse

    async def espia(self):
        interpretados.append(1)
        return await original(self)

    frontera = "limite-de-prueba"

    def troceado(tamano):
        yield (f"--{frontera}\r\nContent-Disposition: form-data; name=\"archivo\"; filename=\"enorme.txt\"\r\n"
               "Content-Type: text/plain\r\n\r\n").encode()
        for _ in range(tamano // (1 << 20) + 1):
            yield b"x" * (1 << 20)
        yield f"\r\n--{frontera}--\r\n".encode()

    formparsers.MultiPartParser.parse = espia
    try:
        con_largo = cliente.post("/api/libros", headers=nuevo_lector(),
                                 files={"archivo": ("enorme.txt", b"x" * (api._TOPE_SUBIDA + 200_000), "text/plain")})
        voz_larga = cliente.post("/api/voz", headers=nuevo_lector(), data={"frase": "Hello there."},
                                 files={"audio": ("v.webm", b"\x1a" * (api._TOPE_AUDIO + 200_000), "audio/webm")})
        # Sin Content-Length (troceado): el tope tiene que saltar leyendo.
        sin_largo = cliente.post("/api/libros", headers={**nuevo_lector(),
                                 "content-type": f"multipart/form-data; boundary={frontera}"},
                                 content=troceado(api._TOPE_SUBIDA + (2 << 20)))
    finally:
        formparsers.MultiPartParser.parse = original
    estados = (con_largo.status_code, voz_larga.status_code, sin_largo.status_code)
    assert estados == (413, 413, 413), estados
    assert interpretados == [], f"se interpretó el multipart {len(interpretados)} veces antes del 413"
    return "413 x3 sin interpretar el formulario"


def topes_de_subidas_por_lector_y_por_hora():
    texto = ("It was a quiet morning in the little town. " * 60 + "\n\n") * 3
    lector = nuevo_lector()
    maximo, dentro = api._MAX_SUBIDOS, ui._dentro_del_limite
    api._MAX_SUBIDOS = 1
    try:
        primero = cliente.post("/api/libros", headers=lector, files={"archivo": ("a.txt", texto.encode(), "text/plain")})
        mismo = cliente.post("/api/libros", headers=lector, files={"archivo": ("a.txt", texto.encode(), "text/plain")})
        otro = cliente.post("/api/libros", headers=lector,
                            files={"archivo": ("b.txt", (texto + " And then it rained.").encode(), "text/plain")})
        ui._dentro_del_limite = lambda pet, cubo, tope: cubo != "subidas"
        por_hora = cliente.post("/api/libros", headers=nuevo_lector(), files={"archivo": ("c.txt", texto.encode(), "text/plain")})
    finally:
        api._MAX_SUBIDOS, ui._dentro_del_limite = maximo, dentro
    # Volver a subir el mismo libro no cuenta como uno más.
    estados = (primero.status_code, mismo.status_code, otro.status_code, por_hora.status_code)
    assert estados == (200, 200, 429, 429), estados
    return "1.º 200, el mismo 200, otro 429, sin cubo 429"


def palabra_que_falla_solo_devuelve_lo_cobrado():
    """Revisión de 4e (5): si consultar lanza, se devolvía un uso aunque no se
    hubiera cobrado."""
    import config
    import cuentas
    devueltos = []

    class Roto:
        def consultar(self, *a, **k):
            raise RuntimeError("diccionario caído")

    originales = (config.falta, api._cobrar, api._va_a_costar, ui.consultor, cuentas.devolver)
    cuentas.devolver = lambda base, codigo: devueltos.append(codigo)
    ui.consultor = lambda: Roto()
    api._va_a_costar = lambda pet: False
    config.falta = lambda: False
    cuerpo = {"palabra": "house", "etapa": "completa"}
    try:
        api._cobrar = lambda pet: (False, "Entra con tu perfil.", None)
        sin_cobro = cliente.post("/api/palabra", headers=A, json=cuerpo)
        devueltos_sin_cobro = len(devueltos)
        api._cobrar = lambda pet: (True, "", "cuenta-prueba")
        con_cobro = cliente.post("/api/palabra", headers=A, json=cuerpo)
    finally:
        config.falta, api._cobrar, api._va_a_costar, ui.consultor, cuentas.devolver = originales
    assert (sin_cobro.status_code, con_cobro.status_code) == (503, 503), (sin_cobro.status_code, con_cobro.status_code)
    assert devueltos_sin_cobro == 0, "devolvió un uso que no se cobró"
    assert len(devueltos) == 1, devueltos
    return "sin cobro 0 devueltos, con cobro 1"


def devolucion_va_a_la_cuenta_cobrada():
    """Auditoría de Codex (2): se cobra a la cuenta A y, a mitad de consulta,
    otra pestaña sale y entra con B. La devolución tiene que ir a A."""
    import config
    import cuentas
    quien = {"codigo": "cuenta-A"}
    cobros, devueltos, estados = [], [], []
    real = ui.consultor()

    class CambiaDeCuenta:
        def __init__(self, lanzar):
            self.lanzar = lanzar

        def consultar(self, *a, **k):
            quien["codigo"] = "cuenta-B"
            if self.lanzar:
                raise RuntimeError("diccionario caído")
            return real.consultar(*a, **{**k, "usar_openai": False})

    originales = (config.falta, api._va_a_costar, ui.consultor, ui._codigo_de, cuentas.consumir, cuentas.devolver)
    config.falta = lambda: False
    api._va_a_costar = lambda pet: False
    ui._codigo_de = lambda pet: quien["codigo"]
    cuentas.consumir = lambda base, codigo: (cobros.append(codigo), (True, ""))[1]
    cuentas.devolver = lambda base, codigo: devueltos.append(codigo)
    try:
        # Una consulta que falla y otra sin llamadas de pago: las dos devuelven.
        for lanzar in (True, False):
            quien["codigo"] = "cuenta-A"
            ui.consultor = (lambda l: (lambda: CambiaDeCuenta(l)))(lanzar)
            estados.append(cliente.post("/api/palabra", headers=nuevo_lector(),
                                        json={"palabra": "raincoat", "etapa": "completa"}).status_code)
    finally:
        config.falta, api._va_a_costar, ui.consultor, ui._codigo_de, cuentas.consumir, cuentas.devolver = originales
    assert estados == [503, 200], estados
    assert cobros == ["cuenta-A", "cuenta-A"], cobros
    assert devueltos == ["cuenta-A", "cuenta-A"], devueltos
    return "cobrado y devuelto a A aunque la sesión pasó a B"


def sinopsis_simultaneas_una_generacion():
    """Auditoría de Codex (1): dos peticiones a la vez del mismo libro sin
    sinopsis guardada cobraban y generaban las dos."""
    import tempfile
    import threading
    import time
    from pathlib import Path
    from types import SimpleNamespace as NS
    import config
    guardadas, generaciones, cobros, respuestas = {}, [], [], []

    def generar(lib, cli):
        time.sleep(0.4)
        generaciones.append(1)
        datos = {"de_que_trata": "Una historia de prueba."}
        guardadas["sinopsis"] = datos
        return datos, None

    carpeta = Path(pruebas_tmp.carpeta("ll_sinopsis_"))
    originales = (config.falta, api._va_a_costar, api._cobrar, ui.consultor, ui._sinopsis_guardada,
                  ui.RUTA_ANALISIS, api.ficha.sinopsis)
    config.falta = lambda: False
    api._va_a_costar = lambda pet: False
    api._cobrar = lambda pet: (cobros.append(1), (True, "", "cuenta-A"))[1]
    ui.consultor = lambda: NS(_cliente=lambda: object())
    ui._sinopsis_guardada = lambda lib: guardadas.get("sinopsis")
    ui.RUTA_ANALISIS = carpeta
    api.ficha.sinopsis = generar
    try:
        hilos = [threading.Thread(target=lambda: respuestas.append(
            cliente.post(f"/api/libros/{LIBRE}/sinopsis", headers=A))) for _ in range(2)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(10)
    finally:
        (config.falta, api._va_a_costar, api._cobrar, ui.consultor, ui._sinopsis_guardada,
         ui.RUTA_ANALISIS, api.ficha.sinopsis) = originales
    assert [r.status_code for r in respuestas] == [200, 200], [r.status_code for r in respuestas]
    assert len(generaciones) == 1 and len(cobros) == 1, (generaciones, cobros)
    return "2 peticiones, 1 generación, 1 cobro"


def borrar_subido_libera_el_cupo():
    """Auditoría de Codex (4): «Mis libros» quitaba la entrada pero el archivo
    seguía contando para el tope, y el 429 no se iba nunca."""
    texto = ("The miller's daughter walked to the market every morning. " * 50 + "\n\n") * 3
    lector = nuevo_lector()
    maximo = api._MAX_SUBIDOS
    api._MAX_SUBIDOS = 1
    try:
        a = _ok(cliente.post("/api/libros", headers=lector, files={"archivo": ("uno.txt", texto.encode(), "text/plain")}))
        _ok(cliente.put(f"/api/libros/{a['id']}/progreso", headers=lector, json={"capitulo": 0}))
        lleno = cliente.post("/api/libros", headers=lector,
                             files={"archivo": ("dos.txt", (texto + " Fin.").encode(), "text/plain")})
        ajeno = cliente.delete(f"/api/libros/{a['id']}", headers=nuevo_lector())
        del_catalogo = cliente.delete(f"/api/libros/{LIBRE}", headers=lector)
        borrado = cliente.delete(f"/api/libros/{a['id']}", headers=lector)
        estanteria = _ok(cliente.get("/api/biblioteca", headers=lector))["libros"]
        otro = cliente.post("/api/libros", headers=lector,
                            files={"archivo": ("dos.txt", (texto + " Fin.").encode(), "text/plain")})
    finally:
        api._MAX_SUBIDOS = maximo
    estados = (lleno.status_code, ajeno.status_code, del_catalogo.status_code, borrado.status_code, otro.status_code)
    assert estados == (429, 404, 400, 200, 200), estados
    assert all(e["id"] != a["id"] for e in estanteria), estanteria
    assert cliente.get(f"/api/libros/{a['id']}", headers=lector).status_code == 404
    return "lleno 429, ajeno 404, catálogo 400, borrado 200 y cabe otro"


def historial_de_voz_ilegible_avisa():
    """4e (d765ee0): con voz.db corrupta, voz lanza HistorialIlegible. Las tres
    rutas contestan 200 con el aviso en español, no un 500 ni una lista vacía
    que diga «no has fallado nada». Sin base, sin aviso."""
    from pathlib import Path
    from types import SimpleNamespace as NS
    lector = nuevo_lector()
    ruta = Path(ui._archivo_lector("voz.db", NS(session_hash=lector["X-Lector"], headers={}, client=None)))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(b"esto no es una base de datos sqlite\n" * 40)
    deb = cliente.get("/api/voz/debiles", headers=lector)
    fal = cliente.get("/api/voz/falladas", headers=lector)
    rep = cliente.get("/api/repaso", headers=lector)
    assert (deb.status_code, fal.status_code, rep.status_code) == (200, 200, 200), (deb.text[:200], fal.text[:200], rep.text[:200])
    for r in (deb.json(), fal.json()):
        assert r["palabras"] == [] and r["aviso"], r
    assert rep.json()["voz"] == [] and rep.json()["aviso_voz"] and "palabras" in rep.json(), rep.json()
    limpio = _ok(cliente.get("/api/voz/falladas", headers=nuevo_lector()))
    assert limpio["palabras"] == [] and limpio["aviso"] is None, limpio
    return deb.json()["aviso"][:60]


def cita_recorta_sin_perder_la_oracion():
    """4e (1a4b998) y central: «cita» es el fragmento para enseñar; «oracion»
    sigue entera en la ficha y en el cuaderno."""
    larga = ("The old man walked slowly along the river bank while the children followed him laughing "
             "and the red raincoat that his wife had sewn for him many years ago shone in the rain "
             "and the dogs barked at the geese and the baker waved from his door and nobody in the "
             "village could remember a wetter spring than that one")
    lector = nuevo_lector()
    d = _ok(cliente.post("/api/palabra", headers=lector,
                         json={"palabra": "raincoat", "oracion": larga, "etapa": "completa"}))
    assert len(d["oracion"].split()) > 40, d["oracion"]
    palabras_cita = len(d["cita"].split())
    assert "raincoat" in d["cita"] and palabras_cita <= 32 and palabras_cita < len(d["oracion"].split()), d["cita"]
    entrada = next(e for e in _ok(cliente.get("/api/cuaderno", headers=lector))["entradas"]
                   if e["palabra"].lower() == "raincoat")
    assert entrada["oracion"] == d["oracion"] and entrada["cita"] == d["cita"], entrada
    return f"oración {len(d['oracion'].split())} palabras → cita {palabras_cita}"


def libro_subido_se_ve_con_su_nombre():
    """f4: «Estimado con «d139e28e2c2f7f80.txt»», el nombre interno del archivo."""
    texto = ("The lighthouse keeper watched the storm roll over the bay. " * 50 + "\n\n") * 3
    lector = nuevo_lector()
    d = _ok(cliente.post("/api/libros", headers=lector,
                         files={"archivo": ("Mi novela favorita.txt", texto.encode(), "text/plain")}))
    assert d["titulo"] == "Mi novela favorita", d["titulo"]
    # Sin la caché de memoria: volver a abrirlo tiene que leer el nombre guardado,
    # no reutilizar el objeto que la subida ya dejó con el título puesto.
    api._LIBROS.clear()
    otra_vez = _ok(cliente.get(f"/api/libros/{d['id']}", headers=lector))
    assert otra_vez["titulo"] == "Mi novela favorita", otra_vez["titulo"]
    return d["titulo"]


def palabra_escrita_no_se_atribuye_al_libro():
    """f4: «war-chant» escrita en «Consultar otra palabra» quedaba en el cuaderno
    como de «Alice…, cap. 2» con la frase «war-chant»."""
    lector = nuevo_lector()
    caps = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=lector))
    base = {"libro_id": LIBRE, "capitulo": caps["inicial"], "etapa": "completa"}
    _ok(cliente.post("/api/palabra", headers=lector, json={**base, "palabra": "xylophone"}))
    _ok(cliente.post("/api/palabra", headers=lector, json={**base, "palabra": "raincoat"}))
    entradas = {e["palabra"].lower(): e for e in _ok(cliente.get("/api/cuaderno", headers=lector))["entradas"]}
    assert {"xylophone", "raincoat"} <= set(entradas), list(entradas)
    fuera = entradas["xylophone"]
    assert fuera["libro"] is None and fuera["capitulo"] is None, fuera
    # La que sí sale del capítulo conserva su libro: el arreglo no borra lo bueno.
    dentro = entradas["raincoat"]
    assert dentro["libro"] and dentro["capitulo"], dentro
    return f"escrita sin libro; «raincoat» en {dentro['libro']}, cap. {dentro['capitulo']}"


def aviso_de_contenido_en_ficha_y_tarjeta():
    """Contrato con f4 (catalogo.py de8a4a8): la nota viaja en la ficha y en la
    tarjeta; sin aviso, null."""
    from types import SimpleNamespace as NS
    cat = ui.catalogo()
    # El dato real del CSV: PG17824 lleva nota; SWV369 no.
    assert cat.aviso_de("PG17824"), "PG17824 debería llevar aviso en avisos_contenido.csv"
    assert not cat.aviso_de(LIBRE)
    original = cat.aviso_de
    try:
        cat.aviso_de = lambda i: "Nota de prueba." if str(i).upper() == LIBRE else None
        con = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=A))
        cat.aviso_de = lambda i: None
        sin = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=A))
    finally:
        cat.aviso_de = original
    assert con["aviso_contenido"] == "Nota de prueba.", con["aviso_contenido"]
    assert sin["aviso_contenido"] is None, sin["aviso_contenido"]
    base = dict(id=LIBRE, titulo="t", autor="a", nivel="B1", dificultad=1.0, gancho="", descargas=1,
                similitud=0.5, afinidad=0.1, url_gutenberg="u")
    assert api._libro_tarjeta(NS(**base, aviso_contenido="Nota de prueba."))["aviso_contenido"] == "Nota de prueba."
    assert api._libro_tarjeta(NS(**base, aviso_contenido=""))["aviso_contenido"] is None
    return "ficha y tarjeta con nota; sin aviso, null"


def medido_en_bloque_en_ficha_y_tarjeta():
    """Contrato con f4 (reinicio 14): un texto libre corto medido dentro de un
    bloque lleva «medido_en_bloque» true en la ficha y en la tarjeta; Gutenberg y
    los medidos solos, false."""
    from types import SimpleNamespace as NS
    cat = ui.catalogo()
    original = cat.medida_de
    try:
        cat.medida_de = lambda i: "bloque" if str(i).upper() == LIBRE else "texto"
        con = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=A))
        cat.medida_de = lambda i: "texto"
        sin = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=A))
    finally:
        cat.medida_de = original
    assert con["medido_en_bloque"] is True, con.get("medido_en_bloque")
    assert sin["medido_en_bloque"] is False, sin.get("medido_en_bloque")
    base = dict(id=LIBRE, titulo="t", autor="a", nivel="B1", dificultad=1.0, gancho="", descargas=1,
                similitud=0.5, afinidad=0.1, url_gutenberg="u", aviso_contenido="")
    assert api._libro_tarjeta(NS(**base, medida="bloque"))["medido_en_bloque"] is True
    assert api._libro_tarjeta(NS(**base, medida="texto"))["medido_en_bloque"] is False
    assert api._libro_tarjeta(NS(**base))["medido_en_bloque"] is False, "sin medida (Gutenberg) no es bloque"
    return "ficha y tarjeta: bloque true; solo y Gutenberg false"


def buscar_devuelve_la_franja_y_la_marca():
    """Contrato con e6 (reinicio 23): /api/buscar pide la franja al catalogo, lleva
    `franja` [lo, hi] en milesimas con nivel y null sin el, y `por_franja` en cada
    tarjeta, siempre presente."""
    from types import SimpleNamespace as NS
    base = dict(titulo="t", autor="a", nivel="B1", dificultad=1.0, gancho="", descargas=1,
                similitud=0.5, afinidad=0.1, url_gutenberg="u", aviso_contenido="", medida="texto")
    pedidas = []

    def buscar(consulta, nivel_lector=None, n=10, franja=False, **k):
        pedidas.append((nivel_lector, franja))
        return [NS(id="PG1342", por_franja=False, **base),
                NS(id=LIBRE, por_franja=bool(franja and nivel_lector is not None), **base)], ""

    cat = ui.catalogo()
    original = cat.buscar
    try:
        cat.buscar = buscar
        con = _ok(cliente.post("/api/buscar", headers=nuevo_lector(),
                               json={"consulta": "fantasmas", "nivel": 0.7999999999999998}))
        sin = _ok(cliente.post("/api/buscar", headers=nuevo_lector(), json={"consulta": "fantasmas", "ajustar": False}))
    finally:
        cat.buscar = original
    assert con["franja"] == [0.35, 1.25], con["franja"]
    assert sin["franja"] is None, sin["franja"]
    assert [r["por_franja"] for r in con["resultados"]] == [False, True], con["resultados"]
    assert [r["por_franja"] for r in sin["resultados"]] == [False, False], sin["resultados"]
    assert pedidas == [(0.7999999999999998, True), (None, True)], pedidas
    assert api._libro_tarjeta(NS(id=LIBRE, **base))["por_franja"] is False, "sin el atributo, false"
    return "franja [0,35, 1,25] con nivel y null sin el; por_franja en cada tarjeta"


def precarga_y_peticion_comparten_el_catalogo():
    """Central, reinicio 26: la precarga del buscador va en un hilo al arrancar el Space. Una
    peticion que llega a mitad espera a la MISMA instancia en el candado de ui.catalogo(): el
    constructor se llama una vez. Sin SPACE_ID ni LITERALEVEL_PRECARGA=1 no arranca, y el Space la
    lanza desde para_gradio(). /api/estado lleva la memoria del proceso."""
    import threading
    import time
    from unittest.mock import patch

    construidos = []

    class Lento:
        embeddings = None

        def __init__(self):
            construidos.append(self)
            time.sleep(0.5)

        def buscar(self, *a, **k):
            return [], ""

        def emb_titulos(self):
            return None

    entorno = {k: os.environ.pop(k) for k in ("SPACE_ID", "LITERALEVEL_PRECARGA") if k in os.environ}
    viejo_cat, vieja_clase = ui._catalogo, ui.Catalogo
    ui._catalogo, ui.Catalogo = None, Lento
    try:
        assert api.precargar_en_segundo_plano() is None, "sin variables no se precarga"
        os.environ["SPACE_ID"], os.environ["LITERALEVEL_PRECARGA"] = "pruebas/literalevel", "0"
        assert api.precargar_en_segundo_plano() is None, "LITERALEVEL_PRECARGA=0 no la apaga con SPACE_ID"
        os.environ.pop("SPACE_ID")
        os.environ["LITERALEVEL_PRECARGA"] = "1"
        hilo = api.precargar_en_segundo_plano()
        time.sleep(0.05)
        desde_peticion = ui.catalogo()
        hilo.join(5)
        desde_hilo = ui._catalogo
    finally:
        ui._catalogo, ui.Catalogo = viejo_cat, vieja_clase
        os.environ.pop("LITERALEVEL_PRECARGA", None)
        os.environ.update(entorno)
    assert hilo is not None and not hilo.is_alive(), "el hilo de precarga no acaba"
    assert len(construidos) == 1, f"{len(construidos)} catalogos construidos a la vez"
    assert desde_peticion is desde_hilo is construidos[0], "la peticion y la precarga no comparten instancia"
    llamadas = []
    with patch.object(api, "precargar_en_segundo_plano", lambda: llamadas.append(1)):
        api.para_gradio()
    assert llamadas == [1], f"para_gradio lanza la precarga {len(llamadas)} veces"
    proceso = _ok(cliente.get("/api/estado", headers=nuevo_lector())).get("proceso")
    assert isinstance(proceso, dict) and set(proceso) == {"memoria_mb", "pico_mb"}, proceso
    return f"una instancia para hilo y peticion; sin variables no arranca; para_gradio la lanza; memoria {proceso}"


def silencio_devuelve_el_uso_con_tope_diario():
    """Central, reinicio 26: una grabacion en la que whisper responde sin voz devuelve el uso,
    por cuenta y con 10 al dia; el 11 no devuelve. Otro dia empieza de cero. Una cuenta sin
    tope no tiene nada que devolver. Veinte devoluciones a la vez dejan el contador exacto."""
    import json
    import threading
    import cuentas

    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    os.environ["LITERALEVEL_CUENTAS"] = "jefe:LLAVE-A:0,invitado:LLAVE-B:40"
    try:
        with tempfile.TemporaryDirectory(prefix="ll_devol_") as carpeta:
            base = Path(carpeta)
            for _ in range(12):
                assert cuentas.consumir(base, "invitado:LLAVE-B")[0]
            hechas = [cuentas.devolver_por_silencio(base, "invitado:LLAVE-B", hoy="2026-09-15") for _ in range(11)]
            assert hechas == [True] * 10 + [False], hechas
            assert cuentas.gastado(base, "invitado") == 2, cuentas.gastado(base, "invitado")
            assert cuentas.devolver_por_silencio(base, "invitado:LLAVE-B", hoy="2026-09-16") is True, "otro dia"
            assert cuentas.gastado(base, "invitado") == 1
            assert cuentas.devolver_por_silencio(base, "jefe:LLAVE-A", hoy="2026-09-16") is False, "sin tope"
            assert cuentas.devolver_por_silencio(base, None, hoy="2026-09-16") is False, "sin codigo"
        with tempfile.TemporaryDirectory(prefix="ll_devol_hilos_") as carpeta:
            base = Path(carpeta)
            for _ in range(20):
                cuentas.consumir(base, "invitado:LLAVE-B")
            devueltas = []

            def devolver():
                if cuentas.devolver_por_silencio(base, "invitado:LLAVE-B", hoy="2026-09-15"):
                    devueltas.append(1)
            hilos = [threading.Thread(target=devolver) for _ in range(20)]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
            registro = json.loads((base / "devoluciones_silencio.json").read_text(encoding="utf-8"))
            assert len(devueltas) == 10, f"{len(devueltas)} devueltas de 20 a la vez"
            assert cuentas.gastado(base, "invitado") == 10, cuentas.gastado(base, "invitado")
            assert registro == {"2026-09-15": {"invitado": 20}}, registro
    finally:
        if viejo is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo
    return "10 al dia y el 11 no; otro dia de cero; sin tope ni codigo, no; 20 a la vez, 10 y contador exacto"


def voz_sin_voz_devuelve_a_la_cuenta_cobrada():
    """/api/voz devuelve el uso solo si whisper respondio sin voz (`sin_voz`), a la cuenta cobrada, y
    lo dice en `uso_devuelto`. Con la red caida o con voz, no. Pasa origen="api" a voz.practicar."""
    from types import SimpleNamespace as NS
    from unittest.mock import patch

    llamadas, origenes = [], []

    def sesion(sin_voz, ok):
        ev = NS(palabras_falladas=[], puntuacion=0, transcripcion="", palabras_objetivo=["the", "cat"], entendidas=[])
        return NS(evaluacion=ev, transcripcion_ok=ok, correccion=None, audio_correcto=None,
                  audios_palabras={}, ritmo=None, sin_voz=sin_voz)

    resultados = {}
    for caso, (sin_voz, ok) in {"silencio": (True, False), "red": (False, False), "voz": (False, True)}.items():
        def practicar(ruta, frase, guardar_fallos=True, nivel=None, origen="", _s=sesion(sin_voz, ok)):
            origenes.append(origen)
            return _s
        with patch.object(api.config, "falta", return_value=[]), \
                patch.object(api, "_va_a_costar", return_value=False), \
                patch.object(ui, "_codigo_de", lambda pet: "invitado:LLAVE-B"), \
                patch.object(ui, "_puede_pagar", lambda pet, *a, **k: (True, "")), \
                patch.object(api.voz, "practicar", practicar), \
                patch.object(api.cuentas, "devolver_por_silencio",
                             lambda base, codigo, hoy=None: (llamadas.append((caso, codigo)), True)[1]):
            r = cliente.post("/api/voz", headers=nuevo_lector(), data={"frase": "The cat."},
                             files={"audio": ("voz.webm", b"x" * 2000, "audio/webm")})
        assert r.status_code == 200, (caso, r.status_code, r.text[:200])
        resultados[caso] = r.json().get("uso_devuelto")
    assert llamadas == [("silencio", "invitado:LLAVE-B")], llamadas
    assert resultados == {"silencio": True, "red": False, "voz": False}, resultados
    assert origenes == ["api", "api", "api"], origenes
    return "silencio devuelve a la cuenta cobrada; red y voz no; origen api"


def salud_dice_si_el_buscador_esta_listo():
    """Reinicio 27: /api/salud lleva `buscador_listo`, siempre presente. False sin catalogo cargado o con uno
    a medias; true solo si el catalogo dice que ya no espera a nada."""
    from types import SimpleNamespace as NS
    viejo = ui._catalogo
    vistos = []
    try:
        for cat, esperado in ((None, False), (NS(listo_para_buscar=lambda: False), False),
                              (NS(listo_para_buscar=lambda: True), True)):
            ui._catalogo = cat
            j = _ok(cliente.get("/api/salud"))
            vistos.append(j.get("buscador_listo"))
            assert j.get("buscador_listo") is esperado, (cat, j)
    finally:
        ui._catalogo = viejo
    return f"buscador_listo {vistos}"


def voz_cobra_y_devuelve_a_la_misma_cuenta():
    """Reinicio 27 (menor de 4e sobre 49a8e4d): el codigo se leia dos veces, antes de cobrar y otra vez
    dentro de `_puede_pagar`. Con una sesion que cambia de A a B justo ahi, se cobraba a una y se devolvia
    a otra. Ahora /api/voz lee el codigo una vez y lo pasa al cobro y a la devolucion."""
    from types import SimpleNamespace as NS
    from unittest.mock import patch

    lecturas, cobros, devueltos = [], [], []

    def codigo_de(pet):
        lecturas.append(1)
        return "cuenta-A" if len(lecturas) == 1 else "cuenta-B"

    ev = NS(palabras_falladas=[], puntuacion=0, transcripcion="", palabras_objetivo=["the"], entendidas=[])
    sesion = NS(evaluacion=ev, transcripcion_ok=False, correccion=None, audio_correcto=None,
                audios_palabras={}, ritmo=None, sin_voz=True)
    with patch.object(api.config, "falta", return_value=[]),             patch.object(api, "_va_a_costar", return_value=False),             patch.object(ui, "_codigo_de", codigo_de),             patch.object(ui, "_puede_pagar", lambda pet, codigo=None: (cobros.append(codigo), (True, ""))[1]),             patch.object(api.voz, "practicar", lambda *a, **k: sesion),             patch.object(api.cuentas, "devolver_por_silencio",
                         lambda base, codigo, hoy=None: (devueltos.append(codigo), True)[1]):
        r = cliente.post("/api/voz", headers=nuevo_lector(), data={"frase": "The cat."},
                         files={"audio": ("voz.webm", b"x" * 2000, "audio/webm")})
    assert r.status_code == 200, r.text[:200]
    assert cobros == ["cuenta-A"], f"se cobro a {cobros}"
    assert devueltos == ["cuenta-A"], f"se devolvio a {devueltos}"
    return "cobro y devolucion a la cuenta A aunque la sesion paso a B"


def curva_de_un_solo_capitulo_sin_forma():
    """Reinicio 27 (e6): con una sola fila, `_resumen_curva` no dice «se va soltando» ni pone el mismo capitulo
    como facil y dificil: forma, facil y dificil van a None. Con dos filas sigue como siempre, y sin filas igual."""
    una = api._resumen_curva("completo", {"filas": [{"capitulo": 1, "indice": 0, "dificultad": 0.8}]})
    assert (una["forma"], una["facil"], una["dificil"]) == (None, None, None), una
    assert una["filas"] and una["global"] is not None, una
    dos = api._resumen_curva("completo", {"filas": [{"capitulo": 1, "indice": 0, "dificultad": 0.4},
                                                    {"capitulo": 2, "indice": 1, "dificultad": 0.8}]})
    assert dos["forma"] == "se_complica", dos["forma"]
    assert dos["facil"]["capitulo"] == 1 and dos["dificil"]["capitulo"] == 2, (dos["facil"], dos["dificil"])
    assert api._resumen_curva("completo", {"filas": []}) == {"fuente": None, "filas": []}
    return "una fila sin forma ni extremos; dos filas se complica; sin filas igual"


def devolucion_sin_cobro_ni_registro_raro():
    """Reinicio 27 (menores de 4e): sin nada cobrado, `devolver_por_silencio` da False y no gasta un hueco del
    dia; si restar lanza, tampoco; y una entrada no numerica en el registro cuenta como 0 en vez de dejar sin
    devolucion el resto del dia."""
    import json
    from unittest.mock import patch
    import cuentas

    viejo = os.environ.get("LITERALEVEL_CUENTAS")
    os.environ["LITERALEVEL_CUENTAS"] = "invitado:LLAVE-B:40"
    try:
        with tempfile.TemporaryDirectory(prefix="ll_devol_menores_") as carpeta:
            base = Path(carpeta)
            registro = base / "devoluciones_silencio.json"
            assert cuentas.devolver_por_silencio(base, "invitado:LLAVE-B", hoy="2026-09-15") is False, "sin cobro"
            assert not registro.exists(), f"sin cobro se apunto: {registro.read_text(encoding='utf-8')}"
            cuentas.consumir(base, "invitado:LLAVE-B")
            with patch.object(cuentas, "_restar_ya_con_candado", side_effect=OSError("disco")):
                assert cuentas.devolver_por_silencio(base, "invitado:LLAVE-B", hoy="2026-09-15") is False
            assert not registro.exists(), "si restar lanza, no se apunta"
            registro.write_text(json.dumps({"2026-09-15": {"invitado": "abc"}}), encoding="utf-8")
            assert cuentas.devolver_por_silencio(base, "invitado:LLAVE-B", hoy="2026-09-15") is True, "entrada rara"
            assert json.loads(registro.read_text(encoding="utf-8")) == {"2026-09-15": {"invitado": 1}}
            assert cuentas.gastado(base, "invitado") == 0
    finally:
        if viejo is None:
            os.environ.pop("LITERALEVEL_CUENTAS", None)
        else:
            os.environ["LITERALEVEL_CUENTAS"] = viejo
    return "sin cobro y con restar roto no apunta; una entrada rara cuenta como 0 y devuelve"


def voz_subida_y_palabra_no_bloquean_a_los_demas():
    """Auditoría cruzada de 4e (14 sep 2026). /api/voz y la subida eran `async` y
    llamaban a voz y al lector en el bucle de eventos: mientras corregían, nada más
    se atendía. Y la etapa completa de /api/palabra retenía el candado léxico durante
    OpenAI, así que la vista previa de otro lector esperaba detrás. Con un solo
    bucle compartido (TestClient en `with`), una petición lenta en un hilo y una
    rápida en otro: la rápida no puede tardar lo que la lenta."""
    import threading
    import time
    from types import SimpleNamespace as NS

    import config
    import voz

    # Relativo a la lenta y no un tiempo fijo: con 0,75 s fijos fallaba 1 de 52
    # cuando corria a la vez que otras suites (Central, 15 sep 2026). Y sin dormir a
    # ciegas: la rapida sale cuando el doble lento ya ha entrado (ronda 2 de e6), y
    # tiene que acabar con la lenta aun viva y en menos del 60 % de lo que duerme; si
    # esperase detras, tardaria casi `duerme` entero.
    duerme = 2.0
    tope = duerme * 0.6
    dentro = threading.Event()

    def durante(lenta, rapida):
        dentro.clear()
        hilo = threading.Thread(target=lenta)
        hilo.start()
        assert dentro.wait(30), "la peticion lenta no llego a su doble"
        t = time.time()
        rapida()
        dt = time.time() - t
        viva = hilo.is_alive()
        hilo.join()
        return viva, dt

    def practicar_lento(ruta, frase, guardar_fallos=True, nivel=None, origen=""):
        dentro.set()
        time.sleep(duerme)
        ev = NS(puntuacion=100, transcripcion=frase, palabras_falladas=[], palabras_objetivo=["hola"], entendidas=[])
        return NS(evaluacion=ev, transcripcion_ok=True, correccion=None, audio_correcto=None)

    def cargar_lento(ruta):
        dentro.set()
        time.sleep(duerme)
        raise api._no(422, "Libro de prueba que no se abre.")

    real = ui.consultor()
    llamadas = []

    class ConsultorLento:
        def consultar(self, *a, **k):
            llamadas.append(1)
            if len(llamadas) == 1:
                dentro.set()
                time.sleep(duerme)
            return real.consultar(*a, **k)

    lento = ConsultorLento()
    originales = (voz.practicar, config.falta, ui._puede_pagar, api._va_a_costar, api._cargar_libro, ui.consultor,
                  ui._dentro_del_limite)
    # Sin gastar el cupo de subidas por IP y hora: las pruebas de despues lo usan.
    ui._dentro_del_limite = lambda *a, **k: True
    config.falta = lambda: False
    ui._puede_pagar = lambda pet, *a, **k: (True, "")
    api._va_a_costar = lambda pet: False
    voz.practicar = practicar_lento
    api._cargar_libro = cargar_lento
    try:
        with TestClient(api.app, raise_server_exceptions=False) as c:
            h1, h2 = nuevo_lector(), nuevo_lector()
            cuerpo = {"palabra": "raincoat", "oracion": "Manu got a red raincoat.", "etapa": "diccionario"}
            _ok(c.post("/api/palabra", headers=h2, json=cuerpo))          # calienta spaCy y el diccionario
            viva_voz, t_voz = durante(
                lambda: c.post("/api/voz", headers=h1, data={"frase": "Hola."},
                               files={"audio": ("voz.webm", b"\x1a" * 2000, "audio/webm")}),
                lambda: _ok(c.get("/api/salud")))
            viva_subida, t_subida = durante(
                lambda: c.post("/api/libros", headers=nuevo_lector(),
                               files={"archivo": ("lento.txt", b"Once upon a time. " * 200, "text/plain")}),
                lambda: _ok(c.get("/api/salud")))
            ui.consultor = lambda: lento
            config.falta = lambda: True          # la completa no cobra: basta con que sea lenta
            viva_palabra, t_palabra = durante(
                lambda: c.post("/api/palabra", headers=h1, json={**cuerpo, "etapa": "completa"}),
                lambda: _ok(c.post("/api/palabra", headers=h2, json=cuerpo)))
    finally:
        (voz.practicar, config.falta, ui._puede_pagar, api._va_a_costar, api._cargar_libro, ui.consultor,
         ui._dentro_del_limite) = originales
    for viva, dt, que in ((viva_voz, t_voz, "/api/salud mientras se corregía una voz"),
                          (viva_subida, t_subida, "/api/salud mientras se abría una subida"),
                          (viva_palabra, t_palabra, "la vista previa del diccionario detrás de una explicación")):
        assert viva and dt < tope, (f"{que}: {dt:.2f} s (tope {tope:.2f} s, el 60 % de {duerme} s) y la lenta "
                                    f"{'seguía' if viva else 'ya había terminado'}")
    return (f"salud {t_voz:.2f} s con voz, {t_subida:.2f} s con subida; diccionario {t_palabra:.2f} s con "
            f"explicación; la lenta dura {duerme} s y seguía viva en los tres")


def validacion_sin_eco_de_la_entrada():
    """Ronda 2 de e6 (15 sep 2026, verificado en el Space): el 422 de /api/entrar
    devolvía la contraseña en «input». Ni ahí ni en ninguna ruta, y tampoco en el
    Space, que monta la API con `para_gradio`."""
    from fastapi.exceptions import RequestValidationError
    secreto = "r2-no-es-real-" + "q" * 240
    r = cliente.post("/api/entrar", headers=nuevo_lector(), json={"usuario": "profe", "clave": secreto})
    assert r.status_code == 422 and "no-es-real" not in r.text, r.text[:300]
    error = r.json()["detail"][0]
    assert set(error) == {"loc", "msg", "type"} and error["loc"][-1] == "clave", error
    otra = cliente.post("/api/perfil/cuestionario", headers=nuevo_lector(),
                        json={"respuestas": "NO-ES-UN-DICCIONARIO-XYZ"})
    assert otra.status_code == 422 and "XYZ" not in otra.text, otra.text[:300]
    manejadores = api.para_gradio()["exception_handlers"]
    assert manejadores.get(RequestValidationError) is api._validacion_sin_eco, manejadores
    return "422 con dónde y qué, sin la contraseña; también en el Space (para_gradio)"


def dos_subidas_a_la_vez_no_pasan_el_tope_ni_rompen_los_nombres():
    """Ronda 2 de e6 (15 sep 2026): con la subida en un hilo, dos subidas del mismo
    lector a la vez daban 200 y 200 con tope 1, y nombres.json quedaba como JSON
    inválido: el lector perdía el nombre de todos sus libros. La escritura del libro
    va retrasada 0,8 s para ensanchar la ventana, como en su medición."""
    import json
    import threading
    import time
    from pathlib import Path as _Path

    texto = ("The old lighthouse keeper climbed the stairs every evening. " * 50 + "\n\n") * 3
    lector = nuevo_lector()
    maximo, escribir = api._MAX_SUBIDOS, _Path.write_bytes

    def escribir_lento(self, datos):
        time.sleep(0.8)
        return escribir(self, datos)

    salida = {}
    api._MAX_SUBIDOS = 1
    _Path.write_bytes = escribir_lento
    # Sin gastar el cupo de subidas por IP y hora: las pruebas de despues lo usan.
    dentro_del_limite = ui._dentro_del_limite
    ui._dentro_del_limite = lambda *a, **k: True
    try:
        with TestClient(api.app, raise_server_exceptions=False) as c:
            barrera = threading.Barrier(2)

            def subir(nombre, extra):
                barrera.wait()
                salida[nombre] = c.post("/api/libros", headers=lector, files={
                    "archivo": (f"{nombre}.txt", (texto + extra).encode(), "text/plain")})

            hilos = [threading.Thread(target=subir, args=("Mi primer libro", " Uno.")),
                     threading.Thread(target=subir, args=("Mi segundo libro", " Dos."))]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
            _Path.write_bytes = escribir
            estados = sorted(r.status_code for r in salida.values())
            buenas = {n: r.json() for n, r in salida.items() if r.status_code == 200}
            reabiertos = {n: _ok(c.get(f"/api/libros/{j['id']}", headers=lector)) for n, j in buenas.items()}
            tercero = c.post("/api/libros", headers=lector, files={
                "archivo": ("Mi tercer libro.txt", (texto + " Tres.").encode(), "text/plain")})
    finally:
        api._MAX_SUBIDOS = maximo
        _Path.write_bytes = escribir
        ui._dentro_del_limite = dentro_del_limite
    assert estados == [200, 429], f"con tope 1, dos subidas a la vez: {estados}"
    assert tercero.status_code == 429, f"quedó más de un libro en disco: {tercero.status_code}"
    for nombre, libro in reabiertos.items():
        assert nombre in json.dumps(libro, ensure_ascii=False), f"el libro perdió su nombre: {nombre}"
    return f"{estados}, un solo libro en disco y con su nombre ({next(iter(reabiertos))})"


def cache_lexica_serializa_la_conexion_entre_hilos():
    """Ronda 2 de e6 (DUDA): la caché léxica usa una sola conexión SQLite con
    check_same_thread=False, y desde 31325a4 la etapa completa corre en paralelo.
    Cada uso de la conexión va con el candado de la caché."""
    import tempfile
    import lexicon

    with tempfile.TemporaryDirectory(prefix="ll_cache_") as d:
        cache = lexicon.CacheLexico(os.path.join(d, "cache.db"))
        real = cache._con
        sin_candado = []

        class Vigilada:
            def execute(self, *a, **k):
                if not cache._candado.locked():
                    sin_candado.append(str(a[0]).split()[0])
                return real.execute(*a, **k)

            def commit(self):
                if not cache._candado.locked():
                    sin_candado.append("COMMIT")
                return real.commit()

        cache._con = Vigilada()
        cache.guardar_respuesta({"a": 1}, "m", "x")
        assert cache.obtener_respuesta("x") == {"a": 1}
        audio = os.path.join(d, "a.mp3")
        open(audio, "wb").close()
        cache.guardar_audio(audio, "y")
        assert cache.obtener_audio("y") == audio
        cache._con = real
        cache.cerrar()
    assert not sin_candado, f"usos de la conexión sin candado: {sin_candado}"
    return "guardar y obtener, de texto y de audio, siempre con el candado"


def borrar_subido_todo_bajo_el_candado():
    """Ronda 3 de e6 (15 sep 2026): borrar_subido quitaba el archivo, la caché y la
    biblioteca fuera del candado de subidas; solo nombres.json iba dentro."""
    from pathlib import Path as _Path

    texto = ("A small fox ran across the frozen river before dawn. " * 50 + "\n\n") * 3
    lector = nuevo_lector()
    limite = ui._dentro_del_limite
    ui._dentro_del_limite = lambda *a, **k: True
    try:
        subido = _ok(cliente.post("/api/libros", headers=lector,
                                  files={"archivo": ("zorro.txt", texto.encode(), "text/plain")}))
    finally:
        ui._dentro_del_limite = limite
    candado_real, borrar = api._candado_subidas, _Path.unlink
    vistos, fuera = [], []

    def candado_vigilado(pet):
        c = candado_real(pet)
        vistos.append(c)
        return c

    def unlink_vigilado(self, *a, **k):
        if self.suffix in api._EXT_LIBRO and not any(c.locked() for c in vistos):
            fuera.append(self.name)
        return borrar(self, *a, **k)

    api._candado_subidas, _Path.unlink = candado_vigilado, unlink_vigilado
    try:
        r = cliente.delete(f"/api/libros/{subido['id']}", headers=lector)
    finally:
        api._candado_subidas, _Path.unlink = candado_real, borrar
    assert r.status_code == 200, r.text
    assert vistos and not fuera, f"libros borrados fuera del candado de subidas: {fuera}"
    return "el archivo del libro se borra con el candado de subidas tomado"


def abrir_un_libro_no_retiene_el_candado_de_otros():
    """Ronda 3 de e6 (15 sep 2026): el candado de subidas se retenía mientras se abría
    el libro, y los candados van por franjas: un lector ajeno de la misma franja
    esperaba. Con una sola franja, la subida de B acaba mientras A sigue abriendo."""
    import threading
    import time

    texto = ("The lighthouse keeper counted the ships every night. " * 50 + "\n\n") * 3
    dentro, duerme = threading.Event(), 2.0
    cargar, candados, limite = api._cargar_libro, api._CANDADOS_SUBIDAS, ui._dentro_del_limite
    llamadas = []

    def cargar_la_primera_lenta(ruta):
        llamadas.append(ruta)
        if len(llamadas) == 1:
            dentro.set()
            time.sleep(duerme)
        return cargar(ruta)

    api._cargar_libro, api._CANDADOS_SUBIDAS = cargar_la_primera_lenta, [threading.Lock()]
    ui._dentro_del_limite = lambda *a, **k: True
    try:
        with TestClient(api.app, raise_server_exceptions=False) as c:
            hilo = threading.Thread(target=lambda: c.post(
                "/api/libros", headers=nuevo_lector(),
                files={"archivo": ("a.txt", texto.encode(), "text/plain")}))
            hilo.start()
            assert dentro.wait(30), "la subida lenta no llegó a abrir su libro"
            t = time.time()
            r = c.post("/api/libros", headers=nuevo_lector(),
                       files={"archivo": ("b.txt", (texto + " Otro.").encode(), "text/plain")})
            dt = time.time() - t
            viva = hilo.is_alive()
            hilo.join()
    finally:
        api._cargar_libro, api._CANDADOS_SUBIDAS, ui._dentro_del_limite = cargar, candados, limite
    assert r.status_code == 200, r.text
    assert viva and dt < duerme * 0.6, f"la subida de otro lector esperó {dt:.2f} s (la otra seguía: {viva})"
    return f"la otra subida, en {dt:.2f} s mientras la primera seguía abriendo su libro ({duerme} s)"


def nombres_que_no_se_pueden_escribir_lo_dicen():
    """Ronda 3 de e6 (15 sep 2026): _escribir_nombres se tragaba el OSError."""
    import contextlib
    import io
    import tempfile
    from pathlib import Path as _Path

    reemplazar, err = os.replace, io.StringIO()

    def falla(*a, **k):
        raise PermissionError("disco de solo lectura")

    with tempfile.TemporaryDirectory(prefix="ll_nombres_") as d:
        os.replace = falla
        try:
            with contextlib.redirect_stderr(err):
                ok = api._escribir_nombres(_Path(d) / "nombres.json", {"u1": "Mi libro"})
        finally:
            os.replace = reemplazar
        restos = list(_Path(d).iterdir())
    assert ok is False and "nombres.json" in err.getvalue(), (ok, err.getvalue())
    assert not restos, f"queda el temporal: {restos}"
    return "devuelve False, lo escribe en stderr y no deja el temporal"


def corte_de_la_boca_en_svg():
    """Las animaciones de 4e, servidas al front: tipo, caché, sin ejecutar nada
    aunque se abran sueltas, quieto distinto de animado y rechazo de lo raro."""
    from urllib.parse import quote
    theta = "/api/articulacion/ga/" + quote("θ") + ".svg"
    r = cliente.get(theta)
    assert r.status_code == 200, (r.status_code, r.text[:200])
    assert r.headers["content-type"].startswith("image/svg+xml"), r.headers
    assert "no-store" in r.headers["cache-control"], r.headers
    assert r.headers["x-content-type-options"] == "nosniff", r.headers
    assert "default-src 'none'" in r.headers["content-security-policy"], r.headers
    assert r.text.lstrip().startswith("<svg"), r.text[:80]
    q = cliente.get(theta + "?quieto=1")
    assert q.status_code == 200 and q.text != r.text, "quieto sale igual que animado"
    assert cliente.get("/api/articulacion/rp/" + quote("əʊ") + ".svg").status_code == 200
    assert cliente.get("/api/articulacion/ga/zz.svg").status_code == 404
    assert cliente.get("/api/articulacion/ga/" + quote("θ") + ".png").status_code == 404
    assert cliente.get("/api/articulacion/fr/" + quote("θ") + ".svg").status_code == 422
    p = cliente.get("/api/articulacion/palabra.svg", params={"ipa": "/wɔɹ/", "acento": "ga"})
    assert p.status_code == 200 and p.headers["content-type"].startswith("image/svg+xml"), p.status_code
    assert "default-src 'none'" in p.headers["content-security-policy"]
    assert cliente.get("/api/articulacion/palabra.svg", params={"ipa": "x" * 61}).status_code == 422
    # Solo IPA: ni una frase cualquiera dibujada en el dominio del Space ni marcas.
    for raro in ("Visit evil.example NOW", "<b>hola</b>", "wɔɹ 123"):
        assert cliente.get("/api/articulacion/palabra.svg", params={"ipa": raro}).status_code == 422, raro
    assert cliente.get("/api/articulacion/palabra.svg", params={"ipa": "/ˈt͡ʃɑːnt/", "acento": "rp"}).status_code == 200
    assert cliente.get("/api/articulacion/rp/" + quote("iː") + ".svg").status_code == 200
    # Kaikki escribe paréntesis: «/ˈhæp(ə)n/» no es un texto raro.
    assert cliente.get("/api/articulacion/palabra.svg", params={"ipa": "/ˈhæp(ə)n/"}).status_code != 422
    return f"sonido {len(r.text)} B, quieto {len(q.text)} B, palabra {len(p.text)} B"


def corte_de_una_pasada_con_la_duracion_del_audio():
    """«Escuchar y ver»: ?dur= (redondeado a 0,1 s, 0,3..10) y ?una=1 llegan al
    módulo de 4e; fuera de rango se ignora; el quieto no cambia; sin nada, el
    SVG de siempre."""
    from urllib.parse import quote
    from app import animacion_articulatoria as aa
    theta = "/api/articulacion/ga/" + quote("θ") + ".svg"
    corta = cliente.get(theta, params={"dur": "1.43", "una": "1"})
    assert corta.status_code == 200, (corta.status_code, corta.text[:200])
    assert corta.text == aa.svg_articulacion("θ", "ga", dur=1.4, repetir=False), "dur o una no llegan como tocan"
    assert corta.text != aa.svg_articulacion("θ", "ga", dur=1.4), "una=1 no quita el bucle"
    # «Más lento»: un audio de 8,6 s a 0,5× son 17,2 s, y tiene que llegar.
    lenta = cliente.get(theta, params={"dur": "17.24", "una": "1"})
    assert lenta.text == aa.svg_articulacion("θ", "ga", dur=17.2, repetir=False), "dur de más de 10 s no llega"
    # Regresión D4: normal -> replay -> replay -> Despacio -> normal conserva
    # exactamente los paths anatómicos; solo puede cambiar el tiempo del CSS.
    def geometria_aire(svg):
        import re
        return re.findall(r'<path[^>]*data-via="(?:oral|nasal)"[^>]*\bd="([^"]+)"', svg)

    secuencia = [
        cliente.get(theta, params={"dur": "7.1", "una": "1", "r": str(vuelta)}).text
        for vuelta in (1, 2, 3)
    ]
    secuencia.append(cliente.get(theta, params={"dur": "14.2", "una": "1", "r": "4"}).text)
    secuencia.append(cliente.get(theta, params={"dur": "7.1", "una": "1", "r": "5"}).text)
    rutas = [geometria_aire(svg) for svg in secuencia]
    assert rutas[0] and all(ruta == rutas[0] for ruta in rutas), rutas
    en_bucle = cliente.get(theta, params={"dur": "1.4"})
    assert en_bucle.text == aa.svg_articulacion("θ", "ga", dur=1.4, repetir=True)
    assert cliente.get(theta).text == aa.svg_articulacion("θ", "ga")
    # Fuera de rango el módulo también lo ignora: lo que guarda la API es que no
    # ocupe otra entrada de la caché (una por cada dur raro que manden).
    api._svg_corte.cache_clear()
    fuera = cliente.get(theta, params={"dur": "50", "una": "1"})
    assert fuera.text == aa.svg_articulacion("θ", "ga", dur=None, repetir=False), "dur fuera de rango no se ignora"
    cliente.get(theta, params={"una": "1"})
    cliente.get(theta, params={"dur": "nan", "una": "1"})
    assert api._svg_corte.cache_info().currsize == 1, api._svg_corte.cache_info()
    quieto = cliente.get(theta, params={"quieto": "1", "dur": "2", "una": "1"})
    assert quieto.text == aa.svg_articulacion_quieto("θ", "ga")
    assert cliente.get(theta, params={"dur": "abc"}).status_code == 422
    palabra = cliente.get("/api/articulacion/palabra.svg",
                          params={"ipa": "/wɔɹ/", "acento": "rp", "dur": "0.84", "una": "1"})
    assert palabra.status_code == 200, palabra.status_code
    assert palabra.text == aa.svg_palabra("/wɔɹ/", "rp", dur=0.8, repetir=False), "la palabra no recibe dur o una"
    assert palabra.headers["x-content-type-options"] == "nosniff"
    return f"sonido 1,4 s de una pasada {len(corta.text)} B, palabra 0,8 s {len(palabra.text)} B"


def indice_de_romanos_de_una_letra_no_abre_el_libro():
    """PG1661 (Sherlock Holmes, un solo capítulo): el «Contents» es UN párrafo
    con doce marcas «romano.», tres de una letra (I., V., X.), y se enseñaba al
    empezar a leer. Con cinco o más marcas es índice; «Chapter IV.» citado una
    vez en prosa no lo es (diagnóstico de entrega-4e)."""
    indice = ("I. A Scandal in Bohemia II. The Red-Headed League III. A Case of Identity "
              "IV. The Boscombe Valley Mystery V. The Five Orange Pips VI. The Man with the Twisted Lip "
              "VII. The Adventure of the Blue Carbuncle VIII. The Adventure of the Speckled Band "
              "IX. The Adventure of the Engineer’s Thumb X. The Adventure of the Noble Bachelor "
              "XI. The Adventure of the Beryl Coronet XII. The Adventure of the Copper Beeches")
    assert api._parece_indice(indice) is True, "el índice de PG1661 pasa por prosa"
    prosa = ("As I explained in Chapter IV. of my notes, I had seldom heard him mention her under any "
             "other name, and in his eyes she eclipsed and predominated the whole of her sex; it was not "
             "that he felt any emotion akin to love for Irene Adler, as V. said.")
    assert api._parece_indice(prosa) is False, "prosa con dos romanos sueltos se toma por índice"
    lib = api._cargar_libro(ui._descargar_gutenberg("PG1661"))
    primero = api._parrafos(lib, 0)[0]
    assert primero.startswith("To Sherlock Holmes she is always _the_ woman."), primero[:80]
    return primero[:40]


def ritmo_de_la_lectura_con_nivel_y_audio_natural():
    """Lectura natural (4e: 9f5f909, 55d546c, b41ff5e): el nivel del perfil llega
    a voz, el ritmo sale tal cual con el mp3 natural como URL, el intento se
    guarda en la voz.db del lector, y /api/voz/ritmo lee su evolución (con aviso
    si la base no se puede leer)."""
    from types import SimpleNamespace as NS
    import config
    import voz
    lector = nuevo_lector()
    mp3 = api._DIR_AUDIO / f"prueba_{uuid.uuid4().hex[:8]}.mp3"
    mp3.parent.mkdir(parents=True, exist_ok=True)
    mp3.write_bytes(b"ID3" + b"\x00" * 64)
    ritmo = {"medido": True, "duracion_s": 3.4,
             "palabras": [{"palabra": "you", "inicio": 0.4, "fin": 0.6}],
             "pausas": [{"despues_de": 0, "segundos": 0.52, "en_referencia": False, "de_mas": True}],
             "tramos": [{"desde": 0, "hasta": 1, "palabras_por_segundo": 2.1, "referencia": 3.2,
                         "objetivo": 2.9, "acelerar": True}],
             "natural": {"enfasis": [{"indice": 1, "ipa": None}], "enlaces": [],
                         "reducciones": [], "tramos_rapidos": [], "version_natural": "you know.",
                         "audio_natural": str(mp3)}}
    vistas, guardados = {}, []

    def practicar_doble(ruta, frase, guardar_fallos=True, nivel=None, origen=""):
        vistas["nivel"] = nivel
        ev = NS(puntuacion=90, transcripcion="you know", palabras_falladas=[],
                palabras_objetivo=["you", "know"], entendidas=[])
        return NS(evaluacion=ev, transcripcion_ok=True, correccion=None, audio_correcto=None,
                  audios_palabras={}, ritmo=ritmo)

    def evolucion_doble(frase, n=10, ruta=None):
        vistas["evolucion"] = (frase, n, Path(ruta).name)
        return [{"fecha": "2026-09-14", "palabras_por_segundo": 2.1, "pausas_de_mas": 1, "tramos_a_acelerar": 1}]

    def ilegible(frase, n=10, ruta=None):
        raise voz.HistorialIlegible("No he podido leer tu historial de voz.")

    originales = (voz.practicar, voz.registrar_ritmo, voz.evolucion_ritmo, config.falta, ui._puede_pagar,
                  api._va_a_costar, api._perfil_de)
    voz.practicar = practicar_doble
    voz.registrar_ritmo = lambda r, frase, ruta=None: guardados.append((r, frase, Path(ruta).name))
    voz.evolucion_ritmo = evolucion_doble
    config.falta = lambda: False
    ui._puede_pagar = lambda pet, *a, **k: (True, "")
    api._va_a_costar = lambda pet: False
    api._perfil_de = lambda pet: NS(nivel=1.6) if pet.session_hash == lector["X-Lector"] else None
    try:
        r = _ok(cliente.post("/api/voz", headers=lector, data={"frase": "You know.", "acento": "US"},
                             files={"audio": ("voz.webm", b"\x1a" * 2000, "audio/webm")}))
        evolucion = _ok(cliente.get("/api/voz/ritmo", headers=lector, params={"frase": "You know."}))
        voz.evolucion_ritmo = ilegible
        rota = _ok(cliente.get("/api/voz/ritmo", headers=lector, params={"frase": "You know."}))
    finally:
        (voz.practicar, voz.registrar_ritmo, voz.evolucion_ritmo, config.falta, ui._puede_pagar,
         api._va_a_costar, api._perfil_de) = originales
        mp3.unlink(missing_ok=True)
    assert vistas.get("nivel") == 1.6, vistas
    esperado = {**ritmo, "natural": {**ritmo["natural"], "audio_natural": f"/api/audio/{mp3.name}"}}
    assert r["ritmo"] == esperado, r.get("ritmo")
    # Se guarda el ritmo de voz (con su ruta), no el JSON ya convertido.
    assert guardados == [(ritmo, "You know.", "voz.db")], guardados
    assert ritmo["natural"]["audio_natural"] == str(mp3), "la API cambió el dict de voz"
    assert evolucion == {"intentos": [{"fecha": "2026-09-14", "palabras_por_segundo": 2.1,
                                       "pausas_de_mas": 1, "tramos_a_acelerar": 1}], "aviso": None}, evolucion
    assert vistas.get("evolucion") == ("You know.", 10, "voz.db"), vistas
    assert rota == {"intentos": [], "aviso": "No he podido leer tu historial de voz."}, rota
    assert cliente.get("/api/voz/ritmo", headers=lector, params={"frase": ""}).status_code == 422
    return f"nivel 1.6, audio natural {r['ritmo']['natural']['audio_natural'][:22]}…, 1 intento"


def temas_para_la_portada():
    """La tarjeta y la ficha traen los temas del catálogo, partidos por «;» y en
    su orden, para la portada tipográfica; un libro sin temas trae []."""
    from app import catalogo as cat
    d = ui.catalogo().df
    fila = d[d["id"].astype(str).str.upper() == "PG1661"].iloc[0]
    esperados = [t.strip() for t in str(fila["temas"]).split(";") if t.strip()][:8]
    assert len(esperados) >= 1, fila["temas"]
    b = cat.Libro(id="PG1661", titulo="The Adventures of Sherlock Holmes", autor="Doyle", nivel="B2",
                  gancho="", descargas=1)
    tarjeta = api._libro_tarjeta(b)
    assert tarjeta["temas"] == esperados, (tarjeta["temas"], esperados)
    # Los ids llegan como sea («pg1661» en una URL escrita a mano): los temas no dependen de eso.
    minusculas = api._libro_tarjeta(cat.Libro(id="pg1661", titulo="x", autor="", nivel="B2", gancho="", descargas=0))
    assert minusculas["temas"] == esperados, minusculas["temas"]
    sin = api._libro_tarjeta(cat.Libro(id="NO-EXISTE-9", titulo="x", autor="", nivel="A1", gancho="", descargas=0))
    assert sin["temas"] == [], sin["temas"]
    libre = d[d["id"].astype(str).str.upper() == LIBRE.upper()].iloc[0]
    ficha = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=A))
    assert ficha["temas"] == [t.strip() for t in str(libre["temas"]).split(";") if t.strip()][:8], ficha["temas"]
    return f"PG1661 {esperados[:2]}, {LIBRE} {ficha['temas']}"


def nota_de_nivel_dice_libros_y_cuentos():
    """Prueba de f4 (4): la nota bajo los resultados decía «medirlo entero,
    capítulo a capítulo», que no es verdad para los cuentos medidos en bloque."""
    nota = ui._nota_nivel()
    assert ui.catalogo().medido, "el catálogo de pruebas no está medido"
    assert nota == ui.NOTA_NIVEL_MEDIDO, nota
    assert "los libros, enteros y capítulo a capítulo" in nota, nota
    assert "los cuentos cortos, en un bloque con otros de su misma fuente y nivel" in nota, nota
    assert "medirlo entero" not in nota, nota
    return nota[:70]


def plurales_de_los_minutos():
    """Prueba de f4 (1): «1 minutos». Uno en singular y sin «unos»; varios, «unos N»."""
    assert ui._cuanto_falta(1) == "en 1 minuto" and ui._cuanto_falta(0) == "en 1 minuto"
    assert ui._cuanto_falta(12) == "en unos 12 minutos"
    # El tiempo de la ficha: un rango con los dos extremos iguales se dice una vez (Central, 15 sep).
    assert ui._rango_de_tiempo(1, 1) == "1 minuto", ui._rango_de_tiempo(1, 1)
    assert ui._rango_de_tiempo(12, 12) == "12 minutos"
    assert ui._rango_de_tiempo(1, 2) == "entre 1 minuto y 2 minutos"
    assert ui._rango_de_tiempo(40, 95) == "entre 40 minutos y 1 h 35 min"
    assert ui._reloj_llano(1) == "1 minuto" and ui._reloj_llano(21) == "21 minutos"
    assert ui._cuanto_falta(1, "en") == "in 1 minute" and ui._cuanto_falta(5, "en") == "in about 5 minutes"
    assert "en 1 minuto." in ui._mensaje_limite("es", 1) and "1 minutos" not in ui._mensaje_limite("es", 1)
    # El aviso dice QUE se ha acabado: con el cubo de la voz no puede hablar de
    # «consultas», que es el del diccionario y otro tope (Miguel, 16 sep 2026).
    assert "correcciones de pronunciación" in ui._mensaje_limite("es", 1, "voz")
    assert "explicaciones en contexto" in ui._mensaje_limite("es", 1, "lexico")
    assert ui._mensaje_limite("es", 1, "voz") != ui._mensaje_limite("es", 1, "lexico")
    assert "en 1 minuto." in ui._mensaje_limite("es", 1, "voz")
    originales = (ui._dentro_del_limite, ui._minutos_para_la_siguiente, ui._descargar_gutenberg)
    ui._dentro_del_limite = lambda pet, cubo, tope, clave=None: cubo != "descargas"
    ui._minutos_para_la_siguiente = lambda cubo, pet, clave=None: 1
    try:
        r = cliente.get("/api/libros/PG999999", headers=nuevo_lector())
    finally:
        ui._dentro_del_limite, ui._minutos_para_la_siguiente, ui._descargar_gutenberg = originales
    assert r.status_code == 429, (r.status_code, r.text[:200])
    detalle = r.json()["detail"]
    assert detalle == (f"Has abierto {ui.LIMITE_DESCARGAS_HORA} libros nuevos en esta hora. "
                       "Espera 1 minuto o sigue con los que ya tienes."), detalle
    return detalle[:60]


def portada_por_ia_si_existe():
    """Punto 3 de las portadas: con PG1661.webp en la carpeta de portadas, la
    tarjeta y la ficha traen su URL versionada y la ruta la sirve con nosniff;
    sin archivo, None; y la ruta no deja salir de la carpeta."""
    from app import catalogo as cat
    carpeta = Path(pruebas_tmp.carpeta("ll_portadas_"))
    original = api._DIR_PORTADAS
    api._DIR_PORTADAS = carpeta
    try:
        b = cat.Libro(id="PG1661", titulo="x", autor="", nivel="B2", gancho="", descargas=0)
        sin = api._libro_tarjeta(b)["portada_ia"]
        (carpeta / "PG1661.webp").write_bytes(b"RIFF\x10\x00\x00\x00WEBPVP8 ")
        (carpeta / "secreto.txt").write_text("no")
        st = (carpeta / "PG1661.webp").stat()
        con = api._libro_tarjeta(cat.Libro(id="pg1661", titulo="x", autor="", nivel="B2", gancho="", descargas=0))["portada_ia"]
        ficha = _ok(cliente.get("/api/libros/PG1661", headers=A))["portada_ia"]
        r = cliente.get("/api/portadas/PG1661.webp")
        malos = [cliente.get(f"/api/portadas/{n}").status_code
                 for n in ("secreto.txt", "..%2Fsecreto.txt", "PG1661.gif", "pg1661.webp", "NOPE.webp")]
    finally:
        api._DIR_PORTADAS = original
        for f in carpeta.iterdir():
            f.unlink()
        carpeta.rmdir()
    esperado = f"/api/portadas/PG1661.webp?v={st.st_size}-{int(st.st_mtime)}"
    assert sin is None, sin
    assert con == esperado and ficha == esperado, (con, ficha, esperado)
    assert r.status_code == 200 and r.headers["content-type"] == "image/webp", (r.status_code, r.headers)
    assert r.headers["x-content-type-options"] == "nosniff", r.headers
    assert malos == [404, 404, 404, 404, 404], malos
    return f"sin archivo None, con archivo {con}"


def topes_de_medir_y_de_la_curva():
    """Revisión de 4e (6): muestra, nivel con libro y medir capítulo gastan
    ficha del cubo «medidas»; la curva, del cubo «curvas», y además no admite
    más hilos vivos que `_CURVAS_VIVAS` (sin gastar ficha si no cabe). Lo que
    se rechaza gratis no gasta; pedir otra vez una curva en marcha tampoco. Y
    el audio sale con nosniff (7)."""
    from types import SimpleNamespace as NS
    # Prosa de verdad (Conan Doyle, dominio público): una frase repetida no pasa el filtro.
    prosa = ("To Sherlock Holmes she is always the woman. I have seldom heard him mention her under any "
             "other name. In his eyes she eclipses and predominates the whole of her sex. It was not that "
             "he felt any emotion akin to love for Irene Adler. All emotions, and that one particularly, "
             "were abhorrent to his cold, precise but admirably balanced mind. He was, I take it, the most "
             "perfect reasoning and observing machine that the world has seen, but as a lover he would have "
             "placed himself in a false position. He never spoke of the softer passions, save with a gibe "
             "and a sneer. They were admirable things for the observer, excellent for drawing the veil "
             "from men's motives and actions. ") * 2
    lector = nuevo_lector()
    gastos, cerrados = [], set()

    def cubo_espia(pet, cubo, tope, clave=None):
        gastos.append((cubo, tope))
        return cubo not in cerrados

    n = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=lector))["inicial"]
    originales = (ui._dentro_del_limite, api._puntuar, api._medir_libro, ui._analisis_guardado)
    trabajos = api._TRABAJOS.copy()
    ui._dentro_del_limite = cubo_espia
    api._puntuar = lambda texto: NS(puntuacion=1.0, banda=2, n_bloques=1, confianza="alta")
    api._medir_libro = lambda trabajo, lib, modo: None      # el hilo no hace nada: el trabajo sigue «en_cola»
    ui._analisis_guardado = lambda *a, **k: None
    try:
        # Lo que se rechaza sin coste no gasta ficha.
        no_prosa = cliente.post("/api/perfil/muestra", headers=lector, json={"texto": "hola " * 3})
        gastos_rechazo = list(gastos)
        abiertos = (cliente.post("/api/perfil/muestra", headers=lector, json={"texto": prosa}).status_code,
                    cliente.post("/api/perfil/libro", headers=lector, json={"libro_id": LIBRE}).status_code,
                    cliente.post(f"/api/libros/{LIBRE}/capitulos/{n}/medir", headers=lector).status_code)
        gastos_abiertos = list(gastos)
        cerrados.add("medidas")
        cerrados_medir = (cliente.post("/api/perfil/muestra", headers=lector, json={"texto": prosa}).status_code,
                          cliente.post("/api/perfil/libro", headers=lector, json={"libro_id": LIBRE}).status_code,
                          cliente.post(f"/api/libros/{LIBRE}/capitulos/{n}/medir", headers=lector).status_code)
        aviso_medir = cliente.post(f"/api/libros/{LIBRE}/capitulos/{n}/medir", headers=lector).json()["detail"]
        # La curva: la primera entra, repetirla no gasta, y sin ficha 429.
        api._TRABAJOS.clear()
        del gastos[:]
        primera = _ok(cliente.post(f"/api/libros/{LIBRE}/curva", headers=lector, json={"modo": "rapido"}))
        repetida = _ok(cliente.post(f"/api/libros/{LIBRE}/curva", headers=lector, json={"modo": "rapido"}))
        gastos_curva = list(gastos)
        api._TRABAJOS.clear()
        cerrados.add("curvas")
        sin_ficha = cliente.post(f"/api/libros/{LIBRE}/curva", headers=lector, json={"modo": "rapido"})
        # Con la cola llena, 503 y SIN gastar ficha.
        cerrados.discard("curvas")
        for i in range(api._CURVAS_VIVAS):
            api._TRABAJOS[f"otro{i}"] = {"id": f"otro{i}", "clave": f"otro{i}", "modo": "rapido", "estado": "en_curso"}
        del gastos[:]
        llena = cliente.post(f"/api/libros/{LIBRE}/curva", headers=lector, json={"modo": "rapido"})
        gastos_llena = list(gastos)
        # Una que ya terminó no ocupa sitio en la cola.
        api._TRABAJOS["otro0"]["estado"] = "hecho"
        hueco = cliente.post(f"/api/libros/{LIBRE}/curva", headers=lector, json={"modo": "rapido"})
    finally:
        ui._dentro_del_limite, api._puntuar, api._medir_libro, ui._analisis_guardado = originales
        api._TRABAJOS.clear()
        api._TRABAJOS.update(trabajos)
    assert no_prosa.status_code == 422 and gastos_rechazo == [], (no_prosa.status_code, gastos_rechazo)
    assert abiertos == (200, 200, 200), abiertos
    assert gastos_abiertos == [("medidas", api._MEDIDAS_HORA)] * 3, gastos_abiertos
    assert cerrados_medir == (429, 429, 429), cerrados_medir
    assert primera["trabajo"] and repetida["trabajo"] == primera["trabajo"], (primera, repetida)
    assert gastos_curva == [("curvas", api._CURVAS_HORA)], gastos_curva
    assert sin_ficha.status_code == 429, sin_ficha.status_code
    # El aviso no promete que medir siga gratis (f4, reinicio 11): dice qué se acabó.
    assert aviso_medir == ("Has llegado al límite de medidas de nivel y de capítulos de esta hora. "
                           "Vuelve a intentarlo en 1 minuto. Leer y buscar siguen funcionando."), aviso_medir
    assert sin_ficha.json()["detail"] == ("Has llegado al límite de curvas de libros de esta hora. "
                                          "Vuelve a intentarlo en 1 minuto. Leer y buscar siguen funcionando."), sin_ficha.json()
    assert llena.status_code == 503 and gastos_llena == [], (llena.status_code, gastos_llena)
    assert f"{api._CURVAS_VIVAS} libros" in llena.json()["detail"], llena.json()
    assert hueco.status_code == 200, hueco.status_code
    # nosniff en el audio.
    mp3 = api._DIR_AUDIO / f"prueba_{uuid.uuid4().hex[:8]}.mp3"
    mp3.parent.mkdir(parents=True, exist_ok=True)
    mp3.write_bytes(b"ID3" + b"\x00" * 64)
    try:
        audio = cliente.get(f"/api/audio/{mp3.name}")
    finally:
        mp3.unlink(missing_ok=True)
    assert audio.status_code == 200 and audio.headers.get("x-content-type-options") == "nosniff", audio.headers
    return f"medidas 3×200 y 3×429, curva 1 ficha, cola llena 503 sin ficha, audio nosniff"


if __name__ == "__main__":
    print("API de LiteraLevel\n")
    for fn in (sin_lector_no_hay_datos, lector_corto_no_vale, perfiles_aislados,
               cuestionario_forma, una_respuesta_estima_sin_guardar,
               respuestas_de_fuera_se_validan, muestra_que_no_es_prosa_no_carga_el_modelo,
               id_que_es_ruta_no_pasa, abrir_libro_libre, progreso_y_estanteria_aislados,
               progreso_fuera_de_rango, subir_txt_y_solo_lo_ve_quien_lo_subio,
               palabra_sin_clave_no_sale_a_la_red, palabra_larguisima_y_frase,
               cuaderno_aislado, lo_de_pago_sin_clave_no_cobra_ni_gasta_ficha,
               con_perfiles_sin_entrar_no_paga, audio_y_fonemas_sin_traversal,
               estado_sin_rutas, curva_de_libro_sin_medir, cors_del_front,
               libro_con_licencia_abre_en_la_obra, cuento_de_parrafos_cortos_no_pierde_el_principio,
               error_inesperado_sin_traza, voz_audio_por_palabra_y_falladas_con_su_frase,
               voz_prepara_temporal_antes_de_cobrar,
               dudoso_coherente_con_el_aviso_de_lexicon, corte_de_la_boca_en_svg,
               corte_de_una_pasada_con_la_duracion_del_audio, indice_de_romanos_de_una_letra_no_abre_el_libro,
               ritmo_de_la_lectura_con_nivel_y_audio_natural, topes_de_medir_y_de_la_curva,
               temas_para_la_portada, portada_por_ia_si_existe, plurales_de_los_minutos,
               nota_de_nivel_dice_libros_y_cuentos,
               fonema_de_la_correccion_en_britanico, subida_grande_se_corta_antes_de_leerla_entera,
               topes_de_subidas_por_lector_y_por_hora, palabra_que_falla_solo_devuelve_lo_cobrado,
               libro_subido_se_ve_con_su_nombre, palabra_escrita_no_se_atribuye_al_libro,
               aviso_de_contenido_en_ficha_y_tarjeta, medido_en_bloque_en_ficha_y_tarjeta,
               buscar_devuelve_la_franja_y_la_marca, precarga_y_peticion_comparten_el_catalogo,
               silencio_devuelve_el_uso_con_tope_diario, voz_sin_voz_devuelve_a_la_cuenta_cobrada,
               salud_dice_si_el_buscador_esta_listo, voz_cobra_y_devuelve_a_la_misma_cuenta,
               curva_de_un_solo_capitulo_sin_forma, devolucion_sin_cobro_ni_registro_raro,
               voz_subida_y_palabra_no_bloquean_a_los_demas,
               validacion_sin_eco_de_la_entrada, dos_subidas_a_la_vez_no_pasan_el_tope_ni_rompen_los_nombres,
               cache_lexica_serializa_la_conexion_entre_hilos,
               borrar_subido_todo_bajo_el_candado, abrir_un_libro_no_retiene_el_candado_de_otros,
               nombres_que_no_se_pueden_escribir_lo_dicen,
               devolucion_va_a_la_cuenta_cobrada,
               sinopsis_simultaneas_una_generacion, borrar_subido_libera_el_cupo,
               historial_de_voz_ilegible_avisa, cita_recorta_sin_perder_la_oracion,
               extracto_de_seguir_leyendo_salta_la_licencia, errores_con_mensaje_propio_y_no_el_500_generico):
        prueba(fn.__name__.replace("_", " "), fn)
    print(f"\n{HECHAS - len(FALLOS)} de {HECHAS} bien")
    if FALLOS:
        print("\nFALLOS:\n" + "\n".join(f"  - {f}" for f in FALLOS))
        sys.exit(1)
