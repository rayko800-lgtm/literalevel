# Ronda 1 de revisión y auditoría — informe consolidado

Para Miguel. Noche del 14 al 15 de septiembre de 2026. Escrito por la central
con los cuatro informes de auditoría cruzada, el diagnóstico del caso Esmeralda
y la prueba como persona del front publicado. Cada hallazgo lleva su dueño.

## En una frase

La app funciona y lo que ve un usuario está bien, pero la auditoría encontró
**10 fallos serios**: 6 en el código y 4 en los documentos. Ninguno rompe la app.
Los del código afectan a la búsqueda de cuentos, a la velocidad cuando hay
varios usuarios a la vez y a la lectura natural. Los de los documentos afectan a
la credibilidad ante el profesor, porque algunas afirmaciones dicen más de lo que
se midió. Todos están asignados, y los dos de búsqueda del caso Esmeralda ya
están arreglados y en producción.

## Cómo se hizo

1. **Poner todo al día.** Cada sesión actualizó lo suyo: despliegue, pendientes,
   contratos entre módulos, README, skills y los cinco entregables.
2. **Auditoría cruzada a ciegas.** Nadie auditó su propio trabajo, y nadie leyó
   los otros informes antes de escribir el suyo.

| Área | Dueño | Auditó | Informe | Serios | Menores | Dudas |
|---|---|---|---|---|---|---|
| API y front | e6 | 4e | `cruzada_2026-09-14_api_front.md` | 2 | 8 | 1 |
| Voz, léxico, animación | 4e | e6 | `cruzada_2026-09-14_voz_lexico.md` | 2 | 6 | 1 |
| Catálogo y despliegue | f4 | e6 | `cruzada_2026-09-14_catalogo_despliegue.md` | 2 | 4 | 1 |
| Documentos | b9 y f4 | 4e | `cruzada_2026-09-14_documentos.md` | 4 | 11 | 2 |
| **Total** | | | | **10** | **29** | **5** |

Además: `diagnostico_encontrar_amor_b1_2026-09-14.md` (e6) y la prueba como
persona del front `45d9999` (f4).

## Los 10 serios, en palabras

### Código

1. **La corrección de voz y la subida de libros congelan el servidor** mientras
   trabajan. Con dos usuarios a la vez, uno espera al otro (medido: 3,4 s de
   espera en una petición que debería ser instantánea). Arregla **f4**.
2. **La vista previa gratuita del diccionario espera a la explicación de pago de
   otro usuario**, por un candado que abarca la llamada a OpenAI. Arregla **f4**.
3. **La lectura natural puede inventar «gonna»** cuando «going to» va seguido de
   un nombre: «I am going to school» se convertía en «I am gonna school» y así
   se leía en «Escúchalo natural». Arregla **4e**.
4. **Si una palabra se repite y se falla de dos maneras**, el segundo fallo pisa
   al primero y el sonido señalado es el equivocado. Arregla **4e**.
5. **Los 15.357 cuentos libres solo se buscan por título y autor.** Su gancho y
   su texto están vacíos en el índice de búsqueda. Es la causa de fondo de lo que
   vio Esmeralda: «amor» devolvía «MY FUTURE». Arregla **f4** recalculando ese
   índice en la CPU de esta máquina, sin gasto.
6. **La medición descarta 16 cuentos** (el final de cada grupo de bloques) y los
   cuenta como rechazados por el filtro. Arregla **f4**.

### Documentos

7. **El 0,908 se presenta como «validación ciega»** en la portada, el resumen y
   el guion de la demo, pero el propio documento (§7.4) reconoce que ese
   conjunto no es virgen. Es lo más delicado ante el profesor. Arregla **4e**.
8. **El coste de cómputo del catálogo está mal**: dice unas 3 horas de A100 dentro
   de 10 USD, cuando lo medido son 17 horas, y la medición real se hizo gratis.
   Arregla **4e**.
9. **El inventario de fuentes está incompleto**: faltan el corpus que entrenó el
   v4 (ELG CEFR), las cuatro fuentes de cuentos libres, common-pile y CMUdict, y
   una fila dice «sin descarga de texto» cuando se descargaron 16.000. La rúbrica
   exige describir fuente, calidad y relevancia. Arregla **4e**.
10. **Hay fuentes citadas sin referencia APA** (Imperial 2025, Grossman y Chen,
    Lexile, ELG…). La rúbrica exige referencias en APA. Arregla **4e**.

## Lo que ya está arreglado y en producción

- **Buscador del caso Esmeralda** (reinicio 16, Space `484b83b`): el nivel ya no
  pesa más que el tema, un título acertado sale siempre primero, y 163 textos
  que no son lectura en inglés quedan fuera.
- **Frase de la demo**: «Don't you want to come with us?» no produce el enlace
  «with us»; se quitó la promesa del guion y la presentación.
- **Cifras de libros de amor**: mi primera medida estaba mal. Con la regla de la
  app escrita en el documento quedan 1 en B1 y 31 en B2 (29 títulos distintos).

## Lo que está en marcha

| Quién | Qué |
|---|---|
| f4 | Serios 1, 2, 5 y 6; menores de API y catálogo; reinicios 17 y 18 |
| 4e | Serios 3, 4, 7, 8, 9 y 10; menores de voz y de documentos |
| e6 | Pantalla nueva de Encontrar (aprobada) y cuatro detalles del front: la barra del 3D tapa la lengua, sombras suaves inactivas, dos «1 minutos», leyenda de enlaces sin enlaces |
| b9 | Parada sin cupo de Fable; su trabajo está repartido |

## Lo que se comprobó y está bien

- Aislamiento entre lectores, cobro atómico y rutas de archivo sin recorridos.
- Degradación sin clave de OpenAI en voz y léxico.
- Fonema determinista, pronunciación por forma con su marca de IA, animación con
  duración.
- Recuento del catálogo (16.251 cargados, 15.357 dentro, 894 fuera), licencias
  por fuente y guardas de los desplegadores.
- Las 25 entradas de la bibliografía están citadas; las cifras de los CSV, el
  diccionario y los modelos 3D cuadran.
- Las 18 suites de pruebas pasan.

## Estado de cierre (15 sep, 01:00)

| Serio | Qué | Commit | En producción |
|---|---|---|---|
| 1 | Voz y subidas congelaban el servidor | 31325a4 (f4) | Sí, Space f237e61 |
| 2 | Vista previa del diccionario esperaba a otro lector | 31325a4 (f4) | Sí, Space f237e61 |
| 3 | «gonna» inventado en la lectura natural | 2661452 (4e) | Pendiente de reinicio |
| 4 | Palabra repetida pisaba el fonema | 2661452 (4e) | Pendiente de reinicio |
| 5 | Cuentos libres buscables solo por título y autor | 6945046 (f4) | Reinicio 18 en curso |
| 6 | 16 colas de grupo descartadas sin medir | 6945046 (f4) | Reinicio 18 en curso |
| 7 | 0,908 presentado como «validación ciega» | 72c9ee6 (4e) | Documentos |
| 8 | Coste de cómputo mal contado | 72c9ee6 (4e) | Documentos |
| 9 | Inventario de fuentes incompleto | 72c9ee6 (4e) | Documentos |
| 10 | Citas sin referencia APA | 72c9ee6 (4e) | Documentos |

Menores cerrados: los 6 de voz y la duda de «set off» (d58b0be, 4e), los 11 de documentos y la cifra de libros de amor (b0dac54, 4e), los 4 del front de la prueba como persona y el rango de tiempo (e6, front publicado 6cfda19), y los tiempos «1 minuto» en motor y front (cb799bc, f712d73). En curso: menores de API (f4).

**Ronda 2 ya empezada.** Catálogo (4e, `ronda2_2026-09-15_catalogo.md`): serios 5 y 6 **verificados como cerrados** (15.366 de 15.367 con gancho, huella del índice comprobada recodificando 40 filas, 10 colas medidas, 4 dificultades que bajan de C1 a B2). Nuevo serio: el rescate por nombre rompe búsquedas temáticas en español («sobre» ≈ «Sombre», «historias» ≈ «Historians», «luna» ≈ «Luna: The Lost Dog»); va con el arreglo del reinicio 19. Nuevo menor: 6 ganchos con anuncios y URL. API (e6, `ronda2_2026-09-15_api.md`): serios 1 y 2 **verificados como cerrados** (/api/salud en 3-5 ms con una voz o una subida en curso, frente a 3 s con la regresión; en el Space, subidas de 19 MB sin bloquear). Nuevo: dos subidas simultáneas del mismo lector se pisan y pueden dejar inválido el archivo de nombres; el 422 de entrar devuelve la contraseña en la respuesta (verificado en el Space); la prueba de concurrencia no espera a que la petición lenta empiece. Los tres van al reinicio 19 (f4). Front (4e, `ronda2_2026-09-15_front.md`): los seis cambios verificados en el Space a 390 px (bloques de Encontrar, 25 tarjetas irrelevantes sin etiqueta, boca 3D sin tapar, consola limpia, «1 minuto»). Nuevo menor: un solo falso positivo por nombre («Fenn, Amor», «Jane G. Austin») vacía los bloques; se resuelve con el reinicio 19. Menor de accesibilidad en los botones de «Ver también» (e6). Dudas para f4: «Londres» no pesa en «detectives en Londres», y un poema de nivel 1 sale B2 por la cola unida a su bloque. Voz (e6, `ronda2_2026-09-15_voz.md`): serios 3 y 4 **verificados como cerrados** con las mismas frases de la ronda 1 («I am going to school» ya no se reduce; «want to come» y «going to see» sí; cat→cut/cap da los dos sonidos). Quedan a medias dos menores (silencio guardado como frase difícil; una palabra inglesa aceptada como IPA) y uno nuevo («Mr.» corta un enlace); van al reinicio 20 (4e). Documentos (e6, `ronda2_2026-09-15_documentos.md`): 13 de 17 hallazgos verificados como cerrados, con cada cifra recontada y las referencias comprobadas en su fuente. **Serio a medias:** el coste de cómputo pasó de «3 h de A100 en 10 USD» a «0 USD en T4 gratuita», pero PENDIENTES.md registra tandas en A100 de pago (2,8 h) y solo la última consta en T4; hay que escribir lo que pasó de verdad. Menores: una fila que aún dice «Validación ciega», las horas referidas a otro total de libros, el inventario sin fecha, y el guion que describe la casilla vieja de Encontrar. Van a la pasada de documentos de 4e tras el reinicio 19. Boca 3D, auditada por primera vez (4e, `ronda2_2026-09-15_boca3d.md`). **Serio nuevo:** fuga de memoria al cerrar el visor, medida en el front publicado: diez aperturas y cierres dejan 48,7 MB y diez escenas vivas con sus contextos gráficos; en un móvil acabaría cerrando la pestaña. Menores: el audio sigue sonando tras cerrar, controles sin teclado, y los modelos regenerados no son idénticos byte a byte. Correcto: licencia CC0 de la cara reproducible desde la versión oficial, nada de terceros sin licencia, carga diferida y respaldo 2D. Lo arregla e6 (b9 sin cupo). En curso: reinicio 19 (f4).

Nuevo, destapado al arreglar el 5: «amor» coincidía con un autor («Fenn, Amor») y títulos parecidos, y el modelo multilingüe apenas relaciona «amor» con «love». Decisión de la central: el nombre solo impulsa con coincidencia completa y no fija la ventana de relevancia si el tema no se parece; las búsquedas de una palabra en español se traducen con el diccionario local; fuera las filas con título «nan». Va al reinicio 19 (f4).

## Qué sigue

Cuando las tres sesiones cierren sus correcciones: reinicio y publicación,
prueba como persona sobre lo corregido, y **ronda 2** de auditoría cruzada solo
sobre lo que cambió, con los auditores rotados.

## Estado de la ronda 2 (15 sep, 02:30)

| Qué | Commit | En producción |
|---|---|---|
| Rescate por nombre, frases en español, anuncios fuera, subidas simultáneas, 422 sin contraseña | 7d94bd9, c63ce44, a557288 (f4), subidos desde el árbol de bffc69d | Sí, reinicio 19, Space 053a486, comprobado sin fallos |
| Fuga de memoria del 3D: renderer compartido, 18,1 MB y 1 contexto vivo tras 20 aperturas (antes 48,7 MB con 10) | d911cc2, b3ed0d7 (e6) | Sí, front 548ff40 |
| Audio tras cerrar, teclado y aria-pressed, pérdida de contexto al 2D, README | bffc69d (e6), 2bbf9ec, 6fa33c0, 5cec3ae (e6) | Sí, front 548ff40 |
| Restos de voz: silencio no se guarda, IPA en ASCII rechazada, «Mr.» no corta la frase | 2c0e681 (4e, 7 mutantes muertos) | Sí, reinicio 20, Space af72fb0, comprobado sin fallos |
| Carpetas temporales de las suites, causa del disco lleno | 42de4cb (4e); 40cdcd4 (f4) | No aplica, 0 carpetas tras cada suite |

Comprobación del reinicio 19 (f4): 0 fallos. «amor» con B1 da 12 de 12 sobre amor; «Jane Austen» sin Jane G. Austin; ningún anuncio ni texto que no es lectura en 14 búsquedas; el error de entrar ya no devuelve la contraseña; dos subidas simultáneas conservan sus nombres. En curso: prueba como persona de «amor» y «Jane Austen» con B1 sobre el Space nuevo (e6), pasada de documentos con el coste real de cómputo (4e). Después: reinicio 20, publicación del front con el 3D sin fuga y ronda 3 sobre lo corregido.

Prueba como persona sobre el Space nuevo (e6, 1b42172, 390 px táctil, perfil B1):
- «amor»: todo es de amor y ya no salen «Fenn, Amor» ni «MY FUTURE». Los 24 resultados son C1–C2: es el hueco de composición del catálogo.
- «historias de la luna» y «libros sobre detectives»: ningún falso positivo por nombre.
- **Serio nuevo, front (e6):** el margen fijo de «Menos parecidos» esconde lo que es del nivel de la lectora. En «historias de la luna», cinco cuentos A2–B1 quedan detrás de 14 libros C1–C2, y la pantalla promete «Primero lo de tu nivel». Decisión de la central: un margen más ancho solo para la franja del lector, dentro de la ventana de relevancia de la API, sin bloque nuevo.
- **Menor nuevo, API (f4, reinicio 20):** con «Jane Austen», sus novelas quedan por debajo de los libros sobre ella, y se cuelan Sidney Austen y Calamity Jane.
- Menor abierto: los .glb sin comprimir.
- **«detectives en Londres» (f4):** no es un fallo de búsqueda. «Londres» sí pesa: 5 de 12 resultados son de Londres. Pero de los 89 libros de detectives con Londres, 2 son B1 y 87 son C1–C2. Es otro hueco del catálogo y no se toca el código.
- **SWV991 (f4):** el poema de nivel 1 no sale B2 por la cola. Sale así porque su bloque incluye APOCALYPTO, la sinopsis de una película con contenido adulto: sin ella el bloque mide 0,273 y con ella 1,291. Es un patrón: en una muestra de 30 bloques, quitar un solo texto mueve la medida más de 0,5 en 3 de ellos.
  - Decisión de la central: medir cada bloque sin cada uno de sus textos. Si uno solo mueve la medida más del margen, fijado antes de ver resultados, los demás se quedan con la medida sin él.
  - El raro conserva la medida del bloque completo y queda marcado. Si no es lectura, sale del catálogo.
  - Cuesta unos 13 minutos de CPU y no cambia el índice de búsqueda.
  - Va al reinicio 21, junto con lo de «Jane Austen».
- Disco: se borraron 1.567 carpetas de pruebas de más de 3 horas en C:. Siguen apareciendo cuando se mata una suite antes de acabar.

Pasada de documentos (4e, 13ad84a, PDF recompilados):
- **Coste de cómputo, lo que consta:** A100 de pago en Colab Pro hasta el 10 sep, con 27.776 libros medidos. Desde entonces, T4 gratuita y textos libres en la CPU local.
- No se da cifra en dólares porque no quedaron registradas las unidades gastadas. Las «2,8 h» eran una estimación, no horas gastadas.
- Cerrados los menores de la ronda 2: la fila del Cuadro 10 ya dice «Validación interna», 14,5 h para los 53.179 libros, Cuadro 2 con fecha, la casilla vieja de Encontrar fuera de los guiones, cabecera del README y cita de _cefr.
- Cifras sincronizadas: 15.367 textos libres, 68.546 en total y tablas de suites al día. El reinicio 21 cambiará el reparto por nivel de los libres, y habrá que recontarlo.
- Carpetas huérfanas de pruebas: cb17bca borra al empezar las de más de 3 horas.

Ronda 3 empezada: 4e audita la búsqueda del reinicio 19 y la boca 3D publicada.

Reinicio 20 (f4): Space af72fb0, con voz.py y lexicon.py del árbol de fdbc54e, comprobado sin fallos. Las 12 suites pasan en árbol limpio. «Mr. Adams wants to come with us.» ya no da avisos, y «amor» con B1 sigue dando 12 de 12.

Reinicio 21 en preparación (f4):
- **Bloques con un texto raro:** margen de 0,5 fijado antes de medir. El texto raro se marca en la columna raro_en_bloque, y APOCALYPTO pasa a no_lectura.
- **«Jane Austen»:** nombre de pila y apellido juntos cuentan como coincidencia completa. Sus obras ya salen primero, sin Sidney Austen ni Calamity Jane.
- Las pruebas cazaron antes de subir que un nombre de pila solo volvía a traer «Fenn, Amor» con «amor». Ahora se exige el apellido, y una prueba lo vigila.

Arreglo del serio de Encontrar (e6): commit ec5bb75, publicado como front 73a34dd.
- **Regla:** lo que cae en la franja de la lectora tiene un margen de 0,10.
- **Dos guardas:** parecido mínimo de 0,65, y no se cruza un hueco de más de 0,05.
- Sin la primera guarda subía un cuento de terroristas en «Terror gótico». Sin la segunda subía «Calamity Jane».
- Con B1, «historias de la luna» trae cuatro cuentos a «En tu nivel» y uno a «Un poco por encima».
- En «amor», «detectives» y «Jane Austen» no sube nada fuera de tema.

Ronda 3, informes recibidos:
- **API (e6, e1cc109):**
  - Cerrados y verificados en el Space: el error de entrar sin la contraseña, las dos subidas simultáneas y la prueba de concurrencia.
  - Siguen abiertos: el uso de CPU durante una subida grande y el grupo de hilos compartido.
  - Tres menores nuevos: borrar un libro subido queda fuera del candado; el candado se retiene mientras se abre el libro; un error al escribir el archivo de nombres se ignora sin avisar.
- **Documentos (e6, 1092a46):**
  - Cerrados: el serio del coste, los cinco menores de la ronda 2 y la duda de _cefr.
  - Cifras recontadas: 15.367, 68.546, 11.881 y 14,5 h.
  - Menor nuevo: las 1,9 unidades son del 9 de septiembre, no del 10.
- **«detectives en Londres» con B1 (f4, medido):** desde el reinicio 19 ya no trae los cuentos de detectives de StoryWeaver en «En tu nivel». Es correcto.
  - Antes subían a 0,75–0,79 porque «detectives» se parecía por la forma de la palabra a sus títulos, no porque trataran de Londres.
  - Ahora quedan en 0,41–0,49 por tema, y el mejor resultado es «Scotland Yard», C2, con 0,75.
  - No se toca antes de la demo. Ofrecer detectives de B1 sin Londres queda como idea para después de la entrega.
- Los tres menores de subidas van al reinicio 22, con pruebas propias (f4).

Ronda 3 de la boca 3D (4e, 444228a), sobre el front publicado 73a34dd:
- **Cerrado y verificado:**
  - La fuga de memoria: tras 20 aperturas quedan 1 contexto gráfico vivo y 13,8 MB, frente a 48,7 MB con 10 antes del arreglo.
  - Al cerrar el visor, el audio ya no suena, a 1x ni a 0,5x.
  - Las flechas del teclado y la etiqueta de «reposo» para lectores de pantalla.
  - Si el navegador pierde el 3D, se pasa al 2D.
  - El README.
- **Menores nuevos, para e6 después del ensayo:**
  - Cada apertura vuelve a bajar cara.glb y lengua.glb, unos 2,7 MB, porque la URL firmada cambia. En un móvil con datos, eso cuenta.
  - El arreglo de la fuga depende de _interceptControlDown, una parte interna de three que la prueba solo simula.

Ronda 3 de búsqueda (4e, 036a207), sobre el Space del reinicio 19 y 20:
- **Cerrado:** el serio de la ronda 2. «sobre», «historias» y «luna» ya no se confunden con títulos parecidos.
- **Serio nuevo:** el endurecimiento del nombre apagó el rescate de autores clásicos. «cervantes» saca libros de animales, «dante» de odontología y «moliere» de insectos, porque su parecido semántico no llega al margen.
  - Decisión de la central: el apellido exacto de un autor rescata sin margen semántico, y el parecido por letras lo sigue necesitando.
  - Va al reinicio 22 (f4), con pruebas para autores clásicos y para palabras españolas que también son apellido.
- **Menores:**
  - Con nombre y apellido gana cualquiera del mismo apellido: puede cerrarlo el 21.
  - Nueve anuncios largos siguen visibles: van al 21.
  - 89 libros de Gutenberg sin título quedan invisibles, y son libros reales: van al 22.
- **Duda:** «luna» sola trae títulos con Luna.
- **Ronda 3 del front:** pasa de f4 a 4e.

Ronda 3 del front (4e, 7ecc2b1), sobre el margen de Encontrar:
- **Cerrado y verificado a 390 px:** con B1, «historias de la luna» sube los cinco cuentos, cuando antes no subía ninguno. «amor», «detectives», «Terror gótico» y «Jane Austen» no cambian, y las 60 tarjetas de «Menos parecidos» van sin etiqueta. Los bordes de las guardas cortan exactos.
- **Menor:** las pruebas no fijan el parecido mínimo ni el margen. Van casos de borde (e6).
- **Menor nuevo:** el chip de sugerencia «Detectives en Londres» deja a una lectora B1 sin nada de su nivel. Se cambia por uno que dé resultados en todos los niveles, y se revisan los demás chips (e6).

Anuncios del reinicio 21 (f4): 8 de 9 salen del catálogo. «The Ant and the Dove» se queda porque es un cuento de verdad. «emily bronte» queda resuelto con el 21; «agatha christie» sigue sin rescate y va con cervantes al 22.

4e audita el código del reinicio 21 (7c9c289) antes de que suba.

Datos del reinicio 21 (f4): código 7c9c289, datos 740eb84.
- **Bloques con un texto raro:** 92, con 225 textos que cambian de letra. Bajan 181; suben 44 cuando el raro era el fácil de su bloque.
- **Reparto de los libres:** A1 766, A2 5.696, B1 5.491, B2 2.524, C1 777 y C2 113. Antes eran 749, 5.589, 5.543, 2.583, 790 y 113.
- **Revisión a mano de los 92 raros:** 7 salen del catálogo. Son APOCALYPTO, cinco textos en francés o italiano y uno que dice que no se puede reproducir.
- **Anuncios:** salen 8.
- **Fuera de la búsqueda:** los textos que no son lectura pasan de 185 a 200.
- pruebas_corpus da 41 de 41. Falta el árbol limpio, los mutantes y la batería de búsqueda antes de subir.

Ensayo de la demo sin cuenta (e6, faee509), front 73a34dd y API af72fb0, a 390 px y 1280:
- **Duración estimada:** entre 3:40 y 4:10. El paso 4 no cabe en 30 s con la explicación de la IA.
- **Tarda más de 3 s:** la primera palabra consultada de la sesión (3,8 s; después, 0,8 s) y la primera boca 3D en el móvil (4,4 s).
- **Diez arreglos de guion (4e, tras el 21):**
  - la receta del perfil 1,20 y la consulta del paso 2, que no enseña cuentos libres;
  - entrar a poverty por el Índice y los nombres reales de los botones de «Afinar»;
  - los 40 ms, que son del servidor, y la voz del navegador;
  - el hash del front citado y abrir la boca 3D antes de grabar.
- **Fallo:** la tarjeta de «Mis palabras» dice «cap. 1» para una palabra del prefacio (e6).
- **Lo que tiene que ensayar Miguel con su cuenta y micrófono:**
  - la explicación de la IA con poverty y la marca de IA;
  - «Corrígeme» con una palabra mal dicha;
  - «Don't you want to come with us?» con la lectura natural;
  - que la palabra aparezca en «Mis palabras»;
  - la demo entera cronometrada.

Reinicio 21 subido (f4): Space 384a206, --commit ef1138c.
- **Qué entra:** 7c9c289, los datos de 740eb84 y ef1138c. Este último hace que el nombre entero del autor solo cuente con dos palabras o más, porque sin él «rosa» traía libros de un colaborador apellidado «de la Rosa». La batería lo cazó antes de subir.
- **Comprobado:** «Jane Austen» abre con su obra, «rosa» trae los títulos con Rosa, «amor» con B1 da 12 de 12, SWV991 pasa a A2 y APOCALYPTO no sale.
- **Queda:** con B1 y el ajuste de nivel, «Jane Austen» abre con la adaptación de MacKaye.

**Serio en producción (4e, 54d6591), fallo de coordinación de la central.**
- **El fallo:** la regla «un apellido suelto no puntúa si la consulta trae otro nombre» usa 24.296 palabras del campo de autor, como island, love, white o wild. Así apaga al autor cuando la consulta mezcla autor y título.
- **Casos medidos:** «treasure island stevenson» baja Treasure Island al 5.º puesto. Con «love poems by browning», «the secret garden frances hodgson burnett» y «white fang jack london», el autor desaparece de los 10 primeros.
- **Por qué subió:** 4e avisó a la central antes de la subida, pero el aviso no llegó a f4 a tiempo.
- **Arreglo:** va en el reinicio 22, primero y solo, junto con el anuncio de venta de GHB (SWV644124) que seguía visible.

**Menores de 4e para el reinicio 23:**
- **Bloques:** un bloque de 3 con dos raros marca mal el texto normal, y la marca de raro queda obsoleta al unir la cola.
- **Idioma:** 42 textos que no están en inglés siguen visibles.
- **Duda sobre la formación de bloques:** dos grupos que suben de A2 a B2.
- **Recuento corregido:** suben 42 y bajan 183.

Front b76ca59 (e6, 88b3a83):
- **Modelos 3D:** cara.glb y lengua.glb se bajan una vez por página (2 peticiones en 6 aperturas, antes 12), y la primera cara tarda 1,9 s, antes 4,3 s.
- **Chip:** «Detectives en Londres» pasa a «Detectives».
- **Pruebas:** casos de borde exactos, con 7 mutantes detectados.
- **Pendiente:** otros cuatro chips no dan nada de nivel A1–B1 y se cambian (e6).
- **«cap. 1» del prefacio:** viene de la API y va al 23 (f4).

Reinicio 22 en preparación (f4). Lleva solo el arreglo del serio del vocabulario de nombres y el anuncio SWV644124.
- **Idea:** una palabra del campo de autor cuenta como nombre solo si el diccionario la tiene únicamente como nombre propio, o no la tiene.
- **Visto bueno previo:** 4e lo da directamente a f4 antes de subir, con sus 5 consultas y la batería entera. f4 no sube sin ese «ok».
- **Reinicio 23:** los tres menores de subidas, que ya están probados con pruebas_api 58/58, los autores clásicos y el resto.
