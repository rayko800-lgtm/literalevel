"""Sube al Space SOLO los archivos de codigo que cambiaron.

    python tools/desplegar_app.py            # compara y sube lo distinto
    python tools/desplegar_app.py --seco     # compara y no sube nada
    python tools/desplegar_app.py --estado   # en que fase va el Space, y si responde
    python tools/desplegar_app.py --solo app/api.py  # solo esta ruta confirmada

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
import subprocess
import sys
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "MikeMaki1763/literalevel"
URL = "https://mikemaki1763-literalevel.hf.space"

# Lo unico que este guion tiene permiso para tocar.
LISTA_BLANCA = [
    "app/api.py",
    "app/audiolibro.py",
    "app/biblioteca.py",
    "app/catalogo.py",
    "app/config.py",
    "app/cuaderno.py",
    "app/cuentas.py",
    # Eos para los audios nuevos (28 sep 2026): cola de /api/eos/*.
    "app/eos.py",
    # api.py lo lee al importar (f5c1fa8, GPT-Live): sin el, el Space no arranca.
    "app/gpt_live_session.json",
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
    # IPA americana de CMUdict donde Kaikki no la trae (4e, 5029a40). Texto de
    # 2,9 MB, sin LFS. Sin el, «tragic» se queda sin IPA y la correccion de voz
    # sin fonema. La licencia de CMUdict viaja con los datos.
    "app/pronunciacion_cmu.tsv",
    "app/pronunciacion_cmu_LICENCIA.txt",
    # Animaciones 2D de la boca (4e, 87f1435 y 05783c0). Si falta, la app no se
    # cae pero no hay animaciones. Los SVG no viajan: se escriben la primera vez
    # en config.dir_datos()/articulacion_svg, que ya esta en allowed_paths.
    "app/animacion_articulatoria.py",
    # Junto al CSV grande y leidos por app/catalogo.py al cargar: la lista curada
    # de avisos de contenido (no se filtra, se avisa) y las correcciones de filas
    # mal medidas en el precalculo (PG2242), sin tocar la huella de los embeddings.
    "avisos_contenido.csv",
    "correcciones_catalogo.csv",
    # Los textos libres que no son lectura en ingles (tools/marcar_no_lectura.py):
    # se excluyen al buscar y recomendar sin tocar el CSV externo ni su .npy.
    "no_lectura_externo.csv",
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


def seleccionar(solo=None):
    """Rutas exactas de la lista blanca, nunca carpetas ni patrones."""
    if solo is None:
        return list(LISTA_BLANCA)
    rutas = list(dict.fromkeys(str(r).replace("\\", "/") for r in solo))
    if not rutas or any(r not in LISTA_BLANCA for r in rutas):
        sys.exit("NO SUBO NADA: --solo admite exclusivamente rutas exactas de la lista blanca.")
    return rutas


def exigir_confirmados(rutas, raiz=None):
    """No publicar un archivo ajeno a HEAD ni cambios de otra sesion."""
    raiz = raiz or RAIZ
    try:
        versionados = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", *rutas], cwd=raiz,
            capture_output=True, check=False)
        if versionados.returncode:
            sys.exit("NO SUBO NADA: hay archivos seleccionados sin versionar o Git no esta disponible.")
        estado = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *rutas],
            cwd=raiz, capture_output=True, check=False)
    except OSError:
        sys.exit("NO SUBO NADA: no se pudo comprobar Git.")
    if estado.returncode:
        sys.exit("NO SUBO NADA: no se pudo comprobar el estado de los archivos seleccionados.")
    if estado.stdout:
        sys.exit("NO SUBO NADA: los archivos seleccionados tienen cambios sin commit. "
                 "Confirma solo tu trabajo o reduce la seleccion con --solo.")

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


# Los finales de linea: con `core.autocrlf=true` el disco de Windows tiene CRLF y
# el repositorio LF. Comparar o subir los bytes del disco dejaba el Space mezclado
# (lo subido con `git show` en LF, lo subido desde el disco en CRLF) y hacia que
# `--seco` pidiera subir archivos identicos en contenido (13-14 sep 2026). Desde
# entonces se compara y se sube lo que dice el commit, con el texto en LF.
BINARIOS = {".mp3", ".parquet", ".npy", ".db", ".png", ".jpg", ".webp", ".gz", ".zip"}


def es_texto(rel):
    return os.path.splitext(rel)[1].lower() not in BINARIOS


def resolver_commit(ref, raiz=None):
    """El sha completo del commit, resuelto UNA vez: si otra sesion hace commit a
    mitad del despliegue, lo que se sube no cambia."""
    r = subprocess.run(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
                       cwd=raiz or RAIZ, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"NO SUBO NADA: «{ref}» no es un commit de este repositorio.")
    return r.stdout.strip()


def bytes_del_commit(rel, commit, raiz=None):
    """Los bytes de `rel` en `commit`; el texto, normalizado a LF."""
    r = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=raiz or RAIZ, capture_output=True)
    if r.returncode:
        sys.exit(f"NO SUBO NADA: {rel} no existe en el commit {commit[:7]}.")
    datos = r.stdout
    return datos.replace(b"\r\n", b"\n") if es_texto(rel) else datos


def huella(tipo, datos):
    """sha1 de blob de git o sha256 de LFS, sobre bytes en memoria."""
    if tipo == "lfs":
        return hashlib.sha256(datos).hexdigest()
    return hashlib.sha1(b"blob " + str(len(datos)).encode() + b"\0" + datos).hexdigest()


def comparar(rel, datos, remoto):
    """'igual', 'nuevo', 'fin_de_linea' (mismo texto, otros finales) o 'distinto'."""
    if rel not in remoto:
        return "nuevo"
    tipo, h = remoto[rel]
    if huella(tipo, datos) == h:
        return "igual"
    if es_texto(rel) and huella(tipo, datos.replace(b"\n", b"\r\n")) == h:
        return "fin_de_linea"
    return "distinto"


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


def _texto_de_parquet(fuente):
    """Todas las celdas de un parquet, descomprimidas, en un solo texto."""
    import pandas as pd
    df = pd.read_parquet(fuente)
    return "\n".join(df[c].astype(str).str.cat(sep="\n") for c in df.columns)


def revisar(ruta, rel, contenido=None):
    # Un binario no lleva credenciales en texto, y leido como texto puede dar un
    # falso positivo que bloquee el despliegue. El parquet del corpus abierto SI
    # se escanea, pero DESCOMPRIMIDO: leido como bytes, Snappy cambia una cadena
    # repetida por una referencia atras, y con gzip o zstd no queda nada legible
    # (auditoria cruzada de e6, D1).
    if rel.endswith(".mp3"):
        return
    if rel.endswith(".parquet"):
        import io
        texto = _texto_de_parquet(ruta if contenido is None else io.BytesIO(contenido))
    elif contenido is None:
        with open(ruta, encoding="utf-8", errors="replace") as f:
            texto = f.read()
    else:
        texto = contenido.decode("utf-8", errors="replace")
    for patron in CREDENCIALES:
        m = patron.search(texto)
        if m:
            sys.exit("NO SUBO NADA: " + rel + " tiene algo con forma de "
                     "credencial en la posicion " + str(m.start()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seco", action="store_true", help="comparar sin subir")
    ap.add_argument("--estado", action="store_true", help="solo mirar el Space")
    ap.add_argument("--solo", nargs="+", action="extend", metavar="RUTA",
                    help="limitar a rutas exactas de la lista blanca; no admite carpetas")
    ap.add_argument("--commit", default="HEAD", metavar="REF",
                    help="commit cuyo contenido se compara y se sube (por defecto HEAD)")
    args = ap.parse_args()
    if args.estado and args.solo is not None:
        ap.error("--estado no se combina con --solo")
    seleccion = seleccionar(args.solo)
    if not args.estado and not args.seco:
        exigir_confirmados(seleccion)

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

    revision = api.repo_info(REPO, repo_type="space").sha
    remoto = {}
    for it in api.list_repo_tree(REPO, repo_type="space", recursive=True,
                                 expand=True, revision=revision):
        if getattr(it, "size", None) is None:
            continue
        # En un archivo LFS el `blob_id` es el del PUNTERO, no el del
        # contenido: comparado con el sha1 local nunca coincide, y el CSV y el
        # parquet del catalogo (22 MB) se resubian en cada despliegue aunque
        # fueran identicos byte a byte. Para esos manda el sha256 del LFS.
        lfs = getattr(it, "lfs", None)
        remoto[it.path] = ("lfs", lfs.sha256) if lfs else ("git", it.blob_id)

    commit = resolver_commit(args.commit)
    print("contenido del commit " + commit[:7] + " (texto en LF)")
    contenidos, motivos, cambian, iguales = {}, {}, [], []
    for rel in seleccion:
        datos = bytes_del_commit(rel, commit)
        revisar(None, rel, contenido=datos)
        motivo = comparar(rel, datos, remoto)
        if motivo == "distinto" and es_texto(rel) and remoto[rel][0] == "git":
            # Con finales MEZCLADOS (parte CRLF, parte LF) ninguna de las dos
            # huellas casa: se mira el texto del Space para no dar por cambiado
            # lo que solo tiene otros finales de linea.
            try:
                from huggingface_hub import hf_hub_download
                texto_space = open(hf_hub_download(REPO, rel, repo_type="space", revision=revision,
                                                   token=api.token), "rb").read()
                if texto_space.replace(b"\r\n", b"\n") == datos:
                    motivo = "fin_de_linea"
            except Exception:
                pass
        if motivo == "igual":
            iguales.append(rel)
        else:
            cambian.append(rel)
            contenidos[rel], motivos[rel] = datos, motivo

    print()
    print("iguales (" + str(len(iguales)) + "): " + ", ".join(iguales))
    print()
    if not cambian:
        print("No hay nada que subir: el Space ya tiene este codigo.")
        return
    print("A subir (" + str(len(cambian)) + "):")
    for rel in cambian:
        nota = {"nuevo": "  (no esta en el Space)", "fin_de_linea": "  (solo fin de linea: pasa a LF)"}.get(motivos[rel], "")
        print("   " + rel + "   " + str(len(contenidos[rel])) + " bytes" + nota)

    faltan_lfs, gitattributes = reglas_lfs_que_faltan(api, cambian)
    if faltan_lfs:
        print()
        print("Al .gitattributes del Space le faltan reglas de LFS para estos "
              "binarios; se anadiran antes, en un commit aparte:")
        for linea in faltan_lfs:
            print("   " + linea)

    if args.seco:
        print()
        print("--seco: no subo nada. Comparacion del commit " + commit[:7] + " con el Space.")
        return

    # Los bytes son los del commit, ya congelados en `contenidos`; se vuelven a
    # escanear justo antes del SDK y se exige otra vez que el disco no tenga
    # cambios sin commit en la seleccion (otra sesion puede haber editado).
    for rel in cambian:
        revisar(None, rel, contenido=contenidos[rel])
    exigir_confirmados(seleccion)

    if faltan_lfs:
        nuevo = gitattributes.rstrip("\n") + "\n" + "\n".join(faltan_lfs) + "\n"
        info_lfs = api.create_commit(
            repo_id=REPO, repo_type="space",
            parent_commit=revision,
            operations=[CommitOperationAdd(path_in_repo=".gitattributes",
                                           path_or_fileobj=nuevo.lstrip("\n").encode("utf-8"))],
            commit_message="lfs para los audios de los fonemas: "
                           + ", ".join(l.split()[0] for l in faltan_lfs))
        revision = info_lfs.oid
        print("reglas de LFS anadidas al .gitattributes del Space")

    ops = [CommitOperationAdd(path_in_repo=rel,
                              path_or_fileobj=contenidos[rel])
           for rel in cambian]
    info = api.create_commit(
        repo_id=REPO, repo_type="space", operations=ops,
        parent_commit=revision,
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
