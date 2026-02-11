# Por qué: el módulo original definía vistas heredadas y campos (ocapi_bindings, etc.)
# que ya no existen. Las vistas quedan en la DB y rompen la validación de otros módulos.
# Limpiamos todas las vistas y datos del módulo antes del upgrade.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Pre-migration: cleaning up old odoo_connector_api views and data")

    # Desactivar vistas heredadas para que no rompan la validación
    cr.execute("""
        UPDATE ir_ui_view SET active = false
        WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'odoo_connector_api'
            AND model = 'ir.ui.view'
        )
    """)
    _logger.info("Deactivated %d view(s)", cr.rowcount)

    # Limpiar ir_model_data del módulo viejo
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'odoo_connector_api'
        AND model != 'ir.module.module'
    """)
    _logger.info("Cleaned %d ir_model_data record(s)", cr.rowcount)
