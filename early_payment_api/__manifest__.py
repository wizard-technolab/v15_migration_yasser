# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details
{
    'name': "Early Payment Integration",  # The name of the module as it will appear in the Odoo apps list
    'version': '15.0.1',  # The version of the module, indicating compatibility with Odoo version 15.0
    'summary': """Early Payment Function""",  # A short summary of the module's purpose
    'description': """Allowing customers to pay a discounted amount to Fuel Finance in exchange for settling invoices before their maturity date""",
    # A detailed description of the module's functionality
    'author': "Fuel Finance/IT Department",
    # The author of the module, with a comment indicating the specific person (Ibrahim Rizeq)
    'license': 'LGPL-3',  # The license under which the module is distributed
    'category': 'API/Integration',
    # The category under which the module falls, for classification in the Odoo apps list
    'website': 'https://fuelfinance.sa',  # The website of the author or the company, for reference
    'depends': ['base', ],  # A list of dependencies, indicating that this module depends on the 'base' module
    'data': [
        'security/ir.model.access.csv',  # A list of data files to be loaded, including access control definitions
    ],
    'qweb': [
        # List of QWeb templates, if any (empty in this case)
    ],
    'assets': {
        # Dictionary of assets (CSS, JavaScript, etc.) to be included (empty in this case)
    },
    'installable': True,  # Indicates that the module can be installed
    'application': True,  # Indicates that the module is an application (appears in the Apps menu)
}
