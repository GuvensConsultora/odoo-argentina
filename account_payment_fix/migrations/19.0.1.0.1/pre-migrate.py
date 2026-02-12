# Por qué: en el upgrade 17→19, Odoo genera vistas COW (Copy-On-Write) por website.
# La COW de website_sale.header_cart_link conserva código viejo que llama a
# sale_get_order (removido en Odoo 19), rompiendo la página de login.
# Desactivamos las COW huérfanas para que Odoo use el template estándar actualizado.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Pre-migration: deactivating orphan COW views for website_sale.header_cart_link")

    # Desactivar COW views (tienen website_id != NULL) que usan el template viejo
    cr.execute("""
        UPDATE ir_ui_view SET active = false
        WHERE key = 'website_sale.header_cart_link'
        AND website_id IS NOT NULL
        AND active = true
    """)
    if cr.rowcount:
        _logger.info("Deactivated %d orphan COW view(s)", cr.rowcount)
