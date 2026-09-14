// Capturas de la demo del visor 3D a 390 px (móvil) en Chrome headless, para
// enseñar cada paso del acabado: la misma vista antes y después.
//
//   PLAYWRIGHT_MODULE=... node tools/boca3d_demo/capturar.mjs <url_de_la_demo> [carpeta] [sufijo]
//
// Saca la boca en reposo de lado, /u/ de lado, /p/ de frente, /ɑ/ a tres
// cuartos y /θ/ a tres cuartos desde arriba; recorta solo el visor.
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE
  ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright-core');
const [base, carpeta = 'build/boca3d_capturas', sufijo = ''] = process.argv.slice(2);
if (!base) { console.error('falta la URL de la demo (http://127.0.0.1:.../)'); process.exit(2); }
const salida = resolve(carpeta);
await mkdir(salida, { recursive: true });

const VISTAS = [
  ['reposo_lado', 's=&ciclo=0'],
  ['u_lado', 's=u&ciclo=0'],
  ['p_frente', 's=p&ciclo=0&giro=-1.55&polar=1.5'],
  ['a_tres_cuartos', 's=%C9%91&ciclo=0&giro=-0.8&polar=1.35'],
  ['theta_arriba', 's=%CE%B8&ciclo=0&giro=-0.6&polar=1.05'],
];
const browser = await chromium.launch({ executablePath: process.env.CHROME ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
try {
  const contexto = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const page = await contexto.newPage();
  const extra = process.env.EXTRA ? '&' + process.env.EXTRA : '';
  for (const [nombre, q] of VISTAS) {
    await page.goto(`${base}?${q}${extra}`);
    await page.waitForFunction(() => window.escenaBoca?.tieneCaraModelada && window.escenaBoca?.tieneLenguaModelada, null, { timeout: 20000 });
    await page.waitForFunction(() => !window.escenaBoca.enTransicion);
    await page.waitForTimeout(400);
    const ruta = resolve(salida, `${nombre}${sufijo}.png`);
    await page.locator('.visor').screenshot({ path: ruta });
    console.log('OK', ruta);
  }
} finally {
  await browser.close();
}
