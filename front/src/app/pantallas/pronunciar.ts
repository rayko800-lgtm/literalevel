import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, computed, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Icono } from '../compartido/icono';
import { Acento, Api, CorreccionVoz, Fonema, InventarioSonidos, mensajeError, urlMotor } from '../nucleo/api';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';

type Grabacion = 'lista' | 'grabando' | 'grabada';

/** Pronunciar: leer una frase en voz alta y saber qué sonido se escapa.
 *
 *  De Laura: los símbolos del AFI a la vista, con su sonido; y un botón de
 *  «Otra frase» para no borrar a mano la anterior. */
@Component({
  selector: 'app-pronunciar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RouterLink, Icono],
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
  protected readonly debiles = signal<{ palabra: string; fallos: number }[]>([]);

  private grabador: MediaRecorder | null = null;
  private trozos: Blob[] = [];
  private blob: Blob | null = null;
  private tipo = 'audio/webm';
  private reloj: ReturnType<typeof setInterval> | undefined;
  private audio: HTMLAudioElement | null = null;

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
    this.audio?.pause();
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
    const src = urlMotor(url);
    if (!src) return;
    this.audio?.pause();
    this.audio = new Audio(src);
    void this.audio.play().catch(() => {});
  }

  protected verFonemas(ev: Event): void {
    if ((ev.target as HTMLDetailsElement).open) this.cargarSonidos(this.acento());
  }

  protected cambiarAcento(acento: Acento): void {
    this.acento.set(acento);
    this.elegido.set(null);
    this.cargarSonidos(acento);
  }

  /** Tocar un símbolo: suena y abre su ficha debajo de su grupo. */
  protected tocarSonido(sonido: Fonema): void {
    this.elegido.set(sonido);
    this.sonar(sonido.audio);
  }

  private cargarSonidos(acento: Acento): void {
    if (this.inventarios()[acento]) return;
    this.api.fonemas(acento).subscribe({
      next: inv => this.inventarios.update(m => ({ ...m, [acento]: inv })),
      error: e => this.error.set(mensajeError(e)),
    });
  }

  private cargarDebiles(): void {
    this.api.debiles().subscribe({ next: r => this.debiles.set(r.palabras.slice(0, 10)), error: () => {} });
  }

  protected abrirAjustes(): void { this.sesion.ajustesAbiertos.set(true); }
}
