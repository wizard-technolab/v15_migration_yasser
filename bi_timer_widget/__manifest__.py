# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Timer Widget Base',
    'version': '15.0.0.0',
    'category': 'Extra Tools',
    'summary': 'Web Timer Widget base timer widget project timer widget project task timer widget helpdesk timer widget ticket timer widget time tracker widget task start timer timesheet timer widget project tracker task tracker tasks time tracker timesheet time tracker',
    'description' :"""

        Timer Widget in odoo,
        Timer Setup in odoo,
        Start Timer in odoo,
        Stop Timer in odoo,
        Display Time Duration in odoo,
        Use Timer Widget in Another Modules in odoo,
        Base Module in odoo,
        
    """,
    'author': 'BrowseInfo',
    "price": 10,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.in',
    'depends': ['base'],
    'data': [
        'views/task.xml',
    ],
    'demo': [],
    'test': [],
    'assets': {
        'web.assets_backend': [
            'bi_timer_widget/static/src/js/timer.js',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/080ABL68rrE',
    "images":['static/description/Banner.png'],
}