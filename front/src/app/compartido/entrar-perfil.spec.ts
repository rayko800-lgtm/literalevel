import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Entrada } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { App } from '../app';
import { Inicio } from '../pantallas/inicio';
import { Pronunciar } from '../pantallas/pronunciar';
import { Ajustes } from './ajustes';

/** Los tres arreglos del informe de Ismael (auditoria/ismael_ayuda_2026-09-15.md, decisión de
 *  Miguel): «Entrar» abre los ajustes ya en «Tu perfil» con el cursor en «Usuario»; el botón de
 *  ajustes lleva su nombre; y la tarjeta «Mídeme» no promete una estimación que ya no existe. */
describe('Entrar y la ayuda de la tanda 1', () => {
  const FUERA: Entrada = { puerta: true, dentro: false, nombre: null, restantes: null, openai: true, mensaje: '' };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  async function abrirAjustes(enPerfil: boolean) {
    const sesion = TestBed.inject(Sesion);
    sesion.entrada.set(FUERA);
    if (enPerfil) sesion.abrirPerfil(); else sesion.ajustesAbiertos.set(true);
    const fixture = TestBed.createComponent(Ajustes);
    document.body.appendChild(fixture.nativeElement);
    fixture.detectChanges();
    await fixture.whenStable();
    TestBed.tick();
    return { fixture, sesion };
  }

  it('«Entrar» abre los ajustes con el cursor en «Usuario», y la marca se consume', async () => {
    const { fixture, sesion } = await abrirAjustes(true);
    const usuario = (fixture.nativeElement as HTMLElement).querySelector('input[name=usuario]');
    expect(usuario).not.toBeNull();
    expect(document.activeElement).toBe(usuario);
    expect(sesion.ajustesEnPerfil()).toBe(false);
    fixture.nativeElement.remove();
  });

  it('el botón de ajustes de siempre no mueve el cursor a «Usuario»', async () => {
    const { fixture } = await abrirAjustes(false);
    const usuario = (fixture.nativeElement as HTMLElement).querySelector('input[name=usuario]');
    expect(document.activeElement).not.toBe(usuario);
    fixture.nativeElement.remove();
  });

  it('el «Entrar» de Pronunciar pide los ajustes en «Tu perfil»', async () => {
    const sesion = TestBed.inject(Sesion);
    sesion.entrada.set(FUERA);
    const fixture = TestBed.createComponent(Pronunciar);
    fixture.detectChanges();
    await fixture.whenStable();
    const entrar = (fixture.nativeElement as HTMLElement).querySelector('.aviso.ambar button') as HTMLButtonElement;
    expect(entrar?.textContent).toContain('Entrar');
    entrar.click();
    expect(sesion.ajustesAbiertos()).toBe(true);
    expect(sesion.ajustesEnPerfil()).toBe(true);
  });

  it('la cabecera dice «Ajustes» a la vista, no solo un icono', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const boton = (fixture.nativeElement as HTMLElement).querySelector('header .boton-ajustes') as HTMLButtonElement;
    expect(boton?.textContent?.trim()).toBe('Ajustes');
    expect(boton.getAttribute('aria-label')).toMatch(/^Ajustes/);
  });

  it('«Mídeme» ya no promete una estimación desde la primera pregunta', async () => {
    const fixture = TestBed.createComponent(Inicio);
    fixture.detectChanges();
    await fixture.whenStable();
    const tarjeta = [...(fixture.nativeElement as HTMLElement).querySelectorAll('a.puerta')].find(a => a.textContent?.includes('Mídeme'));
    // Seis pasos: tres preguntas y tres fragmentos (nivel.ts:17), no «seis preguntas».
    expect(tarjeta?.textContent).toContain('Tres preguntas y tres fragmentos, uno por pantalla. Al final ves tu nivel.');
    expect(tarjeta?.textContent).not.toContain('Seis preguntas');
    expect(tarjeta?.textContent).not.toContain('estimación');
    // La figura de ejemplo, como la bienvenida: ni «tocar» ni «ahí» (4e, 15 sep).
    const figura = (fixture.nativeElement as HTMLElement).querySelector('figure.demo');
    expect(figura?.getAttribute('aria-label')).toBe('Ejemplo: mantener presionada una palabra del libro para ver qué significa en su frase');
  });
});
