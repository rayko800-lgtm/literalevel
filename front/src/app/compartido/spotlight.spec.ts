import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Sesion } from '../nucleo/sesion';
import { PasoTutorial, Tutorial } from '../nucleo/tutorial';
import { Spotlight } from './spotlight';

/** Este proyecto no tiene `zone.js/testing`, así que `fakeAsync`/`tick` no
 *  están disponibles: se espera con temporizadores reales (los márgenes del
 *  propio `spotlight.ts` son cortos, 150/1500 ms, así que el coste es bajo). */
function esperar(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/** Overlay del tutorial guiado v2 (D1.1): nunca a la vez que Ajustes o la
 *  bienvenida actual, nunca bloquea si el elemento objetivo no aparece, y
 *  siempre se puede cerrar (Saltar, Escape). */
describe('Spotlight', () => {
  @Component({ selector: 'app-raiz-prueba', imports: [Spotlight], template: '<app-spotlight />' })
  class Raiz {}

  const CLAVE_DEV = 'literalevel.tutorial-dev';

  beforeEach(() => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    try { localStorage.setItem(CLAVE_DEV, 'on'); } catch { /* sin almacenamiento */ }
    TestBed.configureTestingModule({ imports: [Raiz] });
  });

  function montar() {
    const fixture = TestBed.createComponent(Raiz);
    document.body.appendChild(fixture.nativeElement);
    const tutorial = TestBed.inject(Tutorial);
    const sesion = TestBed.inject(Sesion);
    const raiz = fixture.nativeElement as HTMLElement;
    const dialogo = () => raiz.querySelector('[role=dialog]') as HTMLElement | null;
    const boton = (texto: string) => [...(dialogo()?.querySelectorAll('button') ?? [])]
      .find(b => b.textContent?.trim().startsWith(texto)) as HTMLButtonElement | undefined;
    const pulsar = (texto: string) => { boton(texto)!.click(); fixture.detectChanges(); };
    return { fixture, tutorial, sesion, raiz, dialogo, boton, pulsar };
  }

  afterEach(() => {
    document.querySelectorAll('app-raiz-prueba').forEach(n => n.remove());
  });

  it('no muestra nada si el tutorial no está activo', () => {
    const { fixture, dialogo } = montar();
    fixture.detectChanges();
    expect(dialogo()).toBeNull();
  });

  it('un paso sin objetivo muestra una tarjeta centrada de inmediato', () => {
    const { fixture, tutorial, dialogo } = montar();
    tutorial.iniciar();
    fixture.detectChanges();
    expect(dialogo()).toBeTruthy();
    expect(dialogo()?.querySelector('h2')?.textContent).toBe(tutorial.pasos[0].titulo);
    expect(dialogo()?.textContent).toContain('1 de 3');
  });

  it('nunca se muestra a la vez que Ajustes', () => {
    const { fixture, tutorial, sesion, dialogo } = montar();
    tutorial.iniciar();
    sesion.ajustesAbiertos.set(true);
    fixture.detectChanges();
    expect(dialogo()).toBeNull();
  });

  it('al activarse cierra la bienvenida actual, para que nunca compitan por el foco', () => {
    const { fixture, tutorial, sesion, dialogo } = montar();
    sesion.bienvenida.set(true); // como un visitante nuevo, antes de activar el tutorial
    tutorial.iniciar();
    fixture.detectChanges();
    expect(sesion.bienvenida()).toBe(false);
    expect(dialogo()).toBeTruthy();
  });

  it('«Saltar» cierra el tutorial', () => {
    const { fixture, tutorial, dialogo, pulsar } = montar();
    tutorial.iniciar();
    fixture.detectChanges();
    pulsar('Saltar');
    expect(tutorial.activo()).toBe(false);
    expect(dialogo()).toBeNull();
  });

  it('Escape cierra el tutorial', () => {
    const { fixture, tutorial, dialogo } = montar();
    tutorial.iniciar();
    fixture.detectChanges();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
    fixture.detectChanges();
    expect(tutorial.activo()).toBe(false);
    expect(dialogo()).toBeNull();
  });

  it('«Siguiente»/«Atrás» avanzan y retroceden; «Atrás» no sale en el primer paso', () => {
    const { fixture, tutorial, dialogo, boton, pulsar } = montar();
    tutorial.iniciar();
    fixture.detectChanges();
    expect(boton('Atrás')).toBeUndefined();
    pulsar('Siguiente');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe(tutorial.pasos[1].titulo);
    expect(boton('Atrás')).toBeTruthy();
    pulsar('Atrás');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe(tutorial.pasos[0].titulo);
  });

  it('en el último paso, el botón dice «Terminar» y cierra el tutorial al pulsarlo', () => {
    const { fixture, tutorial, dialogo, pulsar } = montar();
    tutorial.iniciar();
    fixture.detectChanges();
    pulsar('Siguiente');
    pulsar('Siguiente');
    expect(dialogo()?.textContent).toContain('Terminar');
    pulsar('Terminar');
    expect(tutorial.activo()).toBe(false);
  });

  describe('con un paso que apunta a un elemento real (D1.2+ lo hará así)', () => {
    function conObjetivo(objetivo: string): PasoTutorial[] {
      return [{ id: 'con-objetivo', titulo: 'Paso con objetivo', texto: 'texto', objetivo }];
    }

    it('si el elemento ya existe, se posiciona sobre él sin esperar', () => {
      const marca = document.createElement('div');
      marca.id = 'marca-existente';
      document.body.appendChild(marca);
      const { fixture, tutorial, dialogo } = montar();
      (tutorial as unknown as { pasos: PasoTutorial[] }).pasos = conObjetivo('#marca-existente');
      tutorial.iniciar();
      fixture.detectChanges();
      expect(dialogo()?.classList.contains('centrada')).toBe(false);
      expect(dialogo()?.textContent).not.toContain('No encuentro esa parte');
      marca.remove();
    });

    it('si el elemento aparece tarde (dentro del margen de espera), lo encuentra igual', async () => {
      const { fixture, tutorial, dialogo } = montar();
      (tutorial as unknown as { pasos: PasoTutorial[] }).pasos = conObjetivo('#marca-tardia');
      tutorial.iniciar();
      fixture.detectChanges();
      expect(dialogo()?.classList.contains('centrada')).toBe(true); // todavía buscando

      await esperar(300);
      const marca = document.createElement('div');
      marca.id = 'marca-tardia';
      document.body.appendChild(marca);
      await esperar(300); // el sondeo cada 150 ms lo recoge dentro del margen de 1500 ms
      fixture.detectChanges();

      expect(dialogo()?.classList.contains('centrada')).toBe(false);
      marca.remove();
    });

    it('si el elemento nunca aparece, se rinde tras el margen de espera: tarjeta centrada con «Reintentar», sin bucle infinito', async () => {
      const { fixture, tutorial, dialogo, boton } = montar();
      (tutorial as unknown as { pasos: PasoTutorial[] }).pasos = conObjetivo('#nunca-existe');
      tutorial.iniciar();
      fixture.detectChanges();

      await esperar(1800); // pasa de sobra el margen máximo de 1500 ms
      fixture.detectChanges();

      expect(dialogo()?.classList.contains('centrada')).toBe(true);
      expect(dialogo()?.textContent).toContain('No encuentro esa parte de la pantalla ahora mismo.');
      expect(boton('Reintentar')).toBeTruthy();
      // Sigue siendo posible cerrarlo: nunca un overlay imposible de cerrar.
      expect(boton('Saltar')).toBeTruthy();
    });

    it('«Reintentar» vuelve a buscar el elemento', async () => {
      const { fixture, tutorial, dialogo, pulsar } = montar();
      (tutorial as unknown as { pasos: PasoTutorial[] }).pasos = conObjetivo('#marca-para-reintentar');
      tutorial.iniciar();
      fixture.detectChanges();
      await esperar(1800);
      fixture.detectChanges();
      expect(dialogo()?.textContent).toContain('No encuentro esa parte');

      const marca = document.createElement('div');
      marca.id = 'marca-para-reintentar';
      document.body.appendChild(marca);
      pulsar('Reintentar');
      await esperar(50);
      fixture.detectChanges();

      expect(dialogo()?.classList.contains('centrada')).toBe(false);
      marca.remove();
    });
  });

  it('Tab no saca el foco de la tarjeta', () => {
    const { fixture, tutorial, dialogo, boton } = montar();
    tutorial.iniciar();
    fixture.detectChanges();
    const primero = boton('Saltar')!;
    const ultimo = (dialogo()!.querySelectorAll('button') as NodeListOf<HTMLButtonElement>);
    const ultimoBoton = ultimo[ultimo.length - 1];
    ultimoBoton.focus();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }));
    expect(document.activeElement).toBe(primero);
  });
});
