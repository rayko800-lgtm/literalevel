# Relevo de Codex para [Central]

Miguel pidio continuar el 13 de septiembre por la noche, sin compras ni
comprometer el proyecto. Se conserva el reparto por archivos y se trabaja
localmente: al cerrar la primera tanda no habia autorizacion de despliegue.

## Actualizacion: Despliegue Autorizado

Miguel autorizo despues explicitamente cambios, pruebas y despliegue. Codex
principal fue el unico desplegador. Backend publicado en
`e56cf08b2de2c98542963cf2ae3286313d23f684`: solo `app/api.py` y `app/voz.py`,
con los cierres descritos abajo. RUNNING, salud JSON, lectura Angular y rechazo
de voz anonima comprobados; ambos archivos cotejados por hash despues de subir.
No se cambio hardware, plan, secretos ni frontend; no se compro nada.

Script protegido en `7e68a54` y `0aec4ee`: `--solo`, rechazo de cambios sin
commit, control de revision remota y escaneo de los bytes enviados. Diez
pruebas offline. Se repitieron las siete de voz y once de portadas.
La suite API completa ahora se pudo ejecutar en un entorno aislado: 32/35;
tres fallos relacionados con el diccionario por falta de spaCy en ese entorno.
No se cuentan como aprobados. Detalles, limites y otro caso de acepcion
incorrecta observado en `despliegue_codex_2026-09-13_noche.md`.

El resto de este documento conserva el estado historico de la primera tanda.

## Fuente Del Encargo

Se leyeron AGENTS.md, CLAUDE.md y las skills `sesion-central`,
`trabajar-en-equipo`, `corregir-sin-inventar` y `probar-la-app-de-verdad`.
Se recuperaron mensajes de texto de la sesion Claude `[Central]`
`b5e5e340-2e98-4b94-9342-9ea036ff5e50`, hasta el ultimo avance registrado
al iniciar este relevo. No se leyeron `.env` ni `CLAVES.txt`.

Base principal al entrar: `f1cfb5d`. Base 3D separada: `boca3d` en
`.claude/worktrees/boca3d`, limpia en `7aef8f8`. No se fusiona esa rama
experimental ni se modifica un worktree ajeno para desplegarlo.

## Reparto De Esta Sesion

- Codex principal: coordinacion, revision independiente de resultados,
  informe de voz y este relevo. No edita `ui.py`, ni los cambios de catalogo.
- Agente portadas: `tools/colab_portadas.py`, notebook, pruebas e informe.
  Despues, tarea acotada de concurrencia TTS/migracion en `app/voz.py` y una
  prueba nueva, sin cambios de contrato publico.
- Agente Blender: solo rama `boca3d`, generador GLB, demo y pruebas. No master,
  API ni Space.
- Agente API: auditoria estatica y despues cierre separado del fallo de
  temporal de voz en `app/api.py` y pruebas. No `ui.py` ni resto de hallazgos.

## Portadas

Commit `0a2cd1c`: guardas antes de GPU, permiso separado para publicar,
reanudacion por trio completo, muestras locales reutilizadas, escrituras
atomicas y notebook sin GPU preseleccionada. El principal volvio a ejecutar
`C:/Users/laura/anaconda3/python.exe -X utf8 pruebas_portadas.py`: 11/11.

**No hay portadas FLUX nuevas.** No se conecto Colab, ni se descargaron pesos,
ni se consumieron unidades, ni se publico en el bucket. La tanda requiere
saldo y tarifa confirmados, generacion de muestras y aprobacion visual.
Detalles y limites en `portadas_relevo_codex.md`.

## Blender

La base ya tenia diptongos, /h/, cavidad nasal, ocultacion de dientes laterales
y correcciones de la lengua. No se atribuyen esos avances a Codex.
Commit `9ae5494` en rama `boca3d`: labios, perfil nasal, techo nasal, faringe,
garganta y suelo mandibular suavizados; lengua /theta/ corregida y validador
alineado con la transformacion de Three.js. La demo carga GLB por defecto y
conserva respaldo geometrico si falla. **Sin fusionar en master ni integrar
en las pantallas Angular publicas.**

El agente ejecuto build Angular, 19/19 pruebas y validacion Blender de 53 poses.
El principal inspecciono capturas lateral /ng/ y movil /theta/ y repitio
`probar_blender.mjs`: dos viewports, 24 capturas, sin errores, movimiento /h/,
canvas no vacio, encuadre sin corte, respaldo GLB y punta interdental correctos
segun los umbrales del guion. No sustituye revision anatomica ni prueba en
telefono fisico. Es un corte didactico, no una cara fotorrealista completa.

Demo: http://127.0.0.1:61229/ , PID 21428 al cerrarse esta tanda. Solo escucha
en loopback, no es una publicacion ni un enlace movil remoto. El servidor
se inicio oculto, sin tocar los procesos ajenos. Detenerlo solo tras verificar
que el PID aun es el servidor de esta demo; puede reutilizarse tras terminar.
Detalles, comandos y limites en
`.claude/worktrees/boca3d/auditoria/cierre_blender_codex_2026-09-13.md`.
La rama termina en `9c38293`, que aclara ese informe sin cambiar codigo.
Solo sigue vivo ese servidor; terminaron los procesos de pruebas.

## Auditorias Recuperadas

- `codex_api_relevo_2026-09-13.md`: cuatro hallazgos por inspeccion sobre
  `f1cfb5d`, con escenarios y pruebas pendientes. No es una prueba remota.
- `codex_voz_relevo_2026-09-13.md`: concurrencia de audio/migracion y limites
  del filtro de indices. No hubo llamadas a OpenAI ni ejecucion de la app
  para esos informes.

Se conserva el informe historico: cualquier arreglo posterior se identifica
por su commit de cierre, no borrando el hallazgo en la base auditada.

## Cierres De Voz Y API

- `71e4b52`: `app/voz.py` y `pruebas_voz_concurrencia.py`. Candados acotados
  para deduplicar TTS dentro del proceso; migracion SQLite con transaccion
  antes de entregar la conexion. Firma publica sin cambios.
- El principal reviso el diff y repitio
  `C:/Users/laura/anaconda3/python.exe -X utf8 pruebas_voz_concurrencia.py`:
  7/7. Son funciones reales extraidas por AST, proveedor simulado y SQLite
  temporal; cinco rondas de ocho lectores TTS y cinco de doce escritores.
  No se importan config/voz completos. Pendiente deduplicacion TTS entre
  procesos si se cambia el despliegue de proceso unico.
- `a87caa8`: `app/api.py` (solo manejador de voz), `pruebas_api.py`, runner
  `pruebas_api_voz_temporal.py` y cierre separado. Crear/escribir el temporal
  ocurre antes de cobrar; se limpia tambien al rechazar la cuota.
- El principal reviso el diff y ejecuto
  `C:/Users/laura/AppData/Roaming/uv/tools/colab-mcp/Scripts/python.exe -B -X utf8 pruebas_api_voz_temporal.py --comparar f1cfb5d`:
  tres escenarios HTTP multipart pasan y detectan el manejador viejo como
  regresion. Starlette avisa de deprecacion de su TestClient con httpx;
  la prueba pasa sin instalar nada. NO se ejecuto toda la integracion
  FastAPI/Gradio: faltan esas dependencias en los Python localizados.
- Analisis sintactico en memoria de API, voz y sus pruebas: correcto.
- Permanecen abiertos los hallazgos 1, 2 y 4 de la auditoria API y el filtro
  heuristico de indices de la auditoria voz. No se parchean firmas compartidas
  ni se introduce borrado de archivos del usuario de forma improvisada.

## No Pisar

Al entrar ya estaban modificados `AGENTS.md`, `app/catalogo.py`,
`pruebas_corpus.py`, `tools/banco_mutantes.py`; tambien existian sin seguimiento
`.angular/`, `.claude/skills/sesion-central/`,
`auditoria/codex_lexicon_5033e69.md` y `entrega/Untitled-1.ipynb`.
No se incluyen esos cambios en los commits de este relevo ni se revierten.

## Cola Para Claude

1. Leer este relevo y comprobar `git status`, `git log` y el estado de `boca3d`.
2. Cotejar los cierres de auditoria antes de tocar API/voz. Pendientes
   importantes: sinopsis simultaneas y reservas/reintegros ligados a identidad
   mutable; requieren coordinacion API/Gradio, no un parche aislado.
3. Portadas: no lanzar GPU ni tanda sin los datos/validacion indicados arriba.
4. Blender: revisar muestra y limites antes de decidir integracion en Angular.
5. Documentacion/presentacion/video aun deben cotejarse con Angular + API,
   como senalo Central. No se afirma que esa entrega haya quedado actualizada.

No hay mensaje directo confirmado a Claude: sus sesiones no aparecen en el
equipo de Codex. Este archivo queda enlazado desde CLAUDE.md para el siguiente
arranque. No se programa un comando que reanude Claude con permisos amplios
ni un proceso de gasto automatico durante la ausencia de Miguel.
