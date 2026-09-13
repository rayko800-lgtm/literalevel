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
import scoring
from scoring import Puntuador, words

RAIZ = Path(__file__).resolve().parent
FUENTES = {
    "storyweaver": RAIZ / "corpus_graduado" / "storyweaver" / "textos" / "libros.jsonl",
    "african_storybook": RAIZ / "corpus_graduado" / "african_storybook" / "textos" / "cuentos.jsonl",
    # Sin nivel por articulo: solo se describe, no entra en las metricas de orden.
    "voa": RAIZ / "corpus_graduado" / "voa" / "textos" / "articulos.jsonl",
    # Niveles 1-5 del editor; casi todo con licencia NC: se valida, pero interno.
    "letsread": RAIZ / "corpus_graduado" / "letsread" / "textos" / "libros.jsonl",
}
SOLO_DESDE = 250
_SIN_JS = re.compile(
    r"(?m)^[ \t]*(?:\$\(document\)\.ready\(function\(\)\s*\{|var story_editor = .*|"
    r"var dictionary = new HTMLContent\(\);|if\(story_editor\.is_translate\(\)\)\s*\{|"
    r"dictionary\.init\(.*\);|\}\);|\}|\d{1,3}/\d{1,3})[ \t]*$\n?")
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


def _puntuar_sin_filtro(p, texto):
    """Como Puntuador.puntuar pero sin continuous_prose: ventanas, media, escala 0-2."""
    bloques = scoring.fixed_blocks(scoring.normalize(texto))
    if not bloques:
        return float("nan")
    interno = float(np.mean(p._puntuar_bloques(bloques)))
    return round(float(scoring.public_score(interno)), 3)


def _rangos(v):
    return pd.Series(list(v)).rank(method="average").to_numpy()


def _pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    da, db = a - a.mean(), b - b.mean()
    den = float(np.sqrt((da ** 2).sum() * (db ** 2).sum()))
    return float("nan") if den == 0 else float((da * db).sum() / den)


def _spearman(a, b):
    return _pearson(_rangos(a), _rangos(b))


# Los 48 primeros libros de StoryWeaver se bajaron antes de pasar al orden
# aleatorio: vienen del listado de la API, que pone primero los mejor valorados
# (33 de ellos de nivel 1). Con ellos la muestra tendria sesgo de popularidad.
# Se apartan POR SLUG, no por posicion: cortar las 48 primeras lineas se rompia
# en cuanto el archivo se reordenara (revision metodologica de Fable).
SESGADAS = RAIZ / "auditoria" / "storyweaver_sesgadas_48.txt"
B_BOOTSTRAP = 2000
SEMILLA = 20260912


def _slugs_sesgados():
    if not SESGADAS.exists():
        return set()
    return {l.strip() for l in SESGADAS.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")}


def cargar(fuente, ruta, tope, con_sesgadas=False):
    filas = [json.loads(l) for l in ruta.open(encoding="utf-8")]
    if fuente == "storyweaver" and not con_sesgadas:
        fuera = _slugs_sesgados()
        filas = [f for f in filas if f.get("slug") not in fuera]
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
        # StoryWeaver: el bloque de JavaScript del lector web y el contador de
        # pagina ("2/10") venian dentro del texto de TODOS los libros bajados
        # antes del arreglo del descargador. Solo lineas enteras, para no tocar
        # una frase que diga "window".
        t = _SIN_JS.sub("", t)
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


def _parcial(mod, lon, niv):
    s_mod, s_lon, s_ml = _spearman(mod, niv), _spearman(lon, niv), _spearman(mod, lon)
    den = (1 - s_ml ** 2) * (1 - s_lon ** 2)
    return s_mod, s_lon, ((s_mod - s_ml * s_lon) / np.sqrt(den) if den > 0 else float("nan"))


def metricas(df, titulo, col="puntuacion"):
    """Orden contra el nivel del editor, con su incertidumbre.

    Tres correcciones de la revision metodologica de Fable (12 sep 2026):
    - Intervalos bootstrap al 95 % para Spearman y la parcial, y la frecuencia
      con que las medias salen crecientes al remuestrear: "estrictamente
      crecientes" sin eso afirmaba un orden 1 < 2 que no aguanta un remuestreo.
    - La longitud de un BLOQUE no es la de sus cuentos sino cuantos cupieron;
      como covariable se usa la longitud natural media (palabras / n_textos).
    - Se da la correlacion modelo-longitud DENTRO de cada nivel: el v4 lee
      ventanas de 250 palabras y no ve la longitud; si esa correlacion es ~0,
      la que aparece entre niveles viene de como el editor define sus niveles.
    """
    d = df[df[col].notna() & df["nivel"].notna()].copy()
    if d.empty or d["nivel"].nunique() < 2:
        print(f"\n{titulo}: sin datos suficientes ({len(d)} unidades)")
        return None
    d["ordinal"] = d["nivel"].astype(int)
    d["longitud"] = np.where(d["tipo"] == "bloque", d["palabras"] / d["n_textos"].clip(lower=1),
                             d["palabras"])
    print(f"\n{titulo} [{col}] — {len(d)} unidades")
    print(f"  {'nivel':<6}{'n':>6}{'media 0-2':>11}{'IC 95 %':>18}{'desv':>8}{'longitud':>10}{'rho v4-long.':>13}")
    rng = np.random.default_rng(SEMILLA)
    medias, intra = [], {}
    for nivel, g in d.groupby("ordinal"):
        v = g[col].to_numpy()
        boots = [rng.choice(v, len(v)).mean() for _ in range(1000)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        rho = _spearman(g[col], g["longitud"]) if len(g) >= 5 else float("nan")
        intra[int(nivel)] = round(float(rho), 3)
        medias.append(v.mean())
        print(f"  {nivel:<6}{len(g):>6}{v.mean():>11.3f}{f'[{lo:.3f}; {hi:.3f}]':>18}"
              f"{g[col].std(ddof=0):>8.3f}{g['longitud'].mean():>10.0f}{rho:>13.2f}")
    s_mod, s_lon, parcial = _parcial(d[col], d["longitud"], d["ordinal"])
    creciente = all(a < b for a, b in zip(medias, medias[1:]))
    niveles = sorted(d["ordinal"].unique())
    boot_s, boot_p, boot_c = [], [], 0
    idx = np.arange(len(d))
    for _ in range(B_BOOTSTRAP):
        m = d.iloc[rng.choice(idx, len(idx))]
        if m["ordinal"].nunique() < len(niveles):
            continue
        s, _, pa = _parcial(m[col], m["longitud"], m["ordinal"])
        boot_s.append(s)
        boot_p.append(pa)
        mm = m.groupby("ordinal")[col].mean().to_numpy()
        boot_c += all(a < b for a, b in zip(mm, mm[1:]))
    ic_s = np.nanpercentile(boot_s, [2.5, 97.5]) if boot_s else [float("nan")] * 2
    ic_p = np.nanpercentile(boot_p, [2.5, 97.5]) if boot_p else [float("nan")] * 2
    p_crec = boot_c / max(1, len(boot_s))
    print(f"  Spearman v4 vs nivel: {s_mod:.3f} [{ic_s[0]:.3f}; {ic_s[1]:.3f}] | "
          f"longitud vs nivel: {s_lon:.3f} | v4 descontando longitud: {parcial:.3f} "
          f"[{ic_p[0]:.3f}; {ic_p[1]:.3f}]")
    print(f"  medias {'crecientes' if creciente else 'NO crecientes'} en la muestra; "
          f"crecientes en el {100 * p_crec:.1f} % de {len(boot_s)} remuestreos")
    return {"titulo": titulo, "columna": col, "n": len(d),
            "spearman": round(s_mod, 3), "ic95_spearman": [round(float(x), 3) for x in ic_s],
            "longitud": round(s_lon, 3), "parcial": round(float(parcial), 3),
            "ic95_parcial": [round(float(x), 3) for x in ic_p],
            "creciente_en_muestra": creciente, "p_creciente_bootstrap": round(p_crec, 3),
            "medias": [round(float(m), 3) for m in medias], "rho_v4_longitud_por_nivel": intra}


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
    puntos, motivos, sin_filtro = [], [], []
    medibles = u["tipo"] != "cola_corta"
    for k, (texto, medir) in enumerate(zip(u["texto"], medibles), 1):
        if not medir:
            puntos.append(float("nan"))
            motivos.append("cola corta, fuera")
            sin_filtro.append(float("nan"))
            continue
        try:
            puntos.append(float(p.puntuar(texto).puntuacion))
            motivos.append("")
        except ValueError as e:
            puntos.append(float("nan"))
            motivos.append(str(e)[:60])
        # Sensibilidad: la misma puntuacion SIN el filtro estructural de prosa.
        # En African Storybook el filtro rechazaba 42 de los 65 cuentos de nivel
        # 1 (una frase corta por pagina parece una lista) y sobrevivian justo los
        # de frases mas largas: sesgo de supervivencia hacia arriba (Fable). La
        # app mantiene el filtro; esto solo mide cuanto cambia la validacion.
        sin_filtro.append(_puntuar_sin_filtro(p, texto))
        if k % 200 == 0:
            print(f"  {k}/{len(u)} · {(time.time() - t0) / k:.2f} s por unidad", flush=True)
    u["puntuacion"] = puntos
    u["puntuacion_sin_filtro"] = sin_filtro
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
        resumen.append(metricas(g, f"{fuente} · todas, SIN filtro de prosa (sensibilidad)",
                                col="puntuacion_sin_filtro"))
    sn = u[u["nivel"].isna() & u["puntuacion"].notna()]
    for fuente, g in sn.groupby("fuente"):
        print(f"\nSin nivel del editor · {fuente}: {len(g)} unidades · media {g['puntuacion'].mean():.3f} · "
              f"cuartiles {np.percentile(g['puntuacion'], [25, 50, 75]).round(3).tolist()} · "
              f"palabras medias {g['palabras'].mean():.0f}")

    # Un archivo por fuente cuando se pide una sola. Antes cada corrida
    # sobrescribia el mismo CSV, y medir VOA borro las puntuaciones de African
    # Storybook que ya estaban commiteadas.
    salida = SALIDA if not args.fuente else SALIDA.with_name(
        f"{SALIDA.stem}_{args.fuente}{SALIDA.suffix}")
    salida.parent.mkdir(exist_ok=True)
    u.drop(columns=["texto"]).to_csv(salida, index=False)
    print(f"\npuntuaciones (sin texto) en {salida}")
    with open(salida.with_suffix(".json"), "w", encoding="utf-8") as f:
        json.dump([r for r in resumen if r], f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
