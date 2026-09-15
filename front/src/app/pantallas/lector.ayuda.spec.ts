import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { Api, Capitulo, Libro } from '../nucleo/api';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';
import { Lector } from './lector';

/** Tanda 2 de la ayuda (Miguel, sobre el informe de Ismael): la primera vez en el lector salían
 *  dos avisos a la vez (el de la palabra arriba y el de pasar página abajo) y del libro se veían
 *  unas dos líneas a 390 px. Ahora hay uno solo, con ✕ y un «?» que lo vuelve a enseñar. */
describe('Lector: un solo aviso la primera vez', () => {
  const LIBRO: Libro = {
    id: 'PG11', titulo: 'Alice', autor: 'Carroll', palabras: 100, inicial: 1, dificultad: null, cefr: null,
    fuente_dificultad: null, capitulos: [{ indice: 0, titulo: 'Portada', palabras: 10 }, { indice: 1, titulo: 'CHAPTER I', palabras: 90 }],
    ficha: null, sugeridos: [], sinopsis: null,
  };
  const CAP: Capitulo = { libro_id: 'PG11', indice: 1, total: 2, titulo: 'CHAPTER I', palabras: 90, parrafos: ['Alice was beginning to get very tired.'] };
  const matchMediaOriginal = window.matchMedia;

  function tactil(si: boolean) {
    window.matchMedia = ((q: string) => ({ matches: si && q.includes('coarse'), media: q, addEventListener() {}, removeEventListener() {} })) as unknown as typeof window.matchMedia;
  }

  beforeEach(async () => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    await TestBed.configureTestingModule({
      imports: [Lector],
      providers: [
        provideRouter([]),
        { provide: Api, useValue: { capitulo: vi.fn(() => of(CAP)), progreso: vi.fn(() => of({})) } },
        { provide: Sesion, useValue: { libro: vi.fn(async () => LIBRO), perfil: signal(null), entrada: signal(null), inicio: signal(null),
          refrescar: vi.fn(async () => {}), ajustesAbiertos: signal(false), abrirPerfil: vi.fn() } },
      ],
    }).compileComponents();
  });

  afterEach(() => { window.matchMedia = matchMediaOriginal; });

  async function montar(modo: 'paginas' | 'rollo') {
    TestBed.inject(Preferencias).modoLectura.set(modo);
    const fixture = TestBed.createComponent(Lector);
    fixture.componentRef.setInput('id', 'PG11');
    fixture.componentRef.setInput('cap', '1');
    fixture.detectChanges();
    for (let i = 0; i < 4; i++) { await fixture.whenStable(); fixture.detectChanges(); }
    const raiz = fixture.nativeElement as HTMLElement;
    const texto = (el: Element | null) => (el?.textContent ?? '').replace(/\s+/g, ' ').trim();
    return { fixture, raiz, texto };
  }

  it('táctil y por páginas: un solo aviso, con la palabra y el deslizar juntos', async () => {
    tactil(true);
    const { raiz, texto } = await montar('paginas');
    const avisos = raiz.querySelectorAll('.pista, .pista-paginas');
    expect(avisos).toHaveLength(1);
    expect(texto(avisos[0])).toBe('Mantén presionada una palabra para ver qué significa; desliza para cambiar de página.');
  });

  it('con ratón y seguido: el doble clic, sin hablar de páginas', async () => {
    tactil(false);
    const { raiz, texto } = await montar('rollo');
    expect(raiz.querySelectorAll('.pista, .pista-paginas')).toHaveLength(1);
    expect(texto(raiz.querySelector('.pista'))).toBe('Haz doble clic en una palabra para ver qué significa.');
  });

  it('✕ lo cierra para siempre en este navegador, y «?» lo vuelve a enseñar', async () => {
    tactil(true);
    const { fixture, raiz } = await montar('paginas');
    (raiz.querySelector('.pista button') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(raiz.querySelector('.pista')).toBeNull();
    fixture.destroy();

    const otra = await montar('paginas');
    expect(otra.raiz.querySelector('.pista')).toBeNull();
    const ayuda = otra.raiz.querySelector('.herramientas button.ayuda') as HTMLButtonElement;
    expect(ayuda.textContent?.trim()).toBe('?');
    ayuda.click();
    otra.fixture.detectChanges();
    expect(otra.texto(otra.raiz.querySelector('.pista'))).toContain('Mantén presionada una palabra');
  });
});
