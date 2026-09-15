import { LibroTarjeta } from '../nucleo/api';

/** Lo que el motor da por relevante: a esta distancia del mejor parecido
 *  (`catalogo.MARGEN_RELEVANCIA`, f4 3524357). `similitud` llega redondeada a
 *  tres decimales, de ahí la holgura. */
export const MARGEN_RELEVANCIA = 0.05;
const HOLGURA = 0.001;
/** Lo que cae en la franja del lector (de «Fácil» a «Un poco por encima») se da por
 *  relevante con un margen más ancho: con 0,05, en «historias de la luna» los cinco
 *  cuentos A2–B1 (0,704 a 0,738 frente a un techo de 0,802) quedaban en «Menos
 *  parecidos» detrás de catorce libros C1–C2 (SERIO del anexo de la ronda 2; decisión
 *  de la Central: margen más ancho solo en la franja, sin bloque nuevo ni API).
 *  Dos guardas para que el nivel no vuelva a pesar más que el tema (caso Esmeralda),
 *  medidas en el Space del reinicio 19 sobre quince búsquedas:
 *  - PARECIDO_MINIMO_EN_FRANJA: el libro tiene que parecerse de verdad a la búsqueda.
 *    En «Terror gótico» (techo 0,675) subía «ACTION PART-1», un cuento de terroristas,
 *    con 0,586; los candidatos del tema estaban todos en 0,651 o más.
 *  - SALTO: no se cruza un hueco mayor que el margen de relevancia entre parecidos
 *    seguidos. En «Jane Austen» hay 0,062 entre los títulos con su nombre (0,855) y el
 *    resto (0,793), y detrás estaba «Calamity Jane». */
export const MARGEN_EN_FRANJA = 0.10;
export const PARECIDO_MINIMO_EN_FRANJA = 0.65;
const SALTO = MARGEN_RELEVANCIA;
/** Las mismas franjas que las etiquetas de `encaje`: hasta 0,15 por encima es
 *  «A tu medida» (`perfil.RETO`), y hasta 0,45, «Un reto». */
const FACIL = -0.45;
const RETO = 0.15;
const POR_ENCIMA = 0.45;

export interface BloquesBusqueda {
  /** De lo que se pidió y a su medida. */
  enTuNivel: LibroTarjeta[];
  /** De lo que se pidió y un escalón por encima, el más cercano primero. */
  porEncima: LibroTarjeta[];
  /** De lo que se pidió, pero más fáciles, mucho más difíciles o sin medir. */
  otrosNiveles: LibroTarjeta[];
  /** Lo que el motor devuelve detrás y no es de lo que se pidió: sin etiqueta de encaje. */
  menosParecidos: LibroTarjeta[];
}

/** Reparte los resultados de /api/buscar en los bloques de Encontrar
 *  (auditoria/diagnostico_encontrar_amor_b1_2026-09-14.md, aprobado por Miguel):
 *  «A tu medida» solo puede salir en lo que es de lo que se pidió. */
export function bloquesBusqueda(libros: LibroTarjeta[], nivel: number): BloquesBusqueda {
  const b: BloquesBusqueda = { enTuNivel: [], porEncima: [], otrosNiveles: [], menosParecidos: [] };
  if (!libros.length) return b;
  const techo = Math.max(...libros.map(l => l.similitud));
  // Hasta dónde bajan los parecidos desde el techo sin un hueco mayor que SALTO.
  let suelo = techo;
  for (const s of libros.map(l => l.similitud).sort((x, y) => y - x)) {
    if (suelo - s > SALTO + HOLGURA) break;
    suelo = s;
  }
  for (const l of libros) {
    const d = l.dificultad == null ? null : l.dificultad - nivel;
    const enFranja = d !== null && d > FACIL && d <= POR_ENCIMA;
    const relevante = l.similitud >= techo - MARGEN_RELEVANCIA - HOLGURA;
    const subePorFranja = enFranja && l.similitud >= techo - MARGEN_EN_FRANJA - HOLGURA
      && l.similitud >= PARECIDO_MINIMO_EN_FRANJA && l.similitud >= suelo - HOLGURA;
    if (!relevante && !subePorFranja) { b.menosParecidos.push(l); continue; }
    if (d !== null && d > FACIL && d <= RETO) b.enTuNivel.push(l);
    else if (d !== null && d > RETO && d <= POR_ENCIMA) b.porEncima.push(l);
    else b.otrosNiveles.push(l);
  }
  b.porEncima.sort((x, y) => (x.dificultad as number) - (y.dificultad as number));
  return b;
}
