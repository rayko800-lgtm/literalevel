# Informe de velocidad — `perfil_de_texto` (modelo v4)

> Documento vivo: se va rellenando según se miden las cosas. Todo lo que aparece
> aquí está **medido en esta máquina**; lo que no se midió lo digo explícitamente.
> No se ha tocado `app/scoring.py` ni `app/ui.py`.

## 0. Máquina y entorno (medido)

| Dato | Valor |
|---|---|
| CPU | AMD Ryzen 5 2600 — 6 núcleos físicos / 12 lógicos |
| GPU | NVIDIA GTX 1650 SUPER, 4 GB, driver 591.86 |
| Python | 3.11.9 (64 bit) |
| torch | **2.14.0+cpu** — `torch.cuda.is_available() == False` |
| transformers | 5.16.1 |
| `torch.get_num_threads()` por defecto | 6 |
| Disco C: libre | 7,47 GiB (8.025.280.512 B) |
| Disco D: libre | 833,5 GiB (895.012.282.368 B) |

## 1. El trabajo real

Reproduzco lo que hace `app/ui.py:1007`: para cada capítulo con ≥150 palabras que
no sea relleno ni boilerplate, `perfil_de_texto(ficha.sin_licencia(c.texto))`.

| Libro | Palabras | Capítulos analizados | **Ventanas** |
|---|---|---|---|
| `pg2554.epub` Crime and Punishment | 206.864 | 41 | **840** |
| `pg2600.epub` War and Peace | 567.555 | 362 | **2.459** |

El dato de partida "2.475 ventanas en War and Peace" queda **confirmado con
desviación menor del 1 %** (2.459 con el filtrado actual de capítulos).

**Hallazgo estructural (importante para la palanca del lote):** el lote actual es
*por capítulo*, y los capítulos son pequeños. El capítulo más grande de Crime and
Punishment son 31 ventanas y el más grande de War and Peace, 17. Es decir, el
tamaño de lote real hoy es de ~20 ventanas en C&P y ~7 en W&P, no "todas las
ventanas del libro". Probar lotes de 64 o 128 **exige agrupar ventanas de varios
capítulos**, cosa que hoy el código no hace.

### Dos datos que cambian el diagnóstico

1. **Cargar el modelo no tarda ~1 min: tarda 0,9 s** (medido, `from_pretrained`
   de tokenizer + modelo desde `./modelo_v4`). El minuto que se percibe es el
   arranque del proceso e `import torch`/`transformers`, no los pesos.
2. **No hay padding que optimizar.** De 200 ventanas medidas, el **100 %** llega
   a exactamente 256 tokens tras truncar (250 palabras inglesas > 256 BPE
   siempre). Todos los lotes son rectangulares 256 de ancho, así que reagrupar
   ventanas en lotes distintos no cambia la forma del tensor por fila.

### Aviso de contención (afecta a los números absolutos)

Durante las medidas hay **otro proceso Python ajeno** consumiendo CPU en esta
máquina (PID 31324, `python -X utf8 -`, ~120 s de CPU en 2 min de reloj), además
del servidor Gradio (`compartir.py`, PID 23984, prácticamente inactivo). No lo he
matado (regla explícita). Con 6 núcleos físicos y dos procesos de 6 hilos, los
tiempos absolutos de esta tanda salen **pesimistas**. Las comparaciones
*relativas* entre palancas siguen siendo válidas porque todas sufren lo mismo.
Al final del informe se anota si se pudo repetir la medida en máquina ociosa.

## 2. Línea base (MEDIDA)

Código actual sin tocar: lote = capítulo, `torch.no_grad()`, 6 hilos,
`torch.set_num_threads` por defecto. Libro completo `pg2554.epub`.

| Métrica | Valor medido |
|---|---|
| Ventanas | 840 |
| **Total** | **156,3 s** |
| Tokenización | **0,6 s (0,4 %)** |
| Forward | **155,6 s (99,6 %)** |
| **Ventanas/s** | **5,38** |

El dato conocido (~5,7 v/s sobre Notes from a Dead House) queda **confirmado**:
5,38 v/s aquí, con contención de otro proceso en marcha.

**La tokenización no es el problema.** Optimizarla no puede dar más de un 0,4 %.
Todo el tiempo está en el forward de distilroberta sobre 256 tokens.

## 3. Palancas

### 3.a `torch.set_num_threads(N)` — MEDIDO

286 ventanas (14 capítulos completos de C&P), lote = capítulo, `no_grad`.
Máquina ya sin el proceso ajeno.

| Hilos | Total (s) | Ventanas/s | vs. defecto (6) |
|---|---|---|---|
| 1 | 158,2 | 1,81 | 0,29× |
| 2 | 85,5 | 3,34 | 0,54× |
| 3 | 85,0 | 3,37 | 0,55× |
| 4 | 66,1 | 4,33 | 0,70× |
| **6 (defecto)** | 46,4 | **6,16** | 1,00× |
| 8 | 42,7 | 6,70 | 1,09× |
| **12** | **41,1** | **6,96** | **1,13×** |

**Conclusión:** subir a 12 hilos (los lógicos, con SMT) da **+13 %**. Es gratis y
**no cambia ni un decimal** (mismo grafo, mismo dtype; solo cambia el reparto de
hilos de oneDNN). Escalado pobre por encima de 6: el forward está limitado por
ancho de banda de memoria, no por ALU.

Ojo al comparar con la línea base: 5,38 v/s de la base es con el proceso ajeno
compitiendo; **la base limpia con 6 hilos es 6,16 v/s**. Uso 6,16 como referencia.

### 3.b Tamaño de lote — MEDIDO

Las mismas 300 ventanas, 12 hilos, `no_grad`, agrupadas en lotes fijos (ya no
por capítulo).

| Lote | Total (s) | Ventanas/s |
|---|---|---|
| 1 | 48,7 | 6,16 |
| 8 | 44,9 | 6,68 |
| 16 | 41,1 | 7,29 |
| 32 | 37,9 | 7,91 |
| **64** | 36,6 | **8,19** |
| 128 | 36,3 | 8,27 |
| 300 (todo) | 36,3 | 8,27 |

Satura en 64. De 64 a 300 sólo gana un 1 %. Frente al agrupado actual por
capítulo con 12 hilos (6,96 v/s), lotes fijos de 64 dan **+18 %**.

**Exactitud del reagrupado — la comprobación clave:** las mismas 300 ventanas
puntuadas de una en una (lote 1) y en un solo lote de 300 salen
**MAE = 0,000000, máx = 0,000000, 300/300 valores idénticos bit a bit**. Es lo
esperado, porque todas las ventanas ocupan exactamente 256 tokens y no hay
padding: cambiar el agrupado **no puede** mover un decimal. Palanca segura.

### 3.c `inference_mode` vs `no_grad` — MEDIDO

Mismas 300 ventanas, lote 300, 12 hilos, mejor de 2 pasadas:

| Contexto | Total (s) | Ventanas/s |
|---|---|---|
| `no_grad` | 35,2 | 8,53 |
| `inference_mode` | 35,3 | 8,50 |

**Diferencia nula** (0,4 %, por debajo del ruido). En inferencia pura sin
autograd activo no hay nada que ganar. No cambia números, pero tampoco aporta.

### 3.d Cuantización dinámica int8 — MEDIDO, Y SE DESCARTA

`torch.ao.quantization.quantize_dynamic(mod, {nn.Linear}, qint8)`, mismas 300
ventanas, lote 300, 12 hilos.

| | Ventanas/s | Ganancia |
|---|---|---|
| fp32 | 8,53 | — |
| int8 dinámico | **10,06** | **+18 %** |

**Desviación en la escala pública 0–2, sobre las mismas 300 ventanas:**

| Métrica | Valor |
|---|---|
| Error medio absoluto (MAE) | **0,210** |
| Error máximo | **0,379** |
| Media fp32 → media int8 | 1,682 → 1,472 (**sesgo −0,21**) |

Un 18 % de velocidad a cambio de mover cada ventana **0,21 puntos de 2**, y con
sesgo sistemático a la baja: un texto de 1,68 pasa a 1,47, o sea cruza de
"avanzado" a "intermedio" (el corte está en 1,6). **Inaceptable.** Descartada.

### 3.f GPU — MEDIDO. Es la palanca grande.

**Coste en disco (real, medido):** venv aparte en `D:\ll_bench\venv_cuda` con
`torch==2.9.1+cu126` + `transformers==5.16.1` + numpy = **4,3 GB en D:**
(rueda de 2,41 GB descargada; caché de pip y TMP redirigidos a `D:`).
**Bytes escritos en `C:`: cero.** El entorno principal no se ha tocado:
sigue con `torch 2.14.0+cpu`.

CUDA funciona: `torch 2.9.1+cu126`, `cuda_disp=True`,
`NVIDIA GeForce GTX 1650 SUPER`, capacidad de cómputo **(7,5)**.

**840 ventanas de C&P, extremo a extremo** (tokenizar + copiar a GPU + forward +
traer de vuelta), un tamaño de lote por proceso limpio, mejor de 4 pasadas:

| Precisión | Lote | Mejor (s) | **Ventanas/s** | VRAM pico | Desviación vs CPU (0–2) |
|---|---|---|---|---|---|
| fp32 | 16 | 8,47 | 99,2 | 457 MiB | MAE 0,000001 · máx 0,001 · 839/840 idénticas |
| fp32 | 32 | 9,48 | 88,6 | 590 MiB | igual |
| fp32 | 64 | 11,45 | 73,4 | 856 MiB | igual |
| **fp32** | **128** | **7,45** | **112,7** | 1.388 MiB | **MAE 0,000001 · máx 0,001 · 839/840 idénticas** |
| fp16 | 16 | 36,70 | 22,9 | 237 MiB | MAE 0,00035 · máx 0,002 · 551/840 idénticas |
| fp16 | 128 | 35,48 | 23,7 | 706 MiB | MAE 0,00035 · máx 0,002 |

Tres cosas que hay que decir con todas las letras:

1. **fp16 es 4,8× MÁS LENTO que fp32 en esta tarjeta.** No es un error de medida:
   cuatro pasadas por configuración, todas dentro del 3 %. La GTX 1650 SUPER es
   un TU116 y **no tiene tensor cores**; el GEMM en half cae en un camino lento
   de cuBLAS. **En esta GPU, fp16 no se usa.**
2. **fp32 en GPU reproduce los números de CPU.** De 840 ventanas, 839 salen
   idénticas a 3 decimales y una difiere en 0,001 (redondeo del tercer decimal).
   MAE 0,000001 sobre la escala 0–2. A efectos de la interfaz, **no cambia nada**.
3. **El rendimiento no es monótono con el lote**: 128 (112,7 v/s) > 16 (99,2) >
   32 (88,6) > 64 (73,4). Es reproducible dentro de cada proceso. Además, en un
   mismo proceso que ya ha probado varios tamaños, **≥136 se desploma a 13–15
   v/s** (fragmentación del asignador con 4 GB de VRAM). Conclusión práctica:
   **fijar lote = 128 y no ir más arriba**, y no cambiar de tamaño en caliente.

**Libro entero en GPU (medido):** War and Peace, 2.459 ventanas, lote 128,
extremo a extremo, en un proceso que ya venía degradado por el barrido previo:
**55,2 s (44,5 v/s)**. En proceso limpio a 112 v/s serían ~22 s.

## 4. Recomendación

_(pendiente)_

## 5. Extrapolación

_(pendiente)_
