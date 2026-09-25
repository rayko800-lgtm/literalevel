# Modelo articulatorio para la boca 3D: informe de decisión

**Fecha:** 24 sep 2026 (noche). **Encargo:** `docs/ai/investigacion_modelo_articulatorio.md`.
**Estado:** entregables 1-5 hechos (25 sep, madrugada). Piloto en
`piloto.md`, cifras finales en `resultados.md`, integración en
`integracion.md`.

## Veredicto en una línea

Entrenar con **datos CC BY 4.0 solamente**: GRID + Lombard GRID (vídeo
frontal y de perfil, labios, mandíbula y mejillas) y **USC-TIMIT** (EMA de
labios, mandíbula y lengua, frases con todos los fonemas). Salida del modelo:
un **vector continuo de ~12 controles** que sustituye a las categorías de
`PoseSonido` antes de `poseNumerica`. Empezar por la base de referencia
(pose por fonema + dominancia de Cohen-Massaro), luego una TCN pequeña.

---

## 1. Inventario del rig (leído del código)

Lo que el visor interpola **no** es `PoseSonido`: es `PoseNumerica`, un
`Float64Array` que construye `poseNumerica()` en
`front/src/app/compartido/boca3d/escena.ts:953`. Las claves de la línea
(`animacion.ts`) guardan poses categóricas y `mezclarPose` interpola los
vectores numéricos.

Entradas de `PoseSonido` (`poses.ts`):

| Campo | Tipo | Rango |
|---|---|---|
| `mandibula` | continuo | 0–1 (× `MAND_MAX` = 0,21 rad) |
| `labios` | **categórico** | neutros, cerrados, redondeados, muy_redondeados, estirados, labiodental |
| `punta` | **categórico** | reposo, interdental, dental, alveolar, postalveolar, retrofleja |
| `punta_toca` | bool | |
| `cuerpo` | continuo | [altura, adelantamiento], 0–1 |
| `dorso_velo` | bool | |
| `dorso_alto` | continuo | 0–1 |
| `raiz` | continuo | 0–1 |
| `velo_abierto` | bool | |
| `rotica` | bool | (solo 3D) |

Salidas de `poseNumerica` (el vector que se interpola):
mandíbula (rad), velo (ángulo), labio superior (x, y, largo, radio), labio
inferior (x, y, largo, radio, local a la mandíbula), 6 nudos de la lengua
(x, y), 10 morfos de lengua (`mandibula, punta_arriba, punta_atras,
punta_interdental, cuerpo_alto, cuerpo_bajo, cuerpo_delante, cuerpo_atras,
dorso_velo, raiz_atras`), aire oral, contacto (x, y, hay), sonora,
`cierre_labios`, `compresion_labios`, `neutro_articulado`, `contorno_dental`.

Las shape keys de la piel se derivan en `aplicar` (`escena.ts:3349-3376`):
`fruncir` y `estirar` salen del **largo del labio** (1,05 fruncido … 2,3
neutro … 2,9 estirado); `labio_atras` del retroceso del labio inferior;
`abrir_neutro`, `cuerpo_labial`, `sonrisa`, `contorno_dental`, `sello_didactico`.

**Consecuencias para el modelo:**

1. El redondeo ya es de hecho una sola escala continua (el largo del labio).
   Un modelo puede predecirla directamente.
2. La punta de la lengua es categórica: hay que darle dos ejes continuos
   (altura y avance de la punta) o el modelo no puede coarticularla.
3. **No existe ningún control de mejillas.** «Mejillas que acompañan» exige
   una shape key nueva en Blender (`mejilla_arriba`, y quizá `mejilla_hinchar`)
   además del modelo. Es trabajo de malla, no de datos.

### Vector de controles propuesto (lo que predice el modelo)

| # | Control | Fuente de datos | Paso al rig |
|---|---|---|---|
| 1 | mandíbula | vídeo (subnasal–mentón), EMA (sensor de mandíbula) | `mandibula` |
| 2 | apertura labial | vídeo, EMA (LS–LI) | `cierre_labios` + posición del labio inf. |
| 3 | redondeo ↔ estiramiento | vídeo (ancho), perfil (protrusión), EMA (x de labios) | largo del labio 1,05–2,9 |
| 4 | compresión labial | vídeo (`mouthPress*`) | `compresion_labios` |
| 5 | labio inferior atrás (/f v/) | vídeo (`mouthRollLower`) | `labio_atras` |
| 6 | mejilla arriba | vídeo (`cheekSquint*`, pómulos) | **shape key nueva** |
| 7 | cuerpo: altura | EMA (dorso) / rtMRI | `cuerpo[0]` |
| 8 | cuerpo: avance | EMA / rtMRI | `cuerpo[1]` |
| 9 | punta: altura | EMA (sensor de punta) | nuevo, sustituye a `punta` |
| 10 | punta: avance | EMA | nuevo (interdental cuando pasa del incisivo) |
| 11 | dorso–velo | EMA (dorso) | `dorso_velo`, `dorso_alto` |
| 12 | raíz | rtMRI | `raiz` |
| — | velo, sonoridad, aire | **siguen por regla** (no se ven) | como hoy |

## 2. Datos (licencias verificadas hoy en la fuente)

| Fuente | Contenido | Licencia verificada | ¿Nuestro uso? |
|---|---|---|---|
| **GRID** ([Zenodo 3625687](https://zenodo.org/records/3625687)) | 34 hablantes × 1000 frases, vídeo frontal 25 fps, audio 25 kHz, alineación por palabra. 16,2 GB | **CC BY 4.0** | **Sí** (atribución) |
| **Lombard GRID** ([web](https://spandh.dcs.shef.ac.uk/avlombard/), Zenodo) | 54 hablantes × 100 frases, **frontal y perfil** sincronizados | **CC BY 4.0** | **Sí**; el perfil da la protrusión |
| **USC-TIMIT** ([Zenodo 19422914](https://zenodo.org/records/19422914)) | rtMRI de 10 hablantes GA, **EMA de 4**, 460 frases MOCHA (todos los fonemas). 8,5 GB | **CC BY 4.0** | **Sí** |
| **USC 75 hablantes** ([figshare 13725546](https://doi.org/10.6084/m9.figshare.13725546.v1)) | rtMRI 2D + 3D, 75 hablantes. 675,7 GB | **CC BY 4.0** | Sí, pero pesa demasiado: solo una muestra |
| HPRC (Haskins, [Box](https://yale.app.box.com/s/cfn8hj2puveo65fq54rp1ml2mk7moj3h)) | EMA, 8 hablantes, frases IEEE a dos velocidades, ~8 h | **No encontrada** («freely available», sin licencia escrita) | **No** hasta ver la licencia |
| mngu0 ([web](https://homepages.inf.ed.ac.uk/korin/site/research/mngu0/)) | EMA + MRI, 1 hablante británico | «free for research use», registro por correo | No (solo investigación) |
| MOCHA-TIMIT ([CSTR](https://www.cstr.ed.ac.uk/research/projects/artic/mocha.html)) | EMA, 2 hablantes | «free for non-commercial use» | Dudoso → no |
| VOCASET ([licencia](https://voca.is.tue.mpg.de/license.html)) | mallas 3D + audio, 12 hablantes | No comercial y prohíbe poner la Data «available in any form to any third party» | **No** |
| LRS3 (TED) | 433 h de vídeo | CC BY-NC-ND 4.0 + términos de TED (según fuentes secundarias) | **No** |
| MEAD | 60 actores, 7 vistas, emociones | El repo es MIT, pero el conjunto no publica licencia de datos | **No** hasta verla |
| TCD-TIMIT, VoxCeleb | vídeo | EULA de investigación (web de TCD caída hoy, 503) | No |
| Vídeos de Miguel (`Downloads/para astra.mp4`, `para blender.mp4`) | 8K, 30 fps, 200 s y 68 s, boca desde abajo | Privados | Solo calibración local, **nunca** fuera de su máquina/Drive |

**Alineación:** Montreal Forced Aligner 3.4.2 con el modelo acústico y el
diccionario `english_us_arpa` (el diccionario, **CC BY 4.0** según
[mfa-models](https://github.com/MontrealCorpusTools/mfa-models); la licencia
del modelo acústico no la comprobé, pero es una herramienta intermedia: ni
él ni sus salidas se publican).
**Medidas de vídeo:** MediaPipe Face Landmarker (478 puntos + 52
blendshapes), código y modelos Apache 2.0.

### Hueco medido de GRID

GRID tiene 51 palabras. Pasadas por el diccionario de la app
(`app/pronunciacion_cmu.tsv`), **faltan 8 fonemas**: /ŋ ʃ ʒ h ʊ ɝ ɚ ɔɪ/, y
/θ ð æ ɑ ʌ ɔ aʊ m/ salen en una sola palabra. Por eso GRID solo no basta y
entra USC-TIMIT (frases MOCHA, diseñadas para cubrir todos los fonemas en
muchos contextos): da labios y mandíbula por EMA para los fonemas que GRID no
tiene, además de la lengua.

### Combinación elegida

- **Labios, mandíbula, mejillas:** GRID (33 hablantes con vídeo) + Lombard
  GRID frontal. Protrusión: Lombard perfil (descargado, **aún sin medir**).
- **Lengua y cobertura de fonemas:** USC-TIMIT EMA (4 hablantes; M3 apartado porque sus transcripciones son de la sesión de MRI) para
  punta/dorso/labios/mandíbula; rtMRI de USC-TIMIT para la raíz (fase 3).
- **Descartado por licencia:** VOCASET y los pesos de VOCA/FaceFormer
  entrenados con él (la licencia de BIWI no la comprobé), LRS3, MOCHA,
  mngu0, TCD-TIMIT, MEAD, HPRC. Pendiente de Miguel solo HPRC si aparece
  una licencia: es la mejor fuente EMA después de USC-TIMIT.

## 3. Medidas y paso al rig

- **Vídeo** (`tools/modelo_articulatorio/medir_video.py`): por fotograma,
  apertura interior y exterior, ancho, mandíbula (subnasal–mentón), altura de
  comisuras, protrusión (z relativa), altura de pómulos, todo en distancias
  interoculares, más las 52 blendshapes. Normalización por hablante: z-score
  sobre su propio reposo (fotogramas de `sil`).
- **EMA:** sensores de punta, dorso, labios y mandíbula en el plano
  medio-sagital; se restan la cabeza (referencias) y se normalizan por
  hablante con su rango en la palabra de referencia.
- **Paso al rig (calibración):** el plan era renderizar el rig de frente y
  medirlo con MediaPipe, pero **el rig es media cabeza en corte sagital**
  (azimut limitado a −34°): no hay cara frontal que medir. Se calibra con
  las **poses comunes**: las 46 poses hechas a mano contra la media medida
  de esos mismos fonemas, una recta por control (`calibrar_rig.py`). La
  escala la ponen las poses de Miguel; la dinámica, el modelo. Resultado en
  `resultados.md` y `integracion.md`.

## 4. Arquitectura

| Opción | Pros | Contras | Coste |
|---|---|---|---|
| 1. Pose por fonema + dominancia Cohen-Massaro | interpretable, se exporta como tablas (objetivo, peso, α, θ por fonema y control), 0 MB de red | la coarticulación es una suma ponderada: no aprende casos no lineales | CPU, minutos |
| 2. TCN 1-D sobre fonemas con duración | contexto ±300 ms, <100 k parámetros (<0,5 MB), paralelo, trivial en JS | necesita datos alineados buenos | Colab T4, <1 h por entrenamiento |
| 3. Transformer pequeño | contexto largo | con 34+4 hablantes sobreajusta; más lento en móvil | varias horas |
| 4. Latente común vídeo + EMA | une labios y lengua | ningún conjunto tiene los dos a la vez: el alineamiento del latente es frágil | alto, investigación |

**Decisión:** 1 como vara de medir y respaldo exportable; 2 como candidato.
3 y 4 solo si 2 no bate a 1 por un margen claro en los hablantes de prueba.
Entrada: **fonemas con tiempos**, no audio (siempre tenemos el texto y el
audio del TTS no es humano: un modelo de audio aprendería otra voz).
Para labios y lengua a la vez sin opción 4: dos cabezas de salida sobre el
mismo codificador de fonemas, entrenando cada una con la pérdida enmascarada
de los controles que su conjunto sí mide.

## 5. Evaluación

- Hablantes de prueba nunca vistos: GRID s31–s34 (4), USC-TIMIT 1 de 4 EMA.
- Por control: RMSE, Pearson y desfase del pico (correlación cruzada, ±200 ms).
- Pruebas duras: cierre completo en /p b m/ (apertura interior ≈ 0),
  /f v/ (labio inferior atrás), redondeo anticipado de /u w/ (el ancho
  empieza a bajar antes del inicio acústico), /θ ð/ (punta pasa el incisivo,
  solo EMA).
- Reglas actuales de `animacion.ts` con las mismas métricas: se reproduce
  `lineaPalabra` en Python sobre los mismos tiempos de fonemas.

## 6. Plan

| Sesión | Dónde | Qué | Horas |
|---|---|---|---|
| 0 (hoy) | local | descargas, MFA, piloto 3 hablantes GRID, base 1 | 3–4 |
| 1 | local (12 núcleos, CPU) | medir las 33 × 1000 frases de GRID | ~2–4 (a medir en el piloto) |
| 2 | local | MFA sobre GRID y USC-TIMIT; tabla de fonemas con tiempos | 1–2 |
| 3 | Colab gratis (T4) | TCN, 3–5 entrenamientos; puntos de control en Drive | 2–3 |
| 4 | local + navegador | calibración del rig, evaluación contra reglas, hoja lado a lado | 3 |

Nada de esto necesita GPU de pago: MediaPipe corre en CPU y la TCN es
pequeña.

## 7. Riesgos

1. **GRID es habla de laboratorio**, con vocabulario cerrado y sintaxis fija:
   el modelo aprenderá esas transiciones mejor que otras. Se mitiga con
   USC-TIMIT y midiendo por separado los fonemas que GRID no tiene.
2. **Protrusión desde vídeo frontal** es débil (la z de MediaPipe es una
   estimación). Por eso Lombard perfil.
3. **Mejillas:** sin shape key nueva, lo que aprenda el modelo no tiene
   dónde mostrarse.
4. **La calibración rig ↔ humano** es el punto frágil: si el render no se
   parece a una cara, MediaPipe lo mide mal. Plan B: calibrar con 8–10 poses
   clave que Miguel juzgue a ojo, fijadas como constantes.
5. **HPRC**: sin licencia no se usa, aunque sea mejor que USC-TIMIT.
