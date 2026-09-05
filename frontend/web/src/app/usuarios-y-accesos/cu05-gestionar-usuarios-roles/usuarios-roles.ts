import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ConfirmDialogService } from '../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../core/ui/icon/icon';
import { StatusBadge } from '../../core/ui/status-badge/status-badge';
import { ToastService } from '../../core/ui/toast/toast.service';
import { RolUsuario } from '../shared/models/usuario.model';
import {
  CatalogStatusFilter,
  RolDisponible,
  UsuarioAdmin,
} from './usuario-admin.model';
import { UsuarioAdminService } from './usuario-admin.service';
import { UsuarioFormValue, UsuarioForm } from './usuario-form/usuario-form';

const ETIQUETA_CLIENTE = 'Cliente';

@Component({
  selector: 'app-usuarios-roles',
  imports: [FormsModule, Icon, StatusBadge, UsuarioForm],
  templateUrl: './usuarios-roles.html',
  styleUrl: './usuarios-roles.scss',
})
export class UsuariosRoles {
  private readonly usuarioService = inject(UsuarioAdminService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly usuarios = signal<UsuarioAdmin[]>([]);
  protected readonly roles = signal<RolDisponible[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly searchTerm = signal('');
  protected readonly rolFilter = signal<RolUsuario | ''>('');
  protected readonly statusFilter = signal<CatalogStatusFilter>('all');

  protected readonly drawerOpen = signal(false);
  protected readonly editingUsuario = signal<UsuarioAdmin | null>(null);
  protected readonly viewMode = signal(false);
  protected readonly submitting = signal(false);

  protected readonly openMenuId = signal<number | null>(null);

  private searchDebounce?: ReturnType<typeof setTimeout>;

  constructor() {
    this.usuarioService.roles().subscribe({ next: (roles) => this.roles.set(roles) });
    this.load();
  }

  @HostListener('document:click')
  closeMenus(): void {
    this.openMenuId.set(null);
  }

  protected etiquetaRol(rol: RolUsuario): string {
    if (rol === 'CLIENTE') {
      return ETIQUETA_CLIENTE;
    }
    return this.roles().find((r) => r.valor === rol)?.etiqueta ?? rol;
  }

  onSearchChange(value: string): void {
    this.searchTerm.set(value);
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => this.load(), 350);
  }

  onRolFilterChange(value: string): void {
    this.rolFilter.set(value as RolUsuario | '');
    this.load();
  }

  onStatusFilterChange(value: string): void {
    this.statusFilter.set(value as CatalogStatusFilter);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.usuarioService
      .list({
        search: this.searchTerm() || undefined,
        rol: this.rolFilter() || undefined,
        estado: this.statusFilter(),
      })
      .subscribe({
        next: (usuarios) => {
          this.usuarios.set(usuarios);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.usuarios.set([]);
          this.errorMessage.set(
            'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
          );
        },
      });
  }

  openCreate(): void {
    this.editingUsuario.set(null);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openEdit(usuario: UsuarioAdmin): void {
    this.openMenuId.set(null);
    this.editingUsuario.set(usuario);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(usuario: UsuarioAdmin, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(null);
    this.editingUsuario.set(usuario);
    this.viewMode.set(true);
    this.drawerOpen.set(true);
  }

  closeDrawer(): void {
    this.drawerOpen.set(false);
  }

  toggleMenu(id: number, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(this.openMenuId() === id ? null : id);
  }

  save(payload: UsuarioFormValue): void {
    const editing = this.editingUsuario();
    this.submitting.set(true);

    if (editing) {
      const requests = [
        this.usuarioService.update(editing.id, {
          nombre: payload.nombre,
          correo: payload.correo,
          sucursal_id: payload.sucursal_id,
          proveedor_id: payload.proveedor_id,
        }),
      ];
      if (payload.rol !== editing.rol) {
        requests.push(this.usuarioService.changeRole(editing.id, payload.rol));
      }
      if (payload.is_active !== editing.is_active) {
        requests.push(this.usuarioService.setActive(editing.id, payload.is_active));
      }
      forkJoin(requests).subscribe({
        next: () => this.onSaveSuccess('Usuario actualizado correctamente.'),
        error: (err) => this.onSaveError(err),
      });
      return;
    }

    this.usuarioService.create({ ...payload, password: payload.password ?? '' }).subscribe({
      next: () => this.onSaveSuccess('Usuario creado correctamente.'),
      error: (err) => this.onSaveError(err),
    });
  }

  private onSaveSuccess(message: string): void {
    this.submitting.set(false);
    this.drawerOpen.set(false);
    this.toast.success(message);
    this.load();
  }

  private onSaveError(err: { status?: number }): void {
    this.submitting.set(false);
    if (err.status === 409) {
      this.toast.error('Ya existe un usuario con ese correo.');
    } else if (err.status === 422) {
      this.toast.error('Revisa la sucursal o el proveedor seleccionado para este rol.');
    } else {
      this.toast.error('No se pudo guardar el usuario. Intenta nuevamente.');
    }
  }

  async toggleStatus(usuario: UsuarioAdmin, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    if (usuario.is_active) {
      const confirmed = await this.confirmDialog.confirm({
        title: '¿Desactivar usuario?',
        message: `${usuario.nombre} dejará de poder iniciar sesión en FashionStore.`,
        confirmText: 'Desactivar',
        danger: true,
      });
      if (!confirmed) {
        return;
      }
    }

    this.usuarioService.setActive(usuario.id, !usuario.is_active).subscribe({
      next: () => {
        this.toast.success(usuario.is_active ? 'Usuario desactivado.' : 'Usuario activado correctamente.');
        this.load();
      },
      error: (err) => {
        if (err.status === 400) {
          this.toast.error('No puedes desactivar tu propia cuenta.');
        } else {
          this.toast.error('No se pudo actualizar el estado del usuario.');
        }
      },
    });
  }
}
