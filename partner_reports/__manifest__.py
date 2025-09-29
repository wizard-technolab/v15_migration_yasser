# -*- coding: utf-8 -*-
{
    'name': "partner_reports",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','crm'],

    # always loaded
    
    'assets':{
        'web.report_assets_common': [ 
            '/partner_reports/static/src/css/medical_service_financing_request.css',
            '/partner_reports/static/src/css/expression_of_desire_form.css',
        ]
    },
    'data': [
        'security/ir.model.access.csv',
        # 'views/assets.xml',
        'data/sequence.xml',
        'views/generic_template.xml',
        'views/views.xml',
        'report/medical_services_financing_request.xml',
        # 'report/expression_of_desire_form.xml',
        # 'report/health_declaration.xml',
        'report/quotation.xml',
        
    ],# only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
