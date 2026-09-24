# /u/: perfil labial menos puntiagudo

24 sep 2026, revisión nocturna autorizada. Mejora pequeña del piloto raíz
labial 7ae79e6, conservado en la release privada. El cambio suaviza los dos
picos del labio superior al redondear. No alcanza fotorrealismo: la piel
arrastrada alrededor de las comisuras y la abertura dental siguen artificiales.

## Cambio y comparación

En perioral_didactico.py, fruncir transporta los anillos de cuerpo 2/3
respecto al borde manteniendo su espesor lateral de reposo. Se retiran las
exageraciones de proyección (1.25) y altura superior (1.18). El inferior
conserva su compensación vertical 1.08. Los anillos funcionales 0/1 no cambian.
El campo exterior y el contorno del corte se generan desde ese mismo perfil.

Antes/después de /u/ frontal y lateral, misma cámara/luz, 390x844.
También se inspeccionaron /ɒ/ lateral, /i/ frontal y una fase intermedia
de /u/. Comparación de /i/ con la captura Astra aceptada: conserva sonrisa,
tono moreno y proporciones del piloto; esta entrega sólo ajusta redondeo.
La mejora frontal es discreta, principalmente en el borde superior.
No hubo candidato visual descartado en esta ejecución. No se alteran materiales,
texturas, dientes, lengua, sonido ni código de animación.

## Evidencia y límites

- Medir_grosor_labial, 81 estados: superior mínimo/reposo 1.00; sostenida
  /u/ 1.13178, antes 1.33544. Inferior mínimo 0.94938 y sostenida 0.96392,
  sin cambio. Es altura central del tejido, no volumen global ni dato clínico.
- 260 anclas funcionales y 128 comprobaciones inferiores de /f–v/: delta0
  en todos los morfos. La abertura y los contactos quedan idénticos.
- 82/86 mallas idénticas por hashes de atributos, índices y morfos. En las
  cuatro mallas restantes sólo cambian posiciones de fruncir; además hay
  una normal distinta por mitad exterior (delta vectorial máximo .00032802,
  menor al umbral .001 del comprobador). Bases e índices idénticos.
- 2227 estados con aplicar() real: exit0; 53 vértices compartidos, costura0;
  raíz37 vértices/error1.276526e-7; plegado superior0; cierre .0000513077;
  contacto /f–v/ .005401 máximo y liberación .718428; penetración exterior0.
  Lengua: error de sección .00068160 menor a .001, ningún estado fuera.
  Son comprobaciones geométricas acotadas, no certificación anatómica.
- Visor móvil: viewport390, documento375=contenido375; sin desbordamiento
  horizontal ni errores de consola. No medidos FPS ni teléfono físico.
- No se repiten las 135 pruebas Angular, TSC ni build anteriores: runtime y
  frontend permanecen iguales. El GLB cambiado sí tiene nueva validación completa.

## Reproducir y respaldar

Fuente Blender 2.93; salida aislada build/redondeo_perfil. Generar con
SALIDA_DIDACTICA apuntando a esa carpeta y cara_didactica.py. Después:

    node tools/boca3d_demo/medir_didactica.mjs build/redondeo_perfil/cara.glb build/redondeo_perfil/medidas_final.json --completo --exigir --exigir-raices --lengua=build/lengua_realista/lengua.glb
    node tools/boca3d_demo/medir_grosor_labial.mjs build/redondeo_perfil/cara.glb build/redondeo_perfil/grosor.json --exigir
    node build/redondeo_perfil/validar_anclas.mjs
    node build/redondeo_perfil/comprobar_invariantes.mjs build/redondeo_perfil/cara_antes.glb build/redondeo_perfil/cara.glb build/redondeo_perfil/invariantes.json

Los dos comprobadores auxiliares van en Evidencias del ZIP. Para repetirlos,
copiarlos a build/redondeo_perfil y recuperar cara_antes.glb de la entrega
raiz-labial-7ae79e6.zip. El GLB nuevo mide 5,974,316 bytes, SHA256
8b7a98edac236c91fde07d0e5502ca0762f7c2281e1e28263af43997f42cfb32.

Sólo recursos gratuitos y capturas sintéticas del visor. Sin video ni
fotogramas privados. front/angular.json ajeno intacto; sin master ni producción.
Se conserva la entrega anterior para comparación o reversión.

## Corrección del respaldo

El primer ZIP local perfil-redondeado-41ece1c.zip se descartó sin subirlo:
Blender 2.93 devolvía éxito de proceso tras fallar al empacar una textura,
y faltaba cara.blend. SALIDA_DIDACTICA ahora se normaliza como ruta absoluta.
El empaquetador usa --python-exit-code 1 y exige que cada proyecto exista.
Un control con la fuente defectuosa fue rechazado antes de crear el ZIP.

El proyecto se regeneró con rutas absolutas y se incorporó la textura. Las
posiciones, índices, UV y todos los morfos coinciden exactamente con el GLB
ya validado. Sólo una normal de exportación difiere 0.0000051283; imagen
embebida idéntica. Se mantiene el GLB validado, no se repiten pruebas geométricas
por esta reparación de rutas. regeneracion.json documenta esa equivalencia.

## Respaldo confirmado

Fuentes visuales 41ece1cfdbe0b91b9f19c9f87931a80a4ed61a2e y corrección de
empaque d70cd688e79f1a4ea99721510c38292ab9f84426, subidas a origin.
[Release privada](https://github.com/rayko800-lgtm/literalevel/releases/tag/boca3d-noche-2026-09-23):
perfil-redondeado-d70cd68.zip, 10,767,548 bytes, SHA256
b46eef0356fc11bb92ec30a02158a1c1cafb9c3d14b356964725231e69ad47e2.
26 archivos, 25 hashes y CRC verificados; digest remoto idéntico. Incluye
ambos proyectos Blender, seis capturas y ocho archivos de evidencia.

[Visor temporal /u/](https://analysis-heating-drawings-pregnant.trycloudflare.com/?didactica=1&inventario=1&s=u&ciclo=0&sombras=0&vista=frente&velocidad=0.5)
comprobado visualmente y mediante hashes de cara.glb, lengua.glb y demo.js.
Vigencia previa conservada hasta aproximadamente 09:28 CDMX del 24sep.
Servidor 8772 exec4371, túnel56326 intacto; ensayo8774 detenido.
No se sobrescribe ningún respaldo anterior ni se despliega producción.
