# Mensaje para el profesor — adelanto de LiteraLevel

Para WhatsApp o correo. Está en **usted**; si con él se tutean, cámbialo y ya.

> **Antes de mandarlo:** comprueba que el enlace abre desde tu móvil. Si la
> computadora está apagada, el enlace está muerto — y que el profesor se
> encuentre eso es peor que no mandárselo.

---

## Versión corta (WhatsApp)

Profe, buenas. Le comparto un adelanto de mi proyecto del módulo 5, **no como
entrega** — me gustaría saber qué le parece antes de seguir.

**LiteraLevel** ayuda a un hispanohablante a leer en inglés **al nivel que le
toca**. El modelo mide la dificultad de un texto, así que en vez de elegir un
libro a ciegas, la app le dice cuál puede leer y le dibuja la curva de
dificultad capítulo a capítulo.

🔗 **https://huggingface.co/spaces/MikeMaki1763/literalevel**
usuario: `invitado1` · contraseña: `074cfd6zbjy8pc`

Se entra arriba del todo, en «Entrar con tu perfil». El usuario y la
contraseña solo hacen falta para las tres cosas que llaman a un servicio
externo —explicar una palabra en su frase, el resumen de «¿de qué trata?»
y la corrección de pronunciación—; **el resto de la aplicación funciona sin
entrar**: medir un texto, buscar, leer el libro entero, la curva por
capítulos, el diccionario y la fonética.

**Ábralo desde el celular**, porque incluye lo de la pronunciación que usted
mencionó: en la pestaña *Pronunciación* se lee una frase en voz alta y la app
marca palabra por palabra qué sonó bien y qué no, explica cómo corregirlo y
genera el audio de cómo debería sonar. Necesita micrófono, por eso el celular.

Tres cosas que le quiero decir de una vez, para que no se lleve sorpresas:

1. **Está desplegado de verdad**, en Hugging Face Spaces, y no depende de que
   yo tenga la computadora encendida. Va sobre el hardware más barato: si
   lleva días sin visitas, el primer arranque tarda unos 30 segundos.
2. **El catálogo que ve es el chico** (1.197 libros, y solo se abren los de
   Project Gutenberg). Ahora mismo estoy midiendo los **61.642 libros en
   inglés** del catálogo completo con el modelo leyendo cada libro entero; van
   unas 6 horas de GPU.
3. **Las consultas de palabra y de voz usan la API de OpenAI y las pago yo**,
   así que están limitadas a 12 y 4 por hora. Si se topa con el límite, es
   eso y no un error.

Lo que más me interesa de su opinión es **la usabilidad**: si se entiende sola,
qué le estorba, qué sobra. Mi prima de 15 años la probó y me dijo *"está bien
difícil de usar en celular"*, así que ya cambié varias cosas — pero seguro se
me escapan más.

Gracias, profe.

---

## Si prefiere correo, añade esto al final

También le puedo compartir el repositorio y el cuaderno si quiere ver el
código; el cuaderno corre completo en Colab sin configuración.

---

## Notas para ti, Miguel (no las mandes)

- **No digas "chat de voz".** No es conversación libre: es corrección de
  pronunciación sobre una frase concreta. Es lo que él pidió —practicar
  pronunciación— pero prometer un chat y entregar otra cosa se nota.
- **Menciona el precálculo.** Estar a mitad de un trabajo de 6 horas de A100
  sobre 61.642 libros no es una excusa por lo que falta: es la clase de cosa
  que su propia rúbrica valora.
- **Pide opinión de usabilidad, no del modelo.** El módulo declara que evalúa
  *"hacer que esos modelos sean accesibles y valiosos para un usuario final"*.
  Preguntar justo por eso demuestra que leíste la rúbrica.
- **Lo de Esmeralda va a propósito.** Un ciclo de usuario real —crítica,
  diagnóstico, corrección— vale más ante un evaluador que cualquier métrica, y
  además te deja preguntar sin parecer inseguro.
- Si te contesta con críticas, **anótalas literales**. Sirven para la sección
  de estrategia del documento, igual que sirvieron las de tu prima.
