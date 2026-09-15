# Esmeralda se perdió en dos sitios: Tu nivel y Pronunciar

- **Autor:** entrega-e6 (811c22), por encargo de la Central. Solo análisis, sin tocar código.
- **Qué pasó:** Esmeralda (15 años, B1) mandó una nota de voz tras probar la última versión. Le gustó mucho, pero se perdió en dos pantallas y volvió a decir «a lo mejor yo soy muy tonta». Si una lectora de su edad se siente tonta, el fallo es de diseño.
- **Cómo se miró:** recorrí las dos pantallas en el front publicado (Space `657ea8f`, `main-7JROFZ5J.js`) a 390 px táctil, como alguien que llega sin saber nada. Tu nivel lo contesté entero con respuestas de B1. Para Pronunciar sin micrófono ni cuenta usé un micrófono y una cuenta simulados, y la respuesta de corrección es la de «Don't you want to come with us?» con el ritmo real de 4e. Lo que se ve y en qué orden es el front real.
- **Capturas:** están en `auditoria/esmeralda/`, sin commit (la Central pidió commit solo de este archivo). En las capturas de página entera, la barra de abajo aparece a media altura: es cosa de la captura, en el móvil va fija abajo.

---

## 1. Tu nivel

> «no me convencieron las preguntas para medir el nivel… eran como tres, cuatro preguntas al principio, después se decía definir, o con otras preguntas… creo que esa opción no debería estar, porque debería definirlo de una»

### Lo que ve, paso a paso

| # | Pantalla | Qué le pide decidir, con sus palabras | Dónde dudaría |
|---|---|---|---|
| 1 | «1 de 6 · Un minuto para saber qué libros te van · ¿Con qué frecuencia lees algo en inglés?» (`01_nivel_primera_pregunta.png`) | Contestar, o «O mídete con un libro que ya leíste» abajo. | **La primera decisión llega antes de empezar**: dos caminos para lo mismo. |
| 2 | «2 de 6 · Lee este fragmento · ¿Cuánto entiendes?» (`02_nivel_fragmento_con_me_vale_asi.png`) | Encima de Atrás y Siguiente aparece **«Me vale así (0,80 · B1), guardar»**. | **En cada pregunta le ofrece parar.** «Me vale así» con una cifra que no entiende: ¿ya terminé?, ¿lo estoy haciendo bien? |
| 2–6 | La estimación provisional cambia con cada respuesta. | — | **Ve su nivel moverse.** Contestando como B1 y con sinceridad en el fragmento difícil («Me pierdo…»), empezó en **B1 (0,80)** y acabó en **A2 (0,56)**. Ver que el nivel baja mientras contesta es justo lo que hace pensar «soy tonta». |
| 7 | «Ya está · Tu nivel: A2 · 0,56 de 2 · Básico · Buscaré libros entre 0,31 y 0,81» (`03_nivel_ya_esta_tres_decisiones.png`) | **Tres botones:** «Guardar mi nivel», «Afinar con 3 preguntas más», «Cambiar una respuesta». | **Es el «después se decía definir» de su nota.** Tras «Ya está» le pide elegir otra vez, y «Afinar» no dice qué gana. Sin pulsar «Guardar» no se guarda nada. |
| 8 | «Afinar» → **«7 de 9»** (`04_nivel_afinar_7_de_9.png`) | Tres preguntas más, otra vez con «Me vale así (0,56 · A2), guardar». | **La barra decía 6 y ahora dice 9.** Al acabar vuelve a «Ya está» y otra vez a «Guardar mi nivel». |
| 9 | Resultado: «Lees en inglés a nivel A2 · 0,56 de 2 · Básico · la franja clara» (`05_nivel_resultado_con_afinar.png`) | «Ver libros de mi nivel», «Volver a medirme», y dos tarjetas más: «Afinar con un texto» y «Con un libro que ya leíste». | Después de guardar, **tres formas más de medirse.** Además hay jerga: «0,56 de 2», «franja clara», «el modelo lo mide». |

**En resumen:** de principio a fin hay **cinco sitios donde se ofrece otra forma de medirse o de parar**:
1. «O mídete con un libro», al empezar;
2. «Me vale así», en cada pregunta;
3. «Afinar con 3 preguntas más»;
4. «Afinar con un texto», en el resultado;
5. «Con un libro que ya leíste», en el resultado.

Ella pedía que la pantalla **lo defina de una**.

### Propuesta A (la que recomiendo): seis preguntas y el nivel, sin elegir nada

**Qué se quita:**
- «Me vale así» en cada paso;
- la estimación provisional mientras contesta, que es la que baja;
- la pantalla «Ya está» con sus tres botones;
- las 3 preguntas de «Afinar». Si aportan precisión, se meten en las seis, no como elección.

**Qué pasa a secundario:** «Afinar» queda como un enlace pequeño al final del resultado. «0,56 de 2» y la franja se esconden en «Ver el detalle».

Al contestar la sexta, el nivel **se guarda solo** y se ve así:

```
┌──────────────────────────────────────┐
│  TU NIVEL DE LECTURA                 │
│                                      │
│  Lees en inglés a nivel   B1         │
│  A1  A2 [B1] B2  C1  C2              │
│                                      │
│  Te buscaré libros que te queden     │
│  cómodos, con algo de reto.          │
│                                      │
│  [ 📖  Ver libros de mi nivel     ]   │
│                                      │
│  ▸ Ver el detalle  (0,80 de 2 …)     │
└──────────────────────────────────────┘
  Mis palabras                        >

  ¿No te convence?  Afínalo con un libro
  que ya leíste · con un texto           ← enlace pequeño, al final
```

Durante las preguntas, solo la pregunta, sus opciones y «Atrás / Siguiente»:

```
  ‹  ▓▓▓▓▓░░░░░░  3 de 6

  LEE ESTE FRAGMENTO
  ┌──────────────────────────────┐
  │ Alice was beginning to get … │
  └──────────────────────────────┘
  ¿Cuánto entiendes?
  ( ) Lo entiendo con naturalidad…
  ( ) Capto bien la idea…
  …
  [ Atrás ]            [ Siguiente › ]
```

«Volver a medirme» también baja al enlace pequeño.

### Propuesta B (cambio mínimo)

Mantiene el cuestionario, pero:
1. «Ya está» deja de pedir decidir. Guarda solo y muestra un único botón, «Ver libros de mi nivel»; «Afinar con 3 preguntas más» baja a enlace pequeño.
2. «Me vale así» no aparece hasta la pregunta 4, y dice «Terminar ya» sin cifra.
3. El «O mídete con un libro» de la primera pregunta se va al resultado.

```
  YA ESTÁ
  Tu nivel: B1
  [ ✓ Ver libros de mi nivel ]
  afinar con 3 preguntas más ›     ← enlace pequeño
```

**Duda para Miguel, aparte del diseño:** con respuestas sinceras de B1 el cuestionario dio A2. El fragmento difícil pesa mucho: la fórmula toma el máximo de los fragmentos. Si Esmeralda contestó así, el «soy tonta» puede venir también de ver un A2 que no es el suyo. No lo he medido con más perfiles.

---

## 2. Pronunciar

> «me perdí en la corrección de la pronunciación… me gustó muchísimo, pero… no entendí cómo usarlo… en lo de que tienes que ir como que más lento, en eso me perdí un poquito»

### Lo que ve, paso a paso

| # | Pantalla | Qué hace ella | Dónde dudaría |
|---|---|---|---|
| 1 | «Lee una frase en voz alta» · **1 La frase** · **2 Tu voz** · micrófono grande abajo (`06_pronunciar_llegada.png`) | Escribe o pega una frase y pulsa el micrófono. | Sin libro abierto no hay frase de ejemplo, y la caja vacía no le dice qué escribir. |
| 2 | Grabando: «Grabando… 3 s · pulsa para terminar». Al parar: «Escúchate y pide la corrección», su audio y abajo **un botón verde con solo un ✓** entre «Otra vez» y «Otra frase». | Tiene que adivinar que el ✓ es «Corrígeme». | **El paso clave no tiene texto visible**: «Corrígeme» solo está en el aria-label. |
| 3 | Corrección, en este orden (`08_pronunciar_correccion_completa.png`): **1)** «71 /100 · Bien, con algún detalle · Se te entendió: …»; **2)** la frase con etiquetas **«aquí aceleras»** y **«aquí sin pausa»** delante de las palabras; **3)** una leyenda de cuatro puntos; **4)** «Cómo suena natural», con «doncha / wanna», IPA y chips «IA»; **5)** **el resumen en español** («Casi todo se entendió. «want» sonó como «won't»…»); **6)** la palabra a practicar, con IPA, /ɑ/ y «Ver cómo se mueve la boca» cerrado; **7)** «Cómo debería sonar». | Lee de arriba abajo. | **Lo que más le sirve, el resumen, sale en quinto lugar**, detrás del ritmo y del habla natural, que son lo más avanzado. |
| 4 | «aquí aceleras» delante de «don't you want» | — | **Es una orden de ir más rápido**, pero «aquí aceleras» parece describir lo que hizo. Y «aquí sin pausa» sale **delante de «to»** cuando habla de la pausa **después de «want»**. |
| 5 | Dentro de «Ver cómo se mueve la boca»: los cortes y **«Escuchar y ver» · «Más lento» · «Boca en 3D»** (`09_pronunciar_boca_escuchar_y_ver_mas_lento.png`). Lo mismo en la ficha de un sonido de la tabla del AFI (`07_pronunciar_ficha_sonido_mas_lento.png`). | Pulsa «Más lento». | **Es su «tienes que ir como que más lento».** El botón cambia la velocidad del audio y la animación, pero se lee como un consejo: «ve más lento». Encima dice lo contrario que «aquí aceleras», que tiene justo arriba. Al pulsarlo pasa a «Lento · 0,5×», luego a «Muy lento · 0,25×» y vuelve a «Más lento»: a veces nombra la acción y a veces el estado. |
| 6 | Tras corregir, la barra sigue con **✓ Corrígeme** en el centro | — | Puede volver a pulsarlo sin haber grabado otra vez, y es otra llamada de pago con la misma grabación. |

### Propuesta A (la que recomiendo): primero qué hacer, lo avanzado plegado

**Qué se quita del primer plano:**
- las etiquetas de ritmo;
- la leyenda de cuatro puntos;
- «Cómo suena natural».

Todo eso pasa a un plegable «Para sonar más natural», cerrado.

**Qué cambia de nombre:**
- «Más lento» pasa a ser un interruptor de estado: **«🐢 Despacio»**, encendido o apagado;
- «aquí aceleras» pasa a **«más seguido aquí»**, y «aquí sin pausa» a **«no pares aquí»**, puesta detrás de la palabra;
- el ✓ lleva texto: **«Corrígeme»**.

```
┌──────────────────────────────────────┐
│  71/100   Bien, con algún detalle    │
│                                      │
│  Casi todo se entendió. «want» sonó  │  ← el resumen, lo primero
│  como «won't»: abre más la boca.     │
│                                      │
│  don't  you  [want]  to  come  with  │  ← solo bien / a revisar
│  us                                  │
├──────────────────────────────────────┤
│  PRACTICA ESTA PALABRA               │
│  want   /wɑnt/                       │
│  [ 🔊 Escuchar y ver ]  [🐢 Despacio]│  ← interruptor, no orden
│  (corte de la boca)                  │
│  Qué falla: …  Cómo colocar la boca: …│
│  ▸ Boca en 3D                        │
├──────────────────────────────────────┤
│  ▸ Para sonar más natural            │  ← plegado: doncha, wanna,
│    (enlaces, dónde no parar…)        │    «no pares aquí», IPA, IA
├──────────────────────────────────────┤
│  [ 🎤 Grabar otra vez ]  Otra frase › │  ← sin «Corrígeme» repetido
└──────────────────────────────────────┘
```

Barra antes de corregir:

```
  [ ↻ Otra vez ]   ( ✓ Corrígeme )   [ Otra frase › ]
```

### Propuesta B (cambio mínimo)

1. **El resumen**, arriba, justo debajo de la nota.
2. **«Más lento»** pasa a «🐢 Despacio», con estado visible (marcado o no) y sin «0,5×».
3. **Las etiquetas de ritmo:** «más seguido aquí» y «no pares aquí», después de la palabra a la que se refieren.
4. **El ✓** lleva la palabra «Corrígeme».

---

## Lo que decide Miguel

| Pantalla | A | B |
|---|---|---|
| Tu nivel | Seis preguntas, se guarda solo y «afinar» queda como enlace pequeño; nada de «Me vale así» ni de nivel provisional. | «Ya está» sin decisiones; «Me vale así» desde la 4 y sin cifra. |
| Pronunciar | Resumen primero, palabra a practicar con «🐢 Despacio», y lo natural plegado. | Resumen arriba, «🐢 Despacio», etiquetas de ritmo claras y «Corrígeme» con texto. |

Las dos A tocan plantilla y orden, sin API. «Guardar al acabar» usa la misma llamada que hoy hace «Guardar mi nivel». Las dos B son de pocas líneas.
