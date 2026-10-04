import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Sonador, latenciaSalida } from './audio';

/** Auditoría de 4e, ronda 2: con «Escuchar y ver» y «Cerrar 3D» en el mismo turno,
 *  el mp3 terminaba de prepararse con el visor desmontado y sonaba igual. */
describe('el sonador del visor 3D', () => {
  it('destruido, no prepara ni hace sonar nada', async () => {
    const s = new Sonador();
    s.destruir();
    await expect(s.preparar('/api/audio/x.mp3')).resolves.toBeNull();
  });
});

/** Un `<audio>` de mentira: dispara `playing` `tardaEnSonar` ms después de `play()`. */
class AudioFalso extends EventTarget {
  static creados: AudioFalso[] = [];
  static tardaEnSonar = 0;
  preload = '';
  currentTime = 0;
  playbackRate = 1;
  preservesPitch = false;
  paused = true;
  duration = 1;
  constructor(public src = '') { super(); AudioFalso.creados.push(this); }
  load(): void { /* nada que bajar */ }
  play(): Promise<void> {
    this.paused = false;
    setTimeout(() => this.dispatchEvent(new Event('playing')), AudioFalso.tardaEnSonar);
    return Promise.resolve();
  }
  pause(): void { this.paused = true; }
}

/** Un AudioContext de mentira: decodifica un segundo con sonido de 0,1 a 0,6 s. */
class ContextoFalso {
  state = 'running';
  currentTime = 0;
  baseLatency = 0;
  outputLatency = 0;
  destination = {};
  fuentes: { start: ReturnType<typeof vi.fn> }[] = [];
  /** Lo que hace `resume()`: por defecto, corre al instante. */
  reanudar: () => Promise<void> = () => { this.state = 'running'; return Promise.resolve(); };
  resume(): Promise<void> { return this.reanudar(); }
  close(): Promise<void> { return Promise.resolve(); }
  decodeAudioData(): Promise<unknown> {
    const canal = new Float32Array(1000);
    for (let i = 100; i < 600; i++) canal[i] = 0.3;
    return Promise.resolve({ duration: 1, numberOfChannels: 1, sampleRate: 1000, getChannelData: () => canal });
  }
  createBufferSource(): { buffer: unknown; connect: () => void; start: ReturnType<typeof vi.fn>; stop: () => void; disconnect: () => void } {
    const f = { buffer: null as unknown, connect: vi.fn(), start: vi.fn(), stop: vi.fn(), disconnect: vi.fn() };
    this.fuentes.push(f);
    return f;
  }
}

/** 4 oct 2026 (Miguel, tras grabar la demo en el móvil: «el modelo se desfasa
 *  respecto al audio»): el audio tiene que arrancar cuando arranca la boca, y
 *  si no puede, decir cuánto llegó tarde para que la boca se desplace. */
describe('4 oct: el audio arranca con la boca', () => {
  const globales = globalThis as unknown as Record<string, unknown>;
  const ventana = window as unknown as Record<string, unknown>;
  const originales: Record<string, [unknown, unknown]> = {};
  let contexto: ContextoFalso;
  let bajadas = 0;
  const URL_MP3 = '/api/audio/frase.mp3?acceso=x';

  function poner(nombre: string, valor: unknown): void {
    originales[nombre] = [globales[nombre], ventana[nombre]];
    globales[nombre] = valor;
    ventana[nombre] = valor;
  }

  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'Date', 'performance'] });
    AudioFalso.creados = [];
    AudioFalso.tardaEnSonar = 0;
    bajadas = 0;
    contexto = new ContextoFalso();
    poner('AudioContext', function () { return contexto; });
    poner('Audio', AudioFalso);
    poner('fetch', async () => { bajadas++; return { ok: true, blob: async () => new Blob([new Uint8Array([1, 2, 3])]) }; });
    URL.createObjectURL = vi.fn(() => 'blob:prueba');
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    for (const [nombre, [g, w]] of Object.entries(originales)) { globales[nombre] = g; ventana[nombre] = w; }
    vi.useRealTimers();
  });

  it('al preparar guarda los bytes y precarga un <audio> desde un blob:; a 0,5× suena desde él, sin volver a la red', async () => {
    const s = new Sonador();
    s.despertar();
    const listo = await s.preparar(URL_MP3);
    expect(listo).not.toBeNull();
    expect(listo!.silencio).toBeCloseTo(0.1, 3);
    expect(bajadas).toBe(1);
    // El elemento ya existe al preparar, precargado desde el blob.
    expect(AudioFalso.creados.length).toBe(1);
    expect(AudioFalso.creados[0].src).toBe('blob:prueba');
    expect(AudioFalso.creados[0].preload).toBe('auto');
    const r = listo!.tocar(0, 0.5);
    expect(r.velocidad).toBe(0.5);
    const a = AudioFalso.creados[0];
    expect(AudioFalso.creados.length).toBe(1);          // el mismo elemento, no uno nuevo
    expect(a.paused).toBe(false);
    expect(a.playbackRate).toBe(0.5);
    expect(a.preservesPitch).toBe(true);
    expect(bajadas).toBe(1);                            // ni una petición más
    expect(contexto.fuentes.length).toBe(0);            // y no por Web Audio
    s.destruir();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:prueba');
  });

  it('si el <audio> empieza a sonar 300 ms tarde, avisa de 0,3 s para que la línea se desplace', async () => {
    AudioFalso.tardaEnSonar = 300;
    const s = new Sonador();
    s.despertar();
    const listo = (await s.preparar(URL_MP3))!;
    const desfases: number[] = [];
    listo.tocar(0, 0.5, d => desfases.push(d));
    await vi.advanceTimersByTimeAsync(100);
    expect(desfases).toEqual([]);                        // todavía no suena: no se avisa
    await vi.advanceTimersByTimeAsync(200);
    expect(desfases.length).toBe(1);
    expect(desfases[0]).toBeCloseTo(0.3, 2);
    await vi.advanceTimersByTimeAsync(1000);
    expect(desfases.length).toBe(1);                     // una sola vez

    // Con retraso previsto (0,5 s de espera): solo cuenta lo que pasa de ahí.
    const d2: number[] = [];
    listo.tocar(0.5, 0.5, d => d2.push(d));
    await vi.advanceTimersByTimeAsync(800);
    expect(d2.length).toBe(1);
    expect(d2[0]).toBeCloseTo(0.3, 2);

    // Con retraso negativo (ya empezado): salta en tiempo del archivo y el aviso es el mismo.
    const d3: number[] = [];
    listo.tocar(-0.4, 0.5, d => d3.push(d));
    expect(AudioFalso.creados[0].currentTime).toBeCloseTo(0.2, 6);
    await vi.advanceTimersByTimeAsync(300);
    expect(d3[0]).toBeCloseTo(0.3, 2);
  });

  it('con el contexto parado, esperarContexto espera a resume() y no más del tope; tocar a 1× usa el <audio>', async () => {
    contexto.state = 'suspended';
    let correr = (): void => {};
    contexto.reanudar = () => new Promise<void>(res => { correr = () => { contexto.state = 'running'; res(); }; });
    const s = new Sonador();
    s.despertar();                                       // dentro del clic: pide reanudar
    let resultado: boolean | null = null;
    void s.esperarContexto(600).then(v => { resultado = v; });
    await vi.advanceTimersByTimeAsync(200);
    expect(resultado).toBeNull();                        // sigue esperando
    correr();
    await vi.advanceTimersByTimeAsync(0);
    expect(resultado).toBe(true);

    // Un contexto que nunca arranca: al tope, false, y el audio va por el <audio>.
    const atascado = new ContextoFalso();
    atascado.state = 'suspended';
    atascado.reanudar = () => new Promise<void>(() => {});
    contexto = atascado;
    const s2 = new Sonador();
    s2.despertar();
    let r2: boolean | null = null;
    void s2.esperarContexto(600).then(v => { r2 = v; });
    await vi.advanceTimersByTimeAsync(599);
    expect(r2).toBeNull();
    await vi.advanceTimersByTimeAsync(1);
    expect(r2).toBe(false);
    const listo = (await s2.preparar(URL_MP3))!;
    const r = listo.tocar(0, 1);
    expect(r.velocidad).toBe(1);
    expect(atascado.fuentes.length).toBe(0);
    expect(AudioFalso.creados[AudioFalso.creados.length - 1].paused).toBe(false);
  });

  it('a 1× con Web Audio corriendo programa la fuente y avisa solo de la latencia de salida', async () => {
    contexto.baseLatency = 0.01;
    contexto.outputLatency = 0.04;
    const s = new Sonador();
    s.despertar();
    const listo = (await s.preparar(URL_MP3))!;
    const desfases: number[] = [];
    listo.tocar(0.35, 1, d => desfases.push(d));
    expect(contexto.fuentes.length).toBe(1);
    expect(contexto.fuentes[0].start).toHaveBeenCalledWith(0.35);
    expect(desfases).toEqual([0.05]);
    expect(latenciaSalida({ baseLatency: 0.5, outputLatency: 0.5 })).toBe(0.3);
    expect(latenciaSalida({})).toBe(0);
    expect(latenciaSalida({ baseLatency: Number.NaN, outputLatency: -1 })).toBe(0);
  });
});
