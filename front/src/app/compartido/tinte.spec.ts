import { FAMILIAS, Familia, contraste, paletaDe } from './portada';
import { CONTRASTE_ACENTO, CONTRASTE_LECTURA, tinteLector } from './tinte';

describe('El lector teñido con la paleta del libro', () => {
  it('el texto de lectura pasa de 7:1 y el acento de 4,5:1, en claro y en oscuro, en todas las familias', () => {
    let peorTexto = 99;
    let peorAcento = 99;
    for (const familia of Object.keys(FAMILIAS) as Familia[]) {
      for (let i = 0; i < 200; i++) {
        const p = paletaDe(`PG${i * 53 + 7}`, familia);
        for (const oscuro of [false, true]) {
          const t = tinteLector(p, oscuro);
          peorTexto = Math.min(peorTexto, contraste(t.texto, t.fondo));
          peorAcento = Math.min(peorAcento, contraste(t.acentoTexto, t.fondo));
        }
      }
    }
    expect(peorTexto).toBeGreaterThanOrEqual(CONTRASTE_LECTURA);
    expect(peorAcento).toBeGreaterThanOrEqual(CONTRASTE_ACENTO);
  });

  it('respeta el tema: fondo claro en claro y oscuro en oscuro, con el tono del libro', () => {
    const p = paletaDe('PG1661', 'misterio');
    const claro = tinteLector(p, false);
    const oscuro = tinteLector(p, true);
    expect(contraste(claro.fondo, '#ffffff')).toBeLessThan(1.25);
    expect(contraste(oscuro.fondo, '#000000')).toBeLessThan(1.6);
    // Dos familias distintas no dan el mismo fondo.
    expect(tinteLector(paletaDe('PG1661', 'mar'), false).fondo).not.toBe(claro.fondo);
  });
});
