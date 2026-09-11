# Pendientes de LiteraLevel

Actualizado: **11 de septiembre de 2026**, tarde.

La rúbrica son 110 puntos y se aprueba con 80. El orden de esta lista es por
puntos en juego, no por comodidad.

**Si acabas de entrar: lee primero
[`auditoria/cierre_auditoria_17.md`](auditoria/cierre_auditoria_17.md)** —la
última, y la más barata de todas: una pasada ESTRECHA sobre el diff del día
encontró un **crítico** que la auditoría completa de unas horas antes no podía
ver, porque el diff no existía todavía—, luego
[`auditoria/cierre_auditoria_16.md`](auditoria/cierre_auditoria_16.md) —6
serios, con tres de ellos visibles en cámara— y
[`auditoria/cierre_auditoria_15.md`](auditoria/cierre_auditoria_15.md) —7
serios, 6 menores y sobre todo **veintidós mutantes vivos** que se
convirtieron en diecinueve pruebas—, después
[`auditoria/cierre_auditoria_13.md`](auditoria/cierre_auditoria_13.md) —8
serios, 14 menores y 3 notas, con banco de mutantes propio—, después
[`auditoria/cierre_auditoria_11.md`](auditoria/cierre_auditoria_11.md) —la más
productiva del proyecto, y la razón fue pedirle al auditor que **mutara el
código**—, luego
[`auditoria/cierre_2026-09-09_noche.md`](auditoria/cierre_2026-09-09_noche.md)
y [`auditoria/cierre_2026-09-09.md`](auditoria/cierre_2026-09-09.md), y luego
`git log` desde `aed7751`.

Cuatro avisos que valen para cualquiera que toque esto:

1. **Una prueba que pasa no demuestra que cazaría el fallo.** Hay CUATRO formas
   de que no pruebe nada. La tercera la encontró la auditoría 13: el manejador
   rechaza la entrada **antes** de llegar al código que quieres probar, y la
   aserción se cumple sobre el vacío. **La cuarta, la 15, y es la más
   traicionera: un doble puesto por prudencia que anula justo lo que se quiere
   medir.** En la cabecera de `pruebas_extremas.py` había un
   `ui.voz.registrar_fallos = lambda *a, **k: None` para no ensuciar el
   `voz.db` de quien ejecutara las pruebas; desde que `LITERALEVEL_DATOS`
   apunta a una carpeta temporal ya no hacía falta, y mientras estuvo ahí el
   mutante que daba a todos los visitantes la misma `voz.db` **no lo podía
   cazar nadie**. Está en la skill
   `probar-la-app-de-verdad`, y el banco de mutantes vive en
   [`tools/banco_mutantes.py`](tools/banco_mutantes.py) —en el repositorio y
   no en `scratchpad/`, porque un subagente de auditoría sobrescribió el
   archivo cuando estaba en el bloc compartido y se perdió entero—.
2. **La prueba de contraste mide variables de la paleta**, así que un color
   clavado en el CSS le es invisible.
3. **Arreglar algo puede quitar una red que otra cosa usaba.** Al limpiar los
   títulos de capítulo, la portadilla legal de tres libros pasó a contar como
   capítulo, porque el detector de licencia vivía de ese título sin que nadie lo
   hubiera escrito. Se vio midiendo lo mismo con el árbol de antes y el de
   después, no leyendo.

**El Space está al día hasta la auditoría 17**, subida el 11 de septiembre de
2026 y cotejada por hash: los catorce archivos publicados son idénticos byte a
byte a los locales. **No te fíes de esta línea**, que es la que se queda vieja:
`python tools/desplegar_app.py` lo compara y lo dice él mismo. La auditoría 16
ya avisó una vez de que esta frase iba por detrás del repositorio.

Son muchos commits y tocan archivos compartidos: `app/ui.py`, `app/cuentas.py`
—con interfaz pública nueva: `problemas()`, `declaradas()` y `devolver()`—,
`app/paletas.py`, `app/perfil.py` —con `HOLGURA`, que es **la única** holgura de
recomendación y la lee `ui`—, `app/scoring.py`, `app/ficha.py` —con `miles()`,
que usan `ui` y `catalogo`—, `app/catalogo.py`, `validar_local.py`,
`pruebas_extremas.py`, `pruebas_lexicon.py` y `colab_precalculo.py`.

Y dos de Codex, avisados en su commit: `app/reader.py` (la cabecera corrida de
Gutenberg y los pies de ilustración) y `app/lexicon.py` (`llamadas_de_pago` en
`ResultadoLexico` y la clave del audio normalizada).

`auditoria/estado_real.md` **está superado**: úsalo como histórico. El estado
vivo son este archivo, `informe_fable_7.md` e `informe_codex_5.md`.

---

## Bloqueado en Miguel — nadie más puede hacerlo

| Qué | Desbloquea | Por qué solo tú |
|---|---|---|
| ~~Unidades de Colab~~ | **YA NO BLOQUEA** | La **T4 gratuita** hace el trabajo: medido el 10 de septiembre de 2026, 492 ventanas/s, que son **84 libros/min** contra los 61 de la A100 de pago. El cuello de botella era Drive, no la tarjeta, y el prefetch lo tapó. El catálogo entero son ~12 h de T4 gratis y reanudables. Las «15 unidades» ya no hacen falta |
| **Micrófono** | parte de **25 pts** (demo en vivo) | Sin él no se puede enseñar la corrección de pronunciación, que es lo que el profesor pidió ver. Unos audífonos con micro bastan |
| **Grabar el vídeo** | **20 pts** | El guion está escrito, cronometrado (578 palabras, 3:51) y compilado en PDF |
| **Cupo de Astra / Codex** | la auditoría de cifras | Agotado el 9 de sep por la noche: murió tras 9.981 tokens sin emitir nada. **No vuelve hasta el 15 de septiembre a las 8:46.** El encargo está escrito y listo en `auditoria/encargo_7.md`; solo hay que relanzarlo. Comprar créditos lo desbloquea antes |
| ~~Token de Hugging Face~~ | **HECHO** | Modelo en `MikeMaki1763/literalevel-v4`, público, descarga sin credenciales verificada. El token vive en `C:\Users\laura\.hf_token` y **hay que revocarlo** cuando se acabe de subir |
| ~~Despliegue permanente~~ | **HECHO** | `MikeMaki1763/literalevel`, público, `cpu-basic`, RUNNING. Cuesta 7 USD/mes (cuenta Pro, ya pagada). Arranque medido: 31 s hasta `RUNNING`, 32 s hasta que responde |
| ~~Aceptar la pestaña de Colab~~ | **HECHO** | Conectado a `rayko800@gmail.com`, que es la cuenta con Colab Pro y con `literalevel_bigdata` |

El **conector de Drive de claude.ai** sigue devolviendo `Operation is not
implemented, or supported, or enabled`. Ya no bloquea nada: el Drive se lee
entero a través de Colab con `drive.mount`.

---

## El catálogo, que es lo único grande que falta

Cifras vivas: **medidas el 9 de septiembre de 2026** y en movimiento mientras
la descarga y el precalculo sigan corriendo. Sin fecha son falsas mañana.

| | |
|---|---|
| Libros objetivo (inglés, Project Gutenberg) | 61.642 de 79.337 entradas (instantánea del catálogo oficial del 7 de septiembre de 2026) |
| Descargados a Drive | **31.974** (51,9 %) el 9 de septiembre de 2026 |
| **Con perfil medido por el v4** | **29.875** el 10 de septiembre de 2026, sin duplicados (29.875 líneas, 29.875 ids distintos). En `literalevel_bigdata/catalogo_medido.csv` |
| Velocidad | **84 libros/min en T4 gratis** (492 ventanas/s ÷ 350 ventanas por libro), medido el 10 de septiembre de 2026. En A100 sin prefetch eran 61 de extremo a extremo, con la tarjeta parada el 80 % esperando a Drive. **La gratis con prefetch gana a la de pago sin él** |
| Cuello de botella | **no es la GPU**: el 80 % del tiempo espera a Drive |
| Ventanas por libro | **332,3 de media**, mediana 266 (medido sobre 5.153 el 9 de septiembre de 2026) |
| Coste real del catálogo | **2,8 h** de cómputo A100; ~17 h de extremo a extremo |

**Lo que falta ya no es medir: es DESCARGAR.** 29.875 de los ~31.974 textos que
hay en Drive tienen perfil; quedan ~29.700 libros del catálogo oficial sin bajar.
Y descargar **no necesita GPU ni unidades**.

> **Y un hallazgo que hay que decidir, pero NO antes del vídeo.** La dificultad
> media de los 29.875 es **1,75 sobre 2**, con el cuartil 1 en 1,664: **al menos
> tres cuartas partes del corpus puntúan C1 o por encima**. El catálogo que usa
> la app dice lo contrario —sus etiquetas del v1 son 60,4 % A1—. No es un fallo
> del v4: sus propias medias en los textos graduados van de 0,50 (A1) a 1,50
> (C1), así que que la literatura del XIX promedie 1,75 es lo esperable. Lo que
> hay que decidir es qué le ofrece la app a un lector de B1. **La app no se ha
> tocado**: sigue con `catalogo_recomendaciones.csv`. Cambiarla a dos días de
> grabar sería meter una variable enorme en la demo. Todo el detalle en
> [`auditoria/medicion_catalogo_2026-09-10.md`](auditoria/medicion_catalogo_2026-09-10.md).

`colab_precalculo.ipynb` es reanudable: lee los shards que ya hay y se salta
los ids hechos. La descarga **no necesita GPU** — se puede dejar corriendo en
un entorno de CPU gratuito mientras no haya unidades.

---

## Estado de la entrega

- [x] **Documento** (`entrega/documento.md` y `.tex` → `documento.pdf`)
- [x] **Estrategia** (`entrega/estrategia.md`, absorbida en el `.tex`)
- [x] **Cuadernillo** (`entrega/notebook_proyecto.py` → `.ipynb`, 92 celdas)
- [x] **Guion del vídeo** (`entrega/guion_video.md` y `.tex` → PDF)
- [x] **Presentación** (`entrega/presentacion.tex` → PDF, 13 diapositivas)
- [x] **Apartado de competencia** — §8.5 del documento y §5 de la estrategia
- [x] **Manifiesto del corpus externo** (`entrega/manifiesto_corpus_externo.md`)
- [ ] **Vídeo grabado** — bloqueado en el micrófono
- [ ] **Catálogo remedido** — bloqueado en las unidades de Colab

---

## Cifras vigentes, para no volver a publicar las viejas

Medidas el 9 de septiembre de 2026 salvo donde la fila diga otra fecha, y
todas reproducibles con un guion del repo.

| Qué | Valor | Con qué se comprueba |
|---|---|---|
| Validación externa | **47 textos** (los 59 menos 2 sin cuerpo y 10 cortos) | `validar_local.py` |
| Medias por nivel | 0,5040 · **0,5561** · 0,9276 · **1,2414** · 1,4952 | `validar_local.py` |
| Cuadro 13 del `.md`, 18 del PDF (baseline) | **0,860 / 0,807 / 0,668** | `validar_local.py` |
| Modelo contra longitud | 0,732 | `validar_local.py` |
| Pruebas de estrés | **301** | `pruebas_extremas.py` |
| Pasos de integración | **27** | `pruebas_integracion.py` |
| Parejas de contraste | **85** (17 por paleta) | `pruebas_extremas.py` |
| Peor contraste | 4,53 (texto) · 3,11 (título) | `pruebas_extremas.py` |
| Carpeta `modelo_v4/` / diccionario | 332 MB / 243 MB (los pesos solos son 328) | `os.path.getsize`, remedido el 10 de septiembre de 2026 |
| Arranque en frío del Space | **31 s** hasta `RUNNING`, **32 s** hasta que responde | `medir_arranque.py` |
| Recta de compresión | 0,7196x + 0,3760 (4 medias de Colab); 0,67x + 0,41 con las 5 locales | recalculable |
| Textos que pasan el filtro COMPLETO | **36** (el de la app; aquí se puntúan 47) | `validar_local.py` |
| Palabras habladas del guion | **578** = 3:51 | `tools/contar_guion.py` |
| Coste del despliegue | **7 USD/mes** (cuenta Pro; tarifa 9, con descuento) | API `whoami-v2` |
| Carpeta + diccionario | 575 MB (332,1 + 243,3) | `os.path.getsize`, remedido el 10 de septiembre de 2026 |

---

## Decisiones que quedan abiertas

- **Recalibrar la escala.** Un texto A2 puntúa cerca de B1. Es el accionable
  A7. No se toca sin validar contra el catálogo, y el catálogo aún no está.
- **Publicar el diccionario Kaikki** (243 MB). El guion de subida existe; es la
  mitad que falta del accionable A1.
- ~~**Disco persistente en el Space** (A4)~~ **HECHO** el 10 de septiembre de
  2026 por la noche. Bucket privado `MikeMaki1763/literalevel-datos` montado en
  `/data`, con `LITERALEVEL_DATOS=/data`. Verificado reiniciando el Space: el
  perfil sigue ahí. Detalle en `DESPLIEGUE.md`.
- **El modelo v2 de Codex.** Gana en material graduado y pierde en literatura,
  que es nuestro caso de uso. No entra en esta entrega.
