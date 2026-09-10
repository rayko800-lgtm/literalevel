# Cierre de la duodécima auditoría — 10 de septiembre de 2026, de madrugada

`informe_fable_12.md` (Fable, a ciegas, árbol `ffcc0a8`): **0 críticos, 8
serios, 10 menores, 11 notas**, con un banco de **70 mutantes** de los que 44
sobrevivían. Cero críticos por primera vez en el proyecto.

Todo lo de abajo está verificado a mano antes de tocar nada.

---

## Lo que se ha corregido

### S1 — `_medir` levantaba `OSError` hacia Gradio

Solo atrapaba `FileNotFoundError`, que cubre la carpeta local ausente.
Desplegada, el modelo es un repositorio del Hub y `from_pretrained` lanza
`OSError` si el Hub no responde o la descarga se corta en el arranque en frío:
el botón «¿Cómo de difícil es este capítulo?» escupía el traceback. Los otros
tres manejadores que cargan el modelo ya lo atrapaban. **Con prueba nueva**,
verificada por mutación.

### S2 — el tope por hora cortaba consultas que no cuestan nada

La cabecera del módulo promete que «lo que no cuesta dinero no se limita», pero
el tope del cubo «lexico» se aplicaba **antes** de la puerta de pago. Una
consulta sin perfil —o en una copia sin clave— es diccionario, IPA y audio de
Wiktionary: todo local. Un aula entera detrás de la misma NAT compartía 30
consultas de diccionario por hora sin que ninguna pudiera costar un céntimo, y
el aviso les decía que «leer, buscar y medir siguen funcionando: no cuestan
nada», como si aquella sí costara.

Ahora el tope solo se aplica cuando la consulta **va a costar**: hay clave y la
sesión puede pagar. `permite` pregunta sin consumir; quien decide de forma
atómica sigue siendo `consumir`, así que no se reabre la condición de carrera
que se cerró ahí. Medido: 35 consultas gratis pasan sin cortarse, y el control
con clave sigue frenando en la 31.

Esto **rompió una prueba existente**, y era correcto que la rompiera: la del
tope ejercitaba el camino sin clave. Se actualizó para probar la regla nueva.

### S3 — la cifra escrita en letra que mi barrido no vio

`documento.tex` y `estrategia.md` decían «las **cuarenta parejas** de color
—ocho por paleta—» en cuatro sitios. Hoy son **85, diecisiete por paleta**.

Es un fallo del cierre anterior y conviene nombrarlo: el barrido buscó
`40 parejas` y `8 por paleta` **en dígitos**, dio limpio, y la cifra estaba
escrita con letras. La regla de la skill —buscar la cifra en todas sus formas—
se aplicó a medias. Los dos peores contrastes citados (4,53 y 3,11) siguen
siendo ciertos con las 17 parejas, recalculados.

### S5 a S8 — pruebas que no probaban

Los mutantes que sobrevivían, y la prueba que ahora los caza:

| Mutante | Lo caza |
|---|---|
| `_consultar` sin puerta de pago | «la consulta léxica pide código» (nueva) |
| Voz y sinopsis sin tope por hora | «voz y sinopsis respetan su tope» (nueva) |
| `LIMITE_VOZ_HORA = 0` | «los topes por hora están puestos» (nueva) |
| El cuestionario guarda en `anonimo/` | «dos lectores no se ven los datos» (nueva) |
| Quitarle la anotación `gr.Request` al cuestionario | «los manejadores que guardan pasan la petición» (nueva) |
| `session_hash` sin sanitizar | «session_hash con ../ no escapa» (arreglada) |
| `_medir` no atrapa `OSError` | «medir con el modelo inalcanzable» (nueva) |

Dos merecen explicación:

- **La prueba del `../` no podía fallar.** Comprobaba `base/lectores in
  ruta.parents`, y `Path.parents` es **léxico**: `base/lectores/../../etc/passwd`
  tiene a `base/lectores` entre sus padres aunque resuelva fuera del disco.
  Quitando la sanitización entera seguía en verde. La sanitización estaba bien;
  era la prueba la que no valía.
- **La comprobación de inyección del `Request` miraba al revés.** Solo revisaba
  los manejadores que **ya** anotan `gr.Request`, así que un mutante que le
  quitara la anotación al cuestionario se le escapaba: dejaba de anotar, dejaba
  de recibir, y la prueba lo saltaba por no anotar. La nueva saca los
  manejadores **cableados** a la interfaz y exige que el que toque datos del
  lector anote.

Y dos que devolvían un valor que nunca es `False` —un número y una tupla—:
«el tope se respeta» imprimía `ok 4` y con el tope roto habría impreso `ok 9`.

### Menores

- **M4.** `analisis/*.json` y `-sinopsis.json` mal formados levantaban
  `KeyError` y `AttributeError`. Mismo fallo que ya se cerró en `sesion.json` y
  `perfil.json`, en los dos archivos que quedaban. Con prueba.
- **M5.** La latencia publicada era de antes de `reasoning.effort="low"`. Lo
  medido en el código: **67,7 s** con el esfuerzo medio y **14,9 s con `low`**,
  que es el que corre. **No se publica un total nuevo**: el 28-44 anterior
  incluía unos cinco segundos que no son la explicación, y no hay medición del
  total con `low`. Se dice lo que está medido y se deja de afirmar un total que
  nadie ha cronometrado. `AGENTS.md` además daba el cambio a `low` por
  «pendiente, sin hacer», y está hecho.
- **M8.** «partian» → «partían».
- **M9.** **Contraseña real en un archivo versionado.** `mensaje_profesor.md`
  llevaba escrita la de `invitado1`. El repositorio es **privado** —comprobado
  con la API de GitHub—, así que no está expuesta, pero ese mismo archivo
  propone compartir el repositorio con el profesor. Sustituida por un hueco, con
  el aviso de que **hay que rotarla**: estuvo en el historial de git, y eso no se
  puede desescribir.
- **M10.** `_abrir_del_catalogo` dejaba escapar el único `OSError` de disco que
  quedaba en un manejador.

---

## Lo que queda abierto, a propósito

- **S4.** La tarjeta pública del modelo en Hugging Face enlaza «LiteraLevel» a
  `https://github.com/` a secas. El archivo local está, pero **republicarla
  necesita el token de Hugging Face**, que no está en esta máquina. Queda para
  Miguel, junto con el despliegue.
- **M2.** `--ll-lector-texto` vuelve a ser una variable muerta: la regla
  `.prose *` de la paleta, que lleva `!important`, le gana en el DOM real.
  Fable lo midió en el navegador y **la pareja que se pinta sigue pasando AA**,
  así que es cosmético. No se toca porque esa regla es la que sostiene el
  arreglo del crítico C1 de la décima auditoría, y romperla cuesta más de lo que
  arregla. Anotado para que nadie lo «arregle» sin medir.
- **M1, M3, M6, M7** y las 11 notas: el cupo cobrado en dos caminos más sin
  gasto, la caché de Gutenberg con archivos `.txt`, los colores clavados fuera
  de los ocho selectores vigilados, y el modelo que se carga antes de validar.
  Ninguno cambia lo que ve o puede hacer un lector.

---

## Cifras tras esta ronda

| Qué | Antes | Ahora |
|---|---|---|
| Pruebas de estrés | 222 | **229** |
| Parejas de contraste | 85 (17/paleta) | igual, pero **bien escrito** en los entregables |
| Latencia publicada de la consulta | 28-44 s / 23-39 de espera | **14,9 s medidos** de espera, con `low` |
| Llamadas de pago por ejecución de la suite | 0 | **0**, comprobado otra vez con espía |

Las siete suites pasan. Cifras de validación intactas: 47 textos, A2 0,5561,
baseline 0,860 / 0,807 / 0,668, filtro 31. `documento.pdf`: 45 páginas, cero
referencias rotas, con «229 pruebas», «ochenta y cinco parejas» y «14,9
segundos» dentro, y sin rastro de las tres cifras viejas.

**Sigue sin desplegar**, y ahora hay una razón más para hacerlo pronto: en
producción el cuestionario aún manda el perfil de todos los visitantes a la
misma carpeta.

---

## Lo que enseña esta ronda

1. **El banco de mutaciones vale más que el informe.** 44 de 70 mutantes
   sobrevivían a 222 pruebas en verde. Ningún repaso de código habría dado esa
   lista.
2. **Un mutante «cazado» por una prueba ajena no está cubierto.** En este banco,
   una prueba de rutas fallaba en *todas* las copias por un archivo que no se
   copió, y hacía parecer cubiertos a mutantes que no lo estaban. Hay que
   atribuir el fallo a la prueba que se espera, y filtrar ese ruido.
3. **Una cifra se esconde escrita con letras.** El barrido en dígitos dio
   limpio sobre cuatro sitios que estaban mal.
