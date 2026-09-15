import { ChangeDetectionStrategy, Component, OnInit, computed, effect, inject, input, signal, untracked } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { bloquesBusqueda } from '../compartido/bloques-busqueda';
import { Icono } from '../compartido/icono';
import { TarjetaLibro } from '../compartido/tarjeta-libro';
import { Api, EntradaBiblioteca, LibroTarjeta, Recomendacion, mensajeError } from '../nucleo/api';
import { cefr, num } from '../nucleo/formato';
import { Sesion } from '../nucleo/sesion';

type Vista = 'buscar' | 'nivel' | 'mios';

@Component({
  selector: 'app-encontrar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RouterLink, Icono, TarjetaLibro],
  template: `
    <div class="pagina" data-seccion="encontrar">
      <header class="cabecera-pagina">
        <span class="antetitulo">Encontrar</span>
        <h1>¿Qué te apetece leer?</h1>
        <p>Descríbelo con tus palabras, en español o en inglés. Si ya sabes tu nivel, primero salen los que te quedan mejor.</p>
      </header>

      <form class="buscador" (ngSubmit)="buscar()" role="search">
        <app-icono nombre="lupa" class="lupa" />
        <label class="oculto-visual" for="consulta">Qué te apetece leer</label>
        <input id="consulta" name="consulta" class="entrada" [(ngModel)]="consulta" maxlength="300"
               placeholder="Detectives, Jane Austen, aventuras…" autocomplete="off" enterkeyhint="search">
        <button class="boton" type="submit" [disabled]="cargando()">Buscar</button>
      </form>
      <div class="fila bajo-buscador">
        @if (perfil(); as p) {
          <!-- Sin interruptor escondido: primero lo de tu nivel y, junto a los resultados,
               «Ver también los de otros niveles» (propuesta aprobada por Miguel, 14 sep). -->
          <span class="tenue pequeno">Primero lo de tu nivel ({{ num(p.nivel) }} · {{ cefr(p.nivel) }}) y un poco por encima.</span>
        } @else {
          <span class="tenue pequeno">¿No sabes tu nivel? <a routerLink="/nivel">Mídelo en un minuto</a> y ordenaré los libros por lo que te va.</span>
        }
      </div>

      <div class="pestanas" role="tablist" aria-label="Qué mostrar">
        <button role="tab" type="button" [attr.aria-selected]="vista() === 'buscar'" (click)="cambiar('buscar')">Resultados</button>
        <button role="tab" type="button" [attr.aria-selected]="vista() === 'nivel'" (click)="cambiar('nivel')">A mi nivel</button>
        <button role="tab" type="button" [attr.aria-selected]="vista() === 'mios'" (click)="cambiar('mios')">Mis libros</button>
      </div>

      @if (error()) { <div class="aviso error" role="alert"><p>{{ error() }}</p></div> }

      @switch (vista()) {
        @case ('buscar') {
          @if (cargando()) {
            <div class="espera cargando"><span class="giro"></span>
              <span>{{ lento() ? 'Despertando el buscador: la primera búsqueda tarda unos 20 segundos. Después va al momento.' : 'Buscando…' }}</span></div>
          } @else if (resultados(); as rs) {
            @if (aviso()) { <p class="aviso pequeno">{{ aviso() }}</p> }
            @if (rs.length && bloques(); as b) {
              @let sinBloques = !b.enTuNivel.length && !b.porEncima.length;
              @if (sinBloques) {
                <p class="aviso pequeno">De «{{ ultima() }}» no hay libros en tu nivel ni un poco por encima entre los resultados. Estos son los de otros niveles.</p>
              }
              @if (b.enTuNivel.length) {
                <section class="bloque" aria-labelledby="b-nivel">
                  <h2 id="b-nivel">En tu nivel</h2>
                  <div class="rejilla-auto">
                    @for (l of b.enTuNivel; track l.id) { <app-tarjeta-libro [libro]="l" [nivelLector]="nivelBusqueda()" /> }
                  </div>
                </section>
              }
              @if (b.porEncima.length) {
                <section class="bloque" aria-labelledby="b-encima">
                  <h2 id="b-encima">Un poco por encima de tu nivel</h2>
                  @if (b.enTuNivel.length < 4) {
                    <p class="tenue pequeno">De esto hay pocos en tu nivel. Estos se pueden leer tocando las palabras que no conozcas.</p>
                  }
                  <div class="rejilla-auto">
                    @for (l of b.porEncima; track l.id) { <app-tarjeta-libro [libro]="l" [nivelLector]="nivelBusqueda()" /> }
                  </div>
                </section>
              }
              @if (b.otrosNiveles.length || b.menosParecidos.length) {
                <!-- Un solo botón que alterna, con aria-expanded y aria-controls hacia un
                     contenedor que existe siempre (ronda 2 del front, 4e): antes «Ver» llevaba
                     aria-expanded sin aria-controls y «Ocultar» apuntaba a ids que no siempre se pintaban. -->
                @if (!sinBloques) {
                  <button type="button" class="boton secundario ver-otros" (click)="verOtros.set(!verOtros())"
                          [attr.aria-expanded]="verOtros()" aria-controls="otros-niveles">
                    {{ verOtros() ? 'Ocultar los de otros niveles' : 'Ver también los de otros niveles (' + (b.otrosNiveles.length + b.menosParecidos.length) + ')' }}</button>
                }
                <div id="otros-niveles" [hidden]="!(sinBloques || verOtros())">
                  @if (sinBloques || verOtros()) {
                    @if (b.otrosNiveles.length) {
                      <section class="bloque" aria-labelledby="b-otros">
                        <h2 id="b-otros">De otros niveles</h2>
                        <div class="rejilla-auto">
                          @for (l of b.otrosNiveles; track l.id) { <app-tarjeta-libro [libro]="l" [nivelLector]="nivelBusqueda()" /> }
                        </div>
                      </section>
                    }
                    @if (b.menosParecidos.length) {
                      <!-- Sin nivel del lector: la etiqueta «A tu medida» no puede sugerir que esto es lo que se pidió. -->
                      <section class="bloque" aria-labelledby="b-menos">
                        <h2 id="b-menos">Menos parecidos a lo que buscas</h2>
                        <div class="rejilla-auto">
                          @for (l of b.menosParecidos; track l.id) { <app-tarjeta-libro [libro]="l" /> }
                        </div>
                      </section>
                    }
                  }
                </div>
              }
              @if (nota()) { <p class="tenue pequeno nota">{{ nota() }}</p> }
            } @else if (rs.length) {
              <p class="tenue pequeno recuento">{{ rs.length }} {{ rs.length === 1 ? 'libro' : 'libros' }} para «{{ ultima() }}».</p>
              <div class="rejilla-auto">
                @for (l of rs; track l.id) { <app-tarjeta-libro [libro]="l" [nivelLector]="perfil()?.nivel ?? null" /> }
              </div>
              @if (nota()) { <p class="tenue pequeno nota">{{ nota() }}</p> }
            }
          } @else {
            <div class="ideas">
              <p class="etiqueta">Prueba con</p>
              <div class="fila">
                @for (idea of ideas; track idea) {
                  <button type="button" class="chip idea" (click)="usar(idea)">{{ idea }}</button>
                }
              </div>
            </div>
          }
        }
        @case ('nivel') {
          @if (!perfil()) {
            <div class="vacio tarjeta">
              <h2>Primero, tu nivel</h2>
              <p class="suave">Con seis preguntas cortas sé qué libros te quedan cómodos con un poco de reto.</p>
              <a class="boton" routerLink="/nivel">Medir mi nivel</a>
            </div>
          } @else if (cargando()) {
            <div class="espera cargando"><span class="giro"></span>Buscando lecturas cerca de tu nivel…</div>
          } @else if (recomendacion(); as r) {
            @if (r.rango) {
              <!-- Desde el reinicio 12 un tercio de las tarjetas son textos libres
                   (StoryWeaver, African Storybook, Let's Read, VOA) intercalados:
                   ya no es solo «lo más leído» (decisión de Miguel, aviso de f4). -->
              <p class="suave">Lecturas entre <strong>{{ num(r.rango[0]) }}</strong> y <strong>{{ num(r.rango[1]) }}</strong>, cómodas pero con algo de reto:
                {{ hayLibres(r.resultados) ? 'lo más leído, con cuentos de libre acceso intercalados.' : 'lo más leído.' }}</p>
            }
            @if (r.rescate) {
              <p class="aviso ambar">Ninguno de los libros de tu nivel se puede abrir aquí. Estos son los más fáciles que sí: ve despacio y toca las palabras.</p>
            }
            @if (r.resultados.length) {
              <div class="rejilla-auto">
                @for (l of r.resultados; track l.id) { <app-tarjeta-libro [libro]="l" [nivelLector]="perfil()?.nivel ?? null" /> }
              </div>
            } @else {
              <p class="aviso">No hay libros medidos en ese rango. Describe lo que te apetece arriba: el buscador sí se ajusta a tu nivel sin exigir que coincida exacto.</p>
            }
          }
        }
        @case ('mios') {
          @if (cargando()) {
            <div class="espera cargando"><span class="giro"></span>Abriendo tu estantería…</div>
          } @else if (mios(); as ms) {
            @if (ms.length) {
              <ul class="estanteria">
                @for (e of ms; track e.id) {
                  <li class="tarjeta plana">
                    <a class="principal" [routerLink]="['/leer', e.id, e.capitulo]">
                      <strong>{{ e.titulo }}</strong>
                      <span class="suave pequeno">{{ e.autor || 'Autor desconocido' }} · capítulo {{ e.capitulo + 1 }} de {{ e.capitulos }}
                        @if (e.consultadas) { · {{ e.consultadas }} {{ e.consultadas === 1 ? 'palabra consultada' : 'palabras consultadas' }} }</span>
                      <span class="avance"><i [style.width.%]="e.avance * 100"></i></span>
                    </a>
                    <div class="fila">
                      <a class="boton pequeno" [routerLink]="['/leer', e.id, e.capitulo]">Seguir</a>
                      <a class="boton pequeno secundario" [routerLink]="['/libro', e.id]">Ficha</a>
                      <button type="button" class="boton-icono" (click)="olvidar(e)"
                              [attr.aria-label]="(e.id.startsWith('u') ? 'Borrar el libro subido ' : 'Quitar de mis libros ') + e.titulo"><app-icono nombre="basura" /></button>
                    </div>
                  </li>
                }
              </ul>
            } @else {
              <div class="vacio tarjeta">
                <h2>Tu estantería está vacía</h2>
                <p class="suave">Cada libro que abras aparecerá aquí, con el capítulo por donde vas.</p>
              </div>
            }
          }
          <section class="subir tarjeta plana">
            <div>
              <h2>¿Tienes tu propio libro?</h2>
              <p class="suave pequeno">Sube un .epub, un .pdf o un .txt (hasta 20 MB). Solo lo ves tú, en este navegador.</p>
            </div>
            <label class="boton secundario">
              <app-icono nombre="subir" />{{ subiendo() ? 'Subiendo…' : 'Subir un libro' }}
              <input type="file" accept=".epub,.pdf,.txt" class="oculto-visual" (change)="subir($event)" [disabled]="subiendo()">
            </label>
          </section>
        }
      }
    </div>
  `,
  styles: `
    .buscador { position: relative; display: flex; gap: .6rem; }
    .buscador .entrada { padding-left: 3rem; min-height: 58px; font-size: 1.08rem; border-radius: 999px; box-shadow: var(--sombra); }
    .buscador .boton { min-height: 58px; padding: 0 1.6rem; }
    .lupa { position: absolute; left: 1.05rem; top: 50%; transform: translateY(-50%); color: var(--texto-tenue); font-size: 1.2rem; pointer-events: none; }
    .bajo-buscador { margin: .75rem .5rem 1.25rem; min-height: 32px; }
    .interruptor { display: inline-flex; align-items: center; gap: .55rem; cursor: pointer; color: var(--texto-suave); font-weight: 600; min-height: 44px; }
    .interruptor input { width: 20px; height: 20px; accent-color: var(--acento); }
    .pestanas { display: flex; gap: .3rem; padding: .3rem; border-radius: 999px; background: var(--superficie-2); width: fit-content; max-width: 100%; margin-bottom: 1.25rem; overflow-x: auto; }
    .pestanas button { min-height: 48px; padding: 0 1.1rem; border-radius: 999px; border: 0; background: transparent; color: var(--texto-suave); font-weight: 650; cursor: pointer; white-space: nowrap; }
    .pestanas button[aria-selected="true"] { background: var(--superficie); color: var(--texto); box-shadow: var(--sombra); }
    .cargando { padding: 2rem 0; }
    .recuento { margin-bottom: .75rem; }
    .bloque { margin-bottom: 1.5rem; }
    .bloque h2 { font-size: 1.15rem; margin: 0 0 .6rem; }
    .bloque > p { margin: -.2rem 0 .75rem; }
    .ver-otros { min-height: 48px; width: 100%; max-width: 26rem; margin: .25rem 0 1rem; }
    .nota { margin-top: 1rem; max-width: 70ch; }
    .ideas { padding: 1rem 0; }
    /* Una mano (investigacion/una_mano.md §3.3): pestañas a 48 px, ideas a 44 con 8 de
       hueco, y la casilla de «Ordenar por mi nivel» es la fila entera, no los 20 px del cuadro. */
    .idea { min-height: 44px; cursor: pointer; font-size: .92rem; }
    .ideas { gap: .5rem; }
    .bajo-buscador .interruptor { display: inline-flex; align-items: center; gap: .6rem; min-height: 48px; cursor: pointer; }
    .bajo-buscador .interruptor input { width: 22px; height: 22px; accent-color: var(--seccion, var(--acento)); }
    .idea:hover { background: var(--acento-suave); color: var(--acento-texto); }
    .vacio { text-align: center; padding: 2.5rem 1.5rem; }
    .estanteria { list-style: none; padding: 0; margin: 0 0 1.25rem; display: grid; gap: .75rem; }
    .estanteria li { display: flex; align-items: center; gap: 1rem; justify-content: space-between; flex-wrap: wrap; }
    .principal { display: grid; gap: .3rem; flex: 1 1 280px; color: inherit; text-decoration: none; min-width: 0; }
    .principal strong { font-size: 1.08rem; }
    .subir { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; margin-top: 1rem; background: var(--superficie-2); }
    .subir h2 { font-size: 1.1rem; margin-bottom: .2rem; }
    .subir p { margin: 0; }
    .subir label { cursor: pointer; }
    @media (max-width: 560px) {
      .buscador { flex-direction: column; }
      .buscador .boton { width: 100%; min-height: 50px; }
      .lupa { top: 29px; }
    }
  `,
})
export class Encontrar implements OnInit {
  readonly q = input<string>();
  readonly vista_ = input<string>(undefined, { alias: 'vista' });

  private readonly api = inject(Api);
  private readonly sesion = inject(Sesion);
  private readonly router = inject(Router);

  protected consulta = '';
  protected readonly vista = signal<Vista>('buscar');
  /** «Ver también los de otros niveles»: vuelve a cerrarse con cada búsqueda nueva. */
  protected readonly verOtros = signal(false);
  protected readonly cargando = signal(false);
  protected readonly lento = signal(false);
  protected readonly error = signal('');
  protected readonly resultados = signal<LibroTarjeta[] | null>(null);
  protected readonly aviso = signal('');
  protected readonly nota = signal('');
  protected readonly ajustado = signal(false);
  protected readonly ultima = signal('');
  protected readonly recomendacion = signal<Recomendacion | null>(null);
  protected readonly mios = signal<EntradaBiblioteca[] | null>(null);
  protected readonly subiendo = signal(false);
  protected readonly perfil = this.sesion.perfil;

  /** Al entrar o recargar en ?vista=nivel, el perfil llega después de montar la
   *  pantalla (lo trae `Sesion` por red): `cambiar` no lo veía, «A mi nivel»
   *  quedaba vacía y no se pedía /api/recomendar (f4, prueba final). */
  private readonly alLlegarPerfil = effect(() => {
    const p = this.perfil();
    untracked(() => {
      if (p && this.vista() === 'nivel' && !this.recomendacion() && !this.cargando()) void this.recomendar();
    });
  });

  /** «Detectives en Londres» dejaba a A1–B2 sin nada de su nivel ni un poco por
   *  encima (1 en otros niveles y 23 menos parecidos; ronda 3 del front de 4e):
   *  «Detectives» da 9 a la medida de B1 y algo en la franja de A1 a C1. */
  protected readonly ideas = [
    'Detectives', 'Aventuras en el mar', 'Una historia de amor del siglo XIX',
    'Cuentos cortos para empezar', 'Ciencia ficción', 'Jane Austen', 'Terror gótico', 'Fábulas con animales',
  ];
  protected readonly num = num;
  protected readonly cefr = cefr;
  protected readonly hayResultados = computed(() => (this.resultados()?.length ?? 0) > 0);
  /** El nivel con el que el motor ordenó; sin él (sin perfil) no hay bloques. */
  protected readonly nivelBusqueda = signal<number | null>(null);
  protected readonly bloques = computed(() => {
    const rs = this.resultados();
    const nivel = this.nivelBusqueda();
    return rs && nivel !== null ? bloquesBusqueda(rs, nivel) : null;
  });

  ngOnInit(): void {
    const v = this.vista_();
    const q = (this.q() ?? '').trim();
    if (q) {
      this.consulta = q;
      void this.buscar(false);
    } else if (v === 'nivel' || v === 'mios') {
      this.cambiar(v, false);
    }
  }

  protected cambiar(v: Vista, navegar = true): void {
    this.vista.set(v);
    this.error.set('');
    if (navegar) {
      void this.router.navigate([], { queryParams: { vista: v === 'buscar' ? null : v, q: v === 'buscar' ? this.ultima() || null : null }, replaceUrl: true });
    }
    if (v === 'nivel' && this.perfil() && !this.recomendacion()) void this.recomendar();
    if (v === 'mios') void this.cargarMios();
  }

  protected usar(idea: string): void {
    this.consulta = idea;
    void this.buscar();
  }

  protected async buscar(navegar = true): Promise<void> {
    const q = this.consulta.trim();
    if (!q) { this.error.set('Escribe qué tipo de lectura buscas.'); return; }
    this.vista.set('buscar');
    this.error.set('');
    this.cargando.set(true);
    // 3 s: con el catálogo de 15.357 externos, la primera tarda unos 21 (f4, reinicio 10).
    const reloj = setTimeout(() => this.lento.set(true), 3000);
    if (navegar) void this.router.navigate([], { queryParams: { q, vista: null }, replaceUrl: true });
    try {
      // 24 y no 12: con los bloques, lo de otros niveles va detrás de un botón y sin
      // candidatos de sobra «En tu nivel» se quedaba corto.
      const r = await firstValueFrom(this.api.buscar(q, true, 24));
      this.verOtros.set(false);
      this.nivelBusqueda.set(r.ajustado ? r.nivel : null);
      this.resultados.set(r.resultados);
      this.aviso.set(r.aviso);
      this.nota.set(r.nota);
      this.ajustado.set(r.ajustado);
      this.ultima.set(q);
    } catch (e) {
      this.error.set(mensajeError(e, 'No he podido completar la búsqueda.'));
    } finally {
      clearTimeout(reloj);
      this.lento.set(false);
      this.cargando.set(false);
    }
  }

  /** Algún texto libre entre las tarjetas: los de Gutenberg son los únicos con id «PG…». */
  protected hayLibres(libros: LibroTarjeta[]): boolean {
    return libros.some(l => !/^pg/i.test(l.id));
  }

  private async recomendar(): Promise<void> {
    this.cargando.set(true);
    try {
      this.recomendacion.set(await firstValueFrom(this.api.recomendar()));
    } catch (e) {
      this.error.set(mensajeError(e));
    } finally {
      this.cargando.set(false);
    }
  }

  private async cargarMios(): Promise<void> {
    this.cargando.set(true);
    try {
      this.mios.set((await firstValueFrom(this.api.biblioteca())).libros);
    } catch (e) {
      this.error.set(mensajeError(e));
    } finally {
      this.cargando.set(false);
    }
  }

  protected async olvidar(e: EntradaBiblioteca): Promise<void> {
    // Un libro subido se borra de verdad: quitarlo solo de la estantería dejaba el
    // archivo ocupando uno de los 30 huecos y el 429 no se iba nunca (auditoría de Codex, 4).
    const subido = e.id.startsWith('u');
    if (subido && !confirm(`¿Borrar «${e.titulo}»? Se borra el archivo que subiste; para volver a leerlo tendrás que subirlo otra vez.`)) return;
    try {
      await firstValueFrom(subido ? this.api.borrarSubido(e.id) : this.api.olvidar(e.id));
      this.mios.set((this.mios() ?? []).filter(x => x.id !== e.id));
      void this.sesion.refrescar();
    } catch (err) {
      this.error.set(mensajeError(err));
    }
  }

  protected async subir(ev: Event): Promise<void> {
    const entrada = ev.target as HTMLInputElement;
    const archivo = entrada.files?.[0];
    entrada.value = '';
    if (!archivo) return;
    if (archivo.size > 20 * 1024 * 1024) { this.error.set('El archivo pasa de 20 MB.'); return; }
    this.subiendo.set(true);
    this.error.set('');
    try {
      const libro = await firstValueFrom(this.api.subirLibro(archivo));
      void this.router.navigate(['/libro', libro.id]);
    } catch (err) {
      this.error.set(mensajeError(err, 'No he podido abrir ese archivo.'));
    } finally {
      this.subiendo.set(false);
    }
  }
}
