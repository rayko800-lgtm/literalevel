# -*- coding: utf-8 -*-
"""Pone al día entrega/documento.tex con el estado del 26 sep 2026.

Una lectura, todas las sustituciones en memoria (contadas sobre el original),
una escritura. Aborta sin escribir si una cuenta no cuadra.
'@' es la barra invertida (skill latex-en-esta-maquina)."""
import pathlib, sys

BS = chr(92)
RUTA = pathlib.Path(__file__).resolve().parent.parent / 'entrega' / 'documento.tex'


def tex(s):
    return s.replace('@', BS)


ARTICULATORIO = tex(r'''
@subsection{Un segundo modelo: la boca que se mueve como una real}
@label{sec:articulatorio}

La corrección de pronunciación enseña cómo se mueve la boca en cada sonido. Hasta el 25 de
septiembre de 2026 ese movimiento lo decidía una regla escrita a mano: una pose por fonema y
un calendario de transiciones (@cod{animacion.ts}). Una boca real no funciona así:
@textbf{coarticula} ---empieza a redondear los labios antes de llegar a una /uː/ y no cierra
igual una /p/ entre vocales abiertas que entre cerradas---. Se entrenó un modelo pequeño para
aprender ese movimiento de caras reales y se midió contra la regla.

@textbf{Datos, todos bajo CC BY 4.0.} GRID @parencite{cooke2006grid}: 33 hablantes, 32.936
frases y 27,4 horas de vídeo frontal; Lombard GRID @parencite{alghamdi2018lombard}: 54
hablantes y 5.385 frases medidas; y la articulografía electromagnética (EMA) de USC-TIMIT
@parencite{narayanan2014usctimit}: sensores en labios, mandíbula y lengua de tres hablantes,
1.450 frases. Otros conjuntos más grandes se descartaron por licencia ---de uso solo no
comercial o sin licencia publicada--- (@cod{investigacion/@allowbreak modelo@_articulatorio/@allowbreak informe@_decision.md}).

@textbf{Procesamiento.} Cada fotograma se mide con MediaPipe Face Landmarker
@parencite{lugaresi2019mediapipe}, que da 478 puntos y 52 coeficientes de expresión de la
cara; de ahí salen doce controles de la boca (apertura, ancho, mandíbula, protrusión, mejillas
y los coeficientes de los labios), normalizados por hablante (unidades $z$), porque lo que se
aprende es el movimiento y no la forma de cada cara. Los tiempos de cada fonema salen de
alinear audio y transcripción con Montreal Forced Aligner 3.4.2 @parencite{mcauliffe2017mfa}.

@textbf{Modelos comparados.} (1) @emph{Escalón}: la pose del fonema, sin transición.
(2) @emph{Reglas}: el calendario que usaba la aplicación, con las mismas poses objetivo
medidas, de modo que solo cambia la dinámica. (3) @emph{Dominancia}: el modelo clásico de
coarticulación de @textcite{cohen1993coarticulation}, en el que cada fonema tira de la boca con
un peso que decae con la distancia en el tiempo, con sus parámetros aprendidos por fonema y
control. (4) Una red convolucional temporal (TCN) @parencite{bai2018tcn} de 86.380 parámetros
(0,35 MB). La evaluación es sobre @textbf{hablantes que ningún modelo vio}: los cuatro últimos
de GRID (4.000 frases), seis de Lombard y, en la EMA, uno fuera cada vez.

@begin{table}[htbp]
@centering
@small
@begin{tabular}{ARROBA{}l c c cARROBA{}}
@toprule
@textbf{Modelo} & @textbf{GRID} (4 hablantes) & @textbf{Lombard} (6) & @textbf{EMA, lengua} (3 pruebas) @@
@midrule
Escalón & 0,432 & 0,364 & 0,40--0,46 @@
Reglas de la aplicación & 0,443 & 0,406 & 0,43--0,48 @@
Dominancia aprendida & 0,560 & 0,550 & 0,63--0,65 @@
TCN & @textbf{0,566} & @textbf{0,564} & @textbf{0,65--0,67} @@
@midrule
Reglas, con los tiempos que calcula la aplicación & 0,315 & 0,271 & --- @@
TCN entrenada con esos mismos tiempos & 0,530 & 0,498 & --- @@
@bottomrule
@end{tabular}
@caption[Modelo articulatorio contra las reglas]{Pearson medio entre el movimiento predicho y
el real, sobre hablantes no vistos. En GRID y Lombard es la media de los doce controles; en la
EMA, el rango de las tres pruebas. Fuente:
@cod{investigacion/@allowbreak modelo@_articulatorio/@allowbreak resultados.md}.}
@label{cuad:articulatorio}
@end{table}

@textbf{Lo que dice el cuadro~@ref{cuad:articulatorio}.} Aprender la dinámica mejora a las
reglas en los tres conjuntos: en GRID, de 0,443 a 0,560--0,566. Las reglas además llegan tarde
---60 ms en la mandíbula--- y en el redondeo anticipado van al revés: la cara real llega a
medio camino del redondeo unos 40 ms antes de /uː/ o /w/ (mediana), y las reglas, 20 ms
después. En el cierre de /p b m/, el mínimo de apertura cae a menos de 0,3 $z$ del real en el
73@pct{} de los casos con la dominancia, frente al 58@pct{} con las reglas. Pero la fila de
abajo es la importante: @textbf{con los tiempos de fonema que la aplicación sabía calcular, sin
alinear el audio, las reglas caen a 0,315}. Los tiempos pesaban tanto como el modelo.

@textbf{Decisión.} Con tiempos bien alineados, la dominancia empata con la TCN en labios y
mandíbula (0,560 frente a 0,566), cabe en unas tablas de 12,6 KB que el navegador lee sin red
neuronal y se explica fonema a fonema; la TCN solo gana en la lengua, por unas dos centésimas.
Se publicó la dominancia (25 de septiembre, revisión @cod{0f41932} del @emph{front}, del
commit @cod{de1498e}). Los tiempos de las 85 palabras grabadas de @emph{Pronunciar} se
alinearon de antemano, y las frases de la voz sintética se leen con las marcas por palabra que
la corrección ya guarda junto a su audio.

@textbf{Límites.} Es correlación con el movimiento de caras en vídeo, no una prueba de que la
boca 3D ayude a pronunciar mejor, que nadie ha medido con lectores. GRID no ve el contacto de
/f v/ (la cámara está lejos) y la protrusión desde un vídeo frontal es débil. Y la boca de la
aplicación es un corte de media cabeza, no una cara de vídeo: los controles se trasladan a ella
con una calibración por poses comunes, que es una decisión de diseño y no algo medido.

''').replace('ARROBA', '@')

NOVEDADES = tex(r'''

@medskip@noindent@textbf{Lo añadido entre el 16 y el 26 de septiembre.} Todo está publicado y
registrado en @cod{DESPLIEGUE.md}:

@begin{itemize}
  @item @textbf{Mi espacio}, la pantalla de inicio y primera pestaña: los libros empezados,
        las palabras pendientes de practicar y @emph{Mi progreso}, que enseña las palabras
        consultadas por día en las dos últimas semanas y los resultados de los últimos
        repasos, con las cifras siempre a la vista y sin gráficas en cero cuando todavía no
        hay datos. @textbf{Repasar} enseña hasta cinco palabras guardadas: el lector intenta
        recordarlas, ve la respuesta y dice si la sabía, dudó o no, y eso se guarda.
  @item @textbf{Leer en voz alta, en vivo.} En el lector, la aplicación escucha mientras se
        lee un pasaje y marca en el texto las palabras leídas, la actual y las saltadas; al
        terminar da un resumen con el ritmo. Usa un servicio de transcripción en tiempo real
        de pago, así que pide cuenta, gasta un uso por sesión y se corta a los tres minutos.
        Está probado de extremo a extremo con una lectura sintética; con la voz real de un
        lector, pendiente.
  @item @textbf{La boca 3D didáctica} y @textbf{los datos por cuenta}, descritos arriba, y el
        modelo que mueve la boca (apartado~@ref{sec:articulatorio}).
  @item @textbf{La marca Pléyade}: nombre, emblema, un texto «Sobre Pléyade» que se abre al
        pulsar el logo, y un fondo de galaxia en todas las pantallas, con cada una sobre una
        lámina translúcida de su tema (claro, noche o papel). @textbf{El contraste de este
        tema sobre la galaxia no se ha medido}: las pruebas de contraste del @emph{front}
        cubren las portadas y el lector teñido, no el fondo.
@end{itemize}''')

NOMBRES = tex(r'''

@textbf{Tres nombres para tres cosas.} Peldaño es la compañía; @textbf{Pléyade} es su
aplicación, el nombre que ve el lector desde el 26 de septiembre de 2026; y
@textbf{LiteraLevel} es el nombre del proyecto y de su modelo (@cod{literalevel-v4}). Los
repositorios, los Spaces de Hugging Face y el paquete de Python lo conservan a propósito:
renombrarlos habría roto los enlaces publicados y la descarga que hace el cuaderno. Una
@emph{pléyade} es un grupo de personas célebres de una misma época, sobre todo en las letras,
y las Pléyades son un cúmulo de estrellas de Tauro: el nombre junta la literatura y el cielo, y
el emblema ---un pegaso sobre un libro abierto cuyas páginas son alas--- lo dice en imagen.''')

CAMBIOS = [
    # --- nombre ------------------------------------------------------------
    ('%  LiteraLevel — Documento final', '%  Pléyade (proyecto LiteraLevel) — Documento final', 1),
    (tex('@color{llgris}LiteraLevel — Módulo 5 (Integrador)}'),
     tex('@color{llgris}Pléyade (proyecto LiteraLevel) — Módulo 5 (Integrador)}'), 1),
    (tex('{@Huge@bfseries@color{llazul} LiteraLevel@par}'),
     tex('{@Huge@bfseries@color{llazul} Pléyade@par}\n\n@vspace{0.15cm}\n\n{@large@color{llgris} proyecto LiteraLevel@par}'), 1),
    (tex('{@normalsize Ciudad de México, septiembre de 2026@par}'),
     tex('{@normalsize Ciudad de México, octubre de 2026@par}'), 1),
    ('LiteraLevel es una aplicación que responde esa pregunta.',
     'Pléyade, la aplicación del proyecto LiteraLevel, responde esa pregunta.', 1),
    ('propia y\nLiteraLevel no certifica ningún nivel', 'propia y\nPléyade no certifica ningún nivel', 1),
    ('resolver solo. LiteraLevel convierte', 'resolver solo. Pléyade convierte', 1),
    (tex('@textbf{LiteraLevel no certifica'), tex('@textbf{Pléyade no certifica'), 1),
    ('del entrenamiento. LiteraLevel no acredita', 'del entrenamiento. Pléyade no acredita', 1),
    ('LiteraLevel es una herramienta de apoyo a la lectura.',
     'Pléyade es una herramienta de apoyo a la lectura.', 1),
    ('se reconstruye con su manifiesto.\n\nEl nombre no es decorativo.',
     'se reconstruye con su manifiesto.' + NOMBRES + '\n\nEl nombre de la compañía no es decorativo.', 1),
    # --- resumen ------------------------------------------------------------
    (tex('La entrega usa @textbf{Angular como interfaz y una API FastAPI sobre el motor Python};\n'
         'Gradio 6.26 @parencite{abid2019gradio} se conserva como respaldo.'),
     tex('La entrega usa @textbf{Angular como interfaz}, publicada en Vercel\n'
         '(@url{https://pleyade-app.vercel.app}), y @textbf{una API FastAPI sobre el motor Python} en\n'
         'Hugging Face; Gradio 6.26 @parencite{abid2019gradio} se conserva como respaldo. Un segundo\n'
         'modelo, pequeño y aprendido de vídeos de caras reales, mueve la boca 3D con la que la\n'
         'aplicación enseña a pronunciar (apartado~@ref{sec:articulatorio}).'), 1),
    ('Project Gutenberg, Angular.', 'Project Gutenberg, Angular, coarticulación.', 1),
    # --- la interfaz entregada ----------------------------------------------
    (tex('independientes, sin @cod{zone.js}) publicada como @textbf{Space estático} de\n'
         '        Hugging Face (@cod{MikeMaki1763/@allowbreak literalevel-front}), gratuito y siempre\n'
         '        despierto: es HTML, CSS y JavaScript ya compilados. Tiene cuatro sitios en vez de\n'
         '        ocho pestañas —@emph{Leer}, @emph{Encontrar}, @emph{Pronunciar} y @emph{Tu\n'
         '        nivel}—, más @emph{Mis palabras}; los ajustes (paleta, tamaño de letra, idioma de\n'
         '        las explicaciones)'),
     tex('independientes, sin @cod{zone.js}): HTML, CSS y JavaScript ya compilados, así que\n'
         '        no se duerme. Desde el 26 de septiembre de 2026 se publica en @textbf{Vercel}\n'
         '        (@url{https://pleyade-app.vercel.app}, plan gratuito), como pidió el profesor, y se\n'
         '        vuelve a publicar sola con cada cambio de la rama principal del repositorio; el\n'
         '        @textbf{Space estático} de Hugging Face (@cod{MikeMaki1763/@allowbreak literalevel-front})\n'
         '        sirve la misma aplicación como respaldo. Tiene cinco sitios en vez de ocho\n'
         '        pestañas —@emph{Mi espacio}, @emph{Leer}, @emph{Encontrar}, @emph{Pronunciar} y\n'
         '        @emph{Tu nivel}—, más @emph{Mis palabras} y @emph{Repasar}; los ajustes (tema,\n'
         '        tamaño de letra, idioma de las explicaciones)'), 1),
    (tex('40 rutas bajo @cod{/api} a fecha de @cod{8ee42f0}, el @cod{app/} que publica el Space en su revisión @cod{7c09d90}, subida desde @cod{ab4e36f})'),
     tex('44 rutas bajo @cod{/api} a fecha de @cod{06a16db}, el commit que publica el Space en su revisión @cod{103eef5})'), 1),
    (tex('viaja en una cabecera (@cod{X-Lector}) y sus datos siguen en el bucket montado en\n        @cod{/data}.'),
     tex('viaja en una cabecera (@cod{X-Lector}) y sus datos siguen en el bucket montado en\n        @cod{/data}. '
         'Desde el 26 de septiembre, quien entra con usuario y contraseña deja de ser un\n'
         '        navegador: sus libros, sus palabras y su nivel pasan a ser @textbf{de la cuenta}\n'
         '        (@cod{cuentas/}@emph{nombre} en el bucket) y se ven igual en el teléfono, la tableta\n'
         '        o el equipo; sin cuenta siguen siendo de ese navegador. Salió de un caso real: con\n'
         '        la misma cuenta, el teléfono y la tableta del autor enseñaban dos lectores\n'
         '        distintos.'), 1),
    (tex('@cod{d58b0be}.\n@end{itemize}'),
     tex('@cod{d58b0be}. La última publicación de la API (26 de septiembre, revisión\n'
         '        @cod{103eef5} del Space, del commit @cod{06a16db}) pasó 70 de 70 pruebas API, las\n'
         '        extremas sin fallos y 464 de 464 del @emph{front}; en vivo, la misma cuenta entró\n'
         '        desde dos aparatos nuevos y los dos vieron los mismos datos (@cod{DESPLIEGUE.md}).\n'
         '@end{itemize}'), 1),
    (tex('@noindent@textbf{Boca 3D y portadas, a fecha de la revisión @cod{ec957d0} del @emph{front} (del commit @cod{4e6276e}).} '
         'La boca 3D ya está publicada: el @emph{front} sirve @cod{boca3d/cara.glb} y @cod{lengua.glb}, idénticos byte a byte a los del repositorio, '
         'con 72 mallas entre los dos y respaldo 2D si no cargan. La piel de la media cabeza sale de la malla base de MakeHuman 1.3.0, '
         'publicada bajo CC0 1.0 (no obliga a atribuir) @parencite{makehuman_licencia}; paladar, velo, encías, dientes y lengua son modelos propios, '
         'y sus 53 poses se validan contra ellos. Es un corte esquemático, no anatomía validada clínicamente. '),
     tex('@noindent@textbf{Boca 3D, a 26 de septiembre de 2026.} En @emph{Pronunciar}, junto al corte 2D, '
         'hay una boca 3D didáctica que se descarga solo al abrirla, con el corte 2D de respaldo si no carga. '
         'La cabeza parte de un escaneo publicado bajo CC BY 3.0 ---@emph{Infinite, 3D Head Scan}, de Lee Perry-Smith '
         '@parencite{perrysmith_infinite}---, cuya atribución se sirve con el modelo; los labios, la lengua, el corte '
         'anatómico y los materiales son adaptación propia en Blender. Enseña el aire y la vibración de cada sonido, '
         'lee palabras y frases al compás del audio ---con el modelo del apartado~@ref{sec:articulatorio}---, y tiene '
         'zoom, cámara lenta («Despacio») y giro libre («Explorar»). El 26 de septiembre sus texturas pasaron a WebP y '
         'lo que baja por la red se quedó en 1,4 MB en vez de 3,5 (commit @cod{1f5f2c9}). Es un corte esquemático, '
         'no anatomía validada clínicamente. '), 1),
    (tex('Su calidad visual sigue sin comprobarse. El enlace del lector es\n@url{https://mikemaki1763-literalevel-front.static.hf.space/}.'),
     tex('Su calidad visual sigue sin comprobarse. El enlace del lector es\n@url{https://pleyade-app.vercel.app}, y el de respaldo,\n@url{https://mikemaki1763-literalevel-front.static.hf.space/}.'), 1),
    (tex('Las 40 rutas API se contaron en el código a fecha de @cod{8ee42f0}.'),
     tex('Las 44 rutas API se contaron en el código a fecha de @cod{06a16db}.'), 1),
    ('y el guion de la demostración la vuelve a comprobar con cuenta antes de enseñarla.\n\n' + tex('@subsection{Accionables}'),
     'y el guion de la demostración la vuelve a comprobar con cuenta antes de enseñarla.' + NOVEDADES + '\n\n' + tex('@subsection{Accionables}'), 1),
    # --- accionables ----------------------------------------------------------
    (tex('y el Space estático del @emph{front} es gratuito'),
     tex('y el @emph{front}, en Vercel y en el Space estático, es gratuito'), 1),
    (tex('@textbf{HECHO}: @cod{MikeMaki1763/@allowbreak literalevel-@allowbreak front} (el @emph{front}) y @cod{MikeMaki1763/@allowbreak literalevel} (API y motor), públicos y en marcha;'),
     tex('@textbf{HECHO}: el @emph{front} en Vercel (@url{https://pleyade-app.vercel.app}), con respaldo en @cod{MikeMaki1763/@allowbreak literalevel-@allowbreak front}, y @cod{MikeMaki1763/@allowbreak literalevel} (API y motor), públicos y en marcha;'), 1),
    ('se reinició el Space y el perfil seguía ahí \\\\',
     'se reinició el Space y el perfil seguía ahí. Desde el 26 de septiembre, con cuenta, los datos son de la cuenta y se ven en cualquier aparato \\\\', 1),
    (tex('@textbf{A5} & @textbf{Conseguir un micrófono}'), tex('@textbf{A5 · HECHO} & @textbf{Conseguir un micrófono}'), 1),
    ('Coste mínimo de hardware & Se graba una frase desde el equipo del autor y la corrección palabra por palabra aparece en pantalla',
     tex('Coste mínimo de hardware & @textbf{Cumplido con el teléfono}: el 16 de septiembre, desde el teléfono del autor y con cuenta, el micrófono grabó y la corrección salió; se vuelve a ensayar antes de la demo'), 1),
    ('ensayar la voz con micrófono real\n(A5), recorrer',
     'volver a ensayar la voz con cuenta\n(A5), recorrer', 1),
    # --- métricas ---------------------------------------------------------------
    (tex('& @textbf{Cumplido}: las ochenta y cinco parejas de color de las cinco paletas superan WCAG AA; las más ajustadas, 4,53 (texto) y 3,11 (título) @@'),
     tex('& @textbf{Cumplido en la interfaz anterior}: las ochenta y cinco parejas de color de las cinco paletas de Gradio superan WCAG AA; las más ajustadas, 4,53 (texto) y 3,11 (título). En el @emph{front}, las portadas y el lector teñido tienen pruebas de contraste; el tema de la marca sobre el fondo de galaxia, @textbf{sin medir} @@'), 1),
    (tex('del corte anterior @cod{d58b0be}; no equivalen a una prueba completa de usuario @@'),
     tex('del corte anterior @cod{d58b0be}; la última publicación de la API (26 de septiembre, @cod{06a16db}): API 70 de 70, extremas sin fallos y @emph{front} 464 de 464. No equivalen a una prueba completa de usuario @@'), 1),
    (tex('@textbf{Cumplido}: el @emph{front} en @cod{MikeMaki1763/@allowbreak literalevel-front} y la API con el motor en @cod{MikeMaki1763/@allowbreak literalevel}, los dos en Hugging Face Spaces, públicos y en marcha, con los datos del lector en un bucket montado en @cod{/data}'),
     tex('@textbf{Cumplido}: el @emph{front} en Vercel (@url{https://pleyade-app.vercel.app}), con respaldo en @cod{MikeMaki1763/@allowbreak literalevel-front}, y la API con el motor en @cod{MikeMaki1763/@allowbreak literalevel}, en Hugging Face Spaces, con los datos del lector o de su cuenta en un bucket montado en @cod{/data}'), 1),
    # --- decisiones del lector ------------------------------------------------------
    ('¿Lo estoy pronunciando bien? & Lectura en voz alta marcada palabra por palabra, con el sonido concreto que falla & Una frase \\\\',
     tex('¿Lo estoy pronunciando bien? & Lectura en voz alta marcada palabra por palabra, con el sonido concreto que falla y cómo se mueve la boca, en corte 2D o en 3D; en el lector, un pasaje leído en vivo con las palabras saltadas marcadas & Una frase; el pasaje en vivo, hasta tres minutos @@\n@addlinespace\n¿Cómo voy? & @emph{Mi espacio}: libros empezados, palabras consultadas por día y resultados de los repasos; con cuenta, lo mismo en cualquier aparato & Nada @@'), 1),
    # --- el nuevo modelo -----------------------------------------------------------
    ('rechazados con su motivo.\n\n', 'rechazados con su motivo.\n' + ARTICULATORIO, 1),
    # --- limitaciones -----------------------------------------------------------------
    (tex('La aplicación está publicada en dos Spaces de Hugging Face con\n'
         '        dirección fija que sobrevive a apagar el equipo del autor: el @emph{front} de\n'
         '        Angular en un Space estático (@cod{MikeMaki1763/@allowbreak literalevel-front}),\n'
         '        gratuito y sin suspensión, y la API'),
     tex('La aplicación está publicada con\n'
         '        dirección fija que sobrevive a apagar el equipo del autor: el @emph{front} de\n'
         '        Angular en Vercel (@url{https://pleyade-app.vercel.app}) y, de respaldo, en un Space\n'
         '        estático (@cod{MikeMaki1763/@allowbreak literalevel-front}), los dos gratuitos y sin\n'
         '        suspensión, y la API'), 1),
    ('el perfil del lector se guardan en un', 'el perfil del lector ---o de su cuenta--- se guardan en un', 1),
    # --- trabajo futuro -----------------------------------------------------------------
    (tex('  @item @textbf{Convertir las cinco acciones'),
     tex('  @item @textbf{Una cara que habla de frente.} La boca 3D enseña la articulación en corte;\n'
         '        una cara completa que lea las frases de frente (@emph{Eos}, sobre un MetaHuman de\n'
         '        Epic) está en desarrollo y @textbf{no forma parte de esta entrega}.\n'
         '  @item @textbf{Convertir las cinco acciones'), 1),
    # --- conclusiones --------------------------------------------------------------------
    (tex('---el @emph{front} de Angular en un Space estático y la API con el motor en otro---'),
     tex('---el @emph{front} de Angular en Vercel, con un respaldo en Hugging Face, y la API con el\nmotor en un Space---'), 1),
    (tex('optimizar, y medir también lo que se descarta.}\n\n'),
     tex('optimizar, y medir también lo que se descarta.}\n\n'
         '@textbf{La misma lección, en el segundo modelo.} Para mover la boca 3D, un modelo aprendido\n'
         'de caras reales supera a las reglas escritas a mano ---Pearson 0,566 frente a 0,443 con\n'
         'hablantes que no vio---, pero con los tiempos de fonema que la aplicación sabía calcular las\n'
         'reglas caían a 0,315: los datos de entrada pesaban tanto como el modelo. Y entre la red y\n'
         'unas tablas de 12,6 KB que empataban con ella se eligieron las tablas, por coste y porque se\n'
         'explican fonema a fonema (apartado~@ref{sec:articulatorio}).\n\n'), 1),
    # --- alcance -----------------------------------------------------------------------------
    ('perfil de nivel— se guardan separados por navegador y no se comparten entre visitantes.',
     'perfil de nivel— se guardan separados por cuenta, o por navegador si no se entra, y no se\ncomparten entre lectores.', 1),
]


def main():
    crlf = bytes([13, 10]) in RUTA.read_bytes()
    original = RUTA.read_text(encoding='utf-8')
    t = original
    malos = []
    for viejo, nuevo, esperadas in CAMBIOS:
        n = original.count(viejo)
        if n != esperadas:
            malos.append((n, esperadas, viejo[:90]))
        t = t.replace(viejo, nuevo)
    if malos:
        for m in malos:
            print('NO CUADRA', m)
        sys.exit(1)
    assert chr(9) + 'extbf' not in t and '/usr/bin/bash' not in t
    RUTA.write_text(t, encoding='utf-8', newline=chr(13) + chr(10) if crlf else chr(10))
    print('ok', len(CAMBIOS), 'cambios')


if __name__ == '__main__':
    main()
