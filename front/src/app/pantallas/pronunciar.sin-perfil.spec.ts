import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Entrada } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Pronunciar } from './pronunciar';

/** Medido a 390 px sobre el front publicado (auditoria/microfono_casos_a_b_2026-09-16.md):
 *  sin sesión, «Corrígeme» iba `disabled`, sin `title` ni `aria-describedby`, y pulsarlo no
 *  producía ninguna respuesta; la única explicación estaba 309 px más arriba. Decisión de
 *  Miguel por la Central (16 sep): el botón se pulsa, lo dice en la barra y abre Ajustes en
 *  «Tu perfil», calcado del patrón que ya funciona en el lector. */
describe('Pronunciar: «Corrígeme» sin perfil contesta en vez de estar apagado', () => {
  const fuera = (openai: boolean): Entrada =>
    ({ puerta: true, dentro: false, nombre: null, restantes: null, openai, mensaje: '' });

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  async function montarGrabada(openai: boolean) {
    const sesion = TestBed.inject(Sesion);
    sesion.entrada.set(fuera(openai));
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.frase = 'the war';
    c.blob = new Blob(['x'], { type: 'audio/webm' });
    c.estado.set('grabada');
    fixture.detectChanges();
    await fixture.whenStable();
    const raiz = fixture.nativeElement as HTMLElement;
    const boton = () => raiz.querySelector('.grabadora .corregir') as HTMLButtonElement;
    const linea = () => (raiz.querySelector('.grabadora .linea-barra') as HTMLElement | null)?.textContent?.trim() ?? '';
    return { fixture, sesion, raiz, boton, linea };
  }

  it('el botón no va apagado: se puede pulsar', async () => {
    const { boton } = await montarGrabada(true);
    expect(boton()).not.toBeNull();
    expect(boton().disabled).toBe(false);
  });

  it('al pulsarlo dice qué falta y qué no, con «Entrar», y NO abre el panel encima', async () => {
    const { fixture, raiz, sesion, boton, linea } = await montarGrabada(true);
    boton().click();
    fixture.detectChanges();
    await fixture.whenStable();
    expect(linea()).toContain('La corrección necesita tu perfil. Grabarte y escucharte, no.');
    // El panel tapaba el propio aviso: decide el usuario con el «Entrar» de la línea
    // (Central, 16 sep). Es lo que hace el lector.
    expect(sesion.ajustesAbiertos()).toBe(false);
    const entrar = [...raiz.querySelectorAll('.grabadora .linea-barra button')]
      .find(b => b.textContent?.trim() === 'Entrar') as HTMLButtonElement;
    expect(entrar).toBeTruthy();
    entrar.click();
    expect(sesion.ajustesAbiertos()).toBe(true);
    expect(sesion.ajustesEnPerfil()).toBe(true);
    // Y no se gasta una llamada de pago por el camino. Por método y no solo por ruta: la
    // pantalla pide sus palabras débiles con un GET que cuelga de la misma ruta.
    TestBed.inject(HttpTestingController)
      .expectNone(req => req.method === 'POST' && req.url.includes('/api/voz'));
  });

  it('con sesión el guardia no se dispara: corrige de verdad y no abre los ajustes', async () => {
    const sesion = TestBed.inject(Sesion);
    sesion.entrada.set({ puerta: true, dentro: true, nombre: 'miguel', restantes: 3, openai: true, mensaje: '' });
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.frase = 'the war';
    c.blob = new Blob(['x'], { type: 'audio/webm' });
    c.estado.set('grabada');
    fixture.detectChanges();
    await fixture.whenStable();
    const raiz = fixture.nativeElement as HTMLElement;
    (raiz.querySelector('.grabadora .corregir') as HTMLButtonElement).click();
    fixture.detectChanges();
    await fixture.whenStable();
    TestBed.inject(HttpTestingController).expectOne(req => req.method === 'POST' && req.url.includes('/api/voz'));
    expect(sesion.ajustesAbiertos()).toBe(false);
  });

  it('si el servidor no tiene la clave, no manda a entrar: entrar no lo arreglaría', async () => {
    const { fixture, sesion, boton, linea } = await montarGrabada(false);
    boton().click();
    fixture.detectChanges();
    await fixture.whenStable();
    expect(linea()).toContain('La corrección no está disponible en este servidor. Grabarte y escucharte, sí.');
    expect(sesion.ajustesAbiertos()).toBe(false);
  });
});
