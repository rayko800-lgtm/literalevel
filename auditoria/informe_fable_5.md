# Informe Fable 5 — verificación del inventario y daños colaterales

Fecha: 9 de septiembre de 2026. Árbol de trabajo en HEAD `6159f7e` («los
entregables, al dia»), sin cambios sin confirmar. El inventario
`auditoria/estado_real.md` se escribió contra `974308b`; desde entonces hay tres
commits (`cc99bc8`, `75d9ef9`, `6159f7e`) que tocan `documento.md`,
`documento.tex`, `estrategia.md`, `guion_video.*`, `notebook_proyecto.*`,
`README.md`, `app/scoring.py`, `arrancar_gpu.py` y `pruebas_extremas.py`. Se ha
leído ese diff entero y se ha ido al archivo y a la línea en cada caso. No se
modificó ningún archivo del proyecto: este informe es la única escritura.

**Recuento de este informe: 2 CRÍTICO · 5 SERIO · 6 MENOR · 1 DUDA.**
**Del inventario (38 hallazgos ABIERTO o CERRADO A MEDIAS): 2 YA CERRADO,
1 CERRADO A MEDIAS, 1 cambiado a peor, 34 SIGUEN ABIERTOS.**

---

## Parte 2 — Lo que las correcciones rompieron (o dejaron a medias)

### CRÍTICO

**C1. Los entregables se contradicen sobre si la aplicación está desplegada.**
- `README.md:7-9`: «**Está desplegada y funcionando:** / - Aplicación →
  <https://huggingface.co/spaces/MikeMaki1763/literalevel>».
- `entrega/presentacion.tex:359`: «`huggingface.co/spaces/MikeMaki1763/literalevel`».
- `entrega/documento.md:1003-1004` (limitación 12): «**La aplicación no está
  desplegada de forma permanente.** El enlace actual es un túnel temporal».
  Idéntico en `documento.tex:2339-2340`.
- `entrega/estrategia.md:361` y `documento.tex:794` (accionable A2): «El
  enlace actual es un túnel temporal que muere al apagar el equipo. Es el mayor
  riesgo de la entrega».

El commit `6159f7e` puso el enlace de Spaces en el README y en la diapositiva
final y no tocó la limitación 12 ni el accionable A2. Sea cual sea la verdad
hoy, un entregable miente: o el README y la presentación se adelantan, o el
documento y la estrategia describen un riesgo que ya no existe. Es lo primero
que un profesor comprueba, porque es un clic.

**C2. La corrección de «286 ventanas» inventó una medición que no existe.**
Cuatro auditores pidieron cambiar 286 por 300. En vez de eso,
`documento.md:848-852` dice ahora: «Comprobado en dos tandas distintas, y
conviene identificarlas porque circulan las dos cifras: en la tanda de **286
ventanas** —catorce capítulos completos de *Crimen y castigo*, agrupando por
capítulo— salen 286/286 valores idénticos con MAE 0,000000000; en la de **300
ventanas** con lotes fijos, 300/300». Igual en `documento.tex:2146-2150`.

Verificado contra la fuente: `informe_velocidad.md:83` describe la tanda de 286
como el **barrido de hilos** («286 ventanas (14 capítulos completos de C&P),
lote = capítulo») con una tabla de hilos frente a ventanas/s; la única
comprobación de identidad del informe es la de `:122-124`, con **300**
ventanas. `grep -rn 286` sobre `informe_velocidad.md`, `app/scoring.py`,
`colab_precalculo.py`, `pruebas_extremas.py` y `tests_smoke.py` devuelve solo
`informe_velocidad.md:83` y `app/scoring.py:249` —y esta última línea la añadió
la misma corrección («hay otra de 286 agrupando por capitulo, y las dos dan el
mismo resultado»). No hay en el repositorio ningún «286/286 idénticos» ni
ningún «MAE 0,000000000» sobre 286 ventanas. Si esa medición se hizo, no está
escrita en ninguna parte; si no se hizo, el documento afirma ahora un
experimento que no ocurrió, y lo hace justo donde intenta corregir un error.

### SERIO

**S1. El `.md` numera los cuadros 1 a 14 y luego salta al 17.**
`documento.md:902`: «*Cuadro 17. Cifras publicadas frente a las de este
proyecto…*». Los rótulos van `Cuadro 1` (`:163`) … `Cuadro 14` (`:837`); no
existe ningún Cuadro 15 ni 16. El `.tex` numera solo con `\label{cuad:competencia}`,
así que allí no se nota; en el `.md`, que es el que se lee en GitHub, sí.

**S2. La cabecera del cuadro de competencia se corrigió en el `.md` y no en el
`.tex`.** `documento.md:896`: «| Alternativa | Cifra publicada | La nuestra |».
`documento.tex:2200`: «\textbf{Alternativa} & \textbf{Su número} & \textbf{El
nuestro}». El commit `cc99bc8` cambió filas y pie en los dos archivos y la
cabecera solo en uno. El pie nuevo insiste en que «No son comparaciones cara a
cara»; la cabecera vieja del `.tex` («Su número / El nuestro») dice lo contrario.

**S3. El accionable A1 dice «hecho» en el `.tex` y «pendiente» en
`estrategia.md`.** `documento.tex:792`: «\textbf{A1} & \textbf{Publicar el
modelo (328 MB)} como repositorio abierto & … & \textbf{HECHO}:
\cod{MikeMaki1763/literalevel-v4}». `estrategia.md:360`: «| **A1** |
**Publicar el modelo (328 MB) y el diccionario (243 MB)** como repositorios
abiertos, con el guion de subida ya escrito | Desbloquea la reproducibilidad
del cuaderno, **que hoy no corre en un Colab ajeno** | … | El cuaderno corre de
principio a fin en un Colab limpio». Los accionables A2 y A3 sí están
sincronizados; A1 no, y además el `.tex` perdió el diccionario por el camino.

**S4. El README se contradice a sí mismo sobre dónde está el modelo.**
`README.md:162`: «| `modelo_v4/` | 317 MB | Drive, `literalevel_bigdata`
(privado; ver más abajo) |». Diez líneas después, `README.md:171-173`: «El
modelo v4 **está publicado** en Hugging Face, en un repositorio público y sin
credenciales». Y `app/scoring.py:186` sigue mandando a «Drive
(literalevel_bigdata)». Es el hallazgo 18 del inventario, arreglado en un
párrafo y no en la tabla que lo precede. (Ver también M4 sobre los 317 MB.)

**S5. El pie del Cuadro 10 y el balance de exclusiones siguen como estaban, y
el `.md` y el `.tex` los repiten.** `documento.md:689-690` y
`documento.tex:1624-1625`: «sobre los 45 textos que sobreviven a la extracción
de los PDF». `README.md:113`: «extracción de los PDF: en local sobreviven 45
textos de los 59 originales». Y `documento.md:702-704` / `documento.tex:1687-1689`:
«de los 59 originales, uno no está disponible y dos no tienen cuerpo
localizable. Pero **otros diez los rechaza `scoring.continuous_prose`**» —
59 − 1 − 2 − 10 = 46, y el cuadro dice 45. No es daño nuevo; se lista aquí
porque es aritmética visible a primera lectura y lleva cuatro auditorías sin
cerrarse.

### MENOR

**M1. Las menciones a «auditoría externa» quedaron asimétricas.**
`documento.tex:1524-1525`: «Lo detectó una auditoría externa y se retira en
lugar de maquillarse»; el pasaje equivalente en `documento.md:615` dice solo «Se
retira en lugar de maquillarla». A la inversa, `documento.md:984-985` («Lo
señaló una auditoría externa y es una crítica justa») no tiene equivalente en
la limitación 9 del `.tex`. Ninguna frase está rota; los dos archivos ya no
dicen lo mismo.

**M2. El arreglo de la frase rota dejó una repetición.** `documento.md:648-652`:
«citaba una tarjeta `metricas_literalevel_v4.json` que no existe. […] Se
corrige diciéndolo, no citando un archivo que no existe». Dos «que no existe»
en cuatro líneas; el `.tex` termina en «…o rehacerla.» y no lo repite.

**M3. El absoluto «no puede mover un decimal» está en tres sitios, no en uno.**
El inventario cita `documento.md:844`; hoy es `documento.md:846`,
`documento.tex:2144` y, además, el pie de la figura del pipeline,
`documento.tex:415`: «hay relleno y reagrupar en lotes distintos no puede
mover un decimal». Si se corrige, son tres.

**M4. 317 MB sigue en dos sitios.** `README.md:162` y `DESPLIEGUE.md:11`
(«`modelo_v4/` | **317 MB**») frente a `documento.md:634` y `documento.tex:792,1558`
(«328 MB»). El inventario solo citaba el README.

**M5. El recuento de pruebas se alejó más de la realidad.** `pruebas_extremas.py`
creció 83 líneas en `75d9ef9`; hoy tiene **206** líneas con `prueba(` (el
inventario contó 198). Los entregables siguen diciendo 147 (`README.md:145`),
183 (`estrategia.md:142,220,388`; `documento.tex:674,746,832`) y 27 pasos
(`README.md:146`, `estrategia.md:388`, `documento.tex:832`) frente a 28 en
`pruebas_integracion.py`.

**M6. El guion pasó de «ya medidos» a «medición en curso» y el Resumen no.**
`guion_video.md:137-138`: «*medición en curso; lo que no está medido, se mide
al abrirlo*». `documento.md:49-50` y `documento.tex:260`: «un catálogo en curso
de remedición». Aquí sí coinciden; se anota como comprobado, no como fallo.

### DUDA

**D1. ¿Qué dice hoy la aplicación desplegada?** Si el Space existe, el
accionable A2 («9 USD un mes», «Gradio sobre plan de pago personal»,
`estrategia.md:361`, `documento.tex:794`) y la limitación 12 («descarta
cualquier plan gratuito de 512 MB») describen una decisión distinta de la que
se tomó. No se puede verificar desde el repositorio; se deriva de C1.

---

## Parte 1 — Verificación del inventario, hallazgo por hallazgo

Solo los que `estado_real.md` marcaba ABIERTO o CERRADO A MEDIAS. Ubicaciones
de hoy.

| # | Hallazgo (según el inventario) | Veredicto hoy | Dónde y cita |
|---|---|---|---|
| 1 | 6,3 h de A100 en `investigacion/` | **SIGUE ABIERTO** | `investigacion/competencia.md:119` «**6,3 horas de una A100** (§8.3 del documento)», `:326` «6,3 horas de A100», `:481` «6,3 horas de A100 \| `documento.md` §8.3»; `investigacion/transformer_v5.md:190` «6,3 h de A100» |
| 2 | Pie del Cuadro 10 atribuye a la extracción lo que hace el filtro | **SIGUE ABIERTO** | `documento.md:690`, `documento.tex:1625` «sobreviven a la extracción de los PDF»; `README.md:113` |
| 3 | Balance 59−1−2−10 = 46, cuadro dice 45 | **SIGUE ABIERTO** | `documento.md:702-704`, `documento.tex:1687-1689` |
| 4 | Lote 64/128 no se alcanza en vivo; pie del Cuadro 14 sin la salvedad | **SIGUE ABIERTO** | `app/ui.py:1198` «vs = p.perfil_de_texto(…)» dentro del bucle; `documento.md:837-838` y `documento.tex:2091-2092`: el pie solo dice «incluida la tokenización y las transferencias» |
| 5 | Cuaderno: «8 ventanas representan un libro entero» | **SIGUE ABIERTO** | `entrega/notebook_proyecto.py:1547` «**Está medida y la respuesta es sí:**» |
| 6 | Ficha: estadísticas de muestra y «a su ritmo» | **SIGUE ABIERTO** | `documento.md:803` y `documento.tex:1943` «tiempo de lectura a su ritmo»; `estrategia.md:71` y `documento.tex:585` «cuánto tarda en leerlo **a su ritmo**» |
| 7 | «Libros que pueda terminar» en el Resumen; 0,65 sin declarar | **SIGUE ABIERTO** en el Resumen (`documento.md:25`, `documento.tex:234-235` «le busca libros que pueda terminar»). El 0,65 sí aparece ya en `estrategia.md:50` y `documento.tex:552` («Pesan 0,65 en el cálculo del nivel»), aunque como decisión justificada, no como heurístico sin validar |
| 8 | `arrancar_gpu.py` con la tanda vieja de velocidades | **YA CERRADO** | `arrancar_gpu.py:13-14` «8,19 ventanas/s … 112,7 ventanas/s      13,8x» |
| 9 | Cuadro 11 no lo calcula ningún guion | **SIGUE ABIERTO** | `validar_local.py` no contiene `spearman`, `polyfit` ni correlación parcial (grep vacío) |
| 10 | Recta 0,72x+0,38 sin procedencia | **SIGUE ABIERTO** | `documento.tex:1767` «{0.72*x+0.38}» sobre los cinco puntos locales; `:1796` «la pendiente es $0{,}72$ y no $1$»; `documento.md:731` y `:956` «`predicho ≈ 0,72 × real + 0,38`» sin nota |
| 11 | `validar_local.py` une las líneas | **SIGUE ABIERTO** | `validar_local.py:35` «return " ".join(utiles) or None» |
| 12 | MAE 0,499 sin escala | **SIGUE ABIERTO** | `documento.md:659-660`, `documento.tex:1587` «MAE de 0,499 niveles en el conjunto de validación» |
| 13 | Cuaderno: «Validación externa ciega» sobre tabla tecleada | **SIGUE ABIERTO** | `notebook_proyecto.py:1654` «## 7.2 Validación externa ciega»; también `:244` |
| 14 | «Audio de Wiktionary … nada de eso usa red» (cinco sitios) | **SIGUE ABIERTO** en los cinco | `documento.md:1011-1012`, `documento.tex:740-741` y `:2346-2347`, `estrategia.md:213-214`, `README.md:182-183` «audio de Wiktionary, buscador y puntuación no usan red» |
| 15 | «286» donde la fuente dice 300 | **Cambiado, a peor** — ver C2 | `documento.md:848-852`, `documento.tex:2146-2150`, `app/scoring.py:249` |
| 16 | «No hay relleno» | **SIGUE ABIERTO** | `documento.md:847-848`, `documento.tex:2145-2146`, `documento.tex:415` |
| 17 | «No puede mover un decimal» (absoluto) | **SIGUE ABIERTO** | `documento.md:846`, `documento.tex:2144`, `documento.tex:415` |
| 18 | −0,330 emparejado con 18 libros | **SIGUE ABIERTO** | `documento.md:1096` «de 18 libros a los 45.345 del SPGC— dejó la correlación en −0,326 frente a −0,330»; `documento.tex:2432-2433` |
| 19 | «De seis niveles a cuatro» | **SIGUE ABIERTO** | `documento.md:414-415`, `documento.tex:1149` «se encoge de seis niveles a cuatro (A2–C1)» |
| 20 | Tres recuentos de pruebas (147/183/198) y 27/28 pasos | **SIGUE ABIERTO, y más lejos** — ver M5 | `README.md:145-146`; `estrategia.md:142,220,388`; `documento.tex:674,746,832`; real: 206 `prueba(`, 28 pasos |
| 21 | «La peor paleta, 9,51» | **SIGUE ABIERTO** | `estrategia.md:132` «la peor mide **9,51**», `:387`; `documento.tex:662`, `:831` |
| 22 | 317 MB frente a 328 MB | **SIGUE ABIERTO** | `README.md:162`, `DESPLIEGUE.md:11` |
| 23 | README dice «no publicado»; `scoring.py` manda a Drive | **CERRADO A MEDIAS** — ver S4 | `README.md:171-173` corregido; `README.md:162` y `app/scoring.py:186` no |
| 24 | Gradio sin fijar | **SIGUE ABIERTO** | `requirements.txt:5` «gradio>=6.0» |
| 25 | `informe_velocidad.md` con apartados «(pendiente)» | **SIGUE ABIERTO** | `informe_velocidad.md:214`, `:218` «_(pendiente)_»; sin nota de cabecera |
| 26 | Tope de 8 ventanas no declarado en §7.4 | **SIGUE ABIERTO** | `documento.md:635-636`, `documento.tex:1558-1559` «Puntúa bloques de 250 palabras truncados a 256 tokens y promedia sin ponderar» |
| 27 | Composición y partición del corpus de anclaje | **SIGUE ABIERTO** | `modelo_v4/` contiene solo `README.md`, `config.json`, `model.safetensors`, `tokenizer.json`, `tokenizer_config.json` |
| 28 | 0,00037 (fp16 A100) sin respaldo | **SIGUE ABIERTO** | `documento.md:762`, `documento.tex:1838` «la desviación medida es 0,00037 de media» |
| 29 | 0,004 en cinco libros reales sin respaldo | **SIGUE ABIERTO** | `documento.md:757`, `documento.tex:1828` |
| 30 | «Ajena al proyecto» sin decir prima | **SIGUE ABIERTO** (leve) | `documento.md:190` «Una lectora de quince años ajena al proyecto» |
| 31 | Desviaciones poblacionales sin declarar | **SIGUE ABIERTO** (trivial) | `documento.md:681` «\| Desviación \|»; `validar_local.py:84` «np.std(v)» |
| 32 | Los 59 PDF no enumerados | **SIGUE ABIERTO** | `validar_local.py:55` glob `*LearnEnglish-Reading*.pdf`; ningún manifiesto en `entrega/` |
| 33 | `escala_cefr.dat` sin decir qué extremo incluye | **SIGUE ABIERTO** | `entrega/datos_figuras/escala_cefr.dat:1` «desde hasta etiqueta» |
| 34 | Frase rota «Lo detectó una / se corrige diciéndolo» | **YA CERRADO** | `documento.md:651-652` «…o rehacerla. Se corrige diciéndolo, no citando un archivo que no existe.» (deja la repetición de M2) |
| 35 | Codex H23: datos individuales del baseline | **SIGUE ABIERTO** (es el mismo #9) | `validar_local.py` |
| 36 | Codex H06, fleco de intervalos | **SIGUE ABIERTO** (es el mismo #33) | `escala_cefr.dat` |
| 37 | «Sin mover un decimal», titular cuantificado | **SIGUE A MEDIAS** (es el mismo #17) | `documento.md:1100` cuantifica; `:846` sigue absoluto |
| 38 | Fable-3 dudas: artefactos ausentes | **NO VERIFICABLE**, sin cambios | limitaciones 9-11 |

Ningún veredicto del inventario ha resultado **FALSO**: todas las ubicaciones
citadas existían y decían lo que el inventario afirmaba (con los desplazamientos
de línea del diff de `cc99bc8`, que mueve el bloque de 8.3 dos líneas y el de 8.5
seis).

---

## Lo que está bien y podía estar mal

- **Referencias cruzadas del `.tex`:** 39 etiquetas distintas referenciadas con
  `\ref`/`\eqref`, y **las 39 tienen `\label`**. No hay ninguna referencia rota.
  Quedan 13 etiquetas sin referenciar (`cuad:competencia`, `cuad:fuentes`,
  `cuad:metricas`, `cuad:riesgos`, `cuad:tabulares`, `fig:competencia`,
  `fig:dominio`, `sec:competencia`, `sec:eda`, `sec:formulacion`,
  `sec:procesamiento`, `sec:progresion`, `sec:recorrido`); es inofensivo.
- **Números de cuadro y figura en el `.tex`:** no hay ninguno escrito a mano;
  todos van por `\ref`, así que no pueden descuadrarse al insertar tablas.
- **Numeración de secciones del `.md`:** 1 a 11 sin huecos; 7.1–7.6 y 8.1–8.5
  correlativos. Las referencias internas escritas a mano («apartados 4 a 7»,
  «apartado 8», «apartado 6.1», «apartado 7.3», «apartado 7.4», «§4.3»)
  apuntan a apartados que existen y tratan de lo que se dice.
- **Limitaciones:** 14 ítems, en el mismo orden, en `documento.md:936-1016` y en
  `documento.tex:2272-2352`. «La limitación 6» citada en el Resumen
  (`documento.md:34`, `documento.tex:245`) es en los dos archivos «La
  validación no es enteramente independiente de la exploración», que es la
  correcta. «Accionable A7» (`documento.tex:1796`) es «Calibrar la escala», que
  es el correcto.
- **Texto duplicado:** ninguna línea consecutiva repetida ni ninguna frase de
  más de 70 caracteres repetida en `documento.md` ni en `documento.tex` (las
  únicas líneas idénticas del `.tex` son cabeceras de tabla y separadores de
  comentario).
- **Frases sin sujeto:** el barrido de líneas que terminan en artículo,
  preposición o conjunción no encontró ninguna frase rota en los dos documentos;
  la del inventario está arreglada.
- **`guion_video.md` y `guion_video.tex`** dicen lo mismo tras `6159f7e` (547
  palabras, 0,908 «interno», «medición en curso» en los dos).
- **`presentacion.tex`** no contiene ninguna cifra retirada (6,3 h, 0,91, 147
  pruebas, Flesch, 54.600 USD, 11,7×).
- **El Cuadro 4** (−0,379 / −0,330 / −0,326 para 18 / 397 / 45.345 libros) es
  idéntico en `documento.md:387-389` y `documento.tex:1121-1123`; el error de los
  «18 libros» está solo en las conclusiones.
- **El §8.5 «Contra quién compite» y el §5 de `estrategia.md`** se corrigieron a
  la vez y en el mismo sentido (Lexile como coste de procesamiento, el LLM
  *zero-shot* como justificación y no como victoria, «auditable en lo que se
  puede auditar»); el `.md` y el `.tex` coinciden salvo la cabecera de S2.
- **La correlación parcial «indefinida» del contador de palabras** se explicó
  igual en `documento.md:723-725`, `documento.tex:1717-1720`,
  `estrategia.md:345-348` y `notebook_proyecto.py:1730-1737`. Es la única
  corrección de estas horas que llegó a los cuatro sitios.

---

## ¿Queda algo en estos entregables que avergonzaría al autor si lo lee un profesor universitario?

**Sí.** Cinco cosas, y las cinco se ven sin leer el código:

1. El README y la diapositiva final dicen que la aplicación está desplegada en
   Hugging Face; el documento y la estrategia dicen que es un túnel temporal y
   que ese es «el mayor riesgo de la entrega» (C1).
2. El documento afirma una comprobación de «286/286 valores idénticos» que no
   consta en ninguna parte del repositorio; la fuente solo tiene la de 300 (C2).
3. Los cuadros del `.md` van del 14 al 17 (S1).
4. La aritmética de exclusiones da 46 y el cuadro dice 45, «seis niveles» son
   cinco, y −0,330 se atribuye a 18 libros cuando el propio Cuadro 4 dice que es
   de 397 (S5, #18, #19): tres errores de una línea cada uno que llevan cuatro
   auditorías señalados.
5. El accionable A1 está «HECHO» en el PDF y «pendiente, el cuaderno hoy no
   corre» en `estrategia.md` (S3).

Todo lo demás de la lista es trabajo de redacción o de coherencia entre
archivos, y ninguno invalida un resultado. Pero la respuesta a la pregunta, con
esas palabras, es que sí queda.
