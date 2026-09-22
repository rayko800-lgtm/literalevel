// Mide la lengua de un GLB pose a pose, con las mismas influencias que el
// visor (`morfosDe` de escena.ts, copiada de lengua.py): volumen relativo a la
// forma base y grosor de la punta frente al de la lámina, en coordenadas
// locales (antes del giro de la mandíbula). Sirve para comparar dos GLB con
// la MISMA regla y para exigir el hidrostato fuera de Blender.
//
//   node tools/boca3d_demo/medir_lengua.mjs [ruta.glb] [--exigir] [--poses θ,k,...]
//
// --exigir: sale con 1 si alguna pose del piloto se va más de un 10 % de
// volumen o la punta (a 0,2 unidades, ≈4,5 mm, del ápice) queda por debajo de
// 0,75 veces la lámina (a 0,75 unidades): constante de diseño para un extremo
// redondeado, no una cifra publicada.
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const args = process.argv.slice(2);
const ruta = args.find(a => !a.startsWith('--')) ?? resolve(RAIZ, 'front', 'public', 'boca3d', 'lengua.glb');
const exigir = args.includes('--exigir');
const soloPoses = (args.includes('--poses') ? args[args.indexOf('--poses') + 1] ?? '' : '').split(',').filter(Boolean);
const POSES_PILOTO = ['reposo', 'θ', 'ð', 'p', 'b', 'm', 'k', 'ɡ', 'ŋ', 't', 's', 'f', 'n'];
export const TOL_VOLUMEN = 0.10, PUNTA_MIN_RELATIVA = 0.75;

export function leerGlb(buf) {
  const largoJson = buf.readUInt32LE(12);
  const doc = JSON.parse(buf.subarray(20, 20 + largoJson).toString('utf8'));
  const bin = buf.subarray(20 + largoJson + 8);
  const accessor = i => {
    const a = doc.accessors[i], bv = doc.bufferViews[a.bufferView];
    const inicio = (bv.byteOffset ?? 0) + (a.byteOffset ?? 0);
    const n = a.count * { SCALAR: 1, VEC3: 3 }[a.type];
    if (a.componentType === 5126) return new Float32Array(bin.buffer, bin.byteOffset + inicio, n);
    if (a.componentType === 5123) return new Uint16Array(bin.buffer, bin.byteOffset + inicio, n);
    if (a.componentType === 5125) return new Uint32Array(bin.buffer, bin.byteOffset + inicio, n);
    throw new Error(`componente ${a.componentType} no previsto`);
  };
  const malla = doc.meshes.find(m => m.extras?.targetNames?.includes('punta_interdental'));
  const prim = malla.primitives[0];
  return {
    nombres: malla.extras.targetNames,
    base: Array.from(accessor(prim.attributes.POSITION)),
    deltas: prim.targets.map(t => Array.from(accessor(t.POSITION))),
    indices: Array.from(accessor(prim.indices)),
  };
}

// La misma regla que `morfosDe` (escena.ts) y `morfos_de` (lengua.py).
export function morfosDe(p) {
  const [alt, ade] = p.cuerpo;
  const punta = p.punta;
  return [
    0.3 * Math.min(1, Math.max(0, p.mandibula)),
    // Cierre de cara: postalveolar con toque 0,85 (era 1); mismo valor en lengua.py y escena.ts.
    ['alveolar', 'postalveolar'].includes(punta) ? (p.punta_toca ? (p.punta === 'alveolar' ? 1 : 0.85) : 0.75) : punta === 'dental' ? 0.45 : 0,
    punta === 'retrofleja' ? 1 : 0,
    punta === 'interdental' ? 1 : 0,
    Math.max(0, (alt - 0.45) / 0.55),
    Math.max(0, (0.45 - alt) / 0.45),
    Math.max(0, (ade - 0.5) / 0.5),
    Math.max(0, (0.5 - ade) / 0.5),
    // Cierre de cara: sin toque el dorso sube un 10 % menos (/w/); mismo factor en lengua.py y escena.ts.
    p.dorso_velo ? 1 : 0.9 * Math.min(1, p.dorso_alto),
    Math.min(1, Math.max(0, p.raiz)),
  ];
}
const ORDEN = ['mandibula', 'punta_arriba', 'punta_atras', 'punta_interdental', 'cuerpo_alto', 'cuerpo_bajo', 'cuerpo_delante', 'cuerpo_atras', 'dorso_velo', 'raiz_atras'];

function volumen(P, idx) {
  let v = 0;
  for (let t = 0; t < idx.length; t += 3) {
    const a = 3 * idx[t], b = 3 * idx[t + 1], c = 3 * idx[t + 2];
    v += (P[a] * (P[b + 1] * P[c + 2] - P[b + 2] * P[c + 1]) - P[a + 1] * (P[b] * P[c + 2] - P[b + 2] * P[c])
        + P[a + 2] * (P[b] * P[c + 1] - P[b + 1] * P[c])) / 6;
  }
  return Math.abs(v);
}
// glTF Y arriba: x, y = altura, z = lateral. Grosor vertical de la línea media en [x0, x0 + 0,2].
function grosorEn(P, x0) {
  let lo = Infinity, hi = -Infinity;
  for (let i = 0; i < P.length; i += 3) {
    if (P[i] >= x0 && P[i] <= x0 + 0.2 && Math.abs(P[i + 2]) < 0.15) { lo = Math.min(lo, P[i + 1]); hi = Math.max(hi, P[i + 1]); }
  }
  return hi > lo ? hi - lo : 0;
}

export function medir(glb, catalogo, poses = POSES_PILOTO) {
  const { nombres, base, deltas, indices } = glb;
  const orden = ORDEN.map(n => nombres.indexOf(n));
  const v0 = volumen(base, indices);
  const todas = { reposo: catalogo.reposo, ...catalogo.sonidos, ...Object.fromEntries(Object.entries(catalogo.rp).map(([k, v]) => ['rp:' + k, v])) };
  const salida = {};
  for (const nombre of poses) {
    const pose = todas[nombre];
    if (!pose) continue;
    const inf = morfosDe(pose);
    const P = base.slice();
    inf.forEach((w, k) => { if (w) { const d = deltas[orden[k]]; for (let i = 0; i < P.length; i++) P[i] += w * d[i]; } });
    let frente = Infinity;
    for (let i = 0; i < P.length; i += 3) frente = Math.min(frente, P[i]);
    const punta = grosorEn(P, frente + 0.2), lamina = grosorEn(P, frente + 0.75);
    salida[nombre] = { volumen: +(volumen(P, indices) / v0 - 1).toFixed(4), punta: +punta.toFixed(3), lamina: +lamina.toFixed(3),
      punta_relativa: lamina > 0 ? +(punta / lamina).toFixed(3) : null, frente: +frente.toFixed(3) };
  }
  return { volumen_base: +v0.toFixed(4), vertices: base.length / 3, poses: salida };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const catalogo = JSON.parse(readFileSync(resolve(RAIZ, 'front', 'src', 'app', 'compartido', 'boca3d', 'poses.ejemplo.json'), 'utf8'));
  const r = medir(leerGlb(readFileSync(ruta)), catalogo, soloPoses.length ? soloPoses : POSES_PILOTO);
  console.log(JSON.stringify(r));
  if (exigir) {
    const malas = Object.entries(r.poses).filter(([, m]) => Math.abs(m.volumen) > TOL_VOLUMEN || (m.punta_relativa ?? 1) < PUNTA_MIN_RELATIVA);
    if (malas.length) { console.error('HIDROSTATO: fuera de tolerancia', malas.map(([n, m]) => `${n} vol ${m.volumen} punta/lamina ${m.punta_relativa}`).join('; ')); process.exit(1); }
    console.log(`HIDROSTATO_OK ${Object.keys(r.poses).length} poses: volumen ±${TOL_VOLUMEN * 100} %, punta ≥ ${PUNTA_MIN_RELATIVA} lamina`);
  }
}
