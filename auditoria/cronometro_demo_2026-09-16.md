# Cuánto dura la demo — cronometraje del 16 de septiembre de 2026

**Sobre qué:** front en la **revisión del Space `f4920fa`**, **del commit
`a656c2e`**; motor en la revisión `0319290`, despierto y con el buscador listo
(`/api/salud` en 0,27–0,35 s antes de empezar). A **390 × 844 px**, táctil,
contexto limpio y sin cuenta. Guion: `entrega/guion_demo_en_vivo.md` en HEAD.

**Dos relojes distintos, y no se mezclan:**

- **Máquina: medido.** Cronometrado dentro del navegador, desde el toque hasta
  que el resultado está en pantalla, con sondeo cada 40 ms. Es lo que Miguel no
  controla pero tampoco sufre: sale abajo, y es poco.
- **Persona: estimado, no medido.** Un navegador no puede cronometrar a alguien
  hablando. Lo calculo contando las palabras de cada bloque «Dice:» del guion y
  dividiendo por **145 palabras por minuto**, que es un ritmo de demo pausado.
  Si Miguel habla más rápido o más lento, esta parte se mueve entera.

---

## 1. Lo que tarda la máquina (medido)

| Tramo | Medido |
|---|---|
| Arranque del front: primer pintado | **256 ms** |
| Arranque: DOM listo / carga completa | 402 ms / **416 ms** |
| La bienvenida (entra en el primer pintado) y «Saltar» | **58 ms** |
| Ir a *Tu nivel* y tener la primera pregunta | **343 ms** |
| Cuestionario, los seis pasos | **1,79 s** (278 · 267 · 320 · 273 · 284 · **366**) |
| Ir a *Encontrar* | 550 ms |
| Búsqueda «cuentos de dragones» | **896 ms** |
| Búsqueda «una novela de detectives victoriana» | **465 ms** |
| Búsqueda «Crimen y castigo de Dostoyevski» | **572 ms** |
| Abrir la ficha de *Crime and Punishment*, con su curva | **1,19 s** |
| Abrir «Antes del primer capítulo» desde el Índice | **133 ms** |
| **Consultar *poverty*, en frío:** panel abierto | **473 ms** |
| **La misma consulta: IPA y diccionario en pantalla** | **1,02 s** |
| *Mis palabras* con su contador | **182 ms** |

**Suma de todo lo cronometrado: 7,6 s.** Pero esa cifra no es la de la demo,
porque el guion manda dejar preparados la bienvenida, el perfil y el libro.

**Lo que de verdad se paga en directo** —los pasos 2, 3, 4 y 7, que son los que
se hacen con la pantalla compartida—:

| Paso | Máquina en directo |
|---|---|
| 2 · Encontrar (dos búsquedas) | 1,36 s |
| 3 · Buscar el libro y abrir su ficha | 1,76 s |
| 4 · Abrir el capítulo y consultar la palabra | 1,15 s |
| 7 · Mis palabras | 0,18 s |
| Navegar entre pantallas | ~0,55 s |
| **Total** | **≈ 5,0 s** |

**La espera larga que anuncia el guion no es esta.** Los 5 s de la primera
consulta que dábamos por supuestos son en realidad **1,0 s** para el diccionario
y la pronunciación. Lo que tarda de verdad es **la explicación en contexto, que
necesita cuenta y no he podido medir**: el guion dice «unos 15 segundos según la
API» y sigue sin comprobarse con cuenta.

---

## 2. Lo que tarda una persona (estimado a 145 palabras/minuto)

| Bloque | Palabras | Estimado |
|---|---|---|
| A — Atención | 44 | 18 s |
| N — Necesidad | 47 | 19 s |
| 1 · Entrar y el nivel | 39 | 16 s |
| 2 · Encontrar | 36 | 15 s |
| 3 · Abrir un libro y su ficha | 41 | 17 s |
| 4 · Una palabra en su frase | 63 | **26 s** |
| 5 · Pronunciar y corregir | 45 | 19 s |
| 6 · Que no suene robótico | 35 | 14 s |
| 7 · Mis palabras | 20 | 8 s |
| V — Visualización | 39 | 16 s |
| A — Acción | 14 | 6 s |
| **Total hablado** | **423** | **175 s (2:55)** |

A eso hay que sumarle lo que no es hablar ni esperar: teclear las búsquedas,
bajar a la curva, abrir el Índice —que está a dos pantallas—, mantener el dedo
sobre la palabra. **Estimo unos 35 s** para todos los pasos juntos; es la parte
más blanda de este informe y conviene medirla con un cronómetro de mano.

---

## 3. Qué queda para los pasos 5 y 6

No los puedo hacer: necesitan cuenta y micrófono.

- Todo lo demás, hablado: 175 − 33 (lo de los pasos 5 y 6) = **142 s**
- Máquina medida: **5 s**
- Gestos y pausas, estimados: **35 s**
- **Ocupado: ≈ 182 s (3:02)**

| Techo | Queda para los pasos 5 y 6 |
|---|---|
| **5:00**, el máximo de la rúbrica | **118 s (1:58)** |
| **4:00**, el objetivo del propio guion | **58 s** |

El guion les asigna 60 s (2:20 – 3:20). **Cabe, pero justo:** en esos 60 s entran
dos grabaciones leídas en voz alta (4–6 s cada una), dos «Corrígeme» —que son
dos llamadas a un servicio de pago, con tiempo **desconocido**—, abrir «Practica
esta palabra», pulsar «Escuchar y ver» y abrir «Para sonar más natural».

**Si «Corrígeme» tarda más de unos 8 s, los pasos 5 y 6 no caben en el objetivo
de 4:00**, aunque sigan cabiendo en el máximo de 5:00. Es el único número que
decide si la demo se va de tiempo, y es justo el que nadie ha medido todavía.

---

## 4. Recortes propuestos, por orden, sin aplicar ninguno

1. **La segunda búsqueda del paso 2.** El guion hace «cuentos de dragones» y
   «una novela de detectives victoriana». La primera ya enseña lo que importa
   —que salen cuentos de licencia libre en su nivel—; la segunda solo demuestra
   que con otro tema no salen. **Ahorra ~15 s** entre habla, tecleo y espera.
2. **La segunda palabra del paso 4**, la que el diccionario no trae. El guion ya
   permite saltarla («si el tiempo aprieta, sáltala»): basta con convertirlo en
   la norma y no en la excepción. **Ahorra ~10 s.**
3. **El paso 6 entero.** Repite el ciclo del paso 5 con otra frase; lo que añade
   —*doncha*, *wanna*— es bonito pero es el segundo ejemplo de lo mismo.
   **Ahorra ~35 s** y es el recorte que salva la demo si «Corrígeme» va lento.

**Lo que no recortaría:** la curva del paso 3 y la consulta del paso 4. Son el
producto; todo lo demás es el envoltorio.

---

## 5. Lo que este cronometraje no dice

- **Los pasos 5 y 6**, que son de Miguel, con cuenta y micrófono.
- **La explicación en contexto** de una palabra, que es la espera larga de la
  demo y necesita cuenta.
- **El ritmo real de habla.** 145 palabras por minuto es una elección mía; a 130
  el total hablado sube a 195 s y el hueco para los pasos 5 y 6 baja a 1:38.
- **Los gestos**, estimados a ojo y no medidos.

## 6. Tres correcciones a mis propias medidas, para que nadie las repita

Las tres primeras versiones de este cronometraje daban números que parecían
buenos y no lo eran:

1. **«La curva tarda 0 ms».** Mi selector era `svg path`, y **todos los iconos
   de la página son `svg` con `path`**: cazaba un icono al instante. Con
   `app-curva` se ve que la curva ya viene pintada con la ficha (1,19 s).
2. **«El capítulo carga en 6 ms».** Mi condición era que el texto «Antes del
   primer capítulo» estuviera en la página… y **eso ya lo decía el índice de la
   ficha**. Daba por cargado algo que no se había abierto, y por eso la consulta
   de palabra que venía después no encontraba nada. Con la URL del lector **más**
   el texto del capítulo en pantalla: 133 ms.
3. **«La bienvenida tarda 34,8 s».** Eso medía cuándo llegó mi guion, no cuándo
   la vio el usuario. La bienvenida entra en el primer pintado, a 256 ms.

Y un hallazgo de paso: **el cuestionario avanza solo en los seis pasos**, sin
tocar «Siguiente». Mi primer intento pulsaba la opción *y además* «Siguiente», y
saltaba del paso 4 al 6 sin que se notara.
