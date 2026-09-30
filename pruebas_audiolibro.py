"""Lectura con audio: pruebas sin red, sin credenciales y con datos temporales."""
import concurrent.futures
import json
import os
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, "app")
import pruebas_tmp
os.environ["LITERALEVEL_DATOS"] = pruebas_tmp.carpeta("literalevel_audiolibro_")
os.environ["SPACE_ID"] = "pruebas/audiolibro"
os.environ["LITERALEVEL_SIN_CLAVES"] = "1"
os.environ["LITERALEVEL_PRECARGA"] = "0"
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("LITERALEVEL_CUENTAS", None)

import api
import audiolibro
from fastapi.testclient import TestClient


class AudioLibro(unittest.TestCase):
    def setUp(self):
        self.cliente = TestClient(api.app)
        self.cab = {"X-Lector": str(uuid.uuid4())}
        self.base = api.ui.BASE_DATOS_LECTOR / "lectores" / self.cab["X-Lector"]
        self.ruta = "/api/libros/SWV369/capitulos/0/escuchar"

    def test_fragmentos_sin_perder_texto_y_con_tope(self):
        texto = ("Hello world! This is a sentence.\n\n" * 400).strip()
        partes = audiolibro.fragmentos(texto)
        self.assertGreater(len(partes), 1)
        self.assertTrue(all(0 < len(p) <= 2400 for p in partes))
        self.assertEqual(" ".join(" ".join(partes).split()), " ".join(texto.split()))
        self.assertEqual(audiolibro.fragmentos("  "), [])
        self.assertTrue(all(len(p) <= 2400 for p in audiolibro.fragmentos("a" * 5000)))

    def test_marcas_texto_original_y_contracciones(self):
        texto = "I can't go.\nHello!"
        datos = {"duracion": 4, "palabras": [
            {"palabra": "I", "inicio": 0, "fin": .3},
            {"palabra": "can't", "inicio": .4, "fin": 1},
            {"palabra": "go", "inicio": 1.2, "fin": 2},
            {"palabra": "Hello", "inicio": 2.3, "fin": 3.9}]}
        marcas, aprox = audiolibro.marcas(texto, datos)
        self.assertEqual("".join(p["texto"] for p in marcas), texto)
        self.assertFalse(aprox)
        self.assertAlmostEqual(marcas[1]["inicio"], .4)

    def test_huecos_interpolados_y_sin_tiempos(self):
        marcas, aprox = audiolibro.marcas("One missing three", {"duracion": 3, "palabras": [
            {"palabra": "One", "inicio": 0, "fin": 1},
            {"palabra": "three", "inicio": 2, "fin": 3}]})
        self.assertTrue(aprox)
        self.assertEqual(marcas[1]["inicio"], 1)
        self.assertEqual(marcas[1]["fin"], 2)
        self.assertEqual(audiolibro.marcas("Hello", None), ([], True))

    def test_get_gratis_y_fuera_de_rango(self):
        with patch.object(api.cuentas, "consumir") as cobrar:
            r = self.cliente.get(self.ruta, headers=self.cab)
            self.assertEqual(r.status_code, 200, r.text)
            self.assertFalse(r.json()["guardado"])
            self.assertLessEqual(len(r.json()["texto"]), 2400)
            cobrar.assert_not_called()
        self.assertEqual(self.cliente.get(self.ruta + "?parte=-1", headers=self.cab).status_code, 422)
        self.assertEqual(self.cliente.get(self.ruta + "?parte=999", headers=self.cab).status_code, 404)
        self.assertEqual(self.cliente.get(self.ruta).status_code, 400)
        self.assertEqual(self.cliente.get(self.ruta.replace("/0/", "/-1/"), headers=self.cab).status_code, 404)

    def preparar(self, base, texto):
        destino = audiolibro.ruta(base, audiolibro.clave(texto))
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"ID3" + b"x" * 50)

    def test_nueva_generacion_y_repeticion_sin_cobro(self):
        with patch.object(api.config, "falta", return_value=[]), \
             patch.object(api.cuentas, "permite", return_value=(True, "")), \
             patch.object(api.cuentas, "consumir", return_value=(True, "")) as cobro, \
             patch.object(audiolibro, "generar", side_effect=self.preparar) as generar:
            r = self.cliente.post(self.ruta, headers=self.cab)
            self.assertEqual(r.status_code, 200, r.text)
            self.assertTrue(r.json()["guardado"])
            clave = r.json()["clave"]
            with patch.object(api.config, "falta", return_value=["OPENAI_API_KEY"]):
                self.assertEqual(self.cliente.post(self.ruta, headers=self.cab).status_code, 200)
            cobro.assert_called_once()
            generar.assert_called_once()
        audio = f"/api/audiolibro/{clave}.mp3"
        self.assertEqual(self.cliente.get(audio, headers=self.cab).status_code, 200)
        self.assertEqual(self.cliente.get(audio, headers={"X-Lector": str(uuid.uuid4())}).status_code, 404)
        self.assertEqual(self.cliente.get(audio).status_code, 400)
        self.assertEqual(self.cliente.get(audio, headers={**self.cab, "Range": "bytes=0-2"}).status_code, 206)

    def test_cuenta_sin_cupo_no_genera(self):
        with patch.object(api.config, "falta", return_value=[]), \
             patch.object(api.cuentas, "permite", return_value=(False, "Sin cupo")), \
             patch.object(audiolibro, "generar") as generar:
            self.assertEqual(self.cliente.post(self.ruta, headers=self.cab).status_code, 403)
            generar.assert_not_called()

    def test_tope_hora_y_carrera_cupo(self):
        with patch.object(api.config, "falta", return_value=[]), \
             patch.object(api.cuentas, "permite", return_value=(True, "")), \
             patch.object(api.ui, "_dentro_del_limite", return_value=False), \
             patch.object(api.cuentas, "consumir") as cobro:
            self.assertEqual(self.cliente.post(self.ruta, headers=self.cab).status_code, 429)
            cobro.assert_not_called()
        with patch.object(api.config, "falta", return_value=[]), \
             patch.object(api.cuentas, "permite", return_value=(True, "")), \
             patch.object(api.cuentas, "consumir", return_value=(False, "Sin cupo")), \
             patch.object(audiolibro, "generar") as generar:
            self.assertEqual(self.cliente.post(self.ruta, headers=self.cab).status_code, 403)
            generar.assert_not_called()

    def test_fallo_devuelve_cupo_a_la_cuenta_cobrada(self):
        with patch.object(api.config, "falta", return_value=[]), \
             patch.object(api.ui, "_codigo_de", return_value="cuenta-prueba"), \
             patch.object(api.cuentas, "permite", return_value=(True, "")), \
             patch.object(api.cuentas, "consumir", return_value=(True, "")), \
             patch.object(api, "_devolver") as devolver, \
             patch.object(audiolibro, "generar", side_effect=OSError):
            self.assertEqual(self.cliente.post(self.ruta, headers=self.cab).status_code, 502)
            devolver.assert_called_once_with("cuenta-prueba")

    def test_peticion_simultanea_genera_y_cobra_una_vez(self):
        def lento(base, texto):
            time.sleep(.05)
            self.preparar(base, texto)
        with patch.object(api.config, "falta", return_value=[]), \
             patch.object(api.cuentas, "permite", return_value=(True, "")), \
             patch.object(api.cuentas, "consumir", return_value=(True, "")) as cobro, \
             patch.object(audiolibro, "generar", side_effect=lento) as generar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as grupo:
                resultados = list(grupo.map(lambda _: self.cliente.post(self.ruta, headers=self.cab), range(4)))
            self.assertTrue(all(r.status_code == 200 for r in resultados))
            generar.assert_called_once()
            cobro.assert_called_once()

    def test_generador_persiste_audio_y_tiempos_una_vez(self):
        respuesta = Mock()
        respuesta.write_to_file.side_effect = lambda p: Path(p).write_bytes(b"ID3xxx")
        cliente = Mock()
        cliente.audio.speech.create.return_value = respuesta
        with patch.object(api.voz, "_cliente", return_value=cliente), \
             patch.object(api.voz, "transcribir_con_tiempos", return_value=None) as transcribir:
            audiolibro.generar(self.base, "Hello world.")
            ident = audiolibro.clave("Hello world.")
            self.assertTrue(audiolibro.guardado(self.base, ident))
            self.assertTrue(audiolibro.leer_marcas(self.base, ident)["aproximado"])
            transcribir.assert_called_once()
            cliente.audio.speech.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
