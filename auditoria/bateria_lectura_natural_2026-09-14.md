# Batería de la lectura natural — 14 de septiembre de 2026

Encargo de la Central: 10 frases reales del catálogo, de 6 a 14 palabras y con
ocasiones de enlace y reducción, pasadas por `voz.analizar_natural` con la clave
real (una llamada por frase a gpt-4o-mini, guardadas en caché), y evaluadas a
mano. Para ver lo que descarta el validador se guardó también la respuesta del
modelo **antes** de validar, sin llamadas extra.

## Las frases

| # | Fuente | Frase |
|---|---|---|
| 1 | *Alice* (PG11) | Would you like to see a little of it? |
| 2 | *Alice* (PG11) | And how many hours a day did you do lessons? |
| 3 | *Crime and Punishment* (PG2554) | And you want to get a fortune all at once? |
| 4 | *Crime and Punishment* (PG2554) | But what are you going to do to prevent it? |
| 5 | *Crime and Punishment* (PG2554) | You don't pay her money and you won't turn out of the room. |
| 6 | *Pride and Prejudice* (PG1342) | Do not you want to know who has taken it? |
| 7 | *Pride and Prejudice* (PG1342) | I am going to open the instrument, Eliza, and you know what follows. |
| 8 | *Pride and Prejudice* (PG1342) | You dislike an argument, and want to silence this. |
| 9 | StoryWeaver (SWV10029) | Everyone would want to interview him and ask him all sorts of questions. |
| 10 | StoryWeaver (SWV100410) | He also bought two horses and some cows and even an ox. |

## Precisión por tipo

| Tipo | Propuestos por el modelo | Correctos entre los propuestos | Llegan al lector | Correctos entre los que llegan |
|---|---|---|---|---|
| Reducciones | 11 | 2 exactos (*wanna* ×2); 4 más plausibles fuera de la lista o mal escritos | 2 | **2 de 2** |
| Enlaces | 29 | 4 verdaderos y bien tipados; 2 verdaderos con el tipo mal; 23 falsos | 4 | **4 de 4** |
| Versión natural | 10 | fiel en 2 (sin reducciones inventadas y sin tocar palabras) | 10 | **10 de 10** (8 reconstruidas) |

**Reducciones descartadas (9).**
- **Falsas (5):**
  - *gonna* para «to» solo (2 veces);
  - *doncha* para «don't» solo y para «do not»;
  - *won'ta*, inventada.
- **Plausibles pero fuera de la lista cerrada (4):** *are ya*, *ən* por «and» (2 veces), *an* por «and». Es pérdida de exhaustividad, no un error que llegue al lector.

**Enlaces descartados (25).**
- **Falsos por el sonido:** *you like*, *to see*, *a little*, *and you*, *pay her*, *want to*, *to know*, *who has*…
- **Verdaderos con el tipo equivocado:** *and ask* y *and even* marcados como «r de enlace» cuando son consonante + vocal.

**Versiones naturales que el modelo cambió.** Quitó «you» (frase 3), «would» (frase 9) y «and» (frase 8), y cambió «You» por «I» (frase 8). El validador reconstruye todas a partir de la frase y de las reducciones validadas.

**Exhaustividad.** Es baja. El modelo se deja enlaces claros («an argument», «dislike an», «get a», «all at», «turn out», «horses and») y reducciones de la lista («did you», «would you», «out of», «going to» con las posiciones bien). **El validador garantiza la precisión, no la exhaustividad.**

## Lo que el validador dejaba pasar y se ha arreglado

Los enlaces y reducciones que llegaban al lector eran todos verdaderos, pero pasaban dos cosas mal:

1. **La IPA de los enlaces venía del modelo y a veces era basura.** Llegaba «/ə/» para *little of*, «/əv/» para *of it* y «/sɔrts.ə/» para *sorts of*. Ahora sale de la IPA de diccionario de las dos palabras, unida con ‿.
2. **Énfasis en palabras funcionales.** Llegaba «of» acentuada en la frase 1. Ahora el énfasis nunca cae en una palabra de `_PALABRAS_FUNCIONALES`.

Las dos reglas se aplican también al leer lo ya guardado, así que la caché se corrige sin volver a pagar. Van con pruebas en `pruebas_voz_ritmo.py`.

## Las 3 mejores para la demo (de estas 10)

1. **«Everyone would want to interview him and ask him all sorts of questions.»**
   (StoryWeaver): *wanna* y el enlace *sorts‿of*; la versión natural, «Everyone would wanna interview him and ask him all sorts of questions.»
2. **«Would you like to see a little of it?»** (*Alice*): dos enlaces seguidos, *little‿of* y *of‿it*, sin reducciones.
3. **«And you want to get a fortune all at once?»** (*Crime and Punishment*): *wanna*; la versión natural, «And you wanna get a fortune all at once?»

La frase de la demo sigue siendo **«Don't you want to come with us?»**, verificada en el Space publicado: tiene más que enseñar (*doncha*, *wanna*, *with‿us*) que cualquiera de estas diez.

## Coste

Diez llamadas de análisis a gpt-4o-mini, del orden de céntimos, guardadas en caché: la misma frase no se vuelve a pagar.
