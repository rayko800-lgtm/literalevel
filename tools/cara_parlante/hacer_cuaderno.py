"""Genera entrenar_expresion.ipynb (Colab, GPU) a partir de las celdas de abajo.

Se edita aquí y se regenera; el .ipynb no se toca a mano.
"""
import json
import os

CELDAS = [
('md', """# LiteraLevel · la vida de la cara: expresión desde la prosodia

Aprende, a partir de vídeos de gente hablando (TalkingHead-1KH, CC BY 3.0),
cómo se mueven **cejas, cabeza y sonrisa** según el tono y la energía de la
voz. La boca no se toca: la mueve el modelo articulatorio.

Datos: los `.npz` de `tools/cara_parlante/medir_expresion.py`, subidos a
`MyDrive/literalevel_cara/medidas/`. Reparto por **vídeo** (hablante): ningún
hablante de validación sale en entrenamiento.

Licencia de los datos: CC BY 3.0 (atribución en `creditos.csv`). Nada de
MetaHuman entra aquí: su EULA prohíbe usar MetaHumans para entrenar o probar IA."""),
('code', """# --- 1. Drive y dependencias
from google.colab import drive
drive.mount('/content/drive')
BASE = '/content/drive/MyDrive/literalevel_cara'
import glob, json, os, numpy as np, torch
from torch import nn
DISP = 'cuda' if torch.cuda.is_available() else 'cpu'
print(DISP, torch.cuda.get_device_name(0) if DISP == 'cuda' else '')"""),
('code', """# --- 2. Carga: entradas de prosodia, salidas de expresión
SALIDAS = ['browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 'browDownLeft', 'browDownRight',
           'mouthSmileLeft', 'mouthSmileRight']
POSE = ['guinada', 'cabeceo', 'alabeo']

def cargar(ruta):
    d = np.load(ruta)
    if d['ok'].mean() < 0.9:
        return None
    n = list(d['bs_nombres'])
    f0, db = d['f0'].astype(np.float32), d['db'].astype(np.float32)
    voz = (f0 > 0).astype(np.float32)
    lf0 = np.zeros_like(f0)
    if voz.sum() > 10:
        l = np.log(f0[voz > 0]); lf0[voz > 0] = (l - l.mean()) / (l.std() + 1e-6)
    dbn = (db - db.mean()) / (db.std() + 1e-6)
    x = np.stack([lf0, voz, dbn, np.gradient(lf0), np.gradient(dbn)], 1)
    bs = d['bs'][:, [n.index(s) for s in SALIDAS]]
    pose = d['pose'] - np.median(d['pose'], 0)       # respecto a la postura del clip
    y = np.concatenate([bs, pose / 10.0], 1)            # grados/10: misma escala que los blendshapes
    return dict(x=x, y=y.astype(np.float32), video=os.path.basename(ruta).rsplit('_', 1)[0])

clips = [c for c in (cargar(r) for r in sorted(glob.glob(f'{BASE}/medidas/*/*.npz'))) if c]
videos = sorted({c['video'] for c in clips})
rng = np.random.default_rng(0); rng.shuffle(videos)
val_v = set(videos[: max(1, len(videos) // 5)])
tr = [c for c in clips if c['video'] not in val_v]; va = [c for c in clips if c['video'] in val_v]
print(len(clips), 'clips,', len(videos), 'vídeos;', len(tr), 'entrenamiento,', len(va), 'validación',
      f"{sum(len(c['x']) for c in clips) / 25 / 3600:.1f} h")"""),
('code', """# --- 3. Modelo: TCN con poca anticipación (sirve para TTS y, más adelante, para streaming)
K_IN, K_OUT = 5, len(SALIDAS) + len(POSE)

class Bloque(nn.Module):
    def __init__(self, c, dil, k=5, drop=0.1):
        super().__init__()
        self.conv = nn.Conv1d(c, c, k, dilation=dil, padding=dil * (k - 1) // 2)
        self.norm = nn.GroupNorm(1, c); self.drop = nn.Dropout(drop)
    def forward(self, x):
        return x + self.drop(torch.relu(self.norm(self.conv(x))))

class Expresion(nn.Module):
    def __init__(self, c=64, dils=(1, 2, 4, 8, 16)):
        super().__init__()
        self.ent = nn.Conv1d(K_IN, c, 1)
        self.bloques = nn.Sequential(*[Bloque(c, d) for d in dils])
        self.sal = nn.Conv1d(c, K_OUT, 1)
    def forward(self, x):                      # x: (B, T, K_IN)
        return self.sal(self.bloques(self.ent(x.transpose(1, 2)))).transpose(1, 2)

def ventanas(cl, largo=250):                   # trozos de 10 s
    xs, ys = [], []
    for c in cl:
        for i in range(0, len(c['x']) - largo + 1, largo // 2):
            xs.append(c['x'][i:i + largo]); ys.append(c['y'][i:i + largo])
    return torch.tensor(np.array(xs)), torch.tensor(np.array(ys))

Xtr, Ytr = ventanas(tr); Xva, Yva = ventanas(va)
print(Xtr.shape, Xva.shape)"""),
('code', """# --- 4. Entrenamiento
torch.manual_seed(0)
m = Expresion().to(DISP)
opt = torch.optim.AdamW(m.parameters(), 2e-3, weight_decay=1e-4)
for ep in range(40):
    m.train(); perm = torch.randperm(len(Xtr))
    for i in range(0, len(perm), 64):
        b = perm[i:i + 64]
        loss = nn.functional.mse_loss(m(Xtr[b].to(DISP)), Ytr[b].to(DISP))
        opt.zero_grad(); loss.backward(); opt.step()
    if ep % 5 == 4:
        m.eval()
        with torch.no_grad():
            lv = nn.functional.mse_loss(m(Xva.to(DISP)), Yva.to(DISP)).item()
        print(ep + 1, f'{loss.item():.4f}', f'val {lv:.4f}')"""),
('code', """# --- 5. ¿Aprende algo? r de Pearson por salida en validación, contra no predecir nada
m.eval()
with torch.no_grad():
    P = m(Xva.to(DISP)).cpu().numpy().reshape(-1, K_OUT)
Y = Yva.numpy().reshape(-1, K_OUT)
for j, nom in enumerate(SALIDAS + POSE):
    r = np.corrcoef(P[:, j], Y[:, j])[0, 1]
    print(f'{nom:18s} r={r:+.2f}   sd real {Y[:, j].std():.3f}  sd predicha {P[:, j].std():.3f}')
print('Ojo: con MSE la predicción sale más plana que la real (sd menor). En la cara se suma',
      'ruido con la sd real que falte; la r dice si el *cuándo* está bien.')"""),
('code', """# --- 6. Exportar pesos a JSON (el front los lee sin dependencias, como el modelo articulatorio)
pesos = {k: v.detach().cpu().numpy().round(5).tolist() for k, v in m.state_dict().items()}
meta = dict(entradas=['lf0', 'voz', 'db', 'dlf0', 'ddb'], salidas=SALIDAS + POSE,
            escala_pose_grados=10.0, fps=25, arquitectura='Expresion(c=64, dils=1..16, k=5)')
os.makedirs(f'{BASE}/modelos', exist_ok=True)
with open(f'{BASE}/modelos/expresion.json', 'w') as f:
    json.dump(dict(meta=meta, pesos=pesos), f)
print(os.path.getsize(f'{BASE}/modelos/expresion.json') / 1e6, 'MB')"""),
]


def main():
    celdas = []
    for tipo, src in CELDAS:
        c = {'cell_type': 'markdown' if tipo == 'md' else 'code', 'metadata': {},
             'source': src.splitlines(keepends=True)}
        if tipo == 'code':
            c.update(outputs=[], execution_count=None)
        celdas.append(c)
    nb = {'nbformat': 4, 'nbformat_minor': 0, 'cells': celdas,
          'metadata': {'accelerator': 'GPU', 'colab': {'gpuType': 'T4', 'provenance': []},
                       'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}}}
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'entrenar_expresion.ipynb')
    with open(destino, 'w', encoding='utf8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(destino)


if __name__ == '__main__':
    main()
