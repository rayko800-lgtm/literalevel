import { RitmoLectura } from '../nucleo/api';

/** Una palabra de la frase corregida con lo que se le pinta encima. */
export interface PalabraLeida {
  /** Posición en las palabras de la frase: los índices del ritmo apuntan aquí. */
  indice: number;
  texto: string;
  bien: boolean;
  /** Un signo suelto no se pinta (dejaba un subrayado sin nada encima). */
  visible: boolean;
  enfasis: boolean;
  /** Se une con la siguiente (arco ‿): el tipo, en palabras; null si no. */
  enlace: string | null;
  /** «Aquí sin pausa»: segundos de la pausa de más detrás de esta palabra. */
  sinPausaDespues: number | null;
  /** Dentro de un tramo leído más despacio que el objetivo de su nivel. */
  acelerar: boolean;
  /** Primera palabra de ese tramo. */
  empiezaAcelerar: boolean;
  /** Última palabra de ese tramo: detrás va «de corrido aquí» (propuesta A de Pronunciar). */
  terminaAcelerar: boolean;
}

export interface VistaRitmo {
  palabras: PalabraLeida[];
  /** Hubo marcas de tiempo del lector: solo entonces se dice dónde acelerar o no parar. */
  medido: boolean;
  /** Llegó el análisis de énfasis, enlaces y reducciones. */
  natural: boolean;
  reducciones: { texto: string; forma: string; ipa: string | null; ia: boolean }[];
  /** La frase dicha con naturalidad, solo si cambia algo respecto a la escrita. */
  versionNatural: string | null;
  audioNatural: string | null;
  /** Hay alguna marca de tiempo que pintar (para la leyenda). */
  hayMarcasDeTiempo: boolean;
  /** Alguna palabra lleva énfasis o arco ‿: la leyenda solo explica lo que se pinta (f4, prueba de persona). */
  hayEnfasis: boolean;
  hayEnlaces: boolean;
}

const TIPOS_DE_ENLACE: Record<string, string> = {
  consonante_vocal: 'consonante con vocal',
  vocal_vocal: 'vocal con vocal',
  r_de_enlace: 'r de enlace',
};

const normal = (t: string) => t.toLowerCase().replace(/[^\p{L}\p{N}' ]+/gu, ' ').replace(/\s+/g, ' ').trim();

/** Junta la corrección y el ritmo de voz.py (contrato de entrega-4e) en lo que
 *  pinta Pronunciar. Todo índice fuera de la frase se descarta aquí: la
 *  pantalla nunca se rompe por un dato raro. Sin `medido`, ni «aquí aceleras»
 *  ni «aquí sin pausa»: sin marcas de tiempo serían adivinadas. */
export function vistaRitmo(palabras: { palabra: string; bien: boolean }[],
                           ritmo: RitmoLectura | null | undefined): VistaRitmo {
  const n = palabras.length;
  const dentro = (i: unknown): i is number => Number.isInteger(i) && (i as number) >= 0 && (i as number) < n;
  const vista: PalabraLeida[] = palabras.map((w, i) => ({
    indice: i, texto: w.palabra, bien: w.bien, visible: /\p{L}/u.test(w.palabra),
    enfasis: false, enlace: null, sinPausaDespues: null, acelerar: false, empiezaAcelerar: false, terminaAcelerar: false,
  }));
  const medido = !!ritmo?.medido;
  let hayMarcasDeTiempo = false;
  if (ritmo && medido) {
    for (const p of ritmo.pausas ?? []) {
      // Una pausa detrás de la última palabra no es una pausa de la frase.
      if (p.de_mas && dentro(p.despues_de) && p.despues_de < n - 1) {
        vista[p.despues_de].sinPausaDespues = p.segundos;
        hayMarcasDeTiempo = true;
      }
    }
    for (const t of ritmo.tramos ?? []) {
      if (!t.acelerar || !dentro(t.desde) || !dentro(t.hasta) || t.hasta < t.desde) continue;
      vista[t.desde].empiezaAcelerar = true;
      vista[t.hasta].terminaAcelerar = true;
      for (let i = t.desde; i <= t.hasta; i++) vista[i].acelerar = true;
      hayMarcasDeTiempo = true;
    }
  }
  const nat = ritmo?.natural ?? null;
  const reducciones: VistaRitmo['reducciones'] = [];
  let versionNatural: string | null = null;
  if (nat) {
    for (const e of nat.enfasis ?? []) if (dentro(e.indice)) vista[e.indice].enfasis = true;
    for (const l of nat.enlaces ?? []) {
      if (dentro(l.de) && l.a === l.de + 1 && dentro(l.a)) vista[l.de].enlace = TIPOS_DE_ENLACE[l.tipo] ?? 'enlace';
    }
    for (const r of nat.reducciones ?? []) {
      if (!dentro(r.desde) || !dentro(r.hasta) || r.hasta < r.desde) continue;
      reducciones.push({ texto: palabras.slice(r.desde, r.hasta + 1).map(w => w.palabra).join(' '),
        forma: r.forma, ipa: r.ipa ?? null, ia: r.generado_por_ia !== false });
    }
    const v = (nat.version_natural ?? '').trim();
    if (v && normal(v) !== normal(palabras.map(w => w.palabra).join(' '))) versionNatural = v;
  }
  return {
    palabras: vista, medido, natural: !!nat, reducciones, versionNatural,
    audioNatural: nat?.audio_natural ?? null, hayMarcasDeTiempo,
    hayEnfasis: vista.some(p => p.enfasis), hayEnlaces: vista.some(p => p.enlace !== null),
  };
}
