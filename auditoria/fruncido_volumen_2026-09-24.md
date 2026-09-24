# Fruncido: cuerpo labial y abertura

24 sep 2026. Miguel autorizó corregir /u/ tras comparar su captura con el
gesto de su video privado. El modelo anterior parecía una boca encogida,
con tejido fino a los lados y demasiada exposición dental. Esta entrega
recoge el cuerpo del labio alrededor de una abertura menor. Mejora visible
respecto a perfil-redondeado-d70cd68, conservado para comparación.

## Forma y alcance

La curva en profundidad se calcula con el ancho ya contraído: conservar el
arco de reposo dejaba las comisuras atrás, formando un embudo. El cuerpo
de los anillos2/3 gana anchura lateral y espesor al fruncir. La abertura
se reduce y desciende; la piel y el corte se derivan del perfil nuevo.

Sólo cambia el morfo fruncir, compartido por sonidos redondeados. A diferencia
del ajuste anterior, aquí sí se modifica su borde funcional0/1 para reducir
la abertura. Los demás morfos conservan sus anclas. No se ocultan dientes por
código, no se cambian materiales ni texturas, y el runtime permanece igual.

La referencia es el gesto redondeado de los fotogramas privados alrededor
de87s, no una identificación acústica de /u/. Ángulo e iluminación distintos;
no se extraen milímetros, volumen clínico ni una reconstrucción del usuario.
El piloto conserva el tono de piel moreno. Ningún fotograma privado forma
parte de Git, ZIP ni visor. Sólo recursos gratuitos.

## Comparación y pruebas

En unidades del modelo, /u/ sostenida:

| Medida | Anterior | Nueva |
| --- | ---: | ---: |
| Anchura de la abertura | .70040 | .49440 |
| Altura de la abertura | .31600 | .15600 |
| Anchura del cuerpo labial | .92422 | 1.34181 |
| Cuerpo / anchura de reposo | 41.49% | 60.24% |
| Cuerpo / abertura | 1.32 | 2.71 |

El medidor ahora registra anchura de cuerpo y abertura en los81 estados del
ciclo, además del grosor central. El centro por sí solo no detectaba la
pérdida lateral. Mínimo central superior100% e inferior95.81% del reposo;
sostenida181.06% y106.28%. Es un engrosamiento del gesto, no volumen conservado.

- 2227 estados mediante aplicar() real, exit0: penetración exterior0;
  cierre .0000513077; /f–v/ distancia máxima .005401 y liberación .712725.
  Costura53 vértices/error0, plegado superior0, raíz37/error1.276526e-7.
  Lengua: sección .00068160<.001, ningún estado fuera de tolerancia.
- 260 anclas comparadas: sólo fruncir cambia (delta máximo .62460).
  /f–v/, cierre, estirar y demás morfos idénticos, incluidas128 comprobaciones
  del labio inferior. El comprobador excluye explícitamente fruncir de la
  igualdad; la validación del runtime comprueba sus contactos y transiciones.
- 82/86 mallas exactas por hashes. Cuatro mallas cambian sólo posiciones de
  fruncir; además una normal exterior difiere .0000051283. Bases, UV, índices,
  dientes, materiales y lengua se conservan.
- Visor en viewport390x844: documento375=contenido375; sin errores de consola.
  Revisión frontal /u/, /ʊ/, /ɔ/, /w/, /i/, cierre/p y /f/; /u/ lateral;
  muestreo del ciclo a velocidad reducida. Capturas nativas JPEG375x811.
- No se repiten Angular135/TSC/build previos: frontend y runtime no cambian.
  Sí se ejecuta nueva validación completa del GLB y del medidor ampliado.

No hubo ensayo visual descartado en esta ejecución. La primera hipótesis
produjo una mejora conservable. Persisten una superficie labial artificial,
pliegues de piel simplificados y un corte ilustrativo; no fotorrealismo.
No medidos FPS ni teléfono físico. Los controles geométricos no certifican
anatomía clínica ni todas las intersecciones posibles.

## Reproducción

Blender2.93, SALIDA_DIDACTICA=build/fruncido_volumen, generar con
tools/boca3d_blender/cara_didactica.py. Salida se resuelve absoluta.

    node tools/boca3d_demo/medir_didactica.mjs build/fruncido_volumen/cara.glb build/fruncido_volumen/medidas_final.json --completo --exigir --exigir-raices --lengua=build/lengua_realista/lengua.glb
    node tools/boca3d_demo/medir_grosor_labial.mjs build/fruncido_volumen/cara.glb build/fruncido_volumen/grosor.json --exigir
    node tools/boca3d_demo/medir_grosor_labial.mjs build/fruncido_volumen/cara_antes.glb build/fruncido_volumen/grosor_antes.json --exigir
    node build/fruncido_volumen/validar_anclas.mjs
    node build/fruncido_volumen/comprobar_invariantes.mjs build/fruncido_volumen/cara_antes.glb build/fruncido_volumen/cara.glb build/fruncido_volumen/invariantes.json

Los auxiliares van en Evidencias del ZIP. Copiarlos a build/fruncido_volumen;
recuperar cara_antes.glb de perfil-redondeado-d70cd68.zip. GLB nuevo SHA256
a3d529995fe8e62b39b0578587f6a28de42652841c109026190c6230bb4cd619.

Respaldo con dos proyectos Blender/texturas, visor, comparaciones y medidas.
Sin master ni aplicación de producción. front/angular.json ajeno intacto.
