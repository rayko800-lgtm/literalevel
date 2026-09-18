"""D3.2: persistencia de repaso (`app/cuaderno.py`) y su frontera HTTP
(`GET/POST /api/repaso` en `app/api.py`).

Dos partes:
- Directas sobre `cuaderno.py` (rápidas, sin FastAPI): esquema, migración,
  identidad por `consulta_id`, evento append-only.
- Sobre la API (mismo patrón que `pruebas_api.py`): aislamiento entre
  lectores, validación del enum, error real si falla el guardado.

Uso:  python -X utf8 pruebas_repaso.py
"""
from __future__ import annotations

import os
import sqlite3
import sys
import traceback
import uuid
from pathlib import Path

sys.path.insert(0, "app")
import pruebas_tmp  # noqa: E402

CARPETA = Path(pruebas_tmp.carpeta("literalevel_repaso_"))

import cuaderno  # noqa: E402

# Igual que pruebas_api.py: el entorno se fija ANTES de importar `api`.
os.environ["LITERALEVEL_DATOS"] = pruebas_tmp.carpeta("literalevel_repaso_api_")
os.environ["SPACE_ID"] = "pruebas/literalevel"
os.environ.setdefault("LITERALEVEL_PRECARGA", "0")
os.environ.pop("LITERALEVEL_CUENTAS", None)
import config as config_mod  # noqa: E402
config_mod.cargar = lambda *a, **k: None
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import api  # noqa: E402

cliente = TestClient(api.app, raise_server_exceptions=False)
LIBRE = "SWV369"  # The Red Raincoat, StoryWeaver: sin red


def nuevo_lector() -> dict:
    return {"X-Lector": str(uuid.uuid4())}


def _ok(r, estado=200):
    assert r.status_code == estado, f"{r.status_code}: {r.text[:300]}"
    return r.json()


FALLOS: list[str] = []
HECHAS = 0


def prueba(nombre: str, fn):
    global HECHAS
    HECHAS += 1
    try:
        r = fn()
        assert r is not False, "la prueba devolvio False"
        print(f"  ok    {nombre:<52} {str(r)[:70]}")
    except Exception as e:
        FALLOS.append(f"{nombre}: {type(e).__name__}: {e}")
        print(f"  FALLA {nombre:<52} {type(e).__name__}: {e}")
        traceback.print_exc(limit=3)


def _db(nombre: str) -> Path:
    return CARPETA / f"{nombre}_{uuid.uuid4().hex[:8]}.db"


# --- Directas sobre cuaderno.py --------------------------------------------

def esquema_se_crea_en_db_nueva():
    ruta = _db("nueva")
    cuaderno.registrar(palabra="tired", lema="tired", oracion="She was tired.", ruta=ruta)
    con = sqlite3.connect(str(ruta))
    tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    assert {"consultas", "repasos"} <= tablas, tablas
    return "consultas + repasos"


def db_antigua_migra_sin_perder_consultas():
    """Simula un cuaderno.db de ANTES de D3.2: solo `consultas`, sin `repasos`."""
    ruta = _db("antigua")
    con = sqlite3.connect(str(ruta))
    con.execute("""CREATE TABLE consultas (
        id INTEGER PRIMARY KEY, palabra TEXT NOT NULL, lema TEXT NOT NULL,
        categoria TEXT, sentido TEXT, oracion TEXT NOT NULL, libro TEXT,
        capitulo INTEGER, banda TEXT, zipf REAL, creado TEXT NOT NULL)""")
    con.execute("INSERT INTO consultas (palabra, lema, oracion, creado) VALUES "
                "('tired', 'tired', 'She was tired.', '2026-01-01T00:00:00')")
    con.commit()
    con.close()
    # Cualquier función que pase por `_conectar()` migra la tabla que falta.
    anotaciones_antes = cuaderno.ultimas(10, ruta)
    assert len(anotaciones_antes) == 1 and anotaciones_antes[0].palabra == "tired", anotaciones_antes
    con = sqlite3.connect(str(ruta))
    tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    filas_consultas = con.execute("SELECT COUNT(*) FROM consultas").fetchone()[0]
    con.close()
    assert "repasos" in tablas, tablas
    assert filas_consultas == 1, "la migración no debe tocar consultas ya existentes"
    return "repasos añadida, consultas intacta"


def por_id_encuentra_la_fila_exacta():
    ruta = _db("por_id")
    cuaderno.registrar(palabra="raincoat", lema="raincoat", oracion="A red raincoat.", ruta=ruta)
    todas = cuaderno.ultimas(1, ruta)
    a = cuaderno.por_id(todas[0].id, ruta)
    assert a is not None and a.palabra == "raincoat", a
    assert cuaderno.por_id(999999, ruta) is None, "un id inventado no debe encontrar nada"
    return f"id={a.id}"


def registrar_repaso_guarda_evento_append_only():
    ruta = _db("evento")
    cuaderno.registrar(palabra="tired", lema="tired", oracion="She was tired.",
                       sentido="cansada", libro="PG11", capitulo=2, ruta=ruta)
    cid = cuaderno.ultimas(1, ruta)[0].id
    assert cuaderno.registrar_repaso(consulta_id=cid, evaluacion="si", ruta=ruta)
    con = sqlite3.connect(str(ruta))
    fila = con.execute("SELECT consulta_id, lema, evaluacion, palabra, oracion, sentido,"
                       " libro, capitulo FROM repasos").fetchone()
    con.close()
    assert fila == (cid, "tired", "si", "tired", "She was tired.", "cansada", "PG11", 2), fila
    return "snapshot correcto, tomado del servidor"


def evaluacion_invalida_no_se_guarda():
    ruta = _db("invalida")
    cuaderno.registrar(palabra="tired", lema="tired", oracion="She was tired.", ruta=ruta)
    cid = cuaderno.ultimas(1, ruta)[0].id
    assert cuaderno.registrar_repaso(consulta_id=cid, evaluacion="mas o menos", ruta=ruta) is False
    con = sqlite3.connect(str(ruta))
    n = con.execute("SELECT COUNT(*) FROM repasos").fetchone()[0]
    con.close()
    assert n == 0, "una evaluación fuera del enum no debe insertar nada"
    return "rechazada, 0 filas"


def consulta_id_inexistente_no_inserta():
    ruta = _db("sin_consulta")
    assert cuaderno.registrar_repaso(consulta_id=42, evaluacion="no", ruta=ruta) is False
    return "False sin consulta previa"


def mismo_lema_dos_contextos_dos_snapshots_propios():
    ruta = _db("dos_contextos")
    cuaderno.registrar(palabra="bank", lema="bank", oracion="She sat on the river bank.",
                       sentido="orilla", ruta=ruta)
    cuaderno.registrar(palabra="bank", lema="bank", oracion="He works at a bank.",
                       sentido="entidad financiera", ruta=ruta)
    filas = cuaderno.ultimas(10, ruta)
    assert len(filas) == 2, filas
    for f in filas:
        assert cuaderno.registrar_repaso(consulta_id=f.id, evaluacion="dude", ruta=ruta)
    con = sqlite3.connect(str(ruta))
    sentidos = {r[0] for r in con.execute("SELECT sentido FROM repasos")}
    con.close()
    assert sentidos == {"orilla", "entidad financiera"}, sentidos
    return "cada evento con su propio sentido, sin mezclarse"


def varias_evaluaciones_historicas_se_conservan():
    ruta = _db("historial")
    cuaderno.registrar(palabra="tired", lema="tired", oracion="She was tired.", ruta=ruta)
    cid = cuaderno.ultimas(1, ruta)[0].id
    for ev in ("no", "dude", "si"):
        assert cuaderno.registrar_repaso(consulta_id=cid, evaluacion=ev, ruta=ruta)
    con = sqlite3.connect(str(ruta))
    evaluaciones = [r[0] for r in con.execute("SELECT evaluacion FROM repasos ORDER BY id")]
    con.close()
    assert evaluaciones == ["no", "dude", "si"], evaluaciones
    return "3 eventos, ninguno sobrescrito"


def db_corrupta_degrada_sin_lanzar():
    ruta = _db("corrupta")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(b"esto no es una base de datos sqlite")
    assert cuaderno.por_id(1, ruta) is None
    assert cuaderno.registrar_repaso(consulta_id=1, evaluacion="si", ruta=ruta) is False
    return "None / False, sin excepción"


# --- Sobre la API ------------------------------------------------------------

def _consulta_id_de(lector: dict) -> int:
    caps = _ok(cliente.get(f"/api/libros/{LIBRE}", headers=lector))
    _ok(cliente.post("/api/palabra", headers=lector,
                     json={"libro_id": LIBRE, "capitulo": caps["inicial"],
                           "palabra": "raincoat", "etapa": "completa"}))
    repaso = _ok(cliente.get("/api/repaso", headers=lector))
    tarjeta = next(p for p in repaso["palabras"] if p["palabra"].lower() == "raincoat")
    assert isinstance(tarjeta["consulta_id"], int), tarjeta
    return tarjeta["consulta_id"]


def get_repaso_trae_consulta_id():
    lector = nuevo_lector()
    cid = _consulta_id_de(lector)
    return f"consulta_id={cid}"


def evaluar_guarda_y_responde_ok():
    lector = nuevo_lector()
    cid = _consulta_id_de(lector)
    d = _ok(cliente.post("/api/repaso", headers=lector, json={"consulta_id": cid, "evaluacion": "si"}))
    assert d == {"ok": True}, d
    return "ok:true"


def evaluacion_fuera_del_enum_da_422():
    lector = nuevo_lector()
    cid = _consulta_id_de(lector)
    r = cliente.post("/api/repaso", headers=lector, json={"consulta_id": cid, "evaluacion": "mas o menos"})
    assert r.status_code == 422, r.status_code
    return "422"


def consulta_id_de_otro_lector_da_404():
    """El corazón de D2 aplicado a repaso: un X-Lector no puede evaluar lo de otro."""
    a, b = nuevo_lector(), nuevo_lector()
    cid_de_a = _consulta_id_de(a)
    r = cliente.post("/api/repaso", headers=b, json={"consulta_id": cid_de_a, "evaluacion": "si"})
    assert r.status_code == 404, r.status_code
    # Y sí funciona para su dueño real.
    _ok(cliente.post("/api/repaso", headers=a, json={"consulta_id": cid_de_a, "evaluacion": "si"}))
    return "404 para B, 200 para A"


def consulta_id_inventado_da_404_via_api():
    lector = nuevo_lector()
    r = cliente.post("/api/repaso", headers=lector, json={"consulta_id": 999999999, "evaluacion": "no"})
    assert r.status_code == 404, r.status_code
    return "404"


def sin_lector_no_evalua_nada():
    r = cliente.post("/api/repaso", json={"consulta_id": 1, "evaluacion": "no"})
    assert r.status_code in (400, 422), r.status_code
    r2 = cliente.get("/api/repaso")
    assert r2.status_code in (400, 422), r2.status_code
    return "400/422 en los dos"


if __name__ == "__main__":
    print("Repaso persistente — cuaderno.py\n")
    for fn in (esquema_se_crea_en_db_nueva, db_antigua_migra_sin_perder_consultas,
               por_id_encuentra_la_fila_exacta, registrar_repaso_guarda_evento_append_only,
               evaluacion_invalida_no_se_guarda, consulta_id_inexistente_no_inserta,
               mismo_lema_dos_contextos_dos_snapshots_propios,
               varias_evaluaciones_historicas_se_conservan, db_corrupta_degrada_sin_lanzar,
               get_repaso_trae_consulta_id, evaluar_guarda_y_responde_ok,
               evaluacion_fuera_del_enum_da_422, consulta_id_de_otro_lector_da_404,
               consulta_id_inventado_da_404_via_api, sin_lector_no_evalua_nada):
        prueba(fn.__name__.replace("_", " "), fn)
    print(f"\n{HECHAS - len(FALLOS)} de {HECHAS} bien")
    if FALLOS:
        print("\nFALLOS:\n" + "\n".join(f"  - {f}" for f in FALLOS))
        sys.exit(1)
