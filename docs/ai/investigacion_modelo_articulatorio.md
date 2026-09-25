# Encargo: modelo de articulación para la boca 3D de LiteraLevel

**Para:** una sesión nueva (Claude, Codex o ChatGPT) que investigue, decida y
empiece a programar. **De:** Miguel, con el contexto de la sesión que hizo la
boca 3D didáctica (25 sep 2026).

## 1. Contexto

LiteraLevel es una app para practicar lectura y pronunciación en inglés
(front Angular en `front/`, API FastAPI en `app/api.py`, desplegada en Hugging
Face). En «Pronunciar» hay una cabeza 3D (Three.js) que articula cada sonido,
palabra y, desde el 25 sep, frases enteras leídas por el TTS de OpenAI.

- La animación NO sale de ningún modelo aprendido: cada sonido tiene una pose
  hecha a mano (`front/src/app/compartido/boca3d/poses.ejemplo.json` y
  `poses.ajustes3d.json`) y las palabras se encadenan con reglas de duración y
  coarticulación sencillas (`animacion.ts`: `lineaPalabra`, `lineaFrase`).
- Los controles del rig (lo que el modelo tiene que predecir) están en
  `poses.ts` y en `poseNumerica` de `escena.ts`: mandíbula, fruncir, estirar,
  labio_atras (/f v/), cierre y compresión de labios, abrir_neutro,
  contorno_dental y los parámetros de la lengua (punta, dorso, raíz,
  punta_interdental…). Haz primero el inventario exacto de esos controles y
  sus rangos, leyendo el código.
- Miguel quiere que se mueva con más naturalidad: coarticulación real, mejillas
  y mandíbula que acompañan, labios con cuerpo. **Aquí manda la precisión**, no
  la prisa: se puede trabajar en varias sesiones de Colab.

Antes de empezar: lee `docs/ai/HANDOFF.md` y `AGENTS.md`.

## 2. Objetivo

Un modelo que, dada una secuencia de fonemas con sus tiempos (la tenemos: IPA
de diccionario + audio de TTS alineado), devuelva **en cada fotograma los
valores de los controles del rig**, más natural que las reglas actuales y
medido contra datos reales. Debe ser pequeño y correr en el navegador en tiempo
real (objetivo: pesos < 2 MB, < 2 ms por fotograma en un móvil medio), o bien
exportarse como tablas y pesos que lea `animacion.ts`.

## 3. Qué tienes que investigar y decidir (con argumentos y cifras)

### 3.1 Datos

Para cada fuente: qué contiene, cuántos hablantes y horas, formato, **licencia
exacta y si permite usarla en una app pública** (entrenar y publicar pesos; no
publicar sus imágenes), y cómo se descarga. Verifica tú cada licencia en la
fuente original; lo de abajo son pistas, no hechos comprobados.

- **Video frontal de habla en inglés (labios, mandíbula, mejillas):**
  GRID audiovisual (se cree CC BY 4.0, 34 hablantes), LRS3 (TED, uso de
  investigación), TCD-TIMIT (licencia de investigación), VoxCeleb (investigación),
  MEAD, y los videos propios de Miguel (privados: nunca en Git ni en servidores
  públicos).
- **3D de caras hablando (lo más parecido a nuestro caso):** VOCASET y los
  conjuntos que usan VOCA, FaceFormer, CodeTalker, SelfTalk o EmoTalk (mallas o
  blendshapes con audio). Mira las licencias con especial cuidado.
- **Lengua y articulación interna (la vista de corte lateral):**
  electromagnetografía (EMA: MOCHA-TIMIT, mngu0, el corpus de Haskins de
  velocidad de habla) y resonancia en tiempo real (USC-TIMIT, el conjunto de
  75 hablantes de USC, 2021). Sirven para la lengua, que en video no se ve.
- **Alineación fonética:** Montreal Forced Aligner o similar, para tener los
  tiempos de cada fonema en cualquier audio.

Propón **qué combinación usar** y por qué. YouTube queda fuera por licencia.

### 3.2 Medidas y paso a nuestro rig

- Labios y mandíbula desde video: MediaPipe Face Landmarker (478 puntos y
  blendshapes) u otra alternativa. Define las medidas (apertura, ancho,
  protrusión, apertura de mandíbula, subida de mejilla, posición de comisuras),
  normalizadas por hablante.
- Lengua desde EMA/resonancia: punta, dorso y raíz, alturas y avance.
- **La función de paso** de esas medidas a los controles del rig. Hay que
  calibrarla: por ejemplo, poner el rig en poses conocidas, medir el render con
  el mismo MediaPipe y ajustar. Sin esto el mejor modelo no sirve.

### 3.3 Arquitectura

Compara, con pros, contras y coste de entrenamiento:

1. **Base de referencia:** pose objetivo por fonema aprendida de los datos más
   un modelo clásico de coarticulación (dominancia de Cohen-Massaro). Es barata
   e interpretable, y es la vara de medir.
2. **Red convolucional temporal (TCN / 1D-CNN)** sobre la secuencia de fonemas
   con duraciones (y opcionalmente rasgos del audio).
3. **Transformer pequeño** (estilo FaceFormer, pero con fonemas de entrada en
   vez de audio crudo, o con los dos).
4. **Multimodal:** un espacio latente común para labios (video) y lengua
   (EMA/resonancia), entrenado con los dos tipos de datos aunque ningún
   conjunto tenga los dos a la vez.

Criterio: precisión medida primero; luego tamaño y velocidad en el navegador.
La recomendación de partida (a confirmar o refutar con datos) es entrada por
**fonemas con tiempos**, no audio crudo, porque siempre conocemos el texto, y
empezar por 1 y 2 antes de 3 y 4.

### 3.4 Evaluación

- Hablantes de prueba que el modelo nunca ve.
- Por control: RMSE, correlación de Pearson y desfase temporal (el pico de
  apertura, ¿llega a tiempo?).
- Pruebas duras: cierre completo en /p b m/, labio contra dientes en /f v/,
  redondeo anticipado en /u w/ antes de que suene, lengua entre los dientes en
  /θ ð/.
- Comparación contra las reglas actuales de `animacion.ts` con las mismas
  métricas.
- Una hoja de video lado a lado (real contra 3D) para que Miguel juzgue.

## 4. Restricciones

- **Sin gasto:** no se compra nada. Colab gratis, con algo de GPU la semana que
  viene. Todo reanudable: puntos de control en Drive y un cuaderno que retoma
  donde se quedó.
- **Licencias:** si una fuente no permite nuestro uso, no se usa, aunque sea la
  mejor. Datos personales y videos de Miguel: privados, fuera de Git, del ZIP y
  de cualquier servidor público.
- **El repositorio lo tocan varias sesiones:** nada de `git stash`, `checkout`
  global ni `add -A`; commit solo de tus rutas. Trabaja en `investigacion/` o en
  `tools/modelo_articulatorio/`. **No toques `app/` ni `front/`** hasta que
  Miguel apruebe el modelo.
- Un solo hilo de trabajo. Nada de abrir más sesiones sin permiso.

## 5. Entregables, en este orden

1. **Informe de decisión** (un solo bloque markdown): fuentes con licencia
   verificada y enlace, medidas, paso al rig, arquitectura elegida y
   descartadas con su porqué, plan de sesiones de Colab con horas estimadas, y
   riesgos.
2. **Piloto pequeño antes que el lote:** 3 hablantes de GRID, medidas y
   alineación, y la base de referencia (opción 1) evaluada. Con cifras.
3. Cuadernos y scripts de descarga, medida, entrenamiento y evaluación,
   reanudables.
4. Modelo elegido evaluado contra la base de referencia y contra las reglas
   actuales.
5. Propuesta de integración en `animacion.ts` (formato de pesos, coste por
   fotograma), sin tocar la app todavía.

Pide decisión a Miguel solo cuando haya que elegir algo que es suyo (por
ejemplo, una licencia dudosa o gastar horas de GPU).
