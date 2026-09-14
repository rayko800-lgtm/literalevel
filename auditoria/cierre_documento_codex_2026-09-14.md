# Cierre documental de Codex: 14 de septiembre de 2026

## Alcance

Sin entrenamiento, llamadas de pago, publicacion ni envio al profesor.
Archivos: `entrega/documento.md`, `.tex`, `.pdf`, `estrategia.md` y
`mensaje_profesor.md`. Se conservaron las modificaciones ajenas del repositorio.
Las metricas del modelo y los archivos de figuras no se cambiaron.

## Cambios

- Resumen Markdown y LaTeX coinciden en Angular + FastAPI, con Gradio como
  motor/respaldo. El enlace principal apunta al dominio `.static.hf.space`.
- Las pruebas de Esmeralda/Laura se identifican como ciclos de la interfaz
  anterior; no se atribuyen a toda la migracion Angular.
- Se sustituyen garantias falsas: un esquema estructurado no garantiza
  veracidad, los adaptadores API tambien contienen reglas y una bateria de
  pruebas no prueba ausencia universal de excepciones.
- El contrato del diccionario refleja el fallback marcado como IA cuando no
  existe acepcion utilizable. No se redefine una acepcion de Kaikki existente.
- Estado fechado: API 32/35 en entorno aislado; tres casos sin validar por
  dependencias NLP ausentes. Se separan voz concurrente 7/7, despliegue 10/10
  y portadas 11/11. No se afirma haber reejecutado toda la suite en este cierre.
- Se incorpora el limite observado con `house` y se distingue disponibilidad
  remota de calidad semantica y de prueba de microfono fisico.
- A6 queda cerrado por sustitucion del catalogo heredado, no por eliminacion
  realizada ahora. Se prioriza ensayo Angular/voz, usuarios y grabacion.
- Portadas y Blender llevan un corte explicito: pipeline sin imagenes FLUX
  nuevas y demo 3D local, no una afirmacion de integracion/publicacion terminada.
- Mensaje al profesor rehecho como borrador, sin enviar ni incluir credenciales;
  ya no afirma que el catalogo chico sea el actual o que siga a medio precalculo.

## Evidencia comprobada

- Lectura de `app/api.py` por AST: 37 rutas HTTP decoradas bajo `/api`.
- pandas sobre `catalogo_medido.csv`: 53.179 filas, 53.179 IDs unicos y suma
  de `capitulos` = 585.111. No se repitio la inferencia del catalogo.
- `auditoria/despliegue_codex_2026-09-13_noche.md` acredita el backend
  `e56cf08`, cotejo por hash y comprobaciones remotas indicadas; este cierre
  no las convierte en una nueva prueba en produccion del 14 de septiembre.
- `auditoria/portadas_relevo_codex.md` y el relevo nocturno conservan limites
  y pruebas de portadas/Blender. No se consultaron secretos.

## PDF

Compilado con `D:/tex/bin/tectonic.exe -X compile documento.tex --keep-logs`,
`TECTONIC_CACHE_DIR=D:/tex/cache`. Salida: **52 paginas**.
Se instalo PyMuPDF 1.28.2 solo en el venv aislado de despliegue, no en Anaconda.

- Cero referencias `ref/eqref` sin etiqueta y cero `??` en texto extraido.
- Sin barras LaTeX corrompidas ni caracteres de sustitucion en el PDF.
- Todas las paginas renderizadas; revisadas en cinco hojas de contacto y
  detalle de resumen, arquitectura, estado y accionables. Sin texto recortado
  ni solapamientos visibles. Ninguna linea fuera del umbral de margen
  65 pt a ancho de pagina menos 66 pt en la comprobacion geometrica.
- Se corrigieron desbordes de la tabla de modelos y cadenas de codigo.
  Restan cuatro avisos menores de TeX, maximo 2,791 pt, sin recorte visible.
  Se conservan avisos previos de Fontconfig y ancla de pagina duplicada;
  no impiden leer el PDF. No se afirma compilacion sin warnings.
- `git diff --check` sin errores en las fuentes editadas.

## Limites y siguiente paso

Falta grabar video, ensayo con microfono real y nuevos usuarios Angular.
La integracion 3D que el coordinador esta verificando requiere su propio
cierre antes de modificar el estado documental. No se presento como terminada.
No se reauditaron tarifas actuales, literatura cientifica ni metricas pesadas;
las cifras historicas siguen con su contexto original. Los otros entregables
se sincronizan por separado para no mezclar propiedad de presentacion y guion.

## Ampliacion: documentos operativos y notebook

Con autorizacion del coordinador se actualizaron tambien `README.md`,
`PENDIENTES.md`, `DESPLIEGUE.md` y exclusivamente las celdas narrativas de
`entrega/notebook_proyecto.py`, regenerando su `.ipynb` con el conversor del repo.

- README distingue arranque API en 8000 + Angular con proxy en 4200 del
  respaldo `main.py` en 7860. Las rutas y scripts se leyeron en el codigo,
  no se lanzaron servidores para este cambio documental.
- PENDIENTES distingue el corte actual del historial de cuotas/auditorias.
  Corrige el comando de comparacion: sin `--seco`, desplegar_app publica.
- DESPLIEGUE ya no declara pendiente la persistencia resuelta. Documenta
  seleccion exacta `--solo`, revision padre, bytes escaneados, comprobacion
  JSON y limites de publicacion del front. Conserva precios como historicos.
- Notebook: **103 celdas, 57 de codigo**. Comparacion estructurada con HEAD
  anterior: las 57 celdas ejecutables son identicas byte a byte en su fuente.
  Todas pasan `ast.parse` tras excluir magias; no se ejecutaron ni entrenaron.
  Las 103 celdas coinciden exactamente con `tools.a_notebook.celdas(py)`.
- `tools/contar_guion.py`: 480 palabras habladas, 3:12 a 150 ppm sin pausas;
  presentacion: 14 paginas, leida con PyMuPDF. Archivos de otro agente,
  commit `13281a9`; no se modificaron en este encargo.

La documentacion del despliegue 3D definitivo queda a cargo del cierre
coordinado cuando haya evidencia publicada, no de una suposicion documental.
