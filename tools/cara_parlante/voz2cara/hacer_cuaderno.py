"""Genera voz2cara.ipynb: rasgos wav2vec2 de los discursos de Obama y entrenamiento en GPU.

Todo ocurre en Colab (GPU gratuita): los vídeos y medidas de Obama ya están en
`MyDrive/literalevel_cara/casa_blanca/{videos,medidas}`; los rasgos de 1KH se calculan
en el PC (extraer.py) y se suben a Drive como `voz2cara/1kh.zip` (rasgos + medidas).
Deja en `MyDrive/literalevel_cara/voz2cara/modelo/` modelo.pt, normalizacion.json e informe.json.

Se edita aquí y se regenera; el .ipynb no se toca a mano.
"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
EXTRAER = open(os.path.join(AQUI, 'extraer.py'), encoding='utf8').read()
ENTRENAR = open(os.path.join(AQUI, 'entrenar.py'), encoding='utf8').read()

CELDAS = [
('md', """# Pléyade · Eos · modelo voz→cara (GPU)

1. Rasgos wav2vec2 del audio de los discursos de Obama (dominio público) → Drive.
2. Entrenamiento del transformer voz→cara con Obama + TalkingHead-1KH.

Requiere un entorno **GPU (T4 gratuita)** y Drive montado. Reanudable."""),
('code', """# --- 1. Drive, dependencias y guiones
# En VS Code, drive.mount() falla: montar con Ctrl+Shift+P → «Colab: Mount Google Drive to Server...».
import os
if not os.path.isdir('/content/drive/MyDrive'):
    try:
        from google.colab import drive
        drive.mount('/content/drive')
    except Exception as e:
        raise SystemExit('Monta Drive con «Colab: Mount Google Drive to Server...» y vuelve a ejecutar') from e
!pip -q install imageio-ffmpeg
import torch; print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NINGUNA (cambiar el entorno a T4)')
CB = '/content/drive/MyDrive/literalevel_cara/casa_blanca'
V2C = '/content/drive/MyDrive/literalevel_cara/voz2cara'
os.makedirs(V2C, exist_ok=True)
open('/content/extraer.py', 'w', encoding='utf8').write(EXTRAER_PY)
open('/content/entrenar.py', 'w', encoding='utf8').write(ENTRENAR_PY)"""),
('code', """# --- 2. Rasgos de Obama (GPU, ~10-20 min; reanudable). Se guardan en local y en Drive
!mkdir -p /content/datos/voz/obama /content/datos/medidas/obama
!cp -n {V2C}/voz_obama/*.npz /content/datos/voz/obama/ 2>/dev/null; cp -n {CB}/medidas/*.npz /content/datos/medidas/obama/
!python -u /content/extraer.py --medidas /content/datos/medidas/obama --videos {CB}/videos --salida /content/datos/voz/obama --dispositivo cuda
!mkdir -p {V2C}/voz_obama && cp -n /content/datos/voz/obama/*.npz {V2C}/voz_obama/
!ls /content/datos/voz/obama | wc -l"""),
('code', """# --- 3. Rasgos y medidas de 1KH (subidos desde el PC como voz2cara/1kh.zip)
!cd /content/datos && unzip -q -n {V2C}/1kh.zip && ls voz medidas"""),
('code', """# --- 4. Entrenar (GPU). Validación: 1KH val + 1 de cada 8 discursos de Obama
!python -u /content/entrenar.py --voz /content/datos/voz --medidas /content/datos/medidas --salida {V2C}/modelo --epocas 30 --dispositivo cuda
!cat {V2C}/modelo/informe.json | head -n 12"""),
]


def main():
    celdas = []
    for tipo, src in CELDAS:
        if tipo == 'code' and 'EXTRAER_PY' in src:
            src = ('EXTRAER_PY = ' + json.dumps(EXTRAER, ensure_ascii=False) + '\n' +
                   'ENTRENAR_PY = ' + json.dumps(ENTRENAR, ensure_ascii=False) + '\n' + src)
        c = {'cell_type': 'markdown' if tipo == 'md' else 'code', 'metadata': {},
             'source': src.splitlines(keepends=True)}
        if tipo == 'code':
            c.update(outputs=[], execution_count=None)
        celdas.append(c)
    nb = {'nbformat': 4, 'nbformat_minor': 0, 'cells': celdas,
          'metadata': {'colab': {'provenance': []}, 'accelerator': 'GPU',
                       'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}}}
    destino = os.path.join(AQUI, 'voz2cara.ipynb')
    with open(destino, 'w', encoding='utf8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(destino)


if __name__ == '__main__':
    main()
