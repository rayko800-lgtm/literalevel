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
   juntan en bloques de >= 250 palabras de su fuente y nivel, en orden de id;
3) la cola de cada grupo, lo que sobra por debajo de 250 al acabar: se mide
   sola si llega a MIN_WORDS y, si no, se une al ultimo bloque del grupo. Antes
   se tiraba sin medir: 16 textos del 14 sep salian del catalogo sin aviso,
   contados junto a los que rechaza el filtro (auditoria cruzada de e6). Solo
   se queda fuera la cola de un grupo que entero no llega a MIN_WORDS, y se
   cuenta aparte en `df.attrs["cola_sin_medir"]`.
Por eso los bloques no se pueden formar hasta que la primera pasada este
completa: con `--tope` se para ahi y la siguiente ejecucion sigue.

La clave lleva tambien la huella del modelo (config.json y pesos): con otro
modelo, lo medido no se reutiliza. Las medidas anteriores al 15 sep no la
llevan; se aceptan solo si el modelo es el v4 de HUELLA_V4, con el que se
midieron, y se reescriben con la clave nueva.

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
# Un bloque de 3 o más textos se mide también sin cada uno de ellos. Si quitar uno
# solo mueve la medida más de MARGEN_RARO, ese texto es raro: los demás se quedan
# con la medida sin él, y el raro conserva la del bloque entero (no puede bajar de
# nivel) y se marca en `raro_en_bloque`. Fijado ANTES de medir la tanda (Central,
# 15 sep 2026): «APOCALYPTO», una sinopsis de 131 palabras, llevaba su bloque de
# cuentos de nivel 1 de 0,27 a 1,29; en una muestra al azar de 30 bloques, quitar
# un solo texto movía la medida más de 0,5 en 3.
MARGEN_RARO = 0.5


# La del modelo_v4 final (config.json y model.safetensors del 6 sep 2026), con
# el que se midieron los shards del 14 sep. Calculada con `huella_modelo`.
HUELLA_V4 = "fbff06d45f194ca6"


def huella_modelo(carpeta=RAIZ / "modelo_v4"):
    """Huella de config.json y de los pesos (1,6 s para los 328 MB del v4)."""
    h = hashlib.sha256()
    for nombre in ("config.json", "model.safetensors"):
        h.update(nombre.encode())
        h.update(b"\0")
        with open(Path(carpeta) / nombre, "rb") as f:
            for trozo in iter(lambda: f.read(1 << 24), b""):
                h.update(trozo)
        h.update(b"\0")
    return h.hexdigest()[:16]


def clave(tipo, ids, texto, modelo=""):
    """Huella de lo medido: cambia si cambia el texto, la composicion del bloque o
    el modelo. Sin `modelo` es la clave de antes del 15 sep."""
    h = hashlib.sha256()
    for parte in (tipo, "|".join(map(str, ids)), texto) + ((modelo,) if modelo else ()):
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


def medir(df, puntuador=None, carpeta=DIR_MEDIDAS, tope=None, bloque=BLOQUE, salida=print,
          modelo=None, margen=MARGEN_RARO):
    """Rellena `dificultad`, `ventanas` y `medida` de `df` y devuelve (df, completo).

    `tope` limita las unidades NUEVAS medidas en esta llamada; con el tope
    alcanzado, `completo` es False y lo que falte queda sin medida. Sin
    `puntuador` se carga el v4 solo si hay algo nuevo que medir. `modelo` es la
    huella que entra en la clave: sin darla, la del v4 en disco, o el nombre del
    puntuador que se pase."""
    if modelo is None:
        modelo = huella_modelo() if puntuador is None else "puntuador:" + type(puntuador).__name__
    hechas = leer_hechas(carpeta)
    escritor = _Escritor(carpeta)
    df["dificultad"], df["ventanas"], df["medida"] = float("nan"), 0, ""
    df["raro_en_bloque"] = False
    df.attrs["cola_sin_medir"] = []
    df.attrs["bloques_con_raro"] = []
    estado = {"p": puntuador, "nuevas": 0, "ventanas": 0, "t0": time.time(), "completo": True}

    def obtener(tipo, ids, texto):
        k = clave(tipo, ids, texto, modelo)
        if k in hechas:
            return hechas[k]
        if modelo == HUELLA_V4:
            viejo = hechas.get(clave(tipo, ids, texto))
            if viejo is not None and "modelo" not in viejo:
                r = {**viejo, "clave": k, "modelo": modelo}
                escritor.poner(r)
                hechas[k] = r
                return r
        if tope is not None and estado["nuevas"] >= tope:
            estado["completo"] = False
            return None
        if estado["p"] is None:
            estado["p"] = scoring.Puntuador(str(RAIZ / "modelo_v4"))
        r = {"clave": k, "tipo": tipo, "ids": list(ids), "modelo": modelo, **_medir_una(estado["p"], texto)}
        escritor.poner(r)
        hechas[k] = r
        estado["nuevas"] += 1
        estado["ventanas"] += r["ventanas"]
        if estado["nuevas"] % CADA == 0:
            dt = max(1e-9, time.time() - estado["t0"])
            salida(f"  {estado['nuevas']} unidades nuevas | {estado['ventanas'] / dt:.2f} ventanas/s | "
                   f"{estado['nuevas'] / dt * 60:.1f} unidades/min | hechas en total {len(hechas)}")
        return r

    def asignar(idx, ids, trozos):
        """Mide el bloque y reparte su medida; con un texto raro, ver MARGEN_RARO.
        Devuelve False si el tope cortó la medición."""
        r = obtener("bloque", ids, "\n\n".join(trozos))
        if r is None:
            return False
        if r["dificultad"] is None:
            return True
        completo = r["dificultad"]
        raro, sin_raro = None, None
        if margen is not None and len(ids) >= 3:
            mayor = 0.0
            for k in range(len(ids)):
                resto = idx[:k] + idx[k + 1:]
                if sum(int(df.at[j, "palabras"]) for j in resto) < scoring.MIN_WORDS:
                    continue
                rr = obtener("bloque", ids[:k] + ids[k + 1:], "\n\n".join(trozos[:k] + trozos[k + 1:]))
                if rr is None:
                    return False
                if rr["dificultad"] is not None and abs(rr["dificultad"] - completo) > mayor:
                    mayor, raro, sin_raro = abs(rr["dificultad"] - completo), k, rr["dificultad"]
            if mayor <= margen:
                raro, sin_raro = None, None
        for k, j in enumerate(idx):
            df.at[j, "dificultad"] = sin_raro if raro is not None and k != raro else completo
            df.at[j, "medida"] = "bloque"
        if raro is not None:
            df.at[idx[raro], "raro_en_bloque"] = True
            df.attrs["bloques_con_raro"].append({"ids": list(ids), "raro": ids[raro],
                                                 "completo": completo, "sin_raro": sin_raro})
        return True

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
            previo = None                     # (idx, ids, trozos) del ultimo bloque del grupo
            for i, f in g.iterrows():
                idx.append(i)
                ids.append(f["id"])
                trozos.append(f["texto"])
                cuenta += f["palabras"]
                if cuenta >= bloque:
                    if not asignar(idx, ids, trozos):
                        return df, False
                    previo = (idx, ids, trozos)
                    idx, ids, trozos, cuenta = [], [], [], 0
            if not idx:
                continue
            # 3) la cola: sola si llega a MIN_WORDS; si no, con el ultimo bloque.
            if cuenta < scoring.MIN_WORDS and previo is None:
                df.attrs["cola_sin_medir"].extend(ids)
                continue
            if cuenta < scoring.MIN_WORDS:
                idx, ids, trozos = previo[0] + idx, previo[1] + ids, previo[2] + trozos
            if not asignar(idx, ids, trozos):
                return df, False
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
    modelo = huella_modelo()
    pendientes = [t for i, t in zip(solos["id"], solos["texto"])
                  if clave("texto", [i], t, modelo) not in hechas
                  and not (modelo == HUELLA_V4 and clave("texto", [i], t) in hechas)]
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
    cola = len(df.attrs.get("cola_sin_medir", []))
    print(f"completo: {completo} | con medida {medidos} de {len(df)} "
          f"(texto {int((df['medida'] == 'texto').sum())}, bloque {int((df['medida'] == 'bloque').sum())}) | "
          f"sin medida: {len(df) - medidos - cola} por el filtro de prosa, {cola} en grupos de menos de "
          f"{scoring.MIN_WORDS} palabras")


if __name__ == "__main__":
    main()
