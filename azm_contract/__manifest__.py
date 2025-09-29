# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details
{
    'name': "Azm Contracts Integration",  # The name of the module as it will appear in the Odoo application.
    'version': '15.0.1',                  # The version of the module. This follows the format major.minor.patch.
    'summary': """Contracts APIs Services""",  # A short summary of what the module does. This is a brief description shown in the Odoo app list.
    'description': """
        Integration with the Azm Services to sign contracts and Nafith""",  # A more detailed description of the module's functionality and purpose.
    'author': "Fuel Finance/IT Department", # The author of the module, with a comment indicating the specific person (Ibrahim Rizeq)
    'license': 'LGPL-3',                   # The license under which the module is released. LGPL-3 is a permissive open-source license.
    'category': 'API/Integration',         # The category under which the module is classified. This helps users find the module in the Odoo app list.
    'website': 'https://fuelfinance.sa',   # The website URL for the module or the organization that developed it. This provides users with more information.
    'depends': ['base', 'loan'],           # A list of other Odoo modules that this module depends on. This ensures that required modules are loaded first.
    'data': [                             # A list of XML/CSV files that define the module's data and configuration.
        'security/ir.model.access.csv',   # Access control list (ACL) file that defines permissions for different models in the module.
        'views/azm_contracts.xml',        # XML file that defines the views for the module. This includes UI components like forms and lists.
    ],
    'assets': {                           # A dictionary defining the assets (JS/CSS/XML) needed for the module.
        'web.assets_qweb': [             # List of QWeb templates to include in the web assets.
            'azm_contract/static/src/xml/all_contracts_temp.xml'  # Path to the QWeb template XML file.
        ],
        'web.assets_backend': [          # List of JavaScript files to include in the backend assets.
            'azm_contract/static/src/js/all_contracts.js'  # Path to the JavaScript file that adds functionality to the module.
        ]
    }
}