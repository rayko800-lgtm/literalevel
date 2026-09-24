"""Publica solo el build de Angular, sin borrar chunks de sesiones abiertas.

--seco reconstruye y muestra hashes locales, sin leer token ni consultar el Hub.
Ambos modos exigen fuentes confirmadas. No cambia permisos, hardware ni README.
"""
import argparse
import hashlib
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import os
import subprocess
import sys

try:
    from .desplegar_app import exigir_confirmados, revisar, token
except ImportError:
    from desplegar_app import exigir_confirmados, revisar, token

RAIZ = Path(__file__).resolve().parents[1]
REPO = "MikeMaki1763/literalevel-front"
API = "https://mikemaki1763-literalevel.hf.space"
TEXTOS = {".html", ".js", ".css", ".json", ".svg", ".txt"}
# No hay fuentes binarias en el build actual. Una nueva requiere revision aqui.
# 24 sep: la boca didáctica (D4) lleva sus propios GLB y sus créditos (.txt).
BINARIOS = {"favicon.ico", "boca3d/cara.glb", "boca3d/lengua.glb",
            "boca3d/didactica/cara.glb", "boca3d/didactica/lengua.glb"}
REGLA_GLB = b"*.glb filter=lfs diff=lfs merge=lfs -text"


def abortar(mensaje):
    raise SystemExit("NO SUBO NADA: " + mensaje)


def arbol_front(raiz):
    exigir_confirmados(["front"], raiz=str(raiz))
    p = subprocess.run(["git", "rev-parse", "HEAD:front"], cwd=raiz,
                       capture_output=True, check=False)
    if p.returncode:
        abortar("no se pudo identificar el arbol confirmado de front.")
    return p.stdout.strip()


def exigir_mismo_arbol(raiz, arbol):
    if arbol_front(raiz) != arbol:
        abortar("front cambio de commit durante la preparacion.")


def construir(raiz):
    npm = "npm.cmd" if os.name == "nt" else "npm"
    p = subprocess.run([npm, "run", "build"], cwd=raiz / "front", check=False)
    if p.returncode:
        abortar("el build de Angular fallo.")


def configurar_html(contenido):
    """Sustituye solo la etiqueta meta identificada por el parser, no scripts."""
    texto = contenido.decode("utf-8")
    inicios = [0]
    for linea in texto.splitlines(keepends=True):
        inicios.append(inicios[-1] + len(linea))

    class Metas(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.cambios = []

        def handle_starttag(self, tag, attrs):
            if tag != "meta" or not any(
                    k == "name" and v == "literalevel-api" for k, v in attrs):
                return
            if (sum(k == "name" for k, _ in attrs) != 1
                    or sum(k == "content" for k, _ in attrs) != 1):
                abortar("la meta literalevel-api tiene atributos ambiguos.")
            # El build de Angular minifica content="" a `content` sin valor, y el
            # parser lo da como None: sin tratarlo aparte, la meta salía vacía y
            # el front publicado pedía /api a su propio dominio (404, 14 sep).
            nueva = "<meta" + "".join(
                " " + k + ('="' + escape(API, quote=True) + '"' if k == "content"
                           else "" if v is None else '="' + escape(v, quote=True) + '"')
                for k, v in attrs) + ">"
            linea, columna = self.getpos()
            inicio = inicios[linea - 1] + columna
            self.cambios.append((inicio, len(self.get_starttag_text()), nueva))

        handle_startendtag = handle_starttag

    parser = Metas()
    parser.feed(texto)
    parser.close()
    if len(parser.cambios) != 1:
        abortar("index.html debe tener exactamente una meta literalevel-api.")
    inicio, largo, nueva = parser.cambios[0]
    if 'content="' + escape(API, quote=True) + '"' not in nueva:
        abortar("la meta literalevel-api no quedo apuntando a la API.")
    return (texto[:inicio] + nueva + texto[inicio + largo:]).encode("utf-8")


def congelar(raiz):
    carpeta = raiz / "front" / "dist" / "front" / "browser"
    if not carpeta.is_dir() or carpeta.resolve() != carpeta:
        abortar("no existe el directorio de build esperado o es un enlace.")
    contenidos = {}
    for ruta in sorted(carpeta.rglob("*")):
        if ruta.is_symlink() or not ruta.resolve().is_relative_to(carpeta):
            abortar("el build contiene un enlace o una ruta exterior.")
        if ruta.is_dir():
            continue
        rel = ruta.relative_to(carpeta).as_posix()
        if rel in {"README.md", ".gitattributes"}:
            abortar("el build intenta reemplazar metadatos del Space.")
        contenido = ruta.read_bytes()
        if rel in BINARIOS:
            origen = raiz / "front" / "public" / rel
            exigir_confirmados(["front/public/" + rel], raiz=str(raiz))
            if origen.is_symlink() or contenido != origen.read_bytes():
                abortar("un binario no coincide con su asset publico confirmado.")
        elif ruta.suffix.lower() in TEXTOS:
            contenido.decode("utf-8", errors="strict")
            if rel == "index.html":
                contenido = configurar_html(contenido)
            revisar(str(ruta), rel, contenido=contenido)
        else:
            abortar("tipo de archivo no autorizado en el build: " + rel)
        contenidos[rel] = contenido
    if "index.html" not in contenidos:
        abortar("falta index.html.")
    return contenidos


def hash_git(contenido):
    return hashlib.sha1(b"blob " + str(len(contenido)).encode() + b"\0"
                        + contenido).hexdigest()


def atributos_glb(actual):
    # Ultima regla especifica: no se reemplaza ninguna linea remota existente.
    if actual.splitlines() and actual.splitlines()[-1] == REGLA_GLB:
        return actual
    return actual + (b"\n" if actual and not actual.endswith(b"\n") else b"") + REGLA_GLB + b"\n"


def publicar(contenidos, raiz, arbol):
    from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
    from huggingface_hub.errors import EntryNotFoundError

    api = HfApi(token=token())
    revision = api.repo_info(REPO, repo_type="space").sha
    if not revision:
        abortar("el Hub no devolvio una revision remota.")
    remoto = {it.path: it for it in api.list_repo_tree(
        REPO, repo_type="space", recursive=True, revision=revision)
        if getattr(it, "size", None) is not None}
    cambios = {}
    for rel, contenido in contenidos.items():
        it = remoto.get(rel)
        lfs = getattr(it, "lfs", None)
        igual = (hashlib.sha256(contenido).hexdigest() == lfs.sha256 if lfs
                 else hash_git(contenido) == getattr(it, "blob_id", None))
        if not igual:
            cambios[rel] = contenido
    if not cambios:
        print("El build ya coincide con el Space; no se modifica nada.")
        return
    atributos = None
    if any(rel.endswith(".glb") for rel in cambios):
        try:
            ruta = hf_hub_download(REPO, ".gitattributes", repo_type="space",
                                   revision=revision, token=api.token)
            actual = Path(ruta).read_bytes()
        except EntryNotFoundError as error:
            if getattr(getattr(error, "response", None), "status_code", None) != 404:
                raise
            actual = b""
        nuevo = atributos_glb(actual)
        if nuevo != actual:
            revisar(".gitattributes", ".gitattributes", contenido=nuevo)
            atributos = nuevo
    exigir_mismo_arbol(raiz, arbol)
    if atributos is not None:
        info = api.create_commit(
            repo_id=REPO, repo_type="space", parent_commit=revision,
            operations=[CommitOperationAdd(path_in_repo=".gitattributes",
                                           path_or_fileobj=atributos)],
            commit_message="LFS para los modelos GLB del frontend")
        revision = info.oid
        if not revision:
            abortar("el commit de LFS no devolvio revision; no se publica el build.")
    exigir_mismo_arbol(raiz, arbol)
    info = api.create_commit(
        repo_id=REPO, repo_type="space", parent_commit=revision,
        operations=[CommitOperationAdd(path_in_repo=rel, path_or_fileobj=contenido)
                    for rel, contenido in cambios.items()],
        commit_message="Publicar build Angular confirmado " + arbol.decode("ascii")[:12])
    print("Frontend publicado: " + str(info.oid))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seco", action="store_true",
                        help="build y plan local; no token, red ni cambios remotos")
    args = parser.parse_args(argv)
    raiz = RAIZ.resolve()
    arbol = arbol_front(raiz)
    construir(raiz)
    contenidos = congelar(raiz)
    exigir_mismo_arbol(raiz, arbol)
    print("Build confirmado (SHA256):")
    for rel, contenido in contenidos.items():
        print(hashlib.sha256(contenido).hexdigest(), len(contenido), rel)
    if args.seco:
        print("--seco: plan local, sin comparar ni modificar el Space.")
        return
    publicar(contenidos, raiz, arbol)


if __name__ == "__main__":
    main()
