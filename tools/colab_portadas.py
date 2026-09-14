# %% [markdown]
# # Portadas generadas por IA para el catálogo de LiteraLevel
#
# **Nada se lanza solo.** Este cuaderno tiene dos celdas que gastan GPU:
#
# 1. **«Medir 20»**: genera 20 portadas en local, imprime segundos por imagen y
#    KB por webp, y NO sube nada. Sirve para cambiar las estimaciones del estudio
#    del 13 de septiembre de 2026 por cifras reales.
# 2. **«Tanda»**: solo arranca si `SALDO_CONFIRMADO` (unidades de Colab que
#    Miguel ha mirado en el panel Recursos) cubre la estimación con margen.
#
# Reglas que no se negocian:
#
# - Modelo **FLUX.1-schnell** (Apache 2.0), 4 pasos, 768×1152, en **A100**.
# - El prompt sale de **temas + década del autor + gancho**. **Nunca** lleva
#   título, autor, nombres de artistas ni de portadas reales, y pide **sin
#   texto y sin caras**: nada de letras inventadas, parecidos ni estereotipos.
# - Cada portada va con su JSON: paleta de 5 colores, `color_texto` por
#   contraste WCAG y `acento`. La marca «Portada generada por IA, no oficial»
#   la pone el front encima: no va dentro de la imagen.
# - Reanudable: shards de 250, se retoma leyendo qué ids ya tienen JSON en el
#   bucket, y la semilla es un hash del id (regenerar da la misma portada).
#
# Las celdas marcadas `[puro]` no tocan GPU ni red: las prueba
# `pruebas_portadas.py` en local, que además comprueba que las reglas de
# exclusión son las mismas que las de `app/catalogo.py`.

# %% [puro]
# --- 1. Reglas y funciones puras (probadas en local) --------------------------
import hashlib
import json
import re

MODELO = "black-forest-labs/FLUX.1-schnell"
ANCHO, ALTO = 768, 1152            # multiplos de 16, como pide FLUX
PASOS = 4
MINIATURA = 256                    # lado mayor de la miniatura
CALIDAD_WEBP = 80
SHARD = 250
AVISO_IA = "Portada generada por IA, no oficial"

# Copiadas de app/catalogo.py. pruebas_portadas.py falla si divergen.
NO_ES_LECTURA_TEMAS = (
    r"(?i)\bindexes\b|\bcatalogs\b|bibliograph|\bdirectories\b|gazetteers|almanacs")
NO_ES_LECTURA_TITULO = (
    r"(?i)index of the project gutenberg|project gutenberg (?:works|index|catalog)"
    r"|linked index|index for works of|\ban index to all\b|hyperlinks to all chapters"
    r"|world factbook|^list of |\bdirectory\b|\bconstants\b")
LITERARIO = (
    r"(?i)fiction|\btales?\b|stories|\breaders\b|juvenile|poetry|poems|drama|\bplays\b"
    r"|fables|legends|folklore|fairy|nursery rhymes|literature|novels?\b|romance")

# Las 30 raices de tema mas frecuentes entre los 1.200 libros literarios mas
# descargados del catalogo medido (contadas el 13 sep 2026; entre parentesis,
# cuantos libros la llevan). Motivos visuales SIN personas reconocibles.
MOTIVOS = {
    "Science fiction": "a sleek spacecraft over an alien horizon, distant planets, starlight",  # 86
    "England": "rolling green English countryside, stone cottages, low grey sky",  # 82
    "Short stories": "an open lantern-lit doorway onto a winding path, many small lit windows",  # 63
    "Psychological fiction": "a dim room with a tilted mirror, long shadows, a single chair",  # 61
    "Adventure stories": "a rope bridge over a misty jungle gorge, a weathered compass",  # 60
    "Historical fiction": "a cobbled old town square at dusk, horse carriage, gas lamps",  # 55
    "Love stories": "two teacups on a windowsill, spring blossoms, soft morning light",  # 54
    "Domestic fiction": "a warm parlour with a fireplace, embroidery hoop, lace curtains",  # 51
    "Fairy tales": "an enchanted forest clearing, glowing mushrooms, a small stone tower",  # 46
    "Fantasy fiction": "a floating castle among clouds, luminous runes, a winding stair",  # 41
    "Humorous stories": "a toppled stack of hats and umbrellas, a mischievous cat, bright colours",  # 40
    "Folklore": "a village well under a full moon, carved wooden masks, woven baskets",  # 39
    "London (England)": "foggy Victorian London street, gaslight, the silhouette of a clock tower",  # 38
    "Bildungsromans": "a young sapling growing through an old stone wall, a road to the horizon",  # 36
    "Young women": "a writing desk with sealed envelopes and a quill by a tall window, a bonnet on a hook",  # 34
    "Orphans": "an empty swing in a bare autumn garden, a single lit window far away",  # 33
    "Detective and mystery stories": "a magnifying glass over footprints on a rainy pavement, lamplight",  # 30
    "English poetry": "a quill and ink beside wildflowers and a closed leather notebook, dawn light",  # 28
    "Horror tales": "a gothic mansion on a hill under a stormy sky, bare twisted trees",  # 26
    "France": "Parisian rooftops and chimneys at twilight, a wrought-iron balcony",  # 26
    "British": "a red postbox and a stone bridge over a quiet river, drizzle",  # 26
    "Didactic fiction": "a slate board, an apple and neatly stacked schoolbooks, calm light",  # 26
    "Great Britain": "white cliffs above a grey sea, a lighthouse, gulls",  # 26
    "Classical literature": "marble columns and an olive tree, a laurel wreath on a stone step",  # 25
    "Fantasy literature": "a door standing alone in a meadow opening onto a starry night",  # 25
    "Inheritance and succession": "a locked antique chest, a wax-sealed will, a portrait frame with no face",  # 25
    "Russia": "onion domes under snowfall, a troika track across a white plain",  # 24
    "Tragedies (Drama)": "an empty theatre stage, a fallen crown, a single spotlight",  # 24
    "Tales": "a storyteller's hearth with dancing sparks, a carved wooden chest",  # 24
    "Young men": "a travelling trunk on a railway platform, steam, an open road beyond",  # 23
}
MOTIVO_POR_DEFECTO = "an atmospheric still life of old books, a candle and a window at dusk"

ESTILO = ("book cover illustration, painterly, evocative, rich but harmonious colours, "
          "strong composition with calm space at the top")
PROHIBIDO = ("no text, no letters, no words, no title, no logos, no watermark, "
             "no people, no faces, no human figures")


def decada(autor: str) -> str | None:
    """Decada de actividad aproximada a partir de «Apellido, Nombre, 1812-1870».

    Nacimiento + 35 anos, redondeado a la decada. Sin fechas, None: mejor sin
    epoca que con una inventada."""
    m = re.search(r"(\d{3,4})\??\s*-\s*(\d{3,4})?", str(autor or ""))
    if not m:
        return None
    nacido = int(m.group(1))
    if nacido < 1000 or nacido > 2000:
        return None
    return f"{(nacido + 35) // 10 * 10}s"


def raices(temas: str) -> list[str]:
    """Raices de tema de Gutenberg, sin repetir y en orden: «England -- Fiction» -> «England»."""
    vistas, fuera = set(), []
    for t in str(temas or "").split(";"):
        r = t.strip().split(" -- ")[0].strip()
        if r and r not in vistas:
            vistas.add(r)
            fuera.append(r)
    return fuera


def motivos_de(temas: str, maximo: int = 2) -> list[str]:
    """Hasta `maximo` motivos visuales para los temas del libro, en su orden."""
    encontrados = [MOTIVOS[r] for r in raices(temas) if r in MOTIVOS]
    return encontrados[:maximo] or [MOTIVO_POR_DEFECTO]


def _sin_nombres(texto: str, quitar: list[str]) -> str:
    """Quita del gancho palabras del titulo, del autor y cualquier Mayuscula
    que no empiece frase: sin nombres propios en el prompt."""
    fuera = str(texto or "")
    for q in quitar:
        for palabra in re.findall(r"[A-Za-z]{3,}", str(q or "")):
            fuera = re.sub(rf"(?i)\b{re.escape(palabra)}\b", " ", fuera)
    fuera = re.sub(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]+\b", " ", fuera)
    return re.sub(r"\s+", " ", fuera).strip()


def construir_prompt(fila: dict) -> str:
    """El prompt de una portada. Nunca contiene titulo ni autor."""
    partes = [ESTILO]
    partes.extend(motivos_de(fila.get("temas", "")))
    epoca = decada(fila.get("author", ""))
    if epoca:
        partes.append(f"period details of the {epoca}")
    gancho = _sin_nombres(fila.get("hook", ""), [fila.get("title", ""), fila.get("author", "")])
    if gancho:
        partes.append("mood: " + " ".join(gancho.split()[:18]))
    partes.append(PROHIBIDO)
    return ", ".join(partes)


def semilla(id_libro: str) -> int:
    """Semilla determinista por id: regenerar da la misma portada."""
    return int(hashlib.sha256(str(id_libro).upper().encode()).hexdigest()[:8], 16)


def _lum(hex_color: str) -> float:
    """Luminancia relativa WCAG 2.x."""
    h = hex_color.lstrip("#")
    canales = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def _hex(rgb) -> str:
    return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, int(round(c)))) for c in rgb[:3]])


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def oscurecer(hex_color: str, factor: float) -> str:
    return _hex([c * factor for c in _rgb(hex_color)])


def aclarar(hex_color: str, paso: float) -> str:
    return _hex([c + (255 - c) * paso for c in _rgb(hex_color)])


def paleta_de(imagen, n: int = 5) -> list[dict]:
    """Los n colores dominantes (median cut sobre la imagen reducida), del mas
    al menos presente, con su proporcion de pixeles."""
    from PIL import Image
    peq = imagen.convert("RGB").resize((64, 96))
    q = peq.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    crudo = q.getpalette()[: n * 3]
    cuentas = sorted(q.getcolors() or [], reverse=True)
    total = sum(c for c, _ in cuentas) or 1
    return [{"hex": _hex(crudo[i * 3:i * 3 + 3]), "proporcion": round(c / total, 3)}
            for c, i in cuentas][:n]


def _saturacion(hex_color: str) -> float:
    r, g, b = [c / 255 for c in _rgb(hex_color)]
    mx, mn = max(r, g, b), min(r, g, b)
    return 0.0 if mx == 0 else (mx - mn) / mx


def colores_de_lectura(paleta: list[dict]) -> dict:
    """color_texto sobre el dominante (WCAG >= 4,5), fondo del lector y acento.

    - color_texto: blanco o casi negro, el que mas contraste dé sobre el dominante.
    - fondo_lector: el dominante oscurecido hasta que el texto claro del lector
      (#F2F2F2) tenga >= 7:1 (AAA para lectura larga).
    - acento: el color mas saturado de la paleta, aclarado hasta >= 4,5:1 sobre
      ese fondo (enlaces y subrayados)."""
    dominante = paleta[0]["hex"]
    blanco, negro = "#FFFFFF", "#111111"
    color_texto = blanco if contraste(blanco, dominante) >= contraste(negro, dominante) else negro
    fondo = dominante
    for _ in range(40):
        if contraste("#F2F2F2", fondo) >= 7.0:
            break
        fondo = oscurecer(fondo, 0.9)
    base = max((p["hex"] for p in paleta), key=_saturacion)
    acento = base
    for _ in range(40):
        if contraste(acento, fondo) >= 4.5:
            break
        acento = aclarar(acento, 0.12)
    return {"color_texto": color_texto, "contraste_texto": contraste(color_texto, dominante),
            "fondo_lector": fondo, "acento": acento, "contraste_acento": contraste(acento, fondo)}


def json_de_portada(fila: dict, prompt: str, paleta: list[dict], kb_webp: float,
                    kb_mini: float, segundos: float) -> dict:
    """El contrato por libro que leera el front (portada + tintado del lector)."""
    return {
        "id": str(fila["id"]).upper(),
        "modelo": MODELO, "pasos": PASOS, "tam": [ANCHO, ALTO],
        "semilla": semilla(fila["id"]),
        "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()[:16],
        "paleta": paleta,
        **colores_de_lectura(paleta),
        "archivos": {"portada": f"{str(fila['id']).upper()}.webp",
                     "miniatura": f"{str(fila['id']).upper()}_256.webp"},
        "kb": {"portada": round(kb_webp, 1), "miniatura": round(kb_mini, 1)},
        "segundos": round(segundos, 2),
        "generada_por_ia": True, "aviso": AVISO_IA,
    }


def seleccionar(df, conjunto: str = "top_medido", n: int = 1200, ids_curado=None):
    """Que libros llevan portada.

    - top_medido: los n libros LITERARIOS mas descargados del catalogo medido,
      sin indices ni catalogos (mismas reglas que la recomendacion por nivel).
    - curado: los ids de catalogo_recomendaciones.csv que estan en el medido.
    """
    t = df["title"].fillna("").astype(str)
    s = df["temas"].fillna("").astype(str)
    fuera = t.str.contains(NO_ES_LECTURA_TITULO) | s.str.contains(NO_ES_LECTURA_TEMAS)
    literario = s.str.contains(LITERARIO)
    d = df[~fuera & literario].copy()
    if conjunto == "curado":
        d = d[d["id"].astype(str).isin(set(map(str, ids_curado or [])))]
    d["_desc"] = d["downloads"].astype(float)
    return d.sort_values(["_desc", "id"], ascending=[False, True]).head(n).drop(columns="_desc")


def shard_de(i: int) -> str:
    return f"shard_{i // SHARD:03d}"


# %%
# --- 2. Instalar (Colab) -----------------------------------------------------
# !pip -q install "diffusers>=0.31" "transformers>=4.44" accelerate sentencepiece "huggingface_hub>=1.30" pillow pandas

# %%
# --- 3. Configuracion, token y saldo -------------------------------------------
import os
import time
from pathlib import Path

BUCKET = "MikeMaki1763/literalevel-datos"     # el Storage Bucket que monta el Space en /data
PREFIJO = "portadas"                           # /data/portadas/shard_NNN/...
REPO_SPACE = "MikeMaki1763/literalevel"
CONJUNTO = "top_medido"                        # o "curado"
N_LIBROS = 1200
LOCAL = Path("/content/portadas")
LOCAL.mkdir(parents=True, exist_ok=True)

# Unidades que Miguel ha mirado en Recursos. None = la tanda NO arranca.
SALDO_CONFIRMADO = None
UNIDADES_POR_HORA_A100 = 15.0                  # medido en Colab: ~15 u/h
SOBRECARGA = 1.3                               # webp + paleta + subida sobre la GPU

try:
    from google.colab import userdata
    HF_TOKEN = userdata.get("HF_TOKEN")
except Exception:
    HF_TOKEN = os.environ.get("HF_TOKEN", "")
if not HF_TOKEN:
    raise SystemExit("Falta el secreto HF_TOKEN (candado de la barra izquierda) con permiso de escritura.")

import torch
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NINGUNA")
if not torch.cuda.is_available() or "A100" not in torch.cuda.get_device_name(0):
    print("AVISO: el estudio de coste es para A100. Con otra tarjeta, mide antes de nada.")

# %%
# --- 4. Catalogo y seleccion -----------------------------------------------------
import pandas as pd
from huggingface_hub import HfApi, hf_hub_download

api = HfApi(token=HF_TOKEN)
csv_medido = hf_hub_download(REPO_SPACE, "catalogo_medido.csv", repo_type="space", token=HF_TOKEN)
medido = pd.read_csv(csv_medido, dtype={"id": str}).fillna({"hook": "", "temas": "", "author": ""})
ids_curado = None
if CONJUNTO == "curado":
    csv_cur = hf_hub_download(REPO_SPACE, "catalogo_recomendaciones.csv", repo_type="space", token=HF_TOKEN)
    ids_curado = pd.read_csv(csv_cur, dtype=str)["id"].tolist()
lista = seleccionar(medido, CONJUNTO, N_LIBROS, ids_curado).reset_index(drop=True)
print(f"{len(lista)} libros en el conjunto «{CONJUNTO}»")
print("ejemplo de prompt:", construir_prompt(lista.iloc[0].to_dict())[:400])


def ya_hechos() -> set[str]:
    """Ids que YA tienen JSON en el bucket. Se reanuda con esto, no con un contador."""
    hechos = set()
    for x in api.list_bucket_tree(BUCKET, prefix=PREFIJO, recursive=True):
        ruta = getattr(x, "path", "") or ""
        if ruta.endswith(".json") and "/shard_" in ruta:
            hechos.add(Path(ruta).stem.upper())
    return hechos


# %%
# --- 5. Modelo -----------------------------------------------------------------
from diffusers import FluxPipeline

tuberia = FluxPipeline.from_pretrained(MODELO, torch_dtype=torch.bfloat16, token=HF_TOKEN).to("cuda")
tuberia.set_progress_bar_config(disable=True)


def generar(fila: dict):
    """Una portada, su miniatura y su JSON en local. Devuelve (rutas, json)."""
    import io
    prompt = construir_prompt(fila)
    t0 = time.time()
    img = tuberia(prompt, height=ALTO, width=ANCHO, num_inference_steps=PASOS, guidance_scale=0.0,
                  max_sequence_length=256,
                  generator=torch.Generator("cuda").manual_seed(semilla(fila["id"]))).images[0]
    torch.cuda.synchronize()
    segundos = time.time() - t0
    pid = str(fila["id"]).upper()
    b1, b2 = io.BytesIO(), io.BytesIO()
    img.save(b1, "WEBP", quality=CALIDAD_WEBP, method=6)
    mini = img.copy()
    mini.thumbnail((MINIATURA, MINIATURA))
    mini.save(b2, "WEBP", quality=CALIDAD_WEBP, method=6)
    datos = json_de_portada(fila, prompt, paleta_de(img), len(b1.getvalue()) / 1024,
                            len(b2.getvalue()) / 1024, segundos)
    (LOCAL / f"{pid}.webp").write_bytes(b1.getvalue())
    (LOCAL / f"{pid}_256.webp").write_bytes(b2.getvalue())
    (LOCAL / f"{pid}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return [LOCAL / f"{pid}.webp", LOCAL / f"{pid}_256.webp", LOCAL / f"{pid}.json"], datos


# %%
# --- 6. MEDIR 20 (no sube nada) ----------------------------------------------------
# La primera imagen incluye la compilacion/calentamiento: se descarta de la media.
muestra = lista.sample(n=min(21, len(lista)), random_state=20260913).to_dict("records")
tiempos, kbs = [], []
for k, fila in enumerate(muestra):
    _, d = generar(fila)
    if k == 0:
        print(f"calentamiento: {d['segundos']:.1f} s (no cuenta)")
        continue
    tiempos.append(d["segundos"])
    kbs.append(d["kb"]["portada"])
    print(f"{k:2d} {d['id']:>8}  {d['segundos']:.2f} s  {d['kb']['portada']:.0f} KB  "
          f"texto {d['color_texto']} ({d['contraste_texto']}:1)  acento {d['acento']}")
MEDIDA = {"s_por_imagen": sum(tiempos) / len(tiempos), "kb_por_portada": sum(kbs) / len(kbs),
          "gpu": torch.cuda.get_device_name(0)}
horas = len(lista) * MEDIDA["s_por_imagen"] * SOBRECARGA / 3600
print(f"\nMEDIDO en {MEDIDA['gpu']}: {MEDIDA['s_por_imagen']:.2f} s/imagen de GPU, "
      f"{MEDIDA['kb_por_portada']:.0f} KB/portada")
print(f"Estimacion para {len(lista)} libros: {horas:.2f} h, ~{horas * UNIDADES_POR_HORA_A100:.1f} unidades, "
      f"~{len(lista) * MEDIDA['kb_por_portada'] / 1024 / 1024:.2f} GB")
print("Mira las 20 en /content/portadas antes de seguir: si no gustan, se cambia MOTIVOS/ESTILO, no se lanza.")

# %%
# --- 7. TANDA (solo con saldo confirmado) --------------------------------------------
if SALDO_CONFIRMADO is None:
    raise SystemExit("SALDO_CONFIRMADO es None: Miguel tiene que mirar las unidades y ponerlas en la celda 3.")
if "MEDIDA" not in globals():
    raise SystemExit("Primero la celda «Medir 20»: la tanda se estima con cifras medidas, no del estudio.")
pendientes_est = len(lista) - len(ya_hechos())
necesarias = pendientes_est * MEDIDA["s_por_imagen"] * SOBRECARGA / 3600 * UNIDADES_POR_HORA_A100
if SALDO_CONFIRMADO < necesarias * 1.2:
    raise SystemExit(f"Saldo {SALDO_CONFIRMADO} < {necesarias * 1.2:.1f} unidades (estimacion x1,2). No arranca.")

hechos = ya_hechos()
pendientes = [(i, f) for i, f in enumerate(lista.to_dict("records")) if str(f["id"]).upper() not in hechos]
print(f"ya hechos {len(hechos)} | pendientes {len(pendientes)} | necesarias ~{necesarias:.1f} u")
buffer, errores, t0, hechos_ahora = [], 0, time.time(), 0


def volcar(buffer):
    """Sube de golpe lo acumulado y el progreso. Idempotente: reescribir no duplica."""
    if not buffer:
        return
    add = [(str(ruta), f"{PREFIJO}/{shard}/{ruta.name}") for shard, rutas in buffer for ruta in rutas]
    progreso = {"conjunto": CONJUNTO, "total": len(lista), "hechos": len(hechos) + hechos_ahora,
                "errores": errores, "s_por_imagen_medido": round(MEDIDA["s_por_imagen"], 3),
                "actualizado": time.strftime("%Y-%m-%d %H:%M:%S")}
    add.append((json.dumps(progreso, indent=1).encode(), f"{PREFIJO}/progreso.json"))
    for intento in range(4):
        try:
            api.batch_bucket_files(BUCKET, add=add)
            return
        except Exception as e:
            print(f"subida fallida ({intento + 1}/4): {e!r}")
            time.sleep(10 * (intento + 1))
    raise RuntimeError("no se pudo subir el shard; lo local sigue en /content/portadas")


try:
    for n, (i, fila) in enumerate(pendientes, 1):
        try:
            rutas, _ = generar(fila)
            buffer.append((shard_de(i), rutas))
            hechos_ahora += 1
        except Exception as e:
            errores += 1
            print(f"error en {fila.get('id')}: {e!r}")
        if len(buffer) >= SHARD:
            volcar(buffer)
            buffer = []
        if n % 50 == 0:
            ritmo = hechos_ahora / max(1e-9, time.time() - t0) * 60
            print(f"{n}/{len(pendientes)}  {ritmo:.1f} portadas/min  errores {errores}")
finally:
    volcar(buffer)
    print(f"fin: {hechos_ahora} nuevas, {errores} errores, {(time.time() - t0) / 60:.1f} min")
