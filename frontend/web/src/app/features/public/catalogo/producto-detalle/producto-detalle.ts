import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { Icon } from '../../../../core/ui/icon/icon';
import { CiudadPublica } from '../../sucursales/sucursal.model';
import { SucursalPublicaService } from '../../sucursales/sucursal.service';
import { ProductoPublico } from '../catalogo.model';
import { CatalogoService } from '../catalogo.service';
import { CrearReserva } from '../../../reservas/crear-reserva/crear-reserva';
import { AgregarCarrito } from '../../../carrito/agregar-carrito/agregar-carrito';
import { DisponibilidadSucursal, VarianteDisponible } from './disponibilidad.model';
import { DisponibilidadService } from './disponibilidad.service';

const CIUDAD_STORAGE_KEY = 'fashionstore_ciudad_id';

@Component({
  selector: 'app-producto-detalle',
  imports: [RouterLink, Icon, FormsModule, CrearReserva, AgregarCarrito],
  templateUrl: './producto-detalle.html',
  styleUrl: './producto-detalle.scss',
})
export class ProductoDetalle {
  private readonly route = inject(ActivatedRoute);
  private readonly catalogoService = inject(CatalogoService);
  private readonly sucursalService = inject(SucursalPublicaService);
  private readonly disponibilidadService = inject(DisponibilidadService);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly producto = signal<ProductoPublico | null>(null);
  protected readonly loading = signal(true);
  protected readonly notFound = signal(false);

  protected readonly imagenActivaUrl = signal<string | null>(null);
  protected readonly tallaSeleccionadaId = signal<number | null>(null);
  protected readonly colorSeleccionadoId = signal<number | null>(null);
  // Si una imagen referenciada ya no existe físicamente (ej. archivo perdido),
  // se marca aquí para caer al ícono de reserva en vez del roto nativo del navegador.
  protected readonly erroredUrls = signal<ReadonlySet<string>>(new Set());

  // Disponibilidad en tiendas -- CU12: por cada sucursal, trae todas las
  // variantes (talla+color) activas del producto con su stock real (ver
  // ProductoDisponibilidad). Aquí se guarda solo el array de sucursales
  // (`.disponibilidad`), que es lo que consume la plantilla. La lista de
  // ciudades sigue viniendo de CU07 (reutilizada, no duplicada).
  //
  // ciudadId NACE EN null: a diferencia de talla/color (que sí tienen un
  // valor por defecto razonable, la primera opción del producto), la ciudad
  // no se autoselecciona -- mostrar "la primera ciudad de la base de datos"
  // sin que el Cliente la haya elegido es justo lo que no queremos. Se
  // recuerda en localStorage (ver CIUDAD_STORAGE_KEY) para que persista al
  // navegar a otro producto o volver del login, sin crear nada en el
  // backend (no hay "sucursal favorita" todavía, ver ticket de CU17).
  protected readonly ciudades = signal<CiudadPublica[]>([]);
  protected readonly disponibilidad = signal<DisponibilidadSucursal[]>([]);
  protected readonly ciudadId = signal<number | null>(null);
  protected readonly loadingCiudades = signal(true);
  protected readonly loadingDisponibilidad = signal(false);
  protected readonly errorDisponibilidad = signal<string | null>(null);

  // CU17 (crear reserva): sucursal que el propio Cliente eligió haciendo
  // clic en una tarjeta de "Stock por sucursal" -- a diferencia de
  // talla/color (atributos del producto), la sucursal no tiene un valor por
  // defecto: nace en null y solo el Cliente la fija. Se reinicia cuando
  // cambia talla, color o ciudad porque la disponibilidad ya no es la misma.
  // Fecha y horario ya NO se eligen aquí: viven dentro del modal de
  // CrearReserva (ver crear-reserva.ts), que se abre al presionar
  // "Reservar" una vez hay sucursal elegida.
  protected readonly sucursalSeleccionadaId = signal<number | null>(null);

  // Variante real (id) que corresponde a la talla+color elegidos arriba. Es
  // la misma en todas las tarjetas de sucursal (ProductoVariante es global,
  // solo el stock cambia por sucursal) -- se toma de la primera coincidencia.
  // null si CU12 todavía no respondió o si esa combinación no existe.
  protected readonly varianteSeleccionadaId = computed<number | null>(() => {
    const tallaId = this.tallaSeleccionadaId();
    const colorId = this.colorSeleccionadoId();
    for (const item of this.disponibilidad()) {
      const match = item.variantes.find((v) => v.talla_id === tallaId && v.color_id === colorId);
      if (match) {
        return match.producto_variante_id;
      }
    }
    return null;
  });

  // Nombre a mostrar dentro del modal ("Programar reserva") -- se busca por
  // id en la misma respuesta de CU12 que ya trae la lista de sucursales.
  protected readonly sucursalSeleccionadaNombre = computed<string | null>(() => {
    const id = this.sucursalSeleccionadaId();
    return this.disponibilidad().find((s) => s.sucursal_id === id)?.sucursal ?? null;
  });

  // Ruta a la que CrearReserva debe volver tras el login si el visitante no
  // tenía sesión (ver login.ts, que lee "returnUrl"). Conserva ciudad,
  // talla, color y sucursal -- fecha/hora NO se agregan aquí: viven dentro
  // de CrearReserva (el modal), que las agrega a esta misma URL base
  // recién al presionar "Confirmar reserva" (ver confirmar() en
  // crear-reserva.ts), porque es quien las conoce.
  protected readonly returnUrlReserva = computed(() => {
    const producto = this.producto();
    const tallaId = this.tallaSeleccionadaId();
    const colorId = this.colorSeleccionadoId();
    const ciudadId = this.ciudadId();
    const sucursalId = this.sucursalSeleccionadaId();
    if (!producto) {
      return '/';
    }
    let url = `/producto/${producto.id}?tallaId=${tallaId}&colorId=${colorId}`;
    if (ciudadId !== null) {
      url += `&ciudadId=${ciudadId}`;
    }
    if (sucursalId !== null) {
      url += `&sucursalId=${sucursalId}`;
    }
    return url;
  });

  // CU21 (agregar al carrito): a diferencia de returnUrlReserva, NUNCA
  // incluye ciudad ni sucursal -- el carrito no los necesita (ver
  // agregar-carrito.ts). AgregarCarrito le agrega "&agregarCarrito=1" recién
  // al navegar a /login, porque es quien decide disparar esa intención.
  protected readonly returnUrlCarrito = computed(() => {
    const producto = this.producto();
    const tallaId = this.tallaSeleccionadaId();
    const colorId = this.colorSeleccionadoId();
    if (!producto) {
      return '/';
    }
    return `/producto/${producto.id}?tallaId=${tallaId}&colorId=${colorId}`;
  });

  // Se restaura como máximo una vez al volver del login -- si el Cliente
  // cambia de ciudad, talla o color después, la sucursal se reinicia
  // normalmente y no se vuelve a forzar este valor. fecha/hora crudas (sin
  // validar) se pasan tal cual a CrearReserva -- es quien decide si siguen
  // siendo válidas (ver efecto en crear-reserva.ts).
  private sucursalRestaurada = false;
  private readonly ciudadIdParam: number | null;
  private readonly sucursalIdParam: number | null;
  protected readonly fechaParam: string | null;
  protected readonly horaParam: string | null;
  // CU21 (agregar al carrito): "1" crudo si volvemos del login con la
  // intención de agregar al carrito pendiente -- ver returnUrlCarrito() y
  // AgregarCarrito (agregar-carrito.ts), que dispara el agregado automático
  // una sola vez y limpia este mismo query param al terminar.
  protected readonly agregarCarritoParam: boolean;

  constructor() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    const tallaIdParam = Number(this.route.snapshot.queryParamMap.get('tallaId')) || null;
    const colorIdParam = Number(this.route.snapshot.queryParamMap.get('colorId')) || null;
    this.ciudadIdParam = Number(this.route.snapshot.queryParamMap.get('ciudadId')) || null;
    this.sucursalIdParam = Number(this.route.snapshot.queryParamMap.get('sucursalId')) || null;
    this.fechaParam = this.route.snapshot.queryParamMap.get('fecha');
    this.horaParam = this.route.snapshot.queryParamMap.get('hora');
    this.agregarCarritoParam = this.route.snapshot.queryParamMap.get('agregarCarrito') === '1';

    this.catalogoService.getProducto(id).subscribe({
      next: (producto) => {
        this.producto.set(producto);
        this.imagenActivaUrl.set(producto.imagen_principal_url);
        // Si venimos de vuelta del login (ver returnUrlReserva), se respeta
        // la talla/color que el Cliente ya había elegido antes de irse --
        // solo si esa talla/color efectivamente pertenece al producto.
        const tallaValida = producto.tallas.find((t) => t.id === tallaIdParam);
        const colorValido = producto.colores.find((c) => c.id === colorIdParam);
        this.tallaSeleccionadaId.set(tallaValida?.id ?? producto.tallas[0]?.id ?? null);
        this.colorSeleccionadoId.set(colorValido?.id ?? producto.colores[0]?.id ?? null);
        this.loading.set(false);
        this.loadDisponibilidad();
      },
      error: () => {
        this.loading.set(false);
        this.notFound.set(true);
      },
    });

    this.sucursalService.listCiudades().subscribe({
      next: (ciudades) => {
        this.ciudades.set(ciudades);
        this.loadingCiudades.set(false);
        // Prioridad: la ciudad que traía el returnUrl del login (intención
        // explícita reciente) -> la última que el Cliente recordaba de una
        // sesión de navegación anterior (localStorage) -> ninguna. NUNCA la
        // primera de la lista sin que el Cliente la haya elegido.
        const ciudadDeVuelta = ciudades.find((c) => c.id === this.ciudadIdParam);
        const ciudadGuardada = ciudades.find((c) => c.id === this.leerCiudadGuardada());
        const ciudadInicial = ciudadDeVuelta ?? ciudadGuardada ?? null;
        if (ciudadInicial) {
          this.ciudadId.set(ciudadInicial.id);
          this.guardarCiudad(ciudadInicial.id);
          this.loadDisponibilidad();
        }
      },
      error: () => {
        this.loadingCiudades.set(false);
        this.errorDisponibilidad.set('No se pudieron cargar las ciudades. Inténtalo nuevamente.');
      },
    });
  }

  private leerCiudadGuardada(): number | null {
    try {
      const valor = localStorage.getItem(CIUDAD_STORAGE_KEY);
      return valor ? Number(valor) : null;
    } catch {
      return null;
    }
  }

  private guardarCiudad(ciudadId: number): void {
    try {
      localStorage.setItem(CIUDAD_STORAGE_KEY, String(ciudadId));
    } catch {
      // Almacenamiento no disponible (ej. navegación privada) -- la ciudad
      // simplemente no persiste entre productos, sin romper la selección
      // actual.
    }
  }

  onCiudadChange(value: string): void {
    const ciudadId = value ? Number(value) : null;
    this.ciudadId.set(ciudadId);
    this.sucursalSeleccionadaId.set(null);
    if (ciudadId !== null) {
      this.guardarCiudad(ciudadId);
      this.loadDisponibilidad();
    } else {
      this.disponibilidad.set([]);
    }
  }

  loadDisponibilidad(): void {
    const producto = this.producto();
    const tallaId = this.tallaSeleccionadaId();
    const colorId = this.colorSeleccionadoId();
    const ciudadId = this.ciudadId();
    // Requiere producto + talla + color + ciudad ya resueltos -- el
    // producto y las ciudades cargan en paralelo, así que cada uno dispara
    // esta carga al terminar y el que llegue primero simplemente no hace
    // nada. Sin ciudad elegida (todavía) tampoco se consulta nada.
    if (!producto || !tallaId || !colorId || !ciudadId) {
      return;
    }

    this.loadingDisponibilidad.set(true);
    this.errorDisponibilidad.set(null);
    this.disponibilidadService.consultar(producto.id, tallaId, colorId, ciudadId).subscribe({
      next: (respuesta) => {
        this.disponibilidad.set(respuesta.disponibilidad);
        this.loadingDisponibilidad.set(false);
        this.restaurarSucursalSiCorresponde();
      },
      error: () => {
        this.loadingDisponibilidad.set(false);
        this.disponibilidad.set([]);
        this.errorDisponibilidad.set('No se pudo consultar la disponibilidad. Inténtalo nuevamente.');
      },
    });
  }

  // Vuelta del login (ver returnUrlReserva/sucursalIdParam): si esa
  // sucursal sigue apareciendo con stock real en esta misma consulta, se
  // reselecciona sola para no obligar al Cliente a elegirla de nuevo. Si no
  // aparece (ej. cambió de ciudad sin querer, o se agotó), simplemente no
  // se restaura -- no es peor que el comportamiento de antes de este ajuste.
  private restaurarSucursalSiCorresponde(): void {
    if (this.sucursalRestaurada || this.sucursalIdParam === null) {
      return;
    }
    this.sucursalRestaurada = true;
    const tallaId = this.tallaSeleccionadaId();
    const colorId = this.colorSeleccionadoId();
    const item = this.disponibilidad().find((s) => s.sucursal_id === this.sucursalIdParam);
    const variante = item?.variantes.find((v) => v.talla_id === tallaId && v.color_id === colorId);
    if (item && variante && variante.cantidad > 0) {
      this.sucursalSeleccionadaId.set(item.sucursal_id);
    }
  }

  protected get galeria(): string[] {
    const producto = this.producto();
    if (!producto) {
      return [];
    }
    const adicionales = producto.imagenes.map((imagen) => imagen.url);
    return producto.imagen_principal_url
      ? [producto.imagen_principal_url, ...adicionales]
      : adicionales;
  }

  seleccionarImagen(url: string): void {
    this.imagenActivaUrl.set(url);
  }

  marcarImagenRota(url: string): void {
    this.erroredUrls.update((actuales) => new Set(actuales).add(url));
  }

  seleccionarTalla(id: number): void {
    this.tallaSeleccionadaId.set(id);
    this.sucursalSeleccionadaId.set(null);
    this.loadDisponibilidad();
  }

  seleccionarColor(id: number): void {
    this.colorSeleccionadoId.set(id);
    this.sucursalSeleccionadaId.set(null);
    this.loadDisponibilidad();
  }

  // Variante (talla+color ya elegidos arriba) tal como la ve esta sucursal
  // puntual -- solo para leer su `cantidad` y saber si esta tarjeta es
  // seleccionable. No repite color/talla en la tarjeta: eso ya se muestra
  // una sola vez arriba, en la selección del producto.
  varianteDe(item: DisponibilidadSucursal): VarianteDisponible | undefined {
    const tallaId = this.tallaSeleccionadaId();
    const colorId = this.colorSeleccionadoId();
    return item.variantes.find((v) => v.talla_id === tallaId && v.color_id === colorId);
  }

  seleccionarSucursal(sucursalId: number, disponible: boolean): void {
    if (!disponible) {
      return;
    }
    this.sucursalSeleccionadaId.set(sucursalId);
  }

  // Tras una reserva exitosa (ver (reservado) en producto-detalle.html): la
  // confirmación temporal la muestra el ToastService global (ver
  // crear-reserva.ts), no esta vista, y el modal ya se cierra solo dentro
  // de CrearReserva. Se limpia la sucursal elegida -- la tarjeta se
  // deselecciona visualmente y el botón "Reservar" vuelve a su estado
  // inicial (deshabilitado hasta elegir sucursal de nuevo), sin ocultarse
  // nunca. Talla, color y ciudad quedan igual: son atributos del
  // producto/preferencia de navegación, no de una reserva puntual.
  //
  // loadDisponibilidad() se vuelve a llamar a propósito: CU17 acaba de
  // comprometer stock (stock_reservado, ver backend), así que la cantidad
  // "disponible" que ya mostraban las tarjetas de sucursal quedó desactualizada
  // -- sin este refresco, esta misma pantalla seguiría marcando como
  // "Disponible" una unidad que este mismo Cliente ya reservó, dejando
  // reservar de nuevo la misma última unidad sin recargar la página.
  onReservaCreada(): void {
    this.sucursalSeleccionadaId.set(null);
    this.loadDisponibilidad();
  }
}
