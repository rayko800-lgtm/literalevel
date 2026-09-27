# Eos: de la red de fusión a Audio2Face + no verbal generativo (26 sep 2026)

Informe técnico de la sesión `literalevel-29` (con `literalevel-c2`, dueña de Eos).
Sirve para los entregables del Módulo 5 (documento y presentación): qué se midió,
qué se descartó y por qué, y cómo queda la cara que habla.

## 1. Punto de partida

La red de fusión (Blender + voz, `tools/cara_parlante/voz2cara/entrenar_fusion.py`)
tocó techo en la época 22 sobre etiquetas MediaPipe: r de validación boca 0,33,
sonrisa 0,24, cejas 0,14, ojos 0,10, cabeza 0,13. El plan v3 (`estado_del_arte_2026-09.md`)
proponía reetiquetar con SMIRK, voz HuBERT-large, boca por regresión y un modelo
generativo para lo no verbal.

## 2. ¿Merece la pena reetiquetar con SMIRK? No (medido)

- **Piloto en Colab (A100, 37 min, 4,2 unidades):** SMIRK etiquetó 4 discursos de
  Obama (1 h de vídeo; cara en el 88-97 % de los fotogramas). Fiabilidad SMIRK↔MediaPipe
  por grupo (r sin media por clip): boca 0,36, sonrisa 0,44, ojos 0,31, cejas 0,28.
  Umbral previsto para seguir: boca ≥ 0,45. (`voz2cara/v3/fiabilidad_piloto.json` en Drive.)
- **Legibilidad labial (c2, local, 45 clips de 1KH, 12 k fotogramas):** un clasificador
  lineal adivina la clase de sonido (p/b/m, f/v, u/o, vocal abierta, i/e) desde las
  etiquetas, con validación cruzada por clip. SMIRK 0,217, MediaPipe 0,206, juntos
  0,217; azar 0,167. Ninguna etiqueta 2D lee bien los labios; no compensa pagar
  ~12 unidades de etiquetado.
- **Coste que se evitó:** Obama son 3,27 M de fotogramas (36,3 h). MediaPipe en CPU
  cuesta 29 ms/fotograma; una T4 High-RAM tardaría ~7 h (12 u), una A100 ~4,3 h (29 u).
- **Aceleraciones probadas y descartadas** (cambiaban las etiquetas, no solo el tiempo):
  MediaPipe cada 2 fotogramas (expresión r 0,87 frente a cada 1); recorte con el
  detector BlazeFace calibrado en vez de los 478 puntos (mandíbula r 0,92, error 37 %
  de la sd: SMIRK es sensible al recorte). Sí válida: decodificar con NVDEC
  (fotogramas idénticos bit a bit; 16 → 6 ms de CPU).

## 3. La boca: NVIDIA Audio2Face-3D v3.0 sin SDK

Modelo abierto (24 sep 2025; NVIDIA Open Model License, uso comercial y no comercial;
SDK MIT). HuBERT + difusión (180 M), entrenado con captura 4D. En vez de compilar el
SDK (CUDA 12.9 + TensorRT), se reimplementó su ejecutor en Python con ONNX Runtime
en CPU (`tools/cara_parlante/a2f/a2f_onnx.py`; modelo en `D:/literalevel_cara/a2f/`):

- ventanas de 1 s a 16 kHz que avanzan 0,5 s; estado GRU realimentado; ruido N(0,1)
  con semilla fija; salida = desplazamientos de 24 002 vértices de piel + 5 602 de
  lengua; suavizado exponencial del SDK; blendshape solve acotado (bvls, L1/L2/
  temporal/simetría) sobre 4 262 vértices frontales y 39 poses activas.
- 9 s de audio → 15 s de CPU. Salida: 52 ARKit a 60 fps + 16 poses de lengua.
- Límites: no anima ojos ni cabeza (siempre 0); `mouthClose` incluye la mandíbula;
  emoción neutra por defecto (admite 10 emociones por fotograma).
- Comprobación con la frase «Peter Piper picked a peck of pickled peppers…»
  (edge-tts Ava): cierres de labios en las p/m, fruncido 0,85 en «blew», boca
  quieta en los silencios (jawOpen 0,06).
- Frente a la boca de Blender en la misma frase (c2): mandíbula 0,55 vs 0,35, cierre
  de labios 0,42 vs 0,06, redondeo 0,55 vs 0,15. Integrado en `generar.py --boca a2f`
  con las garantías pedagógicas de Blender encima (p/b/m cierran, u/o redondean al
  menos como Blender); lengua, dientes y garganta siguen siendo los de Blender.

## 4. Lo no verbal: modelo generativo v3 (entrenado hoy)

`tools/cara_parlante/voz3/entrenar_noverbal.py`: flow matching 1D con transformer,
condicionado por HuBERT-large (7 capas, 25 Hz), «habla» + articulación y un vector de
estilo. Datos: Obama (36 h) + 1KH (3,5 h) con etiquetas MediaPipe. A100 High-RAM de
rayko800, 20:19-21:55 (≈11,5 unidades): rasgos HuBERT de 882 clips (36 GB) en 25 min,
articulación 1KH con Whisper, y entrenamiento a 11 s/época, parado por paciencia en la
época 232 (mejor 202).

Validación (111 clips, 215 ventanas de 10 s): pérdida de flujo 0,536; **alineación de
los movimientos de cabeza con los golpes de voz 0,773 (caras reales: 0,74)**;
diversidad 0,926; FDD 0,711; r por grupo (orientativo, es generativo) sonrisa 0,12,
cabeza 0,07, cejas 0,05, ojos 0,03. Modelo en `D:/literalevel_cara/v3_modelo/noverbal/`
y en Drive `voz2cara/v3/noverbal/`.

## 4 bis. Boca por regresión v3 (entrenada la noche del 26, 22:52-23:42): NO supera a A2F

`entrenar_boca.py` (transformer sobre HuBERT + articulación de Blender, objetivo MediaPipe), A100,
16,5 s/época, 41 épocas (mejor la 11; después sobreajusta). Validación (111 clips): r boca 0,305
(fusión anterior 0,33; techo con etiquetas 2D ≈ 0,45); jawOpen 0,58, mouthPucker 0,51, mouthFunnel
0,36, mouthClose 0,22; cierre en p/b/m 0,225 (real 0,155), redondeo en u/o 0,245 (real 0,502).
Coincide con la legibilidad labial (§2): con etiquetas 2D la boca no pasa de r ≈ 0,3. Audio2Face
queda confirmado como boca de Eos con números. Modelo guardado en Drive `voz2cara/v3/boca/` para el
vídeo comparativo. Coste del día: ≈ 30 unidades (piloto 4,2 + no verbal 11,5 + boca ≈ 14).

## 5. Cómo queda Eos

| Parte | Fuente | Por qué |
|---|---|---|
| Labios, mandíbula, mejillas al hablar | Audio2Face-3D (52 ARKit) | captura 4D; articula más y mejor que cualquier etiqueta 2D |
| Precisión pedagógica de la boca | modelo articulatorio de Blender (garantías p/b/m y u/o; lengua, dientes, garganta) | es lo que enseña la pronunciación |
| Sonrisa, ojos, cejas, cabeza | no verbal generativo v3 | la voz no los determina: hace falta un modelo generativo para que parezcan vivos |
| Voz | edge-tts (en-US-AvaNeural) | gratis |

Hecho (26 sep, 22:52-23:42): la boca v3 se entrenó y no supera a A2F (§4 bis). Pendiente:
comparar en vídeo tres versiones de la misma frase: fusión actual, A2F + no verbal v3,
boca v3 + no verbal v3.

## 6. Reproducir

- Cuaderno: `tools/cara_parlante/voz3/v3.ipynb` (`91f6dfa`) con `ETIQUETAS='mediapipe'`;
  variables añadidas en la copia lanzada: `ENTRENAR_BOCA`, `SALTAR_NOVERBAL`, `MAX_HORAS`.
  Reanudable desde Drive con la celda 2.
- A2F: `python a2f_onnx.py --wav frase.wav --salida frase_a2f.json --fps 25`.
- Colab desde VS Code y Drive sin robar el foco: skill `conectar-google` §3 ter.
