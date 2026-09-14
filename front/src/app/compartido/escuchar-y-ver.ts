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
}

/** Lo que toca el navegador, aparte para poder probarlo sin él. */
export interface EntornoEscuchar {
  crearAudio(url: string): HTMLAudioElement;
  traerSvg(url: string): Promise<Blob>;
  crearUrl(blob: Blob): string;
  revocarUrl(url: string): void;
  hablar(texto: string, voz: VozNavegador, alEmpezar: () => void): boolean;
  callar(): void;
}

const entornoNavegador: EntornoEscuchar = {
  crearAudio: url => { const a = new Audio(url); a.preload = 'auto'; return a; },
  traerSvg: async url => {
    const r = await fetch(url);
    if (!r.ok) throw new Error(String(r.status));
    return r.blob();
  },
  crearUrl: blob => URL.createObjectURL(blob),
  revocarUrl: url => URL.revokeObjectURL(url),
  hablar: (texto, voz, alEmpezar) => {
    if (!texto || typeof speechSynthesis === 'undefined') return false;
    const frase = new SpeechSynthesisUtterance(texto);
    frase.lang = voz;
    frase.rate = 0.85;
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

/** La duración que se le pide al SVG: la del audio, redondeada a 0,1 s (así la
 *  caché no se multiplica) y dentro de lo que acepta la API, 0,3..10. */
export function duracionParaCorte(segundos: number): number | null {
  if (!Number.isFinite(segundos) || segundos <= 0) return null;
  return Math.min(10, Math.max(0.3, Math.round(segundos * 10) / 10));
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
    if (!p.audio) { this.traerCortes(p.cortes, null); return; }
    const a = this.audioDe(p.audio);
    const conDuracion = () => this.traerCortes(p.cortes, duracionParaCorte(a.duration));
    if (Number.isFinite(a.duration) && a.duration > 0) conDuracion();
    else a.addEventListener('loadedmetadata', conDuracion, { once: true });
  }

  escuchar(p: PeticionEscuchar): void {
    const turno = ++this.turno;
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
      if (!(p.texto && this.entorno.hablar(p.texto, p.voz ?? 'en-US', () => arrancar(null)))) arrancar(null);
    };

    if (!p.audio) { porVoz(); return; }
    const a = this.audioDe(p.audio);
    this.audio = a;
    try { a.currentTime = 0; } catch { /* sin metadatos todavía */ }
    a.addEventListener('playing', () => arrancar(duracionParaCorte(a.duration)), { once: true });
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
