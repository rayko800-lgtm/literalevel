"""Acceso a funciones de pago con cuentas administradas.

El entorno declara las cuentas habilitadas. La API autentica mediante sesiones
revocables; X-Lector no concede acceso a una cuenta. SQLite conserva los usos
y migra uso_openai.json sin reiniciarlo. Toda cuota es finita (máximo 100):
un tope heredado 0 se interpreta como 100. Los fallos de almacenamiento bloquean
el gasto. ClienteProtegido aplica además reservas globales y por llamada.

LITERALEVEL_CUENTAS_AUDITORIA permite cuentas sintéticas temporales con el mismo
contrato; retirarlo deshabilita sus sesiones. Los helpers JSON restantes son
compatibilidad local y no autorizan llamadas al proveedor.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import sys
import threading
import seguridad
from dataclasses import dataclass
from datetime import datetime, timezone
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
    tope: int          # 0 heredado se limita a 100


def _analizar(crudo: str, con_nombre: bool = True,
              ) -> tuple[dict[str, tuple[str, Cuenta]], list[str]]:
    """Lee el secreto y, sobre todo, DICE lo que descarta.

    Descartar en silencio no era un fallo de seguridad, era uno de
    diagnostico, y de los peores: este secreto se edita a ciegas en el panel
    del Space, asi que una entrada con un `:` de mas dejaba a ese perfil sin
    existir y no habia forma de enterarse. El caso caro es el usuario
    repetido: no desaparece el perfil, cambia su contrasena, y quien tenia la
    otra recibe el mismo "No he podido entrar" que un impostor.

    Ningun aviso lleva la contrasena. Se dice la POSICION de la entrada y el
    motivo, que es lo que hace falta para arreglar el secreto.

    `con_nombre` decide si ademas sale el nombre de usuario, y existe porque
    estos avisos van a DOS sitios: al registro del Space, que solo lee el
    dueno, y a la pestana «Estado», que es publica. En la publica no puede
    salir: ahorrarle al que prueba contrasenas la mitad del trabajo -saber
    que usuarios existen- no cuesta nada, y el numero de entrada basta para
    encontrarla en el secreto.
    """
    fuera: dict[str, tuple[str, Cuenta]] = {}
    avisos: list[str] = []

    def con(usuario: str) -> str:
        return f" ({usuario})" if con_nombre else ""
    for i, trozo in enumerate(crudo.split(","), start=1):
        trozo = trozo.strip()
        if not trozo:
            continue
        partes = trozo.split(":")
        if len(partes) != 3:
            avisos.append(f"entrada {i}: {len(partes)} campos en vez de 3 "
                          "(¿un «:» dentro de la contraseña?); descartada")
            continue
        usuario, clave, tope = (p.strip() for p in partes)
        if not usuario or not clave:
            avisos.append(f"entrada {i}: usuario o contraseña vacíos; "
                          "descartada")
            continue
        try:
            n = int(tope)
        except ValueError:
            avisos.append(f"entrada {i}: tope inválido; descartada")
            continue
        if n < 0 or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", usuario):
            avisos.append(f"entrada {i}: usuario o tope inválido; descartada")
            continue
        u = usuario.lower()
        if u in fuera:
            avisos.append(f"entrada {i}{con(usuario)}: repite un usuario ya "
                          "declarado; gana esta, y la contraseña de la otra "
                          "deja de servir")
        fuera[u] = (clave, Cuenta(nombre=usuario, tope=max(0, n)))
    return fuera, avisos


_YA_AVISADO = False


def _tabla() -> dict[str, tuple[str, Cuenta]]:
    """Perfiles declarados en el entorno: usuario -> (clave, cuenta).

    El usuario se compara en minusculas porque nadie recuerda si se lo dieron
    con mayuscula; la contrasena, tal cual, porque esa si es una credencial.
    """
    global _YA_AVISADO
    crudo = ",".join(filter(None, (os.environ.get("LITERALEVEL_CUENTAS", "").strip(),
                                  os.environ.get("LITERALEVEL_CUENTAS_AUDITORIA", "").strip())))
    fuera, avisos = _analizar(crudo)
    # Una vez por proceso, no en cada `verificar`: esto se llama en cada
    # intento de entrar y el registro del Space no necesita la misma queja
    # cien veces. La carrera con otro hilo solo puede duplicar una linea.
    if avisos and not _YA_AVISADO:
        _YA_AVISADO = True
        for a in avisos:
            print(f"LITERALEVEL_CUENTAS, {a}", file=sys.stderr)
    return fuera


def problemas() -> list[str]:
    """Los avisos de la tabla para la pestana «Estado», que es PUBLICA.

    Sin contrasenas y sin nombres de usuario: solo el numero de entrada y el
    motivo. Con nombre van al registro del Space, que no lee cualquiera.
    """
    return _analizar(os.environ.get("LITERALEVEL_CUENTAS", "").strip(),
                     con_nombre=False)[1]


def declaradas() -> int:
    """Entradas no vacias que declara el secreto, validas o no."""
    crudo = os.environ.get("LITERALEVEL_CUENTAS", "").strip()
    return len([t for t in crudo.split(",") if t.strip()])


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
    # En BYTES, no en str. `hmac.compare_digest` con cadenas solo admite
    # ASCII y lanza TypeError con cualquier otra cosa: una contrasena con
    # ene, tilde o emoji tiraba la funcion y el usuario veia "Error"
    # pelado. Un perfil declarado con ene no podia entrar NUNCA.
    coincide = hmac.compare_digest(c.encode("utf-8"), guardada.encode("utf-8"))
    return cuenta if (coincide and cuenta is not None) else None


def validar(credencial: str | None) -> Cuenta | None:
    """Compatibilidad: acepta "usuario:contrasena" en una sola cadena.

    La sesion guarda la credencial junta, y `consumir` la recibe asi.
    """
    if not credencial or ":" not in credencial:
        return None
    if credencial.startswith("sesion:"):
        p = seguridad.resolver(credencial.partition(":")[2])
        return Cuenta(p.nombre, p.tope) if p else None
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
    return seguridad.usos(base, nombre)


def queda(base: Path, cuenta: Cuenta) -> int | None:
    """Usos restantes; las cuentas heredadas sin tope se limitan a 100."""
    return max(0, min(cuenta.tope or 100, 100) - gastado(base, cuenta.nombre))


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


def _restar_ya_con_candado(base: Path, cuenta: Cuenta) -> bool:
    """Baja un uso sin bajar de cero; quien llama ya tiene `_CANDADO` (no es reentrante).
    True si bajo. Puede lanzar: quien llama decide."""
    b = Path(base)
    d = _leer(b)
    actual = d.get(cuenta.nombre, 0)
    if actual <= 0:
        return False
    d[cuenta.nombre] = actual - 1
    tmp = _ruta_uso(b).with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f)
    os.replace(tmp, _ruta_uso(b))
    return True


def _restar(base: Path, cuenta: Cuenta) -> None:
    """Baja un uso, sin bajar nunca de cero. Bajo el mismo candado que `_sumar`."""
    try:
        seguridad.devolver(cuenta.nombre, base)
    except Exception:
        # Si no se puede devolver, el lector pierde un uso. Es lo malo menos
        # malo: lo contrario seria no cobrar por no poder escribir.
        return


def devolver(base: Path, codigo: str | None) -> None:
    """Devuelve un uso ya cobrado, cuando resulta que no se pago nada.

    `consumir` cobra ANTES de llamar a OpenAI, y tiene que ser asi: preguntar
    primero y apuntar despues abre la condicion de carrera que ese docstring
    explica. Pero entonces una consulta que sale de la cache de `lexicon.db`
    -sin una sola llamada a la API- bajaba el contador igual, y `tope` dejaba
    de ser "llamadas de pago permitidas", como se declara arriba, para ser
    "pulsaciones".

    Asi que se cobra siempre y se devuelve cuando se sabe que no hubo gasto.
    Nunca baja de cero: si dos hilos devolvieran a la vez sobre un contador ya
    en cero, el cupo se volveria mas generoso de lo declarado.
    """
    if not hay_codigos():
        return
    cuenta = validar(codigo)
    if cuenta is None:
        return
    _restar(base, cuenta)


# Devoluciones por silencio al dia por cuenta (Central, reinicio 26). A partir de aqui no se
# devuelve y se anota: grabar silencio a proposito no puede convertir un cupo en barra libre.
MAX_DEVOLUCIONES_SILENCIO = 10


def _ruta_devoluciones(base: Path) -> Path:
    return Path(base) / "devoluciones_silencio.json"


def devolver_por_silencio(base: Path, codigo: str | None, hoy: str | None = None) -> bool:
    """Nunca devuelve una transcripción potencialmente facturada."""
    # Una transcripción de silencio puede estar facturada. No se devuelve.
    return False


def consumir(base: Path, codigo: str | None) -> tuple[bool, str]:
    """Reserva un uso de forma atómica en SQLite; sin cuenta o sin disco bloquea."""
    cuenta = validar(codigo)
    if cuenta is None:
        return False, _SIN_CODIGO
    return seguridad.consumir(base, cuenta)


def permite(base: Path, codigo: str | None) -> tuple[bool, str]:
    """Comprueba identidad y cuota finita; consumir debe reservar antes de generar."""
    cuenta = validar(codigo)
    if cuenta is None:
        return False, _SIN_CODIGO
    resto = queda(base, cuenta)
    if resto is not None and resto <= 0:
        return False, (f"El perfil de **{cuenta.nombre}** ha agotado su cupo de "
                       f"{cuenta.tope} usos. El resto de la aplicación sigue "
                       "funcionando.")
    return True, ""
