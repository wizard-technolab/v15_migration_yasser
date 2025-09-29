# -*- coding: utf-8 -*-
{
    'name': "website_portal_custom",

    'summary': """
        Adding custom portal models to the portal of the user
        """,

    'description': """
        Adding custom portal models to the portal of the user ( Later a longer discription will be written )
    """,

    'author': "Eng. Mosab Alhady",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['portal','partner_reports','purchase','product'],

    # always loaded
    'data': [
        'security/quotation_security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/activity.xml',
        'data/mails.xml',
        # 'views/expression_of_desire.xml',
        # 'views/portal_expression_of_desire.xml',
        # 'views/health_declaration.xml',
        # 'views/portal_health_declaration.xml',
        'views/application.xml',
        'views/portal_application.xml',
        'views/hospital_quotation.xml',
        'views/portal_hospital_quotation.xml',
        'views/purchase_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
