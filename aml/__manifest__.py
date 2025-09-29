# -*- coding: utf-8 -*-
# Part of  Custom Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Aml',  # Name of the Anti-Money Laundering module
    'version': '15.0.1',  # Version of the Anti-Money Laundering module
    'summary': 'Anti-Money Laundering Module Management',  # Brief summary of the module
    'sequence': -3000,  # Sequence for module loading order
    'description': """ AML (Anti-Money Laundering): Set of standards, regulations,
     and laws that aim to prevent money laundering activities and advanced financial crimes""",
    # Detailed description of the module
    'author': "Fuel Finance/IT Department", # By Ibrahim Rizeq
    'license': 'LGPL-3',  # License under which the module is distributed
    'category': 'Complaince/Complaince',  # category of module
    'website': 'https://fuelfinance.sa',  # Fuel Finance Website
    'depends': ['base', 'crm', 'account_accountant', 'account', 'contacts'],  # Dependencies of the module
    'data': [
        'security/aml_security.xml',  # Security rules for the module
        'security/ir.model.access.csv',  # Access control rules for the module
        'view/aml_menu.xml',  # Menu definitions for the module
        'view/aml_view.xml',  # View definitions for the module
    ],
    'demo': [],  # Demo data for the module
    'qweb': [],  # QWeb templates for the module
    'installable': True,  # Indicates that the module can be installed
    'application': True,  # Indicates that the module is an application
    'auto_install': False,  # Indicates that the module should not be installed automatically
}
