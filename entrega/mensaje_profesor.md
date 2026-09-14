# Mensaje para el profesor: adelanto de LiteraLevel

Versión revisada el 14 de septiembre de 2026. Borrador: no se ha enviado.

> **Antes de mandarlo:** abrir el enlace desde el móvil, comprobar lectura y
> acceso, y despertar el backend. El front estático y la API son servicios
> distintos: que cargue la página no demuestra que el motor esté disponible.
>
> **No escribir contraseñas en este archivo versionado.** Compartir el acceso
> de invitado por un canal privado y comprobarlo antes de la demostración.
> La credencial incluida aquí hasta el 10 de septiembre debe rotarse;
> borrar el texto del archivo no la elimina del historial de Git.

## Versión para WhatsApp o correo

Profe, buenas. Le comparto un adelanto de **LiteraLevel**, todavía no como
entrega final. Retomé su recomendación: la interfaz ahora está hecha con
**Angular**, separada del motor Python mediante una API.

**https://mikemaki1763-literalevel-front.static.hf.space/**

La idea es ayudar a elegir lecturas en inglés con una estimación de dificultad
antes de empezar. Se puede abrir un libro, ver cómo cambia la dificultad entre
capítulos y consultar palabras dentro de su frase. La escala es propia, de 0 a
2: **no certifica un nivel del MCER ni mide la comprensión del lector**.

El catálogo ya no es el adelanto de 1.197 registros. El archivo medido contiene
**53.179 libros de Gutenberg y 585.111 capítulos**, contados de nuevo el 14 de
septiembre. La recomendación excluye índices y materiales no literarios; no
todo el catálogo es adecuado para un principiante.

Puede probar lectura, búsqueda y diccionario sin entrar con una cuenta.
Para la explicación por IA, el resumen y la corrección de pronunciación le
comparto un acceso de invitado por separado: usan un servicio externo que
pago yo y tienen límites de uso. Si falta una palabra en el diccionario, la
definición por IA aparece identificada como tal.

En **Pronunciar** se lee una frase y se compara con lo que se transcribió;
no es un chat de voz ni una evaluación fonética de laboratorio. Conviene
probarlo desde un teléfono con micrófono. La última comprobación técnica no
incluyó una grabación con micrófono físico, así que quiero ensayar ese paso
antes de la demostración.

Lo que más me interesa de su opinión es **la usabilidad**: si se entiende por
dónde empezar, qué le estorba y qué falta. Dos lectoras encontraron problemas
en la interfaz anterior y esos comentarios guiaron los cambios; aún queda
volver a probar el recorrido completo de Angular con usuarios.

También puedo compartirle el repositorio y el cuaderno para revisar cómo se
obtuvieron las métricas. Las pruebas técnicas y lo que todavía no se ha
validado están separados en el documento, sin presentarlos como una garantía
de que toda la aplicación esté libre de fallos.

Gracias, profe.

## Notas para Miguel, no enviar

- El enlace principal es Angular. Gradio queda como motor y respaldo en
  `MikeMaki1763/literalevel`, no como la interfaz que se presenta primero.
- No prometer portadas FLUX terminadas: no hay imágenes nuevas generadas y
  falta aprobar la muestra. No presentar la demo local de Blender como una
  función publicada sin comprobar primero su integración con Angular.
- No repetir que el catálogo sigue a mitad del precálculo. El registro actual
  contiene 53.179 IDs únicos; el tamaño no demuestra calidad de recomendación.
- Ensayar la función de voz con micrófono real y acceso de invitado antes de
  la demo. La comprobación publicada del 13 de septiembre verificó lectura,
  diccionario local y rechazo de voz anónima, no corrección pagada.
- El video, con cámara visible y máximo cinco minutos, sigue siendo un
  entregable distinto del documento y del guion: falta grabarlo.
