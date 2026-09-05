import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Icon } from '../../../core/ui/icon/icon';
import {
  CiudadOpcion,
  ProveedorOpcion,
  RolAsignableCU05,
  RolDisponible,
  SucursalOpcion,
  UsuarioAdmin,
} from '../usuario-admin.model';
import { UsuarioAdminService } from '../usuario-admin.service';

export interface UsuarioFormValue {
  nombre: string;
  correo: string;
  password?: string;
  rol: RolAsignableCU05;
  sucursal_id: number | null;
  proveedor_id: number | null;
  is_active: boolean;
}

const ROLES_CON_SUCURSAL = new Set(['ENCARGADO_SUCURSAL', 'CAJERO']);
const ROLES_CON_PROVEEDOR = new Set(['PROVEEDOR']);

@Component({
  selector: 'app-usuario-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './usuario-form.html',
  styleUrl: './usuario-form.scss',
})
export class UsuarioForm {
  readonly open = input(false);
  readonly usuario = input<UsuarioAdmin | null>(null);
  readonly roles = input<RolDisponible[]>([]);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<UsuarioFormValue>();
  readonly close = output<void>();

  private readonly fb = inject(FormBuilder);
  private readonly usuarioService = inject(UsuarioAdminService);

  protected readonly ciudades = signal<CiudadOpcion[]>([]);
  protected readonly sucursales = signal<SucursalOpcion[]>([]);
  protected readonly proveedores = signal<ProveedorOpcion[]>([]);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(120)]],
    correo: ['', [Validators.required, Validators.email]],
    password: [''],
    rol: ['' as RolAsignableCU05, [Validators.required]],
    ciudad_id: [null as number | null],
    sucursal_id: [null as number | null],
    proveedor_id: [null as number | null],
    is_active: [true],
  });

  constructor() {
    this.usuarioService.ciudades().subscribe({ next: (ciudades) => this.ciudades.set(ciudades) });
    this.usuarioService.proveedores().subscribe({ next: (p) => this.proveedores.set(p) });

    this.form.controls.ciudad_id.valueChanges.subscribe((ciudadId) => {
      this.form.controls.sucursal_id.setValue(null);
      this.cargarSucursales(ciudadId);
    });

    this.form.controls.rol.valueChanges.subscribe((rol) => this.aplicarReglasPorRol(rol));

    effect(() => {
      if (!this.open()) {
        return;
      }
      const usuario = this.usuario();
      if (usuario) {
        const ciudadId = usuario.sucursal?.ciudad.id ?? null;
        // emitEvent: false evita que valueChanges (suscritos arriba) borren los
        // valores que este mismo reset acaba de precargar.
        this.form.reset(
          {
            nombre: usuario.nombre,
            correo: usuario.correo,
            password: '',
            rol: usuario.rol as RolAsignableCU05,
            ciudad_id: ciudadId,
            sucursal_id: usuario.sucursal?.id ?? null,
            proveedor_id: usuario.proveedor?.id ?? null,
            is_active: usuario.is_active,
          },
          { emitEvent: false },
        );
        this.form.controls.password.clearValidators();
        this.cargarSucursales(ciudadId);
      } else {
        this.form.reset(
          {
            nombre: '',
            correo: '',
            password: '',
            rol: '' as RolAsignableCU05,
            ciudad_id: null,
            sucursal_id: null,
            proveedor_id: null,
            is_active: true,
          },
          { emitEvent: false },
        );
        this.form.controls.password.setValidators([Validators.required, Validators.minLength(8)]);
        this.sucursales.set([]);
      }
      this.form.controls.password.updateValueAndValidity();
      this.aplicarReglasPorRol(this.form.controls.rol.value);

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  private aplicarReglasPorRol(rol: string): void {
    const { ciudad_id, sucursal_id, proveedor_id } = this.form.controls;
    if (ROLES_CON_SUCURSAL.has(rol)) {
      ciudad_id.setValidators([Validators.required]);
      sucursal_id.setValidators([Validators.required]);
      proveedor_id.clearValidators();
      proveedor_id.setValue(null);
    } else if (ROLES_CON_PROVEEDOR.has(rol)) {
      proveedor_id.setValidators([Validators.required]);
      ciudad_id.clearValidators();
      sucursal_id.clearValidators();
      ciudad_id.setValue(null);
      sucursal_id.setValue(null);
    } else {
      ciudad_id.clearValidators();
      sucursal_id.clearValidators();
      proveedor_id.clearValidators();
    }
    ciudad_id.updateValueAndValidity({ emitEvent: false });
    sucursal_id.updateValueAndValidity({ emitEvent: false });
    proveedor_id.updateValueAndValidity({ emitEvent: false });
  }

  protected get mostrarSucursal(): boolean {
    return ROLES_CON_SUCURSAL.has(this.form.controls.rol.value);
  }

  protected get mostrarProveedor(): boolean {
    return ROLES_CON_PROVEEDOR.has(this.form.controls.rol.value);
  }

  private cargarSucursales(ciudadId: number | null): void {
    if (ciudadId == null) {
      this.sucursales.set([]);
      return;
    }
    this.usuarioService
      .sucursalesPorCiudad(ciudadId)
      .subscribe({ next: (sucursales) => this.sucursales.set(sucursales) });
  }

  protected get isEditMode(): boolean {
    return this.usuario() !== null;
  }

  submit(): void {
    if (this.readonly()) {
      return;
    }
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    this.save.emit({
      nombre: value.nombre.trim(),
      correo: value.correo.trim().toLowerCase(),
      password: value.password ? value.password : undefined,
      rol: value.rol,
      sucursal_id: value.sucursal_id,
      proveedor_id: value.proveedor_id,
      is_active: value.is_active,
    });
  }
}
