# Validación del v4 con UniversalCEFR — 12 de septiembre de 2026

Medido con `validar_universalcefr.py`, en local (CPU), en 4,3 minutos. Se
reproduce en cualquier máquina: el guion se baja solo los dos conjuntos.

## El corpus

Los dos conjuntos **ingleses de referencia y de documento completo** de
UniversalCEFR (Imperial et al., EMNLP 2025), públicos en Hugging Face, sin
términos que aceptar, licencia **CC BY-NC-SA 4.0**:

| Conjunto | Filas | Niveles |
|---|---|---|
| `UniversalCEFR/cambridge_exams_en` | 331 | A2–C2 |
| `UniversalCEFR/elg_cefr_en` | 712 | A1–C2, con A2+/B1+/B2+ |

Los otros cuatro conjuntos ingleses de la colección no sirven para esto:
`cefr_sp_en` y `readme_en` son frases sueltas; `icle500_en` y `cefr_asag_en`
son textos **escritos por estudiantes**, que miden producción y no dificultad de
lectura.

**Se solapan.** 130 textos están en los dos, y en los 136 pares de filas el
nivel coincide: es la misma fuente reetiquetada, no dos opiniones. Se deduplica
por texto normalizado.

| | |
|---|---|
| Filas | 1.043 |
| Sin repetir | 901 (142 repetidas) |
| Por debajo de 150 palabras | 74 |
| Rechazados por `continuous_prose` («lista, menú o tabla») | 88 |
| **Puntuados** | **739** |

## Resultado

| Nivel | n | Media 0–2 | Desv. (pobl.) |
|---|---|---|---|
| A1 | 24 | 0,0797 | 0,109 |
| A2 | 100 | 0,3421 | 0,143 |
| B1 | 203 | 0,7596 | 0,242 |
| B2 | 180 | 1,3021 | 0,202 |
| C1 | 127 | 1,6564 | 0,223 |
| C2 | 105 | 1,8971 | 0,102 |

| | Los dos (739) | Cambridge (220) | ELG (519) |
|---|---|---|---|
| Spearman del v4 contra el nivel | **0,946** | 0,933 | 0,942 |
| Spearman de contar palabras | 0,663 | 0,739 | 0,537 |
| v4 descontando la longitud (parcial) | **0,906** | 0,868 | 0,921 |
| v4 contra longitud | 0,646 | 0,687 | 0,512 |

Medias estrictamente crecientes en los seis niveles. El validador puede
suspender y no suspendió.

## Lo que NO se puede afirmar, y por qué

**No es una validación externa demostrada.** La composición del corpus de
anclaje del v4 (654 documentos) no está en el repositorio: es un hueco abierto
desde `auditoria/informe_fable.md` y `auditoria/verificacion_pendientes.md`.
Si ese corpus contiene textos de Cambridge o de ELG, esta cifra está medida en
parte sobre lo que el modelo ya vio.

Y hay una señal que empuja en esa dirección, que no se esconde: **0,946 es más
alto que la validación interna del propio v4 (0,908 sobre 144 documentos
reservados del anclaje)**. Un conjunto externo rara vez supera al de validación
interna. Lo que sí apunta a independencia, sin demostrarla: el cuaderno del v1
al v3 (`notebook_v4_dump.py:2433`) daba los exámenes de Cambridge como «dominio
de validación pendiente», no de entrenamiento.

Cómo se publica, entonces: **como validación reproducible y a escala, con la
advertencia escrita al lado**, nunca como «externa» a secas.

## Lo que sí cambia en el documento

1. **La escala no sale comprimida en este corpus.** Con British Council los
   cinco niveles ocupaban de 0,50 a 1,50; aquí los seis van de 0,08 a 1,90. La
   limitación de «escala comprimida» hay que matizarla: se observó en 47 textos
   de una sola fuente.
2. **A1 y A2 sí se distinguen aquí** (0,08 frente a 0,34, con n = 24 y 100),
   cuando en British Council eran casi iguales (0,504 frente a 0,556, n = 3 en
   A1).
3. **El contraste con la longitud es mucho más favorable**: contar palabras da
   0,663 y el modelo conserva 0,906 descontándola, frente a 0,807 y 0,668 en
   British Council. En exámenes graduados, nivel y longitud van confundidos; en
   este corpus, bastante menos.
