// Empaqueta la demo del visor 3D de la boca (tools/boca3d_demo/demo.ts, que usa
// la escena de front/src/app/compartido/boca3d/) con el esbuild que trae Angular
// y deja un index.html para abrir en el navegador.
//
//   node tools/boca3d_demo.mjs [carpeta_de_salida]      (por defecto, build/boca3d_demo)
//
// Solo lee el front: no toca la app de Angular ni su router.
import { build } from '../front/node_modules/esbuild/lib/main.js';
import { copyFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const salida = resolve(process.argv[2] ?? resolve(RAIZ, 'build', 'boca3d_demo'));
mkdirSync(salida, { recursive: true });

await build({
  entryPoints: [resolve(RAIZ, 'tools/boca3d_demo/demo.ts')],
  bundle: true,
  format: 'iife',
  target: 'es2022',
  outfile: resolve(salida, 'demo.js'),
  nodePaths: [resolve(RAIZ, 'front/node_modules')],
  sourcemap: true,
  logLevel: 'info',
});

writeFileSync(resolve(salida, 'index.html'), `<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Boca 3D · demo</title>
<style>
  :root { color-scheme: light dark; --fondo: #f4f6fb; --texto: #18223a; --borde: #d6deeb; --acento: #2f5bea; }
  @media (prefers-color-scheme: dark) { :root { --fondo: #0f1422; --texto: #e8edf8; --borde: #2f3b58; --acento: #7c9bff; } }
  body { margin: 0; padding: 16px; font: 16px/1.4 'Segoe UI', system-ui, sans-serif; background: var(--fondo); color: var(--texto); }
  #boca3d-demo { max-width: 560px; margin: 0 auto; }
  .chips { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px; }
  .chips button { font: inherit; font-size: .85em; padding: 3px 8px; border-radius: 999px; border: 1px solid var(--borde); background: transparent; color: inherit; cursor: pointer; }
  .chips button.elegido { background: var(--acento); color: #fff; border-color: var(--acento); }
  .visor { width: 100%; aspect-ratio: 4 / 3; border: 1px solid var(--borde); border-radius: 16px; overflow: hidden; }
  .leyenda { min-height: 1.4em; }
  .pista { font-size: .9em; opacity: .75; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
  .pista button { font: inherit; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--borde); background: transparent; color: inherit; }
</style>
<div id="boca3d-demo"></div>
<script src="demo.js"></script>
`);
// La lengua de Blender (tools/boca3d_blender/lengua.py), si se ha generado: ?lengua=glb la carga.
const glb = resolve(RAIZ, 'tools/boca3d_demo/lengua.glb');
if (existsSync(glb)) copyFileSync(glb, resolve(salida, 'lengua.glb'));
const cara = resolve(RAIZ, 'tools/boca3d_demo/cara.glb');
if (existsSync(cara)) copyFileSync(cara, resolve(salida, 'cara.glb'));
console.log('demo en', resolve(salida, 'index.html'), existsSync(glb) ? '(con lengua.glb)' : '(sin lengua.glb)');
