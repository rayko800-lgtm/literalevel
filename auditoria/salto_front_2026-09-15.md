# Propuesta: el SALTO de los bloques de Encontrar y el caso «Robots»

- **Autor:** entrega-e6 (811c22), por encargo de la Central. Solo análisis; no hay commit de código.
- **Sobre qué:** la regla de `front/src/app/compartido/bloques-busqueda.ts` (88b3a83) y la API del Space `384a206` (reinicio 21).
- **Qué se midió:** 70 búsquedas con n = 24 y los niveles 0,1 / 0,4 / 0,8 / 1,2 / 1,6, 350 pares en total:
  - las 23 de la batería de la skill buscador-encontrar;
  - los 8 chips actuales y 6 de los viejos;
  - 33 candidatos medidos para los chips.
- **Cómo:** una réplica en Python de la regla del front. Antes de usarla se comprobó que da lo mismo que la spec en sus 7 casos (luna B1, «Terror gótico», «Jane Austen» y los cuatro bordes).

## El caso

Con A2, «Robots» deja 1 libro en la franja y 13 en «Menos parecidos». El resultado tiene dos alturas:
- **Arriba:** dos títulos a 0,858 y 0,855 («The Helpful Robots», «Sharanya Speaks to Robots»).
- **Abajo:** una meseta a 0,78 de cuentos de robots de su nivel («BRAVE ROBOT», «The Only Robot», «THE ROBOT ATTACK»…).

El hueco es de 0,075. SALTO (0,05) no lo cruza, así que la meseta se queda fuera aunque cabe en el margen de franja (0,10).

## Qué cambia con cada variante

«Cambian» cuenta los pares en los que cambian los libros de «En tu nivel» y «Un poco por encima».

| Variante | Cambian (de 350) | De ellos A2 o B1 | De 0 a algo | Libros que suben | ACTION PART-1 / Calamity Jane |
|---|---|---|---|---|---|
| Hoy (SALTO 0,05) | 0 | 0 | 0 | 0 | fuera / fuera |
| SALTO 0,08 | 9 | 2 | 1 | 78 | fuera / fuera en el Space, **vuelve en la spec** |
| SALTO 0,10 | 19 | 6 | 1 | 124 | fuera / fuera en el Space, **vuelve en la spec** |
| Sin SALTO | 19 | 6 | 1 | 124 | igual que 0,10 |
| 0,05, sin cortar si el de arriba es de otra franja | 8 | 2 | 1 | 51 | fuera / fuera en el Space, **vuelve en la spec** |
| 0,05, escalera medida solo con libros de la franja | 43 | 23 | 0 | 0 (**quita**) | fuera / fuera |

**Qué entra con cada una:**

- **SALTO 0,08:**
  - Bien: «Robots» en los cinco niveles (A2 pasa de 1 a 13 y B1 de 1 a 10), «Piratas» C1 (de 1 a 5, piratas de verdad) y «Detectives en Londres» C1 (+2, policía y misterio de Londres).
  - **Mal: «Familia» B2 y C1.** Sube una meseta de Gutenberg a 0,797–0,798 que se parece a «Familia» por las letras: «A Catechism of Familiar Things», «The Matron's Manual of Midwifery», «Rudiments of Conchology», «Marion Harland's Cookery». Con C1 son 23 libros en la franja, cuando hoy hay 0.
- **SALTO 0,10 o sin SALTO:** entra lo mismo que con 0,08, más dos cosas:
  - «Superhéroes» en los cinco niveles, bien: A2 de 6 a 18, B1 de 7 a 17.
  - **«rosa» de A1 a C1, mal:** «The little rabbit», «The sun in the beach», «The Boy Who Always Hears "Don't!"».
- **Sin cortar si el de arriba es de otra franja:** no arregla «Robots» con A2 ni con B1, porque los dos títulos de arriba sí son de su franja. Solo cambia B2 y C1, y mete la basura de «rosa» (A1–B1) y de «Familia» (C1).
- **Escalera solo de la franja:** deshace el arreglo de la luna. «historias de la luna» pasa de 5 a 0 con B1 y de 4 a 0 con A2, y además vacía «Animales de la selva», «Magia», «Fantasmas»… Descartada.

**Sobre las guardas:**
- «ACTION PART-1» está en los 24 de «Terror gótico» en todos los niveles, a 0,586, y **ninguna variante la sube**. La guarda que la para es el parecido mínimo de 0,65, no el SALTO.
- Calamity Jane **ya no aparece** en los 24 de «Jane Austen» en `384a206`, porque el reinicio 21 arregló el rescate por nombre. Así que en el Space la guarda no se pone a prueba. En los datos de la spec (Space `053a486`), en cambio, vuelve con 0,08, con 0,10, sin SALTO y con la variante «sin cortar si el de arriba es de otra franja»; la prueba de la spec se pondría en rojo.

## Por qué ningún valor de SALTO sirve

El hueco malo de «Familia» (0,856 → 0,798: **0,058**) es **menor** que el bueno de «Robots» (0,855 → 0,780: **0,075**). Pasa lo mismo con «rosa» (0,096, malo) frente a «Superhéroes» (0,082, bueno). Cualquier salto que deje pasar a los robots deja pasar antes a «Familiar Things».

Lo que separa unos de otros no es la distancia, sino **si la meseta es del tema**. Eso lo sabe la recuperación, no el front: «familia» ≈ «familiar» es el mismo parecido de letras que ya dio «Fenn, Amor».

## Propuesta

1. **No tocar SALTO ahora.**
   - Hoy la regla no deja a nadie peor que antes de 73a34dd.
   - «Robots» no es un chip publicado: con los chips actuales, ninguna variante cambia nada con A2 ni con B1.
   - Subirlo metería basura medida en «Familia» y «rosa», y rompería la prueba de Calamity Jane.
2. **Repetir esta medida sobre el reinicio 23**, cuando f4 cambie la recuperación para que traiga más de la franja del lector (hallazgo de 4db6ea3).
   - Si la meseta temática llega **más cerca del techo** o el techo deja de ser de otra franja, SALTO dejará de cortar solo, y puede sobrar.
   - Si «Familia» deja de traer «Familiar Things», el caso contra 0,08–0,10 desaparece.
   - La réplica y el guion de comparación están listos (scratchpad de e6: `salto_eval.py`, `salto_cache.json`); basta volver a llenar la caché contra el Space nuevo.
3. **Si tras el 23 hay que tocarlo**, que sea con la batería entera, la spec de Jane Austen actualizada a datos del 23 y los casos de este informe como pruebas nuevas:
   - «Familia» C1 no sube «Familiar Things»;
   - «rosa» B1 no sube «The little rabbit»;
   - «Robots» A2 sube la meseta de 0,78.

   Y no con un número elegido mirando «Robots» (skill buscador-encontrar, §4).
4. **Para f4, por si sirve en el 23:** en «Familia» el primer resultado es «Mi Familia» (0,856), y los 23 siguientes son Gutenberg con «Familiar» en el título a 0,797–0,798. Es parecido de letras del modelo de embeddings, y mientras no se arregle arriba, el front no puede distinguirlo.

## Actualización: el plan del reinicio 23 (mensaje de la Central, 15 sep)

El 23 cambia la recuperación:
- un segundo top-k dentro de la franja del lector, con umbral relativo al mejor de la franja;
- a los cuentos libres, el máximo entre su fila del índice y su título;
- una marca en cada resultado que entre por la franja.

Con eso, lo marcado irá a su bloque de nivel sin pasar por el margen ni por SALTO, y lo no marcado seguirá como hoy.

Lo medido arriba sigue sirviendo como línea base del 23, con tres riesgos que hay que mirar en cuanto la marca exista:

1. **«Terror gótico»:** «ACTION PART-1» (0,586) puede ser **el mejor de la franja** para B1. Con un umbral solo relativo a ese mejor, entraría marcado y se saltaría el parecido mínimo de 0,65, que hoy es lo único que la para.
2. **«Familia» C1:** la meseta «Familiar Things» / «Midwifery» es de la franja de C1. Si el segundo top-k la trae marcada, sube igual que con SALTO 0,08, y el front ya no podría pararla.
3. **Sin la marca** (Space anterior al 23), el front tiene que dar exactamente lo de hoy. Para distinguir «el API no marca» de «nada vino por la franja», conviene que la marca vaya **en todos los resultados** (verdadero o falso), no solo en los marcados.

Estos tres puntos van a f4 al acordar la forma de la marca.
