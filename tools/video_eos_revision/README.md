# Comercial de Eos: revisión de Miguel (28 sep 2026)

Este corte de revisión conserva a Eos visible y presenta funciones reales de
Pléyade en tema Noche. La voz usa Willow con dirección por escena y pausas
explícitas. El guion no narra métricas de entrenamiento ni la correlación de
la versión anterior.

## Secuencia

`guion_revision.json` contiene 13 escenas: gancho, problema, alivio,
presentación, nivel, búsqueda, curva, lector, práctica, lectura en inglés,
corrección, espacio personal y cierre. La lectura inglesa de Eos fue usada
como entrada de micrófono en la aplicación publicada; la app marcó `father`
y `mother` para revisar y mostró el sonido `/ɑ/` con explicación de la boca.
Las capturas de esa interacción están en
`D:/literalevel_video/comercial_completo_20260928/app_oscura/`.

## Generación del corte

Los WAV por escena y las capturas están fuera del repositorio, en
`D:/literalevel_video/comercial_revision_20260928/`. Las claves se obtienen
mediante `app/config.py` y nunca se escriben en el video ni en este árbol.

1. `generar_voz_revision.py` produce una voz por escena con la API Live y
   comprueba la transcripción recibida. Su importación de
   `generar_willow_demo.py` debe apuntar al directorio local de trabajo.
2. `generar_curvas_revision.py --workdir ...` ejecuta el generador del rig
   en lectura: `--boca modelo --gestos v3 --modelo_v3
   D:/literalevel_cara/v3_solo_noverbal --estilo_v3 real`. La carpeta v3
   contiene únicamente `noverbal/`; no se usa A2F local.
3. `preparar_montaje_revision.py`, ejecutado desde el directorio de trabajo,
   une audio y curvas. Inserta un silencio de 0,38 s en una zona de baja
   energía después de «en inglés», además de la pausa después del gancho.
   `ajustar_boca_audio.py` cierra el articulador Blender en silencios; no
   reemplaza la boca del rig.
4. Un servidor HTTP local sirve `visor/` aislado. `componer_revision.py
   --workdir ...` captura Eos y compone las pantallas de la app con un barrido
   suave, sin recuadro externo. Salida esperada:
   `D:/literalevel_video/comercial_revision_20260928/eos_pleyade_revision_720p.mp4`.

El compositor usa el visor aislado por `127.0.0.1:8772`; no modifica el
`index.html` del rig compartido. El corte apunta a 1280×720 a 24 fps y debe
mantenerse bajo los cinco minutos de la rúbrica. El master 4K queda para
después de la revisión humana de voz, cara, sincronía, ritmo y app. La mayor
resolución no garantiza por sí sola fotorrealismo: el modelo, pelo, materiales,
iluminación y animación de Epic/Unreal requieren su propia revisión.

## Estado

- Guion, voz, curvas, app real y montaje 720p preparados.
- La boca sigue siendo Blender; v3 solo controla lo no verbal.
- Comparación interna de mandíbula y energía: correlación de 0,543 a 0,712;
  mandíbula media en silencio de 0,081 a 0,016. Esta medida orienta la
  inspección, pero no demuestra sincronía labial perfecta. No aparece en el
  comercial.
- **Falta** el visto bueno de Miguel al video completo antes del master.
