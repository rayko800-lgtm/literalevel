"""Eos para los audios nuevos (`app/eos.py` y sus rutas en `app/api.py`).

    python -X utf8 pruebas_eos.py

Sin catálogo ni modelo: `api` se importa pero no carga nada pesado, y todo
escribe en un temporal (`LITERALEVEL_DATOS`)."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "app"))
os.environ["LITERALEVEL_DATOS"] = tempfile.mkdtemp(prefix="literalevel_eos_")
os.environ["LITERALEVEL_SIN_CLAVES"] = "1"
os.environ.setdefault("LITERALEVEL_PRECARGA", "0")
os.environ.pop("LITERALEVEL_EOS_TOKEN", None)

import eos  # noqa: E402

MP4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 40
FALLOS = 0


def ok(cond, nombre):
    global FALLOS
    print(("OK   " if cond else "FALLO"), nombre)
    if not cond:
        FALLOS += 1


def modulo():
    print("-- módulo")
    ok(eos.pedir("../x.mp3")["estado"] == "no", "nombre con ruta: no")
    ok(eos.pedir("frase.mp3")["estado"] == "sin_trabajador", "sin token: sin_trabajador, pero queda apuntado")
    ok(len(eos.cola()) == 1 and eos.cola()[0]["audio"] == "frase.mp3", "la cola lo tiene")
    os.environ["LITERALEVEL_EOS_TOKEN"] = "secreto-de-prueba"
    r = eos.pedir("frase.mp3", "The cat sat.")
    ok(r["estado"] == "pendiente" and eos.clave_valida(r["clave"]), "con token: pendiente")
    ok(eos.estado(r["clave"])["estado"] == "pendiente", "estado: pendiente")
    ok(eos.estado("zzz")["estado"] == "no", "clave inválida: no")
    ok(not eos.entregar(r["clave"], b"hola que tal esto no es mp4"), "entregar rechaza lo que no es mp4")
    ok(eos.fallo(r["clave"], "Chrome caído"), "fallo apuntado")
    ok(eos.estado(r["clave"])["estado"] == "fallo", "estado: fallo")
    ok(eos.pedir("frase.mp3")["estado"] == "fallo", "fallo reciente: no se reencola")
    ok(eos.cola() == [], "la cola no lo devuelve fallido")
    eos.REINTENTO_FALLO_S = 0
    time.sleep(0.01)
    ok(eos.pedir("frase.mp3")["estado"] == "pendiente", "pasado el plazo: se reencola")
    ok(eos.entregar(r["clave"], MP4), "entregar acepta el mp4")
    e = eos.estado(r["clave"])
    ok(e["estado"] == "listo" and e["video"] == f"/api/eos/video/{r['clave']}.mp4", "estado: listo con vídeo")
    ok(eos.cola() == [], "entregado sale de la cola")
    ok(eos.pedir("frase.mp3")["estado"] == "listo", "pedir de nuevo: listo")
    ok(not eos.token_valido("otro") and eos.token_valido("secreto-de-prueba"), "token")


def rutas():
    print("-- rutas")
    from fastapi.testclient import TestClient
    import api
    c = TestClient(api.app, raise_server_exceptions=False)
    cab = {"X-Lector": str(uuid.uuid4())}
    (api._DIR_AUDIO).mkdir(parents=True, exist_ok=True)
    (api._DIR_AUDIO / "leida.mp3").write_bytes(b"ID3" + b"\x00" * 100)
    r = c.post("/api/eos/pedir", json={"audio": "/api/audio/no-existe.mp3", "texto": "x"}, headers=cab)
    ok(r.status_code == 404, "pedir un audio que no existe: 404")
    r = c.post("/api/eos/pedir", json={"audio": "/api/audio/leida.mp3", "texto": "I read it."}, headers=cab)
    ok(r.status_code == 200 and r.json()["estado"] == "pendiente", f"pedir: pendiente ({r.status_code})")
    clave = r.json()["clave"]
    ok(c.get("/api/eos/cola").status_code == 403, "cola sin token: 403")
    t = {"X-Eos-Token": "secreto-de-prueba"}
    r = c.get("/api/eos/cola", headers=t)
    ok(r.status_code == 200 and r.json()["trabajos"][0]["audio_url"] == "/api/audio/leida.mp3", "cola con token")
    r = c.post(f"/api/eos/entregar/{clave}", content=b"no es mp4", headers={**t, "Content-Type": "video/mp4"})
    ok(r.status_code == 422, "entregar basura: 422")
    r = c.post(f"/api/eos/entregar/{clave}", content=MP4, headers={**t, "Content-Type": "video/mp4"})
    ok(r.status_code == 200 and r.json()["estado"] == "listo", "entregar mp4: listo")
    r = c.get(f"/api/eos/estado/{clave}")
    ok(r.json()["estado"] == "listo", "estado por ruta: listo")
    r = c.get(f"/api/eos/video/{clave}.mp4")
    ok(r.status_code == 200 and r.headers["content-type"] == "video/mp4" and r.content == MP4, "vídeo servido")
    r = c.get(f"/api/eos/video/{clave}.mp4", headers={"Range": "bytes=0-9"})
    ok(r.status_code == 206 and r.content == MP4[:10], "vídeo con Range: 206")
    ok(c.get("/api/eos/video/..%2Fx.mp4").status_code == 404, "ruta rara: 404")
    r = c.post(f"/api/eos/fallo/{clave}", json={"motivo": "x"}, headers=t)
    ok(r.status_code == 404, "fallo de un trabajo ya entregado: 404")


if __name__ == "__main__":
    modulo()
    rutas()
    print("TODO OK" if not FALLOS else f"{FALLOS} FALLOS")
    sys.exit(1 if FALLOS else 0)
