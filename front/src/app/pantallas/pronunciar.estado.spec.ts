import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { urlMotor } from '../nucleo/api';
import { ESPERAS_EOS_MAX, EstadoPronunciar } from './pronunciar.estado';
import { Pronunciar } from './pronunciar';

/** Miguel (4 oct, tras grabar la demo): pidió el vídeo de Eos de su frase, tardó, se
 *  fue a leer y al volver a Pronunciar no quedaba ni la frase ni el vídeo. Lo que la
 *  pantalla tenía en el componente vive ahora en `EstadoPronunciar` (raíz): sobrevive
 *  al cambio de pestaña, el sondeo de Eos sigue sin la pantalla y, si termina fuera de
 *  ella, enciende el aviso de arriba. `TestBed` hace un inyector nuevo por prueba, así
 *  que el servicio raíz no se contamina entre ellas. */
describe('Pronunciar: el estado sobrevive al cambio de pestaña (EstadoPronunciar)', () => {
  const resultado = {
    puntuacion: 90, transcripcion_ok: true, transcripcion: 'the cat', palabras: [{ palabra: 'the', bien: true }],
    entendidas: [], resumen: null, audio_correcto: '/api/audio/abc.mp3', restantes: null, detalles: [],
  };
  const CLAVE = 'k'.repeat(24);
  let revocar: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    // jsdom no tiene URL.createObjectURL: la grabación guarda una URL blob: fingida.
    revocar = vi.fn();
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: vi.fn(() => 'blob:grabacion'), revokeObjectURL: revocar }));
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });
  afterEach(() => vi.useRealTimers());

  function montar(entradas: Record<string, string> = {}) {
    const fixture = TestBed.createComponent(Pronunciar);
    for (const [clave, valor] of Object.entries(entradas)) fixture.componentRef.setInput(clave, valor);
    fixture.detectChanges();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    return { fixture, c, raiz: fixture.nativeElement as HTMLElement };
  }

  it('al destruir la pantalla y volver a crearla, la frase, la grabación y la corrección siguen', async () => {
    const guardado = TestBed.inject(EstadoPronunciar);
    const { fixture, c } = montar();
    c.frase = 'the cat';
    guardado.guardarGrabacion(new Blob(['x'], { type: 'audio/webm' }));
    c.resultado.set(resultado);
    c.corregida.set(true);
    fixture.destroy();                                   // a otra pestaña
    // La URL blob: es del servicio: destruir la pantalla no la revoca.
    expect(revocar).not.toHaveBeenCalled();

    const { fixture: f2, c: c2, raiz } = montar();       // y de vuelta
    await f2.whenStable();                               // ngModel escribe el campo en un microtask
    f2.detectChanges();
    expect(c2.frase).toBe('the cat');
    expect(c2.estado()).toBe('grabada');
    expect(c2.audioUrl()).toBe('blob:grabacion');
    expect(c2.blob).not.toBeNull();
    expect(c2.resultado()).toEqual(resultado);
    expect(c2.corregida()).toBe(true);
    expect((raiz.querySelector('textarea') as HTMLTextAreaElement).value).toBe('the cat');
    expect(raiz.querySelector('.resultado')).not.toBeNull();
    expect(raiz.querySelector('audio.mi-voz')?.getAttribute('src')).toBe('blob:grabacion');
  });

  it('si se sale grabando, al volver está «lista»: el micrófono se soltó con la pantalla', () => {
    const { fixture, c } = montar();
    c.frase = 'the cat';
    c.estado.set('grabando');
    fixture.destroy();
    const { c: c2 } = montar();
    expect(c2.estado()).toBe('lista');
    expect(c2.frase).toBe('the cat');
  });

  it('con Eos pendiente, el sondeo sigue sin la pantalla y al llegar «listo» se enciende el aviso', () => {
    const http = TestBed.inject(HttpTestingController);
    const guardado = TestBed.inject(EstadoPronunciar);
    const { fixture, c, raiz } = montar();
    c.resultado.set(resultado);
    fixture.detectChanges();
    http.match('eos/clips.json').forEach(p => p.flush({}));
    // Solo los relojes: la detección de cambios sin zona usa otros mecanismos.
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
    const boton = [...raiz.querySelectorAll('button')].find(b => /Ver a Eos leerla/.test(b.textContent ?? ''));
    (boton as HTMLButtonElement).click();
    http.expectOne(r => r.method === 'POST' && r.url.endsWith('/api/eos/pedir'))
      .flush({ estado: 'pendiente', clave: CLAVE, video: null });
    expect(guardado.eosFrase()?.estado).toBe('pendiente');

    fixture.destroy();                                   // se va a leer
    expect(guardado.avisoEos()).toBe(false);
    vi.advanceTimersByTime(4000);
    http.expectOne(r => r.method === 'GET' && r.url.endsWith('/api/eos/estado/' + CLAVE))
      .flush({ estado: 'pendiente', clave: CLAVE, video: null });
    vi.advanceTimersByTime(4000);
    http.expectOne(r => r.url.endsWith('/api/eos/estado/' + CLAVE))
      .flush({ estado: 'listo', clave: CLAVE, video: '/api/eos/video/k.mp4' });
    expect(guardado.eosFrase()?.estado).toBe('listo');
    expect(guardado.avisoEos()).toBe(true);
    vi.advanceTimersByTime(4000);                        // listo: no se pregunta más
    http.expectNone(r => r.url.includes('/api/eos/estado/'));

    // Al volver a Pronunciar el aviso se apaga y el vídeo está abierto.
    const { raiz: raiz2 } = montar();
    expect(guardado.avisoEos()).toBe(false);
    expect(raiz2.querySelector('app-eos video')?.getAttribute('src')).toBe(urlMotor('/api/eos/video/k.mp4'));
  });

  it('si Eos termina con la pantalla montada, no hay aviso: ya se está viendo', () => {
    const http = TestBed.inject(HttpTestingController);
    const guardado = TestBed.inject(EstadoPronunciar);
    const { fixture, c } = montar();
    c.resultado.set(resultado);
    fixture.detectChanges();
    c.verEosFrase();
    http.expectOne(r => r.url.endsWith('/api/eos/pedir')).flush({ estado: 'listo', clave: CLAVE, video: '/api/eos/video/k.mp4' });
    expect(guardado.eosFrase()?.estado).toBe('listo');
    expect(guardado.avisoEos()).toBe(false);
  });

  it('«Otra frase» limpia lo guardado y corta el sondeo: al volver no reaparece nada', () => {
    const http = TestBed.inject(HttpTestingController);
    const guardado = TestBed.inject(EstadoPronunciar);
    vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
    const { fixture, c, raiz } = montar();
    c.frase = 'the cat';
    guardado.guardarGrabacion(new Blob(['x'], { type: 'audio/webm' }));
    c.resultado.set(resultado);
    c.corregida.set(true);
    fixture.detectChanges();
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
    c.verEosFrase();
    http.expectOne(r => r.url.endsWith('/api/eos/pedir')).flush({ estado: 'pendiente', clave: CLAVE, video: null });

    const otra = [...raiz.querySelectorAll('button')].find(b => /Otra frase/.test(b.textContent ?? ''));
    (otra as HTMLButtonElement).click();
    expect(guardado.frase()).toBe('');
    expect(guardado.estado()).toBe('lista');
    expect(guardado.blob).toBeNull();
    expect(guardado.audioUrl()).toBeNull();
    expect(revocar).toHaveBeenCalledWith('blob:grabacion');
    expect(guardado.resultado()).toBeNull();
    expect(guardado.corregida()).toBe(false);
    expect(guardado.eosFrase()).toBeNull();
    // El sondeo de la frase descartada no sigue.
    vi.advanceTimersByTime(4000);
    http.expectNone(r => r.url.includes('/api/eos/estado/'));

    fixture.destroy();
    const { c: c2 } = montar();
    expect(c2.frase).toBe('');
    expect(c2.resultado()).toBeNull();
    expect(c2.eosFrase()).toBeNull();
  });

  it('una frase en la URL o un libro distinto sustituyen lo guardado; sin parámetros se restaura', async () => {
    const http = TestBed.inject(HttpTestingController);
    const guardado = TestBed.inject(EstadoPronunciar);
    const { fixture, c } = montar();
    c.frase = 'the cat';
    c.resultado.set(resultado);
    fixture.destroy();

    // Desde el lector, con otra frase: lo nuevo manda.
    const { fixture: f2, c: c2 } = montar({ frase: 'a brand new one' });
    expect(c2.frase).toBe('a brand new one');
    expect(c2.resultado()).toBeNull();
    c2.resultado.set(resultado);
    f2.destroy();

    // La pestaña de abajo, sin parámetros: se encuentra todo como se dejó.
    const { fixture: f3, c: c3 } = montar();
    expect(c3.frase).toBe('a brand new one');
    expect(c3.resultado()).toEqual(resultado);
    f3.destroy();

    // La misma frase del mismo sitio (volver atrás en el navegador) tampoco borra nada.
    const { fixture: f4, c: c4 } = montar({ frase: 'a brand new one' });
    expect(c4.resultado()).toEqual(resultado);
    f4.destroy();

    // Otro libro: frase nueva de ese capítulo y nada de lo anterior.
    const { fixture: f5, c: c5 } = montar({ libro: 'PG11', cap: '3' });
    http.expectOne(r => r.url.endsWith('/libros/PG11/capitulos/3/frase')).flush({ frase: 'From the book.' });
    await f5.whenStable();                               // traerFrase() es async
    expect(c5.frase).toBe('From the book.');
    expect(c5.resultado()).toBeNull();
    expect(guardado.contexto).toBe('PG11|3');
  });

  it('Eos pendiente: se sigue preguntando seis minutos antes de rendirse («tarda demasiado»)', () => {
    // Demo grabada del 4 oct: la frase tardó 2 min 50 s y el tope era de tres minutos.
    const http = TestBed.inject(HttpTestingController);
    const guardado = TestBed.inject(EstadoPronunciar);
    const { fixture, c } = montar();
    c.resultado.set(resultado);
    fixture.detectChanges();
    http.match('eos/clips.json').forEach(p => p.flush({}));
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
    c.verEosFrase();
    http.expectOne(r => r.url.endsWith('/api/eos/pedir')).flush({ estado: 'pendiente', clave: CLAVE, video: null });
    expect(ESPERAS_EOS_MAX).toBeGreaterThanOrEqual(90);
    for (let i = 1; i < ESPERAS_EOS_MAX; i++) {
      vi.advanceTimersByTime(4000);
      http.expectOne(r => r.url.endsWith('/api/eos/estado/' + CLAVE)).flush({ estado: 'pendiente', clave: CLAVE, video: null });
    }
    expect(guardado.eosFrase()?.estado).toBe('pendiente');   // a los 5 min 56 s sigue esperando
    vi.advanceTimersByTime(4000);
    http.expectOne(r => r.url.endsWith('/api/eos/estado/' + CLAVE)).flush({ estado: 'pendiente', clave: CLAVE, video: null });
    expect(guardado.eosFrase()?.estado).toBe('fallo');
    expect(guardado.eosFrase()?.motivo).toBe('tarda demasiado');
    vi.advanceTimersByTime(4000);                        // rendido: no se pregunta más
    http.expectNone(r => r.url.includes('/api/eos/estado/'));
  });
});
