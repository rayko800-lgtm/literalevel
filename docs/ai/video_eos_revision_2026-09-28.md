# Eos: revisión audiovisual posterior al primer 720p

**Estado (28 sep 2026):** Miguel vio y aprobó la dirección del primer corte.
Pidió pausas e inflexión, mejor relación boca/audio, quitar la narración de
correlación y mostrar una corrección real de pronunciación. Tras revisar ese
video, pidió que la app no quedara tapada por el difuminado izquierdo, que sus
pantallas no se movieran fuera de los actos narrados y que Eos tuviera menos luz.
La revisión v3 de 720p está terminada en
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
- En v3 la app ocupa el lado derecho sin oscilación: la transición izquierda
  mide 28 px en vez de 145 px. Los cambios de pantalla tienen marcas ligadas
  al audio, y una disolvencia de 0,32 s pasa por el fondo sin superponer dos
  interfaces completas. El contador de grabación cambia dentro de la misma
  vista. El botón «Corrígeme» permanece visible cuando Eos lo dice y el
  resultado aparece al empezar «Mira».
- La luminosidad del avatar se redujo en la composición a 0,82 de la toma
  anterior. No se modificaron el audio, las curvas de boca ni el rig.
- La correlación del modelo y otras métricas de entrenamiento no se narran.
- El master 4K en Colab/Epic queda después de la revisión humana de este
  corte. 4K no vuelve fotorrealista al GLB web actual. Falta un piloto Epic
  iluminado y aprobado de frente y tres cuartos, con piel, pelo, ojos,
  hombros/blusa y animación terminados.

## Evidencia y límites

- Guion y scripts: `tools/video_eos_revision/`.
- La transcripción de Live coincidió con el texto en las doce escenas nuevas
  en español; la escena inglesa usa una toma existente de Eos.
- Revisión v3: `eos_pleyade_revision_v3_720p.mp4`, 12.785.995 bytes,
  SHA256 `B18A8322098D0C0D040609783379AE0E4799B57E47811E8462AD480B3C8A2402`.
  Decodifica completa: 3.169 fotogramas, 1280×720/24 fps, H.264 Baseline y
  AAC. Dura 2:12 y queda bajo el máximo de cinco minutos. El QR del fotograma
  final se decodificó como
  `https://pleyade-app.vercel.app/`.
- Copia v3 para revisión en Drive:
  `https://drive.google.com/file/d/1XBomomgYqRJs9_Iioz_HWLv_DEZf-B4W/view?usp=drivesdk`.
  La lectura de metadatos confirmó 12.785.995 bytes. El procesamiento del
  visor de Drive no equivale a una revisión humana.
- La copia anterior sigue disponible en Drive:
  `https://drive.google.com/file/d/1JE_U4xYRg0Pg_Kx-J6AI9tE6DtC2LtyV/view?usp=drivesdk`.
- El ajuste de mandíbula reduce aperturas en silencio y mejora una medida
  interna de alineación; aún hace falta juicio humano sobre sincronía,
  naturalidad de voz y expresión.
- Se usó un visor aislado. No se editó `index.html` del rig compartido ni
  `docs/ai/HANDOFF.md`, que tenía cambios ajenos sin confirmar.
- Prueba estática `ue_lit_probe_20260928.png`: se activó temporalmente el modo
  iluminado del visor de Unreal 5.8 y se volvió al modo anterior, sin guardar
  assets. El personaje v21 todavía muestra manga/piel provisional, pelo poco
  convincente y mirada/expresión que no justifican prometer fotorrealismo. La
  prueba es del visor, no un render cinematográfico ni evidencia 4K.

**Siguiente paso:** Miguel revisa v3 en Drive. Con su autorización ya dada
para mejorar el realismo, preparar una prueba corta de acabado en Epic/Unreal
antes del master 4K: piel y pelo nativos con iluminación real, hombros y
blusa sin material de piel falso, mirada natural y sincronía de boca. Comparar
de frente y tres cuartos. Mantener los cortes anteriores como referencia.
