import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { CiudadPublica } from '../../public/sucursales/sucursal.model';
import { SucursalPublicaService } from '../../public/sucursales/sucursal.service';
import { ResumenCompraOut, SucursalCompraOut } from '../compra-digital.model';
import { CompraDigitalService } from '../compra-digital.service';

type Paso = 'resumen' | 'sucursal' | 'confirmacion';

/**
 * CU22 -- Realizar compra digital (Cliente). Pantalla "Finalizar compra"
 * ('/finalizar-compra', CLIENTE autenticado -- ver app.routes.ts), a la que
 * lleva el botón "CONTINUAR COMPRA" de CU21 (mi-carrito.html) -- ese botón
 * NUNCA tuvo lógica de compra propia, solo navega aquí.
 *
 * Wizard de un solo componente, 3 pasos (sin rutas hijas: cada paso es
 * estado local, ver `paso`):
 *  1. 'resumen'      -- SOLO las prendas que el Cliente ya marcó
 *                        seleccionadas en su carrito (CU21); si no hay
 *                        ninguna, el backend rechaza y esta pantalla ofrece
 *                        volver al carrito, nunca una tabla vacía rota.
 *  2. 'sucursal'     -- Ciudad -> Sucursales de esa ciudad, cada una con si
 *                        cubre o no TODA la compra (`disponible_para_compra`,
 *                        calculado por FastAPI, nunca en Angular). Si
 *                        ninguna sucursal de la ciudad elegida cubre todo,
 *                        se muestra el mensaje pedido y un botón al carrito.
 *  3. 'confirmacion' -- resumen final (sucursal+ciudad, prendas, total) con
 *                        VOLVER (a elegir sucursal) y CONTINUAR AL PAGO.
 *
 * CU22 TERMINA en 'confirmacion': "Continuar al pago" llama al backend para
 * crear la Venta (PENDIENTE_PAGO, código VT-00001 -- ver
 * CU22_RealizarCompraDigital/service.py) y navega a '/pago/iniciar'
 * (CU23_ProcesarPagoElectronico / features/pago-electronico) -- este
 * componente nunca importa nada de esa carpeta ni sabe nada de Stripe, solo
 * entrega el `venta_id` por query param, igual que mi-carrito.html solo
 * navega aquí sin conocer la lógica de CU22.
 *
 * El total SIEMPRE es el que devuelve el backend en cada paso -- este
 * componente nunca calcula total ni precios: si el precio de un producto
 * cambia entre pantallas, el propio backend lo recalcula al confirmar (ver
 * CU22_RealizarCompraDigital/service.py).
 */
@Component({
  selector: 'app-finalizar-compra',
  imports: [Icon, RouterLink],
  templateUrl: './finalizar-compra.html',
  styleUrl: './finalizar-compra.scss',
})
export class FinalizarCompra implements OnInit {
  private readonly service = inject(CompraDigitalService);
  private readonly sucursalesPublicas = inject(SucursalPublicaService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly paso = signal<Paso>('resumen');
  protected readonly cargando = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly resumen = signal<ResumenCompraOut | null>(null);

  protected readonly ciudades = signal<CiudadPublica[]>([]);
  protected readonly ciudadSeleccionadaId = signal<number | null>(null);
  protected readonly cargandoSucursales = signal(false);
  protected readonly sucursalesConsultadas = signal(false);
  protected readonly sucursales = signal<SucursalCompraOut[]>([]);
  protected readonly sucursalElegida = signal<SucursalCompraOut | null>(null);

  protected readonly confirmando = signal(false);

  get haySucursalDisponible(): boolean {
    return this.sucursales().some((s) => s.disponible_para_compra);
  }

  ngOnInit(): void {
    this.cargarResumen();
    this.sucursalesPublicas.listCiudades().subscribe({
      next: (ciudades) => this.ciudades.set(ciudades),
      error: () => this.ciudades.set([]),
    });
  }

  cargarResumen(): void {
    this.cargando.set(true);
    this.errorMessage.set(null);
    this.service.obtenerResumen().subscribe({
      next: (resumen) => {
        this.resumen.set(resumen);
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.errorMessage.set(detalle ?? 'No hay prendas seleccionadas para continuar.');
      },
    });
  }

  irAElegirSucursal(): void {
    this.paso.set('sucursal');
  }

  volverAResumen(): void {
    this.paso.set('resumen');
  }

  seleccionarCiudad(ciudadId: string): void {
    const id = Number(ciudadId);
    if (!id) {
      this.ciudadSeleccionadaId.set(null);
      this.sucursalesConsultadas.set(false);
      this.sucursales.set([]);
      return;
    }
    this.ciudadSeleccionadaId.set(id);
    this.cargandoSucursales.set(true);
    this.sucursalesConsultadas.set(false);
    this.service.listarSucursales(id).subscribe({
      next: (sucursales) => {
        this.sucursales.set(sucursales);
        this.cargandoSucursales.set(false);
        this.sucursalesConsultadas.set(true);
      },
      error: () => {
        this.sucursales.set([]);
        this.cargandoSucursales.set(false);
        this.sucursalesConsultadas.set(true);
        this.toast.error('No se pudo consultar las sucursales de esa ciudad. Inténtalo nuevamente.');
      },
    });
  }

  elegirSucursal(sucursal: SucursalCompraOut): void {
    if (!sucursal.disponible_para_compra) {
      return;
    }
    this.sucursalElegida.set(sucursal);
    this.paso.set('confirmacion');
  }

  volverAElegirSucursal(): void {
    this.paso.set('sucursal');
  }

  continuarAlPago(): void {
    const sucursal = this.sucursalElegida();
    if (!sucursal || this.confirmando()) {
      return;
    }
    this.confirmando.set(true);
    this.service.confirmar({ sucursal_id: sucursal.id }).subscribe({
      next: (venta) => {
        this.confirmando.set(false);
        // CU22 termina aquí: la Venta ya quedó guardada como
        // PENDIENTE_PAGO (ver CU22_RealizarCompraDigital/service.py).
        // Cobrar es responsabilidad de CU23 -- se navega a su punto de
        // entrada sin importar nada de esa carpeta, mismo criterio que
        // mi-carrito.html al enlazar hacia /finalizar-compra.
        this.router.navigate(['/pago/iniciar'], { queryParams: { venta_id: venta.id } });
      },
      error: (err) => {
        this.confirmando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo continuar con la compra. Inténtalo nuevamente.');
        // La sucursal pudo dejar de estar disponible justo ahora -- se
        // vuelve a elegir en vez de reintentar a ciegas contra la misma.
        this.paso.set('sucursal');
      },
    });
  }
}
