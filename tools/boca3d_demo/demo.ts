/** Demostración de la escena 3D de la boca sin Angular ni router: la empaqueta
 *  `tools/boca3d_demo.mjs` con esbuild y se abre en el navegador para mirar y
 *  sacar capturas. Carga el JSON completo de poses (46 sonidos), no solo los
 *  cinco del prototipo. Vive en tools/ para que `ng build` no la compile.
 *
 *  Parámetros de la URL: ?s=ɑ (sonido), ?ciclo=0 (sin ciclo al elegir: la
 *  pose quieta, para capturas), ?palabra=ˈpɑvɚti (la reproduce),
 *  ?giro=-1.0&polar=1.2 (vista girada: negativo mira hacia la cara),
 *  ?mejilla=0 (sin mejilla), ?fps=1 (mide cuadros por segundo reproduciendo
 *  una palabra en bucle y lo escribe en la leyenda). */
import { cicloSonido, lineaPalabra } from '../../front/src/app/compartido/boca3d/animacion';
import { EscenaBoca } from '../../front/src/app/compartido/boca3d/escena';
import { CatalogoPoses, PoseSonido, poseDe, trocearIpa } from '../../front/src/app/compartido/boca3d/poses';
import catalogoJson from '../../front/src/app/compartido/boca3d/poses.ejemplo.json';

const CATALOGO = catalogoJson as unknown as CatalogoPoses;
const PALABRA_FPS = 'ˌɪntəˈnæʃənəl ˈpɑvɚti';

declare global {
  interface Window { escenaBoca: EscenaBoca; medirFps: (segundos?: number) => Promise<number>; }
}

function arrancar(): void {
  const raiz = document.getElementById('boca3d-demo') ?? document.body;
  raiz.innerHTML = `
    <div class="chips"></div>
    <div class="visor"></div>
    <p class="leyenda"></p>
    <form class="palabra"><input class="ipa" placeholder="IPA de una palabra: ˈpɑvɚti" />
      <button type="submit">Ver la palabra</button>
      <label><input type="checkbox" class="ciclo" checked /> ciclo al elegir</label></form>
    <p class="pista">Arrastra de lado para girar la boca. <button type="button" class="reset">Vista de lado</button>
      <label><input type="checkbox" class="libre" /> girar libremente (sin scroll sobre la boca)</label>
      <label><input type="checkbox" class="lento" /> transición lenta</label></p>`;
  const chips = raiz.querySelector('.chips')!;
  const visor = raiz.querySelector('.visor') as HTMLElement;
  const leyenda = raiz.querySelector('.leyenda')!;
  const lento = raiz.querySelector('.lento') as HTMLInputElement;
  const ciclo = raiz.querySelector('.ciclo') as HTMLInputElement;
  const entradaIpa = raiz.querySelector('.ipa') as HTMLInputElement;

  if (!EscenaBoca.hayWebGL()) {
    visor.textContent = 'No hay WebGL: aquí iría el corte 2D.';
    return;
  }
  const params = new URLSearchParams(location.search);
  const escena = new EscenaBoca(visor, {
    reducirMovimiento: matchMedia('(prefers-reduced-motion: reduce)').matches,
    mejilla: params.get('mejilla') !== '0',
    // ?lengua=glb: la lengua modelada en Blender (lengua.glb junto a la demo).
    lenguaGlb: params.get('lengua') === 'glb' ? 'lengua.glb' : undefined,
  });
  window.escenaBoca = escena;
  if (params.get('ciclo') === '0') ciclo.checked = false;

  const ir = (simbolo: string) => {
    const pose: PoseSonido | null = poseDe(CATALOGO, simbolo);
    if (!pose) return;
    if (ciclo.checked && simbolo) escena.reproducir(cicloSonido(pose, CATALOGO));
    else escena.irA(pose, lento.checked ? 2.5 : 0.55);
    leyenda.textContent = (simbolo ? `/${simbolo}/ · ` : 'reposo · ') + pose.leyenda;
    chips.querySelectorAll('button').forEach(b => b.classList.toggle('elegido', b.dataset['s'] === simbolo));
  };
  for (const s of ['', ...Object.keys(CATALOGO.sonidos)]) {
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset['s'] = s;
    b.textContent = s ? `/${s}/` : 'reposo';
    b.addEventListener('click', () => ir(s));
    chips.appendChild(b);
  }
  const palabra = (ipa: string) => {
    const { texto, segmentos } = trocearIpa(ipa, CATALOGO);
    if (!segmentos.length) { leyenda.textContent = `No reconozco ningún sonido en «${ipa}»`; return null; }
    const linea = lineaPalabra(segmentos, CATALOGO);
    escena.reproducir(linea);
    leyenda.textContent = `/${texto}/ · ${segmentos.map(s => s.simbolo).join(' ')} · ${linea.total.toFixed(1)} s`;
    return linea;
  };
  raiz.querySelector('.palabra')!.addEventListener('submit', e => { e.preventDefault(); palabra(entradaIpa.value); });
  raiz.querySelector('.reset')!.addEventListener('click', () => escena.restablecerVista());
  const libre = raiz.querySelector('.libre') as HTMLInputElement;
  libre.addEventListener('change', () => escena.girarLibre(libre.checked));

  // Cuadros por segundo mientras se reproduce una palabra en bucle: mide el
  // coste de deformar la lengua y pintar, no el de esperar.
  window.medirFps = (segundos = 4) => new Promise<number>(resolve => {
    let cuadros = 0;
    const t0 = performance.now();
    let linea = palabra(PALABRA_FPS)!;
    const tic = () => {
      cuadros++;
      if (!escena.enTransicion) escena.reproducir(linea);
      if (performance.now() - t0 < segundos * 1000) requestAnimationFrame(tic);
      else {
        const fps = cuadros / ((performance.now() - t0) / 1000);
        leyenda.textContent = `${fps.toFixed(1)} cuadros por segundo (${cuadros} en ${segundos} s)`;
        resolve(fps);
      }
    };
    requestAnimationFrame(tic);
  });

  ir(params.get('s') ?? '');
  const p = params.get('palabra');
  if (p) { entradaIpa.value = p; palabra(p); }
  // ?giro=0.9 abre la vista girada de entrada (para capturas sin tocar la pantalla).
  const giro = Number(params.get('giro'));
  if (giro) escena.vista(giro, Number(params.get('polar')) || 1.25);
  if (params.get('fps')) window.medirFps(Number(params.get('fps')) || 4);
}

arrancar();
