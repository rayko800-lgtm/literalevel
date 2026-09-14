// Mide los cuadros por segundo de la demo del visor 3D en Chrome headless con
// la CPU frenada (como un movil), por el protocolo de DevTools y sin instalar
// nada: Node 22+ trae WebSocket.
//
//   node tools/boca3d_demo/medir_fps.mjs <ruta/al/index.html> [factor_cpu=4] [segundos=4] [ancho=390]
//
// Imprime los cuadros por segundo con el factor dado y sin freno, para comparar.
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const [ruta, factor = '4', segundos = '4', ancho = '390'] = process.argv.slice(2);
if (!ruta) { console.error('falta la ruta a index.html'); process.exit(2); }
const CHROME = process.env.CHROME ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PUERTO = 9333;

const chrome = spawn(CHROME, [
  '--headless=new', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--hide-scrollbars',
  `--window-size=${ancho},760`, `--remote-debugging-port=${PUERTO}`, '--no-first-run', 'about:blank',
], { stdio: 'ignore' });

const espera = ms => new Promise(r => setTimeout(r, ms));

async function objetivo() {
  for (let i = 0; i < 50; i++) {
    try {
      const lista = await (await fetch(`http://127.0.0.1:${PUERTO}/json`)).json();
      const p = lista.find(t => t.type === 'page');
      if (p) return p.webSocketDebuggerUrl;
    } catch { /* aun no escucha */ }
    await espera(200);
  }
  throw new Error('Chrome no responde en el puerto de depuracion');
}

class Cdp {
  constructor(ws) { this.ws = ws; this.id = 0; this.pendientes = new Map(); this.eventos = [];
    ws.onmessage = e => {
      const m = JSON.parse(e.data);
      if (m.id && this.pendientes.has(m.id)) { this.pendientes.get(m.id)(m); this.pendientes.delete(m.id); }
      else this.eventos.push(m);
    }; }
  enviar(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((res, rej) => this.pendientes.set(id, m => (m.error ? rej(new Error(m.error.message)) : res(m.result))));
  }
}

async function medir(cdp, url, rate) {
  await cdp.enviar('Emulation.setCPUThrottlingRate', { rate });
  await cdp.enviar('Page.navigate', { url });
  await espera(1500);
  const r = await cdp.enviar('Runtime.evaluate', {
    expression: `window.medirFps(${Number(segundos)})`, awaitPromise: true, returnByValue: true,
  });
  return r.result.value;
}

try {
  const ws = new WebSocket(await objetivo());
  await new Promise(r => (ws.onopen = r));
  const cdp = new Cdp(ws);
  await cdp.enviar('Page.enable');
  await cdp.enviar('Runtime.enable');
  await cdp.enviar('Emulation.setDeviceMetricsOverride', { width: Number(ancho), height: 700, deviceScaleFactor: 2, mobile: true });
  const url = ruta.startsWith('file:') || ruta.startsWith('http') ? ruta : pathToFileURL(ruta).href;
  const conFreno = await medir(cdp, url, Number(factor));
  const sinFreno = await medir(cdp, url, 1);
  console.log(JSON.stringify({ ancho: Number(ancho), escala: 2, segundos: Number(segundos),
    cpu_x1: Number(sinFreno.toFixed(1)), [`cpu_x${factor}`]: Number(conFreno.toFixed(1)) }));
  ws.close();
} finally {
  chrome.kill();
}
