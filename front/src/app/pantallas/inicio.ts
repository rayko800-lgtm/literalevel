import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Icono } from '../compartido/icono';
import { cefr, miles, num } from '../nucleo/formato';
import { Sesion } from '../nucleo/sesion';

/** La puerta: enseñar el producto antes de pedir nada (PLAN_3_OCTUBRE.md §3.1,
 *  enganche.md §3). Diez segundos para entender qué es esto: por eso el ejemplo
 *  de la derecha es la función estrella, no un párrafo que la explique. */
@Component({
  selector: 'app-inicio',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Icono],
  template: `
    <div class="pagina">
      <section class="heroe">
        <div class="texto-heroe">
          <span class="antetitulo">Lee en inglés a tu medida</span>
          <h1>Libros de verdad en inglés, <span class="realce">sin perderte</span>.</h1>
          <p class="entradilla">LiteraLevel mide lo difícil que es cada capítulo y te explica cualquier palabra
            en su frase, sin salir del libro.</p>
          <div class="fila acciones-heroe">
            @if (seguir(); as s) {
              <a class="boton" [routerLink]="['/leer', s.id, s.capitulo]"><app-icono nombre="libro" />Seguir leyendo</a>
            } @else {
              <a class="boton" [routerLink]="['/leer', 'PG11', 'auto']"><app-icono nombre="libro" />Empezar a leer</a>
            }
            <a class="boton secundario" routerLink="/encontrar"><app-icono nombre="lupa" />Buscar un libro</a>
          </div>
        </div>

        <figure class="demo" aria-label="Ejemplo: tocar una palabra del libro para ver qué significa ahí">
          <div class="demo-libro en-libro">
            <span class="demo-cap">Alice's Adventures in Wonderland · capítulo I</span>
            <p>Alice was beginning to get very tired of sitting by her sister on the
              <mark>bank</mark>, and of having nothing to do: once or twice she had peeped into the book her sister was reading…</p>
          </div>
          <div class="demo-ficha">
            <div class="fila demo-cab"><strong>bank</strong><span class="tenue">/bæŋk/</span><span class="chip verde">aquí</span></div>
            <p><strong>Aquí significa:</strong> la orilla del río, no un banco de dinero.</p>
            <p class="tenue pequeno">«On the bank» = sentada en la orilla, junto a su hermana.</p>
          </div>
        </figure>
      </section>

      @if (seguir(); as s) {
        <a class="tarjeta seguir" [routerLink]="['/leer', s.id, s.capitulo]">
          <div class="seguir-cab">
            <span class="antetitulo">Donde lo dejaste</span>
            <span class="chip">Capítulo {{ s.capitulo + 1 }} de {{ s.capitulos }}</span>
          </div>
          <h2>{{ s.titulo }}</h2>
          <p class="suave">{{ s.autor }}@if (s.titulo_capitulo) { · {{ s.titulo_capitulo }} }</p>
          @if (s.extracto) { <blockquote class="en-libro">{{ s.extracto }}</blockquote> }
          <div class="avance" role="progressbar" [attr.aria-valuenow]="Math.round(s.avance * 100)" aria-valuemin="0" aria-valuemax="100">
            <i [style.width.%]="s.avance * 100"></i>
          </div>
          <span class="fila seguir-pie"><span class="tenue pequeno">{{ Math.round(s.avance * 100) }}% del libro</span>
            <span class="enlace">Seguir leyendo <app-icono nombre="flecha" /></span></span>
        </a>
      }

      <section class="puertas" aria-labelledby="titulo-puertas">
        <h2 id="titulo-puertas" class="oculto-visual">¿Por dónde empiezas?</h2>
        <a class="puerta" [routerLink]="['/leer', 'PG11', 'auto']">
          <span class="icono-puerta verde"><app-icono nombre="ojo" /></span>
          <h3>Solo quiero mirar</h3>
          <p>Abre <em>Alicia en el país de las maravillas</em> y toca cualquier palabra. Sin formulario y sin cuenta.</p>
          <span class="enlace">Abrir un libro <app-icono nombre="flecha" /></span>
        </a>
        <a class="puerta" routerLink="/nivel">
          <span class="icono-puerta acento"><app-icono nombre="diana" /></span>
          <h3>Mídeme</h3>
          @if (perfil(); as p) {
            <p>Tu nivel es <strong>{{ num(p.nivel) }} · {{ cefr(p.nivel) }}</strong>. Vuelve a medirte cuando quieras.</p>
          } @else {
            <p>Seis preguntas cortas, una por pantalla. Desde la primera ya ves una estimación.</p>
          }
          <span class="enlace">{{ perfil() ? 'Ver mi nivel' : 'Empezar' }} <app-icono nombre="flecha" /></span>
        </a>
        <a class="puerta" routerLink="/encontrar">
          <span class="icono-puerta ambar"><app-icono nombre="lupa" /></span>
          <h3>Pregúntame</h3>
          <p>Escribe en español lo que te apetece: «detectives en Londres», «algo de Jane Austen».</p>
          <span class="enlace">Buscar <app-icono nombre="flecha" /></span>
        </a>
      </section>

      @if (inicio(); as i) {
        @if (i.cuaderno.consultas > 0 || i.libros > 0) {
          <section class="resumen">
            @if (i.libros > 0) {
              <a class="dato" routerLink="/encontrar" [queryParams]="{ vista: 'mios' }">
                <strong>{{ miles(i.libros) }}</strong><span>{{ i.libros === 1 ? 'libro empezado' : 'libros empezados' }}</span>
              </a>
            }
            @if (i.cuaderno.consultas > 0) {
              <a class="dato" routerLink="/palabras">
                <strong>{{ miles(i.cuaderno.palabras) }}</strong><span>{{ i.cuaderno.palabras === 1 ? 'palabra consultada' : 'palabras consultadas' }}</span>
              </a>
            }
            @if (perfil(); as p) {
              <a class="dato" routerLink="/nivel">
                <strong>{{ cefr(p.nivel) }}</strong><span>tu nivel, {{ num(p.nivel) }} de 2</span>
              </a>
            }
          </section>
        }
      }

      <section class="como">
        <h2>Cómo funciona</h2>
        <ol class="pasos">
          <li><span class="numero">1</span><div><h3>Sabes cuánto te va a costar</h3>
            <p>Un modelo propio lee el libro entero y dibuja su dificultad capítulo a capítulo, en una escala de 0 a 2.</p></div></li>
          <li><span class="numero">2</span><div><h3>Lees con red</h3>
            <p>Toca una palabra y ves su pronunciación, la acepción que tiene en esa frase y la gramática.</p></div></li>
          <li><span class="numero">3</span><div><h3>Practicas en voz alta</h3>
            <p>Lee una frase del libro al micrófono y te dice qué sonido se te escapa y cómo colocar la boca.</p></div></li>
        </ol>
      </section>
    </div>
  `,
  styles: `
    .heroe { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr); gap: clamp(1.5rem, 4vw, 3.5rem);
      align-items: center; padding: clamp(.5rem, 2vw, 2rem) 0 clamp(1.5rem, 3vw, 3rem); }
    .realce { background: linear-gradient(100deg, var(--acento), var(--verde)); -webkit-background-clip: text; background-clip: text; color: transparent; }
    @media (forced-colors: active) { .realce { color: CanvasText; background: none; } }
    .entradilla { font-size: clamp(1.05rem, 1rem + .35vw, 1.25rem); color: var(--texto-suave); max-width: 46ch; margin-bottom: 1.5rem; }
    .demo { margin: 0; position: relative; padding-bottom: 3.5rem; }
    .demo-libro { background: var(--lector-fondo); border: 1px solid var(--borde); border-radius: var(--radio-lg);
      padding: 1.5rem 1.6rem 3rem; box-shadow: var(--sombra); color: var(--lector-texto); font-size: 1.12rem; line-height: 1.7; }
    .demo-libro p { margin: 0; }
    .demo-cap { display: block; font-family: var(--fuente-ui); font-size: .78rem; color: var(--texto-tenue); margin-bottom: .6rem; }
    mark { background: var(--seleccion); color: inherit; border-radius: 4px; padding: 0 .15em; box-shadow: inset 0 -2px 0 var(--acento); }
    .demo-ficha { position: absolute; right: -.5rem; bottom: 0; width: min(320px, 88%); background: var(--superficie);
      border: 1px solid var(--borde-fuerte); border-radius: var(--radio); padding: .9rem 1rem; box-shadow: var(--sombra-alta); font-size: .95rem; }
    .demo-ficha p { margin: .35rem 0 0; }
    .demo-cab { gap: .5rem; }
    .demo-cab strong { font-size: 1.15rem; }
    .seguir { display: block; margin-bottom: 1.5rem; color: inherit; text-decoration: none; border-color: color-mix(in srgb, var(--acento) 35%, var(--borde));
      background: linear-gradient(135deg, var(--superficie), color-mix(in srgb, var(--acento-suave) 55%, var(--superficie))); }
    .seguir:hover { box-shadow: var(--sombra-alta); }
    .seguir-cab { display: flex; justify-content: space-between; align-items: center; gap: .5rem; flex-wrap: wrap; }
    .seguir h2 { margin: .1rem 0 .1rem; }
    .seguir blockquote { margin: .8rem 0 1rem; padding-left: 1rem; border-left: 3px solid var(--acento); color: var(--lector-texto); font-size: 1.05rem; line-height: 1.6; }
    .seguir-pie { justify-content: space-between; margin-top: .6rem; }
    .enlace { display: inline-flex; align-items: center; gap: .35rem; color: var(--acento-texto); font-weight: 650; }
    .puertas { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .puerta { display: flex; flex-direction: column; gap: .35rem; padding: 1.4rem; border-radius: var(--radio-lg); background: var(--superficie);
      border: 1px solid var(--borde); color: inherit; text-decoration: none; box-shadow: var(--sombra);
      transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease; }
    .puerta:hover { transform: translateY(-3px); box-shadow: var(--sombra-alta); border-color: var(--borde-fuerte); }
    .puerta h3 { font-size: 1.25rem; margin: .5rem 0 0; }
    .puerta p { color: var(--texto-suave); margin: 0 0 .6rem; }
    .puerta .enlace { margin-top: auto; }
    .icono-puerta { display: grid; place-items: center; width: 48px; height: 48px; border-radius: 14px; font-size: 1.3rem; }
    .icono-puerta.verde { background: var(--verde-suave); color: var(--verde); }
    .icono-puerta.acento { background: var(--acento-suave); color: var(--acento-texto); }
    .icono-puerta.ambar { background: var(--ambar-suave); color: var(--ambar); }
    .resumen { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(150px, 30%), 1fr)); gap: .75rem; margin-bottom: 2.5rem; }
    .dato { display: grid; gap: .1rem; padding: 1rem 1.2rem; border-radius: var(--radio); background: var(--superficie-2);
      color: inherit; text-decoration: none; border: 1px solid transparent; }
    .dato:hover { border-color: var(--borde-fuerte); }
    .dato strong { font-size: 1.8rem; line-height: 1.1; }
    .dato span { color: var(--texto-suave); font-size: .92rem; }
    .como { padding-top: 1rem; }
    .pasos { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.25rem; }
    .pasos li { display: flex; gap: .9rem; }
    .pasos h3 { margin: .2rem 0 .3rem; }
    .pasos p { color: var(--texto-suave); margin: 0; }
    .numero { flex: none; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%;
      background: var(--acento-suave); color: var(--acento-texto); font-weight: 750; }
    @media (max-width: 900px) {
      .heroe { grid-template-columns: 1fr; }
      .demo { max-width: 560px; }
      .puertas, .pasos { grid-template-columns: 1fr; }
      .demo-ficha { right: 0; }
    }
    @media (max-width: 640px) {
      /* En el móvil la ficha no puede tapar el párrafo que explica: va debajo,
         solapando solo el borde de la hoja. */
      .demo { padding-bottom: 0; }
      .demo-libro { padding-bottom: 2.2rem; }
      .demo-ficha { position: relative; right: auto; bottom: auto; width: auto; margin: -1.4rem .75rem 0; }
      .dato { padding: .8rem .9rem; }
      .dato strong { font-size: 1.45rem; }
      .dato span { font-size: .8rem; line-height: 1.3; }
    }
    @media (max-width: 480px) {
      .acciones-heroe .boton { flex: 1 1 100%; }
      .demo-libro { font-size: 1.02rem; padding: 1.1rem 1.1rem 2.2rem; }
    }
  `,
})
export class Inicio {
  private readonly sesion = inject(Sesion);
  protected readonly inicio = this.sesion.inicio;
  protected readonly perfil = this.sesion.perfil;
  protected readonly seguir = computed(() => this.inicio()?.seguir ?? null);
  protected readonly num = num;
  protected readonly cefr = cefr;
  protected readonly miles = miles;
  protected readonly Math = Math;

  constructor() {
    if (this.sesion.motor() === 'listo') void this.sesion.refrescar();
  }
}
