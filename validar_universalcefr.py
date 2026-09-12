"""Valida el v4 contra los textos de referencia en ingles de UniversalCEFR.

Uso:  python -X utf8 validar_universalcefr.py

Hermano de `validar_local.py`, con dos diferencias que importan:

1. **Este corpus SI se puede reconstruir desde cualquier maquina.** Son dos
   conjuntos publicos de Hugging Face, sin terminos que aceptar, con licencia
   CC BY-NC-SA 4.0: `UniversalCEFR/cambridge_exams_en` (331 textos, A2-C2) y
   `UniversalCEFR/elg_cefr_en` (712 textos, A1-C2). Referencia: Imperial et
   al., *UniversalCEFR*, EMNLP 2025. El guion se los baja solo.
2. **Es un orden de magnitud mayor**: 838 textos con al menos 150 palabras,
   frente a los 47 del British Council.

LOS DOS CONJUNTOS SE SOLAPAN, y eso no se puede ignorar. Medido el 12 de
septiembre de 2026: 130 textos estan en los dos, y en los 136 pares de filas
el nivel coincide. Si se concatenaran sin mas, esos textos contarian dos veces
y la n estaria inflada. Se deduplica por el texto normalizado.

Los niveles con "+" (A2+, B1+, B2+) se cuentan como medio escalon por encima
del suyo para Spearman, y se agrupan con su nivel base para las medias.

Se imprimen puntuaciones, nunca texto: es la misma norma que con el British
Council, aunque aqui la licencia permitiria citar.
"""
import hashlib
import os
import re
import sys
import time
import warnings
from collections import defaultdict

warnings.filterwarnings("ignore")
sys.path.insert(0, "app")
import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download
from scoring import Puntuador, words

FUENTES = [("UniversalCEFR/cambridge_exams_en", "cambridge_exams.json"),
           ("UniversalCEFR/elg_cefr_en", "elg-cefr-en.json")]
MINIMO_PALABRAS = 150          # el mismo suelo que `scoring.continuous_prose`
BASE = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

RUTA_MODELO = os.environ.get("LITERALEVEL_MODELO",
                             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "modelo_v4"))
if not os.path.isdir(RUTA_MODELO):
    sys.exit(f"No encuentro el modelo en {RUTA_MODELO}. "
             "Ponlo en ./modelo_v4 o define LITERALEVEL_MODELO.")


def _huella(t):
    return hashlib.sha1(re.sub(r"\s+", " ", str(t)).strip().lower().encode()).hexdigest()


def _ordinal(nivel):
    nivel = str(nivel).strip().upper()
    base = BASE.get(nivel[:2])
    if base is None:
        return None
    return base + (0.5 if nivel.endswith("+") else 0.0)


# --- El corpus, deduplicado ------------------------------------------------
partes = []
for repo, archivo in FUENTES:
    df = pd.read_json(hf_hub_download(repo, archivo, repo_type="dataset"))
    df["fuente"] = repo.split("/")[1]
    partes.append(df)
todo = pd.concat(partes, ignore_index=True)
todo["h"] = todo["text"].map(_huella)
filas_brutas = len(todo)
todo = todo.drop_duplicates("h").reset_index(drop=True)
unicos = len(todo)
todo["palabras"] = todo["text"].astype(str).map(lambda t: len(words(t)))
todo["ordinal"] = todo["cefr_level"].map(_ordinal)
cortos = todo["palabras"] < MINIMO_PALABRAS
sin_nivel = todo["ordinal"].isna()
todo = todo[~cortos & ~sin_nivel]
print(f"filas: {filas_brutas} · sin repetir: {unicos} "
      f"(repetidas: {filas_brutas - unicos})")
print(f"  por debajo de {MINIMO_PALABRAS} palabras: {int(cortos.sum())} · "
      f"sin nivel legible: {int(sin_nivel.sum())}")
print(f"  se evaluan: {len(todo)}\n")

# --- Puntuar ---------------------------------------------------------------
p = Puntuador(RUTA_MODELO)
print("modelo v4 cargado")
t0 = time.time()
puntos, fallidos = [], []
for k, (_, fila) in enumerate(todo.iterrows(), 1):
    try:
        puntos.append(float(p.puntuar(str(fila["text"])).puntuacion))
    except Exception as e:
        puntos.append(float("nan"))
        fallidos.append(f"{fila['fuente']} / {fila.get('title', '?')}: {type(e).__name__}: {e}")
    if k % 100 == 0:
        print(f"  {k}/{len(todo)} · {(time.time() - t0) / k:.2f} s por texto")
todo["puntuacion"] = puntos
todo = todo[todo["puntuacion"].notna()]
print(f"puntuados {len(todo)} en {(time.time() - t0) / 60:.1f} min · fallidos {len(fallidos)}")
for f in fallidos[:10]:
    print("   ", f)


# --- Metricas: las mismas de validar_local.py ------------------------------
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


def _bloque(df, rotulo):
    niv, mod, pal = df["ordinal"].tolist(), df["puntuacion"].tolist(), df["palabras"].tolist()
    s_mod, s_pal, s_mp = _spearman(mod, niv), _spearman(pal, niv), _spearman(mod, pal)
    den = (1 - s_mp ** 2) * (1 - s_pal ** 2)
    parcial = (s_mod - s_mp * s_pal) / np.sqrt(den) if den > 0 else float("nan")
    print(f"\n{rotulo} ({len(df)} textos)")
    print(f"  Spearman modelo v4 contra nivel           {s_mod:.3f}")
    print(f"  Spearman contar palabras, sin modelo      {s_pal:.3f}")
    print(f"  modelo descontando la longitud (parcial)  {parcial:.3f}")
    print(f"  (modelo contra longitud                   {s_mp:.3f})")
    return s_mod


print(f"\n{'nivel':<6}{'n':>5}{'media 0-2':>12}{'desv (pobl.)':>14}")
por_base = defaultdict(list)
for _, f in todo.iterrows():
    por_base[str(f["cefr_level"]).strip().upper()[:2]].append(f["puntuacion"])
for niv in sorted(por_base, key=BASE.get):
    v = por_base[niv]
    print(f"{niv:<6}{len(v):>5}{np.mean(v):>12.4f}{np.std(v):>14.3f}")

_bloque(todo, "Los dos conjuntos, sin repetir")
for fuente, df in todo.groupby("fuente"):
    _bloque(df, f"Solo {fuente}")

# --- Tambien este validador tiene que poder SUSPENDER ----------------------
problemas = []
medias = [np.mean(por_base[n]) for n in sorted(por_base, key=BASE.get)]
if len(medias) < 5:
    problemas.append(f"solo hay {len(medias)} niveles evaluados")
if not all(a < b for a, b in zip(medias, medias[1:])):
    problemas.append("las medias por nivel NO son estrictamente crecientes")
for niv, v in por_base.items():
    if len(v) < 10:
        problemas.append(f"{niv} solo tiene {len(v)} textos")

print()
if problemas:
    print("VALIDACION FALLIDA:")
    for x in problemas:
        print("  -", x)
else:
    print(f"VALIDACION CORRECTA: {len(todo)} textos, {len(medias)} niveles, "
          f"medias estrictamente crecientes.")
print("\n(no se imprime ni un fragmento de texto)")
sys.exit(1 if problemas else 0)
