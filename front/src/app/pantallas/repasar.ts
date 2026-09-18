import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Icono } from '../compartido/icono';
import { EscucharYVer } from '../compartido/escuchar-y-ver';
import { Api, EvaluacionRepaso, Palabra, TarjetaRepaso, mensajeError, urlMotor } from '../nucleo/api';
import { Preferencias } from '../nucleo/preferencias';

/** Repaso v2 (D3.2): recuerdo activo con persistencia real, sin SRS
 *  todavía. `para_repasar()` sigue eligiendo las mismas hasta 5 tarjetas
 *  de siempre (D3.2 no toca ese algoritmo) — lo nuevo es la interacción
 *  (Mostrar respuesta → evaluar) y que la evaluación se guarda de verdad,
 *  identificada por `consulta_id` (nunca por la palabra ni la frase, que
 *  el servidor recalcula de su propio cuaderno). Ruta propia, como
 *  Pronunciar: una sesión de repaso pide la misma atención completa. */
@Component({
  selector: 'app-repasar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Icono],
  template: `
    <div class="pagina estrecha" data-seccion="nivel">
      <header class="cabecera-pagina">
        <span class="antetitulo">Tu nivel · Repasar</span>
        <h1>Repasar</h1>
      </header>

      @if (error()) { <div class="aviso error"><p>{{ error() }}</p></div> }

      @if (cargando()) {
        <div class="espera"><span class="giro"></span>Abriendo tu repaso…</div>
      } @else if (!error()) {
        @if (terminado()) {
          <section class="tarjeta resumen-final">
            <h2>Repasaste {{ total() }} {{ total() === 1 ? 'palabra' : 'palabras' }}</h2>
            <dl class="cifras-resumen">
              <div><dt>Sí</dt><dd>{{ resultados().si }}</dd></div>
              <div><dt>Dudé</dt><dd>{{ resultados().dude }}</dd></div>
              <div><dt>No</dt><dd>{{ resultados().no }}</dd></div>
            </dl>
            <a class="boton bloque" routerLink="/">Volver a Mi espacio</a>
          </section>
        } @else if (!tarjetas().length) {
          <div class="vacio tarjeta">
            <app-icono nombre="recargar" class="grande" />
            <h2>Todavía no tienes nada que repasar</h2>
            <p class="suave">Consulta alguna palabra mientras lees y aquí tendrás algo que recordar.</p>
            <a class="boton" routerLink="/leer">Ir a leer</a>
          </div>
        } @else if (actual(); as t) {
          <p class="progreso-repaso">{{ indice() + 1 }} de {{ tarjetas().length }}</p>
          <section class="tarjeta pila tarjeta-repaso">
            <blockquote class="en-libro" lang="en">{{ t.cita || t.oracion }}</blockquote>
            <strong class="palabra-repaso" lang="en">{{ t.palabra }}</strong>

            @if (!mostrarRespuesta()) {
              <button type="button" class="boton bloque" (click)="mostrar()">Mostrar respuesta</button>
            } @else {
              <div class="respuesta-repaso">
                <p class="sentido-repaso" lang="en">{{ t.sentido || 'Sin acepción guardada' }}</p>
                @if (cargandoAudio()) {
                  <span class="tenue pequeno"><span class="giro pequeno"></span> Buscando audio…</span>
                } @else if (audioDisponible()) {
                  <button type="button" class="boton pequeno secundario" (click)="escuchar()">
                    <app-icono nombre="altavoz" />Escuchar
                  </button>
                }
              </div>

              @if (errorGuardado()) {
                <div class="aviso error">
                  <p>{{ errorGuardado() }}</p>
                  <button type="button" class="boton pequeno" (click)="reintentar()">Reintentar</button>
                  @if (fallosSeguidos() >= 2) {
                    <button type="button" class="boton pequeno fantasma" (click)="saltar()">Saltar esta palabra</button>
                  }
                </div>
              }

              <div class="fila evaluacion-repaso">
                <p class="tenue">¿La recordabas?</p>
                <div class="fila botones-evaluacion">
                  <button type="button" class="boton secundario" [disabled]="guardando()" (click)="evaluar('no')">No</button>
                  <button type="button" class="boton secundario" [disabled]="guardando()" (click)="evaluar('dude')">Dudé</button>
                  <button type="button" class="boton secundario" [disabled]="guardando()" (click)="evaluar('si')">Sí</button>
                </div>
                @if (guardando()) { <span class="tenue pequeno"><span class="giro pequeno"></span> Guardando…</span> }
              </div>
            }
          </section>
        }
      }
    </div>
  `,
  styles: `
    .grande { font-size: 2.5rem; color: var(--acento-texto); margin-bottom: .5rem; }
    .progreso-repaso { color: var(--texto-suave); font-size: .9rem; font-weight: 650; margin: 0 0 .5rem; }
    .tarjeta-repaso { display: grid; gap: 1rem; }
    .palabra-repaso { font-size: 1.6rem; lang: en; }
    .respuesta-repaso { display: grid; gap: .6rem; justify-items: start; }
    .sentido-repaso { margin: 0; font-size: 1.15rem; color: var(--verde); font-weight: 600; }
    .evaluacion-repaso { flex-direction: column; align-items: stretch; gap: .5rem; }
    .botones-evaluacion { gap: .5rem; }
    .botones-evaluacion .boton { flex: 1 1 0; }
    .aviso.error { display: grid; gap: .5rem; justify-items: start; }
    .resumen-final { display: grid; gap: 1rem; text-align: center; justify-items: center; }
    .cifras-resumen { display: grid; grid-template-columns: repeat(3, 1fr); gap: .75rem; width: 100%; margin: 0; }
    .cifras-resumen div { display: grid; padding: .8rem; border-radius: var(--radio); background: var(--superficie-2); }
    .cifras-resumen dt { font-size: .85rem; color: var(--texto-suave); }
    .cifras-resumen dd { margin: 0; font-size: 1.6rem; font-weight: 750; }
    .giro.pequeno { width: 16px; height: 16px; }
  `,
})
export class Repasar implements OnInit {
  private readonly api = inject(Api);
  private readonly preferencias = inject(Preferencias);
  protected readonly eyv = new EscucharYVer();

  protected readonly cargando = signal(true);
  protected readonly error = signal('');
  protected readonly tarjetas = signal<TarjetaRepaso[]>([]);
  protected readonly indice = signal(0);
  protected readonly mostrarRespuesta = signal(false);
  protected readonly cargandoAudio = signal(false);
  protected readonly detalle = signal<Palabra | null>(null);
  protected readonly guardando = signal(false);
  protected readonly errorGuardado = signal('');
  protected readonly evaluacionElegida = signal<EvaluacionRepaso | null>(null);
  protected readonly fallosSeguidos = signal(0);
  protected readonly terminado = signal(false);
  protected readonly resultados = signal<Record<EvaluacionRepaso, number>>({ no: 0, dude: 0, si: 0 });

  protected readonly actual = computed<TarjetaRepaso | null>(() => this.tarjetas()[this.indice()] ?? null);
  protected readonly total = computed(() => {
    const r = this.resultados();
    return r.no + r.dude + r.si;
  });
  protected readonly audioDisponible = computed(() => {
    const p = this.detalle();
    return !!(p?.audio_uk || p?.audio_us);
  });

  async ngOnInit(): Promise<void> {
    try {
      const r = await firstValueFrom(this.api.repaso());
      this.tarjetas.set(r.palabras);
    } catch (e) {
      this.error.set(mensajeError(e));
    } finally {
      this.cargando.set(false);
    }
  }

  protected mostrar(): void {
    this.mostrarRespuesta.set(true);
    const t = this.actual();
    if (!t) return;
    this.cargandoAudio.set(true);
    // Solo `etapa: 'diccionario'`: nunca cuesta, nunca pide OpenAI, y no
    // vuelve a apuntar la consulta en el cuaderno (api.py: `registrar =
    // False` en esta etapa) — repasar una palabra no debe generar una
    // consulta fantasma en el propio cuaderno que se está repasando.
    this.api.palabra({ palabra: t.palabra, oracion: t.oracion, idioma: 'en', etapa: 'diccionario' })
      .subscribe({
        next: p => { this.detalle.set(p); this.cargandoAudio.set(false); },
        error: () => { this.cargandoAudio.set(false); }, // sin audio: no rompe nada, solo no se ofrece
      });
  }

  protected escuchar(): void {
    const p = this.detalle();
    if (!p) return;
    const uk = this.preferencias.acento() === 'rp';
    const audio = urlMotor(uk ? (p.audio_uk ?? p.audio_us) : (p.audio_us ?? p.audio_uk));
    this.eyv.escuchar({ audio, texto: audio ? undefined : p.palabra, voz: uk ? 'en-GB' : 'en-US', cortes: [] });
  }

  protected evaluar(ev: EvaluacionRepaso): void {
    const t = this.actual();
    if (!t || this.guardando()) return;
    this.evaluacionElegida.set(ev);
    this.guardando.set(true);
    this.errorGuardado.set('');
    this.api.evaluarRepaso(t.consulta_id, ev).subscribe({
      next: () => {
        this.guardando.set(false);
        this.fallosSeguidos.set(0);
        this.resultados.update(r => ({ ...r, [ev]: r[ev] + 1 }));
        this.siguiente();
      },
      error: e => {
        this.guardando.set(false);
        this.fallosSeguidos.update(n => n + 1);
        this.errorGuardado.set(mensajeError(e, 'No se pudo guardar tu repaso.'));
      },
    });
  }

  protected reintentar(): void {
    const ev = this.evaluacionElegida();
    if (ev) this.evaluar(ev);
  }

  /** Salida de emergencia: solo aparece tras dos intentos fallidos
   *  seguidos, para que una caída del backend no deje la sesión atascada.
   *  No cuenta como evaluación: no llama a la API, no suma al resumen. */
  protected saltar(): void {
    this.fallosSeguidos.set(0);
    this.errorGuardado.set('');
    this.evaluacionElegida.set(null);
    this.siguiente();
  }

  private siguiente(): void {
    this.evaluacionElegida.set(null);
    this.mostrarRespuesta.set(false);
    this.detalle.set(null);
    if (this.indice() + 1 >= this.tarjetas().length) { this.terminado.set(true); return; }
    this.indice.update(i => i + 1);
  }
}
