# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details
{
    'name': "Fuel Finance Reports",  # The name of the module
    'version': '15.0.1',  # The version of the module
    'summary': """Generating Reports for Fuel Finance by wizard""",  # A brief summary of the module's purpose
    'description': """This module provides a wizard interface for users to generate and view reports based on various criteria. It simplifies the process of report generation by guiding the user through a series of steps, allowing for the selection of parameters and filters to tailor the report output""",
    # A detailed description of the module's purpose
    'author': "Fuel Finance/IT Department",
    # The author of the module, with a comment indicating the specific person (Ghanem Ibrahim / Ibrahim Rizeq)
    'website': "https://fuelfinance.sa",  # The website of the author or company
    'category': 'FF/Reports',  # The category under which this module falls
    # any module necessary for this one to work correctly
    'depends': ['base', 'loan'],
    'data': [
        # List of data files to be loaded, such as XML or CSV files for setting up the module
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/simah_report_view.xml',
        'views/save_ex_report_wizard_view.xml',
        'views/res_partner.xml',
        'views/daily_report_wizard_view.xml',
        'reports/daily_report.xml',
        'views/templates.xml',
        'views/collection_report.xml',
        'views/after_collection_report.xml',
        'views/payment_report.xml',
        'views/loan.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # List of demo data files to be loaded, such as sample data for testing
        'demo/demo.xml',
    ],
}
