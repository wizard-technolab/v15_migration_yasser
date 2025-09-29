# -*- coding: utf-8 -*-
# Part of  Custom Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Collection Management',  # Name of the Anti-Money Laundering module
    'version': '15.0.1',  # Version of the Anti-Money Laundering module
    'summary': 'Collection Module Management',  # Brief summary of the module
    'sequence': -7000,  # Sequence for module loading order
    'description': """ The Collection Management module is designed to streamline and automate the process of tracking, managing, and collecting payments from customers. It provides tools for managing outstanding dues, following up on invoices, and ensuring timely collections.""",
    # Detailed description of the module
    'author': "Fuel Finance/IT Department",  # By Ibrahim Rizeq
    'license': 'LGPL-3',  # License under which the module is distributed
    'category': 'Collection/Collection',  # category of module
    'website': 'https://fuelfinance.sa',  # Fuel Finance Website
    'depends': ['base', 'web', 'loan', 'account_accountant', 'account', 'contacts', 'mail', 'portal'],
    # Dependencies of the module
    'data': [
        'data/collection_data.xml',
        'security/security.xml',  # Security rules for the module
        'security/ir.model.access.csv',  # Access control rules for the module
        'views/collection_views.xml',  # Menu definitions for the module
        'views/sms_views.xml',  # Menu definitions for the module
        'views/multi_sms_views.xml',  # Menu definitions for the module
        'views/configuration.xml',  # Menu definitions for the module
        'views/sms_template_view.xml',  # Menu definitions for the module
        'views/collection_transfer_wizard_views.xml',
        'views/loan_order_actions.xml',

    ],
    'installable': True,  # Indicates that the module can be installed
    'application': True,  # Indicates that the module is an application
    'auto_install': False,  # Indicates that the module should not be installed automatically
    'assets': {
        'web.assets_backend': [
            # 'web.AbstractAction',
            # 'collection/static/src/js/collection_dashboard.js',
            'collection/static/src/scss/card.scss'

        ],
        # 'web.assets_qweb': [
        #     'collection/static/src/xml/collection_dashboard_templates.xml',
        # ],
    },
}
