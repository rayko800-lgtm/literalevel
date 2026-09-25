"""Estado de los lotes de datos de la cara, con barras y aviso de atascos.

Un lote está ATASCADO si su proceso sigue vivo pero no ha escrito nada
(log ni resultados) en los últimos --minutos minutos.

Uso: python estado.py [--minutos 10]
"""
import argparse
import glob
import os
import re
import subprocess
import time

BASE = 'D:/literalevel_cara'


def barra(n, total, ancho=20):
    total = max(total, 1)
    lleno = int(ancho * min(n, total) / total)
    return '█' * lleno + '░' * (ancho - lleno) + f' {n}/{total} ({100 * n / total:.0f} %)'


def ultimo_cambio(*patrones):
    t = 0
    for p in patrones:
        for f in glob.glob(p):
            t = max(t, os.path.getmtime(f))
    return t


def vivo(patron):
    r = subprocess.run(['powershell', '-NoProfile', '-Command',
                        f"@(Get-CimInstance Win32_Process | Where-Object {{ $_.CommandLine -match '{patron}' "
                        "-and $_.Name -match 'python' }).Count"], capture_output=True, text=True)
    return (r.stdout.strip() or '0') != '0'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--minutos', type=float, default=10)
    a = ap.parse_args()
    ahora = time.time()
    lineas = []

    def fila(nombre, n, total, patron, *rutas):
        v = vivo(patron)
        quieto = (ahora - ultimo_cambio(*rutas)) / 60
        if n >= total:
            est = '✅ terminado'
        elif not v:
            est = '⏸️ parado'
        elif quieto > a.minutos:
            est = f'🔴 ATASCADO ({quieto:.0f} min sin avanzar)'
        else:
            est = f'🟢 avanzando (último cambio hace {quieto:.0f} min)'
        lineas.append(f'{nombre:<24} {barra(n, total)}  {est}')

    # Casa Blanca: lista
    log = f'{BASE}/casa_blanca/listar.log'
    t = open(log, encoding='utf8', errors='replace').read() if os.path.exists(log) else ''
    m = re.findall(r'(\d+) / (\d+)', t)
    n, tot = (int(m[-1][0]), int(m[-1][1])) if m else (0, 2470)
    if 'Traceback' not in t and not vivo('listar_casa_blanca') and os.path.exists(f'{BASE}/casa_blanca/lista.csv')             and sum(1 for _ in open(f'{BASE}/casa_blanca/lista.csv', encoding='utf8')) > tot:
        n = tot
    fila('Obama · lista', n, tot, 'listar_casa_blanca', log, f'{BASE}/casa_blanca/cache_html/*')

    # TalkingHead-1KH
    clips = len(glob.glob(f'{BASE}/1kh/train/*.mp4'))
    med = len(glob.glob(f'{BASE}/medidas/train/*.npz'))
    fila('YouTube CC BY · medir', med, clips, 'medir_expresion.py.*1kh', f'{BASE}/medidas/train/*.npz')

    # Miralles
    hechos = len(glob.glob(f'{BASE}/medidas/miralles/*.npz'))
    fila('Miralles · bajar+medir', hechos, 40, 'bajar_medir_borrar', f'{BASE}/miralles/lote.log',
         f'{BASE}/medidas/miralles/*', f'{BASE}/medidas/tmp*/*')

    print('\n'.join(lineas))


if __name__ == '__main__':
    main()
