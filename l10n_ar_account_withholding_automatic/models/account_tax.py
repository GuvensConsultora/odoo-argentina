# -*- coding: utf-8 -*-
from odoo import models


class AccountTax(models.Model):
    _inherit = "account.tax"

    # Toda la lógica de retenciones Ganancias, partner_tax, escalas y
    # cálculo está en l10n_ar_account_withholding (módulo refactorizado).
    # Este módulo se mantiene instalado por dependencias pero no agrega
    # funcionalidad propia.
