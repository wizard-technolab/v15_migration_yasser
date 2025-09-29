# -*- coding: utf-8 -*-
{
    'name': "Custom Page Website",

    'summary': """
            Create Main Page in Website
        """,

    'description': """""",

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'loan'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',

        'view/menu.xml',
        # 'views/templates.xml',
    ],
    'assets': {
        'web.assets_common': [
            '/website_menu/static/src/js/script.js',
        ]
    },
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
