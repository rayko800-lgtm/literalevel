# Retención en el móvil: qué tomar de las redes sociales y qué no

**Psicología de la retención traducida a la versión Angular de LiteraLevel.**

Fecha: 12 de septiembre de 2026. Documento de investigación; no toca código ni
ningún archivo existente.

## Convenciones y relación con lo que ya existe

- **[verificado]**: fuente consultada en esta investigación (búsqueda web o
  lectura directa). Figura en las referencias.
- **[parte interesada]**: dato publicado por la propia empresa (tests A/B
  internos, sin revisión externa).
- **[secundaria]**: solo lo encontré en blogs jurídicos, prensa o sitios de
  terceros, no en la fuente primaria.
- **[opinión]**: criterio mío; lo sostiene el argumento que lo acompaña.
- **no verificado**: circula, pero no lo pude comprobar. No se usa como
  argumento.

Este informe **se apoya en** `enganche.md` y `diseno_lector.md` y no repite lo
que ya está allí: la teoría de la autodeterminación, el *flow*, la matriz de
manipulación de Eyal, el gradiente de meta, el margen de Sharif y Shu, la
taxonomía de Brignull, el artículo 25 del DSA, el informe de la FTC y las
cifras de Duolingo rastreadas (`enganche.md` §4–§5 y §9). Tampoco repite
tipografía, contraste ni zonas táctiles (`diseno_lector.md`).

**Lo que cambia respecto a esos dos informes.** Ambos se escribieron para una
app de Gradio sin cuentas y abierta en el navegador, y descartaron varias
mecánicas en parte **porque eran imposibles** («no hay a quién notificar»).
Una PWA de Angular instalada en la pantalla de inicio **sí puede** mandar
notificaciones, mostrar un número en el icono, funcionar sin conexión y
vibrar. A partir de ahora cada mecánica se acepta o se descarta **por lo que
vale**, no por lo que la plataforma impide. Ese es el hueco que cubre este
documento.

---

## 0. Resumen: diez recomendaciones por prioridad

**P0** = entra antes del 3 de octubre; **P1** = justo después; **P2** =
cuando haya usuarios reales.

| # | Recomendación | Mecanismo | Prioridad |
|---|---|---|---|
| 1 | **«Seguir leyendo»** como primera tarjeta de la portada, con la última frase leída | Tarea abierta (Ovsiankina) + facilidad (Fogg) | P0 |
| 2 | **Final de capítulo con dos botones del mismo peso**: «Siguiente capítulo» (con su primera frase como gancho) y «Parar aquí» | Tarea abierta sin quitar el punto de parada | P0 |
| 3 | **Todo lo que retiene, apagado de fábrica** y activable por el usuario; se diseña como si todos fueran menores | Directrices del art. 28 del DSA | P0 |
| 4 | **Progreso por nivel real**: «4 de 6 capítulos a tu nivel para volver a medirte» | Gradiente de meta + competencia | P0 |
| 5 | **Micro-interacciones sobrias** al consultar y guardar una palabra; nada que parpadee | *Feedback* informativo (Deci et al., 1999) | P0 |
| 6 | **Repaso espaciado** de 3 palabras del cuaderno, con su frase del libro, al abrir la app | Espaciado (Cepeda et al., 2006) | P1 |
| 7 | **Lectura sin conexión** del capítulo actual y del siguiente | Quitar fricción | P1 |
| 8 | **Racha semanal con comodín**, opcional y sin castigo al romperse | Racha adaptada (Silverman y Barasch, 2023; Lally et al., 2010) | P1 |
| 9 | **Volver a medir el nivel** al acumular capítulos leídos, con antes y después | Competencia (SDT) | P1 |
| 10 | **Una notificación semanal como máximo**, opcional, pedida tras terminar un capítulo, nunca de noche | Disparador externo limitado | P2 |

Y lo que se descarta, en una línea: **autoplay, scroll infinito entre
capítulos, racha diaria, contadores sociales, contenido efímero, recompensas
aleatorias, clasificaciones, número en el icono y avisos de «llevas mucho
tiempo»** (§3).

---

## 1. Los mecanismos, uno por uno

Cada uno con cómo funciona, qué evidencia hay y qué se lleva LiteraLevel.

### 1.1 Recompensa variable

**Cómo funciona.** En los programas de refuerzo de razón variable el premio
llega tras un número de respuestas que cambia y no se puede predecir. Ferster y
Skinner (1957) describieron sistemáticamente cómo cada programa de refuerzo
produce un patrón de respuesta propio **[verificado]**. El de razón variable es
el que produce respuesta sostenida y más resistente a la extinción: como no
sabes cuándo llega el premio, no dejas de intentarlo.

**En las plataformas.** El gesto de deslizar para refrescar y el feed son
máquinas de razón variable: cada deslizamiento puede traer algo bueno o nada.
Monge Roffarello et al. (2023) incluyen el scroll infinito en su tipología de
once *attention capture deceptive designs* **[verificado]**.

**Para LiteraLevel.** `enganche.md` §4.4 ya trazó la línea: la variabilidad
**del contenido** es legítima (cada palabra trae una etimología distinta, cada
capítulo pasa algo nuevo); la variabilidad **fabricada** (cofres, premios al
azar) no lo es. Un libro ya es una fuente de recompensa variable: no hace
falta añadirle otra.

### 1.2 Modelo Hook y modelo de Fogg (B = MAP)

Ambos están desarrollados en `enganche.md` §4.3–§4.4 (Eyal y Hoover, 2014;
Fogg, 2009 **[verificado]**). Lo que añade el móvil:

- **Detonante externo.** Ahora existe: notificación, número en el icono,
  correo. Y el **icono en la pantalla de inicio** es un detonante en sí mismo,
  pasivo y no intrusivo, que se ve cada vez que se desbloquea el teléfono.
- **Facilidad.** En el teléfono la distancia entre intención y lectura se mide
  en toques. Un toque en el icono y ya estás en la frase donde lo dejaste: esa
  es la versión máxima de la «A» de Fogg.
- **Inversión.** El cuaderno de palabras y la biblioteca son datos del usuario.
  Cuanto más contienen, más cuesta irse, y **eso es legítimo** mientras el
  usuario pueda llevárselos (exportar) y borrarlos.

### 1.3 Rachas y aversión a la pérdida

**Cómo funciona.** En la teoría prospectiva, la función de valor es más
empinada para las pérdidas que para las ganancias (Kahneman y Tversky, 1979)
**[verificado]**. La racha convierte un hábito en algo que se puede perder.

**Matiz que conviene saber.** Gal y Rucker (2018) sostienen que la evidencia no
respalda una tendencia **general** a que las pérdidas pesen más: depende del
contexto **[verificado]**. Es decir, el mecanismo psicológico de la racha no es
tan universal como lo venden los blogs de producto.

**Lo que sí está bien medido sobre rachas:**

- **Silverman y Barasch (2023)**, siete estudios en *Journal of Consumer
  Research* **[verificado]**: enseñar una racha intacta aumenta la conducta
  siguiente frente a enseñar una rota, y **el efecto depende de cómo se
  representa la conducta en el registro, no de la conducta real**. Mantener la
  racha se vuelve una meta en sí misma. El efecto de la racha rota **se agrava
  si la persona se culpa** y **se atenúa si puede «repararla»**.
- **Lally et al. (2010)**, 96 voluntarios durante 12 semanas **[verificado]**:
  el tiempo hasta la automaticidad varió **entre 18 y 254 días**, y **saltarse
  alguna repetición no afectó de forma material** a la formación del hábito.
- **Duolingo [parte interesada]**: permitir equipar dos «congeladores de
  racha» a la vez subió los usuarios activos un 0,38 %, y quienes llegan a 7
  días de racha tienen «3,6 veces más probabilidades de terminar su curso»
  (Mansur, 2022). Lo segundo es una correlación sin control (`enganche.md`
  §5.3).
- **Snapchat** permite restaurar una racha perdida **[verificado]** en su
  página de soporte, y ofrece restauraciones adicionales a los suscriptores de
  Snapchat+. Los precios que citan terceros **no los verifiqué**.

**Lectura combinada.** Silverman y Barasch explican por qué la racha funciona
**y** por qué es peligrosa: motiva a mantener el **registro**, no la
conducta. Lally explica por qué una racha **diaria** castiga algo que la
formación de hábitos no necesita. Y la reparación de Snapchat es la prueba de
que la aversión a la pérdida se puede **cobrar**. La versión aceptable para
LiteraLevel es la que tiene comodín incorporado, cuenta lo que importa y no
convierte perderla en un fracaso personal (§3, fila 8).

**Dos apoyos más.** El **efecto de nuevo comienzo** (Dai et al., 2014): tras
hitos temporales como el inicio de semana o de mes aumentan las conductas
aspiracionales **[verificado]**. Una racha semanal que se reinicia el lunes
aprovecha ese hito en vez de pelearse con él. Y en lectores: la app de Kindle
ofrece racha **semanal** además de diaria **[secundaria]**.

### 1.4 Scroll infinito y autoplay: eliminar los puntos de parada

**Cómo funciona.** El final de una página, de un episodio o de un capítulo es
un **punto de decisión**: ¿sigo? El scroll infinito y el autoplay lo eliminan,
y así la continuación deja de ser una decisión y pasa a ser lo que ocurre si no
haces nada.

**Evidencia regulatoria, que aquí pesa más que la experimental:**

- El **6 de febrero de 2026** la Comisión Europea concluyó preliminarmente que
  el diseño adictivo de TikTok infringe el DSA, nombrando **scroll infinito,
  autoplay, notificaciones push y recomendador altamente personalizado**, y
  habló de desactivar funciones y de pausas efectivas de pantalla, también de
  noche **[verificado]**.
- El **10 de julio de 2026** hizo lo mismo con **Instagram y Facebook**, y
  pidió **desactivar por defecto el autoplay y el scroll infinito** y un
  recomendador menos orientado a la interacción **[verificado]**.

**Contraejemplo de la propia industria.** En julio de 2018 Instagram introdujo
«You're All Caught Up», un mensaje al llegar al final de las publicaciones de
los dos últimos días **[verificado]**. Es un **punto de parada reintroducido a
propósito**: la industria sabe ponerlos cuando quiere.

**Para LiteraLevel.** Scroll continuo **dentro** del capítulo, sí: el capítulo
termina, y ese final es un logro (`enganche.md` §5.1). Pasar solo al capítulo
siguiente, no. El final del capítulo se diseña como un «estás al día» de
Instagram: una pausa con información, no un muro ni un tobogán.

### 1.5 Validación social y reciprocidad

**Cómo funciona.** Sherman et al. (2016) simularon Instagram en resonancia
magnética con **32 adolescentes de 13 a 18 años** **[verificado]**: tendían a
dar «me gusta» a fotos que ya tenían muchos, **también cuando mostraban
conductas de riesgo**, y ver fotos populares activaba más las regiones de
recompensa. La reciprocidad (Cialdini, 2021) es otra palanca: quien recibe algo
tiende a devolverlo **[verificado]**.

**En las plataformas.** Contadores de «me gusta», seguidores, «X ha visto tu
historia». Goodreads deja ver cómo van tus amigos en su reto de lectura
(Douaihy, 2026) **[verificado]**. En California, la ley SB 976 intentó ocultar
por defecto los contadores a los menores; el Noveno Circuito **bloqueó esa
parte** en septiembre de 2025 por probable inconstitucionalidad **[secundaria]**.

**Para LiteraLevel.** Una usuaria de 15 años es justo la población del estudio
de Sherman. Sin cuentas no hay red social que medir, y fabricarla («37
personas leen esto») sería prueba social falsa. La reciprocidad **legítima** ya
está en el diseño de las tres puertas (`PLAN_3_OCTUBRE.md` §3.1): **la app da
primero** (un capítulo abierto y palabras explicadas) y pide después (nivel,
instalación, permiso).

### 1.6 Notificaciones como disparador externo

**Coste.** Kushlev et al. (2016), **221 participantes**, diseño intrasujeto:
una semana con alertas activas y el teléfono a mano, y otra con alertas
apagadas y el teléfono lejos **[verificado]**. Las interrupciones del teléfono
aumentaron síntomas de **falta de atención e hiperactividad** en población no
diagnosticada.

**Beneficio, medido por quien más sabe de esto.** Duolingo publicó en KDD un
algoritmo de *bandit* para elegir el texto de sus recordatorios diarios
(Yancey y Settles, 2020) **[verificado]**. El resultado sobre una línea base
fuerte: **+0,5 % de usuarios activos diarios y +2 % de retención de usuarios
nuevos**. Dos lecturas honestas: optimizar millones de notificaciones al día da
mejoras **pequeñas**; y el artículo existe porque los mensajes pierden efecto
con la repetición (el «efecto novedad» que modelan).

**Norma.** Las directrices de la Comisión sobre menores piden **desactivar por
defecto las notificaciones push**, junto con rachas, contenido efímero y
autoplay (Comisión Europea, 2025) **[verificado]**. En Nueva York y California
las leyes para menores restringen las notificaciones **nocturnas** (y, en
California, en horario escolar) salvo consentimiento parental **[verificado /
secundaria]**; ver §2.

**Para LiteraLevel.** Una notificación **útil** existe: «tus 3 palabras de hoy
para repasar» o «el capítulo 5 empieza así: …». Pero debe ser **opcional,
pedida en contexto, espaciada y nunca nocturna**. Y hay un límite práctico que
decide la prioridad: el motor vive en un Space que **se duerme**, y un proceso
dormido no puede enviar avisos programados (§4.3).

### 1.7 Tareas abiertas: Zeigarnik y Ovsiankina

**El dato que casi nadie cita.** El efecto Zeigarnik —recordar mejor las tareas
interrumpidas— es el que se invoca siempre para justificar el «suspense» en
producto. Ghibellini y Meier (2025) metaanalizaron **59 publicaciones**
**[verificado]**: *«no encontramos ventaja de memoria para las tareas
inacabadas, pero sí una tendencia general a retomar tareas»*. El efecto
Zeigarnik **carece de validez universal**; el **Ovsiankina** —la tendencia a
**retomar** lo interrumpido— sí es general.

**Consecuencia de diseño.** Lo que funciona no es «que se acuerde del
cliffhanger», sino **que retomar sea fácil y visible**. Un capítulo a medias
con un botón «Seguir» en la portada explota el efecto que sí existe.

**En las plataformas de ficción seriada.** Kakao Page popularizó desde 2014 el
modelo de «esperar o pagar» el siguiente episodio **[secundaria]**. WEBTOON
tuvo un «Daily Pass» que desbloqueaba un episodio al día con caducidad a los 14
días **[verificado]**, y según prensa especializada lo retiró en 2025
**[secundaria]**. Es decir, el cliffhanger se convierte en **peaje**.

**Para LiteraLevel.** El cliffhanger ya lo escribió el autor; no hay que
fabricarlo. Lo que se diseña es **qué se ve al terminar**: la primera frase del
capítulo siguiente, sin ningún bloqueo, junto a un «Parar aquí» del mismo
tamaño.

### 1.8 Progreso dotado

**Cómo funciona.** Nunes y Drèze (2006): tarjetas de fidelidad en un lavado de
coches **[verificado]**. Una de 8 sellos vacía frente a una de 10 con 2 ya
puestos; ambas exigían 8 lavados. Completaron la tarjeta el **19 %** frente al
**34 %**. Una tarea «empezada» se sostiene más que una «por empezar».

**La línea.** `enganche.md` §4.5 y §9.5 ya descartaron el progreso **falso**
(empezar una barra al 10 % porque sí). Pero hay una versión **real**: si
alguien entra por «Solo quiero mirar» y lee el primer capítulo, **ese capítulo
ya cuenta**. «Llevas 1 de 6 capítulos para volver a medirte» es progreso dotado
**y** verdadero.

### 1.9 Personalización del feed

**Cómo funciona.** TikTok explica que su feed ordena por interacciones
(«me gusta», compartidos, comentarios), información del vídeo y ajustes del
dispositivo, y que mete a propósito contenido **fuera del punto dulce** para
diversificar (TikTok, 2020) **[verificado]**. La función objetivo es el tiempo
de visionado; el contenido es infinito.

**La distinción legal que le sirve a LiteraLevel.** La SB 976 de California
define el «feed adictivo» como el que selecciona contenido **por el
comportamiento del usuario en la plataforma y no por sus preferencias
explícitas** **[secundaria]**. LiteraLevel recomienda por **nivel declarado o
medido a petición** y por **lo que el usuario escribe en español**: está del
lado explícito. **[opinión]** Conviene mantenerlo así y decirlo en la defensa:
«recomendamos por lo que pides y lo que puedes leer, no por lo que te retiene».

### 1.10 Onboarding sin fricción y primer valor rápido

Desarrollado en `enganche.md` §3 y §10 y en las tres puertas de
`PLAN_3_OCTUBRE.md` §3.1. Lo que añade el móvil son **dos peticiones nuevas
que no se pueden hacer al entrar**:

- **Instalar.** Solo tiene sentido después del primer valor. En Chromium hay un
  evento para ofrecerlo desde la propia interfaz; en Safari y Firefox no existe
  (MDN, s. f.-a) **[verificado]**.
- **Permiso de notificaciones.** web.dev recomienda pedirlo cuando el
  beneficio sea obvio y con un **doble permiso**: primero un diálogo propio que
  explica para qué, y solo si acepta, el del sistema **[verificado]**. Firefox
  deniega automáticamente las peticiones que no nacen de un gesto del usuario
  desde la versión 72 (Mozilla, 2019) **[verificado]**, e iOS exige lo mismo
  (WebKit, 2023) **[verificado]**.

### 1.11 FOMO y contenido efímero

**Cómo funciona.** Przybylski et al. (2013) definieron el FOMO como la
aprensión a que otros vivan experiencias gratificantes de las que uno está
ausente **[verificado]**. Lo asociaron a **menor satisfacción de necesidades
psicológicas**, peor ánimo y menor satisfacción vital, y a **más uso de redes**.
Las historias de 24 horas y los desbloqueos que caducan lo explotan. Incluso
Goodreads ofrece marcapáginas digitales «disponibles por tiempo limitado»
(Douaihy, 2026) **[verificado]**.

**Para LiteraLevel.** Nada caduca. Un libro de Gutenberg de 1865 no puede
«desaparecer en 24 horas» sin mentir, y el contenido efímero está en la lista
de funciones que las directrices del art. 28 piden desactivar para menores.
**Descartado sin matices.**

### 1.12 Micro-interacciones y háptica

**Cómo funciona.** Saffer (2013) descompone una micro-interacción en
**disparador, reglas, *feedback*, bucles y modos** **[verificado]**. Es lo que
hace que una app «se sienta viva»: el botón que responde, la hoja que sube.

**El dato que decide cómo celebrar.** El metaanálisis de Deci et al. (1999),
**128 estudios** **[verificado]**: las recompensas **tangibles y esperadas**
—por participar, por completar o por rendimiento— **reducen** la motivación
intrínseca (d = −0,40, −0,36 y −0,28). El **feedback positivo** la
**aumenta** (d = 0,33 en conducta libre). Traducción directa: **informar
bien, no premiar**. «Has leído 2.400 palabras y consultado 6» sí;
«+50 puntos» no.

**Háptica en la web.** La Vibration API figura en MDN como **no soportada en
Safari ni en iOS** **[verificado]**. Una incidencia de marzo de 2026 en el
repositorio de compatibilidad de MDN afirma que ya funciona en iOS Safari:
**no verificado**. Consecuencia: la vibración es un **extra** para Android, con
detección de capacidad, y nunca el único *feedback*.

### 1.13 Añadidos relevantes para este producto

**Repaso espaciado.** El metaanálisis de Cepeda et al. (2006) reúne **839
evaluaciones en 317 experimentos** **[verificado]**: espaciar la práctica
mejora la retención, y el intervalo óptimo **crece con el tiempo que se quiere
retener**. Settles y Meeder (2016) entrenaron un modelo de «vida media» de cada
palabra con datos de Duolingo **[verificado]**. Redujeron más del 45 % el error
al predecir el recuerdo y, en un estudio operativo, subieron un 12 % la
interacción diaria **[parte interesada, pero publicado en ACL y con código
abierto]**. **Es la única mecánica de retención de este informe que es,
literalmente, una técnica de aprendizaje.**

**Estado actual [verificado sobre el repo].** `cuaderno.para_repasar` ya
existe: devuelve las palabras **más raras de las últimas 120** consultas, una
por lema, y `ui.py` la usa en el botón «Repasa 5». No es repaso espaciado
(no registra cuándo se repasó ni si se acertó), pero la tabla `consultas` ya
guarda palabra, lema, **frase del libro**, capítulo, rareza (zipf) y fecha. Lo
que falta es **una tabla de repasos**, no un rediseño.

**Leer mucho es el objetivo.** Day y Bamford (2002), principios 4 y 7: se lee
**tanto como sea posible**, y **la lectura es su propia recompensa**
**[verificado]**. Por eso aquí **no** se copian los avisos de «llevas mucho
tiempo» de las redes: dos horas con una novela no son el problema que resuelven
esos avisos.

---

## 2. Límites éticos y legales

### 2.1 El criterio, en tres preguntas

Para cada mecánica, antes de programarla:

1. **¿Sirve para leer o para abrir la app?** Si la métrica que mueve son
   aperturas y no capítulos o palabras retenidas, fuera.
2. **¿Se apaga en un toque, desde donde se ve?** Si no, es obstrucción.
3. **¿La aceptaría una madre que leyera su explicación en voz alta?** Si hay que
   esconder cómo funciona, es manipulación.

Los nombres de los patrones oscuros (confirmshaming, falsa urgencia, falsa
escasez, obstrucción, preselección) están en `diseno_lector.md` §5.2 y
`enganche.md` §9. Lo nuevo aquí son los **patrones de captura de atención**:
Monge Roffarello et al. (2023) los tipifican aparte de los de engaño comercial
porque no roban dinero ni datos, sino **tiempo**; entre ellos, el scroll
infinito y el autoplay **[verificado]**.

### 2.2 Qué dicen las normas, y cuáles obligan de verdad a LiteraLevel

| Norma | Qué dice sobre esto | ¿Obliga a LiteraLevel? | Estado |
|---|---|---|---|
| **DSA, art. 28 + directrices (UE, 14 jul 2025)** | Desactivar por defecto rachas, contenido efímero, confirmaciones de lectura, autoplay y notificaciones push; quitar diseño persuasivo orientado a la interacción | **Probablemente no**: el art. 19 excluye a las micro y pequeñas empresas de los arts. 19–28 salvo que sean plataformas de muy gran tamaño (CMS, s. f.); y **[opinión]** una app sin contenido de usuarios difícilmente es «plataforma en línea». **Se adopta como estándar de diseño** | Cita literal **[verificado]**; exención **[secundaria]** |
| **DSA, decisiones preliminares** | TikTok (6 feb 2026) y Meta (10 jul 2026): scroll infinito, autoplay, push y recomendador | No; marcan qué considera la Comisión «diseño adictivo» | **[verificado]** |
| **Ley de Equidad Digital (UE)** | Propuesta anunciada sobre patrones oscuros y diseño adictivo | No existe aún | Propuesta prevista para finales de 2026 **no verificado** en fuente primaria |
| **Age Appropriate Design Code (Reino Unido, ICO)** | 15 estándares. El 13, *nudge techniques*: no empujar a menores a dar datos innecesarios ni a bajar su privacidad; sí se permiten *nudges* a favor de su bienestar, como botones de pausa y guardado | Solo con usuarios en Reino Unido | Estándar 13 **[verificado]** (la página devolvió 403; contenido comprobado por el extracto del buscador del propio ICO). La lista de *sticky features* (bucles de recompensa, scroll continuo, notificaciones, autoplay) solo la vi citada por ESRB, posiblemente del borrador: **no verificado** en el texto final |
| **Online Safety Act (Reino Unido), códigos de Ofcom** | Desde el 25 de julio de 2025, filtrar contenido dañino en los feeds de menores | No (va sobre contenido dañino) | **[secundaria]** |
| **FTC, *Bringing Dark Patterns to Light* (EE. UU., 2022)** | Cuatro familias de patrones; el «consumidor razonable» de un público infantil es un miembro razonable de ese grupo | Marco interpretativo | **[verificado]** en `enganche.md` |
| **COPPA reformada (EE. UU.)** | Regla final publicada el 22 abr 2025; en vigor el 23 jun 2025; cumplimiento hasta el 22 abr 2026 | Solo para **menores de 13**; Esmeralda (15) no, pero una lectora de 12 sí | **[verificado]** |
| **SAFE for Kids Act (Nueva York)** | Sin consentimiento parental: sin feeds personalizados algorítmicos ni notificaciones nocturnas para menores de 18. Reglas finales el 28 jul 2026; vigor el 25 ene 2027 | No: aplica a plataformas con contenido de usuarios y ≥ 20 % del tiempo en feeds adictivos | **[verificado]** |
| **SB 976 (California)** | Sin consentimiento parental: sin feeds adictivos para menores ni notificaciones de noche o en horario escolar. El Noveno Circuito dejó aplicar lo central el 9 sep 2025 | No, por lo mismo | **[secundaria]**; que la obligación central de verificación de edad empiece el 1 ene 2027: **[secundaria]** |
| **SB 854 (Virginia)** | Límite por defecto de 1 h/día por plataforma a menores de 16 | No | Suspendida cautelarmente el 27 feb 2026 **[secundaria]** |
| **Age-Appropriate Design Code (Vermont)** | Privacidad máxima por defecto para menores; el fiscal general regulará prácticas que causen «uso compulsivo previsible» | No; vigor el 1 ene 2027 | **[secundaria]** |
| **LFPDPPP (México)** | Nueva ley publicada el 20 mar 2025, vigente el 21. Consentimiento libre, específico e informado; en datos de menores, **interés superior de la niñez**; autoridad: Secretaría Anticorrupción y Buen Gobierno | **Sí**, si trata datos personales de usuarios en México | Publicación y vigencia **[verificado]**; que el consentimiento de menores lo den padres o tutores, **[secundaria]** |
| **Diseño adictivo en México** | **No hay ley federal a septiembre de 2026.** Hay iniciativas: la del senador Dorantes (feb 2026) reforma la Ley General de los Derechos de Niñas, Niños y Adolescentes (privacidad por defecto, datos mínimos). En julio de 2026 la presidenta aclaró que el Gobierno **no** ha presentado iniciativa y abre un debate público | — | Iniciativa y declaración **[verificado]**; la cifra de «16 estados y casi 50 iniciativas», **no verificado** |

### 2.3 La consecuencia práctica, en un párrafo

Casi ninguna norma **obliga** a LiteraLevel: es pequeña, no es red social y no
aloja contenido de usuarios. Pero todas señalan **las mismas funciones**:
autoplay, scroll infinito, rachas, contenido efímero, notificaciones y feeds
por comportamiento. Y la usuaria real es menor. **[opinión]** La decisión
limpia es adoptar el estándar más exigente —las directrices del art. 28— **para
todos los usuarios**, sin preguntar la edad. Tiene tres ventajas: no hay que
recoger la fecha de nacimiento (el propio art. 28 dice que cumplir no obliga a
tratar datos adicionales para saber si alguien es menor), no hay dos versiones
de la app que mantener, y en la defensa se cuenta en una frase: **«todo lo que
retiene está apagado de fábrica y lo enciende el lector»**.

---

## 3. Traducción a LiteraLevel

La prioridad sigue la escala del §0. «—» = no se hace.

| # | Función concreta | Mecanismo | Por qué encaja con aprender a leer en inglés | Riesgo | Decisión | Prioridad |
|---|---|---|---|---|---|---|
| 1 | Tarjeta **«Seguir leyendo»** arriba de la portada: libro, capítulo y última frase leída | Ovsiankina; facilidad (Fogg) | Leer una novela es retomarla muchas veces; la frase reactiva el contexto | Ninguno relevante | **Adoptar** | P0 |
| 2 | **Final de capítulo**: resumen de 1 línea, palabras consultadas, primera frase del siguiente, y «Siguiente» y «Parar aquí» **del mismo tamaño** | Tarea abierta con punto de parada | El suspense lo pone el autor; decidir seguir es del lector | Que derive en autoplay o en botones desiguales (art. 25.3.a del DSA: prominencia) | **Adaptar** | P0 |
| 3 | Scroll continuo **dentro** del capítulo, con barra de progreso y final visible | Quitar fricción sin quitar el final | Leer sin paginar en el móvil (`diseno_lector.md` §4) | Bajo: el capítulo termina | **Adoptar** | P0 |
| 4 | Autoplay de capítulos o scroll infinito **entre** capítulos | Eliminar puntos de parada | Ninguno que no dé ya el n.º 2 | Exactamente lo que la Comisión señala en TikTok y Meta | **Descartar** | — |
| 5 | **Progreso por nivel**: «4 de 6 capítulos a tu nivel para volver a medirte» | Gradiente de meta; competencia | Hace visible la promesa central: subir de nivel leyendo | Meta demasiado lejana; elegir N pequeño | **Adoptar** | P0 |
| 6 | **Progreso dotado real**: el capítulo leído desde «Solo quiero mirar» cuenta como 1 de N | Nunes y Drèze (2006) | Convierte la curiosidad del primer minuto en tarea empezada | Que se infle con progreso falso: prohibido | **Adaptar** | P1 |
| 7 | **Remedición del nivel** tras N capítulos, con antes y después y «libros que ahora te quedan dentro» | Competencia (SDT) | Solo LiteraLevel puede hacerlo: lleva un modelo de dificultad | Que el nivel no suba y desanime; decirlo como resultado honesto | **Adoptar** (`enganche.md` §8.7) | P1 |
| 8 | **Racha semanal**: 1 capítulo en la semana; 1 comodín mensual **automático**; se reinicia el lunes; la rota no se muestra ni se nombra | Racha + margen (Sharif y Shu) + nuevo comienzo (Dai et al.) | Las novelas se leen a ratos desiguales; la semana respeta eso (Lally et al.) | Aparece nominalmente en las directrices para menores → **apagada por defecto**, sin notificaciones y sin reparación de pago | **Adaptar** | P1 |
| 9 | Racha **diaria** | Aversión a la pérdida | Castiga la forma normal de leer | Motiva mantener el contador, no leer (Silverman y Barasch) | **Descartar** | — |
| 10 | **Repaso espaciado**: al abrir, 3 palabras del cuaderno **con su frase del libro**; «la recordaba / no»; intervalos crecientes (p. ej. 1-3-7-21 días) | Espaciado (Cepeda et al.; Settles y Meeder) | Es aprendizaje de vocabulario, no enganche disfrazado | Convertirlo en deberes: máximo 3, y siempre saltable | **Adoptar** | P1 |
| 11 | **Micro-interacciones**: hoja inferior al tocar una palabra, marca breve al guardarla, barra que se llena al acabar el capítulo | Saffer (2013); *feedback* informativo | Hace tangible la acción clave: consultar sin salir del texto | Animaciones largas; respetar `prefers-reduced-motion` | **Adoptar** | P0 |
| 12 | **Vibración** de 10–15 ms al guardar una palabra | Háptica | Confirma sin mirar | No existe en iOS según MDN; interruptor en ajustes | **Adaptar** | P1 |
| 13 | **Celebración al terminar un libro**: palabras nuevas, minutos, nivel antes/después; sin puntos | Feedback positivo (Deci et al., 1999) | Refuerza competencia sin desplazar la motivación intrínseca | Tono infantil; que sea sobria | **Adoptar** | P1 |
| 14 | **Lectura sin conexión** del capítulo actual y del siguiente | Quitar fricción | El autobús sin datos es el caso real de una estudiante | Almacenamiento en iOS (§4.4) | **Adoptar** | P1 |
| 15 | **Instalación sugerida** tras terminar el primer capítulo, una vez, cerrable | Reciprocidad (primero se da) | El icono es el detonante más respetuoso que existe | Pedirla al entrar: cansa y se rechaza | **Adoptar** | P1 |
| 16 | **Notificación semanal opcional**: «tus 3 palabras de repaso» o «el capítulo 5 empieza así: …»; nunca entre 21:00 y 8:00 ni en horario escolar | Disparador externo | Recuerda **aprender**, no «vuelve» | Alto: push para menores; ruido (Kushlev et al.) → apagada por defecto, doble permiso y apagable desde la propia notificación | **Adaptar** | P2 |
| 17 | **Meta propia** a lo Goodreads (libros o capítulos al mes), editable en todo momento | Autonomía; compromiso | La pone el lector, no la app | Que se convierta en obligación; sin avisos de «vas atrasado» | **Adaptar** | P2 |
| 18 | **Número en el icono** con palabras pendientes de repaso | Disparador pasivo persistente | Poco: la notificación del n.º 16 ya cubre el caso | Presión constante; es *nagging* | **Descartar** | — |
| 19 | **Compartir una cita** del libro como imagen, iniciado por el usuario | Reciprocidad y expresión | Una frase subrayada es identidad lectora | Métricas sociales; sin contadores ni cuentas | **Adaptar** | P2 |
| 20 | Contadores sociales, «X personas leyendo», ligas, clasificaciones | Validación social | Ninguno: no hay comunidad real que medir | Prueba social falsa; adolescentes muy sensibles (Sherman et al.) | **Descartar** | — |
| 21 | Contenido efímero, desbloqueos que caducan, «esperar o pagar» | FOMO | Ninguno: los libros no caducan | Falsa escasez; en la lista de las directrices para menores | **Descartar** | — |
| 22 | Cofres, premios aleatorios, puntos, monedas | Recompensa variable fabricada | Compite con «la lectura es su propia recompensa» | Desplaza la motivación intrínseca (Deci et al.) | **Descartar** | — |
| 23 | Recomendación por **nivel y consulta explícita**, con capítulos a tu medida | Personalización | Es el producto | Derivar hacia «más de lo que ya leíste» por comportamiento | **Adoptar** (ya existe) | P0 |
| 24 | Avisos de «llevas 45 minutos, ¿descansas?» | Límite de sesión | Leer mucho es el objetivo (Day y Bamford) | Interrumpe la lectura que se busca | **Descartar** | — |

**Lo que se descarta y por qué, en una línea cada uno:**

- **Autoplay y scroll infinito entre capítulos:** quitan al lector la decisión
  de seguir y son lo que la Comisión persigue en TikTok y Meta.
- **Racha diaria:** mide una cadencia que leer novelas no tiene y motiva a
  mantener el contador, no a leer.
- **Contadores sociales y ligas:** no hay comunidad real, y fabricarla es
  prueba social falsa ante la población más sensible a los «me gusta».
- **Contenido efímero y desbloqueos con caducidad:** falsa escasez; figuran en
  la lista para menores.
- **Recompensas aleatorias, puntos y monedas:** desplazan la motivación
  intrínseca que sostiene leer un libro entero.
- **Número en el icono:** presión permanente que ya cubre, mejor, una
  notificación semanal opcional.
- **Avisos de tiempo de sesión:** resuelven un problema del scroll, no de la
  lectura.

---

## 4. Implementación en Angular móvil

### 4.1 PWA e instalación

- `ng add @angular/pwa` registra el *service worker*, añade el manifiesto, los
  iconos y `ngsw-config.json` (Angular, s. f.-a) **[verificado]**.
- En el manifiesto, `display: "standalone"`: es **requisito** para Web Push en
  iOS (WebKit, 2023) **[verificado]**.
- **Instalación:** en Chromium se captura el evento de instalación y se ofrece
  con un botón propio tras el primer capítulo; en iOS no hay evento (MDN,
  s. f.-a) **[verificado]**. Ahí se muestra una tarjeta, una sola vez, con
  «Compartir → Añadir a pantalla de inicio».

### 4.2 Navegación y gestos

- **Barra inferior con tres destinos**, los de `PLAN_3_OCTUBRE.md` §3.4:
  **Leer · Encontrar · Tu nivel**. Zonas de 48 px (`diseno_lector.md` §7.1) y
  margen inferior con `env(safe-area-inset-bottom)` para el iPhone.
  **[opinión]** En el lector, la barra se oculta al bajar y reaparece al subir.
- **Gestos [opinión]:** **nada de deslizar para cambiar de capítulo**, porque
  choca con la selección de texto (la función estrella) y con el gesto de
  volver del sistema. **Desactivar «deslizar para refrescar»** en el lector con
  `overscroll-behavior: contain`: es uno de los patrones de captura
  documentados, y en un libro no hay nada que refrescar.
- **Pantalla encendida mientras se lee:** la Screen Wake Lock API funciona ya
  en todos los navegadores principales (web.dev, s. f.-b) **[verificado]**. Se
  pide al abrir un capítulo y se libera al salir o al perder visibilidad. Que
  en PWA instaladas de iOS fallara hasta la 18.4: **[secundaria]**.

### 4.3 Web Push y sus restricciones

| Plataforma | Qué hace falta | Estado |
|---|---|---|
| Android (Chrome) | *Service worker* + permiso tras gesto del usuario; no hace falta instalar | Estándar |
| iOS/iPadOS 16.4+ | **App instalada en la pantalla de inicio**, manifiesto `standalone`, permiso **tras interacción directa** («un botón de suscribirse») | **[verificado]** (WebKit, 2023) |
| iOS/iPadOS 18.4+ | Además, **Declarative Web Push**: notificaciones descritas en JSON sin necesitar *service worker* | **[verificado]** (WebKit, 2025) |
| Firefox 72+ | Permiso solo tras gesto del usuario; si no, denegado | **[verificado]** (Mozilla, 2019) |

- En Angular: `SwPush.requestSubscription()` con clave VAPID pide el permiso y
  devuelve la suscripción (Angular, s. f.-b) **[verificado]**.
- **El obstáculo real no es el navegador, es el servidor.** El motor está en un
  Space que **se duerme** por inactividad (`PLAN_3_OCTUBRE.md` §6). Enviar
  avisos programados exige un proceso despierto o un disparador externo que lo
  despierte, además de guardar suscripciones. **Por eso las notificaciones son
  P2**, no por prudencia. La librería de Python para enviar Web Push **no la he
  verificado**.

### 4.4 Service worker y lectura sin conexión

- En `ngsw-config.json`, un `dataGroup` para `/api/libro/*/capitulo/*` con
  estrategia de rendimiento (el texto de un capítulo no cambia) y otro de
  frescura para búsqueda y nivel **[opinión sobre la configuración; el
  mecanismo, verificado en la documentación de Angular]**.
- **Precargar el capítulo siguiente** al pasar del 80 % del actual.
- Posición de lectura y repasos pendientes, en **IndexedDB**, con cola de envío
  cuando vuelva la red.
- **Trampa de iOS [verificado]:** WebKit borra el almacenamiento escribible por
  script (IndexedDB, LocalStorage, registros de *service worker*) de un sitio
  **tras 7 días de uso de Safari sin interacción**. Las apps **añadidas a la
  pantalla de inicio están exentas** (WebKit, 2020). Otro motivo para sugerir la
  instalación: sin ella, el marcapáginas local puede desaparecer. La copia
  buena sigue siendo la del servidor (`/data`).

### 4.5 Carga y espera

- **Esqueletos** (*skeleton loaders*) para lo que tarda menos de ~2 s:
  resultados de búsqueda, portada, capítulo desde caché.
- **[opinión]** Para las esperas largas medidas (primera consulta léxica ~55 s,
  curva ~134 s en frío, `PLAN_3_OCTUBRE.md` §3.5), un esqueleto **miente**:
  promete algo inminente. Ahí va texto de estado con fase y tiempo estimado, y
  el lector sigue pudiendo leer mientras tanto.
- Vibración: `if ('vibrate' in navigator)`, patrones de 10–15 ms, interruptor
  en ajustes y nunca como único *feedback* (§1.12).

### 4.6 APIs del motor que harían falta

Encima de los siete *endpoints* de `PLAN_3_OCTUBRE.md` §5 (salud, medir,
buscar, libro, capítulo, palabra, curva). Todos **leen o escriben** en módulos
existentes o en tablas nuevas, **sin tocar los módulos congelados**:

| *Endpoint* | Para qué | Prioridad |
|---|---|---|
| `GET /api/inicio` | En **una** llamada: «seguir leyendo», progreso por nivel y repasos del día. En el móvil cada viaje de red cuesta | P0 |
| `GET /api/biblioteca` · `POST /api/progreso` | Libros empezados; capítulo terminado y fracción leída (sobre `biblioteca.py`) | P0 |
| `GET /api/repaso` · `POST /api/repaso/{id}` | Palabras que tocan hoy; «la recordaba / no». Necesita una tabla de repasos nueva junto a `consultas` | P1 |
| `POST /api/nivel/remedir` | Remedición sobre lo leído (`desde_muestra`) | P1 |
| `POST /api/eventos` | Contadores agregados del §5 | P1 |
| `POST/DELETE /api/push/suscripcion` | Alta y baja de avisos | P2 |

**Identidad sin cuentas [opinión]:** un identificador aleatorio generado en el
dispositivo, guardado en IndexedDB y enviado en una cabecera, que sustituye al
`session_hash` de Gradio para localizar los datos del lector en `/data`. Si se
pierde, se pierde la biblioteca: en P2, un «código de recuperación» que el
lector puede apuntar.

---

## 5. Métricas: saber si funciona sin recoger de más

### 5.1 Qué medir

**Definición de «activo» [opinión, y es la decisión clave]:** un lector está
activo un día si **leyó al menos una pantalla de un capítulo** o **hizo un
repaso**. Abrir la app **no cuenta**. Así la retención no se puede inflar con
aperturas vacías (el problema de la racha, §1.3).

| Métrica | Definición | Qué dice |
|---|---|---|
| **Retención D1 / D7 / D30** | % de lectores nuevos de un día que están **activos** exactamente 1, 7 y 30 días después | Si vuelven. **[opinión]** Para lectura conviene añadir **semanal (S1, S4)**: activo en la semana 1 y en la 4. La novela no tiene cadencia diaria |
| **Capítulos terminados por lector activo y semana** | Capítulos que llegan al final / lectores activos | Si leen, que es la meta |
| **Libros empezados que se terminan** | La métrica A9 de `estrategia.md` | Si la recomendación acierta |
| **Tiempo hasta el primer capítulo abierto** | Segundos desde la primera carga | Si las tres puertas funcionan |
| **% que consulta una palabra en la primera sesión** | — | Si se descubre la función estrella |
| **Acierto en repaso a 7 días** | «La recordaba» / repasos con intervalo ≥ 7 días | **Aprendizaje**, no enganche |
| **«Parar aquí» frente a «Siguiente»** | Proporción al final de capítulo | Salud del diseño: si nadie para nunca, el final empuja demasiado |
| **Métricas de freno** | % que desactiva notificaciones en 30 días; % de aperturas desde notificación con menos de 30 s de lectura | Si los avisos son ruido. **Si suben, se retira el aviso, no se optimiza el texto** |

### 5.2 Cómo medirlo con datos mínimos

- **Nada de SDK de terceros** ni identificadores publicitarios.
- **Retención sin rastrear a nadie [opinión]:** el dispositivo guarda **su
  propia** fecha de alta y, cuando hay actividad, envía un evento sin
  identificador: `{tipo: "activo", dias_desde_alta: 7}`, **como mucho una vez
  al día por tipo** (deduplicado en el dispositivo). El servidor suma. D7 =
  eventos «activo» con `dias_desde_alta = 7` de una cohorte / altas de esa
  cohorte. Se obtiene la curva sin poder seguir a ninguna persona.
- **Sin IP, sin agente de usuario, sin texto** de lo que se lee o se consulta
  en los eventos. Agregados por día; eventos brutos borrados a los 90 días
  **[opinión sobre el plazo]**.
- Para visitas de páginas, si hace falta, una analítica sin cookies ni datos
  personales como la que describe Plausible (s. f.) **[verificado]**.
- Aviso de privacidad en español y en una pantalla, coherente con los
  principios de la LFPDPPP (consentimiento libre, específico e informado)
  **[verificado]**.

### 5.3 Honestidad de método

Antes del 3 de octubre **no habrá base estadística**: habrá la prueba con cinco
lectores del accionable A8. Las métricas del §5.1 son para después, y en la
defensa se presentan como **instrumentación diseñada**, no como resultados.

---

## 6. Qué no pude verificar

- La lista de *sticky features* del código del ICO (bucles de recompensa,
  scroll continuo, notificaciones, autoplay) en el **texto final**: solo la vi
  en un blog de ESRB que parece citar el borrador. La página del ICO devolvió
  403.
- Fechas de entrada en vigor y periodo de transición del código del ICO.
- Que la Ley de Equidad Digital de la UE se proponga a finales de 2026 (solo
  sitios de seguimiento de terceros).
- Que la Vibration API funcione ya en iOS Safari (incidencia de marzo de 2026
  sin confirmar).
- Que WEBTOON retirara el Daily Pass en 2025, y las cifras de negocio de Kakao
  Page (fuentes secundarias o de contenido patrocinado).
- Las rachas de Kindle y su funcionamiento exacto (solo fuentes secundarias;
  no encontré la página de ayuda de Amazon).
- Los precios de restauración de rachas de Snapchat.
- Que el consentimiento para tratar datos de menores en la nueva LFPDPPP lo den
  padres o tutores (lo afirma un análisis jurídico; no leí el artículo en el
  DOF).
- La cifra de «16 estados y casi 50 iniciativas» sobre redes y menores en
  México.
- Los detalles de aplicación de la SB 976 desde el 1 de enero de 2027 y el
  estado exacto de los litigios de Virginia y Vermont después de las fechas
  citadas.
- El fallo de Wake Lock en PWA de iOS antes de la 18.4.
- La librería de Python para enviar Web Push.
- El artículo original de Zeigarnik (1927): no lo consulté; lo cito solo a
  través del metaanálisis de 2025.

---

## Referencias

Angular. (s. f.-a). *Getting started with service workers*.
https://angular.dev/ecosystem/service-workers/getting-started

Angular. (s. f.-b). *Push notifications*.
https://angular.dev/ecosystem/service-workers/push-notifications

Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., y Rohrer, D. (2006).
Distributed practice in verbal recall tasks: A review and quantitative
synthesis. *Psychological Bulletin, 132*(3), 354–380.
https://doi.org/10.1037/0033-2909.132.3.354

Cialdini, R. B. (2021). *Influence, new and expanded: The psychology of
persuasion*. Harper Business.

CMS. (s. f.). *Article 19: Exclusion for micro and small enterprises*. CMS
DigitalLaws. https://www.cms-digitallaws.com/en/dsa/article-19/

Comisión Europea. (2025). *Guidelines on measures to ensure a high level of
privacy, safety and security for minors online, pursuant to Article 28(4) of
Regulation (EU) 2022/2065* (C/2025/5519).
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:C_202505519

Comisión Europea. (2026a, 6 de febrero). *Commission preliminarily finds
TikTok's addictive design in breach of the Digital Services Act* [Nota de
prensa].
https://digital-strategy.ec.europa.eu/en/news/commission-preliminarily-finds-tiktoks-addictive-design-breach-digital-services-act

Comisión Europea. (2026b, 10 de julio). *Commission preliminarily finds the
addictive design of Instagram and Facebook in breach of the Digital Services
Act* [Nota de prensa].
https://digital-strategy.ec.europa.eu/en/news/commission-preliminarily-finds-addictive-design-instagram-and-facebook-breach-digital-services-act

Dai, H., Milkman, K. L., y Riis, J. (2014). The fresh start effect: Temporal
landmarks motivate aspirational behavior. *Management Science, 60*(10),
2563–2582. https://doi.org/10.1287/mnsc.2014.1901

Day, R. R., y Bamford, J. (2002). Top ten principles for teaching extensive
reading. *Reading in a Foreign Language, 14*(2), 136–141.
https://nflrc.hawaii.edu/rfl/item/61

Deci, E. L., Koestner, R., y Ryan, R. M. (1999). A meta-analytic review of
experiments examining the effects of extrinsic rewards on intrinsic motivation.
*Psychological Bulletin, 125*(6), 627–668.
https://doi.org/10.1037/0033-2909.125.6.627

DLA Piper. (2026, marzo). *Virginia's social media time-limit law for minors
blocked: Key takeaways*. Privacy Matters.
https://privacymatters.dlapiper.com/2026/03/virginias-social-media-time%E2%80%91limit-law-for-minors-blocked-key-takeaways/

Douaihy, T. (2026, 20 de mayo). *Join the Goodreads Reading Challenge*.
Goodreads. https://www.goodreads.com/blog/show/3144-join-the-goodreads-reading-challenge

Eyal, N., y Hoover, R. (2014). *Hooked: How to build habit-forming products*.
Portfolio.

Federal Trade Commission. (2022). *Bringing dark patterns to light* [Informe].
https://www.ftc.gov/reports/bringing-dark-patterns-light

Federal Trade Commission. (2025, 22 de abril). Children's Online Privacy
Protection Rule [Regla final]. *Federal Register*.
https://www.federalregister.gov/documents/2025/04/22/2025-05904/childrens-online-privacy-protection-rule

Ferster, C. B., y Skinner, B. F. (1957). *Schedules of reinforcement*.
Appleton-Century-Crofts.

Fogg, B. J. (2009). A behavior model for persuasive design. En *Proceedings of
the 4th International Conference on Persuasive Technology* (Artículo 40,
pp. 1–7). ACM. https://doi.org/10.1145/1541948.1541999

Gal, D., y Rucker, D. D. (2018). The loss of loss aversion: Will it loom larger
than its gain? *Journal of Consumer Psychology, 28*(3), 497–516.
https://doi.org/10.1002/jcpy.1047

Ghibellini, R., y Meier, B. (2025). Interruption, recall and resumption: A
meta-analysis of the Zeigarnik and Ovsiankina effects. *Humanities and Social
Sciences Communications, 12*, Artículo 962.
https://doi.org/10.1057/s41599-025-05000-w

Hunton Andrews Kurth. (2025). *Ninth Circuit upholds «addictive» social media
feed ban and default privacy settings for minors in California's Protecting Our
Kids from Social Media Addiction Act*. Privacy and Cybersecurity Law Blog.
https://www.hunton.com/privacy-and-cybersecurity-law-blog/ninth-circuit-upholds-addictive-social-media-feed-ban-and-default-privacy-settings-for-minors-in-californias-protecting-our-kids-from-social-media-addiction-act

Information Commissioner's Office. (s. f.). *13. Nudge techniques*. En *Age
appropriate design: A code of practice for online services*.
https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/age-appropriate-design-a-code-of-practice-for-online-services/13-nudge-techniques/

Infobae. (2026, 28 de julio). *¿Hay una iniciativa de ley para regular que
menores usen redes sociales? Sheinbaum aclara campaña de concientización*.
https://www.infobae.com/mexico/2026/07/28/hay-una-iniciativa-de-ley-para-regular-que-menores-usen-redes-sociales-sheinbaum-aclara-campana-de-concientizacion/

Instagram. (2018, 2 de julio). *Introducing «You're All Caught Up» in Instagram
Feed*.
https://about.instagram.com/blog/announcements/introducing-youre-all-caught-up-in-feed

Kahneman, D., y Tversky, A. (1979). Prospect theory: An analysis of decision
under risk. *Econometrica, 47*(2), 263–291. https://doi.org/10.2307/1914185

KED Global. (s. f.). *Kakao Page Corp: The big bang that created the webtoon
universe* [Contenido patrocinado].
https://www.kedglobal.com/kakao_page_corp/brandedContent/brd0001

Kushlev, K., Proulx, J., y Dunn, E. W. (2016). «Silence your phones»:
Smartphone notifications increase inattention and hyperactivity symptoms. En
*Proceedings of the 2016 CHI Conference on Human Factors in Computing Systems*.
ACM. https://doi.org/10.1145/2858036.2858359

Lally, P., van Jaarsveld, C. H. M., Potts, H. W. W., y Wardle, J. (2010). How
are habits formed: Modelling habit formation in the real world. *European
Journal of Social Psychology, 40*(6), 998–1009.
https://doi.org/10.1002/ejsp.674

Ley Federal de Protección de Datos Personales en Posesión de los Particulares.
(2025). *Diario Oficial de la Federación*, 20 de marzo de 2025.
https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf

Mansur, O. (2022, 31 de enero). *How the Duolingo streak builds habit*.
Duolingo Blog. https://blog.duolingo.com/how-duolingo-streak-builds-habit

MDN Web Docs. (s. f.-a). *BeforeInstallPromptEvent*. Mozilla.
https://developer.mozilla.org/en-US/docs/Web/API/BeforeInstallPromptEvent

MDN Web Docs. (s. f.-b). *Navigator: vibrate() method*. Mozilla.
https://developer.mozilla.org/en-US/docs/Web/API/Navigator/vibrate

Monge Roffarello, A., Lukoff, K., y De Russis, L. (2023). Defining and
identifying attention capture deceptive designs in digital interfaces. En
*Proceedings of the 2023 CHI Conference on Human Factors in Computing Systems*.
ACM. https://doi.org/10.1145/3544548.3580729

Mozilla. (2019, noviembre). *Upcoming notification permission changes in
Firefox 72*. Mozilla Hacks.
https://hacks.mozilla.org/2019/11/upcoming-notification-permission-changes-in-firefox-72/

Nunes, J. C., y Drèze, X. (2006). The endowed progress effect: How artificial
advancement increases effort. *Journal of Consumer Research, 32*(4), 504–512.
https://doi.org/10.1086/500480

Office of the New York State Attorney General. (2026, 28 de julio). *Attorney
General James and Governor Hochul release final SAFE for Kids Act rules to
protect children online* [Nota de prensa].
https://ag.ny.gov/press-release/2026/attorney-general-james-and-governor-hochul-release-final-safe-kids-act-rules

Partido Acción Nacional en el Senado. (2026, febrero). *Presenta Agustín
Dorantes iniciativa a fin de fortalecer marco de protección de redes sociales
para niñas, niños y adolescentes*.
https://www.pan.senado.gob.mx/2026/02/presenta-agustin-dorantes-iniciativa-a-fin-de-fortalecer-marco-de-proteccion-de-redes-sociales-para-ninas-ninos-y-adolescentes/

Plausible Analytics. (s. f.). *Data policy*. https://plausible.io/data-policy

Przybylski, A. K., Murayama, K., DeHaan, C. R., y Gladwell, V. (2013).
Motivational, emotional, and behavioral correlates of fear of missing out.
*Computers in Human Behavior, 29*(4), 1841–1848.
https://doi.org/10.1016/j.chb.2013.02.014

Saffer, D. (2013). *Microinteractions: Designing with details*. O'Reilly Media.

Settles, B., y Meeder, B. (2016). A trainable spaced repetition model for
language learning. En *Proceedings of the 54th Annual Meeting of the
Association for Computational Linguistics* (Vol. 1, pp. 1848–1858).
Association for Computational Linguistics. https://aclanthology.org/P16-1174/

Sharif, M. A., y Shu, S. B. (2017). The benefits of emergency reserves: Greater
preference and persistence for goals that have slack with a cost. *Journal of
Marketing Research, 54*(3), 495–509. https://doi.org/10.1509/jmr.15.0231

Sherman, L. E., Payton, A. A., Hernandez, L. M., Greenfield, P. M., y Dapretto,
M. (2016). The power of the like in adolescence: Effects of peer influence on
neural and behavioral responses to social media. *Psychological Science,
27*(7), 1027–1035. https://doi.org/10.1177/0956797616645673

Silverman, J., y Barasch, A. (2023). On or off track: How (broken) streaks
affect consumer decisions. *Journal of Consumer Research, 49*(6), 1095–1117.
https://doi.org/10.1093/jcr/ucac029

Snap Inc. (s. f.). *I lost my Streak. How do I restore it?* Snapchat Support.
https://help.snapchat.com/hc/en-us/articles/7012318024852-I-lost-my-Streak-How-do-I-restore-it

TikTok. (2020, 18 de junio). *How TikTok recommends videos #ForYou*. TikTok
Newsroom. https://newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you

web.dev. (s. f.-a). *Permission UX*. Google.
https://web.dev/articles/push-notifications-permissions-ux

web.dev. (s. f.-b). *The Screen Wake Lock API is now supported in all
browsers*. Google.
https://web.dev/blog/screen-wake-lock-supported-in-all-browsers

WEBTOON. (s. f.). *What is Daily Pass?* WEBTOON Support.
https://webtoon.zendesk.com/hc/en-us/articles/360051129172-What-is-Daily-Pass

WebKit. (2020). *Full third-party cookie blocking and more*.
https://webkit.org/blog/10218/full-third-party-cookie-blocking-and-more/

WebKit. (2023, 16 de febrero). *Web Push for web apps on iOS and iPadOS*.
https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/

WebKit. (2025). *Meet Declarative Web Push*.
https://webkit.org/blog/16535/meet-declarative-web-push/

White & Case. (2025). *UK Online Safety Act: Protection of Children Codes come
into force*.
https://www.whitecase.com/insight-alert/uk-online-safety-act-protection-children-codes-come-force

Yancey, K. P., y Settles, B. (2020). A sleeping, recovering bandit algorithm
for optimizing recurring notifications. En *Proceedings of the 26th ACM SIGKDD
International Conference on Knowledge Discovery & Data Mining*. ACM.
https://doi.org/10.1145/3394486.3403351

**Fuentes secundarias consultadas y no citadas como evidencia:** Good e-Reader
sobre las rachas de Kindle; K Comics Beat (2025) sobre la retirada del Daily
Pass; ESRB sobre las *sticky features* del código del ICO; Wilson Sonsini y
Hunton sobre la ley de Vermont; Xident sobre la SB 976 en 2027; sitios de
seguimiento de la Ley de Equidad Digital.
