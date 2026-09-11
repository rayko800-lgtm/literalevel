# Auditoría 14 (Fable) — LiteraLevel, la última antes de entregar

**Fecha:** 10 de septiembre de 2026, noche. **Auditor:** Fable, a ciegas.
**Árbol auditado:** el local (`C:\Users\laura\literalevel`), que es byte a byte el
del Space: cotejé por el API público del Hub el `blob_id` de los trece módulos
de `app/`, `requirements.txt` y `catalogo_recomendaciones.csv` contra el sha de
git de los archivos locales y **los quince coinciden**. Lo que se dice aquí del
código vale para lo desplegado.

## Cómo se hizo, y qué no se hizo

- **Ciega de verdad.** No abrí `auditoria/` (salvo para escribir esto) ni
  `git log`. Tampoco leí los `auditoria/cierre_*.md` que `AGENTS.md` manda a
  quien vaya a tocar código: yo no toco código, y leerlos habría roto la
  ceguera. `CLAUDE.md` y `AGENTS.md` sí, enteros.
- **Copia de control.** `app/`, los diez `pruebas_*.py` y `tests_smoke.py`,
  `main.py`, `validar_local.py` y el CSV, copiados al scratchpad. El modelo y
  el diccionario se apuntaron por `LITERALEVEL_MODELO` y
  `LITERALEVEL_DICCIONARIO` al original (solo lectura), que es lo que evita el
  fallo de «archivo no copiado» que engañó a rondas anteriores. El `.npy` del
  catálogo no hizo falta copiarlo: `catalogo.py` lo lee de `~/.literalevel`
  hagas lo que hagas, y eso es un hallazgo (S2).
- **Control sin mutar, antes de mutar nada:**

  ```
  smoke          rc=0  TODO OK
  extremas       rc=0  Las 262 pruebas extremas pasan: ningun manejador lanzo excepcion.
  integracion    rc=0  Los 27 pasos del recorrido encadenan bien.
  ficha          rc=0  Todas las pruebas de la ficha pasan.
  perfil         rc=0  TODO OK: extremo fácil=0.000, extremo difícil=1.977
  desambiguacion rc=0  (7 pruebas OK)
  audio_atomico  rc=0  OK
  lexicon        rc=0  RESULTADO: TODO OK   (con --sin-openai)
  voz            rc=1  FALLARON 5 comprobaciones (las cinco de la sección «ciclo completo con API real»)
  ```

  Las cinco de `pruebas_voz.py` fallan **por el montaje, no por el código**:
  la suite lee la clave con `config.cargar()` (`pruebas_voz.py:17`) y gasta
  dinero si se corre a pelo, así que corrí todo con `OPENAI_API_KEY=sk-falsa`
  y `OPENAI_BASE_URL=http://127.0.0.1:9`. Con eso `TIENE_CLAVE` es `True`, la
  sección de red se ejecuta contra un puerto muerto y falla. Esas cinco son la
  línea base: un mutante de voz solo cuenta como cazado si falla **otra**
  comprobación (M28 no lo hizo; M25 lo cazó `pruebas_audio_atomico`).
- **Dinero gastado: cero.** Clave falsa y puerto muerto en todas las suites,
  en el arnés de mutantes, en los ataques directos y en la app arrancada en
  local. `config.cargar()` no pisa una variable ya puesta, así que la clave
  real de `CLAVES.txt` nunca entró en el entorno.
- **El Space se tocó, y solo así:** lectura del árbol y de `app.py` y
  `README.md` por el API público; cinco `GET` a `/gradio_api/file=…` para ver
  si servía algo que no debiera (todos 403); y el cotejo de hashes. Ningún
  clic que llame a OpenAI, ningún secreto.
- **La app se abrió como una persona**, en Chrome, arrancada en local con
  `main.py` como si fuera la nube (`SPACE_ID` puesto, `LITERALEVEL_CUENTAS`
  con un perfil de tope 3, datos en un temporal, clave falsa, OpenAI muerto).
  Hice los clics del guion en su orden.
- **37 mutantes**, cada uno con la prueba que esperaba que lo cazase escrita
  antes de correrlo. Tabla al final.

**Balance:** 0 críticos · 5 serios · 11 menores · 9 notas. Ningún camino
llega a OpenAI saltándose la puerta; ningún visitante ve los datos de otro;
ninguna cifra publicada está mal. Lo que sigue mal es de otro tipo: la suite
tiene agujeros justo donde el proyecto ya se quemó (aislamiento por lector),
cuatro manejadores rompen el invariante central con una excepción que no sea
`ValueError`/`OSError`, el `.npy` que se subió al Space no lo lee nadie, y los
entregables contradicen al repositorio en una cosa que el profesor va a leer.

---

## Hallazgos serios

### S1 · Cuatro manejadores del modelo dejan pasar excepciones hacia Gradio

**Gravedad: serio.** Es el invariante que declara la cabecera de
`app/ui.py:21-22`: *«Ningun manejador levanta excepciones hacia Gradio: lo que
falla se devuelve como texto legible en la propia interfaz.»* Se cumple para
`ValueError` y `OSError`, y para nada más.

- `app/ui.py:1383` (`_medir`): `except (ValueError, OSError) as e:`
- `app/ui.py:1587-1591` (`_analizar_libro`): el `try` cubre solo
  `p = puntuador()`; la llamada que de verdad puntúa,
  `vs = p.perfil_de_texto(ficha.sin_licencia(c.texto), …)` (`ui.py:1598`),
  está fuera de todo `try`.
- `app/ui.py:693` (`_desde_muestra`) y `app/ui.py:665` (`_nivel_desde_libro`):
  `except (ValueError, FileNotFoundError, OSError) as e:`

Lo que lanza torch cuando se queda sin memoria es `RuntimeError`
(«DefaultCPUAllocator: not enough memory»); lo que lanza `safetensors` si la
descarga del Hub llega cortada en el arranque en frío tampoco desciende de
`OSError`. En `cpu-basic` con dos análisis completos encolados y 16 GB no es
lo más probable, pero el invariante no dice «casi nunca».

**Reproducción** (`ataques.py` sobre la copia de control; un `Puntuador` doble
cuyo `puntuar`/`perfil_de_texto` lanzan `RuntimeError`):

```
=== 1. Excepciones que NO son ValueError/OSError desde el modelo ===
  LEVANTA _medir con RuntimeError: RuntimeError: DefaultCPUAllocator: not enough memory
  LEVANTA _analizar_libro con RuntimeError: RuntimeError: DefaultCPUAllocator: not enough memory
  LEVANTA _desde_muestra con RuntimeError: RuntimeError: DefaultCPUAllocator: not enough memory
  LEVANTA _nivel_desde_libro con RuntimeError: RuntimeError: DefaultCPUAllocator: not enough memory
```

La prueba que protege esto, `_medir_con_el_modelo_inalcanzable`
(`pruebas_extremas.py:2040-2065`), solo lanza `OSError`, y solo contra
`_medir`. El mutante M18 (volver a atrapar solo `FileNotFoundError`) sí lo
caza, o sea que la prueba vale para lo que mide; lo que no mide es esto.

**Arreglo:** en los cuatro, `except Exception as e:` con el mismo `_aviso(e)`,
que es exactamente lo que ya hace `_abrir` (`ui.py:1267-1272`, con su
justificación escrita). Y en `_analizar_libro` meter el bucle de
`perfil_de_texto` dentro del `try`. Una prueba: doble de `puntuador()` que
lance `RuntimeError`, pasado por los cuatro manejadores, aseverando que vuelve
texto con `[!]`.

### S2 · El `.npy` del catálogo que se subió al Space no lo lee nadie, y la ruta se salta `LITERALEVEL_DATOS`

**Gravedad: serio** (es la espera visible del segundo paso del guion, y es una
promesa escrita que no se cumple).

`app/catalogo.py:26`:

```python
DIR_CACHE = Path(os.path.expanduser("~")) / ".literalevel"
```

y `app/catalogo.py:183`: `cache = DIR_CACHE / f"catalogo_emb_{_huella(self.ruta)}.npy"`.
No pasa por `config.dir_datos()`. Tres consecuencias:

1. `DESPLIEGUE.md:166-167` afirma: *«Ahora las nueve rutas de escritura salen
   de `config.dir_datos()`, y una prueba lo exige.»* Y la prueba
   `_una_sola_raiz_de_datos` (`pruebas_extremas.py:3668-3711`) dice en su
   docstring *«Todo lo que la app escribe cuelga de `LITERALEVEL_DATOS`.
   TODO.»* Enumera nueve rutas (`BASE_DATOS_LECTOR`, `RUTAS_PERMITIDAS`,
   `RUTA_LIBROS`, `RUTA_ANALISIS`, `RUTA_SESION`, las dos de `lexicon` y las
   dos de `voz`) y **no esta**. La décima ruta de escritura se quedó fuera y
   la prueba pasa en verde.
2. El árbol del Space (API público, `tree/main`) lleva
   `catalogo_emb_653c0cb55f63a386.npy` (1.838.720 B) **en la raíz del
   repositorio**, y `tools/desplegar_app.py:27-28` lo cuenta entre los «datos
   que ya están colocados». Pero `Catalogo.embeddings` solo mira
   `DIR_CACHE`, que en el Space es `/home/user/.literalevel/`, no
   `/home/user/app/`. Ese archivo es peso muerto: nunca acierta.
3. Con `LITERALEVEL_DATOS=/data` montado, la caché del catálogo sigue yendo al
   disco efímero. Cada reinicio —cada `desplegar_app.py`, cada despertar tras
   48 h— recodifica los 1.197 libros con el modelo multilingüe en la primera
   búsqueda.

**Reproducción:**

```
=== 6. catalogo.DIR_CACHE vs config.dir_datos() ===
  catalogo.DIR_CACHE     : C:\Users\laura\.literalevel
  config.dir_datos()     : C:\Users\laura\AppData\Local\Temp\ll_ataques_gpqxrwhe
  LITERALEVEL_DATOS      : C:\Users\laura\AppData\Local\Temp\ll_ataques_gpqxrwhe
```

y el coste, medido en esta máquina (Ryzen 5 2600, 12 hilos; el Space tiene 2
vCPU, así que allí es peor):

```
import catalogo 0.8s | Catalogo()+embeddings (npy cacheado) 0.0s | buscar 'dostoyevski' 20.5s
SIN npy en cache (lo que pasa en cada arranque del Space): recodificar 1.197 libros = 56.9s en esta CPU
```

(Los 20,5 s de la primera búsqueda con caché son cargar el modelo multilingüe
en un proceso limpio, y se pagan una vez por proceso; los 56,9 s son lo que se
paga **además** en cada arranque del Space, y es lo que la pestaña admite como
«puede tardar cerca de un minuto».)

**Arreglo:** `DIR_CACHE = config.dir_datos()` en `catalogo.py` (así el `.npy`
sobrevive en `/data` y se genera una sola vez), o buscar también en `RAIZ`
como respaldo, que es donde está el que ya se subió. Y añadir
`'catalogo.DIR_CACHE': str(catalogo.DIR_CACHE)` a `_una_sola_raiz_de_datos`
para que la prueba diga la verdad. Hasta que se haga, si se redespliega el
sábado antes de grabar, **la primera búsqueda de la demo tarda más de un
minuto** en el Space.

### S3 · Trece mutantes sobreviven: la suite no protege el aislamiento por lector ni el cuestionario

**Gravedad: serio** como conjunto. De 37 mutantes, 24 los cazó exactamente la
prueba que esperaba (tabla al final). Los 13 que sobreviven, agrupados por lo
que dejan sin red:

**(a) El aislamiento por lector, que es donde el proyecto ya se quemó dos veces.**

- **M26** — `app/ui.py:1169-1172`, `_ruta_sesion`, sustituido por
  `return RUTA_SESION` (un marcapáginas para todos, desplegada). Es
  literalmente *«el caso más feo»* que describe `ui.py:92-94` y
  `AGENTS.md:151-155`: `demo.load` pinta a cada visitante el capítulo del PDF
  del anterior. Sobrevive a las 262 extremas y a los 27 pasos.
- **M27** — `app/ui.py:2308` y `:2540`, quitar `peticion` de
  `_archivo_lector("cuaderno.db", …)` en `_consultar` y `_mis_palabras` (un
  cuaderno para todos: visitante B lee las palabras y las frases del libro
  privado de A). Sobrevive.

Por qué sobreviven: `_los_manejadores_que_guardan_pasan_la_peticion`
(`pruebas_extremas.py:670-716`) solo se fija en los manejadores cuyo cuerpo
**contiene** `_archivo_lector(... peticion` o `_ruta_sesion(peticion`; el que
deja de pasarla ya no casa con el regex y se salta. Y
`_dos_lectores_no_se_ven_los_datos` (`:534-567`) solo recorre el perfil. La
red cubre `perfil.json` (M09 cazado) y nada más.

**Arreglo:** una prueba con dos `_Peticion` en `_con_nube` que abra un libro
con A (`_abrir`), cambie de capítulo, consulte una palabra (con un doble de
`consultor`) y compruebe que `_reanudar(B)` devuelve vacío, `_mis_palabras(B)`
no contiene la palabra y `_leer_sesion(B)` es `None`. Yo lo comprobé a mano
y el código lo hace bien (ataques §3, más abajo); solo falta la prueba.

**(b) El cuestionario, que es el primer clic de la demo.**

- **M21** — `app/ui.py:586-587`: `claves = _claves_cuestionario()[::-1]`
  (las respuestas se asignan a las preguntas al revés). Sobrevive a extremas y
  a `pruebas_perfil.py`: `pruebas_perfil` prueba `perfil.desde_cuestionario`
  con diccionarios ya construidos, y en `ui` las pruebas del cuestionario solo
  miran `nombre` y que el perfil no sea `None`. Nadie comprueba que la radio
  «Casi todos los días» acabe en la clave `frecuencia` con valor 1,6.

**Arreglo:** una prueba que llame a `_desde_cuestionario` con un vector que
solo ponga valor en una posición y asevere el nivel resultante (por ejemplo
todo `None` menos `fragmento_dificil=2.0` debe dar 2,0; todo `None` menos
`frecuencia=1.6` debe dar 1,6).

**(c) El buscador y la recomendación.**

- **M33** — `app/catalogo.py:273`: `d = self.df` (por_nivel ignora la
  holgura; «Sorpréndeme» deja de filtrar por nivel). Sobrevive:
  `_el_rango_anunciado_es_el_filtrado` (`:2668-2685`) solo mira el rótulo.
- **M20** — `app/ui.py:951`: rescate del lector A1 desactivado (desplegable
  vacío para quien más ayuda necesita). Sobrevive: no hay prueba del rescate.
- **M02** — `app/ui.py:754-755`: `_opciones_libros` no lista nada («Leerlo
  ahora» siempre vacío). Sobrevive: `prueba("opciones con un libro de
  Gutenberg", …)` (`:327-328`) devuelve `["choices"]` y no asevera nada.
- **M46** — `app/ui.py:728`: `_tabla_libros` marca todo como abrible.
  Sobrevive: no hay prueba del contenido de la tabla.

**(d) Dinero.**

- **M32** — `app/ui.py:1711-1712`: `datos = None` (se ignora la sinopsis
  guardada; cada pulsación de «¿De qué trata?» paga cuatro pasajes). Sobrevive.
  `_el_cupo_cuadra_con_las_llamadas_de_pago` comprueba que no se cobre sin
  llamar, no que no se llame cuando ya está en caché. El documento presume de
  lo contrario (`documento.md:1697-1698`: «un libro se resume una vez y ya»).
- **M03** — `app/ui.py:265`: los cubos `voz` y `sinopsis` contados en el de
  `lexico` (una hora de consultas te agota la voz). Sobrevive:
  `prueba("cubos distintos no se mezclan", …)` (`:424-426`) devuelve una
  **tupla** `(True, False)`, que nunca es `False`.

**(e) Pruebas con el patrón que el propio envoltorio dice haber erradicado.**

- **M01** — `app/ui.py:431-438`, `_css_paleta` devuelve `""` (la página se
  queda sin paleta). Sobrevive porque `pruebas_extremas.py:1085-1087`:

  ```python
  prueba("todas las paletas dan css",
         lambda: [k for k in paletas_mod.PALETAS if not ui._css_paleta(k).startswith("<style>")]
         or "las cinco")
  ```

  devuelve la lista de las cinco que fallan, que es verdadera. Es exactamente
  el patrón `return malas or "todo bien"` que el docstring de `prueba`
  (`:54-80`) cuenta como corregido «en cada una de esas cuatro». Quedó esta, y
  quedó `prueba("los limites de la tabla son los del codigo", …)`
  (`:1044-1048`), que devuelve la lista de límites que no cuadran; a esa la
  salva `_una_sola_letra` (M15 cazado por «la interfaz y el contrato dan la
  misma letra», **no** por la de los límites, que imprimió `ok` con `_cefr`
  roto).
- **M28** — `app/ui.py:2415`, `fallo = set()` (la corrección de pronunciación
  marca todo en verde). Sobrevive: `prueba("marca bien y mal", …)` (`:335-336`)
  devuelve `(falladas, cuenta)` sin aseverar. `pruebas_voz.py` prueba
  `evaluar_pronunciacion`, no el pintado. Es el paso cinco del guion.

**(f) Menores.** **M19** (`ui.py:2301`, el cuaderno registra palabras que el
diccionario no reconoce) y **M45** (`ui.py:1654`, `exigente` invertido: el
tiempo de lectura al revés) sobreviven; no hay prueba de ninguno.

**Pruebas decorativas** (devuelven un valor que nunca es `False`; no las mutó
nadie pero no aseveran): `:327-328`, `:335-336`, `:403-404` («saca la IP»
devuelve la IP sin compararla), `:424-426`, `:721-722` («se recorta» devuelve
la longitud sin exigir 64), `:759-762` («repasar agrupa por lema» devuelve el
recuento sin exigir 1), `:1039-1040` (no exige seis anclajes), `:1085-1087`,
`:1845-1846` (no exige `A2, B2, C2`). Y en `tests_smoke.py:57`, la «lista» se
rechaza por `pocas_frases`, no por la regla de maquetado: con esa regla
apagada (M13) `tests_smoke` sigue en verde (`smoke rc=0`); la caza
`_el_filtro_sigue_rechazando_menus_indices_y_tablas`.

### S4 · Los entregables dicen que no hay disco persistente; el repositorio dice que sí lo hay desde anoche

**Gravedad: serio** (es una limitación enumerada y una conclusión del PDF que
el profesor va a leer, y contradice lo que la app hace).

`DESPLIEGUE.md:155-160`: *«HECHO el 10 de septiembre de 2026 por la noche
(accionable A4 cerrado). Hay un Storage Bucket privado … montado en `/data`
del Space, y la variable `LITERALEVEL_DATOS=/data` … Verificado de punta a
punta»*. `PENDIENTES.md:139-142`, lo mismo. El encargo de esta auditoría lo
confirma («el Space tiene un disco persistente montado en `/data`»).

Y sin embargo:

- `entrega/documento.md:1212-1215` (limitación 12): *«y **no da
  almacenamiento persistente**, así que la estantería, el avance de lectura y
  el cuaderno del lector viven en disco efímero y no sobreviven a un reinicio
  del contenedor. Lo segundo es la acción A4 de la estrategia.»*
  Está igual en `documento.tex:2681-2682` y en el texto extraído de
  `documento.pdf` (47 páginas).
- `entrega/documento.md:1331` (conclusiones): *«se suspende por inactividad y
  no guarda nada entre reinicios»*; `:1351`: *«montar almacenamiento
  persistente, sin el cual el lector pierde su estantería en cada reinicio»*
  (`documento.tex:2819`).
- `entrega/estrategia.md:430` (A4): *«Hoy todo eso vive en disco efímero»*;
  `:456`: *«Sin disco persistente todavía (A4)»* (`documento.tex:875, 910`).
- `entrega/notebook_proyecto.py:1953-1958` (§8.4, accionable 3): *«pero sobre
  disco efímero: la estantería, el avance y el cuaderno del lector no
  sobreviven a un reinicio»*.

Una de las dos partes está desfasada. Por las horas de modificación (los
entregables se tocaron a las 16:0x–18:34 y el bucket se montó «por la noche»)
son los entregables. Hoy la aplicación conserva el perfil, la estantería y el
cuaderno entre reinicios, y el documento presenta eso como lo que falta.

**Arreglo:** reescribir la limitación 12 (queda la parte cierta: cuesta 7 USD,
duerme a las 48 h y el arranque en frío son 31-32 s), las dos frases de las
conclusiones, A4 y el Cuadro 3 de `estrategia.md`, el punto 3 de §8.4 del
cuadernillo (y regenerar el `.ipynb`), y recompilar `documento.pdf`. Si por
lo que sea el bucket no estuviera montado de verdad, entonces lo que hay que
corregir es `DESPLIEGUE.md` y `PENDIENTES.md`; pero en cualquiera de los dos
casos hoy se contradicen.

### S5 · Una nota de edición se quedó dentro de una diapositiva

**Gravedad: serio** (está en `presentacion.pdf`, que se califica).

`entrega/presentacion.tex:217-218`, diapositiva «Hallazgo 1»:

```
Las tres barras salen de \textbf{la misma tanda}: aquí decía 1,06, que es la tanda recalculada, y restarle
las otras dos es la resta que el documento dice que no se puede hacer.
```

Texto extraído de `presentacion.pdf`, diapositiva 6: *«Las tres barras salen
de la misma tanda : aquí decía 1,06, que es la tanda recalculada, y restarle
las otras dos es la resta que el documento dice que no se puede hacer.»*
«Aquí decía» es una nota del autor para el autor. El resto de la nota al pie
(«Subir la potencia del clasificador … Cambiar la representación sí.») está
bien.

**Arreglo:** cortar desde «: aquí decía» hasta el punto, dejar «Las tres
barras salen de la misma tanda.» y recompilar. Un minuto.

---

## Hallazgos menores

### m1 · `_de_que_trata` cobra el uso aunque la sinopsis falle en la red

`app/ui.py:1761-1765`:

```python
        datos = ficha.sinopsis(libro, cliente)
        if datos is None:
            yield ("No pude preparar el resumen ahora mismo. Vuelve a "
                   "intentarlo; el resto de la ficha no depende de esto.")
            return
```

`ficha.sinopsis` atrapa cualquier excepción y devuelve `None`
(`app/ficha.py:363-371`); el uso ya está cobrado por `_puede_pagar` y no se
devuelve. El mensaje dice «vuelve a intentarlo», y cada intento cuesta un uso.

**Reproducción** (ataques §2, perfil `ana:CLAVE:5`, OpenAI en un puerto muerto):

```
  salida: No pude preparar el resumen ahora mismo. Vuelve a intentarlo; el resto de la ficha no depende de est
  gastado antes/despues: 0 1 (la llamada fallo por red: 127.0.0.1:9)
```

Es coherente con la regla de «se cobra lo que se intenta» de `_consultar`, y
no es dinero del dueño; pero el lector no se entera. **Arreglo mínimo:** que el
mensaje diga que ese intento consumió un uso; **mejor:** que `ficha.sinopsis`
distinga `APIConnectionError`/`APITimeoutError` (nada salió) y `ui` devuelva
el uso en ese caso, igual que hace cuando `cliente is None`.

### m2 · La sesión de pago se pierde al recargar la página; los datos no

`app/ui.py:287-293`: `_CODIGO_SESION` se indexa por `session_hash`, que
Gradio estrena en cada carga (lo dice `ui.py:110-114`). La identidad de los
datos se movió a `localStorage` (`:116-125`), la del pago no.

**Reproducción en el navegador:** entré con `demo`, consulté una palabra,
pulsé F5. Tras recargar: nivel «1.20 / 2.00» recuperado, libro recuperado
(«Metamorphosis — seguías en el capítulo 2 de 4»), y la consulta vuelve a
decir *«[!] Esta parte necesita que entres con tu perfil»*. Y en código
(ataques §4): `codigo en sesion-1: ana:CLAVE` / `codigo tras F5 (sesion-2):
None`.

En la demo, cualquier recarga obliga a volver a escribir usuario y
contraseña delante del profesor. **Arreglo:** indexar `_CODIGO_SESION` por
`_lector_de_sesion(sesion) or sesion`, que ya existe para los datos.

### m3 · Dos recuentos de palabras distintos en la misma pantalla al abrir un libro

Tercer clic de la demo. `app/ui.py:1294-1295` pinta el resumen con
`libro.palabras` (crudo, con portadilla y licencia):

> **Metamorphosis** — Franz Kafka · 4 capítulos · **25.077 palabras**

y tres líneas más abajo la ficha (`app/ui.py:1660`) pinta
`ficha.caracteristicas(libro).palabras`, que descuenta licencia y portadilla:

> **21.938 palabras** en 4 capítulos · 2 h 02 min a tu ritmo de lectura

Visto tal cual en el navegador. El documento explica por qué la ficha
descuenta (`documento.md:335-341`), pero no que la cabecera no lo haga.
**Arreglo:** usar el mismo recuento en la cabecera (o rotularlo «con
portadilla y licencia»).

### m4 · La oración de contexto arrastra el título del capítulo

Cuarto clic. `_oracion_de` (`app/ui.py:1972-1981`) aplica `SENT_RE` al texto
crudo del capítulo, cuyas primeras líneas son encabezados sin punto. Lo que
se cita como contexto:

> I I One morning, when Gregor Samsa woke from troubled dreams, he found himself transformed in his bed into a horrible vermin.

El docstring (`:1964-1966`) reconoce el problema para el caso «solo
encabezado», pero no para el «encabezado pegado». `_frase_del_capitulo`
(`:2351-2358`) ya lo resuelve partiendo por párrafos antes; `_oracion_de` no.
**Arreglo:** partir por `\n\s*\n` y saltarse los párrafos de menos de seis
palabras antes de buscar.

### m5 · Un aviso técnico sale en crudo en la ficha de la palabra

Mismo clic. `app/lexicon.py:308-311` produce
`"acepcion provisional: margen bajo (0.004) frente a otra acepcion: …"`; la
tabla `_AVISOS_HUMANOS` (`app/ui.py:2031-2066`) no lo traduce y `_ficha` solo
evita repetirlo (`:2109`). En pantalla:

> [!] acepcion provisional: margen bajo (0.004) frente a otra acepcion: An animal that preys on game, such as a fox or a weasel.

Sin acentos, con «margen bajo (0.004)» y al lado de avisos redactados con
cuidado. **Arreglo:** una entrada en `_AVISOS_HUMANOS` («La acepción elegida
es dudosa; la otra candidata es: …») en los dos idiomas.

### m6 · El guion contradice al documento en lo que dice a cámara

`entrega/guion_video.md:110-111`: *«Le describo en español lo que me apetece
leer y me busca entre los libros que **puedo** leer.»* Pero
`documento.md:926-928` (§8.2): *«Lo que devuelve la búsqueda **no está
filtrado por el nivel del lector**: ordena por cercanía al tema»*, y la propia
casilla dice «Acercar los resultados a mi nivel · no descarta libros»
(`ui.py:2894-2897`). Un profesor que haya leído §8.2 oye lo contrario.

Y `guion_video.md:121-124`: *«Toco una palabra y en **40 milisegundos** me da
su significado **en esta frase**, no en abstracto: la definición del
diccionario, la gramática…»*. Los 40 ms son lo local (lema, diccionario,
IPA); «en esta frase» y «la gramática» son la explicación contextual, que el
documento mide en 14,9 s (`documento.md:955-958`, `estrategia.md:301-304`). En
la grabación esa parte llegará quince segundos después de decirlo.

**Arreglo:** «me busca por lo que quiero leer y me pone el nivel al lado» y
«en 40 milisegundos tengo el diccionario y la fonética; la explicación en
contexto llega unos segundos después».

### m7 · Una etiqueta que la app ya no usa, citada como corrección hecha

`entrega/estrategia.md:188` (Cuadro 1, Esmeralda) y `documento.tex:724`:
*«"Ajustar a mi nivel" es abstracto | "Solo libros que pueda leer", con
información | Etiqueta reescrita»*. La app dice «Acercar los resultados a mi
nivel» porque, según `ui.py:2888-2893`, «Solo libros que pueda leer» *«no deja
fuera nada»* y por eso se cambió. El cuadro presenta como corrección la
etiqueta que después hubo que corregir. **Arreglo:** poner la vigente.

### m8 · «Cinco auditorías externas»

`entrega/documento.md:1132-1135` (y el PDF): *«Este trabajo se sometió a
**cinco auditorías externas** … alrededor de setenta hallazgos»*. Esta es la
decimocuarta y `PENDIENTES.md:8-9` cita la decimotercera. **Arreglo:** «más de
una docena» o la cifra real, y revisar «setenta».

### m9 · Cuadernillo: tres frases desfasadas y dos cifras copiadas a mano que la ejecución no reproduce

Lo ejecuté entero en local (con un `seaborn` de relleno de tres funciones
porque aquí no está instalado y no instalo nada en el entorno de Miguel;
`matplotlib` en `Agg`; el v4 desde la caché del Hub): **`rc=0`, sin
excepciones, y por `stderr` solo la barra de progreso «Loading weights» de
transformers**, que no es un aviso. Las dos URL que descarga responden 200
(CLEAR 3,3 MB; `pg_catalog.csv` 21 MB). Los recuentos vivos siguen siendo
79.337 y 61.642. Pero:

- `notebook_proyecto.py:1634-1635`: *«exige horas de GPU o los pesos que **aún
  no están publicados**»*. Están publicados (lo dice el mismo cuadernillo en
  `:45-48` y `:1409-1416`).
- `:1241`: *«(RMSE 0,765 frente a 0,748)»* y `:1685`: *«El Random Forest no
  mejora … (0,765)»*. La ejecución imprime `Random Forest (300 árboles) 0.605
  0.767 0.686`. Dos milésimas (sklearn 1.9 aquí; Colab llevará otra), pero es
  una cifra escrita a mano al lado de una celda que la calcula, que es lo que
  `:1886-1889` dice que no hay que hacer. Lo mismo `:1228` «34,9 %» frente al
  `0.348` impreso, y `:978` «70,0 %» frente al acumulado `0.701`.
- `:483-485`: *«No hay relleno, y por tanto agrupar las ventanas de una manera
  u otra **no puede cambiar ni un decimal**»*, dicho sin la salvedad que el
  documento sí hace (`documento.md:1000-1007`: en lotes de capítulos distintos
  hay relleno y «no es idéntico bit a bit»). `:1802` repite «300/300 valores
  idénticos bit a bit» sin la salvedad.

Todo lo demás que el cuadernillo copia coincide con lo que imprime (lista en
«Comprobado y bien»).

### m10 · `PENDIENTES.md` dice que el Space va por detrás del árbol

`PENDIENTES.md:36-38`: *«**El Space está a medias:** los cinco módulos que
faltaban se subieron, pero **lo de la auditoría 13 todavía no**.»* Y
`AGENTS.md:19`: «Sin desplegar todavía». Cotejados los hashes hoy: los quince
archivos son idénticos. Está subido; el aviso confunde a quien lea
`PENDIENTES.md` el sábado.

### m11 · `pruebas_extremas.py` corre con una `_consultor` contaminada por un espía

En `_el_cupo_cuadra_con_las_llamadas_de_pago` (`:2273-2446`), la primera
sección llama a `list(ui._de_que_trata(libro_ok, pet))` con `openai.OpenAI`
sustituido por el `Espia`. En esta máquina el diccionario existe, así que
`consultor()` construye el `ConsultorLexico` real y `_cliente()` deja el
**espía** guardado en `ui._consultor._cliente_openai`. El `finally` restaura
`openai.OpenAI` pero no ese atributo. Hoy no rompe nada porque las pruebas
posteriores sustituyen `ui.consultor` por dobles, pero el comentario «sin
diccionario: revienta al construir el consultor» describe otra máquina, no
esta. **Arreglo:** poner `ui._consultor = None` en el `finally`.

---

## Notas

- **n1.** La pestaña Estado corre en `demo.load` para cualquier visitante
  (`ui.py:3154`) y publica «Perfiles: N válidos de M declarados» más los
  avisos de `cuentas.problemas()`, que llevan **nombres de usuario** de las
  entradas mal escritas (`ui.py:2733-2737`). No lleva contraseñas, pero da a
  un desconocido el número de cuentas y algún usuario. Visto en local:
  `Perfiles: 1 válidos de 1 declarados`.
- **n2.** `ui.py:76-77` dice *«Gradio solo sirve archivos del directorio de
  trabajo o del temporal del sistema»*. En Gradio 6.26,
  `gradio.utils.is_allowed_file` sirve **solo** `allowed_paths` y los
  temporales creados; el directorio de trabajo no. El razonamiento del
  comentario es viejo; la decisión (`RUTAS_PERMITIDAS = [… / "audio"]`,
  `:86`) es correcta. En el Space: `file=app.py` → 403,
  `file=kaikki_diccionario.db` → 403, `file=/data/uso_openai.json` → 403,
  `file=/data/lexicon.db` → 403, `file=/data/audio/` → 403.
- **n3.** El coste de una práctica de voz no está acotado por duración:
  `TAMANO_MAXIMO_SUBIDA = "20mb"` (`ui.py:74`) vale también para el audio, y
  whisper-1 cobra por minuto. Un mp3 de 20 MB a bitrate bajo son horas; con un
  perfil de tope 40 y 10 por hora, es el peor caso más caro de la app.
  `gr.Audio(max_length=…)` o un corte en el servidor lo cierran.
- **n4.** `_RONDA_FRASE` (`ui.py:2331`) crece sin poda por (título, índice).
  Irrelevante en la práctica.
- **n5.** En la búsqueda «dostoyevski» (como en el guion) salen los cuatro
  Dostoyevsky y, debajo, «Pehelwaan ji Plays Cricket», «Pehelwaan Ji» y «Hey
  Makaw!» de StoryWeaver, con el rótulo «▸ 6 de 10 se abren aquí». Es la cola
  semántica con `minimo_similitud=0.10`; no es un fallo, pero en la grabación
  se ve.
- **n6.** `RUTA_ANALISIS` y `-sinopsis.json` se comparten entre visitantes por
  huella de contenido (`ui.py:1446-1459`). Un análisis lleva títulos de
  capítulo; no es dato personal y solo lo recupera quien suba el mismo libro.
  Correcto, anotado.
- **n7.** `pruebas_voz.py:17` (`config.cargar()`) gasta dinero si se corre a
  pelo; el README lo dice («usa OpenAI»). Con `OPENAI_API_KEY` puesta a un
  valor falso no gasta, porque `config.cargar` no pisa.
- **n8.** Segunda pulsación de «Traer una frase del capítulo» trae otra frase
  (comprobado: rota). El guion no lo necesita, pero está bien.
- **n9.** `ui.py:1559-1562` y `:2969-2971` documentan cifras viejas que se
  corrigieron leyendo constantes; en pantalla sale «unas 60 ventanas», que es
  `30 × 2`. Correcto.

---

## Dinero: los tres caminos, uno por uno

Lo que se comprobó (código y ejecución):

1. **Consulta léxica** (`_consultar`, `ui.py:2173-2327`). Sin clave no cobra
   (M31 cazado); sin perfil pasa `usar_openai=False` y lo dice (mutante «puede
   = True» lo cazan «la consulta lexica pide codigo» y «el cupo cuadra»);
   `lexicon.consultar` con `usar_openai=False` no construye cliente ni pide
   nada (M23 cazado por `pruebas_lexicon` 6.1: `la puerta de pago de lexicon
   no cierra: ['tts:fetters,', 'responses']`); la caché se mira antes de pagar
   y las variantes «Fetters/FETTERS/fetters.» no pagan audio (M24 cazado por
   6.3); el uso se devuelve si `llamadas_de_pago == 0` (M04 cazado). En el
   navegador, con perfil de tope 3 y OpenAI muerto: una consulta → «Te quedan
   **2**», y el aviso «No hay conexión con OpenAI ahora mismo. El diccionario y
   la fonética son locales y siguen aquí.» Correcto: se intentó y se cobró.
2. **Sinopsis** (`_de_que_trata`, `:1695-1783`). Puerta (M05 cazado), tope por
   hora solo si va a costar («el cubo por hora solo cuenta lo que cuesta»),
   devolución cuando no hay cliente o el consultor no se construye. Fallo m1
   (cobra cuando la red falla) y mutante M32 (caché ignorada, sin prueba).
3. **Voz** (`_practicar`, `:2429-2495`). Puerta (M06 cazado por dos pruebas),
   tope por hora, cobro también sin transcripción (decisión documentada en
   `:2470-2480` y probada). Nota n3 sobre la duración.

`cuentas.consumir` es atómico bajo candado y deshace el incremento rechazado;
`_dentro_del_limite` respeta tope, IP, cubo (salvo la prueba decorativa de
cubos, M03) y ventana de 3.600 s. **Ningún camino llega a `openai.OpenAI` sin
pasar por `_puede_pagar`**: los tres puntos de construcción del cliente
(`lexicon.py:599-622`, `voz.py:51-61`, `ficha.sinopsis` vía `consultor()._cliente()`)
están detrás de un manejador que cobra antes.

## Datos de los lectores

- Desplegada, `perfil.json`, `sesion.json`, `biblioteca.json`, `cuaderno.db`
  y `voz.db` van a `lectores/<id>/` por lector (`_dir_lector`, `ui.py:163-177`).
  Comprobado con dos peticiones en modo nube (ataques §3):

  ```
  sesion A: ...\lectores\lector-A\sesion.json
  sesion B: ...\lectores\lector-B\sesion.json
  B lee el marcapaginas de A?: False
  cuaderno A: ...\lectores\lector-A\cuaderno.db
  cuaderno B: ...\lectores\lector-B\cuaderno.db
  ```

  Funciona. Lo que falta es la prueba (S3a).
- La identidad del navegador se sanea (M08 cazado) y sobrevive a recargar (M09
  cazado; en Chrome: `localStorage.literalevel_lector =
  0df68808-c6db-4d38-a375-8af1324a9e91`, nivel y libro recuperados tras F5).
- `_seguir_leyendo` y `_abrir_del_catalogo` reciben rutas e ids desde un
  `gr.Radio`; en Gradio 6.26 `Radio.preprocess` y `Dropdown.preprocess`
  rechazan cualquier valor que no esté en las `choices` de esa sesión (leído
  en el código instalado), así que no se puede pedir por ahí un archivo
  ajeno. `gr.File`/`gr.Audio` pasan por el control de rutas de Gradio.
- `allowed_paths` es solo `…/audio` (M10 cazado) y el Space devuelve 403 a
  todo lo demás (n2). Los nombres de los mp3 de voz llevan los primeros 40
  caracteres de la frase más un hash de 24 hex: no se enumeran.
- Lo compartido a propósito: `lexicon.db`, `audio/`, `libros/`, `analisis/`,
  `uso_openai.json`. Ninguno lleva datos personales.

## Cifras publicadas: todas cuadran consigo mismas y con el guion que las produce

`validar_local.py` (copia de control, modelo local, 59 PDF en `~/Downloads`):

```
nivel    n   media 0-2  desv (pobl.)   (Colab reportó)
A1       3      0.5040         0.111   —
A2       8      0.5561         0.223   0.6479
B1      12      0.9276         0.198   0.9513
B2      12      1.2414         0.236   1.2883
C1      12      1.4952         0.172   1.4950
textos sin cuerpo localizable: 2
textos que pasarian el filtro COMPLETO (con saltos de linea): 36
textos que fallaron al puntuar: 10       (nueve A1 y un B1, todos «muy corto: 150 palabras»)
  modelo v4                                  0.860
  contar palabras, sin modelo                0.807
  modelo descontando la longitud (parcial)   0.668
  (de paso: modelo contra longitud           0.732)
VALIDACION CORRECTA: 47 textos, 5 niveles, medias estrictamente crecientes.
```

Coinciden con `documento.md` (resumen, Cuadros 11-13), `documento.tex`,
`estrategia.md` (Cuadro 3), `presentacion.tex` (dos diapositivas), `README.md`
(dos tablas), `PENDIENTES.md` y `notebook_proyecto.py` (§7.2), en todas las
apariciones que recorrí con un `grep` cruzado de 70 patrones. Además:

| Cifra | Dónde vive | Comprobación |
|---|---|---|
| 262 pruebas extremas / 27 pasos | doc, estrategia, README, PENDIENTES | `grep -c '^prueba('` = 262; `paso(` = 27; y así lo imprimen |
| 561 palabras · 3:44 | guion, PENDIENTES | `tools/contar_guion.py` → 561, 3:44 |
| 1.197 libros; A1 723 · A2 185 · B1 69 · B2 52 · C1 53 · C2 115; 148 abribles / 1.049 | doc, README, AGENTS, notebook, `ui.py:939-940` | pandas sobre el CSV: idéntico, y PG por nivel C2 99 · C1 25 · B2 12 · B1 10 · A2 2 |
| 85 parejas de contraste = 17 × 5; 4,53 / 3,11 | estrategia, doc.tex, PENDIENTES | `PARES` tiene 17 entradas; la prueba pasa |
| «Cuadro 11 del `.md` = 16 del PDF», «13 = 18», «16 = 21» | doc, README, estrategia | texto extraído del PDF: Cuadro 16 es la validación, 18 el *baseline*, 21 el rendimiento |
| 59 = 12+10+13+12+12 | manifiesto | 59 PDF en disco; validador ve 59 |
| 31 s / 32 s, 7 USD, `gcTimeout` 48 h, cpu-basic | doc, PENDIENTES | API del Space: `RUNNING`, `cpu-basic`, `gcTimeout: 172800` |
| 79.337 / 61.642 / 4.724 / 4.658 títulos | notebook, doc, presentación | la ejecución del cuadernillo hoy imprime exactamente eso |

## Cuadernillo

Corre de principio a fin (m9 tiene las tres frases desfasadas y las dos
cifras a mano). Cifras del EDA que la prosa copia y la ejecución reproduce:
media −0,958, mediana −0,909, desviación 1,034, asimetría −0,134, curtosis
−0,486; CAREC_M −0,582; Google WC −0,125; medianas Lit −0,636 / Info −1,314 y
p = 4,0·10⁻⁸⁸; Spearman Lexile −0,504; `palabras_raras` −0,490, `polisilabas`
−0,477, `silabas_por_palabra` −0,447; PC1 55,1 %, PC2 14,9 %, corr(PC1) 0,614;
32 bandas Lexile en rango reparadas y 0 ilegibles; 0 títulos compartidos entre
train y test; logística 3 vars 0,313 / 1,295, 17 vars 0,352 / 1,061, XGBoost
0,340 / 1,081; línea base RMSE 1,048; lineal 11 métricas 0,764; +6 rasgos
0,748; RF Spearman 0,686; lineal Spearman 0,707; v4 sobre el extracto más
fácil 0,651 (intermedio) y el más difícil 1,794 (avanzado); horas de catálogo
731,7 / 53,2 / 3,0 y factor 247×.

## La aplicación, como la abre una persona (local, modo nube, OpenAI muerto)

1. **Cuestionario → «Estimar mi nivel»**: «Tu nivel de lectura: **1.20 /
   2.00** (intermedio) … entre **0.95 y 1.45** … Guardado.» y el botón «Ver
   libros para mi nivel →». Bien.
2. **«Ver libros para mi nivel →»**: salta a Buscar con «Lo más leído entre
   0.95 y 1.45», «▸ 10 de 10 se abren aquí mismo», diez B2 de Gutenberg y la
   lista «Elige cuál abrir». Bien (en el Space, tras un reinicio, la
   alternativa «Buscar» del guion paga S2).
3. **«Leerlo ahora»** (Metamorphosis): descarga, abre en «capítulo 2 de 4»
   con «Empiezo en el capítulo 2: los anteriores son portadilla», ficha
   contada, curva vacía. Bien salvo m3 (25.077 frente a 21.938 palabras).
4. **Consultar «vermin»** sin perfil: «vermin · noun», IPA UK/US, definición
   de Wiktionary, «Elegido entre 3 acepciones, afinidad 0.10», «rara (zipf
   3.0)», y la puerta explicada. Bien salvo m4 («I I One morning…») y m5 (aviso
   en crudo).
5. **«¿Cómo de difícil es este capítulo?»**: «**1.66 / 2.00** (avanzado) ·
   orientativo **C1** · 8 bloques · confianza alta». Bien.
6. **Entrar → consultar**: «Has entrado como **demo**. Te quedan **3** usos»,
   luego «No hay conexión con OpenAI ahora mismo…», luego «Te quedan **2**».
   Bien.
7. **Buscar «dostoyevski»**: los cuatro Dostoyevsky primero (n5 detrás). Bien.
8. **F5**: nivel y libro recuperados; sesión de pago perdida (m2).
9. **Estado**: coherente con lo cargado (n1).
10. El registro del servidor: cinco líneas, sin `Traceback` ni `Error`.

---

## Tabla de mutantes

Cada uno sobre una copia limpia de control; «cazado» = alguna suite pasó de
verde a rojo **por la prueba esperada** (las cinco de red de `pruebas_voz`
no cuentan: están rojas en el control).

| Id | Archivo:línea | Qué rompe | Cazado | Prueba que lo cazó | Esperado |
|---|---|---|---|---|---|
| M01 | `ui.py:431-438` | `_css_paleta` devuelve `""` | **no** | — | sobrevive (prueba devuelve lista) |
| M02 | `ui.py:754-755` | `_opciones_libros` vacío | **no** | — (extremas + integración) | sobrevive |
| M03 | `ui.py:265` | cubos voz/sinopsis → lexico | **no** | — | sobrevive (tupla) |
| M04 | `ui.py:2295-2296` | no devolver el uso sin llamada | sí | el cupo cuadra con las llamadas de pago | sí |
| M05 | `ui.py:1727-1730` | sinopsis sin puerta | sí | la sinopsis pide codigo | sí |
| M06 | `ui.py:2449-2451` | voz sin puerta | sí | la practica de voz pide codigo (+ el cupo cuadra) | sí |
| M07 | `cuentas.py:177` | cualquier contraseña vale | sí | entrar con una clave mala no abre nada (+ acentos) | sí |
| M08 | `ui.py:143` | id del navegador sin sanear | sí | sin localStorage no revienta | sí |
| M09 | `ui.py:175` | ignorar la identidad del navegador | sí | los datos sobreviven a recargar | sí |
| M10 | `ui.py:86` | `allowed_paths` = raíz de datos | sí | allowed_paths: sirve el audio y nada mas | sí |
| M11 | `ui.py:1499-1501` | `dificultad` sin validar | sí | analisis y sinopsis mal formados | sí (esperaba «a medias»; la caza la otra) |
| M12 | `reader.py:174` | respaldo alfabético | sí | sin spine, los capitulos van en orden natural | sí |
| M13 | `scoring.py:99` | regla de maquetado apagada | sí | el filtro sigue rechazando menus… (`tests_smoke` NO) | sí |
| M14 | `ficha.py:430-433` | media de medias | sí | el caso que destapo la auditoria | sí |
| M15 | `ui.py:1411` | `_cefr` con `round()` | sí | la interfaz y el contrato dan la misma letra (**no** «los limites de la tabla») | sí |
| M16 | `ui.py:1290-1292` | abrir en la portadilla | sí | abrir un libro no cae en la portadilla + 3 pasos de integración | sí |
| M17 | `ui.py:1054` | HTML sin escapar | sí | script incrustado, img onerror | sí |
| M18 | `ui.py:1383` | solo `FileNotFoundError` | sí | medir con el modelo inalcanzable | sí |
| M19 | `ui.py:2301` | cuaderno registra basura | **no** | — | sobrevive |
| M20 | `ui.py:951` | rescate A1 apagado | **no** | — | sobrevive |
| M21 | `ui.py:586-587` | cuestionario mapeado al revés | **no** | — (extremas + perfil) | sobrevive |
| M22 | `perfil.py:253` | `PESO_FRAGMENTOS = 0` | sí | `pruebas_perfil` (`mixto == 1.27`) | sí |
| M23 | `lexicon.py:675` | ignora `usar_openai` | sí | `pruebas_lexicon` 6.1 (extremas no) | sí |
| M24 | `lexicon.py:686-687` | clave de audio sin normalizar | sí | `pruebas_lexicon` 6.3 | sí |
| M25 | `voz.py:186-187` | mp3 con marca de tiempo | sí | `test_cache_anterior_se_invalida_y_la_nueva_sirve_sin_clave` | sí |
| M26 | `ui.py:1169-1172` | marcapáginas compartido en la nube | **no** | — (extremas + integración) | sobrevive |
| M27 | `ui.py:2308, 2540` | cuaderno sin petición | **no** | — (extremas + integración) | sobrevive |
| M28 | `ui.py:2415` | todo en verde | **no** | — (voz: solo las 5 de red del control) | sobrevive |
| M29 | `ui.py:3195` | sin `demo.queue` | sí | la cola admite a mas de uno | sí |
| M30 | `ui.py:2214` | oración sin recortar | sí | lo que viaja a OpenAI va recortado | sí |
| M31 | `ui.py:2250` | cobrar sin clave | sí | el cupo no baja sin clave de OpenAI | sí |
| M32 | `ui.py:1711` | sinopsis guardada ignorada | **no** | — | sobrevive |
| M33 | `catalogo.py:273` | `por_nivel` sin holgura | **no** | — | sobrevive |
| M41 | `lexicon.py:298` | siempre la primera acepción | sí | `pruebas_desambiguacion` (4 casos) + `pruebas_lexicon` (peeped, set off, notwithstanding) | sí |
| M42 | `reader.py:154` | manifiesto solo con `id` antes de `href` | sí | el orden de los capitulos es el del spine (+ portadilla) | sí |
| M45 | `ui.py:1654` | `exigente` invertido | **no** | — | sobrevive |
| M46 | `ui.py:728` | todo marcado abrible | **no** | — | sobrevive |

24 cazados, 13 supervivientes. Todos los cazados cayeron por la prueba
prevista; en M11 y M15 la prueba que saltó fue otra que también cubre el caso,
y lo anoto porque la que **parecía** protegerlos no lo hacía.

---

## Comprobado y estaba bien

- El control pasa entero (arriba). La suite corre sin clave real y sin red y
  no gasta.
- **Dinero:** los tres manejadores cobran antes de llamar y solo cuando puede
  salir algo; sin clave no se cobra; sin perfil no se llama; `consumir`
  atómico y con suelo en cero; devolución en acierto de caché y cuando el
  consultor no se construye; `lexicon` con `usar_openai=False` no toca
  `openai`; clave del audio normalizada; `voz` cachea por contenido; todos los
  clientes con `timeout` y `max_retries`; topes por hora vivos, por IP, por
  cubo y de 3.600 s; el tope de descargas de Gutenberg no cuenta lo cacheado.
- **Datos:** carpeta por lector desplegada; identidad saneada y persistente;
  `allowed_paths` solo audio; el Space no sirve nada fuera de eso (403 ×5);
  `Radio`/`Dropdown` validan contra las opciones de la sesión; `sesion.json`,
  `perfil.json`, `analisis/*.json` y `*-sinopsis.json` con forma torcida no
  tumban el arranque; `lexicon.db` compartida es caché y no historial.
- **Excepciones:** 262 pruebas y todos los ataques con entradas raras que
  probé (`n=None`, índices imposibles, JSON basura, rutas muertas, epub que no
  es zip) vuelven como texto. El agujero es solo S1.
- **Cifras:** todas las de la tabla de arriba, incluidas las que produce
  `validar_local.py`, `contar_guion.py`, pandas sobre el CSV y la ejecución
  del cuadernillo. El `.tex` compila limpio con `tectonic` desde una copia:
  48 `\ref` y 59 `\label`, **cero referencias rotas**, 5 desbordes todos por
  debajo de 20 pt, y el PDF resultante mide lo mismo que el entregado
  (1.151.040 B). `presentacion.tex` también compila.
- **Numeración de cuadros** `.md`↔PDF tal como la anuncia la cabecera del
  `.md`.
- **Space:** `RUNNING`, `cpu-basic`, `gcTimeout 172800`, `app_file: app.py`,
  `sdk_version: 6.26.0`, `app.py` pasa `allowed_paths` y `max_file_size`; los
  quince archivos de código y datos ligeros idénticos al local.
- **Gradio:** las firmas de todos los manejadores con `peticion` reciben el
  `Request` (la prueba lo pasa por `special_args` real); `_desde_cuestionario`
  con `peticion` antes de `*valores` funciona (el nivel 1,20 se guardó en la
  carpeta del lector, no en `anonimo`).
- **Contraste:** las 85 parejas pasan; el CSS no clava colores; la gráfica
  lee la paleta.
- **Lector:** epub con `href` antes de `id`, orden natural sin spine,
  cabecera corrida de Gutenberg fuera del título, portadilla saltada,
  licencia recortada dentro del capítulo, `_es_boilerplate` con la envoltura
  quitada; 52 falsos rechazos de la regla absoluta ya no ocurren (menú,
  índice, tabla y lista sí se rechazan).
- **Guion:** 561 palabras, 3:44, seis bloques; el recorrido (1,20; Notes
  from a Dead House; 130.104; 487; 86 s; 1,73; 40 ms) es el mismo en
  documento §8.2, diapositiva 8 y guion.

---

## Lo que se vería en los tres primeros clics de la demo, o en la primera lectura del PDF

**En la demo, en este orden de aparición:**

1. **Si el Space se reinició antes de grabar** (por ejemplo por un
   `desplegar_app.py` esa mañana), el paso «Dos» del guion —escribir
   «dostoyevski» y pulsar Buscar— se queda **más de un minuto** en
   «processing» delante de cámara (S2; el `.npy` subido no se lee). «Ver
   libros para mi nivel» no lo sufre. Arreglo de una línea en `catalogo.py`,
   o simplemente no reiniciar el Space antes de grabar y hacer una búsqueda de
   calentamiento.
2. **Tercer clic**: «4 capítulos · 25.077 palabras» arriba y «21.938 palabras
   en 4 capítulos» tres líneas más abajo (m3). Es lo primero que un profesor
   compara.
3. **Cuarto clic**: el contexto citado empieza «I I One morning…» (m4) y el
   aviso «acepcion provisional: margen bajo (0.004)» sale sin acentos y en
   jerga (m5). Y lo que se dice a cámara —«en 40 milisegundos… en esta
   frase… la gramática»— no es lo que pasa: la gramática llega quince
   segundos después (m6).
4. **Si hay que recargar** por lo que sea: usuario y contraseña otra vez (m2).

**En la primera lectura atenta del PDF y las diapositivas:**

1. La diapositiva 6 con «aquí decía 1,06…» (S5). Es lo único que un
   evaluador puede tomar como descuido flagrante, y se quita en un minuto.
2. La limitación 12 y las conclusiones afirmando que la app «no guarda nada
   entre reinicios» mientras `DESPLIEGUE.md` y la propia app dicen lo
   contrario (S4): o el documento se vende por debajo de lo que hace, o el
   despliegue no es lo que dice ser; en los dos casos se nota.
3. «Cinco auditorías externas» en un proyecto que ha ido por catorce (m8), y
   la etiqueta «Solo libros que pueda leer» presentada como corrección cuando
   la app la desechó (m7).

**Orden sugerido para el viernes, por coste y por lo que se ve:** S5 (un
minuto) → m3 y m5 (dos cambios de una línea en `ui.py`) → m6 (dos frases del
guion) → S4 y m8 (párrafos del documento y recompilar) → S2 (una línea y una
entrada en la prueba; redesplegar **y hacer una búsqueda** antes de grabar) →
S1 (cuatro `except Exception`) → m2 → y, cuando haya tiempo, las pruebas de
S3, empezando por el marcapáginas y el cuaderno con dos sesiones, que es la
red que el proyecto más ha echado de menos.
