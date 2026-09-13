"""Baja los libros en ingles de StoryWeaver con su nivel de lectura (1 a 4).

    python -X utf8 tools/bajar_storyweaver.py              # todo, reanudable
    python -X utf8 tools/bajar_storyweaver.py --muestra 20 # 20 por nivel, para probar

Por que StoryWeaver entra en el catalogo y no se queda interno: su FAQ dice que
"the CC BY license under which all content is licensed on StoryWeaver". Se
guarda igualmente el aviso de copyright de cada libro, por si alguno lo matiza.

Lo que sale, en corpus_graduado/storyweaver/textos/libros.jsonl (fuera de git):
una linea por libro con id, titulo, nivel del editor, idioma, si es traduccion
o re-nivelado, editorial, autores, aviso, palabras y el texto de las paginas.

Dos cuidados con el servidor, que es de una ONG:
- una peticion cada PAUSA segundos, nunca en paralelo;
- reanudable: lee lo ya bajado y no vuelve a pedirlo.
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "corpus_graduado" / "storyweaver" / "textos"
LIBROS = SALIDA / "libros.jsonl"
BASE = "https://storyweaver.org.in/api/v1"
UA = "LiteraLevel/1.0 (proyecto academico FES Acatlan UNAM; lectura graduada)"
PAUSA = 0.6
POR_PAGINA = 50
LICENCIA = "CC BY 4.0"


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
            espera = 5 * (i + 1)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            espera = 5 * (i + 1)
        time.sleep(espera)
    return None


def texto_de_paginas(paginas):
    """Solo las paginas de cuento: portada y creditos no son lectura."""
    trozos = []
    for p in paginas or []:
        if p.get("pageType") not in ("StoryPage",):
            continue
        t = re.sub(r"<(br|/p|/div|/h\d)[^>]*>", "\n", p.get("html") or "", flags=re.I)
        t = html.unescape(re.sub(r"<[^>]+>", " ", t))
        t = "\n".join(re.sub(r"[ \t]+", " ", l).strip() for l in t.splitlines())
        t = re.sub(r"\n{2,}", "\n", t).strip()
        if t:
            trozos.append(t)
    return "\n\n".join(trozos)


def ids_del_nivel(nivel, tope=None):
    pagina, ids = 1, []
    while True:
        url = (f"{BASE}/books-search?languages%5B%5D=English&levels%5B%5D={nivel}"
               f"&page={pagina}&per_page={POR_PAGINA}")
        d = pedir(url)
        time.sleep(PAUSA)
        if not d or not d.get("data"):
            break
        for b in d["data"]:
            # El filtro de la API se comprueba: si ignorara el nivel, todo el
            # corpus saldria con la etiqueta equivocada y la validacion mentiria.
            if str(b.get("level")) == str(nivel) and b.get("language") == "English":
                ids.append(b["slug"])
        if tope and len(ids) >= tope:
            return ids[:tope]
        if pagina >= d["metadata"].get("totalPages", pagina):
            break
        pagina += 1
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--muestra", type=int, default=None,
                    help="libros por nivel, para probar")
    args = ap.parse_args()

    SALIDA.mkdir(parents=True, exist_ok=True)
    ya = set()
    if LIBROS.exists():
        for linea in LIBROS.open(encoding="utf-8"):
            try:
                ya.add(json.loads(linea)["slug"])
            except (json.JSONDecodeError, KeyError):
                pass
    print(f"ya bajados: {len(ya)}", flush=True)

    # El indice se guarda: listar los ~17.000 libros son ~340 peticiones y no
    # hay por que repetirlas en cada reanudacion.
    indice_ruta = SALIDA / "indice.json"
    if indice_ruta.exists() and not args.muestra:
        indice = json.loads(indice_ruta.read_text(encoding="utf-8"))
    else:
        indice = {str(n): ids_del_nivel(n, args.muestra) for n in (1, 2, 3, 4)}
        if not args.muestra:
            indice_ruta.write_text(json.dumps(indice), encoding="utf-8")
    # Orden ALEATORIO e intercalando niveles. Bajar entero son muchas horas, y
    # asi cualquier trozo ya descargado es una muestra equilibrada y sin sesgo
    # de popularidad (la API lista primero los mas valorados): se puede validar
    # mientras el resto sigue bajando.
    import random
    rng = random.Random(20260912)
    colas = {}
    for n, slugs in indice.items():
        pend = [s for s in slugs if s not in ya]
        rng.shuffle(pend)
        colas[n] = pend
        print(f"nivel {n}: {len(slugs)} en la API, {len(pend)} por bajar", flush=True)
    orden = []
    while any(colas.values()):
        for n in sorted(colas):
            if colas[n]:
                orden.append((n, colas[n].pop()))

    with LIBROS.open("a", encoding="utf-8") as f:
        for n_total, (nivel, slug) in enumerate(orden, 1):
            n = n_total
            if True:
                ficha = pedir(f"{BASE}/stories/{slug}")
                time.sleep(PAUSA)
                lect = pedir(f"{BASE}/stories/{slug}/read")
                time.sleep(PAUSA)
                if not ficha or not lect:
                    continue
                s, r = ficha["data"], lect["data"]
                texto = texto_de_paginas(r.get("pages"))
                fila = {
                    "fuente": "storyweaver", "slug": slug, "id": s.get("id"),
                    "titulo": s.get("name"), "nivel_editor": str(s.get("level")),
                    "nivel_pedido": str(nivel), "idioma": s.get("language"),
                    "es_traduccion": bool(s.get("isTranslation")),
                    "renivelado": bool(s.get("isRelevelled")),
                    "adaptado": bool(s.get("isAdapted")),
                    "editorial": (s.get("publisher") or {}).get("name"),
                    "autores": [a.get("name") for a in s.get("authors") or []],
                    "aviso": s.get("copyrightNotice"),
                    "licencia": LICENCIA,
                    "url": f"https://storyweaver.org.in/en/stories/{slug}",
                    "palabras": len(re.findall(r"[A-Za-z']+", texto)),
                    "texto": texto,
                }
                f.write(json.dumps(fila, ensure_ascii=False) + "\n")
                f.flush()
                ya.add(slug)
                if n % 100 == 0:
                    print(f"  {n}/{len(orden)} ({len(ya)} en total)", flush=True)
    print(f"listo: {len(ya)} libros en {LIBROS}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
