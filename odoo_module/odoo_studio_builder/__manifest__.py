# -*- coding: utf-8 -*-
{
    'name': 'AI Odoo Studio Builder',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Enterprise Studio Replacement: Create Models, Fields, Views, Automations & Webhooks with Floating AI Bot Jemi',
    'description': """
AI Odoo Studio Builder (Community Replacement for Enterprise Studio):
- Create Custom Models & Fields (20 Field Types: Text, Monetary, Selection, Signature, Image)
- Automations & Outbound HTTP Webhooks (base.automation)
- Floating AI Assistant Bot "Jemi"
- AI Account Settings (Gemini 1.5 Pro, User ID, Account ID)
- 1-Click App Exporter
    """,
    'author': 'Antigravity AI',
    'depends': ['base', 'mail', 'base_automation'],
    'data': [
        'security/ir.model.access.csv',
        'views/studio_builder_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_studio_builder/static/src/css/jemi_floating_bot.css',
            'odoo_studio_builder/static/src/js/jemi_floating_bot.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
