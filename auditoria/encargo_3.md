# Encargo: auditoría del documento final, apartados 7 a 11

Eres un **auditor externo**. No escribiste nada de esto y no tienes que ser
amable. Trabajas en `C:\Users\laura\literalevel`. **No modifiques ningún
archivo del proyecto.** Tu única salida es `auditoria/informe_codex_3.md`.

> **No abras nada dentro de `auditoria/`** salvo para escribir tu informe. Ahí
> hay revisiones ajenas; leerlas te haría buscar lo que otro ya buscó.

## Alcance: UN archivo, CUATRO apartados. Nada más.

Audita **solo** `entrega/documento.md`, y dentro de él **solo** los apartados
**7 (resultados), 8 (decisiones), 9 (limitaciones) y 10-11 (conclusiones)**.

Esto es deliberado y va en serio. Tres encargos anteriores con alcance amplio
**se quedaron sin presupuesto en la fase de lectura y no llegaron a escribir ni
una línea de informe**. Prefiero cuatro apartados auditados a fondo que el
documento entero sin auditar.

Si ves algo fuera de ese alcance, anótalo al final en una lista de una línea por
asunto, bajo «fuera de alcance», y sigue.

## Cómo gastar el presupuesto

1. **Lee primero los apartados 9, 10 y 11** —limitaciones y conclusiones—. Ahí
   está lo que el proyecto afirma de sí mismo, y es donde más rinde mirar.
2. Para cada afirmación comprobable, **busca su respaldo hacia atrás**: en el
   apartado 7, en `app/scoring.py`, en `informe_velocidad.md`, en
   `entrega/datos_figuras/*.dat` o en `validar_local.py`.
3. **Usa `grep` para localizar**, no leas archivos enteros.
4. **Escribe el informe en cuanto tengas material sólido** y amplíalo si te
   queda margen.

## Qué buscar, por orden de daño

1. **Cifras sin respaldo**: números que aparecen en el texto y no están en
   ningún archivo de datos ni salen de ningún cálculo del repositorio.
2. **Cifras que se contradicen** entre estos apartados y el código o los `.dat`.
3. **Afirmaciones más fuertes que su evidencia**: «demuestra», «garantiza»,
   «nunca», «siempre», «el techo», «a priori», «ciego». Cada una de esas
   palabras merece que se compruebe qué la respalda.
4. **Conclusiones que el experimento no sostiene**: causalidad donde solo hay
   correlación, generalización a dominios no probados.
5. **Limitaciones que faltan**: algo que el apartado 7 revela y el 9 no
   reconoce.

## Formato

Cada hallazgo, cinco líneas:

```
[GRAVEDAD] Título de una línea
Dónde:      archivo:línea
Qué dice:   la cita literal
Por qué:    en qué falla, con el número o la regla concreta
Arreglo:    qué hay que cambiar
```

Gravedad **CRÍTICO / SERIO / MENOR / DUDA**, y sé estricto: un CRÍTICO que
resulta ser MENOR te quita autoridad sobre los demás.

## Reglas

- **En español.** Ordena por gravedad.
- **Ni un hallazgo sin ubicación ni sin cita.**
- **Verifica antes de afirmar.** Recalcula lo que se pueda recalcular.
- **Si una afirmación la comprobaste y se sostiene, dilo** en una lista corta al
  final. Sin eso no se distingue lo revisado de lo no revisado.
- **Usa DUDA** cuando no puedas verificarlo desde el repositorio.
- **No arregles nada.** Señala; el autor decide.
- Termina con **media página** de veredicto.
