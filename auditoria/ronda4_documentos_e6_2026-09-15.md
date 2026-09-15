# Ronda 4: auditoría a ciegas de los documentos contra la producción de hoy

- **Quién:** entrega-e6 (811c22), por encargo de la Central. No escribí estos documentos.
- **Solo lectura:** para esta ronda no abrí `auditoria/`, salvo para escribir este informe.
- **Alcance:**
  - `entrega/documento.md`, con `documento.tex` cotejado frase a frase en cada hallazgo;
  - `entrega/estrategia.md`;
  - `entrega/presentacion.tex`.

  Versión de los tres: la de HEAD (último cambio, `f829d60`).
- **Contra qué:** API del Space `0319290` (RUNNING) y front `72e9525`. Lo contrasté con el código de `front/src` y `app/api.py`, y con búsquedas hechas hoy contra `/api/buscar`, con `n = 24` como el front y un lector nuevo en cada una. Donde cito algo que se ve a 390 px, sale de los ensayos que hice hoy en el navegador sobre el mismo front; hoy no abrí ninguno.
- **Gravedad:** **serio** si contradice lo que hace hoy la aplicación o promete más de lo medido; **menor** si está fechado, incompleto o redactado de más; **duda** si no pude comprobarlo.

## Hallazgos

### S1 · serio · El recorrido de ejemplo con «dostoyevski» contradice la limitación 15 del propio documento

- **Dónde:**
  - `documento.md:1067` (`documento.tex:2518`): «Busca. Escribe *«dostoyevski»*, mal escrito, y el rescate por parecido ortográfico la lleva igualmente a quien busca»;
  - `presentacion.tex:367`: «\textbf{2. Busca}\\ escribe mal\\ «dostoyevski»», y en la tabla, «el nombre mal escrito llega igual».
- **Por qué falla:**
  - El recorrido es el de «una lectora cuyo perfil da 1,20» (`documento.md:1064`).
  - Con 1,20 y «dostoyevski», hoy la API marca **15 textos por franja**, lo mismo que dice la limitación 15 (`documento.md:1477`).
  - En *Encontrar* a 390 px, «En tu nivel» abre con 9 tarjetas, **7 de ellas cuentos libres sin relación** (*Tanaji Malusare*, *Books*…).
  - *Crime and Punishment* solo aparece tras «Ver también los de otros niveles», a 3.789 px.
  - El documento declara el límite en §9 y lo usa como ejemplo feliz en §8.2, y la presentación hace lo mismo.
  - El guion de la demo ya pasó a «Crimen y castigo de Dostoyevski» por eso. Hoy esa búsqueda da 0 marcas, el aviso de otros niveles, y el libro primero en «De otros niveles», a 679 px.
  - Además, «mal escrito» no está claro: «Dostoyevski» es una transliteración española corriente.
- **Arreglo:** en §8.2 (md y tex) y en la diapositiva, usar «Crimen y castigo de Dostoyevski» con lo que se ve hoy, o conservar «dostoyevski» pero decir lo que pasa con perfil y remitir a la limitación 15. Si se quiere enseñar el rescate ortográfico, que sea sin perfil, o con un ejemplo que de verdad esté mal escrito (el documento cita «chejov» y «Shakespear»).

### S2 · serio · El cuestionario que se describe no es el de la aplicación

- **Dónde:**
  - `documento.md:1054` (`documento.tex:2449`): «Seis preguntas sobre hábitos observables y tres fragmentos reales en escalera»;
  - `estrategia.md:109` (`documento.tex:619`): «Seis preguntas sobre hábitos observables —con qué frecuencia lee, si necesita diccionario, si ve series sin subtítulos, si ha terminado un libro entero—».
- **Por qué falla:** *Tu nivel* hace **seis pasos en total**: tres preguntas y tres fragmentos. En `front/src/app/pantallas/nivel.ts:17`, `PASOS = ['frecuencia', 'fragmento_facil', 'libro_completo', 'fragmento_medio', 'comprension', 'fragmento_dificil']`, y la pantalla dice «1 de 6».
  - Ya no se pregunta ni por el diccionario ni por las series.
  - La API sigue sirviendo seis preguntas, pero el front usa tres.
  - Quien lea «seis preguntas… y tres fragmentos» espera nueve pantallas y dos preguntas que no existen.
- **Arreglo:** «Seis pasos, uno por pantalla: tres preguntas sobre hábitos (con qué frecuencia lee, si ha terminado un libro entero, qué entiende al leer) y tres fragmentos reales en escalera». En la estrategia, quitar «si necesita diccionario» y «si ve series sin subtítulos».

### S3 · serio · El gesto para consultar una palabra ya no es «tocar» ni «doble toque»

- **Dónde:**
  - `documento.md:1057` (`documento.tex:2455`): «Doble toque sobre la palabra»;
  - `documento.md:1113` (`documento.tex:2563`): «Toca una palabra que no conoce».
- **Por qué falla:** la aplicación dice otra cosa.
  - En el móvil, el aviso del lector dice «Mantén presionada una palabra para ver qué significa; desliza para cambiar de página.».
  - Con ratón, «Haz doble clic en una palabra…» (`lector.html`).
  - La bienvenida dice «mantén presionada» o «haz doble clic en».
  - El código lee la selección (`lector.ts`, `selectionchange` y `mouseup`): un toque simple no consulta nada.
  - Los guiones ya se corrigieron a «mantén presionada»; el documento no.
- **Arreglo:** «Mantener presionada la palabra (con ratón, doble clic)», en el Cuadro 15 y en el paso 5.

### S4 · serio · Faltan la tercera prueba de usuario (Ismael) y lo que cambió por ella

- **Dónde:**
  - `documento.md:1461` (`documento.tex:3074`): «La prueba de usuario tiene n = 2. Esmeralda y Laura son dos lectoras.»;
  - `estrategia.md:276`: «Con n = 2 no se puede estimar nada».
  - «Ismael», «bienvenida», «mantén» y «WebView» no aparecen en ninguno de los tres documentos (0 coincidencias en md y en tex).
- **Por qué falla:** en producción hay cambios que salen de otra prueba de usuario y que ningún documento cuenta.
  - **Ayuda en tres tandas**, en el código de hoy:
    1. «Entrar» lleva a «Tu perfil» con el cursor en «Usuario», el botón de la cabecera dice «Ajustes» y la tarjeta «Mídeme» ya no promete la estimación (`sesion.ts`, `ajustes.ts`, `app.html`, `inicio.ts`);
    2. un solo aviso en el lector con «?», y la línea de ayuda de *Pronunciar* con «?» (`lector.html`, `pronunciar.html`, `nucleo/banderas.ts`);
    3. la bienvenida de tres pasos solo en Inicio, con «Saltar» y «Ver la bienvenida otra vez» (`compartido/bienvenida.ts`).
  - **Micrófono:**
    - antes, los avisos quedaban tapados por la barra fija; ahora hay una línea de estado dentro de la barra, con un mensaje para cada rechazo de `getUserMedia`;
    - en un WebView de Android sale, antes de pulsar, «Para grabar tu voz, abre LiteraLevel en Chrome: toca ⋮ y luego «Abrir en Chrome».» (`pronunciar.ts`).
  - El documento sigue diciendo n = 2 y describe los ciclos con la interfaz de Gradio.
- **Arreglo:** en la limitación 13 y en §3 de la estrategia, añadir el ciclo con Ismael (Android, enlace abierto desde WhatsApp): qué dijo, qué se diagnosticó —un fallo real del micrófono y una aplicación saturada— y las tres tandas de ayuda. Contarlo con lo que hay en el código, no con informes. Y actualizar n, dejando claro que siguen siendo pruebas cualitativas.

### M1 · menor · Arranque: la cifra es del Space de Gradio sin buscador precargado

- **Dónde:** `documento.md:1451` (`documento.tex:3065`): «31 s hasta que el runtime dice `RUNNING` y 32 s hasta que la página responde».
- **Por qué falla:** la cifra no está fechada y no dice lo que hoy importa, que es cuándo el buscador está listo.
  - `/api/salud` expone `buscador_listo`.
  - En la tabla de despliegues (`DESPLIEGUE.md`, fila `0319290`): «RUNNING en 46 s; `buscador_listo` a los 14 s».
  - Las filas anteriores dan 20 s (`74f1484`), 29,2 s (`1708cb1`) y 55 s (`62e5a06`) después de RUNNING.
  - Los 31–32 s se quedan cortos como cota inferior, porque hoy se tarda 46 s en RUNNING con la imagen construida, más el tiempo del buscador.
  - El texto del tex, «tarda unos 30 segundos en despertar», coincide con el aviso del front, pero no con el buscador.
- **Arreglo:** fechar la medida y añadir: «desde el reinicio 26 el buscador se precarga al arrancar; en el despliegue del 15 de septiembre (`0319290`), RUNNING en 46 s y `buscador_listo` a los 14 s; en otros arranques, entre 14 y 55 s».

### M2 · menor · «40 milisegundos» es el trabajo del servidor, no lo que ve el lector

- **Dónde:**
  - `documento.md:1115` (`documento.tex:928`, `estrategia.md:368`): «son **40 milisegundos** *en caliente*»;
  - `estrategia.md:368`: «todo el trabajo local … son **40 milisegundos**».
- **Por qué falla:** medido hoy en el front publicado a 390 px, *poverty* tarda 5,0 s en frío (la primera de la sesión) y 0,64–0,73 s en caliente, desde que se selecciona hasta que la hoja se pinta. La cifra del servidor puede ser cierta, pero «aparece al instante» se lee como tiempo de pantalla.
- **Arreglo:** «40 ms de trabajo en el servidor; en el móvil, la hoja tarda unos 0,7 s en caliente y unos 5 s la primera vez de la sesión».

### M3 · menor · La corrección sin coste cuando no se oye voz no está contada

- **Dónde:** ninguno de los tres documentos menciona «No te oí» ni la devolución del uso (0 coincidencias).
- **Por qué:** la API devuelve el uso cuando la grabación no tiene voz (`app/api.py:1945`, `cuentas.devolver_por_silencio`) y lo dice con `uso_devuelto` (`api.py:1994`). El front añade «Este intento no cuenta.». Es un control de coste real sobre un servicio de pago, y la limitación 14 y el cupo por perfil no lo recogen.
- **Arreglo:** una frase en la limitación 14 o en §4.6: con cuenta, una grabación en silencio se descarta con «No te oí…» y no gasta uso; tope de 10 devoluciones por cuenta y día.

### M4 · menor · Cifras fechadas que el lector tomará por actuales

- **Recuento de pruebas:** `documento.md:1299` (`documento.tex:975`, `estrategia.md:414`): «Recuento sin claves del 15 de septiembre sobre `d58b0be`: 52 de 52 pruebas API, 349 de 349 pruebas extremas, 34 de 34 de corpus». El despliegue de hoy dice api 66/66, extremas 351 y corpus 48/48 (`DESPLIEGUE.md`, fila `0319290`). Como está fechado no es falso, pero cualquiera que lo coteje hoy ve otras cifras.
- **Frase de la demo:** `documento.md:1307` (`documento.tex:1021`, `estrategia.md:447`): «La frase de la demostración, «Don't you want to come with us?», da en el Space a fecha de `7c09d90` las reducciones *doncha* y *wanna*… y ningún enlace». Esa comprobación es anterior a la pantalla actual de *Pronunciar*, donde «Para sonar más natural» va plegado y añade «de corrido aquí». Los guiones ya no la dan por verificada.
- **Arreglo:** actualizar el recuento, o decir «en el corte `d58b0be`». Y en la frase de la demo, añadir que se repite con cuenta antes de la demo, como hace el guion.

### M5 · menor · La presentación afirma algo de la búsqueda que no se sostiene con perfil

- **Dónde:** `presentacion.tex`, tabla del ejemplo: «Busca & búsqueda por significado; el nombre mal escrito llega igual».
- **Por qué:** es la misma escena que S1. Con perfil 1,20, «llega igual» solo es cierto después de pulsar «Ver también» y bajar cuatro pantallas.
- **Arreglo:** el que se elija en S1.

### D1 · duda · 114 textos libres de amor frente a 4 de Gutenberg en la franja B1

- **Dónde:** `documento.md:1464` y `estrategia.md:449`: «hay 114 textos libres con *love* o *romance* en el título, frente a 4 libros de Gutenberg».
- **Qué comprobé:** por API, con nivel 0,80, «amor» marca 12 por franja, igual que el documento; «Historias de amor» también marca 12. La franja B1 es [0,35, 1,25], también igual.
- **Qué no:** no recontasté el 114 frente a 4 sobre el CSV del catálogo, para no cargarlo con el banco de f4 en marcha.

## Comprobado y correcto

- **0,908 como validación interna:** siempre se presenta como interna y no como externa ni ciega.
  - `documento.md:41-44`, «En la validación interna —144 documentos reservados del corpus de anclaje, los mismos con los que se eligió el punto de control—».
  - `documento.md:728`, que advierte «Presentarlo como validación externa»; `documento.md:757`; `presentacion.tex:254`.
  - La única «a ciegas» del documento (`documento.md:1369`) se refiere a las auditorías, no a la validación.
- **«Determinista»:** solo se dice de la selección del fonema, y con su salvedad («esto no hace determinista al reconocimiento de voz», `estrategia.md:434-435`, `documento.tex:997-998`). Ningún documento dice que el buscador ordene de forma determinista, así que el límite del 30b («no ordena igual en cualquier máquina», `DESPLIEGUE.md`) no choca con nada escrito.
- **Límites de la búsqueda (limitación 15, `documento.md:1472-1495`, y `estrategia.md:451`),** medidos hoy sobre `0319290` con perfil por nivel directo:
  - con 1,20, «dostoyevski» marca 15, y «tolstoy», «cervantes» y «oscar wilde», 12 cada uno;
  - «Crimen y castigo de Dostoyevski» marca 0;
  - «rosa» con 0,40 y con 0,80 trae en el puesto 2 *The Water Supply of the El Paso…*;
  - «luna» con 0,80 trae *Luna, The Rajapalayam Puppy* en el puesto 5;
  - «dracul» sin perfil abre con *Dracula's Guest* y *Dracula*.

  Todo cuadra con lo escrito. El 30b no cambia ninguna de estas cifras.
- **El caso de la lectora B1 y el amor (`documento.md:1464`, `estrategia.md:449`):** se cuenta como un fallo de búsqueda, no de composición del catálogo («No faltaban en el catálogo; fallaba la búsqueda»). Coincide con el código: la franja (`franja` y `por_franja` en `/api/buscar`) añade textos del nivel del lector detrás de los más parecidos.
- **Tiempos de búsqueda:** «Segundos» (`documento.md:1055`) se queda corto por lo alto. Hoy, en caliente: 0,58–0,77 s por API, y 0,42–0,72 s en el front.
- **Ficha de *Crime and Punishment*:** «1,70 sobre 2» y la curva ya calculada coinciden con la ficha publicada («C1 · 1,70 de 2», «Medido entero»).
- **Paridad md/tex:** las frases de los hallazgos S1–S4, M1, M2 y M4 están igual en los dos archivos. `documento.tex` tiene alguna mención más (por ejemplo, un segundo «n = 2» en la línea 843), con el mismo contenido.
- **Arquitectura y funciones visibles en la presentación:**
  - front Angular estático, API FastAPI dentro del Space de Gradio y Gradio de respaldo;
  - cuatro secciones más *Mis palabras*;
  - barra del micrófono abajo;
  - 53.179 libros y 15.367 textos libres.

  Todo coincide con `app.routes.ts`, `app.html` y `/api/estado` («68.546 libros»).

## Pendiente de quien decida

- **S1–S4:** tocan el documento, su .tex, la estrategia y la presentación, y hay que recompilar los PDF. Los de la presentación y el tex van juntos.
- **D1:** necesita un recuento sobre el CSV del catálogo cuando no haya bancos en marcha.
