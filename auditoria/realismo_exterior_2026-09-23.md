# Exterior más realista — 23 septiembre 2026

## CONFIRMADO

Miguel aprobó anatomía y autorizó avanzar hacia fotorrealismo. Este piloto mejora el exterior; **no alcanza fotorrealismo completo**. Rama `dev/articulacion-v2`, base `0421f0d243dbf6c611f918f1c286d7f212344d2c`.

Superficie del escaneo Lee Perry-Smith unida a los labios funcionales aprobados: nariz, mejillas y mentón con volumen humano; corrección de alineación, UV, continuidad medial y curvatura por gesto. Normales calculadas sobre el gesto deformado. Textura afeitada derivada con image_gen: 1254 × 1254, fuente CC BY 3.0 Lee Perry-Smith / Infinite Realities, atribución conservada. Archivo y prompt exacto: `tools/boca3d_blender/texturas/README.md`.

Implementación: nuevo `apariencia_escaneo.py`, `perioral_didactico.py`, `cara_didactica.py`, textura y `front/src/app/compartido/boca3d/escena.ts`. Generación aislada con Blender 2.93: `-b --python tools/boca3d_blender/cara_didactica.py`. No usar los generadores de producción para regenerar este piloto. Catálogo46+7, Frente/Lado explícitos; sin audio. Interior no reesculpido en esta etapa.

## VERIFICADO

- 133/133 pruebas Boca3D, TypeScript y build correctos. Advertencia CSS previa de +639B. Prueba nueva: normales deformadas a través de costuras UV y reutilización del buffer.
- Barrido final GLB/runtime de 2227 estados: penetración detectada de vértices labiales en coronas convexas0; error de cierre0.000007391; contacto /f v/ central0.00202444 y lateral0.00540100; liberación /p b/1.03087945. Unidades del modelo.
- Costura33 vértices/error0. Discrepancia máxima de área de sección0.000706768, tolerancia ilustrativa0.001; ningún estado fuera. No certifica todas las intersecciones de triángulos ni exactitud clínica.
- Inspección pública /i f u/ y corte /k/. Viewport390×844 sin desbordamiento (ancho cliente/documento375). 58.2 callbacks rAF/s durante4s: escritorio emulando tamaño móvil, no teléfono físico ni benchmark GPU. Consola final limpia. Hash público igual al local.
- Revisor independiente de capturas /i u/ acepta entregar como exterior más realista. Capturas finales del workspace: `evidencia-blender/realismo-{i,u,f}-final.png` y `realismo-k-corte.png`.

## ARTEFACTOS

`build/boca_didactica/cara.glb`: 4861268B, SHA256 `12CAB36C2A82517A922FD7DC075C82CFE923D3EC4E25163F28621B8E0DAD1CA7`. `cara.blend`:9594008B. Métricas: `realismo-medidas.json`, `secciones-medidas.json`.

Respaldo exacto anterior: `build/boca_didactica/aprobado_anatomia/`, GLB SHA256 `FC17D5DEC7101CCDB8E6C9326D272252CDD3434523995F5E2441B6AC2E96B4B2`.

## TEMPORAL

https://apr-button-profits-scsi.trycloudflare.com/?didactica=1&inventario=1&s=i&ciclo=0&sombras=0&vista=frente&velocidad=0.5

Hasta~19:37 CDMX del23sep. Cinco assets permitidos,3532479B comprimidos. Servidor8769 exec86769, túnel exec38976/hijo47808. Assets en memoria: reconstruir `build_blender_preview.mjs` requiere reiniciar únicamente ese servidor identificado. El anterior enlace warned-versions está cerrado.

## NO INTEGRADO / LÍMITES

Sin commit/push/producción ni sustitución de assets versionados. `front/angular.json` ajeno preservado. /u/ aún algo pinzado con pliegues fuertes; /i/ labio superior fino. Dientes, lengua y corte ilustrativos. La iluminación nueva también afecta al corte; no es visualmente idéntico al anterior. Falta teléfono real y feedback de Miguel.

El fundido cutáneo perioral existe en el shader del visor: **no está horneado en PNG ni reproducido por el material Blender**. El .blend conserva geometría/shape keys, no equivale a una película fotorrealista. Se excluyó el normal map antiguo hasta hornearlo para la nueva topología. No hay simulación física de piel.

Referencias consultadas: [Texture](https://threejs.org/docs/pages/Texture.html), [MeshPhysicalMaterial](https://threejs.org/docs/pages/MeshPhysicalMaterial.html), [ejemplo oficial LPS](https://github.com/mrdoob/three.js/blob/dev/examples/webgl_materials_normalmap.html).

## Corrección de carga — feedback móvil posterior
Las capturas de Miguel mostraban el respaldo geométrico, no el GLB final. No se determinó la causa de la descarga/carga fallida en su teléfono; el endpoint público devolvió200 y4861268B en la comprobación actual. La demo ahora oculta ese respaldo mientras carga, confirma ambos modelos antes de mostrar el visor y ofrece reintentar si falla o tarda más de20s. Esbuild correcto. Servidor actualizado exec51409; mismo túnel/enlace y caducidad. Geometría sin cambios. Falta confirmar el resultado en el teléfono de Miguel.
