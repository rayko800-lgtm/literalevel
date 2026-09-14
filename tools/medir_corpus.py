"""Paso 6 del pipeline (PIPELINE_CORPUS.md): medir con el v4 los textos libres del
catalogo externo, por shards reanudables.

    python -X utf8 tools/medir_corpus.py              # todo lo pendiente
    python -X utf8 tools/medir_corpus.py --tope 200   # 200 unidades nuevas y para

Antes lo hacia `catalogar_corpus.puntuar` de un tiron: con los 15.942 libros de
StoryWeaver (14 sep 2026) eran ~12.600 unidades y ~32.000 ventanas en CPU, horas
sin poder cortar. Ahora cada unidad medida se guarda en
corpus_graduado/medidas/medidas_NNNN.jsonl (de 250 en 250) con una clave de su
CONTENIDO, y el catalogador reutiliza lo medido.

El reparto es el mismo que tenia `puntuar`, y el orden importa:
1) cada texto con >= MIN_WORDS palabras se mide solo;
2) los que quedan -los cortos Y los que el filtro de prosa rechazo en 1)- se
   juntan en bloques de >= 250 palabras de su fuente y nivel, en orden de id.
Por eso los bloques no se pueden formar hasta que la primera pasada este
completa: con `--tope` se para ahi y la siguiente ejecucion sigue.

Reanudar lee los ids hechos del disco, no lleva un contador: un contador miente
en cuanto algo se cae a mitad (skill precalculo-en-colab).
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "tools"))
import scoring  # noqa: E402

DIR_MEDIDAS = RAIZ / "corpus_graduado" / "medidas"
SHARD = 250
CADA = 100
BLOQUE = 250


def clave(tipo, ids, texto):
    """Huella del contenido medido: cambia si cambia el texto o la composicion del bloque."""
    h = hashlib.sha256()
    for parte in (tipo, "|".join(map(str, ids)), texto):
        h.update(str(parte).encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:24]


def leer_hechas(carpeta=DIR_MEDIDAS):
    """{clave: registro} de todos los shards. Una linea cortada por un corte se ignora."""
    hechas = {}
    for ruta in sorted(Path(carpeta).glob("medidas_*.jsonl")):
        for linea in ruta.open(encoding="utf-8"):
            try:
                r = json.loads(linea)
                hechas[r["clave"]] = r
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
    return hechas


class _Escritor:
    """Acumula registros y los escribe de SHARD en SHARD, con reemplazo atomico."""

    def __init__(self, carpeta):
        self.carpeta = Path(carpeta)
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.buffer = []
        self.n = len(list(self.carpeta.glob("medidas_*.jsonl")))

    def poner(self, registro):
        self.buffer.append(registro)
        if len(self.buffer) >= SHARD:
            self.volcar()

    def volcar(self):
        if not self.buffer:
            return
        ruta = self.carpeta / f"medidas_{self.n:04d}.jsonl"
        while ruta.exists():                      # otra ejecucion pudo escribir entre medias
            self.n += 1
            ruta = self.carpeta / f"medidas_{self.n:04d}.jsonl"
        temporal = ruta.with_suffix(".tmp")
        temporal.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in self.buffer),
                            encoding="utf-8")
        temporal.replace(ruta)
        self.n += 1
        self.buffer = []


def _medir_una(p, texto):
    try:
        r = p.puntuar(texto)
        return {"dificultad": round(float(r.puntuacion), 4),
                "ventanas": int(getattr(r, "n_bloques", 0) or 0), "error": None}
    except ValueError as e:
        return {"dificultad": None, "ventanas": 0, "error": str(e)[:160]}


def medir(df, puntuador=None, carpeta=DIR_MEDIDAS, tope=None, bloque=BLOQUE, salida=print):
    """Rellena `dificultad`, `ventanas` y `medida` de `df` y devuelve (df, completo).

    `tope` limita las unidades NUEVAS medidas en esta llamada; con el tope
    alcanzado, `completo` es False y lo que falte queda sin medida. Sin
    `puntuador` se carga el v4 solo si hay algo nuevo que medir."""
    hechas = leer_hechas(carpeta)
    escritor = _Escritor(carpeta)
    df["dificultad"], df["ventanas"], df["medida"] = float("nan"), 0, ""
    estado = {"p": puntuador, "nuevas": 0, "ventanas": 0, "t0": time.time(), "completo": True}

    def obtener(tipo, ids, texto):
        k = clave(tipo, ids, texto)
        if k in hechas:
            return hechas[k]
        if tope is not None and estado["nuevas"] >= tope:
            estado["completo"] = False
            return None
        if estado["p"] is None:
            estado["p"] = scoring.Puntuador(str(RAIZ / "modelo_v4"))
        r = {"clave": k, "tipo": tipo, "ids": list(ids), **_medir_una(estado["p"], texto)}
        escritor.poner(r)
        hechas[k] = r
        estado["nuevas"] += 1
        estado["ventanas"] += r["ventanas"]
        if estado["nuevas"] % CADA == 0:
            dt = max(1e-9, time.time() - estado["t0"])
            salida(f"  {estado['nuevas']} unidades nuevas | {estado['ventanas'] / dt:.2f} ventanas/s | "
                   f"{estado['nuevas'] / dt * 60:.1f} unidades/min | hechas en total {len(hechas)}")
        return r

    try:
        # 1) cada texto que se pueda puntuar solo
        for i, f in df.sort_values("id").iterrows():
            if f["palabras"] < scoring.MIN_WORDS:
                continue
            r = obtener("texto", [f["id"]], f["texto"])
            if r is not None and r["dificultad"] is not None:
                df.at[i, "dificultad"] = r["dificultad"]
                df.at[i, "ventanas"] = r["ventanas"]
                df.at[i, "medida"] = "texto"
        if not estado["completo"]:
            return df, False          # sin la primera pasada entera no hay bloques fiables
        # 2) los que quedan, en bloques de su fuente y nivel
        resto = df[df["medida"] == ""].sort_values("id")
        for (_, _), g in resto.groupby(["fuente", resto["nivel_editor"].fillna("sin")]):
            idx, ids, trozos, cuenta = [], [], [], 0
            for i, f in g.iterrows():
                idx.append(i)
                ids.append(f["id"])
                trozos.append(f["texto"])
                cuenta += f["palabras"]
                if cuenta >= bloque:
                    r = obtener("bloque", ids, "\n\n".join(trozos))
                    if r is None:
                        return df, False
                    if r["dificultad"] is not None:
                        for j in idx:
                            df.at[j, "dificultad"] = r["dificultad"]
                            df.at[j, "medida"] = "bloque"
                    idx, ids, trozos, cuenta = [], [], [], 0
    finally:
        escritor.volcar()
    return df, estado["completo"]


def main():
    import catalogar_corpus as cc
    ap = argparse.ArgumentParser()
    ap.add_argument("--tope", type=int, default=None, help="unidades nuevas a medir y parar")
    args = ap.parse_args()
    df = cc.cargar(None)
    solos = df[df["palabras"] >= scoring.MIN_WORDS]
    hechas = leer_hechas()
    pendientes = [t for i, t in zip(solos["id"], solos["texto"]) if clave("texto", [i], t) not in hechas]
    print(f"textos libres {len(df)} | solos {len(solos)} | solos pendientes {len(pendientes)} | "
          f"unidades ya medidas en disco {len(hechas)}")
    t0 = time.time()
    df, completo = medir(df, tope=args.tope)
    dt = time.time() - t0
    nuevas = len(leer_hechas()) - len(hechas)
    if nuevas and not completo:
        ventanas_pend = sum(len(scoring.fixed_blocks(scoring.normalize(t))) for t in pendientes[nuevas:])
        vel = sum(r["ventanas"] for r in list(leer_hechas().values())[-nuevas:]) / max(1e-9, dt)
        print(f"medidas {nuevas} unidades en {dt / 60:.1f} min ({vel:.2f} ventanas/s). "
              f"Quedan ~{len(pendientes) - nuevas} solos (~{ventanas_pend} ventanas) + los bloques: "
              f"~{ventanas_pend / max(vel, 1e-9) / 3600:.2f} h a esta velocidad.")
    medidos = int(df["dificultad"].notna().sum())
    print(f"completo: {completo} | con medida {medidos} de {len(df)} "
          f"(texto {int((df['medida'] == 'texto').sum())}, bloque {int((df['medida'] == 'bloque').sum())})")


if __name__ == "__main__":
    main()
