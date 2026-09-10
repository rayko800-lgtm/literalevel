# Pendientes de LiteraLevel

Actualizado: **9 de septiembre de 2026, por la noche**.

La rúbrica son 110 puntos y se aprueba con 80. El orden de esta lista es por
puntos en juego, no por comodidad.

**Si acabas de entrar: lee primero
[`auditoria/cierre_auditoria_11.md`](auditoria/cierre_auditoria_11.md)** —la
ronda más productiva del proyecto: 1 crítico, 5 serios y 9 menores, y la razón
fue pedirle al auditor que **mutara el código**—, después
[`auditoria/cierre_2026-09-09_noche.md`](auditoria/cierre_2026-09-09_noche.md)
—el cierre de la décima, hallazgo por hallazgo—, luego
[`auditoria/cierre_2026-09-09.md`](auditoria/cierre_2026-09-09.md) para la
tanda de la tarde, y luego `git log` desde `aed7751`.

Dos avisos del cierre de la noche que valen para cualquiera que toque esto:
**una prueba que pasa no demuestra que cazaría el fallo** —la del fallo del Hub
pasaba también con el código roto, y se comprobó mutándolo—, y **la prueba de
contraste mide variables de la paleta, así que un color clavado en el CSS le es
invisible**. Los cambios de esta ronda **no están desplegados todavía**.

Son muchos commits y tocan archivos compartidos: `app/ui.py`, `app/cuentas.py`
—con interfaz pública nueva: `problemas()`, `declaradas()` y `devolver()`—,
`app/paletas.py`, `app/perfil.py`, `app/scoring.py`, `app/ficha.py`,
`validar_local.py`, `pruebas_extremas.py` y `colab_precalculo.py`.

`auditoria/estado_real.md` **está superado**: úsalo como histórico. El estado
vivo son este archivo, `informe_fable_7.md` e `informe_codex_5.md`.

---

## Bloqueado en Miguel — nadie más puede hacerlo

| Qué | Desbloquea | Por qué solo tú |
|---|---|---|
| **Unidades de Colab** | el catálogo medido | Quedaban **1,9 unidades** (5,3/hora): 21 min de A100. Con el prefetch nuevo el catálogo entero sale por unas 15 unidades en vez de 37 |
| **Micrófono** | parte de **25 pts** (demo en vivo) | Sin él no se puede enseñar la corrección de pronunciación, que es lo que el profesor pidió ver. Unos audífonos con micro bastan |
| **Grabar el vídeo** | **20 pts** | El guion está escrito, cronometrado (561 palabras, 3:44) y compilado en PDF |
| **Cupo de Astra / Codex** | la auditoría de cifras | Agotado el 9 de sep por la noche: murió tras 9.981 tokens sin emitir nada. **No vuelve hasta el 15 de septiembre a las 8:46.** El encargo está escrito y listo en `auditoria/encargo_7.md`; solo hay que relanzarlo. Comprar créditos lo desbloquea antes |
| ~~Token de Hugging Face~~ | **HECHO** | Modelo en `MikeMaki1763/literalevel-v4`, público, descarga sin credenciales verificada |
| ~~Despliegue permanente~~ | **HECHO** | `MikeMaki1763/literalevel`, público, `cpu-basic`, RUNNING. Cuesta 7 USD/mes (cuenta Pro, ya pagada). Arranque medido: 31 s |
| ~~Aceptar la pestaña de Colab~~ | **HECHO** | Conectado a `rayko800@gmail.com`, que es la cuenta con Colab Pro y con `literalevel_bigdata` |

El **conector de Drive de claude.ai** sigue devolviendo `Operation is not
implemented, or supported, or enabled`. Ya no bloquea nada: el Drive se lee
entero a través de Colab con `drive.mount`.

---

## El catálogo, que es lo único grande que falta

| | |
|---|---|
| Libros objetivo (inglés, Project Gutenberg) | 61.642 |
| Descargados a Drive | **31.974** (51,9 %) |
| Analizados por el v4 | ver `perfiles_*.jsonl` en Drive; la sonda del cuaderno los cuenta |
| Velocidad medida en A100 | **61 libros/min** de extremo a extremo. Esta tabla decía 103 y se contradecía con las 17 h de la línea de abajo: 61.642 / 61 = 16,8 h; a 103 saldrían 10. La que cuadra con lo medido en el cuaderno es 61 |
| Cuello de botella | **no es la GPU**: el 80 % del tiempo espera a Drive |
| Ventanas por libro | **332,3 de media**, mediana 266 (medido sobre 5.153) |
| Coste real del catálogo | **2,8 h** de cómputo A100; ~17 h de extremo a extremo |

`colab_precalculo.ipynb` es reanudable: lee los shards que ya hay y se salta
los ids hechos. La descarga **no necesita GPU** — se puede dejar corriendo en
un entorno de CPU gratuito mientras no haya unidades.

---

## Estado de la entrega

- [x] **Documento** (`entrega/documento.md` y `.tex` → `documento.pdf`)
- [x] **Estrategia** (`entrega/estrategia.md`, absorbida en el `.tex`)
- [x] **Cuadernillo** (`entrega/notebook_proyecto.py` → `.ipynb`, 92 celdas)
- [x] **Guion del vídeo** (`entrega/guion_video.md` y `.tex` → PDF)
- [x] **Presentación** (`entrega/presentacion.tex` → PDF, 12 diapositivas)
- [x] **Apartado de competencia** — §8.5 del documento y §5 de la estrategia
- [x] **Manifiesto del corpus externo** (`entrega/manifiesto_corpus_externo.md`)
- [ ] **Vídeo grabado** — bloqueado en el micrófono
- [ ] **Catálogo remedido** — bloqueado en las unidades de Colab

---

## Cifras vigentes, para no volver a publicar las viejas

Todas medidas el 9 de septiembre, y todas reproducibles con un guion del repo.

| Qué | Valor | Con qué se comprueba |
|---|---|---|
| Validación externa | **47 textos** (los 59 menos 2 sin cuerpo y 10 cortos) | `validar_local.py` |
| Medias por nivel | 0,5040 · **0,5561** · 0,9276 · **1,2414** · 1,4952 | `validar_local.py` |
| Cuadro 13 del `.md`, 18 del PDF (baseline) | **0,860 / 0,807 / 0,668** | `validar_local.py` |
| Modelo contra longitud | 0,732 | `validar_local.py` |
| Pruebas de estrés | **232** | `pruebas_extremas.py` |
| Pasos de integración | **27** | `pruebas_integracion.py` |
| Parejas de contraste | **85** (17 por paleta) | `pruebas_extremas.py` |
| Peor contraste | 4,53 (texto) · 3,11 (título) | `pruebas_extremas.py` |
| Modelo / diccionario | 328 MB / 243 MB | `os.path.getsize` |
| Arranque en frío del Space | **31 s** | `medir_arranque.py` |
| Recta de compresión | 0,7196x + 0,3760 (4 medias de Colab); 0,67x + 0,41 con las 5 locales | recalculable |
| Textos que pasan el filtro COMPLETO | **31** (el de la app; aquí se puntúan 47) | `validar_local.py` |
| Palabras habladas del guion | **561** = 3:44 | `tools/contar_guion.py` |
| Coste del despliegue | **7 USD/mes** (cuenta Pro; tarifa 9, con descuento) | API `whoami-v2` |
| Modelo + diccionario | 575 MB | `os.path.getsize` |

---

## Decisiones que quedan abiertas

- **Recalibrar la escala.** Un texto A2 puntúa cerca de B1. Es el accionable
  A7. No se toca sin validar contra el catálogo, y el catálogo aún no está.
- **Publicar el diccionario Kaikki** (243 MB). El guion de subida existe; es la
  mitad que falta del accionable A1.
- **Disco persistente en el Space** (A4). Sin él, la estantería del lector no
  sobrevive a un reinicio del contenedor.
- **El modelo v2 de Codex.** Gana en material graduado y pierde en literatura,
  que es nuestro caso de uso. No entra en esta entrega.
