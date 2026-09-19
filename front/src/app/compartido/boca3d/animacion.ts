/** Líneas de tiempo del visor 3D: el ciclo de un sonido (reposo → sonido →
 *  reposo, 2,8 s) y una palabra entera, con los mismos instantes y las mismas
 *  duraciones que el corte 2D (`_linea_sonido` y `_linea_palabra` de
 *  `app/animacion_articulatoria`). Sin three.js: solo poses y segundos. */
import { CatalogoPoses, DURACION_S, PoseSonido, Segmento, resolver } from './poses';

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
}

/** El factor de «despacio» de las palabras del 2D. */
export const LENTO = 1.6;

/** Las cuatro velocidades discretas que ofrece Pronunciar. */
export const VELOCIDADES = [0.25, 0.5, 1, 1.25] as const;
export type Velocidad = (typeof VELOCIDADES)[number];

/** La misma línea, `velocidad` veces más rápida (0,5 = el doble de larga):
 *  todos los instantes se dividen por la velocidad, incluido `sonidoEn`. */
export function aVelocidad(linea: Linea, velocidad: number): Linea {
  const v = velocidad > 0 ? velocidad : 1;
  if (v === 1) return linea;
  return { ...linea, total: linea.total / v, sonidoEn: linea.sonidoEn / v,
    claves: linea.claves.map(c => ({ ...c, t: c.t / v })) };
}

/** Cuándo arrancar el audio (segundos desde el arranque de la línea) para
 *  que su primera energía caiga en `sonidoEn` de la línea ya ralentizada:
 *  el silencio inicial del archivo dura `silencio / velocidadAudio` al
 *  reproducirlo a esa velocidad (1 si el navegador no pudo ralentizarlo). */
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
  return { total: 2.8, claves, quieta: PA, sonidoEn: claves[2].t };
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
export function lineaPalabra(segmentos: Segmento[], catalogo: CatalogoPoses, lento = LENTO): Linea {
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
  let t = inicio;
  segmentos.forEach((s, i) => {
    const d = durs[i];
    const [PA, PB] = objetivos(s.pose, vecino(i), R);
    const m = s.pose.movimiento;
    if (m === 'oclusiva') {
      claves.push({ t: t + 0.45 * d, pose: PA }, { t: t + 0.8 * d, pose: PA });
    } else if (m === 'africada' && PB) {
      claves.push({ t: t + 0.3 * d, pose: PA }, { t: t + 0.5 * d, pose: PA }, { t: t + 0.8 * d, pose: PB }, { t: t + 0.95 * d, pose: PB });
    } else if (m === 'diptongo' && PB) {
      claves.push({ t: t + 0.2 * d, pose: PA }, { t: t + 0.35 * d, pose: PA }, { t: t + 0.85 * d, pose: PB });
    } else {
      claves.push({ t: t + 0.38 * d, pose: PA }, { t: t + 0.72 * d, pose: PA });
    }
    t += d;
  });
  claves.push({ t: t + 0.45, pose: R }, { t: total, pose: R });
  // La pose quieta: la vocal acentuada, o la primera vocal, o el primer sonido.
  const fija = vocales.find(i => segmentos[i].acento_silaba === 1) ?? vocales[0] ?? 0;
  const quieta = segmentos.length ? objetivos(segmentos[fija].pose, vecino(fija), R)[0] : R;
  return { total, claves, quieta, sonidoEn: inicio };
}
