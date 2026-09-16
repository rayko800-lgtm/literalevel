import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, HostListener, afterNextRender, computed, inject, signal, viewChild } from '@angular/core';
import { Router } from '@angular/router';
import { Sesion } from '../nucleo/sesion';
import { Icono } from './icono';

/** `puerta`: el paso 0 sin cuenta, con «Entrar» y «Seguir sin cuenta» en vez de «Siguiente». */
interface Paso { titulo: string; texto: string; puerta?: boolean; }

/** La bienvenida de la primera visita a Inicio (tanda 3 de la ayuda; Miguel, sobre el informe
 *  de Ismael). Cuatro pasos: el 0 pregunta por la cuenta (o, con cuenta, dice qué gasta usos) y
 *  los otros tres, sin el de pronunciar, que tiene su propia línea de ayuda. Solo la pinta
 *  Inicio, así que nunca sale encima de un enlace directo a un libro o al lector. «Saltar» en
 *  cada paso; se guarda en el navegador y se vuelve a ver desde Ajustes. */
@Component({
  selector: 'app-bienvenida',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icono],
  template: `
    <div class="velo"></div>
    <section class="tarjeta-bienvenida" role="dialog" aria-modal="true" aria-labelledby="titulo-bienvenida">
      <header>
        <span class="marca-b" aria-hidden="true">L</span>
        <span class="cuenta">{{ paso() + 1 }} de {{ pasos().length }}</span>
        <button type="button" class="boton pequeno fantasma saltar" (click)="cerrar()">Saltar</button>
      </header>
      <h2 id="titulo-bienvenida" #titulo tabindex="-1">{{ actual().titulo }}</h2>
      <p>{{ actual().texto }}</p>
      <div class="puntos" aria-hidden="true">
        @for (p of pasos(); track $index) { <i [class.activo]="$index === paso()"></i> }
      </div>
      <div class="acciones-b">
        @if (actual().puerta) {
          <!-- Los dos del mismo tamaño: entrar no es la única salida (4e, informe d11057a). -->
          <button type="button" class="boton bloque" (click)="entrar()">Entrar</button>
          <button type="button" class="boton secundario bloque" (click)="siguiente()">Seguir sin cuenta</button>
        } @else if (paso() < pasos().length - 1) {
          <button type="button" class="boton bloque" (click)="siguiente()">Siguiente<app-icono nombre="der" /></button>
        } @else {
          <button type="button" class="boton bloque" (click)="ir(['/nivel'])">Medir mi nivel</button>
          <button type="button" class="boton secundario bloque" (click)="ir(['/leer', 'PG11', 'auto'])">Solo quiero leer</button>
        }
      </div>
    </section>
  `,
  styles: `
    :host { position: fixed; inset: 0; z-index: 90; display: grid; place-items: center; padding: 1rem; }
    .velo { position: absolute; inset: 0; background: var(--velo); }
    .tarjeta-bienvenida {
      position: relative; width: min(440px, 100%); max-height: calc(100svh - 2rem); overflow: auto;
      display: grid; gap: .9rem; padding: 1.25rem 1.25rem 1.4rem; border-radius: var(--radio-lg);
      background: var(--superficie); border: 1px solid var(--borde); box-shadow: var(--sombra-alta);
    }
    header { display: flex; align-items: center; gap: .6rem; }
    .marca-b { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 10px; font-weight: 800;
      color: #fff; background: linear-gradient(145deg, var(--acento), var(--acento-hondo)); }
    .cuenta { color: var(--texto-tenue); font-size: .9rem; font-variant-numeric: tabular-nums; }
    .saltar { margin-left: auto; }
    h2 { margin: .2rem 0 0; font-size: 1.45rem; line-height: 1.25; }
    h2:focus { outline: none; }
    p { margin: 0; font-size: 1.05rem; line-height: 1.5; color: var(--texto-suave); }
    .puntos { display: flex; gap: .4rem; justify-content: center; }
    .puntos i { width: 8px; height: 8px; border-radius: 50%; background: var(--borde-fuerte); }
    .puntos i.activo { background: var(--acento); width: 22px; border-radius: 999px; }
    .acciones-b { display: grid; gap: .5rem; }
    .acciones-b .boton { justify-content: center; }
  `,
})
export class Bienvenida {
  private readonly sesion = inject(Sesion);
  private readonly router = inject(Router);
  private readonly titulo = viewChild<ElementRef<HTMLElement>>('titulo');
  private readonly tactil = typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches;

  /** Paso 0 (Miguel, 16 sep; diseño de 4e en auditoria/introduccion_al_abrir_4e_2026-09-16.md):
   *  preguntar por la cuenta y decir lo que sí se puede sin ella. */
  private readonly pasoSinCuenta: Paso = {
    titulo: '¿Ya tienes cuenta?', puerta: true,
    texto: 'Con cuenta te corrijo la pronunciación y te explico una palabra en su frase. Sin cuenta puedes leer, buscar, medir tu nivel y grabarte.',
  };
  /** Con cuenta, la primera vez que se entra: lo que gasta usos, que es lo que se malentiende.
   *  Las tres cobran en el motor: /api/voz, la etapa completa de /api/palabra y la sinopsis
   *  (`app/api.py`). Texto de la Central con las correcciones de 4e (16 sep). */
  private readonly pasoConCuenta: Paso = {
    titulo: 'Ya tienes cuenta',
    texto: 'Con tu cuenta te corrijo la pronunciación, te explico una palabra en su frase y te resumo un libro. Cada una de esas cosas gasta un uso.',
  };
  protected readonly pasos = computed(() =>
    [this.sesion.entrada()?.dentro ? this.pasoConCuenta : this.pasoSinCuenta, ...this.basicos]);

  private readonly basicos: Paso[] = [
    { titulo: 'Libros en inglés a tu nivel',
      // Sin «que puedas terminar»: la app no lo sabe (4e, 15 sep).
      texto: 'Medimos qué tan difícil es cada capítulo para que elijas uno a tu medida.' },
    { titulo: 'Una palabra, en su frase',
      // Sin «ahí»: el significado en esa frase es de OpenAI y pide entrar, y el paso 3 dice
      // que nada de esto pide cuenta (4e, 15 sep).
      texto: `Mientras lees, ${this.tactil ? 'mantén presionada' : 'haz doble clic en'} una palabra: te decimos qué significa y cómo se pronuncia.` },
    { titulo: '¿Por dónde empiezas?',
      // Seis pasos: tres preguntas y tres fragmentos (nivel.ts:17). «Seis preguntas»
      // decía lo que la pantalla no hace (4e, 16 sep).
      texto: 'Mide tu nivel con tres preguntas y tres fragmentos, o ve directo a un libro. Nada de esto pide cuenta.' },
  ];
  protected readonly paso = signal(0);
  protected readonly actual = () => this.pasos()[this.paso()];

  private readonly host = inject(ElementRef<HTMLElement>);
  /** Dónde estaba el foco al abrir, para devolverlo al cerrar. */
  private readonly focoAnterior = typeof document !== 'undefined' ? (document.activeElement as HTMLElement | null) : null;

  constructor() {
    afterNextRender(() => this.titulo()?.nativeElement.focus());
    inject(DestroyRef).onDestroy(() => {
      const f = this.focoAnterior;
      if (f && f !== document.body && document.contains(f)) f.focus();
    });
  }

  @HostListener('document:keydown.escape')
  protected cerrar(): void { this.sesion.cerrarBienvenida(); }

  /** Un diálogo de verdad: Tab no sale de la tarjeta a la página tapada por el velo (4e, 15 sep). */
  @HostListener('document:keydown.tab', ['$event'])
  @HostListener('document:keydown.shift.tab', ['$event'])
  protected encerrarFoco(ev: Event): void {
    const botones = [...(this.host.nativeElement as HTMLElement).querySelectorAll<HTMLElement>('.tarjeta-bienvenida button')];
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

  protected siguiente(): void {
    this.paso.update(p => Math.min(p + 1, this.pasos().length - 1));
    queueMicrotask(() => this.titulo()?.nativeElement.focus());
  }

  /** Al mismo sitio que los demás «Entrar»: Ajustes, en «Tu perfil», con el cursor en «Usuario». */
  protected entrar(): void {
    this.sesion.cerrarBienvenida();
    this.sesion.abrirPerfil();
  }

  protected ir(ruta: unknown[]): void {
    this.sesion.cerrarBienvenida();
    void this.router.navigate(ruta);
  }
}
