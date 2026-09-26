# -*- coding: utf-8 -*-
"""Pone al día entrega/presentacion.tex (26 sep 2026). '@' es la barra invertida."""
import pathlib, sys

BS = chr(92)
RUTA = pathlib.Path(__file__).resolve().parent.parent / 'entrega' / 'presentacion.tex'


def tex(s):
    return s.replace('@', BS)


ARTICULATORIO = tex(r'''% ===========================================================================
@begin{frame}{Segundo modelo · la boca que se mueve como una real}
@vspace{1mm}
{@small La boca 3D de @emph{Pronunciar} ya no sigue reglas escritas a mano: aprendió
el movimiento de @textbf{vídeos de caras reales} (GRID y Lombard GRID) y de sensores en
la lengua (USC-TIMIT), todos CC BY 4.0.}
@vspace{2mm}
@begin{center}
@begin{tikzpicture}
@begin{axis}[
  width=0.86@linewidth, height=4.3cm, xbar, bar width=9pt, bar shift=0pt,
  xmin=0, xmax=0.72, xlabel={Pearson con el movimiento real, 4 hablantes no vistos (GRID)},
  symbolic y coords={tcn,dom,reglas,app},
  ytick={app,reglas,dom,tcn},
  yticklabels={Reglas con los tiempos de la app,Reglas de antes,Dominancia aprendida,Red TCN},
  yticklabel style={font=@scriptsize}, tick style={draw=none},
  xmajorgrids=true, grid style={llgrisclaro},
  axis line style={draw=llgrisclaro}, enlarge y limits=0.25,
  nodes near coords={@pgfmathprintnumber[fixed,precision=3]{@pgfplotspointmeta}},
  nodes near coords style={font=@scriptsize, color=llgris},
  nodes near coords align={horizontal},
]
@addplot[fill=llgris!25, draw=llgris!60] coordinates {(0.315,app) (0.443,reglas)};
@addplot[fill=llcian!45, draw=llcian!90] coordinates {(0.560,dom) (0.566,tcn)};
@end{axis}
@end{tikzpicture}
@end{center}
@vspace{-1mm}
{@footnotesize @textbf{Se publicó la dominancia}: empata con la red, cabe en tablas de
12,6 KB y se explica fonema a fonema. Y la lección es la del primer modelo: @textbf{los
datos de entrada pesaban tanto como el modelo} ---con los tiempos de fonema mal medidos,
las reglas caían a 0,315---.}

@vspace{1mm}
{@scriptsize@color{llgris} Correlación con caras en vídeo, no una prueba de que ayude a
pronunciar mejor. Documento, apartado 7.8.}
@end{frame}

''')

CAMBIOS = [
    ('%  LiteraLevel — Presentación', '%  Pléyade (proyecto LiteraLevel) — Presentación', 1),
    ('    LiteraLevel · Módulo 5 ', '    Pléyade · proyecto LiteraLevel · Módulo 5 ', 1),
    (tex('@title{LiteraLevel}'), tex('@title{Pléyade}'), 1),
    (tex('@date{Septiembre de 2026}'), tex('@date{Octubre de 2026}'), 1),
    (tex('  {@Huge@bfseries@color{llazul} LiteraLevel}@@[6pt]'),
     tex('  @includegraphics[height=1.5cm]{logos/pleyade_icono.png}@@[3pt]\n'
         '  {@Huge@bfseries@color{llazul} Pléyade}@@[1pt]\n'
         '  {@small@color{llgris} proyecto LiteraLevel}@@[5pt]'), 1),
    (tex('{@small Angular es la interfaz del lector; la API conecta con el motor de Python.}'),
     tex('{@small Angular es la interfaz del lector, en Vercel; la API conecta con el motor de Python.}'), 1),
    (tex('@node[caja] (f) {@textbf{Front · Angular 22}@@ Interfaz entregada@@\n'
         '  Space estático@@ @emph{Leer · Encontrar · Pronunciar · Tu nivel}};'),
     tex('@node[caja] (f) {@textbf{Front · Angular 22}@@ En Vercel; respaldo en@@\n'
         '  un Space estático@@ @emph{Mi espacio · Leer · Encontrar@@ Pronunciar · Tu nivel}};'), 1),
    (tex('  Space de Gradio,@@ @cod{cpu-basic}; Gradio@@ en la raíz, de respaldo};'),
     tex('  Space de Gradio,@@ @cod{cpu-basic}; datos@@ por cuenta en un bucket};'), 1),
    (tex('{@small Boca 3D publicada: 72 mallas, con la piel de la cabeza de MakeHuman (CC0).\n'
         'Se carga al abrirla, con respaldo 2D. Apoyo didáctico, no clínico.}'),
     tex('{@small Boca 3D didáctica: cabeza escaneada (CC BY 3.0), labios, lengua y corte\n'
         'propios; se mueve con un modelo aprendido. Respaldo 2D. Didáctica, no clínica.}'), 1),
    (tex('{@small Lo añadido en los dos últimos días, ya publicado en el @emph{front}.}'),
     tex('{@small Publicado en el @emph{front}. Además: @emph{Mi espacio} con el progreso,\n'
         '@emph{Repasar}, lectura en voz alta en vivo y datos de la cuenta en cualquier aparato.}'), 1),
    (tex('% ===========================================================================\n@begin{frame}{La aplicación entregada}'),
     ARTICULATORIO + tex('% ===========================================================================\n@begin{frame}{La aplicación entregada}'), 1),
    ('Servir interfaz y motor & Angular estático + API en Space de Gradio;',
     'Servir interfaz y motor & Angular en Vercel + API en Space de Gradio;', 1),
    (tex('{@large@ttfamily mikemaki1763-literalevel-front.static.hf.space}'),
     tex('{@large@ttfamily pleyade-app.vercel.app}'), 1),
]


def main():
    crlf = bytes([13, 10]) in RUTA.read_bytes()
    original = RUTA.read_text(encoding='utf-8')
    malos = [(original.count(v), v[:80]) for v, _, n in CAMBIOS if original.count(v) != n]
    if malos:
        for m in malos:
            print('NO CUADRA', m)
        sys.exit(1)
    t = original
    for v, nuevo, _ in CAMBIOS:
        t = t.replace(v, nuevo)
    assert chr(9) + 'extbf' not in t
    RUTA.write_text(t, encoding='utf-8', newline=chr(13) + chr(10) if crlf else chr(10))
    print('ok', len(CAMBIOS))


main()
