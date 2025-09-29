# -*- coding: utf-8 -*-
{
    'name': "Fuel Hide",

    'summary': """
        Hide Element
        """,

    'description': """
       Hide Element Like Menu ,Buttons ... 
    """,

    'author': "Ghanem Ibrahim",
    'website': "https://fuelfinance.sa",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/templates.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'fuel_hide/static/js/hide_action_buttons.js',
            'fuel_hide/static/js/loan_order_hide.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
