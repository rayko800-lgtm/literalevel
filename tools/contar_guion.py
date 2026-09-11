"""Cuenta las palabras HABLADAS del guion del video, y dice como las cuenta.

La cifra del guion se ha publicado mal tres veces -552, 553, 551- porque cada
quien contaba una cosa distinta y nadie escribio la regla. Aqui esta la regla,
ejecutable:

  1. Solo cuenta lo que hay DENTRO de las fases ANSVA, entre "## A - ATENCION"
     y "## Comprobacion antes de grabar". Fuera de ahi hay citas de la rubrica
     y ejemplos de como NO abrir, que no se dicen a camara.
  2. Dentro de eso, solo lo que va entre comillas angulares, que es como el
     guion marca el parlamento.
  3. De ese texto se descuentan las acotaciones entre parentesis -"(doble clic
     en una palabra)"-, que son indicaciones de lo que se hace, no de lo que
     se dice.
  4. Se quitan las marcas de Markdown, que no se pronuncian.
  5. Se tiran antes las NOTAS DE PRODUCCION -las lineas que empiezan por ">"-,
     aunque lleven comillas angulares dentro. Ahi las angulares citan lo que se
     teclea o lo que se ve en pantalla ("escribe «dostoyevski» y sale"), no lo
     que se dice a camara. Esta regla faltaba: la auditoria 15 hizo anadir una
     nota que nombraba «la fonetica britanica y americana» y el contador la
     sumo al parlamento.

Uso:  python -X utf8 tools/contar_guion.py
"""
import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUION = os.path.join(RAIZ, "entrega", "guion_video.md")
PPM = 150          # palabras por minuto en espanol a ritmo claro


def parlamento(texto: str) -> list[str]:
    ini = texto.find("## A — ATENCI")
    fin = texto.find("## Comprobación antes de grabar")
    if ini < 0 or fin < ini:
        raise SystemExit("no encuentro las marcas de las fases ANSVA")
    dentro = texto[ini:fin]
    # Regla 5: fuera las notas de produccion antes de buscar el parlamento.
    dentro = "\n".join(l for l in dentro.split("\n") if not l.lstrip().startswith(">"))
    return re.findall("«(.+?)»", dentro, flags=re.S)


def palabras(bloques: list[str]) -> int:
    limpio = []
    for b in bloques:
        b = re.sub(r"\([^)]*\)", " ", b)     # acotaciones, no se dicen
        b = re.sub(r"[*_`>]", " ", b)        # marcas de Markdown
        limpio.append(b)
    return len(" ".join(limpio).split())


def main() -> None:
    bloques = parlamento(io.open(GUION, encoding="utf-8").read())
    n = palabras(bloques)
    seg = n / PPM * 60
    print(f"bloques de parlamento: {len(bloques)}")
    for b in bloques:
        print(f"  {len(b.split()):4d} palabras | {' '.join(b.split())[:58]}...")
    print()
    print(f"PALABRAS HABLADAS: {n}")
    print(f"a {PPM} palabras por minuto: {int(seg // 60)}:{int(round(seg % 60)):02d}")
    print()
    print("Si esta cifra no coincide con la que publican guion_video.md y .tex,")
    print("manda la de aqui: es la unica que trae su definicion escrita.")


if __name__ == "__main__":
    main()
