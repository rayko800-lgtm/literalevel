import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { EntradaBiblioteca } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { LeerEntrada } from './leer-entrada';

/** D2 (hardening): `LeerEntrada` (la pantalla que resuelve `/leer` sin
 *  id/cap) ya reenviaba a `sesion.inicio()?.seguir` desde antes de D2.
 *  Cierra el hueco de cobertura, sin tocar `leer-entrada.ts`. */
describe('LeerEntrada: /leer sin id resuelve al último libro real', () => {
  @Component({ selector: 'app-falsa', template: '<p>falsa</p>' })
  class Falsa {}

  const SEGUIR: EntradaBiblioteca = {
    id: 'PG11', titulo: 'Alice', autor: 'Carroll', capitulo: 3, capitulos: 12,
    avance: 0.27, palabras: 500, visto: '', consultadas: 0,
  };

  function proveer(motor: ReturnType<typeof signal<string>>, seguir: EntradaBiblioteca | null) {
    return TestBed.configureTestingModule({
      imports: [LeerEntrada],
      providers: [
        provideRouter([{ path: 'leer/:id/:cap', component: Falsa }, { path: 'encontrar', component: Falsa }]),
        {
          provide: Sesion,
          useValue: {
            motor, refrescar: vi.fn(async () => {}), inicio: signal({ seguir }),
          },
        },
      ],
    }).compileComponents();
  }

  it('sin seguir: muestra la entrada normal (sin CTA roto)', async () => {
    await proveer(signal('listo'), null);
    const fixture = TestBed.createComponent(LeerEntrada);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const raiz = fixture.nativeElement as HTMLElement;
    expect(raiz.textContent).toContain('Todavía no estás leyendo nada');
    const enlaces = [...raiz.querySelectorAll('a')];
    expect(enlaces.some(a => a.textContent?.includes('Abrir Alicia'))).toBe(true);
    expect(enlaces.some(a => a.textContent?.includes('Elegir otro libro'))).toBe(true);
  });

  it('con seguir: navega directamente a /leer/:id/:cap (replaceUrl)', async () => {
    await proveer(signal('listo'), SEGUIR);
    const router = TestBed.inject(Router);
    const fixture = TestBed.createComponent(LeerEntrada);
    fixture.detectChanges();
    await fixture.whenStable();
    await new Promise(r => setTimeout(r, 0)); // deja asentar router.navigate()
    fixture.detectChanges();
    expect(router.url).toBe('/leer/PG11/3');
  });

  it('espera a que motor esté listo antes de decidir: sin navegar mientras "comprobando"', async () => {
    const motor = signal('comprobando');
    await proveer(motor, SEGUIR);
    const router = TestBed.inject(Router);
    const fixture = TestBed.createComponent(LeerEntrada);
    fixture.detectChanges();
    await fixture.whenStable();
    await new Promise(r => setTimeout(r, 0));
    fixture.detectChanges();
    expect(router.url).not.toBe('/leer/PG11/3'); // todavía no decidió nada
    const raiz = fixture.nativeElement as HTMLElement;
    expect(raiz.textContent).toContain('Buscando dónde lo dejaste');
    // Ahora el motor está listo: recién entonces decide.
    motor.set('listo');
    fixture.detectChanges();
    await fixture.whenStable();
    await new Promise(r => setTimeout(r, 0));
    fixture.detectChanges();
    expect(router.url).toBe('/leer/PG11/3');
  });

  it('no genera flash falso: con el motor caído, muestra la entrada normal (no queda "buscando" para siempre)', async () => {
    const motor = signal('caido');
    await proveer(motor, null);
    const fixture = TestBed.createComponent(LeerEntrada);
    fixture.detectChanges();
    const raiz = fixture.nativeElement as HTMLElement;
    expect(raiz.textContent).not.toContain('Buscando dónde lo dejaste');
    expect(raiz.textContent).toContain('Todavía no estás leyendo nada');
  });
});
