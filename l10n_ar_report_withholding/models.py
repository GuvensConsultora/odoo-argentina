# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Por qué: campo computed para mostrar/ocultar botón "Imprimir Retención"
    # Solo visible si el pago está confirmado y tiene impuesto de retención asignado
    print_withholding = fields.Boolean(
        'print_withholding',
        compute='_compute_print_withholding',
    )

    def _compute_print_withholding(self):
        for rec in self:
            rec.print_withholding = (
                rec.state == 'posted' and bool(rec.tax_withholding_id)
            )

    def btn_print_withholding(self):
        self.ensure_one()
        return self.env.ref(
            'l10n_ar_report_withholding.action_payment_withholdings'
        ).report_action(self)

    # =====================================================================
    # Helpers para template QWeb del certificado de retención
    # =====================================================================

    def is_ganancias_withholding(self):
        """True si la retención es de tipo Ganancias (tabla_ganancias)."""
        # Por qué: el template muestra secciones condicionales según tipo
        self.ensure_one()
        return self.tax_withholding_id.withholding_type == 'tabla_ganancias'

    def get_withholding_type_label(self):
        """Devuelve etiqueta legible del tipo de impuesto retenido."""
        # Por qué: el encabezado del certificado necesita "Impuesto a las Ganancias"
        # o "Impuesto al Valor Agregado" según corresponda
        self.ensure_one()
        tax = self.tax_withholding_id
        if tax.withholding_type == 'tabla_ganancias':
            return 'Impuesto a las Ganancias'
        # Patrón: detección por nombre del impuesto para IVA
        if tax.name and 'iva' in tax.name.lower():
            return 'Impuesto al Valor Agregado'
        return tax.name or 'Retención'

    def get_withholding_norma(self):
        """Devuelve la norma legal aplicable según tipo de retención."""
        # Por qué: el certificado debe citar la normativa vigente
        self.ensure_one()
        if self.is_ganancias_withholding():
            return 'RG 830/2000 AFIP y sus modificatorias'
        tax = self.tax_withholding_id
        if tax.name and 'iva' in tax.name.lower():
            return 'RG 2854/2010 AFIP y sus modificatorias'
        return ''

    def get_withholding_alicuota(self):
        """Devuelve la alícuota aplicada (%) como float.

        - Ganancias con escala (porcentaje_inscripto == -1): calcula desde
          amount / base * 100
        - Ganancias con porcentaje fijo: usa porcentaje del régimen
        - Otros: calcula desde amount / base * 100
        """
        # Por qué: no hay un campo que almacene la alícuota efectiva usada,
        # hay que derivarla del régimen o calcularla inversamente
        self.ensure_one()
        if self.is_ganancias_withholding():
            pg = self.payment_group_id
            regimen = pg.regimen_ganancias_id if pg else False
            if regimen:
                partner = self.partner_id.commercial_partner_id
                # AC con porcentaje fijo (no escala)
                if (partner.imp_ganancias_padron == 'AC'
                        and regimen.porcentaje_inscripto >= 0):
                    return regimen.porcentaje_inscripto
                # NI: porcentaje fijo del régimen
                if partner.imp_ganancias_padron == 'NI':
                    return regimen.porcentaje_no_inscripto
        # Fallback: cálculo inverso desde montos.
        # withholdable_base_amount lo completa el motor de retenciones
        # automáticas; en una carga manual queda en cero y la alícuota salía 0%.
        # Se usa entonces la base que cargó el operador.
        base = self.withholdable_base_amount or self.withholding_base_amount
        if base:
            return round(abs(self.amount) / abs(base) * 100, 2)
        return 0.0

    def get_withholding_invoices(self):
        """Devuelve las facturas/NC asociadas al pago vía payment_group.

        Usa matched_move_line_ids del payment_group (conciliaciones reales)
        en vez del campo roto reconciled_invoice_ids.
        """
        # Por qué: reconciled_invoice_ids no existe en Odoo 17;
        # matched_move_line_ids viene de account_payment_group y refleja
        # las líneas efectivamente conciliadas con los pagos del grupo
        self.ensure_one()
        pg = self.payment_group_id
        if not pg:
            return self.env['account.move']
        # matched_move_line_ids son account.move.line → extraemos los moves
        moves = pg.matched_move_line_ids.mapped('move_id')
        # Filtrar solo facturas/NC (no asientos de pago)
        return moves.filtered(
            lambda m: m.move_type in (
                'in_invoice', 'in_refund', 'out_invoice', 'out_refund'
            )
        )

    def get_regimen_ganancias_label(self):
        """Devuelve 'Código - Concepto' del régimen de Ganancias."""
        # Por qué: el certificado de Ganancias debe identificar el régimen aplicado
        self.ensure_one()
        pg = self.payment_group_id
        if pg and pg.regimen_ganancias_id:
            r = pg.regimen_ganancias_id
            return '%s - %s' % (r.codigo_de_regimen, r.concepto_referencia)
        return ''

    def get_ganancias_condition_label(self):
        """Devuelve la condición del sujeto frente a Ganancias."""
        # Por qué: el certificado requiere indicar AC/NI/EX del sujeto retenido
        self.ensure_one()
        labels = {
            'AC': 'Inscripto',
            'NI': 'No Inscripto',
            'EX': 'Exento',
            'NC': 'No Corresponde',
        }
        cond = self.partner_id.commercial_partner_id.imp_ganancias_padron
        return labels.get(cond, cond or '')
