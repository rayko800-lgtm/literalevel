# Revisión nocturna: dientes y labios

Miguel revisó y aprobó el avance Astra, pero todavía ve dientes como tubos y
labios artificiales. Autorizó pruebas durante esta noche y guardar/subir commits.
Todo gratuito. Rama dev/articulacion-v2; front/angular.json sigue siendo ajeno.

## Punto de regreso confirmado

Fuentes y piloto anterior guardados en commit edeb914ae139c6b9d599d5d6200e1205cc694cf2,
subido a origin. Paquete descargable con GLB, dos proyectos Blender con texturas
incorporadas, visor local y manifiesto de archivos:
https://github.com/rayko800-lgtm/literalevel/releases/tag/boca3d-astra-2026-09-23
ZIP10361195B; SHA2568ed6c14f3db0bb2c0763f2ce2a058946a3760672048c3d0213953caadbb0a178.
Digest remoto idéntico; CRC correcto. Visor del paquete abierto y comprobado.

## Candidato nuevo

- Incisivos de pala: frente amplio levemente convexo, hombros redondeados y
  concavidad lingual. Sección central reduce espesor de.16279 a.09408 y desnivel
  centro/hombro de.02475 a.00118 (unidades del modelo, no clínica).
- Conservados960 puntos incisales,24 matrices y envolventes; mallas cerradas.
  Mismo número de vértices/caras/colores; caninos y posteriores iguales a v3.
- Volumen labial diferenciado, comisuras más finas y menor relleno externo.
  /i/ adelgaza al estirarse; /u/ abre más oval; /fv/ reduce elevación superior
  y curva el inferior.260 anclas de cierre/compresión/sello/estirar y128 anclas
  inferiores /fv/ exactas. /u/ sí cambia su abertura, intencionalmente.
- Sin cambios de shader, iluminación o textura respecto al piloto aprobado.
  Ningún video/fotograma privado incorporado. Apariencia sigue aproximada.

## Comprobación integrada

`node tools/boca3d_demo/medir_didactica.mjs build/realismo_noche/cara.glb
build/realismo_noche/medidas.json --completo --exigir
--lengua=build/lengua_realista/lengua.glb`:2227 estados, exit0.
Penetración medida0; cierre.0000513077; /fv/.00202444 central y.00540100 lateral;
liberación.718427965; costura53 vértices/error0; sección.000681600<.001;
plegado superior0 (antes.001451612). No certifica todos los triángulos ni clínica.

Capturas reales móvil390×844 de /i æ u f p/ y corte/k/. Sin errores WebGL;
sin desbordamiento horizontal. La ganancia dental visible es menor que en las
coronas aisladas porque el labio sigue cubriendo buena parte de su altura.
No se repiten135 pruebas/TSC/build del checkpoint: runtime Angular intacto;
se prueban la geometría cambiada, exportación y entrega portátil.

Cara final:5973224B, SHA25626C543A881E4065A078ED52907332771F4DFB2701125E5E8C45DC657ED671B92.
Lengua permanece444212B, SHA256451CEEA3BE66B4DA43CE1D38B837AB91A77D2413FC39FB738E5D05E982611F64.
Fuentes propias: dientes_realistas.py, perioral_didactico.py. Comparaciones y
medidas en build/dental_v4, build/labios_noche y build/realismo_noche.

## Entrega y continuación

`empaquetar_realismo.mjs` genera únicamente GLB, proyectos empaquetados, visor,
créditos, manifiesto y evidencia opcional explícita. No recorre el repo completo.
`empacar_blend.py` rechaza sobrescribir el proyecto fuente y verifica texturas.
El material completo Three.js sigue sin estar horneado en Blender.

Revisión nocturna programada en este hilo cada2 horas hasta07:00CDMX del24sep,
ID boca3d-revisi-n-nocturna. Trabajar una mejora justificada por ejecución;
guardar resultados, preservar el mejor y no repetir pruebas sin cambios.
La aceptación estética del candidato nuevo está pendiente. No se ha alcanzado
fotorrealismo. No fusionar master ni desplegar la aplicación de producción.

## Publicación del respaldo verificada

Commit de la mejora:74c99411a72868a5086f2aee4256a6e34eb72afd, confirmado en origin.
https://github.com/rayko800-lgtm/literalevel/releases/tag/boca3d-noche-2026-09-23
ZIP noche-74c9941.zip:10551771B,
SHA256 ed5c8503892007ced05d7b0b2675b2c35f3b3f0b1fac3c3efe56ba4314559b69.
Digest GitHub idéntico; CRC correcto y hashes de los17 archivos listados en el
manifiesto comprobados (18 archivos en el paquete contando el manifiesto).
Incluye informe y capturas antes/después. La fuente del ZIP apunta al commit
de implementación; esta anotación posterior documenta la publicación.

Vista temporal verificada, GLB público idéntico:
https://analysis-heating-drawings-pregnant.trycloudflare.com/?didactica=1&inventario=1&s=i&ciclo=0&sombras=0&vista=frente&velocidad=0.5
Hasta aproximadamente09:28CDMX24sep. Servidor8772 exec37954; túnel exec56326
hijo22152. Sólo cinco assets del piloto. El ZIP sigue disponible en GitHub
cuando termine el enlace temporal. No hay despliegue de la app de producción.

## Revisión 23:24 CDMX: superficie labial

Se ensayó rugosidad variable, mate exterior y húmeda junto a la abertura.
Mejora perceptiva insuficiente en /i f/: se descarta y se restaura escena.ts.
Se conserva íntegramente el piloto74c9941.22 pruebas pertinentes, TypeScript
y compilación WebGL correctos; no repetir geometría ni ensayar otra hipótesis
en esta ejecución. Fuentes del intento y detalles de reproducción en
experimentos/boca3d_superficie_2026-09-24.md y su patch. Evidencia adicional
en la misma release privada; respaldo anterior sin reemplazar.

## Revisión 01:25 CDMX del24sep: correspondencia de color

Nuevo candidato de material: remuestrea sólo el bermellón inferior para reducir
el borde blanquecino de la fotografía. Mallas y dientes v4 idénticos; cierre y
contactos conservados.22 pruebas pertinentes, TypeScript/build y revisión móvil
correctos. No reintroduce el acabado de rugosidad descartado. Informe vigente
completo: color_labial_2026-09-24.md. Mejora parcial, sobre todo/i/; no fotorrealismo.
