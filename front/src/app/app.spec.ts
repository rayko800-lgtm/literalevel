import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { App } from './app';
import { interceptorLector } from './nucleo/lector';
import { EstadoPronunciar } from './pantallas/pronunciar.estado';

@Component({ template: '' })
class Vacia {}

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      // `Sesion` pregunta por /api/salud al arrancar: aquí no sale nada a la red.
      providers: [provideRouter([]), provideHttpClient(withInterceptors([interceptorLector])), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('se crea', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('pinta la marca, Mi espacio y las cuatro funciones de la navegación', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const raiz = fixture.nativeElement as HTMLElement;
    expect(raiz.querySelector('.marca')?.textContent).toContain('Pléyade');
    const funciones = [...raiz.querySelectorAll('.nav-escritorio a')].map(a => a.textContent?.trim());
    expect(funciones).toEqual(['Mi espacio', 'Leer', 'Encontrar', 'Pronunciar', 'Tu nivel']);
  });

  it('manda X-Lector en las peticiones al motor', () => {
    TestBed.createComponent(App);
    const http = TestBed.inject(HttpTestingController);
    const salud = http.expectOne(r => r.url.endsWith('/api/salud'));
    expect((salud.request.headers.get('X-Lector') ?? '').length).toBeGreaterThanOrEqual(16);
  });

  /** Miguel (4 oct): Eos terminó el vídeo de su frase mientras leía y no se enteró. La
   *  franja de arriba lo dice con un enlace a Pronunciar, se cierra con la ✕ y no sale
   *  si ya se está en Pronunciar (ahí el vídeo se ve directamente). */
  it('avisa arriba cuando Eos termina fuera de Pronunciar, con enlace a /pronunciar y ✕', async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([{ path: '', component: Vacia }, { path: 'pronunciar', component: Vacia }]),
        provideHttpClient(withInterceptors([interceptorLector])), provideHttpClientTesting(),
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(App);
    const estado = TestBed.inject(EstadoPronunciar);
    const router = TestBed.inject(Router);
    await fixture.whenStable();
    const raiz = fixture.nativeElement as HTMLElement;
    const franja = () => raiz.querySelector('.motor.eos');
    expect(franja()).toBeNull();

    estado.avisoEos.set(true);
    fixture.detectChanges();
    expect(franja()?.getAttribute('role')).toBe('status');
    expect(franja()?.textContent).toContain('Eos ya tiene lista tu frase');
    expect(franja()?.querySelector('a')?.getAttribute('href')).toBe('/pronunciar');

    // En Pronunciar no hace falta; al salir de ella, si sigue encendido, vuelve.
    await router.navigateByUrl('/pronunciar');
    fixture.detectChanges();
    expect(franja()).toBeNull();
    await router.navigateByUrl('/');
    fixture.detectChanges();
    expect(franja()).not.toBeNull();

    (franja()?.querySelector('button') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(franja()).toBeNull();
    expect(estado.avisoEos()).toBe(false);
  });
});
