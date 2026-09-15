import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Pronunciar } from './pronunciar';

/** Tanda 2 de la ayuda (Miguel, sobre el informe de Ismael): la línea de ayuda de Pronunciar
 *  sale la primera vez en lugar del subtítulo, se cierra con ✕ para siempre en este navegador
 *  y el «?» junto al título la vuelve a abrir. */
describe('Pronunciar: la línea de ayuda', () => {
  const TEXTO = 'Escribe o trae una frase, grábate leyéndola y te digo qué sonido corregir. Sin entrar puedes grabarte, escucharte y ver cómo se dice cada sonido.';

  beforeEach(async () => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  async function montar() {
    const fixture = TestBed.createComponent(Pronunciar);
    fixture.detectChanges();
    await fixture.whenStable();
    const raiz = fixture.nativeElement as HTMLElement;
    return { fixture, raiz, cabecera: () => raiz.querySelector('.cabecera-pagina') as HTMLElement };
  }

  it('la primera vez sale arriba, en la cabecera, en lugar del subtítulo', async () => {
    const { cabecera } = await montar();
    const nota = cabecera().querySelector('.linea-ayuda');
    expect(nota?.textContent).toContain(TEXTO);
    expect(cabecera().textContent).not.toContain('Graba la frase y te digo qué palabras se entendieron');
    // Va antes de la tarjeta de la frase y fuera de la barra fija del micrófono.
    expect(nota?.closest('.grabadora')).toBeNull();
  });

  it('✕ la cierra, vuelve el subtítulo, y no sale al volver a la pantalla', async () => {
    const { fixture, cabecera } = await montar();
    (cabecera().querySelector('.linea-ayuda button') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(cabecera().querySelector('.linea-ayuda')).toBeNull();
    expect(cabecera().textContent).toContain('Graba la frase y te digo');
    fixture.destroy();
    const otra = await montar();
    expect(otra.cabecera().querySelector('.linea-ayuda')).toBeNull();
  });

  it('el «?» la vuelve a abrir', async () => {
    const { fixture, cabecera } = await montar();
    (cabecera().querySelector('.linea-ayuda button') as HTMLButtonElement).click();
    fixture.detectChanges();
    const ayuda = cabecera().querySelector('button.ayuda') as HTMLButtonElement;
    expect(ayuda.textContent?.trim()).toBe('?');
    expect(ayuda.getAttribute('aria-expanded')).toBe('false');
    ayuda.click();
    fixture.detectChanges();
    expect(cabecera().querySelector('.linea-ayuda')?.textContent).toContain(TEXTO);
    expect(ayuda.getAttribute('aria-expanded')).toBe('true');
  });
});
