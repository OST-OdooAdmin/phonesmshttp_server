# -*- coding: utf-8 -*-
{
    'name': 'Phone SMS HTTP Gateway',
    'version': '1.0.0',
    'category': 'Marketing/SMS',
    'summary': 'Send SMS notifications through custom Android Phone Gateway',
    'description': """
Phone SMS HTTP Gateway Module for Odoo
======================================
This module turns an Android phone running the PhoneSMS HTTP Gateway app into an 
automated SMS gateway server for Odoo.

Features:
- Queue outbound SMS messages automatically or manually.
- Direct push via Local HTTP API (`POST /send-sms`).
- Remote polling API for mobile 4G/5G setups (`/api/sms/pending`).
- Delivery status callbacks and execution logs.
""",
    'author': 'Antigravity AI',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/sms_gateway_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
