/** Demostración de la escena 3D de la boca sin Angular ni router: la empaqueta
 *  `tools/boca3d_demo.mjs` con esbuild y se abre en el navegador para mirar y
 *  sacar capturas. Carga el JSON completo de poses (46 sonidos), no solo los
 *  cinco del prototipo. Vive en tools/ para que `ng build` no la compile.
 *
 *  Parámetros de la URL: ?s=ɑ (sonido), ?ciclo=0 (sin ciclo al elegir: la
 *  pose quieta, para capturas), ?palabra=ˈpɑvɚti (la reproduce),
 *  ?giro=-1.0&polar=1.2 (vista girada: negativo mira hacia la cara),
 *  ?velocidad=0.5 (o 0.25: boca y audio despacio), ?audio=palabra.mp3 (con «Ver la palabra», suena y la línea se escala a su
 *  duración: la leyenda dice duración, silencio inicial y factor), ?mejilla=0 (sin mejilla), ?sombras=0 (sin sombras), ?entorno=1 (reflejos), ?guarda=0 (sin guarda de fluidez), ?fps=1 (mide cuadros por segundo reproduciendo
 *  una palabra en bucle y lo escribe en la leyenda). */
import { aVelocidad, cicloSonido, giroPara, lentoParaAudio, lineaPalabra, retrasoAudio } from '../../front/src/app/compartido/boca3d/animacion';
import { Sonador } from '../../front/src/app/compartido/boca3d/audio';
import { EscenaBoca, usarMaterialesBaratos } from '../../front/src/app/compartido/boca3d/escena';
import { AjustesPoses3d, CatalogoPoses, PoseSonido, conAjustes3d, poseDe, trocearIpa } from '../../front/src/app/compartido/boca3d/poses';
import catalogoJson from '../../front/src/app/compartido/boca3d/poses.ejemplo.json';
import ajustes3d from '../../front/src/app/compartido/boca3d/poses.ajustes3d.json';

const CATALOGO = conAjustes3d(catalogoJson as unknown as CatalogoPoses, ajustes3d as unknown as AjustesPoses3d);
const PALABRA_FPS = 'ˌɪntəˈnæʃənəl ˈpɑvɚti';

declare global {
  interface Window { escenaBoca: EscenaBoca; medirFps: (segundos?: number) => Promise<number>; palabraConAudio: (ipa: string) => Promise<void>; }
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
  const didactica = params.get('didactica') === '1';
  // El respaldo geométrico es útil en desarrollo, pero no es el piloto que
  // Miguel está evaluando. Ocultarlo hasta confirmar ambos assets de Blender.
  const necesitaCara = params.get('cara') !== '0';
  const necesitaLengua = params.get('lengua') !== '0';
  const estadoCarga = document.createElement('p');
  estadoCarga.className = 'estado-carga';
  estadoCarga.setAttribute('role', 'status');
  const mensajeCarga = document.createElement('span');
  mensajeCarga.textContent = 'Cargando el modelo detallado…';
  const reintentar = document.createElement('button');
  reintentar.type = 'button'; reintentar.textContent = 'Reintentar carga';
  reintentar.hidden = true;
  reintentar.addEventListener('click', () => location.reload());
  estadoCarga.append(mensajeCarga, document.createTextNode(' '), reintentar);
  if (didactica) {
    visor.before(estadoCarga);
    visor.dataset['cargaPiloto'] = 'pendiente';
    visor.setAttribute('aria-busy', 'true');
    // No depende del CSS de una página concreta y mantiene el tamaño del canvas.
    visor.style.visibility = 'hidden';
  }
  const esperaCarga = didactica ? window.setTimeout(() => {
    mensajeCarga.textContent = 'El modelo está tardando en cargar. Puedes esperar o reintentar.';
    reintentar.hidden = false;
  }, 20000) : undefined;
  const inventario = didactica && params.get('inventario') === '1';
  const elegirPose = (s: string) => s.startsWith('rp/') ? poseDe(CATALOGO, s.slice(3), 'rp') : poseDe(CATALOGO, s);
  const describir = (s: string, pose: PoseSonido) => (s ? `/${s.replace('rp/', '')}/${s.startsWith('rp/') ? ' · británico' : ''} · ` : 'reposo · ') + pose.leyenda;
  const velocidad = Number(params.get('velocidad')) || 1;
  let preparada!: () => void;
  const modelosListos = new Promise<void>(resolve => { preparada = resolve; });
  if (params.get('opt') === '0') usarMaterialesBaratos(false);
  const escena = new EscenaBoca(visor, {
    alPreparar: preparada,
    exploracionDidactica: didactica,
    reducirMovimiento: matchMedia('(prefers-reduced-motion: reduce)').matches,
    mejilla: params.get('mejilla') !== '0',
    sombras: params.get('sombras') !== '0',
    entorno: params.get('entorno') === '1' || (didactica && params.get('entorno') !== '0'),
    guarda: params.get('guarda') !== '0',
    // v5: ?opt=0 desactiva las optimizaciones (pixel ratio en movimiento y materiales baratos) para medirlas.
    menosPixelesEnMovimiento: params.get('opt') !== '0',
    // El modelado es el predeterminado en la demo, nunca en la app pública.
    lenguaGlb: params.get('lengua') !== '0' ? 'lengua.glb' : undefined,
    caraGlb: params.get('cara') !== '0' ? 'cara.glb' : undefined,
  });
  window.escenaBoca = escena;
  void modelosListos.then(() => {
    if (!didactica) return;
    window.clearTimeout(esperaCarga);
    const completa = (!necesitaCara || escena.tieneCaraModelada)
      && (!necesitaLengua || escena.tieneLenguaModelada);
    visor.dataset['cargaPiloto'] = completa ? 'lista' : 'error';
    visor.setAttribute('aria-busy', 'false');
    visor.style.visibility = completa ? 'visible' : 'hidden';
    mensajeCarga.textContent = completa
      ? 'Modelo detallado listo · exterior con textura'
      : 'No se pudo cargar el modelo detallado. Pulsa «Reintentar carga».';
    reintentar.hidden = completa;
  });
  if (didactica) {
    const vistas = document.createElement('div');
    vistas.className = 'chips';
    for (const [texto, frente] of [['Frente · labios', true], ['Lado · interior', false]] as const) {
      const b = document.createElement('button'); b.type = 'button'; b.textContent = texto;
      b.addEventListener('click', () => escena.vistaDidactica(frente)); vistas.appendChild(b);
    }
    const quieta = document.createElement('button'); quieta.type = 'button'; quieta.textContent = 'Mantener gesto';
    quieta.addEventListener('click', () => {
      const seleccionado = chips.querySelector('button.elegido') as HTMLButtonElement | null;
      const pose = elegirPose(seleccionado?.dataset['s'] ?? '');
      if (pose) { escena.irA(pose, 0); leyenda.textContent = describir(seleccionado?.dataset['s'] ?? '', pose); }
    });
    vistas.appendChild(quieta); visor.before(vistas);
    const repetir = document.createElement('button'); repetir.type = 'button'; repetir.textContent = 'Ver movimiento';
    repetir.addEventListener('click', () => {
      const seleccionado = chips.querySelector('button.elegido') as HTMLButtonElement | null;
      const pose = elegirPose(seleccionado?.dataset['s'] ?? '');
      if (pose) { escena.reproducir(aVelocidad(cicloSonido(pose, CATALOGO), velocidad)); leyenda.textContent = describir(seleccionado?.dataset['s'] ?? '', pose); }
    });
    vistas.appendChild(repetir);
    const final = document.createElement('button'); final.type = 'button'; final.className = 'final-diptongo';
    final.textContent = 'Gesto final'; final.hidden = true;
    final.addEventListener('click', () => {
      const s = (chips.querySelector('button.elegido') as HTMLButtonElement | null)?.dataset['s'] ?? '';
      const pose = elegirPose(s);
      if (pose?.hacia) { escena.irA(pose.hacia, 0); leyenda.textContent = `Final de /${s.replace('rp/','')}/ · ${pose.hacia.leyenda}`; }
    });
    vistas.appendChild(final);
    escena.vistaDidactica(params.get('vista') !== 'lado');
  }
  if (params.get('ciclo') === '0') ciclo.checked = false;

  const ir = (simbolo: string) => {
    const pose: PoseSonido | null = elegirPose(simbolo);
    if (!pose) return;
    if (ciclo.checked && simbolo) escena.reproducir(aVelocidad(cicloSonido(pose, CATALOGO), velocidad), { giro: didactica ? 0 : giroPara(pose) });
    else escena.irA(pose, (lento.checked ? 2.5 : 0.55) / velocidad);
    leyenda.textContent = describir(simbolo, pose);
    chips.querySelectorAll('button').forEach(b => b.classList.toggle('elegido', b.dataset['s'] === simbolo));
    const final = raiz.querySelector<HTMLButtonElement>('.final-diptongo');
    if (final) final.hidden = !(pose.movimiento === 'diptongo' && pose.hacia);
  };
  const sonidosVisibles = inventario ? [...Object.keys(CATALOGO.sonidos), ...Object.keys(CATALOGO.rp ?? {}).map(s => 'rp/'+s)]
    : didactica && params.get('piloto') === '1' ? ['p','b','m','f','v','i','u'] : Object.keys(CATALOGO.sonidos);
  for (const s of ['', ...sonidosVisibles]) {
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset['s'] = s;
    b.textContent = s ? `/${s.replace('rp/', '')}/` : 'reposo';
    b.addEventListener('click', () => ir(s));
    chips.appendChild(b);
  }
  if (inventario) {
    const grupoDe = (s: string) => s.startsWith('rp/') ? 'britanico'
      : elegirPose(s)?.movimiento === 'vocal' ? 'vocales'
      : elegirPose(s)?.movimiento === 'diptongo' ? 'diptongos' : 'consonantes';
    const label = document.createElement('label'); label.className = 'familia'; label.textContent = 'Explorar sonidos ';
    const selector = document.createElement('select'); selector.setAttribute('aria-label', 'Grupo de sonidos');
    for (const [value, texto] of [['vocales','Vocales'],['consonantes','Consonantes'],['diptongos','Diptongos'],['britanico','Variantes británicas']]) {
      const o = document.createElement('option'); o.value = value; o.textContent = texto; selector.append(o);
    }
    selector.value = grupoDe(params.get('s') ?? 'u');
    const filtrar = () => chips.querySelectorAll<HTMLButtonElement>('button').forEach(b => {
      b.hidden = !!b.dataset['s'] && grupoDe(b.dataset['s']) !== selector.value;
    });
    selector.addEventListener('change', () => { filtrar(); ir(sonidosVisibles.find(s => grupoDe(s) === selector.value) ?? ''); });
    filtrar(); label.append(selector); chips.before(label);
  }
  const palabra = (ipa: string, lento?: number) => {
    const { texto, segmentos } = trocearIpa(ipa, CATALOGO);
    if (!segmentos.length) { leyenda.textContent = `No reconozco ningún sonido en «${ipa}»`; return null; }
    const linea = aVelocidad(lineaPalabra(segmentos, CATALOGO, lento), velocidad);
    escena.reproducir(linea);
    leyenda.textContent = `/${texto}/ · ${segmentos.map(s => s.simbolo).join(' ')} · ${linea.total.toFixed(1)} s`;
    return linea;
  };
  // Con ?audio=..., la palabra suena y su línea se ajusta a la duración del audio (como en la app).
  const sonador = new Sonador();
  const audioUrl = params.get('audio');
  const palabraConAudio = async (ipa: string) => {
    if (!audioUrl) { palabra(ipa); return; }
    sonador.despertar();
    const listo = await sonador.preparar(audioUrl);
    if (!listo) { palabra(ipa); leyenda.textContent += ' · sin audio'; return; }
    const { segmentos } = trocearIpa(ipa, CATALOGO);
    const lento = lentoParaAudio(segmentos, CATALOGO, listo.duracion, listo.silencio);
    const linea = palabra(ipa, lento);
    if (!linea) return;
    const r = listo.tocar(retrasoAudio(linea.sonidoEn, listo.silencio, velocidad), velocidad);
    leyenda.textContent += ` · audio ${listo.duracion.toFixed(2)} s, silencio ${listo.silencio.toFixed(2)} s, lento ${lento.toFixed(2)}, velocidad ${velocidad} (audio a ${r.velocidad}×)`;
  };
  window.palabraConAudio = palabraConAudio;
  raiz.querySelector('.palabra')!.addEventListener('submit', e => { e.preventDefault(); void palabraConAudio(entradaIpa.value); });
  raiz.querySelector('.reset')!.addEventListener('click', () => escena.restablecerVista());
  const libre = raiz.querySelector('.libre') as HTMLInputElement;
  libre.addEventListener('change', () => escena.girarLibre(libre.checked));

  // Cuadros por segundo mientras se reproduce una palabra en bucle: mide el
  // coste de deformar la lengua y pintar, no el de esperar.
  window.medirFps = (segundos = 4) => modelosListos.then(() => new Promise<number>(resolve => {
    let cuadros = 0;
    const t0 = performance.now();
    let linea = palabra(PALABRA_FPS)!;
    const tic = () => {
      cuadros++;
      if (!escena.enTransicion) escena.reproducir(linea);
      if (performance.now() - t0 < segundos * 1000) requestAnimationFrame(tic);
      else {
        const fps = cuadros / ((performance.now() - t0) / 1000);
        const g = escena.estadoGuarda;
        const guarda = g.fps === null ? 'guarda sin medir' : `guarda: ${g.fps.toFixed(1)} fps al arrancar, `
          + ['todo encendido', 'sombras a 512', 'sombras apagadas', 'sombras y mejilla apagadas'][g.etapa];
        leyenda.textContent = `${fps.toFixed(1)} cuadros por segundo (${cuadros} en ${segundos} s) · ${guarda}`;
        resolve(fps);
      }
    };
    requestAnimationFrame(tic);
  }));

  ir(params.get('s') ?? '');
  const p = params.get('palabra');
  if (p) { entradaIpa.value = p; palabra(p); }
  // ?giro=0.9 abre la vista girada de entrada (para capturas sin tocar la pantalla).
  const giro = Number(params.get('giro'));
  if (giro) escena.vista(giro, Number(params.get('polar')) || 1.25);
  if (params.get('fps')) window.medirFps(Number(params.get('fps')) || 4);
}

arrancar();
