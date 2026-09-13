import { ChangeDetectionStrategy, Component, effect, inject, signal, untracked } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { Icono } from '../compartido/icono';
import { Sesion } from '../nucleo/sesion';

/** «Leer» en la navegación: al libro que tienes a medias, o a elegir uno. */
@Component({
  selector: 'app-leer-entrada',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Icono],
  template: `
    <div class="pagina estrecha">
      @if (buscando()) {
        <div class="espera"><span class="giro"></span> Buscando dónde lo dejaste…</div>
      } @else {
        <div class="vacio tarjeta">
          <span class="icono-grande"><app-icono nombre="libro" /></span>
          <h1>Todavía no estás leyendo nada</h1>
          <p class="suave">Abre un libro y aquí te esperará, en el capítulo donde lo dejes.</p>
          <div class="fila centrada">
            <a class="boton" [routerLink]="['/leer', 'PG11', 'auto']">Abrir Alicia en el país de las maravillas</a>
            <a class="boton secundario" routerLink="/encontrar">Elegir otro libro</a>
          </div>
        </div>
      }
    </div>
  `,
  styles: `
    .vacio { text-align: center; padding: clamp(2rem, 6vw, 4rem) 1.5rem; }
    .icono-grande { display: inline-grid; place-items: center; width: 72px; height: 72px; border-radius: 22px;
      background: var(--acento-suave); color: var(--acento-texto); font-size: 2rem; margin-bottom: 1rem; }
    .centrada { justify-content: center; margin-top: 1.5rem; }
  `,
})
export class LeerEntrada {
  private readonly sesion = inject(Sesion);
  private readonly router = inject(Router);
  protected readonly buscando = signal(true);

  constructor() {
    effect(() => {
      const motor = this.sesion.motor();
      if (motor === 'caido') { this.buscando.set(false); return; }
      if (motor !== 'listo') return;
      untracked(() => void this.ir());
    });
  }

  private async ir(): Promise<void> {
    await this.sesion.refrescar();
    const s = this.sesion.inicio()?.seguir;
    if (s) {
      void this.router.navigate(['/leer', s.id, s.capitulo], { replaceUrl: true });
    } else {
      this.buscando.set(false);
    }
  }
}
