# -*- coding: utf-8 -*-
"""Pone al día entrega/documento.md (copia de lectura) con los mismos cambios
que documento.tex del 26 sep 2026. Una lectura, sustituciones contadas sobre el
original, una escritura; aborta sin escribir si algo no cuadra."""
import pathlib, sys

RUTA = pathlib.Path(__file__).resolve().parent.parent / 'entrega' / 'documento.md'

ARTICULATORIO = '''
### 7.8 Un segundo modelo: la boca que se mueve como una real

La corrección de pronunciación enseña cómo se mueve la boca en cada sonido.
Hasta el 25 de septiembre de 2026 ese movimiento lo decidía una regla escrita a
mano: una pose por fonema y un calendario de transiciones (`animacion.ts`). Una
boca real no funciona así: **coarticula** —empieza a redondear los labios antes
de llegar a una /uː/ y no cierra igual una /p/ entre vocales abiertas que entre
cerradas—. Se entrenó un modelo pequeño para aprender ese movimiento de caras
reales y se midió contra la regla.

**Datos, todos bajo CC BY 4.0.** GRID (Cooke et al., 2006): 33 hablantes,
32.936 frases y 27,4 horas de vídeo frontal; Lombard GRID (Alghamdi et al.,
2018): 54 hablantes y 5.385 frases medidas; y la articulografía
electromagnética (EMA) de USC-TIMIT (Narayanan et al., 2014): sensores en
labios, mandíbula y lengua de tres hablantes, 1.450 frases. Otros conjuntos más
grandes se descartaron por licencia —de uso solo no comercial o sin licencia
publicada— (`investigacion/modelo_articulatorio/informe_decision.md`).

**Procesamiento.** Cada fotograma se mide con MediaPipe Face Landmarker
(Lugaresi et al., 2019), que da 478 puntos y 52 coeficientes de expresión de la
cara; de ahí salen doce controles de la boca (apertura, ancho, mandíbula,
protrusión, mejillas y los coeficientes de los labios), normalizados por
hablante (unidades *z*), porque lo que se aprende es el movimiento y no la forma
de cada cara. Los tiempos de cada fonema salen de alinear audio y transcripción
con Montreal Forced Aligner 3.4.2 (McAuliffe et al., 2017).

**Modelos comparados.** (1) *Escalón*: la pose del fonema, sin transición.
(2) *Reglas*: el calendario que usaba la aplicación, con las mismas poses
objetivo medidas, de modo que solo cambia la dinámica. (3) *Dominancia*: el
modelo clásico de coarticulación de Cohen y Massaro (1993), en el que cada
fonema tira de la boca con un peso que decae con la distancia en el tiempo, con
sus parámetros aprendidos por fonema y control. (4) Una red convolucional
temporal (TCN; Bai et al., 2018) de 86.380 parámetros (0,35 MB). La evaluación
es sobre **hablantes que ningún modelo vio**: los cuatro últimos de GRID (4.000
frases), seis de Lombard y, en la EMA, uno fuera cada vez.

| Modelo | GRID (4 hablantes) | Lombard (6 hablantes) | EMA, lengua (3 pruebas) |
|---|---|---|---|
| Escalón | 0,432 | 0,364 | 0,40–0,46 |
| Reglas de la aplicación | 0,443 | 0,406 | 0,43–0,48 |
| Dominancia aprendida | 0,560 | 0,550 | 0,63–0,65 |
| TCN | **0,566** | **0,564** | **0,65–0,67** |
| Reglas, con los tiempos que calcula la aplicación | 0,315 | 0,271 | — |
| TCN entrenada con esos mismos tiempos | 0,530 | 0,498 | — |

*Cuadro 14b. Pearson medio entre el movimiento predicho y el real, sobre
hablantes no vistos. En GRID y Lombard es la media de los doce controles; en la
EMA, el rango de las tres pruebas. Fuente:
`investigacion/modelo_articulatorio/resultados.md`.*

**Lo que dice el Cuadro 14b.** Aprender la dinámica mejora a las reglas en los
tres conjuntos: en GRID, de 0,443 a 0,560–0,566. Las reglas además llegan
tarde —60 ms en la mandíbula— y en el redondeo anticipado van al revés: la
cara real llega a medio camino del redondeo unos 40 ms antes de /uː/ o /w/
(mediana), y las reglas, 20 ms después. En el cierre de /p b m/, el mínimo de
apertura cae a menos de 0,3 *z* del real en el 73 % de los casos con la
dominancia, frente al 58 % con las reglas. Pero la fila de abajo es la
importante: **con los tiempos de fonema que la aplicación sabía calcular, sin
alinear el audio, las reglas caen a 0,315**. Los tiempos pesaban tanto como el
modelo.

**Decisión.** Con tiempos bien alineados, la dominancia empata con la TCN en
labios y mandíbula (0,560 frente a 0,566), cabe en unas tablas de 12,6 KB que
el navegador lee sin red neuronal y se explica fonema a fonema; la TCN solo
gana en la lengua, por unas dos centésimas. Se publicó la dominancia (25 de
septiembre, revisión `0f41932` del front, del commit `de1498e`). Los tiempos de
las 85 palabras grabadas de *Pronunciar* se alinearon de antemano, y las frases
de la voz sintética se leen con las marcas por palabra que la corrección ya
guarda junto a su audio.

**Límites.** Es correlación con el movimiento de caras en vídeo, no una prueba
de que la boca 3D ayude a pronunciar mejor, que nadie ha medido con lectores.
GRID no ve el contacto de /f v/ (la cámara está lejos) y la protrusión desde un
vídeo frontal es débil. Y la boca de la aplicación es un corte de media cabeza,
no una cara de vídeo: los controles se trasladan a ella con una calibración por
poses comunes, que es una decisión de diseño y no algo medido.
'''

NOVEDADES = '''

**Lo añadido entre el 16 y el 26 de septiembre.** Todo está publicado y
registrado en `DESPLIEGUE.md`:

- **Mi espacio**, la pantalla de inicio y primera pestaña: los libros
  empezados, las palabras pendientes de practicar y *Mi progreso*, que enseña
  las palabras consultadas por día en las dos últimas semanas y los resultados
  de los últimos repasos, con las cifras siempre a la vista y sin gráficas en
  cero cuando todavía no hay datos. **Repasar** enseña hasta cinco palabras
  guardadas: el lector intenta recordarlas, ve la respuesta y dice si la sabía,
  dudó o no, y eso se guarda.
- **Leer en voz alta, en vivo.** En el lector, la aplicación escucha mientras
  se lee un pasaje y marca en el texto las palabras leídas, la actual y las
  saltadas; al terminar da un resumen con el ritmo. Usa un servicio de
  transcripción en tiempo real de pago, así que pide cuenta, gasta un uso por
  sesión y se corta a los tres minutos. Está probado de extremo a extremo con
  una lectura sintética; con la voz real de un lector, pendiente.
- **La boca 3D didáctica** y **los datos por cuenta**, descritos arriba, y el
  modelo que mueve la boca (apartado 7.8).
- **La marca Pléyade**: nombre, emblema, un texto «Sobre Pléyade» que se abre
  al pulsar el logo, y un fondo de galaxia en todas las pantallas, con cada una
  sobre una lámina translúcida de su tema (claro, noche o papel). **El
  contraste de este tema sobre la galaxia no se ha medido**: las pruebas de
  contraste del front cubren las portadas y el lector teñido, no el fondo.'''

REFS_A = '''

Alghamdi, N., Maddock, S., Marxer, R., Barker, J., & Brown, G. J. (2018). A
corpus of audio-visual Lombard speech with frontal and profile views. *The
Journal of the Acoustical Society of America, 143*(6), EL523–EL529.
https://doi.org/10.1121/1.5042758

Bai, S., Kolter, J. Z., & Koltun, V. (2018). *An empirical evaluation of
generic convolutional and recurrent networks for sequence modeling*
(arXiv:1803.01271). arXiv. https://arxiv.org/abs/1803.01271

Breuker, M. (2023)'''

REFS_C = '''

Cohen, M. M., & Massaro, D. W. (1993). Modeling coarticulation in synthetic
visual speech. En N. Magnenat Thalmann & D. Thalmann (Eds.), *Models and
techniques in computer animation* (pp. 139–156). Springer.
https://doi.org/10.1007/978-4-431-66911-1_13

Cooke, M., Barker, J., Cunningham, S., & Shao, X. (2006). An audio-visual
corpus for speech perception and automatic speech recognition. *The Journal of
the Acoustical Society of America, 120*(5), 2421–2424.
https://doi.org/10.1121/1.2229005

Council of Europe. (2020)'''

REFS_L = '''Lugaresi, C., Tang, J., Nash, H., McClanahan, C., Uboweja, E., Hays, M.,
Zhang, F., Chang, C.-L., Yong, M. G., Lee, J., Chang, W.-T., Hua, W., Georg,
M., & Grundmann, M. (2019). *MediaPipe: A framework for building perception
pipelines* (arXiv:1906.08172). arXiv. https://arxiv.org/abs/1906.08172

McAuliffe, M., Socolof, M., Mihuc, S., Wagner, M., & Sonderegger, M. (2017).
Montreal Forced Aligner: Trainable text-speech alignment using Kaldi. En
*Proceedings of Interspeech 2017* (pp. 498–502).
https://doi.org/10.21437/Interspeech.2017-1386'''

REFS_N = '''

Narayanan, S., Toutios, A., Ramanarayanan, V., Lammert, A., Kim, J., Lee, S.,
Nayak, K., Kim, Y.-C., Zhu, Y., Goldstein, L., Byrd, D., Bresch, E., Ghosh,
P., Katsamanis, A., & Proctor, M. (2014). Real-time magnetic resonance imaging
and electromagnetic articulography database for speech production research
(TC). *The Journal of the Acoustical Society of America, 136*(3), 1307–1311.
https://doi.org/10.1121/1.4890284

Nation, I. S. P. (2013)'''

REFS_P = '''

Perry-Smith, L. (s. f.). *Infinite, 3D Head Scan* [Modelo 3D, licencia CC BY
3.0]. Infinite-Realities. http://www.ir-ltd.net/

Pratham Books. (s. f.)'''

CAMBIOS = [
    ('# LiteraLevel: medición automática', '# Pléyade (proyecto LiteraLevel): medición automática', 1),
    ('Autor: Miguel Reyes Carrillo\nSeptiembre de 2026', 'Autor: Miguel Reyes Carrillo\nOctubre de 2026', 1),
    ('LiteraLevel es una aplicación que responde esa pregunta.',
     'Pléyade, la aplicación del proyecto LiteraLevel, responde esa pregunta.', 1),
    ('propia y\nLiteraLevel no certifica ningún nivel', 'propia y\nPléyade no certifica ningún nivel', 1),
    ('La entrega usa **Angular como interfaz y una API FastAPI sobre el motor Python**;\n'
     'Gradio 6.26 se conserva como respaldo.',
     'La entrega usa **Angular como interfaz**, publicada en Vercel\n'
     '(https://pleyade-app.vercel.app), y **una API FastAPI sobre el motor Python** en\n'
     'Hugging Face; Gradio 6.26 se conserva como respaldo. Un segundo modelo, pequeño\n'
     'y aprendido de vídeos de caras reales, mueve la boca 3D con la que la\n'
     'aplicación enseña a pronunciar (apartado 7.8).', 1),
    ('transformers, Project Gutenberg, Angular.', 'transformers, Project Gutenberg, Angular, coarticulación.', 1),
    ('- **Accionables.** Diez, con coste',
     '- **Nombres.** Peldaño es la compañía ficticia del módulo; **Pléyade**, su\n'
     '  aplicación, el nombre que ve el lector desde el 26 de septiembre de 2026; y\n'
     '  **LiteraLevel**, el proyecto y su modelo (`literalevel-v4`). Repositorios,\n'
     '  Spaces y paquete conservan ese nombre para no romper los enlaces publicados ni\n'
     '  la descarga del cuaderno.\n'
     '- **Accionables.** Diez, con coste', 1),
    ('del entrenamiento. LiteraLevel no acredita', 'del entrenamiento. Pléyade no acredita', 1),
    ('LiteraLevel es una herramienta de apoyo a la lectura.', 'Pléyade es una herramienta de apoyo a la lectura.', 1),
    # --- 7.8 -----------------------------------------------------------------
    ('rechazados con su motivo.\n\n---\n\n## 8. Resolución del problema',
     'rechazados con su motivo.\n' + ARTICULATORIO + '\n---\n\n## 8. Resolución del problema', 1),
    # --- 8.1 -----------------------------------------------------------------
    ('| ¿Lo estoy pronunciando bien? | Lectura en voz alta marcada palabra por palabra, con el sonido concreto que falla | Una frase |',
     '| ¿Lo estoy pronunciando bien? | Lectura en voz alta marcada palabra por palabra, con el sonido concreto que falla y cómo se mueve la boca, en corte 2D o en 3D; en el lector, un pasaje leído en vivo con las palabras saltadas marcadas | Una frase; el pasaje en vivo, hasta tres minutos |\n'
     '| ¿Cómo voy? | *Mi espacio*: libros empezados, palabras consultadas por día y resultados de los repasos; con cuenta, lo mismo en cualquier aparato | Nada |', 1),
    # --- 8.5 -----------------------------------------------------------------
    ('**Estado documental al 14 de septiembre de 2026.** El enlace para el lector es\n'
     'https://mikemaki1763-literalevel-front.static.hf.space/ . Es el front Angular;\n'
     'el Space `MikeMaki1763/literalevel` aloja FastAPI y conserva Gradio como respaldo.',
     '**Estado documental al 26 de septiembre de 2026.** El enlace para el lector es\n'
     'https://pleyade-app.vercel.app . Es el front Angular, publicado en Vercel (plan\n'
     'gratuito) desde el 26 de septiembre, como pidió el profesor; se vuelve a publicar\n'
     'solo con cada cambio de la rama principal del repositorio, y el Space estático\n'
     'https://mikemaki1763-literalevel-front.static.hf.space/ sirve la misma aplicación\n'
     'como respaldo. Tiene cinco pestañas —*Mi espacio*, *Leer*, *Encontrar*,\n'
     '*Pronunciar* y *Tu nivel*—, más *Mis palabras* y *Repasar*. El Space\n'
     '`MikeMaki1763/literalevel` aloja FastAPI y conserva Gradio como respaldo.', 1),
    ('**40 rutas bajo `/api`** a fecha de `8ee42f0` (el `app/` que publica el Space en su revisión `7c09d90`, subida desde `ab4e36f`)',
     '**44 rutas bajo `/api`** a fecha de `06a16db` (el commit que publica el Space en su revisión `103eef5`)', 1),
    ('siguió respondiendo.\n\nEl catálogo local se volvió a contar',
     'siguió respondiendo.\n\n'
     '**Datos por cuenta.** Desde el 26 de septiembre, quien entra con usuario y\n'
     'contraseña deja de ser un navegador: sus libros, sus palabras y su nivel pasan\n'
     'a ser **de la cuenta** (`cuentas/<nombre>` en el bucket) y se ven igual en el\n'
     'teléfono, la tableta o el equipo; sin cuenta siguen siendo de ese navegador.\n'
     'Salió de un caso real: con la misma cuenta, el teléfono y la tableta del autor\n'
     'enseñaban dos lectores distintos.\n\n'
     'El catálogo local se volvió a contar', 1),
    ('natural son del corte anterior, `d58b0be`.',
     'natural son del corte anterior, `d58b0be`. La última publicación de la API\n'
     '(26 de septiembre, revisión `103eef5` del Space, del commit `06a16db`) pasó\n'
     '70 de 70 pruebas API, las extremas sin fallos y 464 de 464 del front; en vivo,\n'
     'la misma cuenta entró desde dos aparatos nuevos y los dos vieron los mismos\n'
     'datos (`DESPLIEGUE.md`).', 1),
    ('**Boca 3D y portadas, a fecha de la revisión `ec957d0` del front (del commit `4e6276e`).** La boca 3D ya está publicada: '
     'el front sirve `boca3d/cara.glb` y `lengua.glb`, idénticos byte a byte a los del repositorio, con 72 mallas entre los dos y respaldo 2D si no cargan. '
     'La piel de la media cabeza sale de la malla base de MakeHuman 1.3.0, publicada bajo CC0 1.0 (no obliga a atribuir; MakeHuman Community, s. f.); '
     'paladar, velo, encías, dientes y lengua son modelos propios, y sus 53 poses se validan contra ellos. Es un corte esquemático, no anatomía validada clínicamente. ',
     '**Boca 3D, a 26 de septiembre de 2026.** En *Pronunciar*, junto al corte 2D, hay una boca 3D didáctica que se descarga solo al abrirla, '
     'con el corte 2D de respaldo si no carga. La cabeza parte de un escaneo publicado bajo CC BY 3.0 —*Infinite, 3D Head Scan*, de Lee Perry-Smith '
     '(Perry-Smith, s. f.)—, cuya atribución se sirve con el modelo; los labios, la lengua, el corte anatómico y los materiales son adaptación propia en Blender. '
     'Enseña el aire y la vibración de cada sonido, lee palabras y frases al compás del audio —con el modelo del apartado 7.8—, y tiene zoom, cámara lenta '
     '(«Despacio») y giro libre («Explorar»). El 26 de septiembre sus texturas pasaron a WebP y lo que baja por la red se quedó en 1,4 MB en vez de 3,5 '
     '(commit `1f5f2c9`). Es un corte esquemático, no anatomía validada clínicamente. ', 1),
    ('respuesta puede cambiar, y el guion de la demostración la vuelve a comprobar con cuenta antes\nde enseñarla.',
     'respuesta puede cambiar, y el guion de la demostración la vuelve a comprobar con cuenta antes\nde enseñarla.' + NOVEDADES, 1),
    # --- limitaciones --------------------------------------------------------
    ('consecuencias.** La aplicación está publicada en Hugging Face Spaces\n'
     '    (`MikeMaki1763/literalevel`), con dirección fija que sobrevive a apagar el\n'
     '    equipo del autor.',
     'consecuencias.** La aplicación está publicada con dirección fija que\n'
     '    sobrevive a apagar el equipo del autor: el front en Vercel\n'
     '    (https://pleyade-app.vercel.app) y, de respaldo, en un Space estático, los\n'
     '    dos gratuitos y sin suspensión, y la API con el motor en Hugging Face Spaces\n'
     '    (`MikeMaki1763/literalevel`).', 1),
    ('el cuaderno y el\n    perfil del lector se guardan', 'el cuaderno y el\n    perfil del lector —o de su cuenta— se guardan', 1),
    # --- trabajo futuro ------------------------------------------------------
    ('7. **Convertir las cinco acciones en herramientas de un agente**',
     '7. **Una cara que habla de frente.** La boca 3D enseña la articulación en\n'
     '   corte; una cara completa que lea las frases de frente (*Eos*, sobre un\n'
     '   MetaHuman de Epic) está en desarrollo y **no forma parte de esta entrega**.\n'
     '8. **Convertir las cinco acciones en herramientas de un agente**', 1),
    # --- conclusiones --------------------------------------------------------
    ('antes de optimizar, y medir también lo que se descarta.**\n\n',
     'antes de optimizar, y medir también lo que se descarta.**\n\n'
     '**La misma lección, en el segundo modelo.** Para mover la boca 3D, un modelo\n'
     'aprendido de caras reales supera a las reglas escritas a mano —Pearson 0,566\n'
     'frente a 0,443 con hablantes que no vio—, pero con los tiempos de fonema que la\n'
     'aplicación sabía calcular las reglas caían a 0,315: los datos de entrada\n'
     'pesaban tanto como el modelo. Y entre la red y unas tablas de 12,6 KB que\n'
     'empataban con ella se eligieron las tablas, por coste y porque se explican\n'
     'fonema a fonema (apartado 7.8).\n\n', 1),
    ('dirección fija, pero sobre el hardware más barato:',
     'dirección fija —el front en Vercel, con un respaldo en Hugging Face, y la API\n'
     'con el motor en un Space—, pero el motor corre sobre el hardware más barato:', 1),
    # --- alcance -------------------------------------------------------------
    ('se guardan separados por navegador y no se\ncomparten entre visitantes.',
     'se guardan separados por cuenta, o por navegador si no se\nentra, y no se comparten entre lectores.', 1),
    # --- referencias ---------------------------------------------------------
    ('\n\nBreuker, M. (2023)', REFS_A, 1),
    ('\n\nCouncil of Europe. (2020)', REFS_C, 1),
    ('MakeHuman Community. (s. f.). *License*.\nhttps://static.makehumancommunity.org/about/license.html', REFS_L, 1),
    ('\n\nNation, I. S. P. (2013)', REFS_N, 1),
    ('\n\nPratham Books. (s. f.)', REFS_P, 1),
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
    RUTA.write_text(t, encoding='utf-8', newline=chr(13) + chr(10) if crlf else chr(10))
    print('ok', len(CAMBIOS), 'cambios')


if __name__ == '__main__':
    main()
