import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Entrada } from '../nucleo/api';
import { guardarSesion, tokenSesion } from '../nucleo/lector';
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

  /** 4 oct (Miguel, demo): cambiar la contraseña le echaba y el panel volvía a enseñar
   *  «Entrar», como si se la pidiera otra vez. Ahora el motor emite una sesión nueva para
   *  este aparato, se guarda y se sigue dentro, sin volver a pedir /api/inicio. */
  it('cambiar la contraseña deja al usuario dentro con la sesión nueva', async () => {
    const sesion = TestBed.inject(Sesion);
    const http = TestBed.inject(HttpTestingController);
    guardarSesion('sesion-vieja');
    sesion.entrada.set({ ...DENTRO, restantes: 7 });
    const fixture = TestBed.createComponent(Ajustes);
    fixture.detectChanges();
    const raiz = fixture.nativeElement as HTMLElement;
    const plegable = raiz.querySelector('details.cambiar-clave') as HTMLDetailsElement;
    expect(plegable?.open).toBe(false);
    expect(plegable.querySelector('summary')?.textContent).toContain('Cambiar contraseña');
    const ajustes = fixture.componentInstance as unknown as { actual: string; nueva: string; cambiarClave(): Promise<void> };
    ajustes.actual = 'la-de-antes'; ajustes.nueva = 'la-nueva-de-doce';
    const cambiando = ajustes.cambiarClave();
    http.expectOne(r => r.url.endsWith('/api/cuenta/clave')).flush({
      ...DENTRO, restantes: 7, token: 'sesion-nueva',
      mensaje: 'Contraseña cambiada. En tus otros dispositivos tendrás que volver a entrar.' });
    await cambiando;
    http.expectNone(r => r.url.endsWith('/api/inicio'));
    fixture.detectChanges();
    expect(tokenSesion()).toBe('sesion-nueva');
    expect(sesion.entrada()?.dentro).toBe(true);
    expect(sesion.entrada()?.restantes).toBe(7);
    expect(ajustes.actual).toBe('');
    expect(ajustes.nueva).toBe('');
    expect(raiz.querySelector('input[name=usuario]')).toBeNull();
    expect(raiz.querySelector('.aviso')?.textContent).toContain('Contraseña cambiada');
    guardarSesion(null);
  });
});
