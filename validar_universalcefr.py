"""Valida el v4 con UniversalCEFR, SIN medir sobre su propio entrenamiento.

Uso:  python -X utf8 validar_universalcefr.py

EL HALLAZGO QUE OBLIGO A REESCRIBIRLO (12 de septiembre de 2026).
La primera version de este guion validaba con dos conjuntos de UniversalCEFR
-`cambridge_exams_en` y `elg_cefr_en`- y daba Spearman 0,946. Era mas alto que
la validacion interna del propio v4 (0,908), y eso ya era sospechoso. Leyendo
el guion de entrenamiento del v4 (`ll_v4_transformer.py`, en el Drive del
proyecto) salio la causa, sin ambiguedad:

    DATA_PATH = DRIVE / "elg-cefr-en.json"
    "source": "ELG CEFR English, CC BY-NC-SA 4.0"
    train_test_split(docs, test_size=0.22, ...)   -> 510 / 144 documentos

**El v4 se entreno con ELG CEFR English**, que es el mismo `elg_cefr_en` de
UniversalCEFR (654 aceptados + 57 descartados = 711; el conjunto tiene 712). Y
`cambridge_exams_en` comparte 130 textos con el. Asi que aquel 0,946 era, en su
mayor parte, medir el modelo sobre textos con los que se entreno.

AHORA:
- `elg_cefr_en` es el corpus de ENTRENAMIENTO y no se evalua.
- De `cambridge_exams_en` solo cuenta lo que NO esta en ELG: ni identico (hash
  del texto normalizado) ni casi identico (la mitad o mas de sus 8-gramas de
  palabras dentro de un mismo texto de ELG, para cazar extractos y versiones
  con otra puntuacion).
- Lo contaminado se mide aparte y se imprime al lado, para que la diferencia se
  vea y no haya que creersela.

Se imprimen puntuaciones, nunca texto. Licencia de los datos: CC BY-NC-SA 4.0;
referencia: Imperial et al., UniversalCEFR, EMNLP 2025.
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

ENTRENAMIENTO = ("UniversalCEFR/elg_cefr_en", "elg-cefr-en.json")
EVALUACION = ("UniversalCEFR/cambridge_exams_en", "cambridge_exams.json")
MINIMO_PALABRAS = 150          # el mismo suelo que `scoring.continuous_prose`
N_GRAMA = 8
UMBRAL_CONTENIDO = 0.5         # fraccion de 8-gramas del texto dentro de uno de ELG
BASE = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

RUTA_MODELO = os.environ.get("LITERALEVEL_MODELO",
                             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "modelo_v4"))
if not os.path.isdir(RUTA_MODELO):
    sys.exit(f"No encuentro el modelo en {RUTA_MODELO}. "
             "Ponlo en ./modelo_v4 o define LITERALEVEL_MODELO.")


def _cargar(repo, archivo):
    return pd.read_json(hf_hub_download(repo, archivo, repo_type="dataset"))


def _norm(t):
    return re.sub(r"\s+", " ", str(t)).strip().lower()


def _huella(t):
    return hashlib.sha1(_norm(t).encode()).hexdigest()


def _gramas(t):
    toks = re.findall(r"[a-z0-9']+", _norm(t))
    return {" ".join(toks[i:i + N_GRAMA]) for i in range(max(0, len(toks) - N_GRAMA + 1))}


def _ordinal(nivel):
    nivel = str(nivel).strip().upper()
    base = BASE.get(nivel[:2])
    return None if base is None else base + (0.5 if nivel.endswith("+") else 0.0)


# --- 1. Que textos de Cambridge estan en el entrenamiento -------------------
elg = _cargar(*ENTRENAMIENTO)
cam = _cargar(*EVALUACION)
huellas_elg = set(elg["text"].map(_huella))
indice = defaultdict(set)                       # 8-grama -> textos de ELG
for i, t in enumerate(elg["text"]):
    for g in _gramas(t):
        indice[g].add(i)

estado = []
for t in cam["text"]:
    if _huella(t) in huellas_elg:
        estado.append("identico")
        continue
    g = _gramas(t)
    comunes = defaultdict(int)
    for x in g:
        for j in indice.get(x, ()):
            comunes[j] += 1
    mayor = max(comunes.values(), default=0)
    estado.append("casi_identico" if g and mayor / len(g) >= UMBRAL_CONTENIDO else "limpio")
cam["estado"] = estado
cam["h"] = cam["text"].map(_huella)
cam = cam.drop_duplicates("h").reset_index(drop=True)

print(f"Entrenamiento del v4 (ELG CEFR English): {len(elg)} textos")
print(f"cambridge_exams_en sin repetir: {len(cam)}")
for e in ("identico", "casi_identico", "limpio"):
    print(f"  {e:<14} {int((cam['estado'] == e).sum())}")

cam["palabras"] = cam["text"].astype(str).map(lambda t: len(words(t)))
cam["ordinal"] = cam["cefr_level"].map(_ordinal)
cam = cam[(cam["palabras"] >= MINIMO_PALABRAS) & cam["ordinal"].notna()]
print(f"con al menos {MINIMO_PALABRAS} palabras: {len(cam)} "
      f"(limpios: {int((cam['estado'] == 'limpio').sum())})\n")

# --- 2. Puntuar ------------------------------------------------------------
p = Puntuador(RUTA_MODELO)
t0 = time.time()
puntos, rechazados = [], 0
for t in cam["text"]:
    try:
        puntos.append(float(p.puntuar(str(t)).puntuacion))
    except ValueError:
        puntos.append(float("nan"))
        rechazados += 1
cam["puntuacion"] = puntos
cam = cam[cam["puntuacion"].notna()]
print(f"puntuados {len(cam)} en {(time.time() - t0) / 60:.1f} min · rechazados por el "
      f"filtro de prosa (listas, tablas): {rechazados}")


# --- 3. Metricas: las mismas de validar_local.py ----------------------------
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
    print(f"\n{rotulo} ({len(df)} textos)")
    por = df.groupby(df["cefr_level"].astype(str).str.upper().str[:2])["puntuacion"]
    for niv in sorted(por.groups, key=BASE.get):
        v = por.get_group(niv)
        print(f"  {niv}  n={len(v):>3}  media={v.mean():.4f}  desv={v.std(ddof=0):.3f}")
    if len(df) < 3:
        return None
    niv, mod, pal = df["ordinal"].tolist(), df["puntuacion"].tolist(), df["palabras"].tolist()
    s_mod, s_pal, s_mp = _spearman(mod, niv), _spearman(pal, niv), _spearman(mod, pal)
    den = (1 - s_mp ** 2) * (1 - s_pal ** 2)
    parcial = (s_mod - s_mp * s_pal) / np.sqrt(den) if den > 0 else float("nan")
    print(f"  Spearman modelo v4 contra nivel           {s_mod:.3f}")
    print(f"  Spearman contar palabras, sin modelo      {s_pal:.3f}")
    print(f"  modelo descontando la longitud (parcial)  {parcial:.3f}")
    medias = [por.get_group(n).mean() for n in sorted(por.groups, key=BASE.get)
              if len(por.get_group(n)) >= 5]
    return all(a < b for a, b in zip(medias, medias[1:]))


limpio = cam[cam["estado"] == "limpio"]
sucio = cam[cam["estado"] != "limpio"]
creciente = _bloque(limpio, "LIMPIO: Cambridge fuera del entrenamiento (la validacion que vale)")
_bloque(sucio, "CONTAMINADO: Cambridge que esta en ELG (solo para comparar, NO es validacion)")

print()
if creciente:
    print(f"VALIDACION LIMPIA CORRECTA: {len(limpio)} textos, medias crecientes "
          f"en los niveles con al menos 5 textos.")
else:
    print("VALIDACION LIMPIA FALLIDA: las medias no son crecientes o no hay textos suficientes.")
print("\n(no se imprime ni un fragmento de texto)")
sys.exit(0 if creciente else 1)
