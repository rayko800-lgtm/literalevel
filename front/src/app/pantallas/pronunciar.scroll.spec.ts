import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, DeferBlockBehavior, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Pronunciar } from './pronunciar';

describe('Pronunciar: auto-scroll a la ficha del fonema', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  const ficha = {
    rasgos: 'fricativa', labios: 'neutros', lengua: 'cerca del punto de contacto',
    boca: 'entreabierta', cuerdas: 'sin vibrar', aire: 'continuo', trampa: '', ga: '', rp: '',
  };
  const theta = { simbolo: 'θ', nombre: 'theta', ejemplos: ['think'], grupo: 'fricativas', audio: null, ficha };
  const ese = { simbolo: 's', nombre: 'ese', ejemplos: ['see'], grupo: 'fricativas', audio: null, ficha };

  function preparar(reducir = false) {
    const fixture = TestBed.createComponent(Pronunciar);
    // `sinMovimiento` se calcula al construir; forzarlo aquí permite cubrir
    // ambos contratos sin cambiar el matchMedia global de las demás pruebas.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.sinMovimiento = reducir;
    c.inventarios.set({ ga: {
      acento: 'ga', acentos: { ga: 'US', rp: 'UK' }, fonemas: [theta, ese],
      grupos: [{ clave: 'fricativas', titulo: 'Fricativas', sonidos: [theta, ese] }],
    } });
    fixture.detectChanges();
    return { fixture, c };
  }

  function corteFuera(fixture: ComponentFixture<Pronunciar>) {
    const corte = fixture.nativeElement.querySelector('.ficha-sonido img.corte') as HTMLElement;
    vi.spyOn(corte, 'getBoundingClientRect').mockReturnValue({
      x: 0, y: 1200, top: 1200, right: 240, bottom: 1448, left: 0, width: 240, height: 248,
      toJSON: () => ({}),
    });
    return corte;
  }

  it('clic abre la ficha, espera al DOM y desplaza el corte 2D correcto suavemente', async () => {
    const { fixture, c } = preparar();
    const desplazar = vi.spyOn(window, 'scrollBy').mockImplementation(() => undefined);
    (fixture.nativeElement.querySelectorAll('.celda')[0] as HTMLButtonElement).click();
    fixture.detectChanges();
    const corte = corteFuera(fixture);
    expect(fixture.nativeElement.querySelector('.ficha-sonido')).not.toBeNull();
    expect(c.elegido().simbolo).toBe('θ');
    await new Promise(resolve => setTimeout(resolve, 30));
    expect(corte.getBoundingClientRect).toHaveBeenCalled();
    expect(desplazar).toHaveBeenCalledWith(expect.objectContaining({ behavior: 'smooth' }));

    desplazar.mockClear();
    (fixture.nativeElement.querySelectorAll('.celda')[1] as HTMLButtonElement).click();
    fixture.detectChanges();
    corteFuera(fixture);
    await new Promise(resolve => setTimeout(resolve, 30));
    expect(c.elegido().simbolo).toBe('s');
    expect(fixture.nativeElement.querySelector('.ficha-sonido .simbolo')?.textContent).toContain('/s/');
    expect(desplazar).toHaveBeenCalledTimes(1);
  });

  it('con movimiento reducido solicita desplazamiento inmediato', async () => {
    const { fixture } = preparar(true);
    const desplazar = vi.spyOn(window, 'scrollBy').mockImplementation(() => undefined);
    (fixture.nativeElement.querySelector('.celda') as HTMLButtonElement).click();
    fixture.detectChanges();
    corteFuera(fixture);
    await new Promise(resolve => setTimeout(resolve, 30));
    expect(desplazar).toHaveBeenCalledWith(expect.objectContaining({ behavior: 'auto' }));
  });
});

/** Miguel (4 oct, tras grabar la demo): con el 3D abierto, «Escuchar y ver»
 *  bajaba siempre al 3D, aunque el usuario hubiera subido con el dedo hasta el
 *  corte 2D para mirarlo. Ahora va a lo que más se ve: el 3D solo si es lo que
 *  más cabe en la franja útil (entre la cabecera y la barra pegada); si no, el
 *  2D, que ya está a la vista y no mueve nada. */
describe('Pronunciar: «Escuchar y ver» con el 3D abierto va a lo que más se ve', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
      // El visor va en un @defer: en las pruebas no se monta sin esto.
      deferBlockBehavior: DeferBlockBehavior.Playthrough,
    }).compileComponents();
  });

  const ficha = {
    rasgos: 'fricativa', labios: 'neutros', lengua: 'entre los dientes',
    boca: 'entreabierta', cuerdas: 'sin vibrar', aire: 'continuo', trampa: '', ga: '', rp: '',
  };
  const theta = { simbolo: 'θ', nombre: 'theta', ejemplos: ['think'], grupo: 'fricativas', audio: null, ficha, acento: 'ga' };

  type Rect = { top: number; bottom: number };
  function rect(el: HTMLElement, { top, bottom }: Rect) {
    vi.spyOn(el, 'getBoundingClientRect').mockReturnValue({
      x: 0, y: top, top, right: 320, bottom, left: 0, width: 320, height: bottom - top, toJSON: () => ({}),
    });
  }

  /** La corrección con una palabra fallada y su 3D abierto (sin WebGL en jsdom:
   *  el visor pinta su respaldo 2D, pero el <app-boca3d> y su .visor existen). */
  async function montarCon3d(visor: Rect, cortes: Rect) {
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.resultado.set({
      puntuacion: 60, transcripcion_ok: true, transcripcion: 'the war', palabras: [{ palabra: 'war', bien: false }],
      entendidas: [], resumen: null, audio_correcto: null, restantes: null,
      detalles: [{ palabra: 'war', ipa: '/wɔɹ/', variante: 'US', fonema: theta, audio: null,
        sonido_que_falla: 'la w', como_colocar_la_boca: 'redondea' }],
    });
    c.visor3d.set('detalle-0');
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const raiz = fixture.nativeElement as HTMLElement;
    const boca3d = raiz.querySelector<HTMLElement>('details.boca app-boca3d');
    const cortes2d = raiz.querySelector<HTMLElement>('details.boca .cortes');
    expect(boca3d).not.toBeNull();
    expect(boca3d?.querySelector('.visor')).not.toBeNull();
    expect(cortes2d).not.toBeNull();
    rect(boca3d as HTMLElement, visor);
    rect(cortes2d as HTMLElement, cortes);
    // Lo que se prueba es a dónde va la vista, no el audio ni el corte animado.
    vi.spyOn(c.eyv, 'escuchar').mockImplementation(() => undefined);
    // El espía de scrollBy es el mismo entre pruebas: se vacía lo que trajera de otras.
    const desplazar = vi.spyOn(window, 'scrollBy').mockImplementation(() => undefined);
    desplazar.mockClear();
    const boton = [...raiz.querySelectorAll<HTMLButtonElement>('details.boca .botones-corte button')]
      .find(b => /Escuchar y ver/.test(b.textContent ?? ''));
    expect(boton).toBeDefined();
    return { fixture, c, desplazar, boton: boton as HTMLButtonElement };
  }

  it('con el 3D a medio ver y el 2D fuera, reproducir lleva la vista al 3D', async () => {
    // innerHeight de jsdom: 768. El 3D asoma por abajo (de 500 a 900), el 2D ya pasó por arriba.
    const { desplazar, boton } = await montarCon3d({ top: 500, bottom: 900 }, { top: -400, bottom: -100 });
    boton.click();
    expect(desplazar).toHaveBeenCalledTimes(1);
    const { top } = desplazar.mock.calls[0][0] as ScrollToOptions;
    expect(top).toBeGreaterThan(0);                      // hacia abajo, hacia el 3D
  });

  it('con el 2D a la vista y el 3D por debajo de la pantalla, reproducir no mueve la página', async () => {
    // El usuario subió con el dedo a mirar el corte 2D: se queda donde está (Miguel, 4 oct).
    const { desplazar, boton } = await montarCon3d({ top: 900, bottom: 1300 }, { top: 100, bottom: 348 });
    boton.click();
    expect(desplazar).not.toHaveBeenCalled();
  });

  it('con los dos a la vista por igual, el 2D manda y no se baja al 3D', async () => {
    // Empate (los dos enteros en la franja): no hay motivo para bajar al 3D.
    const { desplazar, boton } = await montarCon3d({ top: 400, bottom: 700 }, { top: 100, bottom: 348 });
    boton.click();
    expect(desplazar).not.toHaveBeenCalled();
  });

  it('al abrir el 3D (alternarBoca) sí se baja hasta él aunque el 2D esté a la vista', async () => {
    const { c, desplazar, boton } = await montarCon3d({ top: 900, bottom: 1300 }, { top: 100, bottom: 348 });
    // Como si se acabara de pulsar «Boca en 3D» desde la misma barra: la boca entera a la vista.
    c.visor3d.set(null);
    c.alternarBoca('detalle-0', { currentTarget: boton } as unknown as Event);
    await new Promise(resolve => setTimeout(resolve, 30));
    expect(desplazar).toHaveBeenCalledTimes(1);
    expect((desplazar.mock.calls[0][0] as ScrollToOptions).top).toBeGreaterThan(0);
  });
});
