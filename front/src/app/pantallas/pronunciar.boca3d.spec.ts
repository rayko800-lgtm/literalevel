import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { BOCA3D_ACTIVO } from '../compartido/boca3d/interruptor';
import { Pronunciar } from './pronunciar';

/** Con el interruptor de la boca 3D encendido (Miguel, 14 sep), la ficha del
 *  sonido y la corrección enseñan «Boca en 3D»; el visor no se monta (ni baja
 *  three.js) hasta que se pulsa. */
describe('Pronunciar con la boca 3D encendida', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('pinta «Boca en 3D» en la ficha y en la corrección, sin montar el visor hasta pulsar', async () => {
    expect(BOCA3D_ACTIVO).toBe(true);
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    const ficha = { rasgos: 'fricativa dental sorda', labios: 'neutros', lengua: 'entre los dientes', boca: 'entreabierta',
      cuerdas: 'sin vibrar', aire: 'continuo', trampa: '', ga: '', rp: '' };
    const theta = { simbolo: 'θ', nombre: 'la z de zapato', ejemplos: ['think'], grupo: 'fricativas', audio: null, ficha };
    c.inventarios.set({
      ga: { acento: 'ga', acentos: { ga: 'US', rp: 'UK' }, fonemas: [theta],
        grupos: [{ clave: 'fricativas', titulo: 'Fricativas', sonidos: [theta] }] },
    });
    c.elegido.set(theta);
    c.resultado.set({
      puntuacion: 60, transcripcion_ok: true, transcripcion: 'the war', palabras: [{ palabra: 'war', bien: false }],
      entendidas: [], resumen: null, audio_correcto: null, restantes: null,
      detalles: [{ palabra: 'war', ipa: '/wɔɹ/', variante: 'US', fonema: { ...theta, acento: 'ga' }, audio: null,
        sonido_que_falla: 'la w', como_colocar_la_boca: 'redondea' }],
    });
    fixture.detectChanges();
    await fixture.whenStable();

    const raiz = fixture.nativeElement as HTMLElement;
    expect(raiz.querySelector('.ficha-sonido')).not.toBeNull();
    expect(raiz.querySelector('details.boca')).not.toBeNull();
    const botones3d = [...raiz.querySelectorAll('button')].filter(b => /Boca en 3D/.test(b.textContent ?? ''));
    // Uno en la ficha del sonido y otro en el detalle de la corrección.
    expect(botones3d.length).toBe(2);
    expect(raiz.querySelector('.ficha-sonido button[aria-expanded]')?.textContent).toContain('Boca en 3D');
    expect(raiz.querySelector('details.boca button[aria-expanded]')?.textContent).toContain('Boca en 3D');
    // Sin pulsar, no se monta el visor.
    expect(raiz.querySelector('app-boca3d')).toBeNull();
    // «Escuchar y ver»: uno solo en cada sitio, junto a «Boca en 3D».
    // «Escuchar y ver», «Más lento» y «Boca en 3D».
    expect(raiz.querySelectorAll('.ficha-sonido .botones-corte button').length).toBe(3);
    expect(raiz.querySelector('.ficha-sonido .botones-corte button:nth-child(2)')?.textContent).toContain('Más lento');
    expect(raiz.querySelector('.ficha-sonido .botones-corte button')?.textContent).toContain('Escuchar y ver');
    expect(raiz.querySelector('details.boca .botones-corte button')?.textContent).toContain('Escuchar y ver');
    expect([...raiz.querySelectorAll('button')].filter(b => /Escuchar y ver/.test(b.textContent ?? '')).length).toBe(2);
  });
});
