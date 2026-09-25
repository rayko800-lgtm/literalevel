import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { Api, Capitulo, Libro, Palabra } from '../nucleo/api';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';
import { Tutorial } from '../nucleo/tutorial';
import { Lector } from './lector';

/** UX-F2 (Miguel, tras D3.V): en Android/Chrome, tras capturar la palabra
 *  quedaba visible el menú nativo de selección (Copiar/Seleccionar todo,
 *  tiradores azules) hasta tocar otra zona. Ahora se limpia con
 *  `removeAllRanges()`, pero SOLO cuando la selección ya fue aceptada —
 *  nunca antes de saber que se va a usar. */
describe('Lector: limpieza de la selección nativa tras capturar (UX-F2)', () => {
  const LIBRO: Libro = {
    id: 'PG11', titulo: 'Alice', autor: 'Carroll', palabras: 100, inicial: 1, dificultad: null, cefr: null,
    fuente_dificultad: null, capitulos: [{ indice: 0, titulo: 'Portada', palabras: 10 }, { indice: 1, titulo: 'CHAPTER I', palabras: 90 }],
    ficha: null, sugeridos: [], sinopsis: null,
  };
  const CAP: Capitulo = { libro_id: 'PG11', indice: 1, total: 2, titulo: 'CHAPTER I', palabras: 90, parrafos: ['She was tired of waiting for the bell.'] };
  const PALABRA: Palabra = {
    etapa: 'diccionario', palabra: 'tired', lema: 'tired', categoria: 'adjective',
    ipa_uk: null, ipa_us: null, ipa_generada_por_ia: false, compuesto: null, parte_del_diccionario: null,
    audio_uk: null, audio_us: null, audio_generado: false, sentido: 'cansada', etiquetas: [],
    similitud: null, sentidos_candidatos: 1, dudoso: false, definicion_contextual: null, explicacion_gramatical: null,
    explicacion_adaptada: null, ejemplo: null,
  } as unknown as Palabra;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Lector],
      providers: [
        provideRouter([]),
        { provide: Api, useValue: { capitulo: vi.fn(() => of(CAP)), progreso: vi.fn(() => of({})), palabra: vi.fn(() => of(PALABRA)) } },
        {
          provide: Sesion,
          useValue: {
            libro: vi.fn(async () => LIBRO), perfil: signal(null), entrada: signal(null), inicio: signal(null),
            refrescar: vi.fn(async () => {}), ajustesAbiertos: signal(false), abrirPerfil: vi.fn(),
          },
        },
        { provide: Tutorial, useValue: { notificarLector: vi.fn() } },
      ],
    }).compileComponents();
  });

  async function montar() {
    TestBed.inject(Preferencias).modoLectura.set('rollo');
    const fixture = TestBed.createComponent(Lector);
    fixture.componentRef.setInput('id', 'PG11');
    fixture.componentRef.setInput('cap', '1');
    fixture.detectChanges();
    for (let i = 0; i < 4; i++) { await fixture.whenStable(); fixture.detectChanges(); }
    const raiz = fixture.nativeElement as HTMLElement;
    const el = raiz.querySelector('[data-tutorial="lector-texto"]') as HTMLElement;
    return { fixture, raiz, el, c: fixture.componentInstance as unknown as { capturar(): void } };
  }

  /** Un nodo de texto de verdad dentro de `.texto`, con una selección real
   *  del navegador (jsdom implementa Selection/Range, a diferencia de
   *  `scrollTo`) — no una llamada directa a `consultar()`, que saltaría
   *  exactamente el código que se quiere probar. */
  function seleccionar(el: HTMLElement, palabra: string, frase = 'She was tired of waiting for the bell.'): Selection {
    const nodo = document.createTextNode(frase);
    el.appendChild(nodo);
    const desde = frase.indexOf(palabra);
    const range = document.createRange();
    range.setStart(nodo, desde);
    range.setEnd(nodo, desde + palabra.length);
    const sel = window.getSelection()!;
    sel.removeAllRanges();
    sel.addRange(range);
    return sel;
  }

  it('selección válida: se limpia con removeAllRanges tras aceptarla, y consulta la palabra', async () => {
    const { el, c } = await montar();
    const sel = seleccionar(el, 'tired');
    expect(sel.rangeCount).toBe(1); // todavía con el menú nativo, antes de capturar
    c.capturar();
    expect(sel.rangeCount).toBe(0); // limpiada: sin Copiar/Seleccionar todo/tiradores
  });

  it('selección colapsada (sin texto): no se toca — nada que limpiar ni que usar', async () => {
    const { el, c } = await montar();
    const nodo = document.createTextNode('She was tired.');
    el.appendChild(nodo);
    const range = document.createRange();
    range.setStart(nodo, 4);
    range.setEnd(nodo, 4); // colapsado
    const sel = window.getSelection()!;
    sel.removeAllRanges();
    sel.addRange(range);
    c.capturar();
    expect(sel.rangeCount).toBe(1); // se deja tal cual, nunca se tocó
  });

  it('selección fuera de #texto: no se limpia — no es una captura válida', async () => {
    const { c } = await montar();
    const fuera = document.createElement('div');
    document.body.appendChild(fuera);
    const nodo = document.createTextNode('tired');
    fuera.appendChild(nodo);
    const range = document.createRange();
    range.setStart(nodo, 0);
    range.setEnd(nodo, 5);
    const sel = window.getSelection()!;
    sel.removeAllRanges();
    sel.addRange(range);
    c.capturar();
    expect(sel.rangeCount).toBe(1); // ajena a #texto: se ignora, no se limpia
    fuera.remove();
  });

  it('demasiadas palabras (subrayar para leer, no consultar): selección larga se deja intacta', async () => {
    const { el, c } = await montar();
    const sel = seleccionar(el, 'tired of waiting for the bell', 'She was tired of waiting for the bell.');
    c.capturar();
    expect(sel.rangeCount).toBe(1); // más de 4 palabras: no es una consulta válida
  });

  it('tras limpiar una selección, una segunda selección real sigue funcionando (no rompe el siguiente long-press)', async () => {
    const { el, c } = await montar();
    const primera = seleccionar(el, 'tired');
    c.capturar();
    expect(primera.rangeCount).toBe(0);
    const segunda = seleccionar(el, 'waiting');
    expect(segunda.rangeCount).toBe(1);
    c.capturar();
    expect(segunda.rangeCount).toBe(0); // la segunda captura también limpia la suya
  });
});
