# Corrección del rostro — 23 septiembre 2026

## CONFIRMADO

Miguel señaló nariz desalineada, labios extraños y dientes como bloques; pidió fotorrealismo con GTA 6 como aspiración. Se entrega otra revisión del piloto, **no fotorrealismo alcanzado**. Rama dev/articulacion-v2, base0421f0d243dbf6c611f918f1c286d7f212344d2c.

- Nariz recentrada; normales del escaneo completo conservadas en la zona nasal para eliminar la franja entre mitades. Normales móviles ponderadas por ángulo.
- Labio superior con más volumen; máscara de color corregida para el espacio lineal de glTF. /i u/ reajustados. Desplazamientos de piel suavizados sobre un grafo común a ambas mitades; transición mandibular continua con segundo canal UV.
- 24 coronas diferenciadas mediante dientes_realistas.py: caras convexas, cuellos estrechos, laterales/caninos distintos y esmalte corregido. Transformaciones y anclajes incisales preservados.
- Exterior renderizado por su lado frontal; fondo bucal ampliado y oscurecido para evitar piel invertida dentro de la boca. Cámara y seguimiento mandibular reajustados.

Generación aislada: Blender 2.93 `-b --python tools/boca3d_blender/cara_didactica.py`. No ejecutar generadores de producción para actualizar este piloto. Catálogo46+7 y controles conservados; sin audio.

## VERIFICADO

- 135 pruebas Boca3D en9 archivos, TypeScript/build correctos. Advertencia CSS previa+639B. Dos regresiones nuevas: normales nasales estáticas y transición mandibular suave con borde labial exacto.
- GLB final:2227 estados, penetración detectada de vértices labiales en coronas convexas0; cierre0.000007391; /f v/ distancia central0.00202444 y lateral0.00540100; liberación /p b/0.87393240. Unidades del modelo. No certifica toda intersección de triángulos ni anatomía clínica.
- Costura labial52 vértices compartidos/error0. Sección: discrepancia máxima de área0.000706768 frente a tolerancia ilustrativa0.001; ningún estado fuera. Datos/logs: build/boca_didactica/rostro-final-medidas.*.
- Dental aislado:24 coronas dentro de envolventes previas,80 anclajes incisales exactos, matrices conservadas y mallas cerradas.
- Inspección pública final /i u f/ y /k/ lateral; /ɑ/ inspeccionado antes del último suavizado exclusivo de/i u/. Capturas workspace evidencia-blender/rostro-{i,u,f}-final.png, rostro-k-corte-final.png, rostro-a-v3.png.
- Viewport390×844, ancho cliente/documento375 sin overflow. Palabra animada57.6 callbacks rAF/s durante4s en escritorio con tamaño móvil; no teléfono físico ni medida de fotogramas GPU. Consola final limpia. Hash público igual al local.
- Revisor independiente considera el nuevo exterior apto para revisión humana; todavía detecta raya vertical en mentón de/i/ y diferencia de acabado entre piel/labios/interior. Aceptación de Miguel pendiente.

## ARTEFACTOS

build/boca_didactica/cara.glb:5482744B, SHA25691491B0E36BFD3403B08F099C96580110C734073325889D0CE8D3EA6CE4BA109. cara.blend:11669188B.

Respaldo exacto previo: build/boca_didactica/antes_correccion_rostro/, GLB SHA25612CAB36C2A82517A922FD7DC075C82CFE923D3EC4E25163F28621B8E0DAD1CA7. Incluye generadores y escena previos. Respaldo anatómico más antiguo: aprobado_anatomia/.

## TEMPORAL

https://apr-button-profits-scsi.trycloudflare.com/?didactica=1&inventario=1&s=i&ciclo=0&sombras=0&vista=frente&velocidad=0.5

Hasta aproximadamente19:37CDMX del23sep. Cinco assets permitidos,3685079B comprimidos. Servidor8769 exec16753; túnel exec38976/hijo47808. Assets en memoria: reconstruir build_blender_preview.mjs requiere reiniciar únicamente el servidor propio identificado. Enlace warned-versions anterior cerrado.

## NO INTEGRADO / LÍMITES

Sin commit/push/producción ni sustitución de assets versionados. front/angular.json ajeno intacto. Lengua y corte ilustrativos; boca muy abierta deja ver una lengua demasiado geométrica. Persiste pequeña marca central del mentón. Faltan coherencia de materiales y deformaciones secundarias antes de llamarlo fotorrealista. No hay dispersión subsuperficial física. Mezcla cutánea del visor no horneada en PNG ni reproducida por material Blender; el .blend no es una película con el acabado web. Falta teléfono real.

Referencias consultadas: [Corrective Smooth](https://docs.blender.org/manual/id/4.4/modeling/modifiers/deform/corrective_smooth.html), [ejemplo oficial de dispersión subsuperficial](https://threejs.org/examples/webgl_materials_subsurface_scattering.html). La segunda técnica no se implementó.
