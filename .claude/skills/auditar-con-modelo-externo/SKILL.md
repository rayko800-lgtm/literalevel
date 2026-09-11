---
name: auditar-con-modelo-externo
description: Encargar una auditoría a otro modelo (Codex/Astra, Fable) y aprovecharla bien — cómo dimensionar el encargo para que quepa en su presupuesto, por qué debe ir a ciegas, y qué hacer con lo que devuelve. Úsala al preparar una revisión externa de un proyecto propio, al escribir el encargo, o al recibir un informe de auditoría de otro modelo.
---

# Auditar con un modelo externo

Un auditor de otra familia de modelos encuentra cosas que tú no vas a encontrar,
porque tiene otros puntos ciegos. Eso es todo el valor, y se pierde entero si el
encargo está mal montado.

> **La regla que lo ordena todo:** un informe no es un resultado. Es una lista de
> hipótesis con ubicación. **Verifica cada hallazgo con tus manos antes de tocar
> nada** y antes de contárselo a nadie.

---

## 1. El encargo tiene que caber en la ventana de créditos

Es el error que más caro sale, porque falla **sin producir nada**.

**Medido el 8 de septiembre de 2026, con `gpt-6-astra` sobre este proyecto:**

| Encargo | Tokens | Resultado |
|---|---|---|
| Auditoría completa, «lee y señala» | 180.448 | Informe de 24 hallazgos, cupo agotado justo al acabar |
| Auditoría completa, «verifica ejecutando» | 151.193 | **Nada.** Murió leyendo, sin emitir un solo hallazgo |

Pedir más rigor sobre el mismo alcance **no cabe**. Ejecutar para verificar
multiplica el gasto por cada comprobación.

**Cómo dimensionarlo:**

- Un encargo de una sola tarea y alcance estrecho («solo coherencia de cifras
  entre archivos») cabe. Uno de «audítalo todo a fondo» no.
- Dile explícitamente que **use `grep` para ir al grano en vez de leer archivos
  enteros**. Sin esa instrucción se los lee.
- Dile que **si se queda sin margen, escriba el informe con lo que lleve**. Un
  informe a medias es útil; uno no escrito no vale nada.
- Parte en pasadas temáticas: coherencia de cifras, metodología, pruebas. Cada
  una con su ventana.

---

## 2. A ciegas, siempre

Si le cuentas lo que ya corregiste, tiende a confirmarlo: lee lo que espera
encontrar. A ciegas, **lo que vuelva a señalar es lo que sigue mal de verdad, y
lo que desaparezca es prueba de que se arregló**.

Dile explícitamente que **no abra el directorio de auditorías** salvo para
escribir su informe. Si no se lo dices, lee el informe anterior y te devuelve una
versión de él.

Un efecto secundario útil: cuando dos auditores de familias distintas coinciden
en un hallazgo, eso es corroboración independiente y vale más que dos avisos
sueltos.

---

## 3. Verifica todo, en las dos direcciones

Los auditores se equivocan por exceso y por defecto. Casos reales de este
proyecto:

- Un informe afirmó que reagrupar ventanas era **«exacto bit a bit»**. Medido:
  103 de 112 idénticas, el resto difería 4,8·10⁻⁷ por el relleno del lote. El
  arreglo era bueno; la justificación, falsa.
- Otro señaló como error un diccionario de valores «que no cuadran». Era una
  **columna de comparación puesta a propósito**, documentada en el README.
- Y un tercero encontró que una tabla publicada evaluaba un modelo **sobre sus
  propios datos de entrenamiento**. Cierto, verificable en tres líneas, y
  ninguno de los otros auditores lo vio.

Así que: ni te fíes, ni descartes. **Ve a la línea que cita y compruébalo.**

---

## 4. Que el informe se pueda usar

Exige el formato de `auditar-proyecto-datos`: gravedad, ubicación, cita
literal, por qué falla y cómo se arregla. Sin ubicación, un hallazgo no es
accionable y se convierte en una discusión de opiniones.

Pide además **una lista de lo que comprobó y estaba bien**. Sin eso no se
distingue lo revisado de lo no revisado, y acabas re-auditando lo mismo.

---

## 5. Cuando el informe llega

1. **Cuenta y clasifica** antes de arreglar nada.
2. **Verifica los críticos uno por uno**, tú, con el código delante.
3. **Mide el daño real.** Muchos hallazgos son ciertos y a la vez
   inconsecuentes: en este proyecto, una fuga de datos real movía la tercera
   cifra decimal, y la versión limpia salía *mejor*. Eso hay que medirlo, no
   suponerlo — y contarlo así, que es mucho mejor defensa que negarlo.
4. **Corrige, y deja escrito qué se corrigió y qué costaba.** «Encontramos una
   fuga, la medimos y aquí está la diferencia» vale más que una métrica bonita
   sin auditar.
5. **Vuelve a auditar a ciegas** cuando hayas cerrado todo.

---

## 6. Lo que cuesta cada auditor, para planificar

- **Codex / Astra** (`gpt-6-astra`, `gpt-5.6-sol`): cupo por ventana de tiempo.
  Al agotarse dice a qué hora vuelve. `gpt-6-spark` **no existe** para cuentas
  de ChatGPT. Una auditoría completa ronda los 150–180 mil tokens.
- **Fable**: se lanza como subagente con `model: fable`. Una auditoría completa
  de este proyecto costó 182 mil tokens y 39 llamadas a herramientas.

Programa la siguiente pasada para cuando el cupo se recupere en vez de
reintentar en caliente: reintentar sin cambiar el alcance falla igual.

---

## 7. Comprueba el cupo ANTES de escribir el encargo

El 9 de septiembre por la noche, un encargo estrecho y bien dimensionado para
Astra —solo coherencia de cifras, con instrucción de usar `grep`, esfuerzo
intermedio— murió tras **9.981 tokens**, sin un solo hallazgo:

```
ERROR: You've hit your usage limit. … or try again at Sep 15th, 2026 8:46 AM.
```

No fue un problema de dimensionado: el cupo ya estaba agotado antes de empezar,
y la ventana de recuperación era de **casi una semana**, no de unas horas. El
encargo estaba escrito, el fichero preparado y el tiempo gastado.

Así que antes de redactar nada, gasta una llamada mínima en preguntar si hay
cupo. Y cuando el error llegue, **apunta la hora exacta de vuelta**: es lo único
que permite programar la pasada siguiente en vez de reintentar en caliente, que
falla igual.

### Y cambiar de modelo no compra otra auditoría

El 10 de septiembre se probó: con Astra agotado, se lanzó la misma llamada de
una palabra a `gpt-5.6-sol`. **Mismo muro, misma hora de vuelta**, palabra por
palabra:

```
ERROR: You've hit your usage limit. … or try again at Sep 15th, 2026 8:46 AM.
```

El cupo es **de la cuenta de ChatGPT**, no del modelo: todos los modelos de
Codex comen del mismo. Así que ante un «usa el otro modelo, que ese está
agotado», la respuesta honesta es que no cambia nada — lo que desbloquea es
comprar créditos o esperar a la hora que dice el error. Comprobarlo cuesta una
llamada de una palabra; suponerlo cuesta el encargo entero.

Corolario de reparto: si solo hay un auditor disponible, dale el alcance
**amplio** y no el estrecho. Lo mecánico —que una cifra coincida consigo misma
en ocho archivos— lo puedes barrer tú con un `grep`; lo que no puedes hacer solo
es que alguien con otros puntos ciegos mire tu trabajo.
