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
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { Linea } from './animacion';
import { Labios, PoseSonido, REPOSO } from './poses';

export interface Colores {
  lengua: string; labios: string; dientes: string; encia: string; velo: string; hueso: string; faringe: string;
  piel: string; mucosa: string;
}

/** Colores de tejido vivo: lengua rosada, encías rosa claro, dientes marfil,
 *  piel cálida y mucosa húmeda un punto más oscura que la encía. Todos van
 *  a materiales físicos (`materialDe`). */
export const COLORES_POR_DEFECTO: Colores = {
  lengua: '#d4737d', labios: '#c9686e', dientes: '#f1e9d8', encia: '#e6989d', velo: '#d68b90',
  hueso: '#e6dcc9', faringe: '#c98a8c', piel: '#eac2ad', mucosa: '#cf868a',
};

/** Qué tejido es cada pieza: decide brillo, barniz húmedo y velo de
 *  subsuperficie (sheen) del material físico. */
export type Tejido = 'piel' | 'mucosa' | 'encia' | 'diente' | 'hueso' | 'labio' | 'lengua';

/** Un material físico por tejido, sin texturas descargadas. La piel y la
 *  mucosa llevan un velo (sheen) que aclara los bordes como la luz que
 *  atraviesa el tejido; la mucosa, la encía y la lengua, un barniz fino y
 *  poco rugoso (húmedas); los dientes, barniz duro y un velo cálido que
 *  imita la leve translucidez del esmalte. */
export function materialDe(tejido: Tejido, color: string, extra: Partial<THREE.MeshPhysicalMaterialParameters> = {}): THREE.MeshPhysicalMaterial {
  const base: Record<Tejido, Partial<THREE.MeshPhysicalMaterialParameters>> = {
    piel: { roughness: 0.62, clearcoat: 0.04, clearcoatRoughness: 0.6, sheen: 0.55, sheenRoughness: 0.75, sheenColor: new THREE.Color('#ffd6c4') },
    mucosa: { roughness: 0.4, clearcoat: 0.5, clearcoatRoughness: 0.32, sheen: 0.45, sheenRoughness: 0.6, sheenColor: new THREE.Color('#ffb0b4') },
    encia: { roughness: 0.42, clearcoat: 0.45, clearcoatRoughness: 0.3, sheen: 0.4, sheenRoughness: 0.6, sheenColor: new THREE.Color('#ffc0c4') },
    diente: { roughness: 0.3, clearcoat: 0.65, clearcoatRoughness: 0.18, sheen: 0.35, sheenRoughness: 0.5, sheenColor: new THREE.Color('#fff4dc'), ior: 1.6 },
    hueso: { roughness: 0.72, clearcoat: 0, sheen: 0.2, sheenRoughness: 0.9, sheenColor: new THREE.Color('#fff3e0') },
    labio: { roughness: 0.45, clearcoat: 0.3, clearcoatRoughness: 0.35, sheen: 0.5, sheenRoughness: 0.65, sheenColor: new THREE.Color('#ffb6b0') },
    lengua: { roughness: 0.46, clearcoat: 0.4, clearcoatRoughness: 0.3, sheen: 0.5, sheenRoughness: 0.6, sheenColor: new THREE.Color('#ff9aa6') },
  };
  return new THREE.MeshPhysicalMaterial({ color: new THREE.Color(color), metalness: 0, ...base[tejido], ...extra });
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
const MAND_MAX = 0.42;                          // radianes con mandibula = 1
const FARINGE_X = 3.15;
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
      (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m.dispose());
    }
  });
}

/** Distribución: [mand, velo, ls(x,y,len,r), li(x,y,len,r) en local de la mandíbula, 6 nudos (x,y), morfos, aire oral]. */
const I_MAND = 0, I_VELO = 1, I_LS = 2, I_LI = 6, I_NUDOS = 10, I_MORFOS = I_NUDOS + N_NUDOS * 2;
const I_AIRE_ORAL = I_MORFOS + MORFOS_LENGUA.length;
const TAMANO = I_AIRE_ORAL + 1;
type PoseNumerica = Float64Array;

/** Las influencias de las shape keys para una pose: cada parámetro, a su morfo. */
function morfosDe(pose: PoseSonido): number[] {
  const [alt, ade] = pose.cuerpo;
  const toca = pose.punta_toca;
  return [
    0.3 * Math.min(1, Math.max(0, pose.mandibula)),   // el resto lo pone el giro de la mandíbula
    pose.punta === 'alveolar' || pose.punta === 'postalveolar' ? (toca ? 1 : 0.75) : pose.punta === 'dental' ? 0.45 : 0,
    pose.punta === 'retrofleja' ? 1 : 0,
    pose.punta === 'interdental' ? 1 : 0,
    Math.max(0, (alt - 0.45) / 0.55),
    Math.max(0, (0.45 - alt) / 0.45),
    Math.max(0, (ade - 0.5) / 0.5),
    Math.max(0, (0.5 - ade) / 0.5),
    pose.dorso_velo ? 1 : Math.min(1, pose.dorso_alto),
    Math.min(1, Math.max(0, pose.raiz)),
  ];
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
  // El aire por la boca se marca en la /h/: sale de la garganta y no hay
  // nada en la boca que lo pare, que es lo que la distingue del reposo.
  n[I_AIRE_ORAL] = pose.lugar === 'glotal' ? 1 : 0;
  return n;
}

function mezclar(a: PoseNumerica, b: PoseNumerica, t: number): PoseNumerica {
  const r = new Float64Array(TAMANO);
  for (let i = 0; i < TAMANO; i++) r[i] = a[i] + (b[i] - a[i]) * t;
  return r;
}

const suavizar = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

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

/** El aire nasal: de la faringe, por detrás del velo, sube a la nariz y sale. */
function geometriaAireNasal(): THREE.BufferGeometry {
  const curva = new THREE.CatmullRomCurve3([
    new THREE.Vector3(2.6, -0.6, 0), new THREE.Vector3(2.7, 0.6, 0), new THREE.Vector3(2.6, 1.7, 0),
    new THREE.Vector3(1.5, 2.05, 0), new THREE.Vector3(-1.0, 2.05, 0), new THREE.Vector3(-3.0, 1.95, 0),
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
  ultimoGiro: number;
}

const suave01 = (t: number) => { const s = Math.min(1, Math.max(0, t)); return s * s * (3 - 2 * s); };

export function pielQueSigueLaMandibula(geometria: THREE.BufferGeometry, labiosEnPiel = false): PielDeformable {
  const pos = geometria.getAttribute('position') as THREE.BufferAttribute;
  const reposo = new Float32Array(pos.array as Float32Array);
  const pesos = new Float32Array(pos.count);
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
      const bajoLabio = suave01((0.2 - y) / 0.1);
      bajo = bajo + (bajoLabio - bajo) * frente;
    }
    const delante = suave01((2.3 - x) / 0.9);         // la garganta y la nuca se quedan
    pesos[i] = bajo * delante;
  }
  return { geometria, reposo, pesos, ultimoGiro: NaN };
}

/** Gira cada vértice alrededor del pivote de la mandíbula por su peso. */
function deformarPiel(piel: PielDeformable, giro: number): void {
  if (giro === piel.ultimoGiro) return;
  piel.ultimoGiro = giro;
  const pos = piel.geometria.getAttribute('position') as THREE.BufferAttribute;
  const salida = pos.array as Float32Array;
  const { reposo, pesos } = piel;
  for (let i = 0; i < pos.count; i++) {
    const w = pesos[i];
    const x = reposo[3 * i], y = reposo[3 * i + 1];
    if (w <= 0) { salida[3 * i] = x; salida[3 * i + 1] = y; continue; }
    const a = giro * w, c = Math.cos(a), s = Math.sin(a);
    const dx = x - PIVOTE_MAND.x, dy = y - PIVOTE_MAND.y;
    salida[3 * i] = PIVOTE_MAND.x + dx * c - dy * s;
    salida[3 * i + 1] = PIVOTE_MAND.y + dx * s + dy * c;
  }
  pos.needsUpdate = true;
  piel.geometria.computeVertexNormals();
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
  /** URL de una lengua modelada en Blender (.glb con las shape keys de
   *  `MORFOS_LENGUA`): sustituye al tubo cuando carga. */
  lenguaGlb?: string;
  /** Labios y perfil seccionado de Blender; conserva las piezas simples si falla. */
  caraGlb?: string;
}

export class EscenaBoca {
  /** Hay WebGL en este navegador (o en este entorno de pruebas). */
  static hayWebGL(): boolean {
    try {
      const c = document.createElement('canvas');
      return !!(c.getContext('webgl2') || c.getContext('webgl'));
    } catch {
      return false;
    }
  }

  readonly canvas: HTMLCanvasElement;
  private readonly renderer: THREE.WebGLRenderer;
  private readonly escena = new THREE.Scene();
  private readonly camara: THREE.PerspectiveCamera;
  private readonly controles: OrbitControls;
  private readonly mandibula = new THREE.Group();
  private readonly velo = new THREE.Group();
  private readonly labioSup: THREE.Mesh;
  private readonly labioInf: THREE.Mesh;
  private readonly lengua: THREE.Mesh;
  private readonly mejilla: THREE.Mesh;
  private readonly aireNasal: THREE.Mesh;
  private readonly aireOral: THREE.Mesh;
  /** Las piezas que van dentro de la mandíbula, en coordenadas del mundo con la boca cerrada. */
  private readonly dentroMandibula: THREE.Group;
  /** La lengua modelada (si se pidió y ya cargó) y sus morfos por índice. */
  private lenguaGlb: THREE.Mesh | null = null;
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
  private t0 = 0;
  private duracion = 0;
  /** La línea de tiempo en marcha (ciclo de un sonido o palabra entera). */
  private linea: { claves: { t: number; n: PoseNumerica }[]; total: number } | null = null;
  private lineaT0 = 0;
  /** Giro de cámara (radianes de azimut) que acompaña a la línea: sube a
   *  mitad del ciclo y vuelve al final. Negativo mira hacia la cara. */
  private giroLinea = 0;
  private giroBase = { azimut: 0, polar: 1.49, distancia: 13 };
  private arrastrando = false;
  private sucio = true;
  private vivo = true;
  private rafId = 0;
  private libre = false;
  reducirMovimiento: boolean;

  constructor(private readonly contenedor: HTMLElement, opciones: OpcionesEscena = {}) {
    contenedor.dataset['lengua'] = 'geometrico';
    contenedor.dataset['cara'] = 'geometrico';
    const col = { ...COLORES_POR_DEFECTO };
    for (const [nombre, valor] of Object.entries(opciones.colores ?? {})) {
      if (valor) col[nombre as keyof Colores] = valor;
    }
    this.reducirMovimiento = !!opciones.reducirMovimiento;

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    // Tono fotográfico (ACES): los brillos del barniz húmedo no se queman.
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.sombras = opciones.sombras !== false;
    this.guarda.midiendo = opciones.guarda !== false;
    if (this.sombras) {
      this.renderer.shadowMap.enabled = true;
      this.renderer.shadowMap.type = THREE.PCFShadowMap;
    }
    this.canvas = this.renderer.domElement;
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
    this.controles.target.set(0.1, 0.05, 0);
    this.controles.enableZoom = false;
    this.controles.enablePan = false;
    this.controles.enableDamping = true;
    this.controles.dampingFactor = 0.12;
    this.controles.rotateSpeed = 0.7;
    this.controles.minPolarAngle = 0.35;
    this.controles.maxPolarAngle = 2.5;
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
    this.escena.add(new THREE.HemisphereLight(0xfff4ea, 0x8a7f86, 0.55));
    const luz = new THREE.DirectionalLight(0xfff1e4, 1.9);
    this.luzPrincipal = luz;
    luz.position.set(-4.5, 7, 7.5);
    if (this.sombras) {
      luz.castShadow = true;
      luz.shadow.mapSize.set(512, 512);
      luz.shadow.radius = 4;
      luz.shadow.bias = -0.0008;
      luz.shadow.normalBias = 0.02;
      const s = luz.shadow.camera;
      s.left = -5; s.right = 5; s.top = 5; s.bottom = -5; s.near = 1; s.far = 30;
    }
    this.escena.add(luz);
    const relleno = new THREE.DirectionalLight(0xdfe8ff, 0.55);
    relleno.position.set(5, -1, -4);
    this.escena.add(relleno);
    const contraluz = new THREE.DirectionalLight(0xffffff, 0.7);
    contraluz.position.set(2, 4, -8);
    this.escena.add(contraluz);
    // La media cabeza lejana mira al otro lado de la luz principal: un
    // relleno suave desde delante y ese lado para que no quede en sombra.
    const lejano = new THREE.DirectionalLight(0xfff0e6, 0.75);
    lejano.position.set(-6, 3, -5);
    this.escena.add(lejano);
    if (opciones.entorno === true) {
      try {
        const pmrem = new THREE.PMREMGenerator(this.renderer);
        this.escena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
        this.escena.environmentIntensity = 0.45;
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
    this.escena.add(this.lengua);

    // La mejilla del lado de la cámara: translúcida, se pinta la última y no
    // escribe profundidad, así que no tapa nada y da un lado a la cabeza.
    this.mejilla = new THREE.Mesh(geometriaMejilla(), material('#f2cfc9', {
      transparent: true, opacity: 0.14, depthWrite: false, side: THREE.DoubleSide, roughness: 0.9,
    }));
    this.mejilla.position.z = ANCHO / 2 + 0.12;
    this.mejilla.renderOrder = 5;
    this.mejilla.visible = opciones.mejilla !== false;
    this.escena.add(this.mejilla);

    this.actual = poseNumerica(REPOSO);
    this.aplicar(this.actual);
    this.sombrear();
    if (opciones.lenguaGlb) this.cargarLengua(opciones.lenguaGlb, col.lengua);
    if (opciones.caraGlb) this.cargarCara(opciones.caraGlb, col);

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
    this.linea = { claves, total: linea.total };
    this.lineaT0 = performance.now();
    // El giro de cámara que acompaña al sonido (labios redondeados o
    // estirados se ven de frente): solo si el usuario no está arrastrando.
    if (opciones.giro && !this.arrastrando) {
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

  /** Corta la línea en marcha y se queda donde está. */
  detener(): void {
    this.linea = null;
  }

  private poseDeLinea(t: number): PoseNumerica {
    const { claves } = this.linea!;
    if (t <= claves[0].t) return claves[0].n;
    for (let i = 0; i < claves.length - 1; i++) {
      const a = claves[i], b = claves[i + 1];
      if (t < b.t) {
        const f = b.t > a.t ? (t - a.t) / (b.t - a.t) : 1;
        return mezclar(a.n, b.n, suavizar(f));
      }
    }
    return claves[claves.length - 1].n;
  }

  /** Coloca la cámara: `azimut` 0 mira de lado (la cara a la izquierda),
   *  negativo gira hacia la cara y positivo hacia la nuca; `polar` π/2 es a
   *  la altura de la boca. */
  vista(azimut: number, polar = 1.49): void {
    const distancia = this.distanciaEncuadre();
    this.controles.target.set(this.cabezaEntera ? 0.9 : 0.1, 0.05, 0);
    this.camara.position.set(
      this.controles.target.x + distancia * Math.sin(polar) * Math.sin(azimut),
      this.controles.target.y + distancia * Math.cos(polar),
      this.controles.target.z + distancia * Math.sin(polar) * Math.cos(azimut));
    this.controles.update();
    this.sucio = true;
  }

  restablecerVista(): void {
    this.vista(0.02);
  }

  private distanciaEncuadre(): number {
    // Con la cara modelada el perfil entero no cabe a 13, pero lo que importa
    // es la boca: en el móvil a 16 quedaba pequeña. La nariz y la garganta se
    // ven enteras al girar.
    // 14,5 es lo más cerca que el perfil entero (nariz, mentón, faringe) cabe
    // sin tocar el borde del lienzo en un móvil (288x420): lo mide
    // tools/probar_boca_integrada.mjs.
    return (this.cabezaEntera ? 17.5 : this.caraModelada ? 14.5 : 13) * Math.max(1, 1 / this.camara.aspect);
  }

  /** Con `true` el lienzo captura todos los gestos táctiles (también los
   *  verticales); con `false`, solo los horizontales y la página sigue
   *  haciendo scroll. */
  girarLibre(activo: boolean): void {
    this.libre = activo;
    this.canvas.style.touchAction = activo ? 'none' : 'pan-y';
  }

  get giraLibre(): boolean {
    return this.libre;
  }

  mostrarMejilla(visible: boolean): void {
    this.mejilla.visible = visible;
    this.sucio = true;
  }

  /** Carga la lengua de Blender y, cuando llega, esconde el tubo. Si falla,
   *  se queda el tubo y no pasa nada. */
  private cargarLengua(url: string, color: string): void {
    new GLTFLoader().load(url, gltf => {
      if (!this.vivo) { liberarModelo(gltf.scene); return; }
      let malla: THREE.Mesh | null = null;
      gltf.scene.traverse(o => {
        if (!malla && o instanceof THREE.Mesh && o.morphTargetInfluences &&
            MORFOS_LENGUA.every(n => Number.isInteger(o.morphTargetDictionary?.[n]))) malla = o;
      });
      if (!malla) { liberarModelo(gltf.scene); return; }
      const m = malla as THREE.Mesh;
      // Mucosa húmeda con papilas de relieve: el material físico de la
      // lengua más el mapa procedimental (si la malla trae UV).
      (Array.isArray(m.material) ? m.material : [m.material]).forEach(mat => mat.dispose());
      const conUv = !!m.geometry.getAttribute('uv');
      m.material = materialDe('lengua', color, conUv && this.papilas ? { bumpMap: this.papilas, bumpScale: 0.6 } : {});
      const dic = m.morphTargetDictionary ?? {};
      this.indicesMorfos = MORFOS_LENGUA.map(nombre => dic[nombre]);
      this.lenguaGlb = m;
      this.lengua.visible = false;
      // La lengua va sobre el suelo de la boca: baja y gira con la mandíbula
      // (consejo de entrega-4e); el morfo `mandibula` solo añade un poco.
      this.dentroMandibula.add(m);
      this.contenedor.dataset['lengua'] = 'blender';
      liberarModelo(gltf.scene);
      this.sombrear();
      this.aplicar(this.actual);
    }, undefined, () => { /* sin lengua modelada: se queda el tubo */ });
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
      o.receiveShadow = opaco;
    });
  }

  private cargarCara(url: string, col: Colores): void {
    new GLTFLoader().load(url, gltf => {
      const piezas = new Map<string, THREE.Mesh>();
      gltf.scene.updateMatrixWorld(true);
      gltf.scene.traverse(o => { if (o instanceof THREE.Mesh) piezas.set(o.name, o); });
      const nombres = ['labio_superior', 'labio_inferior', 'techo_nasal', 'faringe', 'garganta', 'suelo_boca'];
      if (!this.vivo || nombres.some(n => !piezas.has(n))) {
        for (const m of piezas.values()) {
          m.geometry.dispose();
          (Array.isArray(m.material) ? m.material : [m.material]).forEach(mat => mat.dispose());
        }
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
        const fuente = piezas.get(nombre)!;
        const pieza = new THREE.Mesh(fuente.geometry.clone().applyMatrix4(fuente.matrixWorld),
          nombre === 'nariz' ? materialDe('piel', col.piel) : materialDe('mucosa', col.mucosa));
        (nombre === 'suelo_boca' ? this.dentroMandibula : this.escena).add(pieza);
      }
      // La cabeza de MakeHuman trae sus propios labios en la piel: los tubos
      // se esconden (hasta que la piel tenga sus shape keys, el labio de abajo
      // se mueve con la mandíbula por pesos y el de arriba se queda).
      const labiosEnPiel = piezas.get('cabeza_lejana')?.userData?.['labios_en_piel'] === 1;
      if (labiosEnPiel) {
        this.labioSup.visible = false; this.labioInf.visible = false;
        // Una cabeza entera es más grande que el loft: la cámara se aleja y
        // mira un poco más atrás, y la piel translúcida se aclara.
        this.cabezaEntera = true;
        this.controles.target.x = 0.9;
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
        ['ojo_lejano', 'ojo', false], ['iris_lejano', 'iris', false],
      ];
      for (const [nombre, tejido, enMandibula] of cabeza) {
        const fuente = piezas.get(nombre);
        if (!fuente) continue;
        // Caras del corte y pared del fondo claras y mates, como el 2D: la
        // lengua es lo único saturado y la cavidad se lee como hueco.
        const geometria = fuente.geometry.clone().applyMatrix4(fuente.matrixWorld);
        // Marfil mate liso (Central, 14 sep): con textura el corte se mezclaba
        // con la cavidad de lado.
        const mat = tejido === 'corte' ? materialDe('hueso', '#f6ece3', { roughness: 0.92, sheen: 0 })
          : tejido === 'pared' ? materialDe('hueso', '#f6ebe4', { roughness: 0.9, sheen: 0 })
          : tejido === 'ojo' ? materialDe('diente', '#f3efea', { roughness: 0.2, clearcoat: 0.9, clearcoatRoughness: 0.1 })
          : tejido === 'iris' ? materialDe('diente', '#4a3427', { roughness: 0.25, clearcoat: 0.9, clearcoatRoughness: 0.1 })
          : materialDe('piel', col.piel, nombre === 'cabeza_lejana' && labiosEnPiel ? { side: THREE.DoubleSide } : {});
        const pieza = new THREE.Mesh(geometria, mat);
        (enMandibula ? this.dentroMandibula : this.escena).add(pieza);
        // La piel lejana y la pared del fondo siguen a la mandíbula por pesos;
        // si la pared se quedara fija, al abrir asomaría por la piel movida.
        if (nombre === 'cabeza_lejana' || nombre === 'pared_lejana') this.pielesDeformables.push(pielQueSigueLaMandibula(pieza.geometry, labiosEnPiel));
        if (nombre === 'cabeza_lejana') this.conMorfosDeLabios(pieza, fuente);
      }
      const cercana = piezas.get('cabeza_cercana');
      if (cercana) {
        this.mejilla.geometry.dispose();
        this.mejilla.geometry = cercana.geometry.clone().applyMatrix4(cercana.matrixWorld);
        this.mejilla.position.z = 0;
        this.pielesDeformables.push(pielQueSigueLaMandibula(this.mejilla.geometry, labiosEnPiel));
        this.conMorfosDeLabios(this.mejilla, cercana);
      }
      // Las aletas y la punta de la nariz, si el .glb las trae: piel, fijas.
      for (const nombre of ['aleta_izq', 'aleta_der', 'punta_nariz']) {
        const fuente = piezas.get(nombre);
        if (fuente) this.escena.add(new THREE.Mesh(
          fuente.geometry.clone().applyMatrix4(fuente.matrixWorld), materialDe('piel', col.piel)));
      }
      const dientes = Array.from({ length: 12 }, (_, i) => String(i).padStart(2, '0'));
      const papilas = Array.from(piezas.keys()).filter(n => n.startsWith('papila_'));
      const dentales = ['paladar_modelado', 'encia_superior', 'encia_inferior', 'mandibula_modelada',
        ...['encia_borde_sup', 'encia_borde_inf'].filter(n => piezas.has(n)), ...papilas,
        ...dientes.flatMap(i => ['diente_sup_' + i, 'diente_inf_' + i])];
      if (dentales.every(n => piezas.has(n))) {
        this.dentalSimple.forEach(o => { o.visible = false; });
        this.dientesLaterales.length = 0;
        for (const nombre of dentales) {
          const fuente = piezas.get(nombre)!;
          const inferior = nombre.includes('_inf') || nombre === 'mandibula_modelada';
          const geometria = fuente.geometry.clone();
          // Las encias van lisas: su relieve de papilas costaba cuadros en
          // SwiftShader y a la distancia del visor no se distinguia.
          const pieza = new THREE.Mesh(geometria,
            nombre.startsWith('diente_') ? materialDe('diente', col.dientes)
              : nombre === 'mandibula_modelada' ? materialDe('hueso', col.hueso)
              : materialDe('encia', col.encia));
          fuente.matrixWorld.decompose(pieza.position, pieza.quaternion, pieza.scale);
          (inferior ? this.dentroMandibula : this.escena).add(pieza);
          if (nombre.startsWith('diente_') && Math.abs(pieza.position.z) > 0.42) this.dientesLaterales.push(pieza);
        }
        this.lateralesOcultos = 'ninguno';
      }
      if (piezas.has('velo_modelado') && piezas.has('uvula')) {
        this.velo.children.forEach(o => { o.visible = false; });
        for (const nombre of ['velo_modelado', 'uvula']) {
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
      const direccion = this.camara.position.clone().sub(this.controles.target).normalize();
      this.camara.position.copy(this.controles.target).addScaledVector(direccion, this.distanciaEncuadre());
      this.controles.update();
      this.aplicar(this.actual);
    }, undefined, () => { /* Las piezas simples siguen visibles. */ });
  }

  get tieneCaraModelada(): boolean {
    return this.caraModelada;
  }

  destruir(): void {
    this.vivo = false;
    cancelAnimationFrame(this.rafId);
    this.observador?.disconnect();
    this.controles.dispose();
    this.escena.traverse(o => {
      if (o instanceof THREE.Mesh) {
        o.geometry.dispose();
        (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m.dispose());
      }
    });
    this.papilas?.dispose();
    this.hueso?.dispose();
    this.escena.environment?.dispose();
    this.renderer.dispose();
    this.canvas.remove();
  }

  private redimensionar(): void {
    const w = Math.max(1, this.contenedor.clientWidth);
    const h = Math.max(1, this.contenedor.clientHeight || Math.round(w * 0.72));
    this.renderer.setSize(w, h, false);
    this.camara.aspect = w / h;
    this.camara.updateProjectionMatrix();
    const direccion = this.camara.position.clone().sub(this.controles.target).normalize();
    this.camara.position.copy(this.controles.target).addScaledVector(direccion, this.distanciaEncuadre());
    this.controles.update();
    this.sucio = true;
  }

  private bucle = (): void => {
    if (!this.vivo) return;
    this.rafId = requestAnimationFrame(this.bucle);
    if (this.linea) {
      const t = (performance.now() - this.lineaT0) / 1000;
      this.actual = this.poseDeLinea(t);
      this.aplicar(this.actual);
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
      this.actual = mezclar(this.desde, this.hacia, suavizar(t));
      this.aplicar(this.actual);
      if (t >= 1) this.desde = this.hacia = null;
      this.sucio = true;
    }
    this.controles.update();
    this.ocultarLaterales();
    // La guarda de fluidez pinta todos los cuadros mientras mide.
    if (this.guarda.midiendo) this.sucio = true;
    if (this.sucio) {
      this.sucio = false;
      this.renderer.render(this.escena, this.camara);
      this.medirGuarda();
    }
  };

  /** Guarda automática de fluidez (criterio de Central, 14 sep): los dos
   *  primeros segundos se pintan todos los cuadros y se cuentan; por debajo
   *  de 30 por segundo se apagan las sombras sin recargar y se mide otra
   *  vez; si sigue por debajo, se esconde la mejilla translúcida. */
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
    if (g.fps >= 30 || g.etapa >= 2) { g.midiendo = false; return; }
    g.etapa++;
    if (g.etapa === 1) {
      this.apagarSombras();
    } else {
      this.mejilla.visible = false;
      g.midiendo = false;
    }
    this.sucio = true;
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
   *  se ha apagado (0 nada, 1 sombras, 2 sombras y mejilla). */
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
    const opacidad = this.cabezaEntera
      ? base * Math.min(1, Math.max(0, (giro - (25 * Math.PI) / 180) / ((20 * Math.PI) / 180)))
      : base - (base - 0.04) * Math.min(1, Math.max(0, (giro - Math.PI / 4) / (Math.PI / 8)));
    const matMejilla = this.mejilla.material as THREE.MeshStandardMaterial;
    if (Math.abs(matMejilla.opacity - opacidad) > 0.002) { matMejilla.opacity = opacidad; this.sucio = true; }
    if (ahora === this.lateralesOcultos) return;
    this.lateralesOcultos = ahora;
    for (const diente of this.dientesLaterales) {
      const lado = diente.position.z >= 0 ? 'z+' : 'z-';
      diente.visible = ahora !== lado;
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
      const fruncir = Math.min(1, Math.max(0, (2.3 - largo) / (2.3 - 1.05)));
      const estirar = Math.min(1, Math.max(0, (largo - 2.3) / (2.9 - 2.3)));
      const atras = Math.min(1, Math.max(0, (n[I_LI] - LABIO_X) / 0.3));
      for (const piel of this.pielesConLabios) {
        const dic = piel.morphTargetDictionary!, inf = piel.morphTargetInfluences!;
        inf[dic['fruncir']] = fruncir;
        inf[dic['estirar']] = estirar;
        if ('labio_atras' in dic) inf[dic['labio_atras']] = atras;
      }
    }
    if (this.lenguaGlb?.morphTargetInfluences) {
      const inf = this.lenguaGlb.morphTargetInfluences;
      this.indicesMorfos.forEach((idx, i) => { if (idx !== undefined) inf[idx] = n[I_MORFOS + i]; });
    } else {
      deformarLengua(this.lengua.geometry, n);
    }
    this.sucio = true;
  }
}
