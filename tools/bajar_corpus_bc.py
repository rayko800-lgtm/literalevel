"""Reconstruye el corpus de validacion del British Council, verificado byte a byte.

    python -X utf8 tools/bajar_corpus_bc.py [carpeta_de_descargas] [carpeta_destino]
    python -X utf8 validar_local.py [carpeta_destino]

Por defecto busca en ~/Downloads y deja el corpus en ./corpus_bc.

POR QUE EXISTE. Los 59 textos de lectura de British Council LearnEnglish con
los que se valida el v4 tienen derechos: no se pueden redistribuir. Pero son de
DESCARGA PUBLICA Y GRATUITA. Asi que no se entregan los archivos: se entrega la
receta. El manifiesto (`entrega/corpus_bc_manifiesto.csv`) lleva, por archivo,
su nivel, su URL y su SHA-256, y este guion comprueba que lo que tienes es
EXACTAMENTE lo que se midio.

POR QUE NO LOS DESCARGA EL SOLO. Se intento, y no se puede. Comprobado el 12 de
septiembre de 2026: el CDN de British Council responde **403 a `curl`** y deja
**sin respuesta** a Python aunque se haga pasar por un navegador. Es una
proteccion antibots, y no se va a intentar esquivar. Con un navegador de verdad
las 59 URLs funcionan -se comprobaron asi-. De modo que el reparto es:

1. **Tu navegador descarga.** El guion te da la lista de enlaces que faltan.
2. **El guion verifica.** Empareja cada PDF con el manifiesto POR SU HASH, no
   por su nombre -el navegador puede anadir "(1)" o cambiar espacios-, lo copia
   a la carpeta destino con el nombre que espera `validar_local.py` y te dice
   que falta.

TRES COSAS QUE NO SON LA MISMA, y se dicen distinto. Este corpus ya se ha comido
tres fallos silenciosos (un `\\b` que no cortaba en el guion bajo, un patron que
no veia un archivo, un "uno no disponible" que si lo estaba):

- **Falta**: no hay ningun PDF con ese hash ni con ese nombre. Descargalo.
- **No es un PDF**: el archivo con ese nombre esta cortado o es una pagina de
  error guardada como .pdf. Vuelve a descargarlo.
- **PDF valido con otro hash**: British Council ha ACTUALIZADO ese documento
  desde que se midio. No es un error tuyo: las cifras publicadas se midieron
  sobre la version anterior, y ese archivo no se copia al corpus.

Solo biblioteca estandar: no instala nada.
"""
import csv
import hashlib
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MANIFIESTO = RAIZ / "entrega" / "corpus_bc_manifiesto.csv"
ORIGEN = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads"
DESTINO = Path(sys.argv[2]) if len(sys.argv) > 2 else RAIZ / "corpus_bc"


def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for trozo in iter(lambda: fh.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()


def _nombre_remoto(archivo: str) -> str:
    """El nombre con el que lo guarda un navegador: sin el prefijo de nivel."""
    return archivo.split("__", 1)[-1]


def _normalizar(nombre: str) -> str:
    """Quita lo que anade un navegador al repetir una descarga: ' (1)', '_1'."""
    base = re.sub(r"\s*\(\d+\)(?=\.pdf$)", "", nombre, flags=re.I)
    return base.replace(" ", "-").lower()


def main() -> int:
    if not MANIFIESTO.exists():
        print(f"No encuentro el manifiesto en {MANIFIESTO}")
        return 2
    filas = list(csv.DictReader(MANIFIESTO.open(encoding="utf-8")))
    por_hash = {f["sha256"]: f for f in filas}
    por_nombre = {_normalizar(_nombre_remoto(f["archivo"])): f for f in filas}
    DESTINO.mkdir(parents=True, exist_ok=True)

    # 1. Lo que ya esta en el destino y cuadra no se vuelve a mirar.
    listos = {f["archivo"] for f in filas
              if (DESTINO / f["archivo"]).exists()
              and _sha256(DESTINO / f["archivo"]) == f["sha256"]}

    # 2. Se recorre la carpeta de descargas emparejando POR HASH.
    rotos, actualizados = {}, {}
    candidatos = sorted(p for p in ORIGEN.glob("*") if p.suffix.lower() == ".pdf")
    for p in candidatos:
        try:
            h = _sha256(p)
        except OSError:
            continue
        f = por_hash.get(h)
        if f:
            if f["archivo"] not in listos:
                shutil.copyfile(p, DESTINO / f["archivo"])
                listos.add(f["archivo"])
            continue
        # No cuadra el hash: ¿es uno de los nuestros con otro contenido?
        f = por_nombre.get(_normalizar(p.name))
        if f and f["archivo"] not in listos:
            if p.read_bytes()[:5] != b"%PDF-":
                rotos[f["archivo"]] = p.name
            else:
                actualizados[f["archivo"]] = p.name

    faltan = [f for f in filas if f["archivo"] not in listos
              and f["archivo"] not in rotos and f["archivo"] not in actualizados]

    print(f"{len(listos)}/{len(filas)} verificados byte a byte -> {DESTINO}")
    if rotos:
        print(f"\nNO SON UN PDF ({len(rotos)}) -> vuelve a descargarlos:")
        for a, n in sorted(rotos.items()):
            print(f"  - {n}")
    if actualizados:
        print(f"\nACTUALIZADOS POR BRITISH COUNCIL ({len(actualizados)}) -> no es un error "
              f"tuyo. Las cifras publicadas se midieron sobre la version anterior de "
              f"estos documentos, y no se copian al corpus:")
        for a, n in sorted(actualizados.items()):
            print(f"  - {n}")
    if faltan:
        print(f"\nFALTAN ({len(faltan)}). British Council bloquea las descargas "
              f"automaticas, asi que abre estos enlaces en tu navegador, guarda los PDF "
              f"en {ORIGEN} y vuelve a ejecutar este guion:")
        for f in faltan:
            print(f"  {f['nivel']}  {f['url']}")
    if len(listos) == len(filas):
        print(f"\nCorpus completo. Siguiente paso:\n"
              f"  python -X utf8 validar_local.py {DESTINO}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
