# Desplegar LiteraLevel (punto 6)

Todo lo que sigue está **preparado y verificado en local**. Lo único que falta
es elegir plataforma y ejecutar.

## Lo que hay que colocar

| Qué | Tamaño | Dónde va |
|---|---|---|
| Código (`app/`, `main.py`, pruebas) | ~120 KB | el repositorio del despliegue |
| `catalogo_recomendaciones.csv` | 1 MB | el repositorio del despliegue |
| `modelo_v4/` | **317 MB** | fuera: repo de modelo, montado de solo lectura |
| `kaikki_diccionario.db` | **232 MB** | fuera: repo de datos, montado de solo lectura |

Los 549 MB de datos **no van en el repositorio** y están en `.gitignore`. La app
los localiza por variable de entorno, y eso ya está probado moviéndolos fuera:

```
LITERALEVEL_MODELO       -> carpeta del modelo v4   (por defecto ./modelo_v4)
LITERALEVEL_DICCIONARIO  -> SQLite de Kaikki        (por defecto ./kaikki_diccionario.db)
OPENAI_API_KEY           -> secreto; sin ella la app degrada, no falla
```

## Consumo medido, no estimado

**~1,05 GB de RSS** con el modelo y los embeddings del catálogo cargados; con
spaCy y el diccionario encima, pico realista de **1,2–1,5 GB**. Esto **descarta**
Render free, Koyeb free y cualquier plan de 512 MB. No lo intentes.

## Opción A — Hugging Face PRO, 9 $ un mes

La más corta: Gradio nativo, cero reescritura, 16 GB de RAM.

**Ojo, esto cambió a mediados de 2026** y casi toda la documentación de terceros
sigue desactualizada. La doc oficial del Hub dice literalmente:

> *"Static Spaces are free for everyone. Gradio and Docker Spaces run on compute
> and require a paid plan to create: PRO for personal accounts."*

Pasos:

1. Suscribirse a PRO y crear un Space **Gradio**, hardware CPU Basic
   (2 vCPU / 16 GB / 50 GB efímeros, sin coste por hora).
2. Subir modelo y diccionario como repos aparte: `python desplegar_datos.py`.
3. En el README del Space, el front matter tiene que declarar el punto de
   entrada, porque el nombre por defecto (`app.py`) chocaría con la carpeta
   `app/`:

   ```yaml
   ---
   title: LiteraLevel
   emoji: 🧊
   colorFrom: blue
   colorTo: indigo
   sdk: gradio
   sdk_version: 6.26.0
   app_file: main.py
   pinned: false
   ---
   ```
4. `OPENAI_API_KEY` como **Secret** del Space. `app/config.py` ya lee
   `os.environ` antes que el archivo, así que no hay que tocar código.
5. Ajustar `LITERALEVEL_MODELO` y `LITERALEVEL_DICCIONARIO` a donde queden
   montados los datos.

Contra: en hardware gratuito el Space **se duerme por inactividad** y el primer
visitante paga un arranque frío de decenas de segundos (torch + 317 MB). Para
una evaluación es asumible; si molesta, un mes de CPU Upgrade.

## Opción B — ZeroGPU, gratis

La doc del Hub deja una excepción: una cuenta personal gratuita en buen estado
puede alojar **hasta 2 Spaces Gradio sobre ZeroGPU**.

Pero léelo antes de ilusionarte: ZeroGPU está pensado para cargas **de GPU**, y
un distilroberta sobre 8 bloques de 250 palabras no necesita GPU. La cuota es de
**5 minutos de GPU al día**, y su documentación **desaconseja la carga perezosa**
— que es justo la regla de este proyecto para que la app abra en el acto. Si
obedeces a ZeroGPU rompes eso.

Viable si los 9 $ son un problema real. No es el camino limpio.

## Opción C — Modal, gratis de verdad

**30 $/mes de créditos renovables, sin tarjeta.** Escala a cero, factura por
segundo, URL estable con `modal deploy`. Con un profesor evaluando no se gastan
ni de lejos. Gradio se monta como app ASGI y los 549 MB van en un Volume.

Coste: una tarde de ingeniería y aprender su modelo mental. Es el camino más
largo de los tres, y el único sin factura.

## Lo que ya no hace falta resolver

- `main.py` en la raíz mete `app/` en `sys.path` y expone `demo`. **No lo
  renombres a `app.py`.**
- Las rutas del modelo y del diccionario son configurables, y está comprobado
  con los datos fuera del repositorio.
- `requirements.txt` instala `en_core_web_sm` por URL directa, porque en un
  despliegue no hay quien ejecute `python -m spacy download`.
- Las cachés de `~/.literalevel/` (léxico, audio, cuaderno, marcapáginas) son
  disco efímero en un Space: se borran en cada reinicio. Es aceptable porque son
  caché, pero la primera consulta tras cada despertar irá lenta. Si quieres que
  el cuaderno de palabras sobreviva, hace falta almacenamiento persistente.
