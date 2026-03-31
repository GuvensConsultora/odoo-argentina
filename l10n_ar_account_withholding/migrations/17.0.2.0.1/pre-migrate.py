"""Limpia duplicados de regímenes y escalas Ganancias.

Por qué: l10n_ar_account_withholding y l10n_ar_account_withholding_automatic
cargaban los mismos datos con prefijos de módulo distintos, creando
registros duplicados en la base de datos.

Este script se ejecuta automáticamente al actualizar el módulo
a la versión 17.0.2.0.1 y elimina los duplicados del módulo _automatic.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    module_auto = 'l10n_ar_account_withholding_automatic'
    module_new = 'l10n_ar_account_withholding'

    # Borrar regímenes duplicados del módulo _automatic
    cr.execute("""
        DELETE FROM afip_tabla_ganancias_alicuotasymontos
        WHERE id IN (
            SELECT imd1.res_id FROM ir_model_data imd1
            WHERE imd1.module = %s
              AND imd1.model = 'afip.tabla_ganancias.alicuotasymontos'
              AND imd1.name IN (
                  SELECT imd2.name FROM ir_model_data imd2
                  WHERE imd2.module = %s
                    AND imd2.model = 'afip.tabla_ganancias.alicuotasymontos'
              )
        )
    """, (module_auto, module_new))
    _logger.info('Migration: %d regimenes duplicados eliminados de %s',
                 cr.rowcount, module_auto)

    # Borrar escalas duplicadas del módulo _automatic
    cr.execute("""
        DELETE FROM afip_tabla_ganancias_escala
        WHERE id IN (
            SELECT imd1.res_id FROM ir_model_data imd1
            WHERE imd1.module = %s
              AND imd1.model = 'afip.tabla_ganancias.escala'
              AND imd1.name IN (
                  SELECT imd2.name FROM ir_model_data imd2
                  WHERE imd2.module = %s
                    AND imd2.model = 'afip.tabla_ganancias.escala'
              )
        )
    """, (module_auto, module_new))
    _logger.info('Migration: %d escalas duplicadas eliminadas de %s',
                 cr.rowcount, module_auto)

    # Limpiar ir_model_data huérfanos
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = %s
          AND model IN (
              'afip.tabla_ganancias.alicuotasymontos',
              'afip.tabla_ganancias.escala'
          )
    """, (module_auto,))
    _logger.info('Migration: %d ir_model_data huerfanos eliminados',
                 cr.rowcount)

    # También borrar escalas viejas que no coinciden con ningún XML ID
    # (la escala vieja del _automatic tenía montos tipo 1,600,000)
    cr.execute("""
        DELETE FROM afip_tabla_ganancias_escala
        WHERE id NOT IN (
            SELECT res_id FROM ir_model_data
            WHERE model = 'afip.tabla_ganancias.escala'
              AND module = %s
        )
    """, (module_new,))
    if cr.rowcount:
        _logger.info('Migration: %d escalas huerfanas eliminadas', cr.rowcount)
