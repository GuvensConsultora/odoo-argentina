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

    def _get_withholding_account(self):
        """Cuenta contable donde impacta la retención.

        Se usa la cuenta del impuesto cuando la retención acompaña el sentido
        natural de la operación (cobro de cliente / pago a proveedor) y la de
        devolución en el caso inverso.
        """
        self.ensure_one()
        if ((self.partner_type == 'customer' and self.payment_type == 'inbound') or
                (self.partner_type == 'supplier' and self.payment_type == 'outbound')):
            return self.tax_withholding_id.account_id
        return self.tax_withholding_id.refund_account_id

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
        agrega el vínculo con el impuesto, que es lo que la hace visible en los
        informes de impuestos.
        """
        vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals, force_balance=force_balance)

        if not self._is_withholding() or not self.tax_withholding_id:
            return vals_list

        if self.is_internal_transfer:
            raise UserError(_('No se pueden usar retenciones en transferencias internas.'))

        account = self._get_withholding_account()
        liquidity_vals = vals_list[0]
        if account:
            liquidity_vals['account_id'] = account.id
        liquidity_vals['name'] = self.withholding_number or '/'
        liquidity_vals['tax_line_id'] = self.tax_withholding_id.id
        return vals_list

    def _compute_payment_method_description(self):
        payments = self.filtered(lambda x: x.payment_method_code in WITHHOLDING_CODES)
        for rec in payments:
            name = rec.tax_withholding_id.name or rec.payment_method_id.name
            rec.payment_method_description = name
        return super(
            AccountPayment,
            (self - payments))._compute_payment_method_description()
