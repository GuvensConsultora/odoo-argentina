# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date


class AccountTax(models.Model):
    _inherit = "account.tax"

    # Por qué: selection_add agrega 'partner_tax' sin pisar las opciones del core
    amount_type = fields.Selection(
        selection_add=[('partner_tax', 'Alicuota en el partner')],
        ondelete={'partner_tax': 'set default'},
    )

    def get_period_payments_domain(self, payment_group):
        previos_payment_groups_domain, previos_payments_domain = super(
            AccountTax, self).get_period_payments_domain(payment_group)
        if self.withholding_type == 'tabla_ganancias':
            previos_payment_groups_domain += [
                ('regimen_ganancias_id', '=',
                    payment_group.regimen_ganancias_id.id)]
            previos_payments_domain += [
                ('payment_group_id.regimen_ganancias_id', '=',
                    payment_group.regimen_ganancias_id.id)]
        return (
            previos_payment_groups_domain,
            previos_payments_domain)

    # =====================================================================
    # Ganancias — Métodos auxiliares
    # =====================================================================

    def _get_ganancias_base_amount(self, payment_group, vals):
        """Obtener base imponible neta del pago.
        Por qué: si hay facturas seleccionadas, usamos el neto (tax_factor).
        Si es adelanto (sin facturas), usamos to_pay_amount.
        """
        base_amount = 0.0
        if payment_group.debt_move_line_ids:
            for move_line in payment_group.debt_move_line_ids:
                # Por qué: _get_tax_factor() retorna ratio neto/total de la factura
                # amount_residual es negativo para deuda → multiplicamos por -1
                base_amount += (
                    move_line.move_id._get_tax_factor() * (-1)
                    * move_line.with_context(
                        payment_group_id=payment_group.id
                    ).amount_residual
                )
        else:
            # Patrón: adelanto — no hay facturas, usamos el monto a pagar
            base_amount = payment_group.to_pay_amount
        return base_amount

    def _get_ganancias_accumulated(self, payment_group):
        """Buscar pagos previos del mismo mes/partner/régimen.
        Retorna (monto_acumulado, retenciones_previas).
        Por qué: una sola búsqueda de pagos previos elimina la duplicación
        del código viejo que buscaba 2 veces.
        """
        today = payment_group.payment_date
        first_day = date(today.year, today.month, 1)

        # Por qué: buscamos TODOS los pagos outbound posted del mes
        # para este partner, excluyendo el payment_group actual
        prev_payments = self.env['account.payment'].search([
            ('payment_type', '=', 'outbound'),
            ('state', '=', 'posted'),
            ('payment_group_id', '!=', payment_group.id),
            ('partner_id', '=', payment_group.partner_id.id),
            ('payment_group_id.payment_date', '>=', str(first_day)),
            ('payment_group_id.payment_date', '<=', today),
            ('payment_group_id.retencion_ganancias', '=', 'nro_regimen'),
            ('payment_group_id.regimen_ganancias_id', '=',
                payment_group.regimen_ganancias_id.id),
        ])

        accumulated_amount = 0.0
        previous_withholding = 0.0
        has_prev_withholding = False

        for payment in prev_payments:
            if payment.tax_withholding_id.id == self.id:
                # Por qué: es una retención previa de este mismo impuesto
                # → sumar para descontar después
                previous_withholding += payment.amount
                has_prev_withholding = True
            else:
                # Por qué: es un pago normal (no retención de este tax)
                # → acumular su base para el cálculo
                pg = payment.payment_group_id
                if pg and pg.matched_move_line_ids:
                    for matched_line in pg.matched_move_line_ids:
                        accumulated_amount += (
                            matched_line.move_id._get_tax_factor() * (-1)
                            * matched_line.with_context(
                                payment_group_id=pg.id
                            ).payment_group_matched_amount
                        )
                else:
                    accumulated_amount += payment.amount

        return accumulated_amount, previous_withholding, has_prev_withholding

    def _compute_ganancias_escala(self, regimen, base_amount):
        """Calcular retención por escala.
        Por qué: si el régimen tiene escala_ids propias, usarlas.
        Si no, usar la escala general (regimen_id = False).
        Patrón: fallback — escala específica → escala general.
        """
        domain = [
            ('importe_desde', '<=', base_amount),
            ('importe_hasta', '>', base_amount),
        ]
        if regimen.escala_ids:
            # Escala específica del régimen (ej: 119 tiene RG 5423)
            domain.append(('regimen_id', '=', regimen.id))
        else:
            # Escala general RG 830 (regimen_id = False)
            domain.append(('regimen_id', '=', False))

        escala = self.env['afip.tabla_ganancias.escala'].search(
            domain, limit=1)
        if not escala:
            raise UserError(
                'No se encontró escala para el monto %s '
                '(régimen %s)' % (base_amount, regimen.codigo_de_regimen))

        # Fórmula: importe_fijo + porcentaje * (base - excedente)
        amount = escala.importe_fijo + (
            escala.porcentaje / 100.0) * (base_amount - escala.importe_excedente)
        comment = "%s + (%s x %s)" % (
            escala.importe_fijo,
            base_amount - escala.importe_excedente,
            escala.porcentaje / 100.0)
        return amount, comment

    def _compute_ganancias_inscripto(self, payment_group, regimen, vals):
        """Cálculo completo para inscriptos (AC).
        Flujo:
        1. Base imponible del pago actual
        2. Acumular pagos del período
        3. Restar monto no sujeto (1 sola vez por mes)
        4. Calcular por escala o porcentaje fijo
        5. Restar retenciones previas del mes
        """
        # 1. Base imponible del pago actual
        base_amount = self._get_ganancias_base_amount(payment_group, vals)

        # 2. Acumular pagos del mes (si está configurado)
        accumulated_amount = 0.0
        previous_withholding = 0.0
        has_prev_withholding = False
        if self.withholding_accumulated_payments:
            accumulated_amount, previous_withholding, has_prev_withholding = \
                self._get_ganancias_accumulated(payment_group)
            base_amount += accumulated_amount

        # 3. Restar monto no sujeto a retención
        non_taxable = regimen.montos_no_sujetos_a_retencion
        vals['withholding_non_taxable_amount'] = non_taxable

        if base_amount <= non_taxable and not has_prev_withholding:
            # Por qué: si la base no supera el mínimo y no hay retenciones
            # previas, no corresponde retener
            vals['withholdable_base_amount'] = 0.0
            vals['period_withholding_amount'] = 0.0
            vals['previous_withholding_amount'] = previous_withholding
            vals['comment'] = "Base %s <= Monto no sujeto %s" % (
                base_amount, non_taxable)
            return vals

        base_amount -= non_taxable

        # 4. Calcular retención según tipo
        if regimen.porcentaje_inscripto == -1:
            # Por qué: porcentaje_inscripto = -1 indica "calcular por escala"
            amount, comment = self._compute_ganancias_escala(
                regimen, base_amount)
        else:
            # Porcentaje fijo (ej: régimen 78 → 2%)
            amount = base_amount * (regimen.porcentaje_inscripto / 100.0)
            comment = "%s x %s%%" % (base_amount, regimen.porcentaje_inscripto)

        # 5. Verificar mínimo no imponible
        if amount < self.withholding_non_taxable_minimum and not has_prev_withholding:
            amount = 0.0

        vals['withholdable_base_amount'] = base_amount
        vals['period_withholding_amount'] = amount
        vals['previous_withholding_amount'] = previous_withholding
        vals['comment'] = comment
        return vals

    # =====================================================================
    # Método principal — override de get_withholding_vals
    # =====================================================================

    def get_withholding_vals(self, payment_group):
        commercial_partner = payment_group.commercial_partner_id

        force_withholding_amount_type = None
        if self.withholding_type == 'partner_tax':
            alicuot_line = self.get_partner_alicuot(
                commercial_partner,
                payment_group.payment_date or fields.Date.context_today(self),
            )
            alicuota = alicuot_line

        vals = super(AccountTax, self).get_withholding_vals(
            payment_group, force_withholding_amount_type)
        base_amount = vals['withholdable_base_amount']

        if self.withholding_type == 'partner_tax':
            amount = base_amount * (alicuota)
            vals['comment'] = "%s x %s" % (base_amount, alicuota)
            vals['period_withholding_amount'] = amount

        elif self.withholding_type == 'tabla_ganancias':
            # Por qué: usamos el régimen del payment_group (no el del partner)
            # Tip: el régimen se selecciona al crear el pago, puede diferir
            # del default del partner
            regimen = payment_group.regimen_ganancias_id
            imp_ganancias_padron = commercial_partner.imp_ganancias_padron

            if (payment_group.retencion_ganancias != 'nro_regimen'
                    or not regimen):
                # Sin régimen configurado → no retener
                amount = 0.0
            elif not imp_ganancias_padron:
                raise UserError(
                    'El partner %s no tiene configurada inscripción en '
                    'impuesto a las ganancias' % commercial_partner.name)
            elif imp_ganancias_padron in ['EX', 'NC']:
                # Exento o no corresponde → no retener
                amount = 0.0
            elif imp_ganancias_padron == 'AC':
                # Inscripto — cálculo completo
                vals = self._compute_ganancias_inscripto(
                    payment_group, regimen, vals)
                # communication se arma abajo
            elif imp_ganancias_padron == 'NI':
                # No inscripto — porcentaje fijo directo
                base_ni = self._get_ganancias_base_amount(payment_group, vals)
                amount = base_ni * (regimen.porcentaje_no_inscripto / 100.0)
                vals['period_withholding_amount'] = amount
                vals['comment'] = "%s x %s%%" % (
                    base_ni, regimen.porcentaje_no_inscripto)

            vals['communication'] = "%s - %s" % (
                regimen.codigo_de_regimen, regimen.concepto_referencia)

        return vals

    def get_partner_alicuota_percepcion(self, partner, date):
        if partner and date:
            arba = self.get_partner_alicuot(partner, date)
            return arba.alicuota_percepcion / 100.0
        return 0.0

    def get_partner_alicuot(self, partner, date):
        self.ensure_one()
        commercial_partner = partner.commercial_partner_id
        company = self.company_id
        alicuot = 0
        for alicuot_id in commercial_partner.perception_ids:
            if alicuot_id.tax_id.id == self.id:
                alicuot = alicuot_id.percent / 100
        return alicuot

    def _compute_amount(
            self, base_amount, price_unit, quantity=1.0, product=None,
            partner=None, fixed_multiplicator=1):
        if self.amount_type == 'partner_tax':
            try:
                date = self._context.date_invoice
            except Exception:
                date = fields.Date.context_today(self)
            return base_amount * self.get_partner_alicuota_percepcion(
                partner, date)
        else:
            return super(AccountTax, self)._compute_amount(
                base_amount, price_unit, quantity, product, partner, fixed_multiplicator)
