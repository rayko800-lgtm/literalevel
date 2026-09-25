# Resultados con todos los datos (25 sep 2026, madrugada)

**Veredicto:** con los tiempos de fonema bien medidos, el modelo aprendido
sigue a la boca real con Pearson **0,57** frente a **0,44** del calendario de
`animacion.ts`, que además llega **60 ms tarde** a la mandíbula. Con los
tiempos que la app sabe calcular hoy (sin alinear el audio del TTS), las
reglas caen a **0,32** y la TCN entrenada para esos tiempos da **0,53**. La
dominancia (tablas, 12,6 KB) y la TCN (0,35 MB) empatan: **gana la dominancia
por coste**, salvo que la TCN conjunta (abajo) marque diferencia.

## Datos usados

| Conjunto | Hablantes | Frases | Horas | Licencia |
|---|---|---|---|---|
| GRID (vídeo frontal, 25 fps) | 33 | 32 936 | 27,4 | CC BY 4.0 |
| Lombard GRID (vídeo frontal, 24 fps) | 54 | 5 385 medidas | ~3,7 | CC BY 4.0 |
| USC-TIMIT EMA (6 sensores, 50 Hz) | 3 (M3 apartado) | 1 450 | 1,2 | CC BY 4.0 |

Hablantes de prueba, nunca vistos: GRID s31–s34 (4 000 frases), Lombard
ls50–ls55, EMA f5 (y los otros dos EMA por turnos).

## GRID, 29 hablantes de entrenamiento, 4 de prueba

Pearson / RMSE (z del hablante). «Reglas» = el calendario de `lineaPalabra`
con las mismas poses objetivo que el modelo (medias medidas): compara solo
la dinámica.

| Control | Escalón | Reglas | Dominancia | TCN | TCN, tiempos de la app |
|---|---|---|---|---|---|
| apertura interior | 0,70 / 0,71 | 0,69 / 0,73 | 0,80 / 0,58 | **0,81 / 0,56** | 0,76 / 0,62 |
| ancho | 0,40 / 0,88 | 0,44 / 0,86 | **0,63 / 0,74** | 0,60 / 0,75 | 0,55 / 0,79 |
| mandíbula | 0,68 / 0,76 | 0,67 / 0,78 | 0,77 / 0,68 | **0,78 / 0,67** | 0,75 / 0,69 |
| protrusión | 0,28 / 0,93 | 0,31 / 0,93 | **0,52 / 0,82** | 0,48 / 0,85 | 0,44 / 0,87 |
| mejilla (pómulos) | 0,26 / 0,94 | 0,29 / 0,93 | **0,40 / 0,89** | 0,38 / 0,89 | 0,37 / 0,90 |
| jawOpen | 0,67 / 0,74 | 0,65 / 0,75 | 0,74 / 0,65 | **0,76 / 0,63** | 0,71 / 0,68 |
| mouthPucker | 0,35 / 0,74 | 0,40 / 0,72 | 0,52 / 0,69 | **0,54 / 0,68** | 0,50 / 0,72 |
| mouthFunnel | 0,52 / 0,78 | 0,51 / 0,79 | 0,62 / 0,73 | **0,65 / 0,71** | 0,59 / 0,74 |
| mouthRollLower | 0,28 / 0,78 | 0,28 / 0,77 | 0,28 / 0,80 | 0,31 / 0,81 | 0,27 / 0,81 |
| mouthPress | 0,27 / 0,92 | 0,29 / 0,91 | **0,43 / 0,86** | 0,42 / 0,87 | 0,42 / 0,87 |
| mouthClose | 0,35 / 0,82 | 0,39 / 0,81 | **0,52 / 0,76** | 0,51 / 0,76 | 0,49 / 0,78 |
| cheekSquint | 0,40 | 0,40 | 0,50 | 0,54 | 0,50 |
| **media** | 0,432 | 0,443 | 0,560 | **0,566** | 0,530 |

Reglas con los tiempos de la app (sin alinear): **0,315**.

**Desfase** (positivo = llega tarde): reglas +60 ms en mandíbula, +41 en
funnel, +36 en apertura; dominancia y TCN entre −6 y +35 ms (los más tarde:
protrusión y mejillas, ~+30).

**Pruebas duras** (s31–s34):
- Cierre /p b m/ (5 460 segmentos): el mínimo de apertura queda a menos de
  0,3 z del real en el **73 %** (dominancia), **72 %** (TCN), **58 %**
  (reglas).
- Redondeo anticipado /uw w/ (3 818 casos): el ancho real llega a medio
  camino **40 ms** antes del sonido (mediana); dominancia 10 ms, TCN 20 ms,
  reglas **−20 ms** (después del sonido). Ninguno anticipa tanto como la
  cara real; las reglas van al revés.

## Lombard GRID (48 de entrenamiento, 6 de prueba)

| | Pearson medio |
|---|---|
| Reglas, tiempos de la app | 0,271 |
| Escalón | 0,364 |
| Reglas | 0,406 |
| Dominancia | 0,550 |
| TCN | **0,564** |
| TCN, tiempos de la app, entrenada con tiempos de MFA | 0,456 |
| TCN, tiempos de la app, entrenada con esos mismos tiempos | 0,498 |

Aquí `mouthRollLower` sí ve /f v/ (sube +0,64 y +0,31 z): la cámara está más
cerca que en GRID.

## Lengua: USC-TIMIT EMA (uno fuera cada vez)

| Prueba | Escalón | Reglas | Dominancia | TCN |
|---|---|---|---|---|
| f1 | 0,454 | 0,475 | 0,627 | **0,646** |
| f5 | 0,402 | 0,427 | 0,632 | **0,659** |
| m1 | 0,456 | 0,471 | 0,649 | **0,667** |

Con dos hablantes de entrenamiento. Medias por fonema coherentes: /θ ð/
adelantan la punta (+0,8 z), /k g ŋ/ suben el dorso (+1,2 a +1,5 z), /ɑ/
abre la mandíbula (+1,8 z), /ʃ/ protruye los labios (+1,8 z).

## TCN conjunta (vídeo + EMA, un codificador)

12 épocas, 33 668 frases de vídeo (GRID + Lombard) y 964 de EMA de
entrenamiento. Media por hablante de prueba:

| Prueba | Conjunta | Modelo propio del conjunto |
|---|---|---|
| GRID s31–s34 | **0,577** (0,62 / 0,70 / 0,51 / 0,48) | TCN 0,566 · dominancia 0,560 |
| Lombard ls50–ls55 | 0,559 | TCN 0,564 · dominancia 0,550 |
| EMA f5 | 0,650 | TCN 0,659 |

Sin la EMA (misma red, solo vídeo): GRID 0,570, Lombard **0,582**. Compartir
el codificador con la lengua no mejora el vídeo (GRID +0,007, Lombard
−0,023); lo que sí ayuda es entrenar GRID y Lombard juntos (Lombard pasa de
0,564 a 0,582). Un solo modelo sirve para los tres conjuntos perdiendo como
mucho 0,02, que es lo que se paga por tener una sola red en el navegador.

## Lo que esto decide

1. **Los tiempos pesan tanto como el modelo.** Con tiempos de regla, el
   mejor modelo pierde 0,04–0,10. Alinear el audio del TTS (o guardar
   alineaciones hechas offline para las palabras y frases fijas de
   Pronunciar) vale tanto como cambiar la dinámica. Es una decisión de
   Miguel: alinear en la API cuesta CPU del Space; offline no cuesta nada.
2. **Con tiempos bien alineados, dominancia.** Empata con la TCN en labios
   y mandíbula (0,560 contra 0,566), se exporta como tablas de 12,6 KB, se lee
   en `animacion.ts` sin red neuronal y es explicable fonema a fonema.
   **Sin alinear, la TCN entrenada con los tiempos de la app** (0,53 en GRID,
   0,50 en Lombard, contra 0,32 y 0,27 de las reglas actuales). En la
   lengua gana la TCN por ~0,02.
3. **/f v/** no se aprende de GRID (cámara lejos); Lombard sí lo ve.
