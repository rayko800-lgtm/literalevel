# Guion del vídeo - LiteraLevel (Módulo 5)

Actualizado el 14 de septiembre de 2026. El producto que se muestra es **Angular
con la API FastAPI**; Gradio queda como motor y respaldo.

**Rúbrica:** MP4, máximo **5:00**, cara de Miguel visible durante toda la toma.
Grabar con OBS, compartiendo la app sin ocultar la cámara. Objetivo: **4:40**.

**Texto hablado: 480 palabras.** Son 3:12 a 150 palabras por minuto o unos
3:42 a 130. Con 55 segundos de acciones, el presupuesto conservador es 4:37.
El contador oficial es `python -X utf8 tools/contar_guion.py`: cuenta únicamente
los parlamentos entre comillas angulares dentro de las fases ANSVA, sin notas
de producción. La duración es una estimación de lectura; el ensayo completo
con clics y audio es lo que decide si cabe en cinco minutos.

## Preparación de la toma

- Abrir `https://mikemaki1763-literalevel-front.static.hf.space/` a 390 px o
  duplicar el móvil. Mantener cámara y pantalla legibles, sin superponerlas.
- Entrar en Ajustes antes de grabar. No mostrar contraseña, identificador de
  lector, consola, secretos ni paneles de administración.
- Preparar un perfil ilustrativo de **1,20 sobre 2**, buscar *dostoyevski* y
  abrir *Crime and Punishment* (PG2554). No presentarlo como sesión real de
  una persona ni como resultado fijo del cuestionario.
- Abrir la curva guardada antes de la toma. El ejemplo documentado ronda
  **1,70**; si el texto o la medición vigente cambian, decir el valor visible.
  No mezclar el ensayo histórico de EPUB (203.699 palabras, 840 ventanas)
  con el de TXT (203.415, 836), ni prometer esos tiempos en el móvil.
- Preparar una palabra del capítulo y una frase corta para voz. El diccionario
  es local; **traducción y explicación llegan con la etapa de IA**, no con
  una supuesta respuesta completa en 40 ms. Una acepción dudosa debe conservar
  su aviso. Si no hay clave o permiso, mostrar la parte gratuita y decirlo.
- Ensayar audio del micrófono y audio de la app en OBS. La corrección depende
  de lo que se entienda: no prometer que siempre señalará un fonema concreto.
  Si se representa un error intencional, anunciar que es una demostración.
- No depender de portadas FLUX ni de Blender 3D: son ampliaciones en preparación.
  El apoyo articulatorio de esta toma es el corte 2D disponible. No fingir
  imágenes generadas, respuestas en vivo ni tiempos de espera que no ocurrieron.
- Preparar una grabación de respaldo del mismo recorrido. Si se usa, rotularla
  como **grabación previa**, sin presentar la reproducción como respuesta en vivo.

## Ritmo

ANSVA organiza el relato: atención, necesidad, satisfacción, visualización y
acción. La demo ocupa la mayor parte del tiempo. Reservar hasta 55 segundos para
clics, frase leída, audio y pausas; detener un ensayo que supere 4:40 y recortar
acciones, no acelerar hasta resultar incomprensible. La presentación PDF es
apoyo para la defensa; **no hay que leer todas sus diapositivas en el vídeo**.

# EL GUION

## A — ATENCIÓN · 0:00 - 0:25

> **En pantalla:** LiteraLevel. Miguel visible. Una pausa breve tras la pregunta.

«¿Te ha pasado? Abres un libro en inglés que te interesa y, a las pocas
páginas, lo dejas. Quizá no era falta de capacidad: quizá necesitabas otra
lectura. LiteraLevel te ayuda a comparar la dificultad de un libro con tu
nivel antes de empezar, y te acompaña mientras lees.»

## N — NECESIDAD · 0:25 - 0:50

> **En pantalla:** una ficha de libro con su nivel y la curva por capítulos.

«Hay miles de libros gratuitos, pero elegir uno adecuado sigue siendo difícil.
Además, un libro no tiene una sola dificultad: sus capítulos cambian.
Nuestro usuario es un hispanohablante que quiere leer en inglés con autonomía.
Necesita una orientación comprensible, no otro examen ni una etiqueta que
prometa más de lo que puede medir.»

## S — SATISFACCIÓN · 0:50 - 3:35

> **En pantalla:** Angular. Recorrer Tu nivel, Encontrar, ficha, lector,
> Pronunciar y Mis palabras. Las credenciales ya están introducidas fuera de toma.
> Mostrar el perfil ilustrativo preparado; no cumplimentar nueve respuestas
> esperando que den siempre el mismo resultado.

«Esta es la aplicación. La interfaz está hecha en Angular y se comunica con
una API FastAPI. El motor de Python también conserva Gradio como respaldo.

Primero, sitúo mi nivel con un cuestionario o con un texto que ya leo cómodo.
Para este ejemplo preparé un perfil de **1,20 sobre 2**, banda intermedia.

Ahora busco. Puedo describir en español lo que me apetece leer. Escribo
*dostoyevski* y elijo *Crimen y castigo*. La ficha muestra datos del texto y
su curva de dificultad. En este ejemplo, el libro ronda **1,70**. Al
compararlo con mi perfil, veo que me exigirá más.

Entro al lector y toco una palabra. Primero aparece el diccionario, con la
pronunciación disponible. Después, si tengo permiso para usar IA, llegan la
traducción y la explicación de esa frase. El diccionario y el texto generado
se distinguen; si la acepción es dudosa, la aplicación lo avisa.

También puedo practicar una frase en voz alta. Grabo y pido la corrección.
Comparo las palabras que se entendieron con las que quería decir, escucho el
audio de referencia y abro el apoyo de articulación para practicar.

Las palabras consultadas quedan en **Mis palabras**, con su frase, para volver
a ellas sin perder el contexto.

Detrás está un modelo distilroberta afinado en regresión. Su validación interna
registró un Spearman de **0,908**. Es una medida de orden, no una nota para el
lector. **No certificamos ningún nivel del MCER**: usamos una escala propia
de cero a dos para orientar la lectura.»

## V — VISUALIZACIÓN · 3:35 - 4:15

> **En pantalla:** 53.179 libros de Gutenberg y 585.111 capítulos medidos.
> No confundir esta cifra con el catálogo objetivo de 61.642 ni con los corpus graduados.

«El catálogo medido reúne **53.179 libros** de Project Gutenberg y **585.111
capítulos**. La aplicación aprovecha esa información para comparar lecturas
y, cuando hay capítulos adecuados, sugerir por dónde empezar.

Leer, buscar y consultar el diccionario no requieren llamadas de pago a
OpenAI. La explicación y la voz tienen su puerta de acceso y su cuota.
La siguiente validación será comprobar con lectores si esta ayuda mejora
su experiencia y continuidad.»

## A — ACCIÓN · 4:15 - 4:40

> **En pantalla:** `mikemaki1763-literalevel-front.static.hf.space`.
> Mantener la mirada un segundo al terminar. Cara visible hasta el final.

«Este es el enlace de LiteraLevel. Se abre en el navegador del móvil o del
ordenador. Elige un libro que te interese, compara su dificultad con tu perfil
y prueba una página con las ayudas de lectura. Ese es el siguiente paso:
no demostrar cuánto inglés sabes, sino encontrar qué te apetece seguir leyendo.»

## Comprobación antes de grabar

| Comprobación | Criterio |
|---|---|
| Duración real | Ensayo completo menor de 4:40; MP4 final nunca supera 5:00 |
| Cámara | Cara visible y reconocible todo el tiempo |
| Pantalla | Texto legible; cámara no tapa controles ni resultados |
| Privacidad | Sin contraseñas, tokens, IDs de lector ni datos personales de terceros |
| Sonido | Micrófono y audio de la app se oyen sin saturar |
| Estado | Front abre y backend responde; no basta un 200 con HTML |
| Ejemplo | Libro y palabra preparados; valores dichos coinciden con pantalla |
| IA | No atribuir traducción al diccionario ni ocultar un aviso de duda |
| Respaldo | Si se reproduce una captura, rotular grabación previa |
| Formato | Exportar MP4 y reproducirlo completo antes de entregar |

Las métricas corresponden a la documentación del modelo, no a una nueva
evaluación hecha al grabar. Este guion no demuestra mejora pedagógica ni
ausencia total de fallos; esos resultados necesitan una evaluación propia.
