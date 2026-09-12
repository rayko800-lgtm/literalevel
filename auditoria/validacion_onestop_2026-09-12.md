# Validación externa del v4 con OneStopEnglish — 12 de septiembre de 2026

Medido con `validar_onestop.py`, en local (CPU), en 5,5 minutos. Las
puntuaciones, sin texto, están en `validacion_onestop_puntuaciones.csv`.

## Por qué esta sí es externa

El v4 se entrenó solo con ELG CEFR English (`entrenamiento_v4/ll_v4_transformer.py`).
Ningún texto de OneStopEnglish comparte con ELG ni un 8-grama de palabras:
fracción máxima compartida, **0,000**. La comprobación va dentro del guion y se
repite en cada ejecución, porque la validación anterior con UniversalCEFR se
publicó sin ella y resultó medir el entrenamiento.

**Matiz:** OneStopEnglish sí se usó para desarrollar los modelos v1 a v3 (el v2
se afinó con él). Es externo para los pesos del v4, no virgen para el proyecto.

## Un defecto del propio corpus que costó una cifra mal calculada

La carpeta Intermediate del repositorio de OneStopEnglish trae **dos copias de
cada artículo**, con diferencias de unas pocas palabras (`Amazon-int.txt`: 513 y
518). La primera ejecución:

- dio a Intermediate doble peso en Spearman y en las medias (378 textos frente a
  189);
- y, al calcular el orden dentro de cada artículo, llegaba a comparar las dos
  copias entre sí. Dio 39,5 %, **una cifra sin sentido que no se publicó**.

Se corrigió promediando por artículo y nivel: 560 unidades, una por artículo y
nivel.

## Resultado

| Nivel | n | Media v4 (0–2) | Desv. |
|---|---|---|---|
| Elementary | 185 | 0,9343 | 0,182 |
| Intermediate | 189 | 1,2715 | 0,182 |
| Advanced | 186 | 1,5149 | 0,191 |

| | Modelo v4 | Contar palabras |
|---|---|---|
| Spearman con el nivel | **0,800** | 0,692 |
| Correlación parcial, descontando la longitud | **0,688** | indefinida |
| Artículos con sus tres versiones en orden (de 185) | **183** | **179** |
| Parejas bien ordenadas (de 555) | 551 | 547 |

## La trampa que se evitó

El «183 de 185» parecía la prueba más limpia del proyecto: el mismo artículo, con
el mismo tema, escrito a tres niveles. **Pero la longitud sola ya ordena bien
179**, porque las versiones avanzadas son más largas (523, 667 y 809 palabras de
media). Donde la longitud falla, que son seis artículos, el modelo acierta en
cinco, y solo falla en uno donde la longitud acertaba. La ventaja existe y es
pequeña. Lo que de verdad sostiene al modelo en este corpus es la correlación
parcial: **0,688 descontando la longitud**.

Y la escala vuelve a salir comprimida y desplazada hacia arriba: un texto
Elementary puntúa 0,93, dentro de la banda intermedia.
