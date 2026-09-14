"""Regresiones de voz con funciones reales, SQLite temporal y proveedor simulado.

No importa voz/config, no lee secretos, no usa datos reales ni permite red.
Uso: python -X utf8 pruebas_voz_concurrencia.py
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


RAIZ = Path(__file__).resolve().parent


def funciones_reales(carpeta):
    nombres = {"_ahora", "_texto_para_tts", "_ruta_audio_cache", "_escribir_audio_atomico",
               "generar_audio_correcto", "_conectar", "registrar_fallos", "palabras_para_practicar"}
    constantes = {"MODELO_VOZ", "VOZ_POR_DEFECTO", "VERSION_AUDIO_TTS", "_CANDADOS_AUDIO"}
    arbol = ast.parse((RAIZ / "app" / "voz.py").read_text(encoding="utf-8"))
    nodos = [n for n in arbol.body if (
        isinstance(n, ast.FunctionDef) and n.name in nombres) or (
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constantes for t in n.targets))]
    espacio = dict(hashlib=hashlib, os=os, re=re, sqlite3=sqlite3, tempfile=tempfile,
                   threading=threading, nullcontext=nullcontext, datetime=datetime,
                   timezone=timezone, Path=Path, RUTA_DB_POR_DEFECTO=str(Path(carpeta) / "voz.db"),
                   RUTA_AUDIO_GENERADO=Path(carpeta) / "audio")
    exec(compile(ast.Module(body=nodos, type_ignores=[]), "voz[funciones_reales]", "exec"), espacio)
    return espacio


class VozConcurrencia(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="literalevel_voz_prueba_")
        self.addCleanup(self.temporal.cleanup)
        self.v = funciones_reales(self.temporal.name)

    @staticmethod
    def respuesta(contenido=b"audio simulado"):
        return SimpleNamespace(write_to_file=lambda ruta: Path(ruta).write_bytes(contenido))

    def cliente(self, crear):
        self.v["_cliente"] = lambda: SimpleNamespace(audio=SimpleNamespace(speech=SimpleNamespace(create=crear)))

    def test_ocho_lectores_una_peticion_repetido(self):
        for repeticion in range(5):
            texto = f"word {repeticion}"
            ruta = self.v["_ruta_audio_cache"](texto, self.v["VOZ_POR_DEFECTO"])
            indice = int(hashlib.sha256(str(ruta).encode()).hexdigest()[:8], 16) % 64
            todos_esperan, liberar = threading.Event(), threading.Event()
            mutex, contador = threading.Lock(), []
            original = self.v["_CANDADOS_AUDIO"][indice]

            class Observado:
                def __enter__(self):
                    with mutex:
                        contador.append(1)
                        if len(contador) == 8:
                            todos_esperan.set()
                    original.acquire()

                def __exit__(self, *args):
                    original.release()

            self.v["_CANDADOS_AUDIO"][indice] = Observado()
            llamadas = []

            def crear(**kwargs):
                llamadas.append(kwargs)
                if not liberar.wait(5):
                    raise TimeoutError("la prueba no libero el proveedor simulado")
                return self.respuesta()

            self.cliente(crear)
            with ThreadPoolExecutor(max_workers=8) as pool:
                futuros = [pool.submit(self.v["generar_audio_correcto"], texto) for _ in range(8)]
                try:
                    self.assertTrue(todos_esperan.wait(5), "no llegaron los ocho lectores al candado")
                    self.assertEqual(len(llamadas), 1)
                finally:
                    liberar.set()
                rutas = [f.result(timeout=5) for f in futuros]
            self.assertEqual(rutas, [str(ruta)] * 8)
            self.assertEqual(len(llamadas), 1)
            self.assertEqual(ruta.read_bytes(), b"audio simulado")
            self.v["_CANDADOS_AUDIO"][indice] = original
        self.assertEqual(len(self.v["_CANDADOS_AUDIO"]), 64)

    def test_cache_sin_cliente_y_frase_sin_renormalizar(self):
        llamadas = []
        self.cliente(lambda **kw: (llamadas.append(kw), self.respuesta())[1])
        texto = "Don't change THIS sentence!"
        ruta = self.v["generar_audio_correcto"](texto)
        self.assertEqual(llamadas[0]["input"], texto)
        self.v["_cliente"] = lambda: self.fail("cache no debe construir cliente")
        self.assertEqual(self.v["generar_audio_correcto"](texto), ruta)

    def test_error_y_audio_vacio_liberan_candado(self):
        for error in ("red", "vacio"):
            def fallar(**kwargs):
                if error == "red":
                    raise TimeoutError("simulado")
                return self.respuesta(b"")
            self.cliente(fallar)
            self.assertIsNone(self.v["generar_audio_correcto"](error))
            self.cliente(lambda **kwargs: self.respuesta())
            with ThreadPoolExecutor(max_workers=1) as pool:
                self.assertIsNotNone(pool.submit(self.v["generar_audio_correcto"], error).result(timeout=3))
        self.assertEqual(list(self.v["RUTA_AUDIO_GENERADO"].glob("*.tmp")), [])

    def test_claves_distintas_pueden_generar_en_paralelo(self):
        def indice(texto):
            ruta = self.v["_ruta_audio_cache"](texto, self.v["VOZ_POR_DEFECTO"])
            return int(hashlib.sha256(str(ruta).encode()).hexdigest()[:8], 16) % 64
        primero = "one"
        segundo = next(f"other {i}" for i in range(100) if indice(f"other {i}") != indice(primero))
        barrera = threading.Barrier(2, timeout=3)
        def crear(**kwargs):
            barrera.wait()
            return self.respuesta()
        self.cliente(crear)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futuros = [pool.submit(self.v["generar_audio_correcto"], t) for t in (primero, segundo)]
            self.assertTrue(all(f.result(timeout=5) for f in futuros))

    def test_ruta_explicita_conserva_comportamiento(self):
        ruta = Path(self.temporal.name) / "explicito.mp3"
        ruta.write_bytes(b"previo")
        llamadas = []
        self.cliente(lambda **kw: (llamadas.append(kw), self.respuesta())[1])
        self.assertEqual(self.v["generar_audio_correcto"]("hello", ruta), str(ruta))
        self.assertEqual(len(llamadas), 1)
        self.assertEqual(ruta.read_bytes(), b"audio simulado")

    def test_migracion_concurrente_conserva_filas_y_todos_los_fallos(self):
        for repeticion in range(5):
            ruta = str(Path(self.temporal.name) / f"antigua_{repeticion}.db")
            with sqlite3.connect(ruta) as con:
                con.execute("CREATE TABLE palabras_debiles (palabra TEXT PRIMARY KEY, fallos INTEGER NOT NULL DEFAULT 0, ultima_vez TEXT NOT NULL)")
                con.execute("INSERT INTO palabras_debiles VALUES ('old', 7, 'ayer')")
            con.close()
            barrera = threading.Barrier(12, timeout=5)
            def registrar(i):
                barrera.wait()
                self.v["registrar_fallos"](["same", f"new{i}"], ruta, f"frase {i}")
            with ThreadPoolExecutor(max_workers=12) as pool:
                list(pool.map(registrar, range(12)))
            with sqlite3.connect(ruta) as con:
                filas = {p: (n, f) for p, n, f in con.execute("SELECT palabra, fallos, frase FROM palabras_debiles")}
                self.assertEqual(filas["old"], (7, None))
                self.assertEqual(filas["same"][0], 12)
                self.assertEqual(len(filas), 14)
                for i in range(12):
                    self.assertEqual(filas[f"new{i}"], (1, f"frase {i}"))
            con.close()
            conexion = self.v["_conectar"](ruta)
            self.assertFalse(conexion.in_transaction)
            conexion.close()

    def test_migracion_cierra_conexion_y_revierte_al_fallar(self):
        for etapa in ("pragma", "commit"):
            ruta = str(Path(self.temporal.name) / f"fallo_{etapa}.db")
            real = sqlite3.connect(ruta)
            class Conexion:
                def execute(self, consulta):
                    if etapa == "pragma" and consulta.startswith("PRAGMA"):
                        raise RuntimeError("migracion simulada fallida")
                    return real.execute(consulta)
                def commit(self):
                    raise RuntimeError("commit simulado fallido")
                def close(self):
                    real.close()
            self.v["sqlite3"] = SimpleNamespace(connect=lambda ruta: Conexion())
            with self.assertRaises(RuntimeError):
                self.v["_conectar"](ruta)
            with self.assertRaises(sqlite3.ProgrammingError):
                real.execute("SELECT 1")
            with sqlite3.connect(ruta) as nueva:
                self.assertEqual(nueva.execute("SELECT name FROM sqlite_master WHERE name='palabras_debiles'").fetchall(), [])
            nueva.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
