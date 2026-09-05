"""Gestión de Proveedores — Administrador General.

Administra los proveedores externos de FashionStore (razón social, contacto,
correo, teléfono, estado) mediante desactivación lógica. Proveedor NO es
Usuario: no tiene cuenta ni credenciales, y no se relaciona con la tabla
usuarios ni con el rol PROVEEDOR — ese vínculo y el panel propio del
Proveedor son un paso posterior y separado.

No administra todavía productos, precios, stock, órdenes de compra, facturas
ni asociaciones producto-proveedor: eso corresponde a CU08 y a pasos futuros.
"""
