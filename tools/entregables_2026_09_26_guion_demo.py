# -*- coding: utf-8 -*-
"""Pone al día entrega/guion_demo_en_vivo.md (26 sep 2026)."""
import pathlib, sys

RUTA = pathlib.Path(__file__).resolve().parent.parent / 'entrega' / 'guion_demo_en_vivo.md'

CAMBIOS = [
    ('# Guion de la demo en vivo — LiteraLevel (Módulo 5)',
     '# Guion de la demo en vivo — Pléyade, proyecto LiteraLevel (Módulo 5)\n\n'
     '*Puesto al día el 26 de septiembre de 2026: Vercel, datos por cuenta, boca 3D\n'
     'didáctica y Mi espacio. Las capturas de referencia están en `capturas/`\n'
     '(`registro.txt` dice de dónde sale cada una).*', 1),
    ('- [ ] **Front abierto** en `https://mikemaki1763-literalevel-front.static.hf.space/`,',
     '- [ ] **Front abierto** en `https://pleyade-app.vercel.app` (respaldo:\n'
     '      `https://mikemaki1763-literalevel-front.static.hf.space/`, la misma app),', 1),
    ('      corregir la pronunciación salen a un servicio de pago y gastan cupo.',
     '      corregir la pronunciación salen a un servicio de pago y gastan cupo.\n'
     '      **Desde el 26 de septiembre el perfil y las palabras son de la cuenta**, no\n'
     '      del navegador: lo que prepares en el ordenador lo verás igual en el móvil,\n'
     '      y al revés.', 1),
    ('- [ ] **Perfil de 1,20 sobre 2 ya puesto** (banda intermedia).',
     '- [ ] **Perfil de 1,20 sobre 2 ya puesto** (banda intermedia). **Ojo: es el perfil\n'
     '      de tu cuenta.** Tu nivel real, medido en la app el 26 de septiembre, es C2,\n'
     '      1,88 (receta: «Casi todos los días» · fácil «Lo entiendo con naturalidad, sin\n'
     '      necesidad de releer» · «Sí, una obra clásica o especializada» · medio, lo mismo ·\n'
     '      «También los detalles y las relaciones entre ideas» · difícil, lo mismo). Pon el\n'
     '      de 1,20 para la demo y vuelve a medirte después.', 1),
    ('- [ ] **Boca 3D abierta una vez** antes de compartir pantalla (*Pronunciar* → un\n'
     '      sonido → «Boca en 3D»): la cara tarda unos 3–4 s la primera vez (depende de la\n'
     '      red; medido el 15 de septiembre) y menos de 1 s después.',
     '- [ ] **Boca 3D abierta una vez** antes de compartir pantalla (*Pronunciar* → un\n'
     '      sonido → «Boca en 3D»). Es la boca didáctica nueva: desde el 26 de septiembre\n'
     '      baja 1,4 MB por la red en vez de 3,5, pero **su tiempo de carga en Vercel no\n'
     '      se ha medido**: ábrela antes para que en directo salga de la caché. Tiene zoom\n'
     '      (+ y −), «Despacio» y «Explorar».', 1),
    ('«🐢 Despacio» o «Boca en 3D».', '«Despacio» o «Boca en 3D» (con + y − se acerca).', 1),
    ('elige un libro que le queda grande y lo abandona. LiteraLevel le dice, antes de',
     'elige un libro que le queda grande y lo abandona. Pléyade le dice, antes de', 1),
    ('**7. Mis palabras (3:20 – 3:40)**\n\n**Hace:** *Mis palabras*. Enseña la lista con su frase y «Repasa cinco».',
     '**7. Mis palabras y Mi espacio (3:20 – 3:40)**\n\n**Hace:** *Mis palabras*. Enseña la lista con su frase y «Repasa cinco». Si da\n'
     'tiempo, toca *Mi espacio*: el libro donde lo dejaste y *Mi progreso*.', 1),
    ('**Dice:** «Todo lo que consulto y lo que pronuncio mal se queda aquí, con la\nfrase donde lo encontré, para repasar.»',
     '**Dice:** «Todo lo que consulto y lo que pronuncio mal se queda aquí, con la\nfrase donde lo encontré, para repasar. Y es de mi cuenta: en el móvil y en la\ncomputadora veo lo mismo.»', 1),
    ('**Dice:** «Usted lo pidió en la revisión del avance: un front propio, separado del\n'
     'motor. Gradio sigue como motor y respaldo, y el front es una aplicación estática,\n'
     'gratuita y siempre despierta, pensada para el móvil.»',
     '**Dice:** «Usted lo pidió en la revisión del avance: un front propio, separado del\n'
     'motor, y después, en Vercel. Gradio sigue como motor y respaldo, y el front es una\n'
     'aplicación estática, gratuita y siempre despierta, pensada para el móvil; se\n'
     'publica sola cada vez que subo un cambio.»\n\n'
     '**¿Por qué Pléyade, si el proyecto es LiteraLevel?**\n'
     '**Dice:** «LiteraLevel es el proyecto y el modelo; Pléyade es el nombre de la\n'
     'aplicación, el que ve el lector. Una pléyade es un grupo de escritores célebres de\n'
     'una época, y también un cúmulo de estrellas: junta la literatura y el cielo.»\n\n'
     '**¿Hay más de un modelo?**\n'
     '**Dice:** «Dos. El que mide la dificultad, un distilroberta afinado, y uno pequeño\n'
     'que mueve la boca 3D, aprendido de vídeos de caras reales: con hablantes que no\n'
     'vio sigue el movimiento real con una correlación de 0,56, frente a 0,44 de las\n'
     'reglas que había antes. Está en el apartado 7.8 del documento.»', 1),
    ('**Dice:** «LiteraLevel no certifica ningún nivel:', '**Dice:** «Pléyade no certifica ningún nivel:', 1),
    ('**Dice:** «Repetir la prueba de usuario con cinco lectores sobre el front nuevo y',
     '**Dice:** «Terminar la cara que lee de frente, que está en desarrollo, repetir la\n'
     'prueba de usuario con cinco lectores sobre el front nuevo y', 1),
]


def main():
    crlf = bytes([13, 10]) in RUTA.read_bytes()
    original = RUTA.read_text(encoding='utf-8')
    t = original
    malos = []
    for viejo, nuevo, n in CAMBIOS:
        if original.count(viejo) != n:
            malos.append((original.count(viejo), viejo[:80]))
        t = t.replace(viejo, nuevo)
    if malos:
        for m in malos:
            print('NO CUADRA', m)
        sys.exit(1)
    RUTA.write_text(t, encoding='utf-8', newline=chr(13) + chr(10) if crlf else chr(10))
    print('ok', len(CAMBIOS))


main()
