# Informe de auditoría 13 (Fable) — árbol `e630dde`

Auditoría final antes de entregar, **a ciegas**: no se leyó `auditoria/` ni `git log` para saber qué se acababa de tocar (la única excepción son las notas históricas que `AGENTS.md` obliga a leer). Todo lo afirmado está ejecutado; la salida literal va con cada hallazgo. Scratchpad de trabajo: `C:\Users\laura\AppData\Local\Temp\claude\...\scratchpad` (copias del árbol, mutantes, salidas).

**Cambios ajenos durante la auditoría:** a las 15:37–15:38 aparecieron en el árbol `requirements.txt` modificado (añade `huggingface_hub>=0.25,<2`) y `tools/desplegar_app.py` nuevo. No son míos y no se auditaron; todo lo de abajo es sobre `e630dde`.

**No se gastó dinero.** `pruebas_voz.py` y `pruebas_lexicon.py` solo se corrieron con `openai.OpenAI` sustituido por un espía que corta toda llamada; la app se arrancó con `OPENAI_API_KEY=sk-clave-falsa-de-auditoria`. Lo desplegado en el Space **no se auditó** (es más viejo que este árbol): todo es código local.

## Recuento

| Gravedad | Cuántos |
|---|---|
| Crítico | 0 |
| Serio | 8 (S1–S8) |
| Menor | 14 (m1–m14) |
| Notas | 10 (n1–n10) |

Mutantes: 50 aplicados, **34 cazados, 15 sobreviven, 1 equivalente** (tabla al final).

---

## Serios

### S1 · «Sorpréndeme» dice a la vez que hay diez libros en el rango y que no hay ninguno

`app/ui.py:646-676` y `app/ui.py:869-876`.

```python
def _tabla_libros(libros, aviso: str = "") -> str:
    ...
    if aviso:
        filas += ["", f"_{aviso}_"]
```
```python
    si_no_hay = (f"No hay libros etiquetados entre {lo:.2f} y {hi:.2f}. Prueba "
    ...
    return (f"Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:\n\n"
            + _tabla_libros(libros, si_no_hay), _opciones_libros(libros))
```

`_recomendar` pasa `si_no_hay` como `aviso` pensando que solo se pinta cuando la lista está vacía, pero `_tabla_libros` lo añade **siempre** que sea no vacío. Resultado visto en el navegador (perfil 1,13, clic en «Ver libros para mi nivel →»), literal del árbol de accesibilidad:

```
uid=3_11 StaticText "Lo más leído entre "  uid=3_12 "0.88"  " y "  "1.38"  ":"
uid=3_16 StaticText "▸ 10 de 10" " se abren aquí mismo, ..."
   (diez filas: Metamorphosis, ..., An Occurrence at Owl Creek Bridge)
uid=3_74 StaticText "No hay libros etiquetados entre 0.88 y 1.38. Prueba a describir lo que te
        apetece leer en el buscador de arriba: ahí sí se ajusta a tu nivel sin exigir una
        coincidencia exacta."
```

Es la segunda pantalla del recorrido de la demo (`§8.2`) y se contradice sola. **Arreglo:** en `_recomendar`, `_tabla_libros(libros, si_no_hay if not libros else "")`, o que `_tabla_libros` solo use `aviso` en la rama vacía y acepte un segundo parámetro para las notas al pie legítimas de `_buscar` («Se descartaron N resultados por parecido bajo»).

### S2 · La curva «libro entero» tira 38 de los 98 capítulos de *Los hermanos Karamazov* (y 12 de 13 de la *Alicia* ilustrada) por la cabecera corrida de Gutenberg

`app/ficha.py:143-172` (`_es_boilerplate`), `app/ficha.py:336-342` (`capitulos_de_cuerpo`), `app/reader.py:47-52` (`_titulo_capitulo`).

```python
    cabeza = " ".join(limpio.split()[:400])
    if not _BOILERPLATE_RE.search(cabeza):
        return False
    # Una novela puede mencionar Gutenberg de pasada ...
    return capitulo.palabras < 3000 or len(_BOILERPLATE_RE.findall(cabeza)) >= 2
```

Los epub de la generación `pg28xxx` de Gutenberg (formato viejo) llevan **en cada archivo** la línea visible «The Project Gutenberg eBook of …». Por eso todo capítulo de menos de 3.000 palabras cae como «licencia». Medido sobre 19 epub reales del catálogo (los 9 cacheados en `~/.literalevel/libros` más 10 descargados al scratchpad):

```
pg28054.epub The Brothers Karamazov  caps=98  cuerpo=59  -> 38 capitulos de >=500 palabras con titulo normal descartados
   (1, 'Chapter I.  Fyodor Pavlovitch Karamazov', 1345, 'boiler')
   PRIMERAS 60 PALABRAS: The Project Gutenberg eBook of The Brothers Karamazov by Fyodor Dostoyevsky
   Chapter I. Fyodor Pavlovitch Karamazov Alexey Fyodorovitch Karamazov was the third son ...
pg28885.epub Alice's Adventures in Wonderland / Illustrated  caps=13  cuerpo=1  titulos_PG=12
   1..12 "The Project Gutenberg eBook of Alice's Adventures in Wonderland, by By"  (boiler)
   13 'THE END' 5161
```

`PG28054` es *The Brothers Karamazov* del catálogo (B2, 7.836 descargas) y salió **tercero** en el «Sorpréndeme» de la demo; `PG28885` es la segunda *Alicia* del catálogo (B1). Para el primero, «Leer el libro entero» dibuja 59 de 98 capítulos y el resumen afirma «el modelo recorre cada capítulo entero»; para el segundo, el índice son trece entradas «The Project Gutenberg eBook of…», la curva se calcula sobre un solo capítulo y la ficha sobre ese mismo. Los otros 17 epub (formato nuevo) solo llevan esa línea en el primer archivo y salen bien. **Arreglo:** en `reader._titulo_capitulo` descartar candidatos que empiecen por «The Project Gutenberg eBook»; y en `_es_boilerplate` no contar una mención en las primeras ~20 palabras como prueba de licencia cuando el capítulo tiene un encabezado de capítulo real (o quitar esa cabecera corrida en `_limpiar_html`, que es donde nace).

### S3 · Se gasta tts-1 sin cobrar: la explicación en caché devuelve el uso aunque el audio se pague

`app/ui.py:2122-2123`:
```python
    elif puede and getattr(r, "desde_cache", False):
        cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))
```
`app/lexicon.py:670-679` (clave del audio por `palabra_superficie` tal cual) frente a `app/lexicon.py:692-698` (clave de la explicación por `lema_buscado` + oración). `desde_cache` solo mira la explicación; el audio se pide con la superficie literal, así que `Fetters`, `FETTERS`, `fetters.` aciertan la explicación (mismo lema, misma frase), fallan el audio y **llaman a tts-1 con el uso devuelto**. Reproducido con espía sobre `openai.OpenAI`, diccionario y caché reales (`scratchpad/fuga_tts.py`):

```
'fetters'    llamadas nuevas=[('tts', 'fetters,'), ('responses', ...)]  gastado 0->1  desde_cache=False
'Fetters'    llamadas nuevas=[('tts', 'Fetters,')]  gastado 1->1  desde_cache=True
'FETTERS'    llamadas nuevas=[('tts', 'FETTERS,')]  gastado 1->1  desde_cache=True
'fetters.'   llamadas nuevas=[('tts', 'fetters.')]  gastado 1->1  desde_cache=True
TOTAL llamadas de pago: 5 | usos cobrados al final: 1
```

Es exactamente el invariante que `cuentas.py` declara («el cupo baja si y solo si se gasta dinero») y que la prueba `_el_cupo_cuadra_con_las_llamadas_de_pago` (`pruebas_extremas.py:2257`) dice proteger: su `ConsultorDoble` no modela el audio. El coste unitario es ínfimo y el cubo por hora (30/IP) lo acota, pero es un camino de gasto no contabilizado. **Arreglo:** que `ResultadoLexico` diga si hubo llamada (`llamadas_de_pago: int`, o `desde_cache` solo cuando ni explicación ni audio salieron a la red), y que `ui` devuelva el uso solo si es cero; de paso, normalizar `texto_audio` (`.lower().strip(".,;:!?")`) para que las variantes acierten en caché.

### S4 · `_consultar` deja escapar `sqlite3.DatabaseError` hacia Gradio y se queda con el uso cobrado

`app/ui.py:2098-2104`:
```python
        r = consultor().consultar(palabra, oracion, nivel, idioma=idioma,
                                  usar_openai=puede)
    except (FileNotFoundError, OSError) as e:
        cuentas.devolver(...)
```
`CacheLexico.__init__` (`app/lexicon.py:385-395`) ejecuta `CREATE TABLE` sobre `~/.literalevel/lexicon.db`; si ese archivo está corrupto —disco efímero del Space cortado a media escritura— lanza `sqlite3.DatabaseError`, que no desciende de `OSError`. `_de_que_trata` sí lo atrapa (`except Exception`, línea 1594); `_consultar` no. Reproducción:

```
ConsultorLexico(ruta_cache corrupta) -> DatabaseError : file is not a database
_consultar LANZA hacia Gradio: DatabaseError : file is not a database
```

Y como `_puede_pagar` ya cobró, el lector pierde el uso. Rompe la promesa de cabecera de `ui.py` («Ningún manejador levanta excepciones hacia Gradio»). **Arreglo:** `except Exception as e` en ese `try`, con la misma devolución.

### S5 · Cifra publicada inconsistente consigo misma: «31 textos» frente a 36

`entrega/documento.tex:2064-2065` y `entrega/documento.md:867`:
> Medido cambiando una cosa y sólo una: con saltos de línea sobreviven **31 textos en vez de 47**, y A1 se queda con uno solo

Pero el Cuadro 9 (`cuad:conjuntos`), §7.4 («sobreviven **36 de esos 47**»), `PENDIENTES.md` («**36**») y la salida real del guion dicen 36:

```
textos que pasarian el filtro COMPLETO (con saltos de linea): 36  <- el que aplica la app
```

Mi recuento independiente con el filtro estricto por nivel: A1 1, A2 4, B1 9, B2 10, C1 12 = **36**; los dos A1 que caen lo hacen por `maquetado_de_lista` (así que «A1 se queda con uno solo» y «dos de los tres caen por maquetado» son ciertas; solo el 31 es viejo, de antes de `PESO_MAQUETADO`). El comentario de `validar_local.py:565` («con salto 31 textos») arrastra la misma cifra. **Arreglo:** 31 → 36 en los tres sitios.

### S6 · Pruebas que no prueban: 15 mutantes sobreviven, varios en correcciones que las auditorías anteriores dieron por protegidas

Banco: copia real del árbol (`app/`, `pruebas_extremas.py`, `main.py`, `catalogo_recomendaciones.csv`, `tests_smoke.py`, `pruebas_ficha.py`, `pruebas_perfil.py`), control verde en la copia (246/246, 32 s), un mutante por ejecución en subproceso, fallo atribuido por nombre de prueba. Tabla completa al final. Los que importan:

| Mutante | Qué rompe | Quién debería cazarlo |
|---|---|---|
| M09 `if config.falta():` → `if False:` en `_consultar` | vuelve a **cobrar usos sin clave** (el fallo cerrado en la auditoría 12) | nadie: ninguna prueba combina perfil + clave ausente + cupo |
| M10 / M39 `va_a_costar = True` (sinopsis y consulta) | vuelve a gastar el cubo por hora de la IP con visitantes sin perfil (auditoría 12) | nadie: `_voz_y_sinopsis_respetan_su_tope` prueba con la puerta quitada |
| M35 `limpio = capitulo.texto` en `_es_boilerplate` | deshace la corrección del 9 sep («se perdían libros enteros») | nadie en las suites gratuitas (`pruebas_ficha` tampoco) |
| M38 `cliente = self._cliente()` ignorando `usar_openai` | **la puerta de pago dentro de `lexicon.py` deja de existir** | solo `pruebas_lexicon.py`, que cuesta dinero, y ni así (ver abajo) |
| M50 sin mirar la caché antes de pagar | paga dos veces la misma palabra | nadie sin API |
| M26 `tope == 0` → negar | un perfil **sin límite** queda bloqueado en todo lo de pago | nadie: las pruebas del `jefe:0` solo miran `queda()` y `gastado()` |
| M06 ventana de 1 s en `_dentro_del_limite` | el tope por hora dura un segundo | nadie: nunca se prueba que una marca de hace 30 min siga contando |
| M29 `MIN_WORDS` → 1 en `continuous_prose` | se puntúan textos de 20 palabras | nadie (el «muy corto» de `tests_smoke` cae por `pocas_frases`) |
| M46 / M47 sin recorte de `LIMITE_ORACION` / `LIMITE_FRASE_VOZ` | la oración viaja entera a OpenAI | nadie (el Cuadro 5, T8, presume de este recorte) |
| M49 `inicial = 0` en `_abrir` | se abre siempre en la portadilla | nadie (la integración solo mira `idx is not None`) |
| M14 sin candado en `puntuador()` | dos modelos en memoria | nadie |
| M20 quitar `concurrency_id` de `_medir` | `_la_cola_admite_a_mas_de_uno` exige `n < 4` y hay 5 | nadie |

Y **`pruebas_lexicon.py` pasa con la API bloqueada**: con el espía que lanza en `responses.parse` imprime `RESULTADO: TODO OK` tras haber intentado dos llamadas (`LLAMADAS INTERCEPTADAS: 4 ['ctor', 'ctor', 'responses.parse', 'responses.parse']`). Es una suite que gasta dinero y no asevera nada sobre lo que compra. `pruebas_voz.py`, en cambio, falla 5 comprobaciones con el espía: esa sí prueba.

**Arreglo:** una prueba por fila; para M38/M50, un `ConsultorLexico` real con caché temporal y `openai.OpenAI` espiado (como `scratchpad/fuga_tts.py`), sin red.

### S7 · «Mi nivel» promete un rango y «Sorpréndeme» filtra y anuncia otro

`app/perfil.py:41-43` (`rango_recomendado` = nivel −0,10 / +0,15) y `:266` («Te buscaremos lecturas entre …») frente a `app/ui.py:815-876` (`HOLGURA_POR_NIVEL = 0.25`). En el navegador, mismo perfil, dos pestañas seguidas:

```
Mi nivel:     "Te buscaremos lecturas entre " "1.03 y 1.28" ": cómodas pero con algo de reto."
Sorpréndeme:  "Lo más leído entre " "0.88" " y " "1.38" ":"
```

El comentario de `HOLGURA_POR_NIVEL` cuenta que este mismo desajuste se corrigió «para que el rótulo y el filtro no puedan volver a separarse»; se corrigió en la pestaña 2 y se dejó en la 1. **Arreglo:** que `perfil.describir` no anuncie un rango, o que anuncie `nivel ± HOLGURA_POR_NIVEL`.

### S8 · Archivos propios con la «forma» que el validador acepta y aun así tumban manejadores (uno en `demo.load`)

- `app/ui.py:1353-1372` valida `filas[*].capitulo/dificultad` pero `_resumen_analisis` (`:1770-1799`) exige `datos['ventanas']`, `['palabras']`, `['titulo']`, `['autor']`, y `_ficha_libro` (`:1506`) suma `dificultad` sin comprobar el tipo:
  ```
  _analizar_libro LANZA: KeyError : 'ventanas' | json: {"filas": [{"capitulo": 1, "dificultad": 1.0}]}
  _analizar_libro LANZA: TypeError : unsupported operand type(s) for +: 'int' and 'str' | json: {"filas": [{"capitulo": 1, "dificultad": "abc", ...
    _ficha_libro LANZA: TypeError unsupported operand type(s) for +: 'int' and 'str'
  ```
- `app/ui.py:1092`: `os.path.exists(d["ruta"])` con `ruta` lista o dict lanza `TypeError`, y `_leer_sesion` lo llaman `_reanudar` (en `demo.load`) y `_capitulo`:
  ```
  _reanudar LANZA: TypeError : stat: path should be string, bytes, os.PathLike or integer, not list | json {"ruta": ["x"]}
    _capitulo LANZA: TypeError ...
  ```
  Es el caso que la auditoría anterior cerró para `[]`/`"hola"`/`3`, pero con la lista **dentro** del objeto. Probabilidad baja (los escribe la app), gravedad alta cuando pasa (la página arranca en error). **Arreglo:** `isinstance(d.get("ruta"), str)` en `_leer_sesion`; en `_analisis_guardado` exigir `isinstance(f["dificultad"], (int, float))` y `datos.setdefault` de `ventanas/palabras/titulo/autor`.

---

## Menores

**m1 · «232 pruebas» y «27 pasos»: la suite tiene 246.** `entrega/documento.tex:743, 820, 908`, `entrega/estrategia.md:202, 283, 455`, `README.md:154`, `PENDIENTES.md:97`. Salida real: `Las 246 pruebas extremas pasan`. (Los 27 pasos de integración sí cuadran.)

**m2 · La figura de la escala mezcla el punto y la coma decimal.** `entrega/documento.tex:436-442`: `\foreach \x in {0.20,0.60,1.00,1.40,1.80}{ ... {\x}}` imprime el valor crudo, y los extremos van escritos a mano `{0,00}` `{2,00}`. Texto extraído de `documento.pdf`: `0.20 0.60 1.00 1.40 1.800,00 2,00`. Ningún `grep` de cifras lo ve. **Arreglo:** `\pgfmathprintnumber[fixed,precision=2]{\x}` (ya hay `use comma`) o lista de pares valor/etiqueta.

**m3 · Frase rota en `documento.md:283-284`** («rechazo si hay dos o / de una sexta parte de las palabras vive en líneas de maquetado»): resto de la edición «dos o más viñetas» → 17,5 %. Además «una sexta parte» es 16,7 %, no el 17,5 % del código y del `.tex`.

**m4 · Mismo resto en el `.tex`, §7.7** (`documento.tex:2061-2062`): «sus dos comprobaciones —dos palabras en líneas de maquetado, o más de un tercio…». Debe decir «más del 17,5 % de las palabras».

**m5 · La casilla «Solo libros que pueda leer — Deja fuera lo que te quede muy grande o muy pequeño» no deja fuera nada.** `app/ui.py:2714-2718` frente a `app/catalogo.py:203, 235` (`peso_nivel=0.3`, reponderación). Medido: `nivel 0.2 -> ['A1'x6, 'B1'x4]`; `nivel 2.0 -> ['C2','C2','C2','C1','C1','C2','C2','B1','B1','B1']`. El documento (§8.2) dice lo contrario que la etiqueta: «Lo que devuelve la búsqueda **no está filtrado por el nivel del lector**». Es una etiqueta que promete más de lo que hace, la categoría que la §3.1 presume de haber limpiado. **Arreglo:** «Acerca los resultados a mi nivel».

**m6 · Separador de miles inglés en la interfaz.** `app/catalogo.py:277` (`f"{len(self.df):,}"`), `app/ui.py:1167, 1180, 1205, 1239` (`{palabras:,}`). En la pestaña Estado: `Catálogo: 1,197 libros` en la misma app que dice «los 1.197 libros del catálogo»; en Leer, «130,104 palabras» y «2,143 pal.» frente al «130.104» del documento. **Arreglo:** `format(n, ",").replace(",", ".")` en un ayudante.

**m7 · Con una clave inválida la ficha repite dos veces «Sin clave de OpenAI»** y dice «sin clave» cuando sí hay clave (401). Visto en vivo: `uid=9_10` y `uid=9_11` idénticos. Causa: `_humanizar` (`app/ui.py:1917-1940`) mapea tanto «no se pudo generar audio: AuthenticationError» como «OpenAI no disponible: AuthenticationError…» al mismo texto y no se deduplica. **Arreglo:** `dict.fromkeys` sobre los avisos humanizados y una entrada propia para «clave rechazada».

**m8 · `main.py:10` y `README.md:133` afirman «No renombrar a `app.py`: chocaría con `app/`»** mientras `AGENTS.md` y `DESPLIEGUE.md` explican que es falso y que el Space corre justamente `app.py`. Tres documentos, dos verdades.

**m9 · El guion dice «0 herramientas te dicen si ese libro es para ti»** (`guion_video.md:80`, `guion_video.tex:247`) y el documento §8.5 (`documento.tex:2580`) reconoce que *TeakReader* «ya da nivel MCER por capítulo». Un evaluador que lea los dos lo verá.

**m10 · La diapositiva «Hallazgo 1» mezcla tandas.** `entrega/presentacion.tex:207-209` pone en la misma barra 1,061 (17 variables, tanda *recalculada*) con 0,93 y 0,67 (tanda *histórica*), que es la resta que las Conclusiones del documento dicen que «no se puede hacer» («Misma partición y misma semilla, sí; misma definición de las variables, no»).

**m11 · `_nivel_desde_libro` anuncia «tomando muestras de 8 partes»** (`app/ui.py:617`, `min(8, len(libro.capitulos))`) aunque `_muestra_de_libro` (`:563`) elija entre los capítulos de ≥300 palabras: con 12 capítulos cortos y 1 largo dice 8 y usa 1 (`trozos usados: 1 | mensaje diría partes = 8`).

**m12 · *Orgullo y prejuicio* (PG1342, el libro más descargado del catálogo) sale con 15 «capítulos» titulados por los pies de ilustración**: `'I hope Mr. Bingley will like it.    CHAPTER II.' 8438`, `'Covering a screen.    CHAPTER VIII.' 6862`, `'“The Post.”    CHAPTER XLVIII.' 9689`… porque el epub agrupa 3-5 capítulos por archivo y `_titulo_capitulo` (`app/reader.py:47-56`) toma el primer `<h*>`. No es un error de orden, pero el índice se lee raro en el libro con más papeletas de salir en una demo.

**m13 · `_la_cola_admite_a_mas_de_uno` (`pruebas_extremas.py:2190-2225`)** habla de «los cuatro manejadores que cargan el v4», hay cinco `concurrency_id="modelo"` y el umbral es `n < 4`: se puede quitar uno sin que falle (M20).

**m14 · `validar_local.py:565`** comenta «con salto 31 textos, A1 se queda en 1 y la validacion FALLA»: la cifra es la vieja (hoy 36), aunque la conclusión siga siendo cierta (A1 = 1 < `MINIMO_POR_NIVEL`).

---

## Notas

**n1 · El cuadernillo corre entero.** `notebook_proyecto.py` ejecutado de principio a fin en un directorio limpio (seaborn instalado en un `--target` aparte): `exit 0`, descarga CLEAR (4.724 × 28) y el catálogo, carga `MikeMaki1763/literalevel-v4` desde el Hub, y recalcula las cifras que el documento cita: `Regresión logística (3 variables clásicas) exactitud 0.313 | error ordinal 1.295`, `(17 variables) 0.352 | 1.061`, `XGBoost (17 variables) 0.340 | 1.081`, `Orden estrictamente creciente de A1 a C1: True`. `.py` y `.ipynb` son idénticos celda a celda (92/92; 53 de código, sin salidas guardadas). **Un aviso en stderr**: `Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN…` — en Colab saldrá igual; si «sin warnings» es literal, va un `HF_HUB_DISABLE_...` o un `huggingface_hub.utils.logging.set_verbosity_error()` antes de `from_pretrained`. Ni `drive.mount` ni rutas locales (solo se mencionan en el markdown que lo promete).

**n2 · `perfil.cargar` acepta `nivel: 1e400` y `"nan"`** → la pestaña dice «Tu nivel de lectura: **inf / 2.00**» y «Lo más leído entre **inf** y **2.00**». Archivo propio; `math.isfinite` lo cierra.

**n3 · `_registrar_lector` poda la mitad del diccionario cuando pasa de 5.000 sesiones** (`app/ui.py:120-124`), incluidas las vivas: esos lectores caen a la carpeta del `session_hash` y «pierden» sus datos hasta recargar.

**n4 · Los topes por hora van por `x-forwarded-for` o `client.host`**: detrás del proxy del Space, si la cabecera no llega, todos los visitantes comparten un cubo de 30. No verificable en local.

**n5 · `_descargar_gutenberg` (3 fuentes × 45 s) no tiene tope por IP** y ocupa un hueco de los 8 de la cola: ocho «Leerlo ahora» con ids distintos y sin red dejan la app sin huecos ~2 min. Sin coste, pero es la petición lenta que sí puede dejar sin servicio.

**n6 · Un 401 cobra el uso y no lo devuelve** (visto en vivo: `{"prof": 1}` tras una consulta con clave inválida). Es la decisión documentada en `_practicar`; solo se anota que el mensaje que ve el lector («Sin clave de OpenAI») no le dice que acaba de gastar uno.

**n7 · Diálogo de *Alice*: 73 % publicado, 74 % medido hoy** con `pg11.epub` (`dialogo=0.74`); *P&P* 28 % y *C&P* 31 % coinciden. Redondeo o versión del epub; no cambia nada.

**n8 · Velocidad reproducida en esta máquina** (con la app corriendo al lado): `puntuar (8 ventanas): 1.08s`, `7.77 v/s` en lotes de 64 — coherente con «0,96 a 1,04 s» y «8,19».

**n9 · `sólo` con tilde** en `documento.tex:2063` y `documento.md:867` (admitido, pero la RAE recomienda sin tilde y el resto del documento va sin ella).

**n10 · Lo que NO se pudo verificar:** el 13,96 % sobre 530 ventanas, los 487 ventanas/86 s de *Notes from a Dead House* (el epub no está cacheado), las cifras de Colab (38 textos, 0,829, 0,908, 97,2 %) —el propio documento lo declara— y cualquier cosa del Space desplegado.

---

## Tabla de mutantes

Control en la copia: `pruebas_extremas.py rc 0 32s []`, `tests_smoke.py rc 0`, `pruebas_ficha.py rc 0`, `pruebas_perfil.py rc 0`. «Cazado por» es el nombre de la prueba que imprime `FALLA`.

| # | Mutación | Resultado |
|---|---|---|
| M01 | `_dir_lector` → siempre `anonimo` | cazado: «dos sesiones no comparten carpeta», «dos lectores no se ven los datos», «los datos sobreviven a recargar», «sin localStorage no revienta» |
| M02 | `_registrar_lector` sin sanear el id | cazado: «sin localStorage no revienta» |
| M03 | `_registrar_lector` no guarda | cazado: «los datos sobreviven a recargar» |
| M04 | `_dir_lector` ignora la identidad | cazado: «los datos sobreviven a recargar» |
| M05 | tope `>=` → `>` | cazado: «el tope se respeta», «consultar por encima del tope…», «voz y sinopsis respetan su tope» |
| M06 | ventana de 1 s en `_dentro_del_limite` | **SOBREVIVE** |
| M07 | `_puede_pagar` → `True, ""` | cazado: las tres puertas + «el cupo cuadra» |
| M08 | no devolver en acierto de caché | cazado: «el cupo cuadra con las llamadas de pago» |
| M09 | cobrar aunque falte la clave | **SOBREVIVE** |
| M10 | `va_a_costar = True` en la sinopsis | **SOBREVIVE** |
| M11 | `_practicar` sin puerta | cazado: «el cupo cuadra», «la practica de voz pide codigo» |
| M12 | `_entrar` sin comprobar `c is None` | sobrevive, **equivalente**: `queda(None)` revienta dentro del `try` y `consumir` revalida la credencial; nada se abre. Aun así la prueba solo mira el texto |
| M13 | `_salir` no olvida | cazado: «salir olvida el perfil» |
| M14 | `puntuador()` sin candado | **SOBREVIVE** |
| M15 | `_medir` solo `ValueError`/`FileNotFoundError` | cazado: «medir con el modelo inalcanzable» |
| M16 | `_abrir` solo `OSError` | cazado: «extension no soportada», «pdf corrupto», «epub que no es zip»… |
| M17 | `::selection` en `yellow` | cazado: «el CSS no clava…», «ningun color literal» |
| M18 | `--ll-texto` gris en hielo | cazado: «todas las paletas son legibles», «la opacidad…» |
| M19 | `demo.queue(1)` | cazado: «la cola admite a mas de uno» |
| M20 | `_medir` sin `concurrency_id` | **SOBREVIVE** |
| M21 | `total > tope + 1` | cazado: «veinte peticiones…», «no se cobra lo que no se gasta» |
| M22 | no deshacer el rechazo | cazado: «no se cobra lo que no se gasta» |
| M23 | `_restar` baja de cero | cazado: «no se cobra lo que no se gasta» |
| M24 | `verificar` acepta cualquier clave | cazado: «contrasena con acentos», «clave mala no abre», «mayusculas» |
| M25 | tabla distingue mayúsculas | cazado: «el diagnostico avisa de un perfil repetido» |
| M26 | `tope == 0` → negar | **SOBREVIVE** |
| M27 | `PESO_MAQUETADO = 0` | cazado (extremas): «un capitulo dialogado con una lista…», «la ficha y el medidor…»; sobrevive en smoke |
| M28 | `PESO_MAQUETADO = 1` | cazado (extremas): «el filtro sigue rechazando menus…»; sobrevive en smoke |
| M29 | `MIN_WORDS` → 1 | **SOBREVIVE** (extremas y smoke) |
| M30 | «básico» solo A1 | cazado: «la banda nunca contradice a la letra»; sobrevive en smoke |
| M31 | epub ignora el spine | cazado: «el orden de los capitulos es el del spine» |
| M32 | orden de texto sin spine | cazado: «sin spine, los capitulos van en orden natural» |
| M33 | atributos exigen `id` antes de `href` | cazado: «el orden de los capitulos es el del spine» |
| M34 | media de medias | cazado: «la dificultad global es la media…», «el caso que destapo…»; sobrevive en `pruebas_ficha` |
| M35 | `_es_boilerplate` sin quitar la licencia | **SOBREVIVE** (extremas y ficha) |
| M36 | `perfil.cargar` sin validar `nivel` | cazado: «perfil con nivel no numerico» |
| M37 | `PESO_FRAGMENTOS = 0.5` | sobrevive en extremas; cazado por `pruebas_perfil` (`assert mixto.nivel == 1.27`) |
| M38 | `lexicon` ignora `usar_openai` | **SOBREVIVE** |
| M39 | `va_a_costar = True` en `_consultar` | **SOBREVIVE** |
| M40 | sinopsis no devuelve sin cliente | cazado: «el cupo cuadra con las llamadas de pago» |
| M41 | consulta no devuelve sin diccionario | cazado: «el cupo cuadra con las llamadas de pago» |
| M42 | `_leer_sesion` sin `isinstance` | cazado: «sesion.json que no es un objeto» |
| M43 | `_cefr` con `round` al par | cazado: «la interfaz y el contrato dan la misma letra» |
| M44 | `allowed_paths` = `~/.literalevel` entera | cazado: «allowed_paths: sirve el audio y nada mas» |
| M45 | `LIMITE_PALABRA = 40000` | cazado: «palabra larguisima no llena la pantalla» |
| M46 | sin recorte de `LIMITE_ORACION` | **SOBREVIVE** |
| M47 | sin recorte de `LIMITE_FRASE_VOZ` | **SOBREVIVE** |
| M48 | `_html_lectura` sin escapar | cazado: «script incrustado», «img onerror» |
| M49 | `_abrir` siempre en el capítulo 0 | **SOBREVIVE** |
| M50 | `lexicon` sin mirar la caché antes de pagar | **SOBREVIVE** |

---

## OK — lo que se comprobó y estaba bien

- **`validar_local.py`** (una sola vez, 1 min): 47 textos, A1 0,5040 (3) · A2 0,5561 (8) · B1 0,9276 (12) · B2 1,2414 (12) · C1 1,4952 (12), desviaciones 0,111/0,223/0,198/0,236/0,172, 2 sin cuerpo, 10 rechazados por «corto» (9 A1 + 1 B1), 36 pasan el filtro completo, baseline 0,860 / 0,807 / 0,668, modelo-longitud 0,732, `VALIDACION CORRECTA`. Coincide con Cuadros 11-13 del `.md`, 16-18 del PDF, `validacion.dat`, README, PENDIENTES, `modelo_v4/README.md` y el cuadernillo.
- **Rectas de compresión**: 4 medias de Colab → `0,7196x + 0,3760`; 5 locales → `0,667x + 0,411`. Escalón A1–A2 = 0,052. Aritmética publicada: 77/144, 140/144, 44,4 %/50 %, 16,8 h, 2,96 h, 5,14 h, 731,7 h = 30,5 d, 11,1 h a 0,29 MB/s, 22,4 min a 8 MB/s, 8,8 min a 3.362/min, 1,784−1,743 = 0,041: todo cuadra.
- **Figuras desde `.dat`**: *War and Peace* 362 capítulos, mín 1,333 en el 34, máx 1,990 en el 202, media 1,7346 → 1,735, tercios 1,723/1,733/1,747, media móvil centrada de 15 (desvío máximo 5·10⁻⁵ respecto a la columna), máximo de la móvil en el 289; *C&P* 1,679 (1,270–1,891); *Alice* 1,497 (1,296–1,878). Anclas de la figura de validación en su sitio.
- **Numeración cruzada**: baseline = Cuadro 13 del `.md` / 18 del PDF; velocidad = 16 / 21; validación = 11 / 16, tal como dicen README, estrategia y `validar_local.py`. Sin `??` en los tres PDF; los tres PDF son posteriores a su `.tex`; 13 diapositivas; guion 561 palabras / 3:44 (`tools/contar_guion.py`).
- **Contraste**: 85 parejas (17 × 5), mínimos 4,53 (hielo/botón) y 3,11 (menta/título-3), exactamente lo publicado. Medido además en el navegador (hielo y papel): pestaña seleccionada 12,13 / 4,61, casilla elegida 4,53 / 4,65, prosa 15,4 / 10,9, entradas 14,9 / 11,0. Sin errores ni avisos en consola.
- **Identidad y aislamiento, en vivo con `PORT` puesto** (modo desplegado): el cuestionario escribió `lectores/761bcef5-d1fe-467f-91d9-9b2f941bc427/perfil.json`, el mismo UUID de `localStorage`; F5 conserva «1.13 / 2.00»; un contexto de navegador aislado ve «Todavía no has fijado tu nivel». Clave mala → «No he podido entrar…»; buena → «Has entrado como prof. Te quedan 3 usos»; Estado → «Perfiles: 2 válidos de 2 declarados».
- **Dinero, por el lado bueno**: sin perfil, `usar_openai=False` y la ficha dice por qué; sin clave, no se cobra; con la puerta quitada, todo pasa (modo casa); el cupo bajo 20 hilos con tope 2 deja pasar 2; el contador no baja de cero ni pasa del tope; los tres cubos por hora frenan y dicen los minutos que faltan; `cuentas.consumir` es atómico; los clientes de OpenAI llevan `timeout` y `max_retries`.
- **Contrato del módulo**: 246 pruebas extremas, 27 pasos de integración, smoke, perfil, ficha y desambiguación (7) en verde; y las sondas hostiles propias —`None`, índices `999`/`-5`/`"3"`, `perfil.json` con listas donde van cadenas, `biblioteca.json` con `ruta` lista, `sesion.json` `[]`/`"hola"`/`3`— devuelven texto. Solo se cuelan los cuatro casos de S4 y S8.
- **Orden de capítulos**: 19 epub reales de Gutenberg (Alice, P&P, C&P, Emma, W&P, Dracula, Monte Cristo, Holmes, Karamazov, Tom Sawyer, Frankenstein, Earnest, Two Cities, Metamorphosis, Heart of Darkness, Grimm, Secret Adversary, Declaration, Alice ilustrada) salen en el orden del spine; `The Memoirs of Sherlock Holmes` no está cacheado, pero los mutantes M31–M33 (spine ignorado, orden de texto, atributos exigiendo `id` antes de `href`) mueren en la prueba sintética.
- **Datos**: catálogo 1.197 filas, A1 723 / A2 185 / B1 69 / B2 52 / C1 53 / C2 115, 148 PG y 1.049 SW, PG por nivel A2 2 / B1 10 / B2 12 / C1 25 / C2 99 (igual que el comentario de `_recomendar`); diccionario 1.487.639 filas, 7.003 con audio (0,47 %), `idx_palabra`, `COUNT(*)` en 0,1 s; *Alice* cap. XII 5.042 palabras de las que 2.910 son licencia («2.900»); *P&P* 28 % y *C&P* 31 % de diálogo.
- **Stack**: gradio 6.26.0, transformers 5.16.1, pandas 3.0.0, openai 3.8.0, torch 2.14.0+cpu, Python 3.11.9; `launch(theme=…)` y `max_file_size` arrancan; el modelo carga en 11 s y puntúa 8 ventanas en 1,08 s.
- **Secretos**: `.env`, `CLAVES.txt`, `literalevel_codigos.txt`, `kaikki_diccionario.db`, `modelo_v4/` no están rastreados por git. (La contraseña que `mensaje_profesor.md` manda rotar sigue en el historial, commit `921e365`: rotarla, como ya está escrito.)
- **Cuadernillo**: ver n1.

---

## La última pregunta

**Sí, queda algo, y es de dos clases.**

Delante del profesor, con la aplicación abierta: el recorrido de la demo es «fija tu nivel → Ver libros para mi nivel», y esa segunda pantalla dice «Lo más leído entre 0.88 y 1.38» sobre diez libros y, debajo, «No hay libros etiquetados entre 0.88 y 1.38» (S1); la pestaña anterior le acaba de prometer «entre 1.03 y 1.28» (S7). Si abre el tercero de la lista, *Los hermanos Karamazov*, y pulsa «Leer el libro entero», la curva que el documento llama «la figura que mejor explica el producto» se dibuja con 59 de 98 capítulos mientras el pie dice que «el modelo recorre cada capítulo entero» (S2). Y la pestaña Estado escribe «1,197 libros» al lado de un texto que dice «1.197» (m6).

Leyendo el documento: el mismo apartado dice 36 y 31 para el mismo recuento (S5), la figura de la escala pone «0.20 … 1.80» junto a «0,00» y «2,00» (m2), hay dos frases con restos de una edición a medias (m3, m4), y la cifra de pruebas es de hace dos auditorías (m1). Nada de esto cambia el resultado científico; todo es lo que un lector cuidadoso encuentra en la primera pasada, y este trabajo presume, con razón, de haber sido leído con cuidado.

Lo que no avergüenza pero cuesta dinero: S3, y la constatación de que la protección más importante del gasto —`usar_openai` dentro de `lexicon.py`— solo la vigila una suite de pago que pasa con la API desconectada (S6).
