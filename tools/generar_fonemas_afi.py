"""Genera los audios de la tabla del AFI con el formato que pidio Miguel.

    python -X utf8 tools/generar_fonemas_afi.py --seco            # que haria y cuanto costaria
    python -X utf8 tools/generar_fonemas_afi.py                   # los dos acentos, lo que falte
    python -X utf8 tools/generar_fonemas_afi.py --acento rp       # solo el britanico
    python -X utf8 tools/generar_fonemas_afi.py --rehacer ʃ ʊ     # esos, aunque existan
    python -X utf8 tools/generar_fonemas_afi.py --todo            # rehace todos

EL FORMATO (13 sep 2026)
Miguel escucho los primeros audios (el sonido tres veces y dos palabras) y
pidio otra cosa: «que sea lento, que mantenga el sonido; una vez que mantenga
el sonido, ya te lo digo rapido, y luego en una palabra». Cada mp3 son tres
partes separadas por una pausa:

  1. el sonido SOSTENIDO unos dos segundos (las oclusivas y africadas no se
     pueden alargar: se dicen despacio dos veces);
  2. el sonido RAPIDO, una vez;
  3. UNA palabra de ejemplo, a velocidad natural.

Americano: sustituye los mp3 de `app/audio_fonemas/`, que usan tambien la
correccion de voz y la API de Angular (mismo nombre de archivo). Britanico:
`app/audio_fonemas_rp/`, con voz en acento britanico. Se reutilizan las
piezas probadas de `generar_fonemas.py` (PCM de gpt-4o-mini-tts, recorte de
silencios y escritura atomica del mp3).

LO QUE NO SE VERIFICA
El reconocedor de fonemas de la primera version no distingue bien sonidos
sostenidos y ya dio por buenos audios que Miguel oyo mal. Aqui solo se vigila
la duracion de cada parte y se reintenta si sale absurda. **La verificacion es
el oido de quien los escuche.**
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
sys.path.insert(0, str(RAIZ / "app"))
import generar_fonemas as G  # noqa: E402
import articulacion  # noqa: E402
import config  # noqa: E402

REGISTRO = RAIZ / "tools" / "fonemas_afi_generados.json"
PAUSA_S = 0.7
TOPE_LLAMADAS = 400

ACENTO_INS = {
    "ga": "You are an American English pronunciation teacher with a clear General American accent, "
          "speaking to a Spanish-speaking teenager. ",
    "rp": "You are a British English pronunciation teacher with a clear Received Pronunciation "
          "(standard Southern British) accent, speaking to a Spanish-speaking teenager. ",
}

# Pistas de los sonidos que no estan en `generar_fonemas.PISTAS` (solo RP) y
# arreglos medidos en las muestras: con «shhhhhhhhhh» el tramo sostenido de /ʃ/
# salio en silencio y el rapido duro 2,6 s.
PISTAS_EXTRA = {"ɒ": ["o", "aw"], "ɜː": ["er", "urr"], "ɪə": ["eer", "ear"],
                "eə": ["air", "ehr"], "ʊə": ["oor", "ure"]}
LENTA = {"ʃ": "Shhhhhhhhhhhhhhh."}
RAPIDA = {"ʃ": "sh."}
EXTRA = {"ʃ": " It is the hushing sound people make to ask for silence."}


def _pistas(s: articulacion.Sonido) -> list[str]:
    return PISTAS_EXTRA.get(s.simbolo) or G.PISTAS.get(s.clave) or [s.simbolo]


def _alargar(pista: str) -> str:
    return pista + pista[-1] * 7 if pista[-1].isalpha() else pista


def _partes(s: articulacion.Sonido, pista: str) -> list[tuple[str, str, tuple[float, float]]]:
    base = ACENTO_INS[s.acento]
    ancla = s.ejemplos[0]
    extra = EXTRA.get(s.clave, "")
    sonido = (f"The text is a spelling hint for ONE English speech sound: /{s.simbolo}/, "
              f"as in '{ancla}'.{extra} ")
    prohibido = f" Never say the word '{ancla}', never name a letter or a symbol."
    if s.clave in G.OCLUSIVAS:
        lenta = (f"{pista}... {pista}...",
                 base + sonido + "It cannot be held, so say it very slowly two times, with a long "
                 "pause between them, exaggerating how it closes and releases, with the weakest "
                 "possible vowel." + prohibido)
    else:
        lenta = (LENTA.get(s.clave, _alargar(pista)),
                 base + sonido + "Hold that single sound steadily for about two seconds, as one "
                 "continuous sound, without changing it and without adding any other sound." + prohibido)
    rapida = (RAPIDA.get(s.clave, f"{pista}."),
              base + sonido + "Say that bare sound ONCE, short and crisp, at natural speed, with no "
              "extra vowel." + prohibido)
    palabra = (f"{ancla}.", base + "Say this one word clearly, at a calm, natural speed.")
    return [(*lenta, (0.5, 5.0)), (*rapida, (0.1, 1.8)), (*palabra, (0.25, 3.0))]


def generar(s: articulacion.Sonido, cliente, gasto: dict) -> dict:
    trozos, fila = [], {"acento": s.acento, "simbolo": s.simbolo, "archivo": s.archivo,
                        "palabra": s.ejemplos[0], "partes": []}
    for parte, nombre in zip(range(3), ("sostenido", "rapido", "palabra")):
        mejor = None
        for pista in _pistas(s):
            texto, ins, (minimo, maximo) = _partes(s, pista)[parte]
            for _ in range(2):
                if gasto["tts_llamadas"] >= TOPE_LLAMADAS:
                    raise RuntimeError("tope de llamadas alcanzado")
                x = G._recortar(G._pcm(cliente, texto, ins, gasto))
                dur = len(x) / G.SR
                if mejor is None or abs(dur - (minimo + maximo) / 2) < abs(mejor[1] - (minimo + maximo) / 2):
                    mejor = (x, dur, pista)
                if minimo <= dur <= maximo:
                    break
            if minimo <= mejor[1] <= maximo:
                break
        x, dur, pista = mejor
        fila["partes"].append({"parte": nombre, "pista": pista, "segundos": round(dur, 2),
                               "en_rango": bool(minimo <= dur <= maximo)})
        trozos.append(x)
    pausa = np.zeros(int(G.SR * PAUSA_S), dtype=np.float32)
    todo = np.concatenate([trozos[0], pausa, trozos[1], pausa, trozos[2]])
    todo = (todo * (0.9 / (float(np.abs(todo).max()) or 1.0))).astype(np.float32)
    G._escribir_mp3(todo, s.ruta)
    fila.update(segundos=round(len(todo) / G.SR, 2), bytes=s.ruta.stat().st_size,
                fecha=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return fila


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seco", action="store_true")
    ap.add_argument("--acento", choices=["ga", "rp", "ambos"], default="ambos")
    ap.add_argument("--rehacer", nargs="*", default=[])
    ap.add_argument("--todo", action="store_true", help="rehace todos aunque existan")
    args = ap.parse_args()

    acentos = ["ga", "rp"] if args.acento == "ambos" else [args.acento]
    registro = json.loads(REGISTRO.read_text(encoding="utf-8")) if REGISTRO.exists() else {"audios": {}}
    hechos = registro.setdefault("audios", {})
    pendientes = []
    for acento in acentos:
        for s in articulacion.inventario(acento):
            clave = f"{acento}:{s.simbolo}"
            nuevo_formato = clave in hechos and s.audio()
            if args.todo or s.simbolo in args.rehacer or not nuevo_formato:
                pendientes.append(s)
    llamadas = len(pendientes) * 3
    print(f"pendientes: {len(pendientes)} ({', '.join(a + ':' + str(sum(1 for p in pendientes if p.acento == a)) for a in acentos)})"
          f" | llamadas minimas {llamadas} | coste maximo aprox USD {llamadas * 2 * 4 / 60 * G.PRECIO_TTS_MIN:.2f}")
    if args.seco or not pendientes:
        return

    config.cargar()
    from openai import OpenAI
    cliente = OpenAI(api_key=config.obtener("OPENAI_API_KEY"), timeout=60, max_retries=1)
    gasto = {"tts_llamadas": 0, "tts_segundos": 0.0, "stt_llamadas": 0, "stt_segundos": 0.0}
    fuera_de_rango = []
    for i, s in enumerate(pendientes, 1):
        try:
            fila = generar(s, cliente, gasto)
        except Exception as e:
            print(f"[{i}/{len(pendientes)}] {s.acento} /{s.simbolo}/ FALLO: {type(e).__name__}: {e}")
            continue
        hechos[f"{s.acento}:{s.simbolo}"] = fila
        REGISTRO.write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
        raras = [p["parte"] for p in fila["partes"] if not p["en_rango"]]
        if raras:
            fuera_de_rango.append(f"{s.acento} /{s.simbolo}/ ({', '.join(raras)})")
        print(f"[{i}/{len(pendientes)}] {s.acento} /{s.simbolo}/ ({fila['palabra']}) "
              f"{' + '.join(str(p['segundos']) for p in fila['partes'])} s")
    registro["gasto_ultima_ejecucion"] = {**gasto, "usd_aprox": round(gasto["tts_segundos"] / 60 * G.PRECIO_TTS_MIN, 4)}
    REGISTRO.write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"llamadas TTS: {gasto['tts_llamadas']} | USD aprox {registro['gasto_ultima_ejecucion']['usd_aprox']}")
    if fuera_de_rango:
        print("duracion fuera de rango (escuchar primero):", "; ".join(fuera_de_rango))


if __name__ == "__main__":
    main()
