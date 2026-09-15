import {
  ChangeDetectionStrategy, Component, DestroyRef, ElementRef, afterNextRender, computed, inject, input, output, signal,
} from '@angular/core';
import { FilaCurva } from '../nucleo/api';
import { cefr, num } from '../nucleo/formato';

interface Punto { x: number; y: number; fila: FilaCurva; }

/** La curva de dificultad de un libro, capítulo a capítulo.
 *
 *  Una sola serie, así que sin leyenda: el título de la tarjeta la nombra. Línea
 *  de 2 px con un velo del mismo tono; con muchos capítulos, el dato crudo va
 *  fino y tenue debajo de la tendencia (media móvil), como en la gráfica de
 *  Gradio. Rejilla en las seis anclas MCER, una línea de «tu nivel» y un
 *  tooltip con cruz al pasar. Los datos están también en una tabla. */
@Component({
  selector: 'app-curva',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="marco" (pointerleave)="hover.set(null)">
      @if (ancho() > 0 && puntos().length) {
        <svg [attr.width]="ancho()" [attr.height]="alto" role="img" [attr.aria-label]="descripcion()"
             (pointermove)="mover($event)" (pointerdown)="mover($event)" (click)="clic()">
          @for (t of ticks; track t.v) {
            <line class="rejilla" [attr.x1]="m.i" [attr.x2]="ancho() - m.d" [attr.y1]="y(t.v)" [attr.y2]="y(t.v)" />
            <text class="eje" [attr.x]="m.i - 8" [attr.y]="y(t.v) + 4" text-anchor="end">{{ t.etiqueta }}</text>
          }
          @if (actualX() !== null) {
            <rect class="actual" [attr.x]="actualX()! - 6" [attr.y]="m.s" width="12" [attr.height]="alto - m.s - m.b" rx="6" />
          }
          <path class="velo" [attr.d]="area()" />
          @if (suavizar()) {
            <path class="linea cruda" [attr.d]="linea(puntos())" />
            <path class="linea" [attr.d]="linea(suaves())" />
          } @else {
            <path class="linea" [attr.d]="linea(puntos())" />
          }
          @if (puntos().length === 1) {
            <!-- Un trazo de un solo punto no pinta nada: se ve el dato como un círculo. -->
            <circle class="punto unico" [attr.cx]="puntos()[0].x" [attr.cy]="puntos()[0].y" r="5" />
          }
          @if (nivelY() !== null) {
            <line class="tu-nivel" [attr.x1]="m.i" [attr.x2]="ancho() - m.d" [attr.y1]="nivelY()" [attr.y2]="nivelY()" />
            <text class="etiqueta-nivel" [attr.x]="ancho() - m.d" [attr.y]="nivelY()! - 6" text-anchor="end">tu nivel</text>
          }
          @for (t of ticksX(); track t.x) {
            <text class="eje" [attr.x]="t.x" [attr.y]="alto - 8" text-anchor="middle">{{ t.etiqueta }}</text>
          }
          @if (hover(); as h) {
            <line class="cruz" [attr.x1]="h.x" [attr.x2]="h.x" [attr.y1]="m.s" [attr.y2]="alto - m.b" />
            <circle class="punto" [attr.cx]="h.x" [attr.cy]="h.y" r="5" />
          }
        </svg>
        @if (hover(); as h) {
          <div class="tooltip" [style.left.px]="tipX(h.x)" [style.top.px]="Math.max(0, h.y - 70)">
            <span class="tenue">Capítulo {{ h.fila.capitulo }}</span>
            <strong>{{ h.fila.titulo || 'Sin título' }}</strong>
            <span>{{ num(h.fila.dificultad) }} · {{ cefr(h.fila.dificultad) }}</span>
            @if (elegible()) { <span class="tenue pequeno">Toca para leerlo</span> }
          </div>
        }
      } @else {
        <div class="esqueleto" [style.height.px]="alto"></div>
      }
    </div>
    <details class="datos">
      <summary>Ver los datos</summary>
      <div class="tabla">
        <table>
          <thead><tr><th>Capítulo</th><th>Título</th><th>Dificultad</th><th>MCER</th></tr></thead>
          <tbody>
            @for (f of filas(); track f.capitulo) {
              <tr><td>{{ f.capitulo }}</td><td>{{ f.titulo }}</td><td>{{ num(f.dificultad) }}</td><td>{{ cefr(f.dificultad) }}</td></tr>
            }
          </tbody>
        </table>
      </div>
    </details>
  `,
  styles: `
    :host { display: block; }
    .marco { position: relative; width: 100%; touch-action: pan-y; }
    svg { display: block; overflow: visible; cursor: crosshair; }
    .rejilla { stroke: var(--borde); stroke-width: 1; }
    .eje { fill: var(--texto-tenue); font-size: 11px; font-variant-numeric: tabular-nums; }
    .velo { fill: var(--acento); opacity: .1; }
    .linea { fill: none; stroke: var(--acento); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
    .linea.cruda { stroke-width: 1; opacity: .35; }
    .tu-nivel { stroke: var(--verde); stroke-width: 1.5; }
    .etiqueta-nivel { fill: var(--texto-suave); font-size: 11px; font-weight: 650; }
    .actual { fill: var(--acento-suave); }
    .cruz { stroke: var(--texto-tenue); stroke-width: 1; }
    .punto { fill: var(--acento); stroke: var(--superficie); stroke-width: 2; }
    .tooltip {
      position: absolute; pointer-events: none; transform: translateX(-50%);
      display: grid; gap: 1px; min-width: 150px; max-width: 240px; padding: .5rem .7rem;
      background: var(--superficie); border: 1px solid var(--borde-fuerte); border-radius: 10px;
      box-shadow: var(--sombra-alta); font-size: .85rem; line-height: 1.35; color: var(--texto);
    }
    .tooltip strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .datos { margin-top: .6rem; font-size: .9rem; }
    .datos summary { cursor: pointer; color: var(--texto-suave); min-height: 32px; display: inline-flex; align-items: center; }
    .tabla { max-height: 260px; overflow: auto; margin-top: .4rem; border: 1px solid var(--borde); border-radius: 10px; }
    table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
    th, td { text-align: left; padding: .35rem .6rem; border-bottom: 1px solid var(--borde); }
    th { position: sticky; top: 0; background: var(--superficie-2); font-weight: 650; }
  `,
})
export class Curva {
  readonly filas = input.required<FilaCurva[]>();
  readonly nivelLector = input<number | null>(null);
  readonly actual = input<number | null>(null);
  readonly elegible = input(true);
  readonly elegir = output<number>();

  protected readonly alto = 230;
  protected readonly m = { i: 44, d: 12, s: 14, b: 28 };
  protected readonly ticks = [0, 0.4, 0.8, 1.2, 1.6, 2.0].map(v => ({ v, etiqueta: cefr(v) }));
  protected readonly ancho = signal(0);
  protected readonly hover = signal<Punto | null>(null);
  protected readonly num = num;
  protected readonly cefr = cefr;
  protected readonly Math = Math;

  private readonly host = inject(ElementRef<HTMLElement>);

  constructor() {
    const destruir = inject(DestroyRef);
    afterNextRender(() => {
      const el = this.host.nativeElement as HTMLElement;
      const medir = () => this.ancho.set(Math.max(240, Math.floor(el.clientWidth)));
      medir();
      const obs = new ResizeObserver(medir);
      obs.observe(el);
      destruir.onDestroy(() => obs.disconnect());
    });
  }

  protected y(v: number): number {
    const alto = this.alto - this.m.s - this.m.b;
    return this.m.s + alto * (1 - Math.min(2, Math.max(0, v)) / 2);
  }

  private x(i: number, n: number): number {
    const util = this.ancho() - this.m.i - this.m.d;
    return this.m.i + (n <= 1 ? util / 2 : (util * i) / (n - 1));
  }

  protected readonly puntos = computed<Punto[]>(() => {
    const filas = this.filas();
    this.ancho();
    return filas.map((f, i) => ({ x: this.x(i, filas.length), y: this.y(f.dificultad), fila: f }));
  });

  protected readonly suavizar = computed(() => this.filas().length >= 24);

  protected readonly suaves = computed<Punto[]>(() => {
    const p = this.puntos();
    const v = Math.max(3, Math.round(p.length / 25));
    const mitad = Math.floor(v / 2);
    return p.map((pt, i) => {
      const tramo = p.slice(Math.max(0, i - mitad), Math.min(p.length, i + mitad + 1));
      const media = tramo.reduce((s, q) => s + q.fila.dificultad, 0) / tramo.length;
      return { ...pt, y: this.y(media) };
    });
  });

  protected linea(p: Punto[]): string {
    return p.map((pt, i) => `${i ? 'L' : 'M'}${pt.x.toFixed(1)},${pt.y.toFixed(1)}`).join('');
  }

  protected readonly area = computed(() => {
    const p = this.suavizar() ? this.suaves() : this.puntos();
    if (!p.length) return '';
    const base = this.y(0);
    return `${this.linea(p)}L${p[p.length - 1].x.toFixed(1)},${base}L${p[0].x.toFixed(1)},${base}Z`;
  });

  protected readonly nivelY = computed(() => {
    const n = this.nivelLector();
    return n == null ? null : this.y(n);
  });

  protected readonly actualX = computed(() => {
    const a = this.actual();
    if (a == null) return null;
    const i = this.filas().findIndex(f => f.indice === a);
    return i < 0 ? null : this.x(i, this.filas().length);
  });

  protected readonly ticksX = computed(() => {
    const f = this.filas();
    if (!f.length) return [];
    const idx = f.length === 1 ? [0] : [0, Math.floor((f.length - 1) / 2), f.length - 1];
    return [...new Set(idx)].map(i => ({ x: this.x(i, f.length), etiqueta: `cap. ${f[i].capitulo}` }));
  });

  protected readonly descripcion = computed(() => {
    const f = this.filas();
    if (!f.length) return 'Sin datos';
    const min = f.reduce((a, b) => (b.dificultad < a.dificultad ? b : a));
    const max = f.reduce((a, b) => (b.dificultad > a.dificultad ? b : a));
    return `Dificultad de ${f.length} ${f.length === 1 ? 'capítulo' : 'capítulos'}, entre ${num(min.dificultad)} (capítulo ${min.capitulo}) y ${num(max.dificultad)} (capítulo ${max.capitulo}).`;
  });

  protected mover(ev: PointerEvent): void {
    const svg = ev.currentTarget as SVGSVGElement;
    const x = ev.clientX - svg.getBoundingClientRect().left;
    const p = this.puntos();
    if (!p.length) return;
    let mejor = p[0];
    for (const pt of p) if (Math.abs(pt.x - x) < Math.abs(mejor.x - x)) mejor = pt;
    this.hover.set(mejor);
  }

  protected clic(): void {
    const h = this.hover();
    if (h && this.elegible() && h.fila.indice != null) this.elegir.emit(h.fila.indice);
  }

  protected tipX(x: number): number {
    return Math.min(Math.max(x, 90), this.ancho() - 90);
  }
}
