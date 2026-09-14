// PLAYWRIGHT_MODULE=/ruta/a/playwright-core/index.mjs node tools/boca3d_demo/probar_blender.mjs
// Sirve solo el build local en un puerto libre. No toca navegadores existentes.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE
  ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright-core');
const raiz = resolve('build/boca3d_demo');
const salida = resolve('build/boca3d_pruebas');
await mkdir(salida, { recursive: true });
const servidor = createServer(async (req, res) => {
  const ruta = resolve(raiz, '.' + new URL(req.url, 'http://localhost').pathname.replace(/\/$/, '/index.html'));
  if (!ruta.startsWith(raiz + sep)) { res.writeHead(403).end(); return; }
  try {
    const tipos = { '.html': 'text/html', '.js': 'text/javascript', '.glb': 'model/gltf-binary' };
    const contenido = await readFile(ruta);
    res.writeHead(200, { 'Content-Type': tipos[extname(ruta)] ?? 'application/octet-stream' });
    res.end(contenido);
  } catch { res.writeHead(404).end(); }
});
await new Promise(r => servidor.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${servidor.address().port}/`;
let browser;
const resultados = [];
try {
  browser = await chromium.launch({ executablePath: process.env.CHROME ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  for (const movil of [false, true]) {
    const contexto = await browser.newContext({ viewport: { width: movil ? 390 : 1280, height: movil ? 844 : 900 },
      isMobile: movil, hasTouch: movil, deviceScaleFactor: 1 });
    const page = await contexto.newPage();
    const errores = [];
    page.on('pageerror', e => errores.push(e.message));
    await page.goto(base + '?ciclo=0&s=p');
    await page.waitForFunction(() => window.escenaBoca?.tieneCaraModelada && window.escenaBoca?.tieneLenguaModelada);
    await page.waitForFunction(() => !window.escenaBoca.enTransicion);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'desbordamiento horizontal');
    // Los labios del glb exponen sus shape keys POR NOMBRE en el visor: si el
    // diccionario se pierde al clonar la malla (paso en dffece4..f1b4d0a), el
    // visor cae en escalar el tubo sin decir nada y /u/ no frunce.
    const morfosLabios = await page.evaluate(() => {
      const e = window.escenaBoca;
      return [e.labioSup, e.labioInf].map(m => Object.keys(m.morphTargetDictionary ?? {}));
    });
    for (const [i, claves] of morfosLabios.entries()) {
      for (const clave of ['fruncir', 'estirar', i === 0 ? 'comisura_abajo' : 'comisura_arriba']) {
        assert.ok(claves.includes(clave), `labio ${i === 0 ? 'superior' : 'inferior'} sin la shape key «${clave}» por nombre: ${JSON.stringify(claves)}`);
      }
    }
    const muestras = [];
    for (const [sonido, nombre] of [['p','p'], ['i','i'], ['u','u'], ['theta','theta'], ['h','h'], ['ng','ng']]) {
      const s = ({ theta: '\u03b8', ng: '\u014b' })[sonido] ?? sonido;
      await page.locator(`button[data-s="${s}"]`).click();
      await page.waitForFunction(() => !window.escenaBoca.enTransicion);
      if (sonido === 'u' && await page.evaluate(() => !window.escenaBoca.labioSup.visible)) {
        // Con la cabeza de MakeHuman los labios estan en la piel: la piel del
        // lado lejano y la cercana exponen «fruncir» por nombre y /u/ lo aplica.
        const piel = await page.evaluate(() => {
          const e = window.escenaBoca;
          return e.pielesConLabios.map(m => ({ claves: Object.keys(m.morphTargetDictionary ?? {}), fruncir: m.morphTargetInfluences[m.morphTargetDictionary['fruncir']] }));
        });
        assert.equal(piel.length, 2, `pieles con labios: ${JSON.stringify(piel)}`);
        for (const p of piel) {
          assert.ok(p.claves.includes('fruncir') && p.claves.includes('estirar') && p.claves.includes('labio_atras'), `piel sin shape keys de labios: ${JSON.stringify(p)}`);
          assert.ok(p.fruncir > 0.5, `/u/ no frunce la piel: ${JSON.stringify(p)}`);
        }
      } else if (sonido === 'u') {
        // Y se aplican: en /u/ el labio superior frunce (influencia > 0,5) y no se escala.
        const u = await page.evaluate(() => {
          const m = window.escenaBoca.labioSup;
          return { fruncir: m.morphTargetInfluences[m.morphTargetDictionary['fruncir']], escala: m.scale.toArray() };
        });
        assert.ok(u.fruncir > 0.5, `/u/ no frunce los labios: ${JSON.stringify(u)}`);
        assert.deepEqual(u.escala, [1, 1, 1], `/u/ escala el tubo en vez de fruncir: ${JSON.stringify(u)}`);
      }
      if (sonido === 'theta') {
        const punta = await page.evaluate(() => {
          const e = window.escenaBoca, m = e.lenguaGlb;
          m.updateWorldMatrix(true, false);
          const v = m.position.clone(), vertices = [];
          for (let i = 0; i < m.geometry.attributes.position.count; i++) {
            m.getVertexPosition(i, v).applyMatrix4(m.matrixWorld);
            vertices.push([v.x, v.y, v.z]);
          }
          const frente = Math.min(...vertices.map(v => v[0]));
          const punta = vertices.filter(v => v[0] < frente + 0.10);
          return { x: frente, yMin: Math.min(...punta.map(v => v[1])), yMax: Math.max(...punta.map(v => v[1])) };
        });
        assert.ok(punta.x < -2.72, `punta no sale delante de incisivos: ${JSON.stringify(punta)}`);
        assert.ok(punta.yMin > -0.41 && punta.yMax < 0.45,
          `punta fuera del hueco vertical interdental: ${JSON.stringify(punta)}`);
        console.log('THETA_MUNDO', JSON.stringify(punta));
      }
      for (const [vista, giro] of [['lado', 0], ['frente', -Math.PI/2]]) {
        await page.evaluate(g => window.escenaBoca.vista(g), giro);
        await page.waitForTimeout(250);
        const pixeles = await page.evaluate(() => {
          const e = window.escenaBoca;
          e.renderer.render(e.escena, e.camara);
          const copia = document.createElement('canvas');
          copia.width = e.canvas.width; copia.height = e.canvas.height;
          const c = copia.getContext('2d'); c.drawImage(e.canvas, 0, 0);
          const rgba = c.getImageData(0, 0, copia.width, copia.height).data;
          let visibles = 0, suma = 0, borde = 0;
          for (let i = 0; i < rgba.length; i += 4) {
            if (rgba[i+3] > 10) visibles++;
            const p = i/4, x = p % copia.width, y = Math.floor(p/copia.width);
            if ((x < 2 || y < 2 || x >= copia.width-2 || y >= copia.height-2) && rgba[i+3] > 10) borde++;
            suma += rgba[i] + rgba[i+1] + rgba[i+2];
          }
          return { visibles, suma, borde, total: copia.width*copia.height };
        });
        assert.ok(pixeles.visibles / pixeles.total > 0.025, `${nombre} ${vista}: canvas vacio`);
        assert.equal(pixeles.borde, 0, `${nombre} ${vista}: modelo cortado por el borde`);
        muestras.push({ sonido: nombre, vista, ...pixeles });
        await page.screenshot({ path: resolve(salida, `${movil ? 'movil' : 'desktop'}_${nombre}_${vista}.png`), fullPage: true });
      }
    }
    assert.ok(new Set(muestras.map(m => m.suma)).size >= 8, 'poses sin cambios visibles');
    // La /h/ debe moverse tambien durante el ciclo, no solo cambiar el rotulo.
    await page.locator('.ciclo').check();
    await page.locator('button[data-s="h"]').click();
    const antes = await page.evaluate(() => Array.from(window.escenaBoca.actual));
    const imagenAntes = await page.locator('canvas').screenshot();
    await page.waitForTimeout(650);
    const despues = await page.evaluate(() => Array.from(window.escenaBoca.actual));
    const imagenDespues = await page.locator('canvas').screenshot();
    assert.notDeepEqual(antes, despues, '/h/ sin movimiento');
    assert.ok(despues.at(-1) > 0, '/h/ sin aire');
    assert.equal(imagenAntes.equals(imagenDespues), false, '/h/ no cambia los pixeles');
    assert.deepEqual(errores, []);
    resultados.push({ movil, muestras });
    // Fallo de GLB: sigue el visor sencillo, sin esconder piezas.
    await page.route('**/cara.glb', r => r.abort());
    await page.goto(base + '?cara=glb&ciclo=0');
    await page.waitForFunction(() => !!window.escenaBoca);
    assert.equal(await page.evaluate(() => window.escenaBoca.tieneCaraModelada), false);
    await contexto.close();
  }
  await writeFile(resolve(salida, 'resultados.json'), JSON.stringify(resultados, null, 2));
  console.log(JSON.stringify({ ok: true, viewports: resultados.length, capturas: 24, salida }));
} finally {
  await browser?.close();
  await new Promise(r => servidor.close(r));
}
