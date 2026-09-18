# LiteraLevel — Product Roadmap (POST-ENTREGA)

Este documento registra ideas de producto que **no** entran antes de la
entrega. Ninguna se implementa hasta que Miguel lo pida explícitamente.
Ver `docs/ai/HANDOFF.md` para el estado operativo actual y
`docs/ai/AUDIT_STATUS.md` para el estado de las auditorías.

Origen de esta primera tanda: ensayo funcional A7 (16 sep 2026).

---

## 1. Onboarding guiado tipo tutorial interactivo

**Estado:** POST-ENTREGA

Recorrido único, no una serie de pantallas de bienvenida separadas:

cuenta → objetivo → nivel → búsqueda → libro → léxico → pronunciación →
continuar leyendo → mi espacio.

**Por qué:** el ensayo A7 mostró fricción de navegación con el esquema
actual de bienvenidas (paso 0 de cuenta + tarjeta de 4 pasos, que además
puede salir dos veces en el mismo navegador). Un tutorial interactivo que
recorra la app de verdad, en vez de tarjetas explicativas separadas de la
acción, es la alternativa a evaluar.

**No implica:** cambiar el guion de demo actual ni el paso 0 vigente.

---

## 2. "Continuar leyendo" desde Pronunciar

**Estado:** POST-ENTREGA

Añadir un acceso directo desde *Pronunciar* de vuelta al lector, que
regrese **exactamente al punto anterior** (mismo capítulo, misma posición),
no al principio del libro ni al índice.

**Por qué:** hoy "Una frase de mi libro" en *Pronunciar* depende de haber
abierto un libro, pero no hay camino de vuelta simétrico; volver a leer
exige recorrer *Encontrar* → libro → índice otra vez.

---

## 3. "Mi espacio" (Mis libros + Mis palabras + Repasar)

**Estado:** POST-ENTREGA

Replantear *Mis libros*, *Mis palabras* y *Repasa cinco* como una única
sección "Mi espacio" más visible en la navegación, en vez de piezas
sueltas repartidas por la app.

**Por qué:** son las tres superficies donde vive lo que el lector ya hizo
(estantería, vocabulario, repaso), y hoy compiten por atención con las
pantallas de tarea (*Encontrar*, *Pronunciar*) en vez de formar un destino
propio.

---

## 4. Repaso interactivo

**Estado:** POST-ENTREGA

Ampliar "Repasa cinco" con:
- recuerdo activo (no solo relectura pasiva de la lista);
- audio de la palabra;
- práctica de pronunciación integrada en el repaso, no solo en *Pronunciar*;
- repetición espaciada (programar cuándo vuelve a aparecer cada palabra);
- gráficas de progreso.

**Por qué:** hoy "Mis palabras" es una lista con frase de origen; convertirla
en un ciclo de repaso activo es lo que la acercaría a una herramienta de
aprendizaje de vocabulario real, no solo un registro.

---

## 5. Visualización articulatoria v2

**Estado:** POST-ENTREGA

Dos líneas de trabajo, ninguna antes de la entrega:
- **3D/Blender:** la nota ya existente sobre labios y corte de apertura al
  hablar (pedida por Miguel expresamente para después de la entrega, ver
  `docs/ai/HANDOFF.md` — "Blender (labios, corte de apertura) queda
  pospuesto") se conserva tal cual, sin repetirla aquí en detalle.
- **2D:** el corte de respaldo (cuando la boca 3D no carga o el dispositivo
  no la soporta) también debería mejorar, no solo servir de plan B; hoy es
  un dibujo estático de refuerzo.

**Por qué:** ambas vistas (2D y 3D) enseñan cómo se pronuncia un sonido;
mejorar solo la 3D deja al 2D como una versión de segunda para quien no
puede cargar el modelo pesado.

---

## 6. Read-along / audiolibro

**Estado:** POST-ENTREGA

TTS sincronizado con el texto resaltado, con:
- velocidades variables;
- modo *shadowing* (leer en voz alta a la vez que suena el audio, para
  practicar ritmo);
- posible función de pago (premium), a decidir con el resto de la política
  de cupos/costes.

**Por qué:** hoy la aplicación lee palabras y frases sueltas en voz alta
(*Pronunciar*), pero no ofrece seguir un capítulo entero con audio
sincronizado, que es un patrón habitual de apps de lectura en L2.

---

## 7. Crear cuenta self-service

**Estado:** POST-ENTREGA

Hoy no existe autorregistro: las cuentas las reparte Miguel por código
(`literalevel_codigos.txt`), y el front (`compartido/ajustes.ts`) solo
ofrece Usuario/Contraseña para entrar con una cuenta ya creada. Un flujo de
"Crear cuenta" self-service necesitaría ruta nueva en `app/api.py`,
almacenamiento y validación en `app/cuentas.py` (hoy congelado hasta
después de la entrega salvo SERIO) y pantalla nueva en el front.

**Por qué queda fuera de D1.2 (16 sep 2026):** el diseño de
"cuenta-elección" del tutorial guiado (D1) iba a ofrecer Entrar / Crear
cuenta / Continuar sin cuenta, pero "Crear cuenta" no tiene nada real
detrás. Miguel decidió no construir backend ni formulario dentro de D1: el
tutorial ofrece solo Entrar y Continuar sin cuenta, reflejando lo que la
app ya sabe hacer.

---

## Nota de proceso

Ninguno de los seis puntos anteriores tiene código, diseño ni fecha
asignada. Se listan para no perderlos, no para priorizarlos: la prioridad
la fija Miguel cuando llegue el momento post-entrega.
