import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
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
