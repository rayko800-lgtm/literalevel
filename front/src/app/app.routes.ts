import { Routes } from '@angular/router';

/** Tres sitios en vez de ocho pestañas (PLAN_3_OCTUBRE.md §3.4): LEER,
 *  ENCONTRAR y TU NIVEL, más la pronunciación, que Laura quería a la vista.
 *  Colores y Estado salen de la navegación: son ajustes y diagnóstico. */
export const routes: Routes = [
  { path: '', title: 'LiteraLevel', loadComponent: () => import('./pantallas/inicio').then(m => m.Inicio) },
  { path: 'leer', title: 'Leer · LiteraLevel', loadComponent: () => import('./pantallas/leer-entrada').then(m => m.LeerEntrada) },
  { path: 'leer/:id/:cap', title: 'Leyendo · LiteraLevel', loadComponent: () => import('./pantallas/lector').then(m => m.Lector) },
  { path: 'libro/:id', title: 'Libro · LiteraLevel', loadComponent: () => import('./pantallas/libro').then(m => m.FichaLibro) },
  { path: 'encontrar', title: 'Encontrar · LiteraLevel', loadComponent: () => import('./pantallas/encontrar').then(m => m.Encontrar) },
  { path: 'nivel', title: 'Tu nivel · LiteraLevel', loadComponent: () => import('./pantallas/nivel').then(m => m.Nivel) },
  { path: 'pronunciar', title: 'Pronunciar · LiteraLevel', loadComponent: () => import('./pantallas/pronunciar').then(m => m.Pronunciar) },
  { path: 'palabras', title: 'Mis palabras · LiteraLevel', loadComponent: () => import('./pantallas/palabras').then(m => m.Palabras) },
  { path: 'repasar', title: 'Repasar · LiteraLevel', loadComponent: () => import('./pantallas/repasar').then(m => m.Repasar) },
  { path: 'estado', title: 'Estado · LiteraLevel', loadComponent: () => import('./pantallas/estado').then(m => m.Estado) },
  // Compatibilidad con los enlaces del esqueleto anterior.
  { path: 'buscar', redirectTo: 'encontrar' },
  { path: '**', redirectTo: '' },
];
