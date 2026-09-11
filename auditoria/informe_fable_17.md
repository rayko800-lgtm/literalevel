# Informe Fable 17 — regresión sobre `git diff b6a7c21..HEAD`

Auditor externo, a ciegas (sin leer `auditoria/`). Pregunta única: **¿qué se ha roto
con estos cambios?** Fecha: 11 de septiembre de 2026. Gradio 6.26.0 en local y
fijado exacto en `requirements.txt` para el Space, así que lo que se ve en local
vale para el Space —y lo importante lo reproduje además en el Space—.

## Resumen en diez líneas

1. Los cinco cambios de `app/ui.py` **no rompen nada que antes funcionara**: navegar
   por capítulos con los cuatro botones, el desplegable y el índice; subir un .txt de
   un capítulo y un .epub de 366; recargar con libro abierto; dos pestañas del mismo
   navegador. En todos los casos desplegable, índice y texto dicen lo mismo.
2. Pero **el recuadro rojo del paso estrella sigue ahí**: leyendo el capítulo 90 de
   *Karamázov* y abriendo *Notes from the Underground* (24 capítulos) desde el buscador
   sale «Value: 89 is not in the list of choices: [0…23]». Reproducido en local y **en el
   Space desplegado**. El libro se abre bien; el aviso rojo sale igual.
3. La causa no es la que dice el commit. Es `est_libro.change(_indice_de, [est_libro, cap], …)`
   (`ui.py:3433`, línea NO tocada): en los manejadores generadores lee el valor **viejo**
   del desplegable antes de que el navegador aplique el nuevo, y `Dropdown.preprocess`
   lo rechaza **antes** de que `_indice_de` pueda validarlo. La prueba nueva no lo ve.
4. «Retomar donde lo dejé» (`_seguir_leyendo`) conserva el `vacio` que se quitó del
   descargador y pinta el recuadro rojo **siempre** que ya hay un libro abierto. También
   reproducido en el Space.
5. «Leerlo ahora» sin elegir libro sigue borrando el lector (texto, ficha, índice y
   estado) pero ahora deja el desplegable lleno: mandos muertos. El comentario del diff
   dice que eso quedó arreglado, y no.
6. Los 11 mutantes F16 del banco los caza su prueba. De 8 mutantes míos, 4 vivieron:
   la prueba del índice acepta un valor de respaldo `0`, no compara etiquetas entre los
   dos mandos, no ve un `yield` final con el desplegable vacío, ni el rango invertido.
7. La ficha con perfil y sin curva da el rango (prueba y código); el corte sin clave de
   `_practicar` está y cobra solo con clave (prueba y mutante).
8. Un arreglo de **una línea** (quitar `cap` de las entradas de `est_libro.change`) más
   el `sin_tocar` en `_seguir_leyendo` elimina los dos recuadros: lo verifiqué en una copia
   parcheada, con recarga incluida.
9. Incidente propio: `config.cargar()` lee `CLAVES.txt` de la raíz, así que la app local
   **sí** tenía clave y mi clic en «Corrígeme» costó una ronda whisper+gpt+tts (< 1 cent.).
10. **Se puede grabar mañana** con una precaución de marcapáginas; con el arreglo, sin ella.

---

## Hallazgos

### H1 · CRÍTICO — El recuadro rojo del paso estrella sigue saliendo (Space incluido)

**Dónde:** `app/ui.py:3433`
```python
                est_libro.change(_indice_de, [est_libro, cap], indice)
```
y el cambio que pretendía cerrarlo, `app/ui.py:983-984`:
```python
    sin_tocar = gr.update()
    quieto = (None, sin_tocar, _html_lectura(""), gr.update(), gr.Tabs())
```

**Qué falla.** Con un libro abierto en un capítulo cuyo índice es **mayor o igual que el
número de capítulos del libro que se abre**, «Leerlo ahora» pinta el Error rojo de Gradio.
Reproducido dos de dos en local y una de una en `https://mikemaki1763-literalevel.hf.space`:
`Error × Value: 89 is not in the list of choices: [0, 1, 2, …, 23]`. Captura en
`scratchpad/f17_captura_space_error.png`; traceback del servidor en
`scratchpad/f17_app_local.log` (líneas 4-28).

**Por qué.** `_abrir_del_catalogo` es generadora. Su último `yield` cambia `est_libro` y
`cap` a la vez. Con la traza de red del navegador (`/gradio_api/queue/join`) se ve que el
manejador `fn_index=22` —`est_libro.change → _indice_de`, entradas `[est_libro, cap]`—
recibe **`[null, 89]`**, el valor viejo del desplegable, mientras que en el servidor la
copia de sesión de `cap` ya tiene las 24 opciones nuevas. `gradio/components/dropdown.py:210-213`
rechaza el valor en `preprocess` (`raise Error(f"Value: {payload} is not in the list of
choices…")`) **antes de llamar a `_indice_de`**, así que la validación nueva de
`_indice_de` (`ui.py:1465-1469`) nunca llega a ejecutarse. El mismo manejador, en la
subida de archivo (`_abrir`, que no es generadora), recibe `[null, 0]`: el valor nuevo.
El valor rancio solo se lee en los dos caminos generadores: el descargador y «Retomar».

El arreglo del diff (no vaciar el desplegable en el primer `yield`) sí cierra el caso en
que el capítulo viejo existe en el libro nuevo —por eso el autor lo vio desaparecer con
marcapáginas en el capítulo 2—, pero no el caso general.

**Cómo se reproduce** (local o Space): Buscar «dostoyevski» → *The Brothers Karamazov* →
«Leerlo ahora» → Índice del libro → capítulo 90 → Buscar lectura → *Notes from the
Underground* → «Leerlo ahora». Sale el recuadro rojo; el libro se abre en el capítulo 3.

**Riesgo para el vídeo.** *Crime and Punishment* tiene **42** capítulos en el lector. Si el
marcapáginas del navegador con el que se graba está en un capítulo ≥ 43 de cualquier
libro (*Karamázov* tiene 98, *Guerra y paz* 366), el paso Tres del guion sale con el
Error encima. Si el marcapáginas está en el propio *Crime and Punishment* o en un
capítulo bajo, no sale. El marcapáginas local de esta máquina está en *Notes from a Dead
House*, capítulo 6: en local no saldría; en el Space depende del navegador que se use.

**Cómo se arregla** (verificado en `scratchpad/f17_arbol/fix_est_libro/`, puerto 7862,
cero avisos en los dos escenarios y con recarga): quitar `cap` de las entradas de ese
manejador o quitar la línea entera —`cap.change(_indice_de, [est_libro, cap], indice)`
(`ui.py:3449`) ya repinta el índice cada vez que se abre un libro, porque abrir un libro
siempre asigna `cap`—. En la copia parcheada quité la línea y el índice sigue
apareciendo al abrir desde el buscador, al subir archivo y al recargar (`_reanudar`).

**Prueba que debería cazarlo y no lo caza.** «abrir un libro no pinta un error rojo»
comprueba la salida de `_indice_de` y busca cadenas en el fuente; el error lo lanza
Gradio antes de la función. Mi mutante X6 (quitar la línea 3433, que es el arreglo)
vive: ninguna prueba mira ese cableado.

### H2 · SERIO — «Retomar donde lo dejé» pinta el recuadro rojo siempre que hay libro abierto

**Dónde:** `app/ui.py:3025-3031`
```python
    vacio = gr.update(choices=[], value=None)
    ...
    yield (None, vacio, _html_lectura(""), gr.update(), gr.Tabs(),
           "Abriendo…")
```

**Qué falla.** Es exactamente el mecanismo que el commit b019c25 aisló en el descargador
(«vaciar el desplegable mientras trabaja»), en el otro camino generador que abre libros,
y ahí no se tocó. Con un libro abierto —y lo hay siempre que `_reanudar` haya cargado el
marcapáginas— pulsar «Retomar donde lo dejé» en «Mis libros» da
`Error × Value: 2 is not in the list of choices: []`. Reproducido en local y en el Space
(traceback en `scratchpad/f17_app_local.log:29-53`). El libro se retoma bien.

**Cómo se reproduce:** con *Notes from the Underground* abierto → Mis libros → Ver mis
libros → elegir *Karamázov* → Retomar donde lo dejé.

**Cómo se arregla:** el mismo `sin_tocar = gr.update()` en lugar de `vacio` en el `yield`
de «Abriendo…» (verificado en la copia parcheada: sin aviso). Con el arreglo de H1
aplicado el error deja de salir aunque este `vacio` se quede, pero el `vacio` sigue
estando mal por lo mismo que dice el comentario de `ui.py:975-982`.

No está en el guion del vídeo, así que no afecta a la grabación.

### H3 · SERIO — «Leerlo ahora» sin elegir sigue borrando el lector, y ahora deja el desplegable lleno

**Dónde:** `app/ui.py:984-987`
```python
    quieto = (None, sin_tocar, _html_lectura(""), gr.update(), gr.Tabs())
    if not id_libro:
        yield quieto[:3] + ("Elige un libro de la lista.", gr.Tabs(),
                            "Elige un libro de la lista.")
```
El comentario de encima dice: «pulsar «Leerlo ahora» sin elegir nada te borraba el
indice del libro que estabas leyendo». Sigue borrándolo.

**Qué falla.** `quieto[0]` es `None` para `est_libro` y `quieto[2]` vacía el texto. Al
poner `est_libro` a `None` dispara `est_libro.change` → `_indice_de(None, …)` vacía el
índice, `_ficha_libro(None)` borra la ficha y la sinopsis. Medido en local con *Karamázov*
en el capítulo 30: tras el clic, el texto dice «Abre un libro y elige un capitulo.», la
ficha desaparece, el índice tiene 0 opciones, la cabecera sigue diciendo «seguías en el
capítulo 30 de 98» y el desplegable sigue mostrando «30. Chapter V…» con 98 opciones.
Elegir otro capítulo o pulsar «Siguiente ›» no hace nada: `_mover(None, …)` y
`_capitulo(None, …)` devuelven vacío. Es el estado «el desplegable y el índice dejan de
decir lo mismo» que pedías buscar. Los mismos `quieto[:3]` se emiten si salta el tope de
descargas (`ui.py:1000`) o si Gutenberg falla (`ui.py:1016`): un fallo de red en mitad de
la demo deja el lector muerto con el desplegable vivo.

Antes del diff también se borraba todo, pero de forma coherente (desplegable vacío).

**Cómo se arregla:** en esos tres `yield` tempranos no tocar el lector: `gr.skip()` para
`est_libro`, `cap` y `texto` (`gradio/helpers.py:1135`: `gr.skip()` deja el componente
como está; comprobar en una copia que el `gr.State` también lo respeta dentro de una
generadora, que yo no lo probé), y solo el último `yield` cambia de libro. Lo mismo en
`_seguir_leyendo` (`ui.py:3027-3031`).

### H4 · MENOR — Lo que la prueba nueva no distingue (cuatro mutantes vivos)

Prueba «abrir un libro no pinta un error rojo» (`pruebas_extremas.py`, bloque «Lo que
encontro la auditoria 16») y «la ficha no promete un ritmo que no sabe».

| Mutante | Cambio | Resultado | Qué significa |
|---|---|---|---|
| X1-indice-cero | `value=int(actual) if valido else 0` (`ui.py:1469`) | **VIVO** | La comprobación `val is None or val in indices` acepta cualquier respaldo dentro de rango. Con `0`, un valor rancio marcaría el capítulo 1 en el índice y, si viene de `indice.select`, saltaría al capítulo 1. |
| X3-opciones-dos-sitios | `_abrir` vuelve a construir sus etiquetas sin recuento (`ui.py:1394`) | **VIVO** | Nada compara las etiquetas del desplegable con las del índice. «Dos mandos del mismo estado» es una promesa del comentario, no de una prueba. |
| X4-catalogo-final-vacio | último `yield` de `_abrir_del_catalogo` con `vacio` en vez de `upd` (`ui.py:1022`) | **VIVO** | El paso estrella abriría el libro **sin desplegable ni índice** y las siete suites siguen en verde. `pruebas_integracion.py` no pasa por `_abrir_del_catalogo`. |
| X7-ficha-rango-invertido | «entre 53 h y 32 h» (`ui.py:1852-1853`) | **VIVO** | La prueba solo exige «entre» y « y ». |

La parte 5 de esa prueba es un `grep` del fuente: caza los mutantes del banco porque
buscan exactamente esas líneas, pero no prueba comportamiento (cualquier reescritura
equivalente la rompe, y cualquier cableado nuevo con `cap` de entrada —como el de H1—
la pasa).

### H5 · NOTA — La premisa «sin `OPENAI_API_KEY` en local» no se cumple con `CLAVES.txt` en la raíz

`app/config.py:40-56` (`cargar`) vuelca `CLAVES.txt` en `os.environ` en cada `falta()`, y
`RUTAS_ENV` incluye la raíz del repositorio, donde hay un `CLAVES.txt` de 591 bytes. Así
que `python -X utf8 app/ui.py` en esta máquina **tiene clave** aunque el entorno no la
tenga. Consecuencia para esta auditoría: al probar el camino de `_practicar` «sin clave»
desde la interfaz, la app tenía clave y **se hizo una ronda de pago** (whisper-1 sobre
1 s de silencio + una explicación de gpt + un tts-1 de «the quiet harbour»; el mp3 está
en `scratchpad/f17_datos/audio/`). Coste estimado por debajo de un céntimo; lo apunto
porque la regla era no gastar. El corte sin clave de `_practicar` (`ui.py:2799-2803`) lo
verifico por la prueba «la practica de voz no cobra sin clave» y por dos mutantes
(F16-voz-sin-clave y X5, ambos cazados), no por la interfaz. Sugerencia: una variable
para ignorar los archivos de claves (`LITERALEVEL_SIN_CLAVES=1`) para poder ensayar el
modo degradado sin borrar el archivo.

### H6 · NOTA — Pluralización en la cabecera (previo al diff)

`app/ui.py:1417`: `f"{len(libro.capitulos)} capítulos · …"` → con un .txt de un capítulo la
cabecera dice «1 capítulos» y la ficha, tres líneas más abajo, «1 capítulo». No lo toca el
diff; lo vi al probar el libro de un solo capítulo.

### H7 · NOTA — El banco de mutantes cuenta una viñeta de Markdown como fallo

`tools/banco_mutantes.py:463-464` toma como nombre de prueba fallida toda línea que
empiece por «- ». Una prueba imprime `- **1 palabras** en 1 capítulo · entre 1 minutos…`
(la ficha de un libro mínimo) y sale en `fallos` en todas las ejecuciones, control
incluido. No cambia el veredicto (se compara por nombre esperado), pero ensucia la lectura.

---

## Tabla de mutantes

Copias en `scratchpad/f17_arbol/<id>/` (con `app/`, `pruebas_*.py`, `tests_smoke.py`,
`main.py`, `validar_local.py`, `catalogo_recomendaciones.csv` y el `catalogo_emb_*.npy`
de `~/.literalevel`, que no está en la raíz del repo). `LITERALEVEL_MODELO` y
`LITERALEVEL_DICCIONARIO` apuntando a los del repo. **Control sin mutar, antes de mutar:**
`pruebas_extremas.py` 301/301 (50 s), `pruebas_ficha.py`, `tests_smoke.py`,
`pruebas_perfil.py`, `pruebas_lexicon.py --sin-openai`, `pruebas_integracion.py` (27) y
`pruebas_voz.py` (sin clave): las siete con `rc=0` (`scratchpad/f17_control.log`).
Registro completo en `scratchpad/f17_mutantes.log`; salida de cada suite en
`f17_arbol/<id>/f17_salida.txt`.

| Mutante | Archivo | Prueba que dice cubrirlo | Resultado |
|---|---|---|---|
| F16-indice-valor | ui.py (cap.change con value pelado) | abrir un libro no pinta un error rojo | CAZADO por su prueba |
| F16-descarga-vacia | ui.py (`quieto` con `vacio`) | abrir un libro no pinta un error rojo | CAZADO por su prueba |
| F16-indice-select | ui.py (indice.select lambda v: v) | abrir un libro no pinta un error rojo | CAZADO por su prueba |
| F16-indice-rango | ui.py (`valido = actual is not None`) | abrir un libro no pinta un error rojo | CAZADO por su prueba |
| F16-voz-sin-clave | ui.py (`if False:` en `_practicar`) | la practica de voz no cobra sin clave | CAZADO por su prueba |
| F16-ficha-ritmo | ui.py (`if False:` en `_ficha_libro`) | la ficha no promete un ritmo que no sabe | CAZADO por su prueba |
| F16-rescate | catalogo.py (`_PARECIDO_NOMBRE = 0.99`) | el buscador encuentra un nombre mal escrito | CAZADO por su prueba |
| F16-umbral | catalogo.py (`minimo_similitud = 0.0`) | el buscador encuentra un nombre mal escrito | CAZADO por su prueba |
| F16-miles | ficha.py (coma de miles) | los miles llevan punto, no coma (`pruebas_ficha.py`) | CAZADO por su prueba |
| F16-muestra | ficha.py (tope 6000) | el tope de la muestra es el que se documenta (`pruebas_ficha.py`) | CAZADO por su prueba |
| F16-usuarios | cuentas.py (`con_nombre=True`) | la pestana publica no dice que usuarios hay | CAZADO por su prueba |
| X1-indice-cero | ui.py:1469 (`else 0`) | abrir un libro no pinta un error rojo | **VIVO** |
| X2-indice-ignora-actual | ui.py:1469 (`value=None` siempre) | abrir un libro no pinta un error rojo | CAZADO por su prueba |
| X3-opciones-dos-sitios | ui.py:1394 (etiquetas propias en `_abrir`) | abrir un libro no pinta un error rojo | **VIVO** |
| X4-catalogo-final-vacio | ui.py:1022 (`vacio` en el yield final) | abrir un libro no pinta un error rojo | **VIVO** |
| X5-practicar-cobra-antes | ui.py:2799 (`_puede_pagar` antes de la guardia) | la practica de voz no cobra sin clave | CAZADO por su prueba |
| X6-est-libro-sin-indice | ui.py:3433 (línea quitada = el arreglo de H1) | abrir un libro no pinta un error rojo | **VIVO** (nadie mira ese cableado) |
| X7-ficha-rango-invertido | ui.py:1852-1853 (velocidades al revés) | la ficha no promete un ritmo que no sabe | **VIVO** |
| X8-getattr-capitulos | ui.py:1460 (`if libro is None:`) | abrir un libro no pinta un error rojo | VIVO, pero **equivalente**: con `capitulos=[]` el `int(None)` cae en el `except` y devuelve lo mismo |

Balance: 19 mutantes; los 11 del banco cazados por su prueba; de los 8 míos, 2 cazados,
1 equivalente y **5 vivos** (X1, X3, X4, X6, X7), de los que X6 es el arreglo y no un
defecto. Ninguna de las cinco pruebas nuevas es decorativa para lo que se propuso
cubrir; lo que no cubren está en H1 y H4.

---

## Lo que comprobé y estaba bien

Aplicación real: repo en `127.0.0.1:7860` con datos aislados en `scratchpad/f17_datos`
(`LITERALEVEL_DATOS`), Chrome dirigido por DevTools, un observador de toasts de Gradio
instalado en la página y, para el Space, un contexto de navegador limpio.

- **Los cinco cambios no rompen lo que antes funcionaba.** Con *Karamázov* (98 capítulos):
  desplegable de arriba al 60; índice de abajo al 30; «Siguiente ›» y «‹ Anterior» de
  arriba y «Capítulo siguiente ›» / «‹ Capítulo anterior» de abajo. En los cinco
  movimientos desplegable, índice y primera línea del texto coincidieron y no hubo ningún
  toast. Recarga con libro abierto (`_reanudar`): vuelve al capítulo 30 con los tres
  mandos de acuerdo, dos veces. Segunda pestaña del mismo navegador: retoma el mismo
  marcapáginas, navega sola y no interfiere con la primera (el estado de componentes es
  por sesión en Gradio 6: `blocks.py:1873` y `2061`).
- **El arreglo 1 hace lo que dice en su caso.** Con el desplegable en un capítulo que
  existe en el libro nuevo (txt de un capítulo → *Karamázov*; *Karamázov* cap. 30 →
  recarga → buscador) no sale ningún error. La reproducción original —marcapáginas en el
  capítulo 2— queda cerrada. El primer `yield` ya no toca `cap` (mutante
  F16-descarga-vacia cazado).
- **Los arreglos 2 y 3** (`_opciones_capitulos` + `_indice_de` validado, cableado con
  opciones y valor): `indice.select` y `cap.change` mandan opciones y valor juntos; ni el
  índice ni el desplegable mandan nunca un valor suelto (mutantes F16-indice-valor,
  F16-indice-select, F16-indice-rango y X2 cazados). El bucle `select`/`change` no se
  reabre: cero peticiones extra en la traza de red al elegir en el índice.
- **Un capítulo:** .txt subido desde disco → «1. Texto completo · 1.283 pal.» en los dos
  mandos, ficha «en 1 capítulo · entre 7 minutos y 12 minutos». Anterior/Siguiente no se
  salen. **366 capítulos:** *War and Peace* subido desde disco → 366 opciones en el
  índice; elegir el 300 tarda 1,0 s hasta que el desplegable lo refleja; el índice
  **no pierde la posición de scroll** al repintarse con las 366 opciones (scrollTop
  2613 antes y después), que era mi sospecha por mandar `choices` en cada cambio.
- **Subir un archivo con un libro abierto en un capítulo alto** (cap. 90 → txt de 1
  capítulo): sin error, porque `_abrir` no es generadora y el manejador recibe el valor
  nuevo (`[null, 0]` en la traza). Es lo que aísla el problema a los dos caminos
  generadores.
- **Arreglo 4 (`_ficha_libro`):** sin perfil la ficha da «entre 32 h 29 min y 53 h 09 min
  de lectura»; con perfil y sin curva, la prueba (a) exige el rango y (b)/(c) exigen que
  con curva se moje en los dos sentidos; F16-ficha-ritmo cazado. No creé perfil en la
  interfaz, así que la variante con «según lo que te cueste» la doy por la prueba y por
  lectura del código (`ui.py:1844-1858`), no por pantalla.
- **Arreglo 5 (`_practicar`):** la guardia está antes de `_puede_pagar` y devuelve el
  aviso legible; sin clave no descuenta cupo y con clave sí (prueba + F16-voz-sin-clave +
  X5). Las tres pruebas de la suite que dependían de la puerta de perfil fingen la clave
  con `config_mod.falta = lambda: []`, y `_con_puerta` la restaura en `finally`.
- **`pruebas_voz.py`** ya no usa un nombre fijo en el temporal: `mkdtemp` por ejecución;
  con el banco corriendo suites en serie no vi ninguna colisión.
- **El Space** responde con el mismo código: búsqueda «dostoyevski» en 1,6 s (caliente),
  *Karamázov* abierto en 5,1 s (cacheado), *Notes* en 4,2 s. Con identidad nueva, sin
  marcapáginas, abrir el primer libro no da error —que es el caso del guion si el
  navegador de la grabación es limpio o el marcapáginas está bajo—.
- **Repositorio intacto:** `git status` limpio al terminar; nada en `auditoria/` salvo
  este archivo; todo lo temporal en `scratchpad/f17_*`. Mis dos servidores locales
  (7860 y 7862) quedaron apagados.

## Qué haría esta noche, por orden

1. `ui.py:3433`: quitar `cap` de las entradas (`est_libro.change(lambda l: _indice_de(l, None), est_libro, indice)`)
   o borrar la línea. Una línea, verificada en copia. Cierra H1 y, de paso, H2.
2. `ui.py:3030`: `gr.update()` en vez de `vacio` en el «Abriendo…» de `_seguir_leyendo`.
3. Si hay tiempo: `gr.skip()` en los `yield` tempranos de las dos generadoras (H3).
4. Si no se toca nada: antes de grabar, abrir *Crime and Punishment* una vez en el
   navegador de la grabación y dejarlo ahí (marcapáginas en un capítulo < 43), y no
   pulsar «Retomar donde lo dejé» en cámara.

**¿Se puede grabar mañana con este código? Sí** — el paso estrella abre el libro bien y
solo pinta el Error rojo si el marcapáginas del navegador que graba está en un capítulo
por encima del 42; con esa precaución se graba, y con el arreglo de una línea de H1 se
graba sin precauciones.
