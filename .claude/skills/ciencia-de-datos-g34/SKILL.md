---
name: ciencia-de-datos-g34
description: Convenciones, métodos y criterios de evaluación del Diplomado en Ciencia de Datos de la FES Acatlán (UNAM), Generación 34. Úsala al trabajar en cualquier práctica, examen o proyecto del diplomado — notebooks de Colab, documentos en LaTeX, EDA, modelado supervisado o no supervisado, redes neuronales, NLP, PySpark — o al preparar una entrega para los profesores Raúl López Benítez, Carla Malerva, Oscar Acosta o Fernando Barranco.
---

# Diplomado en Ciencia de Datos — FES Acatlán, Generación 34

Destilación del material del diplomado (enero–septiembre 2026). Todo lo que sigue está
verificado contra el material real; cada afirmación lleva su fuente entre paréntesis.

> ## ⚠️ Antes de aplicar nada: los criterios son POR MÓDULO y se contradicen
>
> Este documento reúne cinco módulos con cinco profesores distintos, y **lo que
> exige uno lo prohíbe otro**. Aplicar aquí la regla de allá es la forma más
> fácil de perder puntos. Los choques comprobados:
>
> | Asunto | Módulo 2 (Raúl López) | Módulo 5 (Fernando Barranco) |
> |---|---|---|
> | Kaggle como fuente de datos | **Recomendado** | **Prohibido** |
> | Código en el documento | **Prohibido**, ni capturas | No se prohíbe |
> | Extensión | máx. 16 páginas | sin tope declarado |
> | Uso de IA generativa | restringido en algunas tareas | **objetivo declarado del módulo** |
>
> **Para el proyecto en curso —LiteraLevel, módulo 5— manda la sección 4.5 y
> nada más.** El resto del documento sirve como memoria de cómo se trabaja en
> este diplomado (estilo de código, convenciones, métodos), no como criterio de
> evaluación. Si una regla de otro módulo choca con la rúbrica del 5, gana el 5.

## 0. Mapa del diplomado

| Módulo | Título / tema | Profesor | Proyecto |
|---|---|---|---|
| 1 | Introducción a la ciencia de datos, bases de datos, EDA | Raúl López Benítez | No (solo "Base de datos Proyecto": elegir y describir el dataset) |
| 2 | Aprendizaje supervisado | Raúl López Benítez | Sí — documento PDF, máx. 16 págs |
| 3 | Aprendizaje no supervisado: reducción de dimensión y clustering | Carla Malerva | Sí — zip con PDF + notebook + .py + pptx + video |
| 4 | Técnicas cognitivas e Introducción a Big Data (redes neuronales, NLP, visión, PySpark) | Oscar Daniel Acosta González | Sí — documento científico con enfoque a negocio, PDF |
| 5 | Integrador (proyecto de punta a punta con interfaz desplegada) | Mtro. Fernando Barranco Rodríguez | Sí — el trabajo final del diplomado, 110 puntos |

Todo el diplomado se opera por **Google Classroom** (una clase por módulo, más una clase
"Coordinación Diplomado Ciencia de Datos Generación 34"); el material se comparte por carpetas de
Drive enlazadas desde los anuncios. Al cerrar cada módulo la coordinación abre una tarea
"Opinión Ciencia de Datos (Módulo N)" para evaluar al ponente. En los módulos 3 y 4 hay además
evaluación continua: quizzes en el 3 y un **"Microtest" antes de casi cada clase** en el 4 (ver
un video y contestar).

---

## 1. Reglas de oro (lo que reprueba o baja calificación)

Estas son correcciones y advertencias explícitas de los profesores. Valen más que cualquier
otra cosa de este documento.

1. **"LAS VARIABLES NOMINALES NO ENTRAN A LA MATRIZ DE CORRELACIÓN. Si veo esto en sus
   proyectos automáticamente tienen cero."** Para asociación entre categóricas: tablas de
   contingencia y coeficientes de asociación (Cramér's V, chi-cuadrada), nunca Pearson.
   (Raúl López, anuncio de Classroom del 12 abr 2026, [G34] Módulo 2)
2. **Nada de plots o tablas sin interpretación.** "No colocar plots o tablas sin un fin o sin
   interpretación." Cada figura debe ir numerada, referenciada en el texto y explicada. (ídem)
3. **Si usas ensembles y es tu mejor modelo, incluye el plot de importancia de variables e
   interprétalo.** (ídem)
4. **Extensión máxima del documento del módulo 2: 16 páginas. No se aceptan trabajos más
   largos.** (ídem)
5. **NO incluir código ni capturas de pantalla en el documento** del módulo 2. El documento es
   prosa científica; el código va en el notebook. (`Modulo2_Proyecto.pdf`, Raúl López)
6. **"RESULTADOS, no solo lectura de estadígrafos."** Interpretar lo que significa el número
   para el problema, no recitar la métrica. (Oscar Acosta, tarea Proyecto, módulo 4)
7. **Si falta una sección, el trabajo no se considera.** Cubrir *todas* las secciones pedidas.
   (`1.1 Proyecto Final, modulo 3.pdf`, Carla Malerva)
8. **El notebook debe correr sin un solo error**, de principio a fin, desde cualquier entorno de
   Colab. "Si tienen errores no se considerará" (M3) / "sin errores, warnings, fallos de conexión
   a datos" (rúbrica M5).
9. **Kaggle está baneado como fuente de datos en el módulo 5.** Se esperan APIs, web scraping o
   datos corporativos. (`BienvenidaMdulo5.pdf` y `TrabajoFinal-Rbrica.pdf`)
10. **Ortografía y redacción se califican.** Aparece en las instrucciones de los módulos 2, 3 y 5.

---

## 2. Herramientas y convenciones reales

**Entorno.** Google Colab es el entorno por defecto de todos los módulos. Los datos se montan
desde Drive:

```python
from google.colab import drive
drive.mount('/content/drive')
ruta = "/content/drive/MyDrive/proyecto modulo 3/"
```

Para archivos sueltos en prácticas cortas se usa `from google.colab import files; files.upload()`.

**Stack por módulo** (verificado en los notebooks entregados):

- **Módulos 1–2 (supervisado):** `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`
  (`train_test_split`, `StandardScaler`, `MinMaxScaler`, `LabelEncoder`, `OrdinalEncoder`,
  `LogisticRegression`, `RandomForestClassifier`, métricas), `xgboost`. Y tres que solo aparecen
  aquí: **`plotly`** (`express`, `graph_objects`, `make_subplots`) como graficador principal de
  Raúl, **`pyod`** (`KNN`, `IForest`, `MCD`) para atípicos multivariados, y `scipy.stats`
  (`ks_2samp`, `chi2_contingency`, `entropy`). Para texto, **`spacy`**. Además,
  `sklearn.impute.IterativeImputer` (requiere `from sklearn.experimental import
  enable_iterative_imputer`) y `sklearn.feature_selection.mutual_info_classif`.
  **Parte de la estadística del módulo 1 se enseña en R**, no en Python: `tidyverse`, `nortest`,
  `coin`, `car`, `lmtest` y `shiny`.
- **Módulo 3 (no supervisado):** además `sklearn.decomposition.PCA`, `sklearn.manifold.TSNE`,
  `umap-learn` (`!pip install umap-learn -q`; `import umap.umap_ as umap`),
  `sklearn.cluster.{KMeans, AgglomerativeClustering, DBSCAN}`, `sklearn.mixture.GaussianMixture`,
  `scipy.cluster.hierarchy.{dendrogram, linkage}`, y las tres métricas de clustering
  (`silhouette_score`, `davies_bouldin_score`, `calinski_harabasz_score`).
  También se usó **Excel** para las prácticas de clustering jerárquico y DBSCAN (se entregaban
  como `.xlsx`).
- **Módulo 4 (redes neuronales / big data):** `tensorflow` / `keras` (API `Sequential`),
  `sklearn.neural_network.MLPClassifier` como contraparte "clásica", `MobileNetV2` preentrenada,
  `ultralytics` (YOLO / YOLO Pose), capas `LSTM` y `GRU`, `Conv2D`/`MaxPooling2D`, `Dropout`,
  `EarlyStopping`, `to_categorical`. Para Big Data: **PySpark**.
- **Módulo 5 (integrador):** libre, pero la interfaz se espera en **Gradio o Streamlit**
  (alternativa: Power BI / Tableau / Looker).

**PySpark local — el instructivo textual del profesor** (Oscar Acosta, anuncio del 6 ago 2026):

```
docker run -p 8888:8888 jupyter/pyspark-notebook
# abrir el navegador en el puerto 8888 → Jupyter Lab
```
(imagen `jupyter/pyspark-notebook`; instalación completa: youtube.com/watch?v=7tDOUrl7Aoc)

---

## 3. Cómo se escribe el código aquí

El estilo que los profesores premian (y que Miguel usó en los trabajos calificados con 98 y 100)
es reconocible:

**a) Un primer bloque de librerías numerado y comentado por secciones.** Este patrón se repite
en prácticas de módulo 3 y 4:

```python
# ============================================================
# PROYECTO FINAL MÓDULO 3
# Segmentación de perfiles de salud con NHANES 2013-2014
# ============================================================

# =========================
# 1. Librerías generales
# =========================
import pandas as pd
import numpy as np

# =========================
# 2. Visualización
# =========================
import matplotlib.pyplot as plt
import seaborn as sns

# ... 3. Preprocesamiento / 4. Reducción de dimensiones / 5. Clustering
#     6. Evaluación de clustering / 7. Clustering jerárquico

# =========================
# 8. Manejo de advertencias
# =========================
import warnings
warnings.filterwarnings("ignore")

# =========================
# 9. Configuración visual
# =========================
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 100)
sns.set_theme(style="whitegrid")

print("Librerías cargadas correctamente.")
```

Variante igual de aceptada (examen final del módulo 3): un import por línea bajo un comentario
corto de categoría — `# Manejo de datos`, `# Visualización`, `# Configuración visual`,
`# Estadística`, `# Preprocesamiento`, `# Reducción de dimensiones`, `# Clustering`,
`# Métricas para evaluación`, `# Distancias`, `# Utilidades`. Lo importante es que el bloque esté
**agrupado y rotulado por función**, no que sea compacto.

**b) Reproducibilidad explícita al inicio.** `np.random.seed(...)` y `tf.random.set_seed(...)` en
el mismo bloque de librerías, y la **misma semilla repetida** en cada `train_test_split`,
`KMeans`, generador, etc. Se usó 42 en las prácticas del módulo 4 y 123 en el examen de CNN: lo
que se evalúa no es el número sino que sea uno solo y esté fijado en todas partes.

**c) Celdas cortas y atómicas.** Una operación por celda, con un `print`/`display` de verificación
inmediatamente después. Ejemplo típico del módulo 4:

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
```
```python
print("Entrenamiento:", X_train.shape)
print("Prueba:", X_test.shape)
```

**d) Argumentos verticales, uno por línea**, en todos los constructores de modelos y en las
llamadas a `classification_report`, `fit`, `KMeans(...)`, etc. No se escriben líneas largas.

**e) Celdas markdown en español que *argumentan* la decisión, no que la anuncian.** El texto
entre celdas no dice "ahora escalamos"; dice por qué:

> "Debido a la presencia de valores faltantes en algunas variables clínicas, particularmente en
> ciertos biomarcadores de laboratorio, se decidió construir el conjunto de modelado utilizando
> únicamente registros completos... Como trabajo futuro, podría evaluarse imputación múltiple..."

> "Se compararon los métodos IQR y Z-Score... Considerando que las variables financieras no
> presentan una distribución normal y que la guía de práctica recomienda explícitamente el
> criterio IQR, este método fue seleccionado como criterio principal."

**f) Comparación tabulada de modelos al final.** Siempre se cierra con un `pd.DataFrame` que
compara modelos y una columna de observación:

```python
resultados = pd.DataFrame({
    "Modelo": ["MLPClassifier (Scikit-learn)", "Keras básico", "Keras + Dropout + EarlyStopping"],
    "Accuracy (%)": [90.17, 88.86, 91.55],
    "Observación": ["Buen desempeño", "Presentó sobreajuste", "Mejor modelo"]
})
```

**g) Módulo 3 exige además un `.py`** con todas las funciones del análisis, documentadas, y el
notebook que lo *consume*. Aviso: en la entrega real de Miguel el `.py` fue solo el export
automático de Colab (`Automatically generated by Colab`), sin funciones ni docstrings — eso
**no** cumple lo pedido ("Entrega de un documento con extensión .py, donde se encontrarán todas
las funciones"; "Todas las funciones deben estar documentadas"). Si se repite un entregable así,
refactorizar de verdad a funciones.

**g-bis) Patrón de deep learning del módulo 4** (del examen de CNN, que sigue al pie la forma que
enseña Oscar Acosta):

- Constantes de configuración en `UPPER_SNAKE` en su propia celda, antes de todo:
  `BASE_PATH`, `TRAIN_PATH`, `MODELS_PATH`, `TARGET_SIZE = (160, 160)`, `BATCH_SIZE = 32`,
  `CLASS_MODE = "raw"`. `MODELS_PATH` apunta a Drive y se crea con `os.makedirs` si no existe.
- **Partición por entidad, no por fila**, para no filtrar información: se separan primero los
  identificadores (`df_houses`), luego se filtran las imágenes por esos ids — y a continuación se
  **verifica explícitamente que la intersección es cero**:
  ```python
  print("Train-Test:", len(set(train["img"]).intersection(set(test["img"]))))
  ```
- El escalador de la variable objetivo se ajusta **solo en train** (`fit_transform`) y se aplica
  con `transform` a test y validación; al predecir se hace `inverse_transform` y, si el dominio lo
  exige, `np.clip(..., a_min=0, a_max=None)`.
- `ImageDataGenerator` con `rescale=1./255` en los tres splits y **augmentación únicamente en
  train** (`rotation_range`, `width/height_shift_range`, `zoom_range`, `horizontal_flip`);
  `shuffle=True, seed=123` en train y `shuffle=False` en validación y test.
- Siempre se grafica una muestra del generador antes de entrenar, y luego `generator.reset()`.
- Arquitectura CNN en bloques crecientes 32→64→128→256, cada bloque
  `Conv2D(padding="same", activation="relu")` + `BatchNormalization` + `MaxPooling2D` +
  `Dropout` con tasa que crece por bloque (0.20 → 0.25 → 0.30 → 0.35), luego `Flatten`,
  densas 128 → 64 y salida (`linear` para regresión, `softmax` para clasificación).
- Compilación con `Adam(learning_rate=0.0005)` y métricas nombradas
  (`RootMeanSquaredError(name="rmse")`, `MeanAbsoluteError(name="mae")`).
- Callbacks siempre: `EarlyStopping(monitor="val_mae", patience=15)` y
  `ModelCheckpoint(..., save_best_only=True, monitor="val_mae")` guardando en Drive; después se
  recarga el mejor modelo con `load_model` para evaluar — nunca se evalúa el modelo de la última
  época.
- Se grafica pérdida y métrica de train vs validación en dos figuras separadas, con etiquetas en
  español ("Entrenamiento" / "Validación", "Época").

**h) Nombres de archivo en minúsculas con guion bajo, sin espacios ni acentos:**
`proyecto_final_nombre_completo.{pdf,ipynb,py,pptx}`,
`practica_1_nombre_completo_minusculas_sin_espacios.pdf`,
`practica_dbscan_nombre_completo_sin_espacios.xlsx`,
y todo empaquetado en `proyecto_final_nombre_completo.zip` (módulo 3).

**i) Sección obligatoria de uso de LLM (módulo 4).** Las tareas del módulo 4 pedían documentar el
uso de IA generativa con tres apartados explícitos: **Prompt utilizado** (transcrito literal),
**Validación del código generado** (qué se ejecutó y qué salió) y **Comparación con los modelos
propios**. La conclusión esperada es crítica: el LLM da una implementación funcional pero fue
necesario detectar sobreajuste y ajustar. (`Tarea_1,_módulo_4.ipynb`)

---

## 3-bis. Código de muestra del profesorado (fuente primaria)

Los notebooks que Oscar Acosta usa en clase están en `C:\Users\laura\Downloads` con prefijo
numérico: `02_ Convolutional Neural Networks (fashion_digits).ipynb`, `03_ CNN (COVID-19).ipynb`,
`04_ Práctica Pokemon.ipynb`, `05_ CNN Object detection.ipynb`, `06_ Data Augmentation.ipynb`.
De Raúl López hay `Tarea1Churn.ipynb` (enunciado + solución del módulo 2) y la presentación
`11_Ensembles (1).pptx`. **Este es el molde real: cuando haya duda sobre cómo estructurar algo,
imitar estos archivos.**

### El esqueleto de notebook de Oscar Acosta

Idéntico en los cinco notebooks. La jerarquía de markdown es fija:

```
# <Título>
## Preparación de ambiente
### Carga de módulos
### Funciones auxiliares
## Data Wrangling
### Carga de datos / ### Rutas / ### Obtención de datos
### EDA            (a veces "### Exploratory Data Analysis")
### Preprocesamiento
    #### Escalado
    #### Preparación de la target
    #### Train-test split
### Generadores
## Modelado
### Arquitectura base / ### Baseline
### Capas convolucionales
### Max Pooling / ### Flatten / ### Capas "ocultas"
### Configuración del entrenamiento
### Callbacks
### Entrenamiento
### Evaluación de resultados / ### Análisis de resultados
### Preservación del modelo
### Mejora no. 1
### Mejora no. 2
## Predicción
```

**Detalles del estilo de Oscar que conviene copiar:**

- Bloque de imports agrupado con comentarios **en inglés**, siempre en el mismo orden:
  `# Misc` · `# Data wrangling` · `# Image manipulation` · `# Data Visualization` ·
  `# Preprocessing` · `# Modeling` · `# Model performance` · `# Environment setup`.
- Cierra el bloque con la configuración de entorno:
  `cf.set_config_file(offline=True, theme="solar")` y `filterwarnings("ignore")`.
- **Usa `cufflinks` sobre plotly, no matplotlib, para las curvas de entrenamiento:**
  `results = pd.DataFrame(history.history)` seguido de `results.iplot()`. La matriz de confusión
  también: `cm.iplot(kind="heatmap", colorscale="blues")`.
- Sección `### Funciones auxiliares` con funciones cortas de una sola responsabilidad definidas
  antes de usarse (`png_to_jpg`, `get_image_size`, `draw_annotation`, `print_data`).
- Constantes de generador en `UPPER_SNAKE` en su propia celda, siempre las mismas tres:
  `TARGET_SIZE`, `BATCH_SIZE`, `CLASS_MODE`.
- `kernel_initializer='he_uniform'` en las capas `Conv2D` y `Dense`; optimizador
  `SGD(learning_rate=0.01, momentum=0.9)` en el notebook base y `Adam(learning_rate=0.001)` en
  los que usan generadores.
- Guarda el modelo en una sección propia al final, `### Preservación del modelo`.
- Cierra con matriz de confusión, `classification_report` y una celda markdown con las **fórmulas
  de las métricas en LaTeX** (recall, precision, accuracy, f1).
- El notebook no presenta una sola arquitectura, sino una **sucesión numerada de versiones**
  bajo encabezados `### Mejora no. 1` y `### Mejora no. 2`. La primera añade
  `BatchNormalization` a la arquitectura base; la segunda añade un segundo bloque convolucional.
  Cada versión se evalúa sobre validación, de modo que el lector ve el efecto de cada cambio.
- El checkpoint incorpora **la métrica al nombre del archivo**
  (`'models/pkmn/model_{val_accuracy:.3f}.h5'`, con `save_best_only=True` y
  `monitor='val_accuracy'`); al terminar se elige el mejor listando el directorio y tomando el
  máximo del nombre. Es un patrón propio de la casa.

**Tres esquemas de partición**, los tres presentes; elegir según el caso:
`flow_from_directory` con `subset='training'` / `'validation'` cuando las clases son carpetas
(Pokemon, COVID); `flow_from_dataframe` con `class_mode='raw'` cuando la etiqueta es numérica;
y copia física de archivos a `train/` y `test/` con `np.random.rand() <= 0.7` cuando hay que
reorganizar el dataset desde cero.

**Detección de objetos sin librería de detección** (`05_`): se plantea como **regresión de la
caja delimitadora**. Las coordenadas se normalizan dividiendo entre el tamaño de la imagen
(`df["xmin"] /= df["width"]`), se pasan las cuatro columnas como target
(`y_col=["xmin","ymin","xmax","ymax"]`, `class_mode="raw"`) y se evalúa con
`RootMeanSquaredError`, `MeanAbsoluteError` y `MeanAbsolutePercentageError`.

**Aumentación de datos** (`06_`, "Hey Waldo"): la lección central es que la aumentación se aplica
**solo a la clase minoritaria y solo en entrenamiento** — a cada imagen de `waldo` se le genera un
volteo y diez rotaciones sobre disco, mientras que `notwaldo` se copia tal cual; el generador de
prueba nunca lleva más que `rescale=1./255`. Además la carpeta se borra y se reconstruye al
inicio (`rmtree` + `makedirs`) para que el notebook sea reejecutable de principio a fin.

### El estilo de Raúl López (módulo 1): funciones que devuelven diagnóstico

Los notebooks de clase de la carpeta `Codigos` (`Valores_Atipicos_Extremos.ipynb`,
`Normalizacion_Escalamiento.ipynb`, `Transformaciones_Entropicas.ipynb`,
`Inge_Variables_TV.ipynb`, `Inge_variables_PH.ipynb`) comparten una filosofía muy marcada:
**cada paso del preprocesamiento se encapsula en una función que además reporta su propio efecto.**
Nunca se transforma sin medir qué se rompió.

- Semilla de la casa en el módulo 1: `np.random.seed(1989)`.
- Comentarios de una línea sin espacio tras la almohadilla (`#General`, `#Graficas`,
  `#Valores atipicos`), y el bloque de imports agrupado por finalidad.
- El diccionario de datos va en una celda markdown **antes de cargar los datos**, con una línea
  por variable, su significado y su rango normal o sus valores válidos.

**La firma del módulo: validar toda imputación con una prueba estadística.** Cada función
`fillna_*` compara la distribución original contra la imputada con un **test de
Kolmogorov-Smirnov de dos muestras** (`ks_2samp`) e imprime estadístico y p-value; y cada una
tiene su gemela `impute_*` que superpone ambas densidades con `sns.kdeplot`. Para un DataFrame
completo, `evaluate_imputation(df_original, df_imputed, vars_num, vars_cat)` devuelve una tabla
con **KS para las numéricas y chi-cuadrada para las categóricas**. La regla implícita: una
imputación es aceptable si no altera significativamente la distribución.

**Utilidades que conviene copiar tal cual:**
- `is_na_df(df)` — tabla de nulos por columna con `n_missing`, `total`, `prop_missing`,
  `prop_original`, filtrada a las columnas con al menos un nulo y con una fila `TOTAL` global.
  Aparece en tres notebooks distintos; es la forma canónica de reportar ausentes.
- `zscore_outliers(df, col, n=3)`, `iqr(df, col)` y `cerca_percent(df, col, 0.01, 0.99)` — las
  tres univariadas, con la misma interfaz: imprimen columna, número y **proporción** de atípicos,
  y devuelven el DataFrame limpio.
- Multivariados con **`pyod`**: `KNN`, `IForest` y `MCD`, en pareja
  `detect_outliers_*` (devuelve los atípicos) / `remove_outliers_*` (devuelve el resto).
  Configuración típica: `IForest(n_estimators=1000, contamination=0.01, random_state=1989)`.
- Imputación multivariada: `impute_mice` con `IterativeImputer` (hay que activar
  `from sklearn.experimental import enable_iterative_imputer`), que codifica temporalmente las
  categóricas a códigos, imputa, redondea y las devuelve a sus etiquetas originales; y
  `impute_rf`, la misma idea con `RandomForestRegressor` como estimador interno.

**Vocabulario a no confundir.** Para Raúl, *"normalización de variables"* **no** es escalar: es
recodificar y colapsar categorías de texto libre. Se hace con funciones `recodificar_*` que
pasan a minúsculas y mapean a categorías limpias (por ejemplo, agrupar los estados de México en
regiones, o el grado de estudios en "Básica o sin" / "Media o media superior" / "Superior").
El escalamiento es un paso aparte y posterior.

**Orden canónico de la codificación**, según el tipo de variable:
- Binarias: `.map({"Sí": 1, "No": 0})` explícito.
- Nominales: `LabelEncoder`.
- **Ordinales: `OrdinalEncoder(categories=[[...]])` con el orden escrito a mano**, nunca
  `LabelEncoder`.
- Después se **eliminan las columnas originales** ya codificadas.
- Se escala solo lo numérico (`MinMaxScaler` es el predeterminado del módulo 1, no
  `StandardScaler`) y se reconstruye con `pd.concat([df_std, df_cat], axis=1)`.
- Al resultado final le llama **TAD** (tabla analítica de datos). Es el entregable del
  preprocesamiento y el punto de partida del modelado.

**Clase `analyze` para el EDA**, con tres métodos y gráficas de plotly:
`plot_num()` dibuja para cada numérica un boxplot y un histograma lado a lado con
`make_subplots(rows=1, cols=2)`; `plot_cat()` dibuja un pastel por categórica con
`textinfo='percent+label'`; `corr_matrix()` un heatmap `Viridis` **solo de las numéricas**
(coherente con la regla de oro de no meter nominales a la correlación).

**"Transformaciones entrópicas"** es como Raúl llama a la selección de variables por teoría de
la información, y es el tema propio del módulo:
- `mutual_information(X, y, problem="classification"|"regression")` envolviendo
  `mutual_info_classif` / `mutual_info_regression`, devolviendo un DataFrame ordenado de mayor a
  menor.
- `woe_iv(df, feature, target, bins=5, discretize=False)` que discretiza con `pd.qcut` si hace
  falta, arma una `pd.crosstab` normalizada por columnas, y calcula
  `WoE = log((%buenos + eps) / (%malos + eps))` e `IV_contrib = (%buenos - %malos) * WoE`, con
  `eps = 0.00001` para evitar la división por cero.
- `IV_df(...)` que recorre todas las variables y devuelve el ranking de Information Value.

**Ingeniería de variables sobre texto** (`Inge_Variables_TV.ipynb`, letras de canciones con
**spaCy**): agrupa por unidad de análisis y calcula, por grupo, densidad léxica, **TTR de lemas**
(lemas únicos / tokens), proporción de stopwords, distribución de POS (`NOUN`, `VERB`, `ADJ`,
`ADV`, `PRON`, `INTJ`), densidad de entidades nombradas, longitud media de palabra y proporción
de pronombres de primera y segunda persona como marcador de estilo narrativo, más variables
estructurales. Es directamente reutilizable para cualquier proyecto de dificultad textual.

**Ingeniería de variables sobre transacciones** (`Inge_variables_PH.ipynb`, caso de retail con
4.1 millones de registros): la unidad muestral pasa de transacción a **cliente**. Se marcan
`es_venta` / `es_devolucion` / `es_cero` según el signo del monto, se agrega por cliente con
`groupby(...).agg(...)` nombrando cada salida (`gasto_neto_total`, `ticket_promedio`,
`ticket_mediano`, `ticket_maximo`, `monto_devuelto`), se define un **cociente de devolución**, y
se añaden agregados de frecuencia, de volumen, temporales y por canal/división. Los atípicos de
monto **no se eliminan**: "usualmente la distribución tiene colas pesadas, por lo que se esperan
montos muy grandes"; se documenta la decisión y se sugiere analizarlos aparte.

### El estilo de Raúl López (módulos 1–2): una clase por familia de modelo

En `Tarea1Churn.ipynb` cada modelo se envuelve en una **clase** con una interfaz fija. Es el
patrón que espera ver en el módulo 2:

```python
class LogisticModel:
    def __init__(self, X_train, X_test, y_train, y_test): ...
    def fit_model(self, **kwargs):   # guarda y_pred_* y proba_* de train y test
    def coefs(self):                 # DataFrame Vars | Coef, incluido el intercepto
    def performance(self):           # DataFrame Metrica | Train | Test
    def plot_roc(self): ...
    def cross_auc(self, cv=4): ...   # media, mediana y desv_est del AUC
```

- Cada método arranca con una guarda:
  `if self.model is None: raise ValueError("Primero ajusta el modelo con fit_model()")`.
- `performance()` devuelve **las cuatro métricas en train y test a la vez**: Accuracy,
  **Sensibilidad**, **Especificidad** y AUC. La especificidad se calcula a mano desde
  `tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()` como `tn / (tn + fp)`.
- Validación cruzada con `make_scorer(roc_auc_score, needs_proba=True)`, `cv=4`, `n_jobs=-1`,
  reportando media, mediana y desviación estándar redondeadas a cuatro decimales.
- Comentarios de una línea en español sobre cada celda: `#Instanciamos`,
  `#Ajustamos y entrenamos`, `#Coeficientes`.
- Librerías propias de este módulo que no aparecen en otros: `plotly.express`,
  `plotly.graph_objects`, `make_subplots`, y **`pyod.models.iforest.IForest`** para detección
  multivariada de valores atípicos.

## 4. Contenido por módulo

### Módulo 1 — Introducción, bases de datos y EDA (Raúl López)
- Tarea 1 en **equipos de 4 o 5 personas** (no individuales), entregable un solo `.pdf`, nombres
  por apellido en orden alfabético.
- Tarea 2: Análisis Exploratorio de los Datos.
- "Base de datos Proyecto": elegir individualmente un dataset y describirlo. Prohibidos los
  datasets vistos en clase (casas, churn, vinos) y además iris de Fisher, diamonds de R, Seoul
  Bike Sharing Demand y SPEI operaciones.
- El documento de selección de base de datos es corto y estructurado en LaTeX:
  1) Nombre, 2) Descripción, 3) Variable objetivo, 4) Enlace.
  (`Base_de_datos_para_el_proyecto_del_módulo_2.pdf`, calificado 100/100)

**Contenido real de la Tarea 1** (`Modulo1_Tarea1.pdf`). Se divide en teoría y práctica, y los
ejercicios prácticos **pueden resolverse en R o en Python**. Regla explícita: en cada ejercicio
práctico hay que **plantear la hipótesis nula, indicar la prueba usada y reportar el p-value**,
con α = 0.05; las preguntas teóricas exigen **referencias** (libros, artículos, sitios).

*Teoría:* definiciones breves de muestra aleatoria, base de datos, base relacional y no
relacional, pipeline, tensor y token/tokenización; tipos de bases no relacionales con pros,
contras y casos de uso; **factorización LU, factorización QR y SVD** y su utilidad en machine
learning; ejemplos de uso de las distribuciones normal, exponencial, gamma, beta, Weibull,
Poisson y binomial; diferencias entre **Data Mart, Data Warehouse y Data Lake**; y conceptos de
Python: qué es un objeto, qué es una clase y sus elementos, y qué es una función lambda frente a
una función normal.

*Práctica*, cinco ejercicios, cada uno con su prueba de hipótesis (los CSV están en la misma
carpeta de Drive):
1. `grupos.csv` — ¿la altura se distribuye normal, en general y por género?, ¿hay diferencias
   entre grupos? (normalidad + comparación de distribuciones)
2. `ingresos.csv` — ¿son independientes el sexo y el rango de ingresos? (tabla de contingencia)
3. `hipertension.csv` — ¿tuvo efecto el tratamiento? **El enunciado da la pista: prueba de
   McNemar** (datos apareados antes/después, binarios).
4. `medias.csv` — ¿difiere la edad promedio entre dos áreas? (diferencia de medias)
5. `winequality-red.csv` — ¿existe correlación lineal entre acidez volátil y acidez fija?

**Material en R del profesor** (`Pruebas_Hipotesis.R`, `Intervalos_Confianza_II.R`,
`distribuciones_discretas.R`, `distribuciones_continuas.R`). Buena parte de la estadística del
módulo 1 se enseña en R, no en Python:
- Carga de paquetes con `pacman::p_load(tidyverse, car, coin, nortest, lmtest)`.
- Criterio impreso en mayúsculas al inicio: **"RECHAZAR H0 SI P-VALUE < ALPHA", ALPHA = 0.05**.
- Árbol de decisión de pruebas que sigue: normalidad con `ad.test` (Anderson-Darling) y
  `cvm.test` (Cramér-von Mises) del paquete `nortest`; igualdad de distribuciones con
  `kruskal_test` del paquete `coin`; independencia en tablas de contingencia con `chisq.test`;
  y diferencia de medias con prueba t **solo después de verificar normalidad y varianza
  constante** — si no se cumplen, alternativa no paramétrica.
- Cada prueba se acompaña de una gráfica `ggplot` con `geom_density` y `theme_bw()`, y la
  conclusión se escribe como comentario en mayúsculas junto a la línea.
- `Intervalos_Confianza_II.R` es una **app de Shiny** que simula la cobertura de intervalos de
  confianza sobre 100 muestras para distribuciones Normal, Poisson y Bernoulli, variando tamaño
  de muestra y nivel de confianza. Es material de demostración en clase, no un entregable.

### Módulo 2 — Aprendizaje supervisado (Raúl López)
Evaluación: **Tareas 70% / Proyecto 30%** (anuncio del 6 abr 2026).

Estructura obligatoria del documento (`Modulo2_Proyecto.pdf`):
1. **Introducción** — definir qué es aprendizaje supervisado y si es clasificación o regresión;
   describir el problema, finalidad, función y flujo de trabajo.
2. **Metodología** — describir los métodos de modelado. **Mínimo 3 modelos distintos vistos en
   clase.** Si se usa reducción de dimensión o ajuste de punto de corte, describirlo igual.
3. **Descripción del conjunto de datos** — dimensiones, diccionario de datos, estadísticas,
   correlaciones, medidas importantes, gráficos.
4. **Procesamiento de datos** — escalado, normalización, partición, ingeniería de variables,
   reducción de dimensión.
5. **Modelado** — hiperparámetros y parámetros obtenidos de cada modelo; métricas **en
   entrenamiento y en prueba** para todos; selección del mejor según la métrica de interés.
6. **Conclusiones** — qué se obtuvo, si fue satisfactorio, trabajo futuro y cómo el modelo
   resuelve el problema del inicio.
7. **Referencias**.

**Plantilla oficial del proyecto** (`Modulo2_Proyecto_plantilla.pdf`, Raúl López, primera entrega
el 12 de marzo de 2026). Requisitos de la base de datos:
- **Más de 5,000 registros y al menos 10 variables.**
- Base libre; **se recomienda Kaggle, UCI o datos abiertos**. Ojo con la diferencia: en el
  **módulo 5 Kaggle está explícitamente prohibido**, así que el criterio cambia según el módulo y
  no se puede reutilizar el mismo dataset sin revisar.
- Se permiten datos del trabajo **con autorización y enmascarando lo sensible**.
- **Prohibido usar los datos vistos en clase o en tareas: diamonds, iris, churn, bicis, vinos,
  casas, spei.**
- La primera entrega es un PDF corto con: nombre de la base, descripción breve, tipo de problema,
  variable objetivo y enlace. (Es exactamente el formato de
  `Base_de_datos_para_el_proyecto_del_módulo_2.pdf`, que sacó 100/100.)

**Enunciado real de la Tarea 1** (`Tarea1Churn.ipynb`, dataset de churn de UCI). Sirve de guion
del módulo entero, porque el proyecto repite estos mismos pasos:
1. Descargar el dataset del enlace de UCI.
2. Verificar valores ausentes; imputarlos o eliminar registros.
3. Análisis exploratorio, en seis incisos: (a) distribución de la variable objetivo, **¿está
   balanceada?**; (b) estadísticas descriptivas de las numéricas, ¿hay atípicos?; (c) análisis de
   las categóricas, considerar normalizarlas; (d) remover atípicos **justificando el porqué**;
   (e) correlaciones entre numéricas — *¿tienen sentido?, ¿hay multicolinealidad?*; (f) identificar
   las variables que más influyen en la objetivo.
4. Codificar las categóricas **según sean ordinales o nominales**.
5. Escalar las numéricas con el escalador que se crea conveniente.
6. Aplicar **mutual information, WoE (Weight of Evidence) e IV (Information Value)** para medir el
   poder predictivo de cada explicativa frente a la objetivo.
7. Modelado, incluida **regresión Ridge** (y Lasso / ElasticNet están importados).

Nota que el inciso 6 es el tema distintivo del módulo y no aparece en ningún otro: WoE e IV vienen
del mundo del scoring crediticio y Raúl los usa como criterio de selección de variables.

**Taxonomía de ensembles de Raúl** (`11_Ensembles (1).pptx`, 19 diapositivas). Es el marco con el
que hay que justificar la elección de modelo en el proyecto:
- **Fundamento:** "la sabiduría de las multitudes"; los ensembles superan el compromiso
  sesgo-varianza (*bias-variance tradeoff*) que limita a los modelos individuales.
- **Dos condiciones necesarias:** *diversidad del ensemble* (los estimadores base deben cometer
  errores distintos, sea usando algoritmos distintos o inyectando aleatoriedad al muestrear datos
  o características) y *agregación del modelo* (voto mayoritario en clasificación, promedio en
  regresión).
- **Ensembles paralelos** — entrenan cada componente de forma independiente, típicamente con
  *strong learners*:
  - *Homogéneos* (mismo tipo de estimador, diversidad por muestreo aleatorio): **Bagging**
    (bootstrap con reemplazo; **su objetivo es reducir la varianza**), **Random Forests** (bagging
    de árboles + subconjunto aleatorio de características en cada división), **Extra Trees**
    (además, umbrales de división al azar).
  - *Heterogéneos* (algoritmos distintos): **voto mayoritario / ponderación** y **stacking**
    (las predicciones de nivel 1 se vuelven *meta-features* de un meta-estimador o *blender*;
    **su objetivo es eliminar el sesgo**).
- **Ensembles secuenciales (boosting)** — cada estimador corrige los errores del anterior,
  típicamente con *weak learners*: **AdaBoost** y LogitBoost (re-ponderan los ejemplos mal
  clasificados) y **Gradient Boosting**, que formula el boosting como descenso de gradiente sobre
  una función de pérdida ajustando los residuales — **XGBoost, CatBoost y LightGBM**.

Si en el proyecto se usa un ensemble, la justificación esperada es de este tipo: bagging para
reducir varianza, stacking para reducir sesgo, boosting cuando se quiere ajustar residuales.

Métodos concretos usados en el proyecto que sacó 98/100 (`Proyecto_módulo_2_.pdf`):
regresión logística como *baseline*, luego **ajuste de umbral con el índice de Youden** aplicado
a logística balanceada (`class_weight`), Random Forest + Youden y XGBoost + Youden; comparación
con curvas ROC, AUC, matrices de confusión, plot de importancia de variables; discusión de
recall como métrica crítica en contexto clínico y de por qué un AUC ~0.62 es insuficiente.
Referencias en APA (James/Witten/Hastie/Tibshirani ISLR, Hosmer & Lemeshow, Breiman, Chen &
Guestrin, Cortes & Vapnik).

### Módulo 3 — No supervisado: reducción de dimensión y clustering (Carla Malerva)
Secuencia de prácticas: 1. Reducción de dimensiones → 2. Clustering jerárquico → 3. DBSCAN →
4. "Ciclo clustering". Más Quiz 1, Quiz 2 y examen.

Requisitos del dataset del proyecto final (`1.1 Proyecto Final, modulo 3.pdf`):
- Datos **reales**, no dummy, **sin tratamiento previo**.
- Mínimo **2,000 registros** y **10 columnas**.
- Variedad de tipos: continuas, discretas y texto.
- **Debe tener missings y valores atípicos** (para poder demostrar el tratamiento).

Entregables (zip `proyecto_final_nombre_completo.zip`): PDF de documentación, notebook, `.py`,
presentación `.pptx`, video de **10–15 min**, carpeta `data` con los csv/xlsx y recursos extra.
Ponderación: **Documentación 40% / Video + presentación 40% / Código 20%**.
Documentación en **LaTeX (deseable) — Overleaf**; "el formato es indispensable".
La presentación debe llevar **poco texto**, explicación **nada técnica**, *storytelling*.

Puntos que la documentación debe cubrir: objetivo del proyecto; desarrollo del módulo I
(limpieza, ingeniería, missings) al menos; y del módulo III: **selección del número de clusters
con métricas, método de clustering, visualización de los grupos en dimensión reducida y
perfilamiento detallado de los grupos**; siguientes pasos y cómo la solución ayuda al negocio y
cómo se activaría.

Flujo canónico del módulo 3, tal como se ejecutó:
1. Carga y unión de fuentes → inspección de nulos (incluidos "nulos disfrazados de ceros").
2. Eliminación de variables de **varianza cero** e identificadores.
3. Ingeniería de variables (agregados: gasto total, campañas aceptadas, hijos totales, edad,
   antigüedad; luego se elimina la fecha de nacimiento original).
4. **Outliers: comparar IQR contra Z-score**, notar la discrepancia y decidir con criterio de
   dominio; en el proyecto se revisó variable por variable el valor máximo y se argumentó su
   plausibilidad clínica antes de conservarlo. La guía de práctica recomienda IQR cuando la
   distribución es asimétrica.
5. Imputación justificada (media si la distribución se mantiene y son pocos datos).
6. Categóricas: colapsar categorías poco frecuentes ("other", unir "alone" con "single") y
   **One-Hot encoding** porque no hay orden.
7. **Escalamiento** (`StandardScaler`).
8. **Reducción de dimensión**: PCA (scree plot, varianza explicada, cargas factoriales) y
   **UMAP** barriendo `n_components` / `n_neighbors`.
9. **Clustering** sobre cada representación: KMeans y GaussianMixture (y jerárquico/DBSCAN en las
   prácticas), barriendo k y registrando **silhouette, Calinski-Harabasz y Davies-Bouldin** en un
   DataFrame comparativo.
10. **Modelo ganador** por silhouette (en el proyecto: KMeans sobre UMAP con n=15).
11. **Perfilamiento**: describir cada cluster con las medias de las variables originales,
    nombrarlo cualitativamente y explicar qué variable fue la más discriminante.
12. Visualización 3D de los clusters en el espacio reducido.

Criterio de Carla sobre outliers, visible en el examen final (Airbnb NY): se distinguen **dos
tipos** de valores extremos y se tratan distinto.
- *Extremos irreales* (20,000,000 o 2,147,483,647 noches máximas = códigos internos o errores de
  captura): se sobreescriben como `NaN` y se imputan con la **mediana** para conservar la
  distribución.
- *Extremos reales* (16 habitaciones, 24 camas, 1000 reseñas): **se conservan**, porque "al
  contrario pueden aportar clusters interesantes".

Y sobre variables con muchos nulos: no se borran automáticamente; se argumenta variable por
variable por qué cada una podría tener peso (p. ej. "los faltantes en `review_scores_*` pueden
sugerir propiedades aún no evaluadas") y solo se eliminan ids, urls y columnas totalmente vacías.

### Módulo 4 — Técnicas cognitivas e Introducción a Big Data (Oscar Acosta)
Temario, reconstruible por los "Microtest" previos a cada clase (cada uno pedía ver un video
antes y contestar): **Redes neuronales convolucionales → Object Detection → Data Augmentation →
Modelado Secuencial → Word Embeddings → RNN → Transfer Learning → Introducción a Big Data**.
La secuencia real de clases, según los notebooks numerados del profesor: **02** CNN sobre
`fashion_mnist` (arquitectura desde cero, mejoras incrementales) → **03** CNN sobre radiografías
de COVID-19 (clasificación binaria con `flow_from_directory`, validación de hardware/GPU) →
**04** Práctica Pokemon (clasificación multiclase; reorganizar un dataset crudo en carpetas por
clase, convertir PNG a JPG, validar que cada fila del CSV tenga imagen) → **05** Object detection
sobre "Where's Waldo" (regresión de caja delimitadora) → **06** Data Augmentation sobre
"Hey Waldo" (clases muy desbalanceadas).

Cuatro prácticas, un Examen 1 y el proyecto. Anuncios de apoyo: mapa de word2vec, datos de
Banxico, herramienta de etiquetado de imágenes, sitio para visualizar activaciones de neuronas.

Requisitos del proyecto (tarea de Classroom, 30 jul 2026):
- Ser un **documento de corte científico con enfoque a negocio**.
- **Incluir lo revisado en los módulos anteriores**.
- Considerar las **arquitecturas vistas en clase**.
- Interpretación de **RESULTADOS**, no lectura de estadígrafos.
- Mostrar claramente **cómo la técnica aplicada resuelve parte o todo el problema**.
- Formato cerrado, **PDF preferentemente**.

El proyecto de Miguel (`Proyecto_final_módulo_4__Redes_neuronales.pdf`, 18 págs., **hecho en
LaTeX**) es el mejor modelo disponible de "documento científico con enfoque a negocio". Su
estructura, que conviene reutilizar:

> Portada UNAM/FES Acatlán con logos → **Resumen** (con los números clave ya en el abstract) →
> Índice → 1. Introducción y motivación (con una **pregunta-hipótesis** explícita) →
> 2. Planteamiento del problema (con la **formalización matemática** de las métricas) →
> 3. Datos y exploración inicial → 4. **Diseño experimental y decisiones metodológicas** →
> 5. Arquitecturas evaluadas → 6. Resultados experimentales → 7. De clasificación a
> priorización: decisión de negocio → 8. Robustez → 9. Interpretación → 10. **Limitaciones**
> (numeradas, honestas) → 11. Trabajo futuro → 12. Conclusiones → **Declaración de alcance**
> ética → Referencias numeradas con DOI.

Rasgos que hacen que ese documento funcione y conviene imitar:
- Un **cuadro de "Decisiones metodológicas"** con tres columnas: Decisión / Razón /
  Evidencia-consecuencia. Incluye decisiones que **fracasaron** (rechazar Delta-GRU por
  sobreajuste, PR-AUC de validación 0.3373) — reportar hipótesis rechazadas suma.
- **Traducir la métrica a negocio**: "revisar 75.14% del video recupera 85.73% de los eventos
  anómalos y evita 24.86% del material → de cada 100 horas de video se revisan 75".
- **Evitar data leakage por diseño**: partición por participante/grupo, `StratifiedGroupKFold`,
  predicciones *out-of-fold*, y decir explícitamente por qué una partición aleatoria habría
  filtrado información.
- Elegir la **métrica correcta bajo desbalance**: con 30% de positivos se reporta accuracy,
  precision, recall, F1, ROC-AUC y **PR-AUC**, y se argumenta que PR-AUC es la principal.
- Reconocer cuando el test dejó de ser independiente porque se usó para diagnosticar.
- Sección de **Limitaciones** larga y específica (tamaño de dataset, etiquetas, privacidad y
  equidad) y una **Declaración de alcance** que impide usos indebidos del modelo.
- Diagramas de flujo y gráficas hechas en LaTeX (TikZ/pgfplots), no capturas de pantalla.

Técnicas concretas del módulo aplicadas ahí: MobileNetV2 congelada como extractor de embeddings
(224×224 → 1280 features, *global average pooling*), YOLO26 para detección de objetos/personas,
YOLO Pose para geometría corporal (ángulos codificados con **seno y coseno** para evitar la
discontinuidad en ±π), GRU vs LSTM para dependencias temporales (GRU preferida por tener menos
parámetros con datasets pequeños), fusión multimodal por concatenación + capas densas con
dropout, y ranking por examen en lugar de umbral global.

Del `Tarea_1,_módulo_4.ipynb` (clasificación de letras 28×28) sale la progresión didáctica del
módulo, que conviene replicar como narrativa: `MLPClassifier` de sklearn → Keras `Sequential`
equivalente → Keras + `Dropout` + `EarlyStopping` → CNN con `Conv2D`/`MaxPooling2D`, comparando
accuracy en cada paso y explicando qué problema resolvió cada adición.

### Módulo 5 — Integrador (Fernando Barranco)
Se aprueba con **mínimo 8.0 (80 puntos)**; máximo 2 faltas; prohibido grabar las clases.
Objetivos: repaso general, desarrollo de un proyecto a lo largo del módulo, soft-skills y
habilidades de negocio, y **uso de IA generativa (GenAI)**.

**Rúbrica, 110 puntos, trabajo individual** (`TrabajoFinal-Rbrica.pdf` y `BienvenidaMdulo5.pdf`):

| Entregable | Puntos |
|---|---|
| Documento | 15 |
| Estrategia | 15 |
| Notebook | 15 |
| Presentación | 10 |
| Interfaz de uso | 10 |
| Video | 20 |
| **Demo en vivo** | **25** |

El énfasis declarado del módulo es la **usabilidad**: "la Ciencia de Datos no solo se trata de
construir modelos efectivos, sino de hacer que esos modelos sean accesibles y valiosos para un
usuario final". El entregable con más puntos es la demo en vivo, no el modelo.

**Documento (15 pts)** — secciones: Introducción/abstract accesible para público general ·
Planteamiento del problema · Estrategia · Descripción de los datos (fuente, calidad, relevancia)
· Análisis exploratorio · Procesamiento de datos con justificación de cada transformación ·
Modelación supervisada y/o no supervisada · Resolución del problema · Conclusiones ·
**Referencias en APA** · Calidad de escritura y presentación visual. Se recomienda **LaTeX**.

**Estrategia (15 pts)** — *accionables* concretos y fundamentados, *descripción de usuarios*
(quiénes son y qué necesitan) y *usabilidad del modelo*.

**Notebook (15 pts)** — organización y secuencia lógica, código limpio y comentado, descripción
de datos y EDA, preparación y limpieza, modelado y evaluación, conclusiones y recomendaciones, y
**reproducibilidad: debe correr desde cualquier Colab sin errores ni warnings**.

**Presentación (10 pts)** — libertad de herramienta (PowerPoint, Slides, Prezi, Canva).

**Interfaz (10 pts)** — explicación paso a paso, demostraciones convincentes; **Gradio, Streamlit
o similar**; alternativa: Tableau, Power BI, Looker.

**Video (20 pts)** — **MP4, máximo 5 minutos**, el alumno **debe aparecer hablando a cámara en
todo momento** con las diapositivas de fondo. Se recomienda **OBS** para la grabación de pantalla.

**Demo en vivo (25 pts)** — última semana de clases, 3–5 min por alumno, cámara abierta, compartir
pantalla, enfocarse en la usabilidad, y sección de Q&A. Si no se presenta en ninguno de los dos
días disponibles (y no se avisa antes al profesor), **se pierden los 25 puntos automáticamente**.
No hay prórrogas.

**Calendario del módulo (6 semanas):**
1. Diseño del proyecto (**crear una compañía ficticia de IA**), nicho de negocio, planteamiento
   del problema, estrategia técnica y de negocio, resolución "en papel", usuario final.
2. Obtención del dataset (APIs, web scraping; **Kaggle baneado**), EDA, visualización, limpieza,
   ingeniería de variables fase 1.
3. Baseline (supervisado / no supervisado / generativo), hiperparametría, modelos secundarios,
   diseño de la UI, ingeniería fase 2.
4. Pipeline, flujo de inferencia, desarrollo de la UI, despliegue local, evaluación general,
   ingeniería fase 3.
5. Despliegue remoto, mejoras a la interfaz, limpieza y documentación de código, redacción del
   documento, elevator pitch, video tutorial.
6. Demostraciones en vivo.

**Documento modelo del profesor** (`Ejemplodocumentofinal.pdf`, 30 págs., "I.A. Restaurantera",
Fernando Barranco, datos de Yelp). Su índice muestra el nivel esperado:
Introducción · Planteamiento del problema · Descripción de los datos · **Ingeniería de datos**
(preprocesamiento de texto: stopwords, lematización, detección de frases; vectorización: CBOW y
Skip-gram) · **Análisis exploratorio** dividido en univariado (ley de Zipf, etiquetado
gramatical, NER), bivariado (similitud de términos, álgebra de palabras) y multivariado (t-SNE) ·
**Modelación no supervisada** (LDA para tópicos, autoencoders para remoción de ruido en
imágenes) · **Modelación supervisada** (análisis de sentimientos, categorización de texto) ·
**Estrategia de negocio** (sistema de recomendación dual) · Conclusiones y siguientes pasos.
Nota el patrón: el EDA se organiza en univariado/bivariado/multivariado, y siempre hay una
sección de estrategia de negocio antes de concluir. Librerías que menciona: `spacy`,
`scikit-learn`, `gensim`, `pandas`, `numpy`.

**Presentación modelo del profesor** (`Ejemplopresentacindehallazgos.pdf`, 40 diapositivas, mismo
proyecto). Su guion es la plantilla a seguir para la presentación y el video:

1. Portada.
2. "Antes de comenzar": contexto del dominio en una frase (¿qué es Yelp?).
3. **Los datos** en cifras grandes: 8,021,122 comentarios · 1,968,703 usuarios · 63,944
   restaurantes · 200,000 fotografías · 17 GB. Números, no párrafos.
4. **Agenda** de tres bloques: (1) Hallazgos relevantes — EDA, limpieza, transformaciones e
   ingeniería de variables; (2) Modelación de datos — resultado de las estrategias supervisada y
   no supervisada; (3) Estrategia de negocio — ejemplo de uso y aplicación bajo enfoque práctico.
5. **Objetivos** numerados (01, 02, 03), cada uno en una frase de negocio.
6. Sección "Hallazgos": cada concepto técnico en su propia diapositiva, con **una definición de
   una línea, un ejemplo concreto y una figura** (ley de Zipf y su versión log-log, POS tagging,
   NER, limpieza de texto con ejemplos antes→después, stopwords/lematización/n-gramas,
   CBOW vs Skip-gram con la tabla de dimensiones del embedding).
7. Resultados de modelado con las métricas desnudas: `Precision = 0.90 · Recall = 0.91 ·
   F1-score = 0.90`, y el nombre de la arquitectura.
8. Sección "Estrategia": el producto explicado por tipo de usuario (para los restaurantes / para
   los clientes).
9. **"Ejemplo de uso y aplicación"**: se toma *un* caso real (un comentario concreto) y se recorre
   el pipeline paso por paso numerado (1. se asocian los comentarios → 2. se predicen los tópicos
   con sus probabilidades → 3. se predice el sentimiento → 4. se repite para todos los comentarios
   → 5. se calcula el scorecard de 0 a 10 por rubro), mostrando la tabla que produce cada paso.
   Este recorrido es lo que convierte un modelo en un entregable de negocio; es el corazón de la
   presentación.
10. Cierre con el entregable concreto (un scorecard) para dos casos distintos.

---

## 5. Plantillas rápidas

**Esqueleto de documento final (LaTeX, módulos 2/4/5):**
```
Portada (UNAM · FES Acatlán · logos · título · alumno · profesor · fecha)
Resumen / Abstract  ← con los números clave
Índice
1. Introducción y motivación (+ pregunta-hipótesis)
2. Planteamiento del problema (+ formalización de las métricas)
3. Descripción de los datos (fuente, tamaño, diccionario, calidad)
4. Análisis exploratorio (univariado / bivariado / multivariado)
5. Procesamiento e ingeniería de datos (cada transformación justificada)
6. Diseño experimental y decisiones metodológicas (cuadro Decisión | Razón | Evidencia)
7. Modelado y resultados (métricas en train y test, comparación tabulada)
8. Estrategia de negocio / resolución del problema (accionables, usuarios)
9. Limitaciones (numeradas)
10. Trabajo futuro
11. Conclusiones
[Declaración de alcance, si el tema lo amerita]
Referencias (APA)
```

**Esqueleto de notebook:**
```
# Título del proyecto (markdown)
1. Bloque de librerías numerado y comentado + seeds + configuración visual
2. Carga de datos (drive.mount) y primer acercamiento (.shape, .info(), .head())
3. Nulos y nulos disfrazados; varianza cero; identificadores
4. Ingeniería de variables
5. Outliers (IQR vs Z-score, decisión argumentada por dominio)
6. Codificación de categóricas y escalamiento
7. EDA con gráficos — cada gráfico seguido de una celda markdown que lo interpreta
8. Modelado: baseline primero, luego incrementos, cada uno con su justificación
9. Tabla comparativa de modelos y elección del ganador
10. Interpretación / perfilamiento / importancia de variables
11. Conclusiones y trabajo futuro
```

---

## 6. Lo que no pude leer

- **El contenido de Google Classroom.** No existe conector; las notificaciones de Gmail (~201
  hilos de `no-reply@classroom.google.com`) solo traen título, texto del anuncio y un enlace.
  Presentaciones y códigos de muestra publicados *dentro* de Classroom no son accesibles desde
  aquí. Códigos de clase conocidos: módulo 5 = `r43d5lwa`.
- **Cómo llegar a las carpetas compartidas de los profesores (truco reutilizable).** El buscador
  de Drive **no indexa los hijos de una carpeta compartida**: fallan `parentId`,
  `title contains` con el nombre exacto, `sharedWithMe = true`, `fullText contains` y
  `owner = '<profesor>'` (este último devuelve solo la carpeta). Pero **acceder por `fileId`
  directo sí funciona aunque el buscador nunca haya visto el archivo**:
  - PDFs y documentos → `read_file_content` con el `fileId`. Funciona a la primera.
  - `.ipynb`, `.R` y demás mime types no soportados → `download_file_content` los baja en base64
    (hay que decodificarlos), y si el conector se cae, la vía más rápida es el navegador:
    abrir `https://drive.google.com/uc?export=download&id=<ID>` con el MCP `chrome-devtools`.
    Devuelve `net::ERR_ABORTED`, que **es lo esperado en una descarga**: el archivo cae igual en
    `C:\Users\laura\Downloads`.
  - Los `fileId` se sacan del DOM de Drive en el navegador, no del conector.
- **De la carpeta `[G34] Módulo 1`** (de `xxxxxx@xxxxxx.com`) quedan sin leer:
  `Modulo1_Tarea2.pdf` (id `1N1sqEfWYItYPU8Tu9iVcLFFufUmOnz5C`), `Modulo1_Examen.pdf`
  (`1DWvzDx4v39P4CI1rV8mrr2YuPnLVD1ks`), `G34_Modulo1_Calif.pdf`
  (`1tmGTAbqaDzu9sgZegl_NqMYEdlqgr7Qt`), los CSV de práctica (`grupos`, `hipertension`,
  `ingresos`, `medias`, `wine_quality`, `winequality-red`), los notebooks `librosa.ipynb` y
  `librosa_extract.ipynb` (audio), `distribuciones_discretas.R` y `distribuciones_continuas.R`,
  y las subcarpetas `Tarea 1. Introducción a la ciencia de datos`,
  `Tare 2. Análisis Exploratorio de los Datos` y `Material_Adicional`, cuyos IDs no se han
  extraído todavía. Todos son alcanzables con el truco de arriba.
- **La carpeta de Drive del módulo 2** (`1UkH40-b7fXvIPkQU-NpNtc6k8eqLhei-...`): no se han
  extraído los `fileId` de su contenido.
- **Los notebooks 01 y 07–10 de Oscar Acosta.** En disco solo están el 02, 03, 04, 05, 06 y la
  presentación 11. Faltan por tanto los de modelado secuencial, word embeddings, RNN, transfer
  learning y Big Data / PySpark, que son justo la segunda mitad del módulo 4.
- **Presentaciones de clase de los módulos 1, 3 y 4.** La única del profesorado localizada es
  `11_Ensembles (1).pptx` de Raúl López (módulo 2), ya destilada arriba.
- **Contenido de los notebooks de módulo 5** guardados en Drive (`proyecto módulo 5`,
  `LiteraLevel_v4_entrenamiento.ipynb`): son de ~1.9 MB con salidas embebidas; el proyecto vivo
  está en el repo local `C:\Users\laura\literalevel` y sus memorias asociadas, que son mejor
  fuente que este documento para ese tema.
- **El notebook del proyecto del módulo 2** (`Proyecto del módulo 2.ipynb`, id
  `1sj4hhh7n0G6fhm7FvBpLihek8Tb3EZV1`, 2.6 MB) y `Untitled0.ipynb` (id
  `1m1lmg-4h6Do-e0YWLyPPdfzYAMFl7yQm`): el conector de Drive rechaza el mime type de Colab en
  `read_file_content` y descargarlos en base64 no cabía en el presupuesto de esta sesión. El
  estilo del módulo 2 se infirió del documento entregado y de los notebooks de los módulos 3 y 4.
- **Retroalimentación individual de los profesores a Miguel.** Solo llegan a Gmail las
  calificaciones (100/100 en "Base de datos Proyecto" del módulo 1; 98/100 en el proyecto final
  del módulo 2, calificado por Raúl López el 27 abr 2026), no los comentarios. Las correcciones
  recogidas en la sección 1 son avisos generales al grupo, no observaciones personales.

## 7. Dónde están los originales

- **Código de muestra del profesorado**, todo en `C:\Users\laura\Downloads\`:
  `02_ Convolutional Neural Networks (fashion_digits).ipynb`, `03_ CNN (COVID-19).ipynb`,
  `04_ Práctica Pokemon.ipynb`, `05_ CNN Object detection.ipynb`, `06_ Data Augmentation.ipynb`
  (Oscar Acosta), `Tarea1Churn.ipynb` y `11_Ensembles (1).pptx` (Raúl López).
- **Notebooks de clase del módulo 1** de Raúl López, descargados de su carpeta de Drive a
  `C:\Users\laura\Downloads\`: `Valores_Atipicos_Extremos.ipynb`,
  `Normalizacion_Escalamiento.ipynb`, `Transformaciones_Entropicas.ipynb`,
  `Inge_Variables_TV.ipynb`, `Inge_variables_PH.ipynb`, `EDA_Calories.ipynb`,
  `EDA_SeriesTiempo.ipynb`, `Tarea3_ML.ipynb`, más `Pruebas_Hipotesis.R` e
  `Intervalos_Confianza_II.R`.
- `C:\Users\laura\Downloads\` — `TrabajoFinal-Rbrica.pdf`, `BienvenidaMdulo5.pdf`,
  `Ejemplodocumentofinal.pdf`, `Ejemplopresentacindehallazgos.pdf`,
  `1.1 Proyecto Final, modulo 3.pdf`, `Tarea_1,_módulo_4.ipynb`,
  `CNN_Examen_1_módulo4_miguel_reyes_carrillo.ipynb`, `examen_final_modulo_3_*.{ipynb,pdf}`,
  `proyecto_final_miguel_reyes_carrillo.{ipynb,py,pptx}`, `practica_4_miguel_reyes_carrillo.ipynb`,
  `Hands-OnMachineLearningwithScikit-LearnKerasandTensorflow3rdEdition.pdf`.
- `C:\Users\laura\OneDrive\Escritorio\Libros para el diplomado de ciencia de datos\` —
  `Modulo2_Proyecto.pdf` (instrucciones), `Proyecto_módulo_2_.pdf` (entrega, 98/100),
  `Base_de_datos_para_el_proyecto_del_módulo_2.pdf` (100/100), `Durrett.pdf`, `LuisRincon.pdf`,
  `Módulo 3\` (datos NHANES + entrega), `Módulo 4\Proyecto\` (PDF LaTeX + notebook).
- Google Drive de `xxxxxx@xxxxxx.com` — `Tareas del diplomado/Módulo 2/` (notebook del proyecto
  del módulo 2, id `1sj4hhh7n0G6fhm7FvBpLihek8Tb3EZV1`) y `Colab Notebooks/` (módulo 5).
