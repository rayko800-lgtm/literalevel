import { ChangeDetectionStrategy, Component, ElementRef, HostListener, afterNextRender, inject, output, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Api, mensajeError } from '../nucleo/api';
import { Idioma, ModoLectura, Preferencias, TamanoLetra, Tema } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';
import { Tutorial } from '../nucleo/tutorial';
import { Icono } from './icono';

/** Los ajustes, en un panel lateral y no en la navegación: Laura y el profesor
 *  dijeron lo mismo sin saberlo, «los colores son configuración, no una función». */
@Component({
  selector: 'app-ajustes',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RouterLink, Icono],
  template: `
    <div class="velo" (click)="cerrar.emit()"></div>
    <aside class="panel" role="dialog" aria-modal="true" aria-labelledby="titulo-ajustes">
      <header>
        <h2 id="titulo-ajustes">Ajustes</h2>
        <button class="boton-icono" type="button" (click)="cerrar.emit()" aria-label="Cerrar ajustes">
          <app-icono nombre="cerrar" />
        </button>
      </header>

      <section>
        <h3>Colores</h3>
        <div class="opciones temas">
          @for (t of temas; track t.valor) {
            <button type="button" class="opcion tema" [class.elegida]="prefs.tema() === t.valor"
                    [attr.aria-pressed]="prefs.tema() === t.valor" (click)="prefs.tema.set(t.valor)">
              <span class="muestra" [attr.data-muestra]="t.valor"></span>{{ t.nombre }}
            </button>
          }
        </div>
      </section>

      <section>
        <h3>Color del libro en el lector</h3>
        <!-- El fondo y el acento de la portada, suaves y con el texto a 7:1 o más. -->
        <div class="opciones">
          <button type="button" class="opcion" [class.elegida]="prefs.colorDelLibro() === 'si'"
                  [attr.aria-pressed]="prefs.colorDelLibro() === 'si'" (click)="prefs.colorDelLibro.set('si')">Con su color</button>
          <button type="button" class="opcion" [class.elegida]="prefs.colorDelLibro() === 'no'"
                  [attr.aria-pressed]="prefs.colorDelLibro() === 'no'" (click)="prefs.colorDelLibro.set('no')">Sin color</button>
        </div>
      </section>

      <section>
        <h3>Tamaño de la letra del libro</h3>
        <div class="opciones">
          @for (l of letras; track l.valor) {
            <button type="button" class="opcion" [class.elegida]="prefs.letra() === l.valor"
                    [attr.aria-pressed]="prefs.letra() === l.valor" (click)="prefs.letra.set(l.valor)">
              <span class="en-libro" [style.font-size.px]="l.px">Aa</span>
            </button>
          }
        </div>
      </section>

      <section>
        <h3>Cómo leer</h3>
        <div class="opciones">
          @for (m of modos; track m.valor) {
            <button type="button" class="opcion" [class.elegida]="prefs.modoLectura() === m.valor"
                    [attr.aria-pressed]="prefs.modoLectura() === m.valor" (click)="prefs.modoLectura.set(m.valor)">
              <app-icono [nombre]="m.icono" />{{ m.nombre }}
            </button>
          }
        </div>
      </section>

      <section>
        <h3>Explicaciones de las palabras</h3>
        <div class="opciones">
          @for (i of idiomas; track i.valor) {
            <button type="button" class="opcion" [class.elegida]="prefs.idioma() === i.valor"
                    [attr.aria-pressed]="prefs.idioma() === i.valor" (click)="prefs.idioma.set(i.valor)">{{ i.nombre }}</button>
          }
        </div>
      </section>

      <section #seccionPerfil class="perfil">
        <h3>Tu perfil</h3>
        @if (sesion.entrada(); as e) {
          @if (!e.puerta) {
            <p class="suave">Esta copia no tiene perfiles: todo está disponible sin entrar.</p>
          } @else if (e.dentro) {
            <p>Has entrado como <strong>{{ e.nombre }}</strong>.
              @if (e.restantes !== null) {
                {{ e.restantes === 1 ? 'Te queda' : 'Te quedan' }} <strong>{{ e.restantes }}</strong>
                {{ e.restantes === 1 ? 'uso' : 'usos' }}.
              } @else { Sin límite de usos. }
            </p>
            <button class="boton secundario" type="button" (click)="salir()">Salir</button>
          } @else {
            <p class="suave pequeno">Leer, buscar, medir y el diccionario son libres. La explicación en contexto,
              «¿de qué trata?» y la corrección de pronunciación usan OpenAI y necesitan entrar.</p>
            <form class="pila entrar" (ngSubmit)="entrar()">
              <label class="campo"><span>Usuario</span>
                <input #campoUsuario class="entrada" name="usuario" autocomplete="username" autocapitalize="none" [(ngModel)]="usuario" required>
              </label>
              <label class="campo"><span>Contraseña</span>
                <input class="entrada" name="clave" type="password" autocomplete="current-password" [(ngModel)]="clave" required>
              </label>
              @if (mensaje()) { <p class="aviso" [class.error]="!sesion.entrada()?.dentro" role="status">{{ mensaje() }}</p> }
              <button class="boton" type="submit" [disabled]="entrando()">{{ entrando() ? 'Comprobando…' : 'Entrar' }}</button>
            </form>
          }
        } @else {
          <p class="suave">Conectando con el motor…</p>
        }
      </section>

      <footer>
        <!-- En el móvil, el cierre va abajo, fijo (investigacion/una_mano.md §3.8). -->
        <button class="boton secundario cerrar-abajo" type="button" (click)="cerrar.emit()">Cerrar los ajustes</button>
        <a routerLink="/" (click)="verBienvenida()">Ver la bienvenida otra vez</a>
        @if (tutorial.habilitado()) {
          <!-- Solo visible con el tutorial v2 activado en desarrollo (D1.1): nunca para un usuario normal. -->
          <a routerLink="/" (click)="repetirTutorial()">Repetir tutorial (v2, desarrollo)</a>
        }
        <a routerLink="/estado" (click)="cerrar.emit()">Estado del sistema</a>
        <span class="tenue pequeno">Pléyade no certifica niveles del MCER: orienta para elegir qué leer.</span>
      </footer>
    </aside>
  `,
  styles: `
    :host { position: fixed; inset: 0; z-index: 80; }
    .velo { position: absolute; inset: 0; background: var(--velo); animation: aparecer .2s ease; }
    .panel {
      position: absolute; top: 0; right: 0; bottom: 0; width: min(400px, 100%);
      background: var(--superficie); border-left: 1px solid var(--borde); box-shadow: var(--sombra-alta);
      padding: 1rem 1.25rem calc(1.5rem + env(safe-area-inset-bottom)); overflow-y: auto; overscroll-behavior: contain;
      animation: entrar .25s cubic-bezier(.2,.8,.2,1);
    }
    header { display: flex; align-items: center; justify-content: space-between; margin-bottom: .5rem; }
    h2 { margin: 0; font-size: 1.35rem; }
    section { padding: 1rem 0; border-top: 1px solid var(--borde); }
    h3 { font-size: .95rem; color: var(--texto-suave); margin-bottom: .7rem; }
    .opciones { display: grid; grid-template-columns: repeat(auto-fit, minmax(72px, 1fr)); gap: .5rem; }
    .temas { grid-template-columns: repeat(2, 1fr); }
    .opcion {
      min-height: 52px; border-radius: 12px; border: 1.5px solid var(--borde); background: var(--superficie-2);
      color: var(--texto); font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: .5rem;
    }
    .opcion.elegida { border-color: var(--acento); background: var(--acento-suave); color: var(--acento-texto); }
    .muestra { width: 22px; height: 22px; border-radius: 50%; border: 1px solid rgba(0,0,0,.15); }
    .muestra[data-muestra="sistema"] { background: linear-gradient(135deg, #f4f6fb 50%, #0f1422 50%); }
    .muestra[data-muestra="claro"] { background: #f4f6fb; }
    .muestra[data-muestra="noche"] { background: #182033; }
    .muestra[data-muestra="papel"] { background: #efe7d6; }
    .entrar { margin-top: .75rem; }
    footer { display: grid; gap: .4rem; padding-top: 1rem; border-top: 1px solid var(--borde); }
    .cerrar-abajo { display: none; }
    /* En el móvil, hoja inferior en vez de cajón lateral: la X de arriba queda en la
       zona que no alcanza el pulgar; el cierre de verdad va en el pie, fijo. */
    @media (max-width: 760px) {
      .panel {
        top: auto; left: 0; width: 100%; max-height: 80dvh; border-left: 0; border-top: 1px solid var(--borde);
        border-radius: 22px 22px 0 0; padding-bottom: 0; animation: subir .24s cubic-bezier(.2,.8,.2,1);
      }
      footer {
        position: sticky; bottom: 0; margin: 0 -1.25rem; padding: .75rem 1.25rem max(8px, env(safe-area-inset-bottom));
        background: var(--superficie);
      }
      .cerrar-abajo { display: flex; min-height: 48px; }
    }
    @keyframes aparecer { from { opacity: 0; } }
    @keyframes entrar { from { transform: translateX(24px); opacity: 0; } }
    @keyframes subir { from { transform: translateY(40px); opacity: 0; } }
  `,
})
export class Ajustes {
  protected readonly prefs = inject(Preferencias);
  protected readonly sesion = inject(Sesion);
  protected readonly tutorial = inject(Tutorial);
  private readonly api = inject(Api);
  readonly cerrar = output<void>();
  private readonly seccionPerfil = viewChild<ElementRef<HTMLElement>>('seccionPerfil');
  private readonly campoUsuario = viewChild<ElementRef<HTMLInputElement>>('campoUsuario');

  constructor() {
    // Desde un «Entrar»: el panel se abre ya en «Tu perfil» y con el cursor en «Usuario».
    // Antes abría por arriba y el formulario quedaba fuera de la pantalla (Ismael, 15 sep).
    afterNextRender(() => {
      if (!this.sesion.ajustesEnPerfil()) return;
      this.sesion.ajustesEnPerfil.set(false);
      this.seccionPerfil()?.nativeElement.scrollIntoView?.({ block: 'start' });
      this.campoUsuario()?.nativeElement.focus({ preventScroll: true });
    });
  }

  protected usuario = '';
  protected clave = '';
  protected readonly entrando = signal(false);
  protected readonly mensaje = signal('');

  protected readonly temas: { valor: Tema; nombre: string }[] = [
    { valor: 'sistema', nombre: 'Automático' }, { valor: 'claro', nombre: 'Claro' },
    { valor: 'noche', nombre: 'Noche' }, { valor: 'papel', nombre: 'Papel' },
  ];
  protected readonly letras: { valor: TamanoLetra; px: number }[] = [
    { valor: 'pequena', px: 15 }, { valor: 'normal', px: 18 }, { valor: 'grande', px: 22 }, { valor: 'enorme', px: 26 },
  ];
  protected readonly modos: { valor: ModoLectura; nombre: string; icono: string }[] = [
    { valor: 'paginas', nombre: 'Por páginas', icono: 'paginas' }, { valor: 'rollo', nombre: 'Seguido', icono: 'rollo' },
  ];
  protected readonly idiomas: { valor: Idioma; nombre: string }[] = [
    { valor: 'es', nombre: 'En español' }, { valor: 'en', nombre: 'In English' },
  ];

  @HostListener('document:keydown.escape')
  protected alEscape(): void { this.cerrar.emit(); }

  protected async entrar(): Promise<void> {
    this.entrando.set(true);
    this.mensaje.set('');
    try {
      const e = await firstValueFrom(this.api.entrar(this.usuario, this.clave));
      this.sesion.entrada.set(e);
      this.mensaje.set(e.mensaje);
      if (e.dentro) {
        this.clave = '';
        await this.sesion.cambioDeCuenta();
      }
    } catch (err) {
      this.mensaje.set(mensajeError(err));
    } finally {
      this.entrando.set(false);
    }
  }

  protected verBienvenida(): void {
    this.sesion.verBienvenidaOtraVez();
    this.cerrar.emit();
  }

  protected repetirTutorial(): void {
    this.tutorial.repetir();
    this.cerrar.emit();
  }

  protected async salir(): Promise<void> {
    try {
      this.sesion.entrada.set(await firstValueFrom(this.api.salir()));
      this.mensaje.set('');
      await this.sesion.cambioDeCuenta();
    } catch (err) {
      this.mensaje.set(mensajeError(err));
    }
  }
}
