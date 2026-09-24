# Boca 3D — avance anatómico, 23 sep 2026

Miguel aprobó el catálogo y pidió continuar con más profesionalidad/realismo. Este avance modifica el corte interior del piloto. No es fotorrealismo ni validación clínica.

## CONFIRMADO

- Worktree articulacion-v2, rama dev/articulacion-v2, base 0421f0d. Sin commit/push/integración ni reemplazo de GLB versionados. `front/angular.json` ajeno preservado.
- Nuevo `tools/boca3d_blender/interior_didactico.py`, llamado desde `cara_didactica.py`: paladar con espesor, pared nasofaríngea continua, suelo/mentón, soporte alveolar, velo/úvula y labios derivados del exterior aprobado. Espesores cosméticos son decisiones de ilustración, no medidas clínicas.
- Superficie oral central del paladar y cara interna faríngea conservan envolventes previas. Velo conserva pivote/rotación: /i/ cierra paso nasal y /m/ lo abre (revisión visual independiente).
- Secciones labiales comparten vértices/morfos con exterior: 30 vértices verificados en 2227 estados; error máximo 9.49e-17. No implica cabeza completa unificada.
- Lengua original/poses intactas: sección medial siguiendo aristas reales; triangulación dinámica con buffer GPU reutilizado. Se actualiza desde aplicar(), antes de subir geometría a GPU: onBeforeRender dejaba el apoyo con la pose anterior en gestos sostenidos. Apoyo inferior y estriado ilustrativos, no simulación de músculos. Puede extenderse debajo del suelo de referencia si la pose previa ya desciende más.
- Corte conserva incisivos, oculta arcadas laterales que tapaban articulación. Frente mantiene dientes visibles por la abertura.
- Frente/Lado explícitos: girar ya no sustituye automáticamente el modelo a 35°. Exterior 360°; corte ±35°. Siluetas craneales todavía diferentes.

## Verificación

- 132/132 pruebas Boca3D, TypeScript y build Angular OK; aviso CSS previo +639 B. Pruebas nuevas de vista explícita sin alterar gesto y triangulación cóncava con reutilización de buffer.
- `medir_didactica.mjs ... --completo --exigir`: 2227 estados; cierre máximo .000007391; distancia /f v/ central .0020244 y lateral .0054010; cero vértices labiales dentro de 24 coronas convexas. No es análisis de todas las intersecciones/estructuras nuevas.
- Secciones finitas; discrepancia máxima entre área poligonal y triangulada .000706768, tolerancia de ilustración .001 unidades de área. No es error cero ni tolerancia clínica. `secciones-medidas.json` conserva resultado.
- Revisor independiente acepta /i m/ estáticas: cierre oral/apertura nasal distinguibles, lengua ya no suspendida. Revisión final /k/: sección continua sin grieta, dorso/cierre posterior claros. Todavía simplificada; cierre /m/ demasiado pequeño para valorarlo solo por captura.
- Navegador 390×844: capturas /i m ɑ/ de corte y /f/ frontal, consola sin errores observados. Muestreo visual representativo, no aprobación clínica de cada fonema.
- Fluidez final indicativa: 56.6 callbacks rAF/s (227 en 4 s), guarda inicial45.6, corte animado con modelos cargados y sombras0; escritorio con viewport móvil, no teléfono ni medición GPU formal. Ancho375/scroll375, sin overflow. No se extrapola a Android.

## Artefactos y reproducción

GLB `build/boca_didactica/cara.glb` 1697004 B; `cara.blend` 6731004 B. SHA256 local/remoto `FC17D5DEC7101CCDB8E6C9326D272252CDD3434523995F5E2441B6AC2E96B4B2`.

Respaldo exacto del catálogo aprobado en `aprobado_catalogo/`: GLB, Blender, fuentes, escena.ts y métricas. Reconstruir con Blender 2.93 `-b --python tools/boca3d_blender/cara_didactica.py`; NO ejecutar cara.py/lengua.py, pues escriben assets versionados.

Medidas/logs en build/boca_didactica: anatomia-medidas.json, secciones-medidas.json, anatomia-tests.log, anatomia-build-front.log. Capturas en workspace Nico, evidencia-blender/anatomia-*-final.png y anatomia-f-frente.png.

## TEMPORAL

[Muestra](https://warned-versions-maintenance-additionally.trycloudflare.com/?didactica=1&inventario=1&s=i&ciclo=0&sombras=0&vista=lado&velocidad=0.5). Servidor8769 exec17943, túnel exec69284 hijo47220; dos horas desde ~16:21 CDMX, hasta ~18:21. Sustituye enlace anterior cerrado. Cinco archivos permitidos, 1236505 B comprimidos. Cache: reconstruir build_blender_preview.mjs y reiniciar solo su servidor para renovar.

## Investigación / límites

Se aprovechó d4_4b_v4/investigacion_anatomia.md, contrastado con [atlas muscular primario](https://pmc.ncbi.nlm.nih.gov/articles/PMC3687025/) y [Seeing Speech](https://www.seeingspeech.ac.uk/ipa-charts/). No copiar como restricciones clínicas el grosor apical mínimo universal ni la holgura lengua-suelo ≥16 mm: esta última confunde longitud de lengua libre con separación geométrica. La acción del transverso en §1.4 contradice su propia tabla.

Pendiente: cabeza exterior/interior unificada, musculatura real, texturas de mayor calidad, teléfono físico y audio/integración. No reinvestigar desde cero ni repetir catálogo aprobado. La investigación existe; faltaba trasladarla al modelo visible.
