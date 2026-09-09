"""Codigos de acceso a lo que cuesta dinero.

La aplicacion entera es libre: buscar, medir un libro, leerlo, el diccionario,
el cuestionario de nivel. **Nada de eso pide cuenta ni gasta un centimo.**

Lo que si cuesta son TRES cosas, porque van a la API de OpenAI: la explicacion
de una palabra en su contexto, la correccion de pronunciacion y el resumen de
"¿de que trata?" de la ficha. La tercera estuvo abierta sin codigo ni tope
durante un tiempo -la encontro una auditoria del codigo- y era la mas cara por
uso: cuatro pasajes de 900 palabras por pulsacion. Si se dejan
abiertas en una direccion publica, cualquiera puede agotar el saldo de Miguel
en una tarde. Y si se cierra la app entera detras de un inicio de sesion, se
pierde justo lo que hace util enseniarla: que alguien entre y la use sin
registrarse.

La solucion es un PERFIL: un usuario y una contrasena que se dan a una
persona concreta.

  - sin entrar -> la app funciona entera menos esas tres cosas, y lo dice
  - con perfil -> se activan, con un tope de usos por perfil

Antes esto era un codigo suelto tipo "QQHT-P5V2-V4DM". Se cambio porque un
codigo no le dice nada a quien lo recibe -no sabe si es suyo, ni cuanto le
queda- y porque la caja para canjearlo vivia dentro de un acordeon cerrado,
dentro de una de ocho pestanas: Miguel probo su propia aplicacion y no la
encontro. Un usuario y una contrasena se entienden sin explicacion, y el
saludo puede decir quien eres y cuanto te queda.

Los perfiles NO viven en el repositorio. Se leen de la variable de entorno
`LITERALEVEL_CUENTAS`, que en el Space es un secreto. Formato:

    usuario:contrasena:tope,usuario:contrasena:tope,...

`tope` es el numero de llamadas de pago permitidas; `0` significa sin limite.
Ejemplo:

    miguel:unaclavelarga:0,invitado1:otraclave:40

El recuento se guarda en un JSON junto a los datos del lector, y se comprueba
y se incrementa BAJO CANDADO en una sola operacion (`consumir`). Preguntar
primero y apuntar despues no valia: esta reproducido que con un tope de 2 y
veinte peticiones simultaneas pasaban las veinte.

Sigue sin ser una contabilidad seria: el candado es de proceso, no entre
procesos, y un reinicio del Space con almacenamiento efimero pierde la cuenta.
Cumple lo que tiene que cumplir -que un codigo suelto no vacie la cuenta- y no
mas.
"""
from __future__ import annotations

import hmac
import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path


# Candado de proceso para el contador de usos. Ver `consumir`.
_CANDADO = threading.Lock()

_SIN_CODIGO = ("Esta parte necesita que **entres con tu perfil** (arriba del "
               "todo, en «Entrar»). El resto de la aplicación —medir libros, "
               "leerlos, el diccionario y el cuestionario— funciona sin "
               "entrar.")


@dataclass(frozen=True)
class Cuenta:
    nombre: str
    tope: int          # 0 = sin limite


def _tabla() -> dict[str, tuple[str, Cuenta]]:
    """Perfiles declarados en el entorno: usuario -> (clave, cuenta).

    El usuario se compara en minusculas porque nadie recuerda si se lo dieron
    con mayuscula; la contrasena, tal cual, porque esa si es una credencial.
    """
    crudo = os.environ.get("LITERALEVEL_CUENTAS", "").strip()
    fuera: dict[str, tuple[str, Cuenta]] = {}
    for trozo in crudo.split(","):
        trozo = trozo.strip()
        if not trozo:
            continue
        partes = trozo.split(":")
        if len(partes) != 3:
            continue
        usuario, clave, tope = (p.strip() for p in partes)
        if not usuario or not clave:
            continue
        try:
            n = int(tope)
        except ValueError:
            n = 0
        fuera[usuario.lower()] = (clave, Cuenta(nombre=usuario, tope=max(0, n)))
    return fuera


def hay_codigos() -> bool:
    """Si no hay ningun perfil declarado, la puerta no existe y todo queda
    abierto. Es el caso del ordenador de casa: no hay a quien limitar."""
    return bool(_tabla())


def verificar(usuario: str | None, clave: str | None) -> Cuenta | None:
    """La cuenta si el usuario y la contrasena cuadran, o None.

    La comparacion de la clave es en tiempo constante. No es que aqui haya un
    secreto de Estado, pero comparar credenciales con `==` es una mala
    costumbre que se acaba copiando a sitios donde si importa.

    Y se compara SIEMPRE, exista el usuario o no, contra una clave falsa de
    relleno: si se saliera antes cuando el usuario no existe, el tiempo de
    respuesta diria cuales existen.
    """
    u = (usuario or "").strip().lower()
    c = (clave or "").strip()
    guardada, cuenta = _tabla().get(u, ("no-existe-este-usuario", None))
    coincide = hmac.compare_digest(c, guardada)
    return cuenta if (coincide and cuenta is not None) else None


def validar(credencial: str | None) -> Cuenta | None:
    """Compatibilidad: acepta "usuario:contrasena" en una sola cadena.

    La sesion guarda la credencial junta, y `consumir` la recibe asi.
    """
    if not credencial or ":" not in credencial:
        return None
    usuario, _, clave = credencial.partition(":")
    return verificar(usuario, clave)


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
    _sumar(base, cuenta)


def _sumar(base: Path, cuenta: Cuenta) -> int | None:
    """Suma un uso bajo candado y devuelve el total. None si no se pudo."""
    try:
        with _CANDADO:
            base = Path(base)
            base.mkdir(parents=True, exist_ok=True)
            d = _leer(base)
            total = d.get(cuenta.nombre, 0) + 1
            d[cuenta.nombre] = total
            tmp = _ruta_uso(base).with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f)
            os.replace(tmp, _ruta_uso(base))
            return total
    except Exception:
        return None


def consumir(base: Path, codigo: str | None) -> tuple[bool, str]:
    """Comprueba el cupo Y lo consume, en una sola operacion atomica.

    Esto existe porque `permite` seguido de `apuntar` NO es lo mismo, y el
    fallo esta reproducido: con un codigo de tope 2 y veinte peticiones
    simultaneas pasaban LAS VEINTE y el contador acababa en 1. Las veinte leian
    el mismo valor antes de que ninguna hubiera escrito. En una direccion
    publica eso convierte un cupo de 40 usos en barra libre.

    La comprobacion y el incremento van ahora dentro del mismo candado, y es el
    INCREMENTO el que decide: si al sumar el total supera el tope, la peticion
    se rechaza. Asi dos hilos no pueden obtener el mismo numero.

    El candado es de proceso, no entre procesos. Para un Space con un solo
    trabajador es suficiente; si algun dia se sirve con varios, esto hay que
    llevarlo a una base de datos con transaccion de verdad, y conviene que
    quede escrito aqui antes de que sorprenda a alguien.
    """
    if not hay_codigos():
        return True, ""
    cuenta = validar(codigo)
    if cuenta is None:
        return False, _SIN_CODIGO
    if cuenta.tope == 0:
        return True, ""
    total = _sumar(base, cuenta)
    if total is None:
        # No se pudo contar. Se deja pasar, como antes: es preferible regalar
        # un uso a tumbar la aplicacion porque el disco no admite escrituras.
        return True, ""
    if total > cuenta.tope:
        return False, (f"El código de **{cuenta.nombre}** ha agotado su cupo de "
                       f"{cuenta.tope} usos. El resto de la aplicación sigue "
                       "funcionando.")
    return True, ""


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
        return False, _SIN_CODIGO
    resto = queda(base, cuenta)
    if resto is not None and resto <= 0:
        return False, (f"El código de **{cuenta.nombre}** ha agotado su cupo de "
                       f"{cuenta.tope} usos. El resto de la aplicación sigue "
                       "funcionando.")
    return True, ""
