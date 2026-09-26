import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Entrada } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Ajustes } from './ajustes';

/** 26 sep (Miguel): con cuenta, los datos son de la cuenta en cualquier aparato. Entrar o
 *  salir cambia de quién son, así que la sesión vuelve a pedir /api/inicio. */
describe('Entrar y salir recargan los datos', () => {
  const FUERA: Entrada = { puerta: true, dentro: false, nombre: null, restantes: null, openai: true, mensaje: '' };
  const DENTRO: Entrada = { ...FUERA, dentro: true, nombre: 'miguel', restantes: 0, mensaje: 'Has entrado como miguel.' };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('tras entrar y tras salir pide /api/inicio', async () => {
    const sesion = TestBed.inject(Sesion);
    const http = TestBed.inject(HttpTestingController);
    sesion.entrada.set(FUERA);
    const fixture = TestBed.createComponent(Ajustes);
    fixture.detectChanges();
    const ajustes = fixture.componentInstance as unknown as { usuario: string; clave: string; entrar(): Promise<void>; salir(): Promise<void> };
    ajustes.usuario = 'miguel'; ajustes.clave = 'x';
    const entrando = ajustes.entrar();
    http.expectOne(r => r.url.endsWith('/api/entrar')).flush(DENTRO);
    await Promise.resolve(); await Promise.resolve();
    http.expectOne(r => r.url.endsWith('/api/inicio')).flush({ perfil: null, seguir: null, libros: 0,
      cuaderno: { consultas: 0, palabras: 0, libros: 0 }, entrada: DENTRO });
    await entrando;
    expect(sesion.entrada()?.dentro).toBe(true);

    const saliendo = ajustes.salir();
    http.expectOne(r => r.url.endsWith('/api/salir')).flush(FUERA);
    await Promise.resolve(); await Promise.resolve();
    http.expectOne(r => r.url.endsWith('/api/inicio')).flush({ perfil: null, seguir: null, libros: 0,
      cuaderno: { consultas: 0, palabras: 0, libros: 0 }, entrada: FUERA });
    await saliendo;
    expect(sesion.entrada()?.dentro).toBe(false);
  });
});
