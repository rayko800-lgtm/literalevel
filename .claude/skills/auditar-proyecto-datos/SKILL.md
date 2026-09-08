---
name: auditar-proyecto-datos
description: Auditar de forma externa un proyecto de ciencia de datos y su documentación — buscar cifras que no cuadran, afirmaciones sin respaldo, fugas de datos, métricas mal elegidas y conclusiones que el experimento no sostiene. Úsala al revisar un documento, un notebook o un modelo antes de entregarlo, propio o ajeno.
---

# Auditar un proyecto de ciencia de datos

El trabajo del auditor **no es opinar sobre el enfoque**, es comprobar si lo
escrito se sostiene. Un buen informe de auditoría se puede verificar entero: cada
hallazgo apunta a una línea concreta y dice por qué está mal.

> **La regla que lo ordena todo:** una afirmación solo cuenta como cierta si se
> puede rastrear hasta un número, un archivo o un experimento. Todo lo demás es
> una hipótesis con buena redacción.

---

## 1. Los seis frentes, por daño que causan

### (1) Fuga de datos — el que invalida el trabajo entero

Es el más grave porque no baja la nota: **la anula**, y suele pasar
desapercibido porque las métricas salen *mejores*.

- ¿La partición separa por **grupo** (participante, documento, libro, paciente)
  o solo por fila? Si el mismo sujeto aparece en train y en test, la métrica
  mide memoria, no generalización.
- ¿El preprocesamiento se ajustó **antes** de partir? Un `StandardScaler`,
  `TF-IDF` o imputación ajustados sobre todo el conjunto ya filtraron el test.
- ¿Alguna variable **contiene la respuesta**? Fechas posteriores al evento,
  identificadores correlacionados con la clase, agregados calculados con el
  target dentro.
- ¿La **lista de palabras, el vocabulario o el diccionario** se construyó con el
  propio conjunto de prueba? Es fuga sutil y frecuente en NLP.
- ¿El test se usó para **elegir** algo —umbral, época, hiperparámetro—? Entonces
  ya no es test; es validación, y hay que decirlo.

### (2) Cifras que no cuadran

Mecánico y rápido, y encuentra errores reales:

- **Suma los subconjuntos**: las particiones deben sumar el total; los
  porcentajes, 100 (±0,1 por redondeo).
- **Rehaz las divisiones** que aparecen en el texto. Una razón de aceleración,
  un porcentaje, una media.
- **La misma cifra en dos sitios**: busca cada número clave en todo el documento
  y comprueba que no cambia entre el resumen, el cuerpo y las conclusiones.
- **Documento contra código**: lo que dice el texto debe coincidir con lo que
  hace el notebook y con lo que hay en disco (tamaños de archivo, conteos).
- **Unidades y escalas**: MB frente a MiB, log natural frente a log10, escalas
  0–1 frente a 0–100.

### (3) Métricas mal elegidas o mal leídas

- ¿**Accuracy con clases desbalanceadas**? Sin la proporción de la clase
  mayoritaria al lado, no significa nada.
- ¿Se reporta **PR-AUC** cuando el positivo es raro, o solo ROC-AUC (que se ve
  bonito con desbalance)?
- ¿Hay **baseline**? Sin un modelo trivial —la clase mayoritaria, la media, una
  regla de tres— ninguna métrica se puede juzgar.
- ¿Regresión o clasificación **ordinal**? Si las clases tienen orden, un error
  de dos niveles es peor que uno de un nivel, y accuracy no lo distingue.
- ¿Se dan **intervalos o desviaciones**, o solo el punto? Una diferencia de
  0,01 entre modelos sin dispersión no es una diferencia.

### (4) Afirmaciones sin respaldo

Marca toda frase que afirme algo comprobable y no lo respalde. Los patrones
delatores: *«se sabe que»*, *«claramente»*, *«el estado del arte»*, *«mejora
significativamente»* (¿test estadístico?), *«en tiempo real»* (¿cuántos ms?),
*«escalable»* (¿probado hasta dónde?).

Caso especial y grave: **atribuir a un modelo propio una métrica que viene de
otro corpus, otra versión o la literatura.** Comprueba que cada número tiene un
experimento detrás y que es *este* experimento.

### (5) Reproducibilidad

- ¿**Semilla** fijada, y en todos los sitios (partición, modelo, shuffle)?
- ¿El código corre **de cero** en un entorno limpio? Rutas absolutas, archivos
  locales no publicados y dependencias sin versión lo rompen.
- ¿Los **datos** son accesibles, o solo existen en el disco del autor?
- ¿Las **versiones** de las bibliotecas están fijadas donde importa?

### (6) Conclusiones que el experimento no sostiene

- ¿La conclusión habla de **causalidad** cuando el diseño solo da correlación?
- ¿Generaliza a poblaciones, idiomas o dominios **no probados**?
- ¿Hay sección de **limitaciones**, y es específica o son fórmulas vacías?
- ¿Los **accionables de negocio** se derivan de los resultados, o son deseos?

---

## 2. Cómo se hace, en orden

1. **Lee las conclusiones primero.** Luego busca hacia atrás la evidencia de
   cada una. Es más rápido que leer en orden y encuentra más.
2. **Haz un inventario de cifras**: cada número del documento, con su ubicación.
   Después verifica cada uno contra su fuente.
3. **Contrasta documento contra código.** Las discrepancias entre lo que se dice
   y lo que se ejecuta son la mina más productiva.
4. **Busca lo que falta**, no solo lo que está mal: el baseline ausente, la
   limitación no reconocida, la métrica que convenía y no aparece.
5. **Comprueba lo verificable con las manos.** Si puedes abrir el archivo,
   ejecutar la celda o recalcular la división, hazlo. No lo supongas.

---

## 3. Cómo se escribe el informe

Cada hallazgo lleva **cinco cosas** y nada más:

```
[GRAVEDAD] Título de una línea
Dónde:      archivo:línea o sección
Qué dice:   la cita literal
Por qué:    en qué falla, con el número o la regla concreta
Arreglo:    qué hay que cambiar
```

**Gravedad**, y sé estricto al asignarla:

| | |
|---|---|
| **CRÍTICO** | invalida un resultado (fuga, cifra falsa, métrica que no mide lo que dice) |
| **SERIO** | debilita una conclusión o falta algo exigido (sin baseline, sin limitaciones) |
| **MENOR** | inconsistencia, redacción, formato |
| **DUDA** | no pudiste verificarlo; dilo en vez de callarlo o de inventarlo |

**Reglas del informe:**

- **Ordena por gravedad**, no por orden de aparición.
- **Ni un hallazgo sin ubicación.** «El documento exagera» no es un hallazgo.
- **Si algo está bien y podía estar mal, dilo.** Un informe que solo trae
  defectos no permite distinguir lo revisado de lo no revisado.
- **No reescribas el trabajo.** El auditor señala; el autor decide.
- **Separa lo que verificaste de lo que sospechas.** La categoría DUDA existe
  para eso y usarla es una virtud, no una debilidad.

---

## 4. Trampas del propio auditor

- **No confundas desacuerdo de criterio con error.** «Yo habría usado XGBoost»
  no es un hallazgo. «Se afirma que XGBoost fue peor sin reportar sus
  hiperparámetros» sí lo es.
- **No inventes cifras de referencia.** Si no sabes cuál es el estado del arte,
  di que no lo comprobaste.
- **Un número raro no es un error hasta comprobarlo.** Verifica antes de
  afirmar.
- **No premies la prosa.** Un documento bien escrito puede estar mal; uno torpe
  puede ser correcto.
