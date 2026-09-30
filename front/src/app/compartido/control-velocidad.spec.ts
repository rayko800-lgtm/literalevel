import { TestBed } from '@angular/core/testing';
import { ControlVelocidad } from './control-velocidad';
import { etiquetaVelocidad, velocidadValida } from '../nucleo/velocidad';
import { vi } from 'vitest';

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
  it('se cierra al repetir el botón, pulsar la X o tocar fuera; abrir otro cierra el anterior', async () => {
    await TestBed.configureTestingModule({ imports: [ControlVelocidad] }).compileComponents();
    const uno = TestBed.createComponent(ControlVelocidad), dos = TestBed.createComponent(ControlVelocidad);
    uno.detectChanges(); dos.detectChanges();
    const boton = uno.nativeElement.querySelector('.disparador-velocidad') as HTMLButtonElement;
    boton.click(); uno.detectChanges(); boton.click(); uno.detectChanges();
    expect(uno.nativeElement.querySelector('input')).toBeNull();
    boton.click(); uno.detectChanges(); uno.nativeElement.querySelector('[aria-label="Cerrar velocidad"]').click(); uno.detectChanges();
    expect(uno.componentInstance.abierta()).toBe(false);
    boton.click(); uno.detectChanges();
    const otro = dos.nativeElement.querySelector('.disparador-velocidad') as HTMLButtonElement;
    otro.dispatchEvent(new Event('pointerdown', { bubbles: true })); otro.click(); uno.detectChanges(); dos.detectChanges();
    expect(uno.componentInstance.abierta()).toBe(false); expect(dos.componentInstance.abierta()).toBe(true);
    document.body.dispatchEvent(new Event('pointerdown', { bubbles: true })); dos.detectChanges();
    expect(dos.nativeElement.querySelector('input')).toBeNull();
    uno.destroy(); dos.destroy();
  });
  it('abrir y cerrar rápidamente cancela el pintado pendiente del panel', async () => {
    await TestBed.configureTestingModule({ imports: [ControlVelocidad] }).compileComponents();
    const cancelada = vi.spyOn(window, 'cancelAnimationFrame');
    const fixture = TestBed.createComponent(ControlVelocidad); fixture.detectChanges();
    const boton = fixture.nativeElement.querySelector('.disparador-velocidad') as HTMLButtonElement;
    boton.click(); fixture.detectChanges(); boton.click(); fixture.detectChanges();
    expect(cancelada).toHaveBeenCalled(); expect(fixture.componentInstance.abierta()).toBe(false);
    expect(fixture.nativeElement.querySelector('.selector-velocidad')).toBeNull();
    fixture.destroy(); cancelada.mockRestore();
  });
});
