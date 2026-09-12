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
from modules.P1_SucursalesYCatalogos.CU09_GestionarCategoriasTallasColores.router import (
    router_categorias as cu09_categorias_router,
    router_colores as cu09_colores_router,
    router_tallas as cu09_tallas_router,
)
from modules.P1_SucursalesYCatalogos.CU10_GestionarTemporadasColecciones.router import (
    router_colecciones as cu10_colecciones_router,
    router_temporadas as cu10_temporadas_router,
)
from modules.P1_SucursalesYCatalogos.GestionProveedores.router import (
    router as gestion_proveedores_router,
    router_panel as panel_proveedor_router,
)
from modules.P2_UsuariosYAccesos.CU01_IniciarSesion.router import router as cu01_iniciar_sesion_router
from modules.P2_UsuariosYAccesos.CU03_RecuperarContrasena.router import (
    router as cu03_recuperar_contrasena_router,
)
from modules.P2_UsuariosYAccesos.CU04_ActualizarPerfil.router import (
    router as cu04_actualizar_perfil_router,
)
from modules.P2_UsuariosYAccesos.CU05_GestionarUsuariosRoles.router import (
    router as cu05_usuarios_roles_router,
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
app.include_router(cu03_recuperar_contrasena_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu04_actualizar_perfil_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu05_usuarios_roles_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu06_ciudades_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu06_sucursales_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu07_sucursales_publico_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu08_productos_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu11_catalogo_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu09_categorias_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu09_tallas_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu09_colores_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu10_temporadas_router, prefix=settings.API_V1_PREFIX)
app.include_router(cu10_colecciones_router, prefix=settings.API_V1_PREFIX)
app.include_router(gestion_proveedores_router, prefix=settings.API_V1_PREFIX)
app.include_router(panel_proveedor_router, prefix=settings.API_V1_PREFIX)

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
