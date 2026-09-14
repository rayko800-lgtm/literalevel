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
os.environ["LITERALEVEL_DATOS"] = tempfile.mkdtemp(prefix="literalevel_api_")
# La nube: carpetas por lector. Es el caso que importa, porque en local todos
# comparten la carpeta a proposito y el aislamiento no se veria.
os.environ["SPACE_ID"] = "pruebas/literalevel"
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

    def practicar_doble(ruta, frase, guardar_fallos=True):
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
    ui._puede_pagar = lambda pet: (True, "")
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

    originales = (config.falta, ui._puede_pagar, api._va_a_costar, ui.consultor, cuentas.devolver)
    cuentas.devolver = lambda base, codigo: devueltos.append(codigo)
    ui.consultor = lambda: Roto()
    api._va_a_costar = lambda pet: False
    config.falta = lambda: False
    cuerpo = {"palabra": "house", "etapa": "completa"}
    try:
        ui._puede_pagar = lambda pet: (False, "Entra con tu perfil.")
        sin_cobro = cliente.post("/api/palabra", headers=A, json=cuerpo)
        devueltos_sin_cobro = len(devueltos)
        ui._puede_pagar = lambda pet: (True, "")
        con_cobro = cliente.post("/api/palabra", headers=A, json=cuerpo)
    finally:
        config.falta, ui._puede_pagar, api._va_a_costar, ui.consultor, cuentas.devolver = originales
    assert (sin_cobro.status_code, con_cobro.status_code) == (503, 503), (sin_cobro.status_code, con_cobro.status_code)
    assert devueltos_sin_cobro == 0, "devolvió un uso que no se cobró"
    assert len(devueltos) == 1, devueltos
    return "sin cobro 0 devueltos, con cobro 1"


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


def corte_de_la_boca_en_svg():
    """Las animaciones de 4e, servidas al front: tipo, caché, sin ejecutar nada
    aunque se abran sueltas, quieto distinto de animado y rechazo de lo raro."""
    from urllib.parse import quote
    theta = "/api/articulacion/ga/" + quote("θ") + ".svg"
    r = cliente.get(theta)
    assert r.status_code == 200, (r.status_code, r.text[:200])
    assert r.headers["content-type"].startswith("image/svg+xml"), r.headers
    assert "max-age=2592000" in r.headers["cache-control"], r.headers
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
               dudoso_coherente_con_el_aviso_de_lexicon, corte_de_la_boca_en_svg,
               fonema_de_la_correccion_en_britanico, subida_grande_se_corta_antes_de_leerla_entera,
               topes_de_subidas_por_lector_y_por_hora, palabra_que_falla_solo_devuelve_lo_cobrado,
               libro_subido_se_ve_con_su_nombre, palabra_escrita_no_se_atribuye_al_libro):
        prueba(fn.__name__.replace("_", " "), fn)
    print(f"\n{HECHAS - len(FALLOS)} de {HECHAS} bien")
    if FALLOS:
        print("\nFALLOS:\n" + "\n".join(f"  - {f}" for f in FALLOS))
        sys.exit(1)
