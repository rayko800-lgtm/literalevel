import { Routes } from '@angular/router';

/** Tres sitios en vez de ocho pestañas (PLAN_3_OCTUBRE.md §3.4): LEER,
 *  ENCONTRAR y TU NIVEL, más la pronunciación, que Laura quería a la vista.
 *  Colores y Estado salen de la navegación: son ajustes y diagnóstico. */
export const routes: Routes = [
  { path: '', title: 'Pléyade', loadComponent: () => import('./pantallas/inicio').then(m => m.Inicio) },
  { path: 'leer', title: 'Leer · Pléyade', loadComponent: () => import('./pantallas/leer-entrada').then(m => m.LeerEntrada) },
  { path: 'leer/:id/:cap', title: 'Leyendo · Pléyade', loadComponent: () => import('./pantallas/lector').then(m => m.Lector) },
  { path: 'libro/:id', title: 'Libro · Pléyade', loadComponent: () => import('./pantallas/libro').then(m => m.FichaLibro) },
  { path: 'encontrar', title: 'Encontrar · Pléyade', loadComponent: () => import('./pantallas/encontrar').then(m => m.Encontrar) },
  { path: 'nivel', title: 'Tu nivel · Pléyade', loadComponent: () => import('./pantallas/nivel').then(m => m.Nivel) },
  { path: 'pronunciar', title: 'Pronunciar · Pléyade', loadComponent: () => import('./pantallas/pronunciar').then(m => m.Pronunciar) },
  { path: 'palabras', title: 'Mis palabras · Pléyade', loadComponent: () => import('./pantallas/palabras').then(m => m.Palabras) },
  { path: 'repasar', title: 'Repasar · Pléyade', loadComponent: () => import('./pantallas/repasar').then(m => m.Repasar) },
  { path: 'estado', title: 'Estado · Pléyade', loadComponent: () => import('./pantallas/estado').then(m => m.Estado) },
  // Compatibilidad con los enlaces del esqueleto anterior.
  { path: 'buscar', redirectTo: 'encontrar' },
  { path: '**', redirectTo: '' },
];
