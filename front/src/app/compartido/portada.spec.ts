import { FAMILIAS, Familia, contraste, familiaDe, hslAHex, huella, motivoDe, paletaDe } from './portada';

describe('La portada tipográfica', () => {
  it('agrupa los temas reales de Gutenberg y de los corpus libres en su familia', () => {
    const casos: [string[], Familia][] = [
      [['Science fiction', 'Short stories'], 'ciencia'],
      [['Detective and mystery stories', 'England -- Fiction'], 'misterio'],
      // Los temas reales de PG1661 (Sherlock Holmes) no dicen «detective».
      [['Holmes, Sherlock (Fictitious character) -- Fiction', 'Private investigators -- England -- Fiction'], 'misterio'],
      [['Love stories', 'Man-woman relationships -- Fiction'], 'amor'],
      [['Fairy tales'], 'fantasia'],
      [['English poetry'], 'poesia'],
      [['Comedy plays'], 'teatro'],
      [['Sea stories'], 'mar'],
      [['Western stories'], 'aventura'],
      [['Adventure and adventurers -- Juvenile fiction'], 'aventura'],
      [['Historical fiction', 'World War, 1914-1918 -- Fiction'], 'historia'],
      [["Children's stories", 'StoryWeaver reading level 2'], 'infantil'],
      [['Conduct of life -- Juvenile fiction'], 'infantil'],
      [['VOA Learning English', 'Words & Their Stories'], 'ensayo'],
      [['Essays'], 'ensayo'],
      [['Domestic fiction', 'Psychological fiction'], 'novela'],
      [[], 'novela'],
    ];
    for (const [temas, familia] of casos) expect([temas, familiaDe(temas)]).toEqual([temas, familia]);
  });

  it('el mismo libro da siempre la misma portada y dos libros distintos, otra', () => {
    expect(huella('PG1661')).toBe(huella('PG1661'));
    expect(paletaDe('PG1661', 'misterio')).toEqual(paletaDe('PG1661', 'misterio'));
    expect(motivoDe('PG1661', paletaDe('PG1661', 'misterio'))).toEqual(motivoDe('PG1661', paletaDe('PG1661', 'misterio')));
    expect(paletaDe('PG1661', 'misterio').fondo).not.toBe(paletaDe('PG84', 'misterio').fondo);
    expect(hslAHex(0, 100, 50)).toBe('#ff0000');
    expect(hslAHex(210, 50, 40)).toBe('#336699');
  });

  it('el título se lee sobre el fondo (≥ 4,5:1) en todas las familias y con muchos ids', () => {
    let peor = 99;
    for (const familia of Object.keys(FAMILIAS) as Familia[]) {
      for (let i = 0; i < 300; i++) {
        const p = paletaDe(`PG${i * 37}`, familia);
        peor = Math.min(peor, contraste(p.tinta, p.fondo), contraste(p.tinta, p.hondo));
        expect(motivoDe(`PG${i * 37}`, p).length).toBeGreaterThan(0);
      }
    }
    expect(peor).toBeGreaterThanOrEqual(4.5);
  });
});
