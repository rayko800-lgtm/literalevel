import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { Pronunciar } from './pronunciar';

/** Central, 15 sep: tras corregir, la barra ofrecía «Corrígeme» otra vez con la misma
 *  grabación, que es otra llamada de pago. Hasta grabar de nuevo, el botón del centro
 *  es el micrófono («Grabar otra vez»). */
describe('Pronunciar: la barra tras corregir', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  const resultado = {
    puntuacion: 80, transcripcion_ok: true, transcripcion: 'the war', palabras: [{ palabra: 'war', bien: true }],
    entendidas: [], resumen: null, detalles: [], audio_correcto: '/api/audio/x.mp3', restantes: null, ritmo: null,
  };

  function montar() {
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    const raiz = fixture.nativeElement as HTMLElement;
    const centro = () => raiz.querySelector('.grabadora .microfono') as HTMLButtonElement;
    const acciones = () => [...raiz.querySelectorAll('.grabadora .accion')].map(b => b.textContent?.trim());
    return { fixture, c, raiz, centro, acciones };
  }

  it('con una grabación sin corregir: «Corrígeme» y «Otra vez»', async () => {
    const { fixture, c, centro, acciones } = montar();
    c.frase = 'the war';
    c.estado.set('grabada');
    fixture.detectChanges();
    await fixture.whenStable();
    expect(centro().getAttribute('aria-label')).toBe('Corrígeme');
    expect(acciones()).toContain('Otra vez');
  });

  it('al corregir con éxito, el centro pasa a «Grabar otra vez» y no hay otro «Corrígeme»', async () => {
    const { fixture, c, raiz, centro, acciones } = montar();
    c.frase = 'the war';
    c.blob = new Blob(['x'], { type: 'audio/webm' });
    c.estado.set('grabada');
    const practicar = vi.spyOn(c.api, 'practicar').mockReturnValue(of(resultado));
    await c.corregir();
    fixture.detectChanges();
    await fixture.whenStable();
    expect(practicar).toHaveBeenCalledOnce();
    expect(c.corregida()).toBe(true);
    expect(centro().getAttribute('aria-label')).toBe('Grabar otra vez');
    expect(raiz.querySelector('.grabadora [aria-label="Corrígeme"]')).toBeNull();
    expect(acciones()).not.toContain('Otra vez');
    expect(acciones()).toContain('Bien leída');
    expect(raiz.querySelector('.estado-voz')?.textContent).toContain('Graba otra vez');
  });

  it('si la corrección falla, se puede volver a pedir; descartar deja de contarla como corregida', async () => {
    const { fixture, c, centro } = montar();
    c.frase = 'the war';
    c.blob = new Blob(['x'], { type: 'audio/webm' });
    c.estado.set('grabada');
    vi.spyOn(c.api, 'practicar').mockImplementation(() => { throw new Error('red'); });
    await c.corregir();
    fixture.detectChanges();
    await fixture.whenStable();
    expect(c.corregida()).toBe(false);
    expect(centro().getAttribute('aria-label')).toBe('Corrígeme');
    c.corregida.set(true);
    c.descartar();
    expect(c.corregida()).toBe(false);
  });
});
