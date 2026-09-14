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
import { Linea } from './animacion';
import { Labios, PoseSonido, REPOSO } from './poses';

export interface Colores {
  lengua: string; labios: string; dientes: string; encia: string; velo: string; hueso: string; faringe: string;
}

export const COLORES_POR_DEFECTO: Colores = {
  lengua: '#d9727f', labios: '#e59a94', dientes: '#f6f3ec', encia: '#efb9b1', velo: '#e4a39c',
  hueso: '#ece7dc', faringe: '#cdbcbc',
};

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

/** Distribución: [mand, velo, ls(x,y,len,r), li(x,y,len,r) en local de la mandíbula, 6 nudos (x,y), morfos]. */
const I_MAND = 0, I_VELO = 1, I_LS = 2, I_LI = 6, I_NUDOS = 10, I_MORFOS = I_NUDOS + N_NUDOS * 2;
const TAMANO = I_MORFOS + MORFOS_LENGUA.length;
type PoseNumerica = Float64Array;

/** Las influencias de las shape keys para una pose: cada parámetro, a su morfo. */
function morfosDe(pose: PoseSonido): number[] {
  const [alt, ade] = pose.cuerpo;
  const toca = pose.punta_toca;
  return [
    Math.min(1, Math.max(0, pose.mandibula)),
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

/** El arco dental en planta: u de -1 (izquierda) a 1 (derecha). */
function arco(u: number, retroceso = 2.3): THREE.Vector2 {
  return new THREE.Vector2(-2.6 + retroceso * u * u, (ANCHO / 2) * u);   // (x, z)
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
    diente.rotation.y = -Math.atan2(2 * 2.3 * u, ANCHO / 2);   // mirando a la tangente del arco
    grupo.add(diente);
    if (!incisivo) laterales.push(diente);
  }
  return laterales;
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
  const f = new THREE.Shape();
  f.moveTo(-2.1, 0.7);
  f.quadraticCurveTo(-2.5, 1.2, -1.6, 1.55);
  f.lineTo(2.3, 1.85);
  f.quadraticCurveTo(3.1, 1.9, 3.05, 1.1);
  f.lineTo(3.05, -1.9);
  f.quadraticCurveTo(3.0, -2.5, 2.3, -2.45);
  f.lineTo(-1.3, -2.2);
  f.quadraticCurveTo(-2.3, -2.1, -2.3, -1.2);
  f.lineTo(-2.35, 0.2);
  f.quadraticCurveTo(-2.4, 0.55, -2.1, 0.7);
  const g = new THREE.ExtrudeGeometry(f, { depth: 0.05, bevelEnabled: false });
  return g;
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
  /** URL de una lengua modelada en Blender (.glb con las shape keys de
   *  `MORFOS_LENGUA`): sustituye al tubo cuando carga. */
  lenguaGlb?: string;
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
  /** La lengua modelada (si se pidió y ya cargó) y sus morfos por índice. */
  private lenguaGlb: THREE.Mesh | null = null;
  private indicesMorfos: (number | undefined)[] = [];
  /** Premolares y molares: se esconden los del lado de la cámara en la vista de lado. */
  private readonly dientesLaterales: THREE.Mesh[] = [];
  private lateralesOcultos: 'ninguno' | 'z+' | 'z-' = 'ninguno';
  private readonly observador: ResizeObserver | null = null;
  private actual: PoseNumerica;
  private desde: PoseNumerica | null = null;
  private hacia: PoseNumerica | null = null;
  private t0 = 0;
  private duracion = 0;
  /** La línea de tiempo en marcha (ciclo de un sonido o palabra entera). */
  private linea: { claves: { t: number; n: PoseNumerica }[]; total: number } | null = null;
  private lineaT0 = 0;
  private sucio = true;
  private vivo = true;
  private rafId = 0;
  private libre = false;
  reducirMovimiento: boolean;

  constructor(private readonly contenedor: HTMLElement, opciones: OpcionesEscena = {}) {
    const col = { ...COLORES_POR_DEFECTO, ...opciones.colores };
    this.reducirMovimiento = !!opciones.reducirMovimiento;

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.canvas = this.renderer.domElement;
    this.canvas.style.display = 'block';
    this.canvas.style.width = '100%';
    this.canvas.style.height = '100%';
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
    this.controles.update();
    // OrbitControls pone touch-action: none al conectarse, y eso deja la
    // página sin scroll sobre la boca. Con pan-y el navegador se queda los
    // gestos verticales (scroll) y nos manda pointercancel; los horizontales
    // giran la boca. `girarLibre(true)` captura todo, para quien lo pida.
    this.girarLibre(false);

    this.escena.add(new THREE.HemisphereLight(0xffffff, 0x6b7a90, 1.3));
    const luz = new THREE.DirectionalLight(0xffffff, 1.7);
    luz.position.set(-4, 6, 7);
    this.escena.add(luz);
    const relleno = new THREE.DirectionalLight(0xffffff, 0.6);
    relleno.position.set(5, 1, -5);
    this.escena.add(relleno);

    const mDientes = material(col.dientes, { roughness: 0.4 });
    const mEncia = material(col.encia);
    const mHueso = material(col.hueso);
    const mLabios = material(col.labios, { roughness: 0.6 });

    // Maxilar: paladar, encía con dientes superiores, velo con bisagra, faringe.
    const paladar = new THREE.Mesh(banda(PALADAR, GROSOR_PALADAR, ANCHO), mEncia);
    this.escena.add(paladar);
    const arcoSup = new THREE.Group();
    arcoSup.add(tuboArco(0.98, 0.2, mEncia));
    this.dientesLaterales.push(...arcoDental(arcoSup, 0.7, 0.5, mDientes));
    this.escena.add(arcoSup);

    const veloMalla = new THREE.Mesh(new THREE.CapsuleGeometry(GROSOR_PALADAR / 2, LARGO_VELO - GROSOR_PALADAR / 2, 4, 10), material(col.velo));
    veloMalla.rotation.z = -Math.PI / 2;                      // la cápsula a lo largo de +x
    veloMalla.position.x = LARGO_VELO / 2;
    const veloAncho = new THREE.Mesh(new THREE.BoxGeometry(LARGO_VELO, GROSOR_PALADAR, ANCHO * 0.7), material(col.velo));
    veloAncho.position.x = LARGO_VELO / 2;
    this.velo.add(veloAncho, veloMalla);
    this.velo.position.set(PIVOTE_VELO.x, PIVOTE_VELO.y, 0);
    this.escena.add(this.velo);

    // La pared de la faringe, de la nasofaringe a la garganta.
    const faringe = new THREE.Mesh(new THREE.BoxGeometry(0.3, 5.6, ANCHO), material(col.faringe, { transparent: true, opacity: 0.55 }));
    faringe.position.set(FARINGE_X, -0.6, 0);
    this.escena.add(faringe);
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
    // El aire nasal: un hilo azul que solo se ve cuando el velo está bajado.
    this.aireNasal = new THREE.Mesh(geometriaAireNasal(), material('#2f9cc0', {
      transparent: true, opacity: 0, depthWrite: false, emissive: new THREE.Color('#2f9cc0'), emissiveIntensity: 0.4,
    }));
    this.aireNasal.renderOrder = 4;
    this.escena.add(this.aireNasal);

    // Mandíbula: gira en el pivote y arrastra hueso, dientes inferiores y labio
    // inferior. `dentro` deshace el desplazamiento del pivote para que las
    // piezas se coloquen en coordenadas del mundo con la boca cerrada.
    const dentro = new THREE.Group();
    dentro.position.set(-PIVOTE_MAND.x, -PIVOTE_MAND.y, 0);
    dentro.add(tuboArco(-0.2, 0.2, mEncia));
    dentro.add(tuboArco(-0.62, 0.28, mHueso, 2.6));
    this.dientesLaterales.push(...arcoDental(dentro, 0.1, 0.5, mDientes));
    const suelo = new THREE.Mesh(new THREE.BoxGeometry(SUELO.x1 - SUELO.x0, SUELO.grosor, ANCHO * 0.8), mEncia);
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

    this.lengua = new THREE.Mesh(geometriaLengua(), material(col.lengua, { roughness: 0.55 }));
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
    if (opciones.lenguaGlb) this.cargarLengua(opciones.lenguaGlb, col.lengua);

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
  reproducir(linea: Linea): void {
    this.desde = this.hacia = null;
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
    this.sucio = true;
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
    const distancia = 10.5;
    this.controles.target.set(0.1, 0.05, 0);
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
      if (!this.vivo) return;
      let malla: THREE.Mesh | null = null;
      gltf.scene.traverse(o => { if (!malla && o instanceof THREE.Mesh && o.morphTargetInfluences) malla = o; });
      if (!malla) return;
      const m = malla as THREE.Mesh;
      // Mucosa húmeda sin texturas: brillo de barniz fino y un velo rosado
      // (sheen) que imita algo de subsuperficie en los bordes.
      m.material = new THREE.MeshPhysicalMaterial({
        color: new THREE.Color(color), roughness: 0.42, metalness: 0,
        clearcoat: 0.35, clearcoatRoughness: 0.3,
        sheen: 0.5, sheenRoughness: 0.6, sheenColor: new THREE.Color('#ff9aa6'),
      });
      const dic = m.morphTargetDictionary ?? {};
      this.indicesMorfos = MORFOS_LENGUA.map(nombre => dic[nombre]);
      this.lenguaGlb = m;
      this.lengua.visible = false;
      this.escena.add(m);
      this.aplicar(this.actual);
    }, undefined, () => { /* sin lengua modelada: se queda el tubo */ });
  }

  get tieneLenguaModelada(): boolean {
    return this.lenguaGlb !== null;
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
    this.renderer.dispose();
    this.canvas.remove();
  }

  private redimensionar(): void {
    const w = Math.max(1, this.contenedor.clientWidth);
    const h = Math.max(1, this.contenedor.clientHeight || Math.round(w * 0.72));
    this.renderer.setSize(w, h, false);
    this.camara.aspect = w / h;
    this.camara.updateProjectionMatrix();
    this.sucio = true;
  }

  private bucle = (): void => {
    if (!this.vivo) return;
    this.rafId = requestAnimationFrame(this.bucle);
    if (this.linea) {
      const t = (performance.now() - this.lineaT0) / 1000;
      this.actual = this.poseDeLinea(t);
      this.aplicar(this.actual);
      if (t >= this.linea.total) this.linea = null;
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
    if (this.sucio) {
      this.sucio = false;
      this.renderer.render(this.escena, this.camara);
    }
  };

  /** En la vista de lado (hasta ±20° de azimut) los premolares y molares del
   *  lado de la cámara tapan la lengua: se esconden. Al girar, vuelven. */
  private ocultarLaterales(): void {
    const d = this.camara.position.clone().sub(this.controles.target);
    const azimut = Math.atan2(d.x, d.z);          // 0 = de lado, ±π/2 = cara o nuca
    const deLado = Math.abs(azimut) < (20 * Math.PI) / 180 || Math.abs(Math.abs(azimut) - Math.PI) < (20 * Math.PI) / 180;
    const ahora: 'ninguno' | 'z+' | 'z-' = !deLado ? 'ninguno' : d.z >= 0 ? 'z+' : 'z-';
    if (ahora === this.lateralesOcultos) return;
    this.lateralesOcultos = ahora;
    for (const diente of this.dientesLaterales) {
      const lado = diente.position.z >= 0 ? 'z+' : 'z-';
      diente.visible = ahora !== lado;
    }
    this.sucio = true;
  }

  private labio(m: THREE.Mesh, largo: number, radio: number): void {
    const u = m.userData as { largo: number; radio: number };
    if (Math.abs(u.largo - largo) < 1e-3 && Math.abs(u.radio - radio) < 1e-3) return;
    m.geometry.dispose();
    m.geometry = geometriaLabio(largo, radio);
    m.userData = { largo, radio };
  }

  private aplicar(n: PoseNumerica): void {
    this.mandibula.rotation.z = n[I_MAND];
    this.velo.rotation.z = n[I_VELO];
    // El aire nasal aparece a medida que el velo baja.
    const abierto = (n[I_VELO] - VELO_CERRADO) / (VELO_ABIERTO - VELO_CERRADO);
    (this.aireNasal.material as THREE.MeshStandardMaterial).opacity = 0.75 * Math.min(1, Math.max(0, abierto));
    this.labioSup.position.set(n[I_LS], n[I_LS + 1], 0);
    this.labio(this.labioSup, n[I_LS + 2], n[I_LS + 3]);
    // El labio inferior vive en la mandíbula: su posición es local al pivote.
    this.labioInf.position.set(n[I_LI] - PIVOTE_MAND.x, n[I_LI + 1] - PIVOTE_MAND.y, 0);
    this.labio(this.labioInf, n[I_LI + 2], n[I_LI + 3]);
    if (this.lenguaGlb?.morphTargetInfluences) {
      const inf = this.lenguaGlb.morphTargetInfluences;
      this.indicesMorfos.forEach((idx, i) => { if (idx !== undefined) inf[idx] = n[I_MORFOS + i]; });
    } else {
      deformarLengua(this.lengua.geometry, n);
    }
    this.sucio = true;
  }
}
