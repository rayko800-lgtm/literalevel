# Boca3D: grosor durante /u/ y labios del corte lateral

Petición de Miguel del24sep: /u/ pierde grosor durante el movimiento y los
labios del corte parecen dos pulgares. Base ac2cb09/f653360, dev/articulacion-v2.
La captura que llama2D corresponde al corte del visor3D; el SVG2D no se cambia.

## Referencia y cambio

Se revisó nuevamente el video local autorizado: gestos próximos a83,85,86,87
y88 segundos. El redondeamiento visible conserva cuerpo labial. Son referencias
visuales sin calibración métrica ni asignación automática de fonemas por audio.
Los fotogramas permanecen privados y fuera de repositorio, ZIP y servidor.

En perioral_didactico.py, el morfo fruncir transporta el perfil de los anillos2/3
desde el borde funcional, en lugar de comprimir su espesor con el ancho de boca.
La transición hacia comisuras es suave y el campo cutáneo se resuelve después.
Los anillos0/1 mantienen sus coordenadas. No se alteran dientes, lengua,
texturas, tono moreno ni los demás morfos. Otros sonidos que utilizan fruncir
también reciben su nuevo perfil; la comprobación completa cubre el inventario.

En el corte se conserva el contorno y se distingue su raíz cutánea del
bermellón. El visor conserva los colores por vértice del generador;
los modelos antiguos sin esos colores mantienen el material anterior.
Los siete puntos externos del corte siguen compartidos con el exterior.
La mejoría lateral es modesta: rompe la mancha rosa uniforme, pero la silueta
sigue siendo una ilustración esquemática. No se presenta como anatomía resuelta.

Se descartó un retorno interior curvado/subdividido: sus comprobaciones de
contención no acreditaron seguridad en todas las poses (máximos reportados
.049834 y1.154809 unidades, segundo diagnóstico no resuelto). No se exportó
al piloto final. Se volvió al contorno, pesos mandibulares y morfos previos;
sólo se añadieron los colores. Intentos locales en build/labios_corte_revision.

## Grosor durante el movimiento

medir_grosor_labial.mjs utiliza EscenaBoca.aplicar y poseDeLinea reales en81
instantes del ciclo/u/. Mide altura central del borde al cuerpo del labio,
no volumen3D ni milímetros anatómicos. Se compara con reposo del mismo modelo.

| Perfil | Mínimo anterior | Mínimo candidato | Altura final/u/ del candidato |
| --- | --- | --- | --- |
| Superior |78.70%|100.00%|133.54%|
| Inferior |80.23%|94.94%|96.39%|

El superior gana cuerpo al fruncir; no se afirma espesor idéntico en cada
punto de toda la superficie. Umbral ilustrativo de regresión: conservar al
menos90% de altura central a través del ciclo. Control positivo: modelo
anterior falla con exit1; candidato pasa con exit0.

260 puntos de los anillos0/1 idénticos en TODOS los morfos, incluido fruncir;
128 puntos inferiores/fv/ exactos. Apertura, cierre y contactos no se recalibran.

## Validación y reproducción

135 pruebas Boca3D,9archivos, TypeScript y build correctos con el nuevo material
de corte. Aviso CSS previo: pronunciar.css12.64kB frente a12kB. No se cambia
front/angular.json; SHA2560916137F608401AAF0F52B9FDFEB05F7E7D6876C7B07A7C70F0B78A05F505858.

Combinación final: 2227 estados, exit 0. Penetración medida 0; error de cierre
0.00005131; distancia /f v/ máxima 0.005401; liberación /p b/ 0.718428.
53 vértices compartidos, error de costura 0 y plegado superior 0.
Sección de lengua: 0 estados fuera de tolerancia, error máximo 0.00068160
(tolerancia 0.001). El test dental comprueba vértices contra coronas convexas;
no certifica ausencia de cualquier intersección entre triángulos.

Revisión visual en 390×844: /u/ sostenida y en movimiento, /i/, /p/, /f/
y corte /ɒ/. Sin errores de consola ni desbordamiento horizontal
(375 px de contenido y documento). No equivale a prueba en teléfono físico
ni a medición de FPS. Comparaciones u-antes/u-despues y corte-antes/corte-despues
con cámara e iluminación iguales; controles i/f/p-despues.

Salida de trabajo build/redondeo_grosor; cara_antes.glb/.blend conservan
exactamente el candidato anterior. GLB final 5,974,680 bytes, SHA256
3faf6044757ed7de8de7ee526d607500197b894a4b9de60949e1368465bfbcd8.
La lengua permanece idéntica. Los GLB versionados de producción no se cambian.

Generar con SALIDA_DIDACTICA a una carpeta nueva y Blender2.93 ejecutando
tools/boca3d_blender/cara_didactica.py. Medir con:

    node tools/boca3d_demo/medir_grosor_labial.mjs cara.glb grosor.json --exigir
    node tools/boca3d_demo/medir_didactica.mjs cara.glb medidas.json --completo --exigir --lengua=build/lengua_realista/lengua.glb

Sólo recursos gratuitos. No producción ni master. Los cambios son de geometría
didáctica; todavía requieren aceptación estética de Miguel y no constituyen
fotorrealismo. Los respaldos anteriores se conservan en GitHub privado.
