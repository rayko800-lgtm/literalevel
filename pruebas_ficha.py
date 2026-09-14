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
# 7d846fa: la sinopsis ya NO recibe el ultimo capitulo, para que no pueda
# destripar el final (informe final de f4, punto 9). El ultimo pasaje sale como
# mucho de los dos tercios: en seis capitulos, del 4, y nunca del 5.
comprobar("el ultimo pasaje sale de los dos tercios del libro",
          pasajes[-1].startswith("Chapter 4"), pasajes[-1][:20])
comprobar("ningun pasaje sale del ultimo capitulo",
          not any(p.startswith("Chapter 5") for p in pasajes))
for n_caps in (2, 3, 6, 9):
    libro_n = Lib(f"L{n_caps}", "", [Cap(f"C{i}", f"Chapter {i} begins here. " + NARRACION)
                                     for i in range(n_caps)])
    usados = [int(p.split()[1]) for p in ficha._pasajes(libro_n)]
    comprobar(f"{n_caps} capitulos: nunca el ultimo y como mucho a los dos tercios",
              bool(usados) and n_caps - 1 not in usados and max(usados) <= (2 * n_caps) // 3,
              str(usados))
comprobar("un libro de un solo capitulo da un pasaje",
          len(ficha._pasajes(Lib("x", "", [Cap("I", NARRACION)]))) == 1)
# Y lo que se manda a OpenAI va RECORTADO. Ninguna prueba aseveraba ese tope:
# quitarlo mandaba el capitulo entero -90.000 palabras en un libro largo- en
# cada uno de los cuatro pasajes. La prueba de "lo que viaja a OpenAI va
# recortado" de `pruebas_extremas.py` solo cubre la consulta lexica.
largo = Lib("Largo", "", [Cap(f"C{i}", "word " * 4000) for i in range(6)])
tamanos = [len(p.split()) for p in ficha._pasajes(largo)]
comprobar("ningun pasaje de la sinopsis viaja entero",
          all(t <= ficha._TOPE_EXTRACTO for t in tamanos), str(tamanos))
comprobar("el tope del pasaje es el que se documenta",
          ficha._TOPE_EXTRACTO == 900, str(ficha._TOPE_EXTRACTO))
# El separador de miles. En espanol es el PUNTO, y `f"{n:,}"` usa la coma, que
# aqui es el decimal. La app llego a decir "1,197 libros" y "130,104 palabras"
# en la misma pantalla en la que el documento escribe 1.197 y 130.104. Volver a
# `format(int(n), ",")` no rompia ninguna prueba.
comprobar("los miles llevan punto, no coma",
          ficha.miles(1197) == "1.197" and ficha.miles(203699) == "203.699",
          f"{ficha.miles(1197)} / {ficha.miles(203699)}")
comprobar("los numeros pequenos no se tocan",
          ficha.miles(840) == "840", ficha.miles(840))
# Y el tope de la muestra con la que se cuentan dialogo, frase media y riqueza:
# el documento lo publica, y bajarlo a 6.000 cambiaba esas tres cifras sin que
# fallara nada.
comprobar("el tope de la muestra es el que se documenta",
          ficha._muestra.__defaults__[0] == 60000,
          str(ficha._muestra.__defaults__[0]))


print("Ficha: los capitulos a tu nivel")

# Una curva de juguete con lo que trae un analisis de verdad: indice real,
# dificultad en escala 0..2 y palabras. El libro entero va por encima de un
# lector de 1,0, pero tiene capitulos que puede leer.
CURVA = [
    {"capitulo": 1, "indice": 2, "dificultad": 1.60, "palabras": 4000},
    {"capitulo": 2, "indice": 3, "dificultad": 1.10, "palabras": 4000},
    {"capitulo": 3, "indice": 4, "dificultad": 0.40, "palabras": 4000},
    {"capitulo": 4, "indice": 5, "dificultad": 0.95, "palabras": 4000},
    {"capitulo": 5, "indice": 6, "dificultad": 1.15, "palabras": 4000},
    {"capitulo": 6, "indice": 7, "dificultad": 1.00, "palabras": 300},
]
sel = ficha.capitulos_a_tu_nivel(CURVA, 1.0, 0.15)
comprobar("capitulos a tu nivel: sin filas no hay nada",
          ficha.capitulos_a_tu_nivel([], 1.0, 0.15) == []
          and ficha.capitulos_a_tu_nivel(None, 1.0, 0.15) == [])
comprobar("capitulos a tu nivel: todos por encima no devuelve nada",
          ficha.capitulos_a_tu_nivel(CURVA, 0.0, 0.15) == [],
          str(ficha.capitulos_a_tu_nivel(CURVA, 0.0, 0.15)))
comprobar("capitulos a tu nivel: no recomienda uno por encima del margen",
          all(f["dificultad"] <= 1.15 for f in sel) and 2 not in {f["indice"] for f in sel},
          str([f["indice"] for f in sel]))
comprobar("capitulos a tu nivel: el borde del margen entra",
          6 in {f["indice"] for f in sel}, str([f["indice"] for f in sel]))
comprobar("capitulos a tu nivel: un capitulo corto no se recomienda",
          7 not in {f["indice"] for f in sel}, str([f["indice"] for f in sel]))
comprobar("capitulos a tu nivel: el orden es por cercania, no por facilidad",
          [f["indice"] for f in sel] == [5, 3, 6, 4], str([f["indice"] for f in sel]))
comprobar("capitulos a tu nivel: el tope corta",
          len(ficha.capitulos_a_tu_nivel(CURVA, 1.0, 0.15, tope=2)) == 2)
comprobar("capitulos a tu nivel: una fila sin indice se salta sin reventar",
          ficha.capitulos_a_tu_nivel([{"dificultad": 0.5, "palabras": 5000}], 1.0, 0.15) == [])
comprobar("capitulos a tu nivel: un nivel que no es numero da lista vacia",
          ficha.capitulos_a_tu_nivel(CURVA, None, 0.15) == [])


print("Ficha: alinear con el catalogo")

CUERPO = "The rain fell on the quiet moor and the train ran west. " * 30
con_portada = Lib("Libro", "A", [Cap("Title", "Project Gutenberg title page " * 3),
                                  Cap("CHAPTER I", CUERPO), Cap("CHAPTER II", CUERPO),
                                  Cap("CHAPTER III", CUERPO)])
filas_cat = [{"capitulo": 1, "indice": 0, "titulo": "Chapter I"},
             {"capitulo": 2, "indice": 1, "titulo": "Chapter II"},
             {"capitulo": 3, "indice": 2, "titulo": "Chapter III"}]
mapa = ficha.alinear_con_catalogo(con_portada, filas_cat)
comprobar("alinear: traduce al indice de ESTE libro, no al del catalogo",
          mapa == {1: 1, 2: 2, 3: 3}, str(mapa))
comprobar("alinear: con distinto numero de capitulos no alinea",
          ficha.alinear_con_catalogo(con_portada, filas_cat[:2]) == {})
otro = [dict(f) for f in filas_cat]
otro[1]["titulo"] = "Chapter XX"
comprobar("alinear: un titulo distinto en su posicion no alinea",
          ficha.alinear_con_catalogo(con_portada, otro) == {})
comprobar("alinear: sin filas o con filas rotas no revienta",
          ficha.alinear_con_catalogo(con_portada, []) == {}
          and ficha.alinear_con_catalogo(con_portada, [{"titulo": "x"}]) == {})


print()
if fallos:
    print(f"FALLAN {len(fallos)}: " + ", ".join(fallos))
    sys.exit(1)
print("Todas las pruebas de la ficha pasan.")
