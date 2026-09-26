"""Graba la boca 3D de Pronunciar recorriendo los sonidos del AFI, con su audio.

Sirve el build local de front, pasa /api al motor publicado, abre la tabla del
AFI, abre «Boca en 3D» y, para cada símbolo, lo toca y pulsa «Escuchar y ver».
Playwright graba el vídeo (sin audio); el audio de cada sonido se baja aparte y
ffmpeg lo coloca donde la página arrancó ese audio (hook de Web Audio).

Uso: python tools/grabar_afi_3d.py SALIDA.mp4 [--solo p,θ,ð] [--antes]   (--antes: GLB originales)
"""
import argparse, functools, http.server, json, os, shutil, socketserver, subprocess, tempfile, threading, time, urllib.request

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(RAIZ, 'front', 'dist', 'front', 'browser')   # antes: npm run build
GLB_ANTES = os.environ.get('GLB_ANTES', '')   # carpeta con original_cara.glb y original_didactica_cara.glb, para --antes
API = 'https://mikemaki1763-literalevel.hf.space'
HOOK = """
window.__inicios = [];
const orig = AudioBufferSourceNode.prototype.start;
AudioBufferSourceNode.prototype.start = function (...a) {
  window.__inicios.push(performance.timeOrigin + performance.now()); return orig.apply(this, a); };
const play = HTMLMediaElement.prototype.play;
HTMLMediaElement.prototype.play = function () {
  window.__inicios.push(performance.timeOrigin + performance.now()); return play.apply(this); };
try { localStorage.setItem('literalevel.bienvenida','vista'); localStorage.setItem('literalevel.tema','noche'); } catch (e) {}
"""


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def send_head(self):
        if not os.path.exists(self.translate_path(self.path)): self.path = '/index.html'
        return super().send_head()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('salida'); ap.add_argument('--solo', default=''); ap.add_argument('--antes', action='store_true'); ap.add_argument('--solo-medir', action='store_true')
    ap.add_argument('--ancho', type=int, default=540); ap.add_argument('--alto', type=int, default=1000)
    a = ap.parse_args()
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 8793), functools.partial(H, directory=DIST))
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    inv = json.load(urllib.request.urlopen(API + '/api/fonemas?acento=ga', timeout=60))
    sonidos = [s for g in inv['grupos'] for s in g['sonidos']]
    if a.solo: sonidos = [s for s in sonidos if s['simbolo'] in a.solo.split(',')]
    tmp = tempfile.mkdtemp(prefix='afi_')
    inicios, tiempos = [], []
    with sync_playwright() as p:
        nav = p.chromium.launch(channel='chrome', headless=True,
                                args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'])
        ctx = nav.new_context(viewport={'width': a.ancho, 'height': a.alto}, device_scale_factor=1,
                              record_video_dir=tmp, record_video_size={'width': a.ancho, 'height': a.alto})
        ctx.add_init_script(HOOK)
        t_video = time.time() * 1000
        pg = ctx.new_page()
        def api(route):
            u = route.request.url
            route.fulfill(response=route.fetch(url=API + u[u.index('/api/'):]))
        pg.route('**/api/**', api)
        if a.antes:
            for n in ('didactica/cara.glb', 'cara.glb'):
                orig = os.path.join(GLB_ANTES, 'original_' + n.replace('/', '_'))
                pg.route('**/boca3d/' + n, (lambda f: (lambda r, *_: r.fulfill(path=f, content_type='model/gltf-binary')))(orig))
        pg.goto('http://127.0.0.1:8793/#/pronunciar', wait_until='networkidle', timeout=120000)
        pg.locator('summary:has-text("Los sonidos del inglés")').click()
        pg.locator('.celda').first.wait_for(timeout=60000)
        pg.locator('.celda').first.click(); pg.wait_for_timeout(800)
        pg.locator('.ficha-sonido button:has-text("Boca en 3D")').click()
        pg.wait_for_function("() => { const c = document.querySelector('app-boca3d canvas'); return !!c; }", timeout=60000)
        # Hasta que la boca se ve de verdad (lienzo con dibujo, no un rectángulo liso).
        from PIL import Image, ImageStat
        import io
        visor = pg.locator('.ficha-sonido app-boca3d .visor')
        visor.scroll_into_view_if_needed()
        lienzo = pg.locator('.ficha-sonido app-boca3d .lienzo')
        t_ab = time.time()
        for intento in range(90):
            img = Image.open(io.BytesIO(lienzo.screenshot())).convert('L')
            if ImageStat.Stat(img).stddev[0] > 25: img.save('visible_%s.png' % ('antes' if a.antes else 'webp')); break
            pg.wait_for_timeout(1000)
        print('boca visible tras', round(time.time()-t_ab,1), 's', flush=True)
        if a.solo_medir: ctx.close(); nav.close(); srv.shutdown(); return
        pg.wait_for_timeout(1500)
        pg.evaluate('window.__inicios = []')
        for s in sonidos:
            celda = pg.locator(f'.celda:has(strong:text-is("/{s["simbolo"]}/"))').first
            celda.evaluate('b => b.click()'); pg.wait_for_timeout(350)
            # La boca justo bajo la cabecera, siempre en el mismo sitio (para recortar el vídeo).
            pg.evaluate("""() => { const v = document.querySelector('.ficha-sonido app-boca3d .visor');
              window.scrollBy(0, v.getBoundingClientRect().top - 72); }""")
            pg.wait_for_timeout(450)
            caja = pg.locator('.ficha-sonido app-boca3d .visor').bounding_box()
            n0 = pg.evaluate('window.__inicios.length')
            pg.locator('.ficha-sonido .botones-corte button:has-text("Escuchar y ver")').click()
            pg.wait_for_function(f'window.__inicios.length > {n0}', timeout=15000)
            tiempos.append((s['simbolo'], pg.evaluate('window.__inicios[window.__inicios.length-1]')))
            pg.wait_for_timeout(2600)
        pg.wait_for_timeout(800)
        video = pg.video.path()
        recorte = (int(caja['width'] * 2), int((caja['height'] + 70) * 2), int(caja['x'] * 2), int(caja['y'] * 2))
        ctx.close(); nav.close()
    srv.shutdown()
    # Audio: cada mp3 en su sitio.
    entradas, filtros = [], []
    for i, (simbolo, t) in enumerate(tiempos):
        s = next(x for x in sonidos if x['simbolo'] == simbolo)
        mp3 = os.path.join(tmp, f'{i:03d}.mp3')
        urllib.request.urlretrieve(API + s['audio'], mp3)
        entradas += ['-i', mp3]
        ms = max(0, int(t - t_video))
        filtros.append(f'[{i + 1}:a]adelay={ms}|{ms}[a{i}]')
    mezcla = ';'.join(filtros) + ';' + ''.join(f'[a{i}]' for i in range(len(tiempos))) + f'amix=inputs={len(tiempos)}:normalize=0[aud]'
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', video, *entradas, '-filter_complex', mezcla,
                    '-map', '0:v', '-map', '[aud]', '-ss', '%.2f' % max(0, (tiempos[0][1] - t_video) / 1000 - 1.5), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23',
                    '-preset', 'veryfast', '-c:a', 'aac', a.salida], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print('listo', a.salida, os.path.getsize(a.salida) // 1024, 'KB,', len(tiempos), 'sonidos')


if __name__ == '__main__':
    main()
