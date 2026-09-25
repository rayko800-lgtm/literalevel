import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { Api, Capitulo, Libro } from '../nucleo/api';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';
import { Tutorial } from '../nucleo/tutorial';
import { Lector } from './lector';

/** D2 (hardening): confirma por prueba, no solo por lectura de código, el
 *  contrato del que depende «Continuar leyendo»: abrir un capítulo de
 *  verdad es el ÚNICO evento que actualiza la lectura actual (biblioteca.
 *  anotar() en el servidor, vía PUT progreso), y `literalevel.pos.<id>.<cap>`
 *  restaura la posición dentro del capítulo, con degradación segura si está
 *  corrupta. No se ha tocado `lector.ts` para escribir estas pruebas — solo
 *  se cubre el comportamiento ya existente. */
describe('Lector: progreso, posición y "lectura actual"', () => {
  const LIBRO: Libro = {
    id: 'PG11', titulo: 'Alice', autor: 'Carroll', palabras: 100, inicial: 1, dificultad: null, cefr: null,
    fuente_dificultad: null,
    capitulos: [{ indice: 0, titulo: 'Portada', palabras: 10 }, { indice: 1, titulo: 'CHAPTER I', palabras: 90 }],
    ficha: null, sugeridos: [], sinopsis: null,
  };
  const capitulo = (n: number): Capitulo =>
    ({ libro_id: 'PG11', indice: n, total: 2, titulo: `CAP ${n}`, palabras: 90, parrafos: ['Texto.'] });

  let apiProgreso: ReturnType<typeof vi.fn>;
  let apiCapitulo: ReturnType<typeof vi.fn>;
  let refrescar: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    apiProgreso = vi.fn(() => of({ ok: true }));
    apiCapitulo = vi.fn((_id: string, n: number) => of(capitulo(n)));
    refrescar = vi.fn(async () => {});
    await TestBed.configureTestingModule({
      imports: [Lector],
      providers: [
        provideRouter([]),
        { provide: Api, useValue: { capitulo: apiCapitulo, progreso: apiProgreso, palabra: vi.fn() } },
        {
          provide: Sesion,
          useValue: {
            libro: vi.fn(async () => LIBRO), perfil: signal(null), entrada: signal(null), inicio: signal(null),
            refrescar, ajustesAbiertos: signal(false), abrirPerfil: vi.fn(),
          },
        },
        { provide: Tutorial, useValue: { notificarLector: vi.fn() } },
      ],
    }).compileComponents();
  });

  async function montar(id: string, cap: string, modo: 'rollo' | 'paginas' = 'rollo') {
    TestBed.inject(Preferencias).modoLectura.set(modo);
    const fixture = TestBed.createComponent(Lector);
    fixture.componentRef.setInput('id', id);
    fixture.componentRef.setInput('cap', cap);
    fixture.detectChanges();
    for (let i = 0; i < 4; i++) { await fixture.whenStable(); fixture.detectChanges(); }
    // `restaurarPosicion()` cuelga de un doble requestAnimationFrame anidado
    // (esperar al pintado antes de medir): un flush de temporizador real deja
    // que ambos se resuelvan antes de mirar el resultado.
    await new Promise(r => setTimeout(r, 50));
    fixture.detectChanges();
    return { fixture, c: fixture.componentInstance as unknown as { avance: { set(n: number): void } } };
  }

  it('abrir un capítulo real dispara PUT progreso con el id y el índice correctos', async () => {
    await montar('PG11', '1');
    expect(apiProgreso).toHaveBeenCalledWith('PG11', 1);
  });

  it('tras el PUT progreso, se refresca Sesion (para que seguir() quede al día)', async () => {
    await montar('PG11', '1');
    expect(refrescar).toHaveBeenCalled();
  });

  it('cambiar de capítulo dispara otro PUT progreso con el nuevo índice (seguir() cambiaría con él)', async () => {
    const { fixture } = await montar('PG11', '1');
    apiProgreso.mockClear();
    refrescar.mockClear();
    fixture.componentRef.setInput('cap', '0');
    fixture.detectChanges();
    for (let i = 0; i < 4; i++) { await fixture.whenStable(); fixture.detectChanges(); }
    expect(apiProgreso).toHaveBeenCalledWith('PG11', 0);
    expect(refrescar).toHaveBeenCalled();
  });

  describe('posición dentro del capítulo (literalevel.pos.<id>.<cap>)', () => {
    it('con una fracción guardada válida, restaura scroll más allá del reinicio inicial', async () => {
      localStorage.setItem('literalevel.pos.PG11.1', '0.5000');
      const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
      await montar('PG11', '1', 'rollo');
      // Una llamada la hace `cargar()` al entrar (reset a 0); si la posición
      // guardada es válida, `restaurarPosicion()` hace una SEGUNDA llamada.
      expect(scrollTo.mock.calls.length).toBeGreaterThanOrEqual(2);
      scrollTo.mockRestore();
    });

    it('posición corrupta (no numérica): degrada a 0, sin lanzar y sin restaurar de más', async () => {
      localStorage.setItem('literalevel.pos.PG11.1', 'no-es-un-numero');
      const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
      await expect(montar('PG11', '1', 'rollo')).resolves.toBeTruthy(); // no lanza
      // Sin fracción válida (cae a 0), `restaurarPosicion()` no hace la
      // segunda llamada: solo queda el reinicio de `cargar()`.
      expect(scrollTo.mock.calls.length).toBe(1);
      scrollTo.mockRestore();
    });

    it('sin nada guardado: mismo comportamiento seguro que corrupta (primera visita a ese capítulo)', async () => {
      const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
      await montar('PG11', '1', 'rollo');
      expect(scrollTo.mock.calls.length).toBe(1);
      scrollTo.mockRestore();
    });
  });
});
