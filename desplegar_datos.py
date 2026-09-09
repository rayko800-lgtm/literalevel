"""Sube el modelo v4 y el diccionario Kaikki a Hugging Face, como repos aparte.

Son 571 MB que **no pueden ir en el repositorio del despliegue**: estan en
`.gitignore` a proposito, git guarda una copia entera de cada binario en cada
cambio y GitHub rechaza archivos de mas de 100 MB. La forma limpia es tenerlos
en un repo de modelo y un repo de datos, y montarlos de solo lectura.

Por defecto **no sube nada**: enseña lo que haria. Para subir de verdad hay que
pasar `--subir` explicitamente, porque publicar es dificil de deshacer.

    python -X utf8 desplegar_datos.py                    # simulacro
    python -X utf8 desplegar_datos.py --subir            # sube de verdad
    python -X utf8 desplegar_datos.py --subir --publico  # ademas, publicos

Necesita un token de Hugging Face con permiso de escritura, en `HF_TOKEN` o en
`huggingface-cli login`. El token **no se imprime nunca**.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MODELO = Path(os.environ.get("LITERALEVEL_MODELO", RAIZ / "modelo_v4"))
DICCIONARIO = Path(os.environ.get("LITERALEVEL_DICCIONARIO",
                                  RAIZ / "kaikki_diccionario.db"))

NOMBRE_MODELO = "literalevel-v4-transformer"
NOMBRE_DATOS = "literalevel-kaikki"


def _mb(ruta: Path) -> float:
    if ruta.is_dir():
        return sum(f.stat().st_size for f in ruta.rglob("*") if f.is_file()) / 1e6
    return ruta.stat().st_size / 1e6


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subir", action="store_true",
                   help="sube de verdad; sin esto solo se simula")
    p.add_argument("--publico", action="store_true",
                   help="crea los repos publicos (por defecto, privados)")
    args = p.parse_args()

    faltan = [str(r) for r in (MODELO, DICCIONARIO) if not r.exists()]
    if faltan:
        print("No encuentro:", ", ".join(faltan))
        print("Ajusta LITERALEVEL_MODELO y LITERALEVEL_DICCIONARIO, o ejecuta")
        print("esto desde la raiz del repositorio.")
        return 1

    print(f"modelo v4     {_mb(MODELO):>7.0f} MB  {MODELO}")
    print(f"diccionario   {_mb(DICCIONARIO):>7.0f} MB  {DICCIONARIO}")

    from huggingface_hub import HfApi
    api = HfApi()
    try:
        usuario = api.whoami()["name"]
    except Exception as e:
        print(f"\nSin sesion en Hugging Face ({type(e).__name__}).")
        print("Pon HF_TOKEN en el entorno o ejecuta: huggingface-cli login")
        return 1

    repo_modelo = f"{usuario}/{NOMBRE_MODELO}"
    repo_datos = f"{usuario}/{NOMBRE_DATOS}"
    visibilidad = "publico" if args.publico else "privado"
    print(f"\nusuario: {usuario}")
    print(f"  modelo      -> {repo_modelo}   ({visibilidad})")
    print(f"  diccionario -> {repo_datos}   ({visibilidad}, tipo dataset)")

    if not args.subir:
        print("\nSIMULACRO: no se ha subido nada. Anade --subir para hacerlo.")
        return 0

    print("\nsubiendo el modelo...")
    api.create_repo(repo_modelo, repo_type="model", private=not args.publico,
                    exist_ok=True)
    api.upload_folder(repo_id=repo_modelo, folder_path=str(MODELO),
                      repo_type="model",
                      commit_message="LiteraLevel v4 (distilroberta en regresion 0..5)")

    print("subiendo el diccionario...")
    api.create_repo(repo_datos, repo_type="dataset", private=not args.publico,
                    exist_ok=True)
    api.upload_file(path_or_fileobj=str(DICCIONARIO),
                    path_in_repo=DICCIONARIO.name, repo_id=repo_datos,
                    repo_type="dataset",
                    commit_message="Volcado de Kaikki/Wiktionary, 1.48M entradas")

    print("\nHecho. En el Space, apunta las variables a donde queden montados:")
    print(f"  LITERALEVEL_MODELO       (desde {repo_modelo})")
    print(f"  LITERALEVEL_DICCIONARIO  (desde {repo_datos})")
    print("Ver DESPLIEGUE.md para el resto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
