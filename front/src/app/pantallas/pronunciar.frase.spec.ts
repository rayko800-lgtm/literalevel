import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { Pronunciar } from './pronunciar';

/** Medido a 390 px sobre la revisión f4920fa (auditoria/boca3d_y_frase_2026-09-16.md): el cuadro
 *  de la frase tiene 112 px fijos —seis líneas—, y una oración de libro de 180 caracteres dejaba
 *  cinco líneas ocultas. Al pulsar el micrófono la vista no se movía, así que había que arrastrar
 *  dentro de un cuadro de 112 px para leer el final. Decisión de Miguel por la Central: mientras
 *  se graba, la frase deja de ser un campo y se enseña entera, y la vista va a ella. */
describe('Pronunciar: la frase mientras se graba', () => {
  const LARGA = 'He was in terrible poverty, yet he took upon himself the payment of his '
    + 'brother’s debts, and continued to live in the same modest way for many years.';

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  async function montar(estado: string) {
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.frase = LARGA;
    c.estado.set(estado);
    document.body.appendChild(fixture.nativeElement);
    fixture.detectChanges();
    await fixture.whenStable();
    const raiz = fixture.nativeElement as HTMLElement;
    return { fixture, c, raiz };
  }

  it('al grabar, la frase se enseña entera y deja de ser un campo', async () => {
    const { fixture, raiz } = await montar('grabando');
    const parrafo = raiz.querySelector('.frase-leyendo') as HTMLElement;
    expect(parrafo).not.toBeNull();
    expect(parrafo.textContent?.trim()).toBe(LARGA);
    // Sin campo no hay desplazamiento dentro del cuadro, que era el fallo.
    expect(raiz.querySelector('textarea')).toBeNull();
    // Aquí NO se comprueba «que no haya recorte»: en jsdom scrollHeight y clientHeight son
    // 0 y la comparación pasaría hasta con el párrafo vacío (4e, 16 sep). Lo que se fija
    // aquí es que el texto entero está; que se vea sin recorte se mide a 390 px en el
    // navegador (auditoria/boca3d_y_frase_2026-09-16.md).
    fixture.nativeElement.remove();
  });

  it('antes de grabar sigue siendo un campo editable, con su «Borrar la frase»', async () => {
    const { fixture, raiz } = await montar('lista');
    expect(raiz.querySelector('textarea')).not.toBeNull();
    expect(raiz.querySelector('.frase-leyendo')).toBeNull();
    const borrar = [...raiz.querySelectorAll('button')].find(b => /Borrar la frase/.test(b.textContent || ''));
    expect(borrar).toBeTruthy();
    fixture.nativeElement.remove();
  });

  it('con la grabación hecha vuelve el campo: se puede corregir la frase', async () => {
    const { fixture, raiz } = await montar('grabada');
    expect(raiz.querySelector('textarea')).not.toBeNull();
    expect(raiz.querySelector('.frase-leyendo')).toBeNull();
    fixture.nativeElement.remove();
  });

  it('al empezar a grabar, la aplicación lleva la vista a la frase', async () => {
    // Recorre el camino de verdad: grabar() con dobles del micrófono. Llamar aquí a
    // scrollIntoView y comprobar que se llamó sería una prueba que se cumple sola.
    const espia = vi.fn();
    (Element.prototype as unknown as { scrollIntoView: unknown }).scrollIntoView = espia;
    const pista = { stop: vi.fn() };
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      get: () => ({ getUserMedia: async () => ({ getTracks: () => [pista] }) }),
    });
    class GrabadorFalso {
      static isTypeSupported = () => true;
      state = 'inactive';
      mimeType = 'audio/webm';
      ondataavailable: ((e: { data: { size: number } }) => void) | null = null;
      onstop: (() => void) | null = null;
      start() { this.state = 'recording'; }
      stop() { this.state = 'inactive'; this.onstop?.(); }
    }
    (globalThis as unknown as { MediaRecorder: unknown }).MediaRecorder = GrabadorFalso;

    const { fixture, c } = await montar('lista');
    await c.grabar();
    // Primero pintar —el <p class="frase-leyendo"> todavía no existe al volver de grabar()—
    // y después dejar correr lo que se ejecuta tras el render. Esperar solo un microtask
    // daba cero llamadas: el elemento aún no estaba en el DOM.
    fixture.detectChanges();
    await fixture.whenStable();

    expect(c.estado()).toBe('grabando');
    expect(espia).toHaveBeenCalledWith({ block: 'center' });
    // Y lo que recibió el desplazamiento fue la frase, no otra cosa.
    expect((espia.mock.instances[0] as HTMLElement).classList.contains('frase-leyendo')).toBe(true);
    c.pararGrabacion(true);
    fixture.nativeElement.remove();
  });
});
