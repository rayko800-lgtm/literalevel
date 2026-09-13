---
name: trabajar-en-equipo
description: Coordinar varias sesiones de Claude Code, subagentes en worktree y modelos externos (Codex/Astra, Fable) sobre el mismo repositorio sin pisarse ni quedarse esperando unos a otros — qué va en paralelo y qué en secuencia, cómo repartir archivos, cómo pasar el testigo y cómo hacer commit en una carpeta compartida. Úsala al empezar una noche con más de una sesión abierta, al lanzar un subagente que toca código, al recibir un mensaje de otra sesión, o antes de desplegar.
---

# Trabajar en equipo sin pisarse

Nació la noche del 12 de septiembre de 2026. Dos sesiones de Claude trabajaban
a la vez en la **misma carpeta** (`C:\Users\laura\literalevel`): una con los
corpus graduados y otra con el feedback de Laura. Además había un subagente
en un worktree generando los audios de fonemas del AFI. Salió bien, pero
rozó cuatro accidentes. Esta skill los convierte en reglas.

> **La regla que lo ordena todo:** en paralelo va lo que no comparte archivos
> ni necesita el resultado de otro. **Todo lo demás es una entrega con
> dirección única**: uno produce, avisa con hash y rutas, y el otro consume.
> Nunca dos esperándose a la vez.

---

## 1. Al empezar: el reparto, por escrito y por mensaje

Antes de tocar nada, cada sesión manda a las demás **una lista de lo que va a
tocar**, con este nivel de detalle:

- **Archivos enteros** que son suyos esta noche.
- **Funciones concretas** dentro de un archivo compartido. En `app/ui.py` no
  vale «ui.py», porque hay 4.000 líneas y las dos sesiones lo tocan. Vale
  «`construir()` en la cabecera, `_CSS_GLOBAL` y `_practicar`».
- **Lo que NO va a tocar**, que es lo que evita las sorpresas.
- **Procesos largos en marcha** que no hay que matar. Esa noche eran dos
  descargadores que comían CPU y parecían colgados.

Luego se deja constancia en la tabla de `AGENTS.md`, que es lo que lee quien
llegue mañana (Codex incluido).

**Para descubrir quién hay:** `ListAgents`. Para hablarles: `SendMessage`
con el `from=` del mensaje recibido como `to`. La primera línea del mensaje
tiene que entenderse sola, porque es lo único que ve el humano de la otra
sesión.

---

## 2. Qué va en paralelo y qué en secuencia

| En paralelo, sin esperar | En secuencia, con entrega |
|---|---|
| Tareas sobre archivos distintos | Dos cambios en la misma función |
| Investigación que solo escribe un `.md` nuevo | Documentar una cifra **después** de medirla |
| Un subagente en worktree con zonas acotadas | Fusionar la rama del subagente **antes** de auditar |
| Una auditoría externa ciega sobre un commit ya hecho | Desplegar **después** de que todos hayan hecho commit |
| Pruebas de cada uno sobre su parte | La prueba final con todo junto, justo antes de desplegar |

**Un solo desplegador por noche.** Se decide al principio. Desplegar sube lo
que haya en la carpeta. Esa noche el catálogo externo de la raíz era de
**prueba** (85 filas) y un despliegue «de paso» lo habría publicado.

---

## 3. El protocolo de espera (cómo no bloquearse)

1. **Solo hay puntos de espera declarados**, y cada uno con una dirección:
   «A espera a B para X». Si A espera a B, B no puede esperar a A: B sigue con
   su cola.
2. **Nadie espera sin plazo.** Si en **45 minutos** no llega el aviso, el que
   espera sigue con su cola propia y lo dice por mensaje.
3. **Cada «espero» dice qué hace mientras tanto.** Un «espero tu commit» a
   secas es el principio de un bloqueo mutuo.
4. **Las entregas llevan todo lo necesario para no preguntar**: hash del
   commit, rutas exactas y lo que el otro tiene que hacer con ellas.

Plantilla de fases que funcionó:

```
FASE A (paralelo)  cada uno termina y hace commit de lo suyo
ENTREGA 1 (A→B)    hash + rutas nuevas que B necesita (p. ej. binarios a la lista blanca)
FASE B (paralelo)  B integra, prueba todo junto y despliega · A audita a ciegas lo suyo
ENTREGA 2 (B→A)    hash desplegado + «cotejado por hash»
FASE C             A prueba el despliegue de verdad y pasa lo que falle
```

---

## 4. Commit en una carpeta compartida

Con dos sesiones en la misma carpeta, **`git pull --rebase` no protege
nada**: no hay nada que traer, los cambios del otro ya están en tu disco.

- **Nunca `git add -A`, `git add .` ni `commit -a`.** Solo rutas explícitas.
- **Si un archivo tiene bloques tuyos y del otro**, no se añade entero. Se
  saca `git diff`, se descartan los bloques ajenos y el resto se aplica al
  índice con `git apply --cached -`. Después se comprueba que el archivo
  del índice compila: `git show :app/ui.py`, y luego `compile()`. El guion
  debe **negarse a tocar el índice** si no encuentra exactamente los bloques
  ajenos que esperaba. Esa noche abortó a tiempo: el otro ya había hecho
  commit de los suyos y el diff era distinto del que se había mirado.
- **Relee justo antes de editar.** La herramienta Edit falla con «modified
  since read» cuando la otra sesión ha escrito en el archivo, y hay que volver
  a leer la zona. No es un error: es la señal de que alguien más está ahí.
- **Las pruebas pasan sobre la carpeta con los cambios a medias del otro.** Si
  algo falla, mira de quién es la línea antes de arreglarlo.

---

## 5. Subagentes en worktree

Un worktree aísla el código, pero **no los datos**. Tres trampas medidas:

- **Los datos pesados no están** (`modelo_v4/`, `kaikki_diccionario.db`,
  `.env`), porque están en `.gitignore`. Dile al agente dónde están en la
  carpeta principal y que apunte con `LITERALEVEL_MODELO` y
  `LITERALEVEL_DICCIONARIO`, **sin copiar la clave** a nada versionado.
- **Nunca se despliega desde un worktree.** Git en Windows extrae los `.csv`
  con CRLF: `catalogo_medido.csv` pasaba a pesar 14.941.595 bytes, el hash no
  coincidía con el del Space y se habrían resubido 15 MB convertidos.
- **Acota las zonas de los archivos compartidos.** Si otra sesión cambia
  `construir()`, el agente solo toca `_practicar` y lo imprescindible del
  cableado. Así la fusión no choca.

**Un agente que «se queda esperando» a sus propios procesos en segundo plano
puede terminar sin haber hecho commit.** Si llega su aviso de fin diciendo
«espero a la pasada y a las pruebas», reanúdalo con `SendMessage`. Dile que
esos procesos ya han acabado (si no, no habría llegado el aviso), que mire sus
salidas en disco, que corra las pruebas en primer plano y que haga commit.

Si le llega información nueva del usuario a mitad (esa noche: «no entiendo el
sonido W»), mándasela con `SendMessage` en vez de esperar a que acabe.

---

## 6. Codex (Astra) y Fable: auditores, no coeditores

Otro modelo aporta **otros puntos ciegos**, y ese es todo su valor. Por eso su
papel natural es **auditar un commit ya hecho, a ciegas**, no editar a la vez
los mismos archivos.

- **Codex** se lanza con `codex exec --skip-git-repo-check -m gpt-6-astra
  "<encargo>"`. **Antes de escribir el encargo, gasta una llamada de una
  palabra en comprobar el cupo**: el cupo es de la cuenta y no del modelo, y
  cuando se agota dice la fecha de vuelta, que puede ser de días. Todo lo de
  dimensionar el encargo está en `auditar-con-modelo-externo`.
- **Fable** se lanza como subagente con `model: fable`. Una auditoría completa
  ronda los 180.000 tokens: dale un alcance acotado, por ejemplo «los commits
  de esta noche», con `git diff <base>..HEAD`.
- **Codex es dueño de `reader.py`, `lexicon.py` y `voz.py`** según
  `AGENTS.md`. Si otra sesión los toca, la primera línea del commit lo dice, y
  Codex tiene que leer `git log` antes de volver a entrar.
- **Si dos familias coinciden en un hallazgo, es corroboración.** Si solo lo
  señala una, se verifica igual antes de tocar nada.

Reparto que funciona: la sesión que hizo el cambio **no audita su propio
trabajo**. Encarga la auditoría mientras la otra sesión despliega (fase B), y
verifica cada hallazgo con el código delante antes de corregir.

---

## 7. Verificar como una persona, no solo con pruebas

Esa noche **dos arreglos fallaron la primera vez con las 306 pruebas en
verde**:

- La cabecera del libro salía letra a letra en el móvil.
- El botón de siguiente capítulo no movía la página: el texto nuevo llega
  después del cambio de capítulo, había dos `#ll-lector` en la página, y los
  botones que pulsó la usuaria eran los de **debajo** del texto.

Solo se vio abriendo la app en Chrome controlado por el protocolo de
depuración, a 390 px **con emulación táctil**. Sin ella, Chrome sigue
diciendo `hover:hover` y las reglas de móvil no se aplican. El guion de
capturas y las trampas están en `probar-la-app-de-verdad`.

---

## 8. Lista de comprobación

**Al empezar**
- [ ] `ListAgents`: quién hay y en qué está.
- [ ] Mensaje de reparto: archivos, funciones, lo que no se toca, procesos vivos.
- [ ] Quién despliega esta noche.

**Antes de cada commit**
- [ ] `git status` y `git diff <archivo compartido>`: ¿hay bloques ajenos?
- [ ] Rutas explícitas; bloques filtrados si hace falta; el índice compila.
- [ ] Si tocas un archivo de otro dueño, dilo en la primera línea del commit.

**En cada entrega**
- [ ] Hash, rutas y qué tiene que hacer el otro.
- [ ] Qué haces tú mientras tanto y hasta cuándo esperas.

**Al cerrar**
- [ ] Fila en `AGENTS.md`.
- [ ] El desplegador confirma el despliegue por hash.
- [ ] Lo que queda pendiente, escrito donde lo lea la sesión de mañana.
