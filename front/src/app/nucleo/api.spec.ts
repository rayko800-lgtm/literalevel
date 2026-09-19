import { VERSION_CORTE_2D, urlCortePalabra, urlCorteSonido } from './api';

describe('URLs del corte articulatorio 2D', () => {
  it('versiona igual la base, replay, Despacio y reduced motion', () => {
    const urls = [
      urlCorteSonido('θ', 'ga'),
      urlCorteSonido('θ', 'ga', false, 7.1),
      urlCorteSonido('θ', 'ga', false, 14.2),
      urlCorteSonido('θ', 'ga', true),
      urlCortePalabra('/ðæt/', 'ga', 7.1),
    ];
    for (const url of urls) {
      expect(new URL(url, 'http://local').searchParams.get('v')).toBe(VERSION_CORTE_2D);
    }
    expect(urls[1]).toContain('dur=7.1');
    expect(urls[2]).toContain('dur=14.2');
    expect(urls[3]).toContain('quieto=1');
  });
});
