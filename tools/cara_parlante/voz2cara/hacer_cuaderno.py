"""Genera voz2cara.ipynb: rasgos wav2vec2 de los discursos de Obama y entrenamiento en GPU.

Todo ocurre en Colab (GPU gratuita): los vídeos y medidas de Obama ya están en
`MyDrive/literalevel_cara/casa_blanca/{videos,medidas}`; los rasgos de 1KH se calculan
en el PC (extraer.py) y se suben al servidor como /content/1kh.zip (rasgos + medidas).
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

1. Rasgos wav2vec2 del audio de los discursos de Obama (dominio público).
2. Entrenamiento del transformer voz→cara con Obama + TalkingHead-1KH.

Requiere un entorno **GPU (T4)** y Drive montado. El trabajo largo corre en un
guion (`/content/lanzar.sh`) lanzado desde la terminal del servidor, que no muere
si VS Code reconecta el kernel. Reanudable."""),
('code', """# --- 1. Comprobar GPU y Drive; escribir los guiones y lanzar.sh
# En VS Code, drive.mount() falla: montar con Ctrl+Shift+P → «Colab: Mount Google Drive to Server...».
import os, torch
print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NINGUNA (cambiar el entorno a T4)')
print('Drive montado:', os.path.isdir('/content/drive/MyDrive'))
CB = '/content/drive/MyDrive/literalevel_cara/casa_blanca'
V2C = '/content/drive/MyDrive/literalevel_cara/voz2cara'
open('/content/extraer.py', 'w', encoding='utf8').write(EXTRAER_PY)
open('/content/entrenar.py', 'w', encoding='utf8').write(ENTRENAR_PY)
open('/content/lanzar.sh', 'w').write(LANZAR_SH)
print('Ahora, en la terminal del servidor (Colab: Open Terminal):')
print('  nohup setsid bash /content/lanzar.sh > /content/v2c.log 2>&1 &')"""),
('code', """# --- 2. Progreso (no para nada)
!ls /content/datos/voz/obama 2>/dev/null | wc -l; ls {CB}/medidas | wc -l
!grep -a -v -i warn /content/v2c.log | tail -n 8
!nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader"""),
]


LANZAR = r"""#!/bin/bash
# Rasgos de Obama (GPU) → datos de 1KH (/content/1kh.zip, subido con «Upload to Colab», o Drive) → entrenar.
set -x
CB=/content/drive/MyDrive/literalevel_cara/casa_blanca
V2C=/content/drive/MyDrive/literalevel_cara/voz2cara
mkdir -p /content/datos/voz/obama /content/datos/medidas/obama $V2C/modelo
pip -q install imageio-ffmpeg
cp -n $CB/medidas/*.npz /content/datos/medidas/obama/
python -u /content/extraer.py --medidas /content/datos/medidas/obama --videos $CB/videos --salida /content/datos/voz/obama --dispositivo cuda
Z=/content/1kh.zip; [ -f $Z ] || Z=$V2C/1kh.zip
cd /content/datos && unzip -q -n $Z && ls voz medidas
python -u /content/entrenar.py --voz /content/datos/voz --medidas /content/datos/medidas --salida $V2C/modelo --epocas 30 --dispositivo cuda
echo FIN
"""

def main():
    celdas = []
    for tipo, src in CELDAS:
        if tipo == 'code' and 'EXTRAER_PY' in src:
            src = ('EXTRAER_PY = ' + json.dumps(EXTRAER, ensure_ascii=False) + '\n' +
                   'ENTRENAR_PY = ' + json.dumps(ENTRENAR, ensure_ascii=False) + '\n' +
                   'LANZAR_SH = ' + json.dumps(LANZAR, ensure_ascii=False) + '\n' + src)
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
