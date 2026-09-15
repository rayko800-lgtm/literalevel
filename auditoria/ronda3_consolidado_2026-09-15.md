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
| Motor (Space de Gradio) | reinicio 27, 1708cb1 (autor más título arreglado, anuncios de drogas fuera, silencio sin coste y con el uso devuelto, buscador precargado al arrancar, autores clásicos por apellido y «Jane Austen» con B1) | «amor» con B1 da 12 de 12 sobre amor, y ahora trae también cuentos de su nivel marcados; «Jane Austen» abre con su obra; voz sin falsos «difíciles»; 225 textos remedidos por bloques con un texto raro; 200 textos que no son lectura fuera |
| Front (Space estático) | bdfa418 | Tu nivel y Pronunciar nuevos (propuestas A elegidas por Miguel); boca 3D sin fuga y con una sola descarga; «Primero lo de tu nivel» con la franja; chips con amor y fantasmas; aviso «No te oí · Este intento no cuenta»; ficha de un solo capítulo sin gráfica vacía |
| Documentos y guiones | 2a44731 y 5a3552a | coste de cómputo real; la frase del caso Esmeralda reescrita (no faltaba catálogo, fallaba la búsqueda: 114 cuentos libres de amor en B1); receta del perfil B2 sin «Me vale así» (en la sexta no elegir «Capto bien la idea»); textos de las pantallas A; «Antes de la demo» con voz baja desde el móvil y calentar el buscador |

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
- **Antes de compartir pantalla:** una búsqueda con el perfil guardado (si el Space acaba de
  reiniciarse, esperar medio minuto; después cada búsqueda tarda menos de 1 s), abrir una vez la
  boca 3D, y grabar una frase en voz baja desde el móvil para ver que no sale
  «No te oí».
- **La contraseña de «profesor» se cambió** a las 05:40; la nueva está solo en
  el archivo local.

## Lo que queda

| Qué | Quién | Cuándo |
|---|---|---|
| ~~Reinicio 22: autor más título, anuncios de drogas, tres menores de subidas~~ | hecho, Space 62a5373, comprobado | 04:05 |
| Reinicio 23: arreglos de voz (86e6e1d): «St.» corta la frase, «...» no cuenta como oída | f4 | subido, Space d854649. **La prueba de pago falló:** 2,5 s de silencio dan «you» en whisper y siguen lanzando la corrección de pago |
| ~~Reinicio 24: regla de silencio de whisper (4e, 0a759a5)~~ | hecho, Space 0c09197 | prueba de pago repetida: sin corrección ni fallos guardados |
| ~~Reinicio 25: recuperación dentro de la franja del lector (caso Esmeralda)~~ | hecho, Space 4ba66f9 | «Fantasmas» A2 pasa de 1 a 9 cuentos del tema en su nivel; primera búsqueda con nivel tras reiniciar tarda 18,6 s (precarga en el 26) |
| ~~Reinicio 26: buscador precargado al arrancar, devolución del uso con silencio (API y Gradio), voz sin TTS ni análisis sin voz~~ | hecho, Space 5c6f8d9 | invitado8 17 → 17 tras dos pruebas de silencio; primera búsqueda tras reiniciar, unos 30 s |
| ~~Reinicio 27: autores clásicos, «Jane Austen» con B1, ficha de un capítulo, buscador_listo~~ | hecho, Space 1708cb1 | batería de 16 fallos a 3 |
| Reinicio 28: título en consultas largas («Historias de amor», «Terror gótico»), «rosa» y «luna» con B1, erratas en títulos | f4, con visto bueno de 4e y e6 | en curso |
| Ensayar con cuenta y micrófono: explicación de la IA, «Corrígeme», lectura natural, «Mis palabras», demo cronometrada | **Miguel** | fin de semana del 19-20 |
| Auditoría ciega del estado final | Codex | 19 de septiembre |
