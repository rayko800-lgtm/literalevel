import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
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
    expect(botones3d.find(b => b.closest('.ficha-sonido'))?.getAttribute('aria-expanded')).toBe('false');
    expect(botones3d.find(b => b.closest('details.boca'))?.getAttribute('aria-expanded')).toBe('false');
    // Sin pulsar, no se monta el visor.
    expect(raiz.querySelector('app-boca3d')).toBeNull();
    // «Escuchar y ver»: uno solo en cada sitio, junto a «Boca en 3D».
    // «Escuchar y ver», selector de velocidad y «Boca en 3D».
    expect(raiz.querySelectorAll('.ficha-sonido .botones-corte button').length).toBe(3);
    expect(raiz.querySelector('.ficha-sonido .disparador-velocidad')?.textContent).toContain('Velocidad');
    expect(raiz.querySelector('.ficha-sonido .botones-corte button')?.textContent).toContain('Escuchar y ver');
    expect(raiz.querySelector('details.boca .botones-corte button')?.textContent).toContain('Escuchar y ver');
    expect([...raiz.querySelectorAll('button')].filter(b => /Escuchar y ver/.test(b.textContent ?? '')).length).toBe(2);
  });
});

/** 4 oct 2026 (Miguel, tras grabar la demo en el móvil): «Leer la frase» leía
 *  por letras y sin las marcas de whisper si la IPA pedida al abrir el 3D aún
 *  no había llegado, y la boca quedaba desalineada del audio. */
describe('4 oct: la frase en 3D espera a su IPA', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  const AUDIO = '/api/audio/frase.mp3?acceso=abc';
  const vuelta = (ms = 0) => new Promise(r => setTimeout(r, ms));

  function preparar() {
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    const visor = { anticipar: vi.fn(), leerFrase: vi.fn() };
    c.visor = () => visor;
    c.resultado.set({
      puntuacion: 80, transcripcion_ok: true, transcripcion: 'the cat',
      palabras: [{ palabra: 'the', bien: true }, { palabra: 'cat', bien: true }],
      entendidas: [], resumen: null, audio_correcto: AUDIO, restantes: null, detalles: [],
    });
    c.alternarLectura3d();
    expect(c.visor3d()).toBe('lectura');
    const http = TestBed.inject(HttpTestingController);
    const peticion = http.match(r => r.url.endsWith('/lectura/ipa') && r.params.get('texto') === 'the cat')[0];
    expect(peticion).toBeTruthy();
    expect(peticion.request.params.get('audio')).toBe('frase.mp3');
    return { c, visor, peticion };
  }

  it('con la IPA en vuelo, el audio se anticipa en el clic y la lectura espera a las marcas', async () => {
    const { c, visor, peticion } = preparar();
    c.oirLectura(AUDIO, 'the cat');
    expect(visor.anticipar).toHaveBeenCalledWith(expect.stringContaining('/api/audio/frase.mp3'));
    await vuelta();
    expect(visor.leerFrase).not.toHaveBeenCalled();
    peticion.flush({ palabras: [{ palabra: 'the', ipa: 'ðə', inicio: 0.1, fin: 0.2 }, { palabra: 'cat', ipa: 'kæt', inicio: 0.2, fin: 0.5 }] });
    await vuelta();
    expect(visor.leerFrase).toHaveBeenCalledTimes(1);
    const [audio, palabras] = visor.leerFrase.mock.calls[0];
    expect(audio).toContain('/api/audio/frase.mp3');
    expect(palabras[1]).toEqual({ palabra: 'cat', ipa: 'kæt', inicio: 0.2, fin: 0.5 });
    // La segunda vez ya la tiene: lee en el acto.
    c.oirLectura(AUDIO, 'the cat');
    expect(visor.leerFrase).toHaveBeenCalledTimes(2);
  });

  it('si la IPA no llega a tiempo lee por letras sin esperar más; con el 3D cerrado mientras tanto, no lee', async () => {
    const { c, visor } = preparar();
    c.esperaIpaMs = 20;
    c.oirLectura(AUDIO, 'the cat');
    await vuelta(60);
    expect(visor.leerFrase).toHaveBeenCalledTimes(1);
    expect(visor.leerFrase.mock.calls[0][1]).toEqual([{ palabra: 'the', ipa: null }, { palabra: 'cat', ipa: null }]);

    const otra = preparar();
    otra.c.esperaIpaMs = 20;
    otra.c.oirLectura(AUDIO, 'the cat');
    otra.c.visor3d.set(null);
    await vuelta(60);
    expect(otra.visor.leerFrase).not.toHaveBeenCalled();
  });
});
