import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Api, Palabra, TarjetaRepaso } from '../nucleo/api';
import { Repasar } from './repasar';

/** D3.2: sesión de repaso con recuerdo activo y persistencia real,
 *  identificada por `consulta_id` (D2/D3.2: nunca por lo que mande el
 *  front). Sin SRS todavía: solo interacción + guardado + resumen. */
describe('Repasar (D3.2)', () => {
  const tarjeta = (over: Partial<TarjetaRepaso> = {}): TarjetaRepaso => ({
    palabra: 'tired', lema: 'tired', categoria: null, sentido: 'cansada, agotada',
    oracion: 'She was tired of waiting.', cita: 'She was tired of waiting.',
    libro: 'PG11', capitulo: 2, rareza: 'poco frecuente', creado: '2026-09-18T00:00:00',
    consulta_id: 1, ...over,
  });

  const PALABRA_CON_AUDIO: Palabra = {
    etapa: 'diccionario', palabra: 'tired', lema: 'tired', categoria: 'adjective',
    ipa_uk: '/taɪəd/', ipa_us: '/taɪərd/', ipa_generada_por_ia: false, compuesto: null,
    parte_del_diccionario: null, audio_uk: '/audio/tired-uk.mp3', audio_us: null, audio_generado: false,
    sentido: 'cansada', etiquetas: [], similitud: null, sentidos_candidatos: 1, dudoso: false,
    definicion_contextual: null, explicacion_gramatical: null, explicacion_adaptada: null, ejemplo: null,
  } as unknown as Palabra;

  const PALABRA_SIN_AUDIO: Palabra = { ...PALABRA_CON_AUDIO, audio_uk: null, audio_us: null };

  let apiRepaso: ReturnType<typeof vi.fn>;
  let apiPalabra: ReturnType<typeof vi.fn>;
  let apiEvaluar: ReturnType<typeof vi.fn>;

  function proveer(tarjetas: TarjetaRepaso[]) {
    apiRepaso = vi.fn(() => of({ palabras: tarjetas, voz: [], aviso_voz: null }));
    apiPalabra = vi.fn(() => of(PALABRA_SIN_AUDIO));
    apiEvaluar = vi.fn(() => of({ ok: true }));
    return TestBed.configureTestingModule({
      imports: [Repasar],
      providers: [
        provideRouter([]),
        { provide: Api, useValue: { repaso: apiRepaso, palabra: apiPalabra, evaluarRepaso: apiEvaluar } },
      ],
    }).compileComponents();
  }

  async function montar() {
    const fixture = TestBed.createComponent(Repasar);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return { fixture, raiz: fixture.nativeElement as HTMLElement };
  }

  it('0 palabras: empty state, sin CTA roto', async () => {
    await proveer([]);
    const { raiz } = await montar();
    expect(raiz.textContent).toContain('Todavía no tienes nada que repasar');
    const enlace = raiz.querySelector('a.boton') as HTMLAnchorElement;
    expect(enlace.getAttribute('href')).toBe('/leer');
  });

  it('1 palabra: muestra progreso "1 de 1"', async () => {
    await proveer([tarjeta()]);
    const { raiz } = await montar();
    expect(raiz.textContent).toContain('1 de 1');
  });

  it('5 palabras: empieza en "1 de 5"', async () => {
    await proveer([1, 2, 3, 4, 5].map(n => tarjeta({ consulta_id: n, palabra: `word${n}` })));
    const { raiz } = await montar();
    expect(raiz.textContent).toContain('1 de 5');
  });

  it('la respuesta está oculta hasta pulsar «Mostrar respuesta»', async () => {
    await proveer([tarjeta()]);
    const { raiz } = await montar();
    expect(raiz.textContent).not.toContain('cansada, agotada');
    expect(raiz.textContent).toContain('Mostrar respuesta');
  });

  it('«Mostrar respuesta» revela el sentido ya guardado, sin esperar a la red', async () => {
    await proveer([tarjeta()]);
    const { fixture, raiz } = await montar();
    (raiz.querySelector('button.boton.bloque') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(raiz.textContent).toContain('cansada, agotada');
    expect(apiPalabra).toHaveBeenCalledWith({ palabra: 'tired', oracion: 'She was tired of waiting.', idioma: 'en', etapa: 'diccionario' });
  });

  it('audio presente: aparece el botón Escuchar', async () => {
    await proveer([tarjeta()]);
    apiPalabra.mockReturnValue(of(PALABRA_CON_AUDIO));
    const { fixture, raiz } = await montar();
    (raiz.querySelector('button.boton.bloque') as HTMLButtonElement).click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const escuchar = [...raiz.querySelectorAll('button')].find(b => b.textContent?.includes('Escuchar'));
    expect(escuchar).toBeTruthy();
  });

  it('audio ausente: sin botón Escuchar, sin hueco roto', async () => {
    await proveer([tarjeta()]);
    apiPalabra.mockReturnValue(of(PALABRA_SIN_AUDIO));
    const { fixture, raiz } = await montar();
    (raiz.querySelector('button.boton.bloque') as HTMLButtonElement).click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const escuchar = [...raiz.querySelectorAll('button')].find(b => b.textContent?.includes('Escuchar'));
    expect(escuchar).toBeFalsy();
  });

  it('«Sí» guarda con el consulta_id correcto y avanza a la siguiente tarjeta', async () => {
    await proveer([tarjeta({ consulta_id: 1, palabra: 'tired' }), tarjeta({ consulta_id: 2, palabra: 'raincoat' })]);
    const { fixture, raiz } = await montar();
    (raiz.querySelector('button.boton.bloque') as HTMLButtonElement).click();
    fixture.detectChanges();
    const boton = (texto: string) => [...raiz.querySelectorAll('button')].find(b => b.textContent?.trim() === texto) as HTMLButtonElement;
    boton('Sí').click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(apiEvaluar).toHaveBeenCalledWith(1, 'si');
    expect(raiz.textContent).toContain('2 de 2');
    expect(raiz.textContent).toContain('raincoat');
  });

  it('no avanza a la siguiente tarjeta antes de que el guardado tenga éxito', async () => {
    await proveer([tarjeta({ consulta_id: 1 }), tarjeta({ consulta_id: 2, palabra: 'raincoat' })]);
    let resolver!: (v: { ok: boolean }) => void;
    apiEvaluar.mockReturnValue({ subscribe: ({ next }: { next: (v: { ok: boolean }) => void }) => { resolver = next; } });
    const { fixture, raiz } = await montar();
    (raiz.querySelector('button.boton.bloque') as HTMLButtonElement).click();
    fixture.detectChanges();
    const boton = (texto: string) => [...raiz.querySelectorAll('button')].find(b => b.textContent?.trim() === texto) as HTMLButtonElement;
    boton('Sí').click();
    fixture.detectChanges();
    expect(raiz.textContent).toContain('1 de 2'); // todavía no avanzó
    resolver({ ok: true });
    fixture.detectChanges();
    expect(raiz.textContent).toContain('2 de 2');
  });

  it('error de guardado: no avanza, muestra aviso y permite reintentar', async () => {
    await proveer([tarjeta({ consulta_id: 1 })]);
    apiEvaluar.mockReturnValue(throwError(() => new Error('sin red')));
    const { fixture, raiz } = await montar();
    (raiz.querySelector('button.boton.bloque') as HTMLButtonElement).click();
    fixture.detectChanges();
    const boton = (texto: string) => [...raiz.querySelectorAll('button')].find(b => b.textContent?.trim() === texto) as HTMLButtonElement;
    boton('Dudé').click();
    fixture.detectChanges();
    expect(raiz.textContent).toContain('1 de 1'); // no avanzó
    const reintentar = boton('Reintentar');
    expect(reintentar).toBeTruthy();
    apiEvaluar.mockReturnValue(of({ ok: true }));
    reintentar.click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(apiEvaluar).toHaveBeenCalledWith(1, 'dude');
    expect(raiz.textContent).toContain('Repasaste 1 palabra');
  });

  it('«Continuar sin guardar» aparece solo tras dos fallos seguidos: no es una cuarta evaluación', async () => {
    await proveer([tarjeta({ consulta_id: 1 }), tarjeta({ consulta_id: 2, palabra: 'raincoat' })]);
    apiEvaluar.mockReturnValue(throwError(() => new Error('sin red')));
    const { fixture, raiz } = await montar();
    const boton = (texto: string) => [...raiz.querySelectorAll('button')].find(b => b.textContent?.trim() === texto) as HTMLButtonElement;
    (raiz.querySelector('button.boton.bloque') as HTMLButtonElement).click();
    fixture.detectChanges();
    boton('No').click();
    fixture.detectChanges();
    expect(boton('Continuar sin guardar')).toBeFalsy(); // solo 1 fallo todavía
    boton('Reintentar').click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const continuar = boton('Continuar sin guardar');
    expect(continuar).toBeTruthy(); // 2 fallos seguidos
    const llamadasAntes = apiEvaluar.mock.calls.length;
    continuar.click();
    fixture.detectChanges();
    expect(apiEvaluar.mock.calls.length).toBe(llamadasAntes); // "Continuar sin guardar" no llama a la API
    expect(raiz.textContent).toContain('2 de 2'); // avanzó igual
    // Termina la sesión y confirma que no cuenta como No/Dudé/Sí.
    apiEvaluar.mockReturnValue(of({ ok: true }));
    boton('Mostrar respuesta').click();
    fixture.detectChanges();
    boton('Sí').click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const filaNo = [...raiz.querySelectorAll('.cifras-resumen > div')].find(d => d.querySelector('dt')?.textContent === 'No');
    expect(filaNo?.querySelector('dd')?.textContent).toBe('0'); // sin ese "No" fantasma
    expect(raiz.textContent).toContain('1 palabra continuó sin guardarse');
  });

  it('resumen final: cuenta exactamente lo evaluado con éxito, nada más', async () => {
    await proveer([
      tarjeta({ consulta_id: 1, palabra: 'a' }), tarjeta({ consulta_id: 2, palabra: 'b' }),
      tarjeta({ consulta_id: 3, palabra: 'c' }),
    ]);
    const { fixture, raiz } = await montar();
    const boton = (texto: string) => [...raiz.querySelectorAll('button')].find(b => b.textContent?.trim() === texto) as HTMLButtonElement;
    for (const ev of ['Sí', 'Sí', 'No']) {
      (raiz.querySelector('button.boton.bloque') as HTMLButtonElement).click();
      fixture.detectChanges();
      boton(ev).click();
      fixture.detectChanges();
      await fixture.whenStable();
      fixture.detectChanges();
    }
    expect(raiz.textContent).toContain('Repasaste 3 palabras');
    const cifras = raiz.querySelector('.cifras-resumen') as HTMLElement;
    expect(cifras.textContent).toContain('2'); // Sí
    expect(cifras.textContent).toContain('1'); // No
  });
});
