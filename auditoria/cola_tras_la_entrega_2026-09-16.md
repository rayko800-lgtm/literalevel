# Cola de después de la entrega

Escrito por la Central el 16 de septiembre de 2026. **Esta es la copia que vale**:
antes vivía en el scratchpad de `entrega-f4`, que desaparece con la sesión.

Nada de esta lista se toca antes del 21 de septiembre. **Buscador
(`app/catalogo.py`) y cobro (`app/cuentas.py`) están congelados** hasta después
de la grabación y la demo del 19-20; solo los levanta un SERIO que afecte a la
demo o a los usuarios. Ver la memoria `congelacion-hasta-la-entrega`.

---

## 1. Buscador y cobro (congelados)

| Qué | Dónde | Nota |
|---|---|---|
| Los tres menores de 4e, en `parche_menores_28.py`: registro de devoluciones con disco roto, índice apellido→filas, obras contadas sin fechas | `app/cuentas.py`, `app/catalogo.py`, `pruebas_api.py`, `pruebas_corpus.py`, `tools/banco_mutantes.py` | El de las obras **mueve la exención de 5 obras**, así que toca el buscador: exige medida completa (100 palabras, 27 chips, 20 de control, sin perfil / A2 / B1 / 1,20) contra un **volcado del propio Space**, no contra lo local |
| El comentario del reinicio 30b en `catalogo.py` | `app/catalogo.py`, del commit 1643c4b | Dice que el ruido entre máquinas «no reordena empates», y el límite declarado dice lo contrario. Cambiarlo obliga a subir otra vez o a dejar el Space distinto de HEAD |
| Adelantar el 403 de `/api/voz` antes de leer el formulario | `app/api.py:1881-1935` | Hoy solo se pierde la subida del audio, **no cuota**: `consumir` rechaza sin sumar y el temporal se borra en el `finally`. No adelantar por delante el 503 de la clave de OpenAI |
| Adelantar también el **429 del cubo «voz»**, en el mismo sitio y de una vez | `app/api.py:1875-1925` | `/api/voz` lee el formulario **entero** antes de mirar nada (`contenido = await audio.read(...)`): **el audio ya viajó al servidor** cuando salta el 429, en `:1924`. El usuario graba, sube y **solo entonces** se entera de que no puede corregir. Misma ruta y mismo orden que el 403 de arriba: se arreglan juntos. Visto en la captura de Miguel del 16 sep, con la grabación ya hecha (0:09) |
| Publicar el estado del cubo por hora, para avisar **antes** de grabar | `app/api.py` (`/api/entrada` o ruta nueva) y `front/` | **No es reordenar:** el cubo por hora no se expone en ningún sitio de la API. El único «restantes» que hay (`app/api.py:799` y `:1993`) es `cuentas.queda()`, el cupo del perfil, que es **otro contador**. Avisar antes de grabar exige publicar el dato del cubo y que el front lo pinte, con su prueba |
| El aviso del tope no dice **qué** se ha acabado | `app/ui.py:754-761`, usado desde `app/api.py:1048`, `:1389`, `:1567` y `:1925` | Los cinco caminos que comparten el texto (subidas, sinopsis, léxico, voz y los de Gradio) dicen siempre «límite de **consultas** de esta hora». A Miguel le saltó en *Pronunciar* por el cubo **`voz`** (10/h) y el texto nombraba el de **`lexico`** (30/h): por eso parecía que había que subir `LITERALEVEL_LIMITE_CONSULTAS`, que no habría arreglado nada. Que cada aviso diga su cubo. **La Central lo adelanta a la subida de los dos textos (16 sep), así que esta fila queda solo como registro** |

## 2. Concordancias de singular y plural

La primera tanda fue 0e270f9 y cb799bc (14 y 15 sep). Esto es lo que se le
escapó. **El modelo a seguir ya está en el código**: `app/ui.py:2573`, con
`{'capítulo' if c.capitulos == 1 else 'capítulos'}`.

| Qué sale con n = 1 | Dónde | Alcance |
|---|---|---|
| «Se descartaron 1 resultados por parecido bajo.» | `app/catalogo.py:962`, servido en el campo «aviso» por `app/api.py:998` | **Medido el 16 sep: no lo puede ver nadie.** La rama es **inalcanzable con la configuración que se entrega**: `flojos` solo cuenta las filas flojas que aparecen antes de llenar `n` (`catalogo.py:938-950`, con `break` al llegar a `n`), `minimo_similitud` vale 0.10 (`catalogo.py:830`) y no lo cambia ningún llamador (`api.py:993`, `ui.py:1324`, `api.py:2222`) ni ninguna variable de entorno; con 68.546 vectores el coseno no baja de 0,10. 58 consultas en vivo, incluidas 48 hechas para forzarlo, y el aviso vacío en todas. **Lo primero al retomarlo es decidir si esa rama debe seguir existiendo**; el arreglo sería «Se descartó un resultado por parecido bajo.» |
| «Este libro tiene 1 capítulos; el 2 no existe.» | `app/api.py:563` | Es de la **misma familia** que el fallo de la ficha de un solo capítulo que vio Miguel en su teléfono. Se miran juntos |
| «cupo de 1 usos» | `app/cuentas.py:403` y `:423` | **Condicionado** a que exista alguna cuenta con tope 1. No se comprueba abriendo `literalevel_codigos.txt` |
| «Te quedan 1 usos», «1 de 20 se abren aquí mismo», «1 bloques», «Medidos 1 capitulos» (y le falta la tilde), «de 1 capítulos» | `app/ui.py` 693, 1233, 2140, 2432 y 2883 | Solo Gradio, que es motor y respaldo, no la pantalla de la entrega |

**Mirados y descartados, para que nadie los revise otra vez:** `app/api.py` 366,
1095 y 1525 y `app/scoring.py:392` (la cifra es una constante mayor que uno);
`app/api.py:1311` (no alcanzable con la configuración que se entrega);
`app/ui.py:3304` (ya guardado con `> 1`); `app/ficha.py:114` (contenido por
`ui._reloj_llano`, y el front va por `app/api.py:731`); `app/voz.py`, nada.

## 2b. Dos huecos de prueba que salieron con lo anterior

- **Ninguna prueba ejecuta la cadena de verdad.** `pruebas_extremas.py:5743`
  **fabrica** el texto («Se descartaron 3 por parecido bajo.») para comprobar que
  Gradio lo muestra, y nunca llama a `catalogo.py:962`. Por eso la suite no iba a
  cazar el plural. Si se toca esa rama, la prueba tiene que llamar a `buscar()`
  con un `minimo_similitud` alto, no construir la cadena a mano.
- **El mutante ya existe:** `tools/banco_mutantes.py:963-964` baja
  `minimo_similitud` de 0.10 a 0.0. Ahí está el gancho cuando se retome.
- **Repaso con esa lupa, ofrecido por 4e y aceptado:** al abrir sus tres menores
  después del 20, revisar las pruebas que toque preguntando **de dónde sale el
  texto que comparan**. Los dos casos del 16 sep —la cadena fabricada en
  `pruebas_extremas.py:5743` y el `'1 consulta'` con un espacio que lo ponía el
  CSS— eran el mismo fallo: la prueba se creía a sí misma.

## 2c. Siete pruebas ciegas en `pruebas_extremas.py` (barrido de b9, 16 sep)

Informe completo en `auditoria/ronda5_pruebas_ciegas_b9_2026-09-16.md` (43cdae8),
con las siete demostradas sobre dobles mutantes (7 de 7 en `ok`), doce débiles y
la lista de lo que está bien. **Ninguna afecta a lo que ve un usuario**; son
huecos de red. No se arreglan antes del 20: son solo pruebas, y
`pruebas_extremas.py` tenía cambios de f4 a medias.

- **Primero C3 y C4**, porque dejan una propiedad **sin ninguna otra red**:
  «repasar agrupa por lema» (853-858, el `or` corta si `registrar()` devuelve
  verdadero y la comparación no se evalúa) y «re-anotar no duplica»
  (1043-1048, devuelve la lista sin compararla).
- **C1, C2, C5, C6 y C7** tienen la propiedad cubierta por otra prueba con
  `assert`, pero siguen siendo ciegas: `lista or "…"` (1141-1145),
  `([] or None) and "…"`, que da `None` (333-336), la lista sin comparar de
  «olvidar un libro» (1061-1063), `.name` sin asertar (809-810 y 817-818) y
  `__doc__ is not None` como única comprobación (896).
- **El arreglo de fondo es del lanzador, no de cada prueba:** hoy `prueba()`
  solo falla con excepción o con `False` exacto, así que `None`, tuplas y listas
  pasan como `ok`. Tratar como fallo `None` y los contenedores cerraría de golpe
  varias de estas. Ojo: la convención `condición and "texto"` usa el texto como
  etiqueta de éxito, así que el cambio no puede ser «solo booleanos».

## 3. Mensajes que una persona no entendería

| Texto de hoy | Dónde | Propuesta |
|---|---|---|
| «Falta la cabecera X-Lector con el identificador de este navegador (al menos 16 caracteres).» | `app/api.py:187` | «No he podido identificar este navegador. Recarga la página y vuelve a intentarlo; si sigue igual, abre la aplicación en una pestaña normal, sin modo incógnito ni bloqueadores.» Hoy no lo ve nadie: el front siempre manda la cabecera |
| «Para guardar el nivel hace falta la cabecera X-Lector.» | `app/api.py:891` | «No he podido guardar tu nivel porque no reconozco este navegador. Recarga la página y responde otra vez el cuestionario.» |
| «Ahora mismo se están midiendo 4 libros. Vuelve a pedir la curva en unos minutos.» | `app/api.py:1311` | No dice de quién son esos libros, y quien lo lee entiende que son suyos. «El servidor está midiendo otros libros ahora mismo» |
| «· 3 bloques · confianza 0.8» | `app/ui.py:2140` | Jerga: ni «bloques» ni esa confianza significan nada para un lector. Solo Gradio |

## 4. Limpieza del Space del front

Dejar en `MikeMaki1763/literalevel-front` solo lo alcanzable desde `index.html`,
con la lista de los 14 archivos de e6 como referencia, y **comprobar la
aplicación después de borrar**.

- **Por qué no se hizo antes:** de los 402 `.js` del Space solo 14 se sirven;
  nadie carga el resto. Borrar archivos de un Space publicado tres días antes de
  grabar no compensa, y equivocarse sobre lo alcanzable rompe la entrega.
- **Riesgo declarado, de auditoría y no de usuarios:** quedan 76 chunks huérfanos
  que todavía dicen «seis preguntas». Quien haga `grep` sobre el Space los
  encontrará. La respuesta es que los 14 alcanzables están limpios y el resto es
  basura de despliegues anteriores.

## 5. Casa por dentro

- **Mover la caché local de Hugging Face (3,7 GB) a D:** y reiniciar las sesiones
  para que `TEMP` caiga en D:. Necesita que no haya sesiones trabajando y que
  Miguel las reinicie.
- **Dos carpetas temporales vacías del 7 de septiembre** que dan «Acceso
  denegado» al borrarlas. Ocupan 0 bytes; se dejaron estar.

## 5b. De la prueba de Miguel del 16 de septiembre

- **La boca 3D, más fina (lo dejó él para después).** «La animación 3D me gusta,
  pero se ve muy básica aún… los labios cuando se abren, no se ve el corte de la
  abertura.» Es trabajo de Blender sobre el `.glb`, no de la aplicación. Distinto
  del encuadre cortado que se arregla antes de la entrega.
- **La introducción guiada, versión completa.** Paso 0 de «¿ya tienes cuenta?»,
  guía por las funciones y **quitar texto fijo** de las pantallas, que es lo que
  de verdad pidió: «la interfaz final limpia, sin mucho texto», con la ayuda a
  demanda. La propuesta de 4e queda en `auditoria/`; antes del 20 solo entraría
  una versión mínima, si entra.
- **El scroll de Pronunciar, versión buena.** Antes del 20, si entra, solo la
  opción mínima que mida e6.
- **Si el análisis no detecta el acento tónico** (pendiente de f4): decidir si se
  añade o si se declara como límite, porque la pantalla promete «te digo qué
  sonido corregir» y Miguel esperaba que le corrigiera el acento de «assessors».
- **El límite por hora:** si para la demo se sube o se exime una cuenta, dejarlo
  escrito y **devolverlo a su valor** después del 20.

- **El panel `sticky` de la boca 3D tapa la mandíbula a 360 px** si se desplaza
  la página hasta dejar el visor en la mitad inferior: «Escuchar y ver»,
  «Despacio» y «Cerrar 3D» ocupan tres filas con `bottom: 96px`. Con la vista que
  deja la app no tapa nada (0 % en 551 puntos, medido por e6 el 16 sep).

## 6. Preguntas abiertas de producto, para después

- **Decidir «autor» por la consulta.** Con perfil, un autor buscado con una sola
  palabra («dostoyevski», «tolstoy», «cervantes») trae cuentos sin relación;
  ninguna de las cuatro variantes medidas lo arregla sin quitar cuentos del nivel
  del lector. Límite declarado en el documento (limitación 15).
- **Ideas que quedaron apuntadas:** preferir historias que no sean para «peques»
  cuando el lector tiene nivel alto.
## Encuadre de la boca 3D: sacarlo a una función pura y probarlo

**Por qué no se hizo ahora (16 sep):** el arreglo del encuadre fue cambiar dos
constantes en `compartido/boca3d/escena.ts` —el punto de mira a `0,9` y la
distancia a `17,5` con la cara modelada—, verificado con una captura del
elemento antes y después. No lleva prueba automática porque `EscenaBoca` crea un
`THREE.WebGLRenderer` en sus campos, así que no se puede instanciar en jsdom.

**Forma concreta (la propuso 4e):** extraer una función pura exportada, del tipo
`encuadre(caraModelada, cabezaEntera, aspecto)`, a la que llamen `vista()` y
`distanciaEncuadre()`. Con eso una prueba normal fija que con la cara modelada
salen **0,9 y 17,5**, y que **coinciden con los de la cabeza entera**, que es la
decisión que se tomó.

**Qué fija y qué no, para no venderlo de más:** fija que los números no vuelvan
solos dentro de un mes, que es lo que una captura no caza. **No** fija que se vea
bien: eso solo lo demuestra la captura antes y después.

**Riesgo de hacerlo antes del 20:** es un refactor de la escena 3D a tres días de
grabar, sobre algo ya verificado por captura. No compensa.
