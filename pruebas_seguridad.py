"""Regresiones de seguridad, cuentas sintéticas, sin claves reales ni red."""
import concurrent.futures
import json
import os
import secrets
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent / "app"))
os.environ["LITERALEVEL_SIN_CLAVES"] = "1"
os.environ["LITERALEVEL_PRECARGA"] = "0"
os.environ["SPACE_ID"] = "pruebas/seguridad"
_inicial = tempfile.TemporaryDirectory()
os.environ["LITERALEVEL_DATOS"] = _inicial.name
from fastapi import HTTPException
from fastapi.testclient import TestClient
import api
import config
import cuentas
import lexicon
import seguridad as s
import ui


def consumir_proceso(datos):
    base, codigo = datos
    os.environ["LITERALEVEL_DATOS"] = base
    os.environ["LITERALEVEL_CUENTAS"] = "auditoria:fixture-solo-prueba:2"
    return cuentas.consumir(Path(base), codigo)[0]


class Seguridad(unittest.TestCase):
    def test_arranque_gradio_real_con_interfaz_cerrada(self):
        import socket
        import gradio as gr
        import httpx
        with socket.socket() as reserva:
            reserva.bind(("127.0.0.1", 0))
            puerto = reserva.getsockname()[1]
        with gr.Blocks(analytics_enabled=False) as demo:
            gr.Textbox()
        try:
            demo.launch(server_name="127.0.0.1", server_port=puerto, ssr_mode=False,
                        app_kwargs=api.para_gradio(), prevent_thread_lock=True, quiet=True,
                        share=False)
            base = f"http://127.0.0.1:{puerto}"
            self.assertEqual(httpx.get(base + "/api/salud").json()["api"], api.VERSION)
            self.assertEqual(httpx.get(base + "/config").status_code, 404)
            self.assertEqual(httpx.get(base + "/gradio_api/info").status_code, 404)
        finally:
            demo.close()

    def test_metadatos_audio_privados_y_capacidad_trabajador(self):
        nombre = "auditoria-privada.mp3"
        with s.operacion(self.p): s.permitir_recurso("audio:" + nombre)
        r = self.c.get("/api/lectura/ipa", headers=self.guest, params={"texto": "cat", "audio": nombre})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.c.get("/api/lectura/ipa", headers=self.auth, params={"texto": "cat", "audio": nombre}).status_code, 200)
        cap = s.recurso_para_trabajador("audio:" + nombre)
        s.validar_recurso("audio:" + nombre, cap)
        with self.assertRaises(HTTPException): s.validar_recurso("audio:otro.mp3", cap)
        self.assertEqual(self.c.get("/api/eos/cola", headers=self.guest).status_code, 403)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["LITERALEVEL_DATOS"] = self.tmp.name
        ui.BASE_DATOS_LECTOR = Path(self.tmp.name)
        self.clave = secrets.token_urlsafe(20)
        os.environ["LITERALEVEL_CUENTAS"] = f"auditora:{self.clave}:40,auditorb:{self.clave}:40"
        self.c = TestClient(api.app, raise_server_exceptions=False)
        self.guest = {"X-Lector": "visitante-aleatorio-1234567890"}
        self.token = self.login("auditora")
        self.p = s.resolver(self.token)
        self.auth = {**self.guest, "Authorization": "Bearer " + self.token}

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def login(self, nombre):
        r = self.c.post("/api/entrar", headers=self.guest, json={"usuario": nombre, "clave": self.clave})
        self.assertEqual(r.status_code, 200, r.text[:80])
        return r.json()["token"]

    def test_login_xlector_no_autentica(self):
        self.assertTrue(self.c.get("/api/entrada", headers=self.auth).json()["dentro"])
        self.assertFalse(self.c.get("/api/entrada", headers=self.guest).json()["dentro"])

    def test_sesion_caduca(self):
        with s.transaccion() as db:
            db.execute("UPDATE sesiones SET expira=0")
        self.assertEqual(self.c.get("/api/perfil", headers=self.auth).status_code, 401)

    def test_salir_revoca(self):
        self.assertEqual(self.c.post("/api/salir", headers=self.auth).status_code, 200)
        self.assertEqual(self.c.get("/api/perfil", headers=self.auth).status_code, 401)

    def test_clave_cambiada_revoca_todos(self):
        otra = self.login("auditora")
        nueva = secrets.token_urlsafe(20)
        r = self.c.post("/api/cuenta/clave", headers=self.auth, json={"actual": self.clave, "nueva": nueva})
        self.assertEqual(r.status_code, 200)
        for token in (self.token, otra):
            with self.assertRaises(HTTPException): s.resolver(token)
        r = self.c.post("/api/entrar", headers=self.guest, json={"usuario": "auditora", "clave": self.clave})
        self.assertEqual(r.status_code, 401)
        r = self.c.post("/api/entrar", headers=self.guest, json={"usuario": "auditora", "clave": nueva})
        self.assertEqual(r.status_code, 200)

    def test_cambiar_clave_conserva_este_dispositivo(self):
        # Miguel (demo, 4 oct): cambiar la contraseña no debe echar al que la cambia.
        # El token nuevo de la respuesta sirve; el viejo de este mismo dispositivo, no.
        r = self.c.post("/api/cuenta/clave", headers=self.auth,
                        json={"actual": self.clave, "nueva": secrets.token_urlsafe(20)})
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertTrue(cuerpo["dentro"])
        self.assertEqual(cuerpo["nombre"], "auditora")
        self.assertEqual(cuerpo["expira_en"], s.SESION_SEGUNDOS)
        self.assertNotEqual(cuerpo["token"], self.token)
        nuevo = {**self.guest, "Authorization": "Bearer " + cuerpo["token"]}
        self.assertTrue(self.c.get("/api/entrada", headers=nuevo).json()["dentro"])
        self.assertEqual(self.c.get("/api/perfil", headers=self.auth).status_code, 401)

    def test_clave_actual_incorrecta(self):
        r = self.c.post("/api/cuenta/clave", headers=self.auth, json={"actual": "incorrecta", "nueva": secrets.token_urlsafe(20)})
        self.assertEqual(r.status_code, 401)
        self.assertIsNotNone(s.resolver(self.token))

    def test_rotacion_entorno_revoca(self):
        nueva = secrets.token_urlsafe(20)
        os.environ["LITERALEVEL_CUENTAS"] = f"auditora:{nueva}:40,auditorb:{self.clave}:40"
        with self.assertRaises(HTTPException): s.resolver(self.token)
        self.clave = nueva
        self.assertTrue(self.login("auditora"))

    def test_quitar_cuenta_revoca(self):
        os.environ["LITERALEVEL_CUENTAS"] = f"auditorb:{self.clave}:40"
        with self.assertRaises(HTTPException): s.resolver(self.token)

    def test_recuperacion_admin_reautentica(self):
        datos = {"usuario": "auditorb", "actual": self.clave}
        self.assertEqual(self.c.post("/api/admin/recuperacion", headers=self.auth, json=datos).status_code, 403)
        with patch.dict(os.environ, {"LITERALEVEL_ADMIN_USUARIOS": "auditora"}):
            r = self.c.post("/api/admin/recuperacion", headers=self.auth, json={**datos, "actual": "erronea"})
            self.assertEqual(r.status_code, 401)
            r = self.c.post("/api/admin/recuperacion", headers=self.auth, json=datos)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["expira_en"], 900)
            s.recuperar(r.json()["codigo"], secrets.token_urlsafe(20))

    def test_recuperacion_un_uso(self):
        codigo = s.emitir_recuperacion("auditora")
        nueva = secrets.token_urlsafe(20)
        r = self.c.post("/api/recuperar", headers=self.guest, json={"codigo": codigo, "nueva": nueva})
        self.assertEqual(r.status_code, 200)
        r = self.c.post("/api/recuperar", headers=self.guest, json={"codigo": codigo, "nueva": nueva})
        self.assertEqual(r.status_code, 401)
        with self.assertRaises(HTTPException): s.resolver(self.token)

    def test_recuperacion_caduca_y_reemision(self):
        vieja = s.emitir_recuperacion("auditora")
        nueva = s.emitir_recuperacion("auditora")
        with self.assertRaises(HTTPException): s.recuperar(vieja, secrets.token_urlsafe(20))
        with s.transaccion() as db: db.execute("UPDATE recuperaciones SET expira=0")
        with self.assertRaises(HTTPException): s.recuperar(nueva, secrets.token_urlsafe(20))

    def test_datos_cuentas_aislados(self):
        (ui.BASE_DATOS_LECTOR / "cuentas" / "auditora").mkdir(parents=True)
        (ui.BASE_DATOS_LECTOR / "cuentas" / "auditora" / "perfil.json").write_text(json.dumps({
            "nivel": 1.2, "banda": "B2", "origen": "cuestionario", "creado": "2026-10-01", "nombre": "Prueba A"}))
        self.assertIsNotNone(self.c.get("/api/perfil", headers=self.auth).json()["perfil"])
        b = {**self.guest, "Authorization": "Bearer " + self.login("auditorb")}
        self.assertIsNone(self.c.get("/api/perfil", headers=b).json()["perfil"])
        self.assertIsNone(self.c.get("/api/perfil", headers=self.guest).json()["perfil"])
        cambiada = {**self.auth, "X-Lector": "otro-identificador-123456789"}
        self.assertIsNotNone(self.c.get("/api/perfil", headers=cambiada).json()["perfil"])

    def test_ataduras_antiguas_no_autorizan(self):
        ui._ATADURAS = {self.guest["X-Lector"]: "auditora"}
        self.assertFalse(self.c.get("/api/entrada", headers=self.guest).json()["dentro"])
        self.assertIsNone(self.c.get("/api/perfil", headers=self.guest).json()["perfil"])

    def test_no_admin_publico_ni_gradio(self):
        for ruta in ("/gradio_api/queue/join", "/gradio_api/file=/data/seguridad.sqlite3", "/docs", "/openapi.json", "/config"):
            self.assertEqual(self.c.get(ruta).status_code, 404)
        self.assertEqual(self.c.post("/api/admin/recuperar", headers=self.auth, json={}).status_code, 404)
        self.assertEqual(self.c.post("/api/registro", headers=self.guest, json={}).status_code, 404)

    def test_claves_no_persistidas(self):
        datos = Path(self.tmp.name, "seguridad.sqlite3").read_bytes()
        self.assertNotIn(self.clave.encode(), datos)
        self.assertNotIn(self.token.encode(), datos)

    def test_freno_login_persistente(self):
        for _ in range(14):
            self.c.post("/api/entrar", headers=self.guest, json={"usuario": "desconocida", "clave": "incorrecta"})
        self.assertEqual(self.c.post("/api/entrar", headers={"X-Lector": "otro-id-1234567890123"},
            json={"usuario": "desconocida", "clave": "incorrecta"}).status_code, 429)

    def test_cors(self):
        self.assertEqual(self.c.get("/api/salud", headers={"Origin": "https://malicioso.hf.space"}).status_code, 403)
        r = self.c.options("/api/entrar", headers={"Origin": "https://pleyade-app.vercel.app", "Access-Control-Request-Headers": "authorization,x-lector"})
        self.assertEqual(r.status_code, 204)
        self.assertIn("Authorization", r.headers["access-control-allow-headers"])

    def test_no_eco_clave_validation(self):
        r = self.c.post("/api/entrar", headers=self.guest, json={"clave": self.clave * 30})
        self.assertEqual(r.status_code, 422)
        self.assertNotIn(self.clave, r.text)

    def test_limite_cuerpo(self):
        r = self.c.post("/api/entrar", headers={**self.guest, "Content-Type": "application/json"}, content=b"x" * 140000)
        self.assertEqual(r.status_code, 413)

    def test_live_cerrado(self):
        for ruta in ("/api/gpt-live/sesion", "/api/lectura/vivo"):
            self.assertEqual(self.c.post(ruta, headers=self.auth, json={"sdp": "prueba"}).status_code, 503)

    def test_proveedor_requiere_contexto(self):
        llamadas = []
        cliente = self.proveedor(llamadas)
        with self.assertRaises(HTTPException): cliente.responses.parse(model="gpt-5", input="prueba")
        self.assertEqual(llamadas, [])

    def proveedor(self, llamadas):
        f = lambda **kw: llamadas.append(kw)
        raw = SimpleNamespace(responses=SimpleNamespace(parse=f), chat=SimpleNamespace(completions=SimpleNamespace(parse=f)),
            audio=SimpleNamespace(speech=SimpleNamespace(create=f), transcriptions=SimpleNamespace(create=f)))
        return s.ClienteProtegido(raw)

    def test_presupuesto_total_no_se_devuelve_en_error(self):
        with patch.dict(os.environ, {"LITERALEVEL_PRESUPUESTO_TOTAL_CENTAVOS": "25"}):
            with s.operacion(self.p):
                s.reservar(25, "texto")
                with self.assertRaises(HTTPException): s.reservar(1, "texto")
        with s.transaccion() as db:
            self.assertEqual(db.execute("SELECT sum(centavos) FROM cargos").fetchone()[0], 25)

    def test_presupuesto_diario_y_config_invalida(self):
        for valor in ("0", "invalido"):
            with patch.dict(os.environ, {"LITERALEVEL_PRESUPUESTO_DIA_CENTAVOS": valor}):
                with s.operacion(self.p):
                    with self.assertRaises(HTTPException): s.reservar(1, "texto")

    def test_limite_tokens_modelos_y_texto(self):
        llamadas = []
        cliente = self.proveedor(llamadas)
        with s.operacion(self.p):
            cliente.responses.parse(model="gpt-5", input="prueba", max_output_tokens=999999)
            self.assertEqual(llamadas[0]["max_output_tokens"], 2048)
            self.assertFalse(llamadas[0]["store"])
            for kw in ({"model": "modelo-no-autorizado"}, {"model": "gpt-5", "tools": []}, {"model": "gpt-5", "input": "x" * 40000}):
                with self.assertRaises(HTTPException): cliente.responses.parse(**kw)
        self.assertEqual(len(llamadas), 1)

    def test_maximo_6_llamadas_minuto(self):
        # El tope por minuto es configurable desde el 4 oct 2026; la regresión fija 6.
        with patch.dict(os.environ, {"LITERALEVEL_LLAMADAS_MINUTO": "6"}), s.operacion(self.p):
            for _ in range(6): s.reservar(1, "texto")
            with self.assertRaises(HTTPException): s.reservar(1, "texto")

    def test_topes_por_defecto_admiten_una_correccion(self):
        # Una corrección de pronunciación encadena whisper, gpt-4o-mini y un tts-1 por
        # frase y por palabra fallada: diez llamadas seguidas en el mismo minuto no
        # pueden dar 429 con los valores por defecto (Miguel, demo del 4 oct 2026).
        for variable in ("LITERALEVEL_LLAMADAS_MINUTO", "LITERALEVEL_LLAMADAS_HORA",
                         "LITERALEVEL_LLAMADAS_DIA", "LITERALEVEL_LLAMADAS_TOTAL"):
            self.assertNotIn(variable, os.environ)
        with s.operacion(self.p):
            for _ in range(10): s.reservar(1, "texto")
        with patch.dict(os.environ, {"LITERALEVEL_LLAMADAS_DIA": "invalido"}), s.operacion(self.p):
            with self.assertRaises(HTTPException): s.reservar(1, "texto")

    def consultor_con_hilos(self, llamadas):
        """Un `ConsultorLexico` REAL (hilos, caché y captura de errores) sobre un Kaikki
        de una palabra, sin spaCy ni MiniLM, con el proveedor doblado tras
        `ClienteProtegido`. Es el camino de `/api/palabra` que falló en la demo."""
        ruta = Path(self.tmp.name, "kaikki_fixture.db")
        db = sqlite3.connect(ruta)
        db.execute("CREATE TABLE entradas (palabra TEXT, pos TEXT, sentidos TEXT, ipa_uk TEXT, "
                   "ipa_us TEXT, audio_uk TEXT, audio_us TEXT)")
        db.execute("INSERT INTO entradas VALUES (?,?,?,?,?,?,?)",
                   ("house", "noun", json.dumps([{"glosa": "A structure built for habitation.", "tags": []}]),
                    "/haʊs/", "/haʊs/", "https://upload.wikimedia.org/house.ogg", None))
        db.commit()
        db.close()
        c = lexicon.ConsultorLexico(ruta_diccionario=ruta, ruta_cache=Path(self.tmp.name, "lexicon.db"))

        def parse(**kw):
            llamadas.append(kw)
            return SimpleNamespace(output_parsed=SimpleNamespace(model_dump=lambda: {
                "traduccion": "casa", "acepcion_usada": "",
                "definicion_contextual": "Aquí es el edificio donde vive la familia.",
                "explicacion_gramatical": "Sustantivo contable.",
                "explicacion_adaptada": "Un lugar para vivir.",
                "ejemplo_simplificado": "The house is big."}))
        f = lambda **kw: llamadas.append(kw)
        raw = SimpleNamespace(responses=SimpleNamespace(parse=parse), chat=SimpleNamespace(completions=SimpleNamespace(parse=f)),
            audio=SimpleNamespace(speech=SimpleNamespace(create=f), transcriptions=SimpleNamespace(create=f)))
        c._cliente_openai = s.ClienteProtegido(raw)
        return c

    def palabra_completa(self, llamadas):
        c = self.consultor_con_hilos(llamadas)
        with patch.object(lexicon, "_resolver_lema_y_categoria", lambda oracion, palabra: ("house", "house", "noun", "NOUN")), \
             patch.object(lexicon, "_elegir_sentido", lambda oracion, pares: (pares[0][1], 0.9, []) if pares else (None, None, [])), \
             patch.object(lexicon, "_fonetica_de_la_forma", lambda *a: ("/haʊs/", "/haʊs/", "https://upload.wikimedia.org/house.ogg", None)), \
             patch.object(ui, "consultor", lambda: c), patch.object(config, "falta", lambda: []):
            return self.c.post("/api/palabra", headers=self.auth,
                               json={"palabra": "house", "oracion": "The house was quiet.", "etapa": "completa"})

    def test_palabra_explica_desde_el_hilo_con_la_cuenta(self):
        # Miguel (demo, 4 oct): con sesión, la explicación de la palabra nunca llegaba.
        # `lexicon` pide a OpenAI desde un ThreadPoolExecutor, cuyos hilos nacían sin
        # `seguridad.CONTEXTO`, y `ClienteProtegido` negaba con 403.
        llamadas = []
        r = self.palabra_completa(llamadas)
        self.assertEqual(r.status_code, 200, r.text[:200])
        cuerpo = r.json()
        self.assertEqual(cuerpo["definicion_contextual"], "Aquí es el edificio donde vive la familia.")
        self.assertIsNone(cuerpo["motivo_sin_explicacion"])
        self.assertEqual(len(llamadas), 1)
        self.assertEqual(llamadas[0]["model"], "gpt-5")
        self.assertEqual(self.c.get("/api/entrada", headers=self.auth).json()["restantes"], 39)
        with s.transaccion() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM cargos WHERE nombre='auditora'").fetchone()[0], 1)

    def test_palabra_con_tope_devuelve_ficha_y_motivo_llano(self):
        # Un tope de `seguridad` no es un 503 del diccionario: la ficha sale, el motivo va
        # en texto llano (sin «HTTPException») y el uso cobrado se devuelve.
        llamadas = []
        with patch.dict(os.environ, {"LITERALEVEL_LLAMADAS_MINUTO": "0"}):
            r = self.palabra_completa(llamadas)
        self.assertEqual(r.status_code, 200, r.text[:200])
        cuerpo = r.json()
        self.assertEqual(cuerpo["sentido"], "A structure built for habitation.")
        self.assertIsNone(cuerpo["definicion_contextual"])
        self.assertIn("Has alcanzado el límite de llamadas de pago de tu cuenta.", cuerpo["motivo_sin_explicacion"])
        self.assertIn(cuerpo["motivo_sin_explicacion"], cuerpo["avisos"])
        self.assertNotIn("HTTPException", json.dumps(cuerpo, ensure_ascii=False))
        self.assertEqual(llamadas, [])
        self.assertEqual(self.c.get("/api/entrada", headers=self.auth).json()["restantes"], 40)

    def test_salida_revoca_entre_llamadas(self):
        with s.operacion(self.p):
            s.salir(self.token)
            with self.assertRaises(HTTPException): s.reservar(1, "texto")

    def test_concurrencia_cuenta_y_global(self):
        b = s.resolver(self.login("auditorb"))
        with s.operacion(self.p):
            with self.assertRaises(HTTPException):
                with s.operacion(self.p): pass
            with s.operacion(b):
                with self.assertRaises(HTTPException):
                    with s.operacion(s.Principal("tercera", 40, "")): pass

    def test_cuota_atomica_hilos(self):
        cuenta = cuentas.Cuenta("auditora", 2)
        with concurrent.futures.ThreadPoolExecutor(20) as pool:
            resultados = list(pool.map(lambda _: s.consumir(Path(self.tmp.name), cuenta)[0], range(20)))
        self.assertEqual(sum(resultados), 2)
        self.assertEqual(s.usos(Path(self.tmp.name), "auditora"), 2)

    def test_cuota_atomica_procesos(self):
        import subprocess
        programa = """import sys; sys.path.insert(0,'app')
import seguridad as s
from types import SimpleNamespace
import config
print(sum(s.consumir(config.dir_datos(),SimpleNamespace(nombre='auditora',tope=2))[0] for _ in range(5)))
"""
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            resultados = list(pool.map(lambda _: subprocess.run([sys.executable, "-c", programa],
                capture_output=True, text=True, check=True).stdout.strip(), range(4)))
        self.assertEqual(sum(map(int, resultados)), 2)
        self.assertEqual(s.usos(Path(self.tmp.name), "auditora"), 2)

    def test_migracion_contador(self):
        with s.transaccion() as db: db.execute("DELETE FROM acciones")
        Path(self.tmp.name, "uso_openai.json").write_text('{"auditora":39}')
        self.assertEqual(s.usos(Path(self.tmp.name), "auditora"), 39)
        self.assertTrue(s.consumir(Path(self.tmp.name), cuentas.Cuenta("auditora", 40))[0])
        self.assertFalse(s.consumir(Path(self.tmp.name), cuentas.Cuenta("auditora", 40))[0])

    def test_corrupcion_contador_cierra(self):
        with s.transaccion() as db: db.execute("DELETE FROM acciones")
        Path(self.tmp.name, "uso_openai.json").write_text('invalido')
        with self.assertRaises(HTTPException): s.usos(Path(self.tmp.name), "auditora")

    def test_disco_no_escribible_cierra(self):
        with patch("seguridad.sqlite3.connect", side_effect=__import__('sqlite3').OperationalError("prueba")):
            with self.assertRaises(HTTPException): s.reservar(1, "texto")

    def test_sin_cuentas_no_barra_libre(self):
        with patch.dict(os.environ, {"LITERALEVEL_CUENTAS": ""}):
            self.assertFalse(cuentas.consumir(Path(self.tmp.name), None)[0])

    def test_archivos_privados_expiran_y_logout(self):
        with s.operacion(self.p): acceso = s.permitir_recurso("audio:prueba.mp3")
        s.validar_recurso("audio:prueba.mp3", acceso)
        with self.assertRaises(HTTPException): s.validar_recurso("audio:otro.mp3", acceso)
        s.salir(self.token)
        with self.assertRaises(HTTPException): s.validar_recurso("audio:prueba.mp3", acceso)

    def test_enlaces_privados_duran_lo_configurado(self):
        # Miguel (4 oct): pide una corrección, lee 20 minutos y los enlaces de audio y
        # de Eos daban 403 (15 min fijos). Cuatro horas por defecto, configurables;
        # la caducidad y la revocación siguen vigentes.
        antes = time.time()
        with s.operacion(self.p): acceso = s.permitir_recurso("audio:demo.mp3")
        cap = s.recurso_para_trabajador("audio:demo.mp3")
        with s.transaccion() as db:
            vidas = [f[0] - antes for f in db.execute("SELECT expira FROM recursos ORDER BY expira")]
        self.assertEqual(len(vidas), 2)
        for vida in vidas:
            self.assertGreater(vida, 4 * 3600 - 5)
            self.assertLess(vida, 4 * 3600 + 5)
        with patch.dict(os.environ, {"LITERALEVEL_RECURSO_SEGUNDOS": "0"}):
            with s.operacion(self.p): caducado = s.permitir_recurso("audio:demo.mp3")
            with self.assertRaises(HTTPException): s.validar_recurso("audio:demo.mp3", caducado)
        s.validar_recurso("audio:demo.mp3", acceso)
        s.validar_recurso("audio:demo.mp3", cap)
        with s.transaccion() as db: db.execute("UPDATE recursos SET expira=0")
        for token in (acceso, cap):
            with self.assertRaises(HTTPException): s.validar_recurso("audio:demo.mp3", token)

    def test_audio_no_valido_sin_gasto(self):
        f = Path(self.tmp.name, "audio.webm")
        f.write_bytes(b"falso" * 1000)
        llamadas = []
        with s.operacion(self.p), f.open("rb") as archivo:
            with self.assertRaises(HTTPException): self.proveedor(llamadas).audio.transcriptions.create(model="whisper-1", file=archivo)
        self.assertEqual(llamadas, [])

    def test_audio_no_lee_archivos_referenciados(self):
        import wave
        propia = Path(self.tmp.name) / "referencia.wav"
        with wave.open(str(propia), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
            w.writeframes(b"\0" * 32000)
        lista = Path(self.tmp.name) / "lista.wav"
        lista.write_text("ffconcat version 1.0\nfile 'referencia.wav'\n", encoding="utf-8")
        with lista.open("rb") as archivo:
            with self.assertRaises(HTTPException) as error: s.audio_acotado(archivo)
        self.assertEqual(error.exception.status_code, 422)

    def test_audio_duracion_real(self):
        import wave
        f = Path(self.tmp.name, "audio.wav")
        for segundos in (1, 181):
            with wave.open(str(f), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
                w.writeframes(b"\0" * (segundos * 32000))
            with f.open("rb") as archivo:
                if segundos == 1: self.assertTrue(s.audio_acotado(archivo)[1].startswith(b"RIFF"))
                else:
                    with self.assertRaises(HTTPException): s.audio_acotado(archivo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
