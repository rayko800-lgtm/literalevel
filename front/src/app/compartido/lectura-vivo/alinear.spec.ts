import { describe, expect, it } from 'vitest';
import { Seguidor, coincide, normalizar, trocearTexto } from './alinear';

const texto = 'It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.';

describe('D5: seguir la lectura en voz alta', () => {
  it('normaliza puntuación, mayúsculas y apóstrofos', () => {
    expect(normalizar('Acknowledged,')).toBe('acknowledged');
    expect(normalizar('Don’t')).toBe("don't");
    expect(trocearTexto('— Well, sir! —').map(p => p.clave)).toEqual(['well', 'sir']);
  });

  it('una lectura completa marca todo leído, a trozos partidos como llegan', () => {
    const s = new Seguidor(trocearTexto(texto));
    for (const t of ['It is a truth universally', ' acknowledged that a single man', ' in possession of a good fortune must be in want of a wife.']) s.oir(t);
    expect(s.terminado).toBe(true);
    expect(s.palabras.every(p => p.estado === 'leida')).toBe(true);
  });

  it('las palabras saltadas se marcan y el puntero sigue', () => {
    const s = new Seguidor(trocearTexto(texto));
    s.oir('It is a truth acknowledged that a single man');
    expect(s.saltadas.map(p => p.clave)).toEqual(['universally']);
    expect(s.palabras[s.puntero].clave).toBe('in');
  });

  it('una palabra mal oída o de más no hace perder el sitio', () => {
    const s = new Seguidor(trocearTexto(texto));
    s.oir('It is uh a truth universaly acknowledged');
    expect(s.saltadas.length).toBe(0);
    expect(s.sueltas).toContain('uh');
    expect(s.palabras[s.puntero].clave).toBe('that');
  });

  it('casi igual solo en palabras largas', () => {
    expect(coincide('fortunes', 'fortune')).toBe(true);
    expect(coincide('man', 'men')).toBe(false);
    expect(coincide('cannot', 'cannot')).toBe(true);
  });
});

describe('D5: sin saltos falsos', () => {
  it('leer otro texto no marca como saltadas las palabras cortas que casan sueltas', () => {
    const s = new Seguidor(trocearTexto('"My dear Mr. Bennet," said his lady to him one day, "have you heard that Netherfield Park is let at last?"'));
    s.oir('It is a truth universally acknowledged that a single man in possession of a good fortune');
    expect(s.saltadas.length).toBe(0);
    expect(s.puntero).toBe(0);
  });

  it('un salto de verdad se confirma con la palabra siguiente', () => {
    const s = new Seguidor(trocearTexto('My dear Mr. Bennet said his lady to him one day'));
    s.oir('My dear said his lady');
    expect(s.saltadas.map(p => p.clave)).toEqual(['mr', 'bennet']);
    expect(s.palabras[s.puntero].clave).toBe('to');
  });
});

describe('D5: palabras que el modelo junta', () => {
  it('«someone» por «some one» cuenta las dos como leídas', () => {
    const s = new Seguidor(trocearTexto('property of some one or other'));
    s.oir('property of someone or other');
    expect(s.saltadas.length).toBe(0);
    expect(s.terminado).toBe(true);
  });
});
