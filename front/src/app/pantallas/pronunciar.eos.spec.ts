import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Pronunciar } from './pronunciar';

/** Eos en Pronunciar (Miguel, 28 sep): los sonidos del AFI pregrabados en vídeo.
 *  El botón «Ver a Eos» solo sale para los sonidos que están en `eos/clips.json`,
 *  y el vídeo no se monta hasta pulsarlo. La frase leída se pide a la API. */
describe('Pronunciar con Eos', () => {
  const ficha = { rasgos: 'fricativa dental sorda', labios: 'neutros', lengua: 'entre los dientes', boca: 'entreabierta',
    cuerdas: 'sin vibrar', aire: 'continuo', trampa: '', ga: '', rp: '' };
  const theta = { simbolo: 'θ', nombre: 'la z de zapato', ejemplos: ['think', 'bath'], grupo: 'fricativas',
    audio: '/api/fonemas/03b8.mp3?v=1-2', ficha };
  const she = { ...theta, simbolo: 'ʃ', nombre: 'sh', audio: '/api/fonemas/0283.mp3?v=1-2' };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  function montar(indice: Record<string, { dur: number }> | null) {
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.inventarios.set({
      ga: { acento: 'ga', acentos: { ga: 'US', rp: 'UK' }, fonemas: [theta, she],
        grupos: [{ clave: 'fricativas', titulo: 'Fricativas', sonidos: [theta, she] }] },
    });
    c.elegido.set(theta);
    fixture.detectChanges();
    const http = TestBed.inject(HttpTestingController);
    const pedido = http.expectOne('eos/clips.json');
    if (indice) pedido.flush(indice);
    else pedido.flush('', { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();
    return { fixture, c, http, raiz: fixture.nativeElement as HTMLElement };
  }

  it('sin índice de clips no hay botón de Eos', () => {
    const { raiz } = montar(null);
    expect(raiz.querySelector('.ficha-sonido')).not.toBeNull();
    expect([...raiz.querySelectorAll('button')].some(b => /Ver a Eos/.test(b.textContent ?? ''))).toBe(false);
  });

  it('con el clip en el índice, «Ver a Eos» monta el vídeo del sonido al pulsar', () => {
    const { fixture, raiz } = montar({ 'ga/03b8': { dur: 5.1 } });
    const boton = [...raiz.querySelectorAll('.ficha-sonido button')].find(b => /Ver a Eos/.test(b.textContent ?? ''));
    expect(boton).toBeDefined();
    expect(raiz.querySelector('app-eos')).toBeNull();
    (boton as HTMLButtonElement).click();
    fixture.detectChanges();
    const video = raiz.querySelector<HTMLVideoElement>('app-eos video');
    expect(video).not.toBeNull();
    expect(video?.getAttribute('src')).toBe('eos/ga/03b8.mp4');
    expect(boton?.textContent).toContain('Cerrar a Eos');
  });

  it('un sonido que no está grabado no enseña el botón aunque otros sí', () => {
    const { c, fixture, raiz } = montar({ 'ga/03b8': { dur: 5.1 } });
    c.elegido.set(she);
    fixture.detectChanges();
    expect([...raiz.querySelectorAll('.ficha-sonido button')].some(b => /Ver a Eos/.test(b.textContent ?? ''))).toBe(false);
  });

  it('«Ver a Eos leerla» pide el vídeo de la frase y enseña el estado', () => {
    const { c, fixture, http, raiz } = montar({});
    c.resultado.set({
      puntuacion: 90, transcripcion_ok: true, transcripcion: 'the cat', palabras: [{ palabra: 'the', bien: true }],
      entendidas: [], resumen: null, audio_correcto: '/api/audio/abc.mp3', restantes: null, detalles: [],
    });
    fixture.detectChanges();
    const boton = [...raiz.querySelectorAll('button')].find(b => /Ver a Eos leerla/.test(b.textContent ?? ''));
    expect(boton).toBeDefined();
    (boton as HTMLButtonElement).click();
    const pedido = http.expectOne(r => r.method === 'POST' && r.url.endsWith('/api/eos/pedir'));
    expect(pedido.request.body).toEqual({ audio: '/api/audio/abc.mp3', texto: 'the' });
    pedido.flush({ estado: 'sin_trabajador', clave: 'a'.repeat(24), video: null });
    fixture.detectChanges();
    expect(raiz.querySelector('.eos-estado')?.textContent).toContain('no puede leer frases nuevas');
  });
});
