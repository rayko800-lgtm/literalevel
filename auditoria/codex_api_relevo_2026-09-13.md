# Auditoria de API: relevo de Central, 13 septiembre 2026

## Alcance y evidencia

Revision estatica de `app/api.py` y `pruebas_api.py` en HEAD `f1cfb5d`.
Se leyeron AGENTS.md y CLAUDE.md, y bloques dirigidos de las privadas de
`ui.py` y de los contratos de cuentas, voz y biblioteca. No se leyeron otros
informes de auditoria. No se ejecuto la app, las pruebas, OpenAI ni ninguna
peticion de red. Los escenarios siguientes son recorridos verificables en el
codigo, no reproducciones ejecutadas. Este informe es el unico archivo creado.

El encargo original de Central se referia a `fe01a58`; no se ha auditado esa
version como si siguiera vigente. Entre ella y HEAD, `git diff --stat` muestra
367 lineas de diff en API y 296 en pruebas (619 inserciones, 44 eliminaciones
en conjunto). HEAD ya incluye limites de multipart antes del parseo, topes de
subidas, correccion de devoluciones sin cobro previo en palabra, acento de voz,
animaciones, avisos de contenido y acepciones principales. No se reportan esas
correcciones como problemas abiertos.

Resultado: cuatro hallazgos confirmados por inspeccion; tres serios y uno
menor. No se ha confirmado un critico ni una fuga remota por adivinacion del
identificador de lector.

## Hallazgos

### 1. Serio: dos sinopsis simultaneas pagan la misma generacion

- Ubicacion: `app/api.py:1141`, `app/api.py:1150`, `app/api.py:1161` y
  `app/api.py:1171`.
- Cita: `datos = ui._sinopsis_guardada(lib)` y
  `datos, causa = ficha.sinopsis(lib, cliente)`.
- Escenario: dos peticiones POST a `/api/libros/PG.../sinopsis` del mismo
  libro, sin sinopsis guardada y con cuentas habilitadas. Ambas leen el fallo
  de cache antes de que ninguna escriba, ambas consumen un uso y ambas llaman
  a la generacion. La ultima escritura gana. La puerta atomica de cuentas
  evita rebasar un cupo, pero no deduplica este trabajo. No hay candado ni
  registro de trabajo en curso en la ruta, a diferencia de palabra/curva.
- Efecto: gasto duplicado y dos usos por un resultado compartido. Tambien
  ocurre entre lectores distintos que soliciten el mismo libro a la vez.
- Arreglo propuesto: introducir exclusion por `ui._clave_libro(lib)` compartida
  con Gradio; dentro de ella volver a leer la cache antes de comprobar/cobrar
  y generar. No mantener un unico bloqueo global durante todas las sinopsis.
- Prueba faltante: dos solicitudes sincronizadas con un doble de
  `ficha.sinopsis` y cache temporal; exigir una generacion y un consumo. Hacer
  tambien una pareja API/Gradio si comparten servidor. No se ha probado aqui
  la carrera API/Gradio; la pareja API/API basta para el hallazgo.

### 2. Serio: la devolucion puede ir a otra cuenta o perderse al salir

- Ubicacion: `app/api.py:1317`, `app/api.py:1324`, `app/api.py:1329`;
  mismo patron en `app/api.py:1156`, `app/api.py:1159`, `app/api.py:1164`.
  Contrato: `app/ui.py:605`, `app/ui.py:618`, `app/ui.py:715` y
  `app/cuentas.py:288`.
- Cita: `cuentas.devolver(ui.BASE_DATOS_LECTOR, ui._codigo_de(pet))`.
- Escenario: se consume un uso de la cuenta A y la consulta tarda. Desde otra
  pestana del mismo navegador se llama `/api/salir` antes de que termine. Si
  procede devolver el uso (palabra con `llamadas_de_pago == 0`, o sinopsis sin
  red), `_codigo_de(pet)` ya devuelve None y `cuentas.devolver` no resta nada.
  Si ademas se entra con una cuenta B antes de la devolucion, se resta un uso
  de B, si tenia alguno consumido, y A conserva el cargo.
- Efecto: reintegro perdido o saldo de otra cuenta alterado. No requiere
  adivinar IDs ni acceder a otro navegador: dos pestanas normales bastan.
- Arreglo propuesto: la reserva de pago debe capturar atomicamente el codigo
  realmente cobrado y devolver un comprobante que use toda devolucion; no
  resolver otra vez la identidad mutable. Leer el codigo despues del cobro
  tampoco cierra la carrera. Ajustar el contrato de `_puede_pagar` de forma
  coordinada con Gradio, o anadir un helper compatible para reservas.
- Prueba faltante: pausar un doble de consultor tras el consumo, salir/cambiar
  de cuenta y reanudar con cero llamadas; comprobar saldos A y B. La prueba
  `palabra_que_falla_solo_devuelve_lo_cobrado` (`pruebas_api.py:572`) cuenta
  devoluciones, pero no ejercita el cambio de sesion durante una consulta.

### 3. Serio: voz consume aun cuando falla antes de llamar al proveedor

- Ubicacion: `app/api.py:1620`, `app/api.py:1623` y `app/api.py:1627`.
- Cita: `fd, tmp = tempfile.mkstemp(suffix=ext, prefix="ll_voz_")`;
  comentario: `Sin devolucion del uso en ningun caso`.
- Escenario concreto: clave configurada, cuenta con cupo y formulario valido;
  el directorio temporal no admite escrituras o esta lleno. `_puede_pagar`
  consume, `mkstemp` lanza antes del try y antes de `voz.practicar`, y la
  respuesta generica es 500 sin devolver el uso. Si falla `f.write(contenido)`
  dentro del try, se devuelve 502 pero tampoco se devuelve el uso. En ambos
  casos no ha habido ninguna llamada de voz al proveedor.
- Efecto: se descuenta cuota por fallos locales gratuitos. El argumento de
  que una transcripcion fallida podria haber pagado GPT/TTS no aplica a estos
  dos puntos anteriores a `voz.practicar`.
- Arreglo propuesto: preparar y escribir el temporal antes de reservar pago,
  manteniendo su limpieza en un finally exterior. A largo plazo, extender
  `SesionVoz` con contabilidad explicita de llamadas de pago y su comprobante
  para devolver solo los intentos sin gasto confirmado.
- Limite importante: `SesionVoz` (`app/voz.py:589`) no incluye
  `llamadas_de_pago`. No es correcto devolver siempre al ver
  `transcripcion_ok=False`: `voz.practicar` puede generar explicacion y audio
  despues del fallo de transcripcion (`app/voz.py:629`, `app/voz.py:637`,
  `app/voz.py:646`). No se ha intentado determinar facturacion real de errores
  del proveedor.
- Prueba faltante: hacer que `mkstemp` o la escritura fallen, con dobles de
  cobro y de voz; exigir cero llamadas y cero cuota neta. Las pruebas de voz
  actuales cubren ausencia de clave, audio de detalles y aislamiento, no este
  recorrido de pago.

### 4. Menor: el limite de subidas no se libera con la accion indicada

- Ubicacion: `app/api.py:911`, `app/api.py:912`, `app/api.py:1737` y
  `app/biblioteca.py:101`.
- Cita: `Quita alguno de ... Mis libros ... para subir otro` (mensaje de 429)
  y `biblioteca.olvidar(ruta, ui._archivo_lector("biblioteca.json", pet))`.
- Escenario: el lector alcanza 30 archivos subidos y quita uno desde la
  biblioteca. DELETE solo quita la entrada de `biblioteca.json`;
  `biblioteca.olvidar` no elimina el archivo. La siguiente subida sigue
  contando 30 archivos y devuelve 429. La API no tiene una ruta alternativa
  de borrado de subidos que permita liberar ese espacio. Una subida que nunca
  se anoto con progreso ni siquiera tiene por que aparecer en Mis libros.
- Efecto: el usuario queda bloqueado para nuevas subidas mientras conserve
  su identificador, aunque siga la instruccion del servidor.
- Arreglo propuesto: separar claramente olvidar progreso de eliminar un
  archivo propio; implementar borrado explicito y confirmado del subido,
  acotado a su carpeta, y exponerlo en Angular. No borrar implicitamente
  archivos al ocultarlos de la biblioteca.
- Prueba faltante: con `_MAX_SUBIDOS=1`, subir, anotar progreso, eliminar por
  la accion designada y subir otro. `topes_de_subidas_por_lector_y_por_hora`
  (`pruebas_api.py:552`) cubre el rechazo, no la recuperacion del cupo.

## Puertas de pago revisadas

| Ruta o funcion | Guardas y resultado de la inspeccion |
| --- | --- |
| POST `/api/palabra`, etapa diccionario | `usar_openai=False`; no `_puede_pagar`, no consumo horario. La vista previa no anota en cuaderno. |
| POST `/api/palabra`, etapa completa | Tope lexico condicionado por `_va_a_costar`; despues `_puede_pagar`; consulta con el booleano obtenido. Devuelve si `llamadas_de_pago == 0`. Hallazgo 2 en la identidad del reintegro. |
| POST `/api/libros/{id}/sinopsis` | Cache antes de coste; tope, clave y `_puede_pagar` antes del cliente. Devuelve por cliente ausente/preparacion fallida y causas `sin_red`/`sin_pasajes`. Hallazgos 1 y 2. |
| POST `/api/voz` | Tamano/frase, tope voz, clave y `_puede_pagar` antes de `voz.practicar`. Incluye transcripcion, correccion y TTS dentro de una operacion. Hallazgo 3; no existe contador de llamadas en el resultado. |
| IPA de palabra por IA | No hay ruta IA independiente: forma parte de `consultar` en `/api/palabra` y hereda su puerta. La IPA usada en detalles de voz se consulta mediante `fonemas.ipa_de_palabra`. |
| GET `/api/audio/{nombre}` y `/api/fonemas...` | Sirven archivos existentes; no generan ni llaman a OpenAI. |
| GET `/api/articulacion...` | Generacion SVG local, sin llamada de pago. No se detecto otra ruta OpenAI separada de las anteriores. |

El consumo es por operacion de usuario, no una reserva independiente por cada
subllamada GPT/TTS. No se ha cambiado esa politica ni se afirma que el numero
de usos equivalga al numero de peticiones facturadas.

## Identidad y contratos

- En nube, `X-Lector` se sanea con `[A-Za-z0-9_-]`, se corta a 64 caracteres
  y requiere al menos 16 (`app/api.py:158`). Los datos privados usan `Lector`;
  el cuestionario con lector opcional exige ID cuando `guardar=True`.
- Un ID arbitrario valido abre su propia carpeta. Si alguien conoce el ID
  exacto de otra persona, lo puede reutilizar y tambien hereda su sesion de
  pago: es una credencial de posesion, como documenta `ui._sesion_de`.
  No se encontro en estas rutas un listado que revele los IDs aleatorios.
  No se afirma que cambiar la cabecera a cualquier UUID permita entrar en
  una cuenta ajena. Preservar el ID como secreto y no ponerlo en URLs/logs.
- La sustitucion/el truncado permiten alias de un mismo ID, pero requieren
  conocer su parte saneada; no son por si solos una forma de adivinarla.
- En local, `ui._dir_lector` devuelve siempre `BASE_DATOS_LECTOR`
  (`app/ui.py:373`): los navegadores comparten datos intencionalmente.
  Las pruebas fuerzan `SPACE_ID` (`pruebas_api.py:34`); no validan aislamiento
  del arranque local, porque ese aislamiento no existe por diseno. No exponer
  ese modo como un servicio multiusuario.
- `/api/trabajos/{id}` no exige lector y el UUID del trabajo funciona como
  credencial de lectura de su avance. No se encontro enumeracion de trabajos;
  no se marca como fuga confirmada sin un mecanismo para obtener el ID.

Se cotejaron las firmas vigentes de todas las privadas llamadas mediante
`ui._nombre(...)`: `_dir_lector`, `_archivo_lector`, `_minutos_para_la_siguiente`,
`_dentro_del_limite`, `_codigo_de`, `_puede_pagar`, `_entrar`, `_salir`,
`_mensaje_limite`, `_claves_cuestionario`, `_cuerpo_para_muestra`,
`_muestra_de_libro`, `_nota_nivel`, `_abrible`, `_autor_corto`, `_esta_cacheado`,
`_descargar_gutenberg`, `_guardar_sesion`, `_cap`, `_cefr`, `_clave_libro`,
`_palabras_del_cuerpo`, `_analisis_guardado`, `_guardar_analisis`,
`_capitulos_de_cuerpo`, `_filas_del_catalogo`, `_sinopsis_guardada`, `_oraciones`,
`_sin_encabezado`, `_parece_indice`, `_empieza_entera`, `_oracion_de` y
`_humanizar`. No se encontro desajuste de aridad ni orden de argumentos en
HEAD. La dependencia semantica de reservas mutable esta en el hallazgo 2.
Esto no equivale a haber ejecutado todos sus retornos ni validado cada forma
de datos del modelo/catalogo.

## Comprobado y correcto

- Libro ID: lista de formas PG/SWV/ASB/VOA/LRD o `u` mas hash; no acepta una
  ruta de disco. Desconocidos de corpus se rechazan por `_abrible`, y lo que
  no tiene forma conocida obtiene 404 antes de abrir archivos.
- Subidas: 20 MB, tope leido antes del parseo multipart tambien sin
  Content-Length, extensiones epub/pdf/txt, nombre de destino por hash y
  carpeta del lector; formulario cerrado en finally. La defensa contra
  descompresion excesiva se delega a reader y no se reaudito aqui.
- Audio entrante: cuerpo acotado, minimo 800 bytes, frase/acento comprobados;
  extension desconocida se trata como webm. Eso no verifica el formato real:
  se delega al motor. Las rutas de audio saliente rechazan traversal textual.
- Error inesperado: JSON de 500 generico y traza solo en stderr. La prueba
  `error_inesperado_sin_traza` cubre ese manejador. No se vio una ruta que
  devuelva un traceback completo deliberadamente.
- Ausencia de clave y sesion sin permiso: las ramas de sinopsis/voz rechazan
  antes del motor; palabra mantiene su consulta local. Existen pruebas para
  esos recorridos. No se ejecutaron ni se declara que pasen actualmente.

## Limites pendientes

- `pruebas_api.py` usa `TestClient(api.app)`, no el montaje real
  `para_gradio()`. CORS, manejo de errores y cabeceras a traves del proxy del
  Space no estan verificados por esta revision. Tampoco la topologia real de
  `X-Forwarded-For`; no se afirma un bypass remoto del tope a partir de ella.
- Hay excepciones que se convierten en datos ausentes a proposito:
  `_identificar`, `_aviso_contenido`, `_sugeridos` y el extracto de inicio;
  errores al guardar nombre/sinopsis se ignoran. Estas degradaciones no
  permiten inferir que el disco o el catalogo esten sanos a partir de un 200.
- Las ramas que transmiten `str(ValueError)` necesitan pruebas de errores
  reales de las dependencias. No se confirmo en ellas una ruta o secreto
  expuesto; no se inventa tal hallazgo por poder inyectar un doble malicioso.
- Quedan sin prueba HTTP exhaustiva las puertas horarias de las tres rutas
  pagadas con cuenta habilitada, cambios concurrentes de sesion, cobro/reintegro
  de cache y sinopsis concurrentes. Los contratos privados no tienen una prueba
  automatica que obligue a mantener firma y forma de retorno entre API/Gradio.

No hay arreglos aplicados ni commit de este informe. Las propuestas deben
coordinarse con el responsable de API/Gradio antes de implementarlas.
