# Encargo para una sesión LOCAL en el PC de Miguel (4 oct 2026)

Escrito por la sesión en la nube `literalevel-5e` (rama `claude/hola-vpznit`),
que no puede ver el PC de Miguel ni bajar el vídeo (la red de su entorno bloquea
Drive). Todo lo que necesita archivos locales, la GPU o el visor de Eos lo hace
esta sesión local. Lee antes `AGENTS.md` (reglas de git: nunca `git add -A`,
`git add .`, `git commit -a`, `git stash`, `git reset --hard`; añade solo tus
archivos; nunca imprimas secretos) y `CLAUDE.md` (política secuencial; Sonnet
para implementar, Fable solo si hace falta).

## 0. Punto de partida

```
git fetch origin
git checkout claude/hola-vpznit        # último commit de la nube: f56c35f o posterior
```

Lo que YA está hecho y verificado en esa rama (no repetir, solo probar en real):

| Qué pidió Miguel tras grabar la demo | Arreglo | Commit |
|---|---|---|
| La cabeza 3D (Blender) sale en blanco | `connect-src blob:` en la CSP de `front/vercel.json` (three.js hace `fetch` de un `blob:` para la textura WebP embebida) | `8a225a3` |
| Al pulsar reproducir baja al 3D aunque subí a ver el 2D | `colocarALaVista` elige el bloque más visible; al abrir el 3D sigue bajando a él | `fa8d808` |
| Al cambiar de pestaña se pierde la frase, la corrección y el vídeo de Eos | servicio raíz `front/src/app/pantallas/pronunciar.estado.ts`; franja «Eos ya tiene lista tu frase» en la cabecera | `1a994b6` |
| Me volvió a pedir la contraseña tras cambiarla | `POST /api/cuenta/clave` devuelve sesión nueva (`token`, `expira_en`); el formulario va plegado | `22fce02` |
| Con sesión no me da la explicación de OpenAI de la palabra | `seguridad.CONTEXTO` (ContextVar) no llegaba a los hilos de `lexicon`/`voz`: `contextvars.copy_context().run`; topes de llamadas configurables | `54c39ba` |
| (anomalía vista en código) enlaces de audio/Eos caducaban a los 15 min | `LITERALEVEL_RECURSO_SEGUNDOS`, 4 h por defecto | `b8ffe6e` |
| La boca 3D se desfasa del audio (también en «Lado · interior» y al cambiar velocidad) | audio desde `blob:`, línea anclada al `playing` real, espera al AudioContext, cadencia del sombreado, espera a la IPA, la barra ya no relanza | `2319d37` `63d23f9` `e1971ae` |
| Eos no cierra los labios en /m/ /p/; la lengua va de lado y sale | `tools/eos_pronunciar/corregir_visemas.py` + `generar_clips.py`/`trabajador.py` lo llaman. **Falta regrabar** | `27e2595` |

Verificación en la nube: front 531 pruebas y `npm run build` en verde;
`pruebas_seguridad.py` 43/43; `pruebas_eos_visemas.py` 9/9; `pruebas_api.py`
64/71 (los 7 fallos son por falta de `kaikki_diccionario.db` y red; en el PC
deberían pasar). **Nada está publicado** en Vercel ni en el Space. Detalle en
`docs/ai/HANDOFF.md` (sección «Auditoría de la demo grabada») y
`docs/ai/HANDOFF_SEGURIDAD_2026-10-01.md` (nota del 4 oct).

Ojo con el entorno: el Angular CLI exige Node ≥ 22.22.3; las pruebas del front
se corren desde `front/` con `npx ng test --watch=false`, el typecheck con
`npx tsc --noEmit -p tsconfig.app.json`, el build con `npm run build`.

## 1. Revisar el vídeo de la demo (vídeo Y audio)

Archivo: `para fable.mp4` en la carpeta de Descargas de Chrome de este PC (823
MB; también en Drive). Es Miguel recorriendo la app en el móvil tras la
auditoría de seguridad del 1 oct, narrando lo que falla.

1. Transcribe el audio (en el PC hay whisper, el que usa `generar.py` de
   `D:/literalevel_cara/eos_demo`; o `whisper`/`faster-whisper` con GPU) y guarda
   la transcripción con marcas de tiempo en `auditoria/demo_2026-10-04/transcripcion.md`.
2. Saca fotogramas (`ffmpeg -i "para fable.mp4" -vf fps=1/2 ...`) y recorre el
   vídeo entero. Anota en `auditoria/demo_2026-10-04/hallazgos.md` cada anomalía
   con minuto:segundo, pantalla, qué se ve y qué dice Miguel.
3. Cruza cada hallazgo con la tabla de arriba: ¿lo cubre un arreglo ya hecho?
   ¿coincide la causa con lo que se ve (p. ej. el mensaje exacto que apareció
   cuando no llegó la explicación de OpenAI, o «Te quedan 0 usos» en Ajustes)?
   Si el vídeo contradice un diagnóstico, corrige el código, no el informe.
4. Lo que no esté cubierto: arréglalo en la misma rama, con prueba, un commit
   por asunto, mensaje en español en el estilo del repo.
5. Prueba en real, en un navegador del PC y si se puede en el móvil con
   `npm start` + túnel, lo que la nube no pudo ver: cabeza 3D con textura, el
   scroll 2D/3D, la sincronía a 1×/0,5×/2× y en «Lado · interior», el aviso de
   Eos al cambiar de pestaña, cambiar la contraseña sin salir de la sesión.

## 2. Regrabar los 85 clips de Eos (lo pidió Miguel: «hazlo sin problema»)

Requisitos (todo en este PC): `D:/literalevel_eos_pronunciar/visor` con sus
`clips/*/curvas.json` ya generados (si faltan, `generar_clips.py` los regenera,
≈2 min por clip), el worktree `.claude/worktrees/cara-parlante` con
`tools/cara_parlante/eos_demo/generar.py`, `D:/literalevel_cara/v3_solo_noverbal`,
Chrome con GPU y Playwright.

```
# terminal 1, desde D:/literalevel_eos_pronunciar/visor
python -m http.server 8790 --bind 127.0.0.1

# terminal 2, desde la carpeta del repo, en la rama claude/hola-vpznit
python -X utf8 tools/eos_pronunciar/corregir_visemas.py --informe   # solo mide: cierres por clip, curvas de lengua
python -X utf8 tools/eos_pronunciar/corregir_visemas.py             # escribe; guarda curvas.sin_corregir.json; idempotente
python -X utf8 tools/eos_pronunciar/grabar_clips.py --rehacer       # ≈35 s por clip, ~50 min; deja front/public/eos/
```

Qué comprobar después, antes del commit:
- `ffmpeg -i front/public/eos/ga/006d.mp4 -t 2.4 -vf "fps=10,scale=160:160,tile=6x4" -frames:v 1 m.png`
  (y lo mismo con `ga/0070.mp4` para /p/): en los tres sonidos sostenidos de la
  /m/ los labios tienen que estar juntos; en la /p/, juntos justo antes de cada
  explosión. Antes de corregir no se juntaban en ningún fotograma.
- `ga/006c.mp4` (/l/): la lengua no debe asomar entre los dientes ni irse de
  lado. Si sigue así, el problema está en el visor, no en las curvas: el
  informe de `--informe` dirá «sin curvas de lengua (la pone el visor)». En ese
  caso toca el mapeo de los huesos Tongue1-4 en
  `D:/literalevel_eos_pronunciar/visor/index.html` (copiado del rig de
  `D:/literalevel_cara/eos_demo/index.html`): sin componente lateral; en /l/ la
  punta sube al alvéolo, no avanza; fuera de los dientes solo en /θ ð/.
- `clips.json` con 85 entradas y los mp4 decodificando (`ffprobe`).

Commit: `git add front/public/eos` (solo eso) y mensaje tipo «Eos: 85 clips
regrabados con el corrector de visemas (cierre en /p b m/, lengua acotada)».
Push a `claude/hola-vpznit`. El trabajador de frases nuevas
(`tools/eos_pronunciar/trabajador.py`) ya aplica el corrector solo; relánzalo
si estaba corriendo con el código viejo.

## 3. Publicar (solo con el visto bueno de Miguel)

1. `pruebas_seguridad.py` y `pruebas_api.py` en árbol limpio (`git archive`
   del commit a un directorio aparte, como dice el HANDOFF); pruebas del front.
2. Fusionar `claude/hola-vpznit` en `master` y hacer push: Vercel construye y
   publica el front solo. Comprobar en `pleyade-app.vercel.app` (móvil, 390 px)
   que la cabeza 3D tiene textura y que la CSP incluye `connect-src ... blob:`.
3. API: `python tools/desplegar_app.py --solo app/api.py app/seguridad.py app/lexicon.py app/voz.py`
   (skill `desplegar-en-spaces`), luego `/api/salud` con JSON y
   `tools/auditar_produccion.py`. Las variables nuevas
   (`LITERALEVEL_LLAMADAS_*`, `LITERALEVEL_RECURSO_SEGUNDOS`) no hacen falta:
   los valores por defecto ya aplican.
4. Cupo «Te quedan N usos» de la cuenta `miguel`: vive en la tabla `acciones`
   de `/data/seguridad.sqlite3` del bucket; para reponerlo,
   `UPDATE acciones SET usos=0 WHERE nombre='miguel'` con el Space parado. No
   borrar el archivo entero.
5. Apuntar en `DESPLIEGUE.md` y en `docs/ai/HANDOFF.md` revisión del Space,
   commit y build de Vercel, como siempre.

## 4. Al terminar

Actualiza `docs/ai/HANDOFF.md`: qué del vídeo se confirmó, qué se corrigió de
nuevo, si los clips de Eos quedaron bien (con los fotogramas de prueba en
`auditoria/demo_2026-10-04/`), y qué queda para la demo en vivo del 10 de
octubre (ensayo con la cuenta `miguel`, nivel de la cuenta, cupo).
