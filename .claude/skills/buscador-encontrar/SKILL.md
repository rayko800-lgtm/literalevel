---
name: buscador-encontrar
description: Lo aprendido al arreglar la búsqueda de Encontrar en LiteraLevel (catálogo de 68.546 textos, embeddings MiniLM multilingüe, rescate por nombre, bloques por nivel en el front) — la batería de consultas que hay que repetir antes de cada reinicio y los arreglos que rompieron otra cosa. Úsala antes de tocar app/catalogo.py (buscar, rescate por nombre, márgenes), bloques-busqueda.ts del front, o cuando un usuario diga «no encontré libros de X en mi nivel».
---

# El buscador de Encontrar

Del 14 al 15 de septiembre de 2026 hubo cuatro reinicios del Space dedicados a
la búsqueda (16, 18, 19 y 21), y en tres ocasiones **un arreglo correcto rompió
otro caso** que nadie estaba mirando. Esta skill existe para que el siguiente
arreglo se pruebe contra todos los casos a la vez.

> **La regla:** ningún cambio en el orden de resultados sube sin pasar la
> batería completa de la sección 2, en local y otra vez en el Space. Un
> arreglo que solo se prueba con la consulta que lo motivó está sin probar.

---

## 1. Qué pasó, en orden

| Síntoma | Causa | Arreglo | Lo que rompió después |
|---|---|---|---|
| Esmeralda (B1) busca «amor» y sale «MY FUTURE» | los 15.357 textos libres solo se buscaban por título y autor; el nivel pesaba más que el tema | reinicios 16 y 18: gancho y temas en el índice; el tema antes que el nivel | — |
| «amor» saca a «Fenn, Amor»; «sobre» ≈ «Sombre», «luna» ≈ «Luna: The Lost Dog» | rescate por nombre con parecido de letras | reinicio 19: el nombre solo rescata con coincidencia completa y dentro de `MARGEN_SEMANTICO_NOMBRE` | **«cervantes», «dante», «moliere» dejan de encontrar al autor** (su parecido semántico queda en 0,44–0,52, por debajo del margen) |
| «Jane Austen»: sus novelas detrás de libros sobre ella; se cuelan Sidney Austen y Calamity Jane | solo contaba el apellido | reinicio 21: nombre de pila + apellido = coincidencia completa | la primera versión aceptaba el nombre de pila solo y **«amor» volvió a sacar a «Fenn, Amor»**; lo cazó la prueba antes de subir |
| B1: cinco cuentos de la luna A2–B1 escondidos en «Menos parecidos» | margen fijo de 0,05 bajo el mejor parecido en el front | front 73a34dd: margen 0,10 solo para la franja del lector | sin guardas subían «ACTION PART-1» en «Terror gótico» y «Calamity Jane» en «Jane Austen»; se añadieron parecido mínimo 0,65 y hueco máximo 0,05 |
| «detectives en Londres» B1 ya no trae detectives de StoryWeaver | antes subían por parecido de letras con «detectives» (0,75–0,79); ahora quedan por tema (0,41–0,49) | **ninguno: es correcto** | — |

## 2. La batería (siempre entera)

Con perfil B1 (0,80) y sin perfil. En local sobre el árbol limpio y después en
el Space con `/api/buscar`. Anota el Space y el front en que mediste.

**Temas en español (no deben rescatar nombres):** amor · luna · sobre ·
historias de la luna · cuentos de miedo · Terror gótico · libros sobre
detectives · rosa · paz · lluvia y agricultores · viaje al espacio y la luna.

**Autores (deben salir sus obras primero):** cervantes · dante · moliere ·
dickens · tolstoy · dostoyevski · chejov · Jane Austen · agatha christie ·
emily bronte · browning · robert browning («browning» también es sustantivo).

**Apellido con tema o título, sin perfil (el autor en los 10 primeros al menos
tantas veces como midió 4e con la regla apagada):** treasure island stevenson (8)
· love poems by browning (7) · the secret garden frances hodgson burnett (7) ·
white fang jack london (2) · the call of the wild by jack london (10). **El
reinicio 21 los rompió en producción:** la regla «un apellido suelto no puntúa si
la consulta trae otro nombre» miraba las 24.296 palabras del campo de autor
(island, love, white…) y apagaba al autor buscado. El 22 solo mira nombres de
pila de otros autores con ese apellido, y un seudónimo sin nombre de pila solo
cuenta si tiene dos palabras o más y la consulta lo trae entero («I Love You» y
«Jack Jack» se colaban con cualquier «love» o «jack»).

**Cómo comparar en el Space:** el API recorta el autor con «y otros»; compara por
id contra el campo entero de los CSV, o una obra con coautor sale como fallo.

**Lo que no debe aparecer nunca:** «Fenn, Amor» con «amor»; Jane G. Austin,
Sidney Austen o Calamity Jane arriba en «Jane Austen»; ningún id de
`no_lectura_externo.csv`; ningún gancho con URL o anuncio (prueba a propósito
«digital marketing agency», «blender», «painting contractors», «buying GHB
online», «crystal meth»). StoryWeaver acepta textos de cualquiera: el 15 sep
seguían visibles un anuncio de venta de GHB (con letra B1) y otro de
metanfetamina, de la misma cuenta. **Un barrido por palabras no basta: cuando
aparece un anuncio, se revisan todos los textos de esa cuenta.**

**Los chips de sugerencia:** cada uno, con perfil A2 y con B1, tiene que dar
algo en «En tu nivel» o «Un poco por encima». Una sugerencia que ofrecemos
nosotros no puede acabar en una pantalla vacía: «Detectives en Londres» daba 0
con B1 (ronda 3, 15 sep), porque en el catálogo solo hay 2 libros así.

**En el front, a 390 px táctil:** «Primero lo de tu nivel» se cumple (luna B1
trae cuentos A2–B1 arriba); ninguna tarjeta de «Menos parecidos» lleva
etiqueta de encaje; la página no se desborda.

## 3. Antes de decir «hueco del catálogo», cuenta y compara

**Error de la noche del 14 al 15 sep:** se dio por hecho que con B1 «no hay casi
nada de amor en el catálogo» y se aconsejó ampliar el corpus. Era falso. e6
contó (auditoria/huecos_catalogo_2026-09-15.md) y la central lo verificó sobre
`catalogo_externo.csv`: cuentos libres con el tema en el título y dificultad
entre 0,20 y 1,00 hay **74 de amor, 47 de fantasmas, 29 de monstruos y 338 de
amigos**. La búsqueda no los devolvía: con nivel 0,40 y n=24, «Historias de
amor», «ghost stories» y «Monstruos» traían 24 de 24 libros de Gutenberg. Los
chips que «no llegaban» con A2 y B1 medían la búsqueda, no el catálogo.

Así que, ante «no encontré X en mi nivel»:

1. Cuenta en el `Catalogo` que carga la app cuántos textos de ese tema hay en
   la franja (título, temas y gancho; sin los de `no_lectura`).
2. Compáralo con lo que devuelve `/api/buscar` con ese perfil.
3. Si hay muchos y no salen, **es recuperación**: el top global lo copan los
   libros largos de Gutenberg y el reparto por bloques llega tarde.
4. Solo si no hay, es composición. Escasean de verdad en las fuentes libres:
   piratas, brujas y robots (y detectives con Londres en B1: 2).

Mapa de chips (e6, 15 sep, contra el reinicio 21): con ≥3 en «A tu medida» +
«Un poco por encima» con A2 y B1 salieron detectives, el océano, amistad,
cuentos cortos, viajes al espacio (justo), dinosaurios, miedo para niños,
animales de la selva, hadas, dragones, la luna, magia, música y baile,
aventuras en la selva, un viaje en tren y superhéroes. Los que no llegaban
(amor, familia, fantasmas, monstruos…) hay que volver a medirlos después de
arreglar la recuperación.

## 3b. Por qué no salían los cuentos del nivel (medido por f4, 15 sep)

Dos causas, las dos de recuperación:

- **La ventana de relevancia se mide contra el techo global.** Lo pone casi
  siempre un libro de Gutenberg con el tema en el título («True Ghost
  Stories» 0,855). El mejor cuento del tema quedaba de 0,07 a 0,24 por debajo,
  entre el puesto 12 y el 75, y con n=24 no llegaba.
- **El índice diluye a los libres.** Su vector es título + gancho + temas; el
  de Gutenberg no tiene gancho. Puntuados solo por el título, los mismos
  cuentos suben de 0,07 a 0,21.

Diseño del reinicio 23 (contrato con el front):

- Los n generales **no cambian**. Detrás van hasta K textos de la franja del
  lector, recuperados en un segundo top-k solo entre textos de su nivel, con
  el parecido máximo entre índice y título solo, y tres condiciones: suelo
  absoluto, cerca del mejor de la franja y no demasiado lejos del techo.
- Cada resultado lleva `por_franja` (siempre presente) y la respuesta trae
  `franja: [lo, hi]` redondeada a tres decimales. La franja se define **en un
  solo sitio** (catalogo.py) y el front la lee de la respuesta; sin ese campo
  se comporta como antes.
- Lo marcado entra en su bloque sin márgenes del front; lo no marcado sigue
  sus reglas. Ningún valor del salto del front arreglaba esto sin meter basura
  (e6 lo midió con 70 búsquedas): hacía falta la marca.
- ~~El rescate por título exige palabras enteras~~: se retiró del 25 antes de
  subir (ver abajo).

### El vector del título y las palabras sueltas

Al añadir «el parecido del título solo» para rescatar cuentos libres, entraron
marcados títulos de una palabra sin relación («HOLI», «Kuppu», «Biryani»,
«DINO») con 0,79–0,86 contra «amor» o «Monstruos». El MiniLM multilingüe
acerca dos palabras sueltas cualesquiera; contra una frase ya no. Por eso, en
consultas de una palabra, **el título se compara solo con las frases
«historias de X» y «libros sobre X»**, nunca con la palabra suelta (variante E,
elegida por calibración con dragones, océano y dinosaurios: 231 del tema de 236
marcados).

Límites que quedan y que no se arreglan con pesos: «Monstruos» no se acerca a
«monster» en este modelo (1 de 12 con cualquier variante), y «Historias de
amor» trae títulos genéricos tipo «My story».

### Palabras enteras frente a erratas

Para que «familia» no trajera «Familiar Things», el rescate por título pasó a
exigir palabras enteras. La auditoría previa (4e, 15 sep) midió el precio:
«sherlok holmes» pasaba de 8 Sherlock Holmes a 0, «treasure iland» perdía
Treasure Island y «dracul» perdía Dracula. «sherlok» ≈ «sherlock» y «familia»
≈ «familiar» dan el mismo 0,93: **una regla de letras no distingue una errata de
una palabra de otro idioma.** Se retiró antes de subir.

La regla que se mide para el reinicio 26: el parecido de letras no vale si la
palabra de la consulta es española y la app ya la traduce con el diccionario
local (familia, rosa, luna); sí vale si no lo es (sherlok, iland, dracul).

Añadir a la batería: sherlok holmes · treasure iland · dracul · pride and
prejudise · moby dik · frankenstien · wuthering heigths · familia.

## 4. Márgenes y constantes

Cada constante nueva (`MARGEN_SEMANTICO_NOMBRE`, `MARGEN_RARO`, el 0,10 y las
guardas del front) se **fija antes de ver los resultados** y se escribe en el
commit con la medida que la justifica. Un margen afinado mirando la consulta
que molestaba vuelve a romper la siguiente.
