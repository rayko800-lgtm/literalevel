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
| Motor (Space de Gradio) | reinicio 21, 384a206 | «amor» con B1 da 12 de 12 sobre amor; «Jane Austen» abre con su obra; voz sin falsos «difíciles»; 225 textos remedidos por bloques con un texto raro; 200 textos que no son lectura fuera |
| Front (Space estático) | ec957d0 | boca 3D sin fuga de memoria y con una sola descarga; «Primero lo de tu nivel» se cumple; ocho sugerencias que dan resultados con A2 y B1 |
| Documentos y guiones | 8856030 | coste de cómputo real, cifras del reinicio 21, diez arreglos del ensayo y la sección «Antes de la demo» |

## Informes de la ronda 3

| Área | Auditó | Informe | Cerrado de la ronda 2 | Nuevo |
|---|---|---|---|---|
| Búsqueda del reinicio 19 | 4e | ronda3_2026-09-15_busqueda.md | el rescate por nombre ya no confunde temas | **serio:** autores clásicos sin rescate (cervantes, dante, moliere); 3 menores |
| API: subidas y error de entrar | e6 | ronda3_2026-09-15_api.md | error sin contraseña, subidas simultáneas, prueba de concurrencia | 3 menores de candados |
| Documentos | e6 | ronda3_2026-09-15_documentos.md | coste de cómputo real y los cinco menores | 1 menor de fecha, ya corregido |
| Boca 3D | 4e | ronda3_2026-09-15_boca3d.md | fuga, audio, teclado, caída al 2D | 2 menores, ya corregidos |
| Encontrar: margen de la franja | 4e | ronda3_2026-09-15_front.md | los cinco cuentos de la luna suben | chip vacío y pruebas sin bordes, ya corregidos |
| Código del reinicio 21 | 4e | ronda3_2026-09-15_reinicio21.md | «Fenn, Amor» no vuelve; el raro no baja | **serio:** autor más título pierde al autor; anuncio de GHB; 2 menores de bloques |
| Ensayo de la demo | e6 | ensayo_demo_2026-09-15.md | — | 10 arreglos de guion y un fallo de etiqueta, ya aplicados |

## Los dos serios nuevos

1. **Buscar autor y título a la vez pierde al autor.** «treasure island
   stevenson» dejaba Treasure Island en quinto lugar; «white fang jack london»
   no traía a Jack London. Venía de la regla que evita que «Jane» traiga a
   Sidney Austen, que usaba como nombres de pila palabras corrientes como
   island o white. **Llegó a producción** porque 4e avisó a la central antes de
   la subida y la central no se lo pasó a tiempo a quien desplegaba. Desde
   entonces, el aviso de parar va directo a quien despliega. Arreglo en el
   reinicio 22, probado en local: las cinco búsquedas pasan de 2, 0, 0, 0 y 4
   resultados del autor a 8, 9, 8, 2 y 10.
2. **Autores clásicos por apellido.** «cervantes», «dante», «moliere» y
   «agatha christie» no encuentran sus libros, efecto del endurecimiento del
   nombre del reinicio 19. Va al reinicio 23.

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
El arreglo es buscar también dentro del nivel del lector, y va el primero en
el reinicio 23.

## Lo que queda

| Qué | Quién | Cuándo |
|---|---|---|
| Reinicio 22: autor más título, anuncios de drogas, tres menores de subidas | f4, con visto bueno de 4e y e6 | esta madrugada |
| Reinicio 23: **recuperación dentro de la franja del lector (caso Esmeralda)**, autores clásicos, obras antes que biografías, «luna» y «rosa» con B1, 89 libros sin título, 42 textos que no están en inglés, título del capítulo en «Mis palabras» | f4 | después del 22 |
| Auditoría de voz de la ronda 3 | f4 | después del 22 |
| Ensayar con cuenta y micrófono: explicación de la IA, «Corrígeme», lectura natural, «Mis palabras», demo cronometrada | **Miguel** | fin de semana del 19-20 |
| Auditoría ciega del estado final | Codex | 19 de septiembre |
