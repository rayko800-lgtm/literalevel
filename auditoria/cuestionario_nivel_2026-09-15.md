# ¿El cuestionario de «Tu nivel» infravalora?

**Para la Central, e6 y Miguel.** Medido por entrega-4e el 15 sep 2026, solo lectura, sobre `app/perfil.py` en `304f927` (lo que llama `/api/perfil/cuestionario`) y el orden del front en `front/src/app/pantallas/nivel.ts` (`e7a2f1c`, sin cambios en disco).

**Respuesta corta: no infravalora de forma sistemática.**
- Con los cuatro perfiles fijados antes de calcular, ninguno sale con una letra por debajo de la suya, con 6 preguntas ni con 9.
- El sesgo va hacia arriba: el error medio es de +0,19. Un B2 honesto sale **C1 (1,51)** y un C1 sale **C2 (1,82)**.
- El A2 de e6 cabe, pero solo en el extremo bajo de un B1: 1 de las 64 combinaciones plausibles con 6 preguntas.
- **Lo que tira hacia abajo no es el fragmento difícil.** Con el máximo, «Me pierdo» en Frankenstein no resta nada. Tira hacia abajo que el fragmento fácil tiene techo 0,8 y pesa el 65 %.

## 1. La fórmula, en palabras

`perfil.desde_cuestionario` (`app/perfil.py:270-294`) separa las respuestas en dos bloques:

1. **Opinión** (frecuencia, libro entero, comprensión y, con Afinar, diccionario, series y lecturas): la **media** de los valores elegidos. En «lecturas», que admite varias opciones, cuenta la más alta.
2. **Fragmentos** (Alice, Sherlock Holmes y Frankenstein): el **máximo** de los tres. El comentario del código lo explica: interesa el pasaje más difícil que el lector dice entender.

- Con los dos bloques, el nivel es **0,35 × media de opinión + 0,65 × máximo de fragmentos** (`PESO_FRAGMENTOS = 0.65`), recortado a 0..2 y redondeado a 3 decimales.
- Con un solo bloque, cuenta ese bloque.
- La letra que ve el lector es el ancla MCER más cercana: índice `floor(nivel × 2,5 + 0,5)` sobre A1..C2, en `front/src/app/nucleo/formato.ts:6` y en `scoring.public_band`. Así, A2 va de 0,2 a 0,6, B1 de 0,6 a 1,0, B2 de 1,0 a 1,4 y C1 de 1,4 a 1,8.

Valores de cada opción (`app/perfil.py:134-251`):

| Pregunta | Opciones, de menos a más |
|---|---|
| frecuencia | 0 · 0,4 · 0,8 · 1,2 · 1,6 |
| libro_completo | 0 · 0,4 · 0,8 · 1,4 · 2,0 |
| comprension | 0 · 0,6 · 1,0 · 1,4 · 2,0 |
| fragmento_facil (Alice, A2/B1) | me pierdo 0 · diccionario 0,2 · idea 0,4 · releo 0,6 · natural **0,8** |
| fragmento_medio (Holmes, B2) | 0 · 0,4 · 0,8 · 1,0 · **1,2** |
| fragmento_dificil (Frankenstein, C1/C2) | 0 · 1,0 · 1,6 · 1,8 · **2,0** |
| diccionario *(Afinar)* | 0 · 0,4 · 0,8 · 1,4 · 2,0 |
| series *(Afinar)* | 0 · 0,4 · 0,8 · 1,4 · 2,0 |
| lecturas *(Afinar, varias)* | 0 · 0,4 · 1,0 · 1,4 · 2,0 |

**Orden en el front:**
- `PASOS`: frecuencia, fragmento fácil, libro entero, fragmento medio, comprensión y fragmento difícil.
- `EXTRA` (Afinar): diccionario, series y lecturas.
- Gradio pinta las nueve en el orden de `ui._claves_cuestionario` (leído en el código, no lo he abierto en pantalla).

## 2. Los perfiles, fijados antes de calcular

**Archivo:** `D:\literalevel_tmp\cuestionario_perfiles_fijados.json`, guardado a las 05:11:11; el cálculo empezó a las 05:11:39.

**Criterio, escrito también antes:** infravalora si, con las respuestas principales, al menos 2 de los 4 perfiles bajan de letra, o si el error medio con signo es menor que −0,2.

**Respuesta principal y alternativa:** cada pregunta tiene una respuesta principal. Si otra es igual de plausible para ese lector, lleva también una alternativa, y las alternativas dan el intervalo, no el veredicto.

**Descriptores:** van **parafraseados** de la escala global y de la de comprensión de lectura general del MCER (2001 y volumen complementario de 2020, `referencias.bib`). No hay copia del texto en el repositorio, así que no son citas literales.

| Perfil | Descriptor (paráfrasis) |
|---|---|
| A2 | Entiende textos breves y sencillos sobre asuntos cotidianos con vocabulario muy frecuente. |
| B1 | Lee textos sencillos y factuales sobre temas de su interés con comprensión satisfactoria. |
| B2 | Lee con bastante autonomía; vocabulario amplio, pero le cuestan las expresiones poco frecuentes. |
| C1 | Entiende con detalle textos largos y complejos si puede releer las partes difíciles; reconoce lo implícito. |

| Pregunta | A2 | B1 | B2 | C1 |
|---|---|---|---|---|
| frecuencia | 0,4 (o 0,8) | 0,8 (o 0,4) | 1,2 (o 1,6) | 1,6 (o 1,2) |
| fragmento_facil | idea 0,4 (o diccionario 0,2) | releo 0,6 (o natural 0,8) | natural 0,8 | natural 0,8 |
| libro_completo | adaptado 0,8 (o empecé 0,4) | adaptado 0,8 (o empecé 0,4) | novela actual 1,4 (o adaptado 0,8) | clásica 2,0 (o novela 1,4) |
| fragmento_medio | me pierdo 0 (o diccionario 0,4) | idea 0,8 (o diccionario 0,4) | releo 1,0 (o natural 1,2) | natural 1,2 |
| comprension | idea general 0,6 (o 0) | hechos 1,0 (o idea 0,6) | detalles 1,4 (o hechos 1,0) | implícito 2,0 (o detalles 1,4) |
| fragmento_dificil | me pierdo 0 | diccionario 1,0 (o me pierdo 0) | idea 1,6 (o diccionario 1,0) | releo 1,8 (o natural 2,0) |
| diccionario | 0,4 (o 0) | 0,8 (o 0,4) | 1,4 (o 0,8) | 2,0 (o 1,4) |
| series | subt. español 0,4 | subt. inglés 0,8 (o español 0,4) | sin subt., idea 1,4 (o inglés 0,8) | sin subt., detalles 2,0 (o idea 1,4) |
| lecturas | mensajes 0,4 | + noticias 1,0 (o solo mensajes 0,4) | + novelas 1,4 (o sin novelas 1,0) | + clásica 2,0 (o sin clásica 1,4) |

Cada respuesta está justificada en el JSON: por ejemplo, para B1 el fragmento B2 está un escalón por encima, así que capta la idea y se le escapan «baffled» o «successive instance».

## 3. Lo que da cada perfil

Salida completa en `D:\literalevel_tmp\cuestionario_calculo_salida.txt`, con el guion `cuestionario_calculo.py` al lado.

| Perfil | 6 preguntas | 9 (con Afinar) | Intervalo con 6 | Letras con 6 | Letras con 9 |
|---|---|---|---|---|---|
| A2 (0,4) | **0,470 A2** (+0,07) | 0,435 A2 | 0,223-0,517 | A2 32/32 | A2 64/64 |
| B1 (0,8) | **0,953 B1** (+0,15) | 0,953 B1 | 0,553-0,953 | B1 63, A2 1 | B1 495, A2 17 |
| B2 (1,2) | **1,507 C1** (+0,31) | 1,518 C1 | 1,000-1,553 | B2 18, C1 14 | B2 135, C1 120, B1 1 |
| C1 (1,6) | **1,823 C2** (+0,22) | 1,847 C2 | 1,637-1,953 | C1 8, C2 8 | C1 58, C2 70 |

- **Criterio:** 0 de 4 perfiles bajan de letra, con 6 y con 9. El error medio con signo es **+0,188** en los dos casos. No infravalora.
- **Las 3 preguntas de Afinar** mueven el nivel principal 0,04 como mucho y no cambian ninguna letra.

### El A2 de e6 (0,56 contestando como B1)

La única combinación de las 64 del B1 que cae en A2 con 6 preguntas da **0,553**, a 0,007 del 0,56 de e6. Es el B1 más bajo de los plausibles:
- lee menos de una vez al mes;
- empezó un libro y no lo terminó;
- solo cuenta la idea general;
- necesita diccionario con Holmes;
- se pierde en Frankenstein;
- relee alguna frase de Alice.

La cuenta es 0,35 × media(0,4; 0,4; 0,6) + 0,65 × máx(0,6; 0,4; 0) = 0,163 + 0,39 = 0,553. No conozco las respuestas exactas de e6, así que no afirmo que fueran estas.

**Por qué baja, medido:**
- **El difícil no resta.** Con las respuestas principales de B1:
  - «Me pierdo» en Frankenstein da **0,823**, lo mismo que no contestarlo (0,823);
  - «diccionario» da 0,953;
  - con el máximo, el difícil solo puede subir el nivel.
- **Lo que baja es el techo del fragmento fácil.**
  - Alice vale como mucho 0,8, y releer alguna frase ya da 0,6.
  - Si Holmes no se entiende, ese 0,6 pesa el 65 % del nivel.
  - Por eso, en el recorrido, **el provisional cae en la segunda respuesta en todos los perfiles**:
    - B2: de 1,20 a 0,94 (B1);
    - C1: de 1,60 a 1,08 (B2), entendiendo Alice con naturalidad;
    - B1: de 0,80 a 0,67.
  - Es la bajada que vio e6 y la que hace pensar «soy tonta». La propuesta A de Miguel quita el provisional, y con él desaparece.

## 4. Propuesta

1. **Fórmula: no la cambiaría para corregir una infravaloración, porque no la hay.**
   - El sesgo medido es hacia arriba en B2 y C1, y lo empuja el fragmento difícil. «Capto la idea» en Frankenstein vale 1,6, y para un B2 eso pesa el 65 %: con «diccionario» (1,0) el B2 daría 1,117 B2.
   - No propongo tocar ese valor con estos datos. Calibrarlo sobre estos cuatro perfiles sería ajustar la fórmula a mi propio juicio, que es el mismo conjunto con el que se mide.
   - Si Miguel quiere afinarla, la prueba honesta es con lectores reales que se hayan medido también con un texto o un libro que leyeron, comparando las dos cifras.
2. **No metería las 3 preguntas de Afinar dentro de las seis.**
   - Mueven el nivel 0,04 como mucho y no cambian ninguna letra de los perfiles.
   - En el B1 bajo sube la proporción de combinaciones que caen en A2: 17 de 512 (3,3 %) frente a 1 de 64 (1,6 %).
   - Añaden tres pantallas a quien se perdió con seis.
3. **Para la receta del B2 de la demo** (e6 busca una ahora que se va «Me vale así»): con las seis preguntas del front, en su orden, sale **1,200 exacto** (comprobado con `perfil.desde_cuestionario`):
   - frecuencia «Varias veces por semana» (1,2)
   - fragmento fácil «Lo entiendo con naturalidad» (0,8)
   - libro entero «Sí, una novela actual» (1,4)
   - fragmento medio «Lo entiendo con naturalidad» (1,2)
   - comprensión «Los hechos o argumentos principales» (1,0)
   - fragmento difícil «Me pierdo» (0) o «Entiendo algunas partes, pero necesitaría el diccionario» (1,0), que dan lo mismo.

   La cuenta es 0,35 × media(1,2; 1,4; 1,0) + 0,65 × 1,2 = 0,42 + 0,78 = 1,20. Si se pulsa Afinar, el nivel cambia.

   Coincide con la receta que e6 midió en local y contra el Space, que elige «diccionario» en el difícil. Como aquí no propongo cambiar la fórmula, no hace falta volver a medirla. Si algún día se toca `PESO_FRAGMENTOS` o el valor de alguna opción, sí.

## Límites

- **Los perfiles son de mi juicio**, justificados con descriptores parafraseados, no con lectores reales.
- **El «honesto» de cada nivel** tiene más de una respuesta posible; por eso van las alternativas y los intervalos.
- **No he reproducido las respuestas de e6.** Solo he comprobado que caben en el extremo bajo del B1.
