// Los modelos de Blender existen por duplicado: tools/boca3d_demo/ (la demo y
// las comprobaciones de colision) y front/public/boca3d/ (lo que carga la
// app). Los guiones de Blender escriben los dos; esta prueba garantiza que
// nadie deja uno atrasado, que es lo que paso en 56e0893 (la app cargaba una
// lengua vieja que rozaba los dientes).
//
//   node tools/boca3d_demo/comprobar_modelos.mjs      (sale con 1 si difieren)
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const sha = ruta => createHash('sha256').update(readFileSync(ruta)).digest('hex').slice(0, 12);
let fallos = 0;
for (const nombre of ['lengua.glb', 'cara.glb']) {
  const demo = resolve(RAIZ, 'tools', 'boca3d_demo', nombre);
  const publico = resolve(RAIZ, 'front', 'public', 'boca3d', nombre);
  if (!existsSync(demo) || !existsSync(publico)) {
    console.log(`FALTA ${nombre}: demo ${existsSync(demo)} public ${existsSync(publico)}`);
    fallos++;
    continue;
  }
  const iguales = sha(demo) === sha(publico);
  console.log(`${iguales ? 'OK   ' : 'DIFIEREN'} ${nombre}: demo ${sha(demo)} · public ${sha(publico)}`);
  if (!iguales) fallos++;
}
// Y los labios de cara.glb traen sus shape keys con nombre (extras.targetNames):
// sin ellas el visor no puede fruncir ni estirar por nombre.
const glb = readFileSync(resolve(RAIZ, 'front', 'public', 'boca3d', 'cara.glb'));
const largoJson = glb.readUInt32LE(12);
const doc = JSON.parse(glb.subarray(20, 20 + largoJson).toString('utf8'));
for (const [malla, esperadas] of [['labio_superior', ['fruncir', 'estirar', 'comisura_abajo']], ['labio_inferior', ['fruncir', 'estirar', 'comisura_arriba']],
  ['cabeza_lejana', ['fruncir', 'estirar', 'labio_atras', 'cierre_labios', 'compresion_labios']],
  ['cabeza_cercana', ['fruncir', 'estirar', 'labio_atras', 'cierre_labios', 'compresion_labios']]]) {
  const nodo = doc.nodes.find(x => x.name === malla);
  const m = nodo?.mesh !== undefined ? doc.meshes[nodo.mesh] : doc.meshes.find(x => x.name === malla);
  const nombres = m?.extras?.targetNames ?? [];
  const faltan = esperadas.filter(n => !nombres.includes(n));
  console.log(`${faltan.length ? 'FALTAN' : 'OK   '} ${malla}: shape keys ${JSON.stringify(nombres)}`);
  if (faltan.length) fallos++;
}
for (const [nombre, antes] of [['cara.glb', 1902952], ['lengua.glb', 769224]]) {
  const bytes = readFileSync(resolve(RAIZ, 'front', 'public', 'boca3d', nombre)).length;
  const cumple = bytes <= antes * 1.15;
  console.log(`${cumple ? 'OK   ' : 'EXCESO'} ${nombre}: ${bytes} bytes, limite ${Math.floor(antes * 1.15)}`);
  if (!cumple) fallos++;
}
// D4.4b v4: hidrostato de la lengua en las poses del piloto (misma regla que
// medir_lengua.mjs --exigir): volumen ±10 % y punta ≥ 0,75 de la lámina.
{
  const { execFileSync } = await import('node:child_process');
  try {
    const salida = execFileSync(process.execPath, [resolve(RAIZ, 'tools', 'boca3d_demo', 'medir_lengua.mjs'), '--exigir'], { encoding: 'utf8' });
    console.log('OK    lengua.glb: ' + (salida.trim().split(/\r?\n/).pop() ?? ''));
  } catch (e) {
    console.log('FALLA lengua.glb: hidrostato ' + String(e.stderr ?? e.message).trim().slice(0, 300));
    fallos++;
  }
}
process.exit(fallos ? 1 : 0);
