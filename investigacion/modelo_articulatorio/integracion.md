# Propuesta de integración en `animacion.ts` (sin tocar la app)

**Estado:** propuesta. `app/` y `front/` no se tocan hasta que Miguel apruebe
el modelo (encargo, §4).

## Qué cambia y qué no

- **No cambia** el catálogo de poses ni `poseNumerica`: las 46 poses hechas a
  mano siguen siendo el vocabulario y la escala del rig.
- **Cambia la dinámica:** en lugar de dos claves por sonido (0,38–0,72 del
  tramo) con `suavizar`, la línea lleva una clave cada 40 ms con los valores
  que da el modelo. `mezclarPose` sigue interpolando entre claves igual que
  hoy.
- **Cambio mínimo en el contrato de pose:** un campo opcional
  `PoseSonido.continuo?: { mandibula?, largo_labio?, cierre_labios?,
  punta?: [alt, ade], cuerpo?: [alt, ade] }` que `poseNumerica` usa, si
  está, en vez de las categorías (`labios`, `punta`). Sin ese campo, todo
  funciona como ahora. Es la única línea de `escena.ts` que habría que tocar.

## Dos formatos de pesos, según el modelo que gane

| | Dominancia (Cohen-Massaro) | TCN |
|---|---|---|
| Pesos | 4 tablas fonema × control (T, α, θa, θc): **12,6 KB** en JSON con los 12 controles de vídeo (5,6 KB comprimido), medido con `exportar_modelo.py` | 86 380 parámetros: **0,35 MB** float32, 0,17 MB float16 |
| Cálculo | por fotograma, suma ponderada de los ~10 segmentos vecinos | una pasada por frase, antes de animar |
| Coste medido (JS puro, este PC con la CPU ocupada por el lote) | despreciable (< 0,01 ms/fotograma, estimado: 10 × 21 exponenciales) | **30 ms** una frase de 3 s (75 fotogramas); **121 ms** una de 10 s — `bench_tcn.mjs` |
| Dependencias | ninguna | ninguna (conv 1-D escrita a mano, ~60 líneas) |

En un móvil medio, 3–5 veces más lento: la TCN costaría ~0,1–0,6 s por frase
**una vez**, antes de empezar; no por fotograma. Encaja con cómo arranca hoy
`lineaFrase` (espera al audio del TTS).

## Tiempos de los fonemas

La app ya conoce la IPA de cada palabra y los tramos de voz del audio del TTS
(`lineaFrase`); reparte las duraciones con `DURACION_S` escaladas al tramo.
El modelo usa esos mismos tiempos: no hace falta alinear el audio del TTS.
**Riesgo sin medir:** el modelo se entrenó con tiempos de MFA sobre voz
humana; con tiempos de regla puede perder precisión. Se mide antes de
integrar (reentrenando con tiempos de regla simulados sobre GRID).

## Paso de las salidas al rig

`calibracion.json` (de `calibrar_rig.py`): por control, una recta de la
medida humana (z) al valor del rig, ajustada sobre los fonemas cuyas poses
hechas a mano no dejan el campo libre. Ejemplo medido en el piloto
(3 hablantes): mandíbula r = 0,71 entre fonemas; ancho → largo del labio
r = 0,67; apertura interior → `cierre_labios` r = −0,07. Esto último **no
es un fallo visible**: la cara didáctica publicada anula `cierre_labios` en
las vocales neutras articuladas (`abrir_neutro`), así que /ə ɪ eɪ ɛ/ ya se ven
abiertas (comprobado de frente el 25 sep). La discrepancia real estaba en la
mandíbula: /ɛ/ y /eɪ/ abrían casi como /ɪ/ y en las caras reales abren casi
como /ɑ/. Corregido con la recta medida→rig (0,67 y 0,70) en
`dev/articulacion-v2` (`b6a0a71`), sin publicar.

La lengua sale del modelo EMA (punta, lámina y dorso: altura y avance) y
entra por `continuo.punta` y `continuo.cuerpo`; velo, sonoridad y aire siguen
por regla.

## Orden propuesto

1. Miguel ve la hoja lado a lado (real contra modelo contra reglas) y decide.
2. Exportar el ganador (`exportar_modelo.py`; la dominancia ya sale en `resultados/final/modelo_dominancia_grid.json`) a
   `front/src/app/compartido/boca3d/modelo_articulatorio.json`.
3. `lineaModelo()` en `animacion.ts` detrás de una constante nueva
   (`MODELO_ARTICULATORIO_ACTIVO`, junto a `BOCA3D_ACTIVO` en
   `interruptor.ts`), con las mismas pruebas de `sincronia.spec.ts`.
