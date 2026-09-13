import { Injectable, effect, signal } from '@angular/core';

export type Tema = 'sistema' | 'claro' | 'noche' | 'papel';
export type TamanoLetra = 'pequena' | 'normal' | 'grande' | 'enorme';
export type Idioma = 'es' | 'en';
/** Por páginas, como un Kindle (lo pidió Miguel), o seguido, desplazando. */
export type ModoLectura = 'paginas' | 'rollo';

/** Al subir la letra se estrecha la columna: si no, con letra grande se vuelve
 *  a pasar de 75 caracteres por línea (diseno_lector.md §8.2). */
const CUERPOS: Record<TamanoLetra, { cuerpo: string; medida: string }> = {
  pequena: { cuerpo: '18px', medida: '66ch' },
  normal: { cuerpo: '20px', medida: '64ch' },
  grande: { cuerpo: '23px', medida: '56ch' },
  enorme: { cuerpo: '27px', medida: '48ch' },
};

function leer<T extends string>(clave: string, validos: readonly T[], defecto: T): T {
  try {
    const v = localStorage.getItem(clave) as T | null;
    return v && validos.includes(v) ? v : defecto;
  } catch {
    return defecto;
  }
}

function guardar(clave: string, valor: string): void {
  try { localStorage.setItem(clave, valor); } catch { /* sin almacenamiento */ }
}

@Injectable({ providedIn: 'root' })
export class Preferencias {
  readonly tema = signal<Tema>(leer('literalevel.tema', ['sistema', 'claro', 'noche', 'papel'], 'sistema'));
  readonly letra = signal<TamanoLetra>(leer('literalevel.letra', ['pequena', 'normal', 'grande', 'enorme'], 'normal'));
  readonly idioma = signal<Idioma>(leer('literalevel.idioma', ['es', 'en'], 'es'));
  readonly modoLectura = signal<ModoLectura>(leer('literalevel.modo', ['paginas', 'rollo'], 'paginas'));
  /** Acento de Pronunciar: la tabla del AFI y la IPA de toda la corrección. */
  readonly acento = signal<'ga' | 'rp'>(leer('literalevel.acento', ['ga', 'rp'], 'ga'));

  constructor() {
    effect(() => {
      const t = this.tema();
      guardar('literalevel.tema', t);
      const raiz = document.documentElement;
      if (t === 'sistema') raiz.removeAttribute('data-tema');
      else raiz.setAttribute('data-tema', t);
    });
    effect(() => {
      const l = this.letra();
      guardar('literalevel.letra', l);
      const { cuerpo, medida } = CUERPOS[l];
      document.documentElement.style.setProperty('--cuerpo-libro', cuerpo);
      document.documentElement.style.setProperty('--medida', medida);
    });
    effect(() => guardar('literalevel.idioma', this.idioma()));
    effect(() => guardar('literalevel.modo', this.modoLectura()));
    effect(() => guardar('literalevel.acento', this.acento()));
  }
}
