{
    'name': 'Custom API controller',
    'version': '15.0.1.2.5',
    'license': 'LGPL-3',
    'category': 'Extra Tools',

    'author': 'Kitworks Systems',
    'website': 'https://kitworks.systems/',

    'depends': [
        'kw_api',
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/custom_endpoint_views.xml',
    ],

    'installable': True,
}
