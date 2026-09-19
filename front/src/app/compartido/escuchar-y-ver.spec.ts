import { CorteEnPantalla, EntornoEscuchar, EscucharYVer, VozNavegador, duracionParaCorte } from './escuchar-y-ver';
import { vi } from 'vitest';

/** Un <audio> de mentira: guarda los oyentes y deja disparar los eventos a mano. */
class AudioFalso {
  duration = NaN;
  playbackRate = 1;
  preservesPitch = false;
  currentTime = 5;
  pausado = 0;
  falla = false;
  private oyentes: Record<string, (() => void)[]> = {};
  addEventListener(tipo: string, fn: () => void) { (this.oyentes[tipo] ??= []).push(fn); }
  disparar(tipo: string) { const fns = this.oyentes[tipo] ?? []; this.oyentes[tipo] = []; fns.forEach(f => f()); }
  play() { return this.falla ? Promise.reject(new Error('bloqueado')) : Promise.resolve(); }
  pause() { this.pausado++; }
}

function montar() {
  const audios: AudioFalso[] = [];
  const pedidos: string[] = [];
  const revocadas: string[] = [];
  const habladas: { texto: string; voz: VozNavegador; empezar: () => void; velocidad: number }[] = [];
  let n = 0;
  const entorno: EntornoEscuchar = {
    crearAudio: () => { const a = new AudioFalso(); audios.push(a); return a as unknown as HTMLAudioElement; },
    traerSvg: async url => { pedidos.push(url); return new Blob([url]); },
    crearUrl: () => `blob:vuelta-${++n}`,
    revocarUrl: url => { revocadas.push(url); },
    hablar: (texto, voz, empezar, velocidad) => { habladas.push({ texto, voz, empezar, velocidad }); return true; },
    callar: () => {},
  };
  return { eyv: new EscucharYVer(entorno), audios, pedidos, revocadas, habladas };
}

const corte = (quieto = false): CorteEnPantalla => ({
  clave: 'ficha',
  base: '/api/articulacion/ga/θ.svg',
  animada: dur => quieto ? null : `/api/articulacion/ga/θ.svg?${dur === null ? '' : `dur=${dur}&`}una=1`,
});
const esperar = () => new Promise(r => setTimeout(r));

describe('Escuchar y ver', () => {
  it('descarga el SVG actual sin aceptar una copia HTTP antigua', async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, blob: async () => new Blob(['<svg/>']) });
    vi.stubGlobal('fetch', fetch);
    try {
      const eyv = new EscucharYVer();
      eyv.preparar({ audio: null, cortes: [corte()] });
      await esperar();
      expect(fetch).toHaveBeenCalledWith('/api/articulacion/ga/θ.svg?una=1', { cache: 'no-store' });
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it('redondea la duración a 0,1 s dentro de 0,3..10', () => {
    expect(duracionParaCorte(3.04)).toBe(3);
    expect(duracionParaCorte(1.26)).toBe(1.3);
    expect(duracionParaCorte(0.1)).toBe(0.3);
    expect(duracionParaCorte(14)).toBe(14);
    expect(duracionParaCorte(40)).toBe(30);
    expect(duracionParaCorte(NaN)).toBeNull();
    expect(duracionParaCorte(Infinity)).toBeNull();
  });

  it('con el SVG preparado, el corte vuelve a empezar como blob nuevo cuando suena, y el anterior se suelta', async () => {
    const { eyv, audios, pedidos, revocadas } = montar();
    const p = { audio: 'https://motor/api/fonemas/ga/theta.mp3', cortes: [corte()] };
    eyv.preparar(p);
    audios[0].duration = 3.04;
    audios[0].disparar('loadedmetadata');
    await esperar();
    expect(pedidos).toEqual(['/api/articulacion/ga/θ.svg?dur=3&una=1']);
    expect(eyv.src('ficha', corte().base)).toBe(corte().base);

    eyv.escuchar(p);
    expect(audios.length).toBe(1);                       // el mismo <audio> preparado
    expect(audios[0].currentTime).toBe(0);
    expect(eyv.src('ficha', corte().base)).toBe(corte().base); // aún no suena: no se mueve
    audios[0].disparar('playing');
    expect(eyv.src('ficha', corte().base)).toBe('blob:vuelta-1');

    eyv.escuchar(p);
    audios[0].disparar('playing');
    expect(eyv.src('ficha', corte().base)).toBe('blob:vuelta-2');
    expect(revocadas).toEqual(['blob:vuelta-1']);
    expect(eyv.pulsaciones()).toBe(2);
  });

  it('sin el SVG en memoria, la URL de una pasada con r=n para que recargue', () => {
    const { eyv, audios } = montar();
    eyv.escuchar({ audio: 'a.mp3', cortes: [corte()] });
    audios[0].duration = 1.26;
    audios[0].disparar('playing');
    expect(eyv.src('ficha', corte().base)).toBe('/api/articulacion/ga/θ.svg?dur=1.3&una=1&r=1');
  });

  it('si el mp3 no suena, habla la voz del navegador y el corte arranca con ella', async () => {
    const { eyv, audios, habladas } = montar();
    const a = new AudioFalso();
    a.falla = true;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (eyv as any).audios.set('roto.mp3', a);
    eyv.escuchar({ audio: 'roto.mp3', texto: 'war', voz: 'en-GB', cortes: [corte()] });
    await esperar();
    expect(audios.length).toBe(0);
    expect(habladas.map(h => [h.texto, h.voz])).toEqual([['war', 'en-GB']]);
    expect(eyv.src('ficha', corte().base)).toBe(corte().base);
    habladas[0].empezar();
    expect(eyv.src('ficha', corte().base)).toBe('/api/articulacion/ga/θ.svg?una=1&r=1');
  });

  it('sin audio ni voz, el corte arranca solo; con «reducir movimiento» no se toca', () => {
    const { eyv } = montar();
    eyv.escuchar({ audio: null, cortes: [corte()] });
    expect(eyv.src('ficha', corte().base)).toBe('/api/articulacion/ga/θ.svg?una=1&r=1');

    const quieto = montar();
    quieto.eyv.escuchar({ audio: null, cortes: [corte(true)] });
    expect(quieto.eyv.src('ficha', corte().base)).toBe(corte().base);
  });

  it('una pulsación nueva deja sin efecto la anterior que aún no sonaba', () => {
    const { eyv, audios } = montar();
    eyv.escuchar({ audio: 'uno.mp3', cortes: [corte()] });
    eyv.escuchar({ audio: 'dos.mp3', cortes: [{ ...corte(), animada: () => '/dos.svg?una=1' }] });
    audios[0].disparar('playing');
    expect(eyv.src('ficha', corte().base)).toBe(corte().base);
    expect(audios[0].pausado).toBe(1);
    audios[1].disparar('playing');
    expect(eyv.src('ficha', corte().base)).toBe('/dos.svg?una=1&r=1');
  });

  it('las cuatro velocidades conservan tono y sincronizan duración de audio y SVG', () => {
    for (const [velocidad, duracion] of [[0.25, 16], [0.5, 8], [1, 4], [1.25, 3.2]] as const) {
      const { eyv, audios } = montar();
      eyv.escuchar({ audio: 'a.mp3', cortes: [corte()], velocidad });
      expect(audios[0].playbackRate).toBe(velocidad);
      expect(audios[0].preservesPitch).toBe(true);
      audios[0].duration = 4;
      audios[0].disparar('playing');
      expect(eyv.src('ficha', corte().base)).toBe(`/api/articulacion/ga/θ.svg?dur=${duracion}&una=1&r=1`);
    }
  });

  it('rechaza velocidades fuera del conjunto y conserva 0,25× en la voz del navegador', () => {
    const { eyv, audios, habladas } = montar();
    // Una velocidad que no está entre las cuatro vuelve a 1×.
    eyv.escuchar({ audio: 'a.mp3', cortes: [corte()], velocidad: 3 });
    expect(audios[0].playbackRate).toBe(1);
    eyv.escuchar({ audio: null, texto: 'war', cortes: [corte()], velocidad: 0.25 });
    expect(habladas.map(h => h.velocidad)).toEqual([0.25]);
  });

  it('si cambia la base (otro sonido), pinta la base nueva', () => {
    const { eyv } = montar();
    eyv.escuchar({ audio: null, cortes: [corte()] });
    expect(eyv.src('ficha', '/api/articulacion/ga/s.svg')).toBe('/api/articulacion/ga/s.svg');
  });
});
