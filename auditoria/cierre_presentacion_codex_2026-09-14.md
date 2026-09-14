# Cierre: presentacion y guion del diplomado

## Alcance

Encargo coordinado por la sesion central de Codex sobre el estado inicial
`58518d2`. Solo se editan los cinco entregables de presentacion/guion y este
informe. Documento y estrategia se trabajan por otro agente; no se modifican
app, front, cuadernos, AGENTS ni los datos del proyecto.

Se leyeron las skills `modulo-5-literalevel`, `latex-en-esta-maquina` y
`oratoria-ansva`, y las guias de presentaciones/PDF. Se conserva el formato
LaTeX existente, la identidad UNAM/FES, los graficos de datos y el formato 16:9.

## Cambios

- Angular es la interfaz entregada, FastAPI su frontera HTTP y Gradio el motor
  y respaldo. Se elimina el numero fijo de rutas para no confundir una cuenta
  puntual con un contrato estable durante la integracion de funciones nuevas.
- Diccionario y pronunciacion disponible salen primero; traduccion y
  explicacion contextual pertenecen a la etapa de IA. Se elimina la promesa
  de traduccion gratuita/completa en 40 ms.
- Se conserva el caso ilustrativo 1,20 frente a aproximadamente 1,70, sin
  atribuirlo a una persona real ni garantizar un resultado del cuestionario.
  Los recuentos historicos EPUB y TXT quedan diferenciados en preparacion,
  no mezclados en el parlamento ni prometidos como latencia del front.
- Se eliminan el precio operativo presentado como vigente y la afirmacion
  de que el producto ya consigue que los lectores dejen de abandonar libros.
  La siguiente validacion pedagogica queda como trabajo pendiente.
- Portadas FLUX y Blender 3D se describen como ampliaciones en preparacion.
  La demo narrada no depende de ellas. Root esta integrando 3D por separado;
  una publicacion posterior requerira actualizar ese estado, no inventarlo.
- Guion abreviado con ANSVA, requisitos MP4/cara visible/maximo cinco minutos,
  privacidad, preparacion del audio y respaldo explicitamente rotulado.

## Evidencia y cifras

- Arquitectura contrastada con `app/api.py`, `front/` y el relevo de
  despliegue ya existente; no se declara una nueva prueba del Space aqui.
- Las metricas del modelo se conservan como las publicadas en
  `entrega/documento.tex`: 0,908 interno; 0,860/0,807/0,668 en el contraste
  externo. Esta tarea no reentrena ni vuelve a evaluar el modelo.
- Catalogo medido: 53.179 libros y 585.111 capitulos segun la documentacion
  de cierre del catalogo y documento. El agente de documento corroboró las
  53.179 filas del CSV mediante lectura estructurada. La comprobacion propia
  de metadatos del Parquet no se pudo ejecutar por ausencia de pyarrow en
  Anaconda; no se presenta como un recuento nuevo de capitulos.
- 61.642 se rotula como objetivo de Gutenberg, instantanea del 7 de septiembre,
  no como total ya medido ni como suma con los corpus graduados.

## Verificacion

- `tools/contar_guion.py`: cinco parlamentos, **480 palabras** segun su regla
  oficial. Se comprobo que el texto hablado de Markdown y los cinco bloques
  `dice` de LaTeX coinciden exactamente al retirar sus marcas de formato.
- 480 palabras: 3:12 a 150 palabras/min o aproximadamente 3:42 a 130.
  Con hasta 55 segundos de acciones: aproximadamente **4:37**. Es presupuesto
  estimado, no una grabacion ni un ensayo realizado por Miguel.
- Tectonic compilo ambos PDFs con cache `D:/tex/cache`: **14 diapositivas** y
  **5 paginas de guion**. Los logs finales no contienen Overfull, referencias
  indefinidas ni caracteres faltantes. El aviso Fontconfig del entorno sigue
  siendo inocuo. Una pasada tuvo error Windows 1224 al escribir presentacion;
  se repitio con exito en un directorio temporal y se copio el PDF resultante,
  sin cerrar aplicaciones ni procesos ajenos.
- Poppler renderizo todas las paginas; se inspeccionaron en hojas de contacto
  y las diapositivas modificadas a mayor tamano. Se corrigieron solapamientos
  del pie y las notas. Las dos ultimas variaciones de tipografia/arquitectura
  se renderizaron e inspeccionaron otra vez en el PDF final.
- pypdf verifico texto en todas las paginas, presencia de Angular/FastAPI/MCER
  y ausencia de `??`. No se alteraron las series de datos de los graficos.

## Pendientes de entrega

Miguel debe ensayar y grabar el MP4 con su cara visible, probar el microfono
real y confirmar que la toma completa no supera cinco minutos. Antes de
grabar, comprobar el front y el JSON del backend, el libro abierto y los
valores que se diran en pantalla. No se han comprado servicios ni desplegado
estos documentos. Las pruebas completas de app son de otro encargo y no se
declaran aprobadas desde este cierre.
