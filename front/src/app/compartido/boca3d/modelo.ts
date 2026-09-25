/** El modelo articulatorio aprendido (25 sep 2026): la coarticulación y el
 *  tiempo de la boca salen de datos, no de reglas.
 *
 *  Modelo de dominancia de Cohen-Massaro entrenado con GRID (CC BY 4.0, 33
 *  hablantes, 27 h de vídeo frontal) en `tools/modelo_articulatorio/`: cada
 *  fonema domina cada control con un peso que crece al acercarse a su centro,
 *  con una anticipación (θa) y un arrastre (θc) propios. Frente al calendario
 *  de reglas de `animacion.ts`, sigue a la boca real con Pearson 0,56 contra
 *  0,44, sin los 60 ms de retraso en la mandíbula, y redondea ANTES de la /u/
 *  (las reglas, después). Resultados: `investigacion/modelo_articulatorio/`.
 *
 *  Las poses hechas a mano siguen siendo el vocabulario (lengua, velo, forma
 *  de los labios): el modelo decide CUÁNTO pesa cada sonido en cada instante
 *  (qué pose domina y cuál se mezcla con ella) y la apertura de la mandíbula,
 *  con la recta medida → rig de `calibrar_rig.py` (r = 0,70 entre fonemas). */
import modelo from './modelo_articulatorio.json';
import type { Clave } from './animacion';
import type { PoseSonido } from './poses';

interface ModeloDominancia {
  fonemas: string[];
  controles: string[];
  T: number[][];
  log_alfa: number[][];
  log_theta_ant: number[][];
  log_theta_arr: number[][];
}
const M = modelo as unknown as ModeloDominancia;

/** El control que reparte el peso entre poses (la forma de los labios lleva
 *  el gesto más visible) y el de la mandíbula. */
const K_PESO = M.controles.indexOf('geo:ancho');
const K_MAND = M.controles.indexOf('geo:mandibula');
/** Recta medida (z del hablante) → `mandibula` del rig (calibracion.json, final). */
const MAND_PENDIENTE = 0.5418, MAND_ORDENADA = 0.1356;

/** IPA del rig → ARPAbet del modelo. Los que GRID no tiene (su vocabulario es
 *  pequeño) toman el más parecido en boca: /ʃ ʒ/ como /s z/ con labios del
 *  catálogo, /ŋ/ como /n/, /ɝ ɚ/ como /r/, /ʊ/ como /ʊ/→/uw/, /ɔɪ/ como /ow/. */
const IPA_ARPA: Record<string, string> = {
  p: 'p', b: 'b', t: 't', d: 'd', k: 'k', 'ɡ': 'g', g: 'g', f: 'f', v: 'v', 'θ': 'th', 'ð': 'dh',
  s: 's', z: 'z', 'ʃ': 's', 'ʒ': 'z', h: 'hh', 'tʃ': 'ch', 'dʒ': 'jh', m: 'm', n: 'n', 'ŋ': 'n',
  l: 'l', 'ɫ': 'l', 'ɹ': 'r', r: 'r', w: 'w', j: 'y', i: 'iy', 'iː': 'iy', 'ɪ': 'ih', 'ɛ': 'eh', e: 'eh', 'æ': 'ae',
  'ɑ': 'aa', 'ɑː': 'aa', 'ɒ': 'aa', 'ɔ': 'ao', 'ɔː': 'ao', 'ʊ': 'uw', u: 'uw', 'uː': 'uw', 'ʌ': 'ah', 'ə': 'ah',
  'ɝ': 'r', 'ɜː': 'r', 'ɚ': 'r', 'eɪ': 'ey', 'aɪ': 'ay', 'ɔɪ': 'ow', 'oʊ': 'ow', 'əʊ': 'ow', 'aʊ': 'aw',
};
const INDICE = new Map(M.fonemas.map((f, i) => [f, i]));

function indiceDe(simbolo: string): number {
  const arpa = IPA_ARPA[simbolo] ?? IPA_ARPA[simbolo.replace(/ː/g, '')] ?? 'ah';
  return INDICE.get(arpa) ?? INDICE.get('ah')!;
}

/** Un sonido de la frase con su pose YA resuelta (libres rellenos) y su tramo. */
export interface TramoFonema { simbolo: string; pose: PoseSonido; t0: number; t1: number }

/** Pesos (normalizados) de cada segmento en el instante `t` para el control `k`. */
function pesos(segs: { id: number; c: number }[], t: number, k: number): number[] {
  const logs = segs.map(({ id, c }) => {
    const dt = c - t;
    const theta = Math.exp(dt > 0 ? M.log_theta_ant[id][k] : M.log_theta_arr[id][k]);
    return M.log_alfa[id][k] - theta * Math.abs(dt);
  });
  const max = Math.max(...logs);
  const e = logs.map(l => Math.exp(l - max));
  const suma = e.reduce((a, b) => a + b, 0);
  return e.map(x => x / suma);
}

/** Las claves de la boca cada `paso` segundos, de `desde` a `hasta`: en cada
 *  instante, la pose del sonido que más domina, mezclada con la del segundo
 *  (`hacia`, `f`), y la mandíbula que da el modelo. Antes del primer sonido y
 *  después del último hay silencio (el reposo), como en los datos. */
export function clavesModelo(tramos: TramoFonema[], reposo: PoseSonido, desde: number, hasta: number, paso = 0.04): Clave[] {
  if (!tramos.length) return [];
  const sil = INDICE.get('sil')!;
  const primero = tramos[0].t0, ultimo = tramos[tramos.length - 1].t1;
  const todos = [
    { id: sil, c: primero - 0.25, pose: reposo },
    ...tramos.map(s => ({ id: indiceDe(s.simbolo), c: (s.t0 + s.t1) / 2, pose: s.pose })),
    { id: sil, c: ultimo + 0.25, pose: reposo },
  ];
  const claves: Clave[] = [];
  for (let t = desde; t <= hasta + 1e-9; t += paso) {
    // Solo los vecinos cuentan (el peso cae exponencialmente): ventana de ±0,6 s.
    const cerca = todos.filter(s => Math.abs(s.c - t) < 0.6);
    const lista = cerca.length ? cerca : [todos.reduce((a, b) => (Math.abs(a.c - t) < Math.abs(b.c - t) ? a : b))];
    const w = pesos(lista, t, K_PESO);
    const orden = w.map((x, i) => [x, i] as const).sort((a, b) => b[0] - a[0]);
    const a = lista[orden[0][1]], b = orden[1] ? lista[orden[1][1]] : null;
    const wm = pesos(lista, t, K_MAND);
    const z = wm.reduce((s, x, i) => s + x * M.T[lista[i].id][K_MAND], 0);
    const mandibula = Math.min(1, Math.max(0, MAND_PENDIENTE * z + MAND_ORDENADA));
    const conMand = (p: PoseSonido): PoseSonido => ({ ...p, mandibula });
    const f = b ? orden[1][0] / (orden[0][0] + orden[1][0]) : 0;
    claves.push(b && b.pose !== a.pose && f > 0.02
      ? { t, pose: conMand(a.pose), hacia: conMand(b.pose), f }
      : { t, pose: conMand(a.pose) });
  }
  return claves;
}
