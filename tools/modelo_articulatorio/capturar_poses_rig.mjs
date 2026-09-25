// Fotografía de frente cada pose del rig (la demo del visor 3D, sin tocar la
// app) para medirla después con el mismo `medir_video.py` que las caras reales:
// es la mitad del paso «medida humana → control del rig».
//
//   PLAYWRIGHT_MODULE=.../playwright-core/index.mjs \
//   node capturar_poses_rig.mjs <carpeta_demo> <carpeta_salida> [extra_query] [símbolos...]
//
// La demo se empaqueta antes con `node tools/boca3d_demo.mjs <carpeta_demo>`.
import { createServer } from 'node:http';
import { mkdir, readFile } from 'node:fs/promises';
import { extname, resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE).href);
const [demo, salida, extra = '', ...simbolos] = process.argv.slice(2);
const raiz = resolve(demo);
await mkdir(resolve(salida), { recursive: true });

const servidor = createServer(async (req, res) => {
  const ruta = resolve(raiz, '.' + new URL(req.url, 'http://localhost').pathname.replace(/\/$/, '/index.html'));
  if (!ruta.startsWith(raiz + sep)) { res.writeHead(403).end(); return; }
  try {
    const tipos = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.glb': 'model/gltf-binary' };
    const cuerpo = await readFile(ruta);
    res.writeHead(200, { 'Content-Type': tipos[extname(ruta)] ?? 'application/octet-stream' }).end(cuerpo);
  } catch { res.writeHead(404).end(); }
});
await new Promise(r => servidor.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${servidor.address().port}/`;

const browser = await chromium.launch({ executablePath: process.env.CHROME ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
try {
  const page = await (await browser.newContext({ viewport: { width: 600, height: 700 } })).newPage();
  let lista = simbolos;
  if (!lista.length) {
    await page.goto(`${base}?ciclo=0`);
    await page.waitForFunction(() => window.escenaBoca?.tieneCaraModelada, null, { timeout: 30000 });
    lista = await page.evaluate(() => [...document.querySelectorAll('select option')].map(o => o.value).filter(Boolean));
  }
  for (const s of ['', ...lista]) {
    await page.goto(`${base}?s=${encodeURIComponent(s)}&ciclo=0&giro=-1.5708&polar=1.5708${extra ? '&' + extra : ''}`);
    await page.waitForFunction(() => window.escenaBoca?.tieneCaraModelada && window.escenaBoca?.tieneLenguaModelada, null, { timeout: 30000 });
    await page.waitForFunction(() => !window.escenaBoca.enTransicion);
    await page.waitForTimeout(500);
    const nombre = s ? [...s].map(c => c.codePointAt(0).toString(16)).join('_') : 'reposo';
    await page.locator('.visor').screenshot({ path: resolve(salida, `${nombre}.png`) });
    console.log(s || 'reposo', nombre);
  }
} finally {
  await browser.close();
  servidor.close();
}
