# La boca en 3D esquemático (`app-boca3d`)

Un visor three.js de la boca por dentro, girable con el dedo, con las mismas
poses que el corte 2D de `app/animacion_articulatoria.py`. Es un prototipo en
la rama `boca3d`: **nadie lo importa todavía** y no hay ruta ni pantalla que lo
use. Este archivo dice cómo encajarlo cuando Miguel diga que sí.

## Qué hay en la carpeta

| Archivo | Qué es |
|---|---|
| `boca3d.ts` | El componente standalone `<app-boca3d>`. |
| `escena.ts` | La escena three.js sin Angular: piezas, poses numéricas, transiciones, líneas de tiempo, cámara. |
| `animacion.ts` | Las líneas de tiempo: ciclo de un sonido y palabra entera, con los tiempos del 2D. |
| `poses.ts` | El contrato de poses (`PoseSonido`, `CatalogoPoses`), las cinco embebidas del prototipo, `poseDe`, `resolver` y `trocearIpa`. |
| `poses.ejemplo.json` | Los 46 sonidos + 6 de RP exportados de `PARAMETROS`: lo que la API puede servir. |
| `boca3d.spec.ts` | Pruebas de poses, líneas de tiempo y del respaldo 2D en jsdom. |

Fuera de la carpeta: `tools/exportar_poses_boca3d.py` genera el JSON;
`tools/boca3d_demo.mjs` empaqueta una demo sin router (`tools/boca3d_demo/demo.ts`)
y `tools/boca3d_demo/medir_fps.mjs` mide los cuadros por segundo con la CPU frenada.

## Cómo se usa

```html
<!-- La ficha de un sonido de la tabla del AFI -->
<app-boca3d [sonido]="s.simbolo" [acento]="acento()" />

<!-- La corrección: el sonido que falla y la palabra entera -->
<app-boca3d [sonido]="d.fonema?.simbolo ?? ''" [acento]="d.fonema?.acento ?? 'ga'"
            [ipa]="d.ipa" [leyenda]="false" />
```

`sonido` y `acento` son **los mismos valores que ya van a `urlCorteSonido`**:
el símbolo tal como lo da la API en su inventario (`/api/fonemas`, RP incluido:
«iː», «ɑː», «uː», «r», «əʊ» caen en su pose) y `Acento` de `nucleo/api`.

| Input | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `sonido` | `string` | `''` | Símbolo IPA; vacío es el reposo. |
| `acento` | `Acento` | `'ga'` | `'ga'` o `'rp'`, el mismo que los SVG. |
| `ipa` | `string` | `''` | Transcripción de una palabra: aparece «Ver la palabra». |
| `catalogo` | `CatalogoPoses` | las 5 del prototipo | Las poses. Con el JSON de la API, todo el inventario. |
| `svg2dUrl` | `string \| null` | `null` | Respaldo sin WebGL. `null` = el SVG de la API del sonido (quieto con reduced-motion); `''` lo apaga. |
| `leyenda` | `boolean` | `true` | La frase de la pose bajo el visor. |
| `conSelector` | `boolean` | `false` | Chips para elegir sonido (demo y prototipo). |
| `autoReproducir` | `boolean` | `true` | Al cambiar `sonido`, reproduce reposo → sonido → reposo. |
| `mejilla` | `boolean` | `true` | La mejilla translúcida. Es lo que más cuesta sin GPU. |

Métodos públicos: `verMovimiento()`, `verPalabra()`, `restablecer()`,
`alternarGiro()`. Sin WebGL pinta el respaldo 2D; con `prefers-reduced-motion`
no interpola: salta a la pose (en la palabra, a la vocal acentuada).

### Dónde encajaría

1. **Corrección de pronunciar** (`pantallas/pronunciar.html`, el `<details class="boca">`
   «Ver cómo se mueve la boca»): junto a los dos `<img>` del corte, un botón
   **«Girar en 3D»** que muestra `<app-boca3d>` con el mismo `d.fonema.simbolo`,
   `d.fonema.acento` y `d.ipa`. El 2D sigue siendo lo que se ve por defecto; el
   3D se monta al pulsar (así three.js no se descarga hasta que hace falta:
   el componente va en un `@defer (on interaction)` o en un `@if`).
2. **Ficha de cada sonido** (la tabla del AFI, `elegido()`): el mismo botón bajo
   el corte 2D, con `s.simbolo` y el acento elegido.

Con `@defer` el chunk de three (unos 600 kB minificados) queda fuera del
paquete inicial y del presupuesto de `angular.json`.

## El contrato de poses (lo que la API puede servir)

`poses.ejemplo.json` sale de `tools/exportar_poses_boca3d.py` y **usa los
mismos nombres de campo que `Articulacion` en `app/animacion_articulatoria.py`**,
sin traducir: `movimiento`, `mandibula`, `labios`, `punta`, `punta_toca`,
`cuerpo` (`[altura, adelantamiento]`), `dorso_velo`, `dorso_alto`, `raiz`,
`velo_abierto`, `sonora`, `lugar`, `larga`, `leyenda`, `hacia`. Dos diferencias
a propósito:

- cada pose viene **ya resuelta contra el reposo** (`_resolver`): ningún campo
  es `null`; y
- lleva **`libres`**, la lista de los campos que `PARAMETROS` deja en `None`,
  para que el front los rellene con la vocal vecina en una palabra
  (`resolver` en `poses.ts`, como `_resolver` en el 2D).

Estructura: `{version, origen, escala, duracion_s, factor_lento, reposo,
sonidos: {símbolo: pose}, rp: {símbolo: pose}}`. `sonidos` está indexado por
la clave de `PARAMETROS` (símbolo GA) y `rp` por símbolo RP, igual que
`PARAMETROS_RP`. Una ruta como `GET /api/articulacion/poses.json` que devuelva
`exportar()` de ese guion (o lo mismo calculado en `api.py` con
`animacion_articulatoria._resolver`) es todo lo que el front necesita: se pasa
al input `catalogo` y el componente cubre el inventario entero. Hasta entonces
lleva embebidos el reposo y /p s i ɑ ŋ/.

`trocearIpa` en el front es una versión reducida de `trocear` del 2D (greedy
sobre el catálogo, marcas de acento a la vocal): si la API sirve la palabra ya
troceada (`[{simbolo, acento_silaba}]`), basta con poner a cada segmento su
pose con `poseDe` y dárselo a `lineaPalabra`.

## Rendimiento

`node tools/boca3d_demo/medir_fps.mjs build/boca3d_demo/index.html 4` mide en
Chrome headless con `Emulation.setCPUThrottlingRate` a 390 px. Headless dibuja
con SwiftShader (software), así que es una cota pesimista: 27 fps con mejilla y
50 sin ella sin freno; 25 y 37 con CPU ×4. El freno apenas cambia la cifra: el
coste está en el relleno de la lámina translúcida, no en JavaScript. En la demo
publicada, `?fps=1` mide en el dispositivo real.

## Límites conocidos

- Corte esquemático, no anatomía clínicamente validada. Los dientes, encías y
  velo siguen siendo piezas geométricas; no hay cara completa ni úvula.
- El lienzo captura solo el gesto horizontal (`touch-action: pan-y`); «Girar
  libremente» lo captura todo y sobre él no hay scroll.
- Hay trazas de aire nasal y de /h/, no simulación de fluidos ni cuerdas vocales.

## Muestra Blender, 13 sep 2026

La demo carga lengua y cara modeladas por defecto (`?lengua=0&cara=0` permite
comparar el respaldo geométrico). El componente Angular aún no carga estos
assets y sigue sin integrarse en las pantallas públicas. `EscenaBoca` recibe
`lenguaGlb` y `caraGlb` como URLs opcionales; conserva el respaldo geométrico
si un archivo falta o no contiene las piezas esperadas.

- `tools/boca3d_blender/lengua.py`: lengua con diez shape keys, exportada a
  `tools/boca3d_demo/lengua.glb`.
- `tools/boca3d_blender/cara.py`: labios afinados, perfil de nariz, techo nasal,
  faringe, garganta y suelo de boca biselado, exportados a `cara.glb` (187.496 bytes).
  Los labios se escalan con las poses existentes; no tienen un rig facial completo.
- Las piezas se cargan en sus grupos: labio inferior y suelo siguen la mandíbula.
  El encuadre deja margen para el perfil al girarlo.
- La comprobación de lengua replica ahora el factor 0,3 del morfo mandibular y
  el giro de la escena. Antes medía otra transformación. Se comprueban 53 poses
  estáticas contra un techo aproximado y una heurística de pliegue, no todas
  las intersecciones posibles ni la corrección anatómica de cada pose.

Pruebas locales reproducibles:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 2.93/blender.exe' -b --python tools/boca3d_blender/lengua.py
& 'C:/Program Files/Blender Foundation/Blender 2.93/blender.exe' -b --python tools/boca3d_blender/cara.py
node tools/boca3d_demo.mjs
$env:PLAYWRIGHT_MODULE='ruta/al/playwright-core/index.mjs'
node tools/boca3d_demo/probar_blender.mjs
node tools/boca3d_demo/servir.mjs
```

`probar_blender.mjs` levanta y cierra un servidor local y un Chrome propio. Genera
24 capturas a 1280 y 390 px (con tacto móvil), comprueba píxeles no vacíos,
encuadre sin corte, movimiento real de /h/, carga/fallo del GLB y la posición
mundial de la punta en /θ/. Resultados en `build/boca3d_pruebas/`, no versionados.
`servir.mjs` publica solo en 127.0.0.1, elige un puerto libre e imprime URL/PID.
