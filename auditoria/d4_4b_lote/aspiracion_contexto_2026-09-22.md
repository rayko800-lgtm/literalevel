# D4.4b — aspiración por contexto (y vista previa)

Sesión [ejecutora] (Opus 5.5), 22 sep 2026, sobre `770487e` (fase 3), por encargo de literalevel-6c.

## 1. El soplo solo donde toca

Antes (desde v4): en una palabra, **toda** /p t k/ soplaba. Ahora sopla (`seAspira` en `animacion.ts`) solo si:
- es oclusiva sorda,
- **no** va tras /s/ (spin, stop, sky: sin soplo),
- y se suelta hacia una vocal, un diptongo o /l ɹ w j/ (pin, play, try). Al final de palabra (hot) o ante otra
  consonante (act) no hay soplo.

Fuente: Ladefoged & Johnson (2011), *A Course in Phonetics*, cap. 3 (sordas aspiradas en inicio de sílaba, no
aspiradas tras /s/, y finales a menudo sin suelta audible); Cruttenden (2014). La investigación fonética (§1) solo
decía «inicio de sílaba tónica»: esta regla va más allá de ella, y lo digo. No exijo el acento: la /p/ átona de
paper también sopla (el 3D no distingue la aspiración débil). El ciclo de un sonido suelto no cambia (/p/ sola
sigue soltándose con soplo). La duración por lugar (fase 3) se mantiene.

Pruebas: la de v4 que esperaba 2 soplos en «pat» pasa a 1 (la /t/ final ya no sopla); una nueva recorre pin, play,
try y kin (sí), spin, sky, hot, big y act (no), stop (ninguna), paper (las dos /p/) y cat (solo /k/).
Boca3d **123/123** (8 archivos), front **420/420** (46), `tsc` de la app y de las pruebas sin errores, `ng build`
OK. Sin cambios de pose: `lengua.py`, el hidrostato y la banda no se vuelven a pasar (no hay nada nuevo que medir).

## 2. Vista previa para Miguel: NO abierta

Build de producción hecho y servido en local con la API en solo GET (`ej_servir.mjs`, rechaza cualquier otro
método con 405). A 390 px, los 13 fonemas pedidos (/p b t d k ɡ s θ ð ɹ l ɑ/ en US y /ɒ/ en UK) abren «Boca en 3D»
en modo 3d: **13/13**, sin errores de página y sin desbordar el ancho (390 px).

**El túnel público no se abrió**: el clasificador de permisos de esta sesión lo bloquea como «túnel de entrada
externo». No lo esquivo. Hace falta que Miguel lo autorice en esta sesión (o que lo abra quien tenga el permiso).
El servidor local está parado; la compilación está en `D:\Temp\ej_b_prev` para servirla en cuanto haya permiso.

## 3. SSB moderno

Plan (sin aplicar) en `auditoria/d4_4b_lote/ssb_moderno.md`.
