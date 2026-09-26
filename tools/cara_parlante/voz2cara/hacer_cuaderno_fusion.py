"""Genera fusion.ipynb: la red de fusión (Blender + voz) en Colab A100, de principio a fin.

Pasos (guion /content/fusion.sh, lanzado aparte del kernel para que no muera si VS Code reconecta):
  1. datos: rasgos de voz de Obama (Drive voz2cara/voz_obama), 1KH (voz2cara/1kh.zip) y el
     audio de 1KH (voz2cara/audio_1kh.zip); audio de los discursos extraído en paralelo y
     guardado en Drive (casa_blanca/audio) para no volver a leer los vídeos;
  2. preparar_art.py con Whisper large-v3 en la GPU: palabras con tiempo → modelo articulatorio;
  3. entrenar_fusion.py: hasta 500 épocas con parada temprana; salida en Drive voz2cara/fusion
     (progreso.json se actualiza cada época).

Se edita aquí y se regenera; el .ipynb no se toca a mano.
"""
import base64
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
ARCHIVOS = {
    'extraer.py': os.path.join(AQUI, 'extraer.py'),
    'articulacion.py': os.path.join(AQUI, 'articulacion.py'),
    'preparar_art.py': os.path.join(AQUI, 'preparar_art.py'),
    'entrenar_fusion.py': os.path.join(AQUI, 'entrenar_fusion.py'),
    'modelo_articulatorio.json': os.path.join(RAIZ, 'front', 'src', 'app', 'compartido', 'boca3d',
                                              'modelo_articulatorio.json'),
}

GUION = r"""#!/bin/bash
# Red de fusión de Eos en Colab: datos → Whisper + articulación → entrenamiento. Reanudable.
set -x
CB=/content/drive/MyDrive/literalevel_cara/casa_blanca
V2C=/content/drive/MyDrive/literalevel_cara/voz2cara
D=/content/datos
mkdir -p $D/voz/obama $D/medidas/obama $D/art $CB/audio $V2C/fusion $V2C/art_obama
pip -q install faster-whisper g2p_en imageio-ffmpeg
python -c "import nltk; [nltk.download(p, quiet=True) for p in ('averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger', 'cmudict')]"
# 1. datos
cp -n $V2C/voz_obama/*.npz $D/voz/obama/
cp -n $CB/medidas/*.npz $D/medidas/obama/
cd $D && unzip -q -n $V2C/1kh.zip && unzip -q -n $V2C/audio_1kh.zip && cd /content
ls $CB/videos/*.mp4 | xargs -P 12 -I{} bash -c 'o=$0/$(basename "{}" .mp4).m4a; [ -f "$o" ] || ffmpeg -loglevel error -y -i "{}" -vn -ac 1 -ar 16000 -c:a aac -b:a 48k "$o"' $CB/audio
echo "audio obama: $(ls $CB/audio | wc -l)"
# 2. palabras (Whisper large-v3) → modelo articulatorio
cp -n $V2C/art_obama/*.npz $V2C/art_obama/*.json $D/art/ 2>/dev/null
python -u /content/preparar_art.py --medidas $D/medidas/obama --videos $CB/audio --salida $D/art --whisper large-v3-turbo --modelo_art /content/modelo_articulatorio.json
cp -n $D/art/*.npz $D/art/*.json $V2C/art_obama/
python -u /content/preparar_art.py --medidas $D/medidas/train --videos $D/audio_1kh --salida $D/art --whisper large-v3-turbo --modelo_art /content/modelo_articulatorio.json
python -u /content/preparar_art.py --medidas $D/medidas/val --videos $D/audio_1kh --salida $D/art --whisper large-v3-turbo --modelo_art /content/modelo_articulatorio.json
echo "art: $(ls $D/art/*.npz | wc -l)"
# 3. entrenar
python -u /content/entrenar_fusion.py --voz $D/voz --art $D/art --medidas $D/medidas --salida $V2C/fusion \
  --modelo_art /content/modelo_articulatorio.json --epocas 500 --paciencia 40
echo FIN
"""

CELDAS = [
('md', """# Pléyade · Eos · red de fusión (Blender + voz) — A100

La boca de Blender (precisa fonema a fonema) + la naturalidad aprendida de 28 h de caras
reales. Entorno: **A100, High-RAM**, Drive montado. Todo corre en `/content/fusion.sh`,
independiente del kernel; la última celda enseña el progreso (vuelve a ejecutarla)."""),
('code', """# --- 1. Drive (VS Code pide el permiso en un diálogo)
from google.colab import drive
drive.mount('/content/drive')"""),
('code', """# --- 2. Escribir los guiones y lanzar todo
import base64, os, subprocess, torch
print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NINGUNA')
for nombre, b64 in ARCHIVOS.items():
    open('/content/' + nombre, 'wb').write(base64.b64decode(b64))
open('/content/fusion.sh', 'w').write(GUION)
subprocess.Popen(['setsid', 'bash', '-c', 'bash /content/fusion.sh > /content/fusion.log 2>&1'],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
print('lanzado: /content/fusion.log')"""),
('code', """# --- 3. Progreso (vuelve a ejecutar esta celda con Ctrl+Enter)
!grep -a -E 'audio obama|listo|art:|entrenamiento|parada|mejor|FIN|Error|Traceback|Killed' /content/fusion.log | tail -n 6
!tail -n 3 /content/drive/MyDrive/literalevel_cara/voz2cara/fusion/progreso.json 2>/dev/null | cut -c1-220
!nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader"""),
]


def main():
    b64 = {n: base64.b64encode(open(r, 'rb').read()).decode() for n, r in ARCHIVOS.items()}
    celdas = []
    for tipo, src in CELDAS:
        if tipo == 'code' and 'ARCHIVOS.items()' in src:
            src = 'ARCHIVOS = ' + json.dumps(b64) + '\nGUION = ' + json.dumps(GUION, ensure_ascii=False) + '\n' + src
        c = {'cell_type': 'markdown' if tipo == 'md' else 'code', 'metadata': {},
             'source': src.splitlines(keepends=True)}
        if tipo == 'code':
            c.update(outputs=[], execution_count=None)
        celdas.append(c)
    nb = {'nbformat': 4, 'nbformat_minor': 0, 'cells': celdas,
          'metadata': {'colab': {'provenance': []}, 'accelerator': 'GPU',
                       'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}}}
    destino = os.path.join(AQUI, 'fusion.ipynb')
    with open(destino, 'w', encoding='utf8') as f:
        json.dump(nb, f, ensure_ascii=False)
    print(destino, os.path.getsize(destino))


if __name__ == '__main__':
    main()
