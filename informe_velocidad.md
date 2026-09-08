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

_(midiendo…)_

## 4. Recomendación

_(pendiente)_

## 5. Extrapolación

_(pendiente)_
