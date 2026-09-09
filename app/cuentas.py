"""Codigos de acceso a lo que cuesta dinero.

La aplicacion entera es libre: buscar, medir un libro, leerlo, el diccionario,
el cuestionario de nivel. **Nada de eso pide cuenta ni gasta un centimo.**

Lo que si cuesta son dos cosas, porque van a la API de OpenAI: la explicacion
de una palabra en su contexto y la correccion de pronunciacion. Si se dejan
abiertas en una direccion publica, cualquiera puede agotar el saldo de Miguel
en una tarde. Y si se cierra la app entera detras de un inicio de sesion, se
pierde justo lo que hace util enseniarla: que alguien entre y la use sin
registrarse.

La solucion es un codigo de acceso que se canjea dentro de la aplicacion:

  - sin codigo -> la app funciona entera menos esas dos cosas, y lo dice
  - con codigo -> se activan, con un tope de usos por codigo

Los codigos NO viven en el repositorio. Se leen de la variable de entorno
`LITERALEVEL_CUENTAS`, que en el Space es un secreto. Formato:

    nombre:codigo:tope,nombre:codigo:tope,...

`tope` es el numero de llamadas de pago permitidas; `0` significa sin limite.
Ejemplo:

    miguel:xxxxxxxx:0,prueba1:yyyyyyyy:60

El recuento se guarda en un JSON junto a los datos del lector. No es una
contabilidad seria -no hay bloqueo entre procesos y un reinicio del Space con
almacenamiento efimero lo pierde-, pero cumple lo que tiene que cumplir: que
un codigo suelto no pueda vaciar la cuenta.
"""
from __future__ import annotations

import hmac
import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Cuenta:
    nombre: str
    tope: int          # 0 = sin limite


def _tabla() -> dict[str, Cuenta]:
    """Codigos declarados en el entorno. Vacio si no hay ninguno."""
    crudo = os.environ.get("LITERALEVEL_CUENTAS", "").strip()
    fuera: dict[str, Cuenta] = {}
    for trozo in crudo.split(","):
        trozo = trozo.strip()
        if not trozo:
            continue
        partes = trozo.split(":")
        if len(partes) != 3:
            continue
        nombre, codigo, tope = (p.strip() for p in partes)
        if not codigo:
            continue
        try:
            n = int(tope)
        except ValueError:
            n = 0
        fuera[codigo] = Cuenta(nombre=nombre or "sin nombre", tope=max(0, n))
    return fuera


def hay_codigos() -> bool:
    """Si no hay ninguno declarado, la puerta no existe y todo queda abierto."""
    return bool(_tabla())


def validar(codigo: str | None) -> Cuenta | None:
    """La cuenta a la que corresponde el codigo, o None.

    La comparacion es en tiempo constante. No es que aqui haya un secreto de
    Estado, pero comparar credenciales con `==` es una mala costumbre que se
    acaba copiando a sitios donde si importa.
    """
    if not codigo:
        return None
    limpio = codigo.strip()
    for bueno, cuenta in _tabla().items():
        if hmac.compare_digest(limpio, bueno):
            return cuenta
    return None


def _ruta_uso(base: Path) -> Path:
    return Path(base) / "uso_openai.json"


def _leer(base: Path) -> dict[str, int]:
    try:
        with open(_ruta_uso(base), encoding="utf-8") as f:
            d = json.load(f)
        return {str(k): int(v) for k, v in d.items()}
    except Exception:
        return {}


def gastado(base: Path, nombre: str) -> int:
    return _leer(base).get(nombre, 0)


def queda(base: Path, cuenta: Cuenta) -> int | None:
    """Usos restantes, o None si la cuenta no tiene tope."""
    if cuenta.tope == 0:
        return None
    return max(0, cuenta.tope - gastado(base, cuenta.nombre))


def apuntar(base: Path, cuenta: Cuenta) -> None:
    """Suma un uso. Si no se puede escribir, se calla: cobrar bien es
    deseable, pero tumbar la aplicacion por no poder contar, no."""
    try:
        base = Path(base)
        base.mkdir(parents=True, exist_ok=True)
        d = _leer(base)
        d[cuenta.nombre] = d.get(cuenta.nombre, 0) + 1
        tmp = _ruta_uso(base).with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, _ruta_uso(base))
    except Exception:
        pass


def permite(base: Path, codigo: str | None) -> tuple[bool, str]:
    """(¿puede usar OpenAI?, motivo para ensenar al usuario).

    Si no hay codigos declarados, todo el mundo pasa: es el caso de la
    aplicacion corriendo en el ordenador de casa, donde no hay nadie a quien
    limitar.
    """
    if not hay_codigos():
        return True, ""
    cuenta = validar(codigo)
    if cuenta is None:
        return False, ("Esta parte necesita un **código de acceso**. El resto de "
                       "la aplicación —medir libros, leerlos, el diccionario y el "
                       "cuestionario— funciona sin él.")
    resto = queda(base, cuenta)
    if resto is not None and resto <= 0:
        return False, (f"El código de **{cuenta.nombre}** ha agotado su cupo de "
                       f"{cuenta.tope} usos. El resto de la aplicación sigue "
                       "funcionando.")
    return True, ""
