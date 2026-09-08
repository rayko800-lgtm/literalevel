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
# **Ojo con dos cosas:**
# - Los textos ocupan unos 20 GB en Drive. Hay 400 GB, así que caben.
# - Escribir 61.000 archivos sueltos en Drive es lentísimo. Por eso los
#   resultados van en *shards* de 500 libros, no en un archivo por libro.

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

# --- Contenido adulto fuera ------------------------------------------------
# Esto NO es curaduría moral, y por eso el filtro es corto y se apoya solo en
# las materias que el propio Gutenberg asigna. El motivo es concreto: al
# ordenar por descargas, el CUARTO libro más bajado de todo Gutenberg es "The
# Romance of Lust", cuyas materias son "Incest -- Fiction; Pornography;
# Rape -- Fiction". LiteraLevel la usa una lectora de quince años y se va a
# enseñar a un profesor. Un catálogo que abre con eso es un catálogo roto.
#
# Son 90 libros de 61.642: se quita lo inequívoco y no se toca nada más. Los
# clásicos con sexo -Lady Chatterley, Ulises- no llevan estas materias y se
# quedan, que es lo correcto: el criterio es la etiqueta explícita del
# catálogo, no el juicio de nadie sobre la obra.
_ADULTO = r"[Ee]rotic|Pornograph|Sex customs"
_marca = (en["Subjects"].astype(str).str.contains(_ADULTO, na=False)
          | en["Bookshelves"].astype(str).str.contains(_ADULTO, na=False))
print(f"fuera por materia adulta explícita: {int(_marca.sum())}")
en = en[~_marca].copy()
print(f"catálogo utilizable: {len(en):,}")
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


def descargar(n: int) -> bool:
    destino = TEXTOS / f"pg{n}.txt"
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
# --- 6b. El bucle de descarga (se puede cortar y reanudar) ---------------
# Ejecuta esta celda las veces que haga falta. Baja un lote y para, para que
# se pueda ir viendo el avance sin dejar la sesión colgada horas.
LOTE = 2000

hechos = fallos = 0
inicio = time.time()
for n in pendientes:
    if (TEXTOS / f"pg{n}.txt").exists():
        continue
    if descargar(n):
        hechos += 1
    else:
        fallos += 1
    if hechos and hechos % 100 == 0:
        v = hechos / (time.time() - inicio)
        print(f"  {hechos:,} bajados · {fallos} fallidos · {v:.1f}/s")
    if hechos >= LOTE:
        break

total = len(list(TEXTOS.glob("*.txt")))
print(f"\nlote terminado: +{hechos}, {fallos} fallidos")
print(f"total en Drive: {total:,} de {len(pendientes):,} "
      f"({100 * total / len(pendientes):.1f}%)")

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


def perfil_de_libro(ruta):
    """Recorre el libro ENTERO, capítulo a capítulo, sin muestrear.

    Usa `ficha.capitulos_de_cuerpo`, el MISMO filtro que la app: si aquí se
    escribiera otro parecido, el catálogo quedaría medido sobre un conjunto de
    capítulos distinto del que mide la app y nadie se daría cuenta.
    """
    libro = reader.cargar(str(ruta))
    filas, todas = [], []
    for n, (i, c) in enumerate(ficha.capitulos_de_cuerpo(libro), 1):
        vs = puntuar_lote(scoring.fixed_blocks(ficha.sin_licencia(c.texto),
                                               cap=10**9))
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
            "dificultad": round(sum(todas) / len(todas), 3),
            "modo": "completo", "filas": filas}


ya = hechos_ya()
print(f"ya calculados: {len(ya):,}")
disponibles = [r for r in sorted(TEXTOS.glob("*.txt"))
               if int(r.stem[2:]) not in ya]
print(f"por calcular:  {len(disponibles):,}")

# %%
# --- 10b. Lanzar una tanda ----------------------------------------------
TANDA = 2000            # súbelo si la sesión aguanta

buffer, n_shard = [], len(list(PERFILES.glob("perfiles_*.jsonl")))
inicio, errores = time.time(), 0

for k, ruta in enumerate(disponibles[:TANDA], 1):
    try:
        p = perfil_de_libro(ruta)
        if p:
            p["id"] = int(ruta.stem[2:])
            buffer.append(p)
    except Exception as e:
        errores += 1
        if errores <= 5:
            print("  fallo en", ruta.name, type(e).__name__, e)
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
