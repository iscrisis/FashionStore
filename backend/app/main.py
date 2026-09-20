from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.image_storage import UPLOADS_ROOT
from app.routers import health
from modules.P1_SucursalesYCatalogos.CU06_GestionarSucursales.router import (
    router_ciudades as cu06_ciudades_router,
    router_sucursales as cu06_sucursales_router,
)
from modules.P1_SucursalesYCatalogos.CU07_ConsultarSucursales.router import (
    router as cu07_sucursales_publico_router,
)
from modules.P1_SucursalesYCatalogos.CU08_GestionarProductos.router import (
    router as cu08_productos_router,
)
from modules.P1_SucursalesYCatalogos.CU11_ConsultarCatalogoPrendas.router import (
    router as cu11_catalogo_router,
)
from modules.P1_SucursalesYCatalogos.CU12_ConsultarDisponibilidadPorSucursal.router import (
    router as cu12_disponibilidad_router,
)
from modules.P1_SucursalesYCatalogos.CU09_GestionarCategoriasTallasColores.router import (
    router_categorias as cu09_categorias_router,
    router_colores as cu09_colores_router,
    router_tallas as cu09_tallas_router,
)
from modules.P1_SucursalesYCatalogos.CU10_GestionarTemporadasColecciones.router import (
    router_colecciones as cu10_colecciones_router,
    router_temporadas as cu10_temporadas_router,
)
from modules.P3_ProveedoresEInventario.CU13_GestionarProveedores.router import (
    router as gestion_proveedores_router,
    router_panel as panel_proveedor_router,
)
from modules.P3_ProveedoresEInventario.CU14_ConsultarInventario.router import (
    router_panel as cu14_inventario_router,
)
from modules.P3_ProveedoresEInventario.CU15_RegistrarRecepcionMercaderia.router import (
    router_panel as cu15_recepcion_mercaderia_router,
)
from modules.P3_ProveedoresEInventario.CU16_RegistrarMovimientosInventario.router import (
    router_panel as cu16_movimientos_inventario_router,
)
from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.router import router as cu01_iniciar_sesion_router
from modules.P2_UsuariosYAccesos.CU02_RegistrarCliente.router import router as cu02_registrar_cliente_router
from modules.P2_UsuariosYAccesos.CU03_RecuperarContrasena.router import (
    router as cu03_recuperar_contrasena_router,
)
from modules.P2_UsuariosYAccesos.CU04_ActualizarPerfil.router import (
    router as cu04_actualizar_perfil_router,
)
from modules.P2_UsuariosYAccesos.CU05_GestionarUsuariosRoles.router import (
    router as cu05_usuarios_roles_router,
)
from modules.P4_ReservasYAtencion.CU17_CrearReservaPrendas.router import (
    router as cu17_crear_reserva_router,
)
from modules.P4_ReservasYAtencion.CU19_CancelarReserva.router import (
    router as cu19_cancelar_reserva_router,
)
from modules.P4_ReservasYAtencion.CU20_AtenderReservaPrendas.router import (
    router as cu20_atender_reserva_router,
)
from modules.P5_ComprasVentasYPagos.CU21_UsarCarritoCompras.router import (
    router as cu21_carrito_router,
)
from modules.P5_ComprasVentasYPagos.CU22_RealizarCompraDigital.router import (
    router as cu22_compra_digital_router,
)
from modules.P5_ComprasVentasYPagos.CU23_ProcesarPagoElectronico.router import (
    router as cu23_pago_electronico_router,
)
from modules.P5_ComprasVentasYPagos.CU24_RegistrarVentaPresencial.router import (
    router as cu24_venta_presencial_router,
)
from modules.P5_ComprasVentasYPagos.CU25_ProcesarPagoPresencial.router import (
    router as cu25_pago_presencial_router,
)
from modules.P5_ComprasVentasYPagos.CU26_RegistrarDevolucionCambio.router import (
    router as cu26_devolucion_cambio_router,
)
from modules.P5_ComprasVentasYPagos.CU27_ConsultarHistorialCompras.router import (
    router as cu27_historial_compras_router,
)
from modules.P5_ComprasVentasYPagos.CU31_EmitirComprobanteVenta.router import (
    router as cu31_comprobante_venta_router,
)
from modules.P6_InnovacionYAnalisis.CU32_GestionarPromociones.router import (
    router as cu32_promociones_router,
)
from modules.P6_InnovacionYAnalisis.CU29_ObtenerRecomendacionesIA.router import (
    router as cu29_asistente_ia_router,
)
from modules.P6_InnovacionYAnalisis.CU30_ConsultarReportesIndicadores.router import (
    router as cu30_reportes_router,
)

app = FastAPI(
    title=settings.APP_NAME,
    description="API REST central de FashionStore. Consumida por el frontend web (Angular) "
    "y, en una etapa posterior, por la aplicación móvil (Flutter).",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(cu01_iniciar_sesion_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu02_registrar_cliente_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu03_recuperar_contrasena_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu04_actualizar_perfil_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu05_usuarios_roles_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu06_ciudades_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu06_sucursales_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu07_sucursales_publico_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu08_productos_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu11_catalogo_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu12_disponibilidad_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu09_categorias_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu09_tallas_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu09_colores_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu10_temporadas_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu10_colecciones_router, prefix=settings.API_V1_PREFIX)
app.include_router(gestion_proveedores_router, prefix=settings.API_V1_PREFIX)
app.include_router(panel_proveedor_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu14_inventario_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu15_recepcion_mercaderia_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu16_movimientos_inventario_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu17_crear_reserva_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu19_cancelar_reserva_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu20_atender_reserva_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu21_carrito_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu22_compra_digital_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu23_pago_electronico_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu24_venta_presencial_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu25_pago_presencial_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu26_devolucion_cambio_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu27_historial_compras_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu31_comprobante_venta_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu32_promociones_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu29_asistente_ia_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu30_reportes_router, prefix=settings.API_V1_PREFIX)

# Sirve las imágenes subidas por el Administrador (CU08/CU09) -- ver
# app/core/image_storage.py. Montado bajo API_V1_PREFIX para que Nginx, que ya
# reenvía "/api/" al backend, sirva estas URLs sin configuración adicional.
UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)
app.mount(f"{settings.API_V1_PREFIX}/media", StaticFiles(directory=str(UPLOADS_ROOT)), name="media")


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs": "/docs",
    }
