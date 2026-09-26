// Tras `ng build` en Vercel (despliegue desde GitHub): pone en la meta
// `literalevel-api` del index la URL del motor, como hace tools/desplegar_front.py
// al publicar a mano. Sin ella el front pediría /api a su propio dominio (404).
// La URL sale de la variable LITERALEVEL_API del proyecto de Vercel.
import { readFileSync, writeFileSync } from 'node:fs';

const api = (process.env.LITERALEVEL_API || '').trim();
const ruta = 'dist/front/browser/index.html';
if (!/^https:\/\/[a-z0-9.-]+$/.test(api)) {
  console.error('LITERALEVEL_API falta o no es un origen https: no publico un front sin motor.');
  process.exit(1);
}
const html = readFileSync(ruta, 'utf8');
// El build minifica content="" a `content` sin valor: se aceptan las dos formas.
const patron = /<meta name="?literalevel-api"? content(="[^"]*")?>/g;
const encontradas = html.match(patron) || [];
if (encontradas.length !== 1) {
  console.error(`index.html debe tener exactamente una meta literalevel-api (hay ${encontradas.length}).`);
  process.exit(1);
}
writeFileSync(ruta, html.replace(patron, `<meta name="literalevel-api" content="${api}">`));
console.log('meta literalevel-api -> ' + api);
