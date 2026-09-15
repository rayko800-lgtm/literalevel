"""Catalogo de libros y busqueda semantica (paso 2 del recorrido).

La app anterior guardaba los embeddings en un .npy suelto y, si su longitud no
coincidia con el CSV, la busqueda devolvia vacio sin explicar por que. Ese era
el fallo de "busco realismo y no sale nada".

Aqui los embeddings se calculan a partir del propio CSV y se cachean con una
huella del archivo: si el catalogo cambia, la cache se invalida sola y se
recalcula. Es imposible que queden desincronizados.
"""
from __future__ import annotations
import difflib, hashlib, os, re, unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Solo por `miles()`, el separador de miles en espanol. Es de presentacion y
# vive alli porque `ui` y este modulo lo necesitan los dos; `ficha` no arrastra
# nada pesado (re, dataclasses y scoring, que carga torch en perezoso).
import config
import ficha

RAIZ = Path(__file__).resolve().parent.parent
# El catalogo MEDIDO -53.179 libros de Project Gutenberg, el v4 sobre el libro
# entero- si esta; si no, el heredado. Asi un clon sin los archivos del catalogo
# medido sigue arrancando igual que antes.
CSV_MEDIDO = RAIZ / "catalogo_medido.csv"
CSV_HEREDADO = RAIZ / "catalogo_recomendaciones.csv"
CSV_POR_DEFECTO = CSV_MEDIDO if CSV_MEDIDO.exists() else CSV_HEREDADO
# La curva por capitulo del catalogo medido, junto a su CSV.
NOMBRE_CAPITULOS = "capitulos_medidos.parquet"
# Los corpus externos de licencia libre (StoryWeaver, African Storybook, VOA...),
# medidos por el v4 con tools/catalogar_corpus.py. Van en archivos APARTE, junto
# al CSV principal, por dos razones: los embeddings de los 53.179 libros de
# Gutenberg ya estan calculados y publicados (82 MB) y no hay que recodificarlos
# por anadir filas; y un clon sin estos archivos sigue arrancando como antes.
NOMBRE_EXTERNO = "catalogo_externo.csv"
NOMBRE_TEXTOS_ABIERTOS = "corpus_abierto.parquet"

# El catalogo NO se filtra por contenido: se avisa en la ficha (documento.md,
# «uso responsable»). La lista es curada a mano y la revisa Miguel; nada
# automatico, que una lista de palabras senalaria obras por su vocabulario y no
# por lo que dicen. Un titulo con aviso sigue saliendo, pero no encabeza la
# recomendacion por nivel: baja detras de los PRIMEROS_SIN_AVISO primeros.
NOMBRE_AVISOS = "avisos_contenido.csv"
PRIMEROS_SIN_AVISO = 5
# Textos libres en la recomendacion por nivel (decision de Miguel, 14 sep 2026):
# no tienen descargas de Gutenberg, y ordenados por popularidad salian del puesto
# 20 en adelante en A2 y ninguno en B1. Si hay libres en la franja, uno de cada
# CADA_CUANTOS_LIBRE puestos es suyo (el 2, el 5, el 8...); el resto, por descargas.
CADA_CUANTOS_LIBRE = 3
# Correcciones de filas medidas que salieron mal en el precalculo, aplicadas al
# cargar: el CSV grande no se toca porque su huella indexa los 82 MB de
# embeddings. Cada fila lleva su motivo. Ver la prueba final del 13 sep 2026:
# PG2242 (A Midsummer Night's Dream, First Folio) media 0,697 en el catalogo y
# 1,8 releida por el mismo camino; las otras 32 obras del Folio, 1,54-1,81.
NOMBRE_CORRECCIONES = "correcciones_catalogo.csv"

# Lo que no es un libro para leer, aunque venga de Gutenberg: indices,
# catalogos, bibliografias, directorios. Medido el 12 de septiembre de 2026: 79
# de los 599 libros A1-B1 del catalogo medido eran esto -los *CIA World
# Factbook*, listas de oficinas de correos, tablas de constantes- y puntuan
# "facil" precisamente porque son listas. NO se borran del CSV: los embeddings
# van alineados fila a fila y borrar una obligaria a recodificar el catalogo.
# Se excluyen al recomendar y al buscar.
_NO_ES_LECTURA_TEMAS = re.compile(
    r"(?i)\bindexes\b|\bcatalogs\b|bibliograph|\bdirectories\b|gazetteers|almanacs")
# Los indices enlazados de Gutenberg no siempre llevan el tema «Indexes»: *The
# Fairy Books of Andrew Lang: A Project Gutenberg Linked Index to All Stories*
# viene con «Fairy tales; Folklore», puntua A2 por ser una lista de titulos y
# salia recomendado por nivel (prueba final del 13 de septiembre de 2026). «an
# index to all» y no «an index to the»: la segunda tumbaba *History of the Jews,
# Vol. 6*, que es un libro con su indice al final.
_NO_ES_LECTURA_TITULO = re.compile(
    r"(?i)index of the project gutenberg|project gutenberg (?:works|index|catalog)"
    r"|linked index|index for works of|\ban index to all\b|hyperlinks to all chapters"
    r"|world factbook|^list of |\bdirectory\b|\bconstants\b")

# Y para RECOMENDAR por nivel, ademas, que sea literatura segun sus temas de
# Gutenberg. Medido el 12 de septiembre de 2026: tras quitar indices y
# catalogos, entre los libros "mas faciles" seguian un mapa de tarifas de taxi
# de Londres, problemas de ajedrez y una tabla de numeros de Bernoulli. Es una
# app de lectura literaria: por nivel se ofrecen ficcion, cuentos, lecturas
# escolares, poesia y teatro (290 libros A1-B1 y 1.676 B2 en el catalogo
# medido). El BUSCADOR no filtra por esto: quien escribe un titulo sabe lo que
# busca.
_LITERARIO = re.compile(
    r"(?i)fiction|\btales?\b|stories|\breaders\b|juvenile|poetry|poems|drama|\bplays\b"
    r"|fables|legends|folklore|fairy|nursery rhymes|literature|novels?\b|romance")
# La cache de embeddings del catalogo. Sale de `config.dir_datos()` como las
# demas rutas de escritura: clavada a `~/.literalevel` se quedaba en el disco
# EFIMERO del Space, y cada reinicio recodificaba los 1.197 libros con el
# modelo multilingue. Medido: 56,9 s en un Ryzen de 12 hilos, y el Space tiene
# 2 vCPU. Es la espera de la primera busqueda, que en el video sale en camara.
DIR_CACHE = config.dir_datos()

# Multilingue a proposito: el usuario describe lo que quiere leer en espanol
# ("algo con mucho suspenso"), y el catalogo esta en ingles.
MODELO_EMB = "paraphrase-multilingual-MiniLM-L12-v2"

NIVELES = ["A1", "A2", "B1", "B2", "C1", "C2"]
# Escala publica 0..2 aproximada de cada ancla, para comparar el nivel del
# lector (perfil.py) con el nivel etiquetado de cada libro.
NIVEL_A_PUNTUACION = {n: round(i * 0.4, 2) for i, n in enumerate(NIVELES)}


def _medida_de_fila(f) -> str:
    """La columna `medida` de una fila: "texto" o "bloque" en los corpus libres;
    en Gutenberg no existe o es NaN, y eso no es ninguna de las dos."""
    m = f.get("medida", "")
    return m if m in ("texto", "bloque") else ""


@dataclass
class Libro:
    id: str
    titulo: str
    autor: str
    nivel: str
    gancho: str
    descargas: int
    similitud: float = 0.0
    afinidad: float = 0.0
    dificultad: float | None = None     # medida por el v4; None si es heredada
    aviso_contenido: str = ""           # nota de avisos_contenido.csv; "" si no hay
    medida: str = ""                    # "texto", "bloque" (corpus libres) o "" (Gutenberg)

    @property
    def medido_en_bloque(self) -> bool:
        """Un texto libre corto medido dentro de un bloque de su fuente y nivel:
        su dificultad es la del bloque, no la suya (prueba como persona, 14 sep)."""
        return self.medida == "bloque"

    @property
    def puntuacion_nivel(self) -> float:
        if self.dificultad is not None:
            return self.dificultad
        return NIVEL_A_PUNTUACION.get(self.nivel, 1.0)

    @property
    def url_gutenberg(self) -> str:
        """El enlace a Gutenberg, y solo si el libro es DE Gutenberg.

        Antes se sacaban los digitos de cualquier id, asi que un libro de
        StoryWeaver con id `SWgdlgdl201` acababa enlazando al ebook 201 de
        Gutenberg, que es otra obra completamente distinta. Un enlace a un
        libro equivocado es peor que no tener enlace.
        """
        ident = str(self.id).upper()
        if not ident.startswith("PG"):
            return ""
        num = "".join(c for c in ident if c.isdigit())
        return f"https://www.gutenberg.org/ebooks/{num}" if num else ""


def _ruta_local(nombre: str) -> str:
    """La carpeta ya descargada del modelo, o su nombre si no esta.

    `SentenceTransformer("nombre/modelo")` resuelve ese nombre contra el Hub
    en CADA carga, y eso cuesta segundos aunque el modelo lleve meses en
    disco. Pasarle la ruta local se los ahorra: medido, 2,9 s -> 0,22 s en
    MiniLM-L6 y 5,8 s -> 2,7 s en el multilingue del catalogo.

    Si no esta cacheado -maquina nueva, primer arranque de un despliegue- se
    devuelve el nombre y se descarga como siempre. Nunca falla por esto.
    """
    completo = nombre if "/" in nombre else f"sentence-transformers/{nombre}"
    try:
        from huggingface_hub import snapshot_download
        return snapshot_download(completo, local_files_only=True)
    except Exception:
        return nombre


def _huella(ruta: Path) -> str:
    """Identifica la version exacta del CSV por su CONTENIDO, no por su fecha.

    Antes entraba `st_mtime_ns` en la huella. Eso vale en la maquina donde se
    generaron los embeddings y en ninguna otra: un clon nuevo del repositorio,
    o un despliegue, tienen otra fecha de modificacion, asi que el nombre del
    `.npy` no coincidiria nunca y habria que recodificar los 1197 libros. Son
    **46,7 segundos medidos**, y en un Space que se duerme por inactividad se
    pagan en cada despertar.

    El sha256 del CSV entero cuesta 0,001 s sobre 870 KB. La fecha no compraba
    nada y costaba tres cuartos de minuto por arranque en frio.
    """
    h = hashlib.sha256(str(ruta.stat().st_size).encode())
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()[:16]


_PARECIDO_NOMBRE = 0.75     # "chejov" vs "chekhov" da 0.77: por debajo
                            # de esto ya son nombres distintos
_PESO_NOMBRE = 0.85         # cuanto vale un nombre acertado frente al tema
# Al buscar con «Ordenar por mi nivel», el nivel ordena solo DENTRO de lo
# relevante: lo que queda a MARGEN_RELEVANCIA del mejor parecido. Medido el 14
# sep 2026 sobre el catalogo real: «amor» deja 3 filas dentro de 0,05, «love»
# 469, «detectives en Londres» 109. Y un titulo acertado (a MARGEN_NOMBRE del
# mejor acierto de nombre) va siempre delante, este del nivel que este.
MARGEN_RELEVANCIA = 0.05
MARGEN_NOMBRE = 0.02
# Un nombre acertado solo impulsa si alguno de sus libros se parece de verdad a lo
# pedido: el mejor parecido SEMANTICO entre las filas con nombre tiene que quedar a
# este margen del mejor parecido semantico del catalogo. Si no, son nombres que se
# escriben parecido y nada mas, y no fijan la ventana de relevancia ni van delante.
# Medido el 15 sep 2026 (mejor semantico menos mejor semantico con nombre): chejov
# 0,00, Jane Austen 0,00, A Midsummer Night's Dream 0,00, dostoyevski 0,03, «libros
# de dickens sobre huerfanos» 0,04, Frankenstein 0,06 y Little Black Sambo 0,13, el
# mayor legitimo; «amor» 0,32 («Amory», «Armour»: apellidos, nada de amor).
MARGEN_SEMANTICO_NOMBRE = 0.20
# Una palabra suelta en espanol casi no se parece a su tema en este modelo («amor»
# frente a «love», 0,3). Se incrusta tambien dentro de estas frases y vale el mejor
# parecido. Medido el 15 sep 2026 con amor, miedo, escuela, perros, dragones,
# piratas, fantasmas y amistad, 12 resultados cada una: resultados sobre el tema
# 76 de 96 con la palabra sola, 88 con «historias de» y 88 con «libros sobre»
# («cuentos de» 83, «a story about» 37). «amor» pasa de 4 a 11 de 12. Kaikki no
# sirve para traducir: solo trae cabeceras en ingles.
FRASES_PALABRA_SUELTA = ("historias de {}", "libros sobre {}")
# Un titulo solo cuenta como nombre si TODAS las palabras de la consulta estan en
# el (a este parecido cada una). Una sola palabra parecida («Amour», «Amora» para
# «amor») ya no rescata nada; los apellidos si admiten el parecido de
# _PARECIDO_NOMBRE, que es lo que encuentra a Chekhov escribiendo «chejov».
_PARECIDO_TITULO = 0.9
# Con el nombre ENTERO de un autor (apellido y nombre de pila), sus obras van delante
# de los libros SOBRE él: «Jane Austen» sacaba primero «Jane Austen and her works» y
# «Memoir of Jane Austen» (título entero, 0,857), y Emma, Persuasion y Pride and
# Prejudice quedaban detrás (solo el apellido, 0,793), empatadas con Sidney Austen y
# con «Calamity Jane» (prueba como persona de e6, 15 sep 2026).
_EXTRA_AUTOR_COMPLETO = 0.02
# Palabras de rol del campo de autor de Gutenberg, que no son nombres.
_NO_SON_NOMBRES = frozenset({"illustrator", "editor", "translator", "contributor", "various",
                             "anonymous", "unknown", "compiler", "commentator", "author"})
# Los textos libres que no son lectura en ingles (tools/marcar_no_lectura.py).
NOMBRE_NO_LECTURA = "no_lectura_externo.csv"


def _normalizar(t: str) -> str:
    """Minusculas y sin acentos, para comparar nombres entre idiomas."""
    t = unicodedata.normalize("NFD", str(t).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _fichas(textos: list[str]) -> list[set[str]]:
    return [{p for p in re.split(r"[^a-z0-9]+", _normalizar(t)) if len(p) >= 4}
            for t in textos]


def _similitud_nombres(consulta: str, fichas: list[set[str]]) -> np.ndarray:
    """Cuanto se parece la consulta al titulo o al autor, letra a letra.

    La busqueda semantica entiende de temas, no de ortografia. Un nombre
    transliterado a la espanola -"dostoyevski" por "Dostoyevsky", "Chejov"
    por "Chekhov"- no se parece nada al original en el espacio de embeddings,
    y quien escribe el nombre de un autor espera encontrar sus libros. Esto
    lo rescata sin estorbar a las busquedas por tema: solo puntua cuando hay
    un parecido casi exacto con alguna palabra del titulo o del autor.
    """
    pistas = [p for p in re.split(r"[^a-z0-9]+", _normalizar(consulta)) if len(p) >= 4]
    if not pistas:
        return np.zeros(len(fichas), dtype=np.float32)
    fuera = np.zeros(len(fichas), dtype=np.float32)
    cache: dict[tuple[str, str], float] = {}
    for i, ficha in enumerate(fichas):
        mejor, cubiertas = 0.0, 0
        for pista in pistas:
            mejor_pista = 0.0
            for palabra in ficha:
                # Descarte barato antes de la comparacion cara: longitudes muy
                # distintas o inicial distinta nunca dan un parecido alto.
                if abs(len(palabra) - len(pista)) > 3 or palabra[0] != pista[0]:
                    continue
                clave = (pista, palabra)
                r = cache.get(clave)
                if r is None:
                    r = difflib.SequenceMatcher(None, pista, palabra).ratio()
                    cache[clave] = r
                if r > mejor_pista:
                    mejor_pista = r
            mejor = max(mejor, mejor_pista)
            cubiertas += mejor_pista >= _PARECIDO_NOMBRE
        # La mejor palabra sigue mandando -una sola pista acertada rescata un
        # autor transliterado aunque la consulta traiga mas palabras-, pero
        # cuantas mas palabras de la consulta casan, mas vale. Sin esto,
        # «Little Black Sambo» empataba a 0,85 con cinco titulos que solo
        # comparten «Black» y el libro no salia (prueba final, 13 sep 2026).
        fuera[i] = mejor * (1.0 - 0.15 * (1.0 - cubiertas / len(pistas)))
    return fuera


def _apellidos(autor) -> str:
    """Los apellidos de un campo de autor: lo que va antes de la primera coma de
    cada autor («Dostoyevsky, Fyodor, 1821-1881; Garnett, Constance» da
    «Dostoyevsky Garnett»). Sin coma -los textos libres, «Silvia Vie»- cuenta el
    nombre entero. «Fenn, Amor» da «Fenn»: un nombre de pila no rescata."""
    if autor is None or (isinstance(autor, float) and np.isnan(autor)):
        return ""
    return " ".join(a.split(",")[0] for a in str(autor).split(";"))


def _nombre_entero(autor) -> str:
    """Apellidos y nombres de pila de todos los autores del campo, sin las fechas."""
    if autor is None or (isinstance(autor, float) and np.isnan(autor)):
        return ""
    return re.sub(r"[\d?]+", " ", str(autor))


def _vocabulario_de_nombres(autores) -> set[str]:
    """Todas las palabras de nombre (apellidos y de pila) que hay en el campo de autor."""
    vocabulario: set[str] = set()
    for ficha in _fichas([_nombre_entero(a) for a in autores]):
        vocabulario |= ficha
    return {p for p in vocabulario if p.isalpha()} - _NO_SON_NOMBRES


def _titulo_completo(consulta: str, fichas: list[set[str]]) -> np.ndarray:
    """La media del parecido de cada palabra de la consulta con el titulo, solo si
    TODAS pasan de _PARECIDO_TITULO; si no, 0."""
    pistas = [p for p in re.split(r"[^a-z0-9]+", _normalizar(consulta)) if len(p) >= 4]
    fuera = np.zeros(len(fichas), dtype=np.float32)
    if not pistas:
        return fuera
    cache: dict[tuple[str, str], float] = {}
    for i, ficha in enumerate(fichas):
        if not ficha:
            continue
        suma = 0.0
        for pista in pistas:
            mejor = 0.0
            for palabra in ficha:
                if abs(len(palabra) - len(pista)) > 2 or palabra[0] != pista[0]:
                    continue
                r = cache.get((pista, palabra))
                if r is None:
                    r = cache[(pista, palabra)] = difflib.SequenceMatcher(None, pista, palabra).ratio()
                mejor = max(mejor, r)
            if mejor < _PARECIDO_TITULO:
                break
            suma += mejor
        else:
            fuera[i] = suma / len(pistas)
    return fuera


def _dificultad_de(fila) -> float | None:
    """La dificultad medida de una fila del catalogo, o None si no la hay."""
    try:
        v = float(fila.get("dificultad"))
    except (TypeError, ValueError, AttributeError):
        return None
    return None if np.isnan(v) else v


class Catalogo:
    def __init__(self, ruta_csv: str | os.PathLike = CSV_POR_DEFECTO):
        self.ruta = Path(ruta_csv)
        if not self.ruta.exists():
            raise FileNotFoundError(f"No encuentro el catálogo en {self.ruta}")
        self.df = pd.read_csv(self.ruta).fillna({"hook": "", "huella_texto": "",
                                                 "author": "", "nivel_cefr": ""})
        self._n_propio = len(self.df)
        # Las filas de los corpus externos se ANADEN AL FINAL: asi los
        # embeddings del CSV principal siguen alineados fila a fila con sus
        # libros, y los de las filas externas van en su propio .npy.
        self.ruta_externo = self.ruta.with_name(NOMBRE_EXTERNO)
        if self.ruta_externo.exists():
            try:
                ext = pd.read_csv(self.ruta_externo, dtype={"nivel_editor": str}).fillna(
                    {"hook": "", "huella_texto": "", "author": "", "nivel_cefr": ""})
                ext = ext[~ext["id"].astype(str).isin(set(self.df["id"].astype(str)))]
                if len(ext):
                    self.df = pd.concat([self.df, ext], ignore_index=True, sort=False)
            except Exception:
                self.ruta_externo = None        # un externo roto no tumba el catalogo
        else:
            self.ruta_externo = None
        self._correcciones = self._aplicar_correcciones()
        self._avisos = self._leer_avisos()
        self.df["aviso_contenido"] = (self.df["id"].astype(str).str.upper()
                                      .map(self._avisos).fillna(""))
        # El catalogo MEDIDO trae `dificultad`: la escala publica 0..2 del v4
        # sobre el libro entero. El heredado solo trae `nivel_cefr`, una letra
        # que predijo un modelo v1 sobre ~190 palabras. Si hay medida, manda la
        # medida, y la letra se deriva de ella con la MISMA regla que el resto
        # de la app (`scoring.anchor_cefr`): un libro no puede salir con dos
        # letras segun quien pregunte. Y la letra hace falta aunque haya
        # numero, porque la interfaz ordena por `ANCHORS.index(libro.nivel)`
        # y una cadena vacia ahi revienta.
        if self.medido:
            import scoring
            self.df["dificultad"] = pd.to_numeric(self.df["dificultad"], errors="coerce")
            con = self.df["dificultad"].notna()
            self.df.loc[con, "nivel_cefr"] = self.df.loc[con, "dificultad"].map(
                lambda d: scoring.anchor_cefr(float(d) * 2.5))
        self._emb: np.ndarray | None = None
        self._modelo = None
        self._fichas: list[set[str]] | None = None

    # --- embeddings ---------------------------------------------------
    def _texto_indexable(self) -> list[str]:
        """Lo que se indexa: titulo, autor y las pistas de contenido. En
        Gutenberg `hook` va vacio y `huella_texto` son sus temas. En los textos
        libres, desde el 15 sep, `hook` es el arranque del texto y `huella_texto`
        sus temas y lo que sigue (tools/catalogar_corpus.py). Hasta entonces los
        dos iban vacios y el vector de los 15.357 salia solo de «titulo. autor.»
        (auditoria cruzada de e6). El modelo de embeddings corta a 128 tokens."""
        d = self.df
        return (d["title"].astype(str) + ". " + d["author"].astype(str) + ". "
                + d["hook"].astype(str) + " " + d["huella_texto"].astype(str)).tolist()

    @property
    def embeddings(self) -> np.ndarray:
        if self._emb is not None:
            return self._emb
        textos = self._texto_indexable()
        n = getattr(self, "_n_propio", len(self.df))
        emb = self._embeddings_de("catalogo_emb_", _huella(self.ruta), textos[:n])
        externo = getattr(self, "ruta_externo", None)
        if externo is not None and len(textos) > n:
            # El externo en su propio archivo: anadir o cambiar un corpus
            # recodifica sus filas, no las 53.179 de Gutenberg.
            textos_ext, huella = self._externo_indexable()
            ext = self._embeddings_de("catalogo_emb_ext_", huella, textos_ext)
            emb = np.vstack([emb, ext])
        self._emb = emb
        return emb

    def _externo_indexable(self) -> tuple[list[str], str]:
        """Los textos indexables del externo y la huella que nombra su `.npy`
        (`catalogo_emb_ext_<huella>.npy`). tools/catalogar_corpus.py la usa para
        calcularlo por partes con el mismo nombre que buscara `embeddings`.

        La huella sale de las filas que DE VERDAD quedan tras filtrar las que ya
        estaban en el principal, no del archivo externo: con el mismo externo y
        otro principal pueden quedar otras filas con la misma longitud, y la
        cache devolvia los vectores de otros libros (auditoria de Codex del 12 de
        septiembre de 2026)."""
        textos = self._texto_indexable()
        n = getattr(self, "_n_propio", len(self.df))
        ids_ext = self.df["id"].astype(str).tolist()[n:]
        h = hashlib.sha256("\x1f".join(ids_ext + textos[n:]).encode("utf-8"))
        return textos[n:], h.hexdigest()[:16]

    def _embeddings_de(self, prefijo: str, huella: str, textos: list[str]) -> np.ndarray:
        DIR_CACHE.mkdir(parents=True, exist_ok=True)
        nombre = f"{prefijo}{huella}.npy"
        cache = DIR_CACHE / nombre
        # Y TAMBIEN en la raiz del repositorio. Ahi es donde viaja el `.npy`
        # que se sube al Space, y hasta hoy no lo leia nadie: `embeddings`
        # solo miraba `DIR_CACHE`, que en el Space es otra carpeta. Con esto,
        # el primer arranque no recodifica nada y ademas se guarda la copia en
        # la raiz configurable, que si sobrevive al reinicio.
        for candidata in (cache, RAIZ / nombre):
            if candidata.exists():
                emb = np.load(candidata)
                if len(emb) == len(textos):       # cinturon y tirantes
                    if candidata != cache:
                        try:
                            np.save(cache, emb)
                        except OSError:
                            pass          # sin sitio donde copiarla, da igual
                    return emb
        emb = self._modelo_emb().encode(textos, normalize_embeddings=True,
                                        batch_size=64, show_progress_bar=False)
        emb = np.asarray(emb, dtype=np.float32)
        np.save(cache, emb)
        # Solo se borran las versiones viejas DEL MISMO archivo. El glob de los
        # de Gutenberg ("catalogo_emb_*") tambien casa con los del externo
        # ("catalogo_emb_ext_*"): sin esta guarda, recalcular Gutenberg borraba
        # los embeddings del externo y el siguiente arranque los recodificaba.
        for viejo in DIR_CACHE.glob(f"{prefijo}*.npy"):
            if viejo != cache and (prefijo != "catalogo_emb_" or not viejo.name.startswith("catalogo_emb_ext_")):
                viejo.unlink()             # el catalogo cambio: sobra
        return emb

    def _modelo_emb(self):
        if self._modelo is None:
            from sentence_transformers import SentenceTransformer
            self._modelo = SentenceTransformer(_ruta_local(MODELO_EMB))
        return self._modelo

    def _aplicar_correcciones(self) -> dict[str, dict]:
        """Lee correcciones_catalogo.csv y fija su dificultad en `df`.

        Devuelve {id: {dificultad, min, max, motivo}} para `capitulos_de`. Sin
        archivo, o con uno roto, no cambia nada: una correccion mala no puede
        tumbar el catalogo."""
        ruta = Path(self.ruta).with_name(NOMBRE_CORRECCIONES)
        if not ruta.exists() or "dificultad" not in self.df.columns:
            return {}
        try:
            tabla = pd.read_csv(ruta, dtype={"id": str})
        except Exception:
            return {}
        arreglos = {}
        ids = self.df["id"].astype(str).str.upper()
        for _, f in tabla.iterrows():
            pid = str(f.get("id", "")).strip().upper()
            try:
                dif = float(f["dificultad"])
            except (TypeError, ValueError, KeyError):
                continue
            if not pid or np.isnan(dif) or not (0.0 <= dif <= 2.0):
                continue
            def _num(k):
                try:
                    v = float(f.get(k))
                    return None if np.isnan(v) else round(v, 3)
                except (TypeError, ValueError):
                    return None
            arreglos[pid] = {"dificultad": round(dif, 3), "min": _num("min"), "max": _num("max"),
                             "motivo": str(f.get("motivo", "") or "")}
            self.df.loc[ids == pid, "dificultad"] = round(dif, 3)
        return arreglos

    def _leer_avisos(self) -> dict[str, str]:
        """{id en mayusculas: nota en espanol} de avisos_contenido.csv, o {}."""
        ruta = Path(self.ruta).with_name(NOMBRE_AVISOS)
        if not ruta.exists():
            return {}
        try:
            tabla = pd.read_csv(ruta, dtype=str).fillna("")
        except Exception:
            return {}
        return {str(f["id"]).strip().upper(): str(f["nota_es"]).strip()
                for _, f in tabla.iterrows()
                if str(f.get("id", "")).strip() and str(f.get("nota_es", "")).strip()}

    def medida_de(self, id_libro) -> str:
        """"texto" o "bloque" para un texto libre del catalogo; "" si no es libre
        o no esta. Para la ficha, que se abre por id y no trae la fila."""
        if getattr(self, "_medidas", None) is None:
            d = getattr(self, "df", None)
            if d is None or "medida" not in d.columns:
                self._medidas = {}
            else:
                self._medidas = {str(i).strip().upper(): m for i, m in zip(d["id"], d["medida"])
                                 if m in ("texto", "bloque")}
        return self._medidas.get(str(id_libro or "").strip().upper(), "")

    def aviso_de(self, id_libro) -> str | None:
        """La nota de aviso de contenido de un libro del catalogo, o None."""
        return getattr(self, "_avisos", {}).get(str(id_libro or "").strip().upper()) or None

    @property
    def medido(self) -> bool:
        """¿Trae este catalogo dificultad medida por el v4?

        Propiedad y no atributo fijado en `__init__`, a proposito: hay pruebas y
        caminos que montan un `Catalogo` sin pasar por el constructor, y un
        atributo que solo existe si se paso por ahi revienta con AttributeError.
        Lo encontro `pruebas_extremas.py` la primera vez que se cableo esto."""
        d = getattr(self, "df", None)
        return (d is not None and "dificultad" in d.columns
                and bool(pd.to_numeric(d["dificultad"], errors="coerce").notna().any()))

    @property
    def _excluidos(self) -> np.ndarray:
        """Marca las filas que no son libros para leer (ver _NO_ES_LECTURA_*).

        Solo el catalogo medido trae `temas`; el heredado no se toca."""
        if getattr(self, "_excl", None) is None:
            d = self.df
            if "temas" in d.columns:
                t = d["title"].fillna("").astype(str)
                s = d["temas"].fillna("").astype(str)
                self._excl = (t.str.contains(_NO_ES_LECTURA_TITULO)
                              | s.str.contains(_NO_ES_LECTURA_TEMAS)).to_numpy()
            else:
                self._excl = np.zeros(len(d), dtype=bool)
            # Las filas sin titulo (89 de Gutenberg el 15 sep 2026): su vector sale
            # de «nan. nan.» y encabezaba busquedas como «amor» con 0,61.
            titulo = d["title"] if "title" in d.columns else pd.Series([""] * len(d))
            sin_titulo = (titulo.isna() | titulo.astype(str).str.strip().isin(["", "nan"])).to_numpy()
            self.sin_titulo = int(sin_titulo.sum())
            self._excl = self._excl | sin_titulo
            # Y los textos libres que no son lectura en ingles (relleno, otra
            # lengua): los marca tools/marcar_no_lectura.py y no se borran del CSV.
            fuera = self._leer_no_lectura()
            if fuera:
                self._excl = self._excl | d["id"].astype(str).str.strip().str.upper().isin(fuera).to_numpy()
        return self._excl

    def _leer_no_lectura(self) -> set[str]:
        """Los ids de no_lectura_externo.csv, o un conjunto vacio."""
        ruta = getattr(self, "ruta", None)
        if ruta is None:
            return set()
        ruta = Path(ruta).with_name(NOMBRE_NO_LECTURA)
        if not ruta.exists():
            return set()
        try:
            return {str(i).strip().upper() for i in pd.read_csv(ruta, dtype=str)["id"].dropna()}
        except Exception:
            return set()

    @property
    def _literarios(self) -> np.ndarray:
        """Marca los libros cuyo tema es literatura (ver _LITERARIO).

        Sin `temas` -el catalogo heredado- todo cuenta como literario."""
        if getattr(self, "_lit", None) is None:
            d = self.df
            if "temas" in d.columns:
                self._lit = d["temas"].fillna("").astype(str).str.contains(_LITERARIO).to_numpy()
            else:
                self._lit = np.ones(len(d), dtype=bool)
        return self._lit

    def capitulos_de(self, id_libro) -> list[dict]:
        """La curva por capitulo que midio el catalogo para este libro, o [].

        Se carga una vez y se indexa por id: son 585.111 filas, y convertirlas
        todas a diccionarios al arrancar costaria segundos que nadie ha pedido.
        """
        if getattr(self, "_caps", None) is None:
            self._caps = pd.DataFrame()
            ruta = Path(self.ruta).with_name(NOMBRE_CAPITULOS)
            if self.medido and ruta.exists():
                try:
                    self._caps = pd.read_parquet(ruta).set_index("id").sort_index()
                except Exception:
                    self._caps = pd.DataFrame()       # sin curva, sin sugerencias
        pid = str(id_libro or "").upper()
        if self._caps.empty or pid not in self._caps.index:
            return []
        filas = self._caps.loc[[pid]].reset_index().sort_values("capitulo").to_dict("records")
        arreglo = getattr(self, "_correcciones", {}).get(pid)
        # La correccion es del libro entero: solo se puede trasladar a la curva
        # cuando la curva ES el libro entero (un capitulo). Con varios, la curva
        # medida se deja como esta antes que inventar un reparto por capitulos.
        if arreglo and len(filas) == 1:
            filas[0].update({k: arreglo[k] for k in ("dificultad", "min", "max")
                             if arreglo.get(k) is not None})
        return filas

    def _textos_abiertos(self) -> pd.DataFrame:
        if getattr(self, "_abiertos", None) is None:
            self._abiertos = pd.DataFrame()
            ruta = Path(self.ruta).with_name(NOMBRE_TEXTOS_ABIERTOS)
            if ruta.exists():
                try:
                    self._abiertos = pd.read_parquet(ruta).set_index("id")
                except Exception:
                    self._abiertos = pd.DataFrame()
        return self._abiertos

    def es_abrible(self, id_libro) -> bool:
        """¿Se puede abrir en el lector? Gutenberg se descarga; los corpus
        libres traen su texto en `corpus_abierto.parquet`. Lo que no esta en
        ninguno de los dos -StoryWeaver del catalogo heredado- no se ofrece."""
        pid = str(id_libro or "").strip().upper()
        if pid.startswith("PG") and any(c.isdigit() for c in pid):
            return True
        t = self._textos_abiertos()
        return (not t.empty) and pid in t.index

    def texto_abierto(self, id_libro) -> dict | None:
        """Titulo, autor, licencia, atribucion y texto de un libro libre, o None."""
        pid = str(id_libro or "").strip().upper()
        t = self._textos_abiertos()
        if t.empty or pid not in t.index:
            return None
        f = t.loc[pid]
        return {"id": pid, "titulo": str(f.get("title", "")), "autor": str(f.get("author", "")),
                "licencia": str(f.get("licencia", "")), "atribucion": str(f.get("atribucion", "")),
                "url": str(f.get("url", "")), "texto": str(f.get("texto", ""))}

    def _puntuaciones(self) -> np.ndarray:
        """El nivel de cada libro en la escala publica 0..2: la medida si la
        hay, y si no, la letra heredada traducida con NIVEL_A_PUNTUACION.

        Un solo sitio para las dos rutas -`buscar` y `por_nivel`-, que antes
        repetian la misma traduccion cada una por su lado."""
        heredada = np.array([NIVEL_A_PUNTUACION.get(x, 1.0)
                             for x in self.df["nivel_cefr"]], dtype=np.float32)
        if not self.medido:
            return heredada
        d = pd.to_numeric(self.df["dificultad"], errors="coerce").to_numpy(dtype=np.float32)
        return np.where(np.isnan(d), heredada, d).astype(np.float32)

    # --- busqueda -----------------------------------------------------
    def buscar(self, consulta: str, nivel_lector: float | None = None,
               peso_nivel: float = 0.3, n: int = 10,
               minimo_similitud: float = 0.10) -> tuple[list[Libro], str]:
        """Busca por descripcion libre, en espanol o ingles.

        Devuelve (resultados, aviso). `aviso` explica en lenguaje llano cuando
        el resultado no es el esperado, en vez de devolver una lista vacia muda.
        """
        consulta = (consulta or "").strip()
        if not consulta:
            return [], "Escribe qué tipo de lectura buscas."

        frases = [consulta]
        if len(consulta.split()) == 1:
            frases += [f.format(consulta) for f in FRASES_PALABRA_SUELTA]
        vs = np.asarray(self._modelo_emb().encode(frases, normalize_embeddings=True))
        sem = (self.embeddings @ vs.T).max(axis=1)

        # Rescate por nombre: si la consulta es el titulo entero de un libro o el
        # apellido de su autor (con el parecido ortografico que encuentra a
        # Dostoyevsky escribiendo «dostoyevski»), ese libro sube aunque el tema
        # no case. Un nombre de pila o una palabra suelta del titulo, no.
        # En su propio atributo y no en `_fichas`: hay montajes de prueba que
        # rellenan `_fichas` con la forma de antes (una lista por fila).
        if getattr(self, "_nombres", None) is None:
            autores = self.df["author"].tolist()
            self._nombres = (_fichas(self.df["title"].astype(str).tolist()),
                             _fichas([_apellidos(a) for a in autores]),
                             _fichas([_nombre_entero(a) for a in autores]),
                             _vocabulario_de_nombres(autores))
        titulos, apellidos, enteros, vocabulario = self._nombres
        por_apellido = _similitud_nombres(consulta, apellidos)
        # El nombre entero solo cuenta si incluye el apellido: «amor» es todo «Fenn, Amor»,
        # pero es su nombre de pila, y un nombre de pila suelto no rescata. Y solo con dos
        # palabras o más: una sola palabra que es el apellido de un colaborador («rosa»
        # en «Modern Poets and Poetry of Spain», por «Martínez de la Rosa») no es el nombre
        # entero de nadie, y con el extra pasaba por delante de los títulos con «Rosa»
        # (batería de buscador-encontrar, 15 sep 2026, antes de subir el 21).
        con_apellido = por_apellido >= _PARECIDO_NOMBRE
        # Un apellido suelto no puntúa si la consulta trae otro nombre que ese autor no
        # tiene: «Jane Austen» no es Sidney Austen ni «Calamity Jane».
        pistas = {p for p in re.split(r"[^a-z0-9]+", _normalizar(consulta)) if len(p) >= 4}
        nombres_de_la_consulta = pistas & vocabulario
        if len(pistas) > 1 and nombres_de_la_consulta:
            for i in np.flatnonzero(por_apellido >= _PARECIDO_NOMBRE):
                if nombres_de_la_consulta - enteros[i]:
                    por_apellido[i] = 0.0
        completo = _titulo_completo(consulta, enteros)
        lex = np.maximum.reduce([por_apellido, _titulo_completo(consulta, titulos),
                                 np.where((completo > 0) & con_apellido & (len(pistas) > 1),
                                          completo + _EXTRA_AUTOR_COMPLETO, 0.0)])
        validos = ~self._excluidos
        con_nombre = (lex >= _PARECIDO_NOMBRE) & validos
        if con_nombre.any() and validos.any() and \
                float(sem[con_nombre].max()) < float(sem[validos].max()) - MARGEN_SEMANTICO_NOMBRE:
            lex = np.zeros_like(lex)          # se escribe parecido y no tiene que ver con lo pedido
        # Entre libros con el mismo acierto de nombre (dos ediciones del mismo
        # titulo) desempata el tema, con un peso que no puede adelantar a un
        # nombre mas completo.
        sim = np.maximum(sem, np.where(lex >= _PARECIDO_NOMBRE,
                                       lex * _PESO_NOMBRE + 0.01 * sem, 0.0))

        if nivel_lector is None:
            total = sim
            afin = np.zeros_like(sim)
            orden = np.argsort(-total)
        else:
            objetivo = self._puntuaciones()
            # Afinidad 1 = mismo nivel, 0 = en el extremo opuesto de la escala.
            afin = 1.0 - np.abs(objetivo - nivel_lector) / 2.0
            total = (1 - peso_nivel) * sim + peso_nivel * afin
            # El nivel ordena DENTRO de lo relevante y no adelanta lo que no es
            # de lo que se pidio; un titulo acertado va siempre delante
            # (diagnostico de e6, 14 sep 2026: con perfil B1, «amor» sacaba
            # primero cuentos de su nivel que no eran de amor, y «A Midsummer
            # Night's Dream» buscado por titulo solo salia sin el ajuste).
            validos = ~self._excluidos
            techo = float(sim[validos].max()) if validos.any() else 0.0
            relevante = sim >= techo - MARGEN_RELEVANCIA
            mejor_nombre = float(lex[validos].max()) if validos.any() else 0.0
            nombre = (lex >= _PARECIDO_NOMBRE) & (lex >= mejor_nombre - MARGEN_NOMBRE)
            clave = np.where(nombre | relevante, total, sim)
            orden = np.lexsort((-clave, ~(relevante | nombre), ~nombre))
        libros, flojos = [], 0
        # El orden entero hasta llenar n: con `orden[:n * 3]`, si en esos puestos
        # habia mas de 2n excluidos o flojos, la lista salia corta aunque hubiera
        # candidatos validos mas abajo (auditoria cruzada de e6, M1).
        for i in orden:
            if len(libros) >= n:
                break
            if self._excluidos[i]:
                continue                      # un indice o un catalogo, no un libro
            if sim[i] < minimo_similitud:
                flojos += 1
                continue
            f = self.df.iloc[i]
            libros.append(Libro(id=str(f["id"]), titulo=str(f["title"]),
                                autor=str(f["author"]), nivel=str(f["nivel_cefr"]),
                                gancho=str(f["hook"]), descargas=int(f.get("downloads", 0) or 0),
                                dificultad=_dificultad_de(f),
                                similitud=round(float(sim[i]), 3),
                                afinidad=round(float(afin[i]), 3),
                                aviso_contenido=str(f.get("aviso_contenido", "") or ""),
                                medida=_medida_de_fila(f)))

        if not libros:
            # Nunca devolver vacio en silencio: ese era el fallo original.
            mejor = float(sim[orden[0]])
            return ([], f"Ningún libro supera el umbral de parecido "
                        f"(el mejor llegó a {mejor:.2f} de 1.00). Prueba a "
                        f"describirlo con otras palabras o baja el umbral.")
        aviso = ""
        if flojos:
            aviso = f"Se descartaron {flojos} resultados por parecido bajo."
        return libros, aviso

    def _intercalar_libres(self, d: pd.DataFrame, n: int,
                           nivel_lector: float | None = None) -> pd.DataFrame:
        """Las n primeras filas de `d`, ya ordenado, con un tercio de huecos para
        los textos libres que se abren sin descargar: puestos 2, 5, 8...

        Sin libres en la franja, `d.head(n)` tal cual. Si se acaban, los huecos
        vuelven al orden de siempre. Un titulo con aviso de contenido tampoco
        entra por un hueco en los PRIMEROS_SIN_AVISO primeros puestos.

        Los libres no tienen descargas: por popularidad empataban todos y salian
        por id, asi que A2 y B1 veian los mismos tres cuentos a 0,61, en el borde
        de las dos franjas (prueba como persona, 14 sep 2026). Con `nivel_lector`
        van primero los mas cercanos a su nivel y, a igual distancia, los medidos
        solos antes que los medidos dentro de un bloque."""
        if getattr(self, "_ids_libres", None) is None:
            # Un frozenset y no `isin` contra el indice: con texto de arrow, `isin`
            # recorria en Python los 15.357 ids en cada llamada (0,22 s de 0,28).
            self._ids_libres = frozenset(str(x).strip().upper() for x in self._textos_abiertos().index)
        if n < CADA_CUANTOS_LIBRE or d.empty or not self._ids_libres:
            return d.head(n)
        libre = np.fromiter((str(x).strip().upper() in self._ids_libres for x in d["id"].to_numpy()),
                            dtype=bool, count=len(d))
        if not libre.any():
            return d.head(n)
        if "aviso_contenido" in d.columns:
            aviso = (d["aviso_contenido"].astype(str).str.len() > 0).to_numpy()
        else:
            aviso = np.zeros(len(d), dtype=bool)
        libres = np.flatnonzero(libre).tolist()
        if nivel_lector is not None:
            dif = pd.to_numeric(d.get("dificultad"), errors="coerce")
            distancia = np.round(np.abs(dif.to_numpy(dtype=float) - nivel_lector), 3)
            distancia = np.where(np.isfinite(distancia), distancia, 9.0)
            en_bloque = (d["medida"].astype(str).to_numpy() == "bloque") if "medida" in d.columns \
                else np.zeros(len(d), dtype=bool)
            libres.sort(key=lambda i: (distancia[i], en_bloque[i], i))
        huecos = set(range(1, n, CADA_CUANTOS_LIBRE))
        usados: set[int] = set()

        def siguiente(candidatos, puesto):
            for i in candidatos:
                if i not in usados and not (puesto < PRIMEROS_SIN_AVISO and aviso[i]):
                    return i
            return None

        elegidos = []
        for puesto in range(min(n, len(d))):
            i = siguiente(libres, puesto) if puesto in huecos else None
            if i is None:
                i = siguiente(range(len(d)), puesto)
            if i is None:                     # solo quedan titulos con aviso
                i = next(j for j in range(len(d)) if j not in usados)
            usados.add(i)
            elegidos.append(i)
        return d.iloc[elegidos]

    def por_nivel(self, nivel_lector: float, holgura: float = 0.25,
                  n: int = 10) -> list[Libro]:
        """Libros cercanos al nivel del lector, ordenados por popularidad."""
        obj = self._puntuaciones()
        d = self.df[(np.abs(obj - nivel_lector) <= holgura) & ~self._excluidos
                    & self._literarios]
        d = d.sort_values("downloads", ascending=False, kind="stable")
        # Un titulo con aviso de contenido no encabeza la lista: los
        # PRIMEROS_SIN_AVISO primeros puestos son para los que no lo llevan, y
        # detras sigue el orden de popularidad de siempre. No se quita ninguno.
        if "aviso_contenido" in d.columns:
            con_aviso = d["aviso_contenido"].astype(str).str.len() > 0
            if con_aviso.any():
                cabeza = d[~con_aviso].head(PRIMEROS_SIN_AVISO)
                d = pd.concat([cabeza, d.drop(cabeza.index)])
        d = self._intercalar_libres(d, n, nivel_lector)
        return [Libro(id=str(f["id"]), titulo=str(f["title"]), autor=str(f["author"]),
                      nivel=str(f["nivel_cefr"]), gancho=str(f["hook"]),
                      descargas=int(f.get("downloads", 0) or 0),
                      dificultad=_dificultad_de(f),
                      aviso_contenido=str(f.get("aviso_contenido", "") or ""),
                      medida=_medida_de_fila(f))
                for _, f in d.iterrows()]

    def resumen(self) -> str:
        c = self.df["nivel_cefr"].value_counts().reindex(NIVELES).fillna(0).astype(int)
        return (f"{ficha.miles(len(self.df))} libros | " +
                " ".join(f"{n}:{c[n]}" for n in NIVELES))
