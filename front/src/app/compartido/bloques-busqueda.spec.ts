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

  it('el borde de la relevancia es exacto en milésimas: a 0,050 del techo entra y a 0,051 no', () => {
    const b = bloquesBusqueda([libro('mejor', 0.6, 1), libro('justo', 0.55, 1), libro('fuera', 0.549, 1)], nivel);
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

  // Casos reales del Space en el reinicio 19 (053a486), lectora B1 a 0,80.
  const b1 = 0.8;

  it('«historias de la luna»: los cinco cuentos de su franja suben aunque estén a más de 0,05 del techo', () => {
    const b = bloquesBusqueda([
      libro('the-moon-tratado', 0.802, 1.761),
      libro('the-moon-elger', 0.785, 1.695),
      libro('romance-of-the-moon', 0.79, 1.818),
      libro('moon-endureth', 0.757, 1.849),
      libro('adventures-in-the-moon', 0.747, 1.947),
      libro('aditi', 0.738, 0.458),
      libro('moon-glow', 0.732, 1.577),
      libro('journey', 0.731, 0.776),
      libro('chandu', 0.723, 0.618),
      libro('moon-and-sun', 0.715, 0.956),
      libro('man-in-the-moon', 0.708, 1.393),
      libro('moon-and-hockey', 0.704, 0.701),
      libro('moon-fairy', 0.694, 1.298),         // de su franja, pero a más de 0,10 del techo
    ], b1);
    expect(ids(b.enTuNivel)).toEqual(['aditi', 'journey', 'chandu', 'moon-and-hockey']);
    expect(ids(b.porEncima)).toEqual(['moon-and-sun']);
    // Los relevantes de siempre (a 0,05 del techo) siguen donde estaban: C1–C2 para ella.
    expect(ids(b.otrosNiveles)).toEqual(['the-moon-tratado', 'the-moon-elger', 'romance-of-the-moon', 'moon-endureth']);
    expect(b.menosParecidos.map(l => l.id)).toContain('moon-fairy');
    expect(b.menosParecidos.map(l => l.id)).toContain('man-in-the-moon');   // C1 para ella: el margen ancho es solo de la franja
  });

  it('«Terror gótico»: un cuento de terroristas de su franja no sube con un parecido flojo', () => {
    const b = bloquesBusqueda([
      libro('carmilla', 0.675, 1.8), libro('otro', 0.656, 1.9), libro('tercero', 0.629, 1.85),
      libro('action-part-1', 0.586, 1.07),
    ], b1);
    expect(ids(b.porEncima)).toEqual([]);
    expect(ids(b.menosParecidos)).toEqual(['action-part-1']);
  });

  it('«Jane Austen»: no se cruza el salto entre los títulos con su nombre y el resto', () => {
    const b = bloquesBusqueda([
      libro('memoir', 0.857, 1.889), libro('her-times', 0.857, 1.867), libro('play', 0.856, 1.577),
      libro('emma', 0.793, 1.862), libro('persuasion', 0.793, 1.895),
      libro('calamity-jane', 0.79, 1.39),
    ], 0.953);
    expect(ids(b.porEncima)).toEqual([]);
    expect(ids(b.enTuNivel)).toEqual([]);
    expect(b.menosParecidos.map(l => l.id)).toContain('calamity-jane');
  });

  // Bordes de la regla de la franja (ronda 3 del front de 4e): cada caso cae de un
  // lado u otro por una milésima, así que mover una constante o cambiar un >= por >
  // pone la prueba en rojo. Los de 1,9 son C2 para ella y solo hacen de techo y escalera.
  it('el parecido mínimo en la franja es 0,650: 0,650 sube y 0,649 no', () => {
    const b = bloquesBusqueda([
      libro('techo', 0.72, 1.9), libro('medio', 0.68, 1.9),
      libro('justo-650', 0.65, 0.8), libro('corto-649', 0.649, 0.8),
    ], b1);
    expect(ids(b.enTuNivel)).toEqual(['justo-650']);
    expect(ids(b.menosParecidos)).toEqual(['corto-649']);
  });

  it('un hueco de 0,050 entre parecidos seguidos se cruza y uno de 0,051 no', () => {
    const cruza = bloquesBusqueda([libro('techo', 0.8, 1.9), libro('medio', 0.78, 1.9), libro('tras-050', 0.73, 0.8)], b1);
    expect(ids(cruza.enTuNivel)).toEqual(['tras-050']);
    const corta = bloquesBusqueda([libro('techo', 0.8, 1.9), libro('medio', 0.78, 1.9), libro('tras-051', 0.729, 0.8)], b1);
    expect(ids(corta.enTuNivel)).toEqual([]);
    expect(ids(corta.menosParecidos)).toEqual(['tras-051']);
  });

  it('con franja, a 0,100 del techo sube y a 0,101 no', () => {
    const b = bloquesBusqueda([
      libro('techo', 0.8, 1.9), libro('escalon-1', 0.76, 1.9), libro('escalon-2', 0.72, 1.9),
      libro('a-100', 0.7, 0.8), libro('a-101', 0.699, 0.8),
    ], b1);
    expect(ids(b.enTuNivel)).toEqual(['a-100']);
    expect(ids(b.menosParecidos)).toEqual(['escalon-2', 'a-101']);
  });
});
