import { Component, input } from '@angular/core';

@Component({
  selector: 'app-status-badge',
  template: `
    @if (active()) {
      <span class="badge badge--active">Activa</span>
    } @else {
      <span class="badge badge--inactive">Inactiva</span>
    }
  `,
})
export class StatusBadge {
  readonly active = input.required<boolean>();
}
