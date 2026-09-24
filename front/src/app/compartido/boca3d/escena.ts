/** La boca esquemática en three.js, sin Angular.
 *
 *  Corte sagital con piezas simples: paladar y velo (con bisagra), dientes en
 *  arco, labios como dos cápsulas, mandíbula que gira en un pivote y arrastra
 *  dientes inferiores y labio inferior, lengua como un tubo flexible de seis
 *  nudos (raíz baja, raíz alta, dorso, centro, lámina, punta) cuyo perfil se
 *  reconstruye en cada pose. La cara mira a la izquierda, como en el 2D.
 *
 *  Ejes: -x delante (labios), +x atrás (faringe), +y arriba, z lateral. Las
 *  unidades son arbitrarias: la cavidad mide unos 6 de largo.
 *
 *  Las poses (`PoseSonido`) son los mismos parámetros que el corte 2D de
 *  `app/animacion_articulatoria`; aquí se convierten a una pose numérica
 *  plana y se interpola entre dos con suavizado. Con `reducirMovimiento` no
 *  hay interpolación: se salta a la pose. */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader, type GLTF } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries, mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';

/** Los .glb se bajan una vez por página. El Space los sirve tras una URL firmada
 *  que cambia en cada petición, así que la caché del navegador no los reutilizaba
 *  y cada apertura volvía a bajar cara.glb y lengua.glb, 2,7 MB (4e, ronda 3: 26 y
 *  27 peticiones en 27 aperturas). Se guardan los bytes y no el modelo: `destruir`
 *  suelta geometrías y materiales, y `parse` los rehace sin tocar el buffer. Un
 *  fallo no se queda guardado: la siguiente apertura lo vuelve a intentar. */
const glbs = new Map<string, Promise<ArrayBuffer>>();

export function bajarGlb(url: string): Promise<ArrayBuffer> {
  let bytes = glbs.get(url);
  if (!bytes) {
    bytes = fetch(url).then(r => {
      if (!r.ok) throw new Error(`${r.status} ${url}`);
      return r.arrayBuffer();
    });
    glbs.set(url, bytes);
    bytes.catch(() => glbs.delete(url));
  }
  return bytes;
}

function cargarGlb(url: string, alLlegar: (gltf: GLTF) => void, alFallar: () => void): void {
  bajarGlb(url).then(
    bytes => new GLTFLoader().parse(bytes, url.slice(0, url.lastIndexOf('/') + 1), alLlegar, alFallar),
    alFallar);
}
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

/** Normales del gesto real, soldando sólo para el cálculo las costuras UV.
 * El GLB contiene deltas de posición; iluminarlo con normales de reposo
 * producía pliegues radiales falsos al fruncir. No cambia los contactos. */
export function normalesDelGesto(malla: THREE.Mesh, conservarNariz = false): () => void {
  const origen = malla.geometry;
  const p = origen.getAttribute('position');
  const mapa = new Map<string, number>(), representantes: number[] = [], correspondencia: number[] = [];
  for (let i=0;i<p.count;i++) {
    const clave=[p.getX(i),p.getY(i),p.getZ(i)].map(v=>Math.round(v*1e5)).join(',');
    let j=mapa.get(clave);
    if (j===undefined) { j=representantes.length; mapa.set(clave,j); representantes.push(i); }
    correspondencia.push(j);
  }
  const calculo = new THREE.BufferGeometry();
  const posiciones = new THREE.Float32BufferAttribute(new Float32Array(representantes.length*3),3);
  calculo.setAttribute('position',posiciones);
  calculo.setIndex(Array.from(origen.index?.array ?? correspondencia.map((_,i)=>i),i=>correspondencia[i]));
  if (!origen.getAttribute('normal')) origen.setAttribute('normal',new THREE.Float32BufferAttribute(new Float32Array(p.count*3),3));
  const destino=origen.getAttribute('normal');
  const originales=conservarNariz ? new Float32Array(destino.array) : null;
  const fijas=representantes.map(i=>conservarNariz ? THREE.MathUtils.smoothstep(p.getY(i),1.05,1.30) : 0);
  const punto=new THREE.Vector3();
  const normales=new Float32Array(representantes.length*3);
  const triangulos=calculo.index!.array;
  const a=new THREE.Vector3(), b=new THREE.Vector3(), c=new THREE.Vector3();
  const ab=new THREE.Vector3(), ac=new THREE.Vector3(), normal=new THREE.Vector3();
  return () => {
    representantes.forEach((i,j)=>{malla.getVertexPosition(i,punto);posiciones.setXYZ(j,punto.x,punto.y,punto.z);});
    // Ponderar por ángulo, no por área: al cortar la nariz en dos aparecen
    // triángulos muy estrechos. El promedio por área dejaba una franja de
    // normales inclinadas a un lado aunque los vértices estuvieran soldados.
    normales.fill(0);
    for(let t=0;t<triangulos.length;t+=3) {
      const ia=triangulos[t], ib=triangulos[t+1], ic=triangulos[t+2];
      if(fijas[ia]===1 && fijas[ib]===1 && fijas[ic]===1)continue;
      a.fromBufferAttribute(posiciones,ia); b.fromBufferAttribute(posiciones,ib); c.fromBufferAttribute(posiciones,ic);
      ab.subVectors(b,a); ac.subVectors(c,a); normal.crossVectors(ab,ac);
      const area=normal.length(); if(area<1e-12)continue; normal.divideScalar(area);
      const aa=Math.atan2(area,ab.dot(ac));
      ab.subVectors(a,b); ac.subVectors(c,b);
      const bb=Math.atan2(area,ab.dot(ac)), cc=Math.PI-aa-bb;
      normales[3*ia]+=normal.x*aa; normales[3*ia+1]+=normal.y*aa; normales[3*ia+2]+=normal.z*aa;
      normales[3*ib]+=normal.x*bb; normales[3*ib+1]+=normal.y*bb; normales[3*ib+2]+=normal.z*bb;
      normales[3*ic]+=normal.x*cc; normales[3*ic+1]+=normal.y*cc; normales[3*ic+2]+=normal.z*cc;
    }
    correspondencia.forEach((j,i)=>{
      const x=normales[3*j], y=normales[3*j+1], z=normales[3*j+2], l=Math.hypot(x,y,z)||1;
      const f=fijas[j];
      if(originales && f>0) {
        punto.set(x/l*(1-f)+originales[3*i]*f,y/l*(1-f)+originales[3*i+1]*f,z/l*(1-f)+originales[3*i+2]*f).normalize();
        destino.setXYZ(i,punto.x,punto.y,punto.z);
      } else destino.setXYZ(i,x/l,y/l,z/l);
    });
    destino.needsUpdate=true;
  };
}
import { Linea } from './animacion';
import { Familia, Labios, PoseSonido, REPOSO } from './poses';

export interface Colores {
  lengua: string; labios: string; dientes: string; encia: string; velo: string; hueso: string; faringe: string;
  piel: string; mucosa: string;
}

/** Colores de tejido vivo: lengua rosada, encías rosa claro, dientes marfil,
 *  piel cálida y mucosa húmeda un punto más oscura que la encía. Todos van
 *  a materiales físicos (`materialDe`). */
export const COLORES_POR_DEFECTO: Colores = {
  lengua: '#c85f72', labios: '#c9686e', dientes: '#f1e9d8', encia: '#e6989d', velo: '#d68b90',
  hueso: '#e6dcc9', faringe: '#c98a8c', piel: '#eac2ad', mucosa: '#cf868a',
};

/** Qué tejido es cada pieza: decide brillo y respuesta superficial.
 *  Sheen es brillo superficial; no sustituye dispersión subsuperficial. */
export type Tejido = 'piel' | 'mucosa' | 'encia' | 'diente' | 'hueso' | 'labio' | 'lengua';

/** Las poses pueden volver cóncavo el corte: triangula el contorno deformado,
 * reutilizando el buffer para no acumular recursos GPU durante la animación. */
export function actualizarSeccionSagital(m: THREE.Mesh): void {
  const p = m.geometry.getAttribute('position');
  const contorno = Array.from({length:p.count},(_,i) => {
    const v=m.getVertexPosition(i,new THREE.Vector3());return new THREE.Vector2(v.x,v.y);
  });
  const indices=THREE.ShapeUtils.triangulateShape(contorno,[]).flat();
  const indice=m.geometry.index!;
  if(indice.count < indices.length) throw new Error('Capacidad insuficiente de sección sagital');
  (indice.array as Uint16Array | Uint32Array).set(indices);
  indice.needsUpdate=true;m.geometry.setDrawRange(0,indices.length);
}

function texturaTejidoCortado(): THREE.CanvasTexture | null {
  if(typeof document==='undefined') return null;
  const canvas=document.createElement('canvas');canvas.width=512;canvas.height=256;
  const ctx=canvas.getContext('2d');if(!ctx) return null;
  ctx.fillStyle='#f7eeec';ctx.fillRect(0,0,512,256);
  // Estriado tenue de ilustración; no es un mapa de músculos etiquetados.
  for(let i=0;i<70;i++) {
    ctx.beginPath();ctx.moveTo(-10,120+i*1.5);
    ctx.bezierCurveTo(150,90+i*1.9,350,30+i*2.6,522,45+i*2.8);
    ctx.strokeStyle=i%3===0?'rgba(134,75,77,.16)':'rgba(134,75,77,.07)';
    ctx.lineWidth=.7;ctx.stroke();
  }
  const t=new THREE.CanvasTexture(canvas);t.colorSpace=THREE.SRGBColorSpace;return t;
}

/** Sección medial de la lengua, con los mismos deltas que su superficie.
 * No remodela la lengua ni altera contactos; cierra visualmente el corte. */
export function seccionSagitalLengua(fuente: THREE.Mesh): (THREE.Mesh & { actualizar: () => void }) | null {
  const g = fuente.geometry, p = g.getAttribute('position');
  const ids: number[] = [];
  const canonicos=new Map<number,number>();
  for (let i = 0; i < p.count; i++) {
    if (Math.abs(p.getZ(i)) > 1e-4) continue;
    const igual=ids.find(j => Math.hypot(p.getX(i)-p.getX(j), p.getY(i)-p.getY(j)) < 1e-5);
    if(igual===undefined) ids.push(i);
    canonicos.set(i,igual??i);
  }
  if (ids.length < 6 || !g.index) return null;
  // Seguir aristas reales: ordenar por ángulo cruzaría el contorno cóncavo
  // de la raíz, aunque pareciera correcto en reposo.
  const vecinos=new Map(ids.map(i => [i,new Set<number>()]));
  const ind=g.index.array;
  for(let i=0;i<ind.length;i+=3) for(let k=0;k<3;k++) {
    const a=canonicos.get(ind[i+k]),b=canonicos.get(ind[i+(k+1)%3]);
    if(a!==undefined&&b!==undefined&&a!==b) {vecinos.get(a)!.add(b);vecinos.get(b)!.add(a);}
  }
  if([...vecinos.values()].some(v => v.size!==2)) return null;
  const orden=[ids[0]];
  while(orden.length<ids.length) {
    const siguiente=[...vecinos.get(orden[orden.length-1])!].find(i => !orden.includes(i));
    if(siguiente===undefined) return null;orden.push(siguiente);
  }
  ids.splice(0,ids.length,...orden);
  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(ids.flatMap(i => [p.getX(i),p.getY(i),.006]),3));
  geom.setIndex(new THREE.Uint16BufferAttribute(new Uint16Array((ids.length-2)*3),1).setUsage(THREE.DynamicDrawUsage));
  geom.morphTargetsRelative = g.morphTargetsRelative;
  geom.morphAttributes.position = (g.morphAttributes.position ?? []).map(a =>
    new THREE.Float32BufferAttribute(ids.flatMap(i => [a.getX(i),a.getY(i),g.morphTargetsRelative ? 0 : .006]),3));
  geom.setAttribute('normal',new THREE.Float32BufferAttribute(ids.flatMap(() => [0,0,1]),3));
  const textura=texturaTejidoCortado();
  const tejido = materialDe('mucosa','#c8838a',{roughness:.86,sheen:0,side:THREE.DoubleSide,...(textura?{map:textura}:{})});
  geom.setAttribute('uv',new THREE.Float32BufferAttribute(ids.flatMap(i => [(p.getX(i)+2.6)/5.4,(p.getY(i)+1.8)/3.8]),2));
  const corte = Object.assign(new THREE.Mesh(geom, tejido), { actualizar: () => {} });
  corte.layers.set(0);
  corte.morphTargetDictionary = { ...fuente.morphTargetDictionary };
  corte.morphTargetInfluences = fuente.morphTargetInfluences;
  corte.actualizar=() => actualizarSeccionSagital(corte);
  // Masa extrínseca de apoyo: la superficie superior sigue el vientre de
  // la lengua; su inserción anterior acompaña a la mandíbula. Ilustrativa,
  // sin convertir el esquema en una simulación de músculos individuales.
  const vientre = ids.filter(i => {
    const t = Math.max(0,Math.min(1,(p.getX(i)-.55)/2.05));
    return p.getX(i)>-1.6 && p.getY(i)<-.45-.55*t*t*(3-2*t)-.025;
  }).sort((a,b) => p.getX(a)-p.getX(b));
  if (vientre.length > 3) {
    const puntos = [...vientre,...vientre.slice().reverse()].map(i => [p.getX(i),p.getY(i)]);
    const apoyo = new THREE.BufferGeometry();
    apoyo.setAttribute('position',new THREE.Float32BufferAttribute(puntos.flatMap(q => [q[0],q[1],.009]),3));
    apoyo.setIndex(new THREE.Uint16BufferAttribute(new Uint16Array((puntos.length-2)*3),1).setUsage(THREE.DynamicDrawUsage));
    apoyo.setAttribute('normal',new THREE.Float32BufferAttribute(puntos.flatMap(() => [0,0,1]),3));
    apoyo.setAttribute('uv',new THREE.Float32BufferAttribute(puntos.flatMap(q => [(q[0]+2.6)/5.4,(q[1]+1.8)/3.8]),2));
    const musculo = new THREE.Mesh(apoyo, tejido);
    musculo.layers.set(0);
    corte.actualizar=() => {
      actualizarSeccionSagital(corte);
      // Relleno ilustrativo hacia el suelo. En vocales abiertas el vientre
      // puede descender más: nunca cruza la superficie superior de la lengua.
      const pos=apoyo.getAttribute('position');
      vientre.forEach((i,j) => {
        const v=fuente.getVertexPosition(i,new THREE.Vector3());
        pos.setXYZ(j,v.x,v.y,.009);
        pos.setXYZ(puntos.length-1-j,v.x,Math.min(-1.58,v.y-.025),.009);
      });
      pos.needsUpdate=true;actualizarSeccionSagital(musculo);
      apoyo.computeBoundingSphere();
    };
    corte.add(musculo);
  }
  return corte;
}

/** Un material físico por tejido, sin texturas descargadas. La piel y la
 *  mucosa llevan un velo (sheen) que aclara los bordes como la luz que
 *  atraviesa el tejido; la mucosa, la encía y la lengua, un barniz fino y
 *  poco rugoso (húmedas); los dientes, barniz duro y un velo cálido que
 *  imita la leve translucidez del esmalte. */
/** v5: los tejidos sin clearcoat ni sheen (piel, hueso) van en
 *  `MeshStandardMaterial`; `usarMaterialesBaratos(false)` vuelve a lo físico
 *  en todos (para medir). El tipo devuelto sigue siendo el físico: el
 *  estándar es su superclase y nadie usa aquí propiedades exclusivas. */
let MATERIALES_BARATOS = true;
export function usarMaterialesBaratos(si: boolean): void { MATERIALES_BARATOS = si; }

export function materialDe(tejido: Tejido, color: string, extra: Partial<THREE.MeshPhysicalMaterialParameters> = {}): THREE.MeshPhysicalMaterial {
  const base: Record<Tejido, Partial<THREE.MeshPhysicalMaterialParameters>> = {
    piel: { roughness: 0.87, clearcoat: 0, sheen: 0 },
    mucosa: { roughness: 0.4, clearcoat: 0.5, clearcoatRoughness: 0.32, sheen: 0.45, sheenRoughness: 0.6, sheenColor: new THREE.Color('#ffb0b4') },
    encia: { roughness: 0.3, clearcoat: 0.6, clearcoatRoughness: 0.25, sheen: 0.4, sheenRoughness: 0.6, sheenColor: new THREE.Color('#ffc0c4') },
    diente: { roughness: 0.3, clearcoat: 0.65, clearcoatRoughness: 0.18, sheen: 0.35, sheenRoughness: 0.5, sheenColor: new THREE.Color('#fff4dc'), ior: 1.6 },
    // v5: sin sheen (era un brillo apenas visible en las caras del corte y la
    // pared del fondo, que ocupan media pantalla): con clearcoat y sheen a 0
    // el material baja a MeshStandardMaterial, más barato por píxel.
    hueso: { roughness: 0.72, clearcoat: 0, sheen: 0 },
    labio: { roughness: 0.45, clearcoat: 0.3, clearcoatRoughness: 0.35, sheen: 0.5, sheenRoughness: 0.65, sheenColor: new THREE.Color('#ffb6b0') },
    // La lengua es el articulador, no una superficie barnizada: más mate que
    // encía/paladar, con un rojo algo más profundo para separarla de ambos.
    lengua: { roughness: 0.72, clearcoat: 0.08, clearcoatRoughness: 0.82, sheen: 0.22, sheenRoughness: 0.85, sheenColor: new THREE.Color('#f2a0aa') },
  };
  const parametros = { color: new THREE.Color(color), metalness: 0, ...base[tejido], ...extra };
  if (MATERIALES_BARATOS && !(parametros.clearcoat ?? 0) && !(parametros.sheen ?? 0) && !parametros.transmission) {
    const { clearcoat, clearcoatRoughness, sheen, sheenRoughness, sheenColor, ior, ...estandar } = parametros;
    return new THREE.MeshStandardMaterial(estandar) as unknown as THREE.MeshPhysicalMaterial;
  }
  return new THREE.MeshPhysicalMaterial(parametros);
}

/** Un canvas cuadrado pintado por `pintar`, como textura repetida. Sin
 *  canvas 2D (pruebas), null. */
function texturaCanvas(lado: number, repetir: [number, number], pintar: (ctx: CanvasRenderingContext2D, azar: () => number) => void): THREE.Texture | null {
  try {
    const c = document.createElement('canvas');
    c.width = c.height = lado;
    const ctx = c.getContext('2d');
    if (!ctx) return null;
    let semilla = 7;
    const azar = () => { semilla = (semilla * 16807) % 2147483647; return semilla / 2147483647; };
    pintar(ctx, azar);
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(repetir[0], repetir[1]);
    return t;
  } catch {
    return null;
  }
}

/** Puntitos suaves al azar sobre gris medio: relieve de papilas (lengua,
 *  encías). `n` puntos de radio `r0..r1` en un canvas de 256. */
function texturaPapilas(n = 2600, r0 = 1.6, r1 = 4, repetir: [number, number] = [5, 3]): THREE.Texture | null {
  return texturaCanvas(256, repetir, (ctx, azar) => {
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, 256, 256);
    for (let i = 0; i < n; i++) {
      const x = azar() * 256, y = azar() * 256, r = r0 + azar() * (r1 - r0);
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, `rgba(255,255,255,${0.35 + azar() * 0.4})`);
      g.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = g;
      ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
    }
  });
}

/** Hueso y tejido cortados: vetas claras y oscuras muy suaves (manchas
 *  grandes) y un grano fino, para que las caras del corte no sean un color
 *  plano. Va como mapa de color (multiplica el marfil) y de relieve. */
function texturaHueso(): THREE.Texture | null {
  return texturaCanvas(256, [1.2, 1.2], (ctx, azar) => {
    ctx.fillStyle = '#e8e2dc';
    ctx.fillRect(0, 0, 256, 256);
    for (let i = 0; i < 90; i++) {
      const x = azar() * 256, y = azar() * 256, r = 14 + azar() * 40;
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      const claro = azar() > 0.5;
      g.addColorStop(0, claro ? 'rgba(255,250,244,0.22)' : 'rgba(150,120,110,0.16)');
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
    }
    for (let i = 0; i < 9000; i++) {
      ctx.fillStyle = azar() > 0.5 ? 'rgba(255,255,255,0.10)' : 'rgba(90,70,60,0.08)';
      ctx.fillRect(azar() * 256, azar() * 256, 1.4, 1.4);
    }
  });
}

/** Coordenadas de textura planas (x, y del mundo) para piezas que vienen de
 *  Blender sin UV: bastan para un relieve sutil. */
function uvPlanas(g: THREE.BufferGeometry, escala = 0.35): void {
  const pos = g.getAttribute('position');
  const uv = new Float32Array(pos.count * 2);
  for (let i = 0; i < pos.count; i++) {
    uv[2 * i] = (pos.getX(i) + pos.getZ(i) * 0.7) * escala;
    uv[2 * i + 1] = pos.getY(i) * escala;
  }
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}

// --- Anatomía fija -----------------------------------------------------------

/** Perfil del paladar de delante (cuello de los incisivos) a atrás (arranque del velo). */
const PALADAR: [number, number][] = [
  [-2.55, 0.5], [-2.3, 0.75], [-2.05, 0.92], [-1.7, 1.15], [-1.2, 1.35], [-0.6, 1.48],
  [0.0, 1.52], [0.6, 1.5], [1.2, 1.42], [1.7, 1.32], [2.05, 1.22],
];
const GROSOR_PALADAR = 0.26;
const ANCHO = 2.7;                              // de mejilla a mejilla (z)
const PIVOTE_VELO = new THREE.Vector2(2.05, 1.22);
const LARGO_VELO = 1.2;
const VELO_CERRADO = -0.44, VELO_ABIERTO = -1.22;   // radianes desde +x hacia abajo
const PIVOTE_MAND = new THREE.Vector2(2.6, 0.9);
// Cierre de cara (22 sep 2026): 0,42 → 0,21 para que /æ/ abra ~30 mm entre los
// labios como la boca de Miguel (≈24–30), no 53, con el labio de abajo siguiendo
// al hueso (k = 1). El MISMO valor vive en cara.py (clave de cierre y banda
// labios-dientes) y en lengua.py (comprobación del techo y la punta interdental).
const MAND_MAX = 0.21;                          // radianes con mandibula = 1
const FARINGE_X = 3.15;

/** Hasta dónde deja girar el visor (Miguel, 16 sep; auditoria/boca3d_giro_2026-09-16.md).
 *  El modelo es media cabeza seccionada, hecha para verse de perfil: girada −45° sale media
 *  cara con la mandíbula cortada y la otra mitad translúcida detrás, y a 20° de elevación ya
 *  se ven los planos de corte. El azimut es asimétrico: hacia la cara llega a −34° porque el
 *  perfil real queda en −3,3° tras cargar la cara y el giro automático de los labios
 *  redondeados suma −30° (`giroPara`). La elevación, ±10° alrededor del perfil (85,4°). */
export const LIMITES_GIRO = {
  azimutMin: -34 * Math.PI / 180,
  azimutMax: 20 * Math.PI / 180,
  polarMin: 75 * Math.PI / 180,
  polarMax: 96 * Math.PI / 180,
} as const;

export function aplicarLimitesGiro(controles: OrbitControls, limites: typeof LIMITES_GIRO = LIMITES_GIRO): void {
  controles.minAzimuthAngle = limites.azimutMin;
  controles.maxAzimuthAngle = limites.azimutMax;
  controles.minPolarAngle = limites.polarMin;
  controles.maxPolarAngle = limites.polarMax;
}

const GR = Math.PI / 180;
/** El polar por defecto (85,4°, el centro ya calibrado de `LIMITES_GIRO`):
 *  ningún preset lo cambia, solo el azimut, el zoom y el rango de giro. Subir
 *  o bajar la elevación no está verificado y es lo que más cerca deja los
 *  planos de corte (comentario de `LIMITES_GIRO` arriba). */
const POLAR_DEFECTO = 1.49;

export interface PresetFamilia {
  /** Azimut inicial (radianes); ver `vista()`. */
  azimut: number;
  /** Multiplica la distancia de encuadre: <1 acerca. */
  zoom: number;
  /** D4.2.1 (Miguel, 18 sep): dónde mira la cámara (x, y), no el punto
   *  universal de siempre. `null` = el comportamiento heredado (el punto
   *  medio de la cavidad oral, distinto si hay cabeza/cara modelada o no).
   *  Coordenadas en el mismo espacio que `LABIO_X`, `INCISIVO_SUP`, etc.
   *  (la anatomía interna no cambia de sitio con la cabeza de MakeHuman). */
  target: readonly [number, number] | null;
  /** Rango de la cámara principal de ESTA familia, dentro de los topes
   *  del corte. El detalle frontal bilabial tiene una cámara independiente. */
  limites: { azimutMin: number; azimutMax: number; polarMin: number; polarMax: number };
  /** Piel cercana: en bilabiales completa los labios al mirar de frente;
   *  en labiodentales se oculta para mostrar el incisivo. */
  mejilla: boolean;
  /** D4.3c: "vista exterior" — esconde lo que compite con el gesto labial.
   *  `bilabial` y `labiodental` esconden lengua/velo; `ninguna` conserva el
   *  interior. La dentadura se decide aparte con `dentadura`. */
  exterior: 'ninguna' | 'bilabial' | 'labiodental';
  /** Qué partes de la dentadura aportan a la explicación de esta familia.
   *  Es independiente de `exterior`: /m/ conserva lengua/velo para la vía
   *  nasal, pero no necesita que la dentadura compita con ellos. */
  dentadura: PerfilDental;
}

type PerfilDental =
  | 'completa' | 'oculta' | 'contexto-nasal' | 'incisivos-superiores'
  | 'incisivos-relevantes' | 'referencia-alveolar' | 'subordinada' | 'sin-anteriores';

type GrupoDental =
  | 'soporte-superior' | 'soporte-inferior'
  | 'incisivo-superior' | 'incisivo-inferior'
  | 'posterior-superior' | 'posterior-inferior';

/** Regla semántica pequeña y comprobable: la malla no cambia; cada familia
 *  decide qué piezas ya existentes siguen visibles. */
function visibleEnPerfilDental(perfil: PerfilDental, grupo: GrupoDental, indice = -1): boolean {
  if (perfil === 'completa') return true;
  if (perfil === 'oculta') return false;
  if (grupo === 'soporte-superior') return true;
  if (perfil === 'incisivos-superiores') return grupo === 'incisivo-superior';
  if (perfil === 'incisivos-relevantes') {
    return grupo === 'incisivo-superior' || (grupo === 'incisivo-inferior' && indice >= 5 && indice <= 6);
  }
  if (perfil === 'referencia-alveolar') {
    return grupo === 'incisivo-superior' && indice >= 5 && indice <= 6;
  }
  // /m/, postalveolares y velares conservan el soporte superior que da
  // contexto a la cavidad, pero no una hilera de dientes protagonista.
  return false;
}

/** D4.2/D4.2.1 (Miguel, 18 sep): una vista inicial por FAMILIA articulatoria,
 *  no una por fonema. Cada `limites` es un subconjunto de `LIMITES_GIRO`:
 *  ningún preset gira más lejos de lo que ya está verificado sin revelar los
 *  planos de corte de la media cabeza. `target` centra el foco en el
 *  articulador protagonista (labios ≈ -2,95 en x, alveolo ≈ -2,0, velo ≈
 *  2,0 y atrás): D4.2 solo acercaba la cámara al punto universal de
 *  siempre, que para bilabiales queda dentro de la cavidad, no en los
 *  labios — de ahí el recorte que vio Miguel. Estos numeros son una
 *  primera corrección a partir de las constantes de geometría (LABIO_X,
 *  INCISIVO_SUP, los `case` de `punta` en `poseNumerica`, `PIVOTE_VELO`),
 *  verificada visualmente en esta ronda (D4.2.1) para bilabial/labiodental;
 *  el resto queda a falta de la misma comprobación con capturas. */
export const PRESETS_FAMILIA: Record<Familia, PresetFamilia> = {
  bilabial: {
    // Corte completo; el detalle frontal simultáneo muestra el sello labial.
    azimut: -4 * GR, zoom: 0.88, target: [-0.1, 0.35], mejilla: true, exterior: 'ninguna', dentadura: 'contexto-nasal',
    limites: { azimutMin: -18 * GR, azimutMax: 14 * GR, polarMin: LIMITES_GIRO.polarMin, polarMax: LIMITES_GIRO.polarMax },
  },
  'nasal-bilabial': {
    // /m/: labios, velo y aire nasal visibles sin pedir un giro al alumno.
    azimut: -4 * GR, zoom: 0.88, target: [-0.1, 0.35], mejilla: true, exterior: 'ninguna', dentadura: 'contexto-nasal',
    limites: { azimutMin: -18 * GR, azimutMax: 14 * GR, polarMin: LIMITES_GIRO.polarMin, polarMax: LIMITES_GIRO.polarMax },
  },
  labiodental: {
    // Foco en el labio inferior + incisivos superiores (INCISIVO_SUP = (-2,55; 0,45)).
    azimut: -24 * GR, zoom: 0.58, target: [-2.55, 0.2], mejilla: false, exterior: 'labiodental', dentadura: 'incisivos-superiores',
    limites: { azimutMin: -32 * GR, azimutMax: -10 * GR, polarMin: LIMITES_GIRO.polarMin, polarMax: LIMITES_GIRO.polarMax },
  },
  dental: {
    // Foco en la zona anterior (interdental: J[5] ronda x=-2,8 en poseNumerica).
    azimut: -2 * GR, zoom: 0.72, target: [-2.6, 0.35], mejilla: true, exterior: 'ninguna', dentadura: 'incisivos-relevantes',
    limites: { azimutMin: -18 * GR, azimutMax: 12 * GR, polarMin: LIMITES_GIRO.polarMin, polarMax: LIMITES_GIRO.polarMax },
  },
  alveolar: {
    // Foco en la zona anterior (alveolar: J[5] en x=-2,05).
    azimut: 0.02, zoom: 0.75, target: [-2.0, 0.5], mejilla: true, exterior: 'ninguna', dentadura: 'referencia-alveolar',
    limites: { azimutMin: -16 * GR, azimutMax: 16 * GR, polarMin: LIMITES_GIRO.polarMin, polarMax: LIMITES_GIRO.polarMax },
  },
  postalveolar: {
    // Foco en la zona anterior (postalveolar: J[5] en x=-1,75).
    azimut: 5 * GR, zoom: 0.78, target: [-1.7, 0.55], mejilla: true, exterior: 'ninguna', dentadura: 'subordinada',
    limites: { azimutMin: -14 * GR, azimutMax: 18 * GR, polarMin: LIMITES_GIRO.polarMin, polarMax: LIMITES_GIRO.polarMax },
  },
  rotico: {
    // D4.2 lo dejaba como postalveolar (Miguel: "igual que alveolares"). Lote
    // fase 1 (22 sep): la /ɹ/ de GA es lengua abombada + raíz contra la
    // faringe (investigación fonética §9.2), y con el foco anterior la pared
    // faríngea (x ≈ 2,9) quedaba fuera del encuadre: el target va al centro
    // de la lengua y el zoom a 1 para ver joroba, punta y faringe a la vez.
    azimut: 6 * GR, zoom: 1.0, target: [-0.3, 0.4], mejilla: true, exterior: 'ninguna', dentadura: 'completa',
    limites: { azimutMin: -14 * GR, azimutMax: 18 * GR, polarMin: LIMITES_GIRO.polarMin, polarMax: LIMITES_GIRO.polarMax },
  },
  velar: {
    // Foco mas posterior (dorso contra el velo: cerca de PIVOTE_VELO = (2,05; 1,22)).
    azimut: 10 * GR, zoom: 0.85, target: [1.6, 0.85], mejilla: true, exterior: 'ninguna', dentadura: 'sin-anteriores',
    limites: { azimutMin: -10 * GR, azimutMax: LIMITES_GIRO.azimutMax, polarMin: LIMITES_GIRO.polarMin, polarMax: LIMITES_GIRO.polarMax },
  },
  vocal: {
    // Sin target propio: vista general, el comportamiento de siempre.
    azimut: 0.02, zoom: 1, target: null, mejilla: true, exterior: 'ninguna', dentadura: 'completa',
    limites: { ...LIMITES_GIRO },
  },
};

const INCISIVO_SUP = new THREE.Vector2(-2.55, 0.45);   // borde inferior del incisivo superior
const INCISIVO_INF_LOCAL = new THREE.Vector2(-2.5, 0.35); // borde superior, en la mandíbula
const LABIO_X = -2.95, LABIO_SUP_Y = 0.45, LABIO_INF_Y = -0.15;

interface FormaLabios { dx: number; len: number; r: number; dyS: number; dyI: number; }
const LABIOS: Record<Labios, FormaLabios> = {
  neutros: { dx: 0, len: 2.3, r: 0.3, dyS: 0, dyI: 0 },
  cerrados: { dx: 0.05, len: 2.2, r: 0.3, dyS: -0.05, dyI: 0 },
  redondeados: { dx: -0.35, len: 1.5, r: 0.34, dyS: -0.03, dyI: 0.03 },
  muy_redondeados: { dx: -0.6, len: 1.05, r: 0.38, dyS: -0.06, dyI: 0.06 },
  estirados: { dx: 0.15, len: 2.9, r: 0.24, dyS: 0.05, dyI: -0.03 },
  labiodental: { dx: 0, len: 2.3, r: 0.28, dyS: 0.08, dyI: 0 },
};

/** Nudos de la lengua en reposo, de la raíz a la punta, y sus radios [lateral, vertical]. */
const NUDOS_REPOSO: [number, number][] = [[1.75, -1.7], [2.15, -0.45], [1.3, 0.05], [0.3, 0.15], [-0.9, -0.05], [-1.9, -0.35]];
/** El suelo de la boca (dentro de la mandíbula): tapa el arranque de la lengua. */
const SUELO = { x0: -2.2, x1: 2.5, y: -1.55, grosor: 0.9 };
const RADIOS: [number, number][] = [[0.45, 0.32], [0.75, 0.4], [1.0, 0.48], [1.0, 0.42], [0.85, 0.32], [0.42, 0.16]];
const N_NUDOS = 6;
/** Mayor doblez admitido en la raíz alta (entre raíz baja → raíz alta y raíz alta → dorso). */
const DOBLEZ_MAX = (85 * Math.PI) / 180;

/** Las shape keys de la lengua modelada en Blender (tools/boca3d_blender/lengua.py),
 *  una por parámetro; sus influencias van en la pose numérica para que se
 *  interpolen igual que todo lo demás. */
export const MORFOS_LENGUA = [
  'mandibula', 'punta_arriba', 'punta_atras', 'punta_interdental', 'cuerpo_alto', 'cuerpo_bajo',
  'cuerpo_delante', 'cuerpo_atras', 'dorso_velo', 'raiz_atras',
] as const;

function liberarModelo(raiz: THREE.Object3D): void {
  raiz.traverse(o => {
    if (o instanceof THREE.Mesh) {
      o.geometry.dispose();
      // Sin soltar sus mapas: la piel escaneada (v5) los sigue usando.
      (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m.dispose());
    }
  });
}

/** D4.4b v5: las texturas que trae la piel escaneada en el GLB (color y
 *  normales, JPEG de 1024 px); `materialDe('piel')` las monta sobre el mismo
 *  material físico. Sin texturas (MakeHuman), `null`. */
function texturasDe(fuente: THREE.Mesh): { map: THREE.Texture; normalMap?: THREE.Texture; normalScale?: THREE.Vector2 } | null {
  const m = (Array.isArray(fuente.material) ? fuente.material[0] : fuente.material) as THREE.MeshStandardMaterial;
  if (!m?.map) return null;
  return { map: m.map, normalMap: m.normalMap ?? undefined, normalScale: m.normalMap ? new THREE.Vector2(0.8, 0.8) : undefined };
}

/** D4.4b v8: el bermellón del escaneo (0..1) en coordenadas del visor, con el
 *  mismo perfil que `perfil_lps` de cara.py: línea de contacto en y 0,15 (sube
 *  0,04 hacia las comisuras), 0,22 de labio arriba y 0,28 abajo, que se afinan
 *  hacia las comisuras, y solo en el frente de la cara (que se curva 0,69 z²).
 *  Medido sobre la textura del escaneo: el rojo del labio en la línea media va
 *  de y 0,36 a −0,08, dentro de esta banda. */
export function bermellonEscaneo(x: number, y: number, z: number): number {
  const ancho = 0.45 * 2.15;
  const contacto = 0.15 + 0.04 * Math.min(1, (z / ancho) ** 2);
  const afina = Math.sqrt(Math.max(0, 1 - (Math.abs(z) / (ancho + 0.1)) ** 2));
  const dentro = y >= contacto ? 0.22 * afina - (y - contacto) : 0.28 * afina - (contacto - y);
  const suave = (a: number, b: number, t: number) => { const u = Math.min(1, Math.max(0, (t - a) / (b - a))); return u * u * (3 - 2 * u); };
  return suave(-0.012, 0.02, dentro) * suave(-2.55 + 0.69 * z * z, -2.7 + 0.69 * z * z, x);
}

/** D4.4b v8: la textura lisa del recuadro: piel de un tono cálido uniforme y
 *  el bermellón donde la foto del escaneo es labio (rojo claro: R − G > 58 y
 *  R > 105), solo dentro de la caja UV de la boca (los vértices con
 *  `bermellonEscaneo` > 0,5) y con el borde suavizado (dos cajas de 7 px). Así
 *  el labio conserva su contorno real y desaparecen barba, poros y manchas.
 *  Sin lienzo (pruebas) devuelve null. */
function texturaLisa(foto: THREE.Texture, mallas: THREE.Mesh[]): THREE.Texture | null {
  const img = foto.image as CanvasImageSource & { width: number; height: number } | undefined;
  if (typeof document === 'undefined' || !img?.width) return null;
  const W = img.width, H = img.height;
  const lienzo = document.createElement('canvas'); lienzo.width = W; lienzo.height = H;
  const cx = lienzo.getContext('2d', { willReadFrequently: true });
  if (!cx) return null;
  cx.drawImage(img, 0, 0);
  const datos = cx.getImageData(0, 0, W, H), px = datos.data;
  // Percentiles 5–95 %: algún vértice del labio lleva la UV de otra isla
  // (con el mínimo y el máximo la caja cogía nariz y ojos).
  const us: number[] = [], vs: number[] = [];
  for (const malla of mallas) {
    const p = malla.geometry.getAttribute('position'), uv = malla.geometry.getAttribute('uv');
    if (!uv) continue;
    for (let i = 0; i < p.count; i++) {
      if (bermellonEscaneo(p.getX(i), p.getY(i), p.getZ(i)) < 0.5) continue;
      us.push(uv.getX(i)); vs.push(uv.getY(i));
    }
  }
  if (us.length < 8) return null;
  const q = (a: number[], f: number) => [...a].sort((x, y) => x - y)[Math.floor(f * (a.length - 1))];
  const [u0, u1, v0, v1] = [q(us, 0.05) - 0.01, q(us, 0.95) + 0.01, q(vs, 0.05) - 0.01, q(vs, 0.95) + 0.01];
  const mascara = new Float32Array(W * H), tmp = new Float32Array(W * H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const u = (x + 0.5) / W, v = foto.flipY ? 1 - (y + 0.5) / H : (y + 0.5) / H;
    if (u < u0 || u > u1 || v < v0 || v > v1) continue;
    const k = 4 * (y * W + x), R = px[k], G = px[k + 1];
    mascara[y * W + x] = Math.min(1, Math.max(0, (R - G - 58) / 18)) * Math.min(1, Math.max(0, (R - 105) / 30));
  }
  const caja = (a: Float32Array, b: Float32Array, dx: number, dy: number) => {
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      let suma = 0, n = 0;
      for (let k = -3; k <= 3; k++) {
        const X = x + k * dx, Y = y + k * dy;
        if (X < 0 || Y < 0 || X >= W || Y >= H) continue;
        suma += a[Y * W + X]; n++;
      }
      b[y * W + x] = suma / n;
    }
  };
  caja(mascara, tmp, 1, 0); caja(tmp, mascara, 0, 1);
  const PIEL = [233, 196, 172], LABIO = [200, 108, 104];
  for (let i = 0; i < W * H; i++) {
    const f = Math.min(1, mascara[i] * 1.4);
    for (let j = 0; j < 3; j++) px[4 * i + j] = PIEL[j] + (LABIO[j] - PIEL[j]) * f;
    px[4 * i + 3] = 255;
  }
  cx.putImageData(datos, 0, 0);
  const tex = new THREE.CanvasTexture(lienzo);
  tex.flipY = foto.flipY; tex.colorSpace = foto.colorSpace; tex.wrapS = foto.wrapS; tex.wrapT = foto.wrapT;
  return tex;
}

/** D4.4b v8: el material de la piel en el recuadro: la textura lisa, sin mapa
 *  de normales (el relieve fino de la foto era barba y poros) y con un 30 % de
 *  luz propia para un sombreado suave (con la piel lisa, las costuras de las
 *  dos mitades y del giro de la mandíbula se marcaban). Sin textura, el tono
 *  de piel plano. */
function materialPielLisa(lisa: THREE.Texture | null, lado: THREE.Side): THREE.MeshPhysicalMaterial {
  return lisa
    ? materialDe('piel', '#ffffff', { map: lisa, emissiveMap: lisa, emissive: new THREE.Color(0.3, 0.3, 0.3), roughness: 0.75, side: lado, vertexColors: true })
    : materialDe('piel', '#e9c4ac', { roughness: 0.75, side: lado, vertexColors: true });
}

/** D4.4b v8: la raya entre los labios. La foto del escaneo trae los labios
 *  sellados (la ranura se abre en cara.py), así que la textura lisa no tiene
 *  raya y el cierre de /p b m/ se leía como una mancha roja. Se oscurecen por
 *  vértice los bordes de la ranura (|y − contacto| < 0,04 en el frente, hasta un 75 %), y el
 *  color viaja con las shape keys. El material con la foto no lo usa. */
function rayaDeLosLabios(malla: THREE.Mesh): void {
  const p = malla.geometry.getAttribute('position'), colores = new Float32Array(p.count * 3);
  const ancho = 0.45 * 2.15;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const contacto = 0.15 + 0.04 * Math.min(1, (z / ancho) ** 2);
    const cerca = Math.max(0, 1 - Math.abs(y - contacto) / 0.04) * (bermellonEscaneo(x, contacto, z) > 0.5 ? 1 : 0);
    const k = 1 - 0.75 * cerca;
    colores.set([k, k * 0.82, k * 0.82], i * 3);
  }
  malla.geometry.setAttribute('color', new THREE.BufferAttribute(colores, 3));
}

/** Distribución: [mand, velo, ls(x,y,len,r), li(x,y,len,r) en local de la mandíbula, 6 nudos (x,y), morfos, aire oral]. */
const I_MAND = 0, I_VELO = 1, I_LS = 2, I_LI = 6, I_NUDOS = 10, I_MORFOS = I_NUDOS + N_NUDOS * 2;
export const I_AIRE_ORAL = I_MORFOS + MORFOS_LENGUA.length;
/** D4.2: punto de contacto real (x, y) y si lo hay (0/1), interpolado igual
 *  que todo lo demás: al mezclar dos poses el «hay contacto» pasa por
 *  fracciones, que es lo que se usa como opacidad del marcador (mismo
 *  criterio que el aro `_TOCA` del 2D, que también se apaga en rampa). */
const I_CONTACTO = I_AIRE_ORAL + 1;
/** D4.3b: 1 si la pose es sonora (para el pulso de vibración), 0 si no. */
const I_SONORA = I_CONTACTO + 3;
/** Morfos propios del 3D, interpolados por la linea existente. */
export const I_CIERRE_LABIOS = I_SONORA + 1;
export const I_COMPRESION_LABIOS = I_CIERRE_LABIOS + 1;
/** El exterior distingue labios neutros articulando del reposo sellado. */
export const I_NEUTRO_ARTICULADO = I_COMPRESION_LABIOS + 1;
const I_CONTORNO_DENTAL = I_NEUTRO_ARTICULADO + 1;
const TAMANO = I_CONTORNO_DENTAL + 1;
type PoseNumerica = Float64Array;

/** Mandíbula para la que cara.py calcula `cierre_labios` (la de reposo). */
export const REFERENCIA_CIERRE = 0.2;

/** Cuánto se juntan los labios: del todo en /p b m/; con los labios neutros,
 *  del todo con la mandíbula casi cerrada (reposo: 0,2) y nada a partir de
 *  media apertura (las vocales abiertas). Fruncidos, estirados y el
 *  labiodental tienen su propia forma y no se cierran. */
export function cierreLabial(pose: PoseSonido): number {
  if (pose.labios === 'cerrados') return 1;
  if (pose.labios !== 'neutros') return 0;
  return Math.min(1, Math.max(0, (0.55 - pose.mandibula) / 0.3));
}

/** Las influencias de las shape keys para una pose: cada parámetro, a su morfo. */
function morfosDe(pose: PoseSonido): number[] {
  const [alt, ade] = pose.cuerpo;
  const toca = pose.punta_toca;
  return [
    0.3 * Math.min(1, Math.max(0, pose.mandibula)),   // el resto lo pone el giro de la mandíbula
    // Cierre de cara: postalveolar con toque 0,85 (era 1): con MAND_MAX 0,21 la suma
    // punta_arriba + cuerpo_alto de /tʃ dʒ/ entraba 0,155 en el paladar (lengua.py).
    // Mismo valor en lengua.py (morfos_de) y en medir_lengua.mjs.
    pose.punta === 'alveolar' || pose.punta === 'postalveolar' ? (toca ? (pose.punta === 'alveolar' ? 1 : 0.85) : 0.75) : pose.punta === 'dental' ? 0.45 : 0,
    pose.punta === 'retrofleja' ? 1 : 0,
    pose.punta === 'interdental' ? 1 : 0,
    Math.max(0, (alt - 0.45) / 0.55),
    Math.max(0, (0.45 - alt) / 0.45),
    Math.max(0, (ade - 0.5) / 0.5),
    Math.max(0, (0.5 - ade) / 0.5),
    // Cierre de cara: sin toque el dorso sube un 10 % menos (/w/); mismo factor en lengua.py y medir_lengua.mjs.
    pose.dorso_velo ? 1 : 0.9 * Math.min(1, pose.dorso_alto),
    Math.min(1, Math.max(0, pose.raiz)),
  ];
}

/** El punto donde algo toca de verdad en esta pose, o `null` (mismo criterio
 *  que `_contacto()` del 2D): dorso contra el velo, punta interdental, punta
 *  que toca en alveolar/postalveolar, o labios cerrados/labiodental. `J` son
 *  los nudos de la lengua ya resueltos (coordenadas del mundo) y `ls`, el
 *  labio superior (también del mundo: no vive dentro de la mandíbula). */
function puntoDeContacto(pose: PoseSonido, J: [number, number][], ls: [number, number]): [number, number] | null {
  if (pose.dorso_velo) return [J[2][0], J[2][1]];
  if (pose.punta === 'interdental') return [J[5][0], J[5][1]];
  if (pose.punta_toca && (pose.punta === 'alveolar' || pose.punta === 'postalveolar')) return [J[5][0], J[5][1]];
  if (pose.labios === 'cerrados' || pose.labios === 'labiodental') return [ls[0], ls[1]];
  return null;
}

function paladarEn(x: number): number {
  if (x <= PALADAR[0][0]) return Infinity;      // delante de los dientes no hay techo
  for (let i = 1; i < PALADAR.length; i++) {
    const [x0, y0] = PALADAR[i - 1], [x1, y1] = PALADAR[i];
    if (x <= x1) return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
  }
  return PALADAR[PALADAR.length - 1][1];
}

/** Un punto de la cara inferior del velo a la fracción `f` de su largo, y la normal hacia abajo. */
function veloEn(angulo: number, f: number): { p: THREE.Vector2; abajo: THREE.Vector2 } {
  const c = Math.cos(angulo), s = Math.sin(angulo);
  const p = new THREE.Vector2(PIVOTE_VELO.x + c * LARGO_VELO * f, PIVOTE_VELO.y + s * LARGO_VELO * f);
  const abajo = new THREE.Vector2(s, -c);      // perpendicular con y negativa
  if (abajo.y > 0) abajo.negate();
  return { p, abajo: abajo.normalize() };
}

/** Altura del techo (paladar o velo) sobre x. Infinito donde no hay nada encima. */
function techoEn(x: number, veloAngulo: number): number {
  if (x <= PIVOTE_VELO.x) return paladarEn(x);
  let mejor = Infinity;
  for (let f = 0; f <= 1; f += 0.1) {
    const { p, abajo } = veloEn(veloAngulo, f);
    const y = p.y + abajo.y * GROSOR_PALADAR / 2;
    if (Math.abs(p.x - x) < 0.25) mejor = Math.min(mejor, y);
  }
  return mejor;
}

function local(mundo: THREE.Vector2, mand: number): THREE.Vector2 {
  // Coordenadas dentro de la mandíbula: deshacer su giro alrededor del pivote.
  const d = mundo.clone().sub(PIVOTE_MAND).rotateAround(new THREE.Vector2(), -mand);
  return d.add(PIVOTE_MAND);
}

function mundo(loc: THREE.Vector2, mand: number): THREE.Vector2 {
  return loc.clone().sub(PIVOTE_MAND).rotateAround(new THREE.Vector2(), mand).add(PIVOTE_MAND);
}

/** De los parámetros articulatorios a la pose numérica plana. */
export function poseNumerica(pose: PoseSonido): PoseNumerica {
  const n = new Float64Array(TAMANO);
  const abre = Math.min(1, Math.max(0, pose.mandibula));
  const mand = abre * MAND_MAX;
  const velo = pose.velo_abierto ? VELO_ABIERTO : VELO_CERRADO;
  n[I_MAND] = mand;
  n[I_VELO] = velo;

  // Labios: el superior fijo; el inferior vive dentro de la mandíbula.
  const f = LABIOS[pose.labios] ?? LABIOS.neutros;
  n[I_LS] = LABIO_X + f.dx; n[I_LS + 1] = LABIO_SUP_Y + f.dyS; n[I_LS + 2] = f.len; n[I_LS + 3] = f.r;
  let li: THREE.Vector2;
  if (pose.labios === 'cerrados') {
    li = local(new THREE.Vector2(LABIO_X + f.dx - 0.02, LABIO_SUP_Y + f.dyS - 2 * f.r + 0.05), mand);
  } else if (pose.labios === 'labiodental') {
    li = local(new THREE.Vector2(INCISIVO_SUP.x - 0.1, INCISIVO_SUP.y - f.r + 0.06), mand);
  } else {
    li = new THREE.Vector2(LABIO_X + f.dx, LABIO_INF_Y + f.dyI);
  }
  n[I_LI] = li.x; n[I_LI + 1] = li.y; n[I_LI + 2] = f.len; n[I_LI + 3] = f.r;

  // Lengua.
  const J = NUDOS_REPOSO.map(p => [p[0], p[1]] as [number, number]);
  const [alt, ade] = pose.cuerpo;
  const bx = (0.5 - ade) * 1.4;                // adelantar = hacia -x
  const by = (alt - 0.45) * (alt < 0.45 ? 2.0 : 1.5);
  // El dorso baja menos que el centro: si no, con la lengua baja y atrás el
  // tubo se dobla sobre la raíz.
  for (const [i, px, py] of [[2, 0.6, 0.6], [3, 1.0, 1.0], [4, 0.9, 0.9]] as [number, number, number][]) {
    J[i][0] += bx * px; J[i][1] += by * py;
  }
  J[2][0] -= pose.dorso_alto * 0.2; J[2][1] += pose.dorso_alto * 0.6;
  // La raíz: la baja está anclada al suelo de la boca (baja con la mandíbula);
  // la alta retrocede hacia la faringe con `raiz` y sigue un poco al cuerpo.
  J[1][0] = Math.min(2.65, J[1][0] + bx * 0.25 + pose.raiz * 0.45); J[1][1] += by * 0.2 - abre * 0.2;
  J[0][0] = Math.min(2.3, J[0][0] + pose.raiz * 0.15); J[0][1] -= abre * 0.3;

  const separar = (i: number, holgura: number) => {
    for (let k = 0; k < 40; k++) {
      const techo = techoEn(J[i][0], velo);
      const d = techo - (J[i][1] + RADIOS[i][1]);
      if (d >= holgura) return;
      J[i][1] -= Math.max(0.02, holgura - d);
    }
  };

  if (pose.dorso_velo) {
    const { p, abajo } = veloEn(velo, 0.55);
    J[2][0] = p.x + abajo.x * (GROSOR_PALADAR / 2 + RADIOS[2][1] - 0.06);
    J[2][1] = p.y + abajo.y * (GROSOR_PALADAR / 2 + RADIOS[2][1] - 0.06);
  } else {
    separar(2, 0.12);
  }
  separar(3, 0.12);

  // Punta y lámina.
  const toca = pose.punta_toca;
  let lamina: [number, number] | null = null;
  const ry5 = RADIOS[5][1], ry4 = RADIOS[4][1];
  switch (pose.punta) {
    case 'interdental': {
      const inf = mundo(INCISIVO_INF_LOCAL, mand);
      const y = (INCISIVO_SUP.y + inf.y) / 2;
      J[5] = [-2.8, y]; lamina = [-2.0, y - 0.05];
      break;
    }
    case 'dental':
      J[5] = [-2.35, INCISIVO_SUP.y - ry5 + 0.02];
      break;
    case 'alveolar':
      J[5] = [-2.05, paladarEn(-2.05) - ry5 + (toca ? 0.03 : -0.22)];
      break;
    case 'postalveolar':
      J[5] = [-1.75, paladarEn(-1.75) - ry5 + (toca ? 0.03 : -0.25)];
      lamina = [-1.25, paladarEn(-1.25) - ry4 + (toca ? 0.0 : -0.3)];
      break;
    case 'retrofleja':
      J[5] = [-1.35, paladarEn(-1.35) - 0.55];
      lamina = [-1.75, 0.05];
      break;
    default: {                                   // reposo: baja con la mandíbula
      const punta = mundo(new THREE.Vector2(NUDOS_REPOSO[5][0], NUDOS_REPOSO[5][1]), mand * 0.7);
      J[5] = [punta.x, punta.y];
    }
  }
  if (lamina) {
    J[4] = lamina;
  } else {
    J[4] = [(J[3][0] + J[5][0]) / 2, (J[3][1] + J[5][1]) / 2 - 0.05];
    separar(4, 0.12);
  }
  // Si la raíz alta queda doblada en ángulo (lengua baja y atrás), se acerca
  // a la recta raíz baja → dorso hasta que el tubo pueda seguir la curva.
  for (let k = 0; k < 12; k++) {
    const a = [J[1][0] - J[0][0], J[1][1] - J[0][1]], b = [J[2][0] - J[1][0], J[2][1] - J[1][1]];
    const la = Math.hypot(a[0], a[1]) || 1, lb = Math.hypot(b[0], b[1]) || 1;
    const doblez = Math.acos(Math.max(-1, Math.min(1, (a[0] * b[0] + a[1] * b[1]) / (la * lb))));
    if (doblez <= DOBLEZ_MAX) break;
    J[1][0] += ((J[0][0] + J[2][0]) / 2 - J[1][0]) * 0.3;
    J[1][1] += ((J[0][1] + J[2][1]) / 2 - J[1][1]) * 0.3;
  }
  for (let i = 0; i < N_NUDOS; i++) {
    n[I_NUDOS + 2 * i] = J[i][0]; n[I_NUDOS + 2 * i + 1] = J[i][1];
  }
  morfosDe(pose).forEach((v, i) => { n[I_MORFOS + i] = v; });
  // El aire por la boca (D4.3b, Miguel 18 sep: «mismo significado que en
  // 2D»): continuo en /h/ (sale de la garganta, nada en la boca que lo
  // pare) y en toda fricativa con constriccion oral (el mismo criterio que
  // `marcas["ab"]`/`"fl"` del 2D: no en el interdental/alveolar sordo o
  // sonoro por separado, en cualquiera con paso estrecho por la boca).
  n[I_AIRE_ORAL] = pose.lugar === 'glotal' || pose.movimiento === 'fricativa' ? 1 : 0;
  const contacto = puntoDeContacto(pose, J, [n[I_LS], n[I_LS + 1]]);
  n[I_CONTACTO] = contacto ? contacto[0] : 0;
  n[I_CONTACTO + 1] = contacto ? contacto[1] : 0;
  n[I_CONTACTO + 2] = contacto ? 1 : 0;
  // D4.3b: sonoridad, para el pulso de vibracion -- una señal aparte del
  // aire, igual que en 2D (`marcas["vi"]` nunca es lo mismo que `"ab"`).
  n[I_SONORA] = pose.sonora ? 1 : 0;
  // D4.4b v4: los labios neutros se juntan al cerrar la mandibula (en reposo,
  // casi juntos; no la boca abierta de la malla). Es una regla de POSE, no de
  // malla: con otra cabeza basta con darle su propia shape key `cierre_labios`.
  // La shape key `cierre_labios` (cara.py) compensa el descenso del labio de
  // abajo con la mandíbula de REPOSO (0,2): con menos apertura hace falta
  // menos (0,4 en /p b m/, que van a 0,08); con más, se queda en 1 y el resto
  // lo decide `cierreLabial`.
  n[I_CIERRE_LABIOS] = cierreLabial(pose) * Math.min(1, Math.max(0, pose.mandibula) / REFERENCIA_CIERRE);
  n[I_COMPRESION_LABIOS] = pose.labios === 'cerrados' ? (pose.movimiento === 'nasal' ? 0.35 : 1) : 0;
  const reposo = !pose.lugar && pose.mandibula === .2 && pose.punta === 'reposo'
    && pose.cuerpo[0] === .45 && pose.cuerpo[1] === .5 && !pose.rotica;
  n[I_NEUTRO_ARTICULADO] = pose.labios === 'neutros' && !reposo ? 1 : 0;
  n[I_CONTORNO_DENTAL] = pose.punta === 'interdental' ? 1 : 0;
  return n;
}

function mezclar(a: PoseNumerica, b: PoseNumerica, t: number): PoseNumerica {
  const r = new Float64Array(TAMANO);
  for (let i = 0; i < TAMANO; i++) r[i] = a[i] + (b[i] - a[i]) * t;
  return r;
}

const suavizar = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

/** Mezcla de dos poses en una transición o entre dos claves de la línea.
 *  D4.4b v6: al salir de un cierre bilabial (compresión > 0,3 → < 0,1) la
 *  mandíbula, el cierre y la compresión van por delante con una curva
 *  brusca (Miguel: de 0 a ≈10 mm en menos de 70 ms), dentro del mismo
 *  tramo de tiempo; el resto de la pose sigue con el suavizado de siempre. */
function mezclarPose(a: PoseNumerica, b: PoseNumerica, f: number): PoseNumerica {
  const r = mezclar(a, b, suavizar(f));
  if (a[I_COMPRESION_LABIOS] > 0.3 && b[I_COMPRESION_LABIOS] < 0.1) {
    const t = Math.min(1, Math.max(0, f));
    const brusco = 1 - Math.pow(1 - t, 5);
    for (const i of [I_MAND, I_CIERRE_LABIOS, I_COMPRESION_LABIOS]) r[i] = a[i] + (b[i] - a[i]) * brusco;
    if (b[I_CIERRE_LABIOS] > 0.9) {
      // Vuelta a una pose sellada (el ciclo de /p b m/ acaba en reposo): sin
      // esto los labios nunca se separaban al soltar, solo se veía el soplo.
      // Rebote de la explosión dentro del mismo tramo: en el primer 45 % el
      // cierre cae a cero y la mandíbula abre hasta ~0,55 (v7: con el labio
      // siguiendo al hueso se ven los dientes en el rebote), y luego vuelven al sello.
      const rebote = t < 0.45 ? Math.sin(Math.PI * t / 0.45) : 0;
      r[I_CIERRE_LABIOS] *= 1 - rebote;
      r[I_MAND] += rebote * 0.5 * MAND_MAX;
      // Compresión negativa: los bordes del bermellón se separan de la línea
      // de contacto (el de arriba sube ~2 mm y asoma el borde de los incisivos).
      r[I_COMPRESION_LABIOS] -= 0.6 * rebote;
    }
  }
  return r;
}

// --- Geometrías --------------------------------------------------------------

function material(color: string, extra: Partial<THREE.MeshStandardMaterialParameters> = {}): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({ color: new THREE.Color(color), roughness: 0.75, metalness: 0, ...extra });
}

/** Una banda que sigue un perfil (x, y) con grosor, extruida a lo ancho (z). */
function banda(perfil: [number, number][], grosor: number, ancho: number): THREE.BufferGeometry {
  const arriba: THREE.Vector2[] = [], abajo: THREE.Vector2[] = [];
  for (let i = 0; i < perfil.length; i++) {
    const [x, y] = perfil[i];
    const [xa, ya] = perfil[Math.max(0, i - 1)], [xb, yb] = perfil[Math.min(perfil.length - 1, i + 1)];
    const n = new THREE.Vector2(-(yb - ya), xb - xa).normalize();
    if (n.y < 0) n.negate();
    arriba.push(new THREE.Vector2(x + n.x * grosor / 2, y + n.y * grosor / 2));
    abajo.push(new THREE.Vector2(x - n.x * grosor / 2, y - n.y * grosor / 2));
  }
  const forma = new THREE.Shape([...arriba, ...abajo.reverse()]);
  const g = new THREE.ExtrudeGeometry(forma, { depth: ancho, bevelEnabled: false, steps: 1 });
  g.translate(0, 0, -ancho / 2);
  return g;
}

/** La arcada dental en planta: u de -1 (izquierda) a 1 (derecha). Frente
 *  plano de incisivos y lados que se abren (|u|^2,6, como la de Bonwill); la
 *  misma curva que cara.py, lengua.py y medir_roces.py. */
const EXPO_ARCO = 2.6;
function arco(u: number, retroceso = 2.3): THREE.Vector2 {
  return new THREE.Vector2(-2.6 + retroceso * Math.pow(Math.abs(u), EXPO_ARCO), (ANCHO / 2) * u);   // (x, z)
}
function tangenteArco(u: number, retroceso = 2.3): number {
  return retroceso * EXPO_ARCO * Math.pow(Math.abs(u), EXPO_ARCO - 1) * Math.sign(u);
}

/** Los dientes de un arco. Devuelve los laterales (premolares y molares),
 *  que en la vista de lado tapan la lengua y se esconden. */
function arcoDental(grupo: THREE.Group, y: number, alto: number, mat: THREE.Material): THREE.Mesh[] {
  const posiciones = [-0.92, -0.76, -0.6, -0.44, -0.28, -0.1, 0.1, 0.28, 0.44, 0.6, 0.76, 0.92];
  const laterales: THREE.Mesh[] = [];
  for (const u of posiciones) {
    const p = arco(u);
    const incisivo = Math.abs(u) < 0.3;
    const w = incisivo ? 0.34 : 0.4, d = incisivo ? 0.24 : 0.36;
    const diente = new THREE.Mesh(new THREE.BoxGeometry(d, alto, w), mat);
    diente.position.set(p.x, y, p.y);
    diente.rotation.y = -Math.atan2(tangenteArco(u), ANCHO / 2);   // mirando a la tangente de la arcada
    grupo.add(diente);
    if (!incisivo) laterales.push(diente);
  }
  return laterales;
}

/** El aire por la boca: de la garganta, sobre la lengua, sale entre los labios. */
function geometriaAireOral(): THREE.BufferGeometry {
  const curva = new THREE.CatmullRomCurve3([
    new THREE.Vector3(2.55, -1.9, 0), new THREE.Vector3(2.5, -0.7, 0), new THREE.Vector3(1.6, 0.35, 0),
    new THREE.Vector3(0.0, 0.6, 0), new THREE.Vector3(-1.6, 0.35, 0), new THREE.Vector3(-3.6, 0.1, 0),
  ]);
  return new THREE.TubeGeometry(curva, 40, 0.09, 8, false);
}

/** El aire nasal: de la faringe, por detrás del velo, sube a la nariz y sale.
 *  `salida` (v5): la ventana de la nariz de la cabeza cargada, si la declara
 *  (`nariz_salida` en los extras del GLB); la del escaneo está más alta que
 *  la de MakeHuman y el hilo salía por el labio de arriba. */
function geometriaAireNasal(salida: [number, number] = [-3.0, 1.95]): THREE.BufferGeometry {
  const curva = new THREE.CatmullRomCurve3([
    new THREE.Vector3(2.6, -0.6, 0), new THREE.Vector3(2.7, 0.6, 0), new THREE.Vector3(2.6, 1.7, 0),
    new THREE.Vector3(1.5, 2.05, 0), new THREE.Vector3(-1.0, (2.05 + salida[1]) / 2, 0), new THREE.Vector3(salida[0], salida[1], 0),
  ]);
  return new THREE.TubeGeometry(curva, 40, 0.09, 8, false);
}

function tuboArco(y: number, radio: number, mat: THREE.Material, retroceso = 2.3): THREE.Mesh {
  const puntos: THREE.Vector3[] = [];
  for (let u = -1; u <= 1.0001; u += 0.1) {
    const p = arco(u, retroceso);
    puntos.push(new THREE.Vector3(p.x, y, p.y));
  }
  const curva = new THREE.CatmullRomCurve3(puntos);
  return new THREE.Mesh(new THREE.TubeGeometry(curva, 32, radio, 10, false), mat);
}

/** Un labio: un tubo que sigue el arco de la boca, con las comisuras hacia
 *  atrás. `largo` es la distancia entre comisuras; los labios redondeados son
 *  cortos y salen hacia delante, los estirados, largos y planos. */
function geometriaLabio(largo: number, radio: number): THREE.BufferGeometry {
  const z = largo / 2;
  const atras = 0.45 + 0.3 * Math.max(0, z - 0.6);      // cuanto más ancho, más atrás la comisura
  const puntos = [
    new THREE.Vector3(atras, -0.04, -z), new THREE.Vector3(atras * 0.35, 0, -z * 0.62),
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(atras * 0.35, 0, z * 0.62), new THREE.Vector3(atras, -0.04, z),
  ];
  const curva = new THREE.CatmullRomCurve3(puntos, false, 'centripetal', 0.5);
  return new THREE.TubeGeometry(curva, 24, radio, 10, false);
}

/** La mejilla: una lámina translúcida en el lado de la cámara, con las
 *  esquinas redondeadas, para que la cabeza tenga un lado sin tapar nada. */
function geometriaMejilla(): THREE.BufferGeometry {
  // Sigue el perfil de la cara modelada (tools/boca3d_blender/cara.py): el
  // puente de la nariz y el techo nasal por arriba, la faringe por detrás, el
  // mentón por debajo y, delante, se queda detrás de las comisuras y de la
  // nariz, que sobresalen. Sin cara modelada también cierra bien las piezas
  // simples.
  const f = new THREE.Shape();
  f.moveTo(-2.35, 0.95);                              // bajo la nariz, detrás de los labios
  f.quadraticCurveTo(-2.55, 2.1, -2.35, 3.05);        // el lateral de la nariz, hasta el puente
  f.quadraticCurveTo(-0.6, 3.0, 1.8, 2.75);           // el techo nasal
  f.quadraticCurveTo(3.0, 2.5, 3.1, 1.5);             // la nasofaringe
  f.quadraticCurveTo(3.25, -0.6, 2.85, -2.3);         // la pared de la faringe
  f.quadraticCurveTo(2.7, -2.75, 2.0, -2.45);         // la garganta
  f.quadraticCurveTo(0.5, -2.4, -0.8, -2.35);         // debajo del mentón
  f.quadraticCurveTo(-2.4, -2.2, -2.85, -1.2);        // el mentón
  f.quadraticCurveTo(-3.0, -0.6, -2.55, -0.15);       // el surco bajo el labio
  f.quadraticCurveTo(-2.35, 0.3, -2.35, 0.95);        // detrás de las comisuras
  const g = new THREE.ExtrudeGeometry(f, { depth: 0.05, bevelEnabled: false });
  return g;
}

/** La piel de la media cabeza (cara.py) con los pesos con que cada vértice
 *  sigue el giro de la mandíbula: 1 en la barbilla y bajo el maxilar (también
 *  en el lado lejano: la mandíbula es rígida), 0 por encima de la línea de la
 *  boca y hacia la nuca. */
interface PielDeformable {
  geometria: THREE.BufferGeometry;
  reposo: Float32Array;
  pesos: Float32Array;
  /** v6 (escaneo): cuánto de `pesos` es labio que se retrasa respecto al hueso
   *  (1 junto a la ranura, 0 en la barbilla). El peso efectivo es
   *  `pesos - retraso * (1 - k(mandíbula))`, con k = 0,2 en reposo y 1 en las vocales (v7). */
  retraso: Float32Array;
  seguimientoMaximo?: number;
  ultimoGiro: number;
}

const suave01 = (t: number) => { const s = Math.min(1, Math.max(0, t)); return s * s * (3 - 2 * s); };

export function pielQueSigueLaMandibula(geometria: THREE.BufferGeometry, labiosEnPiel = false, ranuraSeca = false, bordeRegular = false): PielDeformable {
  const pos = geometria.getAttribute('position') as THREE.BufferAttribute;
  const rig = bordeRegular ? geometria.getAttribute('uv1') : null;
  const reposo = new Float32Array(pos.array as Float32Array);
  const pesos = new Float32Array(pos.count);
  const retraso = new Float32Array(pos.count);
  for (let i = 0; i < pos.count; i++) {
    const x = reposo[3 * i], y = reposo[3 * i + 1], z = reposo[3 * i + 2];
    // Solo dos rampas, las dos en el plano del giro: la vertical estira la
    // piel entre la boca y la barbilla, y la de delante-atrás muere hacia el
    // pivote, donde el giro ya mueve poco. Una rampa en z (lado lejano
    // quieto) plegaba los anillos de la piel al abrir y dejaba un rasgón.
    let bajo = suave01((0.45 - y) / 1.35);            // de la línea de la boca (0,45) a la barbilla (-0,9)
    if (labiosEnPiel) {
      // Con los labios en la piel (MakeHuman), por delante el corte es seco
      // en la línea de la boca: el labio de abajo entero va con la mandíbula
      // y el de arriba se queda; los labios son una ranura, así que no se
      // rasga nada. Hacia las mejillas vuelve la rampa suave.
      const frente = suave01((-1.6 - x) / 0.8) * (1 - suave01((Math.abs(z) - 0.85) / 0.5));   // no en las comisuras
      // D4.4b v5: la cabeza escaneada trae los labios sellados y cara.py les
      // abre una ranura en y = 0,15 con los dos lados separados 0,012: el
      // corte va justo ahí, seco, para que cada labio caiga entero de su lado.
      // La topología regular ya tiene un borde exacto. Suavizarlo como el
      // escaneo haría que mucosa y base viajaran a velocidades distintas.
      const suavidad=rig?.getX(i) ?? 0;
      const seco = bordeRegular ? (suavidad>0 ? suave01((.15-y)/suavidad) : Number(y < .15 - 1e-6)) : suave01((0.15 - y) / 0.02);
      // D4.4b v7: por encima de la ranura el labio de arriba SUBE con la
      // apertura (peso negativo, −0,22 en su bermellón): el borde incisal
      // superior está 7 mm por encima de la línea de contacto y sin esto los
      // dientes de arriba no se veían nunca. Misma fórmula que
      // `peso_labio_inferior_lps` en cara.py.
      const arriba = (bordeRegular ? (suavidad>0 ? suave01((y-.15)/suavidad) : Number(y > .15 + 1e-6)) : suave01((y - 0.15) / 0.02)) * (1 - suave01((y - 0.55) / 0.25));
      // El piloto ya eleva el superior con morfos propios; conservar el
      // arrastre viejo completo lo plegaba al abrir mucho la mandíbula.
      const bajoLabio = ranuraSeca ? seco - (bordeRegular ? 0.03 : 0.22) * arriba : suave01((0.2 - y) / 0.1);
      bajo = bajo + (bajoLabio - bajo) * frente;
      // D4.4b v6: bajo la ranura el labio se RETRASA respecto al hueso (sigue
      // un 20 % en reposo y un 60 % en las vocales, `deformarPiel`), y el
      // retraso muere linealmente hacia la barbilla (-1,2), que va con el
      // hueso: el giro de reposo (1 cm en los labios) se reparte como un
      // estirón uniforme en vez de rasgar el bermellón (la «herida» de v5).
      // Misma fórmula que `peso_labio_inferior_lps` en cara.py.
      if (ranuraSeca) retraso[i] = frente * seco * Math.min(1, Math.max(0, (y + 1.2) / 1.35));
    }
    const delante = suave01((2.3 - x) / 0.9);         // la garganta y la nuca se quedan
    pesos[i] = bajo * delante;
    retraso[i] *= delante;
    // Raíz del corte labial: el bermellón es flexible, su inserción sigue
    // el maxilar fijo (-1) o la mandíbula rígida (-2). Los modelos anteriores
    // usan valores >=0 y conservan el campo de piel habitual.
    const ancla = rig?.getX(i) ?? 0;
    if (ancla === -1 || ancla === -2) {
      pesos[i] = ancla === -2 ? 1 : 0;
      retraso[i] = 0;
    }
  }
  return { geometria, reposo, pesos, retraso, seguimientoMaximo: bordeRegular ? .80 : 1, ultimoGiro: NaN };
}

/** Gira cada vértice alrededor del pivote de la mandíbula por su peso. */
function deformarPiel(piel: PielDeformable, giro: number): void {
  if (giro === piel.ultimoGiro) return;
  piel.ultimoGiro = giro;
  const pos = piel.geometria.getAttribute('position') as THREE.BufferAttribute;
  const salida = pos.array as Float32Array;
  const { reposo, pesos, retraso } = piel;
  // v6: k(mandíbula): 0,2 hasta la mandíbula de reposo (0,2); v7: 1 desde
  // 0,5 (con 0,6 los incisivos de abajo quedaban siempre detrás del labio y
  // con 0,9 asomaban 1,6 mm; con 1, 4,6 mm).
  const k = 0.2 + ((piel.seguimientoMaximo ?? 1)-0.2) * suave01((giro / MAND_MAX - 0.2) / 0.3);
  for (let i = 0; i < pos.count; i++) {
    const w = pesos[i] - retraso[i] * (1 - k);
    const x = reposo[3 * i], y = reposo[3 * i + 1];
    // v7: el peso puede ser NEGATIVO (el labio de arriba sube al abrir).
    if (w === 0) { salida[3 * i] = x; salida[3 * i + 1] = y; continue; }
    const a = giro * w, c = Math.cos(a), s = Math.sin(a);
    const dx = x - PIVOTE_MAND.x, dy = y - PIVOTE_MAND.y;
    salida[3 * i] = PIVOTE_MAND.x + dx * c - dy * s;
    salida[3 * i + 1] = PIVOTE_MAND.y + dx * s + dy * c;
  }
  pos.needsUpdate = true;
  piel.geometria.computeVertexNormals();
  {
    const normales = piel.geometria.getAttribute('normal');
    for (let i = 0; i < pos.count; i++) if (Math.abs(pos.getZ(i)) < 1e-5) {
      const x = normales.getX(i), y = normales.getY(i), largo = Math.hypot(x, y) || 1;
      normales.setXYZ(i, x / largo, y / largo, 0);
    }
    normales.needsUpdate = true;
  }
}

const MUESTRAS = 56, LADOS = 16;

/** Geometría vacía de la lengua, con el tamaño fijo: se rellena con `deformarLengua`. */
function geometriaLengua(): THREE.BufferGeometry {
  const g = new THREE.BufferGeometry();
  const nVert = (MUESTRAS + 1) * LADOS + 2;
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(nVert * 3), 3));
  const idx: number[] = [];
  for (let i = 0; i < MUESTRAS; i++) {
    for (let j = 0; j < LADOS; j++) {
      const a = i * LADOS + j, b = i * LADOS + (j + 1) % LADOS;
      const c = (i + 1) * LADOS + j, d = (i + 1) * LADOS + (j + 1) % LADOS;
      idx.push(a, c, b, b, c, d);
    }
  }
  const raiz = nVert - 2, punta = nVert - 1;
  for (let j = 0; j < LADOS; j++) {
    idx.push(raiz, j, (j + 1) % LADOS);
    const base = MUESTRAS * LADOS;
    idx.push(punta, base + (j + 1) % LADOS, base + j);
  }
  g.setIndex(idx);
  return g;
}

function deformarLengua(g: THREE.BufferGeometry, n: PoseNumerica): void {
  const nudos: THREE.Vector3[] = [];
  for (let i = 0; i < N_NUDOS; i++) nudos.push(new THREE.Vector3(n[I_NUDOS + 2 * i], n[I_NUDOS + 2 * i + 1], 0));
  const curva = new THREE.CatmullRomCurve3(nudos, false, 'centripetal', 0.5);
  const pos = g.getAttribute('position') as THREE.BufferAttribute;
  const lateral = new THREE.Vector3(0, 0, 1);
  const p = new THREE.Vector3(), t = new THREE.Vector3(), normal = new THREE.Vector3();
  const radioEn = (u: number, k: 0 | 1) => {
    const s = u * (N_NUDOS - 1), i = Math.min(N_NUDOS - 2, Math.floor(s)), f = s - i;
    const r = RADIOS[i][k] + (RADIOS[i + 1][k] - RADIOS[i][k]) * f;
    // La punta se afina para cerrar el tubo con un casquete suave; la raíz
    // acaba plana, escondida bajo el suelo de la boca.
    const borde = Math.min(1, (1 - u) * 8);
    return r * Math.sqrt(borde);
  };
  for (let i = 0; i <= MUESTRAS; i++) {
    const u = i / MUESTRAS;
    curva.getPoint(u, p);
    curva.getTangent(u, t);
    normal.crossVectors(lateral, t).normalize();   // perpendicular en el plano sagital
    const rz = radioEn(u, 0), ry = radioEn(u, 1);
    for (let j = 0; j < LADOS; j++) {
      const a = (j / LADOS) * Math.PI * 2;
      const k = i * LADOS + j;
      pos.setXYZ(k,
        p.x + normal.x * ry * Math.cos(a) + lateral.x * rz * Math.sin(a),
        p.y + normal.y * ry * Math.cos(a) + lateral.y * rz * Math.sin(a),
        p.z + normal.z * ry * Math.cos(a) + lateral.z * rz * Math.sin(a));
    }
  }
  const nVert = (MUESTRAS + 1) * LADOS + 2;
  curva.getPoint(0, p); pos.setXYZ(nVert - 2, p.x, p.y, p.z);
  curva.getPoint(1, p); pos.setXYZ(nVert - 1, p.x, p.y, p.z);
  pos.needsUpdate = true;
  g.computeVertexNormals();
  g.computeBoundingSphere();
}

// --- La escena ---------------------------------------------------------------

export interface OpcionesEscena {
  /** Piloto optativo: exterior didáctico y exploración horizontal de 360°. */
  exploracionDidactica?: boolean;
  colores?: Partial<Colores>;
  reducirMovimiento?: boolean;
  /** La mejilla translúcida del lado de la cámara (por defecto, sí). */
  mejilla?: boolean;
  /** Sombras de contacto de la luz principal (por defecto, sí). La guarda
   *  de fluidez las apaga sola si el aparato no llega a 30 cuadros por segundo. */
  sombras?: boolean;
  /** La guarda de fluidez (por defecto, sí): mide dos segundos y apaga
   *  sombras y luego la mejilla si no llega a 30 cuadros por segundo. */
  guarda?: boolean;
  /** Reflejos de un entorno neutro precalculado (por defecto, sí). */
  entorno?: boolean;
  /** v5: mientras la boca se mueve, el lienzo se pinta a un pixel ratio
   *  menor (1,25 como mucho) y vuelve al nativo al pararse: el coste por
   *  píxel manda en el móvil y en movimiento el ojo no distingue la mitad
   *  de resolución. Por defecto, sí. */
  menosPixelesEnMovimiento?: boolean;
  /** URL de una lengua modelada en Blender (.glb con las shape keys de
   *  `MORFOS_LENGUA`): sustituye al tubo cuando carga. */
  lenguaGlb?: string;
  /** Labios y perfil seccionado de Blender; conserva las piezas simples si falla. */
  caraGlb?: string;
  /** Los modelos pedidos ya cargaron o fallaron y la composicion visible es
   *  definitiva. Evita enseñar como estado final el respaldo transitorio. */
  alPreparar?: () => void;
  /** El navegador perdió el contexto WebGL (móvil con poca memoria, GPU reiniciada):
   *  quien integra cae al corte 2D en vez de dejar el lienzo en blanco. */
  alPerderContexto?: () => void;
}

export class EscenaBoca {
  /** Segundo encuadre del mismo gesto; no tiene una animación independiente. */
  /** v8: 22° (antes 32): el recuadro se ciñe a la boca y deja fuera el borde
   *  del escaneo bajo el mentón, que en el móvil parecía una segunda boca. */
  private readonly camaraLabios = new THREE.PerspectiveCamera(22, 1.25, 0.1, 60);
  /** D4.4b v4: el detalle frontal se pinta en una textura pequeña (0,6 de la
   *  resolución del recuadro, MSAA ×2) y solo cada tres cuadros mientras hay movimiento;
   *  en el canvas se copia con un plano, que cuesta nada. Con la pasada
   *  completa a resolución entera el recuadro se llevaba un 26 % de los fps. */
  /** v8: la piel del escaneo y su material liso para el recuadro. */
  private readonly pielesNeutras: { malla: THREE.Mesh; neutro: THREE.Material | null }[] = [];
  private texturaLisaActual: THREE.Texture | null = null;
  private detalle: { rt: THREE.WebGLRenderTarget; escena: THREE.Scene; camara: THREE.OrthographicCamera; material: THREE.MeshBasicMaterial } | null = null;
  private detalleCuadro = 0;
  /** Decisión de Miguel (23 sep 2026): solo el corte lateral, sin recuadro frontal. */
  private readonly detalleFrontalActivo = false;
  private pixelRatioNativo = 1;
  private menosPixelesEnMovimiento = true;
  private pixelRatioBajo = false;
  private detalleListo = false;
  private lucesEnDetalle = false;
  private static webgl: boolean | null = null;
  /** El renderer que reutilizan los visores sucesivos (ver el constructor). */
  private static compartido: THREE.WebGLRenderer | null = null;

  private static nuevoRenderer(): THREE.WebGLRenderer {
    return new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
  }

  /** Hay WebGL en este navegador (o en este entorno de pruebas). Se prueba una
   *  vez por página y el contexto de prueba se suelta: antes cada apertura del
   *  visor abría uno más, 20 contextos en diez aperturas (auditoría de 4e, ronda 2). */
  static hayWebGL(): boolean {
    if (EscenaBoca.webgl !== null) return EscenaBoca.webgl;
    try {
      const c = document.createElement('canvas');
      const gl = (c.getContext('webgl2') || c.getContext('webgl')) as WebGLRenderingContext | null;
      gl?.getExtension('WEBGL_lose_context')?.loseContext();
      EscenaBoca.webgl = !!gl;
    } catch {
      EscenaBoca.webgl = false;
    }
    return EscenaBoca.webgl;
  }

  readonly canvas: HTMLCanvasElement;
  private readonly renderer: THREE.WebGLRenderer;
  private readonly escena = new THREE.Scene();
  private readonly camara: THREE.PerspectiveCamera;
  private readonly controles: OrbitControls;
  /** La raíz donde OrbitControls colgó su keydown al construir (ver el constructor). */
  private readonly raiz: Node;
  /** Renderer creado solo para este visor (ya había otro abierto): se suelta entero al cerrar. */
  private readonly propio: boolean;
  /** Escuchador de `webglcontextlost` del lienzo, para quitarlo al cerrar. */
  private readonly alPerder: (e: Event) => void;
  private readonly mandibula = new THREE.Group();
  private readonly velo = new THREE.Group();
  private readonly labioSup: THREE.Mesh;
  private readonly labioInf: THREE.Mesh;
  private readonly lengua: THREE.Mesh;
  private readonly mejilla: THREE.Mesh;
  private readonly aireNasal: THREE.Mesh;
  private readonly aireOral: THREE.Mesh;
  /** D4.2: marcador discreto del punto de contacto real (aro `_TOCA` del 2D,
   *  en 3D). Misma familia de material que aireOral/aireNasal: una malla
   *  minúscula, transparente y sin sombra, no una capa nueva cara. */
  private readonly marcaContacto: THREE.Mesh;
  /** D4.3b: pulso discreto de vibración (glotal, no toda la cabeza) para
   *  sonidos sonoros. Se enciende/apaga con la pose (como los demás) y,
   *  mientras está encendido, también respira con el reloj (`bucle()`),
   *  ritmo fijo aparte del ciclo del sonido -- igual que `-fluir` en 2D. */
  private readonly marcaVibracion: THREE.Mesh;
  /** D4.3c: las caras del corte y la pared del fondo -- lo que revela que
   *  esto es un corte sagital, no una cara entera -- se esconden en
   *  bilabial Y labiodental. No incluye `cabeza_lejana`, ojo/iris ni
   *  nariz/mentón: dan contexto de cara y no compiten con los labios. */
  private readonly piezasCorte: THREE.Object3D[] = [];
  /** Dientes/encía/mandíbula modelados por arco. D4.4a los etiqueta además
   *  por soporte/incisivo/posterior para aplicar el perfil de cada familia. */
  private readonly piezasDentalesInferiores: THREE.Object3D[] = [];
  private readonly piezasDentalesSuperiores: THREE.Object3D[] = [];
  /** Si cargaron los dientes/encías modelados (D4.3c): entonces
   *  `vistaExterior()` no toca `dentalSimple`, que ya se dejó escondido. */
  private dentalesModelados = false;
  /** Si la pose activa es sonora: `bucle()` solo pulsa (y sigue pintando)
   *  cuando esto es cierto. */
  private sonoroActivo = false;
  /** Las piezas que van dentro de la mandíbula, en coordenadas del mundo con la boca cerrada. */
  private readonly dentroMandibula: THREE.Group;
  /** La lengua modelada (si se pidió y ya cargó) y sus morfos por índice. */
  private lenguaGlb: THREE.Mesh | null = null;
  private seccionLingual: ReturnType<typeof seccionSagitalLengua> = null;
  private indicesMorfos: (number | undefined)[] = [];
  private caraModelada = false;
  /** La cabeza de MakeHuman (entera, con sus labios): encuadre más lejano. */
  private cabezaEntera = false;
  private readonly cavidadesSimples: THREE.Mesh[] = [];
  private readonly dentalSimple: THREE.Object3D[] = [];
  private readonly sueloSimple: THREE.Mesh;
  /** Premolares y molares: se esconden los del lado de la cámara en la vista de lado. */
  private readonly dientesLaterales: THREE.Mesh[] = [];
  private lateralesOcultos: 'ninguno' | 'z+' | 'z-' = 'ninguno';
  private readonly sombras: boolean;
  /** Las pieles de la media cabeza: siguen a la mandíbula por pesos. */
  private readonly pielesDeformables: PielDeformable[] = [];
  /** Las pieles con shape keys de labios (cabeza de MakeHuman). */
  readonly pielesConLabios: THREE.Mesh[] = [];
  private readonly luzPrincipal: THREE.DirectionalLight;
  private readonly papilas: THREE.Texture | null;
  private readonly hueso: THREE.Texture | null;
  private readonly guarda = { midiendo: true, t0: 0, calentando: 0, cuadros: 0, fps: null as number | null, etapa: 0 };
  private readonly observador: ResizeObserver | null = null;
  private actual: PoseNumerica;
  private desde: PoseNumerica | null = null;
  private hacia: PoseNumerica | null = null;
  /** Lote fase 3: dentro del soplo de una sorda la vibración espera (VOT). */
  private vozRetenida = false;
  /** v7: los globos oculares del escaneo (`ojo_*` en cara.glb), si los trae. */
  private ojos: THREE.Mesh[] = [];
  /** v7: el fondo oscuro de la boca en el recuadro (solo capa 1). */
  private interiorBoca: THREE.Mesh | null = null;
  private t0 = 0;
  private duracion = 0;
  /** La línea de tiempo en marcha (ciclo de un sonido o palabra entera). */
  private linea: { claves: { t: number; n: PoseNumerica }[]; total: number; aspiracion?: { en: number; dura: number }[] } | null = null;
  private lineaT0 = 0;
  /** Giro de cámara (radianes de azimut) que acompaña a la línea: sube a
   *  mitad del ciclo y vuelve al final. Negativo mira hacia la cara. */
  private giroLinea = 0;
  private giroBase = { azimut: 0, polar: 1.49, distancia: 13 };
  /** D4.2: zoom del preset activo (multiplica `distanciaEncuadre()`); se
   *  conserva al redimensionar (`redimensionar()` lo aplica también) y al
   *  terminar de cargar `cara.glb` (D4.2.1: antes se perdía ahí). */
  private zoomActual = 1;
  /** D4.2.1: target del preset activo, o `null` para el comportamiento
   *  heredado (`objetivoActual()`). */
  private targetFamilia: readonly [number, number] | null = null;
  /** La familia con la vista puesta ahora: `restablecerVista()` vuelve a ESA,
   *  no a un azimut fijo universal. */
  private familiaActual: Familia = 'vocal';
  private perfilDentalActual: PerfilDental = 'completa';
  /** Lo que pide quien integra (input `mejilla`, pensado para rendimiento) y
   *  lo que permite el preset de la familia activa (pensado para pedagogía):
   *  la mejilla solo se ve si las dos lo permiten. */
  private mejillaExterna = true;
  private mejillaFamilia = true;
  private arrastrando = false;
  private sucio = true;
  private vivo = true;
  private rafId = 0;
  private libre = false;
  private readonly exploracionDidactica: boolean;
  private corteDidactico = false;
  private actualizarNormalesPiel: (() => void) | null = null;
  private actualizarNormalesLengua: (() => void) | null = null;
  reducirMovimiento: boolean;

  constructor(private readonly contenedor: HTMLElement, opciones: OpcionesEscena = {}) {
    this.exploracionDidactica = opciones.exploracionDidactica === true;
    contenedor.dataset['lengua'] = 'geometrico';
    contenedor.dataset['cara'] = 'geometrico';
    const col = { ...COLORES_POR_DEFECTO };
    for (const [nombre, valor] of Object.entries(opciones.colores ?? {})) {
      if (valor) col[nombre as keyof Colores] = valor;
    }
    this.reducirMovimiento = !!opciones.reducirMovimiento;

    // Un solo renderer para todos los visores que se abren y cierran: cada uno nuevo
    // dejaba un contexto WebGL retenido por una textura de módulo de three (20 contextos
    // perdidos tras 20 aperturas, medido). Solo si ya hay otro visor abierto se crea uno propio.
    const previo = EscenaBoca.compartido;
    const ocupado = !!previo?.domElement.isConnected;
    const libre = previo && !ocupado && !previo.getContext().isContextLost() ? previo : null;
    this.propio = ocupado;
    this.renderer = libre ?? EscenaBoca.nuevoRenderer();
    if (!this.propio) EscenaBoca.compartido = this.renderer;
    this.pixelRatioNativo = Math.min(window.devicePixelRatio || 1, 2);
    this.menosPixelesEnMovimiento = opciones.menosPixelesEnMovimiento ?? true;
    this.renderer.setPixelRatio(this.pixelRatioNativo);
    // Tono fotográfico (ACES): los brillos del barniz húmedo no se queman.
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.sombras = opciones.sombras !== false;
    this.guarda.midiendo = opciones.guarda !== false;
    // Con el renderer reutilizado, la guarda de fluidez de un visor anterior pudo apagarlas.
    this.renderer.shadowMap.enabled = this.sombras;
    if (this.sombras) {
      // PCFSoftShadowMap ya no existe en three 0.186 (avisaba «has been removed» en
      // consola y caía a PCF): PCF con `shadow.radius` (6, en la luz principal) da la suavidad.
      this.renderer.shadowMap.type = THREE.PCFShadowMap;
    }
    this.canvas = this.renderer.domElement;
    // Perder el contexto dejaba el lienzo en blanco: se avisa a quien integra, que cae al 2D.
    this.alPerder = (e: Event) => { e.preventDefault(); opciones.alPerderContexto?.(); };
    this.canvas.addEventListener('webglcontextlost', this.alPerder);
    this.canvas.style.display = 'block';
    this.canvas.style.width = '100%';
    this.canvas.style.height = '100%';
    // Fondo neutro con viñeta suave, como un fondo de estudio: el lienzo es
    // transparente, así que va en el propio elemento y vale en la app y en la demo.
    this.canvas.style.background = 'radial-gradient(ellipse at 50% 42%, #f8f4f0 0%, #ede7e2 52%, #d6cec7 100%)';
    contenedor.appendChild(this.canvas);

    this.camara = new THREE.PerspectiveCamera(32, 1, 0.1, 60);
    this.camara.position.set(0.3, 0.9, 10.5);
    this.controles = new OrbitControls(this.camara, this.canvas);
    // OrbitControls cuelga un keydown de `canvas.getRootNode()` (el document) y al
    // soltarse vuelve a pedirlo; si el visor ya salió del documento, lo quita de otro
    // sitio y el document retiene controles, canvas y escena. Se guarda aquí.
    this.raiz = this.canvas.getRootNode();
    this.controles.target.set(0.1, 0.05, 0);
    this.controles.enableZoom = false;
    this.controles.enablePan = false;
    this.controles.enableDamping = true;
    this.controles.dampingFactor = 0.12;
    this.controles.rotateSpeed = 0.7;
    aplicarLimitesGiro(this.controles);
    this.controles.addEventListener('change', () => { this.sucio = true; });
    // Si el usuario arrastra, el giro automático de la cámara se cancela.
    this.controles.addEventListener('start', () => { this.arrastrando = true; this.giroLinea = 0; });
    this.controles.addEventListener('end', () => { this.arrastrando = false; });
    this.controles.update();
    // OrbitControls pone touch-action: none al conectarse, y eso deja la
    // página sin scroll sobre la boca. Con pan-y el navegador se queda los
    // gestos verticales (scroll) y nos manda pointercancel; los horizontales
    // giran la boca. `girarLibre(true)` captura todo, para quien lo pida.
    this.girarLibre(false);

    // Luz de tres puntos, suave: principal cálida desde arriba y delante (la
    // única que da sombras de contacto), relleno frío desde atrás y abajo,
    // y un contraluz que separa el perfil del fondo. El entorno (una sala
    // neutra precalculada) da los reflejos del barniz húmedo.
    this.escena.add(new THREE.HemisphereLight(0xfff4ea, 0x8a7f86, this.exploracionDidactica ? .75 : 0.55));
    const luz = new THREE.DirectionalLight(0xfff1e4, this.exploracionDidactica ? 2.0 : 1.9);
    this.luzPrincipal = luz;
    luz.position.set(-4.5, 7, 7.5);
    if (this.exploracionDidactica) {
      const frontal = new THREE.DirectionalLight(0xf3f6ff, .35);
      frontal.position.set(-8,1.5,-4); this.escena.add(frontal);
    }
    if (this.sombras) {
      // Sombras suaves de 1024 (la guarda baja a 512 si hace falta), con
      // sesgo por normal alto: en la piel curva de la cabeza el mapa de 512
      // con sesgo bajo dejaba dientes de sierra en la mandíbula y franjas en
      // la mejilla. El encuadre cubre la cabeza entera (x −3,6..5,5, y −2,6..4).
      luz.castShadow = true;
      luz.shadow.mapSize.set(1024, 1024);
      luz.shadow.radius = 6;
      luz.shadow.bias = -0.0004;
      luz.shadow.normalBias = 0.06;
      const s = luz.shadow.camera;
      s.left = -7; s.right = 7; s.top = 7; s.bottom = -7; s.near = 1; s.far = 30;
    }
    this.escena.add(luz);
    const relleno = new THREE.DirectionalLight(0xdfe8ff, this.exploracionDidactica ? .25 : .55);
    relleno.position.set(5, -1, -4);
    this.escena.add(relleno);
    const contraluz = new THREE.DirectionalLight(0xffffff, 0.7);
    contraluz.position.set(2, 4, -8);
    this.escena.add(contraluz);
    // La media cabeza lejana mira al otro lado de la luz principal: un
    // relleno suave desde delante y ese lado para que no quede en sombra.
    const lejano = new THREE.DirectionalLight(0xfff0e6, this.exploracionDidactica ? .25 : .75);
    lejano.position.set(-6, 3, -5);
    this.escena.add(lejano);
    if (opciones.entorno === true) {
      try {
        const pmrem = new THREE.PMREMGenerator(this.renderer);
        this.escena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
        this.escena.environmentIntensity = this.exploracionDidactica ? 0 : 0.45;
        pmrem.dispose();
      } catch { /* sin entorno: las luces bastan */ }
    }

    const mDientes = materialDe('diente', col.dientes);
    const mEncia = materialDe('encia', col.encia);
    const mHueso = materialDe('hueso', col.hueso);
    const mLabios = materialDe('labio', col.labios);

    // Maxilar: paladar, encía con dientes superiores, velo con bisagra, faringe.
    const paladar = new THREE.Mesh(banda(PALADAR, GROSOR_PALADAR, ANCHO), mEncia);
    this.escena.add(paladar);
    const arcoSup = new THREE.Group();
    arcoSup.add(tuboArco(0.98, 0.2, mEncia));
    this.dientesLaterales.push(...arcoDental(arcoSup, 0.7, 0.5, mDientes));
    this.escena.add(arcoSup);
    this.dentalSimple.push(paladar, arcoSup);

    const veloMalla = new THREE.Mesh(new THREE.CapsuleGeometry(GROSOR_PALADAR / 2, LARGO_VELO - GROSOR_PALADAR / 2, 4, 10), materialDe('mucosa', col.velo));
    veloMalla.rotation.z = -Math.PI / 2;                      // la cápsula a lo largo de +x
    veloMalla.position.x = LARGO_VELO / 2;
    const veloAncho = new THREE.Mesh(new THREE.BoxGeometry(LARGO_VELO, GROSOR_PALADAR, ANCHO * 0.7), materialDe('mucosa', col.velo));
    veloAncho.position.x = LARGO_VELO / 2;
    this.velo.add(veloAncho, veloMalla);
    this.velo.position.set(PIVOTE_VELO.x, PIVOTE_VELO.y, 0);
    this.escena.add(this.velo);

    // La pared de la faringe, de la nasofaringe a la garganta.
    const faringe = new THREE.Mesh(new THREE.BoxGeometry(0.3, 5.6, ANCHO), materialDe('mucosa', col.faringe, { transparent: true, opacity: 0.55 }));
    faringe.position.set(FARINGE_X, -0.6, 0);
    this.escena.add(faringe);
    this.cavidadesSimples.push(faringe);
    // Los huecos por donde va el aire, translúcidos para no tapar nada: la
    // cavidad nasal sobre el paladar, la nasofaringe detrás del velo (el velo
    // cerrado la tapa; abierto, comunica) y la garganta bajo la raíz.
    const mHueco = material('#b9c6d6', { transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide });
    const cavidadNasal = new THREE.Mesh(new THREE.BoxGeometry(5.6, 0.75, ANCHO * 0.6), mHueco);
    cavidadNasal.position.set(-0.2, 2.05, 0);
    const nasofaringe = new THREE.Mesh(new THREE.BoxGeometry(0.75, 2.2, ANCHO * 0.6), mHueco);
    nasofaringe.position.set(2.62, 1.1, 0);
    const garganta = new THREE.Mesh(new THREE.BoxGeometry(0.95, 1.9, ANCHO * 0.6), mHueco);
    garganta.position.set(2.5, -2.35, 0);
    for (const h of [cavidadNasal, nasofaringe, garganta]) { h.renderOrder = 3; this.escena.add(h); }
    this.cavidadesSimples.push(cavidadNasal, nasofaringe, garganta);
    // El aire nasal: un hilo azul que solo se ve cuando el velo está bajado.
    this.aireNasal = new THREE.Mesh(geometriaAireNasal(), material('#2f9cc0', {
      transparent: true, opacity: 0, depthWrite: false, emissive: new THREE.Color('#2f9cc0'), emissiveIntensity: 0.4,
    }));
    this.aireNasal.renderOrder = 4;
    this.escena.add(this.aireNasal);
    this.aireOral = new THREE.Mesh(geometriaAireOral(), material('#2f9cc0', {
      transparent: true, opacity: 0, depthWrite: false, emissive: new THREE.Color('#2f9cc0'), emissiveIntensity: 0.4,
    }));
    this.aireOral.renderOrder = 4;
    this.escena.add(this.aireOral);
    this.marcaContacto = new THREE.Mesh(new THREE.SphereGeometry(0.1, 12, 8), material('#2f9cc0', {
      transparent: true, opacity: 0, depthWrite: false, emissive: new THREE.Color('#2f9cc0'), emissiveIntensity: 0.7,
    }));
    this.marcaContacto.renderOrder = 6;
    this.escena.add(this.marcaContacto);
    // D4.3b: el pulso de vibración, junto a la garganta (misma zona que la
    // cavidad `garganta` de arriba): discreto, no toda la cabeza.
    this.marcaVibracion = new THREE.Mesh(new THREE.SphereGeometry(0.14, 12, 8), material('#e39b3a', {
      transparent: true, opacity: 0, depthWrite: false, emissive: new THREE.Color('#e39b3a'), emissiveIntensity: 0.8,
    }));
    this.marcaVibracion.position.set(2.5, -2.0, 0);
    this.marcaVibracion.renderOrder = 6;
    this.escena.add(this.marcaVibracion);

    // Mandíbula: gira en el pivote y arrastra hueso, dientes inferiores y labio
    // inferior. `dentro` deshace el desplazamiento del pivote para que las
    // piezas se coloquen en coordenadas del mundo con la boca cerrada.
    const dentro = new THREE.Group();
    this.dentroMandibula = dentro;
    dentro.position.set(-PIVOTE_MAND.x, -PIVOTE_MAND.y, 0);
    dentro.add(tuboArco(-0.2, 0.2, mEncia));
    dentro.add(tuboArco(-0.62, 0.28, mHueso, 2.6));
    this.dientesLaterales.push(...arcoDental(dentro, 0.1, 0.5, mDientes));
    this.dentalSimple.push(...dentro.children);
    const suelo = new THREE.Mesh(new THREE.BoxGeometry(SUELO.x1 - SUELO.x0, SUELO.grosor, ANCHO * 0.8), mEncia);
    this.sueloSimple = suelo;
    suelo.position.set((SUELO.x0 + SUELO.x1) / 2, SUELO.y, 0);
    dentro.add(suelo);
    this.mandibula.add(dentro);
    this.mandibula.position.set(PIVOTE_MAND.x, PIVOTE_MAND.y, 0);
    this.escena.add(this.mandibula);

    this.labioSup = new THREE.Mesh(geometriaLabio(2.3, 0.3), mLabios);
    this.labioSup.userData = { largo: 2.3, radio: 0.3 };
    this.escena.add(this.labioSup);
    this.labioInf = new THREE.Mesh(geometriaLabio(2.3, 0.3), mLabios);
    this.labioInf.userData = { largo: 2.3, radio: 0.3 };
    this.mandibula.add(this.labioInf);

    this.papilas = texturaPapilas();
    this.hueso = texturaHueso();
    this.lengua = new THREE.Mesh(geometriaLengua(), materialDe('lengua', col.lengua));
    this.lengua.layers.enable(1);                     // v7: también en el recuadro
    this.escena.add(this.lengua);

    // La mejilla del lado de la cámara: translúcida, se pinta la última y no
    // escribe profundidad, así que no tapa nada y da un lado a la cabeza.
    this.mejilla = new THREE.Mesh(geometriaMejilla(), material('#f2cfc9', {
      transparent: true, opacity: 0.14, depthWrite: false, side: THREE.DoubleSide, roughness: 0.9,
    }));
    this.mejilla.position.z = ANCHO / 2 + 0.12;
    this.mejilla.renderOrder = 5;
    this.mejillaExterna = opciones.mejilla !== false;
    this.mejilla.visible = this.mejillaExterna && this.mejillaFamilia;
    this.escena.add(this.mejilla);

    this.actual = poseNumerica(REPOSO);
    this.aplicar(this.actual);
    this.sombrear();
    let modelosPendientes = Number(!!opciones.lenguaGlb) + Number(!!opciones.caraGlb);
    const modeloTerminado = () => {
      modelosPendientes--;
      if (modelosPendientes === 0 && this.vivo) opciones.alPreparar?.();
    };
    if (opciones.lenguaGlb) this.cargarLengua(opciones.lenguaGlb, col.lengua, modeloTerminado);
    if (opciones.caraGlb) this.cargarCara(opciones.caraGlb, col, modeloTerminado);
    if (modelosPendientes === 0) opciones.alPreparar?.();

    if (typeof ResizeObserver !== 'undefined') {
      this.observador = new ResizeObserver(() => this.redimensionar());
      this.observador.observe(contenedor);
    }
    this.redimensionar();
    this.bucle();
  }

  /** Va a la pose con una transición de `duracionS` segundos (0 = de golpe). */
  irA(pose: PoseSonido, duracionS = 0.5): void {
    this.linea = null;
    const objetivo = poseNumerica(pose);
    if (this.reducirMovimiento || duracionS <= 0) {
      this.desde = this.hacia = null;
      this.actual = objetivo;
      this.aplicar(objetivo);
      return;
    }
    this.desde = this.actual;
    this.hacia = objetivo;
    this.duracion = duracionS * 1000;
    this.t0 = performance.now();
    this.sucio = true;
  }

  /** Está a medio camino entre dos poses, o reproduciendo una línea. */
  get enTransicion(): boolean {
    return this.hacia !== null || this.linea !== null;
  }

  /** Reproduce una línea de tiempo (`cicloSonido` o `lineaPalabra`) desde el
   *  principio; al acabar se queda en su última clave. Con reducir movimiento
   *  no se mueve nada: va de golpe a la pose quieta de la línea. */
  reproducir(linea: Linea, opciones: { giro?: number } = {}): void {
    this.desde = this.hacia = null;
    this.giroLinea = 0;
    if (this.reducirMovimiento || linea.claves.length < 2) {
      this.linea = null;
      this.actual = poseNumerica(linea.quieta);
      this.aplicar(this.actual);
      return;
    }
    const claves = linea.claves.map(c => {
      const n = poseNumerica(c.pose);
      return { t: c.t, n: c.hacia ? mezclar(n, poseNumerica(c.hacia), c.f ?? 0.5) : n };
    });
    this.linea = { claves, total: linea.total, aspiracion: linea.aspiracion };
    this.lineaT0 = performance.now();
    // El giro de cámara que acompaña al sonido (labios redondeados o
    // estirados se ven de frente): solo si el usuario no está arrastrando.
    if (opciones.giro && !this.arrastrando && !this.libre) {
      const d = this.camara.position.clone().sub(this.controles.target);
      this.giroBase = { azimut: Math.atan2(d.x, d.z), polar: Math.acos(Math.min(1, Math.max(-1, d.y / d.length()))), distancia: d.length() };
      this.giroLinea = opciones.giro;
    }
    this.sucio = true;
  }

  /** La cámara a un azimut, conservando la altura y la distancia de `giroBase`. */
  private colocarAzimut(azimut: number): void {
    const { polar, distancia } = this.giroBase;
    const o = this.controles.target;
    this.camara.position.set(
      o.x + distancia * Math.sin(polar) * Math.sin(azimut),
      o.y + distancia * Math.cos(polar),
      o.z + distancia * Math.sin(polar) * Math.cos(azimut));
    this.camara.lookAt(o);
  }

  /** Gira la vista `delta` radianes de azimut alrededor de la boca, para el
   *  teclado (flechas izquierda y derecha): antes solo se giraba con el puntero. */
  girar(delta: number): void {
    const o = this.controles.target;
    const dx = this.camara.position.x - o.x, dz = this.camara.position.z - o.z;
    const polar = Math.acos(Math.max(-1, Math.min(1, (this.camara.position.y - o.y) / Math.max(1e-6, this.camara.position.distanceTo(o)))));
    this.giroBase = { ...this.giroBase, azimut: Math.atan2(dx, dz) + delta, polar, distancia: this.camara.position.distanceTo(o) };
    this.colocarAzimut(this.giroBase.azimut);
    this.controles.update();
    this.sucio = true;
  }

  /** Corta la línea en marcha y se queda donde está. */
  detener(): void {
    this.linea = null;
  }

  /** D4.4b v4: el soplo de aspiración de una oclusiva sorda. Tras la
   *  liberación, el aire oral se enciende del todo y se apaga en rampa
   *  durante `dura` (0,55 s a 1×, lo mismo que la ráfaga del 2D). Una
   *  sonora no lo tiene: en /b/ lo que se ve es la vibración, que ya venía
   *  encendida durante el cierre. */
  private soplar(t: number): void {
    const soplo = (this.linea?.aspiracion ?? []).reduce((mejor, a) => {
      const f = (t - a.en) / a.dura;
      return f >= 0 && f < 1 ? Math.max(mejor, 1 - f * f) : mejor;
    }, 0);
    // Lote fase 3: mientras sale el soplo, la vocal siguiente todavía no vibra
    // (eso es el VOT): la marca de vibración espera a que acabe, y el soplo
    // dura más en /k/ que en /t/ y más en /t/ que en /p/.
    this.vozRetenida = soplo > 0;
    if (soplo <= 0) return;
    const mat = this.aireOral.material as THREE.MeshStandardMaterial;
    mat.opacity = Math.max(mat.opacity, 0.85 * soplo);
  }

  private poseDeLinea(t: number): PoseNumerica {
    const { claves } = this.linea!;
    if (t <= claves[0].t) return claves[0].n;
    for (let i = 0; i < claves.length - 1; i++) {
      const a = claves[i], b = claves[i + 1];
      if (t < b.t) {
        const f = b.t > a.t ? (t - a.t) / (b.t - a.t) : 1;
        return mezclarPose(a.n, b.n, f);
      }
    }
    return claves[claves.length - 1].n;
  }

  /** D4.2.1: dónde mira la cámara ahora. El target de `targetFamilia` si el
   *  preset activo define uno; si no (vocal), el punto universal de
   *  siempre, que cambia con la cara/cabeza modelada (comentario de
   *  `vista()` de siempre). Un método, para que ni `vista()` ni la
   *  reconstrucción del target al cargar la cara (`cargarCara`) puedan
   *  desincronizarse entre sí. */
  private objetivoActual(): THREE.Vector2 {
    if (this.targetFamilia) return new THREE.Vector2(this.targetFamilia[0], this.targetFamilia[1]);
    // Con la cara modelada se mira al mismo punto que con la cabeza entera: mirando a la
    // boca (0,1) el perfil se salía por la izquierda y los labios tocaban el borde del
    // lienzo a 390 px (Miguel, 16 sep; auditoria/boca3d_y_frase_2026-09-16.md).
    return new THREE.Vector2(this.cabezaEntera || this.caraModelada ? 0.9 : 0.1, 0.05);
  }

  /** Coloca la cámara: `azimut` 0 mira de lado (la cara a la izquierda),
   *  negativo gira hacia la cara y positivo hacia la nuca; `polar` π/2 es a
   *  la altura de la boca. */
  vista(azimut: number, polar = 1.49, zoom = 1): void {
    this.zoomActual = zoom;
    const distancia = this.distanciaEncuadre() * zoom;
    const o = this.objetivoActual();
    // OrbitControls.reset() llama a update(), pero con amortiguación activa
    // conserva parte de la inercia. Consumirla sin amortiguación antes de
    // colocar el preset evita que Restaurar vuelva a arrastrar la cámara.
    const amortiguar = this.controles.enableDamping;
    this.controles.enableDamping = false;
    this.controles.reset();
    this.controles.enableDamping = amortiguar;
    this.controles.target.set(o.x, o.y, 0);
    this.camara.position.set(
      this.controles.target.x + distancia * Math.sin(polar) * Math.sin(azimut),
      this.controles.target.y + distancia * Math.cos(polar),
      this.controles.target.z + distancia * Math.sin(polar) * Math.cos(azimut));
    this.controles.update();
    this.sucio = true;
  }

  restablecerVista(): void {
    if (this.exploracionDidactica) { this.vistaDidactica(false); return; }
    this.vistaParaFamilia(this.familiaActual);
  }

  /** Una cámara y una animación: vista frontal de labios o corte lateral. */
  vistaDidactica(frente: boolean): void {
    if (!this.exploracionDidactica) return;
    this.corteDidactico = !frente;
    this.targetFamilia = frente ? [-2.8, 0.45] : [0.9, 0.05];
    this.controles.minAzimuthAngle = frente ? -Infinity : -35 * GR;
    this.controles.maxAzimuthAngle = frente ? Infinity : 35 * GR;
    this.controles.minPolarAngle = 0.35;
    this.controles.maxPolarAngle = Math.PI - 0.35;
    // Encuadre de retrato: más distancia con menor campo angular conserva
    // el tamaño de boca y reduce el aumento de la nariz por perspectiva.
    this.camara.fov = frente ? 22 : 32;
    this.camara.updateProjectionMatrix();
    this.vista(frente ? -Math.PI / 2 : 0, frente ? 1.50 : Math.PI / 2, frente ? 0.50 : 1);
    if (frente) this.actualizarNormalesPiel?.();
    this.giroLinea = 0;
  }

  /** D4.2/D4.2.1: la vista pedagógica inicial de una familia articulatoria
   *  (cámara, zoom, target, rango de giro y mejilla). No cambia la pose ni
   *  la anima; quien llama decide cuándo (al elegir un sonido nuevo, o al
   *  restablecer). */
  vistaParaFamilia(familia: Familia): void {
    this.familiaActual = familia;
    const preset = PRESETS_FAMILIA[familia];
    this.targetFamilia = preset.target;
    this.mejillaFamilia = preset.mejilla;
    this.mejilla.visible = this.mejillaExterna && this.mejillaFamilia;
    aplicarLimitesGiro(this.controles, preset.limites);
    this.vista(preset.azimut, POLAR_DEFECTO, preset.zoom);
    this.vistaExterior(preset.exterior, preset.dentadura);
  }

  /** D4.3c (Miguel, 18 sep): "vista exterior" sin tocar geometría ni GLB —
   *  esconde lengua y velo cuando compiten con el gesto labial; caras del
   *  corte y pared del fondo permanecen porque cierran la cavidad. D4.4a
   *  delega la dentadura al perfil semántico independiente: /f v/ conserva
   *  incisivos superiores y /p b/ ninguno. No
   *  ensancha `LIMITES_GIRO`: la media cabeza sigue siendo media cabeza,
   *  solo se deja de mostrar su interior. */
  private vistaExterior(modo: 'ninguna' | 'bilabial' | 'labiodental', perfilDental: PerfilDental): void {
    this.perfilDentalActual = perfilDental;
    const ocultar = modo !== 'ninguna';
    // Solo se toca la geometria que esta realmente activa: si ya cargo el
    // GLB (lengua modelada), el respaldo simple se queda escondido como ya
    // estaba (`cargarLengua` lo esconde al cargar) y no lo reactiva esta vista.
    if (this.lenguaGlb) this.lenguaGlb.visible = !ocultar; else this.lengua.visible = !ocultar;
    this.velo.visible = !ocultar;
    // D4.3c, corregido tras verlo en el navegador: las caras del corte
    // (corte_craneo/nariz/maxilar/mandibula) y la pared del fondo CIERRAN
    // la cavidad -- esconderlas deja huecos reales en la cabeza, no
    // "menos detalle". `piezasCorte` se queda sin usar aquí a propósito:
    // solo se esconden dientes/lengua/velo, piezas sueltas dentro de la
    // cavidad que no cierran nada al desaparecer.
    for (const o of [...this.piezasDentalesInferiores, ...this.piezasDentalesSuperiores]) {
      const grupo = o.userData['grupoDental'] as GrupoDental | undefined;
      const indice = Number(o.userData['indiceDental'] ?? -1);
      o.visible = !!grupo && visibleEnPerfilDental(perfilDental, grupo, indice);
    }
    // Respaldo sin GLB: no hay arco superior/inferior por separado que
    // valga la pena distinguir; se deja como estaba salvo en bilabial.
    if (!this.dentalesModelados) for (const o of this.dentalSimple) o.visible = perfilDental !== 'oculta';
    // Fuerza a `ocultarLaterales()` a recombinar este preset con el lado de
    // cámara. Antes conservaba su caché y Restaurar podía dejar reaparecer
    // molares que estaban ocultos en la misma vista guiada.
    this.lateralesOcultos = 'ninguno';
    this.sucio = true;
  }

  /** D4.2.1 (registro para depuración, solo lo lee quien integra en modo
   *  desarrollo — ver `boca3d.ts`): la familia, el zoom y el target activos
   *  ahora mismo. */
  get diagnostico(): { familia: Familia; zoom: number; target: { x: number; y: number } } {
    return { familia: this.familiaActual, zoom: this.zoomActual, target: { x: this.controles.target.x, y: this.controles.target.y } };
  }

  private distanciaEncuadre(): number {
    // Con la cara modelada el perfil entero no cabe a 13, pero lo que importa
    // es la boca: en el móvil a 16 quedaba pequeña. La nariz y la garganta se
    // ven enteras al girar.
    // 14,5 se calibró para «lo más cerca que cabe sin tocar el borde» en 288x420, pero
    // medido a 390 px el perfil sí tocaba el borde izquierdo: se aleja a 17,5, el mismo
    // valor que ya usaba la cabeza entera (Central, 16 sep).
    return (this.cabezaEntera || this.caraModelada ? 17.5 : 13) * Math.max(1, 1 / this.camara.aspect);
  }

  /** Con `true` el lienzo captura todos los gestos táctiles (también los
   *  verticales); con `false`, solo los horizontales y la página sigue
   *  haciendo scroll. */
  girarLibre(activo: boolean): void {
    this.libre = activo;
    this.controles.enableRotate = activo;
    this.controles.enableZoom = activo;
    this.controles.enablePan = false;
    if (this.exploracionDidactica) {
      this.controles.minAzimuthAngle = -Infinity;
      this.controles.maxAzimuthAngle = Infinity;
      this.controles.minPolarAngle = 0.35;
      this.controles.maxPolarAngle = Math.PI - 0.35;
    }
    this.canvas.style.touchAction = activo ? 'none' : 'pan-y';
    this.controles.update();
    this.sucio = true;
  }

  get giraLibre(): boolean {
    return this.libre;
  }

  /** Lo que pide quien integra (rendimiento/preferencia). El preset de la
   *  familia activa (`vistaParaFamilia`) puede esconderla igualmente si
   *  estorba más de lo que ayuda en esa familia (bilabiales, labiodentales):
   *  se ve solo si las dos partes lo permiten. */
  mostrarMejilla(visible: boolean): void {
    this.mejillaExterna = visible;
    this.mejilla.visible = this.mejillaExterna && this.mejillaFamilia;
    this.sucio = true;
  }

  /** Carga la lengua de Blender y, cuando llega, esconde el tubo. Si falla,
   *  se queda el tubo y no pasa nada. */
  private cargarLengua(url: string, color: string, alTerminar: () => void = () => {}): void {
    cargarGlb(url, gltf => {
      if (!this.vivo) { liberarModelo(gltf.scene); alTerminar(); return; }
      let malla: THREE.Mesh | null = null;
      gltf.scene.traverse(o => {
        if (!malla && o instanceof THREE.Mesh && o.morphTargetInfluences &&
            MORFOS_LENGUA.every(n => Number.isInteger(o.morphTargetDictionary?.[n]))) malla = o;
      });
      if (!malla) { liberarModelo(gltf.scene); alTerminar(); return; }
      const m = malla as THREE.Mesh;
      // Mucosa húmeda con papilas de relieve: el material físico de la
      // lengua más el mapa procedimental (si la malla trae UV).
      (Array.isArray(m.material) ? m.material : [m.material]).forEach(mat => mat.dispose());
      const conUv = !!m.geometry.getAttribute('uv');
      m.material = materialDe('lengua', color, conUv && this.papilas
        ? (this.exploracionDidactica
          ? { bumpMap: this.papilas, bumpScale: .035, roughness: .48, clearcoat: .22, clearcoatRoughness: .32, sheen: 0 }
          : { bumpMap: this.papilas, bumpScale: 0.36, roughnessMap: this.papilas })
        : {});
      if (this.exploracionDidactica) {
        // La normal ya se calcula sobre la combinación real de morfos;
        // no volver a sumar las normales de cada gesto exportadas en glTF.
        delete m.geometry.morphAttributes.normal;
        this.actualizarNormalesLengua = normalesDelGesto(m);
        // El corte ilumina el interior para estudiarlo; desde fuera, el
        // tejido profundo recibe menos luz. Atenuación visual económica,
        // no cambia geometría/contactos ni pretende simular luz volumétrica.
        const cavidad = { value: 0 };
        const material = m.material as THREE.MeshPhysicalMaterial;
        material.onBeforeCompile = shader => {
          shader.uniforms['vistaCavidad'] = cavidad;
          shader.vertexShader = 'varying float profundidadBoca;\n' + shader.vertexShader;
          shader.vertexShader = shader.vertexShader.replace('#include <project_vertex>',
            'profundidadBoca = transformed.x;\n#include <project_vertex>');
          shader.fragmentShader = 'uniform float vistaCavidad;\nvarying float profundidadBoca;\n' + shader.fragmentShader;
          shader.fragmentShader = shader.fragmentShader.replace('#include <color_fragment>',
            `#include <color_fragment>
            float profundidad = smoothstep(-2.9, -0.4, profundidadBoca);
            diffuseColor.rgb *= mix(1.0, 0.78 - 0.45 * profundidad, vistaCavidad);`);
        };
        material.customProgramCacheKey = () => 'lengua-cavidad-didactica-v1';
        const plano = [new THREE.Plane(new THREE.Vector3(0, 0, -1), 0)];
        this.renderer.localClippingEnabled = true;
        m.onBeforeRender = (_r, _s, camara) => {
          cavidad.value = camara.layers.mask === 2 ? 1 : 0;
          material.clippingPlanes = camara.layers.mask === 2 ? null : plano;
        };
        const corte = seccionSagitalLengua(m);
        if (corte) { m.add(corte); this.seccionLingual=corte; }
      }
      const dic = m.morphTargetDictionary ?? {};
      this.indicesMorfos = MORFOS_LENGUA.map(nombre => dic[nombre]);
      this.lenguaGlb = m;
      m.layers.enable(1);                             // v7: la lengua del .glb también en el recuadro
      this.lengua.visible = false;
      // La lengua va sobre el suelo de la boca: baja y gira con la mandíbula
      // (consejo de entrega-4e); el morfo `mandibula` solo añade un poco.
      this.dentroMandibula.add(m);
      this.contenedor.dataset['lengua'] = 'blender';
      liberarModelo(gltf.scene);
      this.sombrear();
      // D4.3c: si la lengua modelada llega después de aplicar la vista
      // exterior, no debe reaparecer (nace visible por defecto).
      const preset = PRESETS_FAMILIA[this.familiaActual];
      this.vistaExterior(preset.exterior, preset.dentadura);
      this.aplicar(this.actual);
      alTerminar();
    }, () => { alTerminar(); /* sin lengua modelada: se queda el tubo */ });
  }

  get tieneLenguaModelada(): boolean {
    return this.lenguaGlb !== null;
  }

  /** Una piel con las shape keys de los labios (fruncir, estirar,
   *  labio_atras de cara.py): se queda con los nombres de la malla cargada
   *  (al clonar la geometría se pierden) y entra en la lista que `aplicar`
   *  mueve desde la pose. */
  private conMorfosDeLabios(pieza: THREE.Mesh, fuente: THREE.Mesh): void {
    if (!fuente.morphTargetDictionary || !('fruncir' in fuente.morphTargetDictionary)) return;
    pieza.updateMorphTargets();
    pieza.morphTargetDictionary = { ...fuente.morphTargetDictionary };
    this.pielesConLabios.push(pieza);
  }

  /** Las piezas opacas dan y reciben sombra; las translúcidas (aire, huecos,
   *  mejilla) no. Se repite al cargar cada modelo. */
  private sombrear(): void {
    if (!this.sombras) return;
    this.escena.traverse(o => {
      if (!(o instanceof THREE.Mesh)) return;
      const opaco = !(Array.isArray(o.material) ? o.material : [o.material]).some(m => m.transparent);
      o.castShadow = opaco;
      o.receiveShadow = opaco && !o.userData['sinSombraRecibida'];
    });
  }

  private cargarCara(url: string, col: Colores, alTerminar: () => void = () => {}): void {
    cargarGlb(url, gltf => {
      const piezas = new Map<string, THREE.Mesh>();
      gltf.scene.updateMatrixWorld(true);
      gltf.scene.traverse(o => { if (o instanceof THREE.Mesh) piezas.set(o.name, o); });
      const interiorDidactico = this.exploracionDidactica && piezas.has('anatomia_paladar');
      const nombres = ['labio_superior', 'labio_inferior', 'techo_nasal', 'faringe', 'garganta', 'suelo_boca'];
      if (!this.vivo || nombres.some(n => !piezas.has(n))) {
        for (const m of piezas.values()) {
          m.geometry.dispose();
          (Array.isArray(m.material) ? m.material : [m.material]).forEach(mat => mat.dispose());
        }
        alTerminar();
        return;
      }
      const materialAnterior = this.labioSup.material;
      for (const [nombre, destino] of [['labio_superior', this.labioSup], ['labio_inferior', this.labioInf]] as const) {
        const fuente = piezas.get(nombre)!;
        destino.geometry.dispose();
        destino.geometry = fuente.geometry.clone().applyMatrix4(fuente.matrixWorld);
        destino.userData['modelado'] = true;
        // Con colores por vértice (bermellón y piel, cara.py) el color base es
        // blanco y lo pone la malla; sin ellos, el color de los labios.
        const conColores = !!destino.geometry.getAttribute('color');
        destino.material = materialDe('labio', conColores ? '#ffffff' : col.labios, conColores ? { vertexColors: true } : {});
        // Las shape keys del labio (fruncir, estirar): el visor las mezcla
        // desde el largo entre comisuras de la pose. Sin ellas, se escala.
        destino.updateMorphTargets();
        // Los nombres de las shape keys viven en la malla cargada (extras
        // targetNames), no en la geometría: sin copiarlos el diccionario queda
        // «0, 1, 2» y el visor caía en el respaldo de escalar (así estuvo
        // desde dffece4 hasta el 14 sep).
        if (fuente.morphTargetDictionary) destino.morphTargetDictionary = { ...fuente.morphTargetDictionary };
        destino.scale.set(1, 1, 1);
      }
      (Array.isArray(materialAnterior) ? materialAnterior : [materialAnterior]).forEach(m => m.dispose());
      for (const nombre of [...nombres.slice(2), ...(piezas.has('nariz') ? ['nariz'] : [])]) {
        if (interiorDidactico && ['techo_nasal', 'faringe', 'suelo_boca'].includes(nombre)) continue;
        const fuente = piezas.get(nombre)!;
        const pieza = new THREE.Mesh(fuente.geometry.clone().applyMatrix4(fuente.matrixWorld),
          nombre === 'nariz' ? materialDe('piel', col.piel) : materialDe('mucosa', col.mucosa));
        (nombre === 'suelo_boca' ? this.dentroMandibula : this.escena).add(pieza);
      }
      // La cabeza de MakeHuman trae sus propios labios en la piel: los tubos
      // se esconden (hasta que la piel tenga sus shape keys, el labio de abajo
      // se mueve con la mandíbula por pesos y el de arriba se queda).
      const marcaLabios = piezas.get('cabeza_lejana')?.userData?.['labios_en_piel'];
      const salidaNariz = piezas.get('cabeza_lejana')?.userData?.['nariz_salida'] as [number, number] | undefined;
      if (Array.isArray(salidaNariz) && salidaNariz.length === 2) {
        this.aireNasal.geometry.dispose();
        this.aireNasal.geometry = geometriaAireNasal(salidaNariz);
      }
      const labiosEnPiel = marcaLabios === 1 || marcaLabios === 2;
      const ranuraSeca = marcaLabios === 2;
      if (labiosEnPiel) {
        this.labioSup.visible = false; this.labioInf.visible = false;
        // Una cabeza entera es más grande que el loft: la cámara se aleja y
        // mira un poco más atrás (el target se recalcula mas abajo, con
        // `objetivoActual()`: si hay un target de familia activo, D4.2.1 no
        // lo pisa aqui), y la piel translúcida se aclara.
        this.cabezaEntera = true;
        (this.mejilla.material as THREE.MeshStandardMaterial).opacity = 0;
      }
      const menton = piezas.get('menton');
      if (menton) this.dentroMandibula.add(new THREE.Mesh(
        menton.geometry.clone().applyMatrix4(menton.matrixWorld), materialDe('piel', col.piel)));
      // La media cabeza (cara.py): piel lejana en dos trozos (el de la
      // mandíbula gira con ella), caras del corte (tejido mate) y pared del
      // fondo de las cavidades. La piel del lado de la cámara sustituye a la
      // lámina de la mejilla, con el mismo material translúcido.
      const cabeza: [string, Tejido | 'corte' | 'pared' | 'ojo' | 'iris', boolean][] = [
        ['cabeza_lejana', 'piel', false],
        ['corte_craneo', 'corte', false], ['corte_nariz', 'corte', false], ['corte_maxilar', 'corte', false],
        ['corte_mandibula', 'corte', true], ['pared_lejana', 'pared', false],
        ['pared_lejana_2', 'pared', false], ['pared_lejana_3', 'pared', false],
        ['ojo_lejano', 'ojo', false], ['iris_lejano', 'iris', false],
        ['ojo_cercano', 'ojo', false], ['iris_cercano', 'iris', false],
        // D4.4b v4: la sección de cada labio en el corte, con las mismas shape
        // keys que la piel (cara.py las evalúa sobre sus vértices): en el
        // corte sagital los labios son dos volúmenes, no dos láminas.
        ['corte_labio_sup', 'labio', false], ['corte_labio_inf', 'labio', true],
      ];
      this.soltarPielesLisas();
      for (const [nombre, tejido, enMandibula] of cabeza) {
        if (interiorDidactico && ['corte_labio_sup', 'corte_labio_inf', 'corte_maxilar', 'corte_mandibula'].includes(nombre)) continue;
        const fuente = piezas.get(nombre);
        if (!fuente) continue;
        // Caras del corte y pared del fondo claras y mates, como el 2D: la
        // lengua es lo único saturado y la cavidad se lee como hueco.
        const geometria = fuente.geometry.clone().applyMatrix4(fuente.matrixWorld);
        // Marfil mate liso (Central, 14 sep): con textura el corte se mezclaba
        // con la cavidad de lado.
        const mat = tejido === 'corte' ? materialDe('hueso', '#f6ece3', { roughness: 0.92, sheen: 0 })
          : tejido === 'pared' ? materialDe('hueso', '#f6ebe4', { roughness: 0.9, sheen: 0, side: THREE.DoubleSide })
          : tejido === 'ojo' ? materialDe('diente', '#f3efea', { roughness: 0.2, clearcoat: 0.9, clearcoatRoughness: 0.1 })
          : tejido === 'iris' ? materialDe('diente', '#4a3427', { roughness: 0.25, clearcoat: 0.9, clearcoatRoughness: 0.1 })
          : tejido === 'labio' ? materialDe('labio', geometria.hasAttribute('color') ? '#ffffff' : col.labios,
            { side: THREE.DoubleSide, vertexColors: geometria.hasAttribute('color') })
          : materialDe('piel', texturasDe(fuente) || geometria.hasAttribute('color') ? '#ffffff' : col.piel,
            { side: THREE.DoubleSide, vertexColors: !texturasDe(fuente) && geometria.hasAttribute('color'), ...texturasDe(fuente) });
        const pieza = new THREE.Mesh(geometria, mat);
        if (interiorDidactico && tejido === 'piel') {
          // El perfil labial antiguo no debe dibujarse por debajo de la
          // sección derivada de los labios aprobados.
          mat.onBeforeCompile = shader => {
            shader.vertexShader = 'varying vec3 puntoAnatomico;\n' + shader.vertexShader;
            shader.vertexShader = shader.vertexShader.replace('#include <project_vertex>',
              'puntoAnatomico = transformed;\n#include <project_vertex>');
            shader.fragmentShader = 'varying vec3 puntoAnatomico;\n' + shader.fragmentShader;
            shader.fragmentShader = shader.fragmentShader.replace('#include <clipping_planes_fragment>',
              '#include <clipping_planes_fragment>\nif(puntoAnatomico.x < -1.8 && puntoAnatomico.y < 1.5) discard;');
          };
          mat.customProgramCacheKey = () => 'piel-corte-anatomico-v1';
        }
        if (tejido === 'piel' || tejido === 'ojo' || tejido === 'iris') pieza.layers.enable(1);
        if (this.exploracionDidactica && piezas.has('exterior_lejana') && tejido === 'piel') pieza.layers.disable(1);
        if (tejido === 'piel' && texturasDe(fuente)) this.pielesNeutras.push({ malla: pieza, neutro: null });
        if (nombre === 'ojo_cercano' || nombre === 'iris_cercano') pieza.layers.set(1);
        (enMandibula ? this.dentroMandibula : this.escena).add(pieza);
        // D4.3c: las caras del corte y la pared del fondo son justo lo que
        // revela que esto es un corte sagital, no una cara entera: se
        // esconden en la vista exterior (bilabiales/labiodentales).
        if (tejido === 'corte' || tejido === 'pared' || tejido === 'labio') this.piezasCorte.push(pieza);
        if (tejido === 'labio') this.conMorfosDeLabios(pieza, fuente);
        // La piel lejana y la pared del fondo siguen a la mandíbula por pesos;
        // si la pared se quedara fija, al abrir asomaría por la piel movida.
        if (nombre === 'cabeza_lejana' || nombre.startsWith('pared_lejana')) this.pielesDeformables.push(pielQueSigueLaMandibula(pieza.geometry, labiosEnPiel, ranuraSeca));
        // El revés de la piel lejana (a dos caras) no recibe sombras: a la
        // sombra de sí misma se veía negro por dentro desde tres cuartos.
        if ((nombre === 'cabeza_lejana' && labiosEnPiel) || tejido === 'pared') pieza.userData['sinSombraRecibida'] = true;
        // Las paredes del fondo tampoco: las caras del corte les echaban
        // encima su sombra y la cavidad salia oscura y con motas (Central:
        // «pared del fondo clara y lisa»).
        if (nombre === 'cabeza_lejana') this.conMorfosDeLabios(pieza, fuente);
      }
      const cercana = piezas.get('cabeza_cercana');
      if (cercana) {
        this.mejilla.geometry.dispose();
        this.mejilla.geometry = cercana.geometry.clone().applyMatrix4(cercana.matrixWorld);
        this.mejilla.position.z = 0;
        (Array.isArray(this.mejilla.material) ? this.mejilla.material : [this.mejilla.material]).forEach(m => m.dispose());
        this.mejilla.material = materialDe('piel', texturasDe(cercana) || this.mejilla.geometry.hasAttribute('color') ? '#ffffff' : col.piel,
          { vertexColors: !texturasDe(cercana) && this.mejilla.geometry.hasAttribute('color'), transparent: true, opacity: 0,
            depthWrite: false, side: THREE.DoubleSide, ...texturasDe(cercana) });
        this.mejilla.layers.enable(1);
        if (this.exploracionDidactica && piezas.has('exterior_cercana')) this.mejilla.layers.disable(1);
        if (texturasDe(cercana)) this.pielesNeutras.push({ malla: this.mejilla, neutro: null });
        // v8: la textura lisa se hace una vez con las dos mitades y cada una
        // lleva su material (la mejilla, a dos caras como en el corte).
        const foto = texturasDe(cercana)?.map;
        if (foto && this.pielesNeutras.length) {
          const lisa = texturaLisa(foto, this.pielesNeutras.map(p => p.malla));
          this.texturaLisaActual = lisa;
          for (const p of this.pielesNeutras) {
            rayaDeLosLabios(p.malla);
            p.neutro = materialPielLisa(lisa, (p.malla.material as THREE.Material).side);
          }
        }
        this.pielesDeformables.push(pielQueSigueLaMandibula(this.mejilla.geometry, labiosEnPiel, ranuraSeca));
        this.conMorfosDeLabios(this.mejilla, cercana);
      }
      if (this.exploracionDidactica) {
        const exteriores = ['exterior_cercana', 'exterior_lejana'].map(n => piezas.get(n)).filter((m): m is THREE.Mesh => !!m);
        if (exteriores.length) {
          const fotografica = exteriores[0].userData['apariencia_fotografica'] === 1;
          const fotografias = fotografica ? texturasDe(exteriores[0]) : null;
          if (fotografias) { delete fotografias.normalMap; delete fotografias.normalScale; }
          const partes = exteriores.map(f => {
            const g = f.geometry.clone().applyMatrix4(f.matrixWorld);
            // La costura de exportación no debe dividir las normales del rostro.
            if (!fotografica) { g.deleteAttribute('normal'); g.deleteAttribute('uv'); } return g;
          });
          const unida = mergeGeometries(partes)!;
          // BufferGeometryUtils no conserva este indicador de los deltas glTF.
          unida.morphTargetsRelative = partes[0].morphTargetsRelative;
          const geometria = mergeVertices(unida, 1e-5);
          partes.forEach(g => g.dispose()); unida.dispose(); if(!fotografica) geometria.computeVertexNormals();
          // UV de reposo: el grano viaja con la piel al deformarse. Sin nuevos
          // archivos descargados; un relieve fino y muy poco profundo.
          const pos = geometria.getAttribute('position');
          const uv = new Float32Array(pos.count * 2);
          for (let i = 0; i < pos.count; i++) { uv[2*i] = .5 + pos.getZ(i)/7; uv[2*i+1] = .5 + pos.getY(i)/9; }
          if (!fotografica) geometria.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
          if (fotografica) {
            // Coordenadas independientes de la deformación CPU: los pliegues
            // finos viajan con el labio sin deslizarse cuando cambia la pose.
            geometria.setAttribute('pielReposo', new THREE.BufferAttribute(new Float32Array(pos.array), 3));
            // La banda móvil toma detalle cutáneo de una zona sin rasgos.
            // Conservar allí la foto de la boca cerrada estiraba su pliegue
            // oscuro en líneas radiales. Labios y resto del rostro conservan
            // su correspondencia fotográfica; el fundido queda en la piel.
            const detalle = new Float32Array(pos.count*3);
            for (let i=0;i<pos.count;i++) {
              const y=pos.getY(i), z=pos.getZ(i);
              const radio=Math.hypot(z/1.8,(y-.15)/(y>.15?1.0:1.1));
              const peso=1-THREE.MathUtils.smoothstep(radio,.75,1.6);
              detalle[3*i]=.33+.055*z; detalle[3*i+1]=.20-.045*(y-.15);
              detalle[3*i+2]=peso*(1-THREE.MathUtils.smoothstep(pos.getX(i),-1.9,-.8));
            }
            geometria.setAttribute('pielDetalle',new THREE.BufferAttribute(detalle,3));
          }
          const grano = fotografica ? texturaPapilas(3800, .4, 1.25, [12, 12]) : texturaPapilas(2200, .5, 1.4, [10, 10]);
          const material = materialDe('piel', '#ffffff', { vertexColors: true,
            side: fotografica ? THREE.FrontSide : THREE.DoubleSide, roughness: fotografica ? .54 : .82,
            ...(fotografica ? { clearcoat: .035, clearcoatRoughness: .65, ior: 1.4, specularIntensity: .65 } : {}),
            ...(fotografias ?? {}), ...(grano ? { bumpMap: grano, bumpScale: fotografica ? .006 : .012 } : {}) });
          material.onBeforeCompile = shader => {
            // El color por vértice conserva la máscara de tejido, pero el
            // albedo del escaneo se ilumina sin volver a teñirlo con ella.
            if (fotografica) shader.fragmentShader = shader.fragmentShader.replace('#include <color_fragment>',
              '// El albedo conserva su luz propia; AO por mitades marcaba la sutura nasal.');
            if (fotografica) {
              shader.vertexShader='attribute vec3 pielDetalle; attribute vec3 pielReposo; varying vec3 vPielDetalle; varying vec3 vPielReposo;\n'+shader.vertexShader;
              shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',
                '#include <begin_vertex>\n vPielDetalle = pielDetalle; vPielReposo = pielReposo;');
              shader.fragmentShader='varying vec3 vPielDetalle; varying vec3 vPielReposo;\n'+shader.fragmentShader;
              shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',
                `#include <map_fragment>
                #if defined(USE_MAP) && defined(USE_COLOR)
                  // glTF convierte el color a lineal. La diferencia absoluta
                  // confundía el superior oscuro con piel y borraba su color.
                  float labioFoto = smoothstep(0.33, 0.57, (vColor.r-vColor.g)/max(0.001,vColor.r+vColor.g));
                  vec3 detallePiel = texture2D(map,vPielDetalle.xy).rgb;
                  diffuseColor.rgb = mix(diffuseColor.rgb,detallePiel,vPielDetalle.z*(1.0-labioFoto));
                  // El borde inferior del mapa contiene una raya clara de la
                  // foto original. Tomar color del bermellón contiguo reduce
                  // estirarla como un contorno pintado al abrir la boca.
                  // Sólo cambia el muestreo de color, nunca el borde del rig.
                  float labioInferior = 1.0-smoothstep(0.145,0.155,vPielReposo.y);
                  vec2 uvLabioInferior = vec2(vMapUv.x,0.467+(vMapUv.y-0.467)*0.75);
                  vec3 colorLabioInferior = texture2D(map,uvLabioInferior).rgb;
                  diffuseColor.rgb = mix(diffuseColor.rgb,colorLabioInferior,labioFoto*labioInferior);
                  // Tono moreno cálido elegido con la referencia autorizada.
                  // Ajuste de reflectancia, no exposición global: dientes,
                  // luz especular y tejido húmedo conservan su respuesta.
                  // El vídeo tiene luz fuerte; esto no es colorimetría medida.
                  float superior = smoothstep(0.15, 0.26, vPielReposo.y);
                  vec3 pigmentoLabio = mix(vec3(0.70,0.73,0.79),vec3(0.51,0.59,0.65),superior);
                  diffuseColor.rgb *= mix(vec3(0.54,0.47,0.42),pigmentoLabio,labioFoto);
                #endif`);
              shader.fragmentShader = shader.fragmentShader.replace('#include <normal_fragment_maps>',
                `#include <normal_fragment_maps>
                #if defined(USE_COLOR) && defined(USE_BUMPMAP)
                  float tejidoLabial = smoothstep(0.33,0.57,(vColor.r-vColor.g)/max(0.001,vColor.r+vColor.g));
                  vec2 planoLabial = vec2(vPielReposo.z, (vPielReposo.y-0.15)*5.2);
                  float anguloLabial = atan(planoLabial.y,planoLabial.x);
                  float radioLabial = length(planoLabial);
                  // Surcos cortos y de profundidad variable: las estrías
                  // radiales continuas parecían rayos pintados al estirar.
                  float pliegue = sin(anguloLabial*87.0 + 1.8*sin(anguloLabial*13.0)
                    + radioLabial*8.0 + 1.3*sin(radioLabial*9.0+anguloLabial*7.0));
                  float tramos = 0.35+0.65*smoothstep(-0.5,0.55,sin(radioLabial*16.0+anguloLabial*9.0));
                  float microLabial = tejidoLabial*(0.0016*pliegue*tramos
                    + 0.00045*sin(anguloLabial*181.0+radioLabial*43.0));
                  normal = perturbNormalArb(-vViewPosition,normal,vec2(dFdx(microLabial),dFdy(microLabial)),faceDirection);
                #endif`);
              // Translucidez de bajo coste inspirada en el ejemplo oficial
              // SubsurfaceScatteringShader. Es una aproximación local; no
              // reemplaza una simulación de dispersión subsuperficial.
              const luces = THREE.ShaderChunk.lights_fragment_begin.replaceAll(
                'RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );',
                `RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
                {
                  vec3 translucida = normalize(directLight.direction + geometryNormal*0.25);
                  float contraLuz = pow(saturate(dot(geometryViewDir,-translucida)),2.0);
                  reflectedLight.directDiffuse += directLight.color * diffuseColor.rgb * vec3(1.0,0.38,0.22) * (0.035*contraLuz);
                }`);
              shader.fragmentShader = shader.fragmentShader.replace('#include <lights_fragment_begin>',luces);
            }
            shader.fragmentShader = shader.fragmentShader.replace('#include <roughnessmap_fragment>',
              `#include <roughnessmap_fragment>
              #ifdef USE_COLOR
                float bermellon = smoothstep(0.33, 0.57, (vColor.r-vColor.g)/max(0.001,vColor.r+vColor.g));
                roughnessFactor = mix(roughnessFactor, 0.38, bermellon);
              #endif`);
          };
          material.customProgramCacheKey = () => fotografica ? 'piel-morena-labio-relieve-v2' : 'piel-didactica-bermellon-v1';
          const pieza = new THREE.Mesh(geometria, material);
          pieza.layers.set(1);
          pieza.userData['sinSombraRecibida'] = true;
          this.escena.add(pieza);
          this.pielesDeformables.push(pielQueSigueLaMandibula(geometria, true, true, true));
          this.conMorfosDeLabios(pieza, exteriores[0]);
          if (fotografica) this.actualizarNormalesPiel = normalesDelGesto(pieza,true);
        }
      }
      if (interiorDidactico) {
        for (const nombre of ['paladar', 'pared', 'suelo', 'velo', 'uvula', 'labio_sup', 'labio_inf', 'maxilar', 'menton', 'alveolo_sup', 'alveolo_inf']) {
          const fuente = piezas.get('anatomia_' + nombre);
          if (!fuente) continue;
          const original = fuente.material as THREE.MeshStandardMaterial;
          const geometria = fuente.geometry.clone().applyMatrix4(fuente.matrixWorld);
          const pieza = new THREE.Mesh(geometria, nombre.startsWith('labio')
            ? new THREE.MeshBasicMaterial({ color: geometria.hasAttribute('color') ? '#ffffff' : '#bc8580',
              vertexColors: geometria.hasAttribute('color'), side: THREE.DoubleSide })
            : materialDe('mucosa', original.color.getStyle(), { roughness: .8, sheen: 0, side: THREE.DoubleSide }));
          if (nombre === 'velo' || nombre === 'uvula') this.velo.add(pieza);
          else if (nombre === 'suelo' || nombre === 'menton' || nombre === 'alveolo_inf') this.dentroMandibula.add(pieza);
          else this.escena.add(pieza);
          if (nombre.startsWith('labio')) {
            this.pielesDeformables.push(pielQueSigueLaMandibula(geometria, true, true, true));
            this.conMorfosDeLabios(pieza, fuente);
          }
          pieza.userData['sinSombraRecibida'] = true;
        }
      }
      // Las aletas y la punta de la nariz, si el .glb las trae: piel, fijas.
      for (const nombre of ['aleta_izq', 'aleta_der', 'punta_nariz']) {
        const fuente = piezas.get(nombre);
        if (fuente) this.escena.add(new THREE.Mesh(
          fuente.geometry.clone().applyMatrix4(fuente.matrixWorld), materialDe('piel', col.piel)));
      }
      // D4.4b v7: los globos oculares del escaneo (esclerótica, iris y pupila
      // por colores de vértice), detrás de los párpados abiertos. El del lado
      // de la cámara solo se ve cuando la piel de ese lado es opaca
      // (`ocultarLaterales`): tras la piel de cristal flotaría una bola blanca.
      // D4.4b v7: un elipsoide oscuro con las caras hacia dentro, SOLO en la
      // capa 1 (el recuadro): tapa el reverso beige de la piel que se veía por
      // la boca abierta y deja delante dientes, encías y lengua. El corte
      // (capa 0) no lo ve.
      if (this.interiorBoca) { this.escena.remove(this.interiorBoca); this.interiorBoca.geometry.dispose(); (this.interiorBoca.material as THREE.Material).dispose(); }
      this.interiorBoca = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16),
        new THREE.MeshStandardMaterial({ color: this.exploracionDidactica ? '#281117' : '#4a1a1e', roughness: 1, metalness: 0, side: THREE.BackSide }));
      // Dentro de la cabeza: el frente en x = −2,4 (tras las tiras de mucosa),
      // el fondo en −1,6 (la barbilla va por debajo) y 1,5 a los lados.
      this.interiorBoca.scale.set(2.6, this.exploracionDidactica ? 2.7 : 2.0, this.exploracionDidactica ? 2.4 : 1.5);
      this.interiorBoca.position.set(0.2, 0.4, 0);
      this.interiorBoca.layers.set(1);
      this.escena.add(this.interiorBoca);
      this.ojos.length = 0;
      for (const nombre of ['ojo_izq', 'ojo_der']) {
        const fuente = piezas.get(nombre);
        if (!fuente) continue;
        const geometria = fuente.geometry.clone().applyMatrix4(fuente.matrixWorld);
        geometria.computeBoundingSphere();
        const ojo = new THREE.Mesh(geometria, materialDe('piel', '#ffffff', { vertexColors: true, roughness: 0.25 }));
        ojo.userData['lateral'] = geometria.boundingSphere?.center.z ?? 0;
        this.ojos.push(ojo);
        this.escena.add(ojo);
      }
      const dientes = Array.from({ length: 12 }, (_, i) => String(i).padStart(2, '0'));
      const papilas = Array.from(piezas.keys()).filter(n => n.startsWith('papila_'));
      const dentales = ['paladar_modelado', 'encia_superior', 'encia_inferior', 'mandibula_modelada',
        ...['encia_borde_sup', 'encia_borde_inf'].filter(n => piezas.has(n)), ...papilas,
        ...dientes.flatMap(i => ['diente_sup_' + i, 'diente_inf_' + i])];
      if (dentales.every(n => piezas.has(n))) {
        this.dentalSimple.forEach(o => { o.visible = false; });
        this.dentalesModelados = true;
        this.dientesLaterales.length = 0;
        for (const nombre of dentales) {
          if (interiorDidactico && nombre === 'paladar_modelado') continue;
          const fuente = piezas.get(nombre)!;
          const inferior = nombre.includes('_inf') || nombre === 'mandibula_modelada';
          const geometria = fuente.geometry.clone();
          // Las encias van lisas: su relieve de papilas costaba cuadros en
          // SwiftShader y a la distancia del visor no se distinguia.
          const pieza = new THREE.Mesh(geometria,
            nombre.startsWith('diente_') ? materialDe('diente', geometria.hasAttribute('color') ? '#ffffff' : col.dientes,
              {vertexColors:geometria.hasAttribute('color'), ...(this.exploracionDidactica
                ? {roughness:.45,clearcoat:.18,sheen:.10} : {roughness:.36,clearcoat:.35})})
              : nombre === 'mandibula_modelada' ? materialDe('hueso', col.hueso)
              : nombre.endsWith('_dentalv2') ? materialDe('encia', '#ffffff', {vertexColors: true, roughness: .4, clearcoat: .28, sheen: 0})
              : materialDe('encia', col.encia));
          fuente.matrixWorld.decompose(pieza.position, pieza.quaternion, pieza.scale);
          if (this.exploracionDidactica && (nombre.startsWith('diente_') || nombre.endsWith('_dentalv2'))) {
            const matDental = pieza.material as THREE.MeshPhysicalMaterial;
            const exterior = { value: 0 };
            matDental.onBeforeCompile = shader => {
              shader.uniforms['exteriorDental'] = exterior;
              shader.vertexShader = 'varying float profundidadDental;\n' + shader.vertexShader;
              shader.vertexShader = shader.vertexShader.replace('#include <project_vertex>',
                'profundidadDental = (modelMatrix * vec4(transformed,1.0)).x;\n#include <project_vertex>');
              shader.fragmentShader = 'uniform float exteriorDental; varying float profundidadDental;\n' + shader.fragmentShader;
              shader.fragmentShader = shader.fragmentShader.replace('#include <color_fragment>',
                `#include <color_fragment>
                float fondoDental = smoothstep(-2.7,-0.8,profundidadDental);
                diffuseColor.rgb *= mix(1.0,0.94-0.38*fondoDental,exteriorDental);`);
            };
            matDental.customProgramCacheKey = () => 'dental-astra-cavidad-v1';
            pieza.onBeforeRender = (_r,_s,camara) => { exterior.value = camara.layers.mask === 2 ? 1 : 0; };
          }
          if (interiorDidactico) {
            // Retira la mitad próxima de las arcadas SOLO en el corte; las
            // coronas delanteras permanecen completas en la vista exterior.
            this.renderer.localClippingEnabled = true;
            const plano = [new THREE.Plane(new THREE.Vector3(0, 0, -1), .015)];
            const mat = pieza.material as THREE.MeshPhysicalMaterial;
            const prepararMaterial = pieza.onBeforeRender;
            pieza.onBeforeRender = (...args) => {
              prepararMaterial.call(pieza, ...args);
              mat.clippingPlanes = args[2].layers.mask === 2 ? null : plano;
            };
          }
          const coincidencia = /^diente_(sup|inf)_(\d+)$/.exec(nombre);
          const indice = coincidencia ? Number(coincidencia[2]) : -1;
          // En la sección medial se muestran incisivos de referencia. Las
          // arcadas laterales completas ocultarían lengua y punto de contacto.
          if (interiorDidactico && indice !== 5 && indice !== 6) pieza.layers.disable(0);
          const esInferior = inferior;
          const esIncisivo = coincidencia && indice >= 4 && indice <= 7;
          pieza.userData['grupoDental'] = coincidencia
            ? `${esIncisivo ? 'incisivo' : 'posterior'}-${esInferior ? 'inferior' : 'superior'}`
            : `soporte-${esInferior ? 'inferior' : 'superior'}`;
          pieza.userData['indiceDental'] = indice;
          // D4.4b v7: el recuadro (capa 1) solo veía la piel: al abrir la boca
          // enseñaba el reverso beige de la piel y ningún diente. Dientes,
          // incisivos y caninos (3–8) entran en la capa 1; molares, encías,
          // papilas, paladar y hueso no (no se ven por la boca y con todo en
          // la capa el preset bilabial caía por debajo de la base 8bd4a66).
          // La sonrisa muestra la continuación de la arcada. Incluir los
          // primeros premolares evita seis coronas suspendidas en un hueco.
          // El modo normal y el corte conservan su selección anterior.
          if (coincidencia && indice >= (this.exploracionDidactica ? 2 : 3) && indice <= (this.exploracionDidactica ? 9 : 8)) pieza.layers.enable(1);
          if (interiorDidactico && nombre.endsWith('_dentalv2')) pieza.layers.enable(1);
          (inferior ? this.dentroMandibula : this.escena).add(pieza);
          if (nombre.startsWith('diente_') && Math.abs(pieza.position.z) > 0.42) this.dientesLaterales.push(pieza);
          // Los dos arcos se conservan separados; el perfil dental de D4.4a
          // decide después qué soportes/incisivos/posteriores se ven.
          (inferior ? this.piezasDentalesInferiores : this.piezasDentalesSuperiores).push(pieza);
        }
        this.lateralesOcultos = 'ninguno';
      }
      if (piezas.has('velo_modelado') && piezas.has('uvula')) {
        // Conserva los nuevos tejidos; oculta únicamente el respaldo simple.
        if (interiorDidactico) this.velo.children.slice(0,2).forEach(o => { o.visible = false; });
        else this.velo.children.forEach(o => { o.visible = false; });
        for (const nombre of (interiorDidactico ? [] : ['velo_modelado', 'uvula'])) {
          const fuente = piezas.get(nombre)!;
          this.velo.add(new THREE.Mesh(fuente.geometry.clone().applyMatrix4(fuente.matrixWorld),
            materialDe('mucosa', col.velo)));
        }
      }
      for (const m of piezas.values()) {
        m.geometry.dispose();
        (Array.isArray(m.material) ? m.material : [m.material]).forEach(mat => mat.dispose());
      }
      this.cavidadesSimples.forEach(m => { m.visible = false; });
      this.sueloSimple.visible = false;
      this.caraModelada = true;
      this.sombrear();
      this.contenedor.dataset['cara'] = 'blender';
      this.recentrarConservandoAngulo();
      // D4.3c: los dientes/encías/mandíbula/corte modelados nacen visibles;
      // si la familia activa pide vista exterior, se esconden tambien.
      const preset = PRESETS_FAMILIA[this.familiaActual];
      this.vistaExterior(preset.exterior, preset.dentadura);
      this.aplicar(this.actual);
      alTerminar();
    }, () => { alTerminar(); /* Las piezas simples siguen visibles. */ });
  }

  /** D4.2.1: recoloca target y distancia tras un evento que puede cambiar
   *  `distanciaEncuadre()` (cargar `cara.glb`, que activa `caraModelada`/
   *  `cabezaEntera`), conservando el ángulo de vista actual (azimut y
   *  polar). Antes esto se hacía con `distanciaEncuadre()` a secas, sin
   *  `zoomActual` (a diferencia de `redimensionar()`, que sí lo aplicaba):
   *  el zoom del preset de familia se podía perder justo al terminar de
   *  cargar la cara, según qué evento llegara antes. `objetivoActual()` ya
   *  respeta el target de la familia activa, así que tampoco hace falta
   *  tratar aquí el caso bilabial/labiodental aparte. */
  private recentrarConservandoAngulo(): void {
    const objetivoViejo = this.controles.target.clone();
    const direccion = this.camara.position.clone().sub(objetivoViejo);
    const distanciaVieja = direccion.length() || 1;
    const polar = Math.acos(Math.max(-1, Math.min(1, direccion.y / distanciaVieja)));
    const azimut = Math.atan2(direccion.x, direccion.z);
    const o = this.objetivoActual();
    this.controles.target.set(o.x, o.y, 0);
    const distancia = this.distanciaEncuadre() * this.zoomActual;
    this.camara.position.set(
      o.x + distancia * Math.sin(polar) * Math.sin(azimut),
      o.y + distancia * Math.cos(polar),
      distancia * Math.sin(polar) * Math.cos(azimut));
    this.controles.update();
  }

  get tieneCaraModelada(): boolean {
    return this.caraModelada;
  }

  destruir(): void {
    if (!this.vivo) return;
    this.actualizarNormalesPiel = null;
    this.actualizarNormalesLengua = null;
    this.vivo = false;
    cancelAnimationFrame(this.rafId);
    this.observador?.disconnect();
    // El keydown de OrbitControls, quitado de la raíz donde se puso: `dispose` lo
    // busca en `getRootNode()`, que con el visor ya fuera del documento es otro nodo,
    // y el document retenía la escena entera (10 cierres, 10 escenas vivas; 4e, ronda 2).
    // `_interceptControlDown` es un campo privado de OrbitControls en three 0.186: si
    // una versión lo renombra o lo quita, la guarda deja pasar sin quitar nada y
    // `dispose` hace lo suyo; no se rompe el cierre, solo vuelve la fuga (4e, ronda 3).
    const tecla = (this.controles as unknown as { _interceptControlDown?: EventListener })._interceptControlDown;
    if (tecla) this.raiz.removeEventListener('keydown', tecla, { capture: true });
    this.controles.dispose();
    const texturas = new Set<THREE.Texture>();
    this.escena.traverse(o => {
      if (o instanceof THREE.Mesh) {
        o.geometry.dispose();
        for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
          // `material.dispose` no suelta sus mapas: se recogen y se sueltan una vez.
          for (const valor of Object.values(m)) if (valor instanceof THREE.Texture) texturas.add(valor);
          m.dispose();
        }
      }
    });
    texturas.forEach(t => t.dispose());
    this.papilas?.dispose();
    this.soltarPielesLisas();
    if (this.detalle) {
      this.detalle.rt.dispose();
      this.detalle.material.dispose();
      this.detalle.escena.traverse(o => { if (o instanceof THREE.Mesh) o.geometry.dispose(); });
      this.detalle = null;
    }
    this.hueso?.dispose();
    this.escena.environment?.dispose();
    this.luzPrincipal.shadow.dispose();
    this.escena.clear();
    if (this.propio) {
      this.renderer.dispose();
      this.renderer.forceContextLoss();
    } else {
      // El compartido se queda para el siguiente visor: solo se vacían sus listas.
      this.renderer.renderLists.dispose();
      this.renderer.setRenderTarget(null);
    }
    this.canvas.removeEventListener('webglcontextlost', this.alPerder);
    this.canvas.remove();
  }

  private redimensionar(): void {
    const w = Math.max(1, this.contenedor.clientWidth);
    const h = Math.max(1, this.contenedor.clientHeight || Math.round(w * 0.72));
    this.renderer.setSize(w, h, false);
    this.camara.aspect = w / h;
    this.camara.updateProjectionMatrix();
    const direccion = this.camara.position.clone().sub(this.controles.target).normalize();
    this.camara.position.copy(this.controles.target).addScaledVector(direccion, this.distanciaEncuadre() * this.zoomActual);
    this.controles.update();
    this.sucio = true;
  }

  /** (A) v5: pixel ratio bajo mientras hay una línea o una transición en marcha. */
  private ajustarPixelRatio(): void {
    if (!this.menosPixelesEnMovimiento) return;
    const moviendo = this.linea !== null || this.hacia !== null;
    const bajo = moviendo && this.pixelRatioNativo > 1.25;
    if (bajo === this.pixelRatioBajo) return;
    this.pixelRatioBajo = bajo;
    this.renderer.setPixelRatio(bajo ? 1.25 : this.pixelRatioNativo);
    const tam = this.renderer.getSize(new THREE.Vector2());
    this.renderer.setSize(tam.x, tam.y, false);
    this.sucio = true;
  }

  private bucle = (): void => {
    if (!this.vivo) return;
    this.rafId = requestAnimationFrame(this.bucle);
    this.ajustarPixelRatio();
    this.vozRetenida = false;                         // `soplar` la vuelve a poner dentro de un soplo
    if (this.linea) {
      const t = (performance.now() - this.lineaT0) / 1000;
      this.actual = this.poseDeLinea(t);
      this.aplicar(this.actual);
      this.soplar(t);
      if (this.giroLinea) {
        // Sube y baja con una campana suave: en mitad del ciclo está girada del todo.
        const f = Math.min(1, Math.max(0, t / this.linea.total));
        const peso = Math.pow(Math.sin(Math.PI * f), 2);
        this.colocarAzimut(this.giroBase.azimut + this.giroLinea * peso);
      }
      if (t >= this.linea.total) {
        if (this.giroLinea) this.colocarAzimut(this.giroBase.azimut);
        this.linea = null;
        this.giroLinea = 0;
      }
      this.sucio = true;
    } else if (this.hacia && this.desde) {
      const t = Math.min(1, (performance.now() - this.t0) / this.duracion);
      this.actual = mezclarPose(this.desde, this.hacia, t);
      this.aplicar(this.actual);
      if (t >= 1) this.desde = this.hacia = null;
      this.sucio = true;
    }
    this.controles.update();
    this.ocultarLaterales();
    // D4.3b: el pulso de vibración respira con el reloj (no con el ciclo
    // del sonido), aparte de la pose: por eso sigue pintando mientras esté
    // encendido, aunque la pose ya no se mueva.
    if (this.sonoroActivo && this.vozRetenida) {
      if (this.marcaVibracion.visible) { this.marcaVibracion.visible = false; this.sucio = true; }
    } else if (this.sonoroActivo) {
      const pulso = 0.35 + 0.3 * (0.5 + 0.5 * Math.sin((performance.now() / 1000) * 2 * Math.PI * 2.2));
      (this.marcaVibracion.material as THREE.MeshStandardMaterial).opacity = pulso;
      this.marcaVibracion.visible = true;
      this.sucio = true;
    }
    // La guarda de fluidez pinta todos los cuadros mientras mide.
    if (this.guarda.midiendo) this.sucio = true;
    if (this.sucio) {
      this.sucio = false;
      this.dibujar();
      this.medirGuarda();
    }
  };

  /** Corte principal y detalle frontal simultáneo, dentro del mismo canvas.
   * Solo la piel se vuelve opaca durante la segunda pasada: no se duplican
   * mallas, morfos, tiempos ni trayectorias de aire. */
  private dibujar(): void {
    if (this.exploracionDidactica && this.cabezaEntera) {
      // Una vista explícita: girar ya no sustituye bruscamente una cabeza
      // por otra al cruzar un ángulo. El exterior conserva giro completo.
      if (!this.corteDidactico) { this.dibujarExteriorDidactico(); return; }
    }
    const r = this.renderer;
    // Opacidad cero también ejecutaba el shader físico sobre media cabeza.
    // No dibujar esa superficie invisible ahorra trabajo sin rebajar detalle.
    const visiblePrincipal = this.mejilla.visible;
    if ((this.mejilla.material as THREE.MeshStandardMaterial).opacity <= 0.002) this.mejilla.visible = false;
    r.render(this.escena, this.camara);
    this.mejilla.visible = visiblePrincipal;
    // Lote fase 2: /f v/ también llevan el recuadro frontal, para compararlas con
    // /p b/ en el mismo sitio (labio de abajo contra los incisivos frente a cierre).
    if (!this.detalleFrontalActivo || !this.cabezaEntera || !['bilabial', 'nasal-bilabial', 'labiodental'].includes(this.familiaActual)) return;
    const tam = r.getSize(new THREE.Vector2());
    const w = Math.min(138, tam.x * 0.48), h = w / 1.25;
    const fondo = r.getClearColor(new THREE.Color()), alfa = r.getClearAlpha();
    // Quieta, cada cuadro (es uno); en movimiento, uno de cada tres: el gesto
    // de los labios dura 0,5 s y a 10 fps son 5 cuadros; 3 con recuadro nuevo bastan.
    const animando = this.linea !== null || this.hacia !== null;
    this.detalleCuadro++;
    if (!this.detalleListo || !animando || this.detalleCuadro % 3 === 0) this.pintarDetalle(w, h);
    if (!this.detalle) return;
    r.setScissorTest(true);
    r.setScissor(8, 8, w + 4, h + 4); r.setViewport(8, 8, w + 4, h + 4);
    r.setClearColor('#b4a497', 1); r.clear();
    r.setScissor(10, 10, w, h); r.setViewport(10, 10, w, h);
    r.render(this.detalle.escena, this.detalle.camara);
    r.setScissorTest(false); r.setViewport(0, 0, tam.x, tam.y);
    r.setClearColor(fondo, alfa);
  }

  /** El exterior comparte geometría, poses y cámara con el corte; una sola pasada. */
  private dibujarExteriorDidactico(): void {
    if (!this.lucesEnDetalle) {
      this.escena.traverse(o => { if (o instanceof THREE.Light) o.layers.enable(1); });
      this.lucesEnDetalle = true;
    }
    const mat = this.mejilla.material as THREE.MeshStandardMaterial;
    const estado = [this.mejilla.visible, mat.opacity, mat.transparent, mat.depthWrite] as const;
    const capa = this.camara.layers.mask;
    const dentales = [...this.piezasDentalesInferiores, ...this.piezasDentalesSuperiores];
    const visibles = dentales.map(o => o.visible);
    this.mejilla.visible = true; mat.opacity = 1; mat.transparent = false; mat.depthWrite = true;
    dentales.forEach(o => { o.visible = true; });
    this.camara.layers.set(1);
    const entornoAnterior=this.escena.environmentIntensity;
    this.escena.environmentIntensity=.28;
    this.renderer.render(this.escena, this.camara);
    this.escena.environmentIntensity=entornoAnterior;
    this.camara.layers.mask = capa;
    dentales.forEach((o, i) => { o.visible = visibles[i]; });
    [this.mejilla.visible, mat.opacity, mat.transparent, mat.depthWrite] = estado;
  }

  /** v8: suelta los materiales y la textura de la piel lisa del recuadro. */
  private soltarPielesLisas(): void {
    (this.pielesNeutras ?? []).forEach(({ neutro }) => neutro?.dispose());
    if (this.pielesNeutras) this.pielesNeutras.length = 0;
    this.texturaLisaActual?.dispose();
    this.texturaLisaActual = null;
  }

  /** La pasada del detalle frontal, a su textura. */
  private pintarDetalle(w: number, h: number): void {
    const r = this.renderer;
    const ancho = Math.max(32, Math.round(w * r.getPixelRatio() * 0.6)), alto = Math.max(32, Math.round(h * r.getPixelRatio() * 0.6));
    if (!this.detalle || this.detalle.rt.width !== ancho || this.detalle.rt.height !== alto) {
      this.detalle?.rt.dispose();
      // MSAA en la textura (WebGL2): sin él, la silueta de la cara salía a
      // escalones. La pasada ya aplica el tone mapping al escribir en la
      // textura: la copia no debe volver a aplicarlo (salía gris).
      const rt = new THREE.WebGLRenderTarget(ancho, alto, { depthBuffer: true, samples: 2 });
      if (this.detalle) {
        this.detalle.material.map = rt.texture;
        this.detalle.rt = rt;
      } else {
        const material = new THREE.MeshBasicMaterial({ map: rt.texture, toneMapped: false });
        const escena = new THREE.Scene();
        escena.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));
        this.detalle = { rt, escena, camara: new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), material };
      }
    }
    if (!this.lucesEnDetalle) {
      this.escena.traverse(o => { if (o instanceof THREE.Light) o.layers.enable(1); });
      this.lucesEnDetalle = true;
    }
    const mat = this.mejilla.material as THREE.MeshPhysicalMaterial;
    const estado = [this.mejilla.visible, mat.opacity, mat.transparent, mat.depthWrite] as const;
    const sombras = r.shadowMap.autoUpdate;
    this.mejilla.visible = true; mat.opacity = 1; mat.transparent = false; mat.depthWrite = true;
    this.camaraLabios.layers.set(1);
    this.camaraLabios.position.set(-11.8, 0.25, 0);
    this.camaraLabios.lookAt(-3, 0.05, 0);
    this.camaraLabios.updateMatrixWorld();
    r.shadowMap.autoUpdate = false;
    r.setRenderTarget(this.detalle.rt);
    r.setClearColor('#f1e8df', 1); r.clear();
    // D4.4b v7: el recuadro enseña toda la dentadura aunque el perfil dental
    // del corte esconda parte (en las bilabiales los incisivos, para no tapar
    // la lengua): sin esto al abrir la boca no se veía ningún diente.
    const dentales = [...new Set([...(this.piezasDentalesInferiores ?? []), ...(this.piezasDentalesSuperiores ?? []), ...(this.dientesLaterales ?? [])])];
    const visibles = dentales.map(o => o.visible);
    for (const o of dentales) o.visible = true;
    // v7: el recuadro reutiliza el mapa de sombras de la pasada principal (misma
    // luz, misma escena): volver a dibujarlo para el recuadro costaba fps.
    const sombrasAuto = r.shadowMap.autoUpdate;
    r.shadowMap.autoUpdate = false;
    // v8: en el recuadro, la piel lisa en vez de la foto del escaneo (el corte
    // de perfil conserva su material).
    const pieles = this.pielesNeutras ?? [];
    const originales = pieles.map(({ malla, neutro }) => { const m = malla.material; if (neutro) malla.material = neutro; return m; });
    r.render(this.escena, this.camaraLabios);
    pieles.forEach(({ malla }, i) => { malla.material = originales[i]; });
    r.shadowMap.autoUpdate = sombrasAuto;
    dentales.forEach((o, i) => { o.visible = visibles[i]; });
    r.setRenderTarget(null);
    r.shadowMap.autoUpdate = sombras;
    [this.mejilla.visible, mat.opacity, mat.transparent, mat.depthWrite] = estado;
    this.detalleListo = true;
  }

  /** Guarda automática de fluidez (criterio de Central, 14 sep): los dos
   *  primeros segundos se pintan todos los cuadros y se cuentan; por debajo
   *  de 30 por segundo se bajan las sombras a 512, luego se apagan, y si
   *  sigue por debajo, se esconde la mejilla translúcida; todo sin recargar. */
  private medirGuarda(): void {
    const g = this.guarda;
    if (!g.midiendo) return;
    const ahora = performance.now();
    // Los primeros cuadros compilan los shaders y cargan los modelos: no cuentan.
    if (g.t0 === 0) { if (++g.calentando < 12) return; g.t0 = ahora; g.cuadros = 0; g.calentando = 0; return; }
    g.cuadros++;
    const s = (ahora - g.t0) / 1000;
    if (s < 2) return;
    g.fps = g.cuadros / s;
    g.t0 = 0;
    if (g.fps >= 30 || g.etapa >= 3) { g.midiendo = false; return; }
    g.etapa++;
    if (g.etapa === 1) {
      this.bajarSombras();
    } else if (g.etapa === 2) {
      this.apagarSombras();
    } else {
      // En bilabiales ya no es una transparencia decorativa: contiene la
      // mitad cercana de los labios. La guarda no debe borrar el articulador.
      if (this.familiaActual !== 'bilabial' && this.familiaActual !== 'nasal-bilabial') this.mejilla.visible = false;
      g.midiendo = false;
    }
    this.sucio = true;
  }

  /** El mapa de sombras a 512: se descarta el de 1024 y se vuelve a crear. */
  private bajarSombras(): void {
    if (!this.renderer.shadowMap.enabled) return;
    const sombra = this.luzPrincipal.shadow;
    sombra.mapSize.set(512, 512);
    sombra.map?.dispose();
    sombra.map = null;
  }

  private apagarSombras(): void {
    if (!this.renderer.shadowMap.enabled) return;
    this.renderer.shadowMap.enabled = false;
    this.luzPrincipal.castShadow = false;
    this.escena.traverse(o => {
      if (o instanceof THREE.Mesh) (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => { m.needsUpdate = true; });
    });
  }

  /** Estado de la guarda de fluidez: los cuadros por segundo medidos y qué
   *  se ha rebajado (0 nada, 1 sombras a 512, 2 sombras apagadas, 3 sombras
   *  y mejilla apagadas). */
  get estadoGuarda(): { fps: number | null; etapa: number; midiendo: boolean } {
    return { fps: this.guarda.fps, etapa: this.guarda.etapa, midiendo: this.guarda.midiendo };
  }

  /** En la vista de lado (hasta ±20° de azimut) los premolares y molares del
   *  lado de la cámara tapan la lengua: se esconden. Al girar, vuelven. */
  private ocultarLaterales(): void {
    const d = this.camara.position.clone().sub(this.controles.target);
    const azimut = Math.atan2(d.x, d.z);          // 0 = de lado, ±π/2 = cara o nuca
    const deLado = Math.abs(azimut) < (20 * Math.PI) / 180 || Math.abs(Math.abs(azimut) - Math.PI) < (20 * Math.PI) / 180;
    const ahora: 'ninguno' | 'z+' | 'z-' = !deLado ? 'ninguno' : d.z >= 0 ? 'z+' : 'z-';
    // La piel translúcida del lado de la cámara se aclara al pasar de 45° de
    // giro: de frente, media cara sólida y media de cristal quedaba rara.
    const giro = Math.min(Math.abs(azimut), Math.abs(Math.abs(azimut) - Math.PI));
    // Con la cabeza entera, de lado (menos de 25°) la piel translúcida no
    // cubre la cavidad (opacidad cero) y aparece al girar hacia la cara o la
    // nuca; con el loft, al revés: se aclara al pasar de 45°.
    const base = this.cabezaEntera ? 0.09 : 0.14;
    const bilabial = this.familiaActual === 'bilabial' || this.familiaActual === 'nasal-bilabial';
    const opacidad = bilabial
      ? Math.min(1, Math.max(0, (giro - 25 * GR) / (30 * GR)))
      : this.cabezaEntera
      ? base * Math.min(1, Math.max(0, (giro - (25 * Math.PI) / 180) / ((20 * Math.PI) / 180)))
      : base - (base - 0.04) * Math.min(1, Math.max(0, (giro - Math.PI / 4) / (Math.PI / 8)));
    const matMejilla = this.mejilla.material as THREE.MeshStandardMaterial;
    if (Math.abs(matMejilla.opacity - opacidad) > 0.002) { matMejilla.opacity = opacidad; this.sucio = true; }
    for (const ojo of this.ojos ?? []) {
      const cercano = (ojo.userData['lateral'] as number) > 0;
      const visible = !cercano || opacidad >= 0.5;
      if (ojo.visible !== visible) { ojo.visible = visible; this.sucio = true; }
    }
    if (ahora === this.lateralesOcultos) return;
    this.lateralesOcultos = ahora;
    for (const diente of this.dientesLaterales) {
      const lado = diente.position.z >= 0 ? 'z+' : 'z-';
      const grupo = diente.userData['grupoDental'] as GrupoDental | undefined;
      const indice = Number(diente.userData['indiceDental'] ?? -1);
      const porFamilia = !!grupo && visibleEnPerfilDental(this.perfilDentalActual, grupo, indice);
      diente.visible = porFamilia && ahora !== lado;
    }
    this.sucio = true;
  }

  /** `comisura`: cuánto se acercan los extremos de este labio al otro (la
   *  shape key `comisura_abajo` del superior / `comisura_arriba` del inferior
   *  mueve el extremo una unidad por unidad de influencia). */
  private labio(m: THREE.Mesh, largo: number, radio: number, comisura = 0): void {
    if (m.userData['modelado']) {
      const dic = m.morphTargetDictionary, inf = m.morphTargetInfluences;
      if (dic && inf && 'fruncir' in dic && 'estirar' in dic) {
        // 2,3 es el largo neutro; 1,05 el de «muy redondeados»; 2,9 el de «estirados».
        inf[dic['fruncir']] = Math.min(1, Math.max(0, (2.3 - largo) / (2.3 - 1.05)));
        inf[dic['estirar']] = Math.min(1, Math.max(0, (largo - 2.3) / (2.9 - 2.3)));
        const clave = m === this.labioSup ? 'comisura_abajo' : 'comisura_arriba';
        if (clave in dic) inf[dic[clave]] = comisura;
      } else {
        m.scale.set(radio / 0.3, radio / 0.3, largo / 2.3);
      }
      return;
    }
    const u = m.userData as { largo: number; radio: number };
    if (Math.abs(u.largo - largo) < 1e-3 && Math.abs(u.radio - radio) < 1e-3) return;
    m.geometry.dispose();
    m.geometry = geometriaLabio(largo, radio);
    m.userData = { largo, radio };
  }

  private aplicar(n: PoseNumerica): void {
    this.mandibula.rotation.z = n[I_MAND];
    for (const piel of this.pielesDeformables) deformarPiel(piel, n[I_MAND]);
    this.velo.rotation.z = n[I_VELO];
    // El aire nasal aparece a medida que el velo baja.
    const abierto = (n[I_VELO] - VELO_CERRADO) / (VELO_ABIERTO - VELO_CERRADO);
    (this.aireNasal.material as THREE.MeshStandardMaterial).opacity = 0.75 * Math.min(1, Math.max(0, abierto));
    (this.aireOral.material as THREE.MeshStandardMaterial).opacity = 0.75 * Math.min(1, Math.max(0, n[I_AIRE_ORAL]));
    // D4.2: el marcador de contacto se apaga en rampa igual que el aire (la
    // fraccion viene de interpolar el 0/1 de `puntoDeContacto` entre poses).
    const contactoActivo = Math.min(1, Math.max(0, n[I_CONTACTO + 2]));
    this.marcaContacto.position.set(n[I_CONTACTO], n[I_CONTACTO + 1], 0);
    (this.marcaContacto.material as THREE.MeshStandardMaterial).opacity = contactoActivo;
    this.marcaContacto.visible = contactoActivo > 0.02;
    // D4.3b: si la pose es sonora, `bucle()` hace pulsar marcaVibracion con
    // el reloj; si no, se apaga aquí (sin esperar al siguiente pulso).
    this.sonoroActivo = n[I_SONORA] > 0.5;
    if (!this.sonoroActivo) {
      (this.marcaVibracion.material as THREE.MeshStandardMaterial).opacity = 0;
      this.marcaVibracion.visible = false;
    }
    // Las comisuras: el labio de abajo baja con la mandíbula y el de arriba
    // no; lo que se separan sus extremos más de lo normal (0,6 entre los
    // centros de los dos tubos) lo cubren a medias las shape keys de comisura,
    // para que los labios sigan unidos en las esquinas con la boca abierta.
    const finInf = mundo(new THREE.Vector2(n[I_LI] + 0.615, n[I_LI + 1]), n[I_MAND]);
    const hueco = Math.max(0, (n[I_LS + 1] - finInf.y) - 0.6);
    // Los labios modelados ya sacan el centro hacia delante con la shape key
    // «fruncir»: del adelanto de la pose (pensado para el tubo geométrico)
    // solo se conserva un tercio, o los labios se despegan de la cara en /u/.
    // Los retrocesos (labiodental, cerrados) se conservan enteros.
    const avance = (x: number) => (this.labioSup.userData['modelado'] && x < LABIO_X ? LABIO_X + (x - LABIO_X) * 0.35 : x);
    this.labioSup.position.set(avance(n[I_LS]), n[I_LS + 1], 0);
    this.labio(this.labioSup, n[I_LS + 2], n[I_LS + 3], hueco / 2);
    // El labio inferior vive en la mandíbula: su posición es local al pivote.
    this.labioInf.position.set(avance(n[I_LI]) - PIVOTE_MAND.x, n[I_LI + 1] - PIVOTE_MAND.y, 0);
    this.labio(this.labioInf, n[I_LI + 2], n[I_LI + 3], hueco / 2);
    // Los labios en la piel (MakeHuman): las mismas influencias que los tubos
    // (del largo de la pose) y el labio de abajo hacia atrás en la labiodental
    // (la pose lo coloca 0,3 detrás de LABIO_X).
    if (this.pielesConLabios.length) {
      const largo = n[I_LS + 2];
      // La pequeña diferencia de largo del cierre no es redondeamiento.
      const fruncir = Math.min(1, Math.max(0, (2.3 - largo) / (2.3 - 1.05))) * (1 - n[I_CIERRE_LABIOS]);
      const estirar = Math.min(1, Math.max(0, (largo - 2.3) / (2.9 - 2.3)));
      const atras = Math.min(1, Math.max(0, (n[I_LI] - LABIO_X) / 0.3));
      for (const piel of this.pielesConLabios) {
        const dic = piel.morphTargetDictionary!, inf = piel.morphTargetInfluences!;
        // El exterior didáctico tiene un sello propio: al cerrar no mezcla
        // redondeamiento ni retroceso labiodental que separarían sus bordes.
        const neutro = 'abrir_neutro' in dic ? n[I_NEUTRO_ARTICULADO] : 0;
        const cierre = n[I_CIERRE_LABIOS] * (1 - neutro);
        const sello = 'sello_didactico' in dic ? Math.min(1, cierre / 0.4) : 0;
        inf[dic['fruncir']] = fruncir * (1 - sello);
        inf[dic['estirar']] = estirar;
        // Cuerpo en reposo, cierre y apertura, moderado al estirar. Fruncir
        // ya tiene su volumen propio aprobado y no recibe este correctivo.
        if ('cuerpo_labial' in dic) inf[dic['cuerpo_labial']] = (1-fruncir*(1-sello))*(1-.35*estirar);
        if ('labio_atras' in dic) inf[dic['labio_atras']] = atras * (1 - sello) * ('sello_didactico' in dic ? 1 - estirar : 1);
        if ('sello_didactico' in dic) inf[dic['sello_didactico']] = sello;
        // Estirar y fruncir ya abren su propio borde. Sumarlos a la apertura
        // neutra doblaba el labio superior sobre el filtrum en /æ/ y /ɛ/.
        if ('abrir_neutro' in dic) inf[dic['abrir_neutro']] = neutro * (1 - Math.max(estirar, fruncir));
        if ('contorno_dental' in dic) inf[dic['contorno_dental']] = n[I_CONTORNO_DENTAL];
        if ('cierre_labios' in dic) inf[dic['cierre_labios']] = cierre;
        if ('compresion_labios' in dic) inf[dic['compresion_labios']] = n[I_COMPRESION_LABIOS];
      }
    }
    if (!this.corteDidactico) this.actualizarNormalesPiel?.();
    if (this.lenguaGlb?.morphTargetInfluences) {
      const inf = this.lenguaGlb.morphTargetInfluences;
      this.indicesMorfos.forEach((idx, i) => { if (idx !== undefined) inf[idx] = n[I_MORFOS + i]; });
      this.actualizarNormalesLengua?.();
      // Antes de que WebGL suba atributos: onBeforeRender es demasiado
      // tarde y dejaba el relleno con la pose anterior al mantener un gesto.
      this.seccionLingual?.actualizar();
    } else {
      deformarLengua(this.lengua.geometry, n);
    }
    this.sucio = true;
  }
}
