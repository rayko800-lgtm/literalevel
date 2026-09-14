/** El audio que acompaña a la boca en 3D: un sonido (mp3 de `/api/fonemas`)
 *  o una palabra (mp3 de `/api/voz` o `/api/palabra`), arrancado en el mismo
 *  instante que la línea de tiempo y desplazado para que su primera energía
 *  caiga cuando la boca llega a la pose.
 *
 *  Con Web Audio se descarga y decodifica el archivo: así se sabe la
 *  duración exacta, se mide el silencio inicial que trae el TTS (el primer
 *  tramo con energía) y se programa el arranque con precisión de muestra.
 *  Si no se puede (sin AudioContext, sin CORS, archivo roto), un `<audio>`
 *  normal con la duración de sus metadatos y un desfase fijo de 120 ms. Y si
 *  ni eso, `preparar` devuelve null y la boca se mueve sola. */

export interface AudioListo {
  /** Segundos del archivo entero. */
  duracion: number;
  /** Segundos de silencio al principio (medidos, o 0,12 si no se pudo). */
  silencio: number;
  /** Arranca el audio dentro de `retrasoS` segundos (negativo: ya empezado,
   *  salta ese tramo). Devuelve la función que lo para. */
  tocar(retrasoS: number): () => void;
}

const SILENCIO_FIJO = 0.12;
const UMBRAL = 0.02;             // amplitud (unos -34 dB) que cuenta como «ya suena»

/** Primer instante con energía de un buffer decodificado, acotado a medio segundo. */
export function silencioInicial(canales: Float32Array[], frecuencia: number): number {
  const tope = Math.min(canales[0]?.length ?? 0, Math.round(frecuencia * 0.5));
  for (let i = 0; i < tope; i++) {
    for (const c of canales) {
      if (Math.abs(c[i]) > UMBRAL) return i / frecuencia;
    }
  }
  return Math.min(SILENCIO_FIJO, tope / frecuencia);
}

export class Sonador {
  private ctx: AudioContext | null = null;
  private readonly cache = new Map<string, Promise<AudioListo | null>>();
  private parando: (() => void) | null = null;

  /** Llamar dentro del gesto del usuario (clic): iOS solo deja crear y
   *  reanudar el contexto de audio ahí. */
  despertar(): void {
    try {
      const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!this.ctx && Ctx) this.ctx = new Ctx();
      if (this.ctx?.state === 'suspended') void this.ctx.resume();
    } catch { this.ctx = null; }
  }

  preparar(url: string): Promise<AudioListo | null> {
    let p = this.cache.get(url);
    if (!p) {
      p = this.decodificar(url).catch(() => this.conElemento(url)).catch(() => null);
      this.cache.set(url, p);
    }
    return p;
  }

  /** Para lo que esté sonando. */
  parar(): void {
    this.parando?.();
    this.parando = null;
  }

  destruir(): void {
    this.parar();
    void this.ctx?.close().catch(() => {});
    this.ctx = null;
  }

  private async decodificar(url: string): Promise<AudioListo> {
    const ctx = this.ctx;
    if (!ctx) throw new Error('sin AudioContext');
    const r = await fetch(url);
    if (!r.ok) throw new Error(String(r.status));
    const buffer = await ctx.decodeAudioData(await r.arrayBuffer());
    const canales = Array.from({ length: buffer.numberOfChannels }, (_, i) => buffer.getChannelData(i));
    const silencio = silencioInicial(canales, buffer.sampleRate);
    return {
      duracion: buffer.duration,
      silencio,
      tocar: retrasoS => {
        this.parar();
        const fuente = ctx.createBufferSource();
        fuente.buffer = buffer;
        fuente.connect(ctx.destination);
        if (retrasoS >= 0) fuente.start(ctx.currentTime + retrasoS);
        else fuente.start(ctx.currentTime, Math.min(buffer.duration, -retrasoS));
        const parar = () => { try { fuente.stop(); } catch { /* ya parada */ } fuente.disconnect(); };
        this.parando = parar;
        return parar;
      },
    };
  }

  private conElemento(url: string): Promise<AudioListo> {
    return new Promise((resolver, rechazar) => {
      const a = new Audio(url);
      a.preload = 'auto';
      const temporizador = setTimeout(() => rechazar(new Error('sin metadatos')), 4000);
      a.addEventListener('error', () => { clearTimeout(temporizador); rechazar(new Error('audio roto')); }, { once: true });
      a.addEventListener('loadedmetadata', () => {
        clearTimeout(temporizador);
        resolver({
          duracion: Number.isFinite(a.duration) ? a.duration : 1,
          silencio: SILENCIO_FIJO,
          tocar: retrasoS => {
            this.parar();
            let id = 0;
            const arrancar = () => { a.currentTime = retrasoS < 0 ? -retrasoS : 0; void a.play().catch(() => {}); };
            if (retrasoS > 0) id = window.setTimeout(arrancar, retrasoS * 1000);
            else arrancar();
            const parar = () => { clearTimeout(id); a.pause(); };
            this.parando = parar;
            return parar;
          },
        });
      }, { once: true });
    });
  }
}
