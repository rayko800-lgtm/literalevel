import { RitmoLectura } from '../nucleo/api';
import { vistaRitmo } from './ritmo';

const frase = ["don't", 'you', 'ever', 'call', 'me', 'an', 'apple', '.'].map((palabra, i) => ({ palabra, bien: i !== 2 }));

function ritmo(parcial: Partial<RitmoLectura> = {}): RitmoLectura {
  return {
    medido: true, duracion_s: 3.4, palabras: [],
    pausas: [
      { despues_de: 2, segundos: 0.52, en_referencia: false, de_mas: true },
      { despues_de: 4, segundos: 0.4, en_referencia: true, de_mas: false },
      { despues_de: 7, segundos: 0.9, en_referencia: false, de_mas: true },    // tras la última: no cuenta
    ],
    tramos: [
      { desde: 3, hasta: 5, palabras_por_segundo: 2.1, referencia: 3.2, objetivo: 2.9, acelerar: true },
      { desde: 0, hasta: 2, palabras_por_segundo: 3, referencia: 3.2, objetivo: 2.9, acelerar: false },
      { desde: 6, hasta: 40, palabras_por_segundo: 1, referencia: null, objetivo: null, acelerar: true }, // fuera
    ],
    natural: {
      enfasis: [{ indice: 2, ipa: '/ˈɛvɚ/' }, { indice: 99, ipa: null }],
      enlaces: [{ de: 5, a: 6, tipo: 'consonante_vocal', ipa: '/ə.ˈnæpəl/' }, { de: 1, a: 3, tipo: 'vocal_vocal', ipa: null }],
      reducciones: [{ desde: 0, hasta: 1, forma: 'doncha', ipa: '/ˈdoʊntʃə/', generado_por_ia: true }],
      tramos_rapidos: [], version_natural: 'doncha ever call me an apple.', audio_natural: '/api/audio/nat.mp3',
    },
    ...parcial,
  };
}

describe('La vista del ritmo de la lectura', () => {
  it('pinta cada marca en su palabra y descarta los índices que no son de la frase', () => {
    const v = vistaRitmo(frase, ritmo());
    expect(v.palabras.map(p => p.enfasis)).toEqual([false, false, true, false, false, false, false, false]);
    expect(v.palabras.map(p => p.enlace)).toEqual([null, null, null, null, null, 'consonante con vocal', null, null]);
    expect(v.palabras.map(p => p.sinPausaDespues)).toEqual([null, null, 0.52, null, null, null, null, null]);
    expect(v.palabras.map(p => p.acelerar)).toEqual([false, false, false, true, true, true, false, false]);
    expect(v.palabras.map(p => p.empiezaAcelerar)).toEqual([false, false, false, true, false, false, false, false]);
    expect(v.palabras.map(p => p.visible)).toEqual([true, true, true, true, true, true, true, false]);
    expect(v.reducciones).toEqual([{ texto: "don't you", forma: 'doncha', ipa: '/ˈdoʊntʃə/', ia: true }]);
    expect(v.versionNatural).toBe('doncha ever call me an apple.');
    expect(v.audioNatural).toBe('/api/audio/nat.mp3');
    expect(v.hayMarcasDeTiempo).toBe(true);
    expect(v.natural).toBe(true);
  });

  it('sin marcas de tiempo del lector no dice dónde acelerar ni dónde no parar', () => {
    const v = vistaRitmo(frase, ritmo({ medido: false }));
    expect(v.palabras.some(p => p.acelerar || p.empiezaAcelerar || p.sinPausaDespues !== null)).toBe(false);
    expect(v.hayMarcasDeTiempo).toBe(false);
    expect(v.palabras[2].enfasis).toBe(true);           // el análisis natural sí vale
  });

  it('sin análisis natural, solo las marcas de tiempo; sin ritmo, la frase tal cual', () => {
    const sinNatural = vistaRitmo(frase, ritmo({ natural: null }));
    expect(sinNatural.natural).toBe(false);
    expect(sinNatural.reducciones).toEqual([]);
    expect(sinNatural.palabras.some(p => p.enfasis || p.enlace)).toBe(false);
    expect(sinNatural.palabras[3].empiezaAcelerar).toBe(true);

    const nada = vistaRitmo(frase, null);
    expect(nada.medido).toBe(false);
    expect(nada.palabras.map(p => p.texto)).toEqual(frase.map(w => w.palabra));
    expect(nada.palabras.map(p => p.bien)).toEqual(frase.map(w => w.bien));
  });

  it('la versión natural igual a la frase (salvo mayúsculas y signos) no se repite', () => {
    const r = ritmo();
    r.natural!.version_natural = "Don't you ever call me an apple";
    expect(vistaRitmo(frase, r).versionNatural).toBeNull();
  });

  it('la leyenda de énfasis y de enlaces solo sale si hay alguno que pintar', () => {
    const v = vistaRitmo(frase, ritmo());
    expect([v.hayEnfasis, v.hayEnlaces]).toEqual([true, true]);

    // El enlace de 1 a 3 no es de palabras seguidas y el énfasis 99 cae fuera: no se pinta nada.
    const r = ritmo();
    r.natural!.enlaces = [{ de: 1, a: 3, tipo: 'vocal_vocal', ipa: null }];
    r.natural!.enfasis = [{ indice: 99, ipa: null }];
    const sinNada = vistaRitmo(frase, r);
    expect(sinNada.natural).toBe(true);
    expect([sinNada.hayEnfasis, sinNada.hayEnlaces]).toEqual([false, false]);

    expect([vistaRitmo(frase, null).hayEnfasis, vistaRitmo(frase, null).hayEnlaces]).toEqual([false, false]);
  });
});
