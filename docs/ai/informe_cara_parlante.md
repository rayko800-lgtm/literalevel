# Informe de decisión: la cara que habla (vista de frente)

**Fecha:** 25 sep 2026. **Encargo:** `docs/ai/encargo_cara_parlante.md`.
**Decisión de Miguel (25 sep):** MetaHuman. Este informe ya no compara para
elegir: comprueba si MetaHuman es viable aquí, qué falta y en qué orden.

## 1. Veredicto

MetaHuman es viable **con dos condiciones que hay que resolver antes de
escribir código**:

1. **Máquina.** Crear y exportar un MetaHuman exige Unreal Engine 5.6 o
   posterior en local. Epic recomienda 16 núcleos, 32 GB de RAM y una GPU de
   8 GB (RTX 3070). Este PC tiene una **GTX 1650 SUPER de 4 GB y 16 GB de
   RAM**: queda por debajo. Colab no sirve (Unreal necesita editor con
   ventana). Hay dos salidas: probar aquí con texturas bajas (sin garantía;
   el autorig y la síntesis de texturas van en la nube de Epic, así que lo
   pesado local es el ensamblado) o esperar la GPU de la semana próxima.
   Espacio: Unreal ocupa 60–100 GB → instalar en **D:** (HDD de 1 TB, 707 GB
   libres). Se valoró pasarlo al SSD (C:, 223 GB): tiene 16 GB libres y lo
   que se puede mover sin riesgo (Descargas 15 GB, `.cache` 7 GB) no llega;
   para más habría que tocar AppData o anaconda. No compensa: en el HDD
   Unreal tarda más en abrir y compilar sombreadores, pero funciona.
   **Decidido (Miguel, 25 sep): D:, con Colab para entrenar.** El Epic
   Launcher ya está instalado, pero **no tiene sesión**: hay que entrar con
   la cuenta de Epic (no se escriben contraseñas desde aquí).
2. **Licencia para servir el archivo en la web: VERIFICADA (25 sep, texto
   del EULA de Unreal leído entero).** Desde MetaHuman 5.6 rige el EULA
   estándar de Unreal. §4(a)(i): son *Non-Engine Products* los «asset
   files, such as character models and animations, … that you developed
   using Engine Code. Such asset files remain Non-Engine Products even if
   included in Products that use or rely on other video game engines».
   Un `.glb` con la cabeza, servido a three.js, entra ahí: se puede
   distribuir, sin regalías. Nuestro caso además no genera ingresos
   (§4(a)(ii)) y estamos por debajo de 1 M USD (§6(b)).
   **Dos restricciones que sí nos tocan** (§5(e)):
   - no usar MetaHumans ni sus curvas de animación «to build or enhance any
     database or training **or testing** any artificial intelligence». Por
     eso el modelo articulatorio y el de expresión se entrenan **y se
     evalúan** contra vídeo de personas reales (GRID, TalkingHead-1KH), y
     nunca contra renders del MetaHuman. El MetaHuman solo *muestra* lo que
     el modelo predice;
   - no combinar la tecnología de Unreal con código GPL ni CC BY-SA (§5(c)).
     El `.glb` exportado no es tecnología de Unreal, pero por prudencia no
     metemos código GPL en la tubería de exportación.

## 2. Lo que se reutiliza

| Pieza | Licencia (fuente) | Uso |
|---|---|---|
| `smorchj/metahuman-to-glb` | MIT ([repo](https://github.com/smorchj/metahuman-to-glb)) | Tubería UE 5.7 → GLB con **51 blendshapes ARKit** → Blender (Draco) → visor three.js. Probado en Safari de iPhone X. Pide UE 5.7 (o 5.6 heredado), Blender 5.x y Windows. |
| `met4citizen/TalkingHead` | MIT ([repo](https://github.com/met4citizen/TalkingHead)) | **Referencia, no base.** Exige esqueleto Mixamo («Armature») y visemas de Oculus; el MetaHuman no trae ninguno de los dos. Tomamos su lógica de parpadeo, mirada, cabeceo y *streaming* (`streamStart`/`streamAudio`), y la citamos en los créditos. |
| `modelo.ts` + `modelo_articulatorio.json` | propio | Ya produce `jawOpen`, `mouthPucker`, `mouthFunnel`, `mouthRollLower`, `mouthPress`, `mouthClose` y `cheekSquint`: nombres ARKit, que se conectan **directo** a los morph targets. No hacen falta visemas. |
| `lineaFraseAlineada` + énfasis (`app/voz.py`, `analizar_natural`) | propio | Tiempos por palabra para cejas y cabeceo. |

**Límites conocidos de la tubería** (los declara su README): el horneado
FBX **pierde los correctivos finos de los labios** (compresión de labio,
arrugas; 5–10 mm), pestañas de baja resolución, oclusión del ojo sin alfa y
un solo `browInnerUp` (sin asimetría de cejas). Lo primero toca justo los
labios, y los labios son lo que falló en la cabeza actual. **El piloto mira
eso antes que nada.**

## 3. Presupuesto para el móvil de 390 px

- La tubería sale en **~40 MB** con texturas de 1024 px. Es demasiado. La
  cara didáctica actual pesa 7,0 MB.
- **Objetivo: ≤ 10 MB.** Solo cabeza y cuello (sin cuerpo ni ropa), un LOD
  más bajo del MetaHuman, texturas de 1024 → 512 px en KTX2, geometría y
  morphs con meshopt o Draco, y pelo en tarjetas en vez de *grooms*.
- **≥ 30 fps** a 390 px en un Android medio. Se mide igual que la boca 3D
  (`medir_didactica.mjs` adaptado), no a ojo.

## 4. La vida de la cara

**Actualización (25 sep, tarde):** Miguel pidió variedad de YouTube para la
expresión; su profesor dio el visto bueno. Usamos **TalkingHead-1KH**
(NVIDIA, repo MIT): vídeos de YouTube publicados con licencia **CC BY 3.0**
por sus autores y los tramos con cabeza hablando ya marcados. Eso da la
variedad de YouTube con licencia limpia; el guion comprueba vídeo a vídeo
que la licencia sigue siendo CC y guarda título, canal y URL en
`creditos.csv` para la atribución. La descarga (con `yt-dlp`) va contra las
condiciones de uso de YouTube aunque el contenido sea CC BY: se hace sin
cookies de ninguna cuenta, para no arriesgar la de Miguel, y con pausas.

Código: `tools/cara_parlante/` (`bajar_1kh.py`, `medir_expresion.py`,
`lote_1kh.sh`, cuaderno `entrenar_expresion.ipynb` para Colab con GPU).
Datos fuera de Git: `D:/literalevel_cara/`.

**Piloto (3 clips, 97 s, 2 hablantes):** parpadeo **20–21/min**, duración
mediana 80–120 ms; cabeza con desviación típica de 1–4° de guiñada y 2,5–6°
de cabeceo; correlación fotograma a fotograma entre cejas y tono de solo
r = 0,07–0,10. Consecuencias: el parpadeo sube de 10–20/min a ~20/min; el
cabeceo es más amplio de lo que proponía; las cejas no siguen al tono
fotograma a fotograma, así que hay que medirlas por evento (énfasis), no por
correlación. Con 3 clips no hay conclusiones: el lote de 300 vídeos está
corriendo.

Propuesta inicial, antes del piloto (se recalibra con el lote):

| Gesto | Regla inicial | Con qué se mide |
|---|---|---|
| Parpadeo | intervalo 3–6 s (gamma), 150 ms; más probable en pausas y al final de frase | `eyeBlink` de MediaPipe en los vídeos de GRID de `D:/literalevel_articulatorio` (frecuencia y duración reales) |
| Microsacadas | 0,5–2° cada 0,5–1,5 s; la mirada vuelve al centro | ídem, `eyeLook*` |
| Cejas | `browInnerUp`/`browOuterUp` 0,2–0,4 en las palabras con énfasis, 100 ms antes de la sílaba | énfasis de `analizar_natural` |
| Cabeceo | 2–4° hacia abajo al final de frase; deriva lenta con ruido de Perlin mientras habla | pose de cabeza de MediaPipe en GRID |
| Sonrisa | `mouthSmile` 0,1–0,15 en pausas > 400 ms | — |

GRID son frases leídas ante cámara con poco gesto: sirve para el parpadeo y
la mirada, y se queda corto para las cejas. Hay que declararlo.

## 5. Conversación (fase posterior)

La cara ya encaja con audio por *streaming*: el modelo articulatorio
funciona por fotograma (< 0,01 ms), así que puede ir detrás del audio si los
tiempos de fonema se sacan de las marcas de texto que devuelve la API.
Precio orientativo de `gpt-realtime` en julio de 2026: 32 USD por millón de
tokens de audio de entrada y 64 de salida; el mini cuesta ~⅓. Eso da ~0,06–0,11
USD/min con caché en el modelo grande y ~0,02–0,05 en el mini
([forasoft](https://www.forasoft.com/blog/article/openai-realtime-api-pricing),
[layer3labs](https://www.layer3labs.io/guides/openai-realtime-api-pricing);
confirmar en https://developers.openai.com/api/docs/pricing antes de
presupuestar). Con «sin gasto», se hace después de la entrega del 3 oct y
con el mini.

## 6. Descartadas (por decisión de Miguel; quedan de repuesto)

- **ICT-FaceKit:** licencia no comercial. Sirve de repuesto si el EULA de
  Epic cierra la web.
- **MPFB/MakeHuman (CC0)** + transferencia ARKit (MIT): es la salida si la
  máquina no puede con Unreal. Menos realista.
- **Cara de Miguel escaneada:** buena y con consentimiento, pero lleva
  retopología y limpieza a mano (días).
- **Desde cero con anatomía:** semanas. La piel y la forma realistas salen
  de escaneos, no de libros.

## 7. Plan por sesiones

| # | Quién | Qué | Hecho cuando |
|---|---|---|---|
| 0 | Miguel | Confirmar la cláusula de distribución (§1.2) y elegir: probar en este PC o esperar la GPU | decisión escrita |
| 1 | Miguel (+ yo guiando) | Epic Launcher y UE 5.7 en **D:**, aceptar el EULA, crear en MetaHuman Creator una cara inventada (no de persona real), texturas bajas | MetaHuman ensamblado |
| 2 | sesión nueva, rama `dev/cara-parlante` en worktree | `metahuman-to-glb` → solo cabeza, reducción a ≤ 10 MB; medir peso y fps; **revisar labios en `jawOpen`/`mouthPucker`/`mouthFunnel`** | GLB medido + capturas |
| 3 | ídem | Visor aparte (fuera de la ruta de Pronunciar): `modelo.ts` → morphs ARKit directos, frase del TTS alineada, parpadeo y mirada | vídeo lado a lado con la cabeza actual |
| 4 | Miguel | Aprobar o no el piloto | — |
| 5 | sesión | Componente aparte detrás del interruptor «Verla leída en 3D», vista de frente; el corte lateral no se toca; créditos (Epic, TalkingHead, metahuman-to-glb) | pruebas del front + 390 px; se publica con la aprobación de Miguel |
| 6 | después del 3 oct | Conversación con Realtime mini | — |

## Fuentes

- [CG Channel: licencia de MetaHuman 5.6, uso en otros motores](https://www.cgchannel.com/2025/06/you-can-now-sell-metahumans-or-use-them-in-unity-or-godot/)
- [State of Unreal 2025](https://www.unrealengine.com/news/all-the-big-news-and-announcements-from-the-state-of-unreal-2025) · [MetaHuman 5.6](https://www.metahuman.com/news/metahuman-leaves-early-access-with-a-feature-packed-new-release)
- [Requisitos de hardware de MetaHuman en Unreal](https://dev.epicgames.com/documentation/metahuman/metahuman-hardware-requirements-in-unreal-engine)
- [MetaHuman Creator en Unreal](https://dev.epicgames.com/documentation/metahuman/metahuman-creator-in-unreal-engine?lang=en-US)
- [smorchj/metahuman-to-glb](https://github.com/smorchj/metahuman-to-glb) · [met4citizen/TalkingHead](https://github.com/met4citizen/TalkingHead)
- EULA de Unreal: https://www.unrealengine.com/eula/unreal (sin leer: 403/Cloudflare)
