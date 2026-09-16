# Ronda 4 · El micrófono de *Pronunciar* a 390 × 844, medido tres veces (f4)

16 de septiembre de 2026. Encargo de la Central: repetir por mi cuenta la medida de e6 sobre el front
publicado. Solo lectura: no se tocó `front/` ni `app/`, y no se usaron credenciales ni cuenta.

**Lo primero, porque explica todo lo demás: aquí hay tres medidas de tres versiones distintas, no tres
lecturas contradictorias de la misma.** El front se publicó dos veces mientras yo medía. Cada apartado
dice sobre qué revisión se tomó y qué cambió respecto a la anterior.

## Aviso de vocabulario

`48d748d`, `fce0df6` y `9b4a3b5` son **revisiones del Space** de Hugging Face, **no commits de git**: no
resuelven con `git show` y buscarlas en el repositorio hace perder el tiempo. Al lado va siempre el
commit del repositorio que las produjo.

| Revisión del Space | Commit del repo | Publicada (UTC) | Paquete servido | Qué trae |
|---|---|---|---|---|
| `48d748d` | `940c275` | 16:22:50 | — | Estado anterior: «Corrígeme» apagado sin sesión |
| `fce0df6` | `5e9acc0` | 16:54:15 | `main-WCIGOWQ2.js` | «Corrígeme» se pulsa y contesta, pero el panel tapa el aviso |
| `9b4a3b5` | `a1c4268` | — | `main-M2PX4KNU.js` | El aviso queda a la vista; el panel solo abre con «Entrar» |

En las tres, el paquete se leyó de la propia página (`script[src]`), no se supuso.

## Método

Pestaña a `390×844×3` con `mobile` y `touch`, **sin sesión** (botón «Entrar» presente; en
`localStorage` solo preferencias —`letra`, `color-libro`, `idioma`, `acento`, `modo`, `tema`, `lector`—
y ninguna clave de cuenta; `literalevel.lector` es el identificador del navegador para `X-Lector`, no
una sesión). Frase escrita en el `textarea`. Todas las cifras salen de `getBoundingClientRect()` con
`scrollY = 0` y ventana de 844 px.

`navigator.mediaDevices` se sustituye **en caliente**, y basta: `grabar()` resuelve
`navigator.mediaDevices.getUserMedia` en el momento de pulsar (`pronunciar.ts`, `puedeGrabar()` y el
`try` de `grabar()`). Se restaura al terminar. El caso concedido usa un `MediaStream` **real** sacado de
`AudioContext` → `createMediaStreamDestination()` con un oscilador: `MediaRecorder` graba de verdad,
sin hardware.

## 1. Los seis finales de pulsar el micrófono

**Medido en `fce0df6` y repetido entero en `9b4a3b5`. Las cifras son idénticas en las dos**, y coinciden
con las que publicó e6 sobre `48d748d`: los dos arreglos tocaron «Corrígeme», no el camino del permiso.

| Final | Texto | Línea de mensaje | Barra |
|---|---|---|---|
| `navigator.mediaDevices` no existe | «Este navegador no puede grabar. Abre LiteraLevel en Chrome o Safari.» | **638 – 688** | 629 – 776 |
| Permiso denegado (`NotAllowedError`) | «No hay permiso para el micrófono. Actívalo en los ajustes del sitio y vuelve a intentar.» | **638 – 688** | 629 – 776 |
| El permiso no contesta, a los 2 s | «Acepta el permiso del micrófono.» | **656 – 688** | 647 – 776 |
| El permiso no contesta, pasados 5 s | «¿No ves el permiso? Abre LiteraLevel en Chrome o Safari.» | **636 – 688** | 628 – 776 |
| Concedido, sin micrófono (`NotFoundError`) | «No encontramos ningún micrófono. Conecta uno y vuelve a intentar.» | **638 – 688** | 629 – 776 |
| Concedido, con micrófono | «Grabando: habla ahora · 1 s» → «· 3 s» | **657 – 688** | 649 – 776 |

- Clases: `.linea-barra.error` en los tres de error, `.linea-barra.aviso` en los dos de permiso
  pendiente, `.linea-barra.grabando` mientras graba.
- **Los seis acaban exactamente en 688**, con la navegación fija (`.nav-movil`) en **777 – 844**: 89 px
  de holgura, y `scrollY = 0` en todas las lecturas. **Se leen sin desplazar y ninguno es mudo.**
- Referencia sin mensaje: la barra `.grabadora` ocupa 687 – 776 y crece hacia arriba al aparecer el texto.
- El cambio de texto a los 5 s **se comprobó de verdad**, con una promesa que no se resuelve nunca, y se
  soltó después para no dejar el botón bloqueado por `pidiendo()`.
- En el caso concedido el contador **avanza** (1 s → 3 s, no solo aparece), el botón pasa a
  `aria-label="Terminar la grabación"` y al parar queda un `<audio>` en `[34,684,323,54]`.

**Coincido con e6 cifra por cifra en los seis finales.**

> **Cinco o seis, que es el mismo conjunto contado de dos maneras.** Los entregables dicen «cinco
> finales (el del permiso pendiente, en dos momentos)» y aquí se cuentan seis. No hay contradicción:
> el permiso que no contesta es **un solo final** que enseña **dos textos**, a los 2 s y pasados los
> 5 s, y esta tabla les da una fila a cada uno porque cada texto se midió por separado. Los otros
> cuatro coinciden uno a uno. Equivalencia: 5 finales = 6 filas − 1 (las dos filas del permiso
> pendiente son el mismo final). Decisión de la Central, 16 sep.

## 2. «Corrígeme» sin sesión: lo que cambió en cada versión

Aquí es donde las tres versiones dicen cosas distintas, y por eso no hay contradicción entre informes.

### `48d748d` — apagado (medida de e6, no mía)

El botón iba `[disabled]="corrigiendo() || bloqueada()"`. e6 lo midió en 704 – 768 `disabled`, sin
`title` ni `aria-describedby`, y pulsarlo no producía respuesta; la explicación quedaba 309 px más
arriba. **No lo he medido yo**: cuando abrí la pestaña, esa revisión ya no estaba publicada.

### `fce0df6` — contesta, pero el panel tapa su propio aviso (medido por mí)

- Botón `disabled: false`, sin `title` ni `aria-describedby`, rect `[118,704,155,64]`.
- Al pulsarlo aparece «La corrección necesita tu perfil. Grabarte y escucharte, no.», con «Entrar» en
  `[212,650,74,40]`.
- **Pero el aviso no se ve:** el propio clic abre los ajustes, `aside.panel` queda en `[0,169,390,675]`
  —de 169 a 844— por encima de la barra (617 – 776), y `document.elementFromPoint(195, 665)`, el centro
  del aviso, devuelve el **`footer` del panel de ajustes**, no el aviso.

El mensaje estaba bien colocado y aun así quien pulsaba no lo leía.

### `9b4a3b5` — corregido, y comprobado punto por punto (medido por mí)

| Lo que había que confirmar | Medido |
|---|---|
| Botón pulsable en 704 – 768 | rect `[118,704,155,64]` → **704 – 768**, `disabled: false`, sin `title` ni `aria-describedby` |
| Aviso en 625 – 696, `role="alert"` | rect `[16,625,358,71]` → **625 – 696**, `role="alert"` |
| 71 px y hasta cuatro líneas | alto **71 px**; `line-height` 19,44 → **3,65 líneas**, dentro de cuatro |
| Con su «Entrar» dentro | sí, dentro del propio aviso, en `[212,650,74,40]` |
| Ochenta por encima de la navegación | **81 px** (777 − 696) |
| `elementFromPoint` en el centro devuelve el aviso | centro `(195, 661)` → `p.linea-barra.error`, **el aviso**. Es justo lo contrario de `fce0df6` |
| `panelAbierto: false` al pulsar | **falso** inmediatamente después del clic |
| El panel solo abre con «Entrar» | cerrado antes; al pulsar «Entrar» abre `aside.panel` en `[0,169,390,675]` y el foco entra en un campo. El aviso sigue en pantalla |

**Confirmo las cuatro afirmaciones de e6 sobre `9b4a3b5`.** La comprobación de `panelAbierto` se hizo en
una pasada aparte de la de «Entrar», a propósito: si se pulsan los dos en el mismo guion, un panel
abierto al final no se puede atribuir a un clic ni al otro.

## Comprobado y correcto

- Los seis finales del micrófono escriben algo visible, acaban en 688 y se leen sin desplazar, en
  `fce0df6` y en `9b4a3b5`. Ninguno es mudo.
- El cambio de texto a los 5 s del permiso pendiente ocurre.
- En `9b4a3b5`, «Corrígeme» sin sesión se pulsa, contesta dentro de la barra, el aviso queda a la vista
  y el panel ya no se abre encima.

## Huecos y límites declarados

- **No he medido `48d748d`.** Se republicó mientras preparaba la pestaña. Lo de esa revisión es de e6
  (`auditoria/microfono_casos_a_b_2026-09-16.md`); aquí se cita, no se reproduce.
- **El micrófono del caso concedido es simulado** (`AudioContext`), no hardware real, y **nadie ha oído
  el audio**: consta que se graba, que el contador corre y que queda un `<audio>`, no que suene bien.
- **«Corrígeme» con sesión no se ha probado**: exige cuenta y no se usaron credenciales. Que con perfil
  se encienda y corrija sigue siendo cosa de la prueba de Miguel.
- Las medidas de `fce0df6` y `9b4a3b5` se tomaron en cargas distintas de la página; dentro de cada
  revisión, todas las cifras salen de la misma carga y del mismo paquete.
