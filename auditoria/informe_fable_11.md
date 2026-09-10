# Auditoría 11 (Fable, a ciegas) — LiteraLevel, árbol `b32b520`

Fecha: 2026-09-09. Alcance: `app/*.py`, `pruebas_*.py`, `tests_smoke.py`, `main.py`,
`validar_local.py`. No se ha leído nada de `auditoria/` ni el `git log`. Todo lo
que se afirma se ha ejecutado; los guiones están en el scratchpad de la sesión
(`a_request.py`, `b_dequetrata.py`, `c_bordes.py`, `d_red.py`, `e_motivo.py`,
`f_varios.py`, `g_css.py`, `mutar.py`). Las suites se corrieron con
`OPENAI_API_KEY=sk-dummy-no-gastar` para no gastar dinero del autor (ver S4:
con la clave real, `pruebas_extremas.py` sí gasta).

## Recuento por gravedad

| Gravedad | Cuántos |
|---|---|
| Crítico | 1 (C1) |
| Serio | 5 (S1–S5) |
| Menor | 9 (M1–M9) |
| Notas | 6 (N1–N6) |

---

## CRÍTICO

### C1. El cuestionario de nivel nunca recibe el `gr.Request`: desplegada, el perfil va a una carpeta compartida y no sobrevive a recargar la página

**`app/ui.py:461`**

```python
def _desde_cuestionario(p_actual, nombre, *valores, peticion: gr.Request = None):
```

Gradio 6.26 solo inyecta el `Request` en parámetros **posicionales**. Su
`special_args` (`gradio/helpers.py:969-973`) recorre la firma y **corta en el
primer parámetro que no sea posicional**:

```python
for param in signature.parameters.values():
    if param.kind not in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
        break
    positional_args.append(param)
```

`peticion` va detrás de `*valores`, es keyword-only, y nunca se inspecciona.
Llega siempre `None`. Reproducción con el `special_args` real:

```
_desde_cuestionario    recibe Request: False   inputs=['perfil', 'nombre', 0.4, 0.8]
_nivel_desde_libro     recibe Request: True    inputs=['perfil', 'nombre', 'libro.txt', <Pet>]
_desde_muestra         recibe Request: True    inputs=['perfil', 'nombre', 'texto', <Pet>]
carpeta con Request  : ...\lectores\abc123
carpeta sin Request  : ...\lectores\anonimo
```

Por qué falla: en el Space (`EN_LA_NUBE`), `_archivo_lector("perfil.json", None)`
resuelve a `lectores/anonimo/perfil.json`, **una sola carpeta para todos los
visitantes**. Cada "Estimar mi nivel" pisa el archivo del anterior (con el
nombre del lector dentro). Y `_perfil_inicial` sí recibe el `Request`, así que
al recargar busca en `lectores/<hash>/perfil.json`, no lo encuentra, y el
lector vuelve a "Todavía no has fijado tu nivel" pese al "Guardado. Ya puedo
recomendarte lecturas" que acaba de leer. Los otros dos caminos (libro y texto
pegado) sí persisten por sesión. Es el punto 1 de la especificación, la
primera pantalla de la app, y la regla de `AGENTS.md` ("dale
`peticion: gr.Request = None` como último parámetro") aquí no funciona.

En local (`EN_LA_NUBE=False`) no se nota, que es por lo que nadie lo ha visto.

Cómo se arregla: quitar el `*valores` de la firma y recibir las respuestas
como lista, por ejemplo cableando `[est_perfil, nombre, gr.State(...)]`; o, más
simple, `def _desde_cuestionario(p_actual, nombre, peticion: gr.Request, *valores)`
no vale (los posicionales se insertan por índice y desplazarían las
respuestas). Lo limpio: `def _desde_cuestionario(p_actual, nombre, *valores)` y
que el cableado pase el request de otra forma, o convertir los radios en un
único `gr.State` que reúna las respuestas mediante `.change`. Y añadir una
prueba que llame a `gradio.helpers.special_args` sobre **cada manejador con
`peticion`** y compruebe que lo recibe.

---

## SERIO

### S1. Cuarenta pruebas de `pruebas_extremas.py` pasan con el código roto: el envoltorio acepta cualquier valor devuelto

**`pruebas_extremas.py:37-62`**

```python
def prueba(nombre: str, fn):
    ...
    try:
        r = fn()
        resumen = str(r)
        ...
        print(f"  ok    {nombre:<46} {resumen}")
```

Que `fn()` devuelva `False` se imprime como `ok False`. El propio docstring
del envoltorio reconoce el problema para el patrón `return malas`, pero deja
sin tocar el otro: **39 de las 216 pruebas devuelven un booleano pelado que
nadie asevera** (contadas sobre la salida de la suite sin mutar). Se comprobó
con un banco de mutaciones (una línea cambiada por copia, subproceso por
copia); un mutante que **pasa** la suite es una prueba decorativa:

| Mutante | Qué rompe | Suite |
|---|---|---|
| M1 `_entrar` acepta cualquier contraseña (`verificar(...) or Cuenta(...)`) | acceso con contraseña | **PASA** (`ok False` en «entrar con una clave mala no abre nada», «un usuario que no existe no entra», «el usuario no distingue mayusculas y la clave si») |
| M2 `_dentro_del_limite` devuelve `True` siempre | los tres topes por IP y hora | **PASA** («el tope se respeta» imprime `ok 9` en vez de `ok 4`) |
| M8 / M24 / M25 quitar la comprobación del tope en `_consultar` / `_practicar` / `_de_que_trata` | ídem, manejador a manejador | **PASA** las tres |
| M7 quitar `_puede_pagar` de `_practicar` | la puerta de pago de la función más cara | **PASA** (`ok False` en «la practica de voz pide codigo») |
| M3 `_salir` no olvida la sesión | salir | **PASA** |
| M6 `_dir_lector` devuelve la misma carpeta para todas las sesiones | aislamiento de datos por lector | **PASA** (`ok False` en «dos sesiones no comparten carpeta» y «session_hash con ../ no escapa») |
| M4 `_medir` revienta con índice fuera de rango | manejador sin excepciones | **PASA** (ver S1.b) |
| M5 `background:yellow` clavado en `#ll-lector::selection` | color clavado en CSS | **PASA** (ver S1.c) |
| M15 `_opciones_libros` vuelve a listar StoryWeaver | corrección documentada en el propio código | **PASA** |

Controles (mutantes que la suite **sí** caza, y por tanto pruebas que sirven):
C9 cupo ×100 en `cuentas.consumir` → falla «veinte peticiones a la vez»; C10
`--ll-acento` de menta aclarado → falla contraste (1,86); C11 quitar
`_html.escape` del lector → fallan «script incrustado» e «img onerror»; C14
`allowed_paths` a `~/.literalevel` entera → falla; C16 `_cefr` con `round` →
falla; C17 quitar el tope del encabezado → falla; C22 acordeón de entrar
cerrado → falla; C23 `construir()` deja algo cargado → falla; M26 aviso de
afinidad → falla.

Salida literal del mutante M1 (últimas líneas):

```
=== M1_entrar_acepta_cualquier_clave: exit=0 27s -> PASA (decorativa)
    Las 216 pruebas extremas pasan: ningun manejador lanzo excepcion.
    'ok False': ok    entrar con una clave mala no abre nada         False
    'ok False': ok    un usuario que no existe no entra              False
    'ok False': ok    el usuario no distingue mayusculas y la clave si False
```

Tres subcasos concretos, además del envoltorio:

**S1.b `pruebas_extremas.py:158`** — `prueba("medir indice imposible", lambda: ui._medir(libro_ok, 999))`.
`_medir` es generadora: la lambda devuelve el generador sin iterarlo y el
cuerpo **no se ejecuta nunca**. Salida sin mutar:
`ok    medir indice imposible    <generator object _medir at 0x...>`.
Con M4 (`c = libro.capitulos[int(idx)]`, IndexError) sigue en `ok`.

**S1.c `pruebas_extremas.py:1108` y `:1139`** — el detector de colores clavados
solo busca `#hex`, `rgb()`, `hsl()`:
`clavados = (re.findall(r"#[0-9a-fA-F]{3,8}\b", c) + re.findall(r"(?:rgba?|hsla?)\([0-9][^)]*\)", c))`.
Un color con nombre (`yellow`, `red`, `white`) o `currentColor` pasa; y como
`--ll-seleccion` sigue apareciendo en el otro bloque (`_CSS_GLOBAL`), la
comprobación "al menos una aparición usa la variable" tampoco salta. Es
exactamente el amarillo que el comentario de `ui.py:787-791` dice haber
desterrado.

**S1.d `pruebas_extremas.py:380`** — «consultar por encima del tope no llama a
OpenAI»: la expresión condicional es
`... if not all(ui._dentro_del_limite(_Pet(ip="10.6.6.6"), "lexico", 0) for _ in range(1)) else "tope generoso, no aplica"`.
Con tope `0` la función devuelve siempre `True`, así que la rama de la
consulta **no se ejecuta jamás**. Salida sin mutar:
`ok    consultar por encima del tope no llama a OpenAI tope generoso, no aplica`.

**S1.e `pruebas_extremas.py:304`** — «html incrustado en la frase» devuelve
`False` **hoy, sin mutar** (`ok    html incrustado en la frase    False`).
`voz.normalizar_palabras("<script>alert(1)</script> hello")` da
`['script', 'alert', '1', 'script', 'hello']`: la puntuación se quita antes, no
hay `<` que escapar y `"&lt;" in ...` es falso. La prueba lleva tiempo
informando de un fallo como éxito.

Cómo se arregla: en `prueba`, tratar `r is False` como fallo (`assert r is not False`)
—a diferencia de la lista vacía, un `False` explícito nunca es un resultado
legítimo—; iterar las generadoras (`list(ui._medir(...))`); en S1.c ampliar el
regex a nombres CSS (`\b(?:yellow|red|white|black|gray|...)\b|currentColor`) o,
mejor, exigir que TODA propiedad de color de esas reglas sea `var(--ll-...)`;
en S1.d probar el tope de verdad (tope 1, dos llamadas, la segunda tiene que
traer `_mensaje_limite`); en S1.e comprobar contra una palabra con `<` que
sobreviva a la normalización, o cambiar la expectativa.

### S2. `_de_que_trata` levanta `FileNotFoundError` hacia Gradio si falta el diccionario, que no necesita para nada

**`app/ui.py:1353`**

```python
        cliente = consultor()._cliente()
```

Sin `try`. `consultor()` construye `ConsultorLexico()`, cuyo `__init__` abre
`Diccionario(RUTA_DICCIONARIO)` y éste lanza `FileNotFoundError` si el
`.db` no está (`lexicon.py:336-341`). La sinopsis solo quiere un cliente de
OpenAI; el diccionario, spaCy y MiniLM no intervienen. En `_consultar` la
misma construcción sí va dentro de `except (FileNotFoundError, OSError)`
(`ui.py:1818`). Reproducción (`b_dequetrata.py`, `LITERALEVEL_DICCIONARIO`
apuntando a una ruta inexistente, sin perfiles):

```
capitulos: 1 palabras: 1080
EXCEPCION HACIA GRADIO: FileNotFoundError No encuentro el diccionario Kaikki en Z:\no\existe\kaikki.db.
```

Es el caso real del Space si el dataset montado falla o cambia de ruta: la
pestaña Leer funciona, la ficha contada funciona, y el botón «¿De qué trata?»
enseña un "Error" pelado. También lo destapó el banco de mutaciones sin
buscarlo: los mutantes C18 y C21, en una copia sin `kaikki_diccionario.db`,
fallaron con este traceback en «la sinopsis pide codigo» en vez de con el
`assert`.

Cómo se arregla: `_de_que_trata` no debe pasar por `consultor()`. Un
`_cliente_openai()` de módulo (clave de `config.obtener`, `OpenAI(api_key=...)`)
compartido por `lexicon` y `ficha`, o al menos envolver la línea en
`try/except Exception` devolviendo texto.

### S3. `_consultar` tira el motivo de la puerta de pago: al visitante sin perfil se le dice "Sin clave de OpenAI", y el cupo se gasta aunque no se llame a OpenAI

**`app/ui.py:1815-1817`**

```python
        puede, motivo_pago = _puede_pagar(peticion)
        r = consultor().consultar(palabra, oracion, nivel, idioma=idioma,
                                  usar_openai=puede)
```

`motivo_pago` no se usa en ningún sitio de la función. Cuando `puede` es
`False`, `lexicon` sigue el camino de "sin clave" y anota
`"sin OPENAI_API_KEY: no hay explicacion contextual"`, que `_humanizar`
traduce a **"Sin clave de OpenAI: no hay explicación de contexto"**. Es falso:
el servidor tiene clave; lo que pasa es que el visitante no ha entrado (o ha
agotado su cupo), y no se le dice ni una cosa ni la otra. Los otros dos
manejadores de pago (`_de_que_trata:1351`, `_practicar:1953`) sí muestran
`motivo_pago`. Reproducción (`e_motivo.py`, con `LITERALEVEL_CUENTAS` puesto y
un consultor de mentira que devuelve los avisos literales de `lexicon.py`):

```
--- visitante SIN entrar, el servidor SI tiene clave:
[!] Sin clave de OpenAI: no hay explicación de contexto. El resto de la ficha no la necesita.
[!] Sin clave de OpenAI: no hay explicación de contexto. El resto de la ficha no la necesita.
¿le dice que entre con su perfil?: False
```

(Además el aviso sale **dos veces**: `lexicon` emite uno por el audio de
respaldo y otro por la explicación, y las dos pistas caen en la misma entrada
de `_AVISOS_HUMANOS`.)

Segunda mitad: `_puede_pagar` **consume** un uso antes de saber si se va a
llamar a OpenAI. Si la respuesta viene de la caché de `lexicon.db`
(`desde_cache=True`), o la palabra no está en el diccionario, o no hay
sentido elegido, no se gasta un céntimo pero el cupo baja igual. Con tope 3:

```
consulta 1: gastado=1  (desde caché, sin llamada)
consulta 2: gastado=2
consulta 3: gastado=3
consulta 4: gastado=4  -> "Sin clave de OpenAI" (el cupo se agotó y no se dice)
```

`cuentas.py` declara «`tope` es el numero de llamadas de pago permitidas»; no
lo es: es el número de pulsaciones.

Cómo se arregla: si `not puede`, añadir `motivo_pago` a la ficha (y suprimir
el aviso de "sin OPENAI_API_KEY" que en ese caso no aplica). Para el cupo,
`lexicon.consultar` sabe si llamó (`extra` nuevo, `pedir_audio`); devolverlo en
`ResultadoLexico` (o consultar la caché antes) y consumir solo entonces, o
devolver el uso si no hubo llamada. Alternativa barata: separar en `cuentas`
"reservar" y "confirmar".

### S4. `pruebas_extremas.py` gasta dinero en cada ejecución: la prueba «audio inexistente» llama a `gpt-4o-mini`

**`pruebas_extremas.py:555-556`**

```python
prueba("audio inexistente",
       lambda: ui._practicar(str(TMP / "no_existe.wav"), "hello")[0][:60])
```

`_practicar` sin `LITERALEVEL_CUENTAS` (que es como corre la suite) llega a
`voz.practicar`: `transcribir_audio` falla en `open()` y devuelve `None`; la
evaluación contra `""` marca `hello` como fallada; y
`explicar_correccion(["hello"])` (`voz.py:137-166`) **no tiene caché** y llama
a `chat.completions.parse` con `gpt-4o-mini`. `config.cargar()` lee la clave
real de `CLAVES.txt` y `.env` (los dos la definen; no se ha leído el valor).
Reproducción con un espía en `openai.OpenAI` (`d_red.py`):

```
clave configurada en el entorno/archivo: si
resultado de la prueba: ## 0 / 100 ...
llamadas a OpenAI que habria hecho la prueba: [{'model': 'gpt-4o-mini', 'messages': '...', 'response_format': '...'}]
mp3 de 'hello' ya en cache local: True
```

(El `tts-1` de "hello" está en caché en esta máquina; en un clon limpio se
pagaría también.) Es una llamada barata, pero es una llamada de pago escondida
en una suite que se ejecuta "para ver que nada revienta", que además tarda
segundos de red y que sin conexión cambia de resultado. La suite tampoco fija
`OPENAI_API_KEY` a nada inocuo.

Cómo se arregla: en la cabecera de `pruebas_extremas.py`, antes de importar
`ui`, `os.environ["OPENAI_API_KEY"] = "sk-pruebas-sin-red"` **y** vaciar
`config.RUTAS_ENV` (o poner `config.cargar = lambda *a, **k: None`), o
sustituir `ui.voz.practicar` por un doble como ya se hace con
`registrar_fallos`.

### S5. `#ll-voz` sigue con el gris clavado y el `border` abreviado que se corrigió en `#ll-lector`: `--ll-borde` no pinta su borde en ninguna paleta

**`app/ui.py:1896-1899`**

```python
_CSS_VOZ = """<style>
#ll-voz{padding:1.1rem 1.3rem;border:1px solid rgba(128,128,128,.28);
  border-radius:10px;font-family:Georgia,"Times New Roman",serif;
  font-size:21px;line-height:2.1;color:inherit}
```

`_CSS_GLOBAL` (`ui.py:384-386`, en `#ll-css`, arriba del todo) pone
`#ll-voz{background:var(--ll-lector-fondo);border-color:var(--ll-borde);border-radius:14px}`.
`_CSS_VOZ` llega **después** en el DOM (dentro del `gr.HTML` de la práctica),
con la misma especificidad (`#id`), y su `border:` abreviado reescribe
`border-color` entero. Gana `rgba(128,128,128,.28)`. Es, palabra por palabra,
el fallo que el comentario de `ui.py:773-776` dice haber arreglado en
`#ll-lector` ("El gris clavado de antes -rgba(128,128,128,.28)- le ganaba al
border-color... porque este border abreviado va despues y lo reescribe
entero"), y también el `color:inherit` de `ui.py:779`. Cascada reproducida
con el CSS que emite la app (`g_css.py`):

```
1) en #ll-css (arriba del todo):
    #ll-voz{ background:var(--ll-lector-fondo);border-color:var(--ll-borde); border-radius:14px}
2) en el gr.HTML de la practica (mas abajo en el DOM), mismo selector, misma especificidad:
    #ll-voz{padding:1.1rem 1.3rem;border:1px solid rgba(128,128,128,.28); border-radius:10px;...;color:inherit}
3) colores clavados dentro de _CSS_VOZ: ['rgba(128,128,128,.28)', '#3fbf8f', 'rgba(224,72,92,.22)', '#e0485c']
4) la prueba 'el CSS no clava los colores' solo mira: ['#ll-lector::selection', '#ll-lector{', '#ll-biblio .ll-b{', '#ll-biblio .ll-b i{', '#ll-cuaderno .ll-f{']
```

Los cuatro colores fijos de `_CSS_VOZ` (verde de acierto, rojo de fallo y su
fondo) tampoco salen de la paleta y ninguna pareja de `_contraste_suficiente`
los mide. No se ha medido el contraste resultante en navegador (chrome-devtools
no respondió); el hallazgo es la regla muerta y la corrección parcial, no una
cifra.

Cómo se arregla: `border:1px solid var(--ll-borde)` y `color:var(--ll-lector-texto)`
en `_CSS_VOZ`; añadir `#ll-voz{` al diccionario `reglas` de
`_el_css_no_clava_los_colores_que_ya_fallaron`; y decidir si el verde/rojo son
variables de paleta (`--ll-bien`, `--ll-mal`) con su pareja en `PARES`.

---

## MENOR

### M1. «Sorpréndeme» anuncia un rango y filtra con otro

**`app/ui.py:697` y `:744`**

```python
        libros = catalogo().por_nivel(p.nivel, n=int(n))      # holgura por defecto 0.25
    ...
    return (f"Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:\n\n"   # lo, hi = p.rango_recomendado
```

`rango_recomendado` es `(nivel-0.10, nivel+0.15)`; `por_nivel` usa
`holgura=0.25`. Con nivel 1,00 (catálogo real, sin embeddings):

```
rotulo : Lo más leído entre **0.90** y **1.15**:
niveles de los libros listados: ['B1', 'B2']      (B1 = 0.80, B2 = 1.20, ninguno dentro del rótulo)
```

Y `si_no_hay` dice "No hay libros etiquetados entre 0.90 y 1.15" cuando lo que
no hay es dentro de ±0,25. Arreglo: pasar `holgura` derivada del rango, o
rotular con el rango que de verdad se usó.

### M2. Tres números distintos para el mismo "vistazo rápido"

`ui.py:2447` (texto que ve el usuario): «El vistazo toma unas **80** ventanas»;
`ui.py:1187-1188`: `RAPIDO_CAPITULOS = 30`, `RAPIDO_VENTANAS = 2` → **60**;
`ui.py:1204` (docstring): «hasta **40** capitulos». El comentario justo encima
de las constantes (`ui.py:1179-1186`) explica que se bajó de 40 a 30 y que "40 se iba a 23 s";
el docstring y el texto de la interfaz no se actualizaron.

### M3. Tres manejadores levantan excepción con archivos propios mal formados (pregunta 4)

Reproducido con `c_bordes.py`:

```
LEVANTA _reanudar con sesion.json = []           AttributeError: 'list' object has no attribute 'get'
LEVANTA _reanudar con sesion.json = "hola"       AttributeError: 'str' object has no attribute 'get'
LEVANTA _perfil_inicial con nivel='abc'          TypeError: unsupported operand type(s) for -: 'str' and 'float'
LEVANTA _mover(libro, 'abc', 1)                  ValueError: invalid literal for int() with base 10: 'abc'
```

- `ui.py:912` `return d if d.get("ruta") and ...` — `_leer_sesion` solo atrapa
  `(OSError, ValueError)`; un JSON válido que no sea objeto revienta
  `_reanudar`, que corre en **`demo.load`**: la página entera arranca con
  error para ese lector hasta que borre el archivo.
- `ui.py:915-923` — `perfil.cargar` atrapa `JSONDecodeError`/`TypeError` al
  construir, pero no valida tipos; `_describir` hace aritmética con `nivel`.
- `ui.py:874` `int(idx) + paso` — `_mover` no pasa por `_cap` como hacen
  `_capitulo` y `_medir`.

Son archivos que escribe la propia app y no un usuario, así que son bordes; pero
la cabecera de `ui.py` promete que *ningún* manejador levanta. Arreglo:
`isinstance(d, dict)` en `_leer_sesion`; validar `nivel` numérico en
`perfil.cargar`; `_mover` vía `_cap`.

### M4. Vaciar «¿Cuántos te propongo?» enseña un error de Python

`gr.Number.preprocess` devuelve `None` si el campo está vacío (comprobado en
6.26). `ui.py:606` y `:697` hacen `int(n)` dentro del `try`, así que no
revienta, pero el lector lee:

```
[!] int() argument must be a string, a bytes-like object or a real number, not 'NoneType'
```

Arreglo: `n = int(n or 10)` antes del `try`.

### M5. CSS muerto y variables que no pintan nada (pregunta 2)

Comprobado contra el frontend compilado de Gradio 6.26
(`gradio/templates/frontend/assets/*`):

- `ui.py:372` `.tab-nav button.selected{...}`: **no existe `tab-nav`** en
  6.26 (0 apariciones). La pestaña elegida se pinta con
  `.selected.svelte-11gaq1{color:var(--color-accent)}`; lo que la salva es la
  redefinición de `--color-accent` en `paletas.py:273`, cuyo propio comentario
  ya dice que "la regla vieja dejo de enganchar". La regla vieja sigue ahí.
- `paletas.py:288` `label,.label-wrap,.svelte-1gfkn6j{...}`: la clase
  `svelte-1gfkn6j` no existe en 6.26 (0 apariciones); es un hash de otra
  versión.
- `ui.py:353-360` `.gr-box`, `.gr-button`, `.gr-input`, `.gr-text-input`: clases
  de Gradio 3, 0 apariciones.
- `paletas.py:37,63,89,115,141` `--ll-acento-claro`: declarada en las cinco
  paletas, **no la usa ninguna regla** de `ui.py` ni de `paletas.py`.
- `ui.py:778,796` `font-size:var(--ll-lectura, 19px)`: `--ll-lectura` no la
  declara nadie; vive del valor de respaldo.
- `paletas.py:209-212` `--link-text-color*`: cualquier enlace dentro de
  Markdown cae bajo `.prose *{color:var(--ll-texto) !important}`
  (`paletas.py:286`), que gana por `!important` y especificidad; las cuatro
  variables de enlace no pintan nada dentro del `.prose`. Hoy no hay enlaces
  en el Markdown de la app, así que es inocuo.

### M6. Cuatro elementos con el mismo `id="ll-lector"` en la misma página

`construir()` emite 4 `gr.HTML` con `id="ll-lector"` (los tres fragmentos de
«Mi nivel» vía `_html_lectura` en `ui.py:2321` más el lector) y 4 copias del
`<style>` de `_CSS_LECTOR`. Los ids duplicados son HTML inválido; el
`closest('#ll-lector')` del JS de selección funciona igual, y seleccionar una
palabra en un fragmento del cuestionario la copia a la caja de la pestaña Leer
sin que el lector lo vea. Arreglo: `class="ll-lector"` en los fragmentos.

### M7. Esquinas: la corrección de "14 px para todo" no llega al lector ni a la voz

`ui.py:323` fija `_RADIO = "14px"` "para TODAS las paletas". `_CSS_LECTOR`
(`ui.py:776`) y `_CSS_VOZ` (`ui.py:1898`) ponen `border-radius:10px` después y
ganan (`g_css.py`, punto 5).

### M8. Documentación y código que ya no dicen lo mismo (pregunta 3)

- `AGENTS.md:184-188`: «Pendiente para Codex, sin hacer: la llamada de
  `lexicon.py` va sin `reasoning.effort`». `lexicon.py:82` declara
  `ESFUERZO_RAZONAMIENTO = "low"` con su medición y `lexicon.py:514` lo pasa:
  `reasoning={"effort": ESFUERZO_RAZONAMIENTO}`. Hecho y sin cerrar en el
  documento que se pide leer antes de tocar nada.
- `ui.py:3-9`: la cabecera enumera cinco pestañas; hay ocho (faltan «Mis
  libros», «Mis palabras», «Colores»).
- `pruebas_extremas.py:1413-1427` `_no_se_pierden_apuntes`: el docstring dice
  «Dos hilos x 200 usos... el contador llega a 400» y el `assert n == 0`
  comprueba lo contrario (que el sin-tope no cuenta). El nombre de la prueba
  impresa, «el codigo sin tope no gasta contador», sí es el correcto.
- `pruebas_extremas.py:1370-1385` `_cupo_se_agota` prueba `permite` +
  `apuntar`, el par que `cuentas.consumir` sustituyó y que `ui.py` ya no llama
  (grep: solo las pruebas los usan). Sigue siendo válido, pero cubre el camino
  viejo, no el vivo.

### M9. El contador sigue subiendo después de agotar el cupo, y el aviso de tope siempre dice "60 minutos"

`cuentas.consumir` incrementa y luego rechaza (`total > cuenta.tope`): con tope
3, `gastado` llega a 4, 5, 6... (`e_motivo.py`). `queda()` lo tapa con
`max(0, ...)`, así que es cosmético. `_mensaje_limite(idioma, 60)` se llama
siempre con 60 aunque la ventana esté a punto de vencer.

---

## NOTAS

- **N1.** `_abrir_del_catalogo` → `_descargar_gutenberg`: `RUTA_LIBROS.mkdir`
  (`ui.py:636`) está fuera del `try`; un `PermissionError` escaparía. No
  reproducido (aquí se puede escribir).
- **N2.** `_analizar_libro`: `p.perfil_de_texto(...)` (`ui.py:1242`) no está
  en `try`; un `RuntimeError` de torch (memoria) saldría hacia Gradio. Lo
  mismo en `_medir` con excepciones que no sean `ValueError`/`FileNotFoundError`.
- **N3.** `_diagnostico`: `config.estado()` lee `.env`/`CLAVES.txt` sin
  `try`; un archivo con codificación rara tumbaría la pestaña Estado.
- **N4.** Los mutantes C18 y C21 "fallaron" por `FileNotFoundError` del
  diccionario (S2), no por el `assert` previsto; en el árbol real, con el
  `.db` presente, fallarían por el `assert`. Se dejan como controles válidos
  con esa salvedad.
- **N5.** `_opacidad_no_borra_el_texto` compone `--ll-texto` sobre `--ll-fondo`,
  pero las opacidades `.78`/`.85` de `_CSS_CUADERNO` y `_CSS_BIBLIO` se pintan
  sobre `--ll-panel`. En las claras el panel es más claro que el fondo, así
  que la medida es ligeramente optimista; no se ha encontrado un caso que baje
  de 4,5.
- **N6.** Sin chrome-devtools (el MCP no respondió en 1800 s) no se ha medido
  contraste en navegador; todo lo de CSS se ha verificado sobre el HTML/CSS
  que emite la app y sobre el frontend compilado de Gradio 6.26.

---

## OK — comprobado y correcto

Ejecución de suites (con `OPENAI_API_KEY=sk-dummy-no-gastar`):

- `pruebas_extremas.py`: 216 pruebas, exit 0 (27 s). `pruebas_ficha.py`,
  `pruebas_perfil.py`, `tests_smoke.py`: exit 0.
- `pruebas_integracion.py`: **27 pasos, exit 0**, cargando el modelo v4 y el
  diccionario reales una vez: abrir *Alice*, navegar, medir («/ 2.00»),
  consultar una palabra sin red, cuaderno, reanudar en el capítulo exacto,
  frase para la voz. `validar_local.py` se ha leído (regex del nivel, patrón
  `?`, baseline con Spearman y parcial, validación que puede suspender) y no
  se ha ejecutado: necesita el corpus de British Council.
- La app arranca con `construir().launch(...)` en 127.0.0.1:7861 sin clave
  válida: HTTP 200 (248 KB) y ningún recurso pesado cargado
  (`_puntuador/_catalogo/_consultor` en `None` tras `construir()`; el control
  C23 demuestra que la prueba lo detectaría).

Pruebas que **sí** cazan su regresión (mutantes de control fallidos): cupo por
perfil bajo carrera (C9), contraste de paletas (C10), escapado del lector
(C11), `allowed_paths` (C14), coherencia `_cefr`/`anchor_cefr` (C16), tope del
encabezado de la ficha (C17), puerta de pago de la sinopsis (C18), `hay_codigos`
(C21), posición y apertura del acordeón de entrar (C22), arranque perezoso
(C23), aviso de afinidad baja (M26).

Manejadores probados en borde que devuelven texto y no levantan (`c_bordes.py`):
`_capitulo(libro, "abc")`, `_buscar`/`_recomendar` con `n=None`,
`_desde_cuestionario` con valor no numérico, `_ficha_libro` y
`_repintar_grafica` con análisis guardado `{}` o `[]`, `_entrar(None, None)`.
Además: `_abrir` atrapa `Exception` (pypdf/zipfile), `_practicar` atrapa
`Exception`, `cuaderno`/`biblioteca`/`voz.registrar_fallos`/`puntos_debiles`
nunca lanzan (comprobado por lectura y por la suite), `_guardar_sesion` y
`_guardar_analisis` se callan ante `OSError`, `_css_paleta` cae a la paleta
por defecto.

Inyección de `gr.Request`: funciona en `_nivel_desde_libro`, `_desde_muestra`
y, por firma, en todos los demás manejadores con `peticion` posicional
(`_entrar`, `_salir`, `_abrir`, `_capitulo`, `_consultar`, `_practicar`,
`_debiles`, `_mis_palabras`, `_repasar`, `_mis_libros`, `_seguir_leyendo`,
`_perfil_inicial`, `_reanudar`, `_de_que_trata`, `_analizar_libro`). El único
roto es C1.

Contador concurrente: `cuentas.consumir` comprueba e incrementa bajo
`_CANDADO` con escritura atómica (`os.replace`); 20 hilos con cupo 2 pasan 2;
`_sumar` devuelve `None` y deja pasar si el disco falla. `_dentro_del_limite`
bajo `_CANDADO_GASTO`, con limpieza a partir de 5.000 IPs. `_CODIGO_SESION`
bajo `_CANDADO_CODIGO` y nunca viaja al navegador.

CSS/paletas: `paletas.css` redefine `--color-accent`, y en 6.26 es exactamente
lo que usa la pestaña elegida (`.selected.svelte-11gaq1{color:var(--color-accent)}`);
`label.selected` existe en 6.26 (el componente Radio alterna la clase
`selected` en el `label`), así que `label.selected *{color:var(--ll-boton-texto)}`
engancha; `.secondary-wrap`, `.wrap-inner`, `.label-wrap` existen. Las cinco
paletas declaran las mismas 19 variables; `_contraste_suficiente` compone alfa
y pilas de capas correctamente (verificado con el control C10, que da 1,86
cuando se aclara el acento de menta). `_CSS_LECTOR` usa `var(--ll-borde)` y
`var(--ll-lector-texto)`; `_CSS_CUADERNO` y `_CSS_BIBLIO` no llevan color
clavado. `_grafica_analisis` toma los colores de `_colores_paleta`.

Firmas y versiones: `Blocks.launch(theme=...)`, `Textbox` sin
`show_copy_button`, `demo.load(None, None, None, js=...)`, `gr.Tabs(selected=...)`
como salida, `Number.preprocess` con `minimum/maximum`, todo válido en 6.26.
`cuentas.problemas()`/`declaradas()` existen y `_diagnostico` las usa;
`_analizar` alimenta a `_tabla`. `ficha.RELLENO_RE`, `capitulos_de_cuerpo`,
`dificultad_global`, `sin_licencia` existen y `ui.py` los llama con la firma
correcta. `scoring._parece_repo_hf` se importa desde `ui._diagnostico` y
existe. Escala pública 0..2 en todas las fronteras (`Perfil.nivel`,
`catalogo.por_nivel`, `lexicon.consultar(nivel)`); la 0..5 solo en
`scoring.py` (y `_cefr` la reconstruye multiplicando por 2,5, coherente con
`public_score`).

Sin `OPENAI_API_KEY`: `_diagnostico` lo dice; `lexicon.consultar` y
`voz.practicar` degradan a avisos; la sinopsis avisa (cuando el diccionario
existe, ver S2); buscador, medición, lector, ficha contada y cuaderno no tocan
red (confirmado por la integración con clave falsa).

---

## Pregunta 5 — ¿Qué avergonzaría al autor delante de un profesor?

En orden de lo que se ve primero:

1. **El profesor rellena el cuestionario en el Space, ve "Guardado", recarga y
   la app le dice que todavía no ha fijado su nivel** (C1). Y si dos personas
   de la clase lo hacen a la vez, sus perfiles —con nombre— se escriben en el
   mismo archivo. Es el paso 1 de los seis, en la primera pantalla.
2. **Pulsa «Sorpréndeme» y el rótulo dice "entre 0.90 y 1.15" sobre una lista
   de libros B1 (0.80) y B2 (1.20)** (M1). Un profesor de ciencia de datos
   mira exactamente esa línea.
3. **Consulta una palabra sin haber entrado y la app le dice "Sin clave de
   OpenAI"** (S3), en una app que tiene clave. Y si entra y consulta, el cupo
   baja aunque la respuesta venga de caché. La regla "el tope son llamadas de
   pago" del docstring de `cuentas.py` no es verdad.
4. **"Ningún manejador levanta excepciones hacia Gradio" es la primera frase
   de `ui.py`**, y el botón «¿De qué trata?» enseña un traceback si falta un
   archivo que ese botón no usa (S2).
5. **Las 216 pruebas "pasan" con cualquier contraseña** (S1). Es lo peor si el
   profesor pregunta "¿y cómo sabes que la puerta funciona?": la respuesta
   honesta hoy es "porque lo probé a mano". Y el propio envoltorio `prueba`
   tiene un docstring de veinte líneas explicando que ya se arregló este
   mismo problema para las listas.
6. La suite de "no revienta" **factura a OpenAI** en cada `python pruebas_extremas.py`
   (S4). Poco, pero un profesor que lea la palabra "gratis" en la pestaña
   Estado y luego vea la llamada a `gpt-4o-mini` en un test no lo olvida.
7. Los comentarios. Hay tres números para el vistazo rápido (M2), un
   `AGENTS.md` que da por pendiente lo que ya está hecho (M8), una cabecera
   con cinco pestañas de ocho, y un bloque de `_CSS_VOZ` con el mismo gris
   que un comentario a cien líneas de distancia cuenta haber desterrado (S5).
   El proyecto documenta muchísimo —eso es un mérito real— y por eso mismo
   cada comentario desactualizado pesa más que en un proyecto mudo.

Lo que **no** avergüenza, y conviene decirlo: la degradación sin clave es real
y está probada de punta a punta; el aislamiento por sesión está bien pensado
(solo un manejador se le escapó); el contador de cupo aguanta veinte hilos; la
carga perezosa es de verdad; el CSS de paletas está a un `#ll-voz` de ser
consistente; y el recorrido lector completo —abrir, medir, consultar,
recordar, reanudar— encadena con el modelo real.
