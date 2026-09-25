# Piloto: 3 hablantes de GRID (24 sep 2026, noche)

**Veredicto:** el modelo de dominancia (Cohen-Massaro aprendido) sigue a la
boca real bastante mejor que el calendario de claves de `animacion.ts`
(Pearson medio **0,54 contra 0,41**) y no llega tarde; el calendario actual
va **~80 ms tarde en la mandíbula**. La TCN empata con la dominancia con solo
2 hablantes de entrenamiento: el lote completo decide entre las dos.

## Qué se hizo

| Paso | Guion | Resultado |
|---|---|---|
| Descarga s1–s3 + alineaciones oficiales | curl, Zenodo 3625687 | 3 × 1000 vídeos, 360×288, 25 fps |
| Medida por fotograma | `medir_video.py` (MediaPipe 1.0.1, CPU) | s1: cara en los 75 fotogramas en 984 vídeos; en 16 faltan 8–12 (se interpolan). ~0,5 vídeos/s por proceso |
| Alineación por fonema | `corpus_mfa_grid.py` + MFA 3.4.2 (`english_us_arpa`) | 3 × 1000 TextGrid; el inicio de «bin» en `bbaf2n` cae a 0,97 s (GRID dice 0,95) |
| Conjunto por hablante | `datos_fonemas.py` | s1 989, s2 997, s3 991 frases (~74 000 fotogramas cada uno) |
| Base y varas | `base_dominancia.py` | un hablante fuera cada vez |
| TCN (86 380 parámetros, 0,35 MB en float32) | `tcn.py`, 30 épocas, CPU | igual reparto |
| Pruebas duras | `pruebas_duras.py` | cierre /p b m/ y redondeo anticipado |

Los datos y resultados viven en `D:/literalevel_articulatorio/` (fuera de
Git): `resultados/piloto/{base,tcn,pruebas}.json` y los `.pt`.

Las «reglas» se reproducen en Python con el calendario de `lineaPalabra`
(claves a 0,38–0,72 del tramo, oclusivas 0,45–0,80, curva `suavizar`) y
**las mismas poses objetivo que la dominancia** (la media medida por fonema),
así que la comparación mide solo la dinámica, no las poses hechas a mano.

## Correlación y error por control (media de los 3 pliegues)

Pearson / RMSE en unidades z del hablante.

| Control | Escalón | Reglas | Dominancia | TCN |
|---|---|---|---|---|
| apertura interior | 0,58 / 0,83 | 0,57 / 0,83 | **0,73** / 0,71 | **0,74** / 0,72 |
| ancho | 0,31 / 0,94 | 0,36 / 0,91 | **0,59** / 0,80 | 0,58 / 0,83 |
| mandíbula | 0,55 / 0,87 | 0,54 / 0,87 | **0,73** / 0,78 | **0,73** / 0,80 |
| protrusión | 0,21 / 0,97 | 0,25 / 0,95 | 0,48 / 0,86 | **0,50** / 0,88 |
| mejilla (pómulos) | 0,29 / 0,93 | 0,34 / 0,92 | **0,45** / 0,89 | 0,42 / 0,93 |
| jawOpen | 0,51 / 0,87 | 0,50 / 0,88 | 0,67 / 0,76 | **0,70** / 0,77 |
| mouthPucker | 0,37 / 0,77 | 0,42 / 0,74 | **0,56** / 0,70 | 0,53 / 0,74 |
| mouthFunnel | 0,44 / 0,81 | 0,42 / 0,81 | **0,55** / 0,76 | **0,55** / 0,78 |
| mouthRollLower | 0,47 / 0,79 | 0,43 / 0,79 | 0,46 / 0,80 | 0,45 / 0,82 |
| mouthPress | 0,35 / 0,90 | 0,40 / 0,88 | 0,43 / 0,94 | 0,43 / 1,02 |
| mouthClose | 0,38 / 0,85 | 0,45 / 0,83 | **0,52** / 0,80 | **0,52** / 0,82 |
| cheekSquint | 0,21 | 0,23 | 0,35 | 0,34 |
| **media** | 0,39 / 0,80 | 0,41 / 0,79 | **0,54** / 0,74 | **0,54** / 0,76 |

**Desfase** (correlación cruzada ±200 ms; positivo = la predicción llega
tarde): reglas **+82 ms** en mandíbula, +44 en jawOpen, +35 en apertura;
dominancia y TCN entre −22 y +11 ms en todos los controles.

## Pruebas duras

- **Cierre /p b m/** (mínimo de la apertura interior, ~1350 segmentos por
  hablante): depende del hablante de prueba. Dentro de 0,3 z del real:
  dominancia 48 / 24 / 91 %, TCN 33 / 32 / 68 %, reglas 83 / 2 / 2 %
  (s1 / s2 / s3). Con 2 hablantes de entrenamiento la profundidad del cierre
  hereda la de los otros: **no concluyente**; hace falta el lote y quizá una
  normalización del cierre por hablante (su percentil 5 como cero).
- **Redondeo anticipado /uw w/** (~900 casos por hablante): en GRID el
  ancho llega a medio camino **10–30 ms** antes del inicio acústico
  (mediana). Dominancia 0–30 ms, TCN −10 a 40, reglas −30 a 60. Es habla
  de laboratorio: la anticipación real es pequeña.
- **/f v/**: las blendshapes no lo ven. `mouthRollLower` en /f/ sale −0,14 z
  (debería subir). A 360×288 el labio contra los dientes no es medible:
  **/f v/ seguirá por regla** o necesita el perfil de Lombard GRID.
- **/θ ð/**: la lengua no se ve en vídeo; queda para USC-TIMIT (EMA).

## Lo que cambia en el plan

1. `cheekSquint` casi no varía en GRID (RMSE 0,05 en z ya normalizada:
   ruido). La mejilla se mide mejor con la geometría de los pómulos.
2. /f v/ no sale del vídeo frontal: el perfil de Lombard entra antes.
3. El lote completo (33 hablantes) ya está en marcha: `lote_grid.sh`.
   Tiempo medido: 8 procesos midieron 2000 vídeos (s2 y s3) en ~12 min;
   MFA tarda ~8 min por hablante.
