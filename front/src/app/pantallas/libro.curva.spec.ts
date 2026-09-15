import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { Api, Curva, FilaCurva, Libro } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { FichaLibro } from './libro';

/** Reinicio 27 (Miguel en el móvil, el cuento de Kian): con un solo capítulo la ficha decía
 *  «Se va soltando… lo más llevadero, el capítulo 1; lo más exigente, el 1» y la gráfica
 *  salía sin ningún punto. Con uno no hay tendencia ni gráfica; con dos, sí. */
describe('Ficha: dificultad capítulo a capítulo', () => {
  const fila = (capitulo: number, dificultad: number): FilaCurva =>
    ({ capitulo, indice: capitulo - 1, titulo: `Capítulo ${capitulo}`, dificultad, ventanas: 4, palabras: 900 });
  const libro = (n: number): Libro => ({
    id: 'SW-KIAN', titulo: 'Kian', autor: '', palabras: 900 * n, inicial: 0, dificultad: 0.85, cefr: 'B1',
    fuente_dificultad: null, capitulos: Array.from({ length: n }, (_, i) => ({ indice: i, titulo: `Capítulo ${i + 1}`, palabras: 900 })),
    ficha: null, sugeridos: [], sinopsis: null,
  });

  async function montar(n: number, curva: Curva) {
    if (typeof ResizeObserver === 'undefined') {
      (globalThis as { ResizeObserver?: unknown }).ResizeObserver = class { observe() {} disconnect() {} };
    }
    const api = { curva: vi.fn(() => of(curva)), biblioteca: vi.fn(() => of({ libros: [] })) };
    const sesion = { perfil: signal({ nivel: 0.95 }), libro: vi.fn(async () => libro(n)), ajustesAbiertos: signal(false) };
    await TestBed.configureTestingModule({
      imports: [FichaLibro],
      providers: [provideRouter([]), { provide: Api, useValue: api }, { provide: Sesion, useValue: sesion }],
    }).compileComponents();
    const fixture = TestBed.createComponent(FichaLibro);
    fixture.componentRef.setInput('id', 'SW-KIAN');
    fixture.detectChanges();
    for (let i = 0; i < 3; i++) { await fixture.whenStable(); fixture.detectChanges(); }
    const tarjeta = (fixture.nativeElement as HTMLElement).querySelector('section.curva') as HTMLElement;
    return { tarjeta, texto: tarjeta.textContent!.replace(/\s+/g, ' ') };
  }

  it('un capítulo: sin tendencia, sin «más llevadero» y sin gráfica vacía', async () => {
    const f = fila(1, 0.85);
    // Tal cual lo manda la API hoy: forma «se_suelta» porque la segunda mitad está vacía.
    const { tarjeta, texto } = await montar(1, { fuente: 'catalogo', filas: [f], forma: 'se_suelta', facil: f, dificil: f });
    expect(texto).toContain('Es un texto de un solo capítulo');
    expect(texto).toContain('0,85 (B1)');
    for (const sobra of ['Se va soltando', 'Se va complicando', 'Mantiene un nivel', 'Lo más llevadero', 'Toca un punto']) {
      expect(texto).not.toContain(sobra);
    }
    expect(tarjeta.querySelector('app-curva')).toBeNull();
    expect(texto).not.toContain('todavía no está medido');
  });

  it('un capítulo con la API del 27: forma, facil y dificil llegan en null', async () => {
    const { tarjeta, texto } = await montar(1, { fuente: 'completo', filas: [fila(1, 0.96)], forma: null, facil: null, dificil: null });
    expect(texto).toContain('Es un texto de un solo capítulo');
    expect(texto).toContain('0,96 (B1)');
    for (const sobra of ['Se va', 'Mantiene un nivel', 'Lo más llevadero', 'Toca un punto', 'todavía no está medido']) {
      expect(texto).not.toContain(sobra);
    }
    expect(tarjeta.querySelector('app-curva')).toBeNull();
  });

  it('dos capítulos: tendencia, capítulos extremos y gráfica', async () => {
    const a = fila(1, 1.3), b = fila(2, 0.9);
    const { tarjeta, texto } = await montar(2, { fuente: 'catalogo', filas: [a, b], forma: 'se_suelta', facil: b, dificil: a });
    expect(texto).toContain('Se va soltando');
    expect(texto).toContain('Lo más llevadero, el capítulo 2; lo más exigente, el 1.');
    expect(texto).not.toContain('un solo capítulo');
    expect(tarjeta.querySelector('app-curva')).not.toBeNull();
    expect(texto).toContain('Toca un punto');
  });
});
