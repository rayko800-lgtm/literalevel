import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, RouterOutlet, provideRouter } from '@angular/router';
import { Sesion } from '../nucleo/sesion';
import { Inicio } from '../pantallas/inicio';
import { Ajustes } from './ajustes';

@Component({ selector: 'app-lector-falso', template: '<p>lector</p>' })
class LectorFalso {}

@Component({ selector: 'app-nivel-falso', template: '<p>nivel</p>' })
class NivelFalso {}

@Component({ selector: 'app-raiz-prueba', imports: [RouterOutlet], template: '<router-outlet />' })
class Raiz {}

/** Tanda 3 de la ayuda (Miguel, sobre el informe de Ismael): la bienvenida de tres pasos sale
 *  solo en la primera visita a Inicio, nunca encima de un enlace directo al lector; «Saltar» en
 *  cada paso; guardada en el navegador; «Ver la bienvenida otra vez» en Ajustes; y el último paso
 *  con «Medir mi nivel» y «Solo quiero leer». */
describe('Bienvenida', () => {
  const CLAVE = 'literalevel.bienvenida';

  beforeEach(async () => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    await TestBed.configureTestingModule({
      imports: [Raiz],
      providers: [
        provideRouter([
          { path: '', component: Inicio },
          { path: 'leer/:id/:cap', component: LectorFalso },
          { path: 'nivel', component: NivelFalso },
        ]),
        provideHttpClient(), provideHttpClientTesting(),
      ],
    }).compileComponents();
  });

  async function en(ruta: string) {
    const fixture = TestBed.createComponent(Raiz);
    const router = TestBed.inject(Router);
    await router.navigateByUrl(ruta);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const raiz = fixture.nativeElement as HTMLElement;
    const dialogo = () => raiz.querySelector('app-bienvenida [role=dialog]') as HTMLElement | null;
    const boton = (texto: string) => [...(dialogo()?.querySelectorAll('button') ?? [])].find(b => b.textContent?.trim().startsWith(texto)) as HTMLButtonElement | undefined;
    const pulsar = async (texto: string) => { boton(texto)!.click(); fixture.detectChanges(); await fixture.whenStable(); fixture.detectChanges(); };
    return { fixture, router, raiz, dialogo, boton, pulsar };
  }

  it('primera visita a Inicio: tres pasos, con «Saltar» en cada uno y el final con sus dos botones', async () => {
    const { dialogo, boton, pulsar } = await en('/');
    expect(dialogo()?.textContent).toContain('1 de 3');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('Libros en inglés a tu nivel');
    expect(dialogo()?.textContent).toContain('Medimos qué tan difícil es cada capítulo para que elijas uno a tu medida.');
    expect(dialogo()?.textContent).not.toContain('terminar');
    expect(boton('Saltar')).toBeTruthy();
    await pulsar('Siguiente');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('Una palabra, en su frase');
    // Sin cuenta no hay «qué significa ahí» (OpenAI): no se promete.
    expect(dialogo()?.textContent).toContain('una palabra: te decimos qué significa y cómo se pronuncia.');
    expect(dialogo()?.textContent).not.toContain('ahí');
    expect(boton('Saltar')).toBeTruthy();
    await pulsar('Siguiente');
    expect(dialogo()?.textContent).toContain('3 de 3');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Por dónde empiezas?');
    // Seis pasos: tres preguntas y tres fragmentos, como nivel.ts:17 y los documentos.
    expect(dialogo()?.textContent).toContain('Mide tu nivel con tres preguntas y tres fragmentos, o ve directo a un libro. Nada de esto pide cuenta.');
    expect(dialogo()?.textContent).not.toContain('seis preguntas');
    expect(dialogo()?.textContent).not.toContain('pronunci');
    expect(boton('Saltar')).toBeTruthy();
    expect(boton('Medir mi nivel')).toBeTruthy();
    expect(boton('Solo quiero leer')).toBeTruthy();
    expect(boton('Siguiente')).toBeUndefined();
  });

  it('Tab no sale de la tarjeta: del último botón vuelve a «Saltar», y Mayús+Tab al revés', async () => {
    const { fixture, dialogo, boton } = await en('/');
    document.body.appendChild(fixture.nativeElement);
    const tab = (shiftKey = false) => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey, bubbles: true, cancelable: true }));
    boton('Siguiente')!.focus();
    tab();
    expect(document.activeElement).toBe(boton('Saltar'));
    tab(true);
    expect(document.activeElement).toBe(boton('Siguiente'));
    // Desde el título (donde se pone el foco al abrir), Tab entra en los botones de la tarjeta.
    (dialogo()!.querySelector('h2') as HTMLElement).focus();
    tab();
    expect(document.activeElement).toBe(boton('Saltar'));
    fixture.nativeElement.remove();
  });

  it('«Saltar» la cierra y queda guardada: no vuelve a salir', async () => {
    const { dialogo, pulsar, fixture } = await en('/');
    await pulsar('Saltar');
    expect(dialogo()).toBeNull();
    expect(localStorage.getItem(CLAVE)).toBe('vista');
    fixture.destroy();
    TestBed.inject(Sesion).bienvenida.set(false);
    const otra = await en('/');
    expect(otra.dialogo()).toBeNull();
  });

  it('«Medir mi nivel» lleva a Tu nivel y «Solo quiero leer», al libro', async () => {
    const a = await en('/');
    await a.pulsar('Siguiente'); await a.pulsar('Siguiente');
    await a.pulsar('Medir mi nivel');
    expect(a.router.url).toBe('/nivel');
    expect(localStorage.getItem(CLAVE)).toBe('vista');

    TestBed.inject(Sesion).verBienvenidaOtraVez();
    const b = await en('/');
    await b.pulsar('Siguiente'); await b.pulsar('Siguiente');
    await b.pulsar('Solo quiero leer');
    expect(b.router.url).toBe('/leer/PG11/auto');
  });

  it('nunca sale encima de un enlace directo al lector', async () => {
    const { raiz } = await en('/leer/PG11/3');
    expect(raiz.textContent).toContain('lector');
    expect(raiz.querySelector('app-bienvenida')).toBeNull();
    expect(TestBed.inject(Sesion).bienvenida()).toBe(true);
  });

  it('Ajustes: «Ver la bienvenida otra vez» la vuelve a pedir', async () => {
    localStorage.setItem(CLAVE, 'vista');
    const sesion = TestBed.inject(Sesion);
    sesion.bienvenida.set(false);
    const fixture = TestBed.createComponent(Ajustes);
    fixture.detectChanges();
    await fixture.whenStable();
    const enlace = [...(fixture.nativeElement as HTMLElement).querySelectorAll('a')].find(a => a.textContent?.includes('Ver la bienvenida otra vez')) as HTMLAnchorElement;
    expect(enlace).toBeTruthy();
    enlace.click();
    expect(sesion.bienvenida()).toBe(true);
    expect(localStorage.getItem(CLAVE)).toBeNull();
  });
});
