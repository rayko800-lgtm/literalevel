---
name: ritmo-de-trabajo
description: Cómo ejecutar una tarea larga sin quemar la tarde de Miguel — piloto antes que lote, juicio humano como constante y no como algoritmo, y un único artefacto por paso. Escrita el 20 sep 2026 comparando una sesión de Codex de 81 minutos con una sesión mía de seis horas y media sobre el mismo material. Úsala al empezar cualquier tarea que vaya a durar más de una hora o a tocar más de diez elementos.
---

# El ritmo de trabajo

Miguel pidió esto textualmente: *«el trabajo de Codex me gustó porque era
más eficiente; contigo estuvimos toda la tarde; investiga qué es diferente
a lo que hace él»*. Esto no es una impresión suya. Está medido.

## Lo que pasó, con números

Mismo proyecto, mismo día, mismo tipo de material (audio de fonemas).

| | Codex | Yo |
|---|---|---|
| Ventana | 12:10 → 13:31 (**81 min**) | ~14:30 → 21:00 (**6 h 30**) |
| Scripts `.py` dejados en el árbol | **8** | **34** |
| Sesiones de escucha pedidas a Miguel | 1 | 3 |
| Detectores automáticos intentados | 0 | ~7, casi todos fallidos |

Codex entregó en esos 81 minutos: un piloto completo, tres fonemas humanos
validados, 27 candidatos generados, manifiestos y validación técnica.

No es que Codex razonara mejor. Hizo **otra cosa**.

## Las tres diferencias reales

### 1. Codex nunca intentó automatizar un juicio

Ésta es la grande. En `build/audio_candidates_human/build_candidates.py`,
los cortes están escritos a mano, como constante, en la cabecera del
archivo:

```python
SELECTIONS = {
    "z": {"active": (5.630, 9.370), "sustained": (5.630, 7.630), ...},
    "n": {"active": (37.200, 40.230), ...},
}
```

Codex midió una vez (`inspect_source.py`, 133 líneas, imprime un JSON y
termina), **miró el resultado con oído y ojo humanos, y escribió la
respuesta en el código**. Tres minutos entre un archivo y el otro.

Yo pasé la tarde intentando *derivar* esos mismos límites: umbrales de
hueco, timbre, variabilidad espectral, número de estados espectrales,
proxy de F2, flujo espectral. Seis detectores. Todos fallaron. El trabajo
solo se desbloqueó cuando construí el banco de transcripción a ciegas y
dejé que Miguel dijera dónde estaban las fronteras — es decir, cuando por
fin hice lo que Codex había hecho a las 12:57.

**Regla.** Si una decisión depende de percepción — qué se oye, qué se ve,
qué significa un texto — no escribas un detector. Mide lo que sea barato
de medir, enséñalo, pide el juicio, y **fija el juicio como dato en el
código**. Una constante escrita a mano no es deuda técnica: es la forma
correcta de guardar una decisión humana.

**Corolario, que Miguel ya me dijo con otras palabras:** *«gana la
transcripción»*, *«donde la detección contradiga a Miguel, dale la razón a
él»*. Cuando ya te han dicho eso una vez, no vuelvas al detector.

### 2. Codex pilotó tres, yo ataqué ochenta y cinco

`audio_candidates/` es un piloto de un puñado de fonemas con su propio
`validate_pilot.py`. Solo después vino `audio_candidates_human/` con tres
fonemas reales, y solo después el lote de 27.

Yo construí el catálogo de 85 y corté los 85 antes de que nadie hubiera
confirmado que **un solo asset** salía bien de ese proceso. Cuando Miguel
por fin escuchó, el veredicto fue: 51 limpios, 34 con problema, y **24 de
esos 34 eran fallos de corte, no de grabación**. Es decir: el método
estaba roto desde el principio y me enteré con 85 piezas hechas.

**Regla.** Antes de procesar N elementos, cierra **uno** de punta a punta
y hazlo validar. Si el ciclo de validación es lento (hace falta Miguel,
hace falta su móvil), esto no es opcional: es lo único que evita gastar la
tarde entera en la dirección equivocada.

### 3. Codex dejó pocos artefactos, y todos terminales

Ocho scripts, cada uno se ejecuta una vez, escupe un JSON y muere:
`inspect_source.py` → `source_inspection.json` → `build_candidates.py` →
`manifest.json` → `verify_final.py` → `final_validation.json`. Lineal. Sin
vueltas atrás.

De mis 34 scripts, buena parte son callejones sin salida que se quedaron
en el árbol: `barrido_ruido2.json` y `barrido_ruido3.json` pesan 270 KB
entre los dos y no decidieron nada.

**Regla.** Un paso, un script, un archivo de salida, y se acabó. Si vas por
el tercer script del mismo paso, el paso está mal planteado: para y dilo.

## La condición de parada

Miguel tuvo que dármela a mano: *«para y dilo: no busques un séptimo
detector»*. No debería haber hecho falta.

Antes de empezar algo que puede iterar, escribe la condición de parada en
voz alta: **«si el segundo intento de X falla, paro y propongo otra
cosa»**. Y cúmplela. Dos intentos fallidos del mismo tipo de solución no
son mala suerte; son información de que el enfoque no sirve.

## Lo más barato primero

Nunca propuse la opción obvia: **grabar directamente cada sonido ya
delimitado**, en vez de grabar cuatro masters largos y luego pelearme por
cortarlos. Eso es lo que acabamos haciendo (`build/grabador/`), y elimina
de un golpe el problema del corte, el de la alineación y el de la
identidad de las vocales.

Cuando una tarea se pone difícil, la pregunta no es «¿cómo resuelvo esto?»
sino **«¿por qué estoy resolviendo esto?»**. A menudo el paso anterior se
puede cambiar y el problema desaparece.

## Cómo informar

Escribí informes largos. Miguel los lee en el móvil, a veces caminando.

- Primero el veredicto, en una línea.
- Después, como mucho, lo que cambia su siguiente decisión.
- Rutas, hashes y cifras: en el archivo, no en el chat. Da la ruta.
- Un número que no hayas **medido en esta sesión** no se escribe. (El 20
  sep informé de dos pid de memoria; los reales eran otros. Miguel tuvo
  que exigir «pid **medidos**, no escritos de memoria».)

## Resumen operativo

Al empezar una tarea larga, contesta estas cinco antes de escribir código:

1. ¿Hay aquí un **juicio** que estoy a punto de automatizar? → No lo
   automatices. Mide, enseña, pregunta, y fíjalo como constante.
2. ¿Cuál es el **uno** que voy a cerrar entero antes del lote?
3. ¿Cuál es mi **condición de parada** si el enfoque no funciona?
4. ¿Existe un paso **anterior** que, cambiado, hace desaparecer el
   problema?
5. ¿Qué es lo **mínimo** que Miguel necesita leer para decidir?
