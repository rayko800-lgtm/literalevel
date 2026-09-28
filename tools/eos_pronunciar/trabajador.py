"""El trabajador de Eos: en este PC, anima y graba las frases nuevas que pide la app.

    set LITERALEVEL_EOS_TOKEN=...      (el mismo secreto que tiene el Space)
    python -m http.server 8790 --bind 127.0.0.1     (desde D:/literalevel_eos_pronunciar/visor)
    python -X utf8 tools/eos_pronunciar/trabajador.py --api https://mikemaki1763-literalevel.hf.space
    python -X utf8 tools/eos_pronunciar/trabajador.py --api http://127.0.0.1:7860 --una-vez

Cada `--cada` segundos pregunta `GET /api/eos/cola`; por cada trabajo baja el mp3
(`audio_correcto` de una corrección: la frase leída con tts-1), genera las curvas
de Eos con `generar.py` (whisper pone las palabras; boca Audio2Face; gestos v3),
la graba desde el visor aislado (como `grabar_clips.py`) y sube el mp4 con
`POST /api/eos/entregar/<clave>`. Si algo falla, `POST /api/eos/fallo/<clave>`
para que el lector no se quede esperando. Contrato en `app/eos.py`.

El token va en la cabecera `X-Eos-Token` y NUNCA se imprime.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from grabar_clips import CLIPS, grabar  # noqa: E402

GENERADOR = RAIZ / ".claude" / "worktrees" / "cara-parlante" / "tools" / "cara_parlante" / "eos_demo" / "generar.py"
NOVERBAL = Path("D:/literalevel_cara/v3_solo_noverbal")
TOKEN_ENV = "LITERALEVEL_EOS_TOKEN"


def _peticion(api: str, ruta: str, token: str, datos: bytes | None = None, tipo: str | None = None):
    cab = {"X-Eos-Token": token}
    if tipo:
        cab["Content-Type"] = tipo
    p = urllib.request.Request(api + ruta, data=datos, headers=cab, method="POST" if datos is not None else "GET")
    with urllib.request.urlopen(p, timeout=120) as r:
        return json.loads(r.read())


def _bajar(url: str, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as r, open(destino, "wb") as f:
        f.write(r.read())


def hacer(trabajo: dict, api: str, token: str, pag, ff: str, url_visor: str, fps: int) -> Path:
    clave = trabajo["clave"]
    clip = f"frase_{clave}"
    carpeta = CLIPS / clip
    mp3 = carpeta / "original.mp3"
    _bajar(api + trabajo["audio_url"], mp3)
    orden = [sys.executable, "-X", "utf8", str(GENERADOR), "--audio", str(mp3), "--idioma", "en",
             "--salida", str(carpeta), "--boca", "a2f", "--gestos", "v3", "--modelo_v3", str(NOVERBAL),
             "--estilo_v3", "real", "--semilla", str(int(clave[:6], 16) % 1000)]
    subprocess.run(orden, check=True, cwd=str(GENERADOR.parent))
    salida = carpeta / "eos.mp4"
    grabar(pag, clip, fps, ff, url_visor, salida, "0,-0.035,0.62", 24)
    with open(salida, "rb") as f:
        contenido = f.read()
    _peticion(api, f"/api/eos/entregar/{clave}", token, contenido, "video/mp4")
    return salida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", required=True, help="raíz del motor, sin barra final")
    ap.add_argument("--visor", default="http://127.0.0.1:8790")
    ap.add_argument("--cada", type=float, default=10.0, help="segundos entre consultas a la cola")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--una-vez", action="store_true", help="vacía la cola una vez y termina")
    a = ap.parse_args()
    token = os.environ.get(TOKEN_ENV, "").strip()
    if not token:
        raise SystemExit(f"Falta {TOKEN_ENV} en el entorno.")
    if not (NOVERBAL / "noverbal").is_dir():
        raise SystemExit(f"Falta {NOVERBAL}/noverbal")
    import imageio_ffmpeg
    from playwright.sync_api import sync_playwright
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    api = a.api.rstrip("/")
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True,
                                args=["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"])
        pag = nav.new_page(viewport={"width": 640, "height": 640})
        while True:
            try:
                trabajos = _peticion(api, "/api/eos/cola", token).get("trabajos", [])
            except Exception as e:  # noqa: BLE001
                print(f"cola: {type(e).__name__}: {e}", flush=True)
                trabajos = []
            for t in trabajos:
                t0 = time.time()
                try:
                    salida = hacer(t, api, token, pag, ff, a.visor, a.fps)
                    print(f"{t['clave']}: listo, {salida.stat().st_size // 1024} KB, {time.time() - t0:.0f} s", flush=True)
                except Exception as e:  # noqa: BLE001
                    traceback.print_exc()
                    try:
                        _peticion(api, f"/api/eos/fallo/{t['clave']}", token,
                                  json.dumps({"motivo": f"{type(e).__name__}: {e}"[:300]}).encode(), "application/json")
                    except Exception as e2:  # noqa: BLE001
                        print(f"no se pudo avisar del fallo: {type(e2).__name__}", flush=True)
            if a.una_vez:
                break
            time.sleep(a.cada)
        nav.close()


if __name__ == "__main__":
    main()
