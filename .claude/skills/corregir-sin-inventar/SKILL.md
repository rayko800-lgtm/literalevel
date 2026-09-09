---
name: corregir-sin-inventar
description: Cerrar los hallazgos de una auditoría sin empeorar el documento — medir antes de escribir, declarar el hueco en vez de rellenarlo, y propagar la corrección a los cuatro archivos donde vive esa cifra. Úsala siempre que vayas a arreglar lo que una auditoría marcó, y antes de encargar la siguiente.
---

# Corregir lo que una auditoría encontró

La skill hermana, `auditar-con-modelo-externo`, cubre cómo *encargar* la
auditoría. Esta cubre la parte donde de verdad se rompen las cosas: **el
arreglo**. En LiteraLevel, dos de los hallazgos más graves de la quinta y la
sexta auditoría no eran errores originales — **los introdujo la corrección de
un error anterior**.

---

## 1. La regla, que es una sola

> **Ninguna cifra nueva sin haberla medido en esta máquina y en este momento.**

Suena obvia y se incumple sola, porque corregir presiona a *explicar*, y
explicar tienta a inventar la explicación. Los dos casos reales:

**El «286».** Cuatro auditores pidieron cambiar 286 por 300 en una
comprobación de identidad. En vez de eso, la corrección escribió que había
habido *dos* tandas: «286/286 valores idénticos con MAE 0,000000000» y
«300/300». Fui a la fuente: la tanda de 286 era el **barrido de hilos**, no una
comprobación de identidad. Ese experimento no existía. Se había inventado una
medición justo en el sitio donde se intentaba corregir un error.

**La recta.** Una auditoría dijo que `predicho ≈ 0,72x + 0,38` no tenía
procedencia. La corrección le puso una: «mínimos cuadrados sobre las cinco
medias por nivel de la validación local». La siguiente auditoría lo recalculó:
esas cinco medias dan **0,669x + 0,408**. El 0,72 salía de las **cuatro** medias
de otra tanda. Otra vez: un hueco tapado con una explicación plausible y no
comprobada.

**El coste del despliegue.** La API de Hugging Face devolvió
`hardware = "cpu-basic"`, que es el escalón que no cobra por hardware. De ahí
escribí «el despliegue es gratuito» en el documento, la estrategia, la
presentación y tres archivos más. Miguel lo corrigió: paga **7 USD al mes** de
cuenta Pro, porque un Space de Gradio la exige. La API decía la verdad sobre el
hardware; la conclusión sobre el coste la puse yo.

**Cómo se evita:** antes de escribir la frase, ejecuta el cálculo. Si no puedes
ejecutarlo, no escribas la frase. Y cuando el dato venga de una API, comprueba
que responde a **la pregunta que estás contestando**: `hardware` no es
`factura`, y `isPro` sí lo era (`/api/whoami-v2`). Lo que no está en ningún
endpoint —que la tarifa de 9 se quedó en 7 por un descuento— solo lo sabe
Miguel: **pregúntale antes de publicar un precio.**

---

## 2. Si no se puede medir, se declara

No borres el dato y no le inventes una fuente. Degrádalo y di por qué:

> *0,004 de diferencia máxima sobre cinco libros; la medición se hizo en su
> momento y **no queda guion que la reproduzca**, así que se da como orden de
> magnitud, no como cifra auditable.*

Esto es lo contrario de lo que se hizo con el 286, y es lo que un profesor
valora: un hueco declarado es honestidad; un hueco tapado es un problema.

**Ojo con el tic contrario.** Si dos filas seguidas de un cuadro llevan la
misma fórmula de descargo palabra por palabra, el documento deja de afirmar y
empieza a disculparse. La segunda vez basta con «mismo caso que la fila de
arriba».

---

## 3. Los absolutos son casi siempre falsos

El patrón más repetido en seis auditorías: una afirmación **verdadera en el
caso medido**, escrita como si fuera una ley.

| Lo que decía | Lo que es verdad |
|---|---|
| «no puede mover un decimal» | no movió ninguno en la comprobación de 300 ventanas |
| «no hay relleno» | dentro de un texto suelto no; agrupando capítulos sí, y difiere 4,8·10⁻⁷ |
| «250 palabras pasan **siempre** de 256 BPE» | en prosa real sí (mínimo medido 258); 250 monosílabos dan 252 |
| «ocho ventanas representan el libro: **está medido y la respuesta es sí**» | hay una medición, y es de **un** texto |
| «validación externa **ciega**» | se miró durante el desarrollo, y el propio texto lo dice dos párrafos después |
| «tiempo de lectura **a su ritmo**» | son 180 o 110 ppm fijas; la app no conoce su ritmo |
| «le busca libros **que pueda terminar**» | la app no sabe si alguien terminará un libro |
| «análisis **por debajo del segundo**» | 0,96–1,04 s medidos |

Busca en tu propio texto: *siempre, nunca, no puede, garantiza, cualquier,
todos*. Cada uno es un candidato.

---

## 4. Una corrección no está hecha hasta que está en los cuatro sitios

La mitad de los hallazgos de la sexta auditoría eran cosas corregidas **en un
archivo y no en los otros**. En un proyecto así, una cifra vive en:

1. `documento.md` — la copia de lectura
2. `documento.tex` — el entregable de verdad
3. `estrategia.md`, `README.md`, `PENDIENTES.md`, `DESPLIEGUE.md`
4. `notebook_proyecto.py` **y** el `.ipynb` regenerado
5. `presentacion.tex`, `guion_video.md` **y** `.tex`
6. **`datos_figuras/*.dat`** ← el que siempre se olvida
7. el código y sus comentarios
8. `modelo_v4/README.md`, que además está publicado en Hugging Face

El punto 6 es el peligroso: el `.dat` es lo que **dibuja la figura**. Cuando se
corrigió la media de B2 en todas las tablas y no en `validacion.dat`, el
gráfico del PDF decía una cosa y la tabla de al lado otra — y eso no se ve
releyendo el texto, porque no está en el texto.

### El barrido, que sustituye a la memoria

No vayas sitio por sitio de memoria. Escribe un guion que busque **los valores
anteriores** por todo el árbol:

```python
VIEJOS = [
    (r'\b45 textos\b', 'la validacion son 46', []),
    (r'1[.,]2478',     'media de B2 vieja: ahora 1,2414', []),
    (r'\b0[.,]854\b',  'Spearman viejo: ahora 0,855', []),
    # (patron, por que esta mal, archivos donde SI vale)
]
```

Recorre `.md .tex .py .txt .csv .dat .json`, saltando `.git`, `__pycache__`,
`capturas/` y cualquier caché del navegador. Imprime archivo, línea y la línea
entera. La primera vez que lo corrí encontró cuatro sitios que había dado por
actualizados, incluido el `.dat`.

Deja las excepciones legítimas en la lista y anótalas, para que el barrido
pueda quedar en cero: un comentario que **explica** el fallo antiguo contiene
la cifra vieja a propósito, y una frase en pasado («el enlace *era* un túnel
temporal») también.

### Comprueba lo DIBUJADO, no solo lo escrito

Un confirmador ejecutó 78 comprobaciones sobre el documento y dio 77 exactas.
Sobre ese mismo árbol, otro encontró que **la figura de la escala dibujaba los
cortes de banda derogados** —rectángulos en 0,8 y 1,6— cuarenta líneas debajo
de una frase que dice «básico < 0,6 ≤ intermedio < 1,4 ≤ avanzado, **tal como
las dibuja la figura**». Y una segunda figura sombreaba desde 1,6 y rotulaba
«≥ 1,4».

El primero no lo vio porque miraba **números en tablas**. Los cortes vivían en
coordenadas de TikZ.

Así que la lista de sitios donde vive una cifra tiene un apartado propio:

- **`datos_figuras/*.dat`** — lo que alimenta las gráficas.
- **Los números escritos a mano dentro de `tikzpicture`**: coordenadas de
  `ill`, `\draw`, `
ode`, `ddplot`, y las etiquetas `n = 7` puestas a
  mano junto a las barras.
- **Los rótulos de las bandas y las llaves** que marcan tramos.
- **Los pies de figura** que afirman lo que la figura enseña.

Un `grep` de la cifra no los encuentra, porque en el TikZ va como `0.8` sin
coma y sin contexto. La única forma es abrir cada `tikzpicture` que dibuje un
umbral y comprobar el número contra el texto que lo cita.

### Busca la cifra en TODAS sus formas, no solo en la exacta

El barrido busca literales, y una cifra viaja por el documento con varias
caras. En un solo día se escaparon dos por esto:

| Se buscaba | Estaba escrito | Dónde |
|---|---|---|
| `1,2478` | **`1,248`** — redondeado a tres decimales | la presentación |
| `45 textos` | **`45 en local`** — la misma cifra, otra redacción | la limitación 5 |

Las dos las encontró una auditoría externa, no el barrido. Así que por cada
cifra que cambie, mete en la lista de patrones:

- el valor **exacto** (`1,2478`);
- sus **redondeos** plausibles (`1,248`, `1,25`) — una diapositiva o un
  resumen casi nunca lleva todos los decimales;
- el número **suelto**, con contexto flojo (`45` cerca de «texto», «local»,
  «de los 59»), aceptando que dará falsos positivos que descartas a mano;
- las dos formas del separador decimal, coma y punto, porque los `.dat` y el
  código usan punto y la prosa usa coma.

Es más ruidoso y merece la pena: el coste de un falso positivo es mirarlo dos
segundos; el de un falso negativo es que lo encuentre el profesor.

---

## 5. Si los datos siguen llegando, la cifra caduca

Hay números que no se corrigen una vez: **cambian solos** mientras el proyecto
avanza. En LiteraLevel son los del catálogo, porque la descarga y el análisis
siguen corriendo en Colab.

Cada vez que una tanda termina, estos se mueven y hay que rehacerlos **en todos
los sitios de la lista del apartado 4**:

| Cifra | Dónde vive además del documento |
|---|---|
| libros descargados / analizados | `PENDIENTES.md`, §8.3 del documento, el guion del vídeo |
| media de ventanas por libro | §8.3 — el documento declara que **no está medida** |
| horas de A100 para el catálogo | §8.3, la estrategia (A3), la presentación, `competencia.md` |
| reparto por banda del catálogo | Cuadro 3 y el aviso de «etiquetas heredadas» |
| `catalogo_medido.csv` | lo consume la app: si cambia, cambia lo que ve el lector |

Dos reglas que se ganan a base de disgustos:

- **No publiques una cifra viva sin la fecha.** «31.974 descargados **el 9 de
  septiembre**» envejece con dignidad; «31.974 descargados» es falso mañana.
- **Cuando el catálogo esté completo, hay frases que se retiran, no se
  actualizan.** «La remedición está en curso», «las etiquetas son heredadas del
  v1», «el número medio de ventanas por libro todavía no está medido». Ponlas
  en una lista aparte el día que dejes de necesitarlas.

Y el barrido del apartado 4 sirve igual aquí: mete la cifra vieja del catálogo
en la lista de patrones y deja que él encuentre los sitios.

---

## 6. El ciclo, y cuándo se cierra

```
auditar → arreglar → propagar → comprobar → auditar otra vez
```

**Arreglar antes de auditar, no al revés.** Lanzar una auditoría nueva con la
lista anterior sin cerrar produce informes que repiten hallazgos viejos, y
cuesta el doble leerlos. Miguel lo dijo así y tenía razón: *«quiero que las
últimas auditorías sean sobre lo corregido y solucionado»*.

**Comprobar** no es opcional y son cuatro cosas concretas:

- las pruebas pasan (`pruebas_extremas.py` y las demás)
- el `.tex` **compila** y no hay `\ref` sin `\label`
- el `.ipynb` está regenerado desde el `.py`
- el barrido de cifras viejas queda limpio

Se cierra cuando una auditoría vuelve con cero. No antes, y no porque canse.

---

## 7. Las trampas de esta máquina al escribir las correcciones

Están en `latex-en-esta-maquina`, pero la más cara se repite aquí porque
corrompe silenciosamente y solo se ve al compilar: **un heredoc de bash
convierte `\textbf` en tabulador + «extbf»**, y `python -c "…$0…"` deja
`/usr/bin/bash` dentro del `.tex`. Para editar LaTeX, escribe el guion con la
herramienta Write y ejecútalo; no lo pases por el shell.

---

## 8. Qué mirar cuando el informe llega

Un informe de auditoría no se lee entero de golpe. Ordénalo así:

1. **¿Alguna corrección anterior inventó algo?** Es el fallo más grave y el más
   probable. Recalcula todas las cifras nuevas del cierre anterior.
2. **¿Se rompió algo al corregir?** Frases sin sujeto, párrafos duplicados,
   dos archivos que ya no dicen lo mismo, referencias rotas, tablas sin número.
3. **¿Se ha ido al otro extremo?** Un documento tan lleno de salvedades que ya
   no afirma nada tampoco sirve.
4. **¿Queda algo que avergonzaría al autor?** Pídelo con esas palabras. Es la
   pregunta que produce las respuestas útiles.

Y no des por bueno un hallazgo sin comprobarlo: en la sexta auditoría todos
resultaron ciertos, pero en otras hubo tres FALSOS. Ve al archivo y a la línea.
