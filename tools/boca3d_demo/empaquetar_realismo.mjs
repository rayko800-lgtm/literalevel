// Entrega explícita del piloto: no recorre el repo ni incluye referencias privadas.
// node tools/boca3d_demo/empaquetar_realismo.mjs <carpeta-nueva> <blender.exe>
// PYTHON puede indicar un intérprete Python 3 para comprimir el paquete.
import { build } from '../../front/node_modules/esbuild/lib/main.js';
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const [destino, blender]=process.argv.slice(2);
if(!destino || !blender)throw new Error('Indica una carpeta nueva de entrega y Blender');
const out=resolve(destino), visor=join(out,'visor'), proyectos=join(out,'Blender');
if(existsSync(out))throw new Error('La carpeta ya existe; conserva el respaldo y elige otra');
const commit=execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
mkdirSync(visor,{recursive:true});mkdirSync(proyectos);
for(const [src,name] of [['build/boca_didactica/cara.glb','cara.glb'],['build/lengua_realista/lengua.glb','lengua.glb']])
  copyFileSync(join(root,src),join(visor,name));
await build({entryPoints:[join(root,'tools/boca3d_demo/demo.ts')],bundle:true,minify:true,format:'iife',target:'es2022',outfile:join(visor,'demo.js'),nodePaths:[join(root,'front/node_modules')]});
const inicio="<script>if(!location.search)location.replace(location.pathname+'?didactica=1&inventario=1&s=i&ciclo=0&sombras=0&vista=frente&velocidad=0.5');</script>";
writeFileSync(join(visor,'index.html'),readFileSync(join(root,'tools/boca3d_demo/visor_realismo.html'),'utf8').replace('<script src="demo.js">',inicio+'<script src="demo.js">'));
copyFileSync(join(root,'tools/boca3d_blender/lps/LeePerrySmith_License.txt'),join(visor,'credits.txt'));
copyFileSync(join(root,'tools/boca3d_blender/texturas/README.md'),join(out,'ORIGEN_TEXTURA.md'));
if(process.env.INFORME_PILOTO)copyFileSync(resolve(process.env.INFORME_PILOTO),join(out,'INFORME.md'));
if(process.env.CAPTURAS_PILOTO){
  const evidencia=join(out,'Comparacion');mkdirSync(evidencia);
  const capturas=['i-antes.png','i-despues.png','ae-despues.png','u-despues.png','f-despues.png','p-despues.png'];
  const incluidas=[];
  for(const name of capturas){const p=resolve(process.env.CAPTURAS_PILOTO,name);if(existsSync(p)){copyFileSync(p,join(evidencia,name));incluidas.push(name);}}
  writeFileSync(join(evidencia,'index.html'),`<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Comparación del piloto</title><style>body{background:#101b2c;color:#ecf4fa;font:16px system-ui;margin:24px}main{max-width:1040px;margin:auto}.grid{display:flex;flex-wrap:wrap;gap:24px}figure{margin:0;width:310px;max-width:100%}img{width:100%;height:auto}figcaption{padding:10px 0}</style><main><h1>Revisión del modelo</h1><p>Capturas reales del visor. La comparación de /i/ conserva cámara e iluminación. El informe incluido detalla los cambios de forma o material de esta entrega. El resto muestra el candidato.</p><div class="grid">${incluidas.map(name=>`<figure><figcaption>${name.replace('.png','').replaceAll('-',' · ')}</figcaption><img src="${name}" alt="${name}"></figure>`).join('')}</div></main></html>`);
}
for(const [src,name] of [['build/boca_didactica/cara.blend','cara.blend'],['build/lengua_realista/lengua.blend','lengua.blend']]){
  execFileSync(blender,['-b','--python',join(root,'tools/boca3d_blender/empacar_blend.py'),'--',join(root,src),join(proyectos,name)],{stdio:['ignore','pipe','pipe']});
}
writeFileSync(join(out,'LEEME.md'),`# Boca3D: piloto de realismo\n\nFuentes: https://github.com/rayko800-lgtm/literalevel/tree/${commit}\n\nAbre los proyectos de Blender incluidos para editar las mallas y sus gestos. Las texturas van incorporadas. El tono de piel, detalle labial, luz y movimiento finales se aplican en el visor Three.js; no están horneados íntegramente en el material de Blender.\n\nPara ver el piloto, abre una terminal dentro de la carpeta visor y ejecuta:\n\n    python -m http.server 8790 --bind 127.0.0.1\n\nDespués abre http://127.0.0.1:8790/ en un navegador. Detén el servidor con Ctrl+C. Se requiere WebGL2 y Python3. El piloto no incluye audio.\n\nEs un modelo educativo en revisión, no anatomía clínica ni fotorrealismo terminado. Incluye únicamente recursos de la entrega; no contiene video ni fotogramas privados. Consulta visor/credits.txt y ORIGEN_TEXTURA.md.\n`);
const archivos=[];
function inventariar(dir){for(const name of readdirSync(dir)){const p=join(dir,name);if(statSync(p).isDirectory())inventariar(p);else archivos.push({ruta:p.slice(out.length+1).replaceAll('\\','/'),bytes:statSync(p).size,sha256:createHash('sha256').update(readFileSync(p)).digest('hex')});}}
inventariar(out);
writeFileSync(join(out,'MANIFIESTO.json'),JSON.stringify({commit,creado:new Date().toISOString(),archivos},null,2));
const zip=out+'.zip';
execFileSync(process.env.PYTHON||'python',['-c',"import sys,zipfile,pathlib; root=pathlib.Path(sys.argv[1]); z=zipfile.ZipFile(sys.argv[2],'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6); [z.write(p,p.relative_to(root)) for p in sorted(root.rglob('*')) if p.is_file()]; z.close()",out,zip],{stdio:'pipe'});
console.log(JSON.stringify({commit,carpeta:out,zip,bytes:statSync(zip).size,sha256:createHash('sha256').update(readFileSync(zip)).digest('hex')}));
