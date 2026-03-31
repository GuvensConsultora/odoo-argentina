"""Limpia duplicados de regímenes y escalas Ganancias.

Por qué: l10n_ar_account_withholding y l10n_ar_account_withholding_automatic
cargaban los mismos datos con prefijos de módulo distintos, creando
registros duplicados en la base de datos.

Este script se ejecuta automáticamente al actualizar el módulo
a la versión 17.0.2.0.1 y elimina los duplicados por código de régimen
y por tramo de escala, manteniendo siempre el registro con menor ID.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # 1. Borrar regímenes duplicados por codigo_de_regimen (mantener menor ID)
    cr.execute("""
        DELETE FROM afip_tabla_ganancias_alicuotasymontos
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM afip_tabla_ganancias_alicuotasymontos
            GROUP BY codigo_de_regimen
        )
    """)
    if cr.rowcount:
        _logger.info('Migration: %d regimenes duplicados eliminados', cr.rowcount)

    # 2. Borrar escalas duplicadas por (importe_desde, importe_hasta) (mantener menor ID)
    cr.execute("""
        DELETE FROM afip_tabla_ganancias_escala
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM afip_tabla_ganancias_escala
            GROUP BY importe_desde, importe_hasta
        )
    """)
    if cr.rowcount:
        _logger.info('Migration: %d escalas duplicadas eliminadas', cr.rowcount)

    # 3. Limpiar ir_model_data del módulo _automatic para estos modelos
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'l10n_ar_account_withholding_automatic'
          AND model IN (
              'afip.tabla_ganancias.alicuotasymontos',
              'afip.tabla_ganancias.escala'
          )
    """)
    if cr.rowcount:
        _logger.info('Migration: %d ir_model_data huerfanos eliminados', cr.rowcount)
