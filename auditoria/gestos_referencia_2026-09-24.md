# Cuerpo labial en el resto de gestos

24 sep 2026. Miguel aceptó el fruncido de /u/ de la entrega 2fb95c5 y
pidió extender la mejora al resto de sonidos tomando su video como referencia.
Esta es una petición directa nueva, posterior al cierre de la autorización
nocturna automática. Comparación contra fruncido-volumen-2fb95c5.zip.

## Resultado

Los labios conservan más cuerpo en reposo, cierre, estiramiento y apertura.
Se añadió un correctivo `cuerpo_labial` al tejido exterior de los anillos2–5,
con caída gradual hacia las comisuras y continuación suave en la piel.
El visor reduce su contribución al estirar y la apaga cuando el fruncido
alcanza su valor máximo. La /u/ aceptada conserva sus posiciones; /w/ también.
No cambian los anillos funcionales0/1 ni los morfos anteriores. El perfil
del corte comparte el correctivo y mantiene sus raíces rígidas.

El relieve labial del material ahora usa surcos más cortos, menos profundos
y menos regulares. Color, rugosidad, dientes, lengua y tono moreno se conservan.
El correctivo se aplica según los parámetros de cada gesto, incluidos los
estados intermedios; no se ha copiado la forma de /u/ a todos los sonidos.
Modelos antiguos sin la nueva clave siguen funcionando.

Se revisaron las referencias privadas de sonrisa, apertura y cierre alrededor
de3,17 y129s, además del fruncido previamente revisado. Se usan como referencia
visual de tejido; no se atribuyen fonemas a fotogramas sin análisis del audio.
No es una reconstrucción de Miguel ni una estimación de volumen o milímetros.
Sólo recursos gratuitos. Video y fotogramas privados fuera de Git, ZIP y visor.

## Evidencia

Altura central aparente del cuerpo respecto al borde, unidades del modelo:

| Gesto | Superior antes → después | Inferior antes → después |
| --- | ---: | ---: |
| /i/ | .13842 → .18717 | .24393 → .27318 |
| /æ/ | .13888 → .18763 | .27861 → .30786 |
| /ɑ/ | .13591 → .21091 | .29520 → .34020 |
| /p/ | .11504 → .19004 | .16876 → .21376 |
| /f/ | .10747 → .18247 | .38640 → .43140 |
| /u/ | .30660 → .30660 | .31316 → .31316 |

El medidor registra perfiles y anchuras de las46 poses del catálogo, además
de81 muestras del ciclo /u/. Su grosor mínimo central es100% superior y92.20%
inferior respecto al NUEVO reposo, ahora más grueso. No comparar ese porcentaje
directamente con95.81% del reposo anterior. La abertura de /u/ sigue .4944×.156,
y el cuerpo mantiene anchura1.34181. No son pruebas de conservación de volumen.

- 2227 estados del runtime real: penetración exterior0, cierre .0000513077,
  distancia /f–v/ máxima .005401 y liberación .712725. Mismos valores previos.
- Costura:53 vértices/error0. Plegado superior0. Raíces:37/error1.276526e-7.
  Lengua: sección .00068160<.001, ningún estado fuera de tolerancia.
- 260 anclas: morfos anteriores exactos, incluido fruncir; nuevo correctivo0
  en esas anclas. Las128 comprobaciones inferiores de /f–v/ siguen exactas.
- 82/86 mallas idénticas. En las otras4 sólo se añade cuerpo_labial. Una normal
  exterior varía .00032802 (tolerancia .001); base, UV, índices y morfos
  anteriores idénticos por hashes. No hay cambios inesperados.
- Angular:135 pruebas/9 archivos aprobados; TypeScript y build aprobados.
  Persiste advertencia previa de pronunciar.css:12.64kB frente a presupuesto12kB.
- Revisión móvil390×844, contenido375=documento375, consola sin errores.
  Pares antes/después de /i æ u/ con cámara/luz iguales; controles /ɑ p f s θ/;
  /p f/ también en corte. Capturas finales con «Mantener gesto» explícito para
  evitar confundir una transición con la pose sostenida.

La mejora es moderada, más visible en el labio superior abierto o estirado.
Se conserva esta variante; no hubo candidatos visuales descartados. Las
capturas iniciales hechas antes de acabar la transición se reemplazaron por
poses sostenidas y no se usan como evidencia comparativa.

Persisten una lengua simplificada, interior ilustrativo, simetría y pliegues
de piel artificiales. No se alcanzó fotorrealismo. No se midieron FPS ni se
probó un teléfono físico. Las pruebas cubren los contactos definidos por el
piloto, no certifican anatomía clínica ni todas las intersecciones posibles.

## Reproducción

Blender2.93, `SALIDA_DIDACTICA=build/gestos_referencia`, ejecutar
`tools/boca3d_blender/cara_didactica.py`. Fuentes en el commit de esta entrega.

    node tools/boca3d_demo/medir_didactica.mjs build/gestos_referencia/cara.glb build/gestos_referencia/medidas_final.json --completo --exigir --exigir-raices --lengua=build/lengua_realista/lengua.glb
    node tools/boca3d_demo/medir_grosor_labial.mjs build/gestos_referencia/cara.glb build/gestos_referencia/grosor.json --exigir
    node tools/boca3d_demo/medir_grosor_labial.mjs build/gestos_referencia/cara_antes.glb build/gestos_referencia/grosor_antes.json --exigir
    node build/gestos_referencia/validar_anclas.mjs
    node build/gestos_referencia/comprobar_invariantes.mjs build/gestos_referencia/cara_antes.glb build/gestos_referencia/cara.glb build/gestos_referencia/invariantes.json

Los auxiliares están en Evidencias del ZIP; copiarlos a build/gestos_referencia.
Recuperar cara_antes.glb de fruncido-volumen-2fb95c5.zip. Los dos proyectos
Blender del paquete llevan sus texturas incorporadas. La apariencia final
del visor incluye el material y movimiento de Three.js.

No se fusiona master ni se despliega producción. front/angular.json ajeno
conserva SHA256 0916137F608401AAF0F52B9FDFEB05F7E7D6876C7B07A7C70F0B78A05F505858.
