##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Los métodos de pago que crea este módulo (data/account_payment_method_data.xml)
# usan los códigos withholding_customers / withholding_suppliers. El código
# histórico preguntaba por 'withholding' a secas, que no existe: la condición
# nunca se cumplía y la lógica de retención quedaba muerta.
WITHHOLDING_CODES = ('withholding', 'withholding_customers', 'withholding_suppliers')


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # Estos tres campos llevaban readonly=True + states={'draft': ...} hasta la v13.
    # El atributo states se eliminó en versiones posteriores y quedaron de sólo
    # lectura para siempre, sin forma de cargarlos desde la interfaz. La vista es
    # la que ahora controla cuándo se pueden editar.
    tax_withholding_id = fields.Many2one(
        'account.tax',
        string='Impuesto de retencion',
    )
    withholding_number = fields.Char(
        help="If you don't set a number we will add a number automatically "
        "from a sequence that should be configured on the Withholding Tax"
    )
    withholding_base_amount = fields.Monetary(
        string='Monto base de retencion',
    )
    communication = fields.Text('Notas')

    def _is_withholding(self):
        self.ensure_one()
        return self.payment_method_code in WITHHOLDING_CODES

    def _get_withholding_repartition_line(self):
        """Línea de distribución del impuesto de retención.

        Hasta la v13 el impuesto tenía account_id y refund_account_id
        directamente. Esos campos ya no existen: la cuenta vive en las líneas de
        distribución, y la que corresponde es la de tipo 'tax'. Se usa la de
        factura cuando la retención acompaña el sentido natural de la operación
        (cobro de cliente / pago a proveedor) y la de devolución en el inverso.
        """
        self.ensure_one()
        tax = self.tax_withholding_id
        if ((self.partner_type == 'customer' and self.payment_type == 'inbound') or
                (self.partner_type == 'supplier' and self.payment_type == 'outbound')):
            lines = tax.invoice_repartition_line_ids
        else:
            lines = tax.refund_repartition_line_ids
        return lines.filtered(lambda r: r.repartition_type == 'tax')[:1]

    def action_post(self):
        """Completa el número de retención desde la secuencia del impuesto.

        Portado de post(), que no existe desde la v14.
        """
        without_number = self.filtered(
            lambda x: x.tax_withholding_id and not x.withholding_number)

        without_sequence = without_number.filtered(
            lambda x: not x.tax_withholding_id.withholding_sequence_id)
        if without_sequence:
            raise UserError(_(
                'No puede validar pagos con retenciones que no tengan número '
                'de retención. Recomendamos agregar una secuencia a los '
                'impuestos de retención correspondientes. Id de pagos: %s') % (
                without_sequence.ids))

        # a los que tienen secuencia les setamos el numero desde secuencia
        for payment in (without_number - without_sequence):
            payment.withholding_number = \
                payment.tax_withholding_id.withholding_sequence_id.next_by_id()

        return super().action_post()

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        """Redirige la línea de liquidez a la cuenta del impuesto de retención.

        Portado de _get_liquidity_move_line_vals(), que no existe desde la v14:
        el core arma ahora todas las líneas del pago en este método y la de
        liquidez es la primera de la lista.

        En un pago de retención no hay movimiento real de fondos: lo que el
        cliente no entregó se reconoce como crédito fiscal. Por eso la línea que
        iría a la caja o al banco se redirige a la cuenta del impuesto y se le
        agrega la línea de distribución del impuesto, que es lo que la hace
        visible en los informes de impuestos.
        """
        vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals, force_balance=force_balance)

        if not self._is_withholding() or not self.tax_withholding_id:
            return vals_list

        if self.is_internal_transfer:
            raise UserError(_('No se pueden usar retenciones en transferencias internas.'))

        repartition_line = self._get_withholding_repartition_line()
        liquidity_vals = vals_list[0]
        liquidity_vals['name'] = self.withholding_number or '/'
        if repartition_line and repartition_line.account_id:
            liquidity_vals['account_id'] = repartition_line.account_id.id
        # NO se escribe tax_repartition_line_id a propósito. l10n_ar_withholding
        # (localización de Odoo) borra en _synchronize_to_moves toda línea cuyo
        # tax_line_id tenga marca de retención —su propio comentario dice "as the
        # synchronization mechanism is not implemented yet"—. Al vincular la línea
        # de distribución, la línea se creaba y ese código la eliminaba enseguida,
        # dejando el asiento desbalanceado y una línea de compensación en la cuenta
        # transitoria. Sin ese vínculo la línea sobrevive y el importe queda en la
        # cuenta de retención, que es lo que importa para el crédito fiscal.
        return vals_list

    def _compute_payment_method_description(self):
        payments = self.filtered(lambda x: x.payment_method_code in WITHHOLDING_CODES)
        for rec in payments:
            name = rec.tax_withholding_id.name or rec.payment_method_id.name
            rec.payment_method_description = name
        return super(
            AccountPayment,
            (self - payments))._compute_payment_method_description()
