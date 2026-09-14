// Prueba la pantalla Angular compilada sin backend ni proveedores.
// PLAYWRIGHT_MODULE=/ruta/playwright-core/index.mjs node tools/probar_boca_integrada.mjs
// FRONT_BUILD y SALIDA_PRUEBAS pueden cambiar las carpetas. Servidor/Chrome propios.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, readdir, stat, mkdir, writeFile } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE
  ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright-core');
const raiz = resolve(process.env.FRONT_BUILD ?? 'front/dist/front/browser');
const salida = resolve(process.env.SALIDA_PRUEBAS ?? 'build/pruebas_boca_integrada');
const pausa = ms => new Promise(r => setTimeout(r, ms));

// Evita probar inadvertidamente un build anterior sin la integracion.
async function esperarBuild() {
  const hasta = Date.now() + 120_000;
  while (Date.now() < hasta) {
    try {
      await stat(resolve(raiz, 'index.html'));
      for (const nombre of ['lengua.glb', 'cara.glb']) {
        const b = await readFile(resolve(raiz, 'boca3d', nombre));
        assert.equal(b.toString('ascii', 0, 4), 'glTF', `${nombre} no es GLB`);
      }
      const js = (await readdir(raiz)).filter(n => n.endsWith('.js'));
      for (const nombre of js) {
        if ((await readFile(resolve(raiz, nombre), 'utf8')).includes('Boca en 3D')) return;
      }
    } catch { /* Espera al build de la sesion integradora. */ }
    await pausa(1000);
  }
  throw new Error(`No llego un build Angular integrado a ${raiz} en 120 s`);
}

// Formas de front/src/app/nucleo/api.ts y app/api.py:inventario_fonemas.
function inventario(acento) {
  const ficha = { rasgos: 'Sonido de prueba local', labios: 'Relajados', lengua: 'Entre los dientes',
    boca: 'Entreabierta', cuerdas: 'Sin vibracion', aire: 'Por la boca', trampa: '', ga: '', rp: '' };
  const fonemas = [
    { simbolo: '\u03b8', nombre: 'Fricativa dental sorda', ejemplos: ['think'], grupo: 'fricativa', tipo: 'consonante', audio: null, ficha },
    { simbolo: 'h', nombre: 'Fricativa glotal', ejemplos: ['house'], grupo: 'fricativa', tipo: 'consonante', audio: null, ficha },
    { simbolo: acento === 'rp' ? 'i\u02d0' : 'i', nombre: 'Vocal anterior alta', ejemplos: ['see'], grupo: 'vocal', tipo: 'vocal', audio: null, ficha },
  ];
  return { acento, acentos: { ga: 'General American', rp: 'Received Pronunciation' }, fonemas,
    grupos: ['fricativa', 'vocal'].map(clave => ({ clave, titulo: clave, sonidos: fonemas.filter(f => f.grupo === clave) })) };
}
const inicio = { perfil: null, seguir: null, libros: 0, cuaderno: { consultas: 0, palabras: 0, libros: 0 },
  entrada: { puerta: false, dentro: false, nombre: null, restantes: null, openai: false, mensaje: '' } };
const correccion = { puntuacion:75,transcripcion_ok:true,transcripcion:'The bed is here.',
  palabras:[{palabra:'bird',bien:false}],entendidas:[['bird','bed']],resumen:'Respuesta de prueba local.',
  detalles:[{palabra:'bird',ipa:'/b\u025c\u02d0d/',variante:'UK',
    fonema:{simbolo:'\u025d',nombre:'Vocal rotica',ejemplos:['bird'],audio:null,acento:'ga'},
    audio:null,sonido_que_falla:'Sonido de prueba.',como_colocar_la_boca:'Indicacion de prueba.'}],
  audio_correcto:null,restantes:null };
const svgRespaldo = '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="248" viewBox="0 0 240 248"><rect width="240" height="248" fill="#eef2f6"/><path d="M30 80 Q110 20 210 100 M30 160 Q110 210 210 100" fill="none" stroke="#804050" stroke-width="12"/></svg>';

async function pixeles(page, canvas) {
  return canvas.evaluate(origen => {
    const c = document.createElement('canvas'); c.width = origen.width; c.height = origen.height;
    const ctx = c.getContext('2d'); ctx.drawImage(origen, 0, 0);
    const d = ctx.getImageData(0, 0, c.width, c.height).data;
    const colores = new Set(); let distintos = 0, borde = 0;
    for (let i = 0; i < d.length; i += 4) {
      colores.add((d[i] << 16) | (d[i+1] << 8) | d[i+2]);
      const diferente = d[i+3]>10;
      if (diferente) distintos++;
      const p = i/4, x = p%c.width, y = Math.floor(p/c.width);
      if (diferente && (x<2 || y<2 || x>=c.width-2 || y>=c.height-2)) borde++;
    }
    return { colores: colores.size, fraccion: distintos/(d.length/4), borde, ancho: c.width, alto: c.height };
  });
}

async function comprobarLayout(page) {
  const problemas = await page.evaluate(() => {
    const errores = [];
    if (document.documentElement.scrollWidth > innerWidth + 1) errores.push('scroll horizontal');
    const host = document.querySelector('app-boca3d');
    if (!host) return errores;
    const canvas = host.querySelector('canvas');
    const rect = canvas?.getBoundingClientRect();
    if (rect && (rect.width < 160 || rect.height < 120)) errores.push('canvas demasiado pequeno');
    const botones = [...host.querySelectorAll('button')].filter(b => b.getClientRects().length);
    const interseccion = (a,b) => Math.min(a.right,b.right)-Math.max(a.left,b.left)>2 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2;
    for (let i=0;i<botones.length;i++) {
      const b = botones[i].getBoundingClientRect();
      if (botones[i].scrollWidth > botones[i].clientWidth+2) errores.push('texto de boton recortado');
      if (rect && interseccion(b,rect)) errores.push('boton sobre canvas');
      for (let j=i+1;j<botones.length;j++) if(interseccion(b,botones[j].getBoundingClientRect())) errores.push('botones solapados');
    }
    const leyenda = host.querySelector('.leyenda')?.getBoundingClientRect();
    if (leyenda && rect && interseccion(leyenda,rect)) errores.push('leyenda sobre canvas');
    return errores;
  });
  assert.deepEqual(problemas, []);
}

await esperarBuild();
await mkdir(salida, { recursive: true });
const servidor = createServer(async (req, res) => {
  const ruta = resolve(raiz, '.' + new URL(req.url, 'http://localhost').pathname.replace(/\/$/, '/index.html'));
  if (!ruta.startsWith(raiz+sep)) { res.writeHead(403).end(); return; }
  try {
    const nombre = extname(ruta) ? ruta : resolve(raiz, 'index.html');
    const cuerpo = await readFile(nombre);
    const tipos = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml' };
    res.writeHead(200, { 'Content-Type': tipos[extname(nombre)] ?? 'application/octet-stream' }); res.end(cuerpo);
  } catch { res.writeHead(404).end(); }
});
await new Promise(r => servidor.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${servidor.address().port}`;
let browser;
const resultados = [];
try {
  browser = await chromium.launch({ executablePath: process.env.CHROME ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader',
      '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });
  const casos = [
    { nombre: 'desktop', movil: false }, { nombre: 'movil', movil: true },
    { nombre: 'sin-webgl', movil: true, sinWebgl: true },
    { nombre: 'sin-glb', movil: true, sinGlb: true },
    { nombre: 'movimiento-reducido', movil: true, reducido: true },
    { nombre: 'correccion', movil: true, correccion: true },
  ].filter(c => !process.env.CASO || c.nombre === process.env.CASO);
  assert.ok(casos.length, 'CASO desconocido');
  for (const caso of casos) {
    const contexto = await browser.newContext({ viewport: { width: caso.movil ? 390 : 1280, height: caso.movil ? 844 : 900 },
      deviceScaleFactor: 1, isMobile: caso.movil, hasTouch: caso.movil, colorScheme: 'light',
      reducedMotion: caso.reducido ? 'reduce' : 'no-preference' });
    if (caso.correccion) await contexto.grantPermissions(['microphone'],{origin:base});
    await contexto.addInitScript(sinWebgl => {
      const original = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(tipo,...args) {
        if (String(tipo).includes('webgl')) {
          if (sinWebgl) return null;
          // Conserva pixeles para leer el canvas real sin CSS ni overlays.
          // Esta prueba no mide FPS ni rendimiento de produccion.
          return original.call(this,tipo,{...args[0],preserveDrawingBuffer:true});
        }
        return original.call(this,tipo,...args);
      };
    },!!caso.sinWebgl);
    const peticiones = [], glb = [], errores = [], inesperadas = [];
    await contexto.route('**/*', async route => {
      const req = route.request(), u = new URL(req.url());
      if (u.pathname.startsWith('/api/')) {
        peticiones.push({ metodo: req.method(), ruta: u.pathname, acento: u.searchParams.get('acento') });
        if (caso.correccion && u.pathname === '/api/voz' && req.method() === 'POST') {
          const cuerpo = req.postDataBuffer();
          if (!cuerpo || cuerpo.length<1000 || !cuerpo.includes(Buffer.from('name="acento"\r\n\r\nUK'))) {
            inesperadas.push('audio multipart sintetico o acento UK ausente');
            await route.fulfill({status:422,json:{detail:'Fixture multipart no valida'}}); return;
          }
          await route.fulfill({json:correccion}); return;
        }
        if (req.method() !== 'GET') { inesperadas.push('API de escritura: '+u.pathname); await route.abort(); return; }
        let json;
        if (u.pathname === '/api/salud') json = { estado: 'ok', api: 'fixture-local', cargado: { puntuador:false,catalogo:false,consultor:false } };
        else if (u.pathname === '/api/inicio') json = caso.correccion
          ? {...inicio,entrada:{...inicio.entrada,openai:true}} : inicio;
        else if (u.pathname === '/api/voz/debiles') json = { palabras: [] };
        else if (u.pathname === '/api/fonemas') json = inventario(u.searchParams.get('acento') ?? 'ga');
        else if (u.pathname.startsWith('/api/articulacion/')) { await route.fulfill({ contentType:'image/svg+xml',body:svgRespaldo }); return; }
        else { inesperadas.push(u.pathname); await route.fulfill({status:404,json:{detail:'Ruta no simulada'}}); return; }
        await route.fulfill({json}); return;
      }
      if (u.origin !== base) { await route.abort(); return; }
      if (u.pathname.endsWith('.glb')) {
        glb.push(u.pathname);
        if (caso.sinGlb) { await route.fulfill({status:404,body:''}); return; }
      }
      await route.continue();
    });
    const page = await contexto.newPage();
    page.on('pageerror', e => errores.push(e.message));
    await page.goto(base+'/#/pronunciar');
    if (caso.correccion) {
      await page.locator('details summary').filter({hasText:'Los sonidos'}).click();
      await page.getByRole('radio',{name:/Brit/}).click();
      await page.locator('textarea').fill('The bird is here.');
      // En movil la grabadora se oculta mientras el campo tiene foco.
      await page.getByText('Tu voz',{exact:true}).click();
      await page.getByRole('button',{name:'Empezar a grabar',exact:true}).click();
      await page.getByRole('button',{name:'Terminar la grabaci\u00f3n',exact:true}).waitFor();
      await page.waitForTimeout(1200);
      await page.getByRole('button',{name:'Terminar la grabaci\u00f3n',exact:true}).click();
      await page.getByRole('button',{name:'Corr\u00edgeme',exact:true}).click();
      const detalle = page.locator('details.boca');
      await detalle.locator('summary').click();
      await detalle.getByRole('button',{name:'Boca en 3D',exact:true}).click();
      const boca = detalle.locator('app-boca3d'), lienzo = boca.locator('.lienzo'), canvas = boca.locator('canvas');
      await page.waitForFunction(() => {
        const e = document.querySelector('details.boca app-boca3d .lienzo');
        return e?.dataset.lengua==='blender' && e?.dataset.cara==='blender';
      });
      assert.equal(await lienzo.getAttribute('data-acento-sonido'),'ga');
      assert.equal(await lienzo.getAttribute('data-acento-palabra'),'rp');
      assert.match(await lienzo.getAttribute('aria-label'),/\u025d/);
      await page.waitForTimeout(1500);
      const antes = await canvas.screenshot();
      await boca.getByRole('button',{name:/Palabra/}).click();
      await page.waitForTimeout(750);
      assert.equal(antes.equals(await canvas.screenshot()),false,'palabra UK no cambia pixeles');
      const px = await pixeles(page,canvas);
      assert.ok(px.colores>40 && px.fraccion>0.015);
      assert.equal(px.borde,0);
      await comprobarLayout(page);
      await page.screenshot({path:resolve(salida,'correccion.png'),fullPage:true});
      await boca.screenshot({path:resolve(salida,'correccion-boca.png')});
      await detalle.getByRole('button',{name:'Cerrar 3D',exact:true}).click();
      await boca.waitFor({state:'detached'});
      assert.equal(peticiones.filter(p=>p.metodo==='POST'&&p.ruta==='/api/voz').length,1);
      assert.deepEqual(inesperadas,[]); assert.deepEqual(errores,[]);
      resultados.push({caso:caso.nombre,peticiones,glb,pixeles:px,errores});
      await contexto.close(); console.log('OK',caso.nombre); continue;
    }
    await page.locator('details summary').filter({hasText:'Los sonidos'}).click();
    await page.locator('button.celda').filter({hasText:'\u03b8'}).click();
    assert.equal(await page.locator('app-boca3d').count(),0,'3D montado antes de pedirlo');
    assert.equal(glb.length,0,'GLB descargado antes de pedirlo');
    await page.getByRole('button',{name:'Boca en 3D',exact:true}).click();
    const boca = page.locator('app-boca3d');
    await boca.waitFor();
    if (caso.sinWebgl) {
      await boca.locator('img.respaldo').waitFor();
      assert.equal(await boca.locator('canvas').count(),0);
      assert.match(await boca.locator('img.respaldo').getAttribute('src'), /articulacion\/ga\/.*\.svg/);
      assert.equal(glb.length,0);
    } else {
      const canvas = boca.locator('canvas'); await canvas.waitFor();
      await page.waitForTimeout(1800);
      assert.ok(glb.includes('/boca3d/lengua.glb') && glb.includes('/boca3d/cara.glb'),JSON.stringify(glb));
      await page.waitForFunction(modelo => {
        const e = document.querySelector('app-boca3d .lienzo');
        return e?.dataset.lengua === modelo && e?.dataset.cara === modelo;
      }, caso.sinGlb ? 'geometrico' : 'blender');
      const px = await pixeles(page,canvas);
      assert.ok(px.colores>40 && px.fraccion>0.015,`canvas vacio: ${JSON.stringify(px)}`);
      assert.equal(px.borde,0,`modelo recortado: ${JSON.stringify(px)}`);
      if (!caso.sinGlb && !caso.reducido) {
        await page.waitForTimeout(1500);
        const antes = await canvas.screenshot();
        await boca.getByRole('button',{name:/movimiento|reproducir/i}).first().click();
        await page.waitForTimeout(650);
        const durante = await canvas.screenshot();
        assert.equal(antes.equals(durante),false,'reproducir no cambia pixeles');
        await page.waitForTimeout(2400);
      }
      if (caso.reducido) {
        await boca.getByRole('button',{name:/reproducir/i}).first().click();
        // Se permite saltar a la pose quieta; lo prohibido es interpolarla.
        await page.waitForTimeout(100);
        const antes = await canvas.screenshot();
        await page.waitForTimeout(650);
        assert.equal(antes.equals(await canvas.screenshot()),true,'reduced-motion sigue animando');
      }
      if (caso.nombre === 'movil') {
        await canvas.scrollIntoViewIfNeeded();
        assert.equal(await canvas.evaluate(c => getComputedStyle(c).touchAction),'pan-y');
        const antes = await canvas.screenshot(), b = await canvas.boundingBox();
        const cdp = await contexto.newCDPSession(page);
        const x = b.x + b.width*0.4, y = b.y+b.height*0.5;
        await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
        for (let i=1;i<=8;i++) await cdp.send('Input.dispatchTouchEvent',{
          type:'touchMove',touchPoints:[{x:x+i*9,y}] });
        await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
        await page.waitForTimeout(600);
        assert.equal(antes.equals(await canvas.screenshot()),false,'gesto tactil no gira');
        const girado = await pixeles(page,canvas);
        assert.equal(girado.borde,0,`modelo recortado tras giro tactil: ${JSON.stringify(girado)}`);
        await cdp.detach();
      }
      resultados.push({caso:caso.nombre,pixeles:px});
    }
    await comprobarLayout(page);
    await page.screenshot({path:resolve(salida,caso.nombre+'.png'),fullPage:true});
    await boca.screenshot({path:resolve(salida,caso.nombre+'-boca.png')});
    await page.getByRole('button',{name:'Cerrar la ficha',exact:true}).click();
    await page.locator('app-boca3d').waitFor({state:'detached'});
    assert.equal(await page.locator('app-boca3d').count(),0,'cerrar no desmonta');
    if (!caso.sinWebgl && !caso.sinGlb) {
      await page.getByRole('radio',{name:/Brit/}).click();
      await page.locator('button.celda').filter({hasText:'i\u02d0'}).click();
      await page.getByRole('button',{name:'Boca en 3D',exact:true}).click();
      await page.locator('app-boca3d canvas').waitFor();
      await page.waitForTimeout(1200);
      assert.ok(peticiones.some(p=>p.ruta==='/api/fonemas'&&p.acento==='rp'));
      assert.match(await page.locator('app-boca3d').innerText(),/i\u02d0|anterior/i);
      await comprobarLayout(page);
      await page.screenshot({path:resolve(salida,caso.nombre+'-rp.png'),fullPage:true});
    }
    assert.deepEqual(inesperadas,[],'peticiones API no simuladas');
    assert.deepEqual(errores,[],'errores JS');
    resultados.push({caso:caso.nombre,peticiones,glb,errores});
    await contexto.close();
    console.log('OK',caso.nombre);
  }
  await writeFile(resolve(salida,'resultados.json'),JSON.stringify(resultados,null,2));
  console.log(JSON.stringify({ok:true,escenarios:casos.length,salida}));
} catch (error) {
  let n = 0;
  for (const contexto of browser?.contexts() ?? []) for (const page of contexto.pages()) {
    await page.screenshot({path:resolve(salida,`fallo-${++n}.png`),fullPage:true}).catch(()=>{});
    await page.locator('app-boca3d canvas').screenshot({path:resolve(salida,`fallo-canvas-${n}.png`),timeout:1500}).catch(()=>{});
  }
  await writeFile(resolve(salida,'fallo.txt'),String(error.stack ?? error));
  throw error;
} finally {
  await browser?.close();
  await new Promise(r => servidor.close(r));
}
