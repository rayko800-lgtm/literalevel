/** Velocidad compartida por audio, vídeo y animación. */
export const VELOCIDAD_MINIMA = 0.25;
export const VELOCIDAD_MAXIMA = 2;
export function velocidadValida(valor: number | undefined): number {
  return typeof valor === 'number' && Number.isFinite(valor) && valor >= VELOCIDAD_MINIMA && valor <= VELOCIDAD_MAXIMA ? valor : 1;
}
export function etiquetaVelocidad(valor: number): string { return `${velocidadValida(valor).toFixed(2).replace('.', ',')}×`; }
