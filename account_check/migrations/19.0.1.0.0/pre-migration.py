# Por qué: La vista heredada view_account_check_create_tree usa <tree position="attributes">
# pero en Odoo 19 el padre ya fue convertido a <list>, lo que rompe la validación.
# Se elimina la vista ANTES de que Odoo intente validarla.
def migrate(cr, version):
    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'account_check'
            AND name = 'view_account_check_create_tree'
        )
    """)
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'account_check'
        AND name = 'view_account_check_create_tree'
    """)
