# Ronda 3: el margen de Encontrar (15 sep 2026)

- **Auditor:** entrega-4e. La auditoría era de f4 y la Central me la pasó.
- **HEAD al empezar:** `036a207`.
- **Qué se audita:** `ec5bb75` de e6 (`front/src/app/compartido/bloques-busqueda.ts` y su spec).
- **Regla:**
  - margen de relevancia de 0,10 solo para la franja del lector;
  - parecido mínimo de 0,65;
  - sin cruzar un hueco mayor de 0,05 entre parecidos seguidos.
- **Dónde medí, todo en la misma sesión, antes de las 08:56 UTC:**
  - **Front** `MikeMaki1763/literalevel-front` en `73a34dd`, que es `ec5bb75:front` (árbol `f7834d3bf82e`) [V].
  - **API** `MikeMaki1763/literalevel` en `af72fb0`: catálogo y API de `053a486`, el reinicio 19. El reinicio 21 no subió mientras probaba: los dos Spaces seguían en esos commits al empezar y a las 08:55 UTC, al acabar [V].
- **Método:**
  - Chrome con contexto aislado, a 390 × 844, `mobile` y `touch`, en tema claro.
  - **Perfil B1 hecho en el front como una persona:** primera pregunta del cuestionario («Varias veces al mes») y «Me vale así (0,80 · B1), guardar».
  - **Búsquedas:** «historias de la luna» escrita en la caja y enviada con Intro. «amor», «detectives», «Terror gótico» y «Jane Austen» con la caja rellenada por script y el botón «Buscar» pulsado, que es el mismo camino del formulario.
  - En cada una pulsé «Ver también los de otros niveles» y leí bloque, título y etiqueta de encaje de cada tarjeta.
  - **Cotejo:** `/api/buscar` con el mismo `X-Lector`, `n = 24` (lo que pide `encontrar.ts:335`) y la función `bloquesBusqueda` de `ec5bb75` empaquetada con esbuild. La comparé con la regla de antes (solo el margen de 0,05).
  - **Bordes:** el mismo paquete en Node, con casos aislados.
  - La pestaña quedó cerrada.
  - **[V]** es ejecutado; **[L]**, solo leído.

---

## Lo pedido

| Pedido | Resultado | Evidencia |
|---|---|---|
| «historias de la luna» trae los cuentos A2–B1 a «En tu nivel» o «Un poco por encima» | **Sí** | [V] Detalle debajo de la tabla. |
| «amor», «detectives», «Terror gótico» y «Jane Austen» no cambian | **Sí** | [V] Detalle debajo de la tabla. |
| Las tarjetas irrelevantes, sin etiqueta de encaje | **Sí** | [V] Detalle debajo de la tabla. |
| Guarda del parecido mínimo en el borde | **Corta bien** | [V] Con los valores de la API, que llegan con tres decimales, **0,650 sube y 0,649 no**; con cuatro decimales, 0,6499 tampoco. |
| Guarda del hueco en el borde | **Corta bien** | [V] Detalle debajo de la tabla. |
| Sin desbordar a 390 px | **Sí** | [V] `scrollWidth` = 390 en las cinco búsquedas. |

**«historias de la luna»**, pantalla y API cotejada:
- **En tu nivel:** 4 tarjetas, las 4 «A tu medida»: *Aditi's Trip To Moon* (A2, 0,738), *Journey To The Moon* (B1, 0,731), *CHANDU AND THE MOON* (B1, 0,723) y *moon and hockey* (B1, 0,704).
- **Un poco por encima:** 1, «Un reto»: *THE MOON AND THE SUN* (B1, 0,715, medido en bloque).
- **De otros niveles:** 5 «Exigente».
- **Menos parecidos:** 14, sin etiqueta.
- Con la regla de antes, los cinco cuentos estaban en «Menos parecidos» (0 y 0 en los dos primeros bloques).
- El botón dice «Ver también los de otros niveles (19)» = 5 + 14. Mide 48 px, con `aria-expanded` de `false` a `true` y `aria-controls="otros-niveles"` apuntando a un elemento que existe.

**Las otras cuatro búsquedas**, pantalla y API cotejada:

| Búsqueda | En tu nivel | Un poco por encima | De otros niveles | Menos parecidos | Con la regla de antes |
|---|---|---|---|---|---|
| «amor» | 0 (sale el aviso) | 0 | 13 «Exigente» | 11 | igual |
| «detectives» | 9 «A tu medida» | 1 «Un reto» | 14 «Exigente» | 0 | igual |
| «Terror gótico» | 0 (aviso) | 0 | 5 «Exigente» | 19 | igual |
| «Jane Austen» | 0 (aviso) | 0 | 8 «Exigente» | 16 | igual |

**Tarjetas irrelevantes:**
- En «Menos parecidos», **ninguna de las 60 tarjetas** (14 + 11 + 19 + 16) lleva etiqueta de encaje.
- «Exigente» sale solo en «De otros niveles», y «A tu medida» y «Un reto», solo en sus bloques.
- En la ronda 2 eran 25 (2 de «Jane Austen» y 23 de «amor»). Ahora son 16 y 11: el catálogo del 19 cambió los resultados, no el front.

**Guarda del hueco:**
- Con una cadena sin huecos hasta 0,760, un libro de la franja a 0,760 − h:
  - **h = 0,049 y 0,050 cruzan**;
  - **h = 0,051 y 0,052 no**.
- Repetido desde 0,757, 0,755 y 0,753: la resta en coma flotante sale 0,050000000000000044 o 0,04999999999999993 y el corte no cambia.
- La holgura de 0,001 de `:51` es la que hace que 0,050 exacto cruce y 0,051 no.
- **Margen de franja:** con techo 0,800, un libro de la franja a 0,700 sube y a 0,699 no.

---

## Hallazgos

### [MENOR] Las pruebas nuevas no fijan dos de las tres guardas: cambiar el parecido mínimo o el margen de la franja no rompe nada

- **Dónde:** `front/src/app/compartido/bloques-busqueda.spec.ts` (los tres casos de `ec5bb75`) frente a `bloques-busqueda.ts:21-23` y `:56-59`.
- **Qué dice:**
  > `export const MARGEN_EN_FRANJA = 0.10;`
  >
  > `export const PARECIDO_MINIMO_EN_FRANJA = 0.65;`
  >
  > `&& l.similitud >= PARECIDO_MINIMO_EN_FRANJA && l.similitud >= suelo - HOLGURA;`
- **Por qué:**
  - Los tres casos nuevos, pasados por Node contra el paquete con cada guarda mutada [V]:

    | Mutante | ¿Lo caza alguna de las tres pruebas? |
    |---|---|
    | control, sin mutar | las tres pasan |
    | `>= PARECIDO_MINIMO_EN_FRANJA` a `>` | **no** |
    | parecido mínimo 0,65 a 0,60 | **no** |
    | margen de franja 0,10 a 0,12 | **no** |
    | holgura del hueco a 0,005, o sin holgura | **no** |
    | hueco 0,05 a 0,07 | sí («Jane Austen») |
    | sin la guarda del hueco | sí («Jane Austen») |

  - El caso de «Terror gótico» usa 0,586, lejos de 0,65: prueba que un parecido flojo no sube, pero no dónde está el corte.
  - En «historias de la luna», el cuento que queda fuera (*moon-fairy*, 0,694) está también fuera de la franja por dificultad (1,298 para 0,80), así que no fija el margen.
  - Las guardas funcionan hoy, como muestra la tabla de bordes; lo que falta es que una prueba lo diga.
- **Arreglo:** tres casos de borde en el spec:
  - un libro de la franja a 0,650 que sube y otro a 0,649 que no;
  - uno a techo − 0,100 que sube y a techo − 0,101 que no;
  - un hueco de 0,050 que se cruza y uno de 0,051 que no.

### [NOTA] En «Jane Austen» sus novelas siguen en «Menos parecidos» (lo cierra el 21)

- **Dónde:** el catálogo, no el front.
- **Por qué:** [V] *Emma*, *Persuasion*, *Pride and Prejudice* y *Lady Susan* salen sin etiqueta en «Menos parecidos». A 0,793 están a 0,064 del techo (0,857), que ponen los títulos con su nombre.
  - La guarda del hueco hace lo que debe: no deja que el nivel las suba por encima de ese salto. Y como son C2 para una lectora de 0,80, no son de su franja.
  - La causa es el rescate por nombre, que el reinicio 21 cambia según la Central. Por encargo no audito «Jane Austen» en el catálogo.

### [NOTA] La sugerencia «Detectives en Londres» no da nada en el nivel de una lectora B1

- **Dónde:** el chip de «Prueba con» en `encontrar` y el catálogo del 19.
- **Por qué:** [V, solo en la API] con 0,80 da 0 en su nivel, 0 un poco por encima, 1 «Exigente» (*Scotland Yard*, 0,753) y 23 «Menos parecidos». Hay un hueco de 0,078 tras el primero.
  - La Central ya dijo que el catálogo solo tiene 2 libros de Londres. No lo toca `ec5bb75`.
  - Pero es la sugerencia que se ofrece a quien no sabe qué buscar.
- **Qué haría:** cambiar ese chip por uno que dé algo en A2–B1, por ejemplo «detectives», que da 9 «A tu medida».

---

## Comprobado y correcto

- **La regla hace lo que dice el commit** [L y V]:
  - el margen ancho solo vale para `enFranja` (de −0,45 a +0,45 del nivel);
  - lo que era relevante con 0,05 sigue siéndolo;
  - un libro sin dificultad medida no sube por la franja.
- **El hueco se mide entre todos los resultados:** un libro C2 intermedio tapa un hueco y deja subir al de la franja. Es lo que dice el comentario de `:18-20` («entre parecidos seguidos»), no un fallo.
- **`ng test`:** 68 de 68 en 16 archivos, con los tres casos nuevos [V, ronda 3 de la boca 3D, mismo HEAD de front].
- **Consistencia:** el recuento del front y el de la API coinciden en las cinco búsquedas, tarjeta a tarjeta en los dos primeros bloques [V].
