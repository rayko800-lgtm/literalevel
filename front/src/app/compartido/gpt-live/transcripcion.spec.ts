import { describe, expect, it } from 'vitest';
import { agregarDelta, GrupoLive } from './transcripcion';

describe('subtítulos GPT-Live', () => {
  it('conserva exactamente los deltas y agrupa por intervalo de cada hablante', () => {
    let grupos: GrupoLive[] = [];
    grupos = agregarDelta(grupos, { hablante: 'lector', delta: 'I ', start_ms: 100, end_ms: 200 });
    grupos = agregarDelta(grupos, { hablante: 'pleyade', delta: 'Sure', start_ms: 150, end_ms: 350 });
    grupos = agregarDelta(grupos, { hablante: 'lector', delta: 'I mean', start_ms: 400, end_ms: 700 });
    grupos = agregarDelta(grupos, { hablante: 'lector', delta: ' again', start_ms: 2500, end_ms: 2700 });
    expect(grupos.map(g => [g.hablante, g.inicio, g.fin, g.texto])).toEqual([
      ['lector', 100, 700, 'I I mean'],
      ['pleyade', 150, 350, 'Sure'],
      ['lector', 2500, 2700, ' again'],
    ]);
    expect(grupos[0].partes.map(p => [p.delta, p.start_ms, p.end_ms])).toEqual([
      ['I ', 100, 200], ['I mean', 400, 700],
    ]);
  });
});
