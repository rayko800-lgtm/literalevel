import { ChangeDetectionStrategy, Component, ElementRef, HostListener, OnDestroy, inject, input, model, output, signal, viewChild } from '@angular/core';
import { etiquetaVelocidad, velocidadValida } from '../nucleo/velocidad';

@Component({
  selector: 'app-control-velocidad',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button #boton type="button" class="disparador-velocidad" [attr.aria-expanded]="abierta()"
      [attr.aria-label]="'Velocidad de reproducción: ' + etiqueta(valor())" (click)="alternar()">
      @if (!compacto()) { <span>Velocidad</span> }
      <strong>{{ etiqueta(valor()) }}</strong>
    </button>
    @if (abierta()) {
      <div #panel popover="manual" class="selector-velocidad" [style.left.px]="izquierda()" [style.top.px]="arriba()" role="group" aria-label="Ajustar velocidad">
        <div class="cabecera"><span>Velocidad</span><strong>{{ etiqueta(valor()) }}</strong>
          <button type="button" aria-label="Cerrar velocidad" (click)="cerrar()">×</button></div>
        <input #barra type="range" aria-label="Velocidad de reproducción" min="0.25" max="2" step="0.01"
          [value]="valor()" [attr.aria-valuetext]="etiqueta(valor())" (input)="cambiar(+$any($event.target).value)" (change)="ajustada.emit()" />
        <div class="extremos"><span>0,25×</span><button type="button" (click)="cambiar(1); ajustada.emit()">Normal · 1×</button><span>2×</span></div>
      </div>
    }
  `,
  styles: `
    :host { position: relative; display: inline-block; min-width: 72px; }
    .disparador-velocidad { width: 100%; min-height: 48px; display: grid; place-content: center; gap: .15rem; padding: .35rem .6rem;
      background: var(--superficie-2); color: var(--acento-texto); border: 1px solid var(--borde-fuerte); border-radius: .75rem; cursor: pointer; white-space: nowrap; }
    .disparador-velocidad span { font-size: .75rem; color: var(--texto-suave); }
    .disparador-velocidad strong { font-size: .85rem; font-variant-numeric: tabular-nums; }
    .disparador-velocidad[aria-expanded=true] { border-color: var(--acento); background: var(--acento-suave); }
    .selector-velocidad { position: fixed; z-index: 160; margin: 0; inset: auto;
      width: min(280px, calc(100vw - 24px)); padding: .85rem; border: 1px solid var(--borde-fuerte); border-radius: 1rem;
      background: var(--superficie); color: var(--texto); box-shadow: 0 8px 30px #0005; }
    .cabecera { display: flex; align-items: center; gap: .75rem; font-size: .85rem; }
    .cabecera strong { margin-left: auto; color: var(--acento-texto); font-variant-numeric: tabular-nums; }
    .cabecera button { width: 36px; height: 36px; font-size: 1.5rem; }
    button { color: inherit; background: transparent; border: 0; cursor: pointer; }
    input { display: block; width: 100%; height: 44px; margin: .25rem 0; accent-color: var(--acento); cursor: pointer; }
    .extremos { display: flex; align-items: center; justify-content: space-between; gap: .5rem; font-size: .75rem; color: var(--texto-suave); }
    .extremos button { min-height: 36px; color: var(--acento-texto); }
  `,
})
export class ControlVelocidad implements OnDestroy {
  readonly valor = model(1);
  readonly compacto = input(false);
  readonly ajustada = output<void>();
  readonly abierta = signal(false);
  readonly izquierda = signal(12);
  readonly arriba = signal(12);
  readonly etiqueta = etiquetaVelocidad;
  private readonly elemento = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly boton = viewChild<ElementRef<HTMLButtonElement>>('boton');
  private readonly panel = viewChild<ElementRef<HTMLElement>>('panel');
  private readonly barra = viewChild<ElementRef<HTMLInputElement>>('barra');
  private apertura = 0;
  alternar(): void {
    if (this.abierta()) { this.cerrar(); return; }
    this.abierta.set(true);
    this.apertura = requestAnimationFrame(() => {
      if (!this.abierta()) return;
      const panel = this.panel()?.nativeElement, boton = this.boton()?.nativeElement;
      if (!panel || !boton) return;
      if (typeof panel.showPopover === 'function') panel.showPopover();
      else panel.removeAttribute('popover');
      const caja = panel.getBoundingClientRect(), origen = boton.getBoundingClientRect();
      const ancho = document.documentElement.clientWidth || innerWidth;
      this.izquierda.set(Math.max(12, Math.min(ancho - 12 - caja.width, origen.left + origen.width / 2 - caja.width / 2)));
      const arriba = origen.top - caja.height - 10;
      this.arriba.set(arriba >= 12 ? arriba : Math.min(innerHeight - caja.height - 12, origen.bottom + 10));
      this.barra()?.nativeElement.focus({ preventScroll: true });
    });
  }
  cambiar(valor: number): void { this.valor.set(velocidadValida(valor)); }
  cerrar(enfocar = true): void {
    cancelAnimationFrame(this.apertura);
    const panel = this.panel()?.nativeElement;
    if (panel?.isConnected && typeof panel.hidePopover === 'function') panel.hidePopover();
    this.abierta.set(false);
    if (enfocar) this.boton()?.nativeElement.focus({ preventScroll: true });
  }
  @HostListener('document:pointerdown', ['$event']) fuera(ev: PointerEvent): void {
    if (this.abierta() && !this.elemento.nativeElement.contains(ev.target as Node)) this.cerrar(false);
  }
  @HostListener('keydown.escape', ['$event']) escape(ev: Event): void { if (this.abierta()) { ev.stopPropagation(); this.cerrar(); } }
  @HostListener('window:resize') redimensionar(): void { this.cerrar(false); }
  ngOnDestroy(): void { this.cerrar(false); }
}
