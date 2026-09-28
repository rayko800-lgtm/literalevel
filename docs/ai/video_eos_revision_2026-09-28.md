# Eos: revisión audiovisual posterior al primer 720p

**Estado (28 sep 2026):** Miguel vio y aprobó la dirección del primer corte.
Pidió pausas e inflexión, mejor relación boca/audio, quitar la narración de
correlación y mostrar una corrección real de pronunciación. El nuevo corte
de 720p está en preparación en
`D:/literalevel_video/comercial_revision_20260928/`.

## Decisiones vigentes

- Eos sigue visible durante el comercial y narra todo.
- La boca proviene del modelo Blender; v3 solo controla gestos no verbales.
  No se usa A2F local.
- Se usa la voz Willow ya aprobada como dirección, con pausas entre escenas.
- La aplicación publicada se capturó en tema Noche; se mostró nivel,
  búsqueda, ficha, curva de dificultad, lector, palabras y Pronunciar.
- Eos pronuncia intencionalmente `feather` y `matter` ante una frase que
  contiene `father` y `mother`. La app detectó la diferencia y mostró una
  guía para el sonido `/ɑ/`.
- Las pantallas entran con barrido y bordes fundidos al fondo espacial.
- La correlación del modelo y otras métricas de entrenamiento no se narran.
- El master 4K en Colab/Epic queda después de la revisión humana de este
  corte. Todavía falta confirmar la calidad del modelo, materiales, pelo,
  iluminación y animación a esa escala.

## Evidencia y límites

- Guion y scripts: `tools/video_eos_revision/`.
- La transcripción de Live coincidió con el texto en las doce escenas nuevas
  en español; la escena inglesa usa una toma existente de Eos.
- El corte preparado dura aproximadamente 132 s a 1280×720/24 fps, bajo el
  máximo de cinco minutos.
- El ajuste de mandíbula reduce aperturas en silencio y mejora una medida
  interna de alineación; aún hace falta escuchar y mirar el MP4 completo.
- Se usó un visor aislado. No se editó `index.html` del rig compartido ni
  `docs/ai/HANDOFF.md`, que tenía cambios ajenos sin confirmar.

**Siguiente paso:** verificar reproducción, lectura de QR y sincronía visual
del MP4 completo; subirlo a Drive para la revisión de Miguel. Mantener el
primer corte como referencia, sin sustituirlo.
