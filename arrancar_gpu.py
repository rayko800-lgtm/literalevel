"""Arranca LiteraLevel con la GPU, sin tocar el entorno de Python normal.

Por que existe este archivo y no un simple `pip install torch+cu126`: el disco
C: de esta maquina anda por debajo de 4 GB libres y la rueda de torch con CUDA
son 2,4 GB. Instalarla encima del entorno principal lo llenaria y, si algo
saliera mal, dejaria la app rota. Asi que el entorno con CUDA vive **aparte, en
D:**, y el principal se queda como esta: si la GPU da problemas, se arranca con
el de siempre y no hay nada que deshacer.

Lo que se gana esta medido sobre Crimen y Castigo, 840 ventanas, de punta a
punta (tokenizar, copiar a la tarjeta, inferir y traer de vuelta):

    CPU  (Ryzen 5 2600, 12 hilos, lote 64)     8,19 ventanas/s
    GPU  (GTX 1650 SUPER, fp32, lote 128)    112,7 ventanas/s      13,8x

Y da los MISMOS numeros, que es lo que de verdad importa: 839 de 840 ventanas
identicas a tres decimales, MAE 0,0000012, y `validar_local.py` devuelve las
medias exactas de siempre (A1 0.5040 · A2 0.5480 · B1 0.9276 · B2 1.2414 ·
C1 1.4952, orden estrictamente creciente).

Uso:
    python -X utf8 arrancar_gpu.py            # local, en el navegador
    python -X utf8 arrancar_gpu.py --compartir  # enlace publico con clave

Si el entorno de D: no esta, lo dice y explica como rehacerlo en vez de fallar
con un traceback de importacion.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PYTHON_CUDA = Path(r"D:\ll_bench\venv_cuda\Scripts\python.exe")

RECETA = f"""
No encuentro el Python con CUDA en:
    {PYTHON_CUDA}

Para rehacerlo (unos 6 GB en D:, ni un byte en C:):

    py -3.11 -m venv D:\\ll_bench\\venv_cuda
    set TMP=D:\\ll_bench\\tmp
    set PIP_CACHE_DIR=D:\\ll_bench\\pipcache
    D:\\ll_bench\\venv_cuda\\Scripts\\python -m pip install ^
        torch --index-url https://download.pytorch.org/whl/cu126
    D:\\ll_bench\\venv_cuda\\Scripts\\python -m pip install ^
        gradio plotly pandas pypdf sentence-transformers spacy openai transformers
    D:\\ll_bench\\venv_cuda\\Scripts\\python -m pip install ^
        https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

Mientras tanto, la app arranca igual con el Python de siempre; solo va mas
lenta:  python -X utf8 main.py
"""


def main() -> int:
    if not PYTHON_CUDA.exists():
        print(RECETA)
        return 1

    guion = "compartir.py" if "--compartir" in sys.argv[1:] else "main.py"
    entorno = dict(os.environ)
    # Los temporales de torch tambien fuera de C:, que es el disco apretado.
    entorno.setdefault("TMP", r"D:\ll_bench\tmp")
    entorno.setdefault("TEMP", r"D:\ll_bench\tmp")

    print(f"Arrancando {guion} con {PYTHON_CUDA}")
    print("(si la tarjeta esta ocupada, LITERALEVEL_CPU=1 fuerza la CPU)\n")
    return subprocess.call([str(PYTHON_CUDA), "-X", "utf8", str(RAIZ / guion)]
                           + [a for a in sys.argv[1:] if a != "--compartir"],
                           cwd=str(RAIZ), env=entorno)


if __name__ == "__main__":
    sys.exit(main())
