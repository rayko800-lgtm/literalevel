// Servidor de la demo, solo loopback y puerto libre. Ctrl+C lo detiene.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';

const raiz = resolve('build/boca3d_demo');
const servidor = createServer(async (req, res) => {
  const ruta = resolve(raiz, '.' + new URL(req.url, 'http://localhost').pathname.replace(/\/$/, '/index.html'));
  if (!ruta.startsWith(raiz + sep)) { res.writeHead(403).end(); return; }
  try {
    const cuerpo = await readFile(ruta);
    const tipos = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.glb': 'model/gltf-binary' };
    res.writeHead(200, { 'Content-Type': tipos[extname(ruta)] ?? 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(cuerpo);
  } catch { res.writeHead(404).end(); }
});
servidor.listen(0, '127.0.0.1', () => {
  console.log(JSON.stringify({ pid: process.pid, url: `http://127.0.0.1:${servidor.address().port}/`, raiz }));
});
