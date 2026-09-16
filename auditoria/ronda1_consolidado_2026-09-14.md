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

Reinicio 27, clásicos por apellido (f4, sin commit):
- **Riesgo de la regla (a) medido:** lista de 100 palabras de tema escrita antes de medir, 50 en español y 50 en inglés.
  - 7 coinciden con el apellido de un autor de al menos 5 obras: school, brown, grey, castle, king, hope y london.
  - En ninguna de las 100 cambia el top 10, ni sin perfil ni con B1.
  - **Decisión:** (a) aprobada con N=5.
- **Regla (b):** dar ventaja al autor sobre el título rompió la prueba de «rosa», porque Rosa es un colaborador (Martínez de la Rosa). La suite lo cazó antes del commit.
  - **Arreglo aprobado:** la ventaja solo cuenta para el primer autor del campo. Se comprueba también si con eso «Jane Austen» con B1 deja de abrir con la adaptación de MacKaye, que tiene a Austen como coautora.

Visto bueno de 4e a ae4c8d8:
- **Front y ui.py:** ok. El front se publica ya.
- **ficha.py:** falla con textos escritos en mayúsculas. En 48 de 49 se vacía la lista de repetidas, con palabras corrientes dentro (boy, cow, snake).
- **Arreglo medido por 4e:** solo cuenta como nombre lo Capitalizado que nunca aparece en minúscula, y lo escrito en mayúsculas no cuenta. Con eso, 0 textos en mayúsculas vaciados, 35 de 400 al azar, y Emma, P&P y Kian igual.
- **Quién y cuándo:** lo aplica e6 antes del 27, con prueba, mutante y visto bueno corto de 4e.

**Front bdfa418 publicado (e6, desde ae4c8d8):** la ficha de un solo capítulo ya dice «Es un texto de un solo capítulo…», sin gráfica vacía. «Lo que más se repite» se arregla cuando suba el 27. El arreglo de mayúsculas de ficha.py tiene prueba y 2 mutantes detectados, y falta medir los tres casos.

Arreglo de mayúsculas de ficha.py (e6, 3151f51), a falta del visto bueno corto de 4e:
- **Textos en mayúsculas:** se vaciaban 48 listas y ahora 0.
- **400 textos libres al azar:** se vacían 37, antes 41, y son nombres sueltos.
- **Emma y P&P:** idénticas. Kian sigue vacía.
- **Mutantes:** 2 de 2 detectados.
- **Duda:** SWV285707 podría estar escrito con Mayúscula En Cada Palabra, el mismo fallo en otra forma. 4e dice si es más que un caso aislado.
- **Subida:** va con el 27.

Visto bueno de 4e a 3151f51 (ficha.py): ok, entra en el 27.
- **Caso Title Case, medido:** 22 textos de 15.367. Se vacían 5 listas, y en dos o tres se pierden palabras corrientes.
- **Decisión:** es aislado y se deja así. Solo oculta una sección y no muestra nada falso.

Reinicio 27, clásicos medidos en el catálogo real (f4, sin commit, corpus 45/45):
- **Clásicos:** cervantes, dante, moliere y agatha christie abren con sus obras. tolstoy abre con sus obras y no con «My Visit to Tolstoy».
- **Palabras de riesgo:** «london», «hope» y «king» dan el mismo top 10 que antes. «amor» no trae a Fenn, y «rosa» y «luna» salen como antes.
- **Lo que falla:** «Jane Austen» con B1 sigue abriendo con la adaptación de MacKaye, que es C1 y tiene a Austen como coautora. Empata en rescate con sus novelas, y con nivel ordena el encaje.
- **Arreglo aprobado:** dentro de la ventana de nombres van primero las filas cuyo primer autor contiene todas las palabras de la consulta. Lleva una prueba inventada y el mutante C20.

Menores de ui.py para el 27 (e6, 4a265f6 y el banco en 5985e8e): el código de la cuenta se lee una sola vez y el comentario viejo está reescrito. Extremas 351 y C14 + C15 6 de 6. Falta el visto bueno corto de 4e, y los hashes ya los tiene f4.

Alcance del reinicio 27, cerrado por la central para no retrasarlo:
- **Entra:**
  - clásicos por apellido, con (a) N=5 y (b) solo para el primer autor;
  - el arreglo de «Jane Austen» con B1 (C20);
  - `_resumen_curva` con una sola fila (C17);
  - `buscador_listo` en /api/salud;
  - los menores de cuentas.py;
  - de e6: ae4c8d8 (ui.py), 3151f51 (ficha.py) y 4a265f6 (menores de ui.py).
- **Pasa al 28:** el rescate por título con erratas, que necesita una señal nueva medida porque el diccionario no sirve, y el título en consultas largas («Terror gótico», «Historias de amor»).
- **Vistos buenos:** 4e para catalogo.py, cuentas.py y 4a265f6, y e6 para api.py.

Visto bueno de 4e a 4a265f6 y 5985e8e (menores de ui.py del 27): ok. `_practicar` cobra y devuelve a la misma cuenta.
- **Acoplamiento:** el api.py del 27 ya usa la firma nueva de `_puede_pagar`, así que api.py y ui.py suben juntos o no sube ninguno.

Reinicio 27 con commit (f4, 9e51c18), a falta de los vistos buenos de 4e (catalogo.py y cuentas.py) y e6 (api.py).
- **Qué lleva:** clásicos con (a) y (b) al primer autor, «Jane Austen» con B1, `buscador_listo`, C17, /api/voz leyendo el código una vez, los menores de cuentas.py y la lista de palabras de tema en auditoria/.
- **Pruebas:** corpus 46/46 y api 66/66.
- **En el catálogo real:**
  - cervantes, dante, moliere, agatha christie y tolstoy abren con obra suya;
  - «Jane Austen» con B1 abre con The Watsons, Emma y Love and Freindship;
  - london, hope y king no cambian;
  - «amor» sin Fenn.
- **Pendiente:** el banco, el árbol limpio con los cinco commits de e6, el --seco de cinco archivos, la subida y el comprobador con clásicos, Austen, buscador_listo y SWV4008.

Visto bueno de 4e a 9e51c18:
- **cuentas.py:** ok con pruebas. Sus dos menores quedan arreglados, y los 40 hilos siguen dando 10 devoluciones.
- **catalogo.py:** ok solo por lectura, porque no había RAM libre por el banco de f4.
- **Menores:** el recorrido en Python de las 68.546 filas cuando salta la compuerta, las obras contadas sin las fechas del autor, y un False con el disco roto.
- **Después de subir:** 4e mide en el Space los clásicos, Austen, london, hope y king, los tiempos de las búsquedas que hacen saltar la compuerta y `buscador_listo`.

Visto bueno de e6 a api.py de 9e51c18: ok, solo por lectura por la RAM. Revisó `buscador_listo`, `_resumen_curva` con una fila y /api/voz con la firma nueva. Con esto el 27 tiene todos los vistos buenos y solo espera al banco y al árbol limpio de f4. 4e ya tiene la línea base del 26 y un vigía para medir el 27 en el Space.

**Reinicio 27 en producción y comprobado (f4):** Space 1708cb1, desde 9e51c18.
- **Antes de subir:** banco 12 de 12; árbol limpio con api 66/66, corpus 46/46, extremas 351 y ficha en verde.
- **`buscador_listo`:** pasa a true a los 29,2 s. `catalogo` ya decía true a los 0,6 s.
- **SWV4008 (Kian):** sin lista de repetidas, y la curva de una fila sin forma.
- **Clásicos, sin perfil y con B1:** tolstoy, cervantes, dante, moliere y agatha christie abren con obra suya.
- **«Jane Austen» con B1:** abre con The Watsons y Emma, sin MacKaye.
- **Tiempos:** cada búsqueda tarda de 0,6 a 0,7 s.
- **Batería en el Space:** de 16 fallos a 3. Quedan «rosa» con A2 y con B1, y «luna» con B1.
- **Orden del 28:** primero el título en consultas largas («Historias de amor» es un chip), después «rosa» y «luna» junto con las erratas, y al final los menores.

**SERIO en producción, reinicio 27 (4e, medida independiente en el Space).**
- **Qué pasa:** «london», «hope», «king», «school», «rose», «brown» y «castle» traen al autor en vez del tema. Sin perfil, london, hope y king comparten 0 de 10 resultados con el 26. Con B1, «king» trae «Color mixing guide For artists».
- **Por qué no lo cazó la medida previa:** comparaba con y sin la exención, no el 26 contra el 27 completo, que también tiene el extra de (b) y la clave `primero`.
- **Decisión de la central:** el reinicio 28 es solo este arreglo, con el criterio de que las 100 palabras de tema den el mismo top 10 que el 26 y los clásicos y Austen sigan bien. Si en una hora no está, el 28 sube con las tres reglas apagadas. Lo que era el 28 pasa al 29.
- **Lo que sí está bien en el Space:** los clásicos, Austen con B1, las búsquedas por debajo de 1 s y `buscador_listo` a los 23-29 s.

Medida independiente del 27 (4e): el anexo está en 6c71362 y el punto 8 del guion en 800060e.
- **Punto 8:** lo principal es hacer una búsqueda de prueba en Encontrar con el perfil guardado. Tras un reinicio, medio minuto, porque `buscador_listo` pasa a true a los 26-29 s.
- **Línea base para el arreglo del 28:** el catalogo.py que corre en el 25 y en el 26 es el de 9132a59, idéntico al de 49a8e4d según su sha1. f4 saca de ahí el top 10 de las 100 palabras de tema, sin perfil y con B1, y se lo pasa a 4e para comparar después de subir.

Ficha de Kian comprobada en el móvil con el 27 (e6, front bdfa418 y API 1708cb1): dice «Es un texto de un solo capítulo… su dificultad es 0,96 (B1)», sin gráfica vacía y sin «Lo que más se repite». La página mide 390 px.

Arreglo del 28 en curso (f4, sin commit):
- **Referencia:** el top 10 del 26 para las 100 palabras de tema, sacado con el catalogo.py de 49a8e4d, idéntico al de 9132a59, y guardado en auditoria/top10_palabras_de_tema_26.json.
- **Candidato:**
  - (b) solo cuando las obras de primeros autores con ese apellido superan a los títulos con la palabra;
  - `primero` solo con dos palabras o más;
  - prueba de «london» y mutantes C22.
- **Criterio:** las 200 listas iguales al 26.

Arreglo del 28, primera medida contra el 26 (f4, 198 listas):
- **Con la regla de proporción, (b) todavía cambiaba 6 listas:** brown, grey y hope, porque tienen más obras de autor que títulos con la palabra.
- **Quedan iguales:** london, king, school, rose y castle. Los clásicos, Austen con B1, «amor» y «rosa» siguen bien.
- **Decisión:** (b) sale entera. «tolstoy» sin perfil vuelve a abrir con «My Visit to Tolstoy», como en el 26. Se quedan (a), `primero` solo con dos palabras o más, `buscador_listo`, la curva de un capítulo y cuentas.
- **Pendiente:** repetir las 198 listas cuando haya RAM, con 1,3 GB libres. Si alguna sigue distinta, se decide antes de tocar nada.

Arreglo del 28 con commit (f4, b896b1f): 0 de 198 listas distintas del 26 para las 100 palabras de tema, sin perfil y con B1.
- **Siguen bien:** los clásicos, «Jane Austen» con B1, «amor» y «rosa». «tolstoy» sin perfil vuelve a «My Visit to Tolstoy», que se aceptó.
- **Pruebas:** corpus 46/46. La línea base está en auditoria/top10_palabras_de_tema_26.json.
- **Pendiente:** banco, árbol limpio, visto bueno de 4e, --seco (solo catalogo.py) y la subida con las 100 palabras comprobadas en el Space.
- **Front:** 4e dio el ok a 3662e57 de e6, los tipos de la curva con null, que sale con la próxima publicación.

Visto bueno de 4e a b896b1f, el arreglo del 28: ok.
- **Hueco:** el JSON de línea base no trae «rose». f4 lo añade con el catalogo.py del 26.
- **Después de subir:** el vigía de 4e repite las búsquedas en el Space.

**La regresión del 27 era más ancha:** el guion de f4 contra el Space vivo da 54 de 198 listas distintas del 26, en 27 palabras.
- **Palabras afectadas:** castillo, león, love, moon, family, friendship, ocean, forest, mountain, city, school, music, science, space, stars, brown, grey, teacher, snow, fire, castle, queen, king, princess, garden, island, hope y london.
- **Mecanismo, el mismo en todas:** un autor o una entidad con esa palabra en el nombre pasa delante, como Snow, Eliza R.; Love, Nat; o Ocean Spray.
- **El arreglo b896b1f** da 0 de 198 en local, y el guion queda validado para comprobarlo en el Space.
- **Árbol limpio:** corpus 46/46 y api 66/66, con extremas en marcha. --seco: solo catalogo.py.

**Reinicio 28 en producción y verificado por 4e (Space 74f1484, anexo 762d987): cerrado el serio del 27.**
- **Palabras de tema:** london, hope, king, school, brown y castle dan exactamente el top 10 del 26, en el mismo orden.
- **Siguen bien:** los clásicos y Austen con B1. tolstoy vuelve al 26.
- **Tiempos:** la búsqueda más lenta tardó 1,05 s.
- **`buscador_listo`:** true a los 14-17 s de RUNNING.
- **Pendiente:** «rose» contra el 26, y la comprobación de f4 con las 198 listas en el Space.

Reinicio 28 cerrado del todo (4e, anexo 68b7cf3): «rose» también da el mismo top 10 que el 26, con la línea base de f4 en 5a2fc04. Son 14 de 14 listas iguales y en el mismo orden. `buscador_listo` sale a los 14-20 s. Falta la batería de f4.

Reinicio 29, punto 1, el título en consultas largas (f4): **sin cambio de código.**
- **Calibración:** 14 consultas de varias palabras escritas antes de medir. Precisión de los marcados: base 85,4 %, G 84,4 %, J 80,7 % y K 81,2 %. Ninguna variante gana a lo desplegado.
- **Batería (solo informe):** G arregla «Historias de amor», pero vacía «Terror gótico», y elegirla sería decidir con la batería.
- **Decisión de la central:** «Historias de amor» y «Terror gótico» quedan como límite declarado. El chip «Historias de amor» sigue cumpliendo el criterio del tema (5 y 7 a mano).
- **Otros datos:** «rose» ya está en la línea base (5a2fc04). La comprobación de f4 del 28 en el Space da 0 de 198.

Front 3662e57 (e6): no hizo falta publicar. Son solo tipos de TypeScript, y el build sale idéntico al que ya estaba en el Space bdfa418.
- **Comprobado a 390 px:** Kian dice «Es un texto de un solo capítulo…», sin gráfica, y Pride and Prejudice dibuja su curva con marcas de capítulo.

Reinicio 28 cerrado también por f4, en DESPLIEGUE.md con el commit ca605c5.
- **Resultado:** 0 de 198 listas distintas del 26, y `buscador_listo` a los 20 s.
- **Batería en el Space:** 4 fallos. «tolstoy» sin perfil, que se aceptó, más «rosa» con A2 y con B1 y «luna» con B1, que van al 29.
- **Límite de las consultas largas:** documentado en auditoria/limite_titulo_consultas_largas_2026-09-15.md.
- **Siguiente:** f4 mide de dónde sale cada rescate por nombre en «rosa» y «luna» antes de proponer una señal.

Reinicio 29, «rosa» y «luna» con B1 (f4, datos sin propuesta):
- **Causa:** con una sola palabra, cualquier título que la contiene recibe rescate 1,0, con 134 filas en «rosa» y 25 en «luna». La compuerta de tema se decide en grupo por la mejor fila, así que queda abierta para todas. Con nivel, la ventana de nombres va primero y ordena el nivel. Por eso suben «The Water Supply of the El Paso» (índice 0,245) y «Luna, The Rajapalayam Puppy».
- **No es el mismo mecanismo que las erratas.**
- **Señal a medir:** con una sola palabra, el rescate por palabra del título se decide fila a fila, y cada fila solo lo conserva si su índice queda a menos de 0,20 del techo.
- **Calibración, escrita antes de medir:** títulos de una palabra (emma, dracula, hamlet…), erratas de una palabra (dracul, frankenstien) y palabras españolas que coinciden con títulos.

**SERIO para la demo, del segundo ensayo de e6** (front bdfa418, Space 74f1484, perfil 1,20).
- **Qué sale:** «dostoyevski» ya no da el aviso de «no hay libros en tu nivel». «En tu nivel» trae 9 tarjetas, 7 de ellas cuentos libres sin relación («Books» dos veces, «Story Chikkappa», «Tanaji Malusare»…). Crime and Punishment queda tras «Ver también», a 4,5 pantallas.
- **El guion** (paso 3) describe otra pantalla.
- **Hipótesis de la central:** es la franja del 25 con la variante E. En una consulta de una palabra, el título se compara con «historias de X» y «libros sobre X», y los títulos genéricos casan con ese marco, no con el autor.
- **Encargo a f4, prioritario sobre «rosa» y «luna»:** medir la causa y dos arreglos, que la franja no marque cuando se rescata a un autor y que los títulos solo genéricos no puntúen, con el criterio de autores con perfil, temas con A2 y B1 y las 100 palabras iguales al Space. 4e prepara una alternativa para el paso 3 por si no llega.
- **El resto del ensayo a 390 px cuadra con el guion:** la receta, «cuentos de dragones», los detectives, la ficha de Crime and Punishment, poverty, Pronunciar y «Mis palabras».

«rosa» y «luna» con B1: **límite declarado, sin cambio de código** (f4, medido).
- **Qué arreglaba la regla por fila:** «rosa» y «luna».
- **Qué rompía:** 70 de 200 listas de palabras de tema distintas del Space, con el primer resultado cambiado en 27. «dracul» perdía Dracula en los puestos 2 y 3. Además cambiaban 17 de 40 listas de títulos y 5 de 24 de autores.
- **Fallos que ya están en el Space y se apuntan sin tocar:** «emma» con B1, y «hamlet» y «ulysses» sin perfil. «frankenstien» no funcionaba ni antes ni con el candidato.
- **Siguiente, con prioridad:** las consultas de autor con perfil, que afectan al paso 3 de la demo.

Plan B del paso 3 de la demo, comprobado por 4e en la página publicada con perfil 1,20: **«Crimen y castigo de Dostoyevski»**.
- **Qué sale:** 0 marcados y el aviso de que no hay libros en tu nivel. Crime and Punishment es la primera tarjeta de «De otros niveles», sin pulsar «Ver también». La ficha y la curva son las del guion.
- **Decisión de la central:** se cambia ya en el guion, sin esperar al arreglo, porque ese arreglo solo quita marcas.
- **Hipótesis confirmada por 4e:** con una sola palabra, la variante E marca cuentos titulados «Books» o «The Story of Stories» en cualquier autor, también en «dickens».

Segundo ensayo de la demo (e6, d2883bc), sobre el front bdfa418 y el Space 74f1484, a 390 y a 1280:
- **Cuadra con el guion:** la receta B2, «cuentos de dragones», los detectives, la ficha de Crime and Punishment, poverty, Pronunciar, «Mis palabras», el libro de un solo capítulo y el plan B.
- **Serio del paso 3:** resuelto en el guion con «Crimen y castigo de Dostoyevski», que midió 4e. El arreglo del buscador sigue con f4.
- **Tiempos con el buscador caliente:** búsquedas de 0,5 a 0,8 s, primera consulta de palabra 4,5 s y boca 3D la primera vez 2,9 s en el móvil. La duración estimada sigue en 3:40–4:10.
- **Arreglos de guion para 4e:** la cifra de la boca 3D, que la frase de voz ya no cuenta como verificada, «reinicio 28» en el paso 2, y «Este intento no cuenta» en el punto 7.

Guiones al día con el segundo ensayo (4e, 5181c8f; guion_video.pdf recompilado):
- **Paso 3:** «Crimen y castigo de Dostoyevski», con el aviso y el libro primero en «De otros niveles». No se escribe «dostoyevski» a secas.
- **Arreglos:** boca 3D 2,9 s en el móvil, frase de voz sin verificar, «reinicio 28» y «Este intento no cuenta».
- **Lista de Miguel:** punto 9 nuevo, repetir el paso 3 con cuenta.
- **Documento y presentación:** sin cambios. Citan «dostoyevski» solo como rescate de un nombre mal escrito, y la API sigue poniendo Crime and Punishment en el puesto 2.

Causa medida de las consultas de autor con perfil 1,20 (f4, contra el catalogo.py del Space):
- **«dostoyevski»:** manda el suelo de 0,60. Pasan 12 marcas, 5 rusas por índice y 7 cuentos libres solo por título contra «historias de / libros sobre dostoyevski» (0,611–0,636). Sus obras quedan fuera de la franja (d 1,70).
- **«tolstoy» y «cervantes»:** el techo lo pone un título, y casi todo lo que entra es por título («Story», «My stories», «Books», «The Beast»).
- **«Jane Austen»:** entra por índice, por el nombre de pila.
- **Arreglos probados:**
  - **(i)** la franja no marca cuando se rescata a un autor. Arregla los autores y deja el top 10 igual, pero cambia las marcas con B1 de 50 listas de palabras de tema («love» baja de 15 a 3, «rosa» de 12 a 0). No vale.
  - **(ii)** títulos solo genéricos. No arregla ningún autor.
  - **(i)+(ii):** cambia las marcas de 57 listas.
- **Siguiente:** i3, que aplica (i) solo si el primer resultado general viene del rescate por autor. El criterio incluye las marcas de las 100 palabras.

Variante i3 (f4): la franja no marca si el primer resultado general viene del rescate por autor.
- **Autores con 1,20:** dostoyevski y sus variantes, tolstoy, cervantes, Jane Austen y oscar wilde pasan de 12 marcas a 0. dickens pasa de 17 a 5, todas suyas. «Crimen y castigo de Dostoyevski» sigue en 0.
- **Temas:** los tres de A2 y B1, iguales.
- **Las 100 palabras:** 197 de 198 listas iguales. La única distinta es «school» con B1, que pasa de 13 marcas a 1, porque su top 10 abre con una obra cuyo autor en StoryWeaver es «The Polymath School».
- **«crime and punishment» y «crimen y castigo»:** 1 y 4 marcas de tema, igual que hoy. Se aceptan.
- **Siguiente, i4:** i3 solo si esa primera obra es de Gutenberg. Se calibra con una lista de control de palabras que coinciden con autores-organización, escrita antes de medir.

Variante i4 (f4, primera pasada sin la lista de control): la franja no marca si el primer resultado general es una obra de Gutenberg rescatada por autor.
- **Las 100 palabras:** 0 de 198 listas distintas del Space en top 10 y marcas. «school» con B1 conserva sus 13 marcas.
- **Autores con 1,20:** los clásicos de una palabra y Jane Austen pasan de 12 marcas a 0, dickens a 5 marcas suyas, y mark twain sigue en 0.
- **«Crimen y castigo de Dostoyevski»:** 0 marcas. Los temas de A2 y B1, iguales.
- **Falta:** la pasada con las 20 palabras de control, escritas a las 08:31.

i4 con la lista de control (f4, n=10):
- **Las 100 palabras:** 0 de 198 listas distintas del Space.
- **Las 20 de control:** top 10 igual en las 40 listas. Solo cambian las marcas de «institute» con B1, de 12 a 0, porque su primer resultado es un libro de Gutenberg de un coautor institucional. Las marcas que se pierden no tienen que ver con «institute» («Books», «My School»).
- **Autores y paso 3:** los autores con 1,20 y «Crimen y castigo de Dostoyevski», como en la pasada anterior.
- **Decisión de la central:** se acepta el cambio de «institute» (opción a).
- **Condición antes del commit:** una pasada final con n=24, que es lo que pide el front, con todos los grupos. Después, visto bueno de 4e, árbol limpio y subida como reinicio 29.

Pasada final de i4 con n=24 (f4): cumple los cuatro criterios, y un assert confirma que las filas propias son exactamente las de Gutenberg.
- **Las 100 palabras:** 0 de 198 listas distintas del Space.
- **Control:** 1 de 40 distinta, «institute» con B1, que ya se aceptó.
- **Temas A2 y B1:** iguales.
- **Autores con 1,20:**
  - tolstoy, cervantes, Jane Austen y oscar wilde pasan de 12 marcas a 0;
  - dickens se queda en 5, todas suyas;
  - dostoyevski y sus variantes se quedan con 1 a 4 marcas de cuentos rusos que ya estaban entre los 24 generales, no añadidos por título.
- **«Crimen y castigo de Dostoyevski» con 1,20:** 0 marcas.
- **Siguiente:** parche, prueba y mutantes C23, banco, commit, visto bueno corto de 4e, árbol limpio y subida como reinicio 29.

Reinicio 29 con commit (f4, 7e2b861): la regla i4 con `_n_propio`.
- **Pruebas:** corpus 47/47 y mutantes C23 2 de 2. El --seco solo trae catalogo.py.
- **Pendiente:** el visto bueno de 4e y el árbol limpio.
- **Aviso sobre la comprobación:** con n=24, el Space del 28 y la medida local del mismo código difieren en 13 de 257 listas. En 12 solo cambia el orden de los puestos 11 a 24, y en «trust» sin perfil también el top 10.
- **Criterio tras subir:** comparar el Space 29 con un volcado del Space 28 en el mismo entorno, no con la medida local. Solo pueden cambiar los autores con 1,20, «Crimen y castigo de Dostoyevski» con B1 e «institute» con B1.

Visto bueno de 4e a 7e2b861, el reinicio 29: ok.
- **Qué comprobó:** «es de Gutenberg» usa la frontera `_n_propio` y no el prefijo del id, el rescate por título no activa la regla, y sin perfil no cambia nada.
- **Tras subir:** 4e repite en el Space, contra su línea base del 28, el paso 3 con 1,20 y B1, dostoyevski, school, cervantes, dickens y las palabras de control. Compara top 10 y marcas, sin el orden de la cola.

**Fallo del micrófono de Ismael, confirmado (e6, en el front publicado a 390 px).**
- **Qué pasa:** los avisos y el estado de Pronunciar se pintan debajo de la barra fija del micrófono, así que no se ven.
  - Sin `navigator.mediaDevices`, como en el WebView de WhatsApp en Android, el aviso «Este navegador no deja grabar audio» queda tapado. El usuario toca y no ve nada.
  - Con el permiso negado o sin micrófono pasa lo mismo, y el texto de «sin micrófono» dice que falta el permiso, que es falso.
  - Con el permiso concedido, «Grabando…» también queda tapado, y nunca dice «habla ahora».
  - Sin frase, un toque no hace nada.
- **Arreglo aprobado (e6, con visto bueno de 4e):** una línea de estado dentro de la barra fija, siempre visible, con «Acepta el permiso…», «Grabando: habla ahora · N s» y un mensaje para cada rechazo. En un WebView de Android o sin `mediaDevices`, un aviso antes de pulsar para abrir la app en Chrome. Se publica sin esperar al informe de ayuda.

Reinicio 29 (f4): las 13 diferencias entre local y Space son empates entre parecidos iguales, que se ordenan distinto en cada entorno. La comprobación tras subir compara el Space 29 con el volcado del Space 28. Para el 30 queda un desempate determinista por id.

**Reinicio 29 subido (f4):** Space 5ab6832, desde 7e2b861. Árbol limpio con corpus 47/47, api 66/66 y extremas 351. Siguen en marcha la comprobación de f4 contra el volcado del Space 28, la batería y la medida independiente de 4e.

**Reinicio 29 verificado por 4e** (Space 5ab6832, anexo a91ecc9): cambia lo que tenía que cambiar y nada más.
- **Medida:** 11 consultas por tres perfiles (sin perfil, B1 y 1,20), con n=24.
- **Top 10:** igual en 33 de 33 listas, en el mismo orden.
- **Marcas del 28 al 29:**
  - cervantes pasa de 12 a 0;
  - dickens con 1,20 pasa de 17 a 5, suyas;
  - dostoyevski con 1,20 pasa de 15 a 3 cuentos rusos que ya estaban. «Books» y «Story Chikkappa» ya no salen.
  - «Crimen y castigo de Dostoyevski» con B1 pasa de 4 a 0.
- **Paso 3 del guion:** sin cambio, con el aviso y el libro primero.
- **Palabras de control y school:** iguales al 28.
- **Tiempos:** ninguna búsqueda llega a 2 s. `buscador_listo` sale a los 16-19 s.

**Posible regresión del 29 con perfil 1,20** (vista por e6, sin confirmar).
- **Qué se vio:** «animales de la granja» con 1,20 se queda sin «En tu nivel». En el 28 salían 9 cuentos libres en ese bloque y 6 en «Un poco por encima»; en el 29, solo 3 libros de Gutenberg en «Un poco por encima».
- **Sospecha:** un rescate por apellido parecido («granja» ≈ «Grange») activa la regla y apaga la franja.
- **El hueco de la medida:** las 100 palabras se midieron sin perfil y con B1, pero ningún tema con 1,20.
- **Decisión de la central:**
  - primero, «cuentos de dragones» con 1,20, que es el paso 2 del guion. Si cambió, f4 vuelve el Space al catalogo.py del 28 sin esperar.
  - después, el alcance con las 100 palabras y los chips con A2 y 1,20. Si más de 3 palabras de tema pierden marcas, también se vuelve al 28.
- **Regla nueva:** el perfil 1,20 entra en el criterio de toda regla de la franja.

Reinicio 29, comprobación de f4 contra el volcado del Space 28:
- **Sin cambio esperado:** 0 de 247 listas distintas.
- **Con cambio esperado:** 0 de 10 distintas de lo medido en local.
- **«Crimen y castigo de Dostoyevski»:** 0 marcas con 1,20 y con B1.
- **Batería:** los mismos 4 fallos que en el 28.
- **Paso 2 del guion:** «cuentos de dragones» con 1,20 no cambia. Abre con un texto libre, así que la regla no puede activarse. No se vuelve al 28 por esto.
- **En curso:** el diagnóstico de «animales de la granja» con 1,20, y el alcance con las 100 palabras, los chips y la reserva con A2, B1 y 1,20.

Causa probable de «animales de la granja» en el 29 (4e):
- **Mecanismo:** el primer resultado es de «United States. Bureau of Animal Industry». «animales» ≈ «animal» (0,86) pasa el umbral de nombres (0,75), así que i4 lo toma por búsqueda de autor y apaga la franja, también con A2 y B1.
- **Alcance según 4e:** los 21 chips con A2 y B1 dan los mismos bloques que en el 25. Con 1,20 no hay línea base del 28; «Robots» (Shea, Robert) conviene revisarlo.
- **Variantes a medir si la medida de f4 no manda volver al 28:**
  - i5, que la central prefiere: la regla solo actúa si casan con el autor al menos la mitad de las palabras de contenido de la consulta;
  - i6: excluir autores corporativos.

Arreglo del micrófono de Pronunciar (e6, 601788b), con el ok de 4e:
- **Línea de estado:** va dentro de la barra fija y ya no la tapa nada. Muestra «Acepta el permiso…», a los 5 s la sugerencia de abrir en Chrome o Safari, y «Grabando: habla ahora».
- **Errores:** un mensaje distinto para cada tipo de fallo.
- **WebView de WhatsApp en Android:** aparece «Abrir en Chrome» antes de tocar nada.
- **Robustez:** el doble toque no hace nada, y si falla después del permiso se suelta el micrófono.
- **Menor, que e6 cierra en un commit aparte:** si se sale de la pantalla con el permiso pendiente y se concede después, el micrófono queda encendido.
- **Falta:** que Ismael lo pruebe en su Android desde WhatsApp.

**Vuelta atrás del 29 al 28** (f4, aplicando la regla acordada): con 1,20, 4 consultas de tema pierden marcas, más de 3.
- **Consultas afectadas:**
  - «león» pasa de 12 marcas a 0 (Cieza de León);
  - «brown» de 12 a 0 (un autor Brown);
  - «hope» de 9 a 4 (Laura Lee Hope);
  - «animales de la granja» de 15 a 3. Con A2 y B1 también pierde marcas.
- **Qué vuelve al Space:** el catalogo.py de b896b1f.
- **Qué se pierde:** las consultas de autor con perfil vuelven a colar cuentos como «Books». El paso 3 del guion no depende de ello, porque «Crimen y castigo de Dostoyevski» ya daba el aviso en el 28.
- **Siguiente:** i5 e i6 no arreglarían «león», «brown» ni «hope», porque ninguna distingue autor de tema en una palabra. Se sustituyen por i7, que ataca la causa: el título no cuenta si casa igual con el marco «libros sobre» sin la palabra. Se mide sin prisa de demo.

**Corrección: la vuelta atrás al 28 NO se hizo.** El clasificador de permisos de la sesión de f4 denegó la subida («Production Deploy»). f4 no la rodea ni la pide a otra sesión, y la central tampoco: la tiene que autorizar Miguel en el chat de f4 o hacerla él.
- **Estado del Space:** sigue en el 29 (5ab6832). Con 1,20 pierden marcas «león», «brown», «hope» y «animales de la granja», y esta última también con A2 y B1.
- **Comando listo:** `python -X utf8 tools/desplegar_app.py --solo app/catalogo.py --commit b896b1f`. Solo sube catalogo.py.

**Micrófono publicado (e6):** 601788b, en el Space del front 0cfa382. Con el aviso de abrir en Chrome en el navegador de WhatsApp, «Acepta el permiso del micrófono», «Grabando: habla ahora» y un mensaje para cada error. Falta que lo pruebe Ismael.

Decisión de Miguel (AskUserQuestion en la central): **volver al 28**. La autorización de la subida la da él en el chat de f4, porque la bloqueó el permiso de esa sesión. La central no la reenvía como permiso.

Chips del 29 contra el 28 (f4, 27 consultas, n=24, A2, B1 y 1,20):
- **Cambia solo «animales de la granja»:** A2 pasa de 16 marcas a 4, B1 de 13 a 1 y 1,20 de 15 a 3. Los otros 26 quedan iguales.
- **Total de pérdidas con 1,20:** león, brown, hope y animales de la granja. La vuelta atrás sigue pendiente de Miguel.

i7 en preparación (f4, sobre el catalogo.py del 28): el título no cuenta si casa igual con el marco solo («historias de», «libros sobre»).
- **Calibración:** escrita a las 09:04, con 10 temas y 8 autores que no están en ninguna lista.
- **Márgenes a medir:** 0,00, 0,05 y 0,10, más la variante i7b de 4e.
- **Criterio:** el completo con A2, B1 y 1,20.
- **Aviso:** «Jane Austen» tiene dos palabras y sus marcas vienen del índice, así que i7 no las quitará.

Menor del micrófono cerrado (e6, e3f80e4, con el ok de 4e): si alguien sale de Pronunciar con el permiso pendiente y lo concede después, el micrófono se suelta y no graba. Prueba y mutante, ng test 105/105. Se publica ya, sin esperar a otra publicación.

Informe de ayuda para alguien nuevo (e6, ca604e4, auditoria/ismael_ayuda_2026-09-15.md).
- **Dónde se pierde:** 11 puntos. Los más graves:
  - «Entrar» abre Ajustes por arriba y «Tu perfil» queda fuera de la pantalla;
  - el icono de Ajustes no tiene texto;
  - la tarjeta «Mídeme» de Inicio promete una estimación que ya no existe.
- **Dos formas de ayuda:**
  - (A) una bienvenida de 4 pasos;
  - (B) una línea de ayuda por pantalla con «?», que e6 recomienda porque no añade pasos a quien ya sabe.
- **Saturación medida:** casi todas las pantallas enseñan la primera acción sin scroll. Satura en cuatro sitios: el lector la primera vez, con dos avisos y dos líneas de libro; Pronunciar, con 46 palabras antes de la caja; la ficha, con el Índice a 1,9 pantallas; y Ajustes, con «Tu perfil» en sexto lugar.
- **Recortes:** una tabla con qué acortar o plegar en cada pantalla.
- **Decide Miguel:** A, B o las dos; los tres arreglos; y los recortes.

Decisiones de Miguel sobre la ayuda: las dos formas (bienvenida de 3 pasos y línea de ayuda en Pronunciar y en el lector), los tres arreglos ya y el recorte del lector la primera vez. e6 lo hace en tres tandas con visto bueno de 4e. Miguel aprobó en el chat de 4e la vuelta al 28, pero el permiso de subida es de la sesión de f4 y lo tiene que conceder allí.

Front bb31cf4 publicado (e6, e3f80e4): el micrófono se suelta si el permiso llega después de salir de Pronunciar. Lleva también 601788b.

Tanda 1 de ayuda (e6, ad72c8d), a falta del ok de 4e: «Entrar» abre «Tu perfil» con el cursor en Usuario, la cabecera dice «Ajustes» y la tarjeta «Mídeme» ya no promete la estimación. ng test 110/110, el mutante cae y a 390 px nada queda tapado.

Miguel escribió «Autorizo» en el chat de e6, otra vez en un chat que no despliega. e6 no lo aplica. La vuelta al 28 sigue pendiente de que la autorice en el chat de f4.

**Vuelta atrás al 28 subida** (f4, con autorización de Miguel en su chat): Space 62e5a06, con el catalogo.py de b896b1f. f4 compara las 257 listas con el volcado del 28 y confirma el paso 3, y 4e lo comprueba desde fuera.

Tanda 1 de ayuda: ok de 4e a ad72c8d. «Entrar» abre «Tu perfil» con el cursor en Usuario desde Pronunciar, la ficha y la hoja de la palabra, y «Mídeme» dice «Al final ves tu nivel». e6 la publica.

Tanda 1 de ayuda publicada (e6, ad72c8d): Space del front 83f189d, con «Ajustes» con su nombre, «Entrar» hacia «Tu perfil» y la tarjeta «Mídeme» corregida. Lleva también el micrófono. Queda un menor sin bloquear, la marca de «Entrar» con el panel ya abierto, que va a la tanda 2 si sale barato.

**Vuelta atrás al 28 verificada por 4e** (Space 62e5a06, anexo b7cd8d7): las 33 listas de su línea base son idénticas.
- **Las cuatro palabras recuperan sus marcas:** león 12, brown 12 y hope 9 con 1,20; animales de la granja 15 con 1,20, 16 con A2 y 13 con B1.
- **Paso 3 del guion:** sigue bien.
- **«dostoyevski» con 1,20:** vuelve a colar 15 marcas, lo esperado.
- **`buscador_listo`:** esta vez tardó 43-46 s. El punto 8 del guion pasa a «espera un minuto».

Vuelta atrás al 28 comprobada también por f4: las 257 listas del Space 62e5a06 son iguales al volcado del 28, y el paso 3 del guion está bien.
- **DESPLIEGUE.md:** filas del 29 y de la vuelta atrás, con el hueco de medida y el permiso denegado y luego autorizado.
- **Arranque lento:** RUNNING a los 72 s y `buscador_listo` a los 55 s. El log muestra que MiniLM se bajó del Hub sin token. Para el 30, f4 comprueba si es la causa y propone dejar el modelo dentro del Space, porque depender del Hub en cada arranque es un riesgo.

**i7 medida: ninguna variante cumple, no se sube nada** (f4, contra el 28, n=24, con A2, B1 y 1,20).
- **Calibración** (colados y buenos, B1 y 1,20): el 28 da 221/161; i7 con margen 0,00, 184/161; con 0,05, 150/161; con 0,10, 119/161; i7b, 21/109.
- **i7 con 0,05:** entre 11 y 14 listas de tema pierden marcas por perfil (grey pasa de 12 a 2, river de 16 a 9), igual que las de control. Y no arregla tolstoy, cervantes ni wilde.
- **i7b:** rompe casi todos los temas («amor» pasa de 12 a 0).
- **Por qué:** los colados de tolstoy o wilde sí cambian con la palabra, porque MiniLM los acerca por tema, no por el marco. El modelo no sabe quién es Tolstoy.
- **Decisión de la central:** límite declarado. Con perfil, «dostoyevski», «tolstoy» o «cervantes» a secas marcan cuentos sin relación. El guion usa «Crimen y castigo de Dostoyevski».
- **Para después de la entrega:** decidir «autor» por la consulta.
- **Siguiente, el 30:** desempate determinista y MiniLM dentro del Space.

Reinicio 30, primeros datos (f4, sin cambios todavía):
- **Arranque:** el Space (cpu-basic) no tiene almacenamiento persistente ni `preload_from_hub`, así que baja MiniLM (471 MB) del Hub sin token en cada arranque.
- **Propuesta aprobada:** 30a, solo con `preload_from_hub` en la cabecera del README del Space, comprobando que la caché del build es la que usa `_ruta_local` y midiendo `buscador_listo` en 2 reinicios.
- **Aparte, 30b:** el desempate determinista, con puntuaciones redondeadas a 6 decimales y orden estable por fila, medido contra el 28. Solo pueden cambiar empates.
- **Vistos buenos:** 4e antes de cada subida. Si el permiso de la sesión de f4 vuelve a bloquear, se le pide a Miguel en ese chat.

Tanda 2 de ayuda publicada (e6, 6f4e01f, con el ok de 4e): Space del front 898a640.
- **Lector:** la primera vez sale un solo aviso con ✕, «Mantén presionada una palabra para ver qué significa; desliza para cambiar de página.», y un «?» en la barra lo vuelve a mostrar. A 390 px se ven cuatro renglones del libro donde antes eran dos.
- **Pronunciar:** la línea de ayuda sustituye al subtítulo la primera vez, con ✕ y «?».
- **Siguiente:** la tanda 3, la bienvenida. 4e revisa los guiones cuando esté publicada.

Límites declarados de la búsqueda ya en el documento y la estrategia (4e, f829d60, documento.pdf recompilado).
- **Documento:** limitación 15, con tres límites medidos sobre el Space del 28:
  - un autor de una sola palabra con perfil;
  - las consultas de varias palabras, como «Historias de amor» o «Terror gótico»;
  - una sola palabra que coincide con un título, como «rosa» o «luna» con B1.
  Cada uno lleva su cifra y el arreglo descartado.
- **Estrategia:** un párrafo con los tres, detrás de «Primeros usuarios».

Reinicio 30a preparado (f4), a falta del ok de 4e: `preload_from_hub` con solo los 10 archivos de MiniLM que el Space baja al arrancar, no el repo entero de 4,6 GB.
- **Comprobado:** sin HF_HOME ni TRANSFORMERS_CACHE en las variables, así que la caché del build es la que usa `_ruta_local`. En local, con una caché nueva y sin red, el modelo carga.
- **Cambio:** 2 líneas al final de la cabecera YAML del README del Space, con un guion que aborta si se tocara algo más.
- **Tras subir:** reconstrucción completa y medida de `buscador_listo` en 2 reinicios.

Reinicio 30a subido (f4, con el ok de 4e): Space 282c46f. Solo cambia README.md, con 2 líneas de `preload_from_hub`, y el buscador sigue siendo el del 28. Con la reconstrucción completa en marcha, f4 mide RUNNING, `buscador_listo` y si el log aún muestra la descarga del modelo, y después repite en un segundo reinicio.

Tanda 3 de ayuda, la bienvenida (e6, 13a730e), a falta del ok de 4e.
- **Cuándo sale:** 3 pasos, solo en la primera visita a Inicio y nunca sobre un enlace directo. Tiene «Saltar» en cada paso, «Medir mi nivel» y «Solo quiero leer» al final, y «Ver la bienvenida otra vez» en Ajustes.
- **Pruebas:** ng test 121/121. A 390 px la tarjeta queda por encima de la barra.
- **Decisión de la central:** quien ya usaba la app la ve una vez, porque las personas que se perdieron eran justo usuarios que volvían.

Visto bueno de 4e a la bienvenida (13a730e): ok, con dos textos a cambiar antes de publicar.
- **Paso 2:** «te decimos qué significa ahí» pasa a «qué significa y cómo se pronuncia», porque la explicación en contexto pide entrar.
- **Paso 1:** «para que elijas uno que puedas terminar» pasa a «uno a tu medida».
- **Lo que está bien:** solo en Inicio, nunca sobre enlaces directos, entera a 390 px, «Saltar» y Escape guardan la marca, funciona sin cuenta, y «Solo quiero leer» abre Alice.
- **Menor:** la tarjeta no retiene el foco con Tab. e6 lo cierra si sale barato.

f4 revierte i4 en el repositorio (3345ba9): el Space volvió al 28, pero HEAD seguía llevando i4 en catalogo.py, pruebas_corpus.py y banco_mutantes.py, y el siguiente despliegue lo habría subido otra vez. Los tres archivos quedan iguales a b896b1f, y el código de i4 se conserva en 7e2b861.

**Reinicio 30a medido (f4, Space 282c46f): MiniLM ya no se descarga al arrancar.**
- **`buscador_listo`:** a los 20 s de RUNNING, frente a 55 s en 62e5a06.
- **Línea «api precarga»:** catálogo 5,9 s y modelo con títulos y primera búsqueda 17,2 s. Antes eran 11,9 s y 44,4 s.
- **Descargas en el log:** ninguna, aunque el log se leyó solo 20 s.
- **Segunda medida:** no se reinicia a propósito, porque Ismael puede estar probando. Se mide al subir el 30b.

Reinicio 30b medido (f4, 545 listas contra el 28): solo cambian empates y ningún top 10.
- **Qué cambia:** 18 listas cambian el orden entre ids de parecido idéntico. Otras 12 están en la cola de la franja, entre copias con el mismo título.
- **Casos con efecto:** en 4, en el corte de K entra otra copia del mismo título con otra dificultad. Por ejemplo, «family» A2 pasa de SWV345576 (0,68) a SWV100912 (0,25).
- **Decisión de la central:** en la franja, el empate lo decide primero la cercanía al nivel del lector y después la fila. Sin nivel, la fila. Así nunca entra una copia más lejana por azar ni por orden de fila. Se vuelve a medir antes del commit.
- **DESPLIEGUE:** la fila del 30a está en ef8b743.

**Tanda 3 de ayuda publicada** (e6): Space del front c73bbcc, con 13a730e y a202a99. La bienvenida de 3 pasos ya lleva los textos de 4e («uno a tu medida», «qué significa y cómo se pronuncia») y retiene el foco con Tab. ng test 122/122. Con esto terminan las tres tandas de la ayuda, y 4e actualiza ahora los guiones.

**Ensayo de e6 sobre 282c46f y c73bbcc** (perfil 1,20, 390 px):
- Paso 3 con «Crimen y castigo de Dostoyevski»: aviso y *Crime and Punishment* **primero** en «De otros niveles», a 679 px. El guion decía «segundo»; pasado a 4e.
- «dostoyevski» a secas no sirve: el libro queda a 3.789 px, detrás de «Ver también».
- «animales de la granja» da 9 libres; «dragones» da 19 de 20; los detectives dan 3 de Gutenberg.
- Bienvenida con el texto nuevo.
f4 acepta la clave del 30b (parecido redondeado, |d − nivel|, fila) y mide cuando acabe el banco C24. Añadido al criterio de paro: el paso 3 tiene que seguir saliendo primero.

**Guiones tras la tanda 3** (4e, 5ee4949):
- Archivos: guion_demo_en_vivo.md, guion_video.md, .tex y .pdf (9 páginas).
- Textos comprobados en c73bbcc a 390 px.
- «Antes de la demo»:
  - punto 10: bienvenida y «Saltar»;
  - punto 11: ayudas de la primera vez, que se cierran con ✕.
- Paso 4: «mantén presionada».
- Paso 3: con posiciones fechadas (ensayo del 15 sep sobre el 28).
- Revisión encargada a e6.
- MENOR para e6: el aria-label de la figura de Inicio aún dice «tocar… ahí». Se corrige con visto bueno de 4e y se publica tras el banco de f4.

**f4, 30b:**
- Banco C24 del parche por fila: 2 de 2 cazados. Corpus 47/47.
- Medida de las 545 listas con la clave de nivel en la franja: en marcha.
- Criterio de paro:
  - PG2554 primero fuera de la franja en «Crimen y castigo de Dostoyevski» con 1,20;
  - «granja» y «dragones» con 1,20, iguales o solo empates.
- Si cuadra: clave en app/catalogo.py, con prueba y mutante C24-franja-empate-sin-cercania; después, corpus y banco.
- e6 queda avisado de que puede publicar el aria-label antes de ese banco.

**Visto bueno de e6 a 5ee4949:**
- Textos buscados en el bundle publicado c73bbcc; la medida a 390 px es de hoy, sobre el mismo código.
- Puntos 10 y 11 y pasos 3 y 4: bien.
- MENOR opcional para 4e: «1 de 3 · Libros en inglés a tu nivel» son dos textos en pantalla. Se corrige junto con los cambios que traiga el 30b.
- aria-label de Inicio: cambiado por e6 a «Ejemplo: mantener presionada una palabra del libro para ver qué significa en su frase», con aserción en entrar-perfil.spec.ts. Pendiente de pruebas, commit, visto bueno de 4e y publicación.

**Front 72e9525** (e6): publica 9a5fa3d, el aria-label de Inicio, con el ok de 4e.
- Comprobado en lo publicado: texto nuevo una vez, el viejo ausente, sha por la API de HF, meta de la API intacta.
- Build desde un worktree limpio, con 2,89 GB libres tras la medida de f4.
- f4 ya puede lanzar corpus y el banco del 30b.

**30b medido con la clave de nivel** (f4, 545 listas contra el 28, n=24): **sin paro**.
- «Crimen y castigo de Dostoyevski» con 1,20: PG2554 primero fuera de la franja.
- «granja» y «dragones» con 1,20: idénticas.
- Cortes de la franja: siempre igual de cerca del nivel o más («family» B1: 0,44 frente a 0,36; «pintura» B1: 0,78 frente a 0,99).
- Resto: 88 cambios solo en la cola; 18 antes, todos empates a 6 decimales. Marcas y longitudes iguales. Ruido entre procesos descartado (218/218).
- **Criterio corregido antes del commit, por escrito:** el escrito era «ningún top 10 cambia». «mystery» sin perfil intercambia los puestos 7↔8 (PG34933 y PG27722, empatados a 0,857000; en crudo, menos de 1e-6). Queda: el top 10 no cambia de conjunto y solo se admite intercambiar ids empatados a 6 decimales.
  - Motivo: el redondeo es el objetivo del 30b, que el Space y el local ordenen igual.
- Tras el despliegue, e6 repite en el front el paso 3, «granja», «dragones» y «mystery».

**30b, antes del despliegue** (escrito por la Central, pasado a f4):
- Parche en local, corpus 48/48; banco C24 con 3 mutantes en marcha.
- **Criterio de marcha atrás, escrito antes de desplegar.** Se vuelve al 28 (62e5a06) si en el Space:
  - PG2554 deja de ir primero fuera de la franja en el paso 3 con 1,20;
  - «granja» o «dragones» con 1,20 cambian de conjunto o de marcas;
  - alguna lista cambia de marcas o de longitud frente al 28.
- **No se vuelve atrás, se informa,** si el Space y la medida local solo difieren en el orden de empates a 6 decimales.
- Ajuste del punto 3 (f4 propuso contar solo el número de marcas; la Central lo aprieta): ids marcados iguales al 28, con una lista cerrada de 4 excepciones («family» A2 y B1, «Familia» A2, «pintura» B1). En ellas solo se admite una copia del mismo título igual de cerca del nivel o más. Cualquier otra diferencia, o un quinto caso, da código 2 en comprobar_r30b.py. La referencia es r30_28.json (257/257 contra el volcado del Space 28).
- **Corrección de f4:** con la clave de nivel, la lista cerrada tiene **10** listas, no 4:
  - «familia» A2;
  - «escuela» B1;
  - «family» A2 y B1;
  - «friendship» 1,20;
  - «Familia» A2 y B1;
  - «Amigos inseparables» A2 y B1;
  - «Brujas y magia» A2.
  «pintura» B1 ya no cambia. La Central comprobó las 10 distancias al nivel: en todas la copia que entra está igual de cerca o más. En las otras 535 listas, ids marcados y longitud son idénticos al 28.
- Emparejamiento en el guion: por título, distancias ordenadas, elemento a elemento.

**30b, commit 1643c4b** (f4): app/catalogo.py, pruebas_corpus.py y tools/banco_mutantes.py. Banco C24 3/3, corpus 48/48.
- La Central leyó el diff de catalogo.py:
  - sin perfil, orden estable sobre el parecido redondeado;
  - con perfil, la clave redondeada queda como la menos prioritaria en lexsort, así que no altera nombre, relevante ni primero;
  - franja: parecido redondeado, luego |d − nivel|, luego fila;
  - `d` y `nivel` están en ámbito.
- MENOR: el comentario de ejemplo de «family» B1 (0,36 frente a 0,44) no es el caso de la lista cerrada (0,38 → 0,66).
- Pendiente:
  - ok de 4e, árbol limpio y --seco;
  - despliegue y comprobar_r30b.py / marcha_atras_r30b.py;
  - ensayo de e6 en el front: paso 3, granja, dragones, «mystery» y «family» B1.
- **Ok de 4e a 1643c4b.** Árbol limpio en marcha: corpus, luego api y extremas.
- **Criterio de marcha atrás simulado sin red** (marcha_atras_r30b.decidir), 8 casos:
  - no vuelve con el candidato tal cual, con «family» B1 igual al 28 ni con «familia» A2 de 3 por 3;
  - vuelve si «love» B1 marca otro id, si entra una copia más lejos del nivel, si entra un título distinto en «Brujas», si PG2554 queda segundo o si «dragones» da un resultado menos.
  - La primera simulación del caso 4 estaba mal construida, y f4 la repitió.
- **Hueco señalado por la Central:** un conjunto distinto al local con las mismas marcas no se detectaba. comprobar_r30b.py separa ahora tres salidas: idéntico, solo orden (se informa) y conjunto distinto (código propio; no se da por bueno sin mirarlo).
- **Árbol limpio de 1643c4b:** corpus 48/48 y api 66/66; faltan las extremas. comprobar_r30b.py con códigos: 2 vuelve al 28, 3 conjunto distinto al local, 1 solo orden, 0 todo cuadra.
- **Línea base de e6 sobre 282c46f, solo lectura:**
  - «mystery» sin perfil: top 10 idéntico en tres pasadas; PG34933 en el 7.º y PG27722 en el 8.º.
  - «family» con nivel 0,80 por API (`nivel` directo, api.py:981): 36 resultados y 18 marcadas.
  - Predicción del 30b: sale SWV19641 (0,382) y entra LRD5DCD10D6C1764DFD9540DC0B3E15D25C (0,656); el resto de marcadas, igual.
  - Nota: el perfil B1 del cuestionario de e6 da 0,953, no 0,80. Las predicciones de f4 son con 0,80.

**Despliegue 30b:** Space 0319290, con app/catalogo.py de 1643c4b.
- Árbol limpio en D:: corpus 48/48, api 66/66, extremas 351. C24 3/3. Ok de 4e. --seco: solo catalogo.py.
- En marcha: comprobar_r30b.py y la segunda medida del arranque del 30a.
- Ensayo de e6 encargado: family 0,80, mystery, paso 3, granja, dragones y perfil 0,953.
- **Segunda medida del arranque del 30a**, en el arranque del 30b y con el log completo (44 líneas):
  - buscador_listo a los 12 s de RUNNING. La primera medida dio 20 s; antes de la precarga, 55 s.
  - Precarga: catálogo 3,8 s y modelo con primera búsqueda 13,7 s.
  - 0 descargas de MiniLM en el log.
  - Cautela resuelta con dos arranques: el modelo sale de la imagen.
- **Ensayo de e6 sobre 0319290**, con sha confirmado y buscador_listo antes de empezar. Todo según lo previsto:
  - «family» con 0,80: 36 resultados y 18 marcados. La única diferencia es SWV19641 → LRD5DCD… (0,656); orden de los 24 primeros idéntico.
  - «mystery» sin perfil: mismo top 10, con 7↔8 intercambiados (PG27722 y PG34933).
  - Front 72e9525 a 390 px con 1,20:
    - paso 3: *Crime and Punishment* primero en «De otros niveles», a 679 px, sin cambios;
    - granja: 9 libres en «En tu nivel»;
    - dragones: 19 de 20 libres.
  - Perfil 0,953: igual que la línea base (36 resultados, 16 marcados, top 10 idéntico).
- A 4e: sin cifras nuevas en el guion. Hace el MENOR de «1 de 3» con una recompilación.
- Pendiente para dar el 30b por bueno: el código de comprobar_r30b.py.
- Guiones f5849dc (4e): «1 de 3» y el título de la bienvenida por separado, y paso 3 fechado «sobre los reinicios 28 y 30b». PDF de 9 páginas. Una sola recompilación.
- Encargado a e6 el ensayo completo del guion en el front 72e9525 (§15): solo lectura, con copia a 4e.
- Cupo de Codex comprobado con una llamada de una palabra: agotado, vuelve el **19 sep a las 8:56**. Coincide con el día de grabación. Recomendación a Miguel: lanzar la auditoría a las 9:00 y grabar el vídeo el 20, para que dé tiempo a corregir un SERIO.

**Ensayo completo del guion** (e6, f5849dc contra el front 72e9525 y la API 0319290, 390 px táctil, contexto limpio y sin cuenta). §15 cumplido tras las tandas, el aria-label y el 30b.
- **Bien:**
  - motor despierto y búsquedas en caliente de 0,42 a 0,72 s;
  - bienvenida y «Saltar»;
  - perfil 1,20 y paso 1;
  - paso 2 (dragones 19 de 20; detectives, 3 de Gutenberg);
  - ficha de PG2554;
  - lector con un solo aviso;
  - Pronunciar con ayuda visible y /ʌ/;
  - micrófono: sin aviso de WebView en Chrome, estado visible sin tapar;
  - «Entrar» del aviso ámbar;
  - Mis palabras.
- **No coincide, pasado a 4e:**
  - boca 3D: la primera vez tarda 3,6 s por red, no 2,9 s → «unos 3–4 s»;
  - Índice: unas 2 pantallas por debajo de «Empezar a leer», no 2,5.
- **Matiz:** la primera consulta de palabra en frío tarda 5,0 s; el guion ya pide consultar una antes.
- **Sin probar** (hace falta cuenta o micrófono): explicación IA, «Corrígeme», «Practica esta palabra», paso 6 y «Este intento no cuenta». Quedan en la lista de Miguel.
- Guiones 657a640 (4e): boca 3D «unos 3–4 s la primera vez» y el Índice «unas 2 pantallas por debajo de «Empezar a leer»». La Central barrió todo entrega/ (md y tex): no queda «2,9 s», «0,6 s después» ni «2,5 pantallas».

**30b: código 2 por un error de referencia** (f4). En «magic» B1, el Space marca SWV537780 (0,39) y el local SWV522867 (0,73).
- Los dos volcados del Space 28 (74f1484 y 62e5a06) ya marcaban SWV537780, así que frente al 28 real de producción no cambia nada.
- La referencia era r30_28.json (local). Tenía 13 diferencias con el Space 28, «magic» B1 entre ellas. El «257/257» se había informado mal: era Space contra Space.
- **Decisión de la Central: no volver al 28 por este código 2**, porque volver atrás no cambiaría esa lista. El 30b queda sin dar por bueno.
- **Criterio nuevo, escrito antes del resultado:** Space 30b contra el volcado del Space 28, en las 257 listas que tiene.
  - Se vuelve si cambia la longitud o el número de marcas, o si entra una copia más lejos del nivel.
  - Código 3, con ids, si cambian ids marcados fuera de la lista cerrada.
  - Solo se informa si cambia el orden.
  - Las 288 listas sin volcado del 28 se informan frente al candidato local.
- Resto, ya comprobado: 541 listas idénticas al candidato local, 3 solo en orden (cola desde el puesto 24) y 1 con conjunto distinto («magic» B1); paso 3 bien; buscador_listo a los 14 s.
- **Límite declarado del 30b:** el redondeo a 6 no iguala el Space y el local en todas las parejas.
- Skill buscador-encontrar: la referencia de la marcha atrás también es el volcado del Space anterior.
- Guion: e6 da el visto bueno a 657a640 y lo da por cerrado.
- **Space 30b contra el volcado del Space 28**, 257 listas:
  - volver: 0;
  - iguales: 198;
  - solo orden: 58 (53 en la cola; 5 con marcados y longitud iguales). «mystery» sin perfil además intercambia 11↔12 en el Space, cosa que no pasaba en local: otro ejemplo del límite;
  - código 3: 1, «pintura» B1. Sale SWV494921 (0,99, a 0,19 del nivel) y entra SWV661856 (0,775, a 0,025). Mismo título, 36 resultados y 17 marcas. El Space 28 elegía la de 0,99 y el local ya elegía la de 0,78.
- **Decisión de la Central:** «pintura» B1 aceptada como excepción revisada. 30b bueno si en las 5 listas de solo orden el conjunto del top 10 no cambia y PG2554 sigue primero en «Crimen y castigo de Dostoyevski» B1. f4 escribe la fila de DESPLIEGUE con el error de referencia, el 257/257 mal informado y el límite del redondeo.
- **30b dado por bueno** (f4, DESPLIEGUE 9108a52). En las 59 listas que difieren del volcado del 28, el top 10 tiene el mismo conjunto. PG2554 sigue primero en «Crimen y castigo de Dostoyevski» B1, con 4 marcas en los dos. La única lista con marcas que cambia antes del puesto 24 es «piratas» B1 (puesto 19), con los mismos ids y marcados. **30a y 30b cerrados; el Space queda en 0319290.**

**Ronda 4 abierta (Central), a ciegas y solo lectura:**
- e6: documento, estrategia y presentación contra la producción de hoy (0319290 / 72e9525). Cifras viejas, afirmaciones más fuertes de lo medido, límites sin declarar, Esmeralda e Ismael.
- f4: notebook_proyecto (reproducibilidad en Colab sin errores ni warnings; cifras contra el documento).
- MENOR apuntado para después de la entrega: el comentario de 1643c4b en catalogo.py contradice el límite declarado del 30b.
- **Congelación (Central, 15 sep):** buscador (catalogo.py) y cobro (cuentas.py) congelados hasta después del 20; solo se tocan por un SERIO que afecte a la demo o a los usuarios. Los tres menores de 4e (parche_menores_28.py: devoluciones con disco roto, índice apellido→filas, obras sin fechas) quedan para después de la entrega. El de las obras movería la exención de 5 obras y necesitaría medida completa.
- Ronda 4, 4e: enlaces y recursos públicos de todos los entregables (Spaces, repos de HF del modelo y el diccionario, URLs de datos, DOI), solo lectura. Un recurso que el notebook necesita y no es público es SERIO. Informe: ronda4_enlaces_4e_2026-09-15.md.
- Memoria: congelacion-hasta-la-entrega.

**Ronda 4, informe de e6 sobre documentos** (3d63dc3). La Central verificó los 4 SERIOS con las líneas delante:
1. §8.2 (documento.md:1067) y presentacion.tex:367 usan «dostoyevski» con 1,20, justo el límite 15.
2. Cuestionario descrito con diccionario y series (estrategia.md:109) y como «seis preguntas y tres fragmentos» (documento.md:1054). La app tiene 6 pasos: 3 preguntas y 3 fragmentos (nivel.ts:17).
3. «Doble toque» y «Toca una palabra» (documento.md:1057, 1113) frente a «mantén presionada».
4. n = 2 sin Ismael (documento.md:1461, estrategia.md:276).
Menores: arranque sin fecha, 40 ms, silencio sin coste, recuentos de pruebas fechados y frase de Pronunciar. Comprobado y correcto: 0,908 interna; «determinista» solo del fonema; límites con las cifras de hoy; amor B1 como fallo de búsqueda.
Encargado a 4e (tras los enlaces), en un único commit con PDF; revisa e6.

**Ronda 4, informe de f4 sobre el notebook** (530bd3a): 2 SERIOS, 12 menores y 1 duda. 43 celdas ligeras ejecutadas en local sin errores, y las cifras de §4-§7.1 se reproducen.
- S1, verificado: notebook_proyecto.py:2482 dice «sin errores en un Colab limpio | Sí» y la línea 35 dice que no hubo ejecución nueva en Colab. documento.md:1432 lo repite. La ejecución de 1084bdf (13 sep) fue local, en una carpeta vacía.
- S2, verificado: `0,72 × real + 0,38` en las líneas 1813 y 2437 y en la Figura 13. La celda imprime 0,667x + 0,411, que es lo que dice el documento.
- Duda: el filtro global de avisos esconde un PendingDeprecationWarning de seaborn (`vert`).
- **Plan de la Central:**
  1. e6 corrige el notebook: S2, menores, la llamada de seaborn y el filtro estrechado, sin salidas.
  2. f4 revisa y lo ejecuta en Colab gratis (CPU), guardando salidas y fecha real. Si falla, no se tapa.
  3. 4e ajusta después documento.md:1432 con esa fecha.
- **Notebook corregido por e6** (5c4d461, solo el .py y el .ipynb):
  - S2: recta impresa con polyfit, 0,67x + 0,41.
  - D1: filtro global quitado; las cajas con matplotlib (`orientation`/`vert` según versión).
  - Menores de texto y descargas con tiempo de espera, 3 intentos y tamaño mínimo.
  - 103/103 celdas sincronizadas, sin salidas. En local, 57 celdas de código sin error ni avisos con `-W default` (el v4 sustituido).
  - **Riesgo abierto:** §9.3 y la limitación 7 llevan el marcador `<fecha>` hasta que f4 lo ejecute en Colab. Si la ejecución falla, hay que reescribir esas frases antes de la entrega; no pueden quedar con el marcador.

**Ronda 4, informe de enlaces de 4e** (c6d7e8d): ningún enlace roto. CLEAR y el catálogo de Gutenberg responden sin cabeceras; el v4 es público y no gated (sha 0a45209); 59/59 PDF de British Council con el hash del manifiesto (solo desde el navegador, como avisa el cuaderno); front y API en RUNNING; 12 DOI y 25 enlaces web a 200.
- **SERIO:** el repositorio del que se dice que se recalculan cifras no es público (404 sin sesión), y `validar_local.py`, `tools/bajar_corpus_bc.py` y `entrenamiento_v4/` no están en ningún repo público. No bloquea la ejecución del cuaderno.
- **Decisión de la Central:** no se hace público antes de la entrega (la historia puede llevar corpus con derechos y no hay tiempo de revisarla). Se rebaja el texto a «se comparte a petición», como `mensaje_profesor.md:49`, y se deja claro qué sí es público. Si Miguel quiere publicar algo, después del 20 y con revisión.

**Colab (decisión de Miguel, 15 sep):** con rayko800 la CPU gasta unidades del saldo Pro (0,08 por hora), así que f4 paró antes de ejecutar y eliminó el entorno (1,99 unidades intactas). Miguel elige ejecutar en su otra cuenta, miguel.reyes.carrillo19@gmail.com, comprobando «Recursos» antes; si también gasta, no se ejecuta.
- **Notebook, SERIO de enlaces resuelto por e6** (59a367a): las remisiones al repositorio pasan a «no viajan con los entregables y se comparten a petición», con la fórmula de mensaje_profesor.md. Siguen dichos como públicos el v4, CLEAR, el catálogo de Gutenberg y el manifiesto de British Council. No promete que un tercero rehaga el entrenamiento. 103/103 celdas, sin salidas; en local, 57 celdas sin error ni avisos con `-W default`.
- Orden acordado entre sesiones: e6 corrigió antes de que f4 ejecutara, para ejecutar una sola vez.

**Ronda 4, documentos corregidos por 4e** (d232ffd: documento.md y .tex, estrategia.md, presentacion.tex y los dos PDF; documento pasa a 58 páginas):
- S1: §8.2 y la diapositiva usan «Crimen y castigo de Dostoyevski», con las posiciones de hoy y remisión a la limitación 15; fuera «el nombre mal escrito llega igual».
- S2: seis pasos, tres preguntas (frecuencia, libro entero, qué puede contar) y tres fragmentos, citando nivel.ts:17 y perfil.py.
- S3: «mantener presionada (con ratón, doble clic)»; el doble toque queda solo como histórico (estrategia.md:209).
- S4: n = 3 y apartado «El tercer ciclo: Ismael» en documento (1487) y estrategia, con las tres tandas, el arreglo del micrófono (601788b) y su prueba pendiente.
- Menores: arranque fechado, 40 ms aclarado, silencio sin coste con el tope de 10, recuentos 66/351/48 (incluida la fila de Robustez) y la frase de Pronunciar marcada como anterior.
- Repositorio: limitaciones 9, 10 y 11, .tex 532/3041/3234 y estrategia 24-27, con «se comparte a petición».
- Revisión encargada a e6.
- **Menor del front, decisión de la Central: entra antes de la entrega.** bienvenida.ts:77 dice «seis preguntas» y el documento dice tres preguntas y tres fragmentos; e6 lo cambia con el ok de 4e y publica.
- **Revisión de e6 a d232ffd:** los 4 SERIOS y todos los menores resueltos, sin afirmaciones nuevas más fuertes de lo medido, paridad md/tex correcta. Dos restos en la figura del recorrido del .tex, encargados a 4e junto con la fecha del Colab: `documento.tex:2555` («6 preguntas + 3 fragmentos» → 3 + 3) y `documento.tex:2571` («40 ms en local» → en el servidor).
- **Colab:** la cuenta miguel.reyes.carrillo19 no tiene suscripción ni unidades y las GPU de pago salen deshabilitadas. f4 ejecuta el .ipynb de 59a367a en CPU, sin comprar nada y sin pop-ups.
- **Barrido de la Central fuera del front y de entrega/** («seis preguntas», «6 preguntas», «doble toque», «toca dos veces», «toca una palabra»):
  - `README.md:36` desfasado, encargado a 4e;
  - `pruebas_api.py:126` es correcto: `/api/cuestionario` ofrece 6 preguntas y 3 fragmentos, y el front presenta 6 pasos con 3 preguntas y 3 fragmentos (las otras tres son las de «afinar»). El documento debe decir «tres preguntas» solo de la pantalla, no de la API;
  - `estrategia.md:209` y `documento.tex:758` son el histórico del doble toque, correctos.
- **Figura del recorrido:** la etiqueta pasa a «0,7 s en pantalla» (razonamiento de 4e: en esa fila las etiquetas miden lo que espera el lector). Los 40 ms se quedan en el texto con su matiz.
- e6 encontró la misma frase en `encontrar.ts:136` y va en su tanda del front, con barrido de `front/src`.
- **dc447f4** (4e): figura del recorrido con «3 preguntas + 3 fragmentos» y «0,7 s en pantalla», comprobado en el texto extraído del PDF (58 páginas); README.md:36 con «seis pasos: tres preguntas y tres fragmentos» y barrido del README. Los documentos no describen `/api/cuestionario`, así que el matiz de la API no obliga a más cambios. Queda solo el commit pequeño con la fecha del Colab.
- **Tanda del front de e6, detalle aprobado por la Central** (todo texto): bienvenida.ts:77, encontrar.ts:136, inicio.ts:80 y nivel.html:91 pasan a «tres preguntas y tres fragmentos»; inicio.ts:120 pasa de «Toca una palabra» a «Mantén presionada… con ratón, doble clic» (el S3 de los documentos). Dos pruebas fijan los textos nuevos y exigen que no vuelva «seis preguntas». 122/122 y mutante que cae con el texto viejo. En `app/*.py`, cero coincidencias. Pendiente: 390 px (ojo al antetítulo largo de nivel.html), ok de 4e y publicación.

**Notebook ejecutado en Colab** (f4, 68828ff): cuenta gratuita miguel.reyes.carrillo19, CPU, entorno nuevo, sin Drive ni .env y sin pop-ups. **57 de 57 celdas con salidas, 0 errores y 0 salidas por stderr** (ningún aviso, ya sin filtro global). CLEAR 4.724 × 28; catálogo vivo 79.381 / 61.675 frente a la instantánea del 7 sep; v4 cargado del repo público y ordenando los extremos (0,651 y 1,794); British Council 0 de 59, como declara; Figura 13 imprime 0.667 × real + 0.411. Los dos `<fecha>` rellenos con «16 de septiembre de 2026» y `grep -c` a 0. Con esto el SERIO S1 del cuaderno queda cerrado con prueba.
- **Tres cifras de tercera decimal** que el texto y la corrida dan distintas (XGBoost 0,340/1,081 frente a 0.337/1.091; logística 17v 1,061 frente a 1.062; Spearman del bosque 0,686 frente a 0.688). **Decisión de la Central:** manda la corrida que viaja dentro, con el aviso de que la tercera decimal cambia con la versión de las bibliotecas. e6 lo aplica en el cuaderno editando solo celdas de texto y sin perder las salidas; 4e lo comprueba en los documentos.
- **Localización de la Central:** las cifras a corregir están en `documento.md:622`, 623 y 1612 y en `documento.tex:1731`, 1732 y 3300; en la presentación no salen. **Aviso:** los 0,688 de `documento.md:921`/926, `estrategia.md:615` y `documento.tex:2294`/2303 son la correlación parcial descontando la longitud, no el Spearman del Random Forest, y no se tocan.
- **Tanda del front en 940c275** (e6), pendiente del ok de 4e y de publicar. Textos finales: bienvenida «Mide tu nivel con tres preguntas y tres fragmentos, o ve directo a un libro. Nada de esto pide cuenta.»; encontrar «Con tres preguntas y tres fragmentos sé qué libros te quedan cómodos con un poco de reto.»; inicio «Tres preguntas y tres fragmentos, uno por pantalla. Al final ves tu nivel.»; nivel.html «Tres preguntas y tres fragmentos para saber qué libros te van»; inicio «Mantén presionada una palabra —con ratón, doble clic— y ves su pronunciación, la acepción que tiene en esa frase y la gramática.». Medido a 390 px: el antetítulo ocupa dos líneas (154-193) con las cinco opciones en pantalla (última en 621, barra en 777), y la tarjeta «Lees con red» (1805-1934) no desborda. 122/122 y mutante que cae.
- **Método para retocar el cuaderno sin perder las salidas** (e6, aprobado con refuerzos): no se regenera el .ipynb desde el .py; se cambia solo el `source` de las celdas markdown. Añadido por la Central: copia de 68828ff en el scratchpad, comparación por hash del bloque `outputs` y de `execution_count` celda a celda, y un guion que se niega a escribir si la celda no es markdown o el ancla no aparece exactamente una vez.

**Corrección del caso de Ismael (Miguel, 16 sep):** **no había iniciado sesión**, y por eso no tenía esas funciones. Ni el micrófono ni el WebView de WhatsApp eran la causa; esa explicación se escribió antes de medirla, el mismo error que con Esmeralda.
- Sigue en pie, porque está medido: en el front anterior los avisos del micrófono y el «Grabando…» se pintaban debajo de la barra fija (y 750-849 frente a 687) y no se veían. Fallo real, corregido en 601788b, encontrado al investigar su queja.
- Sale de los entregables: que su caso lo causara el WebView de WhatsApp. Sitios: apartado 3.4 de estrategia.md y limitación 13 de documento.md y .tex (d232ffd), encargados a 4e para hoy.
- **Lo que sí es fallo nuestro:** la app no le dijo con claridad que tenía que entrar.
- Encargos: e6 mide qué ve alguien sin sesión al pulsar el micrófono y al consultar una palabra, a 390 px, y propone texto sin implementarlo; f4 mira qué rutas exigen cuenta y qué mensaje devuelven sin credenciales, y si alguna cobra un uso sin devolverlo.
- Informe de la ronda 3 y memoria primeros-usuarios corregidos.
- **Su prueba pendiente ya no es repetir en WhatsApp.**
- **Lado del servidor, medido por f4 sobre 0319290 sin credenciales:** la API queda descartada como causa del caso de Ismael.
  - Solo `/api/voz` y la etapa `completa` de `/api/palabra` exigen cuenta; el resto basta con la cabecera del navegador, y salud, estado, cuestionario y audios no piden nada.
  - `/api/voz` sin perfil da **403** con «Esta parte necesita que entres con tu perfil. El resto de la aplicación… funciona sin entrar.»
  - `/api/palabra` responde 200 con la definición y el aviso; «Mis palabras», repaso y biblioteca dan 200 vacíos; `/api/entrada` dice `puerta:true, dentro:false`.
  - Nada cobra un uso sin devolverlo: `consumir` rechaza sin sumar. `/api/voz` sí lee la grabación antes de comprobar la cuenta, así que se pierde la subida, no cuota.
  - Sin `OPENAI_API_KEY`: 503 con texto claro antes del cobro, y el diccionario sigue respondiendo.
  - **Único texto que una persona no entendería:** el 400 de `X-Lector`. Cambio de código, congelado y el front siempre manda la cabecera: **a la cola de después del 20**, junto con adelantar el 403 de `/api/voz` antes de leer el formulario.
- **c490b11** (4e): limitación 11 con la ejecución del 16 sep (CPU, cuenta gratuita, 57/57 con salida y ningún error, contado por 4e en el .ipynb de 68828ff, no copiado del mensaje); XGBoost 17v a 0,337 y 1,091 y el error ordinal de la logística a 1,062, con pie de cuadro que dice de qué corrida salen y que la tercera decimal se mueve con las bibliotecas; los 0,688 intactos; limitación 13 y apartado 3.4 reescritos, con la causa de Ismael en revisión y la pendiente como «medir qué ve alguien sin sesión». 4e dio el visto bueno a 940c275 antes del recordatorio.
- **Localización del 403** (la Central, porque 4e no lo encontró con la redacción limpia): `_SIN_CODIGO` en `app/cuentas.py:64`, devuelto en `cuentas.py:386` y `:419`, convertido en 403 en `app/api.py:1935`; `_llano` (api.py:126-135) quita el markdown. Regla nueva para los informes: al citar un mensaje que va a un documento, dar archivo y línea de la cadena y decir si es el original o el que ve el usuario.
  - Precisión de f4: `cuentas.py:386` es `consumir`, que produce el 403 de `/api/voz` (api.py:1933-1935); `cuentas.py:419` es `permite`, que se ve **sin** 403 dentro de `/api/palabra`, en `motivo_sin_explicacion` y `avisos` (api.py:1548-1550). La constante es la misma (`cuentas.py:64-67`).

**Front 48d748d** (e6, con el visto bueno de 4e): publica 940c275, los cinco textos del cuestionario y del gesto. Verificado recorriendo el grafo de importaciones desde el index: de los 402 .js del Space solo 14 son alcanzables y en ninguno queda «seis preguntas».
- **76 chunks huérfanos de despliegues viejos sí llevan el texto viejo.** Decisión de la Central: no se limpian antes de la entrega (nadie los carga, y equivocarse al decidir qué es alcanzable rompe la entrega). A la cola de después del 20, con la lista de los 14 como referencia. Riesgo declarado: quien haga grep sobre el Space lo encontrará; la respuesta es que lo alcanzable está limpio.
- Lista de cifras del cuaderno aprobada: se cambian 1455 (0,337 y 1,091), 1453 y 1490 (1,062) y 2523 (0,688, Spearman del bosque); no se tocan 1035 (tabla de la fuga) ni 2160 y 2165 (correlación parcial). Con coma decimal y la salvedad de versiones extendida.

**Respuestas de Miguel (16 sep):**
- **Ismael puede aparecer con su nombre** (es su hermano): lo escrito en c490b11 se queda.
- **Graba el fin de semana del 19-20**, sin día fijo. Codex se lanza el 19 a partir de las 8:56, temprano, para que quepa una corrección antes de grabar; ninguna cifra del guion depende del día.
- **Ha estado probando la app con su cuenta.** Pedido el detalle de la corrección de pronunciación, la explicación de la IA, «Practica esta palabra», el paso 6 y «Este intento no cuenta».
- **Corroboración independiente de 4e sobre 48d748d:** recorrió el grafo desde index.html y llegó a los mismos 14 archivos que e6. Las cinco frases nuevas están servidas y las viejas dan cero («seis preguntas», «Seis preguntas», «6 preguntas», «doble toque», «toca una palabra», «toca dos veces»), con controles positivos para que los ceros signifiquen algo: «preguntas» 13, «fragmentos» 5, «presionada» 4. Con esto, lo que dicen documento, estrategia y presentación es lo que se sirve, y S2 y S3 quedan cerrados en las dos direcciones. 4e coincide en no limpiar los chunks huérfanos antes del 20.

**Arranque para la demo** (f4, informe da49a16, sin reiniciar nada):
- El Space de la API se duerme a las **48 h exactas** sin visitas (`sleep_time` 172.800 s en la API de HF), lo que confirma lo que ya decían documento.md:1473 y el cuadernillo. No se duerme por unas horas.
- Despertar → RUNNING: 26-85 s en diez despliegues (46-72 s los cuatro últimos). RUNNING → `buscador_listo`: 12-14 s desde el 30a. Ya despierto, `/api/salud` en 0,3 s. **Cota en frío: de un minuto a minuto y medio.**
- El front es estático, no se duerme, responde en 0,64 s, y depende de la API para todo lo demás.
- **Hueco declarado:** no se ha medido un despertar real desde la suspensión de 48 h; las cifras son arranques por despliegue. **Decisión de la Central: no se reinicia el Space para medirlo** (hay usuarios con cuenta y el número no cambia ninguna decisión).
- Pasos para «Antes de la demo» encargados a 4e: abrir la víspera, comprobar `buscador_listo` diez minutos antes, esperar hasta minuto y medio sin recargar en bucle, y distinguir siesta de `Error`.

**Vuelco en el caso del micrófono (16 sep).** Miguel manda la nota de voz diciendo «según yo este es de Laura». Transcrita por la Central (whisper-1, scratchpad/laura_nota_16sep.txt): es **la misma grabación** archivada como segunda nota de Ismael, y empieza «te cuenta que entré y **ya me inicié sesión**, pero le falta… le pisas al micrófono pero no te dice que hables, no se activa la grabación».
- Consecuencia: **quien pulsó el micrófono sí había entrado.** Hay dos casos y no se pueden mezclar:
  - **A, con sesión:** entró, pulsó y no se activó la grabación ni le dijo que hablara.
  - **B, sin sesión:** lo que Miguel contó de Ismael, sin cuenta no hay esas funciones.
- La atribución de la nota está en duda (Laura o Ismael) hasta que Miguel lo confirme; no se pone en boca de nadie.
- Encargos: e6 mide el caso A en lo que se puede sin cuenta (borrando `navigator.mediaDevices` en el front 48d748d, permiso denegado, y permiso sin micrófono) además del B, y dice en tres pasos qué debe probar Miguel con su cuenta; 4e no escribe causa y revisa si c490b11 atribuye el micrófono a Ismael.
- Lección, ya en la skill probar-la-app-de-verdad: la causa no se escribe antes de medirla, y **de quién es una nota de voz también se comprueba**.
- **Alcance real del vuelco, que encontró 4e:** la segunda nota lleva dentro **dos** quejas, el micrófono y la saturación de la página, así que si no es de Ismael tampoco es suya la saturación, que es una de las razones escritas para la segunda tanda de ayuda. Y la nota dice «entré y ya inicié sesión», lo que contradice el «no había iniciado sesión» que la Central pasó a los documentos.
- **Decisión de la Central, sin esperar a Miguel** (es la versión correcta en los dos escenarios): en estrategia.md (282, 287-289, 294, 301), documento.tex (851, 856-857, 891, 912, 3186-3188) y documento.md (1493-1495), la primera nota se queda como de Ismael (confirmada por Miguel, con su nombre autorizado), la segunda pasa a «una segunda nota, de uno de los lectores, sin confirmar de quién», se de-atribuyen **las dos** filas y **sale «no había iniciado sesión»** de los entregables.
- **Procedencia, para no perderla:** el «no había iniciado sesión» lo dijo Miguel en su mensaje del 16 sep; queda aquí como suyo y pendiente de confirmar, y no entra en los entregables hasta que se confirme.
- **Confirmado por Miguel (16 sep):** la segunda nota **es de Laura**, y **el micrófono le graba bien a él** con su cuenta en su teléfono. Consecuencias:
  - las dos quejas de esa nota (micrófono y saturación) son de Laura, con su nombre, y la segunda tanda de ayuda se cuelga de la suya;
  - n = 3 se mantiene: Esmeralda, Laura e Ismael;
  - la nota de Ismael es la primera, la de «cuesta entenderle»; lo de que no había iniciado sesión entra como «según Miguel, que habló con él», no medido;
  - **no es un fallo general de la aplicación:** queda como caso de un dispositivo o navegador concreto, con la hipótesis del navegador interno de WhatsApp declarada como hipótesis;
  - sigue en pie lo medido: los avisos se pintaban bajo la barra fija y no se veían (750-849 frente a 687), arreglado en 601788b, que es lo que hacía que ella no viera nada al pulsar.
  - Encargo de e6 recortado: mide el caso sin `mediaDevices` y el de permiso denegado, que es lo que protege a quien reciba el enlace por WhatsApp; el caso sin sesión, en corto. Ya no hacen falta pasos para que Miguel lo pruebe.
- **5fc8302** (4e): los pasos de arranque ya están en los guiones. El punto 8 de «Antes de la demo» sustituye la versión vieja (los 14-46 s), con los cinco pasos; versión corta en la preparación del vídeo con los 0,64 s del front; cifras citadas como arranques por despliegue y dicho expresamente que no se ha medido un despertar desde la suspensión. Además, 4e encontró un resto propio: la línea de la boca 3D citaba `bdfa418` como front publicado y pasa a `940c275` (Space 48d748d), comprobando antes que `boca3d/cara.glb` y `lengua.glb` responden 200.
- **Lección de proceso:** la primera compilación del guion del vídeo falló por una macro inexistente y dejó fuentes nuevas con el PDF viejo. 4e lo vio porque abrió el PDF. Queda en la skill sesion-central §18: un PDF se verifica por su contenido (páginas y una cadena que solo esté en la versión nueva), no por que el guion diga «recompilado».
- **Skill sesion-central §17:** de quién es una queja se confirma igual que la causa; una nota puede llevar varias quejas; lo medido se separa de lo que te contaron; y cuando una sesión pide confirmación antes de escribir, se le da la razón.

**Micrófono, casos A y B medidos** (e6, informe 9d43956, front 48d748d a 390×844, sin atribuir a nadie):
- **Caso A, los cinco finales de pulsar:** el mensaje va dentro de la barra fija y termina en 688 (navegación en 777), así que se lee sin desplazar: sin `mediaDevices` «Este navegador no puede grabar. Abre LiteraLevel en Chrome o Safari.»; permiso denegado; permiso sin contestar («Acepta el permiso del micrófono.», y a los 5 s «¿No ves el permiso? Abre LiteraLevel en Chrome o Safari.»); concedido sin micrófono; y grabando («Grabando: habla ahora · 3 s», contador corriendo). **Hoy no existe el camino «pulso y no pasa nada».**
- **Tres explicaciones para la nota de Laura**, ninguna decidible desde aquí: que sea anterior a 601788b (la que mejor encaja con «no te dice que hables»), que el mensaje saliera y no se leyera como respuesta, o que el fallo esté en `MediaRecorder`, tramo que no se puede provocar.
- **Caso B, sin cuenta:** grabarse, escucharse y el AFI entero funcionan; el aviso ámbar se lee sin desplazar. Solo «Corrígeme» está cerrado.
- **Defecto nuevo y real:** «Corrígeme» va `disabled`, sin `title` ni `aria-describedby`, y pulsarlo no produce respuesta; la explicación está 309 px más arriba. **Aprobado el arreglo**, calcado del patrón del lector: el botón deja de estar apagado y al pulsarlo sin sesión dice «La corrección necesita tu perfil. Grabarte y escucharte, no.» y abre Ajustes en «Tu perfil». Con prueba, mutante, 390 px, visto bueno de 4e y publicación.
- **No comprobado, dicho por e6:** que los audios suenen; esta máquina no reproduce.
- **e3196a7** (4e): versión definitiva en documento (md y tex), estrategia y PDF. La nota es de Laura con su nombre y con sus dos quejas; la segunda tanda de ayuda cuelga de la suya; el apartado pasa a «El tercer ciclo: Ismael, y una segunda nota de Laura»; lo de la sesión va como «según Miguel, que habló con él; no es algo que hayamos medido»; n = 3; el caso del micrófono acotado con las cifras de e6 y la causa como hipótesis fechada. PDF comprobado por contenido: 58 páginas, Laura, el 688 y las tres hipótesis dentro, sin rastro de «sin iniciar sesión».
- **Decisión, propuesta por 4e y aceptada:** «Corrígeme» no se cita en los entregables hasta que esté publicado, ni como pendiente, porque el documento describe lo que la app hace hoy. Y los dos casos no se mezclan en el relato: la nota de Laura es del micrófono, donde sí hay mensaje; el «pulso y no pasa nada» comprobado es el de «Corrígeme», que encontramos al medir.

**«Corrígeme» arreglado** (e6, commit 5e9acc0, Space fce0df6, visto bueno de 4e sobre el commit):
- Sin sesión: «La corrección necesita tu perfil. Grabarte y escucharte, no.»
- **Caso que la Central no había previsto y encontró e6:** `bloqueada()` también es cierta cuando el servidor no tiene clave de OpenAI, y ahí entrar no arregla nada; dice «La corrección no está disponible en este servidor. Grabarte y escucharte, sí.», sin «Entrar».
- 126/126 pruebas y dos mutantes cazados (devolver `bloqueada()` al `[disabled]`, 3 rojas; invertir el guardia, 4).
- Medida real, que corrige lo que la Central había dado por bueno: el aviso ocupa **71 px y hasta cuatro líneas** con su «Entrar», no una línea; sale en 625-696 con `role="alert"`, 90 px por encima de la navegación.
- **Decisión de la Central:** que el panel de Ajustes **no se abra solo**, porque tapaba el aviso y repetía el fallo que se estaba arreglando. El aviso se queda a la vista con su «Entrar» y el panel se abre solo si el usuario lo pulsa. Cambio de una línea, con prueba, mutantes, 390 px y visto bueno de 4e antes de publicar.
- Verificado sobre lo servido: 14 archivos alcanzables, los dos textos en `chunk-CZpwJO52.js`, «seis preguntas» ausente.
- **Cuaderno:** las tres cifras ya escritas (1455 → 0,337 y 1,091; 1453 y 1490 → 1,062; 2523 → 0,688), sin tocar la tabla de la fuga ni la correlación parcial, solo celdas markdown, y con las 57 celdas con salidas y `execution_count` idénticas a la corrida de Colab (68828ff), comprobado celda a celda. Hash pendiente.
- **Verificación de 4e sobre fce0df6** (desde lo servido, entrada main-WCIGOWQ2.js): 14 archivos alcanzables, los dos textos nuevos en `chunk-CZpwJO52.js`, y **la tanda anterior no ha retrocedido** (las cinco frases de 940c275 siguen y las seis redacciones viejas siguen a cero). Lo comprueba en cada publicación porque un despliegue puede deshacer el anterior sin que nadie lo note.
- **Aportación de 4e:** el caso del servidor sin clave merece su línea porque el documento afirma que sin clave la app sigue funcionando en lo que no sale a la red, y en Pronunciar eso era verdad a medias mientras el botón estuviera apagado sin explicarlo. Ahora pantalla y documento dicen lo mismo.
- Skill probar-la-app-de-verdad, dos secciones nuevas: cada publicación se comprueba contra la anterior sobre lo servido, y una afirmación del documento tiene que poder verse en pantalla (con el corolario de que un arreglo no puede reintroducir el fallo que presume de resolver).
- **Cuaderno, cifras escritas** (e6): **6e4db3c** las llevaba, pero al guardar el `.ipynb` se reescribió con otra indentación y el diff salía de 4.684 líneas, imposible de auditar; **26b618d** devuelve el formato original y deja el diff completo en **siete líneas** con los cinco cambios (0,337 y 1,091; 1,062 dos veces; 0,688; y la salvedad de versiones extendida). Las 57 celdas con salidas y `execution_count` idénticas a 68828ff celda a celda, sin ejecutar nada y sin regenerar el .ipynb. f4 revisa 26b618d.
- **Lección, para cuadernos:** un `.ipynb` reescrito con otro formato produce un diff que nadie puede auditar, aunque el contenido esté bien. Si el guardado cambia la indentación, se restaura el formato original antes de pedir revisión; lo que se revisa tiene que poder leerse.
- **Segunda medida del micrófono** (f4, guardada en scratchpad/medida_microfono_fce0df6.md): cayó sobre **fce0df6**, no sobre 48d748d, porque el front se publicó a media medida (Space 48d748d a las 16:22:50; commit 5e9acc0 a las 16:48:28; Space fce0df6 a las 16:54:15). Queda etiquetada como lo que es.
  - **Coincide con e6 cifra por cifra** en los seis finales: los mensajes acaban en 688 con la navegación en 777 y scrollY 0, y ninguno es mudo. El caso con micrófono va simulado con AudioContext y nadie ha oído el audio.
  - **«Corrígeme» en fce0df6:** `disabled` false y contesta con el texto nuevo; no contradice a e6, que midió 48d748d, donde iba `disabled`. Dos revisiones, no dos lecturas.
  - **Prueba de que el panel tapa su propio aviso:** `aside.panel` ocupa de 169 a 844, encima de la barra (617-776) y del aviso (650-690), y `elementFromPoint(195,665)` devuelve el footer del panel. Con eso, la decisión de que el panel no se abra solo deja de ser una opinión.
- **Vocabulario, anotado en la skill desplegar-en-spaces §0:** 48d748d y fce0df6 son **revisiones del Space**, no commits de git, y no resuelven con `git show`. En los informes se dice «revisión del Space» y se cita al lado el commit que la produjo, y cada medida lleva la revisión sobre la que se hizo.
- **Cambio del panel publicado** (e6): **revisión del Space 9b4a3b5, del commit a1c4268**, bundle main-M2PX4KNU.js, con visto bueno de 4e. Medido a 390 px: «Corrígeme» pulsable (704-768); el aviso en 625-696 con `role="alert"`, su «Entrar» dentro, 71 px y hasta cuatro líneas; **`elementFromPoint` en el centro del aviso devuelve el aviso**, no el pie del panel, y `panelAbierto: false` tras pulsar; el panel solo se abre al pulsar «Entrar». Verificado sobre lo servido: 14 alcanzables, los textos en `chunk--rcTzHXR.js`, «seis preguntas» ausente.
- Informe del micrófono de e6 corregido en nomenclatura (e4f6220 el dato real de 71 px y cuatro líneas; 485f721 la distinción revisión/commit).
- Encargos: f4 repite la medida entera sobre 9b4a3b5 y escribe el informe con las tres medidas etiquetadas por revisión (48d748d, fce0df6, 9b4a3b5); 4e cierra el apartado de «Corrígeme» citando la revisión y su commit; e6 repite el ensayo completo del guion sobre 9b4a3b5, incluido el punto 8 nuevo de «Antes de la demo».
- **Cuaderno 26b618d revisado por f4: los cinco puntos cuadran y no hay nada que tocar.** 103 celdas, 57 de código, las 57 con salidas y `execution_count` **idénticos a 68828ff celda a celda**; nada ejecutado y el .ipynb no regenerado (si lo estuviera, no habría salidas); código idéntico; cero ocurrencias de 0,340, 1,081 y 1,061; el único 0,686 que queda es la fila de la tabla de la fuga, que debe quedarse; las cifras nuevas coinciden con lo que imprime su celda; .py y .ipynb sincronizados (57 de código, 46 de texto).
- **Tres correcciones de f4 a lo que la Central había dado por bueno:**
  1. **La huella 4ee9324220fff845 no se puede reproducir** (tres métodos de serialización dan tres valores distintos), así que **no se cita como prueba**; la igualdad celda a celda es más fuerte y sí es verificable.
  2. **Comparar por número de línea es una trampa:** la salvedad de versiones añade una línea y corrió dos pasajes intactos (ahora 2161 y 2166), que por número parecían cambiados. Se compara por contenido. El «conserva 0,688» ya estaba en 68828ff.
  3. **El recuento «siete líneas» era de un archivo, no del acumulado:** 68828ff→26b618d son 11 líneas en el .py y 13 en el .ipynb. Los cinco cambios descritos sí son los que hay. Además, 26b618d toca solo el .ipynb; las cinco líneas del .py vienen de 6e4db3c.
- Las tres van a la skill sesion-central §18: una prueba que se cita tiene que ser reproducible, se compara por contenido y los recuentos se dan con exactitud o no se dan.
- **Medida independiente de f4 sobre 9b4a3b5** (informe ec1ae2c): confirma los cuatro puntos de e6. «Corrígeme» pulsable (704-768, `disabled` false); aviso en 625-696, rect [16,625,358,71], `role="alert"`, 3,65 líneas de 19,44 px; 81 px por encima de la navegación; **`elementFromPoint(195,661)` devuelve el aviso**, justo al revés que en fce0df6, donde daba el pie del panel; `panelAbierto` false tras pulsar, y el panel solo abre al pulsar «Entrar», con el aviso todavía en pantalla. Los seis finales del micrófono, idénticos en las tres revisiones. Paquete leído de la propia página: main-M2PX4KNU.js. Sin sesión de verdad: en localStorage solo preferencias.
- **Método que queda en la skill probar-la-app-de-verdad:** una acción por pasada. f4 midió `panelAbierto` y el «Entrar» en pasadas separadas porque, pulsando los dos en el mismo guion, un panel abierto al final no se puede atribuir a ninguno. Y la promesa que no resuelve, usada para forzar el texto de los 5 s, se suelta al acabar para no dejar el botón bloqueado.
- **Huecos declarados por f4:** 48d748d lo midió e6, no él (se republicó mientras preparaba la pestaña); el micrófono concedido va simulado con AudioContext y nadie ha oído el audio; «Corrígeme» **con** sesión sigue sin probar, y eso es de la prueba de Miguel.
- Encargado a f4: revisar el commit de cierre de 4e cuando llegue, cifra por cifra contra sus medidas.
- **Prueba de validez de la medida de f4**, que se debía a sí mismo: la trampa conocida era que, si la sesión no carga, `entrada()` queda nula, `bloqueada()` sale falsa y el camino medido no se ejecuta. No falseó `/api/inicio`; lo demuestra al revés: el aviso «La corrección necesita tu perfil…» lo escribe el `return` temprano de `corregir()`, que **solo** se alcanza si `bloqueada()` es verdadera; con `entrada()` nula habría salido la respuesta del servidor. Y el sin-sesión queda probado por lo que hay: «Entrar» presente y en `localStorage` solo preferencias, con `literalevel.lector` como identificador de navegador para `X-Lector`, que no es una sesión.
- Queda en la skill probar-la-app-de-verdad: antes de dar por buena la medida de un caso «sin algo», hay que poder decir **qué se habría visto si el caso no se hubiera dado**.
- f4 contrastará el commit de cierre de 4e contra sus cifras (704-768, 625-696, 71 px, `role="alert"`, «Entrar» dentro en [212,650,74,40], 81 px sobre la navegación, `elementFromPoint` devolviendo el aviso) y contra la tabla revisión↔commit: 48d748d/940c275, fce0df6/5e9acc0, 9b4a3b5/a1c4268.

**Ensayo completo sobre 9b4a3b5** (e6, informe e52c823; motor 0319290, RUNNING; 390×844, sin cuenta, perfil 1,20 obtenido contestando el cuestionario):
- **Bien:** `/api/salud` con `buscador_listo: true` y `gcTimeout: 172800`; `/api/estado` con 68.546 libros (53.179 + 15.367); bienvenida y «Saltar» comprobados por geometría; las dos ayudas literales; **la receta del 1,20 verificada entera** («1,20 de 2 · Intermedio, entre 0,95 y 1,45»); paso 2 con 20 tarjetas y 19 libres en dragones y 3 de Gutenberg en detectives; paso 3 con el libro a 679 px y la ficha C1 · 1,70; paso 4 con el Índice a 2,04 pantallas; paso 7 con *poverty* y «Repasa cinco».
- **No coincide:**
  - **A (riesgo en directo):** en *Pronunciar* sin libro empezado, «Una frase de mi libro» **no existe**; aparece tras abrir un libro (412-452). A 4e: el paso 5 dice que se llega después del lector o da la alternativa de escribir la frase, y una línea en «Antes de la demo».
  - **B:** «Antes de conectarse» manda a `/api/estado` y el punto 8 a `/api/salud`; solo `/api/salud` trae `buscador_listo`. A 4e: decir para qué sirve cada una.
  - **C (de la app):** «1 palabras distintas» en *Mis palabras*, que sale en el paso 7. **Decisión: entra antes de la entrega**; e6 arregla singular/plural ahí y en los demás contadores del mismo patrón, con prueba, mutante, 390 px, visto bueno de 4e y publicación.
  - **D:** el paso 1 dice «Unas preguntas y tres fragmentos» y la pantalla dice «Tres preguntas y tres fragmentos». A 4e.
- **Sin medir, declarado:** pasos 5 y 6 con cuenta y micrófono, boca 3D y el cronómetro.
- e6 aclara el origen del «siete líneas»: citó la columna de añadidas de `git diff --numstat`. Y no volverá a citar la huella.

**Cierre de documentos y guiones** (4e, dos commits separados a propósito):
- **0728ffd** (documento md y tex, estrategia, PDF): el apartado cuenta que una queja de usuaria llevó a medir la pantalla y de ahí salió **un fallo distinto del que ella describía**, el único «pulso y no pasa nada» comprobado, con las cifras de f4 (botón 704-768, aviso 625-696, 71 px y hasta cuatro líneas, ochenta por encima de la navegación, `elementFromPoint` devolviendo el aviso, el panel solo al pulsar «Entrar»), publicado en la revisión 9b4a3b5 del commit a1c4268, verificado por 4e desde lo servido. Limitación 14: el caso del servidor sin clave, con su texto y sin ofrecer entrar.
- **acd1ff9** (guiones y PDF del vídeo): los tres cambios del ensayo, A, B y D.
- **Inventario de referencias:** siete revisiones del Space citadas en los entregables (0319290, 7c09d90, 2bb1276, 384a206, e56cf08, ec957d0, 48d748d) y **las siete siguen existiendo** en Hugging Face. Emparejadas: 0319290←1643c4b, 384a206←ef1138c, 2bb1276←0ba8219, ec957d0←4e6276e, 48d748d←940c275, 9b4a3b5←a1c4268. Dos abiertas para f4: si 7c09d90 debe citar 04fced0 (el cambio) o ab4e36f (desde donde se subió), y si alguien tiene apuntado el commit de e56cf08, que hoy dice «su commit no quedó anotado». Cinco supuestas referencias del barrido eran fragmentos de DOI.
- **Defecto de imprenta encontrado al comprobar el PDF:** `\cod{role="alert"}` se imprimía «role=.alert"», con la comilla de apertura rota, único caso en todos los tex y **sin que fallara la compilación**. Se reescribió la frase sin comillas. Queda en la skill sesion-central §18: leer **cómo** salió impreso, no solo que esté.
- **Veredicto de f4 sobre 0728ffd y acd1ff9: los dos cuadran.** Cifra por cifra contra su medida de 9b4a3b5 (704-768; 625-696; `role` en `alert`; 71 px; hasta cuatro líneas, él midió 3,65; ochenta bien redondeado desde 81; `elementFromPoint` devolviendo el aviso; el panel solo con «Entrar»). Comprobó que los diez commits citados existen. B confirmado por código: `buscador_listo` solo en `/api/salud` (api.py:751) y el recuento en `/api/estado`.
- **Respuesta a la pregunta de `7c09d90`:** se queda «subida desde ab4e36f». El Space sirve ese árbol; el commit del cambio (04fced0) ya está en la otra columna.
- **Respuesta a la de `e56cf08`, y era un hallazgo:** sus commits **sí estaban anotados**, en `auditoria/despliegue_codex_2026-09-13_noche.md:21-23`. No sale de un commit sino de una **subida selectiva** de `app/api.py` y `app/voz.py` desde **a87caa8** y **71e4b52**, anterior a que el script exigiera commit (las guardas llegaron en 7e68a54 y 0aec4ee, minutos después). Por eso nadie lo encontraba: la pregunta «¿desde qué commit?» no tenía una sola respuesta por construcción. Nueva redacción a 4e para documento.md:1303, documento.tex:1081 y estrategia.md:466. Aviso: `e3a79cb` también es revisión del Space.
- **Decisión de la Central sobre el recuento:** en los entregables, «cinco finales (el del permiso pendiente, en dos momentos)»; en el informe de f4, los seis con la equivalencia al lado. Así Codex ve dos recuentos y su explicación, no una contradicción.
- **Concordancia que sí puede verse en la demo:** `app/catalogo.py:962`, «Se descartaron {flojos} resultados por parecido bajo.», que `/api/buscar` devuelve en el campo «aviso» (api.py:998), y buscar es el paso 3. **Encargado a f4 medir en qué consultas del guion aparece y con qué número.** Si en alguna de la demo sale con 1, se arregla aunque `app/` esté congelado; si no, a la cola de después del 20.
- **Barrido de concordancias del servidor** (f4, solo lectura). Contexto: ya hubo una primera tanda de plurales (0e270f9 y cb799bc, 14 y 15 sep); esto es lo que se le escapó.
  - **Se ve en la demo:** `app/catalogo.py:962` («Se descartaron 1 resultados por parecido bajo.»), que `/api/buscar` devuelve en «aviso» (api.py:998). **Pendiente de la medida** de en qué consultas del guion aparece y con qué número; eso decide si entra con `app/` congelado.
  - **Por la API, fuera del guion:** `api.py:563` («Este libro tiene 1 capítulos; el 2 no existe.», de la misma familia que el fallo de la ficha de un capítulo que vio Miguel) y `cuentas.py:403`/`:423` («cupo de 1 usos», condicionado a que exista una cuenta con tope 1, que no se comprueba por la norma de no abrir el archivo de códigos).
  - **Solo Gradio:** ui.py 693, 1233, 2140, 2432 y 2883.
  - **Mirados y descartados**, para no repetir el trabajo: api.py 366, 1095, 1525 y scoring.py 392 (constantes > 1); api.py:1311 (no alcanzable con la configuración que se entrega); ui.py:3304 (ya guardado); ficha.py:114 (contenido por `ui._reloj_llano`, y el front va por api.py:731); `app/voz.py`, nada, barrido con patrón más suelto.
  - **Modelo que ya existe en el código:** `app/ui.py:2573`, con `{'capítulo' if c.capitulos == 1 else 'capítulos'}`.
  - **Mensajes que una persona no entendería:** api.py:1311 («se están midiendo 4 libros», que el lector entiende como suyos) y ui.py:2140 («3 bloques · confianza 0.8», jerga).
  - Todo a la cola de después del 20 salvo el del paso 3, pendiente de medida.
- **Plurales arreglados y publicados** (e6): **revisión del Space f4920fa, del commit a656c2e**, bundle main-Y7D6Z2TO.js, con visto bueno de 4e. **Cuatro sitios, no uno:** `palabras.ts:57` («1 palabra distinta»), `palabras.ts:58` («1 consulta»), `ajustes.ts:90` («**Te queda 1 uso.**», con el verbo, y es el que se ve en la demo porque es el cupo del perfil) y `nivel.html:145`. Descartados con motivo escrito, incluidos «capítulo 1 de 1» y «N lectores» (el `@if (descargas > 999)` impide que pinte «1 lectores»). Inventario con veredicto por sitio en ebf5ea2.
  - **Forma:** no se añadió un ayudante `plural(n, …)` porque el repositorio ya resuelve esto con ternario en cinco sitios y mezclar dos estilos a cuatro días de la entrega es más diff que el fallo. Si se unifica, después del 20.
  - 132/132 pruebas con seis casos nuevos, cada contador en singular y en plural con aserciones negativas; dos mutantes cazados, cada uno tumbando solo su prueba. Medido a 390 px: «1 palabra distinta · 1 consulta · 1 libro» y «Te queda 1 uso.». Verificado sobre lo servido, con la tanda anterior sin retroceder.
  - **Dos cosas que e6 cuenta sin que se le pregunten:** su primera aserción estaba mal escrita (pedía «1 consulta» con espacio cuando son dos nodos separados por CSS) y la corrigió emparejando cifra y sustantivo al leer el DOM, con lo que además queda fijado que el número no se despareja; y al falsear la API supuso `/voz/debiles` cuando la pantalla pide `/api/voz/falladas`, así que esa lista no la dio por medida.
- **Cola de después de la entrega pasada al repositorio:** `auditoria/cola_tras_la_entrega_2026-09-16.md`. Vivía en el scratchpad de f4 y habría desaparecido con la sesión.
- **Medida del aviso del paso 3** (f4, contra el Space 0319290): **no aparece en ninguna consulta del guion, ni en ninguna.** Diez consultas del guion con 1,20 y sin perfil, más un **control positivo** de seis consultas hechas para forzarlo (galimatías y temas lejanos) con y sin perfil y con n = 1, 5, 24 y 30: 58 consultas en vivo, aviso vacío en todas.
  - **El motivo, en el código:** `flojos` solo cuenta las filas flojas que salen **antes** de llenar `n` (`catalogo.py:938-950`, con `break` al llegar a `n`); `minimo_similitud` vale 0.10 (`catalogo.py:830`) y no lo cambia ningún llamador (`api.py:993`, `ui.py:1324`, `api.py:2222`) ni ninguna variable de entorno; con 68.546 vectores el coseno no baja de ahí. **`catalogo.py:961-962` es código inalcanzable con la configuración que se entrega.**
  - **Decisión: no entra antes de la entrega, va a la cola**, y lo primero al retomarlo es decidir si esa rama debe seguir existiendo.
  - **Dos huecos de prueba, añadidos a la cola:** `pruebas_extremas.py:5743` fabrica la cadena en vez de ejecutar la línea que la produce, así que la suite nunca iba a cazar el plural; y el gancho del mutante ya existe en `tools/banco_mutantes.py:963-964`.
  - **Corrección de f4 a algo que había contado antes:** los 30 y 36 resultados con n=24 no eran error de medida, es `_marcar_franja` (`catalogo.py:976`) añadiendo detrás hasta K_FRANJA=12 textos de la franja del lector, solo con perfil y después del bucle; no afecta a `flojos`, ya contado.
  - Queda en la skill probar-la-app-de-verdad: **un cero solo vale si la medida puede ver un uno**, y desconfía de una prueba que fabrica la cadena que debería producir el código.
- **Corrección de f4 a la Central:** cuando escribí «bien borrada tu copia del scratchpad», f4 solo lo había anunciado. Ya está borrada de verdad, comprobado después, y la del repositorio (6.915 bytes) es la única lista. Es el mismo error que registrar una vuelta atrás como hecha antes de que estuviera autorizada: **no se da por hecho un anuncio.** Queda en la skill sesion-central §18.
  - f4 borró tarde a propósito, para comprobar antes que la copia del repositorio tenía lo suyo, porque borrar es lo único de hoy que no se deshace. Al comprobarlo le dieron cero menciones de `ui.py:693`, `1233`, `2432` y `2883`: falso negativo, porque la tabla los escribe juntos en una línea. Añadido también a la skill.
  - Lo suyo de hoy son ec1ae2c (informe del micrófono) y 8f33610 (la equivalencia de los cinco y los seis finales). Lo demás modificado en el árbol es de otras sesiones y no lo ha tocado.
- **bfb0ab3 y ab8537b** (4e). Las tres correcciones aplicadas, con dos decisiones de criterio que la Central aprueba:
  - **No se puso `f4920fa` donde el documento dice «comprobado en lo publicado»** sin precisar: esas medidas las hicieron e6 y f4 sobre **9b4a3b5**, y nombrar la revisión más nueva habría movido una medida a una revisión donde nadie la hizo. Las medidas van con 9b4a3b5/a1c4268; `f4920fa`/`a656c2e` solo donde se habla del front publicado hoy.
  - **La salvedad «cinco finales (el del permiso pendiente, en dos momentos)» va una vez por archivo**, en la primera mención, no repetida.
  - El guion del vídeo llamaba «el front publicado» a 940c275 (Space 48d748d), igual que el fallo anterior con `bdfa418`; además de cambiar el par, 4e comprobó lo que la frase afirma: `boca3d/cara.glb` y `lengua.glb` responden 200 en la revisión nueva.
  - Ningún entregable cita «Te quedan N usos», así que el singular nuevo no obliga a tocar nada; y `e3a79cb` no aparece en ningún entregable.
  - PDF comprobados por contenido: guion_video 9 páginas con el par nuevo; documento 60 páginas con 9b4a3b5/a1c4268 y **sin** `f4920fa`, que ahí sería falso.
  - **4e dice por qué no encontró antes el commit de `e56cf08`:** buscó el término pero pidiendo «commit|desde|subido» en la misma línea, y en ese informe los commits van aparte. El dato estaba; falló la búsqueda, no el registro. Es el mismo falso negativo que le pasó a f4 con la tabla de `ui.py`.
  - Encargada a f4 la revisión de los dos commits.
- **El aviso inalcanzable no aparece en ningún entregable** (comprobado por 4e con control positivo antes de reportar el cero: «parecido» sale 3 veces en documento, 3 en el tex y 3 en la estrategia, y el lexema «descart» tiene apariciones de otras cosas, así que la búsqueda veía los archivos). No lo cita el documento, la estrategia, la presentación, los tres guiones, el mensaje al profesor ni el cuadernillo. **Nada que corregir.**
  - Detalle que importa: la fila de la cola decía «se ve en el paso 3 de la demo», el paso que 4e acababa de reescribir. Si se hubiera dado la creencia por buena, el guion describiría hoy una pantalla que nadie puede ver. No entró porque se midió antes de escribirla.
- **Generalización de 4e, aceptada y escrita en la skill probar-la-app-de-verdad («La prueba que se cree a sí misma»):** la cadena fabricada en `pruebas_extremas.py:5743` y el `'1 consulta'` con el espacio que ponía el CSS son el mismo fallo. La pregunta que los separa: ¿de dónde sale el texto que estoy comparando? Si sale de la prueba, no prueba nada. 4e repasará con esa lupa al abrir sus tres menores; apuntado en la cola.

**Cronómetro de la demo** (e6, informe 09e274d, revisión f4920fa con el motor 0319290 caliente, 390 px, sin cuenta):
- **La máquina no es el problema: 5 s en toda la demo.** Paso 2: 0,90 s y 0,47 s. Paso 3: 0,57 s + 1,19 s con la curva. Paso 4: 0,13 s + 1,02 s. Paso 7: 0,18 s. Primer pintado del front, 256 ms; el cuestionario entero, 1,79 s.
- **Corrección de una creencia nuestra:** la primera consulta de palabra **tarda 1,0 s, no 5**. La espera larga de la demo es **la explicación en contexto**, que pide cuenta y sigue sin medirse.
- **Habla estimada** (declarada como estimación, no medida): 423 palabras a 145 p/m son 175 s; a 130 p/m suben a 195 s. Los pasos 5 y 6 son 33 s de eso.
- **Presupuesto:** ocupado ≈ 182 s (3:02). Dentro de 5:00 quedan 1:58 para los pasos 5 y 6; dentro del 4:00 que fija el guion quedan **58 s**, y el guion les asigna 60. **Cabe, pero justo.**
- **El número que decide:** cuánto tarda «Corrígeme», que se hace dos veces y nadie ha medido. Si pasa de unos 8 s, los pasos 5 y 6 no caben en 4:00.
- **Recortes por orden, a 4e para el guion:** segunda búsqueda del paso 2 (~15 s), segunda palabra del paso 4 (~10 s), y el paso 6 entero (~35 s) si «Corrígeme» va lento. No se recortan la curva del paso 3 ni la consulta del paso 4.
- **Tres medidas que e6 tiró y dejó escritas para que nadie las repita:** «la curva tarda 0 ms» (su selector cazaba un icono), «el capítulo carga en 6 ms» (su condición ya la cumplía el índice de la ficha, y por eso la consulta siguiente no encontraba la palabra) y «la bienvenida tarda 34,8 s» (medía cuándo llegó su propio guion). Hallazgo de paso: el cuestionario avanza solo en los seis pasos, sin tocar «Siguiente».

**Miguel prueba la app con su cuenta (16 sep).** Detalle en `auditoria/feedback_usuarios_2026-09-14.md`. Seis cosas, repartidas en el momento:
- **Límite por hora, lo urgente:** «Has llegado al límite de consultas de esta hora… unos 49 minutos». Él creía su cuenta de acceso libre. A f4, solo lectura primero: qué límite es y de dónde sale, qué cuenta y tope tiene (sin abrir el archivo de códigos), qué lo consume, y opciones para que no salte en la demo con su coste. **Es SERIO de demo, así que la congelación se levanta si hace falta, pero decide la Central.**
- **Scroll en Pronunciar** y sensación de perderse: a e6, medir y proponer dos opciones.
- **Introducción guiada con paso 0 de cuenta**, e interfaz final limpia y sin mucho texto: a 4e, propuesta mínima y completa, sin programar. Tercera persona que pide lo mismo.
- **La corrección no señaló el acento de «assessors»:** a f4, mirar si el análisis detecta acento tónico o solo sonidos; si no, es límite a declarar, porque la pantalla promete «te digo qué sonido corregir».
- **Boca 3D cortada y descentrada** en su móvil, y sale en la demo: a e6, reproducir a 390 px y arreglo mínimo sin tocar el `.glb`.
- **Blender más fino:** él mismo lo deja para después de la entrega; a la cola.
- **Lo bueno:** su prueba confirma que el camino con cuenta funciona de punta a punta (graba, pide corrección y acumula palabras difíciles), que era el hueco que faltaba.
- **Decisión sobre ab8537b:** adelante con la opción (a) de f4, volver a 48d748d/940c275 en `documento.tex:929` y `estrategia.md:308`, porque la frase cita el informe que midió esa revisión y dice «entonces». Encargado a 4e con recompilación.
- **904f31e** (4e): aplicada la opción (a), vuelta a **48d748d / 940c275** en `documento.tex:929` y `estrategia.md:308`. **4e reconoce que el error era suyo:** al fechar la frase la emparejó con `9b4a3b5`, pero e6 midió esos cinco finales sobre `48d748d` (su informe 9d43956 lo dice), así que juntó una afirmación con una prueba que no la cubría, **y ocurrió al aplicar el repaso de referencias**. Lección: la regla no basta; hay que comprobar que la prueba citada cubre la revisión que se nombra. PDF recompilado y comprobado, 60 páginas con el par correcto.
- **ec01ce6** (4e): los relojes del guion con el cronómetro de e6. La primera consulta léxica pasa a **1,0 s** fechada sobre f4920fa/a656c2e; los 3,8 s del 15 y los 55 s del 11 se quedan **como historia**, porque explican por qué bajó; **fuera el consejo de calentar consultando una palabra** y se queda el del buscador, que sí está medido (0,90 s y 0,47 s); el cronómetro dice qué reloj está medido y qué es estimación (145 ppm, con la sensibilidad a 130: 175 → 195 s); **punto 12 nuevo** con los recortes por orden y lo que no se recorta.
- **Tres cosas que 4e decidió no tocar, y la Central aprueba:** los «hasta unos 55 segundos» del vídeo son el presupuesto de todas las esperas, incluida la explicación en contexto que nadie ha medido; las 150/130 ppm del vídeo son suyas y no se mezclan con las 145 de la demo; y el único «3,8» que queda es el de la historia, comprobado en contexto.
- Orden: f4 revisa esos dos commits **después** del límite por hora, que es SERIO de demo.

**Introducción al abrir la app** (propuesta de 4e, informe d11057a; decisiones de la Central):
- **Entra antes del 20 solo el paso 0**, dentro de la bienvenida existente: «¿Ya tienes cuenta?» con «Entrar» y «Seguir sin cuenta» del mismo tamaño, «Saltar» intacto, «Entrar» al destino de hoy, y el texto diciendo lo que **sí** se puede sin cuenta (32 palabras). **No invalida el cronómetro ni el ensayo**, porque las dos medidas empiezan con la bienvenida saltada. Lo programa e6 después de la boca 3D y del scroll.
- **Coste real, no cero:** tres líneas de guion que describen la tarjeta de tres pasos (`guion_demo_en_vivo.md:140`, `guion_video.md:99`, `guion_video.tex:265`); las hace 4e **cuando e6 publique**, no antes.
- **«Cómo funciona» de Inicio:** no se toca ahora y, cuando se toque, **se pliega, no se quita**. A la cola.
- **Sí a que la introducción salga también la primera vez que alguien entra con cuenta**, una vez y con «Saltar»; y **español de México**.
- **Corrección de 4e que cambia lo que «menos texto» compra:** quitar «Cómo funciona» **no baja** las 27 palabras de antes de la primera acción, porque va **debajo** de «Empezar a leer»; lo que acorta es la página (76 palabras de sus 3,2 pantallas). Las 27 solo bajan acortando la entradilla. En *Encontrar* sí coinciden: el subtítulo pasa de 25 palabras a unas 6.
- **Dos cosas desaconsejadas por 4e y aceptadas como decisión:** ni tour encadenado de globos (e6 midió que los fallos de Ismael pasaban **dentro** de cada pantalla, no al llegar) ni pop-ups que tapen contenido, que es el mismo fallo del panel de *Ajustes* que se acaba de arreglar.
- **La versión completa (recortes de texto fijo) queda para después del 20:** mueve Inicio y *Encontrar*, que son los pasos 1 y 2 de la demo, invalida las medidas de píxeles y obliga a recronometrar.

**Los dos casos de Miguel, medidos** (e6, informe 5c21026, revisión f4920fa a 390 px, con captura del elemento en `auditoria/capturas/boca3d_390_f4920fa.png`):
- **Boca 3D. Descartadas las cuatro sospechas del encargo:** el lienzo mide 290×420 y cabe entero (248-668); el búfer es 580×840 y `redimensionar()` recalcula el aspecto; el dibujo está centrado (desviación < 1 %); los dos `.glb` cargan (3,17 s y 2,99 s). **Lo que pasa:** el contenido es apaisado y el hueco vertical (proporción 0,69), así que el perfil **toca el borde izquierdo por los labios** y sobra banda arriba y abajo. El corte de la nuca y el plano del cuello son del `.glb` (media cabeza seccionada): eso es Blender.
  - **Arreglo aprobado, mínimo:** punto de mira de `x = 0,1` a `x ≈ 0,9` y distancia de 14,5 a 16-17,5 en `escena.ts`, **con los valores que el propio código ya usa** para «cabeza entera». La buena, después del 20: encuadrar por la caja envolvente con margen del 5 %. Los botones siguen en su sitio y sin solaparse (636-684 y 692-740).
- **La frase de Pronunciar:** el desplazamiento es **dentro del cuadro**, no de la página. El cuadro tiene 112 px fijos y seis líneas: con la frase del guion (31 caracteres) cabe entera, con una oración de libro se ocultan 5 líneas y con una larga 8. Al pulsar, la vista no se mueve, la barra de grabación crece a 159 px y tapa los últimos 29 px del bloque, y **227 de 844 px son barras fijas mientras se graba**.
  - **Arreglo aprobado, mínimo:** mientras se graba, mostrar la frase **entera** en vez de un campo con desplazamiento, y llevar la vista a ella. Con 180 caracteres pasa de 112 a ~200 px y sigue cabiendo. La buena, después del 20: una vista de grabación sin el AFI ni el aviso de OpenAI ni el paso 1, que es lo que provoca el «con tanta información me pierdo».
  - Las dos van **en una sola tanda**, con prueba, mutante donde se pueda, captura antes y después, visto bueno de 4e y el par revisión + commit. Después, el paso 0.
- **e6 declara seis medidas falsas** que tuvo que tirar, escritas una a una (un selector `svg path` que cazaba iconos, una captura recortada con la página desplazada 1.411 px, separar modelo y fondo por saturación con fondo beige…). Lo que sostiene sus conclusiones es el DOM y una captura del elemento.
- **Sospecha seria, encargada a f4 detrás del límite:** `tools/probar_boca_integrada.mjs` garantiza el encuadre con `assert.equal(px.borde, 0)` leyendo el canvas con `getImageData`, y en el navegador ese canvas **se lee vacío** porque WebGL no conserva el búfer. Si en Playwright pasa igual, es la **tercera prueba del día que se cree a sí misma**, y justo la que debía cazar este fallo.
- **f3f530e** (4e): el informe de la introducción deja de ser propuesta. Sección 0 con las cinco decisiones de la Central; la sección 6 pasa de «lo que no recomiendo» a **descartado por decisión** (tour de globos y pop-ups que tapen contenido), **con los motivos escritos a propósito** para que quien lo vuelva a proponer discuta el motivo y no la conclusión; la sección 7 solo dice quién hace qué. 4e comprobó además la costura del cambio de encabezado, que es donde se cuela un texto huérfano.
- 4e espera a que e6 publique para las tres líneas del guion: **un guion que describe una pantalla que todavía no existe es igual de falso que uno que describe una que ya cambió** (su propio fallo con `bdfa418`).
- Encargado a 4e mientras espera: repasar `entrega/mensaje_profesor.md`, que es lo primero que lee el profesor y no había pasado por la ronda 4, incluida una frase sobre el **límite por hora** pendiente de los números de f4.
- **Respuestas de Miguel (16 sep):** de «assessors» **sí hubo corrección**, y además le salió un aviso de que algo «no se detectó» y por eso no podía decirle cómo; esperaba que distinguiera pronunciación de **entonación**. A f4: localizar archivo, línea, texto literal y condición de ese aviso, y si el análisis mira acento o entonación; prioridad detrás del límite por hora y delante de la prueba de la boca. **Hasta tenerlo, no se escribe nada de eso en los entregables.** Confirma también el arreglo del encuadre y del scroll, y **autoriza la introducción guiada ahora**, porque en la demo puede recorrerla antes o pulsar «Saltar»; eso despeja el riesgo que frenaba la decisión. A 4e: que el guion recoja las dos formas.
- **Límite por hora, acotado con dos capturas de Miguel:** 11:32 → «unos 49 minutos»; 11:51 → «unos 30 minutos». Ventana de **una hora**, liberación cerca de las 12:21. A f4, con los números: cómo se calcula el «vuelve en N minutos» y si es tiempo real o redondeo. **Y un hallazgo de la captura nueva: el aviso sale después de grabar** (0:09 ya grabados) y tapando la parte baja, así que el usuario se enfrenta al límite cuando ya ha hecho el trabajo; avisar **antes** de grabar sería mejor, y se decide según lo que cueste. La captura confirma también el problema del cuadro de la frase con una oración larga de libro.
- **Pregunta de Miguel sobre abrir más chats y asignar modelos por tarea.** Respuesta de la Central, con la tarde medida: **no antes del 20**. El cuello de botella no era falta de manos (con tres sesiones hubo ratos con dos esperando a la tercera), y cada chat nuevo cuesta cargar el proyecto más el tráfico con la central. El gasto real del día fue cuatro publicaciones del front en vez de dos tandas, medidas repetidas por culpa de la Central (pedir una medida y publicar el front a media medida), dos sesiones comprobando lo mismo sin ser afirmación de entregable, e informes citados enteros en los mensajes en vez de por hash. Modelos baratos solo para trabajo mecánico y verificable por guion, con revisión de alguien fuerte. Después del 20, el chat que se añadiría es uno de barrido mecánico que escriba en `auditoria/` y no toque código. Queda en la skill sesion-central §16b, con el recordatorio de §6b: al mezclar modelos, una sesión puede quedarse sin cupo del suyo y callarse.

**El aviso de «assessors», encontrado** (f4):
- **Texto y ruta:** nace en `app/voz.py:294-296`, `_SIN_COMPARACION["igual"]`: «Lo que se entendió suena igual que la palabra: puede que la transcripción automática se equivocara» y «Repítela un poco más despacio, marcando cada sonido.» Sale sin transformar por `app/api.py:1983-1984` y lo pinta literal `front/src/app/pantallas/pronunciar.html:256-257`.
- **Condición:** último `return None, "igual"` de `_comparar`: la palabra tiene IPA, lo entendido también, y los dos listados de fonemas no difieren en nada.
- **La causa, y no es un caso raro:** `fonemas.segmentar` **quita la marca de acento** antes de comparar (su docstring lo dice), así que dos pronunciaciones que solo difieren en el acento dan listas idénticas, `difflib` no ve cambio y el código cae **por definición** en «igual». **Un error de acento tónico produce siempre ese aviso y nunca un sonido señalado.**
- **Descartada la alternativa midiéndola:** «sin_ipa» no era, porque «assessors» resuelve a /əˈsɛsɚz/ con 6 segmentos (con palabras de control antes para no fiarse de un negativo).
- **Falta un dato que solo tiene Miguel:** qué escribió whisper en lugar de «assessors» (y la frase completa). Para que hubiera corrección la transcripción tuvo que diferir en el texto, y para salir «igual» la IPA tuvo que coincidir fonema a fonema.
- **Decisiones de la Central:** (1) **el texto se cambia antes de la entrega**, porque hoy culpa a la transcripción de algo que es nuestro; f4 lo redacta, la Central lo aprueba, y va con prueba y mutante, avisando en la primera línea del commit de que `voz.py` es de Codex; (2) **se declara el límite**: se detectan sustituciones de sonido que cambian lo que oye whisper, y quedan fuera el acento tónico y la entonación, **sin mezclarlo** con `medir_ritmo` y la lectura natural, que describen la frase; (3) **Playwright, autorizado** con `PLAYWRIGHT_MODULE` sobre una copia ya presente, sin instalar ni descargar nada.
- **Recordado a f4:** el diagnóstico del límite por hora sigue siendo lo primero; Miguel está bloqueado hasta las 12:21 y no puede probar la corrección.
- **Repaso de `mensaje_profesor.md`** (4e, commit 9086a7b): **no estaba correcto, seis cosas.** (1) `:46-47` prometía una prueba de usuario ya hecha («aún queda volver a probar el recorrido completo de Angular con usuarios»), cuando Ismael y Laura ya lo probaron y los documentos dicen n = 3; la frase anterior sobre las dos lectoras en la interfaz anterior **era correcta y no se tocó**. (2) `:40-42` decía que no se había probado el micrófono físico, y Miguel lo probó el 16. (3) `:32` daba incompleta la lista de lo que se puede sin cuenta: también grabarse, escucharse, ver cómo se dice cada sonido y medir un capítulo. (4) `:27-28` daba 53.179 libros cuando `/api/estado` responde 68.546, que es lo que el profesor verá. (5) `:49` ofrecía compartir el repositorio, que no viaja con la entrega. (6) Fecha al 16.
- **Hallazgo de 4e que precisa el límite, y es clave:** los topes por hora **son por IP** y afectan también a cosas gratis (`app/ui.py:412-422`, `app/api.py:226-227`): consultas 30/h, voz 10/h, sinopsis 6/h, descargas 20/h, medidas 40/h, curvas 6/h. **El cupo por perfil es otro mecanismo**, el que gasta dinero. Encargado a f4 confirmar cuál produjo el aviso de Miguel, si es por IP —lo que empeoraría el riesgo de la demo, porque lo que pruebe antes gasta el cupo— y si se cambian por variable de entorno, que es la diferencia entre subirlo sin tocar el secreto y tener que tocarlo.
- La frase del límite para el mensaje al profesor queda redactada y **sin meter** hasta tener los números, con dos retoques pedidos: nombrar también grabarse y escucharse, y decir qué hacer en vez de «no es un fallo».

**Límite por hora: diagnóstico cerrado** (f4):
- **Cómo se calcula el «vuelve en N minutos»** (`ui._minutos_para_la_siguiente`, `app/ui.py:520-539`): coge la marca **más antigua** del cubo y devuelve `3600 - (ahora - min(marcas))`, redondeado **al alza** al minuto, con suelo de 1. Las dos capturas de Miguel apuntan al mismo instante: 11:32+49 = 12:21 y 11:51+30 = 12:21.
- **Corrección a la lectura de la Central:** la ventana **sí es deslizante**, marca a marca. El aviso dice cuándo se libera **la primera** plaza, no todas: a las 12:21 recupera **una**, y el resto van entrando de una en una. Dos correcciones seguidas a las 12:22 lo dejan seco otra vez.
- **Topes, todos por IP** (`ui.py:412-422`, `api.py:226-227`): voz 10/h, consultas 30/h, sinopsis 6/h, descargas 20/h, medidas 40/h, curvas 6/h. El **cupo por perfil** es otro mecanismo, el que gasta dinero. **Las cuentas no intervienen en el contador**, cuya clave es `cubo:IP` (`ui.py:557-575`), así que **eximir o subir el límite de una cuenta no se puede sin tocar código**.
- **El aviso llega después de grabar, confirmado y peor de lo que parecía:** `/api/voz` lee el formulario entero —el audio **ya viajó** al servidor— y solo después salta el 429 (`api.py:1924-1925`). Mismo patrón que el 403 sin perfil. Y **avisar antes de grabar no es reordenar**: el cubo por hora **no se expone en la API**, así que haría falta publicar su estado y pintarlo en el front, que es código nuevo en `app/` congelado.
- **Decisión de la Central: no se toca nada.** Para la demo, no gastar correcciones en la hora previa (la demo usa dos de diez). Si llega agotado, **reiniciar el Space borra el cubo entero**, porque `_gasto` es un diccionario en memoria (`ui.py:441`), sin tocar secretos ni código, al precio del arranque en frío. Descartado subir `LITERALEVEL_LIMITE_VOZ`, que aplica a todos y reinicia igual.
- **A la cola, juntos:** mover el 429 antes de leer el formulario, exponer el estado del cubo para avisar antes de grabar, y el 403 sin perfil. Misma ruta y mismo arreglo.
- **El texto del límite miente sobre cuál es** (f4): nace en `ui._mensaje_limite` (`app/ui.py:754-761`), lo lanza `/api/voz` (`api.py:1924-1925`) con el cubo **«voz»** (`LIMITE_VOZ_HORA` = 10/h, `ui.py:413`), y **dice «límite de consultas»**, que es el nombre del otro cubo (`lexico`, 30/h). **Cinco caminos comparten ese texto** (subidas, sinopsis, léxico, voz y los de Gradio) y ninguno dice cuál se acabó; por eso hasta nosotros fuimos a mirar la variable equivocada. Los tres cubos que cuestan: voz 10/h, léxico 30/h, sinopsis 6/h, y agotar uno no toca los otros.
- **El tope de su cuenta no se puede consultar aquí** y no hace falta: vive en el secreto del Space, y lo que saltó fue el cubo por hora. Si se quiere el número, lo dice Miguel.
- **Corrección aceptada, y era mía:** «subir o eximir el límite **de una cuenta**» **no existe como opción**; el contador es `cubo:IP` y no sabe de cuentas. La Central lo había repetido tres veces.
- **Decisión: entran dos textos en una sola subida del motor**, con diff mínimo y sin cambios de lógica: (1) que el aviso del límite **diga qué se acabó** y qué sigue funcionando, y (2) el de «igual» del acento. f4 redacta, la Central aprueba, un commit con prueba y mutante avisando de que `voz.py` es de Codex, visto bueno de 4e, una sola subida y comprobación por API de los dos textos.

**La prueba de la boca 3D sí mide** (f4, con `PLAYWRIGHT_MODULE` sobre playwright-core 1.62.1 del runtime de Codex y el Chrome del sistema, sin instalar nada): caso «movil» `OK`, 8.033 colores distintos y 35 % de píxeles opacos, y el propio `assert.ok(px.colores > 40 && px.fraccion > 0.015)` habría saltado si estuviera vacío. **Sospecha descartada: no es una tercera prueba que se cree a sí misma.**
- **Y la mitad en la que e6 acertaba:** la página crea el renderer **sin** `preserveDrawingBuffer` (`escena.ts:667`), así que leer ese canvas desde el navegador da un color y cero opacos; el guion **lo inyecta** antes de arrancar la app (`tools/probar_boca_integrada.mjs:136-139`). e6 describía la página, no el arnés.
- **Cierre honesto, dicho por f4:** su corrida **no dice nada de la regresión**, porque el build era del 15 sep 06:18 (el arreglo del encuadre es de hoy) y el canvas medía **288×420** frente a los **580×840** de lo publicado. Encargado a e6 repetirlo tras su build, con el tamaño real, y ver si el `assert` falla antes del arreglo y pasa después. Si el caso «movil» del guion no representa el móvil real, hay que cambiarlo, y eso es lo que habría cazado esto.
- **Aprobadas las dos redacciones de f4**, para una sola subida del motor:
  - **el aviso del tope, por cubo**, con un parámetro nuevo con valor por defecto y una palabra en cada uno de los 7 puntos de llamada (`api.py` 1048, 1389, 1567, 1925; `ui.py` 2650, 3484, 3780), sin tocar lógica: voz «límite de correcciones de pronunciación», léxico «de explicaciones en contexto», sinopsis «de resúmenes», subidas «de libros subidos», y uno genérico. **Quita «medir un capítulo no cuesta nada», que con los topes de medidas ya era falso en producción.** Inglés solo para léxico, el único camino que pasa idioma;
  - **el aviso de «igual»**: «Los sonidos coinciden con los de la palabra, así que no hay ninguno que señalarte. Lo que no comparamos es el acento de la palabra ni la entonación de la frase, y la diferencia puede estar ahí.» Y como consejo: escuchar «Cómo debería sonar» y fijarse en qué sílaba suena más fuerte. Fuera «puede que la transcripción automática se equivocara».
- **A la cola:** la etiqueta «Cómo colocar la boca:» (`pronunciar.html:257`) no encaja con un consejo de acento; la salida buena es una etiqueta propia para ese caso.
- **1415160** (4e): la frase del límite en `mensaje_profesor.md` con los números de f4, **dichos como lo que son, por conexión y no por cuenta** (10 correcciones, 30 explicaciones, 6 resúmenes, 20 libros nuevos, 40 capítulos medidos, 6 curvas, y el cupo del invitado aparte), diciendo **qué hacer** y nombrando lo que sigue funcionando, **grabarse y escucharse incluidos**. **No dice que a la hora se restablezca todo**, porque sería falso; 4e dejó el mecanismo de la ventana deslizante fuera del texto a propósito, que al profesor no le sirve. Y en `estrategia.md`, pegado al párrafo que ya hablaba de topes, el dato de que **el propio autor se topó con uno probando su aplicación**, con la decisión al lado —no se sube para la entrega, y lo que se cambia después es avisar antes de grabar—, que es lo que lo convierte en argumento y no en queja.
- **Séptimo falso negativo del día por el patrón de búsqueda**, este de 4e: la frase del «espere unos minutos» daba cero porque **cruza dos líneas** y un `grep` de una línea no la ve. Lo comprobó leyendo el párrafo y normalizando espacios. Queda reforzado en la skill sesion-central §18, con las reglas que han salido: buscar por lexema corto, normalizar o usar multilínea, leer el párrafo completo, y decirlo cuando el cero es del patrón. **Los siete se cazaron y ninguno acabó en un entregable.**
- **f4 para antes de tocar `app/` y pide ampliar el alcance; aprobado los tres puntos:**
  1. **Dos pruebas se arrastran obligatoriamente:** `pruebas_extremas.py:560` compara contra el prefijo de `_mensaje_limite` en el camino del léxico, y `:2223` usa **un solo prefijo** exigido a la vez en **voz y sinopsis**, que solo podía funcionar mientras los dos textos fueran iguales. Sin adaptarlas, la suite se cae.
  2. **Quinta prueba del día que se cree a sí misma, y guarda justo la cadena que se va a cambiar:** `pruebas_extremas.py:519-521` usa una lambda que devuelve una **tupla**, y el lanzador solo falla con excepción o `False` exacto, así que imprimía `ok` siempre. El comentario de tres líneas antes describe ese mismo fallo, arreglado en el código y no en la prueba. f4 repasó las 30 lambdas con paréntesis y demostró que las otras seis son booleanos legítimos: **la rota es solo esa.** Se arregla en este commit, porque cambiar una cadena y dejar ciego a su guardián es peor que no tocar nada.
  3. **Faltaba el genérico en inglés**, porque esa prueba llama sin cubo. Aprobados los dos genéricos, con «en 1 minuto» / «in 1 minute» que comprueba `pruebas_api.py:1731` y más de 40 caracteres para la prueba 520 ya arreglada.
- Diff aprobado: `ui.py` (`_mensaje_limite` con parámetro y textos por cubo), `voz.py` (solo la entrada «igual»), 7 puntos de llamada con una palabra cada uno, las suites adaptadas más la prueba nueva del «igual», y dos mutantes cazados cada uno por su prueba y por nombre.
- f4 comprobó que **no hay ningún banco corriendo** (los diez `python.exe` son huérfanos de `colab-mcp`) y avisa por adelantado de que **el clasificador de permisos puede denegarle la subida**, como esta mañana con la vuelta atrás del 30b; si pasa, lo dice y la Central le pasa a Miguel la frase exacta para su chat.
- Queda en la skill probar-la-app-de-verdad: **una aserción que no puede fallar es el mismo fallo sin texto**, con la regla de mirar quién guarda una cadena antes de cambiarla y de hacer que un resultado no booleano sea fallo. El patrón salió **cinco veces en una tarde** y en tres sesiones distintas.

**Front b4459b7, del commit 2836e4d** (e6): publica la frase de *Pronunciar* y **no arregla el 3D**.
- **La frase, cerrada y verificada:** antes, campo de 112 px con 3 líneas ocultas (149 caracteres); ahora, al grabar se muestra **entera** en 401-519, sin recorte y sin campo, con la vista movida hacia ella (`scrollY` 58) y 492 px libres entre la cabecera y la barra para sus 118. 136 pruebas, dos mutantes cazados, visto bueno de 4e.
- **El encuadre del 3D no cambia nada:** la captura del elemento antes (`f4920fa`) y después es **idéntica bit a bit**, 0,00 % de píxeles distintos. El código nuevo está servido (el 17,5 aparece en el paquete) y la cara modelada carga, así que **las dos constantes no llegan a aplicarse**. Pista de e6: al cargar `cara.glb` solo se recalcula la **distancia** sobre el punto de mira viejo, y el punto de mira no se vuelve a fijar.
- **Decisión:** **no se revierten** las constantes, porque son la base del arreglo bueno y lo publicado no empeora nada. Preaprobado el arreglo si consiste en **rellamar al encuadre completo cuando la cara ya está dentro**, con una condición: **la captura antes y después tiene que diferir**; si vuelven a salir idénticas, para y avisa. Y que dé los píxeles de separación de los labios al borde.
- **La prueba no distingue el fallo del arreglo:** pasa en los dos builds con métricas idénticas hasta el sexto decimal. Descartado que el tamaño sea la causa (aspecto idéntico, 0,69, y la distancia sale del aspecto). **Pregunta abierta a f4, con control positivo:** si `borde` valía 0 también cuando los labios tocaban el borde, esa comprobación no mide lo que dice medir; forzar el defecto y ver si `borde` pasa de 0, decir qué mide y qué haría falta, sin implementarlo. La Central se inclina por la cola.
- **«assessors», cerrado como deducido del código:** Miguel ya no recuerda la frase ni la transcripción. La causa queda como **deducida**: `fonemas.segmentar` borra la marca de acento, así que un fallo de acento cae siempre en «igual», y «assessors» tiene IPA, así que no era «sin_ipa». La transcripción concreta no se conserva. No cambia nada de lo aprobado para la subida del motor.
- **b9 vuelve con cupo (Fable 5.1)**, sin trabajo a medias; su último commit es 890c410. **No se le da la fase 1 ni la ronda 2**, porque los documentos ya se pusieron al día en la ronda 4. **Encargo: barrido sistemático de pruebas que se creen a sí mismas** en `pruebas_api.py`, `pruebas_corpus.py`, `pruebas_extremas.py`, las `*.spec.ts` y `tools/probar_*`, **solo lectura**, con demostración de ceguera por hallazgo, separando ciegas de débiles, y con lo revisado y correcto. Informe en `auditoria/ronda5_pruebas_ciegas_b9_2026-09-16.md`. Motivo: hoy salieron cinco por casualidad en tres sesiones. Aviso incluido por §6b: si se queda sin cupo, que escriba lo que lleve y lo diga.

**Reinicio de las sesiones (16 sep).** Todas vuelven con nombres nuevos: la Central es ahora `entrega-80`, y las demás `entrega-a3`, `entrega-b0`, `entrega-18` y `entrega-5d`. La Central les pregunta quién eran, qué tenían a medias y si recuerdan su encargo, y les pide no tocar código hasta contestar.
- **En el árbol quedan cambios sin commitear del motor de f4** —los dos textos aprobados y sus pruebas—: `app/api.py`, `app/ui.py`, `app/voz.py`, `pruebas_api.py`, `pruebas_extremas.py` y `tools/banco_mutantes.py`. Nadie más los toca hasta que la sesión que era f4 los reclame.
- **`entrega-a3` era e6** (ahora Opus 5). Sin nada a medias; último publicado, la revisión `b4459b7` del commit `2836e4d`. Conserva el encargo y afina el diagnóstico del 3D: **la cámara se coloca con números fijos en el constructor, y `vista()` —donde están las constantes nuevas— solo corre al pulsar «Restablecer vista»**. Vía libre al arreglo (aplicar `vista()` al arrancar y cuando la cara está dentro), con captura que difiera, píxeles de separación de los labios, «Restablecer vista» igual que el arranque, prueba, mutante y visto bueno de 4e; y **sin tocar ninguno de los archivos con cambios de f4**.
- **Mapa tras el reinicio:** `entrega-a3` = e6 (Opus 5), `entrega-b0` = 4e (Opus 5), `entrega-5d` = f4 (Opus 5), `entrega-18` = b9 (Fable 5.1, **sin historial**: arrancó con el mensaje de la Central como primer turno). La Central es `entrega-80`.
- **5d (f4)** recuerda su encargo y lo tenía a medio hacer: los dos textos escritos en el árbol, `pruebas_extremas.py` entera en verde (353), y mutantes T1-tope-sin-cubo y T2-igual-culpa-a-whisper. Le faltaban `pruebas_api.py`, los mutantes por nombre, el árbol limpio, el visto bueno de 4e, la subida y la comprobación por API. Sigue en ese orden; `corpus_abierto.parquet` no entra en su commit.
- **b0 (4e)** sin nada a medias (último, 1415160); confundió los cambios del árbol con un banco ajeno y no los tocó, que era lo correcto. Sigue esperando a que a3 publique el paso 0, y le llegarán dos visto buenos: el del motor (5d) y el del encuadre (a3).
- **18 (b9)** recibe entero el encargo del barrido de pruebas ciegas, que se había perdido con el reinicio, citando `HEAD` porque el árbol va a cambiar mientras trabaja.
- **Coordinación de RAM** entre el árbol limpio de 5d y el `ng build` de a3: mirar la RAM libre antes y no solaparlos.

**Boca 3D: el diagnóstico anterior era falso, corregido por e6 (a3).**
- **Por qué las capturas salían idénticas:** `cara.glb` trae `labios_en_piel: 1`, así que `escena.ts:1207-1211` pone `cabezaEntera = true`, punto de mira 0,9 y distancia 17,5 **desde antes** del cambio. Las dos constantes nuevas solo afectan al caso «cara sin cabeza entera», que con este `.glb` no ocurre: **código muerto, sin efecto y sin daño**. Rellamar a `vista()` solo giraría unos 4°.
- **Corrección de una afirmación que la Central dio por buena y repitió:** «los labios tocan el borde izquierdo» **era falso**; la columna 0 de la captura es una línea oscura de la página. A 390 px el dibujo queda a **14 px** del borde izquierdo y a **10-12 px** del derecho: justo, pero dentro. **Esa frase del registro anterior y de los mensajes a Miguel queda retirada.**
- **Lo que vio Miguel no se reproduce a 390 px.** Tres explicaciones sin decidir: un móvil más estrecho (a 360 px el lienzo mide ~260), la vista **girada con el dedo** (en su captura la cara sale de tres cuartos, con los planos del cuello a la vista, lo que apunta aquí) o un fotograma con la mandíbula abierta.
- **Decisión:** primero **medir** (B) a 360 y 412 px, con la vista girada y con la mandíbula abierta; solo si sale la explicación del ancho se aplica A (alejar de 17,5 a ~20), y si sale la del giro no se toca la cámara y se propone que el visor vuelva al perfil. Pregunta a Miguel: si giró la cara con el dedo y qué teléfono tiene.
- **Miguel confirma que giró la cara con el dedo** antes de la captura, y su teléfono es un **Samsung Galaxy S24 FE**. La explicación del giro pasa a ser la principal: el `.glb` es **media cabeza seccionada**, y al girarla se ven los planos de corte, que es lo que describió. No es un fallo de encuadre. Encargado a a3: medir primero en qué rango de giro el modelo se ve entero, luego el ancho a 360, 384 y 412 px (384 es el habitual de ese Samsung con el zoom por defecto, sin darlo por seguro), y proponer **limitar el giro** o **volver al perfil al abrir**, sin aplicar nada.
- **Barrido de pruebas ciegas** (b9, `entrega-18`, informe 43cdae8, sin quedarse sin cupo y sin tocar nada): **siete ciegas de verdad** en `pruebas_extremas.py`, todas fuera de los cambios de f4, demostradas sobre dobles mutantes (7 de 7 en `ok`), **doce débiles** y la lista de lo que está bien por archivo. La Central comprobó tres en `HEAD` (C2, C3 y C4) y son ciegas como se describe. **C3 y C4 dejan su propiedad sin ninguna otra red.** Sobre el `.mjs`, b9 confirma que `borde` va precedido de un guardia de color y fracción, así que el lienzo vacío ya no pasa.
- **Decisión: a la cola, no antes del 20.** Son solo pruebas, ninguna afecta a lo que ve un usuario, y el archivo tenía cambios de f4 a medias. Prioridad C3 y C4, y el arreglo de fondo en el lanzador (que `None` y los contenedores cuenten como fallo, respetando la convención `condición and "texto"`).
