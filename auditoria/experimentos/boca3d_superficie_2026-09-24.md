# Boca3D: prueba de acabado labial, 23:24 CDMX del 23 de septiembre

DESCARTADO como sustituto del piloto. Se conserva 74c9941, con incisivos v4 y
labios diferenciados. Esta ejecución prueba una única hipótesis de material;
no cambia mallas, posiciones, contactos, piel morena ni texturas. Base de
reproducción: e0fc341b2dac50d9bd7d555363902f888f3918a3, dev/articulacion-v2.

## Hipótesis y resultado

El acabado uniforme de los labios podía contribuir a su aspecto plástico.
Se probó rugosidad .54 en el exterior y .30 junto a la abertura, interpolada
en coordenadas de reposo, frente al .38 uniforme del piloto fotográfico.
El cambio se limita al shader de ese piloto; el exterior ilustrado conserva
sus valores. Se actualizó su clave de caché de shader.

En /i/ y /f/ la diferencia visible es insuficiente para sustituir el piloto.
Persiste la franja clara y el relieve visual de la textura. La hipótesis para
una siguiente ejecución es que parte de ese brillo está pintada en el mapa
de color; esto es una inferencia visual, no una medición de reflectancia.
No se ensayó otra hipótesis en esta ejecución. /f/ conserva una banda inferior
demasiado plana y /u/ aún arrastra la piel, límites ya registrados.

Se revirtió únicamente el diff de escena.ts producido aquí; `git diff` de
ese archivo volvió a vacío. El servidor público y sus assets no se modifican.
El ZIP noche-74c9941.zip permanece como mejor candidato guardado; la versión
Astra anterior aceptada por Miguel sigue respaldada por separado.

## Evidencia y pruebas

- Capturas reales del visor en ventana 390 x 844: `i-vigente-viewport.png` e
  `i-candidato-viewport.png`, misma pose, cámara, geometría, luz y color.
- Revisión de /f/ en ambos visores. Las capturas de página completa iniciales
  no se usan para comparación cuantitativa: el capturador alteró su escala.
- WebGL compiló el shader nuevo; consola del candidato sin errores ni avisos.
  Ancho de documento 375 y scrollWidth 375, sin desbordamiento horizontal.
- `npx.cmd ng test --watch=false --include='src/app/compartido/boca3d/piloto.spec.ts'`:
  22 pruebas aprobadas, 1 archivo. `npx.cmd tsc --noEmit -p tsconfig.app.json`:
  exit 0. Empaquetado esbuild del visor correcto.
- No se repiten los 2227 estados de geometría ni toda la batería: no cambian
  mallas/poses y el ensayo se descarta. No se midieron FPS ni teléfono real.
- front/angular.json conserva SHA256
  0916137F608401AAF0F52B9FDFEB05F7E7D6876C7B07A7C70F0B78A05F505858.

## Reproducir sin alterar la versión conservada

En un checkout aislado de la base indicada, aplicar
`git apply auditoria/experimentos/boca3d_superficie_2026-09-24.patch` (copiar
primero el patch de este commit al checkout). El patch contiene el cambio
completo y se comprobó con `git apply --check` sobre la fuente restaurada.
Conservar los GLB de la entrega noche-74c9941.zip y construir tools/boca3d_demo/demo.ts
con esbuild; no regenerar mallas para esta comparación. Usar los parámetros
`?didactica=1&inventario=1&s=i&ciclo=0&sombras=0&vista=frente&velocidad=0.5`.
El runtime utiliza las dependencias gratuitas ya instaladas en front/.

Las dos capturas, este informe, el patch y un manifiesto SHA256 se guardan
como evidencia adicional en la release privada boca3d-noche-2026-09-23.
No contiene video ni fotogramas privados. Sin producción ni fotorrealismo
alcanzado. Autorización de nuevas iteraciones hasta 07:00 CDMX del 24.
