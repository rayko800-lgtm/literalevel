"""Mide en Vercel cuánto tarda la boca 3D didáctica en verse (navegador sin caché), tres veces.

Abre pleyade-app.vercel.app/#/pronunciar en Chrome sin ventana, entra en la tabla del
AFI, toca el primer sonido, pulsa «Boca en 3D» y cronometra hasta que el lienzo deja
de ser un rectángulo liso. Imprime también los bytes del .glb que bajaron.
Resultado del 26 sep 2026 (equipo del autor, móvil emulado a 390 px): 8,9 s la primera vez
(la CDN de Vercel no tenía lengua.glb: x-vercel-cache MISS) y 3,0-3,1 s después; el .glb
principal baja en 1,7 MB (brotli). Uso: python tools/medir_boca3d_vercel.py
"""
import io, time
from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright

URL = 'https://pleyade-app.vercel.app/#/pronunciar'
HOOK = "try { localStorage.setItem('literalevel.bienvenida','vista'); } catch (e) {}"

with sync_playwright() as p:
    nav = p.chromium.launch(channel='chrome', headless=True, args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
    for intento in range(3):
        ctx = nav.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        ctx.add_init_script(HOOK)
        pg = ctx.new_page()
        bajadas = {}
        pg.on('response', lambda r: bajadas.__setitem__(r.url, r) if r.url.endswith('.glb') else None)
        pg.goto(URL, wait_until='networkidle', timeout=120000)
        pg.locator('summary:has-text("Los sonidos del inglés")').click()
        pg.locator('.celda').first.wait_for(timeout=60000)
        pg.locator('.celda').first.click(); pg.wait_for_timeout(600)
        t0 = time.time()
        pg.locator('.ficha-sonido button:has-text("Boca en 3D")').click()
        pg.wait_for_selector('app-boca3d canvas', timeout=60000)
        lienzo = pg.locator('.ficha-sonido app-boca3d .lienzo')
        visto = None
        for _ in range(300):
            try:
                img = Image.open(io.BytesIO(lienzo.screenshot())).convert('L')
                if ImageStat.Stat(img).stddev[0] > 25:
                    visto = time.time() - t0; break
            except Exception:
                pass
            pg.wait_for_timeout(200)
        tam = {}
        for u, r in bajadas.items():
            try:
                tam[u.split('/boca3d/')[-1]] = (len(r.body()), r.headers.get('content-encoding'), r.headers.get('x-vercel-cache'))
            except Exception as e:
                tam[u.split('/boca3d/')[-1]] = str(e)[:60]
        print(f'intento {intento + 1}: boca visible tras {visto:.1f} s' if visto else f'intento {intento + 1}: no se vio en 60 s', tam, flush=True)
        ctx.close()
    nav.close()
