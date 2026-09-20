"""Generación del PDF simple de CU31 -- Emitir comprobante de venta.

Layout mínimo (cabecera + tabla de prendas + total), con `fpdf2` -- una
librería pura Python, sin dependencias nativas, agregada específicamente
para este requerimiento ("si existe generación PDF simple: adjuntar PDF").
No pertenece a ningún otro CU: vive dentro de este módulo, no en
app/integrations, porque el layout (qué columnas, qué orden, qué texto) es
una decisión propia del comprobante de CU31, no una integración genérica
reutilizable como Stripe o SMTP.

Los core fonts de fpdf2 (Helvetica) solo soportan Latin-1 -- de sobra para
español (á, é, í, ó, ú, ñ, Ñ ya están en ese charset), pero `_seguro()`
igual sanea cualquier carácter fuera de rango (ej. un producto cargado con un
emoji en el nombre) en vez de dejar que la generación del PDF reviente por
eso.
"""

from fpdf import FPDF

from .schemas import ComprobanteVentaOut

_ROJO_FASHIONSTORE = (169, 0, 18)
_GRIS_TEXTO_SECUNDARIO = (102, 102, 102)
_GRIS_CLARO = (247, 247, 247)
_TEXTO = (25, 25, 25)

_ANCHOS_COLUMNAS = (70, 40, 18, 26, 26)
_ENCABEZADOS = ("Producto", "Color / Talla", "Cant.", "P. Unit.", "Subtotal")


def _seguro(texto: str) -> str:
    return texto.encode("latin-1", "replace").decode("latin-1")


def construir_pdf_comprobante(comprobante: ComprobanteVentaOut) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*_ROJO_FASHIONSTORE)
    pdf.cell(0, 12, "FashionStore", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_GRIS_TEXTO_SECUNDARIO)
    pdf.cell(0, 6, "Comprobante interno de compra -- no es factura fiscal", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_text_color(*_TEXTO)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 7, f"Venta {comprobante.codigo_venta}", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    tipo_legible = "Digital" if comprobante.tipo == "DIGITAL" else "Presencial"
    filas_info = [
        f"Fecha: {comprobante.fecha_creacion.strftime('%d/%m/%Y %H:%M')}",
        f"Sucursal: {_seguro(comprobante.sucursal.nombre)} ({_seguro(comprobante.sucursal.ciudad)})",
        f"Tipo de venta: {tipo_legible}",
    ]
    if comprobante.cliente is not None:
        filas_info.append(f"Cliente: {_seguro(comprobante.cliente.nombre)}")
    filas_info.append(f"Metodo de pago: {_seguro(comprobante.metodo_pago)}")
    filas_info.append("Estado: PAGADO")
    for fila in filas_info:
        pdf.cell(0, 6, fila, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*_GRIS_CLARO)
    for ancho, encabezado in zip(_ANCHOS_COLUMNAS, _ENCABEZADOS):
        pdf.cell(ancho, 8, encabezado, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for detalle in comprobante.detalles:
        variante = f"{_seguro(detalle.variante.color.nombre)} / {_seguro(detalle.variante.talla.nombre)}"
        pdf.cell(_ANCHOS_COLUMNAS[0], 7, _seguro(detalle.producto.nombre), border=1)
        pdf.cell(_ANCHOS_COLUMNAS[1], 7, variante, border=1)
        pdf.cell(_ANCHOS_COLUMNAS[2], 7, str(detalle.cantidad), border=1, align="C")
        pdf.cell(_ANCHOS_COLUMNAS[3], 7, f"Bs {detalle.precio_unitario:.2f}", border=1, align="R")
        pdf.cell(_ANCHOS_COLUMNAS[4], 7, f"Bs {detalle.subtotal:.2f}", border=1, align="R")
        pdf.ln()

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*_ROJO_FASHIONSTORE)
    pdf.cell(0, 8, f"Total: Bs {comprobante.total:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
