# LiteraLevel — AI Handoff

Estado operativo, corto y vigente. La historia está en
`docs/ai/legacy_architecture/` (los dos HANDOFF anteriores completos, del
árbol y de la rama de desarrollo, hasta el 24-25 sep) y en `git log`.

## Objetivo actual

Entrega del Módulo 5 el **3 de octubre de 2026** (rúbrica: skill
`modulo-5-literalevel`). La app ya tiene usuarios reales probando. Trabajo en
curso, por orden de Miguel (25 sep):

1. **D5 · lectura guiada en vivo** con la transcripción en tiempo real de
   OpenAI (pruebas con ~13 USD de créditos de Miguel).
2. **Ojos de la cabeza 3D** (Blender y visor).
3. **Modelo articulatorio aprendido:** lo investiga otra sesión con
   `docs/ai/investigacion_modelo_articulatorio.md`; esta no lo toca.

## En producción (25 sep 2026)

| Pieza | Revisión del Space | Commit |
|---|---|---|
| Front Angular (`MikeMaki1763/literalevel-front`) | `a9ae51f` | `acbee33` |
| API y Gradio (`MikeMaki1763/literalevel`) | `c49604e` | `acbee33` |

Incluye D1-D3 (Mi espacio, Repasar, Mi progreso; el tutorial v2 sigue detrás
de su flag de desarrollo), el aire 2D en /f/, la boca 3D didáctica con lectura
de frases al compás del audio y la cara del 25 sep, y el arreglo de libros de
teatro sin capítulos (PG844). Registro completo en `DESPLIEGUE.md`.

## Líneas de trabajo (git)

- **`master` = `6b7c95c`** = `publicar/v2`: todo lo publicado. Es la línea
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

- 3D: ojos (mirada y párpados), dientes como bloques, costura del mentón en ¾,
  torso sin ropa.
- Cola post-entrega antigua: `auditoria/cola_tras_la_entrega_2026-09-16.md`.

## Siguiente paso exacto

Prototipo de D5 en `dev/articulacion-v2`: token efímero desde la API (la clave
nunca va al navegador), WebRTC con `gpt-live-transcribe`, seguimiento de la
posición por alineación del texto y tope de minutos por cuenta. Probar con
Miguel antes de publicar.
