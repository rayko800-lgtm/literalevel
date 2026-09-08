"""Reescribe la portada del documento con la maquetacion del modulo 4 de Miguel.

Tres cambios, y los tres los pidio el al leer el PDF.

1. **Los escudos.** Son las UNICAS imagenes externas del documento, y tienen
   motivo: un escudo es una marca institucional, no una figura de datos.
   Dibujarlo en TikZ seria a la vez inexacto y presuntuoso. Las doce figuras
   del documento siguen dibujadas.

2. **La cohesion.** Los archivos son LOS SUYOS, sacados de su propio Overleaf
   (`Proyecto final modulo 4. Redes neuronales`), no unos parecidos bajados de
   internet. Y la maquetacion es la misma que uso alli: los dos escudos a los
   lados a 2,7 cm con el nombre de la institucion en medio, y luego titulo,
   alumno, profesor, diplomado. Asi el documento no se siente cosido a mano.

3. **El orden.** El sello de cifras estaba ENTRE el subtitulo y el autor, que
   es lo que se le hizo raro. Una portada academica presenta primero quien
   firma y bajo la supervision de quien; los resultados apoyan, no encabezan.
   El sello baja al pie.

Se ejecuta desde `entrega/`:  python -X utf8 _portada.py
"""
import pathlib

NUEVA = r"""\begin{titlepage}
\centering

% --- Escudos institucionales -------------------------------------------
% Misma maquetacion que el proyecto del modulo 4, y con sus mismos archivos.
% Son las UNICAS imagenes externas del documento: un escudo es una marca
% institucional, no una figura de datos. Las doce figuras siguen en TikZ.
\begin{minipage}{0.25\textwidth}
    \raggedright
    \includegraphics[height=2.7cm]{logos/logo_unam.png}
\end{minipage}
\hfill
\begin{minipage}{0.45\textwidth}
    \centering
    {\Large\bfseries Universidad Nacional Autónoma de México\par}

    \vspace{0.2cm}

    {\large FACULTAD DE ESTUDIOS SUPERIORES ACATLÁN\par}
\end{minipage}
\hfill
\begin{minipage}{0.25\textwidth}
    \raggedleft
    \includegraphics[height=2.7cm]{logos/logo_fes_acatlan.png}
\end{minipage}

\vspace{2.0cm}

{\Huge\bfseries\color{llazul} LiteraLevel\par}

\vspace{0.6cm}

{\LARGE Medición automática de la dificultad de lectura\\[0.25cm]
en inglés y su entrega a un lector real\par}

\vspace{1.8cm}

{\Large\bfseries Proyecto integrador --- Módulo 5\par}

\vspace{1.2cm}

{\large
\textbf{Alumno:}\\
Miguel Reyes Carrillo
\par}

\vspace{0.7cm}

{\large
\textbf{Profesor:}\\
Mtro. Fernando Barranco Rodríguez
\par}

\vspace{0.7cm}

{\large
Diplomado en Ciencia de Datos --- Generación 34
\par}

\vfill

% El sello de cifras al pie: apoya, no encabeza.
\begin{tikzpicture}[font=\small]
  \node[draw=llazul!35, fill=llfondo, rounded corners=6pt, line width=0.8pt,
        inner sep=9pt, text width=12.4cm, align=center] (caja) {
    \begin{minipage}{12.1cm}
      \centering
      \begin{tabular}{@{}C{3.6cm}C{4.0cm}C{3.3cm}@{}}
        {\large\bfseries\color{llcian} 0,908} & {\large\bfseries\color{llverde} A1 $<\cdots<$ C1} & {\large\bfseries\color{llambar} 97,2\pct} \\[2pt]
        {\scriptsize Spearman, validación ciega} & {\scriptsize orden MCER creciente en corpus externo} & {\scriptsize dentro de $\pm 1$ nivel} \\
      \end{tabular}
    \end{minipage}};
\end{tikzpicture}

\vspace{0.6cm}

{\normalsize Ciudad de México, septiembre de 2026\par}

\end{titlepage}"""


def main() -> int:
    p = pathlib.Path("documento.tex")
    s = p.read_text(encoding="utf-8")

    a = s.index(r"\begin{titlepage}")
    b = s.index(r"\end{titlepage}") + len(r"\end{titlepage}")
    s = s[:a] + NUEVA + s[b:]

    # `graphicx` hace falta ahora que hay escudos; antes no habia ni una imagen.
    if r"\usepackage{graphicx}" not in s:
        s = s.replace(r"\usepackage{iftex}",
                      "\\usepackage{iftex}\n\\usepackage{graphicx}", 1)

    p.write_text(s, encoding="utf-8")
    print("portada reescrita al estilo del modulo 4")
    print("  graphicx:", r"\usepackage{graphicx}" in s)
    print("  escudos :", s.count("logos/"), "referencias")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
