import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, HostListener, computed, effect, inject, signal, viewChild } from '@angular/core';
import { OpcionPaso, Tutorial } from '../nucleo/tutorial';
import { Sesion } from '../nucleo/sesion';

/** Cuánto se espera a que aparezca el elemento objetivo antes de rendirse y
 *  mostrar una tarjeta centrada sin spotlight. Nunca espera para siempre. */
const ESPERA_MAXIMA_MS = 1500;
const REINTENTO_MS = 150;

/** Overlay del tutorial guiado v2. Vive en la raíz de la app (junto a
 *  `<app-ajustes>`), no dentro de una pantalla, para sobrevivir a los
 *  cambios de ruta: el tutorial cruza varias pantallas.
 *
 *  Tres formas de mostrarse, según el paso (`nucleo/tutorial.ts`):
 *  - **de elección** (`opciones`): tarjeta con sus propios botones.
 *  - **de objetivo real** (`objetivo`, vía `[data-tutorial="..."]`, nunca
 *    `nth-child` ni una clase de estilo): existe ya → spotlight normal,
 *    posicionado sobre el elemento; todavía no existe → espera acotada,
 *    reintentando cada 150 ms; sigue sin existir tras la espera → tarjeta
 *    centrada sin spotlight, con «Reintentar». Nunca un botón «Siguiente»
 *    además de la acción real: el avance lo dispara `tutorial.ts` al
 *    detectar esa acción (ver sus `effect`s).
 *  - **silencioso** (`silencioso`): nada de tarjeta ni foco robado, solo un
 *    indicador pequeño, no modal, con «Salir».
 *  En cualquier forma: «Saltar»/Escape cierran siempre, «Atrás» solo si el
 *  paso lo permite. */
@Component({
  selector: 'app-spotlight',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (visible(); as p) {
      <div class="velo-tutorial"></div>
      <section class="tarjeta-tutorial" role="dialog" aria-modal="true" aria-labelledby="titulo-tutorial"
                [class.centrada]="!posicion()"
                [style.top.px]="posicion()?.top" [style.left.px]="posicion()?.left">
        <header>
          <button type="button" class="boton pequeno fantasma saltar" (click)="tutorial.saltar()">Saltar</button>
        </header>
        <h2 id="titulo-tutorial" #titulo tabindex="-1">{{ p.titulo }}</h2>
        <p>{{ p.texto }}</p>
        @if (p.objetivo && !posicion() && !esperando()) {
          <p class="aviso">No encuentro esa parte de la pantalla ahora mismo.</p>
        }
        @if (tutorial.avisoTransitorio(); as a) {
          <p class="aviso">{{ a }}</p>
        }
        <div class="acciones-tutorial">
          @if (tutorial.puedeAtras()) {
            <button type="button" class="boton secundario" (click)="tutorial.atras()">Atrás</button>
          }
          @if (p.objetivo && !posicion() && !esperando()) {
            <button type="button" class="boton secundario" (click)="reintentar()">Reintentar</button>
          }
          @for (o of p.opciones ?? []; track o.etiqueta) {
            <button type="button" class="boton bloque" (click)="tutorial.elegir(o)">{{ o.etiqueta }}</button>
          }
        </div>
      </section>
    }
    @if (pill(); as p) {
      <div class="pildora-tutorial" role="status">
        <span>Tutorial · {{ p.texto }}</span>
        <button type="button" class="boton pequeno fantasma" (click)="tutorial.saltar()">Salir</button>
      </div>
    }
  `,
  styles: `
    :host { position: fixed; inset: 0; z-index: 95; pointer-events: none; }
    .velo-tutorial { position: absolute; inset: 0; background: var(--velo); pointer-events: auto; }
    .tarjeta-tutorial {
      position: fixed; width: min(360px, calc(100% - 2rem)); max-height: calc(100svh - 2rem); overflow: auto;
      display: grid; gap: .75rem; padding: 1.1rem 1.1rem 1.25rem; border-radius: var(--radio-lg);
      background: var(--superficie); border: 1px solid var(--borde); box-shadow: var(--sombra-alta);
      pointer-events: auto;
    }
    .tarjeta-tutorial.centrada { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); }
    header { display: flex; align-items: center; gap: .6rem; }
    .saltar { margin-left: auto; }
    h2 { margin: 0; font-size: 1.2rem; line-height: 1.25; }
    h2:focus { outline: none; }
    p { margin: 0; font-size: .95rem; line-height: 1.45; color: var(--texto-suave); }
    .aviso { color: var(--texto-tenue); font-size: .85rem; }
    .acciones-tutorial { display: flex; gap: .5rem; flex-wrap: wrap; }
    .acciones-tutorial .bloque { flex: 1 1 auto; justify-content: center; }
    /* La píldora: no modal, no le quita sitio al contenido ni el foco a nada. */
    .pildora-tutorial {
      position: fixed; left: 50%; bottom: calc(1rem + env(safe-area-inset-bottom)); transform: translateX(-50%);
      display: flex; align-items: center; gap: .6rem; padding: .5rem .5rem .5rem .9rem; border-radius: 999px;
      background: var(--superficie); border: 1px solid var(--borde); box-shadow: var(--sombra-alta);
      font-size: .85rem; color: var(--texto-suave); pointer-events: auto;
    }
  `,
})
export class Spotlight {
  protected readonly tutorial = inject(Tutorial);
  private readonly sesion = inject(Sesion);
  private readonly titulo = viewChild<ElementRef<HTMLElement>>('titulo');
  private readonly host = inject(ElementRef<HTMLElement>);

  /** Nunca a la vez que Ajustes. `sesion.bienvenida()` no sirve aquí como
   *  guarda: por defecto es `true` para cualquier visitante nuevo (significa
   *  «no la ha visto todavía», no «se está mostrando ahora»), y usarlo así
   *  ocultaría el tutorial siempre. En su lugar, cuando el tutorial se activa
   *  se cierra la bienvenida vieja explícitamente (ver el `effect` de abajo),
   *  así que los dos nunca compiten de verdad por el foco. */
  private readonly activoSinAjustes = computed(() => this.tutorial.activo() && !this.sesion.ajustesAbiertos());

  protected readonly visible = computed(() => {
    const p = this.activoSinAjustes() ? this.tutorial.pasoActual() : null;
    return p && !p.silencioso ? p : null;
  });

  protected readonly pill = computed(() => {
    const p = this.activoSinAjustes() ? this.tutorial.pasoActual() : null;
    return p?.silencioso ? p : null;
  });

  protected readonly posicion = signal<{ top: number; left: number } | null>(null);
  protected readonly esperando = signal(false);

  private temporizadorLimite: ReturnType<typeof setTimeout> | undefined;
  private intervaloReintento: ReturnType<typeof setInterval> | undefined;
  private focoAnterior: HTMLElement | null = null;
  private estabaVisible = false;
  private ultimoPasoId: string | null = null;

  constructor() {
    effect(() => {
      const p = this.visible();
      this.limpiarTemporizadores();
      if (!p) {
        if (this.estabaVisible) this.restaurarFoco();
        this.estabaVisible = false;
        this.posicion.set(null);
        this.esperando.set(false);
        this.ultimoPasoId = null;
        return;
      }
      if (!this.estabaVisible) {
        this.focoAnterior = typeof document !== 'undefined' ? (document.activeElement as HTMLElement | null) : null;
        // Nunca a la vez que la bienvenida actual (D1.1, punto 6): al activarse
        // el tutorial, se cierra la vieja como si el lector la hubiera saltado.
        this.sesion.cerrarBienvenida();
      }
      this.estabaVisible = true;
      if (p.id !== this.ultimoPasoId) {
        this.ultimoPasoId = p.id;
        this.posicion.set(null);
        if (p.objetivo) this.buscarObjetivo(p.objetivo); else this.esperando.set(false);
      }
      queueMicrotask(() => this.titulo()?.nativeElement.focus());
    });
    inject(DestroyRef).onDestroy(() => this.limpiarTemporizadores());
  }

  private buscarObjetivo(selector: string): void {
    this.esperando.set(true);
    const intentar = (): boolean => {
      const el = document.querySelector<HTMLElement>(selector);
      if (!el) return false;
      const r = el.getBoundingClientRect();
      this.posicion.set({ top: r.top, left: r.left });
      this.esperando.set(false);
      return true;
    };
    if (intentar()) return;
    this.intervaloReintento = setInterval(() => { if (intentar()) this.limpiarTemporizadores(); }, REINTENTO_MS);
    this.temporizadorLimite = setTimeout(() => {
      this.limpiarTemporizadores();
      this.esperando.set(false);
      // Se rinde: `posicion()` sigue en null → tarjeta centrada con «Reintentar».
    }, ESPERA_MAXIMA_MS);
  }

  protected reintentar(): void {
    const p = this.tutorial.pasoActual();
    if (p?.objetivo) this.buscarObjetivo(p.objetivo);
  }

  private limpiarTemporizadores(): void {
    if (this.temporizadorLimite) clearTimeout(this.temporizadorLimite);
    if (this.intervaloReintento) clearInterval(this.intervaloReintento);
    this.temporizadorLimite = undefined;
    this.intervaloReintento = undefined;
  }

  private restaurarFoco(): void {
    const f = this.focoAnterior;
    if (f && f !== document.body && document.contains(f)) f.focus();
    this.focoAnterior = null;
  }

  @HostListener('document:keydown.escape')
  protected alEscape(): void { if (this.visible()) this.tutorial.saltar(); }

  /** Un diálogo de verdad: Tab no sale de la tarjeta (igual que `bienvenida.ts`).
   *  La píldora no es un diálogo (no roba foco), así que no entra aquí. */
  @HostListener('document:keydown.tab', ['$event'])
  @HostListener('document:keydown.shift.tab', ['$event'])
  protected encerrarFoco(ev: Event): void {
    if (!this.visible()) return;
    const botones = [...(this.host.nativeElement as HTMLElement).querySelectorAll<HTMLElement>('.tarjeta-tutorial button')];
    if (!botones.length) return;
    const primero = botones[0];
    const ultimo = botones[botones.length - 1];
    const activo = document.activeElement as HTMLElement | null;
    const atras = (ev as KeyboardEvent).shiftKey;
    const dentro = !!activo && botones.includes(activo);
    if (!dentro || (!atras && activo === ultimo) || (atras && activo === primero)) {
      ev.preventDefault();
      (atras ? ultimo : primero).focus();
    }
  }
}
