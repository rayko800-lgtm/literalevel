import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LibroTarjeta } from '../nucleo/api';
import { Portada } from './portada';
import { cefr, encaje, miles, num } from '../nucleo/formato';

@Component({
  selector: 'app-tarjeta-libro',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Portada],
  template: `
    <a class="tarjeta-libro" [routerLink]="['/libro', libro().id]" [class.sin-texto]="!libro().abrible">
      <app-portada class="portada" [id]="libro().id" [titulo]="libro().titulo" [autor]="libro().autor"
                   [cefr]="letra()" [temas]="libro().temas" [ia]="libro().portada_ia" [compacta]="true" />
      <div class="cuerpo">
        <h3>{{ libro().titulo }}</h3>
        <p class="autor">{{ libro().autor || 'Autor desconocido' }}</p>
        @if (libro().gancho) {
          <p class="gancho">{{ libro().gancho }}</p>
        }
        <div class="pie">
          @if (libro().dificultad !== null) {
            <span class="chip">{{ letra() }} · {{ num(libro().dificultad) }}</span>
            <!-- En bloque (f4, 8ee42f0): el número es el del grupo de cuentos de su fuente y nivel. -->
            @if (libro().medido_en_bloque) {
              <span class="tenue pequeno en-bloque">medido en bloque con otros cuentos</span>
            }
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
      display: grid; grid-template-columns: 96px 1fr; gap: 1rem; height: 100%; align-items: start;
      padding: 1rem; border-radius: var(--radio); background: var(--superficie);
      border: 1px solid var(--borde); color: inherit; text-decoration: none;
      box-shadow: var(--sombra); transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
    }
    .tarjeta-libro:hover { transform: translateY(-2px); box-shadow: var(--sombra-alta); border-color: var(--borde-fuerte); }
    .tarjeta-libro.sin-texto { opacity: .78; }
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
  protected readonly encaje = computed(() => encaje(this.libro().dificultad, this.nivelLector()));
  protected readonly num = num;
  protected readonly miles = miles;
}
