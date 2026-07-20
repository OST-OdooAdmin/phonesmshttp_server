# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class PhoneSmsController(http.Controller):

    @http.route('/api/sms/pending', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_pending_sms(self, **kw):
        """Called by Android Phone App to fetch queued SMS messages to send"""
        api_key = request.httprequest.headers.get('X-Api-Key') or kw.get('api_key')
        gateway = request.env['phone.sms.gateway'].sudo().search([('api_key', '=', api_key), ('active', '=', True)], limit=1)
        
        if not gateway:
            return {'error': 'Unauthorized: Invalid API Key'}

        pending_records = request.env['phone.sms.message'].sudo().search([
            ('gateway_id', '=', gateway.id),
            ('state', '=', 'queued')
        ], limit=20)

        tasks = []
        for rec in pending_records:
            tasks.append({
                'id': rec.id,
                'to': rec.recipient_number,
                'message': rec.message_body
            })

        return {'pending': tasks}

    @http.route('/api/sms/status', type='json', auth='none', methods=['POST'], csrf=False)
    def update_sms_status(self, **kw):
        """Called by Android Phone App after attempting to send an SMS"""
        api_key = request.httprequest.headers.get('X-Api-Key')
        data = request.jsonrequest or kw

        task_id = data.get('task_id')
        status = data.get('status')
        detail = data.get('detail', '')

        if not task_id:
            return {'error': 'Missing task_id'}

        msg_record = request.env['phone.sms.message'].sudo().browse(task_id)
        if msg_record.exists():
            if status == 'sent':
                msg_record.state = 'sent'
                msg_record.error_log = f"Delivered via Phone Gateway. Details: {detail}"
            else:
                msg_record.state = 'failed'
                msg_record.error_log = f"Failed on Phone Gateway: {detail}"
            return {'result': 'ok'}

        return {'error': 'Task ID not found'}
