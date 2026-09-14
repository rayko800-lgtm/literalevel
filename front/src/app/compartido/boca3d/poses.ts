/** El contrato de poses del visor 3D de la boca.
 *
 *  Es la misma tabla que `app/animacion_articulatoria.PARAMETROS` (46 sonidos),
 *  ya resuelta contra el reposo: ningún campo queda libre. La genera
 *  `tools/exportar_poses_boca3d.py` en `poses.ejemplo.json`, que es lo que la
 *  API podría servir después. Mientras tanto el visor lleva embebidos el reposo
 *  y los cinco sonidos del prototipo. */

export type Movimiento = 'oclusiva' | 'fricativa' | 'africada' | 'nasal' | 'aproximante' | 'vocal' | 'diptongo';
export type Labios = 'neutros' | 'cerrados' | 'redondeados' | 'muy_redondeados' | 'estirados' | 'labiodental';
export type Punta = 'reposo' | 'interdental' | 'dental' | 'alveolar' | 'postalveolar' | 'retrofleja';

export interface PoseSonido {
  movimiento: Movimiento;
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
    movimiento: 'oclusiva', mandibula: 0.08, labios: 'cerrados', punta: 'reposo', punta_toca: false,
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
    movimiento: 'nasal', mandibula: 0.25, labios: 'neutros', punta: 'reposo', punta_toca: false,
    cuerpo: [0.45, 0.3], dorso_velo: true, dorso_alto: 0, raiz: 0, velo_abierto: true,
    sonora: true, lugar: 'velar', larga: false,
    leyenda: 'dorso contra el velo bajado; aire por la nariz, sin soltar g',
  },
};

export const CATALOGO_PROTOTIPO: CatalogoPoses = {
  version: 1, duracion_s: DURACION_S, reposo: REPOSO, sonidos: POSES_PROTOTIPO,
};

/** La pose de un símbolo en un catálogo, o `null` si no la trae. */
export function poseDe(catalogo: CatalogoPoses, simbolo: string, acento: 'ga' | 'rp' = 'ga'): PoseSonido | null {
  const s = simbolo.normalize('NFC').trim().replace(/^\/|\/$/g, '');
  if (!s) return catalogo.reposo;
  if (acento === 'rp' && catalogo.rp?.[s]) return catalogo.rp[s];
  return catalogo.sonidos[s] ?? null;
}
