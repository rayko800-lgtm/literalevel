# LiteraLevel — AI Handoff

Estado operativo, corto y vigente. La historia está en
`docs/ai/legacy_architecture/` (los dos HANDOFF anteriores completos, del
árbol y de la rama de desarrollo, hasta el 24-25 sep) y en `git log`.

## Sesión local en el PC de Miguel · 4 oct 2026 (rama `claude/hola-vpznit`, encargo `docs/ai/ENCARGO_LOCAL_2026-10-04.md`)

Hecho en el PC lo que la nube no podía: el vídeo, la regrabación de Eos y la
prueba en navegador. **Nada publicado todavía** (parte 3, solo con el visto
bueno de Miguel). Informe completo: `auditoria/demo_2026-10-04/hallazgos.md`
(y `transcripcion.md`, mosaicos de Eos, capturas en `real/`).

**Parte 1 · el vídeo.** `para fable.mp4` estaba en
`D:/pleyade_ettin_local/checkpoints/20261003T022117Z_a8fff0_foco/`, no en
Descargas: 19:10, 1080×2340, 823 MB. **No hay narración**: el audio es el del
teléfono (silencio, la app y Miguel leyendo las dos frases al micrófono);
whisper solo transcribe inglés de la app. Diez hallazgos (H1-H10) con minuto,
cruzados con la tabla de arreglos de la nube:

| Hallazgo | Cubierto por | Estado |
|---|---|---|
| H1 ficha con sesión: «403: Hace falta una sesión autenticada» + «no se pudo generar audio» (98 usos; la sinopsis del libro subido sí llegó) | `54c39ba` (ContextVar en los hilos) | confirmado: la causa coincide; probado en local sin 403 |
| H2 cambiar la contraseña echa de la sesión («Vuelve a entrar en tus dispositivos») | `22fce02` | probado en local: sigue dentro, también tras recargar |
| H3 cabeza 3D blanca (también en «Lado · interior») | `8a225a3` (`connect-src blob:`) | **reproducido y verificado** sirviendo el `dist` con la CSP vieja (gris, «Refused to connect… blob:») y la nueva (piel) |
| H4 velocidad/sincronía del 3D | `2319d37` `63d23f9` `e1971ae` | el vídeo no lo decide (2 fps, sin audio útil); falta oído en el móvil |
| H5 Eos no cierra labios en /m/, lengua entre dientes en /d/ | `27e2595` + regrabación (parte 2) | hecho, ver abajo |
| H6 «Suele tardar un minuto» y tardó 2 min 56 s; el front se rendía a los 3 min | **nuevo** `b18ef2a` | `ESPERAS_EOS_MAX = 90` (6 min), texto «entre uno y tres minutos», prueba |
| H7 Pronunciar pierde frase/corrección/espera al cambiar de pestaña | `1a994b6` | cubierto por su spec |
| H8 «five-storied» → ficha de «five», «muy común», en Mis palabras «A person who is five years old» | **nuevo** `5422de9` | la parte es la cabeza del compuesto («storied», adj, «Having multiple storeys») y la rareza la del compuesto (rara); prueba en `pruebas_api.py` |
| H9 «Leer en voz alta (en vivo)» → «No se pudo» | **nuevo** `49d24b4` | `LECTURA_VIVO_CERRADA`: el botón no se enseña; spec `lector.vivo.spec.ts` |
| H10 subir un libro: bien | — | — |

Verificación en este PC: `pruebas_api.py` 72/72 (ya con `kaikki`),
`pruebas_seguridad.py` 43 comprobaciones bien (dos acaban con error solo en el
`tearDown` en Windows: `cuaderno.db` aún abierto al borrar el temporal; en Linux no pasa), `pruebas_eos_visemas.py` 9/9, front 533/533,
`tsc` y `npm run build` en verde. Prueba en real (Chrome 390×844 con GPU por
Playwright, API local con cuenta de prueba y clave de OpenAI inválida a
propósito): tabla en `hallazgos.md` § «Prueba en real». **No probado**: la
sincronía con oído, el móvil real, OpenAI real.

**Parte 2 · Eos.** `corregir_visemas.py` sobre los 89 `curvas.json` (85 +
4 frases; todos «sin curvas de lengua: la pone el visor»), 85 clips
regrabados en 56 min (`04e3c5f`); `grabar_clips.py --rehacer` ahora deja fuera
las `frase_*` del trabajador, que antes se colaban en `clips.json` (`8be1276`).
`/m/` y `/p/` cierran (mosaicos `eos_ga_006d.jpg`, `eos_ga_0070.jpg`, con
`antes/` al lado); `/l/` no cambia: la lengua la pone el visor
(`D:/literalevel_eos_pronunciar/visor/index.html`, función `lengua`, l. 365-437)
y de frente se ve arriba y dentro, sin irse de lado. El trabajador de frases se
relanzó con el código nuevo (registro en
`D:/literalevel_eos_pronunciar/trabajador_2026-10-04.log`).

**Parte 3 · publicar: pendiente del visto bueno de Miguel.** Además, el Space
`mikemaki1763/literalevel` está **PAUSED** desde el 2 oct (02:40 UTC):
`/api/salud` → 503 «The space is paused»; el trabajador lleva desde el 3 oct
recibiendo 503. Antes de publicar hay que reanudarlo (Settings del Space) y,
tras `desplegar_app.py --solo …`, reponer el cupo de `miguel` si hace falta
(`HANDOFF_SEGURIDAD_2026-10-01.md`, nota del 4 oct). Pasos en el encargo § 3.

**Para la demo en vivo del 10 oct**: ensayar con la cuenta `miguel` (en el
vídeo tenía 98 usos y nivel 1,88 · C2: decidir si se deja así o se baja el
nivel para que la franja de Encontrar enseñe libros más accesibles); Space
despierto y trabajador del PC encendido (las frases de Eos tardan 2-3 min);
probar la sincronía 1×/0,5×/2× y «Lado · interior» con oído; la caché de
respuestas no guarda la ficha de «five-storied»: la próxima consulta sale bien
sin tocar nada, pero la entrada vieja sigue en Mis palabras de `miguel`.

## Auditoría de la demo grabada (4 oct 2026, sesión literalevel-5e, rama `claude/hola-vpznit`)

Miguel grabó en el móvil un recorrido de la demo tras la auditoría de seguridad
de Codex (1 oct) y pidió corregir lo que vio. **El vídeo («para fable.mp4»,
823 MB, Drive `1qEOtbC9uDqK5XP9dDxyQhJfijKpKBOxJ`) NO se pudo bajar**: la red
del entorno de Claude en la nube deniega `drive.google.com` y
`drive.usercontent.google.com`; GitHub sí pasa (verificado: un adjunto de
release se baja con `gh api -H "Accept: application/octet-stream"
repos/rayko800-lgtm/literalevel/releases/assets/<id>`). Pendiente: que Miguel
suba el mp4 como adjunto de una release (`demo-2026-10-04`) o abra la red
(«Network access» → Full) y una sesión lo revise, vídeo y audio. Todo lo de
abajo se hizo a partir de su descripción y del código; **nada está publicado**
(ni en Vercel ni en el Space) ni probado en un móvil real.

Corregido en la rama (tres agentes en worktrees + la sesión principal; suite del
front, `pruebas_seguridad.py` y `pruebas_eos_visemas.py` en verde; `pruebas_api.py`
64/71, los 7 fallos son del entorno sin `kaikki_diccionario.db` ni red, igual
que antes de los cambios):

1. **Cabeza 3D en blanco** (`8a225a3`): la CSP de `front/vercel.json` no
   permitía `connect-src blob:`; three.js carga la textura WebP embebida de
   `boca3d/didactica/cara.glb` con `fetch` sobre un `blob:` (ImageBitmapLoader)
   y el navegador lo bloqueaba → material sin textura. Añadido `blob:`.
2. **«Escuchar y ver» no baja al 3D si el usuario subió al 2D** (`fa8d808`):
   `colocarALaVista` elige el bloque más visible (3D solo si gana
   estrictamente; empate → 2D); al abrir el 3D sigue bajando a él.
3. **Pronunciar conserva su estado al cambiar de pestaña** (`1a994b6`):
   servicio raíz `pantallas/pronunciar.estado.ts` (frase, grabación, corrección,
   Eos y su sondeo, IPA); franja verde en la cabecera «Eos ya tiene lista tu
   frase» con enlace cuando el vídeo llega estando en otra pestaña.
4. **Cambiar la contraseña ya no echa al usuario** (`22fce02`): `POST
   /api/cuenta/clave` devuelve la entrada con `token` y `expira_en` (sesión
   nueva; las demás se revocan); el formulario va plegado en Ajustes.
5. **La explicación de OpenAI no llegaba con sesión** (`54c39ba`): causa real,
   `seguridad.CONTEXTO` (ContextVar) no llegaba a los hilos del
   `ThreadPoolExecutor` de `lexicon.consultar` y `voz.audios_de_palabras`, y
   `ClienteProtegido` negaba con 403 (también el tts por palabra fallada).
   Arreglado con `contextvars.copy_context().run`. Además los topes de llamadas
   por cuenta de `seguridad.reservar` (antes 6/min, 30/h, 40/día, 200 en total)
   son configurables: `LITERALEVEL_LLAMADAS_MINUTO` (20), `_HORA` (120), `_DIA`
   (400), `_TOTAL` (5000); un tope devuelve la ficha con el motivo llano.
6. **Enlaces de audio y vídeo de Eos** (`b8ffe6e`): de 15 min a
   `LITERALEVEL_RECURSO_SEGUNDOS` (14400 = 4 h).
7. **Boca 3D desfasada del audio** (`2319d37`, `63d23f9`, `e1971ae`): a ≠1× el
   `<audio>` volvía a bajar el mp3 por red (`no-store`) → ahora suena desde los
   bytes ya bajados (`blob:`), la línea se ancla al `playing` real
   (`EscenaBoca.desplazarLinea`) y espera al AudioContext; el sombreado de la
   piel fotográfica (6,5 ms de CPU por cuadro medidos) se recalcula con cadencia
   mientras se mueve; «Leer la frase» espera (1,5 s) la IPA con marcas; mover la
   barra de velocidad ya no relanza la animación y al soltar sigue por donde
   iba; «Frente» ya no corta la línea. **Probar en el móvil**: sonido, palabra,
   frase, 1×/0,5×/2× y «Lado · interior».
8. **Eos: /p b m/ sin cierre de labios, lengua de lado** (`27e2595`, sesión
   principal): comprobado en `front/public/eos/ga/006d.mp4` y `0070.mp4`
   (ningún fotograma con los labios juntos). Nuevo
   `tools/eos_pronunciar/corregir_visemas.py` (actúa sobre `curvas.json` con la
   línea de fonemas que ahora guarda `generar_clips.py`; `trabajador.py` lo
   llama para las frases). **Falta regrabar los 85 clips en el PC de Miguel**:
   `python -X utf8 tools/eos_pronunciar/corregir_visemas.py` (sobre
   `D:/literalevel_eos_pronunciar/visor/clips`, idempotente; `--informe` solo
   mide) y después `python -X utf8 tools/eos_pronunciar/grabar_clips.py
   --rehacer` (≈35 s por clip con el visor del puerto 8790), commit de
   `front/public/eos/`. La lengua de Eos la mueve el visor con las poses de
   Blender, no las curvas: si tras regrabar sigue saliendo de lado o fuera de
   los dientes en /l/, el mapeo de los huesos Tongue está en
   `D:/literalevel_eos_pronunciar/visor/index.html` (sin lateral; punta arriba y
   no adelante en /l/; fuera solo en /θ ð/).

Para publicar (con permiso de Miguel): fusionar `claude/hola-vpznit` en
`master` y hacer push (Vercel construye solo); API con
`tools/desplegar_app.py --solo app/api.py app/seguridad.py app/lexicon.py
app/voz.py` tras `pruebas_seguridad.py` en árbol limpio. Las variables nuevas no
hacen falta en el Space (los valores por defecto aplican). Cupo «Te quedan N
usos»: tabla `acciones` de `/data/seguridad.sqlite3` (ver nota del 4 oct en
`HANDOFF_SEGURIDAD_2026-10-01.md`).

## Objetivo actual

Entrega del Módulo 5: archivos en Classroom («Trabajo Final») el **4 de octubre
de 2026, 11:59 p.m.**; demo en vivo de Miguel el **10 de octubre, turno 5**
(leído en Classroom el 26 sep; copia de los PDF de la tarea en
`D:/literalevel_respaldos/classroom/`) (rúbrica: skill
`modulo-5-literalevel`). La app ya tiene usuarios reales probando. Trabajo en
curso, por orden de Miguel (25 sep):

1. **D5 · lectura guiada en vivo:** PUBLICADA (25 sep). Falta que Miguel la
   pruebe con su voz y su móvil (~13 USD de créditos para pruebas).
2. **Ojos de la cabeza 3D:** PUBLICADOS en la malla
   (`tools/boca3d_blender/ojos_didacticos.py`).
3. **Modelo articulatorio aprendido:** entregables 1-5 del encargo
   (`docs/ai/investigacion_modelo_articulatorio.md`) hechos la noche del
   24-25 sep (de `front/` solo `poses.ajustes3d.json`, en `dev/articulacion-v2`). Informes en
   `investigacion/modelo_articulatorio/` (`resultados.md` manda); código en
   `tools/modelo_articulatorio/`; datos y modelos fuera de Git en
   `D:/literalevel_articulatorio/`. 25 sep, decidido por Miguel: alinear
   sin conexión (hechas las 85 palabras grabadas de Pronunciar:
   `investigacion/modelo_articulatorio/datos/palabras_grabadas_tiempos.json`)
   y ajustar a lo real /ɛ eɪ/ (mandíbula 0,67 y 0,70). **Publicado** en la
   quinta publicación junto con la frase del TTS alineada por palabras
   (marcas de whisper ya guardadas; ver `DESPLIEGUE.md`). Las mejillas ya
   acompañan desde `79982c2`; no se hizo shape key nueva.

4. **Cara que habla (vista de frente):** Miguel eligió MetaHuman (25 sep).
   Rama `dev/cara-parlante` (worktree `.claude/worktrees/cara-parlante`,
   `4ffe122`): informe `docs/ai/informe_cara_parlante.md` (EULA verificado:
   el `.glb` se puede servir; prohibido entrenar o *probar* IA con el
   MetaHuman) y `tools/cara_parlante/` (TalkingHead-1KH CC BY con audio →
   blendshapes, pose y prosodia → cuaderno de Colab).
   **Estado 26 sep, madrugada (último commit en la rama: ver `git log dev/cara-parlante`):** la cara se llama
   **Eos** y la app se llamará **Pléyade** (logos en `D:/literalevel_cara/marca/`).
   - Cara final aprobada por Miguel, con rig completo, ensamblada en UE 5.8
     (`/Game/MetaHumans/Cara_LiteraLevel`); scripts en `tools/cara_parlante/unreal/`.
   - GLB web con 51 ARKit: `metahuman-to-glb` (MIT) clonado en
     `D:/literalevel_cara/herramientas/` con **parches locales** para 5.8
     (config sin comentarios, miniatura opcional, escanear `/MetaHumanCharacter/Face/ARKit`
     en la etapa 01, `ErrorActionPreference=Continue` en 02-04) y Blender 5.1.2
     portátil. La etapa 00 se hizo a mano (Montaje → UE Cine). Sale a 44 MB; comprimido a **6 MB** (`eos_web.glb`,
     `npx @gltf-transform/cli optimize … --compress meshopt --texture-compress webp --texture-size 1024 --simplify false`).
   - Demo local `D:/literalevel_cara/eos_demo/` (`python -m http.server 8765`):
     `generar.py` (edge-tts gratis + modelo articulatorio + modelo de gestos),
     `index.html` (visor), `grabar.py` (vídeo con Playwright/Chrome).
   - Modelo de gestos (`tools/cara_parlante/entrenar_gestos.py`, CPU, 9,8 h de
     1KH + Miralles): r en validación cabeceo 0,46, guiñada 0,31, cejas 0,21,
     sonrisa 0,12; **solo 8 clips de validación**, hay que ampliarla.
   - Obama: **158/158 medidos** (26 sep, 14:28 UTC; 0 fallidos, F0 con Praat) en
     Drive `literalevel_cara/casa_blanca/medidas/`. Servidor de Colab apagado.
     Copia local en `D:/literalevel_cara/medidas/obama/`. **Reentrenado** (`dfef3ec`): con Obama
     (35,4 h) y validación fija de 26 clips / 4,9 h mejora todas las salidas frente a sin Obama
     (sonrisa r 0,04→0,20, cabeceo 0,16→0,21, cejas 0,10→0,14). Los r de 8 clips eran optimistas.
   - Speech2Face (MetaHuman Animator) funciona por Python (`eos_habla.py`), pero
     el render en Unreal agotó la RAM (16 GB); pendiente con el editor limpio.
   - Pendiente: pelo aún algo ralo en la web, integrar en
     Pronunciar detrás del interruptor, vídeo lado a lado con la cabeza actual.
   - **v3 y Audio2Face (26 sep, noche; sesión literalevel-29):** la red de fusión
     tocó techo (época 22, boca r 0,33). Piloto SMIRK en A100 (4,2 u): fiabilidad
     boca 0,35; prueba de legibilidad labial de c2: SMIRK 0,217 vs MediaPipe
     0,206 (azar 0,167) → **sin SMIRK**. Medido y descartado para acelerar:
     MediaPipe cada 2 fotogramas y recorte por BlazeFace (cambian las etiquetas);
     NVDEC sí es idéntico. **Boca de Eos = NVIDIA Audio2Face-3D v3.0** reimplementado
     sin SDK (`D:/literalevel_cara/a2f/a2f_onnx.py`, ONNX Runtime CPU, 9 s → 15 s;
     52 ARKit a 60 fps + 16 de lengua; sin ojos ni cabeza; `mouthClose` incluye
     mandíbula); integrado por c2 en `generar.py --boca a2f` (`5cd4921`).
     **v3 no verbal ENTRENADO** en la A100 de rayko800 (20:19-21:55, ≈11,5 u;
     cuaderno `91f6dfa` + `ENTRENAR_BOCA=0`, `MAX_HORAS=2`): HuBERT-large de 882
     clips (36 GB en Drive `voz2cara/v3/voz`), articulación en `v3/art`, y 6b paró
     por paciencia en la época 232 (mejor 202): pérdida val 0,536, FDD 0,71,
     diversidad 0,93, alineación con golpes de voz 0,773 (real 0,74), r sonrisa
     0,12 / cabeza 0,07 (111 clips de validación). Copiado a
     `D:/literalevel_cara/v3_modelo/noverbal/`; A100 apagada (0,00/h). La boca
     (6a) no se entrenó: relanzar la celda 2 con `ENTRENAR_BOCA=1` reanuda desde
     Drive si hiciera falta. Eos final = `generar.py --gestos v3 --boca a2f` (c2).
     **Boca v3 entrenada** (22:52-23:42, ≈14 u): r boca 0,305 (fusión 0,33), no supera
     a A2F; informe y progreso en `D:/literalevel_cara/v3_modelo/boca/`, `modelo.pt`
     (42 MB) aún en Drive `voz2cara/v3/boca/`. **Pendiente (27 sep):** bajar ese
     modelo.pt, grabar los 3 vídeos comparativos de «Peter Piper» (Blender+gestos
     viejos / A2F+v3 / boca v3+v3) con `generar.py`+`grabar.py`, insertar §7.9 en
     `entrega/documento.*` (texto de f3 en `26bbb92`), y el vídeo extra de Eos
     presentando Pléyade (voz es-MX-DaliaNeural ya en `D:/literalevel_cara/a2f/presenta/`,
     falta A2F + grabar). Las ediciones sueltas de `entrega/` son retoques de Codex (ok).
     **Hardware:** tras el reinicio de las 23:56 el PC solo ve 8 GB de RAM (antes 16):
     un módulo no se detecta.

5. **Marca Pléyade en el front** (26 sep): PUBLICADA (nombre, iconos, «Sobre
   Pléyade», fondo astral en todas las pantallas, recarga si el index está viejo).
6. **Vercel (26 sep, lo pidió el profesor):** el front principal está en
   <https://pleyade-app.vercel.app> (proyecto `pleyade`, equipo `mike-d120`,
   Hobby). El Space estático sigue como respaldo. `master` ya está en GitHub
   (`rayko800-lgtm/literalevel`, privado) y **conectado a Vercel**: cada push a
   `master` publica solo (primer build desde GitHub `522de18`, READY). Ojo: la
   cara 3D (`boca3d/didactica/cara.glb`, 7 MB) tarda ~6 s en Vercel (40 s la
   primera vez); **hecho** el 26 sep: texturas WebP (`1f5f2c9`), 1,7 MB por la
   red y ~2,3 s. Zoom + y − en el visor (`8b83454`).
8. **3D en vídeo (pruebas del 26 sep, para que Miguel decida):** A) vídeo del
   recorrido de los 41 sonidos con la boca 3D (`tools/grabar_afi_3d.py`); B) Eos
   por «llamada»: `generar.py` + `grabar.py` de `tools/cara_parlante/eos_demo`
   (~10 s voz y curvas + ~35 s de grabación por frase en este PC con GPU). Al
   vuelo en el Space gratis no cabe (sin GPU ni Chrome): solo pregrabado.
9. **Lengua, dientes y vista interior de Eos (26 sep):** los hará la sesión de Eos
   (`literalevel-c2`) al terminar su modelo de fusión, por decisión de Miguel. Ejemplo
   de f3 en la rama `dev/eos-lengua` (`2a6519a`): `tools/cara_parlante/eos_demo/lengua_lab.html`
   (corte sagital, lengua separada de los dientes por sus pesos, poses de Blender en los
   huesos Tongue1-4 con constantes K calibradas solo con t, k, θ, l, i) y los guiones
   `lengua_comparar.py` y `lengua_palabra.py` (coarticulación por pesos, sin audio).
6 bis. **Guion y cierre retocados para vender (27 sep, d9):**
   investigación de anuncios eficaces en `entrega/pautas_comercial.md` (ABCD de
   Google/Kantar, System1, Amplified, simulación mental; 10 pautas). Aplicada a
   `guion_video.md/.tex/.pdf` (apertura en «tú» con gesto, una sola idea en N,
   V como escena del espectador, acción «mide tu nivel» sin cuenta; **516
   palabras habladas**, `tools/contar_guion.py`) y a la última diapositiva de
   `presentacion.tex/.pdf` (QR que se decodifica a `https://pleyade-app.vercel.app`
   y la acción). Miguel probó la app sin sesión en el móvil: sin problemas. La
   diapositiva «Antes de comenzar» ya va en «tú», igual que la apertura del guion.
   **El profesor aceptó que Eos hable todo el vídeo** (confirmado por Miguel, 27
   sep; su texto no está archivado): el vídeo evaluado es el comercial de Eos
   (guion y voz: d0, `entrega/guion_video_eos.md`; planos y montaje: 86,
   `docs/ai/guion_eos_planos.md`; lengua `148e2b5`, pendiente de integrar por f6).
   `guion_video.*` queda de respaldo. d9 lleva rúbrica y entrega y revisa el
   piloto con las pautas, por mensaje. **Falta** anotar la excepción en la skill
   global `modulo-5-literalevel` (a d9 se le denegó el permiso para editarla).
7. **Datos por cuenta (26 sep):** publicados (Space `103eef5`). Con usuario y
   contraseña, los datos son de la cuenta en cualquier aparato
   (`cuentas/<nombre>` en el bucket). Contraseñas rotadas (10 perfiles) y
   cuentas en cero. **Pendiente de Miguel:** poner a cero `uso_openai.json` del
   bucket (la sesión no tuvo permiso); respaldo previo: hacerlo en
   `D:/literalevel_respaldos/`.
9. **Entregables al día (26 sep, rama `dev/entregables`, worktree
   `.claude/worktrees/entregables`; fusionada en master y subida, `667a749`):** documento
   (tex/pdf/md, con §7.8 del modelo articulatorio y 8 referencias nuevas),
   estrategia, presentación (16 diapositivas), guiones del vídeo (514 palabras
   habladas) y de la demo, mensaje de entrega final al profesor, cuaderno (solo
   texto markdown; salidas intactas), README, PENDIENTES y 22 capturas desde
   Vercel con la cuenta `miguel` (`entrega/capturas/registro.txt`). Nombre:
   «Pléyade (proyecto LiteraLevel)», decidido por Miguel. Inventario:
   `docs/ai/inventario_entregables_2026-09-26.md`. **La cuenta `miguel` queda
   con perfil C2 1,88** (cuestionario en la app). La «L» de la bienvenida ya es el
   icono de Pléyade (`2b37573`, de literalevel-f3); ninguna captura la muestra.
   **Revisión de f3 (26 sep, tarde, `5c7d1bc`):** cruzados con la rúbrica de la
   skill; cuaderno regenerado desde el `.py` y comparado (103 celdas iguales,
   0 errores); la única cifra falsa era «1,4 MB» de la boca 3D (curl a Vercel:
   1,7 MB con brotli) y su carga ya está medida (`tools/medir_boca3d_vercel.py`:
   3,0–3,1 s sin caché del navegador, 8,9 s con la CDN fría). PDF recompilados.
   **Pendiente:** leer la «Tarea» que Barranco publicó hoy en Classroom (no llega
   por correo; Chrome pide permiso de depuración remota en cada conexión).
   **Siguiente:** grabar el vídeo y ensayar la demo con Pléyade.

## En producción (25 sep 2026)

| Pieza | Revisión del Space | Commit |
|---|---|---|
| Front en Vercel (`pleyade-app.vercel.app`) | deploy del 26 sep | `cd623f9` |
| Front Angular (`MikeMaki1763/literalevel-front`, respaldo) | `be6a190` (26 sep) | `1df10b5` |
| API y Gradio (`MikeMaki1763/literalevel`) | `0547de1` (28 sep, noche) | `7864da8` |

Incluye D1-D3 (Mi espacio, Repasar, Mi progreso; el tutorial v2 sigue detrás
de su flag de desarrollo), el aire 2D en /f/, la boca 3D didáctica con lectura
de frases al compás del audio y la cara del 25 sep, y el arreglo de libros de
teatro sin capítulos (PG844), la lectura en voz alta en vivo en el lector
(`POST /api/lectura/vivo` + `front/src/app/compartido/lectura-vivo/`) y los
ojos abiertos en la malla. Registro completo en `DESPLIEGUE.md`.

## Líneas de trabajo (git)

- **`master` = `publicar/v2`** (26 sep, marca Pléyade y fondo astral): todo lo publicado. `dev/articulacion-v2` tiene además `2159783` (el modelo como módulo, de otra sesión) y le falta fusionar `publicar/v2`. Es la línea
  buena. `origin/master` va muy por detrás (11 sep) y **no se sube** sin
  permiso de Miguel.
- **`dev/articulacion-v2`** (worktree `.claude/worktrees/articulacion-v2`):
  desarrollo del 3D y de D5. Para publicar: fusionar en `publicar/v2`
  (worktree `publicar-3d`), pruebas del backend en árbol limpio, API primero y
  front después, y avanzar `master`.
- Ramas ya fusionadas (sin trabajo propio fuera de master): `dev/onboarding-v2`,
  `dev/navigation-v2`, `dev/mi-espacio-v2`, `boca3d`,
  `publicar/boca3d-didactica`, `worktree-agent-*`, `fase-c-fable` (su parche ya
  está en master). Sus worktrees limpios se quitaron el 25 sep; las ramas se
  conservan. Queda `C:\Users\laura\literalevel-fase-c`, limpio y obsoleto.
- `front/angular.json` en `dev/articulacion-v2` lleva cambios locales ajenos
  (túnel y proxy de pruebas): no se hace commit de ellos.

## Sin commit en el árbol principal (decidir con Miguel)

- `corpus_abierto.parquet` modificado el 15 sep y **no desplegado** (el Space
  tiene la versión del commit). Origen sin documentar: no subir sin saber qué
  cambió.
- Carpetas sin seguimiento de otras sesiones: `.agents/`, `.codex/`,
  `audio_masters/`, `corpus_graduado/`, `auditoria/esmeralda/`.

## Cómo verificar

- Backend: `git archive` del commit a un directorio limpio, datos grandes
  enlazados, y las suites de una en una (RAM): `pruebas_api.py`,
  `pruebas_extremas.py` (~25 min), `pruebas_ficha.py`, `pruebas_progreso.py`,
  `pruebas_repaso.py`, `pruebas_animacion.py`.
- Front: `npx ng test --watch=false`, `npx tsc --noEmit -p tsconfig.app.json`,
  `npm run build`, y la app a 390 px.
- 3D: `node tools/boca3d_demo/medir_didactica.mjs <cara.glb> <salida.json>
  --completo --exigir --exigir-raices --lengua=<lengua.glb>`,
  `medir_grosor_labial.mjs --exigir`, `medir_lengua.mjs --exigir`.
- Despliegue: skill `desplegar-en-spaces`; citar siempre revisión del Space y
  commit.

## Abierto

- 3D: dientes como bloques, costura del mentón en ¾, torso sin ropa; cara que
  habla con expresiones (espera al modelo articulatorio).
- D5: el seguidor a veces marca una palabra corta como saltada si la
  transcripción la junta o la cambia (visto: «known»); ajustar con lecturas
  reales de Miguel. Tope de 3 min por sesión, un uso de la cuenta por sesión.
- «Mi espacio» es la pantalla de Inicio (logo), no una pestaña: Miguel no la
  encontró el 25 sep. Decidir si se hace más visible.
- Cola post-entrega antigua: `auditoria/cola_tras_la_entrega_2026-09-16.md`.

## Siguiente paso exacto

Recoger la prueba de Miguel de la lectura en vivo (voz real, móvil, cuánto
tarda y qué marca mal) y ajustar el seguidor; después, dientes y costura del
mentón.

## GPT-Live (27 sep, `f5c1fa8`)

- **CONFIRMADO en código local:** `/api/gpt-live/sesion` crea la sesión WebRTC
  desde el servidor con el JSON exacto de `app/gpt_live_session.json`; la pantalla
  `/conversar` reproduce audio remoto, muestra deltas con tiempos y espera
  `session.closed` antes de soltar el transporte.
- **Clave local:** guardada fuera del repositorio; `LITERALEVEL_CLAVES_RUTA`
  apunta al archivo elegido por Miguel para los procesos nuevos de Windows.
- **Verificado:** API simulada, 3 pruebas del front, TypeScript, build y pantalla
  móvil visual. **NO VERIFICADO:** conversación real con voz y consumo.
  **NO INTEGRADO EN PRODUCCIÓN:** falta publicar API y front juntos.

## Eos en Pronunciar (28 sep, literalevel-c6; pedido por Miguel)

Miguel (28 sep): los sonidos van **pregrabados** en vídeo de alta calidad y, para un
audio nuevo, el vídeo se genera **por fuera** y vuelve a la app. Hecho, sin publicar:

- **Pregrabados (85 = 41 GA + 44 RP):** `tools/eos_pronunciar/generar_clips.py` da a
  Eos el mp3 de cada sonido (`app/audio_fonemas*/`: sonido ×3 + dos palabras), con los
  tramos por energía y el fonema en ARPAbet (whisper no entiende «shhh»); boca
  Audio2Face + gestos v3 no verbal, llamando al `generar.py` del worktree
  `cara-parlante` (copia de trabajo, la misma que usa Codex) sin editarlo.
  `grabar_clips.py` los graba en un visor aislado (`D:/literalevel_eos_pronunciar/visor`,
  puerto 8790; el rig compartido no se toca) a 640×640, 30 fps, cámara cerca de la
  cara, y deja `front/public/eos/<acento>/<archivo>.mp4` + `clips.json` + `reposo.webp`.
  **Los 85 hechos** (28 sep, tarde): 0 fallos, todos decodifican, 50,7 MB en total (582 KB
  de media por clip de ≈5,8 s; ≈2 min por clip de generación, HuBERT se carga en cada
  uno; registros en `D:/literalevel_eos_pronunciar/`). Los mp4 van en git dentro de
  `front/public/eos/` (Vercel construye desde GitHub): si pesan demasiado, la
  alternativa es servirlos desde el Space o un dataset y cambiar `EosClips.url`.
  Primera tanda desechada: un fallo mío contaminaba los fonemas de un clip con los del
  anterior (arreglado antes de relanzar).
- **Front:** `compartido/eos/eos.ts` (`EosClips` lee `eos/clips.json` una vez;
  `app-eos` es un `<video>` que arranca al abrirse) y en Pronunciar «Ver a Eos» en la
  ficha del sonido, en cada palabra fallada (junto a «Boca en 3D») y «Ver a Eos
  leerla» en la frase bien leída. Sin índice, no hay botón. Spec:
  `pronunciar.eos.spec.ts` (4 pruebas). tsc, build y specs de Pronunciar en verde;
  `pronunciar.css` ya estaba por encima del presupuesto (no crece).
- **Audios nuevos (`app/eos.py`, rutas `/api/eos/*`):** `POST /api/eos/pedir` encola
  el mp3 de `audio_correcto`; un PC con Eos (`tools/eos_pronunciar/trabajador.py`, con
  `LITERALEVEL_EOS_TOKEN` en el entorno y el mismo secreto en el Space) recoge
  `GET /api/eos/cola`, genera (whisper + A2F + v3), graba y sube
  `POST /api/eos/entregar/<clave>`; el front pregunta `estado` cada 4 s (3 min) y
  reproduce `/api/eos/video/<clave>.mp4` (Range soportado). Sin token: «sin_trabajador»
  y el front manda a la boca 3D. Nada llama a OpenAI ni cobra usos. `pruebas_eos.py`:
  TODO OK. Trabajador **probado de punta a punta en local** (API en el puerto 8001 con
  token y datos temporales: pedir → cola → generar+grabar en 110 s → entregar → estado
  «listo» → vídeo con Range 206); contra el Space, pendiente del secreto.
- **PUBLICADO en Vercel (28 sep, noche, con permiso de Miguel):** push
  `de1e731..bceac98` (12 commits, míos y de Codex); build nuevo (`main-HPL2JHFA.js`),
  `eos/clips.json` con 85 entradas y los mp4 con Range 206. Probado en
  `pleyade-app.vercel.app` a 390 px: /ʃ/ → «Ver a Eos» → el vídeo carga y suena.
- **API PUBLICADA (28 sep, noche): revisión del Space `0547de1`, commit `7864da8`**
  (`--solo app/api.py app/config.py app/eos.py app/gpt_live_session.json`; ese json
  lo lee `api.py` al importar y no estaba en la lista blanca: sin él el Space no
  arrancaba). Lleva también `/api/gpt-live/sesion` de `f5c1fa8`. Pruebas en árbol
  limpio antes: `pruebas_eos.py` TODO OK y `pruebas_api.py` 71 de 71. Secreto
  `LITERALEVEL_EOS_TOKEN` puesto en el Space (permiso de Miguel); la copia local está
  en `C:/Users/laura/.literalevel_eos_token`, fuera del repo, nunca se imprime.
  **Probado de punta a punta en producción:** `pedir` de un mp3 del bucket → el
  trabajador de este PC lo hizo en 150 s → `estado` «listo» → vídeo servido con
  Range 206 (`e48078afac94238fd3dba1c4`). Los mp4 de frases quedan en el bucket
  (`/data/eos/`).
  **El trabajador corre en este PC** (nohup, registro en
  `D:/literalevel_eos_pronunciar/trabajador.log`) junto al visor del puerto 8790.
  Muere al reiniciar el PC; para relanzarlo: en `D:/literalevel_eos_pronunciar/visor`
  `python -m http.server 8790 --bind 127.0.0.1`, y con `LITERALEVEL_EOS_TOKEN` en el
  entorno (leído del archivo) `python -X utf8 tools/eos_pronunciar/trabajador.py --api
  https://mikemaki1763-literalevel.hf.space --cada 15`. Sin trabajador, la frase
  queda «pendiente» 3 min en el front y luego manda a la boca 3D; los 85 sonidos
  pregrabados no dependen de él.
- **Auditoría de la entrega (29 sep, 18:30):** `auditoria/preentrega_2026-09-29.md`, nota simulada
  86/110. **SERIO A1, mío:** `tools/a_notebook.py` sobre `entrega/notebook_proyecto.py` regeneró el
  `.ipynb` en su sitio y borró las salidas de la ejecución en Colab de hoy; hay que volver a bajar la
  copia ejecutada de Colab a `entrega/`. Skill `auditar-entrega-modulo-5` corregida (regenerar a un temporal).
  **19:15, corregido:** el notebook se ejecutó en una carpeta limpia fuera del repo (57 celdas, 0 errores,
  0 stderr, 1–57) y esa copia es la de `entrega/`; aviso de `HF_TOKEN` silenciado en el `.py`; diapositiva 4
  con el catálogo final; `guion_video.md` l. 30 aclarado; commit de las rutas de `entrega/` (sin el 4K).
  Quedan para Miguel: copia del vídeo en Classroom, `uso_openai.json` a cero, «Entregar» y el ensayo.
- **Segunda auditoría (30 sep, 01:40):** `auditoria/preentrega_2026-09-30.md`, 89/110, 0 serios. Notebook
  ejecutado en limpio por segunda vez (0 errores, 0 stderr); Colab real no se pudo lanzar (la conexión al
  Chrome de Miguel esperó 30 min un permiso). Para Miguel: Colab, volver a adjuntar en Classroom, vídeo
  720p, `uso_openai.json`, «Entregar», ensayo.
- **Revisión ampliada (30 sep, tarde):** 96/110. `documento.tex/.pdf` recompilado (**66 páginas**: cuadros 7 y 8
  bajo sus títulos 3.7 y 3.8, columnas de los cuadros 3 y 6): **volver a subirlo a Classroom**; PENDIENTES aún
  dice 65. **B1, serio para la demo:** la cuenta `miguel` está en 0,72/B1 (cuestionario del 27 sep) y el guion de
  la demo pide 1,20/B2; receta para 1,20 y detalle en `auditoria/preentrega_2026-09-30.md`.
- **Auditoría completa (30 sep, noche):** documento (66 pp.), estrategia (20) y cuaderno leídos enteros; `estrategia.md/.pdf`
  (Cuadro 21→28, PDF regenerado con `tmp/pdfs/make_strategy.mjs` + Chrome) y `notebook_proyecto.py/.ipynb` (599→598,
  reejecutado en limpio) corregidos. Volver a subir a Classroom documento, estrategia y cuaderno. 96/110.
