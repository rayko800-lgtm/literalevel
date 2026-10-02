# Auditoría y protección de Pléyade — 1 de octubre de 2026

Estado: **CORREGIDO, PUBLICADO Y VERIFICADO**, con las limitaciones y pendientes indicados abajo.

## Alcance e identificación

- Aplicación: Pléyade, proyecto LiteraLevel.
- Repositorio privado: `rayko800-lgtm/literalevel`, rama `master`.
- Base revisada: `e382c1967202ec52c02a8518e699954d012459ac`.
- Correcciones iniciales: `cac5dcf`; versión publicada final del servidor: `5128df0` (incluye correcciones del arranque y de los formatos de audio).
- Front Angular: <https://pleyade-app.vercel.app/#/escuchar>.
- API FastAPI y motor: <https://mikemaki1763-literalevel.hf.space>.
- Revisión inicial del Space: `1dca80b0b79dfca12d8fb7f6c30dfc3d755f5619`.
- Revisión final del Space: `b60a6cfe0416130d3ed8df40c1f2f169f4e54e0e`; los siete archivos acoplados coinciden con el commit publicado (`--seco`: nada que subir).
- Front publicado por Vercel: `main-D2L26KL7.js`, bytes idénticos por SHA256 a la compilación local; estados de GitHub/Vercel `success`. El front no cambió en los ajustes posteriores del servidor.
- Se obtuvo acceso efectivo al código, a GitHub y a Hugging Face. El conector de Vercel no mostró equipos accesibles; la publicación del front se verifica mediante Git y el contenido servido.

Se respetaron los archivos sucios de otras sesiones, los procesos de vídeo/Eos y el modelo v4. No se descargaron bases ni archivos de usuarios reales. No se consultaron los valores de las contraseñas existentes. Los proveedores de pago se sustituyeron por dobles en las pruebas locales.

## Datos de usuarios: dónde quedan y qué contienen

**CONFIRMADO:** `LITERALEVEL_DATOS=/data`; el bucket `MikeMaki1763/literalevel-datos` es privado. Hugging Face aloja la API y el almacenamiento; Vercel sirve el front. No hay Supabase, Firebase, Clerk ni base administrada externa en esta arquitectura. La autenticación es propia.

| Ubicación | Información conservada | Protección y límites |
|---|---|---|
| `/data/cuentas/<usuario>/perfil.json` | Nombre elegido, nivel, objetivo y fecha/origen de evaluación | La API deriva el directorio de la sesión validada; no del nombre que manda el cliente |
| Directorio de cuenta: `biblioteca.json`, `sesion.json` y libros propios | Estantería, progreso, capítulo, títulos y contenido de archivos subidos | Autorización por cuenta; otro usuario recibe 404 al pedir un libro propio ajeno |
| Directorio de cuenta: `cuaderno.db` | Palabras, oraciones, acepciones consultadas y repasos | SQLite separado por cuenta |
| Directorio de cuenta: `voz.db` | Palabras débiles, fallos, frases y métricas de ritmo/intentos | SQLite separado por cuenta |
| `/data/lectores/<X-Lector>/` | Equivalentes de visitantes sin cuenta | Identificador aleatorio del navegador como capacidad; no equivale a autenticación ni autoriza gasto |
| Caché compartida de léxico, audio, tiempos y Eos | Explicaciones, frases sintetizadas, MP3, tiempos de palabras, vídeo y cola de generación | No se sirve el disco. Audio/vídeo generado exige una capacidad aleatoria de 15 minutos; metadatos y estado exigen permiso de cuenta |
| `/data/seguridad.sqlite3` | Cuentas habilitadas, hashes de contraseña/semilla, hashes de sesiones y recuperaciones, versiones, vencimientos, usos, reservas monetarias, permisos e intentos | PBKDF2-SHA256 con sal, 600.000 iteraciones; tokens de 256 bits guardados por SHA256; transacciones atómicas |
| Secretos del Space | Claves de proveedores, token del trabajador y aprovisionamiento heredado de cuentas | Solo servidor. El secreto heredado contiene contraseñas originales; los cambios de usuario se guardan como hashes y no reescriben ese secreto |
| Navegador | Identificador de visitante y preferencias en `localStorage`; sesión en `sessionStorage` | El token solo se adjunta a la API propia; se borra al salir, cambiar clave o recibir 401 |

Las grabaciones recibidas para pronunciación se procesan en un temporal y se eliminan al terminar la petición. Las frases, resultados e historiales pueden permanecer en las bases y cachés anteriores. La caché evita volver a pagar por contenido ya generado. No se encontró una política automática de borrado por antigüedad ni un flujo completo de eliminación de cuenta. **NO VERIFICADO:** cifrado en reposo, copias de respaldo, retención de logs del alojamiento y requisitos de privacidad aplicables a menores. La conexión pública usa HTTPS.

OpenAI recibe los textos o audios necesarios cuando se activa una función de pago. Se fuerza `store=False` en generación textual; eso no demuestra retención cero del proveedor ni elimina sus registros de seguridad. No se han activado garantías contractuales de retención cero en esta tarea.

## Hallazgos y correcciones

| ID / gravedad | Evidencia del estado anterior e impacto | Corrección y verificación |
|---|---|---|
| G1 — CRÍTICA | `app/cuentas.py`: cuenta ausente, cuota 0, contador ilegible o fallo de escritura podían dejar pasar consumo. JSON/candado de proceso y ausencia de presupuesto global | Cuotas finitas, migración sin reset, SQLite `BEGIN IMMEDIATE`, reserva antes de cada llamada y bloqueo ante fallo. Pruebas de concurrencia entre hilos y cuatro procesos, cuotas agotadas, disco inválido y contador corrupto |
| A1 — ALTA | `app/ui.py` / `app/api.py`: ataduras persistentes de `X-Lector` y credenciales de sesión sin vencimiento ni revocación uniforme | Identidad de cuenta por bearer aleatorio, expiración de 8 h, versiones y revocación al salir/cambiar/recuperar/rotar/retirar cuenta; no se usan ataduras antiguas desde la API |
| G2 — ALTA | `/api/lectura/vivo` entregaba credencial de audio; `/api/gpt-live/sesion` dependía de temporizador y cierre no demostrado frente a reinicios o clientes manipulados | Ambos endpoints bloqueados con 503 antes de llamar al proveedor; interfaz desactivada. El acceso público a Gradio, su cola y ficheros se bloquea en el middleware real de producción |
| D1 — ALTA | `/api/audio/*`, vídeos/estado Eos y tiempos de audio se podían pedir por su nombre o hash | Capacidades aleatorias de 15 min, permisos por cuenta, caché privada/no-store y revocación de enlaces al salir/cambiar contraseña; Eos conserva descarga autorizada mediante su cola privada |
| D2 — MEDIA | El decodificador admitía listas `ffconcat` que leían audio de un archivo referenciado. Se reprodujo solo con dos archivos sintéticos propios: 32.000 bytes decodificados del segundo archivo. No se probó acceso a archivos reales ni entre cuentas | Lista cerrada de formatos de audio, además de protocolos restringidos. La misma lista se rechaza con 422; WAV válido y duración excesiva se comprueban en las regresiones |
| C1 — MEDIA | CORS admitía cualquier subdominio `hf.space`; faltaban defensas del front contra scripts inyectados y enmarcado | Orígenes exactos, bearer limitado al origen propio, CSP, nosniff, no-referrer, frame-deny y política de permisos. Preflight válido y origen ajeno rechazado |
| P1 — ALTA / CRÍTICA en herramienta de build | Auditoría npm: cinco problemas iniciales, incluidos router Angular y piscina. OSV: advisories en pypdf 6.17, urllib3 2.7, Pillow 12.1, setuptools 78.1 y Pygments 2.19.2 | Angular y herramientas 22.2.1, lockfile nuevo, npm audit sin vulnerabilidades. Mínimos pypdf 6.19, urllib3 2.8, Pillow 12.3, setuptools 83 y Pygments 2.20. OSV: 102 dependencias instaladas locales y 92 paquetes del log de build sin advisories conocidos |

Referencias de implementación: `app/seguridad.py` (transacciones, sesiones, recuperación, recursos y proveedor); `app/api.py` (`ProteccionHTTP`, `_Lector`, rutas de cuenta/Eos y `para_gradio()`); `front/src/app/nucleo/lector.ts`; `front/vercel.json`.

No se encontró una inyección SQL explotable en las consultas revisadas: se usan parámetros. No se encontraron usos de `innerHTML`, `bypassSecurityTrust*` o `eval` en el front revisado; el texto se interpola mediante Angular. Los nombres/rutas de archivos están restringidos y EPUB limita la descompresión a 100 MiB. El audio se decodifica localmente con protocolos de red y formatos restringidos y se envía normalizado; no se confía en duración declarada. Se restringieron cuerpos JSON antes de Pydantic. No se identificó un endpoint que acepte una URL arbitraria para pedir archivos internos; las descargas de catálogo usan fuentes y rutas controladas. D2 documenta la excepción encontrada dentro de un archivo multimedia. Estos resultados son revisión y pruebas específicas, no una demostración de ausencia universal de XSS, SSRF o denegación de servicio.

Gradio responde al preflight válido con HTTP 200 y cabeceras en minúsculas; la API local devolvía 204. La prueba de producción se corrigió para comprobar el comportamiento real del navegador. El middleware de seguridad rechaza con 403 las peticiones efectivas de origen ajeno, aunque Gradio procese el preflight en una capa exterior.

## Límites efectivos de consumo

| Control | Valor publicado | Funcionamiento |
|---|---|---|
| Presupuesto global diario | 500 centavos USD ($5), día UTC | Suma reservas persistentes; se rechaza antes de superar el techo |
| Presupuesto global acumulado | 2.000 centavos USD ($20), desde la activación de este control | No se reinicia cada mes ni al reiniciar el proceso; solo una decisión del operador puede ampliarlo. No reconstruye facturas históricas del proveedor |
| Reserva por llamada de texto | $0,25 | Solo gpt-5 / gpt-4o-mini; entradas combinadas ≤32 KiB UTF-8, salida ≤2.048 tokens; sin herramientas, stream, background ni tier prioritario |
| Reserva TTS | $0,10 | Solo tts-1, ≤4.000 caracteres por llamada |
| Reserva transcripción | $0,05 | Solo whisper-1, ≤180 s reales, archivo ≤12 MiB, normalizado a WAV |
| Cuota de acciones por cuenta | El tope asignado, máximo 100; antiguo 0 →100 | Contador atómico por usuario; no se evade cambiando `X-Lector` |
| Llamadas al proveedor por cuenta | 6/min; 30/h; 40/día UTC; 200 acumuladas | Cuenta cada llamada real, incluidas varias llamadas dentro de una misma acción |
| Concurrencia | 1 operación de pago por cuenta; 2 globales | Reserva transaccional con lease de 30 min; se libera al terminar |
| Tiempo SDK | 60 s; cero reintentos automáticos | Cada nueva llamada requiere su propia reserva; los fallos y el silencio no devuelven la reserva monetaria |
| JSON / subida de libros | 128 KiB / 20 MiB | Cuerpo real acotado; EPUB ≤100 MiB descomprimido |
| Login | 15 intentos/IP/h, 20/usuario/h, 100 globales/h | Persistente; también cuenta aciertos y no se evade cambiando visitante |
| Contraseña / recuperación / Eos | 5 intentos/h por cuenta en cada acción de clave; Eos 6/h | Límites de la instancia adicionales a los límites persistentes de gasto |

Las reservas son máximos conservadores, no una lectura de la factura de OpenAI. Pueden bloquear antes de gastar el saldo nominal. Una alerta de gasto del proveedor no se utiliza como autorización para continuar. El presupuesto cubre llamadas realizadas por estos caminos de Pléyade, no otras aplicaciones que compartan la misma clave, cambios futuros de tarifas ni la factura de alojamiento. Revalidar tarifas antes de cambiar modelos o ampliar límites.

**Límite arquitectónico:** SQLite coordina procesos que comparten el mismo sistema de archivos; no autoriza réplicas con discos independientes. No borrar, restaurar a una copia vieja o mover `seguridad.sqlite3` para recargar cuotas. Una eliminación deliberada de ese archivo por un operador reiniciaría el registro: requiere el mismo cuidado que modificar el presupuesto.

## Cuentas y recuperación

- Registro público: **NO EXISTE**. Las cuentas las habilita el operador; las funciones gratuitas siguen accesibles a visitantes.
- Inicio/salida, cambio de contraseña, aislamiento, recuperación y roles: **CONFIRMADOS en producción** con dos cuentas sintéticas; evidencia de 40 comprobaciones iniciales en `seguridad_produccion_2026-10-01.json`.
- Sesión: 8 horas; expiración y revocación verificables en servidor, no solo interfaz.
- Recuperación: código aleatorio de un solo uso, 15 minutos, nueva emisión invalida la anterior. Solo un administrador explícito, reautenticado con su contraseña actual, puede emitirlo; la persona lo introduce en Ajustes. No se envían correos ni enlaces a terceros.
- Contraseña nueva: 12–200 caracteres. Cambio y recuperación invalidan todas las sesiones previas.
- El rol se configura con `LITERALEVEL_ADMIN_USUARIOS`; si está ausente, no hay administradores web. **PENDIENTE:** el usuario exacto que recibirá este rol no se ha indicado. Se restauró la configuración original sin administradores web, en lugar de asignar privilegios a una cuenta supuesta. La recuperación administrada para usuarios reales requiere habilitar ese rol o intervención del operador en el servidor/aprovisionamiento.
- Las dos cuentas sintéticas se habilitaron mediante un secreto separado, retirado al terminar. Se comprobó que una sesión de una cuenta retirada recibe 401. Se borró el archivo local con credenciales sintéticas. Pueden quedar metadatos y perfiles sintéticos en el bucket; no se borraron registros de seguridad ni datos reales.
- **CONFIRMADO tras un reinicio real del Space:** sesión vigente, cuota de 40 usos, contraseña cambiada y perfil siguen presentes. Esto verifica persistencia operativa de la base y los datos; el estrés de cuota y presupuesto se realizó localmente con dobles, no con llamadas facturadas en producción.

## Verificación y límites de la evidencia

Front: **505/505** pruebas en 60 archivos y compilación de producción, también en copia limpia del commit. API: **71/71** en copia limpia. Seguridad: **38/38** en la suite final de la copia limpia, incluido arranque de Gradio, permisos de metadatos/audio, cuatro procesos compitiendo por cuota y listas multimedia rechazadas. `npm audit`: 0 vulnerabilidades. Las pruebas de medios de JSDOM no prueban reproducción real ni micrófono.

Producción: **53 comprobaciones correctas**, sin fallos en el registro final `seguridad_produccion_2026-10-01.json`: 40 de cuentas/seguridad, 3 de persistencia tras reinicio, 1 de retirada de cuenta y 9 del despliegue final. Los intentos anteriores mientras el Space arrancaba y la expectativa incorrecta de preflight se describen arriba; el registro final contiene la ejecución satisfactoria.

La copia limpia inicial omitió `avisos_contenido.csv`; se añadió desde el mismo commit. Una medición de latencia falló mientras compilaban las pruebas del front y pasó en la ejecución secuencial. La prueba del índice de Gutenberg dependía de una descarga cuyo prólogo había cambiado; se reemplazó por una muestra reproducible que conserva la marca de inicio y el índice. No se cambió el lector por esa diferencia externa.

El primer despliegue falló porque el bloqueo también rechazaba las comprobaciones internas de Gradio (`startup-events` y `HEAD /`). Se corrigió y se añadió una prueba con un servidor Gradio real, después repetida en árbol limpio. La raíz GET/HEAD y la comprobación de arranque devuelven JSON inocuo; no ejecutan eventos de usuario ni abren la cola. La interfaz/configuración/archivos de Gradio permanecen cerrados. El arranque final y la salud JSON se comprobaron en producción.

Interfaz publicada: Escuchar muestra la lectura y exige entrar para generar audio; Pronunciar permite navegar y deshabilita grabación sin cuenta; Ajustes muestra recuperación con código. Comprobación por árbol de accesibilidad y DOM en viewport móvil 390×844, sin desbordamiento horizontal (375 px de contenido útil). **NO VERIFICADO visualmente:** el navegador no pudo producir capturas; no se sustituye revisión humana de audio/animación por esos checks. El navegador no mostró errores de consola en estas pantallas.

Dependencias: `seguridad_dependencias_2026-10-01.json` registra las 102 versiones locales; `seguridad_dependencias_space_2026-10-01.json` registra los 92 paquetes enumerados por pip en el build. El build confirma pypdf 6.19, Pillow 12.3, setuptools 83, FastAPI 0.142.2, Starlette 1.7 y OpenAI 3.23. No se obtuvo un SBOM completo de los paquetes intactos de la imagen base. No se deben presentar 0 advisories conocidos como garantía de ausencia de vulnerabilidades.

No se realizaron llamadas de audio de pago para esta auditoría. Por tanto, calidad del audio, facturación real y latencia del proveedor quedaron sin comprobar. La caducidad temporal se fuerza en las pruebas locales; no se esperaron 8 horas ni 15 minutos de reloj real en producción. La retención, eliminación de cuenta, protección frente a abuso masivo de visitantes y copias de respaldo requieren trabajo adicional.

## Recomendación

**Apta para compartir como beta pública limitada para recibir feedback**, manteniendo Conversar, lectura en vivo y la interfaz pública de Gradio desactivadas. El gasto nuevo de estos caminos está sujeto a reservas y techos efectivos; las funciones gratuitas siguen disponibles. Las cuentas de pago se distribuyen de forma administrada, sin registro público.

Antes de abrirla a uso amplio: indicar el usuario administrador de recuperación; definir aviso de privacidad, retención y eliminación de cuenta; documentar respaldos y recuperación del registro de gasto; reforzar controles contra abuso masivo de servicios gratuitos y revisar la protección de datos de visitantes sin cuenta. No habilitar réplicas independientes ni Realtime sin un mecanismo distribuido y comprobado de límite de gasto. No se certifica ausencia de vulnerabilidades ni cumplimiento legal.

## Fuentes primarias

- [OWASP: consumo no restringido de recursos](https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption/).
- [OWASP: autenticación](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).
- [OpenAI: precios](https://developers.openai.com/api/docs/pricing).
- [Hugging Face: acceso y montaje de buckets](https://huggingface.co/docs/hub/storage-buckets-access).
- [pypdf: GHSA-5jq2-8x83-x246](https://github.com/advisories/GHSA-5jq2-8x83-x246).
- [urllib3: GHSA-8988-9cw3-xx77](https://github.com/advisories/GHSA-8988-9cw3-xx77).
- [Pillow: GHSA-45hq-cxwh-f6vc](https://github.com/advisories/GHSA-45hq-cxwh-f6vc).
- [setuptools: path traversal](https://github.com/advisories/GHSA-5rjg-fvgr-3xxf) y [exclusiones de distribuciones](https://github.com/advisories/GHSA-h35f-9h28-mq5c).
- [Pygments: ReDoS](https://github.com/advisories/GHSA-5239-wwwm-4pmq).
