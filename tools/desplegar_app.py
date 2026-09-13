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
- `kaikki_diccionario.db`, `catalogo_emb_*.npy`: datos que ya estan
  colocados. 243 MB que no cambian.
- `.gitattributes` no se REEMPLAZA nunca: solo se le anade una regla de LFS
  cuando falta (ver `LFS_NECESARIO`), y en un commit aparte y previo.

LOS AUDIOS DE LOS FONEMAS (fusionado a mano del commit e53d8ca de la otra sesion)

Los 41 mp3 de `app/audio_fonemas/` son binarios, y Hugging Face rechaza un
binario que no vaya por LFS/Xet. Cuando se miro el Space (12 sep 2026) su
`.gitattributes` tenia reglas para `*.parquet` o `*.npy`, pero **no para
`*.mp3`**. Si falta, el guion la anade ANTES de subir los audios y en su propio
commit: el modo de subida (LFS o normal) lo decide el Hub con el
`.gitattributes` que ya esta en el repositorio, no con el que viaja en el mismo
commit. La lista de audios sale del inventario de `app/fonemas.py`, asi que un
fonema sin su mp3 para el despliegue en vez de subir una tabla a medias.

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
    # Los corpus libres (StoryWeaver, African Storybook, VOA, Let's Read) que
    # genera tools/catalogar_corpus.py: filas del catalogo y el texto que la app
    # sirve con su atribucion. Solo licencias libres: el catalogador aborta si no.
    # Sus embeddings (catalogo_emb_ext_<huella>.npy) cambian de nombre con cada
    # version del externo y se suben a mano, como los de Gutenberg.
    "catalogo_externo.csv",
    "corpus_abierto.parquet",
    "app/fonemas.py",
    # La tabla del AFI (entrega-4e). ui.py lo importa en la cabecera: sin el,
    # se cae la app entera, no solo la pestana.
    "app/articulacion.py",
]


def _audios_de_fonemas():
    """Los mp3 que la app espera, uno por sonido de cada inventario.

    Se leen de `fonemas.INVENTARIO` (americano, app/audio_fonemas/) y de
    `articulacion.INVENTARIO_RP` (britanico, app/audio_fonemas_rp/), no con un
    glob: un glob subiria lo que haya y callaria el que falte. Ninguno de los
    dos modulos importa nada pesado (ni gradio, ni el SDK de OpenAI)."""
    sys.path.insert(0, os.path.join(RAIZ, "app"))
    import articulacion
    import fonemas
    rp = os.path.relpath(articulacion.DIR_AUDIO_RP, RAIZ).replace(os.sep, "/")
    return ([f"app/audio_fonemas/{f.archivo}" for f in fonemas.INVENTARIO]
            + [f"{rp}/{s.archivo}" for s in articulacion.INVENTARIO_RP])


LISTA_BLANCA += _audios_de_fonemas()

# Reglas de LFS que el Space tiene que tener ANTES de recibir estos binarios.
LFS_NECESARIO = {
    ".mp3": "*.mp3 filter=lfs diff=lfs merge=lfs -text",
}

# Formas de credencial que no deben viajar a un repositorio publico.
# Sin letra ni cifra DELANTE: una clave empieza en su propio token. Sin esa
# condicion, la URL de VOA ".../cask-of-amontillado-edgar-allan-poe..." casaba
# con "sk-of-amontillado-..." y bloqueaba el despliegue (12 sep 2026).
CREDENCIALES = [
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])hf_[A-Za-z0-9]{20,}"),
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


def reglas_lfs_que_faltan(api, cambian):
    """Las lineas de `LFS_NECESARIO` que hacen falta y el Space no tiene."""
    extensiones = {os.path.splitext(rel)[1] for rel in cambian}
    necesarias = [linea for ext, linea in LFS_NECESARIO.items()
                  if ext in extensiones]
    if not necesarias:
        return [], ""
    from huggingface_hub import hf_hub_download
    try:
        actual = open(hf_hub_download(REPO, ".gitattributes", repo_type="space",
                                      token=api.token),
                      encoding="utf-8").read()
    except Exception:
        actual = ""
    patrones = {l.split()[0] for l in actual.splitlines() if l.strip()}
    return [l for l in necesarias if l.split()[0] not in patrones], actual


def revisar(ruta, rel):
    # Un binario no lleva credenciales en texto, y leido como texto puede dar un
    # falso positivo que bloquee el despliegue. El parquet del corpus abierto SI
    # se escanea: lleva texto plano dentro.
    if rel.endswith(".mp3"):
        return
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

    faltan_lfs, gitattributes = reglas_lfs_que_faltan(api, cambian)
    if faltan_lfs:
        print()
        print("Al .gitattributes del Space le faltan reglas de LFS para estos "
              "binarios; se anadiran antes, en un commit aparte:")
        for linea in faltan_lfs:
            print("   " + linea)

    if args.seco:
        print()
        print("--seco: no subo nada.")
        return

    if faltan_lfs:
        nuevo = gitattributes.rstrip("\n") + "\n" + "\n".join(faltan_lfs) + "\n"
        api.create_commit(
            repo_id=REPO, repo_type="space",
            operations=[CommitOperationAdd(path_in_repo=".gitattributes",
                                           path_or_fileobj=nuevo.lstrip("\n").encode("utf-8"))],
            commit_message="lfs para los audios de los fonemas: "
                           + ", ".join(l.split()[0] for l in faltan_lfs))
        print("reglas de LFS anadidas al .gitattributes del Space")

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
