# Cierre de la auditoría 17 (Fable) — la pasada de regresión

Cerrado el **11 de septiembre de 2026**, de madrugada, sobre `950f4c9`. El
informe es [`informe_fable_17.md`](informe_fable_17.md): **1 crítico**, 2
serios, 1 menor y 3 notas, con 5 mutantes vivos de 19. El encargo, en
[`encargo_11.md`](encargo_11.md).

**Esta pasada no auditó el proyecto: auditó lo que yo había tocado.** El
encargo era un diff —`b6a7c21..HEAD`— y una sola pregunta: *¿qué has roto hoy?*
Salió cara y valió cada minuto.

---

## El crítico

### H1 · El recuadro rojo seguía saliendo, y mi arreglo estaba mal diagnosticado

Había dado el fallo por cerrado. **No lo estaba**, y el auditor lo reprodujo en
el Space con un caso que yo no había probado: leyendo el **capítulo 90** de
*Karamázov* y abriendo un libro de **24 capítulos**, sale
`Value: 89 is not in the list of choices: [0…23]`.

La causa está en una línea que **yo no había tocado**:

```python
est_libro.change(_indice_de, [est_libro, cap], indice)
```

Cuando cambia el libro, ese manejador leía también el desplegable de capítulos.
Los manejadores que abren un libro son **generadoras** y cambian `est_libro` y
`cap` a la vez, así que el evento se dispara con el valor **viejo** del
desplegable —el auditor lo midió en la traza de red: recibe `[null, 89]`—. Si
ese número no existe en el libro nuevo, `Dropdown.preprocess` lo rechaza.

**Y aquí está lo que yo no había entendido**, verificado leyendo
`gradio/components/dropdown.py`: el error se lanza **en `preprocess`**, es
decir, **antes de llamar a mi función**. Por eso la validación que había metido
dentro de `_indice_de` no podía servir de nada — la función no llegaba a
ejecutarse. Estuve dos intentos arreglando el sitio equivocado porque no había
mirado dónde nace el error.

Arreglado quitándole `cap` a las entradas de ese manejador: `est_libro` es un
`gr.State` y su valor vive en el servidor, así que ese sí llega al día. El
`cap.change` de al lado marca el capítulo, y ahí `cap` es el que dispara, no
una entrada rancia.

**Comprobado por mí en el Space**, con el caso exacto: capítulo 50 de
*Karamázov* → *Notes from the Underground*. Sin recuadro, abre en su capítulo 3
y la cabecera dice «24 capítulos · 44.069 palabras».

---

## Los dos serios, y los dos eran míos

### H2 · «Retomar donde lo dejé» tenía el mismo vaciado que quité del descargador

Arreglé un sitio y me dejé el otro, que es el mismo camino. Pintaba el recuadro
rojo **siempre** que ya había un libro abierto.

### H3 · «Leerlo ahora» sin elegir nada dejaba mandos vivos sobre un lector vacío

Mi cambio del día anterior dejó de vaciar el desplegable, pero seguía borrando
el libro, el texto y la ficha. Resultado: el desplegable lleno de capítulos de
un libro que ya no estaba. El comentario que escribí decía que eso quedaba
arreglado, y no.

Ahora esos caminos no tocan el lector: `gr.skip()` en todo salvo el aviso. Que
la descarga de otro libro falle no es razón para dejarte sin el que estabas
leyendo.

---

## El menor: cuatro mutantes que mis pruebas no distinguían

Los cuatro eran buenos, y uno era grave:

| Qué rompía | Por qué importaba |
|---|---|
| `value=… if valido else 0` | El índice marcaría el capítulo 1 de un libro que acabas de abrir por otro sitio |
| `_abrir` reconstruye sus etiquetas con otro formato | **Nadie comparaba los dos mandos.** «Dos vistas del mismo estado» era una promesa de un comentario |
| El **último** `yield` del descargador con el desplegable vacío | El paso estrella abriría el libro **sin desplegable ni índice**, y las siete suites en verde: ninguna pasaba por `_abrir_del_catalogo` |
| El rango de la ficha invertido | La prueba solo exigía que apareciera la palabra «entre» |

---

## Las tres notas

- **`LITERALEVEL_SIN_CLAVES=1`.** `config.cargar()` vuelca `CLAVES.txt` de la
  raíz en el entorno, así que la app local **sí** tiene clave aunque el entorno
  no la tenga. El auditor probó el camino «sin clave» desde la interfaz
  creyendo que no la había y **gastó una ronda de pago de verdad** —menos de un
  céntimo—. Vaciar el entorno no basta porque esta función lo vuelve a llenar.
  Ahora hay una variable para ensayar el modo degradado sin borrar el archivo.
- **«1 capítulos»** en la cabecera con un libro de un solo capítulo, mientras la
  ficha tres líneas más abajo decía «1 capítulo».
- **Mi banco de mutantes** contaba una viñeta de Markdown como fallo, porque
  buscaba líneas que empiezan por `- ` en toda la salida. Ahora solo mira las de
  después del titular de fallos. Un medidor que se equivoca hace parecer débil a
  una red que no lo es.

---

## La comprobación

`pruebas_extremas.py` sigue en **301** —las pruebas nuevas reforzaron las que ya
había en vez de añadir más— y las siete suites están en verde. Los **ocho
mutantes** de esta auditoría están en
[`tools/banco_mutantes.py`](../tools/banco_mutantes.py) con el prefijo `F17-`, y
**los ocho caen por su prueba**. El primer intento fueron 7 de 8: el del
singular sobrevivió porque ninguna prueba abría un libro de un solo capítulo.

---

## Lo que esta auditoría enseña, y no es sobre el código

Las tres veces que di el recuadro rojo por arreglado, lo que me delató fue
**volver a reproducirlo**, no volver a leerlo. Y la tercera causa apareció
cuando dejé de razonar y monté una prueba A/B —la misma pantalla con
`localStorage` limpio—.

Pero el diagnóstico bueno no salió de ahí: salió de **ir a leer dónde nace el
error**, en el código de Gradio. Dos de mis tres intentos fueron arreglos en el
sitio equivocado por no haber hecho eso primero.

Y la lección de encargo: **una pasada estrecha sobre un diff pequeño encontró un
crítico que una auditoría completa del día anterior no vio**, porque el diff no
existía todavía. Auditar lo que acabas de arreglar no es redundante; es donde
está el riesgo.
