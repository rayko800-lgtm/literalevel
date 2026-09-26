// (Copia del 26 sep 2026 para la app Pléyade en Vercel; ver entrega/capturas/registro.txt.)
// Las 13 capturas del guion del video (entrega/guion_video.md, «Planos de
// pantalla que hacen falta»), a 390x844 con tacto y perfil 1,20, en el orden
// del guion, en entrega/capturas/NN_nombre.png. Sin 3D.
//
// Recorre el front de verdad (local con `ng serve` o el Space publicado) con
// un lector aislado (X-Lector nuevo en cada ejecucion), prepara el estado por
// la API (perfil, libro, curva, palabras) y hace las capturas en el navegador.
// Lo que cuesta dinero (explicacion en contexto, marca IA, correccion) entra
// con la cuenta que llega por variables de entorno; ninguna contrasena se
// escribe en pantalla ni en disco.
//
//   PLAYWRIGHT_MODULE=ruta/playwright-core/index.mjs BASE=http://127.0.0.1:4200 \
//   USUARIO=... CLAVE=... node tools/capturas_guion.mjs
//
// Variables: BASE (front), API (por defecto BASE; en el Space, la API vive en
// otro origen), USUARIO/CLAVE (cuenta con cupo), SALIDA (entrega/capturas),
// AUDIO_WAV (si ya existe; si no, lo genera tools/capturas_guion_audio.py),
// CHROME, PYTHON, SOLO=NN para repetir una captura.
import { execFileSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE ?? 'playwright-core').href);
const BASE = (process.env.BASE ?? 'http://127.0.0.1:4200').replace(/\/$/, '');
const API = (process.env.API ?? BASE).replace(/\/$/, '');
const SALIDA = resolve(process.env.SALIDA ?? 'entrega/capturas');
// La cuenta: por USUARIO/CLAVE, o leída de un archivo local que no está en el
// repositorio (CUENTA_ARCHIVO: una cuenta por línea, «usuario contraseña …»),
// para que la contraseña no pase por la línea de órdenes ni por ningún registro.
let USUARIO = process.env.USUARIO ?? '', CLAVE = process.env.CLAVE ?? '';
if (process.env.CUENTA_ARCHIVO) {
  const quiero = USUARIO || 'miguel';
  const linea = readFileSync(resolve(process.env.CUENTA_ARCHIVO), 'utf8').split(/\r?\n/)
    .map(l => l.trim().split(/\s+/)).find(c => c[0] === quiero);
  if (!linea || !linea[1]) throw new Error(`la cuenta «${quiero}» no está en ${process.env.CUENTA_ARCHIVO}`);
  USUARIO = linea[0]; CLAVE = linea[1];
}
const CHROME = process.env.CHROME ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PYTHON = process.env.PYTHON ?? 'python';
const SOLO = process.env.SOLO ? new Set(process.env.SOLO.split(',')) : null;
const LIBRO_TITULO = /crime and punishment/i;
const PALABRA = 'poverty';
const FRASE_LIBRO = /terrible poverty/i;
const CANDIDATAS_IA = ['Marmeladov', 'Raskolnikov', 'Svidrigailov', 'Razumihin', 'Zametov', 'Lizaveta', 'Dounia', 'Porfiry'];

mkdirSync(SALIDA, { recursive: true });
const lector = randomUUID();
const pausa = ms => new Promise(r => setTimeout(r, ms));
const registro = [];
const log = (...a) => { console.log(...a); registro.push(a.join(' ')); };

async function api(metodo, ruta, cuerpo) {
  const r = await fetch(API + ruta, {
    method: metodo, headers: { 'X-Lector': lector, 'Content-Type': 'application/json' },
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  });
  const texto = await r.text();
  let json; try { json = JSON.parse(texto); } catch { json = texto; }
  if (!r.ok) throw new Error(`${metodo} ${ruta} -> ${r.status}: ${typeof json === 'string' ? json.slice(0, 200) : JSON.stringify(json).slice(0, 300)}`);
  return json;
}

// --- Estado por la API: cuenta, perfil 1,20, el libro y su curva --------------

// La cuenta entra ANTES de preparar el estado (lo de pago la necesita) y se
// sale antes de la captura de «Ajustes → Tu perfil», que enseña el formulario.
async function entrar() {
  if (!USUARIO) return;
  const e = await api('POST', '/api/entrar', { usuario: USUARIO, clave: CLAVE });
  log('entrada:', e.dentro ? `dentro como ${e.nombre}` : `NO dentro (${e.mensaje ?? ''})`);
}
await entrar();
// 0,35 x media de las seis preguntas + 0,65 x el mejor fragmento; sin fragmentos,
// la media: (1,2 + 1,4 + 1,4 + 1,4 + 0,8 + 1,0) / 6 = 1,20.
const perfil = await api('POST', '/api/perfil/cuestionario', { nombre: '', guardar: true, respuestas: {
  frecuencia: 1.2, lecturas: [1.4], diccionario: 1.4, series: 1.4, libro_completo: 0.8, comprension: 1.0 } });
log('perfil:', JSON.stringify(perfil.perfil ?? perfil).slice(0, 120));

const busqueda = await api('POST', '/api/buscar', { consulta: 'dostoyevski', nivel: 1.2 });
const libro = (busqueda.resultados ?? []).find(b => LIBRO_TITULO.test(b.titulo ?? ''));
if (!libro) throw new Error('la búsqueda «dostoyevski» no devuelve Crime and Punishment: ' + JSON.stringify(busqueda).slice(0, 300));
const LIBRO = libro.id;
log('libro:', LIBRO, libro.titulo);
const ficha = await api('GET', `/api/libros/${LIBRO}`);
const total = ficha.total ?? ficha.capitulos?.length ?? 0;
log('capítulos:', total, 'palabras:', ficha.ficha?.palabras ?? ficha.palabras ?? '?');

// El capítulo de «terrible poverty» y una frase para leer en voz alta.
let CAP = -1, texto = '';
for (let n = 0; n < total && CAP < 0; n++) {
  const c = await api('GET', `/api/libros/${LIBRO}/capitulos/${n}`);
  const t = (c.parrafos ?? []).join('\n');
  if (FRASE_LIBRO.test(t)) { CAP = n; texto = t; }
}
if (CAP < 0) throw new Error('ningún capítulo trae «terrible poverty»');
log('capítulo de poverty:', CAP);
await api('PUT', `/api/libros/${LIBRO}/progreso`, { capitulo: CAP });

// La curva completa, medida antes de abrir la ficha (en local son minutos).
const curva = await api('POST', `/api/libros/${LIBRO}/curva`, { modo: 'completo' });
log('curva:', JSON.stringify(curva).slice(0, 160));
const trabajo = curva.trabajo_id ?? curva.trabajo ?? curva.id;
if (trabajo) {
  for (let i = 0; i < 240; i++) {
    const t = await api('GET', `/api/trabajos/${trabajo}`);
    if (t.terminado || ['hecho', 'listo', 'terminado', 'error'].includes(t.estado)) { log('trabajo:', JSON.stringify(t).slice(0, 160)); break; }
    await pausa(3000);
  }
}

// La palabra que el diccionario no trae (marca IA): primero los nombres de la
// novela, después cualquier palabra con mayúscula del capítulo (cada intento
// es una consulta de pago; se paran en la primera que la IA define).
let PALABRA_IA = '';
const propias = [...new Set((texto.match(/\b[A-Z][a-z]{5,}\b/g) ?? []))].filter(p => !/^(The|This|There|When|After|Before|Which|While|Though|Their|These|Those|Where|Every|About|Since|Because)$/.test(p));
for (const p of [...CANDIDATAS_IA, ...propias].slice(0, 16)) {
  if (!new RegExp(`\\b${p}\\b`).test(texto)) continue;
  const r = await api('POST', '/api/palabra', { palabra: p, libro_id: LIBRO, capitulo: CAP, etapa: 'completa',
    oracion: (texto.match(new RegExp(`[^.]*\\b${p}\\b[^.]*\\.`)) ?? [p])[0].slice(0, 500) }).catch(() => ({}));
  if (r.generado_por_ia) { PALABRA_IA = p; break; }
}
log('palabra IA:', PALABRA_IA || '(ninguna: el diccionario las trae todas)');

// La frase para Pronunciar: una del capítulo que traiga una palabra con un
// cambio de sonido preparado (misma lista que tools/capturas_guion_audio.py),
// para que la corrección tenga un sonido que señalar.
// Solo cambios que whisper no «corrige» solo: una palabra por otra real.
const CAMBIABLES = /\b(poverty|world|bird|doctor|father|mother|house|work|walk|light|lock|three|think|thought|ship|sheep|paper|money|water|strain|year|great|times|life|rest|early|later|heart|hard|long)\b/gi;
// Whisper corrige una palabra suelta por el contexto: mejor una frase con dos.
let FRASE = '', mejor = 0;
for (let i = 0; i < 16 && mejor < 2; i++) {
  const r = await api('GET', `/api/libros/${LIBRO}/capitulos/${CAP}/frase`);
  const f = r.frase ?? r.texto ?? '';
  const n = (f.match(CAMBIABLES) ?? []).length;
  if (n > mejor || !FRASE) { FRASE = f; mejor = n; }
}
// El WAV va a build/ (sin versionar), no junto a las capturas.
mkdirSync(resolve('build'), { recursive: true });
let AUDIO = process.env.AUDIO_WAV ? resolve(process.env.AUDIO_WAV) : resolve('build/capturas_frase_dicha.wav');
if (!process.env.AUDIO_WAV) {
  const dicha = execFileSync(PYTHON, ['-X', 'utf8', resolve('tools/capturas_guion_audio.py'), FRASE, AUDIO], { encoding: 'utf8' }).trim();
  log('frase:', FRASE, '| dicha:', dicha);
}
// Cuánto dura el WAV (PCM 16 bits): la grabación tiene que cubrirlo entero.
const cabecera = readFileSync(AUDIO);
const canales = cabecera.readUInt16LE(22), tasa = cabecera.readUInt32LE(24), bits = cabecera.readUInt16LE(34);
const SEGUNDOS_AUDIO = Math.ceil((cabecera.length - 44) / (tasa * canales * (bits / 8))) + 1;
log('audio:', `${SEGUNDOS_AUDIO - 1} s`);

// Cinco palabras en el cuaderno para «Repasa cinco» (etapa completa: es la que anota).
const oraciones = texto.split(/(?<=[.!?])\s+/).filter(o => o.split(' ').length > 6);
const palabrasCuaderno = [];
for (const o of oraciones) {
  const w = o.split(/\s+/).map(x => x.replace(/[^A-Za-z']/g, '')).filter(x => x.length > 6 && /^[a-z]+$/.test(x));
  for (const x of w) if (!palabrasCuaderno.includes(x)) palabrasCuaderno.push(x);
  if (palabrasCuaderno.length >= 4) break;
}
for (const w of palabrasCuaderno.slice(0, 4)) {
  await api('POST', '/api/palabra', { palabra: w, libro_id: LIBRO, capitulo: CAP, etapa: 'completa',
    oracion: (texto.match(new RegExp(`[^.]*\\b${w}\\b[^.]*\\.`)) ?? [w])[0].slice(0, 500) }).catch(e => log('cuaderno:', w, String(e).slice(0, 80)));
}

// --- El navegador ---------------------------------------------------------------

const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: [
  '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', `--use-file-for-fake-audio-capture=${AUDIO}`,
  '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
] });
const fallos = [];
let numero = 0;
async function paso(nombre, fn) {
  numero++;
  const archivo = `${String(numero).padStart(2, '0')}_${nombre}.png`;
  if (SOLO && !SOLO.has(String(numero).padStart(2, '0'))) return;
  try {
    await fn(resolve(SALIDA, archivo));
    log('OK', archivo);
  } catch (e) {
    fallos.push(archivo + ': ' + String(e.message ?? e).split('\n')[0]);
    log('FALLO', archivo, String(e.message ?? e).split('\n')[0]);
    for (const c of browser.contexts()) for (const p of c.pages()) {
      await p.screenshot({ path: resolve(SALIDA, 'fallo_' + archivo), fullPage: true }).catch(() => {});
      // Que un fallo no deje un panel abierto tapando las capturas siguientes.
      await p.keyboard.press('Escape').catch(() => {});
      for (const sel of ['button[aria-label="Cerrar ajustes"]', '.panel-palabra button[aria-label="Cerrar"]']) {
        const b = p.locator(sel);
        if (await b.count() && await b.first().isVisible().catch(() => false)) await b.first().click({ timeout: 3000 }).catch(() => {});
      }
    }
  }
}

const contexto = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2,
  isMobile: true, hasTouch: true, colorScheme: 'light', locale: 'es-MX' });
await contexto.grantPermissions(['microphone'], { origin: BASE });
await contexto.addInitScript(id => { try {
  localStorage.setItem('literalevel.lector', id);
  // Las ayudas de la primera vez, ya vistas: en el guion se cierran antes de grabar.
  for (const k of ['bienvenida', 'bienvenida-cuenta', 'pista-palabra', 'pista-paginas', 'ayuda-pronunciar'])
    localStorage.setItem('literalevel.' + k, 'vista');
} catch { /* sin almacenamiento */ } }, lector);
const page = await contexto.newPage();
const ir = async ruta => { await page.goto(`${BASE}/#${ruta}`, { waitUntil: 'networkidle' }); await pausa(600); };
const foto = (archivo, opciones = {}) => page.screenshot({ path: archivo, ...opciones });
const ver = async (loc, margen = 0) => { await loc.scrollIntoViewIfNeeded(); if (margen) await page.mouse.wheel(0, -margen); await pausa(400); };

try {
  await paso('inicio', async archivo => {
    await ir('/');
    await page.locator('.marca').waitFor();
    await foto(archivo);
  });

  await paso('ajustes_entrar', async archivo => {
    // Fuera de la cuenta para que se vea el formulario; se vuelve a entrar después.
    if (USUARIO) { await api('POST', '/api/salir').catch(() => {}); await page.reload({ waitUntil: 'networkidle' }); await pausa(600); }
    await page.locator('button[aria-label^="Ajustes"]').click();
    const panel = page.locator('aside.panel');
    await panel.waitFor();
    try {
      const usuario = panel.locator('input[name="usuario"]');
      await usuario.waitFor({ timeout: 10000 });
      await usuario.fill('miguel');                       // solo el usuario; la contraseña, vacía
      await ver(panel.getByRole('button', { name: 'Entrar' }));
      await foto(archivo);
    } finally {
      await page.locator('button[aria-label="Cerrar ajustes"]').click().catch(() => {});
    }
    await entrar();
    await page.reload({ waitUntil: 'networkidle' });
  });

  await paso('nivel', async archivo => {
    await ir('/nivel');
    await page.getByText('Ver el detalle').first().click();
    await page.getByText('1,20').first().waitFor({ timeout: 20000 });
    await page.getByText('Ver el detalle').first().evaluate(e => e.scrollIntoView({ block: 'start' }));
    await page.mouse.wheel(0, -120); await pausa(400);
    await foto(archivo);
  });

  await paso('nivel_afinar', async archivo => {
    const afinar = page.getByText(/Afínalo con un libro/).first();
    await ver(afinar, 120);
    await foto(archivo);
  });

  await paso('encontrar', async archivo => {
    await ir('/encontrar?q=' + encodeURIComponent('Crimen y castigo de Dostoyevski'));
    const tarjeta = page.getByText(LIBRO_TITULO).first();
    await tarjeta.waitFor({ timeout: 60000 });
    // La tarjeta del libro entera, con el nivel al lado, y el buscador encima si cabe.
    await tarjeta.evaluate(e => e.closest('article, li, .tarjeta')?.scrollIntoView({ block: 'center' }) ?? e.scrollIntoView({ block: 'center' }));
    await pausa(400);
    await foto(archivo);
  });

  await paso('ficha', async archivo => {
    await ir(`/libro/${LIBRO}`);
    await page.locator('app-curva svg').waitFor({ timeout: 120000 });
    // La ficha entera: las 203.415 palabras van arriba y la curva abajo, y en
    // una pantalla de móvil no caben juntas. Es la única captura de página completa.
    await pausa(600);
    await foto(archivo, { fullPage: true });
  });

  const seleccionar = async palabra => {
    await page.evaluate(w => {
      const raiz = document.querySelector('.texto');
      const iter = document.createNodeIterator(raiz, NodeFilter.SHOW_TEXT);
      let nodo;
      while ((nodo = iter.nextNode())) {
        const i = nodo.textContent.search(new RegExp(`\\b${w}\\b`));
        if (i < 0) continue;
        const r = document.createRange();
        r.setStart(nodo, i); r.setEnd(nodo, i + w.length);
        const s = getSelection(); s.removeAllRanges(); s.addRange(r);
        nodo.parentElement.scrollIntoView({ block: 'center' });
        document.dispatchEvent(new Event('selectionchange'));
        return;
      }
      throw new Error(`«${w}» no está en el texto del capítulo`);
    }, palabra);
  };

  const cerrarPalabra = async () => {
    const b = page.locator('.panel-palabra button[aria-label="Cerrar"]').first();
    if (await b.isVisible().catch(() => false)) await b.click({ timeout: 5000 }).catch(() => {});
    else await page.keyboard.press('Escape');
    await page.locator('.panel-palabra').waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
    await page.evaluate(() => getSelection()?.removeAllRanges());
  };

  await paso('palabra_poverty', async archivo => {
    await ir(`/leer/${LIBRO}/${CAP}`);
    await page.locator('.texto').waitFor();
    await pausa(1500);
    await seleccionar(PALABRA);
    const panel = page.locator('.panel-palabra');
    await panel.waitFor({ timeout: 20000 });
    await panel.getByText('Aquí significa').waitFor({ timeout: 90000 });
    await panel.locator('.bloque.aqui p').waitFor({ timeout: 90000 });
    await pausa(800);
    await foto(archivo);
    await cerrarPalabra();
  });

  await paso('palabra_ia', async archivo => {
    if (!PALABRA_IA) throw new Error('ninguna palabra del capítulo la define la IA: no hay marca que enseñar');
    await seleccionar(PALABRA_IA);
    const panel = page.locator('.panel-palabra');
    await panel.waitFor({ timeout: 20000 });
    await panel.locator('.chip.ia').first().waitFor({ timeout: 90000 });
    await pausa(800);
    await foto(archivo);
    await cerrarPalabra();
  });

  await paso('pronunciar', async archivo => {
    await ir('/pronunciar');
    const frase = page.locator('textarea#frase');
    const traer = page.getByRole('button', { name: /Una frase de mi libro/ });
    if (await traer.count()) { await traer.click(); await pausa(1500); }
    if ((await frase.inputValue()).trim() !== FRASE.trim()) await frase.fill(FRASE);
    await page.getByText('Tu voz', { exact: true }).click();
    await page.getByRole('button', { name: 'Empezar a grabar', exact: true }).click();
    await page.getByRole('button', { name: 'Terminar la grabación', exact: true }).waitFor();
    await pausa(SEGUNDOS_AUDIO * 1000);
    await page.getByRole('button', { name: 'Terminar la grabación', exact: true }).click();
    await page.getByRole('button', { name: 'Corrígeme', exact: true }).waitFor();
    await pausa(500);
    await foto(archivo);
  });

  await paso('correccion', async archivo => {
    await page.getByRole('button', { name: 'Corrígeme', exact: true }).click();
    const detalle = page.locator('.fonema').first();
    await detalle.waitFor({ timeout: 120000 });
    // La palabra fallada con su sonido, el audio y «Cómo colocar la boca», enteros.
    await detalle.evaluate(e => e.closest('li, article, .detalle, .tarjeta')?.scrollIntoView({ block: 'center' }) ?? e.scrollIntoView({ block: 'center' }));
    await pausa(400);
    await foto(archivo);
  });

  await paso('boca_2d', async archivo => {
    const boca = page.locator('details.boca').first();
    if (!(await boca.evaluate(d => d.open))) await boca.locator('summary').click();
    await boca.locator('img').first().waitFor();
    // Solo las imágenes del primer detalle: las de los demás son perezosas y siguen cerradas.
    await page.waitForFunction(() => {
      const imgs = [...document.querySelector('details.boca').querySelectorAll('img')];
      return imgs.length > 0 && imgs.every(i => i.complete && i.naturalWidth > 0);
    }, null, { timeout: 30000 });
    await ver(boca, 40);
    await foto(archivo);
  });


  await paso('boca_3d', async archivo => {
    const b = page.getByRole('button', { name: 'Boca en 3D' }).first();
    await b.scrollIntoViewIfNeeded(); await b.click();
    await page.locator('app-boca3d canvas').first().waitFor({ timeout: 60000 });
    await pausa(6000);
    await page.locator('app-boca3d').first().evaluate(e => e.scrollIntoView({ block: 'center' }));
    await pausa(800);
    await foto(archivo);
  });

  await paso('lector_en_vivo', async archivo => {
    await ir(`/leer/${LIBRO}/${Math.min(1, total - 1)}`);
    await page.locator('.texto').waitFor();
    await page.getByText('Leer en voz alta (en vivo)').first().waitFor({ timeout: 20000 });
    await pausa(800);
    await foto(archivo);
  });

  await paso('mis_palabras', async archivo => {
    await ir('/palabras');
    const repaso = page.getByText('Repasa cinco');
    await repaso.waitFor({ timeout: 20000 });
    // El título «Repasa cinco» arriba y, debajo, las palabras a repasar.
    await repaso.evaluate(e => e.scrollIntoView({ block: 'start' }));
    await page.mouse.wheel(0, -70);
    await pausa(400);
    await foto(archivo);
  });


  await paso('repasar', async archivo => {
    await ir('/repasar');
    await page.getByRole('button', { name: /Mostrar respuesta/ }).first().waitFor({ timeout: 20000 });
    await pausa(500);
    await foto(archivo);
  });

  await paso('mi_espacio', async archivo => {
    await ir('/');
    const prog = page.getByText('Mi progreso').first();
    await prog.waitFor({ timeout: 20000 });
    await pausa(1500);
    await foto(archivo, { fullPage: true });
  });

  await paso('sobre_pleyade', async archivo => {
    await page.locator('button.marca').click();
    await page.getByRole('dialog').waitFor();
    await pausa(800);
    await foto(archivo);
    await page.keyboard.press('Escape').catch(() => {});
    const c = page.getByRole('button', { name: 'Cerrar' }).first();
    if (await c.isVisible().catch(() => false)) await c.click();
  });

  for (const [nombre, ruta, espera] of [
    ['escritorio_encontrar', '/encontrar?q=' + encodeURIComponent('Crimen y castigo de Dostoyevski'), LIBRO_TITULO],
    ['escritorio_ficha', `/libro/${LIBRO}`, null],
    ['escritorio_pronunciar', '/pronunciar', null],
  ]) {
    await paso(nombre, async archivo => {
      const ctx = await browser.newContext({ viewport: { width: 1366, height: 800 }, deviceScaleFactor: 1, colorScheme: 'light', locale: 'es-MX' });
      await ctx.addInitScript(id => { try {
        localStorage.setItem('literalevel.lector', id);
        for (const k of ['bienvenida', 'bienvenida-cuenta', 'pista-palabra', 'pista-paginas', 'ayuda-pronunciar'])
          localStorage.setItem('literalevel.' + k, 'vista');
      } catch { /* */ } }, lector);
      const p = await ctx.newPage();
      await p.goto(`${BASE}/#${ruta}`, { waitUntil: 'networkidle' });
      if (espera) await p.getByText(espera).first().waitFor({ timeout: 60000 });
      if (ruta.startsWith('/libro')) await p.locator('app-curva svg').waitFor({ timeout: 120000 });
      await pausa(1200);
      await p.screenshot({ path: archivo });
      await ctx.close();
    });
  }

  await paso('cierre', async archivo => {
    // «Donde lo dejaste» enseña el arranque del capítulo actual: que sea el
    // primero de verdad y no el prefacio (que empieza por la licencia de Gutenberg).
    await api('PUT', `/api/libros/${LIBRO}/progreso`, { capitulo: Math.min(1, total - 1) }).catch(() => {});
    const escritorio = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1, colorScheme: 'light' });
    await escritorio.addInitScript(id => { try {
      localStorage.setItem('literalevel.lector', id);
      for (const k of ['bienvenida', 'bienvenida-cuenta']) localStorage.setItem('literalevel.' + k, 'vista');
    } catch { /* */ } }, lector);
    const p = await escritorio.newPage();
    await p.goto(`${BASE}/#/`, { waitUntil: 'networkidle' });
    await pausa(800);
    await p.screenshot({ path: archivo });
    await escritorio.close();
  });

  await paso('nivel_c2', async archivo => {
    await ir('/nivel');
    const otra = page.getByText(/volver a medirme/i).first();
    if (await otra.count()) { await otra.scrollIntoViewIfNeeded(); await otra.click(); await pausa(800); }
    const respuestas = ['Casi todos los días', 'Lo entiendo con naturalidad, sin necesidad de releer',
      'Sí, una obra clásica o especializada', 'Lo entiendo con naturalidad, sin necesidad de releer',
      'También los detalles y las relaciones entre ideas', 'Lo entiendo con naturalidad, sin necesidad de releer'];
    for (const r of respuestas) {
      const o = page.getByText(r, { exact: true }).first();
      await o.waitFor({ timeout: 20000 }); await o.scrollIntoViewIfNeeded(); await o.click(); await pausa(900);
      const sig = page.getByRole('button', { name: /^Siguiente|^Ver mi nivel|^Terminar/ }).first();
      if (await sig.isVisible().catch(() => false) && await sig.isEnabled().catch(() => false)) { await sig.click(); await pausa(900); }
    }
    await page.getByText(/Lees en inglés a nivel/).first().waitFor({ timeout: 30000 });
    await page.getByText('Ver el detalle').first().click().catch(() => {});
    await pausa(800);
    await foto(archivo);
  });
} finally {
  await browser.close();
  writeFileSync(resolve(SALIDA, 'registro.txt'), registro.join('\n') + '\n');
}
if (fallos.length) { console.error('FALLOS:\n' + fallos.join('\n')); process.exitCode = 1; }
else console.log(numero + ' capturas en', SALIDA);
