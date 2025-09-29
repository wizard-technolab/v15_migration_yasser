# -*- coding: utf-8 -*-
{
    'name': 'PRM',
    'version': '15.0.1',
    'summary': 'PRM Management',
    'sequence': -2000,
    'description': """ create module people relation management""",
    'license': 'LGPL-3',
    'depends': ['base', 'crm', 'purchase', 'sale_management'],
    'data': [
        'security/prm_security.xml',
        'security/ir.model.access.csv',
        'view/prm_view.xml',
        'view/prm_views_menus.xml',

    ],
    'demo': [],
    'qweb': [
        'static/src/xml/generate_leads_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
