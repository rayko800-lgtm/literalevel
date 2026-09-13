"""Baja articulos de VOA Learning English para documentarlos (SIN nivel por articulo).

    python -X utf8 tools/bajar_voa.py --tope 120     # hasta 120 articulos por seccion
    python -X utf8 tools/bajar_voa.py                # todo lo que liste cada seccion

POR QUE SIN NIVEL. Las paginas "Beginning / Intermediate / Advanced Level" del
sitio (p/5609, p/5610, p/5611) enlazan las MISMAS secciones y 2-3 articulos de
presentacion cada una: el sitio no etiqueta cada articulo con un nivel. Se
guarda la seccion, que es lo unico que el editor declara, y el v4 dice el resto.

LICENCIA, articulo por articulo. La politica de VOA (p/6021) dice que "all text
... produced exclusively by the Voice of America is in the public domain", y
tambien que el material de Associated Press "may not be copied, published or
redistributed". Muchos articulos de "As It Is" cierran con "X reported on this
story for the Associated Press. Y adapted it for VOA Learning English". Esos
son adaptaciones de AP: se miden, pero se quedan INTERNOS, fuera del catalogo.
Lo mismo con Reuters y AFP. Solo lo escrito por VOA sin agencia va al catalogo.

Tambien se corta el glosario del final ("Words in This Story", "steep - n.
..."): son definiciones sueltas, no prosa, y el filtro del v4 lo sabe.

Sale corpus_graduado/voa/textos/articulos.jsonl (fuera de git).
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
SALIDA = RAIZ / "corpus_graduado" / "voa" / "textos"
ARTICULOS = SALIDA / "articulos.jsonl"
BASE = "https://learningenglish.voanews.com"
UA = "LiteraLevel/1.0 (proyecto academico FES Acatlan UNAM; lectura graduada)"
PAUSA = 1.0

# Secciones de prosa. Se dejan fuera las de video, fotos y lecciones de
# gramatica o pronunciacion, que no son lectura continua.
SECCIONES = {
    "3521": "As It Is",
    "1581": "American Stories",
    "987": "Words & Their Stories",
    "955": "Health & Lifestyle",
    "1579": "Science & Technology",
    "986": "Arts & Culture",
    "7468": "Education Tips",
    "5535": "Ask a Teacher",
}
AGENCIAS = re.compile(r"\b(Associated Press|Reuters|AFP|Agence France[- ]Presse)\b")
GLOSARIO = re.compile(r"^(Words in This Story|_{3,}|\S[^.]{0,40}\s[–-]\s(n|v|adj|adv)\.)", re.I)


def pedir(url, intentos=4):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(5 * (i + 1))
    return None


def limpiar(fragmento):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragmento))).strip()


def articulos_de(seccion, tope):
    urls, pagina = [], 0
    while True:
        t = pedir(f"{BASE}/z/{seccion}" + (f"?p={pagina}" if pagina else ""))
        time.sleep(PAUSA)
        if not t:
            break
        nuevos = [u for u in dict.fromkeys(re.findall(r'href="(/a/[^"]+\.html)"', t))
                  if u not in urls]
        if not nuevos:
            break
        urls.extend(nuevos)
        if tope and len(urls) >= tope:
            return urls[:tope]
        pagina += 1
    return urls


def extraer(pagina_html):
    ini = pagina_html.find('id="article-content"')
    zona = pagina_html[ini:] if ini >= 0 else pagina_html
    parrafos = [limpiar(m.group(1)) for m in re.finditer(r"<p[^>]*>(.*?)</p>", zona, re.S)]
    cuerpo, credito = [], ""
    for p in parrafos:
        if not p:
            continue
        if GLOSARIO.match(p):
            break
        if re.search(r"(reported|wrote) (on )?this story|adapted (it|this story) for VOA", p, re.I):
            credito = p
            break
        # El reproductor de audio deja este aviso al principio de cada articulo.
        if re.fullmatch(r"No media source currently available\.?", p, re.I):
            continue
        if len(p.split()) >= 4:
            cuerpo.append(p)
    titulo = re.search(r"<h1[^>]*>(.*?)</h1>", pagina_html, re.S)
    fecha = re.search(r'<time[^>]+datetime="([^"]+)"', pagina_html)
    return (limpiar(titulo.group(1)) if titulo else "", fecha.group(1) if fecha else "",
            "\n\n".join(cuerpo), credito)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tope", type=int, default=None, help="articulos por seccion")
    args = ap.parse_args()

    SALIDA.mkdir(parents=True, exist_ok=True)
    ya = set()
    if ARTICULOS.exists():
        for linea in ARTICULOS.open(encoding="utf-8"):
            try:
                ya.add(json.loads(linea)["url"])
            except (json.JSONDecodeError, KeyError):
                pass
    print(f"ya bajados: {len(ya)}", flush=True)

    with ARTICULOS.open("a", encoding="utf-8") as f:
        for zona, nombre in SECCIONES.items():
            urls = [u for u in articulos_de(zona, args.tope) if BASE + u not in ya]
            print(f"{nombre}: {len(urls)} por bajar", flush=True)
            for u in urls:
                pagina = pedir(BASE + u)
                time.sleep(PAUSA)
                if not pagina:
                    continue
                titulo, fecha, texto, credito = extraer(pagina)
                agencia = AGENCIAS.search(credito) or AGENCIAS.search(texto[-400:])
                fila = {
                    "fuente": "voa", "url": BASE + u, "seccion": nombre, "titulo": titulo,
                    "fecha": fecha, "nivel_editor": None, "credito": credito,
                    "agencia": agencia.group(1) if agencia else None,
                    "licencia": (f"adaptado de {agencia.group(1)}: con derechos" if agencia
                                 else "dominio publico (VOA)"),
                    "al_catalogo": not agencia,
                    "palabras": len(re.findall(r"[A-Za-z']+", texto)), "texto": texto,
                }
                f.write(json.dumps(fila, ensure_ascii=False) + "\n")
                f.flush()
                ya.add(BASE + u)
    print(f"listo: {len(ya)} articulos en {ARTICULOS}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
