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

Documentos y guiones al día con el reinicio 21 (4e, a978155; PDF recompilados):
- **Catálogo:** reparto recontado sobre el CSV, 11.953 textos entre A1 y B1, la regla de bloques con un texto raro contada con su duda, y no_lectura en 200.
- **Cómputo:** la fecha de las unidades corregida y el origen de los 27.776.
- **Guiones:** los 10 arreglos del ensayo. El paso 2 usa ahora «cuentos de dragones», que con perfil 1,20 da 13 textos libres de 14 en «En tu nivel».
- **Antes de grabar:** una sección nueva con los 6 puntos que Miguel ensaya con cuenta y micrófono.

Chips nuevos de Encontrar (e6, 4e6276e, front ec957d0):
- **Medición:** 32 alternativas contra el reinicio 21. Quedan 8 chips que dan al menos 3 textos de su nivel con A2 y con B1: Detectives, El océano, Una historia de amistad, Cuentos cortos para empezar, Viajes al espacio, Dinosaurios, Cuentos de miedo para niños y Animales de la selva.
- **Cambios:** se cambiaron seis, porque «Aventuras en el mar» y «Fábulas con animales» tampoco llegaban. El ejemplo del buscador ya no cita un autor.
- **Comprobado a 390 px:** con A2 y con B1, ningún chip deja la pantalla sin nada de su nivel.

**Dato para decidir si se amplía el catálogo.** Con A2 y B1 no llegan a 3 textos estos temas: amor, familia, amigos, deportes, la escuela, piratas, fantasmas, monstruos, brujas, robots, planetas, Navidad y misterios. Es el mapa de huecos de composición que vio Esmeralda, ahora medido. La lista está en la skill buscador-encontrar.

Comprobación de los guiones corregidos (e6, feeb806; front ec957d0, Space 384a206):
- **Lo que coincide con la pantalla:** la receta del perfil 1,20, los botones de «Afinar» y poverty por el Índice.
- **Paso 2 con «cuentos de dragones»:** trae 13 cuentos libres de 14, y el primero se ve sin deslizar.
- **La boca 3D:** ahora tarda 2,1 s la primera vez.
- **Quedan retoques (4e):** el título y la entrada de la sección «Antes de…», dos notas viejas en guion_video.md y tres menciones a un front antiguo en el documento y la estrategia.
- **«cap. 1» del prefacio:** es coherente con el resto de la app, que numera el prefacio como 1. Mostrar el título del capítulo es una mejora para el 23, no un arreglo urgente.

Anexo de la ronda 3 del front (4e, 02cc538), sobre el front ec957d0:
- **Cerrado y verificado:** una sola bajada de cada .glb, la guarda de three con su comentario, los bordes exactos en milésimas y los 8 chips con las cifras del commit de e6 en la página, con perfiles A2 y B1.
- **Nota:** dos chips traen alguna tarjeta floja. «Child safety» sale con «Cuentos de miedo para niños» y «A visit to the zoo» con «Animales de la selva». Es el catálogo, no la regla.

Reinicio 22, antes del commit (f4):
- **Arreglo del nombre de pila, en local:** las 5 búsquedas de 4e que mezclan autor y título dan 8, 9, 8, 2 y 10 de 10 resultados del autor. En el Space del 21 daban 2, 0, 0, 0 y 4. «browning» abre con Browning.
- **Serio de datos:** al buscar «Buying GHB Online» salía primero un anuncio de venta de metanfetamina, SWV644179, de la misma cuenta que el de GHB. Van los dos a no_lectura, y f4 revisa todos los textos de las cuentas con anuncios.
- **Pendiente:** el banco de mutantes termina hacia las 03:42. Después vienen el commit, el visto bueno de 4e y e6, y la subida.

Retoques de guion del anexo de e6 (4e, 8856030; PDF recompilados):
- **Demo:** la sección se llama «Antes de la demo, con cuenta y micrófono». Dice por dónde se entra y remite al plan B.
- **Guion:** incluye el camino a poverty por el Índice y la cifra nueva de la boca 3D.
- **Vídeo:** notas de tiempos al día.
- **Documento y estrategia:** citan el front ec957d0, y se comprobó por SHA-256 que los modelos 3D servidos son los del repositorio.

**Corrección importante (e6, 4db6ea3; verificado por la central sobre el CSV).**
- **Lo que se dijo:** el hueco de A2–B1 era de composición del catálogo.
- **Lo que hay de verdad:** cuentos libres con el tema en el título y dificultad entre 0,20 y 1,00. Son 74 de amor, 47 de fantasmas, 29 de monstruos y 338 de amigos.
- **Lo que devuelve la búsqueda:** con nivel 0,40, «Historias de amor», «ghost stories» y «Monstruos» traen 24 de 24 libros de Gutenberg.
- **Por qué importa:** es la causa de fondo del caso Esmeralda, y ampliar el catálogo no lo arregla.
- **Fuentes libres:** en StoryWeaver hay pocos cuentos nuevos, de 0 a 23 por tema. En Let's Read y en lo comprobado de African Storybook no hay ninguno.
- **Arreglo:** recuperar también dentro de la franja del lector. Lo diseña f4 para el reinicio 23.
- **Front:** e6 estudia si su regla del salto deja «Robots» en «Menos parecidos».

Causa medida del hueco de búsqueda (f4, en local con el Catalogo que carga la app). Los cuentos están cargados y casi ninguno excluido. Pierden por dos causas:
- **Ventana de nivel:** se abre a 0,05 del techo global, y ese techo lo pone un Gutenberg con título exacto. El mejor cuento del tema queda de 0,07 a 0,24 por debajo, entre el puesto 12 y el 75.
- **Índice:** diluye a los libres. Su embedding lleva un gancho que los de Gutenberg no tienen, y puntuados solo por el título suben de 0,07 a 0,21.

Con un top-12 dentro de la franja del lector salen de 6 a 12 del tema en casi todas las consultas, con A2 y con B1. La excepción es «Monstruos» con B1, que da 2.

Decisión de la central para el reinicio 23:
- **Segundo top-k dentro de la franja:** umbral relativo al mejor de esa franja, con un suelo.
- **Parecido de los libres:** el máximo entre su fila del índice y su título.
- **Marca en la API:** los resultados que entran por la franja llevan una marca, y el front los respeta.
- **Constantes:** fijadas antes de medir y calibradas con temas que no están en la batería.
- **Visto bueno previo:** 4e aprueba catalogo.py y e6 el front.
- **Después de subir:** volver a medir los chips y reescribir la frase del documento.

La regla SALTO del front y «Robots» (e6, 94a1078; 70 búsquedas por 5 niveles contra 384a206):
- **Resultado:** ningún valor de SALTO arregla «Robots» sin meter resultados sin relación.
  - El hueco malo de «Familia» (0,058, con «Familiar Things» y «Midwifery») es menor que el bueno de «Robots» (0,075).
  - El de «rosa» (0,096, malo) es mayor que el de «Superhéroes» (0,082, bueno).
- **Decisión:** SALTO no se toca, y se vuelve a medir sobre el reinicio 23.
- **Marca de la API:** e6 propone `por_franja`, siempre true o false, para que sin el campo el front se comporte igual que hoy.
- **Pendiente entre f4 y e6:** una sola definición de la franja, ±0,25 o −0,45 a +0,45.
- **Riesgos a medir en el 23:** ACTION PART-1 como mejor de la franja con B1, la meseta «Familiar» en Familia C1 y «rosa» de A1 a B1. Hace falta un suelo absoluto.

Contrato del reinicio 23 entre f4 y e6, cerrado:
- **Franja:** una sola definición, −0,45 < dificultad − nivel ≤ 0,45. La API la devuelve como `franja: [lo, hi]`.
- **Marca:** `por_franja` va en todos los resultados. Los n generales no cambian, y detrás van hasta K textos de la franja.
- **Umbral de lo marcado:** tres condiciones: un suelo absoluto, cercanía al techo general y cercanía al mejor de la franja. Se calibra con dragones, océano y dinosaurios.
- **Pruebas fijas:** ACTION PART-1 con B1, Familia C1 y rosa.
- **Front hecho (e6, 5e4421c), sin publicar:** usa `franja` si viene y, si no, se comporta como hoy. Pruebas 77/77.
- **Visto bueno previo:** 4e lo audita antes de publicar, junto con el catalogo.py del 23.

Visto bueno del front del reinicio 23 (4e sobre e6 5e4421c): ok, con dos condiciones para la API, ya enviadas a f4.
- **Qué se comprobó:** sin `franja`, las 57 respuestas reales del Space dan los mismos bloques que el front publicado. Una marca fuera de la franja no sube, y los bordes son exactos.
- **Condición 1:** `franja` redondeada a tres decimales, porque un borde de 1,2499999999999998 deja fuera el 1,25.
- **Condición 2:** anchura exacta de ±0,45, porque las etiquetas de encaje del front dependen de esas distancias.

Constantes del reinicio 23, aprobadas por la central (f4; calibradas con dragones, océano y dinosaurios antes de mirar la batería):
- **Umbrales:** FRANJA (−0,45, +0,45], SUELO_FRANJA 0,60, MARGEN_FRANJA 0,15, MARGEN_TECHO 0,25 (sin calibrar, se informa lo que corta) y K 12.
- **Parecido de franja:** el máximo entre el índice y el título, solo en el segundo top-k. El orden general no cambia.
- **Embeddings de títulos:** van en un archivo aparte, `catalogo_titulos_emb.npy` (23,6 MB, con los ids para comprobar el orden). Si los ids no cuadran, no se marca nada.
- **Rareza de «familia»:** era el rescate por título con parecido de letras («familia» ≈ «familiar», 0,93). Se exigen palabras enteras en el título, y el parecido de letras se queda solo para apellidos.
- **Reparto:** se parte en dos reinicios. El 23 lleva solo la recuperación por franja y el rescate por título. El 24 lleva autores clásicos, biografías, «Jane Austen» con B1, «luna» y «rosa», los 89 títulos, los textos que no están en inglés, titulo_capitulo y los menores de bloques.
- **Reinicio 22:** 11 de 12 mutantes detectados. no_lectura pasa a 203.

Reinicio 22 con commit (f4): código 8b259c5 y datos 9dcd867.
- **Pruebas:** mutantes C8, C9 y C10, 12 de 12 detectados. corpus 41/41 y api 58/58.
- **Datos:** no_lectura pasa a 203, con GHB, metanfetamina y un artículo SEO, tras revisar 29 cuentas de StoryWeaver.
- **Pendiente:** el visto bueno de 4e (catalogo.py y datos) y de e6 (api.py), y el árbol limpio en D:.
- **Front del 23 (e6):** cde661b recibió el «ok» de 4e.

e6 dio el visto bueno de api.py del reinicio 22 (8b259c5).
- **Pruebas:** pruebas_api 58/58, y el banco C9 detecta sus 3 mutantes.
- **Menor sin daño, para el 24:** si una subida y un borrado del mismo libro coinciden, pueden quedar su nombre y su título en el archivo de nombres. La estantería salta los archivos que no existen.

Visto bueno de 4e al reinicio 22 (f79b562, ronda3_2026-09-15_reinicio22.md): ok.
- **Serio del vocabulario de nombres, arreglado:** autor entre los 10 primeros, del Space del 21 al 22.
  - «treasure island stevenson»: de 2 a 10.
  - «love poems by browning»: de 0 a 7.
  - «the secret garden frances hodgson burnett»: de 0 a 8.
  - «the call of the wild by jack london»: de 4 a 10.
- **Batería:** sin cambios en lo demás. no_lectura queda en 203, sin cuentos.
- **Menores para el 24:** un nombre de pila corto o con iniciales convierte al autor en seudónimo («fu manchu sax rohmer» baja de 10 a 3). Un apellido que es palabra corriente vuelve a rescatar a quien no es («little dorrit dickens» con B1 trae a Burt Little).

**Reinicio 22 en producción y comprobado (f4):** Space 62a5373, fila de DESPLIEGUE en 5a61b19.
- **Autor en los 10 primeros sin perfil, del 21 al 22:** treasure island stevenson de 2 a 8; love poems by browning de 0 a 9; the secret garden frances hodgson burnett de 0 a 8; white fang jack london de 0 a 2, igual que antes de la regresión; the call of the wild by jack london de 4 a 10.
- **Sin regresiones:** «amor» con B1 sin Fenn, «rosa» con los títulos de Rosa primero y los anuncios de drogas fuera. La batería da lo mismo que en local.
- **Único fallo del comprobador:** «Jane Austen» con B1 abre con la adaptación de MacKaye, en la que Austen es coautora. Es el caso conocido del 24.
- **Siguiente, el 23:** el segundo top-k solo se activa desde /api/buscar; la búsqueda de Gradio no cambia.

Ronda 3 de voz (e6, b152637), sobre 2c0e681 en el Space 62a5373:
- **Cerrados:** la IPA en ASCII, y las abreviaturas Mr., Mrs., Ms. y Dr.
- **A medias: la grabación en silencio.** Ya no guarda nada, pero sigue llamando a explicar_correccion. Es una llamada de pago por grabación, con una corrección de palabras que nadie dijo. Además, «...» cuenta como oída.
- **Abierto:** «St.» conserva un enlace entre dos frases.
- **Dudas que siguen abiertas:** «going to work» → gonna, y el emparejado por orden.
- **Arreglos:** los hace 4e con el visto bueno de e6. voz.py sube en el siguiente reinicio que llegue a tiempo.

Arreglos de voz de la ronda 3 (4e, 86e6e1d, con aviso de Codex en el commit):
- **Silencio:** ya no llama a explicar_correccion, y un espía en la prueba lo comprueba.
- **«...»:** ya no cuenta como oída.
- **Abreviaturas:** «St.» sale de la lista, entra «Prof.» y «Jr.» se queda fuera.
- **IPA:** una IPA toda en ASCII casi igual a la palabra escrita tampoco pasa.
- **Pruebas:** suites en verde y mutantes 5 de 5.
- **Pendiente:** el visto bueno de e6, y después sube con el siguiente reinicio.

Visto bueno de e6 a los arreglos de voz (86e6e1d): ok, y suben en el siguiente reinicio.
- **Casos cerrados:** con silencio o «...» ya no hay llamada de pago; «St.» corta la frase; /houses/ por house ya no pasa como IPA.
- **Coste de la regla nueva de IPA:** rechaza 12 IPA más que antes, de 51.261 pares (0,02 %). Algunas son buenas en notación de EE. UU., como flue /flu/. Solo actúa en palabras sin IPA en el diccionario, así que la palabra queda sin IPA en vez de con una falsa.
- **Menor para el 24 (4e):** «uh» y «Thank you.», que whisper inventa con casi silencio, siguen contando como oídas.

**Recuperación por franja, antes de commit (f4).**
- **Lo que funciona:** Robots, Fantasmas, familia sin «Familiar», rosa y escuela marcan casi todo del tema. «Terror gótico» no marca ACTION PART-1, y «ghost stories» sin perfil no cambia. MARGEN_TECHO no corta nada.
- **Fallo, y por eso no sube:** títulos de una palabra o del tipo «My story» entran marcados solo por el vector del título, con un parecido de índice de 0,13 a 0,48. «amor» marca «HOLI» y «Kuppu», y «Monstruos» marca «Biryani».
- **Arreglos a medir con los temas de calibración:** que el título cuente solo con 2 palabras o más; o solo si el índice ya pasa 0,40; o solo contra la consulta tal cual, sin las frases «historias de X». También sus combinaciones.

**Cambio de numeración:** la voz 86e6e1d sube sola ya, como reinicio 23, porque el silencio aún lanza llamadas de pago. La recuperación por franja pasa a ser el reinicio 24, y lo que era el 24 pasa a 25.

Reinicio 23, solo voz (f4, --commit 86e6e1d): subiendo tras el árbol limpio.
- **Qué sube:** solo app/voz.py y app/lexicon.py, según el primer --seco.
- **Prueba en el Space:** la central autorizó una prueba de pago corta con invitado8, que Miguel habilitó para pruebas. Son dos llamadas a /api/voz: silencio, que no debe dar corrección ni guardar nada, y «Baker St. It was late.», que no debe tener enlace st‿it.
- **Contraseña:** leída del archivo local y nunca escrita.

Muletillas de whisper con casi silencio (4e, 0a759a5, para el reinicio 25):
- **Regla de whisper:** no caza ningún invento, porque salen con avg_logprob alto.
- **Regla nueva, fijada antes de validar:** no hay voz si todos los segmentos traen no_speech_prob > 0,6.
- **Validación con whisper-1:** 30 de 30 frases reales oídas (la más alta, 0,503) y 4 de 4 audios sin voz detectados (de 0,866 a 0,943). La voz era TTS, no micrófono.
- **Riesgo:** con el micrófono real y voz baja, el margen de 0,1 puede quedarse corto. Miguel lo comprueba en el ensayo con un punto 7 en «Antes de la demo», que añade 4e. e6 da el visto bueno buscando vías que dejen sin voz una grabación real.

**Reinicio 23 (voz) subido, pero no da por bueno el silencio (f4).** Space d854649, comprobador bien y segundo --seco limpio.
- **Prueba de pago con invitado8 (2 usos, pasa de 20 a 18):** 2,5 s de WAV a cero dan «you» en whisper. transcripcion_ok sale true, se lanza la corrección de pago y se guardan 6 palabras falladas en el lector de prueba. 86e6e1d solo paraba las transcripciones vacías o «...».
- **«Baker St. It was late.»:** bien, sin enlace st‿it.
- **Decisión:** 0a759a5 (regla de no_speech_prob) sube solo como reinicio 24 con el ok de e6. Después se repite la misma prueba con 1 uso.
- **Numeración:** 25 es la búsqueda por franja y 26 lo demás.
- **Incidente:** al mirar el formato de literalevel_codigos.txt, la contraseña de «profesor» salió en la salida de una herramienta local de f4. No fue a ningún mensaje, commit ni archivo. Miguel decide si la cambia.
- **Búsqueda por franja:** el ruido de títulos cortos viene del vector de la palabra sola, no de las frases. f4 mide ahora la variante inversa.

Visto bueno de e6 a 0a759a5: ok, y sube como reinicio 24.
- **Pruebas:** suites en verde y mutantes 10 de 11.
- **Mutante que sobrevive:** cambiar `all` por `any` en `_sin_voz`. Falta un caso de dos segmentos, 0,9 y 0,2, que cuente como oído. Solo son pruebas y no viajan al Space, así que 4e lo añade aparte.
- **Llamada de prueba de e6:** con una pausa larga de silencio, whisper devuelve un solo segmento con no_speech_prob 0,046 y la regla lo cuenta como voz. Pero whisper se comió la frase corta que iba justo después del silencio.
- **Límite:** whisper calcula no_speech_prob una vez por ventana de 30 s, y en Pronunciar eso es en la práctica un único valor.
- **Decisiones:**
  - e6 cambia el aviso de silencio en Pronunciar a «No te oí. Acércate al micrófono y vuelve a grabar.», y lo publica tras el 24.
  - 4e registra no_speech_prob al descartar, solo el número, para calibrar el umbral en el reinicio 26.

**Arreglo de títulos cortos para la búsqueda por franja (reinicio 25): elegida la variante E**, por la calibración y no por la batería.
- **Diagnóstico:** el ruido venía de comparar el título con la palabra suelta. «HOLI» o «Biryani» daban 0,79–0,86 contra «amor» o «Monstruos», y solo 0,35–0,64 contra «historias de X» o «libros sobre X».
- **Qué hace E:** en consultas de una palabra, el título se compara solo con esas frases.
- **Calibración** (dragones, océano y dinosaurios): 231 del tema de 236 marcados (97,9 %), el que más trae.
- **Batería:** 196 de 255. «amor» pasa de 3/12 a 8/12 con A2 y de 2/12 a 9/12 con B1; Robots da 9/9 y 7/7; amigos 17/17 en los dos niveles.
- **Límites declarados:** «Monstruos» se queda en 1/12 con cualquier variante, porque el MiniLM no lo acerca a «monster». «Historias de amor» tiene varias palabras, E no la toca y sigue trayendo los «My story».

e6 comprobó el caso exacto del silencio del Space con whisper simulado. Con 0a759a5 no hay corrección de pago ni se guardan fallos, así que el reinicio 24 puede subir.

Aviso «No te oí» en Pronunciar (e6, b9773bd, sin publicar, ng test 80/80):
- **Qué cambia:** con transcripcion_ok false, el front muestra «No te oí. Acércate al micrófono y vuelve a grabar.», con una raya en vez de «0/100» y sin la nota de ánimo. «Una frase de mi libro» usa la misma corrección.
- **Publicación:** HEAD entero tras el reinicio 24. Los commits de la franja son inertes sin los campos de la API, según la comparación de 4e.
- **Gradio (ui.py):** los mensajes de silencio se cambian en el reinicio 26.

**Reinicio 24 en producción y comprobado (f4):** Space 0c09197, solo app/voz.py de 0a759a5.
- **Prueba de pago con silencio, repetida exacta** (invitado8 pasa de 18 a 17): transcripcion_ok false, sin corrección de pago y sin guardar nada.
- **Menor para el 26 (4e):** la respuesta aún trae audio_correcto, el TTS de la frase modelo. Aquí salió de caché, pero con una frase nueva sería una llamada de pago.
- **Front:** e6 publica HEAD con el aviso «No te oí».
- **Reinicio 25:** f4 aplica la variante E. El banco C11 detecta 16 de 16.

Prueba de dos segmentos (4e, bf6aa0a, solo pruebas):
- **Casos:** «you» con 0,943 queda como no oído; «Thank you for watching.» con 0,897, no oído; 0,503, oído; dos segmentos de 0,9 y 0,2, oído.
- **Mutantes:** 10 de 10, incluido el cambio de `all` por `any`.
- **Límite:** una respuesta sin segments cuenta como oída. whisper-1 siempre los trajo al pedirlos.

Reinicio 25 con commit (f4, cb39b91): búsqueda por franja con la variante E.
- **Datos del commit:** tablas de calibración y batería, límites declarados y MARGEN_TECHO_FRANJA, que corta 0 de 811 marcados.
- **Batería completa en local:** 16 fallos, exactamente los mismos que en el Space de hoy. Ningún marcado es excluido, anuncio ni Fenn, y «ghost stories» sin perfil sale idéntico.
- **Plan de subida:**
  1. el .npy de títulos a mano (23,6 MB);
  2. catalogo.py y api.py con --commit cb39b91;
  3. el comprobador del contrato franja y por_franja;
  4. la batería en el Space.
- **Pendiente:** el visto bueno de 4e y de e6.
- **Si el código sube antes que el .npy:** no se marca nada, así que es seguro.

**Front publicado con el aviso «No te oí»** (e6): Space del front 657ea8f, que sirve b9773bd.
- **Antes de publicar:** los bloques de 350 respuestas reales salen idénticos a los del front anterior, sin franja y con franja sin marcas.
- **En la página a 390 px:** raya en vez de 0/100, el aviso nuevo y ninguna palabra marcada.
- **Con silencio aún se ven** «Cómo debería sonar» y «Bien leída», porque la API manda audio_correcto.
- **Decisión:**
  - En el 26, la API no genera audio_correcto sin voz (4e), y 4e comprueba si analizar_natural llama a OpenAI con silencio.
  - El front solo muestra esos botones si llega el audio, y esconde el aviso de énfasis y enlaces sin voz (e6).
  - Gradio aab69be también va al 26.

Visto bueno de e6 a api.py del reinicio 25 (cb39b91): ok, pruebas_api 59/59.
- **franja:** redondeada, con ±0,45 exacto, y null sin nivel.
- **por_franja:** presente en todas las tarjetas.
- **Matiz del contrato:** los resultados generales que ya cumplen las condiciones de franja se marcan en su sitio, y los nuevos van detrás, hasta 12. El orden general no cambia.
- **Gradio:** no pide franja.
- **Sin el .npy:** no se marca nada.
- **Pendiente:** el visto bueno de 4e a catalogo.py.

Front para el 26 (e6, 8ac6e31, sin publicar): sin voz ya no sale el aviso de énfasis y enlaces, y los botones de audio dependen de que llegue audio_correcto.

Prueba local de la franja del 25 (cb39b91 con el .npy de títulos) con los bloques del front, por e6:
- **Mejoras en «En tu nivel»:**
  - Fantasmas A2 pasa de 1 a 9, todos de fantasmas;
  - Familia C1 pasa de 0 a 4 más 4, sin «Familiar»;
  - rosa B1 pasa de 1 a 13 más 4 cuentos de rosas;
  - Detectives B1 pasa de 11 a 13.
- **Sin perfil:** «ghost stories» no marca nada.
- **Para mirar, sin ajustar sobre la batería:** «Terror gótico» con B1 mete 5 cuentos con índice de 0,33 a 0,49, entre ellos «The Enemy» y «The terror of the lion», que no son terror gótico. ACTION PART-1 no entra. «Historias de amor» con A2 trae tres «My story», que es el límite ya declarado.

Reinicio 25, antes de subir (f4):
- **Tercer límite declarado:** «Terror gótico» con B1 marca 5 cuentos solo por una palabra del título: tres «terror», un «ghost» y «The Enemy». Es la misma clase que «Historias de amor», una consulta de varias palabras que E no toca.
- **Propuesta para el 26, detrás de clásicos y «Jane Austen»:** en consultas largas, el título tiene que casar con más de una palabra. Se calibra con consultas de varias palabras escritas antes de medir.
- **Árbol limpio:** corpus y extremas fallaron por falta de memoria, con 3,4 de 16 GB libres y las copias del banco cargadas. No es un fallo del código. Se repiten solos cuando acabe el banco.
- **Pendiente:** el ok de 4e a catalogo.py, con plazo hasta las 05:14.

Reinicio 25: sube junto o no sube.
- **Por qué:** api.py de cb39b91 llama a `buscar(..., franja=True)` y a `franja_de`. El catalogo.py del Space no tiene ninguno de los dos, así que subir api.py solo daría 503 en todas las búsquedas.
- **Plan:** si a las 05:14 no hay ok de 4e, no se sube nada.
- **Memoria de la máquina:** 2,2 de 15,9 GB libres, con el banco de f4 en tres procesos (unos 2,6 GB) y dos `ng serve` del front vivos desde el 14 (unos 720 MB). Se le pidió a e6 que los pare si no los usa.

Devolución del uso con silencio, para el reinicio 26 (decisión de la central):
- **Cuándo:** si transcripcion_ok es false por silencio, se devuelve el uso. Si falla la red o falta la clave, no.
- **Límite:** 10 devoluciones al día **por cuenta**, no por lector, porque la cabecera X-Lector la pone el cliente.
- **Cómo:** una sola función, `cuentas.devolver_por_silencio(base, codigo)`, bajo el mismo candado del cobro, que llaman la API (f4) y Gradio (e6).
- **Voz del 26:** entra también 681544f de 4e, con el ok de e6. Sin voz ya no hay TTS ni análisis de pago.
- **RAM:** e6 paró los dos `ng serve` olvidados, y la RAM libre pasó de 2,25 a 2,81 GB.

**Visto bueno de 4e a cb39b91: franja y variante E, ok. Pero hay un serio.**
- **El serio:** exigir palabras enteras en el rescate por título pierde las erratas que el Space de hoy sí encuentra. «sherlok holmes» pasa de 8 Sherlock a 0, «treasure iland» saca Treasure Island del top 24 y «dracul» pasa de Dracula del 1 al 4 a 0. A cambio, «familia» deja de traer 23 «Familiar».
- **Decisión de la central:** una lectora se equivoca al escribir títulos en inglés más a menudo de lo que busca «familia».
  - El 25 sube sin ese cambio, con la franja, la variante E, el .npy y el contrato.
  - Añade los dos menores defensivos de 4e: un .npy desordenado o de otra dimensión no marca nada.
  - Hace falta un commit nuevo y un visto bueno corto de 4e.
- **Reinicio 26:** el rescate con erratas bien hecho. El parecido de letras no vale si la palabra es española y la app la traduce, y sí vale si no lo es.
- **Otro menor de 4e:** el techo corta 2 de 1.201 marcados.

**Decisiones de Miguel sobre Esmeralda:** propuesta A en Tu nivel y en Pronunciar. La hace e6, con visto bueno de 4e, solo en plantilla. 4e mide aparte el cuestionario (B1 sincero → A2).
- **Pronunciar tras corregir (e6, 9624b0a):** ya no se ofrece «Corrígeme» con la misma grabación.
- **Reinicio 25 corregido (f4, 9132a59):** sin palabras enteras, así que las erratas vuelven. La franja y E se quedan, y el .npy se comprueba por forma y contenido.
  - **Visto bueno de 4e:** ok. «sherlok holmes», «treasure iland» y «dracul» salen igual que hoy, ningún «Familiar» marcado y ACTION PART-1 fuera.
  - **Pendiente:** el árbol limpio y la subida.
- **Voz del 26:** sin_voz en 50a6304 (4e), con 15 de 15 mutantes.

Receta del perfil de la demo sin «Me vale así» (e6, medida en local y contra el Space):
- **Respuestas:** varias veces por semana · Alice con naturalidad · una novela actual · fragmento medio con naturalidad · los hechos principales · fragmento difícil con diccionario.
- **Resultado:** 1,20 exacto, B2, franja 0,95–1,45. Aguanta un despiste en la 2 o en la 6.
- **Guion:** 4e la escribe cuando se publique Tu nivel A.
- **Si cambia la fórmula** tras la medida de 4e, hay que volver a medirla.

**Reinicio 25 en producción y comprobado (f4):** Space 4ba66f9. El .npy de títulos está en f50cc1b, y catalogo.py y api.py van desde 9132a59.
- **Comprobador sin fallos:**
  - franja y por_franja presentes;
  - «Fantasmas» A2 con 13 marcados, así que el .npy cuadra en el Space;
  - Robots A2 9 y B1 7;
  - «familia» C1 sin «Familiar»;
  - ACTION PART-1 fuera;
  - «ghost stories» sin perfil igual;
  - «amor» sin Fenn;
  - anuncios de drogas fuera.
- **Batería:** los mismos 16 fallos que antes, así que no hay regresión.
- **Primera búsqueda con nivel tras el reinicio:** 18,6 s, por la carga del modelo y la comprobación del .npy. Las siguientes, 0,6–0,7 s.
  - El 26 empieza por precargar en el arranque, luego la devolución por silencio y después la búsqueda.
  - Hasta entonces, el guion dice que se caliente la búsqueda antes de la demo.

Cuestionario de Tu nivel (4e, 88c28d5): no infravalora de forma sistemática, así que la fórmula no se toca.
- **Método:** cuatro perfiles honestos, A2, B1, B2 y C1, fijados antes de calcular.
- **Resultado:** ninguno baja de letra, y el error medio es de +0,19 hacia arriba. B2 da 1,51 (C1) y C1 da 1,82 (C2). Afinar no cambia ninguna letra.
- **El A2 del recorrido de e6:** cabe en un B1 muy bajo, 1 de 64 combinaciones. No lo causa el fragmento difícil, sino el techo del fragmento fácil, que también hundía el nivel provisional. La propuesta A ya lo quita.
- **Decisiones:** Afinar no se mete en las seis, y la receta B2 de la demo sigue valiendo.
- **Pendiente:** la prueba honesta sería con lectores medidos también con un texto o un libro.
- **Registro del silencio para el 26 (06a7aac):** no_speech_prob, hora y origen. Mutantes 18 de 18, con el visto bueno de e6 pendiente.

Precarga del reinicio 26 (f4, medido en local):
- **Memoria y tiempo:** +1,18 GB en total, la misma RAM que hoy ocupa la primera búsqueda, pero desde el arranque. El modelo MiniLM se lleva 18,7 s de los 18,6 s que tarda hoy la primera búsqueda.
- **Diseño aprobado por la central:**
  - un hilo de fondo al arrancar, solo en el Space, que no retrasa RUNNING ni /api/salud;
  - candado en ui.catalogo(), para no crear dos catálogos (2,4 GB), con prueba y mutante;
  - una búsqueda con nivel lanzada durante la precarga tiene que esperar y responder bien.

**Contraseña de «profesor» cambiada (central, 05:40, a petición de Miguel en este chat).**
- **Antes de tocar nada:** las 10 cuentas del archivo local entraban en el Space, así que el archivo coincidía con el secreto.
- **El cambio:** una clave nueva de 16 caracteres, escrita en literalevel_codigos.txt y en el secreto LITERALEVEL_CUENTAS del Space. El Space se reinició solo y estaba RUNNING a los 50 s.
- **Comprobado después:** profesor entra con la nueva y no con la vieja; miguel, invitado1 e invitado8 siguen entrando; los usos no cambian.
- **Rastro:** ninguna contraseña ni el token salieron en ninguna salida. La copia de seguridad temporal se borró.

Chips sobre el reinicio 25 (4e, 7333c4b), con el criterio de e6 y contando también las tarjetas del tema:
- **Los 8 actuales:** cumplen con margen.
- **Reserva:** «Cuentos de hadas» cumple en número pero no trae cuentos de hadas (0 y 1 del tema).
- **Los 13 que no llegaban:** ahora cumplen 12. Amor, familia, fantasmas, amigos, escuela, brujas, robots, planetas, Navidad y misterios ya sirven. «Monstruos» cumple en número con solo 1 del tema. «Piratas» se queda en 2 con A2.
- **A 390 px con B1:** lo marcado de Fantasmas, la luna y Robots cae en sus dos bloques.
- **Decisión de la central:**
  - «Historias de amor» sustituye a «Viajes al espacio», y «Fantasmas» a «Cuentos de miedo para niños».
  - «Cuentos de hadas» sale de la reserva.
  - El criterio pasa a ser al menos 3 del tema, revisado a mano.

Visto bueno de 4e a las pantallas A (b4782a5): ok, con una condición antes de publicar. «🐢 Despacio» tiene que mostrar a la vista si está encendido. Además, «más seguido aquí» pasa a «de corrido aquí». Lo hace e6 en un commit con los chips.

Reinicio 26 en preparación (f4, sin commit):
- **Precarga medida de punta a punta:** se construye un solo catálogo. Una búsqueda lanzada a los 5 s espera a la misma carga y responde bien, y la siguiente tarda 0,37 s. Usa la misma memoria que hoy.
- **Devolución por silencio:** `cuentas.devolver_por_silencio`, con tope de 10 al día por cuenta. /api/voz añade el campo `uso_devuelto`.
- **Decisiones de la central:**
  - Revisan 4e (cuentas.py) y e6 (api.py).
  - Se autoriza una prueba de pago de silencio con invitado8, de 1 uso.
  - Se parte en dos:
    - **26:** precarga, devolución y los commits de voz y Gradio.
    - **27:** clásicos, «Jane Austen» con B1, rescate por título con la regla del diccionario, título en consultas largas y los menores de búsqueda.

Reinicio 26 con commit (f4, 41e7e6d): precarga y devolución por silencio, con api 62/62.
- **Vistos buenos pedidos:** 4e para cuentas.py y e6 para api.py.
- **Hueco que vio f4 antes de subir:** Gradio decía «No te oí», pero no llamaba a `devolver_por_silencio`. La comprobación prevista habría fallado. e6 lo cablea en ui.py con prueba y mutante, y el 26 no sube sin eso.
- **Front:** 41bd2af tiene el ok de 4e (Despacio visible, «de corrido aquí», chips de amor y fantasmas). e6 lo publica ahora.

**Pantallas A publicadas (e6):** front 83520e2, con Tu nivel A, Pronunciar A, «🐢 Despacio» visible, «de corrido aquí» y los chips de amor y fantasmas.

Visto bueno de 4e a cuentas.py del 26 (41e7e6d): ok.
- **Qué comprobó:** solo devuelve con `sin_voz`, nunca baja de cero, el día no se puede forzar desde el cliente, y 40 hilos dejan siempre 10 devoluciones. uso_openai.json no cambia de forma.
- **Dos menores para el 27:** el intento se apunta aunque no haya nada que devolver, y un valor raro en el registro deja sin devolución todo ese día.

Pasada de documentos de 4e sobre 83520e2, en curso:
- la receta B2, los textos de las pantallas A, el punto 7 y el calentamiento de la búsqueda;
- la frase del amor, recontada con el catálogo de la app. En la franja de B1 hay 114 textos libres con love o romance en el título y 4 de Gutenberg. Sin la franja, la búsqueda traía 24 de 24 de Gutenberg; con la del 25 se marcan 12, 8 con el amor en el título.

Comprobación del reinicio 26, autorizada por la central: dos llamadas de pago de silencio con invitado8.
- **Primero /api/voz:** tiene que salir `uso_devuelto` true y los usos quedarse en 17.
- **Después Gradio, con gradio_client** (`/_entrar` y `/_practicar` en la misma sesión): tiene que decir «No te oí» y devolver el uso. Solo se hace si /api/voz sale bien.
- **Coste:** solo whisper, unos céntimos. La contraseña va en una variable y no se imprime nada del archivo. Los usos de antes y después quedan en DESPLIEGUE.md.

Prueba final a 390 px del front publicado 83520e2 (e6):
- **Tu nivel:** con la receta B2 se guarda solo en 0,5 s y dice «Lees en inglés a nivel B2», sin «Me vale así».
- **Pronunciar:** sale en el orden de la propuesta A, «🐢 Despacio · activado» se ve con estilo, y tras corregir la barra dice «Grabar otra vez».
- **api.py del 26 (41e7e6d):** e6 le dio el ok.
- **Gradio:** la devolución está escrita, con prueba y 3 mutantes C14, a falta del hash.
- **Front para después del 26:** 51cda13, «Este intento no cuenta.», con visto bueno corto de 4e.

Corrección de 4e a la receta B2 de la demo: la sexta respuesta no aguanta un despiste hacia arriba.
- **El fallo:** «Capto bien la idea» en la sexta da 1,46, que ya es C1. B2 llega hasta 1,399, porque la letra es floor(nivel × 2,5 + 0,5).
- **Resto de despistes:** cualquier otra respuesta cambiada a la opción de al lado da entre 1,07 y 1,27, que sigue siendo B2.
- **En los guiones:** la receta dirá «en la sexta no elijas "Capto bien la idea"».

Reinicio 26, a punto de subir desde 49a8e4d (f4):
- **Qué lleva:** la precarga y la devolución (41e7e6d), los seis commits de voz y Gradio, y la devolución en Gradio de e6.
- **Qué sube, según el primer --seco:** ui.py, voz.py, cuentas.py y api.py; catalogo.py sale igual.
- **Vistos buenos:** 4e a cuentas.py y e6 a api.py. El ui.py de e6 aún no lo había revisado nadie, así que la central pidió un visto bueno corto de 4e antes de subir.
- **Orden:**
  1. los bancos C12, C13 y C14;
  2. el árbol limpio, de uno en uno por la memoria;
  3. la subida;
  4. la comprobación de la precarga;
  5. las dos pruebas de pago de silencio, primero /api/voz y después Gradio;
  6. el registro del Space, el segundo --seco y la fila de DESPLIEGUE.

Visto bueno de 4e a ui.py de 49a8e4d: ok, así que el 26 ya puede subir. También ok a 51cda13, el front de «Este intento no cuenta.».
- **Menores para el 27:** un comentario viejo contradice el código nuevo, y el código de la cuenta se lee dos veces.

Pasada de documentos de 4e (2a44731), sobre el front 83520e2 y el reinicio 25:
- **Receta B2** en los guiones, con el aviso de la sexta pregunta.
- **Textos de las pantallas A** y capturas del vídeo al día.
- **«Antes de la demo»:** punto 7, voz baja desde el móvil; punto 8, calentar el buscador.
- **La frase del amor** reescrita en documento y estrategia: no faltaba catálogo, fallaba la búsqueda. 114 cuentos libres frente a 4 de Gutenberg.
- **Barrido:** ya no quedan «Me vale así», «Más lento» ni «hueco de composición». PDF recompilados.
- **Pendiente:** cambiar el 18,6 s por la cifra de la precarga, y volver a medir el paso 2 («cuentos de dragones») con la franja.

**Reinicio 26 en producción y comprobado (f4):** Space 5c6f8d9, subido desde 49a8e4d. Árbol limpio con voz, api 62/62, extremas 350 y corpus 42/42.
- **Precarga:** el catálogo carga en 4,6 s y el modelo con los títulos en 24,8 s. Una búsqueda con nivel lanzada a los 5 s de RUNNING esperó 22,1 s y respondió bien; las siguientes tardan de 0,7 a 0,9 s. La memoria del proceso es de 2.562 MB.
  - **Matiz:** `catalogo: true` en /api/salud no significa que el buscador esté listo. En el 27 se añade `buscador_listo`.
- **Pruebas de pago con invitado8:**
  - /api/voz con silencio: sin corrección, `uso_devuelto` true y restantes en 17.
  - Gradio con el mismo silencio: «No te oí» y los usos siguen en 17.
  - Los usos quedan 17 → 17.
- **Registro:** «voz sin_voz» con no_speech_prob 0,943, la hora y el origen (api y gradio), sin texto.
- **Mutantes:** C12 5/5 y C13 5/5. C14 de e6 da 2 de 3, por un hueco en su prueba, que e6 está arreglando.

Guion de la demo al día con el 26 (4e, 5a3552a).
- **Punto 8:** si el Space acaba de reiniciarse, se espera medio minuto y después se hace una búsqueda de prueba. Sale la cifra de 18,6 s.
- **Paso 2:** «cuentos de dragones» trae 19 textos libres de 20. «Una novela de detectives victoriana» no trae ningún cuento libre, pero sí 3 de Gutenberg en su nivel.
- **Pendiente:** afinar el punto 8 con `buscador_listo` en el 27. Falta publicar el front 51cda13 (e6).

**Front dca18b4 publicado con el 26 (e6):** trae 51cda13. Con `uso_devuelto`, el aviso dice «No te oí… Este intento no cuenta.» y los usos no bajan; sin el campo, el aviso de antes. Comprobado a 390 px. El banco C14 da 3 de 3 con la prueba arreglada (24279b2).

**La app queda lista para que Miguel la pruebe:** motor 5c6f8d9 (reinicio 26), front dca18b4 y guion 5a3552a. El reinicio 27 está en curso: clásicos (f4) y los menores de ui.py (e6).

Reinicio 27, punto 1 (f4, sin código todavía): los clásicos por apellido.
- **Causa:** la compuerta de tema apaga el rescate por nombre, porque MiniLM no relaciona el apellido con sus libros. Las obras de Cervantes, Dante, Molière y Christie dan de tema entre 0,24 y 0,52, frente a techos de 0,57 a 0,75.
- **«tolstoy»:** es otro caso, un empate entre sus obras y los libros sobre él.
- **El diccionario Kaikki no sirve de señal:** es inglés, y «rosa» o «amor» salen como nombre igual que los autores.
- **Propuesta:**
  - (a) un apellido exacto de un autor con al menos 5 obras no lo apaga la compuerta;
  - (b) a igual rescate, gana el autor al título.
- **Decisión de la central:** (b) aprobado. (a) solo después de medir las colisiones con una lista de unas 100 palabras de tema escrita antes de mirar, como «london», «hope», «grey», «vega» o «paz».

Fallo que vio Miguel en el móvil, la ficha de un cuento de un solo capítulo (e6, ae4c8d8, a falta del ok de 4e):
- **Causa:** la frase absurda sale de la API (`_resumen_curva`, api.py:1206-1210); con una fila, la segunda mitad cuenta como 0. Gradio tenía el mismo fallo.
- **Front:** con un solo capítulo pone «Es un texto de un solo capítulo…», sin gráfica. Se publica antes del 27.
- **Gráficas:** con un solo punto pintan un círculo o un marcador.
- **«Lo que más se repite»:** filtro nuevo en ficha.caracteristicas; si todo son nombres propios, la sección no sale.
- **API:** f4 devuelve `forma`, `facil` y `dificil` en None con una sola fila (C17).
- **Pruebas:** ng test 93/93, extremas 351, mutantes 6/6.
- **Subida:** ui.py y ficha.py van con el 27.
