import {
  ChangeDetectionStrategy, Component, ElementRef, HostListener, OnDestroy, computed, effect, inject, input, signal,
  untracked, viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Icono } from '../compartido/icono';
import { ControlVelocidad } from '../compartido/control-velocidad';
import { velocidadValida } from '../nucleo/velocidad';
import { LECTURA_VIVO_CERRADA, LecturaVivo } from '../compartido/lectura-vivo/lectura-vivo';
import { familiaDe, paletaDe } from '../compartido/portada';
import { tinteLector } from '../compartido/tinte';
import { Api, Capitulo, Libro, Medida, Palabra, mensajeError, urlMotor } from '../nucleo/api';
import { cefr, miles, minutosDe, num } from '../nucleo/formato';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';
import { Tutorial } from '../nucleo/tutorial';

const PISTA = 'literalevel.pista-palabra';
const PISTA_PAGINAS = 'literalevel.pista-paginas';
/** Hueco entre columnas en modo páginas: cada página avanza su ancho más esto. */
const HUECO = 48;

/** Si el sistema está en oscuro, y se actualiza si cambia (una sola escucha para toda la app). */
const CONSULTA_OSCURO = typeof matchMedia === 'function' ? matchMedia('(prefers-color-scheme: dark)') : null;
const OSCURO_SISTEMA = signal(!!CONSULTA_OSCURO?.matches);
CONSULTA_OSCURO?.addEventListener?.('change', e => OSCURO_SISTEMA.set(e.matches));

function leerBandera(clave: string): boolean {
  try { return localStorage.getItem(clave) !== 'vista'; } catch { return true; }
}

function marcarBandera(clave: string): void {
  try { localStorage.setItem(clave, 'vista'); } catch { /* sin almacenamiento */ }
}

/** El lector: la pantalla protagonista.
 *
 *  Lo que viene de la investigación y de las lectoras: una sola columna de
 *  ~64 caracteres sin justificar; la palabra se consulta seleccionándola, con
 *  `selectionchange` porque iOS no emite `mouseup`; y al final del capítulo,
 *  «Siguiente» y «Parar aquí» del MISMO tamaño.
 *
 *  Dos formas de leer (Ajustes o el botón de la barra):
 *  - **Por páginas**, como un Kindle, que pidió Miguel. Columnas CSS del ancho
 *    de la pantalla; se pasa deslizando o tocando el borde (táctil), con las
 *    flechas o la rueda (ratón). Con ratón no se pasa tocando el borde: el
 *    doble clic es consultar una palabra y pasaría la página dos veces.
 *  - **Seguido**, desplazando.
 *
 *  Y en las dos se guarda dónde ibas dentro del capítulo: Miguel consultó una
 *  palabra, volvió al libro y aparecía al principio. */
@Component({
  selector: 'app-lector',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, FormsModule, Icono, LecturaVivo, ControlVelocidad],
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
  // Solo notifica: el lector no sabe nada del tutorial más allá de avisarle
  // cuándo hay una hoja de palabra local utilizable (D1.4). Tutorial decide
  // qué hacer con eso; nunca al revés.
  private readonly tutorial = inject(Tutorial);

  protected readonly libro = signal<Libro | null>(null);
  protected readonly capitulo = signal<Capitulo | null>(null);
  protected readonly cargando = signal(true);
  protected readonly descargando = signal(false);
  protected readonly error = signal('');
  protected readonly avance = signal(0);
  protected readonly indiceAbierto = signal(false);
  protected readonly pista = signal(leerBandera(PISTA));

  /** Solo los «PG…» se bajan de Gutenberg; los libres salen del corpus abierto. */
  protected readonly esGutenberg = computed(() => /^pg/i.test(this.id()));
  /** Claro u oscuro, como el resto de la app: «Noche», o «Automático» con el sistema en oscuro. */
  private readonly oscuro = computed(() => {
    const t = this.prefs.tema();
    return t === 'noche' || (t === 'sistema' && OSCURO_SISTEMA());
  });
  /** La hoja toma el fondo y el acento de la portada del libro (Miguel, 14 sep),
   *  con el texto a 7:1 o más (compartido/tinte.ts). Se apaga en Ajustes. */
  protected readonly estiloTinte = computed(() => {
    const l = this.libro();
    if (!l || this.prefs.colorDelLibro() === 'no') return '';
    const t = tinteLector(paletaDe(l.id, familiaDe(l.temas)), this.oscuro());
    return `--lector-fondo: ${t.fondo}; --lector-texto: ${t.texto}; --acento: ${t.acento}; ` +
      `--acento-texto: ${t.acentoTexto}; --acento-suave: ${t.acentoSuave}; --seleccion: ${t.seleccion};`;
  });

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

  protected readonly paginado = computed(() => this.prefs.modoLectura() === 'paginas');
  protected readonly pagina = signal(0);
  protected readonly paginas = signal(1);

  private readonly texto = viewChild<ElementRef<HTMLElement>>('texto');
  private carga = 0;
  private consulta = 0;
  private espera: ReturnType<typeof setTimeout> | undefined;
  private reloj: ReturnType<typeof setTimeout> | undefined;
  private relojPosicion: ReturnType<typeof setTimeout> | undefined;
  private relojRecolocar: ReturnType<typeof setTimeout> | undefined;
  private audio: HTMLAudioElement | null = null;
  private abrirAlFinal = false;
  private toque: { x: number; y: number; t: number; tipo: string } | null = null;
  private ultimaRueda = 0;
  private readonly observador = typeof ResizeObserver !== 'undefined'
    ? new ResizeObserver(() => requestAnimationFrame(() => this.recolocar()))
    : null;

  protected readonly perfil = this.sesion.perfil;
  /** Los párrafos listos para pintar. Gutenberg marca la cursiva con
   *  `_guiones bajos_` y separa escenas con filas de asteriscos. */
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
  /** Mismo criterio ya usado en Pronunciar (D1.4/D1.5) para saber, sin
   *  esperar respuesta del servidor, si la explicación de contexto va a
   *  estar bloqueada: sin cuenta cuando la puerta la exige, o sin OpenAI.
   *  No cambia el contrato de cuenta/OpenAI, solo lo lee para dar feedback
   *  inmediato (UX-F1, Miguel: el aviso ya existente tardaba en notarse). */
  /** D5: lectura en voz alta en vivo. Necesita cuenta con OpenAI y un
   *  navegador con WebRTC y micrófono. */
  protected readonly lecturaVivoDisponible = computed(() => {
    if (LECTURA_VIVO_CERRADA) return false;  // 4 oct: cerrada por seguridad, el botón no se enseña
    const e = this.entrada();
    return !!e && e.openai && (!e.puerta || e.dentro)
      && typeof RTCPeerConnection !== 'undefined' && !!navigator.mediaDevices?.getUserMedia;
  });
  protected readonly lecturaVivo = signal<{ parrafos: string[]; desde: number } | null>(null);
  private readonly vivo = viewChild<LecturaVivo>('vivo');

  /** Abre la hoja desde el primer párrafo visible del capítulo. */
  protected abrirLecturaVivo(): void {
    const parrafos = (this.capitulo()?.parrafos ?? []).map(p => p.replace(/_([^_]+)_/g, '$1'));
    let desde = 0;
    for (const el of Array.from(document.querySelectorAll<HTMLElement>('[data-parrafo]'))) {
      const r = el.getBoundingClientRect();
      if (r.bottom > 80) { desde = Number(el.dataset['parrafo']) || 0; break; }
    }
    this.lecturaVivo.set({ parrafos, desde });
    setTimeout(() => void this.vivo()?.empezar());
  }

  protected readonly sinPerfilParaExplicar = computed(() => {
    const e = this.entrada();
    return !!e && ((e.puerta && !e.dentro) || !e.openai);
  });
  /** Toast breve al pulsar «Consultar» (o al seleccionar una palabra) sin
   *  perfil: no espera a que la etapa completa resuelva para avisar. */
  protected readonly avisoRapidoPerfil = signal(false);
  /** Pulso corto sobre la tarjeta de aviso ya existente, una vez llega. */
  protected readonly pulsarAvisoPerfil = signal(false);
  private avisoRapidoTimeout: ReturnType<typeof setTimeout> | undefined;

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
    // Cambiar de modo o de tamaño de letra redistribuye el texto: se vuelve a
    // medir conservando por dónde ibas. El temporizador se guarda y se limpia
    // en `ngOnDestroy` como los demás: sin eso, un componente destruido antes
    // de los 30 ms seguía llamando `recolocar()` sobre su propio `nativeElement`
    // ya fuera de uso (jsdom en los tests: `el.scrollTo is not a function`).
    effect(() => {
      this.paginado();
      this.prefs.letra();
      untracked(() => {
        clearTimeout(this.relojRecolocar);
        this.relojRecolocar = setTimeout(() => this.recolocar(), 30);
      });
    });
    // El elemento del texto aparece cuando llega el capítulo: se observa su tamaño
    // (girar el móvil, abrir el panel de la palabra en escritorio).
    effect(() => {
      const el = this.texto()?.nativeElement;
      untracked(() => {
        this.observador?.disconnect();
        if (el) this.observador?.observe(el);
      });
    });
  }

  ngOnDestroy(): void {
    // Invalida cualquier `token === this.carga` todavía pendiente (D2: lo
    // reprodujo un test con temporizadores reales) — en particular el doble
    // requestAnimationFrame de más abajo, que si no se destruye a tiempo
    // sigue viendo su propio token como vigente y llama recolocar()/
    // aplicarPagina() sobre un componente ya destruido.
    this.carga++;
    clearTimeout(this.espera);
    clearTimeout(this.reloj);
    clearTimeout(this.relojPosicion);
    clearTimeout(this.relojRecolocar);
    clearTimeout(this.avisoRapidoTimeout);
    this.observador?.disconnect();
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
      this.pagina.set(0);
      window.scrollTo({ top: 0, behavior: 'auto' });
      // Tras pintar: medir las páginas y volver a donde se había quedado.
      requestAnimationFrame(() => requestAnimationFrame(() => {
        if (token === this.carga) this.restaurarPosicion(id, n);
      }));
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

  protected alternarModo(): void {
    this.prefs.modoLectura.set(this.paginado() ? 'rollo' : 'paginas');
  }

  // --- Dónde ibas ---------------------------------------------------------------

  private clavePosicion(id = this.id(), n = this.indice()): string {
    return `literalevel.pos.${id}.${n}`;
  }

  private leerPosicion(id: string, n: number): number {
    try {
      const v = Number(localStorage.getItem(this.clavePosicion(id, n)));
      return Number.isFinite(v) ? Math.min(1, Math.max(0, v)) : 0;
    } catch {
      return 0;
    }
  }

  /** La escritura de verdad, sin temporizador: la usan tanto el guardado con
   *  espera (`guardarPosicion`) como el volcado inmediato antes de salir del
   *  lector (`alSalirAPronunciar`, D1.4) — una sola lógica, no dos. */
  private escribirPosicion(fraccion: number, clave = this.clavePosicion()): void {
    try { localStorage.setItem(clave, fraccion.toFixed(4)); } catch { /* sin almacenamiento */ }
  }

  private guardarPosicion(fraccion: number): void {
    const clave = this.clavePosicion();
    clearTimeout(this.relojPosicion);
    this.relojPosicion = setTimeout(() => this.escribirPosicion(fraccion, clave), 300);
  }

  /** Antes de ir a Pronunciar desde la hoja de la palabra (D1.4): la posición
   *  se guarda cada 300 ms, pero si el lector se va antes de que pase ese
   *  plazo, «Continuar leyendo» volvería a un punto viejo. Se vuelca ya,
   *  reutilizando `escribirPosicion`, sin duplicar el cálculo de la fracción
   *  (que ya vive en `avance()`, actualizado por el scroll/paso de página). */
  protected alSalirAPronunciar(): void {
    clearTimeout(this.relojPosicion);
    this.escribirPosicion(this.avance());
  }

  private restaurarPosicion(id: string, n: number): void {
    const alFinal = this.abrirAlFinal;
    this.abrirAlFinal = false;
    const f = alFinal ? 1 : this.leerPosicion(id, n);
    if (this.paginado()) {
      this.medirPaginas();
      const ultima = this.paginas() - 1;
      // Casi al final de un capítulo ya leído, se vuelve al principio.
      this.pagina.set(alFinal ? ultima : (f < 0.98 ? Math.round(f * ultima) : 0));
      this.aplicarPagina(false);
      // En un teléfono la fuente del libro puede terminar de cargar DESPUÉS de
      // medir: el texto se redistribuye en otro número de páginas y la posición
      // guardada caía en otro sitio. Se vuelve a medir cuando la fuente está.
      document.fonts?.ready.then(() => setTimeout(() => this.recolocar(), 0)).catch(() => {});
      return;
    }
    const el = this.texto()?.nativeElement;
    if (el && f > 0.02 && f < 0.98) {
      const arriba = el.getBoundingClientRect().top + window.scrollY;
      const recorrido = el.offsetHeight - window.innerHeight * 0.6;
      window.scrollTo({ top: arriba + f * Math.max(0, recorrido) - window.innerHeight * 0.2, behavior: 'auto' });
    }
  }

  /** Tras un cambio de tamaño, de letra o de modo: mismo sitio, otra maqueta. */
  private recolocar(): void {
    if (!this.capitulo()) return;
    const el = this.texto()?.nativeElement;
    if (!el) return;
    if (this.paginado()) {
      const ultimaAntes = Math.max(1, this.paginas() - 1);
      const fraccion = this.pagina() / ultimaAntes;
      this.medirPaginas();
      this.pagina.set(Math.round(fraccion * Math.max(0, this.paginas() - 1)));
      this.aplicarPagina(false);
    } else {
      el.style.columnWidth = '';
      el.style.columnGap = '';
      el.scrollLeft = 0;
      this.alDesplazar();
    }
  }

  // --- Modo páginas ------------------------------------------------------------------

  private medirPaginas(): void {
    const el = this.texto()?.nativeElement;
    if (!el) return;
    const ancho = el.clientWidth;
    if (!ancho) return;
    el.style.columnWidth = `${ancho}px`;
    el.style.columnGap = `${HUECO}px`;
    const total = Math.max(1, Math.round((el.scrollWidth + HUECO) / (ancho + HUECO)));
    this.paginas.set(total);
    if (this.pagina() > total - 1) this.pagina.set(total - 1);
  }

  private aplicarPagina(suave: boolean): void {
    const el = this.texto()?.nativeElement;
    if (!el) return;
    const reducido = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    el.scrollTo({ left: this.pagina() * (el.clientWidth + HUECO), behavior: suave && !reducido ? 'smooth' : 'auto' });
    const ultima = this.paginas() - 1;
    const fraccion = ultima > 0 ? this.pagina() / ultima : 1;
    this.avance.set(fraccion);
    this.guardarPosicion(fraccion);
  }

  protected irPagina(delta: number): void {
    const destino = this.pagina() + delta;
    if (destino < 0) {
      if (this.anterior() != null) {
        this.abrirAlFinal = true;
        this.ir(this.anterior());
      }
      return;
    }
    if (destino >= this.paginas()) {
      if (this.siguiente() != null) this.ir(this.siguiente());
      return;
    }
    this.pagina.set(destino);
    this.aplicarPagina(true);
  }

  protected alTocar(ev: PointerEvent): void {
    // Lo que nace en el borde es del sistema: «volver» en Android y en Safari
    // desde los lados, «inicio» y el acceso fácil desde abajo
    // (investigacion/una_mano.md §2.4). Pasar página ahí sacaba del capítulo.
    const enElBorde = ev.clientX <= 24 || ev.clientX >= window.innerWidth - 24
      || ev.clientY >= window.innerHeight - 32;
    this.toque = enElBorde ? null : { x: ev.clientX, y: ev.clientY, t: Date.now(), tipo: ev.pointerType };
  }

  protected alSoltarToque(ev: PointerEvent): void {
    const t = this.toque;
    this.toque = null;
    if (!t || !this.paginado() || t.tipo === 'mouse') return;
    const sel = window.getSelection();
    if (sel && !sel.isCollapsed) return;          // estaba seleccionando una palabra
    if ((ev.target as HTMLElement).closest('button, a, input')) return;
    const dx = ev.clientX - t.x;
    const dy = ev.clientY - t.y;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
      this.irPagina(dx < 0 ? 1 : -1);
      return;
    }
    if (Date.now() - t.t < 350 && Math.abs(dx) < 12 && Math.abs(dy) < 12) {
      const caja = (ev.currentTarget as HTMLElement).getBoundingClientRect();
      const donde = (ev.clientX - caja.left) / caja.width;
      if (donde > 0.7) this.irPagina(1);
      else if (donde < 0.3) this.irPagina(-1);
    }
  }

  /** La caja de columnas solo debería moverse cuando la mueve `aplicarPagina`.
   *  Pero en Android, al mantener pulsada una palabra, el navegador la desplaza
   *  para enseñar las manijas de la selección, y queda a medio camino entre dos
   *  páginas: lo que se ve, lo que se guarda y a dónde lleva «siguiente» dejaban
   *  de coincidir. Si pasa, se asienta en la página más cercana. */
  private relojAsentar: ReturnType<typeof setTimeout> | undefined;

  protected alMoverColumnas(): void {
    if (!this.paginado()) return;
    clearTimeout(this.relojAsentar);
    this.relojAsentar = setTimeout(() => {
      const el = this.texto()?.nativeElement;
      if (!el) return;
      const paso = el.clientWidth + HUECO;
      const cercana = Math.max(0, Math.min(this.paginas() - 1, Math.round(el.scrollLeft / paso)));
      if (Math.abs(el.scrollLeft - cercana * paso) < 2 && cercana === this.pagina()) return;
      const sel = window.getSelection();
      if (sel && !sel.isCollapsed) return;       // se asienta al terminar de seleccionar
      this.pagina.set(cercana);
      this.aplicarPagina(false);
    }, 250);
  }

  protected alRueda(ev: WheelEvent): void {
    if (!this.paginado() || Math.abs(ev.deltaY) < 15) return;
    ev.preventDefault();
    const ahora = Date.now();
    if (ahora - this.ultimaRueda < 450) return;
    this.ultimaRueda = ahora;
    this.irPagina(ev.deltaY > 0 ? 1 : -1);
  }


  // --- Avance en modo seguido --------------------------------------------------------

  @HostListener('window:scroll')
  protected alDesplazar(): void {
    if (this.paginado()) return;
    const el = this.texto()?.nativeElement;
    if (!el || !this.capitulo()) return;
    const caja = el.getBoundingClientRect();
    const recorrido = caja.height - window.innerHeight * 0.6;
    const hecho = -caja.top + window.innerHeight * 0.2;
    const fraccion = Math.max(0, Math.min(1, recorrido > 0 ? hecho / recorrido : 1));
    this.avance.set(fraccion);
    this.guardarPosicion(fraccion);
  }

  @HostListener('document:keydown', ['$event'])
  protected alTeclear(ev: KeyboardEvent): void {
    const t = ev.target as HTMLElement | null;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    if (ev.key === 'Escape') { this.cerrarPalabra(); this.indiceAbierto.set(false); }
    if (ev.altKey || ev.ctrlKey || ev.metaKey || this.indiceAbierto()) return;
    if (this.paginado()) {
      if (ev.key === 'ArrowRight' || ev.key === 'PageDown') { ev.preventDefault(); this.irPagina(1); }
      if (ev.key === 'ArrowLeft' || ev.key === 'PageUp') { ev.preventDefault(); this.irPagina(-1); }
      return;
    }
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
    // UX-F2: solo ahora, con la selección ya aceptada, se limpia el menú
    // nativo (Copiar/Seleccionar todo/tiradores) — nunca antes de saber que
    // se va a usar (una selección inválida se deja tal cual, sin tocarla).
    // Un nuevo long-press/doble clic crea su propio rango: quitar este no
    // le afecta.
    sel.removeAllRanges();
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
    // UX-F1: feedback al instante, sin esperar la respuesta — el diccionario
    // sigue funcionando igual, solo se avisa de antemano que la explicación
    // de contexto no va a llegar.
    if (this.sinPerfilParaExplicar()) {
      clearTimeout(this.avisoRapidoTimeout);
      this.avisoRapidoPerfil.set(true);
      this.pulsarAvisoPerfil.set(true);
      this.avisoRapidoTimeout = setTimeout(() => this.avisoRapidoPerfil.set(false), 4000);
      setTimeout(() => this.pulsarAvisoPerfil.set(false), 900);
    }
    const cuerpo = { palabra: texto, libro_id: this.id(), capitulo: this.indice(), idioma: this.prefs.idioma() };
    try {
      const rapida = await firstValueFrom(this.api.palabra({ ...cuerpo, etapa: 'diccionario' }));
      if (token !== this.consulta) return;
      this.palabra.set(rapida);
      this.buscandoPalabra.set(false);
      // D1.4: solo cuenta como "seleccionó una palabra" si la hoja local ya
      // tiene algo que enseñar (igual que decide el propio `lector.html` para
      // no mostrar «no está en el diccionario»). Nunca espera a la IA.
      if (rapida.sentido || rapida.acepciones_principales?.length || rapida.ipa_uk || rapida.ipa_us) {
        this.tutorial.notificarLector('palabra');
      }
      this.explicando.set(rapida.explicacion_pendiente);
      const completa = await firstValueFrom(this.api.palabra({ ...cuerpo, etapa: 'completa' }));
      if (token !== this.consulta) return;
      this.palabra.set(completa);
    } catch (e) {
      if (token === this.consulta) {
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

  // --- Hojas inferiores: cerrar desde abajo (investigacion/una_mano.md §2.2) --------

  /** Arrastrar el asa: hacia abajo cierra, hacia arriba expande la hoja. */
  private arrastre: { y: number; hoja: HTMLElement; cerrar: () => void } | null = null;
  protected readonly hojaExpandida = signal(false);

  /** Al abrir el índice, el capítulo actual a la vista; al cerrarlo, la hoja vuelve a media altura. */
  private readonly alAbrirIndice = effect(() => {
    if (this.indiceAbierto()) {
      setTimeout(() => document.querySelector('.lista-indice a.actual')?.scrollIntoView({ block: 'center' }), 0);
    } else {
      this.hojaExpandida.set(false);
    }
  });

  protected empezarArrastre(ev: PointerEvent, cual: 'palabra' | 'indice'): void {
    const hoja = (ev.currentTarget as HTMLElement).closest('aside') as HTMLElement | null;
    if (!hoja) return;
    this.arrastre = {
      y: ev.clientY, hoja,
      cerrar: cual === 'palabra' ? () => this.cerrarPalabra() : () => this.indiceAbierto.set(false),
    };
    hoja.style.transition = 'none';
  }

  @HostListener('document:pointermove', ['$event'])
  protected moverArrastre(ev: PointerEvent): void {
    const a = this.arrastre;
    if (!a) return;
    const dy = ev.clientY - a.y;
    a.hoja.style.transform = dy > 0 ? `translateY(${dy}px)` : '';
  }

  @HostListener('document:pointerup', ['$event'])
  protected soltarArrastre(ev: PointerEvent): void {
    const a = this.arrastre;
    if (!a) return;
    this.arrastre = null;
    a.hoja.style.transition = '';
    a.hoja.style.transform = '';
    const dy = ev.clientY - a.y;
    if (dy > 80) a.cerrar();
    else if (dy < -40) this.hojaExpandida.set(true);
  }

  @HostListener('document:pointercancel')
  protected cancelarArrastre(): void {
    if (!this.arrastre) return;
    this.arrastre.hoja.style.transition = '';
    this.arrastre.hoja.style.transform = '';
    this.arrastre = null;
  }

  protected cerrarPalabra(): void {
    this.consulta++;
    this.hojaExpandida.set(false);
    this.panelAbierto.set(false);
    this.palabra.set(null);
    this.consultada.set('');
    // Al cerrar la ficha la selección desaparece: si el navegador movió las
    // columnas para enseñarla, ahora es cuando se puede asentar la página.
    if (this.paginado()) setTimeout(() => this.alMoverColumnas(), 50);
  }

  /** El audio del diccionario o el generado; si no hay ninguno, la voz del
   *  propio navegador (Web Speech API): no sale nada a la red ni cuesta. */
  protected sonar(url: string | null, palabra = '', acento: 'en-US' | 'en-GB' = 'en-US'): void {
    const src = urlMotor(url);
    if (src) {
      this.audio?.pause();
      this.audio = new Audio(src);
      this.audio.playbackRate = this.velocidadAudio();
      this.audio.preservesPitch = true;
      void this.audio.play().catch(() => this.hablar(palabra, acento));
      return;
    }
    this.hablar(palabra, acento);
  }

  private hablar(texto: string, acento: 'en-US' | 'en-GB'): void {
    if (!texto || typeof speechSynthesis === 'undefined') return;
    const frase = new SpeechSynthesisUtterance(texto);
    frase.lang = acento;
    frase.rate = 0.85 * this.velocidadAudio();
    const voz = speechSynthesis.getVoices().find(v => v.lang === acento)
      ?? speechSynthesis.getVoices().find(v => v.lang.startsWith('en'));
    if (voz) frase.voice = voz;
    speechSynthesis.cancel();
    speechSynthesis.speak(frase);
  }

  protected readonly vozDelNavegador = typeof speechSynthesis !== 'undefined';
  protected readonly velocidadAudio = signal(1);
  protected cambiarVelocidadAudio(valor: number): void {
    this.velocidadAudio.set(velocidadValida(valor));
    if (this.audio) this.audio.playbackRate = this.velocidadAudio();
  }

  protected abrirAjustes(): void { this.sesion.ajustesAbiertos.set(true); }
  /** El «Entrar» de la hoja de la palabra: los ajustes ya en «Tu perfil». */
  protected entrar(): void { this.sesion.abrirPerfil(); }

  /** Un solo aviso la primera vez (tanda 2 de la ayuda, Miguel): antes eran dos a la vez, el
   *  de la palabra arriba y el de pasar página abajo, y del libro se veían dos líneas. El ✕
   *  cierra los dos para siempre en este navegador; el «?» lo vuelve a enseñar. */
  protected readonly tactil = typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches;

  protected cerrarPista(): void {
    this.pista.set(false);
    marcarBandera(PISTA);
    marcarBandera(PISTA_PAGINAS);
  }

  protected verAyuda(): void {
    this.pista.set(true);
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
      setTimeout(() => this.recolocar(), 30);
    }
  }

  protected readonly rarezas: Record<string, string> = {
    muy_comun: 'muy común', frecuente: 'frecuente', poco_frecuente: 'poco frecuente', rara: 'rara',
  };
}
