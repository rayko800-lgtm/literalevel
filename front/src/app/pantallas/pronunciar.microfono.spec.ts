import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { Pronunciar } from './pronunciar';

/** Ismael (15 sep), Android y enlace abierto desde WhatsApp: «le pisas al micrófono y no te
 *  dice que hables, no se activa la grabación». En el celular la barra del micrófono es fija
 *  y tapaba el aviso de error y el «Grabando…», que se pintaban debajo; sin frase, el
 *  micrófono iba desactivado y un toque no hacía nada. Ahora todo sale en una línea DENTRO
 *  de la barra, con un mensaje por caso. */
describe('Pronunciar: lo que se ve al tocar el micrófono', () => {
  const UA_CHROME = 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36';
  const UA_WEBVIEW = 'Mozilla/5.0 (Linux; Android 14; Pixel 7; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/128.0.0.0 Mobile Safari/537.36';
  const UA_SAFARI = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';

  const mdOriginal = Object.getOwnPropertyDescriptor(navigator, 'mediaDevices');
  const uaOriginal = Object.getOwnPropertyDescriptor(navigator, 'userAgent');
  const mrOriginal = (globalThis as { MediaRecorder?: unknown }).MediaRecorder;

  function ponerNavegador(ua: string, getUserMedia?: () => Promise<MediaStream>) {
    Object.defineProperty(navigator, 'userAgent', { configurable: true, get: () => ua });
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, get: () => (getUserMedia ? { getUserMedia } : undefined) });
  }

  class GrabadorFalso {
    static isTypeSupported() { return true; }
    state = 'inactive';
    mimeType = 'audio/webm';
    ondataavailable: ((ev: { data: Blob }) => void) | null = null;
    onstop: (() => void) | null = null;
    constructor(_: unknown) {}
    start() { this.state = 'recording'; }
    stop() { this.state = 'inactive'; this.onstop?.(); }
  }

  const flujoFalso = () => ({ getTracks: () => [{ stop() {} }] }) as unknown as MediaStream;
  const rechazo = (name: string) => () => Promise.reject(Object.assign(new Error(name), { name }));

  beforeEach(async () => {
    (globalThis as { MediaRecorder?: unknown }).MediaRecorder = GrabadorFalso;
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  afterEach(() => {
    vi.useRealTimers();
    if (mdOriginal) Object.defineProperty(navigator, 'mediaDevices', mdOriginal); else delete (navigator as { mediaDevices?: unknown }).mediaDevices;
    if (uaOriginal) Object.defineProperty(navigator, 'userAgent', uaOriginal); else delete (navigator as { userAgent?: unknown }).userAgent;
    (globalThis as { MediaRecorder?: unknown }).MediaRecorder = mrOriginal;
  });

  async function montar(conFrase = true) {
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    if (conFrase) c.frase = 'Alice was beginning to get very tired.';
    fixture.detectChanges();
    await fixture.whenStable();
    const raiz = fixture.nativeElement as HTMLElement;
    const linea = () => raiz.querySelector('.grabadora .linea-barra') as HTMLElement | null;
    const micro = () => raiz.querySelector('.grabadora .microfono') as HTMLButtonElement;
    const tocar = async () => { micro().click(); await Promise.resolve(); await Promise.resolve(); fixture.detectChanges(); await fixture.whenStable(); fixture.detectChanges(); };
    return { fixture, c, raiz, linea, micro, tocar };
  }

  it('la línea va dentro de la barra, en su propia fila y antes del micrófono', async () => {
    ponerNavegador(UA_CHROME, rechazo('NotAllowedError'));
    const { raiz, linea, tocar } = await montar();
    await tocar();
    const barra = raiz.querySelector('.grabadora') as HTMLElement;
    expect(linea()).not.toBeNull();
    expect(barra.firstElementChild).toBe(linea());
    expect(linea()!.classList).toContain('linea-barra');
    // El aviso de antes, suelto debajo de la tarjeta y tapado por la barra fija, ya no existe.
    expect(raiz.querySelector(':scope > .pagina > .aviso.error, .pagina > .aviso.error')).toBeNull();
  });

  it('sin navigator.mediaDevices: lo dice antes de pulsar y al pulsar', async () => {
    ponerNavegador(UA_CHROME);
    const { linea, tocar } = await montar();
    expect(linea()?.textContent).toContain('Este navegador no puede grabar. Abre LiteraLevel en Chrome o Safari.');
    await tocar();
    expect(linea()?.classList).toContain('error');
    expect(linea()?.textContent).toContain('Abre LiteraLevel en Chrome o Safari');
  });

  it('NotAllowedError en Chrome normal: dice cómo dar el permiso', async () => {
    ponerNavegador(UA_CHROME, rechazo('NotAllowedError'));
    const { linea, tocar } = await montar();
    expect(linea()).toBeNull();
    await tocar();
    expect(linea()?.getAttribute('role')).toBe('alert');
    expect(linea()?.textContent).toContain('No hay permiso para el micrófono. Actívalo en los ajustes del sitio y vuelve a intentar.');
  });

  it('NotFoundError: no hay micrófono, y no dice que falta permiso', async () => {
    ponerNavegador(UA_CHROME, rechazo('NotFoundError'));
    const { linea, tocar } = await montar();
    await tocar();
    expect(linea()?.textContent).toContain('No encontramos ningún micrófono.');
    expect(linea()?.textContent).not.toContain('permiso');
  });

  it('NotReadableError: el micrófono está ocupado', async () => {
    ponerNavegador(UA_CHROME, rechazo('NotReadableError'));
    const { linea, tocar } = await montar();
    await tocar();
    expect(linea()?.textContent).toContain('El micrófono está ocupado por otra app.');
  });

  it('el permiso no contesta: pide aceptarlo y a los 5 s sugiere otro navegador', async () => {
    vi.useFakeTimers();
    ponerNavegador(UA_CHROME, () => new Promise<MediaStream>(() => {}));
    const { fixture, linea, micro } = await montar();
    micro().click();
    fixture.detectChanges();
    expect(linea()?.textContent).toContain('Acepta el permiso del micrófono.');
    vi.advanceTimersByTime(5000);
    fixture.detectChanges();
    expect(linea()?.textContent).toContain('¿No ves el permiso? Abre LiteraLevel en Chrome o Safari.');
  });

  it('concedido: «Grabando: habla ahora» con los segundos, y al parar desaparece', async () => {
    ponerNavegador(UA_CHROME, () => Promise.resolve(flujoFalso()));
    const { fixture, linea, micro, tocar } = await montar();
    await tocar();
    expect(linea()?.textContent).toContain('Grabando: habla ahora · 0 s');
    expect(linea()?.classList).toContain('grabando');
    expect(micro().classList).toContain('grabando');
    micro().click();
    fixture.detectChanges();
    expect(linea()).toBeNull();
  });

  it('sin frase: el toque responde con qué hacer', async () => {
    ponerNavegador(UA_CHROME, () => Promise.resolve(flujoFalso()));
    const { linea, micro, tocar } = await montar(false);
    expect(micro().disabled).toBe(false);
    expect(micro().getAttribute('aria-disabled')).toBe('true');
    await tocar();
    expect(linea()?.textContent).toContain('Primero escribe la frase que vas a leer.');
  });

  it('WebView de Android («; wv)»): el aviso de abrir en Chrome sale antes de pulsar', async () => {
    ponerNavegador(UA_WEBVIEW, rechazo('NotAllowedError'));
    const { linea, tocar } = await montar();
    expect(linea()?.textContent).toContain('Para grabar tu voz, abre LiteraLevel en Chrome: toca ⋮ y luego «Abrir en Chrome».');
    await tocar();
    expect(linea()?.textContent).toContain('Abrir en Chrome');
  });

  it('en Chrome normal y en Safari, con micrófono, no hay aviso previo', async () => {
    for (const ua of [UA_CHROME, UA_SAFARI]) {
      ponerNavegador(ua, () => Promise.resolve(flujoFalso()));
      const { linea } = await montar();
      expect(linea()).toBeNull();
      TestBed.resetTestingModule();
      await TestBed.configureTestingModule({
        imports: [Pronunciar],
        providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
      }).compileComponents();
    }
  });
});
