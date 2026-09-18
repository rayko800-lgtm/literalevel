# LiteraLevel — Desarrollo v2 (entrega 3 oct 2026)

Estado operativo del desarrollo. No es historial: cuando algo cambia de
estado, se reemplaza, no se acumula. Ver `docs/ai/HANDOFF.md` para el
estado operativo general y `docs/ai/AUDIT_STATUS.md` para las auditorías
pre-entrega en curso (que siguen su propio ciclo, independiente de este).

## Leyenda

- ⬜ PENDING
- 🟡 RUNNING
- 🟠 FIX REQUIRED
- 🔵 VERIFY
- ✅ PASSED
- ⏸ DEFERRED
- ❌ FAILED

---

## D0 — Baseline estable

**Status:** ✅ PASSED

**HEAD:** `004eb28` (auditoria: guion cerrado, c1fcfd4; estado al cierre
del 16 de septiembre).

**Front vigente:** `ec68419` / `8a992af`.
**Motor vigente:** `72f3cdc` / `61e3bba`.

Evidencia: `docs/ai/AUDIT_STATUS.md` A0-A5 (✅ PASSED), A7 en 🔵 VERIFY
(pendiente un segundo ensayo, no bloquea el baseline en sí). Ver también
`auditoria/ensayo_demo_final_2026-09-16.md`.

Working tree con cambios sin commitear conocidos y sin relación con
código de aplicación: `.claude/skills/sesion-central/SKILL.md`,
`AGENTS.md`, `CLAUDE.md`, `corpus_abierto.parquet` (diferencia binaria ya
anotada), `entrega/documento.tex`, `entrega/estrategia.md`,
`entrega/guion_video.md`, `entrega/documento.pdf` (las cuatro últimas, de
las correcciones A2/A4 de esta ronda de auditorías). Ningún archivo de
`app/` ni de `front/src/` está modificado sin commit.

---

## D1 — Onboarding guiado

**Rama/worktree aislado:** `dev/onboarding-v2`, en
`.claude/worktrees/onboarding-v2`, creada desde `004eb28` (el baseline D0).
`master` no se ha tocado; sigue en `004eb28`, recuperable.

**Feedback visual/UX adicional (Miguel, 18 sep), registrado sin implementar
— D1 sigue ✅ COMPLETE, esto es refinamiento futuro, no una reapertura:**
Miguel aprueba la introducción actual pero la quiere más directiva
*visualmente*, no más restrictiva: spotlight más evidente, una acción
dominante por paso, copy mínimo, posible pulso/resaltado del target,
autoavance por acción real (ya así desde D1.2-D1.5), conservar siempre
Saltar. Principio explícito: "más directiva visualmente, no más
restrictiva". Pendiente de que Miguel lo priorice como una ronda propia
sobre `dev/onboarding-v2`.

### D1.1 — Motor (tutorial state machine, overlay, persistencia)

**Status:** ✅ PASSED

**Commit:** `bc95db8` en `dev/onboarding-v2`.

**Archivos creados:** `front/src/app/nucleo/tutorial.ts` (+spec),
`front/src/app/compartido/spotlight.ts` (+spec).
**Archivos modificados (mínimo):** `front/src/app/app.ts`, `app.html`
(montar `<app-spotlight>` en la raíz), `front/src/app/compartido/ajustes.ts`
(enlace "Repetir tutorial", visible solo con el flag activado).
**Sin tocar:** `bienvenida.ts` y su spec, cualquier pantalla de
`front/src/app/pantallas/`, todo `app/*.py`.

**Evidencia de los criterios de salida:**
- Suite completa del front: 33/33 archivos, 176/176 pruebas — incluye las
  12 nuevas de `tutorial.spec.ts`, las 13 nuevas de `spotlight.spec.ts`, y
  las de `bienvenida.spec.ts`/`bienvenida-cuenta.spec.ts` sin tocar, todas
  verdes.
- Persistencia versionada probada: guarda/restaura `{version, pasoId,
  estado}`; un `pasoId` inexistente o una `version` distinta degradan a
  inactivo sin lanzar excepción (pruebas dedicadas).
- Saltar/Atrás/Siguiente/Terminar/Repetir probados en `spotlight.spec.ts`
  y `tutorial.spec.ts`.
- Overlay nunca duplicado por construcción: un único `<app-spotlight>` en
  la raíz de `app.html`, fuera del `<router-outlet>`, no dentro de una
  pantalla.
- Target inexistente no bloquea: probado con un elemento que aparece tarde
  (lo encuentra dentro del margen) y uno que nunca aparece (se rinde a los
  1500 ms, tarjeta centrada con Reintentar/Siguiente/Saltar, sin timers
  colgados).
- Flag OFF preserva la experiencia actual: sin `literalevel.tutorial-dev`
  ni `?tutorialv2=on`, `tutorial.habilitado()` es siempre falso,
  `<app-spotlight>` no renderiza nada, y el enlace nuevo de Ajustes queda
  oculto — confirmado porque toda la suite previa (incluida Ajustes)
  sigue verde sin cambios.
- Hallazgo corregido durante la implementación: la guarda inicial de
  coexistencia usaba `sesion.bienvenida()` como si significara "se está
  mostrando ahora", pero por defecto es `true` para cualquier visitante
  nuevo (significa "no la ha visto todavía"), lo que habría ocultado el
  tutorial siempre. Se cambió a: al activarse el tutorial, cierra la
  bienvenida vieja explícitamente (`sesion.cerrarBienvenida()`), en vez de
  quedar bloqueado por su estado por defecto.

### D1.2 — Entrada e intención

**Status:** ✅ PASSED

**Commit:** `6bb3719` en `dev/onboarding-v2` (sobre `bc95db8` de D1.1).

**Archivos modificados:** `front/src/app/nucleo/tutorial.ts` (reescrito:
máquina de estados como grafo, no lista lineal), `front/src/app/nucleo/sesion.ts`
(+`sesionConocida` compartido), `front/src/app/compartido/spotlight.ts`
(paso de elección, píldora no modal, sin botón "Siguiente" genérico),
`front/src/app/pantallas/nivel.html` (+`data-tutorial="nivel-ver-libros"`,
una línea). **Sin tocar:** `bienvenida.ts`, cualquier otra pantalla, `app/*.py`.

**Flujo:** `cuenta-eleccion` (Entrar/Continuar sin cuenta, sin autorregistro)
→ `intencion` (Leer/Medir mi nivel/Practicar) → `leer-eleccion` o
`nivel-inicio`→`nivel-final` o `practicar-eleccion` → checkpoints
`encontrar-inicio`/`practicar-inicio`. Ninguna rama llama `completar()`:
los tres destinos dejan `activo()` en `true`, reservando `completado` para
el final real de D1.5.

**Evidencia de los criterios de salida:**
- Sesión asíncrona: `cuenta-eleccion` nunca se muestra a quien ya está
  autenticado, ni siquiera un instante (probado UNKNOWN→AUTHENTICATED y
  UNKNOWN→ANONYMOUS por separado).
- Avance por la acción real: `nivel-final` avanza al observar que el
  router navega a `/encontrar` (el botón real de `nivel.html`), nunca por
  un "Siguiente" del tutorial — probado que ese botón no existe en esa
  tarjeta.
- Checkpoints (`encontrar-inicio`, `practicar-inicio`) y `nivel-inicio`:
  sin tarjeta modal, solo la píldora no modal; sobreviven un refresh
  simulado (progreso persistido); `tutorial.activo()` sigue `true` al
  llegar a los tres, nunca `completado`.
- Suite completa: 33/33 archivos, 193/193 pruebas (27 de `tutorial.ts`, 15
  de `spotlight.ts`, más las 151 previas sin tocar, incluidas
  `bienvenida.*` y `nivel.spec.ts`).
- Hallazgo corregido durante la implementación: `historial` (para "Atrás")
  era un array mutado con `.push()/.pop()`; como `puedeAtras` es un
  `computed`, no se invalidaba al cambiarlo (y el cortocircuito de `&&`
  hacía que la primera lectura ni siquiera registrara `pasoActual()` como
  dependencia). Se cambió a una signal.
- "Crear cuenta self-service" registrada en `docs/ai/PRODUCT_ROADMAP.md`
  como POST-ENTREGA, sin implementar.

### D1.3 — Búsqueda y libro

**Status:** ✅ PASSED

**Commit:** `6e8261d` en `dev/onboarding-v2` (sobre `6bb3719` de D1.2).

**Archivos modificados:** `front/src/app/nucleo/tutorial.ts` (nuevos pasos
`encontrar-busqueda`/`encontrar-resultados`/`libro-ficha`/`lector-inicio`,
`notificarBusqueda()`, `avisoTransitorio`, watcher de router consolidado con
resolución en cadena), `front/src/app/pantallas/encontrar.ts` (inyecta
`Tutorial`, notifica inicio/con-resultados/sin-resultados/error — nunca al
revés), `front/src/app/compartido/tarjeta-libro.ts` (+`data-tutorial=
"tarjeta-libro"`, utilidad técnica, no es el objetivo del paso),
`front/src/app/compartido/spotlight.ts` (muestra `avisoTransitorio`).
**Sin tocar:** `libro.ts`, `lector.ts`, `bienvenida.ts`, `app/*.py`.

**Flujo:** checkpoint `encontrar-inicio` (D1.2) → resuelve a
`encontrar-busqueda` solo cuando el router está REALMENTE en `/encontrar` →
`encontrar-resultados` (target: la ZONA `[data-tutorial="encontrar-
resultados"]`, no una tarjeta concreta) → `libro-ficha` (silencioso, píldora,
sin velo) → checkpoint `lector-inicio`. Ninguna rama llama `completar()`.

**Evidencia de los criterios de salida:**
- Cero resultados y error nunca avanzan el tutorial ni marcan progreso
  falso; el aviso se limpia al empezar cada búsqueda nueva.
- Cualquier tarjeta (probado con una que no es la primera) y cualquier
  camino "Leer" de la ficha (probado con un capítulo distinto del inicial)
  avanzan igual — el avance depende de a dónde navega el router, no de qué
  elemento se pulsó.
- `notificarBusqueda()` no hace nada si el tutorial está inactivo o si el
  paso actual no es `encontrar-busqueda` (probado).
- `libro-ficha` no usa tarjeta modal ni velo: solo la píldora no modal, sin
  robar foco ni bloquear los botones reales de la ficha.
- Restaurar `encontrar-inicio` fuera de `/encontrar` no produce avance
  falso; una navegación real posterior sigue reconciliando el progreso.
- `lector-inicio` sobrevive un refresh simulado, `activo()` sigue `true`.
- Suite completa: 33/33 archivos, 210/210 pruebas (38 de `tutorial.ts`, 21
  de `spotlight.ts`, resto sin tocar).
- Hallazgo corregido durante la implementación: el watcher de router inicial
  usaba `if/return` con el `pasoIdActual()` leído una sola vez al principio
  del evento; una sola navegación real (p. ej. `nivel-final` → `/encontrar`)
  debía resolver dos pasos en cadena (`encontrar-inicio` → `encontrar-
  busqueda`), y con `return` temprano el tutorial se quedaba esperando una
  segunda navegación que nunca iba a llegar. Se cambió a leer
  `pasoIdActual()` de nuevo en cada condición, encadenando las resoluciones
  dentro del mismo evento (dos pruebas de D1.2 que asumían el corte en
  `encontrar-inicio` se actualizaron para reflejar el comportamiento
  correcto, ahora que D1.3 le da contenido real a ese checkpoint).

### D1.4 — Léxico y Pronunciar

**Status:** ✅ PASSED

**Commit:** `ce06e27` en `dev/onboarding-v2` (sobre `6e8261d` de D1.3), un
solo incremento, sin dividir en D1.4a/b/c (aprobado por Miguel).

**Archivos modificados:** `front/src/app/nucleo/tutorial.ts` (6 pasos:
`lector-inicio`→`lector-palabra`→`lexico-abierto`→`pronunciar-grabar`→
`pronunciar-resultado`→`post-lectura-inicio`; `notificarLector()`,
`notificarPronunciar()`, `registrarContextoPronunciar()`, watcher de router
extendido con match de origen para "Continuar leyendo"),
`front/src/app/pantallas/lector.ts`/`.html` (notifica al tutorial con hoja
local utilizable; `escribirPosicion()` extraído para volcado inmediato
antes de ir a Pronunciar; CTA con `libro`/`cap`; `+data-tutorial`),
`front/src/app/pantallas/pronunciar.ts`/`.html` (notifica
inicio/resultado/error incluida la rama bloqueada; registra `contexto()`
en el Tutorial; "Volver al libro"→"Continuar leyendo" contextual;
`+data-tutorial`). **Sin tocar:** `spotlight.ts` (cero mecanismo nuevo:
reutiliza `opciones`/`objetivo`/`silencioso`/`avisoTransitorio` tal cual),
`libro.ts`, `app/*.py`, geometría/materiales/animaciones de la boca 3D.

**Flujo:** checkpoint `lector-inicio` → resuelve a `lector-palabra` solo
cuando el router está REALMENTE en `/leer/` → selección de cualquier
palabra con hoja local utilizable → `lexico-abierto` → clic real en "Leer
esta frase en voz alta" (ahora con libro/cap) → `pronunciar-grabar` →
grabar+Corrígeme → `pronunciar-resultado` → "Continuar leyendo" (si
coincide con el libro/capítulo de origen) → checkpoint
`post-lectura-inicio`. Ninguna rama llama `completar()`.

**Evidencia de los criterios de salida:**
- La hoja local (etapa `diccionario`) notifica solo si trae `sentido`,
  `acepciones_principales` o IPA; una respuesta vacía no avanza, la UI
  sigue mostrando "no está en el diccionario" sin que el tutorial se mueva.
- La posición se guarda de golpe (`escribirPosicion`, reutilizado, no
  duplicado) antes de navegar a Pronunciar: probado el caso de navegar
  antes de que pasen los 300 ms del guardado normal.
- Los ocho casos de error de Pronunciar (permiso, sin mic, sin soporte,
  grabación vacía, Corrígeme tarda, límite horario, bloqueada, red) se
  reducen a dos familias ya manejadas por la app; ninguno bloquea "Continuar
  leyendo" ni Saltar.
- "Continuar leyendo" solo cuenta como éxito del flujo si el
  libro/capítulo coincide con el origen registrado; volver a OTRO libro no
  bloquea la navegación pero tampoco avanza el tutorial (probado con un
  libro distinto).
- Sin contexto (Pronunciar abierto desde otro sitio), cualquier `/leer/`
  vale, como en D1.3, y "Volver al libro" genérico sigue funcionando igual.
- `post-lectura-inicio` sobrevive un refresh simulado, `activo()` sigue
  `true`.
- Suite completa: 35/35 archivos, 244/244 pruebas (34 nuevas: 15 en
  `lector.tutorial.spec.ts`/`pronunciar.tutorial.spec.ts`, 14 en
  `tutorial.spec.ts`, 5 en `spotlight.spec.ts`).
- Dos pruebas de D1.3 actualizadas (no nuevas): asumían que la cadena se
  detenía en `libro-ficha`→`lector-inicio`; ahora avanzan hasta
  `lector-palabra`, porque D1.4 le da comportamiento real a ese checkpoint
  (mismo patrón que el ajuste de D1.2→D1.3 con `encontrar-inicio`).

**Nota de datos reales (sin cambiar comportamiento, solo constancia):** los
ensayos completos de D1.4 (grabar + Corrígeme de verdad) consumen cupo real
de la cuenta usada y quedan en el historial de voz y en "Mis palabras",
igual que si se hiciera fuera del tutorial. **Los ensayos completos de
D1.4 consumen cupo real de Corrígeme; evitar repeticiones innecesarias.**

### D1.5 — Cierre (Mi espacio)

**Status:** ✅ PASSED

**Commit:** `5fc0717` en `dev/onboarding-v2` (sobre `ce06e27` de D1.4).

**Archivos modificados:** `front/src/app/nucleo/tutorial.ts` (2 pasos:
`cierre-palabras`→`tutorial-final`; `accion: 'terminar'` en `OpcionPaso`/
`elegir()`, única vía de toda la app que llama `completar()`; una línea
más en el watcher de router ya existente), `front/src/app/compartido/spotlight.ts`
(cambio trivial y localizado: `PasoTutorial.sinSaltar` oculta "Saltar" y
desactiva Escape solo en `tutorial-final`). **Sin tocar:** `palabras.ts`/
`.html`, `encontrar.ts`, `lector.ts`, `pronunciar.ts`, `app/*.py`.

**Flujo:** checkpoint `post-lectura-inicio` (D1.4) → resuelve a
`cierre-palabras` cuando el router está REALMENTE en `/leer/` → botón
propio del tutorial "Ver mis palabras" (sin `siguienteId`: solo avanza
cuando el router confirma `NavigationEnd` en `/palabras`) → `tutorial-final`
→ botón propio "Terminar tutorial" → `completar()`, sin navegar, se queda
en `/palabras`. D1.5 es el único tramo de D1 autorizado a completar.

**Evidencia de los criterios de salida:**
- `post-lectura-inicio` solo resuelve con el router realmente en `/leer/`
  (probado que otra ruta no produce avance falso).
- "Ver mis palabras" no avanza al pulsar, solo tras confirmarse
  `NavigationEnd` en `/palabras` — probado el hueco entre clic y
  navegación real.
- Navegación manual a `/palabras` (sin el botón del tutorial) avanza el
  paso pero nunca completa — solo `accion: 'terminar'` lo hace.
- Usuario anónimo y usuario con sesión llegan igual al cierre; ninguna
  prueba de D1.5 depende del contenido de `/palabras` (0 palabras
  incluido).
- `completado` persiste tras refresh simulado, no se reactiva solo, y
  `Repetir tutorial` reinicia correctamente saltando `cuenta-eleccion`
  con sesión y `nivel-inicio` con perfil ya medido — sin tocar D1.1-D1.4,
  ningún bug real encontrado.
- Copy verificado sin prometer una palabra concreta ("no está garantizado
  que se haya guardado").
- Suite completa: 35/35 archivos, 261/261 pruebas (25 nuevas en
  `tutorial.spec.ts`, 9 en `spotlight.spec.ts`).

**Nota de proceso:** en esta ronda aparecieron 3 errores de consola más
(6 en total) por el mismo límite preexistente de jsdom (`scrollTo` no
implementado en `lector.ts`), ahora también visibles en
`boca3d/sonador.spec.ts` por una diferencia de orden/interleaving de
Vitest entre archivos — no son fallos nuevos (0 tests fallando, mismo
origen que los 3 ya conocidos desde D1.1), pero vale la pena que quien
retome D2/D3 lo sepa si vuelve a aparecer.

---

### D1.V — Verificación humana del onboarding completo

**Status:** ✅ PASSED

D1.V intento 1 inválido: se probó Bienvenida v1.
Activación de desarrollo corregida para nueva prueba humana.

`?tutorialv2=on` solo encendía el flag de desarrollo (`activarDesarrollo()`)
sin llamar `iniciar()` ni restaurar un progreso activo; sin un «Repetir
tutorial» manual en Ajustes, `tutorial.activo()` nunca pasaba a verdadero.
La grabación de Miguel mostró únicamente Bienvenida v1 (`bienvenida.ts`,
tarjetas "1 de 4"/"Una palabra, en su frase"/"¿Por dónde empiezas?"),
diagnóstico confirmado por texto exacto y por `bienvenida.spec.ts`. D1.1-D1.5
no llegaron a probarse.

**Corrección (commit `dd9c902` en `dev/onboarding-v2`, sobre `5fc0717`):**
`activarDesarrollo()` ahora decide qué hacer con el progreso guardado (sin
progreso, o corrupto/versión incompatible/pasoId retirado → arranca solo;
`activo` → retoma el pasoId; `completado`/`saltado` → no reinicia, sigue
haciendo falta «Repetir tutorial»). Solo `front/src/app/nucleo/tutorial.ts`
tocado; sin cambios de copy, pasos, spotlight, navegación, 2D/3D ni backend.
Suite completa: 35/35 archivos, 271/271 pruebas (8 nuevas en
`tutorial.spec.ts`, 1 en `spotlight.spec.ts`).

**Intento 2 — prueba humana real, hallazgos de UX (commit `8f2e51e` en
`dev/onboarding-v2`, sobre `dd9c902`):** Miguel completó el recorrido con la
activación ya corregida. Tres correcciones de UX aplicadas:
1. `pronunciar-grabar` instruía a pulsar «Corrígeme» aunque la app ya supiera
   que la corrección estaba bloqueada (sin cuenta/perfil, sin OpenAI). Ahora
   `pronunciar.ts` notifica reactivamente al tutorial (`notificarDisponibilidadCorregir`,
   `notificarGrabacionLista`) y el paso se adapta: disponible → «Grábate» →
   «Pide tu corrección»; bloqueada → «Grábate para escucharte» → señala
   «Continuar leyendo»; error (micrófono/backend/429/bloqueo manual) también
   redirige ahí en vez de dejar al usuario atascado.
2. Nuevo target `data-tutorial="pronunciar-continuar"` en el CTA real
   «Continuar leyendo»/«Volver al libro»; `pronunciar-resultado` también
   apunta ahí ahora.
3. Copy recortado en `cuenta-eleccion`, `pronunciar-resultado` y
   `cierre-palabras` (una tarjeta, una acción, una razón breve).

Archivos: `tutorial.ts`, `pronunciar.ts`, `pronunciar.html` + tests. Sin
tocar: pasos/copy de cuestionario, ficha, léxico o resultados reales;
`spotlight.ts`; navegación; 2D/3D; backend. Suite completa: 35/35 archivos,
274/274 pruebas.

**Feedback confirmado por vídeo, registrado para D4 (NO implementado
todavía):**
- 2D: aumentar velocidad por defecto ~25–30 %; conservar modo Despacio.
- 3D: mucho margen de mejora pedagógica — modelo mayor/menos espacio vacío,
  lengua más clara y protagonista, menos apariencia tubular, evitar que
  dientes/encía oculten la lengua, vistas pedagógicas y encuadre por
  fonema, claridad > realismo.

**Intento 3 — aprobación final:** Miguel repitió D1.V con estas correcciones
y confirmó, con evidencia humana real: recorrido anónimo completo funcional;
Pronunciar ya no produjo una corrección cuando no estaba disponible; el
usuario no quedó atrapado en ningún punto; «Continuar leyendo» funcionó y,
al volver, se llegó correctamente al mismo libro y a la posición donde se
estaba leyendo. **D1.V → ✅ PASSED.**

**D1 → ✅ COMPLETE.** El onboarding guiado (D1.1-D1.5, con las correcciones
de activación y UX de D1.V) queda cerrado como experiencia, verificado por
prueba humana. Sigue detrás del flag de desarrollo (`?tutorialv2=on` /
`literalevel.tutorial-dev`); no hay cambio de comportamiento para un usuario
normal hasta que Miguel decida el corte a producción. HEAD de cierre en
`dev/onboarding-v2`: `8f2e51e`, `master` intacto en `004eb28`.

D2, D3 y D4 quedan pendientes de que Miguel los pida; no se empiezan
automáticamente tras este cierre.

---

### H1 — Higiene de tests: ruido de `el.scrollTo is not a function`

**Status:** ✅ PASSED

**Causa raíz:** el `effect()` de `lector.ts` que reacciona a `paginado()`/
`prefs.letra()` programaba `setTimeout(() => this.recolocar(), 30)` sin
guardar su id, a diferencia de los otros tres temporizadores del componente
(`espera`, `reloj`, `relojPosicion`), que sí se limpian en `ngOnDestroy`. Un
componente destruido antes de esos 30 ms dejaba el timeout vivo; al
disparar, llamaba `recolocar()` → `aplicarPagina()` → `el.scrollTo()` sobre
un `nativeElement` ya fuera de uso, y jsdom no implementa `scrollTo` en
elementos genéricos (solo en `Window`, donde emite un aviso en vez de
lanzar). Fuga de temporizador real, no una limitación de jsdom ni un
problema de los tests.

**Corrección (commit `2cd01a8` en `dev/onboarding-v2`, sobre `8f2e51e`):**
mismo patrón que los otros tres — nuevo campo `relojRecolocar`, guardado al
programar el timeout y limpiado en `ngOnDestroy`. Solo
`front/src/app/pantallas/lector.ts` tocado; sin tests nuevos (el fallo ya
lo reproducía `lector.ayuda.spec.ts` sin cambios). Sin cambio de
comportamiento en producción: solo deja de ejecutarse trabajo sobre un
componente ya destruido, que nunca debía correr.

**Verificación:** `lector.ayuda.spec.ts` aislado, 0 excepciones (antes 3);
`lector*.spec.ts`, 11/11 sin excepciones; suite completa, 35/35 archivos,
274/274 pruebas, **0 errores** (antes 6 `Uncaught Exception`). Quedan avisos
benignos de consola («Not implemented: Window's scrollTo() method»,
«HTMLCanvasElement's getContext()»): son `console.error` de jsdom sin
lanzar excepción, preexistentes y ajenos a este bug.

---

## D2 — Navegación + Continuar leyendo

**Status:** ✅ PASSED

Diseño aprobado por Miguel con correcciones: D2 fue hardening, no
reconstrucción — la inspección de la ronda de diseño mostró que "Continuar
leyendo" ya existía y estaba bien repartido (Inicio, `LeerEntrada`,
Pronunciar D1.4), todos reutilizando la misma fuente canónica
(`biblioteca.json` por `X-Lector`, servida al front como
`sesion.inicio()?.seguir`). Trabajado en `dev/navigation-v2`, creado desde
el checkpoint `2cd01a8` de `dev/onboarding-v2` (D1+H1), no desde `master`.

**Contrato confirmado (sin cambios de arquitectura):**
- Canónico: `biblioteca.json` por `X-Lector`, actualizado exclusivamente
  por `PUT /api/libros/:id/progreso` (única llamada en todo el front,
  desde `lector.ts` al abrir un capítulo real — nunca desde ficha ni
  búsqueda).
- Cache del front: `sesion.inicio()?.seguir`, no canónica, requiere
  refetch explícito (`sesion.refrescar()`), ya disparado en los puntos
  correctos (arranque, Inicio, `LeerEntrada`, tras cada PUT progreso).
- Posición dentro del capítulo: `literalevel.pos.<id>.<cap>`, solo
  `localStorage`, complementaria (no redundante) a `avance` del backend.
- **`X-Lector` no tiene relación con la cuenta/login** — la estantería NO
  sincroniza entre dispositivos aunque haya cuenta. Ningún copy debe
  prometerlo.
- Estado "Terminado" explícitamente NO implementado: `avance ≥ 0,98` o
  último capítulo no demuestra finalización real (un libro de 1 capítulo
  tiene `avance = 1.0` por construcción desde la primera página). Registrado
  para D3/posterior: requiere un evento explícito de fin de lectura.

**Cobertura añadida (commit `[pendiente]` en `dev/navigation-v2`):** 23
tests nuevos/extendidos — `inicio.spec.ts` (4, nuevo), `leer-entrada.spec.ts`
(4, nuevo), `lector.progreso.spec.ts` (6, nuevo), `pronunciar.tutorial.spec.ts`
(+2, prioridad de contexto explícito sobre el fallback a `seguir`). Sin
tocar D1 (`tutorial.ts`/`spotlight.ts`), sin mover Mis libros, sin nueva
tarjeta ni botón de nav.

**Bug real reproducido y corregido (mismo commit):** un test con
temporizadores reales (`lector.progreso.spec.ts`) reprodujo una fuga
distinta a la de H1: el doble `requestAnimationFrame` de `cargar()` que
llama `restaurarPosicion()` no se invalidaba en `ngOnDestroy()` (a
diferencia de los `setTimeout` ya cubiertos), así que un componente
destruido antes de que ambos rAF resolvieran seguía llamando
`aplicarPagina()` → `el.scrollTo()` sobre un elemento ya sin uso. Corregido
incrementando `this.carga` en `ngOnDestroy()`, invalidando de una vez todos
los `token === this.carga` pendientes (el mismo mecanismo que ya usaba
`cargar()` para sus propias condiciones de carrera). Sin cambio de
comportamiento en producción.

**Verificación final:** suite completa, 38/38 archivos, **290/290 pruebas**,
0 errores. Ningún test de D1 roto.

**Feedback visual/UX adicional (Miguel, 18 sep), registrado sin
implementar — D2 sigue ✅ PASSED, esto es un refinamiento pendiente sobre
Pronunciar, no una reapertura de D2:** en móvil, el CTA contextual
"Continuar leyendo" de `pronunciar.html` (D1.4, `data-tutorial=
"pronunciar-continuar"` desde D1.V) queda debajo de toda la zona IPA/
sonidos, y hace falta mucho scroll para encontrarlo. Propuesta a evaluar:
cuando exista `contexto()` `{libro, cap}`, repetir ese mismo CTA real (no
crear una segunda lógica de navegación — reutilizar el contexto de D1.4
tal cual) en la barra sticky de acciones (`.grabadora`, junto a "Otra vez"/
"Corrígeme"), visible durante grabación, error, resultado y exploración
IPA/2D/3D. Si Pronunciar no viene de un libro (`contexto()` null), el CTA
contextual no aparece — igual que hoy.

---

## D3 — Mi espacio + repaso interactivo

**Status:** ⬜ PENDING

**Feedback visual/UX adicional (Miguel, 18 sep), registrado sin
implementar:** la ficha de un libro de un solo capítulo no debe dibujar una
curva de dificultad falsa con un único punto. Cuando solo existe un score
global/capítulo, mostrar en su lugar una **comparación gráfica entre el
nivel del lector y la dificultad del libro** (p. ej. escala 0-2 con ambos
marcadores, o dos barras comparables) — usando únicamente datos ya
disponibles (`perfil.nivel` y la dificultad del libro/capítulo, ambos ya
servidos hoy). Si en el futuro existieran scores internos por segmentos del
capítulo, ahí sí un perfil interno más fino; no inferirlo ahora sin ese
dato. Relacionado con el diseño de D3 (sección de gráficas), pero es una
pantalla distinta (ficha del libro, `libro.ts`/`libro.curva.spec.ts`), no
Mi espacio — a evaluar si entra en D3 o queda como incremento propio.

---

## D4 — Visualización articulatoria v2

**Status:** ⬜ PENDING

**Feedback visual/UX adicional (Miguel, 18 sep), registrado sin
implementar:** hallazgo confirmado por Miguel — en `/b/`, los labios
deberían ser el articulador principal y la vista 3D actual apenas permite
verlos. D4 debe considerar vistas/encuadre específicos según el tipo de
fonema, no una cámara universal: bilabiales `/p b m/` → labios claramente
visibles, preferencia frontal/¾; dentales `/θ ð/` → lengua + dientes;
alveolares → punta de lengua + alveolos; velares → parte posterior de
lengua + velo. Principio explícito: "la cámara y la geometría visible
deben servir al sonido concreto. Claridad pedagógica > una vista 3D
universal."

Feedback de UX ya registrado en D1.V (2D: velocidad; 3D: mejora pedagógica
considerable) — pendiente de implementar cuando Miguel lo pida.

---

## D5 — Read-along MVP [STRETCH]

**Status:** ⬜ PENDING

Fuera del alcance de esta fase salvo que sobre tiempo tras D1-D4.

---

## Próximo paso

Esperar decisión de Miguel sobre el diseño de D1.1 (rama/worktree, y si el
nuevo tutorial convive con `Bienvenida` o la sustituye de una vez). No se
marca D1.1 como RUNNING hasta esa aprobación.
