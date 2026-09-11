# Cierre de la auditoría 15 (Fable) — hallazgo por hallazgo

Cerrado el **11 de septiembre de 2026**, sobre `e608527` y lo que vino después.
El informe es [`informe_fable_15.md`](informe_fable_15.md): 0 críticos, 7
serios (S1–S7), 6 menores (M1–M6) y 2 notas, con **22 mutantes vivos de 30**.

Los cinco primeros serios se cerraron ayer y anteanoche (cola de Gradio, perfil
que sobrevive a recargar, índice del epub, libro de la demo). Este documento
cubre lo que quedaba: **S5, S6 y los seis menores**.

**Lo más caro de este informe no fue un serio.** Fue S6: la red de pruebas.
Veintidós de treinta mutantes sobrevivían, y seis de ellos repartían los datos
de un visitante a todos los demás sin que 276 pruebas en verde se enteraran.

---

## Serios

### S5 · «Sorpréndeme» propone un B2 que el modelo mide C1 — CERRADO como se podía cerrar

No es un fallo del código y el informe lo dice: la letra sale del catálogo
heredado de la v1 —predicciones sobre las primeras ~190 palabras— y el número
sale del modelo v4 leyendo el texto. La remedición del catálogo está en marcha
en Colab y es lo que de verdad lo arregla.

Lo que sí se podía hacer hoy es **dejar de esconderlo**. El documento ya lo
declaraba en la limitación 3, pero una limitación escrita en un PDF no
acompaña al lector que está mirando la tabla. Ahora:

- Las **dos** tablas que enseñan la letra —«Sorpréndeme» y el buscador— llevan
  al pie: «la letra de cada libro es la etiqueta del catálogo, heredada y **sin
  medir con el modelo**; al abrirlo, "¿Cómo de difícil es este capítulo?" mide
  el texto de verdad, y cuando no coinciden manda el número del modelo».
- La limitación 3 del documento trae ahora el caso medido por el auditor:
  *The Secret Adversary*, etiqueta **B2**, **1,50** en el prólogo y **1,77** de
  media en el vistazo, o sea **C1**.
- El guion del vídeo lleva una nota de producción: **no pulsar «Sorpréndeme»
  en cámara**, y si sale, decirlo en voz alta. El paso Dos del recorrido es el
  buscador, que no tiene ese problema.

Mutante `F15-s5-nota`: quitar la nota del pie hace fallar «la letra del
catálogo se declara heredada».

### S6 · Veintidós mutantes vivos — CERRADO: diecinueve pruebas nuevas

Las cuatro familias del informe, y lo que se hizo con cada una.

**1. Los datos de un lector, para todos (F15-01…06).** Seis mutantes de una
línea: quitarle la `peticion` a `_sesion_de`, `_mis_libros`, `_debiles`,
`_practicar`, `_abrir` y `_desde_muestra`. El primero es el peor: con
`_sesion_de` devolviendo `"local"`, **el perfil de pago con el que entra uno
vale para todos los visitantes del Space**.

La prueba que vigilaba esto leía el CUERPO de los manejadores buscando
`_archivo_lector(..., peticion)`. Quitar el argumento en la llamada quita
también el patrón, así que el manejador mutado **dejaba de vigilarse solo**.
Una red que se desactiva sola al romperse lo que vigila.

Ahora hay dos pruebas que ponen dos visitantes y comprueban que lo que escribe
uno no lo lee el otro, pasando por los manejadores de verdad. Y una de ellas
destapó algo peor que el mutante:

> En la cabecera de `pruebas_extremas.py` había un
> `ui.voz.registrar_fallos = lambda *a, **k: None`, puesto cuando la suite
> escribía en el `~/.literalevel/voz.db` de quien la ejecutara. Desde que
> `LITERALEVEL_DATOS` apunta a una carpeta temporal ya no hacía falta, y hacía
> daño: apagar el registro deja **sin efecto** la única línea que decide en qué
> `voz.db` se apunta el fallo. El mutante F15-04 no lo podía cazar nadie.

Es la tercera forma de que una prueba no pruebe nada, y una nueva: **un doble
puesto por prudencia que anula justo lo que se quiere medir.**

**2. Las devoluciones del cupo en el resumen (F15-08, F15-09).** La prueba
grande del cupo solo llegaba a una de las tres salidas de `_de_que_trata`: para
cuando corre, el consultor ya está construido, así que la rama del constructor
roto y las de `sin_red`/`sin_pasajes` no se recorrían nunca. La prueba nueva
fuerza las tres y exige la regla entera, con sus dos mitades: **el cupo baja si
y solo si la petición sale a la red** —y si salió y falló después, se cobra, que
es lo que impide regalar tokens ya pagados.

**3. Las constantes del modelo, aseveradas contra sí mismas (F15-14…17).**
`tests_smoke.py` comprobaba que todas las ventanas midieran `BLOCK_WORDS`: una
cota autorreferente, verde con cualquier valor. Ahora se mide la consecuencia:
1.000 palabras dan **cuatro ventanas de 250**, y 5.000 dan **ocho**. Igual con
`HOLGURA`: la prueba leía la misma variable que el código, así que subirla a 0,5
dejaba a las dos pestañas de acuerdo en la misma barbaridad.

Y `F15-14`, el recorte por ventana, que parecía inofensivo porque el promedio
se vuelve a recortar al final: con tres ventanas a 5, 5 y −10 la media honesta
es **3,33** y la rota **0,00**, o sea C2 contra A1 del mismo texto.

**4. Promesas del documento que no probaba nadie (F15-18…23, 31, 32, 39, 40).**
El nombre de la portada de un `.txt` —que es un contrato con `ficha`—, la
licencia dentro de la medición del capítulo, el escapado de la frase en la
tarjeta del cuaderno, la tabla A1–C2 contra `_cefr`, el tope de subida, la
casilla «acercar al nivel», el recorte del pasaje que viaja a OpenAI, el de la
frase de voz, la rotación de «Traer una frase» y el muestreo del vistazo
rápido.

`pruebas_extremas.py` pasa de **276 a 295**, y `pruebas_ficha.py` suma dos.

---

## Menores

### M1 · La cobertura de IPA no se decía — CERRADO

Cuatro sitios prometían «IPA británica y americana» sin condición y el §6.4
cuantificaba el audio (0,5 %) y callaba sobre la fonética. Medido sobre
`kaikki_diccionario.db`:

```
entradas 1.487.639 | con audio 7.003 (0,5 %) | con alguna IPA 46.794 (3,1 %)
con UK y US 33.635 (2,3 %)
```

Y medido **por el lado del lector**, que es lo que importa y el informe no
tenía: 400 palabras tomadas al azar del texto de la demo y resueltas por el
camino de la app —`_resolver_lema_y_categoria` + `buscar` + `_mejor_fonetica`—,
**384 están en el diccionario (96 %), 232 traen IPA (58 %) y 126 traen audio
grabado (32 %)**. Las dos mediciones no se contradicen: el diccionario es en su
mayoría palabra rara y un libro es en su mayoría palabra corriente.

Eso corrige de paso una frase del documento: «casi cualquier palabra que un
lector consulte por primera vez necesitará síntesis de voz» era el 0,5 % de las
entradas leído como si fuera el 0,5 % de las consultas. Son **dos de cada
tres**.

Y para el vídeo, las palabras del capítulo I de *Crime and Punishment* con las
dos transcripciones **y** audio grabado: **clerk** —/klɑːk/ contra /klɝk/, que
se oye— **glance**, **curtain**, **abject**, **disgust**, **preponderance**.

### M2 · El cuadernillo, §7.2 — CERRADO

Negritas anidadas y cuatro tildes (usó, sí, miró, menú) en la única celda
escrita sin ellas. Corregido y el `.ipynb` regenerado. Se pasó además un
barrido por las 92 celdas buscando lo mismo: no hay más.

### M3 · Seis, ocho o nueve correcciones de Esmeralda — CERRADO

El «8» de la métrica de éxito no salía de ninguna tabla. El Cuadro 1 de la
estrategia tiene **nueve** filas, **seis** de ellas etiquetas. Ahora los tres
sitios dicen «las nueve correcciones del Cuadro 1, seis de ellas etiquetas».

### M4 · `PENDIENTES.md` iba por detrás — CERRADO

El banco de mutantes, el estado del Space, la fecha y las «catorce auditorías»
del documento, que con esta son quince.

### M5 · Tres asimetrías de dinero — CERRADAS las tres

1. **`_consultar` contaba las llamadas ANTES de hacerlas.** Un timeout o un 401
   no cuestan un céntimo y le descontaban un uso al lector, mientras
   `ficha.sinopsis` sí devolvía el uso sin red: dos criterios para la misma
   regla. Ahora se cuenta lo que produjo algo.

   Escribiendo esa prueba salió un caso que no estaba en el informe:
   `_generar_audio_tts` devuelve el mp3 que ya está en disco **sin llamar a
   tts-1**, y ese acierto también se cobraba. Devuelve `(ruta, se_pago)`.

2. **La puerta de entrada no tenía freno.** `compare_digest` hace que el tiempo
   no diga nada, pero nada impedía probar un diccionario de contraseñas a la
   velocidad de la red. **Quince intentos fallidos por IP y hora**; acertar no
   gasta ficha, y con el cubo agotado no se comprueba nada —si no, el freno
   sería un oráculo de contraseñas buenas—. Quince y no tres porque la
   contraseña del profesor va por WhatsApp y el día de la demo nadie quiere un
   candado.

3. **La pestaña «Estado» es pública** y escribía los nombres de usuario de las
   entradas mal formadas del secreto. Al registro del Space siguen yendo con
   nombre —eso solo lo lee el dueño—; a la pantalla, solo el número de entrada,
   que es lo que hace falta para arreglar el secreto.

La sospecha del informe sobre `x-forwarded-for` no se reprodujo: el proxy del
Space sí la pone, y sin ella `_ip` cae al `client.host`, no a un cubo común.

### M6 · Lo que se ve en la pantalla del libro y del buscador — CERRADO

- **«Lo que más se repite»** gastaba cuatro de diez puestos en `don't`,
  `think`, `got` y `down`. Añadir las contracciones a `_VACIAS` no bastaba:
  Gutenberg escribe `don’t` con el apóstrofo tipográfico y no casaba. Y
  `[A-Za-z]` partía «Svidrigaïlov» en «svidriga» y «lov», y las dos mitades
  subían a la lista. Medido después en ocho libros: *Guerra y paz* da «prince,
  pierre, moscow, french, andrew, natásha, room, army, princess, count».
- **El *placeholder* del buscador.** Remedido: «una novela de detectives
  victoriana» con perfil 1,2 **sí** devuelve a Conan Doyle, el séptimo —el
  informe decía que ninguno—. Lo que sí es cierto es que el segundo puesto es
  un cuento infantil A1, y no es un fallo: la casilla acerca y no filtra. El
  documento lo cuenta ahora con la lista medida, antes de que lo pregunte
  nadie.
- **La caja de entrada tras recargar** volvía vacía aunque la sesión de pago
  siguiera viva. El visitante no sabía si seguía dentro hasta que consultaba
  —y le cobraban—, así que volvía a teclear la contraseña por si acaso. Ahora
  `demo.load` la repinta, encadenada después del registro del lector.
- **«Mis puntos débiles» borraba la corrección de pronunciación**: los dos
  botones escribían en el mismo `veredicto`, y volver a verla costaba otra
  llamada de pago. Cada uno tiene su caja.

---

## Notas

### N1 · El `app.py` del Space no está en el repositorio

Cierto, y se queda así por ahora: `tools/desplegar_app.py` no lo toca a
propósito —es el único archivo que se edita en el panel del Space— y el
auditor comprobó bajándolo que es equivalente a `main.py` en lo que importa.
Lo que sí se cerró es la mitad accionable: el valor de
`TAMANO_MAXIMO_SUBIDA` ya lo asevera una prueba (mutante F15-22).

### N2 · La tabla A1–C2 no estaba atada al código

Cerrada: la prueba nueva **lee la tabla** de `_TABLA_CEFR` y exige que cada uno
de sus seis tramos case con `_cefr` en los dos extremos.

---

## Lo que no se cerró, y por qué

**La remedición del catálogo** (A3 del informe, y la raíz de S5). Está corriendo
en Colab sobre la T4 gratuita: 51.248 de 61.789 libros medidos. Mientras no
termine, la letra del catálogo sigue siendo de la v1 y lo único honesto es
decirlo en la pantalla, que es lo que se hizo.

**Los ocho *shards* perdidos** de la descarga de Hugging Face (HTTP 429). La
celda 6c los recupera; no bloquea nada.
