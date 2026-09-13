"""Genera, UNA sola vez, el audio de cada fonema de `app/fonemas.py`.

    python -X utf8 tools/generar_fonemas.py                  # genera lo que falte
    python -X utf8 tools/generar_fonemas.py --seco           # que haria y cuanto costaria, sin llamar
    python -X utf8 tools/generar_fonemas.py --rehacer θ ð    # vuelve a hacer esos
    python -X utf8 tools/generar_fonemas.py --env RUTA/.env  # la clave de otro sitio (un worktree)

Los mp3 quedan en `app/audio_fonemas/` y se versionan: la app los sirve desde
disco, sin clave y sin gastar credito. Este guion es lo UNICO que paga, y solo
por lo que falta: un fonema con su mp3 en disco no se vuelve a pedir, asi que
se puede cortar y relanzar sin pagar dos veces. Lo que ha hecho y lo que ha
oido queda en `tools/fonemas_generados.json`.

COMO SE PIDE EL AUDIO, Y POR QUE ASI

Un TTS pronuncia mal un fonema aislado, y se midio antes de escribir esto
(12 sep 2026, ensayos con un reconocedor de fonemas, ver abajo):

- `tts-1` ignora la pista del sonido y lee solo las palabras, y a veces ni
  eso: «sing... long» salio «Sim, senhora».
- Con `gpt-4o-mini-tts`, sonido y palabras en UNA llamada se mezclan: el
  parentesis «(the voiced th)» se leyo en voz alta.
- Una letra suelta se lee como el NOMBRE de la letra: «p» salio «pee» y «w»
  salio «double-u». Por eso las pistas son deletreos («puh», «woo», «shhh»).

Lo que funciono: dos llamadas a `gpt-4o-mini-tts` en PCM crudo. En la primera,
la pista repetida tres veces («shhh. shhh. shhh.») con unas instrucciones que
dan el simbolo AFI y la palabra ancla y prohiben decir la palabra o anadir
vocal. En la segunda, las dos palabras de ejemplo. Se recortan los silencios,
se unen con una pausa y se guardan en mp3 mono de unos 40 kbps.

COMO SE VERIFICA, Y LO QUE NO

Transcribir de vuelta con Whisper no sirve para el sonido aislado -no es una
palabra- y ni siquiera para palabras sueltas: «see. tea.» volvia como «C, G».
Se usa un reconocedor de FONEMAS, `facebook/wav2vec2-lv-60-espeak-cv-ft`,
local y gratis (1,2 GB; se descarga con --descargar-verificador). Cada pista
candidata se oye con el: si el fonema pedido aparece y domina lo que se oye,
se acepta; si no, se prueba la siguiente pista, y si ninguna pasa se queda la
mejor marcada como `dudoso`. Las palabras de ejemplo se oyen tambien, y ademas
se transcriben con `gpt-4o-mini-transcribe` como aviso (no como filtro).

Limites conocidos del reconocedor, que el registro no esconde: confunde /θ/
con /f/ (oyo «think» como «f ɪ n k»), no separa bien /ɔ/ de /ɑ/, y oye la /æ/
aislada como [a]. Esas parejas se aceptan como equivalentes al verificar, asi
que en esos fonemas la verificacion vale menos. Y **nadie ha escuchado estos
audios con oido humano** al generarlos: la ultima palabra es de quien los oiga.

LA CLAVE

La de siempre: `config.cargar` la toma del entorno, de `.env` o de
`CLAVES.txt`. `--env` permite apuntar a otro archivo (un worktree no tiene el
suyo). No se imprime nunca.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))
import config  # noqa: E402
import fonemas  # noqa: E402

REGISTRO = RAIZ / "tools" / "fonemas_generados.json"

MODELO_TTS = "gpt-4o-mini-tts"
VOZ = "coral"
MODELO_STT = "gpt-4o-mini-transcribe"
VERIFICADOR = "facebook/wav2vec2-lv-60-espeak-cv-ft"
SR = 24000                 # la API devuelve PCM de 16 bits, mono, a 24 kHz
CALIDAD_MP3 = 0.8          # compression_level de libsndfile: ~40 kbps, de sobra para voz
PAUSA_S = 0.6
MAX_SONIDO_S = 6.0         # tres repeticiones de un sonido no llegan ni a 5 s
MAX_PALABRAS_S = 8.0
TOPE_LLAMADAS = 200        # por ejecucion; el presupuesto duro es < 1 USD

# Precios supuestos para ESTIMAR (USD). gpt-4o-mini-tts se factura por tokens y
# OpenAI lo equipara a unos 0,015 $/min de audio; mini-transcribe, 0,003 $/min.
PRECIO_TTS_MIN = 0.015
PRECIO_STT_MIN = 0.003

# Pistas candidatas por fonema, en orden de preferencia. Nunca una letra suelta
# (se lee su nombre) ni un parentesis (se lee en voz alta). Y tampoco dos
# consonantes seguidas que formen un nombre de letra o una sigla: medido en la
# primera tanda, «dd» salio «dee dee» y «dj» salio «DJ».
PISTAS = {
    "p": ["puh", "ph"], "b": ["buh", "bə"], "t": ["tuh", "tə"],
    "d": ["duh", "də", "dduh"], "k": ["kuh", "kə"], "ɡ": ["guh", "gə"],
    "f": ["fff", "ffff", "fuh"], "v": ["vvvv", "vvv", "vuh"],
    "θ": ["thhhh", "θθθ", "thh"], "ð": ["dhhhh", "ðə", "ðððð"],
    "s": ["ssss", "sss"], "z": ["zzzz", "zzz"], "ʃ": ["shhhh", "shh"],
    "ʒ": ["zhhhh", "ʒʒʒ", "zhuh"],
    "h": ["hhhh", "huh"], "tʃ": ["chuh", "tʃə", "tch"], "dʒ": ["juh", "dʒə", "djuh"],
    "m": ["mmmm", "mmm", "hmmm"], "n": ["nnnn", "nnn", "nuh"], "ŋ": ["nggg", "ŋŋŋ", "-ng"],
    "l": ["llll", "lll", "luh"], "ɹ": ["rrrr", "rr"], "w": ["woo", "wuh"],
    "j": ["yuh", "yee"],
    "i": ["ee"], "ɪ": ["ih", "ihh"], "ɛ": ["eh", "ehh"], "æ": ["aa", "aah"],
    "ɑ": ["ah", "aah"], "ɔ": ["aw", "awe"], "ʊ": ["ooh", "uu", "uh"],
    "u": ["oo", "ooo"], "ʌ": ["uh", "uhh"], "ə": ["uh", "uhh", "a"],
    "ɝ": ["er", "err"], "ɚ": ["er", "err"],
    "eɪ": ["ay"], "aɪ": ["eye", "ai"], "ɔɪ": ["oy", "oi"], "oʊ": ["oh", "ohh"],
    "aʊ": ["ow", "ouw"],
}

# Donde el reconocedor no distingue (ver el docstring). Solo para verificar.
# Medido en la primera tanda: la /ʌ/ de «strut» la oye como [ɑ] incluso dentro
# de la palabra, asi que en /ʌ/ la verificacion no separa esas dos.
EQUIVALENTES = {"θ": {"f"}, "æ": {"a"}, "ɔ": {"ɑ"}, "ɑ": {"ɔ"},
                "ə": {"ʌ"}, "ʌ": {"ə", "ɑ"}, "ɝ": {"ɚ"}, "ɚ": {"ɝ"}}
# Una oclusiva, una africada o una semivocal no suenan sin algo de vocal detras;
# en esas se tolera una vocal debil, y el registro lo apunta.
CON_VOCAL_DE_APOYO = {"p", "b", "t", "d", "k", "ɡ", "tʃ", "dʒ", "w", "j", "h"}
VOCALES_DE_APOYO = {"ə", "ʌ", "a", "ɑ"}    # «puh» se oye a veces como [pɑ]
OCLUSIVAS = {"p", "b", "t", "d", "k", "ɡ", "tʃ", "dʒ"}


def _instrucciones_sonido(f: fonemas.Fonema) -> str:
    ancla = f.ejemplos[0]
    if f.simbolo in OCLUSIVAS:
        extra = ("It is a stop consonant: make only its short burst, with the shortest "
                 "and weakest vowel you can after it.")
    elif f.tipo == "consonante":
        extra = "Hold the sound for about half a second each time."
    else:
        extra = "Say only this vowel sound, clearly."
    return ("You are an American English pronunciation teacher with a clear General "
            "American accent. The text is a spelling hint for ONE English speech sound: "
            f"/{f.simbolo}/, the sound in '{ancla}'. Say that bare sound three times, with "
            f"a short pause between repetitions, exactly as it sounds inside '{ancla}'. "
            f"Never say the word '{ancla}', never name a letter or a symbol, and do not "
            f"add a vowel before or after it. {extra}")


INSTRUCCIONES_PALABRAS = (
    "You are an American English pronunciation teacher with a clear General American "
    "accent. Say each word slowly and clearly, with a short pause between the words.")


# --- Audio ---------------------------------------------------------------

def _pcm(cliente, texto: str, instrucciones: str, gasto: dict) -> np.ndarray:
    r = cliente.audio.speech.create(model=MODELO_TTS, voice=VOZ, input=texto,
                                    instructions=instrucciones, response_format="pcm")
    x = np.frombuffer(r.content, dtype="<i2").astype(np.float32) / 32768.0
    gasto["tts_llamadas"] += 1
    gasto["tts_segundos"] += len(x) / SR
    return x


def _recortar(x: np.ndarray, margen_s: float = 0.05) -> np.ndarray:
    """Quita el silencio de los bordes (envolvente RMS en ventanas de 20 ms)."""
    v = int(SR * 0.02)
    n = len(x) // v
    if n == 0:
        return x
    rms = np.sqrt((x[: n * v].reshape(n, v) ** 2).mean(axis=1))
    activo = np.nonzero(rms > max(rms.max() * 0.04, 1e-4))[0]
    if len(activo) == 0:
        return x[:0]
    m = int(SR * margen_s)
    return x[max(0, activo[0] * v - m): min(len(x), (activo[-1] + 1) * v + m)]


def _escribir_mp3(x: np.ndarray, destino: Path) -> None:
    """mp3 junto al destino y publicado con un solo `os.replace`: un corte a
    medias no deja un mp3 truncado que la siguiente ejecucion daria por hecho."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(destino.parent), prefix=f".{destino.stem}.", suffix=".tmp")
    os.close(fd)
    try:
        sf.write(tmp, x, SR, format="MP3", subtype="MPEG_LAYER_III",
                 compression_level=CALIDAD_MP3, bitrate_mode="CONSTANT")
        if os.path.getsize(tmp) == 0:
            raise OSError("mp3 vacio")
        os.replace(tmp, destino)
    finally:
        Path(tmp).unlink(missing_ok=True)


# --- Verificacion -----------------------------------------------------------

class Oidor:
    """Reconocedor de fonemas local (CTC sobre el vocabulario de espeak)."""

    def __init__(self, descargar: bool):
        from huggingface_hub import snapshot_download
        patrones = ["*.json", "*.txt", "pytorch_model.bin", "model.safetensors"]
        carpeta = Path(snapshot_download(VERIFICADOR, allow_patterns=patrones,
                                         local_files_only=not descargar))
        import torch
        from transformers import Wav2Vec2ForCTC
        self._torch = torch
        vocab = json.loads((carpeta / "vocab.json").read_text(encoding="utf-8"))
        self._tokens = {i: t for t, i in vocab.items()}
        self._modelo = Wav2Vec2ForCTC.from_pretrained(str(carpeta)).eval()
        self._pad = self._modelo.config.pad_token_id

    def oir(self, x: np.ndarray) -> list[str]:
        from scipy.signal import resample_poly
        y = resample_poly(x, 2, 3).astype(np.float32)          # 24 kHz -> 16 kHz
        y = (y - y.mean()) / (y.std() + 1e-7)
        with self._torch.no_grad():
            ids = self._modelo(self._torch.from_numpy(y)[None]).logits[0].argmax(-1).tolist()
        salida, previo = [], None
        for i in ids:
            if i != previo and i != self._pad:
                t = self._tokens.get(i, "")
                if t and not t.startswith("<"):
                    salida.append(t)
            previo = i
        return salida


def _a_inventario(tokens: list[str]) -> list[str]:
    """Tokens de espeak -> simbolos del inventario ('?' si no hay equivalente).

    espeak escribe la aspiracion como parte del token («ph»), numera vocales
    reducidas («i5») y junta vocal y r («ɔːɹ»); aqui se deshace todo eso."""
    salida = []
    for tok in tokens:
        # La longitud no distingue fonemas en General American (ver `fonemas`),
        # y quitarla antes deja «aː» en «a» y «ɔːɹ» en «ɔɹ», que si se trocean.
        t = tok.rstrip("0123456789").replace("ː", "")
        if t in ("ph", "th", "kh"):
            t = t[0]
        t = {"ɐ": "ə", "ᵻ": "ɪ", "ɜ": "ɝ"}.get(t, t)
        if t == "a":
            salida.append("a")               # no es del inventario; ver EQUIVALENTES
            continue
        canonico = fonemas.normalizar(t)
        if canonico:
            salida.append(canonico)
            continue
        resto = t
        while resto:
            for largo in (3, 2, 1):
                trozo = fonemas.normalizar(resto[:largo]) if len(resto) >= largo else None
                if trozo:
                    salida.append(trozo)
                    resto = resto[largo:]
                    break
            else:
                salida.append("?")
                resto = resto[1:]
    return _fusionar(salida)


def _fusionar(fonos: list[str]) -> list[str]:
    """El reconocedor parte /ɔɪ/ en dos: oyo «boy» como «b oʊ ɪ». Se vuelve a
    juntar. Tiene un coste que se acepta: «going» (g oʊ ɪ ŋ) tambien se
    juntaria, pero esto solo se usa para verificar, y ningun ejemplo lo tiene."""
    salida: list[str] = []
    for x in fonos:
        if x == "ɪ" and salida and salida[-1] in ("oʊ", "ɔ"):
            salida[-1] = "ɔɪ"
        else:
            salida.append(x)
    return salida


def _veredicto(f: fonemas.Fonema, fonos_sonido: list[str], fonos_palabras: list[str]) -> dict:
    """Veredicto de un audio a partir de lo oido. Lo usan la generacion y
    `--reclasificar`, para que las dos no puedan divergir.

    Tres casos que no son el mismo. «verificado»: el sonido aislado se oye como
    el fonema pedido y las palabras lo contienen. «no verificable»: el
    reconocedor no oye NADA en el sonido aislado -le pasa con fricativas puras
    sostenidas, como /f/, /z/ o /ʃ/, que sin vocal alrededor no parecen habla-,
    asi que ni lo confirma ni lo desmiente. «dudoso»: oye OTRA cosa (un nombre
    de letra, una vocal de mas). Los dos ultimos hay que oirlos."""
    acepta, pureza, apoyo = _puntuar(f, fonos_sonido)
    buenos = {f.simbolo} | EQUIVALENTES.get(f.simbolo, set())
    en_palabras = any(x in buenos for x in fonos_palabras)
    if acepta and en_palabras:
        veredicto = "verificado"
    elif not [x for x in fonos_sonido if x != "?"] and en_palabras:
        veredicto = "no verificable"
    else:
        veredicto = "dudoso"
    return {"acepta": acepta, "pureza": pureza, "con_vocal_de_apoyo": apoyo,
            "fonema_en_palabras": en_palabras, "veredicto": veredicto}


def reclasificar(registro: dict) -> None:
    """Recalcula los veredictos con lo que ya se oyo, sin llamar a nada."""
    for simbolo, fila in registro.get("fonemas", {}).items():
        f = fonemas.buscar(simbolo)
        if f is None or "oido_en_palabras" not in fila:
            continue
        elegido = next(i for i in fila["intentos"] if i["pista"] == fila["pista"])
        v = _veredicto(f, _fusionar(elegido.get("oido", "").split()),
                       _fusionar(fila["oido_en_palabras"].split()))
        elegido.update(acepta=v["acepta"], pureza=v["pureza"],
                       con_vocal_de_apoyo=v["con_vocal_de_apoyo"])
        fila.update(fonema_en_palabras=v["fonema_en_palabras"], veredicto=v["veredicto"])


def _puntuar(f: fonemas.Fonema, fonos: list[str]) -> tuple[bool, float, bool]:
    """(acepta, pureza, con_vocal_de_apoyo) del sonido aislado."""
    buenos = {f.simbolo} | EQUIVALENTES.get(f.simbolo, set())
    apoyo = VOCALES_DE_APOYO if f.simbolo in CON_VOCAL_DE_APOYO else set()
    n_buenos = sum(1 for x in fonos if x in buenos)
    utiles = [x for x in fonos if x not in apoyo or x in buenos]
    if n_buenos == 0:
        return False, 0.0, False
    pureza = round(n_buenos / max(1, len(utiles)), 2)
    con_apoyo = any(x in apoyo and x not in buenos for x in fonos)
    return pureza >= 0.6, pureza, con_apoyo


def _transcribir(cliente, x: np.ndarray, gasto: dict) -> str:
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        sf.write(tmp, x, SR)
        with open(tmp, "rb") as a:
            r = cliente.audio.transcriptions.create(model=MODELO_STT, file=a, language="en")
        gasto["stt_llamadas"] += 1
        gasto["stt_segundos"] += len(x) / SR
        return r.text
    finally:
        Path(tmp).unlink(missing_ok=True)


# --- Un fonema --------------------------------------------------------------

def generar(f: fonemas.Fonema, cliente, oidor: Oidor | None, gasto: dict, tope: int) -> dict:
    instrucciones = _instrucciones_sonido(f)
    intentos, mejor = [], None
    for pista in PISTAS[f.simbolo]:
        if gasto["tts_llamadas"] + gasto["stt_llamadas"] >= tope:
            break
        sonido = _recortar(_pcm(cliente, f"{pista}. {pista}. {pista}.", instrucciones, gasto))
        intento = {"pista": pista, "segundos": round(len(sonido) / SR, 2)}
        # Paso de verdad: «ffff» salio en 65 s, el modelo se quedo repitiendo
        # el sonido. Un audio asi no se queda ni como el menos malo.
        if not 0.2 <= intento["segundos"] <= MAX_SONIDO_S:
            intento.update(descartado=f"dura {intento['segundos']} s", acepta=False, pureza=-1.0)
            intentos.append(intento)
            continue
        if oidor is not None:
            fonos = _a_inventario(oidor.oir(sonido))
            acepta, pureza, apoyo = _puntuar(f, fonos)
            intento.update(oido=" ".join(fonos), pureza=pureza, acepta=acepta,
                           con_vocal_de_apoyo=apoyo)
        intentos.append(intento)
        clave = (intento.get("acepta", True), intento.get("pureza", 1.0))
        if mejor is None or clave > mejor[0]:
            mejor = (clave, pista, sonido, intento)
        if intento.get("acepta", True):
            break
    if mejor is None:
        raise RuntimeError(f"/{f.simbolo}/: ninguna pista dio un audio de duracion razonable "
                           "(o se alcanzo el tope de llamadas)")

    _, pista, sonido, intento = mejor
    palabras = np.zeros(0, dtype=np.float32)
    for _ in range(2):
        palabras = _recortar(_pcm(cliente, ". ".join(f.ejemplos) + ".", INSTRUCCIONES_PALABRAS, gasto))
        if 0.3 <= len(palabras) / SR <= MAX_PALABRAS_S:
            break
    else:
        raise RuntimeError(f"/{f.simbolo}/: las palabras de ejemplo salieron de "
                           f"{len(palabras) / SR:.1f} s dos veces")
    fila = {"simbolo": f.simbolo, "archivo": f.archivo, "pista": pista,
            "intentos": intentos, "ejemplos": list(f.ejemplos)}
    transcrito = _transcribir(cliente, palabras, gasto)
    limpio = "".join(c if c.isalpha() or c.isspace() else " " for c in transcrito.lower()).split()
    fila["transcripcion_palabras"] = transcrito
    fila["palabras_transcritas_ok"] = all(e in limpio for e in f.ejemplos)
    if oidor is not None:
        fonos_palabras = _a_inventario(oidor.oir(palabras))
        fila["oido_en_palabras"] = " ".join(fonos_palabras)
        v = _veredicto(f, intento.get("oido", "").split(), fonos_palabras)
        fila.update(fonema_en_palabras=v["fonema_en_palabras"], veredicto=v["veredicto"])
    else:
        fila["veredicto"] = "sin verificar"

    todo = np.concatenate([sonido, np.zeros(int(SR * PAUSA_S), dtype=np.float32), palabras])
    pico = float(np.abs(todo).max()) or 1.0
    todo = (todo * (0.9 / pico)).astype(np.float32)
    _escribir_mp3(todo, f.ruta)
    fila.update(segundos=round(len(todo) / SR, 2), bytes=f.ruta.stat().st_size,
                fecha=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return fila


def _usd(g: dict) -> float:
    return round(g["tts_segundos"] / 60 * PRECIO_TTS_MIN
                 + g["stt_segundos"] / 60 * PRECIO_STT_MIN, 4)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seco", action="store_true", help="no llama a nada: dice que falta y cuanto costaria como mucho")
    ap.add_argument("--rehacer", nargs="*", default=[], help="simbolos a regenerar aunque exista su mp3")
    ap.add_argument("--solo", nargs="*", default=[], help="limitarse a estos simbolos")
    ap.add_argument("--env", nargs="*", default=[], help="archivos .env de donde leer la clave (no se imprime)")
    ap.add_argument("--sin-verificar", action="store_true", help="no usar el reconocedor de fonemas")
    ap.add_argument("--descargar-verificador", action="store_true", help="bajar el reconocedor (1,2 GB) si no esta")
    ap.add_argument("--max-llamadas", type=int, default=TOPE_LLAMADAS)
    ap.add_argument("--reclasificar", action="store_true",
                    help="recalcular los veredictos del registro con las reglas actuales, sin llamar a nada")
    args = ap.parse_args()

    if args.reclasificar:
        registro = json.loads(REGISTRO.read_text(encoding="utf-8"))
        reclasificar(registro)
        REGISTRO.write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
        from collections import Counter
        print(dict(Counter(f["veredicto"] for f in registro["fonemas"].values())))
        return

    rehacer = {fonemas.normalizar(s) for s in args.rehacer}
    solo = {fonemas.normalizar(s) for s in args.solo}
    if None in rehacer or None in solo:
        sys.exit("--rehacer/--solo: algun simbolo no esta en el inventario")
    registro = (json.loads(REGISTRO.read_text(encoding="utf-8")) if REGISTRO.exists()
                else {"fonemas": {}, "gasto_total": {}})
    pendientes = [f for f in fonemas.INVENTARIO
                  if (not solo or f.simbolo in solo)
                  and (f.simbolo in rehacer or fonemas.audio_de(f.simbolo) is None)]
    print(f"inventario: {len(fonemas.INVENTARIO)}   pendientes: {len(pendientes)}")
    if not pendientes:
        print("Nada que generar: todos los fonemas tienen su mp3.")
        return
    maximo = sum(len(PISTAS[f.simbolo]) + 2 for f in pendientes)
    print("   " + " ".join(f.simbolo for f in pendientes))
    print(f"llamadas como mucho: {maximo} (tope de esta ejecucion: {args.max_llamadas})")
    if args.seco:
        print(f"coste como mucho, a ~4 s por llamada: ~{maximo * 4 / 60 * PRECIO_TTS_MIN:.3f} USD")
        return

    if args.env:
        config.cargar(rutas=tuple(Path(r) for r in args.env))
    clave = config.obtener("OPENAI_API_KEY")
    if not clave:
        sys.exit("Falta OPENAI_API_KEY (entorno, .env, CLAVES.txt o --env).")
    from openai import OpenAI
    cliente = OpenAI(api_key=clave, timeout=90.0, max_retries=1)

    oidor = None
    if not args.sin_verificar:
        try:
            oidor = Oidor(descargar=args.descargar_verificador)
        except Exception as e:
            print(f"SIN VERIFICADOR ({type(e).__name__}): los audios quedaran 'sin verificar'. "
                  "Usa --descargar-verificador (1,2 GB) o --sin-verificar.")
            if not args.descargar_verificador:
                sys.exit(1)

    gasto = {"tts_llamadas": 0, "tts_segundos": 0.0, "stt_llamadas": 0, "stt_segundos": 0.0}
    total = registro.setdefault("gasto_total", {})
    for k in gasto:
        total.setdefault(k, 0)
    registro.update(modelo_tts=MODELO_TTS, voz=VOZ, modelo_stt=MODELO_STT,
                    verificador=VERIFICADOR if oidor else None)
    inicio = time.time()
    try:
        for f in pendientes:
            antes = dict(gasto)
            try:
                fila = generar(f, cliente, oidor, gasto, args.max_llamadas)
            except RuntimeError as e:
                print(f"PARO: {e}")
                break
            finally:
                for k in gasto:
                    total[k] = round(total[k] + gasto[k] - antes[k], 2)
            registro["fonemas"][f.simbolo] = fila
            REGISTRO.write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
            # El intento QUEDADO, no el ultimo: si ninguna pista pasa, se guarda
            # la mejor, que puede ser la primera.
            elegido = next(i for i in fila["intentos"] if i["pista"] == fila["pista"])
            print(f"  {f.simbolo:<3} {fila['veredicto']:<13} pista={fila['pista']!r:<9} "
                  f"oido={elegido.get('oido', '-')!r} palabras={fila.get('oido_en_palabras', '-')!r} "
                  f"{fila['bytes']} B", flush=True)
    finally:
        total["usd_estimado"] = _usd({k: total[k] for k in gasto})
        REGISTRO.write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")

    print()
    print(f"esta ejecucion: {gasto['tts_llamadas']} tts ({gasto['tts_segundos']:.0f} s de audio), "
          f"{gasto['stt_llamadas']} transcripciones ({gasto['stt_segundos']:.0f} s), "
          f"~{_usd(gasto):.3f} USD en {time.time() - inicio:.0f} s")
    print(f"acumulado en el registro: ~{total['usd_estimado']:.3f} USD")


if __name__ == "__main__":
    main()
