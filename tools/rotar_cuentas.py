"""Rota las contrasenas de los perfiles del Space, sin que pasen por ningun chat.

    python -X utf8 tools/rotar_cuentas.py

Pide el token de Hugging Face sin mostrarlo por pantalla, genera contrasenas
nuevas, las escribe en el secreto `LITERALEVEL_CUENTAS` del Space y las guarda
en `literalevel_codigos.txt`, que esta en `.gitignore`.

POR QUE ESTE GUION EXISTE
-------------------------
La contrasena de `invitado1` estuvo escrita en `entrega/mensaje_profesor.md`,
que esta versionado: quedo en el historial de git, y eso no se puede
desescribir. Rotarla a mano en el panel es facil, pero hay NUEVE perfiles y el
formato no perdona -una contrasena con `:` dentro rompe su entrada-, asi que
mejor generarlas bien de una vez.

DOS REGLAS QUE ESTE GUION RESPETA
---------------------------------
1. **Las contrasenas no se imprimen nunca.** Van al archivo local y a la API.
   Lo que se escribe en una conversacion o en un correo nace quemado.
2. **Primero se escribe el secreto y DESPUES el archivo.** Al reves -que es lo
   que hizo la primera version- deja un archivo con nueve contrasenas que no
   son las del Space si la API falla, y quien lo lea le dara al profesor una
   contrasena que no funciona. Si algo falla, aqui no se escribe nada.

EL TOKEN
--------
Necesita permiso sobre la CONFIGURACION del Space, no solo sobre su contenido:
un token que solo pueda escribir archivos da 401 en `/secrets`. En
huggingface.co/settings/tokens vale un token clasico de tipo `write`, o uno
detallado con permiso de escritura sobre los Spaces de tu cuenta.
"""
from __future__ import annotations

import getpass
import os
import pathlib
import secrets
import string
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SPACE = "MikeMaki1763/literalevel"
DESTINO = RAIZ / "literalevel_codigos.txt"

# Sin `:` ni `,`, que son los separadores del formato. Y sin O/0 ni l/1/I, que
# se confunden al dictarlos por telefono o al copiarlos de una diapositiva.
ALFABETO = "".join(c for c in string.ascii_letters + string.digits
                   if c not in "Ol1I0")

PERFILES = [
    # (usuario, tope, para que es).  tope 0 = sin limite
    ("miguel",    0,  "el tuyo: sin limite"),
    ("profesor",  60, "para el profesor; 60 usos sobran para evaluar"),
    ("invitado1", 20, "invitados, 20 usos cada uno"),
    ("invitado2", 20, ""),
    ("invitado3", 20, ""),
    ("invitado4", 20, ""),
    ("invitado5", 20, ""),
    ("invitado6", 20, ""),
    ("invitado7", 20, ""),
]


def clave(n: int = 14) -> str:
    return "".join(secrets.choice(ALFABETO) for _ in range(n))


def main() -> int:
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("Falta huggingface_hub:  pip install huggingface_hub")
        return 1

    token = os.environ.get("HF_TOKEN") or getpass.getpass(
        "Token de Hugging Face (no se vera al teclearlo): ").strip()
    if not token:
        print("Sin token no puedo hacer nada.")
        return 1

    api = HfApi(token=token)
    try:
        quien = api.whoami()
    except Exception as e:
        print(f"El token no sirve: {type(e).__name__}")
        return 1
    print(f"Cuenta: {quien.get('name')}")

    filas = [(u, clave(), t, nota) for u, t, nota in PERFILES]
    secreto = ",".join(f"{u}:{c}:{t}" for u, c, t, _ in filas)
    assert all(":" not in c and "," not in c for _, c, _, _ in filas)

    # PRIMERO el Space. Si esto falla, no se escribe nada en disco.
    try:
        api.add_space_secret(
            repo_id=SPACE, key="LITERALEVEL_CUENTAS", value=secreto,
            description="Perfiles con acceso a lo que cuesta dinero. "
                        "usuario:contrasena:tope, separados por comas. "
                        "Tope 0 = sin limite.")
    except Exception as e:
        print(f"\nNo pude escribir el secreto: {type(e).__name__}")
        print("Si es un 401, al token le falta permiso sobre la CONFIGURACION")
        print("del Space. Uno que solo escriba archivos no basta.")
        print("\nNo se ha cambiado nada y no se ha escrito ningun archivo.")
        return 1

    lineas = [
        "CONTRASENAS DEL SPACE DE LITERALEVEL",
        "",
        "Generadas por tools/rotar_cuentas.py. Sustituyen a las anteriores:",
        "la de invitado1 estuvo en un archivo versionado, o sea en el historial",
        "de git para siempre, asi que se rotaron todas.",
        "",
        "ESTE ARCHIVO NO SE SUBE A GIT (esta en .gitignore) Y NO SE PEGA EN UN",
        "CHAT NI EN UN CORREO. Al profesor, dictale solo su linea.",
        "",
        f"{'usuario':<12} {'contrasena':<16} {'tope':<11} que es",
        "-" * 76,
    ]
    for u, c, t, nota in filas:
        lineas.append(f"{u:<12} {c:<16} "
                      f"{('sin limite' if t == 0 else str(t)):<11} {nota}")
    lineas += [
        "",
        "El 'tope' es el numero de acciones DE PAGO: explicar una palabra en su",
        "frase, el resumen de '¿de que trata?' y la correccion de",
        "pronunciacion. Todo lo demas -medir un texto, buscar, leer el libro",
        "entero, la curva por capitulos, el diccionario y la fonetica- funciona",
        "sin entrar y no gasta nada.",
        "",
        "Para comprobar que el Space las acepto: abre la app, pestana Estado, y",
        f"mira que diga 'Perfiles: {len(filas)} validos de {len(filas)}",
        "declarados'. Si dice menos, ahi mismo aparece cual falla y por que.",
    ]
    DESTINO.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print(f"\nListo: {len(filas)} perfiles nuevos en el Space.")
    print(f"Las contrasenas estan en {DESTINO.name} (no se imprimen aqui).")
    print("El Space se reinicia solo; tarda un par de minutos.")
    print("Luego: pestana Estado -> 'Perfiles: "
          f"{len(filas)} validos de {len(filas)} declarados'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
