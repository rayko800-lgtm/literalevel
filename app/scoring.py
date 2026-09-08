"""Puntuacion de dificultad LiteraLevel V4.

Port fiel de la logica de `ll_v4_transformer.py` (el script que entreno el
modelo). Las constantes y las reglas de bloques/filtrado son identicas a las
del entrenamiento: si divergieran, la app puntuaria distinto que la validacion
reportada, y las metricas dejarian de respaldar lo que ve el usuario.

Escala interna: 0..5 (A1=0, A2=1, B1=2, B2=3, C1=4, C2=5).
Escala publica: 0..2, que es interna * 0.4.
"""
from __future__ import annotations
import re, os
from dataclasses import dataclass

import numpy as np

# --- Constantes del entrenamiento (NO cambiar sin reentrenar) ---------
MODEL_NAME = "distilroberta-base"
BLOCK_WORDS = 250
MIN_WORDS = 150
MAX_BLOCKS_PER_DOC = 8
MAX_LENGTH = 256

# Ventanas por lote de inferencia. No es una constante del entrenamiento: solo
# dice de cuantas en cuantas se le dan al modelo, y esta medido que no altera
# el resultado (ver `_puntuar_bloques`). 64 es donde satura la ganancia.
LOTE_INFERENCIA = 64

ANCHORS = ["A1", "A2", "B1", "B2", "C1", "C2"]
LEVEL_VALUE = {
    "A1": 0.0, "A1+": 0.5, "A2": 1.0, "A2+": 1.5,
    "B1": 2.0, "B1+": 2.5, "B2": 3.0, "B2+": 3.5,
    "C1": 4.0, "C2": 5.0,
}

WORD_RE = re.compile(r"[A-Za-z]+(?:['\u2019-][A-Za-z]+)*")
SENT_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")
BULLET_RE = re.compile(r"^\s*(?:[-*\u2022\u25aa\u25e6]|\d+[.)]|[A-Z][.)])\s+")


def normalize(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto)).strip()


def words(texto: str) -> list[str]:
    return WORD_RE.findall(texto)


def continuous_prose(texto: str) -> tuple[bool, str]:
    """Filtro estructural conservador: descarta listas, menus y fragmentos.

    El modelo solo fue entrenado con prosa continua, asi que puntuar una tabla
    o un indice daria un numero sin significado. Devuelve (ok, motivo).
    """
    bruto = str(texto).replace("\r", "\n")
    toks = words(bruto)
    if len(toks) < MIN_WORDS:
        return False, "corto"
    frases = [s for s in SENT_RE.findall(normalize(bruto)) if len(words(s)) >= 3]
    if len(frases) < 4:
        return False, "pocas_frases"
    media_frase = float(np.mean([len(words(s)) for s in frases]))
    if not 5 <= media_frase <= 55:
        return False, "forma_de_frase"
    lineas = [l.strip() for l in bruto.splitlines() if l.strip()]
    con_vineta = sum(bool(BULLET_RE.match(l)) for l in lineas)
    cortas = sum(len(words(l)) <= 4 for l in lineas)
    if con_vineta >= 2 or (len(lineas) >= 6 and cortas / len(lineas) > 0.35):
        return False, "maquetado_de_lista"
    return True, "ok"


def fixed_blocks(texto: str, size: int = BLOCK_WORDS, minimum: int = MIN_WORDS,
                 cap: int = MAX_BLOCKS_PER_DOC) -> list[str]:
    """Ventanas fijas de palabras. La cola corta se cubre con la ultima ventana
    completa, de modo que la longitud total del documento nunca es una senal."""
    toks = words(texto)
    n = len(toks)
    if n < minimum:
        return []
    if n <= size:
        return [" ".join(toks)]
    inicios = list(range(0, n - size + 1, size))
    ultimo = n - size
    if inicios[-1] != ultimo:
        inicios.append(ultimo)
    if len(inicios) > cap:
        idx = np.linspace(0, len(inicios) - 1, cap).round().astype(int)
        inicios = [inicios[i] for i in sorted(set(idx.tolist()))]
    return [" ".join(toks[s:s + size]) for s in inicios]


def public_score(y: float) -> float:
    """Escala interna 0..5 -> escala publica 0..2."""
    return float(np.clip(y, 0, 5) * 0.4)


def public_band(score: float) -> str:
    if score < 0.8:
        return "básico"
    if score < 1.6:
        return "intermedio"
    return "avanzado"


def anchor_cefr(y: float) -> str:
    """Ancla CEFR mas cercana en la escala interna. Es orientativa: el modelo
    no certifica CEFR, solo declara alineacion de investigacion."""
    return ANCHORS[int(np.clip(round(y), 0, 5))]


@dataclass
class Resultado:
    puntuacion: float          # escala publica 0..2
    banda: str
    nivel_orientativo: str     # ancla CEFR
    interno: float             # escala 0..5
    n_bloques: int
    por_bloque: list[float]

    @property
    def confianza(self) -> str:
        """Dispersion entre bloques: mucha variacion = texto heterogeneo."""
        if self.n_bloques < 2:
            return "baja (un solo bloque)"
        sd = float(np.std(self.por_bloque))
        return "alta" if sd < 0.4 else "media" if sd < 0.8 else "baja (texto irregular)"


class Puntuador:
    """Carga el modelo v4 una sola vez y puntua textos."""

    def __init__(self, ruta_modelo: str | os.PathLike):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch

        self._torch = torch
        ruta = str(ruta_modelo)
        if not os.path.isdir(ruta):
            raise FileNotFoundError(
                f"No encuentro el modelo v4 en {ruta}.\n"
                "Descarga la carpeta 'modelo_literalevel_v4_transformer' de "
                "Drive (literalevel_bigdata) y apunta LITERALEVEL_MODELO a ella."
            )
        # Todos los hilos logicos, no solo los fisicos. Medido en esta maquina
        # (Ryzen 5 2600, 6 nucleos / 12 hilos): 6,16 -> 6,96 ventanas/s, un 13%
        # gratis. El forward esta limitado por ancho de banda de memoria, asi
        # que el escalado por encima de los nucleos fisicos es pobre pero real.
        # No cambia ni un decimal: es el mismo grafo y el mismo dtype, solo
        # cambia como reparte oneDNN. Se respeta lo que ya haya puesto el
        # entorno, que en un servidor compartido puede estar limitado a
        # proposito.
        if not os.environ.get("OMP_NUM_THREADS"):
            try:
                torch.set_num_threads(os.cpu_count() or torch.get_num_threads())
            except Exception:
                pass

        self.tokenizer = AutoTokenizer.from_pretrained(ruta)
        self.modelo = AutoModelForSequenceClassification.from_pretrained(ruta)
        self.modelo.eval()

    def _puntuar_bloques(self, bloques: list[str]) -> list[float]:
        """Puntua ventanas en lotes de tamano fijo.

        Antes el lote era "lo que traiga la llamada", que en la practica son
        las ventanas de UN capitulo: unas 20 en Crimen y Castigo y 7 en Guerra
        y Paz. Medido, agrupar de 64 en 64 sube de 6,96 a 8,19 ventanas/s (+18%)
        y satura ahi: de 64 a 300 solo se gana un 1%.

        Y no cambia el resultado, cosa que hay que justificar y no suponer: una
        ventana son 250 palabras inglesas, que al tokenizar pasan SIEMPRE de 256
        BPE y se truncan a 256. Comprobado sobre 200 ventanas: el 100% mide
        exactamente 256. Como no hay relleno, la forma del tensor por fila no
        depende de con quien vaya agrupada. Verificado ademas a la brava: las
        mismas 300 ventanas de una en una y en un solo lote dan 300/300 valores
        identicos bit a bit.
        """
        torch = self._torch
        fuera: list[float] = []
        for i in range(0, len(bloques), LOTE_INFERENCIA):
            ent = self.tokenizer(bloques[i:i + LOTE_INFERENCIA], truncation=True,
                                 max_length=MAX_LENGTH, padding=True,
                                 return_tensors="pt")
            with torch.no_grad():
                salida = self.modelo(**ent).logits.squeeze(-1).float().cpu().numpy()
            fuera.extend(float(v) for v in np.clip(np.atleast_1d(salida), 0, 5))
        return fuera


    def perfil_de_texto(self, texto: str, tope: int = 0) -> list[float]:
        """Puntuacion publica de CADA ventana del texto, sin muestrear.

        `puntuar()` se queda con 8 bloques repartidos porque su trabajo es dar un
        numero rapido. Esto es lo contrario: recorre el texto entero, ventana a
        ventana, para poder dibujar como sube y baja la dificultad a lo largo de
        un libro. Con `tope` mayor que cero se limita el numero de ventanas, para
        libros muy largos.

        Devuelve la lista vacia si el texto no da ni para una ventana; no lanza.
        """
        bloques = fixed_blocks(texto, cap=tope if tope > 0 else 10 ** 9)
        if not bloques:
            return []
        return [round(public_score(v), 3) for v in self._puntuar_bloques(bloques)]

    def puntuar(self, texto: str) -> Resultado:
        """Puntua un texto. Lanza ValueError si no es prosa continua valida.

        **El filtro va sobre el texto CRUDO, antes de normalizar.** Antes se
        normalizaba primero, y `normalize` colapsa todos los espacios en uno:
        `continuous_prose` recibia siempre una sola linea, asi que sus dos
        comprobaciones de maquetado -dos o mas vinetas, seis o mas lineas- no
        podian dispararse jamas. El detector de listas, menus y tablas era
        codigo muerto en produccion, y una carta de menu de 432 palabras se
        puntuaba como si fuera prosa. Normalizar despues, solo para trocear.
        """
        ok, motivo = continuous_prose(texto)
        if not ok:
            raise ValueError(_MOTIVOS.get(motivo, motivo))
        limpio = normalize(texto)
        bloques = fixed_blocks(limpio)
        if not bloques:
            raise ValueError(_MOTIVOS["corto"])
        por_bloque = self._puntuar_bloques(bloques)
        interno = float(np.mean(por_bloque))
        pub = public_score(interno)
        return Resultado(puntuacion=round(pub, 3), banda=public_band(pub),
                         nivel_orientativo=anchor_cefr(interno),
                         interno=round(interno, 3), n_bloques=len(bloques),
                         por_bloque=[round(v, 3) for v in por_bloque])


_MOTIVOS = {
    "corto": f"El texto es muy corto: se necesitan al menos {MIN_WORDS} palabras.",
    "pocas_frases": "Hacen falta al menos 4 frases completas.",
    "forma_de_frase": "Las frases son demasiado cortas o demasiado largas; "
                      "no parece prosa continua.",
    "maquetado_de_lista": "Parece una lista, un menú o una tabla. "
                          "LiteraLevel solo puntúa prosa continua.",
}
