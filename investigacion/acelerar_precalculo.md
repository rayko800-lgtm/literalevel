# Cómo acelerar el precálculo masivo

**Encargo 3.** *«28.535 libros bajados de 61.642, 2.458 medidos, el análisis
lleva doce horas parado y Miguel pregunta si se puede descargar desde varios
sitios a la vez.»*

No toco nada. Esto es el diagnóstico y el plan, con las órdenes exactas.

> **Qué está medido y qué no.** Lo marcado **[medido]** son cifras que ya
> existen en este repositorio (`informe_velocidad.md`, `investigacion/transformer_v5.md`)
> o que Miguel midió hoy contra Drive. Lo marcado **[comprobado hoy]** lo
> verifiqué yo contra el servidor real, con enlace. Lo marcado **[aritmética]**
> es una cuenta mía sobre cifras medidas, y enseño la cuenta. Lo marcado
> **[no verificado]** es una hipótesis con una prueba de dos minutos al lado.
> No hay ninguna cifra de referencia inventada: donde no encontré medición
> publicada, lo digo.

---

## Resumen: la conclusión antes del razonamiento

1. **La sospecha de Miguel es correcta en el fondo, pero incompleta.** La E/S de
   Drive es un problema real y grave. Pero hay un segundo cuello de botella,
   más barato de arreglar y probablemente mayor: **el precálculo puntúa capítulo
   a capítulo, y los capítulos tienen entre 7 y 31 ventanas.** La A100 está
   recibiendo lotes de veinte ventanas cuando el propio cuaderno mide su
   velocidad con lotes de 256. **La cifra de 2.022 ventanas/s se midió en el
   camino bueno y el precálculo corre por el malo.**

2. **La A100 va al 15 % de su capacidad; la GTX 1650 SUPER de casa iba al 59 %**
   [aritmética, §3.1]. Es decir: la tarjeta cara está *hambrienta*, no lenta.
   No hay nada que arreglar en el modelo.

3. **La descarga fichero a fichero sobra entera.** Project Gutenberg publica
   **un único tar con todos los `.txt`, actualizado semanalmente**:
   `txt-files.tar.zip`, **11.278.856.242 bytes, del 06-sep-2026 23:13**
   [comprobado hoy]. Una petición HTTP en lugar de 33.000. Y sí, además hay
   rsync oficial, con el comando exacto en §2.2.

4. **Lo primero que haría no es tocar el modelo ni cambiar de GPU.** Es medir
   diez minutos para repartir el reloj entre leer / tokenizar / GPU, y luego
   aplanar el lote. Las dos cosas juntas son media jornada y no mueven ni un
   decimal de ningún resultado — eso está demostrado en `informe_velocidad.md`
   §3.b, no es una suposición.

---

## 1. Dónde se va el tiempo, de verdad

### 1.1 Lo que dicen las cifras de hoy

| Dato | Valor | Origen |
|---|---|---|
| Libros descargados | 28.535 de 61.642 (46 %) | medido hoy |
| Libros analizados | 2.458 (6 shards) | medido hoy |
| Análisis parado desde hace | 11,7 h | medido hoy |
| `os.scandir` sobre 28.535 ficheros en Drive | **98 s** | medido hoy |
| Inferencia en A100, fp16, lote 256 | **2.022 ventanas/s** | medido |
| Inferencia en GTX 1650 SUPER, fp32, lote 128 | 112,7 ventanas/s | medido |
| Inferencia en CPU (Ryzen 2600, 12 hilos, lote 64) | 8,27 ventanas/s | medido |

Un dato que conviene dejar dicho antes de seguir: **la estimación de «6,3 horas
de A100» para el catálogo entero no cuadra con 2.022 ventanas/s.**

> 61.642 libros × 350 ventanas/libro ÷ 2.022 v/s ÷ 3.600 = **2,96 h** [aritmética]

Para que salgan 6,3 h hacen falta o **950 ventanas/s** o **745 ventanas por
libro**. Cualquiera de las dos posibilidades importa, así que conviene rehacer
la cuenta con el dato real, que ya está en casa: los seis shards traen el campo
`ventanas` de 2.458 libros.

```python
import json, glob, statistics
v = [json.loads(l)["ventanas"]
     for f in glob.glob("/content/drive/MyDrive/literalevel_bigdata/perfiles/perfiles_*.jsonl")
     for l in open(f, encoding="utf-8")]
print(len(v), "libros | media", statistics.mean(v), "| mediana", statistics.median(v))
```

Con eso, la estimación deja de ser un supuesto (`VENTANAS_POR_LIBRO = 350`,
`colab_precalculo.py` celda 9) y pasa a ser una medición. **Es la primera línea
de código que escribiría.**

### 1.2 El hallazgo principal: la A100 recibe lotes de veinte

En `colab_precalculo.py`, `perfil_de_libro` hace esto:

```python
for n, (i, c) in enumerate(ficha.capitulos_de_cuerpo(libro), 1):
    vs = puntuar_lote(scoring.fixed_blocks(ficha.sin_licencia(c.texto), cap=10**9))
```

**Una llamada a la GPU por capítulo.** `puntuar_lote` trocea internamente de 256
en 256, pero solo si le llegan 256; si le llegan 14, el lote es 14.

Y sabemos cuántas ventanas tiene un capítulo, porque está medido en
`informe_velocidad.md` §1:

> «el capítulo más grande de *Crime and Punishment* son 31 ventanas y el más
> grande de *War and Peace*, 17. Es decir, el tamaño de lote real hoy es de ~20
> ventanas en C&P y ~7 en W&P.»

*War and Peace* son 2.459 ventanas repartidas en **362 capítulos**: 362 llamadas
al modelo con una media de 6,8 ventanas cada una, y **362 sincronizaciones
GPU→CPU**, porque `puntuar_lote` termina en `.float().cpu().numpy()`.

Mientras tanto, la celda 9 —la que produjo el 2.022 v/s— hace:

```python
puntuar_lote(bloques)      # bloques son 300 ventanas seguidas -> lotes de 256 y 44
```

**El benchmark mide el camino rápido y el precálculo corre por el lento.** Esto
no es una hipótesis sobre el hardware: es leer las dos celdas.

### 1.3 Y la corrección es gratis y demostrablemente exacta

Reagrupar ventanas **no puede** cambiar un número, y no es una opinión:

> «las mismas 300 ventanas puntuadas de una en una (lote 1) y en un solo lote de
> 300 salen **MAE = 0,000000, máx = 0,000000, 300/300 valores idénticos bit a
> bit**. Es lo esperado, porque todas las ventanas ocupan exactamente 256 tokens
> y no hay padding.» — `informe_velocidad.md` §3.b [medido]

El 100 % de las ventanas llega a 256 tokens tras truncar (200 ventanas medidas,
`informe_velocidad.md`; confirmado en `investigacion/transformer_v5.md` §1.1).
**Todos los tensores son rectangulares 256 de ancho.** Por eso el agrupado es
libre: no hay padding que cambie el resultado.

### 1.4 ¿Cuánto se gana? La aritmética de la ocupación

`distilroberta-base` con la `config.json` de `modelo_v4/`: 6 capas, `hidden 768`,
`intermediate 3072`, `MAX_LENGTH 256`.

Parámetros del cuerpo, por capa: `4·768² (QKVO) + 2·768·3072 (FFN) = 7.077.888`.
Por seis capas, **42.467.328**.

> FLOPs de matmul por token = 2 × 42.467.328 = **84,93 MFLOP**
> Atención (QKᵀ y AV) por token = 6 capas × 2 × 2 × 256 × 768 = **4,72 MFLOP**
> **Total ≈ 89,65 MFLOP/token → 22,95 GFLOP por ventana de 256 tokens** [aritmética]

Y de ahí sale el número que lo explica todo:

| GPU | Precisión | Ventanas/s | TFLOP/s reales | Pico teórico | **Ocupación** |
|---|---|---|---|---|---|
| A100 | fp16 | 2.022 | 46,4 | **312** (FP16 Tensor Core, [ficha NVIDIA](https://www.nvidia.com/en-us/data-center/a100/)) | **14,9 %** |
| GTX 1650 SUPER | fp32 | 112,7 | 2,59 | ~4,4 (fp32, spec habitual de TU116) [no verificado] | **~59 %** |

**La A100 rinde 17,9× lo que la tarjeta de casa, teniendo 70× su pico.** Una
tarjeta de 200 € va al 59 % de ocupación y la A100 al 15 %. Eso no es un
problema de modelo ni de precisión: es una GPU esperando a que le den trabajo.

Los tres sospechosos de ese 85 % perdido, en orden:

1. **Lotes de 7–31 ventanas** en lugar de 256 (§1.2). A lote pequeño manda el
   coste fijo de lanzar ~100 kernels por *forward* en modo *eager*, no el
   cómputo.
2. **La tokenización, que ahora pesa.** En CPU era el 0,4 % del reloj
   (0,6 s de 156,3 s para 840 ventanas, `informe_velocidad.md` §2) y por eso el
   informe concluyó, con razón para aquella máquina, que no era el problema.
   Pero ese 0,6 s **no baja al cambiar de GPU**, y en A100 esas mismas 840
   ventanas se computan en 0,42 s [aritmética]. **Lo que en CPU era ruido, en
   A100 es más de la mitad del reloj** — y `puntuar_lote` la ejecuta *en serie*
   con el *forward*, no solapada.
3. **La lectura de Drive**, entre libro y libro, también en serie (§1.5).

### 1.5 La sospecha de Drive: confirmada como problema, no como *el* problema

**Lo que está medido:** `os.scandir` sobre 28.535 ficheros = **98 s**, o
**3,43 ms por entrada, solo para el listado**. Eso ya basta para condenar dos
cosas del código actual:

**a) Un `glob` completo dentro del bucle de descarga.** En la celda 6b:

```python
if n % 200 == 0:
    v = n / (time.time() - inicio)
    queda = (len(pendientes) - len(list(TEXTOS.glob('*.txt')))) / v / 3600
```

`TEXTOS.glob('*.txt')` **es el `scandir` de 98 s**, y se ejecuta **cada 200
descargas**, solo para imprimir una estimación. Y empeora según crece el
directorio: a 61.642 ficheros serán unos 210 s. Con seis hilos bajando a unos
pocos ficheros por segundo, **la línea de progreso cuesta tanto como las
descargas que informa.** Es una línea de código.

**b) `_pendientes_reales` hace 61.642 `Path.exists()` sobre Drive** antes de
empezar. Cada uno es un `stat` a través de FUSE. A 3,4 ms serían 3,5 minutos; si
un `stat` no cacheado cuesta más —y lo normal es que cueste más que una entrada
de listado amortizada—, son horas antes de bajar el primer fichero. La
sustitución correcta es un solo `scandir` a un `set`:

```python
ya = {e.name for e in os.scandir(TEXTOS)}          # un listado, no 61.642 stats
cola = [n for n in pendientes if f"pg{n}.txt" not in ya]
```

**Lo que NO está medido y no voy a inventar:** cuánto cuesta *abrir y leer* un
fichero pequeño desde Drive FUSE frente a `/content`. Busqué medición publicada
y no la hay con números sólidos:

- El benchmark de [Cremonesi (2020)](https://sharkovsky.github.io/2020/09/18/colab-io-bench.html)
  compara Drive, GCSFuse y copia manual, pero el autor **advierte explícitamente
  contra tomar sus números como absolutos** y solo publica una cifra cerrada:
  *«The second read is more than 1000x faster for GDrive»* — es decir, mide
  caché, no E/S en frío.
- [colabtools#1691](https://github.com/googlecolab/colabtools/issues/1691)
  reporta caídas de **300 muestras/s a 1 muestra/s** leyendo ficheros pequeños
  de Drive, sin respuesta de Google y sin resolver.
- [FastColabCopy](https://github.com/L0garithmic/FastColabCopy) afirma **10–50×**
  copiando muchos ficheros pequeños con 15–40 hilos. Es la afirmación del autor
  del proyecto, no un benchmark independiente.
- Riesgo adicional documentado:
  [colabtools#1607](https://github.com/googlecolab/colabtools/issues/1607) —
  copiar mucho desde Drive montado dispara *«A Google Drive quota has been
  exceeded»* y un error de E/S. Con 61.642 aperturas de fichero eso no es
  hipotético.
- Y la [FAQ oficial de Colab](https://research.google.com/colaboratory/faq.html)
  avisa de que las operaciones de Drive **fallan por timeout** cuando un
  directorio tiene demasiadas entradas.

**Nada de eso es una cifra utilizable, así que la medición hay que hacerla.**
Cuesta dos minutos y zanja la discusión:

```python
import os, time, random, shutil
rutas = random.sample([e.path for e in os.scandir(TEXTOS)], 200)

t = time.time()
n = sum(len(open(r, "rb").read()) for r in rutas)
t_drive = time.time() - t

os.makedirs("/content/muestra", exist_ok=True)
for r in rutas: shutil.copy(r, "/content/muestra/")
locales = [e.path for e in os.scandir("/content/muestra")]
t = time.time()
n2 = sum(len(open(r, "rb").read()) for r in locales)
t_local = time.time() - t

print(f"Drive : {t_drive:6.2f} s  ({200/t_drive:7.1f} fich/s, {n/t_drive/1e6:.1f} MB/s)")
print(f"local : {t_local:6.2f} s  ({200/t_local:7.1f} fich/s, {n2/t_local/1e6:.1f} MB/s)")
print(f"factor: {t_drive/t_local:.1f}x")
```

**Lo que sí puedo afirmar sin medir**, porque es estructural: un `open()` en
Drive FUSE que no está en caché es **una ida y vuelta HTTPS a la API de Drive**,
mientras que en `/content` es un `read()` sobre un disco persistente de GCE, y
con los **83 GB de RAM del entorno A100** [no verificado, comprobar con
`free -g`] los 20 GB de texto caben enteros en caché de página tras la primera
lectura. La diferencia no puede ser pequeña. Y hay una consecuencia de diseño
que no depende de cuál sea el factor exacto:

> **Ningún fichero pequeño debería vivir en Drive.** Drive es excelente
> guardando pocos objetos grandes y pésimo guardando muchos pequeños. Los
> `.txt` sueltos hay que sacarlos de ahí; los shards de 500 libros ya están
> bien y no se tocan.

---

## 2. Frente 1 — la descarga

### 2.1 La respuesta corta a la pregunta de Miguel

Sí, se puede descargar desde varios sitios a la vez y sí, suma de verdad: los
espejos son máquinas distintas en redes distintas, no cuotas de un mismo
servidor. **Pero es la pregunta equivocada**, por dos razones:

1. **Existe un solo fichero con todo el texto.** No hay que repartir 33.000
   descargas entre nadie: hay que hacer **una**.
2. **Es muy probable que el espejo no sea el cuello de botella.** Cada
   `descargar()` hace un `GET` (rápido) y luego `destino.write_bytes()` **sobre
   Drive FUSE**, que es una subida por la API de Drive. Añadir hilos contra el
   espejo no arregla eso; solo pone más hilos a esperar a Drive. La prueba que
   lo separa es de tres líneas: bajar 200 ficheros a `/content` y 200 a Drive, y
   comparar. **[no verificado]**

### 2.2 El tar semanal con todos los `.txt` — la palanca grande

Project Gutenberg publica, en su página de
[catálogos sin conexión](https://www.gutenberg.org/ebooks/offline_catalogs.html),
*«A zipped tar file of all .txt files, updated weekly»*. Verifiqué el fichero en
el índice del espejo pglaf **hoy**:

| Fichero | Bytes | Modificado |
|---|---|---|
| `txt-files.tar.zip` | **11.278.856.242** | **06-sep-2026 23:13** |
| `pg_catalog.csv` | 21.205.940 | 06-sep-2026 21:29 |
| `rdf-files.tar.bz2` | 126.592.486 | 07-sep-2026 14:42 |

Fuente: [`https://gutenberg.pglaf.org/cache/generated/feeds/`](https://gutenberg.pglaf.org/cache/generated/feeds/)
[comprobado hoy].

Son **11,28 GB en una sola petición HTTP**, contra las ~33.000 que faltan. A un
ritmo modesto de 20 MB/s son **~9 minutos**; si el espejo da 100 MB/s —se
anuncia como *high-speed* en [MIRRORS.ALL](https://www.gutenberg.org/MIRRORS.ALL)—
son menos de dos. **[estimado: no he podido medir el ancho de banda
Colab↔pglaf]**

```bash
# 1. Al disco LOCAL del runtime, nunca a Drive.
mkdir -p /content/pg
curl -L --retry 5 -C - -o /content/pg/txt-files.tar.zip \
     https://gutenberg.pglaf.org/cache/generated/feeds/txt-files.tar.zip

# 2. Una copia a Drive, UN objeto grande, para no volver a bajarlo nunca.
cp /content/pg/txt-files.tar.zip /content/drive/MyDrive/literalevel_bigdata/
```

**Antes de extraer, mirar qué hay dentro.** No he podido verificar la
disposición interna del tar (si es `1/3/4/1342/1342-0.txt` o plano), y no la voy
a suponer. Se resuelve en segundos sin descargarlo entero:

```bash
curl -sL https://gutenberg.pglaf.org/cache/generated/feeds/txt-files.tar.zip \
  | funzip | tar -tvf - | head -30
```

(`funzip` viene con el paquete `unzip`, que Colab trae; descomprime el primer
miembro de un zip leído por tubería. Si faltara: `apt-get -qq install unzip`.)

Y con la disposición conocida, la extracción **solo de lo que interesa**:

```python
# Extrae únicamente los .txt UTF-8 de los ids en inglés del catálogo.
import tarfile, zipfile, io, pathlib
ids = set(int(i) for i in en["Text#"])            # 61.642 ids del catálogo
destino = pathlib.Path("/content/gutenberg_txt"); destino.mkdir(exist_ok=True)

z = zipfile.ZipFile("/content/pg/txt-files.tar.zip")
with z.open(z.namelist()[0]) as flujo:            # el .tar de dentro
    with tarfile.open(fileobj=flujo, mode="r|") as tar:   # "r|" = flujo, no seek
        for m in tar:
            if not m.isfile() or not m.name.endswith(".txt"):
                continue
            base = m.name.rsplit("/", 1)[-1]
            num = base.split("-")[0].removesuffix(".txt")
            if not num.isdigit() or int(num) not in ids:
                continue
            datos = tar.extractfile(m).read()
            if len(datos) > 2000:
                (destino / f"pg{int(num)}.txt").write_bytes(datos)
```

Es un solo recorrido secuencial. **[estimado: ~10 min de CPU para descomprimir
~35 GB y escribir 61.000 ficheros en disco local.]**

**Lo que no es.** El tar trae **todos los idiomas y las tres variantes de
codificación** (`-0.txt` UTF-8, `.txt` ASCII, `-8.txt` Latin-1). Por eso el
filtro de arriba; si un libro tiene varias variantes hay que quedarse con la
UTF-8, que es la que baja hoy `_rutas_posibles`.

### 2.3 Rsync — sí existe, y es la vía sancionada para copias incrementales

La [guía oficial de mirroring](https://www.gutenberg.org/help/mirroring.html) da
los comandos literalmente. Módulos: `gutenberg` (colección principal) y
`gutenberg-epub` (generados). Servidores: `rsync.ibiblio.org` y
`gutenberg.pglaf.org`.

```bash
# Lo que dice la guía, literal (la colección entera: ~6 millones de ficheros)
rsync -av --del gutenberg.pglaf.org::gutenberg /var/www/gutenberg
```

Eso **no** es lo que queremos: son ~2 TB con audio, HTML, imágenes y versiones
antiguas. Lo que queremos es solo texto, y hay dos formas.

**(a) Con filtros.** Precedente publicado y funcionando —
[Robotic Ape, 2018](https://roboticape.com/2018/06/26/getting-all-the-books/) —
que se trajo *todos* los textos comprimidos de *todos* los idiomas en **~8 GB**:

```bash
rsync -avm --max-size=10m \
  --include="*/" --exclude="*-*.zip" --exclude="*/old/*" \
  --include="*.zip" --exclude="*" \
  rsync.mirrorservice.org::gutenberg.org ~/data/gutenberg
```

Adaptado a nuestro caso (`.txt` en UTF-8, no zips ASCII), quedaría:

```bash
rsync -av --prune-empty-dirs --max-size=10m \
  --exclude='old/***' \
  --include='*/' --include='*-0.txt' --exclude='*' \
  gutenberg.pglaf.org::gutenberg/ /content/gutenberg_txt_raw/
```

**Aviso importante:** con filtros, rsync tiene que **recorrer los 6 millones de
entradas del servidor** aunque transfiera pocas. El listado inicial tarda —
minutos, no segundos — y no lo he cronometrado **[no verificado]**.

**(b) Con lista explícita, que es mejor para nosotros**, porque sabemos
exactamente qué ids queremos y evitamos el recorrido completo:

```python
# Genera la lista de rutas relativas tal y como las guarda el espejo
with open("/content/lista.txt", "w") as f:
    for n in sorted(ids):
        d = str(n)
        carpeta = "/".join(d[:-1]) if len(d) > 1 else "0"
        f.write(f"{carpeta}/{d}/{d}-0.txt\n")
```

```bash
rsync -av --files-from=/content/lista.txt --ignore-missing-args \
  gutenberg.pglaf.org::gutenberg/ /content/gutenberg_txt/
```

`--ignore-missing-args` es imprescindible: no todos los libros tienen variante
`-0.txt`. Para los que fallen, se repite con `{d}.txt` y `{d}-8.txt`.

**Cuándo usar rsync y cuándo el tar.** El tar es más rápido de traer y es lo que
haría hoy. Rsync es lo correcto **después**, para actualizaciones incrementales
(`--del` no; solo traer lo nuevo) sin volver a bajar 11 GB. También es la vía si
alguien no se fía del tar y quiere ficheros exactamente como los sirve el
espejo.

### 2.4 Espejos oficiales

De [MIRRORS.ALL](https://www.gutenberg.org/MIRRORS.ALL) [comprobado hoy]:

| Servidor | País | Protocolos | Nota de PG |
|---|---|---|---|
| `gutenberg.pglaf.org` | EE. UU. | HTTPS, **rsync** | *«High-speed mirror. Includes cache/generated files»* |
| `rsync.ibiblio.org` | EE. UU. | **rsync** | *«Main Project Gutenberg rsync Site»* |
| `mirrorservice.org` | Reino Unido | HTTP, FTP, **rsync** | espejo del UK Mirror Service |
| `mirror.cs.odu.edu` | EE. UU. | HTTPS | *«High speed connection»*, con generados |
| `mirror.csclub.uwaterloo.ca` | Canadá | HTTP | Universidad de Waterloo |
| `mirrors.xmission.com` | EE. UU. | HTTP, FTP | ISP |
| `www.gutenberg.org` | EE. UU. | HTTPS | sitio principal — **no automatizar** |

**¿Repartir entre varios acelera o solo reparte la misma cuota?** Acelera de
verdad: son organizaciones y redes independientes (ibiblio en Chapel Hill,
pglaf, el UK Mirror Service en Kent, Waterloo, ODU, XMission), sin cuota común.
El código actual ya lista dos, pero en `ESPEJOS` los usa **como reserva, no en
paralelo**: solo va al segundo si el primero falla. Repartir de verdad sería
`espejo = ESPEJOS[n % len(ESPEJOS)]`. **Dicho lo cual, con el tar de §2.2 esta
optimización sobra entera, y por eso no la recomiendo.**

### 2.5 La política de Gutenberg, y cuántos hilos son aceptables

Esto importa y conviene tenerlo por escrito. La
[política de acceso robótico](https://www.gutenberg.org/policy/robot_access.html)
dice, literalmente:

> *«The Project Gutenberg website is intended for human users only. Any perceived
> use of automated tools to access the Project Gutenberg website will result in a
> temporary or permanent block of your IP address.»*

Y admite exactamente tres excepciones: el punto de entrada `/robot/harvest` con
`wget`, **montar un espejo privado**, y leer el catálogo en formato legible por
máquina. El ejemplo de `wget` que publican lleva **`-w 2`**, o sea **una
petición cada dos segundos** contra el sitio principal. La página de
[bloqueos](https://block.pglaf.org/) confirma que hay un límite de velocidad
automático y que uno de los motivos de bloqueo es *«a program is attempting to
harvest the contents»*.

**Dónde estamos hoy.** El código va al espejo `gutenberg.pglaf.org`, que es
justamente lo que PG recomienda («*download them from one of the mirrors, not
from the main site*»), y eso está bien hecho y está bien razonado en el
comentario de la celda 6. Pero:

- **Seis hilos con `PAUSA = 0,4` son hasta 15 peticiones/s.** Frente al `-w 2`
  del ejemplo oficial, son **30× más rápido**. Para el sitio principal sería
  motivo de bloqueo seguro. Para un espejo no hay número publicado, así que
  estamos en terreno sin norma escrita **[no verificado: no existe límite de
  concurrencia documentado para los espejos]**.
- **La celda 5 baja `pg_catalog.csv` de `www.gutenberg.org`**, que es
  precisamente el host que bloquea. Es una sola petición y no va a pasar nada,
  pero el mismo fichero está en el espejo y no cuesta nada corregirlo:
  `https://gutenberg.pglaf.org/cache/generated/feeds/pg_catalog.csv`.

**La respuesta honesta a «no quiero que nos veten»:** deja de hacer 33.000
peticiones. Una descarga del tar (§2.2) o un `rsync` (§2.3) son **las dos vías
que PG documenta como correctas**, y ninguna de las dos puede parecer un
*scraper*. Es el argumento más fuerte a favor del cambio, por encima incluso de
la velocidad.

### 2.6 Alternativas prefabricadas, y por qué las pongo en tercer lugar

| Fuente | Contenido | Tamaño | Veredicto |
|---|---|---|---|
| [`manu/project_gutenberg`](https://huggingface.co/datasets/manu/project_gutenberg) | **61.340 libros en inglés**, texto completo con cabecera y pie | **12.236.097.193 B** en 52 parquets | **La alternativa seria.** Coincide casi exactamente con los 61.642 objetivo |
| [`sedthh/gutenberg_english`](https://huggingface.co/datasets/sedthh/gutenberg_english) | 48.284 libros, texto ya limpio de cabeceras, con metadatos | 10.748.877.194 B | Menos cobertura (78 %) y **limpieza ajena**: chocaría con `ficha.sin_licencia` |
| [SPGC (Zenodo)](https://zenodo.org/records/2422561) | 55.905 libros de 2018, **tokens y recuentos, no prosa** | 3,6–65 GB | **Descartado.** No hay texto corrido que darle a un transformer |
| Imágenes ISO / CD-DVD | — | — | **No existen ya**; la página de catálogos sin conexión no las menciona y remite a [Kiwix](https://wiki.kiwix.org/wiki/Content) |

Cifras de filas y bytes tomadas de la API de HF
([`size?dataset=manu/project_gutenberg`](https://datasets-server.huggingface.co/size?dataset=manu/project_gutenberg))
[comprobado hoy].

`manu/project_gutenberg` es tentador — 12,2 GB en 52 ficheros grandes, y leer
parquet secuencialmente elimina la E/S por fichero *de raíz*, que es justo el
problema. Comando:

```bash
pip -q install "huggingface_hub[cli]"
hf download manu/project_gutenberg --repo-type dataset \
   --include "data/en-*" --local-dir /content/pg_hf
```

**Por qué aun así lo pongo detrás del tar oficial:** es una instantánea de un
tercero, sin fecha declarada, con 302 libros menos que el catálogo, y no
sabemos de qué variante de codificación salió cada texto. El precálculo produce
las cifras que va a enseñar la app; que el texto medido coincida con el que PG
sirve hoy no es un detalle. **Si se usa, hay que verificarlo**, y la
verificación es barata porque ya hay 28.535 ficheros en Drive con los que
comparar:

```python
# Coge 200 libros que ya estén en Drive y compara byte a byte con la fuente nueva.
import random, hashlib, os
comunes = random.sample([e.name for e in os.scandir(TEXTOS)], 200)
iguales = sum(hashlib.md5(open(TEXTOS/n,'rb').read()).hexdigest()
              == hashlib.md5(open(f"/content/gutenberg_txt/{n}",'rb').read()).hexdigest()
              for n in comunes if os.path.exists(f"/content/gutenberg_txt/{n}"))
print(f"{iguales}/200 idénticos")
```

Esa misma comprobación vale para el tar de §2.2, y ahí espero 200/200.

---

## 3. Frente 2 — el análisis

Por orden de ganancia esperada partida por esfuerzo.

### 3.1 Aplanar el lote: una sola cola de ventanas por libro

**Es la palanca grande, es gratis en exactitud y es media mañana de trabajo.**

Hoy: una llamada a GPU por capítulo, lotes de 7 a 31 ventanas, una sincronización
por capítulo. Lo correcto: juntar todas las ventanas del libro, puntuarlas en
lotes fijos de 256, y repartir los resultados de vuelta por capítulo. Aritmética
idéntica, porque la media por capítulo se calcula después, sobre los mismos
valores.

```python
def perfil_de_libro(ruta):
    libro = reader.cargar(str(ruta))
    tramos, cola = [], []                       # tramos = (n, indice, cap, ini, fin)
    for n, (i, c) in enumerate(ficha.capitulos_de_cuerpo(libro), 1):
        bs = scoring.fixed_blocks(ficha.sin_licencia(c.texto), cap=10**9)
        if not bs:
            continue
        tramos.append((n, i, c, len(cola), len(cola) + len(bs)))
        cola.extend(bs)
    if not cola:
        return None

    vs_todas = puntuar_lote(cola, tam=256)      # UNA cola, lotes llenos

    filas, todas = [], vs_todas
    for n, i, c, a, b in tramos:
        vs = vs_todas[a:b]
        filas.append({"capitulo": n, "titulo": c.titulo[:40], "indice": i,
                      "dificultad": round(sum(vs) / len(vs), 3),
                      "min": round(min(vs), 3), "max": round(max(vs), 3),
                      "ventanas": len(vs), "palabras": c.palabras})
    ...  # el resto igual
```

**Ganancia esperada: entre 1,5× y 4×** [estimado]. El rango es amplio a
propósito: depende de cuánto del 85 % perdido es lote pequeño y cuánto es
tokenización, y eso lo dice la medición de §3.2. **Cómo comprobarlo en dos
minutos, antes de escribir nada:**

```python
for tam in (8, 16, 32, 64, 128, 256, 512):
    puntuar_lote(bloques[:64], tam=tam)                  # calentar
    t = time.time(); puntuar_lote(bloques, tam=tam); s = time.time() - t
    print(f"lote {tam:4d} -> {len(bloques)/s:7.0f} ventanas/s")
```

Si la curva entre 8 y 256 es plana, esta palanca no es la buena y hay que ir a
§3.2. Si sube 3×, es la buena. **Esa tabla vale más que todo lo que he escrito
en esta sección.**

**Requisito previo de la siguiente palanca:** con lotes fijos de 256 todos los
tensores tienen exactamente la misma forma, y eso es lo que hace viable
`torch.compile` (§3.5). Con el troceado por capítulo, cada capítulo daría una
forma distinta y `torch.compile` recompilaría sin parar.

### 3.2 Medir el reparto del reloj antes de nada más

Diez líneas, dos minutos, y decide todo lo demás:

```python
import time
def cronometrar(bloques, tam=256):
    t0 = time.time()
    ent = [tok(bloques[i:i+tam], truncation=True, max_length=scoring.MAX_LENGTH,
               padding=True, return_tensors="pt") for i in range(0, len(bloques), tam)]
    torch.cuda.synchronize(); t1 = time.time()
    for e in ent:
        with torch.inference_mode():
            mod(**e.to(DISPOSITIVO)).logits.float().cpu()
    torch.cuda.synchronize(); t2 = time.time()
    print(f"tokenizar {t1-t0:5.2f} s | GPU {t2-t1:5.2f} s | "
          f"tokenizar es el {100*(t1-t0)/(t2-t0):.0f} % del reloj")
```

**Predicción:** la tokenización saldrá entre el 30 % y el 60 %. Si sale así, §3.3
es obligatoria. **[no verificado: es la extrapolación del 0,6 s medido en CPU]**

### 3.3 Solapar lectura y tokenización con la GPU

Hoy el bucle es estrictamente serie: leer de Drive → parsear capítulos →
tokenizar → GPU → siguiente libro. La GPU está parada durante los tres primeros
pasos. La corrección estándar es un productor en segundo plano; con
`ThreadPoolExecutor` basta, porque la tokenización de HF suelta el GIL (va en
Rust) y la lectura de fichero también.

```python
from concurrent.futures import ThreadPoolExecutor

def preparar(ruta):
    """Todo el trabajo de CPU de un libro: leer, filtrar, trocear, tokenizar."""
    libro = reader.cargar(str(ruta))
    tramos, cola = [], []
    for n, (i, c) in enumerate(ficha.capitulos_de_cuerpo(libro), 1):
        bs = scoring.fixed_blocks(ficha.sin_licencia(c.texto), cap=10**9)
        if bs:
            tramos.append((n, i, c, len(cola), len(cola) + len(bs)))
            cola.extend(bs)
    lotes = [tok(cola[i:i+256], truncation=True, max_length=scoring.MAX_LENGTH,
                 padding=True, return_tensors="pt")
             for i in range(0, len(cola), 256)]
    return ruta, tramos, lotes

with ThreadPoolExecutor(max_workers=4) as pool:
    for ruta, tramos, lotes in pool.map(preparar, disponibles, chunksize=1):
        ...   # aquí la GPU solo hace forwards; el hilo 4 ya está leyendo el libro +3
```

**Ganancia esperada: hasta 2×** si la medición de §3.2 dice que CPU y GPU se
reparten el reloj a partes iguales; menos si no. Cuatro hilos, no más: son
suficientes para tapar la GPU y no compiten con los hilos internos del
tokenizador. **[estimado]**

Nota: `pool.map` con `chunksize=1` mantiene el orden y limita la memoria en
vuelo. Si se prefiere control explícito, una `queue.Queue(maxsize=8)` y un hilo
productor hacen lo mismo y son más fáciles de depurar.

### 3.4 Que los textos vivan en `/content`, no en Drive

Consecuencia de §1.5. El flujo por sesión:

```bash
# Una lectura secuencial grande, que es lo que Drive hace bien
cp /content/drive/MyDrive/literalevel_bigdata/txt-files.tar.zip /content/
# ... extraer solo el inglés a /content/gutenberg_txt (código en §2.2)
```

y en el cuaderno, `TEXTOS = Path("/content/gutenberg_txt")`. **Los shards de
resultados siguen yendo a Drive tal cual están** — 500 libros por fichero es
exactamente el patrón que Drive tolera bien, y el comentario de la celda 10 que
lo justifica es correcto.

**Sobre los 28.535 `.txt` que ya están en Drive:** no hay que borrarlos, pero
tampoco sirven de nada una vez el tar esté en su sitio, y cuestan 98 s cada vez
que alguien lista el directorio (más, según crezca). Yo los movería a una
subcarpeta `viejo/` o los borraría después de que la comprobación md5 de §2.6
dé 200/200.

### 3.5 `torch.compile`, después de §3.1

Con lotes fijos de 256×256 y sin padding, la forma del tensor es constante y
`torch.compile` no tiene nada que recompilar:

```python
mod = torch.compile(mod, mode="max-autotune", dynamic=False, fullgraph=True)
```

La [documentación de transformers](https://huggingface.co/docs/transformers/en/perf_torch_compile)
publica *benchmarks* con `reduce-overhead` en A100 y explica que `max-autotune`
compila más lento pero da la inferencia más rápida. Para un *encoder* de 6 capas
la ganancia viene de fundir LayerNorm, GELU y los sesgos: **entre +10 % y +30 %**
**[estimado; no he encontrado benchmark publicado de `distilroberta` en A100 con
`torch.compile`, y no lo voy a inventar]**.

Dos condiciones:

- **El último lote de cada libro no llega a 256.** O se acepta una segunda forma
  compilada (dos grafos, aceptable), o se acumulan ventanas *entre libros* en un
  buffer de 256 para que todos los lotes sean llenos. Lo segundo es más limpio y
  además redondea §3.1.
- **Hay que volver a pasar la celda 8.** `torch.compile` reordena operaciones y
  puede mover el último decimal. La comparación fp16 vs fp32 que ya existe en el
  cuaderno es exactamente la prueba que hace falta; el criterio publicado allí
  («aceptable si el máximo está por debajo de 0,01») vale igual.

Coste: dos líneas, más 1–3 minutos de compilación al arrancar cada sesión.

---

## 4. Lo que NO merece la pena, y por qué

Esta sección es tan útil como la anterior.

### 4.1 bf16 en la A100 — **no**

La [ficha técnica de NVIDIA](https://www.nvidia.com/en-us/data-center/a100/) da,
para A100:

| | Tensor Core |
|---|---|
| **BFLOAT16** | **312 TFLOPS** |
| **FP16** | **312 TFLOPS** |
| TF32 | 156 TFLOPS |
| FP32 | 19,5 TFLOPS |

**bf16 y fp16 corren exactamente igual de rápido.** No hay ni un 1 % que ganar.
Y bf16 es **menos preciso** para este trabajo: tiene 8 bits de mantisa contra 10
de fp16, y aquí no hace ninguna falta el rango dinámico extra de bf16, porque
los logits del modelo viven en `[0, 5]`. Cambiar a bf16 sería perder decimales
gratis.

El resultado de la GTX 1650 SUPER —fp16 **4,8× más lento** que fp32,
`informe_velocidad.md` §3.f— **no se traslada** y el informe ya explica por qué:
el TU116 no tiene tensor cores. En A100 fp16 es el camino bueno, y el cuaderno
ya lo usa. **Aquí no hay nada que hacer.**

### 4.2 Cuantización int8 — **no, y ya se sabía**

Medido y rechazado en `informe_velocidad.md` §3.d: **+18 % de velocidad a cambio
de MAE 0,210 y sesgo −0,21** en una escala de 0 a 2. Un texto de 1,682 pasa a
1,472 y cruza la frontera de banda. No lo propongo, y añado una razón nueva:
**tampoco resolvería nada.** El problema no es que el cómputo sea caro; es que
la GPU está al 15 % de ocupación. Ir a int8 duplicaría un pico que no se está
usando.

Para que int8 volviera a estar sobre la mesa habría que **recalibrar la escala
pública después de cuantizar** (ajustar la recta int8→fp32 sobre unas cuantas
miles de ventanas y corregir el sesgo antes de `public_score`). Es un proyecto
en sí mismo, con su propia validación, y no es donde están las horas ahorradas.

### 4.3 Flash Attention / SDPA — **casi nada que ganar**

Con `MAX_LENGTH = 256`, la atención es **4,72 de 89,65 MFLOP por token, o sea el
5,3 %** [aritmética, §1.4]. Aunque la atención fuera gratis, el techo de la
mejora es un 5 %. FlashAttention brilla con secuencias largas; 256 tokens no lo
son. Además, `transformers` ya usa SDPA por defecto para RoBERTa desde hace
varias versiones — **compruébalo, no lo supongas**:

```python
print(mod.config._attn_implementation)     # esperado: "sdpa"
```

Y la otra optimización que suele acompañarla, *input unpadding*, aquí vale
exactamente **cero**: no hay padding, todas las ventanas son 256 tokens
[medido].

### 4.4 ONNX Runtime / TensorRT — **no ahora**

El [blog de Microsoft sobre ORT-TensorRT](https://opensource.microsoft.com/blog/2022/05/02/optimizing-and-deploying-transformer-int8-inference-with-onnx-runtime-tensorrt-on-nvidia-gpus/)
reporta *«up to seven times speedup over PyTorch»* para BERT en A100 — pero eso
es **INT8** (§4.2, descartado) y **latencia a lote 1**, que es el régimen
opuesto al nuestro. Para fp16 con lotes grandes, frente a un PyTorch ya
compilado, la ganancia es mucho menor y no la he visto publicada para este
tamaño de modelo **[no verificado]**.

Contra: exportar y verificar numéricamente, instalar TensorRT en cada sesión de
Colab, construir el *engine* (5–15 min, y atado a la GPU concreta que toque),
y sostener **dos implementaciones** del mismo modelo — la app puntúa en PyTorch
*eager* y el catálogo se mediría en ORT. Cada divergencia futura sería
invisible. Eso es exactamente lo que `capitulos_de_cuerpo` existe para evitar.

**Reconsiderar solo si**, hechas §3.1 a §3.5, el reloj sigue dominado por la
GPU. Hoy no lo está.

### 4.5 Un modelo más pequeño o destilado — **no**

Cambiaría los números del catálogo entero y obligaría a revalidar Spearman 0,91
y la calibración. Es un proyecto de modelo, no de velocidad, y `AGENTS.md` es
explícito: **el v4 es final y no se reentrena**. Además, por §1.4, un modelo
la mitad de grande no daría el doble de velocidad, porque el cómputo no es el
que manda.

### 4.6 Más hilos o más espejos en la descarga — **no**

Ver §2.1 y §2.5. Sumaría riesgo de bloqueo, no arreglaría la escritura a Drive,
y queda sin objeto en cuanto se baje el tar de §2.2.

### 4.7 `pin_memory` y `DataLoader` con *workers* — **irrelevante aquí**

Un lote de 256×256 tokens en int64 son **512 KB**. Sobre PCIe 4.0 eso es
microsegundos. `pin_memory` optimiza una transferencia que no cuesta nada. Lo
que sí hay que solapar es **la tokenización y la lectura**, y para eso no hace
falta `DataLoader`: cuatro hilos y una cola (§3.3). Meter `DataLoader` aquí
añade dependencia y complejidad sin ganar nada.

### 4.8 `inference_mode` vs `no_grad` — **da igual**

Medido en `informe_velocidad.md` §3.c: 8,53 vs 8,50 ventanas/s, diferencia por
debajo del ruido. El código ya usa `inference_mode`. No se toca.

---

## 5. Recomendación

### Qué haría, en orden

**Hoy, media hora, sin escribir código de producción.**

1. Ejecutar el barrido de lote de §3.1 (`tam` de 8 a 512) y el cronómetro de
   §3.2. **Estas dos tablas deciden todo lo demás.** Si el barrido es plano, la
   §3.1 no es la palanca y hay que ir directo a la tokenización; si sube 3×, ya
   sabemos dónde estaba la A100.
2. Ejecutar la comparación Drive vs `/content` de §1.5 con 200 ficheros. Pone
   número por fin a la sospecha de Miguel.
3. Sacar la media real de ventanas por libro de los 2.458 shards (§1.1) y
   rehacer la estimación de horas. Deja de haber un `350` supuesto en el
   cuaderno.

**Mañana, media jornada.**

4. **Bajar `txt-files.tar.zip`** (§2.2) a `/content`, copiarlo a Drive como
   único objeto, extraer los ids ingleses a `/content/gutenberg_txt`, y validar
   con los md5 de §2.6 contra 200 libros que ya están en Drive. Parar el bucle
   de descarga HTTP.
5. **Aplanar el lote** (§3.1) y **apuntar `TEXTOS` a `/content`** (§3.4).
6. Relanzar el precálculo y mirar el `libros/s` que imprime la celda 10b.

**Después, si hace falta.**

7. Productor en hilos (§3.3), si §3.2 dijo que la tokenización pesa.
8. `torch.compile` (§3.5), con la celda 8 repetida como control.

### Qué ganancia espero

| Palanca | Esfuerzo | Ganancia esperada | Confianza |
|---|---|---|---|
| Tar en vez de 33.000 GET | 1 h | **~30 h → ~15 min** | Alta: el fichero existe y su tamaño está comprobado |
| Aplanar el lote | 3–4 h | **1,5× – 4×** en el análisis | Media-alta: el 15 % de ocupación es real; el reparto exacto no |
| Textos en `/content` | 1 h | quita un coste desconocido pero seguro | Alta en dirección, nula en magnitud hasta medir |
| Solapar CPU y GPU | 2 h | hasta **2×** | Media, condicionada a §3.2 |
| `torch.compile` | 1 h | **+10–30 %** | Baja-media, sin benchmark propio |
| Quitar el `glob` del bucle de descarga | **1 línea** | hasta **2×** en la descarga | Alta, si se decidiera seguir por HTTP |

Un objetivo razonable, y lo digo como objetivo y no como predicción: **el
catálogo entero medido en una sola sesión de Colab de menos de ocho horas**,
descarga incluida. Hoy, con 2.458 libros en varias sesiones y el análisis
parado, eso está lejos; con las palancas 4 y 5 debería estar cerca.

### Qué riesgo tiene

**El riesgo de exactitud es el que importa, y es bajo pero no nulo.**

- **Aplanar el lote: riesgo cero, y está demostrado.** Sin padding, reagrupar da
  resultados idénticos bit a bit (`informe_velocidad.md` §3.b, 300/300). Aun
  así, la prueba de regresión correcta es barata y la haría: **volver a medir 20
  libros ya presentes en los shards y comprobar que la `dificultad` sale
  idéntica a tres decimales.** Si no sale idéntica, el refactor tiene un fallo,
  no la GPU.
- **Cambiar de fuente de textos: riesgo real, y por eso la comprobación md5.**
  Si el tar trajera una codificación distinta a la que baja hoy
  `_rutas_posibles`, los `.txt` no serían byte a byte los mismos y las cifras
  podrían moverse en el último decimal. Los 200 md5 de §2.6 lo detectan antes de
  medir nada. **Si el dataset de Hugging Face se usara en lugar del tar, este
  riesgo sube bastante** y la comprobación pasa de recomendable a obligatoria.
- **`torch.compile`: riesgo bajo y controlado** por la celda 8, que ya existe.
  Si mueve más de 0,01 en la escala 0–2, se quita y no pasa nada.
- **Mezclar libros medidos con distinta configuración: este es el riesgo
  silencioso.** Los 2.458 libros ya en los shards se midieron con lotes por
  capítulo; los siguientes irían con lotes de 256. Como no hay padding **deben**
  coincidir — pero «deben» no es «coinciden». Antes de dar el catálogo por
  bueno, remediría los 20 libros de control del primer punto. Es diez minutos y
  cierra la duda por escrito, que es como se han cerrado las demás en este
  proyecto.

**El riesgo operativo baja, no sube.** Pasar de 33.000 peticiones HTTP a una
descarga de un tar o a un `rsync` nos saca de la zona gris de la política de
Gutenberg (§2.5) y nos pone exactamente en las dos vías que ellos documentan.
Y pasar de 61.642 ficheros pequeños en Drive a un objeto grande elimina de
golpe la clase entera de fallos que Colab documenta: timeouts al montar,
cuotas de Drive excedidas y listados de 98 segundos.

---

## Fuentes

- [Mirroring How-To — Project Gutenberg](https://www.gutenberg.org/help/mirroring.html)
- [Robot Access to Pages — Project Gutenberg](https://www.gutenberg.org/policy/robot_access.html)
- [Request Blocked — block.pglaf.org](https://block.pglaf.org/)
- [Offline Catalogs — Project Gutenberg](https://www.gutenberg.org/ebooks/offline_catalogs.html)
- [MIRRORS.ALL](https://www.gutenberg.org/MIRRORS.ALL)
- [Índice `cache/generated/feeds/` del espejo pglaf](https://gutenberg.pglaf.org/cache/generated/feeds/) — de aquí salen el tamaño y la fecha de `txt-files.tar.zip`
- [Getting All the Books — Robotic Ape (2018)](https://roboticape.com/2018/06/26/getting-all-the-books/) — precedente de rsync con filtros
- [How to Politely Download All English Language Text Format Files — Ex Ratione](https://www.exratione.com/2014/11/how-to-politely-download-all-english-language-text-format-files-from-project-gutenberg/)
- [`manu/project_gutenberg` en Hugging Face](https://huggingface.co/datasets/manu/project_gutenberg) · [tamaños vía API](https://datasets-server.huggingface.co/size?dataset=manu/project_gutenberg)
- [`sedthh/gutenberg_english` en Hugging Face](https://huggingface.co/datasets/sedthh/gutenberg_english)
- [Standardized Project Gutenberg Corpus — Zenodo](https://zenodo.org/records/2422561)
- [NVIDIA A100 — especificaciones](https://www.nvidia.com/en-us/data-center/a100/)
- [Optimize inference using `torch.compile()` — Hugging Face](https://huggingface.co/docs/transformers/en/perf_torch_compile)
- [Optimizing and deploying transformer INT8 inference with ONNX Runtime-TensorRT — Microsoft](https://opensource.microsoft.com/blog/2022/05/02/optimizing-and-deploying-transformer-int8-inference-with-onnx-runtime-tensorrt-on-nvidia-gpus/)
- [Reading large datasets for training on Colab — F. Cremonesi](https://sharkovsky.github.io/2020/09/18/colab-io-bench.html)
- [colabtools#1691 — Insanely slow data reading from Google Drive](https://github.com/googlecolab/colabtools/issues/1691)
- [colabtools#1607 — Google Drive quota exceeded al copiar](https://github.com/googlecolab/colabtools/issues/1607)
- [FastColabCopy](https://github.com/L0garithmic/FastColabCopy)
- [FAQ de Google Colab](https://research.google.com/colaboratory/faq.html)

Y, dentro de casa: `informe_velocidad.md` (§1, §2, §3.b, §3.c, §3.d, §3.f),
`investigacion/transformer_v5.md` (§1.1), `colab_precalculo.py` (celdas 5, 6,
6b, 7, 9, 10, 10b), `modelo_v4/config.json`, `app/scoring.py`, `app/ficha.py`.
