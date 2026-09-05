"""Endpoints de CU05 — Gestionar usuarios y roles.

Todos requieren un ADMINISTRADOR autenticado (única autoridad de alcance global
definida hoy en el sistema). La autorización se valida en FastAPI, no solo en
el frontend.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import (
    ROLES_INTERNOS,
    CambiarEstadoRequest,
    CambiarRolRequest,
    RolDisponible,
    UsuarioActualizar,
    UsuarioAdminView,
    UsuarioCrear,
)
from .service import (
    CorreoDuplicadoError,
    OperacionNoPermitidaError,
    ProveedorNoEncontradoError,
    ProveedorYaVinculadoError,
    RolNoAsignableError,
    SucursalNoEncontradaError,
    UsuarioNoEncontradoError,
    UsuariosRolesService,
)

router = APIRouter(prefix="/usuarios", tags=["CU05 - Gestionar usuarios y roles"])

_ETIQUETAS_ROL = {
    RolUsuario.ADMINISTRADOR: "Administrador general",
    RolUsuario.ENCARGADO_SUCURSAL: "Encargado de sucursal",
    RolUsuario.CAJERO: "Cajero",
    RolUsuario.PROVEEDOR: "Proveedor",
    RolUsuario.CLIENTE: "Cliente",
}

require_admin = require_roles(RolUsuario.ADMINISTRADOR)


@router.get("/roles", response_model=list[RolDisponible])
def listar_roles_asignables(_: Usuario = Depends(require_admin)) -> list[RolDisponible]:
    return [RolDisponible(valor=rol, etiqueta=_ETIQUETAS_ROL[rol]) for rol in ROLES_INTERNOS]


@router.get("", response_model=list[UsuarioAdminView])
def listar_usuarios(
    search: str | None = Query(default=None),
    rol: RolUsuario | None = Query(default=None),
    estado: str | None = Query(default=None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[Usuario]:
    is_active = {"active": True, "inactive": False}.get(estado)
    return UsuariosRolesService(db).listar(search=search, rol=rol, is_active=is_active)


@router.get("/{usuario_id}", response_model=UsuarioAdminView)
def obtener_usuario(
    usuario_id: int, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> Usuario:
    try:
        return UsuariosRolesService(db).obtener(usuario_id)
    except UsuarioNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.") from exc


@router.post("", response_model=UsuarioAdminView, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    payload: UsuarioCrear, db: Session = Depends(get_db), _: Usuario = Depends(require_admin)
) -> Usuario:
    try:
        return UsuariosRolesService(db).crear(payload)
    except RolNoAsignableError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Rol no asignable desde este módulo.",
        ) from exc
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La sucursal indicada no existe.") from exc
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El proveedor indicado no existe.") from exc
    except ProveedorYaVinculadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ese proveedor ya tiene una cuenta de acceso vinculada."
        ) from exc
    except CorreoDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un usuario con ese correo.") from exc


@router.put("/{usuario_id}", response_model=UsuarioAdminView)
def actualizar_usuario(
    usuario_id: int,
    payload: UsuarioActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> Usuario:
    try:
        return UsuariosRolesService(db).actualizar_datos(usuario_id, payload)
    except UsuarioNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.") from exc
    except SucursalNoEncontradaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La sucursal indicada no existe.") from exc
    except ProveedorNoEncontradoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El proveedor indicado no existe.") from exc
    except ProveedorYaVinculadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ese proveedor ya tiene una cuenta de acceso vinculada."
        ) from exc
    except CorreoDuplicadoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un usuario con ese correo.") from exc


@router.patch("/{usuario_id}/rol", response_model=UsuarioAdminView)
def cambiar_rol(
    usuario_id: int,
    payload: CambiarRolRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_admin),
) -> Usuario:
    try:
        return UsuariosRolesService(db).cambiar_rol(usuario_id, payload.rol, actor)
    except UsuarioNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.") from exc
    except RolNoAsignableError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Rol no asignable desde este módulo.",
        ) from exc


@router.patch("/{usuario_id}/estado", response_model=UsuarioAdminView)
def cambiar_estado(
    usuario_id: int,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(require_admin),
) -> Usuario:
    try:
        return UsuariosRolesService(db).cambiar_estado(usuario_id, payload.is_active, actor)
    except UsuarioNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.") from exc
    except OperacionNoPermitidaError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No puedes desactivar tu propia cuenta.",
        ) from exc
