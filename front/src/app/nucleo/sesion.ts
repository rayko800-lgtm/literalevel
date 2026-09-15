import { Injectable, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Api, Entrada, Inicio, Libro, Perfil } from './api';

export type EstadoMotor = 'comprobando' | 'listo' | 'despertando' | 'caido';

/** Lo que comparten todas las pantallas: si el motor responde, el perfil, la
 *  entrada con usuario y lo que se abre en la portada. */
@Injectable({ providedIn: 'root' })
export class Sesion {
  private readonly api = inject(Api);

  readonly motor = signal<EstadoMotor>('comprobando');
  readonly inicio = signal<Inicio | null>(null);
  readonly perfil = signal<Perfil | null>(null);
  readonly entrada = signal<Entrada | null>(null);
  readonly ajustesAbiertos = signal(false);
  /** Abrir los ajustes ya en «Tu perfil», con el cursor en «Usuario»: los «Entrar» de las
   *  pantallas abrían el panel por arriba y el formulario quedaba fuera (Ismael, 15 sep). */
  readonly ajustesEnPerfil = signal(false);

  abrirPerfil(): void {
    this.ajustesEnPerfil.set(true);
    this.ajustesAbiertos.set(true);
  }

  private intentos = 0;
  private readonly libros = new Map<string, Promise<Libro>>();

  constructor() {
    void this.comprobar();
  }

  /** El Space se duerme por inactividad y tarda ~30 s en volver. Mientras
   *  tanto se dice, en vez de dejar botones que no responden. */
  async comprobar(): Promise<void> {
    try {
      await firstValueFrom(this.api.salud());
      this.motor.set('listo');
      this.intentos = 0;
      await this.refrescar();
    } catch (e) {
      const sinRed = e instanceof HttpErrorResponse && [0, 502, 503, 504].includes(e.status);
      this.intentos++;
      if (this.intentos <= 45 && (sinRed || !(e instanceof HttpErrorResponse))) {
        this.motor.set('despertando');
        setTimeout(() => void this.comprobar(), 4000);
      } else {
        this.motor.set('caido');
      }
    }
  }

  async refrescar(): Promise<void> {
    try {
      const i = await firstValueFrom(this.api.inicio());
      this.inicio.set(i);
      this.perfil.set(i.perfil);
      this.entrada.set(i.entrada);
    } catch {
      /* la portada funciona sin esto */
    }
  }

  fijarPerfil(p: Perfil | null): void {
    this.perfil.set(p);
    const i = this.inicio();
    if (i) this.inicio.set({ ...i, perfil: p });
    // El encaje de cada libro depende del perfil: fuera lo cacheado.
    this.libros.clear();
  }

  /** El índice y la ficha de un libro se piden una vez por visita. */
  libro(id: string, forzar = false): Promise<Libro> {
    if (forzar || !this.libros.has(id)) {
      const p = firstValueFrom(this.api.libro(id));
      p.catch(() => this.libros.delete(id));
      this.libros.set(id, p);
    }
    return this.libros.get(id)!;
  }
}
