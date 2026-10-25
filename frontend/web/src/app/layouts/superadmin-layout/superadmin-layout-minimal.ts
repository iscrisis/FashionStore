import { Component } from '@angular/core';

@Component({
  selector: 'app-superadmin-layout-minimal',
  standalone: true,
  template: `
    <div class="superadmin-layout">
      <header class="superadmin-header">
        <div class="header-content">
          <h1>FASHION STORE</h1>
          <p>SUPERADMIN</p>
        </div>
      </header>

      <div class="superadmin-container">
        <aside class="superadmin-sidebar">
          <nav class="sidebar-nav">
            <div class="nav-item">Dashboard</div>
            <div class="nav-item">Empresas</div>
            <div class="nav-item">Planes SaaS</div>
            <div class="nav-item">Suscripciones</div>
            <div class="nav-item">Usuarios</div>
            <div class="nav-item">Configuración</div>
          </nav>
        </aside>

        <main class="superadmin-main">
          <div class="content-header">
            <h2>Panel de administración de la plataforma.</h2>
          </div>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .superadmin-layout {
      display: flex;
      flex-direction: column;
      height: 100vh;
    }

    .superadmin-header {
      background: #333;
      color: white;
      padding: 20px;
      border-bottom: 1px solid #ddd;
    }

    .header-content h1 {
      margin: 0;
      font-size: 20px;
    }

    .header-content p {
      margin: 5px 0 0 0;
      font-size: 14px;
      color: #aaa;
    }

    .superadmin-container {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    .superadmin-sidebar {
      width: 250px;
      background: #f5f5f5;
      border-right: 1px solid #ddd;
      padding: 20px;
      overflow-y: auto;
    }

    .sidebar-nav {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .nav-item {
      padding: 10px;
      cursor: pointer;
      border-radius: 4px;
      transition: background 0.2s;
    }

    .nav-item:hover {
      background: #e0e0e0;
    }

    .superadmin-main {
      flex: 1;
      padding: 30px;
      overflow-y: auto;
    }

    .content-header {
      margin-bottom: 30px;
    }

    .content-header h2 {
      margin: 0;
      font-size: 18px;
      color: #333;
    }
  `],
})
export class SuperadminLayoutMinimal {}
