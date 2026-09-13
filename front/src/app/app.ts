import { ChangeDetectionStrategy, Component, HostListener, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { Ajustes } from './compartido/ajustes';
import { Icono } from './compartido/icono';
import { Preferencias } from './nucleo/preferencias';
import { Sesion } from './nucleo/sesion';

@Component({
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Icono, Ajustes],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly sesion = inject(Sesion);
  // Se inyecta aquí para que aplique el tema y la letra desde el arranque.
  private readonly prefs = inject(Preferencias);
  private readonly router = inject(Router);

  protected readonly navegacion = [
    { ruta: '/leer', etiqueta: 'Leer', icono: 'libro' },
    { ruta: '/encontrar', etiqueta: 'Encontrar', icono: 'lupa' },
    { ruta: '/pronunciar', etiqueta: 'Pronunciar', icono: 'micro' },
    { ruta: '/nivel', etiqueta: 'Tu nivel', icono: 'nivel' },
  ];

  /** La barra de abajo se esconde al bajar leyendo y vuelve al subir. */
  protected readonly barraOculta = signal(false);
  private ultimoY = 0;

  constructor() {
    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd), takeUntilDestroyed())
      .subscribe(() => {
        this.barraOculta.set(false);
        this.ultimoY = 0;
      });
  }

  @HostListener('window:scroll')
  protected alDesplazar(): void {
    const y = window.scrollY;
    if (Math.abs(y - this.ultimoY) < 10) return;
    this.barraOculta.set(y > this.ultimoY && y > 160);
    this.ultimoY = y;
  }
}
