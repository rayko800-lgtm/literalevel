// Comprobaciones que el guion de Codex no cubre: la barra del micrófono no se
// mueve al abrir el 3D ni al hacer scroll; el giro de cámara del ciclo de /u/
// cambia la vista a mitad y la devuelve al final; los .glb servidos son los
// nuevos (sha256 de tools/boca3d_demo). Móvil 390x844 con tacto.
// PLAYWRIGHT_MODULE=ruta/playwright-core/index.mjs FRONT_BUILD=front/dist/front/browser REPO=. node tools/boca3d_demo/probar_boca_extra.mjs
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE).href);
const raiz = resolve(process.env.FRONT_BUILD);
const repo = resolve(process.env.REPO);
const salida = resolve(process.env.SALIDA_PRUEBAS ?? 'pruebas_extra');
await mkdir(salida, { recursive: true });
const pausa = ms => new Promise(r => setTimeout(r, ms));
const sha = b => createHash('sha256').update(b).digest('hex').slice(0, 12);

const servidor = createServer(async (req, res) => {
  const ruta = resolve(raiz, '.' + new URL(req.url, 'http://localhost').pathname.replace(/\/$/, '/index.html'));
  if (!ruta.startsWith(raiz + sep)) { res.writeHead(403).end(); return; }
  try {
    const nombre = extname(ruta) ? ruta : resolve(raiz, 'index.html');
    const cuerpo = await readFile(nombre);
    const tipos = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.glb': 'model/gltf-binary' };
    res.writeHead(200, { 'Content-Type': tipos[extname(nombre)] ?? 'application/octet-stream' }); res.end(cuerpo);
  } catch { res.writeHead(404).end(); }
});
await new Promise(r => servidor.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${servidor.address().port}`;

const ficha = { rasgos: 'x', labios: 'x', lengua: 'x', boca: 'x', cuerdas: 'x', aire: 'x', trampa: '', ga: '', rp: '' };
const fonemas = [
  { simbolo: 'u', nombre: 'Vocal posterior alta', ejemplos: ['food'], grupo: 'vocal', tipo: 'vocal', audio: null, ficha },
  { simbolo: 'i', nombre: 'Vocal anterior alta', ejemplos: ['see'], grupo: 'vocal', tipo: 'vocal', audio: null, ficha },
  { simbolo: 'p', nombre: 'Oclusiva bilabial', ejemplos: ['pen'], grupo: 'oclusiva', tipo: 'consonante', audio: null, ficha },
];
const inventario = acento => ({ acento, acentos: { ga: 'GA', rp: 'RP' }, fonemas,
  grupos: ['vocal', 'oclusiva'].map(clave => ({ clave, titulo: clave, sonidos: fonemas.filter(f => f.grupo === clave) })) });
const inicio = { perfil: null, seguir: null, libros: 0, cuaderno: { consultas: 0, palabras: 0, libros: 0 },
  entrada: { puerta: false, dentro: false, nombre: null, restantes: null, openai: false, mensaje: '' } };

const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const informe = [];
try {
  const contexto = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1,
    isMobile: true, hasTouch: true, colorScheme: 'light' });
  await contexto.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (tipo, ...args) {
      if (String(tipo).includes('webgl')) return original.call(this, tipo, { ...args[0], preserveDrawingBuffer: true });
      return original.call(this, tipo, ...args);
    };
  });
  const glbServidos = {};
  await contexto.route('**/*', async route => {
    const u = new URL(route.request().url());
    if (u.pathname.startsWith('/api/')) {
      let json;
      if (u.pathname === '/api/salud') json = { estado: 'ok', api: 'fixture', cargado: {} };
      else if (u.pathname === '/api/inicio') json = inicio;
      else if (u.pathname === '/api/voz/debiles') json = { palabras: [] };
      else if (u.pathname === '/api/fonemas') json = inventario(u.searchParams.get('acento') ?? 'ga');
      else if (u.pathname.startsWith('/api/articulacion/')) { await route.fulfill({ contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg"/>' }); return; }
      else { await route.fulfill({ status: 404, json: { detail: 'no simulada' } }); return; }
      await route.fulfill({ json }); return;
    }
    if (u.origin !== base) { await route.abort(); return; }
    if (u.pathname.endsWith('.glb')) {
      const cuerpo = await readFile(resolve(raiz, '.' + u.pathname));
      glbServidos[u.pathname] = sha(cuerpo);
    }
    await route.continue();
  });
  const page = await contexto.newPage();
  const errores = [];
  page.on('pageerror', e => errores.push(e.message));
  await page.goto(base + '/#/pronunciar');
  await page.locator('details summary').filter({ hasText: 'Los sonidos' }).click();

  // 1. La barra del micrófono: fija abajo; no se mueve al abrir el 3D ni al hacer scroll.
  const rectBarra = async () => page.locator('.grabadora').boundingBox();
  const barra0 = await rectBarra();
  assert.ok(barra0 && barra0.y + barra0.height <= 844 + 1 && barra0.y > 500, `barra fuera del pulgar: ${JSON.stringify(barra0)}`);
  await page.locator('button.celda').filter({ hasText: 'u' }).first().click();
  await page.getByRole('button', { name: 'Boca en 3D', exact: true }).click();
  const boca = page.locator('app-boca3d'), canvas = boca.locator('canvas');
  await canvas.waitFor();
  await page.waitForFunction(() => {
    const e = document.querySelector('app-boca3d .lienzo');
    return e?.dataset.lengua === 'blender' && e?.dataset.cara === 'blender';
  }, null, { timeout: 15000 });
  await pausa(1500);
  const barra1 = await rectBarra();
  await page.mouse.wheel(0, 300);
  await pausa(400);
  const barra2 = await rectBarra();
  // La barra va pegada abajo: sobre la navegación (48 px) o, si esta se ha
  // escondido al bajar, en el borde. Lo que no puede es quedar en otro sitio
  // ni moverse en horizontal.
  const altoNav = (await page.locator('.nav-movil').boundingBox())?.height ?? 0;
  const pegada = r => Math.abs(r.y + r.height - 844) < 2 || Math.abs(r.y + r.height - (844 - altoNav)) < 2;
  assert.ok(pegada(barra0) && pegada(barra1) && pegada(barra2) && barra1.x === barra0.x && barra2.x === barra0.x
    && barra1.width === barra0.width, `la barra se mueve: ${JSON.stringify([barra0, barra1, barra2])}`);
  informe.push({ barra: { antes: barra0, con3d: barra1, tras_scroll: barra2 } });

  // 2. Los .glb servidos son los nuevos (los de tools/boca3d_demo del commit).
  for (const nombre of ['lengua.glb', 'cara.glb']) {
    const esperado = sha(await readFile(resolve(repo, 'tools', 'boca3d_demo', nombre)));
    assert.equal(glbServidos['/boca3d/' + nombre], esperado, `${nombre} servido no es el del commit`);
  }
  informe.push({ glb: glbServidos });

  // 3. El giro de cámara en el ciclo de /u/: a mitad la vista cambia; al final vuelve.
  await canvas.scrollIntoViewIfNeeded();
  await pausa(600);
  // Píxeles del canvas (preserveDrawingBuffer), no bytes PNG: la compresión
  // hace que dos PNG casi iguales difieran en todo.
  // Muestra el canvas cada 6 píxeles (preserveDrawingBuffer): leer todos los
  // píxeles por CDP tarda segundos y desplaza la medida dentro del ciclo.
  const leer = () => canvas.evaluate(origen => {
    const c = document.createElement('canvas'); c.width = origen.width; c.height = origen.height;
    const ctx = c.getContext('2d'); ctx.drawImage(origen, 0, 0);
    const d = ctx.getImageData(0, 0, c.width, c.height).data, salida = [];
    for (let y = 0; y < c.height; y += 6) for (let x = 0; x < c.width; x += 6) {
      const i = (y * c.width + x) * 4; salida.push(d[i], d[i + 1], d[i + 2]);
    }
    return salida;
  });
  const distintos = (a, b) => {
    let n = 0;
    for (let i = 0; i < a.length; i += 3) if (Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]) > 24) n++;
    return n / (a.length / 3);
  };
  // Al abrir, el visor enseña la pose de /u/ quieta; el ciclo acaba en reposo.
  // Referencia: el reposo de lado al acabar un primer ciclo.
  await canvas.screenshot({ path: resolve(salida, 'u_abierto.png') });
  const reproducir = boca.getByRole('button', { name: /reproducir/i }).first();
  await reproducir.click();
  await pausa(3400);
  const fin1 = await leer();
  await canvas.screenshot({ path: resolve(salida, 'u_fin1.png') });
  await reproducir.click();
  await pausa(1300);
  const mitad = await leer();
  await canvas.screenshot({ path: resolve(salida, 'u_mitad.png') });
  await pausa(2300);
  const fin2 = await leer();
  await canvas.screenshot({ path: resolve(salida, 'u_fin2.png') });
  const dMitad = distintos(fin1, mitad), dFin = distintos(fin1, fin2);
  assert.ok(dMitad > 0.05, `a mitad del ciclo no cambia la vista: ${dMitad}`);
  assert.ok(dFin < 0.01, `al final no vuelve: mitad ${dMitad}, final ${dFin}`);
  informe.push({ giro: { mitad: dMitad, final: dFin } });
  const antes = fin1;

  // 4. Arrastrar con el dedo durante el ciclo cancela el giro y gira a mano.
  await boca.getByRole('button', { name: /reproducir/i }).first().click();
  await pausa(300);
  const b = await canvas.boundingBox();
  const cdp = await contexto.newCDPSession(page);
  const x = b.x + b.width * 0.4, y = b.y + b.height * 0.5;
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
  for (let i = 1; i <= 10; i++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x + i * 10, y }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await pausa(3000);
  const girado = await leer();
  await canvas.screenshot({ path: resolve(salida, 'u_girado_a_mano.png') });
  assert.ok(distintos(antes, girado) > 0.02, 'tras arrastrar, la vista volvió a la de lado: el giro automático pisó al dedo');
  await cdp.detach();

  // 5. «Cerrar 3D» desmonta el visor.
  await page.getByRole('button', { name: 'Cerrar 3D', exact: true }).click();
  await boca.waitFor({ state: 'detached' });
  await page.screenshot({ path: resolve(salida, 'ficha_cerrada.png'), fullPage: false });
  assert.deepEqual(errores, []);
  await writeFile(resolve(salida, 'informe.json'), JSON.stringify(informe, null, 2));
  console.log(JSON.stringify({ ok: true, informe }));
} catch (error) {
  for (const c of browser.contexts()) for (const p of c.pages()) await p.screenshot({ path: resolve(salida, 'fallo.png'), fullPage: true }).catch(() => {});
  console.error(String(error.stack ?? error));
  process.exitCode = 1;
} finally {
  await browser.close();
  await new Promise(r => servidor.close(r));
}
