import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LibroTarjeta } from '../nucleo/api';
import { TarjetaLibro } from './tarjeta-libro';

const base: LibroTarjeta = {
  id: 'SWV100019', titulo: 'Doggie is Happy', autor: 'Parul', nivel: 'A2', dificultad: 0.35, gancho: '',
  descargas: 0, similitud: 0, afinidad: 0, abrible: true, url: '', temas: ["Children's stories"],
};

/** Contrato de f4 (8ee42f0): un cuento medido en bloque lo dice en su chip de nivel. */
describe('Tarjeta de libro medido en bloque', () => {
  async function chip(libro: LibroTarjeta): Promise<HTMLElement> {
    await TestBed.configureTestingModule({ imports: [TarjetaLibro], providers: [provideRouter([])] }).compileComponents();
    const f = TestBed.createComponent(TarjetaLibro);
    f.componentRef.setInput('libro', libro);
    f.detectChanges();
    return (f.nativeElement as HTMLElement).querySelector('.pie .chip') as HTMLElement;
  }

  it('medido en bloque: la letra y, junto a ella, «medido en bloque con otros cuentos»', async () => {
    const c = await chip({ ...base, medido_en_bloque: true });
    expect(c.textContent?.replace(/\s+/g, ' ').trim()).toBe('A2 · 0,35');
    expect(c.parentElement?.querySelector('.en-bloque')?.textContent?.trim()).toBe('medido en bloque con otros cuentos');
  });

  it('medido solo (o sin el campo): el chip de siempre', async () => {
    const c = await chip({ ...base, medido_en_bloque: false });
    expect(c.textContent?.replace(/\s+/g, ' ').trim()).toBe('A2 · 0,35');
    expect(c.parentElement?.querySelector('.en-bloque')).toBeNull();
  });
});
