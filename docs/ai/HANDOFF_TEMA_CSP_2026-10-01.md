# Pléyade: restauración de la interfaz tras la auditoría

- Corrección publicada: `ce77e84`, Vercel `success`.
- Causa confirmada: el optimizador de CSS crítico de Angular emitía un script
  inline. La CSP `script-src 'self'` lo bloqueaba y la hoja completa permanecía
  con `media="print"`. Escuchar tenía fondo transparente y padding cero; los
  temas, botones y tarjetas globales no se aplicaban.
- Corrección: `optimization.styles.inlineCritical=false` en producción. Se
  conserva la minificación y el diseño original, sin modificar la CSP, el
  servidor, las cuentas ni los límites de gasto.
- `npm run build` comprueba ahora la carga directa del CSS, ausencia de scripts
  y manejadores inline y presencia de las reglas de temas y superficies. Build
  correcto; cuatro pruebas del interceptor de seguridad correctas.
- Producción móvil 390×844: Claro, Noche, Papel y Automático cambian los colores;
  Noche persiste al recargar. Automático coincide con el sistema claro del
  navegador de prueba. No se pudo emular un cambio del sistema a oscuro.
- Hoja servida y local idénticas, SHA256
  `A55C96316E37F8947EB1374B064B00ED1739934EEA448A95108FD205419D7D26`.
  Página con fondo translúcido, padding `23.808px 16px 48px`, tarjetas blancas
  en claro y azul noche en oscuro; ancho/scrollWidth 375/375. Se verificó DOM
  y estilos computados; capturas no disponibles en este navegador.
- API sigue sana: `estado=ok`, `api=0.3.0-seguridad`, `buscador_listo=true`.
- El cambio ajeno `cli.analytics=false` en `front/angular.json` sigue local y
  no entró en el commit. Los demás cambios ajenos se conservaron.
