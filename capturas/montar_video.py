"""Monta el video de demostracion de LiteraLevel a partir de los fotogramas.

Los fotogramas se capturan conduciendo Chrome sobre la app real (no son
maquetas). Este script los une, les pone un rotulo explicativo abajo y escribe
un mp4 que se puede enviar por WhatsApp o proyectar en clase.

Uso:  python -X utf8 capturas/montar_video.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
FOTOGRAMAS = AQUI / "video"
SALIDA = AQUI / "literalevel-demo.mp4"

FPS = 30
SEGUNDOS_POR_ESCENA = 3.2
ALTO_ROTULO = 96

ESCENAS = [
    ("f01", "1. Situar al lector",
     "Tres preguntas. Ni examen, ni registro, ni cuenta de usuario"),
    ("f02", "Responde como lee de verdad",
     "No se pregunta por un nivel CEFR que casi nadie sabe de si mismo"),
    ("f03", "Nivel estimado",
     "1.07 / 2.00 (intermedio) y el rango de dificultad que le conviene leer"),
    ("f05", "2. Buscar que leer, en espanol",
     "1.197 libros indexados por significado; se describe la trama, no el titulo"),
    ("f06", "Un clic y a leer",
     "El libro se descarga de Gutenberg y se abre solo: no hay que salir de la app"),
    ("f07", "3. El modelo v4 mide el capitulo",
     "1.53 / 2.00 - orientativo C1 - 8 bloques - confianza alta"),
    ("f08", "4. Consultar una palabra",
     "Doble clic sobre 'peeped' y se copia sola; la oracion sale del capitulo"),
    ("f09", "Diccionario, IPA y contexto",
     "Lema, IPA britanica, Wiktionary, sentido en contexto y gramatica"),
    ("f10", "La explicacion, en ingles si se quiere",
     "Quien ya lee comodo no tiene por que salir del ingles para entender"),
    ("f11", "5. Practicar pronunciacion",
     "Trae una frase del capitulo que se esta leyendo"),
    ("f12", "Palabra por palabra",
     "Verde lo que sono bien, rojo lo que no, y como colocar la boca para cada sonido"),
    ("f13", "6. Todo en local",
     "Modelo v4, diccionario de 243 MB y catalogo. Sin Colab y sin tuneles temporales"),
]


def _fuente(tam: int):
    for nombre in ("segoeui.ttf", "arial.ttf", "calibri.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{nombre}", tam)
        except OSError:
            continue
    return ImageFont.load_default()


TITULO = _fuente(30)
PIE = _fuente(21)


def componer(ruta: Path, titulo: str, pie: str, ancho: int, alto: int) -> Image.Image:
    img = Image.open(ruta).convert("RGB")
    lienzo = Image.new("RGB", (ancho, alto + ALTO_ROTULO), (16, 18, 27))
    # La captura, centrada y sin deformar.
    if img.size != (ancho, alto):
        img.thumbnail((ancho, alto), Image.LANCZOS)
    lienzo.paste(img, ((ancho - img.width) // 2, (alto - img.height) // 2))

    d = ImageDraw.Draw(lienzo)
    y = alto
    d.rectangle([0, y, ancho, y + ALTO_ROTULO], fill=(24, 26, 38))
    d.line([0, y, ancho, y], fill=(90, 96, 130), width=2)
    d.text((36, y + 18), titulo, font=TITULO, fill=(233, 236, 245))
    d.text((36, y + 56), pie, font=PIE, fill=(158, 166, 196))
    return lienzo


def main() -> int:
    faltan = [n for n, _, _ in ESCENAS if not (FOTOGRAMAS / f"{n}.jpeg").exists()]
    if faltan:
        print("Faltan fotogramas:", ", ".join(faltan))
        return 1

    primera = Image.open(FOTOGRAMAS / f"{ESCENAS[0][0]}.jpeg")
    ancho, alto = primera.size
    # Los codecs quieren dimensiones pares.
    ancho -= ancho % 2
    alto -= alto % 2

    repeticiones = int(FPS * SEGUNDOS_POR_ESCENA)
    with imageio.get_writer(SALIDA, fps=FPS, quality=8, macro_block_size=None) as w:
        for nombre, titulo, pie in ESCENAS:
            marco = componer(FOTOGRAMAS / f"{nombre}.jpeg", titulo, pie, ancho, alto)
            datos = np.asarray(marco)
            for _ in range(repeticiones):
                w.append_data(datos)
            print(f"  {nombre}  {titulo}")

    mb = SALIDA.stat().st_size / 1e6
    print(f"\n{SALIDA}")
    print(f"{len(ESCENAS)} escenas · {len(ESCENAS) * SEGUNDOS_POR_ESCENA:.0f} s · {mb:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
