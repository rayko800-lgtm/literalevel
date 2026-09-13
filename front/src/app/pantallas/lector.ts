import {
  ChangeDetectionStrategy, Component, ElementRef, HostListener, OnDestroy, computed, effect, inject, input, signal,
  untracked, viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Icono } from '../compartido/icono';
import { Api, Capitulo, Libro, Medida, Palabra, mensajeError, urlMotor } from '../nucleo/api';
import { cefr, miles, minutosDe, num } from '../nucleo/formato';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';

const PISTA = 'literalevel.pista-palabra';

/** El lector: la pantalla protagonista.
 *
 *  Lo que viene de la investigación y de las lectoras: una sola columna de
 *  ~64 caracteres sin justificar; un solo desplazamiento (nada de caja con su
 *  propio scroll); la palabra se consulta seleccionándola, con `selectionchange`
 *  porque iOS no emite `mouseup`; al cambiar de capítulo se sube arriba; y al
 *  final del capítulo, «Siguiente» y «Parar aquí» del MISMO tamaño: el suspense
 *  lo pone el autor, la decisión de seguir es del lector (retencion_movil.md). */
@Component({
  selector: 'app-lector',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, FormsModule, Icono],
  templateUrl: './lector.html',
  styleUrl: './lector.css',
})
export class Lector implements OnDestroy {
  readonly id = input.required<string>();
  readonly cap = input.required<string>();

  private readonly api = inject(Api);
  private readonly sesion = inject(Sesion);
  private readonly router = inject(Router);
  protected readonly prefs = inject(Preferencias);

  protected readonly libro = signal<Libro | null>(null);
  protected readonly capitulo = signal<Capitulo | null>(null);
  protected readonly cargando = signal(true);
  protected readonly descargando = signal(false);
  protected readonly error = signal('');
  protected readonly avance = signal(0);
  protected readonly indiceAbierto = signal(false);
  protected readonly pista = signal(this.leerPista());

  protected readonly medida = signal<Medida | null>(null);
  protected readonly midiendo = signal(false);
  protected readonly errorMedida = signal('');

  protected readonly palabra = signal<Palabra | null>(null);
  protected readonly consultada = signal('');
  protected readonly buscandoPalabra = signal(false);
  protected readonly explicando = signal(false);
  protected readonly errorPalabra = signal('');
  protected readonly panelAbierto = signal(false);
  protected otraPalabra = '';

  private readonly texto = viewChild<ElementRef<HTMLElement>>('texto');
  private carga = 0;
  private consulta = 0;
  private espera: ReturnType<typeof setTimeout> | undefined;
  private reloj: ReturnType<typeof setTimeout> | undefined;
  private audio: HTMLAudioElement | null = null;

  protected readonly perfil = this.sesion.perfil;
  /** Los párrafos listos para pintar. Gutenberg marca la cursiva con
   *  `_guiones bajos_` y separa escenas con filas de asteriscos: una se pinta
   *  en cursiva y la otra como un separador, no como texto crudo. */
  protected readonly parrafos = computed(() =>
    (this.capitulo()?.parrafos ?? []).map(p => ({
      separador: /^[\s*·•]+$/.test(p),
      trozos: p.split(/_([^_]+)_/g).map((t, i) => ({ t, cursiva: i % 2 === 1 })).filter(x => x.t),
    })));
  protected readonly indice = computed(() => this.capitulo()?.indice ?? 0);
  protected readonly total = computed(() => this.libro()?.capitulos.length ?? 0);
  protected readonly anterior = computed(() => (this.indice() > 0 ? this.indice() - 1 : null));
  protected readonly siguiente = computed(() => (this.indice() + 1 < this.total() ? this.indice() + 1 : null));
  protected readonly sugeridos = computed(() => new Set((this.libro()?.sugeridos ?? []).map(s => s.indice)));
  protected readonly entrada = this.sesion.entrada;

  protected readonly num = num;
  protected readonly cefr = cefr;
  protected readonly miles = miles;
  protected readonly minutosDe = minutosDe;

  constructor() {
    effect(() => {
      const id = this.id();
      const cap = this.cap();
      untracked(() => void this.cargar(id, cap));
    });
  }

  ngOnDestroy(): void {
    clearTimeout(this.espera);
    clearTimeout(this.reloj);
    this.audio?.pause();
  }

  private async cargar(id: string, cap: string): Promise<void> {
    const token = ++this.carga;
    this.cargando.set(true);
    this.error.set('');
    this.medida.set(null);
    this.errorMedida.set('');
    this.indiceAbierto.set(false);
    this.cerrarPalabra();
    // Si el libro tarda más de un segundo es que se está descargando: se dice.
    clearTimeout(this.reloj);
    this.reloj = setTimeout(() => { if (token === this.carga && !this.libro()) this.descargando.set(true); }, 1000);
    try {
      if (this.libro()?.id !== id) this.libro.set(null);
      const libro = await this.sesion.libro(id);
      if (token !== this.carga) return;
      this.libro.set(libro);
      this.descargando.set(false);
      const n = cap === 'auto' ? libro.inicial : Number(cap);
      if (!Number.isInteger(n) || n < 0 || n >= libro.capitulos.length || cap === 'auto') {
        const destino = Number.isInteger(n) && n >= 0 && n < libro.capitulos.length ? n : libro.inicial;
        void this.router.navigate(['/leer', id, destino], { replaceUrl: true });
        return;
      }
      const c = await firstValueFrom(this.api.capitulo(id, n));
      if (token !== this.carga) return;
      this.capitulo.set(c);
      this.avance.set(0);
      window.scrollTo({ top: 0, behavior: 'auto' });
      this.api.progreso(id, n).subscribe({ next: () => void this.sesion.refrescar(), error: () => {} });
    } catch (e) {
      if (token === this.carga) this.error.set(mensajeError(e, 'No he podido abrir este libro.'));
    } finally {
      if (token === this.carga) {
        this.cargando.set(false);
        this.descargando.set(false);
      }
    }
  }

  protected ir(n: number | null): void {
    if (n == null) return;
    void this.router.navigate(['/leer', this.id(), n]);
  }

  // --- Avance dentro del capítulo --------------------------------------------------

  @HostListener('window:scroll')
  protected alDesplazar(): void {
    const el = this.texto()?.nativeElement;
    if (!el) return;
    const caja = el.getBoundingClientRect();
    const recorrido = caja.height - window.innerHeight * 0.6;
    const hecho = -caja.top + window.innerHeight * 0.2;
    this.avance.set(Math.max(0, Math.min(1, recorrido > 0 ? hecho / recorrido : 1)));
  }

  @HostListener('document:keydown', ['$event'])
  protected alTeclear(ev: KeyboardEvent): void {
    const t = ev.target as HTMLElement | null;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    if (ev.key === 'Escape') { this.cerrarPalabra(); this.indiceAbierto.set(false); }
    if (ev.altKey || ev.ctrlKey || ev.metaKey) return;
    if (ev.key === 'ArrowRight' && this.siguiente() != null) this.ir(this.siguiente());
    if (ev.key === 'ArrowLeft' && this.anterior() != null) this.ir(this.anterior());
  }

  // --- La palabra ------------------------------------------------------------------

  @HostListener('document:selectionchange')
  protected alSeleccionar(): void { this.programar(450); }

  @HostListener('document:mouseup')
  protected alSoltar(): void { this.programar(30); }

  private programar(ms: number): void {
    clearTimeout(this.espera);
    this.espera = setTimeout(() => this.capturar(), ms);
  }

  private capturar(): void {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    const el = this.texto()?.nativeElement;
    if (!el || !sel.anchorNode || !el.contains(sel.anchorNode)) return;
    // Sin la puntuación de los bordes: «bank,» es «bank».
    const txt = sel.toString().trim().replace(/^[^\p{L}]+|[^\p{L}]+$/gu, '');
    // Una palabra o un phrasal verb corto; más que eso es subrayar para leer.
    if (!txt || txt.split(/\s+/).length > 4 || txt.length > 40) return;
    if (txt.toLowerCase() === this.consultada().toLowerCase() && this.panelAbierto()) return;
    void this.consultar(txt);
  }

  protected consultarEscrita(): void {
    const p = this.otraPalabra.trim();
    if (p) void this.consultar(p);
    this.otraPalabra = '';
  }

  /** Dos etapas: el diccionario llega en milisegundos y la explicación de
   *  contexto después. La etapa completa se pide siempre: es la que apunta la
   *  palabra en el cuaderno. */
  protected async consultar(texto: string): Promise<void> {
    const token = ++this.consulta;
    this.cerrarPista();
    this.consultada.set(texto);
    this.panelAbierto.set(true);
    this.palabra.set(null);
    this.errorPalabra.set('');
    this.buscandoPalabra.set(true);
    this.explicando.set(false);
    const cuerpo = { palabra: texto, libro_id: this.id(), capitulo: this.indice(), idioma: this.prefs.idioma() };
    try {
      const rapida = await firstValueFrom(this.api.palabra({ ...cuerpo, etapa: 'diccionario' }));
      if (token !== this.consulta) return;
      this.palabra.set(rapida);
      this.buscandoPalabra.set(false);
      this.explicando.set(rapida.explicacion_pendiente);
      const completa = await firstValueFrom(this.api.palabra({ ...cuerpo, etapa: 'completa' }));
      if (token !== this.consulta) return;
      this.palabra.set(completa);
    } catch (e) {
      if (token === this.consulta) {
        // Si ya hay diccionario, el fallo de la explicación va como aviso.
        if (this.palabra()) {
          const p = this.palabra()!;
          this.palabra.set({ ...p, avisos: [...p.avisos, mensajeError(e)] });
        } else {
          this.errorPalabra.set(mensajeError(e));
        }
      }
    } finally {
      if (token === this.consulta) {
        this.buscandoPalabra.set(false);
        this.explicando.set(false);
      }
    }
  }

  protected cerrarPalabra(): void {
    this.consulta++;
    this.panelAbierto.set(false);
    this.palabra.set(null);
    this.consultada.set('');
  }

  protected sonar(url: string | null): void {
    const src = urlMotor(url);
    if (!src) return;
    this.audio?.pause();
    this.audio = new Audio(src);
    void this.audio.play().catch(() => {});
  }

  protected abrirAjustes(): void { this.sesion.ajustesAbiertos.set(true); }

  private leerPista(): boolean {
    try { return localStorage.getItem(PISTA) !== 'vista'; } catch { return true; }
  }

  protected cerrarPista(): void {
    this.pista.set(false);
    try { localStorage.setItem(PISTA, 'vista'); } catch { /* sin almacenamiento */ }
  }

  // --- Medir el capítulo -------------------------------------------------------------

  protected async medir(): Promise<void> {
    this.midiendo.set(true);
    this.errorMedida.set('');
    try {
      this.medida.set(await firstValueFrom(this.api.medirCapitulo(this.id(), this.indice())));
    } catch (e) {
      this.errorMedida.set(mensajeError(e));
    } finally {
      this.midiendo.set(false);
    }
  }

  protected readonly rarezas: Record<string, string> = {
    muy_comun: 'muy común', frecuente: 'frecuente', poco_frecuente: 'poco frecuente', rara: 'rara',
  };
}
