# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details

{
    'name': "Elm and Yakeen Integration",  # The name of the module
    'version': '15.0.1',  # The version of the module
    'summary': """Integration With Elm Company For Yakeen Service""",  # A brief summary of the module
    'description': """A digital service that provides basic customer data and national addresses""",
    # A detailed description of the module
    'author': "Fuel Finance/IT Department",
    # The author of the module, with a comment indicating the specific person (Ibrahim Rizeq)
    'license': 'LGPL-3',  # The license under which the module is distributed
    'category': 'API/Integration',  # The category under which the module falls
    'website': 'https://fuelfinance.sa',  # The website of the module or the company
    # Any modules necessary for this one to work correctly
    'depends': ['loan'],  # Dependencies for this module to function, in this case, the 'loan' module
    # Data files always loaded (even in demo mode)
    'data': [
        'security/ir.model.access.csv',  # Security access control file
        'views/res_partner_views.xml',  # XML file for customizing views related to 'res.partner'
        'views/log_views.xml',  # XML file for customizing log views
    ],
}
