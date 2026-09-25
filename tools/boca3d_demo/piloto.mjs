// Evidencia reproducible del piloto D4.4b: siete poses, mismo viewport y cámara.
// node tools/boca3d_demo/piloto.mjs <demo> <carpeta de capturas>
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import { pathToFileURL } from 'node:url';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright-core');
const raiz = resolve(process.argv[2]), salida = resolve(process.argv[3]);
await mkdir(salida,{recursive:true});
const servidor = createServer(async(req,res)=>{
  const p=resolve(raiz,'.'+new URL(req.url,'http://localhost').pathname.replace(/\/$/,'/index.html'));
  if(!p.startsWith(raiz+sep)) return res.writeHead(403).end();
  try { res.writeHead(200,{'Content-Type':({'.html':'text/html; charset=utf-8','.js':'text/javascript','.glb':'model/gltf-binary'})[extname(p)],'Cache-Control':'no-store'}).end(await readFile(p)); }
  catch {res.writeHead(404).end();}
});
await new Promise(r=>servidor.listen(0,'127.0.0.1',r));
const url=`http://127.0.0.1:${servidor.address().port}/`;
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const resultados=[];
try {
 const contexto=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true,colorScheme:'light'});
 const page=await contexto.newPage();
 const errores=[];page.on('pageerror',e=>errores.push(e.message));
 for(const [s,nombre] of [['p','p'],['θ','theta'],['k','k'],['b','b'],['m','m'],['t','t'],['ŋ','eng']]){
  await page.goto(url+`?ciclo=0&guarda=0&s=${encodeURIComponent(s)}`);
  await page.waitForFunction(()=>window.escenaBoca?.tieneCaraModelada&&window.escenaBoca?.tieneLenguaModelada&&!window.escenaBoca.enTransicion);
  await page.evaluate(s=>window.escenaBoca.vistaParaFamilia(({p:'bilabial',b:'bilabial',m:'nasal-bilabial','θ':'dental',t:'alveolar',k:'velar','ŋ':'velar'})[s]),s);
  await page.waitForTimeout(350);
  await page.screenshot({path:resolve(salida,nombre+'.png')});
  await page.locator('.visor').screenshot({path:resolve(salida,nombre+'_visor.png')});
  resultados.push(await page.evaluate(s=>{
   const e=window.escenaBoca;e.renderer.render(e.escena,e.camara);
   const c=document.createElement('canvas');c.width=e.canvas.width;c.height=e.canvas.height;
   const ctx=c.getContext('2d');ctx.drawImage(e.canvas,0,0);const d=ctx.getImageData(0,0,c.width,c.height).data;
   let borde=0;for(let i=0;i<d.length;i+=4){const p=i/4,x=p%c.width,y=Math.floor(p/c.width);if(d[i+3]>10&&(x<2||y<2||x>=c.width-2||y>=c.height-2))borde++;}
   return {s,borde,ancho:c.width,alto:c.height,morfos:e.pielesConLabios.map(m=>({claves:m.morphTargetDictionary,pesos:m.morphTargetInfluences})),desbordamiento:document.documentElement.scrollWidth>innerWidth};
  },s));
  if (['p','b','m'].includes(s)) {
   // Vista complementaria frontal: mismos GLB y misma escena, sin ocultar
   // defectos del encuadre guiado (que se captura arriba).
   await page.evaluate(()=>{const e=window.escenaBoca;e.girarLibre(true);e.controles.minAzimuthAngle=-Math.PI;e.controles.maxAzimuthAngle=Math.PI;e.vista(-1.45,Math.PI/2,0.70);});
   await page.waitForTimeout(200);
   await page.locator('.visor').screenshot({path:resolve(salida,nombre+'_frente.png')});
   await page.locator('.ciclo').check();
   await page.locator(`button[data-s="${s}"]`).click();
   await page.evaluate(()=>{window.__lineaPiloto=window.escenaBoca.linea;window.escenaBoca.detener();});
   const fases=[];
   for (const [fase,t] of [['reposo',0.42],['contacto',1.2],['liberacion',1.6],['final',2.25]]) {
    fases.push(await page.evaluate(({fase,t})=>{
     const e=window.escenaBoca;e.linea=window.__lineaPiloto;
     const n=e.poseDeLinea(t);e.detener();e.actual=n;e.aplicar(n);
     return {fase,t,pesos:e.pielesConLabios.map(m=>Object.fromEntries(Object.entries(m.morphTargetDictionary).map(([k,i])=>[k,m.morphTargetInfluences[i]])))};
    },{fase,t}));
    await page.waitForTimeout(100);
    await page.locator('.visor').screenshot({path:resolve(salida,`${nombre}_${fase}.png`)});
   }
   resultados.at(-1).fases=fases;
  }
 }
 await writeFile(resolve(salida,'medidas.json'),JSON.stringify({viewport:[390,844],resultados,errores},null,2));
 console.log(JSON.stringify({capturas:resultados.length,errores,salida}));
}finally{await browser.close();await new Promise(r=>servidor.close(r));}
