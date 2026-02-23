# Por qué: limpiar vistas y datos del módulo removido para evitar errores de validación
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Pre-migration: cleaning up old custom_template views and data")

    cr.execute("""
        UPDATE ir_ui_view SET active = false
        WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'custom_template'
            AND model = 'ir.ui.view'
        )
    """)
    _logger.info("Deactivated %d view(s)", cr.rowcount)

    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'custom_template'
        AND model != 'ir.module.module'
    """)
    _logger.info("Cleaned %d ir_model_data record(s)", cr.rowcount)
