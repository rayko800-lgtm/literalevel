import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, computed, inject, input, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Icono } from '../compartido/icono';
// Import directo desde boca3d.ts, no reexportado: con una reexportación el
// @defer no separa el componente y three.js (736 KB) entraba en el chunk de
// Pronunciar en vez de bajar al pulsar «Boca en 3D».
import { Boca3d } from '../compartido/boca3d/boca3d';
import { BOCA3D_ACTIVO } from '../compartido/boca3d/interruptor';
import { CorteEnPantalla, EscucharYVer, PeticionEscuchar } from '../compartido/escuchar-y-ver';
import {
  Acento, Api, CorreccionVoz, Fonema, InventarioSonidos, mensajeError, urlCortePalabra, urlCorteSonido, urlMotor,
} from '../nucleo/api';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';

type Grabacion = 'lista' | 'grabando' | 'grabada';
type Detalle = CorreccionVoz['detalles'][number];

/** Pronunciar: leer una frase en voz alta y saber qué sonido se escapa.
 *
 *  De Laura: los símbolos del AFI a la vista, con su sonido; y un botón de
 *  «Otra frase» para no borrar a mano la anterior. */
@Component({
  selector: 'app-pronunciar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RouterLink, Icono, Boca3d],
  templateUrl: './pronunciar.html',
  styleUrl: './pronunciar.css',
})
export class Pronunciar implements OnInit, OnDestroy {
  readonly frase_ = input<string>(undefined, { alias: 'frase' });
  readonly libro = input<string>();
  readonly cap = input<string>();

  private readonly api = inject(Api);
  protected readonly sesion = inject(Sesion);

  protected frase = '';
  protected readonly estado = signal<Grabacion>('lista');
  protected readonly segundos = signal(0);
  protected readonly audioUrl = signal<string | null>(null);
  protected readonly corrigiendo = signal(false);
  protected readonly resultado = signal<CorreccionVoz | null>(null);
  protected readonly error = signal('');
  protected readonly necesitaEntrar = signal(false);
  protected readonly trayendo = signal(false);
  /** La tabla del AFI: dos acentos, cargados cuando se piden y una sola vez.
   *  El elegido se guarda y es también el de la IPA de la corrección. */
  private readonly preferencias = inject(Preferencias);
  protected readonly acento = this.preferencias.acento;
  private readonly inventarios = signal<Partial<Record<Acento, InventarioSonidos>>>({});
  protected readonly elegido = signal<Fonema | null>(null);
  protected readonly visor3d = signal<string | null>(null);
  /** Interruptor de compilación (compartido/boca3d/interruptor.ts): apagado, sin botones ni three.js. */
  protected readonly boca3d = BOCA3D_ACTIVO;
  protected readonly debiles = signal<{ palabra: string; fallos: number }[]>([]);
  protected readonly avisoDebiles = signal<string | null>(null);

  private grabador: MediaRecorder | null = null;
  private trozos: Blob[] = [];
  private blob: Blob | null = null;
  private tipo = 'audio/webm';
  private reloj: ReturnType<typeof setInterval> | undefined;
  /** «Escuchar y ver»: el audio y el corte 2D arrancan juntos (compartido/escuchar-y-ver.ts). */
  protected readonly eyv = new EscucharYVer();
  /** El visor 3D abierto, si lo hay. Por referencia de plantilla y no por clase:
   *  `viewChild(Boca3d)` usaría la clase como valor y el @defer dejaría de
   *  separar three.js. */
  private readonly visor = viewChild<Boca3d>('visor');

  protected readonly entrada = this.sesion.entrada;
  protected readonly bloqueada = computed(() => {
    const e = this.entrada();
    return !!e && ((e.puerta && !e.dentro) || !e.openai);
  });
  protected readonly contexto = computed(() => {
    const libro = this.libro();
    const cap = Number(this.cap());
    if (libro && Number.isInteger(cap)) return { id: libro, cap };
    const s = this.sesion.inicio()?.seguir;
    return s ? { id: s.id, cap: s.capitulo } : null;
  });
  protected readonly nota = computed(() => {
    const r = this.resultado();
    if (!r) return '';
    if (r.puntuacion >= 90) return '¡Muy bien!';
    if (r.puntuacion >= 70) return 'Bien, con algún detalle';
    return 'Vamos a por ello';
  });
  /** Solo lo que es una palabra: un signo suelto dejaba un subrayado verde
   *  sin nada encima en una línea propia. */
  protected readonly palabrasVisibles = computed(() =>
    (this.resultado()?.palabras ?? []).filter(w => /\p{L}/u.test(w.palabra)));
  protected readonly grupos = computed(() => this.inventarios()[this.acento()]?.grupos ?? null);
  /** La nota propia del acento elegido, si la ficha la trae. */
  protected readonly notaAcento = computed(() => {
    const f = this.elegido()?.ficha;
    if (!f) return '';
    return this.acento() === 'ga' ? f.ga : f.rp;
  });

  ngOnInit(): void {
    const f = (this.frase_() ?? '').trim();
    if (f) this.frase = f.slice(0, 300);
    else if (this.libro()) void this.traerFrase();
    this.cargarDebiles();
  }

  ngOnDestroy(): void {
    this.pararGrabacion(true);
    this.eyv.destruir();
    const u = this.audioUrl();
    if (u) URL.revokeObjectURL(u);
  }

  protected async traerFrase(): Promise<void> {
    const c = this.contexto();
    if (!c) return;
    this.trayendo.set(true);
    try {
      const r = await firstValueFrom(this.api.frase(c.id, c.cap));
      if (r.frase) { this.frase = r.frase; this.descartar(); }
      else this.error.set('No he encontrado una frase de buen tamaño en ese capítulo.');
    } catch (e) {
      this.error.set(mensajeError(e));
    } finally {
      this.trayendo.set(false);
    }
  }

  protected async grabar(): Promise<void> {
    this.error.set('');
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      this.error.set('Este navegador no deja grabar audio. Prueba con Chrome, Edge, Firefox o Safari actualizados.');
      return;
    }
    try {
      const flujo = await navigator.mediaDevices.getUserMedia({ audio: true });
      const tipos = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'];
      this.tipo = tipos.find(t => MediaRecorder.isTypeSupported(t)) ?? '';
      this.grabador = new MediaRecorder(flujo, this.tipo ? { mimeType: this.tipo } : undefined);
      this.trozos = [];
      this.grabador.ondataavailable = ev => { if (ev.data.size) this.trozos.push(ev.data); };
      this.grabador.onstop = () => {
        flujo.getTracks().forEach(t => t.stop());
        this.blob = new Blob(this.trozos, { type: this.grabador?.mimeType || this.tipo || 'audio/webm' });
        const previa = this.audioUrl();
        if (previa) URL.revokeObjectURL(previa);
        this.audioUrl.set(URL.createObjectURL(this.blob));
        this.estado.set('grabada');
      };
      this.grabador.start();
      this.estado.set('grabando');
      this.segundos.set(0);
      this.reloj = setInterval(() => {
        this.segundos.update(s => s + 1);
        if (this.segundos() >= 30) this.pararGrabacion();
      }, 1000);
    } catch {
      this.error.set('No tengo permiso para usar el micrófono. Actívalo en el candado de la barra de direcciones.');
    }
  }

  protected pararGrabacion(silencio = false): void {
    clearInterval(this.reloj);
    if (this.grabador && this.grabador.state !== 'inactive') {
      if (silencio) this.grabador.onstop = null;
      this.grabador.stop();
    }
  }

  protected descartar(): void {
    const u = this.audioUrl();
    if (u) URL.revokeObjectURL(u);
    this.audioUrl.set(null);
    this.blob = null;
    this.estado.set('lista');
    this.resultado.set(null);
  }

  protected async corregir(): Promise<void> {
    if (!this.blob || !this.frase.trim()) return;
    this.corrigiendo.set(true);
    this.error.set('');
    this.necesitaEntrar.set(false);
    const ext = (this.blob.type.includes('mp4') ? 'm4a' : this.blob.type.includes('ogg') ? 'ogg' : 'webm');
    try {
      const r = await firstValueFrom(this.api.practicar(this.frase.trim(), this.blob, `voz.${ext}`, this.acento()));
      this.resultado.set(r);
      const e = this.entrada();
      if (e && r.restantes !== null) this.sesion.entrada.set({ ...e, restantes: r.restantes });
      this.cargarDebiles();
    } catch (err) {
      this.error.set(mensajeError(err));
      this.necesitaEntrar.set(err instanceof HttpErrorResponse && err.status === 403);
    } finally {
      this.corrigiendo.set(false);
    }
  }

  /** «Otra frase ↺»: lo que pidió Laura en vez de borrar a mano. */
  protected otraFrase(): void {
    this.descartar();
    this.error.set('');
    if (this.contexto()) void this.traerFrase();
    else this.frase = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  protected sonar(url: string | null): void {
    this.eyv.escuchar({ audio: urlMotor(url), cortes: [] });
  }

  /** «Escuchar y ver» de la corrección: la palabra suena (su mp3 o, si no hay,
   *  la voz del navegador) y los dos cortes vuelven a empezar. Con el 3D
   *  abierto, el audio lo pone el 3D (verPalabra, en este mismo clic) y aquí
   *  solo se reinicia el 2D, para no oírlo dos veces. */
  protected escucharPalabra(d: Detalle, i: number): void {
    const pedido = this.pedidoPalabra(d, i);
    const visor = this.visor();
    if (visor && this.visor3d() === 'detalle-' + i) {
      visor.verPalabra();
      this.eyv.escuchar({ ...pedido, audio: null, texto: d.audio ? undefined : pedido.texto });
    } else {
      this.eyv.escuchar(pedido);
    }
  }

  /** El altavoz del sonido que falla: suena y su corte vuelve a empezar. */
  protected escucharFonemaDetalle(d: Detalle, i: number): void {
    const pedido: PeticionEscuchar = { audio: urlMotor(d.fonema?.audio), cortes: this.cortesDelDetalle(d, i, true) };
    const visor = this.visor();
    if (visor && this.visor3d() === 'detalle-' + i) {
      visor.escucharYVer();
      this.eyv.escuchar({ ...pedido, audio: null });
    } else {
      this.eyv.escuchar(pedido);
    }
  }

  private pedidoPalabra(d: Detalle, i: number): PeticionEscuchar {
    return { audio: urlMotor(d.audio), texto: d.palabra, voz: d.variante === 'UK' ? 'en-GB' : 'en-US',
      cortes: this.cortesDelDetalle(d, i) };
  }

  /** Con el audio del sonido, su corte dura lo que el mp3; con el de la palabra,
   *  el sonido da su pasada normal y la palabra se estira a la duración del mp3. */
  private cortesDelDetalle(d: Detalle, i: number, soloSonido = false): CorteEnPantalla[] {
    const cortes: CorteEnPantalla[] = [];
    const sonido = this.corteDelSonido(d);
    const f = d.fonema;
    if (sonido && f) {
      cortes.push({ clave: `d${i}-sonido`, base: sonido,
        animada: dur => this.sinMovimiento ? null : urlCorteSonido(f.simbolo, f.acento ?? 'ga', false, soloSonido ? dur : null) });
    }
    const palabra = soloSonido ? null : this.corteDeLaPalabra(d);
    if (palabra && d.ipa) {
      const ipa = d.ipa;
      const acento: Acento = d.variante === 'UK' ? 'rp' : 'ga';
      cortes.push({ clave: `d${i}-palabra`, base: palabra, animada: dur => urlCortePalabra(ipa, acento, dur) });
    }
    return cortes;
  }

  /** «Escuchar y ver» de la ficha y su altavoz: el mp3 del sonido y el corte a
   *  su compás. Con el 3D abierto en el mismo sonido, el audio lo pone el 3D. */
  protected escucharSonido(s: Fonema): void {
    const pedido = this.pedidoSonido(s);
    const visor = this.visor();
    if (visor && this.visor3d() === 'sonido' && this.elegido()?.simbolo === s.simbolo) {
      visor.escucharYVer();
      this.eyv.escuchar({ ...pedido, audio: null });
    } else {
      this.eyv.escuchar(pedido);
    }
  }

  private pedidoSonido(s: Fonema): PeticionEscuchar {
    const acento = this.acento();
    return { audio: urlMotor(s.audio), cortes: [{ clave: 'ficha', base: this.corteSonido(s.simbolo),
      animada: dur => this.sinMovimiento ? null : urlCorteSonido(s.simbolo, acento, false, dur) }] };
  }

  protected verFonemas(ev: Event): void {
    if ((ev.target as HTMLDetailsElement).open) this.cargarSonidos(this.acento());
    else this.visor3d.set(null);
  }

  protected alternarBoca(id: string): void {
    this.visor3d.update(actual => actual === id ? null : id);
  }

  /** Al abrir «Ver cómo se mueve la boca» se adelantan el audio y el SVG, para
   *  que «Escuchar y ver» arranque sin esperar; al cerrarla se cierra el 3D. */
  protected cerrarBoca(ev: Event, d?: Detalle, i?: number): void {
    if ((ev.target as HTMLDetailsElement).open) {
      if (d && i !== undefined) this.eyv.preparar(this.pedidoPalabra(d, i));
    } else {
      this.visor3d.set(null);
    }
  }

  /** «Reducir movimiento» del sistema: el corte de la boca, quieto en su posición. */
  protected readonly sinMovimiento =
    typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

  protected corteSonido(simbolo: string): string {
    return urlCorteSonido(simbolo, this.acento(), this.sinMovimiento);
  }

  /** Primero el sonido que falla y luego la palabra entera (lo pidió Miguel).
   *  El corte, en el inventario del símbolo que da la API: RP con acento UK si
   *  hay equivalente; si no (/ɝ/, /ɚ/), el americano. */
  protected corteDelSonido(d: Detalle): string | null {
    return d.fonema ? urlCorteSonido(d.fonema.simbolo, d.fonema.acento ?? 'ga', this.sinMovimiento) : null;
  }

  /** La palabra sale aunque no haya fonema («tragic» entendido «Mahic»); con
   *  «reducir movimiento», no: solo el sonido quieto. */
  protected corteDeLaPalabra(d: Detalle): string | null {
    if (!d.ipa || this.sinMovimiento) return null;
    return urlCortePalabra(d.ipa, d.variante === 'UK' ? 'rp' : 'ga');
  }

  protected cambiarAcento(acento: Acento): void {
    this.acento.set(acento);
    this.cerrarFicha();
    this.cargarSonidos(acento);
  }

  /** El @defer del 3D no pasa por el router: si falla su chunk (tras publicar un
   *  build nuevo), la recarga automática de nucleo/version.ts no lo ve. */
  protected recargarPara3d(): void {
    location.reload();
  }

  protected cerrarFicha(): void {
    this.elegido.set(null);
    if (this.visor3d() === 'sonido') this.visor3d.set(null);
  }

  /** Tocar un símbolo: suena, abre su ficha debajo de su grupo y su corte arranca con el audio. */
  protected tocarSonido(sonido: Fonema): void {
    const otro = this.elegido()?.simbolo !== sonido.simbolo;
    this.elegido.set(sonido);
    // Con otro sonido, el 3D abierto aún tiene el anterior: suena por aquí.
    if (otro) this.eyv.escuchar(this.pedidoSonido(sonido));
    else this.escucharSonido(sonido);
  }

  private cargarSonidos(acento: Acento): void {
    if (this.inventarios()[acento]) return;
    this.api.fonemas(acento).subscribe({
      next: inv => this.inventarios.update(m => ({ ...m, [acento]: inv })),
      error: e => this.error.set(mensajeError(e)),
    });
  }

  private cargarDebiles(): void {
    this.api.debiles().subscribe({
      next: r => { this.debiles.set(r.palabras.slice(0, 10)); this.avisoDebiles.set(r.aviso ?? null); },
      error: () => {},
    });
  }

  protected abrirAjustes(): void { this.sesion.ajustesAbiertos.set(true); }
}
