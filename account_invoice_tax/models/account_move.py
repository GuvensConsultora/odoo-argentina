##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):

    _inherit = "account.move"


    def _compute_tax_totals(self):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        # Por qué: El override original pasaba tax_total_origin=move._origin.tax_totals
        #          en contexto, lo que causa: (1) recursión en el compute, (2) el método
        #          _prepare_tax_totals retorna un dict sin las keys Enterprise
        #          (amount_company_currency, etc.), crasheando el template de factura.
        # Tip: Dejamos que el compute nativo de Odoo 19 Enterprise genere el dict
        #       completo sin interferencia de contexto.
        return super()._compute_tax_totals()
