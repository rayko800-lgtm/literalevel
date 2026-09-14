"""Pruebas offline del publicador Angular. No token, npm, SDK real ni red.

    python -X utf8 pruebas_despliegue_front.py
"""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from tools import desplegar_front as d


HTML = b'<!doctype html><head><meta name="literalevel-api" content=""></head><script>const n = "original";</script>'


class DespliegueFront(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name).resolve()
        self.browser = self.raiz / "front/dist/front/browser"
        self.browser.mkdir(parents=True)
        (self.raiz / "front/src").mkdir()
        (self.raiz / "front/src/index.html").write_bytes(HTML)
        (self.raiz / ".gitignore").write_text("front/dist/\n", encoding="utf-8")
        (self.browser / "index.html").write_bytes(HTML)
        (self.browser / "main-new.js").write_bytes(b"console.log('ok');")
        self.git("init", "-q")
        self.git("config", "user.name", "Pruebas")
        self.git("config", "user.email", "pruebas@example.invalid")
        self.confirmar()
        self.arbol = d.arbol_front(self.raiz)
        self.salida = contextlib.redirect_stdout(io.StringIO())
        self.salida.__enter__()
        self.addCleanup(self.salida.__exit__, None, None, None)

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.raiz, check=True,
                       capture_output=True)

    def confirmar(self):
        self.git("add", "--", ".")
        self.git("commit", "-qm", "fixture")

    def sdk(self, items=(), error=None):
        class Missing(Exception):
            pass

        class Add:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        commits, lecturas = [], []
        attrs = self.raiz / "remote-attributes.txt"
        attrs.write_bytes(b"*.ico filter=lfs diff=lfs merge=lfs -text\n")

        def download(*args, **kwargs):
            lecturas.append(kwargs)
            if isinstance(error, int):
                fallo = Missing("simulado")
                fallo.response = SimpleNamespace(status_code=error)
                raise fallo
            if error:
                raise error
            return str(attrs)

        def commit(**kwargs):
            commits.append(kwargs)
            return SimpleNamespace(oid="revision-" + str(len(commits)))

        def tree(*args, **kwargs):
            self.assertEqual(kwargs["revision"], "base")
            return iter(items)

        api = SimpleNamespace(token="simulado", repo_info=lambda *a, **k: SimpleNamespace(sha="base"),
                              list_repo_tree=tree, create_commit=commit)
        sdk = ModuleType("huggingface_hub")
        sdk.CommitOperationAdd = Add
        sdk.HfApi = lambda **kwargs: api
        sdk.hf_hub_download = download
        errors = ModuleType("huggingface_hub.errors")
        errors.EntryNotFoundError = Missing
        return patch.dict(sys.modules, {"huggingface_hub": sdk,
                                       "huggingface_hub.errors": errors}), commits, lecturas, Missing

    def test_seco_build_sin_token_ni_red(self):
        with patch.object(d, "RAIZ", self.raiz), patch.object(d, "construir") as build, \
                patch.object(d, "token", side_effect=AssertionError("token")), \
                patch.object(d, "publicar", side_effect=AssertionError("red")):
            d.main(["--seco"])
        build.assert_called_once_with(self.raiz)
        self.assertEqual((self.browser / "index.html").read_bytes(), HTML)
        self.assertEqual((self.raiz / "front/src/index.html").read_bytes(), HTML)

    def test_dirty_front_bloquea_antes_build_y_token(self):
        for staged in (False, True):
            with self.subTest(staged=staged):
                (self.raiz / "front/src/index.html").write_bytes(HTML + b"dirty")
                if staged:
                    self.git("add", "--", "front/src/index.html")
                with patch.object(d, "RAIZ", self.raiz), patch.object(d, "construir") as build, \
                        patch.object(d, "token", side_effect=AssertionError("token")):
                    with self.assertRaises(SystemExit):
                        d.main([])
                build.assert_not_called()

    def test_untracked_front_bloquea_pero_ajeno_no(self):
        (self.raiz / "trabajo-ajeno.txt").write_bytes(b"ajeno")
        self.assertEqual(d.arbol_front(self.raiz), self.arbol)
        (self.raiz / "front/src/nuevo.ts").write_bytes(b"nuevo")
        with self.assertRaises(SystemExit):
            d.arbol_front(self.raiz)

    def test_cambio_confirmado_durante_build_bloquea(self):
        (self.raiz / "front/src/index.html").write_bytes(HTML + b"nuevo")
        self.confirmar()
        with self.assertRaises(SystemExit):
            d.exigir_mismo_arbol(self.raiz, self.arbol)

    def test_meta_unica_y_resto_literal(self):
        original = b'<head>\n<meta content="local?a=1&amp;b=2" name="literalevel-api"/>\n</head><script>let x="<meta name=other>";</script>'
        resultado = d.configurar_html(original)
        self.assertIn(d.API.encode(), resultado)
        self.assertTrue(resultado.endswith(original[original.index(b"\n</head>"):]))
        # Lo que de verdad sale del build: Angular minifica content="" a
        # `content` sin valor, y así se publicó un front sin API (14 sep).
        minificado = d.configurar_html(b'<head><meta name="literalevel-api" content><title>x</title></head>')
        self.assertEqual(minificado, b'<head><meta name="literalevel-api" content="'
                         + d.API.encode() + b'"><title>x</title></head>')
        for html in (b"<head></head>", HTML + HTML,
                     b'<meta name="literalevel-api" content="" content="x">',
                     b'<meta name="literalevel-api" name="otro" content="">',
                     b'<meta name="literalevel-api">'):
            with self.subTest(html=html), self.assertRaises(SystemExit):
                d.configurar_html(html)

    def test_forma_credencial_en_bytes_congelados_bloquea(self):
        # Forma sintetica, nunca una credencial real; se introduce al leer.
        sintetico = b'const x="' + b"hf_" + b"Z" * 24 + b'";'
        leer = Path.read_bytes

        def cambiado(ruta):
            return sintetico if ruta.name == "main-new.js" else leer(ruta)

        with patch.object(Path, "read_bytes", cambiado), \
                patch.object(d, "token", side_effect=AssertionError("token")):
            with self.assertRaises(SystemExit) as error:
                d.congelar(self.raiz)
        self.assertNotIn(sintetico.decode(), str(error.exception))

    def test_todos_textos_se_escanean_y_binarios_desconocidos_no(self):
        for extension in d.TEXTOS:
            (self.browser / ("asset" + extension)).write_bytes(b"texto")
        with patch.object(d, "revisar", wraps=d.revisar) as revisar:
            contenidos = d.congelar(self.raiz)
        self.assertEqual(revisar.call_count, len(contenidos))
        for llamada in revisar.call_args_list:
            self.assertEqual(llamada.kwargs["contenido"], contenidos[llamada.args[1]])
        for nombre in (".env", "modelo.glb", "source.map", "README.md", ".gitattributes", "font.woff2"):
            ruta = self.browser / nombre
            ruta.write_bytes(b"no autorizado")
            with self.subTest(nombre=nombre), self.assertRaises(SystemExit):
                d.congelar(self.raiz)
            ruta.unlink()

    def test_binario_debe_coincidir_con_public_versionado(self):
        origen = self.raiz / "front/public/favicon.ico"
        origen.parent.mkdir(parents=True)
        origen.write_bytes(b"icono")
        self.confirmar()
        ruta = self.browser / "favicon.ico"
        ruta.write_bytes(b"otro")
        with self.assertRaises(SystemExit):
            d.congelar(self.raiz)
        ruta.write_bytes(b"icono")
        self.assertEqual(d.congelar(self.raiz)["favicon.ico"], b"icono")

    def test_sdk_recibe_snapshot_y_conserva_chunks_viejos(self):
        contenidos = d.congelar(self.raiz)
        (self.browser / "main-new.js").write_bytes(b"cambio posterior")
        remoto = [SimpleNamespace(path="chunk-antiguo.js", size=4, blob_id="old", lfs=None),
                  SimpleNamespace(path="README.md", size=4, blob_id="readme", lfs=None)]
        mock, commits, _, _ = self.sdk(remoto)
        with mock, patch.object(d, "token", return_value="simulado"):
            d.publicar(contenidos, self.raiz, self.arbol)
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0]["parent_commit"], "base")
        ops = commits[0]["operations"]
        self.assertEqual({op.path_in_repo: op.path_or_fileobj for op in ops}, contenidos)
        self.assertNotIn("chunk-antiguo.js", [op.path_in_repo for op in ops])
        self.assertNotIn("README.md", [op.path_in_repo for op in ops])

    def test_lfs_previo_preserva_atributos_y_encadena_parent(self):
        mock, commits, lecturas, _ = self.sdk()
        with mock, patch.object(d, "token", return_value="simulado"):
            d.publicar({"boca3d/cara.glb": b"glb"}, self.raiz, self.arbol)
        self.assertEqual(len(commits), 2)
        self.assertEqual(lecturas[0]["revision"], "base")
        self.assertEqual(commits[0]["parent_commit"], "base")
        self.assertEqual(commits[1]["parent_commit"], "revision-1")
        attrs = commits[0]["operations"][0]
        self.assertEqual(attrs.path_in_repo, ".gitattributes")
        self.assertTrue(attrs.path_or_fileobj.startswith(b"*.ico filter=lfs diff=lfs merge=lfs -text\n"))
        self.assertTrue(attrs.path_or_fileobj.endswith(d.REGLA_GLB + b"\n"))
        self.assertEqual(d.atributos_glb(attrs.path_or_fileobj), attrs.path_or_fileobj)

    def test_error_lectura_remota_aborta_sin_commits(self):
        mock, commits, _, _ = self.sdk(error=PermissionError("denegado"))
        with mock, patch.object(d, "token", return_value="simulado"):
            with self.assertRaises(PermissionError):
                d.publicar({"boca3d/cara.glb": b"glb"}, self.raiz, self.arbol)
        self.assertEqual(commits, [])

    def test_solo_404_admite_gitattributes_ausente(self):
        for codigo in (404, 403, 500):
            mock, commits, _, missing = self.sdk(error=codigo)
            with self.subTest(codigo=codigo), mock, patch.object(d, "token", return_value="simulado"):
                if codigo == 404:
                    d.publicar({"boca3d/cara.glb": b"glb"}, self.raiz, self.arbol)
                    self.assertEqual(len(commits), 2)
                    self.assertEqual(commits[0]["operations"][0].path_or_fileobj, d.REGLA_GLB + b"\n")
                else:
                    with self.assertRaises(missing):
                        d.publicar({"boca3d/cara.glb": b"glb"}, self.raiz, self.arbol)
                    self.assertEqual(commits, [])

    def test_cambio_fuente_durante_red_bloquea_commit(self):
        mock, commits, _, _ = self.sdk()
        with mock, patch.object(d, "token", return_value="simulado"):
            def info(*args, **kwargs):
                (self.raiz / "front/src/index.html").write_bytes(HTML + b"cambio")
                return SimpleNamespace(sha="base")
            sdk = sys.modules["huggingface_hub"]
            sdk.HfApi().repo_info = info
            with self.assertRaises(SystemExit):
                d.publicar({"index.html": HTML}, self.raiz, self.arbol)
        self.assertEqual(commits, [])

    def test_conflicto_parent_no_reintenta_ni_fuerza(self):
        mock, commits, _, _ = self.sdk()
        with mock, patch.object(d, "token", return_value="simulado"):
            api = sys.modules["huggingface_hub"].HfApi()
            with patch.object(api, "create_commit", side_effect=RuntimeError("conflicto remoto")) as commit:
                with self.assertRaises(RuntimeError):
                    d.publicar({"index.html": HTML}, self.raiz, self.arbol)
            commit.assert_called_once()
            self.assertEqual(commit.call_args.kwargs["parent_commit"], "base")
        self.assertEqual(commits, [])

    def test_build_real_comando_fijo_y_fallo_detiene(self):
        with patch.object(d.subprocess, "run", return_value=SimpleNamespace(returncode=1)) as run:
            with self.assertRaises(SystemExit):
                d.construir(self.raiz)
        self.assertEqual(run.call_args.args[0][1:], ["run", "build"])
        self.assertEqual(run.call_args.kwargs["cwd"], self.raiz / "front")

    def test_remoto_igual_no_commit(self):
        contenidos = d.congelar(self.raiz)
        remoto = [SimpleNamespace(path=rel, size=len(b), blob_id=d.hash_git(b), lfs=None)
                  for rel, b in contenidos.items()]
        mock, commits, _, _ = self.sdk(remoto)
        with mock, patch.object(d, "token", return_value="simulado"):
            d.publicar(contenidos, self.raiz, self.arbol)
        self.assertEqual(commits, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
