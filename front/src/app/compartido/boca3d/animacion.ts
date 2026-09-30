/** Líneas de tiempo del visor 3D: el ciclo de un sonido (reposo → sonido →
 *  reposo, 2,8 s) y una palabra entera, con los mismos instantes y las mismas
 *  duraciones que el corte 2D (`_linea_sonido` y `_linea_palabra` de
 *  `app/animacion_articulatoria`). Sin three.js: solo poses y segundos. */
import { CatalogoPoses, DURACION_S, Movimiento, PoseSonido, Segmento, resolver } from './poses';
import { MODELO_ARTICULATORIO_ACTIVO } from './interruptor';
import { TramoFonema, clavesModelo } from './modelo';

/** Un instante de la línea: la boca está en `pose`, o a la fracción `f` del
 *  camino entre `pose` y `hacia` (la «suelta» de una oclusiva). */
export interface Clave {
  t: number;
  pose: PoseSonido;
  hacia?: PoseSonido;
  f?: number;
}

export interface Linea {
  total: number;
  claves: Clave[];
  /** La pose que se enseña quieta cuando no hay que mover nada. */
  quieta: PoseSonido;
  /** Segundo de la línea en que empieza a sonar el sonido (o la palabra):
   *  el audio se arranca para que su primera energía caiga ahí. */
  sonidoEn: number;
  /** D4.4b v4: soplos de aspiración. Cada oclusiva SORDA (/p t k/) suelta un
   *  chorro de aire tras la liberación (VOT ≈25–40 ms, Lisker y Abramson
   *  1964); la sonora (/b d ɡ/) no: en ella la vibración sigue desde la
   *  liberación. `en` es el instante de la liberación y `dura`, lo que se ve
   *  el soplo: la misma ráfaga que el 2D (0,55 s en `_linea_sonido`, contra
   *  0,25 en las sonoras), escalada con la velocidad como todo lo demás. */
  aspiracion?: { en: number; dura: number }[];
}

/** Duración visible del soplo de una oclusiva sorda, a 1× (la del 2D). */
export const SOPLO_S = 0.55;

/** Lote fase 3: el VOT de las sordas crece cuanto más atrás se articulan,
 *  labial < alveolar < velar (≈25 / 35 / 42 ms en inicio tónico, Lisker y
 *  Abramson 1964; investigación fonética §1 y §9.10). El soplo visible y el
 *  retraso de la vibración de la vocal siguiente se escalan en esa proporción
 *  sobre la alveolar, que conserva los 0,55 s del 2D. */
export const VOT_MS: Record<string, number> = { bilabial: 25, alveolar: 35, velar: 42 };

/** Lo que se ve el soplo de una oclusiva sorda, a 1×. */
export function soploDe(pose: PoseSonido): number {
  return SOPLO_S * (VOT_MS[pose.lugar] ?? VOT_MS['alveolar']) / VOT_MS['alveolar'];
}

/** El factor de «despacio» de las palabras del 2D. */
export const LENTO = 1.6;

/** Factor continuo elegido en Pronunciar (0,25×..2×). */
export type Velocidad = number;

/** La misma línea, `velocidad` veces más rápida (0,5 = el doble de larga):
 *  todos los instantes se dividen por la velocidad, incluido `sonidoEn`. */
export function aVelocidad(linea: Linea, velocidad: number): Linea {
  const v = velocidad > 0 ? velocidad : 1;
  if (v === 1) return linea;
  return { ...linea, total: linea.total / v, sonidoEn: linea.sonidoEn / v,
    claves: linea.claves.map(c => ({ ...c, t: c.t / v })),
    aspiracion: linea.aspiracion?.map(a => ({ en: a.en / v, dura: a.dura / v })) };
}

/** Cuándo arrancar el audio (segundos desde el arranque de la línea) para
 *  que su primera energía caiga en `sonidoEn` de la línea ya ralentizada:
 *  el silencio inicial del archivo dura `silencio / velocidadAudio` al
 *  reproducirlo a esa velocidad (1 si el navegador no pudo ralentizarlo). */
/** Ajusta el ciclo de un sonido a lo que de verdad dura su audio (Miguel,
 *  24 sep: «que la animación vaya al mismo tiempo que el sonido»). El tramo
 *  que suena se estira o acorta a `sonora` segundos (a 1×) y lo que viene
 *  después se desplaza; `sonidoEn` pasa al comienzo de ese tramo:
 *  - vocales, fricativas, nasales, aproximantes: la pose sostenida;
 *  - oclusivas: desde la explosión (fin del cierre) hasta volver al reposo;
 *  - africadas: desde la suelta del cierre hasta el final de la fricción;
 *  - diptongos: del primer objetivo al final del segundo. */
export function alAudio(linea: Linea, movimiento: Movimiento, sonora: number): Linea {
  const c = linea.claves;
  if (c.length < 5 || !(sonora > 0)) return linea;
  const [ia, ib] = movimiento === 'oclusiva' ? [3, 5]
    : movimiento === 'africada' || movimiento === 'diptongo' ? (c.length >= 7 ? (movimiento === 'africada' ? [3, 5] : [2, 5]) : [2, 3])
    : [2, 3];
  const a = c[ia].t, b = c[ib].t, largo = Math.min(4, Math.max(0.2, sonora));
  const escala = largo / Math.max(1e-6, b - a), desplazar = largo - (b - a);
  const mover = (t: number) => t <= a ? t : t <= b ? a + (t - a) * escala : t + desplazar;
  return {
    ...linea,
    claves: c.map(k => ({ ...k, t: mover(k.t) })),
    total: linea.total + desplazar,
    sonidoEn: a,
    aspiracion: linea.aspiracion?.map(x => ({ en: mover(x.en), dura: x.dura })),
  };
}

/** El gesto de un sonido repetido en cada tramo que suena de su audio (en
 *  segundos del archivo). La línea va `ADELANTO` por delante del archivo
 *  para que la boca llegue a la pose justo cuando empieza cada tramo:
 *  `sonidoEn - silencio` es ese adelanto (ver `retrasoAudio`). Oclusivas:
 *  cierre antes del tramo y explosión al empezar; africadas: cierre y luego
 *  la fricción durante el tramo; diptongos: del primer objetivo al segundo. */
export const ADELANTO = 0.45;
export function alCompasDeTramos(pose: PoseSonido, catalogo: CatalogoPoses,
                                 tramos: { inicio: number; fin: number }[], silencio: number, duracion: number,
                                 palabra: Segmento[] = []): Linea | null {
  if (!tramos.length) return null;
  const R = catalogo.reposo;
  const [PA0, PB] = objetivos(pose, R, R);
  const PA = conAlgoQueVer(pose, PA0, R);
  const m = pose.movimiento, L = ADELANTO;
  const claves: Clave[] = [{ t: 0, pose: R }];
  const aspiracion: { en: number; dura: number }[] = [];
  let libre = 0;          // instante desde el que se puede empezar a mover
  tramos.forEach(({ inicio, fin }, n) => {
    const a = L + inicio, b = Math.max(a + 0.08, L + fin);
    const ir = Math.max(libre, a - 0.35);
    if (palabra.length && n === tramos.length - 1) {
      // El último tramo es la palabra de ejemplo grabada (p. ej. «vision» en
      // /ʒ/): la boca la articula entera, ajustada a lo que dura.
      const lento = Math.min(3, Math.max(0.35, (b - a) / Math.max(1e-6, duracionSegmentos(palabra, catalogo))));
      const lp = lineaPalabra(palabra, catalogo, lento);
      const fin = lp.claves[lp.claves.length - 2].t, mover = a - lp.sonidoEn;
      claves.push({ t: ir, pose: R });
      for (const k of lp.claves) if (k.t >= lp.sonidoEn - 0.05 && k.t <= fin) claves.push({ ...k, t: k.t + mover });
      for (const x of lp.aspiracion ?? []) aspiracion.push({ en: x.en + mover, dura: x.dura });
      libre = fin + mover;
      return;
    }
    if (m === 'oclusiva') {
      const cierre = Math.max(libre + 0.05, a - 0.3);
      claves.push({ t: Math.max(libre, cierre - 0.3), pose: R }, { t: cierre, pose: PA }, { t: a, pose: PA },
        { t: a + 0.08, pose: PA, hacia: R, f: 0.5 }, { t: Math.max(a + 0.35, b), pose: R });
      if (!pose.sonora) aspiracion.push({ en: a + 0.08, dura: soploDe(pose) });
      libre = Math.max(a + 0.35, b);
    } else if (m === 'africada' && PB) {
      claves.push({ t: ir, pose: R }, { t: a - 0.05, pose: PA }, { t: a + 0.05, pose: PB }, { t: b, pose: PB }, { t: b + 0.3, pose: R });
      libre = b + 0.3;
    } else if (m === 'diptongo' && PB) {
      claves.push({ t: ir, pose: R }, { t: a, pose: PA }, { t: b, pose: PB }, { t: b + 0.3, pose: R });
      libre = b + 0.3;
    } else {
      claves.push({ t: ir, pose: R }, { t: a, pose: PA }, { t: b, pose: PA }, { t: b + 0.3, pose: R });
      libre = b + 0.3;
    }
  });
  const total = Math.max(libre, L + duracion) + 0.2;
  claves.push({ t: total, pose: R });
  // Instantes estrictamente crecientes (huecos muy cortos entre tramos).
  for (let i = 1; i < claves.length; i++) if (claves[i].t <= claves[i - 1].t) claves[i] = { ...claves[i], t: claves[i - 1].t + 0.01 };
  const linea: Linea = { total: claves[claves.length - 1].t, claves, quieta: PA, sonidoEn: L + silencio };
  if (aspiracion.length) linea.aspiracion = aspiracion;
  return linea;
}

/** Una frase o un párrafo leído por el TTS (Miguel, 24 sep: «que el modelo
 *  3D nos lea el texto en tiempo real»). Las palabras se reparten entre los
 *  tramos que suenan del audio en proporción a lo que duran sus sonidos (una
 *  pausa del audio cae entre las palabras que le tocan), y en cada tramo la
 *  boca las articula seguidas, estiradas a lo que dura el tramo. Entre tramos,
 *  la boca vuelve al reposo. Mismo arranque que `alCompasDeTramos`: el archivo
 *  empieza cuando la línea va por `ADELANTO`. Sin sonidos, null. */
export function lineaFrase(palabras: Segmento[][], catalogo: CatalogoPoses,
                           tramos: { inicio: number; fin: number }[], silencio: number, duracion: number,
                           marcas?: (Marca | null | undefined)[]): Linea | null {
  const llenas = palabras.filter(p => p.length);
  if (!llenas.length) return null;
  const alineada = marcas ? lineaFraseAlineada(palabras, catalogo, marcas, silencio, duracion) : null;
  if (alineada) return alineada;
  const R = catalogo.reposo, L = ADELANTO;
  // Sin tramos medidos (audio por <audio>, sin Web Audio): todo lo que suena.
  const tr = tramos.length ? tramos : [{ inicio: silencio, fin: Math.max(silencio + 0.3, duracion - 0.15) }];
  const pesos = llenas.map(p => duracionSegmentos(p, catalogo));
  const totalPeso = pesos.reduce((a, b) => a + b, 0);
  const largos = tr.map(t => Math.max(0, t.fin - t.inicio));
  const totalVoz = largos.reduce((a, b) => a + b, 0) || 1;
  const grupos: Segmento[][] = tr.map(() => []);
  let acum = 0;
  llenas.forEach((p, i) => {
    const medio = (acum + pesos[i] / 2) / totalPeso * totalVoz;
    acum += pesos[i];
    let k = 0;
    for (let c = largos[0]; k < tr.length - 1 && medio >= c; c += largos[++k]) { /* busca el tramo */ }
    grupos[k].push(...p);
  });
  const claves: Clave[] = [{ t: 0, pose: R }];
  const aspiracion: { en: number; dura: number }[] = [];
  let libre = 0;
  tr.forEach(({ inicio, fin }, k) => {
    const segs = grupos[k];
    if (!segs.length) return;
    const a = L + inicio, b = Math.max(a + 0.1, L + fin);
    const lento = Math.min(3, Math.max(0.2, (b - a) / Math.max(1e-6, duracionSegmentos(segs, catalogo))));
    const lp = lineaPalabra(segs, catalogo, lento);
    // La boca se adelanta un poco al sonido (coarticulación anticipatoria).
    const mover = a - lp.sonidoEn - 0.04;
    claves.push({ t: Math.max(libre, a - 0.2), pose: R });
    for (const c of lp.claves.slice(2, -2)) claves.push({ ...c, t: c.t + mover });
    for (const x of lp.aspiracion ?? []) aspiracion.push({ en: x.en + mover, dura: x.dura });
    libre = b + 0.18;
    claves.push({ t: libre, pose: R });
  });
  const total = Math.max(libre, L + duracion) + 0.2;
  claves.push({ t: total, pose: R });
  for (let i = 1; i < claves.length; i++) if (claves[i].t <= claves[i - 1].t) claves[i] = { ...claves[i], t: claves[i - 1].t + 0.01 };
  const linea: Linea = { total: claves[claves.length - 1].t, claves, quieta: R, sonidoEn: L + silencio };
  if (aspiracion.length) linea.aspiracion = aspiracion;
  return linea;
}

export function retrasoAudio(sonidoEnLento: number, silencio: number, velocidadAudio: number): number {
  return sonidoEnLento - silencio / (velocidadAudio > 0 ? velocidadAudio : 1);
}

function objetivos(pose: PoseSonido, vecino: PoseSonido, reposo: PoseSonido): [PoseSonido, PoseSonido | null] {
  const a = resolver(pose, vecino);
  let b: PoseSonido | null = null;
  if (pose.hacia) {
    b = pose.movimiento === 'diptongo' ? resolver(pose.hacia, reposo) : resolver(pose.hacia, a);
  }
  return [a, b];
}

/** Un sonido que lo deja todo libre (/h/: la boca ya está en la vocal) no
 *  se distingue del reposo. Para que se vea algo, abre la mandíbula. */
function conAlgoQueVer(pose: PoseSonido, resuelta: PoseSonido, R: PoseSonido): PoseSonido {
  const libres = pose.libres ?? [];
  const todoLibre = (['mandibula', 'labios', 'punta', 'cuerpo'] as const).every(c => libres.includes(c));
  return todoLibre ? { ...resuelta, mandibula: Math.max(resuelta.mandibula, R.mandibula + 0.25) } : resuelta;
}

/** Cuánto gira la cámara hacia la cara (radianes de azimut, negativo = hacia
 *  la cara) durante el ciclo de un sonido: lo que pasa en los labios —el
 *  fruncido de /u/, el estiramiento de /i/— se ve de frente, no de lado. */
export function giroPara(pose: PoseSonido): number {
  return pose.labios === 'redondeados' || pose.labios === 'muy_redondeados' || pose.labios === 'estirados'
    ? -(30 * Math.PI) / 180 : 0;
}

/** Reposo → sonido → reposo, en un ciclo de 2,8 s. */
export function cicloSonido(pose: PoseSonido, catalogo: CatalogoPoses): Linea {
  const R = catalogo.reposo;
  const [PA0, PB] = objetivos(pose, R, R);
  const PA = conAlgoQueVer(pose, PA0, R);
  const m = pose.movimiento;
  let claves: Clave[];
  if (m === 'oclusiva') {
    claves = [{ t: 0, pose: R }, { t: 0.42, pose: R }, { t: 0.95, pose: PA }, { t: 1.5, pose: PA },
      { t: 1.6, pose: PA, hacia: R, f: 0.5 }, { t: 2.25, pose: R }, { t: 2.8, pose: R }];
  } else if (m === 'africada' && PB) {
    claves = [{ t: 0, pose: R }, { t: 0.4, pose: R }, { t: 0.9, pose: PA }, { t: 1.3, pose: PA },
      { t: 1.7, pose: PB }, { t: 1.95, pose: PB }, { t: 2.45, pose: R }, { t: 2.8, pose: R }];
  } else if (m === 'diptongo' && PB) {
    claves = [{ t: 0, pose: R }, { t: 0.35, pose: R }, { t: 0.8, pose: PA }, { t: 1.05, pose: PA },
      { t: 1.7, pose: PB }, { t: 1.95, pose: PB }, { t: 2.45, pose: R }, { t: 2.8, pose: R }];
  } else {
    let t: [number, number, number, number];
    if (m === 'vocal') t = pose.larga ? [0.45, 0.95, 1.95, 2.45] : [0.6, 1.05, 1.6, 2.15];
    else if (m === 'aproximante') t = [0.5, 1.0, 1.7, 2.3];
    else t = [0.42, 0.95, 1.9, 2.45];
    claves = [{ t: 0, pose: R }, { t: t[0], pose: R }, { t: t[1], pose: PA }, { t: t[2], pose: PA },
      { t: t[3], pose: R }, { t: 2.8, pose: R }];
  }
  // El sonido suena cuando la boca llega a la pose (la tercera clave en
  // todos los casos), no cuando arranca el movimiento.
  const linea: Linea = { total: 2.8, claves, quieta: PA, sonidoEn: claves[2].t };
  // La «suelta» de la oclusiva sorda (la clave con `hacia`) lleva el soplo.
  if (m === 'oclusiva' && !pose.sonora) linea.aspiracion = [{ en: claves[4].t, dura: soploDe(pose) }];
  return linea;
}

/** Si la oclusiva `i` de la palabra lleva soplo. Solo la sorda que se suelta
 *  hacia una vocal o /l ɹ w j/ (pin, play, try); tras /s/ no hay aspiración
 *  (spin, stop, sky) y al final, o ante otra consonante, no se suelta con
 *  soplo (hot, act). Ladefoged y Johnson (2011, cap. 3); Cruttenden (2014).
 *  El ciclo de un sonido suelto sí lo lleva: es la suelta ante el reposo. */
export function seAspira(segmentos: Segmento[], i: number): boolean {
  const s = segmentos[i];
  if (s.pose.movimiento !== 'oclusiva' || s.pose.sonora) return false;
  if (segmentos[i - 1]?.simbolo === 's') return false;
  const sig = segmentos[i + 1]?.pose.movimiento;
  return sig === 'vocal' || sig === 'diptongo' || sig === 'aproximante';
}

/** Cuánto duran los sonidos de una palabra (sin reposos), a `lento` = 1. */
function duracionSegmentos(segmentos: Segmento[], catalogo: CatalogoPoses): number {
  return segmentos.reduce((suma, s) => {
    let d = (catalogo.duracion_s[s.pose.movimiento] ?? DURACION_S[s.pose.movimiento]) * (s.pose.larga ? 1.25 : 1);
    d *= s.acento_silaba === 1 ? 1.4 : s.acento_silaba === 2 ? 1.15 : 1;
    return suma + d;
  }, 0);
}

/** El factor de `lineaPalabra` que hace que la palabra dure lo que dura su
 *  audio: la parte hablada del audio (sin el silencio inicial que trae el
 *  TTS y un poco de cola) repartida entre los sonidos. Acotado para que un
 *  audio raro no deje la boca parada ni frenética. */
/** Dónde suena una palabra en su audio, en segundos desde el principio del
 *  archivo (las marcas de whisper que la API guarda al lado del mp3). */
export interface Marca { inicio: number; fin: number }

/** Hueco entre dos palabras a partir del cual la boca vuelve al reposo. */
export const PAUSA_ENTRE_PALABRAS = 0.25;

/** «Alinea el TTS» (Miguel, 25 sep): con las marcas por palabra del audio,
 *  cada palabra se articula en su sitio, estirada a lo que dura de verdad, en
 *  vez de repartir las palabras por el tramo según sus duraciones de regla.
 *  Medido en GRID (4 hablantes de prueba, 4 000 frases): con las mismas poses
 *  y el mismo calendario dentro de la palabra, la correlación con la boca
 *  real sube de 0,31 a 0,42 (`investigacion/modelo_articulatorio/`). Las
 *  palabras sin marca se colocan entre sus vecinas por su duración de regla;
 *  con menos de la mitad marcadas, null (se usa el reparto por tramos). */
export function lineaFraseAlineada(palabras: Segmento[][], catalogo: CatalogoPoses, marcas: (Marca | null | undefined)[],
                                   silencio: number, duracion: number): Linea | null {
  const idx = palabras.map((p, i) => i).filter(i => palabras[i].length);
  const valida = (m: Marca | null | undefined): m is Marca =>
    !!m && Number.isFinite(m.inicio) && Number.isFinite(m.fin) && m.fin > m.inicio;
  const conMarca = idx.filter(i => valida(marcas[i]));
  if (!idx.length || conMarca.length * 2 < idx.length) return null;
  // Tiempos de cada palabra: los marcados tal cual (crecientes); los demás,
  // repartidos por peso en el hueco entre las vecinas marcadas.
  const pesos = idx.map(i => duracionSegmentos(palabras[i], catalogo));
  const t: (Marca | null)[] = idx.map(i => (valida(marcas[i]) ? { inicio: marcas[i]!.inicio, fin: marcas[i]!.fin } : null));
  for (let k = 1; k < t.length; k++) {
    const a = t[k - 1], b = t[k];
    if (a && b && b.inicio < a.fin) t[k] = null;          // marca fuera de orden: se recoloca
  }
  for (let k = 0; k < t.length;) {
    if (t[k]) { k++; continue; }
    let j = k;
    while (j < t.length && !t[j]) j++;
    const peso = pesos.slice(k, j).reduce((x, y) => x + y, 0);
    const antes = k > 0 ? t[k - 1]!.fin : null, despues = j < t.length ? t[j]!.inicio : null;
    let desde = antes ?? Math.max(0, (despues ?? 0) - peso), hasta = despues ?? (antes ?? 0) + peso;
    if (hasta - desde < 0.05 * (j - k)) hasta = desde + 0.05 * (j - k);
    let c = desde;
    for (let q = k; q < j; q++) {
      const d = (hasta - desde) * pesos[q] / (peso || 1);
      t[q] = { inicio: c, fin: c + d };
      c += d;
    }
    k = j;
  }
  const R = catalogo.reposo, L = ADELANTO;
  const claves: Clave[] = [{ t: 0, pose: R }];
  const aspiracion: { en: number; dura: number }[] = [];
  let libre = 0, finAnterior = -Infinity;
  idx.forEach((i, k) => {
    const segs = palabras[i], m = t[k]!;
    const a = L + m.inicio, b = Math.max(a + 0.06, L + m.fin);
    if (a - finAnterior >= PAUSA_ENTRE_PALABRAS) {
      // Pausa (o primera palabra): la boca vuelve al reposo entre medias.
      if (Number.isFinite(finAnterior)) { libre = finAnterior + 0.18; claves.push({ t: libre, pose: R }); }
      claves.push({ t: Math.max(libre, a - 0.2), pose: R });
    }
    const lento = Math.min(3, Math.max(0.15, (b - a) / Math.max(1e-6, duracionSegmentos(segs, catalogo))));
    const lp = lineaPalabra(segs, catalogo, lento);
    // Como en el reparto por tramos: la boca se adelanta 40 ms al sonido.
    const mover = a - lp.sonidoEn - 0.04;
    for (const c of lp.claves.slice(2, -2)) claves.push({ ...c, t: c.t + mover });
    for (const x of lp.aspiracion ?? []) aspiracion.push({ en: x.en + mover, dura: x.dura });
    finAnterior = b;
    libre = b;
  });
  libre = finAnterior + 0.18;
  claves.push({ t: libre, pose: R });
  const total = Math.max(libre, L + duracion) + 0.2;
  claves.push({ t: total, pose: R });
  for (let i = 1; i < claves.length; i++) if (claves[i].t <= claves[i - 1].t) claves[i] = { ...claves[i], t: claves[i - 1].t + 0.01 };
  const linea: Linea = { total: claves[claves.length - 1].t, claves, quieta: R, sonidoEn: L + silencio };
  if (aspiracion.length) linea.aspiracion = aspiracion;
  return linea;
}

export function lentoParaAudio(segmentos: Segmento[], catalogo: CatalogoPoses, duracionAudioS: number,
                               silencioInicialS = 0.12, silencioFinalS = 0.15): number {
  const base = duracionSegmentos(segmentos, catalogo);
  if (!(base > 0) || !(duracionAudioS > 0)) return LENTO;
  const hablado = Math.max(0.2, duracionAudioS - silencioInicialS - silencioFinalS);
  return Math.min(3, Math.max(0.35, hablado / base));
}

/** La palabra entera: cada sonido con su duración (`DURACION_S`, larga ×1,25,
 *  acento ×1,4 o ×1,15, todo ×`lento`), los consonantes coarticulados con la
 *  vocal vecina, y el reposo al principio y al final. */
export function lineaPalabra(segmentos: Segmento[], catalogo: CatalogoPoses, lento = LENTO,
                             conModelo = MODELO_ARTICULATORIO_ACTIVO): Linea {
  const R = catalogo.reposo;
  const poses = segmentos.map(s => s.pose);
  const vocales = poses.map((p, i) => (p.movimiento === 'vocal' || p.movimiento === 'diptongo' ? i : -1)).filter(i => i >= 0);
  const vecino = (i: number): PoseSonido => {
    const sig = vocales.find(j => j > i);
    if (sig !== undefined) return resolver(poses[sig], R);
    const ant = [...vocales].reverse().find(j => j < i);
    if (ant !== undefined) {
      const a = poses[ant];
      return a.hacia ? resolver(a.hacia, R) : resolver(a, R);
    }
    return R;
  };
  const durs = segmentos.map(s => duracionSegmentos([s], catalogo) * lento);
  const inicio = 0.45;
  const total = inicio + durs.reduce((a, b) => a + b, 0) + 1.0;
  const claves: Clave[] = [{ t: 0, pose: R }, { t: inicio - 0.05, pose: R }];
  const aspiracion: { en: number; dura: number }[] = [];
  const tramos: TramoFonema[] = [];
  let t = inicio;
  segmentos.forEach((s, i) => {
    const d = durs[i];
    const [PA, PB] = objetivos(s.pose, vecino(i), R);
    const m = s.pose.movimiento;
    // Para el modelo: el tramo de cada sonido con su pose resuelta; diptongos y
    // africadas en dos mitades (primer y segundo objetivo).
    if (PB && (m === 'diptongo' || m === 'africada')) {
      tramos.push({ simbolo: s.simbolo, pose: PA, t0: t, t1: t + d / 2 }, { simbolo: s.simbolo, pose: PB, t0: t + d / 2, t1: t + d });
    } else {
      tramos.push({ simbolo: s.simbolo, pose: conAlgoQueVer(s.pose, PA, R), t0: t, t1: t + d });
    }
    if (m === 'oclusiva') {
      claves.push({ t: t + 0.45 * d, pose: PA }, { t: t + 0.8 * d, pose: PA });
      if (seAspira(segmentos, i)) aspiracion.push({ en: t + 0.8 * d, dura: soploDe(s.pose) * lento });
    } else if (m === 'africada' && PB) {
      claves.push({ t: t + 0.3 * d, pose: PA }, { t: t + 0.5 * d, pose: PA }, { t: t + 0.8 * d, pose: PB }, { t: t + 0.95 * d, pose: PB });
    } else if (m === 'diptongo' && PB) {
      claves.push({ t: t + 0.2 * d, pose: PA }, { t: t + 0.35 * d, pose: PA }, { t: t + 0.85 * d, pose: PB });
    } else {
      claves.push({ t: t + 0.38 * d, pose: PA }, { t: t + 0.72 * d, pose: PA });
    }
    t += d;
  });
  if (conModelo && tramos.length) {
    // 25 sep: el modelo aprendido (GRID) sustituye el calendario de reglas
    // entre el primer y el último sonido; el reposo de los extremos no cambia.
    claves.splice(2, claves.length - 2, ...clavesModelo(tramos, R, inicio, t));
  }
  claves.push({ t: t + 0.45, pose: R }, { t: total, pose: R });
  // La pose quieta: la vocal acentuada, o la primera vocal, o el primer sonido.
  const fija = vocales.find(i => segmentos[i].acento_silaba === 1) ?? vocales[0] ?? 0;
  const quieta = segmentos.length ? objetivos(segmentos[fija].pose, vecino(fija), R)[0] : R;
  return { total, claves, quieta, sonidoEn: inicio, aspiracion: aspiracion.length ? aspiracion : undefined };
}
