# -*- coding: utf-8 -*-
{
    'name': 'Phone SMS Gateway',
    'version': '17.0.1.0.0',
    'category': 'Services/SMS',
    'summary': 'Integrate Android Phone SMS Gateway with Odoo for Employee and Client SMS Notifications',
    'description': """
        Phone SMS Gateway Odoo Integration
        ===================================
        - Send SMS to employees and clients via Android SIM Card / Central SMS Gateway.
        - Supports Central Server Gateway (Port 22/5005), Direct Push, and Polling modes.
        - Real-time logging of SMS status (draft, queued, sent, failed).
    """,
    'author': 'Antigravity AI Team',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/sms_gateway_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
