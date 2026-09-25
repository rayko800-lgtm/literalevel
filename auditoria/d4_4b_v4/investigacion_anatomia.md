# Anatomía del habla: cifras utilizables para modelar en 3D (LiteraLevel)

Investigación de apoyo para el visor 3D (corte sagital + recuadro frontal) de LiteraLevel. Objetivo: sustituir las mallas actuales (punta de lengua fina/plana en /θ/, dorso en bloque en /k/, labios de maniquí, cara de muñeco) por proporciones ancladas en literatura anatómica, de rtMRI/cine-MRI y de biomecánica.

**Cómo leer las tablas:** «valor típico» es una media reportada; «rango» cubre la variación entre estudios/hablantes cuando se encontró; «fuente» es autor, año y URL. Donde no se encontró una cifra con respaldo académico, se indica explícitamente «sin fuente fiable» en vez de inventarla.

---

## 1. Lengua

### 1.1 Partes y terminología
Ápice (punta), lámina (blade, justo detrás del ápice, la zona que se eleva hacia el paladar en consonantes coronales), predorso, dorso (cuerpo), raíz (base, pared anterior de la faringe). El ápice es la porción más anterior y más móvil del órgano (Kenhub, 2024, https://www.kenhub.com/en/library/anatomy/tongue).

### 1.2 Dimensiones globales

| Medida | Valor típico | Rango | Fuente |
|---|---|---|---|
| Longitud total de la lengua | ~9,0 cm | 7,5–10,5 cm | medición en especímenes anatómicos, recogida en scirps.blog (2024), https://scirps.blog/average-length-width-human-tongue-4864 |
| Anchura, tercio anterior | 2,9 cm | 2,5–3,0 cm | ídem |
| Anchura, tercio medio | 6,4 cm | 6,0–6,6 cm | ídem |
| Anchura, tercio posterior | 5,0 cm | 4,0–6,0 cm | ídem |
| Grosor (profundidad), lámina, medial/lateral | 14 mm / 11 mm | — | ídem |
| Grosor, cuerpo, medial/lateral | 17 mm / 12 mm | — | ídem |
| Grosor, base, medial/lateral | 17 mm / 11 mm | — | ídem |
| Peso | 99 g (hombre) / 79 g (mujer) | — | ídem |

**Consenso:** la lengua se afina de posterior a anterior en anchura y en grosor lateral; el perfil medial es más grueso que el lateral en toda su longitud, consistente con el surco medio (ver 1.4). Esta fuente agrega estudios de especímenes; no es un único paper primario citado con DOI, así que trátese como orientativa, no como cifra de laboratorio única.

**Punta y lámina específicamente:** no se encontró una fuente académica que dé un grosor en mm solo del ápice (los últimos 10–15 mm anteriores) de forma aislada de «lámina». La cifra de lámina (11–14 mm) es la mejor aproximación disponible. **Sin fuente fiable** para un valor propio de «solo la punta».

### 1.3 Frenillo lingual
El rango normal del frenillo sublingual es >16 mm (medido desde la punta de la lengua hasta la inserción del frenillo) (Yoon et al., 2017, validación de escalas de ankiloglosia, https://aomtinfo.org/wp-content/uploads/2016/08/2017-Toward-a-functional-defintion-of-ankyloglossia-frenulum-length-mobility-in-1052-subjects-Sleep-Breathing-Yoon.pdf). Clasificación de Kotlow: Tipo 1 (normal-corto) 12–16 mm, Tipo 2 8–11 mm, Tipo 3 (moderado) 3–7 mm, Tipo 4 (completo) ≤3 mm. Otra fuente usa ≥20 mm como normal y 16–19 mm como leve (mismo documento). **Discutido:** el punto de corte de «normal» varía entre 16 y 20 mm según el sistema de clasificación citado.

### 1.4 Hidrostato muscular (volumen constante)
La lengua es un hidrostato muscular: no tiene soporte óseo interno, y su volumen total es aproximadamente constante durante la deformación (Kier & Smith, 1985, «Tongues, tentacles and trunks», *Zoological Journal of the Linnean Society*, https://onlinelibrary.wiley.com/doi/10.1111/j.1096-3642.1985.tb01178.x; recogido también en Smith & Kier, 1989 y en la revisión de biomecánica de la lengua de primates, PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC13045644/).

- **Principio clave (consenso):** como el volumen es constante, una disminución en una dimensión produce un aumento compensatorio en al menos otra. Al **alargarse** la lengua (protrusión), su sección transversal (grosor/anchura) debe **reducirse**; al **acortarse**, la sección debe **aumentar** (engrosarse).
- Elongación: contracción de músculos transversales, circulares o radiales que reducen la sección transversal.
- Acortamiento: contracción de músculos longitudinales.
- Aplanamiento (p. ej. hacia /θ/ interdental o /s/): contracción del transverso combinado con relajación vertical, redistribuyendo volumen hacia los bordes laterales, no hacia adelante como una lámina fina sin masa. **Esto es exactamente el error a corregir**: la punta en /θ/ no debe volverse fina y plana perdiendo volumen; debe ensancharse lateralmente y bajar de altura mientras conserva grosor real, porque el volumen no desaparece.

### 1.5 Músculos y su acción (consenso anatómico estándar, Gray's/Kenhub)

| Músculo | Tipo | Acción principal |
|---|---|---|
| Genihioglosso | Extrínseco | Protruye la lengua y deprime el dorso (empuja la masa hacia adelante y abajo) |
| Hiogloso | Extrínseco | Deprime y retrae la lengua (tira del dorso hacia abajo/atrás) |
| Estilogloso | Extrínseco | Retrae la lengua y eleva los bordes laterales/posteriores (forma canal) |
| Palatogloso | Extrínseco | Eleva la raíz de la lengua / deprime el velo (cierre orofaríngeo) |
| Longitudinal superior | Intrínseco | Acorta la lengua; curva la punta hacia arriba |
| Longitudinal inferior | Intrínseco | Acorta la lengua; curva la punta hacia abajo |
| Transverso | Intrínseco | Estrecha y alarga la lengua (angosta la sección, la empuja hacia adelante) |
| Vertical | Intrínseco | Aplana y ensancha la lengua |

(Kenhub, 2024, «Tongue: Anatomy, muscles, neurovasculature and histology», https://www.kenhub.com/en/library/anatomy/tongue). Esta tabla es anatomía de libro de texto, ampliamente consensuada; no varía por hablante.

### 1.6 Surco medio y sección transversal
El surco medio (median sulcus) es una depresión longitudinal en el dorso que refleja el septo lingual medio (tejido conectivo fibroso que separa las mitades derecha e izquierda). Consenso anatómico estándar; no se encontró una cifra en mm de su profundidad en fuentes accesibles. **Sin fuente fiable** para profundidad numérica del surco; modelarlo como una depresión sutil (regla práctica en §9) es razonable pero no está anclado en una medición publicada.

### 1.7 Rango de movimiento y forma dinámica (rtMRI/cine-MRI)
Los estudios de cine-MRI y MRI etiquetada (tagged MRI) de Stone y colaboradores muestran deformación tridimensional de la lengua durante el habla, incluyendo cambios de forma del ápice y la lámina durante distintos sonidos (Stone et al., trabajo recogido en «Analysis of 3-D Tongue Motion From Tagged and Cine Magnetic Resonance Images», *JSLHR*, 2016, https://pubs.asha.org/doi/10.1044/2016_JSLHR-S-14-0155; y «A Four-dimensional Motion Field Atlas of the Tongue from Tagged and Cine Magnetic Resonance Imaging», PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC5659618/). Estas fuentes confirman cualitativamente el comportamiento de hidrostato (compensación de volumen) pero no publican, en el resumen accesible, tablas de rango de movimiento del ápice en mm por fonema. **Discutido/variable:** el grado exacto de elevación/protrusión del ápice varía considerablemente entre hablantes y dialectos; no hay un único número consensuado por fonema.

---

## 2. Labios

### 2.1 Dimensiones (población adulta, varios estudios antropométricos)

| Medida | Valor típico | Rango / variación | Fuente |
|---|---|---|---|
| Altura vermellón superior | 5,6–9,1 mm según población | 5,60±1,60 mm (H) a 9,09 mm (mujeres asiáticas) | Indonesia: Enhancing Aesthetic Harmony, 2024, ScienceDirect, https://www.sciencedirect.com/science/article/pii/S2352587823001092 ; Asia: JCAD review, https://jcadonline.com/lip-preferences-asians-hispanics/ |
| Altura vermellón inferior | 9,8–11,8 mm | 6,59±1,39 mm (mujeres, Indonesia) a 11,83±2,45 mm (España) | Southern Spain study; Asian review (arriba) |
| Ratio altura superior:inferior | Caucásicas ~1:1,6; asiáticas ~1:1,08 | discutido — varía fuerte por etnia | Springer 2024, «The Concept of Ideal Lips of Caucasian Female», https://link.springer.com/article/10.1007/s00266-024-04299-1 ; JCAD (arriba) |
| Anchura boca (comisura a comisura) | 47–49 mm | 47,34±3,65 a 49,24±6,06 mm | Indonesia y España (arriba) |

**Consenso:** el labio inferior es más alto (más grueso en vermellón) que el superior en casi todas las poblaciones medidas; la proporción exacta es discutida/variable por etnia. La anchura de comisura a comisura ronda 47–50 mm en población adulta general (no hay cifra separada para EN/ES hablantes).

### 2.2 Bermellón: color y textura
El vermellón tiene una mucosa diferenciada de la piel circundante (mayor vascularización superficial, ausencia de folículos pilosos/glándulas sebáceas, epitelio más fino → color rojo/rosado y textura más lisa y brillante frente a la piel perioral, que tiene poros, vello fino y textura mate). Esto es anatomía de libro de texto estándar (emedicine, «Lips and Perioral Region Anatomy», https://emedicine.medscape.com/article/835209-overview); no se encontró una cifra numérica de reflectancia o rugosidad comparativa.

### 2.3 Orbicular de los labios y cierre bilabial
El orbicular de los labios es un músculo esfinteriano que rodea la boca; su contracción comprime y protruye los labios, produciendo el cierre bilabial (/p/, /b/, /m/) y el redondeo labial. Consenso anatómico estándar. No se encontró una cifra en mm de la fuerza de compresión o del desplazamiento del bermellón durante el cierre bilabial en las fuentes revisadas — **sin fuente fiable** para esa cifra específica.

### 2.4 Redondeo, protrusión y abertura
- La protrusión labial se mide típicamente como el desplazamiento de las comisuras en el plano sagital; el área labial (constricción entre labios) es una medida más fiable que la protrusión pura para el redondeo vocálico, especialmente en inglés (revisión ICPhS 2003, «Lip protrusion/rounding dissociation in French and English», https://www.internationalphoneticassociation.org/icphs-proceedings/ICPhS2003/papers/p15_1763.pdf).
- El vocal con mayor redondeo en la mayoría de dialectos de inglés es /u/ (Wikipedia/Roundedness, resumen de fuentes lingüísticas estándar, https://en.wikipedia.org/wiki/Roundedness).
- **Sin fuente fiable** para una cifra en mm de protrusión labial máxima en /u/ específicamente para inglés; los estudios citados dan medidas relativas (áreas, no mm absolutos) y advierten que la protrusión varía mucho entre hablantes («inconsistente… entre individuos»). Esto es un punto **discutido**: no fijar un valor único de protrusión en mm; usar un rango relativo (p. ej. "área de apertura labial se reduce a ~30–50 % del máximo en vocales no redondeadas" no está respaldado directamente; mejor usar solo la dirección del cambio, no una cifra).

---

## 3. Dientes y alvéolo

| Medida | Valor típico | Rango | Fuente |
|---|---|---|---|
| Overjet (solape horizontal) | 2–3 mm | 1,5–4 mm según fuente | Wikipedia/Overjet (resume literatura ortodóncica), https://en.wikipedia.org/wiki/Overjet ; ScienceDirect Topics, https://www.sciencedirect.com/topics/medicine-and-dentistry/overjet |
| Overbite (solape vertical) | 2–3 mm | ~20–30 % de la altura de la corona del incisivo inferior; otra fuente da 3–5 mm como «ideal» | mismas fuentes; PMC evaluación India, https://pmc.ncbi.nlm.nih.gov/articles/PMC8375840/ |
| Altura del paladar duro (bóveda) | 10,9–20 mm según método/población | 10,93±2,32 mm (India) a 20±2,2 mm (población general) | North Indian study, Azerbaijan Pharm J, https://www.azpharmjournal.com/en/2024-volume-23-issue-3/hard-palate-dimensions-in-north-indian-adult-skulls-a-morphometric-study/ ; estudio de 29 sujetos, referenciado en PMC9707855, https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9707855/ |
| Altura vault palatino, Patrón I / II (cefalometría) | 17,03±2,42 mm / 16,79±2,42 mm | — | PMC9707855 (arriba) |

**Discutido:** la altura del paladar varía mucho según el método de medición (radiográfico vs. escaneo de modelo dental vs. cráneo seco) y la población — el rango citado va de ~11 a ~20 mm según el estudio. Para modelar, usar un valor medio (~15 mm) es razonable pero no hay consenso cerrado.

**Overjet/overbite (consenso):** 2–3 mm es el valor típico citado más frecuentemente en fuentes ortodóncicas generales; es la cifra recomendada para una oclusión "normal" de referencia.

---

## 4. Velo (paladar blando) y úvula

| Medida | Valor típico | Fuente |
|---|---|---|
| Longitud total del velo | ~30 mm | Miller, «Anatomy of the Soft Palate and Its Role in Upper Airway Function», *Clinical Anatomy*, 2024/2025, Wiley, https://onlinelibrary.wiley.com/doi/full/10.1002/ca.70183 |
| Grosor del velo | ~5 mm de media (varía de un extremo a otro) | ídem |

**Función (consenso):** en los sonidos orales el velo se eleva y se retrae contra la pared faríngea posterior, cerrando la vía nasal (cierre velofaríngeo, tipo esfínter, con participación de las paredes faríngeas laterales); en los sonidos nasales el velo desciende, abriendo la vía nasal. Músculos implicados: elevador del velo del paladar (levator veli palatini, principal elevador), músculo de la úvula, constrictor superior de la faringe, palatofaríngeo, palatogloso, salpingofaríngeo (Miller 2024/2025, arriba; Cincinnati Children's, «Velopharyngeal Function and Disfunction», https://www.cincinnatichildrens.org/service/s/speech/specialty-clinics/vpi-clinic/velopharyngeal).

**Sin fuente fiable** para el grado de elevación del velo en mm o en grados durante /k/ vs. /m/, por ejemplo; los estudios revisados describen el mecanismo cualitativamente, no en cifras angulares utilizables directamente.

---

## 5. Mandíbula: apertura y movimiento

| Medida | Valor típico | Rango | Fuente |
|---|---|---|---|
| Apertura interincisal máxima (MIO) | — | 40–55 mm | Referencia clínica general (ClinicalTrials.gov NCT03875118, contexto de rango normal de apertura máxima), https://clinicaltrials.gov/study/NCT03875118 |
| Apertura mandibular en el habla (vocales/consonantes) | — | mucho menor que MIO; varía por vocal y consonante | Mooshammer, Hoole & Geumann, 2007, «Jaw and Order», https://doi.org/10.1177/00238309070500020101 ; voicescience.org, «Jaw (Mandible): Articulation, F1 Tuning, and Trade-offs», https://www.voicescience.org/lexicon/jaw/ |

**Consenso cualitativo:**
- La mandíbula funciona como "articulador silábico": se abre para vocales y se cierra para consonantes, en un ciclo abierto-cerrado por sílaba.
- La apertura mandibular es el principal factor que controla F1 (la vocal más abierta, como /ɑ/, tiene mayor apertura mandibular que una vocal cerrada como /i/ o /u/).
- El movimiento mandibular combina **rotación y traslación** simultáneamente durante los gestos de apertura y cierre en el habla (no es solo bisagra).

**Sin fuente fiable** para una tabla de apertura en mm específica por fonema del inglés (los papers citados dan patrones relativos y gráficos, no una tabla numérica reutilizable en el resumen accesible). Para el habla conversacional normal, la apertura interincisal es sustancialmente menor que los 40–55 mm de la apertura voluntaria máxima — es razonable modelar el rango de habla como una fracción pequeña de la MIO (sugerido: **discutido**, no hay cifra exacta consensuada).

---

## 6. Faringe, epiglotis y laringe (glotis)

| Medida | Valor típico | Rango | Fuente |
|---|---|---|---|
| Longitud vertical de la faringe | — | 12–14 cm (de la base del cráneo al esfínter esofágico superior) | StatPearls/Kenhub, recogido de «Pharynx (throat) anatomy», https://www.kenhub.com/en/library/anatomy/the-pharynx |
| Longitud/anchura de la laringe | ~4–5 cm | 4–5 cm; más pequeña en mujeres, más grande en adultos que en niños | StatPearls, «Anatomy, Head and Neck: Larynx», https://ncbi.nlm.nih.gov/books/NBK538202/ |
| Epiglotis, posición arqueada | 22±3 mm | — | ídem |
| Epiglotis, posición aplanada | 25±3 mm | — | ídem |
| Glotis | región entre el borde superior de las cuerdas vocales verdaderas y 1 cm por debajo | — | ídem |

**Consenso:** la laringe es más pequeña en mujeres que en hombres (diferencia sexual bien establecida, ligada al desarrollo puberal). La glotis se define anatómicamente como una franja de ~1 cm de alto centrada en las cuerdas vocales.

---

## 7. Proporciones relativas entre estructuras

A partir de las cifras anteriores, para un modelo proporcionado en unidades arbitrarias (tomando el paladar duro como referencia, longitud ≈ 40–45 mm desde el borde alveolar hasta el borde posterior, cifra típica de anatomía dental estándar aunque **sin una única fuente numérica citada aquí con ese valor exacto — tratar como orientativo**):

- **Lengua : paladar duro** — la lengua completa (~90 mm) es aproximadamente el doble de larga que el paladar duro; solo el tercio anterior de la lengua (ápice+lámina, ~30 mm) recorre la longitud del paladar duro durante los gestos coronales.
- **Velo : paladar duro** — el velo (~30 mm) es más corto que el paladar duro pero del mismo orden de magnitud; en el modelo, el velo no debería superar ~70-75 % de la longitud visible del paladar duro.
- **Anchura de labios : anchura de arco dental** — la anchura de comisura a comisura (~48 mm) es mayor que la anchura intercanina típica, por lo que en el recuadro frontal los labios deben sobresalir lateralmente respecto al arco dental visible al centrar el modelo.
- **Grosor de lengua (cuerpo, 17 mm) : altura de paladar (~15 mm de referencia media)** — son del mismo orden; el dorso lleno ocupa casi toda la altura de la bóveda palatina en reposo, lo que explica por qué el contacto dorso-velar en /k/ debe representarse como una superficie de contacto amplia y curva, no como un bloque anguloso.
- **Epiglotis (~22-25 mm) : laringe (~40-50 mm)** — la epiglotis mide aproximadamente la mitad de la longitud de la laringe.

Estas relaciones son deducciones aritméticas de las cifras tabuladas arriba, no mediciones directas conjuntas publicadas en una sola fuente; trátense como estimaciones razonadas, no como consenso cerrado.

---

## 8. Rasgos de realismo facial perioral

Fuentes: Medscape, «Lips and Perioral Region Anatomy» (https://emedicine.medscape.com/article/835209-overview); ScienceDirect Topics, «Philtrum» (https://www.sciencedirect.com/topics/medicine-and-dentistry/philtrum); PMFA Journal, «Lips and the perioral area» (https://www.thepmfajournal.com/features/features/post/lips-and-the-perioral-area-anatomical-considerations-for-safer-and-natural-results).

- **Filtrum:** depresión central entre dos columnas verticales (crestas filtrales) que van de la base de la columela nasal al arco de Cupido. Es lo que más "humaniza" la zona superior del labio: sin las dos crestas con su valle intermedio, el labio superior se lee como un tubo genérico.
- **Arco de Cupido:** dos elevaciones paramedianas en el borde cutáneo-mucoso del labio superior, en el punto donde terminan las crestas filtrales.
- **Surco nasolabial:** pliegue que va de la nariz a la comisura bucal; marca el límite lateral de la mejilla y ancla visualmente la boca a la cara.
- **Comisuras:** puntos de unión labial superior/inferior; su posición y sombra definen el ancho aparente de la boca y son clave para las poses de sonrisa/habla.
- **Subsurface scattering y sombreado:** el bermellón, al ser mucosa fina y muy vascularizada, se beneficia de subsurface scattering (dispersión subsuperficial) más marcado que la piel circundante para leer como tejido vivo y no plástico; la piel perioral necesita microrelieve (poros, vello fino) para no leerse como maniquí.

**Regla de diseño (no cuantitativa, pero consensuada cualitativamente):** una cara perioral realista necesita, como mínimo, (1) filtrum con dos crestas y un valle, (2) arco de Cupido definido, (3) surco nasolabial, y (4) diferencia de textura/color/reflectancia entre bermellón y piel. La ausencia de cualquiera de estos cuatro es lo que suele producir el efecto «muñeco» que Miguel describe.

---

## 9. Parámetros para el modelo 3D (reglas accionables para Blender)

Notación: todas las cifras son de partida (peso adulto medio, sin distinción de sexo salvo que se indique); usar como escala relativa dentro del rig, no como valores absolutos de producción salvo que el modelo esté a escala real.

1. **Grosor de la punta/lámina en reposo:** usar como base el grosor medido de la lámina, 11–14 mm (medial/lateral) — no adelgazar el ápice por debajo de ese rango en reposo; el shape key de /θ/ no debe reducir el grosor del ápice, solo aplanarlo *ensanchando* lateralmente (ver regla 3).
2. **Grosor del dorso/cuerpo:** 12–17 mm (lateral/medial); el dorso debe ser sensiblemente más grueso que la lámina (~1,2–1,5×), no un bloque uniforme — degradar el grosor gradualmente desde el dorso hacia los bordes laterales.
3. **Regla de hidrostato (volumen constante) para los shape keys:** cualquier shape key que alargue la lengua (protrusión, /θ/, /s/) debe llevar acoplado un adelgazamiento proporcional de la sección transversal en el punto de máxima extensión, y viceversa: cualquier shape key que acorte o retraiga la lengua (p. ej. hacia /k/, /g/) debe engrosar el dorso, no dejarlo como bloque rígido de volumen fijo. Nunca cambiar la longitud sin cambiar la sección; eso es lo que produce el efecto de "punta que se aplana sin masa" en /θ/ y el "bloque" en /k/.
4. **Surco medio:** modelar como una depresión longitudinal sutil y continua en el dorso (sin cifra de profundidad publicada — usar un valor pequeño relativo al grosor del dorso, p. ej. ≤10 % del grosor local, como estimación de diseño, no como cifra de fuente).
5. **Superficie de contacto dorso-velar en /k/:** el contacto debe representarse como una zona ancha y curva (siguiendo el contorno cóncavo del velo, longitud del velo ≈30 mm), no como una arista o bloque anguloso — el dorso tiene grosor (12–17 mm) suficiente para "envolver" el contacto, no chocar en un punto.
6. **Labios — altura de vermellón:** labio inferior más alto que el superior; usar una proporción aproximada 1:1,3–1,6 (superior:inferior) como punto de partida, marcando que la proporción exacta es discutida entre poblaciones — no tratarla como fija.
7. **Anchura de comisura a comisura:** ~47–50 mm en reposo (referencia adulto genérico); el redondeo (/u/, /oʊ/) debe *reducir* visualmente esta anchura y proyectar el bermellón hacia adelante, pero no fijar una cifra de protrusión en mm (sin fuente fiable) — modelar el cambio de forma vía reducción de área de apertura, no vía una distancia de protrusión inventada.
8. **Cierre bilabial (/p,b,m/):** el orbicular de los labios comprime y protruye ligeramente el bermellón; el shape key de cierre debe mostrar compresión visible del bermellón (aplanamiento con ligero abultamiento lateral), reflejando el comportamiento de un esfínter muscular, no un simple "cierre de compuerta" rígido.
9. **Textura y sombreado del bermellón vs. piel:** dar al material del bermellón mayor subsurface scattering, mayor saturación de rojo y superficie más lisa/brillante que la piel perioral circundante; dar a la piel perioral micro-relieve (poros, vello) para evitar el look de maniquí.
10. **Filtrum y arco de Cupido:** modelar las dos crestas filtrales con un valle intermedio entre la base nasal y el arco de Cupido; sin esto, el labio superior se leerá genérico. Añadir el surco nasolabial como pliegue suave que ancla la boca a la mejilla en el recuadro frontal.
11. **Dientes/oclusión de referencia:** overjet 2–3 mm, overbite 2–3 mm como oclusión "normal" por defecto del rig.
12. **Altura de la bóveda palatina:** usar ~15 mm como valor de referencia medio (el rango publicado es amplio, 11–20 mm, según método) — suficiente para que el dorso lingual en reposo casi la toque, coherente con la regla 5.
13. **Velo:** longitud ~30 mm, grosor ~5 mm; el shape key oral debe elevar y retraer el velo contra la pared faríngea posterior (cierre tipo esfínter, incluyendo aproximación de las paredes laterales, no solo el velo); el shape key nasal debe descender el velo dejando un canal visible hacia la nasofaringe.
14. **Mandíbula:** modelar el movimiento como combinación de rotación (bisagra) + traslación (deslizamiento anterior), no solo bisagra pura; la apertura de habla debe ser una fracción claramente menor que la apertura voluntaria máxima (40–55 mm) — sin cifra exacta por fonema, usar los gestos relativos (vocales abiertas > vocales cerradas > consonantes) como guía cualitativa.
15. **Proporciones generales del rig:** lengua completa ≈2× la longitud del paladar duro; velo ≈0,7× la longitud del paladar duro; epiglotis ≈0,5× la longitud de la laringe. Usar estas razones para escalar mallas entre sí de forma coherente aunque el modelo no esté a escala real en mm.
16. **Frenillo:** longitud visible libre de la lengua respecto al suelo de la boca ≥16 mm en la posición de reposo/protrusión moderada, para evitar una apariencia de "lengua atada" salvo que se quiera representar explícitamente anquiloglosia.

---

## Resumen de vacíos («sin fuente fiable»)

- Grosor exacto solo del ápice (aislado de la lámina).
- Profundidad en mm del surco medio lingual.
- Fuerza/desplazamiento de compresión del orbicular en el cierre bilabial, en mm o N.
- Protrusión labial en mm específica para /u/ en inglés (solo hay medidas de área relativa).
- Grado de elevación del velo en mm o grados por fonema.
- Apertura mandibular en mm por fonema específico del inglés.
- Longitud del paladar duro en mm de un único estudio consolidado (se usó una estimación orientativa a partir de proporciones).

Donde el texto dice "estimación de diseño" o "orientativo", es una inferencia razonada para modelado, no una cifra publicada — señalado así explícitamente para que quien modele sepa qué tiene respaldo directo y qué es extrapolación.
