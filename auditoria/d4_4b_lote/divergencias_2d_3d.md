# Divergencias entre el 3D y el 2D congelado

Las poses del 3D salen de `app/animacion_articulatoria.PARAMETROS` (2D congelado) por
`tools/exportar_poses_boca3d.py` → `front/src/app/compartido/boca3d/poses.ejemplo.json`. El 2D no se toca y,
desde el lote fase 1, **ese JSON tampoco se edita a mano**: lo que el 3D cambia vive en
`front/src/app/compartido/boca3d/poses.ajustes3d.json` (campos sueltos por símbolo) y se mezcla encima al
cargar (`conAjustes3d` en `poses.ts`, y la misma regla en `tools/boca3d_blender/lengua.py` y
`tools/boca3d_demo/medir_lengua.mjs`). Regenerar el JSON con el exportador no pierde nada del 3D.

Aviso previo (medido el 22 sep): el exportador da hoy `factor_lento` 1,143 y el JSON commiteado lleva 1,6
(es el que usa el front); todo lo demás coincide. El factor de «Despacio» es un timing del ciclo (congelado):
**no regenerar el JSON sin resolver antes esa diferencia**.

## Poses (por símbolo)

| Fecha | Fonema | Parámetro | Valor 2D | Valor 3D | Motivo | Dónde |
|---|---|---|---|---|---|---|
| 22 sep (cierre de cara) | /θ/, /ð/ | `mandibula` | 0,36 | 0,6 | Con `MAND_MAX` 0,21 rad el hueco entre bordes incisales a 0,36 es 0,54 u (12 mm) y la punta interdental aprobada (roma, v4) mide 0,64 u: no cabe. Decisión de e6/Miguel (dato, no excepción). | `poses.ajustes3d.json` `sonidos.θ/ð`; `auditoria/d4_4b_cierre_cara_2026-09-22.md` §3 |
| 22 sep (lote fase 1) | /ɹ/ GA | `punta` | `retrofleja` | `reposo` | Variante **abombada** (bunched), la más frecuente en GA (Delattre & Freeman 1968; Zhou et al. 2008, RM): el dorso se abomba hacia el paladar medio y la punta queda recogida y baja, no curvada. La retrofleja sigue siendo una realización válida (mismas fuentes) y se conserva como alternativa: basta quitar esta fila. | `sonidos.ɹ` |
| 22–23 sep (fases 1 y 2) | /ɹ/ GA | `cuerpo` · `dorso_alto` · `raiz` | [0,55; 0,35] · 0 · 0,8 | [0,82; 0,35] · 0,3 · **0,6** | La joroba (cúspide y 0,99 en x 0,50, medido) y la constricción faríngea (hueco raíz-pared 0,10–0,19 u, frente a 0,29–0,38 en RP /ɜː ə/). Fase 1 puso raíz 0,9 y cuerpo 0,85; la fase 2 los baja porque inflaban la lengua +43 % (hidrostato ±10 %, que ahora se exige en todas las poses): queda en +9,8 %. | `sonidos.ɹ` |
| 22–23 sep (fases 1 y 2) | /ɝ/ GA | `punta` · `cuerpo` · `dorso_alto` · `raiz` | `retrofleja` · [0,58; 0,35] · 0,2 · 0,8 | `reposo` · [0,78; 0,38] · 0,3 · **0,65** | Vocal rótica abombada, mismo criterio que /ɹ/ (§9.2: la constricción se sostiene en /ɝ ɚ/). Fase 2: volumen de +40 % a +9,7 %. | `sonidos.ɝ` |
| 22 sep (lote fase 1) | /ɚ/ GA | `punta` · `cuerpo` · `dorso_alto` · `raiz` | `retrofleja` · [0,52; 0,40] · 0,1 · 0,6 | `reposo` · [0,7; 0,42] · 0,2 · 0,65 | Ídem, átona: menos joroba y menos raíz. | `sonidos.ɚ` |
| 22 sep (lote fase 1) | /r/ RP (`rp.ɹ`) | pose entera | (no existe en `PARAMETROS_RP`: RP usaba la pose GA de /ɹ/) | `punta` `postalveolar` sin toque, `cuerpo` [0,55; 0,45], `dorso_alto` 0, `raiz` 0 | /r/ de RP es postalveolar y **sin** constricción faríngea ni joroba (§9.3). La no-roticidad en coda no es de la pose: viene de las transcripciones RP del catálogo (sin /r/ en coda), que el visor recibe ya hechas. | `rp.ɹ` |
| 22 sep (lote fase 1) | /ɑ/ GA | `raiz` · `cuerpo` | 0,8 · [0,05; 0,05] | 0 · [0,05; 0,4] | Con la pared faríngea modelada (cara.glb, x 2,84–3,0) la raíz entraba 0,57 u (13 mm) en ella: el giro de la mandíbula (0,21 rad sobre el pivote 2,6; 0,9) ya lleva la raíz 0,44 u hacia atrás con la boca abierta, y `cuerpo_atras` + `raiz` la empujaban más. El 2D no tenía pared. Queda «baja y atrás» por la mandíbula; holgura −0,05. | `sonidos.ɑ` |
| 22 sep (lote fase 1) | /ɒ/ RP | `raiz` · `cuerpo` | 0,8 · [0,02; 0,02] | 0 · [0,02; 0,42] | Ídem /ɑ/ (entraba 0,62 u). Holgura −0,02. | `sonidos.ɒ` |
| 22 sep (lote fase 1) | /ɔ/ GA | `raiz` · `cuerpo` | 0,6 · [0,3; 0,05] | 0,15 · [0,3; 0,35] | Ídem (entraba 0,35 u). Holgura −0,07. | `sonidos.ɔ` |
| 22 sep (lote fase 1) | /ɔː/ RP (`rp.ɔː`) | `raiz` · `cuerpo` | 0,4 · [0,55; 0,05] | 0,15 · [0,55; 0,25] | Ídem (entraba 0,14 u); y RP no enciende la constricción faríngea. | `rp.ɔː` |

| 23 sep (lote fase 2) | /ɪ/ GA | `mandibula` | 0,26 | 0,36 | Con 0,26 la abertura entre labios era 1,4 mm y se leía como boca cerrada (el cierre labial de las vocales neutras se apaga con la mandíbula). A 0,36: 5,2 mm, entre el reposo y /ɛ/ (8,1 mm). Medido también 0,30 → 2,6 y 0,33 → 3,8. | `sonidos.ɪ` |
| 23 sep (lote fase 2) | /l/ GA | `leyenda` | «punta en el alvéolo, aire por los lados; dorso alzado atrás (l oscura)» | «l oscura, la de final de sílaba (feel, ball): …» | La pose sigue siendo la del 2D (OSCURA). Decisión de e6: el error del hispanohablante es usar la /l/ clara en todas partes, así que la ficha enseña por defecto la oscura (el gesto que le falta) y, con un chip, la clara (misma pose sin dorso alzado ni raíz atrás; `boca3d.ts`). Ni el 2D ni el 3D saben la posición en la sílaba: el diccionario escribe casi siempre «l» (feel, milk, ball) y solo a veces «ɫ» (light US [ɫɐɪt], table UK [ˈt(ʰ)eɪbɫ̩]), que `app/fonemas.py` y `PARECIDOS` colapsan a «l». Si algún día el 3D conoce la posición en la sílaba, se puede afinar (clara en ataque, oscura en coda). | `sonidos.l`; `boca3d.ts` (`elegirVarianteL`) |
| 22 sep (lote fase 3) | /ɒ/ RP | `mandibula` | 1,0 | 0,8 | Con 1,0 /ɒ/ abría **más** que /ɑ/ de GA (24,2 mm frente a 20,8, medido en la demo): al revés de lo descrito. /ɒ/ es baja, posterior, redondeada y breve, y en el SSB moderno está algo **elevada** respecto a la RP clásica (Wells 1982; Lindsey 2019, cap. 6; investigación §7 y §9.9). A 0,8: 19,9 mm, entre /ɑ/ (20,8) y /ɔ/ (17,3); redondeo sin cambio (anchura 34,3 mm frente a 43,2 de /ɑ/, labios 6 mm más adelante) y breve (`larga` false, la del 2D). Medido también 0,9 → 22,1 y 0,72 → 18,1. Faringe: holgura −0,12 (antes −0,02). | `sonidos.ɒ`; `auditoria/d4_4b_lote/fase3_2026-09-22.md` §2 |

## Campos que solo existen en el 3D

| Fecha | Campo | Dónde se pone | Para qué |
|---|---|---|---|
| 22 sep (lote fase 1) | `rotica: true` | `sonidos.ɹ/ɝ/ɚ`, `rp.ɹ` | `familiaDe` manda la pose a la familia `rotico` (antes el criterio era «punta retrofleja», que la /ɹ/ abombada ya no cumple; `raiz ≥ 0,5` no vale porque /ɑ ɒ ɔ/ la llevaban). La familia `rotico` encuadra desde el lote la joroba, la punta y la pared faríngea (target [−0,3; 0,4], zoom 1). Ningún otro fonema cambia de familia (comprobado sobre todo el catálogo). |

## Mapeos pose → morfos que se apartan del 1:1 (no son poses, pero conviene verlos aquí)

| Fecha | Mapeo | Antes | Ahora | Motivo | Dónde |
|---|---|---|---|---|---|
| 22 sep (cierre) | `punta_arriba` con toque en postalveolar (/tʃ dʒ/) | 1,0 | 0,85 | Con la mandíbula de 0,21 rad la suma punta_arriba + cuerpo_alto entraba 0,155 en el paladar (toque permitido 0,08). | `lengua.py` `morfos_de`, `escena.ts` `morfosDe`, `medir_lengua.mjs` |
| 22 sep (cierre) | `dorso_velo` sin toque (`dorso_alto` de /w l ɝ ɚ/) | 1,0 × dorso_alto | 0,9 × dorso_alto | /w/ entraba 0,013 en el velo. /ɝ ɚ/ ya revisadas en el lote fase 1 (abombadas); /l/ y /w/ pendientes de su fase. | mismos tres archivos |
| 22 sep (lote fase 1) | comprobación nueva: raíz contra la pared faríngea | — | perfil medido de la pared (`PARED_FARINGE`), tolerancia 0,08 si `rotica` (roce a propósito) y 0,06 (grosor de la banda) para el resto | Entra en las comprobaciones de siempre de `lengua.py` (COLISION si falla). | `lengua.py` |
| 22 sep (lote fase 3) | soplo de /p t k/ (encima del ciclo, sin tocar sus claves) | 0,55 s para las tres (`SOPLO_S`, v4) | `SOPLO_S` × VOT / 35 ms: /p/ 0,39 · /t/ 0,55 · /k/ 0,66 s a velocidad 1 (en palabras, × `lento`; con `aVelocidad`, escalado). Mientras sopla, la marca de vibración de la vocal siguiente espera (`vozRetenida`) | El VOT de las sordas aspiradas crece hacia atrás: labial < alveolar < velar, ≈25 / 35 / 42 ms (Lisker & Abramson 1964; resumen en PMC5665574, «VOT at 50», 2017; investigación §1 y §9.10). /t/ conserva el soplo aprobado en v4; el tiempo real (decenas de ms) está ampliado como todo el ciclo, se mantiene la proporción. /b d ɡ/ siguen sin soplo. | `animacion.ts` (`VOT_MS`, `soploDe`), `escena.ts` (`soplar`, `vozRetenida`) |

## Claves de los modelos (geometría del 3D; no son poses, pero cambian cómo se ven)

| Fecha | Clave | Antes | Ahora | Motivo | Dónde |
|---|---|---|---|---|---|
| 23 sep (lote fase 2) | lengua `cuerpo_alto` | cara de arriba +1,35, de abajo +0,81, sin estrechar | abajo +1,08 y estrecha a lo ancho −0,20·y | Engordaba la lengua en vez de subirla: 17 de 47 poses fuera de ±10 % (/u/ +49 %, /i j/ +46 %). | `lengua.py` |
| 23 sep (lote fase 2) | lengua `punta_arriba` | estrechaba todo el cuerpo −0,16·y | −0,04·y | Era la compensación del engorde de `cuerpo_alto`; sin ese engorde /t d n/ quedaban en −12 % (en la lengua de la fase 1, /t/ sin `cuerpo_alto` ya daba −13,5 %: su −2,9 % escondía el déficit). | `lengua.py` |
| 23 sep (lote fase 2) | lengua `raiz_atras` | estrecha −0,06·y | −0,16·y | Alargaba la lengua 0,5 u sin adelgazarla (/ɹ/: +10,5 puntos de volumen solo por la raíz). | `lengua.py` |
| 23 sep (lote fase 2) | cara `labio_atras` (/f v/) | movía el cuerpo del labio de abajo con una rampa que valía 0,1 en su borde | el borde del labio de abajo sube 0,24 y retrocede 0,08, arqueado al centro; el de arriba se levanta 0,14 | El borde se quedaba a 7,3 mm del filo incisal; ahora a 2,9 mm. Límite: el filo de los incisivos no asoma (el labio superior de este escaneo tapa 6,7 mm de diente; levantarlo ≥ 7 mm sería una mueca, descartado por e6). | `cara.py`; banda labios-dientes con 8 comprobaciones nuevas de /f v/ |
| 23 sep (lote fase 2) | recuadro frontal | familias bilabial y nasal-bilabial | + labiodental | Comparar /f v/ con /p b/ en el mismo sitio. | `escena.ts` `dibujar` |

## Opciones descartadas (con sus cifras)

| Fecha | Opción | Por qué no |
|---|---|---|
| 23 sep (lote fase 2) | Recuadro de labios en /s ʃ tʃ/ (familias alveolar y postalveolar) | El corte ya enseña el contraste: la boca de /ʃ tʃ/ mide 34,3 mm frente a 57,4 de /s/ (23 mm menos) y los labios van 11 mm más adelante; un recuadro más cuesta fluidez en esas vistas. Decisión de e6. |
| 23 sep (lote fase 2) | Forzar el redondeo de /ʃ ʒ tʃ dʒ/ a −30..−45 % | Esas cifras del vídeo de Miguel son de /kw u w/, no de /ʃ/. /ʃ/ queda en −20,6 % con 6,5 mm de avance (protrusión moderada de postalveolar); para −30 % habría que dejarla casi igual que /u/ (−32 %). |
| 23 sep (lote fase 2) | Levantar el labio superior ≥ 7 mm en /f v/ para que asome el filo incisal | Sería una mueca; el contacto labiodental ya se lee con el labio de abajo a 2,9 mm de los incisivos. |

## Cierre del D4.4b (22 sep, lote fase 3): motivo y fuente de cada fila

Repaso fila por fila. «Medición» quiere decir que la cifra se midió en el modelo en esta rama (informe citado);
«decisión» es de e6/Miguel y está escrita en su informe. Donde la fila de arriba no citaba la fuente fonética,
la pongo aquí; ninguna fila queda sin motivo.

| Fila | Motivo | Fuente |
|---|---|---|
| /θ ð/ mandíbula 0,6 | la punta interdental no cabía con `MAND_MAX` 0,21 | medición (cierre de cara §3) + decisión e6/Miguel; el gesto: investigación §2 (Dart) |
| /ɹ/ GA punta en reposo | variante abombada | Delattre & Freeman 1968; Zhou et al. 2008 (investigación §5, §9.2, §10) |
| /ɹ/ GA cuerpo, dorso, raíz | joroba y constricción faríngea; volumen | **añadida aquí**: investigación §5 y §9.2 (mismas fuentes); cifras: medición (fases 1 y 2) |
| /ɝ/ GA | ídem, sostenida en la vocal | investigación §9.2 |
| /ɚ/ GA | ídem, átona | **añadida aquí**: investigación §6 (/ɚ/, Delattre & Freeman 1968) y §9.2 |
| /r/ RP | postalveolar, sin joroba ni raíz | investigación §5 (r RP: Wells 1982; Cruttenden 2014) y §9.3 |
| /ɑ ɒ ɔ/ GA/RP, /ɔː/ RP raíz | la raíz entraba en la pared faríngea | medición (fase 1 §1); «baja y atrás» se conserva: investigación §6–7 |
| /ɒ/ RP mandíbula 0,8 | abría más que /ɑ/ | Wells 1982 (§7: /ɒ/ «abierta», /ɑː/ «muy abierta»); Lindsey 2019 cap. 6 (elevación de LOT; la investigación solo pudo leer reseñas e índice, §10) |
| /ɪ/ mandíbula 0,36 | a 0,26 la boca parecía cerrada | investigación §6 («algo más abierta que /i/», Ladefoged & Johnson 2011) + medición (fase 2) |
| /l/ leyenda y chip | enseñar la oscura por defecto | investigación §5 y §9.7 + decisión e6 (fase 2) |
| campo `rotica` | la familia ya no puede decidirse por la punta | mecanismo del visor (sin afirmación fonética) |
| `punta_arriba` 0,85 en /tʃ dʒ/ | entraba en el paladar | medición (cierre §3) |
| `dorso_velo` ×0,9 | /w/ entraba en el velo | medición (cierre §3) |
| comprobación de la pared faríngea | la raíz no debe atravesarla | medición del perfil de `cara.glb` (fase 1) |
| soplo por lugar (VOT) | labial < alveolar < velar | Lisker & Abramson 1964; PMC5665574 (investigación §1, §9.10, §10) |
| claves `cuerpo_alto`, `punta_arriba`, `raiz_atras` | la lengua cambiaba de volumen | medición (fase 2 §1); el criterio ±10 % es el del encargo de e6 (la lengua es un hidrostato muscular: cambia de forma, no de volumen). **Sin fuente bibliográfica citada en la investigación**; queda como criterio de modelado |
| clave `labio_atras` | el labio de abajo no llegaba a los incisivos en /f v/ | investigación §2 (/f v/ labiodental) + medición (fase 2) |
| recuadro en labiodental | comparar /f v/ con /p b/ | decisión e6 (fase 2) |
| tres opciones descartadas | — | cada una con sus cifras en su fila |
