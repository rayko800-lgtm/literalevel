import { TestBed } from '@angular/core/testing';
import { cicloSonido, giroPara, lentoParaAudio, lineaPalabra } from './animacion';
import { silencioInicial } from './audio';
import { Boca3d } from './boca3d';
import { poseNumerica } from './escena';
import { POSES_PROTOTIPO, REPOSO, poseDe, resolver, trocearIpa, CATALOGO_PROTOTIPO } from './poses';

// Distribución de la pose numérica (ver escena.ts): mandíbula, velo, labio
// superior (x, y, largo, radio), labio inferior (x, y, largo, radio), 6 nudos.
const MAND = 0, VELO = 1, LS_Y = 3, LS_LEN = 4, LI_Y = 7, NUDO = (i: number) => 10 + 2 * i;

describe('poseNumerica', () => {
  it('abre más la mandíbula en /ɑ/ que en /i/, y las dos más que con los dientes juntos', () => {
    const a = poseNumerica(POSES_PROTOTIPO['ɑ']), i = poseNumerica(POSES_PROTOTIPO['i']);
    const p = poseNumerica(POSES_PROTOTIPO['p']);
    expect(a[MAND]).toBeGreaterThan(i[MAND]);
    expect(i[MAND]).toBeGreaterThan(p[MAND]);
  });

  it('junta los labios en /p/ y los estira en /i/', () => {
    const p = poseNumerica(POSES_PROTOTIPO['p']), i = poseNumerica(POSES_PROTOTIPO['i']);
    const r = poseNumerica(REPOSO);
    // En /p/ el labio inferior sube hasta tocar el superior (sin contar el giro leve de la mandíbula).
    expect(p[LS_Y] - p[LI_Y]).toBeLessThan(r[LS_Y] - r[LI_Y]);
    expect(i[LS_LEN]).toBeGreaterThan(r[LS_LEN]);
  });

  it('baja el velo y alza el dorso hasta él en /ŋ/', () => {
    const n = poseNumerica(POSES_PROTOTIPO['ŋ']), r = poseNumerica(REPOSO);
    expect(n[VELO]).toBeLessThan(r[VELO]);              // más negativo = cuelga más
    expect(n[NUDO(2) + 1]).toBeGreaterThan(r[NUDO(2) + 1]);
  });

  it('sube la punta hacia el alvéolo en /s/ sin llegar al paladar', () => {
    const s = poseNumerica(POSES_PROTOTIPO['s']), r = poseNumerica(REPOSO);
    expect(s[NUDO(5) + 1]).toBeGreaterThan(r[NUDO(5) + 1]);
    expect(s[NUDO(5) + 1]).toBeLessThan(0.92);           // la cresta alveolar está en y = 0.92
  });

  it('nunca mete la lengua en el paladar', () => {
    for (const pose of [REPOSO, ...Object.values(POSES_PROTOTIPO)]) {
      const n = poseNumerica(pose);
      for (let i = 0; i < 6; i++) expect(n[NUDO(i) + 1]).toBeLessThan(1.6);
    }
  });
});

describe('poseDe', () => {
  it('quita las barras y devuelve el reposo con el símbolo vacío', () => {
    expect(poseDe(CATALOGO_PROTOTIPO, '/s/')).toBe(POSES_PROTOTIPO['s']);
    expect(poseDe(CATALOGO_PROTOTIPO, '')).toBe(REPOSO);
    expect(poseDe(CATALOGO_PROTOTIPO, 'x')).toBeNull();
  });

  it('encuentra los diptongos tal cual (la «a» de «aɪ» no se cambia por «æ») y una «a» suelta cae en /æ/', () => {
    const con_diptongos = {
      ...CATALOGO_PROTOTIPO,
      sonidos: { ...POSES_PROTOTIPO, 'aɪ': { ...POSES_PROTOTIPO['ɑ'], movimiento: 'diptongo' as const, hacia: POSES_PROTOTIPO['i'] },
                 'oʊ': POSES_PROTOTIPO['ɑ'], 'æ': POSES_PROTOTIPO['i'] },
    };
    expect(poseDe(con_diptongos, 'aɪ')?.movimiento).toBe('diptongo');
    expect(poseDe(con_diptongos, 'oʊ')).toBe(POSES_PROTOTIPO['ɑ']);
    expect(poseDe(con_diptongos, 'a')).toBe(POSES_PROTOTIPO['i']);          // «a» suelta → /æ/
    expect(cicloSonido(poseDe(con_diptongos, 'aɪ')!, con_diptongos).claves.length).toBe(8);
  });

  it('acepta los símbolos del inventario británico de la API: «iː» y «ɑː» caen en /i/ y /ɑ/', () => {
    expect(poseDe(CATALOGO_PROTOTIPO, 'iː', 'rp')).toBe(POSES_PROTOTIPO['i']);
    expect(poseDe(CATALOGO_PROTOTIPO, 'ɑː', 'rp')).toBe(POSES_PROTOTIPO['ɑ']);
    // Lo que el británico articula distinto va en `rp` y gana al americano.
    const con_rp = { ...CATALOGO_PROTOTIPO, rp: { 'ɑː': POSES_PROTOTIPO['i'] } };
    expect(poseDe(con_rp, 'ɑː', 'rp')).toBe(POSES_PROTOTIPO['i']);
    expect(poseDe(con_rp, 'ɑ', 'ga')).toBe(POSES_PROTOTIPO['ɑ']);
  });
});

describe('trocearIpa y resolver', () => {
  it('reconoce los sonidos del catálogo, salta lo que no conoce y apunta el acento a la vocal', () => {
    const { texto, segmentos } = trocearIpa('/ˈspɑŋk/', CATALOGO_PROTOTIPO);
    expect(texto).toBe('ˈspɑŋk');
    expect(segmentos.map(s => s.simbolo)).toEqual(['s', 'p', 'ɑ', 'ŋ']);   // la k no está en el prototipo
    expect(segmentos.map(s => s.acento_silaba)).toEqual([1, 1, 1, 0]);
  });

  it('coarticula: /p/ toma el cuerpo de la vocal que sigue y no la punta de una consonante', () => {
    const p = resolver(POSES_PROTOTIPO['p'], POSES_PROTOTIPO['i']);
    expect(p.cuerpo).toEqual([1, 1]);
    expect(p.labios).toBe('cerrados');                  // lo suyo no se toca
    const p2 = resolver(POSES_PROTOTIPO['p'], POSES_PROTOTIPO['s']);
    expect(p2.punta).toBe('reposo');                    // una consonante no presta la punta
    expect(p2.cuerpo).toEqual([0.62, 0.65]);
  });
});

describe('líneas de tiempo', () => {
  it('la cámara gira 30° hacia la cara solo en los sonidos con labios redondeados o estirados', () => {
    expect(giroPara(POSES_PROTOTIPO['i'])).toBeCloseTo(-Math.PI / 6, 6);      // estirados
    expect(giroPara({ ...REPOSO, labios: 'muy_redondeados' })).toBeLessThan(0);
    expect(giroPara(POSES_PROTOTIPO['p'])).toBe(0);                           // cerrados
    expect(giroPara(POSES_PROTOTIPO['ɑ'])).toBe(0);                           // neutros
  });

  it('la /h/, que lo deja todo libre, abre la mandíbula en su ciclo para que se vea algo', () => {
    const h = { ...REPOSO, movimiento: 'fricativa' as const, sonora: false, lugar: 'glotal',
                libres: ['mandibula', 'labios', 'punta', 'cuerpo'] as const, leyenda: 'aire en la garganta' };
    const l = cicloSonido({ ...h, libres: [...h.libres] }, CATALOGO_PROTOTIPO);
    expect(l.quieta.mandibula).toBeGreaterThan(REPOSO.mandibula + 0.2);
    expect(l.claves.some(c => c.pose.mandibula > REPOSO.mandibula + 0.2)).toBe(true);
    const n = poseNumerica(l.quieta);
    expect(n[n.length - 1]).toBe(1);                   // el aire oral, último valor de la pose numérica
    expect(poseNumerica(REPOSO)[n.length - 1]).toBe(0);
  });

  it('el ciclo de un sonido dura 2,8 s, empieza y acaba en reposo y pasa por el sonido', () => {
    const l = cicloSonido(POSES_PROTOTIPO['p'], CATALOGO_PROTOTIPO);
    expect(l.total).toBe(2.8);
    expect(l.claves[0].pose).toBe(REPOSO);
    expect(l.claves[l.claves.length - 1].pose).toBe(REPOSO);
    expect(l.claves.some(c => c.pose.labios === 'cerrados')).toBe(true);
    expect(l.claves.some(c => c.hacia === REPOSO && c.f === 0.5)).toBe(true);   // la suelta
    expect(l.quieta.labios).toBe('cerrados');
    for (let i = 1; i < l.claves.length; i++) expect(l.claves[i].t).toBeGreaterThanOrEqual(l.claves[i - 1].t);
  });

  it('la palabra suma las duraciones del catálogo (larga ×1,25, acento ×1,4, ×1,6) más el reposo', () => {
    const { segmentos } = trocearIpa('ˈsi', CATALOGO_PROTOTIPO);
    const l = lineaPalabra(segmentos, CATALOGO_PROTOTIPO);
    // La marca ˈ afecta a la sílaba entera: la /s/ de delante también va ×1,4, como en el 2D.
    const esperado = 0.45 + (0.22 * 1.4 * 1.6) + (0.34 * 1.25 * 1.4 * 1.6) + 1.0;
    expect(l.total).toBeCloseTo(esperado, 6);
    expect(l.quieta.cuerpo).toEqual([1, 1]);           // la vocal acentuada
    const s = l.claves.find(c => c.pose.punta === 'alveolar')!;
    expect(s.pose.cuerpo).toEqual([0.62, 0.65]);       // la /s/ tiene cuerpo propio
    for (let i = 1; i < l.claves.length; i++) expect(l.claves[i].t).toBeGreaterThanOrEqual(l.claves[i - 1].t);
    expect(l.sonidoEn).toBeCloseTo(0.45, 6);            // la palabra suena al acabar el reposo inicial
  });

  it('el sonido de un ciclo suena cuando la boca llega a la pose, no al arrancar', () => {
    const l = cicloSonido(POSES_PROTOTIPO['p'], CATALOGO_PROTOTIPO);
    expect(l.sonidoEn).toBeCloseTo(0.95, 6);
    expect(l.claves.findIndex(c => c.pose.labios === 'cerrados')).toBe(2);
    expect(cicloSonido(POSES_PROTOTIPO['i'], CATALOGO_PROTOTIPO).sonidoEn).toBeCloseTo(0.95, 6);
  });

  it('con audio, la palabra dura lo que dura la parte hablada del audio', () => {
    const { segmentos } = trocearIpa('ˈsi', CATALOGO_PROTOTIPO);
    const base = 0.22 * 1.4 + 0.34 * 1.25 * 1.4;          // sin ×1,6
    // Un audio de 1,2 s con 0,1 s de silencio inicial: hablado 0,95 s.
    const lento = lentoParaAudio(segmentos, CATALOGO_PROTOTIPO, 1.2, 0.1);
    expect(lento).toBeCloseTo(0.95 / base, 6);
    const l = lineaPalabra(segmentos, CATALOGO_PROTOTIPO, lento);
    expect(l.total).toBeCloseTo(0.45 + 0.95 + 1.0, 6);
    // Acotado: un audio absurdo no deja la boca parada ni frenética.
    expect(lentoParaAudio(segmentos, CATALOGO_PROTOTIPO, 30)).toBe(3);
    expect(lentoParaAudio(segmentos, CATALOGO_PROTOTIPO, 0.05)).toBe(0.35);
    expect(lentoParaAudio(segmentos, CATALOGO_PROTOTIPO, 0)).toBe(1.6);
  });

  it('mide el silencio inicial del audio y lo acota a medio segundo', () => {
    const f = 1000;
    const canal = new Float32Array(f);                    // 1 s
    for (let i = 250; i < f; i++) canal[i] = 0.3;         // suena a partir de 0,25 s
    expect(silencioInicial([canal], f)).toBeCloseTo(0.25, 6);
    expect(silencioInicial([new Float32Array(f)], f)).toBeCloseTo(0.12, 6);   // todo silencio: el fijo
    expect(silencioInicial([], f)).toBe(0);
  });
});

describe('Boca3d', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [Boca3d] }).compileComponents();
  });

  it('sin WebGL (jsdom) pinta el corte 2D que le dan', async () => {
    const fixture = TestBed.createComponent(Boca3d);
    fixture.componentRef.setInput('svg2dUrl', '/corte/s.svg');
    fixture.componentRef.setInput('sonido', 's');
    await fixture.whenStable();
    fixture.detectChanges();
    const raiz = fixture.nativeElement as HTMLElement;
    expect(fixture.componentInstance.modo()).toBe('2d');
    expect(raiz.querySelector('canvas')).toBeNull();
    const img = raiz.querySelector('img.respaldo') as HTMLImageElement;
    expect(img.getAttribute('src')).toBe('/corte/s.svg');
    expect(img.alt).toContain('/s/');
  });

  it('sin URL dada, el respaldo es el SVG de la API del sonido elegido', async () => {
    const fixture = TestBed.createComponent(Boca3d);
    fixture.componentRef.setInput('sonido', 'ŋ');
    await fixture.whenStable();
    fixture.detectChanges();
    const img = (fixture.nativeElement as HTMLElement).querySelector('img.respaldo') as HTMLImageElement;
    expect(img.getAttribute('src')).toBe('/api/articulacion/ga/%C5%8B.svg');
    fixture.componentRef.setInput('acento', 'rp');
    fixture.detectChanges();
    expect(img.getAttribute('src')).toBe('/api/articulacion/rp/%C5%8B.svg');
  });

  it('con la URL apagada y sin WebGL lo dice con una frase, y el selector cambia la leyenda', async () => {
    const fixture = TestBed.createComponent(Boca3d);
    fixture.componentRef.setInput('conSelector', true);
    fixture.componentRef.setInput('svg2dUrl', '');
    await fixture.whenStable();
    fixture.detectChanges();
    const raiz = fixture.nativeElement as HTMLElement;
    expect(fixture.componentInstance.modo()).toBe('2d');
    expect(raiz.querySelector('img.respaldo')).toBeNull();
    expect(raiz.querySelector('.sin')?.textContent).toContain('3D');
    expect(raiz.querySelectorAll('.chip').length).toBe(47);   // reposo + inventario completo
    fixture.componentInstance.elegir('ŋ');
    fixture.detectChanges();
    expect(raiz.querySelector('.leyenda')?.textContent).toContain('velo');
  });

  it('el catalogo completo tiene poses finitas y objetivos de diptongo', () => {
    const fixture = TestBed.createComponent(Boca3d);
    const catalogo = fixture.componentInstance.catalogo();
    const revisar = (pose: typeof REPOSO) => {
      expect(pose.cuerpo.length).toBe(2);
      expect([...poseNumerica(pose)].every(Number.isFinite)).toBe(true);
      if (pose.hacia) revisar(pose.hacia);
    };
    [catalogo.reposo, ...Object.values(catalogo.sonidos), ...Object.values(catalogo.rp ?? {})].forEach(revisar);
    expect(poseDe(catalogo, 'θ')).not.toBeNull();
    expect(poseDe(catalogo, 'əʊ', 'rp')?.hacia).toBeTruthy();
  });

  it('conserva el acento de la palabra aunque el fonema use el respaldo americano', () => {
    const fixture = TestBed.createComponent(Boca3d);
    fixture.componentRef.setInput('sonido', 'ɚ');
    fixture.componentRef.setInput('acento', 'ga');
    fixture.componentRef.setInput('ipa', 'əʊ');
    fixture.componentRef.setInput('acentoIpa', 'rp');
    const c = fixture.componentInstance;
    expect(c.segmentos()[0].pose).toEqual(poseDe(c.catalogo(), 'əʊ', 'rp'));
    expect(c.pose()).toEqual(poseDe(c.catalogo(), 'ɚ', 'ga'));
  });
});
