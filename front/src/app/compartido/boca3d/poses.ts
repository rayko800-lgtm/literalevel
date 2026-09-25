/** El contrato de poses del visor 3D de la boca.
 *
 *  Es la misma tabla que `app/animacion_articulatoria.PARAMETROS` (46 sonidos),
 *  ya resuelta contra el reposo: ningún campo queda libre. La genera
 *  `tools/exportar_poses_boca3d.py` en `poses.ejemplo.json`, que es lo que la
 *  API podria servir despues. El visor integrado usa ese snapshot completo;
 *  las cinco poses del prototipo se conservan para las pruebas aisladas. */

export type Movimiento = 'oclusiva' | 'fricativa' | 'africada' | 'nasal' | 'aproximante' | 'vocal' | 'diptongo';
export type Labios = 'neutros' | 'cerrados' | 'redondeados' | 'muy_redondeados' | 'estirados' | 'labiodental';
export type Punta = 'reposo' | 'interdental' | 'dental' | 'alveolar' | 'postalveolar' | 'retrofleja';

/** Familia articulatoria por articulador protagonista (D4.2, diseño
 *  aprobado 18 sep): agrupa fonemas que enseñan el mismo gesto, para elegir
 *  un preset de cámara por familia y no uno por cada símbolo. */
export type Familia =
  | 'bilabial' | 'nasal-bilabial' | 'labiodental' | 'dental' | 'alveolar' | 'postalveolar' | 'rotico' | 'velar' | 'vocal';

export type CampoLibre = 'mandibula' | 'labios' | 'punta' | 'cuerpo';

export interface PoseSonido {
  movimiento: Movimiento;
  /** Campos que la tabla deja libres: en una palabra los pone la vocal
   *  vecina (`resolver`), no el reposo. `cuerpo` arrastra raíz y dorso. */
  libres?: CampoLibre[];
  /** Apertura de la mandíbula: 0 dientes juntos, 1 muy abierta. */
  mandibula: number;
  labios: Labios;
  punta: Punta;
  /** La punta llega a tocar (oclusivas, nasales, /l/). */
  punta_toca: boolean;
  /** Cuerpo de la lengua: [altura, adelantamiento], 0..1. */
  cuerpo: [number, number];
  /** El dorso cierra contra el velo (/k ɡ ŋ/). */
  dorso_velo: boolean;
  /** Elevación extra del dorso sin tocar (l oscura, /w/). */
  dorso_alto: number;
  /** Retracción de la raíz hacia la faringe, 0..1. */
  raiz: number;
  /** Lote fase 1 (3D solo, no viene del 2D): rótica de GA (/ɹ ɝ ɚ/, lengua
   *  abombada con la raíz contra la faringe) o /r/ de RP; manda la pose a la
   *  familia `rotico`, que desde el lote encuadra también la faringe. */
  rotica?: boolean;
  /** El velo baja y abre la nariz (nasales). */
  velo_abierto: boolean;
  sonora: boolean;
  lugar: string;
  larga: boolean;
  leyenda: string;
  /** Segundo objetivo: diptongos y la fase fricativa de las africadas. */
  hacia?: PoseSonido;
}

/** Lo que exporta el guion: reposo, sonidos por símbolo y duraciones. */
export interface CatalogoPoses {
  version: number;
  duracion_s: Partial<Record<Movimiento, number>>;
  reposo: PoseSonido;
  sonidos: Record<string, PoseSonido>;
  /** Lo que el británico articula distinto, por símbolo RP. */
  rp?: Record<string, PoseSonido>;
}

/** Lote fase 1 (22 sep 2026): lo que el 3D cambia sobre la exportación del 2D
 *  congelado, por símbolo (campos sueltos de la pose). Vive en
 *  `poses.ajustes3d.json` para que `poses.ejemplo.json` siga siendo la
 *  exportación intacta de `tools/exportar_poses_boca3d.py`; cada entrada está
 *  justificada en `auditoria/d4_4b_lote/divergencias_2d_3d.md`. */
export interface AjustesPoses3d {
  origen?: string;
  sonidos?: Record<string, Partial<PoseSonido>>;
  /** Un símbolo RP sin entrada propia en `rp` parte de su pose de GA. */
  rp?: Record<string, Partial<PoseSonido>>;
}

/** El catálogo exportado con los ajustes del 3D encima. La misma regla en
 *  `lengua.py` (comprobación) y `tools/boca3d_demo/medir_lengua.mjs`. */
export function conAjustes3d(catalogo: CatalogoPoses, ajustes: AjustesPoses3d): CatalogoPoses {
  const sonidos: Record<string, PoseSonido> = { ...catalogo.sonidos };
  for (const [s, extra] of Object.entries(ajustes.sonidos ?? {})) if (sonidos[s]) sonidos[s] = { ...sonidos[s], ...extra };
  const rp: Record<string, PoseSonido> = { ...(catalogo.rp ?? {}) };
  for (const [s, extra] of Object.entries(ajustes.rp ?? {})) {
    const base = rp[s] ?? sonidos[s];
    if (base) rp[s] = { ...base, ...extra };
  }
  // 25 sep (Miguel): en el 3D el reposo es respirar en silencio. Marcado como
  // sonoro, el punto de vibración latía en la garganta antes y después de
  // sonidos sordos como /f/, y parecía que /f/ vibraba.
  return { ...catalogo, reposo: { ...catalogo.reposo, sonora: false }, sonidos, rp };
}

export const REPOSO: PoseSonido = {
  movimiento: 'vocal', mandibula: 0.2, labios: 'neutros', punta: 'reposo', punta_toca: false,
  cuerpo: [0.45, 0.5], dorso_velo: false, dorso_alto: 0, raiz: 0, velo_abierto: false,
  sonora: true, lugar: '', larga: false, leyenda: 'boca en reposo',
};

/** Segundos que dura cada tipo de sonido en una palabra (`_DURACION` del 2D). */
export const DURACION_S: Record<Movimiento, number> = {
  vocal: 0.34, diptongo: 0.46, oclusiva: 0.2, africada: 0.28, fricativa: 0.22, nasal: 0.2, aproximante: 0.18,
};

/** Los cinco sonidos del prototipo, copiados de `poses.ejemplo.json`. */
export const POSES_PROTOTIPO: Record<string, PoseSonido> = {
  p: {
    movimiento: 'oclusiva', libres: ['punta', 'cuerpo'],
    mandibula: 0.08, labios: 'cerrados', punta: 'reposo', punta_toca: false,
    cuerpo: [0.45, 0.5], dorso_velo: false, dorso_alto: 0, raiz: 0, velo_abierto: false,
    sonora: false, lugar: 'bilabial', larga: false,
    leyenda: 'labios cerrados que se abren de golpe, con soplo',
  },
  s: {
    movimiento: 'fricativa', mandibula: 0.1, labios: 'estirados', punta: 'alveolar', punta_toca: false,
    cuerpo: [0.62, 0.65], dorso_velo: false, dorso_alto: 0, raiz: 0, velo_abierto: false,
    sonora: false, lugar: 'alveolar', larga: false,
    leyenda: 'punta cerca del alvéolo sin tocarlo; aire afilado',
  },
  i: {
    movimiento: 'vocal', mandibula: 0.12, labios: 'estirados', punta: 'reposo', punta_toca: false,
    cuerpo: [1.0, 1.0], dorso_velo: false, dorso_alto: 0, raiz: 0, velo_abierto: false,
    sonora: true, lugar: '', larga: true,
    leyenda: 'lengua alta y adelante, labios estirados; larga y tensa',
  },
  ɑ: {
    movimiento: 'vocal', mandibula: 0.92, labios: 'neutros', punta: 'reposo', punta_toca: false,
    cuerpo: [0.05, 0.05], dorso_velo: false, dorso_alto: 0, raiz: 0.8, velo_abierto: false,
    sonora: true, lugar: '', larga: true,
    leyenda: 'boca muy abierta, lengua baja y atrás; larga',
  },
  ŋ: {
    movimiento: 'nasal', libres: ['labios', 'punta'],
    mandibula: 0.25, labios: 'neutros', punta: 'reposo', punta_toca: false,
    cuerpo: [0.45, 0.3], dorso_velo: true, dorso_alto: 0, raiz: 0, velo_abierto: true,
    sonora: true, lugar: 'velar', larga: false,
    leyenda: 'dorso contra el velo bajado; aire por la nariz, sin soltar g',
  },
};

export const CATALOGO_PROTOTIPO: CatalogoPoses = {
  version: 1, duracion_s: DURACION_S, reposo: REPOSO, sonidos: POSES_PROTOTIPO,
};

/** La pose de un símbolo en un catálogo, o `null` si no la trae. Acepta los
 *  símbolos tal como los da la API en cada inventario (`/api/fonemas`): en RP,
 *  «iː», «ɑː», «uː» y «r» caen en «i», «ɑ», «u» y «ɹ», como en el 2D. */
export function poseDe(catalogo: CatalogoPoses, simbolo: string, acento: 'ga' | 'rp' = 'ga'): PoseSonido | null {
  const s = normalizarSimbolo(simbolo.normalize('NFC').trim().replace(/^\/|\/$/g, ''), acento);
  if (!s) return catalogo.reposo;
  if (acento === 'rp' && catalogo.rp?.[s]) return catalogo.rp[s];
  const corto = s.replace(/ː/g, '');
  return catalogo.sonidos[s] ?? catalogo.sonidos[corto] ?? catalogo.sonidos[PARECIDOS[corto] ?? ''] ?? null;
}

/** La familia de una pose: el mismo criterio que agrupa `PARAMETROS` en el
 *  2D por articulador protagonista. Los róticos (punta retrofleja: /ɹ ɝ ɚ/)
 *  se separan de alveolares/postalveolares aunque compartan `lugar`, porque
 *  lo que hay que enseñar es justo que la punta se curva sin tocar. `/h/`
 *  (glotal) y el reposo no tienen articulador protagonista: caen en la
 *  vista general de `vocal`. */
export function familiaDe(pose: PoseSonido): Familia {
  // Lote fase 1: la /ɹ/ de GA pasa de retrofleja a abombada (punta en reposo),
  // así que la familia la decide el campo `rotica`; la retrofleja sigue siendo rótica.
  if (pose.punta === 'retrofleja' || pose.rotica) return 'rotico';
  if (pose.movimiento === 'nasal' && pose.lugar === 'bilabial') return 'nasal-bilabial';
  switch (pose.lugar) {
    case 'bilabial': return 'bilabial';
    case 'labiodental': return 'labiodental';
    case 'interdental': return 'dental';
    case 'alveolar': return 'alveolar';
    case 'postalveolar': return 'postalveolar';
    case 'velar': return 'velar';
    // Vocales y diptongos (lugar vacío), /h/ (glotal) y el reposo: sin
    // articulador protagonista, vista general.
    default: return 'vocal';
  }
}

/** Rellena los campos libres de `pose` con los del vecino (una vocal, o el
 *  reposo), como hace el 2D antes de dibujar una palabra. */
export function resolver(pose: PoseSonido, vecino: PoseSonido): PoseSonido {
  const libres = pose.libres ?? [];
  if (!libres.length) return pose;
  const r: PoseSonido = { ...pose, libres: [] };
  if (libres.includes('mandibula')) r.mandibula = vecino.mandibula;
  if (libres.includes('labios')) r.labios = vecino.labios;
  // La punta solo se hereda de una vocal: una consonante vecina no la presta.
  if (libres.includes('punta') && (vecino.movimiento === 'vocal' || vecino.movimiento === 'diptongo')) {
    r.punta = vecino.punta;
  }
  if (libres.includes('cuerpo')) {
    r.cuerpo = vecino.cuerpo; r.raiz = vecino.raiz; r.dorso_alto = vecino.dorso_alto;
  }
  return r;
}

// --- Trocear una transcripción -----------------------------------------------

export interface Segmento {
  simbolo: string;
  pose: PoseSonido;
  /** 0 sin acento, 1 primario (ˈ), 2 secundario (ˌ). */
  acento_silaba: 0 | 1 | 2;
}

const NO_SIGNIFICA = new Set([...'/[]()«»“”"`.‿ -', ...'̯̩͜͡ʰ̠̟̥̪̚ˑ']);
/** Grafías que nunca forman parte de una clave del catálogo: se cambian
 *  carácter a carácter. Nada de vocales aquí: «a» sí forma parte de «aɪ». */
const EQUIVALENTES: Record<string, string> = { g: 'ɡ', r: 'ɹ', ':': 'ː', ʧ: 'tʃ', ʤ: 'dʒ' };
/** Símbolos sueltos que no están en la tabla y caen en el más parecido; solo
 *  cuando el símbolo entero no se encuentra (`poseDe`). */
const PARECIDOS: Record<string, string> = { a: 'æ', e: 'ɛ', o: 'oʊ', ɐ: 'ʌ', ɫ: 'l', ɾ: 't', ʔ: 't' };
const GA_A_RP: Record<string, string> = { ɝ: 'ɜː', ɚ: 'ə' };

function normalizarSimbolo(s: string, acento: 'ga' | 'rp'): string {
  let t = '';
  for (const c of s) t += EQUIVALENTES[c] ?? c;
  return acento === 'rp' ? (GA_A_RP[t] ?? t) : t;
}

/** Los sonidos de una transcripción IPA, en orden, con los del catálogo; lo
 *  que no reconoce lo salta. Devuelve el texto limpio y los segmentos. La
 *  marca de acento (ˈ ˌ) se apunta a la siguiente vocal. Es una versión
 *  reducida de `trocear` del 2D: la API es quien manda si un día la sirve. */
export function trocearIpa(ipa: string, catalogo: CatalogoPoses, acento: 'ga' | 'rp' = 'ga'): { texto: string; segmentos: Segmento[] } {
  const texto = ipa.normalize('NFC').trim().replace(/^[/[]+|[/\]]+$/g, '');
  const sig: string[] = [];
  const marcas = new Map<number, 1 | 2>();
  for (const c of texto) {
    if (c === 'ˈ' || c === "'") marcas.set(sig.length, 1);
    else if (c === 'ˌ') marcas.set(sig.length, 2);
    else if (c === 'ː' || (!NO_SIGNIFICA.has(c) && !/\p{M}/u.test(c))) sig.push(c);
  }
  const claves = new Set([...Object.keys(catalogo.sonidos), ...Object.keys(catalogo.rp ?? {})]);
  const segmentos: Segmento[] = [];
  let pendiente: 0 | 1 | 2 = 0;
  for (let k = 0; k < sig.length;) {
    if (marcas.has(k)) pendiente = marcas.get(k)!;
    let hallado: { n: number; simbolo: string; pose: PoseSonido } | null = null;
    for (let n = Math.min(4, sig.length - k); n >= 1; n--) {
      const sub = sig.slice(k, k + n).join('');
      if (sub.startsWith('ː')) continue;
      const simbolo = normalizarSimbolo(sub, acento);
      if (!claves.has(simbolo)) continue;
      const pose = poseDe(catalogo, simbolo, acento);
      if (pose) { hallado = { n, simbolo, pose }; break; }
    }
    if (!hallado) { k++; continue; }
    segmentos.push({ simbolo: hallado.simbolo, pose: hallado.pose, acento_silaba: pendiente });
    if (hallado.pose.movimiento === 'vocal' || hallado.pose.movimiento === 'diptongo') pendiente = 0;
    k += hallado.n;
  }
  return { texto, segmentos };
}
