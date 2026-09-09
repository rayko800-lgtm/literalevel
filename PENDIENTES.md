# Pendientes de LiteraLevel

Actualizado: **9 de septiembre de 2026, 09:25**.

La rúbrica son 110 puntos y se aprueba con 80. El orden de esta lista es por
puntos en juego, no por comodidad.

**Si eres Codex y acabas de entrar: lee primero
[`auditoria/cierre_2026-09-09.md`](auditoria/cierre_2026-09-09.md)**, que dice
qué se corrigió hoy y contra qué se comprobó, y después `git log` desde
`aed7751`. Hay seis commits nuevos y tocan archivos compartidos.

---

## Bloqueado en Miguel — nadie más puede hacerlo

| Qué | Desbloquea | Por qué solo tú |
|---|---|---|
| **Unidades de Colab** | el catálogo medido | Quedaban **1,9 unidades** (5,3/hora): 21 min de A100. Con el prefetch nuevo el catálogo entero sale por unas 15 unidades en vez de 37 |
| **Micrófono** | parte de **25 pts** (demo en vivo) | Sin él no se puede enseñar la corrección de pronunciación, que es lo que el profesor pidió ver. Unos audífonos con micro bastan |
| **Grabar el vídeo** | **20 pts** | El guion está escrito, cronometrado (552 palabras, 3:41) y compilado en PDF |
| ~~Token de Hugging Face~~ | **HECHO** | Modelo en `MikeMaki1763/literalevel-v4`, público, descarga sin credenciales verificada |
| ~~Despliegue permanente~~ | **HECHO** | `MikeMaki1763/literalevel`, público, `cpu-basic`, RUNNING. Arranque medido: 31 s |
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
| Analizados por el v4 | ver `perfiles_*.jsonl` en Drive |
| Velocidad medida en A100 | **60 libros/min** sin prefetch |
| Cuello de botella | **no es la GPU**: el 80 % del tiempo espera a Drive |

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
| Validación externa | **46 textos** (no 45) | `validar_local.py` |
| Medias por nivel | 0,5040 · 0,5480 · 0,9276 · **1,2414** · 1,4952 | `validar_local.py` |
| Cuadro 12 (baseline) | **0,855 / 0,799 / 0,665** | `validar_local.py` |
| Modelo contra longitud | 0,725 | `validar_local.py` |
| Pruebas de estrés | **205** | `pruebas_extremas.py` |
| Pasos de integración | **27** | `pruebas_integracion.py` |
| Parejas de contraste | **40** (8 por paleta) | `pruebas_extremas.py` |
| Peor contraste | 4,53 (texto) · 3,11 (título) | `pruebas_extremas.py` |
| Modelo / diccionario | 328 MB / 243 MB | `os.path.getsize` |
| Arranque en frío del Space | **31 s** | `medir_arranque.py` |
| Recta de compresión | 0,7196x + 0,3760 (4 medias de Colab) | recalculable |

---

## Decisiones que quedan abiertas

- **Recalibrar la escala.** Un texto A1 se anuncia como A2. Es el accionable
  A7. No se toca sin validar contra el catálogo, y el catálogo aún no está.
- **Publicar el diccionario Kaikki** (243 MB). El guion de subida existe; es la
  mitad que falta del accionable A1.
- **Disco persistente en el Space** (A4). Sin él, la estantería del lector no
  sobrevive a un reinicio del contenedor.
- **El modelo v2 de Codex.** Gana en material graduado y pierde en literatura,
  que es nuestro caso de uso. No entra en esta entrega.
