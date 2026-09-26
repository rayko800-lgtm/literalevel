"""Estado compacto del cuaderno v3, escrito cada minuto en Drive (voz2cara/v3/estado.txt) para
seguirlo desde el teléfono o desde otra sesión sin abrir el log: líneas cortas, sin listas.

Lee: el log del guion (/content/v3.log: la última línea «### paso» dice en qué paso va), los
recuentos de etiquetas y rasgos hechos frente a los que hay que hacer, la última línea de
progreso.json de cada entrenamiento y la GPU. Se lanza con setsid desde el guion; muere solo
cuando aparece FIN o ERROR en el log (tras escribir el estado final).

Uso: python estado_v3.py --log /content/v3.log --v3 /content/drive/MyDrive/literalevel_cara/voz2cara/v3
        --medidas /content/datos/medidas [--cada 60]
"""
import argparse
import glob
import json
import os
import subprocess
import time


def ultimo(patron, ruta):
    if not os.path.exists(ruta):
        return ''
    lineas = [l for l in open(ruta, errors='replace') if patron in l]
    return lineas[-1].strip() if lineas else ''


def cuenta(d):
    return len(glob.glob(os.path.join(d, '**', '*.npz'), recursive=True))


def progreso(d):
    p = os.path.join(d, 'progreso.json')
    if not os.path.exists(p):
        return 'sin empezar'
    lineas = open(p).read().strip().splitlines()
    if not lineas:
        return 'sin empezar'
    u = json.loads(lineas[-1])
    inf = os.path.join(d, 'informe.json')
    mejor = json.load(open(inf)).get('mejor_epoca', '?') if os.path.exists(inf) else '?'
    if 'r_boca' in u:
        return f"época {u['epoca']} r boca {u['r_boca']} (mejor: época {mejor}) pedagogía {u['pedagogia']} {u['s']} s/época"
    return (f"época {u['epoca']} pérdida val {u['perdida_val']} (mejor: época {mejor}) r {u['r']} fdd {u['fdd']} "
            f"diversidad {u['diversidad']} alineación {u['alineacion']} {u['s']} s/época")


def gpu():
    try:
        r = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader'],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:
        return 'sin nvidia-smi'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True); ap.add_argument('--v3', required=True); ap.add_argument('--medidas', required=True)
    ap.add_argument('--cada', type=int, default=60)
    a = ap.parse_args()
    while True:
        paso = ultimo('### ', a.log)
        n_med = cuenta(a.medidas)
        lineas = [time.strftime('%H:%M:%S') + '  ' + (paso or 'arrancando'),
                  f'etiquetas SMIRK: {cuenta(os.path.join(a.v3, "smirk"))}/{n_med} clips',
                  f'rasgos de voz: {cuenta(os.path.join(a.v3, "voz"))}/{n_med} clips',
                  f'articulación: {cuenta(os.path.join(a.v3, "art"))}/{n_med} clips',
                  'boca: ' + progreso(os.path.join(a.v3, 'boca')),
                  'no verbal: ' + progreso(os.path.join(a.v3, 'noverbal')),
                  'GPU: ' + gpu()]
        err = ultimo('Traceback', a.log) or ultimo('Killed', a.log)
        if err:
            lineas.append('AVISO en el log: ' + err[:120])
        try:
            with open(os.path.join(a.v3, 'estado.txt.tmp'), 'w') as f:
                f.write('\n'.join(lineas) + '\n')
            os.replace(os.path.join(a.v3, 'estado.txt.tmp'), os.path.join(a.v3, 'estado.txt'))
        except OSError:
            pass
        if paso.startswith('### FIN') or paso.startswith('### ERROR'):
            break
        time.sleep(a.cada)


if __name__ == '__main__':
    main()
