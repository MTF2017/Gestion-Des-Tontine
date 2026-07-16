{
    'name': 'SenTontine',

    'summary': 'Gestion des tontines, cotisations, distributions et caisse',

    'description': """
Gestion Tontine
===============

Ce module permet de gérer :

* Les tontines
* Les membres
* Les adhésions
* Les cotisations
* Les distributions
* Les pénalités
* La caisse
* Les rapports

Compatible avec Odoo 18 Community.
""",

    'author': 'Mor Talla Fall',
    'website': 'https://www.gestion_tontine.com',

    'category': 'Accounting',
    'version': '18.0.1.0.0',

    'license': 'LGPL-3',

    'depends': [
        'base',
        'contacts',
        'mail',
    ],

    'data': [
        # Sécurité
        'security/security.xml',
        'security/ir.model.access.csv',

        # Vues
        'views/tontine_group_views.xml',
        'views/tontine_member_views.xml',
        'views/tontine_subscription_views.xml',
        'views/tontine_payment_views.xml',
        'views/tontine_distribution_views.xml',
        'views/tontine_penalty_views.xml',
        'views/tontine_cash_views.xml',
        'views/tontine_reports_views.xml',

        # Menus
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'gestion_tontine/static/src/js/tontine_dashboard.js',
            'gestion_tontine/static/src/xml/tontine_dashboard.xml',
        ],
    },
    'demo': [
        # 'demo/demo.xml',
    ],

    'images': [
        'static/description/icon.png',
    ],

    'application': True,
    'installable': True,
    'auto_install': False,
}