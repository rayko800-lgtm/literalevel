# Qué hizo Codex la noche del 13 de septiembre, y si valió la pena

Para Miguel. Escrito por la sesión central el 14 de septiembre a mediodía, con
los datos del repositorio: cada afirmación tiene su commit o su archivo.

## En una frase

Sí ayudó: encontró seis fallos reales que nadie había visto, arregló dos y los
desplegó, integró la boca 3D en la app y blindó el desplegador. Pero lo hizo
lanzando **cuatro agentes a la vez durante una hora**, y eso se comió el cupo
semanal entero; y dos de sus cambios crearon trabajo extra: reescribió el guion
del vídeo, que hubo que fusionar, y su publicador del front dejó la app sin
motor unos minutos al día siguiente.

## Dónde se fue el cupo

El cupo de Codex es semanal y de la cuenta, no del modelo. Ese día se gastó en
tres tandas:

| Hora | Quién lo lanzó | Qué | Resultado |
|---|---|---|---|
| 16:17 a 16:48 | Tú, desde la app | Auditoría del léxico (commit `5033e69`) | Informe `auditoria/codex_lexicon_5033e69.md`: 1 alto y 3 serios, **los 4 confirmados y corregidos** |
| 16:49 a 17:10 | La central, por `codex exec` | Comprobación de cupo + auditoría de la API | 15.628 tokens la comprobación y 38.991 la auditoría, que **murió sin informe** por cupo |
| 20:51 a 21:51 | Tú, desde la app, con permiso de trabajar y desplegar | Sesión de una hora con **cuatro agentes en paralelo** (principal, portadas, Blender, API) | 16 commits, 7 informes, un despliegue; **cupo agotado hasta el viernes 19 a las 8:56** |

La tercera tanda es la que lo vació. No fue mal uso: es cómo trabaja la app de
Codex cuando se le da un encargo amplio. Cuatro agentes leyendo el proyecto
entero a la vez cuestan cuatro veces lo que uno.

## Lo que hizo, commit a commit, y qué pasó después con cada cosa

### Valió la pena y se quedó

- **Auditorías de API y voz** (`codex_api_relevo_2026-09-13.md`,
  `codex_voz_relevo_2026-09-13.md`): 4 hallazgos en la API y 2 en la voz.
  **Los 6 eran ciertos**. e6 y 4e los verificaron con el código delante y los
  arreglaron: dos sinopsis simultáneas pagaban doble, la devolución de un uso
  podía ir a otra cuenta si cambiabas de sesión, olvidar un libro no liberaba
  el cupo de subidas, el audio de una palabra se pagaba dos veces en paralelo,
  y la migración de la base de voz tenía una carrera.
- **Dos arreglos suyos, desplegados por él** (`a87caa8` en la API, `71e4b52`
  en la voz; Space `e56cf08`): el temporal de audio se crea antes de cobrar y
  el audio repetido no se paga dos veces. e6 los pasó por las 35 pruebas y 4e
  por las suyas: correctos. 4e afinó después dos detalles menores.
- **Integración de la boca 3D en Pronunciar** (`ca75ef4`, `56e0893`,
  `0132ddc`): tomó la rama de b9, la metió en la pantalla del front y escribió
  un guion de prueba de seis escenarios que b9 y e6 siguen usando. Tú lo
  encendiste al día siguiente.
- **Cara de Blender** en la rama 3D (`9ae5494`): nariz de perfil, faringe,
  garganta y labios. b9 lo validó y siguió encima. Sus labios eran una malla
  fija que se escalaba; b9 los sustituyó por deformaciones de verdad.
- **Guardas en el desplegador** (`7e68a54`, `0aec4ee`): ya no se puede subir
  un archivo con cambios sin commit, ni pisar un despliegue concurrente, y se
  escanean los bytes exactos que salen. f4 las conservó todas.
- **Frenos de gasto en el cuaderno de portadas** (`0a2cd1c`): no arranca sin
  tarifa, saldo, medición previa y muestras aprobadas. f4 confirmó que no tocó
  su diseño.
- **Documentos de relevo** para la central (`relevo_codex_2026-09-13_noche.md`
  y compañía): dijeron qué había hecho, qué no y qué dejaba en cola. Fue lo
  que permitió retomar a medianoche sin adivinar.

### Costó trabajo extra

- **Reescribió el guion del vídeo y la presentación** (`13281a9`: 420 líneas
  nuevas y 848 borradas). Acortó el guion de b9 de 601 a 480 palabras y quitó
  afirmaciones: una era falsa (la traducción «en 40 milisegundos»), otras solo
  prudentes, y otras verdaderas que no debió quitar (la búsqueda en español,
  que el profesor pidió el front). 4e comparó las dos versiones y escribió la
  fusionada de 496 palabras que tienes para aprobar. Sin la reescritura, ese
  paso no habría hecho falta.
- **Publicador del front** (`f658288`): la primera vez que e6 lo usó, publicó
  la app **sin la dirección del motor** y estuvo rota unos minutos. Causa: el
  build minifica una etiqueta y el parser recibía vacío. e6 lo arregló con una
  prueba. La herramienta se usa desde entonces.
- **Su comparación del desplegador mentía** por los finales de línea de
  Windows: marcaba cuatro archivos como distintos que eran idénticos. f4 lo
  corrigió comparando texto normalizado.
- **Sus pruebas de la API dieron «32 de 35»** porque su entorno no tenía spaCy.
  No era un fallo real, pero hubo que comprobarlo.
- **Su relevo decía que no integraría el 3D en la app**, y media hora después
  lo integró (con tu permiso). No es grave, pero obligó a leer dos veces.

### Retoques de documentos

- `46819e7` y `f72c446`: documento, estrategia, notebook y mensaje al profesor
  con prudencia (quita el precio operativo presentado como vigente y una
  afirmación no medida sobre lectores). Se conservaron; b9 y 4e actualizaron
  encima las cifras al día siguiente.

## Balance

| | Cuenta |
|---|---|
| Fallos reales encontrados por Codex ese día | 10 (4 léxico + 4 API + 2 voz), todos confirmados |
| Arreglos suyos desplegados y validados | 2 |
| Cambios suyos que hubo que rehacer o arreglar | 3 (guion, publicador del front, comparación del desplegador) |
| Horas de verificación de las sesiones de Claude sobre su trabajo | unas 2 |
| Cupo semanal consumido | todo, en unas tres horas de uso repartidas en el día |

Verdad completa: **lo que mejor hace Codex es mirar tu código con otros ojos**.
Sus diez hallazgos son la mejor tanda de auditoría del proyecto en un solo día.
Lo que peor le sale es editar documentos y herramientas de despliegue a la vez
que audita: ahí creó tanto trabajo como el que ahorró.

## Qué haría la próxima vez

1. Codex **solo para auditar a ciegas**, una tarea estrecha por encargo, un
   agente, sin permiso de editar documentos ni desplegar. Es lo que dice la
   skill `auditar-con-modelo-externo`, y lo que dio los diez hallazgos.
2. Antes de lanzarlo desde la app, decidir **cuánto cupo se quiere gastar ese
   día**; un encargo amplio con varios agentes lo vacía en una hora.
3. Cuando vuelva el viernes 19, el mejor uso es **una auditoría ciega del
   estado final** antes de la demo: API, voz y lectura natural, con `git diff`
   acotado a los commits de esta semana. Eso cabe en un encargo y no toca nada.
