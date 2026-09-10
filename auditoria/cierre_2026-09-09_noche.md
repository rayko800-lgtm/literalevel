# Cierre de la décima auditoría — 9 de septiembre de 2026, por la noche

La décima auditoría (`informe_fable_10.md`) dio **1 crítico, 4 serios, 6
menores**. Este documento dice, hallazgo por hallazgo, qué estaba ya cerrado,
qué no lo estaba, y con qué se comprobó cada cosa.

**Cómo se verificó.** Cuatro verificadores independientes en paralelo, cada uno
con un bloque de hallazgos y con una instrucción explícita: **no dar por bueno
el documento de cierre anterior ni los mensajes de commit, medir contra el
código.** Esa instrucción es consecuencia directa de S4, que fue exactamente el
pecado contrario. Los cuatro entregaron reproducciones ejecutables.

Todo lo que sigue está medido en esta máquina el 9 de septiembre por la noche,
sobre el árbol posterior a `1478bd5`.

---

## Lo que ya estaba cerrado y se confirmó

| | Hallazgo | Con qué se confirmó |
|---|---|---|
| **C1** | La paleta no le ganaba al modo del navegador | `app/paletas.py:200-275` reasigna 50 variables del tema con `!important`. Un verificador reprodujo primero las cifras viejas de Fable **exactamente** para validar su método, y luego midió las nuevas: claro y oscuro dan ahora el mismo valor en todas las filas, mínimo **9,88:1** donde había 1,04. `--input-text-color` no existe en Gradio 6.26, así que no era un hueco |
| **S1** | «Modelo v4: FALTA» con el modelo funcionando | `app/ui.py:2167-2174` usa `_parece_repo_hf`. Reproducido con `LITERALEVEL_MODELO=MikeMaki1763/literalevel-v4`: «Modelo v4: repositorio de Hugging Face». El diccionario **no** debe tener ese trato: es siempre la ruta de un archivo |
| **S3** | Tarjetas de «Mis libros» y «Mis palabras» entre 2,5 y 3,9:1 | `rgba(8,16,28,.55)` ya solo sobrevive en un comentario. Peor caso medido: **5,28:1**, antes 2,50 |
| **S4 fallo 2** | Nadie comprobaba que la caja de entrar se encuentre | Probado por mutación: caza las dos formas del fallo real (acordeón cerrado, bloque movido dentro de las pestañas) |
| **M6** | Comentario de JS con la posición vieja | `app/ui.py:819` dice «encima del lector». Revisados además todos los comentarios de posición de `02335ae` y `88c414b`: correctos |
| **M3** | `LITERALEVEL_CUENTAS` sin documentar | Documentada en `DESPLIEGUE.md:24-29` y `main.py:19-24` |

---

## Lo que NO estaba cerrado, y se ha corregido ahora

### S2 (parcial) — `_entrar` no envolvía nada

`cuentas.verificar` ya comparaba bytes, así que la ñ dejó de reventar. Pero
`app/ui.py:219` seguía desnudo: **cualquier otro** fallo salía como traceback
crudo a la interfaz, contra el contrato declarado en la cabecera del propio
módulo («ningún manejador levanta excepciones hacia Gradio»).

Corregido con un `try/except` alrededor del cuerpo. El detalle va a `stderr` —o
sea al registro del Space— y **no** a la pantalla, a propósito: ese mensaje lo
lee quien está probando contraseñas, y no tiene por qué aprender si el fallo
fue del usuario, de la clave o del disco del cupo. Reproducido inyectando un
`RuntimeError` dentro de `verificar`: devuelve «No he podido entrar. Ha fallado
algo al comprobar el perfil» y registra `_entrar: RuntimeError: …`.

### S4 fallo 1 — la prueba existía, pasaba, y pasaba con el código roto

Lo más grave de la ronda. La prueba de `pruebas_extremas.py` comprobaba
`_parece_repo_hf` **en aislamiento** y el camino de la carpeta inexistente. Las
dos cosas siguen siendo verdad con el guardia roto, o sea que medía el ayudante
y no el guardia.

Añadida la aserción que sí distingue: construir `Puntuador` con un
identificador del Hub y comprobar que **llega a cargar**, cortando
`from_pretrained` con un centinela para no descargar los 328 MB. Verificado por
mutación, en subprocesos separados:

```
codigo real   -> la prueba PASA
CODIGO MUTADO -> la prueba FALLA -> No encuentro el modelo v4 en MikeMaki1763/literalevel-v4.
```

### M4 — `_tabla` descartaba perfiles en silencio

Reproducido: 8 entradas declaradas → 4 perfiles, sin un solo aviso. El caso
caro no es el perfil que desaparece, es el **usuario repetido**: no desaparece
nada, cambia la contraseña, y quien tenía la otra recibe el mismo «No he podido
entrar» que un impostor.

`app/cuentas.py` separa ahora `_analizar`, que devuelve los motivos de
descarte, con `problemas()` y `declaradas()` como interfaz pública. Los avisos
salen una vez por proceso a `stderr` y la pestaña **Estado** los enseña:
«Perfiles: 4 válidos de 8 declarados» con el motivo de cada pérdida. **Ningún
aviso lleva una contraseña**: se dice la posición de la entrada y el nombre de
usuario, que no es una credencial.

### M5 — la prueba de opacidad pasaba por convención de escritura

`re.findall(r"opacity:(\.[0-9]+)", …)` no veía `opacity: 0.3`, `opacity:0`,
`opacity:1` ni `opacity:30%`. Demostrado inyectando las cuatro formas: la
prueba seguía diciendo «3 opacidades». Ampliado el regex a las cuatro formas y
al porcentaje, y ahora lee **los dos** archivos con CSS (`ui.py` y
`paletas.py`), no solo el primero.

De paso, dos agujeros del mismo tipo que encontró el verificador:

- `#[0-9a-fA-F]{6}` en la prueba de la gráfica no veía `#8ce`, ni `rgb()`, ni
  `hsl()`. Ampliado, con la excepción anotada de `rgba(0,0,0,0)`, que es
  transparencia deliberada para que la gráfica herede el fondo de la paleta.
- El lector de colores de la prueba de opacidad **saltaba la paleta entera en
  silencio** si el fondo no era hex de 6. Ahora entiende hex de 3 y `rgb()`, y
  si no sabe leer un color falla en vez de callarse.

### M1 y M2 — residuos de documentación

- **M1:** lo visible al usuario ya estaba limpio. Quedaban tres restos internos
  titulados «Códigos de acceso» (`app/cuentas.py:1`, `app/ui.py:180-181`).
  Corregidos. Las menciones históricas que **explican** por qué se cambió se
  quedan a propósito.
- **M2:** el túnel muerto ya no estaba, pero el aviso de cabecera seguía
  diciendo «si la computadora está apagada, el enlace está muerto», que
  contradice al punto 1 del propio mensaje. Y los topes eran **falsos**: decía
  «12 y 4 por hora» y en el código son **30 consultas, 10 prácticas de voz y 6
  resúmenes**, por IP y por hora (`app/ui.py:132-138`). Ni el 12 ni el 4
  existen en ningún sitio.

### Propagación que se había quedado a medias

`991fab7` corrigió «entre 3 y 5 horas de A100» —que medía la tarjeta, no el
trabajo— pero no llegó a `entrega/mensaje_profesor.md`, que seguía diciendo «6
horas de GPU», una cifra que no coincide con ninguna medición. Corregido a las
cifras vivas: **~17 h de reloj, unas 3 de cómputo**, con el motivo, que es la
parte interesante (la GPU está parada el 80 % del tiempo esperando a Drive).

---

## Contrastes que la décima auditoría no vio

Los encontró el verificador de contraste **después** de confirmar que C1 estaba
cerrado, y los cuatro son el mismo fallo en sitios que nadie había revisado. La
prueba de contraste no podía verlos porque mide **variables de la paleta**, y un
color clavado en el CSS le es invisible: puede seguir en verde midiendo una
variable que el navegador ya no usa.

| | Qué | Antes | Ahora |
|---|---|---|---|
| N1 | La franja de error: único sitio donde el color seguía saliendo del tema del navegador | **1,02:1** | 8,76 |
| N2 | El resaltado de `::selection`, clavado en amarillo — **y seleccionar es cómo se consulta el diccionario** | **1,20:1** | 6,11 |
| N3 | Canal de la barra de avance de «Mis libros» | **1,47:1** | 3,66 |
| N3b | Borde de la cita del cuaderno | **1,23:1** | 4,79 |
| N4 | `--ll-lector-texto` era código muerto: `color:inherit` le ganaba | — | se pinta |
| — | El borde del lector iba clavado en gris; el `border` abreviado reescribe el `border-color` de la paleta porque va después | — | `var(--ll-borde)` |

`--ll-seleccion` y `--ll-lector-texto` estaban declaradas en las cinco paletas
y no las pintaba nadie. Ninguna prueba podía delatarlo, porque las pruebas las
medían a ellas.

**Cobertura añadida contra esto:** las tres parejas nuevas en
`_contraste_suficiente` (la prueba admite ahora una **pila** de capas, porque la
selección del lector son tres semitransparentes una encima de otra), las dos
variables de error en la lista de superficies, y una prueba estructural nueva
—«el CSS no clava los colores que ya fallaron»— que abre los bloques `<style>`,
quita los comentarios y exige que esas cinco reglas usen `var(--ll-…)` sin
ningún color literal.

Esa prueba encontró, al escribirla, un caso más que nadie había mirado: el
borde del lector.

---

## Cifras vigentes tras esta ronda

| Qué | Valor | Con qué se comprueba |
|---|---|---|
| Pruebas de estrés | **216** (eran 205 publicadas, 215 antes de la prueba nueva) | `pruebas_extremas.py` |
| Pasos de integración | 27, sin cambio | `pruebas_integracion.py` |
| Parejas de contraste | **70** (14 por paleta; eran 40) | `pruebas_extremas.py` |
| Peor contraste | **4,53** (texto) · **3,11** (título) — recalculado con los 14 pares, sin cambio | `pruebas_extremas.py` |
| `documento.pdf` | 45 páginas, **cero referencias rotas** | `tectonic` + comprobador |

**El 205 estaba publicado en ocho sitios** —`documento.tex` ×3,
`estrategia.md` ×3, `README.md`, `PENDIENTES.md`— y se propagó a los ocho. El
barrido de la cifra vieja queda limpio.

Suites ejecutadas después de todos los cambios, todas en verde:
`pruebas_extremas` (216), `pruebas_integracion` (27), `tests_smoke`,
`pruebas_ficha`, `pruebas_perfil`, `pruebas_desambiguacion`,
`pruebas_audio_atomico`.

---

## Lo que queda abierto, a propósito

- **No se ha vuelto a desplegar.** Todo lo de arriba está medido en local; el
  Space sigue en la versión anterior. Los cambios de CSS hay que verlos en la
  app desplegada, en los dos modos de color, antes de darlos por buenos: es lo
  que dice la skill y es cómo se encontró C1.
- **Los cuatro agujeros C–F de la prueba del fallo 2** (la caja construida
  dentro de un `if`, `visible=False`, `render=False`, anidada en otro acordeón
  cerrado). Son variantes que nunca han ocurrido; quedan nombradas aquí.
- **El verde y el rojo de la pronunciación** (`#3fbf8f`, `#e0485c`) son colores
  semánticos y no salen de la paleta. Es deliberado —verde es «bien» y rojo es
  «mal», no un tema— pero su contraste no está medido.
- **`titulo-*` se mide solo sobre `--ll-fondo`.** Sobre `--ll-fondo-bajo` esos
  mismos colores dan 2,75–2,86. Hoy no falla porque el único `h1` va sobre
  panel, pero el umbral está más cerca de lo que sugiere la prueba.
