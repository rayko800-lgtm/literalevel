"""Pruebas del ritmo de lectura (voz.medir_ritmo y su paso por practicar), sin red.

Whisper y el TTS van simulados con marcas de tiempo fabricadas; no se lee ninguna
clave ni se escribe fuera de una carpeta temporal.
Uso: python -X utf8 pruebas_voz_ritmo.py
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "app"))

import config  # noqa: E402

config.cargar = lambda *a, **k: None

import voz  # noqa: E402

FRASE = "I would like a cup of coffee please"


def seguidas(palabras: list[str], inicio: float, cada: float) -> list[tuple[str, float, float]]:
    return [(w, round(inicio + k * cada, 3), round(inicio + (k + 1) * cada, 3)) for k, w in enumerate(palabras)]


def como_dict(marcas: list[tuple[str, float, float]]) -> dict:
    return {"texto": " ".join(w for w, _, _ in marcas), "duracion": marcas[-1][2] if marcas else 0.0,
            "palabras": [{"palabra": w, "inicio": a, "fin": b} for w, a, b in marcas]}


# Referencia: 0,3 s por palabra, sin huecos. Lector: 0,34 s por palabra y una
# pausa de 0,6 s despues de «like».
REFERENCIA = seguidas(FRASE.split(), 0.0, 0.3)
LECTOR = seguidas(["I", "would", "like"], 0.0, 0.34) + seguidas(["a", "cup", "of", "coffee", "please"], 1.62, 0.34)


class MedirRitmo(unittest.TestCase):
    def setUp(self):
        self.ev = voz.evaluar_pronunciacion(FRASE, FRASE)

    def test_pausa_de_mas_y_objetivo_por_nivel(self):
        resultados = {n: voz.medir_ritmo(self.ev, como_dict(LECTOR), como_dict(REFERENCIA), n)
                      for n in (0.5, 1.0, 1.8)}
        r = resultados[1.0]
        self.assertTrue(r["medido"])
        self.assertEqual(len(r["palabras"]), 8)
        self.assertEqual(r["pausas"], [{"despues_de": 2, "segundos": 0.6, "en_referencia": False, "de_mas": True}])
        self.assertEqual([(t["desde"], t["hasta"]) for t in r["tramos"]], [(0, 2), (3, 7)])
        # Tramo 1: 2,94 palabras/s frente a 3,33 de referencia (88 %).
        self.assertEqual(r["tramos"][0]["palabras_por_segundo"], 2.94)
        self.assertEqual(r["tramos"][0]["referencia"], 3.33)
        self.assertFalse(resultados[0.5]["tramos"][0]["acelerar"], "basico: objetivo 80 %, va al 88 %")
        self.assertTrue(resultados[1.0]["tramos"][0]["acelerar"], "intermedio: objetivo 90 %")
        self.assertTrue(resultados[1.8]["tramos"][0]["acelerar"], "avanzado: objetivo 100 %")
        self.assertIsNone(r["natural"])

    def test_factor_por_nivel_y_sin_nivel(self):
        self.assertEqual([voz.factor_objetivo(n) for n in (0, 0.69, 0.7, 1.39, 1.4, 2)],
                         [0.8, 0.8, 0.9, 0.9, 1.0, 1.0])
        for raro in (None, "x", float("nan")):
            self.assertEqual(voz.factor_objetivo(raro), voz.FACTOR_SIN_NIVEL)

    def test_una_palabra_mal_oida_corta_el_tramo_y_no_lleva_marca(self):
        oido = [(("copy" if w == "coffee" else w), a, b) for w, a, b in LECTOR]
        ev = voz.evaluar_pronunciacion(FRASE, " ".join(w for w, _, _ in oido))
        r = voz.medir_ritmo(ev, como_dict(oido), como_dict(REFERENCIA), 1.0)
        self.assertNotIn("coffee", [p["palabra"] for p in r["palabras"]])
        self.assertEqual([(t["desde"], t["hasta"]) for t in r["tramos"]], [(0, 2), (3, 5)],
                         "«please», sola tras la palabra mal oida, no forma tramo")

    def test_sin_referencia_no_se_pide_acelerar(self):
        r = voz.medir_ritmo(self.ev, como_dict(LECTOR), None, 1.8)
        self.assertTrue(r["medido"])
        self.assertTrue(all(t["objetivo"] is None and not t["acelerar"] for t in r["tramos"]), r["tramos"])
        self.assertTrue(all(not p["en_referencia"] for p in r["pausas"]))

    def test_sin_marcas_del_lector_no_se_marca_nada(self):
        for tiempos in (None, {"texto": FRASE, "duracion": 2.0, "palabras": []}):
            r = voz.medir_ritmo(self.ev, tiempos, como_dict(REFERENCIA), 1.0)
            self.assertEqual(r, {"medido": False, "duracion_s": None, "palabras": [], "pausas": [],
                                 "tramos": [], "natural": None})


class ClienteSimulado:
    """whisper con marcas fabricadas y un TTS que escribe unos bytes."""

    def __init__(self):
        self.transcripciones: list[tuple[str, str | None, list | None]] = []
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self.transcribir),
                                     speech=SimpleNamespace(create=self.hablar))

    def transcribir(self, **kw):
        nombre = Path(kw["file"].name).name
        self.transcripciones.append((nombre, kw.get("response_format"), kw.get("timestamp_granularities")))
        marcas = REFERENCIA if nombre.endswith(".mp3") else LECTOR
        return SimpleNamespace(text=" ".join(w for w, _, _ in marcas), duration=marcas[-1][2],
                               words=[SimpleNamespace(word=w, start=a, end=b) for w, a, b in marcas])

    @staticmethod
    def hablar(**_kw):
        return SimpleNamespace(write_to_file=lambda ruta: Path(ruta).write_bytes(b"mp3 simulado"))


class Practicar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="literalevel_ritmo_")
        self.addCleanup(self.tmp.cleanup)
        self.carpeta = Path(self.tmp.name)
        self.grabacion = self.carpeta / "lector.webm"
        self.grabacion.write_bytes(b"audio del lector")
        parches = [mock.patch.object(voz, "RUTA_AUDIO_GENERADO", self.carpeta / "audio"),
                   mock.patch.object(voz, "RUTA_DB_POR_DEFECTO", str(self.carpeta / "voz.db"))]
        for p in parches:
            p.start()
            self.addCleanup(p.stop)

    def test_sin_clave_no_se_mide_y_no_revienta(self):
        with mock.patch.object(voz, "_cliente", lambda: None):
            s = voz.practicar(str(self.grabacion), FRASE, guardar_fallos=False, nivel=1.0)
        self.assertFalse(s.transcripcion_ok)
        self.assertEqual(s.ritmo["medido"], False)
        self.assertIsNone(s.ritmo["natural"])

    def test_con_whisper_simulado_mide_y_la_referencia_se_transcribe_una_vez(self):
        cliente = ClienteSimulado()
        with mock.patch.object(voz, "_cliente", lambda: cliente):
            s1 = voz.practicar(str(self.grabacion), FRASE, guardar_fallos=False, nivel=1.0)
            s2 = voz.practicar(str(self.grabacion), FRASE, guardar_fallos=False, nivel=0.5)
        self.assertTrue(s1.transcripcion_ok and s1.ritmo["medido"])
        self.assertEqual(s1.ritmo["pausas"][0]["despues_de"], 2)
        self.assertTrue(s1.ritmo["tramos"][0]["acelerar"])
        self.assertFalse(s2.ritmo["tramos"][0]["acelerar"], "el nivel del segundo intento es basico")
        formatos = {(f, g and tuple(g)) for _n, f, g in cliente.transcripciones}
        self.assertEqual(formatos, {("verbose_json", ("word",))}, "siempre con marcas por palabra")
        referencia = [n for n, _f, _g in cliente.transcripciones if n.endswith(".mp3")]
        self.assertEqual(len(referencia), 1, "la frase bien leida se transcribe una sola vez")
        self.assertTrue(Path(str(s1.audio_correcto) + ".tiempos.json").is_file())
        self.assertEqual(list((self.carpeta / "audio").rglob("*.tmp")), [])


class TranscribirConTiempos(unittest.TestCase):
    def test_lee_objetos_o_diccionarios_y_salta_marcas_rotas(self):
        respuesta = {"text": "hi there", "duration": 1.2,
                     "words": [{"word": "hi", "start": 0.0, "end": 0.3}, {"word": "there", "start": "x", "end": 1}]}
        cliente = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=lambda **kw: respuesta)))
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(b"audio")
        try:
            with mock.patch.object(voz, "_cliente", lambda: cliente):
                datos = voz.transcribir_con_tiempos(f.name)
        finally:
            Path(f.name).unlink()
        self.assertEqual(datos, {"texto": "hi there", "duracion": 1.2,
                                 "palabras": [{"palabra": "hi", "inicio": 0.0, "fin": 0.3}]})

    def test_si_falla_devuelve_none(self):
        def reventar(**_kw):
            raise TimeoutError("simulado")
        cliente = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=reventar)))
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(b"audio")
        try:
            with mock.patch.object(voz, "_cliente", lambda: cliente):
                self.assertIsNone(voz.transcribir_con_tiempos(f.name))
        finally:
            Path(f.name).unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
