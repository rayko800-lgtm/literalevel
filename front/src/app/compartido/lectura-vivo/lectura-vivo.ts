import { ChangeDetectionStrategy, Component, DestroyRef, computed, inject, input, output, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { Api, mensajeError } from '../../nucleo/api';
import { Icono } from '../icono';
import { ConexionLectura } from './conexion';
import { PalabraTexto, Seguidor, trocearTexto } from './alinear';

/** D5 · lectura guiada en vivo (Miguel, 25 sep). Una hoja sobre el lector con
 *  el párrafo que toca: mientras el lector lee en voz alta, la transcripción en
 *  vivo de OpenAI marca cada palabra leída, la que toca ahora y las saltadas, y
 *  pasa sola al párrafo siguiente. Al terminar, un resumen: palabras leídas,
 *  saltadas y ritmo. No puntúa la pronunciación (para eso está «Corrígeme»):
 *  el modelo no da tiempos ni confianza por palabra. */
@Component({
  selector: 'app-lectura-vivo',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icono],
  template: `
    <div class="velo" (click)="terminar()"></div>
    <aside class="hoja-vivo" role="dialog" aria-modal="true" aria-label="Lectura en voz alta en vivo">
      <header>
        <strong>Lectura en voz alta</strong>
        <span class="estado" role="status">
          @switch (fase()) {
            @case ('preparando') { Preparando el micrófono… }
            @case ('escuchando') { <span class="punto"></span>Te escucho · {{ restante() }} }
            @case ('fin') { Resumen }
            @case ('error') { No se pudo }
          }
        </span>
        <button type="button" class="boton-icono" (click)="terminar()" aria-label="Terminar"><span aria-hidden="true">✕</span></button>
      </header>

      @if (fase() === 'error') {
        <p class="aviso">{{ error() }}</p>
      } @else if (fase() !== 'fin') {
        <p class="texto" lang="en">
          @for (w of palabras(); track $index) {
            <span [class]="w.estado" [class.actual]="$index === actual()">{{ w.texto }}</span>{{ ' ' }}
          }
        </p>
        <p class="tenue pequeno">Lee en voz alta a tu ritmo. Verde: leída; tachada: te la saltaste. Párrafo {{ parrafo() + 1 }} de {{ parrafos().length }}.</p>
        <div class="fila"><button type="button" class="boton" (click)="terminar()"><app-icono nombre="check" />Terminar</button></div>
      } @else {
        <ul class="resumen">
          <li><strong>{{ leidas() }}</strong> palabras leídas en {{ minutosTexto() }}@if (ppm()) { · {{ ppm() }} por minuto }</li>
          <li><strong>{{ saltadas().length }}</strong> saltadas@if (saltadas().length) {: <span lang="en">{{ saltadasTexto() }}</span>}</li>
        </ul>
        <p class="tenue pequeno">Para saber qué sonido corregir en una frase, llévala a Pronunciar.</p>
        <div class="fila"><button type="button" class="boton" (click)="cerrar.emit()">Volver al libro</button></div>
      }
    </aside>
  `,
  styles: `
    .velo { position: fixed; inset: 0; background: rgba(8, 12, 24, .35); z-index: 1000; }
    .hoja-vivo { position: fixed; left: 0; right: 0; bottom: 0; z-index: 1001; max-height: 70vh; overflow: auto;
      background: var(--tarjeta, #fff); color: var(--texto, #1b2233); border-radius: 18px 18px 0 0;
      padding: 14px 16px calc(16px + env(safe-area-inset-bottom)); box-shadow: 0 -8px 30px rgba(0,0,0,.18); }
    header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    header strong { flex: 1; }
    .estado { font-size: .85rem; color: var(--texto-suave, #48566f); display: inline-flex; align-items: center; gap: 6px; }
    .punto { width: 9px; height: 9px; border-radius: 50%; background: #d33; animation: latido 1.2s infinite; }
    @keyframes latido { 50% { opacity: .3; } }
    .boton-icono { min-width: 44px; min-height: 44px; border: 0; background: transparent; color: inherit; font-size: 1.1rem; cursor: pointer; }
    .texto { font-family: Georgia, 'Times New Roman', serif; font-size: 1.2rem; line-height: 1.7; margin: 0 0 10px; }
    .texto span { border-radius: 4px; padding: 0 1px; transition: background-color .2s; }
    .texto .leida { color: #1d7a45; }
    .texto .saltada { color: #b3261e; text-decoration: line-through; }
    .texto .actual { background: #fff1b8; color: #1b2233; }
    .fila { display: flex; justify-content: flex-end; margin-top: 8px; }
    .boton { font: inherit; display: inline-flex; align-items: center; gap: 6px; min-height: 48px; padding: 8px 16px;
      border-radius: 10px; border: 0; background: var(--acento, #2f5bea); color: #fff; cursor: pointer; }
    .resumen { margin: 0 0 8px; padding-left: 18px; line-height: 1.7; }
    .aviso { color: #b3261e; }
    .tenue { color: var(--texto-tenue, #647189); } .pequeno { font-size: .85rem; }
  `,
})
export class LecturaVivo {
  /** Los párrafos del capítulo (texto plano) y desde cuál empezar. */
  readonly parrafos = input.required<string[]>();
  readonly desde = input(0);
  readonly cerrar = output<void>();

  private readonly api = inject(Api);
  protected readonly fase = signal<'preparando' | 'escuchando' | 'fin' | 'error'>('preparando');
  protected readonly error = signal('');
  protected readonly parrafo = signal(0);
  protected readonly palabras = signal<PalabraTexto[]>([]);
  protected readonly actual = signal(0);
  private readonly todas: PalabraTexto[] = [];
  private seguidor: Seguidor | null = null;
  private conexion: ConexionLectura | null = null;
  private pendiente = '';
  private inicio = 0;
  private fin = 0;
  private limite = 0;
  private reloj = 0;
  protected readonly segundosRestantes = signal(0);
  protected readonly restante = computed(() => {
    const s = this.segundosRestantes();
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  });

  protected readonly leidas = signal(0);
  protected readonly saltadas = signal<string[]>([]);
  protected readonly saltadasTexto = computed(() => this.saltadas().slice(0, 12).join(', ') + (this.saltadas().length > 12 ? '…' : ''));
  private readonly segundos = signal(0);
  protected readonly minutosTexto = computed(() => {
    const s = this.segundos();
    return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${s % 60} s`;
  });
  protected readonly ppm = computed(() => (this.segundos() >= 15 ? Math.round(this.leidas() * 60 / this.segundos()) : 0));

  constructor() {
    inject(DestroyRef).onDestroy(() => this.soltar());
  }

  /** Arranca: llamar dentro del clic que abre la hoja (micrófono). */
  async empezar(): Promise<void> {
    this.parrafo.set(this.desde());
    this.cargarParrafo();
    this.conexion = new ConexionLectura({
      alOir: t => this.oir(t),
      alCerrarTramo: () => this.oir(' '),
      alError: m => this.fallo(m),
    });
    try {
      this.segundosRestantes.set(180);
      await this.conexion.microfono();
      const sesion = await firstValueFrom(this.api.lecturaVivo());
      await this.conexion.abrir(sesion.clave);
      this.fase.set('escuchando');
      this.inicio = Date.now();
      this.limite = this.inicio + sesion.minutos * 60_000;
      this.reloj = window.setInterval(() => {
        const queda = Math.max(0, Math.round((this.limite - Date.now()) / 1000));
        this.segundosRestantes.set(queda);
        if (!queda) this.terminar();
      }, 500);
    } catch (e) {
      const nombre = (e as { name?: string })?.name;
      this.fallo(nombre === 'NotAllowedError' ? 'Sin permiso para el micrófono. Actívalo en el navegador y vuelve a probar.'
        : mensajeError(e));
    }
  }

  private cargarParrafo(): void {
    let n = this.parrafo();
    const lista = this.parrafos();
    while (n < lista.length && !trocearTexto(lista[n]).length) n++;
    this.parrafo.set(n);
    const palabras = n < lista.length ? trocearTexto(lista[n]) : [];
    this.todas.push(...palabras);
    this.seguidor = new Seguidor(palabras);
    this.palabras.set([...palabras]);
    this.actual.set(0);
  }

  /** Los trozos llegan partidos por cualquier sitio («sup» + «plied»): solo
   *  se entregan las palabras ya cerradas por un espacio. */
  private oir(trozo: string): void {
    if (this.fase() !== 'escuchando' || !this.seguidor) return;
    this.pendiente += trozo;
    const corte = this.pendiente.lastIndexOf(' ');
    if (corte < 0) return;
    const listas = this.pendiente.slice(0, corte);
    this.pendiente = this.pendiente.slice(corte);
    this.seguidor.oir(listas);
    this.palabras.set([...this.seguidor.palabras]);
    this.actual.set(this.seguidor.puntero);
    if (this.seguidor.terminado) {
      if (this.parrafo() + 1 < this.parrafos().length) { this.parrafo.update(n => n + 1); this.cargarParrafo(); }
      else this.terminar();
    }
  }

  private fallo(mensaje: string): void {
    this.soltar();
    this.error.set(mensaje);
    this.fase.set('error');
  }

  terminar(): void {
    if (this.fase() === 'fin' || this.fase() === 'error') { this.cerrar.emit(); return; }
    if (this.fase() === 'preparando') { this.soltar(); this.cerrar.emit(); return; }
    if (this.pendiente.trim() && this.seguidor) this.seguidor.oir(this.pendiente);
    this.fin = Date.now();
    this.soltar();
    this.leidas.set(this.todas.filter(p => p.estado === 'leida').length);
    // Solo cuentan como saltadas las que quedaron atrás del puntero, no las
    // que no se llegaron a leer porque el lector paró.
    this.saltadas.set(this.todas.filter(p => p.estado === 'saltada').map(p => p.texto.replace(/[^\p{L}\p{N}'’-]/gu, '')));
    this.segundos.set(Math.round((this.fin - this.inicio) / 1000));
    this.fase.set('fin');
  }

  private soltar(): void {
    window.clearInterval(this.reloj);
    this.conexion?.cerrar();
    this.conexion = null;
  }
}
