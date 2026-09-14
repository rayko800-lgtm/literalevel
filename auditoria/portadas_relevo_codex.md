# Portadas: relevo de Codex, 13 de septiembre de 2026

## Estado real

Pipeline preparado y probado sin red; **no se han generado portadas con FLUX**,
no se han descargado pesos, no se ha conectado Colab ni publicado en el bucket.
No hay saldo confirmado. No declarar terminado el trabajo visual ni activar
la tanda durante la ausencia de Miguel.

Base revisada: `df68912`. Propiedad de este cambio: `tools/colab_portadas.py`,
su `.ipynb`, `pruebas_portadas.py` y este informe. No se toca el cambio ajeno
de `app/catalogo.py`, ni API ni Angular.

## Corregido

- Antes el saldo se comprobaba despues de cargar FLUX y generar 21 imagenes.
  Ahora autorizacion, saldo y tarifa actual positivos y finitos se comprueban
  antes de leer secretos o importar torch. Carga del modelo vuelve a comprobar
  la guarda. Abrir el notebook no preselecciona GPU.
- La tanda necesita saldo nuevo despues de medir, aprobacion visual y permiso
  separado de publicacion. `volcar` vuelve a comprobar ese permiso.
- Un JSON remoto sin ambos WebP en el mismo shard no cuenta como terminado.
  IDs de otras selecciones no reducen el presupuesto de la tanda actual;
  duplicados de la seleccion no generan dos veces.
- Las muestras locales compatibles se reutilizan en la tanda. Se comprueban
  ID, prompt, modelo, dimensiones, pasos, semilla, marca IA y WebP decodificables.
  Las escrituras usan reemplazo de temporales, con JSON ultimo.
- El ID admite solo `PG` mas digitos antes de construir rutas.
- La medicion guarda `medida.json` y no reutiliza tiempos cacheados como si
  fueran una medicion nueva. Repetir esa celda con muestras locales se detiene;
  conservar `MEDIDA` para pasar a tanda o medir en otra carpeta explicitamente.
- Hay frenos de tiempo entre imagenes durante medicion y tanda. **No son un
  limite de facturacion de Colab**: una inferencia, carga o subida ya en curso
  puede excederlos, y una GPU conectada sigue consumiendo hasta desconectarla.

## Verificacion local

`C:\Users\laura\anaconda3\python.exe -X utf8 pruebas_portadas.py`: **11/11**.
Incluye ejecucion de `generar` con pipeline simulado y Pillow real: dos
consultas de la misma fila hacen una sola inferencia, y archivos parciales,
WebP corruptos y un prompt distinto invalidan la cache. Tambien ejecuta la
celda real de configuracion bloqueada y la guarda real de publicacion.
Comprueba sincronizacion de todas las celdas `.py`/`.ipynb`.

Recalculado con pandas sobre `catalogo_medido.csv` local y `seleccionar` actual:
**1.200 seleccionados, 746 con motivo tematico y 454 con motivo generico**.
No se ampliaron los motivos sin una revision editorial de los temas y muestras.

## Pendiente para Claude

1. Confirmar saldo y tarifa actual en Recursos con Miguel antes de conectar
   A100. No usar el antiguo valor fijo de 15 unidades/h como tarifa actual.
2. Confirmar permiso para generar las 21 muestras, elegir minutos autorizados,
   ejecutar las celdas y revisar visualmente las imagenes, no solo los prompts.
3. Revisar las 454 portadas de motivo generico y ajustar temas donde haga falta.
   El filtro de nombres del gancho sigue siendo heuristico, no una garantia
   absoluta de ausencia de nombres; la imagen puede incumplir el prompt.
4. Aprobar muestras, confirmar saldo restante en la celda Tanda y autorizar
   publicacion explicitamente. Desconectar la GPU al terminar o detenerse.
5. Probar contra Hugging Face la subida real, permisos, rutas y reanudacion.
   El listado remoto acredita presencia, no integridad, version de prompt ni
   contenido de archivos; esos aspectos no se verificaron en remoto.
6. Verificar API y Angular con assets reales y marca IA. No se verificaron
   cambios visuales de las portadas porque todavia no se generaron.

`SOBRECARGA=1.3` sigue siendo una estimacion heredada, no un rendimiento medido.
La duracion GPU y la de extremo a extremo deben distinguirse al reportar costes.
No se audito compatibilidad del entorno FLUX ni licencia/precios actuales con
fuentes externas; se conservaron las elecciones de Claude y no se lanzaron.

Para regenerar el notebook, usar `tools/a_notebook.py tools/colab_portadas.py`
y retirar de sus metadatos `accelerator` y `colab.gpuType`: el conversor generico
del repo los agrega. La prueba de sincronizacion exige que no reaparezcan.
