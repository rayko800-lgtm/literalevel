"""Validacion EXTERNA del v4 con OneStopEnglish: un corpus que sus pesos no vieron.

Uso:  python -X utf8 validar_onestop.py

POR QUE ESTA SI VALE. El v4 se entreno solo con ELG CEFR English
(`entrenamiento_v4/ll_v4_transformer.py`: un unico `DATA_PATH`). Comprobado el
12 de septiembre de 2026, y este guion lo vuelve a comprobar cada vez: ningun
texto de OneStopEnglish comparte con ELG ni un solo 8-grama de palabras. La
comprobacion va DENTRO del guion a proposito: la validacion anterior con
UniversalCEFR se publico sin ella y resulto estar midiendo el entrenamiento.

UN MATIZ QUE NO SE ESCONDE. OneStopEnglish si se uso para desarrollar modelos
ANTERIORES: el v2 se afino con el, y en esas pruebas se decidio, por ejemplo,
leer los textos por ventanas. Los pesos del v4 no lo vieron nunca; el diseno del
proceso si se informo de el. Es externo para el modelo, no virgen para el
proyecto.

EL CORPUS. Vajjala y Lucic (2018), CC BY-SA 4.0: articulos de noticias escritos
tres veces, en nivel Elementary, Intermediate y Advanced. Se descarga solo de
GitHub. Como el mismo articulo aparece en los tres niveles, ademas de Spearman
se mide lo mas limpio que tiene este corpus: **dentro de cada articulo**, si el
modelo ordena bien sus tres versiones. Ahi el tema es el mismo por construccion,
asi que lo que se mide es la dificultad y no de que va el texto.

Mismo proceso que la aplicacion (`scoring.Puntuador`) y las mismas metricas que
`validar_local.py`. Se imprimen puntuaciones, nunca texto.
"""
import hashlib
import io
import os
import re
import sys
import time
import urllib.request
import warnings
import zipfile
from collections import defaultdict

warnings.filterwarnings("ignore")
sys.path.insert(0, "app")
import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download
from scoring import Puntuador, words

URL_ONESTOP = ("https://github.com/nishkalavallabhi/OneStopEnglishCorpus/"
               "archive/refs/heads/master.zip")
NIVELES = {"Ele-Txt": ("Elementary", 1), "Int-Txt": ("Intermediate", 2),
           "Adv-Txt": ("Advanced", 3)}
N_GRAMA = 8

RUTA_MODELO = os.environ.get("LITERALEVEL_MODELO",
                             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "modelo_v4"))
if not os.path.isdir(RUTA_MODELO):
    sys.exit(f"No encuentro el modelo en {RUTA_MODELO}. "
             "Ponlo en ./modelo_v4 o define LITERALEVEL_MODELO.")


def _norm(t):
    return re.sub(r"\s+", " ", str(t)).strip().lower()


def _gramas(t):
    toks = re.findall(r"[a-z0-9']+", _norm(t))
    return {" ".join(toks[i:i + N_GRAMA]) for i in range(max(0, len(toks) - N_GRAMA + 1))}


def _articulo(nombre):
    """El mismo articulo en sus tres niveles comparte nombre salvo el sufijo."""
    base = os.path.splitext(os.path.basename(nombre))[0]
    return re.sub(r"(?i)[-_ ]*(ele|int|adv|elementary|intermediate|advanced)$", "", base).strip()


# --- 1. El corpus, sin repetidos ------------------------------------------
z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(URL_ONESTOP, timeout=180).read()))
filas, vistos = [], set()
for n in z.namelist():
    carpeta = n.split("/")[-2] if n.count("/") >= 2 else ""
    if carpeta not in NIVELES or not n.lower().endswith(".txt"):
        continue
    crudo = z.read(n).decode("utf-8", "ignore")
    # Una linea que es solo el nombre del nivel no es texto del articulo.
    lineas = [l for l in crudo.splitlines()
              if l.strip().lower() not in ("elementary", "intermediate", "advanced", "adv", "ele", "int")]
    texto = "\n".join(lineas).strip()
    h = hashlib.sha1(_norm(texto).encode()).hexdigest()
    if h in vistos:
        continue
    vistos.add(h)
    etiqueta, orden = NIVELES[carpeta]
    filas.append({"articulo": _articulo(n), "nivel": etiqueta, "ordinal": orden, "texto": texto})
df = pd.DataFrame(filas)
print(f"OneStopEnglish sin repetir: {len(df)} textos, {df['articulo'].nunique()} articulos")
print("  " + " · ".join(f"{e}: {int((df['nivel'] == e).sum())}" for e, _ in NIVELES.values()))

# --- 2. La comprobacion de fuga, dentro del guion --------------------------
elg = pd.read_json(hf_hub_download("UniversalCEFR/elg_cefr_en", "elg-cefr-en.json",
                                   repo_type="dataset"))
gramas_elg = set()
for t in elg["text"]:
    gramas_elg |= _gramas(t)
compartidos = [len(_gramas(t) & gramas_elg) / max(1, len(_gramas(t))) for t in df["texto"]]
df["compartido_con_elg"] = compartidos
contaminados = int((df["compartido_con_elg"] >= 0.5).sum())
print(f"\nFuga contra el entrenamiento del v4 (ELG CEFR English, {len(elg)} textos):")
print(f"  fraccion maxima de 8-gramas compartidos: {max(compartidos):.3f}")
print(f"  textos con la mitad o mas compartida: {contaminados}")
if contaminados:
    print("  -> se EXCLUYEN de la validacion")
    df = df[df["compartido_con_elg"] < 0.5]

# --- 3. Puntuar -------------------------------------------------------------
p = Puntuador(RUTA_MODELO)
t0 = time.time()
puntos, rechazados = [], 0
for k, t in enumerate(df["texto"], 1):
    try:
        puntos.append(float(p.puntuar(t).puntuacion))
    except ValueError:
        puntos.append(float("nan"))
        rechazados += 1
    if k % 100 == 0:
        print(f"  {k}/{len(df)} · {(time.time() - t0) / k:.2f} s por texto")
df["puntuacion"] = puntos
df["palabras"] = df["texto"].map(lambda t: len(words(t)))
df = df[df["puntuacion"].notna()]
print(f"puntuados {len(df)} en {(time.time() - t0) / 60:.1f} min · rechazados por el "
      f"filtro de prosa: {rechazados}")

# UNA puntuacion por articulo y nivel. La carpeta Intermediate del repositorio
# trae DOS copias de cada articulo, con diferencias de un punado de palabras
# (Amazon-int.txt: 513 y 518). Contarlas como dos textos daba doble peso a ese
# nivel en Spearman y en las medias, y la primera version del orden dentro de
# cada articulo llegaba a comparar las dos copias entre si. Se promedian: el
# diseno del corpus es un articulo escrito una vez por nivel, 189 x 3.
dobles = int((df.groupby(["articulo", "ordinal"]).size() > 1).sum())
df = (df.groupby(["articulo", "nivel", "ordinal"], as_index=False)
        .agg(puntuacion=("puntuacion", "mean"), palabras=("palabras", "mean")))
print(f"articulo-nivel con mas de un archivo, promediados: {dobles} · "
      f"unidades de medida: {len(df)}")


# --- 4. Metricas --------------------------------------------------------------
def _rangos(v):
    orden = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and v[orden[j + 1]] == v[orden[i]]:
            j += 1
        for k in range(i, j + 1):
            r[orden[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return np.array(r)


def _pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    da, db = a - a.mean(), b - b.mean()
    den = float(np.sqrt((da ** 2).sum() * (db ** 2).sum()))
    return float("nan") if den == 0 else float((da * db).sum() / den)


def _spearman(a, b):
    return _pearson(_rangos(list(a)), _rangos(list(b)))


print(f"\n{'nivel':<14}{'n':>5}{'media 0-2':>12}{'desv (pobl.)':>14}")
medias = []
for etiqueta, orden in sorted(NIVELES.values(), key=lambda x: x[1]):
    v = df.loc[df["nivel"] == etiqueta, "puntuacion"]
    medias.append(v.mean())
    print(f"{etiqueta:<14}{len(v):>5}{v.mean():>12.4f}{v.std(ddof=0):>14.3f}")

s_mod = _spearman(df["puntuacion"], df["ordinal"])
s_pal = _spearman(df["palabras"], df["ordinal"])
s_mp = _spearman(df["puntuacion"], df["palabras"])
den = (1 - s_mp ** 2) * (1 - s_pal ** 2)
parcial = (s_mod - s_mp * s_pal) / np.sqrt(den) if den > 0 else float("nan")
print(f"\nSpearman modelo v4 contra nivel           {s_mod:.3f}")
print(f"Spearman contar palabras, sin modelo      {s_pal:.3f}")
print(f"modelo descontando la longitud (parcial)  {parcial:.3f}")

# Dentro de cada articulo: las tres versiones, ordenadas.
#
# OJO, y costo una cifra mal calculada: la carpeta Intermediate trae DOS archivos
# por articulo. La primera version de este bloque ordenaba las puntuaciones por
# nivel y cogia las tres primeras, asi que con dos Intermediate a veces comparaba
# dos versiones del MISMO nivel entre si. Ahora se promedia por articulo y nivel
# ANTES de comparar: cada articulo aporta exactamente una puntuacion por nivel.
por_art = (df.groupby(["articulo", "ordinal"])["puntuacion"].mean()
           .unstack("ordinal"))
completos = por_art.dropna(subset=[1, 2, 3])
n_art = len(completos)
if n_art:
    e, i, a = completos[1], completos[2], completos[3]
    bien = int(((e < i) & (i < a)).sum())
    parejas_bien = int((e < i).sum() + (i < a).sum() + (e < a).sum())
    print(f"\nDentro de cada articulo ({n_art} con sus tres niveles; "
          f"{dobles} parejas articulo-nivel con mas de un archivo, promediadas):")
    print(f"  orden completo Elementary < Intermediate < Advanced: {bien}/{n_art} "
          f"({100 * bien / n_art:.1f} %)")
    print(f"  parejas bien ordenadas: {parejas_bien}/{3 * n_art} "
          f"({100 * parejas_bien / (3 * n_art):.1f} %)")
    print(f"    Elementary < Intermediate: {int((e < i).sum())}/{n_art}")
    print(f"    Intermediate < Advanced:   {int((i < a).sum())}/{n_art}")
    print(f"    Elementary < Advanced:     {int((e < a).sum())}/{n_art}")

# Las puntuaciones, sin texto, para no tener que volver a medir.
df[["articulo", "nivel", "puntuacion", "palabras"]].to_csv(
    "auditoria/validacion_onestop_puntuaciones.csv", index=False)
print("\npuntuaciones guardadas (sin texto) en auditoria/validacion_onestop_puntuaciones.csv")

creciente = all(a < b for a, b in zip(medias, medias[1:]))
print()
print(("VALIDACION CORRECTA" if creciente else "VALIDACION FALLIDA") +
      f": {len(df)} textos, medias {'estrictamente crecientes' if creciente else 'NO crecientes'}.")
print("\n(no se imprime ni un fragmento de texto)")
sys.exit(0 if creciente else 1)
