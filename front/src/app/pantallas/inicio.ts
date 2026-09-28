import { ChangeDetectionStrategy, Component, computed, effect, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Bienvenida } from '../compartido/bienvenida';
import { Icono } from '../compartido/icono';
import { Api, PalabraFallada, Progreso, mensajeError } from '../nucleo/api';
import { cefr, miles, num } from '../nucleo/formato';
import { Sesion } from '../nucleo/sesion';

/** La puerta: enseñar el producto antes de pedir nada (PLAN_3_OCTUBRE.md §3.1,
 *  enganche.md §3) para quien no tiene nada que ver todavía — y «Mi espacio»
 *  (D3.1, Miguel: "no crear /espacio, Inicio evoluciona") para quien ya lee,
 *  consulta o se ha medido. Una sola pantalla, dos estados: nunca dos
 *  dashboards casi iguales compitiendo por atención. */
@Component({
  selector: 'app-inicio',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Icono, Bienvenida],
  template: `
    <!-- Solo aquí: la bienvenida nunca sale encima de un enlace directo a un libro o al lector.
         Ni encima de Ajustes: quien pulsa «Entrar» en el paso 0 y entra no debe encontrarse la
         bienvenida «con cuenta» tapando el formulario en ese mismo momento. -->
    @if (bienvenida() && !ajustesAbiertos() && sesionConocida()) { <app-bienvenida /> }
    <div class="pagina">
      @if (modoEspacio()) {
        <header class="cabecera-espacio cielo">
          <img class="icono-espacio" src="marca/icono-96.webp" width="48" height="48" alt="">
          <div>
            <span class="antetitulo">Mi espacio</span>
            <h1>Lo que ya llevas hecho</h1>
          </div>
        </header>

        @if (seguir(); as s) {
          <a class="tarjeta seguir" [routerLink]="['/leer', s.id, s.capitulo]">
            <div class="seguir-cab">
              <span class="antetitulo">Donde lo dejaste</span>
              <span class="chip">Capítulo {{ s.capitulo + 1 }} de {{ s.capitulos }}</span>
            </div>
            <h2>{{ s.titulo }}</h2>
            <p class="suave">{{ s.autor }}@if (s.titulo_capitulo) { · {{ s.titulo_capitulo }} }</p>
            @if (s.extracto) { <blockquote class="en-libro">{{ s.extracto }}</blockquote> }
            <div class="avance" role="progressbar" [attr.aria-valuenow]="Math.round(s.avance * 100)" aria-valuemin="0" aria-valuemax="100">
              <i [style.width.%]="s.avance * 100"></i>
            </div>
            <!-- «Avance por capítulos», no «% leído» (Miguel, D3.3): avance
                 es capítulo/(capítulos-1), progreso estructural, no una
                 medida real de texto leído — el capítulo de al lado ya lo
                 deja claro, esto solo lo remacha en el propio número. -->
            <span class="fila seguir-pie"><span class="tenue pequeno">Avance por capítulos: {{ Math.round(s.avance * 100) }}%</span>
              <span class="enlace">Seguir leyendo <app-icono nombre="flecha" /></span></span>
          </a>
        }

        @if (inicio(); as i) {
          <section class="rejilla-espacio">
            <a class="tarjeta-mini" routerLink="/encontrar" [queryParams]="{ vista: 'mios' }">
              <span class="icono-mini"><app-icono nombre="libro" /></span>
              @if (i.libros > 0) {
                <strong>{{ miles(i.libros) }}</strong><span>{{ i.libros === 1 ? 'libro' : 'libros' }}</span>
              } @else {
                <strong>Mis libros</strong><span class="tenue">Encuentra tu primera lectura</span>
              }
            </a>
            <a class="tarjeta-mini" routerLink="/palabras">
              <span class="icono-mini"><app-icono nombre="palabras" /></span>
              @if (i.cuaderno.consultas > 0) {
                <strong>{{ miles(i.cuaderno.palabras) }}</strong><span>{{ i.cuaderno.palabras === 1 ? 'palabra' : 'palabras' }}</span>
              } @else {
                <strong>Mis palabras</strong><span class="tenue">Consulta palabras mientras lees</span>
              }
            </a>
            <!-- Directo a la sesión (D3.2): el CTA de Mi espacio no debe
                 obligar a encontrarla dentro de /palabras. La propia
                 pantalla de repaso resuelve su empty state si no hay nada
                 que repasar todavía. -->
            <a class="tarjeta-mini" routerLink="/repasar">
              <span class="icono-mini"><app-icono nombre="recargar" /></span>
              @if (i.cuaderno.consultas > 0) {
                <strong>Repasar</strong><span class="tenue">Recuerda lo que has consultado</span>
              } @else {
                <strong>Repasar</strong><span class="tenue">Aparece en cuanto consultes algo</span>
              }
            </a>
            <a class="tarjeta-mini" routerLink="/palabras">
              <span class="icono-mini"><app-icono nombre="micro" /></span>
              @if (falladas().length > 0) {
                <strong>{{ falladas().length }}</strong><span>{{ falladas().length === 1 ? 'para practicar' : 'para practicar' }}</span>
              } @else {
                <strong>Pronunciación</strong><span class="tenue">Prueba Pronunciar</span>
              }
            </a>
          </section>
        }

        <!-- D3.3: agregados de /api/progreso, nunca anotaciones completas.
             Una sola tarjeta con las dos gráficas — si la llamada falla,
             solo esta tarjeta lo dice, el resto de Mi espacio sigue igual. -->
        <section class="tarjeta mi-progreso">
          <h2>Mi progreso</h2>
          @if (progreso(); as p) {
            <div class="bloque-progreso">
              <h3>Palabras consultadas · 14 días</h3>
              @if (totalConsultas14() === 0) {
                <p class="tenue pequeno">Todavía no has consultado palabras.</p>
              } @else {
                <div class="barras-dias" aria-hidden="true">
                  @for (d of p.palabras_por_dia; track d.fecha) {
                    <span class="barra-dia" [style.height.%]="alturaBarra(d.consultas)"></span>
                  }
                </div>
                <!-- El dato real, para quien no puede ver la altura/color de la barra. -->
                <ul class="oculto-visual">
                  @for (d of p.palabras_por_dia; track d.fecha) {
                    <li>{{ d.fecha }}: {{ d.consultas }} {{ d.consultas === 1 ? 'consulta' : 'consultas' }}</li>
                  }
                </ul>
              }
            </div>
            <div class="bloque-progreso">
              @if (p.repasos.total === 0) {
                <h3>Resultados de repaso</h3>
                <p class="tenue pequeno">Haz tu primer repaso para empezar a ver tus resultados.</p>
                <a class="boton pequeno secundario" routerLink="/repasar">Repasar</a>
              } @else {
                <h3>Resultados de tus últimos {{ p.repasos.total }} {{ p.repasos.total === 1 ? 'repaso' : 'repasos' }}</h3>
                <div class="barra-segmentada" aria-hidden="true">
                  <i class="seg si" [style.width.%]="pct(p.repasos.si, p.repasos.total)"></i>
                  <i class="seg dude" [style.width.%]="pct(p.repasos.dude, p.repasos.total)"></i>
                  <i class="seg no" [style.width.%]="pct(p.repasos.no, p.repasos.total)"></i>
                </div>
                <ul class="leyenda-repasos">
                  <li><span class="punto si"></span>Sí <strong>{{ p.repasos.si }}</strong></li>
                  <li><span class="punto dude"></span>Dudé <strong>{{ p.repasos.dude }}</strong></li>
                  <li><span class="punto no"></span>No <strong>{{ p.repasos.no }}</strong></li>
                </ul>
              }
            </div>
          } @else if (progresoError()) {
            <p class="tenue pequeno">{{ progresoError() }}</p>
          } @else {
            <div class="esqueleto-progreso" aria-hidden="true"></div>
          }
        </section>

        <a class="tarjeta-mini ancho" routerLink="/nivel">
          <span class="icono-mini"><app-icono nombre="diana" /></span>
          @if (perfil(); as p) {
            <div><strong>{{ cefr(p.nivel) }}</strong><span class="tenue"> · {{ num(p.nivel) }} de 2 — vuelve a medirte cuando quieras</span></div>
          } @else {
            <div><strong>Mi nivel</strong><span class="tenue"> — todavía no lo has medido</span></div>
          }
          <span class="enlace">{{ perfil() ? 'Ver' : 'Medir mi nivel' }} <app-icono nombre="flecha" /></span>
        </a>
        <a class="tarjeta-mini ancho" routerLink="/conversar">
          <span class="icono-mini"><app-icono nombre="micro" /></span>
          <div><strong>Conversar con Pléyade</strong><span class="tenue">Habla y escucha una respuesta en tiempo real</span></div>
          <span class="enlace">Empezar <app-icono nombre="flecha" /></span>
        </a>
      } @else {
        <section class="heroe cielo">
          <div class="texto-heroe">
            <img class="logo-heroe" src="marca/logo-cosmos-600.webp"
                 srcset="marca/logo-cosmos-600.webp 600w, marca/logo-cosmos-1200.webp 1200w"
                 sizes="(max-width: 640px) 240px, 320px" width="600" height="512" alt="Pléyade">
            <span class="antetitulo">Lee en inglés a tu medida</span>
            <h1>Libros de verdad en inglés, <span class="realce">sin perderte</span>.</h1>
            <p class="entradilla">Pléyade mide lo difícil que es cada capítulo y te explica cualquier palabra
              en su frase, sin salir del libro.</p>
            <div class="fila acciones-heroe">
              <a class="boton" [routerLink]="['/leer', 'PG11', 'auto']"><app-icono nombre="libro" />Empezar a leer</a>
              <a class="boton secundario" routerLink="/encontrar"><app-icono nombre="lupa" />Buscar un libro</a>
            </div>
          </div>

          <figure class="demo" aria-label="Ejemplo: mantener presionada una palabra del libro para ver qué significa en su frase">
            <div class="demo-libro en-libro">
              <span class="demo-cap">Alice's Adventures in Wonderland · capítulo I</span>
              <p>Alice was beginning to get very tired of sitting by her sister on the
                <mark>bank</mark>, and of having nothing to do: once or twice she had peeped into the book her sister was reading…</p>
            </div>
            <div class="demo-ficha">
              <div class="fila demo-cab"><strong>bank</strong><span class="tenue">/bæŋk/</span><span class="chip verde">aquí</span></div>
              <p><strong>Aquí significa:</strong> la orilla del río, no un banco de dinero.</p>
              <p class="tenue pequeno">«On the bank» = sentada en la orilla, junto a su hermana.</p>
            </div>
          </figure>
        </section>

        <section class="puertas" aria-labelledby="titulo-puertas">
          <h2 id="titulo-puertas" class="oculto-visual">¿Por dónde empiezas?</h2>
          <a class="puerta" [routerLink]="['/leer', 'PG11', 'auto']">
            <span class="icono-puerta verde"><app-icono nombre="ojo" /></span>
            <h3>Solo quiero mirar</h3>
            <p>Abre <em>Alicia en el país de las maravillas</em> y toca cualquier palabra. Sin formulario y sin cuenta.</p>
            <span class="enlace">Abrir un libro <app-icono nombre="flecha" /></span>
          </a>
          <a class="puerta" routerLink="/nivel">
            <span class="icono-puerta acento"><app-icono nombre="diana" /></span>
            <h3>Mídeme</h3>
            <p>Tres preguntas y tres fragmentos, uno por pantalla. Al final ves tu nivel.</p>
            <span class="enlace">Empezar <app-icono nombre="flecha" /></span>
          </a>
          <a class="puerta" routerLink="/encontrar">
            <span class="icono-puerta ambar"><app-icono nombre="lupa" /></span>
            <h3>Pregúntame</h3>
            <p>Escribe en español lo que te apetece: «detectives en Londres», «algo de Jane Austen».</p>
            <span class="enlace">Buscar <app-icono nombre="flecha" /></span>
          </a>
        </section>

        <section class="como">
          <h2>Cómo funciona</h2>
          <ol class="pasos">
            <li><span class="numero">1</span><div><h3>Sabes cuánto te va a costar</h3>
              <p>Un modelo propio lee el libro entero y dibuja su dificultad capítulo a capítulo, en una escala de 0 a 2.</p></div></li>
            <li><span class="numero">2</span><div><h3>Lees con red</h3>
              <p>Mantén presionada una palabra —con ratón, doble clic— y ves su pronunciación, la acepción que tiene en esa frase y la gramática.</p></div></li>
            <li><span class="numero">3</span><div><h3>Practicas en voz alta</h3>
              <p>Lee una frase del libro al micrófono y te dice qué sonido se te escapa y cómo colocar la boca.</p></div></li>
          </ol>
        </section>
        <a class="tarjeta-mini ancho" routerLink="/conversar">
          <span class="icono-mini"><app-icono nombre="micro" /></span>
          <div><strong>Conversar con Pléyade</strong><span class="tenue">Habla con ella y sigue la conversación por escrito</span></div>
          <span class="enlace">Abrir <app-icono nombre="flecha" /></span>
        </a>
      }
    </div>
  `,
  styles: `
    /* La portada va directamente sobre el cielo (el fondo astral de body, en
       styles.css), sin lámina; las tarjetas siguen el tema elegido. */
    .heroe { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr); gap: clamp(1.5rem, 4vw, 3.5rem);
      align-items: center; padding: clamp(1.25rem, 3vw, 2.75rem); margin-bottom: clamp(1.5rem, 3vw, 2.5rem); }
    /* La marca: el cielo del logo (azul noche, estrellas y oro rosa). Es igual
       en los tres temas: es el logo, no una superficie de lectura. */
    .cielo { position: relative; border-radius: var(--radio-lg); color: var(--crema);
      background: linear-gradient(160deg, rgba(6, 11, 36, .62), rgba(10, 16, 48, .42));
      border: 1px solid rgba(243, 201, 180, .16); box-shadow: 0 30px 80px -40px rgba(0, 0, 0, .8); }
    .cielo h1, .cielo h2 { color: var(--crema); }
    .cielo .antetitulo { color: var(--oro-rosa); }
    /* La ficha del ejemplo es una superficie de la app, no del cielo. */
    .cielo .demo { color: var(--texto); }
    .cielo .entradilla { color: #c8d3ee; }
    .cielo .boton { background: linear-gradient(135deg, var(--oro-rosa-brillo), var(--oro-rosa) 55%, var(--oro-rosa-sombra));
      color: var(--marca-noche); box-shadow: 0 8px 22px -10px var(--oro-rosa); }
    .cielo .boton:hover { background: var(--oro-rosa-brillo); }
    .cielo .boton.secundario { background: transparent; color: var(--crema);
      border-color: color-mix(in srgb, var(--oro-rosa) 60%, transparent); box-shadow: none; }
    .cielo .boton.secundario:hover { background: rgba(255, 255, 255, .08); }
    .cielo :focus-visible { outline-color: var(--oro-rosa-brillo); }
    .logo-heroe { display: block; width: 320px; max-width: 100%; height: auto; margin: -.75rem 0 .5rem -1rem;
      -webkit-mask-image: radial-gradient(closest-side, #000 70%, transparent 100%);
      mask-image: radial-gradient(closest-side, #000 70%, transparent 100%); }
    .cielo .realce { background-image: linear-gradient(100deg, var(--oro-rosa-brillo), var(--oro-rosa) 60%, var(--estrella)); }
    .realce { background: linear-gradient(100deg, var(--acento), var(--verde)); -webkit-background-clip: text; background-clip: text; color: transparent; }
    @media (forced-colors: active) { .realce { color: CanvasText; background: none; } }
    .entradilla { font-size: clamp(1.05rem, 1rem + .35vw, 1.25rem); color: var(--texto-suave); max-width: 46ch; margin-bottom: 1.5rem; }
    .demo { margin: 0; position: relative; padding-bottom: 3.5rem; }
    .demo-libro { background: var(--lector-fondo); border: 1px solid var(--borde); border-radius: var(--radio-lg);
      padding: 1.5rem 1.6rem 3rem; box-shadow: var(--sombra); color: var(--lector-texto); font-size: 1.12rem; line-height: 1.7; }
    .demo-libro p { margin: 0; }
    .demo-cap { display: block; font-family: var(--fuente-ui); font-size: .78rem; color: var(--texto-tenue); margin-bottom: .6rem; }
    mark { background: var(--seleccion); color: inherit; border-radius: 4px; padding: 0 .15em; box-shadow: inset 0 -2px 0 var(--acento); }
    .demo-ficha { position: absolute; right: -.5rem; bottom: 0; width: min(320px, 88%); background: var(--superficie);
      border: 1px solid var(--borde-fuerte); border-radius: var(--radio); padding: .9rem 1rem; box-shadow: var(--sombra-alta); font-size: .95rem; }
    .demo-ficha p { margin: .35rem 0 0; }
    .demo-cab { gap: .5rem; }
    .demo-cab strong { font-size: 1.15rem; }
    .cabecera-espacio { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.2rem;
      padding: clamp(1rem, 2.5vw, 1.4rem) clamp(1.1rem, 3vw, 1.75rem); }
    .cabecera-espacio h1 { margin: .1rem 0 0; font-family: var(--fuente-libro); font-weight: 700; letter-spacing: 0; }
    .cabecera-espacio .antetitulo { margin-bottom: 0; }
    .icono-espacio { flex: none; width: 48px; height: 48px; border-radius: 12px; box-shadow: 0 6px 18px -6px rgba(0, 0, 0, .6); }
    .seguir { display: block; margin-bottom: 1.5rem; color: inherit; text-decoration: none; border-color: color-mix(in srgb, var(--acento) 35%, var(--borde));
      background: linear-gradient(135deg, var(--superficie), color-mix(in srgb, var(--acento-suave) 55%, var(--superficie))); }
    .seguir:hover { box-shadow: var(--sombra-alta); }
    .seguir-cab { display: flex; justify-content: space-between; align-items: center; gap: .5rem; flex-wrap: wrap; }
    .seguir h2 { margin: .1rem 0 .1rem; }
    .seguir blockquote { margin: .8rem 0 1rem; padding-left: 1rem; border-left: 3px solid var(--acento); color: var(--lector-texto); font-size: 1.05rem; line-height: 1.6; }
    .seguir-pie { justify-content: space-between; margin-top: .6rem; }
    .enlace { display: inline-flex; align-items: center; gap: .35rem; color: var(--acento-texto); font-weight: 650; }
    .puertas { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .puerta { display: flex; flex-direction: column; gap: .35rem; padding: 1.4rem; border-radius: var(--radio-lg); background: var(--superficie);
      border: 1px solid var(--borde); color: inherit; text-decoration: none; box-shadow: var(--sombra);
      transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease; }
    .puerta:hover { transform: translateY(-3px); box-shadow: var(--sombra-alta); border-color: var(--borde-fuerte); }
    .puerta h3 { font-size: 1.25rem; margin: .5rem 0 0; }
    .puerta p { color: var(--texto-suave); margin: 0 0 .6rem; }
    .puerta .enlace { margin-top: auto; }
    .icono-puerta { display: grid; place-items: center; width: 48px; height: 48px; border-radius: 14px; font-size: 1.3rem; }
    .icono-puerta.verde { background: var(--verde-suave); color: var(--verde); }
    .icono-puerta.acento { background: var(--acento-suave); color: var(--acento-texto); }
    .icono-puerta.ambar { background: var(--ambar-suave); color: var(--ambar); }
    .como { padding-top: 1rem; }
    .como h2, .como h3 { color: var(--crema); }
    .como .pasos p { color: #c8d3ee; }
    .como .numero { background: linear-gradient(135deg, var(--oro-rosa-brillo), var(--oro-rosa)); color: var(--marca-noche); }
    .pasos { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.25rem; }
    .pasos li { display: flex; gap: .9rem; }
    .pasos h3 { margin: .2rem 0 .3rem; }
    .pasos p { color: var(--texto-suave); margin: 0; }
    .numero { flex: none; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%;
      background: var(--acento-suave); color: var(--acento-texto); font-weight: 750; }
    /* Mi espacio: rejilla 2×2 compacta (D3.1) + la tarjeta de nivel, ancha, debajo. */
    .rejilla-espacio { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; margin-bottom: .75rem; }
    .tarjeta-mini { display: grid; grid-template-columns: auto 1fr; align-items: center; gap: .1rem .8rem; padding: 1rem 1.1rem;
      border-radius: var(--radio); background: var(--superficie-2); color: inherit; text-decoration: none; border: 1px solid transparent; }
    .tarjeta-mini:hover { border-color: var(--borde-fuerte); }
    .tarjeta-mini strong { grid-column: 2; font-size: 1.3rem; line-height: 1.15; }
    .tarjeta-mini span:not(.icono-mini) { grid-column: 2; color: var(--texto-suave); font-size: .85rem; }
    .icono-mini { grid-row: 1 / 3; display: grid; place-items: center; width: 40px; height: 40px; border-radius: 12px;
      background: var(--acento-suave); color: var(--acento-texto); font-size: 1.15rem; }
    .tarjeta-mini.ancho { grid-template-columns: auto 1fr auto; margin-bottom: 1.75rem; }
    .tarjeta-mini.ancho div { grid-column: 2; }
    .tarjeta-mini.ancho .enlace { grid-column: 3; }
    /* Mi progreso (D3.3): dos bloques compactos, CSS puro, sin librería de gráficas. */
    .mi-progreso { margin-bottom: 1.75rem; display: grid; gap: 1.25rem; }
    .mi-progreso h2 { margin: 0 0 .25rem; }
    .bloque-progreso h3 { margin: 0 0 .6rem; font-size: 1rem; }
    .barras-dias { display: flex; align-items: flex-end; gap: 3px; height: 56px; }
    .barra-dia { flex: 1 1 0; min-width: 4px; border-radius: 3px 3px 0 0; background: var(--acento); opacity: .85; }
    .esqueleto-progreso { height: 56px; border-radius: var(--radio-sm, 8px); background: var(--superficie-3); }
    .barra-segmentada { display: flex; height: 14px; border-radius: 999px; overflow: hidden; background: var(--superficie-3); }
    .seg.si { background: var(--verde); }
    .seg.dude { background: var(--ambar); }
    .seg.no { background: var(--rojo); }
    .leyenda-repasos { list-style: none; display: flex; gap: 1rem; margin: .6rem 0 0; padding: 0; font-size: .88rem; flex-wrap: wrap; }
    .leyenda-repasos .punto { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: .35rem; }
    .punto.si { background: var(--verde); }
    .punto.dude { background: var(--ambar); }
    .punto.no { background: var(--rojo); }
    @media (max-width: 900px) {
      .heroe { grid-template-columns: 1fr; }
      .logo-heroe { margin: -.5rem auto .25rem; width: 240px; }
      .texto-heroe { text-align: center; }
      .texto-heroe .entradilla { margin-inline: auto; }
      .acciones-heroe { justify-content: center; }
      .demo { max-width: 560px; }
      .puertas, .pasos { grid-template-columns: 1fr; }
      .demo-ficha { right: 0; }
    }
    @media (max-width: 640px) {
      /* En el móvil la ficha no puede tapar el párrafo que explica: va debajo,
         solapando solo el borde de la hoja. */
      .demo { padding-bottom: 0; }
      .demo-libro { padding-bottom: 2.2rem; }
      .demo-ficha { position: relative; right: auto; bottom: auto; width: auto; margin: -1.4rem .75rem 0; }
    }
    @media (max-width: 480px) {
      .acciones-heroe .boton { flex: 1 1 100%; }
      .demo-libro { font-size: 1.02rem; padding: 1.1rem 1.1rem 2.2rem; }
      .rejilla-espacio { grid-template-columns: 1fr; }
    }
  `,
})
export class Inicio {
  private readonly sesion = inject(Sesion);
  private readonly api = inject(Api);
  protected readonly inicio = this.sesion.inicio;
  protected readonly perfil = this.sesion.perfil;
  protected readonly seguir = computed(() => this.inicio()?.seguir ?? null);
  protected readonly bienvenida = this.sesion.bienvenida;
  protected readonly ajustesAbiertos = this.sesion.ajustesAbiertos;
  /** La bienvenida elige su paso 0 según haya cuenta o no, y la sesión llega después del primer
   *  pintado: sin esperar, quien ya ha entrado veía un instante «¿Ya tienes cuenta?» (4e, 16 sep).
   *  Con el motor caído, o si /api/inicio falla, la sesión no llega en esta visita, y ahí se
   *  enseña como a un visitante. */
  protected readonly sesionConocida = computed(() =>
    this.sesion.entrada() !== null || this.sesion.motor() === 'caido' || this.sesion.sesionFallida());
  protected readonly num = num;
  protected readonly cefr = cefr;
  protected readonly miles = miles;
  protected readonly Math = Math;

  /** D3.1 (Miguel): «Mi espacio» en cuanto hay ALGO real que enseñar, no
   *  solo libros/consultas — un perfil ya medido también cuenta, aunque
   *  todavía no se haya leído nada. Se apoya solo en `/api/inicio`, ya
   *  cargado de un único golpe: nunca cambia de modo a medio cargar
   *  (antes de que `inicio()` llegue, `modoEspacio()` es `false` y se ve
   *  la puerta de siempre — el mismo comportamiento que ya tenía esta
   *  pantalla con la tarjeta «Donde lo dejaste» y el resumen). */
  protected readonly modoEspacio = computed(() => {
    const i = this.inicio();
    return !!i && (i.libros > 0 || i.cuaderno.consultas > 0 || !!i.perfil);
  });

  /** Solo para la tarjeta de Pronunciación: no viene en `/api/inicio`, así
   *  que se pide aparte, y solo una vez que ya se sabe que hace falta
   *  (Miguel: "no hacer llamadas innecesarias" — aquí sí hace falta un
   *  conteo real, a diferencia de Repasar, que no llama a `/api/repaso`
   *  porque basta con `cuaderno.consultas > 0` para saber que hay algo). */
  protected readonly falladas = signal<PalabraFallada[]>([]);
  private falladasPedidas = false;

  /** D3.3: agregados de `/api/progreso` — solo se pide una vez, y solo en
   *  modo Mi espacio (igual que `falladas`). Si falla, se dice en la
   *  propia tarjeta «Mi progreso»; el resto de la pantalla no se entera. */
  protected readonly progreso = signal<Progreso | null>(null);
  protected readonly progresoError = signal('');
  private progresoPedido = false;
  protected readonly totalConsultas14 = computed(() =>
    (this.progreso()?.palabras_por_dia ?? []).reduce((s, d) => s + d.consultas, 0));

  constructor() {
    if (this.sesion.motor() === 'listo') void this.sesion.refrescar();
    effect(() => {
      if (!this.modoEspacio() || this.falladasPedidas) return;
      this.falladasPedidas = true;
      this.api.falladas().subscribe({ next: r => this.falladas.set(r.palabras), error: () => {} });
    });
    effect(() => {
      if (!this.modoEspacio() || this.progresoPedido) return;
      this.progresoPedido = true;
      // La zona real del navegador, nunca la del servidor (D3.3, Miguel):
      // si falla incluso leerla, se manda sin `tz` y el backend cae a UTC.
      let tz: string | undefined;
      try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch { /* sin Intl */ }
      this.api.miProgreso(tz).subscribe({
        next: p => this.progreso.set(p),
        error: e => this.progresoError.set(mensajeError(e, 'No se pudo cargar tu progreso.')),
      });
    });
  }

  /** Altura de la barra del día, con un mínimo visible para los días en 0
   *  (una barra invisible se lee como "no hay dato", no como "cero"). */
  protected alturaBarra(consultas: number): number {
    const max = Math.max(1, ...(this.progreso()?.palabras_por_dia ?? []).map(d => d.consultas));
    return Math.max(8, (consultas / max) * 100);
  }

  protected pct(n: number, total: number): number {
    return total > 0 ? (n / total) * 100 : 0;
  }
}
