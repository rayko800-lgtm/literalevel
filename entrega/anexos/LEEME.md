# Cuadernos de la entrega final

El cuaderno evaluable del Módulo 5 es [`../notebook_proyecto.ipynb`](../notebook_proyecto.ipynb). Los otros tres cuadernos son anexos técnicos para documentar cómo se obtuvo el modelo v4, el catálogo y los gestos de Eos. No son pasos necesarios para ejecutar el cuaderno evaluable ni para usar la aplicación.

| Cuaderno | Función | Verificación del 29 sep 2026 | Límite para reproducirlo |
|---|---|---|---|
| `../notebook_proyecto.ipynb` | Resultados y análisis evaluables | Colab CPU: 57/57 celdas de código, sin salidas de error, dos ejecuciones | Apareció un aviso del entorno sobre `HF_TOKEN`; se omitió el permiso porque el modelo es público. |
| `../LiteraLevel_V4_reproducible.ipynb` | Reproducción del modelo v4 congelado | 11/11 celdas de cálculo ejecutadas localmente en modo `verify`; 144 documentos y métricas concordantes con los resultados esperados; sin excepciones | La celda restante instala dependencias en Colab. En Colab no se completó el montaje de Drive porque pedía un permiso amplio; no se afirma una ejecución íntegra allí. Requiere acceso al [paquete de datos del modelo](https://drive.google.com/drive/folders/1azhceQzk3cEHZkESe26QIzrMSbDTak2T) y situarlo bajo la ruta `MyDrive/literalevel_bigdata/entrega_profesor_v4`, o cambiar `LITERALEVEL_DELIVERY_ROOT`. |
| `colab_precalculo.ipynb` | Precálculo del catálogo de producción | Sintaxis de 17/17 celdas de código y estructura del notebook; sin errores guardados | No ejecutar todas las celdas: requiere `HF_TOKEN`, acceso a los datos y lanza un lote de hasta 3.5 horas. No se repitió ese lote para esta entrega. |
| `eos_v3_no_verbal.ipynb` | Entrenamiento de gestos no verbales de Eos | Sintaxis de 3/3 celdas de código y estructura del notebook; sin errores guardados | Requiere datos en Drive y GPU; la ejecución completa entrena en segundo plano. La boca final de Eos usa Audio2Face; las pruebas de boca de este cuaderno no describen la versión final. |

El cuaderno histórico `LiteraLevel_v4_entrenamiento.ipynb` y los pilotos `fusion.ipynb` y `voz2cara.ipynb` no se incluyen: contienen exploración previa y no son la fuente limpia de esta entrega.

**Regla de lectura:** la verificación de sintaxis confirma que el código se puede analizar, pero no demuestra que una ejecución completa termine. El único cuaderno exigido por la rúbrica como entrega reproducible es `notebook_proyecto.ipynb`.
