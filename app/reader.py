"""Lector de libros para LiteraLevel: epub, pdf y txt -> capitulos de texto plano.

Sin dependencias externas para epub y txt (solo stdlib). El pdf usa pypdf
si esta disponible y degrada con un mensaje claro si no lo esta.
"""
from __future__ import annotations
import re, zipfile, html, os
from dataclasses import dataclass, field


@dataclass
class Capitulo:
    titulo: str
    texto: str

    @property
    def palabras(self) -> int:
        return len(self.texto.split())


@dataclass
class Libro:
    titulo: str
    autor: str
    capitulos: list[Capitulo] = field(default_factory=list)

    @property
    def palabras(self) -> int:
        return sum(c.palabras for c in self.capitulos)


_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v]+")
_NL = re.compile(r"\n{3,}")


def _limpiar_html(bruto: str) -> str:
    """Quita script/style, convierte saltos de bloque y colapsa espacios."""
    bruto = re.sub(r"(?is)<(script|style).*?</\1>", " ", bruto)
    bruto = re.sub(r"(?i)<(br|/p|/div|/h[1-6]|/li)[^>]*>", "\n", bruto)
    texto = html.unescape(_TAG.sub(" ", bruto))
    texto = _WS.sub(" ", texto)
    return _NL.sub("\n\n", texto).strip()


def _titulo_capitulo(bruto: str, texto: str, titulo_libro: str) -> str:
    """Saca el titulo del capitulo de los encabezados h1-h6, ignorando el
    encabezado corrido del libro que muchos epub repiten en cada archivo."""
    for m in re.finditer(r"(?is)<h[1-6][^>]*>(.*?)</h[1-6]>", bruto):
        cand = _limpiar_html(m.group(1)).replace("\n", " ").strip()
        if cand and cand.casefold() != titulo_libro.casefold():
            return cand[:80]
    for linea in texto.split("\n"):
        linea = linea.strip()
        if linea and linea.casefold() != titulo_libro.casefold():
            return linea[:80]
    return "(sin título)"


def _leer_epub(ruta: str) -> Libro:
    with zipfile.ZipFile(ruta) as z:
        nombres = z.namelist()

        # El OPF declara metadatos y el orden de lectura (spine).
        opf = next((n for n in nombres if n.endswith(".opf")), None)
        titulo = autor = ""
        orden: list[str] = []
        if opf:
            xml = z.read(opf).decode("utf-8", "replace")
            base = os.path.dirname(opf)
            m = re.search(r"(?is)<dc:title[^>]*>(.*?)</dc:title>", xml)
            if m:
                titulo = _limpiar_html(m.group(1))
            m = re.search(r"(?is)<dc:creator[^>]*>(.*?)</dc:creator>", xml)
            if m:
                autor = _limpiar_html(m.group(1))

            ids = dict(re.findall(r'(?is)<item\s[^>]*id="([^"]+)"[^>]*href="([^"]+)"', xml))
            for idref in re.findall(r'(?is)<itemref\s[^>]*idref="([^"]+)"', xml):
                href = ids.get(idref)
                if not href:
                    continue
                ruta_int = os.path.normpath(os.path.join(base, href)).replace("\\", "/")
                if ruta_int in nombres:
                    orden.append(ruta_int)

        # Sin spine legible, caemos al orden alfabetico de los xhtml.
        if not orden:
            orden = sorted(n for n in nombres if n.endswith((".xhtml", ".html", ".htm")))

        capitulos = []
        for n in orden:
            bruto = z.read(n).decode("utf-8", "replace")
            texto = _limpiar_html(bruto)
            if len(texto.split()) < 50:       # portadas, creditos, paginas vacias
                continue
            capitulos.append(Capitulo(_titulo_capitulo(bruto, texto, titulo), texto))

    return Libro(titulo or os.path.basename(ruta), autor, capitulos)


def _leer_pdf(ruta: str) -> Libro:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("Para leer PDF instala pypdf:  pip install pypdf") from e
    lector = PdfReader(ruta)
    meta = lector.metadata or {}
    caps = []
    for i, pagina in enumerate(lector.pages, 1):
        texto = (pagina.extract_text() or "").strip()
        if texto:
            caps.append(Capitulo(f"Página {i}", _NL.sub("\n\n", texto)))
    return Libro(meta.get("/Title") or os.path.basename(ruta), meta.get("/Author") or "", caps)


def _leer_txt(ruta: str) -> Libro:
    with open(ruta, encoding="utf-8", errors="replace") as f:
        texto = f.read()
    # Partimos por encabezados tipo "CHAPTER I" / "Capitulo 3" si los hay.
    partes = re.split(r"(?im)^\s*(chapter|cap[ií]tulo|part[e]?)\s+[\dIVXLC]+.*$", texto)
    caps = [Capitulo(f"Parte {i}", p.strip())
            for i, p in enumerate(partes, 1) if len(p.split()) > 50]
    return Libro(os.path.basename(ruta), "", caps or [Capitulo("Texto completo", texto.strip())])


def cargar(ruta: str) -> Libro:
    """Carga un libro y devuelve sus capitulos en orden de lectura."""
    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".epub":
        return _leer_epub(ruta)
    if ext == ".pdf":
        return _leer_pdf(ruta)
    if ext in (".txt", ".md"):
        return _leer_txt(ruta)
    raise ValueError(f"Formato no soportado: {ext}. Usa .epub, .pdf o .txt")


if __name__ == "__main__":
    import sys
    libro = cargar(sys.argv[1])
    print(f"Título   : {libro.titulo}")
    print(f"Autor    : {libro.autor}")
    print(f"Capítulos: {len(libro.capitulos)}")
    print(f"Palabras : {libro.palabras:,}")
    for c in libro.capitulos[:6]:
        print(f"  - {c.titulo[:60]:<60} {c.palabras:>7,} palabras")
