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
from scoring import Puntuador, continuous_prose

RE_INI = re.compile(r"reading text", re.I)
RE_FIN = re.compile(r"^\s*(tasks|task 1)\s*$", re.I)
RUIDO = re.compile(r"(learnenglish|britishcouncil|british council|©|copyright"
                   r"|all rights|www\.|http|page \d+)", re.I)
RE_NIVEL = re.compile(r"\b(A1|A2|B1|B2|C1|C2)\b")


def cuerpo(lineas):
    ini = next((k + 1 for k, l in enumerate(lineas) if RE_INI.search(l)), None)
    if ini is None:
        return None
    fin = next((k for k in range(ini, len(lineas)) if RE_FIN.match(lineas[k])), len(lineas))
    utiles = [l.strip() for l in lineas[ini:fin]
              if l.strip() and not RUIDO.search(l) and not l.strip().isdigit()
              and len(l.strip()) >= 3]
    return " ".join(utiles) or None


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
saltados = 0
fallidos = []
for ruta in sorted(glob.glob(os.path.join(CORPUS, "*LearnEnglish-Reading*.pdf"))):
    m = RE_NIVEL.search(os.path.basename(ruta))
    if not m:
        continue
    nivel = m.group(1)
    try:
        lineas = []
        for pg in PdfReader(ruta).pages:
            lineas.extend((pg.extract_text() or "").split("\n"))
        texto = cuerpo(lineas)
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

print(f"{'nivel':<6}{'n':>4}{'media 0-2':>12}{'desv':>8}   (Colab reportó)")
esperado = {"A2": 0.6479, "B1": 0.9513, "B2": 1.2883, "C1": 1.4950}
for niv in sorted(por_nivel):
    v = por_nivel[niv]
    e = esperado.get(niv)
    print(f"{niv:<6}{len(v):>4}{np.mean(v):>12.4f}{np.std(v):>8.3f}   "
          f"{('%.4f' % e) if e else '—'}")
print(f"\ntextos sin cuerpo localizable: {saltados}")
print(f"textos que fallaron al puntuar: {len(fallidos)}")
for f in fallidos[:5]:
    print("   ", f)

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
