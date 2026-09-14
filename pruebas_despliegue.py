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
        operacion.assert_called_once_with(path_in_repo="app/api.py",
                                         path_or_fileobj=(self.raiz / "app/api.py").read_bytes())
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
