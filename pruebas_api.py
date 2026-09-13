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
    cabecera = ("The Project Gutenberg eBook of Pruebas de lectura\n\n"
                "*** START OF THE PROJECT GUTENBERG EBOOK PRUEBAS DE LECTURA ***\n\n"
                "Produced by Alguien Inventado and the Online Distributed Proofreading "
                "Team at https://www.pgdp.net\n\n"
                "PRUEBAS DE LECTURA\n\nCONTENTS.\n\nThe Garden\n\nThe River\n\n")
    parrafo = " ".join(["The old gardener walked slowly along the path beside the quiet river."] * 5)
    prosa = "\n\n".join([parrafo] * 20)
    pie = ("\n\n*** END OF THE PROJECT GUTENBERG EBOOK PRUEBAS DE LECTURA ***\n\n"
           + "The Full Project Gutenberg License applies to this work. " * 80)
    d = _ok(cliente.post("/api/libros", headers=A,
                         files={"archivo": ("licencia.txt", (cabecera + prosa + pie).encode(), "text/plain")}))
    c = _ok(cliente.get(f"/api/libros/{d['id']}/capitulos/{d['inicial']}", headers=A))
    texto = " ".join(c["parrafos"]).lower()
    assert c["parrafos"][0].startswith("The old gardener"), c["parrafos"][:3]
    for sucio in ("produced by", "proofreading", "project gutenberg", "start of the", "contents"):
        assert sucio not in texto, f"el capitulo sigue trayendo «{sucio}»"
    for _ in range(3):
        f = _ok(cliente.get(f"/api/libros/{d['id']}/capitulos/{d['inicial']}/frase", headers=A))["frase"]
        assert f and "produced" not in f.lower() and "gutenberg" not in f.lower(), f
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
               error_inesperado_sin_traza):
        prueba(fn.__name__.replace("_", " "), fn)
    print(f"\n{HECHAS - len(FALLOS)} de {HECHAS} bien")
    if FALLOS:
        print("\nFALLOS:\n" + "\n".join(f"  - {f}" for f in FALLOS))
        sys.exit(1)
