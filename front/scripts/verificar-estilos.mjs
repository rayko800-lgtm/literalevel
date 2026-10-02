// La CSP publicada prohíbe scripts inline. La optimización de CSS crítico
// de Angular necesita uno para activar la hoja completa: no debe reaparecer.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync('dist/front/browser/index.html', 'utf8');
const config = JSON.parse(readFileSync('vercel.json', 'utf8'));
const csp = config.headers.flatMap(r => r.headers)
  .find(h => h.key.toLowerCase() === 'content-security-policy')?.value;
assert.match(csp || '', /script-src 'self'(?:;|$)/, 'Mantener scripts limitados al origen propio');
assert.doesNotMatch(html, /<script\b(?![^>]*\bsrc=)[^>]*>/i, 'El build no puede depender de scripts inline');
assert.doesNotMatch(html, /\bon(?:load|error)\s*=/i, 'Sin manejadores inline bloqueados por CSP');
const links = [...html.matchAll(/<link\b[^>]*\brel="?stylesheet"?[^>]*>/gi)].map(m => m[0]);
assert.ok(links.length, 'Debe haber una hoja CSS cargada directamente');
for (const link of links) {
  assert.doesNotMatch(link, /\bmedia="?(?:print|not all)\b/i, 'La hoja no puede esperar activación por JavaScript');
  assert.doesNotMatch(link, /data-beasties/, 'Sin activación diferida por Beasties');
  const href = link.match(/\bhref="([^"]+)"/)?.[1];
  assert.ok(href && /^styles-[\w-]+\.css$/.test(href), 'Hoja global con hash');
  const css = readFileSync(`dist/front/browser/${href}`, 'utf8');
  for (const selector of ['data-tema', 'prefers-color-scheme', '.pagina', '.boton', '.tarjeta']) {
    assert.ok(css.includes(selector), `La hoja completa conserva ${selector}`);
  }
}
console.log('Estilos de producción: carga directa, temas completos y CSP estricta compatibles.');
