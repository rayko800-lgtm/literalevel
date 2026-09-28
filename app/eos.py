"""Eos en Pronunciar: vídeos de la cara que habla para los audios NUEVOS.

Los 85 sonidos del AFI (41 GA + 44 RP) van PREGRABADOS en el front
(`front/public/eos/<acento>/<archivo>.mp4`, `tools/eos_pronunciar/`): Vercel los
sirve y este módulo no interviene. Lo que Eos no puede tener grabado es la frase
que el lector acaba de leer (`audio_correcto`, el mp3 que genera `voz.py` con
tts-1 y cachea por contenido en `dir_datos()/audio`). El Space gratis no tiene
ni GPU ni Chrome para animarla y grabarla: se genera POR FUERA.

    lector →  POST /api/eos/pedir {audio, texto}   → «pendiente» (o «listo» si ya está)
    PC con Eos (tools/eos_pronunciar/trabajador.py, con LITERALEVEL_EOS_TOKEN):
              GET  /api/eos/cola                    → trabajos pendientes
              POST /api/eos/entregar/<clave>        → el mp4
    lector →  GET  /api/eos/estado/<clave>          → «listo» + /api/eos/video/<clave>.mp4

Sin token en el servidor no hay trabajador: `pedir` contesta «sin_trabajador» y el
front no hace esperar a nadie. Todo lo que se escribe cuelga de `dir_datos()/eos`
(el disco persistente del Space): `cola/<clave>.json` mientras se hace y
`<clave>.mp4` al terminar. Nada de esto llama a OpenAI ni cobra usos.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
from pathlib import Path

import config

TOKEN_ENV = "LITERALEVEL_EOS_TOKEN"
TOPE_MP4 = 25 * 1024 * 1024
_NOMBRE_AUDIO = re.compile(r"[\w.-]{1,160}\.mp3")
_CLAVE = re.compile(r"[0-9a-f]{24}")
# Un trabajo fallido se puede volver a pedir pasado este tiempo (el PC estaba apagado, etc.).
REINTENTO_FALLO_S = 15 * 60


def dir_eos() -> Path:
    return config.dir_datos() / "eos"


def _dir_cola() -> Path:
    return dir_eos() / "cola"


def hay_trabajador() -> bool:
    return bool(os.environ.get(TOKEN_ENV, "").strip())


def token_valido(token: str | None) -> bool:
    esperado = os.environ.get(TOKEN_ENV, "").strip()
    return bool(esperado) and isinstance(token, str) and hmac.compare_digest(token.strip(), esperado)


def clave_de(nombre_audio: str) -> str:
    """La clave del vídeo sale del NOMBRE del mp3, que `voz.py` ya forma con el hash
    del texto y la voz: la misma frase pedida dos veces es el mismo vídeo."""
    return hashlib.sha256(nombre_audio.encode("utf-8")).hexdigest()[:24]


def nombre_audio_valido(nombre: object) -> bool:
    return isinstance(nombre, str) and bool(_NOMBRE_AUDIO.fullmatch(nombre)) and ".." not in nombre


def clave_valida(clave: object) -> bool:
    return isinstance(clave, str) and bool(_CLAVE.fullmatch(clave))


def ruta_video(clave: str) -> Path:
    return dir_eos() / f"{clave}.mp4"


def _ruta_trabajo(clave: str) -> Path:
    return _dir_cola() / f"{clave}.json"


def _leer_trabajo(clave: str) -> dict | None:
    try:
        with open(_ruta_trabajo(clave), encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else None
    except (OSError, ValueError):
        return None


def _escribir_trabajo(datos: dict) -> None:
    _dir_cola().mkdir(parents=True, exist_ok=True)
    tmp = _ruta_trabajo(datos["clave"]).with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    os.replace(tmp, _ruta_trabajo(datos["clave"]))


def _respuesta(clave: str, estado: str, **mas) -> dict:
    r = {"estado": estado, "clave": clave, "video": None}
    if estado == "listo":
        r["video"] = f"/api/eos/video/{clave}.mp4"
    r.update(mas)
    return r


def estado(clave: str) -> dict:
    """listo | pendiente | fallo | no (nadie lo pidió) | sin_trabajador."""
    if not clave_valida(clave):
        return _respuesta("", "no")
    p = ruta_video(clave)
    if p.is_file() and p.stat().st_size > 0:
        return _respuesta(clave, "listo")
    t = _leer_trabajo(clave)
    if t is None:
        return _respuesta(clave, "no")
    if t.get("estado") == "fallo":
        return _respuesta(clave, "fallo", motivo=str(t.get("motivo") or ""))
    if not hay_trabajador():
        return _respuesta(clave, "sin_trabajador")
    return _respuesta(clave, "pendiente")


def pedir(nombre_audio: str, texto: str = "") -> dict:
    """Encola el vídeo de un mp3 de `dir_datos()/audio`. Idempotente: si ya está
    hecho contesta «listo»; si está en cola, «pendiente»; sin trabajador, lo
    deja apuntado igual (por si se enciende) pero contesta «sin_trabajador»."""
    if not nombre_audio_valido(nombre_audio):
        return _respuesta("", "no")
    clave = clave_de(nombre_audio)
    p = ruta_video(clave)
    if p.is_file() and p.stat().st_size > 0:
        return _respuesta(clave, "listo")
    t = _leer_trabajo(clave)
    ahora = time.time()
    if t is not None and t.get("estado") == "fallo" and ahora - float(t.get("actualizado") or 0) < REINTENTO_FALLO_S:
        return _respuesta(clave, "fallo", motivo=str(t.get("motivo") or ""))
    if t is None or t.get("estado") == "fallo":
        _escribir_trabajo({"clave": clave, "audio": nombre_audio, "texto": str(texto or "")[:600],
                           "estado": "pendiente", "pedido": ahora, "actualizado": ahora})
    return _respuesta(clave, "pendiente" if hay_trabajador() else "sin_trabajador")


def cola() -> list[dict]:
    """Los trabajos pendientes, los más antiguos primero. Para el trabajador."""
    out = []
    try:
        archivos = sorted(_dir_cola().glob("*.json"))
    except OSError:
        return out
    for a in archivos:
        t = _leer_trabajo(a.stem)
        if t and t.get("estado") == "pendiente" and clave_valida(t.get("clave")):
            out.append({"clave": t["clave"], "audio": t.get("audio"), "texto": t.get("texto", ""),
                        "pedido": t.get("pedido")})
    out.sort(key=lambda t: float(t.get("pedido") or 0))
    return out


def es_mp4(contenido: bytes) -> bool:
    """Caja `ftyp` al principio: lo que sube el trabajador es un mp4, no otra cosa."""
    return len(contenido) > 12 and contenido[4:8] == b"ftyp"


def entregar(clave: str, contenido: bytes) -> bool:
    if not clave_valida(clave) or not es_mp4(contenido) or len(contenido) > TOPE_MP4:
        return False
    dir_eos().mkdir(parents=True, exist_ok=True)
    destino = ruta_video(clave)
    tmp = destino.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        f.write(contenido)
    os.replace(tmp, destino)
    try:
        os.unlink(_ruta_trabajo(clave))
    except OSError:
        pass
    return True


def fallo(clave: str, motivo: str = "") -> bool:
    t = _leer_trabajo(clave) if clave_valida(clave) else None
    if t is None:
        return False
    t.update(estado="fallo", motivo=str(motivo or "")[:300], actualizado=time.time())
    _escribir_trabajo(t)
    return True
