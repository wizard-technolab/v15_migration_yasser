# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

{
    'name': 'Hide Delete Button', 
    'version': '15.0.1.0',
    'sequence': 1, 
    'category': 'Tools', 
    'description': 
        """ 
         Hide Duplicate. disable duplicate button , disbale delete
This Odoo application will hide Delete option from the all the records of the odoo. So once this application is installed, nobody can Delete any record of odoo(except some authenticated users)

Delete option will be hidden for all the records of odoo
Only user with Access Delete right can duplicate records

Delete option of odoo
Remove Delete access from the user
Delete option is hidden now

odoo appp Hide delete button from action. hide delete, delete buttton hide, hide delete button, hide delete action, hide delete, delete hide button, hide delete action, action delete hide, disable delete, delete disable, delete hide

    """,
    'summary': 'odoo appp Hide delete button from action. hide delete, delete buttton hide, hide delete button, hide delete action, hide delete, delete hide button, hide delete action, action delete hide, disable delete, delete disable, delete hide',
    'author': 'DevIntelle Consulting Service Pvt.Ltd', 
    'website': 'http://www.devintellecs.com',
    'depends': ['web'],
    'data': [
        'security/security.xml',
    ],
    'assets': {
       'web.assets_backend': [
           'dev_hide_delete/static/src/js/hide_delete.js',
       ],
   },
    'qweb': [],
        'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':9.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
