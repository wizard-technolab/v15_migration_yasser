{
    'name': 'Kitworks API',
    'version': '15.0.1.1.7',
    'license': 'LGPL-3',
    'category': 'Extra Tools',

    'author': 'Kitworks Systems',
    'website': 'https://kitworks.systems/',

    'depends': [
        'kw_mixin', 'mail',
    ],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'data/ir.cron.xml',

        'views/api_main_menu_views.xml',

        'views/api_log_views.xml',
        'views/api_token_views.xml',
        'views/api_key_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_users_views.xml',
    ],

    'installable': True,
}
