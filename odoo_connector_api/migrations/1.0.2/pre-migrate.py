# Por qué: Las migrations 1.0.0 y 1.0.1 tenían dirs con formato 19.0.x inválido → nunca corrieron.
#          Esta limpia vistas con ocapi_bindings que rompen validación de sale.order views.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("odoo_connector_api 1.0.2: cleanup INICIO (from %s)", version)

    # Desactivar vistas con ocapi_bindings
    cr.execute("""
        UPDATE ir_ui_view SET active = false
        WHERE arch_db::text LIKE '%%ocapi_bindings%%'
          AND active = true
    """)
    if cr.rowcount:
        _logger.info("odoo_connector_api: %d vistas ocapi DESACTIVADAS", cr.rowcount)

    # Desactivar TODAS las vistas del módulo
    cr.execute("""
        UPDATE ir_ui_view SET active = false
        WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'odoo_connector_api'
              AND model = 'ir.ui.view'
        )
    """)
    if cr.rowcount:
        _logger.info("odoo_connector_api: %d vistas DESACTIVADAS", cr.rowcount)

    # Limpiar ir_model_data
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'odoo_connector_api'
          AND model != 'ir.module.module'
    """)
    if cr.rowcount:
        _logger.info("odoo_connector_api: %d ir_model_data ELIMINADOS", cr.rowcount)

    _logger.info("odoo_connector_api 1.0.2: cleanup FIN")
