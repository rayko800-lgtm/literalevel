import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { Entrada } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Tutorial } from '../nucleo/tutorial';
import { Spotlight } from './spotlight';

/** Overlay del tutorial guiado v2, D1.2: tarjetas de elección, objetivos
 *  reales (D1.1, reutilizado en `nivel-final`), y la píldora no modal de
 *  los pasos silenciosos (checkpoints y el cuestionario de nivel). Nunca a
 *  la vez que Ajustes; siempre se puede cerrar. */
describe('Spotlight (D1.2)', () => {
  @Component({ selector: 'app-falsa', template: '<p>falsa</p>' })
  class Falsa {}

  @Component({ selector: 'app-raiz-prueba', imports: [Spotlight], template: '<app-spotlight />' })
  class Raiz {}

  const CLAVE_DEV = 'literalevel.tutorial-dev';
  const AUTENTICADA: Entrada = { puerta: true, dentro: true, nombre: 'miguel', restantes: null, openai: true, mensaje: '' };

  beforeEach(() => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    try { localStorage.setItem(CLAVE_DEV, 'on'); } catch { /* sin almacenamiento */ }
    TestBed.configureTestingModule({
      imports: [Raiz],
      providers: [
        provideRouter([
          { path: 'encontrar', component: Falsa },
          { path: 'nivel', component: Falsa },
          { path: 'palabras', component: Falsa },
          { path: 'pronunciar', component: Falsa },
        ]),
        provideHttpClient(), provideHttpClientTesting(),
      ],
    });
  });

  function montar() {
    const fixture = TestBed.createComponent(Raiz);
    document.body.appendChild(fixture.nativeElement);
    const tutorial = TestBed.inject(Tutorial);
    const sesion = TestBed.inject(Sesion);
    const raiz = fixture.nativeElement as HTMLElement;
    const dialogo = () => raiz.querySelector('[role=dialog]') as HTMLElement | null;
    const pildora = () => raiz.querySelector('.pildora-tutorial') as HTMLElement | null;
    const boton = (texto: string) => [...(dialogo()?.querySelectorAll('button') ?? [])]
      .find(b => b.textContent?.trim().startsWith(texto)) as HTMLButtonElement | undefined;
    const pulsar = (texto: string) => { boton(texto)!.click(); fixture.detectChanges(); };
    return { fixture, tutorial, sesion, raiz, dialogo, pildora, boton, pulsar };
  }

  afterEach(() => {
    document.querySelectorAll('app-raiz-prueba').forEach(n => n.remove());
  });

  it('no muestra nada si el tutorial no está activo', () => {
    const { fixture, dialogo, pildora } = montar();
    fixture.detectChanges();
    expect(dialogo()).toBeNull();
    expect(pildora()).toBeNull();
  });

  it('cuenta-eleccion: tarjeta con sus dos opciones, sin «Siguiente» genérico', () => {
    const { fixture, tutorial, dialogo, boton } = montar();
    tutorial.iniciar(); // sesión desconocida al llegar aquí: queda oculto hasta saberse anónima
    TestBed.inject(Sesion).entrada.set({ puerta: true, dentro: false, nombre: null, restantes: null, openai: true, mensaje: '' });
    fixture.detectChanges();
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Ya tienes cuenta?');
    expect(boton('Entrar')).toBeTruthy();
    expect(boton('Continuar sin cuenta')).toBeTruthy();
    expect(boton('Siguiente')).toBeUndefined();
    expect(boton('Terminar')).toBeUndefined();
  });

  it('elegir una opción llama a tutorial.elegir() y la tarjeta pasa al siguiente paso', () => {
    const { fixture, tutorial, dialogo, pulsar } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Qué quieres hacer?');
    pulsar('🧠 Practicar');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Qué practicas hoy?');
  });

  it('«Atrás» solo aparece cuando tutorial.puedeAtras() es verdad', () => {
    const { fixture, tutorial, dialogo, boton, pulsar } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    expect(boton('Atrás')).toBeUndefined(); // intencion, sin historial
    pulsar('🧠 Practicar');
    expect(boton('Atrás')).toBeTruthy();
    pulsar('Atrás');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Qué quieres hacer?');
  });

  it('nunca se muestra a la vez que Ajustes', () => {
    const { fixture, tutorial, sesion, dialogo } = montar();
    tutorial.iniciar();
    sesion.entrada.set(AUTENTICADA);
    fixture.detectChanges();
    sesion.ajustesAbiertos.set(true);
    fixture.detectChanges();
    expect(dialogo()).toBeNull();
  });

  it('«Saltar» cierra el tutorial', () => {
    const { fixture, tutorial, dialogo, pulsar } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    pulsar('Saltar');
    expect(tutorial.activo()).toBe(false);
    expect(dialogo()).toBeNull();
  });

  it('Escape cierra el tutorial', () => {
    const { fixture, tutorial, dialogo } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
    fixture.detectChanges();
    expect(tutorial.activo()).toBe(false);
  });

  it('Tab no saca el foco de la tarjeta', () => {
    const { fixture, tutorial, dialogo, boton } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    const primero = boton('Saltar')!;
    const botones = dialogo()!.querySelectorAll('button') as NodeListOf<HTMLButtonElement>;
    botones[botones.length - 1].focus();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }));
    expect(document.activeElement).toBe(primero);
  });

  describe('pasos silenciosos (checkpoints y nivel-inicio): sin tarjeta, con píldora', () => {
    it('nivel-inicio no muestra tarjeta modal, solo la píldora, y no roba el foco', () => {
      const { fixture, tutorial, dialogo, pildora, pulsar } = montar();
      tutorial.iniciar();
      TestBed.inject(Sesion).entrada.set(AUTENTICADA);
      fixture.detectChanges();
      pulsar('🎯 Medir mi nivel');
      expect(dialogo()).toBeNull();
      expect(pildora()?.textContent).toContain('Midiendo tu nivel');
      expect(pildora()?.textContent).toContain('Salir');
      // No roba el foco: a diferencia de la tarjeta modal, nada aquí lo mueve.
      expect(pildora()!.contains(document.activeElement)).toBe(false);
    });

    it('«Salir» de la píldora cierra el tutorial igual que «Saltar»', () => {
      const { fixture, tutorial, pildora, pulsar } = montar();
      tutorial.iniciar();
      TestBed.inject(Sesion).entrada.set(AUTENTICADA);
      fixture.detectChanges();
      pulsar('🎯 Medir mi nivel');
      const salir = [...pildora()!.querySelectorAll('button')].find(b => b.textContent?.includes('Salir'))!;
      salir.click();
      fixture.detectChanges();
      expect(tutorial.activo()).toBe(false);
    });

    it('un checkpoint (encontrar-inicio) tampoco muestra tarjeta modal, y no bloquea nada', () => {
      const { fixture, tutorial, sesion, dialogo, pildora, pulsar } = montar();
      tutorial.iniciar();
      sesion.entrada.set(AUTENTICADA);
      sesion.perfil.set({
        nivel: 1.2, banda: 'intermedio', origen: 'cuestionario', creado: '',
        nombre: '', objetivo: 1.2, rango_recomendado: [1, 1.4], cefr: 'B2',
      });
      fixture.detectChanges();
      pulsar('📖 Leer');
      expect(dialogo()).toBeNull();
      expect(pildora()).toBeTruthy();
      expect(tutorial.activo()).toBe(true); // no completado
    });

    it('la píldora desaparece al llegar a nivel-final (deja de ser silencioso)', () => {
      const { fixture, tutorial, sesion, dialogo, pildora, pulsar } = montar();
      tutorial.iniciar();
      sesion.entrada.set(AUTENTICADA);
      fixture.detectChanges();
      pulsar('🎯 Medir mi nivel');
      expect(pildora()).toBeTruthy();
      sesion.perfil.set({
        nivel: 1.2, banda: 'intermedio', origen: 'cuestionario', creado: '',
        nombre: '', objetivo: 1.2, rango_recomendado: [1, 1.4], cefr: 'B2',
      });
      TestBed.tick();
      fixture.detectChanges();
      expect(pildora()).toBeNull();
      expect(dialogo()).toBeTruthy();
    });
  });

  describe('nivel-final: objetivo real, avanza sin «Siguiente»', () => {
    function abrirNivelFinal(fixture: ReturnType<typeof montar>['fixture'], tutorial: Tutorial, sesion: Sesion) {
      tutorial.iniciar();
      sesion.entrada.set(AUTENTICADA);
      fixture.detectChanges();
      const boton = [...(fixture.nativeElement as HTMLElement).querySelectorAll('button')]
        .find(b => b.textContent?.trim().startsWith('🎯 Medir mi nivel')) as HTMLButtonElement;
      boton.click();
      fixture.detectChanges();
      sesion.perfil.set({
        nivel: 1.2, banda: 'intermedio', origen: 'cuestionario', creado: '',
        nombre: '', objetivo: 1.2, rango_recomendado: [1, 1.4], cefr: 'B2',
      });
      TestBed.tick();
      fixture.detectChanges();
    }

    it('sin el elemento real en pantalla: tarjeta centrada con «Reintentar», nunca «Siguiente»', async () => {
      const { fixture, tutorial, sesion, dialogo, boton } = montar();
      abrirNivelFinal(fixture, tutorial, sesion);
      await new Promise(r => setTimeout(r, 1700)); // agota el margen de espera del objetivo
      fixture.detectChanges();
      expect(dialogo()?.textContent).toContain('No encuentro esa parte de la pantalla ahora mismo.');
      expect(boton('Reintentar')).toBeTruthy();
      expect(boton('Siguiente')).toBeUndefined();
      expect(boton('Saltar')).toBeTruthy(); // sigue siendo posible cerrarlo
    });

    it('con el elemento real en pantalla, se posiciona sobre él sin esperar', () => {
      const marca = document.createElement('a');
      marca.setAttribute('data-tutorial', 'nivel-ver-libros');
      document.body.appendChild(marca);
      const { fixture, tutorial, sesion, dialogo } = montar();
      abrirNivelFinal(fixture, tutorial, sesion);
      expect(dialogo()?.classList.contains('centrada')).toBe(false);
      marca.remove();
    });

    it('avanza al checkpoint encontrar-inicio cuando el router navega a /encontrar (el clic real en el botón de la app), no por un botón del tutorial', async () => {
      const { fixture, tutorial, sesion } = montar();
      abrirNivelFinal(fixture, tutorial, sesion);
      expect(tutorial.pasoActual()?.id).toBe('nivel-final');
      await TestBed.inject(Router).navigateByUrl('/encontrar');
      expect(tutorial.pasoActual()?.id).toBe('encontrar-inicio');
      expect(tutorial.activo()).toBe(true);
    });
  });
});
