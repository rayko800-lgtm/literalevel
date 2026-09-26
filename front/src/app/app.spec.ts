import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';
import { interceptorLector } from './nucleo/lector';

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
});
