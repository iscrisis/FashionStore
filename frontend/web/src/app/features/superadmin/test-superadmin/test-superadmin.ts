import { Component } from '@angular/core';

@Component({
  selector: 'app-test-superadmin',
  standalone: true,
  template: `
    <div style="padding: 20px; font-family: sans-serif;">
      <h1>SUPERADMIN TEST</h1>
      <p>La ruta /superadmin está funcionando correctamente.</p>
      <p style="color: green; margin-top: 20px;">✓ Este es un componente estático mínimo sin layout, sidebar, header, dashboard, servicios HTTP ni efectos.</p>
    </div>
  `,
})
export class TestSuperadminComponent {}
