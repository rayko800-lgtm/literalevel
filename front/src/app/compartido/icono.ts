import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/** Iconos de trazo en SVG en línea: sin fuentes de iconos ni peticiones. */
const RUTAS: Record<string, string> = {
  casa: 'M3.5 11 12 4l8.5 7M6 9.5V20h12V9.5',
  libro: 'M12 6.5C10.3 5.2 8 4.5 4 4.5v14c4 0 6.3.7 8 2 1.7-1.3 4-2 8-2v-14c-4 0-6.3.7-8 2ZM12 6.5v14',
  lupa: 'M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13ZM20 20l-4.8-4.8',
  micro: 'M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3ZM5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M8.5 21h7',
  nivel: 'M5 20v-6M10 20V9M15 20v-9M20 20V5',
  ajustes: 'M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1M15 4v4M9 10v4M17 16v4',
  izq: 'M15 5l-7 7 7 7',
  der: 'M9 5l7 7-7 7',
  cerrar: 'M6 6l12 12M18 6 6 18',
  indice: 'M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01',
  play: 'M8 5.5v13l10.5-6.5L8 5.5Z',
  stop: 'M7 7h10v10H7z',
  altavoz: 'M4 9.5h3.5L12 5.5v13l-4.5-4H4v-5ZM16 9a4 4 0 0 1 0 6M18.5 6.5a7.5 7.5 0 0 1 0 11',
  check: 'M5 12.5l4.5 4.5L19 7.5',
  subir: 'M12 16V4M7 9l5-5 5 5M4 16v3.5h16V16',
  recargar: 'M20 11.5A8 8 0 1 0 17.7 17M20 5v6.5h-6.5',
  palabras: 'M6 3.5h11.5v17H6A1.5 1.5 0 0 1 4.5 19V5A1.5 1.5 0 0 1 6 3.5ZM8.5 8h6M8.5 11.5h6',
  rayo: 'M13 3 5 13.5h6L10 21l8-10.5h-6L13 3Z',
  ojo: 'M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12ZM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
  reloj: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 7.5V12l3 2',
  persona: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM4.5 20.5a7.5 7.5 0 0 1 15 0',
  letra: 'M3 18 7.5 6h1L13 18M4.6 14h6.8M15 18l3-8h.6l3 8M15.9 15.6h4.8',
  chispa: 'M12 3.5v3.5M12 17v3.5M3.5 12H7M17 12h3.5M6 6l2.4 2.4M15.6 15.6 18 18M6 18l2.4-2.4M15.6 8.4 18 6',
  basura: 'M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13',
  diana: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM12 12h.01',
  flecha: 'M5 12h14M13 6l6 6-6 6',
  medir: 'M4 17 9.5 11.5l3.5 3.5L20 8M15 8h5v5',
  info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 11v5.5M12 7.5h.01',
  paginas: 'M3.5 5.5c2.8-.8 5.6-.6 8.5.9v13c-2.9-1.5-5.7-1.7-8.5-.9v-13ZM20.5 5.5c-2.8-.8-5.6-.6-8.5.9v13c2.9-1.5 5.7-1.7 8.5-.9v-13Z',
  rollo: 'M7 3.5h10M7 20.5h10M8.5 8h7M8.5 12h7M8.5 16h5',
};

@Component({
  selector: 'app-icono',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { class: 'icono', 'aria-hidden': 'true' },
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"
    stroke-linecap="round" stroke-linejoin="round" focusable="false"><path [attr.d]="ruta()" /></svg>`,
  styles: `:host{display:inline-grid;place-items:center;width:1.3em;height:1.3em;flex:none}
    svg{width:100%;height:100%}`,
})
export class Icono {
  readonly nombre = input.required<string>();
  protected readonly ruta = computed(() => RUTAS[this.nombre()] ?? RUTAS['info']);
}
