import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Pronunciar } from './pronunciar';
import { retornoAudio } from '../nucleo/retorno-audio';

describe('Pronunciar desde la escucha', () => {
  it('carga la frase y ofrece volver al audio en ambas barras, conservando su punto', async () => {
    await TestBed.configureTestingModule({ imports: [Pronunciar], providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()] }).compileComponents();
    const fixture = TestBed.createComponent(Pronunciar);
    for (const [clave, valor] of Object.entries({ frase: 'Hello world.', libro: 'PG11', cap: '1', parte: '2', posicion: '24.5', ritmo: '1.37', regreso: 'escuchar' })) fixture.componentRef.setInput(clave, valor);
    fixture.detectChanges(); await fixture.whenStable(); fixture.detectChanges();
    expect((fixture.nativeElement.querySelector('textarea') as HTMLTextAreaElement).value).toBe('Hello world.');
    const enlaces = [...fixture.nativeElement.querySelectorAll('a')].filter((a: any) => a.textContent.includes('Volver a leer y escuchar')) as HTMLAnchorElement[];
    expect(enlaces).toHaveLength(2);
    for (const enlace of enlaces) {
      const url = new URL(enlace.href);
      expect(url.pathname).toBe('/escuchar');
      expect(Object.fromEntries(url.searchParams)).toEqual({ libro: 'PG11', cap: '1', parte: '2', posicion: '24.5', ritmo: '1.37', regreso: 'escuchar' });
    }
    fixture.destroy();
  });
  it('rechaza datos de retorno inválidos sin aceptar destinos arbitrarios', () => {
    const params = { regreso: 'escuchar', libro: 'PG11', cap: '0', parte: '0', posicion: '24', ritmo: '.83' };
    expect(retornoAudio(params)?.ritmo).toBe(.83);
    for (const cambio of [{ regreso: 'https://otro.example' }, { cap: '-1' }, { parte: '1.2' }, { posicion: 'Infinity' }, { parte: undefined }, { libro: '' }]) expect(retornoAudio({ ...params, ...cambio })).toBeNull();
    expect(retornoAudio({ ...params, ritmo: 'NaN' })?.ritmo).toBe(1);
  });
});
