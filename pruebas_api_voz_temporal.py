"""Prueba focal sin importar el motor pesado ni cargar claves.

Requiere Starlette, httpx y python-multipart. Extrae por AST las funciones
reales de api.py y su prueba; las ejecuta con HTTP multipart y dobles de las
dependencias de pago. No sustituye pruebas_api.py sobre FastAPI completo.

    python -B -X utf8 pruebas_api_voz_temporal.py
    python -B -X utf8 pruebas_api_voz_temporal.py --comparar f1cfb5d

--comparar comprueba que el manejador anterior cae con la misma prueba.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import tempfile
import types
import uuid
from pathlib import Path

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartParser
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

RAIZ = Path(__file__).resolve().parent


def _extraer(texto: str, nombres: set[str], espacio: dict) -> None:
    arbol = ast.parse(texto)
    nodos = [n for n in arbol.body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in nombres]
    if {n.name for n in nodos} != nombres:
        raise AssertionError("Han cambiado los nombres de las funciones de la prueba.")
    for nodo in nodos:
        nodo.decorator_list = []
    modulo = ast.fix_missing_locations(ast.Module(body=nodos, type_ignores=[]))
    exec(compile(modulo, "<funciones-reales-extraidas>", "exec"), espacio)


def comprobar(comparar: str | None = None) -> None:
    os.environ["LITERALEVEL_SIN_CLAVES"] = "1"
    os.environ.pop("OPENAI_API_KEY", None)
    api = types.ModuleType("api_aislada")
    ui = types.SimpleNamespace(
        LIMITE_FRASE_VOZ=300, LIMITE_VOZ_HORA=30,
        # Dos argumentos y `_codigo_de`: desde el reinicio 27 `_corregir_voz` lee el
        # codigo una sola vez y se lo pasa al cobro. Sin esto la prueba caia con
        # AttributeError y el manejador lo tapaba como «Error generico.»: llevaba
        # rota desde el 27 y nadie lo dijo (f4, 16 sep 2026).
        _codigo_de=lambda pet: None,
        _puede_pagar=lambda pet, codigo=None: (False, "No autorizado."),
        _dentro_del_limite=lambda *a: True)

    def sin_proveedor(*a, **k):
        raise AssertionError("La prueba no permite llamar al proveedor.")

    api.__dict__.update(
        os=os, re=re, tempfile=tempfile, Request=Request, Lector=object,
        HTTPException=HTTPException, MultiPartParser=MultiPartParser, ui=ui,
        run_in_threadpool=run_in_threadpool, _Lector=object,
        config=types.SimpleNamespace(falta=lambda: ["sin clave"]),
        voz=types.SimpleNamespace(practicar=sin_proveedor),
        _va_a_costar=lambda pet: False)
    fuente = (RAIZ / "app/api.py").read_text(encoding="utf-8")
    constantes = {"_TOPE_AUDIO", "_HOLGURA_FORMULARIO", "_EXT_AUDIO"}
    for nodo in ast.parse(fuente).body:
        if (isinstance(nodo, ast.Assign) and len(nodo.targets) == 1
                and isinstance(nodo.targets[0], ast.Name)
                and nodo.targets[0].id in constantes):
            exec(compile(ast.Module(body=[nodo], type_ignores=[]), "<constante-real>", "exec"),
                 api.__dict__)
    if not constantes <= api.__dict__.keys():
        raise AssertionError("Han cambiado las constantes de la API.")
    _extraer(fuente, {"_llano", "_no", "_formulario", "practicar", "_corregir_voz"}, api.__dict__)

    async def endpoint(request):
        pet = types.SimpleNamespace(session_hash=request.headers.get("x-lector"))
        return JSONResponse(await api.practicar(pet, request))

    async def error(request, exc):
        return JSONResponse({"detail": "Error generico."}, status_code=500)

    app = Starlette(routes=[Route("/api/voz", endpoint, methods=["POST"])],
                    exception_handlers={Exception: error})
    with TestClient(app, raise_server_exceptions=False) as cliente:
        espacio = dict(api=api, ui=ui, os=os, tempfile=tempfile, Path=Path, cliente=cliente,
                       nuevo_lector=lambda: {"X-Lector": str(uuid.uuid4())})
        _extraer((RAIZ / "pruebas_api.py").read_text(encoding="utf-8"),
                 {"voz_prepara_temporal_antes_de_cobrar"}, espacio)
        prueba = espacio["voz_prepara_temporal_antes_de_cobrar"]
        print("ACTUAL:", prueba())
        if comparar:
            original = subprocess.run(
                ["git", "show", f"{comparar}:app/api.py"], cwd=RAIZ,
                check=True, capture_output=True, encoding="utf-8").stdout
            _extraer(original, {"practicar"}, api.__dict__)
            try:
                prueba()
            except AssertionError:
                print(f"REGRESION {comparar}: detectada por la prueba")
            else:
                raise AssertionError("La prueba no detecta el manejador anterior.")
    print("Sin importar app/ui, voz ni config; sin proveedor ni modelo.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparar", help="Commit anterior cuyo manejador debe fallar")
    comprobar(parser.parse_args().comparar)
