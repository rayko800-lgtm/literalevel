"""Publica el build de Angular en Vercel (proyecto `pleyade`), el mismo que va al Space.

    python tools/desplegar_vercel.py --seco   # build y carpeta preparada, sin subir
    python tools/desplegar_vercel.py          # sube y lo pone en produccion

Miguel, 26 sep: el profesor pidió Vercel. El motor (API y modelo) sigue en el
Space de Hugging Face; aquí solo va el front estático.

Reutiliza las comprobaciones de `desplegar_front.py`: build desde el árbol
confirmado, lista blanca de archivos, binarios iguales a `front/public`,
revisión de credenciales en los textos y la meta `literalevel-api` apuntando al
Space. Lo que se sube es una carpeta preparada con esos bytes, nunca `front/`
ni el repositorio: la CLI de Vercel sube lo que haya en la carpeta.

Añade un `vercel.json` con las cabeceras de caché que el Space no manda: el
`index.html` sin caché (26 sep: el móvil de Miguel se quedó con el index viejo)
y los chunks con hash, inmutables.

La sesión de la CLI (`npx vercel login`) la guarda la propia CLI; el token no
pasa por aquí ni se imprime.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from . import desplegar_front as front
except ImportError:
    import desplegar_front as front

PROYECTO = "pleyade"
EQUIPO = "mike-d120"
DOMINIO = "https://pleyade.vercel.app"

CABECERAS = {
    "headers": [
        {"source": "/", "headers": [{"key": "Cache-Control", "value": "no-cache"}]},
        {"source": "/index.html", "headers": [{"key": "Cache-Control", "value": "no-cache"}]},
        {"source": "/manifest.webmanifest", "headers": [{"key": "Cache-Control", "value": "no-cache"}]},
        {"source": "/(.*)-([A-Za-z0-9_]{8})\\.(js|css)",
         "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
    ],
}


def preparar(contenidos, destino: Path) -> None:
    for rel, contenido in contenidos.items():
        ruta = destino / rel
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(contenido)
    (destino / "vercel.json").write_text(json.dumps(CABECERAS, indent=2), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="build y carpeta preparada; no sube")
    args = ap.parse_args(argv)
    raiz = front.RAIZ.resolve()
    arbol = front.arbol_front(raiz)
    front.construir(raiz)
    contenidos = front.congelar(raiz)
    front.exigir_mismo_arbol(raiz, arbol)
    destino = Path(tempfile.mkdtemp(prefix="pleyade_vercel_"))
    try:
        preparar(contenidos, destino)
        print(f"Build confirmado, {len(contenidos)} archivos (+ vercel.json):")
        for rel, contenido in contenidos.items():
            print(hashlib.sha256(contenido).hexdigest()[:16], len(contenido), rel)
        if args.seco:
            print("--seco: no subo nada. Carpeta preparada en " + str(destino))
            return
        npx = "npx.cmd" if os.name == "nt" else "npx"
        p = subprocess.run([npx, "--yes", "vercel", "deploy", str(destino), "--prod", "--yes",
                            "--scope", EQUIPO, "--project", PROYECTO],
                           capture_output=True, text=True, check=False)
        salida = (p.stdout or "") + (p.stderr or "")
        print("\n".join(l for l in salida.splitlines() if "vercel.app" in l or "Error" in l or "rror:" in l))
        if p.returncode:
            front.abortar("la CLI de Vercel fallo (codigo " + str(p.returncode) + ").")
        print("Publicado en " + DOMINIO)
    finally:
        if not args.seco:
            shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    main()
