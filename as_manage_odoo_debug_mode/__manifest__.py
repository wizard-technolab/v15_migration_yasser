# -*- coding: utf-8 -*-
{
    'name': "Disable Debug Mode",
    'summary': """
        Allow users to disable/enable debug mode based on security groups.
        """,
    'description': """
        This module allow users to enable and disable odoo debug option if they have access to allow_modify_debug_mode group.
        """,

    'author': "Aemal Shirzai, NETLINKS LTD",
    'website': "https://aemal-shirzai.github.io/portfolio",
    'support': 'aemalshirzai2016@gmail.com',
    'price': '20',
    'currency': 'USD',

    'category': 'Technical',
    'version': '15.0.0.1.0.0',
    "license": "OPL-1",

    'depends': ['base'],

    'data': ['security/security.xml'],

    'demo': [],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}
