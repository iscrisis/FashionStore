import { Component } from '@angular/core';

/**
 * Panel de inicio del administrador. Todavía no existen CU08 (productos),
 * CU06 (sucursales) ni CU09-datos-reales, así que solo se muestran estados
 * vacíos honestos — nunca estadísticas inventadas.
 */
@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard {
  protected readonly cards = [
    { title: 'Sucursales', message: 'Todavía no existen sucursales registradas.' },
    { title: 'Productos', message: 'Todavía no existen productos registrados.' },
    { title: 'Reservas', message: 'Todavía no existen reservas registradas.' },
    { title: 'Ventas', message: 'Todavía no existen ventas registradas.' },
  ];
}
