"""Eos dice cada sonido del AFI de Pronunciar: curvas de la cara para los mp3 pregrabados.

    python -X utf8 tools/eos_pronunciar/generar_clips.py                 # los 85 (41 GA + 44 RP) que falten
    python -X utf8 tools/eos_pronunciar/generar_clips.py --solo ga/0283  # uno (la ʃ del General American)
    python -X utf8 tools/eos_pronunciar/generar_clips.py --boca modelo   # la boca de Blender en vez de Audio2Face

Los mp3 de `app/audio_fonemas/` (GA) y `app/audio_fonemas_rp/` (RP) son los que ya
oye el lector: el sonido sostenido tres veces y las dos palabras de ejemplo
(`tools/generar_fonemas.py`). Aquí NO se genera voz ni se paga nada: se le da a
Eos ese mismo audio y sale `curvas.json` con los gestos por fotograma, que luego
`grabar_clips.py` convierte en vídeo.

El generador de Eos es `generar.py` de la sesión de la cara (rama
`dev/cara-parlante`, worktree `.claude/worktrees/cara-parlante`), que con `--audio`
pide a whisper las palabras con sus tiempos. Whisper no entiende un «shhh. shhh.
shhh.»: aquí se localizan los tramos sonoros por energía (tres del sonido y dos de
las palabras), se les pone el fonema (ARPAbet, para las garantías pedagógicas y la
lengua) y se sustituyen esas dos funciones ANTES de llamar a su `main()`, sin
tocar su archivo.

Cada clip queda en `D:/literalevel_eos_pronunciar/visor/clips/<acento>_<archivo>/`
(`voz.mp3`, `voz.wav`, `curvas.json`, `a2f.json`), donde el visor aislado los lee.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
import articulacion  # noqa: E402

# El inventario se lee ahora y `app/` sale de la ruta: `generar.py` (voz3, voz2cara)
# importa OTRO módulo llamado `articulacion`, el suyo, y con `app/` delante chocaban.
INVENTARIO = {acento: list(articulacion.inventario(acento)) for acento in ("ga", "rp")}
sys.path.remove(str(RAIZ / "app"))
del sys.modules["articulacion"]

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corregir_visemas  # noqa: E402

GENERADOR = RAIZ / ".claude" / "worktrees" / "cara-parlante" / "tools" / "cara_parlante" / "eos_demo"
TRABAJO = Path(os.environ.get("LITERALEVEL_EOS_TRABAJO", "D:/literalevel_eos_pronunciar"))
CLIPS = TRABAJO / "visor" / "clips"
NOVERBAL = Path("D:/literalevel_cara/v3_solo_noverbal")   # solo noverbal/: la boca la pone A2F o Blender

# AFI del inventario (`app/articulacion.py`, GA y RP) → ARPAbet sin acento, como lo
# escribe g2p_en y lo espera el modelo articulatorio de `generar.py`.
ARPABET = {
    "p": "p", "b": "b", "t": "t", "d": "d", "k": "k", "ɡ": "g", "f": "f", "v": "v", "θ": "th", "ð": "dh",
    "s": "s", "z": "z", "ʃ": "sh", "ʒ": "zh", "h": "hh", "tʃ": "ch", "dʒ": "jh", "m": "m", "n": "n",
    "ŋ": "ng", "l": "l", "ɹ": "r", "r": "r", "w": "w", "j": "y",
    "i": "iy", "iː": "iy", "ɪ": "ih", "ɛ": "eh", "e": "eh", "æ": "ae", "ɑ": "aa", "ɑː": "aa", "ɒ": "aa",
    "ɔ": "ao", "ɔː": "ao", "ʊ": "uh", "u": "uw", "uː": "uw", "ʌ": "ah", "ə": "ah", "ɝ": "er", "ɜː": "er",
    "ɚ": "er", "eɪ": "ey", "aɪ": "ay", "ɔɪ": "oy", "oʊ": "ow", "əʊ": "ow", "aʊ": "aw",
    "ɪə": "ih", "eə": "eh", "ʊə": "uh",
}


def clave(acento: str, sonido) -> str:
    return f"{acento}_{sonido.ruta.name[:-4]}"


def tramos_sonoros(mp3: Path, ff: str) -> list[tuple[float, float]]:
    """Tramos con voz por energía (RMS cada 10 ms, umbral 30 dB bajo el máximo),
    unidos si el hueco es menor de 150 ms; una cola suelta de menos de 120 ms
    (la explosión final de «back») se pega al tramo anterior."""
    raw = subprocess.run([ff, "-loglevel", "error", "-i", str(mp3), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = 160
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1))
    db = 20 * np.log10(rms + 1e-6)
    con_voz = db > db.max() - 30
    segs, s = [], None
    for i, v in enumerate(con_voz):
        if v and s is None:
            s = i
        elif not v and s is not None:
            if i - s > 3:
                segs.append([s / 100, i / 100])
            s = None
    if s is not None:
        segs.append([s / 100, n / 100])
    unidos: list[list[float]] = []
    for a, b in segs:
        if unidos and a - unidos[-1][1] < 0.15:
            unidos[-1][1] = b
        else:
            unidos.append([a, b])
    if len(unidos) > 1 and unidos[-1][1] - unidos[-1][0] < 0.12:
        unidos[-2][1] = unidos[-1][1]
        unidos.pop()
    return [(round(a, 3), round(b, 3)) for a, b in unidos]


def guion(acento: str, sonido, ff: str):
    """(palabras, fonemas) para `generar.py`: [texto, t0, t1] y [arpabet, t0, t1].
    Los dos últimos tramos son las palabras de ejemplo; los anteriores, el sonido."""
    t = tramos_sonoros(sonido.ruta, ff)
    if len(t) < 3:
        raise RuntimeError(f"{acento} /{sonido.simbolo}/: solo {len(t)} tramos sonoros: {t}")
    ejemplos = list(sonido.ejemplos[:2])
    arpa = ARPABET[sonido.simbolo]
    palabras, fons = [], []
    for a, b in t[:-2]:
        palabras.append([sonido.simbolo, a, b])
        fons.append((arpa, a, b))
    for (a, b), texto in zip(t[-2:], ejemplos):
        palabras.append([texto, a, b])
        fons += _fonemas_de_palabra([(texto, a, b)])
    return palabras, fons


def _generar():
    sys.path.insert(0, str(GENERADOR))
    import generar  # noqa: E402  (el de la sesión de la cara)
    return generar


# El `fonemas` original de generar.py (g2p_en), guardado ANTES de sustituirlo: con la
# sustitución de un clip, el siguiente recibía los fonemas del anterior (visto en la
# primera tanda: «93 fonemas» en /k/).
_fonemas_de_palabra = _generar().fonemas


def generar_clip(acento: str, sonido, boca: str, semilla: int, ff: str) -> Path:
    salida = CLIPS / clave(acento, sonido)
    palabras, fons = guion(acento, sonido, ff)
    generar = _generar()
    generar.palabras_de_audio = lambda mp3, idioma: palabras
    generar.fonemas = lambda _palabras: fons
    sys.argv = ["generar.py", "--audio", str(sonido.ruta), "--idioma", "en", "--salida", str(salida),
                "--boca", boca, "--gestos", "v3", "--modelo_v3", str(NOVERBAL), "--estilo_v3", "real",
                "--semilla", str(semilla)]
    cwd = os.getcwd()
    os.chdir(GENERADOR)   # generar.py resuelve voz3/ y voz2cara/ respecto a su carpeta
    try:
        generar.main()
    finally:
        os.chdir(cwd)
    datos = json.load(open(salida / "curvas.json", encoding="utf-8"))
    # Los tramos del sonido aislado van primero (`guion`): en ellos el tramo sonoro de
    # una /p b/ es la explosión y el cierre tiene que ir delante (corregir_visemas.py).
    aislados = len(palabras) - 2
    datos["guion"] = {"acento": acento, "simbolo": sonido.simbolo, "palabras": palabras,
                      "fonemas": [{"arpabet": str(f[0]), "t0": float(f[1]), "t1": float(f[2]), "aislado": i < aislados}
                                  for i, f in enumerate(fons)]}
    json.dump(datos, open(salida / "curvas.json", "w", encoding="utf-8"))
    # 4 oct (Miguel, tras la demo): A2F no junta los labios en /p b m/ y la lengua se iba
    # de lado. Se corrige sobre las curvas, antes de grabar; idempotente.
    informe = corregir_visemas.corregir_archivo(salida / "curvas.json")
    print(f"   visemas: cierres {informe['cierres']}, jawOpen en cierre "
          f"{informe.get('jawOpen_en_cierre_antes')}→{informe.get('jawOpen_en_cierre_despues')}", flush=True)
    return salida


def todos():
    for acento in ("ga", "rp"):
        for s in INVENTARIO[acento]:
            yield acento, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", default="", help="acento/archivo, p. ej. ga/0283")
    ap.add_argument("--boca", choices=["a2f", "modelo"], default="a2f")
    ap.add_argument("--rehacer", action="store_true")
    a = ap.parse_args()
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    if not (NOVERBAL / "noverbal").is_dir() or (NOVERBAL / "boca").exists():
        raise SystemExit(f"{NOVERBAL} debe tener solo noverbal/")
    CLIPS.mkdir(parents=True, exist_ok=True)
    hechos, fallos = 0, []
    for k, (acento, s) in enumerate(todos()):
        if a.solo and f"{acento}/{s.ruta.name[:-4]}" != a.solo:
            continue
        salida = CLIPS / clave(acento, s)
        if (salida / "curvas.json").exists() and not a.rehacer:
            continue
        print(f"== {acento} /{s.simbolo}/ → {salida.name}", flush=True)
        try:
            generar_clip(acento, s, a.boca, 100 + k, ff)
            hechos += 1
        except Exception as e:  # noqa: BLE001  (un clip que falla no para la tanda)
            fallos.append((acento, s.simbolo, f"{type(e).__name__}: {e}"))
            print("   FALLÓ", fallos[-1], flush=True)
    print(f"hechos {hechos}, fallos {len(fallos)}")
    for f in fallos:
        print("  ", f)


if __name__ == "__main__":
    main()
