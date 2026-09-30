import { Params } from '@angular/router';
import { velocidadValida } from './velocidad';

export interface RetornoAudio { libro: string; cap: number; parte: number; posicion: number; ritmo: number; }

/** Solo admite un regreso a una lectura concreta; nunca una URL arbitraria. */
export function retornoAudio(params: Params): RetornoAudio | null {
  if (params['regreso'] !== 'escuchar' || typeof params['libro'] !== 'string' || !params['libro']) return null;
  const cap = Number(params['cap']), parte = Number(params['parte']), posicion = Number(params['posicion']);
  if (params['cap'] == null || params['parte'] == null || params['posicion'] == null
      || !Number.isSafeInteger(cap) || cap < 0 || !Number.isSafeInteger(parte) || parte < 0
      || !Number.isFinite(posicion) || posicion < 0 || posicion > 86400) return null;
  return { libro: params['libro'], cap, parte, posicion, ritmo: velocidadValida(Number(params['ritmo'])) };
}
