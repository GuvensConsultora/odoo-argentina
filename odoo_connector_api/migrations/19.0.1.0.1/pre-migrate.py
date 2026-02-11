# Por qué: la migración 19.0.1.0.0 limpió ir_model_data y vistas,
# pero dejó registros en ir_model e ir_model_fields.
# Odoo loguea ERROR "Missing model ocapi.*" al encontrar ir_model
# sin clase Python correspondiente. Esto marca builds como fallidos en Odoo.sh.
import logging

_logger = logging.getLogger(__name__)

OCAPI_MODELS = [
    'ocapi.connection.account',
    'ocapi.connection.notification',
    'ocapi.connection.binding.product_template',
    'ocapi.binding.sale_order',
    'ocapi.binding.client',
]


def migrate(cr, version):
    _logger.info("Pre-migration: removing orphan ir_model records for ocapi models")

    # Eliminar campos huérfanos de los modelos ocapi
    cr.execute(
        "DELETE FROM ir_model_fields WHERE model IN %s",
        (tuple(OCAPI_MODELS),)
    )
    _logger.info("Deleted %d orphan ir_model_fields record(s)", cr.rowcount)

    # Eliminar constraints huérfanas
    cr.execute(
        "DELETE FROM ir_model_constraint WHERE model IN "
        "(SELECT id FROM ir_model WHERE model IN %s)",
        (tuple(OCAPI_MODELS),)
    )
    _logger.info("Deleted %d orphan ir_model_constraint record(s)", cr.rowcount)

    # Eliminar relaciones huérfanas
    cr.execute(
        "DELETE FROM ir_model_relation WHERE model IN "
        "(SELECT id FROM ir_model WHERE model IN %s)",
        (tuple(OCAPI_MODELS),)
    )
    _logger.info("Deleted %d orphan ir_model_relation record(s)", cr.rowcount)

    # Eliminar access rules huérfanas
    cr.execute(
        "DELETE FROM ir_model_access WHERE model_id IN "
        "(SELECT id FROM ir_model WHERE model IN %s)",
        (tuple(OCAPI_MODELS),)
    )
    _logger.info("Deleted %d orphan ir_model_access record(s)", cr.rowcount)

    # Eliminar ir_model_data remanente del módulo
    cr.execute(
        "DELETE FROM ir_model_data WHERE module = 'odoo_connector_api'"
        " AND model != 'ir.module.module'"
    )
    _logger.info("Deleted %d orphan ir_model_data record(s)", cr.rowcount)

    # Finalmente, eliminar los registros de ir_model
    cr.execute(
        "DELETE FROM ir_model WHERE model IN %s",
        (tuple(OCAPI_MODELS),)
    )
    _logger.info("Deleted %d orphan ir_model record(s)", cr.rowcount)
