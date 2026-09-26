# -*- coding: utf-8 -*-
"""Pone al día entrega/estrategia.md con el estado del 26 sep 2026 (los mismos
cambios que el apartado de Estrategia de documento.tex)."""
import pathlib, sys

RUTA = pathlib.Path(__file__).resolve().parent.parent / 'entrega' / 'estrategia.md'

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
- **La boca 3D didáctica** y **los datos por cuenta**, descritos arriba. La
  boca se mueve con un segundo modelo, aprendido de vídeos de caras reales, que
  se describe en el apartado 7.8 del documento principal.
- **La marca Pléyade**: nombre, emblema, un texto «Sobre Pléyade» que se abre
  al pulsar el logo, y un fondo de galaxia en todas las pantallas, con cada una
  sobre una lámina translúcida de su tema (claro, noche o papel). **El
  contraste de este tema sobre la galaxia no se ha medido**: las pruebas de
  contraste del front cubren las portadas y el lector teñido, no el fondo.

Las capturas de todo esto, hechas el 26 de septiembre desde la app publicada,
están en `capturas/` con su procedencia en `capturas/registro.txt`.'''

CAMBIOS = [
    ('# LiteraLevel — Estrategia', '# Pléyade (proyecto LiteraLevel) — Estrategia', 1),
    ('Autor: Miguel Reyes Carrillo\nSeptiembre de 2026', 'Autor: Miguel Reyes Carrillo\nOctubre de 2026', 1),
    ('manifiesto.\n\nEl nombre no es decorativo.',
     'manifiesto.\n\n'
     '**Tres nombres para tres cosas.** Peldaño es la compañía; **Pléyade** es su\n'
     'aplicación, el nombre que ve el lector desde el 26 de septiembre de 2026; y\n'
     '**LiteraLevel** es el nombre del proyecto y de su modelo (`literalevel-v4`).\n'
     'Los repositorios, los Spaces de Hugging Face y el paquete de Python lo conservan\n'
     'a propósito: renombrarlos habría roto los enlaces publicados y la descarga que\n'
     'hace el cuaderno. Una *pléyade* es un grupo de personas célebres de una misma\n'
     'época, sobre todo en las letras, y las Pléyades son un cúmulo de estrellas de\n'
     'Tauro: el nombre junta la literatura y el cielo, y el emblema —un pegaso sobre un\n'
     'libro abierto cuyas páginas son alas— lo dice en imagen.\n\n'
     'El nombre de la compañía no es decorativo.', 1),
    ('libro adecuado es un problema que el lector no puede resolver solo. LiteraLevel\nconvierte',
     'libro adecuado es un problema que el lector no puede resolver solo. Pléyade\nconvierte', 1),
    ('- **Continuidad.** «Mis libros» guarda cada libro empezado',
     '- **Continuidad.** *Mi espacio* («Donde lo dejaste») guarda cada libro empezado', 1),
    ('incurrir en una promesa que no puede cumplir: **LiteraLevel no certifica',
     'incurrir en una promesa que no puede cumplir: **Pléyade no certifica', 1),
    # --- 4.6 ----------------------------------------------------------------------
    ('  `zone.js`) publicada como **Space estático** de Hugging Face\n'
     '  (`MikeMaki1763/literalevel-front`), gratuito y siempre despierto: es HTML, CSS\n'
     '  y JavaScript ya compilados. Tiene cuatro sitios en vez de ocho pestañas\n'
     '  —*Leer*, *Encontrar*, *Pronunciar* y *Tu nivel*—, más *Mis palabras*; los\n'
     '  ajustes (paleta, tamaño de letra, idioma de las explicaciones)',
     '  `zone.js`): HTML, CSS y JavaScript ya compilados, así que no se duerme. Desde\n'
     '  el 26 de septiembre de 2026 se publica en **Vercel**\n'
     '  (https://pleyade-app.vercel.app, plan gratuito), como pidió el profesor, y se\n'
     '  vuelve a publicar sola con cada cambio de la rama principal del repositorio;\n'
     '  el **Space estático** de Hugging Face (`MikeMaki1763/literalevel-front`) sirve\n'
     '  la misma aplicación como respaldo. Tiene cinco sitios en vez de ocho pestañas\n'
     '  —*Mi espacio*, *Leer*, *Encontrar*, *Pronunciar* y *Tu nivel*—, más *Mis\n'
     '  palabras* y *Repasar*; los ajustes (tema, tamaño de letra, idioma de las\n'
     '  explicaciones)', 1),
    ('40 rutas bajo `/api` a fecha de `8ee42f0`, el `app/` que publica el Space en su revisión `7c09d90`, subida desde `ab4e36f`)',
     '44 rutas bajo `/api` a fecha de `06a16db`, el commit que publica el Space en su revisión `103eef5`)', 1),
    ('  viaja en una cabecera (`X-Lector`) y sus datos siguen en el bucket montado en\n  `/data`.',
     '  viaja en una cabecera (`X-Lector`) y sus datos siguen en el bucket montado en\n  `/data`. '
     'Desde el 26 de septiembre, quien entra con usuario y contraseña deja de ser\n'
     '  un navegador: sus libros, sus palabras y su nivel pasan a ser **de la cuenta**\n'
     '  (`cuentas/<nombre>` en el bucket) y se ven igual en el teléfono, la tableta o\n'
     '  el equipo; sin cuenta siguen siendo de ese navegador. Salió de un caso real:\n'
     '  con la misma cuenta, el teléfono y la tableta del autor enseñaban dos\n'
     '  lectores distintos.', 1),
    ('  son del corte anterior, `d58b0be`.\n',
     '  son del corte anterior, `d58b0be`. La última publicación de la API (26 de\n'
     '  septiembre, revisión `103eef5` del Space, del commit `06a16db`) pasó 70 de 70\n'
     '  pruebas API, las extremas sin fallos y 464 de 464 del front; en vivo, la misma\n'
     '  cuenta entró desde dos aparatos nuevos y los dos vieron los mismos datos\n'
     '  (`DESPLIEGUE.md`).\n', 1),
    ('**Boca 3D y portadas, a fecha de la revisión `ec957d0` del front (del commit `4e6276e`).** La boca 3D ya está publicada: '
     'el front sirve `boca3d/cara.glb` y `lengua.glb`, idénticos byte a byte a los del repositorio, con 72 mallas entre los dos y respaldo 2D si no cargan. '
     'La piel de la media cabeza sale de la malla base de MakeHuman 1.3.0, publicada bajo CC0 1.0 (no obliga a atribuir; MakeHuman Community, s. f.); '
     'paladar, velo, encías, dientes y lengua son modelos propios, y sus 53 poses se validan contra ellos. Es un corte esquemático, no anatomía validada clínicamente. ',
     '**Boca 3D, a 26 de septiembre de 2026.** En *Pronunciar*, junto al corte 2D, hay una boca 3D didáctica que se descarga solo al abrirla, '
     'con el corte 2D de respaldo si no carga. La cabeza parte de un escaneo publicado bajo CC BY 3.0 —*Infinite, 3D Head Scan*, de Lee Perry-Smith '
     '(Perry-Smith, s. f.)—, cuya atribución se sirve con el modelo; los labios, la lengua, el corte anatómico y los materiales son adaptación propia en Blender. '
     'Enseña el aire y la vibración de cada sonido, lee palabras y frases al compás del audio, y tiene zoom, cámara lenta («Despacio») y giro libre '
     '(«Explorar»). El 26 de septiembre sus texturas pasaron a WebP y lo que baja por la red se quedó en 1,4 MB en vez de 3,5 (commit `1f5f2c9`). '
     'Es un corte esquemático, no anatomía validada clínicamente. ', 1),
    ('El enlace del lector es https://mikemaki1763-literalevel-front.static.hf.space/ .',
     'El enlace del lector es https://pleyade-app.vercel.app, y el de respaldo,\n'
     'https://mikemaki1763-literalevel-front.static.hf.space/ .' + NOVEDADES, 1),
    # --- accionables --------------------------------------------------------------
    ('y el Space estático del front es gratuito', 'y el front, en Vercel y en el Space estático, es gratuito', 1),
    ('| **HECHO**: `MikeMaki1763/l', '| **HECHO**: el front en Vercel (https://pleyade-app.vercel.app), con respaldo en `MikeMaki1763/l', 1),
    ('se fijó un perfil, se reinici', 'se fijó un perfil, se reinici', 1),
    ('| **A5** | **Conseguir un micrófono**', '| **A5 · HECHO** | **Conseguir un micrófono**', 1),
    ('| Coste mínimo de hardware | Se graba una frase desde el equipo del autor y la corrección palabra por palabra aparece en pantalla |',
     '| Coste mínimo de hardware | **Cumplido con el teléfono**: el 16 de septiembre, desde el teléfono del autor y con cuenta, el micrófono grabó y la corrección salió; se vuelve a ensayar antes de la demo |', 1),
    ('**Orden de ejecución actualizado:** ensayar la voz con micrófono real (A5),',
     '**Orden de ejecución actualizado:** volver a ensayar la voz con cuenta (A5),', 1),
    # --- métricas -------------------------------------------------------------------
    ('| **Cumplido**: las ochenta y cinco parejas de color de las cinco paletas superan WCAG AA; las más ajustadas, 4,53 (texto) y 3,11 (título) |',
     '| **Cumplido en la interfaz anterior**: las ochenta y cinco parejas de color de las cinco paletas de Gradio superan WCAG AA; las más ajustadas, 4,53 (texto) y 3,11 (título). En el front, las portadas y el lector teñido tienen pruebas de contraste; el tema de la marca sobre el fondo de galaxia, **sin medir** |', 1),
    ('del corte anterior `d58b0be`; no equivalen a una prueba completa de usuario |',
     'del corte anterior `d58b0be`; la última publicación de la API (26 de septiembre, `06a16db`): API 70 de 70, extremas sin fallos y front 464 de 464. No equivalen a una prueba completa de usuario |', 1),
    ('| **Cumplido**: el front en `MikeMaki1763/literalevel-front` y la API con el motor en `MikeMaki1763/literalevel`, los dos en Hugging Face Spaces, públicos y en marcha, con los datos del lector en un bucket montado en `/data` |',
     '| **Cumplido**: el front en Vercel (https://pleyade-app.vercel.app), con respaldo en `MikeMaki1763/literalevel-front`, y la API con el motor en `MikeMaki1763/literalevel`, en Hugging Face Spaces, con los datos del lector o de su cuenta en un bucket montado en `/data` |', 1),
    # --- referencias ----------------------------------------------------------------
    ('MakeHuman Community. (s. f.). *License*.\nhttps://static.makehumancommunity.org/about/license.html\n\n', '', 1),
    ('\n\nPratham Books. (s. f.)',
     '\n\nPerry-Smith, L. (s. f.). *Infinite, 3D Head Scan* [Modelo 3D, licencia CC BY\n3.0]. Infinite-Realities. http://www.ir-ltd.net/\n\nPratham Books. (s. f.)', 1),
]


def main():
    crlf = bytes([13, 10]) in RUTA.read_bytes()
    original = RUTA.read_text(encoding='utf-8')
    t = original
    malos = [(original.count(v), v[:80]) for v, _, n in CAMBIOS if original.count(v) != n]
    if malos:
        for m in malos:
            print('NO CUADRA', m)
        sys.exit(1)
    for v, nuevo, _ in CAMBIOS:
        t = t.replace(v, nuevo)
    RUTA.write_text(t, encoding='utf-8', newline=chr(13) + chr(10) if crlf else chr(10))
    print('ok', len(CAMBIOS))


main()
