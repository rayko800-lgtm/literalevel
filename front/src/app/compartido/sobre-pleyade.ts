import { ChangeDetectionStrategy, Component, ElementRef, HostListener, afterNextRender, output, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Icono } from './icono';

/** «Sobre Pléyade»: se abre al pulsar el logo (Miguel, 26 sep). El texto es
 *  el de Miguel («Pleyade_Acerca_de_la_App.md»), tal cual; el guiño al Quijote y el vídeo de Eos
 *  se añadieron a petición suya el 8 oct para la demo. */
@Component({
  selector: 'app-sobre-pleyade',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Icono],
  template: `
    <div class="velo" (click)="cerrar.emit()"></div>
    <div class="caja" role="dialog" aria-modal="true" aria-labelledby="titulo-sobre">
      <div class="cielo">
        <img src="marca/logo-cosmos-600.webp" width="600" height="512" alt="Logo de Pléyade: un pegaso blanco sobre un libro abierto con alas, bajo una estrella dorada">
        <button #cerrarBoton class="boton-icono cerrar" type="button" (click)="cerrar.emit()" aria-label="Cerrar">
          <app-icono nombre="cerrar" />
        </button>
      </div>
      <div class="cuerpo">
        <span class="antetitulo">Sobre Pléyade</span>
        <h2 id="titulo-sobre">Pléyade</h2>
        <p class="lema">Leer para descubrir. Aprender para ir más lejos.</p>
        <p>Pléyade te ayuda a encontrar lecturas en inglés acordes con tu nivel y tus intereses, y te
          acompaña a comprenderlas y disfrutarlas.</p>

        <h3>¿Qué significa Pléyade?</h3>
        <p>Una <strong>pléyade</strong> es un grupo de personas célebres de una misma época, especialmente
          en las letras. La palabra tiene raíz griega y llegó al español a través del latín
          (<a href="https://dle.rae.es/pl%C3%A9yade" target="_blank" rel="noopener">Diccionario de la lengua española</a>).</p>
        <p>El nombre también remite a las <strong>Pléyades</strong>, un cúmulo de estrellas que forma parte
          del cielo de Tauro (<a href="https://science.nasa.gov/mission/hubble/science/explore-the-night-sky/hubble-messier-catalog/messier-45/" target="_blank" rel="noopener">NASA: las Pléyades</a>).</p>

        <h3>¿Por qué elegimos este nombre?</h3>
        <p>Porque reúne dos formas de explorar: la literatura y el cielo.</p>
        <p>Nos inspira el amor por la literatura en español y la posibilidad de descubrir otras voces en
          otra lengua. Para nosotros, Pléyade es un punto de encuentro entre libros, lectores y aprendizaje:
          un espacio donde cada historia puede abrir una nueva manera de mirar el mundo.</p>

        <h3>Un guiño a don Quijote</h3>
        <p>En la segunda parte del <em>Quijote</em> (1615), don Quijote y Sancho montan con los ojos vendados a
          <strong>Clavileño el Alígero</strong>, un caballo de madera que, según les cuentan, vuela por los aires.
          Al volver, Sancho jura que pasó junto a las <strong>siete cabrillas</strong>, que es el nombre popular
          de las Pléyades (<a href="https://dle.rae.es/cabrilla" target="_blank" rel="noopener">DLE: cabrilla</a>),
          y que se bajó a jugar con ellas:</p>
        <blockquote>«Y sucedió que íbamos por parte donde están las siete cabrillas; […] bonita y pasitamente me
          apeé de Clavileño, y me entretuve con las cabrillas, que son como unos alhelíes y como unas flores, casi
          tres cuartos de hora».
          <cite>Miguel de Cervantes, <em>Don Quijote de la Mancha</em>, II, cap. XLI
            (<a href="https://www.gutenberg.org/ebooks/2000" target="_blank" rel="noopener">texto completo</a>)</cite>
        </blockquote>
        <p>Por eso nuestro emblema es un caballo con alas: como Clavileño, un buen libro te lleva hasta las
          estrellas sin moverte de tu sitio.</p>

        <h3>¿Qué puedes hacer aquí?</h3>
        <ul>
          <li><strong>Encontrar tu próxima lectura:</strong> explorar libros de acuerdo con tu nivel de inglés
            y los temas que te interesan.</li>
          <li><strong>Comprender lo que lees:</strong> apoyarte en el vocabulario y en explicaciones del
            significado y la gramática de los textos.</li>
          <li><strong>Explorar la pronunciación:</strong> relacionar las palabras escritas con sus sonidos y
            acercarte al inglés también a través de la voz.</li>
        </ul>
        <p>Nuestro propósito es que puedas aprender mientras lees y elegir historias que te den ganas de continuar.</p>

        <h3>¿Qué representa nuestro emblema?</h3>
        <p>El <strong>libro abierto</strong> representa la literatura y el conocimiento. Sus páginas se
          transforman en <strong>alas</strong>, porque leer amplía lo que podemos imaginar.
          <strong>Pegaso</strong> expresa esa imaginación y la libertad de explorar; la <strong>estrella que
          lo ilumina</strong> representa la curiosidad y el descubrimiento.</p>
        <p>La ornamentación barroca es nuestro homenaje a la tradición literaria en español.</p>
        <p>En la versión astral del emblema aparece también <strong>Lira</strong>, vinculada con Orfeo en la
          tradición clásica. La incorporamos como un guiño a la poesía, la música y la voz
          (<a href="https://www.thelatinlibrary.com/hyginus/hyginus2.shtml" target="_blank" rel="noopener">Higino, <em>De astronomia</em>, II, VII</a>).</p>

        <p class="lema cierre">Tu próxima lectura empieza aquí.</p>

        <h3>Eos te explica Pléyade</h3>
        <!-- 4K tal como se renderizó (HEVC 10 bits); si el navegador no lo decodifica, la copia H.264 4K. -->
        <video class="video-eos" controls playsinline preload="metadata" [poster]="poster" width="3840" height="2160">
          <source [src]="videoBase + 'eos_pleyade_4k_hevc.mp4'" type='video/mp4; codecs="hvc1.2.4.L150.B0, mp4a.40.2"'>
          <source [src]="videoBase + 'eos_pleyade_4k_h264.mp4'" type="video/mp4">
        </video>
        <p class="nota-video">Vídeo en 4K (2:12). Para verlo a toda resolución, usa la pantalla completa.</p>

        <div class="fila pie-sobre">
          <a class="boton secundario pequeno" routerLink="/" (click)="cerrar.emit()"><app-icono nombre="casa" />Ir a Mi espacio</a>
          <button class="boton pequeno" type="button" (click)="cerrar.emit()">Cerrar</button>
        </div>
      </div>
    </div>
  `,
  styles: `
    :host { position: fixed; inset: 0; z-index: 90; display: grid; place-items: center; padding: 1rem; }
    .velo { position: absolute; inset: 0; background: var(--velo); animation: aparecer .2s ease; }
    .caja {
      position: relative; width: min(560px, 100%); max-height: calc(100dvh - 2rem); overflow: auto;
      background: var(--superficie); border-radius: var(--radio-lg); box-shadow: var(--sombra-alta);
      animation: subir .22s ease;
    }
    .cielo { position: relative; background: var(--marca-noche); display: grid; place-items: center; }
    .cielo img { display: block; width: min(360px, 90%); height: auto;
      -webkit-mask-image: radial-gradient(closest-side, #000 72%, transparent 100%);
      mask-image: radial-gradient(closest-side, #000 72%, transparent 100%); }
    .cerrar { position: absolute; top: .5rem; right: .5rem; color: var(--crema); }
    .cerrar:hover { background: rgba(255, 255, 255, .12); color: #fff; }
    .cuerpo { padding: 1.25rem clamp(1.1rem, 4vw, 1.75rem) 1.5rem; }
    .cuerpo h2 { margin-bottom: .75rem; }
    .cuerpo h3 { margin: 1.1rem 0 .35rem; color: var(--acento-texto); }
    .cuerpo p { color: var(--texto-suave); margin: 0 0 .6rem; }
    .cuerpo ul { color: var(--texto-suave); margin: 0 0 .6rem; padding-left: 1.2rem; display: grid; gap: .35rem; }
    .cuerpo .lema { font-family: var(--fuente-libro); font-size: 1.15rem; font-style: italic; color: var(--texto); }
    .cuerpo .cierre { margin-top: 1.2rem; }
    .antetitulo { color: var(--oro-rosa-texto); }
    .cuerpo blockquote { margin: .4rem 0 .8rem; padding: .5rem .9rem; border-left: 3px solid var(--acento-texto);
      font-family: var(--fuente-libro); font-style: italic; color: var(--texto); }
    .cuerpo blockquote cite { display: block; margin-top: .4rem; font-family: inherit; font-style: normal;
      font-size: .85rem; color: var(--texto-suave); }
    .video-eos { display: block; width: 100%; height: auto; aspect-ratio: 16 / 9; margin: .4rem 0 .3rem;
      background: #000; border-radius: var(--radio-lg); }
    .cuerpo .nota-video { font-size: .85rem; }
    .pie-sobre { justify-content: flex-end; margin-top: 1.5rem; }
    @keyframes aparecer { from { opacity: 0; } }
    @keyframes subir { from { opacity: 0; transform: translateY(12px); } }
  `,
})
export class SobrePleyade {
  readonly cerrar = output<void>();
  /** El vídeo pesa 268 MB: no cabe en GitHub/Vercel (100 MB por archivo) y se sirve desde Hugging Face. */
  protected readonly videoBase = 'https://huggingface.co/datasets/MikeMaki1763/pleyade-video/resolve/main/';
  protected readonly poster = 'marca/eos-video-poster.webp';
  private readonly cerrarBoton = viewChild<ElementRef<HTMLButtonElement>>('cerrarBoton');

  constructor() {
    afterNextRender(() => this.cerrarBoton()?.nativeElement.focus({ preventScroll: true }));
  }

  @HostListener('document:keydown.escape')
  protected alEscape(): void { this.cerrar.emit(); }
}
