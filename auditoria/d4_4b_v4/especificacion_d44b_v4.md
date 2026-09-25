# D4.4b v4 — Especificación (anatomía + fonética GA/RP)

Fuentes: `investigacion_anatomia.md` (21 URL, 16 reglas de modelado) e `investigacion_fonetica.md`
(8 tablas por familia; citas por autor y año, sin URL). Base de partida: `dev/articulacion-v2` @ `9544250` (v3).

## 1. Principios (se aplican a todo)

1. **Hidrostato muscular: la lengua conserva el volumen.** Si una shape key alarga la lengua, la sección
   adelgaza un poco y se ensancha; si la acorta o la retrae, el dorso engrosa. Nunca se pierde masa ni se
   deja un bloque rígido. (Kier y Smith 1985.) Esto explica tanto el aplanamiento de `/θ/` como el bloque de `/k/`.
2. **Grosores de referencia:** lámina y punta 11–14 mm; dorso 12–17 mm (≈1,2–1,5× la lámina, con transición
   gradual). La punta **nunca** baja del grosor de la lámina: se adelgaza ensanchándose, no aplastándose.
   Surco medio sutil (≤10 % del grosor local; estimación de diseño).
3. **Proporciones:** lengua ≈2× el paladar duro; velo ≈30 mm y ≈0,7× el paladar duro; bóveda ≈15 mm;
   overjet y overbite de 2–3 mm.
4. **Labios:** el inferior es más alto que el superior (≈1:1,3–1,6). Anchura en reposo de 47–50 mm. El bermellón
   lleva otro material: más rojo, más liso y con más subsurface que la piel. En el cierre bilabial, el orbicular
   **comprime y abomba ligeramente** los labios; no es una compuerta.
5. **Realismo perioral:** crestas del filtrum, arco de Cupido y surco nasolabial suave; piel mate con microrrelieve.
6. **Mandíbula:** rotación + traslación. La apertura del habla es una fracción de la máxima: vocales abiertas >
   vocales cerradas > consonantes. En reposo, los labios casi juntos, **no** abiertos.
7. **Velo:** en los orales, alto y cerrando contra la pared faríngea; en las nasales, bajo, con el canal visible.

## 2. Cambios de v4 (orden de trabajo)

**A. `/θ ð/` — lo que rechazó Miguel («la lengua se aplana»).**
- Postura pedagógica: la punta asoma **ligeramente** entre los incisivos, o toca su borde, **gruesa y redondeada**,
  con la lámina ancha. La lengua es un volumen, no una hoja.
- Mandíbula semiabierta, algo más que en `/f v/`. Labios neutros. Velo alto. El aire pasa por encima de la lámina.
- Nota honesta (Dart 1991): muchos nativos son dentales o laminales, no interdentales puros. En el texto de
  la ficha puede decirse «variante interdental, la más clara para aprender».
- Criterio: la punta, vista a 390 px, se lee como un extremo redondeado con grosor ≥ el de la lámina; sin arrugas
  ni pliegues. Distinta de `/s/` (punta detrás de la cresta, sin asomar) y de `/t/` (oclusión en la cresta).

**B. Rendimiento de `/p b m/` (bloqueante de fusión: −26 %).**
- El recuadro frontal no puede costar un cuarto de los fps. Opciones: renderizar el recuadro a menor
  resolución o cada 2 fotogramas, reducir sus mallas y sombras, o compartir más estado del render.
- Criterio: dentro de ±15 % de la línea base `8bd4a66`, con la misma herramienta y rondas alternas.

**C. Labios.**
- En el corte sagital: dos labios con volumen y bordes limpios (hoy son láminas dentadas).
- En el recuadro: el reposo y el final con los labios **casi juntos** (hoy salen muy abiertos).
- En el cierre `/p b m/`: compresión visible, sin franja oscura.
- `/p/` frente a `/b/`: hoy solo los distingue la etiqueta. Hay que mostrar la **aspiración** de `/p/`: VOT de
  labial ≈25 ms en posición inicial tónica (Lisker y Abramson 1964), con un soplo visible tras la liberación,
  frente a `/b/` con vibración desde la liberación (VOT ≈0).

**D. `/k ɡ ŋ/`.**
- El dorso forma un contacto **ancho y curvo** que sigue la concavidad del velo, no un bloque alto. Aplica el
  hidrostato: al subir el dorso, la lámina anterior baja y adelgaza, sin añadir volumen (hoy hay +79 %).
- `/ŋ/`: cierre velar sin liberación oclusiva añadida (error típico de hispanohablantes).

## 3. Después de aprobar v4: lote por prioridad pedagógica (investigación de fonética, §9)

1. `/θ ð/` frente a `/s t d f/`.
2. `/ɹ/` de GA: lengua **abombada**, la más frecuente, con constricción faríngea y **raíz retraída**. La retrofleja
   es una alternativa válida (Delattre y Freeman 1968; Zhou et al. 2008). `/r/` de RP: postalveolar, sin
   rótica en coda.
3. El contraste rótico GA `/ɝ ɚ/` frente a RP `/ɜː ə/`: activar o desactivar la constricción.
4. `/v/` frente a `/b/`: contacto labiodental con fricción continua, frente a cierre y liberación.
5. Vocales `/i ɪ/`, `/æ ɛ ʌ/`: altura y anterioridad relativas y apertura de la mandíbula.
6. `/ʃ ʒ tʃ dʒ/` con **protrusión labial**.
7. `/l/` clara y oscura: retracción y descenso del dorso en la coda.
8. `/ɒ/` en RP (redondeada) frente a `/ɑ/` en GA (sin redondeo).
9. VOT de `/p t k/`: labial < alveolar < velar (≈25 / 35 / 42 ms).

## 4. Restricciones (se mantienen)

- El 2D está congelado; no se tocan `app/animacion_articulatoria.py`, los timings, el ciclo de 2,0 s ni las rutas
  de aire.
- Tampoco el audio, master ni el despliegue.
- Blender 2.93 (`tools/boca3d_blender/`).
- Comprobaciones: techo de `lengua.py` 53/53 con exceso 0, guard 534 preexistente, pruebas focalizadas + front + tsc + build.
- Evidencia en la **vista del alumno** a 390 px, con comparativa v3|v4 legible.
