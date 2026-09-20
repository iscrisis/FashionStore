"""Reglas de negocio de CU31 -- Emitir comprobante de venta (Cliente/Cajero).

Autorización -- NUNCA se confía en un id que Angular envíe, todo sale del
actor autenticado (JWT, ver router.py):
  - CLIENTE: solo puede consultar el comprobante de una Venta cuyo
    `cliente_id` sea el suyo.
  - CAJERO: solo puede consultar el comprobante de una Venta de SU sucursal
    (`actor.sucursal_id`), sin importar quién la vendió.
  - Cualquier otro rol: rechazado (la ruta ya restringe con require_roles,
    esto es una segunda defensa).
Ambos casos usan el MISMO mensaje/error genérico (VentaNoEncontradaError) --
no revela si esa Venta existe a nombre de otro Cliente o de otra sucursal.

Solo existe comprobante para una Venta PAGADA -- PENDIENTE_PAGO (CU22/CU24
todavía sin confirmar) se rechaza explícitamente. `Venta.estado` no tiene hoy
ningún valor "CANCELADA" (ver Models/venta.py: el enum solo define
PENDIENTE_PAGO/PAGADA) -- por eso ese caso queda cubierto por el mismo
chequeo `!= PAGADA`, sin inventar un estado que CU22/23/24/25 no producen.

obtener_comprobante() es la única función que arma el DTO completo -- tanto
generar_pdf() como enviar_comprobante() la reutilizan en vez de duplicar el
ensamblado (nunca un segundo camino que pueda desincronizarse del primero).

enviar_comprobante() -- "Pago aprobado = Venta completada": el correo es una
notificación posterior, best-effort. Si el SMTP falla (o el Cliente no tiene
un correo válido, o la Venta no tiene ningún Cliente asociado -- venta
presencial directa de mostrador), NUNCA se lanza un error que tumbe la
petición: se responde igual (200) con `enviado=False` y un mensaje amigable,
nunca el detalle técnico.
"""

from app.integrations.mailer import EnvioCorreoError, enviar_correo
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta, Venta

from .pdf import construir_pdf_comprobante
from .repository import PagoRepository, ProductoLecturaRepository, UsuarioLecturaRepository, VentaRepository
from .schemas import (
    ClienteComprobanteOut,
    ColorResumen,
    ComprobanteVentaOut,
    DetalleComprobanteOut,
    EnviarComprobanteOut,
    ProductoResumen,
    SucursalComprobanteOut,
    TallaResumen,
    VarianteResumen,
)


class VentaNoEncontradaError(Exception):
    """No existe, o no pertenece al Cliente/sucursal del actor autenticado
    (mismo mensaje: no revela la existencia de ventas ajenas)."""


class VentaSinComprobanteError(Exception):
    """La Venta no está PAGADA -- no hay comprobante que emitir todavía
    (PENDIENTE_PAGO) o nunca lo habrá (cualquier estado que no sea PAGADA)."""


class PagoNoEncontradoError(Exception):
    """Defensivo -- una Venta PAGADA siempre debería tener un Pago PAGADO
    (CU23/CU25 lo crean en la misma transacción que marcan la Venta)."""


class ClienteSinCorreoError(Exception):
    """enviar_comprobante(): la Venta no tiene Cliente asociado (venta
    presencial directa de mostrador, CU24) -- no hay a quién enviarle nada."""


class ComprobanteVentaService:
    def __init__(self, db):
        self._ventas = VentaRepository(db)
        self._pagos = PagoRepository(db)
        self._productos = ProductoLecturaRepository(db)
        self._usuarios = UsuarioLecturaRepository(db)

    @staticmethod
    def _autorizar(actor: Usuario, venta: Venta) -> None:
        if actor.rol == RolUsuario.CLIENTE:
            if venta.cliente_id != actor.id:
                raise VentaNoEncontradaError
            return
        if actor.rol == RolUsuario.CAJERO:
            if actor.sucursal_id is None or venta.sucursal_id != actor.sucursal_id:
                raise VentaNoEncontradaError
            return
        raise VentaNoEncontradaError

    def obtener_comprobante(self, actor: Usuario, venta_id: int) -> ComprobanteVentaOut:
        venta = self._ventas.obtener_por_id(venta_id)
        if venta is None:
            raise VentaNoEncontradaError
        self._autorizar(actor, venta)
        if venta.estado != EstadoVenta.PAGADA:
            raise VentaSinComprobanteError

        pago = self._pagos.obtener_pagado_por_venta(venta.id)
        if pago is None:
            raise PagoNoEncontradoError

        producto_ids = {d.producto_variante.producto_id for d in venta.detalles}
        productos = self._productos.get_by_ids(producto_ids)

        detalles_out: list[DetalleComprobanteOut] = []
        for detalle in venta.detalles:
            variante = detalle.producto_variante
            producto = productos.get(variante.producto_id)
            if producto is None:
                continue
            detalles_out.append(
                DetalleComprobanteOut(
                    producto=ProductoResumen(
                        id=producto.id, nombre=producto.nombre, imagen_principal_url=producto.imagen_principal_url
                    ),
                    variante=VarianteResumen(
                        id=variante.id,
                        talla=TallaResumen.model_validate(variante.talla),
                        color=ColorResumen.model_validate(variante.color),
                    ),
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    subtotal=detalle.subtotal,
                )
            )

        cliente_out = None
        if venta.cliente_id is not None:
            cliente = self._usuarios.get_by_id(venta.cliente_id)
            if cliente is not None:
                cliente_out = ClienteComprobanteOut(nombre=cliente.nombre, correo=cliente.correo)

        return ComprobanteVentaOut(
            venta_id=venta.id,
            codigo_venta=venta.codigo_venta,
            fecha_creacion=venta.fecha_creacion,
            tipo=venta.tipo.value,
            sucursal=SucursalComprobanteOut(
                id=venta.sucursal.id,
                nombre=venta.sucursal.nombre,
                direccion=venta.sucursal.direccion,
                ciudad=venta.sucursal.ciudad.nombre,
            ),
            cliente=cliente_out,
            detalles=detalles_out,
            total=venta.total,
            metodo_pago=pago.proveedor.value,
            estado=venta.estado.value,
            estado_pago=pago.estado.value,
        )

    def generar_pdf(self, actor: Usuario, venta_id: int) -> tuple[str, bytes]:
        comprobante = self.obtener_comprobante(actor, venta_id)
        return comprobante.codigo_venta, construir_pdf_comprobante(comprobante)

    def enviar_comprobante(self, actor: Usuario, venta_id: int) -> EnviarComprobanteOut:
        comprobante = self.obtener_comprobante(actor, venta_id)
        if comprobante.cliente is None:
            raise ClienteSinCorreoError

        pdf_bytes = construir_pdf_comprobante(comprobante)
        asunto = f"Comprobante de compra FashionStore {comprobante.codigo_venta}"
        cuerpo_texto, cuerpo_html = _armar_cuerpo_correo(comprobante)

        try:
            enviar_correo(
                comprobante.cliente.correo,
                asunto,
                cuerpo_html,
                cuerpo_texto,
                adjuntos=[(f"{comprobante.codigo_venta}.pdf", pdf_bytes, "application", "pdf")],
            )
        except EnvioCorreoError:
            return EnviarComprobanteOut(
                enviado=False,
                mensaje="No se pudo enviar el comprobante por correo. Inténtalo nuevamente más tarde.",
            )

        return EnviarComprobanteOut(enviado=True, mensaje="Comprobante enviado correctamente.")


def _armar_cuerpo_correo(comprobante: ComprobanteVentaOut) -> tuple[str, str]:
    tipo_legible = "Digital" if comprobante.tipo == "DIGITAL" else "Presencial"
    nombre_cliente = comprobante.cliente.nombre if comprobante.cliente is not None else "Cliente"
    fecha_legible = comprobante.fecha_creacion.strftime("%d/%m/%Y %H:%M")

    lineas_productos_texto = "\n".join(
        f"  - {d.producto.nombre} ({d.variante.color.nombre} / {d.variante.talla.nombre}) "
        f"x{d.cantidad} -- Bs {d.subtotal:.2f}"
        for d in comprobante.detalles
    )
    cuerpo_texto = (
        f"Hola {nombre_cliente},\n\n"
        f"Gracias por tu compra en FashionStore. Este es el comprobante de tu venta {comprobante.codigo_venta}.\n\n"
        f"Fecha: {fecha_legible}\n"
        f"Sucursal: {comprobante.sucursal.nombre} ({comprobante.sucursal.ciudad})\n"
        f"Método de pago: {comprobante.metodo_pago}\n\n"
        f"Productos:\n{lineas_productos_texto}\n\n"
        f"Total: Bs {comprobante.total:.2f}\n\n"
        "Adjuntamos el comprobante en PDF a este correo."
    )

    filas_productos_html = "".join(
        f"""<tr>
          <td style="padding:6px 8px; border-bottom:1px solid #e8e8e8;">{d.producto.nombre}</td>
          <td style="padding:6px 8px; border-bottom:1px solid #e8e8e8;">{d.variante.color.nombre} / {d.variante.talla.nombre}</td>
          <td style="padding:6px 8px; border-bottom:1px solid #e8e8e8; text-align:center;">{d.cantidad}</td>
          <td style="padding:6px 8px; border-bottom:1px solid #e8e8e8; text-align:right;">Bs {d.subtotal:.2f}</td>
        </tr>"""
        for d in comprobante.detalles
    )
    cuerpo_html = f"""\
<div style="font-family: Arial, Helvetica, sans-serif; color: #191919; max-width: 520px; margin: 0 auto;">
  <h2 style="color: #a90012; margin-bottom: 4px;">FashionStore</h2>
  <p>Hola {nombre_cliente},</p>
  <p>Gracias por tu compra. Este es el comprobante de tu venta <strong>{comprobante.codigo_venta}</strong>.</p>
  <p style="color:#666666; font-size:13px; margin: 4px 0 16px;">
    Fecha: {fecha_legible} &middot; Sucursal: {comprobante.sucursal.nombre} ({comprobante.sucursal.ciudad})
    &middot; Tipo: {tipo_legible} &middot; Método de pago: {comprobante.metodo_pago}
  </p>
  <table style="width:100%; border-collapse:collapse; font-size:13px;">
    <thead>
      <tr style="background:#f7f7f7;">
        <th style="padding:6px 8px; text-align:left;">Producto</th>
        <th style="padding:6px 8px; text-align:left;">Color / Talla</th>
        <th style="padding:6px 8px; text-align:center;">Cant.</th>
        <th style="padding:6px 8px; text-align:right;">Subtotal</th>
      </tr>
    </thead>
    <tbody>
      {filas_productos_html}
    </tbody>
  </table>
  <p style="text-align:right; font-size:16px; font-weight:bold; color:#a90012; margin-top:14px;">
    Total: Bs {comprobante.total:.2f}
  </p>
  <p style="color:#666666; font-size:12px;">Adjuntamos el comprobante en PDF a este correo.</p>
</div>
"""
    return cuerpo_texto, cuerpo_html
