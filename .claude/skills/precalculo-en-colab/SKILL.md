---
name: precalculo-en-colab
description: Procesar un catálogo grande con GPU en Colab sin tirar el dinero — cuánto cuesta de verdad, por qué la GPU casi nunca es el cuello de botella, y cómo dejar el trabajo reanudable para que una sesión caída no borre horas. Úsala antes de lanzar cualquier tanda larga en Colab.
---

# Precálculo en Colab, con presupuesto

Para tandas largas sobre GPU alquilada: medir el catálogo de Gutenberg, o
cualquier cosa que sean miles de archivos por un modelo.

---

## 1. Mira el saldo ANTES de tocar nada

Panel derecho → pestaña **Recursos**. Da tres números que deciden todo:

```
Unidades informáticas disponibles: 1.9
Porcentaje de uso: aproximadamente 5.3 por hora
Los recursos de prepago pueden durar hasta 0,36 horas
```

**1,9 unidades a 5,3/hora son 21 minutos.** Enterarse de esto *después* de
montar el entorno y cargar el modelo es tirar cinco de esos minutos.

Coste aproximado por hora: A100 ≈ 11–13 unidades (aquí midió 5,3 porque el
consumo se prorratea), T4 ≈ 1,8. **Una A100 no siempre gana**: si el trabajo es
de entrada/salida, una hora de T4 hace más que veinte minutos de A100.

Y cuando el saldo se acaba, Colab avisa de que «es posible que no podamos
conservar tu entorno de ejecución actual». Da por hecho que la sesión muere sin
avisar.

---

## 2. La GPU casi nunca es el cuello de botella

**Medido en LiteraLevel, dos veces, y las dos veces era lo mismo:**

| Síntoma | Causa real |
|---|---|
| A100 al 15 % de ocupación | se llamaba al modelo **una vez por capítulo** — lotes de ~20 donde el banco de pruebas medía 256 |
| 60 libros/min = 1 s por libro | un libro son ~350 ventanas = **0,17 s de tarjeta**. El otro 80 % es esperar al FUSE de Google Drive |

La segunda es la traicionera, porque el banco de pruebas dice 2.022 ventanas/s
y es verdad — solo que mide el trozo rápido y lo presenta como si fuera el
proceso entero.

**Antes de optimizar el modelo, haz la división:** tiempo por elemento contra
tiempo de GPU por elemento. Si el cociente es 5, el problema es el disco.

### Leer por delante mientras la GPU trabaja

Leer de Drive es E/S y suelta el GIL, así que hilos sirven:

```python
HILOS_LECTURA = 8
POR_DELANTE = 32     # cola FIJA, no todas las tareas

def _en_orden(rutas):
    it = iter(rutas)
    with ThreadPoolExecutor(max_workers=HILOS_LECTURA) as pool:
        cola = deque()
        for _ in range(POR_DELANTE):
            try: cola.append(pool.submit(_leer, next(it)))
            except StopIteration: break
        while cola:
            fut = cola.popleft()
            try: cola.append(pool.submit(_leer, next(it)))
            except StopIteration: pass
            yield fut
```

Dos cosas que no son opcionales:

- **`executor.map` no vale.** Devuelve en orden, pero encola *todas* las
  tareas de golpe: con 29.516 archivos eso es intentar abrir 29.516 a la vez.
  La cola tiene que ser fija.
- **Solo el hilo principal toca CUDA.** Los hilos leen y trocean; el principal
  puntúa. Dos hilos escribiendo en la tarjeta es pedir un fallo que luego no se
  reproduce.

Eso obliga a partir la función en dos: una que lee y trocea (sin GPU) y otra
que arma el resultado (sin disco ni GPU).

---

## 3. Reanudable de verdad

La sesión **se va a caer**. El diseño tiene que asumirlo.

- **Un archivo por elemento, no.** 61.000 escrituras pequeñas en Drive es más
  lento que el cómputo. Agrupa en *shards*.
- **Tamaño del shard = cuánto estás dispuesto a perder.** 500 elementos a 60/min
  son 8 minutos en el aire. Con la sesión a punto de morir, baja a 250.
- **Reanudar leyendo lo hecho**, no llevando un contador:

```python
ya = set()
for s in glob.glob(PERFILES + '/perfiles_*.jsonl'):
    for linea in open(s, encoding='utf-8'):
        try: ya.add(json.loads(linea)['id'])
        except Exception: pass
pendientes = [r for r in sorted(glob.glob(TEXTOS + '/*.txt'))
              if int(os.path.basename(r)[2:-4]) not in ya]
```

Un contador miente en cuanto algo se cae a mitad; el conjunto de ids no.

- **`try/finally` con volcado en el `finally`.** Si te interrumpen, lo que hay
  en el buffer se guarda igual.
- **Un `print` cada 100** con velocidad y errores. Sin eso no sabes si va bien
  hasta que termina, y a veces no termina.

---

## 4. Separa lo que necesita GPU de lo que no

**Descargar no necesita GPU.** Analizar sí. Si quedan pocas unidades, gasta la
GPU en lo único que solo ella hace, y deja la descarga para un entorno de CPU
gratuito. En LiteraLevel había 29.516 libros ya bajados esperando: trabajo de
sobra para la GPU sin tocar la red.

---

## 5. Montar Drive desde Claude Code

`drive.mount()` abre un diálogo modal en la pestaña de Colab y **la celda se
queda colgada** hasta que alguien pulsa. Desde aquí se resuelve con
`chrome-devtools`:

1. `take_snapshot` de la pestaña de Colab → botón «Conectar con Google Drive»
2. `click` → se abre una pestaña nueva de `accounts.google.com`
3. `take_snapshot` de **esa** pestaña → **comprueba la cuenta**: el Colab Pro
   está en `xxxxxx@xxxxxx.com`, no en la otra
4. `click` en «Continuar», dos veces (elegir cuenta y confirmar permisos)

El MCP de Colab devuelve **timeout a los 90 s** en cualquier celda larga. Eso
**no** significa que haya fallado: la celda sigue corriendo. Comprueba con
`get_cells(..., includeOutputs=True)`, que devuelve la salida acumulada.

Y las celdas se ejecutan **en cola**, en un solo kernel: una celda de
diagnóstico lanzada mientras corre la tanda no se ejecuta hasta que la tanda
termina.

---

## 6. Escanear una carpeta de Drive es lento

`os.scandir` sobre 31.974 entradas tardó **109 segundos** con el montaje
recién hecho (5 s con la caché caliente). No lo pongas dentro de un bucle: en
una versión anterior se listaba el directorio cada 200 libros y se perdieron
más de dos horas en listados.

---

## 7. El catálogo, para escribirlo bien en el documento

Cuando reportes el coste, distingue dos cifras y di cuál es cuál:

- **Rendimiento de la GPU** (2.022 ventanas/s): mide la tarjeta, y es real.
- **Rendimiento de extremo a extremo** (60 libros/min): mide el proceso, e
  incluye leer, trocear y escribir.

Publicar la primera como si fuera el coste del catálogo es lo que convierte
«17 horas» en «entre 3 y 5», y una auditoría lo va a encontrar.
