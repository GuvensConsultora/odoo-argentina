# Por qué: La versión 1.0.0 tenía la misma versión expandida que la DB → no upgradeaba.
#          Esta migration desactiva TODAS las vistas del módulo + vistas con ocapi_bindings
#          que causan "field does not exist" al validar cualquier inherited view de sale.order.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("custom_template 1.0.1: cleanup INICIO (from %s)", version)

    # --- 1. Desactivar vistas de custom_template ---
    cr.execute("""
        UPDATE ir_ui_view SET active = false
        WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'custom_template'
              AND model = 'ir.ui.view'
        )
    """)
    if cr.rowcount:
        _logger.info("custom_template: %d vistas DESACTIVADAS", cr.rowcount)

    # --- 2. Desactivar vistas con ocapi_bindings (de meli_oerp/odoo_connector_api) ---
    # Por qué: Cualquier inherited view de sale.order falla si ocapi_bindings
    #          está en una vista hermana activa. Limpiamos antes de validar.
    cr.execute("""
        UPDATE ir_ui_view SET active = false
        WHERE arch_db::text LIKE '%%ocapi_bindings%%'
          AND active = true
    """)
    if cr.rowcount:
        _logger.info("custom_template: %d vistas ocapi DESACTIVADAS", cr.rowcount)

    # --- 3. Desactivar vistas de módulos OCAPI/meli ---
    cr.execute("""
        UPDATE ir_ui_view SET active = false
        WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module IN ('meli_oerp', 'meli_oerp_accounting',
                            'meli_oerp_stock', 'meli_oerp_multiple',
                            'odoo_connector_api')
              AND model = 'ir.ui.view'
        )
        AND active = true
    """)
    if cr.rowcount:
        _logger.info("custom_template: %d vistas OCAPI/meli DESACTIVADAS", cr.rowcount)

    # --- 4. Limpiar ir_model_data del módulo ---
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'custom_template'
          AND model != 'ir.module.module'
    """)
    if cr.rowcount:
        _logger.info("custom_template: %d ir_model_data ELIMINADOS", cr.rowcount)

    _logger.info("custom_template 1.0.1: cleanup FIN")
