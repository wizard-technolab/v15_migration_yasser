{
    'name': "Financing Services Website",
    'author': "Mosab",
    'website': "",
    'category': "Generic Modules",
    'version': "1.0",
    'depends': [
        'base',
        'crm',
        'website',
    ],

    # always loaded
    'data': [
        'security/security.xml',
        # 'templates/elm_otp.xml',
        'templates/form1.xml',
        'templates/form2.xml',
        'templates/form3.xml',
        'templates/form4.xml',
        'templates/success.xml',
    ],
    'qweb': [
    ],
    'assets':{
        'web.assets_common':[
            '/financing_services/static/src/js/desire-script.js',
            '/financing_services/static/src/js/script.js',
            '/financing_services/static/src/js/load_quot_data.js',
        ]
    },
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
