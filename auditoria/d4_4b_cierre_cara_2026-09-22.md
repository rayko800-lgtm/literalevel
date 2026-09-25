# D4.4b — cierre de cara (apertura de mandíbula y ojos)

Hecho por la sesión [ejecutora] (Fable 5.1) el 22 sep 2026 sobre `dev/articulacion-v2` @ `d09446f` (v7), por
encargo de e6 con los dos ajustes aprobados por Miguel. Todo lo de aquí está medido en esta sesión. No cambian
el 2D, `animacion_articulatoria.py`, los timings del ciclo, el audio, master, catálogo ni cuentas.

## 1. Los dos ajustes

**MAND_MAX 0,42 → 0,21 rad** (mandíbula = 1), el mismo valor en los tres sitios donde vivía el 0,42:
`escena.ts` (giro de la mandíbula, k del labio, rebote), `cara.py` (clave `cierre_labios`, calculada para el
giro de reposo, y la banda labios-dientes) y `lengua.py` (comprobación del techo y de la punta interdental).
k = 1 en las vocales se conserva (se siguen viendo los dientes de abajo). Además la subida del labio de arriba
en `estirar` baja de 0,50 a 0,40: en /æ/ (estirados + mandíbula 1) sumaba ~8 mm fijos que no escalan con el
ángulo y con 0,50 /æ/ daba 33,4 mm a 0,23 y 30,8 a 0,22.

**Ojos cerrados**: las tres llamadas de `cabeza_escaneada` (`ranura_parpados_bm`, `abrir_parpados`,
`ojos_lps`) quedan sin llamar; el escaneo trae los párpados cerrados y en el corte de perfil el ojo no entra.
`cara.glb` 2 162 772 → **2 130 576 B** (límite 2 188 394).

## 2. Aberturas interlabiales (demo, `medir_labios2.mjs`, IO = 2,71 u = 63 mm)

| Pose (mandíbula) | v7 (0,42) | **cierre (0,21)** | Miguel |
|---|---:|---:|---|
| reposo (0,2) / /p/ (0,08) / /m/ | 0,5 / 0,3 / 0,5 mm | 0,5 / 0,3 / 0,5 mm | ≈0 / sello |
| /æ/ (1,0; estirados) | 52,7 | **29,8** | máximo ≈24–30 |
| /ɑ/ = /aʊ/ (0,92) | 40,5 | **20,8** | ≈24 (/aʊ/) |
| /ʌ/ (0,58) | ≈ 30 | **13,4** | típica 8–14 |
| /ɛ/ (0,42) | ≈ 22 | **8,1** | típica 8–14 |
| /ɪ/ (0,26) | ≈ 8 | **1,4** | — |
| /i/ (0,12; estirados) | 11,2 | **8,8**, anchura +32,7 % | +33 %, incisivos a la vista |
| /u/ (0,12; redondeados) | 5,2 | **4,3** de orificio, anchura −32,2 % | −30..−45 % |
| liberación /p/ → /æ/ | 28,7 mm a 94 ms | **12,5 mm a 73 ms** | 0 → ≈10 mm en ≤ 67 ms |
| rebote del ciclo /p/ → reposo | 20,4 mm a 74 ms | **9,7 mm a 69 ms, 15,2 a 134, sellado a 378 ms** | — |

Con 0,23 /æ/ daba 33,4 y con 0,22 30,8 (subida 0,40); 0,21 es el primer valor dentro de la banda; /ɛ/ queda
en el borde bajo (8,1) porque las vocales sin `estirar` solo abren por el ángulo.

## 3. La lengua con la mandíbula de 0,21 (`lengua.py`, 53 poses)

- **Techo 53/53 con exceso 0, pliegue 0, roce −0,039** (la holgura de siempre); hidrostato 13/13 en
  `comprobar_modelos.mjs`; banda labios-dientes de `cara.py` 20/20 sin intersecciones nuevas.
- **/θ ð/ — mandíbula 0,36 → 0,6 en `poses.ejemplo.json` (decisión de e6/Miguel, opción 2).** Con 0,36 y
  0,21 rad el hueco entre bordes incisales era 0,54 u (12 mm) y la punta aprobada mide 0,64 (15 mm): no cabía
  (con `INTERDENTAL_ALZA` 1,25 subía a y 0,63 > 0,45; con 0,88–0,93 se hundía 0,037 en las coronas de abajo).
  Con 0,6 el hueco es 0,78 u, la alza aprobada (1,25) se conserva y la punta queda a y 0,09..0,42, frente
  x −2,96, roce −0,039. Lectura a 390 px (`comparativa_v7_cierre.png`, `hoja_lectura_390.png`): la punta sigue asomando entre los dientes, gruesa y redondeada, distinta de /s/ (detrás de la cresta) y de /t/ (arriba, cerrada); la boca abre algo más (≈12 mm entre labios) sin parecer un bostezo. **Se mantiene la opción 2**; no hizo falta el tope propio (opción 1).
- **/tʃ dʒ/ — `punta_arriba` con toque 1,0 → 0,85** (mismo valor en `lengua.py`, `escena.ts` y
  `medir_lengua.mjs`): la suma punta_arriba + cuerpo_alto entraba 0,155 en el paladar (toque permitido 0,08);
  con 0,42 la mandíbula bajaba la lengua 0,28 y lo escondía. Lectura a 390 px: el contacto postalveolar se sigue viendo (la punta sube y apoya en la zona detrás de la cresta), no queda flotando.
- **Dorso sin toque ×0,9** (mismos tres sitios): /w/ entraba 0,013 en el velo. Afecta a /w l ɝ ɚ/ (un 10 %
  del dorso): **hay que mirarlos cuando les toque en el lote** (la /ɹ/ y la /l/ oscura están en su lista).
- Familias comprobadas sin tocar: /s t n d/ (t/d holgura −0,08 respecto al techo, roce −0,16), velares /k ɡ ŋ/
  (volumen +7,4 %, roce −0,177), /p b m f/.

## 4. Comprobaciones visuales que pidió e6 (a 390 px, `hoja_lectura_390.png` en el scratchpad y
`comparativa_v7_cierre.png`)

- /ɪ/ 1,4 mm y /u/ 4,3 mm: /u/ se lee redondeada, con el orificio y la mucosa oscura; /ɪ/ se lee como labios apenas separados (una línea oscura entre ellos), no como boca cerrada, pero es la más justa de todas: si en el lote se quiere más margen, /ɪ/ está en mandíbula 0,26.
- /i/ 8,8 mm con +32,7 % de anchura (medido con el borde real de la ranura): sí, y los incisivos superiores siguen a la vista.

## 5. Rendimiento y pruebas

`medir_fps.mjs`, SwiftShader, 6 s, CPU ×4 / ×1, tres rondas alternas base | v7 | cierre, medianas
(`fps_rondas.txt`):

| | base `8bd4a66` | v7 `d09446f` | **cierre** |
|---|---:|---:|---:|
| preset bilabial | 13,6 / 14,3 | 14,3 / 13,6 | **14,7 / 15,2** (+8 % / +6 % sobre la base) |
| vista por defecto | 7,9 / 7,9 | 12,2 / 13,9 | **12,6 / 13,7** |

Pruebas: boca3d focalizadas 119/119 (8 archivos), front 416/416 (46), `lengua.py` 53/53 (exceso 0, pliegue 0, roce −0,039), banda labios-dientes 20/20, `comprobar_modelos.mjs` OK con hidrostato 13/13. Una prueba cambia con el dato: `v4.spec.ts` fijaba «/θ/ semiabierta cierra a medias» (mandíbula 0,36); ahora /θ/ (0,6) no cierra y el caso «a medias» lo hace /ɜː/ (0,36). `tsc` sin diagnósticos; `ng build` OK.

## 6. Evidencia (`build/d4_4b_cierre_cara/`)

- `recuadro_aberturas_mm.png`: recuadro real de la app (reloj controlado) en reposo, cierre y liberación de
  /p/, y la demo de frente en /æ ɛ u i/, cada uno con su abertura en mm.
- `comparativa_v7_cierre.png`: /p b m θ k t s n/ al abrir «Boca en 3D», v7 y cierre.
- `tira_p.png`, `tira_b.png`, `tira_m.png`: 8 fotogramas en tiempos exactos del ciclo, v7 arriba, cierre abajo.
- `cabeza_cierre_tres_cuartos_y_perfil.png`: ¾, de frente, el corte del alumno y /æ/ en el corte de cerca.
- `fps_rondas.txt`, `componer.py`.

## 7. Queda anotado

- /w l ɝ ɚ/: dorso un 10 % más bajo; revisar en el lote.
- /ɛ/ 8,1 mm en el borde bajo de la banda (las vocales neutras solo abren por el ángulo).
- La exportación del GLB de la cara no es byte-determinista (±2,5 KB; §4 del informe de v7).
- fps en teléfono y guard 534 [SIN MEDIR].
