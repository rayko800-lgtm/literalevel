# Guion del vídeo narrado por Eos, en formato de anuncio (borrador del 27 sep 2026)

Miguel lo pidió el 27 de septiembre: que el vídeo no lo presente él, sino **Eos**, la
asistente de Pléyade, en formato de anuncio (como los de Duolingo). Eos está en primer
plano y cuenta el problema, y detrás se ve Pléyade funcionando en el celular.

> **Antes de grabar nada: la rúbrica.** El apartado «Video (20 Puntos)» dice «se debe
> aparecer hablando a cámara» y «se debe aparecer en todo momento en el video final junto
> a la presentación en el fondo». Miguel le preguntó al profesor si acepta este formato.
> **Mientras no conteste, la versión que cumple la rúbrica tal cual es `guion_video.md`**
> (Miguel a cámara todo el rato, con Eos como demostración dentro). Si el profesor pide
> que Miguel aparezca, este mismo guion vale con Miguel en una ventana pequeña en una
> esquina.

**Quién hace qué.** La sesión de los entregables se encarga de este guion y de elegir la
voz. La sesión de Eos (literalevel-d6) se encarga de animar a Eos con el audio y de montar
el anuncio. `guion_video.md` no se toca.

**Voz.** Pendiente de que Miguel la elija. El 27 de septiembre se probaron cinco voces de
OpenAI (`gpt-4o-mini-tts-2025-12-15`: coral, marin, sage, shimmer y nova), todas con las
mismas instrucciones: «Eos, asistente de Pléyade; español de México neutro; mujer joven,
cálida y luminosa; energía de anuncio de una app educativa, sonriendo al hablar, ritmo
ágil y muy claro». Las cinco dijeron el texto completo y en español: se comprobó
transcribiéndolas con whisper. **Miguel las descartó: no suenan naturales.** La voz
que le gusta es la de la Eos inglesa (edge-tts, en-US-AvaNeural). La segunda tanda: Ava
Multilingual hablando español (la misma voz), Emma Multilingual y gpt-audio-1.5 (marin y
coral), todas comprobadas con whisper.

**Duración.** El texto hablado son **unas 470 palabras**, unos 3:10 a 150 palabras por
minuto. Deja hueco para las pausas y para que se vean los pasos de la app sin prisa, y el
total no debe pasar de 4:30. El máximo son 5:00.

**Las cifras** son las mismas del documento y de `guion_video.md`, del mismo caso: perfil
1,20, *Crime and Punishment* (203.415 palabras, media 1,70), Spearman 0,908 en validación
interna, 53.179 libros de Gutenberg y 15.367 textos libres. No se añade ninguna.

---

## A — Atención · 0:00–0:20

**En pantalla:** Eos en primer plano, sobre el fondo de galaxia de Pléyade. Nada más.

**Eos:**
«¡Hola! Soy Eos. ¿Alguna vez abriste un libro en inglés… y a las tres páginas lo
cerraste?
*(pausa)*
No te preocupes: no era tu inglés. Era el libro.»

## N — Necesidad · 0:20–0:50

**En pantalla:** Eos a un lado. Al otro, tres frases grandes, una detrás de otra: «Leer
mucho funciona» · «Libros gratis hay de sobra» · «¿Cuál es el tuyo?».

**Eos:**
«Leer mucho, un poquito por encima de tu nivel, es de lo que mejor funciona para aprender
un idioma. Y libros gratis hay de sobra. El problema es saber cuál.
Las etiquetas —A1, B2, C1— casi nunca las pone alguien que leyó el libro. Y un libro no es
igual de difícil de principio a fin: cambia de capítulo a capítulo.»

## S — Satisfacción · 0:50–3:10

**En pantalla:** Eos se hace a un lado y detrás aparece **el celular con Pléyade grabada de
verdad** (pleyade-app.vercel.app a 390 px): nada de capturas fijas, que se vea el dedo. Cada
paso tiene su referencia en `capturas/` (entre paréntesis).

**Eos:**
«Por eso existe Pléyade. Mira.

**Uno.** Primero, tu nivel: tres preguntas y tres fragmentos de libros reales. En este
ejemplo, una lectora con uno coma veinte sobre dos: banda intermedia. *(03_nivel)*

**Dos.** Me dices en español qué quieres leer. Por ejemplo: *Crimen y castigo*, de
Dostoyevski. Pléyade busca por significado y pone el nivel al lado de cada libro.
*(05_encontrar)*

**Tres.** Abres el libro: doscientas tres mil palabras, cuánto es diálogo, qué se repite… y
la curva, la dificultad capítulo a capítulo. De media, uno coma setenta. Te queda por
encima… y lo sabes antes de la primera página. *(06_ficha)*

**Cuatro.** ¿Una palabra que no conoces? Deja el dedo encima. Al instante, el diccionario y
cómo se pronuncia, en británico y en americano. Unos segundos después, la inteligencia
artificial te explica qué significa en esa frase. Y si el diccionario no la trae, te avisa
de que la escribió la IA. *(07_palabra_poverty, 08_palabra_ia)*

**Cinco.** Ahora léela en voz alta. Pléyade te marca, palabra por palabra, lo que se
entendió, te señala el sonido que falla, te lo dice bien… y te enseña cómo se mueve la
boca, también en 3D. *(09_pronunciar, 10_correccion, 11_boca_2d, 12_boca_3d)*

**Seis.** Y lo que consultas se queda en tu espacio, con su frase, para repasarlo. Con tu
cuenta, lo ves igual en el celular y en la computadora.» *(14_mis_palabras, 16_mi_espacio)*

**En pantalla:** las métricas, grandes y sin adornos: **distilroberta-base** · Spearman
**0,908** (validación interna) · orden A1 → C1 creciente en textos de examen · escala 0–2.

**Eos:**
«¿Y cómo sabe Pléyade lo difícil que es un libro? Porque lo lee entero un modelo de
lenguaje afinado para medir dificultad. En su validación interna, su correlación con el
nivel de referencia es de cero coma noventa y uno. Y en textos de examen con nivel oficial, pone los
niveles en orden, de A1 a C1.
Eso sí: Pléyade **no certifica** ningún nivel del Marco Común Europeo. Sirve para elegir
qué leer.»

## V — Visualización · 3:10–3:50

**En pantalla:** el catálogo, en dos cifras grandes: **53.179** libros de Project
Gutenberg y **15.367** textos libres. Eos delante.

**Eos:**
«Ahora imagínalo en grande: cincuenta y tres mil libros de Project Gutenberg, medidos
enteros, capítulo a capítulo, y quince mil textos cortos de licencia libre.
Si un libro te queda grande, Pléyade te dice qué capítulos sí están a tu alcance.
Empiezas el libro que te toca, entiendes lo que lees… y sigues.»

## A — Acción · 3:50–4:15

**En pantalla:** el logo de Pléyade y, grande, `pleyade-app.vercel.app`. Abajo, pequeño:
«Un proyecto de Miguel Reyes Carrillo · Módulo 5 · Diplomado en Ciencia de Datos, FES
Acatlán».

**Eos:**
«Pléyade ya funciona, en tu celular. El enlace está en pantalla.
Y si alguna vez dejaste un libro en inglés pensando que el problema eras tú…
*(pausa)*
no lo eras. Era el libro. ¡Nos vemos leyendo!»

*Mantener a Eos sonriendo un segundo después de la última palabra, sin cortar en seco.*

---

## Notas para generar la voz

- **Las cifras, escritas con letra en el texto que va a la voz.** Si el modelo recibe
  «203.415» o «1,20», puede leer «doscientos tres punto cuatrocientos quince» o «uno
  veinte». Por eso el parlamento de arriba ya las lleva con letra y en pantalla van en
  número.
- **Los nombres en inglés:** *Crime and Punishment* se dice en español («*Crimen y
  castigo*»); «Spearman» no se dice en voz alta, solo sale en pantalla.
- **Por fases:** una llamada por fase ANSVA, con las mismas instrucciones de estilo, y
  después se juntan. Así, si una frase sale mal, se repite solo esa.
- **Tiempos por palabra para la animación:** OpenAI no los da. La sesión de Eos dirá si los
  saca de whisper, de MFA o de su propia cadena.
- **Piloto antes que lote:** primero solo A y N con la voz elegida. Miguel lo escucha y,
  si le gusta, se hace el resto.
