# Ensayo final del guion de la demo — 16 de septiembre de 2026

**Sobre qué se ensayó, las tres referencias:**

| Pieza | Revisión del Space | Commit |
|---|---|---|
| Front | `ec684196a6ded11e9db59da6d32789d6e45afb64` | `8a992af` |
| Motor | `72f3cdce0225a8ddd24d2ee68bfcf7332e23e75f` (RUNNING, `buscador_listo`) | `61e3bba` |
| Guion | — | `ad51d05` (`entrega/guion_demo_en_vivo.md`) |

Comprobado que el motor servido es ese commit: `app/ui.py`, `app/api.py`,
`app/voz.py` y `app/cuentas.py` del Space en `72f3cdc` coinciden blob a blob con
`61e3bba`.

**Cómo:** navegador a **390 × 844 px**, móvil y táctil, contexto limpio, **sin
cuenta y sin gastar nada**: ninguna corrección, explicación ni resumen. La
bienvenida **sin saltar**. El perfil de 1,20 se obtuvo con la receta del propio
guion.

**Lo que este ensayo no puede ver:** lo que pide cuenta o micrófono (pasos 5 y
6 con corrección, la explicación en contexto, la marca IA con cuenta) y los dos
textos nuevos del motor, que solo salen agotando un cupo o pagando una
corrección. Esos se comprueban contra el código servido (§3).

---

## 1. Bien

**Punto 8, el arranque.** Se puede hacer tal cual:
- `/api/salud` responde `"buscador_listo": true`.
- `gcTimeout` del Space es **172.800 s**, la cifra que cita el guion.
- La carga completa del front tarda **641 ms**: el «se pinta en 0,64 s».

**Punto 10, la bienvenida sin saltar**, los cuatro pasos tal como los describe
el guion:

| Contador | Título | Botones |
|---|---|---|
| **1 de 4** | **¿Ya tienes cuenta?** | Saltar · **Entrar** · **Seguir sin cuenta** |
| 2 de 4 | Libros en inglés a tu nivel | Saltar · Siguiente |
| 3 de 4 | Una palabra, en su frase | Saltar · Siguiente |
| 4 de 4 | ¿Por dónde empiezas? | Saltar · Medir mi nivel · Solo quiero leer |

Los textos del paso 0 son los aprobados, literales. «Medir mi nivel» lleva a
*Tu nivel*.

**Punto 11, las ayudas de la primera vez:** las dos salen literales —la del
lector y la de *Pronunciar*—.

**La receta del 1,20:** las seis respuestas existen en ese orden y dan «Lees en
inglés a nivel B2» y, en «Ver el detalle», «**1,20 de 2 · Intermedio**». El pie
dice «¿No te convence? Afínalo con un libro que ya leíste · con un texto · volver
a medirme».

**Paso 2:**
- «cuentos de dragones» → «En tu nivel», **20 tarjetas, 19 de licencia libre**.
- «una novela de detectives victoriana» → **3, las tres de Gutenberg**.

**Paso 3:**
- Aviso literal «De "Crimen y castigo de Dostoyevski" no hay libros en tu nivel ni
  un poco por encima entre los resultados. Estos son los de otros niveles.».
- *Crime and Punishment*, **el primero en «De otros niveles»**, a **679 px** sin
  pulsar nada.
- Ficha **C1 · 1,70 de 2**, con su curva.

**Paso 4:**
- El Índice está a **2,02 pantallas** de «Empezar a leer» («unas 2»).
- «Antes del primer capítulo» abre el capítulo 0.
- *poverty*: diccionario e IPA en **0,65 s** («unos 1,0 s»), con «Sin grabación
  para esta palabra».
- *Mihail*: «Esta palabra no está en el diccionario.», que es lo que dice el
  punto 2 de «Antes de la demo» para el caso sin cuenta.

**Paso 5, llegando desde el lector:** «Una frase de mi libro» existe y trae una
frase del capítulo («Dostoevsky was the son of a doctor.»). Sin libro empezado no
estaría, como avisa el punto 3.

**Boca 3D abierta una vez:** la cara está en **2,4 s** («unos 3–4 s la primera
vez, depende de la red»), con «Escuchar y ver», «🐢 Despacio» y «Cerrar 3D».

**Paso 7:** *Mis palabras* con «**1 palabra distinta · 1 consulta · 1 libro**»,
«Repasa cinco» y *poverty* con «Crime and Punishment, cap. 1», como avisa el
guion.

**Textos de los pasos que piden cuenta, en el paquete servido** (no se pueden ver
sin pagar, así que se busca que existan): «Practica esta palabra», «Para sonar más
natural», «no pares aquí», «Escúchalo natural», «Corrígeme», «En español», «Aquí
significa», «Puede ser», «generada por IA», «Recargar y reintentar» (Plan B) y
«Despertando» (Plan B). Todos están.

## 2. Punto 13, la regla de las correcciones: se sostiene entera

Comprobado contra el código servido (`app/ui.py` y `app/api.py` de `61e3bba`), y
sin gastar nada:

| Lo que dice el guion | Lo que hace el motor |
|---|---|
| «Corrígeme» tiene **10 por hora** | `LIMITE_VOZ_HORA` = 10 |
| explicaciones **30**, resúmenes **6** | `LIMITE_CONSULTAS_HORA` = 30, `LIMITE_SINOPSIS_HORA` = 6 |
| el tope va **por conexión, no por cuenta** | la clave es `f"{cubo}:{_ip(peticion)}"` |
| la cuenta es **deslizante** | cada marca vive 60 min (`_VENTANA` = 3600) |
| el aviso dice cuándo vuelve **la primera** | `_minutos_para_la_siguiente` usa la marca más antigua viva |
| agotar uno **no toca los otros** | un cubo por cosa: `voz`, `lexico`, `sinopsis` |
| **reiniciar el Space borra el contador** | `_gasto` es un diccionario en memoria |
| con el tope agotado siguen **leer, buscar, el diccionario, grabarte y escucharte** | el tope de `voz` solo corta `/api/voz`; el de `lexico` solo la etapa completa de `/api/palabra`, no el diccionario |

**Y ninguna variable del Space cambia esos valores:** las únicas definidas son
`LITERALEVEL_DATOS` y `LITERALEVEL_MODELO`, leídas de la API de Hugging Face.

El aviso que el guion no cita, pero describe, es el de `_mensaje_limite` por
cubo: «Has llegado al límite de correcciones de pronunciación de esta hora.
Vuelve a intentarlo …. Grabarte y escucharte, leer y buscar siguen funcionando.»
Cuadra con la última frase del punto 13.

## 3. Los dos textos nuevos del motor

**El guion no cita literalmente ninguno de los dos.** Las únicas citas del motor
que hay en el guion son «No te oí» y «Este intento no cuenta.» (punto 7), y las
dos están en el `app/ui.py` servido. *doncha* y *wanna* (paso 6) están en
`app/voz.py`.

Para constancia, el texto nuevo de «igual» (`61e3bba`) dice ahora «Lo que no
comparamos es en qué sílaba cae el acento, y la diferencia puede estar ahí». No
contradice nada del guion.

## 4. No coincide, todo menor

**A. Los tiempos se mueven de una medida a otra.** El guion da cifras del
cronómetro de esta mañana; hoy salen otras:

| Tramo | Guion | Este ensayo |
|---|---|---|
| Primera búsqueda | 0,90 s (puntos de conexión y 6) | **1,26 s** |
| Ficha con curva (paso 3) | 1,19 s (punto 6) | **2,19 s** |
| Primer pintado del front | 256 ms (punto 6) | **480 ms** |

Ninguno cambia la conclusión del punto 6 —la máquina no es el problema: sigue
siendo poco más de 5 s en toda la demo—, pero las cifras exactas no se repiten.
**Sugerencia:** darlas como orden de magnitud («alrededor de un segundo») o
decir que varían con la red.

**B. Paso 7, «Todo lo que consulto… se queda aquí».** Sin cuenta, *Mihail* no
se guardó. El motor solo apunta una palabra si trae acepción (`registrar =
bool(r.sentido)`, `app/api.py:1588`), y sin cuenta una palabra fuera del
diccionario no tiene ninguna. **Con cuenta, la IA la define y sí se guarda**, así
que la frase vale para la demo real, que se hace con cuenta. Solo sería falsa si
alguien ensaya sin entrar.

## 5. Lo que no se comprobó

- Nada que pida cuenta o micrófono: la corrección, la explicación en contexto, la
  marca IA con cuenta, la bienvenida «Ya tienes cuenta» en el Space (se midió en
  el build de `8a992af`, no en la revisión servida).
- La aparición real de los dos textos nuevos del motor, que exigiría agotar un
  cubo o pagar una corrección.
