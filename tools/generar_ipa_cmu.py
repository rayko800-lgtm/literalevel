"""Genera `app/pronunciacion_cmu.tsv`: la IPA americana de CMUdict.

    python -X utf8 tools/generar_ipa_cmu.py ruta/a/cmudict.dict

Por que: el volcado de Kaikki/Wiktionary solo trae IPA para unas 40.000 de
sus 1,48 M entradas, y palabras tan corrientes como «tragic» o «magic» no la
tienen. Sin IPA, la correccion de pronunciacion no podia comparar lo que se
debia decir con lo que se entendio, y el fonema lo elegia el modelo: con la
misma grabacion dijo /dʒ/ y luego /tʃ/ cuando el error era /tr/ -> /m/ (f4,
13 sep 2026).

CMUdict (Carnegie Mellon, licencia BSD, ~134.000 palabras) es un diccionario
de pronunciacion del ingles americano. Sigue siendo un diccionario, no el
modelo: la regla de `fonemas.ipa_de_palabra` -la transcripcion no se le pide
nunca a OpenAI- se mantiene. ARPAbet pasa a los simbolos del inventario de
`fonemas` uno a uno; AH y ER se separan por el acento (AH0 -> ə, AH1 -> ʌ;
ER0 -> ɚ, ER1 -> ɝ), igual que hace Wiktionary para General American.

Solo se guarda la primera pronunciacion de cada palabra (las variantes
«word(2)» se saltan). La licencia se copia junto al archivo.

Fuente: https://github.com/cmusphinx/cmudict (cmudict.dict y LICENSE).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
# Texto plano y no .gz: Hugging Face rechaza binarios que no vayan por LFS.
SALIDA = RAIZ / "app" / "pronunciacion_cmu.tsv"
LICENCIA = RAIZ / "app" / "pronunciacion_cmu_LICENCIA.txt"

ARPABET = {
    "AA": "ɑ", "AE": "æ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ", "EH": "ɛ", "EY": "eɪ",
    "IH": "ɪ", "IY": "i", "OW": "oʊ", "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f", "G": "ɡ", "HH": "h",
    "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ", "P": "p",
    "R": "ɹ", "S": "s", "SH": "ʃ", "T": "t", "TH": "θ", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}


def a_ipa(fonos: list[str]) -> str | None:
    """ARPAbet -> IPA del inventario, con ˈ/ˌ delante de la silaba acentuada
    (solo en palabras de mas de una silaba, como Wiktionary)."""
    simbolos, acentos = [], []
    for fono in fonos:
        base, cifra = fono.rstrip("012"), fono[len(fono.rstrip("012")):]
        if base == "AH":
            s = "ə" if cifra == "0" else "ʌ"
        elif base == "ER":
            s = "ɚ" if cifra == "0" else "ɝ"
        else:
            s = ARPABET.get(base)
        if s is None:
            return None
        simbolos.append(s)
        acentos.append(cifra)
    vocales = [i for i, c in enumerate(acentos) if c]
    marcas = {}
    if len(vocales) > 1:
        for n, i in enumerate(vocales):
            if acentos[i] not in ("1", "2"):
                continue
            # El inicio de la silaba: las consonantes justo antes de la vocal,
            # dejando una en la silaba anterior si hay dos o mas entre vocales.
            inicio = i
            while inicio > 0 and not acentos[inicio - 1]:
                inicio -= 1
            if n > 0 and i - inicio >= 2:
                inicio += 1
            marcas[inicio] = "ˈ" if acentos[i] == "1" else "ˌ"
    return "/" + "".join(marcas.get(i, "") + s for i, s in enumerate(simbolos)) + "/"


def main(origen: str) -> None:
    filas, vistas = [], set()
    for linea in Path(origen).read_text(encoding="utf-8").splitlines():
        linea = linea.split("#", 1)[0].strip()
        if not linea:
            continue
        palabra, *fonos = linea.split()
        if "(" in palabra or palabra in vistas:
            continue
        ipa = a_ipa(fonos)
        if ipa:
            vistas.add(palabra)
            filas.append(f"{palabra}\t{ipa}")
    SALIDA.write_text("\n".join(filas) + "\n", encoding="utf-8", newline="\n")
    licencia = Path(origen).with_name("cmudict_LICENSE")
    if licencia.is_file():
        shutil.copyfile(licencia, LICENCIA)
    print(f"{len(filas)} palabras -> {SALIDA} ({SALIDA.stat().st_size} bytes)")


if __name__ == "__main__":
    main(sys.argv[1])
