"""D3.3: agregados de progreso (`app/cuaderno.py`: `por_dia`/`ultimos_repasos`)
y su frontera HTTP (`GET /api/progreso` en `app/api.py`).

Dos partes: directas sobre `cuaderno.py` (fechas/zona horaria/horizonte de
repasos) y sobre la API (payload agregado, aislamiento entre lectores).

Uso:  python -X utf8 pruebas_progreso.py
"""
from __future__ import annotations

import os
import sqlite3
import sys
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, "app")
import pruebas_tmp  # noqa: E402

CARPETA = Path(pruebas_tmp.carpeta("literalevel_progreso_"))

import cuaderno  # noqa: E402

os.environ["LITERALEVEL_DATOS"] = pruebas_tmp.carpeta("literalevel_progreso_api_")
os.environ["SPACE_ID"] = "pruebas/literalevel"
os.environ.setdefault("LITERALEVEL_PRECARGA", "0")
os.environ.pop("LITERALEVEL_CUENTAS", None)
import config as config_mod  # noqa: E402
config_mod.cargar = lambda *a, **k: None
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

import api  # noqa: E402

cliente = TestClient(api.app, raise_server_exceptions=False)


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


def _consulta(ruta: Path, creado: str, lema: str = "x") -> None:
    """Inserta una fila de `consultas` con un `creado` EXACTO (a diferencia
    de `cuaderno.registrar()`, que siempre usa la hora actual) — para poder
    poner una consulta en un dia concreto del pasado."""
    cuaderno.registrar(palabra=lema, lema=lema, oracion="una frase.", ruta=ruta)  # crea el esquema
    con = sqlite3.connect(str(ruta))
    con.execute("UPDATE consultas SET creado=? WHERE id=(SELECT MAX(id) FROM consultas)", (creado,))
    con.commit()
    con.close()


def _repaso(ruta: Path, evaluacion: str, creado: str | None = None) -> None:
    cuaderno.registrar(palabra="x", lema="x", oracion="frase.", ruta=ruta)
    cid = cuaderno.ultimas(1, ruta)[0].id
    assert cuaderno.registrar_repaso(consulta_id=cid, evaluacion=evaluacion, ruta=ruta)
    if creado:
        con = sqlite3.connect(str(ruta))
        con.execute("UPDATE repasos SET creado=? WHERE id=(SELECT MAX(id) FROM repasos)", (creado,))
        con.commit()
        con.close()


def _utc(hace_dias: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=hace_dias)).isoformat()


# --- por_dia -------------------------------------------------------------

def sin_consultas_14_ceros():
    ruta = _db("vacio")
    dias = cuaderno.por_dia(None, 14, ruta)
    assert len(dias) == 14, len(dias)
    assert all(c == 0 for _, c in dias), dias
    return "14 dias, todo 0"


def un_dia_varias_consultas():
    ruta = _db("undia")
    for _ in range(3):
        _consulta(ruta, _utc(0), "hoy")
    dias = cuaderno.por_dia(None, 14, ruta)
    assert dias[-1][1] == 3, dias[-1]
    assert sum(c for _, c in dias) == 3, dias
    return f"hoy={dias[-1]}"


def varios_dias_y_huecos():
    ruta = _db("huecos")
    _consulta(ruta, _utc(0), "a")
    _consulta(ruta, _utc(2), "b")
    _consulta(ruta, _utc(2), "c")
    dias = cuaderno.por_dia(None, 14, ruta)
    assert dias[-1][1] == 1, dias[-1]      # hoy
    assert dias[-2][1] == 0, dias[-2]      # ayer: hueco
    assert dias[-3][1] == 2, dias[-3]      # anteayer
    return f"hoy={dias[-1][1]} ayer={dias[-2][1]} anteayer={dias[-3][1]}"


def mismo_lema_dos_veces_cuenta_dos_consultas():
    ruta = _db("mismolema")
    _consulta(ruta, _utc(0), "raincoat")
    _consulta(ruta, _utc(0), "raincoat")
    dias = cuaderno.por_dia(None, 14, ruta)
    assert dias[-1][1] == 2, dias[-1]  # dos CONSULTAS, no una palabra distinta
    return "2 consultas del mismo lema"


def corte_exacto_14_dias():
    """La ventana son 14 dias de CALENDARIO incluyendo hoy: hoy-13 .. hoy.
    A mediodia UTC, hoy-13 esta dentro y hoy-14 ya esta fuera — usar fechas
    de calendario exactas, no "hace X.Y dias", que depende de la hora actual."""
    ruta = _db("corte")
    hoy = datetime.now(timezone.utc).date()
    dentro = datetime.combine(hoy - timedelta(days=13), datetime.min.time(), timezone.utc).replace(hour=12)
    fuera = datetime.combine(hoy - timedelta(days=14), datetime.min.time(), timezone.utc).replace(hour=12)
    _consulta(ruta, dentro.isoformat(), "dentro")
    _consulta(ruta, fuera.isoformat(), "fuera")
    dias = cuaderno.por_dia(None, 14, ruta)
    assert sum(c for _, c in dias) == 1, dias
    assert dias[0][1] == 1, dias[0]  # el primer dia de la ventana es hoy-13
    return "solo la de dentro de 14 dias cuenta"


def fecha_corrupta_se_ignora():
    ruta = _db("corrupta_fecha")
    cuaderno.registrar(palabra="x", lema="x", oracion="frase.", ruta=ruta)
    con = sqlite3.connect(str(ruta))
    con.execute("UPDATE consultas SET creado='no-es-una-fecha' WHERE id=(SELECT MAX(id) FROM consultas)")
    con.commit()
    con.close()
    dias = cuaderno.por_dia(None, 14, ruta)  # no debe lanzar
    assert sum(c for _, c in dias) == 0, dias
    return "ignorada, sin excepcion"


def orden_cronologico_ascendente():
    ruta = _db("orden")
    dias = cuaderno.por_dia(None, 14, ruta)
    fechas = [f for f, _ in dias]
    assert fechas == sorted(fechas), fechas
    return f"{fechas[0]} .. {fechas[-1]}"


# --- Zona horaria ----------------------------------------------------------

def zona_utc_explicita():
    ruta = _db("tz_utc")
    _consulta(ruta, "2026-01-15T12:00:00+00:00")
    dias = cuaderno.por_dia("UTC", 14, ruta)
    total = sum(c for _, c in dias)
    # Puede caer dentro o fuera de la ventana segun cuando se corra la prueba;
    # lo que importa es que no lanza y que el total es 0 o 1, nunca mas.
    assert total in (0, 1), total
    return f"total={total}"


def zona_offset_negativo_desplaza_el_dia():
    """02:00 UTC menos 8 h (Los Angeles) cae en el dia UTC anterior."""
    ruta = _db("tz_offset")
    ahora_utc = datetime.now(timezone.utc)
    medianoche_utc = ahora_utc.replace(hour=2, minute=0, second=0, microsecond=0)
    _consulta(ruta, medianoche_utc.isoformat())
    dias_utc = cuaderno.por_dia("UTC", 14, ruta)
    dias_la = cuaderno.por_dia("America/Los_Angeles", 14, ruta)
    fecha_utc = next(f for f, c in dias_utc if c == 1)
    fecha_la = next(f for f, c in dias_la if c == 1)
    assert fecha_la < fecha_utc, (fecha_la, fecha_utc)
    return f"UTC={fecha_utc} LA={fecha_la}"


def evento_cerca_de_medianoche_cambia_de_dia_local():
    ruta = _db("tz_medianoche")
    ahora_utc = datetime.now(timezone.utc)
    # 23:50 UTC de "ayer" (en referencia al reloj de la maquina): en una zona
    # muy adelantada (Tokio, UTC+9) ya es "hoy" localmente.
    tarde_utc = (ahora_utc - timedelta(days=1)).replace(hour=23, minute=50, second=0, microsecond=0)
    _consulta(ruta, tarde_utc.isoformat())
    dias_utc = cuaderno.por_dia("UTC", 14, ruta)
    dias_tokio = cuaderno.por_dia("Asia/Tokyo", 14, ruta)
    fecha_utc = next(f for f, c in dias_utc if c == 1)
    fecha_tokio = next(f for f, c in dias_tokio if c == 1)
    assert fecha_tokio > fecha_utc, (fecha_tokio, fecha_utc)
    return f"UTC={fecha_utc} Tokio={fecha_tokio}"


def zona_invalida_cae_a_utc_sin_lanzar():
    ruta = _db("tz_invalida")
    _consulta(ruta, _utc(0))
    dias_invalida = cuaderno.por_dia("Zona/Inventada", 14, ruta)
    dias_utc = cuaderno.por_dia("UTC", 14, ruta)
    assert dias_invalida == dias_utc, (dias_invalida, dias_utc)
    return "identico a UTC"


def zona_vacia_o_none_cae_a_utc():
    ruta = _db("tz_none")
    _consulta(ruta, _utc(0))
    assert cuaderno.por_dia(None, 14, ruta) == cuaderno.por_dia("", 14, ruta)
    return "None == ''"


# --- ultimos_repasos ---------------------------------------------------------

def repasos_vacio():
    ruta = _db("repasos_vacio")
    assert cuaderno.ultimos_repasos(20, ruta) == []
    return "[]"


def repasos_solo_si():
    ruta = _db("repasos_si")
    for _ in range(3):
        _repaso(ruta, "si")
    evs = cuaderno.ultimos_repasos(20, ruta)
    assert evs == ["si", "si", "si"], evs
    return evs


def repasos_mezcla():
    ruta = _db("repasos_mezcla")
    for ev in ("no", "dude", "si", "si"):
        _repaso(ruta, ev)
    evs = cuaderno.ultimos_repasos(20, ruta)
    assert sorted(evs) == sorted(["no", "dude", "si", "si"]), evs
    assert evs[0] == "si", "el ultimo insertado va primero"
    return evs


def repasos_respeta_el_horizonte():
    ruta = _db("repasos_horizonte")
    for _ in range(25):
        _repaso(ruta, "si")
    evs = cuaderno.ultimos_repasos(20, ruta)
    assert len(evs) == 20, len(evs)
    return f"{len(evs)} de 25"


def repasos_menos_de_20_usa_los_que_hay():
    ruta = _db("repasos_pocos")
    for ev in ("no", "dude"):
        _repaso(ruta, ev)
    evs = cuaderno.ultimos_repasos(20, ruta)
    assert len(evs) == 2, evs
    return evs


# --- API -----------------------------------------------------------------

def api_progreso_forma_del_payload():
    lector = nuevo_lector()
    d = _ok(cliente.get("/api/progreso", headers=lector))
    assert len(d["palabras_por_dia"]) == 14, d["palabras_por_dia"]
    assert set(d["repasos"]) == {"si", "dude", "no", "total"}, d["repasos"]
    assert d["repasos"]["total"] == 0, d["repasos"]
    # Nunca una anotacion completa: sin 'oracion', 'sentido' ni 'palabra' sueltos.
    assert "entradas" not in d and "palabras" not in d, d
    return "14 dias, repasos en 0, sin anotaciones completas"


def api_progreso_con_tz_del_navegador():
    lector = nuevo_lector()
    d = _ok(cliente.get("/api/progreso", headers=lector, params={"tz": "America/Los_Angeles"}))
    assert len(d["palabras_por_dia"]) == 14, d
    return "acepta tz sin romper"


def api_progreso_tz_invalida_no_rompe():
    lector = nuevo_lector()
    d = _ok(cliente.get("/api/progreso", headers=lector, params={"tz": "Nada/Real"}))
    assert len(d["palabras_por_dia"]) == 14, d
    return "degrada a UTC, 200 igual"


def api_progreso_aisla_entre_lectores():
    a, b = nuevo_lector(), nuevo_lector()
    caps = _ok(cliente.get("/api/libros/SWV369", headers=a))
    _ok(cliente.post("/api/palabra", headers=a,
                     json={"libro_id": "SWV369", "capitulo": caps["inicial"],
                           "palabra": "raincoat", "etapa": "completa"}))
    da = _ok(cliente.get("/api/progreso", headers=a))
    db_ = _ok(cliente.get("/api/progreso", headers=b))
    assert sum(x["consultas"] for x in da["palabras_por_dia"]) >= 1, da
    assert sum(x["consultas"] for x in db_["palabras_por_dia"]) == 0, db_
    return "A tiene 1+, B tiene 0"


def sin_lector_no_hay_progreso():
    r = cliente.get("/api/progreso")
    assert r.status_code in (400, 422), r.status_code
    return "400/422"


if __name__ == "__main__":
    print("Progreso (D3.3) — cuaderno.py y API\n")
    for fn in (sin_consultas_14_ceros, un_dia_varias_consultas, varios_dias_y_huecos,
               mismo_lema_dos_veces_cuenta_dos_consultas, corte_exacto_14_dias,
               fecha_corrupta_se_ignora, orden_cronologico_ascendente,
               zona_utc_explicita, zona_offset_negativo_desplaza_el_dia,
               evento_cerca_de_medianoche_cambia_de_dia_local,
               zona_invalida_cae_a_utc_sin_lanzar, zona_vacia_o_none_cae_a_utc,
               repasos_vacio, repasos_solo_si, repasos_mezcla,
               repasos_respeta_el_horizonte, repasos_menos_de_20_usa_los_que_hay,
               api_progreso_forma_del_payload, api_progreso_con_tz_del_navegador,
               api_progreso_tz_invalida_no_rompe, api_progreso_aisla_entre_lectores,
               sin_lector_no_hay_progreso):
        prueba(fn.__name__.replace("_", " "), fn)
    print(f"\n{HECHAS - len(FALLOS)} de {HECHAS} bien")
    if FALLOS:
        print("\nFALLOS:\n" + "\n".join(f"  - {f}" for f in FALLOS))
        sys.exit(1)
