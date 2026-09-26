# Audio → cara 3D: estado del arte y qué hacer con Eos (26 sep 2026)

Resumen de una búsqueda (agente de investigación) tras el entrenamiento de la red de fusión
(boca 0,32, sonrisa 0,23, cejas 0,12, ojos 0,10, cabeza 0,13 de r en la época 11).

## Lo que limita
- **Etiquetas.** Los blendshapes de MediaPipe son imprecisos en labios (asimetrías, inestables con
  el giro de cabeza; [issue #5329](https://github.com/google-ai-edge/mediapipe/issues/5329)). Con Obama
  a 640 px, la boca ocupa unos 40 px. El ruido de fotograma a fotograma es pequeño (≈10 % de la
  varianza, medido aquí); el problema es el sesgo del estimador, no el temblor.
- **Cejas, parpadeo y cabeza no están determinados por la voz.** El campo no los evalúa con r, sino
  con FDD, diversidad y alineación con los golpes de voz; solo salen naturales con modelos
  generativos (DiffPoseTalk, ARTalk) o procedimentales.
- Casi nadie publica r por fotograma. Referencia orientativa (no publicada): boca 0,5–0,7 con
  etiquetas limpias y 0,3–0,45 con vídeo 2D.

## Qué haría, por ganancia/esfuerzo
1. **Reetiquetar con [SMIRK](https://github.com/georgeretsi/smirk)** (CVPR 2024; código MIT, FLAME no
   comercial). Piloto: 1 h de Obama y medir r MediaPipe↔SMIRK por blendshape; el techo alcanzable
   es ≈ √(fiabilidad). Si la fiabilidad de boca es baja, reetiquetar todo y pasar FLAME → ARKit con
   una matriz lineal ([mediapipe-blendshapes-to-flame](https://github.com/PeizhiYan/mediapipe-blendshapes-to-flame), invertida).
   Alternativa más legible en labios: [SPECTRE](https://github.com/filby89/spectre) (CC BY-NC-SA; sobrearticula).
2. **Codificador de voz HuBERT-large o WavLM-large**, congelado, con suma ponderada aprendida de
   capas. Mejora la sincronía labial frente a wav2vec2 (FaceDiffuser, KeySync).
3. **Separar boca y no verbal.** La boca, por regresión (con [BlendVOCA](https://arxiv.org/html/2401.08655v1)
   como supervisión limpia auxiliar). Cejas, parpadeo y cabeza, con una cabeza generativa pequeña
   (difusión 1D o VQ), evaluada con FDD y diversidad.

## Licencias
Todo vale para uso académico. FLAME, VOCASET, SPECTRE, MEAD y Multiface no permiten uso comercial
sin licencia aparte; solo son permisivos UniTalker (Apache-2.0) y el código de SMIRK (MIT).
