import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { SucursalAdmin } from '../../../sucursales-catalogo/cu06-gestionar-sucursales/sucursal-admin.model';
import { SucursalAdminService } from '../../../sucursales-catalogo/cu06-gestionar-sucursales/sucursal-admin.service';
import { BarraItem, GraficoBarras } from './grafico-barras/grafico-barras';
import { GraficoLineas, PuntoLinea } from './grafico-lineas/grafico-lineas';
import { ReconocimientoVozService } from './reconocimiento-voz.service';
import {
  InventarioReporte,
  ProductoMasVendido,
  ReportesFiltro,
  ReservasReporte,
  ResumenReporte,
  VentasReporte,
} from './reportes.model';
import { ReportesService } from './reportes.service';

// CU30 -- segunda parte: ejemplos discretos debajo de la consulta
// inteligente (ver instrucciones: "NO convertir esto en un chatbot" --
// solo rellenan el input, el Administrador confirma con GENERAR).
const EJEMPLOS_CONSULTA = [
  'Ventas de este mes',
  'Stock bajo en Mall Ventura',
  'Productos más vendidos esta semana',
];

const MSG_IA_NO_DISPONIBLE =
  'La consulta inteligente no está disponible en este momento. Puedes utilizar los filtros manuales.';
const MSG_VOZ_NO_DISPONIBLE =
  'El reconocimiento de voz no está disponible en este navegador. Puedes escribir tu consulta.';

const ETIQUETAS_TIPO_VENTA: Record<string, string> = {
  DIGITAL: 'Digital',
  PRESENCIAL: 'Presencial',
};

const ETIQUETAS_METODO_PAGO: Record<string, string> = {
  STRIPE: 'Stripe',
  EFECTIVO: 'Efectivo',
  TARJETA: 'Tarjeta',
  QR: 'QR',
};

function formatearFecha(fecha: Date): string {
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${anio}-${mes}-${dia}`;
}

function primerDiaDelMes(): string {
  const hoy = new Date();
  return formatearFecha(new Date(hoy.getFullYear(), hoy.getMonth(), 1));
}

function hoyComoTexto(): string {
  return formatearFecha(new Date());
}

/**
 * CU30 -- Consultar reportes e indicadores (Administrador).
 *
 * Primera parte: dashboard analítico real sobre PostgreSQL (KPIs, filtros
 * manuales, gráficos) -- ver secciones más abajo, sin tocar su lógica.
 *
 * Segunda parte (esta ampliación): "consulta inteligente" -- texto o
 * comando de voz -> POST /reportes/consulta-inteligente (Gemini interpreta
 * intención/filtros, FastAPI los valida/resuelve y reutiliza los MISMOS
 * endpoints de la primera parte, nunca una consulta nueva). El resultado
 * SIEMPRE controla los filtros/reportes ya existentes -- nunca una
 * respuesta aislada (ver generarConsultaInteligente(), que reutiliza
 * exactamente cargarDatos()).
 *
 * El filtrado (fechas/sucursal) se resuelve SIEMPRE en FastAPI -- este
 * componente nunca descarga datos crudos para sumarlos/agruparlos acá, solo
 * presenta lo que ya llega calculado (ver reportes.service.ts).
 *
 * Filtros "borrador" (sucursalIdDraft/fechaDesdeDraft/fechaHastaDraft)
 * separados de los "aplicados" -- mismo criterio que el resto del panel
 * Admin: escribir en los inputs no dispara ninguna consulta, solo
 * "APLICAR" (o una consulta inteligente exitosa) lo hace.
 */
@Component({
  selector: 'app-reportes',
  imports: [FormsModule, GraficoBarras, GraficoLineas],
  templateUrl: './reportes.html',
  styleUrl: './reportes.scss',
})
export class Reportes implements OnInit {
  private readonly service = inject(ReportesService);
  private readonly sucursalService = inject(SucursalAdminService);
  private readonly voz = inject(ReconocimientoVozService);

  protected readonly ejemplosConsulta = EJEMPLOS_CONSULTA;
  protected readonly vozDisponible = this.voz.disponible;

  protected readonly sucursales = signal<SucursalAdmin[]>([]);

  protected readonly sucursalIdDraft = signal<number | null>(null);
  protected readonly fechaDesdeDraft = signal<string>(primerDiaDelMes());
  protected readonly fechaHastaDraft = signal<string>(hoyComoTexto());
  protected readonly errorFiltro = signal<string | null>(null);

  private filtroAplicado: ReportesFiltro = {
    fecha_desde: this.fechaDesdeDraft(),
    fecha_hasta: this.fechaHastaDraft(),
    sucursal_id: null,
  };

  // -- CU30, segunda parte: consulta inteligente ------------------------
  protected readonly consultaTexto = signal('');
  protected readonly escuchando = signal(false);
  protected readonly generandoConsulta = signal(false);
  protected readonly resumenIA = signal<string | null>(null);
  protected readonly avisoVoz = signal<string | null>(null);

  protected readonly cargando = signal(true);
  protected readonly error = signal<string | null>(null);

  protected readonly resumen = signal<ResumenReporte | null>(null);
  protected readonly ventas = signal<VentasReporte | null>(null);
  protected readonly inventario = signal<InventarioReporte | null>(null);
  protected readonly reservas = signal<ReservasReporte | null>(null);
  protected readonly productosMasVendidos = signal<ProductoMasVendido[]>([]);

  ngOnInit(): void {
    this.sucursalService.list({ estado: 'active' }).subscribe({
      next: (sucursales) => this.sucursales.set(sucursales),
      error: () => this.sucursales.set([]),
    });
    this.cargarDatos();
  }

  protected etiquetaTipo(tipo: string): string {
    return ETIQUETAS_TIPO_VENTA[tipo] ?? tipo;
  }

  protected etiquetaMetodo(metodo: string): string {
    return ETIQUETAS_METODO_PAGO[metodo] ?? metodo;
  }

  protected barrasPorTipo(): BarraItem[] {
    return (this.ventas()?.por_tipo ?? []).map((item) => ({
      etiqueta: this.etiquetaTipo(item.tipo),
      valor: item.ventas,
      valorTexto: `${item.ventas} · Bs ${item.ingresos.toFixed(2)}`,
    }));
  }

  protected barrasPorMetodoPago(): BarraItem[] {
    return (this.ventas()?.por_metodo_pago ?? []).map((item) => ({
      etiqueta: this.etiquetaMetodo(item.metodo),
      valor: item.ventas,
      valorTexto: `${item.ventas} · Bs ${item.ingresos.toFixed(2)}`,
    }));
  }

  protected barrasPorSucursal(): BarraItem[] {
    return (this.ventas()?.por_sucursal ?? []).map((item) => ({
      etiqueta: item.sucursal,
      valor: item.ingresos,
      valorTexto: `Bs ${item.ingresos.toFixed(2)}`,
    }));
  }

  protected barrasProductosMasVendidos(): BarraItem[] {
    return this.productosMasVendidos().map((item) => ({
      etiqueta: item.nombre,
      valor: item.unidades,
      valorTexto: `${item.unidades} uds · Bs ${item.ingresos.toFixed(2)}`,
    }));
  }

  protected puntosVentasPorPeriodo(): PuntoLinea[] {
    return (this.ventas()?.por_periodo ?? []).map((item) => ({ etiqueta: item.periodo, valor: item.ingresos }));
  }

  aplicarFiltros(): void {
    const desde = this.fechaDesdeDraft() || null;
    const hasta = this.fechaHastaDraft() || null;
    if (desde && hasta && desde > hasta) {
      this.errorFiltro.set('La fecha "Desde" no puede ser posterior a "Hasta".');
      return;
    }
    this.errorFiltro.set(null);
    this.filtroAplicado = { fecha_desde: desde, fecha_hasta: hasta, sucursal_id: this.sucursalIdDraft() };
    this.cargarDatos();
  }

  limpiarFiltros(): void {
    this.sucursalIdDraft.set(null);
    this.fechaDesdeDraft.set(primerDiaDelMes());
    this.fechaHastaDraft.set(hoyComoTexto());
    this.errorFiltro.set(null);
    this.filtroAplicado = { fecha_desde: primerDiaDelMes(), fecha_hasta: hoyComoTexto(), sucursal_id: null };
    this.cargarDatos();
  }

  // -----------------------------------------------------------------
  // CU30, segunda parte -- consulta inteligente (texto/voz + Gemini)
  // -----------------------------------------------------------------

  protected actualizarConsultaTexto(valor: string): void {
    this.consultaTexto.set(valor);
  }

  protected usarEjemplo(ejemplo: string): void {
    this.consultaTexto.set(ejemplo);
  }

  protected limpiarConsultaInteligente(): void {
    this.consultaTexto.set('');
    this.resumenIA.set(null);
    this.avisoVoz.set(null);
  }

  protected alternarMicrofono(): void {
    if (this.escuchando()) {
      this.voz.detener();
      return;
    }
    if (!this.vozDisponible) {
      this.avisoVoz.set(MSG_VOZ_NO_DISPONIBLE);
      return;
    }

    this.avisoVoz.set(null);
    this.escuchando.set(true);
    this.voz
      .escuchar()
      .then((texto) => {
        this.escuchando.set(false);
        if (texto) {
          // El Administrador puede editarlo antes de GENERAR -- solo se
          // rellena el input, nunca se envía automáticamente.
          this.consultaTexto.set(texto);
        }
      })
      .catch(() => {
        this.escuchando.set(false);
      });
  }

  protected onSubmitConsultaIA(evento: Event): void {
    evento.preventDefault();
    this.generarConsultaInteligente();
  }

  protected generarConsultaInteligente(): void {
    const consulta = this.consultaTexto().trim();
    if (!consulta || this.generandoConsulta()) {
      return;
    }

    this.generandoConsulta.set(true);
    this.resumenIA.set(null);

    this.service
      .consultaInteligente({
        consulta,
        sucursal_id_actual: this.filtroAplicado.sucursal_id,
        fecha_desde_actual: this.filtroAplicado.fecha_desde,
        fecha_hasta_actual: this.filtroAplicado.fecha_hasta,
      })
      .subscribe({
        next: (respuesta) => {
          this.generandoConsulta.set(false);
          this.resumenIA.set(respuesta.resumen);

          if (!respuesta.exito || !respuesta.filtros) {
            // Mensaje amigable ya mostrado en `resumenIA` -- el dashboard
            // (filtros/KPIs/gráficos) se deja intacto, nunca se toca con
            // una consulta que no se pudo resolver.
            return;
          }

          // La consulta inteligente CONTROLA los filtros ya existentes --
          // nunca arma una vista aislada (ver reportes.html).
          const { sucursal_id, fecha_desde, fecha_hasta } = respuesta.filtros;
          this.sucursalIdDraft.set(sucursal_id);
          this.fechaDesdeDraft.set(fecha_desde ?? '');
          this.fechaHastaDraft.set(fecha_hasta ?? '');
          this.errorFiltro.set(null);
          this.filtroAplicado = { sucursal_id, fecha_desde, fecha_hasta };
          this.cargarDatos();
        },
        error: () => {
          this.generandoConsulta.set(false);
          this.resumenIA.set(MSG_IA_NO_DISPONIBLE);
        },
      });
  }

  private cargarDatos(): void {
    this.cargando.set(true);
    this.error.set(null);

    forkJoin({
      resumen: this.service.resumen(this.filtroAplicado),
      ventas: this.service.ventas(this.filtroAplicado),
      inventario: this.service.inventario(this.filtroAplicado),
      reservas: this.service.reservas(this.filtroAplicado),
      productosMasVendidos: this.service.productosMasVendidos(this.filtroAplicado),
    }).subscribe({
      next: ({ resumen, ventas, inventario, reservas, productosMasVendidos }) => {
        this.resumen.set(resumen);
        this.ventas.set(ventas);
        this.inventario.set(inventario);
        this.reservas.set(reservas);
        this.productosMasVendidos.set(productosMasVendidos.productos);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar los reportes. Inténtalo nuevamente.');
        this.cargando.set(false);
      },
    });
  }
}
