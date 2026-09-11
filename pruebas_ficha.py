"""Pruebas de `app/ficha.py`: la ficha del libro.

Lo que se comprueba aqui no es "que no lance" -de eso ya se ocupan las
extremas- sino que los numeros signifiquen algo. Tres de las cuatro
comprobaciones nacieron de errores reales encontrados probando con libros de
verdad, y estan escritas para que no vuelvan:

1. El dialogo salia 100% en Alicia, Orgullo y Prejuicio y Crimen y Castigo,
   los tres. Se media por parrafos y el epub no tiene parrafos.
2. 'gutenberg' y 'project' aparecian entre las palabras mas repetidas de
   Alicia, porque la licencia entera va pegada al capitulo XII.
3. El tiempo de lectura se imprimia "entre 4 y 2 h": dos horas redondeadas
   por separado, al reves y perdiendo los minutos.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "app"))

import ficha  # noqa: E402

fallos = []


def comprobar(nombre, condicion, detalle=""):
    print(f"  {'ok  ' if condicion else 'FALLA'} {nombre}"
          + (f"  -> {detalle}" if detalle and not condicion else ""))
    if not condicion:
        fallos.append(nombre)


@dataclass
class Cap:
    titulo: str
    texto: str

    @property
    def palabras(self):
        return len(self.texto.split())


@dataclass
class Lib:
    titulo: str
    autor: str
    capitulos: list

    @property
    def palabras(self):
        return sum(c.palabras for c in self.capitulos)


NARRACION = ("The house stood alone on the hill, and the wind moved through "
             "the long grass without stopping. He walked up the path slowly, "
             "counting the stones as he went. Nothing had changed in twenty "
             "years, and that was the worst of it. ") * 30
DIALOGO = ('"Where have you been?" she asked. "Nowhere," he said. "You have '
           'been gone all day." "I told you I would be." "You told me '
           'nothing." ') * 40
LICENCIA = ("*** END OF THE PROJECT GUTENBERG EBOOK TEST *** "
            "Project Gutenberg volunteers and employees expend considerable "
            "effort to identify the Project Gutenberg-tm collection. "
            "Project Gutenberg is a registered trademark. ") * 30


print("Ficha: lo que se cuenta")

narrado = Lib("Narrado", "A", [Cap("I", NARRACION), Cap("II", NARRACION)])
hablado = Lib("Hablado", "A", [Cap("I", DIALOGO), Cap("II", DIALOGO)])
cn = ficha.caracteristicas(narrado)
ch = ficha.caracteristicas(hablado)

comprobar("el dialogo distingue narracion de conversacion",
          ch.dialogo > cn.dialogo + 0.4, f"narrado {cn.dialogo}, hablado {ch.dialogo}")
comprobar("un libro narrado no da 100% de dialogo", cn.dialogo < 0.2, str(cn.dialogo))
comprobar("un libro hablado no da 0% de dialogo", ch.dialogo > 0.5, str(ch.dialogo))
comprobar("la frase media es un numero de palabras creible",
          5 <= cn.frase_media <= 40, str(cn.frase_media))
comprobar("la riqueza esta entre 0 y 1", 0 < cn.riqueza <= 1, str(cn.riqueza))


print("Ficha: la licencia de Gutenberg")

con_licencia = Lib("Con licencia", "A",
                   [Cap("I", NARRACION), Cap("II", NARRACION + " " + LICENCIA)])
cl = ficha.caracteristicas(con_licencia)
comprobar("'gutenberg' no entra en las palabras mas repetidas",
          not any(p in ("gutenberg", "project") for p in cl.distintivas),
          str(cl.distintivas))
comprobar("la licencia no cuenta como palabras del libro",
          cl.palabras < con_licencia.palabras, f"{cl.palabras} de {con_licencia.palabras}")
comprobar("recortar no se come el libro",
          cl.palabras >= cn.palabras * 0.9, f"{cl.palabras} vs {cn.palabras}")
comprobar("sin_licencia deja intacto un texto que no es de Gutenberg",
          ficha.sin_licencia(NARRACION).strip() == NARRACION.strip())
comprobar("sin_licencia con texto vacio devuelve cadena vacia",
          ficha.sin_licencia("") == "")
comprobar("una mencion temprana a Gutenberg no borra el libro",
          len(ficha.sin_licencia("End of Project Gutenberg's note. " + NARRACION))
          > len(NARRACION) * 0.9)
solo_licencia = Lib("Solo licencia", "", [Cap("Licencia", LICENCIA)])
comprobar("un archivo que es solo licencia sigue dando un recuento",
          ficha.caracteristicas(solo_licencia).palabras > 0)


print("Ficha: el reloj")

comprobar("minutos sueltos", ficha.reloj(46) == "46 minutos", ficha.reloj(46))
comprobar("horas exactas sin minutos", ficha.reloj(120) == "2 h", ficha.reloj(120))
comprobar("horas y minutos", ficha.reloj(148) == "2 h 28 min", ficha.reloj(148))
comprobar("el limite de 90 no rompe", ficha.reloj(90) == "1 h 30 min", ficha.reloj(90))
comprobar("mas comodo tarda menos que mas exigente",
          cn.minutos(False) < cn.minutos(True))


print("Ficha: lo que no debe reventar")

vacio = Lib("Vacio", "", [])
comprobar("libro sin capitulos", ficha.caracteristicas(vacio).palabras == 0)
comprobar("capitulo vacio", ficha.caracteristicas(
    Lib("x", "", [Cap("I", "")])).palabras == 0)
comprobar("capitulo de una palabra", ficha.caracteristicas(
    Lib("x", "", [Cap("I", "Hola")])).frase_media >= 0)
comprobar("sinopsis sin cliente devuelve None",
          ficha.sinopsis(narrado, None) == (None, "sin_cliente"))
comprobar("sinopsis de un libro vacio devuelve None",
          ficha.sinopsis(vacio, object()) == (None, "sin_pasajes"))
# Seis capitulos distintos: se piden cuatro pasajes repartidos y tienen que
# salir cuatro y distintos. Con capitulos de texto identico esta comprobacion
# no dice nada, que fue como estaba escrita al principio.
seis = Lib("Seis", "", [Cap(f"C{i}", f"Chapter {i} begins here. " + NARRACION)
                        for i in range(6)])
pasajes = ficha._pasajes(seis)
comprobar("se sacan cuatro pasajes repartidos", len(pasajes) == 4, str(len(pasajes)))
comprobar("los pasajes son de capitulos distintos",
          len(set(pasajes)) == len(pasajes))
comprobar("el ultimo pasaje viene del final del libro",
          pasajes[-1].startswith("Chapter 5"), pasajes[-1][:20])
comprobar("un libro de un solo capitulo da un pasaje",
          len(ficha._pasajes(Lib("x", "", [Cap("I", NARRACION)]))) == 1)


print()
if fallos:
    print(f"FALLAN {len(fallos)}: " + ", ".join(fallos))
    sys.exit(1)
print("Todas las pruebas de la ficha pasan.")
