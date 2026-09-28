import { ChangeDetectionStrategy, Component, ElementRef, OnDestroy, inject, signal, viewChild } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { Api, mensajeError } from '../nucleo/api';
import { ConexionLive } from '../compartido/gpt-live/conexion';
import { agregarDelta, GrupoLive } from '../compartido/gpt-live/transcripcion';

type Fase = 'lista' | 'preparando' | 'hablando' | 'cerrando' | 'cerrada' | 'incompleta' | 'error';

@Component({
  selector: 'app-conversar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="pagina estrecha">
      <header class="cabecera-pagina">
        <span class="antetitulo">Voz en vivo</span>
        <h1>Conversar con Pléyade</h1>
        <p>Habla con naturalidad. Puedes interrumpirla; escucharás su respuesta y verás las palabras de ambos.</p>
      </header>

      <section class="tarjeta conversacion" aria-label="Conversación">
        <p role="status" class="estado">
          @switch (fase()) {
            @case ('lista') { Lista para conversar. }
            @case ('preparando') { Conectando el micrófono… }
            @case ('hablando') { Te escucho. }
            @case ('cerrando') { Terminando la conversación… }
            @case ('cerrada') { Conversación finalizada. }
            @case ('incompleta') { Finalización incompleta. }
            @case ('error') { No se pudo iniciar la conversación. }
          }
        </p>
        @if (aviso()) { <p class="aviso" role="alert">{{ aviso() }}</p> }
        @if (fase() === 'lista' || fase() === 'cerrada' || fase() === 'incompleta' || fase() === 'error') {
          <button type="button" class="boton" (click)="empezar()">{{ fase() === 'lista' ? 'Empezar a hablar' : 'Nueva conversación' }}</button>
        } @else if (fase() === 'preparando' || fase() === 'hablando') {
          <button type="button" class="boton secundario" (click)="terminar()">Terminar</button>
        }
        <audio #salida controls playsinline [hidden]="fase() === 'lista' || fase() === 'error'" aria-label="Audio de Pléyade"></audio>
        @if (uso() !== null && fase() === 'cerrada') {
          <p class="tenue pequeno">Duración final: {{ uso() }} s@if (razon()) { · {{ razon() }} }</p>
        }
      </section>

      @if (grupos().length) {
        <section class="subtitulos" aria-label="Transcripción en vivo" aria-live="polite">
          @for (g of grupos(); track $index) {
            <div class="fragmento" [class.pleyade]="g.hablante === 'pleyade'">
              <div class="metadatos"><strong>{{ g.hablante === 'lector' ? 'Tú' : 'Pléyade' }}</strong>
                <span>{{ tiempo(g.inicio) }}–{{ tiempo(g.fin) }}</span></div>
              <p>{{ g.texto }}</p>
            </div>
          }
        </section>
      }
    </div>
  `,
  styles: `
    .conversacion { display: grid; gap: .85rem; justify-items: start; }
    .estado { margin: 0; font-weight: 600; }
    .aviso { margin: 0; color: var(--rojo, #b3261e); }
    audio { width: 100%; max-width: 480px; }
    .subtitulos { display: grid; gap: .75rem; margin-top: 1.25rem; }
    .fragmento { padding: .85rem 1rem; border-radius: 14px; background: var(--tarjeta, #fff); }
    .fragmento.pleyade { border-left: 3px solid var(--acento, #385dce); }
    .metadatos { display: flex; justify-content: space-between; gap: 1rem; color: var(--texto-suave, #48566f); font-size: .85rem; }
    .fragmento p { margin: .45rem 0 0; white-space: pre-wrap; overflow-wrap: anywhere; }
    .pequeno { font-size: .85rem; } .tenue { color: var(--texto-suave, #48566f); }
  `,
})
export class Conversar implements OnDestroy {
  private readonly api = inject(Api);
  private readonly salida = viewChild.required<ElementRef<HTMLAudioElement>>('salida');
  private conexion: ConexionLive | null = null;
  private limite = 0;
  protected readonly fase = signal<Fase>('lista');
  protected readonly aviso = signal('');
  protected readonly grupos = signal<GrupoLive[]>([]);
  protected readonly uso = signal<number | null>(null);
  protected readonly razon = signal<string | null>(null);

  protected tiempo(ms: number): string {
    const s = Math.floor(ms / 1000);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  }

  protected async empezar(): Promise<void> {
    this.grupos.set([]);
    this.aviso.set('');
    this.uso.set(null);
    this.razon.set(null);
    this.fase.set('preparando');
    const conexion = new ConexionLive(this.salida().nativeElement, {
      alEmpezar: () => {
        if (this.fase() !== 'cerrando') this.fase.set('hablando');
        // Límite de la interfaz para controlar el gasto de una conversación.
        this.limite = window.setTimeout(() => this.terminar(), 180_000);
      },
      alDelta: delta => this.grupos.update(g => agregarDelta(g, delta)),
      alCerrar: (uso, razon) => {
        window.clearTimeout(this.limite);
        this.uso.set(uso); this.razon.set(razon);
        this.fase.set('cerrada');
        this.conexion = null;
      },
      alIncompleto: motivo => {
        window.clearTimeout(this.limite);
        this.aviso.set(motivo);
        this.fase.set('incompleta');
        this.conexion = null;
      },
      alError: mensaje => this.aviso.set(mensaje),
    });
    this.conexion = conexion;
    try {
      await conexion.abrir(sdp => firstValueFrom(this.api.sesionGptLive(sdp)));
    } catch (e) {
      if (this.fase() !== 'incompleta') {
        this.aviso.set((e as { name?: string })?.name === 'NotAllowedError'
          ? 'Activa el permiso del micrófono en el navegador.' : mensajeError(e, e instanceof Error ? e.message : 'No se pudo conectar.'));
        this.fase.set('error');
      }
      this.conexion = null;
    }
  }

  protected terminar(): void {
    if (this.fase() === 'cerrando') return;
    window.clearTimeout(this.limite);
    this.fase.set('cerrando');
    this.conexion?.cerrar();
  }

  ngOnDestroy(): void {
    window.clearTimeout(this.limite);
    this.conexion?.cerrar();
  }
}
