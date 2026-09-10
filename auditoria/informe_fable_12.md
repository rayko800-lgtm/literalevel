# Duodécima auditoría (Fable), a ciegas — árbol `ffcc0a8`

Fecha: 10 de septiembre de 2026. No se leyó nada de `auditoria/` (solo se listó
el directorio para elegir el nombre de este archivo). Todo lo que se afirma
abajo se ejecutó; las salidas literales van con cada hallazgo. Guiones y
salidas en el scratchpad de la sesión (`mutar.py`, `mut_resultados.json`,
`mut_*.out`, `espia/sitecustomize.py`, `espia_*.out`, `validar_local.out`).

## Recuento

| Gravedad | Nº |
|---|---|
| Crítico | 0 |
| Serio | 8 |
| Menor | 10 |
| Notas | 11 |

Los serios se reparten en tres grupos: **pruebas que no prueban** (S5–S8, con
mutantes que sobreviven a la suite entera), **la aplicación** (S1, S2) y
**cifras y artefactos públicos** (S3, S4).

---

## Método del banco de mutaciones

Copia del árbol en el scratchpad (`app/`, pruebas, `main.py`, el CSV), un
subproceso por mutante, `LITERALEVEL_MODELO` y `LITERALEVEL_DICCIONARIO`
apuntando a los datos reales para que ninguna prueba falle por un archivo no
copiado. La copia sin mutar pasa las 222 pruebas (`mut_base.out`). Se
ejecutaron **70 mutantes** (uno no se aplicó por no casar el texto):
**26 cazados, 44 sobreviven**. Para cada uno se anota **qué prueba** cae, no
solo que la suite cae. Los que interesan están en los hallazgos; la lista
completa está en `mut_resultados.json` (claves sin prefijo `M`/`C`, que son
de otra sesión que compartía el archivo y no se han leído).

---

## Hallazgos serios

### S1. `_medir` levanta `OSError` hacia Gradio cuando el modelo es un repositorio del Hub que no se puede descargar

`app/ui.py:1154-1158`:

```python
    try:
        r = puntuador().puntuar(ficha.sin_licencia(c.texto))
    except (ValueError, FileNotFoundError) as e:
        yield _aviso(e)
        return
```

`FileNotFoundError` solo cubre la carpeta local inexistente. En el Space,
`LITERALEVEL_MODELO=MikeMaki1763/literalevel-v4` y `from_pretrained` lanza
`OSError` (no `FileNotFoundError`) si el Hub no responde, si el repositorio se
renombra o si la descarga se corta en el arranque en frío. Los otros tres
manejadores que cargan el modelo (`_desde_muestra`, `_nivel_desde_libro`,
`_analizar_libro`) sí atrapan `OSError`; este, que es el botón «¿Cómo de
difícil es este capítulo?», no. Reproducido con `HF_HUB_OFFLINE=1` y un
identificador de repositorio:

```
_medir -> LEVANTA OSError : We couldn't connect to 'https://huggingface.co' to load the files, and couldn't find them in the cached files. ...
_desde_muestra -> devolvio: (None, "[!] We couldn't connect to 'https://huggingface.co' ...
_analizar_libro -> devolvio: [("[!] We couldn't connect to 'https://huggingface.co' ...
```

Arreglo: `except (ValueError, OSError) as e:` (`FileNotFoundError` es
subclase de `OSError`, así que no se pierde el mensaje de la carpeta). La
suite no lo ve porque ninguna prueba mide con un modelo ausente: el mutante
`medir_no_atrapa_modelo_ausente` (quitar `FileNotFoundError` del `except`)
**sobrevive** a las 222 pruebas.

### S2. El tope por hora del cubo «lexico» corta consultas de diccionario que no cuestan nada

`app/ui.py:127-130` promete:

```
# Las acciones que no cuestan dinero (leer, buscar, medir un capitulo) no se
# limitan: son locales.
```

pero `app/ui.py:1899` aplica `_dentro_del_limite(peticion, "lexico",
LIMITE_CONSULTAS_HORA)` **antes** de `_puede_pagar`, es decir, también a un
visitante sin perfil (o a una copia sin `OPENAI_API_KEY`), cuya consulta va con
`usar_openai=False` y es diccionario + IPA + Wiktionary, todo local.
Reproducido con un consultor falso que registra `usar_openai` y sin clave:

```
llamadas al consultor (todas con usar_openai=False, o sea gratis): 30 {True}
consulta numero 31 -> [!] Has llegado al límite de consultas de esta hora. Vuelve a intentarlo en unos 60 minutos. Leer, buscar y medir un capítulo sigu
```

(El `{True}` es porque sin `LITERALEVEL_CUENTAS` la puerta está abierta; en
`lexicon` no hay clave y no se gasta nada igual.) El tope es **por IP**: un
aula entera detrás de la NAT del colegio comparte 30 consultas de diccionario
por hora, sin que ninguna pueda costar un céntimo, y el aviso les dice que
«leer, buscar y medir siguen funcionando: no cuestan nada», como si la consulta
sí costara. El dinero ya lo frena la puerta de perfil más el cupo; el tope por
hora solo tiene sentido cuando `puede` es verdadero.

Arreglo: comprobar primero, sin consumir, si la sesión puede pagar
(`cuentas.permite`), aplicar `_dentro_del_limite` solo en ese caso y después
`consumir`. Lo mismo, con menos consecuencia, en `_de_que_trata`
(`ui.py:1425`), donde la ficha por hora se gasta antes de saber si hay perfil.

### S3. «Cuarenta parejas de color, ocho por paleta» ya no es lo que mide la prueba: son 85, 17 por paleta

`entrega/documento.tex:667` (cuadro de Esmeralda) y `:840` (métricas de
éxito), y `entrega/estrategia.md:133` y `:392`, dicen literalmente:

> las **cuarenta parejas** de color que se comprueban —ocho por paleta, cada una con su umbral […]

`pruebas_extremas.py:926-970` tiene 17 parejas en `PARES` y la prueba imprime
`5 paletas x 17 pares, todas AA`. `PENDIENTES.md:95` sí dice **85 (17 por
paleta)**. Los dos «peores» que se citan siguen siendo ciertos con las 17
parejas (recalculado con el mismo código de la prueba): 4,53 es
`hielo/boton-alto` (4,527) y 3,11 es `menta/titulo-3` (3,108). Solo hay que
corregir el recuento en los cuatro sitios.

### S4. La tarjeta pública del modelo enlaza a `https://github.com/` a secas

`modelo_v4/README.md:20` (y es lo que está publicado, comprobado en
`https://huggingface.co/MikeMaki1763/literalevel-v4/raw/main/README.md`):

> Es el motor de [LiteraLevel](https://github.com/), una aplicación que recorre libros enteros …

Es la única URL del documento y apunta a la portada de GitHub. Quien abra la
tarjeta desde el enlace que da la presentación (diapositiva final,
«Modelo público») y pulse el nombre del proyecto aterriza en la página de
inicio de GitHub. El repositorio remoto (`rayko800-lgtm/literalevel`)
devuelve 404 sin sesión, así que o se enlaza el Space
(`https://huggingface.co/spaces/MikeMaki1763/literalevel`) o se quita el
enlace.

### S5. La puerta de pago de la explicación léxica no tiene prueba

«Las tres puertas del dinero» (`pruebas_extremas.py:1624-1681`) ejercitan la
sinopsis y la voz. La tercera —`_puede_pagar` dentro de `_consultar`,
`ui.py:1909`— no. Mutante `consultar_sin_puerta_de_pago`:

```python
        puede, motivo_pago = True, ""          # en vez de _puede_pagar(peticion)
        r = consultor().consultar(
```

**Sobrevive: 222 de 222 en verde.** Es la puerta que se abre más veces por
sesión (cada palabra consultada). Una prueba con `_con_puerta` y un
`ui.consultor` falso que registre `usar_openai` basta: debe recibir `False` y
la ficha debe llevar el motivo.

### S6. Los topes por hora de la voz y de la sinopsis no tienen prueba, y los valores configurados de los tres tampoco

Sobreviven, sin que caiga ninguna prueba:

- `voz_sin_tope_hora`: `ui.py:2070` `if not _dentro_del_limite(peticion, "voz", …)` → `if False:`
- `sinopsis_sin_tope_hora`: `ui.py:1425` ídem con `"sinopsis"`
- `tope_voz_ilimitado`: `LIMITE_VOZ_HORA = 0`
- `tope_sinopsis_ilimitado`: `LIMITE_SINOPSIS_HORA = 0`
- `tope_consultas_ilimitado`: `LIMITE_CONSULTAS_HORA = 0` (la prueba que sí
  existe, `_por_encima_del_tope_no_llega_al_consultor`, **sustituye** la
  constante por 1, así que el valor real del módulo nunca se comprueba)

El docstring de `prueba` (`pruebas_extremas.py:72-77`) cuenta que una ronda
anterior demostró que «la suite pasaba con los tres topes por hora apagados»
y que eso se arregló. Se arregló para el cubo «lexico»; los otros dos siguen
igual. Además, `prueba("el tope se respeta", …)` (`:408-410`) devuelve
`sum(...)` sin aseverar nada —imprime `ok 4` y con un tope roto imprimiría
`ok 9`—, y `"una IP no consume la cuota de otra"` (`:411-414`) devuelve una
tupla, que nunca es `False`: el mutante `ip_constante` (todas las IP son
«local») solo cae por una prueba ajena, «el aviso de tope dice los minutos que
faltan», que tropieza con un cubo ya lleno. Arreglo: aseverar en las dos
(`assert sum(...) == 4`, `assert segunda_ip is True`) y añadir para voz y
sinopsis el mismo patrón que `_por_encima_del_tope…`, comprobando además que
`LIMITE_*_HORA > 0` cuando la variable de entorno no está.

### S7. El aislamiento de datos por lector se prueba en `_dir_lector` y en nada más

Sobreviven, sin que caiga ninguna prueba, cinco mutantes que devuelven el
Space a «una carpeta para todos»:

| mutante | qué cambia |
|---|---|
| `ruta_sesion_compartida` | `_ruta_sesion` (`ui.py:957-960`) devuelve siempre `RUTA_SESION`: el marcapáginas, «el caso más feo» según el comentario de `ui.py:92-94`, vuelve a ser uno para todos los visitantes |
| `cuestionario_guarda_en_anonimo` | `_desde_cuestionario` guarda en `_archivo_lector("perfil.json", None)`: exactamente el fallo histórico de `lectores/anonimo/` que documenta `ui.py:489-495`, por otra vía |
| `cuestionario_sin_anotacion_request` | se quita la anotación `gr.Request` a `peticion`; Gradio deja de inyectarla, `peticion` llega `None` siempre, y la prueba «todos los manejadores reciben la peticion» (`:1260-1301`) **lo salta** porque solo mira los que anotan `Request` |
| `perfil_inicial_compartido` | `_perfil_inicial` lee el perfil de `None` |
| `cuaderno_compartido` | `_mis_palabras` lee `cuaderno.RUTA_POR_DEFECTO` |
| `voz_db_compartida` | `_debiles` lee `voz.db` global |

Las pruebas de «Datos de cada lector, no de todos» (`:467-502`) comprueban
que `_dir_lector` separa carpetas, pero ninguna llama a un manejador con dos
`session_hash` distintos y mira que lo guardado por uno no lo vea el otro.
Arreglo: una prueba en modo nube que ejecute `_desde_cuestionario` /
`_perfil_inicial`, `_abrir` / `_reanudar`, `_consultar` (con consultor falso)
/ `_mis_palabras` y `_practicar`-`_debiles` con dos peticiones y asevere el
aislamiento; y que la comprobación de inyección también marque como fallo a
todo manejador que use `_archivo_lector(..., peticion)` sin anotar.

### S8. La prueba «session_hash con ../ no escapa» no puede fallar

`pruebas_extremas.py:491-494`:

```python
prueba("session_hash con ../ no escapa",
       lambda: _con_nube(lambda: (
           ui.BASE_DATOS_LECTOR / "lectores") in ui._dir_lector(
               _Peticion("../../etc/passwd")).parents))
```

`Path.parents` es léxico: `.../lectores/../../etc/passwd` tiene a
`.../lectores` entre sus padres aunque resuelva fuera. Mutante
`sesion_escape_sin_limpiar` (`ui.py:118` sin `_SESION_SEGURA.sub`) →
**sobrevive**. Comprobación directa:

```
parents contiene base/lectores: True
ruta resuelta: C:\etc\passwd
resuelta dentro de base: False
```

Arreglo: `assert base.resolve() in ui._dir_lector(...).resolve().parents`, o
mejor, aseverar que `.name` no contiene `.`, `/` ni `\`. La sanitización real
(`ui.py:104,118`) está bien; lo que no vale es la prueba.

---

## Hallazgos menores

### M1. El cupo del perfil se cobra en tres caminos en los que no se gasta nada

`cuentas.consumir` cobra antes de llamar y `devolver()` (`app/cuentas.py:259-278`)
existe para deshacerlo, pero `ui.py` solo devuelve en un caso (acierto de
caché, `:1930-1931`). Reproducido con `LITERALEVEL_CUENTAS="invitado:LLAVE-B:3"`
y sin clave de OpenAI:

```
entrar: Has entrado como **invitado**. Te quedan **3** usos de la ex
de_que_trata sin clave -> Para el resumen hace falta la clave de OpenAI. Todo lo demás de la fic
   usos apuntados: {'invitado': 1}
consultar sin diccionario -> [!] No encuentro el diccionario Kaikki
   usos apuntados: {'invitado': 2}
queda(): 1
practicar audio roto -> ## 0 / 100

[!] No se pudo transcribir (sin `OPENAI_API_KEY`
   usos apuntados: {'invitado': 3}
```

Tres usos gastados, cero llamadas a la API. El caso `cliente is None`
(`ui.py:1446`) se sabe antes de cobrar y no tiene excusa; los otros dos
(`FileNotFoundError` en `:1912`, `voz.practicar` sin transcripción en
`:2083`) deberían llamar a `cuentas.devolver`. Los mutantes
`devolver_no_hace_nada`, `restar_baja_de_cero`, `queda_negativo` y
`consumir_no_devuelve_al_rechazar` **sobreviven**: nada prueba la devolución
ni el suelo en cero.

### M2. `--ll-lector-texto` vuelve a ser una variable muerta: la regla `.prose *` de la paleta le gana

`app/paletas.py:305-306`:

```
".prose,.prose *,.markdown-text,.markdown-text *{"
"color:var(--ll-texto) !important}"
```

`gr.HTML` pinta su contenido dentro de `div.prose`, así que
`#ll-lector{color:var(--ll-lector-texto)}` (`ui.py:845`) y
`#ll-voz{…color:var(--ll-lector-texto)}` (`:2015`) pierden contra un
`!important`. Medido en el navegador sobre la app local:

```
"ancestros":["DIV.","DIV.prose.gradio-style.svelte-26mp0t", ...]
"reglasColor":[..., ".prose, .prose *, ... => var(--ll-texto) !important", "#ll-lector => var(--ll-lector-texto)", ...]
"computed":"rgb(223, 234, 243)"      <- --ll-texto (#dfeaf3), no --ll-lector-texto (#e8f1f8)
```

No es un fallo de legibilidad —la pareja pintada de verdad, `--ll-texto`
sobre el fondo del lector, da entre 10,0 y 16,0 en las cinco paletas—, pero
la prueba de contraste mide `--ll-lector-texto` sobre `--ll-lector-fondo`
(`PARES["lector"]`), que es una pareja que el navegador no pinta, y el
comentario de `ui.py:841-844` dice haber resucitado la variable. Arreglo:
`#ll-lector,#ll-lector p{color:var(--ll-lector-texto) !important}` (y lo
mismo en `#ll-voz`), o excluir `#ll-lector` de la regla de `.prose`.

### M3. Un libro descargado como `.txt` no acierta nunca en la caché de Gutenberg

`app/ui.py:682-684`:

```python
    destino = RUTA_LIBROS / f"pg{num}.epub"
    if destino.exists() and destino.stat().st_size > 2000:
        return str(destino)
```

Cuando el epub falla y se baja la segunda fuente, `final =
destino.with_suffix(".txt")`, que la comprobación siguiente no mira. Con
`pg99999.txt` de 5.000 bytes en la carpeta y la red cortada:

```
resultado: ConnectionError No pude descargarlo de Gutenberg: sin red
intentos de red pese a tener pg99999.txt en cache: 3
```

Arreglo: comprobar `.epub` y `.txt` (`for ext in (".epub", ".txt")`).

### M4. Archivos propios mal formados que sí levantan

Probados en `analisis/` (los escribe la app; no son entrada del usuario):

```
analizar_libro con filas sin claves      -> LEVANTA KeyError: 'dificultad'
repintar_grafica con filas sin claves    -> LEVANTA KeyError: 'capitulo'
de_que_trata con sinopsis '[]'           -> LEVANTA AttributeError: 'list' object has no attribute 'get'
de_que_trata con sinopsis '"hola"'       -> LEVANTA AttributeError: 'str' object has no attribute 'get'
de_que_trata con sinopsis '{"de_que_trata": 5}' -> LEVANTA AttributeError: 'int' object has no attribute 'strip'
```

Es el mismo tipo de fallo que ya se corrigió en `sesion.json` (`ui.py:981-987`)
y en `perfil.json`, en los dos archivos que quedaban. Arreglo: en
`_analisis_guardado` y `_sinopsis_guardada`, devolver `None` si lo leído no
es un `dict` con la forma esperada (y en la sinopsis, `str()` sobre cada
campo antes de `.strip()`).

### M5. La latencia publicada de la consulta léxica es de antes de `reasoning.effort="low"`

`entrega/documento.tex:771`, `entrega/estrategia.md:240` y `AGENTS.md:182`:

> De los 28 a 44 segundos de una consulta léxica nueva, **23 a 39 son espera al servicio externo**

`app/lexicon.py:69-82` mide, «llamadas de verdad», 67,7 s con el esfuerzo por
defecto y **14,9 s con `low`**, que es lo que corre (`ESFUERZO_RAZONAMIENTO =
"low"`, `:82,514`). Y `AGENTS.md:196-201` sigue diciendo que el cambio a
`low` está «pendiente para Codex, sin hacer». Tres cifras para la misma
espera; la que ve el usuario hoy no es ninguna de las dos publicadas.

### M6. Colores clavados que la prueba de CSS no ve, y `label.selected` sin comprobar

`_el_css_no_clava_los_colores_que_ya_fallaron` (`pruebas_extremas.py:1197-1257`)
mira ocho selectores concretos. Sobreviven, sin que caiga ninguna prueba:

- `css_color_clavado_en_cuaderno`: `#ll-cuaderno .ll-c{… background:#0a1522;color:#dfeaf3}`
- `css_color_clavado_en_biblio`: `#ll-biblio .ll-l{… background:#0a1522;color:#dfeaf3}`
- `css_boton_primario_clavado`: `button.primary{background:#2e9cc4 !important}` — el botón que más se pulsa, con la pareja `boton-alto` de la prueba de contraste midiendo una variable que ya no se pinta
- `css_h1_clavado`: el degradado del título sustituido por `#eaf8ff`
- `paleta_label_selected_con_texto_cuerpo`: `label.selected{color:var(--ll-texto)}` — la prueba `:1156-1158` solo comprueba que exista la cadena `label.selected`
- `paleta_sin_prose`: quitar entera la regla `.prose *` de la paleta (el texto de Markdown vuelve al color del tema del navegador, el fallo medido «1,1:1» que cuenta `paletas.py:210-215`)

Arreglo barato: en vez de una lista de selectores, pasar `_colores_literales`
sobre **todo** el CSS de `ui.py` y `paletas.py` con una lista blanca corta
(`rgba(0,0,0,0)`, `transparent`, las estrellas), y comprobar en
`label.selected` que el color sea `--ll-boton-texto`.

### M7. La carga del modelo en `_desde_muestra` y en la suite: se paga antes de validar

`app/ui.py:578`: `perfil_mod.desde_muestra(texto, puntuador(), …)` evalúa
`puntuador()` antes de que `puntuar` rechace el texto. Pegar una lista o un
menú obliga a cargar 328 MB para leer «no parece prosa». Y por eso
`pruebas_extremas.py` —que dice en su sección 4 evitar los recursos pesados—
carga el modelo en la prueba «muestra que no es prosa» (`extremas_base.out`):

```
Loading weights: 100%|██████████| 105/105 [0
  ok    muestra que no es prosa                        [!] El texto es muy corto: se necesitan al menos 150 palabras.
```

Arreglo: `scoring.continuous_prose(texto)` antes de `puntuador()` en
`_desde_muestra` y `_nivel_desde_libro`.

### M8. Ortografía: «partian» en `entrega/estrategia.md:199`

> y no los 0,8 y 1,6 de antes, que ni siquiera partian el 0–2 en tres partes iguales

Es «partían». La misma frase en `documento.tex:1864-1865` y `documento.md:820`
está bien. Es el único fallo de acento encontrado en los `.md`/`.tex` de la
entrega, `README.md`, `PENDIENTES.md` y `DESPLIEGUE.md` con una lista de
setenta formas verbales y sustantivos que suelen perderlo (los «paso» y
«practica» que salen son válidos).

### M9. Contraseña real en un archivo versionado

`entrega/mensaje_profesor.md:23`:

> usuario: `invitado1` · contraseña: `074cfd6zbjy8pc`

`git ls-files` lo incluye y `master` está en `origin/master`
(`rayko800-lgtm/literalevel`, hoy 404 sin sesión, o sea privado). `.gitignore`
excluye `literalevel_codigos.txt`, así que la intención era no versionar
credenciales, y esta se coló. Si el repositorio se comparte con el profesor
—«le puedo compartir el repositorio», mismo archivo— o se hace público, la
credencial que abre el gasto de la API viaja con él. Arreglo: sustituir por
`<contraseña>` y rotar el perfil `invitado1` en el secreto del Space.

### M10. `_abrir_del_catalogo` no atrapa los errores de disco de su propia caché

`ui.py:681` `RUTA_LIBROS.mkdir(...)` va fuera del `try` interno y
`_abrir_del_catalogo` solo atrapa `(ValueError, ConnectionError)`:

```
abrir_del_catalogo con RUTA_LIBROS=archivo -> LEVANTA FileExistsError [WinError 183] ...
```

Improbable en el Space (disco efímero pero escribible); es el único
`OSError` de disco que un manejador deja pasar. Arreglo: `except (ValueError,
ConnectionError, OSError)`.

---

## Notas

- **N1.** `entrega/documento.tex:150` (comentario): «Las doce figuras siguen en TikZ». Hay **13** `\begin{figure}` (`fig:pipeline` … `fig:competencia`). No se ve en el PDF.
- **N2.** `documento.tex:2178`: el trazo se llama `corte16` y está en `y=1.4`. El nombre es del corte derogado (1,6); el valor y la leyenda («banda avanzado (≥ 1,4)») son los vigentes. Solo confunde a quien edite el `.tex`.
- **N3.** Tamaño en disco: `AGENTS.md:143` dice 576 MB (incluye el CSV); `PENDIENTES.md:103` y `DESPLIEGUE.md:17` dicen 575. Medido: 328,5 + 3,6 + 243,3 = 575,4 MB sin CSV; 576,3 con él. Las dos son defendibles; conviene una sola.
- **N4.** Audio del diccionario: `lexicon.py:641` dice 7.003 entradas con audio; `ui.py:1830` dice «las 7.484 son de upload.wikimedia.org». Comprobado en el `.db`: 7.003 filas con algún audio, 7.484 campos no vacíos (1.025 UK + 6.459 US), 4.393 URL distintas, ninguna fuera de `upload.wikimedia.org`, ninguna con comillas. Las dos cifras son ciertas para cosas distintas.
- **N5.** `DESPLIEGUE.md:48` titula «Opción A — Hugging Face PRO, 9 $ un mes» y `:3-4` dice «cuenta Pro de 7 USD/mes». El documento lo explica (9 de tarifa, 7 con descuento); aquí queda sin explicar.
- **N6.** `gr.Number` con `minimum=1, maximum=50` deja que Gradio valide antes del manejador: un `-3` o un `500` sacan un aviso en inglés («Value -3 is less than minimum value 1.»). No es una excepción del manejador; es el único mensaje de la interfaz que no está en español.
- **N7.** `_diagnostico` corre en `demo.load` y llama a `catalogo()`, que construye `Catalogo()` (lee el CSV, no los embeddings). Después la propia pestaña dice «Cargado en memoria · Catálogo: sí», que es verdad a medias: el CSV sí, el modelo de embeddings no.
- **N8.** `cuaderno.contar` (`app/cuaderno.py:151-153`) cuenta `COUNT(DISTINCT COALESCE(libro,''))`, así que consultas hechas sin libro abierto suman «1 libro» en «Mis palabras».
- **N9.** En «Mi nivel» hay tres `div#ll-lector` (uno por fragmento): identificadores repetidos en el DOM. Funciona porque el CSS es por `#id` y no hay JS que los busque, pero es HTML inválido.
- **N10.** `pruebas_voz.py` y `pruebas_lexicon.py` llaman a la API de verdad y lo declaran en su docstring; no están entre las seis suites del encargo. Con el espía (ver OK) ninguna de las siete suites locales construye `openai.OpenAI`.
- **N11.** De las 222 pruebas extremas, 140 son lambdas que devuelven un valor sin ninguna comparación ni aserción: comprueban «que no levanta», que es lo que la cabecera promete, pero conviene saber que dos tercios de la suite no puede fallar por un resultado equivocado, solo por una excepción.

---

## OK: lo que se comprobó y estaba bien

**Pruebas y mutantes cazados** (con la prueba que cae):

- Guardia del modelo `isdir or _parece_repo_hf` → «el modelo vale como repositorio del Hub».
- Contraseña: aceptar cualquier clave → «entrar con una clave mala no abre nada» (+2); usuario sensible a mayúsculas → «el usuario no distingue mayusculas y la clave si»; `hay_codigos` siempre `False` → 11 pruebas.
- Cupo: `consumir` con tope doble → «veinte peticiones a la vez no burlan el cupo»; puertas de sinopsis y voz quitadas → «la sinopsis pide codigo» / «la practica de voz pide codigo».
- Tope «lexico»: quitado, o con `>` en vez de `>=` → «consultar por encima del tope no llama a OpenAI»; ventana de 1 s → «el aviso de tope dice los minutos que faltan».
- Contraste: aclarar `--ll-acento` de menta → «todas las paletas son legibles»; `opacity:.4` → «la opacidad del CSS no borra el texto»; `#ll-lector{color:inherit}` → «el CSS no clava los colores que ya fallaron»; quitar `--color-accent` o `--error-text-color` → «las superficies tambien salen de la paleta».
- Aislamiento: `_dir_lector` a una sola carpeta → «dos sesiones no comparten carpeta»; `allowed_paths` a `~/.literalevel` entero → «allowed_paths: sirve el audio y nada mas».
- Interfaz: acordeón de entrar cerrado → «lo que abre funciones se encuentra»; `_cefr` con `round` → «la interfaz y el contrato dan la misma letra»; HTML sin escapar → «script incrustado», «img onerror»; palabra larga sin tope → «palabra larguisima no llena la pantalla»; media de medias en `dificultad_global` → dos pruebas; perfil sin validar `nivel` → «perfil con nivel no numerico»; `sesion.json` no-dict → «sesion.json que no es un objeto»; `_mover` sin validar → «mover con un indice que no es numero».

**Espía sobre `openai.OpenAI`** (`espia/sitecustomize.py` en `PYTHONPATH`, con la clave real de `.env` disponible): `pruebas_extremas`, `tests_smoke`, `pruebas_ficha`, `pruebas_perfil`, `pruebas_audio_atomico`, `pruebas_desambiguacion` y `pruebas_integracion` terminan en verde y el registro solo contiene las siete líneas «espía cargado»: **ninguna construye un cliente**.

**Suites**: `pruebas_extremas` 222/222; `pruebas_integracion` 27/27; `tests_smoke` OK; `pruebas_ficha` OK; `pruebas_perfil` OK (0,000 / 1,977); `pruebas_desambiguacion` 7 (README dice 7); `validar_local.py` (una vez): A1 3 0,5040 · A2 8 0,5561 · B1 12 0,9276 · B2 12 1,2414 · C1 12 1,4952; 2 sin cuerpo, 31 pasan el filtro completo, 10 fallan por «muy corto»; baseline 0,860 / 0,807 / 0,668 / 0,732; «VALIDACION CORRECTA: 47 textos, 5 niveles».

**Cifras** (guion → `.dat` → `.tex` → `.md` → README → PENDIENTES → modelo_v4/README → presentación → guion del vídeo): las cinco medias y desviaciones, las tres del baseline y el 0,732, 47/59/2/10/31/38, 0,908/0,829/97,2/53,5 (77/144, 140/144), 144/510/654, la recta 0,7196x+0,3760 sobre las cuatro medias de Colab y 0,67x+0,41 sobre las cinco locales (recalculadas: 0,7196/0,3760 y 0,6669/0,4113), la escala de `escala_cefr.dat` frente a `_TABLA_CEFR` y `public_band`, la figura de la escala (rellenos en 0,6 y 1,4, cortes en 0,2/0,6/1,0/1,4/1,8), el catálogo (1.197; 723/185/69/52/53/115; 148 PG con 0/2/10/12/25/99; 121; 60,4 %; 87,6 %), 8,19/112,7/2.022 → 13,8× y 247×, 2,96 h y 5,14 h, 61 libros/min → 16,8 h, 0,29 MB/s → ~11 h, 8,0 MB/s → 22 min, 3.362/min → 8,8 min, +33 %, MAE 0,499 → 0,200, 44,4 %/50 % del azar, 52 %/21 % de la cuantización, T7 0,041, T8 40/400/20 MB, 0,65 de los fragmentos, 180/110 ppm, 60.000/20.000 de la ficha, 7.003 (0,47 %), 1.487.639. *War and Peace*: el `.dat` tiene 362 filas (el libro 366 capítulos, 362 de cuerpo, comprobado con `reader`+`ficha`), media 1,7346 → 1,735, mín 1,333 en el 34, máx 1,990 en el 202, 0,657, tercios 1,723/1,733/1,747, máximo de la media móvil en el 289, y la columna `media_movil` es exactamente la media móvil centrada de 15 (diferencia máxima 0,0). *Crime and Punishment* 30 filas, 1,6793, 1,270–1,891; *Alice* 12 filas, 1,4967, 1,296–1,878; diálogo 73 % / 28 % / 31 % recalculado sobre los epub. Numeración de cuadros: baseline = 18 del PDF y 13 del `.md`, validación = 16/11, velocidad = 21/16, como dicen README, `validar_local.py` y `estrategia.md`. Guion del vídeo: 561 palabras, 3:44 (`tools/contar_guion.py`). Presentación: 12 diapositivas. `notebook_proyecto.py` y `.ipynb` (92 celdas) contienen las mismas cifras. PDF de 45 páginas sin «??», sin referencias indefinidas, presentación y guion tampoco.

**Aplicación** (local, sin clave, en el navegador): las cinco paletas se aplican y, en amanecer, ningún elemento visible conserva un color del tema hielo; `label.selected` pinta `--ll-boton-texto` sobre `--ll-boton-alto`; la pestaña activa, el botón primario, las cajas y las fichas de radio salen de la paleta. El Space está `RUNNING`, `cpu-basic`, gradio 6.26.0, público. `gr.Blocks.launch` en Gradio 6.26 acepta `theme`, `allowed_paths`, `max_file_size`; `special_args` inyecta por anotación `routes.Request`, como asume el código. Manejadores probados con entradas de usuario (vacíos, índices imposibles, archivos corruptos, `sesion.json`/`perfil.json`/`biblioteca.json` rotos, `cuaderno.db` en ruta imposible): ninguno levanta. Sin `OPENAI_API_KEY`: diccionario, IPA, buscador, medición, ficha y curva funcionan; lo de pago degrada con texto.

**Prosa**: aparte de «partian» (M8), no se encontraron faltas de acento ni desequilibrios de «¿ ?» o «« »» en los entregables; los comentarios de `app/*.py` van sin acentos por convención y las cadenas de usuario con ellos, como se pide.

---

## Lo que no me dio tiempo a comprobar, o quedó a medias

- **Un mutante no se aplicó**: `cuaderno_html_sin_escapar` (quitar `_html.escape` en la tarjeta de «Mis palabras»); el texto que buscaba no casó y el guion lo saltó. Queda sin saber si la suite cazaría HTML vivo en el cuaderno (sospecho que no: ninguna prueba renderiza `_mis_palabras` con una palabra con `<`).
- **Atribución de los cazados**: en todos los mutantes cazados la prueba que cae es la que se esperaba y se nombra arriba, salvo dos casos incidentales que se dicen como tales: `ip_constante` y `ventana_de_un_segundo` caen por «el aviso de tope dice los minutos que faltan», no por las pruebas del freno de gasto (S6). Ningún fallo se debió a un archivo no copiado: la base copiada pasa 222/222 antes de mutar.
- **`mut_resultados.json` tiene 94 entradas**: 70 son de este banco (claves sin prefijo); las 24 con prefijo `M`/`C` estaban ya en el archivo, son de otra sesión que compartía el scratchpad y no se han leído ni se usan aquí.
- **No se condujo la app entera desde el navegador**: chrome-devtools sí respondió y se midió el CSS (paleta, `.prose`, `label.selected`), pero no se hizo el recorrido completo (subir libro, medir, consultar) con clics; esos caminos se ejercitaron llamando a los manejadores desde Python.
- **No se probó el despliegue real** más allá de la API del Hub (`RUNNING`, `cpu-basic`) y la tarjeta del modelo; S1 se reprodujo en local forzando `HF_HUB_OFFLINE=1`, no tirando el Space.
- **`pruebas_voz.py` y `pruebas_lexicon.py` no se ejecutaron**: llaman a la API por diseño y gastarían dinero.

---

## ¿Queda algo que avergonzaría al autor?

**Delante de un profesor que lea:**

1. La tarjeta del modelo, que el propio profesor puede abrir desde la última diapositiva, enlaza a `https://github.com/` (S4).
2. «Cuarenta parejas de color, ocho por paleta» en el documento y en la estrategia, cuando el guion que lo mide imprime 85 y `PENDIENTES.md` ya lo dice (S3). Es exactamente la clase de cifra que un evaluador coteja.
3. Una contraseña real en un `.md` versionado (M9).

**Delante de un profesor que use la app:**

4. Si el Hub tarda o falla al despertar el Space, el primer botón de la pestaña Leer enseña «Error» a secas mientras el resto degrada con frases (S1).
5. En un aula detrás de una sola IP, a la consulta 31 del diccionario —gratis— la app dice que se ha llegado al límite de consultas de pago (S2).
6. Con perfil y un fallo de red, cada intento fallido descuenta un uso del cupo que él ve en «Te quedan N usos» (M1).

Nada de esto es un fallo del modelo ni de las cifras que sostienen el trabajo:
la validación se reproduce, las figuras dibujan lo que sus `.dat` dicen y las
tablas cuadran. Lo que hay es una suite que cubre muy bien lo que ya se rompió
una vez y casi nada de lo que se rompería por segunda vez de otra forma
(S5–S8), y cuatro artefactos con una cifra o un enlace viejos.
