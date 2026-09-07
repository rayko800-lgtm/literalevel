"""Los libros que el lector ha abierto, y por donde va en cada uno.

`sesion.json` recuerda **un** libro: el ultimo. Esto recuerda todos, que es
lo que pidio Miguel: *"me gustaria que yo tenga como mi libro tambien los
libros que estoy leyendo y que se queden guardados, en que partes voy, con
todo lo que he buscado"*.

Es un JSON y no una base de datos a proposito: son unas decenas de entradas,
se leen enteras cada vez y se quieren poder mirar a ojo si algo va mal. Como
todo lo que guarda esta app, si no se puede escribir se calla y sigue: llevar
la cuenta de los libros jamas puede estropear la lectura.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

RUTA_POR_DEFECTO = Path(os.path.expanduser("~")) / ".literalevel" / "biblioteca.json"
MAXIMO = 60          # mas que esto ya no es una biblioteca, es un archivo


@dataclass
class Entrada:
    ruta: str
    titulo: str
    autor: str
    capitulos: int
    capitulo: int          # indice 0..n-1 por donde iba
    palabras: int
    visto: str             # ISO 8601 UTC

    @property
    def existe(self) -> bool:
        return bool(self.ruta) and os.path.exists(self.ruta)

    @property
    def avance(self) -> float:
        """Fraccion leida, 0..1, contando el capitulo actual como empezado."""
        if self.capitulos <= 1:
            return 1.0
        return min(1.0, max(0.0, self.capitulo / (self.capitulos - 1)))


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _leer(ruta) -> list[dict]:
    try:
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _escribir(datos, ruta) -> bool:
    try:
        p = Path(ruta)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
        return True
    except OSError:
        return False


def anotar(*, ruta_libro: str, titulo: str, autor: str, capitulos: int,
           capitulo: int, palabras: int,
           ruta=RUTA_POR_DEFECTO) -> bool:
    """Registra o actualiza un libro. Identifica por ruta del archivo.

    Si el libro ya estaba, se actualiza el capitulo y la fecha y sube al
    principio: la biblioteca se ordena por lo ultimo que se ha tocado, que es
    lo que uno busca cuando vuelve.
    """
    if not ruta_libro or not titulo:
        return False
    datos = [e for e in _leer(ruta) if e.get("ruta") != str(ruta_libro)]
    datos.insert(0, {"ruta": str(ruta_libro), "titulo": titulo, "autor": autor or "",
                     "capitulos": int(capitulos), "capitulo": int(capitulo),
                     "palabras": int(palabras), "visto": _ahora()})
    return _escribir(datos[:MAXIMO], ruta)


def listar(ruta=RUTA_POR_DEFECTO) -> list[Entrada]:
    fuera = []
    for e in _leer(ruta):
        try:
            fuera.append(Entrada(
                ruta=str(e.get("ruta", "")), titulo=str(e.get("titulo", "")),
                autor=str(e.get("autor", "")), capitulos=int(e.get("capitulos", 0)),
                capitulo=int(e.get("capitulo", 0)), palabras=int(e.get("palabras", 0)),
                visto=str(e.get("visto", ""))))
        except (TypeError, ValueError):
            continue
    return fuera


def olvidar(ruta_libro: str, ruta=RUTA_POR_DEFECTO) -> bool:
    datos = [e for e in _leer(ruta) if e.get("ruta") != str(ruta_libro)]
    return _escribir(datos, ruta)
