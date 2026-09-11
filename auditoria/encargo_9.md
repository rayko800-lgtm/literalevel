# Encargo 9 — el de Codex, partido en trozos que quepan

Escrito el **jueves 10 de septiembre de 2026** por la noche. Sustituye a
`encargo_7.md` en la parte de Codex; la de Fable ya se hizo (informe 11) y la 13
la cerró Fable sola.

---

## Lo primero: para el fin de semana, Codex NO llega

El cupo vuelve el **martes 15 de septiembre a las 8:46**. El fin de semana
empieza el **sábado 12**. Son tres días de diferencia, así que **ningún encargo
de Codex puede participar en la entrega del fin de semana**, con créditos o sin
ellos.

Eso deshace el miedo de raíz: **no hace falta comprar nada.** El cupo se recupera
solo, gratis, y para cuando se recupere el trabajo del fin de semana ya estará
hecho. Lo de Codex es un repaso *posterior*, no una dependencia.

Y comprobado hoy con una llamada de una palabra: **el cupo es de la cuenta, no
del modelo.** `gpt-5.6-sol` da el mismo error y la misma hora de vuelta que
`gpt-6-astra`. Cambiar de modelo no compra otra auditoría.

---

## Por qué se parte, y cómo

El 9 de septiembre un encargo «estrecho y bien dimensionado» murió tras **9.981
tokens sin emitir un solo hallazgo**. No fue el tamaño: el cupo ya estaba
agotado. Pero la lección de diseño vale igual, porque el cupo que haya el martes
tampoco se conoce:

> **Cada trozo tiene que valer por sí solo.** Si el cupo muere después del
> primero, el primero ya tiene que haber dejado un informe útil. Un encargo
> grande que muere a mitad no deja nada.

Así que van **cuatro trozos, en este orden**, y cada uno escribe su propio
archivo. Se lanzan **de uno en uno**, comprobando el cupo antes de cada uno con
una llamada de una palabra. Si el cupo aguanta, se sigue; si no, se para y lo que
haya quedado ya sirve.

Lo mecánico que yo puedo barrer con un `grep` **no va aquí**: sería regalarle el
cupo a un trabajo que no necesita juicio.

---

### Trozo 1 — las cifras del documento contra el código (el más valioso)

Informe a `auditoria/informe_codex_6.md`.

> Eres auditor externo. **No abras `auditoria/`** salvo para escribir tu informe.
>
> En `entrega/documento.md` y `entrega/estrategia.md` hay cifras medidas. Para
> **cada** cifra de las secciones 7 (validación) y 8 (producto), comprueba que el
> guion que se cita al lado la produce de verdad: ejecútalo o lee el código que
> la calcula. Interesa lo que **no cuadra**, y da igual si el que está mal es el
> documento o el guion.
>
> Usa `grep` para localizar; no leas archivos enteros.
>
> Formato por hallazgo: cifra publicada, dónde, qué dice el código, y cuál de los
> dos hay que cambiar. Al final, la lista de las que sí cuadran, porque sin eso
> no se distingue lo revisado de lo no revisado.
>
> No corrijas nada. Solo el informe.

**Por qué primero:** es lo único que un profesor puede comprobar él mismo con el
repositorio delante, y es donde un error cuesta nota directa.

---

### Trozo 2 — el cuadernillo, celda por celda

Informe a `auditoria/informe_codex_7.md`.

> `entrega/notebook_proyecto.py` es la fuente del cuadernillo que se entrega
> (`.ipynb` se genera de ahí con `tools/a_notebook.py`).
>
> La rúbrica exige que corra **en un Colab limpio sin errores ni warnings**.
> Busca lo que lo impediría: una celda que dependa de otra que va después, una
> ruta local, un archivo que solo existe en el disco del autor, una dependencia
> sin instalar, una salida que se imprima como aviso.
>
> No hace falta ejecutarlo entero: léelo en orden y di qué celda rompería y por
> qué.

---

### Trozo 3 — la prosa entregable

Informe a `auditoria/informe_codex_8.md`.

> Lee `entrega/documento.md` y `entrega/estrategia.md` buscando **solo** tres
> cosas, que son las que se califican:
>
> 1. Frases que quedaron a medias de una edición anterior —les falta el sujeto,
>    el verbo, o empiezan con el final de otra frase—.
> 2. Afirmaciones que el propio documento contradice más adelante.
> 3. Ortografía y concordancia.
>
> Cita `archivo:línea` y la frase literal. No reescribas el documento: señala.

---

### Trozo 4 — lo que quede, a ciegas

Informe a `auditoria/informe_codex_9.md`.

> Mira `app/*.py` con una sola pregunta: **¿qué le pasaría a un visitante que no
> sabe nada de esta aplicación y hace lo que no debe?** Pegar un texto vacío,
> subir un archivo que no es un libro, pulsar dos veces seguidas, entrar con una
> contraseña mal copiada.
>
> El módulo declara que **ningún manejador levanta una excepción hacia Gradio**.
> Busca uno que sí.

---

## Cómo se lanza cada trozo

```bash
# 1. el cupo, ANTES de escribir o lanzar nada
codex exec -m gpt-6-astra --sandbox read-only "Responde solo con la palabra LISTO"

# 2. si contesta LISTO, el trozo (y solo uno)
codex exec -m gpt-6-astra --sandbox workspace-write -C C:/Users/laura/literalevel "<el texto del trozo>"
```

`--sandbox read-only` para la comprobación de cupo y `workspace-write` para el
trozo, porque tiene que poder escribir su informe. Si el cupo cae a mitad, el
error lo dice y **no se reintenta en caliente**: se apunta la hora de vuelta.
