/** Demostración de la escena sin Angular ni router: la empaqueta
 *  `tools/boca3d_demo.mjs` con esbuild y se abre en el navegador para mirar y
 *  sacar capturas. No la importa nadie de la app. */
import { EscenaBoca } from './escena';
import { CATALOGO_PROTOTIPO, PoseSonido, poseDe } from './poses';

function arrancar(): void {
  const raiz = document.getElementById('boca3d-demo') ?? document.body;
  raiz.innerHTML = `
    <div class="chips"></div>
    <div class="visor"></div>
    <p class="leyenda"></p>
    <p class="pista">Arrastra para girar la boca. <button type="button" class="reset">Vista de lado</button>
      <label><input type="checkbox" class="lento" /> transición lenta</label></p>`;
  const chips = raiz.querySelector('.chips')!;
  const visor = raiz.querySelector('.visor') as HTMLElement;
  const leyenda = raiz.querySelector('.leyenda')!;
  const lento = raiz.querySelector('.lento') as HTMLInputElement;

  if (!EscenaBoca.hayWebGL()) {
    visor.textContent = 'No hay WebGL: aquí iría el corte 2D.';
    return;
  }
  const escena = new EscenaBoca(visor, {
    reducirMovimiento: matchMedia('(prefers-reduced-motion: reduce)').matches,
  });
  (window as unknown as { escenaBoca: EscenaBoca }).escenaBoca = escena;

  const ir = (simbolo: string) => {
    const pose: PoseSonido | null = poseDe(CATALOGO_PROTOTIPO, simbolo);
    if (!pose) return;
    escena.irA(pose, lento.checked ? 2.5 : 0.55);
    leyenda.textContent = (simbolo ? `/${simbolo}/ · ` : 'reposo · ') + pose.leyenda;
    chips.querySelectorAll('button').forEach(b => b.classList.toggle('elegido', b.dataset['s'] === simbolo));
  };
  for (const s of ['', ...Object.keys(CATALOGO_PROTOTIPO.sonidos)]) {
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset['s'] = s;
    b.textContent = s ? `/${s}/` : 'reposo';
    b.addEventListener('click', () => ir(s));
    chips.appendChild(b);
  }
  raiz.querySelector('.reset')!.addEventListener('click', () => escena.restablecerVista());
  const params = new URLSearchParams(location.search);
  ir(params.get('s') ?? '');
  // ?giro=0.9 abre la vista girada de entrada (para capturas sin tocar la pantalla).
  const giro = Number(params.get('giro'));
  if (giro) escena.vista(giro, Number(params.get('polar')) || 1.25);
}

arrancar();
