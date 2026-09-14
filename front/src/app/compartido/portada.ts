import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/** Las doce familias en que se agrupan los temas de Gutenberg («Science
 *  fiction», «Detective and mystery stories»…) y de los corpus libres
 *  («Children's stories; StoryWeaver reading level 2», «VOA Learning English»).
 *  Cada una tiene su tono y su motivo geométrico. */
export type Familia =
  | 'aventura' | 'misterio' | 'amor' | 'fantasia' | 'ciencia' | 'historia'
  | 'infantil' | 'poesia' | 'teatro' | 'mar' | 'ensayo' | 'novela';

/** Por orden de prioridad: gana la primera familia que casa con ALGÚN tema.
 *  Lo más concreto va antes (poesía, teatro, ciencia ficción) y lo más general
 *  después («Juvenile fiction» solo decide si no hay nada más específico). */
const REGLAS: readonly (readonly [Familia, RegExp])[] = [
  ['poesia', /poe(try|ms?)\b|\bverse\b|ballads|sonnets|hymns/i],
  ['teatro', /drama|\bplays\b|comed(y|ies)|traged|theat(er|re)|humou?r|\bwit\b|satire/i],
  ['ciencia', /science fiction|human-alien|outer space|interplanetary|robots|time travel|\bscience\b|technology|inventions/i],
  ['misterio', /detective|investigators|sherlock|police|criminals|myster|crime|murder|ghost|horror|gothic|supernatural|suspense|\bspies\b|\bspy\b/i],
  ['fantasia', /fantasy|fairy|magic|legends?\b|mytholog|\bmyths?\b|folklore|dragons|wizards/i],
  ['mar', /\bsea\b|voyages|travel|sailors|\bships\b|pirates|islands|shipwrecks/i],
  ['aventura', /adventure|western|frontier|cowboys|explorers?|hunting|survival/i],
  ['historia', /historical|history|\bwars?\b|world war|biograph|revolution|kings and rulers|antiquities/i],
  ['amor', /love stories|romance|man-woman|courtship|\blove\b/i],
  ['infantil', /children|juvenile|storyweaver|african storybook|let's read|nursery|picture books/i],
  ['ensayo', /essays|periodicals|philosophy|religio|christian|sermons|education|voa|words & their|ask a teacher|as it is|health|arts & culture|conduct of life|economics|politic|\bletters\b/i],
];

export function familiaDe(temas: readonly string[] | null | undefined): Familia {
  const lista = (temas ?? []).filter(Boolean);
  for (const [familia, regla] of REGLAS) {
    if (lista.some(t => regla.test(t))) return familia;
  }
  return 'novela';
}

interface EstiloFamilia { nombre: string; tono: number; saturacion: number }

/** Tonos repartidos por el círculo para que dos familias vecinas no se confundan. */
export const FAMILIAS: Record<Familia, EstiloFamilia> = {
  teatro: { nombre: 'Teatro y humor', tono: 5, saturacion: 62 },
  aventura: { nombre: 'Aventura', tono: 24, saturacion: 66 },
  historia: { nombre: 'Historia', tono: 42, saturacion: 44 },
  infantil: { nombre: 'Infantil', tono: 96, saturacion: 48 },
  novela: { nombre: 'Novela', tono: 162, saturacion: 34 },
  ciencia: { nombre: 'Ciencia', tono: 184, saturacion: 58 },
  mar: { nombre: 'Viajes y mar', tono: 204, saturacion: 60 },
  ensayo: { nombre: 'Ensayo', tono: 218, saturacion: 22 },
  misterio: { nombre: 'Misterio', tono: 242, saturacion: 42 },
  fantasia: { nombre: 'Fantasía', tono: 274, saturacion: 48 },
  poesia: { nombre: 'Poesía', tono: 312, saturacion: 40 },
  amor: { nombre: 'Amor', tono: 348, saturacion: 58 },
};

/** FNV-1a de 32 bits: el mismo id da siempre la misma portada. */
export function huella(texto: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < texto.length; i++) {
    h ^= texto.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** Números pseudoaleatorios deterministas a partir de una semilla (mulberry32). */
export function azar(semilla: number): () => number {
  let a = semilla >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// --- Color: HSL, luminancia y contraste WCAG ----------------------------------

export function hslAHex(h: number, s: number, l: number): string {
  const tono = ((h % 360) + 360) % 360;
  const sat = Math.max(0, Math.min(100, s)) / 100;
  const luz = Math.max(0, Math.min(100, l)) / 100;
  const k = (n: number) => (n + tono / 30) % 12;
  const a = sat * Math.min(luz, 1 - luz);
  const f = (n: number) => luz - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return '#' + [f(0), f(8), f(4)].map(x => Math.round(x * 255).toString(16).padStart(2, '0')).join('');
}

export function luminancia(hex: string): number {
  const n = parseInt(hex.replace('#', ''), 16);
  const canal = (c: number) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * canal((n >> 16) & 255) + 0.7152 * canal((n >> 8) & 255) + 0.0722 * canal(n & 255);
}

export function contraste(a: string, b: string): number {
  const [x, y] = [luminancia(a), luminancia(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}

/** Los cinco colores de un libro. `tinta` es el texto sobre `fondo` (≥ 4,5:1). */
export interface Paleta {
  familia: Familia;
  tono: number;
  saturacion: number;
  fondo: string;
  hondo: string;
  motivo: string;
  luz: string;
  tinta: string;
}

export function paletaDe(id: string, familia: Familia): Paleta {
  const base = FAMILIAS[familia];
  const r = azar(huella(`${id}|${familia}`));
  // Los cuentos infantiles son miles (StoryWeaver): con el mismo verde, una
  // lista de resultados era una pared. Su tono se abre de naranja a turquesa.
  const abanico = familia === 'infantil' ? 150 : 30;
  const tono = base.tono + Math.round((r() - 0.5) * abanico);
  const sat = base.saturacion + Math.round((r() - 0.5) * 14);
  // Los tonos amarillos y verdes son muy luminosos: a la misma luz que un azul,
  // el título blanco no se lee. Se oscurece el fondo hasta que pase de 4,8:1.
  let l = 27 + Math.round(r() * 9);
  while (l > 10 && contraste('#ffffff', hslAHex(tono, sat, l)) < 4.8) l -= 2;
  const fondo = hslAHex(tono, sat, l);
  const hondo = hslAHex(tono + 8, sat + 6, l - 13);
  const motivo = hslAHex(tono + 34 + Math.round(r() * 20), Math.min(90, sat + 18), 58);
  const luz = hslAHex(tono - 28, Math.max(18, sat - 10), 80);
  let tinta = hslAHex(tono, 30, 97);
  if (contraste(tinta, fondo) < 4.5) tinta = '#ffffff';
  return { familia, tono, saturacion: sat, fondo, hondo, motivo, luz, tinta };
}

// --- Motivos: geometría sencilla, distinta en cada libro -----------------------

export interface Forma {
  d?: string;
  cx?: number; cy?: number; r?: number;
  relleno: string;
  trazo?: string;
  grosor?: number;
  opacidad: number;
}

const W = 300;
const H = 420;

function onda(y: number, amplitud: number, periodo: number, fase: number): string {
  let d = `M -10 ${y}`;
  for (let x = -10; x <= W + 10; x += 10) {
    d += ` L ${x} ${(y + Math.sin((x / periodo) * Math.PI * 2 + fase) * amplitud).toFixed(1)}`;
  }
  return d;
}

export function motivoDe(id: string, p: Paleta): Forma[] {
  const r = azar(huella(`motivo|${id}`));
  const f: Forma[] = [];
  const entre = (a: number, b: number) => a + r() * (b - a);
  switch (p.familia) {
    case 'aventura': {                                   // cordillera y sol
      f.push({ cx: entre(60, 240), cy: entre(250, 290), r: entre(34, 52), relleno: p.luz, opacidad: 0.8 });
      for (let i = 0; i < 3; i++) {
        const x = entre(-40, 220), alto = entre(90, 160), ancho = entre(140, 220);
        f.push({ d: `M ${x} ${H} L ${x + ancho / 2} ${H - alto} L ${x + ancho} ${H} Z`, relleno: i % 2 ? p.motivo : p.hondo, opacidad: 0.85 });
      }
      break;
    }
    case 'misterio': {                                   // luna menguante y niebla
      const cx = entre(170, 240), cy = entre(250, 300), rr = entre(40, 58);
      f.push({ cx, cy, r: rr, relleno: p.luz, opacidad: 0.9 });
      f.push({ cx: cx - rr * 0.45, cy: cy - rr * 0.2, r: rr, relleno: p.fondo, opacidad: 1 });
      for (let i = 0; i < 3; i++) f.push({ d: onda(340 + i * 22, 4, 140, r() * 6), relleno: 'none', trazo: p.motivo, grosor: 3, opacidad: 0.45 });
      break;
    }
    case 'amor': {                                       // círculos que se cruzan
      const y = entre(270, 320);
      f.push({ cx: entre(95, 130), cy: y, r: entre(52, 70), relleno: p.motivo, opacidad: 0.7 });
      f.push({ cx: entre(170, 205), cy: y + entre(-20, 20), r: entre(52, 70), relleno: p.luz, opacidad: 0.55 });
      break;
    }
    case 'fantasia': {                                   // estrellas de cuatro puntas
      for (let i = 0; i < 9; i++) {
        const x = entre(20, 280), y = entre(210, 400), t = entre(5, i < 2 ? 22 : 11);
        f.push({ d: `M ${x} ${y - t} Q ${x} ${y} ${x + t} ${y} Q ${x} ${y} ${x} ${y + t} Q ${x} ${y} ${x - t} ${y} Q ${x} ${y} ${x} ${y - t} Z`,
          relleno: i < 2 ? p.luz : p.motivo, opacidad: 0.9 });
      }
      break;
    }
    case 'ciencia': {                                    // planeta y órbitas
      const cx = entre(100, 200), cy = entre(290, 330);
      for (let i = 0; i < 3; i++) {
        const rx = 70 + i * 34, ry = 20 + i * 11;
        f.push({ d: `M ${cx - rx} ${cy} A ${rx} ${ry} ${entre(-20, 20)} 1 0 ${cx + rx} ${cy} A ${rx} ${ry} 0 1 0 ${cx - rx} ${cy}`,
          relleno: 'none', trazo: p.luz, grosor: 2, opacidad: 0.6 });
      }
      f.push({ cx, cy, r: entre(22, 32), relleno: p.motivo, opacidad: 1 });
      break;
    }
    case 'historia': {                                   // columnata
      const n = 4 + Math.floor(r() * 3), paso = W / n;
      for (let i = 0; i < n; i++) {
        f.push({ d: `M ${i * paso + paso * 0.3} ${H} L ${i * paso + paso * 0.3} ${entre(250, 280)} L ${i * paso + paso * 0.7} ${entre(250, 280)} L ${i * paso + paso * 0.7} ${H} Z`,
          relleno: i % 2 ? p.motivo : p.luz, opacidad: 0.5 });
      }
      f.push({ d: `M 0 245 L ${W} 245`, relleno: 'none', trazo: p.luz, grosor: 6, opacidad: 0.6 });
      break;
    }
    case 'infantil': {                                   // confeti de lunares
      for (let i = 0; i < 11; i++) {
        f.push({ cx: entre(10, 290), cy: entre(220, 410), r: entre(8, 30), relleno: i % 3 === 0 ? p.luz : p.motivo, opacidad: entre(0.55, 0.9) });
      }
      break;
    }
    case 'poesia': {                                     // versos como líneas finas
      for (let i = 0; i < 7; i++) f.push({ d: onda(250 + i * 22, entre(3, 9), entre(90, 180), r() * 6), relleno: 'none', trazo: i % 2 ? p.luz : p.motivo, grosor: 1.6, opacidad: 0.7 });
      break;
    }
    case 'teatro': {                                     // telón
      const caida = entre(300, 360);
      f.push({ d: `M 0 200 Q 90 ${caida - 60} 40 ${H} L 0 ${H} Z`, relleno: p.motivo, opacidad: 0.8 });
      f.push({ d: `M ${W} 200 Q 210 ${caida - 60} 260 ${H} L ${W} ${H} Z`, relleno: p.motivo, opacidad: 0.8 });
      f.push({ d: `M 0 196 Q 150 ${entre(230, 250)} ${W} 196`, relleno: 'none', trazo: p.luz, grosor: 5, opacidad: 0.7 });
      break;
    }
    case 'mar': {                                        // olas
      for (let i = 0; i < 4; i++) f.push({ d: onda(290 + i * 30, entre(8, 14), entre(110, 160), r() * 6) + ` L ${W + 10} ${H + 10} L -10 ${H + 10} Z`,
        relleno: i % 2 ? p.hondo : p.motivo, opacidad: 0.55 });
      break;
    }
    case 'ensayo': {                                     // retícula
      const lado = 26 + Math.floor(r() * 12);
      for (let y = 250; y < H; y += lado + 8) {
        for (let x = 16; x < W - lado; x += lado + 8) {
          if (r() < 0.55) f.push({ d: `M ${x} ${y} h ${lado} v ${lado} h ${-lado} Z`, relleno: r() < 0.3 ? p.luz : p.motivo, opacidad: 0.5 });
        }
      }
      break;
    }
    default: {                                           // novela: franjas diagonales
      const inclinacion = entre(60, 140);
      for (let i = 0; i < 5; i++) {
        const x = -120 + i * 80 + entre(-10, 10), ancho = entre(14, 34);
        f.push({ d: `M ${x} ${H} L ${x + inclinacion} 220 L ${x + inclinacion + ancho} 220 L ${x + ancho} ${H} Z`, relleno: i % 2 ? p.luz : p.motivo, opacidad: 0.45 });
      }
    }
  }
  return f;
}

/** Portada tipográfica de un libro, determinista y sin imágenes externas
 *  (Miguel, 14 sep): tono y motivo de su familia de temas, colores derivados
 *  del id, título grande, autor pequeño y banda de nivel.
 *
 *  `portadaIa`: si algún día hay una ilustración generada en /data/portadas,
 *  se enseña en lugar de la tipográfica con su aviso (ver punto 3). */
@Component({
  selector: 'app-portada',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="portada" [class.compacta]="compacta()" [attr.data-familia]="paleta().familia"
         [style.--fondo]="paleta().fondo" [style.--hondo]="paleta().hondo" [style.--tinta]="paleta().tinta"
         [style.--luz]="paleta().luz" [style.--escala]="escala()">
      <svg class="motivo" viewBox="0 0 300 420" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
        @for (m of formas(); track $index) {
          @if (m.d) {
            <path [attr.d]="m.d" [attr.fill]="m.relleno" [attr.stroke]="m.trazo ?? null" [attr.stroke-width]="m.grosor ?? null"
                  [attr.opacity]="m.opacidad" stroke-linecap="round" />
          } @else {
            <circle [attr.cx]="m.cx" [attr.cy]="m.cy" [attr.r]="m.r" [attr.fill]="m.relleno" [attr.opacity]="m.opacidad" />
          }
        }
      </svg>
      <div class="letras" aria-hidden="true">
        <span class="titulo">{{ tituloVisible() }}</span>
        @if (!compacta() && autor()) { <span class="autor">{{ autor() }}</span> }
      </div>
      <span class="banda" aria-hidden="true">{{ cefr() || '—' }}</span>
    </div>
  `,
  styles: `
    :host { display: block; container-type: inline-size; }
    .portada {
      position: relative; aspect-ratio: 3 / 4.2; overflow: hidden; border-radius: 6px 11px 11px 6px;
      background: linear-gradient(170deg, var(--fondo) 0%, var(--fondo) 45%, var(--hondo) 100%);
      box-shadow: inset 5px 0 0 rgba(0, 0, 0, .16), 0 6px 14px -8px rgba(0, 0, 0, .5);
      color: var(--tinta);
    }
    .motivo { position: absolute; inset: 0; width: 100%; height: 100%; }
    .letras {
      position: absolute; left: 9%; right: 8%; top: 8%; display: grid; gap: .45em;
    }
    .titulo {
      font-family: var(--fuente-libro); font-weight: 700; line-height: 1.04; letter-spacing: -.01em;
      font-size: calc(13cqi * var(--escala, 1)); overflow-wrap: anywhere; hyphens: auto;
      display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden;
      text-shadow: 0 1px 2px rgba(0, 0, 0, .25);
    }
    .autor {
      font-family: var(--fuente-ui); font-size: max(9px, 6.2cqi); font-weight: 600; letter-spacing: .06em;
      text-transform: uppercase; opacity: .9;
      display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
    }
    .banda {
      position: absolute; left: 0; bottom: 7%; padding: .25em .7em .25em 9%; border-radius: 0 999px 999px 0;
      font-family: var(--fuente-ui); font-size: max(9px, 7cqi); font-weight: 800; letter-spacing: .05em;
      background: rgba(0, 0, 0, .38); color: #fff;
    }
    .compacta .letras { top: 7%; left: 8%; right: 7%; }
    .compacta .titulo { font-size: max(9px, calc(14cqi * var(--escala, 1))); -webkit-line-clamp: 4; }
    .compacta .banda { bottom: 6%; font-size: max(9px, 11cqi); }
  `,
})
export class Portada {
  readonly id = input.required<string>();
  readonly titulo = input<string>('');
  readonly autor = input<string>('');
  readonly cefr = input<string | null>(null);
  readonly temas = input<readonly string[] | null | undefined>([]);
  /** En las tarjetas: sin autor y con el título más apretado. */
  readonly compacta = input(false);

  protected readonly familia = computed(() => familiaDe(this.temas()));
  protected readonly paleta = computed(() => paletaDe(this.id(), this.familia()));
  protected readonly formas = computed(() => motivoDe(this.id(), this.paleta()));
  /** Sin el subtítulo tras «:» o «;»: en la portada manda el nombre corto. */
  protected readonly tituloVisible = computed(() => {
    const t = this.titulo().trim();
    const corto = t.split(/\s*[:;]\s+|\s+—\s+/)[0];
    return corto.length >= 3 ? corto : t;
  });
  /** Cuanto más largo el título, más pequeña la letra. */
  protected readonly escala = computed(() => {
    const n = this.tituloVisible().length;
    const c = this.compacta();
    if (n <= 12) return c ? 1.25 : 1.3;
    if (n <= 24) return 1;
    if (n <= 44) return c ? 0.78 : 0.8;
    return c ? 0.64 : 0.66;
  });
}
