import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-superadmin-dashboard',
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
  standalone: true,
})
export class SuperadminDashboard {
  protected readonly statsCards = [
    { label: 'Empresas', icon: 'branches', value: '—' },
    { label: 'Empresas activas', icon: 'dashboard', value: '—' },
    { label: 'Administradores', icon: 'users', value: '—' },
  ];
}
