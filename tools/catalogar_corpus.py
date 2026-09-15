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
eso -el filtro de prosa lo rechaza, o su grupo entero no llega a MIN_WORDS-, no
entra: sin medida no hay recomendacion. Los dos casos se cuentan por separado.

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

import ficha
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
# El gancho, en palabras, y lo que entra del texto en la huella de busqueda.
GANCHO_MIN, GANCHO_MAX = 12, 30
HUELLA_PALABRAS = 40
DIR_PARTES_EMB = CORPUS / "embeddings_externo"
PARTE_EMB = 1000
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


# Lo que se SIRVE al lector, limpio; lo que se MIDE, tal cual. La clave de
# `medir_corpus` es el contenido del texto: limpiar antes de medir cambiaria la
# clave de esos textos y habria que volver a medirlos (prueba como persona del
# 14 sep 2026: SWV138722 repetia paginas enteras y SWV229485 traia U+FEFF).
_FIN_DE_FRASE = re.compile(r"[.!?][\"”’')]*(?=\s|$)")


def _pagina_doble(parrafo):
    """La mitad de un parrafo que es la misma pagina dos veces seguidas, o None.
    Solo si cada mitad tiene al menos 12 palabras y dos frases: un estribillo de
    una frase repetida es del cuento, no del volcado."""
    w = parrafo.split()
    if len(w) < 24 or len(w) % 2:
        return None
    mitad = w[:len(w) // 2]
    if mitad != w[len(w) // 2:] or len(_FIN_DE_FRASE.findall(" ".join(mitad))) < 2:
        return None
    return " ".join(mitad)


def limpiar_para_servir(texto):
    """Sin U+FEFF, sin un parrafo identico al anterior y sin paginas duplicadas
    dentro de un parrafo. Las frases repetidas sueltas se quedan: en un cuento
    infantil la repeticion suele ser a proposito."""
    salida = []
    for p in re.split(r"\n\s*\n", str(texto or "").replace("﻿", "")):
        p = " ".join(p.split())
        if not p:
            continue
        p = _pagina_doble(p) or p
        if salida and salida[-1] == p:
            continue
        salida.append(p)
    return "\n\n".join(salida)


def textos_para_servir(df):
    """Las filas de corpus_abierto.parquet: el texto limpio y la atribucion al final."""
    textos = df[["id", "title", "author", "licencia", "atribucion", "url", "texto"]].copy()
    textos["texto"] = textos["texto"].map(limpiar_para_servir) + "\n\n" + textos["atribucion"]
    return textos


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


def _cuerpo(texto):
    """El texto en una linea, limpio y sin atribucion: de ahi salen gancho y huella."""
    return " ".join(ficha.para_medir(limpiar_para_servir(texto)).split())


def gancho(texto, minimo=GANCHO_MIN, maximo=GANCHO_MAX):
    """El arranque del texto, en frases enteras: hasta llegar a `minimo` palabras
    sin pasar de `maximo`. Si la primera frase ya pasa, sus `maximo` primeras
    palabras y «…». Sale en la tarjeta y entra en el vector de busqueda.

    Extractivo y local, sin OpenAI: son 15.367 textos y la busqueda no puede
    depender de una clave (auditoria cruzada de e6, 14 sep 2026: en los libres
    `hook` iba vacio y solo se indexaban titulo y autor)."""
    palabras_ = _cuerpo(texto).split()
    if not palabras_:
        return ""
    cuerpo = " ".join(palabras_[:maximo + 1])
    fin = 0
    for m in _FIN_DE_FRASE.finditer(cuerpo):
        n = len(cuerpo[:m.end()].split())
        if n > maximo:
            break
        fin = m.end()
        if n >= minimo:
            break
    if fin:
        return cuerpo[:fin]
    return " ".join(palabras_[:maximo]) + ("…" if len(palabras_) > maximo else "")


def huella_de_busqueda(temas_, texto, gancho_, palabras=HUELLA_PALABRAS):
    """Los temas y las `palabras` que siguen al gancho. De los temas se quita el
    «reading level N» del editor: no dice de que va el texto y es igual en miles
    de filas. Los temas van delante porque el modelo corta a 128 tokens."""
    tema = re.sub(r"\s*reading level \S+", "", str(temas_ or "")).strip()
    resto = _cuerpo(texto).split()[len(gancho_.rstrip("…").split()):]
    return (tema + ". " + " ".join(resto[:palabras])).strip()


def pistas_de_busqueda(df):
    """Rellena `hook` y `huella_texto`, que `Catalogo._texto_indexable` junta con
    titulo y autor para el vector de busqueda."""
    df["hook"] = df["texto"].map(gancho)
    df["huella_texto"] = [huella_de_busqueda(t, x, g)
                          for t, x, g in zip(df["temas"], df["texto"], df["hook"])]
    return df


def embeddings_por_partes(cat, carpeta=DIR_PARTES_EMB, parte=PARTE_EMB, salida=print):
    """Los embeddings del externo de `cat`, de `parte` en `parte` filas, cada parte
    guardada en disco al acabar: si se corta, la siguiente ejecucion sigue por la
    primera que falte. Devuelve (matriz, nombre del .npy que busca el catalogo)."""
    import numpy as np
    textos, huella = cat._externo_indexable()
    nombre = f"catalogo_emb_ext_{huella}.npy"
    destino = Path(carpeta) / huella
    destino.mkdir(parents=True, exist_ok=True)
    trozos = []
    for k, i in enumerate(range(0, len(textos), parte)):
        lote = textos[i:i + parte]
        ruta = destino / f"parte_{k:04d}.npy"
        if ruta.exists():
            emb = np.load(ruta)
            if len(emb) == len(lote):
                trozos.append(emb)
                continue
        emb = np.asarray(cat._modelo_emb().encode(lote, normalize_embeddings=True, batch_size=64,
                                                  show_progress_bar=False), dtype=np.float32)
        temporal = ruta.with_suffix(".tmp.npy")
        np.save(temporal, emb)
        temporal.replace(ruta)
        trozos.append(emb)
        salida(f"  embeddings: {i + len(lote)} de {len(textos)}")
    return np.vstack(trozos), nombre


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
    # Los 48 libros de StoryWeaver bajados por popularidad
    # (auditoria/storyweaver_sesgadas_48.txt) solo se apartan al VALIDAR: son
    # libres y entran al catalogo como los demas (central, 14 sep 2026).
    filas = []
    for fuente, ruta in FUENTES.items():
        if not ruta.exists():
            print(f"(sin {fuente})")
            continue
        n = 0
        for linea in ruta.open(encoding="utf-8"):
            f = json.loads(linea)
            # StoryWeaver no trae `al_catalogo`: entra solo si su registro dice
            # una licencia libre. Antes se le presumia «CC BY 4.0» si faltaba, y
            # `licencia_libre` recibia la presumida (auditoria cruzada de e6, M3).
            al_catalogo = f.get("al_catalogo")
            if al_catalogo is None and fuente == "storyweaver":
                al_catalogo = licencia_libre(f.get("licencia"), f)
            if not al_catalogo:
                continue
            texto = parrafos(f.get("texto"))
            if not texto:
                continue
            nivel = f.get("nivel_editor")
            filas.append({
                "fuente": fuente, "id": identificador(fuente, f), "title": f.get("titulo") or "",
                "author": ", ".join(a for a in (f.get("autores") or []) if a)
                          or {"voa": "VOA Learning English"}.get(fuente, ""),
                "licencia": f.get("licencia") or "",
                "atribucion": atribucion(fuente, f), "url": f.get("url") or "",
                "nivel_editor": None if nivel in (None, "", "None") else str(int(float(nivel))),
                "temas": temas(fuente, f), "texto": texto,
                "palabras": len(words(texto)),
                "_libre": licencia_libre(f.get("licencia"), f),
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
    """Mide con tools/medir_corpus.py: el mismo reparto (textos solos y bloques de
    cortos y rechazados por fuente y nivel), pero reanudable y reutilizando lo ya
    medido por clave de contenido. Si falta algo, lo mide aqui mismo."""
    sys.path.insert(0, str(RAIZ / "tools"))
    import medir_corpus
    df, _ = medir_corpus.medir(df)
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
    cola = len(df.attrs.get("cola_sin_medir", []))
    df = df[df["dificultad"].notna()].copy()
    print(f"medidos: {len(df)} (texto {int((df['medida'] == 'texto').sum())}, "
          f"bloque {int((df['medida'] == 'bloque').sum())}) | sin medida, fuera: {len(fuera)} "
          f"({len(fuera) - cola} por el filtro de prosa, {cola} en grupos de menos de "
          f"{scoring.MIN_WORDS} palabras)")

    df["nivel_cefr"] = df["dificultad"].map(lambda d: scoring.anchor_cefr(float(d) * 2.5))
    df["downloads"], df["capitulos"] = 0, 1
    pistas_de_busqueda(df)
    columnas = ["id", "title", "author", "hook", "huella_texto", "nivel_cefr", "downloads",
                "dificultad", "palabras", "ventanas", "capitulos", "temas",
                "fuente", "licencia", "atribucion", "url", "nivel_editor", "medida"]
    # LF siempre: en Windows pandas escribia CRLF, y la huella del archivo (y con
    # ella el nombre del .npy de embeddings) cambiaba segun la maquina.
    df[columnas].to_csv(CSV_SALIDA, index=False, lineterminator="\n")
    textos_para_servir(df).to_parquet(TEXTOS_SALIDA, index=False)
    print("letras:", df["nivel_cefr"].value_counts().sort_index().to_dict())
    print("->", CSV_SALIDA, "|", TEXTOS_SALIDA)

    # Los embeddings del externo, calculados AQUI y dejados en la raiz, que es
    # donde los recoge el despliegue. Sin este paso se calculaban en el primer
    # arranque del Space (2 vCPU) o en la primera busqueda, y en la cache, no
    # en la raiz. Los de Gutenberg ya estan y no se tocan.
    # Por partes en CPU (corpus_graduado/embeddings_externo/<huella>/), con el
    # nombre que buscara `Catalogo.embeddings`, y en la cache y en la raiz.
    if not args.sin_embeddings:
        import numpy as np
        import catalogo as cat_mod
        cat = cat_mod.Catalogo(cat_mod.CSV_MEDIDO)
        ext, nombre = embeddings_por_partes(cat)
        for carpeta in (cat_mod.DIR_CACHE, RAIZ):
            for viejo in carpeta.glob("catalogo_emb_ext_*.npy"):
                if viejo.name != nombre:
                    viejo.unlink()
            np.save(carpeta / nombre, ext)
        emb = cat.embeddings
        print(f"embeddings: {emb.shape[0]} filas ({cat._n_propio} de Gutenberg + "
              f"{ext.shape[0]} externas) -> {nombre}")


if __name__ == "__main__":
    main()
