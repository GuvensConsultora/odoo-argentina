# -*- coding: utf-8 -*-
from odoo import models, fields


class AfipTablagananciasEscala(models.Model):
    _name = 'afip.tabla_ganancias.escala'
    _rec_name = 'importe_desde'
    # Por qué: ordenar por régimen permite agrupar escalas específicas vs generales
    _order = 'regimen_id, importe_desde'

    # Por qué: si regimen_id está seteado, la escala aplica solo a ese régimen.
    # Si es False, es la escala general (RG 830) usada por defecto.
    regimen_id = fields.Many2one(
        'afip.tabla_ganancias.alicuotasymontos',
        string='Régimen',
        ondelete='set null',
    )
    importe_desde = fields.Float(
        'Mas de $',
    )
    importe_hasta = fields.Float(
        'A $',
    )
    importe_fijo = fields.Float(
        '$',
    )
    porcentaje = fields.Float(
        'Más el %'
    )
    importe_excedente = fields.Float(
        'S/ Exced. de $'
    )


class AfipTablagananciasAlicuotasymontos(models.Model):
    _name = 'afip.tabla_ganancias.alicuotasymontos'
    _rec_name = 'codigo_de_regimen'

    codigo_de_regimen = fields.Char(
        'Codigo de regimen',
        size=6,
        required=True,
        help='Codigo de regimen de inscripcion en impuesto a las ganancias.'
    )
    anexo_referencia = fields.Char(
        required=True,
    )
    concepto_referencia = fields.Text(
        required=True,
    )
    porcentaje_inscripto = fields.Float(
        '% Inscripto',
        help='Elija -1 si se debe calcular s/escala'
    )
    porcentaje_no_inscripto = fields.Float(
        '% No Inscripto'
    )
    montos_no_sujetos_a_retencion = fields.Float(
    )
    # Por qué: One2many inverso para acceder rápido a las escalas
    # específicas de este régimen desde la vista form y el cálculo
    escala_ids = fields.One2many(
        'afip.tabla_ganancias.escala',
        'regimen_id',
        string='Escalas',
    )
