import { Component, input } from '@angular/core';

export type IconName =
  | 'dashboard'
  | 'catalog'
  | 'products'
  | 'seasons'
  | 'branches'
  | 'inventory'
  | 'reservations'
  | 'suppliers'
  | 'sales'
  | 'users'
  | 'reports'
  | 'settings'
  | 'search'
  | 'user'
  | 'bag'
  | 'heart'
  | 'chevron-down'
  | 'chevron-right'
  | 'plus'
  | 'bell'
  | 'dots'
  | 'eye'
  | 'eye-off'
  | 'mail'
  | 'lock'
  | 'edit'
  | 'power'
  | 'close'
  | 'arrow-right'
  | 'menu';

@Component({
  selector: 'app-icon',
  templateUrl: './icon.html',
  styleUrl: './icon.scss',
})
export class Icon {
  readonly name = input.required<IconName>();
}
