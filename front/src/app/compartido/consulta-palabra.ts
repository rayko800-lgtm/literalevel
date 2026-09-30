import { ChangeDetectionStrategy, Component, ElementRef, HostListener, OnDestroy, afterNextRender, computed, effect, inject, input, output, signal, untracked, viewChild } from '@angular/core';
import { Params, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Api, Palabra, mensajeError } from '../nucleo/api';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';
import { Icono } from './icono';
import { ControlVelocidad } from './control-velocidad';
import { EscucharYVer } from './escuchar-y-ver';
import { urlMotor } from '../nucleo/api';

@Component({
  selector: 'app-consulta-palabra',
  imports: [Icono, ControlVelocidad, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="velo" (click)="cerrar.emit()"></div>
    <aside #hoja tabindex="-1" role="dialog" aria-modal="true" aria-label="Significado de la palabra" class="hoja">
      <header><div><span class="antetitulo">Consulta</span><h2 lang="en">{{ palabra()?.palabra || texto() }}</h2></div>
        <button type="button" class="boton-icono" aria-label="Cerrar consulta" (click)="cerrar.emit()"><app-icono nombre="cerrar" /></button></header>
      <div class="contenido-consulta">
        @if (buscando()) { <p role="status">Buscando en el diccionario…</p> }
        @if (error()) { <p class="aviso" role="alert">{{ error() }}</p> }
        @if (palabra(); as w) {
          @if (w.categoria) { <p class="tenue">{{ w.categoria }}</p> }
          <div class="pron">
            <button type="button" class="boton secundario pequeno" (click)="sonar(w.audio_us, w.palabra, 'en-US')"><app-icono nombre="altavoz" />US {{ w.ipa_us || '' }}</button>
            <button type="button" class="boton secundario pequeno" (click)="sonar(w.audio_uk, w.palabra, 'en-GB')"><app-icono nombre="altavoz" />UK {{ w.ipa_uk || '' }}</button>
            <app-control-velocidad [(valor)]="velocidad" />
          </div>
          @if (w.ipa_generada_por_ia) { <p class="tenue pequeno">IPA generada por IA.</p> }
          @if (w.traduccion) { <section><h3>En español</h3><p>{{ w.traduccion }}</p></section> }
          @if (explicando()) { <p role="status">Preparando la explicación de esta frase…</p> }
          @if (w.definicion_contextual) { <section><h3>Aquí significa @if (w.generado_por_ia) { <span class="chip ia">IA</span> }</h3><p>{{ w.definicion_contextual }}</p></section> }
          @if (w.acepciones_principales?.length && !w.definicion_contextual) {
            <section><h3>Diccionario · Wiktionary</h3><ul lang="en">@for (s of w.acepciones_principales; track s) { <li>{{ s }}</li> }</ul></section>
          } @else if (w.sentido) {
            <section><h3>En el diccionario · Wiktionary</h3><p lang="en">{{ w.sentido }}</p>
              @if (w.dudoso && !w.definicion_contextual) { <p class="aviso">Esta acepción puede no encajar con la frase.</p> }
            </section>
          } @else if (w.generado_por_ia && w.definicion_ia && w.definicion_ia !== w.definicion_contextual) {
            <section><h3>Definición generada por IA</h3><p>{{ w.definicion_ia }}</p></section>
          } @else if (!buscando() && !explicando() && !w.definicion_contextual) { <p>Esta palabra no está en el diccionario.</p> }
          @if (w.explicacion_gramatical) { <section><h3>Gramática</h3><p>{{ w.explicacion_gramatical }}</p></section> }
          @if (w.explicacion_adaptada) { <section><h3>Para tu nivel</h3><p>{{ w.explicacion_adaptada }}</p></section> }
          @if (w.ejemplo) { <section><h3>Ejemplo</h3><p lang="en">{{ w.ejemplo }}</p></section> }
          @if (w.cita || w.oracion) { <blockquote lang="en">{{ w.cita || w.oracion }}</blockquote> }
          @if (w.motivo_sin_explicacion && !w.definicion_contextual && !explicando()) { <p class="aviso">{{ w.motivo_sin_explicacion }}</p> }
          @for (a of w.avisos; track a) { @if (a !== w.motivo_sin_explicacion) { <p class="aviso">{{ a }}</p> } }
          @if (w.desde_cache) { <p class="tenue pequeno">Respuesta guardada: esta consulta no ha gastado usos.</p> }
        }
      </div>
      <footer>
        <a class="boton" routerLink="/pronunciar" [queryParams]="parametrosPronunciar()">
          <app-icono nombre="micro" />Leer esta frase en voz alta
        </a>
        <button type="button" class="boton secundario" (click)="cerrar.emit()">Volver a la lectura</button>
      </footer>
    </aside>
  `,
  styles: `
    .velo { position: fixed; inset: 0; z-index: 90; background: #0008; }
    .hoja { position: fixed; z-index: 91; left: 50%; bottom: 0; transform: translateX(-50%); width: min(640px, 100%);
      max-height: 85svh; display: flex; flex-direction: column; background: var(--superficie); color: var(--texto);
      border: 1px solid var(--borde-fuerte); border-radius: 1.25rem 1.25rem 0 0; box-shadow: 0 -8px 40px #0005; }
    header { display: flex; align-items: center; justify-content: space-between; padding: 1rem 1.25rem .5rem; }
    h2 { font-size: 1.5rem; margin: 0; }
    h3 { font-size: .8rem; color: var(--texto-suave); margin: 1rem 0 .35rem; }
    .contenido-consulta { overflow-y: auto; padding: .5rem 1.25rem 1rem; }
    .pron { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; padding-top: .25rem; }
    blockquote { border-left: 3px solid var(--acento); padding-left: .75rem; margin: 1rem 0; }
    footer { display: grid; gap: .5rem; padding: .75rem 1.25rem max(.75rem, env(safe-area-inset-bottom)); border-top: 1px solid var(--borde); }
    footer .boton { width: 100%; }
  `,
})
export class ConsultaPalabra implements OnDestroy {
  readonly texto = input.required<string>();
  readonly libro = input.required<string>();
  readonly capitulo = input.required<number>();
  readonly regreso = input<Params>({});
  readonly parametrosPronunciar = computed(() => ({
    ...this.regreso(), libro: this.libro(), cap: this.capitulo(),
    frase: this.palabra()?.cita || this.palabra()?.oracion || this.texto(),
  }));
  readonly cerrar = output<void>();
  readonly palabra = signal<Palabra | null>(null);
  readonly buscando = signal(false);
  readonly explicando = signal(false);
  readonly error = signal('');
  readonly velocidad = signal(1);
  private readonly api = inject(Api);
  private readonly prefs = inject(Preferencias);
  private readonly sesion = inject(Sesion);
  private readonly voz = new EscucharYVer();
  private readonly hoja = viewChild<ElementRef<HTMLElement>>('hoja');
  private turno = 0;
  constructor() {
    afterNextRender(() => this.hoja()?.nativeElement.focus({ preventScroll: true }));
    effect(() => {
      const texto = this.texto(), libro = this.libro(), cap = this.capitulo();
      untracked(() => void this.consultar(texto, libro, cap));
    });
    effect(() => this.voz.cambiarVelocidad(this.velocidad()));
  }
  private async consultar(texto: string, libro_id: string, capitulo: number): Promise<void> {
    const turno = ++this.turno;
    this.voz.parar();
    this.palabra.set(null); this.error.set(''); this.buscando.set(true); this.explicando.set(false);
    const cuerpo = { palabra: texto, libro_id, capitulo, idioma: this.prefs.idioma() };
    try {
      const rapida = await firstValueFrom(this.api.palabra({ ...cuerpo, etapa: 'diccionario' }));
      if (turno !== this.turno) return;
      this.palabra.set(rapida); this.buscando.set(false); this.explicando.set(rapida.explicacion_pendiente);
      const completa = await firstValueFrom(this.api.palabra({ ...cuerpo, etapa: 'completa' }));
      if (turno === this.turno) this.palabra.set(completa);
    } catch (e) { if (turno === this.turno) this.error.set(mensajeError(e)); }
    finally {
      if (turno === this.turno) { this.buscando.set(false); this.explicando.set(false); void this.sesion.refrescar(); }
    }
  }
  sonar(audio: string | null, texto: string, voz: 'en-US' | 'en-GB'): void {
    this.voz.escuchar({ audio: urlMotor(audio), texto, voz, cortes: [], velocidad: this.velocidad() });
  }
  @HostListener('document:keydown.escape') escape(): void { this.cerrar.emit(); }
  @HostListener('keydown.tab', ['$event']) tabular(evento: Event): void {
    const ev = evento as KeyboardEvent;
    const elementos = [...(this.hoja()?.nativeElement.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),a[href]') ?? [])];
    const primero = elementos[0], ultimo = elementos.at(-1);
    if (!primero || !ultimo) return;
    if (ev.shiftKey && (document.activeElement === primero || document.activeElement === this.hoja()?.nativeElement)) { ev.preventDefault(); ultimo.focus(); }
    else if (!ev.shiftKey && document.activeElement === ultimo) { ev.preventDefault(); primero.focus(); }
  }
  ngOnDestroy(): void { ++this.turno; this.voz.destruir(); }
}
