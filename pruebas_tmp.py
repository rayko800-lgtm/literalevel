"""Carpetas temporales de las suites, que se borran solas al salir.

Cada corrida dejaba sus carpetas en %TEMP%, 100 MB la de pruebas_extremas, y
los bancos de mutantes llenaron C: con 1.002 (Central, 15 sep 2026). Con
LITERALEVEL_TMP definida se crean ahi, por ejemplo en otro disco.
"""
from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import sys
import tempfile

# Lo que queda lo borra otro proceso cuando este ya ha salido, reintentando
# medio minuto: en Windows un SQLite que sigue abierto al salir (la cache lexica
# de `ui`, en pruebas_integracion) no se deja borrar mientras vive el proceso.
_BORRAR_LUEGO = (
    "import os, shutil, sys, time\n"
    "for _ in range(60):\n"
    "    time.sleep(0.5)\n"
    "    shutil.rmtree(sys.argv[1], ignore_errors=True)\n"
    "    if not os.path.exists(sys.argv[1]):\n"
    "        break\n"
)


def _borrar(ruta: str) -> None:
    shutil.rmtree(ruta, ignore_errors=True)
    if not os.path.exists(ruta):
        return
    try:
        subprocess.Popen([sys.executable, "-c", _BORRAR_LUEGO, ruta],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         close_fds=True, creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    except OSError:
        pass


def carpeta(prefijo: str = "literalevel_") -> str:
    """Una carpeta nueva, como `tempfile.mkdtemp` (la ruta en str), que se borra
    al terminar el proceso."""
    base = os.environ.get("LITERALEVEL_TMP") or None
    if base:
        os.makedirs(base, exist_ok=True)
    ruta = tempfile.mkdtemp(prefix=prefijo, dir=base)
    atexit.register(_borrar, ruta)
    return ruta
