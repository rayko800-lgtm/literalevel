# Qué se ve al pulsar el micrófono, y qué funciona sin cuenta

**Medido el 16 de septiembre de 2026** sobre el front publicado (Space
`48d748d7624a17ca0bad1cb0ca43cd413e52138f`, commit `940c275`), a **390 × 844 px**,
móvil y táctil, en un contexto de navegador aislado y **sin sesión**. Todas las
cifras son píxeles desde el borde superior de la ventana, sin desplazar.

Nadie tocó código para esto: la aplicación es la publicada y las únicas
intervenciones fueron sustituir `navigator.mediaDevices` **antes** de que
arrancase la aplicación, para reproducir los cuatro caminos del permiso que no
se pueden provocar de otra forma en esta máquina.

**Los dos casos se miden por separado y no se atribuyen a nadie.** De quién es
la nota de voz lo confirma Miguel.

- **Caso A — con sesión:** entró, pulsó el micrófono y «no se activó la
  grabación ni le dijo que hablara». Aquí solo se mide la parte que no depende
  de la cuenta: qué pinta la pantalla en cada final posible de la petición de
  permiso. El resto lo prueba Miguel (§4).
- **Caso B — sin sesión:** qué ofrece y qué niega la aplicación a quien no ha
  entrado.

---

## 0. El escenario: dónde cae cada cosa

| Elemento | Píxeles |
|---|---|
| Cabecera fija (`.barra`) | 0 – 65 |
| Aviso ámbar «La corrección usa OpenAI…» | 303 – 395 (su botón «Entrar», 340 – 380) |
| Paso 1 «La frase» | 395 – 590 |
| Barra fija del micrófono (`.grabadora`) | 629 – 776 |
| **Línea de mensaje, dentro de la barra** | **636 – 688** |
| Botón del micrófono | 696 – 768 |
| Navegación inferior fija (`.nav-movil`) | 777 – 844 |

El dato que importa: **la línea de mensaje va dentro de la barra fija y termina
en 688**, noventa píxeles por encima de la navegación inferior. En la versión
anterior estos mismos textos se pintaban en 750 – 849, debajo de una barra que
empieza en 687, y por eso no se veían. La corrección de `601788b` está viva en
lo publicado: **en los cinco escenarios el mensaje se lee sin desplazar**.

---

## 1. Caso A: los cinco finales de pulsar el micrófono

Frase escrita, micrófono pulsado una vez. Entre paréntesis, la posición.

| Escenario | Qué se lee |
|---|---|
| **`navigator.mediaDevices` no existe** (WebView, o contexto no seguro) | «Este navegador no puede grabar. Abre LiteraLevel en Chrome o Safari.» (638 – 688) |
| **Permiso denegado** (`NotAllowedError`) | «No hay permiso para el micrófono. Actívalo en los ajustes del sitio y vuelve a intentar.» (638 – 688) |
| **El permiso no contesta**, a los 2 s | «Acepta el permiso del micrófono.» (656 – 688) |
| **El permiso no contesta**, pasados 5 s | «¿No ves el permiso? Abre LiteraLevel en Chrome o Safari.» (636 – 688) |
| **Concedido, sin micrófono** (`NotFoundError`) | «No encontramos ningún micrófono. Conecta uno y vuelve a intentar.» (638 – 688) |
| **Concedido, con micrófono** | «Grabando: habla ahora · 3 s» (657 – 688) y, en el paso 2, «Grabando… 3 s · pulsa para terminar» |

En los cuatro primeros el paso 2 repite el mensaje en su sitio («2 · Tu voz ·
Pulsa el micrófono y lee la frase con calma. + el aviso»), así que el texto
aparece dos veces en pantalla, no una.

La lógica está en `front/src/app/pantallas/pronunciar.ts:178-210`: `lineaBarra`
decide el texto, `mensajeMicrofono(e)` reparte un mensaje distinto por cada
nombre de error, y `pidiendoLento` cambia el texto a los 5 s de silencio.

**Conclusión del caso A, y su límite.** Hoy, en lo publicado, **no existe el
camino «pulso y no pasa nada»** en ninguno de los cinco finales: los cinco
escriben algo visible. Eso deja tres posibilidades para la nota de voz, y
ninguna se puede decidir desde aquí:

1. La nota es **anterior a `601788b`**, cuando el mensaje se pintaba debajo de
   la barra y efectivamente no se veía. Es la explicación que mejor encaja con
   «no te dice que hables».
2. El mensaje salió y **no se leyó como respuesta**: es una franja fina, gris,
   pegada encima del botón, y quien mira el botón puede no registrarla.
3. El fallo está **después** del permiso —`MediaRecorder` no arranca, o el
   contador se queda parado—, que es el único tramo que no he podido provocar.

---

## 2. Caso B: qué funciona sin cuenta

Verificado tocando cada cosa, no leyendo el código.

**Funciona entero sin entrar:**

- **Grabarse.** El micrófono arranca, el contador corre y el paso 2 pasa a
  «Escúchate y pide la corrección.»
- **Escucharse.** Queda un `<audio controls>` en 726 – 780 con el audio propio
  (blob de 29,9 s en la medición).
- **Repetir.** Botón «Otra vez» en 705 – 767.
- **Ver cómo se dice cada sonido.** La tarjeta «Los sonidos del inglés (AFI)»
  es un `<details>` **cerrado de inicio** (854 – 958). Al abrirlo carga **41
  sonidos** agrupados; al tocar `/p/` salen la descripción («oclusiva bilabial
  sorda», «Como en pen, top»), el corte de perfil de la boca —servido por la
  API, `/api/articulacion/ga/p.svg`, cargado y pintado—, los botones «Escuchar
  y ver», «🐢 Despacio» y «Boca en 3D», la posición de labios y lengua, y el
  aviso «Ojo: decirla sin soplo, como la p española, hace que "pin" suene a
  "bin"». Nada de esto pidió cuenta.
- **El lector entero**, con el diccionario (§3).

**No funciona sin entrar:**

- **«Corrígeme».** Es lo único cerrado de la pantalla.

**El texto que lo anuncia es correcto y está a la vista:** el subtítulo dice
«Sin entrar puedes grabarte, escucharte y ver cómo se dice cada sonido», y el
aviso ámbar de 303 – 395 dice «La corrección usa OpenAI, así que necesita que
entres con tu perfil», con su «Entrar». Ambos se leen sin desplazar.

### El defecto de esta parte

**«Corrígeme» está `disabled` y no explica por qué donde está.** Medido en
`704 – 768`: el atributo es `disabled`, sin `title` y sin `aria-describedby`, y
**pulsarlo no produce ninguna respuesta** (el texto de la pantalla no cambia).
La explicación existe, pero está **309 píxeles más arriba**, y quien acaba de
grabar está mirando la mitad de abajo. Además, un botón deshabilitado no lo
anuncia un lector de pantalla más que como «no disponible».

Esto no es lo que cuenta la nota de voz, pero sí es un «pulso y no pasa nada»
real, y está en la misma pantalla.

**Propuesta, sin implementar** (decide Miguel):

- Que «Corrígeme» **no vaya deshabilitado**: que se pueda pulsar y que, sin
  sesión, abra los ajustes en «Tu perfil» —el mismo destino que el «Entrar» del
  aviso—, en lugar de no hacer nada.
- Y que debajo del botón, dentro de la barra, en la misma línea de mensaje que
  ya usan los avisos del micrófono (636 – 688), ponga:
  **«La corrección necesita tu perfil. Grabarte y escucharte, no.»**
  Repite el «qué sí» al lado del «qué no».

### Lo que se hizo, y las dos cifras que corrijo

Miguel lo aprobó por la Central el mismo día y está publicado. Medido otra vez
sobre el commit, a 390 px, con el botón ya pulsable:

- El aviso sale en **625 – 696**, con `role="alert"` y su botón «Entrar»
  dentro, sin desbordar a lo ancho y ochenta píxeles por encima de la
  navegación inferior. **Se lee sin desplazar.**
- **Corrijo lo que escribí arriba:** no cabe en una línea. Ocupa **71 px**, es
  decir **hasta cuatro líneas** contando el «Entrar». Cabe y se lee, pero el
  dato bueno es ese.
- La primera versión **abría el panel de Ajustes al pulsar**, y medido ocupaba
  de 169 a 844: tapaba el propio aviso. Es exactamente el defecto que se estaba
  corrigiendo, así que la Central decidió quitarlo: ahora pulsar «Corrígeme»
  sin sesión **solo** muestra el aviso, y el panel se abre si el usuario pulsa
  «Entrar». Es lo que hace el lector.
- Hay un segundo texto, para cuando el servidor no tiene clave de OpenAI —donde
  entrar no arreglaría nada—: «La corrección no está disponible en este
  servidor. Grabarte y escucharte, sí.», sin «Entrar» y sin panel.

---

## 3. El lector sin cuenta: consultar una palabra

Gesto real: mantener presionada la palabra. El panel es una hoja inferior
(`aside.panel-palabra`) que ocupa **338 – 844** y tiene desplazamiento propio
(616 px de contenido en 505 visibles).

**Palabra que sí está en el diccionario** («waistcoat»): categoría y frecuencia
(«noun · rara»), botones US/UK, la acepción de Wiktionary («An ornamental
garment worn under a doublet»), la cautela «No estoy seguro de que sea esta
acepción (afinidad 0,20). Lee la frase entera antes de fiarte», y la frase del
libro. Todo sin cuenta.

**Palabra que no está** («Dinah»): dice exactamente

> **«Esta palabra no está en el diccionario.»** (545 – 570)

y debajo, el aviso de lo que falta (677 – 815, con «Entrar» en 761 – 801):

> «Esta parte necesita que entres con tu perfil. El resto de la aplicación
> —medir libros, leerlos, el diccionario y el cuestionario— funciona sin
> entrar.»

Los dos textos se leen **sin desplazar dentro del panel** y sin que nada los
tape. Aquí no hay nada que arreglar: dice qué falta, qué no falta y cómo
entrar. Es el patrón que le falta a «Corrígeme».

---

## 4. Lo que tiene que probar Miguel, con su cuenta

No se puede medir desde aquí y no se supone. Tres pasos, en su móvil, con el
enlace tal como le llegó por WhatsApp. **Sin mandar ninguna contraseña por
ningún canal.**

1. **Abrir el enlace desde WhatsApp**, entrar con su perfil, ir a *Pronunciar*,
   escribir una frase y pulsar el micrófono una vez. Mirar la **franja fina que
   hay justo encima del botón**, dentro de la barra gris, y decir **qué pone
   exactamente** (una captura vale más). Si no pone nada, decir «no pone nada».
2. **Si pone «Acepta el permiso del micrófono.» y no aparece ningún cartel del
   sistema:** salir, abrir el enlace en Chrome (⋮ → «Abrir en Chrome») y repetir
   el paso 1. Decir si ahí sí sale el cartel del permiso.
3. **Si pone «Grabando: habla ahora · N s», mirar si el número avanza.** Si se
   queda parado, el fallo está después del permiso y no en él. Y al terminar la
   grabación, decir si **«Corrígeme» sigue apagado estando dentro**: con sesión
   tiene que encenderse.

Con esas tres respuestas se cierra el caso A. Sin ellas, la causa sigue en
revisión y no debe escribirse en los documentos.

---

## 5. Lo que se revisó y estaba bien

Para que se distinga lo mirado de lo no mirado:

- Los mensajes del micrófono no los tapa nada en ninguno de los cinco
  escenarios (medido con las cajas de los elementos fijos).
- El aviso de OpenAI y el botón «Entrar» de *Pronunciar* se ven sin desplazar.
- El AFI no pide cuenta en ningún punto, ni siquiera el corte de la boca, que
  viene de la API.
- El lector dice lo correcto tanto con palabra en el diccionario como sin ella.
- Sin frase escrita, el micrófono se marca `aria-disabled` y el paso 2 dice
  «Primero escribe la frase.»

**No comprobado:** que los audios **suenen** (esta máquina no reproduce y no hay
forma de oírlos desde aquí); solo consta que los recursos existen y que la API
responde. Y el tramo posterior al permiso (`MediaRecorder`), que es el paso 3
de Miguel.
