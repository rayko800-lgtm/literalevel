# Auditoría cruzada a ciegas: API y front (14 sep 2026)

- **Auditor:** entrega-4e.
- **Área:** `app/api.py`, `pruebas_api.py` y `front/src`.
- **HEAD al empezar:** `4d4bb1b`.
- **Método:** solo lectura, con la skill `auditar-proyecto-datos`. No se ha abierto nada de `auditoria/` salvo este archivo.

## Qué se ejecutó y qué solo se leyó

**Ejecutado.** Todo con datos en un temporal, sin claves y sin tocar el repo.

- `python -X utf8 pruebas_api.py`: **51 de 51 bien**.
- Un guion propio contra la API real, con uvicorn en `127.0.0.1`. Lo de pago se sustituye por dobles que duermen 4 s. Así se midieron el bloqueo del bucle, el candado léxico, los cuerpos grandes, el eco del 422, el SVG, el tope de subidas, los recorridos de ruta y las entradas malformadas.
- Peticiones GET al Space publicado (`mikemaki1763-literalevel.hf.space`):
  - `/api/salud` y `/api/estado`;
  - 6 intentos de recorrido de ruta;
  - un preflight CORS desde un origen ajeno.
- El front publicado (`literalevel-front`) en Chrome con viewport emulado de 390×844 (móvil y táctil), en un contexto aislado. Se midió:
  - el desbordamiento horizontal en 8 pantallas;
  - los colores calculados de la pista del lector teñido en 4 libros, en claro y en oscuro.

  La pestaña quedó cerrada.
- El algoritmo de `tinte.ts`, copiado a Node, sobre las 12 familias de `portada.ts`: todos los tonos y saturaciones que pueden salir, 7.380 combinaciones por modo.

**Solo leído.** `ui.py` (identidad, topes, puerta, `_clave_libro`, `_practicar`), `lexicon.py` (qué es `desde_cache` y qué cuenta `llamadas_de_pago`), `ficha.sinopsis`, `voz.registrar_fallos`, el resto de `front/src` y `version.ts`. No se ejecutó `version.spec.ts` ni ninguna prueba de Angular.

**No verificado.**
- Si el proxy de Hugging Face corta los cuerpos grandes antes de llegar a Python. No se probó contra el Space, a propósito.
- La grabación real con micrófono.
- La boca 3D en un móvil de verdad.
- La recarga tras publicar con un despliegue real.

---

## Hallazgos

### [SERIO] `/api/voz` congela el servidor entero mientras corrige

- **Dónde:**
  - [app/api.py:1792](app/api.py#L1792) y [app/api.py:1844](app/api.py#L1844);
  - lo mismo en la subida: [app/api.py:993](app/api.py#L993) y [app/api.py:1043](app/api.py#L1043).
- **Qué dice:**
  > `async def practicar(pet: Lector, request: Request) -> dict:`
  >
  > `s = voz.practicar(tmp, frase, guardar_fallos=False,`
- **Por qué:**
  - La ruta es `async def` para leer el formulario por trozos. Pero después llama de forma **síncrona** a `voz.practicar`, que hace las llamadas a whisper, gpt y tts-1.
  - En una ruta `async`, FastAPI no manda ese trabajo a su hilo: se ejecuta en el bucle de eventos. Mientras dura la corrección, el proceso no atiende ninguna otra petición, ni de la API ni del Gradio montado en el mismo proceso.
  - **Medido:** con un doble de `voz.practicar` que duerme 4 s, `/api/salud` tardó **3,41 s** en responder (en frío, 0,03 s).
  - `subir_libro` tiene el mismo patrón: abre un PDF o epub de hasta 20 MB con `_cargar_libro` dentro de la ruta `async`. Esto último está leído, no medido.
- **Arreglo:** leer el formulario con `await` y pasar el resto a un hilo con `await starlette.concurrency.run_in_threadpool(...)`, en `practicar` y en `subir_libro`.

### [SERIO] La vista previa del diccionario («40 ms») espera a la explicación de pago de cualquier lector

- **Dónde:** [app/api.py:1469](app/api.py#L1469) y [app/api.py:1484-1490](app/api.py#L1484-L1490). La promesa está en [app/api.py:1428-1430](app/api.py#L1428-L1430).
- **Qué dice:**
  > `El front pide primero etapa=diccionario (40 ms, nunca cuesta) y despues etapa=completa (la explicacion de OpenAI, ~15 s)`
  >
  > `with _CANDADO_LEXICO:` … `r = ui.consultor().consultar(palabra_, oracion, _nivel(pet), idioma=idioma, usar_openai=puede)`
- **Por qué:**
  - El candado es global y la etapa completa lo retiene **durante la llamada a OpenAI**.
  - Cualquier consulta de diccionario de cualquier lector espera detrás. También la del mismo lector que toca una segunda palabra mientras la primera se explica: el cliente pide las dos etapas y la completa sigue viva en el servidor aunque la pestaña ya no la quiera.
  - **Medido:** con un doble de `consultar` de 4 s en la etapa completa de otro lector, la etapa `diccionario` tardó **3,41 s**. `/api/salud`, a la vez, tardó 0,0 s: el candado es lo que frena, no el pool.
- **Arreglo:** retener el candado solo en la parte local (diccionario y embeddings) y soltarlo durante la llamada de red. Esto es un cambio en `lexicon.py`, de Codex. Mientras tanto, como mínimo, que la etapa `diccionario` no comparta candado con la completa.

### [MENOR] La pista del lector teñido baja de 4,5:1 en tema claro, con libros reales publicados

- **Dónde:**
  - [front/src/app/compartido/tinte.ts:14-15](front/src/app/compartido/tinte.ts#L14-L15) y [tinte.ts:50](front/src/app/compartido/tinte.ts#L50);
  - [front/src/app/pantallas/lector.css:32](front/src/app/pantallas/lector.css#L32);
  - [front/src/app/pantallas/lector.html:78](front/src/app/pantallas/lector.html#L78).
- **Qué dice:**
  > `/** Enlaces, chips y botones con color de acento sobre el fondo teñido: AA. */ export const CONTRASTE_ACENTO = 4.5;`
  >
  > `acentoSuave: hslAHex(tono, sat, oscuro ? 22 : 88),`
  >
  > `.pista { … background: var(--acento-suave); color: var(--acento-texto); }`
- **Por qué:**
  - El acento se ajusta hasta 4,5:1 contra el **fondo** de la hoja. Pero la pista (texto normal, «Toca dos veces una palabra…») lo pinta sobre **`acento-suave`**, que es más oscuro que el fondo, y ese contraste no se comprueba.
  - **Medido en el Space, tema claro:** 4,17:1 en SWV369 y SWV10029, 5,38 en PG11 y 6,20 en PG120. En oscuro, SWV369 da 6,49.
  - **Con el algoritmo copiado, tema claro:** 4.354 de las 7.380 combinaciones de tono y saturación que pueden salir de las 12 familias quedan por debajo de 4,5. El peor caso es 3,84 (aventura). Infantil acumula 2.236.
  - **En oscuro:** 204, solo en misterio y fantasía; el peor es 4,24.
  - Son combinaciones posibles, no ponderadas por cuántos libros hay de cada una.
  - El texto de la hoja sí pasa siempre de 7:1: el mínimo calculado es 11,5. El acento sobre el fondo pasa de 4,5.
  - El índice y el paginador también usan `acento-suave`, pero están fuera de `.hoja` y no llevan tinte.
- **Arreglo:** en `tinteLector`, ajustar el acento contra el más oscuro (en claro) o el más claro (en oscuro) de `fondo` y `acentoSuave`, no solo contra `fondo`.

### [MENOR] Los cuerpos JSON no tienen tope, y el 422 devuelve la entrada entera, contraseña incluida

- **Dónde:** todas las rutas con cuerpo JSON, por ejemplo [app/api.py:741-743](app/api.py#L741-L743) y [app/api.py:932-933](app/api.py#L932-L933). Solo hay un manejador para `Exception` ([app/api.py:102](app/api.py#L102)), así que la validación usa el de FastAPI.
- **Qué dice:**
  > `clave: str = Field(default="", max_length=200)`
  >
  > `consulta: str = Field(min_length=1, max_length=300)`
- **Por qué:**
  - `max_length` se aplica **después** de leer e interpretar el cuerpo entero. El tope multipart de `_formulario` no cubre JSON.
  - **Medido en local:**
    - 30 MB a `/api/buscar` se leen e interpretan (0,57 s) y salen como 422, no como 413;
    - el 422 de FastAPI incluye `input`: 1 MB de consulta devuelve 1,00 MB de respuesta y 5 MB devuelven 5,00 MB;
    - `/api/entrar` con una clave de más de 200 caracteres devuelve la clave en el eco.
  - El eco va a quien la mandó, pero una respuesta del tamaño de la petición es un amplificador barato, y la contraseña acaba en las herramientas de desarrollo y en cualquier registro intermedio.
  - No se probó si el proxy del Space corta antes.
- **Arreglo:** un middleware que devuelva 413 si `Content-Length` pasa de, por ejemplo, 1 MB en lo que no sea multipart. Además, un manejador de `RequestValidationError` que quite `input` del detalle.

### [MENOR] El 429 de subidas dice «límite de consultas» y que medir «no cuesta nada»

- **Dónde:** [app/api.py:997](app/api.py#L997). El mismo texto sale de palabra, sinopsis y voz: [app/api.py:1318](app/api.py#L1318), [app/api.py:1482-1483](app/api.py#L1482-L1483) y [app/api.py:1833](app/api.py#L1833).
- **Qué dice:**
  > `raise _no(429, ui._mensaje_limite("es", ui._minutos_para_la_siguiente("subidas", pet)))`
- **Por qué:**
  - **Medido:** la subida número 13 en la misma hora devuelve «Has llegado al límite de consultas de esta hora. Vuelve a intentarlo en unos 60 minutos. Leer, buscar y medir un capítulo siguen funcionando: no cuestan nada.».
  - Quien subía un libro lee que ha gastado «consultas».
  - Y «medir un capítulo sigue funcionando» ya no es verdad siempre: medir tiene su propio tope de 40 por hora. Lo reconoce la propia API en [app/api.py:873-876](app/api.py#L873-L876) («con estos topes ya no es verdad»), pero solo lo corrige en `_mensaje_tope_medir`.
- **Arreglo:** un mensaje propio para las subidas («Has subido 12 archivos en esta hora…»), y quitar «medir un capítulo» de `_mensaje_limite` o dejar de usarlo en la API.

### [MENOR] «Esta consulta no ha gastado usos» sale también cuando sí se gastó

- **Dónde:**
  - [front/src/app/pantallas/lector.html:310-312](front/src/app/pantallas/lector.html#L310-L312);
  - [app/api.py:1499-1500](app/api.py#L1499-L1500);
  - `app/lexicon.py:171` y `app/lexicon.py:1127`.
- **Qué dice:**
  > `@if (w.desde_cache) { … Respuesta guardada: esta consulta no ha gastado usos.`
  >
  > `elif puede and getattr(r, "llamadas_de_pago", 0) == 0: _devolver(cobrado)`
  >
  > `desde_cache: bool # la EXPLICACION vino de la cache`
  >
  > `llamadas_de_pago = (int(audio_pagado) + int(pedir_explicacion and extra is not None))`
- **Por qué:**
  - El uso solo se devuelve si `llamadas_de_pago == 0`.
  - `desde_cache` solo dice que la **explicación** estaba guardada. `lexicon` lo avisa: «`desde_cache` no valia para saber si se gasto o no».
  - Si la explicación sale de caché pero el audio de tts-1 se genera, se cobra un uso y la ficha dice que no.
  - Esto está leído, no ejecutado.
- **Arreglo:** que la API devuelva `uso_cobrado` (cobrado y con `llamadas_de_pago > 0`) y que el front enseñe la frase solo si es falso.

### [MENOR] Si la corrección de voz falla después de cobrar, el mensaje no dice que se gastó el uso

- **Dónde:** [app/api.py:1852-1853](app/api.py#L1852-L1853), frente a la sinopsis en [app/api.py:1337-1339](app/api.py#L1337-L1339).
- **Qué dice:**
  > `raise _no(502, f"No he podido corregir la grabación ({type(e).__name__}).") from e`
- **Por qué:**
  - No devolver el uso es deliberado y está razonado en `ui._practicar`.
  - Pero el lector lee un fallo sin más, y en su siguiente intento tiene un uso menos sin haber recibido nada. La sinopsis, en el mismo caso, añade «Este intento sí ha consumido uno de tus usos.».
  - **Medido:** con el doble que lanza, la respuesta es exactamente ese 502 sin aviso.
- **Arreglo:** añadir la misma frase que en la sinopsis.

### [MENOR] El servidor acepta grabaciones de cualquier duración hasta 10 MB; el tope de 30 s es solo del front

- **Dónde:** [app/api.py:1749](app/api.py#L1749) y [front/src/app/pantallas/pronunciar.ts:170](front/src/app/pantallas/pronunciar.ts#L170).
- **Qué dice:**
  > `_TOPE_AUDIO = 10 * 1024 * 1024`
  >
  > `if (this.segundos() >= 30) this.pararGrabacion();`
- **Por qué:**
  - whisper-1 factura por minuto de audio. Un cliente escrito a mano, con un perfil válido, puede mandar en un solo uso muchos minutos donde el front manda 30 s.
  - El precio de lista no se ha comprobado hoy.
  - El freno es la contraseña y el cupo de usos, de ahí que sea MENOR.
- **Arreglo:** leer la duración del archivo antes de llamar a whisper y rechazar lo que pase de unos 35 s, o bajar el tope de bytes al tamaño medido de una grabación real de 30 s.

### [MENOR] La caché de SVG puede guardar decenas de MB a petición de cualquiera

- **Dónde:** [app/api.py:1666](app/api.py#L1666) y [app/api.py:1713-1715](app/api.py#L1713-L1715).
- **Qué dice:**
  > `@functools.lru_cache(maxsize=1024)`
  >
  > `ipa: str = Query(..., min_length=1, max_length=60)`
- **Por qué:**
  - La ruta es pública, sin X-Lector y sin tope por hora.
  - **Medido:** un SVG de palabra con 60 caracteres de IPA ocupa **53 KB**. Cada combinación distinta de IPA, `dur` y `una` es una entrada.
  - 1.024 entradas de ese tamaño son unos 54 MB retenidos en el único proceso del Space. Esa cifra sale de multiplicar; la memoria no se midió.
  - Generar uno nuevo tarda 0,03 s, así que se puede llenar la caché en segundos.
- **Arreglo:** `maxsize=128`, o no cachear las peticiones de palabra con `dur` (la variante que se multiplica).

### [MENOR] Nada limita el disco total de libros subidos

- **Dónde:** [app/api.py:206-207](app/api.py#L206-L207), [app/api.py:996](app/api.py#L996) y [app/api.py:1032](app/api.py#L1032).
- **Qué dice:**
  > `_MAX_SUBIDOS = 30                   # libros propios por lector`
  >
  > `_SUBIDAS_HORA = 12                  # intentos de subida por IP y hora`
- **Por qué:**
  - El tope de 30 es por X-Lector, que el cliente elige. El único freno real es el de 12 por IP y hora, a 20 MB cada una.
  - Con un X-Lector nuevo en cada subida, una sola IP escribe hasta 240 MB por hora en el disco persistente, y nada limpia `lectores/*/subidos`.
  - Leído y calculado, no ejecutado.
- **Arreglo:** un tope diario de bytes por IP, o una limpieza de los subidos que no se han abierto en N días.

### [DUDA] La identidad se sanea antes de medirse: cabeceras distintas caen en la misma carpeta

- **Dónde:** [app/api.py:158-161](app/api.py#L158-L161).
- **Qué dice:**
  > `limpio = ui._SESION_SEGURA.sub("", crudo)[:64]`
  >
  > `return limpio if len(limpio) >= _MINIMO_ID else None`
- **Por qué:**
  - **Medido:**
    - `X-Lector: ` seguido de 64 guiones se acepta (200);
    - 20 eñes + `abcdefghijklmnop` se acepta y cae en la carpeta `abcdefghijklmnop`.
  - El comentario pide 16 caracteres para que el id sea «difícil de adivinar», pero se aceptan ids triviales y colisiones por saneado.
  - El front siempre manda un UUID ([front/src/app/nucleo/lector.ts:10](front/src/app/nucleo/lector.ts#L10)), así que solo afecta a clientes hechos a mano. Y la identidad no es autenticación, lo que el propio código declara. Por eso es DUDA y no hallazgo.
- **Arreglo:** rechazar la cabecera si el saneado la cambia, y exigir 32 o más caracteres hexadecimales o forma de UUID.

---

## Comprobado y correcto

- **Recorridos de ruta.**
  - En local, 9 intentos devuelven 404: `..%2F`, `%00` y `....mp3` en portadas, audio, fonemas/rp, articulación, libros y trabajos.
  - En el Space publicado, 6 intentos devuelven 404.
  - Las expresiones regulares de `/api/portadas`, `/api/audio`, `_servir_fonema` y el inventario de `/api/articulacion/{acento}/{archivo}` no dejan pasar ni `/` ni `..` (leído).
- **Sin X-Lector no se tocan datos de lector** y no se crea `lectores/anonimo`: prueba `sin_lector_no_hay_datos`, ejecutada.
- **Perfil, cuaderno, estantería y subidos, aislados por lector**: pruebas ejecutadas. `_ruta_libro` solo busca en la carpeta del lector y `_id_de_ruta` comprueba la carpeta padre (leído).
- **Caché de análisis y sinopsis compartida entre lectores.** La clave es el hash **del texto** (`ui._clave_libro`), así que solo la comparte quien tiene el mismo texto. Un libro subido con el título de otro ya no pisa su curva (leído).
- **Freno de contraseñas.**
  - Va por IP (la última dirección pública de `x-forwarded-for`) y por usuario, y solo gastan ficha los intentos fallidos.
  - Cambiar de X-Lector no lo salta: la sesión de pago se guarda por X-Lector, pero el freno no depende de él.
  - Un id de sesión de Gradio (unos 10 caracteres) no puede colisionar con un X-Lector de 16 o más.
  - Todo esto está leído.
- **Cobro y devolución.**
  - La sinopsis vuelve a mirar la caché dentro del candado por libro **antes** de cobrar. Devuelve el uso solo con `sin_red` o `sin_pasajes`, y a la cuenta cobrada. Pruebas `sinopsis_simultaneas_una_generacion` y `devolucion_va_a_la_cuenta_cobrada`, ejecutadas.
  - `/api/palabra` devuelve solo lo cobrado (prueba ejecutada).
  - El tope por hora solo se gasta si va a costar.
  - Voz no devuelve el uso, a propósito y razonado.
  - Voz prepara el temporal antes de cobrar (prueba ejecutada).
  - La curva mira la cola antes de gastar ficha.
  - Hay topes en medidas (muestra, libro y capítulo), curvas, subidas, descargas, léxico, voz y sinopsis (leído y prueba `topes_de_medir_y_de_la_curva` ejecutada).
- **El multipart se corta antes de interpretarse**: prueba `subida_grande_se_corta_antes_de_leerla_entera`, ejecutada.
- **Entradas malformadas dan 422, no 500.** Medido con: capítulo no entero, `n=abc`, respuestas en lista y palabra sin cuerpo. Un error inesperado sale sin traza: prueba `error_inesperado_sin_traza`, ejecutada.
- **`/api/estado` en el Space** no da rutas ni nombres. Medido: `"perfiles":{"puerta":true,"validos":10,"declarados":10,"avisos":[]}`, catálogo 68536.
- **CORS.** El Space refleja cualquier origen: el preflight desde `https://evil.example` devuelve `access-control-allow-origin: https://evil.example`. Es lo que documenta `para_gradio`. Sin cookies y con la identidad en `localStorage` de otro origen, una web ajena no puede leer los datos de nadie (medido y razonado).
- **`/api/trabajos/{id}` sin X-Lector.** El id es `uuid4` y solo lo recibe quien lanzó el trabajo, o quien abre un libro con el mismo texto (leído).
- **A 390 px, en el front publicado,** ninguna de estas pantallas desborda en horizontal (`scrollWidth` 390 en todas): inicio, encontrar, nivel, pronunciar, ficha de PG11, lector de SWV369, mis palabras y estado. En el lector hay nodos con `right` de unos 750, pero son las páginas siguientes del modo paginado, dentro de su contenedor, y no desbordan la página (medido).
- **El texto de lectura del lector teñido** pasa de 7:1 en todas las combinaciones calculadas: el mínimo es 11,82 en claro y 11,53 en oscuro. En el Space, la hoja da de 13,8 a 15,8 (medido). El acento sobre el fondo, sin `acento-suave`, pasa de 4,5.
- **Recarga tras publicar.**
  - `withNavigationErrorHandler` llama a `recargarSiVersionVieja`, que recarga una vez en el destino, con una marca de 30 s en `sessionStorage` para no entrar en bucle.
  - El `@defer` del 3D, que no pasa por el router, tiene su propio `@error` con «Recargar y reintentar» ([pronunciar.html:221-225](front/src/app/pantallas/pronunciar.html#L221-L225)).
  - Leído; no probado con un despliegue real.
- **Interruptor del 3D.** `BOCA3D_ACTIVO = true`. El import directo mantiene three.js en su propio chunk. Respeta `prefers-reduced-motion` ([boca3d.ts:162](front/src/app/compartido/boca3d/boca3d.ts#L162)) y sin WebGL pinta el corte 2D ([boca3d.ts:182](front/src/app/compartido/boca3d/boca3d.ts#L182)). Leído.
- **Accesibilidad (leído).**
  - Los tres paneles tienen `role="dialog"`, `aria-modal` y cierre con Escape. Los velos con `(click)` son un complemento de Escape.
  - Hay `:focus-visible` global con un contorno de 3 px.
  - Las imágenes de los cortes y del respaldo 3D tienen `alt` descriptivo.
  - El botón de parar la grabación tiene `aria-label`.
- **Textos del front contrastados con el backend:**
  - «Solo lo ves tú, en este navegador» cuadra con X-Lector en `localStorage`;
  - «hasta 20 MB» cuadra con `_TOPE_SUBIDA`;
  - «Borrar el libro subido» llama a `DELETE /api/libros`, que libera el cupo;
  - «Sin formulario y sin cuenta»: leer y consultar el diccionario no piden entrar.
- **`pruebas_api.py`: 51 de 51 bien** en `4d4bb1b`. Cubre identidad, aislamiento, recorridos, cobro y devolución, topes y errores. **No cubre** los dos SERIOS de arriba: ninguna prueba mide concurrencia entre peticiones.
