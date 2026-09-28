import { ChangeDetectionStrategy, Component, ElementRef, Injectable, afterNextRender, effect, inject, input, signal, viewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, of } from 'rxjs';

/** El índice de los vídeos pregrabados de Eos (`front/public/eos/clips.json`,
 *  lo escribe `tools/eos_pronunciar/grabar_clips.py`): «ga/0283» → duración.
 *  Se baja una vez y solo cuando alguien abre Pronunciar. Si no está (build sin
 *  vídeos, red caída), no hay botón de Eos y no pasa nada más. */
@Injectable({ providedIn: 'root' })
export class EosClips {
  private readonly http = inject(HttpClient);
  private pedido = false;
  private readonly indice = signal<Record<string, { dur: number }> | null>(null);

  cargar(): void {
    if (this.pedido) return;
    this.pedido = true;
    this.http.get<Record<string, { dur: number }>>('eos/clips.json').pipe(catchError(() => of({})))
      .subscribe(i => this.indice.set(i));
  }

  /** El clip pregrabado de un mp3 de sonido de la API («/api/fonemas/0283.mp3?v=…»
   *  → «ga/0283»; «/api/fonemas/rp/0283.mp3» → «rp/0283»), si Eos lo tiene grabado. */
  clipDeAudio(audio: string | null | undefined): string | null {
    const m = /\/api\/fonemas\/(rp\/)?([0-9a-f_]{4,64})\.mp3(?:\?|$)/.exec(audio ?? '');
    if (!m) return null;
    const clip = `${m[1] ? 'rp' : 'ga'}/${m[2]}`;
    return this.indice()?.[clip] ? clip : null;
  }

  url(clip: string): string { return `eos/${clip}.mp4`; }
}

/** Eos, la cara que habla, en vídeo: pregrabado (los sonidos del AFI) o generado
 *  fuera para una frase nueva (`/api/eos/video/…`). Arranca sola al abrirse: quien
 *  la abre acaba de pulsar «Ver a Eos», así que el navegador lo permite. */
@Component({
  selector: 'app-eos',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <figure class="eos">
      @if (fallo()) {
        <p class="sin" role="status">Eos no ha podido cargar este vídeo.</p>
      } @else {
        <video #video [src]="src()" playsinline controls preload="metadata" poster="eos/reposo.webp"
               [attr.aria-label]="titulo()" (error)="fallo.set(true)"></video>
      }
      <figcaption>Eos · {{ titulo() }}</figcaption>
    </figure>
  `,
  styles: `
    :host { display: block; }
    .eos { margin: .5rem auto; display: grid; gap: .3rem; justify-items: center; width: min(360px, 100%); }
    video { display: block; width: 100%; aspect-ratio: 1 / 1; border-radius: var(--radio, 14px); background: #0b1840;
      box-shadow: 0 6px 24px rgba(11, 24, 64, .28); }
    figcaption { font-size: .85rem; color: var(--texto-suave, #667); text-align: center; }
    .sin { margin: 0; padding: 1rem; text-align: center; color: var(--texto-suave, #667); }
  `,
})
export class Eos {
  /** URL del mp4, ya resuelta (relativa al front o contra el motor). */
  readonly src = input.required<string>();
  readonly titulo = input('');
  protected readonly fallo = signal(false);
  private readonly video = viewChild<ElementRef<HTMLVideoElement>>('video');

  constructor() {
    afterNextRender(() => this.arrancar());
    // Otro clip en el mismo panel (otro sonido de la tabla): vuelve a arrancar.
    effect(() => { this.src(); this.fallo.set(false); this.arrancar(); });
  }

  private arrancar(): void {
    const v = this.video()?.nativeElement;
    if (!v) return;
    v.load();
    // Sin gesto reciente el navegador lo deja parado, con sus controles a la vista
    // (y en las pruebas, jsdom no implementa play()).
    const p = v.play();
    if (p && typeof p.catch === 'function') p.catch(() => {});
  }
}
