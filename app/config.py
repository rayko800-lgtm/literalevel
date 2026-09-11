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


def dir_datos() -> Path:
    """LA raiz de todo lo que la app escribe. Una sola, y configurable.

    Por defecto `~/.literalevel`. Con `LITERALEVEL_DATOS` se mueve entera, y eso
    es lo que permite montar un disco persistente en un Space sin tocar codigo:
    el disco del contenedor es EFIMERO y ahi viven la estanteria del lector, su
    cuaderno de vocabulario, su perfil, las curvas ya calculadas, los libros
    descargados y las caches de lexico y de audio que evitan volver a pagar a
    OpenAI por lo mismo.

    Se lee en cada llamada y no se guarda en una constante de modulo: las
    pruebas fijan `LITERALEVEL_DATOS` a un temporal, y una constante congelada
    en el import las haria escribir en los datos de verdad segun el orden de los
    imports. Aqui ya paso: la bateria de pruebas abria libro.txt, vacio.txt y
    falso.txt y los anotaba en la biblioteca de Miguel.
    """
    return Path(os.environ.get("LITERALEVEL_DATOS",
                               Path(os.path.expanduser("~")) / ".literalevel"))


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
