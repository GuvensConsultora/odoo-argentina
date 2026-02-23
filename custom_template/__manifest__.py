# Por qué: módulo stub para evitar "inconsistent states" en upgrade 17→19
# El módulo original fue removido pero queda como installed en la DB
{
    'name': 'Custom Template (deprecated)',
    'version': '1.0.0',
    'category': 'Hidden',
    'summary': 'Stub - module removed in Odoo 19 upgrade',
    'depends': ['base'],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
