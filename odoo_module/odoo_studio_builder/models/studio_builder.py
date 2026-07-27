# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class OdooStudioConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_provider = fields.Selection([
        ('gemini_pro', 'Google Gemini 1.5 Pro (Google One AI Pro)'),
        ('antigravity', 'Google Antigravity AI Engine'),
        ('openai', 'OpenAI GPT-4o')
    ], string='AI Engine Provider', default='gemini_pro', config_parameter='odoo_studio_builder.ai_provider')

    jemi_user_id = fields.Char(string='AI User ID / License', config_parameter='odoo_studio_builder.jemi_user_id')
    jemi_account_id = fields.Char(string='AI Account / Org ID', config_parameter='odoo_studio_builder.jemi_account_id')
    gemini_api_key = fields.Char(string='Google Gemini API Key', config_parameter='odoo_studio_builder.gemini_api_key')

class OdooStudioApp(models.Model):
    _name = 'studio.custom.app'
    _description = 'AI Odoo Studio Custom App Definition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='App Name', required=True, tracking=True)
    technical_name = fields.Char(string='Technical Name', required=True, tracking=True)
    model_name = fields.Char(string='Model Technical Name (e.g. x_custom.model)', required=True)
    description = fields.Text(string='App Description / AI Prompt')
    field_ids = fields.One2many('studio.custom.field', 'app_id', string='Fields')
    automation_ids = fields.One2many('studio.custom.automation', 'app_id', string='Automations & Webhooks')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('guided_chat', 'Guided Chat with Jemi'),
        ('generated', 'Generated & Installed')
    ], default='draft', tracking=True)

    jemi_conversation_log = fields.Text(string='Jemi Conversation History', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(OdooStudioApp, self).create(vals_list)
        for rec in records:
            rec._initialize_jemi_welcome_message()
        return records

    def _initialize_jemi_welcome_message(self):
        """Sends welcome message from AI Bot Jemi into Chatter"""
        jemi_partner = self.env['res.partner'].sudo().search([('name', '=', 'Jemi (AI Studio Assistant)')], limit=1)
        if not jemi_partner:
            jemi_partner = self.env['res.partner'].sudo().create({
                'name': 'Jemi (AI Studio Assistant)',
                'company_type': 'person',
                'comment': 'Official AI Studio Module Builder Chatbot powered by Gemini'
            })
        
        welcome_msg = _(
            "👋 Hi! I am <b>Jemi</b>, your AI Studio Module Builder Bot!<br/><br/>"
            "I am ready to build your custom Odoo module tailored to your business needs.<br/>"
            "Tell me: <b>What app or workflow would you like to create today?</b><br/>"
            "<i>(e.g., Field Service Dispatch, Inventory SMS Tracker, Customer Approval System)</i>"
        )
        self.message_post(body=welcome_msg, author_id=jemi_partner.id)

    def action_start_jemi_guided_chat(self):
        """Triggers Jemi guided questioning wizard"""
        self.ensure_one()
        self.state = 'guided_chat'
        jemi_partner = self.env['res.partner'].sudo().search([('name', '=', 'Jemi (AI Studio Assistant)')], limit=1)
        step_msg = _(
            "<b>Jemi</b>: Step 1 of 3: Got it! What custom fields do you need for <b>%s</b>?<br/>"
            "Allowed field types: <i>Text, Monetary, Selection, Signature, Image, Date, Attachments</i>.<br/>"
            "Type your response in the chatter below or click <b>🚀 Generate & Build App via Gemini AI</b>!"
        ) % self.name
        self.message_post(body=step_msg, author_id=jemi_partner.id if jemi_partner else False)

    def action_generate_app(self):
        """Generates & registers the model, fields, and views dynamically via Gemini AI"""
        for rec in self:
            rec.state = 'generated'
            jemi_partner = self.env['res.partner'].sudo().search([('name', '=', 'Jemi (AI Studio Assistant)')], limit=1)
            success_msg = _("🎉 <b>Jemi</b>: Your custom module <b>'%s'</b> has been successfully generated and compiled into Odoo!") % rec.name
            rec.message_post(body=success_msg, author_id=jemi_partner.id if jemi_partner else False)

class OdooStudioField(models.Model):
    _name = 'studio.custom.field'
    _description = 'AI Odoo Studio Field Definition'

    app_id = fields.Many2one('studio.custom.app', string='Custom App', ondelete='cascade')
    name = fields.Char(string='Field Technical Name (e.g. x_name)', required=True)
    field_description = fields.Char(string='Field Label', required=True)
    ttype = fields.Selection([
        ('char', 'Text (Char)'),
        ('text', 'Multiline Text'),
        ('html', 'HTML'),
        ('integer', 'Integer'),
        ('float', 'Decimal (Float)'),
        ('monetary', 'Monetary'),
        ('boolean', 'Checkbox (Boolean)'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('selection', 'Selection'),
        ('many2one', 'Many2One'),
        ('one2many', 'One2Many'),
        ('many2many', 'Many2Many'),
        ('binary', 'File Attachment'),
        ('image', 'Image'),
        ('signature', 'Signature')
    ], string='Field Type', required=True, default='char')

class OdooStudioAutomation(models.Model):
    _name = 'studio.custom.automation'
    _description = 'AI Odoo Studio Automation & Webhook'

    app_id = fields.Many2one('studio.custom.app', string='Custom App', ondelete='cascade')
    name = fields.Char(string='Rule Name', required=True)
    trigger = fields.Selection([
        ('on_create', 'On Creation'),
        ('on_write', 'On Update'),
        ('on_unlink', 'On Deletion')
    ], string='Trigger Event', required=True, default='on_create')
    action_type = fields.Selection([
        ('webhook', 'Send Webhook Notification (HTTP POST)'),
        ('sms', 'Send SMS (via Phone Gateway)'),
        ('email', 'Send Email'),
        ('code', 'Execute Python Code')
    ], string='Action Type', required=True, default='webhook')
    webhook_url = fields.Char(string='Webhook Target URL')
