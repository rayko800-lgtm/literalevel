"""El codificador de SMIRK (Retsinas et al., CVPR 2024; código MIT) sin el resto del repositorio.

SMIRK reconstruye una cara FLAME a partir de una imagen recortada de 224×224 con tres
MobileNetV3 (pose+cámara, forma, expresión). Para ETIQUETAR solo hace falta el codificador:
los pesos públicos SMIRK_em1.pt (Google Drive del autor, sin registro) y `timm`. El modelo
FLAME del MPI (con registro) únicamente hace falta para pasar de parámetros a malla y
renderizar, y aquí no se renderiza nada: la red v3 aprende sobre los parámetros y el mapa
a ARKit (mapa_arkit.py) se ajusta con los pares SMIRK↔MediaPipe.

Salidas por imagen (los mismos nombres que en el repo, traducidos):
  expresion [50]   coeficientes de expresión FLAME
  mandibula [3]    rotación de la mandíbula (apertura ≥ 0 y dos giros pequeños)
  parpados  [2]    cierre de cada párpado en [0, 1]
  pose      [3]    rotación global (eje-ángulo); grados() la pasa a guiñada, cabeceo y alabeo
  cam       [3]    escala y traslación en la imagen
  forma     [300]  identidad (constante en un clip; se guarda la media)

Uso:
    red = cargar('SMIRK_em1.pt', 'cuda')
    tform = recorte(puntos_xy)            # matriz 2×3 para cv2.warpAffine a 224×224
    salida = red(lote_de_imagenes)        # [B, 3, 224, 224] RGB en [0, 1]
"""
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

TAMANO = 224
ESCALA_RECORTE = 1.4     # la del demo de SMIRK


def _tronco(nombre):
    import timm
    red = timm.create_model(nombre, pretrained=False, features_only=True)
    return red, red.feature_info[-1]['num_chs']


class _Codificador(nn.Module):
    def __init__(self, tronco):
        super().__init__()
        self.encoder, self.d = _tronco(tronco)

    def rasgos(self, img):
        h = self.encoder(img)[-1]
        return F.adaptive_avg_pool2d(h, (1, 1)).flatten(1)


class CodificadorPose(_Codificador):
    def __init__(self):
        super().__init__('tf_mobilenetv3_small_minimal_100')
        self.pose_cam_layers = nn.Sequential(nn.Linear(self.d, 6))

    def forward(self, img):
        pc = self.pose_cam_layers(self.rasgos(img))
        return {'pose': pc[:, :3], 'cam': pc[:, 3:]}


class CodificadorForma(_Codificador):
    def __init__(self, n=300):
        super().__init__('tf_mobilenetv3_large_minimal_100')
        self.shape_layers = nn.Sequential(nn.Linear(self.d, n))

    def forward(self, img):
        return {'forma': self.shape_layers(self.rasgos(img))}


class CodificadorExpresion(_Codificador):
    def __init__(self, n=50):
        super().__init__('tf_mobilenetv3_large_minimal_100')
        self.expression_layers = nn.Sequential(nn.Linear(self.d, n + 2 + 3))
        self.n = n

    def forward(self, img):
        p = self.expression_layers(self.rasgos(img))
        n = self.n
        return {'expresion': p[:, :n], 'parpados': torch.clamp(p[:, n:n + 2], 0, 1),
                'mandibula': torch.cat([F.relu(p[:, n + 2:n + 3]), torch.clamp(p[:, n + 3:n + 5], -.2, .2)], 1)}


class Smirk(nn.Module):
    def __init__(self):
        super().__init__()
        self.pose_encoder = CodificadorPose()
        self.shape_encoder = CodificadorForma()
        self.expression_encoder = CodificadorExpresion()

    def forward(self, img):
        out = {}
        for m in (self.pose_encoder, self.shape_encoder, self.expression_encoder):
            out.update(m(img))
        return out


def cargar(checkpoint, dispositivo='cpu'):
    """Lee SMIRK_em1.pt (guarda codificador y generador) y devuelve solo el codificador."""
    ck = torch.load(checkpoint, map_location='cpu', weights_only=True)
    pesos = {k.replace('smirk_encoder.', ''): v for k, v in ck.items() if k.startswith('smirk_encoder.')}
    red = Smirk()
    red.load_state_dict(pesos, strict=True)
    return red.to(dispositivo).eval()


def caja(puntos):
    """Centro (x, y) y lado del recorte cuadrado a partir de los puntos MediaPipe [478, 2] en píxeles."""
    izq, der = puntos[:, 0].min(), puntos[:, 0].max()
    arr, aba = puntos[:, 1].min(), puntos[:, 1].max()
    lado = (der - izq + aba - arr) / 2 * ESCALA_RECORTE
    return np.array([(izq + der) / 2, (arr + aba) / 2]), float(lado)


def recorte(centro, lado):
    """Matriz 2×3 (cv2.warpAffine) que lleva el cuadrado de `lado` centrado en `centro` a 224×224."""
    s = (TAMANO - 1) / lado
    return np.array([[s, 0, TAMANO / 2 - 0.5 - s * centro[0]], [0, s, TAMANO / 2 - 0.5 - s * centro[1]]], np.float32)


def recortar(img_bgr, centro, lado):
    """Imagen 224×224 RGB uint8 lista para la red (permute y /255 se hacen en el lote)."""
    rec = cv2.warpAffine(img_bgr, recorte(centro, lado), (TAMANO, TAMANO), flags=cv2.INTER_LINEAR)
    return cv2.cvtColor(rec, cv2.COLOR_BGR2RGB)


def grados(pose):
    """Eje-ángulo FLAME [N, 3] → grados (guiñada, cabeceo, alabeo) con la misma convención que
    medir_expresion.pose_de_matriz (para que el mapa lineal a la pose de MediaPipe sea sencillo)."""
    out = np.zeros_like(pose, dtype=np.float32)
    for i, v in enumerate(pose):
        r, _ = cv2.Rodrigues(np.asarray(v, np.float64))
        cabeceo = np.degrees(np.arctan2(r[2, 1], r[2, 2]))
        guinada = np.degrees(np.arcsin(-np.clip(r[2, 0], -1, 1)))
        alabeo = np.degrees(np.arctan2(r[1, 0], r[0, 0]))
        out[i] = (guinada, cabeceo, alabeo)
    return out
