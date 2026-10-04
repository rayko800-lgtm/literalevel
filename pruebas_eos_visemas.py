"""Corrector de visemas de Eos (tools/eos_pronunciar/corregir_visemas.py): sin red ni modelos.

    python pruebas_eos_visemas.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools" / "eos_pronunciar"))
import corregir_visemas as cv  # noqa: E402

FPS = 60


def curvas_abiertas(segundos: float, jaw: float = 0.35) -> dict:
    n = int(segundos * FPS)
    return {"fps": FPS, "curvas": {
        "jawOpen": [jaw] * n, "mouthClose": [0.1] * n, "mouthPressLeft": [0.0] * n, "mouthPressRight": [0.0] * n,
        "mouthLowerDownLeft": [0.4] * n, "mouthFunnel": [0.3] * n, "mouthSmileLeft": [0.2] * n,
        "tongueOut": [0.6] * n, "tongueLeft": [0.3] * n, "tongueRight": [0.0] * n, "tongueTipUp": [0.5] * n,
    }}


def marco(t: float) -> int:
    return int(round(t * FPS))


class Cierre(unittest.TestCase):
    def test_m_aislada_cierra_todo_el_tramo(self):
        datos = curvas_abiertas(2.0)
        fon = [{"arpabet": "m", "t0": 0.5, "t1": 1.2, "aislado": True}]
        salida, informe = cv.corregir(datos, fon)
        c = salida["curvas"]
        self.assertEqual(informe["cierres"], 1)
        for t in (0.55, 0.8, 1.15):
            self.assertLessEqual(c["jawOpen"][marco(t)], 0.03, t)
            self.assertGreaterEqual(c["mouthClose"][marco(t)], 0.69, t)
            self.assertGreaterEqual(c["mouthPressLeft"][marco(t)], 0.34, t)
            self.assertLessEqual(c["mouthLowerDownLeft"][marco(t)], 0.06, t)
        # Fuera del tramo (más allá de las rampas) no se toca.
        for t in (0.2, 1.6):
            self.assertAlmostEqual(c["jawOpen"][marco(t)], 0.35, places=3)
            self.assertAlmostEqual(c["mouthLowerDownLeft"][marco(t)], 0.4, places=3)
        # La sonrisa no separa los labios: se queda.
        self.assertAlmostEqual(c["mouthSmileLeft"][marco(0.8)], 0.2, places=3)
        self.assertEqual(salida["visemas_corregidos"]["cierres"], 1)

    def test_p_aislada_cierra_antes_de_la_explosion(self):
        datos = curvas_abiertas(2.0)
        fon = [{"arpabet": "p", "t0": 1.0, "t1": 1.15, "aislado": True}]
        salida, _ = cv.corregir(datos, fon)
        jaw = salida["curvas"]["jawOpen"]
        self.assertLessEqual(jaw[marco(0.9)], 0.03)          # cerrada 100 ms antes
        self.assertLessEqual(jaw[marco(1.0)], 0.03)          # y en la explosión
        self.assertGreaterEqual(jaw[marco(1.12)], 0.3)       # ya suelta durante la aspiración
        self.assertAlmostEqual(jaw[marco(0.6)], 0.35, places=3)

    def test_b_en_palabra_suelta_antes_del_fin_del_fono(self):
        datos = curvas_abiertas(2.0)
        fon = [{"arpabet": "B", "t0": 0.60, "t1": 0.72, "aislado": False},
               {"arpabet": "EH1", "t0": 0.72, "t1": 0.85, "aislado": False}]
        salida, _ = cv.corregir(datos, cv.normalizar_fonemas(fon))
        jaw = salida["curvas"]["jawOpen"]
        self.assertLessEqual(jaw[marco(0.62)], 0.03)
        self.assertLessEqual(jaw[marco(0.68)], 0.03)
        self.assertGreaterEqual(jaw[marco(0.80)], 0.3)

    def test_sin_fonemas_solo_lengua(self):
        datos = curvas_abiertas(1.0)
        salida, informe = cv.corregir(datos)
        self.assertEqual(informe["cierres"], 0)
        self.assertEqual(informe["fonemas"], "ninguno")
        self.assertAlmostEqual(salida["curvas"]["jawOpen"][10], 0.35, places=3)
        self.assertEqual(max(salida["curvas"]["tongueLeft"]), 0.0)
        self.assertLessEqual(max(salida["curvas"]["tongueOut"]), cv.LENGUA_FUERA_MAX)


class Explosion(unittest.TestCase):
    def test_p_aislada_abre_de_golpe_tras_el_cierre(self):
        datos = curvas_abiertas(2.0, jaw=0.04)          # un /p/ solo: A2F apenas abre la boca tras el soplo
        datos["curvas"]["cheekPuff"] = [0.0] * len(datos["curvas"]["jawOpen"])
        datos["curvas"]["mouthUpperUpLeft"] = [0.0] * len(datos["curvas"]["jawOpen"])
        fon = [{"arpabet": "p", "t0": 1.0, "t1": 1.15, "aislado": True}]
        salida, informe = cv.corregir(datos, fon)
        c = salida["curvas"]
        tb = 1.0 + cv.TRAS_EXPLOSION_S
        self.assertEqual(informe["explosiones"], 1)
        self.assertLessEqual(c["jawOpen"][marco(tb - 0.03)], 0.03)            # cerrada hasta el soplo
        self.assertGreaterEqual(c["cheekPuff"][marco(tb - 0.04)], 0.2)        # carrillos hinchados antes
        self.assertGreaterEqual(c["jawOpen"][marco(tb + 0.05)], 0.2)          # se abre de golpe
        self.assertGreaterEqual(c["mouthLowerDownLeft"][marco(tb + 0.05)], 0.28)
        self.assertGreaterEqual(c["mouthUpperUpLeft"][marco(tb + 0.05)], 0.1)
        self.assertLessEqual(c["mouthClose"][marco(tb + 0.05)], 0.05)
        self.assertLessEqual(c["cheekPuff"][marco(tb + 0.06)], 0.02)          # y los carrillos se vacían
        self.assertAlmostEqual(c["jawOpen"][marco(tb + 0.5)], 0.04, places=2)  # luego, lo que diga A2F
        self.assertEqual(salida["visemas_corregidos"]["explosiones"], 1)

    def test_b_en_palabra_explota_menos_y_la_m_no(self):
        datos = curvas_abiertas(2.0, jaw=0.04)
        datos["curvas"]["cheekPuff"] = [0.0] * len(datos["curvas"]["jawOpen"])
        fon = cv.normalizar_fonemas([("B", 0.60, 0.72, False), ("AH0", 0.72, 0.80, False),
                                     ("M", 1.20, 1.40, False), ("AH0", 1.40, 1.50, False)])
        salida, informe = cv.corregir(datos, fon)
        c = salida["curvas"]
        tb = max(0.63, 0.72 - cv.SUELTA_ANTES_DEL_FIN_S)
        self.assertEqual(informe["explosiones"], 1)
        self.assertGreaterEqual(c["jawOpen"][marco(tb + 0.05)], 0.15)
        self.assertLess(c["jawOpen"][marco(tb + 0.05)], 0.2)
        self.assertGreaterEqual(c["cheekPuff"][marco(tb - 0.04)], 0.1)
        self.assertLess(c["cheekPuff"][marco(tb - 0.04)], 0.2)
        # la /m/ cierra y suelta suave: sin soplo
        self.assertLessEqual(c["jawOpen"][marco(1.3)], 0.03)
        self.assertLessEqual(c["jawOpen"][marco(1.48)], 0.05)
        self.assertLessEqual(max(c["cheekPuff"][marco(1.0):marco(1.6)]), 0.02)


class Lengua(unittest.TestCase):
    def test_lateral_a_cero_y_fuera_acotada_salvo_interdental(self):
        datos = curvas_abiertas(2.0)
        fon = [{"arpabet": "th", "t0": 0.5, "t1": 0.8, "aislado": True}]
        salida, informe = cv.corregir(datos, fon)
        c = salida["curvas"]
        self.assertEqual(max(c["tongueLeft"]), 0.0)
        self.assertEqual(informe["lengua"]["laterales_anuladas"], ["tongueLeft"])
        self.assertIn("tongueOut", informe["lengua"]["fuera_acotadas"])
        self.assertLessEqual(c["tongueOut"][marco(0.2)], cv.LENGUA_FUERA_MAX)
        self.assertLessEqual(c["tongueOut"][marco(1.5)], cv.LENGUA_FUERA_MAX)
        self.assertAlmostEqual(c["tongueOut"][marco(0.65)], cv.LENGUA_FUERA_INTERDENTAL, places=3)
        # Lo que no es lateral ni fuera no se toca.
        self.assertAlmostEqual(c["tongueTipUp"][marco(0.65)], 0.5, places=3)

    def test_sin_curvas_de_lengua_lo_dice(self):
        datos = curvas_abiertas(1.0)
        for k in list(datos["curvas"]):
            if k.startswith("tongue"):
                del datos["curvas"][k]
        _, informe = cv.corregir(datos)
        self.assertEqual(informe["lengua"]["curvas"], [])
        self.assertIn("visor", informe["lengua"]["nota"])


class Aislado(unittest.TestCase):
    def test_sin_bandera_se_deduce_por_el_hueco(self):
        # Como los curvas.json de generar_clips.py: tres /p/ sueltas y luego «pen».
        fon = cv.normalizar_fonemas([["p", 0.07, 0.24], ["p", 0.86, 1.08], ["p", 2.81, 2.852], ["eh", 2.852, 2.938]])
        self.assertEqual([f["aislado"] for f in fon], [True, True, False, True])
        # Con bandera explícita no se toca.
        fon = cv.normalizar_fonemas([{"arpabet": "p", "t0": 0.1, "t1": 0.3, "aislado": False}])
        self.assertFalse(fon[0]["aislado"])

    def test_p_suelta_sin_bandera_abre_con_el_soplo(self):
        datos = curvas_abiertas(2.0, jaw=0.04)
        salida, _ = cv.corregir(datos, cv.normalizar_fonemas([["p", 1.0, 1.17]]))
        jaw = salida["curvas"]["jawOpen"]
        self.assertLessEqual(jaw[marco(0.9)], 0.03)        # cerrada antes del soplo (t0 = 1,0)
        self.assertGreaterEqual(jaw[marco(1.06)], 0.2)     # y abierta 60 ms después, no 130 ms más tarde


class Fonemas(unittest.TestCase):
    def test_de_palabras_por_letras_sin_motor(self):
        # Sin los diccionarios del motor (o con una palabra que no esté), por letras.
        fon = cv.fonemas_de_palabras([["pen", 1.0, 1.3], ["lamb", 1.4, 1.8]])
        p = [f for f in fon if f["arpabet"] == "p"]
        self.assertEqual(len(p), 1)
        self.assertAlmostEqual(p[0]["t0"], 1.0)
        self.assertAlmostEqual(p[0]["t1"], 1.1)
        self.assertEqual([f["arpabet"] for f in fon if f["t0"] >= 1.4], ["x", "x", "m"])  # la b de lamb no suena

    def test_del_json_prefiere_guion(self):
        datos = {"fps": FPS, "curvas": {"jawOpen": [0.3] * 60},
                 "guion": {"fonemas": [("m", 0.1, 0.4, True)], "palabras": [["man", 0.1, 0.4]]}}
        fon, origen = cv.fonemas_del_json(datos)
        self.assertEqual(origen, "guion.fonemas")
        self.assertEqual(fon[0]["arpabet"], "m")
        self.assertTrue(fon[0]["aislado"])


class Archivo(unittest.TestCase):
    def test_idempotente_con_copia(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "ga_006d" / "curvas.json"
            ruta.parent.mkdir()
            datos = curvas_abiertas(1.0)
            datos["guion"] = {"acento": "ga", "simbolo": "m", "palabras": [["m", 0.2, 0.6]],
                              "fonemas": [{"arpabet": "m", "t0": 0.2, "t1": 0.6, "aislado": True}]}
            ruta.write_text(json.dumps(datos), encoding="utf-8")
            primero = cv.corregir_archivo(ruta)
            self.assertTrue((ruta.parent / cv.COPIA).exists())
            self.assertEqual(primero["cierres"], 1)
            segundo = cv.corregir_archivo(ruta)
            self.assertEqual(segundo["jawOpen_en_cierre_antes"], primero["jawOpen_en_cierre_antes"])
            self.assertLessEqual(json.loads(ruta.read_text(encoding="utf-8"))["curvas"]["jawOpen"][marco(0.4)], 0.03)
            self.assertEqual(json.loads((ruta.parent / cv.COPIA).read_text(encoding="utf-8"))["curvas"]["jawOpen"][marco(0.4)], 0.35)


if __name__ == "__main__":
    unittest.main(verbosity=2)
