# Piloto Astra — 23 sep 2026, Nico

## CONFIRMADO

Referencia personal autorizada revisada localmente. Presupuesto cero. No se
incorporan fotogramas ni textura personal al repositorio o a la vista pública.
Estado base dev/articulacion-v2, HEAD0421f0d; `front/angular.json` es ajeno.

- Piel morena cálida mediante reflectancia, conservando reflejos; labio superior
  más oscuro, detalle labial que sigue la deformación y microrelieve superficial.
  El color es aproximado: la iluminación fuerte del video impide calibrarlo.
- Coronación dental v3: domo vestibular, cuello ovoide, esmalte marfil y margen
  gingival. 960 puntos de la banda incisal intactos. Premolares2/9 visibles en
  exterior y atenuación del fondo dental. Brillo reducido para leer las formas.
  Normales suaves sólo en remates triangulares de caninos03/08.
- Lengua: difusión de las correcciones discontinuas de `mandibula`/`cuerpo_bajo`.
  Desaparece el escalón anterior en /æ/; topología, UV y10 morfos conservados.

## VALIDADO

- 135 pruebas Boca3D (9 archivos), TypeScript y build de producción correctos.
  Build final advierte budget CSS `pronunciar.css`12.64kB frente12kB, preexistente.
- 2227 estados con cara v3 y lengua nueva: penetración medida0; cierre.0000513077;
  /fv/ central.00202444/lateral.00540100, ambos bajo.008; liberación.71836269.
  Costura52 vértices/error0; sección áreaerror.000681600 bajo.001,0 estados fuera;
  plegado superior.001451612 bajo.015. `build/astra-medidas.json` y `.log`.
- Corrección final de normales posterior al barrido: comparación del GLB con
  `comprobar_normales_astra.mjs` del workspace verifica mismas posiciones,
  triángulos, morfos y transformaciones en86 mallas. No cambia el barrido.
- Lengua aislada:54/54 poses de volumen/espesor y260 estados contra techo/dientes;
  no regresiones fuera de tolerancia; contacto interdental permitido máximo.04948
  frente.08. Holgura mínima /æ/.0053. Ver `build/lengua_realista/NOTAS.md`.
- Inspección navegador móvil390×844: /i æ ɑ u f/ frontal; /θ t k/ lateral y
  animación. Sin errores WebGL; clientWidth=scrollWidth375. No benchmark actual
  de teléfono/FPS: el navegador no expone el reloj en su evaluación restringida.
- Dos GLB públicos con SHA256 idéntico al local. Ruta privada denegada404 en
  servidor; cinco archivos permitidos explícitamente. Aproximadamente3.90MB gzip.

## ARTEFACTOS

`build/boca_didactica/cara.glb`:6033132B,
SHA256 FBD6C1C31AADFCCE84D8C876DB1C8F6C5FCAC2EC6F0ADE77753AE2E4F28C5DB2.
`build/lengua_realista/lengua.glb`:444212B,
SHA256451CEEA3BE66B4DA43CE1D38B837AB91A77D2413FC39FB738E5D05E982611F64.
Blender: cara.blend12761596B; lengua.blend1323952B.

Fuentes: `dientes_realistas.py`, `lengua_realista.py`, `cara_didactica.py` y
`escena.ts`. Medidor admite `--lengua=build/lengua_realista/lengua.glb`.
Exportar con Blender2.93 `-b --python tools/boca3d_blender/cara_didactica.py` y
`-b --python tools/boca3d_blender/lengua_realista.py`. Capturas y respaldo anterior
en workspace de Nico `evidencia-blender/astra-*` y `respaldo-antes-astra/`.

## TEMPORAL / NO INTEGRADO

Vista: https://city-gabriel-tier-nickel.trycloudflare.com/?didactica=1&inventario=1&s=i&ciclo=0&sombras=0&vista=frente&velocidad=0.5
Hasta aproximadamente23:02CDMX del23sep. Puerto8771, servidor exec79767;
túnel exec2150 hijo49452. No producción/commit/push ni sustitución de los GLB
versionados. Validación geométrica no certifica todas las colisiones de triángulos
ni anatomía clínica. Aceptación visual del usuario pendiente.

## LÍMITES REALES

No se alcanzó fotorrealismo ni equivalencia GTA6. La parte visible de las coronas
es corta por la cobertura labial; el interior todavía es ilustrativo y la lengua
en /i/ mantiene una franja plana heredada. No alterar anclajes para arreglarlo sólo
con brillo. El siguiente salto exige revisar proporción/exposición dental y
deformación perioral con una comparación visual pequeña.

La piel/estrías y atenuación bucal se aplican en Three.js, no están horneadas al
.blend/PNG. Translucidez es aproximación local de iluminación, no SSS física.
Referencias técnicas: https://threejs.org/docs/pages/module-SubsurfaceScatteringShader.html
y https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
