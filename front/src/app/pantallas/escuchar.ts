import { ChangeDetectionStrategy, Component, ElementRef, HostListener, OnDestroy, computed, effect, inject, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Api, AudioLectura, EntradaBiblioteca, Libro, mensajeError } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Icono } from '../compartido/icono';
import { ControlVelocidad } from '../compartido/control-velocidad';
import { ConsultaPalabra } from '../compartido/consulta-palabra';
import { velocidadValida } from '../nucleo/velocidad';

@Component({
  selector: 'app-escuchar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RouterLink, Icono, ControlVelocidad, ConsultaPalabra],
  template: `
    <div class="pagina estrecha" [attr.inert]="consultada() ? '' : null">
      <header class="cabecera-pagina">
        <span class="antetitulo">Mi espacio</span>
        <h1>Escuchar un libro</h1>
        <p>Escucha mientras lees. El texto se ilumina para ayudarte a seguir la voz.</p>
      </header>
      <section class="tarjeta controles" aria-label="Elegir lectura" [attr.aria-busy]="ocupado()">
        <label for="libro-audio">Libro de mi biblioteca</label>
        <select id="libro-audio" [ngModel]="id()" (ngModelChange)="elegir($event)" [disabled]="ocupado()">
          <option value="">Elige un libro</option>
          @for (b of libros(); track b.id) { <option [value]="b.id">{{ b.titulo }}</option> }
        </select>
        @if (!libros().length && !ocupado()) {
          <p>Abre o sube un libro para escucharlo aquí.</p>
          <a routerLink="/encontrar" class="enlace">Buscar un libro</a>
          <a routerLink="/leer" class="enlace">Abrir o subir un libro</a>
        }
        @if (libro(); as b) {
          <label for="capitulo-audio">Capítulo</label>
          <select id="capitulo-audio" [ngModel]="cap()" (ngModelChange)="cambiarCapitulo(+$event)" [disabled]="ocupado()">
            @for (c of b.capitulos; track c.indice) { <option [ngValue]="c.indice">{{ c.titulo || 'Capítulo ' + (c.indice + 1) }}</option> }
          </select>
        }
        @if (fragmento(); as f) {
          <div class="fila partes">
            <button type="button" class="boton secundario" (click)="mover(-1)" [disabled]="ocupado() || !hayAnterior()">Anterior</button>
            <span>Fragmento {{ f.parte + 1 }} de {{ f.total }}</span>
            <button type="button" class="boton secundario" (click)="mover(1)" [disabled]="ocupado() || !haySiguiente()">Siguiente</button>
          </div>
          @if (f.guardado) {
            <p class="suave">Audio guardado. Volver a escucharlo no consume usos.</p>
            @if (!audioUrl()) { <button class="boton" type="button" (click)="escuchar()" [disabled]="ocupado()">Cargar audio guardado</button> }
          } @else {
            <p class="suave">Hasta {{ f.tope_caracteres }} caracteres por fragmento. Preparar este audio consume 1 uso de tu cuenta; después queda guardado.</p>
            @if (puedeGenerar()) {
              <button class="boton" type="button" (click)="escuchar()" [disabled]="ocupado()">Preparar este fragmento</button>
            } @else {
              <p>{{ motivoCuenta() }}</p>
              @if (!sesion.entrada()?.dentro && sesion.entrada()?.puerta) {
                <button class="boton" type="button" (click)="sesion.abrirPerfil()">Entrar</button>
              }
            }
          }
        }
        @if (ocupado()) { <p role="status">{{ estado() }}</p> }
        @if (aviso()) { <p class="aviso" role="alert">{{ aviso() }}</p> }
      </section>
      @if (fragmento(); as f) {
        <section class="tarjeta lectura" aria-label="Texto de la lectura">
          <h2>{{ f.titulo }}</h2>
          @if (audioUrl(); as url) {
            <audio #reproductor hidden preload="metadata" [src]="url" (timeupdate)="sincronizar()" (seeking)="sincronizar()"
              (loadedmetadata)="sincronizar()" (durationchange)="sincronizar()" (play)="sincronizar()" (pause)="sincronizar()"
              (ended)="terminar()" (error)="errorAudio()"></audio>
            <section class="barra-audio" aria-label="Reproductor de lectura">
              <div class="contexto-audio">
                <app-icono nombre="libro" />
                <strong>{{ f.titulo }}</strong>
                <span>{{ f.parte + 1 }} / {{ f.total }}</span>
              </div>
              <div class="acciones-audio">
                <button class="control-audio salto" type="button" aria-label="Retroceder 10 segundos" title="Retroceder 10 segundos"
                  (click)="saltar(-10)" [disabled]="!duracion()"><app-icono nombre="recargar" /><span>10</span></button>
                <button class="control-audio reproducir" type="button" [attr.aria-label]="reproduciendo() ? 'Pausar audio' : 'Reproducir audio'"
                  (click)="alternar()" [disabled]="iniciando()">
                  @if (reproduciendo()) {
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14M16 5v14" /></svg>
                  } @else { <app-icono nombre="play" /> }
                </button>
                <button class="control-audio salto adelante" type="button" aria-label="Avanzar 10 segundos" title="Avanzar 10 segundos"
                  (click)="saltar(10)" [disabled]="!duracion()"><app-icono nombre="recargar" /><span>10</span></button>
                <app-control-velocidad class="velocidad" [compacto]="true" [valor]="velocidad()" (valorChange)="cambiarVelocidad($event)" />
                <button class="control-audio siguiente" type="button" aria-label="Siguiente fragmento" title="Siguiente fragmento"
                  (click)="mover(1)" [disabled]="ocupado() || !haySiguiente()"><app-icono nombre="ultimo" /></button>
              </div>
              <div class="progreso-audio">
                <span>{{ reloj(tiempo()) }}</span>
                <input type="range" aria-label="Posición del audio" min="0" [max]="duracion() || 1" step="0.1" [value]="tiempo()"
                  [disabled]="!duracion()" [attr.aria-valuetext]="reloj(tiempo()) + ' de ' + reloj(duracion())"
                  (input)="buscar(+$any($event.target).value)" />
                <span>{{ reloj(duracion()) }}</span>
              </div>
            </section>
            <p class="tenue pequeno">Voz generada por IA.@if (f.aproximado) { El resaltado es aproximado. }</p>
          }
          <p class="tenue pequeno">Toca una palabra o selecciónala para consultar su significado. El audio se pausa y conserva tu lugar.</p>
          <p #texto class="texto" lang="en">@for (p of palabras(); track $index) {<span role="button" tabindex="0" [attr.aria-label]="'Consultar ' + p.trim()"
            (click)="consultar(p)" (keydown.enter)="consultar(p)" (keydown.space)="$event.preventDefault(); consultar(p)"
            [class.leida]="$index < leidas()" [class.actual]="$index === activa()">{{ p }}</span>}</p>
          @if (finalizado()) { <p role="status">Fragmento terminado. Puedes repetirlo o pasar al siguiente.</p> }
        </section>
      }
    </div>
    @if (consultada(); as palabra) {
      <app-consulta-palabra [texto]="palabra" [libro]="id()" [capitulo]="cap()" (cerrar)="cerrarConsulta()" />
    }
  `,
  styles: `
    .controles { display: grid; gap: .85rem; margin-bottom: 1.25rem; }
    select { width: 100%; min-height: 44px; padding: .65rem; border: 1px solid var(--borde); border-radius: .5rem; background: var(--fondo); color: inherit; }
    :host { display: block; }
    :host:has(.barra-audio) { padding-bottom: 11rem; }
    .partes { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; }
    .partes span { grid-column: 1 / -1; grid-row: 1; text-align: center; font-size: .85rem; }
    .lectura h2 { font-size: 1.2rem; margin-bottom: 1rem; }
    .barra-audio { position: fixed; z-index: 45; bottom: 1rem; left: 50%; transform: translateX(-50%); width: min(640px, calc(100% - 2rem));
      padding: .75rem 1rem; border: 1px solid var(--borde-fuerte); border-radius: 1.25rem; background: var(--superficie);
      box-shadow: 0 8px 32px -8px #0006; }
    .contexto-audio { display: flex; align-items: center; gap: .5rem; color: var(--acento-texto); font-size: .8rem; }
    .contexto-audio strong { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .contexto-audio span { margin-left: auto; white-space: nowrap; color: var(--texto-suave); font-variant-numeric: tabular-nums; }
    .acciones-audio { display: flex; align-items: center; justify-content: center; gap: .65rem; padding-top: .45rem; }
    .control-audio { position: relative; display: inline-grid; place-items: center; width: 44px; height: 44px; padding: 0;
      border: 0; border-radius: 50%; background: transparent; color: var(--acento-texto); cursor: pointer; }
    .control-audio:hover { background: var(--acento-suave); }
    .control-audio:disabled { opacity: .4; cursor: default; }
    .reproducir { width: 52px; height: 52px; background: var(--acento); color: var(--sobre-acento); font-size: 1.35rem; }
    .reproducir:hover { background: var(--acento-hondo); }
    .reproducir svg { width: 26px; height: 26px; fill: none; stroke: currentColor; stroke-width: 4; stroke-linecap: round; }
    .salto app-icono { width: 32px; height: 32px; }
    .salto span { position: absolute; font-size: .65rem; font-weight: 700; }
    .adelante app-icono { transform: scaleX(-1); }
    .velocidad { width: 78px; }
    .progreso-audio { display: flex; align-items: center; gap: .6rem; font-size: .75rem; color: var(--texto-suave); font-variant-numeric: tabular-nums; }
    .progreso-audio input { flex: 1; min-width: 0; height: 32px; margin: 0; accent-color: var(--acento); cursor: pointer; }
    .texto { font-family: Georgia, serif; font-size: 1.2rem; line-height: 1.9; white-space: pre-wrap; overflow-wrap: anywhere; }
    .texto span { border-radius: .2rem; cursor: pointer; }
    .leida { color: var(--acento-texto); }
    .actual { background: #ffe08a; color: #172a43; box-shadow: 0 2px 0 #bd8300; }
    @media (max-width: 760px) {
      .barra-audio { left: 0; right: 0; transform: none; width: auto; bottom: var(--barra-inf); border-radius: 1rem 1rem 0 0;
        padding: .6rem max(1rem, env(safe-area-inset-left)); transition: bottom .25s ease; }
      :host-context(body:has(.nav-movil.oculta)) .barra-audio { bottom: 0; padding-bottom: max(.6rem, env(safe-area-inset-bottom)); }
    }
    @media (max-width: 420px) { .partes .boton { padding: .6rem .65rem; } .texto { font-size: 1.1rem; } }
  `,
})
export class Escuchar implements OnDestroy {
  private readonly api = inject(Api);
  private readonly elemento = inject<ElementRef<HTMLElement>>(ElementRef);
  readonly sesion = inject(Sesion);
  readonly reproductor = viewChild<ElementRef<HTMLAudioElement>>('reproductor');
  readonly texto = viewChild<ElementRef<HTMLElement>>('texto');
  readonly consultada = signal('');
  readonly libros = signal<EntradaBiblioteca[]>([]);
  readonly libro = signal<Libro | null>(null);
  readonly id = signal('');
  readonly cap = signal(0);
  readonly fragmento = signal<AudioLectura | null>(null);
  readonly ocupado = signal(false);
  readonly estado = signal('Cargando biblioteca…');
  readonly aviso = signal('');
  readonly audioUrl = signal('');
  readonly activa = signal(-1);
  readonly leidas = signal(0);
  readonly finalizado = signal(false);
  readonly velocidad = signal(1);
  readonly reproduciendo = signal(false);
  readonly iniciando = signal(false);
  readonly tiempo = signal(0);
  readonly duracion = signal(0);
  readonly palabras = computed(() => this.fragmento()?.texto.match(/\S+\s*/g) ?? []);
  readonly hayAnterior = computed(() => !!this.fragmento() && (this.fragmento()!.parte > 0 || this.cap() > 0));
  readonly haySiguiente = computed(() => !!this.fragmento() && (this.fragmento()!.parte + 1 < this.fragmento()!.total || this.cap() + 1 < (this.libro()?.capitulos.length ?? 0)));
  readonly puedeGenerar = computed(() => {
    const e = this.sesion.entrada();
    return !!e?.openai && (!e.puerta || e.dentro) && (e.restantes === null || e.restantes > 0);
  });
  readonly motivoCuenta = computed(() => {
    const e = this.sesion.entrada();
    if (!e) return 'Comprobando tu cuenta…';
    if (e.puerta && !e.dentro) return 'Entra con tu cuenta para preparar audio.';
    if (e.restantes === 0) return 'Has agotado tus usos. Puedes seguir escuchando los audios guardados.';
    return 'La voz no está disponible ahora. Los audios guardados siguen funcionando.';
  });
  private version = 0;
  private desplazamiento = 0;
  private identidad: string | null = null;
  private seleccion: ReturnType<typeof setTimeout> | undefined;
  private origenConsulta: HTMLElement | null = null;
  private readonly cuenta = effect(() => {
    const e = this.sesion.entrada();
    if (!e) return;
    const identidad = e.dentro ? e.nombre : 'visitante';
    if (identidad !== this.identidad) {
      this.identidad = identidad;
      void this.iniciar();
    }
  });

  private limpiarAudio(): void {
    this.reproductor()?.nativeElement.pause();
    this.consultada.set('');
    const url = this.audioUrl();
    if (url) URL.revokeObjectURL(url);
    this.audioUrl.set('');
    this.activa.set(-1);
    this.leidas.set(0);
    cancelAnimationFrame(this.desplazamiento);
    this.finalizado.set(false);
    this.reproduciendo.set(false);
    this.iniciando.set(false);
    this.tiempo.set(0);
    this.duracion.set(0);
  }

  async iniciar(): Promise<void> {
    const v = ++this.version;
    this.limpiarAudio();
    this.fragmento.set(null);
    this.libro.set(null);
    this.id.set('');
    this.libros.set([]);
    this.ocupado.set(true);
    this.aviso.set('');
    this.estado.set('Cargando biblioteca…');
    try {
      const biblioteca = await firstValueFrom(this.api.biblioteca());
      if (v !== this.version) return;
      this.libros.set(biblioteca.libros);
      const seguir = this.sesion.inicio()?.seguir;
      const elegido = biblioteca.libros.find(b => b.id === seguir?.id) ?? biblioteca.libros[0];
      if (elegido) await this.elegir(elegido.id);
    } catch (e) { if (v === this.version) this.aviso.set(mensajeError(e)); }
    finally { if (v === this.version) this.ocupado.set(false); }
  }

  async elegir(id: string): Promise<void> {
    const v = ++this.version;
    this.limpiarAudio();
    this.fragmento.set(null);
    this.libro.set(null);
    this.id.set(id);
    if (!id) { this.ocupado.set(false); return; }
    this.ocupado.set(true);
    this.estado.set('Abriendo el libro…');
    this.aviso.set('');
    try {
      const libro = await firstValueFrom(this.api.libro(id));
      if (v !== this.version) return;
      this.libro.set(libro);
      const guardado = this.libros().find(b => b.id === id)?.capitulo;
      this.cap.set(guardado ?? libro.inicial);
      await this.cargar(0);
    } catch (e) { if (v === this.version) this.aviso.set(mensajeError(e)); }
    finally { if (v === this.version) this.ocupado.set(false); }
  }

  async cargar(parte: number): Promise<void> {
    const v = ++this.version;
    this.limpiarAudio();
    this.fragmento.set(null);
    this.ocupado.set(true);
    this.estado.set('Cargando fragmento…');
    this.aviso.set('');
    try {
      const f = await firstValueFrom(this.api.audioLectura(this.id(), this.cap(), parte));
      if (v === this.version) this.fragmento.set(f);
    } catch (e) { if (v === this.version) this.aviso.set(mensajeError(e)); }
    finally { if (v === this.version) this.ocupado.set(false); }
  }

  async cambiarCapitulo(cap: number): Promise<void> { this.cap.set(cap); await this.cargar(0); }

  async mover(paso: number): Promise<void> {
    const f = this.fragmento();
    if (!f || this.ocupado()) return;
    let parte = f.parte + paso;
    if (parte >= f.total) { this.cap.update(c => c + 1); parte = 0; }
    else if (parte < 0) {
      this.cap.update(c => c - 1);
      await this.cargar(0);
      const anterior = this.fragmento();
      if (anterior && anterior.total > 1) await this.cargar(anterior.total - 1);
      return;
    }
    await this.cargar(parte);
  }

  async escuchar(): Promise<void> {
    const f = this.fragmento();
    if (!f || this.ocupado()) return;
    const v = ++this.version;
    this.ocupado.set(true);
    this.estado.set(f.guardado ? 'Cargando audio guardado…' : 'Preparando audio y guía de lectura…');
    this.aviso.set('');
    try {
      const listo = f.guardado ? f : await firstValueFrom(this.api.audioLectura(this.id(), this.cap(), f.parte, true));
      if (v !== this.version) return;
      this.fragmento.set(listo);
      const blob = await firstValueFrom(this.api.audioLecturaArchivo(listo.clave));
      if (v !== this.version) return;
      this.limpiarAudio();
      this.audioUrl.set(URL.createObjectURL(blob));
    } catch (e) { if (v === this.version) this.aviso.set(mensajeError(e)); }
    finally {
      if (v === this.version) {
        this.ocupado.set(false);
        if (!f.guardado) void this.sesion.refrescar();
      }
    }
  }

  sincronizar(): void {
    const audio = this.reproductor()?.nativeElement;
    const f = this.fragmento();
    if (!audio || !f) return;
    audio.playbackRate = this.velocidad();
    const tiempo = audio.currentTime;
    this.tiempo.set(tiempo);
    this.duracion.set(Number.isFinite(audio.duration) ? audio.duration : 0);
    this.reproduciendo.set(!audio.paused && !audio.ended);
    if (audio.ended) { this.terminar(); return; }
    this.finalizado.set(false);
    if (f.palabras.length === this.palabras().length && f.palabras.length) {
      this.activa.set(f.palabras.findIndex(p => tiempo >= p.inicio && tiempo < p.fin));
      this.leidas.set(f.palabras.filter(p => p.fin <= tiempo).length);
    } else if (Number.isFinite(audio.duration) && audio.duration > 0) {
      const pesos = this.palabras().map(p => Math.max(1, p.trim().length));
      const objetivo = tiempo / audio.duration * pesos.reduce((a, b) => a + b, 0);
      let acumulado = 0;
      this.activa.set(pesos.findIndex(p => { acumulado += p; return acumulado > objetivo; }));
      this.leidas.set(Math.max(0, this.activa()));
    }
    if (!audio.paused && this.activa() >= 0) {
      cancelAnimationFrame(this.desplazamiento);
      this.desplazamiento = requestAnimationFrame(() => {
        const palabra = this.elemento.nativeElement.querySelector('.actual');
        const caja = palabra?.getBoundingClientRect();
        const barra = this.elemento.nativeElement.querySelector('.barra-audio')?.getBoundingClientRect();
        if (caja && (caja.top < 80 || caja.bottom > (barra?.top ?? window.innerHeight - 100) - 16)) {
          palabra?.scrollIntoView({ block: 'center', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
        }
      });
    }
  }
  async alternar(): Promise<void> {
    const audio = this.reproductor()?.nativeElement;
    if (!audio || this.iniciando()) return;
    if (!audio.paused) { audio.pause(); return; }
    const v = this.version;
    this.iniciando.set(true);
    this.aviso.set('');
    if (audio.ended || this.finalizado()) audio.currentTime = 0;
    try { await audio.play(); }
    catch { if (v === this.version) this.aviso.set('No se ha podido iniciar el audio. Pulsa reproducir para intentarlo de nuevo.'); }
    finally { if (v === this.version) { this.iniciando.set(false); this.sincronizar(); } }
  }
  buscar(valor: number): void {
    const audio = this.reproductor()?.nativeElement;
    if (!audio || !Number.isFinite(valor) || !this.duracion()) return;
    audio.currentTime = Math.max(0, Math.min(this.duracion(), valor));
    this.sincronizar();
  }
  saltar(segundos: number): void { this.buscar(this.tiempo() + segundos); }
  reloj(segundos: number): string {
    const total = Math.max(0, Math.floor(segundos));
    return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
  }
  cambiarVelocidad(valor: number): void { this.velocidad.set(velocidadValida(valor)); this.sincronizar(); }
  consultar(valor: string): void {
    const palabra = valor.trim().replace(/^[^\p{L}]+|[^\p{L}]+$/gu, '');
    if (!palabra || palabra.length > 40 || palabra.split(/\s+/).length > 4) return;
    this.origenConsulta = document.activeElement as HTMLElement | null;
    this.reproductor()?.nativeElement.pause();
    this.reproduciendo.set(false);
    cancelAnimationFrame(this.desplazamiento);
    this.consultada.set(palabra);
  }
  cerrarConsulta(): void {
    this.consultada.set('');
    requestAnimationFrame(() => this.origenConsulta?.focus({ preventScroll: true }));
  }
  @HostListener('document:selectionchange') alSeleccionar(): void { this.programarSeleccion(450); }
  @HostListener('document:mouseup') alSoltar(): void { this.programarSeleccion(30); }
  private programarSeleccion(ms: number): void {
    clearTimeout(this.seleccion);
    this.seleccion = setTimeout(() => {
      if (this.consultada()) return;
      const sel = window.getSelection(), texto = this.texto()?.nativeElement;
      if (!sel || sel.isCollapsed || !sel.anchorNode || !sel.focusNode || !texto?.contains(sel.anchorNode) || !texto.contains(sel.focusNode)) return;
      const palabra = sel.toString().trim().replace(/^[^\p{L}]+|[^\p{L}]+$/gu, '');
      if (!palabra || palabra.length > 40 || palabra.split(/\s+/).length > 4) return;
      sel.removeAllRanges(); this.consultar(palabra);
    }, ms);
  }
  terminar(): void {
    this.reproduciendo.set(false);
    this.activa.set(this.palabras().length); this.leidas.set(this.palabras().length); this.finalizado.set(true);
  }
  errorAudio(): void { this.aviso.set('No se ha podido reproducir el audio. Vuelve a cargarlo.'); this.limpiarAudio(); }
  ngOnDestroy(): void { ++this.version; clearTimeout(this.seleccion); this.limpiarAudio(); }
}
