import { TestBed } from '@angular/core/testing';
import { ControlVelocidad } from './control-velocidad';
import { etiquetaVelocidad, velocidadValida } from '../nucleo/velocidad';

describe('Barra de velocidad', () => {
  it('acepta velocidades intermedias y ambos extremos, rechaza números inválidos', () => {
    for (const valor of [.25, .83, 1.37, 2]) expect(velocidadValida(valor)).toBe(valor);
    for (const valor of [undefined, NaN, Infinity, .24, 2.01]) expect(velocidadValida(valor)).toBe(1);
    expect(etiquetaVelocidad(1.37)).toBe('1,37×');
  });
  it('abre el control propio sin alterar la velocidad y emite cada movimiento', async () => {
    await TestBed.configureTestingModule({ imports: [ControlVelocidad] }).compileComponents();
    const fixture = TestBed.createComponent(ControlVelocidad), c = fixture.componentInstance;
    fixture.componentRef.setInput('valor', .83); fixture.detectChanges();
    const valores: number[] = []; c.valor.subscribe(v => valores.push(v));
    const boton = fixture.nativeElement.querySelector('.disparador-velocidad') as HTMLButtonElement;
    boton.click(); fixture.detectChanges();
    const barra = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    expect([barra.min, barra.max, barra.step]).toEqual(['0.25', '2', '0.01']);
    expect(valores).toEqual([]);
    barra.value = '1.37'; barra.dispatchEvent(new Event('input')); fixture.detectChanges();
    expect(valores).toEqual([1.37]); expect(boton.textContent).toContain('1,37×');
    barra.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); fixture.detectChanges();
    expect(c.abierta()).toBe(false); expect(document.activeElement).toBe(boton);
    fixture.destroy();
  });
});
