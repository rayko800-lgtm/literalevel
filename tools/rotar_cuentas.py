"""Rota las contrasenas de los perfiles del Space, sin que pasen por ningun chat.

    python -X utf8 tools/rotar_cuentas.py

Genera contrasenas nuevas, las escribe en el secreto `LITERALEVEL_CUENTAS` del
Space y las guarda en `literalevel_codigos.txt` (en `.gitignore`) y en la copia
de la carpeta «claves» de Miguel, junto con la direccion de la aplicacion.

POR QUE ESTE GUION EXISTE
-------------------------
La contrasena de `invitado1` estuvo escrita en `entrega/mensaje_profesor.md`,
que esta versionado: quedo en el historial de git, y eso no se puede
desescribir. Rotarla a mano en el panel es facil, pero hay DIEZ perfiles y el
formato no perdona -una contrasena con `:` dentro rompe su entrada-, asi que
mejor generarlas bien de una vez.

POR QUE PALABRAS Y NO LETRAS AL AZAR (13 sep 2026)
--------------------------------------------------
La primera version generaba 14 caracteres aleatorios con mayusculas
(`sZyXGhzkf4XgJM`). Laura no pudo entrar con `invitado3` desde el telefono:
tecleo mal una contrasena asi, y es lo esperable. Ahora son dos palabras
cortas del español y tres cifras, todo en minusculas y sin simbolos
(`lunatrigo482`): se dictan, se leen de un mensaje y se teclean con un solo
cambio de teclado. Lo que la hace segura para esta app no es la longitud sino
el freno de la puerta: 15 intentos fallidos por IP y hora, y un tope de usos
de pago por perfil.

TRES REGLAS QUE ESTE GUION RESPETA
----------------------------------
1. **Las contrasenas no se imprimen nunca.** Van a los archivos locales y a la
   API.
2. **Primero se escribe el secreto y DESPUES los archivos.** Si la API falla,
   aqui no se escribe nada, y nadie reparte contrasenas que no funcionan.
3. **Sin `:` ni `,`**, que son los separadores del formato del secreto.

EL TOKEN
--------
Se lee de la variable HF_TOKEN, o de `~/.hf_token`, o se pide sin mostrarlo.
Necesita permiso sobre la CONFIGURACION del Space: un token que solo pueda
escribir archivos da 401 en `/secrets`.
"""
from __future__ import annotations

import getpass
import os
import pathlib
import secrets
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SPACE = "MikeMaki1763/literalevel"
URL_APP = "https://mikemaki1763-literalevel.hf.space"
URL_PAGINA = "https://huggingface.co/spaces/MikeMaki1763/literalevel"
DESTINOS = [
    RAIZ / "literalevel_codigos.txt",
    pathlib.Path(r"C:\Users\laura\OneDrive\Escritorio\Libros para el diplomado de ciencia de datos"
                 r"\claves\literalevel_codigos.txt"),
]

# Palabras cortas, sin tildes ni eñe (no todos los teclados las tienen a mano)
# y sin pares que se confundan al dictarlas.
PALABRAS = [
    "luna", "sol", "mar", "rio", "lago", "nube", "flor", "roca", "trigo", "pino",
    "gato", "perro", "oso", "lobo", "pato", "vaca", "rana", "tigre", "mango", "limon",
    "pera", "uva", "coco", "miel", "pan", "sal", "te", "cafe", "piano", "tambor",
    "libro", "lapiz", "papel", "mapa", "barco", "tren", "avion", "faro", "puente", "torre",
    "verde", "azul", "rojo", "gris", "oro", "plata", "nieve", "lluvia", "viento", "fuego",
]

PERFILES = [
    # (usuario, tope, para que es).  tope 0 = sin limite
    ("miguel",    0,  "desarrollador: sin limite"),
    ("profesor",  60, "para el profesor; 60 usos sobran para evaluar"),
] + [(f"invitado{i}", 20, "invitados, 20 usos cada uno" if i == 1 else "") for i in range(1, 9)]


def clave() -> str:
    a = secrets.choice(PALABRAS)
    b = secrets.choice([p for p in PALABRAS if p != a])
    return f"{a}{b}{secrets.randbelow(900) + 100}"


def _token() -> str:
    tok = os.environ.get("HF_TOKEN", "").strip()
    archivo = pathlib.Path.home() / ".hf_token"
    if not tok and archivo.exists():
        tok = archivo.read_text(encoding="utf-8").strip()
    if not tok:
        tok = getpass.getpass("Token de Hugging Face (no se vera al teclearlo): ").strip()
    return tok


def main() -> int:
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("Falta huggingface_hub:  pip install huggingface_hub")
        return 1

    token = _token()
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

    usadas: set[str] = set()
    filas = []
    for u, t, nota in PERFILES:
        c = clave()
        while c in usadas:
            c = clave()
        usadas.add(c)
        filas.append((u, c, t, nota))
    secreto = ",".join(f"{u}:{c}:{t}" for u, c, t, _ in filas)
    assert all(":" not in c and "," not in c and c.isalnum() and c.islower() for _, c, _, _ in filas)

    # PRIMERO el Space. Si esto falla, no se escribe nada en disco.
    try:
        api.add_space_secret(
            repo_id=SPACE, key="LITERALEVEL_CUENTAS", value=secreto,
            description="Perfiles con acceso a lo que cuesta dinero. "
                        "usuario:contrasena:tope, separados por comas. "
                        "Tope 0 = sin limite.")
    except Exception as e:
        print(f"\nNo pude escribir el secreto: {type(e).__name__}")
        print("Si es un 401, al token le falta permiso sobre la CONFIGURACION del Space.")
        print("\nNo se ha cambiado nada y no se ha escrito ningun archivo.")
        return 1

    lineas = [
        "CONTRASENAS DEL SPACE DE LITERALEVEL",
        "",
        f"Aplicacion (para mandar):  {URL_APP}",
        f"Pagina del Space:          {URL_PAGINA}",
        "",
        "Generadas por tools/rotar_cuentas.py el 13 sep 2026. Sustituyen a todas las",
        "anteriores, que ya no funcionan. Son dos palabras y tres cifras, en",
        "minusculas y sin espacios, para poder teclearlas en el telefono. El usuario",
        "no distingue mayusculas; la contrasena si, y va toda en minusculas.",
        "",
        "ESTE ARCHIVO NO SE SUBE A GIT (esta en .gitignore). A cada persona, mandale",
        "solo su linea.",
        "",
        f"{'usuario':<12} {'contrasena':<18} {'tope':<11} que es",
        "-" * 76,
    ]
    for u, c, t, nota in filas:
        lineas.append(f"{u:<12} {c:<18} {('sin limite' if t == 0 else str(t)):<11} {nota}")
    lineas += [
        "",
        "El 'tope' es el numero de acciones DE PAGO: explicar una palabra en su",
        "frase, el resumen de '¿de que trata?' y la correccion de",
        "pronunciacion. Todo lo demas -medir un texto, buscar, leer el libro",
        "entero, la curva por capitulos, el diccionario y la fonetica- funciona",
        "sin entrar y no gasta nada.",
        "",
        "Para comprobar que el Space las acepto: abre la app, boton ⚙ Ajustes,",
        f"'Estado del servicio', y mira que diga 'Perfiles: {len(filas)} validos de",
        f"{len(filas)} declarados'.",
    ]
    texto = "\n".join(lineas) + "\n"
    for destino in DESTINOS:
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(texto, encoding="utf-8")
            print(f"escrito: {destino}")
        except OSError as e:
            print(f"no pude escribir {destino}: {type(e).__name__}")

    print(f"\nListo: {len(filas)} perfiles nuevos en el Space (no se imprimen aqui).")
    print("El Space se reinicia solo; tarda un par de minutos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
