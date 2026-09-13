"""Validacion del v4 con corpus de lectura GRADUADA por sus editores.

Uso:
    python -X utf8 validar_graduados.py                      # todas las fuentes bajadas
    python -X utf8 validar_graduados.py --fuente storyweaver
    python -X utf8 validar_graduados.py --tope 40            # 40 textos por fuente y nivel

QUE SE VALIDA Y QUE NO. El nivel de StoryWeaver (1-4) y el de African Storybook
(1-5) los pone cada editor con su propio criterio para lectores infantiles: NO
son niveles del MCER. Por eso lo unico que se puede comprobar es el ORDEN: si el
nivel 1 del editor puntua por debajo del 2, el 2 del 3, etc. Una media de 0,6
en el nivel 1 no significa "el modelo dice A2" en ningun sentido certificable.

LOS CUENTOS CORTOS. El v4 lee ventanas de 250 palabras y rechaza textos de menos
de 150. Muchos cuentos infantiles no llegan. Decision de Miguel (12 sep 2026):
- los de 250 palabras o mas se puntuan solos;
- los mas cortos se juntan, SIEMPRE dentro de la misma fuente y el mismo nivel,
  en bloques de al menos 250 palabras. Juntar niveles distintos mezclaria justo
  lo que se quiere medir. El orden de union es estable (por identificador) para
  que el resultado se pueda repetir.
Las metricas se dan por separado para "solos" y "bloques": un bloque de cinco
cuentos no es un texto natural y conviene ver si se porta distinto.

FUGA. Igual que con OneStopEnglish: se descarta cualquier texto que comparta la
mitad o mas de sus 8-gramas con ELG CEFR English, el corpus de entrenamiento.

Mismas metricas que validar_onestop.py: medias por nivel, Spearman contra el
nivel, la linea base de contar palabras y la correlacion parcial que descuenta
la longitud. Las puntuaciones se guardan sin texto en auditoria/.
"""
import argparse
import json
import os
import re
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, "app")
import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download
from scoring import Puntuador, words

RAIZ = Path(__file__).resolve().parent
FUENTES = {
    "storyweaver": RAIZ / "corpus_graduado" / "storyweaver" / "textos" / "libros.jsonl",
    "african_storybook": RAIZ / "corpus_graduado" / "african_storybook" / "textos" / "cuentos.jsonl",
    # Sin nivel por articulo: solo se describe, no entra en las metricas de orden.
    "voa": RAIZ / "corpus_graduado" / "voa" / "textos" / "articulos.jsonl",
}
SOLO_DESDE = 250
N_GRAMA = 8
SALIDA = RAIZ / "auditoria" / "validacion_graduados_puntuaciones.csv"

RUTA_MODELO = os.environ.get("LITERALEVEL_MODELO", str(RAIZ / "modelo_v4"))
if not os.path.isdir(RUTA_MODELO):
    sys.exit(f"No encuentro el modelo en {RUTA_MODELO}.")


def _norm(t):
    return re.sub(r"\s+", " ", str(t)).strip().lower()


def _gramas(t):
    toks = re.findall(r"[a-z0-9']+", _norm(t))
    return {" ".join(toks[i:i + N_GRAMA]) for i in range(max(0, len(toks) - N_GRAMA + 1))}


def _rangos(v):
    return pd.Series(list(v)).rank(method="average").to_numpy()


def _pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    da, db = a - a.mean(), b - b.mean()
    den = float(np.sqrt((da ** 2).sum() * (db ** 2).sum()))
    return float("nan") if den == 0 else float((da * db).sum() / den)


def _spearman(a, b):
    return _pearson(_rangos(a), _rangos(b))


# Las primeras 48 lineas de StoryWeaver se bajaron antes de pasar al orden
# aleatorio: vienen del listado de la API, que pone primero los libros mejor
# valorados. Con ellas la muestra tendria sesgo de popularidad, asi que se
# apartan; todo lo que sigue se bajo en orden aleatorio e intercalando niveles.
SESGADAS_AL_PRINCIPIO = {"storyweaver": 48}


def cargar(fuente, ruta, tope):
    filas = [json.loads(l) for l in ruta.open(encoding="utf-8")]
    filas = filas[SESGADAS_AL_PRINCIPIO.get(fuente, 0):]
    df = pd.DataFrame(filas)
    df["fuente"] = fuente
    for col in ("slug", "archivo", "url"):
        if col in df:
            df["clave"] = df[col].astype(str)
            break
    if "nivel_editor" not in df:
        df["nivel_editor"] = None
    # El nivel llega como texto ("1"), numero o vacio segun la fuente; sin
    # normalizar, pandas mezcla float(nan) con cadenas y ni se puede contar.
    df["nivel_editor"] = [None if v is None or (isinstance(v, float) and np.isnan(v))
                          or str(v).strip() in ("", "None", "nan") else str(int(float(v)))
                          for v in df["nivel_editor"]]
    # Cada pagina de un libro ilustrado es un parrafo, pero llega partida en
    # renglones de una frase (African Storybook) o con saltos a mitad de frase
    # (StoryWeaver). Tal cual, el filtro de prosa del v4 los tomaba por listas:
    # la primera pasada rechazo 70 de 219 unidades de African Storybook con
    # "parece una lista, un menu o una tabla". Se une cada pagina en un
    # parrafo y las paginas se separan con una linea en blanco.
    def _parrafos(t):
        # VOA: el reproductor de audio deja este aviso delante de cada articulo
        # bajado antes de que el descargador lo quitara. No es prosa.
        t = re.sub(r"(?im)^\s*No media source currently available\.?\s*$", "", str(t or ""))
        paginas = re.split(r"\n\s*\n", t)
        return "\n\n".join(re.sub(r"\s+", " ", p).strip() for p in paginas if p.strip())

    df["texto"] = df["texto"].map(_parrafos)
    df["palabras"] = df["texto"].map(lambda t: len(words(t)))
    df = df[df["palabras"] > 0]
    if tope:
        df = (df.sort_values("clave").groupby("nivel_editor", dropna=False, group_keys=False)
                .head(tope))
    return df


def unidades(df):
    """Solos (>=250 palabras) y bloques de cortos dentro de fuente y nivel."""
    out = []
    for (fuente, nivel), g in df.groupby(["fuente", "nivel_editor"], dropna=False):
        g = g.sort_values("clave")
        for _, f in g[g["palabras"] >= SOLO_DESDE].iterrows():
            out.append({"fuente": fuente, "nivel": nivel, "tipo": "solo",
                        "claves": f["clave"], "n_textos": 1, "texto": f["texto"]})
        trozos, claves, cuenta = [], [], 0
        for _, f in g[g["palabras"] < SOLO_DESDE].iterrows():
            trozos.append(f["texto"])
            claves.append(f["clave"])
            cuenta += f["palabras"]
            if cuenta >= SOLO_DESDE:
                out.append({"fuente": fuente, "nivel": nivel, "tipo": "bloque",
                            "claves": "|".join(claves), "n_textos": len(claves),
                            "texto": "\n\n".join(trozos)})
                trozos, claves, cuenta = [], [], 0
        # La cola que no llega a 250 no se estira ni se mezcla con otro nivel:
        # se declara y se deja fuera.
        if claves:
            out.append({"fuente": fuente, "nivel": nivel, "tipo": "cola_corta",
                        "claves": "|".join(claves), "n_textos": len(claves),
                        "texto": "\n\n".join(trozos)})
    return pd.DataFrame(out)


def metricas(df, titulo):
    d = df[df["puntuacion"].notna() & df["nivel"].notna()].copy()
    if d.empty or d["nivel"].nunique() < 2:
        print(f"\n{titulo}: sin datos suficientes ({len(d)} unidades)")
        return None
    d["ordinal"] = d["nivel"].astype(int)
    print(f"\n{titulo} — {len(d)} unidades")
    print(f"  {'nivel':<6}{'n':>6}{'media 0-2':>11}{'desv':>8}{'palabras':>10}")
    medias = []
    for nivel, g in d.groupby("ordinal"):
        medias.append(g["puntuacion"].mean())
        print(f"  {nivel:<6}{len(g):>6}{g['puntuacion'].mean():>11.3f}"
              f"{g['puntuacion'].std(ddof=0):>8.3f}{g['palabras'].mean():>10.0f}")
    s_mod = _spearman(d["puntuacion"], d["ordinal"])
    s_pal = _spearman(d["palabras"], d["ordinal"])
    s_mp = _spearman(d["puntuacion"], d["palabras"])
    den = (1 - s_mp ** 2) * (1 - s_pal ** 2)
    parcial = (s_mod - s_mp * s_pal) / np.sqrt(den) if den > 0 else float("nan")
    creciente = all(a < b for a, b in zip(medias, medias[1:]))
    print(f"  Spearman modelo vs nivel: {s_mod:.3f} | contar palabras: {s_pal:.3f} | "
          f"modelo descontando longitud: {parcial:.3f}")
    print(f"  medias {'ESTRICTAMENTE CRECIENTES' if creciente else 'NO crecientes'}")
    return {"titulo": titulo, "n": len(d), "spearman": s_mod, "palabras": s_pal,
            "parcial": parcial, "creciente": creciente,
            "medias": [round(float(m), 3) for m in medias]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuente", choices=sorted(FUENTES), default=None)
    ap.add_argument("--tope", type=int, default=None)
    args = ap.parse_args()

    marcos = []
    for fuente, ruta in FUENTES.items():
        if args.fuente and fuente != args.fuente:
            continue
        if not ruta.exists():
            print(f"(sin datos de {fuente}: {ruta})")
            continue
        df = cargar(fuente, ruta, args.tope)
        cuenta = Counter("sin nivel" if v is None or v != v else str(v) for v in df["nivel_editor"])
        print(f"{fuente}: {len(df)} textos | por nivel {sorted(cuenta.items())}")
        marcos.append(df)
    if not marcos:
        sys.exit("No hay corpus bajado.")
    textos = pd.concat(marcos, ignore_index=True)

    # --- Fuga contra el entrenamiento -------------------------------------
    elg = pd.read_json(hf_hub_download("UniversalCEFR/elg_cefr_en", "elg-cefr-en.json",
                                       repo_type="dataset"))
    gramas_elg = set()
    for t in elg["text"]:
        gramas_elg |= _gramas(t)
    textos["compartido_con_elg"] = [len(_gramas(t) & gramas_elg) / max(1, len(_gramas(t)))
                                    for t in textos["texto"]]
    fuga = int((textos["compartido_con_elg"] >= 0.5).sum())
    print(f"\nFuga contra ELG CEFR English ({len(elg)} textos): maximo "
          f"{textos['compartido_con_elg'].max():.3f} · textos con >=50 %: {fuga}")
    textos = textos[textos["compartido_con_elg"] < 0.5]

    con_nivel = textos[textos["nivel_editor"].notna()]
    sin_nivel = textos[textos["nivel_editor"].isna()]
    u = unidades(con_nivel)
    if not sin_nivel.empty:
        s = sin_nivel.copy()
        s["nivel_editor"] = None
        us = unidades(s.assign(nivel_editor="sin"))
        us["nivel"] = None
        u = pd.concat([u, us], ignore_index=True)

    # --- Puntuar ------------------------------------------------------------
    p = Puntuador(RUTA_MODELO)
    t0 = time.time()
    puntos, motivos = [], []
    medibles = u["tipo"] != "cola_corta"
    for k, (texto, medir) in enumerate(zip(u["texto"], medibles), 1):
        if not medir:
            puntos.append(float("nan"))
            motivos.append("cola corta, fuera")
            continue
        try:
            puntos.append(float(p.puntuar(texto).puntuacion))
            motivos.append("")
        except ValueError as e:
            puntos.append(float("nan"))
            motivos.append(str(e)[:60])
        if k % 200 == 0:
            print(f"  {k}/{len(u)} · {(time.time() - t0) / k:.2f} s por unidad", flush=True)
    u["puntuacion"] = puntos
    u["motivo_rechazo"] = motivos
    u["palabras"] = u["texto"].map(lambda t: len(words(t)))
    print(f"\npuntuadas {int(u['puntuacion'].notna().sum())} de {len(u)} unidades en "
          f"{(time.time() - t0) / 60:.1f} min")
    rech = u[u["puntuacion"].isna()]
    if len(rech):
        print("rechazos por fuente, nivel y motivo:")
        for (f, n, m), c in rech.groupby(["fuente", rech["nivel"].astype(str), "motivo_rechazo"]).size().items():
            print(f"  {f:<18} nivel {n:<5} {c:>4}  {m}")

    # --- Metricas -----------------------------------------------------------
    resumen = []
    for fuente, g in u[u["nivel"].notna()].groupby("fuente"):
        resumen.append(metricas(g, f"{fuente} · todas las unidades"))
        resumen.append(metricas(g[g["tipo"] == "solo"], f"{fuente} · solo textos de >=250 palabras"))
        resumen.append(metricas(g[g["tipo"] == "bloque"], f"{fuente} · solo bloques de cuentos cortos"))
    sn = u[u["nivel"].isna() & u["puntuacion"].notna()]
    for fuente, g in sn.groupby("fuente"):
        print(f"\nSin nivel del editor · {fuente}: {len(g)} unidades · media {g['puntuacion'].mean():.3f} · "
              f"cuartiles {np.percentile(g['puntuacion'], [25, 50, 75]).round(3).tolist()} · "
              f"palabras medias {g['palabras'].mean():.0f}")

    SALIDA.parent.mkdir(exist_ok=True)
    u.drop(columns=["texto"]).to_csv(SALIDA, index=False)
    print(f"\npuntuaciones (sin texto) en {SALIDA}")
    with open(SALIDA.with_suffix(".json"), "w", encoding="utf-8") as f:
        json.dump([r for r in resumen if r], f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
