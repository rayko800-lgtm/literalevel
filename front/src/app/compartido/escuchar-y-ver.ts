import { signal } from '@angular/core';

/** Voz del navegador para cuando no hay mp3. */
export type VozNavegador = 'en-US' | 'en-GB';

/** Un corte de la boca en pantalla. `base` es lo que pinta antes de pulsar (el
 *  ciclo en bucle); `animada(dur)` la pasada única que acompaña al audio, con
 *  su duración en segundos si se sabe, o null si no hay que moverlo («reducir
 *  movimiento»). */
export interface CorteEnPantalla {
  clave: string;
  base: string;
  animada: (dur: number | null) => string | null;
}

export interface PeticionEscuchar {
  /** mp3 ya resuelto contra el motor (urlMotor), o null. */
  audio: string | null;
  /** Si el mp3 falta o no suena, lo dice la voz del navegador. */
  texto?: string;
  voz?: VozNavegador;
  /** Los cortes que vuelven a empezar cuando empieza a sonar. */
  cortes: CorteEnPantalla[];
  /** «Más lento» (Miguel, 14 sep): 1, 0,5 o 0,25. El audio va a esa velocidad
   *  sin cambiar el tono y el corte dura lo que dura el audio así. */
  velocidad?: number;
}

/** Lo que toca el navegador, aparte para poder probarlo sin él. */
export interface EntornoEscuchar {
  crearAudio(url: string): HTMLAudioElement;
  traerSvg(url: string): Promise<Blob>;
  crearUrl(blob: Blob): string;
  revocarUrl(url: string): void;
  hablar(texto: string, voz: VozNavegador, alEmpezar: () => void, velocidad: number): boolean;
  callar(): void;
}

const entornoNavegador: EntornoEscuchar = {
  crearAudio: url => { const a = new Audio(url); a.preload = 'auto'; return a; },
  traerSvg: async url => {
    // La anatomía debe venir del motor actual: una respuesta antigua de la
    // caché HTTP no puede reaparecer al convertirla en blob en cada replay.
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(String(r.status));
    return r.blob();
  },
  crearUrl: blob => URL.createObjectURL(blob),
  revocarUrl: url => URL.revokeObjectURL(url),
  hablar: (texto, voz, alEmpezar, velocidad) => {
    if (!texto || typeof speechSynthesis === 'undefined') return false;
    const frase = new SpeechSynthesisUtterance(texto);
    frase.lang = voz;
    frase.rate = Math.max(0.1, 0.85 * velocidad);
    const voces = speechSynthesis.getVoices();
    const elegida = voces.find(v => v.lang === voz) ?? voces.find(v => v.lang.startsWith('en'));
    if (elegida) frase.voice = elegida;
    frase.onstart = alEmpezar;
    speechSynthesis.cancel();
    speechSynthesis.speak(frase);
    return true;
  },
  callar: () => { if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel(); },
};

/** Tope de la duración que se le pide al SVG: un mp3 de sonido dura hasta 8,4 s
 *  y a 0,25× pasa de 30. */
export const DURACION_MAXIMA = 30;

/** La duración que se le pide al SVG: la del audio, redondeada a 0,1 s (así la
 *  caché no se multiplica) y dentro de lo que acepta la API, 0,3..30. */
export function duracionParaCorte(segundos: number): number | null {
  if (!Number.isFinite(segundos) || segundos <= 0) return null;
  return Math.min(DURACION_MAXIMA, Math.max(0.3, Math.round(segundos * 10) / 10));
}

/** Velocidades de «Más lento»: 1, 0,5 y 0,25; lo demás vuelve a 1. */
export function velocidadValida(v: number | undefined): number {
  return v === 0.5 || v === 0.25 ? v : 1;
}

/** «Escuchar y ver» (Miguel, 14 sep): un botón que hace sonar el sonido o la
 *  palabra y, en el mismo instante, vuelve a empezar la animación del corte,
 *  una sola pasada que dura lo que el audio (contrato de entrega-4e: `dur` en
 *  segundos y `una=1`).
 *
 *  Una animación dentro de un <img> no se rebobina: empieza al cargar el
 *  documento. Así que cada vuelta es un documento nuevo, un `blob:` distinto
 *  hecho con el SVG ya descargado (arranca al instante, sin red). Si aún no
 *  había llegado, la URL con `r=n`, que la API ignora.
 *
 *  El audio se arranca dentro del clic (iOS no deja hacerlo después de un
 *  await) y el corte se cambia con el evento `playing`, que es cuando suena de
 *  verdad. Por eso conviene `preparar` al enseñar el botón: así se sabe la
 *  duración y el SVG está en memoria al pulsar. Si el mp3 falla, habla la voz
 *  del navegador y el corte arranca con ella; si tampoco hay voz, arranca solo. */
export class EscucharYVer {
  private readonly vivos = signal<Record<string, { base: string; url: string }>>({});
  private readonly svgs = new Map<string, Promise<Blob | null>>();
  private readonly listos = new Map<string, Blob | null>();
  private readonly audios = new Map<string, HTMLAudioElement>();
  private audio: HTMLAudioElement | null = null;
  private turno = 0;
  private vuelta = 0;
  /** Cuenta las pulsaciones: la boca 3D la escucha para lanzar su ciclo. */
  readonly pulsaciones = signal(0);

  constructor(private readonly entorno: EntornoEscuchar = entornoNavegador) {}

  /** La URL que pinta ahora el corte `clave`: la base mientras no se haya
   *  pulsado, o si la base cambió (otro sonido, otro acento). */
  src(clave: string, base: string): string {
    const v = this.vivos()[clave];
    return v && v.base === base ? v.url : base;
  }

  /** Adelanta lo que se pueda: la duración del mp3 y el SVG de esa duración. */
  preparar(p: PeticionEscuchar): void {
    const velocidad = velocidadValida(p.velocidad);
    if (!p.audio) { this.traerCortes(p.cortes, null); return; }
    const a = this.audioDe(p.audio);
    const conDuracion = () => this.traerCortes(p.cortes, duracionParaCorte(a.duration / velocidad));
    if (Number.isFinite(a.duration) && a.duration > 0) conDuracion();
    else a.addEventListener('loadedmetadata', conDuracion, { once: true });
  }

  escuchar(p: PeticionEscuchar): void {
    const turno = ++this.turno;
    const velocidad = velocidadValida(p.velocidad);
    this.pulsaciones.update(n => n + 1);
    this.parar(false);

    let arrancado = false;
    const arrancar = (dur: number | null) => {
      if (arrancado || turno !== this.turno) return;
      arrancado = true;
      this.reiniciar(p.cortes, dur);
    };
    const porVoz = () => {
      if (turno !== this.turno || arrancado) return;
      if (!(p.texto && this.entorno.hablar(p.texto, p.voz ?? 'en-US', () => arrancar(null), velocidad))) arrancar(null);
    };

    if (!p.audio) { porVoz(); return; }
    const a = this.audioDe(p.audio);
    this.audio = a;
    try { a.currentTime = 0; } catch { /* sin metadatos todavía */ }
    // Más lento sin voz de pato: el navegador estira el audio y mantiene el tono.
    a.playbackRate = velocidad;
    (a as HTMLAudioElement & { preservesPitch?: boolean; webkitPreservesPitch?: boolean }).preservesPitch = true;
    (a as HTMLAudioElement & { webkitPreservesPitch?: boolean }).webkitPreservesPitch = true;
    a.addEventListener('playing', () => arrancar(duracionParaCorte(a.duration / velocidad)), { once: true });
    a.addEventListener('error', porVoz, { once: true });
    const jugada = a.play();
    if (jugada && typeof jugada.catch === 'function') jugada.catch(porVoz);
  }

  /** Para lo que suene (el corte se queda donde esté). */
  parar(tambienTurno = true): void {
    if (tambienTurno) this.turno++;
    this.audio?.pause();
    this.audio = null;
    this.entorno.callar();
  }

  destruir(): void {
    this.parar();
    for (const v of Object.values(this.vivos())) if (v.url.startsWith('blob:')) this.entorno.revocarUrl(v.url);
    this.vivos.set({});
    this.audios.clear();
  }

  private audioDe(url: string): HTMLAudioElement {
    let a = this.audios.get(url);
    if (!a) {
      a = this.entorno.crearAudio(url);
      this.audios.set(url, a);
    }
    return a;
  }

  private traerCortes(cortes: CorteEnPantalla[], dur: number | null): void {
    for (const c of cortes) {
      const url = c.animada(dur);
      if (url && !this.svgs.has(url)) {
        this.svgs.set(url, this.entorno.traerSvg(url).then(
          b => { this.listos.set(url, b); return b; },
          () => { this.listos.set(url, null); return null; },
        ));
      }
    }
  }

  /** Sin esperas: lo que ya está en memoria va como blob y lo demás por red. */
  private reiniciar(cortes: CorteEnPantalla[], dur: number | null): void {
    this.vuelta++;
    const nuevos = { ...this.vivos() };
    for (const c of cortes) {
      const animada = c.animada(dur);
      if (!animada) continue;
      const previa = nuevos[c.clave]?.url;
      if (previa?.startsWith('blob:')) this.entorno.revocarUrl(previa);
      const blob = this.listos.get(animada);
      const url = blob ? this.entorno.crearUrl(blob) : `${animada}${animada.includes('?') ? '&' : '?'}r=${this.vuelta}`;
      nuevos[c.clave] = { base: c.base, url };
    }
    this.vivos.set(nuevos);
    // La siguiente pulsación ya lo tendrá en memoria.
    this.traerCortes(cortes, dur);
  }
}
