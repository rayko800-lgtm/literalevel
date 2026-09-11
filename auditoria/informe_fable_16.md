# Auditoría externa Fable 16 — LiteraLevel

**Fecha:** 11 de septiembre de 2026 · **Alcance:** las cuatro pasadas del encargo
(recorrido de la demo ejecutándolo, cifras, mutantes, dinero y datos). Trabajo a
ciegas: no se abrió `auditoria/` salvo para escribir esto.

## Resumen (diez líneas)

1. Recorrí los cinco pasos del guion **contra el Space en vivo**
   (`mikemaki1763-literalevel.hf.space`) y ejecuté las nueve suites y 21 mutantes
   sobre una copia local del árbol.
2. El caso del guion cuadra en lo grande: nivel **1,20 / 2,00** (rango 0,95–1,45),
   búsqueda de *dostoyevski* mal escrito, ficha **203.699 palabras · 31 % diálogo**,
   curva **840 ventanas · media 1,70 · C1 · cap 19 = 1,52 / cap 36 = 1,87**. Todo
   coincide con `documento.md` §8.2 y con el guion.
3. **Pero al abrir el libro desde el buscador salta un recuadro rojo de `Error`**
   («Value: N is not in the list of choices: []»), de forma **determinista**, en
   pleno paso de la demo.
4. **La primera consulta léxica tarda ~55 s en frío** (carga del diccionario +
   spaCy + MiniLM); el guion dice «en 40 milisegundos» a cámara. Los 40 ms son
   solo en caliente.
5. La ficha da **dos tiempos de lectura distintos para el mismo libro y lector**
   (18 h 52 sin curva calculada, 30 h 52 con ella): se contradice a sí misma.
6. Dinero: los tres caminos a OpenAI pasan por la puerta de pago; **ninguno la
   esquiva**. Pero `_practicar` **cobra el cupo aunque no haya clave**, al revés
   que sus dos hermanos.
7. Mutantes: **5 de 21 sobrevivieron**. El más grave: un cambio que **filtra los
   nombres de usuario en la pestaña pública «Estado»** no lo caza ninguna prueba.
8. Y **el rescate por parecido del buscador** (el «dostoyevski mal escrito» del
   paso 2) **no lo cubre ninguna prueba**: se puede romper y la suite sigue verde.
9. Cifras verificadas contra el código y la BD: diccionario 1.487.639 filas,
   IPA 3,1 %, audio 0,5 %; aritmética del README (654, 53,47 %, 97,22 %); guion
   578 palabras = 3:51. Todo cuadra.
10. Divergencia PDF: `documento.md` §8.2 trae los números de capítulo
    (19/1,52, 36/1,87) que el `.pdf` **no** tiene: el `.md` se corrigió y el
    `.tex`/`.pdf` no.

**Recuento:** 0 críticos · 6 serios · 4 menores · 3 notas · **5 mutantes vivos**.

---

## Hallazgos

### SERIO 1 — Recuadro rojo de «Error» al abrir un libro desde el buscador
- **Ubicación:** `app/ui.py:3380-3382` (cableado del índice).
- **Cita:**
  ```
  est_libro.change(_indice_de, [est_libro, cap], indice)
  indice.select(lambda v: v, indice, cap)
  cap.change(lambda v: gr.update(value=v), cap, indice)
  ```
- **Qué falla y por qué:** al abrir un libro desde «Buscar → Leerlo ahora»,
  `_abrir_del_catalogo` cambia a la vez `est_libro` y `cap`. El listener
  `cap.change` fija el **valor** del `Radio` del índice (`gr.update(value=v)`)
  antes de que `est_libro.change(_indice_de, ...)` haya poblado sus **choices**,
  así que Gradio lanza el aviso rojo *«Value: 2 is not in the list of choices:
  []»* (o «Value: 1…»). Es una carrera entre dos listeners del mismo evento.
- **Cómo se reproduce (en vivo, determinista):** Buscar «dostoyevski» → seleccionar
  *Crime and Punishment* → «Leerlo ahora». Sale el toast rojo. Lo reproduje **dos
  veces de dos** (una con «Value: 1», otra con «Value: 2»). El libro se abre bien
  igualmente; el problema es que **en cámara aparece un recuadro rojo de Error**
  justo en el paso estrella (SATISFACCIÓN, minuto 1:05–3:35).
- **Cómo se arregla:** actualizar choices y value del índice en un **solo**
  manejador cuando cambia el libro (por ejemplo que `_indice_de` devuelva
  `gr.update(choices=…, value=actual)` colgado de `est_libro.change`, y que
  `cap.change` **no** toque el índice mientras las choices puedan estar vacías),
  o encadenar con `.then()` para forzar el orden choices→value. Para grabar hoy:
  abrir el libro **antes** de empezar a grabar ese tramo, o subirlo desde disco
  (el toast no sale por la subida directa).

### SERIO 2 — La primera consulta léxica tarda ~55 s, no «40 milisegundos»
- **Ubicación:** `app/ui.py:608` (`consultor()` perezoso) · `app/lexicon.py`
  (carga de diccionario + spaCy + MiniLM) · guion paso 4 · `documento.md` §8.2.
- **Cita (guion):** «Toco una palabra y en **40 milisegundos** tengo el diccionario
  y la fonética».
- **Qué falla y por qué:** los 40 ms son **en caliente** (lo dice `AGENTS.md`:
  «el trabajo local … son 40 ms **en caliente**»). La **primera** consulta de la
  sesión carga el SQLite de 243 MB + spaCy + MiniLM. Medido en vivo:
  «clerks» tardó **~55 s** desde el clic hasta la ficha (11:40:01 → 11:40:57); la
  segunda palabra («preponderance») bajó a **~11 s**. El guion no dice a cámara que
  hay que precalentar.
- **Cómo se reproduce:** sesión nueva, ir directo a consultar una palabra sin
  haber consultado ninguna antes en ese proceso.
- **Cómo se arregla (día de grabación):** **consultar una palabra cualquiera antes
  de grabar** para que el consultor quede caliente; entonces la del guion sale en
  ~1 s. No cambiar la carga a anticipada (AGENTS lo prohíbe con razón).

### SERIO 3 — La ficha da dos tiempos de lectura distintos para el mismo libro y lector
- **Ubicación:** `app/ui.py:1787-1817` (`_ficha_libro`) · `app/ficha.py:31-32`
  (`PPM_COMODO=180`, `PPM_EXIGENTE=110`).
- **Qué falla y por qué:** `_ficha_libro` decide `exigente = nivel_libro > p.nivel
  + 0.15`, pero `nivel_libro` sale de `_analisis_guardado(libro)`: **si aún no se
  ha calculado la curva, es `None`** y `exigente=False`, así que muestra el ritmo
  cómodo (180 ppm). Medido en vivo sobre *Crime and Punishment* con perfil 1,20:
  - primera apertura (sin curva en caché): **«18 h 52 min a tu ritmo de lectura»**
  - reapertura (con la curva ya calculada, 1,70): **«30 h 52 min (va por encima de
    tu nivel)»**
  Son 12 horas de diferencia (64 %) para el mismo libro y lector, y el primer
  texto **etiqueta como “a tu ritmo” el ritmo que corresponde a leer por debajo
  del nivel**. `documento.md` §8.2 promete el ritmo según nivel sin condiciones.
- **Cómo se reproduce:** abrir un libro que no tenga análisis guardado con un
  perfil por debajo del nivel del libro → 18 h 52; calcular la curva y reabrir →
  30 h 52.
- **Cómo se arregla:** cuando no hay análisis, mostrar el **rango** (como hace la
  rama `p is None`: «entre 18 h 52 y 30 h 52») en vez de comprometerse con el
  ritmo cómodo; o recalcular la ficha al terminar el análisis. Para grabar:
  **precalcular la curva del libro antes** (el paso 4 la deja en caché y a partir
  de ahí la ficha dice 30 h 52).

### SERIO 4 — `_practicar` cobra el cupo aunque no haya clave de OpenAI
- **Ubicación:** `app/ui.py:2728-2755` (`_practicar`), frente a
  `app/ui.py:2536-2555` (`_consultar`) y `app/ui.py:1893-1900` (`_de_que_trata`).
- **Cita (`_practicar`):**
  ```
  va_a_costar = (not config.falta() and cuentas.permite(...)[0])
  if va_a_costar and not _dentro_del_limite(peticion, "voz", LIMITE_VOZ_HORA): ...
  puede, motivo_pago = _puede_pagar(peticion)      # <-- sin guardia config.falta()
  ```
- **Qué falla y por qué:** `_consultar` y `_de_que_trata` llaman a `_puede_pagar`
  **solo si `not config.falta()`** (con clave); si no hay clave, no cobran, porque
  no puede haber llamada. `_practicar` llama a `_puede_pagar` **incondicionalmente**
  y en la rama sin transcripción decide adrede no devolver el uso. Resultado: en un
  despliegue **con perfiles pero sin `OPENAI_API_KEY`** (clave caducada/borrada,
  que ya ha pasado en este proyecto), **cada intento de pronunciación descuenta un
  uso del cupo sin que salga una sola petición a la red**. Es exactamente el fallo
  que ya se corrigió en `_consultar` («con la clave caducada CADA consulta
  descontaba un uso») y que aquí quedó sin corregir.
- **Cómo se reproduce:** perfiles declarados en `LITERALEVEL_CUENTAS`, sin
  `OPENAI_API_KEY`, entrar con un perfil de tope > 0 y pulsar «practicar» con un
  audio → el contador de `uso_openai.json` sube sin gasto.
- **Cómo se arregla:** anteponer la misma guardia que los otros dos:
  `if config.falta(): puede, motivo_pago = False, ""` antes de `_puede_pagar`, o
  devolver el uso cuando `voz.practicar` no encontró cliente.
- **Respuesta a las cuatro preguntas de la pasada 4:** ¿se cobra el cupo cuando no
  se gasta? **Sí, en `_practicar` sin clave** (los otros dos caminos lo hacen bien
  y devuelven el uso). ¿Se deja de cobrar cuando sí se gasta? No se detectó ese
  caso. ¿Puede un visitante ver/gastar lo de otro? No: el código de sesión va por
  identidad de navegador (`_codigo_de`) y el cupo se cuenta por `cuenta.nombre`.
  ¿Hay un camino a OpenAI que no pase por la puerta? **No**: los tres únicos sitios
  (`consultor().consultar` en `_consultar`, `voz.practicar` en `_practicar`,
  `ficha.sinopsis`/`_cliente()` en `_de_que_trata`) pasan por
  `_puede_pagar`/`cuentas.consumir`.

### SERIO 5 — La pestaña pública «Estado» puede filtrar nombres de usuario (mutante M04 vivo)
- **Ubicación:** `app/cuentas.py:150-159` (`problemas()`), prueba
  `pruebas_extremas.py:2282` («el diagnostico avisa de un perfil repetido»).
- **Qué falla y por qué:** `problemas()` llama a `_analizar(..., con_nombre=False)`
  a propósito, para que la pestaña pública no revele qué usuarios existen. El
  mutante **M04** lo cambia a `con_nombre=True` y **ningún test falla**: la prueba
  comprueba que no se filtra la **contraseña** (`"x" not in [a.split()[-1] …]`)
  pero **no** que falte el **usuario**. Es un agujero real: si alguien invierte
  ese flag, los nombres de usuario configurados salen en «Estado», que es pública,
  y le ahorra medio trabajo a quien prueba contraseñas.
- **Cómo se reproduce:** ejecutar el mutante M04 (abajo) — la suite pasa entera.
- **Cómo se arregla:** añadir a la prueba un aserto de que el nombre de usuario
  **no** aparece en `problemas()` (p. ej. `assert "ana" not in texto`).

### SERIO 6 — El buscador (rescate por parecido y umbral) no lo cubre ninguna prueba (mutantes M16 y M17 vivos)
- **Ubicación:** `app/catalogo.py:114` (`_PARECIDO_NOMBRE = 0.75`),
  `app/catalogo.py:227` (`minimo_similitud = 0.10`) y el bucle de `buscar`.
- **Qué falla y por qué:** el rescate ortográfico que hace que «dostoyevski» mal
  escrito encuentre a Dostoyevsky —el **paso 2 de la demo** y `documento.md`
  §8.2— **no lo prueba nadie**. El mutante **M16** sube `_PARECIDO_NOMBRE` a 0.99
  (desactiva el rescate) y sobrevive; el **M17** baja `minimo_similitud` a 0.0 (no
  descarta nunca resultados flojos ni muestra «Ningún libro supera el umbral») y
  también sobrevive. No hay ninguna prueba que llame a `catalogo.buscar` con un
  nombre mal escrito o con una consulta sin resultados.
- **Cómo se reproduce:** ejecutar M16/M17 — la suite pasa entera. Y, en vivo, si se
  rompiera el rescate, el paso 2 del guion dejaría de ser cierto delante de cámara.
- **Cómo se arregla:** una prueba de integración del buscador: «chejov» / «dostoyevski»
  devuelven al autor correcto; una consulta absurda devuelve el aviso «Ningún libro
  supera el umbral».

### MENOR 1 — `documento.pdf` no trae los números de capítulo de §8.2 que sí tienen el `.md` y la app
- **Ubicación:** `documento.md:972` vs `documento.tex:2230` y `documento.pdf`.
- **Cita (`documento.md`):** «su capítulo más llevadero (**el 19, 1,52**) y su
  capítulo más exigente (**el 36, 1,87**)». En el `.tex`/`.pdf`: «su capítulo más
  llevadero y su capítulo más exigente» **sin números**.
- **Qué falla y por qué:** la app muestra exactamente 19/1,52 y 36/1,87 (verificado
  en vivo), y el `.md` también, pero el PDF entregable se quedó con la versión
  vaga. Es el patrón «`.md` corregido, `.tex` sin corregir» que ya ha pasado. No es
  una cifra falsa, es una corrección no propagada. `1,52` aparece 1 vez en el `.md`
  y **0** en el `.tex`/`.pdf`.
- **Cómo se arregla:** propagar la frase al `.tex` y recompilar, o dejar el `.md`
  igual de vago que el PDF si no da tiempo. (El PDF no es incorrecto, solo menos
  específico que la app.)

### MENOR 2 — La palabra del guion, «clerk», muestra una acepción equivocada y marcada «dudosa»
- **Ubicación:** desambiguación de `lexicon._elegir_sentido`, observado en vivo.
- **Qué falla y por qué:** «clerk(s)» en la frase de *Crime and Punishment* («petty
  clerks») devuelve la acepción **«In the Church of England, the layman that
  assists…» (archaic), afinidad 0,18**, con el aviso «La acepción elegida es
  dudosa». La IPA UK/US sale bien (`/klɑːk/` · `/klɝk/`), que es lo que el guion
  quiere enseñar, pero **la definición del diccionario es la equivocada** y, sin
  perfil, no hay explicación de OpenAI que la corrija. En cámara se ve el
  diccionario dando una acepción errónea que la propia app marca como dudosa.
- **Cómo se reproduce:** consultar «clerk» en el capítulo I sin haber entrado con
  perfil.
- **Cómo se arregla (día de grabación):** entrar con perfil para que la explicación
  contextual de OpenAI acompañe (y desmienta) la glosa, o elegir para el paso 4 una
  palabra cuya acepción salga limpia (afinidad alta, sin aviso «dudosa»). La IPA de
  «clerk» sí luce el contraste UK/US que pide el guion.

### MENOR 3 — El separador de miles español no lo fija ninguna prueba (mutante M19 vivo)
- **Ubicación:** `app/ficha.py:119` (`miles`).
- **Qué falla y por qué:** `miles()` convierte a «1.197» (punto español). El mutante
  **M19** lo devuelve a `format(int(n), ",")` («1,197») y **ninguna prueba falla**,
  aunque la app enseña «203.699», «840» y «1.197» por todas partes (y el propio
  comentario del código advierte del fallo histórico «1,197 no 1.197»).
- **Cómo se arregla:** un aserto `ficha.miles(1197) == "1.197"`.

### MENOR 4 — El tope de muestra de 60.000 palabras de la ficha no lo fija ninguna prueba (mutante M15 vivo)
- **Ubicación:** `app/ficha.py:249` (`_muestra(..., tope_palabras=60000)`),
  `documento.md`/`.tex` §8.2 («tope de 60.000 palabras»).
- **Qué falla y por qué:** el mutante **M15** baja el tope a 6.000 y sobrevive.
  Las cifras demostradas de la ficha (diálogo 31 %, frase 15, riqueza 18,5) se
  calculan sobre esa muestra; nada asegura que el tamaño documentado se mantenga.
- **Cómo se arregla:** una prueba que fije el tope o compruebe estabilidad de las
  cifras de la ficha.

### NOTA 1 — «134 segundos» de la curva no es verificable en vivo
El Space sirve el análisis **desde caché** (`/data` persistente): el «Leer el libro
entero» devolvió en ~6 s, no en 134 s. Bien para la demo (sale al instante), pero
la cifra «840 ventanas en 134 segundos» es un análisis previo, no algo que ocurra
a cámara. **Riesgo:** si el disco `/data` se reinicia/limpia, la primera medición
en vivo sí tardaría ~134 s de silencio. Asegurar que la curva de *Crime and
Punishment* está en caché antes de grabar (lo está tras ejecutar el paso 4).

### NOTA 2 — El libro del guion sale en 4.º lugar y las etiquetas son heredadas
«dostoyevski» devuelve *The Idiot*, *The Brothers Karamazov*, *Notes from the
Underground* y luego *Crime and Punishment* (4.º), más 4 de StoryWeaver sin
descarga. Hay que seleccionarlo en la lista (funciona). Las letras al lado (B2/C1)
son **heredadas del catálogo**; el propio guion avisa de no pulsar «Sorpréndeme» y
de que la letra puede contradecir al modelo. El buscador (paso 2) no tiene ese
problema; se confirma que el rótulo «etiqueta heredada, sin medir con el modelo»
está a la vista.

### NOTA 3 — El Space puede ir por detrás de la auditoría 15
`PENDIENTES.md` dice que las correcciones de la auditoría 15 (`ui.py`, `lexicon.py`,
`ficha.py`, `cuentas.py`) **están sin volver a subir**. Las pruebas de navegador de
este informe son contra el Space; los mutantes, contra el código **local**. Si se
redespliega antes de grabar, conviene rehacer el paso 1 contra el Space nuevo (el
recuadro rojo del SERIO 1 y el frío del SERIO 2 son de código, así que seguirán).

---

## Tabla de mutantes

Control: **las 9 suites pasan sin mutar** (`tests_smoke`, `pruebas_ficha`,
`pruebas_perfil`, `pruebas_voz`, `pruebas_audio_atomico`, `pruebas_desambiguacion`,
`pruebas_lexicon`, `pruebas_integracion`, `pruebas_extremas` — 296 extremas, 27
integración). Copia del árbol en `scratchpad/f16_arbol/`, con
`LITERALEVEL_MODELO`/`LITERALEVEL_DICCIONARIO` exportados y sin `OPENAI_API_KEY`.

> **Aviso metodológico:** `pruebas_voz.py` usa una ruta de temp **fija**
> (`literalevel_voz_prueba.db`) que ignora `LITERALEVEL_DATOS`; al correr dos
> mutantes en paralelo choca y da `PermissionError` (rc=1) **espurio**. Solo afecta
> a `pruebas_voz` (las demás usan uuid/TemporaryDirectory), y solo prueba `voz.py`,
> así que no oculta ninguna caza real: los mutantes marcados «vivo» tienen las
> **9** suites en verde. (Es en sí un fallo menor de la suite de voz.)

| Mutante | Qué rompe | Prueba que debía cazarlo | ¿Vivió? |
|---|---|---|---|
| M01-cupo-mas-uno | `cuentas.consumir`: `total > tope` → `> tope+1` | «el cupo se agota y no revive» / «no se cobra lo que no se gasta» | muerto |
| M02-devolver-nunca | `cuentas.devolver`: no resta nunca | «el resumen devuelve el uso…» / «no se cobra lo que no se gasta» | muerto |
| M03-usuario-mayusculas | `verificar`: usuario sensible a mayúsculas | «el usuario no distingue mayusculas y la clave si» | muerto |
| **M04-estado-con-nombres** | `problemas()` con `con_nombre=True` (filtra usuarios en «Estado») | «el diagnostico avisa de un perfil repetido» (no lo asevera) | **VIVO** |
| M05-intentos-16 | freno de intentos `>= tope` → `> tope` | «la puerta de entrada tiene freno» | muerto |
| M06-cefr-redondeo-par | `_cefr` con `round()` (redondeo al par) | «la tabla que ve el lector es la del codigo» | muerto |
| M07-sesion-pago-compartida | `_sesion_de` → `"local"` (cupo/sesión compartidos) | «la sesion de pago es de cada visitante» | muerto |
| M08-id-navegador-sin-sanear | `_registrar_lector` sin sanear el id | «sin localStorage no revienta» | muerto |
| M09-sinopsis-cobra-sin-red | `_de_que_trata` no devuelve el uso sin red | «el resumen devuelve el uso cuando no sale a la red» | muerto |
| M10-pago-por-intencion | `lexicon` cuenta la intención, no el gasto | pruebas_lexicon: «una llamada que fallo cobro 2 usos» | muerto |
| M11-audio-sin-normalizar | clave de audio sin normalizar (Fetters/fetters.) | pruebas_lexicon: «las variantes… pagan de nuevo» | muerto |
| M12-escala-publica-0.5 | `public_score` ×0,5 en vez de ×0,4 | «la interfaz y el contrato dan la misma letra» | muerto |
| M13-peso-fragmentos | `PESO_FRAGMENTOS` 0,65 → 0,5 | pruebas_perfil + «cada respuesta va a su pregunta» | muerto |
| M14-ritmo-exigente | `PPM_EXIGENTE` 110 → 180 | pruebas_ficha: «mas comodo tarda menos que mas exigente» | muerto |
| **M15-muestra-6000** | tope de muestra de ficha 60.000 → 6.000 | (ninguna) | **VIVO** |
| **M16-sin-rescate-nombre** | `_PARECIDO_NOMBRE` 0,75 → 0,99 (mata el rescate ortográfico) | (ninguna) | **VIVO** |
| **M17-umbral-parecido-0** | `minimo_similitud` 0,10 → 0,0 (no descarta flojos) | (ninguna) | **VIVO** |
| M18-maquetado-nunca | `PESO_MAQUETADO` 0,175 → 1,0 (no rechaza listas) | «el filtro sigue rechazando menus, indices y tablas» | muerto |
| **M19-miles-con-coma** | `miles()` con coma («1,197») | (ninguna) | **VIVO** |
| M20-rechazo-sigue-sumando | `consumir` no resta el incremento rechazado | «no se cobra lo que no se gasta» | muerto |
| M21-voz-sin-plazo | cliente de `voz` sin `timeout`/`max_retries` | «los clientes de OpenAI tienen plazo» | muerto |

**Vivos: 5 de 21** — M04 (dinero/datos: filtra usuarios), M16 + M17 (el buscador
del paso 2 y su umbral, sin red de pruebas), M15 y M19 (constantes de la ficha).

---

## Lo que comprobé y estaba bien

- **Recorrido del guion, en vivo:** nivel **1,20 / 2,00**, rango recomendado
  **0,95–1,45** (paso 1). Búsqueda «dostoyevski» mal escrito → devuelve a
  Dostoyevsky (paso 2). Ficha **203.699 palabras · 42 capítulos · 31 % diálogo ·
  15 palabras/frase · riqueza 18,5 · «raskolnikov, sonia…»** (paso 3). Curva
  **840 ventanas · media 1,70 / 2,00 · orientativo C1 · cap 19 = 1,52 · cap 36 =
  1,87 · recorrido 1,52–1,87** (paso 4). Todo coincide con `documento.md` §8.2 y el
  guion. La consulta léxica muestra IPA UK/US, diccionario Wiktionary y, sin perfil,
  el aviso correcto «entres con tu perfil».
- **Tiempos medidos (Space caliente):** nivel ~11 s (frío de sesión), búsqueda ~2 s,
  abrir libro ~3 s (cacheado), curva ~6 s (cacheada), 2.ª consulta léxica ~11 s.
  (Los que preocupan están en los SERIO 1–3.)
- **Cifras contra el código/BD:** diccionario **1.487.639 filas** exactas; **IPA
  46.794 (3,1 %)**, **audio 7.003 (0,5 %)**, **ambas IPA 33.635 (2,3 %)** — cuadran
  al dígito con §6.4. `public_score(y)=clip(y,0,5)*0,4` (contrato). Escala interna
  0..5 no se filtra a la interfaz.
- **README:** aritmética 510+144=654, 77/144=53,47 %, 140/144=97,22 % correcta;
  la propia tabla ya avisa de que 0,908 y 97,2 % **no** son verificables desde el
  repo (corpus no incluido) — honesto.
- **Guion:** `tools/contar_guion.py` reproduce **578 palabras = 3:51**; el `.md` y
  el `.pdf` del guion coinciden (0 cifras divergentes). El `.pdf` del documento
  coincide con el `.md` salvo la NOTA/MENOR 1. La presentación PDF trae 0,908,
  distilroberta, 61.642, 203.699, 1,70.
- **Degradación sin clave:** con `OPENAI_API_KEY` vacía, diccionario, IPA, buscador,
  ficha, curva y cuestionario funcionan; lo que se apaga se anuncia bien.
- **Dinero:** los tres caminos pasan por `_puede_pagar`/`cuentas.consumir` (atómico
  bajo candado); refutados los intentos de burlar el cupo (M01, M07, M09, M10, M11,
  M20 muertos); no hay camino a OpenAI fuera de la puerta. La única grieta es el
  SERIO 4 (`_practicar` sin clave).
- **Arranque:** `python -X utf8 app/ui.py` (el de `CLAUDE.md`) tiene su bloque
  `__main__` y arranca; el import de `ui` no carga los recursos pesados.

---

## Si mañana esto se graba tal cual, ¿qué va a salir mal?

Tres cosas, por orden de probabilidad de aparecer en cámara:

1. **El recuadro rojo de «Error» al abrir el libro (SERIO 1).** Es determinista y
   cae en el paso más importante. **Antídoto de un día:** abrir el libro **antes**
   de empezar a grabar ese tramo (o subirlo desde disco, que no dispara el toast).
   El arreglo de código es de una línea, pero para hoy basta con el orden.
2. **El silencio de ~55 s en la primera consulta léxica (SERIO 2).** Se dice «40
   milisegundos» y la primera vez no lo es. **Antídoto:** consultar una palabra
   cualquiera antes de grabar para dejar el consultor caliente.
3. **Que la palabra «clerk» salga con acepción equivocada y aviso «dudosa» (MENOR
   2), y que la ficha diga «18 h 52 a tu ritmo» si no se ha precalculado la curva
   (SERIO 3).** **Antídoto:** entrar con perfil para el paso 4 (o cambiar la palabra
   por una limpia), y precalcular la curva del libro antes de grabar (eso también
   deja la ficha en 30 h 52 y la curva instantánea).

Todo lo demás del recorrido —nivel, búsqueda, cifras de la ficha y de la curva—
coincide con el documento y el guion y aguanta la cámara. Lo que **no** hay que
enseñar: el botón «Sorpréndeme» (el guion ya lo dice) y cualquier consulta léxica
o curva **sin precalentar**.
