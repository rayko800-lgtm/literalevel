import { tiempoLlano } from './formato';

describe('El tiempo de lectura en llano', () => {
  it('«1 minutos» pasa a «1 minuto» y lo demás no se toca', () => {
    expect(tiempoLlano('1 minutos')).toBe('1 minuto');
    expect(tiempoLlano('11 minutos')).toBe('11 minutos');
    expect(tiempoLlano('21 minutos')).toBe('21 minutos');
    expect(tiempoLlano('2 minutos')).toBe('2 minutos');
    expect(tiempoLlano('2 h 01 min')).toBe('2 h 01 min');
    expect(tiempoLlano(null)).toBe('');
  });

  it('un rango con los dos extremos iguales se dice una vez', () => {
    expect(tiempoLlano('entre 1 minutos y 1 minutos')).toBe('1 minuto');
    expect(tiempoLlano('entre 12 minutos y 12 minutos')).toBe('12 minutos');
    expect(tiempoLlano('entre 2 h 05 min y 2 h 05 min de lectura')).toBe('2 h 05 min de lectura');
    expect(tiempoLlano('entre 1 minuto y 2 minutos')).toBe('entre 1 minuto y 2 minutos');
    expect(tiempoLlano('entre 2 minutos y 21 minutos')).toBe('entre 2 minutos y 21 minutos');
    expect(tiempoLlano('entre 1 h y 1 h 30 min')).toBe('entre 1 h y 1 h 30 min');
  });
});
