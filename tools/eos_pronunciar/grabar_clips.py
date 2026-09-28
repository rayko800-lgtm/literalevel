"""Graba en vídeo a Eos diciendo cada sonido, desde el visor aislado, y los deja en el front.

    python -m http.server 8790 --bind 127.0.0.1   (desde D:/literalevel_eos_pronunciar/visor)
    python -X utf8 tools/eos_pronunciar/grabar_clips.py                  # los clips que falten
    python -X utf8 tools/eos_pronunciar/grabar_clips.py --solo ga_0283   # uno
    python -X utf8 tools/eos_pronunciar/grabar_clips.py --lado 720 --fps 30

Un solo Chrome (Playwright, el Chrome instalado, con GPU) para todos los clips:
por cada uno carga `index.html?grabar=clips/<clip>&plano=cara`, esconde el
subtítulo y los botones, pinta fotograma a fotograma (`window.pintar(t)`, como
`grabar.py` de la sesión de la cara) y ffmpeg lo une con el mp3 original.

Salida: `front/public/eos/<acento>/<archivo>.mp4` (H.264 main, yuv420p, faststart,
AAC 64 kb/s: lo que reproduce cualquier móvil sin descargar entero), la imagen
de reposo `front/public/eos/reposo.webp` (primer fotograma del primer clip) y el
índice `front/public/eos/clips.json` con la duración de cada uno.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TRABAJO = Path(os.environ.get("LITERALEVEL_EOS_TRABAJO", "D:/literalevel_eos_pronunciar"))
CLIPS = TRABAJO / "visor" / "clips"
SALIDA = RAIZ / "front" / "public" / "eos"
SIN_UI = "#ui, #titulo, #estado { display: none !important; }"


def grabar(pag, clip: str, fps: int, ff: str, url: str, destino: Path, camara: str, crf: int) -> float:
    # `camara=dx,dy,dz` respecto a los ojos (index.html): más cerca que el plano de presentadora,
    # para que la boca se vea grande en un móvil.
    pag.goto(f"{url}/index.html?grabar=clips/{clip}&camara={camara}")
    pag.add_style_tag(content=SIN_UI)
    pag.wait_for_function("window.listo === true", timeout=300000)
    dur = float(pag.evaluate("window.duracion"))
    n = int(dur * fps)
    tmp = Path(tempfile.mkdtemp(prefix="eos_"))
    try:
        for i in range(n):
            pag.evaluate(f"window.pintar({i / fps})")
            pag.screenshot(path=str(tmp / f"{i:05d}.png"))
        destino.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(tmp / "%05d.png"),
                        "-i", str(CLIPS / clip / "voz.mp3"), "-c:v", "libx264", "-profile:v", "main",
                        "-pix_fmt", "yuv420p", "-crf", str(crf), "-movflags", "+faststart", "-c:a", "aac",
                        "-b:a", "64k", "-shortest", str(destino)], check=True)
        reposo = SALIDA / "reposo.webp"
        if not reposo.exists():
            subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(tmp / "00000.png"), "-quality", "82",
                            str(reposo)], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", default="")
    ap.add_argument("--url", default="http://127.0.0.1:8790")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--lado", type=int, default=640)
    ap.add_argument("--rehacer", action="store_true")
    ap.add_argument("--camara", default="0,-0.035,0.62")
    ap.add_argument("--crf", type=int, default=24)
    a = ap.parse_args()
    import imageio_ffmpeg
    from playwright.sync_api import sync_playwright
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    clips = sorted(p.name for p in CLIPS.iterdir() if (p / "curvas.json").exists())
    if a.solo:
        clips = [c for c in clips if c == a.solo]
    indice_ruta = SALIDA / "clips.json"
    indice = json.load(open(indice_ruta, encoding="utf-8")) if indice_ruta.exists() else {}
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True,
                                args=["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"])
        pag = nav.new_page(viewport={"width": a.lado, "height": a.lado})
        for clip in clips:
            acento, archivo = clip.split("_", 1)
            destino = SALIDA / acento / f"{archivo}.mp4"
            if destino.exists() and not a.rehacer and f"{acento}/{archivo}" in indice:
                continue
            t0 = time.time()
            dur = grabar(pag, clip, a.fps, ff, a.url, destino, a.camara, a.crf)
            indice[f"{acento}/{archivo}"] = {"dur": round(dur, 2), "bytes": destino.stat().st_size}
            json.dump(dict(sorted(indice.items())), open(indice_ruta, "w", encoding="utf-8"), indent=1)
            print(f"{clip}: {dur:.1f} s, {destino.stat().st_size // 1024} KB, {time.time() - t0:.0f} s", flush=True)
        nav.close()
    print(f"{len(indice)} clips en {indice_ruta}")


if __name__ == "__main__":
    main()
