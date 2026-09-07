"""Carga de claves desde .env, sin dependencias externas.

Las claves nunca se imprimen ni se registran. `falta()` permite que la interfaz
desactive con elegancia las funciones que no tienen credencial, en vez de
reventar a media sesion.
"""
from __future__ import annotations
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# Se admiten dos nombres: .env es la convencion, CLAVES.txt es lo que de
# verdad se encuentra en el explorador de Windows.
RUTAS_ENV = (RAIZ / ".env", RAIZ / "CLAVES.txt")
RUTA_ENV = RUTAS_ENV[0]

# Oxford Dictionaries quedo descartado (sus claves devuelven 403); el
# diccionario es Kaikki/Wiktionary en SQLite local y no necesita credencial.
CLAVES = ("OPENAI_API_KEY",)


def cargar(rutas=RUTAS_ENV) -> None:
    """Mete las variables de los archivos de claves en os.environ.

    No pisa lo que ya este definido, asi que una variable de entorno real
    siempre gana sobre el archivo.
    """
    for ruta in rutas:
        if not ruta.exists():
            continue
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            nombre, _, valor = linea.partition("=")
            nombre, valor = nombre.strip(), valor.strip().strip("'\"")
            if valor and not os.environ.get(nombre):
                os.environ[nombre] = valor


def obtener(nombre: str) -> str | None:
    cargar()
    v = os.environ.get(nombre)
    return v or None


def falta() -> list[str]:
    """Claves que siguen vacias. La UI usa esto para avisar sin romperse."""
    cargar()
    return [c for c in CLAVES if not os.environ.get(c)]


def estado() -> str:
    """Diagnostico seguro: nunca muestra fragmentos ni longitud de secretos."""
    cargar()
    lineas = []
    for c in CLAVES:
        v = os.environ.get(c)
        lineas.append(f"  {c:<18} {'CONFIGURADA' if v else 'FALTA'}")
    return "\n".join(lineas)


if __name__ == "__main__":
    for r in RUTAS_ENV:
        print(f"{'encontrado' if r.exists() else 'no existe '}  {r}")
    print(estado())
