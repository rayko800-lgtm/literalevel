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
emily bronte.

**Lo que no debe aparecer nunca:** «Fenn, Amor» con «amor»; Jane G. Austin,
Sidney Austen o Calamity Jane arriba en «Jane Austen»; ningún id de
`no_lectura_externo.csv`; ningún gancho con URL o anuncio (prueba a propósito
«digital marketing agency», «blender», «painting contractors»).

**Los chips de sugerencia:** cada uno, con perfil A2 y con B1, tiene que dar
algo en «En tu nivel» o «Un poco por encima». Una sugerencia que ofrecemos
nosotros no puede acabar en una pantalla vacía: «Detectives en Londres» daba 0
con B1 (ronda 3, 15 sep), porque en el catálogo solo hay 2 libros así.

**En el front, a 390 px táctil:** «Primero lo de tu nivel» se cumple (luna B1
trae cuentos A2–B1 arriba); ninguna tarjeta de «Menos parecidos» lleva
etiqueta de encaje; la página no se desborda.

## 3. Huecos que no son fallos

Con B1 no hay casi nada de amor ni de detectives en Londres **en el catálogo**
(amor: 1 en B1 y 31 en B2; detectives con Londres: 2 en B1 y 87 en C1–C2). La
búsqueda hace bien en decirlo con el aviso de otros niveles. Antes de tocar
código por «no encontré X en mi nivel», cuenta cuántos hay con la regla de la
app; si el hueco es de composición, se arregla añadiendo textos, no pesos.

## 4. Márgenes y constantes

Cada constante nueva (`MARGEN_SEMANTICO_NOMBRE`, `MARGEN_RARO`, el 0,10 y las
guardas del front) se **fija antes de ver los resultados** y se escribe en el
commit con la medida que la justifica. Un margen afinado mirando la consulta
que molestaba vuelve a romper la siguiente.
