# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details
{
    'name': 'Cash Wallet Module',  # The name of the module
    'version': '15.0.1',  # The version of the module, indicating it's the first release for Odoo 15
    'summary': 'Cash Wallet and Flags Management',  # A brief summary of the module's functionality
    'sequence': -3000,  # The sequence in which the module should be loaded; negative value places it early in the loading order
    'description': """ Effective cash wallet management ensures that funds are used efficiently, reduces the risk of loss or fraud, and provides transparency and accountability in financial operations.""",  # A detailed description of the module
    'license': 'LGPL-3',  # The license under which the module is distributed (GNU Lesser General Public License v3.0)
    'category': 'Finance/finance',  # The category under which the module will be listed in the Odoo app store
    'website': 'https://fuelfinance.sa',  # The website URL for more information about the module or the developer
    'depends': ['base', 'loan', 'account_accountant', 'account', 'contacts'],  # List of dependencies; other modules that must be installed for this module to work
    'data': [
        'security/wallet_security.xml',  # XML file defining security rules and access rights
        'security/ir.model.access.csv',  # CSV file defining access control lists (ACLs) for models

        'view/wallet_menu.xml',  # XML file defining the menu items for the module
        'view/wallet_view.xml',  # XML file defining the views (forms, lists, etc.) for the module

    ],
    'demo': [],  # List of demo data files to be loaded for demonstration purposes
    'qweb': [],  # List of QWeb templates (if any) used by the module
    'installable': True,  # Boolean indicating if the module can be installed
    'application': True,  # Boolean indicating if the module should be listed as an application
    'auto_install': False,  # Boolean indicating if the module should be automatically installed if all dependencies are met
}
