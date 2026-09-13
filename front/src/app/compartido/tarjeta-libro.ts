import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LibroTarjeta } from '../nucleo/api';
import { cefr, encaje, miles, num } from '../nucleo/formato';

@Component({
  selector: 'app-tarjeta-libro',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <a class="tarjeta-libro" [routerLink]="['/libro', libro().id]" [class.sin-texto]="!libro().abrible">
      <div class="portada" [attr.data-letra]="letra()" aria-hidden="true">
        <span class="inicial">{{ inicial() }}</span>
        <span class="nivel">{{ letra() || '—' }}</span>
      </div>
      <div class="cuerpo">
        <h3>{{ libro().titulo }}</h3>
        <p class="autor">{{ libro().autor || 'Autor desconocido' }}</p>
        @if (libro().gancho) {
          <p class="gancho">{{ libro().gancho }}</p>
        }
        <div class="pie">
          @if (libro().dificultad !== null) {
            <span class="chip">{{ letra() }} · {{ num(libro().dificultad) }}</span>
          }
          @if (encaje(); as e) {
            <span class="chip" [class]="'chip ' + e.clase">{{ e.texto }}</span>
          }
          @if (!libro().abrible) {
            <span class="chip">Sin texto para abrirlo</span>
          }
          @if (libro().descargas > 999) {
            <span class="tenue pequeno">{{ miles(libro().descargas) }} lectores</span>
          }
        </div>
      </div>
    </a>
  `,
  styles: `
    :host { display: block; }
    .tarjeta-libro {
      display: grid; grid-template-columns: 72px 1fr; gap: 1rem; height: 100%;
      padding: 1rem; border-radius: var(--radio); background: var(--superficie);
      border: 1px solid var(--borde); color: inherit; text-decoration: none;
      box-shadow: var(--sombra); transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
    }
    .tarjeta-libro:hover { transform: translateY(-2px); box-shadow: var(--sombra-alta); border-color: var(--borde-fuerte); }
    .tarjeta-libro.sin-texto { opacity: .78; }
    .portada {
      position: relative; aspect-ratio: 3 / 4.2; border-radius: 8px 12px 12px 8px; overflow: hidden;
      display: grid; place-items: center; color: #fff;
      background: linear-gradient(160deg, var(--p1, #4f6df5), var(--p2, #2a3f9e));
      box-shadow: inset 4px 0 0 rgba(0,0,0,.12), 0 6px 14px -8px rgba(0,0,0,.45);
    }
    .portada[data-letra="A1"], .portada[data-letra="A2"] { --p1: #3fb58a; --p2: #1f7a5b; }
    .portada[data-letra="B1"], .portada[data-letra="B2"] { --p1: #5b7cf0; --p2: #2e46b0; }
    .portada[data-letra="C1"] { --p1: #c0782f; --p2: #874b14; }
    .portada[data-letra="C2"] { --p1: #b0496b; --p2: #6e2440; }
    .inicial { font-family: var(--fuente-libro); font-size: 2rem; line-height: 1; font-weight: 600; opacity: .95; }
    .nivel {
      position: absolute; bottom: 5px; right: 5px; font-size: .68rem; font-weight: 800; letter-spacing: .04em;
      background: rgba(0,0,0,.28); padding: 1px 6px; border-radius: 999px;
    }
    .cuerpo { min-width: 0; display: flex; flex-direction: column; }
    h3 { margin: 0 0 .15rem; font-size: 1.04rem; line-height: 1.25; overflow-wrap: anywhere; }
    .autor { margin: 0 0 .45rem; color: var(--texto-suave); font-size: .9rem; }
    .gancho {
      margin: 0 0 .7rem; color: var(--texto-suave); font-size: .9rem; line-height: 1.45;
      display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
    }
    .pie { margin-top: auto; display: flex; flex-wrap: wrap; gap: .4rem; align-items: center; }
  `,
})
export class TarjetaLibro {
  readonly libro = input.required<LibroTarjeta>();
  readonly nivelLector = input<number | null>(null);

  protected readonly letra = computed(() => cefr(this.libro().dificultad) || this.libro().nivel);
  protected readonly inicial = computed(() => (this.libro().titulo.trim()[0] ?? '·').toUpperCase());
  protected readonly encaje = computed(() => encaje(this.libro().dificultad, this.nivelLector()));
  protected readonly num = num;
  protected readonly miles = miles;
}
