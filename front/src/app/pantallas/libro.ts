import { ChangeDetectionStrategy, Component, OnDestroy, computed, effect, inject, input, signal, untracked } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Curva as GraficaCurva } from '../compartido/curva';
import { Icono } from '../compartido/icono';
import { Api, Curva, EntradaBiblioteca, Libro, Trabajo, mensajeError } from '../nucleo/api';
import { cefr, miles, minutosDe, num } from '../nucleo/formato';
import { Sesion } from '../nucleo/sesion';

/** La ficha: todo lo que ayuda a decidir si leer esto, antes de leerlo. */
@Component({
  selector: 'app-libro',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Icono, GraficaCurva],
  template: `
    <div class="pagina" data-seccion="encontrar">
      <a class="volver" routerLink="/encontrar"><app-icono nombre="izq" />Encontrar</a>

      @if (error()) {
        <div class="aviso error" role="alert"><p>{{ error() }}</p></div>
      } @else if (!libro()) {
        <div class="tarjeta">
          <div class="espera"><span class="giro"></span>
            <span>{{ lento() ? (esGutenberg() ? 'Descargando el libro de Project Gutenberg. La primera vez puede tardar; después queda guardado.' : 'Preparando el texto. La primera vez puede tardar; después queda guardado.') : 'Abriendo el libro…' }}</span>
          </div>
        </div>
      }

      @if (libro(); as l) {
        <section class="cabecera">
          <div class="portada" [attr.data-letra]="l.cefr" aria-hidden="true">
            <span>{{ (l.titulo[0] || '·').toUpperCase() }}</span>
          </div>
          <div class="info">
            <h1>{{ l.titulo }}</h1>
            <p class="autor">{{ l.autor || 'Autor desconocido' }}</p>
            <div class="fila chips">
              @if (l.dificultad !== null) {
                <span class="chip acento">{{ l.cefr }} · {{ num(l.dificultad) }} de 2</span>
              }
              <span class="chip">{{ l.capitulos.length }} {{ l.capitulos.length === 1 ? 'capítulo' : 'capítulos' }}</span>
              <span class="chip">{{ miles(l.palabras) }} palabras</span>
              @if (l.ficha) { <span class="chip"><app-icono nombre="reloj" />{{ l.ficha.tiempo }}</span> }
            </div>
            <!-- Aviso de contenido (contrato con f4): informa antes de abrir, no bloquea nada. -->
            @if (l.aviso_contenido) {
              <aside class="aviso-contenido" role="note">
                <strong><app-icono nombre="info" />Aviso sobre el contenido</strong>
                <p>{{ l.aviso_contenido }}</p>
              </aside>
            }
            <div class="fila cta">
              @if (enEstanteria(); as e) {
                <a class="boton" [routerLink]="['/leer', l.id, e.capitulo]"><app-icono nombre="libro" />Seguir en el capítulo {{ e.capitulo + 1 }}</a>
                @if (e.capitulo !== l.inicial) {
                  <a class="boton secundario" [routerLink]="['/leer', l.id, l.inicial]">Desde el principio</a>
                }
              } @else {
                <a class="boton" [routerLink]="['/leer', l.id, l.inicial]"><app-icono nombre="libro" />Empezar a leer</a>
              }
            </div>
            @if (l.inicial > 0) { <p class="tenue pequeno">Empieza en el capítulo {{ l.inicial + 1 }}: los anteriores son portadilla.</p> }
          </div>
        </section>

        <!-- Paridad con Gradio: la tabla de _TABLA_CEFR, junto a la dificultad del libro. -->
        <details class="tarjeta plana niveles">
          <summary><app-icono nombre="info" />¿Qué significa cada nivel?</summary>
          <div class="tabla-niveles">
            <table>
              <thead><tr><th scope="col">LiteraLevel</th><th scope="col">MCER</th><th scope="col">Qué suele significar</th></tr></thead>
              <tbody>
                @for (n of niveles; track n.letra) {
                  <tr [class.este]="l.cefr === n.letra">
                    <td>{{ n.rango }}</td><td><strong>{{ n.letra }}</strong></td><td>{{ n.texto }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          <p class="suave pequeno"><strong>LiteraLevel no certifica ningún nivel del MCER</strong>, y esta columna no equivale a un examen.
            El modelo aprendió a colocar un texto en una recta continua; la letra es la etiqueta más cercana.
            Sirve para elegir qué leer, no para acreditar nada ante nadie.</p>
        </details>

        <section class="veredicto tarjeta" [class.bien]="l.ficha?.exigente === false" [class.reto]="l.ficha?.exigente === true">
          @if (!perfil()) {
            <h2>¿Te va este libro?</h2>
            <p class="suave">Mide tu nivel en un minuto y te diré si te queda cómodo o qué capítulos están a tu alcance.</p>
            <a class="boton secundario" routerLink="/nivel">Medir mi nivel</a>
          } @else if (l.ficha?.exigente === true) {
            <h2>Va por encima de tu nivel</h2>
            @if (l.sugeridos.length) {
              <p class="suave">Pero no entero. Estos capítulos están a tu alcance ({{ num(perfil()!.nivel) }} · {{ cefr(perfil()!.nivel) }}):</p>
              <ul class="sugeridos">
                @for (s of l.sugeridos; track s.indice) {
                  <li><a [routerLink]="['/leer', l.id, s.indice]">
                    <span class="n">{{ s.indice + 1 }}</span>
                    <span class="t">{{ s.titulo }}</span>
                    <span class="chip verde">{{ num(s.dificultad) }}</span>
                  </a></li>
                }
              </ul>
            } @else {
              <p class="suave">Se puede leer igual: ve despacio y toca las palabras que no conozcas.</p>
            }
          } @else if (l.ficha?.exigente === false) {
            <h2><app-icono nombre="check" /> A tu medida</h2>
            <p class="suave">Con tu nivel ({{ num(perfil()!.nivel) }} · {{ cefr(perfil()!.nivel) }}) lo leerás con algo de reto pero sin atascarte.</p>
          } @else {
            <h2>Todavía no sé lo difícil que es</h2>
            <p class="suave">Mide la curva de abajo y te diré cómo te queda.</p>
          }
        </section>

        <section class="tarjeta curva">
          <div class="cab-seccion">
            <div>
              <h2>Dificultad capítulo a capítulo</h2>
              @if (curva(); as cv) {
                @if (cv.filas.length) {
                  <p class="suave">
                    @switch (cv.forma) {
                      @case ('se_complica') { Se va complicando: la segunda mitad es más dura que la primera. }
                      @case ('se_suelta') { Se va soltando: cuesta más al principio que al final. }
                      @default { Mantiene un nivel parejo de principio a fin. }
                    }
                    @if (cv.facil && cv.dificil) {
                      Lo más llevadero, el capítulo {{ cv.facil.capitulo }}; lo más exigente, el {{ cv.dificil.capitulo }}.
                    }
                  </p>
                }
              }
            </div>
            @if (curva()?.fuente; as f) {
              <span class="chip">{{ fuentes[f] }}</span>
            }
          </div>

          @if (trabajo(); as t) {
            <div class="progreso-medida">
              <div class="espera"><span class="giro"></span>
                <span>{{ t.estado === 'en_cola' ? 'Esperando turno: el modelo está midiendo otro libro.' :
                  'Leyendo con el modelo: capítulo ' + t.hechos + ' de ' + (t.total || '…') + '.' }}</span></div>
              <div class="avance"><i [style.width.%]="t.total ? (t.hechos / t.total) * 100 : 3"></i></div>
              @if (t.filas.length > 1) {
                <app-curva [filas]="t.filas" [nivelLector]="perfil()?.nivel ?? null" [elegible]="false" />
              }
            </div>
          } @else if (curva(); as cv) {
            @if (cv.filas.length) {
              <app-curva [filas]="cv.filas" [nivelLector]="perfil()?.nivel ?? null" [actual]="enEstanteria()?.capitulo ?? null"
                         (elegir)="leer($event)" />
              <p class="tenue pequeno">Toca un punto para leer ese capítulo.{{ perfil() ? ' La línea verde es tu nivel.' : '' }}</p>
            } @else {
              <p class="suave">Este libro todavía no está medido. El modelo lo lee y dibuja cómo sube y baja la dificultad.</p>
            }
            @if (cv.fuente !== 'completo') {
              <div class="fila">
                @if (!cv.filas.length) {
                  <button type="button" class="boton" (click)="medir('rapido')"><app-icono nombre="rayo" />Vistazo rápido (segundos)</button>
                }
                @if (cv.fuente !== 'catalogo') {
                  <button type="button" class="boton secundario" (click)="medir('completo')">Medir el libro entero (tarda más)</button>
                }
              </div>
            }
          } @else {
            <div class="esqueleto" style="height:230px"></div>
          }
          @if (errorCurva()) { <p class="aviso error">{{ errorCurva() }}</p> }
        </section>

        <div class="dos-col">
          @if (l.ficha; as f) {
            <section class="tarjeta">
              <h2>Cómo es de leer</h2>
              <dl class="rasgos">
                <div><dt>Frases</dt><dd>{{ num(f.frase_media, 0) }} palabras de media</dd></div>
                <div><dt>Diálogo</dt><dd>{{ num(f.dialogo * 100, 0) }}% de las frases · {{ f.forma_del_dialogo }}</dd></div>
                <div><dt>Vocabulario</dt><dd>{{ num(f.riqueza * 100, 1) }} palabras distintas por cada 100</dd></div>
                <div><dt>Tiempo</dt><dd>{{ f.tiempo }}{{ f.exigente === true ? ' (va por encima de tu nivel)' : f.exigente === false ? ' a tu ritmo' : '' }}</dd></div>
              </dl>
              @if (f.distintivas.length) {
                <p class="etiqueta">Lo que más se repite</p>
                <div class="fila palabras-clave" lang="en">
                  @for (p of f.distintivas; track p) { <span class="chip">{{ p }}</span> }
                </div>
              }
              <p class="tenue pequeno">Contado sobre el texto del libro; no lo dice ningún modelo.</p>
            </section>
          }

          <section class="tarjeta">
            <h2>¿De qué trata?</h2>
            @if (sinopsis(); as s) {
              @if (s.de_que_trata) { <p>{{ s.de_que_trata }}</p> }
              @if (s.temas?.length) { <div class="fila palabras-clave">@for (t of s.temas; track t) { <span class="chip acento">{{ t }}</span> }</div> }
              @if (s.para_quien) { <p><strong>Para quién:</strong> {{ s.para_quien }}</p> }
              @if (s.aviso) { <p class="aviso ambar"><span><strong>Antes de empezar:</strong> {{ s.aviso }}</span></p> }
              <p class="tenue pequeno">Resumen escrito por un modelo de lenguaje a partir de pasajes del libro.</p>
            } @else {
              <p class="suave">Un resumen en español hecho a partir de pasajes del principio, el medio y el final, sin destripar el final.</p>
              @if (errorSinopsis()) {
                <div class="aviso" [class.error]="!necesitaEntrar()"><p>{{ errorSinopsis() }}</p></div>
              }
              <div class="fila">
                <button type="button" class="boton secundario" (click)="pedirSinopsis()" [disabled]="pidiendoSinopsis()">
                  <app-icono nombre="chispa" />{{ pidiendoSinopsis() ? 'Leyendo pasajes…' : 'Resúmemelo' }}
                </button>
                @if (necesitaEntrar()) {
                  <button type="button" class="boton fantasma" (click)="abrirAjustes()">Entrar con mi perfil</button>
                }
              </div>
            }
          </section>
        </div>

        <details class="tarjeta indice">
          <summary><h2>Índice · {{ l.capitulos.length }} capítulos</h2></summary>
          <ol>
            @for (c of l.capitulos; track c.indice) {
              <li><a [routerLink]="['/leer', l.id, c.indice]">
                <span class="n">{{ c.indice + 1 }}</span><span class="t">{{ c.titulo }}</span>
                <span class="tenue pequeno">{{ minutosDe(c.palabras) }} min</span>
              </a></li>
            }
          </ol>
        </details>
      }
    </div>
  `,
  styles: `
    .volver { display: inline-flex; align-items: center; gap: .3rem; min-height: 44px; margin-bottom: .5rem; color: var(--texto-suave); text-decoration: none; font-weight: 600; }
    .cabecera { display: grid; grid-template-columns: 150px 1fr; gap: clamp(1rem, 3vw, 2rem); align-items: center; margin-bottom: 1.5rem; }
    .portada { aspect-ratio: 3 / 4.3; border-radius: 10px 16px 16px 10px; display: grid; place-items: center; color: #fff;
      font-family: var(--fuente-libro); font-size: 3.5rem; background: linear-gradient(160deg, var(--p1, #5b7cf0), var(--p2, #2e46b0));
      box-shadow: inset 6px 0 0 rgba(0,0,0,.12), var(--sombra-alta); }
    .portada[data-letra="A1"], .portada[data-letra="A2"] { --p1: #3fb58a; --p2: #1f7a5b; }
    .portada[data-letra="C1"] { --p1: #c0782f; --p2: #874b14; }
    .portada[data-letra="C2"] { --p1: #b0496b; --p2: #6e2440; }
    .info h1 { margin-bottom: .2rem; overflow-wrap: anywhere; }
    .autor { color: var(--texto-suave); font-size: 1.1rem; margin-bottom: .8rem; }
    .chips { gap: .45rem; margin-bottom: 1.1rem; }
    .cta { margin-bottom: .4rem; }
    .veredicto { margin-bottom: 1.25rem; border-left: 5px solid var(--borde-fuerte); }
    .aviso-contenido { margin: .75rem 0 .75rem; padding: .7rem .9rem; border-radius: var(--radio-sm);
      background: var(--ambar-suave); border-left: 4px solid var(--ambar); display: grid; gap: .25rem; }
    .aviso-contenido strong { display: flex; align-items: center; gap: .4rem; color: var(--texto); }
    .aviso-contenido p { margin: 0; color: var(--texto); line-height: 1.5; }
    .niveles { margin-bottom: 1.25rem; }
    .niveles summary { display: flex; align-items: center; gap: .5rem; min-height: 48px; cursor: pointer; font-weight: 650;
      color: var(--acento-texto); list-style: none; }
    .niveles summary::-webkit-details-marker { display: none; }
    .niveles p { margin: .75rem 0 0; }
    .tabla-niveles { overflow-x: auto; margin-top: .5rem; }
    .tabla-niveles table { width: 100%; border-collapse: collapse; font-size: .92rem; }
    .tabla-niveles th, .tabla-niveles td { text-align: left; padding: .45rem .6rem; border-bottom: 1px solid var(--borde); vertical-align: top; }
    .tabla-niveles th { font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; color: var(--texto-suave); }
    .tabla-niveles td:first-child { white-space: nowrap; font-variant-numeric: tabular-nums; }
    .tabla-niveles tr.este td { background: var(--acento-suave); color: var(--acento-texto); }
    .veredicto.bien { border-left-color: var(--verde); }
    .veredicto.reto { border-left-color: var(--ambar); }
    .veredicto h2 { display: flex; align-items: center; gap: .4rem; margin-bottom: .3rem; }
    .veredicto.bien h2 { color: var(--verde); }
    .sugeridos { list-style: none; padding: 0; margin: .5rem 0 0; display: grid; gap: .35rem; }
    .sugeridos a, .indice li a { display: grid; grid-template-columns: 2.2rem 1fr auto; align-items: center; gap: .6rem;
      min-height: 48px; padding: .3rem .6rem; border-radius: 12px; color: var(--texto); text-decoration: none; background: var(--superficie-2); }
    .sugeridos a:hover, .indice li a:hover { background: var(--superficie-3); }
    .n { display: grid; place-items: center; width: 2rem; height: 2rem; border-radius: 50%; background: var(--superficie); font-weight: 650; font-size: .85rem; }
    .t { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .curva { margin-bottom: 1.25rem; }
    .cab-seccion { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
    .cab-seccion h2 { margin-bottom: .25rem; }
    .progreso-medida { display: grid; gap: .8rem; }
    .dos-col { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.25rem; margin-bottom: 1.25rem; }
    .rasgos { margin: 0 0 1rem; display: grid; gap: .6rem; }
    .rasgos div { display: grid; grid-template-columns: 7.5rem 1fr; gap: .75rem; }
    .rasgos dt { font-weight: 650; color: var(--texto-suave); }
    .rasgos dd { margin: 0; }
    .palabras-clave { gap: .35rem; margin: .4rem 0 .8rem; }
    .indice summary { cursor: pointer; list-style: none; }
    .indice summary h2 { display: inline; margin: 0; }
    .indice summary::after { content: '▾'; float: right; color: var(--texto-tenue); }
    .indice ol { list-style: none; padding: 0; margin: 1rem 0 0; display: grid; gap: .3rem;
      grid-template-columns: repeat(auto-fill, minmax(min(300px, 100%), 1fr)); }
    .indice li a { background: transparent; border: 1px solid var(--borde); }
    @media (max-width: 760px) {
      .cabecera { grid-template-columns: 96px 1fr; align-items: start; }
      .portada { font-size: 2.2rem; }
      .dos-col { grid-template-columns: 1fr; }
      .cta .boton { flex: 1 1 100%; }
      .rasgos div { grid-template-columns: 1fr; gap: 0; }
    }
  `,
})
export class FichaLibro implements OnDestroy {
  readonly id = input.required<string>();

  private readonly api = inject(Api);
  private readonly sesion = inject(Sesion);
  private readonly router = inject(Router);

  protected readonly libro = signal<Libro | null>(null);
  protected readonly error = signal('');
  protected readonly lento = signal(false);
  /** Solo los «PG…» se bajan de Gutenberg; los textos libres (StoryWeaver, VOA…) salen del corpus abierto. */
  protected readonly esGutenberg = computed(() => /^pg/i.test(this.id()));
  protected readonly curva = signal<Curva | null>(null);
  protected readonly trabajo = signal<Trabajo | null>(null);
  protected readonly errorCurva = signal('');
  protected readonly estanteria = signal<EntradaBiblioteca[]>([]);
  protected readonly sinopsisPedida = signal<Libro['sinopsis']>(null);
  protected readonly pidiendoSinopsis = signal(false);
  protected readonly errorSinopsis = signal('');
  protected readonly necesitaEntrar = signal(false);

  protected readonly perfil = this.sesion.perfil;
  protected readonly enEstanteria = computed(() => this.estanteria().find(e => e.id === this.libro()?.id) ?? null);
  protected readonly sinopsis = computed(() => this.sinopsisPedida() ?? this.libro()?.sinopsis ?? null);

  protected readonly fuentes: Record<string, string> = {
    completo: 'Medido entero', rapido: 'Vistazo rápido', catalogo: 'Medido en el catálogo',
  };
  protected readonly num = num;
  protected readonly cefr = cefr;
  /** La misma tabla que `ui._TABLA_CEFR` en Gradio. */
  protected readonly niveles = [
    { rango: '0,00 – 0,20', letra: 'A1', texto: 'frases muy cortas, vocabulario de andar por casa' },
    { rango: '0,20 – 0,60', letra: 'A2', texto: 'narración sencilla, poca subordinación' },
    { rango: '0,60 – 1,00', letra: 'B1', texto: 'novela juvenil, prosa clara' },
    { rango: '1,00 – 1,40', letra: 'B2', texto: 'novela adulta corriente' },
    { rango: '1,40 – 1,80', letra: 'C1', texto: 'prosa literaria densa, vocabulario amplio' },
    { rango: '1,80 – 2,00', letra: 'C2', texto: 'clásicos exigentes, sintaxis larga' },
  ];
  protected readonly miles = miles;
  protected readonly minutosDe = minutosDe;

  private vivo = true;
  private carga = 0;

  constructor() {
    effect(() => {
      const id = this.id();
      untracked(() => void this.cargar(id));
    });
  }

  ngOnDestroy(): void { this.vivo = false; }

  private async cargar(id: string, forzar = false): Promise<void> {
    const token = ++this.carga;
    this.error.set('');
    if (!forzar) { this.libro.set(null); this.curva.set(null); this.trabajo.set(null); }
    const aviso = setTimeout(() => this.lento.set(true), 1200);
    try {
      const libro = await this.sesion.libro(id, forzar);
      if (token !== this.carga) return;
      this.libro.set(libro);
      this.api.biblioteca().subscribe({ next: b => this.estanteria.set(b.libros), error: () => {} });
      const cv = await firstValueFrom(this.api.curva(id));
      if (token !== this.carga) return;
      this.curva.set(cv);
      if (cv.trabajo) void this.seguirTrabajo(cv.trabajo);
    } catch (e) {
      if (token === this.carga) this.error.set(mensajeError(e, 'No he podido abrir este libro.'));
    } finally {
      clearTimeout(aviso);
      this.lento.set(false);
    }
  }

  protected async medir(modo: 'rapido' | 'completo'): Promise<void> {
    this.errorCurva.set('');
    try {
      const r = await firstValueFrom(this.api.medirCurva(this.id(), modo));
      if (r.trabajo) await this.seguirTrabajo(r.trabajo);
      else await this.cargar(this.id(), true);
    } catch (e) {
      this.errorCurva.set(mensajeError(e));
    }
  }

  private async seguirTrabajo(id: string): Promise<void> {
    while (this.vivo) {
      try {
        const t = await firstValueFrom(this.api.trabajo(id));
        if (!this.vivo) return;
        if (t.estado === 'hecho') {
          this.trabajo.set(null);
          // Con la curva nueva cambian el veredicto y los capítulos sugeridos.
          await this.cargar(this.id(), true);
          return;
        }
        if (t.estado === 'error') {
          this.trabajo.set(null);
          this.errorCurva.set(t.error || 'La medición se ha interrumpido.');
          return;
        }
        this.trabajo.set(t);
      } catch (e) {
        this.trabajo.set(null);
        this.errorCurva.set(mensajeError(e));
        return;
      }
      await new Promise(r => setTimeout(r, 1500));
    }
  }

  protected leer(indice: number): void {
    void this.router.navigate(['/leer', this.id(), indice]);
  }

  protected async pedirSinopsis(): Promise<void> {
    this.pidiendoSinopsis.set(true);
    this.errorSinopsis.set('');
    this.necesitaEntrar.set(false);
    try {
      const r = await firstValueFrom(this.api.sinopsis(this.id()));
      this.sinopsisPedida.set(r.sinopsis);
    } catch (e) {
      this.errorSinopsis.set(mensajeError(e));
      this.necesitaEntrar.set(e instanceof HttpErrorResponse && e.status === 403);
    } finally {
      this.pidiendoSinopsis.set(false);
    }
  }

  protected abrirAjustes(): void { this.sesion.ajustesAbiertos.set(true); }
}
