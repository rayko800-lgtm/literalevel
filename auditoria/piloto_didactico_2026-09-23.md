# Piloto didáctico — catálogo completo y acabado

Estado histórico del catálogo aprobado. La versión posterior del corte y el enlace vigente están en `anatomia_didactica_2026-09-23.md`.

23 sep 2026. Rama `dev/articulacion-v2`, base `0421f0d`. Miguel aprobó /i f v/ y autorizó extender al resto y mejorar realismo. Nico es único editor; agente de revisión solo lectura. `front/angular.json` ajeno, conservado.

## CONFIRMADO

- Correcciones extendidas a las familias del catálogo: 46 sonidos y siete variantes británicas. No se cambió el modelo fonético/audio ni el 2D.
- Redondeadas /u w ʊ ɔ/ y destinos de diptongos: orificio oval, proyección contenida y distinta abertura según mandíbula. /u/ es más estrecha que /ʊ/.
- Neutros articulados /t d k ɡ n ŋ l h/, vocales neutras y dentales ya no heredan el sello del reposo. Dos canales adicionales se interpolan con las poses y solo afectan al modelo didáctico.
- El borde regular sigue el mismo giro que el cuerpo del labio inferior. Corrige el estiramiento excesivo en /æ ɑ/ sin perder el cierre /p b m/.
- /θ ð/: el labio inferior acompaña menos al hueso para mostrar la punta sin exponer toda la base lingual. La geometría de lengua y su contacto interno conservan los ajustes previos.
- Acabado: variación tonal del bermellón, rugosidad distinta piel/labios, relieve superficial fino. Se redujo el relieve exagerado de papilas en el piloto. Desde fuera, el tejido lingual profundo se atenúa para leerse dentro de la cavidad; el corte conserva iluminación clara. Es una aproximación visual, no simulación volumétrica ni fotorealismo.
- Demo completa por grupos: Vocales, Consonantes, Diptongos y Variantes británicas. Mantener gesto, Ver movimiento y Gesto final para diptongos. Se verificaron las leyendas de los 53 controles (barrido en dos tramos tras timeout de la herramienta, sin fallo de app).

## Verificación

`medir_didactica.mjs --completo --exigir`: **2227 estados**, 54 fijos (incluido reposo) y 2173 muestras de ciclos. Runtime real, incluida la nueva deformación de piel y todos los destinos incrustados. Exige abertura en neutros y contraste de redondeamiento.

- Cierre máximo: 0.000007391 unidades del modelo.
- Distancia /f v/ a incisivos centrales 0.0020244, laterales 0.0054010. Se conservó el contacto del piloto aprobado.
- Cero vértices labiales dentro de las 24 coronas convexas. NO es una prueba completa de intersecciones de superficies ni validación anatómica clínica.
- Ancho del borde: /i/ 2.5544, /ʊ/ 1.13712, /u/ 0.618. Abertura vertical /u/ 0.206 frente a /ɑ/ 1.6961. Son unidades de diseño, no milímetros.
- `medir_lengua.mjs --exigir`: volumen dentro de ±10 % en 54/54 poses; criterio de grosor de punta pasa en 47/54 donde corresponde. No se reesculpió la lengua.
- TypeScript OK; 129/129 pruebas Boca3D; build Angular OK, aviso CSS previo +639 B. `git diff --check` OK.
- Navegador: 390×844, ancho útil/contenido 375/375, sin overflow horizontal. Capturas de familias y extremos /aʊ/, frontal y perfil; consola sin errores. Muestreo visual representativo, no revisión clínica de cada fonema.
- Fluidez indicativa del build final: 59.1 callbacks de animación/s (237 en 4 s), reproducción en bucle, modelos ya cargados, sombras desactivadas. Guarda inicial 59.6. Navegador de escritorio con viewport móvil, NO teléfono Android ni medición GPU formal.
- Revisor independiente: /ʊ/ ya no se lee como protrusión lingual; /θ/ suficiente como ilustración, aunque persiste cierto aspecto de bloque. No detectó impedimentos en esas dos capturas finales.

## Artefactos y reproducción

GLB `build/boca_didactica/cara.glb`, 1 581 604 B; Blender editable `cara.blend`, 6 370 648 B. SHA-256 GLB local/remoto: `1D1017AB2213A86EB3FDEA96C334CCCDBF234596471212AD56CF50CB8F0F0328`.

Medidas: `inventario-medidas.json`; lengua: `lengua-inventario.json` (salida JSON primera línea y resultado textual segunda línea). GLB aprobado anterior y métricas preservados en `aprobado_ifv/`; el script allí es una copia del inicio de edición del inventario, no garantía de reproducción del GLB anterior.

```powershell
& 'C:\Program Files\Blender Foundation\Blender 2.93\blender.exe' -b --python tools/boca3d_blender/cara_didactica.py
node tools/boca3d_demo/medir_didactica.mjs build/boca_didactica/cara.glb build/boca_didactica/inventario-medidas.json --completo --exigir
node tools/boca3d_demo/medir_lengua.mjs tools/boca3d_demo/lengua.glb --exigir
```

Capturas en workspace de Nico `evidencia-blender/`: `inventario-ae-corregido.png`, `inventario-a.png`, `inventario-th-final.png`, `inventario-uh-final.png`, `catalogo-au-inicio.png`, `catalogo-au-final.png`. Las anteriores a final reflejan etapas previas de material; no tratarlas como todas capturadas del mismo build.

## TEMPORAL / NO INTEGRADO

https://commercial-rep-exposed-loaded.trycloudflare.com/?didactica=1&inventario=1&s=u&ciclo=0&sombras=0&velocidad=0.5

Muestra sin audio, cinco assets permitidos, ~1.20 MB comprimidos. Servidor 8769, exec 87031; túnel exec 94879, hijo 41580, límite aproximado 16:30 CDMX. No commit, push, despliegue ni sustitución de GLB de producción.

## Límites siguientes

Anatomía aún ilustrativa. Corte sagital mantiene la malla anterior y no comparte toda la silueta labial nueva. Falta integrar superficies interior/exterior con continuidad al girar, revisar aspecto de bloque lingual en dentales, validar en teléfono real y en app con audio. Un salto al fotorrealismo requiere remodelado/texturas anatómicas de mayor calidad y evaluación de coste móvil. El barrido numérico no sustituye esas revisiones.

Referencias: [Seeing Speech](https://www.seeingspeech.ac.uk/ipa-charts/), [Blender/glTF PBR — Khronos](https://www.khronos.org/blog/blender-gltf-i-o-support-for-gltf-pbr-material-extensions). El formato de exportación y el visor deben soportar los materiales; no todo efecto de Blender se conserva automáticamente.
