import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Icono } from '../compartido/icono';
import { Api, Cuaderno, Repaso, mensajeError } from '../nucleo/api';
import { miles } from '../nucleo/formato';

/** Mis palabras: lo que consultaste leyendo, con su frase. Sin nota y sin
 *  racha: el repaso es un recordatorio, no un examen (enganche.md §5). */
@Component({
  selector: 'app-palabras',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Icono],
  template: `
    <div class="pagina">
      <header class="cabecera-pagina">
        <span class="antetitulo">Tu nivel · Mis palabras</span>
        <h1>Mis palabras</h1>
        <p>Cada palabra que consultas mientras lees se guarda aquí con la frase donde la encontraste.</p>
      </header>

      @if (error()) { <div class="aviso error"><p>{{ error() }}</p></div> }

      @if (cuaderno(); as c) {
        @if (c.consultas === 0) {
          <div class="vacio tarjeta">
            <app-icono nombre="palabras" class="grande" />
            <h2>Todavía no has consultado ninguna palabra</h2>
            <p class="suave">Abre un libro y selecciona una palabra que no conozcas (en el móvil, mantenla pulsada).</p>
            <a class="boton" routerLink="/leer">Ir a leer</a>
          </div>
        } @else {
          <section class="cifras">
            <div><strong>{{ miles(c.palabras) }}</strong><span>palabras distintas</span></div>
            <div><strong>{{ miles(c.consultas) }}</strong><span>consultas</span></div>
            <div><strong>{{ miles(c.libros) }}</strong><span>{{ c.libros === 1 ? 'libro' : 'libros' }}</span></div>
          </section>

          @if (repaso(); as r) {
            @if (r.palabras.length) {
              <section class="repaso">
                <h2>Repasa cinco</h2>
                <p class="suave">Las más raras de las últimas que miraste. ¿Recuerdas qué significaban en su frase?</p>
                <div class="rejilla-auto">
                  @for (a of r.palabras; track a.lema) {
                    <button type="button" class="tarjeta carta" [class.vuelta]="vistas().has(a.lema)" (click)="voltear(a.lema)"
                            [attr.aria-expanded]="vistas().has(a.lema)">
                      <strong lang="en">{{ a.palabra }}</strong>
                      <span class="frase en-libro" lang="en">{{ a.oracion }}</span>
                      @if (vistas().has(a.lema)) {
                        <span class="sentido" lang="en">{{ a.sentido || 'Sin acepción guardada' }}</span>
                      } @else {
                        <span class="tenue pequeno"><app-icono nombre="ojo" /> Toca para ver el sentido</span>
                      }
                    </button>
                  }
                </div>
              </section>
            }
          }

          <section>
            <h2>Últimas consultas</h2>
            <ul class="lista">
              @for (a of c.entradas; track $index) {
                <li class="tarjeta plana">
                  <div class="cab"><strong lang="en">{{ a.palabra }}</strong>
                    @if (a.rareza) { <span class="chip">{{ a.rareza }}</span> }
                    @if (a.libro) { <span class="tenue pequeno">{{ a.libro }}@if (a.capitulo) {, cap. {{ a.capitulo }}}</span> }
                  </div>
                  <blockquote class="en-libro" lang="en">{{ a.oracion }}</blockquote>
                  @if (a.sentido) { <p class="suave pequeno" lang="en">{{ a.sentido }}</p> }
                </li>
              }
            </ul>
          </section>
        }
      } @else if (!error()) {
        <div class="espera"><span class="giro"></span>Abriendo tu cuaderno…</div>
      }
    </div>
  `,
  styles: `
    .vacio { text-align: center; padding: 2.5rem 1.5rem; }
    .grande { font-size: 2.5rem; color: var(--acento-texto); margin-bottom: .5rem; }
    .cifras { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; }
    .cifras div { display: grid; padding: 1rem 1.2rem; border-radius: var(--radio); background: var(--superficie-2); }
    .cifras strong { font-size: 2rem; line-height: 1.1; }
    .cifras span { color: var(--texto-suave); font-size: .9rem; }
    .repaso { margin-bottom: 2rem; }
    .carta { display: grid; gap: .5rem; text-align: left; font: inherit; color: inherit; cursor: pointer; align-content: start; min-height: 150px; }
    .carta strong { font-size: 1.3rem; }
    .carta.vuelta { border-color: var(--verde); background: color-mix(in srgb, var(--verde-suave) 50%, var(--superficie)); }
    .frase { color: var(--lector-texto); line-height: 1.5; }
    .sentido { color: var(--verde); font-weight: 600; }
    .lista { list-style: none; padding: 0; margin: 0; display: grid; gap: .6rem; }
    .cab { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
    .cab strong { font-size: 1.15rem; }
    blockquote { margin: .5rem 0; padding-left: .8rem; border-left: 3px solid var(--acento); color: var(--lector-texto); line-height: 1.55; }
    li p { margin: 0; }
    @media (max-width: 520px) { .cifras { grid-template-columns: 1fr 1fr; } .cifras div:last-child { grid-column: span 2; } }
  `,
})
export class Palabras implements OnInit {
  private readonly api = inject(Api);
  protected readonly cuaderno = signal<Cuaderno | null>(null);
  protected readonly repaso = signal<Repaso | null>(null);
  protected readonly error = signal('');
  protected readonly vistas = signal(new Set<string>());
  protected readonly miles = miles;

  async ngOnInit(): Promise<void> {
    try {
      const [c, r] = await Promise.all([firstValueFrom(this.api.cuaderno()), firstValueFrom(this.api.repaso())]);
      this.cuaderno.set(c);
      this.repaso.set(r);
    } catch (e) {
      this.error.set(mensajeError(e));
    }
  }

  protected voltear(lema: string): void {
    const s = new Set(this.vistas());
    if (s.has(lema)) s.delete(lema); else s.add(lema);
    this.vistas.set(s);
  }
}
