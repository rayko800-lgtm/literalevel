# Manifiesto del corpus externo de validación

Textos de lectura del catálogo gratuito de **British Council LearnEnglish**,
descargados en PDF. Aquí van **solo los nombres de archivo y el nivel MCER**
que declara cada uno: el cuerpo tiene derechos y no se redistribuye, ni
siquiera en fragmentos. Con esta lista cualquiera puede bajarse los mismos
documentos de learnenglish.britishcouncil.org y repetir `validar_local.py`.

## Cómo reconstruir el corpus y comprobar que es el mismo

**La URL y el SHA-256 de cada archivo están en
[`corpus_bc_manifiesto.csv`](corpus_bc_manifiesto.csv).** Las 59 URLs se
comprobaron el 12 de septiembre de 2026 descargándolas desde un navegador: los
59 archivos del sitio son idénticos byte a byte a los que se midieron.

1. Descarga los PDF **con el navegador**. British Council bloquea las descargas
   automáticas (403 a `curl`, sin respuesta a Python aunque se identifique como
   navegador), así que no hay guion que los baje solo, y no se intenta esquivar.
2. `python -X utf8 tools/bajar_corpus_bc.py [carpeta_de_descargas]` los empareja
   con el manifiesto **por su hash**, los copia a `corpus_bc/` con el nombre que
   espera el validador y dice cuáles faltan, cuáles están rotos y cuáles ha
   actualizado British Council desde que se midieron.
3. `python -X utf8 validar_local.py corpus_bc` reproduce las cifras. Comprobado
   desde una carpeta vacía: 47 textos, cinco niveles, Spearman 0,860, contar
   palabras 0,807, parcial 0,668, que son las publicadas.

| Nivel | n |
|---|---|
| A1 | 12 |
| A2 | 10 |
| B1 | 13 |
| B2 | 12 |
| C1 | 12 |
| **Total** | **59** |

**Son 59, y están los 59.** Durante un tiempo el documento hablaba de «uno no
disponible». No lo era: el patrón de búsqueda decía
`*LearnEnglish-Reading*.pdf` y uno de los archivos se llama
`LearnEnglish_Reading`, con guion BAJO, así que se caía del corpus sin que
nadie lo notara. El patrón de hoy usa `?` en esa posición y los ve todos.

De los 59: **2** no tienen cuerpo localizable al extraer el PDF, **10** los
rechaza `scoring.continuous_prose` por quedarse bajo las 150 palabras, y los
**47** restantes son los que se evalúan.

## A1 (12)

- `A1__LearnEnglish-Reading-A1-A-poster-at-work.pdf`
- `A1__LearnEnglish-Reading-A1-A-poster-for-exam-candidates.pdf`
- `A1__LearnEnglish-Reading-A1-A-restaurant-menu.pdf`
- `A1__LearnEnglish-Reading-A1-A-study-timetable.pdf`
- `A1__LearnEnglish-Reading-A1-An-airport-departures-board.pdf`
- `A1__LearnEnglish-Reading-A1-Business-cards.pdf`
- `A1__LearnEnglish-Reading-A1-Dictionary-definitions.pdf`
- `A1__LearnEnglish-Reading-A1-Holiday home adverts.pdf`
- `A1__LearnEnglish-Reading-A1-Job-adverts.pdf`
- `A1__LearnEnglish-Reading-A1-Notes-at-work.pdf`
- `A1__LearnEnglish-Reading-A1-Student-card-application.pdf`
- `A1__LearnEnglish-Reading-A1-Text-messages-to-a-friend.pdf`

## A2 (10)

- `A2__LearnEnglish-Reading-A2-A-message-to-a-new-friend.pdf`
- `A2__LearnEnglish-Reading-A2-An-airport-notice.pdf`
- `A2__LearnEnglish-Reading-A2-An-end-of-term-report.pdf`
- `A2__LearnEnglish-Reading-A2-An-infographic.pdf`
- `A2__LearnEnglish-Reading-A2-An-invitation-to-a-job-interview.pdf`
- `A2__LearnEnglish-Reading-A2-Choosing-a-conference-venue.pdf`
- `A2__LearnEnglish-Reading-A2-English-course-prospectus.pdf`
- `A2__LearnEnglish-Reading-A2-Professional-profile-summaries.pdf`
- `A2__LearnEnglish-Reading-A2-Study-skills-tips.pdf`
- `A2__LearnEnglish_Reading-A2-An-email-from-a-friend.pdf`

## B1 (13)

- `B1__LearnEnglish-Reading-B1-A-conference-programme.pdf`
- `B1__LearnEnglish-Reading-B1-A-flyer-for-a-gym.pdf`
- `B1__LearnEnglish-Reading-B1-A-travel-guide.pdf`
- `B1__LearnEnglish-Reading-B1-An-email-request-for-help.pdf`
- `B1__LearnEnglish-Reading-B1-Digital-habits-across_generations.pdf`
- `B1__LearnEnglish-Reading-B1-Encyclopedia-entry.pdf`
- `B1__LearnEnglish-Reading-B1-How-to-spot-fake-news.pdf`
- `B1__LearnEnglish-Reading-B1-Innovation-in-business.pdf`
- `B1__LearnEnglish-Reading-B1-Planning-an-event.pdf`
- `B1__LearnEnglish-Reading-B1-Robot-teachers.pdf`
- `B1__LearnEnglish-Reading-B1-Social-media-influencers.pdf`
- `B1__LearnEnglish-Reading-B1-The-Martian-a-book-review.pdf`
- `B1__LearnEnglish-Reading-B1-The-legend-of-fairies.pdf`

## B2 (12)

- `B2__LearnEnglish-Reading-B2-A-Plastic-Ocean-a-film-review.pdf`
- `B2__LearnEnglish-Reading-B2-A-short-story-extract.pdf`
- `B2__LearnEnglish-Reading-B2-An-email-from-a-friend.pdf`
- `B2__LearnEnglish-Reading-B2-Asteroids.pdf`
- `B2__LearnEnglish-Reading-B2-Cultural-expectations-and-leadership.pdf`
- `B2__LearnEnglish-Reading-B2-Instant-messages.pdf`
- `B2__LearnEnglish-Reading-B2-Millennials-in-the-workplace.pdf`
- `B2__LearnEnglish-Reading-B2-Star-Wars-and-the-hero-myth.pdf`
- `B2__LearnEnglish-Reading-B2-The-Buy-Nothing-movement.pdf`
- `B2__LearnEnglish-Reading-B2-The-sharing-economy.pdf`
- `B2__LearnEnglish-Reading-B2-Why-bridges-collapse.pdf`
- `B2__LearnEnglish-Reading-B2_Work-life-balance.pdf`

## C1 (12)

- `C1__LearnEnglish-Reading-C1-A-biography-of-Kilian-Jornet.pdf`
- `C1__LearnEnglish-Reading-C1-A-threat-to-bananas.pdf`
- `C1__LearnEnglish-Reading-C1-Cultural-behaviour-in-business.pdf`
- `C1__LearnEnglish-Reading-C1-Four-book-summaries.pdf`
- `C1__LearnEnglish-Reading-C1-Giving-and-receiving-positive-feedback.pdf`
- `C1__LearnEnglish-Reading-C1-Horror-film-cliches.pdf`
- `C1__LearnEnglish-Reading-C1-How-humans-evolved-language.pdf`
- `C1__LearnEnglish-Reading-C1-Life-on-Mars.pdf`
- `C1__LearnEnglish-Reading-C1-Managing-a-problem.pdf`
- `C1__LearnEnglish-Reading-C1-Political-manifestos.pdf`
- `C1__LearnEnglish-Reading-C1-Sustainable-supermarkets.pdf`
- `C1__LearnEnglish-Reading-C1-The-state-of-the-world.pdf`

