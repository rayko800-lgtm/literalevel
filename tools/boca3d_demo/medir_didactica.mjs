// Inspección geométrica del piloto con el método aplicar() REAL del visor.
// No necesita navegador, WebGL ni texturas. No valida por sí sola la anatomía.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { build } from '../../front/node_modules/esbuild/lib/main.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const out = resolve(root, 'build/boca_didactica');
mkdirSync(out, { recursive: true });
await build({ stdin: { contents: `export * from './front/src/app/compartido/boca3d/escena';
export * from './front/src/app/compartido/boca3d/poses';
export * from './front/src/app/compartido/boca3d/animacion';
export { mergeGeometries, mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import * as THREE from 'three'; export { THREE };`, resolveDir: root },
  bundle: true, platform: 'node', format: 'esm', nodePaths: [resolve(root, 'front/node_modules')],
  outfile: resolve(out, 'medidor-runtime.mjs'), logLevel: 'silent' });
const { THREE: T, EscenaBoca, poseNumerica, pielQueSigueLaMandibula, conAjustes3d, cicloSonido, mergeGeometries, mergeVertices, seccionSagitalLengua, actualizarSeccionSagital, MORFOS_LENGUA } = await import(pathToFileURL(resolve(out, 'medidor-runtime.mjs')));
const path = resolve(process.argv[2] ?? resolve(out, 'cara.glb'));
const buf = readFileSync(path), len = buf.readUInt32LE(12);
const doc = JSON.parse(buf.subarray(20, 20 + len));
const bin = buf.subarray(28 + len);
function accessor(i, gltf=doc, data=bin) {
  const a = gltf.accessors[i], v = gltf.bufferViews[a.bufferView];
  const n = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 }[a.type];
  const bytes = { 5126: 4, 5125: 4, 5123: 2, 5121: 1 }[a.componentType];
  const read = { 5126: 'readFloatLE', 5125: 'readUInt32LE', 5123: 'readUInt16LE', 5121: 'readUInt8' }[a.componentType];
  return Array.from({ length: a.count * n }, (_, j) => data[read]((v.byteOffset ?? 0) + (a.byteOffset ?? 0) + Math.floor(j / n) * (v.byteStride ?? n * bytes) + (j % n) * bytes));
}
const nodes = doc.nodes.map(n => {
  const o = new T.Object3D();
  if (n.matrix) { o.matrix.fromArray(n.matrix); o.matrix.decompose(o.position, o.quaternion, o.scale); }
  else { if (n.translation) o.position.fromArray(n.translation); if (n.rotation) o.quaternion.fromArray(n.rotation); if (n.scale) o.scale.fromArray(n.scale); }
  return o;
});
doc.nodes.forEach((n, i) => n.children?.forEach(j => nodes[i].add(nodes[j])));
nodes.filter(o => !o.parent).forEach(o => o.updateMatrixWorld(true));
function mesh(name) {
  const i = doc.nodes.findIndex(n => n.name === name), m = doc.meshes[doc.nodes[i].mesh], p = m.primitives[0];
  const g = new T.BufferGeometry();
  if(p.attributes.TEXCOORD_1!==undefined)g.setAttribute('uv1',new T.Float32BufferAttribute(accessor(p.attributes.TEXCOORD_1),2));
  g.setAttribute('position', new T.Float32BufferAttribute(accessor(p.attributes.POSITION), 3));
  g.setIndex(accessor(p.indices));
  g.morphTargetsRelative = true;
  if (p.targets) g.morphAttributes.position = p.targets.map(t => new T.Float32BufferAttribute(accessor(t.POSITION), 3));
  g.applyMatrix4(nodes[i].matrixWorld); g.computeVertexNormals();
  const o = new T.Mesh(g); o.name = name;
  if (p.targets) o.morphTargetDictionary = Object.fromEntries(m.extras.targetNames.map((n, j) => [n, j]));
  return o;
}
const halves = ['exterior_cercana', 'exterior_lejana'].map(mesh);
halves.forEach(m => m.geometry.deleteAttribute('normal'));
const joined = mergeGeometries(halves.map(m => m.geometry));
joined.morphTargetsRelative = halves[0].geometry.morphTargetsRelative;
const combined = mergeVertices(joined, 1e-5);
combined.computeVertexNormals();
const exterior = new T.Mesh(combined); exterior.morphTargetDictionary = { ...halves[0].morphTargetDictionary };
const skin = [exterior];
const sections = ['anatomia_labio_sup','anatomia_labio_inf'].filter(name => doc.nodes.some(n => n.name === name)).map(mesh);
const animatedSkin = [...skin, ...sections];
const upper = Array.from({ length: 4 }, (_, i) => mesh('diente_sup_' + String(i + 4).padStart(2, '0')));
const teeth = ['sup', 'inf'].flatMap(a => Array.from({ length: 12 }, (_, i) => mesh(`diente_${a}_${String(i).padStart(2, '0')}`)));
const dummy = () => new T.Mesh(new T.BufferGeometry(), new T.MeshStandardMaterial());
const scene = Object.create(EscenaBoca.prototype);
Object.assign(scene, { mandibula: new T.Group(), velo: new T.Group(), aireNasal: dummy(), aireOral: dummy(), marcaContacto: dummy(), marcaVibracion: dummy(),
  labioSup: dummy(), labioInf: dummy(), pielesConLabios: animatedSkin, pielesDeformables: animatedSkin.map(m => pielQueSigueLaMandibula(m.geometry, true, true, true)),
  lenguaGlb: { morphTargetInfluences: [] }, indicesMorfos: [], labio() {} });
const bases = skin.map(m => Array.from({ length: m.geometry.attributes.position.count }, (_, i) => new T.Vector3().fromBufferAttribute(m.geometry.attributes.position, i)));
const seams = sections.flatMap(m => {
  const p=m.geometry.attributes.position;
  return Array.from({length:p.count},(_,i) => {
    const v=new T.Vector3().fromBufferAttribute(p,i);
    const j=bases[0].findIndex(q => q.distanceTo(v)<1e-5);
    return {m,i,j};
  }).filter(a => a.j>=0);
});
let seamError=0;
// Las dos inserciones posteriores deben quedarse con el maxilar/mentón.
// Se identifican por su reposo también en el modelo anterior (control positivo).
const raices=sections.flatMap(m=>{
  const p=m.geometry.getAttribute('position');
  const inferior=m.name.endsWith('_inf');
  const anclas=inferior?[[-2.63,-.50],[-2.72,-.12]]:[[-2.66,.82],[-2.73,.46]];
  return Array.from({length:p.count},(_,i)=>({m,i,inferior,base:new T.Vector3().fromBufferAttribute(p,i)}))
    .filter(r=>anclas.some(([x,y])=>Math.hypot(r.base.x-x,r.base.y-y)<1e-5));
});
let rootError=0, rootWorst=null;
let upperLipFold=0, upperLipFoldWorst=null;
const lenguaArgumento=process.argv.find(v=>v.startsWith('--lengua='))?.slice('--lengua='.length);
const tb=readFileSync(lenguaArgumento ? resolve(lenguaArgumento) : resolve(root,'tools/boca3d_demo/lengua.glb')),tl=tb.readUInt32LE(12);
const td=JSON.parse(tb.subarray(20,20+tl)),tbin=tb.subarray(28+tl),tm=td.meshes[0],tp=tm.primitives[0];
const tg=new T.BufferGeometry();tg.morphTargetsRelative=true;
tg.setAttribute('position',new T.Float32BufferAttribute(accessor(tp.attributes.POSITION,td,tbin),3));
tg.setIndex(accessor(tp.indices,td,tbin));
tg.morphAttributes.position=tp.targets.map(t => new T.Float32BufferAttribute(accessor(t.POSITION,td,tbin),3));
const tongue=new T.Mesh(tg);tongue.morphTargetDictionary=Object.fromEntries(tm.extras.targetNames.map((n,i) => [n,i]));
scene.lenguaGlb=tongue;scene.indicesMorfos=MORFOS_LENGUA.map(n => tongue.morphTargetDictionary[n]);
const tongueSection=seccionSagitalLengua(tongue);
if(!tongueSection) throw new Error('No se pudo construir la sección lingual');
scene.seccionLingual=tongueSection;
let sectionStatesOverTolerance=0;
const sectionAreaTolerance=.001; // área en unidades del modelo, no tolerancia clínica
let sectionAreaError=0;
let sectionWorst=null;
const catalog = conAjustes3d(JSON.parse(readFileSync(resolve(root, 'front/src/app/compartido/boca3d/poses.ejemplo.json'))), JSON.parse(readFileSync(resolve(root, 'front/src/app/compartido/boca3d/poses.ajustes3d.json'))));
const results = [];
const triangles = upper.map(m => {
  const g = m.geometry, ids = g.index.array;
  return Array.from({ length: ids.length / 3 }, (_, i) => new T.Triangle(...[0, 1, 2].map(j => new T.Vector3().fromBufferAttribute(g.attributes.position, ids[3 * i + j]))));
});
const full = process.argv.includes('--completo');
const selected = full ? { ...catalog.sonidos, ...Object.fromEntries(Object.entries(catalog.rp ?? {}).map(([s,p]) => ['rp/'+s,p])) } : Object.fromEntries(['p','b','m','v','f','i','u','ɑ','k','θ'].map(s => [s,catalog.sonidos[s]]));
const cases = Object.entries({ reposo: catalog.reposo, ...selected }).map(([symbol, pose]) => ({ symbol, n: poseNumerica(pose) }));
for (const s of (full ? Object.keys(selected) : ['p','b','f','v','i'])) {
  const line = cicloSonido(selected[s], catalog);
  scene.linea = { total: line.total, claves: line.claves.map(c => {
    const n = poseNumerica(c.pose);
    if (c.hacia) { const to = poseNumerica(c.hacia); n.forEach((v, i) => n[i] = v + (to[i]-v)*(c.f ?? .5)); }
    return { t: c.t, n };
  }) };
  for (let i=0;i<=40;i++) cases.push({ symbol: `${s}@${i}/40`, n: scene.poseDeLinea(line.total*i/40) });
}
for (const {symbol, n} of cases) {
  scene.aplicar(n);
  for(const r of raices){
    const expected=r.base.clone();
    if(r.inferior) expected.sub(new T.Vector3(2.6,.9,0))
      .applyAxisAngle(new T.Vector3(0,0,1),scene.mandibula.rotation.z).add(new T.Vector3(2.6,.9,0));
    const error=r.m.getVertexPosition(r.i,new T.Vector3()).distanceTo(expected);
    if(error>rootError){rootError=error;rootWorst=symbol;}
  }
  for (const {m,i,j} of seams) seamError=Math.max(seamError,
    m.getVertexPosition(i,new T.Vector3()).distanceTo(exterior.getVertexPosition(j,new T.Vector3())));
  let inverted=false;
  for(const m of [tongueSection,...tongueSection.children]) {
    const ps=Array.from({length:m.geometry.attributes.position.count},(_,i) => m.getVertexPosition(i,new T.Vector3()));
    if(process.argv.includes('--debug-seccion') && symbol==='k') console.log('SECCION_K',m===tongueSection?'lengua':'apoyo',JSON.stringify(ps.map(p=>[p.x,p.y])));
    if(ps.some(p => !p.toArray().every(Number.isFinite))) throw new Error('Sección no finita: '+symbol);
    const ids=m.geometry.index.array;
    let area=0,polygon=0;
    ps.forEach((p,i) => {const q=ps[(i+1)%ps.length];polygon+=p.x*q.y-p.y*q.x;});
    for(let i=0;i<m.geometry.drawRange.count;i+=3) {
      const [a,b,c]=[ps[ids[i]],ps[ids[i+1]],ps[ids[i+2]]];
      area+=Math.abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x));
    }
    const error=Math.abs(area-Math.abs(polygon))/2;
    if(error>sectionAreaError) sectionWorst={symbol,mesh:m===tongueSection?'lengua':'apoyo'};
    sectionAreaError=Math.max(sectionAreaError,error);
    if(error>sectionAreaTolerance) inverted=true;
  }
  if(inverted) sectionStatesOverTolerance++;
  const points = skin.map(m => bases[skin.indexOf(m)].map((_, i) => m.getVertexPosition(i, new T.Vector3())));
  // Regresión de la captura /æ/: el bermellón no debe pasar por encima
  // del filtrum y volver hacia abajo antes de alcanzar la nariz.
  if (['æ','ɛ','ɑ','i','u'].some(s => symbol===s || symbol.startsWith(s+'@'))) {
    const medial=bases[0].map((p,i)=>({base:p,p:points[0][i]}))
      .filter(v=>Math.abs(v.base.z)<1e-5 && v.base.x<-2.4 && v.base.y>.2 && v.base.y<1.14)
      .sort((a,b)=>a.base.y-b.base.y);
    for(let j=1;j<medial.length;j++) {
      const fold=medial[j-1].p.y-medial[j].p.y;
      if(fold>upperLipFold){upperLipFold=fold;upperLipFoldWorst=symbol;}
    }
  }
  if (points.flat().some(p => !p.toArray().every(Number.isFinite))) throw new Error(`Vertices no finitos en ${symbol}`);
  const gaps = [], lip = [], rim = [];
  bases.forEach((base, mi) => {
    base.forEach((p, i) => {
      if (Math.abs(p.x - (-3.13 + .46*p.z*p.z)) < .002 && Math.abs(p.y-.15) < .014) rim.push(points[mi][i]);
      if (Math.abs(p.z) > .80) return;
      if (Math.abs(p.x - (-3.13 + .46 * p.z * p.z)) < .002 && p.y > .15 && p.y < .165) {
        const j = base.findIndex(q => Math.abs(q.x - p.x) < 1e-5 && Math.abs(q.z - p.z) < 1e-5 && Math.abs(q.y + p.y - .3) < 1e-5);
        if (j >= 0) gaps.push({ lateral: p.z, gap: points[mi][i].y - points[mi][j].y, dx: points[mi][i].x - points[mi][j].x });
      }
      if (p.x < -2.5 && p.y < .15 && p.y > -.05) lip.push(points[mi][i]);
    });
  });
  const contacts = triangles.map((ts, k) => {
    let nearest = Infinity, point, target;
    for (const p of lip) for (const t of ts) {
      const q = t.closestPointToPoint(p, new T.Vector3()), d = p.distanceTo(q);
      if (d < nearest) { nearest = d; point = p.toArray(); target = q.toArray(); }
    }
    return { tooth: upper[k].name, distance: nearest, lip: point, toothPoint: target };
  });
  // Coronas convexas del generador: semiespacios orientados desde su centro.
  // Comprueba vértices de ambos labios contra 24 dientes, no intersecciones
  // arbitrarias entre triángulos. Reportamos esa limitación explícitamente.
  let penetration = 0, penetrationTooth = null, insideVertices = 0;
  for (const tooth of teeth) {
    const pos = tooth.geometry.attributes.position, ids = tooth.geometry.index.array;
    const vs = Array.from({ length: pos.count }, (_, i) => {
      const p = new T.Vector3().fromBufferAttribute(pos, i);
      if (tooth.name.includes('_inf_')) {
        p.sub(new T.Vector3(2.6,.9,0)).applyAxisAngle(new T.Vector3(0,0,1), scene.mandibula.rotation.z).add(new T.Vector3(2.6,.9,0));
      }
      return p;
    });
    const box = new T.Box3().setFromPoints(vs), center = box.getCenter(new T.Vector3());
    const planes = Array.from({ length: ids.length / 3 }, (_, i) => {
      const plane = new T.Plane().setFromCoplanarPoints(...[0,1,2].map(j => vs[ids[3*i+j]]));
      if (plane.distanceToPoint(center) > 0) plane.negate();
      return plane;
    });
    for (const group of points) for (const p of group) {
      if (!box.containsPoint(p)) continue;
      const depth = -Math.max(...planes.map(plane => plane.distanceToPoint(p)));
      if (depth > 1e-5) insideVertices++;
      if (depth > penetration) { penetration = depth; penetrationTooth = tooth.name; }
    }
  }
  const size = new T.Box3().setFromPoints(rim).getSize(new T.Vector3());
  results.push({ symbol, jaw: n[0]/.21, aperture: {width:size.z, height:size.y}, influences: Object.fromEntries(Object.entries(skin[0].morphTargetDictionary).map(([k, i]) => [k, skin[0].morphTargetInfluences[i]])), gaps: { count: gaps.length, min: Math.min(...gaps.map(g => g.gap)), max: Math.max(...gaps.map(g => g.gap)), depthMax: Math.max(...gaps.map(g => Math.abs(g.dx))) }, contacts, penetration, penetrationTooth, insideVertices });
}
const report = { path, units: 'unidades del modelo; no milimetros clinicos', method: 'EscenaBoca.aplicar real + Mesh.getVertexPosition; distancia vertice labial a superficie dental, no certifica ausencia de intersecciones', results };
writeFileSync(process.argv[3] ?? resolve(out, 'medidas.json'), JSON.stringify(report, null, 2));
const summary = { poses: results.length, maximumPenetration: Math.max(...results.map(r => r.penetration)), closureError: Math.max(...results.filter(r => ['reposo','p','b','m'].includes(r.symbol)).flatMap(r => [Math.abs(r.gaps.min),Math.abs(r.gaps.max),r.gaps.depthMax])), labiodentalDistances: results.filter(r => ['f','v'].includes(r.symbol)).map(r => r.contacts.map(c => c.distance)), release: ['p','b'].map(s => Math.max(...results.filter(r => r.symbol.startsWith(s+'@')).map(r => r.gaps.max))) };
console.log(JSON.stringify(summary, null, 2));
const sectionReport={sharedLipVertices:seams.length,seamError,sectionStatesOverTolerance,sectionAreaError,sectionAreaTolerance,sectionWorst};
writeFileSync(resolve(out,'secciones-medidas.json'),JSON.stringify(sectionReport,null,2));
console.log(JSON.stringify(sectionReport));
console.log(JSON.stringify({upperLipFold,upperLipFoldWorst}));
console.log(JSON.stringify({rootVertices:raices.length,rootError,rootWorst}));
if(process.argv.includes('--exigir-raices') && (raices.length<4 || rootError>1e-5)) {
  console.error('La raiz del corte labial se separa del maxilar/mandibula');process.exitCode=1;
}
if(process.argv.includes('--exigir') && upperLipFold>.015) {
  console.error('El labio superior se pliega sobre el filtrum');process.exitCode=1;
}
if(process.argv.includes('--exigir') && sectionStatesOverTolerance) process.exitCode=1;
if (process.argv.includes('--exigir') && sections.length && (seams.length<14 || seamError>1e-4)) {
  console.error('El corte labial no coincide con el exterior');process.exitCode=1;
}
if (full && process.argv.includes('--exigir')) {
  const pose = s => results.find(r => r.symbol === s);
  const fail = ['t','d','n','k','ɡ','ŋ','l','h','θ','ð','ɪ','ɛ','ɑ','ʌ','ə','ɚ'].some(s => pose(s).gaps.max < .1)
    || pose('u').aperture.width >= pose('i').aperture.width*.5
    || pose('u').aperture.height >= pose('ɔ').aperture.height;
  if (fail) { console.error('Contrato de abertura/redondeamiento incumplido'); process.exitCode = 1; }
}
if (process.argv.includes('--exigir') && (summary.closureError > 1e-4 || summary.maximumPenetration > .002 || summary.labiodentalDistances.flat().some(d => d > .008) || summary.release.some(g => g < .05))) process.exitCode = 1;
