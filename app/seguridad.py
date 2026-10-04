"""Sesiones y reservas de gasto persistentes. No almacena claves ni texto de lectores.

Una reserva se confirma ANTES de salir al proveedor y nunca se devuelve por
timeout: una respuesta perdida puede haberse facturado. SQLite BEGIN IMMEDIATE
coordina procesos que comparten el mismo disco; no sirve para réplicas con discos
independientes. Los modelos y tamaños admitidos son una lista cerrada.
"""
from __future__ import annotations

import contextlib
import contextvars
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException
import config

SESION_SEGUNDOS = 8 * 60 * 60
RECUPERACION_SEGUNDOS = 15 * 60
CONTEXTO = contextvars.ContextVar("pleyade_cuenta", default=None)
MAX_AUDIO_SEGUNDOS = 180
_CLAVE_CACHE = secrets.token_bytes(32)
_SEMILLAS_VERIFICADAS = {}


def limite(nombre: str, defecto: int) -> int:
    # Una configuración inválida cierra la puerta, nunca significa ilimitado.
    try:
        return max(0, int(os.environ.get(nombre, str(defecto))))
    except ValueError:
        return 0


def negar(estado: int, mensaje: str):
    raise HTTPException(estado, mensaje)


def huella(valor: str) -> str:
    return hashlib.sha256(valor.encode()).hexdigest()


def hash_clave(clave: str, sal: str | None = None) -> str:
    sal = sal or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), 600_000)
    return sal + ":" + digest.hex()


def comprobar(clave: str, guardada: str) -> bool:
    return hmac.compare_digest(hash_clave(clave, guardada.split(":")[0]), guardada)


@contextlib.contextmanager
def transaccion(base: Path | None = None):
    db = None
    try:
        base = Path(base) if base is not None else config.dir_datos()
        base.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(base / "seguridad.sqlite3", timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        db.executescript("""
          CREATE TABLE IF NOT EXISTS cuentas (nombre TEXT PRIMARY KEY, clave TEXT NOT NULL, semilla TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1, tope INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS sesiones (hash TEXT PRIMARY KEY, nombre TEXT NOT NULL,
            version INTEGER NOT NULL, expira REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS recuperaciones (hash TEXT PRIMARY KEY, nombre TEXT NOT NULL,
            version INTEGER NOT NULL, expira REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS cargos (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL,
            momento REAL NOT NULL, centavos INTEGER NOT NULL, tipo TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS acciones (nombre TEXT PRIMARY KEY, usos INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS activos (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, expira REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS intentos (clave TEXT NOT NULL, momento REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS recursos (hash TEXT PRIMARY KEY, nombre TEXT NOT NULL,
            recurso TEXT NOT NULL, expira REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS permisos (nombre TEXT NOT NULL, recurso TEXT NOT NULL,
            PRIMARY KEY(nombre,recurso));
          CREATE INDEX IF NOT EXISTS cargos_nombre ON cargos(nombre, momento);
          CREATE INDEX IF NOT EXISTS intentos_clave ON intentos(clave, momento);
        """)
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.execute("COMMIT")
    except (OSError, sqlite3.Error):
        negar(503, "No se puede verificar la seguridad ahora. Las funciones de pago están bloqueadas.")
    finally:
        if db is not None:
            db.close()


@dataclass(frozen=True)
class Principal:
    nombre: str
    tope: int
    token_hash: str


def provisionar(tabla, usuario: str | None = None):
    """Importa cuentas nuevas y respeta rotaciones del secreto de aprovisionamiento.

    Las contraseñas heredadas permanecen en el secreto del Space hasta su retirada
    por el propietario. En la base nueva solo se conservan PBKDF2 con sal.
    """
    comprobadas = {}
    with transaccion() as db:
        existentes = {r["nombre"]: r for r in db.execute("SELECT * FROM cuentas")}
        for _, (clave, cuenta) in tabla.items():
            nombre = cuenta.nombre.lower()
            if not re.fullmatch(r"[a-z0-9_-]{1,64}", nombre):
                continue
            tope = min(cuenta.tope or 100, 100)
            marca = hmac.new(_CLAVE_CACHE, clave.encode(), "sha256").digest()
            if nombre not in existentes:
                guardada = hash_clave(clave)
                db.execute("INSERT INTO cuentas(nombre,clave,semilla,tope) VALUES(?,?,?,?)",
                           (nombre, guardada, guardada, tope))
                comprobadas[nombre] = marca
            elif usuario is None or nombre == usuario:
                db.execute("UPDATE cuentas SET tope=? WHERE nombre=?", (tope, nombre))
                if _SEMILLAS_VERIFICADAS.get(nombre) != marca:
                    if not comprobar(clave, existentes[nombre]["semilla"]):
                        _cambiar(db, nombre, clave)
                        db.execute("UPDATE cuentas SET semilla=? WHERE nombre=?", (hash_clave(clave), nombre))
                    comprobadas[nombre] = marca
    _SEMILLAS_VERIFICADAS.update(comprobadas)


def entrar(usuario: str, clave: str, ip: str, tabla) -> str:
    usuario = usuario.strip().lower()
    ahora = time.time()
    # Consumir intentos antes de la comparación: también limita carreras y aciertos.
    with transaccion() as db:
        db.execute("DELETE FROM intentos WHERE momento<?", (ahora - 3600,))
        for cubo, maximo in (("ip:" + huella(ip), 15), ("usuario:" + huella(usuario), 20), ("global", 100)):
            n = db.execute("SELECT count(*) FROM intentos WHERE clave=?", (cubo,)).fetchone()[0]
            if n >= maximo:
                negar(429, "Demasiados intentos. Vuelve a probar en una hora.")
        for cubo in ("ip:" + huella(ip), "usuario:" + huella(usuario), "global"):
            db.execute("INSERT INTO intentos VALUES(?,?)", (cubo, ahora))
    provisionar(tabla, usuario)
    with transaccion() as db:
        cuenta = db.execute("SELECT * FROM cuentas WHERE nombre=?", (usuario,)).fetchone() if usuario in tabla else None
        guardada = cuenta["clave"] if cuenta else hash_clave("cuenta inexistente", "00" * 16)
        if not comprobar(clave, guardada) or cuenta is None:
            negar(401, "No he podido entrar. Revisa el usuario y la contraseña.")
        token = secrets.token_urlsafe(32)
        db.execute("DELETE FROM sesiones WHERE expira<=?", (ahora,))
        db.execute("INSERT INTO sesiones VALUES(?,?,?,?)",
                   (huella(token), usuario, cuenta["version"], ahora + SESION_SEGUNDOS))
    return token


def resolver(token: str | None) -> Principal | None:
    if not token:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        negar(401, "La sesión no es válida. Vuelve a entrar.")
    with transaccion() as db:
        fila = db.execute("""SELECT c.nombre,c.tope FROM sesiones s JOIN cuentas c ON c.nombre=s.nombre
            WHERE s.hash=? AND s.expira>? AND s.version=c.version""", (huella(token), time.time())).fetchone()
    if fila is None:
        negar(401, "Tu sesión ha caducado. Vuelve a entrar.")
    import cuentas
    tabla = cuentas._tabla()
    if fila["nombre"] not in tabla:
        negar(401, "Esta cuenta ya no está habilitada.")
    provisionar(tabla, fila["nombre"])
    # Una rotación del secreto revoca también las sesiones ya emitidas.
    with transaccion() as db:
        fila = db.execute("""SELECT c.nombre,c.tope FROM sesiones s JOIN cuentas c ON c.nombre=s.nombre
            WHERE s.hash=? AND s.expira>? AND s.version=c.version""", (huella(token), time.time())).fetchone()
    if fila is None:
        negar(401, "La sesión se ha revocado. Vuelve a entrar.")
    return Principal(fila["nombre"], fila["tope"], huella(token))


def salir(token: str):
    with transaccion() as db:
        c = db.execute("SELECT nombre FROM sesiones WHERE hash=?", (huella(token),)).fetchone()
        if c:
            db.execute("DELETE FROM recursos WHERE nombre=?", (c[0],))
        db.execute("DELETE FROM sesiones WHERE hash=?", (huella(token),))


def nueva_clave(clave: str):
    if not 12 <= len(clave) <= 200:
        negar(422, "Usa una contraseña de entre 12 y 200 caracteres.")


def es_admin(principal: Principal | None) -> bool:
    permitidos = {n.strip().lower() for n in os.environ.get("LITERALEVEL_ADMIN_USUARIOS", "").split(",") if n.strip()}
    return principal is not None and principal.nombre in permitidos


def autorizar_admin(principal: Principal | None, actual: str):
    if not es_admin(principal):
        negar(403, "Esta función requiere una cuenta administradora.")
    with transaccion() as db:
        c = db.execute("SELECT clave FROM cuentas WHERE nombre=?", (principal.nombre,)).fetchone()
        if c is None or not comprobar(actual, c[0]):
            negar(401, "No se ha podido verificar tu contraseña actual.")


def cambiar(principal: Principal, actual: str, nueva: str) -> str:
    """Cambia la contraseña y devuelve una sesión nueva para ESTE dispositivo.

    `_cambiar` sigue revocando todas las sesiones anteriores (también la que hace
    el cambio), las recuperaciones y los enlaces a archivos. Antes aquí acababa
    todo y el que cambiaba la clave aparecía fuera de la app y volvía a ver el
    formulario de entrar, como si se la pidieran otra vez (Miguel, demo del 4 oct
    2026). La sesión nueva se emite en la misma transacción, con la versión ya
    incrementada de la cuenta, exactamente como en `entrar`.
    """
    nueva_clave(nueva)
    ahora = time.time()
    with transaccion() as db:
        c = db.execute("SELECT clave FROM cuentas WHERE nombre=?", (principal.nombre,)).fetchone()
        if c is None or not comprobar(actual, c["clave"]):
            negar(401, "La contraseña actual no coincide.")
        _cambiar(db, principal.nombre, nueva)
        version = db.execute("SELECT version FROM cuentas WHERE nombre=?", (principal.nombre,)).fetchone()[0]
        token = secrets.token_urlsafe(32)
        db.execute("INSERT INTO sesiones VALUES(?,?,?,?)",
                   (huella(token), principal.nombre, version, ahora + SESION_SEGUNDOS))
    return token


def _cambiar(db, nombre, clave):
    db.execute("UPDATE cuentas SET clave=?,version=version+1 WHERE nombre=?", (hash_clave(clave), nombre))
    db.execute("DELETE FROM sesiones WHERE nombre=?", (nombre,))
    db.execute("DELETE FROM recuperaciones WHERE nombre=?", (nombre,))
    db.execute("DELETE FROM recursos WHERE nombre=?", (nombre,))


def permitir_recurso(recurso: str) -> str | None:
    principal = CONTEXTO.get()
    if principal is None:
        return None
    token = secrets.token_urlsafe(32)
    with transaccion() as db:
        db.execute("DELETE FROM recursos WHERE expira<=?", (time.time(),))
        db.execute("INSERT OR IGNORE INTO permisos VALUES(?,?)", (principal.nombre, recurso))
        db.execute("INSERT INTO recursos VALUES(?,?,?,?)",
                   (huella(token), principal.nombre, recurso, time.time() + 900))
    return token


def tiene_recurso(principal: Principal | None, recurso: str) -> bool:
    if principal is None:
        return False
    with transaccion() as db:
        return db.execute("SELECT 1 FROM permisos WHERE nombre=? AND recurso=?",
                          (principal.nombre, recurso)).fetchone() is not None


def validar_recurso(recurso: str, token: str):
    with transaccion() as db:
        fila = db.execute("SELECT 1 FROM recursos WHERE hash=? AND recurso=? AND expira>?",
                          (huella(token), recurso, time.time())).fetchone()
    if fila is None:
        negar(403, "No tienes acceso a este archivo o el enlace ha caducado.")


def recurso_para_trabajador(recurso: str) -> str | None:
    """Capacidad breve para la cola autenticada; nunca publica un archivo sin dueño."""
    token = secrets.token_urlsafe(32)
    with transaccion() as db:
        fila = db.execute("SELECT nombre FROM permisos WHERE recurso=? LIMIT 1", (recurso,)).fetchone()
        if fila is None:
            return None
        db.execute("INSERT INTO recursos VALUES(?,?,?,?)",
                   (huella(token), fila[0], recurso, time.time() + 900))
    return token


def emitir_recuperacion(nombre: str) -> str:
    """Solo operador desde el servidor. No hay endpoint público de emisión."""
    with transaccion() as db:
        c = db.execute("SELECT version FROM cuentas WHERE nombre=?", (nombre.lower(),)).fetchone()
        if c is None:
            negar(404, "Cuenta inexistente.")
        token = secrets.token_urlsafe(32)
        db.execute("DELETE FROM recuperaciones WHERE nombre=?", (nombre.lower(),))
        db.execute("INSERT INTO recuperaciones VALUES(?,?,?,?)",
                   (huella(token), nombre.lower(), c[0], time.time() + RECUPERACION_SEGUNDOS))
        return token


def recuperar(token: str, nueva: str):
    nueva_clave(nueva)
    with transaccion() as db:
        c = db.execute("""SELECT r.nombre FROM recuperaciones r JOIN cuentas c ON c.nombre=r.nombre
            WHERE r.hash=? AND r.expira>? AND r.version=c.version""", (huella(token), time.time())).fetchone()
        if c is None:
            negar(401, "El código de recuperación ha caducado o ya se usó.")
        _cambiar(db, c[0], nueva)


def usos(base: Path, nombre: str) -> int:
    with transaccion(base) as db:
        fila = db.execute("SELECT usos FROM acciones WHERE nombre=?", (nombre.lower(),)).fetchone()
        if fila:
            return fila[0]
        # Migrar el contador anterior sin ponerlo a cero. JSON corrupto: bloquear.
        ruta = Path(base) / "uso_openai.json"
        try:
            previo = json.loads(ruta.read_text("utf-8")) if ruta.exists() else {}
            n = next((int(v) for k, v in previo.items() if k.lower() == nombre.lower()), 0)
        except (OSError, ValueError, AttributeError):
            negar(503, "No se puede verificar tu cuota. El gasto está bloqueado.")
        db.execute("INSERT INTO acciones VALUES(?,?)", (nombre.lower(), max(0, n)))
        return max(0, n)


def consumir(base: Path, cuenta) -> tuple[bool, str]:
    usos(base, cuenta.nombre)
    tope = min(cuenta.tope or 100, 100)
    with transaccion(base) as db:
        n = db.execute("SELECT usos FROM acciones WHERE nombre=?", (cuenta.nombre.lower(),)).fetchone()[0]
        if n >= tope:
            return False, "Has agotado tu cupo de usos. Las funciones gratuitas siguen disponibles."
        db.execute("UPDATE acciones SET usos=usos+1 WHERE nombre=?", (cuenta.nombre.lower(),))
    return True, ""


def devolver(nombre: str, base: Path | None = None):
    with transaccion(base) as db:
        db.execute("UPDATE acciones SET usos=max(0,usos-1) WHERE nombre=?", (nombre.lower(),))


@contextlib.contextmanager
def operacion(principal: Principal):
    ahora = time.time()
    ident = secrets.token_hex(16)
    with transaccion() as db:
        db.execute("DELETE FROM activos WHERE expira<=?", (ahora,))
        if db.execute("SELECT count(*) FROM activos WHERE nombre=?", (principal.nombre,)).fetchone()[0]:
            negar(429, "Ya hay una operación de pago en curso en tu cuenta.")
        if db.execute("SELECT count(*) FROM activos").fetchone()[0] >= 2:
            negar(429, "El servicio de pago está ocupado. Prueba en un momento.")
        # Lease supera el límite de toda petición (los SDK tienen timeout y cero retries).
        db.execute("INSERT INTO activos VALUES(?,?,?)", (ident, principal.nombre, ahora + 1800))
    token = CONTEXTO.set(principal)
    try:
        yield
    finally:
        CONTEXTO.reset(token)
        with transaccion() as db:
            db.execute("DELETE FROM activos WHERE id=?", (ident,))


def reservar(centavos: int, tipo: str):
    principal = CONTEXTO.get()
    if principal is None:
        negar(403, "Las llamadas de pago requieren una sesión autenticada en el servidor.")
    ahora = time.time()
    dia = int(ahora // 86400) * 86400
    with transaccion() as db:
        # Revalidar revocación/caducidad, incluso entre llamadas de una misma petición.
        valido = db.execute("""SELECT 1 FROM sesiones s JOIN cuentas c ON c.nombre=s.nombre
            WHERE s.hash=? AND s.expira>? AND s.version=c.version""", (principal.token_hash, ahora)).fetchone()
        if not valido:
            negar(401, "La sesión ya no es válida.")
        total, diario = db.execute("SELECT coalesce(sum(centavos),0),coalesce(sum(CASE WHEN momento>=? THEN centavos ELSE 0 END),0) FROM cargos", (dia,)).fetchone()
        if total + centavos > limite("LITERALEVEL_PRESUPUESTO_TOTAL_CENTAVOS", 2000) or diario + centavos > limite("LITERALEVEL_PRESUPUESTO_DIA_CENTAVOS", 500):
            negar(429, "Se ha alcanzado el presupuesto del servicio. Leer y el diccionario siguen disponibles.")
        cuenta_total, cuenta_dia, hora, minuto = db.execute("""SELECT count(*),
            coalesce(sum(momento>=?),0), coalesce(sum(momento>=?),0), coalesce(sum(momento>=?),0)
            FROM cargos WHERE nombre=?""", (dia, ahora - 3600, ahora - 60, principal.nombre)).fetchone()
        if cuenta_total >= 200 or cuenta_dia >= 40 or hora >= 30 or minuto >= 6:
            negar(429, "Has alcanzado el límite de llamadas de pago de tu cuenta.")
        db.execute("INSERT INTO cargos(nombre,momento,centavos,tipo) VALUES(?,?,?,?)",
                   (principal.nombre, ahora, centavos, tipo))


def audio_acotado(archivo):
    """Decodifica localmente: duración real, sin confiar en extensión/metadata.

    Se envía WAV normalizado, con protocolos de red deshabilitados. El proceso
    tiene plazo y salida acotados; no se envía el archivo original al proveedor.
    """
    ruta = getattr(archivo, "name", None)
    if not isinstance(ruta, str) or not Path(ruta).is_file() or Path(ruta).stat().st_size > 12 * 1024 * 1024:
        negar(422, "No se puede validar esta grabación.")
    ejecutable = shutil.which("ffmpeg")
    if not ejecutable:
        try:
            import imageio_ffmpeg
            ejecutable = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            negar(503, "No se puede verificar la duración del audio ahora.")
    try:
        r = subprocess.run([ejecutable, "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe",
            "-format_whitelist", "wav,mp3,ogg,matroska,webm,mov,flac,aac",
            "-i", ruta, "-t", str(MAX_AUDIO_SEGUNDOS + 1), "-vn", "-ac", "1", "-ar", "16000",
            "-f", "s16le", "pipe:1"], capture_output=True, timeout=20, check=True)
    except (subprocess.SubprocessError, OSError):
        negar(422, "La grabación no es un audio válido.")
    if not r.stdout or len(r.stdout) > MAX_AUDIO_SEGUNDOS * 32000:
        negar(413, "La grabación supera los tres minutos permitidos.")
    salida = io.BytesIO()
    with wave.open(salida, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(r.stdout)
    return ("grabacion.wav", salida.getvalue(), "audio/wav")


class ClienteProtegido:
    """Solo cuatro operaciones admitidas; cada llamada reserva su peor coste.

    Límites conservadores (USD): texto 0.25, TTS 0.10, transcripción 0.05.
    Tarifas de modelos legacy + margen; ninguna herramienta, tier prioritario,
    modelo nuevo ni reintento está autorizado por esta lista.
    """
    def __init__(self, cliente):
        self.responses = SimpleNamespace(parse=lambda **kw: self._llamar(cliente.responses.parse, "texto", kw))
        self.chat = SimpleNamespace(completions=SimpleNamespace(parse=lambda **kw: self._llamar(cliente.chat.completions.parse, "chat", kw)))
        self.audio = SimpleNamespace(
            speech=SimpleNamespace(create=lambda **kw: self._llamar(cliente.audio.speech.create, "tts", kw)),
            transcriptions=SimpleNamespace(create=lambda **kw: self._llamar(cliente.audio.transcriptions.create, "audio", kw)))

    def _llamar(self, funcion, tipo, kw):
        if CONTEXTO.get() is None:
            negar(403, "Hace falta una sesión autenticada para generar contenido de pago.")
        if tipo in ("texto", "chat"):
            if kw.get("model") not in ("gpt-5", "gpt-4o-mini") or any(k in kw for k in ("tools", "previous_response_id", "conversation", "stream", "background")):
                negar(403, "Operación de proveedor no autorizada.")
            texto = json.dumps({k: kw.get(k) for k in ("input", "instructions", "messages")}, ensure_ascii=False)
            if len(texto.encode()) > 32768:
                negar(413, "El texto supera el tamaño permitido.")
            kw["max_output_tokens" if tipo == "texto" else "max_completion_tokens"] = 2048
            kw["service_tier"] = "default"
            kw["store"] = False
            if tipo == "chat":
                kw["n"] = 1
            costo = 25
        elif tipo == "tts":
            if kw.get("model") != "tts-1" or len(kw.get("input", "")) > 4000:
                negar(413, "El audio solicitado supera el tamaño permitido.")
            costo = 10
        else:
            if kw.get("model") != "whisper-1":
                negar(403, "Modelo de transcripción no autorizado.")
            kw["file"] = audio_acotado(kw.get("file"))
            costo = 5
        reservar(costo, tipo)
        return funcion(**kw)
