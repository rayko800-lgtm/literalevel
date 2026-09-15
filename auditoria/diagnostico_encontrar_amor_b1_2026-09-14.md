# Diagnóstico: una lectora B1 busca «amor» (caso Esmeralda)

Reproducido el 14 de septiembre de 2026 por la noche en el Space (front
`45d9999`, motor del reinicio 14), con un lector nuevo situado por el
cuestionario en **0,95 · B1** (franja de «A mi nivel»: 0,70–1,20), a 390 px.
Sin cambios de código: esto es el diagnóstico y una propuesta, y la decisión es
de Miguel. Captura: `esmeralda_amor_B1_390.jpeg` (scratchpad de e6).

## Qué ve

Encontrar, buscando «amor» con «Ordenar por mi nivel (0,95 · B1)» marcado, que
es lo que sale por defecto con perfil:

- «12 libros para «amor», ordenados también por tu nivel.»
- Los tres primeros: **«edws»** (autor 윤예찬), **«MY FUTURE»** (휘영김) y
  **«dak side»**, cuentos de StoryWeaver con la etiqueta verde «A tu medida».
  Luego «SANGKURIANG», «Nakal Ki Akal», «time», «Love story» (A2), «DIWALI»,
  «Roster of Company I, 24th Regiment, Massachusetts», «bumbumyj,jc»,
  «HASTALIK» y «BILLOMANIA».
- **Solo uno de los doce trata de amor** («Love story», A2). Nueve caen en su
  franja, pero no del tema que pidió.
- Ningún aviso. Nada dice que haya pocos libros de amor en su nivel ni ofrece
  alternativa: ni ampliar la franja, ni ver los que están un poco por encima,
  ni quitar el ajuste. La única salida es desmarcar «Ordenar por mi nivel», y
  entonces salen libros de amor de verdad, pero en C1–C2 y sin explicación.
- «A mi nivel» (30 tarjetas en 0,70–1,20): ninguna de amor.

## Por qué

1. **Composición** (medido por Central, `feedback_usuarios_2026-09-14.md`): en
   la franja B1 hay 3 títulos con temas de amor entre unos 6.100; en B2, 60; la
   novela romántica de Gutenberg está en C1–C2 y los cuentos libres no tratan de
   amor. Con ese catálogo, ninguna pantalla puede darle «muchos».
2. **Ordenación** (lo que añade este diagnóstico): con el ajuste, el nivel pesa
   más que el tema. Los 3 de amor que sí hay en su franja **no salen ni entre
   los 30 primeros** de «amor» ni de «love». Incluso buscando el título exacto,
   «A Midsummer Night's Dream» solo aparece **sin** el ajuste.
3. **Relleno sin contenido**: los primeros puestos son cuentos libres con título
   de relleno («edws», «bumbumyj,jc») y sin gancho, con similitud 0,85 a «amor»,
   más que «Love story» (0,85 con peor afinidad de nivel). Un texto casi vacío
   se parece a cualquier consulta. Esto es de catálogo y de búsqueda (f4), no de
   pantalla.
4. **La pantalla no sabe decir «pocos»**: con 12 resultados «en franja» el
   buscador no distingue entre «hay mucho de lo que pides en tu nivel» y «hay
   cosas de tu nivel que no son lo que pides».

## Propuesta de pantalla (para que decida Miguel)

La mejora barata no crea libros: **enseña los que hay y dice la verdad en una
línea**.

1. **Dos bloques cuando el tema escasea en su franja.** Si entre los resultados
   relevantes (similitud por encima de un umbral o con el tema en `temas`) hay
   menos de, digamos, 4 en su franja:
   - arriba, «En tu nivel» con los que haya, aunque sean 1 o 3;
   - debajo, **«Un poco por encima de tu nivel»**: los más cercanos por encima
     (B2 primero, luego C1), cada tarjeta con su distancia en palabras («un
     escalón por encima», «dos escalones») y ordenados por cercanía;
   - y una línea: «De amor hay pocos libros en B1. Estos son los más cercanos
     por encima: se pueden leer tocando las palabras que no conozcas.»
2. **Nunca «A tu medida» en lo que no es de lo que pidió.** Hoy la etiqueta
   verde aparece en «edws» y «MY FUTURE». Que la etiqueta de nivel no sugiera
   que el resultado encaja con la búsqueda.
3. **Un botón, no un interruptor escondido**: «Ver también los de otros
   niveles», que hace lo mismo que desmarcar el ajuste pero dicho al lado de
   los resultados, y que vuelve con un toque.
4. Del lado del motor (f4, fuera de la pantalla): que los textos sin gancho ni
   huella no pasen de cierta similitud, y que en la búsqueda con ajuste el nivel
   **desempate** entre relevantes en vez de adelantar a lo irrelevante.

Coste estimado del 1–3 en el front: medio día, sobre la respuesta actual de
`/api/buscar` si la API da la similitud (ya la da) y la franja (la da
`/api/recomendar`; habría que añadirla a `/api/buscar`, o calcularla en el front
con `rango_recomendado` del perfil).
