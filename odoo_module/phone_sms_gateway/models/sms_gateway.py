# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class PhoneSmsGatewayConfig(models.Model):
    _name = 'phone.sms.gateway'
    _description = 'Phone SMS Gateway Configuration'

    name = fields.Char(string='Gateway Name', required=True, default='My Android Phone Gateway')
    mode = fields.Selection([
        ('direct_push', 'Direct Push (Local Wi-Fi HTTP POST)'),
        ('polling', 'Remote Polling (Phone pulls from Odoo over 4G/5G)')
    ], string='Communication Mode', default='direct_push', required=True)

    phone_ip = fields.Char(string='Phone IP Address', help='e.g. 192.168.1.120 (for Direct Push mode)')
    phone_port = fields.Integer(string='Phone Port', default=8080)
    api_key = fields.Char(string='API Security Key', default='secret_sms_key_123')
    active = fields.Boolean(string='Active', default=True)

    def test_connection(self):
        """Test connection to local Android phone app HTTP endpoint"""
        self.ensure_one()
        if self.mode == 'direct_push':
            if not self.phone_ip:
                return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': 'Error', 'message': 'Please enter a Phone IP Address.', 'sticky': False, 'type': 'danger'}}
            
            url = f"http://{self.phone_ip}:{self.phone_port}/status"
            try:
                response = requests.get(url, timeout=4)
                if response.status_code == 200:
                    return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': 'Success', 'message': f'Connected to Phone Gateway! Device response: {response.text}', 'sticky': False, 'type': 'success'}}
                else:
                    return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': 'Failed', 'message': f'Phone returned HTTP {response.status_code}', 'sticky': False, 'type': 'warning'}}
            except Exception as e:
                return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': 'Connection Error', 'message': f'Cannot reach phone at {url}: {str(e)}', 'sticky': False, 'type': 'danger'}}
        else:
            return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': 'Polling Mode Active', 'message': 'In Polling mode, the Android app periodically checks Odoo for new messages.', 'sticky': False, 'type': 'info'}}


class PhoneSmsMessage(models.Model):
    _name = 'phone.sms.message'
    _description = 'Phone SMS Outbound Queue & Logs'
    _order = 'create_date desc'

    gateway_id = fields.Many2one('phone.sms.gateway', string='Gateway', required=True)
    recipient_number = fields.Char(string='Recipient Phone', required=True)
    message_body = fields.Text(string='Message Content', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], string='Status', default='queued', required=True)

    error_log = fields.Text(string='Error / Response Log')

    def action_send_now(self):
        """Manually trigger SMS dispatch"""
        for record in self:
            if record.gateway_id.mode == 'direct_push':
                record._send_via_direct_push()
            else:
                record.state = 'queued'
                record.error_log = 'Waiting for Android Phone App polling check...'

    def _send_via_direct_push(self):
        self.ensure_one()
        gateway = self.gateway_id
        if not gateway.phone_ip:
            self.state = 'failed'
            self.error_log = 'No Phone IP set on gateway configuration.'
            return

        url = f"http://{gateway.phone_ip}:{gateway.phone_port}/send-sms"
        payload = {
            "to": self.recipient_number,
            "message": self.message_body
        }
        headers = {"Content-Type": "application/json"}

        try:
            res = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
            if res.status_code == 200:
                self.state = 'sent'
                self.error_log = f"SUCCESS: {res.text}"
            else:
                self.state = 'failed'
                self.error_log = f"HTTP Error {res.status_code}: {res.text}"
        except Exception as e:
            self.state = 'failed'
            self.error_log = f"Network exception: {str(e)}"
