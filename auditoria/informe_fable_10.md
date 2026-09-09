# Auditoría 10 — la aplicación, no los documentos

Auditor externo. Árbol `1a0276c` (limpio, `git status` vacío). Space
`MikeMaki1763/literalevel` en `RUNNING`, sha `6092831`, `lastModified`
2026-09-09 22:36 Z, página 200, `/config` 200. Conducido con chrome-devtools en
dos pestañas: una con el modo de color del sistema (aquí, oscuro) y otra con
`?__theme=light`. Ningún archivo del proyecto modificado; esta es la única
escritura.

## Recuento

| Gravedad | Nº |
|---|---:|
| Crítico | 1 |
| Serio | 4 |
| Menor | 6 |
| Notas (sin acción obligada) | 3 |

Y lo que está bien, que también es resultado: las siete cifras vivas cuadran,
el Space **puntúa** (fallo 1 cerrado en producción), el bloque «Entrar con tu
perfil» está arriba y abierto, no queda rastro de «código», y en «Leer» la
palabra va antes del texto. Ver §OK.

---

## CRÍTICO

### C1. En un navegador en modo claro, la paleta por defecto es ilegible: texto negro sobre paneles negros

**Evidencia, medida en la app desplegada.** Con `?__theme=light` (que es lo
que Gradio aplica solo cuando el sistema del visitante está en modo claro,
porque `theme_mode` es «system»), en la paleta por defecto «Hielo»:

- párrafo de bienvenida «Lee en inglés al nivel que te toca»: `color`
  computado `rgb(23,30,48)` (= `NOCHE.c800`, `app/ui.py:277`) sobre el panel
  `rgba(12,22,38,.72)` compuesto sobre `#05070d` → **1,1:1**;
- la misma medición vale para todo lo que sea Markdown o HTML: la cabecera del
  acordeón «Entrar con tu perfil», su explicación, la fila de pestañas, el
  texto de «Estado». Captura: `scratchpad/hielo_light.png` — se ve una página
  negra con paneles vacíos y dos cajas de texto claras;
- la regla que manda es de Gradio, `.gradio-container-6-26-0 .prose *
  {color:var(--body-text-color)}` (`0.DSNh2M0f.css`), y `--body-text-color`
  la fija el **tema** (`TEMA`, `app/ui.py:279`) según el modo claro/oscuro
  del navegador, no la paleta: `paletas.css()` solo pinta
  `color:var(--ll-texto)` en `body,gradio-app,.gradio-container`
  (`app/paletas.py:175-183`), y una regla sobre un ancestro no vence a una
  regla que apunta al propio elemento.

**Es simétrico.** En el navegador en modo oscuro (la otra pestaña), las tres
paletas claras dan el efecto inverso: «Menta» pinta `rgb(214,220,234)`
(`NOCHE.c100`) sobre panel `rgba(255,255,255,.86)` sobre `#f4faf6` →
**1,3:1** en TODO el cuerpo de texto (captura `scratchpad/menta_colores.png`).
Calculado para las cinco paletas con el color real de cada modo:

| paleta | texto `.prose` sobre panel, modo claro | modo oscuro |
|---|---:|---:|
| hielo (por defecto) | **1,13** | 13,67 |
| amanecer | 16,13 | **1,33** |
| menta | 16,47 | **1,36** |
| papel | 15,68 | **1,30** |
| medianoche | **1,04** | 11,57 |

Es decir: **ninguna paleta se lee en los dos modos**, y la que sale al abrir
la app se lee solo en modo oscuro. Un profesor con un portátil en modo claro
—que es el valor por defecto de Windows y macOS— abre el enlace y ve una
página negra sin texto.

**Por qué ninguna prueba lo ve.** `_contraste_suficiente` y
`_opacidad_no_borra_el_texto` (`pruebas_extremas.py:781-897`) miden
`--ll-texto` sobre `--ll-fondo`. El navegador no pinta esa pareja en ningún
párrafo: pinta `--body-text-color` sobre `--ll-panel`. Las 40 parejas y las
opacidades pasan porque miden colores que no se usan.

**Consecuencia sobre el fallo 3 «corregido».** La queja de Miguel («en las
pastel las letras son muy tenues») es exactamente lo que se ve en un móvil en
modo oscuro con una paleta clara (1,3:1). Subir `opacity` de .62 a .78 no
toca eso: el color del texto sigue siendo el del tema. La corrección del
fallo 3 mide y arregla otra cosa.

**Arreglo (indicativo, no ejecutado):** que `paletas.css()` reasigne también
las variables del tema de Gradio que la página usa de verdad —al menos
`--body-text-color`, `--body-text-color-subdued`, `--block-label-text-color`,
`--block-title-text-color`, `--input-background-fill`, `--input-text-color`,
`--background-fill-primary/secondary`— desde `--ll-texto`/`--ll-panel`, o
fijar el modo de Gradio en uno solo. Y que la prueba de contraste mida
`--body-text-color` (en sus dos valores) sobre `--ll-panel` compuesto.

---

## SERIO

### S1. La pestaña «Estado» del Space dice que el modelo FALTA, mientras el modelo funciona

`app/ui.py:2104`: `modelo_ok = os.path.isdir(RUTA_MODELO)`. En el Space
`RUTA_MODELO` es `MikeMaki1763/literalevel-v4`. Leído en vivo en la pestaña
«Estado»:

```
Recursos
Modelo v4: FALTA — MikeMaki1763/literalevel-v4
```

Es el mismo error que mató la puntuación (fallo 1), corregido en
`scoring.Puntuador.__init__` (`app/scoring.py:211`) y **no** en el
diagnóstico, que existe «para la demo» (`app/ui.py:9`). Delante de un
profesor, la pantalla que se enseña para demostrar que todo está en su sitio
dice que falta lo principal. Basta reutilizar `_parece_repo_hf` ahí.

### S2. Una «ñ» (o cualquier no-ASCII) en la contraseña revienta el inicio de sesión con un «Error» pelado

`app/cuentas.py:120`: `hmac.compare_digest(c, guardada)`. Con `str`,
`compare_digest` **solo admite ASCII**; con otra cosa lanza
`TypeError: comparing strings with non-ASCII characters is not supported`.
Reproducido en local:

```
verificar('nadie',  'contraseña') -> TypeError
verificar('acento', 'contraseña') -> TypeError   (clave declarada en el entorno con ñ)
ui._entrar('nadie', 'contraseña') -> TypeError
```

y **en la app desplegada**: usuario `nadie`, contraseña `contraseña`, «Entrar»
→ aparece «Error» junto al botón «Salir» y el estado no cambia. Nada lo
captura: `_entrar` (`app/ui.py:210-235`) no envuelve la llamada. Dos
consecuencias: (a) cualquier visitante que teclee una ñ, una tilde o un
emoji ve un error crudo de Gradio en vez de «No he podido entrar»; (b) si a
un perfil se le da una clave con ñ en `LITERALEVEL_CUENTAS`, ese perfil no
puede entrar nunca. El código anterior tenía la misma llamada, pero un código
`XXXX-XXXX-XXXX` no invita a teclear una ñ; una caja «Contraseña» en una app
en español, sí. Arreglo: comparar `c.encode()` con `guardada.encode()`.

### S3. Las tarjetas de «Mis libros» y «Mis palabras» quedan entre 2,5 y 3,9:1 en las tres paletas claras, en ambos modos

`app/ui.py:1915` y `:2001`: `background:rgba(8,16,28,.55)`, un azul casi
negro al 55 %, pensado para «Hielo». Sobre `--ll-panel` claro compone un gris
medio (`#72797e` en menta). Con el color de texto real de cada modo, sobre
esa tarjeta compuesta:

| paleta | texto pleno, modo claro | `.ll-d`/`.ll-a` a `opacity:.78` | modo oscuro pleno | `.78` |
|---|---:|---:|---:|---:|
| amanecer | 3,85 | **2,96** | 3,14 | **2,53** |
| menta | 3,91 | **2,99** | 3,09 | **2,50** |
| papel | 3,77 | **2,91** | 3,21 | **2,58** |

(Captura de las tarjetas inyectadas con el CSS exacto de `_CSS_BIBLIO` y
`_CSS_CUADERNO`: `scratchpad/menta_colores.png`, abajo.) Es el «`rgba()` con
alfa que hace lo mismo y nadie mide» que preguntaba el encargo: la prueba
nueva (`pruebas_extremas.py:887-896`) solo compone `--ll-texto` sobre
`--ll-fondo` y no conoce ni el panel ni la tarjeta. La subida a `.78` deja
esas dos pestañas por debajo de AA en las paletas claras igual que antes.

### S4. `auditoria/cierre_2026-09-09.md:197` afirma «los tres tienen ahora una prueba que los cazaría»; dos de los tres no la tienen

- Fallo 1 (ruta del Hub): `grep -n "_parece_repo_hf\|literalevel-v4\|Hub"` en
  `pruebas_extremas.py`, `pruebas_integracion.py`, `tests_smoke.py`,
  `pruebas_ficha.py`, `pruebas_perfil.py` → **cero** resultados. Ninguna
  prueba instancia `Puntuador` con un identificador ni llama a
  `_parece_repo_hf`. La propia skill (`.claude/skills/probar-la-app-de-verdad/SKILL.md`,
  §1) dice «escribe una prueba para cada una, aunque sea fea».
- Fallo 2 (la caja no se encontraba): ninguna prueba busca «Entrar con tu
  perfil» ni comprueba que el acordeón esté fuera de las pestañas y abierto.
  Las cinco pruebas nuevas (`pruebas_extremas.py:1084-1096`) ejercitan
  `ui._entrar`/`ui._salir`, no la posición.
- Fallo 3: sí existe (`_opacidad_no_borra_el_texto`), pero mide una pareja
  que no se pinta (ver C1).

El fallo que dejó la app sin puntuar en producción sigue sin cobertura; la
próxima regresión de ese camino volverá a pasar por 209 pruebas en verde.

---

## MENOR

### M1. Mensajes al usuario que todavía hablan de «código»

`app/cuentas.py:214` y `:234`: «El código de **{nombre}** ha agotado su cupo
de N usos». Es lo que verá un invitado con tope al agotarlo. Y
`app/cuentas.py:1`: el docstring del módulo sigue titulado «Codigos de
acceso». (En el Space no queda ningún rastro visible sin agotar un cupo:
`/config` e `innerText` dan 0 apariciones de «código», «XXXX», «canjea»,
«Activar».)

### M2. `entrega/mensaje_profesor.md` está desactualizado por el despliegue

`:21` enlaza `https://f01c1e0273b4839b46.gradio.live` (un túnel muerto; la
app vive en `mikemaki1763-literalevel.hf.space`); `:31` «Está corriendo desde
mi computadora, no está desplegado todavía»; `:38` «limitadas a 12 y 4 por
hora» (los topes hoy son por perfil, `LITERALEVEL_CUENTAS`, más los de
`app/ui.py:132-137`). La línea `:22` con usuario y contraseña sí es coherente
con el sistema nuevo. Si Miguel lo manda tal cual, el profesor pulsa un
enlace muerto.

### M3. `DESPLIEGUE.md` no documenta `LITERALEVEL_CUENTAS`, y `main.py:19`/`DESPLIEGUE.md:24` siguen diciendo «carpeta del modelo v4»

`grep -rn LITERALEVEL_CUENTAS` fuera de `auditoria/`: solo `app/cuentas.py`
y `pruebas_extremas.py`. El único secreto del Space que documenta
`DESPLIEGUE.md:26,66` es `OPENAI_API_KEY`. Y `LITERALEVEL_MODELO` ahora
acepta también un identificador del Hub —que es lo que usa el Space—, pero
las dos descripciones dicen «carpeta».

### M4. `_tabla` descarta en silencio y colapsa duplicados

`app/cuentas.py:86-96`: una entrada con `:` dentro de la contraseña
(`inv:a:b:c:3`) tiene cuatro trozos y se descarta sin aviso, así que ese
perfil «no existe» y nadie sabe por qué; y `miguel:x:0,Miguel:y:5` se reduce
a uno (`usuario.lower()`, gana el último) también sin aviso. Reproducido:
tabla con siete entradas declaradas → tres perfiles. No es un fallo de
seguridad, es un fallo de diagnóstico: el secreto se edita a ciegas en el
panel del Space.

### M5. La prueba de opacidad solo reconoce `opacity:.NN`

`pruebas_extremas.py:880`: `re.findall(r"opacity:(\.[0-9]+)", …)`. Un
`opacity:0.5`, `opacity: .5` u `opacity:1` no cuenta. Hoy todas las
declaraciones del CSS van en la forma `.NN` (`app/ui.py:371,764,1820,1822,
1920,1924,2004,2009,2010`; ninguna por debajo de `.78`), así que pasa, pero
pasa por convención de escritura y no por cobertura.

### M6. Comentario de JS desactualizado

`app/ui.py:819`: «En un movil la caja queda fuera de pantalla, **debajo del
lector**». Desde `02335ae` está encima. El `scrollIntoView` que sigue es
correcto y sigue haciendo falta (en un capítulo largo la caja queda ahora
*arriba*, a varias pantallas), pero el motivo escrito es el viejo.

---

## NOTAS (comprobado y sin acción obligada)

- **Tiempo constante en `verificar`.** Medido 20 000 iteraciones: usuario
  existente 5,00 µs, inexistente 5,12 µs. La cadena de relleno
  `no-existe-este-usuario` (22 caracteres, `app/cuentas.py:119`) tiene otra
  longitud que las claves reales, y `compare_digest` en CPython recorre la
  longitud del segundo argumento, así que hay una diferencia teórica de
  nanosegundos por carácter. Irrelevante a través de una red; el mensaje es el
  mismo para usuario y contraseña malos (`app/ui.py:223-224`), así que no se
  enumera por texto.
- **`_parece_repo_hf`** clasifica bien todo lo razonable: `./modelo_v4`,
  `modelo_v4`, `C:\x\modelo_v4`, `C:/x/modelo_v4`, `/home/u/modelo`,
  `~/modelo_v4`, `mis modelos/v4`, `../modelo_v4`, `owner/name/`, `""`,
  `" owner/name"` → carpeta (o error claro); `MikeMaki1763/literalevel-v4` y
  con mayúsculas → repo. Dos bordes asumidos y documentados en el propio
  docstring (`app/scoring.py:176-178`): una ruta relativa **inexistente** con
  una barra (`modelos/v4`) se toma por identificador y recibe el error de
  `from_pretrained`, no el amable; y `~` no se expande (ya era así antes). La
  primera condición (`app/scoring.py:182`) es redundante con las dos
  siguientes, no incorrecta.
- **`app/ui.py` tras mover el bloque:** `palabra`, `b_palabra`, `ficha`,
  `audio_web`, `audio_local`, `oracion`, `idioma` se definen en
  `:2345-2380`, antes de `texto` (`:2382`) y de todos los manejadores que los
  usan (`:2395-2396, 2428-2431, 2487-2488, 2497-2498`). `estado_codigo`,
  `caja_usuario`, `caja_clave`, `b_entrar`, `b_salir` solo se nombran dentro
  del `if cuentas.hay_codigos()` (`:2144-2168`). No hay componente huérfano
  ni referencia fuera de alcance: `construir()` se ejecuta en las pruebas y en
  el Space, y el `/config` vivo tiene los 152 componentes en el orden del
  código.

---

## OK — lo que está bien

**Parte B, cifras vivas (todas con salida 0):**

| Suite | Esperado | Obtenido |
|---|---|---|
| `pruebas_extremas.py` | 209 | «Las 209 pruebas extremas pasan» |
| `pruebas_integracion.py` | 27 | «Los 27 pasos del recorrido encadenan bien» |
| `pruebas_ficha.py` | pasa | «Todas las pruebas de la ficha pasan» |
| `pruebas_perfil.py` | pasa | «TODO OK: extremo fácil=0.000, extremo difícil=1.977» |
| `tests_smoke.py` | pasa | «TODO OK» |
| `validar_local.py` | 47 · A2 n=8 0,5561 · 0,860/0,807/0,668 · 0,732 · 31 | 47 textos · A2 n=8 media 0.5561 · 0.860 / 0.807 / 0.668 · 0.732 · 31 |
| `tools/contar_guion.py` | 561 | «PALABRAS HABLADAS: 561» |

**Parte C, la aplicación desplegada:**

- **Puntúa.** «Mi nivel → O pega un fragmento a mano», 268 palabras de
  *Pride and Prejudice*, «Medir con este texto» → «Tu nivel de lectura:
  **1.39 / 2.00** (intermedio) … Te buscaremos lecturas entre 1.29 y 1.54».
  El modelo se cargó desde el Hub en cpu-basic. El fallo 1 está cerrado
  donde importa.
- «Entrar con tu perfil» es el componente 4 del `/config`, `open=True`, antes
  de `Tabs` (15); en vivo, `.label-wrap.open` = true y el texto está en la
  posición 200 de 4518 caracteres.
- Login con clave mala → «**No he podido entrar.** Revisa el usuario y la
  contraseña…», sin decir si el usuario existe.
- «Leer»: `Consultar una palabra` (95) precede al lector (110); en el
  `innerText` vivo, 1595 < 2119 («Capítulo siguiente») < 2140 («Índice»).
- Cero apariciones de «código de acceso», «Código», «XXXX», «canjea»,
  «Activar», «tendencia» en `/config` y en el `innerText`; «nivel general»
  tampoco aparece porque la gráfica solo existe con un libro abierto.

**Parte D, entregables:** `documento.tex`, `presentacion.tex`,
`guion_video.tex`, `notebook_proyecto.{py,ipynb}`, `README.md`, `PENDIENTES.md`
no mencionan códigos de acceso ni la «tendencia» de la gráfica (la única
«tendencia» del cuaderno, `:603`, es la de Dale-Chall y es correcta). El
documento no incluye capturas (`documento.tex:8`), así que las cinco de
`capturas/` del 6 de septiembre, que muestran la interfaz vieja, no
contaminan la entrega. Lo desactualizado está en M2 y M3.

---

## Parte E — ¿queda algo que avergonzaría al autor si lo lee un profesor universitario, o si abre la aplicación delante de él?

**Sí.** Cuatro cosas, en este orden:

1. **Si el profesor abre el enlace en un portátil en modo claro, ve una
   página negra sin texto** (C1). No hay que buscarlo: es la primera
   pantalla. Y si el profesor está en modo oscuro y Miguel enseña «mira, hay
   paletas claras», la que elija se queda sin letras.
2. **La pestaña «Estado», la que existe para enseñar que todo está en su
   sitio, dice «Modelo v4: FALTA»** (S1) mientras el modelo acaba de puntuar.
3. **Teclear una contraseña con ñ devuelve «Error»** (S2), en una app en
   español cuyo campo se llama «Contraseña».
4. **Decir en el cierre que los tres fallos tienen ya una prueba** (S4)
   cuando el que dejó la app sin puntuar no la tiene. Un profesor que lea el
   cierre y luego `grep` la suite lo ve en un minuto.

Nada de esto lo delatan los documentos: los tres primeros solo se ven usando
la aplicación —en el otro modo de color, en la pestaña que nadie mira, con la
tecla que un español pulsa— que es, otra vez, lo que la skill nueva dice que
hay que hacer.
