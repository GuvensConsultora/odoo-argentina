##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'license': 'AGPL-3',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_tax_view.xml',
        'views/account_payment_view.xml',
        'data/account_payment_method_data.xml',
    ],
    'depends': [
        'account',
        # for payment method description and company_id field on form view
        'l10n_ar',
        # el dominio del impuesto de retención lee l10n_ar_withholding_payment_type,
        # que define este módulo de la localización. Se usa esa marca y no
        # type_tax_use porque son excluyentes entre sí, y así el mismo impuesto
        # sirve para este circuito y para el asistente nativo de registro de pagos.
        'l10n_ar_withholding',
    ],
    'installable': True,
    'name': 'Retenciones en pagos',
    'test': [],
    'version': '17.0.1.0.0',
}
