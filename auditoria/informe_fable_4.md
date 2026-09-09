# Auditoría externa nº 4 (Fable) — el código y lo que recibe el usuario

**Fecha:** 9 de septiembre de 2026. **Ámbito:** `app/ui.py`, `app/scoring.py`, `app/ficha.py`, `app/catalogo.py`, `app/cuentas.py`, `pruebas_extremas.py`, `colab_precalculo.py`; `lexicon.py`, `perfil.py`, `reader.py` y `main.py` leídos solo para comprobar contratos. No se ha modificado ningún archivo del proyecto.

**Método:** cada hallazgo marcado *[reproducido]* se disparó ejecutando el módulo real con `python -X utf8` desde un directorio temporal (`LITERALEVEL_DATOS`), sin modelo cargado y sin red. Los marcados *[por lectura]* se sostienen en el flujo de control citado línea a línea. No se ha abierto nada de `auditoria/` salvo para escribir este archivo.

**Recuento:** 2 CRÍTICOS · 6 SERIOS · 5 MENORES · 3 DUDAS.

---

## CRÍTICO

### C1. «¿De qué trata?» llama a gpt-5 sin código, sin límite por hora y sin contar el uso

- **Dónde:** `app/ui.py:1280-1321` (`_de_que_trata`), en concreto `1290` (`cliente = consultor()._cliente()`) y `1297` (`datos = ficha.sinopsis(libro, cliente)`); `app/ficha.py:255-301`.
- **Caso que lo dispara:** un visitante cualquiera del Space, **sin código**, sube un archivo (o abre uno del catálogo) y pulsa el botón de sinopsis. `_de_que_trata` no llama a `_puede_pagar`, ni a `_dentro_del_limite`, ni a `_apuntar_uso`; ni siquiera recibe `peticion: gr.Request`, así que no podría limitarse por IP aunque se quisiera. Cada pulsación es una llamada a `gpt-5` con cuatro pasajes de 900 palabras (`ficha.py:226-227`).
- **Por qué la caché no protege:** la sinopsis se guarda por `_clave_libro` (`ui.py:1098-1108`) = título + palabras + títulos de los 40 primeros capítulos. Basta cambiar una palabra del `.txt`, o subir archivos distintos, para que cada clic sea una llamada nueva. El tope de subida es 20 MB (`ui.py:74`).
- **Lo que dice el proyecto de sí mismo:** `cuentas.py:6-7` («Lo que si cuesta son dos cosas») y el acordeón de la app, `ui.py:2366-2368` («las dos únicas cosas que cuestan dinero»). Hay una tercera, y es la única que está completamente abierta. Es exactamente el escenario que `cuentas.py:8` describe como el que se quería impedir: «cualquiera puede agotar el saldo de Miguel en una tarde».
- **Verificación:** por lectura del flujo (no se ha llamado a OpenAI). `_cliente()` (`lexicon.py:589-601`) devuelve el cliente siempre que exista `OPENAI_API_KEY`, sin mirar ningún código.

### C2. El tope de usos de un código no es un tope: `permite` y `apuntar` no son atómicos y `apuntar` pierde incrementos

- **Dónde:** `app/cuentas.py:115-128` (`apuntar`: lee, suma, escribe, sin candado; el `except Exception: pass` de la línea 127 se traga cualquier fallo); `app/cuentas.py:131-150` (`permite` consulta el contador y no lo reserva); `app/ui.py:195-203` (`_puede_pagar` / `_apuntar_uso`, sin candado: `_CANDADO_CODIGO` solo protege el diccionario de sesiones); `app/ui.py:1694-1698` y `1832-1835` (la comprobación y el apunte van separados por la llamada de pago entera).
- **Caso que lo dispara [reproducido]:** código `invitado:LLAVE-B:2` (tope 2) y 20 peticiones simultáneas que hacen lo mismo que `_consultar`: `permite` → `apuntar`. Resultado: **20 llamadas de pago pasan y el contador acaba en 1**. Reproducido también en secuencia: dos hilos × 200 `apuntar` sobre la misma cuenta dejan el contador en **41 de 400** (en Windows, `os.replace` falla con `PermissionError` cuando otro hilo tiene el archivo abierto y la línea 127 lo silencia; en Linux la pérdida es por lectura-modificación-escritura sin bloqueo, menor pero real).
- **Consecuencia para el usuario:** dos lectores que comparten un código de prueba, o un código filtrado usado en paralelo, gastan lo que quieran. El código es la única barrera entre un enlace público y el saldo; y `_consultar` es generadora con 23-39 s de espera a OpenAI (`AGENTS.md`), así que la ventana de carrera no es de milisegundos: es de medio minuto por petición.
- **Nota:** `cuentas.py:28-31` avisa de que «no hay bloqueo entre procesos». Aquí no lo hay ni entre hilos del mismo proceso, que es el caso del Space.

---

## SERIO

### S1. El contador de usos falla *abierto* en todos sus caminos de error

- **Dónde:** `app/cuentas.py:62-66` (tope ilegible → `n = 0` → «sin límite»; tope negativo → `max(0, n)` → «sin límite»); `app/cuentas.py:95-101` (`_leer` devuelve `{}` ante cualquier excepción, incluido JSON corrupto).
- **Casos [reproducidos]:** `LITERALEVEL_CUENTAS="prueba:abcd1234:6O"` (una O por un cero, en un secreto que nadie ve escrito) → `Cuenta(tope=0)`, `queda` = `None` = ilimitado. `otro:zzzz:-5` → ilimitado. `uso_openai.json` con contenido `{corrupto` → `gastado` = 0 y `permite` = `(True, '')` para un código que podía estar agotado.
- **Por qué es serio:** en un sistema de cupos la única dirección segura de fallo es cerrarse. Un error de escritura del secreto o un archivo dañado convierten un código de 60 usos en uno infinito, y nada en la interfaz lo delata salvo que quien canjea lea «Sin límite de usos» y le extrañe.

### S2. Un libro de un solo capítulo «se va soltando»

- **Dónde:** `app/ui.py:1403-1410` (`_resumen_analisis`): `mitad = len(medias) // 2 or 1`, `principio` = media de `medias[:1]`, `final = sum(medias[1:]) / max(1, 0)` = **0.0**; como `principio - 0.0 > 0.12` siempre que la dificultad supere 0,12 (siempre), sale «**se va soltando**: cuesta más al principio que al final».
- **Caso [reproducido]:** `datos` con una sola fila de dificultad 0,90 → el texto afirma que el libro se suelta, seguido de «Lo más llevadero: capítulo 1 · Lo más exigente: capítulo 1 · Recorrido 0.90 a 0.90». Y no es un caso raro: **cualquier `.txt` sin encabezados de capítulo** (un cuento, un artículo, un fragmento pegado en un archivo) lo carga `reader` como **un único capítulo «Texto completo»** [reproducido con un archivo de 8.800 palabras]. Ninguna de las 198 pruebas pasa por `_resumen_analisis` con una sola fila.

### S3. El freno «por hora» apaga el diccionario gratuito, que es lo que la app manda usar al principiante

- **Dónde:** `app/ui.py:1688` (`_dentro_del_limite(peticion, "lexico", 30)`) se consume **antes** de `app/ui.py:1694` (`_puede_pagar`). Sin código, `usar_openai=False` y la consulta no cuesta nada (`lexicon.py:647-654`), pero la ficha del cubo se gasta igual.
- **Caso [por lectura]:** un visitante sin código consulta 30 palabras en una hora; en la 31.ª recibe `_mensaje_limite` (`ui.py:225-232`): «Has llegado al límite de consultas de esta hora… Leer, buscar y medir un capítulo siguen funcionando: no cuestan nada». La consulta tampoco costaba nada. El comentario de `ui.py:127-129` («treinta palabras consultadas en una hora es mucha lectura») describe a un lector intermedio; `_recomendar` (`ui.py:693-697`) le dice al lector A1 que lea por encima de su nivel y «usa el doble clic sobre las palabras». Es el usuario que más palabras va a consultar, y el que primero se queda sin diccionario, con un mensaje que le habla de un gasto que no existe.
- **Agravante:** el mismo cubo se consume aunque la consulta falle después (`ui.py:1699-1701`) y, en voz, aunque `_puede_pagar` diga que no (`ui.py:1827` antes de `1832`).

### S4. Precálculo: una descarga cortada entre 10,0 y 11,28 GB deja el cuaderno inservible hasta borrar a mano

- **Dónde:** `colab_precalculo.py:271` (`ZIP_LOCAL.stat().st_size > 10 ** 10` se toma por «descarga completa»); `colab_precalculo.py:326-365` (`extraer` no tiene ningún `try`); `colab_precalculo.py:387-388` (`if bajar_archivo(): sacados = extraer(QUIERO)` — el respaldo solo corre en el `else`).
- **Caso [reproducido el mecanismo]:** el archivo mide 11.278.856.242 bytes; si la conexión se corta pasado el 89 % (`timeout=120` en `urlopen` es por operación de socket, y Colab corta sesiones), queda en `/content` un parcial de más de 10 GB. En la siguiente ejecución `bajar_archivo` dice «ya esta en /content» y devuelve `True`; `zipfile.ZipFile` sobre un zip truncado lanza `BadZipFile: File is not a zip file` (el directorio central está al final del archivo; reproducido con un zip recortado al 90 %). La celda muere, el respaldo libro a libro nunca se alcanza, y así en cada reejecución mientras exista `/content/txt-files.tar.zip`. Ningún mensaje dice qué borrar.

### S5. Precálculo: dos caminos «de respaldo» que no existen, y un tar corto que se calla

- **Dónde:** `colab_precalculo.py:330-331`: «el zip no contiene un .tar; se usa el metodo antiguo» y `return 0`. Pero el llamador (`387-388`) hace `sacados = extraer(QUIERO)` y sigue con 0 textos: el método antiguo solo se ejecuta si `bajar_archivo()` devolvió `False`. El mensaje anuncia un respaldo que no se ejecuta.
- **Tar truncado dentro de un zip válido [reproducido]:** `tarfile` en modo `r|` trata el fin de fichero a mitad de cabecera como fin de archivo, **sin excepción**: la extracción termina corta y el único indicio es el porcentaje de «TEXTOS LISTOS» (`399-401`), que nadie compara con nada. Tampoco hay comprobación de recuento contra `QUIERO`.
- **Disco lleno durante la extracción [por lectura]:** `destino.write_bytes(datos)` (`361`) no es atómico; un `OSError` mata la celda y deja `pg<n>.txt` a medias; al reejecutar, `if destino.exists(): continue` (`354`) lo da por bueno y el libro truncado se mide como si fuera corto. Lo mismo vale para el respaldo (`183`).

### S6. Precálculo: la comprobación fp16/fp32 y la medida de velocidad se saltan en silencio con el flujo nuevo

- **Dónde:** `colab_precalculo.py:446` (`muestra = sorted(TEXTOS.glob("*.txt"))[:5]`) lee de **Drive** (`TEXTOS`), no de `TEXTOS_LISTOS`/`LOCAL`, que es donde la celda 6b acaba de extraer los textos. Por diseño del propio cuaderno «Los textos NO se guardan en Drive» (líneas 17-22).
- **Caso [por lectura]:** Drive sin restos de tandas anteriores → `bloques = []` → `if MEDIA_PRECISION and bloques:` (`454`) e `if bloques:` (`469`) no entran. No se imprime desviación ni velocidad, y la celda 10 arranca en `fp16` sin la verificación que el cuaderno presenta como condición («Antes de medir 61.000 libros con él hay que saber CUÁNTO cambia»). Esa celda es la que respalda que el catálogo precalculado coincide con lo que la app calcula en vivo.

---

## MENOR

### M1. La contradicción «cifra intermedia · orientativo C1» que `public_band` promete imposible, sigue siendo posible

- **Dónde:** `app/scoring.py:306` (`puntuacion=round(pub, 3)`, pero `banda=public_band(pub)` con `pub` sin redondear); `app/ui.py:1039` (`_medir` muestra `_cefr(r.puntuacion)`, el ancla de la cifra **redondeada**).
- **Caso [reproducido]:** interno 3,4996 → `puntuacion` 1,4 · `banda` «intermedio» · `_cefr(1.4)` = C1 → la línea que ve el usuario: «**1.40 / 2.00** (intermedio) · orientativo **C1**». Barrido de 50.000 internos entre 0 y 5: 24 caen en la trampa (intervalos [1,4988, 1,499] y [3,4997, 3,4999]). Es exactamente lo que `scoring.py:123-124` dice que «nunca mas saldra». Raro; cuando pase, pasará en la pantalla de la demo.

### M2. Se cobra un uso que no costó nada, y se cobra antes de saber si funcionó

- **Dónde:** `app/ui.py:1697-1698` cobra siempre que `puede`, sin mirar `r.desde_cache` (`lexicon.py:687`: respuesta servida de la caché compartida, cero llamadas) ni el caso «sin sentido elegido» (`lexicon.py:689`: la palabra no está en el diccionario y no se pide explicación). `app/ui.py:1835` (`_practicar`) apunta el uso **antes** de `voz.practicar`; una grabación ilegible (`except Exception` en `1846`) cuesta un uso.
- **Caso:** un lector con código de 60 usos consulta «brook» que otro lector ya consultó en la misma oración y banda: uso descontado, gasto real cero. La contabilidad juega contra el usuario en un sentido y contra Miguel en el otro (C2).

### M3. Dos visitantes abriendo el mismo libro del catálogo a la vez

- **Dónde:** `app/ui.py:604` (`destino.exists() and st_size > 2000` = «ya está») y `622` (`final.write_bytes(datos)`, no atómico, en `RUTA_LIBROS`, carpeta compartida por todas las sesiones, `ui.py:581`).
- **Caso [por lectura]:** el segundo visitante llega cuando el epub lleva 3 KB escritos: lo da por bajado, `reader.cargar` recibe un zip a medias y ve «[!] No pude abrir el archivo (BadZipFile)». Ventana corta; molesto porque el mensaje culpa al archivo. Además `RUTA_LIBROS` ignora `LITERALEVEL_DATOS`, así que una prueba que llegara a descargar escribiría en los datos reales (el mismo fallo que motivó `ui.py:95-99`).

### M4. El filtro de extracción admite variantes que no sabe distinguir

- **Dónde:** `colab_precalculo.py:337-347`. [Reproducido] pasan el filtro `cache/epub/84/pg84.txt`, `pg84-images.txt`, `pg84-0.txt` y `8/4/84/84-8.txt`; el primero en orden de tar gana y los demás se saltan por `destino.exists()`. Un `-8` es Latin-1 y `reader.py:133` lo abre como UTF-8 con `errors="replace"`: acentos convertidos en «�» que el modelo puntúa. El docstring (`306-318`) afirma que solo existe `pg<n>.txt`, comprobado sobre los primeros 3 MB de 11,3 GB. Puede ser cierto; no está demostrado.

### M5. `_cefr` convierte la basura en A1

- **Dónde:** `app/ui.py:1057-1059`: `float(publico)` falla → `return scoring.ANCHORS[0]`. Un error de tipo se presenta como «nivel A1». Hoy solo se alcanza por un bug; cuando ese bug llegue, la pantalla dirá A1 en lugar de fallar.

---

## DUDA (no verificable sin desplegar)

### D1. La IP detrás del proxy de Hugging Face
`app/ui.py:140-152`: si el Space no reenvía `x-forwarded-for`, todos los visitantes comparten `peticion.client.host` (o «desconocida»): un solo cubo de 30 consultas/hora **para todo el Space**. Combinado con S3, el diccionario dejaría de funcionar para todos a la 31.ª palabra de la hora, sea de quien sea.

### D2. El 2,6× de espacio
`colab_precalculo.py:281`: `_hay_espacio(total * 2.6)` = 29 GB. El factor no sale de ninguna medida escrita; los `.txt` en inglés descomprimidos más el zip pueden superar esa cifra. En una VM de Colab Pro sobra disco; en otra, el fallo sería el de S5 (disco lleno a media extracción), no un aviso previo.

### D3. Un «Analizar el libro entero» de 500.000 palabras en CPU Basic
`_analizar_libro` (`ui.py:1147`) mide ventana a ventana; con la concurrencia por defecto de Gradio (1 por manejador) un segundo visitante que pulse el mismo botón espera minutos. No medido.

---

## Contratos entre módulos (encargo nº 2)

Comprobado, y **se cumple**: la escala pública 0..2 es la única que sale de `scoring.py`. `perfil.py:29` declara `nivel` en 0..2 y las opciones del cuestionario están en 0..2 (`perfil.py:81-186`); `catalogo.py:30` (`NIVEL_A_PUNTUACION = i*0.4`) y `234` (afinidad dividida por 2,0) trabajan en 0..2; `lexicon.py:616` convierte con `public_band(nivel)`; `ficha.dificultad_global` recibe dificultades públicas (`_analizar_libro` usa `perfil_de_texto`, que devuelve `public_score`); `_cefr` (`ui.py:1057`) multiplica por 2,5 antes de mirar `ANCHORS`. `Resultado.confianza` (`scoring.py:165-170`) usa umbrales en escala interna sobre `por_bloque`, que es interna: coherente. El precálculo (`colab_precalculo.py:409-421`) guarda `public_score` redondeado a 3 decimales, como la app. No he encontrado ningún punto donde una función reciba una escala y trate la otra.

## Lo que las pruebas no ejercitan (encargo nº 3)

`pruebas_extremas.py` declara 198 pruebas y llama a 48 símbolos de `ui`. Manejadores de `ui.py` que **ninguna prueba llama**: `_canjear`, `_puede_pagar`, `_apuntar_uso`, `_codigo_de`, `_sesion_de`, `_perfil_inicial`, `_limpiar_consulta`, `_mis_palabras`, `_repasar`, `_mis_libros`, `_diagnostico`, `_descargar_gutenberg` (solo indirectamente), `_analisis_guardado`, `_guardar_analisis`, `_clave_libro`. Y tres que se llaman pero **nunca alcanzan la rama de pago**: `_de_que_trata` (solo con `None` y con libro vacío, líneas 658-660), `_practicar` (tres llamadas, líneas 553-556, todas salen antes de `_puede_pagar`), `_consultar` (una llamada). Las siete pruebas de `cuentas` (líneas 883-941) son secuenciales, con tope bien escrito y JSON sano.

**El hueco peligroso es uno:** toda la puerta del dinero en su forma real —el canje por sesión, el cobro concurrente, la sinopsis— tiene cero cobertura. C1, C2 y S1 viven exactamente ahí. El segundo hueco es `_resumen_analisis` con una fila (S2), que es el caso más común de un `.txt` subido a mano.

## Concurrencia y estado compartido (encargo nº 4)

- Bien protegido: los tres recursos pesados (doble comprobación con `_CANDADO`, `ui.py:372-399`), el cubo de gasto por IP (`_CANDADO_GASTO`, `ui.py:155-179`), el diccionario de códigos por sesión (`_CANDADO_CODIGO`), los datos por lector resueltos por `session_hash` saneado (`_dir_lector`, `ui.py:107-120`), las cachés de análisis por hash de contenido (compartirlas es correcto).
- Sin proteger: el contador de usos (C2), la descarga de Gutenberg (M3), `_RONDA_FRASE` (`ui.py:1735`, diccionario global sin candado ni tope: inofensivo, crece con cada par libro/capítulo que alguien practique), y las escrituras `write_text` de `_guardar_analisis`/`_guardar_sesion`/sinopsis (no atómicas; un lector concurrente ve JSON parcial, `_analisis_guardado` lo trata como inexistente y remide: correcto, solo cuesta tiempo).

## Lo que está bien y podía estar mal

- `_cap` (`ui.py:981-994`) valida índice `None`, cadena y fuera de rango antes de indexar; `_reanudar` y `_seguir_leyendo` recomprueban el capítulo guardado contra la longitud real.
- `_abrir` atrapa **todo** a propósito (`BadZipFile`, `PdfStreamError` no descienden de `OSError`) y lo dice en el comentario.
- `fixed_blocks` y `continuous_prose` no dividen por cero: `cortas / len(lineas)` va detrás de `len(lineas) >= 6`; `_suavizar` corta en `len < ventana`; `ficha.caracteristicas` guarda cada división con `if frases`/`if muestra`; `dificultad_global([])` devuelve 0,0 y `_ficha_libro` lo trata como «no exigente».
- `cuentas.validar` compara en tiempo constante y el código no viaja en ningún `gr.State`.
- `cuentas.apuntar` escribe por `.tmp` + `os.replace`: el archivo nunca queda a medias (el problema de C2 es otro).
- `Libro.url_gutenberg` solo enlaza ids `PG…`; `_descargar_gutenberg` rechaza StoryWeaver con un mensaje útil.
- `gr.Number` de resultados tiene `minimum=1, maximum=50, precision=0` (`ui.py:2184-2185`), así que `n=0` (que devolvería «Ningún libro supera el umbral (el mejor llegó a 1.00)», reproducido llamando a `Catalogo.buscar` directamente) no es alcanzable desde la interfaz.
- `main.py` solo escucha en `0.0.0.0` en la nube y pasa `max_file_size` y `allowed_paths`.
- `_dir_lector` sanea el `session_hash` (`[^A-Za-z0-9_-]`, 64 caracteres): no hay travesía de rutas.
- En el precálculo, `descargar` lee `DESTINO_TEXTOS` en tiempo de llamada, así que el respaldo, cuando de verdad corre, escribe en `/content` y no en Drive; el filtro de extracción sí rechaza `readme.txt` [reproducido]; `perfil_de_libro` usa `ficha.capitulos_de_cuerpo`, el mismo filtro que la app.

---

## Veredicto

Lo más peligroso que puede pasarle hoy a un usuario de la aplicación no es un error que vea, sino uno que no verá: **cualquier visitante sin código, con el botón «¿De qué trata?» y archivos distintos, puede consumir el saldo de OpenAI de Miguel a razón de una llamada a gpt-5 por clic (C1)**, y quien sí tenga código puede sobrepasar su cupo lanzando peticiones en paralelo, porque el contador ni reserva ni cuenta bien (C2). Cuando el saldo se agote, la explicación contextual y la corrección de voz mueren para todos los lectores legítimos a la vez, y la app lo reportará como «sin OPENAI_API_KEY» sin que nadie sepa por qué.

Para el lector de a pie, lo que más probablemente le ocurra esta semana es más modesto: pegar un cuento en un `.txt`, pedir el análisis y leer que el libro «se va soltando» cuando solo tiene un capítulo (S2), o quedarse sin diccionario a la 31.ª palabra de la hora con un mensaje que le habla de un gasto que nunca hizo (S3).
