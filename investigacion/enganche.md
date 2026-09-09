# Enganche e intuitividad de LiteraLevel

**Cómo hacer que se entienda sola y que quien la abre siga leyendo.**

Fecha: 8 de septiembre de 2026. Investigación sobre el código real de
`app/ui.py`, `app/perfil.py`, `app/catalogo.py` (Gradio 6.26), más evidencia
externa citada y enlazada.

Este documento **no toca ningún archivo del repositorio**. Es un plan para
aplicar.

## Convenciones

- **[medido]** — lo he calculado yo sobre este repositorio o cronometrado en
  esta máquina. Se puede reproducir con el comando que acompaña.
- **[documentado]** — tiene enlace a la fuente. Si la fuente es la propia
  empresa interesada, lo digo.
- **[opinión]** — criterio mío; solo lo sostiene el argumento que lleva al lado.
- **no verificado** — circula, no encontré el origen, no se usa como argumento.

## Relación con `investigacion/diseno_lector.md`

Ese informe cubre tipografía, contraste, color, medida de línea, zonas táctiles
y CSS. **Aquí se da todo eso por hecho y no se repite.** Este documento es
sobre lo otro: en qué orden ocurren las cosas, qué se le pide al usuario y
cuándo, qué le hace volver y qué no debemos hacer para conseguirlo.

Hay dos puntos donde los dos informes se rozan y aquí van más lejos:

- El §5 de `diseno_lector.md` enumeró patrones oscuros con la taxonomía de
  Brignull. Aquí se añade **regulación real y vigente** (DSA art. 25, las
  directrices de la Comisión sobre menores de julio de 2025, y las decisiones
  preliminares contra TikTok y Meta de 2026), que es lo que convierte "esto
  está feo" en "esto está prohibido para el caso de una lectora de 15 años".
- Ese informe marcó las cifras de Duolingo como no verificadas. Aquí están
  **rastreadas hasta su origen**: cuáles son de la propia Duolingo (existen,
  pero son sus tests A/B internos, sin revisión externa) y cuáles son de blog
  de agencia (esas siguen sin origen y no se usan).

---

## 0. Resumen: siete cambios, por efecto ÷ esfuerzo

| # | Cambio | Problema que resuelve | Esfuerzo |
|---|---|---|---|
| 1 | **Una sola pregunta al entrar**, con un párrafo real en inglés, y detrás una estantería de libros | Hoy la app abre con 9 preguntas y 165 palabras de inglés antes de enseñar un solo libro (§2.1) | ~30 líneas en `ui.py`; `perfil.py` no se toca (§8.1) |
| 2 | **Empaquetar `catalogo_emb_*.npy` con el despliegue** | La primera búsqueda de verdad cuesta **63 s** [medido] (§2.2) | Copiar 1,84 MB y una variable de entorno |
| 3 | **Recomendar solo libros que se abren** | A nivel A1 salen **0 de 10** libros abribles; a A2, 2 de 10 [medido] (§2.3) | ~5 líneas |
| 4 | **Estado vacío que enseña** en "Mis libros" y "Mis palabras" | Hoy son pantallas en blanco hasta que pulsas un botón (§6.2) | ~10 líneas |
| 5 | **Reducir de 8 pestañas a 4**, con "Colores" y "Estado" fuera de la fila principal | Ocho pestañas de igual rango, dos de ellas de desarrollo (§6.1) | ~20 líneas |
| 6 | **Progreso visible durante la espera larga** (`gr.Progress` / generadora en `_buscar`) | No hay ni un `gr.Progress` en las 2.318 líneas de `ui.py` [medido] (§6.3) | ~10 líneas |
| 7 | **Cerrar el bucle del nivel**: "cuando termines este libro, vuelvo a medirte" | Es la única promesa que LiteraLevel puede cumplir y Kindle no (§4.1) | ~40 líneas |

Los tres primeros son los que arreglan lo que le pasó a Esmeralda. El resto son
mejoras reales pero de segundo orden.

---

## 1. El diagnóstico: qué significa «o yo soy muy tonta para esto»

Esa frase tiene nombre en la literatura de diseño y no es de la usuaria.

**[documentado]** Don Norman, en *The Design of Everyday Things*, describe que
cuando algo falla la gente **se culpa a sí misma antes que al diseño**, y que
la repetición del fallo lleva a lo que él llama *taught helplessness*
—indefensión enseñada—: la persona concluye que el problema es ella, deja de
explorar y abandona. Norman es explícito en que el error humano es
habitualmente resultado de un mal diseño, no de estupidez
([resumen del capítulo, Sharritt](https://www.sharritt.com/CISHCIExam/norman.html) ·
[reseña](https://askeladdencapital.com/don-normans-the-design-of-everyday-things-book-review-notes-analysis/)).

Esmeralda dijo cuatro cosas. Tres son de superficie —"difícil de usar en
celular", "casi todo", "la página se siente antigua"— y las cubre
`diseno_lector.md`. La cuarta, "o yo soy muy tonta para esto", es la única que
mide el fallo real: **la app no le dijo qué hacer, y ella dedujo que la culpa
era suya.** Cualquier cambio que no ataque eso es decoración.

**[documentado]** El otro texto fundacional que hace falta aquí es la *paradoja
del usuario activo* (Carroll y Rosson, 1987): los usuarios nuevos **no leen las
instrucciones**; se lanzan a usar el producto aunque eso implique chocar con
errores, porque solo les mueve el objetivo concreto que traen, no el potencial
del sistema. Carroll y Rosson subrayan que **esto no es un defecto a corregir en
el usuario, sino una constante del comportamiento humano** que el diseño debe
asumir
([PDF del capítulo](https://research.cs.vt.edu/ns/cs5724papers/4.mental.mental.carroll.paradox.pdf) ·
[Laws of UX](https://lawsofux.com/paradox-of-the-active-user/)).

Consecuencia directa para LiteraLevel: la cabecera actual —*"**1)** Fija tu
nivel · **2)** busca algo que te apetezca leer · **3)** léelo aquí… Las
pestañas están en ese orden"*— es una instrucción de tres pasos colocada antes
de cualquier valor. Está bien escrita y **nadie la va a leer**. El orden tiene
que estar en el comportamiento de la app, no en un párrafo.

---

## 2. Lo que hoy hace la app cuando alguien entra por primera vez

Todo este apartado es **[medido]** sobre el código de hoy.

### 2.1 La primera pantalla pide nueve decisiones antes de dar nada

`construir()` monta ocho pestañas y abre en la primera, "Mi nivel", con dos
acordeones ya desplegados (`open=True`). Lo que ve alguien que entra:

| Elemento | Cantidad |
|---|---|
| Preguntas de opinión (`perfil.PREGUNTAS`) | **6** (5 `Radio` + 1 `CheckboxGroup`) |
| Opciones que hay que leer en esas seis | **30** |
| Fragmentos literarios en inglés (`perfil.FRAGMENTOS`) | **3** — Carroll, Conan Doyle, Shelley |
| Palabras de prosa inglesa en esos fragmentos | **165** (57 + 59 + 49) |
| Opciones de las tres preguntas de fragmento | **15** |
| **Total de decisiones antes del botón** | **9 preguntas / 45 opciones** |
| Acordeones cerrados con métodos alternativos | 2 más |
| Libros enseñados hasta aquí | **0** |

Reproducible con:

```bash
python -X utf8 -c "import sys; sys.path.insert(0,'app'); import perfil; \
print(len(perfil.PREGUNTAS), len(perfil.FRAGMENTOS), \
sum(len(f['texto'].split()) for f in perfil.FRAGMENTOS))"
```

Léalo otra vez pensando en una chica de 15 años a la que le pasaron un enlace:
lo primero que le pide una app que aún no le ha demostrado nada es **leer 165
palabras de literatura inglesa del XIX y juzgarse a sí misma cinco veces**. Si
no entiende el fragmento de *Frankenstein* —lo normal— la primera experiencia
del producto es un suspenso autoadministrado. Ese es el terreno perfecto para
"o yo soy muy tonta para esto".

El cuestionario **no es malo**: está bien escrito, la escala de fragmentos pesa
0,65 frente a 0,35 la opinión, y medir con texto real es mejor idea que
preguntar. El problema no es su contenido, es **su posición**.

### 2.2 La primera acción interesante cuesta entre 15 y 63 segundos

Cronometrado en esta máquina, proceso limpio, en frío:

| Paso | Tiempo |
|---|---|
| `import ui` | **5,5 – 6,0 s** |
| `_diagnostico()` (corre en `demo.load`, en cada carga de página) | **0,03 s** |
| `_recomendar(...)` — "Sorpréndeme", solo pandas | **0,01 s** |
| `_buscar(...)` primera vez, **con** la caché `.npy` en disco | **15,1 s** |
| `_buscar(...)` siguientes | **0,03 s** |
| Cargar el modelo multilingüe, sin caché de disco | **14,8 s** |
| Codificar los 1.197 textos del catálogo desde cero | **47,9 s** |
| **Primera búsqueda absoluta (sin caché)** | **≈ 63 s** |

```bash
python -X utf8 -c "import sys,time; sys.path.insert(0,'app'); \
t=time.perf_counter(); import ui; print(time.perf_counter()-t); \
t=time.perf_counter(); ui._buscar(None,'novela de detectives',True,10); \
print(time.perf_counter()-t)"
```

Tres conclusiones:

1. El aviso de la interfaz —*"puede tardar cerca de un minuto"*— **es cierto**
   la primera vez de todas, y **exagerado por un factor de cuatro** el resto de
   veces (15 s con la caché en disco). Decir "un minuto" cuando serán quince
   segundos hace que la gente cierre antes de comprobarlo.
2. Esa caché es el archivo `~/.literalevel/catalogo_emb_653c0cb55f63a386.npy`,
   de **1,84 MB**. `AGENTS.md` ya advierte que las cachés de `~/.literalevel/`
   son disco efímero en un Space y se borran en cada reinicio: **desplegada, la
   app pagará los 63 segundos cada vez que despierte**, y despierta por
   inactividad. Empaquetar 1,84 MB con el despliegue elimina 48 de esos 63
   segundos y es de las cosas más baratas que hay en esta lista.
3. **El camino barato ya existe y está tapado.** `Catalogo.por_nivel()` es
   pandas puro: no toca embeddings, no toca torch, tarda **0,01 s** y devuelve
   10 libros en cualquiera de los once niveles que probé. Es lo que usa el
   botón "Sorpréndeme con algo de mi nivel"… que hoy contesta *"Primero fija tu
   nivel en la pestaña **Mi nivel**"* si no hay perfil (`_recomendar`, línea
   ~608). El único camino instantáneo de la app está cerrado con llave detrás
   de las nueve preguntas.

### 2.3 Al lector principiante se le recomiendan libros que no puede abrir

Este es el hallazgo más serio del informe, y es aritmética del catálogo:

```bash
python -X utf8 -c "import sys; sys.path.insert(0,'app'); import pandas as pd; \
from catalogo import Catalogo; d=Catalogo().df.copy(); \
d['pg']=d['id'].astype(str).str.upper().str.startswith('PG'); \
print(pd.crosstab(d['nivel_cefr'], d['pg']))"
```

| nivel | **no** abribles (StoryWeaver / GDL) | **sí** abribles (Project Gutenberg) |
|---|---|---|
| A1 | 723 | **0** |
| A2 | 183 | **2** |
| B1 | 59 | 10 |
| B2 | 40 | 12 |
| C1 | 28 | 25 |
| C2 | 16 | 99 |
| **total** | **1.049** | **148** |

De los 1.197 libros del catálogo, **148 (12,4 %) se pueden abrir dentro de la
app**; el resto solo se pueden mirar. Y el reparto está invertido respecto a
quien los necesita: **dos tercios de lo abrible es C2**, y en A1 no hay nada.

Comprobado con el flujo real: para un perfil de nivel 0,0, "Sorpréndeme"
devuelve diez libros, la tabla dice honestamente *"Ninguno de estos se puede
abrir aquí: son de StoryWeaver"*, y el `gr.Radio` de "Elige cuál abrir" se
queda **vacío**. A nivel 0,4, 2 de 10.

El código maneja el caso **bien** —filtra el desplegable, avisa arriba, no
miente— y los comentarios de `_opciones_libros` demuestran que ya se pensó. El
problema no es de manejo del error: es que **el camino feliz del principiante
termina en un callejón sin salida bien señalizado**. Y el principiante es
exactamente Esmeralda.

Nota de contexto, no de este informe: `AGENTS.md` ya advierte que las etiquetas
CEFR del catálogo salieron del modelo v1 sobre las primeras ~190 palabras con
cortes por cuantiles y que **esa correspondencia no se sostiene**. Es decir: el
sesgo A1 del catálogo es dudoso *además* de inservible. No hace falta resolver
lo primero para arreglar lo segundo.

### 2.4 Lo que ya está bien y no hay que tocar

Digo esto antes de proponer nada, porque casi todo lo de abajo son ajustes
sobre una base que está mejor de lo que sugiere el comentario de Esmeralda:

- **`_reanudar` en `demo.load`.** Al volver, la app abre en el libro y el
  capítulo donde lo dejaste y salta sola a la pestaña "Leer". Es la mecánica de
  retención más honesta que existe y **ya está construida**. La mitad del §4 de
  este informe consiste en enseñarla más, no en inventarla.
- **Los textos de los botones.** "¿Cómo de difícil es este capítulo?",
  "Vistazo rápido (unos segundos)", "Leer el libro entero (tarda más)",
  "Retomar donde lo dejé", "Sorpréndeme con algo de mi nivel". Son etiquetas
  que dicen el **resultado y su coste**, que es justo lo que pide la guía de
  revelación progresiva de NN/g. El consejo genérico de "etiqueta resultados,
  no acciones" **ya está aplicado** en esta app; no lo repito como hallazgo.
- **`_descargar_gutenberg`.** Cerrar el bucle buscar → leer sin echar al
  usuario a gutenberg.org es la decisión de producto más importante del repo.
- **La honestidad de los avisos.** `_recomendar` no dice "Sin resultados": dice
  qué hacer a continuación. `catalogo.buscar` nunca devuelve vacío en silencio.
- **La doble barra de capítulos y el resultado del cuestionario pintado dos
  veces.** Son correcciones de scroll móvil ya razonadas.

---

## 3. Los primeros treinta segundos: qué dice la evidencia

### 3.1 El tiempo real que hay

**[documentado]** Jakob Nielsen, sobre el análisis de Chao Liu y colegas
(Microsoft Research) de **205.873 páginas y más de 2.000 millones de tiempos de
permanencia**: la probabilidad de abandono es altísima en los primeros
segundos, *"los primeros 10 segundos de la visita son críticos"*, y la curva
**se aplana alrededor de los 30 segundos**: quien pasa de ahí suele quedarse
dos minutos o más. Su recomendación literal: *"para ganar varios minutos de
atención del usuario, tienes que comunicar tu propuesta de valor claramente en
10 segundos"*
([NN/g](https://www.nngroup.com/articles/how-long-do-users-stay-on-web-pages/)).

Aplicado sin adornos: **LiteraLevel tiene diez segundos para enseñar un libro**,
y hoy gasta esos diez segundos pidiendo la tercera de nueve respuestas.

### 3.2 El onboarding que funciona es el que no existe

**[documentado]** NN/g, sobre onboarding de aplicaciones móviles: hay tres
componentes —promoción de funciones, personalización e instrucciones— y la
recomendación general es **evitarlos siempre que se pueda** e invertir ese
esfuerzo en que la interfaz no los necesite. Motivos: coste de interacción,
carga de memoria, y que **los tutoriales no mejoran el rendimiento en la
tarea**. Frase literal: *"El onboarding instructivo no debe usarse para
compensar un mal diseño"*
([Mobile-App Onboarding](https://www.nngroup.com/articles/mobile-app-onboarding/) ·
[Onboarding Tutorials vs. Contextual Help](https://www.nngroup.com/articles/onboarding-tutorials/) ·
[Onboarding: Skip it When Possible](https://www.nngroup.com/videos/onboarding-skip-it-when-possible/)).

Y una observación que aplica letra por letra al caso: NN/g dice que
**la personalización visual debe irse a ajustes** y no cargarse sobre el
usuario nuevo, y que la personalización de contenido solo se justifica *si es
imprescindible para que el producto funcione, breve, y explicando por qué se
pregunta*.

Traducido a LiteraLevel:

- La pestaña **"Colores"** es personalización visual en la fila principal de
  navegación. A ajustes.
- El **cuestionario de nivel** sí es personalización de contenido
  imprescindible: sin nivel no hay recomendación ajustada, que es el producto.
  Pero "breve" y "explicando por qué" significa **una pregunta**, no nueve.
- Las tres condiciones que NN/g sí acepta para instruir —dato imprescindible
  para empezar, producto muy personalizado, interacción genuinamente novedosa—
  se cumplen en **un** sitio de esta app: que **seleccionar una palabra del
  texto la consulta sola**. Eso no lo espera nadie, y hoy se explica con un
  párrafo de Markdown que está *debajo* del texto del capítulo. Ese es el único
  punto donde una ayuda contextual —al abrir el primer capítulo, una vez—
  está justificada.

### 3.3 ¿Cuestionario al entrar o después? Respuesta concreta

**[opinión, apoyada en 3.1 y 3.2]** Después. Pero no "después" como en
"escondido": después como en **al final del primer momento de valor**, y
partido en dos.

El argumento fuerte no es teórico, es del código: **`perfil.desde_cuestionario`
ya acepta una sola respuesta.** Verificado:

```bash
python -X utf8 -c "import sys; sys.path.insert(0,'app'); import perfil; \
p=perfil.desde_cuestionario({'fragmento_medio': 0.6}); print(p)"
# Perfil(nivel=0.6, banda='intermedio', origen='cuestionario', ...)
```

Un único fragmento contestado produce un perfil válido, con banda, y con rango
de recomendación. **`perfil.py` no necesita ni una línea nueva.** El cambio es
solo de montaje en `ui.py`, y `perfil.py` es archivo compartido, así que
además evita pisar a nadie.

Con eso, la secuencia de apertura pasa de "9 preguntas → 0 libros" a
"1 pregunta → 10 libros en 0,01 s". Las otras ocho preguntas siguen existiendo
en un "Afinar mi nivel" para quien quiera precisión, que es exactamente la
definición de **revelación progresiva**: las opciones secundarias en una
pantalla subordinada, con una etiqueta que promete lo que hay detrás
([NN/g, Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)).

---

## 4. Motivación que respeta al usuario

Cuatro marcos, y qué dice cada uno para *este* producto. Los cito porque cada
uno responde una pregunta distinta, no por acumular nombres.

### 4.1 Autodeterminación (Deci y Ryan): qué tipo de motivación queremos

**[documentado]** La teoría de la autodeterminación sostiene que la motivación
intrínseca florece cuando se satisfacen tres necesidades psicológicas:
**autonomía** (elijo yo), **competencia** (soy capaz) y **relación** (pertenezco
a algo). Fuente primaria: Ryan, R. M. y Deci, E. L. (2000), *Self-Determination
Theory and the Facilitation of Intrinsic Motivation, Social Development, and
Well-Being*, **American Psychologist 55(1), 68-78**
([PDF en selfdeterminationtheory.org](https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf) ·
[PubMed](https://pubmed.ncbi.nlm.nih.gov/11392867/)).

Lo importante de SDT para un trabajo evaluado: distingue motivación
**intrínseca** de **controlada** (premios, castigos, presión). Las recompensas
externas pueden **desplazar** a la intrínseca. Una app de lectura cuyo objetivo
declarado es que la gente **lea**, no que abra la app, tiene que apoyarse en la
intrínseca.

Qué toca en LiteraLevel:

- **Autonomía.** El usuario elige el libro, el nivel de ajuste, el idioma de la
  explicación, la escala (0–2 o A1–C2) y los colores. Esto la app **ya lo hace
  bien**, y es su mejor activo motivacional. Lo que le falta es autonomía sobre
  **la meta**: hoy no puede decir "quiero leer 15 minutos al día" ni "quiero
  terminar este libro este mes".
- **Competencia.** Es el punto flaco, y es donde falló con Esmeralda. La
  competencia se siente al **conseguir algo**, y lo primero que consiguió ella
  fue no entender a Mary Shelley. El sitio natural donde LiteraLevel puede dar
  sensación de competencia es el que ya tiene medio construido: **volver a
  medir el nivel después de leer** y enseñar que subió. Ninguna otra app de
  lectura puede hacer eso, porque ninguna otra lleva un modelo de dificultad
  dentro.
- **Relación.** Aquí no hay nada que hacer y **está bien que no lo haya**: no
  hay cuentas, no hay red social, y meterla sería inventar un producto distinto.
  Decirlo explícitamente en la defensa es mejor que fingir.

### 4.2 Flow (Csikszentmihalyi): por qué el nivel es la mecánica, no un adorno

**[documentado]** Csikszentmihalyi describió el *flow* como el estado en que la
habilidad está plenamente ocupada por un reto abordable, y lo situó **en el
canal entre el aburrimiento y la ansiedad**: si la dificultad supera la
habilidad aparece ansiedad; si queda por debajo, aburrimiento. Fuentes: *Beyond
Boredom and Anxiety* (1975) y *Flow: The Psychology of Optimal Experience*
(1990)
([resumen académico](https://www.psy.gla.ac.uk/~steve/courses/pospsydocs/oldwikis/2015.20.Flow.pdf) ·
[crítica del supuesto reto=habilidad, Springer](https://link.springer.com/article/10.1007/s11205-012-0211-9)).

Es el marco que mejor le sienta a LiteraLevel, porque **el producto entero es
un medidor de la distancia entre reto y habilidad**. `perfil.rango_recomendado`
ya implementa literalmente el canal de flow. Consecuencias prácticas:

- La ficha del libro debería decir el reto **en términos del lector** ("va un
  poco por encima de lo tuyo, pero te lo puedes comer") antes que en cifras.
  `_ficha_libro` ya distingue el caso `nivel_libro > p.nivel + 0.15`: es
  cuestión de darle voz.
- Un lector con nivel 0,0–0,4 al que se le ofrecen 99 libros C2 y ninguno A1
  está **fuera del canal por el lado de la ansiedad**. §2.3 no es solo un bug de
  catálogo: es el mecanismo central del producto funcionando al revés.

**[documentado]** La crítica honesta que hay que conocer: la hipótesis "reto =
habilidad" no siempre se sostiene empíricamente; Løvoll y Vittersø (2014) siguieron a 64 y a 26 estudiantes de
deporte al aire libre y encontraron que los indicadores de *flow* **no** hacían
pico en la condición de equilibrio, y que la razón reto/habilidad explicaba solo
el **9 % y el 14 %** de la varianza de la experiencia
([Social Indicators Research 115(1)](https://link.springer.com/article/10.1007/s11205-012-0211-9)).
O sea: ajustar el nivel es necesario, no suficiente. El libro tiene que
apetecer, y por eso el buscador semántico en español ("una novela de detectives
victoriana") vale tanto como el ajuste de nivel.

### 4.3 Fogg (B = MAP): dónde está el cuello de botella

**[documentado]** El modelo de Fogg: **B = MAP**, un comportamiento ocurre
cuando **motivación**, **habilidad** (facilidad) y **detonante** coinciden en
el mismo instante por encima del umbral de activación; si falta uno, no ocurre.
Fuente primaria: B. J. Fogg, *A Behavior Model for Persuasive Design*,
Persuasive '09 (26 de abril de 2009). En el artículo original el tercer factor
se llama *trigger*; Fogg lo renombró después *prompt*, de ahí las dos siglas
B=MAT y B=MAP que circulan
([ACM](https://dl.acm.org/doi/10.1145/1541948.1541999) ·
[behaviormodel.org](https://behaviormodel.org/)).

Su tesis más útil aquí: **el cuello de botella casi nunca es la motivación,
es la facilidad**. Esmeralda tenía motivación —abrió la app, la probó, dio su
opinión— y se estrelló contra la facilidad: 9 preguntas, 8 pestañas, 63
segundos de espera y un desplegable vacío.

Regla de trabajo que saco de esto y que ordena la lista del §8: **antes de
añadir una sola mecánica de motivación, hay que gastar el presupuesto en
quitar pasos.** Añadir una racha a una app donde el primer libro cuesta un
minuto de espera es poner gasolina en un coche sin ruedas.

Los "detonantes" de Fogg merecen una nota: en una app **local, sin cuentas y
sin notificaciones**, el único detonante posible es que el usuario decida
volver. Eso limita el repertorio honesto a **una sola cosa**: que al volver
encuentre exactamente donde lo dejó, en un clic. Que es lo que `_reanudar` ya
hace.

### 4.4 *Hooked* (Eyal): el modelo y su propio freno ético

**[documentado]** El modelo *Hooked* es un bucle de cuatro fases —**detonante →
acción → recompensa variable → inversión**— formalizado por Nir Eyal en 2014,
apoyado en el refuerzo variable de Skinner y en el modelo de Fogg
([nirandfar.com](https://www.nirandfar.com/how-to-manufacture-desire/)).

Aplicado con honestidad a un lector de libros, tres de las cuatro fases son
inocuas y una es la peligrosa:

| Fase | Versión legítima en LiteraLevel | Versión que hay que rechazar |
|---|---|---|
| Detonante | Volver a abrir la app y encontrar el marcapáginas | Notificaciones, correos, "Duo está triste" |
| Acción | Un clic desde "abrir" hasta "leyendo" | — |
| Recompensa **variable** | La palabra consultada trae etimología, IPA, audio: contenido genuinamente distinto cada vez **porque el diccionario lo es** | Cofres, ruletas, puntos aleatorios, sorpresas fabricadas |
| Inversión | El cuaderno de palabras y el progreso por libro, que son **datos que el usuario creó** | Rachas que se pierden, monedas que caducan |

La distinción importa: la recompensa variable **de contenido real** (cada
palabra tiene una historia distinta) es legítima; la recompensa variable
**fabricada** (premio aleatorio para producir refuerzo intermitente) es la
mecánica de casino.

**[documentado]** El propio Eyal propone la **matriz de manipulación**, con dos
preguntas: *¿usaría yo mismo el producto?* y *¿mejora materialmente la vida del
usuario?* Cuatro cuadrantes: **facilitador** (sí/sí), **entretenedor**,
**vendedor** (*peddler*) y **traficante** (*dealer*)
([Forbes, del propio autor](https://www.forbes.com/sites/nireyal/2012/07/02/the-art-of-manipulation/) ·
[nirandfar](https://www.nirandfar.com/the-art-of-manipulation/)).

LiteraLevel está cómodamente en "facilitador" —Miguel la usa y ayuda a leer— y
la matriz sirve de prueba de fuego para cada mecánica nueva. **Aviso de
honestidad intelectual, porque un profesor puede sacarlo:** el propio Eyal es
figura discutida, y hay críticas argumentadas de que sus libros normalizan el
diseño adictivo y que su matriz es autoexculpatoria
([Axbom](https://axbom.com/nir-eyal-habit-danger/)). Si se cita *Hooked* en la
defensa, conviene citarlo **como el mapa del terreno que hay que atravesar con
cuidado**, no como un manual a seguir.

### 4.5 Progreso: dos resultados con fuente primaria

**[documentado]** El **efecto de gradiente de meta**: Kivetz, Urminsky y Zheng
(2006), *The Goal-Gradient Hypothesis Resurrected: Purchase Acceleration,
Illusionary Goal Progress, and Customer Retention*, **Journal of Marketing
Research 43(1), 39-58**. Los clientes aceleran conforme se acercan a una
recompensa visible; y una tarjeta de 12 sellos con 2 regalados se completa
**más rápido** que una de 10 vacía, aunque ambas exijan 10 compras
([PDF de los autores, U. Chicago](https://home.uchicago.edu/ourminsky/Goal-Gradient_Illusionary_Goal_Progress.pdf) ·
[JMR](https://journals.sagepub.com/doi/abs/10.1509/jmkr.43.1.39)).

Esto **verifica** la referencia que `diseno_lector.md` §5.1 dejó marcada como
pendiente de comprobar: existe, es de 2006, es de JMR, y el PDF de los autores
está accesible. Pero ojo con la segunda mitad del hallazgo: *illusionary goal
progress* —regalar progreso falso— es una manipulación, aunque sea suave. En
LiteraLevel eso sería, por ejemplo, arrancar la barra del libro al 10 % porque
sí. **No.** El progreso que se enseña tiene que ser el progreso que hay.

**[documentado]** El **hueco con coste** (*emergency reserve*): Sharif, M. A. y
Shu, S. B. (2017), *The Benefits of Emergency Reserves: Greater Preference and
Persistence for Goals That Have Slack with a Cost*, **Journal of Marketing
Research 54(3), 495-509**. Un objetivo que incluye un margen explícito de
excepciones se prefiere y **se sostiene mejor** que uno rígido; y el
seguimiento de 2019 en *OBHDP* muestra que ayuda a **persistir después de
fallar**
([PDF, Wharton](https://marketing.wharton.upenn.edu/wp-content/uploads/2016/10/The-Benefits-of-Emergency-Reserves-Greater-Preference-and-Performance-for-Goals-having-Slack-with-a-Cost.pdf) ·
[JMR](https://journals.sagepub.com/doi/abs/10.1509/jmr.15.0231) ·
[seguimiento OBHDP 2019, UCLA](https://anderson-review.ucla.edu/wp-content/uploads/2021/03/Sharif-Shu_EmergencyReserveFailure_OBHDP2019.pdf)).

Esta es la fuente primaria **detrás del "streak freeze" de Duolingo**, que la
propia Duolingo cita sin dar la referencia. Y es la que justifica que **si**
alguna vez hay meta en LiteraLevel, tenga margen desde el primer día.

---

## 5. La frontera ética, con nombres

### 5.1 Qué hace cada una, y de qué lado cae

**[documentado]** Las cuatro mecánicas que la Comisión Europea ha señalado por
su nombre en 2026 —y la línea que separa las legítimas:

| Técnica | Quién la usa | ¿Legítima en LiteraLevel? | Por qué |
|---|---|---|---|
| **Scroll infinito** | Instagram, Facebook, TikTok | **Sí, para el capítulo** | En un libro el scroll no es infinito: **termina**. El texto tiene final, y ese final es un logro. Un feed sin fondo es otra cosa |
| **Autoplay** | YouTube, TikTok, Instagram Reels | **No** | Pasar solo al capítulo siguiente sin que el lector lo pida es la misma mecánica de "un vídeo más" y le quita la decisión |
| **Recomendador personalizado** | Todos | **Sí** | Recomendar por **nivel y por lo que el lector pidió en español** no es lo mismo que optimizar tiempo de permanencia. La diferencia es la función objetivo: aquí es "que lo pueda leer", no "que no se vaya" |
| **Notificaciones push** | Todos | **No** — además es imposible: la app no tiene a quién notificar | |
| **Rachas** | Duolingo, Snapchat | **No en su forma habitual** (§5.3) | |
| **Recompensa variable fabricada** (cofres, ruletas) | Duolingo, juegos | **No** | La app ya tiene recompensa variable real: cada palabra trae una entrada distinta |
| **Ligas / clasificaciones** | Duolingo | **No** | Sin cuentas no hay contra quién competir; simularlo sería prueba social falsa |
| **Progreso visible y honesto** | Kindle, Instapaper | **Sí** | Es información que el lector necesita, no un truco (§4.5) |
| **Continuar donde lo dejaste** | Todos los lectores | **Sí, y es la mejor** | No inventa un motivo para volver: elimina el coste de volver |

### 5.2 Lo que dice la ley, y por qué aquí sí importa

Esto ya no es criterio de diseño. Es derecho vigente, y es lo que
`diseno_lector.md` no cubría.

**[documentado] DSA, artículo 25(1)** — *Diseño y organización de las interfaces
en línea*, aplicable en toda la UE desde el 17 de febrero de 2024:

> *"Providers of online platforms shall not design, organise or operate their
> online interfaces in a way that deceives or manipulates the recipients of
> their service or in a way that otherwise materially distorts or impairs the
> ability of the recipients of their service to make free and informed
> decisions."*

El apartado 3 encarga a la Comisión emitir directrices, y menciona
expresamente tres prácticas: **dar más prominencia a unas opciones que a
otras**, **volver a pedir una decisión ya tomada mediante ventanas
emergentes**, y **hacer más difícil darse de baja que darse de alta**
([texto del artículo](https://www.eu-digital-services-act.com/Digital_Services_Act_Article_25.html) ·
[Reglamento (UE) 2022/2065 en EUR-Lex](https://eur-lex.europa.eu/eli/reg/2022/2065/oj/eng)).
El considerando 67 define los patrones oscuros como prácticas que *"distorsionan
o menoscaban materialmente… la capacidad de los destinatarios del servicio de
tomar decisiones autónomas e informadas"*
([Parlamento Europeo, resumen](https://www.europarl.europa.eu/RegData/etudes/ATAG/2025/767191/EPRS_ATA(2025)767191_EN.pdf)).

**[documentado] Directrices sobre protección de menores (art. 28 DSA), 14 de
julio de 2025.** Este es el documento que hace que todo esto sea directamente
pertinente, porque **la primera usuaria de LiteraLevel tiene 15 años**. Entre
las medidas que la Comisión considera apropiadas y proporcionadas está,
literalmente:

> *"Disabling by default features that contribute to excessive use, like
> communication 'streaks', ephemeral content, 'read receipts', autoplay, or
> push notifications, as well as removing persuasive design features aimed
> predominantly at engagement."*

([anuncio de la Comisión](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-protection-minors) ·
[texto en el DOUE, C/2025/5519](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:C_202505519)).
No son vinculantes, pero la Comisión las usa para evaluar el cumplimiento del
art. 28(1). **Las rachas están nombradas, con esa palabra, en una lista de
cosas que hay que desactivar por defecto para menores.**

**[documentado] Y ya hay expedientes.** El 6 de febrero de 2026 la Comisión
concluyó preliminarmente que el **diseño adictivo de TikTok** infringe el DSA,
nombrando **scroll infinito, autoplay, notificaciones push y el recomendador
altamente personalizado**, con el argumento de que esos elementos *"recompensan
constantemente al usuario con contenido nuevo"* y *"alimentan el impulso de
seguir deslizando y ponen el cerebro del usuario en modo piloto automático"*;
exige desactivar el scroll infinito y establecer pausas efectivas de tiempo de
pantalla
([Comisión Europea](https://digital-strategy.ec.europa.eu/en/news/commission-preliminarily-finds-tiktoks-addictive-design-breach-digital-services-act)).
Una decisión equivalente se dirigió al **diseño adictivo de Instagram y
Facebook**
([Comisión Europea](https://digital-strategy.ec.europa.eu/en/news/commission-preliminarily-finds-addictive-design-instagram-and-facebook-breach-digital-services-act)).

**[documentado] Al otro lado del Atlántico**, el informe de la FTC *Bringing
Dark Patterns to Light* (septiembre de 2022) organiza los patrones en cuatro
familias:

1. **Elementos de diseño que inducen creencias falsas** — incluye
   explícitamente *"cuentas atrás en ofertas que no están realmente limitadas
   en el tiempo"*, *"afirmar que un artículo está casi agotado cuando hay
   existencias de sobra"* y *"afirmaciones falsas de que otras personas están
   viendo o han comprado el mismo producto"*.
2. **Elementos que ocultan o retrasan información material.**
3. **Elementos que llevan a cargos no autorizados.**
4. **Elementos que ocultan o subvierten las opciones de privacidad.**

Dos frases del informe que valen para la defensa: que las empresas deben mirar
no solo *"el efecto que sus decisiones de diseño tienen sobre las ventas, las
tasas de clic u otras métricas de beneficio"*, sino sobre la comprensión del
usuario; y que cuando una práctica **se dirige a un público específico, como
los niños**, el "consumidor razonable" a efectos de la sección 5 es un miembro
razonable **de ese grupo**
([PDF del informe](https://www.ftc.gov/system/files/ftc_gov/pdf/P214800+Dark+Patterns+Report+9.14.2022+-+FINAL.pdf) ·
[ficha FTC](https://www.ftc.gov/reports/bringing-dark-patterns-light)).

### 5.3 El caso Duolingo, con las cifras rastreadas

Duolingo es el ejemplo obligado porque es célebre en las dos direcciones. Lo
importante es separar **qué está documentado, por quién, y con qué método.**

**Lo que la propia Duolingo publica** (fuente de primera mano, pero es la parte
interesada, son tests A/B internos y **no hay revisión externa ni datos
brutos**):

- La *apuesta de racha* (Streak Wager) produjo *"aumentos estadísticamente
  significativos en la retención a día 1, 7 y 14"*, siendo el mayor el de
  **día 7, +14 %**.
- El *amuleto de fin de semana*: los usuarios fueron **4 %** más propensos a
  volver una semana después y **5 %** menos propensos a perder la racha; el uso
  cae entre un **5 y un 10 %** los fines de semana.
  ([blog de Duolingo](https://blog.duolingo.com/how-streaks-keep-duolingo-learners-committed-to-their-language-goals/))
- **6 millones** de personas con racha de 7 días o más; unas animaciones nuevas
  subieron la retención a 7 días **+1,7 %**; duplicar los "congeladores de
  racha" subió los usuarios activos diarios **+0,38 %**; y *"quienes alcanzan
  una racha de solo 7 días tienen 3,6 veces más probabilidades de completar su
  curso"*.
  ([blog de Duolingo](https://blog.duolingo.com/how-duolingo-streak-builds-habit))

Sobre esa última: **es una correlación presentada sin control**. Quien aguanta
siete días es distinto de quien no antes de que exista la racha. No sirve como
prueba de que la racha causa el aprendizaje, y **no debe usarse así en la
defensa**.

**Lo que no está verificado**: el "de 12 % a 55 % de retención" que circula por
todas partes procede de blogs de agencia
([ejemplo, StriveCloud](https://www.strivecloud.io/duolingo-gamification-explained)).
No encontré ninguna publicación de Duolingo ni artículo revisado que lo
sostenga. **No verificado. No usarlo**, tal y como ya concluyó
`diseno_lector.md`.

**La parte que la racha hace mal**, documentada:

- El mecanismo es **aversión a la pérdida**: la racha no motiva a aprender,
  motiva a **no perder el contador**. La propia Duolingo lo nombra así en su
  blog.
- Lleva a hacer **el mínimo para salvar el contador** —abrir, tocar, cerrar—,
  activando la métrica de retención sin que ocurra aprendizaje
  ([The Decision Lab, *Streak Creep*](https://thedecisionlab.com/insights/consumer-insights/streak-creep-the-perils-of-too-much-gamification)).
- La comunicación de rescate usa **culpa explícita**: notificaciones del tipo
  *"You made Duo sad"* con el mascota apenada. Eso es *confirmshaming* con otro
  nombre, y en el catálogo de Brignull tiene entrada propia
  ([deceptive.design/types](https://www.deceptive.design/types)).
- Y hoy, además, **la palabra "streaks" aparece en una lista de la Comisión
  Europea de funciones a desactivar por defecto para menores** (§5.2).

**Lo que la racha hace bien y sí es copiable**: el *streak freeze* está apoyado
en investigación real y anterior a Duolingo —Sharif y Shu, §4.5—: un objetivo
con margen explícito se sostiene mejor que uno rígido. **La idea aprovechable
no es la racha: es el margen.**

### 5.4 El argumento del profesor

**[opinión, pero con base]** Esto lo evalúa un profesor universitario, en un
trabajo de ciencia de datos, sobre una herramienta educativa, probada por una
menor. Un patrón oscuro en ese contexto **se penaliza solo**, por tres vías:

1. **Es contradictorio con el objetivo declarado.** El producto dice medir la
   dificultad para que la gente lea mejor. Una mecánica que optimiza aperturas
   de app en vez de capítulos leídos contradice la tesis del propio trabajo, y
   eso es un fallo de diseño experimental antes que de ética.
2. **Es ilegal en el caso de uso descrito.** No hay que argumentar sensibilidad:
   basta citar el art. 25 del DSA y las directrices del art. 28 de julio de
   2025, donde las rachas aparecen nominalmente.
3. **La métrica se contamina a sí misma.** El argumento de *The Problem with
   Metrics* —ya citado en `diseno_lector.md`— es que optimizar métricas de
   interacción realimenta el problema. Si al final se presentan resultados de
   uso, conviene que la métrica sea **capítulos terminados**, no minutos.

El movimiento fuerte para la defensa es el inverso al que suele hacerse: **no
esconder que se estudiaron estas mecánicas, sino enseñar la lista de las que se
rechazaron y por qué.** Un apartado de "qué no implementamos" con el DSA
citado vale más que una racha bonita.

---

## 6. Intuitividad: que la interfaz se explique sola

### 6.1 Ocho pestañas del mismo rango, dos de ellas de desarrollo

**[medido]** Las ocho pestañas y su carga de controles interactivos (botones,
radios, cajas, desplegables, ficheros, audios):

| Pestaña | Controles interactivos |
|---|---|
| Mi nivel | 10 declarados (**y 9 preguntas más generadas en bucle**) |
| Buscar lectura | 7 |
| **Leer** | **17** |
| Pronunciación | 6 |
| Mis libros | 3 |
| Mis palabras | 2 |
| Colores | 1 |
| Estado | 1 |

Tres problemas de arquitectura de la información, en orden de gravedad:

1. **"Estado" no es una pestaña de usuario.** `_diagnostico()` imprime rutas
   absolutas del disco de Miguel (`C:\Users\laura\literalevel\modelo_v4`), el
   tamaño del diccionario y si la clave de OpenAI está configurada. Para
   Esmeralda es ruido incomprensible; desplegada, es información del servidor a
   la vista de cualquiera. Es una herramienta de demo excelente —el propio
   `AGENTS.md` la llama "punto 6, diagnóstico para la demo"— pero su sitio no
   es la fila principal de navegación. **Propuesta: dejarla, y moverla al final
   dentro de un acordeón "Para el profesor: estado del sistema"**, o detrás de
   un parámetro de URL.
2. **"Colores" es personalización visual en la navegación primaria**, justo lo
   que NN/g dice que debe irse a ajustes (§3.2).
3. **"Leer" carga con 17 controles**, y el texto del libro —lo único que
   importa— aparece **después** de: subida de archivo, navegación de capítulos,
   acordeón de ficha, botón de resumen, selector de escala, acordeón de niveles
   CEFR, botón de medir, dos botones de análisis, un párrafo explicativo, dos
   huecos de resultado y una gráfica. El lector llega al libro al final de la
   maquinaria de medición. **Es exactamente el reproche de "se siente
   antigua"**: densidad de formulario, no de aplicación de lectura.

**[documentado]** Sobre pestañas: el consejo estándar es que las pestañas
representen **vistas alternativas de un mismo objeto**, no pasos de un proceso
ni cajones de sastre; cuando se abusa, *"entierran información clave y
convierten la navegación en un juego de adivinanzas"*
([Eleken, *Tabs UX*](https://www.eleken.co/blog-posts/tabs-ux)). Las de
LiteraLevel son hoy **tres cosas mezcladas**: un flujo (nivel → buscar → leer),
dos archivos personales (mis libros, mis palabras) y dos utilidades (colores,
estado).

**[opinión]** Reagrupación de cuatro pestañas que respeta el flujo:

| Pestaña nueva | Contiene |
|---|---|
| **Leer** (por defecto) | El lector, la consulta de palabras, la ficha, el análisis. Es donde debe abrir la app |
| **Descubrir** | Buscador, "Sorpréndeme", y la pregunta de nivel al final |
| **Lo mío** | Mis libros + Mis palabras + Pronunciación (que es práctica personal) + progreso de nivel |
| **Ajustes** | Colores, tamaño de letra, escala 0–2 / CEFR, idioma de la explicación, y el estado del sistema al fondo |

### 6.2 Estados vacíos que no enseñan nada

**[medido]** "Mis libros" y "Mis palabras" abren en **blanco**: solo se pintan
tras pulsar "Ver mis libros" / "Ver mis palabras" (`b_biblio.click`,
`b_cuaderno.click`). No hay `demo.load` ni `.select` que los rellene.

Dos consecuencias: el usuario nuevo ve una pestaña vacía y concluye que no hay
nada (o que no funciona); y el usuario que **sí** tiene datos tiene que
pedirlos. Hoy hay una `demo.load` gastada en `_diagnostico` (la pestaña que no
le importa a nadie) y ninguna en las dos pestañas que contienen el trabajo del
lector.

**[documentado]** Un estado vacío debe explicar qué irá ahí y ofrecer la
primera acción que lo llena
([patrón de estados vacíos, Carbon](https://carbondesignsystem.com/patterns/empty-states-pattern/)).
Los textos que ya hay —*"Se llena solo mientras lees"*— son buenos; el fallo es
que **hay que pulsar un botón para leerlos**.

### 6.3 No hay ni un indicador de progreso en toda la app

**[medido]** `grep -n "gr.Progress" app/ui.py` no devuelve nada en 2.431
líneas. Cuatro manejadores son generadoras y van informando por texto
(`_consultar`, `_abrir_del_catalogo`, `_analizar_libro`, `_seguir_leyendo`),
lo cual está muy bien; pero **`_buscar` no lo es**, y es la que puede tardar
entre 15 y 63 segundos (§2.2). Entre el clic y el resultado el usuario solo
tiene el indicador genérico de Gradio, y el aviso de "puede tardar cerca de un
minuto" está en un párrafo **encima** del botón, es decir, ya leído y olvidado
cuando llega la espera.

Esto es la heurística número uno de Nielsen —visibilidad del estado del
sistema— y no cuesta nada arreglarla: convertir `_buscar` en generadora con un
primer `yield` ("Indexando el catálogo por primera vez, unos 15 segundos…") es
el mismo patrón que ya usa `_consultar`, y el comentario del código lo explica.

### 6.4 Fallos típicos de las apps de Gradio, y cuáles tiene esta

**[documentado]** Lo que se rompe habitualmente en Gradio, con enlace:

| Fallo típico | ¿Lo tiene LiteraLevel? |
|---|---|
| **Componentes ocultos que se montan tarde**: en apps grandes con muchas pestañas y acordeones, el primer cambio a una pestaña no renderizada congela la interfaz mientras se montan los hijos ocultos ([issue #12891](https://github.com/gradio-app/gradio/issues/12891)) | **Riesgo bajo, vigilar.** El caso del issue son 2.289 componentes; aquí hay **96 construcciones de componente** en el código. Si se añaden listas por libro con controles propios, sube rápido. El parámetro `render_children` de `gr.Tab` es la palanca ([docs](https://gradio.app/docs/gradio/tab)) |
| **La fila de pestañas se desborda en móvil** | Sí, y lo cubre `diseno_lector.md` §7.2 |
| **`css=` en `Blocks` reescribe los selectores** | Ya evitado (usa `gr.HTML("<style>")`), documentado en `diseno_lector.md` |
| **Un solo proceso para todos los visitantes** | Ya resuelto con `_dir_lector(peticion)` y `session_hash` |
| **Colas y concurrencia**: en Gradio 6.26 el `default_concurrency_limit` es **1** salvo que se diga lo contrario ([`blocks.py`, línea 2570](https://gradio.app/docs/gradio/blocks)) | **Sin verificar en carga real.** Con un solo evento por vez y una espera de 63 s, dos visitantes simultáneos en la demo pueden hacer cola. Merece una prueba antes de la defensa |
| **Herramientas de desarrollo visibles al usuario** | Sí: la pestaña "Estado" (§6.1) |
| **Todo el estado en la sesión de navegador**: refrescar borra lo no persistido | Parcialmente resuelto: perfil, cuaderno, biblioteca y sesión van a disco |

**[medido]** Recuento de componentes:

```bash
python -X utf8 -c "import re; s=open('app/ui.py',encoding='utf-8').read(); \
print(len(re.findall(r'gr\.(Button|Radio|CheckboxGroup|Checkbox|Textbox|Dropdown|File|Number|Audio|Slider|Markdown|HTML|Plot|Accordion)\b', s)))"
# 96
```

### 6.5 Los mensajes de error: el único sitio donde ya se hace bien

**[documentado]** La guía de NN/g pide que los errores usen lenguaje llano,
digan con precisión cuál es el problema y **sugieran constructivamente una
solución**
([Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)).

`ui.py` lo cumple mejor que la mayoría del software comercial. Ejemplos del
código actual: cuando `por_nivel` no encuentra nada dice *"No hay libros
etiquetados entre 0,50 y 0,75. Prueba a describir lo que te apetece leer en el
buscador de arriba: ahí sí se ajusta a tu nivel sin exigir una coincidencia
exacta"*; cuando el libro no es de Gutenberg explica de dónde viene y qué
hacer. **No hay nada que arreglar aquí y conviene decirlo en la defensa**, que
es un punto fuerte poco visible.

La única excepción es la que se convierte en callejón: a nivel A1, el mensaje
es correcto pero **la salida que ofrece no existe** (§2.3). Un error bien
redactado que apunta a una puerta cerrada sigue siendo un callejón.

---

## 7. Qué encaja con **este** producto y qué no

### 7.1 La lectura extensiva ya tiene una teoría, y coincide con la app

**[documentado]** Day y Bamford (2002), *Top Ten Principles for Teaching
Extensive Reading*, **Reading in a Foreign Language 14(2)**
([NFLRC, Universidad de Hawái](https://nflrc.hawaii.edu/rfl/item/61)). Sus
principios, resumidos, son casi el pliego de requisitos de LiteraLevel:

1. **El material debe ser fácil para el alumno.**
2. Debe haber **variedad** de materiales y temas.
3. **El alumno elige** qué leer.
4. Se lee **tanto como sea posible**.
5. Se lee **por placer, información y comprensión general**, no por entenderlo
   al 100 %.
6. La velocidad de lectura debe aumentar.
7. **La lectura es su propia recompensa.**

El principio 7 es demoledor para cualquier plan de gamificación: en lectura
extensiva la evidencia pedagógica dice que **la recompensa es leer**, y
cualquier premio externo compite con ella. Coincide con SDT (§4.1). Hay incluso
trabajo que empareja explícitamente los principios de Day y Bamford con la
teoría de la autodeterminación
([ERIC EJ1167206](https://files.eric.ed.gov/fulltext/EJ1167206.pdf)).

Los principios 1 y 3 son los que LiteraLevel incumple hoy sin querer: el
principio 3 lo cumple bien (buscador libre en español), pero el **1 lo rompe el
catálogo** (§2.3: cero libros abribles fáciles, 99 de 148 en C2).

**[documentado]** Sobre "fácil": el umbral de referencia es el de Hu y Nation
(2000) —hace falta conocer en torno al **98 % del léxico** de un texto para
comprenderlo sin apoyo, o sea **una palabra desconocida de cada cincuenta**—,
con la advertencia importante de que la réplica reciente **no reproduce del
todo** el resultado y de que la cobertura léxica por sí sola es un predictor
débil
([Kremmel et al., *Language Learning* 2023](https://onlinelibrary.wiley.com/doi/10.1111/lang.12622) ·
[Nation, *Lexical text coverage*, PDF](https://files.eric.ed.gov/fulltext/EJ887873.pdf)).

Esto le da a LiteraLevel un argumento **propio y defendible**: como el
diccionario está dentro y una palabra se consulta seleccionándola, la app puede
sostener a un lector por debajo del 98 % de cobertura, que es donde un lector
con un libro de papel se hunde. Eso es diferenciación real y cabe en una
frase de la defensa.

### 7.2 ¿Tiene sentido una racha diaria en una novela? No

**[opinión, apoyada en §4 y §7.1]** No, por cuatro razones concretas y no por
prudencia genérica:

1. **La unidad de la actividad no es el día.** Una novela se lee a ratos
   desiguales: dos horas un domingo, nada durante la semana, cuarenta minutos
   en el autobús. Una racha diaria mide una cadencia que **la actividad no
   tiene**, y por tanto castiga la forma normal de leer.
2. **Premia lo contrario de lo que queremos.** El mínimo para salvar una racha
   es abrir y tocar; el objetivo del producto es **terminar capítulos**. Ya hay
   una métrica mejor y honesta a mano —capítulos terminados— y `biblioteca.py`
   la guarda.
3. **La usuaria es menor.** Las directrices del art. 28 del DSA nombran
   "streaks" entre las funciones a desactivar por defecto para menores (§5.2).
4. **La app no puede notificar.** Sin notificaciones, la racha solo funciona
   como castigo diferido: te enteras de que la perdiste **al volver**. Es la
   peor mitad de la mecánica sin la mitad que la sostiene.

**Lo que sí encaja y captura casi todo el valor**, sin ninguno de los cuatro
problemas: **una racha de libro, no de calendario.** "Llevas 7 capítulos de
*Alice*, 4 esta semana". Cuenta hacia algo que **termina**, no se pierde por
faltar un día, y el evento de celebración —terminar el libro— es real.

### 7.3 Qué más encaja, y qué no, en un lector para hispanohablantes

| Mecánica | ¿Encaja? | Razón |
|---|---|---|
| Continuar donde lo dejaste | **Sí, la primera** | Ya existe (`_reanudar`); solo hay que enseñarla en la portada |
| Progreso del libro y del capítulo | **Sí** | Información que el lector necesita; §4.5 |
| Contador de palabras del cuaderno | **Sí** | Es trabajo suyo acumulado, no puntos inventados |
| Volver a medir el nivel tras leer | **Sí, y es lo distintivo** | Cierra la promesa del producto; nadie más puede hacerlo |
| Metas puestas por el usuario, con margen | **Sí, si sobra tiempo** | SDT autonomía + Sharif y Shu (§4.5) |
| Celebrar el fin de capítulo | **Sí, sobrio** | Un evento real, no fabricado |
| Explicación en español de la palabra | **Sí, ya existe** | Es la ventaja concreta para hispanohablantes frente a Kindle |
| Racha diaria | **No** | §7.2 |
| Ligas, puntos, monedas, cofres | **No** | Sin cuentas no hay contra quién; y compiten con el principio 7 de Day y Bamford |
| Notificaciones | **No** | Imposible y prohibido para menores por defecto |
| Vidas / corazones que limitan la lectura | **No, rotundo** | Poner un tope artificial a **leer** es lo contrario del producto |
| Compartir logros en redes | **No** | Requiere identidad, y no la hay |

---

## 8. Cambios concretos, ordenados por efecto ÷ esfuerzo

Cada uno dice: **qué se cambia**, **en qué se apoya** y **cómo se sabría si
funcionó**. Todos son en `app/ui.py`, que es de Claude Code según `AGENTS.md`,
salvo donde se indique.

### 8.1 Una pregunta al entrar, y detrás una estantería

**Qué se cambia.** La app abre en una portada, no en el cuestionario:

- Un fragmento de inglés real (el de `fragmento_medio`, Conan Doyle) y **una
  sola pregunta**: *"¿Cuánto entiendes de esto?"*, con sus cinco opciones ya
  escritas en `perfil.FRAGMENTOS`.
- Al responder: se guarda el perfil con `desde_cuestionario({'fragmento_medio':
  v})` —**verificado que funciona con una sola clave**, §3.3— y se llama a
  `_recomendar`, que tarda 0,01 s, para pintar diez libros de su nivel.
- Las otras ocho preguntas pasan a un acordeón **"Afinar mi nivel (más
  preciso)"**, cerrado, debajo de la lista de libros.
- La cabecera de tres pasos ("1) Fija tu nivel · 2) busca · 3) lee") se
  sustituye por una frase de qué es esto y qué va a pasar.

**En qué se apoya.** Los 10 segundos de Nielsen (§3.1); "evita el onboarding,
y si personalizas, que sea breve y explicando por qué" de NN/g (§3.2); la
paradoja del usuario activo (§1); B=MAP, donde el cuello es la facilidad
(§4.3); y el hecho medido de que `perfil.py` ya admite una sola respuesta y
`por_nivel` responde en 0,01 s (§2.2, §3.3).

**Cómo se sabría.** Prueba con 3–5 personas nuevas, cronómetro en mano:
**segundos hasta ver el primer libro** (hoy: nunca, sin contestar nueve
preguntas; objetivo: < 15 s) y **segundos hasta tener texto en pantalla**.
Y la pregunta cualitativa que de verdad importa, la misma que falló:
*"¿Sabes qué hace esta app?"* al cabo de 30 segundos.

### 8.2 Empaquetar la caché de embeddings con el despliegue

**Qué se cambia.** Copiar `~/.literalevel/catalogo_emb_<huella>.npy` (1,84 MB)
junto a los datos del despliegue y hacer que `DIR_CACHE` apunte allí, o
sembrarlo en el arranque. **Ojo:** el nombre incluye la huella del CSV, y
`catalogo.embeddings` verifica que `len(emb) == len(df)`; si el CSV cambia, hay
que regenerarlo. Es una línea de `DESPLIEGUE.md` más que de código.

**En qué se apoya.** Medido: 47,9 s de codificación evitados, 14,8 s de carga
de modelo que siguen; de 63 s a 15 s en el peor caso (§2.2). Y `AGENTS.md` ya
avisa de que `~/.literalevel/` es disco efímero en un Space, o sea que **hoy
esos 63 segundos se pagarían en cada despertar**.

**Cómo se sabría.** Cronometrar la primera búsqueda tras un reinicio del Space.
Objetivo: por debajo de 20 s.

### 8.3 Recomendar solo lo que se puede abrir

**Qué se cambia.** Que `_recomendar` (y el ajuste por nivel del buscador) den
prioridad a los 148 libros de Gutenberg. Se puede hacer **sin tocar
`catalogo.py`**, que es archivo compartido: pedir `n * 5` a `por_nivel` y
filtrar en `ui.py` por `id.startswith("PG")` antes de quedarse con `n`.

Y para el tramo bajo, donde **no hay nada** (§2.3), decir la verdad y ofrecer
la salida que sí existe: *"Para tu nivel todavía no tengo libros que pueda
abrir aquí dentro. Dos opciones: empezar con [Grimms' Fairy Tales], que va un
punto por encima, o subir un libro tuyo."* Ambos caminos ya están construidos.

**En qué se apoya.** Medido: 0/10 abribles en A1, 2/10 en A2 (§2.3). Flow: un
principiante ante 99 libros C2 está fuera del canal por ansiedad (§4.2).
Principio 1 de Day y Bamford: el material debe ser fácil (§7.1).

**Cómo se sabría.** Prueba automatizable, no de opinión: para los once niveles
de 0,0 a 2,0, comprobar que **el `gr.Radio` de "Elige cuál abrir" nunca queda
vacío**. Hoy falla en 0,0 y 0,2. Cabe en `pruebas_integracion.py`.

### 8.4 Estados vacíos que enseñan, y sin botón

**Qué se cambia.** `demo.load(_mis_libros, ...)` y `demo.load(_mis_palabras,
...)` para que las dos pestañas lleguen llenas; y cuando estén de verdad
vacías, que muestren qué irá ahí y el botón que lo llena ("Buscar mi primer
libro" → salta a Descubrir). Los botones "Ver mis libros" / "Ver mis palabras"
pasan a "Actualizar" o desaparecen.

**En qué se apoya.** Medido: hoy solo se pintan al pulsar (§6.2). Patrón de
estado vacío (§6.2). Y la observación de Fogg de que cada paso extra mata la
acción (§4.3).

**Cómo se sabría.** Ninguna de las dos pestañas puede estar en blanco al
llegar. Verificable a ojo en un minuto.

### 8.5 Cuatro pestañas en vez de ocho

**Qué se cambia.** La reagrupación de §6.1: **Leer / Descubrir / Lo mío /
Ajustes**, con "Estado" dentro de Ajustes en un acordeón cerrado y rotulado
*"Para el profesor: estado del sistema"*.

**En qué se apoya.** Ocho pestañas de tres naturalezas distintas (§6.1);
NN/g sobre llevar la personalización visual a ajustes (§3.2); y el riesgo de
rendimiento del issue #12891 baja al haber menos subárboles ocultos (§6.4).

**Cómo se sabría.** Pregunta a un usuario nuevo: *"¿dónde crees que están los
libros que ya empezaste?"*. Hoy la respuesta correcta está repartida entre "Mis
libros" y la pestaña "Leer".

**Riesgo, y es real.** Es el cambio más invasivo de la lista: mover pestañas
implica mover `elem_id`, `gr.Tabs(selected=…)` y varios cableados que hoy
cruzan pestañas (`b_ir_buscar`, `b_abrir`, `b_seguir`). **Si el tiempo aprieta,
este es el primero que se cae**, y basta con sacar "Estado" y "Colores" de la
fila principal.

### 8.6 Que la espera larga se explique mientras ocurre

**Qué se cambia.** Convertir `_buscar` en generadora, como ya lo son
`_consultar` y `_analizar_libro`: primer `yield` inmediato con *"Indexando el
catálogo por primera vez (unos 15 segundos). Solo pasa una vez."*, segundo
`yield` con los resultados. Y corregir el texto fijo de "cerca de un minuto",
que sobreestima por cuatro el caso normal.

**En qué se apoya.** Medido: 15,1 s con caché, 0,03 s después, 63 s sin caché
(§2.2); no hay ningún `gr.Progress` en la app (§6.3); visibilidad del estado
del sistema.

**Cómo se sabría.** Que nadie cierre la pestaña durante la primera búsqueda en
las pruebas con usuarios. Es el fallo más probable de la demo en vivo.

### 8.7 Cerrar el bucle del nivel

**Qué se cambia.** Cuando el lector termina un libro (o llega al último
capítulo), ofrecer: *"Has terminado *Alice*. ¿Vuelvo a medir tu nivel con lo
que acabas de leer?"* → `desde_muestra` sobre el libro leído → enseñar el nivel
anterior y el nuevo, lado a lado, y **la lista de libros que ahora te quedan
dentro y antes no**.

**En qué se apoya.** SDT, necesidad de competencia (§4.1): es la evidencia de
"soy capaz" más fuerte que este producto puede dar, y es medida, no inventada.
Y es lo único de esta lista que **ningún competidor puede copiar sin un modelo
de dificultad**. La maquinaria existe entera: `_muestra_de_libro` ya toma ocho
trozos repartidos, `desde_muestra` ya devuelve un perfil.

**Cómo se sabría.** Cuántos lectores aceptan la remedición al terminar un
libro. Y, con más valor para la memoria del trabajo: si el nivel medido sube,
es un resultado presentable; si no sube, **también es un resultado**, y más
honesto que cualquier gráfica de retención.

### 8.8 Una sola ayuda contextual: la selección de palabras

**Qué se cambia.** La primera vez que se abre un capítulo, y **solo la
primera**, un aviso junto al texto: *"Toca dos veces una palabra (o mantenla
pulsada en el móvil) y te la explico."* Después no vuelve a salir.

**En qué se apoya.** Es el único punto de la app que cumple la excepción de
NN/g —interacción genuinamente novedosa que el usuario no puede adivinar—
(§3.2). Hoy se explica en un Markdown situado **debajo** del texto del
capítulo, o sea, después de todo el capítulo en un móvil.

**Cómo se sabría.** Porcentaje de usuarios de prueba que consultan alguna
palabra en su primera sesión sin que nadie se lo diga.

### 8.9 Racha de libro, si es que hay racha

**Qué se cambia.** En la ficha del libro abierto: *"Capítulo 7 de 24 · 4
capítulos esta semana"*. Nada de días. Nada que se pierda. Nada que parpadee.

**En qué se apoya.** §7.2 entero. Gradiente de meta con progreso **real**
(§4.5). Y el margen de Sharif y Shu está implícito: no hay nada que romper.

**Cómo se sabría.** Capítulos terminados por lector y semana, que es la métrica
que el §5.4 defiende. `biblioteca.py` ya guarda el capítulo actual por libro.

---

## 9. Lo que NO hay que hacer, con nombre y motivo

No repito la tabla de patrones de Brignull de `diseno_lector.md` §5.2. Estos
son los específicos de enganche, flujo y motivación, y los que la regulación
señala por su nombre.

1. **Racha diaria de calendario.** Nombre: *streak*; familia: *Addictive
   Design* en Brignull. Motivo: mide una cadencia que leer una novela no tiene;
   premia abrir en vez de leer; y **aparece nominalmente en la lista de
   funciones que las directrices de la Comisión Europea de julio de 2025 piden
   desactivar por defecto para menores** — y la primera usuaria tiene 15 años
   (§5.2, §7.2).
2. **Cualquier mensaje de culpa al volver.** *"Hace 5 días que no lees"*,
   *"Tu progreso se está enfriando"*, mascota triste. Nombre: *confirmshaming*.
   Motivo: es la técnica que la propia Duolingo usa (*"You made Duo sad"*) y la
   más criticada de todas (§5.3).
3. **Cuenta atrás o caducidad inventada.** *"Tu recomendación expira en 2
   horas"*. Nombre: *false urgency*. Motivo: la FTC lo pone en su primera
   familia —elementos que inducen creencias falsas— citando literalmente las
   cuentas atrás sobre ofertas que no están limitadas en el tiempo (§5.2).
4. **Prueba social fabricada.** *"37 personas están leyendo este libro"*.
   Nombre: *fake social proof / false activity messages*. Motivo: la FTC lo
   nombra con ese ejemplo exacto ("24 other people are viewing this listing"),
   y en esta app sería una mentira sin paliativos: no hay cuentas ni telemetría
   con la que saberlo (§5.2).
5. **Progreso regalado.** Empezar la barra del libro al 10 % para aprovechar el
   gradiente de meta. Nombre: *illusionary goal progress*, y está en el título
   del propio artículo de Kivetz et al. Motivo: funciona, y es exactamente por
   eso que es manipulación. En una herramienta que **presume de medir bien**,
   falsear la medida más visible destruye el argumento del trabajo (§4.5).
6. **Autoplay de capítulos.** Saltar solo al siguiente cuando termina uno.
   Motivo: es la mecánica que la Comisión Europea nombra en su decisión
   preliminar contra TikTok, y contra Instagram y Facebook, con el argumento
   del "piloto automático" (§5.2). El botón "Capítulo siguiente ›" que ya
   existe es la versión correcta: el lector decide.
7. **Notificaciones, recordatorios y correos.** Motivo: técnicamente imposible
   (no hay cuentas ni direcciones) y, además, prohibido por defecto para
   menores según las directrices del art. 28. Que sea imposible no es excusa
   para no decirlo: **decirlo es parte del argumento**.
8. **Ligas, puntos, monedas, cofres o recompensas aleatorias.** Motivo: sin
   identidad no hay contra quién competir, y el principio 7 de Day y Bamford
   —"la lectura es su propia recompensa"— más SDT dicen que los premios
   externos **desplazan** a la motivación intrínseca, que es justo la que
   sostiene leer una novela entera (§4.1, §7.1).
9. **Vidas, corazones o cualquier límite artificial a leer.** Motivo:
   contradice el producto en una sola frase. Se registra aquí porque es la
   mecánica más copiada de Duolingo y la tentación existe.
10. **Un tutorial de bienvenida con tarjetas.** Motivo: NN/g documenta que los
    tutoriales de tarjetas **no mejoran el rendimiento en la tarea**, y que
    incluso el botón de "saltar" tiene coste de interacción. Si hace falta un
    tutorial, es que la pantalla está mal (§3.2).
11. **Obligar al cuestionario completo antes de ver un libro.** Nombre:
    *obstruction*, y en el art. 25(3)(a) del DSA cae en "dar más prominencia a
    unas opciones sobre otras" cuando la alternativa está escondida. Motivo: es
    el estado actual y es lo que rompió la primera sesión de Esmeralda (§2.1).
12. **Optimizar "minutos en la app" o "sesiones por semana".** Motivo: son las
    métricas que se contaminan a sí mismas (argumento ya recogido en
    `diseno_lector.md` §5.3). Las honestas aquí son **capítulos terminados** y
    **palabras consultadas que luego se reconocen**.
13. **Usar la cifra de "12 % → 55 % de retención" de Duolingo.** Motivo: no
    verificada, origen en blogs de agencia (§5.3). Si se cita algo de Duolingo,
    que sea el **+14 % de retención a día 7 del Streak Wager**, diciendo en la
    misma frase que es **un test A/B interno de la propia empresa, sin revisión
    externa**. Y ni siquiera esa se necesita para el argumento.
14. **Reescribir `ui.py`.** Motivo: ya está en `diseno_lector.md` §11.1 y sigue
    valiendo. Los comentarios del archivo registran decisiones caras de
    descubrir (el `selectionchange` de iOS, el `.select` que evita el bucle del
    índice, la carga perezosa). Todos los cambios de §8 son quirúrgicos.

---

## 10. Guion de los primeros treinta segundos

Tal como debería ser. Los tiempos son los **medidos** en §2.2, no aspiraciones.

### Pantalla 1 — segundo 0 a 3. La portada

```
LiteraLevel
Lee libros en inglés al nivel que de verdad tienes.

  ┌──────────────────────────────────────────────┐
  │  "To Sherlock Holmes she is always the       │
  │  woman. I have seldom heard him mention      │
  │  her under any other name..."                │
  └──────────────────────────────────────────────┘

  ¿Cuánto entiendes de esto?

  ( ) Lo entiendo con naturalidad, sin releer
  ( ) Lo entiendo, aunque releo alguna frase
  ( ) Capto la idea; se me escapan palabras sueltas
  ( ) Entiendo partes, necesitaría diccionario
  ( ) Me pierdo

              [ Buscar libros para mí ]
```

Una sola pregunta. El texto de la pregunta y las cinco opciones **ya están
escritos** en `perfil.FRAGMENTOS[1]`. No hay pestañas visibles todavía, o hay
cuatro y ninguna reclama atención. No se pide nombre. No se pide nada más.

En tres segundos la usuaria ya sabe tres cosas: que esto va de leer en inglés,
que la app va a medir algo, y que se mide **con un texto real**, no con un
examen.

### Pantalla 2 — segundo 4 a 8. Diez libros suyos

Al pulsar, `desde_cuestionario` con una sola clave (0,01 s) y `por_nivel`
filtrado a abribles (0,01 s). En pantalla, sin espera perceptible:

```
Tu nivel: 0,80 de 2  (intermedio)
Te busco libros entre 0,65 y 0,95: cómodos, con algo de reto.

  ▸ Alice's Adventures in Wonderland — Carroll · B1
  ▸ The Adventures of Tom Sawyer — Twain · B1
  ▸ Adventures of Huckleberry Finn — Twain · B1
  ... (7 más, todos abribles)

  ( ) elige uno            [ Leerlo ahora ]

  ¿No te apetece ninguno? Dime qué buscas: [_______________]
  ▸ Afinar mi nivel con 8 preguntas más (opcional)
```

Esto es el momento de valor. **Ocho segundos desde que llegó.** Y es
íntegramente código que ya existe.

El acordeón de afinar queda **debajo** de los libros, cerrado, y ofrecido como
mejora, no como peaje. Quien quiera precisión lo abre; quien quiera leer, lee.

### Pantalla 3 — segundo 9 a 20. El libro se abre

Elige *Alice*, pulsa "Leerlo ahora". `_abrir_del_catalogo` ya es generadora y
ya informa mientras descarga de Gutenberg y salta sola a la pestaña de lectura.
Lo que hay que añadir es que lo que aparezca primero sea **el texto**, con la
ficha y la maquinaria de medición debajo o plegadas:

```
Alice's Adventures in Wonderland — Lewis Carroll
Capítulo 1 de 12 · unos 11 minutos de lectura

  Alice was beginning to get very tired of sitting by
  her sister on the bank, and of having nothing to do...

  ─────────────────────────────────────────────────
  Toca dos veces una palabra y te la explico.   [×]
```

Ese aviso es la única ayuda contextual de toda la app (§8.8), sale una vez, y
se cierra.

### Pantalla 4 — segundo 21 a 30. La primera palabra

Selecciona *bank*. La caja de consulta se rellena sola (`JS_SELECCION`, que ya
funciona), `_consultar` es generadora y **la primera etapa sale al instante**:
definición de Wiktionary, IPA y audio, sin red y sin esperar a OpenAI, que
llega después con la explicación de contexto.

A los treinta segundos la usuaria ha: dicho una cosa de sí misma, recibido un
nivel, visto diez libros que puede leer, abierto uno y consultado una palabra
con audio. **Ninguna de esas cinco cosas requiere código nuevo**: requieren
otro orden.

### Y lo que ve al volver mañana

`_reanudar` ya la deja en el capítulo donde estaba, con *"seguías en el capítulo
3 de 12"*. Lo único que falta es que en la portada, encima de todo, ponga:

```
  [ Seguir con Alice — capítulo 3 de 12 ]
```

Un botón. Es la mecánica de retención más honesta que existe, ya tiene los
datos detrás, y no hay ninguna decisión ética que tomar sobre ella.

---

## 11. Cómo medir si algo de esto funcionó

**[opinión]** Sin telemetría, y así debe seguir. Lo que se puede hacer, en
orden de coste:

1. **Cinco personas y un cronómetro.** Sentarse con 3–5 personas ajenas al
   proyecto —Esmeralda otra vez, si acepta— y medir cuatro cosas: segundos
   hasta el primer libro en pantalla; segundos hasta texto de libro en
   pantalla; si consultan una palabra sin que se lo digan; y la respuesta a
   *"¿qué hace esta app?"* a los treinta segundos. Con cinco personas se
   detectan la mayoría de los problemas graves de usabilidad, y **los tres
   primeros son cronómetro, no opinión**.
2. **Pruebas que codifican el bucle**, en `pruebas_integracion.py`: que para
   los once niveles de 0,0 a 2,0 el radio de "Elige cuál abrir" nunca quede
   vacío (§8.3); que un perfil con una sola respuesta produzca recomendaciones;
   que la primera búsqueda tras arrancar tarde menos de 20 s con la caché
   sembrada. Eso convierte los hallazgos de este informe en algo que no se
   puede volver a romper.
3. **Contadores locales honestos**, si se quiere una cifra para la memoria:
   **capítulos terminados** y **palabras consultadas**, que ya se guardan en
   `biblioteca.py` y `cuaderno.py`. No minutos de sesión, no aperturas.

Y una advertencia de método para la memoria del trabajo: con una lectora y una
sesión, **no hay resultado estadístico que presentar**. Lo presentable es el
razonamiento —el problema observado, la evidencia citada, el cambio hecho y la
prueba que impide la recaída—. Presentar eso con honestidad puntúa mejor que
una cifra de retención inventada sobre n = 1.

---

## 12. Fuentes

**Onboarding y primeros segundos**
- Nielsen Norman Group — [How Long Do Users Stay on Web Pages?](https://www.nngroup.com/articles/how-long-do-users-stay-on-web-pages/) (sobre los datos de Chao Liu et al., Microsoft Research: 205.873 páginas, >2.000 millones de tiempos de permanencia)
- Nielsen Norman Group — [Mobile-App Onboarding: An Analysis of Components and Techniques](https://www.nngroup.com/articles/mobile-app-onboarding/)
- Nielsen Norman Group — [Onboarding Tutorials vs. Contextual Help](https://www.nngroup.com/articles/onboarding-tutorials/)
- Nielsen Norman Group — [Onboarding: Skip it When Possible (vídeo)](https://www.nngroup.com/videos/onboarding-skip-it-when-possible/)
- Carroll, J. M. y Rosson, M. B. (1987). *Paradox of the Active User*, en *Interfacing Thought*, MIT Press — [PDF](https://research.cs.vt.edu/ns/cs5724papers/4.mental.mental.carroll.paradox.pdf) · [ficha en Laws of UX](https://lawsofux.com/paradox-of-the-active-user/)
- Norman, D. A. *The Design of Everyday Things* — sobre el autoinculpado del usuario y la *taught helplessness*: [resumen por capítulos](https://www.sharritt.com/CISHCIExam/norman.html)

**Motivación**
- Ryan, R. M. y Deci, E. L. (2000). *Self-Determination Theory and the Facilitation of Intrinsic Motivation, Social Development, and Well-Being*. **American Psychologist 55(1), 68-78** — [PDF](https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/11392867/)
- Csikszentmihalyi, M. *Beyond Boredom and Anxiety* (1975) y *Flow* (1990) — [síntesis académica](https://www.psy.gla.ac.uk/~steve/courses/pospsydocs/oldwikis/2015.20.Flow.pdf)
- Løvoll, H. S. y Vittersø, J. (2014). *Can Balance be Boring? A Critique of the "Challenges Should Match Skills" Hypotheses in Flow Theory*. **Social Indicators Research 115(1), 117-136** — [Springer](https://link.springer.com/article/10.1007/s11205-012-0211-9)
- Fogg, B. J. (2009). *A Behavior Model for Persuasive Design*. Persuasive '09 — [ACM](https://dl.acm.org/doi/10.1145/1541948.1541999) · [behaviormodel.org](https://behaviormodel.org/)
- Eyal, N. *Hooked* y el bucle detonante–acción–recompensa variable–inversión — [nirandfar.com](https://www.nirandfar.com/how-to-manufacture-desire/); matriz de manipulación — [Forbes, del propio autor](https://www.forbes.com/sites/nireyal/2012/07/02/the-art-of-manipulation/); crítica — [Axbom](https://axbom.com/nir-eyal-habit-danger/)
- Kivetz, R., Urminsky, O. y Zheng, Y. (2006). *The Goal-Gradient Hypothesis Resurrected*. **JMR 43(1), 39-58** — [PDF de los autores](https://home.uchicago.edu/ourminsky/Goal-Gradient_Illusionary_Goal_Progress.pdf) · [JMR](https://journals.sagepub.com/doi/abs/10.1509/jmkr.43.1.39)
- Sharif, M. A. y Shu, S. B. (2017). *The Benefits of Emergency Reserves*. **JMR 54(3), 495-509** — [PDF, Wharton](https://marketing.wharton.upenn.edu/wp-content/uploads/2016/10/The-Benefits-of-Emergency-Reserves-Greater-Preference-and-Performance-for-Goals-having-Slack-with-a-Cost.pdf) · [JMR](https://journals.sagepub.com/doi/abs/10.1509/jmr.15.0231); seguimiento en **OBHDP** (2019) — [PDF, UCLA](https://anderson-review.ucla.edu/wp-content/uploads/2021/03/Sharif-Shu_EmergencyReserveFailure_OBHDP2019.pdf)

**Regulación y patrones oscuros**
- Reglamento (UE) 2022/2065 (DSA), **art. 25** — [texto del artículo](https://www.eu-digital-services-act.com/Digital_Services_Act_Article_25.html) · [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2022/2065/oj/eng)
- Parlamento Europeo (2025). *Regulating dark patterns in the EU: Towards digital fairness* — [PDF](https://www.europarl.europa.eu/RegData/etudes/ATAG/2025/767191/EPRS_ATA(2025)767191_EN.pdf)
- Comisión Europea (14 jul 2025). *Directrices sobre la protección de menores, art. 28 DSA* — [anuncio](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-protection-minors) · [texto en el DOUE C/2025/5519](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:C_202505519)
- Comisión Europea (6 feb 2026). *Preliminary findings: TikTok's addictive design* — [nota](https://digital-strategy.ec.europa.eu/en/news/commission-preliminarily-finds-tiktoks-addictive-design-breach-digital-services-act)
- Comisión Europea (2026). *Preliminary findings: addictive design of Instagram and Facebook* — [nota](https://digital-strategy.ec.europa.eu/en/news/commission-preliminarily-finds-addictive-design-instagram-and-facebook-breach-digital-services-act)
- FTC (sep 2022). *Bringing Dark Patterns to Light* — [PDF](https://www.ftc.gov/system/files/ftc_gov/pdf/P214800+Dark+Patterns+Report+9.14.2022+-+FINAL.pdf) · [ficha](https://www.ftc.gov/reports/bringing-dark-patterns-light)
- Harry Brignull — [Types of deceptive pattern](https://www.deceptive.design/types)

**Duolingo (primera mano y crítica)**
- Duolingo — [How Streaks keep Duolingo learners committed](https://blog.duolingo.com/how-streaks-keep-duolingo-learners-committed-to-their-language-goals/) (Streak Wager: +14 % D7; datos internos)
- Duolingo — [How the Duolingo streak builds habit](https://blog.duolingo.com/how-duolingo-streak-builds-habit) (6 M de rachas ≥7 días; +1,7 %; +0,38 %; "3,6×", correlación sin control)
- The Decision Lab — [Streak Creep: When Gamified Engagement Mechanics Backfire](https://thedecisionlab.com/insights/consumer-insights/streak-creep-the-perils-of-too-much-gamification)
- **No verificado**: el "12 % → 55 %" de retención, difundido por [StriveCloud](https://www.strivecloud.io/duolingo-gamification-explained) y réplicas. Sin fuente primaria localizable. No usar.

**Lectura en segunda lengua**
- Day, R. y Bamford, J. (2002). *Top Ten Principles for Teaching Extensive Reading*. **Reading in a Foreign Language 14(2)** — [NFLRC, U. de Hawái](https://nflrc.hawaii.edu/rfl/item/61)
- Emparejamiento de esos principios con SDT — [ERIC EJ1167206](https://files.eric.ed.gov/fulltext/EJ1167206.pdf)
- Kremmel, B. et al. (2023). *Unknown Vocabulary Density and Reading Comprehension: Replicating Hu and Nation (2000)*. **Language Learning** — [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/lang.12622)
- Nation, I. S. P. — *Lexical text coverage, learners' vocabulary size* — [PDF, ERIC](https://files.eric.ed.gov/fulltext/EJ887873.pdf)

**Interfaz**
- Nielsen Norman Group — [Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- Nielsen Norman Group — [Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)
- Carbon Design System — [Empty states pattern](https://carbondesignsystem.com/patterns/empty-states-pattern/)
- Eleken — [Tabs UX Best Practices](https://www.eleken.co/blog-posts/tabs-ux)
- Gradio — [issue #12891: primer cambio de pestaña muy lento con hijos montados en diferido](https://github.com/gradio-app/gradio/issues/12891) · [documentación de `gr.Tab` y `render_children`](https://gradio.app/docs/gradio/tab)

**Del propio repositorio (medido, no citado de fuera)**
- `app/ui.py` — montaje de la interfaz (~1971-2318), `_recomendar` (~608), `_buscar` (~515), `_tabla_libros` y `_opciones_libros` (~513-575), `_reanudar` (~768), `_diagnostico` (~1969), `_ficha_libro` (~1115)
- `app/perfil.py` — `PREGUNTAS` (6), `FRAGMENTOS` (3, 165 palabras), `PESO_FRAGMENTOS = 0.65`, `desde_cuestionario` admite una sola respuesta
- `app/catalogo.py` — `por_nivel` (pandas, 0,01 s), `embeddings` y su caché `.npy` (1,84 MB), `NIVEL_A_PUNTUACION`
- `app/biblioteca.py` — capítulo por libro, ya persistido
- `AGENTS.md` — coste de importación del stack (~11,8 s), cachés efímeras en un Space, procedencia dudosa de las etiquetas CEFR del catálogo
- Gradio 6.26 instalado — `default_concurrency_limit` por defecto **1** (`blocks.py`, línea 2570)
