# Cierre de la undécima auditoría — 9 de septiembre de 2026, de noche

`informe_fable_11.md` (Fable, a ciegas, árbol `b32b520`) dio **1 crítico, 5
serios, 9 menores y 6 notas**. Fue la auditoría más productiva del proyecto, y
la razón es que se le pidió una cosa que no se había pedido nunca: **mutar el
código y comprobar que las pruebas fallan**.

Todo lo que sigue está verificado a mano antes de tocar nada, y medido en esta
máquina. Los hallazgos se cerraron en el orden de lo que costaba dejarlos
abiertos, no en el del informe.

---

## C1 — el cuestionario de nivel nunca recibía el `gr.Request`

**Verificado y cerrado.** Es el peor de la ronda porque afecta a la **primera
pantalla** y solo se manifiesta desplegado.

`_desde_cuestionario(p_actual, nombre, *valores, peticion=None)`: Gradio solo
inyecta el `Request` en parámetros **posicionales**, y su `special_args` corta
el recorrido de la firma en el primero que no lo sea. Con `*valores` delante,
`peticion` era keyword-only y llegaba `None` **siempre**. Comprobado leyendo el
bucle en el Gradio instalado, no de memoria.

Y `None` ahí no es inocuo: `_archivo_lector(..., None)` resuelve a
`lectores/anonimo/`, **una carpeta para todos los visitantes del Space**. Cada
«Estimar mi nivel» pisaba el perfil del anterior —con su nombre dentro— y al
recargar `_perfil_inicial`, que sí recibe el Request, buscaba en la carpeta de
la sesión y no encontraba nada: el lector volvía a «Todavía no has fijado tu
nivel» justo después de leer «Guardado».

**Un solo manejador estaba afectado**, comprobado recorriendo los 29 que
declaran `peticion`.

**Corrección, y aquí el informe se equivocaba.** Proponía rehacer el cableado
con un `gr.State`, y descartaba la solución simple diciendo que poner `peticion`
en tercera posición «desplazaría las respuestas». No lo hace: `special_args`
inserta el Request **en el índice de su parámetro**, así que las entradas quedan
alineadas. Se comprobó ejecutando `special_args` con las dos firmas antes de
elegir. La corrección es una línea.

**Prueba nueva:** pasa **todos** los manejadores que anotan `gr.Request` por el
`special_args` real y exige que reciban un centinela. Verificada por mutación:
con la firma vieja falla, con la nueva pasa. Es la prueba que habría cazado
esto desde el principio, y no existía.

---

## S1 — 39 pruebas pasaban con el código roto

**Verificado y cerrado**, y es el hallazgo más valioso del día.

El envoltorio `prueba(nombre, fn)` imprimía lo que devolviera la función, así
que un `False` salía como `ok False` y la suite terminaba en verde. Con eso, el
banco de mutaciones del auditor demostró que la suite pasaba entera con `_entrar`
aceptando cualquier contraseña, con los tres topes por hora apagados, con la
práctica de voz sin puerta de pago, con `_salir` que no olvida y con
`_dir_lector` mezclando las carpetas de dos lectores.

**El arreglo del informe era demasiado brusco.** `assert r is not False` a secas
rompe cinco pruebas legítimas —«palabra vacía se rechaza», «sin título se
rechaza», «libro que ya no existe se marca»…— donde `False` **es** el acierto,
porque la función devuelve `False` cuando rechaza. Al aplicar la regla salieron
seis pruebas en rojo; el informe solo había detectado una.

Así que se hicieron las dos cosas:

1. el envoltorio trata `False` como fallo **y** itera lo que devuelva una
   generadora (`_medir` y compañía devolvían el generador sin ejecutar una sola
   línea del cuerpo: «medir índice imposible» imprimía `ok <generator object>`);
2. las seis pruebas afectadas **aseveran su expectativa** en vez de devolver el
   booleano crudo, así que ahora dicen «rechazada» cuando aciertan y fallan de
   verdad cuando el rechazo deja de funcionar.

**Los subcasos, todos cerrados:**

- **S1.b** `medir indice imposible`: lo arregla la iteración del envoltorio.
- **S1.c** el detector de colores clavados no veía los colores **por nombre**.
  Ahora sí, con `transparent` exento a propósito. Verificado con el mutante del
  informe (`background:yellow` en `::selection`): antes pasaba, ahora falla.
- **S1.d** «consultar por encima del tope no llama a OpenAI» **no probaba nada**:
  preguntaba con `tope=0`, que significa sin límite, así que la rama de la
  consulta no se ejecutaba jamás e imprimía «tope generoso, no aplica».
  Reescrita: agota un tope real y comprueba que no se llega al consultor.
- **S1.e** «html incrustado en la frase» devolvía `False` desde hacía tiempo.
  La expectativa era la equivocada, no el código: `normalizar_palabras` quita la
  puntuación antes, así que no hay ningún `<` que escapar. Ahora asevera la
  propiedad de seguridad de verdad —que no salga HTML vivo—.

**Banco de mutaciones, después de los arreglos.** Cada mutante lo caza ahora
**su propia prueba**, que es lo que importa:

| Mutante | Lo caza |
|---|---|
| `_entrar` acepta cualquier contraseña | «entrar con una clave mala no abre nada», «un usuario que no existe no entra», «el usuario no distingue mayúsculas y la clave sí» |
| `_dentro_del_limite` siempre `True` | «consultar por encima del tope no llama a OpenAI» |
| `_salir` no olvida | «salir olvida el perfil» (reescrita: antes solo miraba el mensaje) |
| `_dir_lector` no separa lectores | «dos sesiones no comparten carpeta» |
| `_medir` revienta con índice fuera de rango | «medir índice imposible» |
| `_practicar` sin puerta de pago | «la práctica de voz pide código» |

---

## S4 — la suite gastaba dinero en cada ejecución

**Verificado y cerrado.** Es el que más urgía porque cobraba.

La prueba «audio inexistente» llegaba a `voz.explicar_correccion`, que no tiene
caché, y pagaba un `gpt-4o-mini` **cada vez que alguien corría las pruebas**,
con la clave real: `config.cargar` la lee de `CLAVES.txt` y la mete en el
entorno al importarse. Reproducido con un espía sobre `openai.OpenAI`.

Se corta en el origen y no prueba a prueba: la suite anula `config.cargar` y
borra la clave del entorno antes de importar nada, así que corre por el camino
degradado —que es el que `AGENTS.md` promete y el que conviene ejercitar—.
**Comprobado con el espía sobre la suite completa: cero llamadas de pago.**

De paso deja de depender de la red, que era la otra mitad del problema: la
prueba tardaba segundos y daba otro resultado sin conexión.

---

## S2, S3 y S5

**S2 — `_de_que_trata` reventaba sin diccionario.** `consultor()` construye el
`ConsultorLexico` entero, que abre el Kaikki de 243 MB y lanza
`FileNotFoundError` si no está. El resumen no necesita el diccionario: solo un
cliente de OpenAI. En el Space con el dataset mal montado, la pestaña Leer
funcionaba y ese botón devolvía un «Error» pelado. Envuelto.

**S3 — dos fallos en uno.**

- Al visitante sin perfil se le decía **«Sin clave de OpenAI»** en un servidor
  que sí tiene clave: `_consultar` tiraba `motivo_pago` y `lexicon` seguía su
  camino de «sin clave». Ahora se le dice que entre con su perfil, o que agotó
  su cupo, según el caso. Verificado: el aviso falso desaparece y aparece el
  verdadero.
- **El cupo se gastaba sin gastar dinero.** `_puede_pagar` cobra *antes* de
  llamar a OpenAI —y tiene que hacerlo así, porque preguntar primero y apuntar
  después abre la condición de carrera que ese código cerró—, pero una
  respuesta que sale de la caché de `lexicon.db` no cuesta un céntimo. `tope`
  no era «llamadas de pago» como declara `cuentas.py`, sino pulsaciones. Se
  añade `cuentas.devolver`: se cobra siempre y se devuelve cuando se sabe que
  no hubo gasto. Medido: cuatro consultas desde caché dejan el contador en 0;
  tres sin caché lo dejan en 3.

**S5 — `#ll-voz` repetía palabra por palabra el fallo de `#ll-lector`:** un
`border` abreviado y posterior en el DOM que reescribía el
`border-color:var(--ll-borde)`, más un `color:inherit`. Se había corregido en
uno y no en el otro.

**Y aquí sale algo que el informe declaró sin medir.** Decía que el verde y el
rojo de la pronunciación tampoco salen de la paleta, y que no había medido su
contraste. Medidos: **fallan de verdad** en las tres paletas claras —verde
2,21–2,30 y rojo 2,86–2,95, contra el 3:1 que WCAG pide a un objeto gráfico—. Y
**no hay un par de colores que valga para las cinco**: oscurecerlos arregla las
claras y hunde las oscuras (el rojo a x0,8 sube a 4,04 en amanecer y cae a 2,45
en medianoche). Así que son variables de paleta nuevas —`--ll-bien`,
`--ll-mal`, `--ll-mal-fondo`— con sus tres parejas en la prueba de contraste. El
significado no cambia; el tono sí.

---

## Menores cerrados

- **M1.** «Sorpréndeme» anunciaba un rango y filtraba con otro: el rótulo daba
  `rango_recomendado` (nivel−0,10 a nivel+0,15) mientras `por_nivel` usaba una
  holgura simétrica de 0,25. Con un lector en 1,00 decía «entre 0.90 y 1.15» y
  listaba B1 (0,80) y B2 (1,20): **ninguno de los dos dentro**. Ahora hay una
  sola constante y se pasa explícita, así que no pueden volver a separarse.
- **M2.** Tres números para el mismo vistazo rápido: 80 en la interfaz, 60 real
  (30 × 2) y 40 en un docstring. El texto lo calcula ahora de las constantes y
  el docstring las nombra en vez de repetir la cifra.
- **M3.** Cuatro bordes que levantaban excepción con archivos que escribe la
  propia app, contra lo que promete la cabecera del módulo. El peor era
  `_reanudar`, que corre en `demo.load`: un `sesion.json` con JSON válido que no
  fuera un objeto hacía que **la página entera arrancara con error** para ese
  lector hasta que borrara el archivo a mano. Cerrados los cuatro, con prueba.
- **M4.** Vaciar «¿Cuántos te propongo?» enseñaba `int() argument must be…
  not 'NoneType'`. Dos sitios, los dos con `int(n or 10)`.
- **M9.** El contador de usos seguía subiendo después de agotar el cupo —un
  perfil de tope 5 podía marcar 40—, así que `queda()` daba negativo y el número
  del diagnóstico no significaba nada. Y el aviso de tope decía **siempre «60
  minutos»**, que es la ventana entera y casi nunca lo que falta: quien agotó el
  cupo hace 58 minutos leía que debía esperar una hora. Ahora se calcula con la
  marca más antigua viva.

## Menores que quedan abiertos, a propósito

- **M5** (CSS muerto contra el frontend compilado de 6.26, `--ll-acento-claro`
  declarada y sin uso), **M6** (cuatro elementos con el mismo `id="ll-lector"`),
  **M7** (el radio de esquina no llega al lector ni a la voz) y **M8**
  (documentación y código que discrepan en detalles menores). Son limpieza, no
  fallos: ninguno cambia lo que ve o puede hacer un lector.
- Las **6 notas** del informe, que no pedían acción.

---

## Cifras tras esta ronda

| Qué | Antes | Ahora |
|---|---|---|
| Pruebas de estrés | 216 | **222** |
| Parejas de contraste | 70 (14/paleta) | **85 (17/paleta)** |
| Peor contraste | 4,53 · 3,11 | **4,53 · 3,11** (recalculado, sin cambio) |
| Llamadas de pago por ejecución de la suite | 1 (`gpt-4o-mini`) | **0**, comprobado con espía |

Las siete suites pasan. Las cifras de validación, intactas: 47 textos, A2
0,5561, baseline 0,860 / 0,807 / 0,668, modelo contra longitud 0,732, filtro 31.
`documento.pdf`: 45 páginas, cero referencias rotas, «222 pruebas» dentro y ni
un «216» ni un «205».

**Sigue sin desplegar.** Los cambios de CSS y el arreglo de C1 hay que verlos en
la app real —y C1 **solo se manifiesta desplegado**, porque en local no se
reparte por sesión—. Es lo primero que hay que hacer, y con la app delante.

---

## Lo que esta ronda enseña sobre auditar

1. **Pedir mutaciones cambia el resultado.** Nueve auditorías anteriores
   leyeron el mismo código y ninguna encontró que 39 pruebas no aseveraban
   nada. La diferencia no fue el auditor: fue el encargo.
2. **Un informe sigue siendo una lista de hipótesis.** En esta ronda: el arreglo
   propuesto para C1 era innecesariamente grande y su objeción era falsa; el de
   S1 rompía cinco pruebas legítimas; y dos hallazgos venían declarados «sin
   medir» y al medirlos resultaron peores de lo que decían. Verificar no es
   desconfianza, es la mitad del trabajo.
3. **Al escribir la prueba que falta aparece el fallo siguiente.** La prueba
   estructural del CSS encontró, al escribirla, el borde clavado del lector, que
   no estaba en ningún informe.
