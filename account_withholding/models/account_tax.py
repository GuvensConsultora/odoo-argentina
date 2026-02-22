from odoo import models, fields, api


class AccountTax(models.Model):
    """
    We could also use inherits but we should create methods of chart template
    """
    _inherit = "account.tax"

    # Por qué: selection_add en vez de redefinir — evita warning en v19
    type_tax_use = fields.Selection(
            selection_add=[
                ('customer', 'Pagos a Clientes'),
                ('supplier', 'Pagos a Proveedores'),
            ],
            ondelete={'customer': 'set default', 'supplier': 'set default'},
    )
    amount = fields.Float(
        default=0.0,
    )
    withholding_sequence_id = fields.Many2one(
        'ir.sequence',
        'Secuencia de impuestos',
        copy=False
    )

    @api.model
    def create(self, vals):
        tax = super(AccountTax, self).create(vals)
        if tax.type_tax_use == 'supplier' and not tax.withholding_sequence_id:
            tax.withholding_sequence_id = self.withholding_sequence_id.\
                sudo().create({
                    'name': tax.name,
                    'implementation': 'no_gap',
                    # 'prefix': False,
                    'padding': 8,
                    'number_increment': 1,
                    'code': 'tax.name',
                    'company_id': tax.company_id.id,
                }).id
        return tax
