# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details

{
    'name': "Fuel Finance - Purchase Quotation API",  # The name of the module
    'version': '15.0.1',  # The version of the module
    'summary': """Supplier Quotation API""",  # A brief summary of the module's purpose
    'description': """Integration between supplier portal and odoo system for send quotation and accept the quotation""",
    # A detailed description of the module
    'author': "Fuel Finance/IT Department",
    # The author of the module, with a comment indicating the specific person (Ibrahim Rizeq)
    'license': 'LGPL-3',  # The license under which the module is distributed
    'category': 'API/Integration',  # The category under which the module falls
    'website': 'https://fuelfinance.sa',  # The website of the module's author or company
    'depends': ['base'],  # The list of other modules that this module depends on
    # always loaded
    'data': [
        'security/ir.model.access.csv',  # The security access control file
    ],
    'qweb': [
        # List of QWeb templates to load, if any
    ],
    'assets': {
        # Assets such as JavaScript, CSS, and other static files to load
    },
    'installable': True,  # Indicates if the module can be installed
    'application': True,  # Indicates if the module should be considered as an application
}
