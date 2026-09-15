---
name: sesion-central
description: Ser la sesión «central» que Miguel usa como único punto de contacto cuando hay varias sesiones de Claude Code y Codex trabajando a la vez — cómo arrancar, qué pedir a cada sesión, cómo pedir permisos a Miguel una sola vez, cuándo avisarle al móvil, cómo lanzar a Codex desde aquí y qué skill dejar escrita al cerrar. Úsala cuando Miguel diga «este chat es la central», cuando otra sesión te pida que reportes por ella, o al empezar una tarde con más de dos sesiones abiertas.
---

# La sesión central

Nació el 13 de septiembre de 2026 por la tarde. Había tres sesiones de Claude
Code en la misma carpeta (front Angular, motor de voz y léxico, despliegues y
corpus), dos subagentes en segundo plano, un worktree de Fable y la app de Codex
abierta. Miguel no podía seguirlas y pidió una sola sesión que lo hiciera por
él: **aquí se le reporta, aquí se le pide permiso, y aquí se le avisa al móvil**.
Esta skill es lo que funcionó. El protocolo entre sesiones (reparto, commits en
carpeta compartida, entregas con hash) está en `trabajar-en-equipo` y no se
repite aquí.

> **La regla que lo ordena todo:** la central no edita código del proyecto.
> Recoge, decide el orden, pide permiso una sola vez y reparte la respuesta.
> Si se pone a programar, deja de ser la central y nadie coordina.

---

## 1. Arranque (diez minutos, siempre igual)

1. `ListAgents`. Apunta los nombres con su `[ref]`: son la dirección.
2. A **cada** sesión viva, el mismo mensaje con seis preguntas: (1) tarea y
   qué ha hecho ya, con hashes; (2) archivos enteros y funciones concretas que
   toca; (3) lo que NO toca; (4) procesos largos en marcha, con PID; (5) qué
   necesita de Miguel o de otra sesión; (6) commits pendientes y de qué rutas.
   Añade la orden: «a partir de ahora, decisiones de Miguel y despliegues pasan
   por mí». Manda los tres mensajes en la misma respuesta, con
   `notify_when_idle: true`, y sigue: contestan en uno o dos minutos.
3. Mientras contestan, no te quedes esperando: lee la tabla de reparto de
   `AGENTS.md`, `git status`, `git worktree list` y los últimos archivos de
   `auditoria/`. Con eso sabes quién dice la verdad y qué falta.
4. **Codex no es una sesión.** No aparece en `ListAgents`. Mira si hay un
   `codex exec` vivo con la línea de comandos de los procesos:
   `Get-CimInstance Win32_Process | ? Name -match codex`. Dos `codex.exe
   app-server` son la app de escritorio y la extensión de VS Code, **no un
   encargo**. Sin un `codex exec`, Codex está parado aunque parezca ocupado.
5. Corre `python -X utf8 tools/desplegar_app.py --seco` (solo lectura, tarda
   un minuto): te dice qué archivos del Space difieren de HEAD. Es la única
   forma de saber qué despliegue está pendiente de verdad, mejor que lo que
   diga cualquier sesión.

Esa tarde el arranque destapó que **dos sesiones esperaban permiso para el
mismo reinicio del Space**, cada una por su lado, y que la desplegadora ya
había propuesto juntarlos. Sin central, Miguel habría autorizado dos reinicios.

---

**El nombre del chat es la dirección.** Al renombrar la sesión con `/rename`
(Miguel lo hizo tres veces esa tarde hasta dar con «[Central]»), el nombre
que las demás usan para escribirte cambia con ella: f4 intentó mandar un
informe a «entrega-35» y ya no existía. Después de cada `/rename`, corre
`ListAgents`, copia el nombre exacto con su `[ref]` y mándaselo a todas las
sesiones. Y si aparece una sesión nueva en `ListAgents`, pídele el reparto
igual que a las primeras: Miguel abre chats sin avisar.

## 2. Pedir permiso a Miguel: una vez y todo junto

- Junta todo lo que está parado esperando una decisión y pregúntalo en **un
  solo `AskUserQuestion` con varias preguntas**, cada una con la opción
  recomendada primero y el coste real en la descripción («reinicia el Space
  un minuto: no grabes en Pronunciar»). Miguel responde a todo de golpe.
- **Antes de la pregunta, `PushNotification`** con una línea que diga qué se
  espera de él. Si está delante del ordenador, la herramienta dice «not
  sent» y no pasa nada; si no está, es lo que lo trae de vuelta. Miguel lo
  pidió expresamente: avisar al móvil cuando se le necesite.
- **Miguel puede haber contestado ya en otro chat.** Esa tarde autorizó el
  despliegue a la desplegadora directamente mientras yo se lo preguntaba
  aquí. No pasa nada: la central confirma por mensaje a las sesiones, y así
  todas saben que la autorización existe y quién la tiene.
- Al reenviar la autorización, añade lo que la sesión tiene que devolver:
  hash del commit del Space, el JSON de `/api/salud`, y a quién avisar.

## 3. Ordenar el trabajo: qué dejas en paralelo

Lo que no comparte archivos ni Space va a la vez. Esa tarde, en paralelo:

| Sesión | Qué | Por qué no choca |
|---|---|---|
| desplegadora | dos tandas de tres sesiones en **un** reinicio de Gradio | única que toca el Space de Gradio |
| front | republicar el Space estático (`dist/` solo) | otro Space, no reinicia Gradio |
| motor | dos subagentes que solo crean archivos nuevos | no tocan `ui.py` hasta integrar |
| central | auditoría de Codex a ciegas sobre un commit ya hecho | solo escribe un `.md` en `auditoria/` |

Y en secuencia, con dirección única: la desplegadora prueba en local que la
API de una sesión casa con el `ui.py` de otra **antes** de subir; la sesión del
motor integra a sus subagentes en `ui.py` **antes** de pedir despliegue; el
front consume los nombres nuevos del motor **después** del commit del motor.

**Un solo desplegador de Gradio.** Se dice en el mensaje de autorización a
todas las sesiones, no solo a la desplegadora, para que nadie «suba de paso».

## 3b. Un «idle» sin informe es una parada, no un descanso

A las 18:28 llegaron dos avisos automáticos de sesión libre (e6 y f4) y a
las 18:40 un tercero (b9), **sin que ninguna hubiera mandado el informe que
se le había pedido**. Los di por avisos rezagados, como otros anteriores que
sí lo eran, y a las 19:10 Miguel escribió «reactiva todo»: cuarenta minutos
con el Space sin el reinicio pendiente y sin la prueba final. Regla: cuando
llega un idle de una sesión a la que se acaba de mandar trabajo y no hay
informe suyo, **se le escribe en cinco minutos**, con dos preguntas: «¿estás
bloqueada en un permiso de tu chat? ¿cuál?» y el siguiente paso concreto.
Un permiso pendiente en otro chat solo lo puede contestar Miguel allí, así
que la central se lo dice a él con el nombre de la sesión. Distinguir un
idle rezagado de una parada es fácil: el rezagado llega **antes** del
informe de esa sesión; la parada, **después** de la última orden y sin
informe.

La causa real esa tarde, vista en una captura de Miguel: **las sesiones
habían chocado con el límite de gasto mensual de Claude** («You've hit your
monthly spend limit · your session limit resets 7:10pm»), y ninguna podía
decirlo por mensaje porque ninguna podía correr. La central no lo ve: sus
mensajes se encolan y llegan todos juntos cuando el límite se reinicia (f4:
«tus dos mensajes me llegaron juntos»). Señales: varios idles a la misma
hora sin informe, y `ListAgents` con todas en `idle`. Qué hacer: mirar el
panel «Account & Usage» de la extensión (o pedirle a Miguel una captura),
apuntar la hora de reinicio y, si queda trabajo que no depende de Claude
(Codex, un `codex exec` ya lanzado, un despliegue en marcha), dejarlo
correr. Y en cualquier caso: una orden importante no está entregada hasta
que la sesión la acusa; si en cinco minutos no hay acuse, se reenvía en una
línea.

**Se repitió el 14 por la mañana**: a las 06:52 cayeron a la vez las cuatro
sesiones y la central, y nadie volvió hasta las 10:12. Tres horas y veinte
minutos sin reinicio y con un despliegue a medio ordenar. Lo que sí siguió
fue el proceso de medición de f4, porque era un `python` en segundo plano y
no dependía de Claude: terminó solo a las 07:57. Dos reglas más:

- Cuando la central vuelve de un límite, **da por hecho que las demás
  también cayeron**: `ListAgents` con todas en `idle` y `git log` sin
  commits desde la misma hora lo confirman. Reactívalas en el mismo
  mensaje con su siguiente paso y la frase «si tenías algo a medias, dime
  el estado en una línea y continúa».
- **Lo que tenga que sobrevivir a un límite va como proceso del sistema**
  (medición, descarga, banco de mutantes), reanudable por shards, nunca
  como turno de una sesión.

## 4. Lanzar a Codex desde la central

La central es el sitio natural para encargar la auditoría externa: no ha
escrito el código que se audita, así que el encargo sale a ciegas sin
esfuerzo. Pasos, todos de `auditar-con-modelo-externo`:

0. **Mira primero si el informe ya existe.** `ls -lt auditoria/ | head`. Esa
   tarde Miguel ya le había dado el encargo a Codex desde su app y el informe
   estaba en disco desde las 16:48; el mío, lanzado a las 16:50 con el mismo
   archivo de salida, lo habría sobreescrito. Se vio a tiempo por la hora del
   archivo, y hubo que matar mi `codex exec` con `Stop-Process`. Regla: un
   encargo que otra sesión ya propuso puede estar hecho; pregunta a Miguel
   «¿ya se la diste?» solo si el archivo no está.
1. `codex exec --skip-git-repo-check -m gpt-6-astra "Responde solo: ok"`. Si
   contesta, hay cupo (esa tarde: 15.628 tokens la llamada de una palabra, por
   el contexto que carga). Si dice `usage limit`, apunta la hora de vuelta.
   **Que conteste no dice cuánto queda.** A las 16:49 contestó; a las 17:10 el
   encargo de la API murió a los 38.991 tokens sin informe, porque la
   auditoría de lexicon que Miguel había lanzado desde su app una hora antes
   se había comido el cupo de la ventana. La ventana volvía a las 21:40 (unas
   cuatro horas y media, no una semana). Lección: si esa misma tarde ya hubo
   un informe de Codex, cuenta con que el siguiente encargo no cabe, y
   **encadena las pasadas con `;` solo si la primera es la que más importa**:
   la segunda muere igual, y de paso te confirma la hora de vuelta.
   Programa el relanzamiento con `CronCreate` para cinco minutos después de
   esa hora, en vez de reintentar en caliente.
2. Escribe el encargo en un `.txt` del scratchpad y lánzalo con
   `"$(cat encargo.txt)"`, en **segundo plano** con salida a un `.log`. Tarda
   varios minutos y la central tiene que seguir contestando mensajes.
3. Encargo estrecho: un commit, cinco preguntas numeradas, `grep` en vez de
   leer archivos enteros, un solo archivo de salida en `auditoria/`, y
   prohibido leer el resto de `auditoria/`.
4. Cuando llegue el informe, **no lo corrige la central**: cuenta, clasifica
   y se lo pasa a la sesión dueña del código con la lista de hallazgos, para
   que verifique cada uno con el código delante (`corregir-sin-inventar`).

## 4b. Codex puede entrar por su cuenta, con permiso de Miguel

La noche del 13 al 14 de septiembre, mientras las sesiones de Claude
estaban paradas por el límite de gasto, Miguel abrió Codex en su app y le
dio permiso directo para trabajar y desplegar. En una hora (20:51 a 21:51)
Codex hizo 20 commits en master: desplegó él el backend (api.py y voz.py),
cambió `tools/desplegar_app.py`, integró la rama 3D en Pronunciar, reescribió
guion y presentación, y escribió sus propias auditorías de API y voz. De
paso **agotó el cupo semanal de Codex** (vuelve el 19 sep), así que el
relanzamiento programado a las 21:46 murió en la llamada de una palabra.

Qué hacer la central cuando pase:

- **Leer primero `auditoria/relevo_codex_*.md`**: Codex lo escribe para la
  central, enlaza desde `CLAUDE.md`, y dice qué desplegó (hash del Space),
  qué no tocó y qué deja en cola. También lee la transcripción de la central
  para situarse: es la sesión que mejor sabe lo que pasó.
- `git log --format='%h %an %ad %s' <último hash conocido>..HEAD` y
  `list_repo_commits` de los dos Spaces con `huggingface_hub`: la verdad
  está ahí, no en la tabla de `AGENTS.md`.
- **Repartir la verificación por dueño**: cada sesión revisa los commits de
  Codex en sus archivos con sus pruebas, y no se despliega nada más hasta
  que digan si lo dejarían así. Codex no pudo correr `pruebas_api` entera
  (le faltaba spaCy en su venv): un «32/35» suyo no es un fallo real.
- **Cron y cupo**: si hubo un informe de Codex esa tarde, el cron de
  relanzamiento no va a caber. Antes de programarlo, pregunta a Miguel si va a
  usar Codex él; si sí, no lo programes.

## 5. Lo que se guarda al cerrar

- Fila en `AGENTS.md` con quién hizo qué y qué hash quedó desplegado.
- Memoria `sesion-central` en la carpeta de memoria de Claude: Miguel quiere
  este modo de trabajo siempre que haya más de dos sesiones.
- **Esta skill, actualizada** con lo que falló esa tarde. Miguel lo pidió con
  estas palabras: «ve generando skills de todo el proceso, entrena con lo que
  hemos hecho». Cada tarde de central añade una sección, no un archivo nuevo.

## 6. Lista de comprobación

**Al empezar**
- [ ] `ListAgents` y mensaje de seis preguntas a cada sesión, con `notify_when_idle`.
- [ ] `AGENTS.md`, `git status`, `git worktree list`, procesos de Codex.
- [ ] `desplegar_app.py --seco` para saber qué despliegue falta de verdad.

**En cada decisión**
- [ ] Todo lo parado, en un solo `AskUserQuestion`; `PushNotification` antes.
- [ ] Autorización reenviada a todas las sesiones, con lo que deben devolver.

**Al cerrar**
- [ ] Hash desplegado confirmado por la desplegadora, no por la tabla.
- [ ] Informe de Codex entregado a la sesión dueña, no corregido aquí.
- [ ] Fila en `AGENTS.md` y esta skill actualizada.

## 6b. Cupo por modelo: una sesión en Fable se para sola

El 14 sep por la noche la central, que corría en Fable, se quedó sin cupo de
Fable y siguió en Opus; b9 se paró a la vez y dejó de acusar órdenes sin
decir nada. El panel «Account & Usage» tiene un límite propio para Fable
(«Fable limit»), aparte del de sesión y el semanal. Señales: una sola sesión
en `idle` sin acuse mientras las demás trabajan, y ningún cambio suyo en
disco. Qué hacer: redistribuir su tarea a una sesión libre en el acto (no
esperar) y decirle a Miguel que, si quiere recuperarla, escriba `/model opus`
en ese chat. El límite de gasto mensual es otra cosa: se sube en
claude.ai/settings/usage, y eso es dinero de Miguel, así que solo se le
explica y decide él.

## 7. El commit que se lleva líneas ajenas

El 14 sep a las 15:15, e6 hizo commit de `app/api.py` y `app/ui.py` enteros
para unos plurales y arrastró cinco llamadas de f4 a una función que aún no
existía en ningún commit (`ficha.para_medir`). HEAD dejó de poder medir. La
regla ya estaba en `trabajar-en-equipo` (rutas explícitas y `git apply
--cached` solo con los bloques propios); lo que faltaba era la red de la
central: **después de cada commit sobre un archivo compartido, la central
comprueba que HEAD importa y pasa la suite corta** (`python -X utf8
tests_smoke.py`), o se lo pide a f4 antes de cualquier reinicio. Y cuando
dos sesiones editan el mismo archivo a la vez, la central lo sabe (lo dijo
f4 media hora antes): en ese momento hay que avisar a las dos de que solo
suban sus hunks.

## 8. El disco se llena solo cuando hay cuatro sesiones

La madrugada del 15 de septiembre C: llegó a 0 GB con 819 GB libres en D:.
Una sesión no podía ni abrir la salida de sus propios comandos (ENOSPC en
%TEMP%) y un cálculo largo se cortó. Causas: copias de árbol limpio de 25 MB
por reinicio en el scratchpad, diferencias de edición del arnés (unos 30 MB
cada una), volcados de memoria de Chrome y temporales de días anteriores.
Cambiar `TEMP` y `TMP` a `D:\Temp` solo afecta a los procesos que arrancan
después: **las sesiones ya abiertas siguen escribiendo en C:**.

- Antes de una tarde con cálculo pesado, mira `Get-PSDrive C`. Por debajo de
  5 GB, libera antes de lanzar nada.
- Lo pesado va a `D:\literalevel_tmp` por orden explícita en el encargo:
  árboles limpios, banco de mutantes, perfiles de Chrome, volcados.
- Borrable sin preguntar, con el permiso general de Miguel para lo
  regenerable: `.tmp` de más de dos días en %TEMP% y carpetas de
  `Temp/claude/bash-edit-diff` de más de tres horas. Los scratchpads de otras
  sesiones vivas no se tocan: se le pide a su dueña.
- Los procesos que escriben por partes con temporal y renombrado sobreviven a
  un disco lleno; los que escriben directo, no. Pídelo así en cualquier tanda
  larga.
- Cuando la ronda acabe, reinicia las sesiones de una en una para que tomen
  los temporales de D:.

**La causa de fondo, encontrada media hora después:** no eran los árboles ni
los volcados. Ocho suites crean su carpeta de datos con `tempfile.mkdtemp` y
**nunca la borran**: `pruebas_extremas.py` y `pruebas_corpus.py` dejan 100 MB
por corrida, y el banco de mutantes corre la suite una vez por mutante. Había
1.002 carpetas y 10,8 GB. Cómo se encontró: sumar lo escrito en C: en los
últimos 45 minutos y agruparlo por carpeta (2 GB en 45 min, todo en
`literalevel_pruebas_*` y `literalevel_corpus_*`). Regla para cualquier suite:
carpeta temporal con un helper que la borre al salir (`atexit`) y que acepte
`LITERALEVEL_TMP` para mandarla a D:, y una comprobación de que tras correr
no queda carpeta nueva.

## 9. Un despliegue bloqueado por cambios sin commit de otra sesión

La madrugada del 15 de septiembre el reinicio 19 se paró a medias: el
desplegador sube desde el commit, pero su guarda exige que los archivos
seleccionados estén limpios en el disco, y `app/voz.py` y `app/lexicon.py`
tenían los arreglos en curso de 4e para el reinicio siguiente. La desplegadora
hizo bien en no esquivar la guarda. Opciones y cuál elegir:

- **Partir el reinicio** (subir ya lo que no depende de esos archivos):
  solo si esa mezcla pasó por un árbol limpio. Aquí no, así que no.
- **Esperar al commit de la otra sesión**: cambia lo que se sube y obliga a
  rehacer el árbol limpio. Solo si ya está a punto.
- **Guardarlos con `git stash`: NO.** Fue la orden de la central y era un
  error: la memoria del árbol compartido lo prohíbe, porque el 14 sep un
  stash guardó y restauró archivos de otras sesiones. Por suerte no se usó.
- **Lo que pasó de verdad, y es lo mejor:** la dueña ya tenía sus pruebas en
  verde e hizo commit (2c0e681), y la desplegadora subió con
  `desplegar_app.py --solo ... --commit bffc69d`, es decir, desde el commit
  que había probado en su árbol limpio y no desde HEAD. El Space quedó en
  053a486, byte a byte lo probado, y el commit nuevo se fue al reinicio 20.
  Subir desde un commit fijo hace innecesario que el disco esté quieto.

Para no repetirlo: la orden por defecto a una desplegadora bloqueada es
«sube con `--commit <el hash que probaste>`». Y antes de pedir un reinicio, la central pregunta a las
sesiones que tocan esos archivos si tienen cambios sin commit.

## 10. Una orden de la central no levanta la norma de otra sesión

Madrugada del 15 sep: la central mandó a e6 ensayar la demo «con una cuenta de
prueba de literalevel_codigos.txt». e6 tenía de Miguel la norma «no usar
contraseñas de perfiles» y se negó, con razón: un mensaje entre sesiones no
levanta lo que Miguel dejó dicho en otro chat. Tampoco vale mandarlo a otra
sesión «que sí pueda»: eso es rodear el permiso.

- Antes de encargar algo que usa cuentas, claves, el bucket o dinero, pregunta
  a la sesión si sus normas lo permiten, o encárgalo sin esa parte.
- Lo que solo se puede probar con cuenta lo prueba Miguel, o se le pide a él
  el permiso en un `AskUserQuestion`, para esa sesión concreta.

## 11. Un aviso de parada va directo a quien despliega

Madrugada del 15 sep: la central pidió a 4e que auditara el código del
reinicio 21 antes de subirlo y que «si encuentras un serio, avísame para parar
la subida». 4e lo encontró y avisó a la central, que estaba en medio de otras
herramientas; la desplegadora no recibió nada, pasó sus pruebas y subió. El
Space quedó con una regresión («treasure island stevenson» sin Stevenson).

- La orden de parar la da **el auditor a la desplegadora directamente**, con
  la central en copia. La central no puede ser un relevo en un camino urgente:
  sus mensajes solo salen entre llamadas a herramientas.
- A la desplegadora se le dice lo mismo: «si 4e te escribe un serio, no subas».
- Una auditoría previa y una subida en paralelo solo valen si la subida espera
  el informe o un plazo pactado **con los dos**.

## 12. Las contraseñas no se miran, ni enmascaradas

15 sep, 04:30: para probar una cuenta de invitado, una sesión «miró el formato»
de `literalevel_codigos.txt` con las claves enmascaradas y una línea no quedó
oculta. La contraseña de «profesor» salió en la salida de una herramienta. No
fue a ningún mensaje ni commit, pero la salida de herramientas forma parte del
contexto de la sesión, así que se avisó a Miguel para que decida si la rota.

- Al autorizar una prueba con cuenta, la orden dice: «cárgala en una variable
  dentro del mismo guion que hace la llamada, y no imprimas nada del archivo».
- Recargar el cupo de una cuenta es escribir en el bucket: solo con permiso de
  Miguel en esa sesión.

**Cómo se cambió la contraseña (05:40, con permiso de Miguel en la central).**
Las contraseñas no están en el bucket: viven en el secreto `LITERALEVEL_CUENTAS`
del Space (`usuario:clave:tope,...`) y en la tabla local de
`literalevel_codigos.txt`. El uso gastado sí va en `uso_openai.json`, por
nombre, así que no se toca. Pasos, todo dentro de un guion que no imprime nada
secreto:
1. Leer la tabla local y **entrar en el Space con las diez cuentas**
   (`POST /api/entrar` con un X-Lector de prueba y luego `/api/salir`): si
   todas entran, el archivo coincide con el secreto y se puede reconstruir.
2. Copia del archivo al scratchpad, clave nueva con `secrets` (sin «:» ni «,»),
   sustituir solo la celda de esa cuenta.
3. `HfApi(token=~/.hf_token).add_space_secret(...)` con el valor completo; el
   Space se reinicia solo (unos 50 s). Avisar antes a la desplegadora.
4. Comprobar: la nueva entra, la vieja no, otras cuentas siguen y los usos no
   cambian. Solo entonces borrar la copia.

## 13. La regla de «sube lo que tenga ok» no vale para archivos acoplados

Para no bloquear una subida se pactó «si un visto bueno tarda más de 30
minutos, sube solo lo aprobado». En el reinicio 25 la API nueva llamaba a
funciones que solo existían en el catálogo nuevo: subir api.py solo habría
dejado todas las búsquedas en 503. La desplegadora lo vio y paró.

- Antes de pactar una subida parcial, pregunta si los archivos dependen entre
  sí (una función nueva, un campo del contrato, un .npy que el código espera).
- Si dependen, la regla es **juntos o nada**, y el plazo solo sirve para avisar.
- Y con cuatro sesiones en la misma máquina, mira la RAM antes de un árbol
  limpio: bancos de mutantes con el catálogo cargado y `ng serve` olvidados
  dejaron 2 GB libres y las suites fallaron por memoria, no por código.
