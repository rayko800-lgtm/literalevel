# Mensaje para el profesor: entrega final de Pléyade

Versión del 26 de septiembre de 2026, para acompañar la entrega del 3 de octubre.
El adelanto del 16 de septiembre ya se envió; este es otro mensaje.

> **Antes de mandarlo:** abrir el enlace desde el móvil y comprobar que el motor
> responde (`https://mikemaki1763-literalevel.hf.space/api/salud` debe decir
> `"buscador_listo": true`). El front y la API son servicios distintos: que la
> página cargue no demuestra que el motor esté despierto.
>
> **Aquí no van contraseñas.** El usuario y la contraseña del profesor se mandan
> aparte, por un canal privado. Las contraseñas se cambiaron el 26 de septiembre:
> las del adelanto ya no sirven.

## Versión para WhatsApp o correo

Profe, buenas. Le comparto la entrega final del proyecto. La aplicación ahora se
llama **Pléyade**; el proyecto y el modelo siguen llamándose LiteraLevel, así que
verá los dos nombres. Como me recomendó, el front ya está en Vercel:

**https://pleyade-app.vercel.app**

Sigue siendo lo mismo: ayuda a elegir lecturas en inglés con una estimación de
dificultad antes de empezar, enseña cómo cambia la dificultad entre capítulos y
explica las palabras dentro de su frase. La escala es propia, de 0 a 2: **no
certifica un nivel del MCER ni mide la comprensión del lector**.

Desde el adelanto añadí:

- **Mi espacio**, la pantalla de inicio: el libro que dejó a medias, las
  palabras que consultó, las que le costó pronunciar y su progreso.
- **Repasar**: las palabras guardadas, con su frase, para recordarlas.
- **Una boca en 3D** en *Pronunciar*, que se mueve con un modelo entrenado con
  vídeos de caras reales. Tiene zoom, cámara lenta y giro libre.
- **Leer en voz alta en vivo**: en el lector, la aplicación sigue lo que usted
  va leyendo y marca las palabras que se saltó.
- **Datos por cuenta**: si entra con su usuario, sus libros, palabras y nivel se
  ven igual en el teléfono y en la computadora.

Sin cuenta puede leer, buscar, consultar el diccionario, medir su nivel y, en
*Pronunciar*, grabarse y escucharse. La explicación con IA, el resumen, la
corrección de pronunciación y la lectura en vivo necesitan cuenta, porque usan un
servicio de pago y tienen límites. Su usuario y su contraseña se los mando aparte.

Hay además topes por hora, que van por conexión y no por cuenta: 10 correcciones
de voz, 30 explicaciones, 6 resúmenes, 20 libros nuevos, 40 capítulos medidos y
6 curvas. Si le sale el aviso de tope, espere unos minutos; mientras tanto puede
seguir leyendo, buscar y consultar el diccionario.

El motor se duerme si pasa dos días sin visitas. Si la primera búsqueda tarda,
es que está despertando: en uno o dos minutos responde.

Con la entrega van el documento, la estrategia, el cuaderno de Colab, la
presentación y el vídeo. En el documento están separados lo que está medido y lo
que todavía no se ha validado con lectores.

Gracias por las recomendaciones de la revisión, profe.

## Notas para Miguel, no enviar

- El enlace principal es Vercel. El Space estático
  (`mikemaki1763-literalevel-front.static.hf.space`) sirve la misma aplicación
  de respaldo. Gradio sigue en `MikeMaki1763/literalevel` como motor y respaldo.
- **Eos** (la cara MetaHuman) está en desarrollo: no la menciones como
  terminada.
- Los topes son los de `app/ui.py:493-503` y `app/api.py:228-229` a fecha de
  `06a16db`. Si cambian, cambia este párrafo.
- La lectura en vivo solo se ha probado con una lectura sintética. Antes de
  enseñarla en la demo, pruébala con tu voz.
- El contraste del tema nuevo sobre la galaxia no se ha medido.
- Antes de mandar el mensaje, la cuenta del profesor tiene que tener cupo.
  `uso_openai.json` del bucket sigue sin ponerse a cero: lo tienes pendiente
  (HANDOFF).
