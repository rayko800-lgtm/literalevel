"""Regresiones del audio TTS: expresion completa, cache y escritura atomica.

Ejecutar con:
    python -X utf8 pruebas_audio_atomico.py

No lee claves ni llama a OpenAI. Las respuestas binarias se simulan para
comprobar tambien el caso importante: una escritura que falla a la mitad no
puede reemplazar un mp3 bueno ni dejar un mp3 parcial reutilizable.
"""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "app")
import lexicon  # noqa: E402
import voz  # noqa: E402


class RespuestaAudio:
    def __init__(self, contenido: bytes = b"mp3 completo", fallar: bool = False):
        self.contenido = contenido
        self.fallar = fallar
        self.rutas: list[Path] = []

    def write_to_file(self, ruta) -> None:
        destino = Path(ruta)
        self.rutas.append(destino)
        destino.write_bytes(self.contenido)
        if self.fallar:
            raise OSError("corte simulado a media escritura")


class SpeechFalso:
    def __init__(self, respuesta: RespuestaAudio):
        self.respuesta = respuesta
        self.llamadas: list[dict] = []

    def create(self, **kwargs):
        self.llamadas.append(kwargs)
        return self.respuesta


class ClienteFalso:
    def __init__(self, respuesta: RespuestaAudio):
        self.audio = type("AudioFalso", (), {})()
        self.audio.speech = SpeechFalso(respuesta)


class AudioLexico(unittest.TestCase):
    def test_consultar_pronuncia_la_expresion_completa_y_cachea_v2(self):
        respuesta = RespuestaAudio()
        cliente = ClienteFalso(respuesta)
        entrada = lexicon.EntradaDiccionario(
            "pick", "verb", [], None, None, None, None)

        class DiccionarioFalso:
            def buscar(self, _palabra):
                return [entrada]

            def cerrar(self):
                pass

        with tempfile.TemporaryDirectory() as td:
            consultor = lexicon.ConsultorLexico.__new__(lexicon.ConsultorLexico)
            consultor.diccionario = DiccionarioFalso()
            consultor.cache = lexicon.CacheLexico(":memory:")
            consultor.modelo_openai = "modelo-prueba"
            consultor._sin_clave = False
            consultor._cliente_openai = cliente
            try:
                with patch.object(
                    lexicon, "_resolver_lema_y_categoria",
                    return_value=("pick", "pick", "verb", "VERB"),
                ), patch.object(
                    lexicon.ConsultorLexico, "_cliente", return_value=cliente,
                ), patch.object(
                    lexicon, "RUTA_AUDIO_GENERADO", Path(td),
                ):
                    primero = consultor.consultar(
                        "pick on", "They always pick on the smallest child.", 1.0)
                    segundo = consultor.consultar(
                        "pick on", "They always pick on the smallest child.", 1.0)
            finally:
                consultor.cerrar()

            self.assertEqual(cliente.audio.speech.llamadas[0]["input"], "pick on,")
            self.assertEqual(len(cliente.audio.speech.llamadas), 1)
            self.assertEqual(primero.audio_uk, segundo.audio_uk)
            self.assertEqual(Path(primero.audio_uk).read_bytes(), b"mp3 completo")
            self.assertTrue(all(r.suffix == ".tmp" for r in respuesta.rutas))
            self.assertFalse(list(Path(td).glob("*.tmp")))

    def test_fallo_a_media_escritura_no_publica_un_mp3_parcial(self):
        respuesta = RespuestaAudio(b"parcial", fallar=True)
        with tempfile.TemporaryDirectory() as td:
            destino = Path(td) / "existente.mp3"
            destino.write_bytes(b"audio anterior bueno")
            with self.assertRaises(OSError):
                lexicon._escribir_audio_atomico(respuesta, destino)
            self.assertEqual(destino.read_bytes(), b"audio anterior bueno")
            self.assertFalse(list(Path(td).glob("*.tmp")))


class AudioVoz(unittest.TestCase):
    def test_cache_anterior_se_invalida_y_la_nueva_sirve_sin_clave(self):
        texto = "fortress"
        respuesta = RespuestaAudio()
        cliente = ClienteFalso(respuesta)
        with tempfile.TemporaryDirectory() as td, patch.object(
            voz, "RUTA_AUDIO_GENERADO", Path(td),
        ):
            # Nombre exacto de la cache anterior a VERSION_AUDIO_TTS.
            clave_vieja = hashlib.sha256("\x1f".join(
                (voz.MODELO_VOZ, voz.VOZ_POR_DEFECTO, texto)
            ).encode("utf-8")).hexdigest()[:24]
            vieja = Path(td) / f"fortress_{clave_vieja}.mp3"
            vieja.write_bytes(b"clip truncado")

            with patch.object(voz, "_cliente", return_value=cliente):
                nueva = voz.generar_audio_correcto(texto)
            self.assertIsNotNone(nueva)
            self.assertNotEqual(Path(nueva), vieja)
            self.assertEqual(cliente.audio.speech.llamadas[0]["input"], "fortress,")
            self.assertEqual(Path(nueva).read_bytes(), b"mp3 completo")

            with patch.object(voz, "_cliente", return_value=None):
                reutilizada = voz.generar_audio_correcto(texto)
            self.assertEqual(reutilizada, nueva)
            self.assertEqual(len(cliente.audio.speech.llamadas), 1)

    def test_fallo_a_media_escritura_conserva_el_destino_y_degrada(self):
        respuesta = RespuestaAudio(b"parcial", fallar=True)
        cliente = ClienteFalso(respuesta)
        with tempfile.TemporaryDirectory() as td:
            destino = Path(td) / "referencia.mp3"
            destino.write_bytes(b"audio anterior bueno")
            with patch.object(voz, "_cliente", return_value=cliente):
                resultado = voz.generar_audio_correcto("fortress", destino)
            self.assertIsNone(resultado)
            self.assertEqual(destino.read_bytes(), b"audio anterior bueno")
            self.assertFalse(list(Path(td).glob("*.tmp")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
