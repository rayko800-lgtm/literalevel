# %% [markdown]
# # LiteraLevel — cuadernillo del proyecto
#
# **Diplomado en Ciencia de Datos, FES Acatlán (UNAM) · Generación 34**
# **Módulo 5, proyecto integrador · Mtro. Fernando Barranco Rodríguez**
#
# Estimar la dificultad de un texto en inglés para un lector hispanohablante, y
# usar esa estimación para que el lector elija bien qué libro abrir.
#
# ---
#
# ## Índice
#
# 1. Introducción
# 2. Planteamiento del problema
# 3. Descripción de los datos: fuente, calidad y relevancia
# 4. Análisis exploratorio: univariado · bivariado · multivariado
# 5. Procesamiento de datos, con la justificación de cada transformación
# 6. Modelación
# 7. Evaluación
# 8. Estrategia de negocio
# 9. Conclusiones y recomendaciones

# %% [markdown]
# ## Antes de ejecutar: qué corre y qué no
#
# Este cuadernillo está escrito para abrirse en **cualquier Colab y ejecutarse de
# principio a fin sin errores**. Tres decisiones lo hacen posible:
#
# - **No instala nada.** Todo lo que usa (`pandas`, `numpy`, `matplotlib`,
#   `seaborn`, `scipy`, `scikit-learn`, `openpyxl`, `xgboost`) viene ya en la
#   imagen de Colab. No hay una sola celda `!pip install`, que es de donde salen
#   la mayoría de los avisos y de los conflictos de versiones.
# - **Los datos se descargan desde URL públicas dentro del propio cuadernillo.**
#   Nada de `drive.mount`, nada de rutas locales. Kaggle no se usa: el módulo lo
#   prohíbe expresamente, y las dos fuentes de este proyecto son un corpus
#   académico publicado en GitHub y el catálogo oficial de Project Gutenberg.
# - **No entrena la red neuronal.** El modelo final (v4) es un afinado de
#   `distilroberta-base` que tarda horas de GPU. Aquí se reproduce toda la
#   cadena que lleva hasta él —datos, EDA, ingeniería de variables, modelos de
#   referencia— y el v4 se **carga ya entrenado**.
#
# ### La limitación honesta, dicha antes de empezar
#
# **El modelo v4 todavía no está publicado.** Hoy vive solo en el disco del autor
# y en una carpeta privada de Drive; publicarlo en Hugging Face es un trámite
# pendiente. Mientras tanto, la sección 6.5 tiene una variable **`URL_MODELO`**,
# vacía y bien visible, lista para rellenar con el identificador del repositorio
# en cuanto exista.
#
# **El cuadernillo no se rompe por eso.** Las celdas que necesitan los pesos
# comprueban primero si están disponibles: si no lo están, imprimen qué falta y
# siguen adelante. Todo lo demás —las 4.724 filas del corpus, las 79.337
# entradas del catálogo, el EDA completo, la ingeniería de variables, los siete
# modelos de referencia y las tablas comparativas— se calcula de verdad, aquí,
# en cada ejecución.
#
# Lo mismo vale para el diccionario Kaikki/Wiktionary (243 MB) que usa la
# aplicación: tampoco está publicado y tampoco hace falta para este cuadernillo,
# porque no interviene en la estimación de dificultad.

# %%
# ============================================================
# PROYECTO INTEGRADOR — MÓDULO 5
# LiteraLevel: estimación de dificultad de lectura en inglés
# ============================================================

# =========================
# 1. Librerías generales
# =========================
import os
import re
import collections
import urllib.request

import numpy as np
import pandas as pd

# =========================
# 2. Visualización
# =========================
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# 3. Estadística
# =========================
from scipy.stats import spearmanr, mannwhitneyu, skew, kurtosis

# =========================
# 4. Preprocesamiento
# =========================
from sklearn.preprocessing import StandardScaler, LabelEncoder

# =========================
# 5. Partición de datos
# =========================
from sklearn.model_selection import GroupShuffleSplit

# =========================
# 6. Reducción de dimensiones
# =========================
from sklearn.decomposition import PCA

# =========================
# 7. Modelado
# =========================
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor

# =========================
# 8. Métricas
# =========================
from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report

# =========================
# 9. Manejo de advertencias
# =========================
import warnings
warnings.filterwarnings("ignore")

# =========================
# 10. Reproducibilidad
# =========================
# Una sola semilla, repetida después en cada partición y en cada modelo que
# tenga componente aleatoria. No se usa ninguna otra en todo el cuadernillo.
SEMILLA = 42
np.random.seed(SEMILLA)

# =========================
# 11. Configuración visual
# =========================
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 120)
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 110

print("Librerías cargadas correctamente. Semilla fija:", SEMILLA)

# %% [markdown]
# # 1. Introducción
#
# Alrededor de mil quinientos millones de personas estudian inglés en el mundo.
# Casi todas llegan tarde o temprano al mismo consejo, que además está bien
# respaldado por la investigación en adquisición de segundas lenguas: **leer
# mucho y leer seguido**. Y casi todas tropiezan en el mismo sitio: eligen un
# libro que suena bien, lo abren, y a las tres páginas lo cierran. No porque no
# sepan inglés, sino porque *ese* libro no era para *ese* lector todavía.
#
# El problema no es la falta de libros. Project Gutenberg regala más de sesenta
# mil obras en inglés de dominio público. El problema es que **nadie le dice al
# lector cuáles de esas sesenta mil puede leer hoy sin ahogarse**. Las etiquetas
# que existen —«clásico», «juvenil», «nivel intermedio»— las pone un editor a
# ojo, y solo cubren el catálogo comercial.
#
# **LiteraLevel** es una aplicación que mide esa dificultad con un modelo de
# lenguaje afinado para ello, acompaña al lector mientras lee (diccionario,
# pronunciación, progreso) y le recomienda qué abrir a continuación. Este
# cuadernillo documenta la parte cuantitativa: de dónde salen los datos, qué
# dicen, qué se hizo con ellos y qué tan bien funciona el resultado.
#
# **La pregunta que guía todo el trabajo:** ¿se puede estimar, con una sola
# cifra comprensible, si un texto en inglés le queda grande a un lector
# determinado, con suficiente fiabilidad como para ordenar un catálogo de sesenta
# mil libros?
#
# La respuesta corta, que el cuadernillo desarrolla y matiza: **sí para ordenar,
# no para certificar**. Y esa distinción es la que gobierna cómo se presenta el
# número al usuario final.

# %% [markdown]
# # 2. Planteamiento del problema
#
# ## 2.1 Qué se predice, exactamente
#
# Es un problema de **aprendizaje supervisado de regresión**, no de
# clasificación. La decisión no es cosmética y conviene justificarla, porque el
# camino evidente habría sido clasificar en los seis niveles del Marco Común
# Europeo (A1…C2):
#
# - La dificultad de un texto es **continua y ordinal**. Confundir B1 con B2 es
#   un error pequeño; confundir B1 con C2 es un desastre. Un clasificador
#   multiclase trata los dos errores igual; un regresor no.
# - Las fronteras entre niveles CEFR son **convenciones**, no discontinuidades
#   observables en el texto. Obligar al modelo a aprender esas fronteras es
#   pedirle que aprenda ruido de etiquetado.
# - Con una salida continua se puede **ordenar** el catálogo, que es lo que la
#   aplicación necesita de verdad. Una etiqueta discreta no ordena dentro de su
#   propia clase.
#
# ## 2.2 La formalización
#
# Un documento $d$ se parte en ventanas de tamaño fijo
# $b_1, \dots, b_k$ de 250 palabras cada una (mínimo 150 para que una ventana
# cuente). El modelo $f$ puntúa **cada ventana** y el documento es la media sin
# ponderar:
#
# $$\hat{y}(d) = \frac{1}{k}\sum_{i=1}^{k} f(b_i), \qquad f(b) \in [0, 5]$$
#
# La escala interna $[0,5]$ está anclada al MCER: 0 = A1, 1 = A2, 2 = B1,
# 3 = B2, 4 = C1, 5 = C2, con medios niveles en los valores intermedios. Lo que
# ve el usuario es la **escala pública**, comprimida a $[0,2]$:
#
# $$\text{pública}(y) = 0.4 \cdot \mathrm{clip}(y, 0, 5)$$
#
# **El troceado en ventanas fijas es la pieza clave del planteamiento**, y tiene
# una consecuencia que hay que enunciar explícitamente: como todas las ventanas
# miden lo mismo, **la longitud del documento no puede entrar como señal**. Un
# cuento de mil palabras y una novela de medio millón se puntúan con la misma
# regla. Esto es deliberado: sin ello, el modelo aprendería que «largo = difícil»,
# que es cierto en los corpus de examen y falso en una biblioteca.
#
# ## 2.3 Qué se optimiza
#
# La métrica principal no es el acierto exacto sino la **correlación de Spearman**
# entre la puntuación y la dificultad real, más una condición cualitativa: que
# **las medias por nivel oficial queden estrictamente ordenadas**. Un sistema de
# recomendación necesita ordenar bien; no necesita clavar la etiqueta.

# %% [markdown]
# # 3. Descripción de los datos: fuente, calidad y relevancia
#
# ## 3.1 Las cuatro fuentes, y por qué ninguna es Kaggle
#
# El módulo prohíbe expresamente Kaggle como origen de datos y espera APIs, web
# scraping o datos corporativos. Las fuentes de este proyecto son públicas,
# citables y de descarga directa:
#
# | Fuente | Qué aporta | Tamaño | Acceso |
# |---|---|---|---|
# | **CLEAR Corpus** (Crossley et al.) | Corpus de **entrenamiento**: extractos con dificultad medida sobre juicios humanos | 4.724 extractos | GitHub, descarga directa |
# | **Project Gutenberg** | El **catálogo** que la aplicación ordena | 79.337 entradas | Feed CSV oficial |
# | **SPGC** (Gerlach & Font-Clos) | Lista de frecuencia de vocabulario en inglés | 45.345 libros, solo conteos | Zenodo (procesado aparte) |
# | **British Council** | **Validación externa ciega**, con nivel CEFR oficial | 59 textos (45 legibles en local) | Material con derechos, no se distribuye |
#
# En este cuadernillo se descargan y se analizan las dos primeras. El SPGC se
# usó en su momento con PySpark para construir la lista de palabras familiares
# —2.838.258.803 palabras procesadas, 3.295.146 palabras únicas de vocabulario—
# y su resultado se resume aquí, pero no se reprocesa: son horas de cómputo para
# una lista que después resultó no aportar (§4.2). El corpus de British Council
# **tiene derechos y no se distribuye**; su papel es la validación externa y sus
# resultados se reportan en la §7.
#
# ## 3.2 Por qué CLEAR y no otra cosa
#
# La variable objetivo del CLEAR Corpus es **`BT_easiness`**: no es una fórmula
# de legibilidad ni la opinión de un editor, sino un **parámetro de Bradley-Terry**
# estimado a partir de miles de comparaciones por pares hechas por lectores
# humanos («¿cuál de estos dos textos es más fácil?»). Es la diferencia decisiva
# frente a las alternativas:
#
# - Es una escala **continua**, que es lo que pide un problema de regresión.
# - Mide **facilidad percibida por personas**, no una proxy tipográfica como
#   sílabas por palabra.
# - Viene acompañada de **once métricas clásicas de legibilidad ya calculadas**,
#   que sirven de línea base honesta y gratuita.
#
# Ojo con el signo, porque se presta a confusión durante todo el cuadernillo:
# **`BT_easiness` alto = texto FÁCIL**. Va al revés que la dificultad.

# %%
# --- Descarga del corpus de entrenamiento (CLEAR) -------------------------
# Repositorio público de los autores. Se guarda en disco para no volver a
# pedirlo si se reejecuta la celda.
URL_CLEAR = ("https://raw.githubusercontent.com/scrosseye/CLEAR-Corpus/"
             "main/CLEAR_corpus_final.xlsx")
RUTA_CLEAR = "CLEAR_corpus_final.xlsx"

if not os.path.exists(RUTA_CLEAR):
    urllib.request.urlretrieve(URL_CLEAR, RUTA_CLEAR)

clear = pd.read_excel(RUTA_CLEAR)
print("CLEAR Corpus descargado:", clear.shape[0], "filas x", clear.shape[1], "columnas")

# %%
print("Columnas del corpus:")
for i, col in enumerate(clear.columns):
    print(f"  {i:>2}  {col}")

# %%
clear[["Title", "Author", "Categ", "Lexile Band", "Google WC", "BT_easiness"]].head()

# %% [markdown]
# ## 3.3 Diccionario de datos
#
# Las 28 columnas se agrupan en cuatro familias. Solo la primera y la última
# entran al modelo; las demás sirven para particionar, describir y validar.
#
# | Columna | Qué es | Papel en el proyecto |
# |---|---|---|
# | `Excerpt` | El texto del extracto, ~175 palabras | **Entrada del modelo neuronal** |
# | `BT_easiness` | Facilidad Bradley-Terry estimada con juicios humanos | **Variable objetivo** |
# | `s.e.` | Error estándar de la estimación anterior | Diagnóstico de calidad de la etiqueta |
# | `Title`, `Author`, `Anthology`, `URL`, `Pub Year` | Procedencia de la obra | `Title` es la **variable de agrupación** para partir sin fuga |
# | `Categ`, `Sub Cat` | Literario (`Lit`) o informativo (`Info`) | Análisis bivariado por dominio |
# | `Lexile Band` | Banda Lexile editorial | Etiqueta externa **independiente** con la que contrastar |
# | `License`, `Location`, `MPAA*` | Derechos y clasificación de contenido | No se usan |
# | `Google WC`, `Sentence Count`, `Paragraphs` | Conteos estructurales | Rasgos de la línea base |
# | `Flesch-Reading-Ease`, `Flesch-Kincaid-Grade-Level`, `Automated Readability Index`, `SMOG Readability`, `New Dale-Chall Readability Formula`, `CAREC`, `CAREC_M`, `CML2RI` | Ocho índices clásicos de legibilidad, ya calculados | **Línea base** contra la que hay que ganar |

# %%
# --- Calidad: ausentes, duplicados y unidades de análisis ----------------
faltantes = clear.isna().sum()
faltantes = faltantes[faltantes > 0].sort_values(ascending=False)
tabla_nulos = pd.DataFrame({
    "n_ausentes": faltantes,
    "prop_ausentes": (faltantes / len(clear)).round(4),
})
print("Columnas con al menos un ausente:")
print(tabla_nulos)
print()
print("Filas totales:", len(clear))
print("Títulos únicos:", clear["Title"].nunique())
print("Autores únicos:", clear["Author"].nunique())
print("Ausentes en las columnas que sí se usan:",
      int(clear[["Excerpt", "BT_easiness", "Title", "Categ"]].isna().sum().sum()))

# %% [markdown]
# ### Interpretación de la calidad
#
# El corpus está **limpio donde importa y sucio donde no**, que es la mejor
# combinación posible.
#
# - **Cero ausentes en `Excerpt`, `BT_easiness`, `Title` y `Categ`**, es decir,
#   en la entrada del modelo, en la variable objetivo y en la variable de
#   agrupación. No hay que imputar nada de lo que se va a usar, así que tampoco
#   hay que discutir si la imputación deforma la distribución.
# - Los ausentes se concentran en columnas **descriptivas y prescindibles**:
#   `Sub Cat` (87,6 % vacía), `License` (70,3 %) y `Anthology` (42,6 %). La
#   decisión es **no imputarlas y no eliminarlas**: no entran al modelo, y
#   borrar filas por ellas costaría la mitad del corpus a cambio de nada. Es la
#   aplicación literal del criterio de que un ausente solo es un problema si la
#   columna se va a usar.
# - **4.658 títulos únicos en 4.724 filas**: hay obras que aportan más de un
#   extracto. Poco, pero suficiente para justificar que la partición se haga
#   **por título y no por fila** (§5.4). Dos extractos del mismo libro
#   comparten vocabulario, estilo y autor; si uno cae en entrenamiento y otro en
#   prueba, la evaluación sale inflada.

# %%
# --- El catálogo que la aplicación tiene que ordenar ---------------------
# Feed oficial de Project Gutenberg. Es un archivo vivo: crece cada semana,
# así que las cifras que imprima esta celda pueden ser algo mayores que las
# comentadas debajo, medidas el 8 de septiembre de 2026.
URL_CATALOGO = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"
RUTA_CATALOGO = "pg_catalog.csv"

if not os.path.exists(RUTA_CATALOGO):
    urllib.request.urlretrieve(URL_CATALOGO, RUTA_CATALOGO)

catalogo = pd.read_csv(RUTA_CATALOGO)
print("Entradas del catálogo completo:", f"{len(catalogo):,}")
print()
print("Reparto por tipo de material:")
print(catalogo["Type"].value_counts().head(7))

# %%
libros_en = catalogo[(catalogo["Language"] == "en") & (catalogo["Type"] == "Text")]
print("Libros de TEXTO en INGLÉS:", f"{len(libros_en):,}")
print("Autores distintos:", f"{libros_en['Authors'].nunique():,}")

temas = libros_en["Subjects"].dropna().str.split("; ").explode().str.strip()
print("Materias distintas:", f"{temas.nunique():,}")
print()
print("Las diez materias más frecuentes:")
print(temas.value_counts().head(10))

# %% [markdown]
# ### Interpretación: relevancia de los datos para el problema
#
# El catálogo tiene **79.337 entradas**, de las cuales solo **61.642 son libros
# de texto en inglés** (el resto son grabaciones, imágenes, datasets y obras en
# otros idiomas). Ese es el universo real del producto, y es también el
# argumento de negocio: **61.642 libros gratuitos y ninguna medida de dificultad
# fiable para ninguno de ellos**.
#
# Las materias más frecuentes —ciencia ficción, relatos cortos, aventuras,
# novela detectivesca— confirman que el catálogo es **literatura de consumo, no
# documentación técnica**. Eso es exactamente el dominio del CLEAR Corpus, cuya
# mitad literaria (`Lit`) recoge prosa narrativa del mismo tipo. La fuente de
# entrenamiento y la población de destino coinciden, que es la condición para
# que un modelo generalice.
#
# Hay un matiz que hay que decir y no esconder: el corpus de entrenamiento son
# extractos de ~175 palabras y el catálogo son novelas enteras. Esa distancia se
# salva **troceando el libro en ventanas del tamaño del extracto**, que es la
# razón de ser del planteamiento de la §2.2 y no un detalle de implementación.

# %% [markdown]
# # 4. Análisis exploratorio
#
# Organizado en tres pasos: **univariado** (cada variable por su cuenta),
# **bivariado** (cada variable contra la dificultad) y **multivariado** (todas a
# la vez). Cada figura va seguida de su lectura; ninguna se deja sin
# interpretar.
#
# ## 4.1 Análisis univariado

# %%
print("Variable objetivo: BT_easiness (alto = fácil)")
print(clear["BT_easiness"].describe().round(3))
print()
print("Asimetría (skew):", round(float(skew(clear["BT_easiness"])), 3))
print("Curtosis (exceso):", round(float(kurtosis(clear["BT_easiness"])), 3))

# %%
fig, ejes = plt.subplots(1, 2, figsize=(11, 4))
ejes[0].hist(clear["BT_easiness"], bins=45, color="#4C72B0", edgecolor="white")
ejes[0].axvline(clear["BT_easiness"].mean(), color="#C44E52", linestyle="--",
                label=f"media {clear['BT_easiness'].mean():.2f}")
ejes[0].set_title("Distribución de BT_easiness")
ejes[0].set_xlabel("BT_easiness (alto = más fácil)")
ejes[0].set_ylabel("Extractos")
ejes[0].legend()
sns.boxplot(x=clear["BT_easiness"], ax=ejes[1], color="#4C72B0")
ejes[1].set_title("Dispersión y valores extremos")
ejes[1].set_xlabel("BT_easiness")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 1 — Distribución de la variable objetivo.**
#
# La variable se comporta bien: media −0,958, mediana −0,909, desviación típica
# 1,034, asimetría −0,13 y curtosis −0,49. Es decir, **prácticamente simétrica y
# ligeramente más plana que una normal**, sin cola larga por ningún lado.
#
# Esto tiene dos consecuencias prácticas:
#
# 1. **No hay que transformar la variable objetivo.** Ni logaritmo ni raíz: no
#    hay asimetría que corregir. Una transformación aquí solo añadiría un paso
#    de vuelta atrás en cada predicción, sin ganar nada.
# 2. **Los puntos que el boxplot marca como atípicos no se tocan.** Son los
#    extremos legítimos del fenómeno —los textos infantiles muy fáciles y la
#    prosa académica muy densa—, precisamente los que el modelo tiene que
#    aprender a separar. Eliminarlos recortaría el rango útil del sistema justo
#    en los bordes donde el usuario más agradece un aviso. Se conservan los
#    4.724 extractos.
#
# Que el rango vaya de −3,68 a +1,71 y no esté centrado en cero es solo la
# convención de escala de Bradley-Terry; no significa que el corpus sea «difícil
# en promedio».

# %%
clear["palabras_excerpt"] = clear["Excerpt"].str.split().str.len()
print("Longitud de los extractos, en palabras:")
print(clear["palabras_excerpt"].describe().round(1))

# %%
plt.figure(figsize=(7, 3.6))
plt.hist(clear["palabras_excerpt"], bins=40, color="#55A868", edgecolor="white")
plt.title("Longitud de los extractos del CLEAR Corpus")
plt.xlabel("Palabras por extracto")
plt.ylabel("Extractos")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 2 — Longitud de los extractos.**
#
# Todos los extractos miden entre **129 y 205 palabras**, con media 173 y
# desviación típica 17. No es casualidad: **los autores del corpus controlaron la
# longitud por diseño**, para que los lectores compararan dificultad de prosa y
# no cantidad de texto.
#
# Este histograma, que parece un dato menor, es la justificación de dos
# decisiones del sistema final:
#
# - **`MIN_WORDS = 150`**: la aplicación se niega a puntuar cualquier fragmento
#   más corto que un extracto típico del corpus. Por debajo de esa longitud el
#   modelo estaría extrapolando fuera del régimen en el que aprendió.
# - **`MAX_LENGTH = 256` tokens**: 250 palabras inglesas siempre superan los 256
#   subtokens BPE, de modo que **todas las ventanas ocupan exactamente el mismo
#   tensor**. No hay relleno, y por tanto agrupar las ventanas de una manera u
#   otra no puede cambiar ni un decimal del resultado.
#
# Y anticipa un hallazgo del análisis bivariado: si en el corpus todos los
# textos miden casi lo mismo, **la longitud no puede ser una señal de dificultad
# aquí**. Lo comprobamos en la Figura 4.

# %%
fig, ejes = plt.subplots(1, 2, figsize=(11, 4))
conteo_categ = clear["Categ"].value_counts()
ejes[0].bar(conteo_categ.index.astype(str), conteo_categ.values,
            color=["#4C72B0", "#DD8452"])
ejes[0].set_title("Extractos por dominio")
ejes[0].set_ylabel("Extractos")
for i, v in enumerate(conteo_categ.values):
    ejes[0].text(i, v + 30, f"{v:,}", ha="center")

conteo_lexile = clear["Lexile Band"].astype(str).value_counts().head(8)
ejes[1].barh(conteo_lexile.index[::-1], conteo_lexile.values[::-1], color="#937860")
ejes[1].set_title("Banda Lexile (ocho valores más frecuentes)")
ejes[1].set_xlabel("Extractos")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 3 — Dominio y banda Lexile.**
#
# El corpus está **equilibrado por dominio**: 2.420 extractos literarios frente
# a 2.304 informativos. No hay clase minoritaria, así que no hace falta
# ponderar ni remuestrear, y las comparaciones entre `Lit` e `Info` de la §4.2
# se apoyan en tamaños parecidos.
#
# La banda Lexile, en cambio, **está concentrada y sucia**. Concentrada: 1100 y
# 1300 se llevan 2.738 de los 4.724 extractos, y las bandas extremas (100, 1900)
# tienen menos de diez casos cada una; cualquier conclusión sobre esos extremos
# será anecdótica y así habrá que decirlo. Sucia: junto a valores enteros
# aparecen 32 filas escritas como rango de texto —`410L-600L`, `610L - 800L`,
# `610L-800`—, con tres grafías distintas para dos bandas. Es un problema de
# captura, no de contenido, y se corrige en la §4.2 antes de usar la variable.

# %% [markdown]
# ## 4.2 Análisis bivariado
#
# La pregunta de este bloque es una sola: **¿qué variables se mueven con la
# dificultad, y cuáles no?**

# %%
METRICAS_CORPUS = [
    "Flesch-Reading-Ease", "Flesch-Kincaid-Grade-Level",
    "Automated Readability Index", "SMOG Readability",
    "New Dale-Chall Readability Formula", "CAREC", "CAREC_M", "CML2RI",
    "Google WC", "Sentence Count", "Paragraphs",
]

asociacion = pd.DataFrame({
    "Pearson": clear[METRICAS_CORPUS].corrwith(clear["BT_easiness"]),
    "Spearman": clear[METRICAS_CORPUS].corrwith(clear["BT_easiness"], method="spearman"),
}).round(3).sort_values("Pearson")
print("Asociación de cada métrica clásica con BT_easiness:")
print(asociacion)

# %%
plt.figure(figsize=(8, 4.5))
orden = asociacion["Pearson"].sort_values()
colores = ["#C44E52" if v < 0 else "#4C72B0" for v in orden.values]
plt.barh(orden.index, orden.values, color=colores)
plt.axvline(0, color="black", linewidth=0.8)
plt.title("Correlación de Pearson de cada métrica con BT_easiness")
plt.xlabel("Correlación (negativa = la métrica sube cuando el texto se pone difícil)")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 4 — Qué correlaciona con la facilidad, y qué no.**
#
# Tres lecturas, en orden de importancia:
#
# 1. **Las métricas de legibilidad funcionan, pero se quedan a medias.** Las más
#    fuertes son `CAREC_M` (−0,58), `CAREC` (−0,58), `SMOG` (−0,56) y
#    `New Dale-Chall` (−0,56); `Flesch-Reading-Ease` va en positivo (+0,55)
#    porque su escala está invertida por definición, y `CML2RI` también (+0,56).
#    Los signos son todos los que la teoría predice, lo que confirma que la
#    etiqueta `BT_easiness` mide lo que dice medir. Pero **ninguna pasa de 0,58**:
#    con la mejor de ellas se explica un tercio de la varianza. Ahí está el hueco
#    que justifica todo el proyecto.
#
# 2. **`Google WC` —el número de palabras— correlaciona −0,125. Prácticamente
#    nada.** Es el resultado más importante de esta figura. En este corpus la
#    longitud no informa, porque el corpus la controló por diseño (Figura 2).
#    Sirve de contraste con lo que ocurre en la validación externa de la §7: en
#    los exámenes de British Council el nivel y la longitud **sí** están
#    confundidos, y allí contar palabras llega a Spearman 0,807. La diferencia
#    entre los dos corpus no es un capricho estadístico: es la razón de que el
#    modelo se entrene con ventanas de tamaño fijo.
#
# 3. **`Sentence Count` (+0,36) y `Paragraphs` (+0,25) son señales estructurales
#    débiles**: a igualdad de palabras, más frases significa frases más cortas, y
#    las frases cortas se leen mejor. Consistente, pero flojo.

# %%
fig, ejes = plt.subplots(1, 2, figsize=(11, 4.2))
ejes[0].scatter(clear["New Dale-Chall Readability Formula"], clear["BT_easiness"],
                s=6, alpha=0.25, color="#4C72B0")
ejes[0].set_title("La métrica más informativa (r = -0,56)")
ejes[0].set_xlabel("New Dale-Chall")
ejes[0].set_ylabel("BT_easiness")
ejes[1].scatter(clear["Google WC"], clear["BT_easiness"],
                s=6, alpha=0.25, color="#C44E52")
ejes[1].set_title("La longitud del texto (r = -0,13)")
ejes[1].set_xlabel("Palabras del extracto (Google WC)")
ejes[1].set_ylabel("BT_easiness")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 5 — La mejor señal clásica frente a la longitud.**
#
# El panel izquierdo tiene la nube inclinada que se espera: cuanto mayor el
# índice Dale-Chall, más difícil el texto. Pero también se ve la **dispersión
# enorme alrededor de la tendencia**: para un mismo valor de Dale-Chall hay
# textos que los lectores puntúan casi tres unidades aparte. Ese grosor de la
# nube es, literalmente, el error que un modelo mejor tiene que reducir.
#
# El panel derecho es una **nube sin forma**, comprimida entre 125 y 205
# palabras. Es la comprobación visual del punto anterior: aquí, la longitud no
# dice nada. Y es el ejemplo perfecto de por qué una variable que correlaciona
# con la etiqueta en un corpus puede ser una trampa en otro; en la §7 se ve el
# mismo `Google WC` disparado a 0,807 en otro conjunto de datos.

# %%
grupo_lit = clear.loc[clear["Categ"] == "Lit", "BT_easiness"]
grupo_info = clear.loc[clear["Categ"] == "Info", "BT_easiness"]
estadistico, p_valor = mannwhitneyu(grupo_lit, grupo_info, alternative="two-sided")

print("Literario  -> n =", len(grupo_lit), "| media", round(float(grupo_lit.mean()), 3),
      "| mediana", round(float(grupo_lit.median()), 3))
print("Informativo-> n =", len(grupo_info), "| media", round(float(grupo_info.mean()), 3),
      "| mediana", round(float(grupo_info.median()), 3))
print()
print("H0: la facilidad se distribuye igual en ambos dominios.")
print("Prueba de Mann-Whitney (no paramétrica, no exige normalidad)")
print("   U =", f"{estadistico:,.0f}", "| p-value =", f"{p_valor:.3g}")
print("   Decisión con alpha = 0.05:", "se RECHAZA H0" if p_valor < 0.05 else "no se rechaza H0")

# %%
plt.figure(figsize=(6.5, 4))
sns.boxplot(data=clear, x="Categ", y="BT_easiness", color="#4C72B0")
plt.title("Facilidad por dominio")
plt.xlabel("Dominio (Lit = literario, Info = informativo)")
plt.ylabel("BT_easiness (alto = más fácil)")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 6 — Literatura frente a texto informativo.**
#
# La diferencia es grande y estadísticamente indiscutible: mediana −0,64 en los
# textos literarios frente a **−1,31 en los informativos**, con un p-value de la
# prueba de Mann-Whitney del orden de 10⁻⁸⁸. **El texto informativo es
# sistemáticamente más difícil**, aproximadamente 0,6 unidades de la escala, que
# es más de media desviación típica.
#
# Se usa Mann-Whitney y no una prueba *t* porque la comparación no exige
# normalidad de los grupos y aquí, con curtosis negativa y colas cortas, la
# prueba no paramétrica es la conservadora.
#
# Dos consecuencias concretas para el producto:
#
# - **El dominio es una variable de confusión que el modelo no ve.** Un ensayo y
#   una novela con la misma sintaxis reciben puntuaciones distintas de los
#   lectores porque la carga conceptual es distinta. Esto acota lo que el sistema
#   puede prometer.
# - **Favorece al caso de uso real.** El catálogo que LiteraLevel ordena es
#   literatura —las materias más frecuentes de la §3.3 son ciencia ficción,
#   relatos y aventuras—, es decir, el subconjunto donde el modelo está mejor
#   calibrado.

# %%
# --- Limpieza de `Lexile Band` para poder usarla en el análisis ----------
# 32 filas de 4.724 (0,7 %) están escritas como rango de texto en unidades L
# en vez de como el entero de la banda. NO son un error de contenido: son otra
# notación. Se convierten al punto medio del rango y se ajustan a la banda
# canónica más cercana, en vez de tirarlas. Justificación: perder 32
# observaciones etiquetadas para ahorrarse tres líneas de código es una mala
# permuta, y descartar filas por su formato sesga hacia las fuentes que
# capturaron bien.
BANDAS_CANONICAS = np.array([100, 300, 500, 700, 900, 1100, 1300, 1500, 1700, 1900])


def banda_lexile(valor):
    """Devuelve la banda Lexile canónica de una celda, entera o en rango."""
    numeros = [int(x) for x in re.findall(r"\d+", str(valor))]
    if not numeros:
        return np.nan
    punto_medio = float(np.mean(numeros))
    return int(BANDAS_CANONICAS[np.argmin(np.abs(BANDAS_CANONICAS - punto_medio))])


clear["lexile"] = clear["Lexile Band"].map(banda_lexile)
print("Filas con banda ilegible tras la limpieza:", int(clear["lexile"].isna().sum()))
print("Bandas resultantes:", sorted(clear["lexile"].unique().tolist()))
print("Spearman(banda Lexile, BT_easiness):",
      round(float(spearmanr(clear["lexile"], clear["BT_easiness"])[0]), 3))

# %%
orden_lexile = [str(b) for b in sorted(clear["lexile"].unique())]
plt.figure(figsize=(9, 4))
sns.boxplot(data=clear.assign(banda=clear["lexile"].astype(str)),
            x="banda", y="BT_easiness", order=orden_lexile, color="#55A868")
plt.title("Facilidad medida por lectores frente a banda Lexile editorial")
plt.xlabel("Banda Lexile (mayor = el editor la considera más difícil)")
plt.ylabel("BT_easiness (alto = más fácil)")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 7 — Dos etiquetas independientes contrastadas.**
#
# La banda Lexile la asigna un procedimiento editorial; `BT_easiness` sale de
# comparaciones entre lectores. Son dos mediciones **independientes** del mismo
# fenómeno, y la figura muestra que **se ordenan igual**: las medianas bajan
# monótonamente de 500 a 1500, con Spearman −0,504.
#
# Hay una sola inversión, entre 1500 (mediana −1,85) y 1700 (−1,82), y se
# explica sola: la banda 1700 tiene 58 extractos y la 1900 tiene 9. **Con esos
# tamaños, el orden en el extremo derecho es ruido**, y así hay que reportarlo en
# vez de presentar la curva como perfecta.
#
# La lectura de fondo importa para el proyecto entero: **dos sistemas de
# medición distintos coinciden en el orden, no en la magnitud**. Es exactamente
# lo que después se observará con el modelo v4 frente al MCER (§7), y la razón de
# que la interfaz muestre bandas anchas —básico, intermedio, avanzado— en lugar
# de una letra CEFR con pretensión de exactitud.

# %%
# --- El catálogo viejo de la aplicación: 1.197 libros mal etiquetados ---
# Recuento verificado sobre `catalogo_recomendaciones.csv` del repositorio, que
# no está publicado y por eso se reproduce aquí como dato en vez de recalcularse.
etiquetas_v1 = pd.Series(
    {"A1": 723, "A2": 185, "B1": 69, "B2": 52, "C1": 53, "C2": 115},
    name="libros")
print("Catálogo antiguo, etiquetado por el modelo v1:")
print(etiquetas_v1)
print("Total:", int(etiquetas_v1.sum()))
print("Proporción etiquetada A1:", round(float(etiquetas_v1["A1"] / etiquetas_v1.sum()), 3))
print("Libros en la franja B1-B2, donde está la mayoría de los lectores:",
      int(etiquetas_v1[["B1", "B2"]].sum()))

# %%
plt.figure(figsize=(6.5, 3.8))
plt.bar(etiquetas_v1.index, etiquetas_v1.values, color="#C44E52")
plt.title("Reparto del catálogo antiguo según las etiquetas del modelo v1")
plt.xlabel("Nivel CEFR asignado")
plt.ylabel("Libros")
for i, v in enumerate(etiquetas_v1.values):
    plt.text(i, v + 12, str(v), ha="center")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 8 — Por qué hubo que volver a medir el catálogo entero.**
#
# Esta figura documenta un **fracaso propio**, y está aquí precisamente por eso.
#
# El catálogo con el que la aplicación funcionó durante meses tenía 1.197 libros
# etiquetados por un modelo anterior (v1) leyendo solo **las primeras ~190
# palabras** de cada obra, con cortes CEFR obtenidos por cuantiles. El resultado
# es la distribución de la figura: **723 de 1.197 libros —el 60 %— etiquetados
# A1**, y apenas **121 libros en toda la franja B1-B2**, que es justo donde se
# concentran los lectores reales.
#
# Una distribución así no describe a Project Gutenberg; describe un
# procedimiento roto. Y se puede señalar exactamente dónde se rompió: leer 190
# palabras de una novela es leer el prólogo, la dedicatoria o la nota del editor,
# no la novela. De ahí salen los cuentos infantiles etiquetados C1 y los clásicos
# más dispares agrupados todos en C2.
#
# **Consecuencia asumida:** esas etiquetas están marcadas como no fiables en la
# documentación del proyecto, y el precálculo masivo (§8) vuelve a medir el
# catálogo **libro entero, capítulo a capítulo, sin muestrear**. Es la lección
# metodológica más cara del proyecto: *el modelo estaba bien y el protocolo de
# lectura estaba mal*.

# %% [markdown]
# ## 4.3 Análisis multivariado
#
# Hasta aquí se ha mirado cada variable contra la dificultad. Ahora se miran
# **todas a la vez**, para responder a dos preguntas: ¿cuánta información
# redundante hay entre las métricas clásicas?, y ¿bastan para separar niveles?
#
# **Nota metodológica obligatoria:** en la matriz de correlación entran
# **únicamente variables numéricas**. Las nominales (`Categ`, `Title`, `Author`)
# quedan fuera; su asociación con la dificultad se estudió con la prueba de
# Mann-Whitney de la Figura 6, que es el instrumento correcto para una
# categórica frente a una continua.

# %%
numericas = METRICAS_CORPUS + ["BT_easiness"]
matriz = clear[numericas].corr()

plt.figure(figsize=(9.5, 7.5))
sns.heatmap(matriz, annot=True, fmt=".2f", cmap="coolwarm", center=0,
            annot_kws={"size": 7}, cbar_kws={"label": "Pearson"})
plt.title("Matriz de correlación de las métricas clásicas (solo numéricas)")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 9 — Multicolinealidad entre las métricas clásicas.**
#
# El bloque rojo intenso de la esquina superior izquierda es el hallazgo:
# `Flesch-Kincaid`, `Automated Readability Index`, `SMOG` y `New Dale-Chall`
# **están correlacionadas entre sí muy por encima de lo que cada una
# correlaciona con la variable objetivo**. Es lógico —todas se calculan a partir
# de las mismas dos cantidades, longitud de frase y longitud de palabra— pero
# tiene tres consecuencias que condicionan el modelado:
#
# 1. **Once métricas no son once informaciones.** Son esencialmente dos o tres
#    ejes repetidos. Añadir más índices de la misma familia no puede mejorar el
#    resultado; se comprueba en la §6.
# 2. **Los coeficientes de una regresión lineal sobre estas variables no son
#    interpretables uno a uno.** Con esta multicolinealidad, los signos
#    individuales se reparten de forma arbitraria entre variables casi idénticas.
#    Por eso el modelo lineal se usa aquí como **línea base de rendimiento**, no
#    como herramienta explicativa.
# 3. **`Google WC` es la única columna que no se parece a ninguna otra** —fila y
#    columna casi blancas— y además es la que menos correlaciona con la
#    objetivo. Independiente e inútil a la vez, en este corpus.
#
# Justifica pasar a componentes principales: si la información se repite,
# conviene ver cuántos ejes independientes hay realmente.

# %%
# --- Rasgos propios calculados sobre el texto crudo ---------------------
# Se usan las MISMAS expresiones regulares que `app/scoring.py`, no otras
# parecidas: si el troceado del cuadernillo divergiera del de la aplicación,
# los números dejarían de significar lo mismo.
PALABRA_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
FRASE_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")


def contar_silabas(palabra):
    """Aproximación por grupos de vocales. Basta para una variable agregada."""
    return max(1, len(re.findall(r"[aeiouy]+", palabra.lower())))


# --- La partición se calcula AQUÍ, y no más abajo, y hay un motivo ------
# Uno de los seis rasgos, `palabras_raras`, necesita una lista de palabras
# familiares. Si esa lista se construyera con el corpus entero, las palabras
# de los extractos reservados para prueba entrarían en la definición de una
# variable de entrada: es fuga de datos, aunque sea sutil. Así que primero se
# parte y después se cuenta.
#
# `GroupShuffleSplit` reparte según los grupos, el número de filas y la
# semilla; no mira los valores de X. Por eso puede calcularse antes de existir
# los rasgos y da exactamente la misma partición que se usa en el bloque 5.
grupos = clear["Title"].values
particion = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SEMILLA)
idx_train, idx_test = next(
    particion.split(np.zeros(len(clear)), clear["BT_easiness"].values, grupos))

# Lista de palabras familiares: las 3.000 más frecuentes DEL ENTRENAMIENTO.
contador = collections.Counter()
for texto in clear["Excerpt"].iloc[idx_train]:
    contador.update(w.lower() for w in PALABRA_RE.findall(texto))
PALABRAS_FAMILIARES = set(w for w, _ in contador.most_common(3000))

print("Vocabulario del entrenamiento:", f"{len(contador):,}", "palabras distintas")
print("Tokens totales:", f"{sum(contador.values()):,}")
print("Umbral de 'familiar': las 3.000 más frecuentes")

# %%
def rasgos_de_texto(texto):
    """Seis rasgos lingüísticos agregados de un texto en inglés."""
    palabras = [w.lower() for w in PALABRA_RE.findall(texto)]
    frases = [f for f in FRASE_RE.findall(texto) if PALABRA_RE.findall(f)]
    n_palabras = max(len(palabras), 1)
    n_frases = max(len(frases), 1)
    silabas = [contar_silabas(w) for w in palabras]
    return {
        "palabras_por_frase": n_palabras / n_frases,
        "diversidad_lexica": len(set(palabras)) / n_palabras,
        "letras_por_palabra": sum(len(w) for w in palabras) / n_palabras,
        "palabras_raras": sum(1 for w in palabras if w not in PALABRAS_FAMILIARES) / n_palabras,
        "silabas_por_palabra": sum(silabas) / n_palabras,
        "polisilabas": sum(1 for s in silabas if s >= 3) / n_palabras,
    }


RASGOS = ["palabras_por_frase", "diversidad_lexica", "letras_por_palabra",
          "palabras_raras", "silabas_por_palabra", "polisilabas"]

rasgos = pd.DataFrame([rasgos_de_texto(t) for t in clear["Excerpt"]])
print("Rasgos calculados:", rasgos.shape)
rasgos.head(3).round(3)

# %%
asociacion_rasgos = (rasgos.assign(BT_easiness=clear["BT_easiness"].values)
                     .corr()["BT_easiness"].drop("BT_easiness")
                     .sort_values().round(3))
print("Correlación de cada rasgo propio con BT_easiness:")
print(asociacion_rasgos)

# %% [markdown]
# ### Interpretación: los rasgos propios no baten a las métricas clásicas
#
# El rasgo más informativo de los seis es **`palabras_raras` (−0,490)**: la
# proporción de palabras que no están entre las 3.000 más frecuentes. Le siguen
# `polisilabas` (−0,477) y `silabas_por_palabra` (−0,447). Todos van en la
# dirección correcta y ninguno alcanza a `CAREC_M` (−0,582).
#
# **Este número tuvo una fuga de datos, y esto es lo que costó.** En una versión
# anterior de este cuadernillo la lista de palabras familiares se construía con
# el corpus entero, contando también las palabras de los extractos reservados
# para prueba. Una auditoría externa lo señaló y la lista pasó a construirse
# solo con entrenamiento, que es como está ahora.
#
# Lo interesante es que **la fuga no inflaba nada**. Al medir las dos versiones
# con todo lo demás idéntico —misma semilla, misma partición, mismos modelos—,
# solo **228 de las 3.000 palabras** cambian de lista, y los resultados se
# mueven en la tercera cifra decimal:
#
# | | Lista contaminada | Lista solo de entrenamiento |
# |---|---|---|
# | `palabras_raras` vs `BT_easiness` (Pearson) | −0,486 | **−0,490** |
# | Regresión lineal, 17 variables (MAE) | 0,5948 | 0,5946 |
# | Random Forest (Spearman) | 0,688 | 0,686 |
# | Logística, 3 variables (exactitud) | 0,312 | 0,313 |
# | Logística, 17 variables (exactitud) | 0,354 | 0,352 |
#
# Es decir: la cifra limpia es **ligeramente mejor**, no peor. La explicación es
# la misma ley de Zipf que aparece en la tabla de abajo — con 4.724 extractos,
# las 3.000 palabras más frecuentes son casi las mismas se cuenten sobre el
# corpus entero o sobre el 80 % de él.
#
# Que el efecto sea despreciable **no lo convierte en aceptable**: era fuga y
# había que quitarla. Pero conviene separar las dos cosas, porque una fuga
# medida es un dato y una fuga sospechada es solo un miedo.
#
# Aquí hay una **hipótesis rechazada que conviene reportar** en lugar de
# esconderla. Durante el proyecto, `palabras_raras` se recalculó tres veces con
# listas de vocabulario cada vez más grandes, esperando que una lista mejor diera
# una señal mejor:
#
# | Lista de palabras familiares | Corpus de origen | Correlación con `BT_easiness` |
# |---|---|---|
# | 18 libros del corpus Gutenberg de NLTK | ~2 M palabras | −0,379 |
# | Muestra de 397 libros | 27,6 M palabras | −0,330 |
# | **SPGC completo** | **45.345 libros, 2.838 M palabras** | **−0,326** |
#
# Multiplicar el corpus de referencia por mil **no mejoró nada**; si acaso,
# empeoró levemente. La explicación es la ley de Zipf: la distribución de
# frecuencias del inglés converge muy rápido, así que las 3.000 palabras más
# frecuentes son casi las mismas se calculen sobre dos millones de palabras o
# sobre dos mil ochocientos millones. El esfuerzo de big data —agregación con
# PySpark sobre el catálogo completo— produjo una lista más robusta para texto
# nuevo arbitrario, que es un beneficio real de cobertura, pero **no una métrica
# mejor**. Reportarlo así es más útil que presentarlo como una mejora.

# %%
# --- PCA sobre el conjunto completo de variables numéricas --------------
X_completo = pd.concat([clear[METRICAS_CORPUS].reset_index(drop=True), rasgos], axis=1)

escalador_pca = StandardScaler().fit(X_completo)
X_escalado = escalador_pca.transform(X_completo)
pca = PCA(n_components=5, random_state=SEMILLA).fit(X_escalado)

varianza = pd.DataFrame({
    "Componente": [f"PC{i+1}" for i in range(5)],
    "Varianza explicada": pca.explained_variance_ratio_.round(3),
    "Acumulada": pca.explained_variance_ratio_.cumsum().round(3),
})
print(varianza.to_string(index=False))

# %%
componentes = pca.transform(X_escalado)
plt.figure(figsize=(6.5, 3.6))
plt.bar([f"PC{i+1}" for i in range(5)], pca.explained_variance_ratio_,
        color="#4C72B0")
plt.plot([f"PC{i+1}" for i in range(5)], pca.explained_variance_ratio_.cumsum(),
         marker="o", color="#C44E52", label="acumulada")
plt.title("Varianza explicada por componente principal")
plt.ylabel("Proporción de varianza")
plt.legend()
plt.tight_layout()
plt.show()

print("Correlación de PC1 con BT_easiness:",
      round(float(np.corrcoef(componentes[:, 0], clear["BT_easiness"])[0, 1]), 3))

# %% [markdown]
# **Figura 10 — Cuántos ejes independientes hay realmente.**
#
# **Un solo componente explica el 55,1 % de la varianza de las diecisiete
# variables**, y los dos primeros llegan al 70,0 %. Confirma numéricamente lo que
# el mapa de calor insinuaba: diecisiete columnas contienen, en la práctica, dos
# informaciones.
#
# PC1 está cargado en un extremo por `SMOG`, `New Dale-Chall`,
# `Flesch-Kincaid`, `polisilabas` y `letras_por_palabra`, y en el otro por
# `Flesch-Reading-Ease`. Es, en una sola cifra, **la complejidad de superficie
# del texto**: palabras largas, frases largas, vocabulario poco frecuente.
#
# Y correlaciona **0,614** con `BT_easiness`, es decir, explica el **38 %** de
# su varianza.
#
# **Cuidado con lo que ese 38 % significa y con lo que no.** El PCA se ajusta
# *sin mirar la variable objetivo*: busca la dirección de máxima varianza de
# las diecisiete entradas, no la que mejor predice la dificultad. Así que ese
# número describe cuánta señal lleva **el resumen no supervisado** de estas
# variables, y **no es un techo**: nada impide que una combinación supervisada,
# otro componente o una relación no lineal saquen más. De hecho, más abajo se
# ve que una regresión lineal sobre las mismas variables llega a Spearman
# 0,707, por encima de ese 0,614.
#
# Lo que sí sostiene el experimento es la comparación completa: ninguno de los
# modelos clásicos de este cuadernillo —lineal, bosque, logística, XGBoost—
# despega de esa zona, por mucha capacidad que se les dé. El argumento para
# pasar a un transformador no es el PCA por sí solo, sino que **subir la
# capacidad del modelo sobre estas variables no mueve el resultado, y cambiar
# la representación del texto sí**.

# %%
# --- Seis sextiles de facilidad, y por qué NO son niveles MCER ----------
# `qcut` parte `BT_easiness` en seis tramos con el mismo número de extractos
# cada uno. Eso produce seis clases **relativas a este corpus**, no niveles del
# Marco Común Europeo: aquí no hay ni una sola anotación institucional de MCER.
# Se les dan nombres de la forma A1..C2 solo para poder hablar de ellos en
# orden, y por eso en el resto del cuadernillo se llaman **sextiles**.
#
# El anclaje de verdad al MCER llega mucho más tarde, con otro corpus —los 654
# documentos con nivel asignado— y es el que usa el modelo desplegado. Son dos
# escalas distintas y no hay que confundirlas.
#
# Segunda salvedad, y también importante: los cortes se calculan sobre el
# corpus entero, incluidas las filas que después sirven de prueba. La
# definición de las clases, por tanto, ve las etiquetas reservadas. Es una
# evaluación **transductiva**: describe bien cómo se ordenan estos 4.724
# extractos, y no debe leerse como un test independiente. Se mantiene así
# a propósito, porque el resultado del transformador que aparece más abajo se
# midió contra estos mismos cortes y recalcularlos haría incomparable toda la
# progresión de modelos.
SEXTILES = ["C2", "C1", "B2", "B1", "A2", "A1"]
NIVELES_CEFR = SEXTILES  # nombre antiguo, se conserva para no romper el resto
nivel_cefr, bordes_cefr = pd.qcut(clear["BT_easiness"], q=6,
                                  labels=SEXTILES, retbins=True)
clear["nivel_cefr"] = nivel_cefr

plt.figure(figsize=(7, 5.5))
paleta = dict(zip(NIVELES_CEFR,
                  ["#4C2C69", "#4C72B0", "#55A868", "#CCB974", "#DD8452", "#C44E52"]))
for nivel in NIVELES_CEFR:
    mascara = (clear["nivel_cefr"] == nivel).values
    plt.scatter(componentes[mascara, 0], componentes[mascara, 1],
                s=7, alpha=0.45, label=nivel, color=paleta[nivel])
plt.title("Los extractos en el plano de los dos primeros componentes")
plt.xlabel("PC1 — complejidad de superficie (55,1 % de la varianza)")
plt.ylabel("PC2 — 14,9 % de la varianza")
plt.legend(title="Nivel", markerscale=2, fontsize=8)
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 11 — Los niveles se ordenan, pero no se separan.**
#
# Es la figura que resume el diagnóstico completo del análisis exploratorio.
#
# Hay **gradiente**: recorriendo PC1 de izquierda a derecha se pasa de los
# extractos C2 a los A1 de forma ordenada, sin saltos ni inversiones. La
# estructura existe y va en la dirección correcta.
#
# Pero **no hay fronteras**. Las seis nubes se solapan masivamente; los niveles
# adyacentes (B1 con B2, A2 con B1) son indistinguibles a ojo, y solo los
# extremos ocupan territorios propios. Con estas variables, un clasificador de
# seis clases no puede hacer mucho mejor que acertar el vecindario.
#
# **Y esa es exactamente la razón de que el producto final muestre bandas anchas
# en lugar de una letra CEFR.** La decisión de interfaz —tres bandas: básico,
# intermedio, avanzado— no es una simplificación comercial: **es la conclusión
# honesta de esta figura**. La geometría de los datos sostiene un orden, no una
# frontera de seis clases.

# %% [markdown]
# # 5. Procesamiento de datos
#
# Cada transformación aplicada, con su razón y con la evidencia que la respalda.
# Las decisiones que **no** se tomaron aparecen también, porque no imputar y no
# eliminar son decisiones igual de consecuentes que las contrarias.
#
# | Decisión | Razón | Evidencia / consecuencia |
# |---|---|---|
# | **No imputar** ausentes | Los ausentes están solo en columnas descriptivas (`Sub Cat` 87,6 %, `License` 70,3 %) que no entran al modelo | Cero ausentes en `Excerpt`, `BT_easiness`, `Title` y `Categ` |
# | **No eliminar filas** por ausentes | Borrar por `Sub Cat` costaría el 87 % del corpus a cambio de nada | Se conservan las 4.724 filas |
# | **Conservar los atípicos** de `BT_easiness` | Son los extremos legítimos del fenómeno, no errores de captura | Asimetría −0,13: no hay cola anómala (Figura 1) |
# | **No transformar** la variable objetivo | Distribución casi simétrica y curtosis negativa | Un logaritmo no arreglaría nada y añadiría un paso inverso |
# | **Reparar** `Lexile Band` en vez de tirar las filas | 32 filas (0,7 %) usan otra notación; es formato, no contenido | Tras la reparación, medianas monótonas salvo el tramo 1500-1700 (n = 58) |
# | **Rasgos propios** con las regex de `app/scoring.py` | Que el cuadernillo y la aplicación troceen igual | Si divergieran, las métricas dejarían de describir el sistema desplegado |
# | **Discretizar** en 6 niveles con `qcut` | Poder comparar contra clasificadores y contra el MCER | Clases balanceadas (787-788 cada una) por construcción |
# | **Partición por título**, no por fila | 4.724 extractos salen de 4.658 títulos: hay obras repetidas | Intersección train/test verificada = 0 |
# | **Escalar solo lo numérico y ajustar solo en train** | Evitar que la media y la varianza del test se filtren al ajuste | `fit` en entrenamiento, `transform` en prueba |
# | **No escalar** para el modelo neuronal | Un transformador recibe texto, no vectores numéricos | El escalado afecta únicamente a la línea base |

# %%
# --- 5.1 Etiquetado ordinal en seis niveles ------------------------------
# Discretización por cuantiles sobre la MISMA distribución ya validada. Se hace
# con qcut y no con cortes a mano para que las seis clases queden balanceadas y
# la comparación entre clasificadores sea limpia.
print("Bordes de los seis niveles (en la escala BT_easiness):")
print(np.round(bordes_cefr, 3).tolist())
print()
print("Extractos por nivel:")
print(clear["nivel_cefr"].value_counts().sort_index())

# %% [markdown]
# ### Qué significa —y qué no— esta discretización
#
# Los seis niveles salen de partir `BT_easiness` en sextiles. Eso garantiza
# clases balanceadas y hace comparables los clasificadores, pero **hay que decir
# con todas las letras qué no es**: no es una certificación MCER. El Marco Común
# Europeo describe lo que un aprendiz *sabe hacer*; aquí se está etiquetando un
# texto por su posición relativa dentro de este corpus concreto.
#
# La consecuencia es que **la letra CEFR es un ancla de investigación, no una
# credencial**, y así se enuncia en la interfaz de la aplicación y en toda la
# documentación del proyecto. Un texto que este sistema llama B1 no es «un texto
# B1 oficial»; es un texto que cae en el cuarto sextil de facilidad de un corpus
# de 4.724 extractos con juicios humanos.

# %%
# --- 5.2 Partición por grupo, para no filtrar información ---------------
# La unidad de agrupación es la OBRA, no el extracto. Dos extractos del mismo
# libro comparten autor, época, vocabulario y estilo: si uno entrena y otro
# evalúa, la evaluación mide memoria, no generalización.
X_modelo = pd.concat([clear[METRICAS_CORPUS].reset_index(drop=True), rasgos], axis=1)
y_modelo = clear["BT_easiness"].values

# `idx_train` e `idx_test` ya se calcularon en el bloque 4, antes de construir
# la lista de palabras familiares, para que esa lista no viera el conjunto de
# prueba. Se reutilizan aquí tal cual: es la misma partición, no otra.

print("Entrenamiento:", X_modelo.iloc[idx_train].shape)
print("Prueba:       ", X_modelo.iloc[idx_test].shape)

# %%
# Verificación explícita de que no hay fuga: la intersección debe ser CERO.
titulos_train = set(clear["Title"].iloc[idx_train])
titulos_test = set(clear["Title"].iloc[idx_test])
print("Títulos compartidos entre entrenamiento y prueba:",
      len(titulos_train & titulos_test))

# %%
# --- 5.3 Escalado: se ajusta SOLO en entrenamiento ----------------------
escalador = StandardScaler().fit(X_modelo.iloc[idx_train])
X_train = escalador.transform(X_modelo.iloc[idx_train])
X_test = escalador.transform(X_modelo.iloc[idx_test])
y_train, y_test = y_modelo[idx_train], y_modelo[idx_test]

print("Media de la primera variable en entrenamiento tras escalar:",
      round(float(X_train[:, 0].mean()), 6))
print("Media de la misma variable en prueba tras escalar:",
      round(float(X_test[:, 0].mean()), 4))
print("(la de prueba NO es cero, y debe no serlo: el escalador no la vio)")

# %% [markdown]
# # 6. Modelación
#
# La secuencia sigue la lógica de ir dándole al modelo **representaciones cada
# vez más ricas del texto**, y medir qué gana en cada paso:
#
# 1. Predecir siempre la media (línea base trivial, el suelo).
# 2. Regresión lineal sobre las once métricas del corpus.
# 3. Regresión lineal sobre esas once más los seis rasgos propios.
# 4. Random Forest sobre las diecisiete.
# 5. Clasificadores de seis niveles: regresión logística y XGBoost.
# 6. Redes neuronales: embeddings, `roberta-base` y el **v4** final.
#
# Los cinco primeros se calculan aquí. El sexto se documenta y se carga.

# %%
# --- 6.1 Línea base: predecir siempre la media del entrenamiento -------
prediccion_media = np.full(len(y_test), y_train.mean())
resultados = []


def evaluar(nombre, prediccion, observacion=""):
    """Registra MAE, RMSE y Spearman de una predicción sobre el conjunto de prueba.

    Una predicción constante no ordena nada, así que su Spearman no está
    definido; se reporta como «no aplica» en vez de inventar un cero.
    """
    mae = mean_absolute_error(y_test, prediccion)
    rmse = float(np.sqrt(np.mean((prediccion - y_test) ** 2)))
    ordena = len(np.unique(prediccion)) > 1
    texto_rho = f"{float(spearmanr(prediccion, y_test)[0]):.3f}" if ordena else "no aplica"
    resultados.append({"Modelo": nombre, "MAE": round(mae, 3),
                       "RMSE": round(rmse, 3), "Spearman": texto_rho,
                       "Observación": observacion})
    print(f"{nombre:<44} MAE {mae:.3f} | RMSE {rmse:.3f} | Spearman {texto_rho}")


evaluar("Línea base: la media del entrenamiento", prediccion_media,
        "El suelo que hay que superar")
print("\nDesviación típica de y en prueba:", round(float(np.std(y_test)), 3))

# %%
# --- 6.2 Regresión lineal sobre las once métricas del corpus -----------
indices_metricas = [X_modelo.columns.get_loc(c) for c in METRICAS_CORPUS]
lineal_metricas = LinearRegression().fit(X_train[:, indices_metricas], y_train)
evaluar("Regresión lineal (11 métricas clásicas)",
        lineal_metricas.predict(X_test[:, indices_metricas]),
        "Lo que dan las fórmulas de legibilidad")

# %%
# --- 6.3 Añadiendo los seis rasgos propios ------------------------------
lineal_completa = LinearRegression().fit(X_train, y_train)
evaluar("Regresión lineal (11 métricas + 6 rasgos propios)",
        lineal_completa.predict(X_test),
        "Los rasgos propios aportan poco")

# %%
# --- 6.4 Random Forest: ¿el problema es la falta de no linealidad? -----
bosque = RandomForestRegressor(
    n_estimators=300,
    random_state=SEMILLA,
    n_jobs=-1,
).fit(X_train, y_train)
evaluar("Random Forest (300 árboles)", bosque.predict(X_test),
        "Más capacidad no ayuda")

# %%
importancias = pd.Series(bosque.feature_importances_,
                         index=X_modelo.columns).sort_values(ascending=False)
plt.figure(figsize=(7.5, 5))
plt.barh(importancias.index[:12][::-1], importancias.values[:12][::-1],
         color="#55A868")
plt.title("Importancia de variables en el Random Forest")
plt.xlabel("Reducción de impureza (normalizada)")
plt.tight_layout()
plt.show()
print(importancias.head(6).round(3))

# %% [markdown]
# **Figura 12 — Dónde mira el Random Forest.**
#
# El bosque concentra el **34,9 % de su importancia en una sola variable**,
# `New Dale-Chall`, y otro 12,5 % en `CML2RI`. Las seis restantes reparten
# migajas, y ninguno de los rasgos propios entra entre las cinco primeras.
#
# El detalle relevante es que Dale-Chall es, precisamente, **la única métrica
# clásica que consulta una lista de palabras familiares** en vez de contar
# sílabas. Es decir: incluso entre las fórmulas tradicionales, la señal fuerte
# es **léxica**, no tipográfica. Coincide con que `palabras_raras` fuera el mejor
# de los rasgos propios, y anticipa por qué un modelo que conoce el vocabulario
# del inglés —un transformador preentrenado— parte con ventaja.
#
# Y el resultado de conjunto es más elocuente todavía: el Random Forest, con
# capacidad de sobra para relaciones no lineales e interacciones, **no supera a
# la regresión lineal** (RMSE 0,765 frente a 0,748). **El cuello de botella no
# es el algoritmo: es la representación del texto.** Ninguna de estas diecisiete
# variables sabe qué dice el texto.

# %%
# --- 6.5 Clasificación en seis niveles ----------------------------------
# Mismo problema, planteado como clasificación, para poder comparar con la
# literatura y con la etiqueta CEFR. Misma partición que la regresión.
y_nivel = clear["nivel_cefr"].astype(str)
ORDEN_NIVEL = {"C2": 0, "C1": 1, "B2": 2, "B1": 3, "A2": 4, "A1": 5}
codigo_real = y_nivel.iloc[idx_test].map(ORDEN_NIVEL).values

resultados_clf = []


def evaluar_clf(nombre, prediccion, observacion=""):
    """Exactitud y error ordinal medio. El segundo es la métrica justa aquí."""
    exactitud = accuracy_score(y_nivel.iloc[idx_test], prediccion)
    codigo_pred = pd.Series(prediccion).astype(str).map(ORDEN_NIVEL).values
    error_ordinal = float(np.abs(codigo_real - codigo_pred).mean())
    resultados_clf.append({"Modelo": nombre,
                           "Exactitud": round(float(exactitud), 3),
                           "Error ordinal (niveles)": round(error_ordinal, 3),
                           "Observación": observacion})
    print(f"{nombre:<44} exactitud {exactitud:.3f} | error ordinal {error_ordinal:.3f}")


# Primero, con las TRES variables clásicas del experimento original, para que
# la comparación contra los modelos neuronales del Bloque B sea del mismo tipo.
TRES_CLASICAS = ["palabras_por_frase", "diversidad_lexica", "palabras_raras"]
indices_tres = [X_modelo.columns.get_loc(c) for c in TRES_CLASICAS]
logistica_tres = LogisticRegression(max_iter=1000).fit(
    X_train[:, indices_tres], y_nivel.iloc[idx_train])
evaluar_clf("Regresión logística (3 variables clásicas)",
            logistica_tres.predict(X_test[:, indices_tres]),
            "La referencia del experimento original")

# %%
logistica = LogisticRegression(max_iter=1000).fit(X_train, y_nivel.iloc[idx_train])
evaluar_clf("Regresión logística (17 variables)", logistica.predict(X_test),
            "Acierta el vecindario, no el nivel")

# %%
# XGBoost viene preinstalado en Colab. Se importa aquí, y no en el bloque
# inicial, para que su ausencia en un entorno atípico no impida ejecutar el
# resto del cuadernillo.
try:
    from xgboost import XGBClassifier
    XGBOOST_DISPONIBLE = True
except ImportError:
    XGBOOST_DISPONIBLE = False
    print("xgboost no está disponible en este entorno; se omite ese modelo.")

if XGBOOST_DISPONIBLE:
    codificador = LabelEncoder().fit(y_nivel.iloc[idx_train])
    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="mlogloss",
        random_state=SEMILLA,
    ).fit(X_train, codificador.transform(y_nivel.iloc[idx_train]))
    evaluar_clf("XGBoost (17 variables)",
                codificador.inverse_transform(xgb.predict(X_test)),
                "Un ensamble no arregla variables pobres")

# %%
print("Informe de clasificación de la regresión logística:")
print(classification_report(y_nivel.iloc[idx_test], logistica.predict(X_test),
                            zero_division=0))
print("Referencias:")
print("   azar con 6 clases balanceadas :", round(1 / 6, 3))
print("   predecir siempre la clase mayoritaria del entrenamiento:",
      round(float((y_nivel.iloc[idx_test] == y_nivel.iloc[idx_train].mode()[0]).mean()), 3))

# %% [markdown]
# ### Interpretación: hasta dónde llegan las variables de conteo
#
# Tres cifras, en orden:
#
# - Con las **tres variables clásicas** del experimento original: exactitud
#   **0,313**, error ordinal **1,295 niveles**.
# - Con las **diecisiete**: exactitud **0,352**, error ordinal **1,061**.
#   Catorce variables más compran cuatro puntos de exactitud.
# - **XGBoost sobre las mismas diecisiete: 0,340 y 1,081. Es peor que la
#   regresión logística en las dos métricas**, con trescientos árboles y
#   capacidad para modelar interacciones que la logística ni siquiera puede
#   representar.
#
# Ese empate —o esa derrota— es informativo, no decepcionante. Cuando un modelo
# lineal y un ensamble de *gradient boosting* rinden lo mismo sobre las mismas
# variables, **la limitación está en las variables**. Es el mismo diagnóstico que
# dio el Random Forest en regresión, llegando por otro camino.
#
# Vale la pena leer también el informe por clase: los niveles extremos (A1 y C2)
# se recuperan razonablemente y los intermedios (A2, B1, B2) se confunden entre
# sí. Es la traducción numérica de la Figura 11: hay orden, no hay fronteras.
#
# Por eso el error ordinal medio es **la métrica correcta aquí** y la exactitud
# es engañosa: confundir B1 con B2 y confundir B1 con C2 son errores de coste
# radicalmente distinto para el lector, y solo la primera métrica lo refleja.

# %% [markdown]
# ## 6.6 El salto a las redes neuronales
#
# Los modelos anteriores comparten una limitación: **reciben conteos, no texto**.
# El siguiente paso es darles el texto crudo. La progresión que se siguió, y sus
# resultados medidos en su momento sobre esta misma partición (3.774 / 950
# extractos, agrupada por obra), fue:
#
# **a) Embeddings semánticos.** Se representó cada extracto con
# `all-MiniLM-L6-v2` (384 dimensiones) y se entrenó una regresión logística
# encima. Frente a la referencia de tres variables clásicas —exactitud 0,29 y
# error ordinal 1,39 en aquel experimento—, los embeddings dieron **0,37** y
# **0,93 niveles**, con el mismo clasificador: lo único que cambió fue la
# representación.
#
# > **Matiz que el cuadernillo obliga a hacer.** Aquella comparación se hizo
# > contra tres variables, y aquí se ha visto que ampliarlas a diecisiete sube la
# > referencia clásica a 0,352 y 1,061. Es decir, **la ventaja de los embeddings
# > sobre unas variables clásicas bien surtidas es bastante menor de lo que aquel
# > experimento sugería**. La brecha que sí es grande, y que no se cierra con más
# > conteos, es la del transformador que lee el texto: 0,46 y 0,67.
#
# **b) Híbrido embeddings + rasgos clásicos.** Exactitud 0,37, error ordinal
# 0,91. **No mejora**: el embedding ya contiene lo que los rasgos aportaban. Una
# hipótesis razonable, comprobada y descartada.
#
# **c) `roberta-base` afinado en regresión** (125 M parámetros, cabeza de
# regresión sobre `BT_easiness`, 6 épocas, `learning rate` 2e-5, `weight decay`
# 0,01, calentamiento, precisión mixta sobre GPU T4). RMSE **0,560** y
# correlación de Pearson **0,89** sobre los 950 extractos.
#
# > **Sobreajuste, atrapado en el acto — y una salvedad que hay que hacer.** El
# > RMSE mejoró hasta la época 3 (0,560) y a partir de ahí empeoró —época 4:
# > 0,578; época 5: 0,637; época 6: 0,660— mientras la pérdida de entrenamiento
# > seguía bajando. El entrenamiento guardaba un punto de control por época y se
# > quedaba con el mejor (`load_best_model_at_end`), así que **el modelo
# > entregado es el de la época 3, no el de la última**.
# >
# > La salvedad: esos 950 extractos son los que **eligieron la época**, y
# > después son los que dan el 0,560 y el 0,89. Son, por tanto, un conjunto de
# > **validación de selección**, no un test independiente, y así hay que
# > leerlos: la cifra puede ser algo optimista porque se escogió el punto de
# > control que mejor le sentaba. No hubo un tercer conjunto reservado en este
# > experimento histórico. Lo señaló una auditoría externa del proyecto y es
# > justo reconocerlo.
# >
# > Esto afecta a **este** experimento sobre CLEAR, que es el que cuenta por qué
# > hizo falta un transformador. El modelo desplegado, el v4, se entrenó y se
# > midió con otro corpus, y sus propias limitaciones —incluida la de que su
# > conjunto de validación no puede recalcularse desde este cuadernillo— se
# > tratan en su sección.
#
# **d) El modelo v4, que es el que está desplegado.** Es un afinado de
# **`distilroberta-base`** —la variante destilada, la mitad de capas que
# `roberta-base`— con una cabeza de **regresión** y las constantes de troceado
# que se justifican en la §2.2: bloques de **250 palabras**, mínimo **150**,
# hasta **8 bloques por documento** repartidos por todo el texto, `MAX_LENGTH`
# **256**, media sin ponderar, escala interna 0–5 y escala pública 0–2.
#
# La elección de la versión destilada fue **deliberada y de producto**: la
# aplicación tiene que puntuar libros enteros en una demo en vivo, y un modelo
# con la mitad de capas puntúa sensiblemente más ventanas por segundo.
# Con `roberta-base`, la curva de dificultad capítulo a capítulo de una novela
# larga dejaría de ser interactiva.
#
# **Aviso de reproducibilidad, otra vez y en su sitio:** el guion de
# entrenamiento del v4 no forma parte del repositorio de la aplicación —el
# repositorio contiene el producto, no el experimento— y **los pesos todavía no
# están publicados**. Lo que sigue está preparado para cargarlos en cuanto lo
# estén.

# %%
# ============================================================
#  LA CASILLA QUE HAY QUE RELLENAR
# ============================================================
# Cuando el modelo v4 se publique en Hugging Face, escribir aquí el
# identificador del repositorio, por ejemplo "usuario/literalevel-v4".
# Mientras esta variable esté vacía, el cuadernillo sigue funcionando: las
# celdas que necesitan los pesos avisan y se saltan solas.

URL_MODELO = ""          # <--- rellenar aquí

# ============================================================

MODELO_DISPONIBLE = False
tokenizador_v4 = None
modelo_v4 = None

if URL_MODELO.strip():
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        tokenizador_v4 = AutoTokenizer.from_pretrained(URL_MODELO)
        modelo_v4 = AutoModelForSequenceClassification.from_pretrained(URL_MODELO)
        modelo_v4.eval()
        MODELO_DISPONIBLE = True
        print("Modelo v4 cargado desde:", URL_MODELO)
    except Exception as error:
        print("No se pudo cargar el modelo desde", URL_MODELO)
        print("  ", type(error).__name__, ":", error)
        print("El cuadernillo continúa sin él.")
else:
    print("URL_MODELO está vacía.")
    print()
    print("El modelo v4 (332 MB) aún no se ha publicado: hoy existe solo en el")
    print("disco del autor y en una carpeta privada de Drive. En cuanto se")
    print("publique en Hugging Face, basta con escribir su identificador arriba")
    print("y volver a ejecutar desde esta celda.")
    print()
    print("Lo que sí se ha calculado de verdad en esta ejecución: el corpus")
    print("completo, todo el análisis exploratorio, la ingeniería de variables")
    print("y los siete modelos de referencia. Lo que se reporta sin recalcular:")
    print("las métricas del v4, medidas en su momento y detalladas en la §7.")

# %%
# --- Las constantes y el troceado del sistema desplegado ----------------
# Copia literal de `app/scoring.py`. Se reproduce aquí para que el cuadernillo
# sea autocontenido y para poder enseñar el troceado aunque los pesos no estén.
BLOCK_WORDS = 250          # tamaño de la ventana, en palabras
MIN_WORDS = 150            # por debajo de esto no se puntúa
MAX_BLOCKS_PER_DOC = 8     # ventanas por documento en el modo rápido
MAX_LENGTH = 256           # subtokens BPE por ventana


def ventanas_fijas(texto, tamano=BLOCK_WORDS, minimo=MIN_WORDS,
                   tope=MAX_BLOCKS_PER_DOC):
    """Ventanas de tamaño fijo, repartidas por todo el documento.

    La cola corta se cubre retrocediendo la última ventana, de modo que la
    longitud total del documento nunca llega al modelo como señal.
    """
    palabras = PALABRA_RE.findall(texto)
    n = len(palabras)
    if n < minimo:
        return []
    if n <= tamano:
        return [" ".join(palabras)]
    inicios = list(range(0, n - tamano + 1, tamano))
    ultimo = n - tamano
    if inicios[-1] != ultimo:
        inicios.append(ultimo)
    if len(inicios) > tope:
        elegidos = np.linspace(0, len(inicios) - 1, tope).round().astype(int)
        inicios = [inicios[i] for i in sorted(set(elegidos.tolist()))]
    return [" ".join(palabras[i:i + tamano]) for i in inicios]


def puntuacion_publica(y):
    """Escala interna 0-5 -> escala pública 0-2."""
    return float(np.clip(y, 0, 5) * 0.4)


def banda_publica(puntuacion):
    if puntuacion < 0.8:
        return "básico"
    if puntuacion < 1.6:
        return "intermedio"
    return "avanzado"


print("Constantes del v4 cargadas.")
print("Ventana:", BLOCK_WORDS, "palabras | mínimo:", MIN_WORDS,
      "| tope por documento:", MAX_BLOCKS_PER_DOC, "| máx. subtokens:", MAX_LENGTH)

# %%
# --- El troceado, demostrado sobre un documento largo -------------------
# Se construye un documento largo concatenando extractos del corpus. Es texto
# real y no requiere descargar nada más.
documento_largo = " ".join(clear["Excerpt"].head(30).tolist())
palabras_totales = len(PALABRA_RE.findall(documento_largo))

muestreo = ventanas_fijas(documento_largo)
completo = ventanas_fijas(documento_largo, tope=10 ** 9)

print("Documento de prueba:", f"{palabras_totales:,}", "palabras")
print("Ventanas en el modo rápido (tope de 8):", len(muestreo))
print("Ventanas en el recorrido completo:      ", len(completo))
print("Palabras por ventana (todas iguales):",
      sorted(set(len(PALABRA_RE.findall(v)) for v in completo)))
print()
print("Texto demasiado corto ->", ventanas_fijas("Solo unas pocas palabras sueltas."),
      "(lista vacía, no excepción)")

# %% [markdown]
# ### Interpretación: por qué el muestreo de 8 ventanas es defendible
#
# El troceado hace lo que promete: **todas las ventanas miden exactamente 250
# palabras**, sin excepción, incluida la última. Por eso la longitud del
# documento no puede filtrarse como señal, y por eso todas las ventanas ocupan
# el mismo tensor de 256 subtokens sin relleno.
#
# La pregunta de producto es si ocho ventanas bastan para representar un libro
# entero. **Está medida y la respuesta es sí:** sobre un mismo texto, el muestreo
# de 8 ventanas da **1,784** y el recorrido completo da **1,743**. Cuatro
# centésimas sobre una escala de 0 a 2, dentro de la misma banda pública.
#
# La aplicación ofrece las dos opciones y **declara cuál usó**. El modo rápido es
# el predeterminado para la búsqueda y la ficha; el recorrido completo se
# reserva para la curva de dificultad capítulo a capítulo, donde el objetivo no
# es una cifra sino un perfil, y para el precálculo del catálogo de la §8.

# %%
# --- Puntuación con el v4, si está disponible ---------------------------
def puntuar_ventanas(ventanas):
    """Puntuación pública 0-2 de cada ventana. Requiere el modelo cargado."""
    if not MODELO_DISPONIBLE:
        return []
    entradas = tokenizador_v4(ventanas, truncation=True, max_length=MAX_LENGTH,
                              padding=True, return_tensors="pt")
    with torch.no_grad():
        salida = modelo_v4(**entradas).logits.squeeze(-1).float().numpy()
    return [round(puntuacion_publica(v), 3) for v in np.atleast_1d(salida)]


if MODELO_DISPONIBLE:
    largos = clear[clear["palabras_excerpt"] >= MIN_WORDS]
    mas_facil = largos.loc[largos["BT_easiness"].idxmax()]
    mas_dificil = largos.loc[largos["BT_easiness"].idxmin()]
    for etiqueta, fila in [("MÁS FÁCIL del corpus", mas_facil),
                           ("MÁS DIFÍCIL del corpus", mas_dificil)]:
        valores = puntuar_ventanas(ventanas_fijas(fila["Excerpt"]))
        media = float(np.mean(valores))
        print(f"{etiqueta:<24} BT_easiness {fila['BT_easiness']:.3f}"
              f" -> v4 {media:.3f} ({banda_publica(media)})")
else:
    print("Sin modelo cargado: esta comprobación se omite.")
    print("Con URL_MODELO rellena, esta celda puntúa el extracto más fácil y el")
    print("más difícil del corpus y comprueba que el v4 los ordena bien.")

# %% [markdown]
# # 7. Evaluación
#
# ## 7.1 Todos los modelos, en una tabla
#
# Dos bloques, separados a propósito. El primero se **calcula en esta ejecución**
# y sus cifras cambian si alguien cambia la semilla. El segundo se **midió en su
# momento** y se reporta sin recalcular, porque exige horas de GPU o los pesos
# que aún no están publicados.

# %%
tabla_regresion = pd.DataFrame(resultados)
print("BLOQUE A — modelos de regresión calculados en esta ejecución")
print("            (950 extractos de prueba, agrupados por obra)")
print()
print(tabla_regresion.to_string(index=False))

# %%
tabla_clasificacion = pd.DataFrame(resultados_clf)
print("BLOQUE A (continuación) — clasificación en seis niveles")
print()
print(tabla_clasificacion.to_string(index=False))

# %%
tabla_reportada = pd.DataFrame([
    {"Modelo": "Embeddings MiniLM + reg. logística",
     "Métrica principal": "exactitud 0.37",
     "Error ordinal": "0.93",
     "Observación": "El mayor salto del proyecto: cambió la representación"},
    {"Modelo": "Híbrido embeddings + rasgos clásicos",
     "Métrica principal": "exactitud 0.37",
     "Error ordinal": "0.91",
     "Observación": "Hipótesis descartada: no aporta sobre el embedding"},
    {"Modelo": "roberta-base afinado (regresión)",
     "Métrica principal": "RMSE 0.560 · Pearson 0.89",
     "Error ordinal": "0.67",
     "Observación": "Mejor época 3; de la 4 en adelante, sobreajuste"},
    {"Modelo": "v4 · distilroberta-base + ventanas",
     "Métrica principal": "Spearman 0.908 · 97.2 % dentro de +-1 nivel",
     "Error ordinal": "—",
     "Observación": "MODELO DESPLEGADO. n = 144, corpus de validación"},
])
print("BLOQUE B — resultados medidos en su momento, NO recalculados aquí")
print()
print(tabla_reportada.to_string(index=False))

# %% [markdown]
# ### Interpretación de la comparación
#
# La progresión es monótona y **cada escalón tiene una explicación, no es
# casualidad**:
#
# - Predecir la media da RMSE 1,048, que es la desviación típica de la variable.
#   Es el suelo.
# - Las once métricas clásicas bajan a **0,764**. Un 27 % de mejora sobre no
#   hacer nada, con fórmulas de los años cuarenta.
# - Añadir los seis rasgos propios llega a **0,748**. Mejora real pero pequeña.
# - El Random Forest **no mejora** a la regresión lineal (0,765). Cuando más
#   capacidad no compra nada, el problema son las variables.
# - `roberta-base`, leyendo el texto, baja a **0,560**. Es un 25 % mejor que la
#   mejor combinación de conteos, y el salto se produce **sin ninguna variable
#   nueva**: el modelo la construye por su cuenta.
#
# El v4 aparece en otra fila y con otra métrica porque **resuelve un problema
# distinto**: no puntúa extractos de 175 palabras, puntúa libros de medio millón.
# Su cifra —Spearman 0,908 sobre 144 textos de validación, 97,2 % dentro de un
# nivel— no es comparable con las anteriores y sería deshonesto ponerla en la
# misma columna.

# %% [markdown]
# ## 7.2 Validación externa ciega
#
# La prueba que de verdad sostiene el trabajo no es ninguna de las anteriores,
# porque todas comparten corpus con el entrenamiento. Es esta: **textos con nivel
# MCER oficial, de una fuente ajena al proyecto, que el modelo nunca vio**.
#
# Se usaron los textos de lectura graduada de **British Council**, cada uno con
# su nivel oficial en el nombre del archivo. El material tiene derechos y no se
# distribuye; el guion de validación del repositorio (`validar_local.py`) no
# imprime ni un fragmento, solo puntuaciones.

# %%
validacion_externa = pd.DataFrame({
    "Nivel oficial": ["A1", "A2", "B1", "B2", "C1"],
    "n": [3, 7, 12, 11, 12],
    "Media v4 (escala 0-2)": [0.5040, 0.5480, 0.9276, 1.2478, 1.4952],
})
print("Validación externa: British Council, 45 textos legibles en local")
print()
print(validacion_externa.to_string(index=False))

medias = validacion_externa["Media v4 (escala 0-2)"].tolist()
print()
print("Orden estrictamente creciente de A1 a C1:",
      all(a < b for a, b in zip(medias, medias[1:])))

# %%
plt.figure(figsize=(6.5, 4))
plt.plot(validacion_externa["Nivel oficial"],
         validacion_externa["Media v4 (escala 0-2)"],
         marker="o", linewidth=2, color="#4C72B0")
for _, fila in validacion_externa.iterrows():
    plt.annotate(f"{fila['Media v4 (escala 0-2)']:.3f}",
                 (fila["Nivel oficial"], fila["Media v4 (escala 0-2)"]),
                 textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
plt.axhline(0.8, color="#937860", linestyle=":", linewidth=1)
plt.axhline(1.6, color="#937860", linestyle=":", linewidth=1)
plt.title("Puntuación media del v4 por nivel MCER oficial")
plt.xlabel("Nivel oficial del texto (British Council)")
plt.ylabel("Puntuación media en la escala pública 0-2")
plt.ylim(0, 2)
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 13 — La curva que sostiene el proyecto.**
#
# Las líneas punteadas son los cortes de las bandas públicas: 0,8 y 1,6.
#
# **La curva sube de forma estrictamente creciente en los cinco niveles**, sin
# una sola inversión, sobre un corpus que el modelo no vio nunca y con niveles
# asignados por examinadores humanos. Ese es el resultado que respalda todo lo
# demás.
#
# Y sin embargo la figura muestra también, con la misma claridad, **dos
# limitaciones que hay que enunciar antes de que las señale otro**:
#
# 1. **La escala está comprimida.** Contra el ancla real, el ajuste ronda
#    `predicho ≈ 0,72 × real + 0,38`. Los cinco niveles ocupan de 0,50 a 1,50
#    en una escala de 0 a 2: el modelo **ordena bien y estima corto**. Un texto
#    A2 puntúa cerca de donde debería puntuar un B1. Por eso el producto muestra
#    bandas y no una letra.
# 2. **A1 y A2 casi no se distinguen** (0,504 frente a 0,548), y A1 tiene tres
#    textos. El extremo fácil de la escala está mal resuelto, y con esa n no se
#    puede afirmar nada más.
#
# Conviene además reportar el contraste que hace honesta la cifra: **contar las
# palabras del texto, sin modelo alguno, alcanza Spearman 0,807 en este mismo
# corpus**, frente a 0,854 del v4. En los exámenes graduados, nivel y longitud
# están confundidos. Lo que sostiene al modelo no es ganarle a un contador de
# palabras por cinco centésimas, sino que **aporta señal por encima de la
# longitud**: descontándola por correlación parcial, el modelo conserva 0,657, y
# un contador de palabras, por construcción, se queda en cero.

# %% [markdown]
# ## 7.3 Decisiones de despliegue que también son evaluación
#
# Dos mediciones más, hechas sobre el modelo ya entrenado, que cambiaron el
# producto. Se reportan aquí porque una evaluación que solo mira métricas de
# calidad y no mira coste está incompleta para un sistema que tiene que
# funcionar en vivo.

# %%
decisiones = pd.DataFrame([
    {"Prueba": "Muestreo de 8 ventanas vs. recorrido completo",
     "Resultado": "1.784 vs 1.743 sobre la escala 0-2",
     "Decisión": "ACEPTADO: se ofrecen los dos modos y se declara cuál se usó"},
    {"Prueba": "Cuantización dinámica a int8",
     "Resultado": "+18 % de velocidad, MAE 0.210 sobre 2, sesgo -0.21",
     "Decisión": "DESCARTADO: cruza la frontera de banda en 1.6"},
    {"Prueba": "Media precisión (fp16) en GPU de consumo",
     "Resultado": "4,5 veces MÁS LENTA que fp32 en una GTX 1650 SUPER",
     "Decisión": "DESCARTADO en esa tarjeta: un TU116 no tiene tensor cores"},
    {"Prueba": "Agrupar ventanas en lotes fijos de 64 en vez de por capítulo",
     "Resultado": "+18 % de velocidad, 300/300 valores idénticos bit a bit",
     "Decisión": "ADOPTADO: no hay relleno, así que no puede cambiar nada"},
])
print(decisiones.to_string(index=False))

# %% [markdown]
# ### Interpretación: una optimización rechazada por razones de producto
#
# La cuantización a int8 es el caso interesante. Da **un 18 % de velocidad
# gratis**, que en un sistema que tiene que medir 61.642 libros no es poco. Y se
# rechazó.
#
# El motivo no es que el error sea grande en abstracto, sino **dónde cae**: un
# MAE de 0,210 sobre una escala de 0 a 2, con sesgo sistemático a la baja de
# −0,21, mueve un texto de 1,68 a 1,47. Y **el corte entre «intermedio» y
# «avanzado» está en 1,60**. Es decir, la optimización no degrada la cifra: le
# cambia la etiqueta al libro. Un lector recibiría una recomendación distinta
# según con qué precisión se hubiera compilado el modelo.
#
# Es el tipo de decisión que solo aparece cuando se evalúa el sistema contra el
# uso real y no contra una métrica agregada. La misma prueba, mirando solo el
# MAE, habría dicho «error pequeño, adelante».

# %% [markdown]
# # 8. Estrategia de negocio
#
# ## 8.1 Los usuarios, y qué necesita cada uno
#
# | Usuario | Quién es | Qué necesita | Qué le da LiteraLevel |
# |---|---|---|---|
# | **El lector autodidacta** | Hispanohablante con inglés intermedio que quiere leer de verdad, no hacer ejercicios | Saber si *este* libro le queda grande **antes** de empezarlo | Una cifra y una banda por libro, y un catálogo filtrado por su nivel |
# | **El estudiante de bachillerato** | Perfil de la primera lectora ajena al proyecto: 15 años, preparatoria | Que no se sienta tonta usando la herramienta | Etiquetas reescritas y una interfaz que explica en vez de suponer |
# | **El docente de inglés** | Prepara material graduado a mano, texto por texto | Medir un texto propio y encontrar lecturas de un nivel dado | Pega el texto y obtiene la medida; busca por nivel en el catálogo |
# | **La propia plataforma** | El catálogo, como activo | Ordenar 61.642 libros sin intervención humana | Precálculo masivo, medido y reanudable |
#
# ## 8.2 El ciclo de usuario que sí se hizo, con su corrección
#
# La primera persona ajena al proyecto que usó la aplicación fue **Esmeralda, 15
# años, de preparatoria**. Sus tres frases textuales son el material más valioso
# que produjo el proyecto:
#
# > *«está bien difícil de usar en celular»* · *«la página se siente antigua»* ·
# > **«o yo soy muy tonta para esto»**
#
# La tercera es la que importa, y no es una queja de estilo: **es un fallo de
# diseño documentado**. Cuando una usuaria concluye que el problema es ella, la
# herramienta ha fallado en explicarse. La corrección fue concreta y medible:
# **seis etiquetas reescritas y cinco paletas de color probadas**.
#
# Un ciclo así —usuaria real, frase textual, diagnóstico, corrección
# verificable— vale más para este apartado que cualquier estimación de mercado,
# porque es evidencia de primera mano y es reproducible como método.
#
# ## 8.3 El accionable principal, con su coste calculado

# %%
# --- Cuánto cuesta medir el catálogo entero -----------------------------
# Velocidades MEDIDAS sobre el modelo v4, extremo a extremo.
LIBROS = int(len(libros_en))
VENTANAS_POR_LIBRO = 350        # SUPUESTO de trabajo, no una medición

velocidades = pd.DataFrame([
    {"Dispositivo": "CPU (Ryzen 5 2600, 12 hilos, lote 64)", "Ventanas/s": 8.7},
    {"Dispositivo": "GPU local (GTX 1650 SUPER, fp32, lote 128)", "Ventanas/s": 101.7},
    {"Dispositivo": "GPU de nube (A100)", "Ventanas/s": 2022.0},
])
ventanas_totales = LIBROS * VENTANAS_POR_LIBRO
velocidades["Horas para el catálogo"] = (
    ventanas_totales / velocidades["Ventanas/s"] / 3600).round(1)
velocidades["Días"] = (velocidades["Horas para el catálogo"] / 24).round(1)

print("Libros de texto en inglés en el catálogo:", f"{LIBROS:,}")
print("Ventanas por libro (supuesto de trabajo):", VENTANAS_POR_LIBRO)
print("Ventanas totales a puntuar:", f"{ventanas_totales:,}")
print()
print(velocidades.to_string(index=False))

# %%
plt.figure(figsize=(7, 3.8))
plt.barh(velocidades["Dispositivo"], velocidades["Horas para el catálogo"],
         color=["#C44E52", "#DD8452", "#55A868"])
plt.xscale("log")
plt.title("Coste de medir el catálogo completo, por dispositivo (escala log)")
plt.xlabel("Horas de cómputo")
for i, v in enumerate(velocidades["Horas para el catálogo"]):
    plt.text(v * 1.1, i, f"{v:,.1f} h", va="center", fontsize=9)
plt.tight_layout()
plt.show()

# %% [markdown]
# **Figura 14 — El argumento económico del proyecto, en una figura.**
#
# Medir los 61.642 libros del catálogo cuesta **unas 689 horas en la CPU de una
# computadora de escritorio —veintiocho días seguidos— y unas tres horas en una
# A100**. El factor entre los dos extremos es de **232 veces**, y la escala del
# eje es logarítmica precisamente para que quepan los dos.
#
# Ese es el accionable, y es de negocio antes que técnico: **el precálculo no se
# hace en el equipo del usuario ni en el servidor de la aplicación; se hace una
# vez en la nube y se sirve ya calculado**. La aplicación no puntúa un libro
# cuando alguien lo busca: lo busca ya medido. Y como el trabajo es reanudable
# por lotes, una sesión de nube que se corte no pierde lo hecho.
#
# **Advertencia sobre este cálculo:** las tres velocidades están medidas, pero
# las 350 ventanas por libro son **un supuesto de trabajo**, no una medición. Es
# un supuesto conservador para la media del catálogo —*Crimen y castigo* son 840
# ventanas y *Guerra y paz* 2.459, pero la mediana de Gutenberg está muy por
# debajo de una novela rusa—; aun así, cualquier lectura de esta tabla hereda esa
# incertidumbre y hay que decirlo.
#
# ## 8.4 Los accionables, en orden y con su justificación
#
# 1. **Publicar el modelo v4 y el diccionario en Hugging Face.** Es media hora
#    de trabajo y desbloquea la reproducibilidad completa de este cuadernillo,
#    que hoy es su única carencia. Es el primero de la lista por relación entre
#    coste y efecto.
# 2. **Ejecutar el precálculo del catálogo en A100.** Tres horas de nube
#    convierten 61.642 libros sin medir en 61.642 libros medidos **libro entero,
#    capítulo a capítulo**, y jubilan definitivamente las etiquetas del v1 cuyo
#    fracaso documenta la Figura 8.
# 3. **Despliegue permanente de la interfaz.** El enlace actual es temporal y
#    muere al apagar la computadora. Consumo medido: **1,05 GB de RSS** con
#    modelo y catálogo cargados, con pico realista de 1,2-1,5 GB, y 562 MB en
#    disco. Eso **descarta todos los planes de 512 MB de memoria** y acota la
#    decisión a opciones de pago, con cifras y no con impresiones.
# 4. **Cerrar el ciclo de usuario con más lectores como Esmeralda.** El primero
#    produjo seis correcciones concretas. No hay razón para pensar que el
#    segundo produzca menos.
#
# ## 8.5 Usabilidad: cómo se presenta el modelo al usuario
#
# Tres reglas de presentación, y las tres salen de resultados de este cuadernillo
# y no de preferencias estéticas:
#
# - **Se muestra una banda, no una letra.** Básico, intermedio, avanzado. Lo
#   justifica la Figura 11 —los niveles se ordenan pero no se separan— y lo
#   confirma la compresión de escala de la Figura 13.
# - **Se declara el modo de medición.** La ficha del libro dice si la cifra sale
#   del muestreo de 8 ventanas o del recorrido completo. El usuario tiene derecho
#   a saber con cuánta evidencia se le está hablando.
# - **Se avisa, no se filtra.** El catálogo no se poda por contenido: es una
#   plataforma de literatura, y podar por materias tiraría obras que son
#   literatura por derecho propio. En su lugar, la ficha del libro trae un aviso
#   cuando la obra tiene algo que conviene saber de antemano. Informar al lector y
#   dejarle elegir, en vez de elegir por él.

# %% [markdown]
# # 9. Conclusiones y recomendaciones
#
# ## 9.1 Lo que se concluye
#
# **1. El problema es real y la aproximación clásica no lo resuelve.** Sobre las
# diecisiete variables de conteo, todos los modelos se quedan en la misma zona:
# la regresión lineal llega a Spearman 0,707 y un Random Forest con trescientos
# árboles se queda en 0,686, por debajo. Dar más capacidad al algoritmo no
# cambia el resultado. **El cuello de botella nunca fue el algoritmo: fue la
# representación del texto.**
#
# **2. Cada vez que se enriqueció la representación, el resultado subió.**
# Conteos → embeddings → transformador que lee el texto: exactitud 0,29 → 0,37 →
# 0,46; error ordinal 1,39 → 0,93 → 0,67 niveles; RMSE 0,748 → 0,560. La
# progresión es monótona y cada escalón tiene una explicación.
#
# **3. El modelo desplegado ordena bien y estima corto.** Spearman 0,908 en
# validación y, sobre todo, **medias estrictamente crecientes de A1 a C1 en un
# corpus externo con nivel oficial**. Pero la escala está comprimida
# (`predicho ≈ 0,72 × real + 0,38`) y los dos niveles más bajos casi no se
# distinguen. **Sirve para ordenar un catálogo; no sirve para certificar a
# nadie**, y el producto lo dice en pantalla.
#
# **4. Leer el documento entero importó más que cambiar de modelo.** El fallo más
# caro del proyecto no fue de arquitectura: fue puntuar cada libro por sus
# primeras ~190 palabras. De ahí salió un catálogo con el 60 % de los libros
# etiquetados A1 (Figura 8). El troceado en ventanas fijas lo corrigió sin tocar
# los pesos.
#
# **5. Las decisiones de despliegue son parte de la evaluación.** La cuantización
# int8 pasaba la prueba de MAE y se rechazó porque su sesgo cruzaba una frontera
# de banda. Una evaluación que no mira dónde caen los errores no es suficiente
# para un sistema que se pone delante de un usuario.
#
# ## 9.2 Limitaciones
#
# 1. **La escala pública 0-2 es propia.** El MCER es el ancla con la que se
#    entrenó, no un certificado que se emita.
# 2. **La escala está comprimida y sesgada a la baja** frente al ancla real, y
#    A1 y A2 son prácticamente indistinguibles (0,504 frente a 0,548, con n = 3
#    en A1).
# 3. **El dominio confunde la medida.** El texto informativo puntúa medio punto
#    más difícil que el literario con la misma sintaxis (Figura 6); el modelo no
#    ve esa distinción.
# 4. **La validación externa es pequeña**: 45 textos legibles de 59, y el corpus
#    tiene derechos, así que no se distribuye ni se puede auditar desde fuera.
# 5. **Las cifras de 0,908 y 97,2 % no son verificables desde el repositorio**,
#    porque el corpus de validación de 144 textos no está incluido.
# 6. **El guion de entrenamiento del v4 no forma parte del repositorio.** Este
#    cuadernillo reproduce la cadena de datos, el EDA y los modelos de
#    referencia, no el afinado final.
# 7. **Este cuadernillo no es hoy 100 % reproducible**, por la única razón que se
#    enuncia abajo.
#
# ## 9.3 Lo que falta para que esto sea reproducible al cien por cien
#
# Una sola cosa, y no es técnica: **publicar los pesos del v4**. En cuanto exista
# el repositorio en Hugging Face, se escribe su identificador en `URL_MODELO`
# (§6.6) y este cuadernillo pasa de ejecutarlo casi todo a ejecutarlo entero.
# No hace falta cambiar ninguna otra línea.
#
# Mientras tanto, lo que sí se calcula en cada ejecución es: la descarga y
# validación de las 4.724 filas del corpus de entrenamiento, la descarga del
# catálogo completo de Project Gutenberg, las once figuras del análisis
# exploratorio, la ingeniería de seis rasgos lingüísticos, la partición sin fuga
# y los siete modelos de referencia con sus métricas.
#
# ## 9.4 Recomendaciones y trabajo futuro
#
# 1. **Publicar el modelo y el diccionario.** Es lo primero por coste-beneficio.
# 2. **Recalibrar la escala pública con una transformación afín** ajustada sobre
#    el ancla externa. El proyecto ya usó esa técnica con éxito en una iteración
#    anterior (`y = 0,322 x − 0,832`), corrigiendo la magnitud **sin tocar los
#    pesos** ni el orden aprendido. Es la vía natural para atacar la compresión de
#    escala de la Figura 13.
# 3. **Ampliar la validación externa**, sobre todo en A1 y A2, que es donde la
#    evidencia es más fina y donde están los lectores que más ayuda necesitan.
# 4. **Modelar el dominio explícitamente**, o al menos avisar en la ficha cuando
#    el libro es informativo, dado el desplazamiento medido en la Figura 6.
# 5. **Ejecutar el precálculo completo** y retirar definitivamente las etiquetas
#    heredadas del v1.
#
# ---
#
# ## Referencias
#
# Bradley, R. A., & Terry, M. E. (1952). Rank analysis of incomplete block
# designs: I. The method of paired comparisons. *Biometrika, 39*(3/4), 324-345.
#
# Council of Europe. (2020). *Common European Framework of Reference for
# Languages: Learning, teaching, assessment. Companion volume*. Council of
# Europe Publishing.
#
# Crossley, S., Heintz, A., Choi, J. S., Batchelor, J., Karimi, M., &
# Malatinszky, A. (2023). A large-scaled corpus for assessing text readability.
# *Behavior Research Methods*.
#
# Gerlach, M., & Font-Clos, F. (2020). A standardized Project Gutenberg corpus
# for statistical analysis of natural language and quantitative linguistics.
# *Entropy, 22*(1), 126.
#
# Liu, Y., Ott, M., Goyal, N., Du, J., Joshi, M., Chen, D., Levy, O., Lewis, M.,
# Zettlemoyer, L., & Stoyanov, V. (2019). *RoBERTa: A robustly optimized BERT
# pretraining approach*. arXiv:1907.11692.
#
# Project Gutenberg. (2026). *Project Gutenberg catalog feed*.
# https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv
#
# Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). *DistilBERT, a distilled
# version of BERT: Smaller, faster, cheaper and lighter*. arXiv:1910.01108.
#
# Vajjala, S., & Lucic, I. (2018). OneStopEnglish corpus: A new corpus for
# automatic readability assessment and text simplification. En *Proceedings of
# the 13th Workshop on Innovative Use of NLP for Building Educational
# Applications* (pp. 297-304). Association for Computational Linguistics.
