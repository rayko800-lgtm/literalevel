import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { EntradaBiblioteca, Inicio as InicioApi } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Inicio } from './inicio';

/** D2 (hardening): `sesion.inicio()?.seguir` ya alimentaba el CTA «Seguir
 *  leyendo» del héroe y la tarjeta «Donde lo dejaste» desde antes de D2 —
 *  esto solo cierra el hueco de cobertura que dejaba esa capacidad sin
 *  ningún test. No se ha tocado `inicio.ts` para escribir estas pruebas. */
describe('Inicio: CTA de continuar leyendo', () => {
  const SEGUIR: EntradaBiblioteca = {
    id: 'PG11', titulo: 'Alice in Wonderland', autor: 'Lewis Carroll',
    capitulo: 3, capitulos: 12, avance: 0.273, palabras: 500, visto: '', consultadas: 2,
    titulo_capitulo: 'CHAPTER IV', extracto: 'Down, down, down.',
  };
  const inicioBase = (seguir: EntradaBiblioteca | null): InicioApi => ({
    perfil: null, seguir, libros: 0, cuaderno: { consultas: 0, palabras: 0, libros: 0 },
    entrada: { puerta: true, dentro: false, nombre: null, restantes: null, openai: true, mensaje: '' },
  });

  function proveer(inicio: ReturnType<typeof signal<InicioApi | null>>) {
    return TestBed.configureTestingModule({
      imports: [Inicio],
      providers: [
        provideRouter([]),
        {
          provide: Sesion,
          useValue: {
            inicio, perfil: signal(null), bienvenida: signal(false), ajustesAbiertos: signal(false),
            entrada: signal(null), motor: signal('listo'), sesionFallida: signal(false),
            refrescar: vi.fn(async () => {}),
          },
        },
      ],
    }).compileComponents();
  }

  function montar() {
    const fixture = TestBed.createComponent(Inicio);
    fixture.detectChanges();
    return { fixture, raiz: fixture.nativeElement as HTMLElement };
  }

  it('con seguir: el hero muestra «Seguir leyendo» hacia el libro/capítulo correctos', async () => {
    await proveer(signal(inicioBase(SEGUIR)));
    const { raiz } = montar();
    const enlace = [...raiz.querySelectorAll('a')].find(a => a.textContent?.includes('Seguir leyendo')) as HTMLAnchorElement;
    expect(enlace).toBeTruthy();
    expect(enlace.getAttribute('href')).toBe('/leer/PG11/3');
  });

  it('con seguir: la tarjeta «Donde lo dejaste» muestra título, capítulo y avance reales', async () => {
    await proveer(signal(inicioBase(SEGUIR)));
    const { raiz } = montar();
    const tarjeta = raiz.querySelector('.tarjeta.seguir') as HTMLElement;
    expect(tarjeta).toBeTruthy();
    expect(tarjeta.textContent).toContain('Alice in Wonderland');
    expect(tarjeta.textContent).toContain('Capítulo 4 de 12'); // capitulo es 0-index
    expect(tarjeta.textContent).toContain('27%'); // 0.273 → Math.round(27.3) = 27
  });

  it('sin seguir: no muestra la tarjeta «Donde lo dejaste» ni un CTA roto, cae al libro fijo', async () => {
    await proveer(signal(inicioBase(null)));
    const { raiz } = montar();
    expect(raiz.querySelector('.tarjeta.seguir')).toBeNull();
    const enlace = [...raiz.querySelectorAll('a')].find(a => a.textContent?.includes('Empezar a leer')) as HTMLAnchorElement;
    expect(enlace).toBeTruthy();
    expect(enlace.getAttribute('href')).toBe('/leer/PG11/auto');
  });

  it('inicio() todavía null (sesión no ha llegado): sin CTA roto, sin tarjeta, sin excepción', async () => {
    await proveer(signal(null));
    const { raiz } = montar();
    expect(raiz.querySelector('.tarjeta.seguir')).toBeNull();
    const enlace = [...raiz.querySelectorAll('a')].find(a => a.textContent?.includes('Empezar a leer')) as HTMLAnchorElement;
    expect(enlace).toBeTruthy(); // el CTA por defecto, nunca uno vacío
  });
});
