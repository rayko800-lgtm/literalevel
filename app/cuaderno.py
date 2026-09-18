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
-- D3.2: eventos de repaso, aparte de `consultas` (append-only, nunca se
-- reescribe ni se borra una fila). `consulta_id` identifica la tarjeta
-- exacta que se evaluo (la fila de `consultas` vigente en ese momento);
-- `lema` se repite aqui para que D3.3 pueda agregar por palabra sin tener
-- que volver a `consultas` (que puede tener varias filas por lema y sigue
-- cambiando). El resto es una foto de lo que se enseño al evaluar.
CREATE TABLE IF NOT EXISTS repasos (
    id          INTEGER PRIMARY KEY,
    consulta_id INTEGER NOT NULL,
    lema        TEXT NOT NULL,
    evaluacion  TEXT NOT NULL CHECK (evaluacion IN ('no', 'dude', 'si')),
    palabra     TEXT,
    oracion     TEXT,
    sentido     TEXT,
    libro       TEXT,
    capitulo    INTEGER,
    creado      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_repasos_lema ON repasos(lema);
CREATE INDEX IF NOT EXISTS idx_repasos_consulta ON repasos(consulta_id);
CREATE INDEX IF NOT EXISTS idx_repasos_creado ON repasos(creado);
"""


@dataclass
class Anotacion:
    id: int
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
    return [Anotacion(id=f[0], palabra=f[1], lema=f[2], categoria=f[3], sentido=f[4],
                      oracion=f[5], libro=f[6], capitulo=f[7], zipf=f[8], creado=f[9])
            for f in filas]


_COLUMNAS = ("id, palabra, lema, categoria, sentido, oracion, libro, capitulo, "
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


def por_id(consulta_id: int, ruta: str | os.PathLike = RUTA_POR_DEFECTO) -> Anotacion | None:
    """La consulta exacta con ese id, o `None` si no existe EN ESTE cuaderno.

    Como cada lector tiene su propio archivo (D2: por `X-Lector`, nunca por
    cuenta), buscar aqui ya implica "es de este lector": un id que exista en
    el cuaderno de otro lector simplemente no aparece en este archivo.
    """
    filas = _filas(f"SELECT {_COLUMNAS} FROM consultas WHERE id = ?", (int(consulta_id),), ruta)
    return filas[0] if filas else None


EVALUACIONES = ("no", "dude", "si")


def registrar_repaso(*, consulta_id: int, evaluacion: str,
                      ruta: str | os.PathLike = RUTA_POR_DEFECTO) -> bool:
    """Evento de repaso, append-only: nunca reescribe ni borra nada.

    La foto (palabra/oracion/sentido/libro/capitulo) se toma AQUI, de la
    propia consulta en este cuaderno — nunca de lo que mande el front, que
    solo trae `consulta_id` y `evaluacion` (D3.2, decision de Miguel: el
    front no es la fuente de verdad de que se enseño). Si `consulta_id` no
    existe en este cuaderno, no se guarda nada y se devuelve `False`: quien
    llama (la API) lo convierte en 404, no en un evento a medias.
    """
    if evaluacion not in EVALUACIONES:
        return False
    a = por_id(consulta_id, ruta)
    if a is None:
        return False
    try:
        with _conectar(ruta) as con:
            con.execute(
                "INSERT INTO repasos (consulta_id, lema, evaluacion, palabra, oracion,"
                " sentido, libro, capitulo, creado) VALUES (?,?,?,?,?,?,?,?,?)",
                (a.id, a.lema, evaluacion, a.palabra, a.oracion, a.sentido,
                 a.libro, a.capitulo, _ahora()),
            )
        return True
    except (sqlite3.Error, OSError):
        return False
