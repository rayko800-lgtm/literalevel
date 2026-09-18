import {
  ChangeDetectionStrategy, Component, DestroyRef, ElementRef, afterNextRender, computed, effect, inject, input, signal,
  viewChild,
} from '@angular/core';
import { Acento, urlCorteSonido, urlMotor } from '../../nucleo/api';
import { Icono } from '../icono';
import posesCompletas from './poses.ejemplo.json';
import { Linea, Velocidad, aVelocidad, cicloSonido, giroPara, lentoParaAudio, lineaPalabra, retrasoAudio } from './animacion';
import { Sonador } from './audio';
import { EscenaBoca } from './escena';
import { CatalogoPoses, DURACION_S, PoseSonido, familiaDe, poseDe, trocearIpa } from './poses';

/** La boca en 3D esquemático, girable con el dedo.
 *
 *  `sonido` es el símbolo IPA a enseñar ('' = reposo); `catalogo`, las poses
 *  (por defecto, el snapshot completo). Sin WebGL pinta el corte 2D que
 *  llegue en `svg2dUrl` (la ruta la pone quien integre: aquí no hay ninguna
 *  fija), y sin eso, una frase. Con `prefers-reduced-motion` no hay
 *  transiciones: salta a la pose. `conSelector` añade una fila de chips para
 *  elegir sonido, pensada para el prototipo y la demo. */
@Component({
  selector: 'app-boca3d',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icono],
  template: `
    @if (conSelector()) {
      <div class="chips" role="group" aria-label="Sonido">
        <button type="button" class="chip" [class.elegido]="!elegido()" [attr.aria-pressed]="!elegido()" (click)="elegir('')">reposo</button>
        @for (s of simbolos(); track s) {
          <button type="button" class="chip ipa" [class.elegido]="elegido() === s" [attr.aria-pressed]="elegido() === s"
                  (click)="elegir(s)">/{{ s }}/</button>
        }
      </div>
    }
    <div class="visor" [class.tres]="modo() === '3d'" [attr.data-modo]="modo()">
      <!-- Con el teclado: foco en el lienzo y flechas izquierda y derecha para girar
           (auditoría de 4e, ronda 2: antes solo se giraba con el puntero). -->
      <div #lienzo class="lienzo" [hidden]="modo() !== '3d'" role="img" tabindex="0"
           [attr.aria-label]="descripcion() + '. Flechas izquierda y derecha para girar.'"
           aria-keyshortcuts="ArrowLeft ArrowRight" (keydown)="teclaGiro($event)"
           [attr.data-acento-sonido]="acento()" [attr.data-acento-palabra]="acentoIpa() ?? acento()"></div>
      @if (modo() === '2d' && urlRespaldo(); as url) {
        <img class="respaldo" [src]="url" [alt]="descripcion()" />
      } @else if (modo() === '2d') {
        <p class="sin">Este navegador no puede dibujar la boca en 3D.</p>
      }
    </div>
    @if (modo() === '3d') {
      <div class="pie">
        <span class="botones">
          @if (pose() && elegido()) {
            @if (urlAudioSonido() && conEscuchar()) {
              <button type="button" class="boton principal" (click)="escucharYVer()"><app-icono nombre="altavoz" />Escuchar y ver</button>
            } @else {
              <button type="button" class="boton" (click)="verMovimiento()" title="Reproducir el sonido" aria-label="Reproducir el sonido"><app-icono nombre="play" /></button>
            }
          }
          @if (segmentos().length) {
            <button type="button" class="boton" [class.principal]="!!urlAudioPalabra() && conEscuchar()" (click)="verPalabra()">
              <app-icono [nombre]="urlAudioPalabra() && conEscuchar() ? 'altavoz' : 'play'" />{{ urlAudioPalabra() && conEscuchar() ? 'Escuchar y ver' : 'Palabra' }}
              <span class="ipa">/{{ textoIpa() }}/</span></button>
          }
          <button type="button" class="boton" [attr.aria-pressed]="giroLibre()" [class.activo]="giroLibre()"
                  (click)="alternarGiro()" title="Giro libre" aria-label="Giro libre"><app-icono nombre="girar" /></button>
          <button type="button" class="boton" (click)="restablecer()" title="Restablecer vista de lado" aria-label="Restablecer vista de lado"><app-icono nombre="recargar" /></button>
        </span>
      </div>
    }
    @if (leyenda() && pose()?.leyenda; as l) {
      <p class="leyenda"><strong class="ipa">{{ elegido() ? '/' + elegido() + '/' : 'reposo' }}</strong> · {{ l }}</p>
    }
    @if (aviso(); as a) {
      <p class="leyenda aviso" role="status">{{ a }}</p>
    }
  `,
  styles: `
    :host { display: block; min-width: 0; margin-top: 12px; }
    /* Pastillas y controles con los mínimos de investigacion/una_mano.md: se tocan
       seguidos (un sonido tras otro), así que 44-48 px y 8 px de hueco. */
    .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
    .chip { font: inherit; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--borde, #d6deeb);
      background: var(--tarjeta, transparent); color: inherit; cursor: pointer; min-height: 44px; }
    .chip.elegido { background: var(--acento, #2f5bea); color: #fff; border-color: var(--acento, #2f5bea); }
    .ipa { font-family: 'Charis SIL', 'Doulos SIL', 'DejaVu Sans', 'Segoe UI', sans-serif; }
    .visor { position: relative; width: 100%; overflow: hidden; min-height: 220px; }
    /* --boca3d-alto la pone la pantalla que tenga barras encima (Pronunciar a 390 px). */
    .lienzo { width: 100%; height: var(--boca3d-alto, 420px); max-height: 65vh; min-height: 220px; }
    .lienzo[hidden] { display: none; }
    .respaldo { display: block; width: 100%; height: 360px; object-fit: contain; }
    .sin { margin: 0; padding: 24px 16px; color: var(--texto-suave, #48566f); text-align: center; }
    .pie { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;
      margin-top: 8px; font-size: .9em; color: var(--texto-tenue, #647189); }
    .botones { display: flex; flex-wrap: wrap; gap: 8px; }
    .boton { font: inherit; display: inline-flex; align-items: center; justify-content: center; gap: 6px;
      padding: 8px; border-radius: 6px; border: 1px solid var(--borde, #d6deeb);
      background: transparent; color: inherit; cursor: pointer; min-height: 48px; min-width: 48px; }
    .boton.activo { background: var(--acento-suave, #e6ecff); border-color: var(--acento, #2f5bea);
      color: var(--acento-texto, #2449c9); }
    .boton.principal { background: var(--acento, #2f5bea); border-color: var(--acento, #2f5bea); color: #fff; padding: 8px 14px; }
    .leyenda { margin: 8px 0 0; color: var(--texto-suave, #48566f); }
    .leyenda.aviso { font-size: .9em; color: var(--texto-tenue, #647189); }
  `,
})
export class Boca3d {
  /** Símbolo IPA a enseñar, tal como lo da la API en su inventario (el mismo
   *  que va a `urlCorteSonido`); vacío es el reposo. */
  readonly sonido = input<string>('');
  /** El mismo acento que usa el front para los SVG (`Fonema.acento` en la
   *  corrección, el elegido en la tabla del AFI). */
  readonly acento = input<Acento>('ga');
  /** Snapshot reproducible del mismo inventario que sirve el corte 2D. */
  readonly catalogo = input<CatalogoPoses>(posesCompletas as unknown as CatalogoPoses);
  /** El corte 2D para cuando no hay WebGL. Por defecto, el SVG de la API del
   *  sonido elegido (`/api/articulacion/{acento}/{símbolo}.svg`, quieto si se
   *  pide reducir el movimiento); `''` lo apaga y deja solo una frase. */
  readonly svg2dUrl = input<string | null>(null);
  readonly leyenda = input<boolean>(true);
  readonly conSelector = input<boolean>(false);
  /** Una transcripción IPA: «Ver la palabra» la reproduce entera. */
  readonly ipa = input<string>('');
  readonly acentoIpa = input<Acento | null>(null);
  /** El mp3 del sonido, tal como lo da `/api/fonemas` en `audio` (relativo o
   *  absoluto): aparece «Escuchar y ver», que arranca audio y ciclo a la vez. */
  readonly audioSonido = input<string | null>(null);
  /** El mp3 de la palabra (`audio` del detalle de `/api/voz`, o `audio_us` /
   *  `audio_uk` de `/api/palabra`): «Escuchar y ver /ipa/» reproduce la palabra
   *  con la boca ajustada a la duración real del audio. */
  readonly audioPalabra = input<string | null>(null);
  /** Con `false` no se enseñan los botones «Escuchar y ver» (la pantalla
   *  pone el suyo y llama a `escucharYVer()` / `verPalabra()`); el play del
   *  sonido queda como siempre, pero ese play NO toca el audio: el audio solo
   *  suena por los métodos. `verPalabra()` sí lo toca si hay `audioPalabra`. */
  readonly conEscuchar = input<boolean>(true);
  /** Al cambiar `sonido`, reproducir su ciclo reposo → sonido → reposo. */
  readonly autoReproducir = input<boolean>(true);
  /** Velocidad de la boca y del audio: 1 (normal), 0,5 o 0,25. La línea de
   *  tiempo (ciclo y palabra) se estira y el audio suena con `playbackRate`
   *  igual y `preservesPitch`; si el navegador no sabe ralentizar sin
   *  cambiar el tono, el audio va a 1× y la boca despacio, y se avisa en
   *  `aviso` (Miguel, 14 sep: «va muy rápida; que se pueda ver cada movimiento»). */
  readonly velocidad = input<Velocidad>(1);
  /** La mejilla translúcida del lado de la cámara. Es lo que más cuesta
   *  pintar sin GPU (medido en Chrome headless): se puede apagar. */
  readonly mejilla = input<boolean>(true);

  /** `2d` es «sin WebGL»: se pinta el corte 2D si hay URL y, si no, una frase. */
  readonly modo = signal<'cargando' | '3d' | '2d'>('cargando');
  /** Un aviso bajo la leyenda (el audio no se pudo ralentizar), o vacío. */
  readonly aviso = signal('');
  /** El lienzo captura también los gestos verticales (sin scroll sobre la boca). */
  readonly giroLibre = signal(false);
  private readonly elegidoPorChip = signal<string | null>(null);
  readonly elegido = computed(() => this.elegidoPorChip() ?? this.sonido());
  readonly simbolos = computed(() => Object.keys(this.catalogo().sonidos));
  readonly pose = computed<PoseSonido | null>(() => poseDe(this.catalogo(), this.elegido(), this.acento()));
  private readonly troceada = computed(() => trocearIpa(this.ipa(), this.catalogo(), this.acentoIpa() ?? this.acento()));
  readonly segmentos = computed(() => this.troceada().segmentos);
  readonly textoIpa = computed(() => this.troceada().texto);
  readonly urlAudioSonido = computed(() => urlMotor(this.audioSonido()));
  readonly urlAudioPalabra = computed(() => urlMotor(this.audioPalabra()));
  readonly urlRespaldo = computed(() => {
    const dada = this.svg2dUrl();
    if (dada !== null) return dada || null;
    const s = this.elegido();
    if (!s) return null;
    let quieto = false;
    try { quieto = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch { /* sin matchMedia */ }
    return urlCorteSonido(s, this.acento(), quieto);
  });
  readonly descripcion = computed(() => {
    const p = this.pose();
    const s = this.elegido();
    if (!p) return `No sé cómo se articula /${s}/`;
    return s ? `La boca diciendo /${s}/: ${p.leyenda}` : 'La boca en reposo';
  });

  private readonly lienzo = viewChild.required<ElementRef<HTMLDivElement>>('lienzo');
  private escena: EscenaBoca | null = null;
  private readonly sonador = new Sonador();
  /** Número de la última petición de audio: si llega otra antes de que la
   *  primera decodifique, la primera no arranca nada. */
  private peticion = 0;

  constructor() {
    const destruir = inject(DestroyRef);
    afterNextRender(() => {
      if (!EscenaBoca.hayWebGL()) {
        this.modo.set('2d');
        return;
      }
      try {
        const host = this.lienzo().nativeElement;
        const estilo = getComputedStyle(host);
        const color = (v: string) => estilo.getPropertyValue(v).trim() || undefined;
        this.escena = new EscenaBoca(host, {
          colores: { lengua: color('--ll-lengua') as string | undefined },
          reducirMovimiento: matchMedia('(prefers-reduced-motion: reduce)').matches,
          mejilla: this.mejilla(),
          lenguaGlb: new URL('boca3d/lengua.glb', document.baseURI).href,
          caraGlb: new URL('boca3d/cara.glb', document.baseURI).href,
          alPerderContexto: () => this.perdioContexto(),
        });
        this.modo.set('3d');
        const p = this.pose();
        if (p) {
          this.escena.vistaParaFamilia(familiaDe(p));
          this.escena.irA(p, 0);
        }
      } catch {
        this.modo.set('2d');
      }
    });
    effect(() => { this.escena?.mostrarMejilla(this.mejilla()); });
    effect(() => {
      const p = this.pose();
      const escena = this.escena;
      if (!p || !escena) return;
      // D4.2: cada sonido pone primero la vista pedagógica de su familia
      // (sin interacción), y luego la pose/animación como hasta ahora.
      escena.vistaParaFamilia(familiaDe(p));
      if (this.autoReproducir() && this.elegido()) escena.reproducir(this.lenta(cicloSonido(p, this.catalogo())), { giro: giroPara(p) });
      else escena.irA(p, Math.max(0.45, (DURACION_S[p.movimiento] ?? 0.3) * 1.6) / this.velocidad());
    });
    destruir.onDestroy(() => {
      // Invalida la petición en curso: un mp3 que termina de prepararse después de
      // cerrar ya no arranca (sonaba con el visor desmontado, auditoría de 4e).
      this.peticion++;
      this.sonador.destruir();
      this.escena?.destruir();
      this.escena = null;
    });
  }

  /** La línea a la velocidad elegida. */
  private lenta(l: Linea): Linea {
    return aVelocidad(l, this.velocidad());
  }

  /** Reposo → sonido → reposo, una vez. */
  verMovimiento(): void {
    const p = this.pose();
    if (p && this.escena) this.escena.reproducir(this.lenta(cicloSonido(p, this.catalogo())), { giro: giroPara(p) });
  }

  /** El sonido: su audio y su ciclo arrancan en el mismo instante, con el
   *  audio desplazado para que suene cuando la boca llega a la pose. Si el
   *  audio no se puede preparar, el ciclo va solo. */
  escucharYVer(): void {
    const p = this.pose();
    if (!p || !this.escena) return;
    const url = this.urlAudioSonido();
    if (!url) { this.verMovimiento(); return; }
    void this.conAudio(url, () => cicloSonido(p, this.catalogo()), { giro: giroPara(p) });
  }

  /** La palabra de `ipa` entera: con audio, la línea se escala a la duración
   *  real del audio (menos su silencio inicial) para que las bocas caigan en
   *  sus sílabas; sin audio, con las duraciones del catálogo. */
  verPalabra(): void {
    const segs = this.segmentos();
    if (!segs.length || !this.escena) return;
    const url = this.urlAudioPalabra();
    if (!url) { this.escena.reproducir(this.lenta(lineaPalabra(segs, this.catalogo()))); return; }
    void this.conAudio(url, listo => lineaPalabra(segs, this.catalogo(),
      listo.duracion > 0 ? lentoParaAudio(segs, this.catalogo(), listo.duracion, listo.silencio) : undefined));
  }

  private async conAudio(url: string, linea: (listo: { duracion: number; silencio: number }) => Linea,
                         opciones: { giro?: number } = {}): Promise<void> {
    this.sonador.despertar();                    // dentro del clic, por iOS
    this.sonador.parar();
    const numero = ++this.peticion;
    const listo = await this.sonador.preparar(url);
    if (numero !== this.peticion || !this.escena) return;
    this.aviso.set('');
    if (!listo) {
      this.escena.reproducir(this.lenta(linea({ duracion: 0, silencio: 0 })), opciones);
      return;
    }
    // La línea se ajusta al audio a 1× y después se estira; el audio suena a
    // la misma velocidad, así que el desfase del silencio inicial se estira igual.
    const v = this.velocidad();
    const l = this.lenta(linea(listo));
    this.escena.reproducir(l, opciones);
    // Con la boca despacio el audio puede no poder ralentizarse (sin
    // preservesPitch): suena a 1× y su silencio dura lo de siempre.
    const r = listo.tocar(retrasoAudio(l.sonidoEn, listo.silencio, v), v);
    if (r.velocidad !== v) {
      r.parar();
      listo.tocar(retrasoAudio(l.sonidoEn, listo.silencio, 1), 1);
      this.aviso.set('Este navegador no puede ralentizar el audio sin cambiar el tono: el audio suena a velocidad normal y la boca va despacio.');
    }
  }

  elegir(simbolo: string): void {
    this.sonador.parar();
    this.elegidoPorChip.set(simbolo);
  }

  restablecer(): void {
    this.escena?.restablecerVista();
  }

  alternarGiro(): void {
    this.giroLibre.update(v => !v);
    this.escena?.girarLibre(this.giroLibre());
  }

  /** Flechas izquierda y derecha con el foco en el lienzo: un cuarto de vuelta
   *  entre cuatro pulsaciones (22,5° cada una). */
  teclaGiro(ev: KeyboardEvent): void {
    if (ev.key !== 'ArrowLeft' && ev.key !== 'ArrowRight') return;
    if (!this.escena) return;
    ev.preventDefault();
    this.escena.girar((ev.key === 'ArrowLeft' ? -1 : 1) * Math.PI / 8);
  }

  /** Se perdió el contexto WebGL: sin escena, audio parado y el corte 2D en su sitio. */
  perdioContexto(): void {
    this.peticion++;
    this.sonador.parar();
    this.escena?.destruir();
    this.escena = null;
    this.modo.set('2d');
  }
}
