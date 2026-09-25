// Grosor central en81 pasos del ciclo /u/, con aplicar() REAL del visor.
// node tools/boca3d_demo/medir_grosor_labial.mjs cara.glb informe.json --exigir
// No necesita navegador. Mide altura aparente, no volumen ni anatomía clínica.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { build } from '../../front/node_modules/esbuild/lib/main.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const out = resolve(root, 'build/redondeo_grosor');
mkdirSync(out, { recursive: true });
await build({ stdin: { contents: `export * from './front/src/app/compartido/boca3d/escena';
export * from './front/src/app/compartido/boca3d/poses';
export * from './front/src/app/compartido/boca3d/animacion';
export { mergeGeometries, mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import * as THREE from 'three'; export { THREE };`, resolveDir: root },
  bundle: true, platform: 'node', format: 'esm', nodePaths: [resolve(root, 'front/node_modules')],
  outfile: resolve(out, 'medidor-runtime.mjs'), logLevel: 'silent' });
const { THREE: T, EscenaBoca, poseNumerica, pielQueSigueLaMandibula, conAjustes3d, cicloSonido, mergeGeometries, mergeVertices } = await import(pathToFileURL(resolve(out, 'medidor-runtime.mjs')));
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
const dummy = () => new T.Mesh(new T.BufferGeometry(), new T.MeshStandardMaterial());
const scene = Object.create(EscenaBoca.prototype);
Object.assign(scene, { mandibula: new T.Group(), velo: new T.Group(), aireNasal: dummy(), aireOral: dummy(), marcaContacto: dummy(), marcaVibracion: dummy(),
  labioSup: dummy(), labioInf: dummy(), pielesConLabios: animatedSkin, pielesDeformables: animatedSkin.map(m => pielQueSigueLaMandibula(m.geometry, true, true, true)),
  lenguaGlb: { morphTargetInfluences: [] }, indicesMorfos: [], labio() {} });
const bases = skin.map(m => Array.from({ length: m.geometry.attributes.position.count }, (_, i) => new T.Vector3().fromBufferAttribute(m.geometry.attributes.position, i)));

// Perfil central real del visor: borde del anillo1 al cuerpo del anillo3.
// Altura aparente y distancia sagital; no equivalen a volumen o mm clínicos.
const rig=exterior.geometry.getAttribute('uv1');
function nearest(v) { return bases[0].map((p,i)=>[p.distanceTo(v),i]).sort((a,b)=>a[0]-b[0])[0][1]; }
const perfiles=[['superior',.163,1],['inferior',.137,-1]].map(([nombre,y,s])=>{
 const cuerpo=bases[0].map((v,i)=>({v,i})).filter(({v,i})=>Math.abs(v.z)<1e-5 && Math.abs(rig.getX(i)-.05)<1e-6 && s*(v.y-.15)>0);
 if(cuerpo.length!==1)throw new Error('Anillo central ambiguo: '+nombre);
 return {nombre,borde:nearest(new T.Vector3(-3.13,y,0)),cuerpo:cuerpo[0].i};
});
// Anchura del cuerpo completo (anillo3), además del grosor central. Un
// centro grueso puede ocultar un estrechamiento excesivo en los laterales.
const cuerpoIds=bases[0].map((p,i)=>i).filter(i=>Math.abs(rig.getX(i)-.05)<1e-6);
if(cuerpoIds.length<60)throw new Error('Contorno de cuerpo incompleto');
const comisuras=[-1,1].map(s=>nearest(new T.Vector3(-3.13+.46*1.03**2,.15,s*1.03)));
function anchuras(){
 const laterales=cuerpoIds.map(i=>exterior.getVertexPosition(i,new T.Vector3()).z);
 const borde=comisuras.map(i=>exterior.getVertexPosition(i,new T.Vector3()).z);
 return {cuerpo:Math.max(...laterales)-Math.min(...laterales),abertura:Math.abs(borde[1]-borde[0])};
}
function medir() { return Object.fromEntries(perfiles.map(({nombre,borde,cuerpo})=>{
 const a=exterior.getVertexPosition(borde,new T.Vector3()),b=exterior.getVertexPosition(cuerpo,new T.Vector3());
 return [nombre,{altura:Math.abs(b.y-a.y),sagital:Math.hypot(b.y-a.y,b.x-a.x),perfil:[a.toArray(),b.toArray()]}];
})); }
const catalog=conAjustes3d(JSON.parse(readFileSync(resolve(root,'front/src/app/compartido/boca3d/poses.ejemplo.json'))),JSON.parse(readFileSync(resolve(root,'front/src/app/compartido/boca3d/poses.ajustes3d.json'))));
scene.aplicar(poseNumerica(catalog.reposo));const reposo=medir(),anchurasReposo=anchuras();
const line=cicloSonido(catalog.sonidos.u,catalog);
scene.linea={total:line.total,claves:line.claves.map(c=>{
 const n=poseNumerica(c.pose);
 if(c.hacia){const to=poseNumerica(c.hacia);n.forEach((v,i)=>n[i]=v+(to[i]-v)*(c.f??.5));}
 return {t:c.t,n};
})};
const muestras=[];
for(let i=0;i<=80;i++) { const t=line.total*i/80;scene.aplicar(scene.poseDeLinea(t));muestras.push({t,perfiles:medir(),anchuras:anchuras()}); }
scene.aplicar(poseNumerica(catalog.sonidos.u));const u=medir(),anchurasU=anchuras();
const resumen=Object.fromEntries(perfiles.map(({nombre})=>[nombre,{
 reposo:reposo[nombre].altura,u:u[nombre].altura,
 minimo:Math.min(...muestras.map(m=>m.perfiles[nombre].altura)),
 maximo:Math.max(...muestras.map(m=>m.perfiles[nombre].altura)),
 relacionU:u[nombre].altura/reposo[nombre].altura,
 relacionMinima:Math.min(...muestras.map(m=>m.perfiles[nombre].altura))/reposo[nombre].altura
}]));
for(const p of Object.values(resumen))if(!Number.isFinite(p.relacionMinima)||p.minimo<=0)throw new Error('Perfil colapsado');
const contorno={reposo:anchurasReposo,u:anchurasU,cuerpoUReposo:anchurasU.cuerpo/anchurasReposo.cuerpo,cuerpoUAbertura:anchurasU.cuerpo/anchurasU.abertura};
// Muestreo del mismo perfil central en todo el catálogo: permite comparar
// familias abiertas, estiradas y cerradas sin confundir altura con volumen.
const familias={};
for(const [simbolo,pose] of Object.entries(catalog.sonidos)){
 scene.aplicar(poseNumerica(pose));
 familias[simbolo]={perfiles:medir(),anchuras:anchuras()};
}
writeFileSync(process.argv[3],JSON.stringify({modelo:path,resumen,contorno,muestras,perfiles,familias},null,2));
console.log(JSON.stringify(resumen));
console.log(JSON.stringify({contorno}));
// Umbral de diseño del piloto: evita perder más del10% de altura central
// durante el ciclo. No es una tolerancia anatómica ni una prueba de volumen.
if(process.argv.includes('--exigir') && Object.values(resumen).some(p=>p.relacionMinima<.90))
 throw new Error('El ciclo pierde más del10% del grosor central de reposo');
