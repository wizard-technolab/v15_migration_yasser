# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details

{
    'name': "ROSOM Payment API",  # The name of the module
    'version': '15.0.1',  # The version of the module
    'summary': """Create Rosom Number For pay installment""",  # A brief summary of the module's purpose
    'description': """The integration for create sadad number to customers and bay installment via number""",
    # A detailed description of the module
    'author': "Fuel Finance/IT Department",
    # The author of the module, with a comment indicating the specific person (Obay Abdulgader)
    'license': 'LGPL-3',  # The license under which the module is distributed
    'category': 'API/Integration',  # The category under which the module falls
    'website': 'https://fuelfinance.sa',  # The website of the module's author or company
    # any module necessary for this one to work correctly
    'depends': ['base', 'loan', 'ff_api_common'],
    # always loaded
    'data': [
        'data/rosom_activity.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/api_log_views.xml',
        'views/rosom_loan_views.xml',
        'views/rosom_payment_views.xml',
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
