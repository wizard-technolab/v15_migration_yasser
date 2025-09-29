# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details

{
    'name': 'Hide Delete Button in Chatter', # The name of the module
    'version': '15.0.1',  # The version of the module
    'summary': 'Hide the delete button in log notes', # A brief summary of the module's purpose
    'description': 'Hides the delete button in log notes (chatter)',  # A detailed description of the module
    'author':  "Fuel Finance/IT Department",  # The author of the module, with a comment indicating the specific person (Ibrahim Rizeq/Hadeel Ahmed)
    'license': 'LGPL-3', # The license under which the module is distributed
    'category': 'FF/Module/Feature',  # The category under which the module falls
    'website': 'https://fuelfinance.sa',  # The website of the module's author or company
    'depends': ['base', 'web', 'mail'],
    'data': [
    ],
    'assets': {
        'web.assets_qweb': [
            # Assets such as JavaScript, CSS, and other static files to load
            'hide_delete_button/static/src/xml/assets.xml'
        ],
    },
    'qweb': [
        # List of QWeb templates to load, if any
    ],
    'installable': True, # Indicates if the module can be installed
    'application': False, # Indicates if the module should be considered as an application
}
