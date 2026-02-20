from odoo import fields, models, api
# from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_method_description = fields.Char(
        compute='_compute_payment_method_description',
        string='Payment Method',
    )

    def _compute_payment_method_description(self):
        for rec in self:
            rec.payment_method_description = rec.payment_method_line_id.display_name

    # nuevo campo funcion para definir dominio de los metodos
    payment_method_ids = fields.Many2many(
        'account.payment.method.line',
        compute='_compute_payment_methods',
        string='Available payment methods',
    )
    journal_ids = fields.Many2many(
        'account.journal',
        compute='_compute_journals'
    )
    destination_journal_ids = fields.Many2many(
        'account.journal',
        compute='_compute_destination_journals'
    )

    @api.depends(
        'journal_id',
    )
    def _compute_destination_journals(self):
        for rec in self:
            domain = [
                ('type', 'in', ('bank', 'cash')),
                # al final pensamos mejor no agregar esta restricción, por ej,
                # para poder transferir a tarjeta a pagar. Esto solo se usa
                # en transferencias
                # ('at_least_one_inbound', '=', True),
                ('company_id', '=', rec.journal_id.company_id.id),
                ('id', '!=', rec.journal_id.id),
            ]
            rec.destination_journal_ids = rec.journal_ids.search(domain)

    def get_journals_domain(self):
        """
        We get domain here so it can be inherited
        """
        self.ensure_one()
        domain = [('type', 'in', ('bank', 'cash'))]
        if self.payment_type == 'inbound':
            domain.append(('inbound_payment_method_line_ids', '!=', False))
        # Al final dejamos que para transferencias se pueda elegir
        # cualquier sin importar si tiene outbound o no
        # else:
        elif self.payment_type == 'outbound':
            domain.append(('outbound_payment_method_line_ids', '!=', False))
        return domain

    @api.depends(
        'payment_type',
    )
    def _compute_journals(self):
        for rec in self:
            rec.journal_ids = rec.journal_ids.search(rec.get_journals_domain())

    @api.depends(
        'journal_id.outbound_payment_method_line_ids',
        'journal_id.inbound_payment_method_line_ids',
        'payment_type',
    )
    def _compute_payment_methods(self):
        for rec in self:
            if rec.payment_type in ('outbound', 'transfer'):
                methods = rec.journal_id.outbound_payment_method_line_ids
            else:
                methods = rec.journal_id.inbound_payment_method_line_ids
            rec.payment_method_ids = methods

    @api.onchange('currency_id')
    def _onchange_currency(self):
        """ Anulamos metodo nativo que pisa el monto remanente que pasamos
        por contexto TODO ver si podemos re-incorporar esto y hasta extender
        _compute_payment_amount para que el monto se calcule bien aun usando
        el save and new"""
        return False

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        """
        Sobre escribimos y desactivamos la parte del dominio de la funcion
        original ya que se pierde si se vuelve a entrar
        """
        if not self.invoice_line_ids:
            # Set default partner type for the payment type
            if self.payment_type == 'inbound':
                self.partner_type = 'customer'
            elif self.payment_type == 'outbound':
                self.partner_type = 'supplier'
            else:
                self.partner_type = False
            # limpiamos journal ya que podria no estar disponible para la nueva
            # operacion y ademas para que se limpien los payment methods
            self.journal_id = False

    # @api.onchange('partner_type')
    def _onchange_partner_type(self):
        """
        Agregasmos dominio en vista ya que se pierde si se vuelve a entrar
        Anulamos funcion original porque no haria falta
        """
        return False

    def _onchange_amount(self):
        """
        Anulamos este onchange que termina cambiando el domain de journals
        y no es compatible con multicia y se pierde al guardar.
        TODO: ver que odoo con este onchange llama a
        _compute_journal_domain_and_types quien devolveria un journal generico
        cuando el importe sea cero, imagino que para hacer ajustes por
        diferencias de cambio
        """
        return True

    @api.depends('payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        """
        // Por qué: se usa with_company para que property fields resuelvan
        // la cuenta de la compañía correcta en entornos multi-compañía.
        // Patrón: iterar con rec (no self) para soportar multi-record compute.
        """
        res = super(AccountPayment, self)._compute_destination_account_id()
        for rec in self.filtered(lambda x: not x.is_internal_transfer):
            # Sin partner, dejamos el fallback que ya seteo el super() estándar
            if not rec.partner_id:
                continue
            partner = rec.partner_id.with_company(rec.company_id)
            if rec.partner_type == 'customer':
                rec.destination_account_id = (
                    partner.property_account_receivable_id)
            else:
                rec.destination_account_id = (
                    partner.property_account_payable_id)
        for rec in self.filtered(lambda x: x.is_internal_transfer):
            if rec.payment_type == 'outbound':
                rec.destination_account_id = rec.journal_id.company_id.transfer_account_id
        return res
