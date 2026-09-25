"""Lista los vídeos del archivo de la Casa Blanca de Obama con su MP4 directo.

obamawhitehouse.archives.gov (NARA) marca los vídeos como dominio público
(obra del gobierno federal de EE. UU.) y ofrece el MP4 en HD sin pasar por
YouTube. Cada página de vídeo lleva una lista paginada de todos los vídeos
(index__q_page=N.html, ~17 por página); se recorre entera y, por vídeo, se
saca el título, el MP4 y si la página dice «Public Domain».

Salida: CSV con fecha, slug, título, mp4, mp3, dominio_publico, tipo.
  tipo = discurso_semanal | presidente | otro   (por el slug y el título)

Reanudable: guarda las páginas ya leídas en un caché.

Uso: python listar_casa_blanca.py --salida D:/literalevel_cara/casa_blanca/lista.csv
"""
import argparse
import csv
import html
import json
import os
import re
import time
import urllib.request

BASE = 'https://obamawhitehouse.archives.gov'
SEMILLA = '/photos-and-video/video/2016/10/17/president-obama-delivers-remarks-education'
UA = {'User-Agent': 'Mozilla/5.0 (LiteraLevel, proyecto academico)'}


def bajar(ruta, cache):
    f = os.path.join(cache, re.sub(r'[^A-Za-z0-9]+', '_', ruta)[-180:] + '.html')
    if os.path.exists(f):
        return open(f, encoding='utf8', errors='replace').read()
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + ruta, headers=UA), timeout=60) as r:
                t = r.read().decode('utf8', 'replace')
            open(f, 'w', encoding='utf8').write(t)
            time.sleep(0.5)
            return t
        except Exception as e:  # noqa: BLE001 — red: reintentar
            print('reintento', ruta, e)
            time.sleep(5 * (intento + 1))
    return ''


def tipo(slug, titulo):
    s = (slug + ' ' + titulo).lower()
    if 'weekly-address' in s or 'weekly address' in s:
        return 'discurso_semanal'
    if 'press-briefing' in s or 'first-lady' in s or 'vice-president' in s:
        return 'otro'
    if re.search(r'president|potus|obama|state-of-the-union|farewell', s) and \
            re.search(r'remarks|speech|address|speaks|statement|conference|delivers|message', s):
        return 'presidente'
    return 'otro'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', required=True)
    a = ap.parse_args()
    cache = os.path.join(os.path.dirname(a.salida), 'cache_html')
    os.makedirs(cache, exist_ok=True)

    slugs = []
    p = 1
    while True:
        t = bajar(f'{SEMILLA}/index__q_page={p}.html', cache)
        nuevos = [s for s in dict.fromkeys(re.findall(r'href="(/photos-and-video/video/20\d\d/[^"/]+/[^"/]+/[^"/]+)"', t))
                  if s != SEMILLA]
        if not nuevos:
            break
        slugs += nuevos
        if p % 50 == 0:
            print('página', p, len(dict.fromkeys(slugs)), 'vídeos')
        p += 1
    slugs = list(dict.fromkeys(slugs))
    print(len(slugs), 'vídeos en', p - 1, 'páginas')

    with open(a.salida, 'w', newline='', encoding='utf8') as f:
        w = csv.writer(f)
        w.writerow(['fecha', 'slug', 'titulo', 'mp4', 'mp3', 'dominio_publico', 'tipo'])
        for i, s in enumerate(slugs):
            t = bajar(s, cache)
            tit = re.search(r'<title>([^<]*)</title>', t)
            tit = html.unescape(tit.group(1)).split('|')[0].strip() if tit else ''
            mp4 = re.findall(r'href="(/videos/[^"]+\.mp4)"', t)
            hd = [m for m in mp4 if 'HD' in m] or mp4
            mp3 = re.findall(r'href="(/videos/[^"]+\.mp3)"', t)
            fecha = '-'.join(s.split('/')[3:6])
            w.writerow([fecha, s, tit, BASE + hd[0] if hd else '', BASE + mp3[0] if mp3 else '',
                        int('Public Domain' in t), tipo(s, tit)])
            if i % 200 == 0:
                print(i, '/', len(slugs))
                f.flush()


if __name__ == '__main__':
    main()
