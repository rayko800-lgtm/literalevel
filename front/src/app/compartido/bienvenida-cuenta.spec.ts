import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, RouterOutlet, provideRouter } from '@angular/router';
import { Entrada } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Inicio } from '../pantallas/inicio';

@Component({ selector: 'app-raiz-cuenta', imports: [RouterOutlet], template: '<router-outlet />' })
class Raiz {}

/** El paso 0 de la bienvenida (Miguel, 16 sep; diseño de 4e en
 *  auditoria/introduccion_al_abrir_4e_2026-09-16.md; texto «con cuenta» de la Central):
 *  sin cuenta pregunta por ella y dice lo que sí se puede; con cuenta, la primera vez que se
 *  entra, dice qué gasta usos. Dos marcas: quien ya la vio sin cuenta la ve una vez más al
 *  entrar, y quien entra la primera vez no la ve dos veces. */
describe('Bienvenida: el paso 0 y la cuenta', () => {
  const SIN = 'literalevel.bienvenida';
  const CON = 'literalevel.bienvenida-cuenta';
  const entrada = (dentro: boolean): Entrada =>
    ({ puerta: true, dentro, nombre: dentro ? 'miguel' : null, restantes: dentro ? 5 : null, openai: true, mensaje: '' });

  beforeEach(async () => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    await TestBed.configureTestingModule({
      imports: [Raiz],
      providers: [provideRouter([{ path: '', component: Inicio }]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  async function inicio() {
    const fixture = TestBed.createComponent(Raiz);
    await TestBed.inject(Router).navigateByUrl('/');
    const pintar = async () => { fixture.detectChanges(); await fixture.whenStable(); fixture.detectChanges(); };
    await pintar();
    const raiz = fixture.nativeElement as HTMLElement;
    const dialogo = () => raiz.querySelector('app-bienvenida [role=dialog]') as HTMLElement | null;
    const botones = () => [...(dialogo()?.querySelectorAll('.acciones-b button') ?? [])] as HTMLButtonElement[];
    const boton = (t: string) => [...(dialogo()?.querySelectorAll('button') ?? [])].find(b => b.textContent?.trim() === t) as HTMLButtonElement | undefined;
    const pulsar = async (t: string) => { boton(t)!.click(); await pintar(); };
    return { fixture, dialogo, botones, boton, pulsar, pintar };
  }

  it('sin cuenta: pregunta por ella, dice lo que sí se puede y ofrece dos salidas iguales', async () => {
    TestBed.inject(Sesion).entrada.set(entrada(false));
    const { dialogo, botones, boton } = await inicio();
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Ya tienes cuenta?');
    expect(dialogo()?.querySelector('p')?.textContent).toBe(
      'Con cuenta te corrijo la pronunciación y te explico una palabra en su frase. Sin cuenta puedes leer, buscar, medir tu nivel y grabarte.');
    expect(botones().map(b => b.textContent?.trim())).toEqual(['Entrar', 'Seguir sin cuenta']);
    // «Del mismo tamaño»: los dos son botones de bloque, a todo el ancho.
    expect(botones().every(b => b.classList.contains('bloque'))).toBe(true);
    expect(boton('Saltar')).toBeTruthy();
    expect(boton('Siguiente')).toBeUndefined();
  });

  it('«Entrar» cierra la bienvenida y abre Ajustes en «Tu perfil»', async () => {
    const sesion = TestBed.inject(Sesion);
    sesion.entrada.set(entrada(false));
    const { dialogo, pulsar } = await inicio();
    await pulsar('Entrar');
    expect(dialogo()).toBeNull();
    expect(sesion.ajustesAbiertos()).toBe(true);
    expect(sesion.ajustesEnPerfil()).toBe(true);
    expect(localStorage.getItem(SIN)).toBe('vista');
  });

  it('con cuenta: el paso 0 dice qué gasta usos, sin preguntar, y sigue con «Siguiente»', async () => {
    TestBed.inject(Sesion).entrada.set(entrada(true));
    const { dialogo, botones, boton } = await inicio();
    expect(dialogo()?.textContent).toContain('1 de 4');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('Ya tienes cuenta');
    expect(dialogo()?.querySelector('p')?.textContent).toBe(
      'Con tu cuenta te corrijo la pronunciación y te explico cada palabra en su frase. Cada una de esas dos cosas gasta un uso.');
    expect(botones().map(b => b.textContent?.trim())).toEqual(['Siguiente']);
    expect(boton('Entrar')).toBeUndefined();
    expect(boton('Saltar')).toBeTruthy();
  });

  it('quien ya la vio sin cuenta la ve una vez más al entrar, y después no', async () => {
    const sesion = TestBed.inject(Sesion);
    sesion.entrada.set(entrada(false));
    const a = await inicio();
    await a.pulsar('Saltar');
    expect(localStorage.getItem(SIN)).toBe('vista');
    expect(localStorage.getItem(CON)).toBeNull();
    // Entra con su perfil: vuelve a salir, ya en su versión con cuenta.
    sesion.entrada.set(entrada(true));
    await a.pintar();
    expect(a.dialogo()?.querySelector('h2')?.textContent).toBe('Ya tienes cuenta');
    await a.pulsar('Saltar');
    expect(localStorage.getItem(CON)).toBe('vista');
    // Y no vuelve, aunque salga y entre otra vez.
    sesion.entrada.set(entrada(false));
    sesion.entrada.set(entrada(true));
    await a.pintar();
    expect(a.dialogo()).toBeNull();
  });

  it('quien entra la primera vez ya con cuenta la ve una sola vez, no dos', async () => {
    const sesion = TestBed.inject(Sesion);
    sesion.entrada.set(entrada(true));
    const a = await inicio();
    expect(a.dialogo()?.querySelector('h2')?.textContent).toBe('Ya tienes cuenta');
    await a.pulsar('Saltar');
    expect(localStorage.getItem(SIN)).toBe('vista');
    expect(localStorage.getItem(CON)).toBe('vista');
    sesion.entrada.set(entrada(false));
    await a.pintar();
    expect(a.dialogo()).toBeNull();
  });

  it('no sale encima de Ajustes abierto', async () => {
    const sesion = TestBed.inject(Sesion);
    sesion.entrada.set(entrada(false));
    sesion.ajustesAbiertos.set(true);
    const a = await inicio();
    expect(a.dialogo()).toBeNull();
    sesion.ajustesAbiertos.set(false);
    await a.pintar();
    expect(a.dialogo()).not.toBeNull();
  });
});
