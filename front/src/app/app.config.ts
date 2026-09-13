import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter, withComponentInputBinding, withHashLocation, withInMemoryScrolling } from '@angular/router';
import { routes } from './app.routes';
import { interceptorLector } from './nucleo/lector';

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
    ),
  ],
};
