"""Paso 7 del pipeline (PIPELINE_CORPUS.md): los textos LIBRES entran al catalogo.

    python -X utf8 tools/catalogar_corpus.py              # todas las fuentes bajadas
    python -X utf8 tools/catalogar_corpus.py --tope 30    # 30 por fuente, para probar

Solo entra lo marcado `al_catalogo` por su descargador (dominio publico o CC BY).
Lo que tiene derechos se mide en validar_graduados.py y se queda interno: aqui
se comprueba otra vez y el guion ABORTA si algo con derechos llegara a colarse.

Cada libro lleva la dificultad del v4 medida sobre SU texto. Un cuento de menos
de 150 palabras no se puede puntuar solo (el v4 lee ventanas de 250 y rechaza
por debajo de 150): toma la puntuacion del bloque de cuentos cortos de su misma
fuente y nivel en que se midio, y se marca `medida = bloque` para decirlo. Si ni
eso -el filtro de prosa lo rechaza-, no entra: sin medida no hay recomendacion.

Salen, en la raiz del repositorio:
- catalogo_externo.csv   mismas columnas que catalogo_medido.csv, mas fuente,
                         licencia, atribucion, url, nivel_editor y medida;
- corpus_abierto.parquet el texto que la aplicacion sirve al abrir el libro,
                         con su atribucion al final (CC BY la exige).
"""
import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))
import pandas as pd

import scoring
from scoring import Puntuador, words

CORPUS = RAIZ / "corpus_graduado"
FUENTES = {
    "storyweaver": CORPUS / "storyweaver" / "textos" / "libros.jsonl",
    "african_storybook": CORPUS / "african_storybook" / "textos" / "cuentos.jsonl",
    "voa": CORPUS / "voa" / "textos" / "articulos.jsonl",
    "letsread": CORPUS / "letsread" / "textos" / "libros.jsonl",
}
CSV_SALIDA = RAIZ / "catalogo_externo.csv"
TEXTOS_SALIDA = RAIZ / "corpus_abierto.parquet"
BLOQUE = 250
# Licencias que dejan entrar al catalogo, EXACTAS una vez normalizadas. Antes era
# una regex con "dominio publico.*", y "dominio publico salvo material adaptado
# de Reuters" pasaba (auditoria de Codex, 12 de septiembre de 2026).
LIBRES = {"cc by", "cc by 4.0", "cc by 3.0", "dominio publico (voa)"}
AGENCIAS = re.compile(r"(?i)associated press|reuters|\bafp\b|agence france")


def licencia_libre(licencia, fila=None) -> bool:
    norma = re.sub(r"[\s\-_]+", " ", str(licencia or "")).strip().lower()
    if norma not in LIBRES:
        return False
    # Y aunque la etiqueta sea libre, nada que venga de una agencia.
    if fila is not None and (fila.get("agencia") or AGENCIAS.search(str(fila.get("credito") or ""))):
        return False
    return True


_SIN_JS = re.compile(
    r"(?m)^[ \t]*(?:\$\(document\)\.ready\(function\(\)\s*\{|var story_editor = .*|"
    r"var dictionary = new HTMLContent\(\);|if\(story_editor\.is_translate\(\)\)\s*\{|"
    r"dictionary\.init\(.*\);|\}\);|\}|\d{1,3}/\d{1,3})[ \t]*$\n?")


def parrafos(t):
    """Igual que validar_graduados.py: cada pagina un parrafo, sin avisos ni el
    JavaScript y el contador de pagina que StoryWeaver mete en cada pagina."""
    t = re.sub(r"(?im)^\s*No media source currently available\.?\s*$", "", str(t or ""))
    t = _SIN_JS.sub("", t)
    return "\n\n".join(re.sub(r"\s+", " ", p).strip()
                       for p in re.split(r"\n\s*\n", t) if p.strip())


def identificador(fuente, f):
    if fuente == "storyweaver":
        return f"SWV{f['id']}"
    if fuente == "african_storybook":
        return "ASB" + re.match(r"(\d+)", f["archivo"]).group(1)
    if fuente == "letsread":
        # masterBookId es un UUID: sin guiones y en mayusculas, para que el id
        # sea solo letras y cifras como los demas y quepa en un nombre de archivo.
        return "LRD" + re.sub(r"[^0-9A-Za-z]", "", str(f["master"])).upper()
    return "VOA" + re.search(r"/(\d+)\.html$", f["url"]).group(1)


def atribucion(fuente, f):
    autores = ", ".join(a for a in (f.get("autores") or []) if a) or None
    if fuente == "storyweaver":
        return (f"«{f['titulo']}»{' de ' + autores if autores else ''}, publicado en "
                f"StoryWeaver ({f.get('editorial') or 'Pratham Books'}) con licencia CC BY 4.0: {f['url']}")
    if fuente == "african_storybook":
        return (f"«{f['titulo']}», African Storybook Project, licencia CC BY "
                f"(texto de global-asp/asp-source): https://www.africanstorybook.org/")
    if fuente == "letsread":
        ilustra = ", ".join(f.get("ilustradores") or [])
        return (f"«{f['titulo']}»{' de ' + autores if autores else ''}"
                f"{', ilustrado por ' + ilustra if ilustra else ''}, Let's Read "
                f"(The Asia Foundation), licencia {f.get('licencia')}: {f['url']}")
    return (f"«{f['titulo']}», VOA Learning English, dominio publico. "
            f"Credito: voanews.com / Voice of America. {f['url']}")


def temas(fuente, f):
    if fuente == "storyweaver":
        return f"Children's stories; StoryWeaver reading level {f.get('nivel_editor')}"
    if fuente == "african_storybook":
        nivel = f.get("nivel_editor")
        return "Children's stories; African Storybook" + (f" reading level {nivel}" if nivel else "")
    if fuente == "letsread":
        return f"Children's stories; Let's Read reading level {f.get('nivel_editor')}"
    return f"VOA Learning English; {f.get('seccion')}"


def cargar(tope):
    filas = []
    for fuente, ruta in FUENTES.items():
        if not ruta.exists():
            print(f"(sin {fuente})")
            continue
        n = 0
        for linea in ruta.open(encoding="utf-8"):
            f = json.loads(linea)
            if not f.get("al_catalogo", fuente == "storyweaver"):
                continue
            texto = parrafos(f.get("texto"))
            if not texto:
                continue
            nivel = f.get("nivel_editor")
            filas.append({
                "fuente": fuente, "id": identificador(fuente, f), "title": f.get("titulo") or "",
                "author": ", ".join(a for a in (f.get("autores") or []) if a)
                          or {"voa": "VOA Learning English"}.get(fuente, ""),
                "licencia": f.get("licencia") or ("CC BY 4.0" if fuente == "storyweaver" else ""),
                "atribucion": atribucion(fuente, f), "url": f.get("url") or "",
                "nivel_editor": None if nivel in (None, "", "None") else str(int(float(nivel))),
                "temas": temas(fuente, f), "texto": texto,
                "palabras": len(words(texto)),
                "_libre": licencia_libre(
                    f.get("licencia") or ("CC BY 4.0" if fuente == "storyweaver" else ""), f),
            })
            n += 1
            if tope and n >= tope:
                break
    df = pd.DataFrame(filas).drop_duplicates("id")
    # El mismo libro vive en varias bibliotecas: «The Red Raincoat» de Kiran
    # Kasturia esta en StoryWeaver (nivel 1) y en Let's Read (nivel 2), con el
    # mismo texto. En el catalogo del 12 de septiembre salia dos veces en el
    # buscador (61 filas de 1.812 repetian titulo y autor). Se queda uno por
    # titulo y autor normalizados, con la fuente de mas prioridad.
    prioridad = {f: i for i, f in enumerate(["storyweaver", "african_storybook", "letsread", "voa"])}
    df["_orden"] = df["fuente"].map(prioridad).fillna(9)
    df["_obra"] = (df["title"].astype(str).str.lower().str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()
                   + "|" + df["author"].astype(str).str.lower().str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip())
    antes = len(df)
    df = (df.sort_values(["_orden", "id"]).drop_duplicates("_obra", keep="first")
            .drop(columns=["_orden", "_obra"]))
    if antes != len(df):
        print(f"obras repetidas entre fuentes, fuera: {antes - len(df)}")
    malas = df[~df["_libre"].astype(bool)]
    if len(malas):
        sys.exit(f"NO CATALOGO NADA: {len(malas)} textos con licencia no libre llegaron "
                 f"hasta aqui, p. ej. {malas[['id', 'licencia']].head(3).to_dict('records')}")
    return df


def puntuar(df):
    p = Puntuador(str(RAIZ / "modelo_v4"))
    df["dificultad"], df["ventanas"], df["medida"] = float("nan"), 0, ""
    # 1) cada texto que se pueda puntuar solo
    for i, f in df.iterrows():
        if f["palabras"] < scoring.MIN_WORDS:
            continue
        try:
            r = p.puntuar(f["texto"])
            df.at[i, "dificultad"] = round(float(r.puntuacion), 4)
            df.at[i, "ventanas"] = len(scoring.fixed_blocks(scoring.normalize(f["texto"])))
            df.at[i, "medida"] = "texto"
        except ValueError:
            pass
    # 2) los que quedan, en bloques de su fuente y nivel
    resto = df[df["medida"] == ""].sort_values("id")
    for (_, _), g in resto.groupby(["fuente", resto["nivel_editor"].fillna("sin")]):
        idx, trozos, cuenta = [], [], 0
        for i, f in g.iterrows():
            idx.append(i)
            trozos.append(f["texto"])
            cuenta += f["palabras"]
            if cuenta >= BLOQUE:
                try:
                    r = p.puntuar("\n\n".join(trozos))
                    for j in idx:
                        df.at[j, "dificultad"] = round(float(r.puntuacion), 4)
                        df.at[j, "medida"] = "bloque"
                except ValueError:
                    pass
                idx, trozos, cuenta = [], [], 0
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tope", type=int, default=None)
    ap.add_argument("--sin-embeddings", action="store_true",
                    help="no calcular el .npy del externo (para probar rapido)")
    args = ap.parse_args()

    df = cargar(args.tope)
    print(f"textos libres: {len(df)} | por fuente: {df['fuente'].value_counts().to_dict()}")
    df = puntuar(df)
    fuera = df[df["dificultad"].isna()]
    df = df[df["dificultad"].notna()].copy()
    print(f"medidos: {len(df)} (texto {int((df['medida'] == 'texto').sum())}, "
          f"bloque {int((df['medida'] == 'bloque').sum())}) | sin medida, fuera: {len(fuera)}")

    df["nivel_cefr"] = df["dificultad"].map(lambda d: scoring.anchor_cefr(float(d) * 2.5))
    df["hook"], df["huella_texto"], df["downloads"], df["capitulos"] = "", "", 0, 1
    columnas = ["id", "title", "author", "hook", "huella_texto", "nivel_cefr", "downloads",
                "dificultad", "palabras", "ventanas", "capitulos", "temas",
                "fuente", "licencia", "atribucion", "url", "nivel_editor", "medida"]
    # LF siempre: en Windows pandas escribia CRLF, y la huella del archivo (y con
    # ella el nombre del .npy de embeddings) cambiaba segun la maquina.
    df[columnas].to_csv(CSV_SALIDA, index=False, lineterminator="\n")
    textos = df[["id", "title", "author", "licencia", "atribucion", "url", "texto"]].copy()
    textos["texto"] = textos["texto"] + "\n\n" + textos["atribucion"]
    textos.to_parquet(TEXTOS_SALIDA, index=False)
    print("letras:", df["nivel_cefr"].value_counts().sort_index().to_dict())
    print("->", CSV_SALIDA, "|", TEXTOS_SALIDA)

    # Los embeddings del externo, calculados AQUI y dejados en la raiz, que es
    # donde los recoge el despliegue. Sin este paso se calculaban en el primer
    # arranque del Space (2 vCPU) o en la primera busqueda, y en la cache, no
    # en la raiz. Los de Gutenberg ya estan y no se tocan.
    if not args.sin_embeddings:
        import shutil
        import catalogo as cat_mod
        cat = cat_mod.Catalogo(cat_mod.CSV_MEDIDO)
        emb = cat.embeddings
        nuevos = sorted(cat_mod.DIR_CACHE.glob("catalogo_emb_ext_*.npy"),
                        key=lambda p: p.stat().st_mtime)
        if not nuevos:
            sys.exit("No se genero el .npy del externo")
        ultimo = nuevos[-1]
        for viejo in RAIZ.glob("catalogo_emb_ext_*.npy"):
            if viejo.name != ultimo.name:
                viejo.unlink()
        shutil.copy2(ultimo, RAIZ / ultimo.name)
        print(f"embeddings: {emb.shape[0]} filas ({cat._n_propio} de Gutenberg + "
              f"{emb.shape[0] - cat._n_propio} externas) -> {ultimo.name}")


if __name__ == "__main__":
    main()
