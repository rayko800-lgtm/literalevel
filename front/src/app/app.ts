import { ChangeDetectionStrategy, Component, HostListener, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { Ajustes } from './compartido/ajustes';
import { Icono } from './compartido/icono';
import { Spotlight } from './compartido/spotlight';
import { Preferencias } from './nucleo/preferencias';
import { Sesion } from './nucleo/sesion';
import { Tutorial } from './nucleo/tutorial';

@Component({
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Icono, Ajustes, Spotlight],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly sesion = inject(Sesion);
  // Se inyecta aquí para que aplique el tema y la letra desde el arranque.
  private readonly prefs = inject(Preferencias);
  private readonly router = inject(Router);
  // Tutorial v2 (D1.1), detrás de un flag de desarrollo: se inyecta aquí para
  // que `<app-spotlight>` funcione en cualquier ruta, no solo en Inicio.
  private readonly tutorial = inject(Tutorial);

  protected readonly navegacion = [
    { ruta: '/leer', etiqueta: 'Leer', icono: 'libro', seccion: 'leer' },
    { ruta: '/encontrar', etiqueta: 'Encontrar', icono: 'lupa', seccion: 'encontrar' },
    { ruta: '/pronunciar', etiqueta: 'Pronunciar', icono: 'micro', seccion: 'voz' },
    { ruta: '/nivel', etiqueta: 'Tu nivel', icono: 'nivel', seccion: 'nivel' },
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
    // Solo para nosotros, en desarrollo: `?tutorialv2=on` activa el tutorial
    // v2 sin tocar nada visible para quien no pase ese parámetro.
    if (typeof location !== 'undefined' && new URLSearchParams(location.search).get('tutorialv2') === 'on') {
      this.tutorial.activarDesarrollo();
    }
  }

  @HostListener('window:scroll')
  protected alDesplazar(): void {
    const y = window.scrollY;
    if (Math.abs(y - this.ultimoY) < 10) return;
    this.barraOculta.set(y > this.ultimoY && y > 160);
    this.ultimoY = y;
  }
}
