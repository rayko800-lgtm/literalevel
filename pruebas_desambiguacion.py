"""Regresiones locales de acepciones, afinidad, avisos y cache por idioma.

Ejecutar con los modelos ya descargados:
    python -X utf8 pruebas_desambiguacion.py
No lee claves ni llama a OpenAI. La BD se abre en modo de solo lectura y la
cache es SQLite en memoria. Los tests de ranking usan spaCy/MiniLM reales;
los de fallos y cache simulan exclusivamente las dependencias indicadas.
"""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, "app")
import lexicon  # noqa: E402


class DesambiguacionReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.consultor = lexicon.ConsultorLexico(ruta_cache=":memory:")
        cls.consultor._sin_clave = True

    @classmethod
    def tearDownClass(cls):
        cls.consultor.cerrar()

    def test_sentidos_y_contratos(self):
        casos = [
            ("peeped", "Once or twice she had peeped into the book her sister was reading.",
             "To look forth from concealment", "verb", "peep", 6),
            ("peeped", "She peeped through the keyhole to see who was outside.",
             "To look forth from concealment", "verb", "peep", 6),
            ("peeped", "The chicks peeped softly in their nest.",
             "To make a soft, shrill noise like a baby bird.", "verb", "peep", 6),
            ("peeped", "She peeped a quiet reply.",
             "To speak briefly with a quiet voice.", "verb", "peep", 6),
            ("brook", "A small brook ran behind the old cottage.",
             "a small stream", "noun", "brook", 2),
            ("brook", "He could not brook such an insult from a stranger.",
             "tolerate", "verb", "brook", 3),
            ("set off", "The fireworks will set off at midnight over the bay.",
             "To cause to explode", "verb", "set off", 7),
            ("set off", "They set off on a long journey at dawn.",
             "to begin a journey", "verb", "set off", 7),
            ("notwithstanding", "Notwithstanding the rain, they continued the hike.",
             "In spite of, despite.", None, "notwithstanding", 4),
            ("free", "You are free to leave whenever you want.",
             "liberated", "adj", "free", None),
            ("welcome", "You are always welcome in this house.",
             "received with gladness", "adj", "welcome", None),
        ]
        for palabra, oracion, glosa, categoria, lema, cantidad in casos:
            with self.subTest(oracion=oracion):
                r = self.consultor.consultar(palabra, oracion, 1.0)
                self.assertIsNotNone(r.sentido)
                self.assertIn(glosa, r.sentido)
                self.assertEqual(r.categoria, categoria)
                self.assertEqual(r.lema_buscado, lema)
                if cantidad is not None:
                    self.assertEqual(r.n_sentidos_candidatos, cantidad)
                self.assertIsNone(r.definicion_contextual)
                self.assertTrue(any("OPENAI_API_KEY" in a for a in r.avisos))
                print(f"  OK {palabra}: {r.sentido} (afinidad {r.similitud})")

    def test_afinidad_publica_y_margen(self):
        oracion = "Once or twice she had peeped into the book her sister was reading."
        r = self.consultor.consultar("peeped", oracion, 1.0)
        modelo = lexicon._cargar_embebedor()
        v = modelo.encode([oracion, r.sentido], normalize_embeddings=True)
        self.assertEqual(r.similitud, round(float(v[0] @ v[1]), 4))
        self.assertTrue(any("acepcion provisional" in a for a in r.avisos))

    def test_cache_separa_idioma_y_acepcion(self):
        c = lexicon.ConsultorLexico(ruta_cache=":memory:")
        oracion = "Once or twice she had peeped into the book her sister was reading."
        glosa_vieja = "To speak briefly with a quiet voice."

        def respuesta(texto):
            return dict.fromkeys(("definicion_contextual", "explicacion_gramatical",
                                  "explicacion_adaptada", "ejemplo_simplificado"), texto)

        # Una explicacion previa sobre la acepcion erronea no debe reutilizarse.
        c.cache.guardar_respuesta(
            respuesta("acepcion erronea"), c.modelo_openai,
            "contextual", "peep", "verb", glosa_vieja, oracion,
            lexicon.public_band(1.0), c.modelo_openai, "es")
        try:
            with patch.object(c, "_cliente", return_value=object()), \
                 patch.object(lexicon, "_mejor_fonetica", return_value=(None, None, "uk", "us")), \
                 patch.object(lexicon, "_pedir_explicacion_openai",
                              side_effect=lambda *a, **kw: respuesta(kw["idioma"])) as pedir:
                for idioma in ("es", "en"):
                    primera = c.consultar("peeped", oracion, 1.0, idioma=idioma)
                    segunda = c.consultar("peeped", oracion, 1.0, idioma=idioma)
                    self.assertFalse(primera.desde_cache)
                    self.assertTrue(segunda.desde_cache)
                    self.assertEqual(segunda.definicion_contextual, idioma)
                    self.assertTrue(any("acepcion provisional" in a for a in segunda.avisos))
                self.assertEqual(pedir.call_count, 2)
                for llamada in pedir.call_args_list:
                    self.assertIn("To look forth from concealment", llamada.kwargs["glosa"])
        finally:
            c.cerrar()

    def test_sin_modelo_o_red_conserva_diccionario(self):
        with patch.object(lexicon, "_cargar_embebedor", side_effect=OSError("sin red")):
            r = self.consultor.consultar("brook", "A small brook ran behind the old cottage.", 1.0)
        self.assertIsNotNone(r.sentido)
        self.assertIsNone(r.similitud)
        self.assertTrue(any("sin modelo de embeddings" in a for a in r.avisos))


class BordesDelRanking(unittest.TestCase):
    @staticmethod
    def pares(*glosas):
        sentidos = [lexicon.Sentido(g, "noun") for g in glosas]
        entrada = lexicon.EntradaDiccionario("test", "noun", sentidos, None, None, None, None)
        return [(entrada, s) for s in sentidos]

    def test_vacio_y_unico_no_cargan_modelo(self):
        with patch.object(lexicon, "_cargar_embebedor", side_effect=AssertionError("carga innecesaria")):
            self.assertEqual(lexicon._elegir_sentido("contexto", []), (None, None, []))
            pares = self.pares("unico")
            self.assertEqual(lexicon._elegir_sentido("contexto", pares), (pares[0][1], None, []))

    def test_margen_ignora_glosas_duplicadas(self):
        # Vectores unitarios: las dos copias puntuan 0.8, el rival 0.6.
        class Modelo:
            def encode(self, textos, **kwargs):
                vectores = {"contexto": [1., 0.], "igual": [.8, .6], "rival": [.6, .8]}
                return lexicon.np.array([vectores[t] for t in textos])

        with patch.object(lexicon, "_cargar_embebedor", return_value=Modelo()):
            elegido, similitud, avisos = lexicon._elegir_sentido(
                "contexto", self.pares("igual", "igual", "rival"))
        self.assertEqual(elegido.glosa, "igual")
        self.assertAlmostEqual(similitud, .8)
        self.assertEqual(avisos, [])

    def test_empate_entre_glosas_distintas_avisa(self):
        class Modelo:
            def encode(self, textos, **kwargs):
                return lexicon.np.array([[1., 0.] for _ in textos])

        with patch.object(lexicon, "_cargar_embebedor", return_value=Modelo()):
            elegido, _, avisos = lexicon._elegir_sentido("contexto", self.pares("uno", "dos"))
        self.assertEqual(elegido.glosa, "uno")
        self.assertTrue(any("margen bajo (0.000)" in a and "dos" in a for a in avisos))


if __name__ == "__main__":
    unittest.main(verbosity=2)
