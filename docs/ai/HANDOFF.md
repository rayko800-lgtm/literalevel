# LiteraLevel — AI Handoff

Estado operativo, corto y vigente. La historia está en
`docs/ai/legacy_architecture/` (los dos HANDOFF anteriores completos, del
árbol y de la rama de desarrollo, hasta el 24-25 sep) y en `git log`.

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
| API y Gradio (`MikeMaki1763/literalevel`) | `103eef5` (26 sep) | `06a16db` |

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
