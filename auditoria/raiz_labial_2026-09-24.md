# Boca3D: unión de los labios en el corte lateral

Petición directa de Miguel: continuar corrigiendo la forma labial tras las
capturas de /u/ y /ɒ/. Base 356b3a6, piloto visual f4c14aa. No se toca el SVG2D.

## Problema y resultado

El contorno exterior del labio se movía correctamente, pero los dos puntos
posteriores del corte recibían morfos labiales y seguimiento blando de piel.
El mentón y la arcada inferior seguían otro movimiento, rígido. Al abrir y
redondear se separaban: el labio parecía una pieza pegada o un muñón.

Los puntos posteriores ahora se quedan con el maxilar superior o giran con
la mandíbula inferior. No reciben morfos de fruncir/estirar. En el canal
RigMandibula, X=-1 identifica inserción fija y X=-2 inserción mandibular rígida;
el visor interpreta esos dos marcadores. Los valores anteriores >=0 siguen
usando el campo de piel habitual. Los siete puntos exteriores del corte
permanecen unidos al exterior y mantienen sus morfos.

La comparación /ɒ/ muestra una base inferior continua y oblicua hacia el
mentón, en lugar de una pieza rectangular separada. La mejoría es del corte;
la apariencia frontal de /u/ es idéntica al piloto anterior y aún artificial.
No se afirma que se hayan resuelto su forma ni el fotorrealismo.

84 de 86 mallas mantienen exactamente atributos, índices y morfos. Sólo
cambian anatomia_labio_sup/inf. Cara exterior, dientes, lengua, texturas y
tono moreno se conservan. El GLB final mide 5,974,312 bytes; SHA256:
5f87ffab94b5043a64d58f2023a0517d21198b2dcdc71aac373f6dac4b132df6.

## Verificación

- 2.227 estados con aplicar() real: error de raíz máximo 0.000000128,
  37 vértices exportados correspondientes a las cuatro inserciones.
- Control positivo, modelo anterior: falla la nueva comprobación, error
  máximo 0.525686 en /θ/ (216 estados). Es una medida del modelo, no milímetros.
- 53 vértices compartidos: error de costura 0. Plegado superior 0.
- Cierre 0.00005131, contacto /f v/ máximo 0.005401 y liberación /p b/ 0.718428,
  iguales al piloto anterior. Penetración labial medida 0.
- Raíces sin morfos comprobadas contra 24 coronas convexas en los 545 ángulos
  mandibulares distintos del inventario: 483.960 comprobaciones, penetración 0.
  No certifica cualquier intersección posible entre triángulos.
- Grosor central de /u/, 81 muestras: mínimo superior 100%, inferior 94.94%
  respecto de reposo; idéntico a f4c14aa. No es una medida de volumen global.
- 135 pruebas Boca3D/9 archivos, TypeScript y build correctos. Permanece el
  aviso CSS previo pronunciar.css de 12.64 kB frente a 12 kB.
- Revisión móvil 390×844: /ɒ/, /u/ lateral sostenida y movimiento, cierre /p/,
  contacto /f/ y /u/ frontal. Consola sin errores; documento y contenido 375 px.
  No sustituye revisión en teléfono físico ni medición de FPS.

## Intentos y límites

Se descartó trasladar la raíz posterior un 25% hacia el contorno externo:
adelgazaba la base pero no corregía el movimiento de la inserción. Fuente
interior_raiz25.py y GLB aislado conservados en build/labios_perfil.
No se convirtió ese intento en el modelo publicado.

La revisión del guard anterior de Blender encontró que no reproducía el
seguimiento .80 del visor y aplicaba un campo no lineal a puntos interpolados.
Sus cifras de contención no prueban por sí solas invasión oral. Esta entrega
usa aplicar() real y comprueba la inserción directamente.

La silueta sigue siendo una ilustración simplificada. /u/ frontal y la piel
arrastrada alrededor de las comisuras requieren otra mejora independiente.
Sin video ni fotogramas privados; sólo recursos gratuitos. Sin master ni
aplicación de producción. front/angular.json conserva su hash ajeno.

## Reproducción y respaldo

Generar con Blender 2.93, SALIDA_DIDACTICA apuntando a carpeta nueva y
tools/boca3d_blender/cara_didactica.py. Después:

    node tools/boca3d_demo/medir_didactica.mjs cara.glb medidas.json --completo --exigir --exigir-raices --lengua=build/lengua_realista/lengua.glb
    node tools/boca3d_demo/medir_grosor_labial.mjs cara.glb grosor.json --exigir

El control anterior usa el GLB de redondeo-f4c14aa.zip con --exigir-raices y
debe fallar. La comprobación adicional de raíces/dientes está en Evidencias;
para repetirla, colocar su .mjs en build/labios_perfil del checkout y recuperar
build/redondeo_grosor/medidas_final.json del ZIP de evidencias anterior.

Salida local: build/labios_perfil. Los modelos de producción versionados no
se sustituyen. El paquete de entrega incluye proyectos Blender, visor, siete
capturas y diez archivos de evidencia con manifiesto de hashes.

## Respaldo confirmado

Fuente 7ae79e6fec1b041e44225a6f8ff4fa4ef093539c subida a origin.
[Release privada](https://github.com/rayko800-lgtm/literalevel/releases/tag/boca3d-noche-2026-09-23).
raiz-labial-7ae79e6.zip: 10,807,851 bytes, SHA256
631afe5e19e845738653b124f5a203960371e1a70f0d533203428063730b879b.
29 archivos, 28 hashes y CRC comprobados; digest remoto idéntico.
Respaldos anteriores conservados. El informe del ZIP corresponde a la fuente,
este recibo se añade después.

[Visor temporal](https://analysis-heating-drawings-pregnant.trycloudflare.com/?didactica=1&inventario=1&s=%C9%92&ciclo=0&sombras=0&vista=lado&velocidad=0.5)
verificado visualmente y por identidad de cara.glb, lengua.glb y demo.js.
demo.js 775,731 bytes, SHA256
e07639b09cc2dd46e18aa4cf7afaa07923f132afae2dda4b99e5c0e6e4c6c387.
Servidor 8772 exec1106; túnel56326 conservado, fin previsto 09:28 CDMX24sep.
