import { Paleta, contraste, hslAHex } from './portada';

/** Los colores del lector teñidos con la paleta de la portada del libro. */
export interface TinteLector {
  fondo: string;
  texto: string;
  acento: string;
  acentoTexto: string;
  acentoSuave: string;
  seleccion: string;
}

/** Contraste mínimo del texto de lectura: AAA (7:1), no el 4,5 de AA. */
export const CONTRASTE_LECTURA = 7;
/** Enlaces, chips y botones con color de acento sobre el fondo teñido: AA. */
export const CONTRASTE_ACENTO = 4.5;

/** El fondo y el acento del lector a partir de la paleta de un libro,
 *  respetando si el lector está en claro u oscuro (Miguel, 14 sep).
 *
 *  El tinte es suave a propósito: el fondo solo toma el tono del libro con poca
 *  saturación, y el texto se aleja hasta pasar de 7:1. Si ni así llega (no
 *  debería: el texto puede ir hasta casi negro o casi blanco), se lleva el
 *  fondo hacia el blanco o el negro hasta que llegue. */
export function tinteLector(p: Paleta, oscuro: boolean): TinteLector {
  const tono = p.tono;
  const sat = Math.min(p.saturacion, oscuro ? 30 : 42);
  let luzFondo = oscuro ? 13 : 95;
  let luzTexto = oscuro ? 88 : 16;
  const fondo = () => hslAHex(tono, sat, luzFondo);
  const texto = () => hslAHex(tono, 22, luzTexto);
  while (contraste(texto(), fondo()) < CONTRASTE_LECTURA && (oscuro ? luzTexto < 98 : luzTexto > 4)) {
    luzTexto += oscuro ? 1 : -1;
  }
  while (contraste(texto(), fondo()) < CONTRASTE_LECTURA && (oscuro ? luzFondo > 2 : luzFondo < 99)) {
    luzFondo += oscuro ? -1 : 1;
  }
  const f = fondo();
  let luzAcento = oscuro ? 70 : 38;
  const acento = () => hslAHex(tono, Math.min(85, p.saturacion + 15), luzAcento);
  while (contraste(acento(), f) < CONTRASTE_ACENTO && (oscuro ? luzAcento < 95 : luzAcento > 5)) {
    luzAcento += oscuro ? 2 : -2;
  }
  const a = acento();
  return {
    fondo: f,
    texto: texto(),
    acento: a,
    acentoTexto: a,
    acentoSuave: hslAHex(tono, sat, oscuro ? 22 : 88),
    seleccion: `color-mix(in srgb, ${a} ${oscuro ? 34 : 24}%, transparent)`,
  };
}
