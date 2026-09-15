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
});
