# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details

{
    'name': "Nafaes Order API",  # The name of the module
    'version': '15.0.1',  # The version of the module
    'summary': """Buy and sell commodity""",  # A brief summary of the module's purpose
    'description': """The integration can buy and sell commodity between fuel finance and nafaes platform for customers""",
    # A detailed description of the module
    'author': "Fuel Finance/IT Department",
    # The author of the module, with a comment indicating the specific person (Ibrahim Rizeq/Obay Abdulgader)
    'license': 'LGPL-3',  # The license under which the module is distributed
    'category': 'API/Integration',  # The category under which the module falls
    'website': 'https://fuelfinance.sa',  # The website of the module's author or company
    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'loan'],
    # always loaded
    'data': [
        'data/nafaes_activity.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/nafaes_order_views.xml',
        'views/api_log_views.xml',
        'views/commodity_views.xml',
        'views/order_result_views.xml',
        'views/nafaes_loan_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'qweb': [
        # List of QWeb templates to load, if any
    ],
    'installable': True,  # Indicates if the module can be installed
    'application': False,  # Indicates if the module should be considered as an application
}
