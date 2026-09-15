# Feedback de los primeros usuarios (desde el 14 sep 2026)

Cuentas repartidas por Miguel el 14 de septiembre por la tarde: invitado1 a
invitado8 con 20 usos cada una, profesor con 60. Front `45d9999`, motor
`7c09d90`. Este archivo recoge lo que dicen y lo que se mide a raíz de ello.

## Esmeralda (15 años, prepa), por partes

**Lo que dijo:** le gustó mucho. No encontró en su nivel muchos libros: salió
**B1** y buscó **amor**.

**Lo que se midió** (catalogo_medido.csv + catalogo_externo.csv, temas y gancho
con love/romance/courtship, letra por dificultad pública):

| Letra | Gutenberg | con amor | Libres | con amor |
|---|---|---|---|---|
| A1 | 1 | 0 | 749 | 0 |
| A2 | 40 | 0 | 5.580 | 0 |
| B1 | 558 | 2 | 5.543 | 0 |
| B2 | 3.127 | 33 | 2.578 | 0 |
| C1 | 23.454 | 884 | 794 | 0 |
| C2 | 25.999 | 1.107 | 113 | 0 |

En la franja de recomendación de B1 (0,55 a 1,05) salían **3** títulos con amor y
en la de B2 **60**, pero **esa primera medida era mía y estaba mal**: usaba el CSV
crudo, donde *A Midsummer Night's Dream* guarda 0,697, y buscaba las palabras
como subcadena. f4 lo midió sobre el catálogo que carga la app y dio **1 en B1** y **28 en B2**;
la auditoría de documentos (4e) no reprodujo el 28. **Cifra que queda**, con la
regla de la app escrita en el documento (libros literarios, sin excluidos, a
0,25 del nivel, love/romance/courtship en los temas): **1 en B1** (*The Princess
Nobody*) y **31 en B2** (29 títulos distintos). La tabla de arriba sirve solo
como forma del reparto.

**Lectura:** su experiencia coincide con los datos. La novela romántica de
Gutenberg (Austen, Brontë, Hardy) está casi toda en C1 y C2, y los cuentos
libres son infantiles y no tratan de amor. **Crecer el catálogo con más cuentos
no lo arregla**: el hueco es de composición, no de tamaño.

**Qué se hace:** e6 reproduce la búsqueda con un perfil B1 en el Space y
propone cómo debería responder la pantalla cuando un tema tiene pocos libros en
la franja (por ejemplo, ofrecer los más cercanos por encima, marcados «un poco
por encima de tu nivel»). La decisión es de Miguel.


## Lo que se hizo (14 sep, noche)

- e6 lo reprodujo en el Space: `auditoria/diagnostico_encontrar_amor_b1_2026-09-14.md`. Además del hueco, dos fallos: con «Ordenar por mi nivel» el nivel pesaba más que el tema, y textos sin contenido («edws», «bumbumyj,jc», un cuento en coreano titulado «Love story») se colaban arriba.
- f4 los arregló en el reinicio 16 (Space `484b83b`): el nivel ordena solo dentro de lo relevante, un título acertado va siempre delante, y 163 textos libres que no son lectura en inglés quedan fuera del buscador y de recomendar (`no_lectura_externo.csv`).
- Miguel aprobó la pantalla nueva de Encontrar: dos bloques «En tu nivel» y «Un poco por encima de tu nivel», sin «A tu medida» para lo que no es lo pedido, y un botón «Ver también los de otros niveles». La hace e6.
