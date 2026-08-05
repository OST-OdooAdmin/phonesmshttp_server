# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging
import os

_logger = logging.getLogger(__name__)

class PhoneSmsController(http.Controller):

    @http.route('/download/app-debug.apk', type='http', auth='none', methods=['GET'], csrf=False)
    def download_apk(self, **kw):
        """Serves the crash-proof Android SMS Gateway APK directly for web browsers on port 8069"""
        apk_paths = [
            '/var/lib/odoo/custom_addons/phone_sms_gateway/app-debug.apk',
            '/mnt/extra-addons/phone_sms_gateway/app-debug.apk',
            '/root/app-debug.apk'
        ]
        for path in apk_paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    content = f.read()
                headers = [
                    ('Content-Type', 'application/vnd.android.package-archive'),
                    ('Content-Disposition', 'attachment; filename="app-debug.apk"'),
                    ('Content-Length', str(len(content))),
                    ('Access-Control-Allow-Origin', '*')
                ]
                return request.make_response(content, headers=headers)
        
        return request.make_response("APK file not found on server", headers=[('Content-Type', 'text/plain')])

    def _get_api_key(self, **kw):
        api_key = request.httprequest.headers.get('X-Api-Key') or request.httprequest.headers.get('Api-Key') or kw.get('api_key')
        if not api_key and request.httprequest.data:
            try:
                body_data = json.loads(request.httprequest.data.decode('utf-8'))
                api_key = body_data.get('api_key') or body_data.get('key')
            except Exception:
                pass
        return api_key

    @http.route('/api/sms/pending', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_pending_sms(self, **kw):
        """Called by Android Phone App to fetch queued SMS messages from all queue tables"""
        api_key = self._get_api_key(**kw)
        _logger.info("SMS Gateway Pending Request received. API Key: %s", api_key)

        tasks = []

        # 1. Fetch from phone.sms.message (All queued messages)
        try:
            pending_records = request.env['phone.sms.message'].sudo().search([('state', '=', 'queued')], limit=20)
            for rec in pending_records:
                tasks.append({
                    'id': rec.id,
                    'to': rec.recipient_number,
                    'message': rec.message_body,
                    'model': 'phone.sms.message'
                })
        except Exception as e:
            _logger.warning("Error fetching phone.sms.message: %s", e)

        # 2. Fetch from sms.outbound.queue (created by wizard / test dispatch)
        try:
            if 'sms.outbound.queue' in request.env:
                wizard_records = request.env['sms.outbound.queue'].sudo().search([('state', '=', 'queued')], limit=20)
                for rec in wizard_records:
                    rec_to = getattr(rec, 'recipient', None) or getattr(rec, 'recipient_number', '') or getattr(rec, 'to', '')
                    rec_msg = getattr(rec, 'message', None) or getattr(rec, 'message_body', '')
                    tasks.append({
                        'id': rec.id,
                        'to': rec_to,
                        'message': rec_msg,
                        'model': 'sms.outbound.queue'
                    })
        except Exception as e:
            _logger.warning("Error fetching sms.outbound.queue: %s", e)

        res_data = json.dumps({'pending': tasks})
        return request.make_response(res_data, headers=[('Content-Type', 'application/json'), ('Access-Control-Allow-Origin', '*')])

    @http.route('/api/sms/logs', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_sms_logs(self, **kw):
        """Called by Android Phone App to display logs dashboard"""
        logs = []
        try:
            all_records = request.env['phone.sms.message'].sudo().search([], limit=100, order='create_date desc')
            for rec in all_records:
                status_str = "SUCCESS" if rec.state == 'sent' else ("FAILED: " + (rec.error_log or '') if rec.state == 'failed' else "QUEUED")
                logs.append({
                    "recipient": rec.recipient_number or '',
                    "message": rec.message_body or '',
                    "status": status_str,
                    "timestamp": str(rec.create_date or ''),
                    "wordCount": len((rec.message_body or '').split())
                })
        except Exception as e:
            _logger.warning("Error reading phone.sms.message logs: %s", e)

        try:
            if 'sms.outbound.queue' in request.env:
                w_records = request.env['sms.outbound.queue'].sudo().search([], limit=100, order='create_date desc')
                for rec in w_records:
                    rec_to = getattr(rec, 'recipient', None) or getattr(rec, 'recipient_number', '')
                    rec_msg = getattr(rec, 'message', None) or getattr(rec, 'message_body', '')
                    status_str = "SUCCESS" if rec.state == 'sent' else ("FAILED: " + (getattr(rec, 'error_log', '') or '') if rec.state == 'failed' else "QUEUED")
                    logs.append({
                        "recipient": rec_to or '',
                        "message": rec_msg or '',
                        "status": status_str,
                        "timestamp": str(rec.create_date or ''),
                        "wordCount": len((rec_msg or '').split())
                    })
        except Exception as e:
            _logger.warning("Error reading sms.outbound.queue logs: %s", e)

        res_data = json.dumps({'logs': logs})
        return request.make_response(res_data, headers=[('Content-Type', 'application/json'), ('Access-Control-Allow-Origin', '*')])

    @http.route('/api/sms/status', type='http', auth='none', methods=['POST'], csrf=False)
    def update_sms_status(self, **kw):
        """Called by Android Phone App after attempting to send an SMS"""
        try:
            raw_body = request.httprequest.data.decode('utf-8') if request.httprequest.data else ''
            data = json.loads(raw_body) if raw_body else kw
        except Exception:
            data = kw

        task_id = data.get('task_id')
        status = data.get('status')
        detail = data.get('detail', '')
        model_name = data.get('model', 'phone.sms.message')

        if not task_id:
            res_data = json.dumps({'error': 'Missing task_id'})
            return request.make_response(res_data, headers=[('Content-Type', 'application/json'), ('Access-Control-Allow-Origin', '*')])

        # Try specified model or fallback to both
        models_to_check = [model_name] if model_name in request.env else ['phone.sms.message', 'sms.outbound.queue']
        for m_name in models_to_check:
            if m_name in request.env:
                msg_record = request.env[m_name].sudo().browse(int(task_id))
                if msg_record.exists():
                    if status in ['sent', 'SUCCESS', 'success']:
                        msg_record.state = 'sent'
                        if hasattr(msg_record, 'error_log'):
                            msg_record.error_log = f"Delivered via Phone Gateway. Details: {detail}"
                    else:
                        msg_record.state = 'failed'
                        if hasattr(msg_record, 'error_log'):
                            msg_record.error_log = f"Failed on Phone Gateway: {detail}"
                    res_data = json.dumps({'result': 'ok'})
                    return request.make_response(res_data, headers=[('Content-Type', 'application/json'), ('Access-Control-Allow-Origin', '*')])

        res_data = json.dumps({'error': 'Task ID not found'})
        return request.make_response(res_data, headers=[('Content-Type', 'application/json'), ('Access-Control-Allow-Origin', '*')])
