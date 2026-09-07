"""Catalogo de libros y busqueda semantica (paso 2 del recorrido).

La app anterior guardaba los embeddings en un .npy suelto y, si su longitud no
coincidia con el CSV, la busqueda devolvia vacio sin explicar por que. Ese era
el fallo de "busco realismo y no sale nada".

Aqui los embeddings se calculan a partir del propio CSV y se cachean con una
huella del archivo: si el catalogo cambia, la cache se invalida sola y se
recalcula. Es imposible que queden desincronizados.
"""
from __future__ import annotations
import hashlib, os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CSV_POR_DEFECTO = RAIZ / "catalogo_recomendaciones.csv"
DIR_CACHE = Path(os.path.expanduser("~")) / ".literalevel"

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

    @property
    def puntuacion_nivel(self) -> float:
        return NIVEL_A_PUNTUACION.get(self.nivel, 1.0)

    @property
    def url_gutenberg(self) -> str:
        num = "".join(c for c in str(self.id) if c.isdigit())
        return f"https://www.gutenberg.org/ebooks/{num}" if num else ""


def _huella(ruta: Path) -> str:
    """Identifica la version exacta del CSV: tamano + mtime + primeros bytes."""
    st = ruta.stat()
    h = hashlib.sha256(f"{st.st_size}-{st.st_mtime_ns}".encode())
    with open(ruta, "rb") as f:
        h.update(f.read(65536))
    return h.hexdigest()[:16]


class Catalogo:
    def __init__(self, ruta_csv: str | os.PathLike = CSV_POR_DEFECTO):
        self.ruta = Path(ruta_csv)
        if not self.ruta.exists():
            raise FileNotFoundError(f"No encuentro el catálogo en {self.ruta}")
        self.df = pd.read_csv(self.ruta).fillna({"hook": "", "huella_texto": "",
                                                 "author": "", "nivel_cefr": ""})
        self._emb: np.ndarray | None = None
        self._modelo = None

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
        DIR_CACHE.mkdir(parents=True, exist_ok=True)
        cache = DIR_CACHE / f"catalogo_emb_{_huella(self.ruta)}.npy"
        if cache.exists():
            emb = np.load(cache)
            if len(emb) == len(self.df):      # cinturon y tirantes
                self._emb = emb
                return emb
        emb = self._modelo_emb().encode(self._texto_indexable(),
                                        normalize_embeddings=True,
                                        batch_size=64, show_progress_bar=False)
        emb = np.asarray(emb, dtype=np.float32)
        np.save(cache, emb)
        for viejo in DIR_CACHE.glob("catalogo_emb_*.npy"):
            if viejo != cache:
                viejo.unlink()             # el catalogo cambio: sobra
        self._emb = emb
        return emb

    def _modelo_emb(self):
        if self._modelo is None:
            from sentence_transformers import SentenceTransformer
            self._modelo = SentenceTransformer(MODELO_EMB)
        return self._modelo

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

        if nivel_lector is None:
            total = sim
            afin = np.zeros_like(sim)
        else:
            objetivo = np.array([NIVEL_A_PUNTUACION.get(x, 1.0)
                                 for x in self.df["nivel_cefr"]], dtype=np.float32)
            # Afinidad 1 = mismo nivel, 0 = en el extremo opuesto de la escala.
            afin = 1.0 - np.abs(objetivo - nivel_lector) / 2.0
            total = (1 - peso_nivel) * sim + peso_nivel * afin

        orden = np.argsort(-total)
        libros, flojos = [], 0
        for i in orden[:n * 3]:
            if len(libros) >= n:
                break
            if sim[i] < minimo_similitud:
                flojos += 1
                continue
            f = self.df.iloc[i]
            libros.append(Libro(id=str(f["id"]), titulo=str(f["title"]),
                                autor=str(f["author"]), nivel=str(f["nivel_cefr"]),
                                gancho=str(f["hook"]), descargas=int(f.get("downloads", 0) or 0),
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
        obj = np.array([NIVEL_A_PUNTUACION.get(x, 1.0)
                        for x in self.df["nivel_cefr"]], dtype=np.float32)
        d = self.df[np.abs(obj - nivel_lector) <= holgura]
        d = d.sort_values("downloads", ascending=False).head(n)
        return [Libro(id=str(f["id"]), titulo=str(f["title"]), autor=str(f["author"]),
                      nivel=str(f["nivel_cefr"]), gancho=str(f["hook"]),
                      descargas=int(f.get("downloads", 0) or 0))
                for _, f in d.iterrows()]

    def resumen(self) -> str:
        c = self.df["nivel_cefr"].value_counts().reindex(NIVELES).fillna(0).astype(int)
        return (f"{len(self.df):,} libros | " +
                " ".join(f"{n}:{c[n]}" for n in NIVELES))
