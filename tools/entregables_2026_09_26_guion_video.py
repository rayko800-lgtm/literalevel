# -*- coding: utf-8 -*-
"""Pone al día entrega/guion_video.md y guion_video.tex (26 sep 2026).
'@' es la barra invertida en las cadenas del .tex."""
import pathlib, sys

BS = chr(92)
ENT = pathlib.Path(__file__).resolve().parent.parent / 'entrega'


def tex(s):
    return s.replace('@', BS)


BOCA_MD_VIEJA = ('- **La boca en 3D.** El front publicado —revisión `ec68419` del Space, del commit `8a992af`— lleva la\n'
                 '  cabeza de MakeHuman y la lengua corregida de la rama `boca3d` (75f334a está en\n'
                 '  `master`), con el giro ya limitado a donde el modelo se lee de perfil\n'
                 '  (`a70af4e`): el ensayo final del 16 de septiembre abrió la boca 3D en esa\n'
                 '  misma revisión y cargó con normalidad (`auditoria/ensayo_demo_final_2026-09-16.md`).\n'
                 '  **Ábrela una vez antes de grabar**: la cara\n'
                 '  tarda unos 3–4 s la primera vez (depende de la red; medido el 15 de\n'
                 '  septiembre) y menos de 1 s después. Si no carga, basta el corte 2D.')
BOCA_MD_NUEVA = ('- **La boca en 3D.** Desde el 24 de septiembre es la boca didáctica nueva (cabeza\n'
                 '  escaneada bajo CC BY 3.0, labios, lengua y corte propios), que se mueve con el\n'
                 '  modelo aprendido de caras reales (documento §7.8). Desde el 26 de septiembre\n'
                 '  baja 1,4 MB por la red en vez de 3,5 y tiene zoom (+ y −), «Despacio» y\n'
                 '  «Explorar». **Su tiempo de carga en Vercel no se ha medido: ábrela una vez\n'
                 '  antes de grabar**, para que en la toma salga de la caché. Si no carga, basta el\n'
                 '  corte 2D.\n'
                 '- **El perfil es de la cuenta.** Desde el 26 de septiembre, al entrar, el perfil\n'
                 '  y las palabras son de la cuenta y se ven igual en el móvil y en el equipo. Poner\n'
                 '  el 1,20 cambia tu nivel real (C2, 1,88, medido en la app el 26 de septiembre):\n'
                 '  vuelve a medirte después de grabar.')

MD = [
    ('# Guion del vídeo — LiteraLevel (Módulo 5)',
     '# Guion del vídeo — Pléyade, proyecto LiteraLevel (Módulo 5)\n\n'
     '*Puesto al día el 26 de septiembre de 2026: la app se llama Pléyade y está en\n'
     'Vercel. Las capturas de referencia están hechas: `capturas/01`–`22`\n'
     '(`capturas/registro.txt`).*', 1),
    ('es el front de Angular** (`mikemaki1763-literalevel-front.static.hf.space`), en\nel móvil:',
     'es el front de Angular** (`pleyade-app.vercel.app`), en\nel móvil:', 1),
    (BOCA_MD_VIEJA, BOCA_MD_NUEVA, 1),
    ('> **En pantalla:** portada. Solo el nombre *LiteraLevel* y una frase.',
     '> **En pantalla:** portada. Solo el nombre *Pléyade*, su emblema y una frase.', 1),
    ('Baskerville* le quedaba justo. Eso es lo que hace LiteraLevel.»',
     'Baskerville* le quedaba justo. Eso es lo que hace Pléyade.»', 1),
    ('> - [CAPTURA: para el cierre, la dirección del front grande sobre la\n>   portada: `mikemaki1763-literalevel-front.static.hf.space`]',
     '> - [CAPTURA: para el cierre, la dirección del front grande sobre la\n>   portada: `pleyade-app.vercel.app`]\n>\n'
     '> Hechas el 26 de septiembre desde Vercel con tu cuenta: `capturas/01`–`22`,\n'
     '> más la boca 3D (12), el lector con la lectura en vivo (13), Repasar (15), Mi\n'
     '> espacio (16), «Sobre Pléyade» (17) y tres de escritorio (18–20).', 1),
    ('«Esto es LiteraLevel, en el móvil.', '«Esto es Pléyade, en el móvil.', 1),
    ('sonido** que falla, lo oigo bien dicho y veo **cómo se mueve la boca**.',
     'sonido** que falla, lo oigo bien dicho y veo **cómo se mueve la boca**, también\nen 3D.', 1),
    ('**Seis.** Lo que consulto se queda en **Mis palabras**, con su frase, para\nrepasar.»',
     '**Seis.** Lo que consulto se queda en **Mis palabras**, con su frase, para\nrepasar, y lo veo igual en cualquier aparato donde entre.»', 1),
    ('> **En pantalla:** el enlace del front, grande:\n> `mikemaki1763-literalevel-front.static.hf.space`.',
     '> **En pantalla:** el enlace del front, grande:\n> `pleyade-app.vercel.app`.', 1),
    ('«LiteraLevel funciona ahora mismo, no es una maqueta.', '«Pléyade funciona ahora mismo, no es una maqueta.', 1),
]

TEX = [
    ('%  LiteraLevel — Guion del vídeo', '%  Pléyade (proyecto LiteraLevel) — Guion del vídeo', 1),
    (tex('@color{llgris} LiteraLevel — guion del vídeo}'), tex('@color{llgris} Pléyade — guion del vídeo}'), 1),
    (tex('{@LARGE LiteraLevel@par}'), tex('{@LARGE Pléyade@par}@vspace{2pt}{@normalsize@color{llgris} proyecto LiteraLevel@par}'), 1),
    (tex('{@normalsize Ciudad de México, septiembre de 2026@par}'), tex('{@normalsize Ciudad de México, octubre de 2026@par}'), 1),
    (tex('de Angular} (@texttt{mikemaki1763-literalevel-front.static.hf.space}), en el'),
     tex('de Angular} (@texttt{pleyade-app.vercel.app}), en el'), 1),
    (tex('  @item @textbf{La boca en 3D.} El @emph{front} publicado ---revisión @texttt{f4920fa} del Space, del\n'
         '        commit @texttt{a656c2e}--- lleva la cabeza de MakeHuman\n'
         '        y la lengua corregida de la rama @texttt{boca3d} (75f334a está en\n'
         '        @texttt{master}): comprobado hoy, @texttt{boca3d/cara.glb} y\n'
         '        @texttt{boca3d/lengua.glb} responden 200 en el Space publicado. @textbf{Ábrela una vez antes de grabar}: la cara tarda\n'
         '        unos 3--4 s la primera vez (depende de la red; medido el 15 de\n'
         '        septiembre) y menos de 1 s después. Si no carga, basta el corte 2D.'),
     tex('  @item @textbf{La boca en 3D.} Desde el 24 de septiembre es la boca didáctica nueva\n'
         '        (cabeza escaneada bajo CC BY 3.0; labios, lengua y corte propios), que se mueve\n'
         '        con el modelo aprendido de caras reales (documento §7.8). Desde el 26 de\n'
         '        septiembre baja 1,4 MB por la red en vez de 3,5 y tiene zoom (+ y $-$),\n'
         '        «Despacio» y «Explorar». @textbf{Su tiempo de carga en Vercel no se ha medido:\n'
         '        ábrela una vez antes de grabar}, para que en la toma salga de la caché. Si no\n'
         '        carga, basta el corte 2D.\n'
         '  @item @textbf{El perfil es de la cuenta.} Desde el 26 de septiembre, al entrar, el\n'
         '        perfil y las palabras son de la cuenta y se ven igual en el móvil y en el equipo.\n'
         '        Poner el 1,20 cambia tu nivel real (C2, 1,88, medido en la app el 26 de\n'
         '        septiembre): vuelve a medirte después de grabar.'), 1),
    (tex('portada. Solo el nombre @emph{LiteraLevel} y una frase.'),
     tex('portada. Solo el nombre @emph{Pléyade}, su emblema y una frase.'), 1),
    ('le quedaba justo. Eso es lo que hace LiteraLevel.', 'le quedaba justo. Eso es lo que hace Pléyade.', 1),
    (tex('        portada: @texttt{mikemaki1763-literalevel-front.static.hf.space}]'),
     tex('        portada: @texttt{pleyade-app.vercel.app}]'), 1),
    ('Esto es LiteraLevel, en el móvil.', 'Esto es Pléyade, en el móvil.', 1),
    (tex('sonido} que falla, lo oigo bien dicho y veo @textbf{cómo se mueve la boca}.'),
     tex('sonido} que falla, lo oigo bien dicho y veo @textbf{cómo se mueve la boca}, también\nen 3D.'), 1),
    (tex('@textbf{Seis.} Lo que consulto se queda en @textbf{Mis palabras}, con su frase, para\nrepasar.'),
     tex('@textbf{Seis.} Lo que consulto se queda en @textbf{Mis palabras}, con su frase, para\nrepasar, y lo veo igual en cualquier aparato donde entre.'), 1),
    (tex('@texttt{mikemaki1763-literalevel-front.static.hf.space}@@'), tex('@texttt{pleyade-app.vercel.app}@@'), 1),
    ('LiteraLevel funciona ahora mismo, no es una maqueta.', 'Pléyade funciona ahora mismo, no es una maqueta.', 1),
]


def aplicar(nombre, cambios):
    ruta = ENT / nombre
    crlf = bytes([13, 10]) in ruta.read_bytes()
    original = ruta.read_text(encoding='utf-8')
    t = original
    malos = [(original.count(v), v[:80]) for v, _, n in cambios if original.count(v) != n]
    if malos:
        for m in malos:
            print(nombre, 'NO CUADRA', m)
        return False
    for v, nuevo, _ in cambios:
        t = t.replace(v, nuevo)
    assert chr(9) + 'extbf' not in t
    ruta.write_text(t, encoding='utf-8', newline=chr(13) + chr(10) if crlf else chr(10))
    print(nombre, 'ok', len(cambios))
    return True


ok_md = aplicar('guion_video.md', MD)
ok_tex = aplicar('guion_video.tex', TEX)
sys.exit(0 if ok_md and ok_tex else 1)
