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
 *  ni eso, `preparar` devuelve null y la boca se mueve sola.
 *
 *  4 oct 2026 (Miguel, tras grabar la demo en el móvil: «el modelo se
 *  desfasa respecto al audio»): fuera de 1× el `<audio>` se creaba al tocar
 *  con la URL del Space, que responde `Cache-Control: private, no-store` para
 *  las palabras y las frases, así que el mp3 volvía a bajar por la red y
 *  empezaba a sonar cientos de ms después de arrancar la boca. Ahora los
 *  bytes ya bajados se guardan y el `<audio>` se crea precargado desde un
 *  `blob:` al preparar; y, pase lo que pase, `tocar` avisa (`alEmpezar`) de
 *  cuánto se retrasó el arranque real para que la línea se desplace. */

export interface AudioListo {
  /** Segundos del archivo entero. */
  duracion: number;
  /** Segundos de silencio al principio (medidos, o 0,12 si no se pudo). */
  silencio: number;
  /** Último instante con energía (medido; sin medida, la duración entera).
   *  `fin - silencio` es lo que de verdad suena, para ajustar la boca. */
  fin: number;
  /** Tramos que suenan, en segundos del archivo (los sonidos de Miguel traen
   *  el sonido largo, uno corto y un ejemplo separados por silencios). Vacío
   *  si no se pudo medir. */
  tramos: Tramo[];
  /** Arranca el audio dentro de `retrasoS` segundos (negativo: ya empezado,
   *  salta ese tramo) a `velocidad` (0,25..2) conservando el tono.
   *  `alEmpezar` recibe, una sola vez y cuando el audio de verdad empieza a
   *  sonar, los segundos que llegó tarde respecto a lo previsto (negativo si
   *  se adelantó): quien anima desplaza su línea en ese tiempo.
   *  Devuelve la función que lo para y la velocidad a la que de verdad suena:
   *  1 si el navegador no sabe ralentizar sin cambiar el tono (entonces la
   *  boca va despacio y el audio no; quien llama lo avisa). */
  tocar(retrasoS: number, velocidad?: number, alEmpezar?: (desfaseS: number) => void): { parar: () => void; velocidad: number };
}

/** El navegador ralentiza un `<audio>` conservando el tono (`preservesPitch`;
 *  Safari viejo, `webkitPreservesPitch`). */
export function conservaTono(a: HTMLMediaElement): boolean {
  return 'preservesPitch' in a || 'webkitPreservesPitch' in a;
}

function ralentizar(a: HTMLMediaElement, velocidad: number): number {
  if (velocidad === 1) { a.playbackRate = 1; return 1; }
  if (!conservaTono(a)) { a.playbackRate = 1; return 1; }
  (a as HTMLMediaElement & { webkitPreservesPitch?: boolean }).preservesPitch = true;
  (a as HTMLMediaElement & { webkitPreservesPitch?: boolean }).webkitPreservesPitch = true;
  a.playbackRate = velocidad;
  return velocidad;
}

/** Un `<audio>` que arranca dentro de `retrasoS` a `velocidad`; el salto
 *  inicial (retraso negativo) va en tiempo del archivo: `-retraso * velocidad`.
 *  Al primer `playing` mide cuánto llegó tarde respecto a lo previsto (el
 *  archivo en `inicio` a los `retrasoS` del tocar, avanzando a `velocidad`) y
 *  se lo da a `alEmpezar`; el `currentTime` de ese instante descuenta lo que
 *  ya hubiera avanzado. */
function tocarElemento(a: HTMLAudioElement, retrasoS: number, velocidad: number,
                       alEmpezar?: (desfaseS: number) => void): { parar: () => void; velocidad: number } {
  const real = ralentizar(a, velocidad);
  const t0 = performance.now();
  const inicio = retrasoS < 0 ? -retrasoS * real : 0;
  let id = 0;
  const empezo = () => {
    if (!alEmpezar) return;
    const avanzado = Number.isFinite(a.currentTime) ? Math.max(0, a.currentTime - inicio) : 0;
    const previsto = Math.max(retrasoS, 0) + avanzado / real;
    alEmpezar((performance.now() - t0) / 1000 - previsto);
  };
  a.addEventListener('playing', empezo, { once: true });
  const arrancar = () => { a.currentTime = inicio; void a.play().catch(() => {}); };
  if (retrasoS > 0) id = window.setTimeout(arrancar, retrasoS * 1000);
  else arrancar();
  return { parar: () => { clearTimeout(id); a.removeEventListener('playing', empezo); a.pause(); }, velocidad: real };
}

/** Lo que tarda lo programado en Web Audio en salir por el altavoz, si el
 *  navegador lo dice (`baseLatency` del grafo más `outputLatency` del
 *  dispositivo; Safari no da la segunda). Acotado: un valor disparatado no
 *  debe mover la boca medio segundo. */
export function latenciaSalida(ctx: { baseLatency?: number; outputLatency?: number }): number {
  const base = Number.isFinite(ctx.baseLatency) ? ctx.baseLatency! : 0;
  const salida = Number.isFinite(ctx.outputLatency) ? ctx.outputLatency! : 0;
  return Math.min(0.3, Math.max(0, base) + Math.max(0, salida));
}

const SILENCIO_FIJO = 0.12;
const UMBRAL = 0.02;             // amplitud (unos -34 dB) que cuenta como «ya suena»

export interface Tramo { inicio: number; fin: number }

/** Tramos con sonido: energía media (RMS) por ventanas de 20 ms sobre el 6 %
 *  del pico, uniendo huecos de menos de 0,2 s y quitando chasquidos de menos
 *  de 60 ms. El ruido de fondo de una grabación directa queda por debajo. */
export function tramosSonoros(canales: Float32Array[], frecuencia: number): Tramo[] {
  const largo = canales[0]?.length ?? 0, paso = Math.max(1, Math.round(frecuencia * 0.02));
  const rms: number[] = [];
  for (let i = 0; i < largo; i += paso) {
    let suma = 0, n = 0;
    for (const c of canales) for (let k = i; k < Math.min(largo, i + paso); k++) { suma += c[k] * c[k]; n++; }
    rms.push(Math.sqrt(suma / Math.max(1, n)));
  }
  const umbral = Math.max(0.01, 0.06 * Math.max(0, ...rms));
  const tramos: Tramo[] = [];
  rms.forEach((r, j) => {
    if (r < umbral) return;
    const t0 = j * paso / frecuencia, t1 = Math.min(largo, (j + 1) * paso) / frecuencia;
    const ultimo = tramos[tramos.length - 1];
    if (ultimo && t0 - ultimo.fin < 0.2) ultimo.fin = t1; else tramos.push({ inicio: t0, fin: t1 });
  });
  return tramos.filter(t => t.fin - t.inicio >= 0.06);
}

/** Último instante con energía de un buffer decodificado (el silencio del
 *  final no cuenta como sonido). Sin energía, la duración entera. */
export function finSonoro(canales: Float32Array[], frecuencia: number): number {
  const largo = canales[0]?.length ?? 0;
  for (let i = largo - 1; i >= 0; i--) {
    for (const c of canales) {
      if (Math.abs(c[i]) > UMBRAL) return (i + 1) / frecuencia;
    }
  }
  return largo / frecuencia;
}

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
  /** La promesa del último `resume()`: `esperarContexto` la espera. */
  private reanudando: Promise<void> | null = null;
  private readonly cache = new Map<string, Promise<AudioListo | null>>();
  /** Los `blob:` de los mp3 ya bajados (uno por URL), para revocarlos al destruir. */
  private readonly blobs: string[] = [];
  private parando: (() => void) | null = null;
  /** Tras `destruir`, nada vuelve a sonar: ni lo que se estaba preparando ni un `tocar` tardío. */
  private destruido = false;

  /** Llamar dentro del gesto del usuario (clic): iOS solo deja crear y
   *  reanudar el contexto de audio ahí. */
  despertar(): void {
    if (this.destruido) return;
    try {
      const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!this.ctx && Ctx) this.ctx = new Ctx();
      if (this.ctx && this.ctx.state !== 'running') this.reanudando = this.ctx.resume().catch(() => {});
    } catch { this.ctx = null; }
  }

  /** 4 oct 2026: el reloj de Web Audio (`currentTime`) no avanza hasta que el
   *  contexto corre, y en Android reanudarlo tras el gesto tarda 100–500 ms la
   *  primera vez: si la línea arrancaba antes, la fuente programada salía
   *  tarde. Espera a que corra, como mucho `topeMs`. True si corre; false si
   *  no llegó a tiempo o no hay contexto (entonces `tocar` usa el `<audio>`). */
  esperarContexto(topeMs = 600): Promise<boolean> {
    const ctx = this.ctx;
    if (!ctx || this.destruido) return Promise.resolve(false);
    if (ctx.state === 'running') return Promise.resolve(true);
    const reanudar = this.reanudando ?? (this.reanudando = ctx.resume().catch(() => {}));
    return new Promise(resolver => {
      const id = setTimeout(() => resolver(ctx.state === 'running'), topeMs);
      void reanudar.then(() => { clearTimeout(id); resolver(ctx.state === 'running'); });
    });
  }

  preparar(url: string): Promise<AudioListo | null> {
    if (this.destruido) return Promise.resolve(null);
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
    this.destruido = true;
    this.parar();
    void this.ctx?.close().catch(() => {});
    this.ctx = null;
    for (const u of this.blobs) { try { URL.revokeObjectURL(u); } catch { /* sin blobs */ } }
    this.blobs.length = 0;
  }

  /** El mp3 ya bajado en un `<audio>` precargado desde un `blob:` (la CSP de
   *  producción lo permite en `media-src`); si el navegador no sabe hacer
   *  blobs, la URL de siempre. Se crea al preparar, no al tocar, para que al
   *  tocar ya esté listo. */
  private elementoDe(blob: Blob, url: string): HTMLAudioElement {
    let src = url;
    try {
      if (typeof URL.createObjectURL === 'function') { src = URL.createObjectURL(blob); this.blobs.push(src); }
    } catch { src = url; }
    const a = new Audio(src);
    a.preload = 'auto';
    try { a.load(); } catch { /* jsdom */ }
    return a;
  }

  private async decodificar(url: string): Promise<AudioListo> {
    const ctx = this.ctx;
    if (!ctx) throw new Error('sin AudioContext');
    const r = await fetch(url);
    if (!r.ok) throw new Error(String(r.status));
    // Los bytes se guardan (Blob) antes de decodificar: `decodeAudioData`
    // vacía el ArrayBuffer que recibe, y hacen falta para el <audio>.
    const blob = await r.blob();
    const buffer = await ctx.decodeAudioData(await blob.arrayBuffer());
    const canales = Array.from({ length: buffer.numberOfChannels }, (_, i) => buffer.getChannelData(i));
    const silencio = silencioInicial(canales, buffer.sampleRate);
    const elemento = this.destruido ? null : this.elementoDe(blob, url);
    return {
      duracion: buffer.duration,
      silencio,
      fin: Math.max(silencio, finSonoro(canales, buffer.sampleRate)),
      tramos: tramosSonoros(canales, buffer.sampleRate),
      tocar: (retrasoS, velocidad = 1, alEmpezar) => {
        this.parar();
        if (this.destruido || !elemento) return { parar: () => {}, velocidad };
        if (velocidad !== 1 || ctx.state !== 'running') {
          // Fuera de 1×: el <audio> con preservesPitch (Web Audio cambiaría el
          // tono). Y con el contexto parado (no se reanudó a tiempo), también:
          // su reloj no avanza y la fuente no sonaría cuando toca.
          const r = tocarElemento(elemento, retrasoS, velocidad, alEmpezar);
          this.parando = r.parar;
          return r;
        }
        const fuente = ctx.createBufferSource();
        fuente.buffer = buffer;
        fuente.connect(ctx.destination);
        if (retrasoS >= 0) fuente.start(ctx.currentTime + retrasoS);
        else fuente.start(ctx.currentTime, Math.min(buffer.duration, -retrasoS));
        const parar = () => { try { fuente.stop(); } catch { /* ya parada */ } fuente.disconnect(); };
        this.parando = parar;
        // Programado con precisión de muestra: lo único que llega tarde es lo
        // que tarda en salir por el altavoz.
        alEmpezar?.(latenciaSalida(ctx));
        return { parar, velocidad: 1 };
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
          fin: Number.isFinite(a.duration) ? a.duration : 1,
          tramos: [],
          tocar: (retrasoS, velocidad = 1, alEmpezar) => {
            this.parar();
            if (this.destruido) return { parar: () => {}, velocidad };
            const r = tocarElemento(a, retrasoS, velocidad, alEmpezar);
            this.parando = r.parar;
            return r;
          },
        });
      }, { once: true });
    });
  }
}
