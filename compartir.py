"""Publica LiteraLevel en un enlace temporal, para usarla desde el movil.

Sirve para lo que en este portatil no se puede hacer: **practicar
pronunciacion**, porque aqui no hay microfono y en un telefono si.

El enlace lo crea Gradio (`share=True`), es HTTPS -condicion imprescindible,
porque el navegador solo da acceso al microfono en contexto seguro- y **dura
unas 72 horas**. No es un despliegue: mientras este proceso siga vivo y este
ordenador encendido, el enlace funciona; en cuanto se cierre, deja de existir.

Va **con contrasena**, y no es paranoia: el enlace es publico para cualquiera
que lo tenga, y detras esta la clave de OpenAI del dueno pagando cada consulta.
Con `auth`, Gradio ademas empieza a comprobar de verdad quien pide los archivos.

Uso:
    python -X utf8 compartir.py                 # genera una contrasena
    LITERALEVEL_CLAVE_COMPARTIR=loquesea python -X utf8 compartir.py
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "app"))

from ui import (LIMITE_CONSULTAS_HORA, LIMITE_VOZ_HORA,  # noqa: E402
                RUTAS_PERMITIDAS, TAMANO_MAXIMO_SUBIDA, TEMA, construir)

USUARIO = os.environ.get("LITERALEVEL_USUARIO_COMPARTIR", "miguel")
PALABRAS = ("iceberg", "fortress", "lantern", "harbour", "compass", "thistle",
            "meadow", "quarry", "beacon", "willow")

# Cuentas de invitado. Existen para poder pasarle el enlace a alguien -familia,
# el profesor- SIN darle la contrasena del dueno. Cada una es independiente:
# si una se filtra, se cambia esa y las demas siguen.
#
# Y no son un adorno de seguridad: `gr.Request.session_hash` mantiene los datos
# separados por sesion, asi que cada invitado tiene su propio nivel, su propia
# estanteria y su propio cuaderno. Nadie pisa la lectura de nadie.
INVITADOS = int(os.environ.get("LITERALEVEL_INVITADOS", "3"))


def _clave() -> str:
    """Una contrasena que se pueda teclear en un movil sin odiarla."""
    puesta = os.environ.get("LITERALEVEL_CLAVE_COMPARTIR")
    if puesta:
        return puesta
    return _clave_nueva()


def _clave_nueva() -> str:
    return "-".join((secrets.choice(PALABRAS), secrets.choice(PALABRAS),
                     str(secrets.randbelow(90) + 10)))


def _cuentas() -> list[tuple[str, str]]:
    """El dueno y los invitados. Gradio admite una lista de pares."""
    cuentas = [(USUARIO, _clave())]
    for i in range(1, max(0, INVITADOS) + 1):
        cuentas.append((f"invitado{i}", _clave_nueva()))
    return cuentas


def main() -> int:
    cuentas = _cuentas()
    print("=" * 70)
    print("  LiteraLevel — enlace temporal")
    print("=" * 70)
    for usuario, clave in cuentas:
        etiqueta = "tuya" if usuario == USUARIO else "para prestar"
        print(f"  {usuario:<10} {clave:<28} ({etiqueta})")
    print()
    print("  Cada cuenta lleva su propio nivel, su propia estantería y su")
    print("  propio cuaderno: no se pisan entre ellas.")
    print()
    print(f"  Límites por IP y hora: {LIMITE_CONSULTAS_HORA} consultas de")
    print(f"  palabra, {LIMITE_VOZ_HORA} prácticas de voz. Leer, buscar y medir")
    print("  no se limitan: no cuestan dinero.")
    print()
    print("  El enlace vive mientras este proceso siga abierto y este")
    print("  ordenador encendido. Ctrl+C lo cierra.")
    print("=" * 70)

    demo = construir()
    demo.launch(
        share=True,                 # enlace publico HTTPS: hace falta para el microfono
        auth=cuentas,
        theme=TEMA,
        allowed_paths=RUTAS_PERMITIDAS,
        max_file_size=TAMANO_MAXIMO_SUBIDA,
        inbrowser=False,
        show_error=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
