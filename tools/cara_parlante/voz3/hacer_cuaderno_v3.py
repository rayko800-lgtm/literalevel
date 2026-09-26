"""Genera v3.ipynb: la versión 3 de la cara de Eos en Colab (A100 High-RAM; funciona en T4 con
menos capas y lotes), de principio a fin y reanudable.

Guion /content/v3.sh, lanzado con setsid (sigue vivo si el kernel o VS Code se caen). Pasos, cada
uno se salta lo ya hecho:
  0. paquetes; SMIRK_em1.pt (Drive del autor, sin registro) y face_landmarker.task, guardados en Drive;
     medidas de Obama y de 1KH (voz2cara/1kh.zip) y audio de 1KH (voz2cara/audio_1kh.zip) a /content/datos;
     audio de los discursos de Obama en casa_blanca/audio (ya lo dejó fusion.sh; si falta, se extrae).
  1. PILOTO: SMIRK sobre ~1 h de Obama + fiabilidad.py → v3/fiabilidad_piloto.json. Con SOLO_PILOTO=1
     el guion termina aquí (para mirar el informe antes de gastar la GPU en todo).
  2. Etiquetado SMIRK completo: Obama en N_PROC procesos a la vez (MediaPipe va en CPU); 1KH solo si
     hay vídeos en voz2cara/1kh_videos.zip (los .mp4 no están en Drive) o etiquetas ya subidas a v3/smirk/1kh.
  3. mapa_arkit.py con todos los pares → v3/mapa_arkit.json.
  4. Rasgos de voz (HuBERT-large, 7 capas, 25 Hz) → v3/voz (~36 GB en Drive).
  5. Articulación de Blender (Whisper large-v3-turbo): Obama copiada de voz2cara/art_obama, 1KH nueva → v3/art.
  6. entrenar_boca.py → v3/boca; entrenar_noverbal.py → v3/noverbal (ultimo.pt reanuda solos).
estado_v3.py escribe cada minuto v3/estado.txt (líneas cortas). La última celda lo enseña.

Se edita aquí y se regenera: python hacer_cuaderno_v3.py  → v3.ipynb al lado. El .ipynb no se toca a mano.
"""
import base64
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
V2C = os.path.join(AQUI, '..', 'voz2cara')
ARCHIVOS = {
    'tools/cara_parlante/voz3/' + n: os.path.join(AQUI, n) for n in
    ('smirk_codificador.py', 'etiquetar_smirk.py', 'datos_v3.py', 'mapa_arkit.py', 'fiabilidad.py', 'extraer_v3.py',
     'red_v3.py', 'entrenar_boca.py', 'entrenar_noverbal.py', 'estado_v3.py')
}
ARCHIVOS.update({'tools/cara_parlante/voz2cara/' + n: os.path.join(V2C, n) for n in ('extraer.py', 'articulacion.py', 'preparar_art.py')})
ARCHIVOS['modelo_articulatorio.json'] = os.path.join(RAIZ, 'front', 'src', 'app', 'compartido', 'boca3d', 'modelo_articulatorio.json')

GUION = r"""#!/bin/bash
# Eos v3 en Colab: SMIRK → fiabilidad → etiquetas → voz → articulación → boca + no verbal. Reanudable.
# Variables: SOLO_PILOTO=1 (parar tras el piloto), N_PROC (procesos de etiquetado), CODIFICADOR (hubert-large|wavlm-large).
set -x
CB=/content/drive/MyDrive/literalevel_cara/casa_blanca
V2C=/content/drive/MyDrive/literalevel_cara/voz2cara
V3=$V2C/v3
D=/content/datos
S=/content/tools/cara_parlante
N_PROC=${N_PROC:-6}
CODIFICADOR=${CODIFICADOR:-hubert-large}
mkdir -p $D/medidas/obama $D/cache $V3/smirk/obama $V3/smirk/1kh $V3/voz/obama $V3/voz/1kh $V3/art $V3/boca $V3/noverbal $CB/audio
paso() { echo "### $1"; }
falla() { paso "ERROR en $1"; exit 1; }

paso "0 preparar"
pip -q install timm mediapipe gdown imageio-ffmpeg faster-whisper g2p_en 2>&1 | tail -n 2
python -c "import nltk; [nltk.download(p, quiet=True) for p in ('averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger', 'cmudict')]"
[ -f $V3/SMIRK_em1.pt ] || gdown 1T65uEd9dVLHgVw5KiUYL66NUee-MCzoE -O $V3/SMIRK_em1.pt || falla "descarga SMIRK"
[ -f $V3/face_landmarker.task ] || wget -q -O $V3/face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
cp -n $CB/medidas/*.npz $D/medidas/obama/
cd $D && unzip -q -n $V2C/1kh.zip && unzip -q -n $V2C/audio_1kh.zip && cd /content
[ -f $V2C/1kh_videos.zip ] && { mkdir -p $D/1kh && cd $D/1kh && unzip -q -n $V2C/1kh_videos.zip && cd /content; }
ls $CB/videos/*.mp4 | xargs -P 8 -I{} bash -c 'o=$0/$(basename "{}" .mp4).m4a; [ -f "$o" ] || ffmpeg -loglevel error -y -i "{}" -vn -ac 1 -ar 16000 -c:a aac -b:a 48k "$o"' $CB/audio
# GPU pequeña (T4): menos capas, lotes más cortos
MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n 1)
if [ "${MEM:-0}" -lt 20000 ]; then EXTRA="--lote 16 --capas_usar 12,18,24"; BOCA_EXTRA="--d 256 --capas 4"; else EXTRA="--lote 48"; BOCA_EXTRA=""; fi
SM="--checkpoint $V3/SMIRK_em1.pt --landmarker $V3/face_landmarker.task"

paso "1 piloto SMIRK (1 h de Obama)"
LISTA=$(python - <<'EOF'
import glob, numpy as np, os
s, out = 0.0, []
for f in sorted(glob.glob('/content/datos/medidas/obama/*.npz')):
    t = np.load(f)['t']; out.append(os.path.splitext(os.path.basename(f))[0]); s += t[-1]
    if s >= 3600: break
print(','.join(out))
EOF
)
for i in $(seq 1 $N_PROC); do
  python -u $S/voz3/etiquetar_smirk.py --medidas $D/medidas/obama --videos $CB/videos --salida $V3/smirk/obama $SM --lista "$LISTA" --parte $i/$N_PROC > /content/smirk_piloto_$i.log 2>&1 &
done; wait
grep -h "listo:" /content/smirk_piloto_*.log
python -u $S/voz3/fiabilidad.py --smirk $V3/smirk/obama --medidas $D/medidas/obama --salida $V3/fiabilidad_piloto.json | tail -n 8
[ "${SOLO_PILOTO:-0}" = "1" ] && { paso "FIN (solo piloto)"; exit 0; }

paso "2 etiquetado SMIRK completo"
for i in $(seq 1 $N_PROC); do
  python -u $S/voz3/etiquetar_smirk.py --medidas $D/medidas/obama --videos $CB/videos --salida $V3/smirk/obama $SM --parte $i/$N_PROC > /content/smirk_obama_$i.log 2>&1 &
done; wait
if [ -d $D/1kh ]; then
  for i in $(seq 1 $N_PROC); do
    python -u $S/voz3/etiquetar_smirk.py --medidas $D/medidas --videos $D/1kh --salida $V3/smirk/1kh $SM --parte $i/$N_PROC > /content/smirk_1kh_$i.log 2>&1 &
  done; wait
fi
grep -h "listo:" /content/smirk_*.log; grep -h ERROR /content/smirk_*.log | head -n 5

paso "3 mapa SMIRK→ARKit"
python -u $S/voz3/mapa_arkit.py --smirk $V3/smirk --medidas $D/medidas --salida $V3/mapa_arkit.json || falla "mapa"

paso "4 rasgos de voz ($CODIFICADOR)"
python -u $S/voz3/extraer_v3.py --medidas $D/medidas/obama --audio $CB/audio --salida $V3/voz/obama --codificador $CODIFICADOR || falla "voz obama"
python -u $S/voz3/extraer_v3.py --medidas $D/medidas --audio $D/audio_1kh --salida $V3/voz/1kh --codificador $CODIFICADOR || falla "voz 1kh"

paso "5 articulación de Blender (Whisper)"
cp -n $V2C/art_obama/*.npz $V2C/art_obama/*.json $V3/art/ 2>/dev/null
python -u $S/voz2cara/preparar_art.py --medidas $D/medidas/obama --videos $CB/audio --salida $V3/art --whisper large-v3-turbo --modelo_art /content/modelo_articulatorio.json
python -u $S/voz2cara/preparar_art.py --medidas $D/medidas --videos $D/audio_1kh --salida $V3/art --whisper large-v3-turbo --modelo_art /content/modelo_articulatorio.json

paso "6a entrenar boca"
python -u $S/voz3/entrenar_boca.py --voz $V3/voz --art $V3/art --smirk $V3/smirk --mapa $V3/mapa_arkit.json --salida $V3/boca \
  --modelo_art /content/modelo_articulatorio.json --cache $D/cache --epocas 300 --paciencia 30 $EXTRA $BOCA_EXTRA || falla "boca"
paso "6b entrenar no verbal"
python -u $S/voz3/entrenar_noverbal.py --voz $V3/voz --art $V3/art --smirk $V3/smirk --medidas $D/medidas --mapa $V3/mapa_arkit.json \
  --salida $V3/noverbal --cache $D/cache --epocas 300 --paciencia 30 $EXTRA || falla "no verbal"
paso "FIN"
"""

CELDAS = [
('md', """# Pléyade · Eos · cara v3 (SMIRK + HuBERT + boca por regresión + no verbal generativo) — A100

Entorno: **A100, High-RAM**, Drive montado (funciona en T4, más lento y con menos capas de voz).
Todo corre en `/content/v3.sh`, independiente del kernel. Salidas en Drive
`literalevel_cara/voz2cara/v3/`: `fiabilidad_piloto.json`, `smirk/`, `mapa_arkit.json`, `voz/`,
`art/`, `boca/`, `noverbal/` y `estado.txt` (se reescribe cada minuto).

Para Eos en el PC: copiar `v3/boca/{modelo.pt,normalizacion.json}` y `v3/noverbal/{...}` a
`D:/literalevel_cara/v3_modelo/{boca,noverbal}/` y `generar.py --gestos v3`."""),
('code', """# --- 1. Drive (VS Code pide el permiso en un diálogo)
from google.colab import drive
drive.mount('/content/drive')"""),
('code', """# --- 2. Escribir los guiones y lanzar todo
SOLO_PILOTO = 0      # 1: parar tras el piloto de fiabilidad (1 h de Obama) y mirar fiabilidad_piloto.json
N_PROC = 6           # procesos de etiquetado SMIRK a la vez (MediaPipe va en CPU; el A100 High-RAM tiene 12 vCPU)
CODIFICADOR = 'hubert-large'   # o 'wavlm-large'
import base64, os, subprocess, torch
print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NINGUNA')
for nombre, b64 in ARCHIVOS.items():
    os.makedirs(os.path.dirname('/content/' + nombre) or '/content', exist_ok=True)
    open('/content/' + nombre, 'wb').write(base64.b64decode(b64))
open('/content/v3.sh', 'w').write(GUION)
env = dict(os.environ, SOLO_PILOTO=str(SOLO_PILOTO), N_PROC=str(N_PROC), CODIFICADOR=CODIFICADOR)
subprocess.Popen(['setsid', 'bash', '-c', 'bash /content/v3.sh > /content/v3.log 2>&1'],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, env=env)
V3 = '/content/drive/MyDrive/literalevel_cara/voz2cara/v3'
os.makedirs(V3, exist_ok=True)
subprocess.Popen(['setsid', 'python', '/content/tools/cara_parlante/voz3/estado_v3.py', '--log', '/content/v3.log',
                  '--v3', V3, '--medidas', '/content/datos/medidas'],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
print('lanzado: /content/v3.log y', V3 + '/estado.txt')"""),
('code', """# --- 3. Estado (vuelve a ejecutar esta celda con Ctrl+Enter)
!cat /content/drive/MyDrive/literalevel_cara/voz2cara/v3/estado.txt 2>/dev/null
!grep -a -E '^### |listo|por grupo|parada|Error|Traceback|Killed' /content/v3.log | tail -n 8"""),
]


def main():
    b64 = {n: base64.b64encode(open(r, 'rb').read()).decode() for n, r in ARCHIVOS.items()}
    celdas = []
    for tipo, src in CELDAS:
        if tipo == 'code' and 'ARCHIVOS.items()' in src:
            src = 'ARCHIVOS = ' + json.dumps(b64) + '\nGUION = ' + json.dumps(GUION, ensure_ascii=False) + '\n' + src
        c = {'cell_type': 'markdown' if tipo == 'md' else 'code', 'metadata': {}, 'source': src.splitlines(keepends=True)}
        if tipo == 'code':
            c.update(outputs=[], execution_count=None)
        celdas.append(c)
    nb = {'nbformat': 4, 'nbformat_minor': 0, 'cells': celdas,
          'metadata': {'colab': {'provenance': []}, 'accelerator': 'GPU', 'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}}}
    destino = os.path.join(AQUI, 'v3.ipynb')
    with open(destino, 'w', encoding='utf8') as f:
        json.dump(nb, f, ensure_ascii=False)
    print(destino, os.path.getsize(destino))


if __name__ == '__main__':
    main()
