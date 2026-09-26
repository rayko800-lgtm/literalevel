# Inventario de entregables: lo que ya no es cierto (26 sep 2026)

Rama `dev/entregables` (worktree `.claude/worktrees/entregables`, desde `245d5e6`).
Encargo: `docs/ai/encargo_entregables.md`. Todavía no se ha cambiado nada.

Las fuentes del estado actual son el código de `front/` y `app/`, `docs/ai/HANDOFF.md`,
`DESPLIEGUE.md` y `git log` desde el 16 sep (202 commits). Las líneas citadas son del
worktree.

## Lo que cambió desde el 16 sep y ningún entregable cuenta

| Tema | Estado real | Fuente |
|---|---|---|
| Nombre | **Pléyade** en el front (títulos, logo, icono, «Sobre Pléyade» al pulsar el logo). Repos, Spaces, paquete y modelo siguen como `literalevel` | `cc1445e`, `front/src/app/app.routes.ts`, `compartido/sobre-pleyade.ts` |
| Enlace principal | <https://pleyade-app.vercel.app> (Vercel Hobby, se publica con cada push a `master`). El Space estático queda de respaldo | `a25247c`, `README.md:9-10` |
| Cuentas | Desde el 26 sep, con usuario y contraseña los datos (libros, palabras, nivel) son **de la cuenta** en cualquier aparato (`cuentas/<nombre>` en el bucket `MikeMaki1763/literalevel-datos`). Sin cuenta, por navegador. Contraseñas rotadas y cuentas en cero | `5cea8b0`, HANDOFF §7 |
| Navegación | Cinco pestañas: **Mi espacio** · Leer · Encontrar · Pronunciar · Tu nivel (antes eran cuatro). Además, Mis palabras, **Repasar** y **Mi progreso** | `front/src/app/app.ts:33-37`, `2197bb6`, D1–D3 |
| Diseño | Tema de la marca con fondo de galaxia y una lámina translúcida en todas las pantallas; los temas son Automático, Claro, Noche y Papel. Las **cinco paletas** (*hielo*, *amanecer*…) eran de **Gradio** | `df7b6ad`, `nucleo/preferencias.ts:3` |
| Boca 3D | La boca 3D didáctica de Blender (D4) sustituye a la de MakeHuman/72 mallas: aire en 2D y 3D, lectura de frases al compás del audio, ojos, texturas WebP (3,5 → 1,4 MB), zoom + y −, «Despacio» y «Explorar» | `4d41512`, `1f5f2c9`, `8b83454`, DESPLIEGUE §«La boca 3D didáctica» |
| Modelo articulatorio | **Modelo nuevo y medido**: TCN y dominancia entrenadas con GRID, Lombard GRID y USC-TIMIT (CC BY). Pearson 0,57 frente a 0,44 de las reglas; publicado en la boca 3D | `investigacion/modelo_articulatorio/resultados.md` |
| Lectura en vivo (D5) | Lectura en voz alta en el lector con transcripción en tiempo real | `dd0b3e5` |
| Eos | Cara MetaHuman **en desarrollo** en otra sesión; no se presenta como terminada | HANDOFF §4 |
| Fecha | Entrega el **3 oct 2026** | encargo |

## Por archivo

### `mensaje_profesor.md` (81 líneas): hay que rehacerlo
- l. 1, 16: «LiteraLevel» → Pléyade.
- l. 20: enlace del Space estático → Vercel.
- l. 3: «revisada el 16 sep, borrador no enviado»: ¿se llegó a enviar? **Pregunta para Miguel.**
- l. 32-38: «Sin entrar con una cuenta…» y el acceso de invitado: hay que añadir que con cuenta los datos se ven en cualquier aparato. Queda «su usuario y contraseña se los mando aparte». Las contraseñas no están en el archivo (bien).
- l. 38-43: los topes por hora (10/30/6/20/40/6): comprobar que siguen iguales en `app/api.py`.
- l. 60-70 (notas): «no presentar la demo local de Blender como publicada» ya no aplica, porque la boca 3D didáctica está publicada. En cambio, Eos no se presenta.
- No dice nada de Mi espacio, Repasar, Mi progreso, lectura en vivo ni del nuevo diseño.

### `guion_video.md` / `.tex` / `.pdf` (405 / 608 líneas)
- l. 1, 118, 129, 303, 367: nombre.
- l. 47, 301, 364: enlace `…static.hf.space` → Vercel (en pantalla y dicho).
- l. 86-93: la boca 3D «de MakeHuman», la revisión `ec68419` y «3–4 s la primera vez» ya no valen. Hay que volver a medir la carga en Vercel; el HANDOFF da unos 2,3 s, pero hay que medirlo.
- l. 73-82: la suspensión del Space a las 48 h y `/api/salud` siguen valiendo para la API. El front de Vercel no se duerme.
- l. 103-110: la bienvenida y las ayudas de la primera vez. Hay que comprobar que siguen iguales tras el tutorial v2 y Mi espacio.
- l. 175: «Ajustes → Tu perfil» sigue igual (`ajustes.ts:85`).
- l. 181-192: las latencias del 16 sep son de otra revisión. Se dicen «al instante»; hay que volver a medir o decir la fecha.
- l. 272-301: las 13 capturas de referencia son del diseño viejo (ver Capturas).
- Guion hablado: no enseña nada nuevo (Mi espacio, 3D nuevo, lectura en vivo, cuentas multiaparato). Añadir algo **cuesta segundos**: hay que recontarlo con `tools/contar_guion.py` (hoy son 496 palabras).

### `guion_demo_en_vivo.md` (371 líneas)
- l. 1, 186: nombre. l. 25: enlace → Vercel.
- l. 53-55, 308: la boca 3D (tiempos y «Recargar y reintentar»): comprobar en la versión actual.
- l. 331-334: «¿Por qué Angular?»: añadir Vercel («lo pidió el profesor», HANDOFF §6).
- l. 341-345: «el servidor del motor cuesta 7 dólares al mes»: sigue siendo la cuenta Pro de HF. **Pregunta para Miguel:** ¿la suscripción sigue activa después de septiembre?
- l. 283: «Todo lo que consulto… se queda aquí»: añadir que con cuenta se ve igual en el móvil y en el equipo, que es una demostración vistosa.
- Falta un paso con lo nuevo (Mi espacio/Mi progreso o la boca 3D nueva), si Miguel lo quiere dentro de los 4:00.

### `presentacion.tex` / `.pdf` (491 líneas)
- l. 2, 57, 68, 95: nombre. l. 479: enlace → Vercel.
- l. 285-290: el diagrama dice «Front · Angular 22, Space estático» → Vercel (y el Space como respaldo).
- l. 286: «Leer · Encontrar · Pronunciar · Tu nivel» → añadir Mi espacio.
- l. 310-311: «Boca 3D: 72 mallas, piel de MakeHuman (CC0)» → la boca didáctica actual. **Hueco:** contar sus mallas en el `.glb` publicado antes de dar una cifra.
- l. 316-317: portadas FLUX pendientes (sigue siendo cierto, sin presupuesto).
- l. 323: «Lo añadido en los dos últimos días»: está fechado a mediados de septiembre.
- l. 444: «Angular estático + API en Space de Gradio» → Vercel + Space.
- l. 118-133: la compañía ficticia se llama **Peldaño**. **Pregunta para Miguel:** ¿Peldaño sigue siendo la compañía y Pléyade su app, o cambia?
- Posible diapositiva nueva: el modelo articulatorio (0,57 frente a 0,44).

### `documento.tex` / `.pdf` (3.443 líneas) y `documento.md` (1.865, la copia de lectura)
Las secciones de datos, EDA, procesamiento y modelación del v4 **siguen siendo ciertas**
(el v4 es final y el catálogo no ha cambiado). Lo que envejeció:
- Título, cabeceras y l. 260, 271 (resumen y palabras clave): nombre y arquitectura.
- §Estrategia → Usabilidad → «La interfaz entregada» (l. 1046-1137): el Space estático → Vercel; «cuatro sitios» → cinco con Mi espacio; «ajustes (paleta…)» → temas; «40 rutas a fecha de `8ee42f0`» → **volver a contar** en `app/api.py`; la boca 3D de MakeHuman (l. 1125) → la didáctica; falta D5 y los datos por cuenta; enlace (l. 1129).
- Accionables (l. 1161-1187): A2 «Space estático gratuito» → Vercel; A4 «datos del lector» → por cuenta; A5 (micrófono): ¿ya se tiene? (el 16 sep se probó con el teléfono de Miguel); A8 (cinco lectores): ¿se hizo algo? Hay cuentas repartidas desde el 14 sep.
- Métricas de éxito (l. 1200-1201): las «85 parejas de las cinco paletas» son de **Gradio**; el contraste del front nuevo con fondo de galaxia **no está medido** → hueco o medirlo.
- Limitaciones (l. 3192-3243): despliegue (estático → Vercel) y (l. 3432) «datos separados por navegador» → por cuenta si se entra.
- Conclusiones (l. 3386-3390): «cinco paletas» y «el front en un Space estático».
- **Falta:** el modelo articulatorio como segundo modelo (Modelación o Resolución), si Miguel quiere. Es trabajo nuevo, con sus cifras en `investigacion/modelo_articulatorio/`.
- Referencias: MakeHuman (l. 762 de `estrategia.md` y el `.bib`) sobra si ya no se usa su malla; faltan GRID, Lombard GRID, USC-TIMIT, Blender y Vercel, si se citan.

### `estrategia.md` (791 líneas)
Tiene los mismos bloques que el documento: l. 1, 84, 155 (nombre); l. 429-512 (la interfaz entregada, la boca 3D de MakeHuman y el enlace); l. 665-667 (A2, A4); l. 691-692 (las cinco paletas); l. 129 «Mis libros» (hoy está en Mi espacio: comprobar).

### `notebook_proyecto.py` → `.ipynb` (2.675 líneas)
- l. 2, 11-12: nombre, arquitectura y enlace.
- l. 2486-2497: despliegue (7 USD, 48 h, «la demo 3D local no se cuenta como publicada»).
- l. 2367, 2386: tabla de usuarios y «cinco paletas».
- El resto (datos, modelos, métricas) no cambia. Se regenera con `tools/a_notebook.py` y hay que volver a ejecutarlo en limpio (57 celdas, 0 errores).

### `_portada.py`, `referencias.bib`
- `_portada.py:53`: el título es «LiteraLevel». Depende de cómo se decida el nombre.
- `referencias.bib`: Gradio sigue (es el motor). MakeHuman, según lo anterior. Faltan las fuentes nuevas si se citan.

### `README.md` (262 líneas)
Ya se actualizó en parte (`132da6b`: Vercel y respaldo). Quedan: l. 1 el título; l. 7 «Angular + API, con Gradio como respaldo» (bien); l. 255 la boca 3D «con la cabeza de…» (comprobar); el recuento de pruebas del 15 sep (l. 192).

### `PENDIENTES.md` (297 líneas)
- l. 1, 12-13: nombre y enlace.
- l. 59: «integración pública de la boca 3D sin verificar»: ya está publicada.
- l. 104, 121, 273: las paletas y `app/paletas.py` son de Gradio.
- l. 144, 280: 7 USD/mes (misma pregunta).
- Le faltan los pendientes de hoy: el vídeo con Angular, Eos, `uso_openai.json` a cero y las 13 capturas.

## Capturas
Las 13 de `entrega/capturas/` (01_inicio … 13_cierre) son del **14–15 sep**, con el diseño y
el nombre viejos (`registro.txt`: perfil 1,20, *Crime and Punishment*). Ni el documento ni la
presentación incluyen capturas: solo las usan los guiones como referencia y plan B.
Hay que rehacerlas desde Vercel con un navegador sin ventana, a 390 px y en escritorio.
Las que piden cuenta (explicación de IA, corrección, Mis palabras con cuenta) **no se pueden
hacer sin usar una contraseña**. Sin cuenta salen: inicio, nivel (cuestionario hasta 1,20),
Encontrar, ficha y curva, lector con el diccionario local, Pronunciar, la boca 2D y 3D y
«Sobre Pléyade».

## Preguntas para Miguel antes de tocar nada grande
1. **Nombre en el documento académico:** ¿«Pléyade (proyecto LiteraLevel)»? ¿El modelo sigue siendo «LiteraLevel v4»? ¿Y la compañía ficticia **Peldaño**?
2. **Modelo articulatorio:** ¿entra en el documento y en la presentación como segundo modelo, o solo se menciona?
3. **Capturas con cuenta:** ¿me das una cuenta de pruebas para usar dentro de un guion (sin imprimirla), o las hago solo sin cuenta?
4. **Coste:** ¿la cuenta Pro de HF (7 USD/mes) sigue activa hasta la entrega?
5. **`mensaje_profesor.md`:** ¿se envió? ¿Lo rehago como mensaje de entrega final?
6. **Classroom:** ¿hay avisos nuevos del profesor (por ejemplo, la petición de Vercel) que deba leer? Ahora mismo no tengo acceso a Classroom.

## Plan propuesto (piloto antes que lote)
1. Piloto: **`presentacion.tex`** (491 líneas, se compila y revisa en minutos, y toca el nombre, la arquitectura, la boca 3D y el enlace, que son los mismos cambios que todo lo demás). Miguel lo revisa.
2. Después: `mensaje_profesor.md` → `guion_demo_en_vivo.md` → `guion_video` (md, tex y pdf) → capturas → `estrategia.md` → `documento` (tex, pdf y md) → notebook → README y PENDIENTES.
