import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { BOCA3D_ACTIVO } from '../compartido/boca3d/interruptor';
import { Pronunciar } from './pronunciar';

/** Con el interruptor de la boca 3D apagado (decisión de Miguel, 14 sep), ni la
 *  ficha del sonido ni la corrección enseñan «Boca en 3D»; el corte 2D sí. */
describe('Pronunciar con la boca 3D apagada', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('no pinta el botón 3D ni el visor, y sí la ficha y los cortes 2D', async () => {
    expect(BOCA3D_ACTIVO).toBe(false);
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
    // Control: lo que rodea al botón sí está, así que su ausencia no es por no pintar nada.
    expect(raiz.querySelector('.ficha-sonido')).not.toBeNull();
    expect(raiz.querySelector('details.boca')).not.toBeNull();
    const botones = [...raiz.querySelectorAll('button')].map(b => b.textContent ?? '');
    expect(botones.some(t => /Boca en 3D|Cerrar 3D/.test(t))).toBe(false);
    expect(raiz.querySelector('app-boca3d')).toBeNull();
  });
});
