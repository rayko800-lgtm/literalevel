import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Api, Cuestionario, Perfil } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Nivel } from './nivel';

/** Propuesta A de Tu nivel (Miguel, 15 sep; auditoria/esmeralda_ux_2026-09-15.md): seis
 *  preguntas sin «Me vale así» ni nivel provisional, se guarda solo al contestar la sexta,
 *  y el resultado es el nivel con un botón; afinar queda como enlace pequeño. */
describe('Tu nivel (propuesta A)', () => {
  const opciones = [{ etiqueta: 'Poco', valor: 0.4 }, { etiqueta: 'Mucho', valor: 1.2 }];
  const pregunta = (clave: string) => ({ clave, pregunta: `¿${clave}?`, opciones, multiple: false });
  const fragmento = (clave: string) => ({ ...pregunta(clave), texto: 'Alice was beginning…', obra: 'Alice', autor: 'Carroll',
    nivel_cefr: 'B1', fuente: 'PG' });
  const CUESTIONARIO: Cuestionario = {
    preguntas: ['frecuencia', 'libro_completo', 'comprension', 'diccionario', 'series', 'lecturas'].map(pregunta),
    fragmentos: ['fragmento_facil', 'fragmento_medio', 'fragmento_dificil'].map(fragmento),
    peso_fragmentos: 0.65,
  };
  const PERFIL: Perfil = { nivel: 1.2, banda: 'intermedio', origen: 'cuestionario', creado: '', nombre: '', objetivo: 1.2,
    rango_recomendado: [0.95, 1.45], cefr: 'B2' };
  const SEIS = ['frecuencia', 'fragmento_facil', 'libro_completo', 'fragmento_medio', 'comprension', 'fragmento_dificil'];

  let api: { cuestionario: ReturnType<typeof vi.fn>; perfilDesdeCuestionario: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    api = { cuestionario: vi.fn(() => of(CUESTIONARIO)), perfilDesdeCuestionario: vi.fn(() => of(PERFIL)) };
    const perfil = signal<Perfil | null>(null);
    const sesion = { perfil, inicio: signal(null), fijarPerfil: (p: Perfil | null) => perfil.set(p) };
    await TestBed.configureTestingModule({
      imports: [Nivel],
      providers: [provideRouter([]), { provide: Api, useValue: api }, { provide: Sesion, useValue: sesion }],
    }).compileComponents();
  });

  async function montar() {
    const fixture = TestBed.createComponent(Nivel);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return { fixture, c: fixture.componentInstance as any, raiz: fixture.nativeElement as HTMLElement };
  }

  async function contestarLasSeis(fixture: { detectChanges(): void; whenStable(): Promise<unknown> }, c: any) {
    c.respuestas.set(Object.fromEntries(SEIS.map(k => [k, 1.2])));
    c.paso.set(5);
    c.avanzar();
    await fixture.whenStable();
    fixture.detectChanges();
  }

  it('las preguntas: seis, sin «Me vale así», sin nivel provisional y sin otro camino al empezar', async () => {
    const { c, raiz } = await montar();
    expect(raiz.textContent).toContain('1 de 6');
    expect(raiz.textContent).not.toContain('Me vale así');
    expect(raiz.textContent).not.toContain('Estimación provisional');
    expect(raiz.textContent).not.toContain('mídete con un libro');
    c.elegir(1.2);                                        // contestar no pide ninguna estimación
    expect(api.perfilDesdeCuestionario).not.toHaveBeenCalled();
  });

  it('al contestar la sexta se guarda solo y enseña el nivel con un botón; afinar es un enlace pequeño', async () => {
    const { fixture, c, raiz } = await montar();
    await contestarLasSeis(fixture, c);
    expect(api.perfilDesdeCuestionario).toHaveBeenCalledOnce();
    const [respuestas, guardar] = api.perfilDesdeCuestionario.mock.calls[0];
    expect(Object.keys(respuestas).sort()).toEqual([...SEIS].sort());
    expect(guardar).toBe(true);
    expect(c.vista()).toBe('resultado');
    const texto = raiz.textContent ?? '';
    expect(raiz.querySelector('h1')?.textContent).toContain('Lees en inglés a nivel B2');
    expect(texto).toContain('Ver libros de mi nivel');
    const detalle = raiz.querySelector('details.detalle-nivel') as HTMLDetailsElement;
    expect(detalle.open).toBe(false);
    expect(detalle.textContent).toContain('1,20');
    expect(raiz.querySelector('.afinar-pie')?.textContent).toContain('Afínalo con un libro que ya leíste');
    expect(raiz.querySelector('.afinar-pie')?.textContent).toContain('volver a medirme');
    for (const viejo of ['Guardar mi nivel', 'Afinar con 3 preguntas más', 'Ya está', 'Cambiar una respuesta']) {
      expect(texto).not.toContain(viejo);
    }
  });

  it('si guardar falla se queda en la sexta con el error, y «Ver mi nivel» lo reintenta', async () => {
    api.perfilDesdeCuestionario.mockReturnValueOnce(throwError(() => new Error('sin red')));
    const { fixture, c, raiz } = await montar();
    await contestarLasSeis(fixture, c);
    expect(c.vista()).toBe('preguntas');
    expect(raiz.querySelector('[role=alert]')).not.toBeNull();
    expect(raiz.textContent).toContain('Ver mi nivel');
    c.avanzar();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(api.perfilDesdeCuestionario).toHaveBeenCalledTimes(2);
    expect(c.vista()).toBe('resultado');
  });
});
