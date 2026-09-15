# Límite declarado: el título en consultas largas de la búsqueda por franja

15 sep 2026, f4. Decisión de la Central: **sin cambio de código**. «Historias de amor» y
«Terror gótico» quedan como límite declarado de la búsqueda por franja. El chip
«Historias de amor» del front se queda, porque sigue cumpliendo el criterio del tema
(5 y 7 contados a mano).

## Qué se midió

En consultas de varias palabras, `_marcar_franja` usa el parecido máximo entre el índice
y el vector del título. «Historias de amor» marca «My stories» o «Amazing stories»
porque «historias» casa con «story».

- **Variantes, reimplementadas sin tocar la app**
  (`scratchpad/opciones_titulo_largas_r28.py`, catálogo del reinicio 27, igual al 28 en
  la franja):
  - **base**: lo desplegado; el título contra la consulta entera.
  - **G**: el título solo cuenta si la fila del índice ya pasa 0,40.
  - **J**: el título contra la consulta sin las palabras de marco (historias, cuentos,
    libros, sobre, de, stories, about…).
  - **K**: sin vector del título en consultas de varias palabras.
- **Métrica:** de los textos marcados «por franja», cuántos son del tema (expresión
  regular en título o gancho), con A2 (0,4) y B1 (0,8).
- **Calibración:** 14 consultas escritas antes de medir
  (`scratchpad/consultas_largas_calibracion_r28.txt`), ninguna de la batería. Decide la
  calibración; la batería va solo como informe.

## Calibración: del tema / marcados, A2 y B1

| consulta | base | G | J | K |
|---|---|---|---|---|
| cuentos de dragones y princesas | 14/19 16/18 | 14/19 16/18 | 16/19 17/17 | 12/19 15/20 |
| historias del mar y piratas | 11/12 15/15 | 11/12 14/15 | 8/12 13/15 | 5/7 12/15 |
| libros sobre dinosaurios gigantes | 11/11 12/12 | 11/11 12/12 | 10/10 11/11 | 12/12 11/11 |
| cuentos de animales del bosque | 13/14 14/15 | 14/14 15/15 | 12/13 4/4 | 12/14 13/15 |
| historias de perros perdidos | 16/18 6/8 | 16/17 6/8 | 10/11 8/8 | 14/15 19/20 |
| cuentos de hadas y duendes | 2/17 3/18 | 2/17 3/18 | 1/14 3/15 | 1/17 3/18 |
| aventuras en la selva | 9/9 9/9 | 9/9 9/9 | 17/18 16/17 | 21/24 22/26 |
| historias de viajes en tren | 13/13 12/12 | 13/13 12/12 | 11/11 8/8 | 9/9 10/10 |
| cuentos de la granja | 9/9 6/6 | 9/9 6/6 | 6/13 7/13 | 13/13 12/13 |
| libros sobre el cuerpo humano | 1/1 2/2 | 2/5 2/5 | 1/1 1/1 | 0/0 1/1 |
| stories about brave knights | 2/2 7/10 | 1/1 6/9 | 4/11 7/12 | 0/0 2/2 |
| books about space travel | 8/8 7/7 | 7/7 7/7 | 7/7 8/8 | 7/8 11/12 |
| tales of magic and wizards | 13/13 13/13 | 13/13 13/13 | 13/13 13/13 | 12/13 12/13 |
| stories about friendship at school | 14/14 18/18 | 14/14 18/18 | 15/15 16/16 | 11/11 13/13 |
| **TOTAL** | **276/323 (85,4 %)** | 275/326 (84,4 %) | 263/326 (80,7 %) | 285/351 (81,2 %) |

## Batería (solo informe)

| consulta | base | G | J | K |
|---|---|---|---|---|
| Historias de amor | 6/12 8/12 | 9/12 10/12 | 2/12 2/12 | 4/4 6/7 |
| Terror gótico | 5/11 5/6 | 2/2 4/4 | 6/12 7/10 | 0/0 0/0 |
| cuentos de miedo | 9/14 7/12 | 9/14 8/12 | 3/3 3/4 | 7/7 6/9 |
| libros sobre detectives | 6/8 8/9 | 5/6 6/7 | 4/6 6/6 | 0/0 0/1 |
| historias de la luna | 15/15 16/16 | 15/15 16/16 | 16/16 13/13 | 16/16 17/17 |
| viaje al espacio y la luna | 12/12 15/15 | 12/12 15/15 | 7/7 7/7 | 12/14 14/16 |
| cuentos sobre la lluvia y los agricultores | 16/16 23/23 | 15/15 23/23 | 24/24 23/23 | 7/7 8/8 |
| **TOTAL** | 151/181 (83 %) | 149/165 (90 %) | 123/155 (79 %) | 97/106 (92 %) |

Primeros marcados con A2:

- **«Historias de amor»**
  - base: The bond of love (0,78), My stories (0,75), THE TREE OF LOVE (0,74), Spread the
    Love (0,74), Amazing stories (0,73), Story (0,72).
  - G: quita My stories, Amazing stories y Story.
  - J: «amor» sola trae HOLI, Kuppu, Pehelwaan Ji, Suma.
  - K: Love begins at home, Love and Ego, THE HIDDEN TREASURE, Mutual Bond of Love.
- **«Terror gótico»**
  - base: The Ghost Terror, The terror of the night, The Enemy, The terror of the lion,
    THE REBEL, The horror incident.
  - G: se queda en 2 marcados.
  - K: ninguno.

## Por qué no se sube ninguna

- **G** es la única que arregla «Historias de amor», pero solo en la batería. En la
  calibración queda un punto por debajo de base, y vacía «Terror gótico». Subirla sería
  elegir con la batería.
- **K** marca más textos, pero con menos precisión.
- **J** rompe las consultas en las que casi todo es marco.
