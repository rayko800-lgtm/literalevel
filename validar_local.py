"""Verifica que el pipeline local reproduce la validacion externa de Colab.

Uso:  python -X utf8 validar_local.py [carpeta_con_los_pdf]
El modelo se busca en ./modelo_v4 o en LITERALEVEL_MODELO; el corpus en
el argumento, en LITERALEVEL_CORPUS o en ~/Downloads.

Usa los PDFs de British Council de Downloads, con el nivel en el nombre.
Replica el anclaje de ll_paso_30.py ("Reading text" .. "Tasks") para quedarse
solo con el cuerpo del articulo.

British Council es material con derechos: se imprimen puntuaciones, nunca texto.
"""
import glob, os, re, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "app")
import numpy as np
from pypdf import PdfReader
from scoring import Puntuador, continuous_prose, words

RE_INI = re.compile(r"reading text", re.I)
RE_FIN = re.compile(r"^\s*(tasks|task 1)\s*$", re.I)
RUIDO = re.compile(r"(learnenglish|britishcouncil|british council|©|copyright"
                   r"|all rights|www\.|http|page \d+)", re.I)
# Nada de \b: en el nombre el nivel puede ir pegado a un guion bajo
# (B2__LearnEnglish-Reading-B2_Work-life-balance.pdf) y \b NO corta entre
# "2" y "_", porque el guion bajo es caracter de palabra. Ese archivo se caia
# de la validacion sin que nadie lo notara: la muestra eran 45 textos en vez
# de 46. Se mira letra o digito a los lados, no "caracter de palabra".
RE_NIVEL = re.compile(r"(?<![A-Za-z0-9])(A1|A2|B1|B2|C1|C2)(?![A-Za-z0-9])")


def cuerpo(lineas):
    ini = next((k + 1 for k, l in enumerate(lineas) if RE_INI.search(l)), None)
    if ini is None:
        return None
    fin = next((k for k in range(ini, len(lineas)) if RE_FIN.match(lineas[k])), len(lineas))
    utiles = [l.strip() for l in lineas[ini:fin]
              if l.strip() and not RUIDO.search(l) and not l.strip().isdigit()
              and len(l.strip()) >= 3]
    # OJO, que esto no es un detalle. `continuous_prose` tiene cuatro reglas y
    # UNA de ellas -la del maquetado de lista- mira `splitlines()`: salta si hay
    # dos vinetas seguidas o si mas de un tercio de las lineas tienen cuatro
    # palabras o menos. Uniendo con espacio esa regla no se dispara nunca, asi que este validador filtra MAS FLOJO que la app -que
    # si recibe saltos de parrafo, porque reader._limpiar_html los restaura-.
    #
    # Medido cambiando el espacio por salto de linea:
    #     con espacio  47 textos, cinco niveles, medias crecientes
    #     con salto    31 textos, A1 se queda en 1 y la validacion FALLA
    #
    # Se conserva el espacio porque es lo que reproduce el Cuadro 10 del
    # documento -la reproduccion local- y porque cambiarlo dejaria el resultado
    # sin A1. NO reproduce las cifras de Colab: aquella tanda son 38 textos y
    # A2 se desvia 0,10. Nada de aqui las reproduce. Pero no se esconde la otra cifra: `cuerpo_estricto`
    # rehace el recuento con el filtro completo y el guion lo imprime.
    return " ".join(utiles) or None


def cuerpo_estricto(lineas):
    """El mismo cuerpo, pero conservando los saltos de linea del PDF.

    Sirve para contar cuantos textos pasarian el filtro que aplica la
    aplicacion de verdad. No se usa para puntuar: solo para informar.
    """
    ini = next((k + 1 for k, l in enumerate(lineas) if RE_INI.search(l)), None)
    if ini is None:
        return None
    fin = next((k for k in range(ini, len(lineas)) if RE_FIN.match(lineas[k])), len(lineas))
    utiles = [l.strip() for l in lineas[ini:fin]
              if l.strip() and not RUIDO.search(l) and not l.strip().isdigit()
              and len(l.strip()) >= 3]
    return "\n".join(utiles) or None


# Sin rutas clavadas a una maquina concreta: el profesor clona el repo y
# tiene que poder ejecutarlo. Se admiten variables de entorno y argumentos.
RUTA_MODELO = os.environ.get("LITERALEVEL_MODELO",
                             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "modelo_v4"))
CORPUS = (sys.argv[1] if len(sys.argv) > 1
          else os.environ.get("LITERALEVEL_CORPUS",
                              os.path.join(os.path.expanduser("~"), "Downloads")))
if not os.path.isdir(RUTA_MODELO):
    sys.exit(f"No encuentro el modelo en {RUTA_MODELO}. "
             "Ponlo en ./modelo_v4 o define LITERALEVEL_MODELO.")
p = Puntuador(RUTA_MODELO)
print("modelo v4 cargado\n")

por_nivel = {}
pasan_estricto = 0   # cuantos pasarian el filtro completo de la app
filas = []          # (nivel, puntuacion, palabras) por texto
saltados = 0
fallidos = []
# El "?" del patron no es un descuido. Uno de los 59 archivos se llama
# LearnEnglish_Reading con guion BAJO, y con "*LearnEnglish-Reading*.pdf" se
# caia del corpus sin que nadie lo notara: por eso el documento hablaba de "uno
# no disponible" que en realidad estaba en el disco desde el principio. Es el
# tercer fallo del mismo tipo en un dia -antes fueron un \b que no cortaba en
# el guion bajo y una cifra buscada solo en su forma sin redondear-: un patron
# que contempla una sola manera de escribir lo mismo.
PATRON = "*LearnEnglish?Reading*.pdf"
for ruta in sorted(glob.glob(os.path.join(CORPUS, PATRON))):
    m = RE_NIVEL.search(os.path.basename(ruta))
    if not m:
        continue
    nivel = m.group(1)
    try:
        lineas = []
        for pg in PdfReader(ruta).pages:
            lineas.extend((pg.extract_text() or "").split("\n"))
        texto = cuerpo(lineas)
        estricto = cuerpo_estricto(lineas)
        if estricto and continuous_prose(estricto)[0]:
            pasan_estricto += 1
        if not texto:
            saltados += 1
            continue
        r = p.puntuar(texto)
    except Exception as e:
        # Se contaban juntos "no encontre el cuerpo del texto" y "la
        # puntuacion fallo", bajo el rotulo de lo primero. Son cosas
        # distintas: la primera es un PDF con otra maquetacion, la segunda
        # puede ser un fallo del modelo. Ahora se cuentan aparte y se dice
        # que excepcion fue.
        fallidos.append(f"{os.path.basename(ruta)}: {type(e).__name__}: {e}")
        continue
    por_nivel.setdefault(nivel, []).append(r.puntuacion)
    # Para el baseline del Cuadro 12 hace falta ademas la longitud.
    filas.append((nivel, float(r.puntuacion), len(words(texto))))

# np.std es la desviacion POBLACIONAL (ddof=0). Con n de 3 a 12 la muestral
# saldria mayor; se deja la poblacional porque es la que reporto el Colab y
# lo que aqui se compara son las medias, no la dispersion.
print(f"{'nivel':<6}{'n':>4}{'media 0-2':>12}{'desv (pobl.)':>14}   (Colab reportó)")
esperado = {"A2": 0.6479, "B1": 0.9513, "B2": 1.2883, "C1": 1.4950}
for niv in sorted(por_nivel):
    v = por_nivel[niv]
    e = esperado.get(niv)
    print(f"{niv:<6}{len(v):>4}{np.mean(v):>12.4f}{np.std(v):>14.3f}   "
          f"{('%.4f' % e) if e else '—'}")
print(f"\ntextos sin cuerpo localizable: {saltados}")
print(f"textos que pasarian el filtro COMPLETO (con saltos de linea): "
      f"{pasan_estricto}  <- el que aplica la app; aqui se puntuan mas")
print(f"textos que fallaron al puntuar: {len(fallidos)}")
for f in fallidos:
    print("   ", f)

# --- Cuadro 12 del documento: el modelo frente a la senal trivial -----------------------
# Esto lo publicaba el documento sin que ningun guion lo calculase. Se calcula
# aqui, sobre los mismos textos que acaban de puntuarse, para que la cifra sea
# reproducible y no una herencia de una sesion de Colab que ya no existe.
#
# Spearman = Pearson sobre los rangos. Sin scipy, que no esta en requirements.
ORDINAL = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


def _rangos(v):
    """Rangos con promedio en los empates, como scipy.stats.rankdata."""
    orden = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and v[orden[j + 1]] == v[orden[i]]:
            j += 1
        medio = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[orden[k]] = medio
        i = j + 1
    return np.array(r)


def _pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    da, db = a - a.mean(), b - b.mean()
    den = float(np.sqrt((da ** 2).sum() * (db ** 2).sum()))
    return float("nan") if den == 0 else float((da * db).sum() / den)


def _spearman(a, b):
    return _pearson(_rangos(list(a)), _rangos(list(b)))


if len(filas) >= 3:
    niv = [ORDINAL[f[0]] for f in filas]
    mod = [f[1] for f in filas]
    pal = [f[2] for f in filas]

    s_mod = _spearman(mod, niv)
    s_pal = _spearman(pal, niv)
    s_mp = _spearman(mod, pal)

    # Correlacion parcial sobre rangos: que le queda al modelo cuando se
    # descuenta la longitud. La misma formula para el contador de palabras
    # daria 0/0, porque descontar la longitud de la longitud deja varianza
    # cero: no es que salga peor, es que no esta definida.
    den = (1 - s_mp ** 2) * (1 - s_pal ** 2)
    parcial = (s_mod - s_mp * s_pal) / np.sqrt(den) if den > 0 else float("nan")

    print()
    print("Cuadro 12 - el modelo frente a la senal trivial "
          f"({len(filas)} textos)")
    print(f"  modelo v4                                  {s_mod:.3f}")
    print(f"  contar palabras, sin modelo                {s_pal:.3f}")
    print(f"  modelo descontando la longitud (parcial)   {parcial:.3f}")
    print(f"  (de paso: modelo contra longitud           {s_mp:.3f})")
    print("  contar palabras descontando la longitud:   indefinida")

# --- El validador tiene que poder SUSPENDER -------------------------------
# Antes esto era `all(a < b for a, b in zip(medias, medias[1:]))` a secas, y
# `all()` de una lista vacia es True. O sea que sin un solo PDF encontrado
# -carpeta equivocada, nombres distintos- el guion imprimia "orden
# estrictamente creciente: True" y quedaba tan ancho. Lo mismo con un solo
# nivel. Una validacion que aprueba sin evaluar nada no es una validacion.
# Lo encontro una auditoria externa.
NIVELES_ESPERADOS = ("A1", "A2", "B1", "B2", "C1")
MINIMO_POR_NIVEL = 2

problemas = []
faltan = [n for n in NIVELES_ESPERADOS if n not in por_nivel]
if faltan:
    problemas.append(f"no se evaluo ningun texto de: {', '.join(faltan)}")
for niv, v in sorted(por_nivel.items()):
    if len(v) < MINIMO_POR_NIVEL:
        problemas.append(f"{niv} solo tiene {len(v)} texto(s), hacen falta {MINIMO_POR_NIVEL}")

medias = [np.mean(por_nivel[n]) for n in sorted(por_nivel)]
creciente = len(medias) >= 2 and all(a < b for a, b in zip(medias, medias[1:]))
if not creciente:
    problemas.append("las medias por nivel NO son estrictamente crecientes")

print()
if problemas:
    print("VALIDACION FALLIDA:")
    for x in problemas:
        print("  -", x)
else:
    print(f"VALIDACION CORRECTA: {sum(len(v) for v in por_nivel.values())} textos, "
          f"{len(por_nivel)} niveles, medias estrictamente crecientes.")

print("\n(no se imprime ni un fragmento: material con derechos)")
sys.exit(1 if problemas else 0)
