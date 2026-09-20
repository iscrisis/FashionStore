import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { ComprobanteService } from '../../comprobantes/comprobante.service';
import { PagoElectronicoService } from '../pago-electronico.service';
import { VentaPagadaOut } from '../pago-electronico.model';

type Estado = 'verificando' | 'pagado' | 'no-completado';

/**
 * CU23 -- Procesar pago electrónico (Cliente). Pantalla de retorno desde
 * Stripe ('/pago/resultado', CLIENTE autenticado -- ver app.routes.ts):
 * tanto `success_url` como `cancel_url` de la Checkout Session (ver
 * CU23_ProcesarPagoElectronico/router.py) apuntan aquí.
 *
 * Angular NUNCA decide que el pago se completó -- este componente solo
 * interpreta la URL de dos formas posibles:
 *  - `?cancelado=1` (cancel_url): el Cliente cerró/canceló Stripe Checkout
 *    -- se muestra el mensaje amigable pedido, sin llamar al backend (no
 *    hay session_id que verificar).
 *  - `?session_id=...` (success_url, Stripe reemplaza {CHECKOUT_SESSION_ID}
 *    por el id real): se llama a POST /pagos/verificar con ESE session_id.
 *    Recién si FastAPI confirma el pago contra Stripe (ver
 *    CU23_ProcesarPagoElectronico/service.py) se muestra "COMPRA REALIZADA".
 *    Si el backend responde que no se completó (cancelado/fallido/todavía
 *    abierto), se muestra el MISMO mensaje amigable que el caso cancelado,
 *    nunca el detalle técnico de Stripe.
 *
 * Idempotente por diseño: un F5 en esta misma pantalla vuelve a llamar a
 * /pagos/verificar con el mismo session_id, pero el backend ya lo tiene
 * PAGADO y responde exactamente lo mismo sin volver a descontar stock ni
 * borrar el carrito otra vez (ver service.py).
 *
 * CU31 -- Emitir comprobante de venta: apenas se confirma el pago, dispara
 * en segundo plano POST /comprobantes/{id}/enviar (fire-and-forget, sin
 * mostrar ningún error si falla -- "pago aprobado = venta completada", el
 * correo es solo una notificación posterior, ver
 * CU31_EmitirComprobanteVenta/service.py) y ofrece "Ver comprobante" para
 * consultarlo en el momento -- CU23 en sí no se modifica, esto solo se
 * agrega sobre la misma pantalla de resultado.
 */
@Component({
  selector: 'app-resultado-pago',
  imports: [Icon, RouterLink],
  templateUrl: './resultado-pago.html',
  styleUrl: './resultado-pago.scss',
})
export class ResultadoPago implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(PagoElectronicoService);
  private readonly comprobanteService = inject(ComprobanteService);

  protected readonly estado = signal<Estado>('verificando');
  protected readonly venta = signal<VentaPagadaOut | null>(null);
  protected readonly ventaId = signal<number | null>(null);

  ngOnInit(): void {
    const params = this.route.snapshot.queryParamMap;
    const ventaIdParam = params.get('venta_id');
    this.ventaId.set(ventaIdParam ? Number(ventaIdParam) : null);

    if (params.get('cancelado') === '1') {
      this.estado.set('no-completado');
      return;
    }

    const sessionId = params.get('session_id');
    if (!sessionId) {
      this.estado.set('no-completado');
      return;
    }

    this.service.verificarPago({ session_id: sessionId }).subscribe({
      next: (venta) => {
        this.venta.set(venta);
        this.estado.set('pagado');
        // Fire-and-forget: un correo que falle nunca debe verse como un
        // error de la compra, que ya quedó completada (ver docstring).
        this.comprobanteService.enviar(venta.id).subscribe({ error: () => undefined });
      },
      error: () => {
        // Nunca se muestra el detalle técnico del backend/Stripe aquí --
        // solo el mensaje amigable pedido ("El pago no fue completado.").
        this.estado.set('no-completado');
      },
    });
  }
}
