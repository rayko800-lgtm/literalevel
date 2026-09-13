"""Baja los libros en ingles de Let's Read (The Asia Foundation) con su nivel (1-5).

    python -X utf8 tools/bajar_letsread.py              # todo, reanudable
    python -X utf8 tools/bajar_letsread.py --muestra 5  # 5 por nivel, para probar

Endpoints localizados el 12 de septiembre de 2026 leyendo el codigo del lector
(chunk _app de letsreadasia.org), sin autenticacion:
- listado por nivel: /api/book/elastic/search/?lId=<ingles>&readingLevel=N&limit=20&cursor=
  con `readingLevel`, `license`, `masterBookId`, `slug`, autores...
- texto por paginas: /api/v5/book/preview/language/<ingles>/book/<masterBookId>
  (`pages[].extractedLongContentValue`). Con el id del libro da 404.

No hay robots.txt y los terminos no dicen nada de acceso automatizado. Aun asi:
una peticion por segundo, User-Agent identificable y reanudable.

LICENCIA POR LIBRO, y mezclada: CC-BY-4.0 va al catalogo; CC-BY-NC-4.0 y
CC-BY-NC-ND-4.0 se miden pero se quedan INTERNOS (regla de Miguel, ver
PIPELINE_CORPUS.md). ND ademas impide publicar derivados: el texto no se toca.

Muchos libros "en ingles" son traducciones de un original asiatico: se guarda un
solo libro por `masterBookId`. Sale corpus_graduado/letsread/textos/libros.jsonl.
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "corpus_graduado" / "letsread" / "textos"
LIBROS = SALIDA / "libros.jsonl"
BASE = "https://letsreadasia.org/api"
INGLES = "4846240843956224"
UA = "LiteraLevel/1.0 (proyecto academico FES Acatlan UNAM; lectura graduada)"
PAUSA = 1.0
LIBRES = {"CC-BY-4.0", "CC-BY 4.0", "CC BY 4.0"}


def pedir(url, intentos=4):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            pass
        time.sleep(5 * (i + 1))
    return None


def listar(nivel, tope=None):
    libros, cursor = [], ""
    while True:
        url = (f"{BASE}/book/elastic/search/?searchText=&lId={INGLES}&readingLevel={nivel}"
               f"&limit=20&cursor={urllib.parse.quote(str(cursor))}")
        d = pedir(url)
        time.sleep(PAUSA)
        if not d:
            break
        lote = (d.get("featured") or []) + (d.get("other") or [])
        nuevos = [b for b in lote if b.get("masterBookId") not in {x.get("masterBookId") for x in libros}]
        # El filtro de nivel se comprueba: si la API lo ignorara, el corpus
        # entero saldria con la etiqueta equivocada.
        libros.extend(b for b in nuevos if str(b.get("readingLevel")) == str(nivel))
        if tope and len(libros) >= tope:
            return libros[:tope]
        siguiente = d.get("cursorWebSafeString")
        if not nuevos or not siguiente or siguiente == cursor:
            break
        cursor = siguiente
    return libros


def texto_de(paginas):
    trozos = []
    for p in sorted(paginas or [], key=lambda p: p.get("pageNum") or 0):
        t = p.get("extractedLongContentValue") or ""
        t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
        t = html.unescape(re.sub(r"<[^>]+>", " ", t))
        t = "\n".join(re.sub(r"[ \t]+", " ", l).strip() for l in t.splitlines()).strip()
        if t:
            trozos.append(t)
    return "\n\n".join(trozos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--muestra", type=int, default=None)
    args = ap.parse_args()

    SALIDA.mkdir(parents=True, exist_ok=True)
    ya = set()
    if LIBROS.exists():
        for linea in LIBROS.open(encoding="utf-8"):
            try:
                ya.add(json.loads(linea)["master"])
            except (json.JSONDecodeError, KeyError):
                pass
    print(f"ya bajados: {len(ya)}", flush=True)

    with LIBROS.open("a", encoding="utf-8") as f:
        for nivel in (1, 2, 3, 4, 5):
            lista = [b for b in listar(nivel, args.muestra) if b.get("masterBookId") not in ya]
            print(f"nivel {nivel}: {len(lista)} por bajar", flush=True)
            for b in lista:
                master = b["masterBookId"]
                if master in ya:
                    continue
                d = pedir(f"{BASE}/v5/book/preview/language/{INGLES}/book/{master}")
                time.sleep(PAUSA)
                if not d:
                    continue
                texto = texto_de(d.get("pages"))
                licencia = str(b.get("license") or d.get("license") or "desconocida")
                # Los autores NO vienen en el listado (alli collaboratorsByRole
                # llega vacio): solo en la respuesta del texto, con la clave en
                # mayusculas. Los 15 libros de la primera prueba salieron sin
                # autor por leerlos del listado. La atribucion CC BY los necesita.
                roles = d.get("collaboratorsByRole") or b.get("collaboratorsByRole") or {}

                def nombres(rol):
                    return [c["name"].strip() for c in roles.get(rol) or []
                            if isinstance(c, dict) and (c.get("name") or "").strip()]

                autores = nombres("AUTHOR")
                ilustradores = nombres("ILLUSTRATOR")
                fila = {
                    "fuente": "letsread", "master": master, "id": b.get("id"), "slug": b.get("slug"),
                    "titulo": b.get("name"), "nivel_editor": str(b.get("readingLevel")),
                    "decodable": bool(b.get("decodable")), "pais": b.get("countryOfOrigin"),
                    "autores": autores, "ilustradores": ilustradores,
                    "editorial": nombres("PUBLISHER") or nombres("ORGANIZATION"),
                    "licencia": licencia,
                    "al_catalogo": licencia in LIBRES,
                    "url": f"https://www.letsreadasia.org/book/{b.get('slug') or master}",
                    "palabras": len(re.findall(r"[A-Za-z']+", texto)), "texto": texto,
                }
                f.write(json.dumps(fila, ensure_ascii=False) + "\n")
                f.flush()
                ya.add(master)
    print(f"listo: {len(ya)} libros en {LIBROS}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
