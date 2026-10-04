import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { Api } from './api';
import { guardarSesion, interceptorLector, tokenSesion } from './lector';

describe('sesión emitida por el servidor', () => {
  let http: HttpClient;
  let mock: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(withInterceptors([interceptorLector])), provideHttpClientTesting()] });
    http = TestBed.inject(HttpClient);
    mock = TestBed.inject(HttpTestingController);
    guardarSesion(null);
  });
  afterEach(() => { mock.verify(); guardarSesion(null); });

  it('envía X-Lector y el bearer solo al motor', () => {
    guardarSesion('fixture-de-sesion');
    http.get('/api/perfil').subscribe();
    const propia = mock.expectOne('/api/perfil');
    expect(propia.request.headers.get('Authorization')).toBe('Bearer fixture-de-sesion');
    expect(propia.request.headers.get('X-Lector')?.length).toBeGreaterThanOrEqual(16);
    propia.flush({});
    http.get('https://tercero.example/api/perfil').subscribe();
    const ajena = mock.expectOne('https://tercero.example/api/perfil');
    expect(ajena.request.headers.has('Authorization')).toBe(false);
    expect(ajena.request.headers.has('X-Lector')).toBe(false);
    ajena.flush({});
  });

  it('elimina la sesión caducada al recibir 401', () => {
    guardarSesion('fixture-de-sesion');
    http.get('/api/perfil').subscribe({ error: () => {} });
    mock.expectOne('/api/perfil').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(tokenSesion()).toBeNull();
  });

  it('conserva el token de entrar y lo elimina al salir', () => {
    const api = TestBed.inject(Api);
    api.entrar('fixture', 'clave-solo-fixture').subscribe();
    mock.expectOne('/api/entrar').flush({ dentro: true, token: 'fixture-servidor' });
    expect(tokenSesion()).toBe('fixture-servidor');
    api.salir().subscribe();
    const salida = mock.expectOne('/api/salir');
    expect(salida.request.headers.get('Authorization')).toBe('Bearer fixture-servidor');
    salida.flush({ dentro: false });
    expect(tokenSesion()).toBeNull();
  });

  it('guarda la sesión nueva que emite el motor al cambiar la contraseña', () => {
    // Miguel (4 oct): cambiar la clave no echa a este aparato; los demás quedan revocados.
    guardarSesion('fixture-de-sesion');
    TestBed.inject(Api).cambiarClave('actual-fixture', 'nueva-fixture-larga').subscribe();
    const cambio = mock.expectOne('/api/cuenta/clave');
    expect(cambio.request.headers.get('Authorization')).toBe('Bearer fixture-de-sesion');
    cambio.flush({ dentro: true, mensaje: 'Cambiada', token: 'fixture-nueva-sesion' });
    expect(tokenSesion()).toBe('fixture-nueva-sesion');
  });

  it('retira el token si el motor no devuelve sesión nueva al cambiar la contraseña', () => {
    guardarSesion('fixture-de-sesion');
    TestBed.inject(Api).cambiarClave('actual-fixture', 'nueva-fixture-larga').subscribe();
    mock.expectOne('/api/cuenta/clave').flush({ dentro: false, mensaje: 'Cambiada' });
    expect(tokenSesion()).toBeNull();
  });
});
