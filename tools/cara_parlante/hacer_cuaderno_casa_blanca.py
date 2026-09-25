"""Genera bajar_casa_blanca.ipynb: baja los MP4 del archivo de Obama a Drive y los mide.

Todo ocurre en Colab: los vídeos van de archives.gov a Drive sin pasar por el
PC de Miguel. La medición (MediaPipe + prosodia) es la misma de
`medir_expresion.py`; en Drive quedan los vídeos y un .npz por vídeo.

Se edita aquí y se regenera; el .ipynb no se toca a mano.
"""
import json
import os

MEDIR = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medir_expresion.py'),
             encoding='utf8').read()

CELDAS = [
('md', """# LiteraLevel · discursos de la Casa Blanca de Obama → Drive

Vídeos oficiales de obamawhitehouse.archives.gov, marcados como **dominio
público** (obra del gobierno federal de EE. UU.). Se bajan directos a
`MyDrive/literalevel_cara/casa_blanca/` y se miden con MediaPipe (blendshapes
ARKit, pose de la cabeza, tono y energía). Reanudable: si una sesión se cae,
se vuelve a ejecutar y sigue donde iba.

Antes: subir `lista.csv` (de `listar_casa_blanca.py`) con «Upload to Colab»."""),
('code', """# --- 1. Drive y dependencias
# En VS Code, drive.mount() falla (MessageError request_auth): Drive se monta con
# Ctrl+Shift+P → «Colab: Mount Google Drive to Server...». En el navegador sí vale drive.mount.
import os
if not os.path.isdir('/content/drive/MyDrive'):
    try:
        from google.colab import drive
        drive.mount('/content/drive')
    except Exception as e:
        raise SystemExit('Monta Drive con «Colab: Mount Google Drive to Server...» y vuelve a ejecutar') from e
!pip -q install -U mediapipe librosa imageio-ffmpeg   # sin fijar: Colab ya va en Python 3.13
!wget -q -nc -O /content/face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
import os, csv
DESTINO = '/content/drive/MyDrive/literalevel_cara/casa_blanca'
os.makedirs(f'{DESTINO}/videos', exist_ok=True); os.makedirs(f'{DESTINO}/medidas', exist_ok=True)
lista = [f for f in ['/content/lista.csv', f'{DESTINO}/lista.csv'] if os.path.exists(f)][0]
!cp -n {lista} {DESTINO}/lista.csv
filas = list(csv.DictReader(open(lista, encoding='utf8')))
TIPOS = {'discurso_semanal', 'presidente'}
MAX_VIDEOS = 160   # ~40-60 h; subirlo si hay sitio en Drive
sel = [f for f in filas if f['tipo'] in TIPOS and f['mp4'] and f['dominio_publico'] == '1']
# primero los discursos semanales (de frente, leyendo), luego el resto; tope para no llenar Drive
sel = sorted(sel, key=lambda f: (f['tipo'] != 'discurso_semanal', f['fecha']))[:MAX_VIDEOS]
print(len(filas), 'vídeos en la lista;', len(sel), 'seleccionados (discursos del presidente, dominio público)')"""),
('code', """# --- 2. Bajar a Drive (varios a la vez; se salta lo ya bajado)
import concurrent.futures, subprocess
def bajar(f):
    nombre = f['fecha'] + '_' + f['slug'].rstrip('/').split('/')[-1][:80] + '.mp4'
    ruta = f'{DESTINO}/videos/{nombre}'
    if os.path.exists(ruta) and os.path.getsize(ruta) > 1e5:
        return 'ya'
    r = subprocess.run(['wget', '-q', '--tries=5', '-O', ruta + '.part', f['mp4']])
    if r.returncode == 0:
        os.replace(ruta + '.part', ruta); return 'ok'
    if os.path.exists(ruta + '.part'): os.remove(ruta + '.part')
    return 'fallo'
from collections import Counter
with concurrent.futures.ThreadPoolExecutor(6) as ex:
    res = Counter(ex.map(bajar, sel))
print(res)
!du -sh {DESTINO}/videos"""),
('code', """# --- 3. Medir (MediaPipe en CPU; varios procesos a la vez)
open('/content/medir_expresion.py', 'w', encoding='utf8').write(MEDIR_PY)
import glob
# primero los discursos semanales (de frente, leyendo), luego los cortos: así lo más útil se mide antes
videos = sorted(glob.glob(f'{DESTINO}/videos/*.mp4'), key=lambda v: ('weekly-address' not in v, os.path.getsize(v)))
faltan = [v for v in videos if not os.path.exists(f"{DESTINO}/medidas/{os.path.basename(v)[:-4]}.npz")]
print(len(videos), 'vídeos,', len(faltan), 'por medir')
NPROC = os.cpu_count() or 2
trozos = [faltan[i::NPROC] for i in range(NPROC)]
procs = [subprocess.Popen(['python', '/content/medir_expresion.py', '--modelo', '/content/face_landmarker.task',
                          '--salida', f'{DESTINO}/medidas', '--ancho', '640', *t], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
         for t in trozos if t]
hechos = len(videos) - len(faltan)
for p in procs:
    for linea in p.stdout:
        if 'fotogramas' in linea or 'salta' in linea:
            hechos += 1
            b = int(20 * hechos / len(videos))
            print('█' * b + '░' * (20 - b), f'{hechos}/{len(videos)}', linea.strip(), flush=True)
        elif 'Error' in linea or 'Traceback' in linea:
            print(linea.strip(), flush=True)
!ls {DESTINO}/medidas | wc -l"""),
]


def main():
    celdas = []
    for tipo, src in CELDAS:
        if tipo == 'code' and 'MEDIR_PY' in src:
            src = 'MEDIR_PY = ' + json.dumps(MEDIR, ensure_ascii=False) + '\n' + src
        c = {'cell_type': 'markdown' if tipo == 'md' else 'code', 'metadata': {},
             'source': src.splitlines(keepends=True)}
        if tipo == 'code':
            c.update(outputs=[], execution_count=None)
        celdas.append(c)
    nb = {'nbformat': 4, 'nbformat_minor': 0, 'cells': celdas,
          'metadata': {'colab': {'provenance': []},
                       'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}}}
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bajar_casa_blanca.ipynb')
    with open(destino, 'w', encoding='utf8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(destino)


if __name__ == '__main__':
    main()
