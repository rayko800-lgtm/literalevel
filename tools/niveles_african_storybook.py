"""Cruza los cuentos en ingles de African Storybook con su nivel de lectura.

    python -X utf8 tools/niveles_african_storybook.py <booklistjs.php guardado>

El texto viene del repositorio global-asp/asp-source (Markdown, con licencia por
cuento) y el nivel de la lista que usa la propia web (booklistjs.php): cada
entrada trae id, titulo, idioma (un codigo numerico) y `level`. El repositorio
no trae el id de la web, asi que se cruza por titulo normalizado.

Sale corpus_graduado/african_storybook/textos/cuentos.jsonl con texto, nivel,
licencia y si puede ir al catalogo (CC BY) o se queda interno (NC).
"""
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ / "corpus_graduado" / "african_storybook" / "crudo" / "asp-source-master" / "en"
SALIDA = RAIZ / "corpus_graduado" / "african_storybook" / "textos" / "cuentos.jsonl"

CAMPO = re.compile(r'(\w+):"((?:[^"\\]|\\.)*)"')
ENTRADA = re.compile(r"bookItems\.push\(\{(.*?)\}\);", re.S)


def normalizar(titulo):
    t = html.unescape(titulo or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def leer_lista(ruta):
    t = Path(ruta).read_text(encoding="utf-8", errors="replace")
    return [dict(CAMPO.findall(m.group(1))) for m in ENTRADA.finditer(t)]


def leer_cuento(ruta):
    crudo = ruta.read_text(encoding="utf-8")
    lineas = crudo.splitlines()
    titulo = lineas[0].lstrip("# ").strip() if lineas else ruta.stem
    licencia = re.search(r"License:\s*\[?([^\]\n]+)\]?", crudo)
    cuerpo = re.split(r"\n\*\s*License:", crudo)[0]
    paginas = [p.strip() for p in cuerpo.split("\n##") if p.strip()]
    texto = "\n\n".join(p for p in paginas[1:] if not p.startswith("#")) if paginas else ""
    return titulo, (licencia.group(1).strip() if licencia else "desconocida"), texto


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    lista = leer_lista(sys.argv[1])
    muestra = [i for i in lista if normalizar(i.get("title")) == "a very tall man"]
    codigos = Counter(i.get("lang") for i in muestra)
    print(f"entradas en la lista: {len(lista)} | codigos de 'A very tall man': {dict(codigos)}")
    por_titulo = {}
    for cod, _ in codigos.most_common():
        for i in lista:
            if i.get("lang") == cod:
                por_titulo.setdefault(normalizar(i.get("title")), i)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    filas, sin_nivel = [], []
    for ruta in sorted(FUENTES.glob("*.md")):
        titulo, licencia, texto = leer_cuento(ruta)
        entrada = por_titulo.get(normalizar(titulo))
        libre = licencia.upper().replace("-", " ") in ("CC BY", "CC BY 4.0")
        fila = {
            "fuente": "african_storybook", "archivo": ruta.name, "titulo": titulo,
            "id_web": entrada.get("id") if entrada else None,
            "nivel_editor": entrada.get("level") if entrada else None,
            "aprobado": entrada.get("approved") if entrada else None,
            "licencia": licencia, "al_catalogo": libre,
            "palabras": len(re.findall(r"[A-Za-z']+", texto)), "texto": texto,
        }
        filas.append(fila)
        if not entrada:
            sin_nivel.append(titulo)
    with SALIDA.open("w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")

    print(f"cuentos: {len(filas)} | con nivel: {len(filas) - len(sin_nivel)} | sin cruzar: {len(sin_nivel)}")
    print("por nivel:", sorted(Counter(f["nivel_editor"] for f in filas if f["nivel_editor"]).items()))
    print("licencias:", dict(Counter(f["licencia"] for f in filas)))
    print("al catalogo:", sum(f["al_catalogo"] for f in filas), "| internos:", sum(not f["al_catalogo"] for f in filas))
    pal = sorted(f["palabras"] for f in filas)
    print(f"palabras: mediana {pal[len(pal) // 2]}, <150: {sum(p < 150 for p in pal)}, <250: {sum(p < 250 for p in pal)}")
    print("sin cruzar (muestra):", sin_nivel[:8])
    print("->", SALIDA)


if __name__ == "__main__":
    main()
