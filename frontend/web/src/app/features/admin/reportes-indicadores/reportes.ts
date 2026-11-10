import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin, timeout, finalize } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { SuperadminService } from '../../superadmin/services/superadmin.service';
import { SucursalAdmin } from '../../../sucursales-catalogo/cu06-gestionar-sucursales/sucursal-admin.model';
import { SucursalAdminService } from '../../../sucursales-catalogo/cu06-gestionar-sucursales/sucursal-admin.service';
import { BarraItem, GraficoBarras } from './grafico-barras/grafico-barras';
import { GraficoLineas, PuntoLinea } from './grafico-lineas/grafico-lineas';
import { ReconocimientoVozService } from './reconocimiento-voz.service';
import { CategoryService } from '../../../sucursales-catalogo/atributos/services/category.service';
import { ProductoService } from '../../../sucursales-catalogo/cu08-gestionar-productos/producto.service';
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
  private readonly authService = inject(AuthService);
  private readonly superadminService = inject(SuperadminService);
  // CU17 -- Servicios para cargar categorías y productos
  private readonly categoryService = inject(CategoryService);
  private readonly productoService = inject(ProductoService);

  protected readonly ejemplosConsulta = EJEMPLOS_CONSULTA;
  protected readonly vozDisponible = this.voz.disponible;
  protected readonly tieneFuncionialidadIA = signal(false);

  protected readonly sucursales = signal<SucursalAdmin[]>([]);

  // CU17 -- Categorías y productos para selectores
  protected readonly categorias = signal<any[]>([]);
  protected readonly productos = signal<any[]>([]);
  protected readonly cargandoCategorias = signal(false);
  protected readonly cargandoProductos = signal(false);

  protected readonly sucursalIdDraft = signal<number | null>(null);
  // CU17 -- Nuevos filtros para reporte dinámico (ahora selectores en lugar de inputs)
  protected readonly categoriaIdDraft = signal<number | null>(null);
  protected readonly productoIdDraft = signal<number | null>(null);

  // CU17 -- Productos filtrados por categoría seleccionada
  protected readonly productosFiltrados = computed(() => {
    const categoriaId = this.categoriaIdDraft();
    if (!categoriaId) return this.productos();
    return this.productos().filter((p: any) => p.categoria?.id === categoriaId);
  });

  protected readonly fechaDesdeDraft = signal<string>(primerDiaDelMes());
  protected readonly fechaHastaDraft = signal<string>(hoyComoTexto());
  protected readonly errorFiltro = signal<string | null>(null);

  private filtroAplicado: ReportesFiltro = {
    fecha_desde: this.fechaDesdeDraft(),
    fecha_hasta: this.fechaHastaDraft(),
    sucursal_id: null,
  };

  // CU17 -- Datos adicionales del reporte dinámico
  protected readonly reporteDinamico = signal<any>(null);

  // CU18 -- Estado de exportación
  protected readonly exportandoPDF = signal(false);
  protected readonly exportandoXLSX = signal(false);
  protected readonly errorExportacion = signal<string | null>(null);

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

    // CU17 -- Cargar categorías y productos para los selectores
    this.cargarCategorias();
    this.cargarProductos();

    const usuario = this.authService.usuario();
    if (usuario?.empresa_id) {
      this.superadminService.getSuscripcionEmpresa(usuario.empresa_id).subscribe({
        next: (data: any) => {
          const tieneFuncionialidad = data.plan?.reportes_generativos_ia ?? false;
          this.tieneFuncionialidadIA.set(tieneFuncionialidad);
        },
        error: () => this.tieneFuncionialidadIA.set(false),
      });
    }

    this.cargarDatos();
  }

  private cargarCategorias(): void {
    this.cargandoCategorias.set(true);
    this.categoryService.list({ estado: 'active' }).subscribe({
      next: (categorias: any[]) => {
        this.categorias.set(categorias);
        this.cargandoCategorias.set(false);
      },
      error: () => {
        this.categorias.set([]);
        this.cargandoCategorias.set(false);
      },
    });
  }

  private cargarProductos(): void {
    this.cargandoProductos.set(true);
    this.productoService.list({ estado: 'active' }).subscribe({
      next: (productos: any[]) => {
        this.productos.set(productos);
        this.cargandoProductos.set(false);
      },
      error: () => {
        this.productos.set([]);
        this.cargandoProductos.set(false);
      },
    });
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

    // CU17 -- Si hay filtros de categoría o producto, generar reporte dinámico
    if (this.categoriaIdDraft() || this.productoIdDraft()) {
      this.generarReporteDinamico();
    } else {
      this.reporteDinamico.set(null);
    }

    this.cargarDatos();
  }

  protected generarReporteDinamico(): void {
    const filtros = {
      fecha_desde: this.fechaDesdeDraft() || null,
      fecha_hasta: this.fechaHastaDraft() || null,
      sucursal_id: this.sucursalIdDraft(),
      categoria_id: this.categoriaIdDraft(),
      producto_id: this.productoIdDraft(),
      tipo_reporte: 'completo',
    };

    this.service.generarReporteDinamico(filtros).subscribe({
      next: (respuesta: any) => {
        this.reporteDinamico.set(respuesta.datos);
      },
      error: (err: any) => {
        console.error('Error generando reporte dinámico:', err);
        this.reporteDinamico.set(null);
      },
    });
  }

  limpiarFiltros(): void {
    this.sucursalIdDraft.set(null);
    this.categoriaIdDraft.set(null);
    this.productoIdDraft.set(null);
    this.fechaDesdeDraft.set(primerDiaDelMes());
    this.fechaHastaDraft.set(hoyComoTexto());
    this.errorFiltro.set(null);
    this.filtroAplicado = { fecha_desde: primerDiaDelMes(), fecha_hasta: hoyComoTexto(), sucursal_id: null };
    this.reporteDinamico.set(null);
    this.cargarDatos();
  }

  // CU17 -- Cuando cambia la categoría, resetear el producto si no está en la nueva categoría
  protected onCategoriaChange(nuevaCategoria: number | null): void {
    this.categoriaIdDraft.set(nuevaCategoria);
    if (nuevaCategoria && this.productoIdDraft()) {
      const producto = this.productos().find((p: any) => p.id === this.productoIdDraft());
      if (producto?.categoria?.id !== nuevaCategoria) {
        this.productoIdDraft.set(null);
      }
    }
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
      .pipe(
        timeout(30000),
        finalize(() => {
          // Garantizar que generandoConsulta SIEMPRE se resetee,
          // incluso si la solicitud se aborta o causa timeout
          if (this.generandoConsulta()) {
            this.generandoConsulta.set(false);
          }
        })
      )
      .subscribe({
        next: (respuesta) => {
          this.resumenIA.set(respuesta.resumen);

          if (!respuesta.exito || !respuesta.filtros) {
            return;
          }

          const { sucursal_id, fecha_desde, fecha_hasta } = respuesta.filtros;
          this.sucursalIdDraft.set(sucursal_id);
          this.fechaDesdeDraft.set(fecha_desde ?? '');
          this.fechaHastaDraft.set(fecha_hasta ?? '');
          this.errorFiltro.set(null);
          this.filtroAplicado = { sucursal_id, fecha_desde, fecha_hasta };
          this.cargarDatos();
        },
        error: () => {
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

  // CU18 -- Exportar reporte dinámico
  protected exportarReportePDF(): void {
    if (!this.reporteDinamico()) {
      this.errorExportacion.set('No hay reporte generado para exportar');
      return;
    }

    this.exportandoPDF.set(true);
    this.errorExportacion.set(null);

    const payload = {
      fecha_desde: this.fechaDesdeDraft() || null,
      fecha_hasta: this.fechaHastaDraft() || null,
      sucursal_id: this.sucursalIdDraft(),
      categoria_id: this.categoriaIdDraft(),
      producto_id: this.productoIdDraft(),
      tipo_reporte: 'completo',
    };

    this.service.exportarReporte(payload, 'pdf').pipe(
      finalize(() => this.exportandoPDF.set(false))
    ).subscribe({
      next: (blob: Blob) => {
        this._descargarArchivo(blob, 'application/pdf', `reporte_${new Date().getTime()}.pdf`);
      },
      error: (err: any) => {
        console.error('Error exportando PDF:', err);
        this.errorExportacion.set('Error al exportar PDF. Inténtalo nuevamente.');
      },
    });
  }

  protected exportarReporteXLSX(): void {
    if (!this.reporteDinamico()) {
      this.errorExportacion.set('No hay reporte generado para exportar');
      return;
    }

    this.exportandoXLSX.set(true);
    this.errorExportacion.set(null);

    const payload = {
      fecha_desde: this.fechaDesdeDraft() || null,
      fecha_hasta: this.fechaHastaDraft() || null,
      sucursal_id: this.sucursalIdDraft(),
      categoria_id: this.categoriaIdDraft(),
      producto_id: this.productoIdDraft(),
      tipo_reporte: 'completo',
    };

    this.service.exportarReporte(payload, 'xlsx').pipe(
      finalize(() => this.exportandoXLSX.set(false))
    ).subscribe({
      next: (blob: Blob) => {
        this._descargarArchivo(blob, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          `reporte_${new Date().getTime()}.xlsx`);
      },
      error: (err: any) => {
        console.error('Error exportando Excel:', err);
        this.errorExportacion.set('Error al exportar Excel. Inténtalo nuevamente.');
      },
    });
  }

  private _descargarArchivo(blob: Blob, tipo: string, nombre: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = nombre;
    link.click();
    window.URL.revokeObjectURL(url);
  }
}
