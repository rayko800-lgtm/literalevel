# Ronda 3 de auditoría: informe para Miguel

Madrugada del 15 de septiembre de 2026. Escrito por la central con los siete
informes de la ronda 3, el ensayo de la demo y las comprobaciones de cada
reinicio. El detalle hallazgo a hallazgo está en el consolidado de la ronda 1,
que se fue ampliando durante la noche.

## En una frase

Todo lo serio que abrió la ronda 2 está cerrado y verificado en producción. La
ronda 3 encontró dos fallos serios nuevos en la búsqueda, los dos causados por
arreglos anteriores. Uno llegó a producción por un fallo de coordinación de la
central y se corrige en el reinicio 22. El ensayo de la demo cabe en unos
cuatro minutos, y los guiones ya coinciden con lo que se ve.

## Qué está en producción

| Pieza | Versión | Qué lleva de esta noche |
|---|---|---|
| Motor (Space de Gradio) | reinicio 30b, 0319290 (empates por cercanía al nivel en la franja; encima: 30a 282c46f con MiniLM precargado; 28 restaurado 62e5a06 con autor más título arreglado, anuncios de drogas fuera, silencio sin coste y con el uso devuelto, buscador precargado al arrancar, autores clásicos por apellido y «Jane Austen» con B1) | «amor» con B1 da 12 de 12 sobre amor, y ahora trae también cuentos de su nivel marcados; «Jane Austen» abre con su obra; voz sin falsos «difíciles»; 225 textos remedidos por bloques con un texto raro; 200 textos que no son lectura fuera |
| Front (Space estático) | revisión f4920fa, del commit a656c2e | Tu nivel y Pronunciar nuevos; «Primero lo de tu nivel» con la franja; chips con amor y fantasmas; micrófono con estado visible dentro de la barra (el aviso se pintaba debajo y no se veía) y aviso para abrir en Chrome desde el navegador de WhatsApp; «Entrar» lleva a «Tu perfil» y «Ajustes» con nombre; un solo aviso en el lector y ayuda con «?» en el lector y en Pronunciar; bienvenida de 3 pasos; textos del cuestionario y del gesto corregidos; «Corrígeme» sin sesión ya contesta y su aviso no queda tapado; singular y plural correctos en «Mis palabras», Ajustes y «Mídeme con un texto» |
| Documentos y guiones | 16 sep: d232ffd, dc447f4 y c490b11 (documento, estrategia y presentación) y 657a640 (guiones de la demo y del vídeo); antes: 2a44731, 5a3552a, 5181c8f, 489ee48 y f829d60 | coste de cómputo real; la frase del caso Esmeralda reescrita (no faltaba catálogo, fallaba la búsqueda: 114 cuentos libres de amor en B1); receta del perfil B2 sin «Me vale así» (en la sexta no elegir «Capto bien la idea»); textos de las pantallas A; «Antes de la demo» con voz baja desde el móvil y calentar el buscador; límites declarados de la búsqueda en el documento (limitación 15) y en la estrategia; paso 3 con «Crimen y castigo de Dostoyevski»; esperar un minuto tras un reinicio; ronda 4: cuestionario contado como es (tres preguntas y tres fragmentos), gesto «mantener presionada», n = 3 con Ismael, cuaderno ejecutado en Colab el 16 sep con salidas, cifras de esa corrida y los guiones de verificación «a petición» |

## Informes de la ronda 3

| Área | Auditó | Informe | Cerrado de la ronda 2 | Nuevo |
|---|---|---|---|---|
| Búsqueda del reinicio 19 | 4e | ronda3_2026-09-15_busqueda.md | el rescate por nombre ya no confunde temas | **serio:** autores clásicos sin rescate (cervantes, dante, moliere); 3 menores |
| API: subidas y error de entrar | e6 | ronda3_2026-09-15_api.md | error sin contraseña, subidas simultáneas, prueba de concurrencia | 3 menores de candados |
| Documentos | e6 | ronda3_2026-09-15_documentos.md | coste de cómputo real y los cinco menores | 1 menor de fecha, ya corregido |
| Boca 3D | 4e | ronda3_2026-09-15_boca3d.md | fuga, audio, teclado, caída al 2D | 2 menores, ya corregidos |
| Encontrar: margen de la franja | 4e | ronda3_2026-09-15_front.md | los cinco cuentos de la luna suben | chip vacío y pruebas sin bordes, ya corregidos |
| Código del reinicio 21 | 4e | ronda3_2026-09-15_reinicio21.md | «Fenn, Amor» no vuelve; el raro no baja | **serio:** autor más título pierde al autor; anuncio de GHB; 2 menores de bloques |
| Voz, restos de la ronda 2 | e6 | ronda3_2026-09-15_voz.md | IPA en ASCII y abreviaturas Mr., Mrs., Ms. y Dr. | silencio a medias: sigue la llamada de pago; «St.» abierto |
| Ensayo de la demo | e6 | ensayo_demo_2026-09-15.md | — | 10 arreglos de guion y un fallo de etiqueta, ya aplicados |

## Los dos serios nuevos

1. **Buscar autor y título a la vez pierde al autor.** «treasure island
   stevenson» dejaba Treasure Island en quinto lugar; «white fang jack london»
   no traía a Jack London. Venía de la regla que evita que «Jane» traiga a
   Sidney Austen, que usaba como nombres de pila palabras corrientes como
   island o white. **Llegó a producción** porque 4e avisó a la central antes de
   la subida y la central no se lo pasó a tiempo a quien desplegaba. Desde
   entonces, el aviso de parar va directo a quien despliega. Arreglo en el
   reinicio 22, **ya en producción**: en el Space, las cinco búsquedas pasan de 2, 0, 0, 0 y 4
   resultados del autor a 8, 9, 8, 2 y 10.
2. **Autores clásicos por apellido.** «cervantes», «dante», «moliere» y
   «agatha christie» no encuentran sus libros, efecto del endurecimiento del
   nombre del reinicio 19. Va al reinicio 26.

Y un hallazgo de datos que no es de código: StoryWeaver acepta textos de
cualquiera, y seguían visibles un anuncio de venta de GHB y otro de
metanfetamina de la misma cuenta. Salen en el reinicio 22, con revisión de
todas las cuentas que tenían algún anuncio.

## Lo que aprendimos (queda en skills)

- Un arreglo de búsqueda que solo se prueba con la consulta que lo motivó
  rompe otra. Hay una batería fija de búsquedas en la skill
  `buscador-encontrar`, y esta noche cazó dos regresiones antes de subir.
- Subir desde un commit fijo (`--commit`) evita depender de que el disco esté
  quieto con cuatro sesiones trabajando.
- Un aviso de parada no puede pasar por un relevo.
- Una orden de la central no levanta una norma que Miguel dejó a otra sesión
  (las contraseñas de perfiles).
- Una medida de riesgo tiene que comparar el Space actual contra el cambio
  completo que va a subir. En el 27 se midió solo una de tres reglas y subió
  una regresión en 27 palabras de tema; la cazó la medida independiente de 4e
  contra una línea base tomada antes, y el 28 la cerró en menos de una hora.
- Si los archivos dependen entre sí, suben juntos o no sube ninguno.
- Las contraseñas no se muestran nunca, ni enmascaradas; y un cambio de
  contraseña se hace verificando antes todas las cuentas contra el Space.

## El catálogo: los textos están, la búsqueda no los saca

Al elegir las sugerencias parecía que con A2 y B1 faltaban textos de amor,
familia, fantasmas o monstruos. e6 los contó y la central lo verificó: hay 74
cuentos libres de amor en A2–B1, 47 de fantasmas, 29 de monstruos y 338 de
amigos. La búsqueda no los devuelve, porque los libros de Gutenberg copan los
primeros puestos antes de repartir por nivel. **Es la causa de fondo del caso
de Esmeralda**, y ampliar el catálogo no lo arreglaría: en las fuentes libres
que usamos solo quedan unos pocos cuentos nuevos, casi todos en StoryWeaver.
El arreglo es buscar también dentro del nivel del lector, en el reinicio 25.

## Esmeralda probó la versión nueva

Nota de voz del 15 de septiembre por la madrugada. Le gusta mucho más que la
primera vez: «ya es más fácil de usar y aparte ya lo disfrutas más… ya no
siento que estoy haciendo un trabajo de informática». Le encantaron las
paletas, las portadas, los ajustes y poder subir su libro. Tres cosas no:

1. **Poca variedad en su nivel.** Es el fallo de búsqueda de esta noche; lo
   arregla el reinicio 25.
2. **Las preguntas de Tu nivel.** Después de las preguntas se le ofrece afinar
   con otras, y cree que debería darle el nivel directamente.
3. **Pronunciar.** Se perdió en la corrección y en «más lento», y volvió a
   decir «a lo mejor yo soy muy tonta».

e6 recorre esas dos pantallas como alguien que llega sin saber nada y prepara
propuestas con esquema para que Miguel elija antes de programar.

## Ismael probó la app, y una segunda nota de Laura

Nota de voz del 15 de septiembre: la probó el 14 y el 15, y «cuesta un poquito
entenderle»; pide que sea más intuitiva o que tenga «cuadros de diálogo que te
digan qué hace cada cosa». Es la segunda persona, después de Esmeralda, que no
entiende sola para qué sirve cada pantalla. e6 recorre el front publicado como
alguien que llega por primera vez y propone dos formas de ayuda con esquema (una
bienvenida de pocos pasos que se puede saltar, o una frase de ayuda por
pantalla) para que Miguel elija antes de programar.

Hay una segunda nota, **de Laura**, que concreta dos cosas. **El micrófono:**
había entrado —«entré y ya me inicié sesión»—, pulsó grabar y no pasó nada
visible ni empezó la grabación. **La saturación:** textos largos y mucho scroll
antes de saber qué hacer; de esa queja sale la segunda tanda de ayuda. Durante un
día esta nota estuvo archivada como de Ismael, y de ahí salieron dos
explicaciones equivocadas seguidas; Miguel aclaró el 16 de septiembre de quién
era. De Ismael, según Miguel, es el dato del teléfono **Android** con el enlace
abierto **desde WhatsApp**, y que **no había iniciado sesión**; eso no lo hemos
medido nosotros y no entra en los entregables como causa.

**Cerrado el 16 de septiembre, y con un hallazgo distinto.** Miguel confirmó que
la nota es de Laura y que en su teléfono, con su cuenta, el micrófono graba bien.
e6 midió los cinco finales de pulsar el micrófono en lo publicado (48d748d, 390
px, informe 9d43956) y en todos sale un mensaje dentro de la barra, que acaba en
688 y se lee sin desplazar: ninguno es mudo. Así que la explicación que mejor
encaja para su nota es que fuera **anterior al arreglo 601788b**, cuando el aviso
se pintaba en 750-849 bajo la barra; queda como hipótesis fechada, junto con las
otras dos de e6 (que el mensaje saliera y no se leyera como respuesta, o un fallo
en `MediaRecorder`, el único tramo que no se puede provocar).

**Y el fallo que sí está comprobado es otro:** en *Pronunciar* sin sesión,
«Corrígeme» va apagado, sin explicación al alcance, y pulsarlo no da ninguna
respuesta; el texto que lo explica está 309 px más arriba. Es el único «pulso y
no pasa nada» verificado que tenemos, lo encontramos nosotros al medir, y no es
lo que ella describía: no hay que mezclarlos. Arreglo aprobado, calcado del
patrón del lector, con revisión de 4e antes de publicar.

Lo que sí era un fallo real y sigue arreglado: **e6 lo confirmó,** los avisos de
Pronunciar se pintaban debajo de la barra fija del micrófono, así que en el
móvil no se veía ni «este navegador no deja grabar», ni «no tengo permiso», ni
siquiera «Grabando…». El arreglo pone una línea de estado dentro de la barra
(«Grabando: habla ahora»), un mensaje para cada error y, en el navegador de
WhatsApp, un aviso antes de pulsar para abrir la app en Chrome.

## Un incidente con una contraseña

A las 04:30, al preparar la prueba con invitado8, una sesión miró el formato
del archivo local de contraseñas con las claves enmascaradas, y la línea de
«profesor» no quedó oculta. La contraseña salió en la salida de una
herramienta local. No fue a ningún mensaje, commit ni archivo, pero la salida
de las herramientas forma parte del contexto de esa sesión. **Miguel decide si
la cambia.** Cambiarla es escribir en el bucket, así que tiene que hacerlo él o
dar el permiso en una sesión.

## Lo que Miguel tiene que saber para la demo

- **Receta del perfil B2**, en «Tu nivel»: varias veces por semana · Alice con
  naturalidad · una novela actual · fragmento medio con naturalidad · los hechos
  principales · fragmento difícil «Entiendo algunas partes, pero necesitaría el
  diccionario». En la sexta, **no** «Capto bien la idea» (sube a C1). Se guarda
  sola al contestar la sexta.
- **Paso 3:** buscar «Crimen y castigo de Dostoyevski» (no «dostoyevski» a
  secas, que hoy enseña cuentos sin relación). Repetirlo con tu cuenta antes de
  grabar.
- **Tras un reinicio del Space, espera un minuto** antes de la búsqueda de prueba
  (un arranque tardó 45 s en tener el buscador listo).
- **Antes de compartir pantalla:** una búsqueda con el perfil guardado (si el Space acaba de
  reiniciarse, esperar medio minuto; después cada búsqueda tarda menos de 1 s), abrir una vez la
  boca 3D, y grabar una frase en voz baja desde el móvil para ver que no sale
  «No te oí».
- **La contraseña de «profesor» se cambió** a las 05:40; la nueva está solo en
  el archivo local.

## Estado al cierre de la ronda (15 sep, 08:00)

- **Motor:** reinicio 28 (Space 74f1484), verificado por dos sesiones.
- **Front:** bdfa418, con Tu nivel y Pronunciar nuevos, la ficha de un capítulo
  arreglada y el aviso «No te oí · Este intento no cuenta».
- **Guion de la demo:** 800060e, con la receta B2 y «Antes de la demo».
- **Consultas de autor con perfil (paso 3 original):** el arreglo del 29 quita cuentos a 4 temas con el perfil 1,20; se volvió al 28 con autorización de Miguel. **La demo no depende de ello:** con el perfil B2 de la receta,
  buscar un autor como «dostoyevski» enseña primero cuentos libres sin
  relación («Books», «Story Chikkappa») en «En tu nivel», y ya no el aviso de
  que no hay libros de su nivel. Parece un efecto de la búsqueda por franja
  (reinicio 25) en consultas de autor: con una sola palabra, títulos genéricos
  como «Books» o «The Story of Stories» casan con «libros sobre X». f4 lo mide
  con prioridad. **El guion ya no depende de ello:** el paso 3 pasa a buscar
  «Crimen y castigo de Dostoyevski», que da el aviso de que no hay libros de su
  nivel y Crime and Punishment como primera tarjeta de «De otros niveles»
  (comprobado por 4e en la página publicada con el perfil B2).
- **Segundo ensayo de la demo (e6):** todo lo demás cuadra con el guion a 390 px
  y a 1280 (receta B2, «cuentos de dragones», detectives, ficha de Crime and
  Punishment, poverty, Pronunciar, «Mis palabras», libro de un capítulo, plan
  B). Búsquedas de 0,5 a 0,8 s; la boca 3D tarda 2,9 s la primera vez en el
  móvil; la demo sigue en 3:40–4:10.
- **Límites declarados, sin cambio de código:** «Historias de amor» y «Terror
  gótico» (título en consultas largas), «rosa» y «luna» con B1 (el arreglo
  rompía 70 de 200 listas), «tolstoy» sin perfil, y «emma» con B1, «hamlet» y
  «ulysses» sin perfil, que ya fallaban antes.

## Lo que queda

| Qué | Quién | Cuándo |
|---|---|---|
| ~~Reinicio 22: autor más título, anuncios de drogas, tres menores de subidas~~ | hecho, Space 62a5373, comprobado | 04:05 |
| Reinicio 23: arreglos de voz (86e6e1d): «St.» corta la frase, «...» no cuenta como oída | f4 | subido, Space d854649. **La prueba de pago falló:** 2,5 s de silencio dan «you» en whisper y siguen lanzando la corrección de pago |
| ~~Reinicio 24: regla de silencio de whisper (4e, 0a759a5)~~ | hecho, Space 0c09197 | prueba de pago repetida: sin corrección ni fallos guardados |
| ~~Reinicio 25: recuperación dentro de la franja del lector (caso Esmeralda)~~ | hecho, Space 4ba66f9 | «Fantasmas» A2 pasa de 1 a 9 cuentos del tema en su nivel; primera búsqueda con nivel tras reiniciar tarda 18,6 s (precarga en el 26) |
| ~~Reinicio 26: buscador precargado al arrancar, devolución del uso con silencio (API y Gradio), voz sin TTS ni análisis sin voz~~ | hecho, Space 5c6f8d9 | invitado8 17 → 17 tras dos pruebas de silencio; primera búsqueda tras reiniciar, unos 30 s |
| ~~Reinicio 27: autores clásicos, «Jane Austen» con B1, ficha de un capítulo, buscador_listo~~ | hecho, Space 1708cb1 | trajo una regresión (27 palabras de tema traían al autor), cerrada en el 28 |
| ~~Reinicio 28: arreglo de la regresión del 27~~ | hecho, Space 74f1484 | las 100 palabras de tema con el mismo top 10 que el 26; clásicos y Austen siguen bien (verificado por 4e) |
| ~~Reinicio 29: consultas de autor con perfil~~ | subido y **vuelto atrás al 28** (Space 62e5a06, autorizado por Miguel, verificado por 4e: las 33 listas de control idénticas al 28) | quitaba cuentos de su nivel a «león», «brown», «hope» y «animales de la granja» con el perfil 1,20; se mide otra vía (i7). El paso 3 del guion no depende de esto |
| ~~Ayuda para usuarios nuevos (decisión de Miguel)~~ | hecho, front 48d748d (aria-label de Inicio en 72e9525; textos del cuestionario y del gesto en 48d748d) | tanda 1 (Entrar → Tu perfil, «Ajustes» con nombre, «Mídeme» corregida), tanda 2 (un solo aviso en el lector y ayuda con «?» en el lector y en Pronunciar) y tanda 3 (bienvenida de 3 pasos que se puede saltar); guiones 657a640, con visto bueno de e6 y ensayo completo sobre el 30b |
| ~~Otra vía para las consultas de autor con perfil (i7)~~ | medida | ninguna variante cumple: quitaba cuentos a temas o no arreglaba los autores. **Límite declarado:** con perfil, «dostoyevski», «tolstoy» o «cervantes» a secas marcan cuentos sin relación; el guion usa «Crimen y castigo de Dostoyevski» |
| Reinicio 30a: MiniLM precargado en el Space | hecho, Space 282c46f | buscador listo a los 20 s de RUNNING en el primer arranque y a los 12 s en el segundo (0319290), frente a 55 s; 0 descargas de MiniLM en el log completo |
| Reinicio 30b: empates deterministas (redondeo a 6 decimales, cercanía al nivel en la franja y fila) | hecho, Space 0319290 (DESPLIEGUE 9108a52) | contra el volcado del Space 28: 0 vueltas, 198 iguales, 58 solo orden, top 10 con el mismo conjunto en todas y «pintura» B1 aceptada (copia de 0,775 en vez de 0,99); paso 3, granja y dragones bien en el front; límite declarado: el redondeo no iguala Space y local en todas las parejas («magic» B1, «mystery» 11↔12). Medida previa: 545 listas contra el 28 sin paro; «mystery» sin perfil intercambia 7↔8 (empate); lista cerrada de 10 cortes con copias más cercanas al nivel; marcha atrás si falla el paso 3, «granja», «dragones», marcas o longitud |
| Ensayar con cuenta: explicación de la IA, «Practica esta palabra», paso 6 y «Este intento no cuenta»; demo cronometrada | **Miguel** | 16 sep: ha estado probando la app con su cuenta y **el micrófono le graba bien**; queda cronometrar la demo entera |
| Auditoría ciega del estado final | Codex | 19 de septiembre, desde las 8:56 (cupo comprobado el 15) |
| Ronda 4, a ciegas: documento, estrategia y presentación contra la producción de hoy | e6 | 15 sep |
| Ronda 4, a ciegas: reproducibilidad y cifras del notebook | f4 | 15 sep |
| Ronda 4: enlaces y recursos públicos de los entregables (HF, Spaces, datos, DOI) | 4e | 15 sep |
| Tres menores de 4e (parche_menores_28.py: devoluciones con disco roto, índice apellido→filas, obras sin fechas); buscador y cobro congelados hasta el 20 | f4 | después del 20; el de las obras mueve la exención de 5 obras y exige medida completa |
| MENOR tras la entrega: el comentario de 1643c4b en catalogo.py promete que los empates no se reordenan entre máquinas, en contra del límite declarado | quien toque catalogo.py | después del 20 |

## Al cierre del 16 de septiembre

La ronda 4 se cerró y el día siguió con la prueba de Miguel, que es la que más
cambió el trabajo. Resumen para no leer el consolidado entero.

**Publicado hoy.** Front: textos del cuestionario y del gesto, el aria-label de
Inicio, «Corrígeme» que ya contesta sin sesión y con su aviso visible, y singular
y plural correctos. Última revisión del Space del front citada aquí: `f4920fa`,
del commit `a656c2e`. Motor: reinicio 30b (`0319290`), con los empates ordenados
por cercanía al nivel.

**Lo que trajo la ronda 4.** Documento, estrategia y presentación corregidos
(cuestionario contado como es, el gesto de mantener presionada, n = 3 con los
tres lectores, el cuaderno **ejecutado de verdad en Colab** el 16 con las salidas
guardadas, y los guiones de verificación dichos como «se comparten a petición»).
Enlaces: ninguno roto y las siete revisiones citadas siguen existiendo. Notebook:
revisado celda a celda, sin cifras viejas.

**Lo que encontró Miguel probando con su cuenta.** El límite de **10
correcciones por hora y por IP**, que no es de su cuenta y vive en memoria; el
aviso que **nombraba el cubo equivocado**; el mensaje de «igual» que culpaba a la
transcripción cuando la verdad es que **no comparamos el acento**; la boca 3D con
el encuadre cortado; y la frase de *Pronunciar* que obliga a desplazarse. Los
cuatro primeros se arreglan o se declaran antes de la entrega; el último, en su
versión mínima.

**Lo que queda, con dueño.** e6: la tanda del encuadre y la frase, repetir la
prueba de la boca tras compilar con el tamaño real, y el paso 0 de la bienvenida.
f4: la subida del motor con los dos textos y la revisión de los dos commits de
4e. 4e: el paso 0 en los guiones y la regla de no gastar correcciones en la hora
previa. Miguel: cronometrar la demo entera y lanzar Codex el 19 por la mañana.

**Lo aparcado con su motivo** está en `auditoria/cola_tras_la_entrega_2026-09-16.md`.
