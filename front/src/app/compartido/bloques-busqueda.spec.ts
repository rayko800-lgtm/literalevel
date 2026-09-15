import { LibroTarjeta } from '../nucleo/api';
import { bloquesBusqueda } from './bloques-busqueda';

function libro(id: string, similitud: number, dificultad: number | null): LibroTarjeta {
  return { id, titulo: id, autor: '', nivel: '', dificultad, gancho: '', descargas: 0, similitud, afinidad: 0,
    abrible: true, url: '' };
}

const ids = (ls: LibroTarjeta[]) => ls.map(l => l.id);

describe('Los bloques de Encontrar', () => {
  // Lectora B1 (1,05) que busca «amor»: el caso del diagnóstico del 14 sep.
  const nivel = 1.05;

  it('reparte lo relevante por franja y deja fuera lo que no es de lo que se pidió', () => {
    const b = bloquesBusqueda([
      libro('amor-b1', 0.52, 1.1),
      libro('amor-c1-cerca', 0.5, 1.45),
      libro('amor-b2', 0.49, 1.3),
      libro('amor-facil', 0.48, 0.5),
      libro('amor-sin-medir', 0.47, null),
      libro('amor-c2', 0.472, 1.9),
      libro('my-future', 0.3, 1.05),               // de su nivel, pero no es de amor
    ], nivel);
    expect(ids(b.enTuNivel)).toEqual(['amor-b1']);
    expect(ids(b.porEncima)).toEqual(['amor-b2', 'amor-c1-cerca']);      // el más cercano primero
    expect(ids(b.otrosNiveles)).toEqual(['amor-facil', 'amor-sin-medir', 'amor-c2']);
    expect(ids(b.menosParecidos)).toEqual(['my-future']);
  });

  it('el borde de la relevancia aguanta el redondeo a tres decimales', () => {
    const b = bloquesBusqueda([libro('mejor', 0.6, 1), libro('justo', 0.55, 1), libro('fuera', 0.548, 1)], nivel);
    expect(ids(b.enTuNivel)).toEqual(['mejor', 'justo']);
    expect(ids(b.menosParecidos)).toEqual(['fuera']);
  });

  it('las franjas son las de las etiquetas: 0,15 por encima aún es tu nivel y 0,45 aún es un poco por encima', () => {
    const b = bloquesBusqueda([libro('a', 0.5, 1.2), libro('b', 0.5, 1.5), libro('c', 0.5, 1.51), libro('d', 0.5, 0.6)], nivel);
    expect(ids(b.enTuNivel)).toEqual(['a']);
    expect(ids(b.porEncima)).toEqual(['b']);
    expect(ids(b.otrosNiveles)).toEqual(['c', 'd']);
    expect(bloquesBusqueda([], nivel)).toEqual({ enTuNivel: [], porEncima: [], otrosNiveles: [], menosParecidos: [] });
  });
});
