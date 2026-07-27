# -*- coding: utf-8 -*-
{
    'name': 'AI Odoo Studio Builder',
    'version': '18.0.1.0.0',
    'category': 'Customization',
    'summary': 'Enterprise Studio Replacement: Create Models, Fields, Views, Automations & Webhooks',
    'description': """
AI Odoo Studio Builder
======================
Replaces Odoo Enterprise Studio in Odoo Community:
- Custom Model & Field Creator
- Form, List, and Kanban View Generator
- Automation Rules & Outbound Webhooks Trigger
- 1-Click Module Exporter
""",
    'author': 'Antigravity AI',
    'depends': ['base', 'mail', 'base_automation'],
    'data': [
        'security/ir.model.access.csv',
        'views/studio_builder_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
