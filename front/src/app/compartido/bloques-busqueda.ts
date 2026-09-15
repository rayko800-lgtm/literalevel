import { LibroTarjeta } from '../nucleo/api';

/** Lo que el motor da por relevante: a esta distancia del mejor parecido
 *  (`catalogo.MARGEN_RELEVANCIA`, f4 3524357). `similitud` llega redondeada a
 *  tres decimales, de ahí la holgura. */
export const MARGEN_RELEVANCIA = 0.05;
const HOLGURA = 0.001;
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
  for (const l of libros) {
    if (l.similitud < techo - MARGEN_RELEVANCIA - HOLGURA) { b.menosParecidos.push(l); continue; }
    const d = l.dificultad == null ? null : l.dificultad - nivel;
    if (d !== null && d > FACIL && d <= RETO) b.enTuNivel.push(l);
    else if (d !== null && d > RETO && d <= POR_ENCIMA) b.porEncima.push(l);
    else b.otrosNiveles.push(l);
  }
  b.porEncima.sort((x, y) => (x.dificultad as number) - (y.dificultad as number));
  return b;
}
