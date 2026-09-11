# Cierre de la auditoría 16 (Fable) — hallazgo por hallazgo

Cerrado el **11 de septiembre de 2026**, de noche, sobre `b6a7c21`. El informe
es [`informe_fable_16.md`](informe_fable_16.md): 0 críticos, 6 serios, 4
menores, 3 notas y **5 mutantes vivos de 21**. El encargo, en
[`encargo_10.md`](encargo_10.md).

**Es la auditoría del día antes de grabar**, y por eso el encargo pedía dos
cosas que las anteriores no pedían: que **ejecutara el recorrido del guion** en
lugar de leerlo, y que **cronometrara cada paso**. Las dos dieron fruto: tres de
los seis serios solo se ven usando la aplicación, y uno de ellos no es un fallo
del código sino del reloj.

**Verificados los seis serios uno por uno antes de tocar nada.** Ninguno se cayó
al comprobarlo. El primero lo reproduje yo en el Space en vivo.

---

## Serios

### S1 · Un recuadro rojo de «Error» al abrir un libro desde el buscador — CERRADO

El peor, porque cae justo en el paso estrella de la demo.

```
Error ×
Value: 1 is not in the list of choices: []
```

**Reproducido por mí en el Space**, con un `MutationObserver` puesto antes de
pulsar: buscar «dostoyevski» → elegir *Crime and Punishment* → «Leerlo ahora».
El libro se abre perfectamente; lo que sale es un recuadro rojo de Gradio
encima.

La causa es una carrera entre dos manejadores del mismo componente. El índice
del libro tenía uno que ponía sus **opciones** (`est_libro.change(_indice_de…)`)
y otro que ponía su **valor** (`cap.change(lambda v: gr.update(value=v)…)`).
Abrir desde el buscador cambia `est_libro` y `cap` a la vez, así que el valor
podía llegar antes que las opciones —o traer el número de capítulo del libro
anterior, que tiene otros capítulos—.

Arreglado por los dos lados a la vez, que es lo que lo hace robusto en vez de
afortunado:

1. Los dos manejadores usan ahora `_indice_de`, que manda **opciones y valor
   juntos**. Ninguno puede poner un valor sin sus opciones.
2. `_indice_de` **valida el valor contra ESTE libro**: si el índice no existe en
   él —o llega como `None`, `"3"`, `-1`, `99`, `NaN` o una lista, que Gradio
   sabe mandar—, no se selecciona nada. Mejor sin selección que con una
   selección que no existe.

### S2 · «40 milisegundos» son en caliente: la primera consulta tarda ~55 s — CERRADO como nota de producción

El auditor lo cronometró: la primera consulta léxica de la sesión tardó **55 s**
(11:40:01 → 11:40:57) y la segunda **11 s**. No es un fallo: es la carga del
SQLite de 243 MB, spaCy y MiniLM, y `AGENTS.md` ya dice que los 40 ms son en
caliente. Lo que faltaba es que **el guion no lo decía**, y quien grabe se
encuentra con cincuenta y cinco segundos de silencio mientras afirma «cuarenta
milisegundos».

No se toca el código: cargar los modelos al arrancar está prohibido a propósito
—la app tiene que abrir rápido—. Lo que se hace es decirlo donde sirve: el guion
lleva ahora una nota de producción de **encender la aplicación y usarla antes de
grabar**.

### S3 · La ficha daba dos tiempos de lectura para el mismo libro y lector — CERRADO

Medido por el auditor sobre *Crime and Punishment* con perfil 1,20:

| | Tiempo que anunciaba |
|---|---|
| Primera apertura, sin la curva calculada | **18 h 52 min a tu ritmo de lectura** |
| Reapertura, con la curva ya medida (1,70) | **30 h 52 min (va por encima de tu nivel)** |

Doce horas de diferencia por el mismo libro y el mismo lector. `_ficha_libro`
decidía `exigente = nivel_libro > p.nivel + 0.15`, y cuando no hay análisis
guardado `nivel_libro` es `None`, así que `exigente` salía `False` **por
ausencia de dato** y se rotulaba «a tu ritmo de lectura»: una afirmación que la
aplicación no podía sostener todavía.

Ahora, con perfil pero sin medir el libro, da **el rango** —«entre 18 h 52 y
30 h 52, según lo que te cueste»—, igual que hace sin perfil. Medido el libro,
se moja: por encima avisa, por debajo da el ritmo cómodo.

### S4 · La pronunciación cobraba el cupo aunque no hubiera clave — CERRADO

El mismo fallo que ya se corrigió en `_consultar` —«con la clave caducada CADA
consulta descontaba un uso»— y que en `_practicar` se quedó sin corregir.
`_consultar` y `_de_que_trata` llaman a `_puede_pagar` **solo si hay clave**;
`_practicar` la llamaba siempre, y encima es la única de las tres que a
propósito no devuelve el uso.

Consecuencia real: un Space con perfiles y sin `OPENAI_API_KEY` —clave caducada
o borrada, que ya ha pasado aquí— descontaba un uso por cada intento de
pronunciación sin que saliera una sola petición. Ahora tiene la misma guardia
que sus dos hermanos y dice por qué.

### S5 · La pestaña pública «Estado» podía filtrar los nombres de usuario — CERRADO

La prueba del diagnóstico comprobaba que no se filtrara la **contraseña** y no
que faltara el **nombre de usuario**, así que invertir el `con_nombre=False` de
`problemas()` sacaba los usuarios configurados a una pestaña pública sin que
fallara nada. Es medio trabajo regalado a quien prueba contraseñas.

La prueba nueva exige las dos direcciones: que el nombre **no** salga en lo
público, y que **sí** salga en el registro del Space —si no, quien edita el
secreto a ciegas no sabría cuál arreglar—.

### S6 · El buscador no lo cubría ninguna prueba — CERRADO

El rescate por parecido ortográfico —lo que hace que «dostoyevski» mal escrito
encuentre a Dostoyevsky, que es **el paso 2 de la demo**— no lo probaba nadie.
Subir `_PARECIDO_NOMBRE` de 0,75 a 0,99 lo apaga y las 296 pruebas seguían en
verde. Igual el umbral de parecido: bajarlo a 0 hace que no se descarte nunca un
resultado flojo y el aviso de «ningún libro supera el umbral» no salga jamás.

La prueba nueva pone el parecido por **tema** a cero, de modo que lo único que
puede encontrar al autor sea el rescate del nombre. Sin eso se cumpliría sola.

---

## Menores

- **M1 · Los capítulos de §8.2 estaban en el `.md` y no en el `.tex`.** La app
  enseña «el 19, 1,52» y «el 36, 1,87», el `.md` también, y el PDF se quedó en
  «su capítulo más llevadero y su capítulo más exigente», sin números. Es el
  patrón de siempre: el `.md` corregido y el `.tex` sin corregir. Propagado y
  recompilado.
- **M2 · «clerk» sale con una acepción equivocada y marcada dudosa.** Cierto, y
  es la palabra que el guion manda tocar: en «petty clerks» el diccionario
  devuelve la acepción eclesiástica arcaica con afinidad 0,18. La IPA UK/US —que
  es lo que el guion quiere enseñar— sale bien. Queda como nota de producción:
  con perfil, la explicación de contexto la desmiente.
- **M3 y M4 · El separador de miles y el tope de la muestra.** Dos constantes
  que la aplicación enseña por todas partes («1.197», «203.699») y que ninguna
  prueba fijaba: volver a `format(int(n), ",")` daba «1,197» sin romper nada.
  Tres asertos en `pruebas_ficha.py`.

---

## Notas

- **N1 · Los «134 segundos» de la curva no se ven en vivo**, porque el Space la
  sirve desde la caché de `/data` y responde en 6 s. Es bueno para la demo y hay
  que saberlo: si el disco se limpiara, la primera medición serían dos minutos
  de silencio. En la nota de producción del guion.
- **N2 · Con el perfil puesto, *Crime and Punishment* sale el cuarto.**
  «dostoyevski» devuelve *The Idiot*, *Karamázov* y *Notes from the Underground*
  antes, porque la casilla «acercar a mi nivel» sube los B2 y el perfil del
  guion es 1,20. Lo medí yo también, y coincide. No es un fallo —el libro sale y
  se abre— pero hay que elegirlo sin dudar delante de la cámara. En el guion.
- **N3 · `PENDIENTES.md` iba otra vez por detrás**: decía que lo de la auditoría
  15 estaba sin subir cuando ya estaba subido y cotejado. Corregido, y con la
  frase que avisa de que esa línea es justo la que envejece.

Y un hallazgo del auditor **sobre su propio método**, que vale la pena guardar:
`pruebas_voz.py` usaba una ruta fija en el temporal del sistema, así que dos
ejecuciones simultáneas —que es exactamente lo que hace un banco de mutantes—
se pisaban el SQLite y daban un `PermissionError` que no tenía nada que ver con
lo que se medía. Un mutante podía parecer cazado por esa suite cuando lo único
que pasaba era eso. Las tres rutas cuelgan ahora de una carpeta propia por
ejecución.

---

## La comprobación

`pruebas_extremas.py` pasa de **296 a 301**, y `pruebas_ficha.py` suma tres
asertos. Los nueve mutantes de esta auditoría están en
[`tools/banco_mutantes.py`](../tools/banco_mutantes.py) con el prefijo `F16-`,
para que ninguno de estos seis arreglos se pueda deshacer en silencio.
