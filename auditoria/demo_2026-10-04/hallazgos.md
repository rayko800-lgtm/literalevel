# Demo grabada de Miguel («para fable.mp4») · revisión del 4 oct 2026

Sesión local en el PC de Miguel (rama `claude/hola-vpznit`), encargo
`docs/ai/ENCARGO_LOCAL_2026-10-04.md`, parte 1.

## El archivo

| | |
|---|---|
| Ruta en el PC | `D:/pleyade_ettin_local/checkpoints/20261003T022117Z_a8fff0_foco/para fable.mp4` (no estaba en `C:\Users\laura\Downloads`) |
| Tamaño | 823.558.116 bytes |
| Duración | 19:09,87 |
| Vídeo | h264 1080×2340 (móvil en vertical), 64 fps variables |
| Audio | AAC estéreo 48 kHz |
| Grabado | móvil de Miguel, reloj del teléfono 7:30 → 7:46, cuenta `miguel` (98 usos), `pleyade-app.vercel.app` |

Método: fotograma cada 2 s (`ffmpeg -vf fps=1/2`, 575 fotogramas) en hojas de
10 y recorrido entero; transcripción con faster-whisper turbo en GPU
(`transcripcion.md`). Los minutos de abajo son del vídeo (mm:ss), con una
precisión de ±2 s.

## El audio: no hay narración

**Miguel no habla sobre el vídeo.** El audio es el del teléfono: silencio
casi todo el rato (tramos > 1,5 s por debajo de −35 dB cubren más del 90 %
de los 19 minutos) y, cuando suena algo, es la app o Miguel leyendo las dos
frases al micrófono de Pronunciar. Lo que whisper transcribe (todo en inglés):

| Minuto | Qué suena |
|---|---|
| 4:08 | «Staircase» (los botones US/UK de la ficha: voz del navegador, «Sin grabación para esta palabra») |
| 5:20 | Miguel lee «He had successfully avoided meeting his landlady on the staircase» al micrófono |
| 6:22–7:33 | «Meeting» × 9 («Escuchar y ver» del corte 2D y la boca 3D) |
| 7:33–8:36 | La frase bien leída, el 3D leyéndola y Eos |
| 11:45–13:58 | Miguel lee «His garret was under the roof of a high, five-storied house…» y la app la repite |
| 15:33–17:24 | «Five-storied» y la frase otra vez (segunda grabación, 3D y Eos) |

Una pasada sin VAD del primer tramo (0:00–4:00) solo devuelve las
alucinaciones típicas de whisper sobre silencio («Thank you»). La columna
«qué dice Miguel» del encargo queda, por tanto, vacía: lo que sigue sale de
lo que se ve.

## Recorrido y hallazgos

Cada hallazgo lleva: minuto, pantalla, qué se ve, cruce con la tabla de
arreglos de la nube (commits de la rama) y estado tras esta sesión.

### H1 · 0:24–0:58 y 5:12 · Ficha de palabra con sesión: la explicación no llega (403)

Pantalla: Leer → Crime and Punishment, cap. 2 → pulsación larga en
«staircase». Se ve la ficha («staircase · noun · poco frecuente», IPA US/UK,
«EN EL DICCIONARIO: A connected set of flights of stairs; a stairwell», aviso
de afinidad 0,33) y debajo dos cajas grises:

- «no se pudo generar audio: HTTPException» (`app/lexicon.py:1178`,
  el tts de respaldo por palabra);
- «OpenAI no disponible: HTTPException: 403: Hace falta una sesión
  autenticada para generar contenido de pago.» (`app/seguridad.py:460`).

Miguel **está dentro** (cabecera «miguel», Ajustes dice «Has entrado como
miguel. Te quedan 98 usos»). A las 5:00 sale y vuelve a entrar («Has entrado.
Tu sesión caduca en ocho…») y a las 5:12 la misma ficha da los mismos dos
mensajes; a las 12:10 («storied») y 15:40 («five-storied») también.

Cruce: **lo cubre `54c39ba`** y la causa coincide con lo que se ve: el 403 es
el de `ClienteProtegido` cuando `seguridad.CONTEXTO` (ContextVar) no llega al
hilo del `ThreadPoolExecutor` de `lexicon.consultar` / `voz.audios_de_palabras`;
por eso fallan a la vez la explicación y el audio por palabra. Lo refuerza el
contraste con 14:54: la ficha del libro subido («¿De qué trata?», «Resumen
escrito por un modelo de lenguaje») **sí** llegó, y esa ruta no pasa por un
hilo. El cupo no era el problema (98 usos). Estado: arreglado en la rama; en
este PC `pruebas_seguridad.py` 43/43 y `pruebas_api.py` (ver abajo); no
probado con OpenAI real para no gastar.

### H2 · 1:00–1:18 · Cambiar la contraseña echa de la sesión

Pantalla: Ajustes → «Contraseña actual» / «Nueva contraseña (mínimo 12
caracteres)» → Google propone una contraseña → «Cambiar contraseña» → aviso
rojo «Contraseña cambiada. Vuelve a entrar en tus dispositivos.» (texto de
`app/api.py:927` en `master`) y el bloque «Tu perfil» pasa al formulario de
Usuario/Contraseña: la sesión del propio móvil se ha cerrado. Miguel vuelve a
entrar a las 5:00.

Cruce: **lo cubre `22fce02`** (`POST /api/cuenta/clave` devuelve `token` y
`expira_en`; el mensaje nuevo es «Contraseña cambiada. En tus otros
dispositivos tendrás que volver a entrar.» y el formulario va plegado). Estado:
arreglado en la rama; probado en local (ver «Prueba en real»).

### H3 · 6:26–6:40, 8:26, 13:26, 16:54 · La cabeza 3D sale blanca

Pantalla: Pronunciar → corrección de «meeting» → «Boca en 3D» → «Cargando
modelo…» → la cara aparece **sin textura**: blanca, de arcilla, con la
etiqueta «Vibración · sonora». Igual en «Verla leída en 3D» (8:28, 13:26,
16:54) y en «Lado · interior» (6:48: el corte sagital sí tiene sus colores,
la piel de fuera no).

Cruce: **lo cubre `8a225a3`** (`connect-src blob:` en la CSP de
`front/vercel.json`: three.js baja la textura WebP embebida del GLB con
`fetch` sobre un `blob:` y la CSP lo bloqueaba). Estado: arreglado en la rama;
reproducido y verificado en local sirviendo el `dist` con la CSP vieja y la
nueva (ver «Prueba en real»).

### H4 · 7:30–7:56 · Velocidad del 3D y sincronía

Pantalla: barra «Velocidad» del 3D (0,25× · Normal · 2×) a 0,48×, luego
1,11× y 1,00×. En fotogramas fijos no se puede medir el desfase boca/audio;
la línea de aire del corte interior se dibuja (7:04–7:16) y la boca se mueve.

Cruce: `2319d37`, `63d23f9`, `e1971ae` (audio desde `blob:`, línea anclada al
`playing` real, cadencia del sombreado). El vídeo ni confirma ni contradice:
no hay audio de referencia sincronizable con 2 fps. Estado: pendiente de la
prueba con oído en el móvil (Miguel), como ya decía el HANDOFF.

### H5 · 7:40–7:58 · Eos no cierra los labios en la /m/

Pantalla: «Ver a Eos» → «Eos · el sonido /m/ y sus ejemplos» a 0,48×. En los
fotogramas 7:42–7:50 Eos tiene los labios separados durante la /m/ sostenida.
A 16:26 («Eos · el sonido /d/») la lengua se ve entre los dientes.

Cruce: **lo cubre `27e2595`** (corrector de visemas) **más la regrabación de
esta sesión** (parte 2 del encargo). Estado: 85 clips regrabados; medidas y
fotogramas en «Parte 2» del HANDOFF y en esta carpeta.

### H6 · 8:42–11:38 y 13:42–14:12 · «Eos está preparando la frase. Suele tardar un minuto» tarda tres

Pantalla: «Ver a Eos leerla» → aviso con rueda «Eos está preparando la
frase. Suele tardar un minuto.» (`front/src/app/pantallas/pronunciar.html`).
La primera frase se pide a las 8:42 y el vídeo («Eos · la frase leída») aparece
a las 11:38: **2 min 56 s**. El front se rendía a los 45 sondeos de 4 s (3 min,
«tarda demasiado»): quedó al borde. La segunda frase se pide a las 13:42,
Miguel espera hasta 14:12, se va a Encontrar y al volver a Pronunciar (15:00)
no queda ni la frase ni el aviso (H7). Cuando la vuelve a pedir (17:08) llega
al instante: el PC ya la había hecho entre tanto
(`D:/literalevel_eos_pronunciar/trabajador.log`: 100–190 s por frase, más los
15 s del sondeo del trabajador y la subida).

Cruce: **no lo cubría ningún arreglo.** Corregido en esta sesión:
`ESPERAS_EOS_MAX = 90` (seis minutos) en `pronunciar.estado.ts` y el texto pasa
a «Suele tardar entre uno y tres minutos.»; prueba nueva en
`pronunciar.estado.spec.ts`.

### H7 · 15:00 · Pronunciar pierde la frase, la corrección y la espera de Eos al cambiar de pestaña

Pantalla: tras pasar por Encontrar, subir un libro y Mi espacio, Pronunciar
está vacío («Escribe o pega la frase en inglés que vas a leer», «Primero
escribe la frase»). La corrección de «His garret…» (12:48) y la espera de Eos
(13:42) han desaparecido.

Cruce: **lo cubre `1a994b6`** (servicio raíz `pronunciar.estado.ts`, franja
«Eos ya tiene lista tu frase»). Estado: arreglado en la rama; probado en local.

### H8 · 15:28–15:42 y 17:46 · «five-storied» sale como «five · muy común»

Pantalla: pulsación larga sobre «five-storied» (la palabra entera; a las 12:04
la selección había cogido solo «storied», que sí está en el diccionario y sale
bien: «adj · rara · Having multiple storeys; multistoried»). La ficha dice
«five-storied · five · muy común», aviso «La entrada del diccionario es de
«five», una parte de «five-storied»», acepciones «A numerical value equal to
5…», «The digit/figure 5», «Tu frase no deja claro cuál de estas es, y esta vez
no hay explicación de contexto», y «De esta palabra no hay pronunciación: ni
el diccionario la trae ni se pudo generar». En Mis palabras (17:46, 18:00) la
consulta queda como «five-storied · muy común · A person who is five years
old.».

Causa: spaCy parte el compuesto y `lexicon.consultar` tomaba como ancla la
primera pieza («five»); la rareza se calculaba sobre esa pieza (zipf 5,45).
Con OpenAI funcionando (H1) la explicación habría tapado la acepción, pero la
rareza y la pieza seguirían mal.

Cruce: **no lo cubría ningún arreglo.** Corregido en esta sesión
(`app/lexicon.py`): si el diccionario no trae el compuesto, la parte que se
enseña es su **cabeza** (la última pieza: «storied», «chant» de «war-chant»)
con su categoría, y la rareza es la del compuesto entero (`wordfreq`:
«five-storied» 2,99 → «rara»). Prueba nueva en `pruebas_api.py`
(`compuesto_sin_entrada_usa_su_cabeza_y_su_rareza`): devuelve «storied (adj,
rara) · Having multiple storeys; multistoried». Ojo: la consulta de Miguel ya
está guardada así en su cuaderno; la caché de respuestas de OpenAI no guarda
esta parte, así que la próxima consulta saldrá bien sin tocar nada.

### H9 · 18:44–18:46 · «Leer en voz alta (en vivo)» lleva a «No se pudo»

Pantalla: Leer → botón «Leer en voz alta (en vivo)» encima del capítulo →
hoja «Lectura en voz alta · No se pudo · La lectura en vivo está
temporalmente desactivada. Puedes grabar una frase en Pronunciar.»
(`lectura-vivo.ts`, cerrada por la auditoría de seguridad `cac5dcf`). El botón
seguía porque `lecturaVivoDisponible` solo miraba cuenta, OpenAI y WebRTC.

Cruce: **no lo cubría ningún arreglo.** Corregido en esta sesión:
`LECTURA_VIVO_CERRADA` (exportada desde `lectura-vivo.ts`) y el lector no
enseña el botón mientras sea `true`; prueba nueva `lector.vivo.spec.ts`.

### H10 · 14:28–14:54 · Subir un libro funciona

Pantalla: Encontrar → «Subir un libro» → selector de Android → «Subiendo…» →
ficha «Notes from a Dead House · Fyodor Dostoevsky · C1 · 1,74 de 2 · 30
capítulos · 129.589 palabras · 12 h · Empieza en el capítulo 6», curva por
capítulos, «¿De qué trata?» con resumen generado. Sin anomalía; se anota
porque demuestra que OpenAI sí respondía fuera de los hilos (H1).

### Lo que no se ve en el vídeo

- El desfase boca/audio del 3D (H4): hace falta oído.
- La franja «Eos ya tiene lista tu frase» y la sesión conservada al cambiar la
  contraseña: son arreglos posteriores al vídeo; probados en local.
- Ningún mensaje «Te quedan 0 usos»: la cuenta tenía 98.

## Estado del Space durante esta sesión

Al empezar (06:08) el Space `mikemaki1763/literalevel` estaba **PAUSED**
(`/api/salud` → 503 «The space is paused, ask a maintainer to restart it»;
`space_info` → `stage: PAUSED`). El trabajador de Eos del PC lleva desde
después de la última frase del 3 oct (19:42, hora del PC) recibiendo 503
(1.051 líneas en `trabajador.log`). Nadie de esta sesión lo ha tocado: lo
reanuda Miguel cuando decida publicar (parte 3).

## Prueba en real (Chrome del PC, 390×844 táctil, Playwright con GPU)

Montaje: `npm start` (4200, proxy a la API), API local `uvicorn app.api:app`
en el 8000 con `LITERALEVEL_DATOS` en un temporal, cuenta de prueba
`prueba` (tope 100) y una `OPENAI_API_KEY` inválida a propósito (sin gasto;
la explicación falla con «OpenAI ha rechazado la clave de este servidor», no
con el 403 del vídeo). Para la CSP, el `dist` de `npm run build` servido con
las cabeceras de `front/vercel.json` (8081) y con la CSP anterior sin `blob:`
en `connect-src` (8082). Guion: `probar_front.py` (scratch de la sesión);
capturas y JSON en `real/`.

| Qué | Resultado | Prueba |
|---|---|---|
| H2 cambiar la contraseña | «Contraseña cambiada. En tus otros dispositivos tendrás que volver a entrar.»; la cabecera sigue con `prueba`, no aparece el formulario de entrada y tras recargar sigue dentro | `real/clave_cambiada_sigue_dentro.jpg`, `tras_recargar_sigue_dentro.jpg` |
| H1 ficha con sesión | Con sesión, «Sunday»: diccionario, IPA, cita; **ningún** «Hace falta una sesión autenticada» ni «no se pudo generar audio: HTTPException». Solo el aviso de clave rechazada (clave inválida a propósito) | `real/ficha_con_sesion_sin_403.jpg` |
| H9 botón de lectura en vivo | 0 botones «Leer en voz alta (en vivo)» con cuenta dentro, OpenAI y WebRTC | `real/lector_sin_boton_en_vivo.jpg` |
| H3 cabeza 3D | CSP de `vercel.json`: textura de piel (centro del lienzo RGB 158·106·94, saturación 0,40), sin avisos de CSP. CSP vieja: gris (212·210·209, saturación 0,02) y en consola «Refused to connect because it violates the document's Content Security Policy» + «THREE.GLTFLoader: Couldn't load texture blob:…» | `real/boca3d_csp_nueva_con_textura.jpg`, `boca3d_csp_vieja_sin_textura.jpg` |
| Scroll 2D/3D | Con el corte 2D arriba y el 3D abierto más abajo, «Escuchar y ver» no mueve la página (scrollY 2427 antes y después) | `real/escuchar_y_ver_no_baja_al_3d.jpg` |
| H7 estado de Pronunciar | Cubierto por `pronunciar.estado.spec.ts` (suite del front 533/533 en este PC) | — |

No probado aquí: la sincronía boca/audio con oído (hace falta el móvil y
escuchar), el aviso «Eos ya tiene lista tu frase» con un PC generando de
verdad (el Space está en pausa) y nada con OpenAI real.

## Parte 2 · Eos regrabado

- `corregir_visemas.py --informe` midió 89 clips (85 sonidos + 4 frases del
  trabajador); todos con fonemas y **sin curvas de lengua** (la lengua la pone
  el visor con los canales `lengua` del json). Luego sin `--informe`: 89
  `curvas.sin_corregir.json` guardados.
- `grabar_clips.py --rehacer` (con la corrección de esta sesión para dejar
  fuera las frases): 85 clips en 56 min, todos decodifican con ffmpeg,
  `clips.json` con 85 entradas y ninguna frase. Commit `04e3c5f`.
- `/m/` (`ga/006d`): en los tres sonidos sostenidos los labios quedan juntos
  todo el tramo (`eos_ga_006d.jpg`; antes, `antes/eos_ga_006d.jpg`, nunca se
  tocaban). `/p/` (`ga/0070`): cierre justo antes de cada explosión
  (`eos_ga_0070.jpg`). `mouthClose` en la /m/: máximo 0,39 → 0,70 y 138
  fotogramas por encima de 0,5 (antes 0).
- `/l/` (`ga/006c`): igual que antes fotograma a fotograma: la punta se ve
  arriba, detrás de los dientes, sin irse de lado ni asomar. Si a Miguel le
  sigue pareciendo que sale, el sitio es el mapeo de la lengua en
  `D:/literalevel_eos_pronunciar/visor/index.html` (función `lengua`, líneas
  365-437: avance de Tongue1 y tope de los incisivos), no las curvas.

## Archivos de esta carpeta

- `transcripcion.md`: lo que whisper oyó, con marcas.
- `hallazgos.md`: este informe.
- `eos_*.jpg`: mosaicos (fps=10, 2,4 s) de los clips regrabados; `antes/`, los mismos clips antes de regrabar; `real/`, capturas y resultados de la prueba en navegador (parte 1.5).
