// Mide la demo con Chromium aislado y CPU x4/x1 mediante CDP.
// PLAYWRIGHT_MODULE=... node tools/boca3d_demo/medir_fps.mjs <url> [factor=4] [segundos=4] [ancho=390]
import { pathToFileURL } from 'node:url';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright-core');
const [ruta, factor='4', segundos='4', ancho='390'] = process.argv.slice(2);
if (!ruta) throw new Error('Falta la URL de la demo');
const browser = await chromium.launch({ executablePath: process.env.CHROME ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:true,
  args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--hide-scrollbars'] });
try {
 const contexto=await browser.newContext({viewport:{width:Number(ancho),height:700},deviceScaleFactor:2,isMobile:true});
 const page=await contexto.newPage();
 const cdp=await contexto.newCDPSession(page);
 const valores={};
 for (const rate of [Number(factor),1]) {
  await cdp.send('Emulation.setCPUThrottlingRate',{rate});
  await page.goto(ruta.startsWith('http')||ruta.startsWith('file:')?ruta:pathToFileURL(ruta).href);
  await page.waitForFunction(()=>window.escenaBoca?.tieneCaraModelada&&window.escenaBoca?.tieneLenguaModelada);
  const fps=await page.evaluate(s=>window.medirFps(s),Number(segundos));
  console.log(`cpu x${rate}: ${await page.locator('.leyenda').textContent()}`);
  valores[`cpu_x${rate}`]=Number(fps.toFixed(1));
 }
 console.log(JSON.stringify({ancho:Number(ancho),alto:700,escala:2,segundos:Number(segundos),...valores}));
} finally { await browser.close(); }