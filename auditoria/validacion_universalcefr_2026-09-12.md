# Validación del v4 con UniversalCEFR — 12 de septiembre de 2026

> **ACTUALIZACIÓN, el mismo día: hubo fuga, confirmada.** Lo que sigue abajo
> es la primera versión de esta validación y **sus cifras no valen como
> validación**. Se deja como registro de cómo se encontró.
>
> **La prueba.** El guion de entrenamiento del v4, `ll_v4_transformer.py`
> (Drive del proyecto, carpeta `src`, 6 de septiembre de 2026), carga un único
> archivo de datos:
>
> ```
> DATA_PATH = DRIVE / "elg-cefr-en.json"
> "source": "ELG CEFR English, CC BY-NC-SA 4.0"
> train_test_split(docs, test_size=0.22, random_state=SEED, stratify=strata)
> ```
>
> Y su tarjeta de métricas, `metricas_literalevel_v4.json` (carpeta `outputs`),
> lo confirma al número: **654 documentos aceptados + 57 cortos + 1 descartado
> por forma de frase = 712**, que es exactamente el tamaño de
> `UniversalCEFR/elg_cefr_en`. Partición 510 / 144, Spearman de validación
> 0,9084 y 97,22 % dentro de un nivel: las cifras que publica el documento.
>
> **Consecuencias:**
>
> 1. `elg_cefr_en` **es el corpus de entrenamiento del v4**. Medirlo no es
>    validar: el 0,946 de abajo medía, en su mayor parte, textos vistos.
> 2. `cambridge_exams_en` comparte 130 textos con ELG, así que **también está
>    contaminado en parte**. Solo vale lo que no esté en ELG.
> 3. **Se cierra un hueco abierto desde la primera auditoría**
>    (`informe_fable.md`, crítico 2): ya se sabe de qué está hecho el corpus de
>    anclaje. **British Council no estaba en el entrenamiento**: el guion lo usa
>    como `british_council_development_validation` (38 documentos, Spearman
>    0,829). Se miró durante el desarrollo, que es lo que el documento ya
>    llamaba «no del todo ciega».
>
> `validar_universalcefr.py` se reescribió para excluir ELG y medir solo los
> textos de Cambridge que no están en él, ni idénticos ni casi idénticos.

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

## La comprobación limpia, con `validar_universalcefr.py` reescrito

| `cambridge_exams_en` sin repetir | 325 |
|---|---|
| Idénticos a un texto de ELG | 130 |
| Casi idénticos (≥ 50 % de sus 8-gramas dentro de un texto de ELG) | 195 |
| **Limpios** | **0** |

Los 195 casi idénticos no salen de un umbral flojo. La fracción de 8-gramas
compartidos con el texto de ELG más parecido tiene **mediana 0,921** (percentil
10: 0,781; mínimo: 0,557); 122 comparten el 90 % o más; y **en los 195 el texto
de ELG tiene el mismo nivel**. Es el mismo texto con otra puntuación o con otro
encabezado.

**Conclusión: ninguno de los dos conjuntos ingleses de referencia de
UniversalCEFR sirve para validar el v4.** Las cifras de la primera versión se
retiran de los entregables y quedan aquí solo como registro.
