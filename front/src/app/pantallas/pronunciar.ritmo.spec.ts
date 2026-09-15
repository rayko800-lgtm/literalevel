import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { RitmoLectura } from '../nucleo/api';
import { Pronunciar } from './pronunciar';

/** El JSON real que mandó entrega-4e para «Don't you want to come with us?»
 *  (marcas de la referencia con una pausa de 0,5 s tras «want» y el análisis
 *  de gpt-4o-mini validado), pintado en la corrección. */
const RITMO: RitmoLectura = {
  medido: true, duracion_s: 2.25,
  palabras: [{ palabra: "don't", inicio: 0, fin: 0.24 }, { palabra: 'you', inicio: 0.24, fin: 0.38 },
    { palabra: 'want', inicio: 0.38, fin: 0.46 }, { palabra: 'to', inicio: 0.96, fin: 1.12 },
    { palabra: 'come', inicio: 1.12, fin: 1.22 }, { palabra: 'with', inicio: 1.22, fin: 1.4 },
    { palabra: 'us', inicio: 1.4, fin: 1.64 }],
  pausas: [{ despues_de: 2, segundos: 0.5, en_referencia: false, de_mas: true }],
  tramos: [{ desde: 0, hasta: 2, palabras_por_segundo: 6.52, referencia: 6.52, objetivo: 5.87, acelerar: false },
    { desde: 3, hasta: 6, palabras_por_segundo: 5.88, referencia: 5.88, objetivo: 5.29, acelerar: false }],
  natural: {
    enfasis: [{ indice: 0, ipa: '/ˈdoʊnt/' }, { indice: 2, ipa: '/wɑnt/' }, { indice: 4, ipa: '/kʌm/' }, { indice: 6, ipa: '/ʌs/' }],
    enlaces: [{ de: 5, a: 6, tipo: 'consonante_vocal', ipa: '/wɪð.ʌs/' }],
    reducciones: [{ desde: 0, hasta: 1, forma: 'doncha', ipa: '/ˈdoʊntʃə/', generado_por_ia: true },
      { desde: 2, hasta: 3, forma: 'wanna', ipa: '/ˈwɑnə/', generado_por_ia: true }],
    tramos_rapidos: [{ desde: 0, hasta: 3 }, { desde: 4, hasta: 6 }],
    version_natural: 'Doncha wanna come with us?',
    audio_natural: '/api/audio/natural.mp3',
  },
};

describe('Pronunciar con el ritmo de la lectura', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  async function pintar(ritmo: RitmoLectura | null) {
    const fixture = TestBed.createComponent(Pronunciar);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    const palabras = ["don't", 'you', 'want', 'to', 'come', 'with', 'us'].map(palabra => ({ palabra, bien: true }));
    c.resultado.set({ puntuacion: 92, transcripcion_ok: true, transcripcion: "don't you want to come with us",
      palabras, entendidas: [], resumen: null, detalles: [], audio_correcto: null, restantes: null, ritmo });
    fixture.detectChanges();
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  it('pinta «no pares aquí» tras want, el arco with‿us, las negritas y cómo suena natural, plegados', async () => {
    const raiz = await pintar(RITMO);
    // Propuesta A: el ritmo va dentro de «Para sonar más natural», cerrado.
    expect((raiz.querySelector('details.sonar-natural') as HTMLDetailsElement).open).toBe(false);
    const items = [...raiz.querySelectorAll('.sonar-natural .palabras-voz > li')].map(li =>
      li.classList.contains('marca') ? `[${li.textContent?.trim()}]`
        : li.classList.contains('enlace') ? '‿'
          : (li.classList.contains('enfasis') ? '*' : '') + (li.firstChild?.textContent ?? '').trim());
    expect(items).toEqual(["*don't", 'you', '*want', '[no pares aquí]', 'to', '*come', 'with', '‿', '*us']);
    expect(raiz.querySelector('.marca.acelera')).toBeNull();
    const natural = raiz.querySelector('.natural') as HTMLElement;
    expect(natural.querySelector('.version-natural')?.textContent).toContain('Doncha wanna come with us?');
    const reducciones = [...natural.querySelectorAll('.reducciones li')].map(li => li.textContent?.replace(/\s+/g, ' ').trim());
    expect(reducciones).toEqual(["don't you → /ˈdoʊntʃə/ (doncha) IA", 'want to → /ˈwɑnə/ (wanna) IA']);
    expect(natural.querySelector('button')?.textContent).toContain('Escúchalo natural');
  });

  it('sin clave: sin marcas de tiempo, sin énfasis y con el aviso', async () => {
    const raiz = await pintar({ medido: false, duracion_s: null, palabras: [], pausas: [], tramos: [], natural: null });
    expect(raiz.querySelectorAll('.palabras-voz .marca, .palabras-voz .enlace, .palabras-voz .enfasis').length).toBe(0);
    expect(raiz.querySelector('.natural')).toBeNull();
    expect(raiz.textContent).toContain('no llegaron el énfasis ni los enlaces');
  });
});
