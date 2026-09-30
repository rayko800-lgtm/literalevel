import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Pronunciar } from './pronunciar';

/** Propuesta A de Pronunciar (Miguel, 15 sep; auditoria/esmeralda_ux_2026-09-15.md):
 *  primero el resumen, la frase solo con bien o a revisar, «Practica esta palabra» con
 *  «Escuchar y ver» y el selector «🐢 Despacio» a la vista, y el ritmo y lo natural
 *  plegados en «Para sonar más natural», con las marcas detrás de su palabra. */
describe('Pronunciar (propuesta A)', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  const ficha = { rasgos: 'vocal abierta', labios: 'neutros', lengua: 'baja', boca: 'abierta', cuerdas: 'vibran',
    aire: 'por la boca', trampa: '', ga: '', rp: '' };
  const fonema = { simbolo: 'ɑ', nombre: 'a abierta', ejemplos: ['hot'], grupo: 'vocales', audio: null, ficha, acento: 'ga' };
  const palabras = ["don't", 'you', 'want', 'to', 'come', 'with', 'us'];

  async function pintar() {
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.resultado.set({
      puntuacion: 71, transcripcion_ok: true, transcripcion: "don't you won't to come with us",
      palabras: palabras.map(p => ({ palabra: p, bien: p !== 'want' })), entendidas: [],
      resumen: 'Casi todo se entendió: abre más la boca en «want».',
      detalles: [{ palabra: 'want', ipa: '/wɑnt/', variante: 'US', audio: null, fonema,
        sonido_que_falla: 'la vocal', como_colocar_la_boca: 'abre la boca' }],
      audio_correcto: null, restantes: null,
      ritmo: {
        medido: true, duracion_s: 2.2, palabras: [],
        pausas: [{ despues_de: 2, segundos: 0.5, en_referencia: false, de_mas: true }],
        tramos: [{ desde: 4, hasta: 6, palabras_por_segundo: 3, referencia: 5, objetivo: 4.5, acelerar: true }],
        natural: null,
      },
    });
    fixture.detectChanges();
    await fixture.whenStable();
    return { fixture, c, raiz: fixture.nativeElement as HTMLElement };
  }

  it('el resumen va antes que la frase, y la frase solo dice bien o a revisar', async () => {
    const { raiz } = await pintar();
    const resumen = raiz.querySelector('.resultado .resumen') as HTMLElement;
    const frase = raiz.querySelector('.resultado .frase-corregida') as HTMLElement;
    expect(resumen.textContent).toContain('abre más la boca');
    expect(resumen.compareDocumentPosition(frase) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(frase.querySelectorAll('.marca, .enlace, .enfasis').length).toBe(0);
    expect([...frase.querySelectorAll('li.mal')].map(li => li.firstChild?.textContent)).toEqual(['want']);
  });

  it('la velocidad abre una barra continua de 0,25 a 2 sin cambiar el valor al abrir', async () => {
    const { fixture, c, raiz } = await pintar();
    const detalle = raiz.querySelector('.detalle') as HTMLElement;
    const boton = detalle.querySelector('.disparador-velocidad') as HTMLButtonElement;
    expect(boton.textContent).toContain('1,00×');
    boton.click(); fixture.detectChanges();
    expect(c.velocidad()).toBe(1);
    const barra = detalle.querySelector('[aria-label="Velocidad de reproducción"]') as HTMLInputElement;
    expect([barra.min, barra.max, barra.step]).toEqual(['0.25', '2', '0.01']);
    barra.value = '0.83'; barra.dispatchEvent(new Event('input')); fixture.detectChanges();
    expect(c.velocidad()).toBe(0.83);
    expect(boton.textContent).toContain('0,83×');
    barra.value = '2'; barra.dispatchEvent(new Event('input')); fixture.detectChanges();
    expect(c.velocidad()).toBe(2);
    expect(detalle.querySelector('[role="radiogroup"]')).toBeNull();
  });

  it('el ritmo va plegado y cada marca detrás de su palabra: «no pares aquí» tras want, «de corrido aquí» tras us', async () => {
    const { raiz } = await pintar();
    const plegado = raiz.querySelector('details.sonar-natural') as HTMLDetailsElement;
    expect(plegado.open).toBe(false);
    expect(plegado.querySelector('summary')?.textContent).toContain('Para sonar más natural');
    const items = [...plegado.querySelectorAll('.palabras-voz > li')].map(li =>
      li.classList.contains('marca') ? `[${li.textContent?.trim()}]` : (li.firstChild?.textContent ?? '').trim());
    expect(items).toEqual(["don't", 'you', 'want', '[no pares aquí]', 'to', 'come', 'with', 'us', '[de corrido aquí]']);
    expect(raiz.textContent).not.toContain('más seguido');   // en México «seguido» es «a menudo» (4e)
    expect(raiz.textContent).not.toContain('aquí aceleras');
    expect(raiz.textContent).not.toContain('aquí sin pausa');
  });

  it('«Corrígeme» lleva su nombre a la vista en la barra', async () => {
    const { fixture, c, raiz } = await pintar();
    c.resultado.set(null);
    c.frase = 'hello';
    c.estado.set('grabada');
    fixture.detectChanges();
    await fixture.whenStable();
    const boton = raiz.querySelector('.grabadora .microfono') as HTMLButtonElement;
    expect(boton.getAttribute('aria-label')).toBe('Corrígeme');
    expect(boton.textContent?.trim()).toBe('Corrígeme');
  });
});
