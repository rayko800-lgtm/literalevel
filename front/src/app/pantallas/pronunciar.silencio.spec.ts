import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Pronunciar } from './pronunciar';

/** Con una grabación en silencio (o con el «you» que whisper inventa sin voz) la API
 *  responde transcripcion_ok false y puntuación 0 (reinicio 24, 0a759a5). El aviso dice
 *  qué hacer, sin un 0/100 ni «Vamos a por ello». También vale para «Una frase de mi
 *  libro», que usa la misma corrección. */
describe('Pronunciar sin voz', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  async function pintar(transcripcion_ok: boolean, uso_devuelto?: boolean) {
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.resultado.set({
      puntuacion: transcripcion_ok ? 64 : 0, transcripcion_ok, uso_devuelto, transcripcion: transcripcion_ok ? 'the war' : '',
      palabras: [{ palabra: 'the', bien: transcripcion_ok }, { palabra: 'war', bien: false }],
      entendidas: [], resumen: null, detalles: [], audio_correcto: null, restantes: null,
      // Sin análisis natural: con voz sale «no llegaron el énfasis…»; sin voz, no.
      ritmo: { medido: false, duracion_s: null, palabras: [], pausas: [], tramos: [], natural: null },
    });
    fixture.detectChanges();
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  it('sin voz: «No te oí», sin puntuación ni nota, y sin marcar palabras', async () => {
    const raiz = await pintar(false);
    const resultado = raiz.querySelector('.resultado') as HTMLElement;
    expect(resultado.textContent).toContain('No te oí. Acércate al micrófono y vuelve a grabar.');
    expect(resultado.textContent).not.toContain('la puntuación no es válida');
    expect(resultado.querySelector('.anillo')?.textContent?.trim()).toBe('—');
    expect(resultado.querySelector('.nota h2')).toBeNull();
    expect(resultado.querySelector('.palabras-voz')).toBeNull();
    expect(resultado.textContent).not.toContain('no llegaron el énfasis');
  });

  it('sin voz y con el uso devuelto (reinicio 26): «Este intento no cuenta.»; sin el campo, no lo dice', async () => {
    const devuelto = await pintar(false, true);
    expect(devuelto.querySelector('.resultado .aviso')?.textContent).toContain('No te oí. Acércate al micrófono y vuelve a grabar. Este intento no cuenta.');
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    const sinCampo = await pintar(false);
    expect(sinCampo.querySelector('.resultado .aviso')?.textContent).not.toContain('no cuenta');
  });

  it('con voz: la puntuación, la nota y lo que se entendió, sin el aviso', async () => {
    const raiz = await pintar(true);
    const resultado = raiz.querySelector('.resultado') as HTMLElement;
    expect(resultado.querySelector('.anillo strong')?.textContent).toBe('64');
    expect(resultado.querySelector('.nota h2')?.textContent).toBe('Vamos a por ello');
    expect(resultado.textContent).toContain('«the war»');
    expect(resultado.textContent).not.toContain('No te oí');
    expect(resultado.textContent).toContain('no llegaron el énfasis');
  });
});
