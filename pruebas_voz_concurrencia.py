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
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


RAIZ = Path(__file__).resolve().parent


def funciones_reales(carpeta):
    nombres = {"_ahora", "_texto_para_tts", "_ruta_audio_cache", "_escribir_audio_atomico",
               "_candado_audio", "generar_audio_correcto", "_conectar", "registrar_fallos",
               "palabras_para_practicar", "puntos_debiles", "_cuenta_como_dificil"}
    constantes = {"MODELO_VOZ", "VOZ_POR_DEFECTO", "VERSION_AUDIO_TTS", "_CANDADOS_AUDIO",
                  "_CANDADO_TABLA_AUDIO", "_PALABRAS_FUNCIONALES", "_PARAMETROS_FILTRO",
                  "_FILTRO_DIFICILES"}
    clases = {"HistorialIlegible"}
    arbol = ast.parse((RAIZ / "app" / "voz.py").read_text(encoding="utf-8"))
    nodos = [n for n in arbol.body if (
        isinstance(n, ast.FunctionDef) and n.name in nombres) or (
        isinstance(n, ast.ClassDef) and n.name in clases) or (
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constantes for t in n.targets))]
    espacio = dict(hashlib=hashlib, os=os, re=re, sqlite3=sqlite3, tempfile=tempfile,
                   threading=threading, nullcontext=nullcontext, contextmanager=contextmanager,
                   datetime=datetime, timezone=timezone, Path=Path,
                   RUTA_DB_POR_DEFECTO=str(Path(carpeta) / "voz.db"),
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
            liberar, llamadas = threading.Event(), []

            def crear(**kwargs):
                llamadas.append(kwargs)
                if not liberar.wait(5):
                    raise TimeoutError("la prueba no libero el proveedor simulado")
                return self.respuesta()

            self.cliente(crear)
            with ThreadPoolExecutor(max_workers=8) as pool:
                futuros = [pool.submit(self.v["generar_audio_correcto"], texto) for _ in range(8)]
                try:
                    # Los ocho se apuntan al candado de la MISMA clave y el primero ya
                    # esta llamando al proveedor antes de que nadie termine.
                    fin = time.monotonic() + 5
                    while time.monotonic() < fin:
                        entrada = self.v["_CANDADOS_AUDIO"].get(str(ruta))
                        if entrada is not None and entrada[1] == 8 and len(llamadas) == 1:
                            break
                        time.sleep(0.01)
                    else:
                        self.fail("no llegaron los ocho lectores al candado de la clave")
                    self.assertEqual(len(llamadas), 1)
                finally:
                    liberar.set()
                rutas = [f.result(timeout=5) for f in futuros]
            self.assertEqual(rutas, [str(ruta)] * 8)
            self.assertEqual(len(llamadas), 1)
            self.assertEqual(ruta.read_bytes(), b"audio simulado")
        self.assertEqual(self.v["_CANDADOS_AUDIO"], {}, "quedan candados de claves que ya nadie usa")

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
        self.assertEqual(self.v["_CANDADOS_AUDIO"], {})

    def test_claves_distintas_pueden_generar_en_paralelo(self):
        barrera = threading.Barrier(2, timeout=3)

        def crear(**kwargs):
            barrera.wait()
            return self.respuesta()

        self.cliente(crear)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futuros = [pool.submit(self.v["generar_audio_correcto"], t) for t in ("one", "other")]
            self.assertTrue(all(f.result(timeout=5) for f in futuros))

    def test_claves_de_la_misma_franja_antigua_no_se_esperan(self):
        """Con las 64 franjas de 71e4b52, dos audios distintos cuya ruta caia en
        la misma franja se esperaban durante la llamada de red. Con la clave
        exacta, no: los dos llegan al proveedor a la vez."""
        def franja(texto):
            ruta = self.v["_ruta_audio_cache"](texto, self.v["VOZ_POR_DEFECTO"])
            return int(hashlib.sha256(str(ruta).encode()).hexdigest()[:8], 16) % 64

        primero = "one"
        segundo = next(f"other {i}" for i in range(5000) if franja(f"other {i}") == franja(primero))
        barrera = threading.Barrier(2, timeout=3)

        def crear(**kwargs):
            barrera.wait()
            return self.respuesta()

        self.cliente(crear)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futuros = [pool.submit(self.v["generar_audio_correcto"], t) for t in (primero, segundo)]
            self.assertTrue(all(f.result(timeout=5) for f in futuros),
                            "dos audios de la misma franja antigua se esperaron")

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

    def test_leer_no_espera_al_que_escribe(self):
        """`BEGIN IMMEDIATE` en cada conexion hacia que una lectura esperase a
        cualquier escritura y, pasados 5 s, devolviera vacio. Con el esquema al
        dia, leer ya no abre transaccion."""
        ruta = str(Path(self.temporal.name) / "lectura.db")
        self.v["registrar_fallos"](["fox"], ruta, "The fox jumps.")
        escritor = sqlite3.connect(ruta)
        escritor.execute("BEGIN IMMEDIATE")          # otro hilo o proceso a mitad de escribir
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                filas = pool.submit(self.v["palabras_para_practicar"], 5, ruta).result(timeout=3)
        finally:
            escritor.rollback()
            escritor.close()
        self.assertEqual([f["palabra"] for f in filas], ["fox"])

    def test_historial_ilegible_avisa_y_sin_historial_es_vacio(self):
        """Una base que no se puede leer no es «no has fallado nada»."""
        no_existe = str(Path(self.temporal.name) / "no" / "existe.db")
        self.assertEqual(self.v["palabras_para_practicar"](5, no_existe), [])
        self.assertEqual(self.v["puntos_debiles"](5, no_existe), [])
        self.assertFalse(Path(no_existe).parent.exists(), "leer sin historial no debe crear carpetas")
        rota = Path(self.temporal.name) / "rota.db"
        rota.write_bytes(b"esto no es una base de datos sqlite " * 50)
        for funcion in ("palabras_para_practicar", "puntos_debiles"):
            with self.assertRaises(self.v["HistorialIlegible"]):
                self.v[funcion](5, str(rota))


if __name__ == "__main__":
    unittest.main(verbosity=2)
