import {
  ChangeDetectionStrategy, Component, DestroyRef, ElementRef, afterNextRender, computed, effect, inject, input, signal,
  viewChild,
} from '@angular/core';
import { urlCorteSonido } from '../../nucleo/api';
import { EscenaBoca } from './escena';
import { CATALOGO_PROTOTIPO, CatalogoPoses, DURACION_S, PoseSonido, poseDe } from './poses';

/** La boca en 3D esquemático, girable con el dedo.
 *
 *  `sonido` es el símbolo IPA a enseñar ('' = reposo); `catalogo`, las poses
 *  (por defecto, las cinco del prototipo). Sin WebGL pinta el corte 2D que
 *  llegue en `svg2dUrl` (la ruta la pone quien integre: aquí no hay ninguna
 *  fija), y sin eso, una frase. Con `prefers-reduced-motion` no hay
 *  transiciones: salta a la pose. `conSelector` añade una fila de chips para
 *  elegir sonido, pensada para el prototipo y la demo. */
@Component({
  selector: 'app-boca3d',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (conSelector()) {
      <div class="chips" role="group" aria-label="Sonido">
        <button type="button" class="chip" [class.elegido]="!elegido()" (click)="elegir('')">reposo</button>
        @for (s of simbolos(); track s) {
          <button type="button" class="chip ipa" [class.elegido]="elegido() === s" [attr.aria-pressed]="elegido() === s"
                  (click)="elegir(s)">/{{ s }}/</button>
        }
      </div>
    }
    <div class="visor" [class.tres]="modo() === '3d'">
      <div #lienzo class="lienzo" [hidden]="modo() !== '3d'" role="img" [attr.aria-label]="descripcion()"></div>
      @if (modo() === '2d' && urlRespaldo(); as url) {
        <img class="respaldo" [src]="url" [alt]="descripcion()" />
      } @else if (modo() === '2d') {
        <p class="sin">Este navegador no puede dibujar la boca en 3D.</p>
      }
    </div>
    @if (modo() === '3d') {
      <div class="pie">
        <span class="pista">{{ giroLibre() ? 'Arrastra en cualquier dirección' : 'Arrastra de lado para girar la boca' }}</span>
        <span class="botones">
          <button type="button" class="boton" [attr.aria-pressed]="giroLibre()" [class.activo]="giroLibre()"
                  (click)="alternarGiro()">Girar libremente</button>
          <button type="button" class="boton" (click)="restablecer()">Vista de lado</button>
        </span>
      </div>
    }
    @if (leyenda() && pose()?.leyenda; as l) {
      <p class="leyenda"><strong class="ipa">{{ elegido() ? '/' + elegido() + '/' : 'reposo' }}</strong> · {{ l }}</p>
    }
  `,
  styles: `
    :host { display: block; }
    .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
    .chip { font: inherit; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--borde, #d6deeb);
      background: var(--tarjeta, transparent); color: inherit; cursor: pointer; min-height: 36px; }
    .chip.elegido { background: var(--acento, #2f5bea); color: #fff; border-color: var(--acento, #2f5bea); }
    .ipa { font-family: 'Charis SIL', 'Doulos SIL', 'DejaVu Sans', 'Segoe UI', sans-serif; }
    .visor { position: relative; width: 100%; border-radius: var(--radio, 16px); overflow: hidden;
      background: var(--fondo, #f4f6fb); border: 1px solid var(--borde, #d6deeb); }
    .lienzo { width: 100%; aspect-ratio: 4 / 3; max-height: 420px; }
    .lienzo[hidden] { display: none; }
    .respaldo { display: block; width: 100%; height: auto; }
    .sin { margin: 0; padding: 24px 16px; color: var(--texto-suave, #48566f); text-align: center; }
    .pie { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;
      margin-top: 8px; font-size: .9em; color: var(--texto-tenue, #647189); }
    .botones { display: flex; gap: 6px; }
    .boton { font: inherit; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--borde, #d6deeb);
      background: transparent; color: inherit; cursor: pointer; min-height: 36px; }
    .boton.activo { background: var(--acento-suave, #e6ecff); border-color: var(--acento, #2f5bea);
      color: var(--acento-texto, #2449c9); }
    .leyenda { margin: 8px 0 0; color: var(--texto-suave, #48566f); }
  `,
})
export class Boca3d {
  /** Símbolo IPA a enseñar; vacío es el reposo. */
  readonly sonido = input<string>('');
  readonly acento = input<'ga' | 'rp'>('ga');
  /** Las poses; por defecto, las cinco del prototipo. */
  readonly catalogo = input<CatalogoPoses>(CATALOGO_PROTOTIPO);
  /** El corte 2D para cuando no hay WebGL. Por defecto, el SVG de la API del
   *  sonido elegido (`/api/articulacion/{acento}/{símbolo}.svg`, quieto si se
   *  pide reducir el movimiento); `''` lo apaga y deja solo una frase. */
  readonly svg2dUrl = input<string | null>(null);
  readonly leyenda = input<boolean>(true);
  readonly conSelector = input<boolean>(false);

  /** `2d` es «sin WebGL»: se pinta el corte 2D si hay URL y, si no, una frase. */
  readonly modo = signal<'cargando' | '3d' | '2d'>('cargando');
  /** El lienzo captura también los gestos verticales (sin scroll sobre la boca). */
  readonly giroLibre = signal(false);
  private readonly elegidoPorChip = signal<string | null>(null);
  readonly elegido = computed(() => this.elegidoPorChip() ?? this.sonido());
  readonly simbolos = computed(() => Object.keys(this.catalogo().sonidos));
  readonly pose = computed<PoseSonido | null>(() => poseDe(this.catalogo(), this.elegido(), this.acento()));
  readonly urlRespaldo = computed(() => {
    const dada = this.svg2dUrl();
    if (dada !== null) return dada || null;
    const s = this.elegido();
    if (!s) return null;
    let quieto = false;
    try { quieto = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch { /* sin matchMedia */ }
    return urlCorteSonido(s, this.acento(), quieto);
  });
  readonly descripcion = computed(() => {
    const p = this.pose();
    const s = this.elegido();
    if (!p) return `No sé cómo se articula /${s}/`;
    return s ? `La boca diciendo /${s}/: ${p.leyenda}` : 'La boca en reposo';
  });

  private readonly lienzo = viewChild.required<ElementRef<HTMLDivElement>>('lienzo');
  private escena: EscenaBoca | null = null;

  constructor() {
    const destruir = inject(DestroyRef);
    afterNextRender(() => {
      if (!EscenaBoca.hayWebGL()) {
        this.modo.set('2d');
        return;
      }
      try {
        const host = this.lienzo().nativeElement;
        const estilo = getComputedStyle(host);
        const color = (v: string) => estilo.getPropertyValue(v).trim() || undefined;
        this.escena = new EscenaBoca(host, {
          colores: { lengua: color('--ll-lengua') as string | undefined },
          reducirMovimiento: matchMedia('(prefers-reduced-motion: reduce)').matches,
        });
        this.modo.set('3d');
        const p = this.pose();
        if (p) this.escena.irA(p, 0);
      } catch {
        this.modo.set('2d');
      }
    });
    effect(() => {
      const p = this.pose();
      if (p && this.escena) this.escena.irA(p, Math.max(0.45, (DURACION_S[p.movimiento] ?? 0.3) * 1.6));
    });
    destruir.onDestroy(() => this.escena?.destruir());
  }

  elegir(simbolo: string): void {
    this.elegidoPorChip.set(simbolo);
  }

  restablecer(): void {
    this.escena?.restablecerVista();
  }

  alternarGiro(): void {
    this.giroLibre.update(v => !v);
    this.escena?.girarLibre(this.giroLibre());
  }
}
