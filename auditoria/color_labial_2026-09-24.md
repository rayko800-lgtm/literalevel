# Boca3D: color del labio inferior — 24 sep 2026, 01:25 CDMX

CONFIRMADO: corrección acotada del muestreo de color en el piloto fotográfico.
Reduce la franja blanquecina exterior del labio inferior, especialmente en /i/.
NO INTEGRADO en producción. Candidato pendiente del juicio estético de Miguel;
no fotorrealismo alcanzado. Base d47a7a5 (geometría vigente74c9941); rama
dev/articulacion-v2. Autorización de iteraciones hasta07:00CDMX24sep.

## Cambio y comparación

La textura derivada de LPS tiene una franja más clara bajo el bermellón. En
el centro del mapa, filas normalizadas .479 y .483: RGB medio aproximado
[.682,.344,.350] y [.787,.494,.498] respectivamente (sRGB, no colorimetría
de piel). El muestreo anterior estiraba ese borde en una raya clara al abrir.

En escena.ts, sólo para el exterior fotográfico y la máscara del labio inferior,
se acerca un25% la coordenada vertical de color a .467, la línea de reposo
del mapa exportado glTF. Se conserva horizontal, mezcla gradual, mapa original,
color moreno, pigmentación, luz y rugosidad. Añade una lectura de textura por
fragmento de ese material; no añade imágenes ni vértices ni modifica el rig.
La clave de caché del shader cambia para recompilar el material correcto.

Revisada la captura Astra aceptada astra-i-final.png. Para aislar esta corrección,
las capturas i-antes/i-despues comparan74c9941 con este candidato: mismas mallas,
pose, cámara y luz. Disminuye el contorno claro; el labio queda algo más oscuro.
En /f/ la ganancia es menor y persiste una banda demasiado plana. /u/ todavía
arrastra la piel; /æ/ tiene apertura exagerada. Dientes idénticos a v4.

Intento descartado durante implementación: usar .533 como línea de referencia
(convención UV de Blender) tomaba piel clara y blanqueaba el labio. Se corrigió
a .467 después de leer TEXCOORD_0 del GLB: primeros puntos inferiores
[.500,.468], [.502389,.467999]. Nunca se publicó ese error. La rugosidad
variable descartada en la ejecución anterior NO se reintroduce.

## Verificación pertinente

- 22 pruebas en piloto.spec.ts aprobadas; TypeScript sin errores.
- Build Angular correcto tras corregir la coordenada. Aviso previo: pronunciar.css
  12.64kB frente a presupuesto12kB; front/angular.json ajeno sin modificar.
- WebGL compila sin errores/avisos. Revisión móvil390x844 de /i f p u æ/,
  cierre/p/, corte lateral/æ/ y movimiento/æ/. Ancho375=scrollWidth375.
- Sin nueva prueba de2227 estados: geometría y poses no cambian. Cara y lengua
  tienen exactamente los hashes ya validados. No se midieron FPS ni teléfono real.
- No regresiones visuales observadas en estas poses; esto no certifica anatomía
  clínica ni una mejora estética de todos los sonidos.

Cara5973224B SHA25626C543A881E4065A078ED52907332771F4DFB2701125E5E8C45DC657ED671B92.
Lengua444212B SHA256451CEEA3BE66B4DA43CE1D38B837AB91A77D2413FC39FB738E5D05E982611F64.
Angular.json ajeno SHA2560916137F608401AAF0F52B9FDFEB05F7E7D6876C7B07A7C70F0B78A05F505858.

## Reproducción y respaldo

Fuentes exactas en el commit identificado por MANIFIESTO.json del paquete.
Crear una carpeta nueva con tools/boca3d_demo/empaquetar_realismo.mjs y Blender;
INFORME_PILOTO=auditoria/color_labial_2026-09-24.md,
CAPTURAS_PILOTO=build/labios_color/capturas. La descripción del comparador ahora
remite al informe para distinguir cambios de material y de forma.
El paquete incluye visor, GLB, Blender con texturas, seis capturas y hashes.
El cambio de color se aplica en Three.js: no está horneado en Blender.

Se guarda como archivo adicional de la release privada boca3d-noche-2026-09-23;
se conservan noche-74c9941.zip y la release Astra aceptada. No video/fotogramas
personales, ningún recurso de pago, no master ni aplicación de producción.
