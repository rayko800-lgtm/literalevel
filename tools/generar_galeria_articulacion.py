"""Genera tools/galeria_articulacion.html: todas las animaciones de articulacion.

    python -X utf8 tools/generar_galeria_articulacion.py

Una rejilla con cada sonido de General American y de RP (animado y quieto) y
unas palabras de ejemplo, para revisarlos de un vistazo. El boton de arriba
cambia entre fondo claro y oscuro; los SVG no traen fondo propio.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))

import animacion_articulatoria as aa  # noqa: E402
import articulacion  # noqa: E402

SALIDA = RAIZ / "tools" / "galeria_articulacion.html"
PALABRAS = [("/ˈmoʊstli/", "ga"), ("[ˈθɔːt]", "rp"), ("/dʒʌdʒ/", "ga"), ("/ˈvɛɹi/", "ga"),
            ("/ˈbɛɹi/", "ga"), ("/θɪŋk/", "ga"), ("/ʃip/", "ga"), ("/ʃɪp/", "ga"),
            ("[ˈwɔːtə]", "rp"), ("/ˈwɑɾɚ/", "ga"), ("[ɡəʊ]", "rp"), ("/ɡoʊ/", "ga")]


def celda(svg: str, pie: str) -> str:
    return f'<figure>{svg}<figcaption>{html.escape(pie)}</figcaption></figure>'


def main() -> None:
    bloques = []
    for acento, inventario in (("ga", articulacion.INVENTARIO_GA), ("rp", articulacion.INVENTARIO_RP)):
        celdas = []
        for sonido in articulacion.inventario(acento):
            svg = aa.svg_articulacion(sonido.simbolo, acento)
            if svg:
                pie = f"/{sonido.simbolo}/ · {sonido.ficha.rasgos} · {len(svg.encode('utf-8')) // 1024 + 1} KB"
                celdas.append(celda(svg, pie))
        bloques.append(f'<h2>{html.escape(articulacion.ACENTOS[acento])} · animados ({len(celdas)})</h2>'
                       f'<div class="rejilla">{"".join(celdas)}</div>')
        quietos = [celda(aa.svg_articulacion_quieto(s.simbolo, acento), f"/{s.simbolo}/ quieto")
                   for s in articulacion.inventario(acento)]
        bloques.append(f'<details><summary>{html.escape(articulacion.ACENTOS[acento])} · quietos</summary>'
                       f'<div class="rejilla">{"".join(quietos)}</div></details>')
    palabras = []
    for ipa, acento in PALABRAS:
        svg = aa.svg_palabra(ipa, acento)
        if svg:
            palabras.append(celda(svg, f"{ipa} ({acento}) · {len(svg.encode('utf-8')) // 1024 + 1} KB"))
    bloques.insert(0, f'<h2>Palabras</h2><div class="rejilla">{"".join(palabras)}</div>')

    pagina = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Galería de articulación · LiteraLevel</title>
<style>
body{{margin:0;padding:16px;font:14px system-ui,sans-serif;background:#fafafa;color:#222}}
body.oscuro{{background:#14171c;color:#ddd}}
h1{{font-size:20px;margin:0 0 8px}} h2{{font-size:16px;margin:24px 0 8px}}
.rejilla{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}}
figure{{margin:0;border:1px solid #8883;border-radius:8px;padding:6px}}
figure svg{{width:100%;height:auto;display:block}}
figcaption{{font-size:12px;opacity:.75;margin-top:4px}}
button{{font:inherit;padding:4px 10px}} summary{{cursor:pointer;margin:12px 0}}
</style></head><body>
<h1>Galería de articulación</h1>
<p>Generada con <code>tools/generar_galeria_articulacion.py</code>. Corte lateral, la cara mira a la izquierda.
<button onclick="document.body.classList.toggle('oscuro')">Fondo claro / oscuro</button></p>
{"".join(bloques)}
</body></html>
"""
    SALIDA.write_text(pagina, encoding="utf-8")
    print(f"{SALIDA} ({SALIDA.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
