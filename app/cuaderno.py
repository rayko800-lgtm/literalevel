"""Cuaderno de palabras: lo que has consultado, con su frase y su libro.

Existe porque hasta ahora, cuando cerrabas LiteraLevel, no quedaba rastro de
nada. Se leia, se consultaban palabras y al salir la sesion se evaporaba: no
habia a que volver.

Que NO es esto, deliberadamente:

  - No es la cache de `lexicon.py`. Aquella guarda respuestas de OpenAI por
    `sha256(palabra, oracion, nivel)` para no pagar dos veces lo mismo: no
    tiene libro, ni fecha util, ni forma de recorrerse. Es cache, no historia.
  - No es un sistema de puntos, rachas ni recompensas. Leer ya es
    gratificante por si mismo, y la evidencia sobre recompensas externas dice
    que ponerle una nota a algo que ya te gusta lo estropea. Aqui no se
    premia entrar ni se castiga faltar.

Lo que si es: un registro que se llena solo mientras lees, con la unidad que
de verdad sirve para recordar una palabra, que es **la palabra en su frase y
en su libro**, no una definicion suelta.

Base en `~/.literalevel/cuaderno.db`. Si no se puede escribir, se calla y
sigue: apuntar una palabra jamas puede estropear la lectura.
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

RUTA_POR_DEFECTO = Path(os.path.expanduser("~")) / ".literalevel" / "cuaderno.db"

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS consultas (
    id        INTEGER PRIMARY KEY,
    palabra   TEXT NOT NULL,     -- la forma tal como aparecia en el texto
    lema      TEXT NOT NULL,
    categoria TEXT,
    sentido   TEXT,              -- la glosa que se eligio
    oracion   TEXT NOT NULL,     -- la frase del libro, que es lo que fija el recuerdo
    libro     TEXT,
    capitulo  INTEGER,
    banda     TEXT,
    zipf      REAL,
    creado    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cuaderno_lema ON consultas(lema);
CREATE INDEX IF NOT EXISTS idx_cuaderno_creado ON consultas(creado);
"""


@dataclass
class Anotacion:
    palabra: str
    lema: str
    categoria: str | None
    sentido: str | None
    oracion: str
    libro: str | None
    capitulo: int | None
    zipf: float | None
    creado: str

    @property
    def rareza(self) -> str:
        if self.zipf is None:
            return ""
        return ("muy común" if self.zipf >= 5 else "frecuente" if self.zipf >= 4
                else "poco frecuente" if self.zipf >= 3 else "rara")


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _conectar(ruta: str | os.PathLike = RUTA_POR_DEFECTO) -> sqlite3.Connection:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(ruta))
    con.executescript(_ESQUEMA)
    return con


def registrar(*, palabra: str, lema: str, oracion: str, categoria: str | None = None,
              sentido: str | None = None, libro: str | None = None,
              capitulo: int | None = None, banda: str | None = None,
              zipf: float | None = None,
              ruta: str | os.PathLike = RUTA_POR_DEFECTO) -> bool:
    """Apunta una consulta. Devuelve si se pudo guardar, sin lanzar nunca.

    No se deduplica a proposito: volver a mirar la misma palabra en otra
    frase es informacion, no ruido; y volver a mirarla en la MISMA frase dice
    que aun no se ha fijado.
    """
    if not (palabra or "").strip() or not (oracion or "").strip():
        return False
    try:
        with _conectar(ruta) as con:
            con.execute(
                "INSERT INTO consultas (palabra, lema, categoria, sentido, oracion,"
                " libro, capitulo, banda, zipf, creado)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (palabra.strip(), (lema or palabra).strip(), categoria, sentido,
                 " ".join(oracion.split()), libro, capitulo, banda, zipf, _ahora()),
            )
        return True
    except (sqlite3.Error, OSError):
        return False


def _filas(sql: str, args: tuple, ruta) -> list[Anotacion]:
    try:
        with _conectar(ruta) as con:
            filas = con.execute(sql, args).fetchall()
    except (sqlite3.Error, OSError):
        return []
    return [Anotacion(palabra=f[0], lema=f[1], categoria=f[2], sentido=f[3],
                      oracion=f[4], libro=f[5], capitulo=f[6], zipf=f[7], creado=f[8])
            for f in filas]


_COLUMNAS = ("palabra, lema, categoria, sentido, oracion, libro, capitulo, "
             "zipf, creado")


def ultimas(n: int = 20, ruta: str | os.PathLike = RUTA_POR_DEFECTO) -> list[Anotacion]:
    return _filas(f"SELECT {_COLUMNAS} FROM consultas ORDER BY id DESC LIMIT ?",
                  (max(1, int(n)),), ruta)


def para_repasar(n: int = 5, ruta: str | os.PathLike = RUTA_POR_DEFECTO) -> list[Anotacion]:
    """Las mas raras de entre las ultimas consultadas.

    Se mira solo lo reciente y de ahi se sacan las menos frecuentes: son las
    que de verdad cuesta retener. Una palabra por lema, para no repetir.
    """
    return _filas(
        f"SELECT {_COLUMNAS} FROM ("
        f"  SELECT {_COLUMNAS}, MAX(id) AS ultimo FROM ("
        "     SELECT * FROM consultas ORDER BY id DESC LIMIT 120"
        "  ) GROUP BY lema"
        ") ORDER BY COALESCE(zipf, 0) ASC, ultimo DESC LIMIT ?",
        (max(1, int(n)),), ruta)


def contar(ruta: str | os.PathLike = RUTA_POR_DEFECTO) -> tuple[int, int, int]:
    """(consultas totales, lemas distintos, libros distintos)."""
    try:
        with _conectar(ruta) as con:
            return tuple(con.execute(
                "SELECT COUNT(*), COUNT(DISTINCT lema),"
                " COUNT(DISTINCT COALESCE(libro,'')) FROM consultas").fetchone())
    except (sqlite3.Error, OSError):
        return (0, 0, 0)
