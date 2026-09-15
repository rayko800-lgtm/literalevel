"""Pruebas del ritmo de lectura (voz.medir_ritmo y su paso por practicar), sin red.

Whisper y el TTS van simulados con marcas de tiempo fabricadas; no se lee ninguna
clave ni se escribe fuera de una carpeta temporal.
Uso: python -X utf8 pruebas_voz_ritmo.py
"""
from __future__ import annotations

import sys
import tempfile
import threading
import time
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


# Lo que devolveria el modelo para FRASE, con cosas que NO casan a proposito:
# posiciones fuera de la frase, un enlace entre palabras no seguidas, un tipo
# inventado, una reduccion sin IPA y un tramo de una sola palabra.
RESPUESTA_NATURAL = {
    "enfasis": [{"indice": 4, "ipa": "/ˈkʌp/"}, {"indice": 6, "ipa": "/ˈkɔfi/"}, {"indice": 99, "ipa": "/x/"}],
    "enlaces": [{"de": 4, "a": 5, "tipo": "consonante_vocal", "ipa": "/ˈkʌ.pəv/"},
                {"de": 2, "a": 4, "tipo": "consonante_vocal", "ipa": "/x/"},
                {"de": 1, "a": 2, "tipo": "inventado", "ipa": "/x/"}],
    "reducciones": [{"desde": 0, "hasta": 1, "forma": "I'd", "ipa": "/aɪd/"},
                    {"desde": 5, "hasta": 5, "forma": "a", "ipa": ""},
                    {"desde": 3, "hasta": 9, "forma": "x", "ipa": "/x/"}],
    "tramos_rapidos": [{"desde": 3, "hasta": 6}, {"desde": 6, "hasta": 6}],
    "version_natural": "I'd like a cuppa coffee please",
}
# «cuppa» no esta respaldada por ninguna reduccion validada: la version se reconstruye.
NATURAL_VALIDADO = {
    # La IPA del enfasis sale del diccionario, no del modelo (M3).
    "enfasis": [{"indice": 4, "ipa": voz._ipa_de_diccionario("cup")},
                {"indice": 6, "ipa": voz._ipa_de_diccionario("coffee")}],
    "enlaces": [{"de": 4, "a": 5, "tipo": "consonante_vocal", "ipa": voz._ipa_enlace("cup", "of")}],
    "reducciones": [{"desde": 0, "hasta": 1, "forma": "I'd", "ipa": "/aɪd/", "generado_por_ia": True}],
    "tramos_rapidos": [{"desde": 3, "hasta": 6}],
    "version_natural": "I'd like a cup of coffee please",
}
PALABRAS = voz.normalizar_palabras(FRASE)

# La primera frase real (14 sep), tal cual la devolvio gpt-4o-mini: «to come» -> «gonna»
# es inventada, y «don't you», «want to» y «to come» no son enlaces consonante+vocal.
FRASE_REAL = "Don't you want to come with us?"
RESPUESTA_REAL = {
    "enfasis": [{"indice": 0, "ipa": "/ˈdoʊnt/"}, {"indice": 2, "ipa": "/wɑnt/"},
                {"indice": 4, "ipa": "/kʌm/"}, {"indice": 6, "ipa": "/ʌs/"}],
    "enlaces": [{"de": 0, "a": 1, "tipo": "consonante_vocal", "ipa": "/ˈdoʊn.tʃə/"},
                {"de": 2, "a": 3, "tipo": "consonante_vocal", "ipa": "/wɑn.tə/"},
                {"de": 3, "a": 4, "tipo": "consonante_vocal", "ipa": "/tə.kʌm/"},
                {"de": 5, "a": 6, "tipo": "consonante_vocal", "ipa": "/wɪð.ʌs/"}],
    "reducciones": [{"desde": 0, "hasta": 1, "forma": "doncha", "ipa": "/ˈdoʊntʃə/"},
                    {"desde": 2, "hasta": 3, "forma": "wanna", "ipa": "/ˈwɑnə/"},
                    {"desde": 3, "hasta": 4, "forma": "gonna", "ipa": "/ˈɡʌnə/"}],
    "tramos_rapidos": [{"desde": 0, "hasta": 3}, {"desde": 4, "hasta": 6}],
    "version_natural": "Doncha wanna come with us?",
}


class ClienteSimulado:
    """whisper con marcas fabricadas, un TTS que escribe unos bytes y el analisis."""

    def __init__(self):
        self.transcripciones: list[tuple[str, str | None, list | None]] = []
        self.analisis: list[dict] = []
        self.habladas: list[str] = []
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self.transcribir),
                                     speech=SimpleNamespace(create=self.hablar))
        self.chat = SimpleNamespace(completions=SimpleNamespace(parse=self.analizar))

    def analizar(self, **kw):
        self.analisis.append(kw)
        parsed = voz.AnalisisNatural(**RESPUESTA_NATURAL)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))])

    def transcribir(self, **kw):
        nombre = Path(kw["file"].name).name
        self.transcripciones.append((nombre, kw.get("response_format"), kw.get("timestamp_granularities")))
        marcas = REFERENCIA if nombre.endswith(".mp3") else LECTOR
        return SimpleNamespace(text=" ".join(w for w, _, _ in marcas), duration=marcas[-1][2],
                               words=[SimpleNamespace(word=w, start=a, end=b) for w, a, b in marcas])

    def hablar(self, **kw):
        self.habladas.append(str(kw.get("input", "")))
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

    def test_sin_transcripcion_no_se_guardan_fallos_aunque_se_pida(self):
        """e6, 14 sep (M1): con guardar_fallos=True y sin transcripcion guardaba la frase entera."""
        with mock.patch.object(voz, "_cliente", lambda: None), \
                mock.patch.object(voz, "registrar_fallos") as registrar, \
                mock.patch.object(voz, "registrar_ritmo"):
            s = voz.practicar(str(self.grabacion), FRASE, guardar_fallos=True, nivel=1.0)
        self.assertFalse(s.transcripcion_ok)
        self.assertFalse(s.sin_voz, "sin clave no hubo respuesta de whisper: el uso no se devuelve")
        registrar.assert_not_called()

    def test_con_transcripcion_vacia_no_se_guarda_nada_ni_se_da_por_transcrita(self):
        """e6, rondas 2 y 3 (M1): whisper da "" o "..." con silencio; se guardaba la frase
        entera, se pedian sus audios y se pagaba una explicacion de palabras que nadie dijo."""
        for texto in ("  ", "...", "♪"):
            cliente = ClienteSimulado()

            def silencio(texto=texto, cliente=cliente, **kw):
                cliente.transcripciones.append((Path(kw["file"].name).name, kw.get("response_format"), None))
                return SimpleNamespace(text=texto, duration=2.0, words=[])
            cliente.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=silencio), speech=cliente.audio.speech)
            with mock.patch.object(voz, "_cliente", lambda cliente=cliente: cliente), \
                    mock.patch.object(voz, "explicar_correccion") as explicar, \
                    mock.patch.object(voz, "registrar_fallos") as registrar, \
                    mock.patch.object(voz, "registrar_ritmo"):
                s = voz.practicar(str(self.grabacion), FRASE, guardar_fallos=True, nivel=1.0)
            self.assertFalse(s.transcripcion_ok, f"{texto!r}: la API y Gradio guardan si transcripcion_ok")
            self.assertTrue(s.sin_voz, f"{texto!r}: whisper respondio sin palabras, el uso se devuelve")
            registrar.assert_not_called()
            explicar.assert_not_called()
            self.assertIsNone(s.correccion, texto)
            self.assertEqual(s.audios_palabras, {}, f"{texto!r}: sin palabras oidas, los audios de cada palabra son gasto")
            # Central y f4, reinicio 24: la respuesta seguia trayendo el mp3 de la frase, tts-1
            # por grabacion con una frase nueva; y el analisis natural y su audio, otros dos.
            self.assertEqual(cliente.habladas, [], f"{texto!r}: sin voz no se llama al TTS")
            self.assertEqual(cliente.analisis, [], f"{texto!r}: sin voz no se analiza la frase")
            self.assertIsNone(s.audio_correcto, texto)
            self.assertIsNone(s.ritmo["natural"], texto)

    def test_lo_que_whisper_inventa_sin_voz_no_cuenta_como_oido(self):
        """Central y e6, ronda 3: con casi silencio whisper escribe «Thank you for watching.»
        con palabras y todo; se pagaba la explicacion de una frase que nadie dijo. f4, reinicio 23:
        con 2,5 s de WAV a cero whisper-1 dio «you» (0,943 en la medida local). e6: con dos segmentos,
        uno dudoso y otro con voz, la grabacion cuenta; si no, sobrevive el mutante all -> any."""
        for texto, no_voz, oida in (("you", (0.943,), False), ("Thank you for watching.", (0.897,), False),
                                    ("Thank you for watching.", (0.503,), True),
                                    ("Thank you for watching.", (0.9, 0.2), True)):
            cliente = ClienteSimulado()

            def inventa(texto=texto, no_voz=no_voz, cliente=cliente, **kw):
                cliente.transcripciones.append((Path(kw["file"].name).name, kw.get("response_format"), kw.get("timestamp_granularities")))
                return SimpleNamespace(text=texto, duration=3.0,
                                       words=[SimpleNamespace(word=w, start=1.6 + i * 0.3, end=1.9 + i * 0.3)
                                              for i, w in enumerate(texto.split())],
                                       segments=[SimpleNamespace(start=1.58 + i, end=2.58 + i, text=" " + texto,
                                                                 no_speech_prob=p, avg_logprob=-0.82)
                                                 for i, p in enumerate(no_voz)])
            cliente.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=inventa), speech=cliente.audio.speech)
            with mock.patch.object(voz, "_cliente", lambda cliente=cliente: cliente), \
                    mock.patch.object(voz, "explicar_correccion") as explicar, \
                    mock.patch.object(voz, "registrar_fallos") as registrar, \
                    mock.patch.object(voz, "registrar_ritmo"):
                s = voz.practicar(str(self.grabacion), FRASE, guardar_fallos=True, nivel=1.0)
            self.assertEqual(s.transcripcion_ok, oida, (texto, no_voz))
            self.assertEqual(s.sin_voz, not oida, f"{texto!r} con {no_voz}: sin_voz")
            self.assertEqual(explicar.called, oida, f"{texto!r} con no_speech_prob {no_voz}: explicacion de pago")
            self.assertEqual(registrar.called, oida, (texto, no_voz))
            self.assertEqual(s.audio_correcto is not None, oida, (texto, no_voz))
            # Los casos sin voz van primero, con la cache de audio aun vacia: si se pidiera el
            # mp3 de la frase o sus marcas, se veria aqui. Con voz la cache ya puede tenerlos.
            if not oida:
                self.assertEqual(cliente.habladas, [], f"{texto!r} con {no_voz}: TTS de la frase modelo")
                self.assertEqual(len(cliente.transcripciones), 1,
                                 f"{texto!r} con {no_voz}: sin voz la referencia no se transcribe")
            self.assertIn("segment", cliente.transcripciones[0][2], "sin pedir segmentos whisper no los manda")

    def test_si_rechazan_las_marcas_se_transcribe_sin_ellas_y_si_no_no(self):
        """e6, 14 sep (M5): con un plazo agotado el audio pudo cobrarse; no se sube otra vez."""
        class Rechazo(Exception):
            status_code = 400
        for error, esperadas, ok in ((Rechazo("formato"), 2, True), (TimeoutError("plazo"), 1, False)):
            llamadas = []

            def crear(error=error, llamadas=llamadas, **kw):
                llamadas.append(kw.get("response_format"))
                if kw.get("response_format") == "verbose_json":
                    raise error
                return SimpleNamespace(text=FRASE)
            cliente = ClienteSimulado()
            cliente.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=crear),
                                            speech=cliente.audio.speech)
            with mock.patch.object(voz, "_cliente", lambda: cliente), \
                    mock.patch.object(voz, "explicar_correccion", lambda *a, **k: None):
                s = voz.practicar(str(self.grabacion), FRASE, guardar_fallos=False, nivel=1.0)
            self.assertEqual(len(llamadas), esperadas, (error, llamadas))
            self.assertEqual(s.transcripcion_ok, ok)
            self.assertFalse(s.sin_voz, f"{error!r}: con voz o sin respuesta, sin_voz es False")

    def test_la_referencia_pedida_a_la_vez_se_transcribe_una_vez(self):
        """e6, 14 sep (M4): sin candado, dos lectores con la misma frase pagaban dos whisper."""
        cliente = ClienteSimulado()
        transcribir = cliente.transcribir

        def lento(**kw):
            time.sleep(0.3)
            return transcribir(**kw)
        cliente.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=lento), speech=cliente.audio.speech)
        mp3 = self.carpeta / "referencia.mp3"
        mp3.write_bytes(b"mp3 simulado")
        salidas = []
        with mock.patch.object(voz, "_cliente", lambda: cliente):
            hilos = [threading.Thread(target=lambda: salidas.append(voz._tiempos_de_referencia(mp3)))
                     for _ in range(3)]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
        self.assertEqual(len(cliente.transcripciones), 1)
        self.assertTrue(len(salidas) == 3 and all(s and s["palabras"] for s in salidas), salidas)

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
        self.assertEqual(formatos, {("verbose_json", ("word", "segment"))},
                         "siempre con marcas por palabra, y con segmentos para saber si hubo voz")
        referencia = [n for n, _f, _g in cliente.transcripciones if n.endswith(".mp3")]
        self.assertEqual(len(referencia), 1, "la frase bien leida se transcribe una sola vez")
        self.assertTrue(Path(str(s1.audio_correcto) + ".tiempos.json").is_file())
        self.assertEqual(list((self.carpeta / "audio").rglob("*.tmp")), [])


class Natural(unittest.TestCase):
    """Parte 2: el analisis del modelo, validado contra la frase y cacheado."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="literalevel_natural_")
        self.addCleanup(self.tmp.cleanup)
        self.carpeta = Path(self.tmp.name)
        self.grabacion = self.carpeta / "lector.webm"
        self.grabacion.write_bytes(b"audio del lector")
        parches = [mock.patch.object(voz, "RUTA_AUDIO_GENERADO", self.carpeta / "audio"),
                   mock.patch.object(voz, "RUTA_DB_POR_DEFECTO", str(self.carpeta / "voz.db"))]
        for p in parches:
            p.start()
            self.addCleanup(p.stop)

    def test_se_descarta_lo_que_no_casa_con_la_frase(self):
        self.assertEqual(voz._validar_natural(RESPUESTA_NATURAL, PALABRAS, FRASE), NATURAL_VALIDADO)
        # Y leyendo el objeto de pydantic, como llega del SDK.
        self.assertEqual(voz._validar_natural(voz.AnalisisNatural(**RESPUESTA_NATURAL), PALABRAS, FRASE),
                         NATURAL_VALIDADO)

    def test_la_primera_frase_real_sin_lo_inventado(self):
        datos = voz._validar_natural(RESPUESTA_REAL, voz.normalizar_palabras(FRASE_REAL), FRASE_REAL)
        self.assertEqual([(r["desde"], r["hasta"], r["forma"]) for r in datos["reducciones"]],
                         [(0, 1, "doncha"), (2, 3, "wanna")], "«to come» -> «gonna» fuera")
        self.assertEqual([(e["de"], e["a"]) for e in datos["enlaces"]], [(5, 6)], "solo «with us» se enlaza")
        self.assertEqual(datos["version_natural"], "Doncha wanna come with us?")
        self.assertEqual([e["indice"] for e in datos["enfasis"]], [0, 2, 4], "«us» es funcional: sin enfasis")
        self.assertEqual(datos["enlaces"][0]["ipa"], voz._ipa_enlace("with", "us"))

    def test_enlace_con_ipa_de_diccionario_y_enfasis_sin_funcionales(self):
        """Bateria del 14 sep: «little of» llego con IPA «/ə/» y «of» con enfasis."""
        frase = "Would you like to see a little of it?"
        bruto = {"enfasis": [{"indice": 0, "ipa": "/wʊd/"}, {"indice": 6, "ipa": "/ˈlɪtəl/"},
                             {"indice": 7, "ipa": "/ʌv/"}],
                 "enlaces": [{"de": 6, "a": 7, "tipo": "consonante_vocal", "ipa": "/ə/"},
                             {"de": 7, "a": 8, "tipo": "consonante_vocal", "ipa": "/əv/"}],
                 "reducciones": [], "tramos_rapidos": [], "version_natural": frase}
        datos = voz._validar_natural(bruto, voz.normalizar_palabras(frase), frase)
        self.assertEqual([e["indice"] for e in datos["enfasis"]], [0, 6], "«of» sin enfasis")
        self.assertEqual([e["ipa"] for e in datos["enlaces"]],
                         [voz._ipa_enlace("little", "of"), voz._ipa_enlace("of", "it")])
        self.assertTrue(all("‿" in e["ipa"] and e["ipa"] != "/ə/" for e in datos["enlaces"]), datos["enlaces"])

    def test_reducciones_solapadas_o_de_otras_palabras_fuera(self):
        bruto = {**RESPUESTA_REAL, "reducciones": [
            {"desde": 2, "hasta": 3, "forma": "wanna", "ipa": "/ˈwɑnə/"},
            {"desde": 2, "hasta": 3, "forma": "gotta", "ipa": "/ˈɡɑtə/"},
            {"desde": 4, "hasta": 5, "forma": "kinda", "ipa": "/ˈkaɪndə/"}],
                 "version_natural": "Don't you gotta come with us?"}
        datos = voz._validar_natural(bruto, voz.normalizar_palabras(FRASE_REAL), FRASE_REAL)
        self.assertEqual([r["forma"] for r in datos["reducciones"]], ["wanna"])
        self.assertEqual(datos["version_natural"], "Don't you wanna come with us?", "reconstruida")

    def test_gonna_y_gotta_solo_con_verbo_detras(self):
        """e6, 14 sep: «I am going to school» -> «I am gonna school» llegaba al TTS."""
        if voz._etiquetador() is None:
            self.skipTest("sin spaCy estas reducciones no se aceptan nunca")
        casos = [("I am going to school.", 2, 3, "gonna", False),
                 ("We got to the station late.", 1, 2, "gotta", False),
                 ("She is going to London tomorrow.", 2, 3, "gonna", False),
                 ("I am going to leave now.", 2, 3, "gonna", True),
                 ("You have to go.", 1, 2, "hafta", True)]
        for frase, desde, hasta, forma, vale in casos:
            bruto = {"enfasis": [], "enlaces": [], "tramos_rapidos": [], "version_natural": "",
                     "reducciones": [{"desde": desde, "hasta": hasta, "forma": forma, "ipa": "/x/"}]}
            datos = voz._validar_natural(bruto, voz.normalizar_palabras(frase), frase)
            self.assertEqual(bool(datos["reducciones"]), vale, (frase, datos["reducciones"]))
            if not vale:
                self.assertEqual(datos["version_natural"], frase, "sin la reduccion falsa, la frase tal cual")
        self.assertEqual(voz._validar_natural(RESPUESTA_REAL, voz.normalizar_palabras(FRASE_REAL),
                                              FRASE_REAL)["version_natural"],
                         "Doncha wanna come with us?", "«want to come» si lleva verbo detras")

    def test_sin_spacy_no_se_acepta_ninguna_que_pida_verbo(self):
        frase = "I am going to leave now."
        bruto = {"enfasis": [], "enlaces": [], "tramos_rapidos": [], "version_natural": "",
                 "reducciones": [{"desde": 2, "hasta": 3, "forma": "gonna", "ipa": "/x/"},
                                 {"desde": 0, "hasta": 1, "forma": "I'm", "ipa": "/aɪm/"}]}
        with mock.patch.object(voz, "_etiquetador", lambda: None):
            datos = voz._validar_natural(bruto, voz.normalizar_palabras(frase), frase)
        self.assertEqual([r["forma"] for r in datos["reducciones"]], ["I'm"], "la contraccion no pide verbo")

    def test_una_reduccion_falsa_ya_guardada_se_quita_al_leer(self):
        frase = "I am going to school."
        viejo = {"enfasis": [], "enlaces": [], "tramos_rapidos": [], "version_natural": "I am gonna school.",
                 "reducciones": [{"desde": 2, "hasta": 3, "forma": "gonna", "ipa": "/ˈɡʌnə/",
                                  "generado_por_ia": True}]}
        ruta = voz._ruta_analisis_natural(frase)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(__import__("json").dumps(viejo, ensure_ascii=False), encoding="utf-8")
        with mock.patch.object(voz, "_cliente", lambda: None):
            datos = voz.analizar_natural(frase)
        self.assertEqual(datos["reducciones"], [])
        self.assertEqual(datos["version_natural"], frase)

    def test_sin_enlace_a_traves_de_un_punto(self):
        """e6, 14 sep (M2): «Stop. Eat it.» aceptaba stop‿eat."""
        frase = "Stop. Eat it."
        bruto = {"enfasis": [], "reducciones": [], "tramos_rapidos": [], "version_natural": frase,
                 "enlaces": [{"de": 0, "a": 1, "tipo": "consonante_vocal", "ipa": "/x/"},
                             {"de": 1, "a": 2, "tipo": "consonante_vocal", "ipa": "/x/"}]}
        datos = voz._validar_natural(bruto, voz.normalizar_palabras(frase), frase)
        self.assertEqual([(e["de"], e["a"]) for e in datos["enlaces"]], [(1, 2)])
        otra = "Wait, stop! Are you sure? Yes."
        self.assertEqual(voz._fronteras_de_frase(otra, voz.normalizar_palabras(otra)), {1, 4, 5},
                         "la coma no corta; el signo de fin de frase si")

    def test_el_punto_de_un_tratamiento_no_acaba_la_frase(self):
        """e6, ronda 2: «Mr. Adams» cortaba el enlace como si fuera fin de frase."""
        for frase, esperadas in (("Mr. Adams ate it.", {3}),
                                 ("I stopped. Mrs. Evans and Dr. Ross left.", {1, 7}),
                                 ("Talk to Prof. Adams.", {3}),
                                 # «St.» puede cerrar la frase: se corta tambien ante un
                                 # nombre (e6, ronda 3), mejor que colar st‿it.
                                 ("He lives on Baker St. It was late.", {4, 7}),
                                 ("\"Mr. Ives,\" said Ms. Orr of St. Anne.", {6, 7})):
            self.assertEqual(voz._fronteras_de_frase(frase, voz.normalizar_palabras(frase)), esperadas, frase)

    def test_ipa_del_enfasis_del_diccionario_y_no_del_modelo(self):
        """e6, 14 sep (M3): «cualquier cosa» salia como /cualquier cosa/."""
        bruto = {**RESPUESTA_NATURAL, "enfasis": [{"indice": 4, "ipa": "cualquier cosa"}]}
        datos = voz._validar_natural(bruto, PALABRAS, FRASE)
        self.assertEqual(datos["enfasis"], [{"indice": 4, "ipa": voz._ipa_de_diccionario("cup")}])
        self.assertTrue(str(datos["enfasis"][0]["ipa"]).startswith("/") and "cualquier" not in str(datos))

    def test_dos_lectores_a_la_vez_pagan_un_solo_analisis(self):
        """e6, 14 sep (M4): sin candado, la misma frase nueva a la vez pagaba dos analisis."""
        cliente = ClienteSimulado()
        analizar = cliente.analizar

        def lento(**kw):
            time.sleep(0.3)
            return analizar(**kw)
        cliente.chat = SimpleNamespace(completions=SimpleNamespace(parse=lento))
        resultados = []
        with mock.patch.object(voz, "_cliente", lambda: cliente):
            hilos = [threading.Thread(target=lambda: resultados.append(voz.analizar_natural(FRASE)))
                     for _ in range(3)]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
        self.assertEqual(len(cliente.analisis), 1)
        self.assertEqual(resultados, [NATURAL_VALIDADO] * 3)

    def test_version_natural_vacia_o_desmedida_vuelve_a_la_frase(self):
        for version in ("", "   ", "x" * 500):
            datos = voz._validar_natural({**RESPUESTA_NATURAL, "version_natural": version}, PALABRAS, FRASE)
            self.assertEqual(datos["version_natural"], NATURAL_VALIDADO["version_natural"])
        sin_reducciones = voz._validar_natural({**RESPUESTA_NATURAL, "reducciones": []}, PALABRAS, FRASE)
        self.assertEqual(sin_reducciones["version_natural"], FRASE, "sin reducciones, la frase tal cual")

    def test_se_cachea_y_se_sirve_sin_clave(self):
        cliente = ClienteSimulado()
        with mock.patch.object(voz, "_cliente", lambda: cliente):
            primero = voz.analizar_natural(FRASE)
        with mock.patch.object(voz, "_cliente", lambda: None):
            guardado = voz.analizar_natural(FRASE)
            otra = voz.analizar_natural("Nobody has analysed this sentence yet")
        self.assertEqual(primero, NATURAL_VALIDADO)
        self.assertEqual(guardado, NATURAL_VALIDADO, "lo guardado se sirve aunque no haya clave")
        self.assertIsNone(otra, "sin cache y sin clave, no hay analisis")
        self.assertEqual(len(cliente.analisis), 1)
        self.assertEqual(list((self.carpeta / "analisis_natural").glob("*.tmp")), [])

    def test_lo_guardado_antes_se_pule_al_leer_sin_llamar(self):
        frase = "Would you like to see a little of it?"
        viejo = {"enfasis": [{"indice": 7, "ipa": "/ʌv/"}, {"indice": 2, "ipa": "/laɪk/"}],
                 "enlaces": [{"de": 6, "a": 7, "tipo": "consonante_vocal", "ipa": "/ə/"}],
                 "reducciones": [], "tramos_rapidos": [], "version_natural": frase}
        ruta = voz._ruta_analisis_natural(frase)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(__import__("json").dumps(viejo, ensure_ascii=False), encoding="utf-8")
        with mock.patch.object(voz, "_cliente", lambda: None):
            datos = voz.analizar_natural(frase)
        self.assertEqual([e["indice"] for e in datos["enfasis"]], [2])
        self.assertEqual(datos["enlaces"][0]["ipa"], voz._ipa_enlace("little", "of"))

    def test_una_llamada_que_falla_no_rompe_ni_se_guarda(self):
        def reventar(**_kw):
            raise TimeoutError("simulado")
        cliente = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=reventar)))
        with mock.patch.object(voz, "_cliente", lambda: cliente):
            self.assertIsNone(voz.analizar_natural(FRASE))
        self.assertFalse((self.carpeta / "analisis_natural").exists())

    def test_practicar_rellena_natural_con_su_audio_y_analiza_una_vez(self):
        cliente = ClienteSimulado()
        with mock.patch.object(voz, "_cliente", lambda: cliente):
            s1 = voz.practicar(str(self.grabacion), FRASE, guardar_fallos=False, nivel=1.0)
            s2 = voz.practicar(str(self.grabacion), FRASE, guardar_fallos=False, nivel=1.0)
        natural = s1.ritmo["natural"]
        self.assertEqual({k: v for k, v in natural.items() if k != "audio_natural"}, NATURAL_VALIDADO)
        self.assertTrue(natural["audio_natural"] and Path(natural["audio_natural"]).is_file())
        self.assertNotEqual(natural["audio_natural"], s1.audio_correcto, "la version natural es otra frase")
        self.assertIn("I'd like a cup of coffee please", " ".join(cliente.habladas))
        self.assertEqual(len(cliente.analisis), 1, "la segunda vez sale de la cache")
        self.assertEqual(s2.ritmo["natural"]["enlaces"], NATURAL_VALIDADO["enlaces"])
        numeradas = cliente.analisis[0]["messages"][1]["content"]
        self.assertIn("0:i 1:would 2:like", numeradas.lower(), "el modelo recibe las posiciones")


class FonemaDeUnaPalabraRepetida(unittest.TestCase):
    def test_la_misma_palabra_fallada_de_dos_maneras(self):
        """e6, 14 sep: con «cat» oida «cut» y luego «cap», los dos detalles salian con /t/."""
        por_separado = [voz.fonema_que_cambia("cat", "cut"), voz.fonema_que_cambia("cat", "cap")]
        self.assertNotEqual(por_separado[0], por_separado[1], por_separado)
        c = voz.Correccion(resumen="Casi.", detalles=[
            voz.DetallePalabra(palabra="cat", fonema="t", sonido_que_falla="x", como_colocar_la_boca="y")
            for _ in range(2)])
        detalles = voz.fijar_fonemas(c, [("cat", "cut"), ("cat", "cap")]).detalles
        self.assertEqual([d.fonema for d in detalles], por_separado)
        # Mas detalles que veces se fallo: el tercero repite la ultima lectura.
        c3 = voz.Correccion(resumen="Casi.", detalles=[
            voz.DetallePalabra(palabra="cat", fonema="t", sonido_que_falla="x", como_colocar_la_boca="y")
            for _ in range(3)])
        self.assertEqual([d.fonema for d in voz.fijar_fonemas(c3, [("cat", "cut"), ("cat", "cap")]).detalles],
                         por_separado + [por_separado[1]])


class IpaDeLaIA(unittest.TestCase):
    """e6, 14 sep (M6), en `lexicon`: la IPA que escribe el modelo tiene que ser IPA."""

    def test_solo_pasa_lo_que_es_una_transcripcion(self):
        import lexicon
        self.assertIsNone(lexicon._ipa_de_modelo("no sé, quizá"))
        self.assertIsNone(lexicon._ipa_de_modelo("cualquier cosa", "house"))
        self.assertIsNone(lexicon._ipa_de_modelo("HOUSE"))
        self.assertIsNone(lexicon._ipa_de_modelo("//"))
        self.assertEqual(lexicon._ipa_de_modelo("ˈhæp(ə)n"), "/ˈhæp(ə)n/")
        self.assertEqual(lexicon._ipa_de_modelo("/sɛt ˈɔf/", "set off"), "/sɛt ˈɔf/")
        self.assertEqual(lexicon._ipa_de_modelo("[tʰɒp]", "top"), "[tʰɒp]")
        self.assertEqual(lexicon._ipa_de_modelo("t͡ʃɪp", "chip"), "/t͡ʃɪp/")

    def test_la_palabra_tal_cual_se_escribe_no_es_ipa(self):
        """e6, ronda 2 (M6): _ipa_de_modelo("house", "house") daba "/house/"."""
        import lexicon
        self.assertIsNone(lexicon._ipa_de_modelo("house", "house"))
        self.assertIsNone(lexicon._ipa_de_modelo("/House/", "house"), "las mayusculas ya no pasaban")
        self.assertIsNone(lexicon._ipa_de_modelo("/set off/", "set off"))
        self.assertIsNone(lexicon._ipa_de_modelo("hello"), "sin palabra con que comparar, solo ASCII no vale")
        self.assertIsNone(lexicon._ipa_de_modelo("/houses/", "house"), "casi la palabra escrita (e6, ronda 3)")
        self.assertIsNone(lexicon._ipa_de_modelo("/colour/", "color"), "casi la palabra escrita (e6, ronda 3)")
        self.assertEqual(lexicon._ipa_de_modelo("/haus/", "house"), "/haus/", "ASCII que no es la ortografia pasa")
        self.assertEqual(lexicon._ipa_de_modelo("ˈhaʊs", "house"), "/ˈhaʊs/")


class HistorialRitmo(unittest.TestCase):
    """Parte 3: lo medido en cada intento, por frase, en la base del lector."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="literalevel_historial_ritmo_")
        self.addCleanup(self.tmp.cleanup)
        self.carpeta = Path(self.tmp.name)
        self.db = str(self.carpeta / "voz.db")
        self.medido = voz.medir_ritmo(voz.evaluar_pronunciacion(FRASE, FRASE), como_dict(LECTOR),
                                      como_dict(REFERENCIA), 1.0)

    def test_sin_medicion_no_se_guarda_nada(self):
        for ritmo in (None, {"medido": False, "palabras": [], "pausas": [], "tramos": []}):
            voz.registrar_ritmo(ritmo, FRASE, ruta=self.db)
        voz.registrar_ritmo(self.medido, "   ", ruta=self.db)
        self.assertEqual(voz.evolucion_ritmo(FRASE, ruta=self.db), [])

    def test_un_intento_medido_guarda_velocidad_pausas_y_tramos(self):
        voz.registrar_ritmo(self.medido, FRASE, ruta=self.db)
        filas = voz.evolucion_ritmo(FRASE, ruta=self.db)
        self.assertEqual(len(filas), 1)
        # 8 palabras de 0,00 a 3,32 s; una pausa de mas; los dos tramos por debajo del 90 %.
        self.assertEqual((filas[0]["palabras_por_segundo"], filas[0]["pausas_de_mas"],
                          filas[0]["tramos_a_acelerar"]), (2.41, 1, 2))
        self.assertTrue(filas[0]["fecha"])

    def test_evolucion_del_mas_antiguo_al_mas_reciente_por_frase_y_con_tope(self):
        for pausas in (3, 2, 1):
            ritmo = {**self.medido, "pausas": [{"de_mas": True}] * pausas}
            voz.registrar_ritmo(ritmo, FRASE, ruta=self.db)
        voz.registrar_ritmo(self.medido, "Another sentence entirely", ruta=self.db)
        self.assertEqual([f["pausas_de_mas"] for f in voz.evolucion_ritmo(FRASE, ruta=self.db)], [3, 2, 1])
        self.assertEqual([f["pausas_de_mas"] for f in voz.evolucion_ritmo(FRASE, n=2, ruta=self.db)], [2, 1],
                         "los dos ultimos, en orden")
        self.assertEqual(len(voz.evolucion_ritmo("Another sentence entirely", ruta=self.db)), 1)

    def test_sin_base_vacio_y_base_ilegible_avisa(self):
        self.assertEqual(voz.evolucion_ritmo(FRASE, ruta=str(self.carpeta / "no" / "existe.db")), [])
        self.assertFalse((self.carpeta / "no").exists(), "leer sin historial no crea carpetas")
        rota = self.carpeta / "rota.db"
        rota.write_bytes(b"esto no es una base de datos sqlite " * 50)
        with self.assertRaises(voz.HistorialIlegible):
            voz.evolucion_ritmo(FRASE, ruta=str(rota))
        voz.registrar_ritmo(self.medido, FRASE, ruta=str(rota))  # no lanza

    def test_practicar_guarda_el_intento_solo_con_guardar_fallos(self):
        grabacion = self.carpeta / "lector.webm"
        grabacion.write_bytes(b"audio del lector")
        cliente, llamadas = ClienteSimulado(), []
        with mock.patch.object(voz, "RUTA_AUDIO_GENERADO", self.carpeta / "audio"), \
             mock.patch.object(voz, "_cliente", lambda: cliente), \
             mock.patch.object(voz, "registrar_fallos", lambda *a, **k: None), \
             mock.patch.object(voz, "registrar_ritmo", lambda ritmo, frase, *a, **k: llamadas.append((ritmo, frase))):
            voz.practicar(str(grabacion), FRASE, guardar_fallos=False, nivel=1.0)
            self.assertEqual(llamadas, [])
            s = voz.practicar(str(grabacion), FRASE, guardar_fallos=True, nivel=1.0)
        self.assertEqual(len(llamadas), 1)
        self.assertIs(llamadas[0][0], s.ritmo)
        self.assertEqual(llamadas[0][1], FRASE)


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
