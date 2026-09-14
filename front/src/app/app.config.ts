import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  NavigationError, provideRouter, withComponentInputBinding, withHashLocation, withInMemoryScrolling, withNavigationErrorHandler,
} from '@angular/router';
import { routes } from './app.routes';
import { interceptorLector } from './nucleo/lector';
import { recargarSiVersionVieja } from './nucleo/version';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideHttpClient(withInterceptors([interceptorLector])),
    provideRouter(
      routes,
      // Rutas con #: un Space estático no redirige /leer/PG11 a index.html, y
      // recargar esa página daría un 404.
      withHashLocation(),
      withComponentInputBinding(),
      // Cambiar de pantalla sube arriba. Laura: «doy a siguiente capítulo y me
      // deja ahí mismo abajo».
      withInMemoryScrolling({ scrollPositionRestoration: 'top', anchorScrolling: 'enabled' }),
      // Tras publicar, una pestaña con el build anterior pide chunks que ya no
      // existen: se recarga una vez en el destino (nucleo/version.ts).
      withNavigationErrorHandler((e: NavigationError) => { recargarSiVersionVieja(e.error, e.url); }),
    ),
  ],
};
