import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Entrada } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Ajustes } from './ajustes';
import { Palabras } from '../pantallas/palabras';
import { Nivel } from '../pantallas/nivel';

/** Del ensayo del guion del 16 de septiembre (auditoria/ensayo_demo_2026-09-16.md): en el paso 7
 *  de la demo, con una sola palabra consultada, se leía «1 palabras distintas». Los contadores que
 *  pueden valer uno llevan ahora su singular. Decisión de Miguel por la Central: arreglarlos todos,
 *  no solo el que se vio. Los de «capítulo/capítulos» y «libro/libros» ya lo hacían. */
describe('Los contadores concuerdan en singular', () => {
  const entrada = (restantes: number | null): Entrada =>
    ({ puerta: true, dentro: true, nombre: 'miguel', restantes, openai: true, mensaje: '' });

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  async function montarPalabras(palabras: number, consultas: number, libros: number) {
    const fixture = TestBed.createComponent(Palabras);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.cuaderno.set({ palabras, consultas, libros, entradas: [] });
    fixture.detectChanges();
    await fixture.whenStable();
    // La cifra y su palabra son dos nodos sin espacio entre ellos —los separa el CSS—, así que
    // se emparejan aquí: además de la concordancia, esto fija que el número no se despareje
    // de su sustantivo.
    return [...(fixture.nativeElement as HTMLElement).querySelectorAll('.cifras div')]
      .map(d => `${d.querySelector('strong')?.textContent?.trim()} ${d.querySelector('span')?.textContent?.trim()}`)
      .join(' · ');
  }

  it('«Mis palabras» con una sola de cada cosa: todo en singular', async () => {
    const t = await montarPalabras(1, 1, 1);
    expect(t).toContain('palabra distinta');
    expect(t).not.toContain('palabras distintas');
    expect(t).toContain('1 consulta');
    expect(t).not.toContain('consultas');
    expect(t).toContain('1 libro');
    expect(t).not.toContain('libros');
  });

  it('«Mis palabras» con varias: todo en plural', async () => {
    const t = await montarPalabras(3, 7, 2);
    expect(t).toContain('palabras distintas');
    expect(t).toContain('7 consultas');
    expect(t).toContain('2 libros');
  });

  async function textoAjustes(restantes: number | null) {
    TestBed.inject(Sesion).entrada.set(entrada(restantes));
    const fixture = TestBed.createComponent(Ajustes);
    TestBed.inject(Sesion).ajustesAbiertos.set(true);
    fixture.detectChanges();
    await fixture.whenStable();
    return (fixture.nativeElement as HTMLElement).textContent!.replace(/\s+/g, ' ').trim();
  }

  it('con un solo uso: «Te queda 1 uso.»', async () => {
    const t = await textoAjustes(1);
    expect(t).toContain('Te queda 1 uso.');
    expect(t).not.toContain('Te quedan');
    expect(t).not.toContain('usos');
  });

  it('con varios usos: «Te quedan 5 usos.»', async () => {
    const t = await textoAjustes(5);
    expect(t).toContain('Te quedan 5 usos.');
  });

  // «Mídeme con un texto» cuenta las palabras mientras se pega: al escribir la primera
  // se leía «1 palabras».
  async function contadorDeMuestra(texto: string) {
    const fixture = TestBed.createComponent(Nivel);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    c.vista.set('muestra');
    c.muestra = texto;
    fixture.detectChanges();
    await fixture.whenStable();
    const p = [...(fixture.nativeElement as HTMLElement).querySelectorAll('p')]
      .map(e => e.textContent!.replace(/\s+/g, ' ').trim())
      .find(t => /La primera medición/.test(t));
    return p ?? '';
  }

  it('la muestra con una sola palabra dice «1 palabra»', async () => {
    const t = await contadorDeMuestra('hola');
    expect(t).toContain('1 palabra.');
    expect(t).not.toContain('1 palabras');
  });

  it('la muestra con varias dice «palabras»', async () => {
    const t = await contadorDeMuestra('una frase de varias palabras');
    expect(t).toContain('5 palabras.');
  });
});
