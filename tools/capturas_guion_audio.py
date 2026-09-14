"""Genera el audio (WAV) que Chrome usa como microfono falso en las capturas del
guion: la frase del libro dicha con UNA palabra cambiada, para que la
correccion tenga un sonido que señalar. Usa tts-1 con la clave de .env /
CLAVES.txt (gasta unos centimos, autorizado por Miguel para las capturas).

    python -X utf8 tools/capturas_guion_audio.py "frase original" salida.wav

Imprime la frase que de verdad se dijo (con la palabra cambiada).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import config  # noqa: E402  (carga .env / CLAVES.txt)

from openai import OpenAI  # noqa: E402

# Cambios que suenan parecido y que whisper transcribe tal cual: la correccion
# marca la palabra y señala un sonido concreto.
# Solo cambios de una palabra real por otra real: whisper transcribe la que
# oye y la correccion la marca. (La misma lista que CAMBIABLES en
# tools/capturas_guion.mjs.)
CAMBIOS = {
    "poverty": "property", "world": "word", "bird": "bed", "doctor": "daughter", "father": "feather",
    "mother": "matter", "house": "horse", "work": "walk", "walk": "work", "light": "right",
    "lock": "rock", "three": "free", "think": "sink", "thought": "taught", "ship": "sheep",
    "sheep": "ship", "paper": "pepper", "money": "many", "water": "waiter", "strain": "train",
    "year": "ear", "great": "grade", "times": "dimes", "life": "wife", "rest": "wrest",
    "early": "hourly", "later": "letter", "heart": "hurt", "hard": "heard", "long": "wrong",
}


def frase_dicha(original: str) -> str:
    """Cambia hasta DOS palabras: whisper corrige una sola por el contexto."""
    palabras = original.split()
    cambiadas = 0
    for i, p in enumerate(palabras):
        limpia = re.sub(r"[^\w']", "", p).lower()
        if limpia in CAMBIOS:
            palabras[i] = re.sub(re.escape(limpia), CAMBIOS[limpia], p, flags=re.I)
            cambiadas += 1
            if cambiadas == 2:
                break
    if cambiadas:
        return " ".join(palabras)
    # Sin palabra de la lista: se cambia la vocal de la palabra mas larga con «e» -> «a».
    idx = max(range(len(palabras)), key=lambda k: len(re.sub(r"[^\w]", "", palabras[k])))
    cambiada = re.sub(r"e", "a", palabras[idx], count=1, flags=re.I)
    if cambiada == palabras[idx]:
        cambiada = re.sub(r"[aiou]", "e", palabras[idx], count=1, flags=re.I)
    palabras[idx] = cambiada
    return " ".join(palabras)


def main() -> None:
    original, salida = sys.argv[1], Path(sys.argv[2])
    dicha = frase_dicha(original)
    config.cargar()
    cliente = OpenAI(api_key=config.obtener("OPENAI_API_KEY"), timeout=60)
    with cliente.audio.speech.with_streaming_response.create(
            model="tts-1", voice="alloy", input=dicha, response_format="wav") as r:
        r.stream_to_file(salida)
    print(dicha)


if __name__ == "__main__":
    main()
