"""H02: cuanto vale la fuga del vocabulario.

Reproduce exactamente el pipeline de entrega/notebook_proyecto.py dos veces:

  CONTAMINADO  las 3.000 palabras familiares salen de TODO el corpus
               (lo que hace hoy el cuaderno, linea 820-824)
  LIMPIO       salen SOLO de las filas de entrenamiento

Todo lo demas es identico: misma semilla, misma particion agrupada por obra,
mismos modelos, mismos hiperparametros. La unica diferencia es de donde sale
la lista. Asi la diferencia entre las dos columnas es la fuga y nada mas.
"""
import collections
import os
import re
import urllib.request

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder, StandardScaler

SEMILLA = 42

METRICAS_CORPUS = [
    "Flesch-Reading-Ease", "Flesch-Kincaid-Grade-Level",
    "Automated Readability Index", "SMOG Readability",
    "New Dale-Chall Readability Formula", "CAREC", "CAREC_M", "CML2RI",
    "Google WC", "Sentence Count", "Paragraphs",
]
NIVELES_CEFR = ["C2", "C1", "B2", "B1", "A2", "A1"]
ORDEN_NIVEL = {"C2": 0, "C1": 1, "B2": 2, "B1": 3, "A2": 4, "A1": 5}
TRES_CLASICAS = ["palabras_por_frase", "diversidad_lexica", "palabras_raras"]

PALABRA_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
FRASE_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")

URL_CLEAR = ("https://raw.githubusercontent.com/scrosseye/CLEAR-Corpus/"
             "main/CLEAR_corpus_final.xlsx")
RUTA_CLEAR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "CLEAR_corpus_final.xlsx")


def contar_silabas(palabra):
    return max(1, len(re.findall(r"[aeiouy]+", palabra.lower())))


def rasgos_de_texto(texto, familiares):
    palabras = [w.lower() for w in PALABRA_RE.findall(texto)]
    frases = [f for f in FRASE_RE.findall(texto) if PALABRA_RE.findall(f)]
    n_palabras = max(len(palabras), 1)
    n_frases = max(len(frases), 1)
    silabas = [contar_silabas(w) for w in palabras]
    return {
        "palabras_por_frase": n_palabras / n_frases,
        "diversidad_lexica": len(set(palabras)) / n_palabras,
        "letras_por_palabra": sum(len(w) for w in palabras) / n_palabras,
        "palabras_raras": sum(1 for w in palabras if w not in familiares) / n_palabras,
        "silabas_por_palabra": sum(silabas) / n_palabras,
        "polisilabas": sum(1 for s in silabas if s >= 3) / n_palabras,
    }


def vocabulario(textos):
    contador = collections.Counter()
    for t in textos:
        contador.update(w.lower() for w in PALABRA_RE.findall(t))
    return set(w for w, _ in contador.most_common(3000))


if not os.path.exists(RUTA_CLEAR):
    print("descargando CLEAR...")
    urllib.request.urlretrieve(URL_CLEAR, RUTA_CLEAR)

clear = pd.read_excel(RUTA_CLEAR)
print("CLEAR:", clear.shape[0], "filas")

# La particion no depende de los valores de X, solo de los grupos, del numero
# de filas y de la semilla. Por eso se puede calcular ANTES de construir los
# rasgos y sale identica a la del cuaderno.
grupos = clear["Title"].values
y_modelo = clear["BT_easiness"].values
particion = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SEMILLA)
idx_train, idx_test = next(particion.split(np.zeros(len(clear)), y_modelo, grupos))
print("entrenamiento:", len(idx_train), "| prueba:", len(idx_test))
print("titulos compartidos:",
      len(set(clear["Title"].iloc[idx_train]) & set(clear["Title"].iloc[idx_test])))

nivel_cefr = pd.qcut(clear["BT_easiness"], q=6, labels=NIVELES_CEFR)
y_nivel = pd.Series(nivel_cefr.astype(str))
codigo_real = y_nivel.iloc[idx_test].map(ORDEN_NIVEL).values

voc_todo = vocabulario(clear["Excerpt"])
voc_train = vocabulario(clear["Excerpt"].iloc[idx_train])
print("palabras que cambian entre las dos listas:",
      len(voc_todo ^ voc_train), "de 3.000")

filas = []


def correr(etiqueta, familiares):
    rasgos = pd.DataFrame([rasgos_de_texto(t, familiares) for t in clear["Excerpt"]])
    X_modelo = pd.concat([clear[METRICAS_CORPUS].reset_index(drop=True), rasgos],
                         axis=1)
    escalador = StandardScaler().fit(X_modelo.iloc[idx_train])
    X_train = escalador.transform(X_modelo.iloc[idx_train])
    X_test = escalador.transform(X_modelo.iloc[idx_test])
    y_train, y_test = y_modelo[idx_train], y_modelo[idx_test]

    def reg(nombre, pred):
        filas.append({
            "modelo": nombre, "version": etiqueta,
            "MAE": round(float(mean_absolute_error(y_test, pred)), 4),
            "RMSE": round(float(np.sqrt(np.mean((pred - y_test) ** 2))), 4),
            "Spearman": round(float(spearmanr(pred, y_test)[0]), 4),
        })

    def clf(nombre, pred):
        cod = pd.Series(pred).astype(str).map(ORDEN_NIVEL).values
        filas.append({
            "modelo": nombre, "version": etiqueta,
            "exactitud": round(float(accuracy_score(y_nivel.iloc[idx_test], pred)), 4),
            "error_ordinal": round(float(np.abs(codigo_real - cod).mean()), 4),
        })

    ind_metricas = [X_modelo.columns.get_loc(c) for c in METRICAS_CORPUS]
    reg("lineal 11 metricas",
        LinearRegression().fit(X_train[:, ind_metricas], y_train)
        .predict(X_test[:, ind_metricas]))
    reg("lineal 17 variables",
        LinearRegression().fit(X_train, y_train).predict(X_test))
    reg("random forest 300",
        RandomForestRegressor(n_estimators=300, random_state=SEMILLA, n_jobs=-1)
        .fit(X_train, y_train).predict(X_test))

    ind_tres = [X_modelo.columns.get_loc(c) for c in TRES_CLASICAS]
    clf("logistica 3 clasicas",
        LogisticRegression(max_iter=1000)
        .fit(X_train[:, ind_tres], y_nivel.iloc[idx_train])
        .predict(X_test[:, ind_tres]))
    clf("logistica 17 variables",
        LogisticRegression(max_iter=1000).fit(X_train, y_nivel.iloc[idx_train])
        .predict(X_test))
    try:
        from xgboost import XGBClassifier
        codificador = LabelEncoder().fit(y_nivel.iloc[idx_train])
        xgb = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8,
                            eval_metric="mlogloss", random_state=SEMILLA)
        xgb.fit(X_train, codificador.transform(y_nivel.iloc[idx_train]))
        clf("xgboost 17 variables",
            codificador.inverse_transform(xgb.predict(X_test)))
    except ImportError:
        print("sin xgboost en este entorno")

    # La correlacion suelta que el cuaderno ya reportaba como -0,486.
    corr = spearmanr(rasgos["palabras_raras"], clear["BT_easiness"])[0]
    filas.append({"modelo": "corr. palabras_raras vs BT_easiness",
                  "version": etiqueta, "Spearman": round(float(corr), 4)})


correr("contaminado", voc_todo)
correr("limpio", voc_train)

tabla = pd.DataFrame(filas)
print()
print("=" * 78)
for nombre in tabla["modelo"].unique():
    sub = tabla[tabla["modelo"] == nombre].set_index("version")
    print()
    print(nombre)
    print(sub.drop(columns="modelo").dropna(axis=1, how="all").to_string())

tabla.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "h02_resultados.csv"), index=False)
print()
print("guardado h02_resultados.csv")
