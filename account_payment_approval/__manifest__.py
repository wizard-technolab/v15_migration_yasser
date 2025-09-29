# -*- coding: utf-8 -*-
{
    'name': 'Payment Approvals',
    'version': '15.0.1.0.0',
    'category': 'Accounting',
    'summary': """ This modules enables approval feature in the payment.""",
    'description': """This modules enables approval feature in the payment. """,
    'author': 'higazi',
    'depends': ['account'],
    'data': [
        'security/security.xml',
        'views/res_config_settings_views.xml',
        'views/account_payment_view.xml',
    ],
    'installable': True,
    'application': True,
}
