# Encargo: la cara que habla (vista de frente) de LiteraLevel

**Para:** una sesión nueva. **De:** Miguel (25 sep 2026), con el contexto de la
sesión que hizo la boca 3D y la integración del modelo articulatorio.

Antes de empezar lee `docs/ai/HANDOFF.md`, `AGENTS.md` y, para el modelo,
`investigacion/modelo_articulatorio/resultados.md` e `integracion.md`.

## 1. Por qué

La cabeza 3D actual de Pronunciar (`front/src/app/compartido/boca3d/`,
`tools/boca3d_blender/`) es un escaneo LPS (CC BY 3.0) con la boca y los ojos
CERRADOS, partido en dos mitades, al que se le añadieron a mano labios de
topología regular, ojos, pelo y mentón. Miguel lo grabó hablando (25 sep) y
el diagnóstico es:

- grietas y línea de corte vertical en labio y mentón (costura de las mitades);
- labios «de goma» (pieza aparte sobre una cara de boca cerrada);
- dientes como bloques y boca negra por dentro;
- cara inexpresiva: sin parpadeo, cejas, mirada ni movimiento de cabeza.

Cada arreglo mejoró algo, pero esa base no llega a «una persona hablando».

## 2. Objetivo

Una cabeza de frente **que hable con naturalidad** el audio del TTS de OpenAI
(y, más adelante, que se pueda **conversar** con ella con un chat de voz). La
vista lateral didáctica (corte con lengua, paladar, anatomía) **se queda como
está**: la cara nueva es solo la vista de frente, en un componente aparte y
detrás de un interruptor hasta que Miguel la apruebe al 100 %.

## 3. Lo que hay que decidir con datos (informe primero, sin código)

### 3.1 La cabeza

Compara, con licencia verificada en la fuente, calidad visual, peso en web y
trabajo necesario:

1. **MetaHuman** (Epic). Desde 2025 la licencia permite usarlos fuera de
   Unreal, gratis por debajo de 1 M USD al año. Fotorrealista y con rig facial
   completo; pesado para WebGL: hay que exportar a Blender y reducir (LOD,
   texturas, número de blendshapes). Confirma que el uso en una app web
   pública lo permite y qué exige la exportación (¿Unreal instalado? ¿GPU?).
2. **ICT-FaceKit** (USC ICT): modelo facial escaneado con expresiones con los
   nombres de ARKit; MIT para la versión no comercial. Confirma si nuestro uso
   (proyecto académico, app pública gratuita) cabe.
3. **MakeHuman / MPFB** (CC0 / CC BY): libre del todo, menos fotorrealista;
   blendshapes ARKit por transferencia de deformación
   (`vasiliskatr/deformation_transfer_ARkit_blendshapes`, MIT).
4. **La cara de Miguel escaneada** (fotogrametría con el móvil, gratis) y
   transferida a una topología con blendshapes ARKit. Es su cara y él da su
   consentimiento; valorar el trabajo de limpieza y retopología.
5. **Desde cero con anatomía** (cráneo, músculos, piel): Miguel lo propuso.
   Valora el coste honestamente frente a las demás; el realismo de piel y
   forma sale de escaneos, no de libros.

Nada de caras de personas reales sin su consentimiento (una foto de Instagram
no vale). Sin gasto: nada de pago (ni Faceit, ni Wrap, ni tiendas).

### 3.2 Lo que ya está hecho y se puede reutilizar

- **TalkingHead** (`met4citizen/TalkingHead`): clase JavaScript de cabezas
  parlantes con blendshapes ARKit y visemas, parpadeo, mirada y movimiento de
  cabeza, en three.js. Verifica licencia y si sirve de base o de referencia.
- Nuestro **modelo articulatorio** (`front/src/app/compartido/boca3d/modelo.ts`
  + `modelo_articulatorio.json`, dominancia entrenada con GRID): ya predice
  controles con nombre ARKit (`jawOpen`, `mouthPucker`, `mouthFunnel`,
  `mouthRollLower`, `mouthPress`, `mouthClose`, `cheekSquint`) y geometría de
  labios. Con una cabeza ARKit se conectan directos, sin pasar por poses.
- La frase del TTS alineada por palabra (`lineaFraseAlineada`, marcas de
  whisper) y el énfasis por palabra que ya calcula `app/voz.py`
  (`analizar_natural`): sirven para cejas y cabeceo en las palabras con énfasis.

### 3.3 La vida de la cara

Parpadeo (cada 3–6 s, más en pausas), microsacadas de la mirada, cejas en el
énfasis, cabeceo leve al final de frase, sonrisa suave en las pausas. Proponer
cómo se genera (reglas con aleatoriedad controlada o aprendido de los mismos
datos de GRID/MediaPipe) y medirlo contra vídeo real.

### 3.4 Conversación (fase posterior)

Qué haría falta para hablar con la cabeza en tiempo real (OpenAI Realtime /
GPT-Live con voz de salida y la cara sincronizada con el audio que llega por
streaming): latencia, coste por minuto y límites por cuenta.

## 4. Restricciones

- Sin gasto (Colab gratis; GPU la semana próxima si hace falta).
- Licencias verificadas en la fuente original y citadas en los créditos.
- Varias sesiones comparten el repo: nada de `git stash`, `checkout` global
  ni `add -A`; commit solo de tus rutas. Trabaja en una rama o worktree
  propio; **no toques** el corte lateral ni `app/` sin avisar.
- Publicar solo con la aprobación de Miguel (API primero, pruebas en árbol
  limpio, front después; skill `desplegar-en-spaces`).
- En el móvil de 390 px tiene que ir fluido: presupuesto de peso y fps.

## 5. Entregables, en este orden

1. Informe de decisión (un bloque markdown) con la opción recomendada, las
   descartadas y por qué, licencias con enlace y un plan por sesiones.
2. Piloto: la cabeza elegida en el navegador diciendo una frase del TTS con
   el modelo articulatorio y parpadeo, en un visor aparte. Vídeo lado a lado
   con la cabeza actual para que Miguel decida.
3. Integración detrás de un interruptor en Pronunciar («Verla leída en 3D»).
