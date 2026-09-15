# Ronda 3: auditoría de la pasada de documentos de 4e

- **Auditor:** entrega-e6 (811c22).
- **Qué se audita:** `git show 13ad84a` en `entrega/`, `AGENTS.md`, `README.md` y `PENDIENTES.md`. Es la respuesta a mi ronda 2 (`auditoria/ronda2_2026-09-15_documentos.md`, `70efb73`) con las cifras del reinicio 19.
- **Informe anterior:** solo lo usé para la tabla de cierre; lo nuevo, a ciegas en el diff.
- **Fuera de alcance** (lo pide la Central): el reparto por nivel de los textos libres, que cambia en el reinicio 21.
- **Método:** **[V]** es ejecutado; **[L]**, solo leído.

## Qué se ejecutó

**Catálogo** (`catalogo_externo.csv` en `a557288`):
- 15.367 filas;
- por fuente y licencia: StoryWeaver 14.506 (CC BY 4.0), Let's Read 318 (CC-BY-4.0) + 10 (CC-BY-3.0), African Storybook 280 (CC-BY) y VOA 253 (dominio público);
- con la regla de `ui._cefr`: 749 + 5.589 + 5.543 = **11.881 entre A1 y B1**.

**Space** (`053a486`):
- `/api/estado` da «68.546 libros»;
- `/api/buscar` con «dostoyevski», con nivel 1,20 y sin nivel.

**Pruebas:**
- `pruebas_api.py` sin claves: **55 de 55** (ejecutada hoy para la ronda 3 de la API);
- recuento en su commit: `pruebas_voz_ritmo.py` en `2c0e681` tiene **37** `test_`, y `pruebas_corpus.py` en `40cdcd4`, **39** `prueba(`;
- `pruebas_extremas.py:1138-1142`, leído.

**PDF:**
- texto extraído de `documento.pdf`, `guion_video.pdf` y `presentacion.pdf`;
- `grep` de «casilla», 15.357, 68.536, 11.872 y «0 USD» en `.md`, `.tex`, README y AGENTS.

**Fuentes del coste:**
- `colab_precalculo.py:903`;
- `auditoria/medicion_catalogo_2026-09-10.md`;
- `PENDIENTES.md`;
- el mensaje de `5a6c2c7`.

## Hallazgos nuevos

### [MENOR] «Ese día quedaban 1,9 unidades»: la fuente las fecha el 9 de septiembre, no el 10 [V]

- **Dónde:** `entrega/documento.md:1329-1330` y `entrega/documento.tex:2943-2944` (Cuadro 17, párrafo siguiente).
- **Qué dice:**
  > «Hasta el 10 de septiembre de 2026 el cuaderno de Colab se abría con una A100 […] y hasta esa tarde se midieron 27.776 libros; ese día quedaban 1,9 unidades.»
- **Por qué:**
  - La única fuente de la cifra en el repositorio es `colab_precalculo.py:903` (y su `.ipynb`): «Con 1,9 unidades (**9 de septiembre de 2026**) salen 0,35 h = 21 min».
  - Es un día antes del que dice el texto.
  - No cambia la conclusión, pero es una cifra con fecha que no cuadra con su fuente.
- **Arreglo:** «el 9 de septiembre quedaban 1,9 unidades».

### [NOTA] Los 27.776 libros no tienen una fuente directa; salen de una resta que el texto no da [V]

- **Dónde:** los mismos párrafos y `entrega/estrategia.md:479`.
- **Por qué:**
  - No hay ningún archivo que diga 27.776, salvo el resumen `auditoria/ronda1_consolidado_2026-09-14.md:156`.
  - Cuadra con dos cifras que sí tienen fuente:
    - `PENDIENTES.md` da 29.875 medidos el 10 de septiembre;
    - `auditoria/medicion_catalogo_2026-09-10.md:14-15` da 2.099 en la tanda de T4 de ese día.
  - 29.875 − 2.099 = **27.776**.
  - Está bien, pero quien la busque no la encuentra.
- **Arreglo:** una nota «29.875 medidos el 10 de septiembre menos los 2.099 de la primera tanda en T4».

## Tabla de cierre

| Hallazgo de la ronda 2 | Estado | Cómo lo sé |
|---|---|---|
| **SERIO.** «0 USD de cómputo» frente a la A100 de pago del registro | **cerrado** | [V] El Cuadro 17 dice «A100 de pago hasta el 10 sep y T4 gratuita después; sin coste en USD registrado», igual en `.md`, `.tex` y PDF («0 USD de cómputo»: 0 veces). El párrafo lo explica, y la estrategia también. El registro se corrigió en `PENDIENTES.md`: las 2,8 h son estimación. Comprobado: 61.642 × 332,3 ventanas ÷ 2.022/s = **2,81 h**. Queda la fecha de las 1,9 unidades (MENOR nuevo). |
| **MENOR.** «Validación ciega» en el Cuadro 10 | **cerrado** | [V] `documento.tex:1921` dice «Validación interna»; en el PDF, «Validación ciega» 0 veces y «Validación interna» 1 (más 4 en minúscula). |
| **MENOR.** 17 h atribuidas a los 53.179 | **cerrado** | [V] «los 53.179 habrían sido unas 14,5 horas de reloj (§8.3 da 17 para los 61.642)». 53.179 ÷ 61 = 871,8 min = **14,5 h**. |
| **MENOR.** Cuadro 2 sin fecha y con recuentos viejos | **cerrado** | [V] Pie «Los recuentos de textos libres son de `a557288`, el catálogo publicado en el reinicio 19», y los cuatro recuentos y el desglose de Let's Read cuadran con el CSV de `a557288`. |
| **MENOR.** La casilla de Encontrar y el aviso en el guion | **cerrado** | [V] Sin «casilla puesta» ni «casilla de acercar» en `.md`, `.tex` y PDF. El guion del vídeo, la demo y §8.2 describen el aviso y el bloque «De otros niveles». Contra el Space: con 1,20, *Crime and Punishment* sale **2.º** y ningún resultado de «dostoyevski» sube a las franjas con la regla del front `ec5bb75`; sin perfil **no está entre los 12 primeros**. |
| **MENOR.** Cabecera de la tabla de pruebas del README | **cerrado** | [V] README y AGENTS: «las filas con fecha llevan el commit sobre el que se corrieron», y cada fila cambiada lleva su commit. |
| **DUDA (ronda 1).** Empates de `_cefr` sin prueba | **cerrado** | [V] `pruebas_extremas.py:1138-1142` fija los cinco límites: `ui._cefr(lim - 0.001)` y `ui._cefr(lim)` para 0,20, 0,60, 1,00, 1,40 y 1,80. |

## Comprobado y correcto (cifras nuevas de 13ad84a)

**Catálogo**
- **15.367 textos libres y 68.546 en total:** CSV de `a557288` y `/api/estado` del Space. Salen en documento, estrategia, guiones, presentación, README, AGENTS y PENDIENTES, y en los tres PDF ya no queda 15.357 ni 68.536 (salvo donde se fecha en `377a650`). [V]
- **11.881 entre A1 y B1:** recontado. [V]
- **Recuentos de suites:**
  - API 55 [V ejecutada];
  - lectura natural 37 en `2c0e681` y corpus 39 en `40cdcd4` [V recuento en el commit];
  - extremas 349 e integración 27 [L].

**El coste, contado con sus fuentes**
- **Cuándo cambió el cuaderno de A100 a T4:** `5a6c2c7` (10 sep), «el cuaderno se abre ya en T4, y no en A100». [V]
- **La primera tanda en T4 fue de 2.099 libros**, según `medicion_catalogo_2026-09-10.md`. [V]
- **Dónde se guardaban los resultados:** en Drive hasta el 12 de septiembre y en Hugging Face después, como dice `PENDIENTES.md`. [L]

**Guiones y presentación**
- **La demo en vivo** avisa del aviso de otros niveles al buscar «dostoyevski» con 1,20, y lo da por esperado. [L y V en el Space]
- **Las cifras de la presentación** (15.367 y 53.179) cuadran con el documento, y el PDF está recompilado. [V]
