# -*- coding: utf-8 -*-
# Part of Custom Odoo. See LICENSE file for full copyright and licensing details

{
    'name': "Simah Platform API",  # The name of the module
    'version': '15.0.1',  # The version of the module
    'sequence': -1000,
    'summary': """Integration With Simah Platform""",  # A brief summary of the module's purpose
    'description': """The integration for Inquiries All Customers For Salary Certificate and Liability Information""",
    # A detailed description of the module
    'author': "Fuel Finance/IT Department",
    # The author of the module, with a comment indicating the specific person (Ibrahim Rizeq)
    'license': 'LGPL-3',  # The license under which the module is distributed
    'category': 'API/Integration',  # The category under which the module falls
    'website': 'https://fuelfinance.sa',  # The website of the module's author or company
    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'loan'],
    'css': [
        "static/src/css/simah_style.css",
    ],
    # always loaded
    'data': [
        'data/activity.xml',
        'security/simah_security.xml',
        'security/ir.model.access.csv',
        'views/simah_view.xml',
        'views/pre_enquiry.xml',
        'views/credit_instrument.xml',
        'views/simah_narr.xml',
        'views/simah_address.xml',
        'views/simah_contact.xml',
        'views/simah_employee.xml',
        'views/simah_score.xml',
        'views/simah_expense.xml',
        'views/menu.xml',
        'views/salary_certificate.xml',
        'views/simah_city.xml',
        'views/customer.xml',
        'report/report_consumer_credit_templates.xml',
        'report/consumer_credit_report.xml',

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
