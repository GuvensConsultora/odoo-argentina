# Por qué: módulos custom_template y odoo_connector_api no existen en 19.0
# pero quedan como 'installed' en la DB del upgrade desde 17.0.
# Odoo loguea ERROR "inconsistent states" y Odoo.sh marca el build como fallido.
# Este script los marca como uninstalled antes de que se detecte la inconsistencia.
import logging

_logger = logging.getLogger(__name__)

MODULES_TO_REMOVE = ['custom_template', 'odoo_connector_api']


def migrate(cr, version):
    _logger.info("Pre-migration: cleaning up removed modules %s", MODULES_TO_REMOVE)
    cr.execute(
        "UPDATE ir_module_module SET state = 'uninstalled' "
        "WHERE name IN %s AND state = 'installed'",
        (tuple(MODULES_TO_REMOVE),)
    )
    if cr.rowcount:
        _logger.info("Marked %d module(s) as uninstalled", cr.rowcount)
