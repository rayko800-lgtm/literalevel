# Auditoría de `5033e69`: léxico, consumidores y gasto

Fecha: 13 de septiembre de 2026  
Alcance: `app/lexicon.py` en `5033e69`, con sus consumidores `app/ui.py` y
`app/api.py` en el mismo commit.  
Modo: solo lectura. No se hicieron llamadas a OpenAI ni se ejecutó código con
credenciales.

## Resultado

Encontré **4 problemas**: 1 alto y 3 serios. La ruta sin clave, la etapa
`diccionario` de la API, la caché secuencial y el cobro/devolución del cupo sí
están correctamente cableados en el código auditado.

| Requisito | Resultado |
|---|---|
| Palabra ausente sin `OPENAI_API_KEY` | Pasa por inspección; falta una regresión exacta |
| Caché de una consulta idéntica, secuencial | Pasa |
| Dos consultas idénticas simultáneas | Falla en Gradio y entre Gradio/API |
| Etapa `diccionario` sin OpenAI | Pasa |
| Topes y `_puede_pagar` | Pasa en el flujo inspeccionado |
| Toda salida del modelo marcada como IA | Falla |
| Una acepción existente sigue viniendo de Kaikki | Pasa estructuralmente |
| Alternativas dudosas sin registros descartados | Falla parcialmente |
| Texto del modelo seguro en Angular | Pasa: JSON + interpolación de Angular |
| Texto del modelo neutralizado en Gradio | Falla para Markdown |

## Hallazgos

### ALTO 1. `generado_por_ia` queda en `False` para casi todo el texto generado

**Ubicación:** `app/lexicon.py:926-947`; consumidores en
`app/ui.py:2924-2962` y `app/api.py:1191-1202`.

**Escenario concreto:** Kaikki sí contiene `mostly`, por lo que `modo_ia` es
`False`. OpenAI devuelve `traduccion`, `definicion_contextual`,
`explicacion_gramatical`, `explicacion_adaptada` y `ejemplo_simplificado`.
Todos son texto generado, pero `generado_por_ia` permanece en `False` porque
solo se activa dentro de `if modo_ia` y únicamente si `definicion_ia` no queda
vacía. La API publica los cinco textos junto a `generado_por_ia: false`; Gradio
los presenta bajo “Traducción”, “Aquí significa”, “Gramática”, “Para tu nivel”
y “Ejemplo” sin una marca de procedencia.

Hay un segundo caso: para una palabra ausente, Structured Outputs acepta una
cadena de espacios. Si `definicion_ia == " "` pero los demás campos tienen
contenido, la línea 935 la convierte en `None`, la marca queda en `False` y
Gradio muestra “No hay entrada de diccionario” seguido de explicaciones de IA
sin marcar.

La acepción mostrada como “Diccionario (Wiktionary)” sí continúa saliendo de un
objeto `Sentido`: no encontré una ruta que copie una definición libre del modelo
a `ResultadoLexico.sentido`.

**Arreglo propuesto:** hacer que la marca describa la procedencia de la
respuesta, no solo la presencia de `definicion_ia`, y marcar las secciones
contextuales en Gradio.

```diff
diff --git a/app/lexicon.py b/app/lexicon.py
@@
-        generado_por_ia = acepcion_elegida_por_ia = False
+        # Cualquier `extra` salió originalmente de OpenAI, aunque hoy venga
+        # de la caché. La marca describe procedencia, no gasto en esta llamada.
+        generado_por_ia = extra is not None
+        acepcion_elegida_por_ia = False
@@
             if modo_ia:
                 definicion_ia = (extra.get("definicion_ia") or "").strip() or None
-                generado_por_ia = definicion_ia is not None
+                if definicion_ia is None:
+                    avisos.append("OpenAI devolvió una definición vacía; no se mostró.")
diff --git a/app/ui.py b/app/ui.py
@@
     if r.definicion_contextual:
-        L.append(f"**{t['aqui']}:** {r.definicion_contextual}")
+        marca = " · IA" if getattr(r, "generado_por_ia", False) else ""
+        L.append(f"**{t['aqui']}{marca}:** {r.definicion_contextual}")
```

La API ya transporta `generado_por_ia`; el cliente Angular debe usarlo también
para rotular traducción, contexto, gramática y ejemplo, no solo la definición
de una palabra ausente.

### SERIO 2. Dos consultas simultáneas pueden pagar dos veces la misma respuesta

**Ubicación:** `app/lexicon.py:843-925`; `app/ui.py:4134-4137,4264-4275`;
`app/api.py:1133-1156`.

**Escenario concreto:** con la caché vacía, dos lectores consultan a la vez
`glimmerous` en `The glimmerous lake shone.`. Los dos hilos pueden observar
`extra is None` en `lexicon.py:858`, ambos crean `f_expl` y ambos pagan antes de
que cualquiera guarde la misma clave en `lexicon.py:925`.

La API evita la carrera entre dos peticiones Angular con `_CANDADO_LEXICO`, pero
Gradio permite ocho eventos concurrentes y sus dos enlaces a `_consultar` no
comparten `concurrency_id`. Además, el candado de la API no cubre a Gradio, de
modo que una petición de cada interfaz también puede duplicar el gasto.

La caché secuencial sí es correcta: la segunda consulta idéntica encuentra la
fila antes de construir el futuro y devuelve `llamadas_de_pago == 0`.

**Arreglo propuesto:** la exclusión debe vivir en `ConsultorLexico`, que es el
punto común de ambas interfaces, y ser por clave para no serializar palabras
distintas. Dentro del candado se vuelve a consultar la caché antes de llamar.

```diff
diff --git a/app/lexicon.py b/app/lexicon.py
@@
 import tempfile
+import threading
@@ class ConsultorLexico:
         self._sin_clave = False
+        self._candados_clave: dict[str, threading.Lock] = {}
+        self._candado_candados = threading.Lock()
+
+    def _candado_para(self, partes: tuple[str, ...]) -> threading.Lock:
+        clave = CacheLexico._clave(*partes)
+        with self._candado_candados:
+            return self._candados_clave.setdefault(clave, threading.Lock())
@@
-        pedir_explicacion = partes_clave is not None and extra is None
+        candado_respuesta = (self._candado_para(partes_clave)
+                             if partes_clave is not None else None)
+        if candado_respuesta is not None:
+            candado_respuesta.acquire()
+            # Otro hilo pudo llenar la caché mientras esperábamos.
+            extra = self.cache.obtener_respuesta(*partes_clave)
+            desde_cache = extra is not None
+        pedir_explicacion = partes_clave is not None and extra is None
@@
         if extra and pedir_explicacion:
             self.cache.guardar_respuesta(extra, self.modelo_openai, *partes_clave)
+        if candado_respuesta is not None:
+            candado_respuesta.release()
```

La liberación debe ir en un `finally`; el fragmento muestra el lugar del cambio,
no sustituye ese `try/finally`. Conviene añadir una prueba con dos hilos, un
cliente espía y una barrera: deben observarse una llamada y dos resultados.

### SERIO 3. La segunda selección vuelve a ofrecer acepciones descartadas

**Ubicación:** `app/lexicon.py:303-310,775-787,938-948`.

**Escenario concreto:** `_elegir_sentido` quita sentidos `obsolete`, `archaic`,
`dated`, `rare`, `historical` y `nonstandard`, pero ese filtrado ocurre en una
variable local. Al construir `alternativas`, `consultar` recorre otra vez
`pares`, la lista original. Por tanto, cuando el margen es dudoso, OpenAI puede
devolver exactamente una acepción que el primer filtro decidió que no debía
competir; la validación de las líneas 943-947 la acepta porque vuelve a estar en
`permitidas`.

Ejemplos comprobados en el SQLite del proyecto:

- `awful`, en `The meal was awful.`: junto a `Very bad.` se vuelve a ofrecer
  `Awe-inspiring...` (`archaic`) y `Causing fear or horror` (`dated`).
- `nice`, en `She was nice to him.`: puede volver a entrar `Silly, ignorant;
  foolish.` (`obsolete`).
- `gay`, en un texto actual: tras colapsar glosas duplicadas pueden reaparecer
  `Happy, joyful, and lively.` (`dated`) y `Fair, beautiful, pretty...`
  (`obsolete`).

Además, el corte `[:8]` conserva el orden del volcado, no cercanía contextual.
`set` tiene 49 sentidos verbales en la base y `To arrange with dishes and
cutlery, to set the table.` aparece después de los ocho primeros. Si el ranking
inicial duda en `She set the table before dinner.`, la acepción correcta puede
no llegar nunca al modelo que debía corregirlo.

**Arreglo propuesto:** aplicar una sola función de elegibilidad tanto al ranking
como a las alternativas, y seleccionar las ocho alternativas por similitud, no
por posición en el JSON.

```diff
diff --git a/app/lexicon.py b/app/lexicon.py
@@
+def _sin_marginales(candidatos):
+    normales = [(e, s) for e, s in candidatos
+                if not ({t.lower() for t in s.etiquetas}
+                        & _ETIQUETAS_MARGINALES)]
+    return normales or candidatos
+
 def _elegir_sentido(oracion, candidatos):
@@
-    normales = [(e, s) for e, s in candidatos
-                if not {t.lower() for t in s.etiquetas} & _ETIQUETAS_MARGINALES]
-    if normales:
-        candidatos = normales
+    candidatos = _sin_marginales(candidatos)
@@ class ConsultorLexico:
-        sentido, similitud, avisos_sentido = _elegir_sentido(oracion, pares)
+        pares_elegibles = _sin_marginales(pares)
+        sentido, similitud, avisos_sentido = _elegir_sentido(oracion, pares_elegibles)
@@
-            s.glosa for _, s in pares
+            s.glosa for _, s in pares_elegibles
```

Después hay que reemplazar `[:8]` por los ocho sentidos más cercanos al
contexto y conservar siempre el elegido. No propongo ampliar sin límite: palabras
como `take` (91 sentidos verbales) inflarían el prompt y el coste.

### SERIO 4. El texto del modelo entra como Markdown activo en Gradio

**Ubicación:** `app/ui.py:2926-2962`; salida final en
`app/ui.py:3200-3203`.

**Escenario concreto:** una oración de un libro contiene una instrucción hostil
y consigue que el modelo devuelva en `definicion_contextual` algo como
`![continúa](https://ejemplo.invalid/rastreo)` o un enlace Markdown. `_ficha`
concatena ese valor sin neutralizarlo y lo entrega a `gr.Markdown`. El resultado
puede alterar la estructura de la ficha, crear enlaces o intentar cargar una
imagen remota.

No afirmo una ejecución de JavaScript: Gradio documenta `sanitize_html=True`
por defecto para `Markdown`, lo que reduce el riesgo de XSS por HTML. Ese
saneamiento no convierte el texto en literal ni desactiva la sintaxis Markdown,
y el código tampoco fija el parámetro de forma explícita. La prueba agregada en
el commit solo escapa `palabra_superficie` dentro del HTML de los botones de
audio; no prueba ninguno de los campos producidos por el modelo.

**Arreglo propuesto:** neutralizar HTML y metacaracteres Markdown de todos los
campos no confiables antes de interpolarlos, y declarar el saneamiento del
componente explícitamente.

```diff
diff --git a/app/ui.py b/app/ui.py
@@
+_META_MARKDOWN = re.compile(r"([\\`*_{}\[\]()#+.!|>~-])")
+
+def _texto_markdown(valor) -> str:
+    literal = _html.escape(str(valor or ""), quote=False)
+    return _META_MARKDOWN.sub(r"\\\1", literal)
@@ def _ficha(r, idioma="es"):
-        L.append(f"**{t['trad']}:** {r.traduccion}")
+        L.append(f"**{t['trad']}:** {_texto_markdown(r.traduccion)}")
@@
-        L.append(f"**{t['aqui']}:** {r.definicion_contextual}")
+        L.append(f"**{t['aqui']}:** {_texto_markdown(r.definicion_contextual)}")
@@
-        L.append(f"**{t['gram']}:** {r.explicacion_gramatical}")
+        L.append(f"**{t['gram']}:** {_texto_markdown(r.explicacion_gramatical)}")
@@
-        L.append(f"**{t['nivel']} ({r.banda_lector}):** {r.explicacion_adaptada}")
+        L.append(f"**{t['nivel']} ({r.banda_lector}):** "
+                 f"{_texto_markdown(r.explicacion_adaptada)}")
@@
-        L.append(f"**{t['ej']}:** _{r.ejemplo_simplificado}_")
+        L.append(f"**{t['ej']}:** _{_texto_markdown(r.ejemplo_simplificado)}_")
@@ construir():
-                    ficha = gr.Markdown()
+                    ficha = gr.Markdown(sanitize_html=True)
```

Hay que aplicar el mismo helper a `definicion_ia` y a los demás datos dinámicos
que comparten esa ficha. En la API no encontré el problema equivalente:
FastAPI serializa los campos como JSON y el Angular de `5033e69` los pinta con
interpolación `{{ ... }}`, no con `[innerHTML]`; Angular escapa esa interpolación.

## Controles que pasan

### Sin clave y sin entrada de Kaikki

En `app/lexicon.py:807`, `usar_openai=False` asigna `cliente = None` sin llamar
a `_cliente`. Para una palabra ausente, `sentido is None`; las líneas 851-852
solo añaden un aviso y `pedir_explicacion` queda falso. El resultado vuelve con
`sentido=None`, `definicion_ia=None`, `generado_por_ia=False` y cero llamadas.
`app/ui.py:2949-2953` cae entonces en “No hay entrada de diccionario para esta
palabra”.

En la API, `app/api.py:1133-1137` fuerza `usar_openai=False` para la etapa
`diccionario`. En la etapa completa, `app/api.py:1151-1156` también lo fuerza
si `config.falta()`.

No hay una prueba exacta de “palabra ausente + sin clave”: `pruebas_api.py`
usa `raincoat`, que sí tiene entrada, y `pruebas_extremas.py:6557-6559`
construye el resultado manualmente. No ejecuté el blob histórico en un checkout
aislado porque el encargo prohíbe modificar el árbol y el árbol actual contiene
cambios de otra sesión. La conclusión anterior es de flujo estático, no de una
ejecución de punta a punta.

### Caché y cupos

- La clave contextual cambia a `contextual-v2` en
  `app/lexicon.py:843-847`; incluye lema, categoría, glosa, oración, banda,
  modelo, idioma y si hubo alternativas.
- La definición de una palabra ausente usa su propia versión
  `definicion-ia-v1` en `app/lexicon.py:854-857`; una consulta secuencial
  idéntica reutiliza esa fila.
- `app/api.py:1133-1144` no consume el cupo ni llama a OpenAI en la etapa
  `diccionario`.
- La etapa completa revisa el tope horario antes de consumir
  (`app/api.py:1146-1148`), llama a `_puede_pagar` una vez
  (`app/api.py:1151-1156`) y devuelve el uso cuando
  `llamadas_de_pago == 0` (`app/api.py:1160-1163`).
- Gradio aplica la misma secuencia en `app/ui.py:3112-3172`.

El problema restante es la carrera descrita en el hallazgo 2, no el camino
secuencial.

## Cobertura recomendada

1. Palabra inexistente, `usar_openai=False`, con `_cliente` sustituido por una
   función que falle si se toca; verificar la ficha completa.
2. Dos hilos con la misma clave de caché y un cliente espía sincronizado por
   barrera; exigir una sola llamada.
3. Respuesta de IA con `definicion_ia=" "` y los demás campos llenos; exigir
   marca de IA o rechazo completo.
4. Todos los campos del modelo con HTML, enlaces, imágenes y metacaracteres
   Markdown; verificar texto literal en Gradio y texto escapado por Angular.
5. `awful`, `nice`, `gay` y `set the table` con una elección dudosa; ninguna
   alternativa marginal descartada debe reaparecer y la correcta debe caber en
   el conjunto enviado al modelo.
