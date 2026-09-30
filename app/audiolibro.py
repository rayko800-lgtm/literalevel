"""Fragmentos de lectura y caché persistente de voz, sin historial compartido."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path

import voz

TOPE_CARACTERES = 2400
VERSION = "lectura-1"


def fragmentos(texto: str) -> list[str]:
    partes = []
    resto = texto.strip()
    while resto:
        corte = min(len(resto), TOPE_CARACTERES)
        if corte < len(resto):
            # Preferir una oración completa; en prosa sin puntuación, una palabra.
            finales = list(re.finditer(r'[.!?][\"”\u2019\u0027)]*\s+', resto[:corte]))
            corte_frase = finales[-1].end() if finales else 0
            if corte_frase >= TOPE_CARACTERES // 2:
                corte = corte_frase
            else:
                espacio = resto.rfind(" ", 0, corte)
                if espacio > 0:
                    corte = espacio
        partes.append(resto[:corte].strip())
        resto = resto[corte:].strip()
    return partes


def clave(texto: str) -> str:
    return hashlib.sha256("\x1f".join(
        (VERSION, voz.MODELO_VOZ, voz.VOZ_POR_DEFECTO, texto)).encode()).hexdigest()


def ruta(base: Path, ident: str) -> Path:
    return base / "audiolibro" / f"{ident}.mp3"


def guardado(base: Path, ident: str) -> bool:
    p = ruta(base, ident)
    return p.is_file() and p.stat().st_size > 0


def marcas(texto: str, datos: dict | None) -> tuple[list[dict], bool]:
    """Alinear las marcas al texto original, conservando puntuación y espacios."""
    tokens = re.findall(r"\S+\s*", texto)
    normales, propietarios = [], []
    for i, token in enumerate(tokens):
        for palabra in voz.normalizar_palabras(token):
            normales.append(palabra)
            propietarios.append(i)
    alineadas = voz._tiempos_por_indice(normales, datos)
    por_token = {}
    for i, (inicio, fin) in alineadas.items():
        if math.isfinite(inicio) and math.isfinite(fin) and 0 <= inicio <= fin:
            t = propietarios[i]
            anterior = por_token.get(t, (inicio, fin))
            por_token[t] = (min(anterior[0], inicio), max(anterior[1], fin))
    # Los huecos se interpolan entre palabras reconocidas. Sin marcas se usa
    # la duración real del reproductor en el cliente, sin otra llamada pagada.
    duracion = (datos or {}).get("duracion")
    if not isinstance(duracion, (int, float)) or not math.isfinite(duracion) or duracion <= 0:
        return [], True
    resultado, cursor = [], 0.0
    for i, token in enumerate(tokens):
        if i in por_token:
            inicio, fin = por_token[i]
            inicio = max(cursor, inicio)
            fin = max(inicio, fin)
        else:
            siguiente = next((j for j in range(i + 1, len(tokens)) if j in por_token), len(tokens))
            hasta = por_token[siguiente][0] if siguiente < len(tokens) else duracion
            peso = max(1, len(token.strip()))
            total = sum(max(1, len(t.strip())) for t in tokens[i:siguiente])
            inicio, fin = cursor, cursor + max(0, hasta - cursor) * peso / total
        resultado.append({"texto": token, "inicio": inicio, "fin": fin})
        cursor = fin
    return resultado, len(por_token) != len(tokens)


def leer_marcas(base: Path, ident: str) -> dict:
    try:
        return json.loads(ruta(base, ident).with_suffix(".json").read_text("utf-8"))
    except (OSError, ValueError):
        return {"palabras": [], "aproximado": True}


def generar(base: Path, texto: str) -> None:
    """Llamar solo tras reservar cuota y adquirir el candado de esta clave."""
    destino = ruta(base, clave(texto))
    cliente = voz._cliente()
    if cliente is None:
        raise RuntimeError("Sin voz disponible")
    respuesta = cliente.audio.speech.create(
        model=voz.MODELO_VOZ, voice=voz.VOZ_POR_DEFECTO,
        input=texto, response_format="mp3")
    voz._escribir_audio_atomico(respuesta, destino)
    try:
        datos = voz.transcribir_con_tiempos(str(destino))
        palabras, aproximado = marcas(texto, datos)
    except Exception:
        palabras, aproximado = [], True
    descriptor, temporal = tempfile.mkstemp(dir=destino.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as f:
            json.dump({"palabras": palabras, "aproximado": aproximado}, f, ensure_ascii=False)
        os.replace(temporal, destino.with_suffix(".json"))
    finally:
        Path(temporal).unlink(missing_ok=True)
