# Visto bueno del reinicio 22 antes de subir (15 sep 2026)

- **Auditor:** entrega-4e.
- **Qué se revisa:**
  - `app/catalogo.py` de **8b259c5**, frente a `ef1138c`, que es lo publicado en el Space `384a206` (reinicio 21);
  - `no_lectura_externo.csv` de **9dcd867**.
- **Veredicto:** **ok**, con dos menores para el reinicio 24.
  - El 22 arregla el SERIO de la ronda 3 (vocabulario de nombres) sin romper la batería.
  - Sí empeora unas pocas consultas de autores con nombre de pila corto o con apellido que es palabra corriente. Son las de abajo, con sus números.
- **Método:**
  - **La batería de buscador-encontrar,** en local con el código de `8b259c5` ejecutado como si viviera en `app/` y los datos del árbol, frente a `/api/buscar` del Space `384a206`. Sin perfil y con B1 (0,80), n = 10.
  - **Comprobación del arnés:** con el código de `ef1138c`, las 45 consultas dan en local lo mismo que el Space.
  - **Parecido de nombre sin modelo** para los casos límite.
  - Todo en solo lectura.
  - **[V]** es ejecutado; **[L]**, solo leído.

---

## Lo que arregla

**Nombre y título, autor en los 10 primeros** [V]:

| Consulta | Sin perfil: 21 → 22 | B1: 21 → 22 |
|---|---|---|
| treasure island stevenson | 2 → **10** | 2 → **10** |
| love poems by browning | 0 → **7** | 0 → **5** |
| the secret garden frances hodgson burnett | 0 → **8** | 0 → **8** |
| white fang jack london | 0 → 2 | 0 → 1 |
| the call of the wild by jack london | 4 → **10** | 1 → 6 |
| little women alcott | 3 → 9 | 3 → 9 |
| anne of green gables montgomery | 1 → 1 | 1 → 8 |
| jane eyre | 0 → 1 | 0 → 1 |

**Sin modelo, el parecido de nombre del autor buscado pasa de 0 a 0,88-0,90** en «king lear shakespeare», «moby dick herman melville», «ulysses james joyce», «the jungle book kipling», «the murder of roger ackroyd agatha christie», «king solomon's mines haggard», «peter rabbit beatrix potter» y «the gift of the magi o henry» [V].

**Temas, autores y nombres de pila:** iguales que en el Space [V].
- Temas: amor, luna, sobre, historias de la luna, cuentos de miedo, Terror gótico, libros sobre detectives, rosa, paz y viaje al espacio y la luna.
- Autores: dickens, tolstoy, dostoyevski, chejov, Jane Austen (sin intrusos), agatha christie y emily bronte.
- Nombres de pila: grace, jane, rose y hope and glory.
- «lluvia y agricultores» mejora: abre con *Girl and a farmer*, *Farmers Hard work*, *The Water Seed* y *Rain*, donde el Space daba manuales de conservas.
- Los fallos que ya tenía el 21 (cervantes, dante, moliere, agatha christie) siguen igual; van al 24, como se acordó.

**«Fenn, Amor»** no sale con «amor» [V].

## Datos (9dcd867)

- `no_lectura` pasa de 200 a **203**, todas con motivo «anuncio (revisado a mano)» [V]:
  - SWV644124 (venta de GHB);
  - SWV644179 (venta de metanfetamina, de la misma cuenta);
  - SWV119683 (UCAS Appraisal, un artículo publicitario de tasación inmobiliaria).
- No se quita ninguna fila, y ninguna de las nuevas es un cuento.
- Los 6 textos visibles de Shlok Jagtap, cuentos infantiles de verdad, se quedan.
- **En la búsqueda:** «buying GHB online», «crystal meth» y «buy online» ya no traen ningún texto de `no_lectura`. En el Space traían SWV644124 y SWV644179 [V].
- **Entre los textos que siguen visibles,** el barrido de reclamos (comprar en línea, «where to buy», drogas, «order now», «visit our website» sin los créditos de Bilum Books y VOA, SEO, «assignment help») da 5 coincidencias, y las 5 son cuentos que hablan de comprar [V].

---

## Hallazgos

### [MENOR] Un nombre de pila de menos de cuatro letras o con iniciales convierte al autor en seudónimo, y se apaga en consultas de varias palabras

- **Dónde:** `app/catalogo.py` de `8b259c5`: `_es_seudonimo` y el `if seudonimos[i]:` de `buscar`.
- **Qué dice:**
  > `if len(partes) >= 2 and any(p.isalpha() for p in _fichas([partes[1]])[0] - _NO_SON_NOMBRES):`
  >
  > `if len(apellidos[i]) < 2 or not apellidos[i] <= pistas:`
  >
  > `    por_apellido[i] = 0.0`
- **Por qué:**
  - `_fichas` descarta las palabras de menos de cuatro letras. «Rohmer, Sax», «Rand, Ayn», «Beach, Rex», «Wallace, Lew», «Maupassant, Guy de», «Meade, L. T.» o «Bower, B. M.» se quedan sin nombre de pila y pasan por seudónimo. Con un apellido de una palabra, se apagan en cualquier consulta de dos pistas o más.
  - **Afecta a 591 autores del catálogo (1.128 libros)**, 60 de ellos entre los 3.000 con más descargas [V].
  - **Con el modelo** [V], autor en los 10 primeros, Space 21 → 22:

    | Consulta | Sin perfil | B1 |
    |---|---|---|
    | fu manchu sax rohmer | 10 → **3** | — |
    | the insidious dr fu manchu rohmer | 10 → **5** | — |
    | the spoilers rex beach | 10 → **2** | 4 → **2** |

  - En otras consultas del mismo tipo no pierde, porque el título o el tema bastan: «the necklace maupassant» 9 → 8 y 10 → 10, «maupassant short stories» 3 → 10, «zuleika dobson beerbohm» 0 → 1.
- **Arreglo:** en `_es_seudonimo`, contar como nombre de pila cualquier palabra alfabética tras la coma, también las cortas y las iniciales, en vez de pasar por `_fichas`. Y lo mismo al llenar `_pila_por_apellido`. Añadir «fu manchu sax rohmer» y «the spoilers rex beach» a la prueba.

### [MENOR] Un apellido que es palabra corriente vuelve a rescatar: «little dorrit dickens» con B1 trae a Burt Little segundo

- **Dónde:** el mismo bloque de `buscar`. La regla nueva solo apaga un apellido si la consulta trae el nombre de pila de otro autor con ese apellido.
- **Por qué:**
  - «little» es el apellido de «Little, Burt», y la consulta no trae ningún nombre de pila de los Little, así que no se apaga.
  - **Con el modelo, B1** [V]:
    - el Space del 21 abre con cuatro obras de Dickens, *Little Dorrit* 4.ª, 5 de Dickens en los 10 primeros;
    - el 22 local abre con *A Child's Dream of a Star*, luego *Francisco the Filipino* (Burt Little) y *Jacob Hamblin*, y *Little Dorrit* no está entre los 6 primeros; 4 de Dickens.
  - Sin perfil mejora (5 → 9 de Dickens).
  - Es la misma clase que el autor de apellido Love que f4 ya apuntó para el 24 con «love poems by browning».
- **Arreglo:** que un apellido de una sola palabra que además aparece como palabra del título o del tema de la consulta no rescate si otro apellido de la consulta ya rescata a un autor con parecido completo. O, más simple, dar prioridad al apellido que casa con el nombre entero más largo. Va al 24.

---

## Comprobado y correcto

- **La regla nueva hace lo que dice** [L y V sin modelo]:
  - «Jane Austen» apaga a Sidney Austen;
  - «island», «love», «white», «wild» o «call» ya no apagan a nadie, porque no son nombre de pila de ningún Stevenson, Browning o London;
  - un seudónimo de dos palabras solo cuenta con la consulta entera.
- **Las consultas de una sola pista no cambian:** la regla solo actúa con `len(pistas) > 1` («dostoyevski», «dickens», «grace» y «rose», iguales) [V].
- **Pruebas de f4:** no las repetí; me remito a su mensaje (corpus 41/41; C8 y C10, 9 de 9).
