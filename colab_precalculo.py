# %% [markdown]
# # LiteraLevel — precálculo masivo del catálogo
#
# Mide con el modelo v4 **todos** los libros en inglés de Project Gutenberg y
# guarda el perfil de dificultad de cada uno en Drive. Cuando esto termine, la
# app no tiene que medir nada en vivo: busca el libro y el análisis ya está.
#
# **Qué hace, en orden:** comprueba la GPU, monta Drive, trae el código de
# LiteraLevel, baja el catálogo oficial de Gutenberg, descarga los textos,
# carga el modelo v4 en la GPU, **mide su velocidad real** y solo entonces
# lanza el precálculo.
#
# **Se puede interrumpir en cualquier momento.** Todo va por lotes y todo es
# reanudable: si Colab corta la sesión, se vuelve a ejecutar y sigue donde
# estaba. Con 61.000 libros eso no es una comodidad, es un requisito.
#
# **Los textos NO se guardan en Drive, y es a propósito.** Project Gutenberg
# publica todos sus `.txt` en un solo archivo de 11,3 GB que se regenera cada
# semana; se baja de una vez al disco del entorno y se extrae ahí. Escribir
# sesenta mil archivos sueltos en Drive es lentísimo —solo *listar* 28.535
# tardaba 98 segundos— y además no hace falta: lo que tiene que sobrevivir a la
# sesión son los resultados, no los textos, que se vuelven a bajar en minutos.
#
# Por eso los resultados van a Drive en *shards* de 500 libros: seis archivos,
# no sesenta mil.

# %%
# --- 1. ¿Qué GPU nos tocó? ------------------------------------------------
# Con Colab Pro y A100 esto vuela; con una T4 tarda bastante más. Conviene
# saber en cuál estamos ANTES de lanzar nada, porque cambia el plan.
import subprocess
print(subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout)

import torch
print("torch:", torch.__version__, "| CUDA:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0),
          "|", round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1), "GB")
else:
    print("SIN GPU. Entorno de ejecución > Cambiar tipo > GPU (A100). "
          "En CPU esto tardaría meses y no merece la pena empezar.")

# %%
# --- 2. Drive y carpetas --------------------------------------------------
import os, time
from pathlib import Path

from google.colab import drive

# Se reintenta a proposito. La primera llamada falla con `ValueError: mount
# failed` cuando el dialogo de permiso se contesta despues de que el montaje ya
# arranco -que es lo normal la primera vez-, y al reintentar funciona. Sin esto,
# "Ejecutar todas" se para en la segunda celda cada vez que Colab da una VM
# nueva, y con un trabajo de horas que hay que reanudar eso pasa a menudo.
for intento in range(1, 4):
    try:
        drive.mount("/content/drive", force_remount=(intento == 1),
                    timeout_ms=180000)
        break
    except Exception as e:
        print(f"  intento {intento} de montar Drive: {type(e).__name__}: {e}")
        if intento == 3:
            raise
        time.sleep(5)

RAIZ = Path("/content/drive/MyDrive/literalevel_bigdata")
TEXTOS = RAIZ / "gutenberg_txt"        # los libros descargados
PERFILES = RAIZ / "perfiles"           # los resultados, en shards
MODELO = RAIZ / "modelo_literalevel_v4_transformer"
for d in (RAIZ, TEXTOS, PERFILES):
    d.mkdir(parents=True, exist_ok=True)

print("modelo v4 en Drive:", MODELO.exists())
if not MODELO.exists():
    print("  Ajusta MODELO a la carpeta real. Contenido de", RAIZ, ":")
    for n in sorted(os.listdir(RAIZ))[:40]:
        print("   ", n)

# %%
# --- 3. Dependencias ------------------------------------------------------
# Colab ya trae torch y transformers. El resto es ligero.
!pip -q install transformers --upgrade 2>/dev/null | tail -1
print("listo")

# %%
# --- 4. El código de LiteraLevel -----------------------------------------
# Se usan los módulos REALES del repositorio, no una copia reescrita aquí.
# Si se reimplementara el troceado en el notebook, tarde o temprano divergiría
# del de la app y los números dejarían de significar lo mismo. Copia la
# carpeta `app/` del repo a Drive (dentro de literalevel_bigdata) antes de
# ejecutar esto.
import sys
# Se admiten las dos formas de haberlos subido: dentro de una carpeta `app/` o
# sueltos en la raiz de literalevel_bigdata. Subir una carpeta a Drive desde el
# navegador no siempre conserva la carpeta, y no merece la pena que el notebook
# falle por eso.
APP = next((d for d in (RAIZ / "app", RAIZ) if (d / "scoring.py").exists()), None)
if APP is None:
    raise SystemExit(
        f"No encuentro scoring.py ni en {RAIZ / 'app'} ni en {RAIZ}. "
        "Sube scoring.py, reader.py y ficha.py del repositorio a Drive.")
faltan = [n for n in ("scoring.py", "reader.py", "ficha.py")
          if not (APP / n).exists()]
if faltan:
    raise SystemExit(f"Faltan en {APP}: {', '.join(faltan)}")
sys.path.insert(0, str(APP))

import scoring, reader, ficha
print("scoring, reader y ficha importados desde", APP)
print("BLOCK_WORDS:", scoring.BLOCK_WORDS, "| MAX_LENGTH:", scoring.MAX_LENGTH)

# %%
# --- 5. El catálogo oficial de Gutenberg ----------------------------------
# 79.337 entradas, de las cuales ~61.600 son libros de texto en inglés.
import pandas as pd, urllib.request

RUTA_CAT = RAIZ / "pg_catalog.csv"
if not RUTA_CAT.exists():
    urllib.request.urlretrieve(
        "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv", RUTA_CAT)

cat = pd.read_csv(RUTA_CAT)
en = cat[(cat["Language"] == "en") & (cat["Type"] == "Text")].copy()
en["Text#"] = en["Text#"].astype(int)
print(f"catálogo completo: {len(cat):,}")
print(f"libros de texto en inglés: {len(en):,}")

# --- Aquí NO se filtra el catálogo, y es una decisión, no un descuido -------
# Hubo un filtro por materias "adultas" y se quitó. La razón es de Miguel y es
# buena: esto es una plataforma de literatura, y la literatura es donde esas
# cosas aparecen. Filtrar por la etiqueta `Subjects` habría tirado también
# obras que son literatura por derecho propio -Fanny Hill, sin ir más lejos,
# que se persiguió judicialmente y por eso mismo importa-. Un catálogo de
# dominio público que se poda a sí mismo deja de ser un catálogo.
#
# Lo que sí se hace, y es lo honesto, es AVISAR en vez de esconder: la ficha de
# cada libro (`ficha.sinopsis`) trae un campo `aviso` que sale en la app como
# "Antes de empezar" y dice si la obra tiene algo que conviene saber. Informar
# al lector y dejarle elegir; no elegir por él.
en[["Text#", "Title", "Authors", "Subjects"]].head()

# %%
# --- 6. Descargar los textos ---------------------------------------------
# Se baja de un ESPEJO, no de gutenberg.org: el sitio principal pide
# explícitamente que no se le rasque en masa y bloquea por IP. Los espejos
# existen justamente para esto.
#
# Reanudable: lo que ya está en Drive no se vuelve a pedir. Y con una pausa
# entre peticiones, porque el espejo es un servicio gratuito de alguien.
import time, random, urllib.error

ESPEJOS = [
    "https://gutenberg.pglaf.org",          # espejo oficial recomendado
    "https://aleph.gutenberg.org",
]
PAUSA = 0.4          # segundos entre descargas; no lo bajes


def _rutas_posibles(n: int) -> list[str]:
    """Gutenberg reparte los ids en carpetas por sus dígitos: el 1342 vive en
    /1/3/4/1342/. Los ids de un solo dígito son la excepción y van en /0/."""
    d = str(n)
    carpeta = "/".join(d[:-1]) if len(d) > 1 else "0"
    base = f"/{carpeta}/{d}/"
    return [f"{base}{d}-0.txt", f"{base}{d}.txt", f"{base}{d}-8.txt"]


DESTINO_TEXTOS = TEXTOS      # la celda 6b lo repunta al disco local


def descargar(n: int) -> bool:
    destino = DESTINO_TEXTOS / f"pg{n}.txt"
    if destino.exists() and destino.stat().st_size > 2000:
        return True                      # ya estaba
    for espejo in ESPEJOS:
        for ruta in _rutas_posibles(n):
            try:
                req = urllib.request.Request(
                    espejo + ruta, headers={"User-Agent": "LiteraLevel/1.0 (proyecto academico)"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    datos = r.read()
                if len(datos) > 2000:
                    destino.write_bytes(datos)
                    time.sleep(PAUSA)
                    return True
            except (urllib.error.URLError, OSError, TimeoutError):
                continue
    return False


# EL ORDEN IMPORTA, y mucho más de lo que parece. El catálogo de Gutenberg
# viene ordenado por número de texto, y los primeros números son la
# Declaración de Independencia, la Carta de Derechos y un discurso de Kennedy:
# documentos, no novelas. Si el precálculo se corta a media faena —y con
# 61.642 libros es lo más probable—, lo hecho sería justo lo que nadie va a
# querer leer.
#
# Los recuentos de descargas están en la metadata del SPGC, que ya vive en
# Drive. Con ella se empieza por lo que la gente lee de verdad.
RUTA_SPGC = RAIZ / "SPGC-metadata-2018-07-18.csv"
if RUTA_SPGC.exists():
    spgc = pd.read_csv(RUTA_SPGC)
    col = next((c for c in spgc.columns if "download" in c.lower()), None)
    if col:
        spgc["num"] = (spgc["id"].astype(str).str.extract(r"(\d+)")[0]
                       .astype("Int64"))
        popularidad = dict(zip(spgc["num"].dropna().astype(int),
                               spgc[col].fillna(0)))
        print(f"popularidad conocida de {len(popularidad):,} libros")
    else:
        popularidad = {}
        print("la metadata del SPGC no trae descargas; se deja el orden natural")
else:
    popularidad = {}
    print("sin metadata del SPGC; se deja el orden natural")

pendientes = sorted((int(i) for i in en["Text#"].tolist()),
                    key=lambda n: -popularidad.get(n, 0))
print(f"{len(pendientes):,} libros en la lista")
print("Ya en Drive:", len(list(TEXTOS.glob('*.txt'))))
if popularidad:
    cab = {int(r["Text#"]): str(r["Title"])[:44] for _, r in en.iterrows()}
    print("\nLos diez primeros por descargas:")
    for n in pendientes[:10]:
        print(f"  {int(popularidad.get(n, 0)):>7} descargas · {cab.get(n, '?')}")

# %%
# --- 6b. La descarga, de un tirón ----------------------------------------
# Project Gutenberg publica **todos sus .txt en un solo archivo**, que se
# regenera cada semana:
#
#     https://gutenberg.pglaf.org/cache/generated/feeds/txt-files.tar.zip
#     11.278.856.242 bytes, comprobado el 8 de septiembre de 2026
#
# Una peticion HTTP en lugar de treinta y tres mil. Antes esta celda bajaba
# libro a libro con seis hilos y salian unos 0,3 libros/s: mas de dos dias
# para el catalogo, con Colab cortando la sesion cada pocas horas. Bajando el
# archivo entero, el limite pasa a ser el ancho de banda y no la latencia.
#
# DONDE SE DESCOMPRIME, que es la otra mitad del arreglo. En el disco local
# del entorno (`/content`), NO en Drive. Escribir sesenta mil ficheros
# pequenios en Drive es lentisimo -solo LISTAR 28.535 tardaba 98 segundos-, y
# ademas no hace falta: lo que tiene que sobrevivir a la sesion son los
# resultados, que son seis ficheros de perfiles, no los textos, que se pueden
# volver a bajar.
#
# Se pagan unos minutos de descarga en cada sesion nueva a cambio de no
# escribir decenas de miles de ficheros en Drive ni una sola vez.
#
# Si el archivo no estuviera disponible, la celda cae sola al metodo de antes
# -libro a libro, en paralelo- para los que falten.
import shutil
import tarfile
import zipfile

ARCHIVO_URL = "https://gutenberg.pglaf.org/cache/generated/feeds/txt-files.tar.zip"
LOCAL = Path("/content/gutenberg_txt")
LOCAL.mkdir(parents=True, exist_ok=True)
ZIP_LOCAL = Path("/content/txt-files.tar.zip")


def _hay_espacio(bytes_necesarios: int, donde="/content") -> bool:
    libre = shutil.disk_usage(donde).free
    print(f"  espacio libre en {donde}: {libre / 1e9:.1f} GB "
          f"(hacen falta ~{bytes_necesarios / 1e9:.0f})")
    return libre > bytes_necesarios


def bajar_archivo() -> bool:
    """Baja el tar.zip a /content. Devuelve False si no se pudo."""
    if ZIP_LOCAL.exists() and ZIP_LOCAL.stat().st_size > 10 ** 10:
        print("el archivo ya esta en /content, no se vuelve a bajar")
        return True
    try:
        req = urllib.request.Request(
            ARCHIVO_URL,
            headers={"User-Agent": "LiteraLevel/1.0 (proyecto academico)"})
        with urllib.request.urlopen(req, timeout=120) as r:
            total = int(r.headers.get("Content-Length") or 0)
            print(f"bajando {total / 1e9:.1f} GB ...")
            if total and not _hay_espacio(int(total * 2.6)):
                print("  NO hay espacio suficiente en /content; se usa el "
                      "metodo de libro a libro")
                return False
            hecho, t0, ultimo = 0, time.time(), 0.0
            with open(ZIP_LOCAL, "wb") as f:
                while True:
                    trozo = r.read(8 * 1024 * 1024)
                    if not trozo:
                        break
                    f.write(trozo)
                    hecho += len(trozo)
                    if time.time() - ultimo > 30:
                        ultimo = time.time()
                        v = hecho / max(time.time() - t0, 1) / 1e6
                        pct = f"{100 * hecho / total:.1f}%" if total else "?"
                        print(f"  {hecho / 1e9:.1f} GB · {pct} · {v:.0f} MB/s")
        print(f"bajado en {(time.time() - t0) / 60:.1f} min")
        return True
    except Exception as e:
        print("no se pudo bajar el archivo completo:", type(e).__name__, e)
        return False


def extraer(numeros_que_quiero: set[int]) -> int:
    """Saca de dentro del archivo SOLO los libros que interesan.

    El archivo trae los .txt de todo Gutenberg, incluidos los que no estan en
    ingles y los que ya no aplican. Extraer los 61.642 que queremos y dejar
    fuera el resto se hace aqui, leyendo el tar en streaming sin descomprimirlo
    entero.

    ESTRUCTURA REAL DEL ARCHIVO, comprobada el 9 de septiembre de 2026 pidiendo
    los primeros 3 MB por rango HTTP y descomprimiendolos al vuelo:

        cache/epub/10000/pg10000.txt      101.742 B
        cache/epub/1000/pg1000.txt        597.903 B
        cache/epub/84/pg84.txt            ...

    El zip contiene un unico miembro, `txt-files.tar`, comprimido con deflate.
    Dentro, cada libro va en `cache/epub/<n>/pg<n>.txt`, o sea que el numero
    aparece DOS VECES: en la carpeta y en el nombre. Se exigen las dos y que
    coincidan, que es mas seguro que fiarse de una sola: un `readme.txt` o un
    fichero suelto con digitos en el nombre no pasa el filtro.
    """
    sacados = 0
    with zipfile.ZipFile(ZIP_LOCAL) as z:
        interiores = [n for n in z.namelist() if n.endswith(".tar")]
        if not interiores:
            print("  el zip no contiene un .tar; se usa el metodo antiguo")
            return 0
        print(f"  el zip contiene: {interiores[0]}")
        with z.open(interiores[0]) as tar_bruto:
            with tarfile.open(fileobj=tar_bruto, mode="r|") as tar:
                t0 = time.time()
                for miembro in tar:
                    if not miembro.isfile() or not miembro.name.endswith(".txt"):
                        continue
                    partes = Path(miembro.name).parts
                    if len(partes) < 2:
                        continue
                    carpeta = "".join(c for c in partes[-2] if c.isdigit())
                    base = Path(miembro.name).stem
                    fichero = "".join(c for c in base.split("-")[0] if c.isdigit())
                    # El numero tiene que estar en la carpeta Y en el nombre, y
                    # ser el mismo. Asi un readme.txt o un fichero raro con
                    # digitos sueltos no se cuela.
                    if not carpeta or not fichero or carpeta != fichero:
                        continue
                    n = int(fichero)
                    if n not in numeros_que_quiero:
                        continue
                    destino = LOCAL / f"pg{n}.txt"
                    if destino.exists():
                        continue
                    f = tar.extractfile(miembro)
                    if f is None:
                        continue
                    datos = f.read()
                    if len(datos) > 2000:
                        destino.write_bytes(datos)
                        sacados += 1
                        if sacados % 2000 == 0:
                            print(f"  {sacados:,} extraidos · "
                                  f"{(time.time() - t0) / 60:.1f} min")
    return sacados


# Los libros que queremos, por numero.
QUIERO = set(int(n) for n in pendientes)

# Lo que ya haya en Drive de tandas anteriores se aprovecha: se enlaza al
# directorio local en vez de volver a extraerlo.
reciclados = 0
if TEXTOS.exists():
    for r in TEXTOS.glob("*.txt"):
        destino = LOCAL / r.name
        if not destino.exists():
            try:
                os.symlink(r, destino)
            except (OSError, NotImplementedError):
                shutil.copy2(r, destino)
            reciclados += 1
print(f"reaprovechados de Drive: {reciclados:,}")

sacados = 0
if bajar_archivo():
    sacados = extraer(QUIERO)
    print(f"extraidos del archivo: {sacados:,}")
else:
    # Camino de respaldo: el de siempre, libro a libro y en paralelo.
    from concurrent.futures import ThreadPoolExecutor
    DESTINO_TEXTOS = LOCAL
    faltan = [n for n in pendientes if not (LOCAL / f"pg{n}.txt").exists()]
    print(f"respaldo libro a libro para {len(faltan):,}")
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i, ok in enumerate(pool.map(descargar, faltan), 1):
            if i % 500 == 0:
                print(f"  {i:,} intentados")

TEXTOS_LISTOS = LOCAL
disponibles_ahora = sum(1 for _ in LOCAL.glob("*.txt"))
print(f"\nTEXTOS LISTOS PARA ANALIZAR: {disponibles_ahora:,} "
      f"de {len(pendientes):,} ({100 * disponibles_ahora / len(pendientes):.1f}%)")
print(f"estan en {LOCAL} (disco del entorno, no Drive)")
print("Los resultados si van a Drive: son seis ficheros, no sesenta mil.")


# %%
# --- 7. El modelo v4 en la GPU -------------------------------------------
# Los pesos son los mismos que en la app. Lo único que cambia es dónde corren
# y en qué precisión, y de la precisión se rinden cuentas más abajo.
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
MEDIA_PRECISION = DISPOSITIVO == "cuda"

tok = AutoTokenizer.from_pretrained(str(MODELO))
mod = AutoModelForSequenceClassification.from_pretrained(str(MODELO))
mod.eval().to(DISPOSITIVO)
if MEDIA_PRECISION:
    mod = mod.half()
print("modelo en", DISPOSITIVO, "| fp16:", MEDIA_PRECISION)


def puntuar_lote(bloques, tam=256):
    """Escala pública 0..2 para cada ventana. Mismo troceado que la app."""
    fuera = []
    for i in range(0, len(bloques), tam):
        trozo = bloques[i:i + tam]
        ent = tok(trozo, truncation=True, max_length=scoring.MAX_LENGTH,
                  padding=True, return_tensors="pt").to(DISPOSITIVO)
        with torch.inference_mode():
            y = mod(**ent).logits.squeeze(-1).float().cpu().numpy()
        fuera.extend(float(v) for v in y.reshape(-1).clip(0, 5))
    return [round(scoring.public_score(v), 3) for v in fuera]

# %%
# --- 8. ¿Cuánto se desvía la media precisión? ----------------------------
# fp16 es el doble de rápido, pero cambia los números en el último decimal.
# Antes de medir 61.000 libros con él hay que saber CUÁNTO cambia, porque si
# se desviara de verdad, el catálogo entero quedaría con cifras que no
# coinciden con las que la app calcula en vivo.
import numpy as np

muestra = sorted(TEXTOS.glob("*.txt"))[:5]
bloques = []
for r in muestra:
    t = ficha.sin_licencia(r.read_text(encoding="utf-8", errors="ignore"))
    bloques.extend(scoring.fixed_blocks(t, cap=60))
bloques = bloques[:300]
print(f"{len(bloques)} ventanas de prueba")

if MEDIA_PRECISION and bloques:
    y16 = np.array(puntuar_lote(bloques))
    mod = mod.float()
    y32 = np.array(puntuar_lote(bloques))
    mod = mod.half()
    d = np.abs(y16 - y32)
    print(f"desviación fp16 vs fp32 -> media {d.mean():.5f} · máx {d.max():.5f}"
          f"  (escala 0-2)")
    print("Aceptable si el máximo está por debajo de 0.01. Si no lo está, "
          "pon MEDIA_PRECISION = False y vuelve a ejecutar la celda 7.")

# %%
# --- 9. Velocidad real, medida aquí --------------------------------------
# Nada de estimaciones: se cronometra en esta máquina, con este modelo, y de
# ahí sale cuánto va a tardar todo.
if bloques:
    puntuar_lote(bloques[:64])                     # calentar
    t = time.time()
    puntuar_lote(bloques)
    seg = time.time() - t
    vps = len(bloques) / seg
    print(f"{vps:.0f} ventanas/s")
    VENTANAS_POR_LIBRO = 350                       # media razonable
    horas = len(pendientes) * VENTANAS_POR_LIBRO / vps / 3600
    print(f"\n{len(pendientes):,} libros x {VENTANAS_POR_LIBRO} ventanas "
          f"-> {horas:.1f} horas de GPU")
    print("Colab corta las sesiones: reparte en varias tandas. La celda 10 "
          "es reanudable, así que basta con volver a ejecutarla.")

# %%
# --- 10. El precálculo (reanudable, en shards) ---------------------------
# Un archivo por libro serían 61.000 escrituras en Drive y Drive va lentísimo
# con archivos pequeños. Se agrupan de 500 en 500.
import json

POR_SHARD = 500


def hechos_ya() -> set:
    ids = set()
    for s in PERFILES.glob("perfiles_*.jsonl"):
        for linea in s.read_text(encoding="utf-8").splitlines():
            try:
                ids.add(json.loads(linea)["id"])
            except (ValueError, KeyError):
                continue
    return ids


# Titulo y autor salen del CATALOGO de Gutenberg, no del archivo. En un .txt
# el lector no tiene de donde sacarlos y devuelve el nombre del fichero:
# comprobado, Orgullo y Prejuicio se llamaba "pg1342.txt" y no tenia autor.
META = {int(r["Text#"]): (" ".join(str(r["Title"]).split()),
                          " ".join(str(r["Authors"]).split()))
        for _, r in en.iterrows()}


def perfil_de_libro(ruta, ya_leido=None):
    """Recorre el libro ENTERO, capítulo a capítulo, sin muestrear.

    Usa `ficha.capitulos_de_cuerpo`, el MISMO filtro que la app: si aquí se
    escribiera otro parecido, el catálogo quedaría medido sobre un conjunto de
    capítulos distinto del que mide la app y nadie se daría cuenta.

    `ya_leido` lo pasa el hilo lector de la celda 10b con el troceado hecho,
    para que la GPU no espere al disco. Sin él, esta función sigue valiendo
    sola: lee y trocea aquí mismo.
    """
    if ya_leido is not None:
        libro, trozos, marcas = ya_leido
        puntos = puntuar_lote(trozos) if trozos else []
        return _armar_perfil(ruta, libro, marcas, puntos)
    libro = reader.cargar(str(ruta))

    # TODAS las ventanas del libro en UNA sola cola, y una sola llamada a la
    # GPU. Antes se llamaba a `puntuar_lote` una vez por capitulo, y un
    # capitulo tiene entre 7 y 31 ventanas (medido en informe_velocidad.md).
    # Es decir: la tarjeta recibia lotes de ~20 cuando `puntuar_lote` agrupa de
    # 256 en 256. La A100 no estaba lenta, estaba hambrienta -y el banco de
    # pruebas que dio 2.022 ventanas/s medía justo el camino que el precalculo
    # no usaba.
    #
    # Reagrupar no cambia el resultado en ninguna cifra que guardemos, pero
    # conviene decirlo con precision y no de mas: NO es identico bit a bit.
    # Medido sobre Alicia, 112 ventanas: 103 coinciden exactamente y las otras
    # difieren como mucho en 4,8e-07. El motivo es el relleno -`padding=True`
    # rellena hasta la ventana mas larga del lote, asi que la composicion del
    # lote cambia el orden de las sumas en coma flotante-. Como las cifras se
    # guardan redondeadas a tres decimales, una diferencia de 5e-07 no puede
    # mover ninguna, salvo en un empate exacto que no se da en la practica.
    trozos, marcas = [], []
    for n, (i, c) in enumerate(ficha.capitulos_de_cuerpo(libro), 1):
        bs = scoring.fixed_blocks(ficha.sin_licencia(c.texto), cap=10**9)
        if not bs:
            continue
        marcas.append((n, i, c, len(trozos), len(bs)))
        trozos.extend(bs)

    puntos = puntuar_lote(trozos) if trozos else []
    return _armar_perfil(ruta, libro, marcas, puntos)


def _armar_perfil(ruta, libro, marcas, puntos):
    """Junta las puntuaciones con los capitulos. No toca ni disco ni GPU.

    Sale de `perfil_de_libro` para que el bucle de la celda 10b pueda leer
    los libros por delante en varios hilos y dejar aqui solo la aritmetica.
    """
    filas, todas = [], []
    for n, i, c, desde, cuantas in marcas:
        vs = puntos[desde:desde + cuantas]
        if not vs:
            continue
        todas.extend(vs)
        filas.append({"capitulo": n, "titulo": c.titulo[:40], "indice": i,
                      "dificultad": round(sum(vs) / len(vs), 3),
                      "min": round(min(vs), 3), "max": round(max(vs), 3),
                      "ventanas": len(vs), "palabras": c.palabras})
    if not filas:
        return None
    num = int(ruta.stem[2:])
    titulo, autor = META.get(num, (libro.titulo, libro.autor))
    return {"titulo": titulo, "autor": autor,
            "palabras": sum(f["palabras"] for f in filas),
            "ventanas": len(todas),
            # Media sobre TODAS las ventanas del libro. Es el mismo estimador
            # que `ficha.dificultad_global` usa en la app -alli se calcula
            # ponderando las medias de capitulo por su numero de ventanas, que
            # es algebraicamente identico-. Aqui se hace directo sobre los
            # valores crudos porque los tenemos. Lo que NO puede volver a
            # pasar es que uno de los dos haga la media de las medias.
            "dificultad": round(sum(todas) / len(todas), 3),
            "modo": "completo", "filas": filas}


ya = hechos_ya()
print(f"ya calculados: {len(ya):,}")
# `TEXTOS_LISTOS` lo fija la celda 6b: el disco local del entorno si el
# archivo masivo se pudo bajar, y Drive si hubo que caer al respaldo. Se usa
# `globals().get` para que esta celda siga funcionando si alguien ejecuta el
# cuaderno salteado y la 6b no llego a correr.
ORIGEN = globals().get("TEXTOS_LISTOS", TEXTOS)
disponibles = [r for r in sorted(ORIGEN.glob("*.txt"))
               if int(r.stem[2:]) not in ya]
print(f"leyendo los textos de:  {ORIGEN}")
print(f"por calcular:  {len(disponibles):,}")

# %%
# --- 10b. Lanzar una tanda ----------------------------------------------
# Igual que la descarga: todo lo que haya, no una tanda fija.
TANDA = 10 ** 9
HORAS_TOPE_ANALISIS = 8.0

# Cuantos libros se van leyendo por delante mientras la GPU trabaja.
#
# Esto NO es una optimizacion de laboratorio: medido en una A100 el
# precalculo iba a 61 libros/min, o sea ~1 s por libro. Un libro medio son
# unas 350 ventanas, que a 2.022 ventanas/s son 0,17 s de tarjeta. El otro
# 80 % del tiempo la A100 estaba parada esperando a que el FUSE de Google
# Drive entregase un .txt. La tarjeta no estaba lenta: estaba esperando al
# disco, que es el mismo error que ya se cometio una vez agrupando por
# capitulo en vez de por libro.
#
# Un ThreadPoolExecutor vale porque leer de Drive es E/S y suelta el GIL. Se
# leen los textos por delante y se puntuan en el hilo principal, que es el
# unico que toca la GPU: dos hilos escribiendo en CUDA a la vez es pedir un
# problema que no se reproduce.
HILOS_LECTURA = 8
POR_DELANTE = 32

buffer, n_shard = [], len(list(PERFILES.glob("perfiles_*.jsonl")))
inicio, errores = time.time(), 0


def _leer(ruta):
    """Solo lee y trocea. NO toca la GPU: eso se hace en el hilo principal."""
    libro = reader.cargar(str(ruta))
    trozos, marcas = [], []
    for n, (i, c) in enumerate(ficha.capitulos_de_cuerpo(libro), 1):
        bs = scoring.fixed_blocks(ficha.sin_licencia(c.texto), cap=10 ** 9)
        if not bs:
            continue
        marcas.append((n, i, c, len(trozos), len(bs)))
        trozos.extend(bs)
    return ruta, libro, trozos, marcas


def _en_orden(rutas):
    """Va entregando (ruta, libro, trozos, marcas) con POR_DELANTE en vuelo.

    No se usa `executor.map` porque devuelve en orden pero encola TODAS las
    tareas de golpe: con 29.516 libros eso es intentar leer 29.516 archivos
    de Drive a la vez y quedarse sin memoria. Aqui la cola es fija.
    """
    from concurrent.futures import ThreadPoolExecutor
    from collections import deque
    it = iter(rutas)
    with ThreadPoolExecutor(max_workers=HILOS_LECTURA) as pool:
        cola = deque()
        for _ in range(POR_DELANTE):
            try:
                cola.append(pool.submit(_leer, next(it)))
            except StopIteration:
                break
        while cola:
            fut = cola.popleft()
            try:
                cola.append(pool.submit(_leer, next(it)))
            except StopIteration:
                pass
            yield fut


for k, fut in enumerate(_en_orden(disponibles[:TANDA]), 1):
    if time.time() - inicio > HORAS_TOPE_ANALISIS * 3600:
        print(f"  alcanzado el tope de {HORAS_TOPE_ANALISIS} h; guardo lo que "
              f"llevo y paro")
        break
    # `ruta` se pone a None antes del try: si el fallo ocurre DENTRO del hilo
    # lector, `fut.result()` relanza la excepcion aqui y `ruta` no existiria
    # todavia; el except que imprime `ruta.name` reventaria con NameError y
    # se perderia el error de verdad.
    ruta = None
    try:
        ruta, libro, trozos, marcas = fut.result()
        p = perfil_de_libro(ruta, ya_leido=(libro, trozos, marcas))
        if p:
            p["id"] = int(ruta.stem[2:])
            buffer.append(p)
    except Exception as e:
        errores += 1
        if errores <= 5:
            print("  fallo en", ruta.name if ruta else "(al leer)",
                  type(e).__name__, e)
    if len(buffer) >= POR_SHARD:
        destino = PERFILES / f"perfiles_{n_shard:04d}.jsonl"
        destino.write_text("\n".join(json.dumps(x, ensure_ascii=False)
                                     for x in buffer), encoding="utf-8")
        print(f"  guardado {destino.name} ({len(buffer)} libros)")
        buffer, n_shard = [], n_shard + 1
    if k % 100 == 0:
        v = k / (time.time() - inicio)
        queda = (len(disponibles) - k) / v / 3600
        print(f"  {k:,}/{len(disponibles):,} · {v:.2f} libros/s · "
              f"faltarían {queda:.1f} h")

if buffer:
    destino = PERFILES / f"perfiles_{n_shard:04d}.jsonl"
    destino.write_text("\n".join(json.dumps(x, ensure_ascii=False)
                                 for x in buffer), encoding="utf-8")
    print(f"  guardado {destino.name} ({len(buffer)} libros)")

print(f"\ntanda terminada en {(time.time() - inicio) / 60:.1f} min, "
      f"{errores} errores")

# %%
# --- 11. El catálogo final para la app -----------------------------------
# Junta los shards con los metadatos de Gutenberg y deja un CSV que la app
# pueda leer directamente: título, autor, temas, dificultad ya medida.
filas = []
for s in sorted(PERFILES.glob("perfiles_*.jsonl")):
    for linea in s.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linea)
        except ValueError:
            continue
        filas.append({"id": f"PG{d['id']}", "titulo": d["titulo"],
                      "autor": d["autor"], "palabras": d["palabras"],
                      "dificultad": d["dificultad"], "ventanas": d["ventanas"],
                      "capitulos": len(d["filas"])})

perf = pd.DataFrame(filas)
meta = en.rename(columns={"Text#": "num", "Title": "titulo_pg",
                          "Authors": "autor_pg", "Subjects": "temas"})
meta["id"] = "PG" + meta["num"].astype(str)
final = perf.merge(meta[["id", "temas", "titulo_pg", "autor_pg"]],
                   on="id", how="left")

salida = RAIZ / "catalogo_medido.csv"
final.to_csv(salida, index=False)
print(f"{len(final):,} libros medidos -> {salida}")
print(final["dificultad"].describe())
final.head(10)
