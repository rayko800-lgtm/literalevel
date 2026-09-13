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

# Lo que no es un libro para leer, aunque venga de Gutenberg: indices,
# catalogos, bibliografias, directorios. Medido el 12 de septiembre de 2026: 79
# de los 599 libros A1-B1 del catalogo medido eran esto -los *CIA World
# Factbook*, listas de oficinas de correos, tablas de constantes- y puntuan
# "facil" precisamente porque son listas. NO se borran del CSV: los embeddings
# van alineados fila a fila y borrar una obligaria a recodificar el catalogo.
# Se excluyen al recomendar y al buscar.
_NO_ES_LECTURA_TEMAS = re.compile(
    r"(?i)\bindexes\b|\bcatalogs\b|bibliograph|\bdirectories\b|gazetteers|almanacs")
_NO_ES_LECTURA_TITULO = re.compile(
    r"(?i)index of the project gutenberg|project gutenberg (?:works|index|catalog)"
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
        mejor = 0.0
        for pista in pistas:
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
                if r > mejor:
                    mejor = r
        fuera[i] = mejor
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
        """Lo que se indexa: titulo, autor y las pistas de contenido. El
        `hook` solo tiene ~8 palabras, asi que sin `huella_texto` la busqueda
        semantica se queda sin senal."""
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
            # recodifica sus filas (segundos), no las 53.179 de Gutenberg.
            ext = self._embeddings_de("catalogo_emb_ext_", _huella(externo), textos[n:])
            emb = np.vstack([emb, ext])
        self._emb = emb
        return emb

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
        return self._excl

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
        filas = self._caps.loc[[pid]].reset_index()
        return filas.sort_values("capitulo").to_dict("records")

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

        v = self._modelo_emb().encode([consulta], normalize_embeddings=True)[0]
        sim = self.embeddings @ v

        # Rescate por nombre: si la consulta se parece casi exactamente al
        # titulo o al autor de un libro, ese libro sube aunque el tema no
        # case. Es lo que hace que "dostoyevski" encuentre a Dostoyevsky.
        if self._fichas is None:
            self._fichas = _fichas(
                (self.df["title"].astype(str) + " " + self.df["author"].astype(str)).tolist())
        lex = _similitud_nombres(consulta, self._fichas)
        sim = np.maximum(sim, np.where(lex >= _PARECIDO_NOMBRE,
                                       lex * _PESO_NOMBRE, 0.0))

        if nivel_lector is None:
            total = sim
            afin = np.zeros_like(sim)
        else:
            objetivo = self._puntuaciones()
            # Afinidad 1 = mismo nivel, 0 = en el extremo opuesto de la escala.
            afin = 1.0 - np.abs(objetivo - nivel_lector) / 2.0
            total = (1 - peso_nivel) * sim + peso_nivel * afin

        orden = np.argsort(-total)
        libros, flojos = [], 0
        for i in orden[:n * 3]:
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
                                afinidad=round(float(afin[i]), 3)))

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

    def por_nivel(self, nivel_lector: float, holgura: float = 0.25,
                  n: int = 10) -> list[Libro]:
        """Libros cercanos al nivel del lector, ordenados por popularidad."""
        obj = self._puntuaciones()
        d = self.df[(np.abs(obj - nivel_lector) <= holgura) & ~self._excluidos
                    & self._literarios]
        d = d.sort_values("downloads", ascending=False).head(n)
        return [Libro(id=str(f["id"]), titulo=str(f["title"]), autor=str(f["author"]),
                      nivel=str(f["nivel_cefr"]), gancho=str(f["hook"]),
                      descargas=int(f.get("downloads", 0) or 0),
                      dificultad=_dificultad_de(f))
                for _, f in d.iterrows()]

    def resumen(self) -> str:
        c = self.df["nivel_cefr"].value_counts().reindex(NIVELES).fillna(0).astype(int)
        return (f"{ficha.miles(len(self.df))} libros | " +
                " ".join(f"{n}:{c[n]}" for n in NIVELES))
