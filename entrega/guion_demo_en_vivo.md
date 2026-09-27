# Guion de la demo en vivo — Pléyade, proyecto LiteraLevel (Módulo 5)

*Puesto al día el 26 de septiembre de 2026: Vercel, datos por cuenta, boca 3D
didáctica y Mi espacio. Las capturas de referencia están en `capturas/`
(`registro.txt` dice de dónde sale cada una).*

**Formato de la rúbrica:** de 3 a 5 minutos, **cámara abierta y pantalla
compartida**, centrado en la **usabilidad**, y después preguntas del profesor.
La rúbrica de Classroom lo dice así: «describir de forma breve el reto que se
busca resolver y la interfaz de uso donde se evidencie cómo a través de su(s)
modelo(s) seleccionado(s) se da resolución a la problemática planteada».

**Cuándo:** la demo de Miguel es el **10 de octubre de 2026, turno 5** (lista
«M5G34 - Proyectos.pdf» de la tarea «Trabajo Final», leída el 26 de septiembre;
el otro día es el 8 de octubre). Los archivos se entregan en Classroom antes del
**4 de octubre, 11:59 p.m.** Si no se puede presentar ninguno de los dos días,
hay que avisar al profesor antes para presentar la semana anterior; si no, los
25 puntos se pierden solos.

**Objetivo: 4:00 de demo.** Lo que sobra hasta 5:00 es el colchón para las
esperas reales (despertar el motor, la explicación de la IA, el audio). Si un
paso se atasca más de lo previsto, **se dice lo que tendría que salir y se
pasa al siguiente**: una demo que se queda mirando una rueda pierde más que un
paso saltado.

Cómo leer este guion:

- **Dice:** lo que Miguel dice en voz alta, a cámara o mirando la pantalla.
- **Hace:** lo que se toca en pantalla. No se lee.
- Todas las cifras que se dicen están en `documento.tex`. No añadir otras en
  directo.

---

## Antes de conectarse

Una por una, y marcando:

- [ ] **Front abierto** en `https://pleyade-app.vercel.app` (respaldo:
      `https://mikemaki1763-literalevel-front.static.hf.space/`, la misma app),
      en el navegador del equipo con la vista de dispositivo a 390 px, o el
      móvil duplicado en pantalla. Solo esa pestaña compartida: nada de consola,
      contraseñas ni otras pestañas.
- [ ] **Motor despierto.** Abrir en otra pestaña (sin compartir)
      `https://mikemaki1763-literalevel.hf.space/api/salud` y comprobar que dice
      `"buscador_listo": true`, que es lo que hace falta para buscar. `/api/estado`
      responde también, pero sirve para otra cosa —el recuento de libros— y no trae
      ese campo. Después, en el front, **hacer una
      búsqueda de prueba**: la primera tras el arranque es la lenta —0,90 s frente
      a 0,47 s la siguiente, medido el 16 de septiembre—. Consultar una palabra no
      hace falta para calentar: tarda unos 1,0 s desde la primera.
- [ ] **Sesión iniciada** en *Ajustes → Tu perfil*, **fuera de plano**, con una
      cuenta que tenga **cupo**: explicar una palabra, resumir un libro y
      corregir la pronunciación salen a un servicio de pago y gastan cupo.
      **Desde el 26 de septiembre el perfil y las palabras son de la cuenta**, no
      del navegador: lo que prepares en el ordenador lo verás igual en el móvil,
      y al revés.
- [ ] **Perfil de 1,20 sobre 2 ya puesto** (banda intermedia). **Ojo: es el perfil
      de tu cuenta.** Tu nivel real, medido en la app el 26 de septiembre, es C2,
      1,88 (receta: «Casi todos los días» · fácil «Lo entiendo con naturalidad, sin
      necesidad de releer» · «Sí, una obra clásica o especializada» · medio, lo mismo ·
      «También los detalles y las relaciones entre ideas» · difícil, lo mismo). Pon el
      de 1,20 para la demo y vuelve a medirte después. En directo no se
      responde el cuestionario: no garantiza ese número. **Receta** (medida por e6
      en local y contra el Space, y por 4e con la fórmula, 15 de septiembre): en
      *Tu nivel*, las seis respuestas en orden: «Varias veces por semana»; en el
      fragmento fácil, «Lo entiendo con naturalidad, sin necesidad de releer»;
      «Sí, una novela actual»; en el fragmento medio, «Lo entiendo con
      naturalidad, sin necesidad de releer»; «Los hechos o argumentos
      principales»; y en el difícil, «Entiendo algunas partes, pero necesitaría el
      diccionario para seguirlo». Al contestar la sexta **se guarda solo**. El
      titular dirá «Lees en inglés a nivel B2»: que no sorprenda al decir «banda
      intermedia». El 1,20 está plegado en «Ver el detalle». Un despiste de una
      opción en cualquier respuesta deja el perfil en B2, entre 1,07 y 1,27, salvo
      en la sexta: «Capto bien la idea» da 1,46, que ya es C1.
- [ ] **Boca 3D abierta una vez** antes de compartir pantalla (*Pronunciar* → un
      sonido → «Boca en 3D»). Es la boca didáctica nueva: desde el 26 de septiembre
      baja 1,7 MB por la red en vez de 3,5 y **tarda unos 3 s en verse** (medido el
      26 de septiembre contra Vercel, en un navegador sin caché y desde el equipo del
      autor: 3,0 y 3,1 s; 8,9 s la primera vez, cuando la CDN aún no tenía el
      archivo): ábrela antes para que en directo salga de la caché. Tiene zoom
      (+ y −), «Despacio» y «Explorar».
- [ ] **_Crime and Punishment_ abierto una vez** y con su **curva ya
      calculada**: queda guardada y en directo sale al momento.
- [ ] **Una palabra ensayada** del capítulo abierto y **otra que el diccionario
      no traiga** (un nombre propio raro), para enseñar la marca **IA** o un
      «Puede ser».
- [ ] **Frase de voz ensayada:** «Don't you want to come with us?». Leerla
      **una vez antes** en *Pronunciar*, para que su análisis quede guardado y en
      directo salga sin esperar. **Ya no se da por verificada**: la comprobación
      de f4 (Space `7c09d90`, 14 de septiembre) es anterior a la pantalla nueva de
      *Pronunciar*. Se repite con cuenta en el punto 4 de «Antes de la demo». Si
      entonces no sale ningún enlace, no prometer el arco de *with us*.
- [ ] **Auriculares con micrófono** conectados y probados. Nivel de entrada
      comprobado en el sistema.
- [ ] **«Reducir movimiento» apagado** en el sistema: con él encendido, la boca
      sale quieta.
- [ ] **Grabación de respaldo** del recorrido completo, abierta en un
      reproductor y **rotulada en pantalla como «Grabación previa»**. Solo se usa
      si falla algo del plan B, y se dice que es una grabación.

## Antes de la demo, con cuenta y micrófono

Lo que el ensayo de e6 (`auditoria/ensayo_demo_2026-09-15.md`) no pudo probar
sin cuenta ni micrófono. Miguel lo ensaya en su teléfono antes de la demo,
**habiendo entrado en *Ajustes → Tu perfil***. Si un punto falla, se ensaya lo
que dice el **Plan B** para ese paso.

1. **Paso 4:** cuánto tardan en llegar «En español» y «Aquí significa» con
   *poverty* (se llega por *Índice → «Antes del primer capítulo»*).
2. **Paso 4, la marca IA:** con qué palabra sale. Sin cuenta, *Mihail* solo
   dice «no está en el diccionario».
3. **Paso 5:** grabar «Una frase de mi libro» con una palabra mal dicha a
   propósito. Cuánto tarda «Corrígeme», y si salen el sonido que falla y su
   «Escuchar y ver». **Si pruebas *Pronunciar* en frío, sin haber abierto un
   libro, ese botón no está:** depende del libro en curso, no de la pantalla, y
   aparece al volver desde el lector (medido el 16 de septiembre por e6 sobre la
   revisión `9b4a3b5` del Space, del commit `a1c4268`). No es un fallo; escribe la frase a mano.
4. **Paso 6:** «Don't you want to come with us?». Que, al abrir «Para sonar
   más natural», salgan *doncha* y *wanna*, «no pares aquí» y «Escúchalo
   natural», y cuánto tarda.
5. **Paso 7:** que la palabra mal pronunciada aparezca en «Mis palabras».
   **Ensáyalo con cuenta:** sin entrar, una palabra que el diccionario no trae no se
   guarda, porque solo se apuntan las que traen acepción.
6. **El cronómetro:** la demo entera, contra los 3–5 minutos. **La máquina no es
   el problema:** suma unos pocos segundos en toda la demo, y las cifras por paso
   cambian de una medida a otra con la red. El 16 de septiembre, la primera
   búsqueda dio 0,90 s en una medida y 1,26 s en otra; la ficha con la curva,
   1,19 s y 2,19 s; el primer pintado del front, 256 y 480 ms. La primera medida es
   sobre la revisión `f4920fa` del front; la segunda, la del ensayo final
   (`auditoria/ensayo_demo_final_2026-09-16.md`). Lo que ocupa el tiempo es hablar:
   unos **3:02**, que es una **estimación** a 145 palabras por minuto y no una
   medida —a 130 palabras por minuto el total hablado sube de 175 a 195 s—. Dentro
   de 5:00 quedan 1:58 para los pasos 5 y 6; dentro del 4:00 que fija este guion,
   **58 s**, y el guion les asigna 60: cabe, pero justo. Lo único que falta por
   medir es cuánto tarda «Corrígeme» (`auditoria/cronometro_demo_2026-09-16.md`).
7. **Una frase en voz baja desde el móvil:** grabarla hablando bajo y comprobar
   que se oye y se corrige. Si sale «No te oí», apuntarlo y avisar antes de
   grabar la demo. La aplicación descarta la grabación cuando whisper da, en
   todos sus trozos, más de 0,6 de probabilidad de que no haya voz; la voz más
   baja que se probó, sintética, dio 0,503. Con cuenta, el aviso termina en
   «Este intento no cuenta.» y ese intento no gasta usos.
8. **El motor, despierto y con el buscador listo.** El Space de la API se
   suspende a las **48 h exactas sin visitas** (`sleep_time` 172.800 s, leído de
   la API de Hugging Face el 16 de septiembre), así que:
   - **La víspera, abre la aplicación una vez.** Con eso el contador de 48 h
     vuelve a empezar y el Space llega despierto a la demo.
   - **Diez minutos antes, abre `/api/salud`** y comprueba que dice
     `"buscador_listo": true`. Si lo dice, no hay nada más que hacer.
   - **Si no está listo, espera con esa pestaña abierta de uno a minuto y
     medio**, que es lo que tarda el arranque. **No recargues en bucle** ni
     abras más pestañas: no acelera nada.
   - **Si a los dos minutos no responde,** abre la página del Space y mira la
     fase: con `Error` es un fallo, no una siesta, y hay que avisar.
   - **La primera búsqueda tras el arranque va más lenta** y la siguiente
     responde en unos 0,3 s. Aun así, calienta el buscador antes de compartir
     pantalla con una búsqueda de prueba en *Encontrar*, con tu perfil ya
     guardado, y espera a que salgan las tarjetas.

   Las cifras del arranque son de **arranques por despliegue**, no de un
   despertar desde la suspensión, que no se ha medido: de 26 a 85 s hasta
   `RUNNING` en los diez despliegues de `DESPLIEGUE.md` —los cuatro últimos, de
   46 a 72 s— y de 12 a 14 s más hasta `buscador_listo` desde el reinicio 30a
   (`auditoria/ronda4_arranque_demo_f4_2026-09-16.md`). El front es estático, no
   se duerme y se pinta en 0,64 s, pero todo lo que no sea pintarse espera a la
   API.
9. **Paso 3:** con el perfil de 1,20, buscar «Crimen y castigo de Dostoyevski» y
   comprobar que sale el aviso de que no hay libros en tu nivel ni un poco por
   encima, y *Crime and Punishment* el primero en «De otros niveles».
10. **La bienvenida:** en un navegador limpio o en incógnito, al abrir Inicio sale
    una tarjeta de cuatro pasos («1 de 4» y, debajo, «¿Ya tienes cuenta?», con
    «Entrar» y «Seguir sin cuenta»). **La decisión es tuya:** recórrela una vez antes
    de grabar, o pulsa «Saltar», arriba a la derecha de la tarjeta, y enseña la
    aplicación directamente; las dos formas valen. **Sale dos veces en ese
    navegador**, porque aquí se entra antes de la demo: la de sin cuenta al abrir
    Inicio y, al entrar con tu cuenta, otra, que empieza por «Ya tienes cuenta» y
    dice qué gasta usos. Sáltalas o recórrelas las dos antes de compartir pantalla.
    En un navegador donde ya la viste, sin cuenta no vuelve; con cuenta sale esa
    segunda una sola vez. Un enlace directo al lector o a una ficha no la muestra, y
    se puede volver a ver desde *Ajustes* → «Ver la bienvenida otra vez».
11. **Las ayudas de la primera vez:** al abrir el lector sale arriba «Mantén
    presionada una palabra para ver qué significa; desliza para cambiar de
    página.», y en *Pronunciar*, en lugar del subtítulo, «Escribe o trae una frase,
    grábate leyéndola y te digo qué sonido corregir…». Ciérralas con ✕ antes de
    compartir pantalla (vuelven con el «?» de la barra del lector y el del título de
    *Pronunciar*), para que no tapen el libro ni la frase.
12. **Si hay que recortar, en este orden**, y no improvises otro: primero la
    **segunda búsqueda del paso 2**, unos 15 s; después la **segunda palabra del
    paso 4**, unos 10 s; y solo si «Corrígeme» va lento, el **paso 6 entero**, unos
    35 s, que es el segundo ejemplo de lo mismo que enseña el 5. **No se recortan
    la curva del paso 3 ni la consulta del paso 4:** son el producto.
13. **No gastes correcciones en la hora previa.** «Corrígeme» tiene **10 por hora**, y
    la demo usa una o dos: sobran si no ensayas en ráfaga. El tope va **por conexión,
    no por cuenta**, así que ensayar y grabar desde la misma red gastan el mismo cupo:
    un ensayo largo desde casa se come el de la demo. La cuenta es deslizante: el
    aviso dice cuándo vuelve **la primera**, no todas. Las explicaciones (30 por
    hora) y los resúmenes (6) llevan su propio cupo, y agotar uno no toca los otros.
    **Si aun así llegas al tope**, no hay ningún ajuste que tocar: la salida es
    reiniciar el Space, que borra el contador, al precio del arranque en frío del
    punto 8 (de uno a minuto y medio). Pídelo **antes** de empezar, nunca a mitad de
    la demo. Con el tope agotado siguen funcionando leer lo que ya abriste, buscar,
    el diccionario, grabarte y escucharte.

---

## El recorrido

### A — Atención · 0:00 – 0:20

**Hace:** cámara a pantalla completa un momento; luego comparte el front.

**Dice:** «Quien quiere leer en inglés suele fallar antes de la primera página:
elige un libro que le queda grande y lo abandona. Pléyade le dice, antes de
empezar, qué libro le va y le acompaña mientras lo lee. Se lo enseño en el
móvil.»

### N — Necesidad · 0:20 – 0:40

**Dice:** «Hay decenas de miles de libros gratis, pero casi ninguno trae su
dificultad medida, y un libro no es igual de difícil de principio a fin. Por
eso el catálogo está medido capítulo a capítulo: 53.179 libros de Project
Gutenberg y, además, 15.367 textos de licencia libre.»

### S — Satisfacción · 0:40 – 3:40

**1. Entrar y el nivel (0:40 – 1:00)**

**Hace:** *Tu nivel*. Enseña el resultado ya preparado («Lees en inglés a nivel B2») y
abre «Ver el detalle» para que se vea el 1,20. Señala abajo «¿No te convence?
Afínalo con un libro que ya leíste · con un texto».

**Dice:** «Primero, mi nivel. Tres preguntas y tres fragmentos, o un texto que
ya leo cómodo. Para esta demo tengo un perfil preparado: 1,20 sobre 2, banda
intermedia. Es una escala propia: la letra del Marco Común es solo
orientativa.»

**2. Encontrar (1:00 – 1:25)**

**Hace:** *Encontrar*. Escribe «cuentos de dragones». Con el perfil de 1,20,
«En tu nivel» abre con cuentos de licencia libre: 19 de sus 20 tarjetas en la
página publicada con el reinicio 28 (15 de septiembre, medido a 390 px). Con
«una novela de detectives victoriana» no sale ningún cuento libre: en «En tu
nivel» salen 3 libros, los tres de Gutenberg.

**Dice:** «Busco en español y me devuelve libros por significado, con su nivel
al lado. Y entre los clásicos salen cuentos de licencia libre, que es donde está
la lectura de nivel bajo que Gutenberg no tiene.»

**3. Abrir un libro y su ficha (1:25 – 1:50)**

**Hace:** busca «Crimen y castigo de Dostoyevski» y abre *Crime and Punishment*.
Con el perfil de 1,20 sale primero el aviso de que no hay libros en tu nivel ni
un poco por encima, y el libro aparece el primero en «De otros niveles», que ya
se ve sin pulsar nada: es lo esperado. Enseña la ficha y la curva. No escribas
solo «dostoyevski»: con el perfil de 1,20, «En tu nivel» se llena de cuentos que
no son suyos y el libro queda detrás de «Ver también» (ensayo del 15 de septiembre
sobre los reinicios 28 y 30b, a 390 px: con la consulta larga el libro queda a 679 px sin
pulsar nada; con «dostoyevski», a 3.789 px).

**Dice:** «Abro *Crimen y castigo*. La ficha está contada sobre el texto, no
escrita por un modelo, y la curva dice cómo se complica capítulo a capítulo. De
media, 1,70: me queda por encima, y lo sé antes de la primera página.»

**4. Una palabra en su frase (1:50 – 2:20)**

**Hace:** en el lector, mantén presionada la palabra ensayada (con ratón, doble
clic). La de siempre, *poverty*, está
en «Antes del primer capítulo»: se abre desde el **Índice**, no con «Empezar a
leer», que lleva al capítulo 2. En la ficha, el Índice queda unas 2 pantallas
por debajo de «Empezar a leer»: baja hasta él, o usa «Índice» arriba del lector. Si suena, es la **voz del navegador** («Sin
grabación para esta palabra»). **Sigue hablando mientras llega la explicación**,
que tarda unos segundos (unos 15 según la API, sin medir con cuenta). Luego mantén
presionada la palabra que el diccionario no trae; si el tiempo aprieta, sáltala.

**Dice:** «Mantengo el dedo sobre una palabra. El diccionario y la pronunciación salen al
instante; la explicación de qué significa en esta frase llega unos segundos
después, porque esa parte la hace la IA. Y cuando el diccionario no la trae o no
está claro qué acepción es, la aplicación lo dice: esto lo ha escrito una IA, o
*puede ser* esto o esto.»

**5. Pronunciar y corregir (2:20 – 2:50)**

**Hace:** *Pronunciar*, llegando **desde el lector**: el botón «Una frase de mi
libro» solo existe si hay un libro empezado. Púlsalo, o escribe una frase corta a
mano, que también vale. Graba
leyendo con una palabra mal dicha a propósito. Pulsa «Corrígeme». En «Practica
esta palabra» la boca ya está abierta: pulsa «Escuchar y ver»; si da tiempo,
«Despacio» o «Boca en 3D» (con + y − se acerca).

**Dice:** «Ahora la leo en voz alta, y una palabra la digo mal a propósito.
Me marca palabra por palabra lo que se entendió y el sonido que falla. Lo oigo
bien dicho y veo a la vez cómo se mueve la boca, también más despacio.»

**6. Que no suene robótico (2:50 – 3:20)**

**Hace:** escribe «Don't you want to come with us?», graba, corrige. Abre «Para
sonar más natural» y señala el «no pares aquí» y las reducciones. Pulsa
«Escúchalo natural».

**Dice:** «Cuando se lee palabra a palabra suena cortado. La aplicación mide
dónde me paré y me enseña cómo se dice de corrido: *don't you* suena
*doncha* y *want to* suena *wanna*. Y así suena natural.»

**7. Mis palabras y Mi espacio (3:20 – 3:40)**

**Hace:** *Mis palabras*. Enseña la lista con su frase y «Repasa cinco». Si da
tiempo, toca *Mi espacio*: el libro donde lo dejaste y *Mi progreso*. La
tarjeta de *poverty* dice «cap. 1» aunque la palabra es del prefacio: no lo leas
en voz alta.

**Dice:** «Todo lo que consulto y lo que pronuncio mal se queda aquí, con la
frase donde lo encontré, para repasar. Y es de mi cuenta: en el móvil y en la
computadora veo lo mismo.»

### V — Visualización · 3:40 – 3:55

**Dice:** «Detrás hay un modelo afinado que ordena los niveles del Marco Común
de forma creciente en textos que no vio al ajustarse. Para el lector significa
empezar el libro que le toca, entender lo que lee y seguir leyendo.»

### A — Acción · 3:55 – 4:05

**Dice:** «Está publicado y funciona en el móvil ahora mismo. Con gusto
respondo sus preguntas.»

**Hace:** vuelve a la cámara. Mirada a cámara un segundo antes de callar.

---

## Plan B

| Si pasa esto | Se hace esto | Se dice |
|---|---|---|
| **El Space está dormido** y el front enseña «Despertando…» | Seguir hablando del paso siguiente mientras despierta; si no responde en lo que dura una frase larga, abrir la **grabación previa** rotulada | «El servidor del motor se duerme si nadie lo usa; mientras despierta, les cuento lo que va a salir.» |
| **El micrófono falla** en *Pronunciar* | Probar una vez más con los auriculares; si falla, pasar a la **grabación previa** de los pasos 5 y 6 | «El micrófono no me responde; se lo enseño en una grabación previa del mismo recorrido.» |
| **La IA no responde** o se acabó el cupo | Seguir: el diccionario, la fonética, el buscador y la ficha no dependen de ella | «La parte de IA no está respondiendo, y precisamente por eso la aplicación no se cae: el diccionario y la lectura siguen funcionando.» |
| **La boca 3D no carga** | Pulsar «Recargar y reintentar» una vez; si no, quedarse con el corte 2D | «La 3D tarda en cargar; el corte de perfil enseña lo mismo.» |
| **Una búsqueda devuelve algo raro** | No discutirlo en directo: abrir el libro ya preparado desde la estantería | — |

---

## Preguntas probables del profesor

Respuestas de dos frases, con las cifras del documento. Si la pregunta va más
allá, **remitir al apartado del documento** en vez de improvisar números.

**¿Qué tan bien funciona el modelo?**
**Dice:** «En la validación interna, 144 documentos reservados del corpus con
el que se entrenó, tiene una correlación de Spearman de 0,908 con el
nivel de referencia, y el 97,2 % de los textos queda dentro de un nivel del
correcto. Lo que sostiene el trabajo es que, en textos externos de British
Council, ordena los niveles de A1 a C1 de forma estrictamente creciente, aunque
el escalón entre A1 y A2 está dentro del ruido.»

**¿No mide simplemente lo largo que es el texto?**
**Dice:** «En British Council, contar palabras ya da 0,807 y el modelo llega a
0,860, así que la longitud explica mucho. Descontándola, el modelo conserva una
correlación parcial de 0,668: hay señal que no es longitud.»

**¿Por qué Angular y no Gradio?**
**Dice:** «Usted lo pidió en la revisión del avance: un front propio, separado del
motor, y después, en Vercel. Gradio sigue como motor y respaldo, y el front es una
aplicación estática, gratuita y siempre despierta, pensada para el móvil; se
publica sola cada vez que subo un cambio.»

**¿Por qué Pléyade, si el proyecto es LiteraLevel?**
**Dice:** «LiteraLevel es el proyecto y el modelo; Pléyade es el nombre de la
aplicación, el que ve el lector. Una pléyade es un grupo de escritores célebres de
una época, y también un cúmulo de estrellas: junta la literatura y el cielo.»

**¿Hay más de un modelo?**
**Dice:** «Dos. El que mide la dificultad, un distilroberta afinado, y uno pequeño
que mueve la boca 3D, aprendido de vídeos de caras reales: con hablantes que no
vio sigue el movimiento real con una correlación de 0,56, frente a 0,44 de las
reglas que había antes. Está en el apartado 7.8 del documento.»

**¿Qué límites tiene respecto al Marco Común Europeo?**
**Dice:** «Pléyade no certifica ningún nivel: la letra es solo el ancla más
cercana en una escala propia de 0 a 2. Además la escala del modelo sale
comprimida, por eso la interfaz enseña bandas y no decimales.»

**¿Cuánto cuesta mantenerlo?**
**Dice:** «Medir, leer, buscar y consultar el diccionario no cuestan nada. Solo
explicar una palabra, resumir un libro y corregir la pronunciación salen a un
servicio de pago, con un cupo por perfil, y el servidor del motor cuesta 7
dólares al mes.»

**¿De dónde salen los datos y qué licencias tienen?**
**Dice:** «De corpus académicos publicados y de repositorios de dominio público,
sin Kaggle: Gutenberg es dominio público, el diccionario sale de Wiktionary y los
15.367 textos del catálogo externo tienen licencia libre. El único corpus con
derechos, el de British Council, no se redistribuye: se reconstruye con su
manifiesto.»

**¿Qué haría con más tiempo?**
**Dice:** «Terminar la cara que lee de frente, que está en desarrollo, repetir la
prueba de usuario con cinco lectores sobre el front nuevo y
medir cuántos libros empezados se terminan, que es la métrica que valida la
idea. Y calibrar la escala y ampliar el corpus de anclaje del Marco Común, que hoy
tiene 654 documentos.»

**¿Y si la IA se equivoca?**
**Dice:** «La IA nunca redefine una palabra que trae el diccionario: la explica
en su frase, y lo que escribe ella va marcado. Cuando la elección de acepción es
dudosa, la aplicación lo dice en vez de afirmar una.»

---

## Después de la demo

- Dejar de compartir pantalla solo cuando el profesor dé paso a preguntas.
- Si algo falló, decirlo en una frase y **no** volver a intentarlo durante las
  preguntas.
