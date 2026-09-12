"""Sube al Space SOLO los archivos de codigo que cambiaron.

    python tools/desplegar_app.py            # compara y sube lo distinto
    python tools/desplegar_app.py --seco     # compara y no sube nada
    python tools/desplegar_app.py --estado   # en que fase va el Space, y si responde

EL TOKEN

Sale de `C:/Users/laura/.hf_token` (fuera del repositorio) o de la variable
HF_TOKEN. No se imprime nunca, ni entero ni a trozos: un token con permiso de
escritura que aparece en un registro de conversacion queda quemado. Tiene que
ser de tipo *write*; uno de lectura da 401 al subir.

POR QUE UNA LISTA BLANCA Y NO `upload_folder`

`huggingface_hub.upload_folder` **no lee .gitignore**. Apuntado a la raiz de
este repositorio subiria `CLAVES.txt` y `.env` a un Space PUBLICO, con la clave
de OpenAI dentro. Aqui se enumeran los archivos uno a uno y ademas se revisa
cada uno antes de subirlo por si lleva algo con forma de credencial.

QUE NO SE TOCA, Y POR QUE

- `README.md`: el del Space no es el del repositorio. Lleva el front matter que
  declara `sdk_version` y `app_file`. Sobrescribirlo rompe el arranque.
- `app.py`: es el punto de entrada del Space y no existe en local (aqui es
  `main.py`). Son equivalentes; el que corre es el del Space.
- `kaikki_diccionario.db`, `catalogo_emb_*.npy`, `.gitattributes`: datos y
  configuracion de LFS que ya estan colocados. 243 MB que no cambian.

Cada subida reconstruye el Space sobre la misma URL. Si cambia
`requirements.txt` la reconstruccion es larga (rehace la imagen); si solo
cambia codigo, reinicia en un par de minutos.
"""
import argparse
import hashlib
import os
import re
import sys
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "MikeMaki1763/literalevel"
URL = "https://mikemaki1763-literalevel.hf.space"

# Lo unico que este guion tiene permiso para tocar.
LISTA_BLANCA = [
    "app/biblioteca.py",
    "app/catalogo.py",
    "app/config.py",
    "app/cuaderno.py",
    "app/cuentas.py",
    "app/ficha.py",
    "app/lexicon.py",
    "app/paletas.py",
    "app/perfil.py",
    "app/reader.py",
    "app/scoring.py",
    "app/ui.py",
    "app/voz.py",
    "requirements.txt",
    # El catalogo medido por el v4 (12 de septiembre de 2026): el CSV por libro
    # y la curva por capitulo. Sus embeddings (catalogo_emb_165a842a755c1b33.npy,
    # 82 MB) NO van en esta lista: en el Space viajan por LFS, su hash de git no
    # coincide con el local y se volverian a subir en cada despliegue. Se suben
    # una vez, a mano, con upload_file.
    "catalogo_medido.csv",
    "capitulos_medidos.parquet",
]

# Formas de credencial que no deben viajar a un repositorio publico.
CREDENCIALES = [
    re.compile("sk-[A-Za-z0-9_-]{20,}"),
    re.compile("hf_[A-Za-z0-9]{20,}"),
    re.compile("(?i)api[_-]?key[\"']?\\s*[:=]\\s*[\"'][A-Za-z0-9_-]{20,}"),
]


def token():
    tok = os.environ.get("HF_TOKEN", "").strip()
    if not tok:
        ruta = os.path.join(os.path.expanduser("~"), ".hf_token")
        if not os.path.isfile(ruta):
            sys.exit("No hay token: ni HF_TOKEN ni " + ruta)
        tok = open(ruta, encoding="utf-8").read().strip()
    if not tok:
        sys.exit("El archivo del token esta vacio.")
    return tok


def quien(tok):
    """Nombre y permiso del token. Nunca devuelve el token."""
    p = urllib.request.Request(
        "https://huggingface.co/api/whoami-v2",
        headers={"Authorization": "Bearer " + tok})
    import json
    try:
        d = json.load(urllib.request.urlopen(p, timeout=30))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("El token no vale (401). Revocado, mal copiado o de otra cuenta.")
        raise
    papel = ((d.get("auth") or {}).get("accessToken") or {}).get("role")
    return d.get("name"), papel


def sha_git(ruta):
    """El sha1 que git le pone a un blob: asi se compara con lo del Hub."""
    b = open(ruta, "rb").read()
    h = hashlib.sha1()
    h.update(b"blob " + str(len(b)).encode() + b"\0" + b)
    return h.hexdigest()


def sha256_de(ruta):
    """El sha256 del contenido: es lo que el Hub guarda de un archivo LFS."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()


def revisar(ruta, rel):
    texto = open(ruta, encoding="utf-8", errors="replace").read()
    for patron in CREDENCIALES:
        m = patron.search(texto)
        if m:
            sys.exit("NO SUBO NADA: " + rel + " tiene algo con forma de "
                     "credencial en la posicion " + str(m.start()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seco", action="store_true", help="comparar sin subir")
    ap.add_argument("--estado", action="store_true", help="solo mirar el Space")
    args = ap.parse_args()

    try:
        from huggingface_hub import CommitOperationAdd, HfApi
    except ImportError:
        sys.exit("Falta huggingface_hub:  pip install huggingface_hub")

    api = HfApi(token=token())

    if args.estado:
        estado(api)
        return

    nombre, papel = quien(token())
    print("cuenta: " + str(nombre) + "   permiso del token: " + str(papel))
    if papel != "write":
        sys.exit("El token no es de escritura. Uno de lectura no sube nada.")

    remoto = {}
    for it in api.list_repo_tree(REPO, repo_type="space", recursive=True,
                                 expand=True):
        if getattr(it, "size", None) is None:
            continue
        # En un archivo LFS el `blob_id` es el del PUNTERO, no el del
        # contenido: comparado con el sha1 local nunca coincide, y el CSV y el
        # parquet del catalogo (22 MB) se resubian en cada despliegue aunque
        # fueran identicos byte a byte. Para esos manda el sha256 del LFS.
        lfs = getattr(it, "lfs", None)
        remoto[it.path] = ("lfs", lfs.sha256) if lfs else ("git", it.blob_id)

    faltan, cambian, iguales = [], [], []
    for rel in LISTA_BLANCA:
        local = os.path.join(RAIZ, rel.replace("/", os.sep))
        if not os.path.isfile(local):
            faltan.append(rel)
            continue
        revisar(local, rel)
        if rel not in remoto:
            cambian.append(rel)
        elif remoto[rel][0] == "lfs" and sha256_de(local) != remoto[rel][1]:
            cambian.append(rel)
        elif remoto[rel][0] == "git" and sha_git(local) != remoto[rel][1]:
            cambian.append(rel)
        else:
            iguales.append(rel)

    if faltan:
        sys.exit("NO SUBO NADA: en la lista blanca hay archivos que no existen: "
                 + ", ".join(faltan))

    print()
    print("iguales (" + str(len(iguales)) + "): " + ", ".join(iguales))
    print()
    if not cambian:
        print("No hay nada que subir: el Space ya tiene este codigo.")
        return
    print("A subir (" + str(len(cambian)) + "):")
    for rel in cambian:
        n = os.path.getsize(os.path.join(RAIZ, rel.replace("/", os.sep)))
        print("   " + rel + "   " + str(n) + " bytes")

    if args.seco:
        print()
        print("--seco: no subo nada.")
        return

    ops = [CommitOperationAdd(path_in_repo=rel,
                              path_or_fileobj=os.path.join(
                                  RAIZ, rel.replace("/", os.sep)))
           for rel in cambian]
    info = api.create_commit(
        repo_id=REPO, repo_type="space", operations=ops,
        commit_message="sincronizar con el arbol local: " + ", ".join(cambian))
    print()
    print("subido en un solo commit: " + str(getattr(info, "oid", "") or ""))
    print("el Space reconstruye ahora. Mira como va con:")
    print("   python tools/desplegar_app.py --estado")


def estado(api):
    r = api.get_space_runtime(REPO)
    print("fase: " + str(r.stage) + "   hardware: " + str(r.hardware))
    p = urllib.request.Request(URL, headers={"User-Agent": "literalevel"})
    try:
        with urllib.request.urlopen(p, timeout=30) as resp:
            print("HTTP " + str(resp.status) + " en " + URL)
    except urllib.error.HTTPError as e:
        print("HTTP " + str(e.code) + " en " + URL)
    except Exception as e:
        print("no responde todavia: " + type(e).__name__)
    print()
    print("Ojo: RUNNING y un 200 no demuestran que la app funcione. Abrela.")


if __name__ == "__main__":
    main()
