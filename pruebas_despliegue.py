"""Guardas del despliegue, sin token, red ni SDK de Hugging Face.

    python -B -X utf8 pruebas_despliegue.py
"""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from tools import desplegar_app as despliegue


class DespliegueSeguro(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix="ll_despliegue_prueba_")
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        (self.raiz / "app").mkdir()
        (self.raiz / "app/api.py").write_text("api = 1\n", encoding="utf-8")
        (self.raiz / "app/catalogo.py").write_text("catalogo = 1\n", encoding="utf-8")
        self.git("init", "-q")
        self.git("config", "user.name", "Prueba offline")
        self.git("config", "user.email", "prueba@example.invalid")
        self.git("config", "core.autocrlf", "false")
        self.git("add", "app/api.py", "app/catalogo.py")
        self.git("commit", "-qm", "base de prueba")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.raiz,
                              capture_output=True, check=True)

    def test_api_en_lista_y_seleccion_exacta(self):
        self.assertIn("app/api.py", despliegue.seleccionar())
        self.assertEqual(despliegue.seleccionar(["app\\api.py", "app/api.py"]), ["app/api.py"])
        for ruta in (".env", "CLAVES.txt", "../app/api.py", "app/../app/api.py",
                     "/app/api.py", "C:/app/api.py", "app", "app/*.py", "desconocido.py"):
            with self.subTest(ruta=ruta), self.assertRaises(SystemExit):
                despliegue.seleccionar([ruta])
        with self.assertRaises(SystemExit):
            despliegue.seleccionar([])

    def test_dirty_no_seleccionado_permitido(self):
        (self.raiz / "app/catalogo.py").write_text("catalogo = 2\n", encoding="utf-8")
        despliegue.exigir_confirmados(["app/api.py"], self.raiz)
        with self.assertRaises(SystemExit):
            despliegue.exigir_confirmados(["app/api.py", "app/catalogo.py"], self.raiz)

    def test_dirty_seleccionado_bloqueado_sin_o_con_stage(self):
        (self.raiz / "app/api.py").write_text("api = 2\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            despliegue.exigir_confirmados(["app/api.py"], self.raiz)
        self.git("add", "app/api.py")
        with self.assertRaises(SystemExit):
            despliegue.exigir_confirmados(["app/api.py"], self.raiz)

    def test_no_versionado_o_borrado_bloqueado(self):
        (self.raiz / "app/voz.py").write_text("voz = 1\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            despliegue.exigir_confirmados(["app/voz.py"], self.raiz)
        (self.raiz / "app/api.py").unlink()
        with self.assertRaises(SystemExit):
            despliegue.exigir_confirmados(["app/api.py"], self.raiz)

    def test_dirty_aborta_antes_del_token(self):
        (self.raiz / "app/api.py").write_text("api = 2\n", encoding="utf-8")
        with patch.object(despliegue, "RAIZ", str(self.raiz)), \
                patch.object(sys, "argv", ["desplegar_app.py", "--solo", "app/api.py"]), \
                patch.object(despliegue, "token") as token, self.assertRaises(SystemExit):
            despliegue.main()
        token.assert_not_called()

    def test_seco_selecciona_sin_subir_aunque_dirty(self):
        (self.raiz / "app/api.py").write_text("api = 2\n", encoding="utf-8")
        api = Mock()
        api.list_repo_tree.return_value = []
        sdk = types.SimpleNamespace(HfApi=Mock(return_value=api), CommitOperationAdd=Mock())
        salida = io.StringIO()
        with patch.dict(sys.modules, {"huggingface_hub": sdk}), \
                patch.object(despliegue, "RAIZ", str(self.raiz)), \
                patch.object(despliegue, "token", return_value="token-simulado"), \
                patch.object(despliegue, "quien", return_value=("prueba", "write")), \
                patch.object(sys, "argv", ["desplegar_app.py", "--solo", "app/api.py", "--seco"]), \
                contextlib.redirect_stdout(salida):
            despliegue.main()
        api.create_commit.assert_not_called()
        self.assertIn("A subir (1)", salida.getvalue())
        self.assertIn("--seco", salida.getvalue())

    def test_commit_simulado_solo_lleva_seleccion(self):
        (self.raiz / "app/catalogo.py").write_text("catalogo = 2\n", encoding="utf-8")
        api, operacion = Mock(), Mock()
        api.list_repo_tree.return_value = []
        sdk = types.SimpleNamespace(HfApi=Mock(return_value=api), CommitOperationAdd=operacion)
        with patch.dict(sys.modules, {"huggingface_hub": sdk}), \
                patch.object(despliegue, "RAIZ", str(self.raiz)), \
                patch.object(despliegue, "token", return_value="token-simulado"), \
                patch.object(despliegue, "quien", return_value=("prueba", "write")), \
                patch.object(sys, "argv", ["desplegar_app.py", "--solo", "app/api.py"]), \
                contextlib.redirect_stdout(io.StringIO()):
            despliegue.main()
        # Los bytes del commit con el texto en LF, no los del disco (en Windows,
        # write_text deja CRLF): asi el Space no vuelve a quedar mezclado.
        operacion.assert_called_once_with(path_in_repo="app/api.py", path_or_fileobj=b"api = 1\n")
        api.create_commit.assert_called_once()
        self.assertEqual(api.create_commit.call_args.kwargs["parent_commit"], api.repo_info.return_value.sha)
        self.assertEqual(api.list_repo_tree.call_args.kwargs["revision"], api.repo_info.return_value.sha)

    def test_edicion_durante_comparacion_bloquea_commit(self):
        api = Mock()

        def remoto(*a, **k):
            (self.raiz / "app/api.py").write_text("api = 2\n", encoding="utf-8")
            return []

        api.list_repo_tree.side_effect = remoto
        sdk = types.SimpleNamespace(HfApi=Mock(return_value=api), CommitOperationAdd=Mock())
        with patch.dict(sys.modules, {"huggingface_hub": sdk}), \
                patch.object(despliegue, "RAIZ", str(self.raiz)), \
                patch.object(despliegue, "token", return_value="token-simulado"), \
                patch.object(despliegue, "quien", return_value=("prueba", "write")), \
                patch.object(sys, "argv", ["desplegar_app.py", "--solo", "app/api.py"]), \
                contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            despliegue.main()
        api.create_commit.assert_not_called()

    def test_lfs_avanza_parent_commit(self):
        ruta = next(r for r in despliegue.LISTA_BLANCA if r.endswith(".mp3"))
        archivo = self.raiz / ruta
        archivo.parent.mkdir(parents=True)
        archivo.write_bytes(b"audio de prueba offline")
        self.git("add", ruta)
        self.git("commit", "-qm", "audio de prueba")
        api = Mock()
        api.repo_info.return_value.sha = "revision-base"
        api.list_repo_tree.return_value = []
        api.create_commit.side_effect = [types.SimpleNamespace(oid="revision-lfs"),
                                        types.SimpleNamespace(oid="revision-archivos")]
        sdk = types.SimpleNamespace(HfApi=Mock(return_value=api), CommitOperationAdd=Mock())
        with patch.dict(sys.modules, {"huggingface_hub": sdk}), \
                patch.object(despliegue, "RAIZ", str(self.raiz)), \
                patch.object(despliegue, "token", return_value="token-simulado"), \
                patch.object(despliegue, "quien", return_value=("prueba", "write")), \
                patch.object(despliegue, "reglas_lfs_que_faltan", return_value=(["*.mp3 filter=lfs"], "")), \
                patch.object(sys, "argv", ["desplegar_app.py", "--solo", ruta]), \
                contextlib.redirect_stdout(io.StringIO()):
            despliegue.main()
        self.assertEqual([c.kwargs["parent_commit"] for c in api.create_commit.call_args_list],
                         ["revision-base", "revision-lfs"])

    def test_escanea_bytes_que_recibe_el_sdk(self):
        """Desde el 14 sep 2026 los bytes salen del commit, no del disco: una
        credencial en el commit se bloquea aunque el disco este limpio, y sin
        que el mensaje la repita."""
        falsa = "sk-" + "x" * 24
        (self.raiz / "app/api.py").write_text("clave = '" + falsa + "'\n", encoding="utf-8")
        self.git("add", "app/api.py")
        self.git("commit", "-qm", "credencial de prueba")
        (self.raiz / "app/api.py").write_text("api = 1\n", encoding="utf-8")
        api = Mock()
        api.list_repo_tree.return_value = []
        sdk = types.SimpleNamespace(HfApi=Mock(return_value=api), CommitOperationAdd=Mock())
        with patch.dict(sys.modules, {"huggingface_hub": sdk}), \
                patch.object(despliegue, "RAIZ", str(self.raiz)), \
                patch.object(despliegue, "token", return_value="token-simulado"), \
                patch.object(despliegue, "quien", return_value=("prueba", "write")), \
                patch.object(despliegue, "exigir_confirmados"), \
                patch.object(sys, "argv", ["desplegar_app.py", "--solo", "app/api.py"]), \
                contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as fallo:
            despliegue.main()
        self.assertIn("forma de credencial", str(fallo.exception))
        self.assertNotIn(falsa, str(fallo.exception))
        api.create_commit.assert_not_called()
        sdk.CommitOperationAdd.assert_not_called()

    def _remoto(self, rel, datos):
        return [types.SimpleNamespace(path=rel, size=len(datos), lfs=None,
                                      blob_id=despliegue.huella("git", datos))]

    def _seco(self, api):
        sdk = types.SimpleNamespace(HfApi=Mock(return_value=api), CommitOperationAdd=Mock())
        salida = io.StringIO()
        with patch.dict(sys.modules, {"huggingface_hub": sdk}), \
                patch.object(despliegue, "RAIZ", str(self.raiz)), \
                patch.object(despliegue, "token", return_value="token-simulado"), \
                patch.object(despliegue, "quien", return_value=("prueba", "write")), \
                patch.object(sys, "argv", ["desplegar_app.py", "--solo", "app/api.py", "--seco"]), \
                contextlib.redirect_stdout(salida):
            despliegue.main()
        return salida.getvalue()

    def test_crlf_en_disco_no_sale_a_subir(self):
        """Lo que dispararon los despliegues del 13 sep: el disco de Windows con
        CRLF y el Space con el mismo texto en LF. No hay nada que subir."""
        (self.raiz / "app/api.py").write_bytes(b"api = 1\r\n")
        api = Mock()
        api.list_repo_tree.return_value = self._remoto("app/api.py", b"api = 1\n")
        salida = self._seco(api)
        self.assertNotIn("A subir", salida)
        self.assertIn("No hay nada que subir", salida)

    def test_space_en_crlf_se_normaliza_a_lf(self):
        api, operacion = Mock(), Mock()
        api.list_repo_tree.return_value = self._remoto("app/api.py", b"api = 1\r\n")
        self.assertIn("solo fin de linea", self._seco(api))
        sdk = types.SimpleNamespace(HfApi=Mock(return_value=api), CommitOperationAdd=operacion)
        with patch.dict(sys.modules, {"huggingface_hub": sdk}), \
                patch.object(despliegue, "RAIZ", str(self.raiz)), \
                patch.object(despliegue, "token", return_value="token-simulado"), \
                patch.object(despliegue, "quien", return_value=("prueba", "write")), \
                patch.object(sys, "argv", ["desplegar_app.py", "--solo", "app/api.py"]), \
                contextlib.redirect_stdout(io.StringIO()):
            despliegue.main()
        operacion.assert_called_once_with(path_in_repo="app/api.py", path_or_fileobj=b"api = 1\n")

    def test_sube_lo_del_commit_pedido_no_lo_del_disco(self):
        (self.raiz / "app/api.py").write_text("api = 2\n", encoding="utf-8")
        self.git("add", "app/api.py")
        self.git("commit", "-qm", "api 2")
        viejo = self.git("rev-parse", "HEAD~1").stdout.decode().strip()
        api, operacion = Mock(), Mock()
        api.list_repo_tree.return_value = []
        sdk = types.SimpleNamespace(HfApi=Mock(return_value=api), CommitOperationAdd=operacion)
        with patch.dict(sys.modules, {"huggingface_hub": sdk}), \
                patch.object(despliegue, "RAIZ", str(self.raiz)), \
                patch.object(despliegue, "token", return_value="token-simulado"), \
                patch.object(despliegue, "quien", return_value=("prueba", "write")), \
                patch.object(sys, "argv", ["desplegar_app.py", "--solo", "app/api.py", "--commit", viejo]), \
                contextlib.redirect_stdout(io.StringIO()):
            despliegue.main()
        operacion.assert_called_once_with(path_in_repo="app/api.py", path_or_fileobj=b"api = 1\n")
        with patch.object(despliegue, "RAIZ", str(self.raiz)), self.assertRaises(SystemExit):
            despliegue.resolver_commit("no-existe")


if __name__ == "__main__":
    unittest.main(verbosity=2)
