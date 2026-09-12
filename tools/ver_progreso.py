"""Por donde va la medicion del catalogo, sin abrir Colab.

    python -X utf8 tools/ver_progreso.py

La tanda de Colab sube `progreso.json` al repositorio privado de resultados
tras cada shard de 500 libros. Esto lo lee y lo cuenta. Existe porque durante
dias la unica forma de saber como iba era abrir el cuaderno y pegar la salida
de una celda en el chat.

El token se lee de HF_TOKEN o de `~/.hf_token`. Nunca se imprime.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = "MikeMaki1763/literalevel-catalogo"


def _token() -> str:
    t = os.environ.get("HF_TOKEN", "").strip()
    if t:
        return t
    ruta = Path.home() / ".hf_token"
    return ruta.read_text(encoding="utf-8").strip() if ruta.exists() else ""


def main() -> int:
    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import EntryNotFoundError

    try:
        ruta = hf_hub_download(REPO, "progreso.json", repo_type="dataset",
                               token=_token() or None, force_download=True)
    except EntryNotFoundError:
        print("Todavia no hay progreso.json: la tanda no ha guardado su primer shard.")
        return 1
    e = json.loads(Path(ruta).read_text(encoding="utf-8"))

    medidos, objetivo = e.get("medidos") or 0, e.get("objetivo")
    print(f"Libros medidos: {medidos:,}".replace(",", "."), end="")
    if objetivo:
        print(f" de {objetivo:,}".replace(",", ".") + f"  ({100 * medidos / objetivo:.1f} %)")
    else:
        print()
    vpm = e.get("libros_por_minuto")
    if vpm:
        print(f"Velocidad de la sesion: {vpm} libros/min")
        if objetivo and objetivo > medidos:
            h = (objetivo - medidos) / vpm / 60
            print(f"Faltarian unas {h:.1f} h de GPU a este ritmo")
    cuando = e.get("cuando_utc")
    if cuando:
        t = datetime.strptime(cuando, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        minutos = (datetime.now(timezone.utc) - t).total_seconds() / 60
        print(f"Ultimo shard: {e.get('ultimo_shard')} hace {minutos:.0f} min")
        # Un shard son 500 libros; a ~84 libros/min eso son ~6 min. Mas de media
        # hora sin shard nuevo es que la sesion se ha cortado.
        if minutos > 30:
            print("OJO: mas de 30 min sin shard nuevo. Lo mas probable es que Colab "
                  "haya cortado la sesion: vuelve a ejecutar las celdas y sigue sola.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
